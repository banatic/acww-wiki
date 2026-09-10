# 디스플레이 오브젝트
<!-- source: wiki/engine/display-objects.md -->

**요약.** 게임이 그리거나 스텝하는 모든 것은 "디스플레이 오브젝트(display object)"이다: 두 개의
리스트 노드를 소유하고 네 개의 전역 리스트 — 초기화, 업데이트, 그리기, 파괴 — 중 하나에 존재하는 C++ 오브젝트이다.
프레임마다 한 번씩 스테퍼가 각 리스트를 순회하며 발견하는 모든 오브젝트에 대해
멤버 함수 포인터를 호출한다. 각 스테퍼는 고정된 패턴으로 세 개의 vtable 슬롯을 구동한다: 동작 여부를
결정하는 술어(predicate), 작업 자체, 그리고 무슨 일이 있었는지 통보받는 핸들러이다. 오브젝트는
채널 생성자에 의해 만들어지고, 대기 리스트에 join되고, 실제 리스트에 commit되며, 게이트가 열릴
때까지 매 스텝 거부된다. 씬은 존재하는데 아무것도 움직이지 않는다면, 그 게이트가
읽어야 할 대상이다.

## 무슨 일이 일어나는가

### 네 개의 리스트

네 개의 리스트 헤드가 메인 RAM에 인접하여 위치한다: `0x021fd004`, `0x021fd014`, `0x021fd024`,
`0x021fd034` [S: `port/shim/gfx/dispstep.c:28-30, 55-58`]. 이것들은 역참조할 포인터가 아니라
주소(ADDRESS) 자체이다 — ROM은 각각을 PC 상대 리터럴 로드로 적재하고 리스트 호출에
그대로 넘긴다 [S: `port/shim/gfx/dispstep.c:29-31`]. 그 역할은 초기화 리스트
(`0x021fd014`), 업데이트 리스트(`0x021fd004`), 그리기 리스트(`0x021fd024`), 파괴
리스트(`0x021fd034`)이다 [S: `port/shim/gfx/commit.c:22-24`; `port/shim/gfx/dispsteppers.c:24-28`].

### 네 개의 스테퍼와 3슬롯 패턴

각 리스트에는 자체 스테퍼가 있으며, 넷 모두 같은 형태이다: 리스트 오브젝트와 함수의 리터럴 풀에서
읽어 낸 세 개의 멤버 포인터를 넘기는 `func_01ffd44c` 호출이다
[S: `port/shim/gfx/dispsteppers.c:10-18`]. `func_01ffd44c`는 세 번째(THIRD) 매개변수를 먼저 호출하고,
그 다음 두 번째(SECOND), 마지막으로 네 번째(FOURTH)를 호출하며, 두 번째의 반환값에서 파생된 마커를 넘긴다
[S: `port/shim/gfx/dispsteppers.c:16-18`].

어떤 재구성본의 매개변수 이름이 아니라 풀 워드에서 읽어 낸 것이다
[S: `port/shim/gfx/dispsteppers.c:20-31`, from `extract/adm-kr/arm9/itcm.bin` and
`unk_autoload_2.bin`]:

| 스테퍼 | 리스트 | 두 번째 매개변수 | 세 번째 매개변수 | 네 번째 매개변수 |
|---|---|---|---|---|
| `func_020ede60` | `0x021fd014` (init) | vtable 슬롯 0 | 슬롯 1 | 슬롯 2 |
| `func_01ffd14c` | `0x021fd004` (update) | 슬롯 6 | 슬롯 7 | 슬롯 8 |
| `func_01ffd0e4` | `0x021fd024` (draw) | 슬롯 9 | 슬롯 10 | 슬롯 11 |
| `func_020edddc` | `0x021fd034` (destroy) | 슬롯 3 | 슬롯 4 | 슬롯 5 |

하나의 패턴이 네 번 반복된다: 가운데 슬롯은 술어(PREDICATE)이며 먼저 실행되고, 낮은 슬롯은
작업(WORK)이며 성공 시 1을 반환하고, 높은 슬롯은 핸들러(HANDLER)이며 작업이 1을 반환했을 때
2를 받으며 진입한다 [S: `port/shim/gfx/dispsteppers.c:32-36`]. 이 규칙성이 이
해석이 옳다는 논거이다 — 다른 해석은 네 그룹 모두에 같은 순열을 아무 목적 없이
적용하는 셈이다 [S: `port/shim/gfx/dispsteppers.c:36-40`]. 이 열두 개의 멤버 포인터 모두
this 조정값이 0이다 [S: `port/shim/gfx/dispsteppers.c:41-43`].

구체적인 결과 하나: `func_020a553c`는 슬롯 5이며, `func_020a536c`가 새 씬 로드를
거부하는 데 쓰는 바이트를 지우고, 두 번째 인수가 2일 때만 동작한다 — 이것이 바로
네 번째 매개변수가 받는 값이다 [S: `port/shim/gfx/dispsteppers.c:32-38`].

바이트 매칭으로는 어떤 풀 워드가 무엇인지 확정할 수 없는데, 하네스가 리터럴 풀
재배치를 마스킹하기 때문이다: 풀에서 세 개의 데이터 주소를 로드하는 함수는 세 이름의
어떤 순열에서도 바이트 동일하다 [H: host/prose inference from `port/shim/gfx/dispsteppers.c:8-14`; verify against the ROM function or symbol table and this page's recipe].

### 순회 자체

`func_020ee834`가 리스트 순회이다
[S: `func_020ee834`, autoload_2, `port/shim/gfx/pmflist.c` header]. 그 인수는
리스트 헤드와 2워드
멤버 함수 포인터를 담고 있다; 각 노드의 오브젝트를 가져와 그것에 멤버 포인터를 호출한다
[S: `func_020ee834`, autoload_2, `port/shim/gfx/pmflist.c` header and `:104-118`]. 이 네 리스트 중
하나에 있는 노드는 3워드이다 — 이전, 다음, 그리고 오브젝트로의 역포인터
[S: `port/shim/gfx/pmflist.c:106-119`]. `0x021fcff8`에 다섯 번째(FIFTH) 리스트가 있으며, 그 노드는
각 디스플레이 오브젝트의 `+0x14`에 있는 `sub` 블록이고 레이아웃이 다르다; `func_020ee9a0`은
네 리스트를 `func_020ee834`로 순회하고 그 다섯 번째는 자체 순회로 처리한다
[S: `port/shim/gfx/pmflist.c:961-972`].

순회의 두 가지 속성은 ROM의 것이며 필수적이다: `next`는 호출 전(BEFORE)에 읽는데,
호출이 자기 대상 노드를 언링크할 수 있기 때문이다; 그리고 현재 노드는 루프 전과 각 스텝 후에
`0x021fcff4`에 공개되는데, 콜백이 실행되는 동안 다른 무언가가 이를 읽기 때문이다
[S: `port/shim/gfx/pmflist.c:36-39, 726-729`].

멤버 포인터는 mwcc의 2워드 레이아웃이며, 이 함수 자체의 명령어들이 조정값을 적용하며
디코딩되는 모습을 보여 준다: 워드 0은 함수 주소이거나 vtable
바이트(BYTE) 오프셋이고, 워드 1은 `(delta << 1) | isVirtual`이다 — 비트 0이 가상 여부를 선택하고,
this 포인터는 오브젝트에 워드 1을 산술적으로 오른쪽 1비트 시프트한 값을 더한 것이다
[S: `func_020ee834`, autoload_2, `port/shim/gfx/pmflist.c:22-34`]. 이것은 그 레이아웃의
세 번째 독립적 확인이며, 조정값이 사용되는 모습을 보여 주는 유일한 것이다
[S: `port/shim/gfx/pmflist.c:22-24`].

### 오브젝트별 스텝: 재구축 또는 동기화

프레임별 상태 스텝은 `func_01ffd1b4`로, `itcm`의 0x230바이트 ARM 코드이며, 오브젝트의 vtable을 통해
`func_020ee934 -> func_020ee9a0 -> func_020eea4c`로 프레임마다 오브젝트당 한 번
도달된다 [S: `func_01ffd1b4`, itcm,
`port/shim/gfx/dispstep.c` header]. 두 부분으로 되어 있다
[S: `port/shim/gfx/dispstep.c:19-27`]:

- `+0x0f`의 더티 바이트가 설정되어 있으면 재구축(REBUILD): 오브젝트의 두 노드(`+0x28`과
  `+0x38`)를 그것들을 담고 있는 리스트에서 언링크하고, 첫 번째를 다시 링크하고,
  `+0x18` 리스트의 모든 자식을 같은 처리가 필요하다고 표시한다;
- 그렇지 않으면 동기화(SYNC): `func_020ee45c`가 반환하는 오브젝트에서 두 플래그 비트를 내려 복사하고,
  `+0x0e`의 정렬 키가 `+0x0c`에 있는 마지막 정렬 시 키와 더 이상 일치하지 않는
  노드 각각을 다시 정렬한다.

노드의 `+0x0e` 상태 바이트는 1(라이브, 정렬됨)에서 2(재구축 중)로 갔다가 돌아온다
[S: `port/shim/gfx/dispstep.c:32-35`]. 이 바이트들을 단일 enum으로 읽는 것은 틀렸다:
`0x01ffd35c`는 특별히 2인지를 검사하고 그 외에는 그냥 통과시키므로, 네 번째 값이
가능하며 아무것도 하지 않음으로써 처리된다 [S: `port/shim/gfx/dispstep.c:33-35`].

### join과 commit

`func_020edec8`은 새로 만들어진 디스플레이 오브젝트를 대기 리스트에 넣는 훅이며,
거절하는 방법이 네 가지로 구분된다: 오브젝트가 준비되지 않았다는 플래그 둘, 이미 라이브라는
플래그 하나, 그리고 현재 실행 중인 순회가 잘못된 것이라는 플래그 하나이다
[S: `func_020edec8`, autoload_2, `port/shim/gfx/dispjoin.c` header]. `func_020ee59c`는
commit이며, ROM에서 `+0x10`의 지연(deferral) 바이트를 쓰는 유일한 함수이다
[S: `func_020ee59c`, autoload_2, `port/shim/gfx/commit.c` header, body from
`src/matched/func_020ee59c.c`]. commit의 동작은 `0x0213e7fc`의 전역 워크 모드에
따라 달라진다 [S: `port/shim/gfx/commit.c:21, 64`]. 모드 3이 라이브인 동안 commit하면
바로 그 리스트가 순회되는 도중에 `0x021fd004`에 추가한다
[S: `port/shim/gfx/commit.c:58-63`].

### 모든 스텝 앞에 있는 게이트

`func_01ffd41c`는 여섯 명령어와 하나의 검사이다: 스텝은 오브젝트의
`+0x0f`가 클리어이고(AND) `+0x13`의 비트 1이 클리어일 때만 일어난다 [S: `func_01ffd41c`, itcm,
`port/shim/gfx/dispgate.c` header]. `+0x0f`는 디스플레이 스텝이 쓰고 `+0x13`은
생성자가 부모의 값을 복사하며 쓴다 [S: `port/shim/gfx/dispgate.c:10-12`].

그 게이트의 상류에는 하나의 술어가 있다: `func_020edd74`는 `func_01ffcfc0`을 끝 센티널로,
`func_01ffcffc`를 후속자로 하여 자식 리스트를 순회함으로써 "내 자식 중 아직 라이브가 아닌 것이
있는가?"에 답한다 [S: `func_020edd74`, autoload_2,
`port/shim/gfx/childlive.c` header, body from `src/matched/func_020edd74.c`]. 답이
1이면 `func_020a5430`은 씬의 `+0x13` 비트 0을 설정된 채로 둔다; 생성자는 비트 0을
모든 자식에게 비트 1로, 비트 2를 비트 3으로 전파한다; 그러면 게이트는 서브트리 전체에 대해
모든 스텝을 거부한다 [S: `port/shim/gfx/childlive.c:7-16`]. `+0x13 = 0x05`인 씬 오브젝트는
자식에게 `0x0a`를 주고, `0x0a`는 거부된다 [S: `port/shim/gfx/childlive.c:17-19`].

### VBlank 태스크 리스트

네 리스트와 별도로 `0x021f6ca0`에 VBlank 태스크 리스트가 있으며, `func_020b98ec`가 순회한다
[S: `port/shim/gfx/vbtask.c:22-25`]. 각 태스크의 노드는 자기 오브젝트의 4바이트 안쪽에 위치하고, 각각은 VBlank 안에서
vtable 슬롯 0을 통해 실행된다 [S: `func_020b98ec`, main, `port/shim/gfx/vbtask.c` header, body from
`src/matched/func_020b98ec.cpp`]. ROM에는 거기에 null vtable 검사가 없는데, NDS에서는
null 읽기가 ITCM 미러 바이트를 반환하기 때문이다 [S: `port/shim/gfx/vbtask.c:8-11`].

### 그리기

오브젝트가 거치는 그리기 경로는 `func_02055e7c`이며, `func_02055e10`을 통해 오브젝트의 카메라 상태를
설정한 다음 `func_02055e04`로 그린다
[S: `func_02055e7c`, main, `port/shim/gfx/drawobj.c` header]. `func_02055e10`은 두 번째 인수로
스케일을 받으며(null 스케일은 단위 스케일을 선택한다) `NNS_G3dGlbFlushP`로 끝나는데, 이것이
실제로 카메라와 투영 상태를 지오메트리 엔진에 업로드하는 것이다
[S: `port/shim/gfx/drawobj.c:1-16`].

두 오브젝트는 이름을 밝혀 둘 만한데, 상수로는 어떤 것도 그것들을 가리킬 수 없기 때문이다 — 그
할당 위치가 실행마다 바뀐다. 첫 번째는 채널 189의 오브젝트로, vtable `0x022382ac`이다; 지오메트리는
그 `+0x5c`를 기준으로 그려진다 [S: `port/shim/gfx/pmflist.c:52-56`]. **그 오브젝트는
마을의 필드 렌더러가 아니라 눈사람(SNOWMAN)이며**, 포트 자체의 심 헤더가 아직 달고 있는
"필드 렌더러" 라벨은 철회된 오식별이다: 채널 189의 바인드 로그는
`/snowman/snowball1.nsbmd`(`SNW0`, id `0x022383ac`)와 `/snowman/snow_face.nsbmd`(`SNW1`,
id `0x022383c8`)를 이름 짓고, 두 문자열 모두 `ov003`의 해당 주소에 상주한다
[E: `port/BOOT-STATE.md:1159-1171`, "CHANNEL 189 IS THE SNOWMAN"; see `../systems/town.md`].
필드 카메라(FIELD CAMERA)의 vtable은 `0x020da87c`이고 그 그리기
슬롯 `func_0203c610`은 투영 행렬과 뷰 행렬을 모두 설정하며, `at`을 `+0x188`에서,
`eye`를 `+0x194`에서, `up`을 `+0x1a0`에서, near를 `+0x1b0`에서, far를 `+0x1b4`에서, 시야각
인덱스를 `+0x1c8`에서 읽는다 [S: `port/shim/gfx/pmflist.c:59-63, 184-190`].

### 프레임워크는 하나의 서브시스템이다 — 포팅에서 얻은 교훈

PC 포트에서 디스플레이 오브젝트 프레임워크는 손으로 작성한 호스트 코드 29개 파일에 걸쳐 있으며,
그중 일부(SUBSET)만 ROM에 거부하면 부팅이 멈춘다: ROM의 순회는 인터프리트되지만
네이티브 join과 commit이 여전히 링크되어 네이티브 VBlank 핸들러에서 호출되는 상태에서는, join이
순회가 기대하는 것을 거부하여 아무것도 업데이트 리스트에 들어가지 못했다 — 닌텐도 로고에서
36,000개의 동일한 프레임이다 [E: `docs/log/cycle40-keyboard-gate-probe.md` REG40b and REG40c]. 29개 모두를 거부하면
통과한다 [E: same]. 이 규칙은 일반화된다: 프레임워크는 하나의 서브시스템이며,
ROM의 것이거나 포트의 것이지, 결코 반반이 아니다 [E: `docs/kb/hybrid/runtime.md` section 5].

업데이트 리스트가 죽는 측정된 증상은 조용하다: 마을이 계속 그려지는 동안 업데이트 리스트가
프레임 0에서 한 번 순회되고 다시는 순회되지 않는 실행이다
[H: host-source account from `port/shim/gfx/pmflist.c:696-700`, the per-list pass counters; verify with a retained scripted run and frame using this page's recipe].

## 어디에 있는가

| 함수 또는 심볼 | 모듈 | 역할 | 등급 / 출처 |
|---|---|---|---|
| `func_020ee834` | autoload_2 | 디스플레이 리스트 순회; 멤버 함수 포인터를 인라인으로 디코딩 | [S: `port/shim/gfx/pmflist.c` header] |
| `func_01ffd44c` | itcm | 오브젝트당 세 슬롯 실행: 술어, 작업, 핸들러 | [S: `port/shim/gfx/dispsteppers.c:16-18`] |
| `func_020ede60` / `func_01ffd14c` / `func_01ffd0e4` / `func_020edddc` | autoload_2, itcm | init / update / draw / destroy 스테퍼 | [S: `port/shim/gfx/dispsteppers.c:24-28`] |
| `func_01ffd1b4` | itcm | 오브젝트별 재구축 또는 동기화 상태 스텝 | [S: `port/shim/gfx/dispstep.c` header] |
| `func_020ee934` / `func_020ee9a0` / `func_020eea4c` | autoload_2 | 오브젝트별 스텝에 도달하는 체인 | [S: `port/shim/gfx/dispstep.c:17-19`] |
| `func_01ffd41c` | itcm | 게이트: `+0x0f` 클리어 및 `+0x13` 비트 1 클리어 | [S: `port/shim/gfx/dispgate.c` header] |
| `func_020edd74` | autoload_2 | "아직 라이브가 아닌 자식이 있는가?" | [S: `port/shim/gfx/childlive.c` header] |
| `func_01ffcfc0` / `func_01ffcffc` | itcm | 리스트 끝 센티널과 후속자 | [S: `port/shim/gfx/childlive.c:22-23`] |
| `func_020edec8` | autoload_2 | 대기 리스트에 join; 거절 방법 넷 | [S: `port/shim/gfx/dispjoin.c` header] |
| `func_020ee59c` | autoload_2 | commit; `+0x10` 지연 바이트의 유일한 쓰기자 | [S: `port/shim/gfx/commit.c` header] |
| `func_020e8ce0` / `func_020e8c70` / `func_020ee8a8` | autoload_2 | 언링크, 추가, 정렬 순서 삽입 | [S: `port/shim/gfx/dispstep.c:44-47`] |
| `func_020ee45c` / `func_020ee470` | autoload_2 | 동기화가 플래그 비트를 복사해 오는 오브젝트 | [S: `port/shim/gfx/dispstep.c:48-49`] |
| `func_020b98ec` | main | VBlank 태스크 리스트 순회 | [S: `port/shim/gfx/vbtask.c` header] |
| `func_02055e7c` / `func_02055e10` / `func_02055e04` | main | 카메라 상태 설정 후 그리기 | [S: `port/shim/gfx/drawobj.c` header] |
| `NNS_G3dGlbFlushP` | main | 카메라와 투영을 지오메트리 엔진에 업로드 | [S: `port/shim/gfx/drawobj.c:11-13`] |
| `func_0203c610` | main | 필드 카메라의 그리기 슬롯: 투영과 뷰 | [S: `port/shim/gfx/pmflist.c:59-61`] |
| vtable `0x022382ac` | ov003 | 채널 189의 오브젝트 — 필드 렌더러가 아니라 눈사람(SNOWMAN) | [H: source/log account from `port/BOOT-STATE.md:1159-1171`; verify with a retained run using this page's recipe] |

## 읽고 쓰는 데이터

| 주소 또는 필드 | 의미 | 쓰는 쪽 | 읽는 쪽 |
|---|---|---|---|
| `0x021fd014` | 초기화(INITIALISE) 리스트 헤드 | join/commit | `func_020ede60` [S: `port/shim/gfx/commit.c:22`] |
| `0x021fd004` | 업데이트(UPDATE) 리스트 헤드 | join/commit | `func_01ffd14c` [S: `port/shim/gfx/commit.c:23`] |
| `0x021fd024` | 그리기(DRAW) 리스트 헤드 | join/commit | `func_01ffd0e4` [S: `port/shim/gfx/commit.c:24`] |
| `0x021fd034` | 파괴(DESTROY) 리스트 헤드 | join/commit | `func_020edddc` [S: `port/shim/gfx/dispsteppers.c:28`] |
| `0x021fcff4` | 순회가 지금 스텝 중인 노드 | `func_020ee834` | 콜백 실행 중 무언가가 읽음 [S: `port/shim/gfx/pmflist.c:36-39`] |
| `0x0213e7fc` | 전역 워크 모드; 3이면 commit을 지연 | 스테퍼들 | `func_020ee59c` [S: `port/shim/gfx/commit.c:21, 64`] |
| `0x021f6ca0` | VBlank 태스크 리스트 헤드 | 태스크 등록 | `func_020b98ec` [S: `port/shim/gfx/vbtask.c:22-25`] |
| 오브젝트 `+0x0f` | 더티 바이트: 재구축 요청; 스텝의 게이트 역할도 함 | 디스플레이 스텝 | `func_01ffd1b4`, `func_01ffd41c` [S: `port/shim/gfx/dispstep.c:21`, `dispgate.c` header] |
| 오브젝트 `+0x10`, `+0x11` | 두 개의 요청 바이트, 소비 후 클리어됨 | `func_020ee59c`가 `+0x10`을 씀 | `func_01ffd1b4` [S: `port/shim/gfx/dispstep.c:32-33`] |
| 오브젝트 `+0x13` | 플래그 비트; 비트 1은 스텝을 거부하며 자식에게 전파됨 | 생성자, `func_020a5430` | `func_01ffd41c` [S: `port/shim/gfx/childlive.c:7-16`] |
| 오브젝트 `+0x18` | 자식 리스트 | 생성자 | `func_020edd74`, 재구축 [S: `port/shim/gfx/dispstep.c:21-23`] |
| 오브젝트 `+0x28`, `+0x38` | 오브젝트의 두 리스트 노드 | join/commit | 재구축 [S: `port/shim/gfx/dispstep.c:21-22`] |
| 노드 `+0x0c`, `+0x0e` | 마지막 정렬 키와 현재 정렬 키 | 동기화 | 재정렬 [S: `port/shim/gfx/dispstep.c:25-26`] |
| 필드 카메라 `+0x188` / `+0x194` / `+0x1a0` / `+0x1b0` / `+0x1b4` / `+0x1c8` | at, eye, up, near, far, fov 인덱스 | 카메라 자체 로직 | `func_0203c610` [S: `port/shim/gfx/pmflist.c:184-190`] |

## 확인 방법

`docs/kb/hybrid/recipes.md`의 아무 레시피나 `ACWW_TRACE_STATE`를 설정하고 실행한 뒤, 포트가 순회 내부에서
출력하는 세 가지 계측을 읽는다: 600프레임마다 출력되는 `acww passes: frame N init=... update=...
draw=... destroy=...`는 멈춘 패스를 멈춘 카운터로
보이게 한다 [S: `port/shim/gfx/pmflist.c:696-722`]; `acww listwalk: list ... node
... back-pointer ... is not an object`는 링크되어 있지만 오브젝트 워드가
메인 RAM이 아닌 노드를 지목한다 [S: `port/shim/gfx/pmflist.c:731-757`]; 그리고 `acww camnf: obj ... near ... far
...`는 필드 카메라의 near/far 쌍이 바뀔 때마다 출력된다
[S: `port/shim/gfx/pmflist.c:203-232`].

"프레임워크가 실행 중이다"에 대한 반증 관측은 업데이트 리스트 카운터이다:
`draw=`는 계속되는데 `update=`가 진행을 멈추면, 오브젝트는 그려지고 있지만 아무것도
스텝되고 있지 않은 것이다 [H: host-source account from `port/shim/gfx/pmflist.c:696-700`; verify with a retained scripted run and frame using this page's recipe].

## 가설

- (해결됨, 기록용으로 유지.) 노드의 오브젝트 역포인터를 두고 `+0x08`과 `node+0x10`이
  불일치한 것은 하나의 모순이 아니라 두 종류의 서로 다른 노드였다. `func_020ee834`의
  네 리스트는 오브젝트가 `+0x08`에 있는 3워드 노드 `{prev, next, obj}`를 사용한다
  [S: `port/shim/gfx/pmflist.c:106-119`]. `0x021fcff8`의 다섯 번째(FIFTH) 리스트 — 노드가 각 디스플레이
  오브젝트의 `+0x14`에 있는 `sub` 블록이고 `func_020ee9a0`이 순회하는 — 는 `head`가 `+0`에,
  멤버 포인터가 `+4`/`+8`에, 오브젝트가 `node+0x10`에 있으며, 콜백이 노드를 언링크할 수 있기
  때문에 필드를 로드하는 대신 `func_01ffcffc(node)`를 호출(CALLING)하여 `next`를 얻는다
  [S: `port/shim/gfx/pmflist.c:961-981`, read off the ROM's instructions].
- `+0x28`과 `+0x38`의 두 노드는 자유로운 쌍이 아니라 고정된 리스트 쌍에 대한 "리스트 X 위의 이 오브젝트"와
  "리스트 Y 위의 이 오브젝트"이다 [H: settled by logging, per object, which list
  head each of its two nodes is linked into across a scene change].
- `+0x0e`의 노드 상태 바이트의 네 번째 값은 원리상만이 아니라 실제 플레이에서도 존재한다
  [H: settled by a watchpoint on that byte over the town recipe, recording every distinct
  value].
- 열두 개의 스테퍼 슬롯 하나하나가 적어도 하나의 라이브 클래스에 의해 채워져 있다 [H: settled by
  counting dispatches per slot over the town recipe with the per-object trace already in
  `port/shim/gfx/dispsteppers.c`].

## 관련 문서

- `scenes-and-channels.md` — 이 오브젝트들을 생성하는 것, 그리고 게이트 위의 게이트
- `threads-and-interrupts.md` — 태스크 리스트가 그 안에서 실행되는 VBlank
- `memory-map.md` — `0x021fdxxx` 리스트 대역
- `overlays.md` — 오버레이 언로드가 쓸어 내는 소멸자 체인
