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
[S: `src/matched/func_020a6688.c`; source account: `func_020a6688` / `func_020a636c`, main,
`port/shim/game/scenestate.c` header, body from `src/matched/func_020a6688.c`]. 세터는
`func_020a6688`이고 게터는 `func_020a6684`인데, 게터는 매 스텝마다 호출되므로
머신의 틱을 보는 유일한 장소다 [H: source account: `port/shim/game/scenestate.c:30-40`; direct ROM-source provenance unresolved].
관측된 상태의 순서는 16, 그다음 0, 1, 2, 그리고 위로 올라간다
[H: host-source account from `port/shim/game/scenestate.c` header, from the port's `acww scenest:` trace; verify with a retained scripted run and frame using this page's recipe].

상태 16의 본체 전체는 하나의 가드다: 씬 id `data_020e3c80`이
5와 같지 않으면 반환한다 [H: source account: `port/shim/game/scenestate.c:31-34`; direct ROM-source provenance unresolved]. 따라서 하나의 상태를 설정하고 멈추는
머신은 결코 열리지 않는 가드를 가진 것이며, 상태 트레이스가 어느 것인지 이름 짓는다
[H: log/source account: same instrument; receipt provenance unresolved].

### 씬 6의 여섯 스테이지 로더

씬 6의 초기화는 `func_020b6c0c`로, 호출당 한 스테이지를 실행하며 모든 스테이지가 0이 아닌 값을
반환할 때까지 — 또는 프레임의 40 ms가 소비될 때까지, 둘 중 먼저 오는 쪽까지 —
"끝나지 않음"(-1)을 보고하는 단계적 로더다 [S: `config/adm-kr/arm9/symbols.txt` (`func_020b6c0c` at 0x020b6c0c); source account: `func_020b6c0c`, main, `port/shim/game/scene6init.c` header]. 스테이지들은 함수 지역 정적 변수에 담긴 멤버 함수
포인터이며, 첫 호출 때 RAM의 `0x021f6a3c`로 `0x020e54c4`를 기반으로 한 여섯 ROM 정적
변수에서 복사된다. 스테이지 카운터는 `0x021f42f0`의 바이트로 씬에 진입할 때
`func_020a5598`이 지운다 [H: source account: `port/shim/game/scene6init.c` header; the descriptor addresses read from the extracted
ARM9 image, `docs/log/cycle41-gameplay.md` LOAD52 L52-1; direct ROM-source provenance unresolved].

**40 ms는 로더 전체의 타이밍 계약이며, 스테이지별 예산이 아니라 측정값이다.**
`func_020b6c0c`는 진입할 때 `OS_GetTick()`을 **한 번** 호출하고 그 틱을 모든 스테이지
핸들러에 전달하며, 핸들러는 다시 아래로 전달한다. 각 단계의 검사는
`((OS_GetTick() - start) * 64 / 33514) > 0x28`이고, `33514`가 kHz 단위의 NDS 시스템
클록이므로 몫은 밀리초이며 `0x28`은 40이다. **이 체인의 어느 것도 완료 플래그, DMA 비트,
VBlank 카운트 또는 ARM7이 쓰는 워드를 읽지 않는다** — 로더는 대기자가 아니라 시간 분할
작업 루프다 [S: `src/matched/func_020b0b00.c`; source account: `func_020b6c0c`, `func_020b0b00`, `func_020b0ea8`,
`func_020b0bbc`, main; `src/matched/func_020b0b00.c` is byte-verified and carries the test].

스테이지 4는 채널을 여는 서브스테이지 목록이다
[H: host-source account from `port/shim/game/chanvector.c` header, narrowed by elimination on the native path; verify with a retained scripted run and frame using this page's recipe].
스테이지 5는 `func_020b6d8c`이며 `func_020b0abc` -> `func_020b0b00`을 꼬리 호출하는
리소스 항목 루프다. 각 항목에 대해 `data_020e41ec[e->b0]`를 디스패치하며, 0을 반환하는
핸들러는 "끝나지 않았으니 다음 프레임에 다시 오라"는 뜻이다
[S: `src/matched/func_020b0b00.c`; source account: `func_020b0b00`, main,
`port/shim/game/stageloop.c` header, body from `src/matched/func_020b0b00.c`]. 디스패치 테이블에는 **정확히 세 개**의 항목 — 종류 0, 1, 2에
해당하는 `func_020b0ea8`, `func_020b0c4c`, `func_020b0bbc` — 만 있으며, 그 주소의 네 번째
워드는 문자열 데이터다 [H: source account: read from the extracted ARM9 image; `docs/log/cycle41-gameplay.md` LOAD52 L52-1; direct ROM-source provenance unresolved].
이 루프는 `func_020b6d8c`가 자체 리터럴 풀에서 제공하는 두 바이트 카운터를 유지한다:
거부된 호출이 멈춘 곳에서 다시 시작하도록 하는 **재개 인덱스** `0x021f42dc`와, 항목별
플래그이면서 종류 0/종류 2 핸들러 자신의 서브 항목 인덱스이기도 한 `0x021f42e4`다
[H: source account: read from the extracted ARM9 image; `docs/log/cycle41-gameplay.md` LOAD52 L52-1; direct ROM-source provenance unresolved].
스테이지 6은 ROM에서 시퀀서 메일박스를 지우는 유일한 것으로,
`func_020b5e88`을 통해 지운다
[H: source account: `docs/kb/port/sequencer-and-modes.md`, LEGACY-NATIVE page describing the ROM's mechanism; direct ROM-source provenance unresolved].

씬 6의 프레임별 업데이트 슬롯은 `func_020b6a7c`이며, `0x021c75b8`의 바이트가 2이거나
`0x021c75b0`의 바이트가 0이 아닌 경우가 아니면 즉시 — 아무것도 하지 않고 — 반환한다
[S: `src/matched/func_020b6a7c.c`; source account: `func_020b6a7c`, main, `port/shim/gfx/pmflist.c:122-131`]. 마을 이후의 모든 것이
그 두 바이트를 기다린다: 씬이 결코 바뀌지 않으므로, 열네 항목짜리 마을 채널 목록 전체를
순회하는 레코드 배열이 결코 설치되지 않는다
[H: source account: `port/shim/gfx/pmflist.c:124-129`; direct ROM-source provenance unresolved].

### 씬별 채널 목록

`func_020b0bbc`는 씬의 채널 목록을 순회한다: 두 하프워드 항목의 배열로, 개수는 객체의 두 번째
바이트에 있고 재개 인덱스가 인자로 전달된다 [S: `src/matched/func_020b0bbc.c`; source account: `func_020b0bbc`, main,
`port/shim/game/chanlist.c`, body from `src/matched/func_020b0bbc.c`]. 순회는
시간 제한이 있다 — 프레임의 40 ms 후에 포기하고 다음번에 재개한다 — 그래서 "테이블에 id N이
없다"와 "순회가 거기까지 가지 못했다"는 밖에서 보면 똑같아 보인다
[H: source account: `port/shim/game/chanlist.c` header; direct ROM-source provenance unresolved]. 씬 6은 상수가 아니라 그 테이블에서 채널을 연다:
필드 렌더 객체인 id 189는 ROM 어디에도 즉시값(immediate)으로 등장하지 않는다
[H: source account: `port/shim/game/chanlist.c` header; direct ROM-source provenance unresolved].

### 채널 열기: 세 단계

정문은 `func_0202f134`로, 모든 씬의 채널 목록이 이를 거치며 네 개의 인자로 호출을
구성한다 [S: `src/matched/func_0202f134.c`; source account: `func_0202f134`, main,
`port/shim/game/chanopen.c` header]. 이는 `func_020edbbc`로 전달되는데, 핸들러 레코드가 null이면
0을 반환하고, 거기에 0x14를 더한 뒤 `func_020edc58`로 꼬리 호출하는 열세 개의 ARM
명령어다 — r2나 r3에 쓰지 않으므로 둘 다 그대로 통과한다
[S: `src/matched/func_020edbbc.c`, `src/matched/func_0202f134.c`, `src/matched/func_020edc58.c`; source account: `func_020edbbc`, autoload_2, `port/shim/game/chanopen.c` header].

`func_020edc58`은 `autoload_2`의 0xd8바이트짜리 ARM이며 mwcc 1.2/base `-O4,p`에서 ROM과
바이트 단위로 동일하다 [S: `src/matched/func_020edc58.c`; source account: `func_020edc58`, autoload_2,
`src/matched/func_020edc58.c` via `port/shim/game/chanstage.c:37-40`]. 채널 id를
`0x021fcfdc`의 하프워드에, 상태 바이트를 `0x021fcfd4`에 기록한 다음 세 가지를 실행한다
[H: source account: `port/shim/game/chanstage.c:78-96`; direct ROM-source provenance unresolved]:

1. 상태 1 — 열기 전 훅, `func_020edc20`;
2. 상태 2 — `func_020edd30`, 채널의 두 추가 인자로부터 파라미터 블록을
   채운다;
3. 상태 3 — 채널의 열기 핸들러, 핸들러 테이블을 통해 호출된다.

실패 시 상태를 4로 올리고 오류 훅 `func_020edec8`을 호출한다; 어느 쪽 종료에서든
상태를 0으로, 채널 슬롯을 센티널 `0xffff`로 되돌린다
[H: source account: `port/shim/game/chanstage.c:89-98, 143-176`; direct ROM-source provenance unresolved].

"오류"라는 해석은 틀렸으며 기억해 둘 가치가 있다: ROM은 생성자의 `blx`와
`func_020edec8`으로의 `bl` 사이에 r0을 건드리지 않으므로, 거기에 전달되는 값은
생성자의 반환값 — 객체 — 이며, 0이 아닌 결과는 "오류"가 아니라 "객체가 만들어졌다"는
뜻이다 [H: source account: `port/shim/game/chanstage.c:146-152`; direct ROM-source provenance unresolved]. `func_020edec8`은 그 객체의 바이트
`+0x0e`부터 `+0x11`까지를 읽고 쓰며 이를 큐에 넣는다
[H: source account: `port/shim/game/chanstage.c:152-156`; direct ROM-source provenance unresolved].

### 이중 간접 핸들러 테이블

테이블 포인터는 `0x021fd044`의 워드다
[H: source account: `port/shim/game/chanstage.c:80`; direct ROM-source provenance unresolved]. 이는 채널로 인덱싱되는 핸들러 포인터의 배열이며,
ROM은 전역 변수의 값을 역참조하고, 인덱싱하고, 호출 전에 그 결과를 다시 한 번
역참조한다 — 주소 리터럴 이후 세 번의 로드다
[H: source account: `g_handlerTable` at `0x021fd044`, autoload_2, `port/shim/game/chanstage.c:41-56, 80`; direct ROM-source provenance unresolved].
별표(*) 하나를 잘못 세면 핸들러 대신 레코드에 도달해 그것을 호출하게 된다
[H: source account: `g_handlerTable` at `0x021fd044`, autoload_2, `port/shim/game/chanstage.c:41-56, 80` header; direct ROM-source provenance unresolved]. `func_020edc58`의 형제인 `func_020ee660`은 같은 테이블을 순회하며
그것에 대해 객체를 초기화한다 [S: `src/matched/func_020edc58.c`; source account: `func_020ee660`, autoload_2,
`port/shim/game/drvopen.c` header].

테이블 포인터는 부팅 내내 상수가 아니다. 초기화 중에는 `main` 자체의 테이블인 `0x020e3134`를
담고 있다; 마을의 채널 0x22가 열릴 때쯤이면 ROM 디스패처
`func_020edc58`은 그것이 대신 씬 자체의 테이블을 가리켜야 한다
[H: log/source account: `docs/log/cycle40-keyboard-gate-probe.md` REG40, where an interpreter run still had
`main`'s; receipt provenance unresolved]. PC 포트에서는 마을의 채널 0x22가 테이블 항목이 호스트 함수 안을 가리키는 채로
도착했고, 그래서 맹목적인 이중 간접 참조가 그 함수의 첫 네 바이트를 읽어
실행했다 [H: log/source account: `docs/log/cycle40-keyboard-gate-probe.md` CHAN40, `EXECUTE at 0x50e58955`; receipt provenance unresolved].

그것을 고치며 얻은 교훈은 여기에 기록할 만큼 일반적이다: 주소가 NDS 주소 범위에 있다고 해서
코드인 것은 아니다 — 데이터도 거기에 살기 때문에, 레코드 검사가 코드 검사보다 먼저
와야 한다 [H: log/source account: `docs/log/cycle40-keyboard-gate-probe.md` CHAN40b, where channel 0's entry
`0x020e35fc` is a record in main RAM; receipt provenance unresolved].

### 실제로 관측된 채널들

`func_020edbbc`에 전달되는 서로 다른 핸들러 id의 집합이 곧 한 부팅이 여는 채널의 집합인데,
첫 번째 인자가 테이블을 인덱싱하는 id이기 때문이다
[H: source account: `port/shim/game/chanopen.c:40-56`; direct ROM-source provenance unresolved]. 지금까지 이름이 붙은 id: 채널 1은 타이틀 씬
[H: host-source account from `port/shim/gfx/dispjoin.c` header; verify with a retained scripted run and frame using this page's recipe]; 채널 13은 마을의 지면으로, 레코드는
`0x02239a2c`에 있고 생성자 `func_ov003_0221fe10`은 vtable 슬롯 0에 에이커 모델 및 텍스처 로더를
가진다 [H: source account: `port/shim/game/chanopen.c:41-45`; direct ROM-source provenance unresolved]; 채널 189의 객체는 `0x022382ac`의 vtable 슬롯 9에
모델 그리기를 가지며, 포트의 심 헤더들이 여전히 부르는 이름인 필드 렌더러가 아니라
눈사람이다 — 바인드 로그가 `/snowman/snowball1.nsbmd`와
`/snowman/snow_face.nsbmd`를 이름 짓는다 [H: source account: `port/shim/game/chanlist.c` header, retracted by
H: historical measurement account: `port/BOOT-STATE.md:1159-1171`; direct ROM-source provenance unresolved]; 채널 0x22는 마을 채널
[H: log/source account: cycle40 log, CHAN40; receipt provenance unresolved]; 채널 0xd2는 파티클 시스템
[H: source account: `port/shim/game/chanstage.c:6-8`; direct ROM-source provenance unresolved]; 채널 216의 숨김 해제는 하드웨어에서 씬 1에서 실행된다
[H: source account: `port/shim/gfx/pmflist.c:290-296`; direct ROM-source provenance unresolved].

### 메일박스와 모드 바이트

`0x021f69d0`은 한 슬롯짜리 요청 메일박스로, 바이트 0이 `0x3f`이면 유휴 상태를 뜻하며, 정확히
하나의 함수만이 `0x3f`를 되돌려 쓴다: 씬 6의 스테이지 6에서만 호출되는 `func_020b5e88`
[H: source account: `docs/kb/port/sequencer-and-modes.md`; direct ROM-source provenance unresolved]. 그 메일박스의 바이트 0은 매 프레임
`func_020b6fd0`이 `func_020b5e84`를 통해 게임 모드 바이트 `data_020e54ac`로 복사한다
[H: source account: `docs/kb/port/sequencer-and-modes.md`; direct ROM-source provenance unresolved].

모드 바이트는 모든 씬 전환 위에 있는 진짜 게이트다: `func_020418d0`은 `func_020412a0()`이
0이 아닐 때 정확히 0을 반환하며, 이는 `func_020b65c4()`가 반환하는 모드 바이트가
6, 12, 13, 14, 44, 45, 46, 47, 48, 50 중 하나일 때 참이다
[H: source account: `docs/kb/port/sequencer-and-modes.md`; direct ROM-source provenance unresolved]. 모드 0x2c부터 0x2f까지는 전환/페이드
띠다 — `func_020b6fd0`은 모드 0xc, 0xd, 0xe, 0x2e, 0x2f에 대해 `func_020a6ef0(4)`를 호출한다
[H: source account: `docs/kb/port/sequencer-and-modes.md`; direct ROM-source provenance unresolved]. 스테이지 5가 중단되면 스테이지 6은 결코 실행되지 않고,
메일박스는 결코 지워지지 않으며, 이후의 모든 모드 요청은 거부되고 모드 바이트는 페이드
띠에 머문다 [H: log/source account: `docs/kb/port/sequencer-and-modes.md`, measured on the native path at `c84db69f`; receipt provenance unresolved].

이 모든 것 옆에는 프레임별 펌프가 `func_020a6c08`인 스크린 매니저가 있다; 그 아래의 무언가가
실행되는지는 `mgr+0x64`의 현재 스크린과 그 스크린의 활성화 바이트가
결정한다 [S: `src/matched/func_020a6c08.c`; source account: `func_020a6c08`, main, `port/shim/game/screenpump.c` header].

### 두 생산자에서 측정한 전환 하나의 구조

씬 전환에는 두 단계가 있으며, 그중 로더는 하나뿐이다. 메일박스가 올라간 뒤 지워질 때까지
게임은 먼저 **프리로더 단계**를 실행하며, 여기서 화면이 페이드 아웃한다. 그다음
**여섯 스테이지 로더**를 실행하며, 진행 상황은 스테이지 카운터 `0x021f42f0`에서 보인다.
하드웨어에서 문 전환은 두 단계에 프레임을 대략 절반씩 쓰지만, PC 포트에서는 로더가 한
프레임으로 압축된다
[E: `docs/log/cycle41-gameplay.md` TRANSITION51 T51-2, T51-4, one-frame shots and peeks on both
producers over the same 93-row pad chain ; `scratchpad/transition51/RECEIPTS.md`].

| | 원본(DS) | PC 포트 |
|---|---|---|
| 메일박스 `0x021f69d0[0]` `0x3f` -> `0x80000011` | 프레임 57,187 | 프레임 57,309 |
| 프리로더 단계, 그 안의 페이드 아웃 | **59 프레임** | **63 프레임** |
| 스테이지 카운터가 1..7을 순회 | 메인 루프 본체마다 한 스테이지, 그다음 스테이지 5에서 유지; **59 프레임** | **일곱 번의 쓰기 모두 한 프레임** |
| 메일박스가 `0x8000003f`로 지워짐 | 프레임 57,305 | 프레임 57,372 |
| 전체 전환 | **118 프레임 / 메인 루프 본체 30회** | **63 프레임 / 본체 21회** |

프리로더 단계의 비용은 양쪽에서 네 프레임 이내로 같으므로, **전체 차이는
로더이다** [E: `docs/log/cycle41-gameplay.md` TRANSITION51 T51-2, T51-4, one-frame shots and peeks on both
producers over the same 93-row pad chain ; `scratchpad/transition51/RECEIPTS.md`]. 포트에서는 모든
스테이지가 첫 호출에서 "완료"를 반환하기 때문이다. 한
프레임 안에서 카운터가 7에 도달한다는 것은 루프가 "끝나지 않았으니 다음 프레임에 다시
오라"는 말을 듣지 않았다는 뜻이며, 하드웨어에서는 스테이지 5의 리소스 핸들러가
**슬라이스에서 40 ms가 소모된 뒤에** 그렇게 말한다 — TRANSITION51이 여기서 쓴 것처럼
읽기가 미완료인 동안이 아니다. 기다릴 미완료 읽기는 없다(LOAD52)
[H: log/source account: `ACWW_INTERP_WATCH=0x021f42f0`, six stores at pc `0x020b6ca6` in frame 57,372; the same
shape at the town-hall exit in frame 49,656; receipt provenance unresolved]. 마을 회관을 나가는
경우에도 같은 측정을 하면 하드웨어는 스테이지 5를 적어도 150 프레임 동안 유지하며, 메인
루프 본체당 **23.6 프레임**으로 포트의 2.95에 비해 길다. 포트가 오랫동안 지녀 온 약
115프레임의 외출 선행은 여기서 생긴다
[E: TRANSITION51 T51-4, retiring TUT45-4's "inherited from before the seam" ; `scratchpad/transition51/RECEIPTS.md`].

카드 전송 대기는 아니다. ROM-FS 계측을 켜면 문의 로더 프레임은 읽기 요청 7,413개,
724,265바이트, 오버레이 이미지 3개를 처리하고, 마을 회관 출구는 요청 35,631개,
1,322,272바이트, 오버레이 4개를 처리한다. 이 ROM의 카트리지 클록에서 이는 측정된
59프레임과 150+프레임에 비해 버스 시간 6.5프레임과 11.8프레임이다
[E: `docs/log/cycle41-gameplay.md` LOAD52 L52-3, `ACWW_FSTRACE=1`; the clock from the header's
`MCCNT1` CT bit ; `scratchpad/load52/RECEIPTS.md`]. **TRANSITION51의 "마을 회관 출구는
오버레이를 전혀 로드하지 않는다"는 주장은 철회한다** — 오버레이 id마다 한 번만 출력하는
`acww ovl:` 줄에서 읽은 것이어서 재로드를 보여 줄 수 없었다. 반박은 수정된 수치에서도
유효하다.

**스테이지 5가 실제로 기다리는 것은 40 ms의 벽시계 BUDGET이며, 다른 것은 없다.**
스테이지 머신과 리소스 루프의 모든 0 반환 경로는 진입 시 스테이지 머신이 `OS_GetTick`에서
얻어 모든 핸들러에 전달한 틱으로부터 `0x28`밀리초를 넘었는지만 검사한다. 체인의 어디에도 완료
플래그, DMA 완료 비트, VBlank 카운트, ARM7이 쓴 워드는 없다
[S: `src/matched/func_020b0b00.c`; source account: `func_020b6c0c`, `func_020b0b00`, `func_020b0ea8`, `func_020b0bbc`, main;
`src/matched/func_020b0b00.c` is byte-verified and carries the test verbatim]. 포트가 "끝나지
않음"이라고 말하지 않는 것은 `port/platform/tick.c`가 **프레임마다 한 번, 한 프레임 분량만큼**
틱을 전진시키기 때문이다. 따라서 로더를 한 번 호출하는 동안 경과 시간은 정확히 0이고,
40 ms 예산은 만료될 수 없다 [E: LOAD52 L52-2 ; `scratchpad/load52/RECEIPTS.md`]. 59프레임과
150+프레임은 분할된 ARM9 작업이다.

페이드 자체는 **차이의 일부가 아니다**. 양쪽에서 같은 구간을 차지한다.
~~포트는 그것을 그리지 않는다 — 샘플링한 모든 프레임의 384개 스캔라인에서 `MASTER_BRIGHT`와
`BLDY`를 읽으면 0이고, `port/render/nds2d.c`는 출력할 때만 `MASTER_BRIGHT`를 읽는다.~~
**FADE52에 의해 철회됨**: 밝기 램프는 없고, "어두워짐"은 x=127.5 주변에서 약 10개 열씩
13단계로 window 0을 닫는 것이다(`0x0213fe94`의 섀도에서 가져온 `WIN0H`를
`func_02001ecc`가 플러시한다). 두 생산자에서 `MASTER_BRIGHT`는 0이며, 포트는 이제
윈도와 master brightness를 그린다(`wiki/engine/graphics-pipeline.md`, window 섹션)
[E: `scratchpad/fade52/RECEIPTS.md`; log: `docs/log/cycle41-gameplay.md` FADE52]. 포트에
아직 없는 것은 열세 개의 중간 `WIN0H` 값이다(포트는 두 개를 쓴다): WINDOW53.
로더이다** [E: `scratchpad/fade52/RECEIPTS.md`; log: `docs/log/cycle41-gameplay.md` FADE52]. 모든
스테이지가 포트에서 첫 호출에 "완료"를 반환한다는 뜻은, 한 프레임 안에서 카운터가 7에
도달했으므로 루프가 "끝나지 않았으니 다음 프레임에 다시 오라"는 말을 듣지 않았다는 것이다
[H: `ACWW_INTERP_WATCH=0x021f42f0`, six stores at pc `0x020b6ca6` in frame 57,372; the same
shape at the town-hall exit in frame 49,656 ; provenance unresolved]. 마을 회관 출구에서도 같은
측정을 하면 하드웨어는 스테이지 5를 적어도 150 프레임 동안 유지하며, 메인 루프 본체당
**23.6 프레임**으로 포트의 2.95에 비해 길다. 포트의 오랜 약 115프레임 외출 선행은
여기서 생긴다
[E: TRANSITION51 T51-4, retiring TUT45-4's "inherited from before the seam"; current receipt locator: `scratchpad/transition51/RECEIPTS.md`].

**루프가 "끝나지 않음"이라고 말하게 하는 것은 CLOCK이며, LOAD52 전까지 이 페이지는
다르게 말했다** — "하드웨어에서 스테이지 5의 리소스 핸들러가 읽기가 미완료인 동안 그렇게
말한다"는 주장은 철회한다. 체인 어디에도 폴링되는 워드는 없다. 스테이지 머신은 진입할
때 `OS_GetTick`을 **한 번** 취해 모든 핸들러에 전달하고, 일곱 함수의 모든 "다음 프레임에
다시 오라" 반환은 같은 검사를 한다. ROM 자체의 `64 / 33514`로 스케일한 델타 — kHz 단위
NDS 시스템 클록에 따른 정확한 밀리초 — 를 `0x28`과 비교하며, 이는 **40 ms**이다. 스테이지
5는 메인 루프 본체마다 40 ms를 스스로 부여받는 시간 분할 작업 루프이고, 예산은 서브 항목
사이에서만 검사된다. 따라서 본체는 40 ms에 경계를 넘은 서브 항목의 초과 시간이 더해진
값이 되며, DS에서 50.6 ms로 측정되었다. 마을 회관 출구의 두 개별 서브 항목은 각각
551 ms와 1,036 ms가 걸렸다 [E: LOAD52 L52-0..L52-5; `src/matched/func_020b0b00.c` carries the test verbatim; current receipt locator: `scratchpad/load52/RECEIPTS.md`].

**포트가 거부하지 않았던 것은 클록에 서브프레임 해상도가 없었기 때문이다**: 포트는
제시된 프레임마다 한 프레임 분량만큼 전진시켰으므로 한 번의 호출 안 경과 시간은 항등적으로
0이었다. `ACWW_TICK_MODEL=1`을 사용하면 — ROM 자체의 명령 스트림에서 가격을 매긴 클록으로
— 예산이 만료되고 스테이지 카운터가 처음으로 순회 중간에서 잡힌다. 출구 로더는 DS의
150+프레임에 비해 세 메인 루프 본체에서 15프레임, 문은 59프레임에 비해 12프레임을
차지한다 [E: TICK53 T53-4; `docs/kb/hybrid/hardware-services.md` 4b; current receipt locator: `scratchpad/tick53/RECEIPTS.md`].

카드 전송 대기는 아니며, 그 주장의 앞선 형태는 ABSENCE 때문에 틀렸다. 문은 오버레이 3개와
724,265바이트를 로드하고 마을 회관 출구는 4개와 1,322,272바이트를 로드한다 —
TRANSITION51의 "출구는 오버레이를 로드하지 않는다"는 말은 오버레이 id마다 한 번 출력되는
보고서 줄에서 나왔으므로 재로드가 보이지 않았다. 이 ROM의 카트리지 클록에서 이는 측정된
59프레임과 150+프레임의 **11%와 8%**인 108 ms와 197 ms이므로, 결론은 수정된 수치에서도
유지된다 [E: LOAD52 L52-3, `ACWW_FSTRACE`; the header's `MCCNT1` CT bit; current receipt locator: `scratchpad/load52/RECEIPTS.md`].

**마을 회관 출구의 긴 서브 항목 두 개가 실제로 무엇인지, 각각 한 메인 루프 본체에 대한
함수별 스텝 조사로 이름을 붙였다.** 둘은 서로 다른 서브시스템이며 어느 쪽도 대기가 아니다.
첫 번째(`*flag` 3 -> 4)는 **TOWN TILE SCAN**이다. ov003 드라이버를 한 번 호출하면 에이커
격자를 순회하며 모든 타일의 종류를 검사하고, `acre_x * acre_y * 16 * 16`회 반복한다.
6 x 6 에이커는 **9,216**이고, 본체에서 인터프리터가 실행한 명령의 63%가 이 순회와 그
아래의 두 ITCM 조회다. 두 번째(`*flag` 4 -> 10)는 **ROM-FS NAME WALK**다:
`FSi_ReadTable`, `FSi_ReadDirCommand`, `FSi_ReadRomCallback`이 한 본체에서 테이블을
2,556회 읽으며, 이는 카트리지 조사에서 세는 같은 2,556회다. 첫 번째의 상한은 계산된
크기가 아니라 STATIC 워드 두 개 — `(*0x021c80bc)[+4]`와 `[+8]` — 이며, `--peek`는
`0x02395444`에서 그 포인터를 읽어 같은 마을에서 **원본에서도 6과 6**인 두 워드를 얻는다.
**따라서 두 생산자 모두 9,216회 반복을 전부 실행한다.** 이는 "포트가 수행하지 않는 작업이
누락된 시간이다"라는 말을 세 번의 사이클에 걸쳐 철회한다. 포트가 그곳에서 건너뛰는 모든
것은 DS의 551 ms 중 14%에 해당한다
[E: CENSUS56, `ACWW_INTERP_CENSUS` + `--peek`; `docs/log/cycle41-gameplay.md` CENSUS56 C56-4/5].

**어느 서브 항목이 그 스캔인지와 긴 항목들이 무엇인지는 DS 쪽에서 정정되었다.**
에뮬레이터의 실행 샘플러(`--exec`, 프레임당 항목별 한 번의 카운트)는 리프
`func_02031478`의 9,216개 진입을 프레임 49,683..49,686 — `*flag` **2 -> 3** 구간,
**4프레임 = 67 ms** — 에 배치하며, 조사 대상이었던 `*flag` 3 -> 4의 33프레임 구간에서는
그중 **0개**를 찾는다. 따라서 타일 스캔은 DS에서 긴 서브 항목이 전혀 아니며, 포트의
1.43 M 명령은 20배 빠른 작업이 아니라 4프레임 작업에 맞는 크기다. 33프레임 구간에는
읽기마다 `OS_SleepThread`가 한 번씩 붙은 `CARDi_ReadRom` 왕복 8,898회와
`FSi_ReadTable` 호출 11,740회가 있다 — ARM9는 **절대 유휴 상태가 아니다**: 그 구간의
`OS_Halt`는 프레임당 6.0회이고, 로더 직전 마을 플레이에서는 68.9회다. 스테이지 5 전체는
1,905 ms 동안 카드 읽기 30,957회, 읽기당 **4,126 ARM9 사이클**이며, LOAD52 자체의
`ACWW_FSTRACE` 요청 수 35,631회와 비교된다. 전환은 바이트당 비용이 아니라 요청당
카트리지 비용이다. "카드 전송 대기가 아니다"는 바이트에 대해서는 맞았지만, 질문을
잘못 세운 것이다 [E: `docs/log/cycle41-gameplay.md` ISSUE57 I57-0/I57-3/I57-6 ;
`scratchpad/issue57/spans-exit.txt`].

문의 스테이지 5는 같은 장치 위의 세 번째 형태다 — 타일 스캔은 전혀 없고(타일 조회는
9,216회가 아니라 1,332회 실행됨), 선두에서 `func_020723a8`을 150,240명령으로 한 번
호출한다 — 따라서 한 문에서 순위가 높은 항이 다른 문으로 옮겨 가지 않는다
[E: CENSUS56 C56-3].

(여기에 있던 페이드 문단은 대체되었다. 위의 FADE52 철회를 보라 — "어두워짐"은 밝기
램프가 아니라 window 0을 닫는 것이다.)

### 씬 기계 장치가 동작할 때의 모습

인터프리터 경로에서는 마을의 전체 진입 시퀀스 — 네이티브 포트가 사이클 34부터 40까지를
쏟은 문제 — 가 아예 발생하지 않았는데, ROM 자체의 코드가 그것을 실행했기 때문이다
[E: `docs/log/cycle40-keyboard-gate-probe.md` TOWN40, run `scratchpad/cycle40/runs/tap-D56`].
마을의 씬 6 스테이지 1부터 4까지가 오버레이 5가 로드된 후 실행되는 것이 관측되었다
[H: log/source account: `docs/log/cycle40-keyboard-gate-probe.md` CALL40; receipt provenance unresolved].

## 어디에 있는가

| 함수 또는 심볼 | 모듈 | 역할 | 등급 / 출처 |
|---|---|---|---|
| `func_020a636c` | main | 최상위 씬 머신 | [S: `src/matched/func_020a636c.c`; source account: `port/shim/game/scenestate.c` header] |
| `func_020a6688` / `func_020a6684` | main | 그 상태 세터(`self[24]`)와 게터 | [S: `src/matched/func_020a6688.c`, `src/matched/func_020a6684.c`; source account: `port/shim/game/scenestate.c:19-40`] |
| `func_020b6c0c` | main | 씬 6의 여섯 스테이지 로더, 호출당 한 스테이지, 40 ms 예산 | [S: `config/adm-kr/arm9/symbols.txt` (`func_020b6c0c` at 0x020b6c0c); source account: `port/shim/game/scene6init.c` header] |
| `func_020a5598` | main | 씬 진입 시 스테이지 카운터를 지운다 | [S: `src/matched/func_020a5598.c`; source account: `port/shim/game/scene6init.c` header] |
| `func_020b0b00` | main | 스테이지 5의 리소스 항목 루프 | [S: `src/matched/func_020b0b00.c`; source account: `port/shim/game/stageloop.c` header] |
| `func_020b5e88` | main | 스테이지 6; 메일박스 유휴 값을 쓰는 유일한 함수 | [S: `src/matched/func_020b5e88.c`; source account: `docs/kb/port/sequencer-and-modes.md`] |
| `func_020b6a7c` | main | 씬 6의 업데이트 슬롯, 두 타이틀 게이트 바이트 뒤에 있음 | [S: `src/matched/func_020b6a7c.c`; source account: `port/shim/gfx/pmflist.c:122-131`] |
| `func_020b0bbc` | main | 씬별 채널 목록 순회, 시간 제한 있음 | [S: `src/matched/func_020b0bbc.c`; source account: `port/shim/game/chanlist.c` header] |
| `func_0202f134` | main | 채널 열기 정문, 인자 네 개 | [S: `src/matched/func_0202f134.c`; source account: `port/shim/game/chanopen.c` header] |
| `func_020edbbc` | autoload_2 | 열세 명령어; null 검사, `+0x14`, 꼬리 호출 | [S: `src/matched/func_020edbbc.c`; source account: `port/shim/game/chanopen.c` header] |
| `func_020edc58` | autoload_2 | 세 단계 채널 열기 | [S: `src/matched/func_020edc58.c`; source account: `port/shim/game/chanstage.c:37-66`] |
| `func_020edc20` / `func_020edd30` / `func_020edec8` | autoload_2 | 스테이지 1 훅, 스테이지 2 파라미터 블록, 객체 큐잉 훅 | [S: `src/matched/func_020edc20.c`, `src/matched/func_020edd30.c`, `src/matched/func_020edec8.c`; source account: `port/shim/game/chanstage.c:82-84, 143-156`] |
| `func_020ee660` | autoload_2 | 핸들러 테이블을 순회하며 그것에 대해 객체를 만든다 | [S: `config/adm-kr/arm9/autoload_2/symbols.txt` (`func_020ee660` at 0x020ee660); source account: `port/shim/game/drvopen.c` header] |
| `func_020a6c08` | main | 스크린 매니저의 프레임별 펌프 | [S: `src/matched/func_020a6c08.c`; source account: `port/shim/game/screenpump.c` header] |
| `func_ov003_0221fe10` | ov003 | 채널 13의 생성자; 슬롯 0에 에이커 모델/텍스처 로더 | [S: `src/matched/func_ov003_0221fe10.c`; source account: `port/shim/game/chanopen.c:41-45`] |

## 읽고 쓰는 데이터

| 주소 또는 필드 | 의미 | 쓰는 쪽 | 읽는 쪽 |
|---|---|---|---|
| `0x021fd044` | 채널 핸들러 포인터 배열을 가리키는 포인터 | 초기화(`0x020e3134`), 그다음 씬 | `func_020edc58`, `func_020ee660` [S: `src/matched/func_020edc58.c`; source account: `port/shim/game/chanstage.c:80`] |
| `0x021fcfdc` | 열리고 있는 채널; `0xffff`는 "없음" | `func_020edc58` | 열기 시퀀스 [S: `src/matched/func_020edc58.c`; source account: `port/shim/game/chanstage.c:78, 89`] |
| `0x021fcfd4` | 열기의 스테이지 바이트, 1/2/3/4, 0으로 재설정 | `func_020edc58` | 열기 시퀀스 [S: `src/matched/func_020edc58.c`; source account: `port/shim/game/chanstage.c:79-96`] |
| `0x021f42f0` | 씬 6의 스테이지 카운터 | 진입 시 `func_020a5598`이 지운다 | `func_020b6c0c` [S: `src/matched/func_020a5598.c`; source account: `port/shim/game/scene6init.c` header] |
| `0x021f69d0` | 한 슬롯짜리 요청 메일박스; 바이트 0 `0x3f` = 유휴 | `func_020b5e88` (스테이지 6) | `func_020b6fd0` [S: `src/matched/func_020b5e88.c`, `src/matched/func_020b6fd0.c`; source account: `docs/kb/port/sequencer-and-modes.md`] |
| `data_020e54ac` | 게임 모드 바이트; 0x2c-0x2f는 페이드 띠 | `func_020b6fd0`이 `func_020b5e84`를 통해 | `func_020b65c4`, `func_020412a0` [S: `src/matched/func_020b6fd0.c`, `src/matched/func_020b5e84.c`, `src/matched/func_020b65c4.c`, `src/matched/func_020412a0.c`; source account: `docs/kb/port/sequencer-and-modes.md`] |
| `data_020e3c80` | 상태 16이 5와 같아지기를 기다리는 씬 id | 씬 머신 | `func_020a6684` [S: `src/matched/func_020a6684.c`; source account: `port/shim/game/scenestate.c:31-34`] |
| `0x021c75b8` / `0x021c75b0` | 씬 6의 업데이트 슬롯을 게이트하는 두 바이트 | 확인되지 않음 | `func_020b6a7c` [S: `src/matched/func_020b6a7c.c`; source account: `port/shim/gfx/pmflist.c:124-131`] |
| `data_020e41ec` | 스테이지 5의 리소스 종류 디스패치 테이블 | 정적 | `func_020b0b00` [S: `src/matched/func_020b0b00.c`; source account: `port/shim/game/stageloop.c:23`] |
| `0x020e3134` | `main`의 채널 핸들러 테이블 | 정적 | 초기화의 테이블 포인터 쓰기 [S: `config/adm-kr/arm9/symbols.txt` (`main` at 0x02000c38); source account: `port/shim/gfx/gxdirect_a.c:241`] |
| `0x02239a2c` | 채널 13의 핸들러 레코드 | `ov003`의 정적 데이터 | `func_020edc58`의 테이블 순회 [S: `src/matched/func_020edc58.c`; source account: `port/shim/game/chanopen.c:41-45`] |

## 확인 방법

두 번 탭 마을 레시피(`docs/kb/hybrid/recipes.md` section 3)를 실행하고 로그에서 포트의
채널 계측 줄을 grep한다: `acww chanstage: chan <id> table entry=... *entry=...`는 각 채널의
테이블 항목이 어떤 형태를 취했고 처리되었는지 거부되었는지를 말해 준다
[H: source account: `port/shim/game/chanstage.c:130-141`; direct ROM-source provenance unresolved]; `acww chanlist: count=... from index ...`는
씬의 채널 목록을 출력한다 [H: source account: `port/shim/game/chanlist.c:40-48`; direct ROM-source provenance unresolved]; `acww scenest: -> N`은
첫 40개의 씬 상태 전환을 출력하고 `acww scenest: state=`는 120회 호출마다 머신을
샘플링한다 [H: source account: `port/shim/game/scenestate.c:19-40`; direct ROM-source provenance unresolved]. 계측이 `acww_trace_state()`를 검사하는 곳에서는
그 줄들에 `ACWW_TRACE_STATE`가 필요하다 [H: source account: `port/shim/game/chanopen.c:38`; direct ROM-source provenance unresolved].

"채널 목록이 짧다"와 "순회가 프레임 예산을 다 썼다"를 구분하려면, 출력된 개수를
`acww chanstage` 줄의 수와 비교한다 — 순회는 40 ms로 제한되며
다음 프레임에 재개된다 [H: host/prose inference from `port/shim/game/chanlist.c` header; verify against the ROM function or symbol table and this page's recipe].

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
- ~~채널 목록과 여섯 스테이지 로더 양쪽의 40 ms 예산은 ROM 자체의 프레임 허용치이며 디버그
  값이 아니다.~~ LOAD52로 확정됨: 상수는 `0x28`밀리초이며 `OS_GetTick`을 33514 kHz로
  스케일하고, `func_020b0b00`과 `func_020b6c0c`에서 시험된다(ROM에 있는 33514의 워드
  정렬 발생 32개가 예산 계열을 열거한다) [S: `src/matched/func_020b0b00.c`; log: `docs/log/cycle41-gameplay.md` L52-2].
  아직 열린 것은 WHY 40뿐이다(16.7 ms 프레임의 두 배 반보다 작은 설계상 허용치이며,
  이 계열은 릴리스 코드이므로 디버그 값이 아니다) [H].

## 관련 문서

- `display-objects.md` — 채널의 생성자가 무엇에 합류하는지, 그리고 매 프레임 무엇이 그것을 스텝하는지
- `overlays.md` — 씬의 채널이 상주를 필요로 하는 오버레이
- `boot-and-entry.md` — 제어가 씬 머신에 도달하는 방법
- `memory-map.md` — 이 전역 변수들이 있는 `0x021fxxxx` 띠

## 로더 뒤의 검은 유지: 네 번의 업데이트와 kind-2 아이리스

공유 마을 주민-1 문에서 포트의 57,372..57,432 검은 구간은 60을 로드한 측정 카운터가
아니다. 메인 루프 스케줄에서 네 번 업데이트되는 지연과 kind-2 아이리스의 진행/정리로
구성된다
[E: `scratchpad/handoff/black-hold-1/mechanism.json`, `original-comparison.json`; current receipt locator: `scratchpad/handoff/black-hold-1/original-comparison.json`].

| 워드 또는 바이트 | 측정된 역할 | 영수증 |
|---|---|---|
| `0x021f42e0` 바이트 | 57,372에서 4로 설정되고 57,384에서 0으로 감소 | [E: `scratchpad/handoff/black-hold-1/delay-summary.json`] |
| `0x021c75b8` / `+1` 바이트 | 페이드 상태 / 종류; 57,384에서 1 / 2, 57,432에서 2 / 2 | [E: `scratchpad/handoff/black-hold-1/fade-summary.json`] |
| `0x021c75bc` 워드 | 4096에서 0으로 진행, -273/clamp 업데이트 열여섯 번, 57,429에서 0 | [E: `scratchpad/handoff/black-hold-1/fade-summary.json`] |
| `0x021c75c0` 워드 | 부호 있는 스텝 -273, 진행 값이 0이 되면 클리어 | [E: `scratchpad/handoff/black-hold-1/fade-summary.json`] |
| `0x021fbdd0` 워드 | 57,372..57,432 동안 메인 루프 카운트 19,059에서 19,079 | [E: `scratchpad/handoff/black-hold-1/progress-summary.json`] |

마지막 기록자는 `func_02001ba4`이며, PC는 `0x02001baa`, LR은 `0x02041f2b`다.
57,432에서 윈도 마스크 `0x0213fe8c`에 바이트 0을 저장한다. 호출자인 정리 함수
`func_02041f20`은 서브엔진 윈도 마스크와 BG2 평면 비트도 클리어한다. 아래 화면은
57,431에서 완전히 검은 상태였다가 57,432에서 집 내부로 바뀐다(평균 휘도 84.02095)
[E: `scratchpad/handoff/black-hold-1/door-summary.json`,
`fade-summary.json`, `door-pictures.json`; current receipt locator: `scratchpad/handoff/black-hold-1/fade-summary.json`, `scratchpad/handoff/black-hold-1/door-pictures.json`].

네이티브로 등록된 `func_0206e63c`는 `func_02054070`을 호출한 다음
`func_02041c28` / `func_020e88dc`가 루프 카운터가 증가하기 전에 진행 값을 갱신하게
한다. 따라서 인터프리터의 저장 감시는 초기화와 정리는 관측하지만 네이티브 진행 저장은
관측할 수 없다. 그 침묵은 타이머가 멈췄다는 뜻이 아니다 [S: main, `port/shim/gfx/frameswap.c`,
`src/matched/func_02054070.c`, `port/build/shadow/func_02041c28.c`]
[E: `scratchpad/handoff/black-hold-1/source-evidence.json`, `progress-values-summary.json`; current receipt locator: `scratchpad/handoff/black-hold-1/progress-values-summary.json`].

원본도 같은 kind-2 페이드와 같은 진행 값 열여섯 개를 실행하지만, 진행 중인 57,315부터
확장되는 원형 아이리스를 그린다. 페이드는 57,311에서 시작하고 57,359에서 정리된다:
포트와 같은 48프레임 단계다. 메일박스가 57,305에서 지워질 때 원본의 지연 바이트가 이미
2이고 포트는 4이므로, 전체 클리어 후 구간은 60이 아니라 **54**다. 이 6프레임의 스케줄
잔여분은 보이지 않는 아이리스와 별개로 남는다
[O: `scratchpad/handoff/black-hold-1/original-summary.json`, `original-pictures.json`]
[E: `scratchpad/handoff/black-hold-1/original-comparison.json`].

추가로 범위를 좁힐 후속 조사는 가정한 MASTER_BRIGHT 램프가 아니라 HBlank 가드다.
PC `0x0204216e`의 실제 리더는 `func_02042154`에 속하며, 그 WIN0H 쓰기에는 DISPSTAT
비트 1이 필요하다. 포트의 합성 `dispstat_load`는 그 비트를 항상 클리어하고,
`scanline_hook`은 라인 번호를 설정하지만 HBlank 위상은 제공하지 않는다. (이 부록을
측정한 대상은 IRIS54 전의 산출물이었다. IRIS54가 스캔라인 훅 주변에서 플래그를 올렸고,
아이리스는 이제 라인별로 그려진다 — `wiki/engine/graphics-pipeline.md`의 "포트는 이를
재현한다"를 보라.) 57,400..57,402에서 관측된 유일한 메인 WIN0H 쓰기는
`func_02042120`(PC `0x02042128`)의 `0x8080`이다. 수정은 적용되지 않았고 반사실적 실행도
하지 않았다. RWATCH는 I/O 훅 전에 백킹 워드를 보고하므로, 그 값은 합성된 반환값으로
인용해서는 안 된다 [S: main,
`src/matched/func_02042154.c`, `port/interp/interp_boot.c`,
`port/interp/interp_cpu.c`]
[E: `scratchpad/handoff/black-hold-1/guard-summary.json`].
