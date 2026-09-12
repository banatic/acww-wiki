# 라이브 플레이: 키보드로 포트를 조작하기
<!-- source: wiki/experiments/live-play.md -->

**상태: 실행됨, 2026-09-09 (LIVE41, `fd8da4d8`), PERF42 (`fbfc987d`) 이후 재측정, 그리고
2026-09-10에 세션 전체를 끝까지 통과함 (LIVE42, `0687d989` 및 LIVE42 편집분).**
포트는 키보드로 플레이할 수 있다: 명령 하나로 DS 자체의 59.8261 Hz에 맞춰 페이싱되고,
2배 창에서, 사운드와 함께, 유지되는 세이브 파일과 실제 날짜·시각으로 실행된다.
**LIVE42는 LIVE41의 미해결 항목을 종결시킨다.** 이제 플레이어는 새 마을을 시작하고, 게임
자체의 한국어 키보드에서 자기 이름과 마을 이름을 입력하고, 택시에서 내리고, 펠리의 안내로
마을 회관을 둘러보고, 마을을 걷고, 지도와 주머니를 열고, 자기 집을 찾고, 너굴과의 도착
절차를 마치고, 세이브를 쓰고, 종료하고, 저장한 마을로 다시 실행할 수 있다 -- 전부 실제
Windows 메시지만으로 구동된 129,001 프레임(약 36분)짜리 세션 하나에서
[E: `scratchpad/live42/RECEIPTS.md`].

**2026-09-10에 회귀 검사로 재실행 (LIVE43, `4ec6dff0`, C 코드 변경 없음).** ARM7 오디오
드라이버, 빠른 카드 읽기, 상한이 있는 env 리더, 스레드 쿼터를 가진 빌드에서 같은 세션을
돌렸다: **경로 전체가 여전히 동작하고 부팅은 2.3배 빨라졌다**. 744페이지 플래시 읽기가
이제 747프레임(12.5 s) 대신 **48프레임(0.80 s)**이 들어, 타이틀 화면이 ~59 s 대신
**26 s**에, 이름 키보드가 ~160 s 대신 **104 s**에 도착한다; 세이브를 쓰기까지의 새 마을
세션 전체는 **23분 20초 / 83,430프레임**이 걸렸다. 마을 플레이 190 s 동안 호스트 시계에
대해 측정한 프레임 레이트는 **59.8254 fps** -- NDS 자체의 59.8261에서 0.0007 차이다.
네 번의 실행 모두에서 실제 장치로 소리가 나왔고 **9,186개 중 9,186개의 노트가 울렸으며
누락은 없었다**; 세이브는 두 뱅크 모두에서 검증되고 재실행은 이어하기 경로를 탄다.
네 번의 실행, 132,000프레임, 어떤 종류의 폴트도 **0건**
[E: `scratchpad/live43/RECEIPTS.md`, `receipt.json`; `docs/log/cycle42-save.md` LIVE43].
거기서 나온 라이브 노트 셋: 키보드가 뜬 뒤 `Z`를 그만 누르면 `ㅃ` 이름 필드는 나타나지
않는다(NAME42의 규칙, 끝에서 끝까지 확인됨); 자기 집 현관문은 방향키를 누르고 있는 것이
아니라 **A 버튼**을 원한다; 그리고 `play.py`의 실제 시계 때문에 저녁에는 마을이 잠들어
있다 -- 같은 세이브에서 `--time 113000`을 주자 80 s 안에 주민이 걸어와 말을 걸었다.

**회귀 검사로 다시 실행, 2026-09-11 (LIVE44, `24b1a636` IRIS54, C 변경 없음).** 픽셀별
창과 마스터 밝기를 갖춘 빌드(FADE52), 스캔라인별 아이리스(IRIS54), 스위치로 보호된
서브프레임 시계(TICK53/MEM54, 둘 다 기본값은 OFF이며 여기서도 꺼져 있음을 확인함), 로더
계측기와 스레드 쿼터를 갖춘 빌드에서 같은 결과물을 다시 확인했다: **다섯 번의 실행,
246,510프레임, 모두 exit 0, `unimplemented`, `STOP status`, `fault_pc`, queue-full 줄은
0건**이다. 타이틀 화면은 이제 **24 s**에 도착하고, 저장된 마을은 이어하기 경로로 로드되며,
해변에서는 `X`를 한 번 눌러 조개를 얻고 세이브 파일에도 남는다. 벚나무는 흔들려 빈 나무가
되었고, **너굴 상점은 360벨짜리 조개에 190벨, 2,000벨짜리 체리에 100벨을 지급했다 --
90 = base/4이고 과일에는 고정 100이다**. 지갑은 385 -> 575가 되었고, START ->
저장하고 마치기는 양쪽 뱅크에서 검증되는 세이브를 쓴다.

**핵심은 전환이다.** 건물에서 걸어 나오면 이제 둥근 IRIS가 닫힌다. 프레임에 고정한 캡처가
아니라 픽셀에서 라이브로 측정했으며, 빛이 드는 열 범위는 DS 자체의 14단계를 따라
`119..136`으로 줄어들고 빛이 드는 행도 함께 닫힌다. 아래 화면의 평균 휘도는
`30.51, 24.98, 20.45, 15.73, 10.49, 6.32, 2.84, 0.62`로 읽혔다 -- 외부 캡처에서
사람이 직접 누른 키로 얻은 IRIS54의 프레임 고정 수치와 소수점 둘째 자리까지 같다.
프레임 레이트는 300 s 동안 호스트 시계 대비 **59.8366 fps**이다(더 짧은 창은 캡션의
양자화 때문에 0.1 높게 읽힌다). 포트 자체 카운터의 창 198개 평균은 59.71이고 모든 하락은
씬 로드에서 발생했으며, `ACWW_FRAMETIME`은 마을 렌더링이 **4.2 ms**라고 말한다. PERF42의
6.5-7.0과 비교하면 창 마스크에는 측정 가능한 비용이 없다. 사운드는 `FIRST SOUND at
frame 38`, 피크 32,006, 싱크 `dropped 0 frames`였고 다섯 실행 중 네 실행에서는 모든
노트가 울렸다. 다섯 번째는 **`no instrument`로 22,224개 중 19개가 누락**되어 LIVE43보다
한 수치 나쁘며 원인은 아직 특정되지 않았다 [E: `scratchpad/live44/RECEIPTS.md`, `runs/*/receipt.json`;
`docs/log/cycle42-save.md` LIVE44]. 여기서 얻은 라이브 관측 세 가지: 너굴 표지판 아래의
어두운 틈은 WINDOW이고 문은 그 옆 패널이며, Redd의 비밀번호 키보드는 빈 칸에 노란
PLACEHOLDER 표시를 그리고 무엇인가 입력할 때까지 결정 입력을 조용히 거부한다. 그리고
걸어 다니는 주민은 아홉 번 시도해도 대화하려고 세울 수 없었지만, 두 상점 주인은 첫 `Z`에
대답했다.

## 목적

다른 페이지의 모든 레시피는 스크립트다: 시계를 고정하고, 스토어를 끄고, 진행 줄을
출력하고, 호스트가 낼 수 있는 최대 속도로 돈다. 사람에게는 이 넷 모두의 반대가 필요하다.
이 페이지는 스크립트된 실행이 측정하는 것을 아무것도 바꾸지 않으면서 사람에게 그것을
주는 방법이며, 실제로 바꾸지 않았다는 영수증이다.

## 레시피

    python port/tools/play.py

그게 전부다 [H: log/source account: `port/tools/play.py`; `docs/kb/hybrid/live-play.md`; receipt provenance unresolved]. 이 명령은
`port/build/acww.exe`를 인터프리터 경로에서 실제 시계로, `%LOCALAPPDATA%/acww/town.sav`의
세이브와 함께, 페이서를 켜고, 인터프리터의 진행 줄을 끄고, 콘솔 창 없이 실행한다; 로그는
세이브 옆에 남는다. 옵션: `--save PATH`, `--log PATH`, `--date YYYYMMDD --time HHMMSS`,
`--state PATH`(세이브스테이트 재개 -- 이 방법이면 전체 재생 대신 약 80 s로 마을에
도달한다), `--console`, `--verbose`, `--wait`, `--env K=V`, 그리고 LIVE42부터 `--mute`,
`--wav PATH`, `--no-sink` -- **이제 사운드는 기본적으로 켜져 있다**.

**문서화된 명령줄 대신 런처를 쓰는 이유**: 환경의 기본값 넷은 영수증에는 맞고 플레이어에게는
틀리다 -- RTC는 모든 레시피에서 고정되고, `ACWW_SAVE`는 의도적으로 설정되지 않으며,
인터프리터의 진행 줄은 9,000프레임 OFF 레시피에서 1,738,500번의 쓰기와 101 MB의 로그(프레임
시간의 약 20%)를 소모하고, 콘솔 서브시스템 exe는 터미널에서 실행되지 않으면 콘솔 창을
띄운다 [H: log/source account: `docs/kb/hybrid/live-play.md`; receipt provenance unresolved].

### 키 맵

스크립트된 키가 없는 모든 실행의 첫 프레임에 영어와 한국어로 전부 출력된다
[H: host/prose inference from `port/platform/hostinput.c`; verify against the ROM function or symbol table and this page's recipe].

| 키 | DS | 키 | DS |
|---|---|---|---|
| 화살표 | 십자키 | `Z` | A |
| `X` | B | `A` | Y |
| `S` | X | `Enter` / `Space` | START |
| `Backspace` / `RShift` | SELECT | `Q` / `W` | L / R |
| 아래 화면에서 왼쪽 마우스 | 스타일러스(드래그하면 획을 긋는다) | `Escape` | 종료, 세이브를 플러시하면서 |

### 페이서

포트는 NDS 자체의 속도 -- 33.513982 MHz / 560190 사이클 = **59.8261 Hz** -- 에 맞춰
`timeBeginPeriod(1)`, 마지막 1밀리초를 제외한 전부를 sleep, 나머지는 yield로 페이싱한다.
데드라인은 프레임마다 정확히 한 주기씩 전진하므로 드리프트가 없고, 두 프레임 이상 뒤처진
호스트는 **전력 질주 대신 기준을 다시 잡으므로**, 멈춤이 빨리감기로 바뀔 수 없다
[H: host-source account from `port/platform/frame.c`; verify with a retained scripted run and frame using this page's recipe].

**스크립트 냄새가 나는 것에는 기본적으로 꺼져 있다.** `ACWW_KEYS*`, `ACWW_TOUCH*`,
`ACWW_SHOT*` 변수 중 하나라도, 또는 `ACWW_STOP_FRAME`, 또는 `ACWW_NOPACE=1`이 있으면
꺼진다; 환경은 접두사로 한 번 스캔되므로 새로운 `ACWW_KEYS4`도 아무것도 고치지 않고
포함된다. `ACWW_PACE=1` 또는 `ACWW_NOPACE=0`은 페이서 자체를 측정하기 위해 강제로 켠다
[H: log/source account: `docs/kb/hybrid/live-play.md`; receipt provenance unresolved].

## 플레이어가 하는 일, 단계별로

측정됨 (LIVE42). 모든 입력은 포트 자신의 창 큐로 들어가는 `PostMessageA` --
`WM_KEYDOWN`/`WM_KEYUP`과 `WM_LBUTTONDOWN`/`WM_LBUTTONUP` -- 이므로, 실제 키보드와 마우스가
지나는 경로를 그대로 탄다: 포트의 wndproc, `host_vk[]` / 펜 에지 큐, `hostinput.c`의
액티브-로우 패드 레지스터 둘, `touch.c`의 최소 접촉. **`ACWW_KEYS*`, `ACWW_TOUCH*`,
`ACWW_SHOT*`, `ACWW_STOP_FRAME`, `ACWW_PADSCRIPT`는 어디에도 설정되지 않았고**, 그것이
페이서를 켜진 채로, 입력을 라이브 경로에 유지하는 요인이다. 그림은 `scratchpad/live42/shots/`;
드라이버는 `scratchpad/live42/drive.py`.

| # | 할 일 | 나타나는 것 | 프레임 | E |
|---|---|---|---|---|
| 1 | 기다린다 | 타이틀 화면, 낮에 -- 시계가 실제여서, LIVE41의 것은 밤이었다 | 3,510 | `01-title.png` |
| 2 | 아래 화면을 한 번 클릭 | Rover: 안녕하세요！놀러 오셨군요 | 4,290 | `02-after-title-tap.png` |
| 3 | `Z` x4 | 택시 안 | 5,100 | `03-menu.png` |
| 4 | `Z` | Rover의 질문들, 일부는 두 선택지 상자 포함 | 7,050 | `04-taxi.png` |
| 5 | 선택지를 클릭 | 받아들인다 -- 스타일러스가 대화에서 동작한다 | 8,490 | `05-after-choice-tap.png` |
| 6 | `Z` | **이름 키보드**, 당신 이름은? | 9,601 | `06-taxi2.png`, `06-lower-4x.png` |
| 7 | DS(33,128)의 ㅁ을 클릭, 그다음 DS(193,128)의 ㅣ | 두 탭이 한 음절을 조합한다 | 12,630 | `07-typed-mi.png` |
| 8 | DS(231,112)의 백스페이스를 클릭 | 음절이 다시 지워진다 | 18,090 | `08-bksp.png` |
| 9 | 이름을 입력하고 DS(220,179)의 결정을 클릭 | 한 번의 탭으로 확정; Rover가 이름을 읽어 준다 | 20,190 | `09-typed-mimi.png`, `10-nameline.png` |
| 10 | `Z` | **마을 이름 키보드**, 마을 이름은? | 24,390 | `12-townkbd.png` |
| 11 | 입력하고 결정 | 헤헷 농담이야, 농담ー！ | 27,390 | `13-townname.png`, `14-townconfirm.png` |
| 12 | `Z` | **택시 밖으로**, 마을 회관 앞 포장도로 위, 위 화면에 하늘 | 31,500 | `16-taxi4.png` |
| 13 | 위를 누르고 있기 | 안쪽, 펠리(Pelly)와 함께 | 32,700 | `17-townhall.png` |
| 14 | `Z` | 펠리의 지도 페이지, HUD에 **9/10 목 AM11:27** -- 실제 날짜와 시각 | 34,770 | `18-pelly.png` |
| 15 | 각 질문에서 **아래 다음 `Z`** | 안내가 그럼 다녀 오세요！에서 끝난다 | 50k-56k | `steps.png` |
| 16 | 마지막 상자를 지나도록 아래를 누르고 있기 | **마을 밖으로**: 위에는 하늘, 아래에는 땅, 오른쪽 위에 지도 화살표 | 61,260 | `35-escape.png` |
| 17 | `S`(X 버튼) | **지도**: 마을, 건물들, 주민 패치 / 핑키 / 탱크 | 62,070 | `36-map.png` |
| 18 | `A`(Y 버튼) | **주머니**: 초상, 이름, `00000` 벨, 격자, 편지 슬롯 열 개 | 62,910 | `37-pockets.png` |
| 19 | 화살표를 양방향으로 600프레임씩 누르고 있기 | 마을이 걸어간다; 캡션이 정확히 600만큼 전진한다 | 90,270-91,710 | `walk-montage.png`, `walk.txt` |
| 20 | `Enter`(START) | **어머? 지금은 아직 저장하지 못하나 봐요** -- SAVE42의 도착 시 거부, 라이브로 | 94,170 | `41-start.png` |
| 21 | 지도의 초록 집 아이콘으로 걸어가기 | 플레이어 자신의 집, 빨간 우편함과 함께 | 111,210 | `43-mapbox.png`, `45-nearhouse.png` |
| 22 | `A`로 앞벽에 미끄러져 들어가기 | 안쪽: 4x4 방, 벤치, 피규어, 스테레오 | 113,910 | `47-enter.png` |
| 23 | 아래를 누르고 있기 | 문 앞의 너굴(Tom Nook) | 115,050 | `48-nook.png` |
| 24 | `Z` | 너굴이 그려지고, 손짓하며, 대출 연설을 한다 | 116,700 | `49-nook2.png` |
| 25 | `Z` | 그럼 나중에 가게로 날 찾아와구리 | 118,620 | `50-nook3.png` |
| 26 | `Enter`(START) | **오늘은 여기까지 하시겠습니까?** -- 거부가 사라졌다 | 120,001 | `52-savemenu.png` |
| 27 | 저장하고 마치기를 두 번 클릭 | 저장하고 있습니다 전원을 끄지 말고 그대로 기다려 주십시오！ | 123,270 | `53-zoom.png`, `54-saving.png`, `55-saved.png` |
| 28 | `Z` | 다시 타이틀 화면 -- **방금 저장한 마을을 보여 주며**, 우편함까지 그대로 | 128,401 | `58-postsave.png` |
| 29 | `Escape` | `acww save: flushed the backup store to disk`, 0.11 s 만에 exit 0 | 129,001 | `escape-time.txt` |
| 30 | 같은 `--save`로 `play.py`를 다시 | 타이틀 화면이 당신의 마을이다 | 3,510 (B) | `60-relaunch-title.png` |
| 31 | 클릭, 그다음 `Z` | **다락방 침대에서 깨어난다**: 이 방은 당신의 집에 있는 다락방입니다 | 6,630 (B) | `63-wake.png` |
| 32 | `Z` | 자기 집 현관문 밖, HUD 9/10 목 AM11:59. 택시도 없고, 키보드 둘 다 없음 | 11,040 (B) | `66-continued-town.png` |

모든 실행은, 페이싱 여부와 무관하게, `acww pace: NN.NN fps over 600 frames, frame N (paced|unpaced)`를
출력한다 -- "느린 것인가 멈춘 것인가"에 대한 정직한 답이다 [H: source/log account from `port/platform/frame.c`; verify with a retained run using this page's recipe]. LIVE42의
세 세션 전체에서 이 줄은 거의 모든 창에서 **59.82**를 읽는다; 예외는 부팅(58.7, 54.6)과
방 전환 양쪽의 로드(58.3-58.4)다. 독립적인 검사는 19단계다: 벽시계로 600프레임 동안 키를
누르고 있자 캡션이 정확히 600프레임 전진했다, 양방향 모두 [E: `scratchpad/live42/walk.txt`].

**세이브는 진짜다.** 게임은 256바이트 페이지를 `0x00000..0x2e7f8`에 걸쳐 썼고, 각 페이지는
한 프레임 뒤에 검증되었으며, 불일치는 0이었다. 그 이미지에 대한 `savetool.py check`는
`checksum stored 0xaf74 computed 0xaf74 VERIFIES`와 `the game would LOAD this bank`를 읽고,
주민 8명 중 3명이 차 있다 -- 새 마을이다 [E: `scratchpad/live42/sessionA.log`; SAVE43 reached the same chain under a pad script].

### 워크스루가 배워야 했던 세 가지

**도착 대화는 저절로 다시 시작된다** -- 플레이어가 펠리의 카운터에 서 있는 동안: 상자는
`A`로 닫히고 아무것도 누르지 않아도 2.5 s 안에 어머 무슨 일 있으신가요?가 돌아온다
[H: log/source account: `shots/32-free.png`, frame 56,310, 150 frames after the closing press; receipt provenance unresolved]. 마지막 상자가 닫히기
전에 떠나고 싶은 방향을 미리 누르고 있으면 조작이 돌아오는 순간 걸어 나간다. 안내는
혹시 지도를 어떻게 꺼내는지 잊으셨나요?에서 반복되기도 하는데, `A`가 첫 번째 선택지,
즉 "네, 다시 알려 주세요"를 고르기 때문이다 -- 먼저 아래를 누른다 [H: log/source account: `shots/21-pelly4.png` against
`24-declined.png`; receipt provenance unresolved].

**키 격자는 캡처 하나로 측정할 수 있다.** 창 캡처에서 아래 화면을 잘라내고(클라이언트
512x768이므로 아래 화면은 아래쪽 절반이고, 기본 2배에서 DS = 클라이언트/2), 다시 2배로
확대하면 DS 좌표는 그 이미지의 픽셀을 4로 나눈 것이다. 행은 DS y = 96, 112, 128, 144에
있고, 열은 x = 14부터 DS 20픽셀 간격이다; 백스페이스는 DS(231,112)이고 결정은
DS(220,179)다 -- `run_town.py`가 오래전부터 쓰던 `ACWW_TOUCH_X=221 ACWW_TOUCH_Y=181`이
줄곧 가리키던 바로 그곳이다 [H: log/source account: `shots/06-lower-4x.png`; receipt provenance unresolved].

**지도 페이지로 길 찾기가 된다.** `scratchpad/live42/nav.py`는 화살표로 걷고, 지도를 열고,
플레이어 마커(B173 G90 R247)와 플레이어 자신의 집 아이콘(B0 G165 R0)을 색으로 찾는다;
대각선으로 600프레임 걸으면 마커가 지도 픽셀 82만큼 움직이고, 세 번의 반복으로 집에
다다랐다. 기록된 함정 둘: **깜빡임 감지는 동작하지 않는다** -- 지도의 강이 애니메이션되므로,
지도 프레임 안에서 가장 크게 변하는 것은 마커가 아니라 물이다 -- 그리고 "초록 집 아이콘이
보이는가"는 "지도가 열려 있는가"의 검사가 되지 못하는데, 마을의 나무 잎이 같은 순수한
진초록이기 때문이다.

## 입력 지연, 플레이어가 느끼는 대로

측정됨 (LIVE42; 전체 표와 방법은 `scratchpad/live42/LATENCY.md`).

| 질문 | 답 | E |
|---|---|---|
| DS의 패드 레지스터가 키를 담을 때까지 | **0.07-0.98프레임, 중앙값 0.69** -- 모든 시행에서 같은 프레임 | `lat-padpublish.txt` |
| 픽셀이 바뀔 때까지, 키 | **8.7-12.7프레임** (145-212 ms), n=6 | `lat-keys.txt`, `lat-right.txt` |
| 픽셀이 바뀔 때까지, 클릭 | **11.3-13.3프레임** (188-223 ms), n=6 | `lat-taps.txt`, `lat-firsttap.txt` |
| 클릭을 얼마나 오래 유지해야 하는가 | **아무 길이나**: 서브프레임에서 400 ms까지의 유지 시간에서 24/24가 ROM에 도달 | `lat-touch-sweep.txt` |
| Escape에서 프로세스 종료까지 | **0.11-0.13 s**, 세 세션 | `escape-time.txt` |

**포트 자신의 입력 경로는 한 프레임도 안 든다** -- `acww_window_pump()`가 게임이
샘플링하기 전에 프레임마다 한 번 큐를 비우고, 그게 전부다. 플레이어가 그림을 기다리는
9-13프레임은 ROM 자체의 샘플링 주기와 ROM 자체의 열림 애니메이션이다. **12프레임을
포트 오버헤드로 인용하지 말 것**: 지연에 대한 에뮬레이터 차분이 없으므로, 여기서는 "ROM이
원래 이렇다"와 "포트가 이걸 느리게 한다"를 분리하는 것이 아무것도 없다.

50-100 ms의 보통 마우스 클릭은 안정적으로 등록되고, 한 프레임보다 짧은 클릭도 그렇다 --
`ACWW_TOUCH_MIN_FRAMES`(4, 약 67 ms)가 제 몫을 하는 것이다.

**계측기, 다시 필요할 것이므로.** `PrintWindow`는 캡처 하나에 **37.0 ms**, 두 프레임
이상이 들고, 캡션의 프레임 번호는 초당 두 번만 갱신되므로 둘 다 입력의 시간을 잴 수 없다.
창 자신의 DC에서 `BitBlt`(`GetDC(hwnd)`; 클래스가 `CS_OWNDC`이고 `acww_present`가 거기로
곧장 StretchBlt한다)는 200x160 패치에 **0.21 ms**가 들고, 화면 DC에서의 BitBlt가 검게
나오는 세션에서도 실제 픽셀을 돌려준다 [H: log/source account: `drive.py`, `FastProbe`; receipt provenance unresolved].

## 사운드: 이제 플레이어가 듣는다, 그리고 이 기계에서 장치까지 도달했다

`play.py`는 `ACWW_SND`를 설정한 적이 없었고, 이 변수는 모든 레시피에서 설정되지 않아
꺼져 있으므로, 런처는 소리 없는 게임을 내보내고 있었다 [E: `scratchpad/live42/session1.log`, the abandoned first launch]. 이제 기본적으로 켜지고, `--mute`, `--wav PATH`, `--no-sink`가 있다.

측정됨: `acww snd: driver ON (ACWW_SND=1)`, `FIRST SOUND at frame 38`, 센서스에 21개의
서로 다른 tag-7 명령 id(`PREPARE_SEQ` 38, `START_PREPARED_SEQ` 38, `TRACK_PARAM` 111,
`PLAYER_PARAM` 75; `SETUP_ALARM`만이 아직 디스패치되지 않고 로그만 된다), 노트 43개
시도에 **43개 울림, 어떤 이유로도 누락 0**, 최대 동시 채널 7, 그리고 32,768 Hz 스테레오의
33.73 s WAV 티(tee), 피크 20,357, 샘플의 57.7%가 64 초과 [H: log/source account: `sessionC.log`, `sessionC.wav`; receipt provenance unresolved].

**그리고 `docs/kb/hybrid/audio.md`의 "이 기계의 세션에는 오디오 엔드포인트가 없다"는
항상 참은 아니다.** 세션 A는 `GetDefaultAudioEndpoint failed, code 0x80070490`과
`waveOutGetNumDevs = 0`을 받았다; 40분 뒤 같은 기계의 같은 사용자 세션에서 세션 B와 C는
`acww snd: sink WASAPI shared mode, 32768 Hz stereo, device buffer 6554 frames`를 받았다 --
싱크가 열렸고 게임이 소리를 내어 재생했다 [H: log/source account: `sessionA.log` against `sessionB.log`; receipt provenance unresolved].

**스타일러스 발견 사항, 그리고 이것이 라이브 플레이가 동작하기 위해 바뀌어야 했던 유일한
것이다.** 창의 에지 큐는 이미 한 프레임보다 짧은 클릭이 유실되지 않음을 보장했다. 그러나
ROM은 최신 샘플로 끝나는 **연속 세 개의 양호한 샘플**이 있을 때만 접촉을 공개하고, ARM7
샘플러는 프레임당 네 샘플을 쓰면서 펜업 샘플을 INVALID로 표시하며, ROM 자체의 샘플러는
메인 루프 본체에서 돈다 -- 측정치는 약 **세 프레임에 한 번**이다. 따라서 한 프레임짜리
접촉은 ROM이 보기 전에 8~12개의 무효 샘플 아래에 묻힌다. 타이틀 화면에서 라이브로 측정:
메시지 펌프 한 번 안의 DOWN+UP은 `acww touch: DOWN x=128 y=96`을 냈고 `TP_POINT` 변화는
전혀 없었다; 같은 클릭을 400 ms 유지하자 `trig 1`인 `TP_POINT`가 나오고 화면이 넘어갔으며,
ROM의 공개는 프레임 7569, 7572, 7581, 7584에 있었다 -- 세 프레임 주기가 눈에 보인다
[H: log/source account: `docs/kb/hybrid/live-play.md`; `../systems/input-and-touch.md`; `touch-latency.md`; receipt provenance unresolved].
이제 소비된 접촉은 `ACWW_TOUCH_MIN_FRAMES` 프레임(4, 약 67 ms) 동안 유지되는데, 이는
어떤 사람의 클릭보다도 훨씬 짧고, 그러면 같은 서브프레임 클릭이 ROM에 도달한다.

### 비용, PERF42 전과 후

LIVE41 자체의 측정은 포트가 실제 게임 내용을 **두 경로 모두에서 30-40 fps**로, 인터프리트
경로와 네이티브 경로 똑같이 렌더링한다는 것이었으므로, 인터프리터는 원인이 아니었다:
`acww_nds2d_frame`이 16.71 ms 프레임 중 14-22 ms를, 게임 자체의 프레임이 4-6 ms를 썼다
[E: `ACWW_FRAMETIME=1`, `scratchpad/liveplay/frametime/`]. **PERF42가 같은 날 밤 그 간격을
닫았다**: 그리기는 택시에서 7.3 ms, 마을에서 6.2 ms, 페이싱 없이 77과 92 fps이고, 페이싱된
라이브 실행은 창을 연 채 59.82 Hz를 유지한다 [H: log/source account: `docs/kb/hybrid/render-perf.md` section 5;
`../engine/graphics-pipeline.md`; receipt provenance unresolved]. LIVE41은 또한 잘못된 렌더러를 지목했다 -- 단계 보고서는
26.5 ms 중 21.1이 2D 컴포지터가 아니라 3D 래스터라이저였음을 보여 준다 [H: log/source account: `docs/kb/hybrid/render-perf.md` section 5;
`../engine/graphics-pipeline.md`, section 3; receipt provenance unresolved].

## 스크립트된 실행이 영향받지 않는다는 영수증

이것이 이 페이지가 레시피들 옆에 존재할 수 있는 이유 전부다.

- OFF 레시피, 프레임 4,500..9,000을 150마다: 손대지 않은 `174ae9e3` 빌드와 LIVE41 빌드
  사이에서 **31/31 SHA-256 동일** [E: `scratchpad/liveplay/exactness-off.json`].
- 페이싱된 패드 스크립트 실행은 페이싱 없는 쌍둥이와 **31/31** 같다
  [E: `scratchpad/liveplay/exactness-paced.json`].
- 마을 레시피를 페이싱 대 비페이싱으로, 11프레임: **11/11 정확히 일치**, 한 링크 뒤에
  측정 [E: `scratchpad/perf42/exactness-town-paced.json`].
- 렌더러를 치우고(`ACWW_HEADLESS=1`) 강제로 켜면, 달성 속도는 **연속 여덟 개의 600프레임
  창에서 59.82 fps**, 4,800프레임이 목표의 0.01 이내 [E: `scratchpad/liveplay/paced-hl2/`].

## 반증 조건

- "사람이 플레이했다"를 "사람이 앉아서 플레이했다"로 읽는 것. LIVE42 표의 모든 입력은
  스크립트가 포스트한 것이다 -- 포트 자신의 창 큐로 들어가는 `PostMessageA`. 그것은
  키보드와 마우스가 지나는 것과 같은 경로(wndproc, `host_vk[]`, 펜 에지 큐, 패드
  레지스터)이고 그래서 페이서가 켜진 채였고 타이밍이 의미를 가지지만, 한 쌍의 손은
  아니다. 이제 확정된 것은 **게임을 그 경로로 오프닝 전체를 통과시킬 수 있다**는 것이다;
  아직 측정되지 않은 것은 그것이 쾌적한가다 -- 아무도 손맛을 판단하지 않았고, 9-13프레임의
  입력-그림 수치는 포트와 ROM 사이에 귀속되지 않았다.
- LIVE42 워크스루를 원본에 대한 주장으로 읽는 것. 이름 필드의 `ㅃ` 프리필(아래)이 가장
  명확한 사례다: 그것은 실재하고, 세이브 파일에 도달하며, 여기의 어떤 것도 ROM이 똑같이
  하지 않는다고 말하지 않는다. 이 세션에는 오라클 조건이 없다.
- 페이서를 `ACWW_HEADLESS=1`로 측정하고 그것을 프레임 레이트라 부르는 것. 그 조건은
  래스터라이저를 완전히 건너뛰므로 페이서만을 측정할 수 있을 뿐이다; 창을 연 조건이
  플레이어가 얻는 숫자다.
- 페이싱된 실행의 58.4-59.7 fps 창을 렌더러 비용으로 읽는 것. 이 기계에서 그 창들은
  경합(B14)이다: 헤드리스 조건은 모든 창에서 59.82를 유지하고 같은 레시피를 페이싱 없이
  돌리면 91.7 fps다 -- 10 ms의 여유가 있는 프레임은 다른 무언가가 코어를 가져가지 않는 한
  데드라인을 놓치지 않는다 [H: log/source account: `docs/kb/hybrid/render-perf.md` section 5; receipt provenance unresolved].
- 라이브 세션을 스크립트된 레퍼런스와 비교하는 것. `play.py`는 실제 시계를 쓰고, RTC42
  이후로 시계는 낮/밤 블렌드를 통해 그림의 매 프레임을 움직인다
  [H: log/source account: `../systems/time-and-rtc.md`; receipt provenance unresolved].

## 거친 모서리, 고친 것과 남긴 것

측정됨 (LIVE42). 아래의 모든 수정은 게이트를 거쳤다: `offgate.py --check --ref
scratchpad/offgate/33376a19/offgate.json`은 손대지 않은 빌드에서, `window.c` + `play.py`
편집 뒤에, 그리고 `frame.c` 편집 뒤에 다시 **31/31 EXACT**를 읽었다.

| 모서리 | 플레이어가 겪은 것 | 수정 |
|---|---|---|
| 소리 없음 | `play.py`가 `ACWW_SND`를 설정한 적이 없었다 | 이제 설정한다; `--mute`가 예전 동작을 되돌린다 |
| 창이 포커스를 가져가지 않음 | 게임은 터미널에서 실행되고 터미널이 전경을 유지한다 -- 그래서 터치를 요구하는 게임에 처음 입력한 것이 셸로 갔다 | `ShowWindow` 뒤에 `SetForegroundWindow`, 선택적 임포트 |
| DPI 비인식 | 150%/200% 디스플레이에서 Windows는 512x768 클라이언트를 작게 렌더링한 뒤 비트맵을 늘려서, `win_scale`이 정수이고 블릿이 `COLORONCOLOR`인 이유를 무너뜨린다 | `SetProcessDpiAwarenessContext(PER_MONITOR_AWARE_V2)`, 실패하면 `SetProcessDPIAware`로 폴백; 둘 다 선택적 임포트로, 이 링크에 매니페스트가 없어서 코드로 선언 |
| 제목 표시줄이 게임 이름을 떨어뜨림 | "Animal Crossing: Wild World (port)"로 열리고 반 초 뒤 첫 상태 갱신이 "ACWW (port)"로 바꿔 놓았다 | 상태 캡션이 전체 이름을 담는다 |
| 라이브 세션이 사운드 영수증을 남기지 않음 | `acww_snd_report()` -- tag-7 센서스, 드라이버 카운터, `ACWW_SND_WAV` 플러시 -- 는 `ACWW_STOP_FRAME` 경로에서만 돌았고, 라이브 실행은 정의상 Escape로 끝나므로 `ACWW_SND_WAV`는 파일을 쓰지 않았고 이유도 말하지 않았다 | `frame.c`가 창 닫힘 경로에서도 호출한다; 모든 레시피에는 무해한데, 전부 프레임에서 멈추기 때문 [H: log/source account: `sessionC.wav`, 4.4 MB, written by an Escape; receipt provenance unresolved] |

남긴 것:

- **이름 필드가 `ㅃ`(U+3143)이 반복된 채로 미리 채워져 나온다** -- 플레이어 이름은 열두
  칸, 마을 이름은 여덟 칸 -- 그리고 입력한 것은 그 뒤에 덧붙는다. 그림 아티팩트가 아니다:
  이 세션에서 입력한 마을 이름은 세이브 파일에서 원시 바이트 `43 31 43 31 43 31 60 be 34 bb`,
  즉 `ㅃ ㅃ ㅃ 빠 무`로 돌아왔고, 이름을 출력하는 모든 대화 줄이 ㅃ들을 출력한다
  [H: log/source account: `shots/10-nameline.png`, `shots/17-townhall.png`, `savetool.py check` on the played save; receipt provenance unresolved].
  우회책은 입력 전에 필드 폭만큼 백스페이스를 누르는 것이다. **원본이 이렇게 하는지는
  확립되지 않았다** -- 여기에는 오라클 조건이 없으므로, 이는 열린 질문이지 아직 결함
  주장이 아니다. 새 플레이어가 마주치는 가장 눈에 띄는 것이다.
  **NAME42가 답함** (`docs/log/cycle40-keyboard-gate-probe.md`, 영수증 `scratchpad/name42/`),
  그리고 그 답은 이 항목을 두 번 바로잡는다. 포트의 것이 아니다: 마을 키보드의 이름 행은
  탭 대 탭 오라클 조건 `scratchpad/oracle/tap-24700`에 대해 1,190픽셀 중 0픽셀 차이, 세
  프레임이고, 플레이어 키보드의 행은 24픽셀이 다른데 전부 깜빡이는 캐럿 하나다. **그리고
  프리필이 아니다**: 키보드의 커서는 왼쪽 위 키에서 시작하는데 그것이 바로 `ㅃ`이고, A는
  "선택된 키를 누른다"를 뜻한다 -- 그래서 택시 대화를 넘기던 `Z` 입력이 키보드가 열린
  순간부터 필드에 타이핑된 것이다. 필드는 A 입력 하나당 `ㅃ` 하나씩 늘어나고(측정: 600프레임
  펄스당 글리프 잉크 8열) 용량에서 멈추는데, 그 용량은 여기서 센 열둘이 아니라 **6**자다 --
  `ㅃ`는 `ㅂ` 상자 둘로 그려진다. 진짜 우회책은 키보드가 뜨면 A를 그만 누르는 것이다.
- **키보드를 쓴 뒤 첫 스타일러스 탭이 동작 없이 떨어질 수 있다.** 세이브 메뉴에서
  저장하고 마치기에 대한 첫 탭은 커서를 그 위로 옮기기만 했고 두 번째가 확정했다; 열린
  페이지의 탭들에 대한 첫 두 탭은 눈에 보이는 일이 없었고 다음 넷은 모두 12.2-13.3프레임에
  응답했다. TOUCH41의 스타일러스 모드 전환이 라이브로 보인 것이다. 마을을 탭하는 후속
  시행에서는 재현되지 않았으므로, 규칙이 아니라 메뉴 대상에서 관측된 것으로 보고한다
  [H: log/source account: `shots/54-saving.png` against `55-saved.png`; `lat-taps.txt` against `lat-firsttap.txt`; receipt provenance unresolved].
- **창 아이콘 없음** (`wc.hIcon = 0`): 이 링크에는 리소스가 없고 만들 SDK도 없다.
- **Escape는 확인 없이 종료한다.** 스토어는 플러시하므로 게임이 쓴 것은 아무것도 잃지
  않는다 -- 그러나 마지막 게임 내 저장 이후의 모든 것은 잃는다. 확인에는 `-nostdlib`
  링크 안의 대화 상자가 필요하다.
- **창은 `CW_USEDEFAULT`에 열리고** 작은 디스플레이에서는 일부가 화면 밖에 걸릴 수 있다.

## 관련 문서

- `../systems/input-and-touch.md` -- 패드 레지스터, 터치 링, 포트의 주입
- `touch-latency.md` -- 연속 세 샘플 규칙이 측정된 곳
- `savestate-resume.md` -- `--state`가 무엇을 재개하는지, 그리고 스냅샷이 재링크에서 죽는 이유
- `../engine/graphics-pipeline.md` -- 렌더러가 무엇을 소모하는지, PERF42가 무엇을 했는지
- `run-stability.md` -- 세션이 얼마나 오래 살아남는지, 종료 코드가 무엇을 뜻하는지
- `docs/kb/hybrid/live-play.md` -- 이 페이지의 운영용 버전
