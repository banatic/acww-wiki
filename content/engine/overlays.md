# 오버레이
<!-- source: wiki/engine/overlays.md -->

**요약.** 상주하는 `main`, `itcm`, `autoload_2` 이미지 외에도, ACWW의 코드는 필요할 때 메인 RAM에
페이징되어 들어오는 148개의 오버레이(overlay) 슬롯에 들어 있다. 대부분이 서로 주소를 공유하므로,
"`0x02260020`에 무엇이 있는가"는 어느 오버레이가 상주해 있는지를 알지 못하면 답이 없다.
오버레이를 로드하면 그 이미지를 복사하고(선택적으로 압축을 풀고) C++ 정적 초기화자를 실행한다;
언로드하면 전역 체인에서 그 소멸자들을 쓸어낸다. 마을은 다섯 개의 오버레이가 동시에 상주해야
하며, 거기까지 데려다주는 택시가 여섯 번째다.

## 무슨 일이 일어나는가

### 몇 개이고 얼마나 큰가

빌드 설정은 메인 모듈과 네 개의 오토로드(`itcm`, `dtcm`, `autoload_2`, `autoload_3`) 옆에
`ov000`부터 `ov147`까지 148개의 오버레이 슬롯을 선언한다
[S: `config/adm-kr/arm9/config.yaml`; 148 directories under
`config/adm-kr/arm9/overlays/`]. 그 슬롯 중 138개는 적어도 하나의 함수 심볼을 가지고 있고; 열 개는
전혀 없다 — `ov000`, `ov057`부터 `ov064`, 그리고 `ov089`
[S: counted from `config/adm-kr/arm9/overlays/*/symbols.txt`, `kind:function` lines].

모든 모듈에 걸쳐 심볼 테이블은 25,516개의 함수와 15,313개의 데이터 심볼을 이름 짓는다
[S: counted from `config/adm-kr/arm9/**/symbols.txt`]. `main`이 함수 중 11,923개를,
`autoload_2`가 2,199개를 가지며; `itcm`은 158개; 오버레이들이 합쳐서 11,236개를 가진다
[S: same count]. 오버레이 띠의 함수 주소는 `0x02207cc0`부터 `0x022a31d8`까지다
[S: minimum and maximum `addr:` over `config/adm-kr/arm9/overlays/*/symbols.txt`,
`kind:function` lines].

### 오버레이는 겹치며, 그것이 오버레이에 관한 핵심 사실이다

인접한 오버레이 137쌍 중 129쌍이 주소가 겹친다
[S: `port/shim/fs/ovlreloc.c` header]. 공유는 사소하지 않다: 35개의 오버레이가
`0x02260020`에서 시작하고, 19개가 `0x02278a00`, 14개가 `0x0229c180`, 12개가 `0x02260420`에서 시작한다
[S: counted from the minimum function address of each `config/adm-kr/arm9/overlays/*/symbols.txt`].

두 가지 결과가 따르며, 둘 다 포트에 오류를 일으킨 적이 있다. 첫째, 공유된 주소의 워드는
어느 오버레이가 로드되어 있든 그것에 속하므로, 재배치(relocation) 테이블을 모든 후보에
미리 적용할 수 없다 — 테이블은 오버레이 id별로 생성되고 로드 시점에 적용된다
[S: `port/shim/fs/ovlreloc.c` header]. 둘째, 주소만으로는 명령어 집합이 결정되지 않는다:
`ov003`과 `ov004`는 주소를 공유하며, 주소만으로 키를 잡은 테이블이
Thumb 함수 `func_ov003_02226048`을 ARM으로 실행하여, 푸시 대상 함수의 호스트 주소에서 푸시를
실행했다 [E: `docs/log/cycle40-keyboard-gate-probe.md` CARD40..SND40, second
fault]. 그런 이유로 명령어 집합 테이블은 모든 항목 옆에 오버레이 id를 담고 있다
[S: `port/interp/interp.h:64-68`].

### 하나를 로드하기

오버레이의 헤더는 고정된 레코드다: id, RAM 주소, RAM 크기, BSS 크기, 정적 초기화자
배열의 경계, 파일 id, 24비트 압축 크기, 8비트 플래그
[S: `FSOverlayInfoHeader`, `port/shim/fs/ovlreloc.c:31-41`]. `FS_LoadOverlayImage`가
오버레이의 바이트를 RAM에 복사하고, `FS_StartOverlay`가 작업을 마무리한다
[S: `FS_StartOverlay` / `FS_LoadOverlayImage`, `port/shim/fs/ovlreloc.c` header]. 플래그의
비트 0은 이미지가 역방향 압축되어 있고 `MIi_UncompressBackward`로 풀린다는 뜻이다
[S: `FS_OVERLAY_FLAG_COMP`, `port/shim/fs/ovlreloc.c:50, 56`].

`FS_StartOverlay`가 마지막으로 하는 일은 `sinit_init`부터 `sinit_init_end`까지의 배열을 순회하며
그 안의 각 워드를 호출하는 것이다 — 오버레이의 C++ 정적 초기화자들이다
[S: `port/shim/fs/ovlreloc.c` header, and the walk at `:243-258`]. 그 워드들은 방금 복사된
이미지 안의 NDS 주소이며, 바로 이것이 포트에서 첫 오버레이 호출이 `0x02266905`의 날것 ARM 코드로의
점프로 나타난 이유다
[H: host-source account from `port/shim/fs/ovlreloc.c` header; verify with a retained scripted run and frame using this page's recipe]. 하나의 오버레이는 많아야 이백여 개를 담으며;
인터프리터 경로는 최대 256개까지 읽는다 [S: `port/shim/fs/ovlreloc.c:206-212`].

인증 블록도 있다: `FSi_CompareDigest`는 이미지를 다이제스트 테이블과 대조하며 그 유일한
실패 경로는 `OS_Terminate()`이다 [S: `port/shim/fs/ovlreloc.c` header].
PC 포트는 이를 의도적으로 생략하며, 조용히 생략하는 대신 그렇게 한다고 밝힌다
[S: `port/shim/fs/ovlreloc.c` header].

### 하나를 언로드하기, 그리고 소멸자 체인

`FS_EndOverlay`는 전역 소멸자 체인을 쓸어내며 주소가 언로드되는 범위 안에 들어가는 등록된
소멸자를 모두 끊어낸다 — 검사는 저장된 워드에 대한 `lo <= dtor < hi`이다
[S: `FS_EndOverlay`, `port/shim/fs/ovlreloc.c:213-220`]. 이 검사가 PC 포트가 인터프리터 경로에서
오버레이 풀 워드를 다시 쓸 수 없는 이유다: 코드 주소를 호스트 주소로 바꿔 쓰면 그것이 모든 NDS
범위 밖에 놓이고, 노드는 연결된 채 남으며, 다음 오버레이가 그 위에 로드되고, 체인은
쓰레기 속으로 걸어 들어간다
[E: `docs/log/cycle40-keyboard-gate-probe.md` OVL40, runs `tap-D53` and `tap-D54`].

같은 오류의 이전 변형도 알아 둘 가치가 있는데, 실수로 재현하기 쉽기 때문이다: 호스트
`FS_EndOverlay`가 ROM의 체인 대신 호스트 C++ 런타임의 `__global_destructor_chain`을
순회했고, 이는 완전히 다른 체인이다
[E: `docs/log/cycle40-keyboard-gate-probe.md` OVL40, `tap-D52`].

### 어느 오버레이가 어느 기능을 담는가

아래의 식별은 출력 가능한 ROM 텍스트를 가리키는 리터럴 풀 워드를 해석한 데서 나온다 —
오버레이는 자신의 에셋 경로를 통해 스스로의 주제를 이름 짓는다
[S: `docs/kb/modules/ov003-068.md`, "What these modules are"].

`ov003`은 야외 마을/필드 3D 씬 모듈이다: 전체 전경 에셋 트리(나무, 풀, 꽃, 구멍, 돌),
집, 지면, 눈사람 NPC, 물고기, 곤충, 표지판, 그리고 계절별 텍스처 변형
[S: `docs/kb/modules/ov003-068.md`]. `ov004`는 그 실내 대응물이다 — 방 오브젝트, 가구,
TV 프로그램, 벽과 바닥 — 그리고 `ov003`과 소스 트리를 공유하며, 동일한 곤충 테이블에 이르기까지
같다 [S: `docs/kb/modules/ov003-068.md`;
`docs/kb/modules/ov004.md`]. `ov068`은 특수 NPC와 도착 시퀀스다: 특수 NPC
모델, 개, 택시와 그 부품, 비와 물튀김 효과, 그리고 새 게임 질문 시퀀스의 스크립트
레이블 — 캇페이의 택시 [S: `docs/kb/modules/ov003-068.md`].

`ov001`은 NitroDWC의 `util` 씬/UI 라이브러리와 AOSS/Aterm 벤더 접합부(seam)다
[S: `docs/kb/modules/ov001.md`]. `ov065`는 세 벤더에서 온 네 컴포넌트가 한 오버레이에 들어 있는
것이다: NitroWiFi, NitroDWC, GameSpy [S: `docs/kb/modules/ov065.md`]. `ov067`은
NitroSDK의 `add-ins/wxc`, 즉 Wireless eXchange 라이브러리이며, 54개 함수 중 54개가 완전히
식별되었다 [S: `docs/kb/modules/ov067.md`]. `ov068`의 `0x022667e0` 슬롯은
`ov065`, `ov066`, `ov067` 옆에 있지만, 그것은 재사용되는 일시적 메모리이지 Wi-Fi 영역이 아니다
[S: `docs/kb/modules/ov003-068.md`].

`ov126`은 화면 키보드의 터치 디스패처 `func_ov126_022a1228`을 담고 있는데, 이것은 함수
포인터로만 존재한다 — 오버레이의 `0x022a1ff0` 재배치 항목이 Thumb 진입점인 `0x022a1229`를
담고 있다 [S: `docs/log/cycle40-keyboard-gate-probe.md` PROBE40 unit block]. `ov147`은
`0x0229ad4c`의 BSS에 부팅 머신 상태 테이블을 두며, 자체 정적 초기화자가 채운다
[S: `port/shim/gfx/pmflist.c:213-222`].

### 마을 시퀀스 중의 상주 상태

스크립트된 마을 실행의 프레임 37,500 — 플레이어가 마을 회관 앞에 서 있는 시점 — 에서
오버레이 5, 36, 54, 120, 117이 로드되어 있다
[E: `scratchpad/cycle40/runs/tap-D56`, frame 37500;
`docs/log/cycle40-keyboard-gate-probe.md` TOWN40]. 오버레이 5는 그보다 일찍, 마을 진입 중에,
마을의 씬 6 스테이지가 실행되기 전에 로드된다
[E: `docs/log/cycle40-keyboard-gate-probe.md` CALL40].

심볼 테이블도 이것들이 작은 모듈임에 동의한다: `ov005`는 함수 하나, `ov036`도
하나, `ov054`는 88개, `ov117`은 31개, `ov120`은 95개를 이름 짓는다
[S: counted from `config/adm-kr/arm9/overlays/*/symbols.txt`]. `ov054`는 `0x02260420`에서
시작하고 `ov120`은 `0x0229a340`에서 시작한다 [S: same tables].

### 확정됨: `ov004`에 함수가 몇 개 있는가

`ov004`에 대해 기록된 두 숫자는 모순이 아니라 두 개의 테이블이다.
커밋된 `symbols.txt`는 121개의 `kind:function` 항목을 나열하며, 그중 90개는 0이 아닌 크기를 가지고
31개는 크기 0의 `_unk` 자리표시자다 [S: `config/adm-kr/arm9/overlays/ov004/symbols.txt`,
counted over `kind:function` lines]. 그 옆에는 3,060개의 경계 복원된 타깃이 모두 크기를 가진 채
들어 있는 사이드카(SIDECAR)인 `recovered.txt`가 있다 [S: `config/adm-kr/arm9/overlays/ov004/recovered.txt`,
same count]. 사이드카가 존재하는 이유는 dsd가 `symbols.txt`를 소유하고 다시 쓰기 때문에, 복원된
추측을 섞어 넣을 수 없어서다 [S: `tools/agent/target.py:183-215`, the "WHY A SIDECAR BESIDE
symbols.txt" note, which records the same 90 sized symbols covering 3.8% of the module].
`T.load_all()`은 둘 다 로드하므로, `recovered.txt`에만 등장하는 `func_ov004_*` 이름은
`../STYLE.md` 규칙 2에 따라 정당한 심볼 테이블 이름이다 [S: `tools/agent/target.py:50-65, 224`].
kb 문서의 "90 symbols to 3,075 targets"는 같은 사건을 조금 이전 리비전에서 센 것이다
[S: `docs/kb/modules/ov004.md`].

## 어디에 있는가

| 함수 또는 심볼 | 모듈 | 역할 | 등급 / 출처 |
|---|---|---|---|
| `FS_LoadOverlayImage` | main | 오버레이의 바이트를 RAM에 복사한다 | [S: `port/shim/fs/ovlreloc.c` header] |
| `FS_StartOverlay` | main | 압축 해제, 인증, 정적 초기화자 실행 | [S: `port/shim/fs/ovlreloc.c` header] |
| `FS_EndOverlay` | main | 주소가 언로드 범위에 있는 소멸자를 쓸어낸다 | [S: `port/shim/fs/ovlreloc.c:213-220`] |
| `FSi_CompareDigest` | main | 오버레이 무결성 검사; 실패는 `OS_Terminate()` | [S: `port/shim/fs/ovlreloc.c` header] |
| `MIi_UncompressBackward` | autoload_2 | 압축된 오버레이 이미지를 푼다 | [S: `port/shim/fs/ovlreloc.c:56`] |
| `func_ov126_022a1228` | ov126 | 키보드의 터치 디스패처, 포인터로만 도달 | [S: cycle40 log, PROBE40] |
| `func_ov003_02226048` | ov003 | Thumb; `ov004` 함수와 주소를 공유 | [E: cycle40 log, CARD40..SND40] |
| `__sinit_ov147_0229a700` | ov147 | `0x0229ad4c`의 부팅 머신 상태 테이블을 채운다 | [S: `port/shim/gfx/pmflist.c:213-217`] |

## 읽고 쓰는 데이터

| 주소 또는 필드 | 의미 | 쓰는 쪽 | 읽는 쪽 |
|---|---|---|---|
| 오버레이 헤더 `ram_address` / `ram_size` / `bss_size` | 이미지가 놓이는 곳과 차지하는 양 | ROM의 오버레이 테이블 | `FS_StartOverlay` [S: `port/shim/fs/ovlreloc.c:31-41`] |
| 오버레이 헤더 `sinit_init` .. `sinit_init_end` | 정적 초기화자 배열 | 링커 | `FS_StartOverlay`의 마지막 순회 [S: `port/shim/fs/ovlreloc.c` header] |
| 오버레이 헤더 `flag` 비트 0 | 이미지가 역방향 압축됨 | 링커 | `FS_StartOverlay` [S: `port/shim/fs/ovlreloc.c:50`] |
| ROM의 전역 소멸자 체인 | 등록된 오버레이 소멸자 | C++ 정적 초기화자 | `FS_EndOverlay`의 `lo <= dtor < hi` 스윕 [S: `port/shim/fs/ovlreloc.c:213-220`] |
| `0x0229ad4c` | `ov147`의 부팅 머신 상태 테이블 (첫 8워드가 폴링됨) | `__sinit_ov147_0229a700` | `ov147`의 상태 머신 [S: `port/shim/gfx/pmflist.c:213-222`] |
| `0x022a1ff0` (`ov126` 재배치 슬롯) | 키보드 터치 디스패처인 `0x022a1229`를 담는다 | `ov126`의 재배치 | 키보드 [S: cycle40 log, PROBE40] |

## 확인 방법

`docs/kb/hybrid/recipes.md` section 3의 두 번 탭 마을 레시피를 실행하고 로그에서 포트 자체의
오버레이 줄을 읽는다: `FS_StartOverlay`는 인터프리터 경로에서 로드하는 첫 여덟 개의 오버레이에 대해
`acww ovl: overlay N: M static initialisers run as ROM code`를 출력한다
[S: `port/shim/fs/ovlreloc.c:219-231`]. 그 실행의 프레임 37,500이
위에서 인용한 오버레이 집합을 가진 마을 회관 프레임이다
[E: `scratchpad/cycle40/runs/tap-D56`].

실행 없이 주어진 주소가 어느 오버레이에 속하는지 확인하려면, 그 주소를 포함하는 모듈 디렉터리의
함수 심볼을 센다: 모든 `config/adm-kr/arm9/overlays/ovNNN/symbols.txt`
줄은 `addr:0x...`를 담고 있고 모듈은 그 디렉터리다
[S: `config/adm-kr/arm9/overlays/*/symbols.txt`].

## 가설

- 심볼이 없는 열 개의 슬롯(`ov000`, `ov057`-`ov064`, `ov089`)은 데이터 전용 오버레이다 —
  코드가 아니라 아카이브나 테이블이다 [H: settled by reading their extracted images' section
  headers, or by showing no branch target in any module resolves into their address range].
- 마을 회관에서 상주하는 다섯 오버레이(5, 36, 54, 117, 120)는 야외 마을 플레이를 위한
  안정된 집합이지, 그 한 프레임의 일시적 상태가 아니다 [H: settled by logging every
  `FS_StartOverlay` / `FS_EndOverlay` across the 40,500-48,000 window of the town recipe].
- 리터럴 풀 텍스트로 이루어진 오버레이 식별은 작은 번호의 오버레이들에도 유효하며,
  그 대부분은 그런 문서가 없다 [H: settled by re-running the pool-text extraction
  over all 138 symbol-bearing overlays and publishing the subject of each].

## 관련 문서

- `memory-map.md` — 오버레이 띠가 어디에 있는지, 그리고 그 주소를 또 무엇이 차지하는지
- `boot-and-entry.md` — 첫 오버레이가 로드되기 전에 실행되어야 하는 파일 시스템 초기화
- `scenes-and-channels.md` — 어떤 오버레이가 필요한지 결정하는 씬 기계 장치
- `display-objects.md` — 언로드가 쓸어내는 소멸자 체인
