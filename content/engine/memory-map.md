# 메모리 맵
<!-- source: wiki/engine/memory-map.md -->

**요약.** ACWW는 `0x02000000`에 있는 4 MB 메인 RAM에서 실행되며, 그 양옆에 두 개의 밀결합 메모리(tightly-coupled memory) —
아래쪽 `0x01ff8000`의 명령 TCM과 `0x027e0000`의 데이터 TCM — 가 있고, 여기에 통상적인 NDS I/O, 팔레트, VRAM, OAM 윈도우가 더해진다.
코드는 메인 RAM의 맨 아래를 차지하고(`main`, 그다음 `autoload_2`); 오버레이는 `0x02207cc0`-`0x022a31d8` 주변의 띠(band)에 페이징되어 들어오며;
게임의 전역 변수는 `0x021cxxxx`-`0x021fdxxx`에 모여 있고; 아레나의 로우 워터 마크 위쪽의 모든 것은 게임이 모든 객체를 할당하는
하나의 확장 힙이다. 이 문서는 다른 엔진 문서들이 인용해 들어오는 주소 색인이다.

## 무슨 일이 일어나는가

### 영역

| 영역 | 주소 범위 | 크기 | 등급 / 출처 |
|---|---|---|---|
| ITCM | `0x01ff8000`-`0x02000000` | 32 KB | [S: `docs/kb/hybrid/runtime.md` section 2, from `port/interp/interp.h`] |
| 메인 RAM | `0x02000000`-`0x02400000` | 4 MB | [S: `port/platform/win32.c:75-76`] |
| DTCM | `0x027e0000`-`0x027e4000` | 16 KB | [S: `port/interp/interp_boot.c:11-14`] |
| 시스템 RAM 미러 윈도우 | `0x027f0000`-`0x02800000` | 64 KB | [S: `port/platform/win32.c:108-111`] |
| I/O 레지스터, 두 2D 엔진 모두 | `0x04000000`-`0x04002000` | 8 KB | [S: `port/platform/win32.c:99`] |
| 팔레트 RAM | `0x05000000`-`0x05000800` | 2 KB | [S: `port/platform/win32.c:100`] |
| VRAM, 모든 윈도우와 LCDC 별칭 | `0x06000000`-`0x068a4000` | — | [S: `port/platform/win32.c:106`] |
| OAM | `0x07000000`-`0x07000800` | 2 KB | [S: `port/platform/win32.c:107`] |

메인 RAM은 하드웨어에서 `0x02000000`-`0x02ffffff`에 걸쳐 미러링되며, 게임은 이에 의존한다:
crt0는 `0x027fff9c`의 인터럽트 벡터 슬롯에 쓰고 부팅 플래그는 `0x027ffc20`에 있는데,
둘 다 `0x027fxxxx` 윈도우 안에 있고, 이는 `0x023fxxxx`와 같은 저장 공간이다
[H: host/prose inference from `port/platform/win32.c:78-83`; verify against the ROM function or symbol table and this page's recipe]. VRAM 범위 안에서 엔진 A의 BG 윈도우는
`0x06000000`, 엔진 B의 것은 `0x06200000`, 두 OBJ 윈도우는 `0x06400000`과 `0x06600000`,
LCDC 뱅크 별칭은 `0x06800000`에 있다; ROM 자체의 초기화(bring-up)는 마지막 것의 128 KB를
지운다 [H: host/prose inference from `port/platform/win32.c:101-105`; verify against the ROM function or symbol table and this page's recipe].

### 코드가 있는 곳

| 모듈 | 함수 주소 범위 | 함수 심볼 수 | 등급 / 출처 |
|---|---|---|---|
| `itcm` | `0x01ff8000`-`0x01ffda6c` | 158 | [S: `config/adm-kr/arm9/itcm/symbols.txt`] |
| `main` | `0x0200007a`-`0x020c74c4` | 11,923 | [S: `config/adm-kr/arm9/symbols.txt`] |
| `autoload_2` | `0x020e8840`-`0x02138f00` | 2,199 | [S: `config/adm-kr/arm9/autoload_2/symbols.txt`] |
| 오버레이 (코드가 있는 것 138개) | `0x02207cc0`-`0x022a31d8` | 11,236 | [S: `config/adm-kr/arm9/overlays/*/symbols.txt`] |
| `dtcm`, `autoload_3` | — | 0 | [S: their `symbols.txt` files contain no `kind:function` lines] |

`itcm`은 작고 자주 실행된다(hot): 객체별 디스플레이 스텝 `func_01ffd1b4`, 스테퍼
`func_01ffd44c`, 스텝 게이트 `func_01ffd41c`, 그리고 리스트 센티널/후속자 쌍이 모두 여기에
있다 [S: `port/shim/gfx/dispstep.c` header; `port/shim/gfx/dispsteppers.c:24-28`;
`port/shim/gfx/dispgate.c` header]. `autoload_2`는 라이브러리 계층이다 — MSL C,
CodeWarrior float/64비트 런타임, SPL, 한국어 IME, C++ 언와인더
[S: `docs/kb/modules/autoload2.md`]. 그 안에서 `0x021341f0`-`0x02137124`는 CodeWarrior의
`FP_fastI_v5t_LE.a`에서 온 미리 빌드된 어셈블리이며 컴파일된 C가 전혀 아니다
[S: `docs/kb/modules/autoload2.md`].

오버레이는 심하게 겹친다 — 인접한 137쌍 중 129쌍이 주소 범위를 공유한다 — 그래서 오버레이 띠 안의
주소는 상주(residency) 여부에 대한 답과 함께일 때만 하나의 바이트를 식별한다
[H: host/prose inference from `port/shim/fs/ovlreloc.c` header; verify against the ROM function or symbol table and this page's recipe]. `overlays.md`를 참고하라.

### DTCM의 스택

crt0는 SVC와 IRQ 스택을 DTCM 맨 위에 두고 시스템 스택을 그 아래에 둔다; 분할은
NitroSDK의 기본값으로, `0x027e3fc0` 위에 IRQ 0x100과 SVC 0x40이다
[S: `port/interp/interp_boot.c:11-14`]. 둘 아래인 `0x027e3e00`에서 PC 포트의 인터프리터는
자체 시스템 스택을 시작하고 아래로 자란다 [S: `port/interp/interp_boot.c:31`]. DTCM의 맨 아래는
OS 인터럽트 테이블이다: `OS_IRQTable[0]`, 즉 VBlank 슬롯은 `0x027e0000`의 워드이다
[S: `port/shim/os/vblank.c:80`]. PXI 수신 콜백 테이블은 `0x027e0394`에 있으며, FIFO 태그로
인덱싱된다 [S: `port/shim/os/pxisend.c:99-135` via `docs/kb/hybrid/hardware-services.md` section 1].

### 아레나와 게임 힙

초기화의 마지막 호출인 `func_020ea48c`가 OS 아레나에서 게임의 메인 힙을 잘라낸다
[S: `port/shim/boot/heapinit.c` header]. 이 함수는 `OS_GetArenaLo(0)`과 `OS_GetArenaHi(0)`을 읽고, 빼기 전에 낮은 쪽 끝을 32바이트로
올림하여 크기가 이미 정렬 패딩을 감당하도록 한 다음, 나머지를
`OS_AllocFromArenaLo`로 할당한다 [S: `func_020ea48c`, autoload_2,
`port/shim/boot/heapinit.c` header]. 두 리터럴이 이 함수의 전체 상태다: `0x021fbe90`의 설정된 힙
크기(0이면 "아레나의 나머지를 모두 가져간다"는 뜻)와 `0x021fbe98`의 아레나 id(이 함수는
항상 메인 아레나인 0으로 설정한다)
[S: `port/shim/boot/heapinit.c` header].

그다음 `func_020ea50c`가 힙 자체를 만든다 [S: `port/shim/boot/gameheap.c` header]. 블록 앞에 0x30바이트 헤더를
유지한다: NNS 확장 힙은 블록 + 0x30에 0x30바이트 적은 크기로 생성되고, 옵션
플래그는 `data_0213e5a4`에서 읽으며, `func_020ea41c`가 그 배치를 해당 헤더에 기록한다
[S: `func_020ea50c` / `func_020ea298`, autoload_2, `port/shim/boot/gameheap.c` header]. 이
패밀리 자체의 풀 워드는 `0x021fbe78`, `0x021fbe8c`, `0x021fbe94`이다
[S: `port/shim/boot/gameheap.c:40-43`].

하드웨어에서 아레나 상한은 `0x023e0000`이다 [S: `OS_GetInitArenaHi`,
`port/shim/os/arenahi.c` header]. PC 포트는 메인 아레나에 한해 이를 `0x023f0000`으로 올리는데,
이는 하드웨어가 OS를 위해 예약하는 64 KB를 게임 힙에 주는 명시적으로 표시된 양보(concession)로,
타이틀 화면에서 포트가 하드웨어보다 약 48 KB 더 많은 살아 있는 메인 힙 무게를 들고 있어
0x4b000 크기의 씬 버퍼가 그렇지 않으면 할당에 실패하기 때문이다
[S: `port/shim/os/arenahi.c` header]. 그 심은 인터프리터 경로에 등록된 호스트 서비스이며
— 거부 목록에 없다 — 따라서 그 차이는 거기서도 살아 있다
[S: `port/tools/interp_registry.py`, whose `DENY_FILES` set has 49 basenames and does not name
`arenahi.c`; `docs/kb/hybrid/runtime.md` section 4 says "40 shim files" and is stale by nine]. 하드웨어에서는
같은 씬이 `0x022a3330`-`0x023e0000`에 들어간다 [S: `port/shim/os/arenahi.c` header].

디스플레이 오브젝트는 그 힙에서 할당되며, 그래서 상수로는 어느 것도 이름 지을 수 없다:
관측된 마을 시기의 객체들은 `0x022b6xxx`-`0x022b7xxx` 부근에 있으며 실행마다 이동한다
[H: host-source account from `port/shim/gfx/pmflist.c:52-66, 262-268`, which keeps live pointers precisely because the
allocations move; verify with a retained scripted run and frame using this page's recipe].

### 전역 변수 띠

전역 변수는 몇 개의 좁은 띠에 모여 있으며, 주소가 어느 띠에 있는지 아는 것만으로도 보통
그것이 무엇인지 짐작하기에 충분하다.

`0x020exxxx`는 `main` 맨 위의 정적 데이터다: `0x020e3134`의 채널 핸들러 테이블,
리소스 종류 디스패치 테이블 `data_020e41ec`, 씬 id `data_020e3c80`, 그리고
게임 모드 바이트 `data_020e54ac` [S: `port/shim/gfx/gxdirect_a.c:241`;
`port/shim/game/stageloop.c:23`; `port/shim/game/scenestate.c:31-34`;
`docs/kb/port/sequencer-and-modes.md`].

`0x0213xxxx`는 `autoload_2`의 데이터다: 힙 옵션 플래그 `data_0213e5a4`, `0x0213e7fc`의 디스플레이 워크
모드, 그리고 치명적 오류 경로가 `0x0213fde0`에 쓰는 예외 레지스터 테이블
[S: `port/shim/boot/gameheap.c:40`; `port/shim/gfx/commit.c:21`; E: cycle40 log, CARD40..SND40].

`0x021cxxxx`는 씬 시기의 게임 상태다: `0x021c526c`의 필드 데이터 포인터, `0x021c67d0`-`0x021c67d8`의 카메라
타깃 기본값, 그리고 `0x021c75b0`과 `0x021c75b8`의 씬 6의 두 업데이트 게이트 바이트
[S: `port/shim/gfx/pmflist.c:296-300, 173-176, 124-131`].

`0x021fxxxx`는 엔진 자체의 제어 블록이다: `0x021f42f0`의 씬 6 스테이지 카운터,
`0x021f69d0`의 시퀀서 메일박스, `0x021f6ca0`의 VBlank 태스크 리스트, `0x021fbe78`-`0x021fbe98`의 게임 힙
워드, `0x021fcfd4`/`0x021fcfdc`의 채널 열림 상태,
`0x021fcff4`의 현재 노드 공개(publication), `0x021fd004`,
`0x021fd014`, `0x021fd024`, `0x021fd034`의 네 디스플레이 리스트 헤드, 그리고
`0x021fd044`의 채널 핸들러 테이블 포인터 [S: `port/shim/game/scene6init.c` header; `docs/kb/port/sequencer-and-modes.md`;
`port/shim/gfx/vbtask.c:22-25`; `port/shim/boot/gameheap.c:40-43`;
`port/shim/game/chanstage.c:78-80`; `port/shim/gfx/pmflist.c:104`;
`port/shim/gfx/dispstep.c:55-58`].

### PC 포트가 추가하는 것과 매핑하는 것

위의 모든 것은 NDS 주소다. 포트 자체의 추가분은 호스트 주소이며, 게임의 것으로
오인되지 않도록 여기에만 이름을 적어 둔다:

- 포트의 실행 이미지는 `0x00400000`-`0x00c00000`을 차지하며, 그 안의 모든 함수는
  같은 3바이트 프롤로그로 시작하는데, 이것이 포트가 호스트 코드 진입점과
  NDS 워드를 구분하는 방법이다 [S: `port/shim/gfx/pmflist.c:76-100`];
- `0x30000000`에 있는 0x02780000바이트 크기의 생성된 아레나는 ROM 테이블이
  배치할 수 없는 데이터 심볼을 담는다 [S: `port/platform/win32.c:114-117`];
- 인터프리터의 인터럽트 스택은 16 KB 호스트 버퍼로, 중첩 진입은 2 KB씩
  내려가고 깊이 7을 넘으면 거부한다 [S: `docs/kb/hybrid/runtime.md` section 4, from
  `port/interp/interp_boot.c:613-641`].

포트는 NDS 메모리를 실제 주소에 매핑하므로, NDS 주소가 곧 호스트 포인터이며
인터프리터는 변환도 MMU도 없이 ROM 바이트를 제자리에서 실행한다
[S: `docs/kb/hybrid/runtime.md` section 2]. 메인 RAM은 두 번의 할당이 아니라 하나의 4 MB 파일 매핑을
두 번 바라보는 것이므로, `0x023fxxxx` / `0x027fxxxx` 별칭이 계속 동작한다
[H: host/prose inference from `port/platform/win32.c:78-86`; verify against the ROM function or symbol table and this page's recipe]. I/O 페이지는 훅이 개입하는 곳을 제외하면 평범한 호스트
메모리이며, 그래서 ROM이 폴링하는 레지스터는 스스로 바뀌지 않는다 — 이것이 세 가지
부류의 멈춤(stall)의 근원이다 [S: `docs/kb/hybrid/runtime.md` section 2].

## 어디에 있는가

| 함수 또는 심볼 | 모듈 | 역할 | 등급 / 출처 |
|---|---|---|---|
| `OS_GetArenaLo` (`0x02115ef4`) / `OS_GetArenaHi` (`0x02115f08`) | autoload_2 | 아레나의 현재 경계 | [S: `port/shim/boot/heapinit.c` header] |
| `OS_AllocFromArenaLo` (`0x02115c28`) | autoload_2 | 낮은 쪽 끝에서 블록을 가져간다 | [S: `port/shim/boot/heapinit.c` header] |
| `OS_GetInitArenaHi` | autoload_2 | 아레나 상한, 메인 아레나는 `0x023e0000` | [S: `port/shim/os/arenahi.c` header] |
| `func_020ea48c` | autoload_2 | 게임 힙을 잘라낸다; 초기화의 마지막 호출 | [S: `port/shim/boot/heapinit.c` header] |
| `func_020ea50c` / `func_020ea298` | autoload_2 | 블록 + 0x30에 확장 힙을 만든다 | [S: `port/shim/boot/gameheap.c` header] |
| `func_020ea41c` | autoload_2 | 블록/힙 배치를 0x30 헤더에 기록한다 | [S: `port/shim/boot/gameheap.c` header] |
| `NNS_FndCreateExpHeapEx` | main | NNS 확장 힙 생성자 | [S: `port/shim/boot/gameheap.c:34`] |
| `MIi_UncompressBackward` | autoload_2 | 역방향 압축된 이미지를 제자리에서 푼다 | [S: `port/shim/fs/ovlreloc.c:56`] |

## 읽고 쓰는 데이터

| 주소 | 의미 | 쓰는 쪽 | 읽는 쪽 |
|---|---|---|---|
| `0x021fbe90` | 설정된 게임 힙 크기; 0 = 아레나의 나머지 | ROM 데이터 | `func_020ea48c` [S: `port/shim/boot/heapinit.c` header] |
| `0x021fbe98` | 할당할 아레나 id; 항상 0으로 설정 | `func_020ea48c` | `func_020ea48c` [S: same] |
| `0x021fbe78` / `0x021fbe8c` / `0x021fbe94` | 게임 힙 패밀리의 풀 워드 | `func_020ea50c` / `func_020ea298` | 할당자 [S: `port/shim/boot/gameheap.c:40-43`] |
| `data_0213e5a4` | 확장 힙 생성 시 사용되는 옵션 플래그 | ROM 데이터 | `func_020ea50c` [S: `port/shim/boot/gameheap.c:33-34`] |
| `0x027e0000` | `OS_IRQTable[0]`, VBlank 핸들러 슬롯 | `OS_SetIrqFunction` | 인터럽트 벡터 [S: `port/shim/os/vblank.c:80`] |
| `0x027e0394 + tag*4` | PXI 수신 콜백 테이블 | `PXI_SetFifoRecvCallback` | PXI 전달 [S: `docs/kb/hybrid/hardware-services.md` section 1] |
| `0x027ffc20` | 부팅 플래그; 1이면 두 번째 부팅 경로를 선택 | `NitroMain` 이전 | `NitroMain` [S: `port/platform/nitromain.c:50, 77`] |
| `0x027fff9c` | crt0가 쓰는 인터럽트 벡터 슬롯 | `Entry` | 벡터 [S: `port/platform/win32.c:79-80`] |
| `0x04000208` (`REG_IME`) | 인터럽트 마스터 활성화 | `NitroMain` | 인터럽트 컨트롤러 [S: `port/platform/nitromain.c:49`] |
| `0x04000004` | 하위 절반 `DISPSTAT`, 상위 절반 `VCOUNT` | 디스플레이 컨트롤러 | ROM 대기 루프; 포트가 합성한다 [S: `docs/kb/hybrid/hardware-services.md` section 4] |
| `0x04000280`-`0x040002bf` | 나눗셈 및 제곱근 유닛 | `FX_Div` / `FX_Sqrt` | 같은 함수, 읽을 때 [S: `docs/kb/hybrid/hardware-services.md` section 3] |
| `0x04000400`-`0x040005ff` | GX FIFO와 명령 포트 | 지오메트리 제출 경로 | 지오메트리 엔진 [S: `docs/kb/hybrid/hardware-services.md` section 5] |
| `0x04000640` / `0x04000680` | `CLIPMTX_RESULT` (16워드) / `VECMTX_RESULT` (9워드) | 지오메트리 엔진 | `G3X_GetClipMtx` / `G3X_GetVectorMtx` [S: `docs/kb/hybrid/hardware-services.md` section 5] |

## 확인 방법

어떤 실행이든 시작 시 포트의 영역 보고를 출력하며, 각 예약 영역과 그 크기를 이름으로 나열하고,
고정 기준 주소 예약이 실패하면 계속 진행을 거부한다
[H: host/prose inference from `port/platform/win32.c:1-25, 97-112`; verify against the ROM function or symbol table and this page's recipe]. 매핑이 실제 주소에 있으므로, 오류 보고의
주소는 심볼 테이블 행과 직접 비교할 수 있다: 모듈은 그 `config/adm-kr/arm9/**/symbols.txt`가
가장 가까운 아래쪽 `addr:0x...`를 담고 있는 것이다
[S: `config/adm-kr/arm9/**/symbols.txt`].

살아 있는 메모리에 관한 질문에는 인터프리터가 두 가지 계측 도구를 제공한다: `ACWW_INTERP_WATCH=<hex>`는
한 주소에 대한 저장 워치포인트이고, `ACWW_INTERP_PEEK=<hex,...>`는 매 덤프마다 해당 워드들을
출력한다 [S: `docs/log/cycle40-keyboard-gate-probe.md` CARD40..SND40, "Instruments added
this stretch"].

## 가설

- 포트가 올린 아레나 상한(`0x023e0000` 대신 `0x023f0000`)은 게임 동작에는 관측 가능한
  영향이 없고, 누수가 숨을 수 있는 여유 공간의 크기에만 영향을 준다 [H: settled by running
  the town recipe with the concession removed and comparing frames and heap-free traces;
  the file itself asks to be deleted the day the leak is found —
  `port/shim/os/arenahi.c` header].
- `autoload_3`와 `dtcm`은 데이터만 담고 있으며, 그래서 그 심볼 테이블에 함수 이름이
  없다 [H: settled by checking whether any branch target in another module resolves into
  their address ranges].
- `0x021cxxxx` 띠는 씬마다 해체되고 다시 만들어지는 씬 수명의 상태이고,
  `0x021fxxxx`는 부팅 수명이다 [H: settled by watching one address from each band across a
  scene change and recording whether it is rewritten].
- 도달 가능한 게임 코드 중 DMA 레지스터를 되읽는 것은 없으며, 그래서 포트는 DMA 레지스터
  되읽기를 에뮬레이션하지 않는다 [H: settled by a load watchpoint over `0x040000b0`-`0x040000ef`
  on the town recipe; the port's position is that such a read should hang loudly rather than
  silently work — `docs/kb/hybrid/hardware-services.md` section 7].

## 관련 문서

- `boot-and-entry.md` — 힙을 잘라내는 초기화 호출
- `threads-and-interrupts.md` — DTCM 맨 아래에 있는 것
- `display-objects.md` — `0x021fdxxx` 리스트 헤드와 이를 순회하는 것
- `overlays.md` — 오버레이 띠와 그곳의 주소가 모호한 이유
