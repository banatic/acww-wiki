# 씬과 채널
<!-- source: wiki/engine/scenes-and-channels.md -->

**요약.** 디스플레이 오브젝트 프레임워크 위에는 씬(scene) 머신이 있다 — 각 씬이 "채널"의 목록을
소유하는 번호가 매겨진 상태 머신이다. 채널(channel)은 번호가 매겨진 기능(지면, 필드 렌더러,
파티클 시스템, 위젯)으로, 세 단계 시퀀스를 통해 열리고 이중 간접 핸들러 테이블을 통해
디스패치된다. 야외 필드 씬인 씬 6은 필요한 만큼의 프레임에 걸쳐 여섯 스테이지로 로드되며,
다섯 번째 스테이지가 리소스 항목을 순회하는 스테이지다. 한 슬롯짜리 메일박스와 게임 모드 바이트가
씬 사이의 모든 전환을 게이트한다; 게임이 진행되지 않을 때, 그 둘이 가장 먼저 읽어야 할
것이다.

## 무슨 일이 일어나는가

### 최상위 씬 머신

`func_020a636c`가 게임의 최상위 씬 머신이며, 그 상태는 자기 객체의 오프셋 24에 있는 워드 하나다
[S: `func_020a6688` / `func_020a636c`, main,
`port/shim/game/scenestate.c` header, body from `src/matched/func_020a6688.c`]. 세터는
`func_020a6688`이고 게터는 `func_020a6684`인데, 게터는 매 스텝마다 호출되므로
머신의 틱을 보는 유일한 장소다 [S: `port/shim/game/scenestate.c:30-40`].
관측된 상태의 순서는 16, 그다음 0, 1, 2, 그리고 위로 올라간다
[E: `port/shim/game/scenestate.c` header, from the port's `acww scenest:` trace].

상태 16의 본체 전체는 하나의 가드다: 씬 id `data_020e3c80`이
5와 같지 않으면 반환한다 [S: `port/shim/game/scenestate.c:31-34`]. 따라서 하나의 상태를 설정하고 멈추는
머신은 결코 열리지 않는 가드를 가진 것이며, 상태 트레이스가 어느 것인지 이름 짓는다
[E: same instrument].

### 씬 6의 여섯 스테이지 로더

씬 6의 초기화는 `func_020b6c0c`로, 호출당 한 스테이지를 실행하며 모든 스테이지가 0이 아닌 값을
반환할 때까지 — 또는 프레임의 40 ms가 소비될 때까지, 둘 중 먼저 오는 쪽까지 —
"끝나지 않음"(-1)을 보고하는 단계적 로더다 [S: `func_020b6c0c`, main,
`port/shim/game/scene6init.c` header]. 스테이지들은 함수 지역 정적 변수에 담긴 멤버 함수
포인터이며, 스테이지 카운터는 `0x021f42f0`의 바이트로 씬에 진입할 때 `func_020a5598`이
지운다 [S: `port/shim/game/scene6init.c` header].

스테이지 4는 채널을 여는 서브스테이지 목록이다
[E: `port/shim/game/chanvector.c` header, narrowed by elimination on the native path].
스테이지 5는 `func_020b0b00`을 실행하는데, 이는 리소스 항목을 순회하며 각 항목에 대해
`data_020e41ec[e->b0]`를 디스패치하는 루프다; 0을 반환하는 핸들러는 "끝나지 않았으니 다음 프레임에
다시 오라"는 뜻이다 [S: `func_020b0b00`, main, `port/shim/game/stageloop.c` header, body from
`src/matched/func_020b0b00.c`]. 스테이지 6은 ROM에서 시퀀서 메일박스를 지우는 유일한 것으로,
`func_020b5e88`을 통해 지운다
[S: `docs/kb/port/sequencer-and-modes.md`, LEGACY-NATIVE page describing the ROM's mechanism].

씬 6의 프레임별 업데이트 슬롯은 `func_020b6a7c`이며, `0x021c75b8`의 바이트가 2이거나
`0x021c75b0`의 바이트가 0이 아닌 경우가 아니면 즉시 — 아무것도 하지 않고 — 반환한다
[S: `func_020b6a7c`, main, `port/shim/gfx/pmflist.c:122-131`]. 마을 이후의 모든 것이
그 두 바이트를 기다린다: 씬이 결코 바뀌지 않으므로, 열네 항목짜리 마을 채널 목록 전체를
순회하는 레코드 배열이 결코 설치되지 않는다
[S: `port/shim/gfx/pmflist.c:124-129`].

### 씬별 채널 목록

`func_020b0bbc`는 씬의 채널 목록을 순회한다: 두 하프워드 항목의 배열로, 개수는 객체의 두 번째
바이트에 있고 재개 인덱스가 인자로 전달된다 [S: `func_020b0bbc`, main,
`port/shim/game/chanlist.c`, body from `src/matched/func_020b0bbc.c`]. 순회는
시간 제한이 있다 — 프레임의 40 ms 후에 포기하고 다음번에 재개한다 — 그래서 "테이블에 id N이
없다"와 "순회가 거기까지 가지 못했다"는 밖에서 보면 똑같아 보인다
[S: `port/shim/game/chanlist.c` header]. 씬 6은 상수가 아니라 그 테이블에서 채널을 연다:
필드 렌더 객체인 id 189는 ROM 어디에도 즉시값(immediate)으로 등장하지 않는다
[S: `port/shim/game/chanlist.c` header].

### 채널 열기: 세 단계

정문은 `func_0202f134`로, 모든 씬의 채널 목록이 이를 거치며 네 개의 인자로 호출을
구성한다 [S: `func_0202f134`, main,
`port/shim/game/chanopen.c` header]. 이는 `func_020edbbc`로 전달되는데, 핸들러 레코드가 null이면
0을 반환하고, 거기에 0x14를 더한 뒤 `func_020edc58`로 꼬리 호출하는 열세 개의 ARM
명령어다 — r2나 r3에 쓰지 않으므로 둘 다 그대로 통과한다
[S: `func_020edbbc`, autoload_2, `port/shim/game/chanopen.c` header].

`func_020edc58`은 `autoload_2`의 0xd8바이트짜리 ARM이며 mwcc 1.2/base `-O4,p`에서 ROM과
바이트 단위로 동일하다 [S: `func_020edc58`, autoload_2,
`src/matched/func_020edc58.c` via `port/shim/game/chanstage.c:37-40`]. 채널 id를
`0x021fcfdc`의 하프워드에, 상태 바이트를 `0x021fcfd4`에 기록한 다음 세 가지를 실행한다
[S: `port/shim/game/chanstage.c:78-96`]:

1. 상태 1 — 열기 전 훅, `func_020edc20`;
2. 상태 2 — `func_020edd30`, 채널의 두 추가 인자로부터 파라미터 블록을
   채운다;
3. 상태 3 — 채널의 열기 핸들러, 핸들러 테이블을 통해 호출된다.

실패 시 상태를 4로 올리고 오류 훅 `func_020edec8`을 호출한다; 어느 쪽 종료에서든
상태를 0으로, 채널 슬롯을 센티널 `0xffff`로 되돌린다
[S: `port/shim/game/chanstage.c:89-98, 143-176`].

"오류"라는 해석은 틀렸으며 기억해 둘 가치가 있다: ROM은 생성자의 `blx`와
`func_020edec8`으로의 `bl` 사이에 r0을 건드리지 않으므로, 거기에 전달되는 값은
생성자의 반환값 — 객체 — 이며, 0이 아닌 결과는 "오류"가 아니라 "객체가 만들어졌다"는
뜻이다 [S: `port/shim/game/chanstage.c:146-152`]. `func_020edec8`은 그 객체의 바이트
`+0x0e`부터 `+0x11`까지를 읽고 쓰며 이를 큐에 넣는다
[S: `port/shim/game/chanstage.c:152-156`].

### 이중 간접 핸들러 테이블

테이블 포인터는 `0x021fd044`의 워드다
[S: `port/shim/game/chanstage.c:80`]. 이는 채널로 인덱싱되는 핸들러 포인터의 배열이며,
ROM은 전역 변수의 값을 역참조하고, 인덱싱하고, 호출 전에 그 결과를 다시 한 번
역참조한다 — 주소 리터럴 이후 세 번의 로드다
[S: `g_handlerTable` at `0x021fd044`, autoload_2, `port/shim/game/chanstage.c:41-56, 80`].
별표(*) 하나를 잘못 세면 핸들러 대신 레코드에 도달해 그것을 호출하게 된다
[S: same header]. `func_020edc58`의 형제인 `func_020ee660`은 같은 테이블을 순회하며
그것에 대해 객체를 초기화한다 [S: `func_020ee660`, autoload_2,
`port/shim/game/drvopen.c` header].

테이블 포인터는 부팅 내내 상수가 아니다. 초기화 중에는 `main` 자체의 테이블인 `0x020e3134`를
담고 있다; 마을의 채널 0x22가 열릴 때쯤이면 ROM 디스패처
`func_020edc58`은 그것이 대신 씬 자체의 테이블을 가리켜야 한다
[E: `docs/log/cycle40-keyboard-gate-probe.md` REG40, where an interpreter run still had
`main`'s]. PC 포트에서는 마을의 채널 0x22가 테이블 항목이 호스트 함수 안을 가리키는 채로
도착했고, 그래서 맹목적인 이중 간접 참조가 그 함수의 첫 네 바이트를 읽어
실행했다 [E: `docs/log/cycle40-keyboard-gate-probe.md` CHAN40, `EXECUTE at 0x50e58955`].

그것을 고치며 얻은 교훈은 여기에 기록할 만큼 일반적이다: 주소가 NDS 주소 범위에 있다고 해서
코드인 것은 아니다 — 데이터도 거기에 살기 때문에, 레코드 검사가 코드 검사보다 먼저
와야 한다 [E: `docs/log/cycle40-keyboard-gate-probe.md` CHAN40b, where channel 0's entry
`0x020e35fc` is a record in main RAM].

### 실제로 관측된 채널들

`func_020edbbc`에 전달되는 서로 다른 핸들러 id의 집합이 곧 한 부팅이 여는 채널의 집합인데,
첫 번째 인자가 테이블을 인덱싱하는 id이기 때문이다
[S: `port/shim/game/chanopen.c:40-56`]. 지금까지 이름이 붙은 id: 채널 1은 타이틀 씬
[E: `port/shim/gfx/dispjoin.c` header]; 채널 13은 마을의 지면으로, 레코드는
`0x02239a2c`에 있고 생성자 `func_ov003_0221fe10`은 vtable 슬롯 0에 에이커 모델 및 텍스처 로더를
가진다 [S: `port/shim/game/chanopen.c:41-45`]; 채널 189의 객체는 `0x022382ac`의 vtable 슬롯 9에
모델 그리기를 가지며, 포트의 심 헤더들이 여전히 부르는 이름인 필드 렌더러가 아니라
눈사람이다 — 바인드 로그가 `/snowman/snowball1.nsbmd`와
`/snowman/snow_face.nsbmd`를 이름 짓는다 [S: `port/shim/game/chanlist.c` header, retracted by
E: `port/BOOT-STATE.md:1159-1171`]; 채널 0x22는 마을 채널
[E: cycle40 log, CHAN40]; 채널 0xd2는 파티클 시스템
[S: `port/shim/game/chanstage.c:6-8`]; 채널 216의 숨김 해제는 하드웨어에서 씬 1에서 실행된다
[S: `port/shim/gfx/pmflist.c:290-296`].

### 메일박스와 모드 바이트

`0x021f69d0`은 한 슬롯짜리 요청 메일박스로, 바이트 0이 `0x3f`이면 유휴 상태를 뜻하며, 정확히
하나의 함수만이 `0x3f`를 되돌려 쓴다: 씬 6의 스테이지 6에서만 호출되는 `func_020b5e88`
[S: `docs/kb/port/sequencer-and-modes.md`]. 그 메일박스의 바이트 0은 매 프레임
`func_020b6fd0`이 `func_020b5e84`를 통해 게임 모드 바이트 `data_020e54ac`로 복사한다
[S: `docs/kb/port/sequencer-and-modes.md`].

모드 바이트는 모든 씬 전환 위에 있는 진짜 게이트다: `func_020418d0`은 `func_020412a0()`이
0이 아닐 때 정확히 0을 반환하며, 이는 `func_020b65c4()`가 반환하는 모드 바이트가
6, 12, 13, 14, 44, 45, 46, 47, 48, 50 중 하나일 때 참이다
[S: `docs/kb/port/sequencer-and-modes.md`]. 모드 0x2c부터 0x2f까지는 전환/페이드
띠다 — `func_020b6fd0`은 모드 0xc, 0xd, 0xe, 0x2e, 0x2f에 대해 `func_020a6ef0(4)`를 호출한다
[S: `docs/kb/port/sequencer-and-modes.md`]. 스테이지 5가 중단되면 스테이지 6은 결코 실행되지 않고,
메일박스는 결코 지워지지 않으며, 이후의 모든 모드 요청은 거부되고 모드 바이트는 페이드
띠에 머문다 [E: `docs/kb/port/sequencer-and-modes.md`, measured on the native path at `c84db69f`].

이 모든 것 옆에는 프레임별 펌프가 `func_020a6c08`인 스크린 매니저가 있다; 그 아래의 무언가가
실행되는지는 `mgr+0x64`의 현재 스크린과 그 스크린의 활성화 바이트가
결정한다 [S: `func_020a6c08`, main, `port/shim/game/screenpump.c` header].

### 씬 기계 장치가 동작할 때의 모습

인터프리터 경로에서는 마을의 전체 진입 시퀀스 — 네이티브 포트가 사이클 34부터 40까지를
쏟은 문제 — 가 아예 발생하지 않았는데, ROM 자체의 코드가 그것을 실행했기 때문이다
[E: `docs/log/cycle40-keyboard-gate-probe.md` TOWN40, run `scratchpad/cycle40/runs/tap-D56`].
마을의 씬 6 스테이지 1부터 4까지가 오버레이 5가 로드된 후 실행되는 것이 관측되었다
[E: `docs/log/cycle40-keyboard-gate-probe.md` CALL40].

## 어디에 있는가

| 함수 또는 심볼 | 모듈 | 역할 | 등급 / 출처 |
|---|---|---|---|
| `func_020a636c` | main | 최상위 씬 머신 | [S: `port/shim/game/scenestate.c` header] |
| `func_020a6688` / `func_020a6684` | main | 그 상태 세터(`self[24]`)와 게터 | [S: `port/shim/game/scenestate.c:19-40`] |
| `func_020b6c0c` | main | 씬 6의 여섯 스테이지 로더, 호출당 한 스테이지, 40 ms 예산 | [S: `port/shim/game/scene6init.c` header] |
| `func_020a5598` | main | 씬 진입 시 스테이지 카운터를 지운다 | [S: `port/shim/game/scene6init.c` header] |
| `func_020b0b00` | main | 스테이지 5의 리소스 항목 루프 | [S: `port/shim/game/stageloop.c` header] |
| `func_020b5e88` | main | 스테이지 6; 메일박스 유휴 값을 쓰는 유일한 함수 | [S: `docs/kb/port/sequencer-and-modes.md`] |
| `func_020b6a7c` | main | 씬 6의 업데이트 슬롯, 두 타이틀 게이트 바이트 뒤에 있음 | [S: `port/shim/gfx/pmflist.c:122-131`] |
| `func_020b0bbc` | main | 씬별 채널 목록 순회, 시간 제한 있음 | [S: `port/shim/game/chanlist.c` header] |
| `func_0202f134` | main | 채널 열기 정문, 인자 네 개 | [S: `port/shim/game/chanopen.c` header] |
| `func_020edbbc` | autoload_2 | 열세 명령어; null 검사, `+0x14`, 꼬리 호출 | [S: `port/shim/game/chanopen.c` header] |
| `func_020edc58` | autoload_2 | 세 단계 채널 열기 | [S: `port/shim/game/chanstage.c:37-66`] |
| `func_020edc20` / `func_020edd30` / `func_020edec8` | autoload_2 | 스테이지 1 훅, 스테이지 2 파라미터 블록, 객체 큐잉 훅 | [S: `port/shim/game/chanstage.c:82-84, 143-156`] |
| `func_020ee660` | autoload_2 | 핸들러 테이블을 순회하며 그것에 대해 객체를 만든다 | [S: `port/shim/game/drvopen.c` header] |
| `func_020a6c08` | main | 스크린 매니저의 프레임별 펌프 | [S: `port/shim/game/screenpump.c` header] |
| `func_ov003_0221fe10` | ov003 | 채널 13의 생성자; 슬롯 0에 에이커 모델/텍스처 로더 | [S: `port/shim/game/chanopen.c:41-45`] |

## 읽고 쓰는 데이터

| 주소 또는 필드 | 의미 | 쓰는 쪽 | 읽는 쪽 |
|---|---|---|---|
| `0x021fd044` | 채널 핸들러 포인터 배열을 가리키는 포인터 | 초기화(`0x020e3134`), 그다음 씬 | `func_020edc58`, `func_020ee660` [S: `port/shim/game/chanstage.c:80`] |
| `0x021fcfdc` | 열리고 있는 채널; `0xffff`는 "없음" | `func_020edc58` | 열기 시퀀스 [S: `port/shim/game/chanstage.c:78, 89`] |
| `0x021fcfd4` | 열기의 스테이지 바이트, 1/2/3/4, 0으로 재설정 | `func_020edc58` | 열기 시퀀스 [S: `port/shim/game/chanstage.c:79-96`] |
| `0x021f42f0` | 씬 6의 스테이지 카운터 | 진입 시 `func_020a5598`이 지운다 | `func_020b6c0c` [S: `port/shim/game/scene6init.c` header] |
| `0x021f69d0` | 한 슬롯짜리 요청 메일박스; 바이트 0 `0x3f` = 유휴 | `func_020b5e88` (스테이지 6) | `func_020b6fd0` [S: `docs/kb/port/sequencer-and-modes.md`] |
| `data_020e54ac` | 게임 모드 바이트; 0x2c-0x2f는 페이드 띠 | `func_020b6fd0`이 `func_020b5e84`를 통해 | `func_020b65c4`, `func_020412a0` [S: `docs/kb/port/sequencer-and-modes.md`] |
| `data_020e3c80` | 상태 16이 5와 같아지기를 기다리는 씬 id | 씬 머신 | `func_020a6684` [S: `port/shim/game/scenestate.c:31-34`] |
| `0x021c75b8` / `0x021c75b0` | 씬 6의 업데이트 슬롯을 게이트하는 두 바이트 | 확인되지 않음 | `func_020b6a7c` [S: `port/shim/gfx/pmflist.c:124-131`] |
| `data_020e41ec` | 스테이지 5의 리소스 종류 디스패치 테이블 | 정적 | `func_020b0b00` [S: `port/shim/game/stageloop.c:23`] |
| `0x020e3134` | `main`의 채널 핸들러 테이블 | 정적 | 초기화의 테이블 포인터 쓰기 [S: `port/shim/gfx/gxdirect_a.c:241`] |
| `0x02239a2c` | 채널 13의 핸들러 레코드 | `ov003`의 정적 데이터 | `func_020edc58`의 테이블 순회 [S: `port/shim/game/chanopen.c:41-45`] |

## 확인 방법

두 번 탭 마을 레시피(`docs/kb/hybrid/recipes.md` section 3)를 실행하고 로그에서 포트의
채널 계측 줄을 grep한다: `acww chanstage: chan <id> table entry=... *entry=...`는 각 채널의
테이블 항목이 어떤 형태를 취했고 처리되었는지 거부되었는지를 말해 준다
[S: `port/shim/game/chanstage.c:130-141`]; `acww chanlist: count=... from index ...`는
씬의 채널 목록을 출력한다 [S: `port/shim/game/chanlist.c:40-48`]; `acww scenest: -> N`은
첫 40개의 씬 상태 전환을 출력하고 `acww scenest: state=`는 120회 호출마다 머신을
샘플링한다 [S: `port/shim/game/scenestate.c:19-40`]. 계측이 `acww_trace_state()`를 검사하는 곳에서는
그 줄들에 `ACWW_TRACE_STATE`가 필요하다 [S: `port/shim/game/chanopen.c:38`].

"채널 목록이 짧다"와 "순회가 프레임 예산을 다 썼다"를 구분하려면, 출력된 개수를
`acww chanstage` 줄의 수와 비교한다 — 순회는 40 ms로 제한되며
다음 프레임에 재개된다 [S: `port/shim/game/chanlist.c` header].

## 가설

- `0x021c75b8`과 `0x021c75b0`의 두 바이트는 채널 핸들러가 아니라 씬 진입 경로가
  쓴다 [H: settled by a store watchpoint on both
  (`ACWW_INTERP_WATCH=<hex>`) across the title-to-town transition].
- 씬 자체의 핸들러 테이블 — 채널 0x22가 열리기 전에 `0x021fd044`가 가리켜야 하는 것
  — 은 씬 6의 스테이지 4가 설치한다 [H: settled by watching `0x021fd044` and correlating the
  change frame with the `acww chanstage` line for the first town channel].
- 채널 id는 씬별 인덱스가 아니라 씬에 걸쳐 안정적이다(id 13은 항상 지면을 뜻한다)
  [H: settled by logging every distinct id and its resolved handler record across two
  different scenes and comparing].
- 채널 목록과 여섯 스테이지 로더 양쪽의 40 ms 예산은 디버그 값이 아니라 ROM 자체의 프레임
  허용치다 [H: settled by locating the constant in the ROM's literal pool
  and checking it against the NDS frame period].

## 관련 문서

- `display-objects.md` — 채널의 생성자가 무엇에 합류하는지, 그리고 매 프레임 무엇이 그것을 스텝하는지
- `overlays.md` — 씬의 채널이 상주를 필요로 하는 오버레이
- `boot-and-entry.md` — 제어가 씬 머신에 도달하는 방법
- `memory-map.md` — 이 전역 변수들이 있는 `0x021fxxxx` 띠
