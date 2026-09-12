# 입력과 터치
<!-- source: wiki/systems/input-and-touch.md -->

**요약.** DS는 게임에 두 개의 입력 장치를 제공하며 ARM9는 그 어느 쪽도 혼자서 완전히 읽을
수 없다. 열 개의 버튼 중 여덟 개는 ARM9가 직접 읽을 수 있는 레지스터에 있다; X, Y와 디버그
비트는 공유 하프워드를 통해 ARM7에서 온다; 그리고 스타일러스는 ARM7이 채우는 링 버퍼에 원시
아날로그-디지털 변환 카운트로 도착하며, ARM9는 이를 본체 소유자가 몇 년 전에 기록한 보정으로
화면 픽셀로 변환한다. 동물의 숲은 이 모든 것을 프레임당 한 번 읽어 하나의 터치 지점을
`0x021fbde8`에 다시 게시하고, 하류의 모든 것이 그것을 소비한다. PC 포트의 네이티브 경로는
보정의 *출력*에 마우스를 주입하며, 이것이 포트의 탭과 원본의 탭이 1픽셀과 약 2프레임만큼
달랐던 이유다 -- 오랫동안 이 프로젝트에서 단연 가장 잘 측정된 불일치였다. 인터프리터
경로에서는 그 간극이 닫혔다: ROM 자신의 프레임별 게시가 실행되고 포트는 대신 ARM7의 링을
채우며, 1프레임의 지연까지 그대로다.

## 무슨 일이 일어나는가

### 패드

`func_020e9548`은 게임의 키 경로 전부이며, 두 워드를 읽는다:

    held = ((*0x04000130 | *0x027fffa8) ^ 0x2fff) & 0x2fff

따라서 두 레지스터 모두 액티브 로우이며 버튼 공간은 마스크 `0x2fff`다
[S: `func_020e9548`, autoload_2, `src/matched/func_020e9548.c`]. `0x04000130`은
`REG_KEYINPUT`으로 비트 0..9 -- A, B, SELECT, START, Right, Left, Up, Down, R, L -- 를 담는다
[S: `func_ov001_0222db68`, ov001, `src/matched/func_ov001_0222db68.c`]. `0x027fffa8`은 ARM7이
공유 하위 WRAM에 유지하는 하프워드로 X, Y와 디버그 비트를 담는다
[S: `func_ov001_0222db68`, ov001, `src/matched/func_ov001_0222db68.c`]. 따라서 떼어진 상태는
레지스터에서 `0x03ff`, 공유 하프워드에서 `0x2c00`이며, 이 둘을 OR하면 정확히 `0x2fff`다
[H: log/source account: `port/platform/hostinput.c`; the ARM7 halfword reads `2c00` on every frame of the oracle's
probe run, O: `port/tools/oracle/README.md`, the `TP_POINT` probe table; receipt provenance unresolved].

**`0x027fffa8`의 비트 15는 "아무것도 보고하지 말라"를 뜻하며**, 입력 경로에서만이 아니라
게임 전체에서 검사된다: main의 `func_0200f748`과 `func_020089b0`은 이 비트로 상태 전이를
게이트하고, `func_ov001_0221ff3c`와 `func_ov001_02218fa0`은 이를 불리언으로 반환하며, ov055의
두 함수는 이 비트로 RTC 작업을 게이트한다 -- 그러므로 이것은 입력 플래그라기보다 일반적인
"하드웨어 접근 차단" 플래그로 읽힌다 [S: `src/matched/func_0200f748.c`,
`src/matched/func_020089b0.c`, `src/matched/func_ov055_022607a0.c`].

키 반복은 SDK가 아니라 게임의 것이다. `func_ov001_0222db68`은 `cur`, `trg`(새로 눌림),
`up`(새로 떼어짐), `trgRepeat`를 가진 `PadStatus`를 유지하고 열네 항목의 타이머 배열을
순회한다: 누르고 있는 버튼은 40프레임 동안 눌린 뒤 다시 트리거되고 그 이후로는 7프레임마다
트리거된다 [S: `func_ov001_0222db68`, ov001, `src/matched/func_ov001_0222db68.c`]. main의 별도
콤보 검출기는 `0x04000130`을 `0x3ff`로 마스킹해 읽고 일곱 상태의 시퀀스 머신을 돌린다
[S: `func_02001324`, main, `src/matched/func_02001324.c`].

### 스타일러스

터치 패널은 요청 시가 아니라 ARM7에 의해 지속적으로 샘플링된다. `func_020e948c`는 전체
기동을 순서대로 수행한다 -- `TP_Init`, `TP_GetUserInfo`, `TP_SetCalibrateParam`,
`TP_RequestSetStabilityAsync(3, 30)`, 대기, `TP_RequestAutoSamplingStartAsync(0, 4, &gAutoData,
9)`, 대기 -- 그러므로 ACWW는 샘플링 주기 4로 **아홉 항목** 링을 돌린다
[S: `func_020e948c`, autoload_2, `src/matched/func_020e948c.c`]. 링 자체는 호출자의 메모리다;
SDK는 포인터와 크기만 저장한다
[S: `TP_RequestAutoSamplingStartAsync`, autoload_2,
`src/matched/TP_RequestAutoSamplingStartAsync.c`].

각 항목은 네 개의 하프워드로 된 `TPData`다: x, y, touch, validity. `touch`는 펜 업/펜 다운에
대해 0 또는 1이다; **`validity`는 오류 코드이며 0은 샘플이 정상임을 뜻하므로**, 소비자는
validity가 0인 항목이 아니라 0이 아닌 항목을 건너뛴다
[S: `TP_GetCalibratedPoint`, autoload_2, `src/matched/TP_GetCalibratedPoint.c`;
`func_ov001_0222d9b0`, ov001, `src/matched/func_ov001_0222d9b0.c`]. 전달은 PXI 태그 6으로
이루어진다: `TPi_TpCallback`은 `tpState.index`를 버퍼 크기로 나눈 나머지로 증가시킨 뒤 공유
시스템 작업 영역에서 패킹된 비트필드(x:12, y:12, touch:1, validity:2)를 푼다
[S: `TPi_TpCallback`, autoload_2, `src/matched/TPi_TpCallback.c`].

펜이 떨어져 있을 때 ARM7은 x=0, y=0, touch=0, validity=3(INVALID_XY)을 쓴다; 펜 다운 샘플은
압력 검사가 거부하지 않는 한 validity 0과 함께 원시 카운트를 담는다
[H: source account: NitroSDK `libraries/spi/src/ARM7/tp/tp_sampling.c` (public source, `TP_ExecSampling`); direct ROM-source provenance unresolved].
게임의 프레임별 샘플 `func_020e9314`는 최신 항목 이전의 네 항목을 읽고, 연속된 세 항목이
터치되고 유효할 때에만 -- 그 가운데 것을 -- 게시하며, 아무것도 터치되지 않았으면
x=y=0xff를 쓴다; 그 외에는 이전 지점을 그대로 둔다
[S: `func_020e9314`, autoload_2, disassembly at 0x020e9314..0x020e9470]. 원본의 1~2프레임
스타일러스 지연은 여기서 온다: 프레임당 네 샘플이면, 프레임 중간에 시작된 접촉은 다음
프레임에 게시된다 [E: `scratchpad/cycle40/runs/tap-T41pd`,
contact scheduled at 8,700, TP_POINT set at 8,701]. 포트는 인터프리터 경로에서 ARM7을 이런
방식으로 모델링한다(`port/shim/os/pxisend.c`, TOUCH41) [H: source account: `docs/log/cycle40-keyboard-gate-probe.md` TOUCH41; direct ROM-source provenance unresolved].

보정은 12비트 ADC 카운트를 픽셀로 바꾼다. 본체 소유자는 펌웨어 설정 중 두 개의 십자 표시를
터치했다; `TP_GetUserInfo`는 그 두 개의 원시/표시 지점 쌍을 NVRAM에서 읽고,
`TP_CalcCalibrateParam`은 선형 보간으로 축마다 원점과 픽셀당 카운트 기울기를 도출하며, 각각을
`s16` 범위로 검사한다
[S: `TP_GetUserInfo`, autoload_2, `src/matched/TP_GetUserInfo.c`; `TP_CalcCalibrateParam`,
autoload_2, `src/matched/TP_CalcCalibrateParam.c`]. 이어서 `TP_SetCalibrateParam`은
`0x04000280`의 하드웨어 나눗셈기를 사용해 축마다 역수 `0x10000000 / dotSize`를 미리 계산한다
[S: `TP_SetCalibrateParam`, autoload_2, `src/matched/TP_SetCalibrateParam.c`]. 말로 풀면, 변환은
원시 카운트를 왼쪽으로 2 시프트하고, 원점을 빼고, 그 역수를 곱하고, 오른쪽으로 22 시프트한
뒤, x를 0..255로, y를 0..191로 클램프한다
[S: `TP_GetCalibratedPoint`, autoload_2, `src/matched/TP_GetCalibratedPoint.c`].

### 프레임별 게시

`func_020e9314`는 두 세계가 만나는 곳이다. `TP_GetLatestIndexInAuto`를 통해 링의 마지막 네
항목을 읽고, invalid 하프워드가 0인 것들을 복사한 뒤, 세 분기 중 하나를 탄다: 가장 최신으로
끝나는 세 개의 정상 샘플이 있으면 최신 샘플을 보정해 `0x021fbde8`에 쓴다; 하나 더 오래된
것으로 끝나는 세 개의 정상 샘플이 있으면 그것을 보정한다; 유효한 것이 없으면 터치 없음
상태, 즉 **x = y = 0x00ff**에 두 플래그 모두 0을 쓴다 -- `0x020e941c`의 `mov r1,#0xff`와
`strh`이며, 포트의 첫 전사가 가정했던 0xffff가 아니다; ROM의 값은 이제 전사되어
`port/tools/test_scheduled_touch.py`에 고정되어 있다
[S: `func_020e9314`, autoload_2, disassembly `0x020e9314`..`0x020e9470`;
`docs/log/cycle40-keyboard-gate-probe.md` TOUCH41]. 어느 분기가 실행되었든
꼬리는 같다: 눌림 플래그를 이전 프레임의 것과 XOR하여 `0x021fbddc`에 트리거 바이트를 만들고,
`0x021fbdd8`의 이전 플래그를 갱신하며, x와 y를 `0x021fbde0`과 `0x021fbde4`에 다시 게시한다
[S: `config/adm-kr/arm9/autoload_2/symbols.txt`, `func_020e9314` at `0x020e9314`; historical account: transcribed in `port/shim/input/touch.c`].

소비자는 유일한 호출자인 `func_020b9280`이며, 두 좌표를 모두 `u8`로 절단한다 -- 이것이
게시되는 x가 0..255이고 y가 0..191인 이유다. **이 함수는 `0x027fffa8`의 비트 15가 0일 때에만
`func_020e9314`를 호출한다** [S: `func_020b9280`, main, `src/matched/func_020b9280.c`, as
recorded in `port/shim/input/touch.c`].

### 포트는 대신 무엇을 하는가

**두 경로가 있고, 여기서 갈린다.** 인터프리터 경로에서는 -- TOUCH41 이후의 기록용 경로 --
`port/shim/input/touch.c`가 호스트 본체 레지스트리에서 DENIED 처리되어(89개 항목 -> 88개),
ROM 자신의 `func_020e9314`가 실행되고 포트는 대신 ARM7 역할을 한다: `pxisend.c`는 AUTO_ON
요청을 기록해 두고 VBlank마다 `frequence`개의 샘플을 `0x02206134`에 있는 ROM 자신의
`tpState`에 쓰며, `TPi_TpCallback`의 AUTO_SAMPLING 단계를 호스트에서 수행하고, 이때
`port/shim/boot/usersettings.c`가 게시하는 항등 보정(raw = pixel x 16)을 따른다. 샘플은 ROM의
VBlank 핸들러 **뒤에** 도착하며, 이것이 하드웨어의 순서다
[H: source account: `docs/log/cycle40-keyboard-gate-probe.md` TOUCH41, TOUCH42;
see `../experiments/touch-latency.md`; direct ROM-source provenance unresolved]. 이 섹션의 나머지는 NATIVE 경로를 설명하며, 이는
`ACWW_INTERP=1` 없이 실행할 때 여전히 돌아가는 경로다.

패널도 ARM7도 없으므로, 포트는 `func_020e9314`를 터치 없음 분기와 주입 지점으로 대체하고,
보정의 입력이 아니라 **출력**에 주입한다. 링을 합성 ADC 카운트로 채워서 꾸며낸 보정이
그것을 우리가 시작한 픽셀로 도로 변환하게 하는 것은 아무 이득 없이 두 SDK 함수를 왕복하는
일이다 [H: host-source account from `port/shim/input/touch.c`; verify with a retained scripted run and frame using this page's recipe]. 창 아래 절반에 대한 호스트 마우스 클릭은 그 픽셀에서
`touch = 1, validity = 0`이 된다; 위 절반은 터치가 아닌데, 디지타이저가 아래 화면 아래에만
있기 때문이다 [H: host-source account from `port/shim/input/touch.c`, `port/render/window.c`; verify with a retained scripted run and frame using this page's recipe].

패드는 에지에서가 아니라 매 프레임 기록되며, 메인 루프 본문이 아니라 `port/platform/frame.c`의
프레임 경계에서 기록된다 -- 본문은 약 3프레임에 한 번 실행되는 것으로 측정되었고, 이는 20 Hz
키보드가 될 것이다 [H: host-source account from `port/platform/hostinput.c`; verify with a retained scripted run and frame using this page's recipe].
매핑은 D-패드에 화살표, Z=A, X=B, A=Y, S=X, Enter 또는 Space=START, Backspace 또는
오른쪽 Shift=SELECT, Q=L, W=R, 아래 화면 왼쪽 클릭이 스타일러스, Escape가 종료다
[H: host-source account from `port/platform/hostinput.c`; verify with a retained scripted run and frame using this page's recipe]. `ACWW_KEYS`가 `0x2fff` 공간에서 0이 아닌 마스크를 지정하거나
`ACWW_KEYS3_ENABLE`이 설정되면, 스크립트 경로가 레지스터를 소유하고 실시간 키보드는
완전히 무시된다; 실행은 어느 쪽인지를 한 줄의 안내 라인으로 알린다
[H: host-source account from `port/platform/hostinput.c`; verify with a retained scripted run and frame using this page's recipe].

예약된 접촉은 모든 터치 측정이 사용하는 계측 수단이다:
`ACWW_TOUCH_ENABLE`, `_X`, `_Y`, `_AT`, `_FOR`, 그리고 `_EVERY`(반복 주기, `_FOR`보다 커야 함)와
`_REPEAT`(접촉 횟수; 없으면 무한), 그리고 같은 여섯 필드를 가진 독립적인 두 번째 접촉
`ACWW_TOUCH2_*`. **두 번째 접촉이 먼저 검사되며 자신의 창에서 이긴다** [H: log/source account: `port/shim/input/touch.c`;
`docs/kb/hybrid/hardware-services.md` section 6; receipt provenance unresolved]. 설정은 `GetEnvironmentVariableA`를 직접 통해
한 번 파싱되는데, 포트 자신의 `acww_env_dec`는 미설정, 파싱 불가, 0을 하나의 답으로 접어
버리기 때문이다; 완전히 유효한 설정에 못 미치는 것은 무엇이든 한 줄의 거부 메시지를
출력하고 그 실행 동안 비활성으로 남는다 [H: host-source account from `port/shim/input/touch.c`; verify with a retained scripted run and frame using this page's recipe].

`ACWW_PADSCRIPT=<file>`은 네 번째 스크립트 입력이며, 펄스 생성기가 아니라 TIMELINE인 유일한
입력이다: 한 줄에 한 행, 패드는 `<frame> <mask> <frames>`, 스타일러스는
`<frame> T <x> <y> <frames>`, 숫자는 `0x` 접두사가 없으면 십진수이며, 겹치는 패드 행은 OR로
합쳐지고 스타일러스 행은 처음 일치하는 것이 이긴다
[H: source/log account from `port/platform/hostinput.c`; verify with a retained run using this page's recipe]. 스크립트가 살아 있는 동안에는 프레임 경계에서 두 패드
레지스터를 모두 소유하고 `port/shim/gfx/frameswap.c`는 어느 쪽도 쓰지 않는데,
`frameswap.c`의 phase2와 phase3가 세이브스테이트에서 옛 스케줄이 여전히 무장된 채로 블롭으로
되돌아오기 때문이다
[H: log/source account: `port/platform/hostinput.c`; `port/shim/gfx/frameswap.c`;
S: `docs/kb/hybrid/savestate.md` section 4; receipt provenance unresolved]. 그 스타일러스 행은 `ACWW_TOUCH*` 스케줄보다
먼저, 그리고 마우스보다 먼저 질의된다 [H: source/log account from `port/shim/input/touch.c`; verify with a retained run using this page's recipe]. 설정하지 않으면 아무것도
바꾸지 않는다: 이것을 실은 빌드에서의 OFF 레시피는 손대지 않은 HEAD의 재링크와 31/31
바이트 단위로 동일하다 [H: `scratchpad/cycle40/runs/off-ps` vs `off-base`;
`docs/log/cycle41-gameplay.md`; receipt lost with its worktree; repeat the named recipe and retain the stated frames]. 이것이 스크립트 플레이어가 마을 회관을 걸어 나와
마을을 돌아다닐 수 있게 한 것이다 [H: log/source account: `wiki/experiments/gameplay-walkthrough.md`; receipt provenance unresolved].

## 포트와 원본은 측정 가능하게 불일치한다

오라클의 프로브 모드는 원본에서 ROM 자신의 `TP_POINT`를 `0x021fbde8`에서 읽는다. 접촉을
221,181에서 10프레임 동안 60프레임마다 두 번, 프레임 1000부터 예약하면:

| 무비 프레임 | 무비 스타일러스 | `0x021fbde8` x, y, touch, validity | `0x027fffa8` |
|---|---|---|---|
| 1000..1009 | 다운 221,181 | 222, 182, 1, 0 | `2c00` |
| 1010 | 업 | 222, 182, 1, 0 (1프레임 지연) | `2c00` |
| 1060..1061 | 다운 221,181 | 255, 255, 0, 0 (아직 샘플링되지 않음) | `2c00` |
| 1062.. | 다운 221,181 | 222, 182, 1, 0 | `2c00` |

[O: `port/tools/oracle/README.md`, "...and the tap reaches the GAME", 1,200-frame probe run].

세 가지가 따라온다. 접촉은 게임에 도달한다. **좌표는 1픽셀 크게 돌아온다** -- 221,181이
들어가 222,182가 나온다 -- 에뮬레이터가 화면 픽셀을 원시 ADC 카운트로 변환하고
`TP_GetCalibratedPoint`가 이를 되돌리는 왕복 때문이며, 포트는 이 왕복을 의도적으로 건너뛴다
[O: `port/tools/oracle/README.md`, "...and the tap reaches the GAME"]. 그리고 **게임은 접촉을 1~2프레임 늦게 보고 1프레임 더 길게 유지한다**. ARM9가
읽기 한 프레임 전에 링이 채워지는 반면 포트는 정확한 프레임에 게시하기 때문이다 [O: `port/tools/oracle/README.md`, "...and the tap reaches the GAME"].
그 2프레임 차이는 두 생산자 사이에서 실재하고, 측정되었으며, 피할 수 없는 것이고, 한쪽에서만
동작하는 모든 탭에 대한 상시 후보 설명이다 [O: `port/tools/oracle/README.md`, "...and the tap reaches the GAME"].

계측 수단 자체에 대한 한 가지 주의로, 이후 정정되었다: 그 Lua 빌드의 `memory.readword`는
터치 없음 행에서 255를 반환했는데, 이는 0xffff를 쓰던 포트 전사에 비추어 하위 8비트 절단처럼
보였다. ROM 자신의 터치 없음 값은 **0x00ff**이므로 프로브의 255는 옳다
[S: `func_020e9314`, disassembly `0x020e9314`..`0x020e9470`;
`docs/log/cycle40-keyboard-gate-probe.md` TOUCH41]. 그 Lua 빌드의 `readword`가 일반적으로
16비트 폭인지는 아직 검증되지 않았으며, 어느 쪽이든 표의 모든 값은 256 미만이다
[O: `port/tools/oracle/README.md`, "...and the tap reaches the GAME"; M1].

이것이 설명할 수 있을 불일치는 두 번째 키보드다. 마을 레시피에서 포트와 원본은 프레임
6000부터 24000까지 한 걸음 한 걸음 같은 화면에 있다 -- 샘플링된 아홉 프레임에서 전체 프레임
ncc 0.9920에서 0.9959 -- 그리고 `TOUCH2` 창 안의 25,500에서 갈라진다: 포트의 두 탭은 마을
이름을 확정하고 원본의 동일한 탭은 그렇지 않아, 원본은 48,000까지 마을 이름 키보드에
남는다(ncc는 약 0.70으로, 위 화면 ncc는 0.0000으로 떨어진다)
[O: `scratchpad/oracle/tap-fullpad/compare-vs-tap-D56.txt`, frames 6000..48000]
[E: `scratchpad/cycle40/runs/tap-D56`]. **이것은 확정되었고(ORACLE42) 답은 이 페이지 끝의 결과
섹션에 있다: 어느 쪽도 틀리지 않았고, 탭 프레임이 틀렸다.**

## 어디에 있는가

| 함수 또는 심볼 | 모듈 | 역할 | 등급/출처 |
|---|---|---|---|
| `func_020e9548` | autoload_2 | 게임의 키 읽기: `((KEYINPUT | ext) ^ 0x2fff) & 0x2fff`, 이전 값, 변화 | [S: `src/matched/func_020e9548.c`] |
| `func_ov001_0222db68` | ov001 | `cur`/`trg`/`up`/`trgRepeat`를 가진 `PadStatus`와 40 후 7프레임 반복 | [S: `src/matched/func_ov001_0222db68.c`] |
| `func_02001324` | main | `0x04000130`을 `0x3ff`로 마스킹한 일곱 상태 콤보 검출기 | [S: `src/matched/func_02001324.c`] |
| `TP_Init` | autoload_2 | PXI 기동, 터치 태그에 `TPi_TpCallback` 등록 | [S: `src/matched/TP_Init.c`] |
| `TP_RequestAutoSamplingStartAsync` | autoload_2 | 호출자의 링을 설치하고, 모든 슬롯의 터치 플래그를 지우고, ARM7에 시작을 요청 | [S: `src/matched/TP_RequestAutoSamplingStartAsync.c`] |
| `TP_RequestSetStabilityAsync` | autoload_2 | ADC 재시도/범위 노이즈 제거; ACWW는 (3, 30)을 넘김 | [S: `src/matched/TP_RequestSetStabilityAsync.c`] |
| `TP_GetLatestIndexInAuto` `0x0211d00c` | autoload_2 | 최신 링 인덱스를 반환 | [S: `src/matched/TP_GetLatestIndexInAuto.c`] |
| `TP_GetCalibratedPoint` `0x0211cc6c` | autoload_2 | 원시 ADC를 화면 픽셀로, 0..255 / 0..191 클램프 포함 | [S: `src/matched/TP_GetCalibratedPoint.c`] |
| `TP_SetCalibrateParam`, `TP_CalcCalibrateParam`, `TP_GetUserInfo` | autoload_2 | 펌웨어 NVRAM에서 보정을 설치, 도출, 로드 | [S: `src/matched/TP_SetCalibrateParam.c`] |
| `TP_CheckError`, `TP_WaitBusy` | autoload_2 | `err_flg`를 폴링, `command_flg`를 스핀 | [S: `src/matched/TP_WaitBusy.c`] |
| `TPi_TpCallback` | autoload_2 | PXI 태그 6 수신 핸들러; x:12 y:12 touch:1 validity:2를 풂 | [S: `src/matched/TPi_TpCallback.c`] |
| `func_020e948c` | autoload_2 | 게임의 터치 기동; 주기 4로 9샘플 링을 시작 | [S: `src/matched/func_020e948c.c`] |
| `func_020e9314` | autoload_2 | 프레임별 게시와 그 세 분기 | [H: source account: literal pool, transcribed in `port/shim/input/touch.c`; direct ROM-source provenance unresolved] |
| `func_020b9280` | main | 유일한 소비자; u8로 절단; `0x027fffa8`의 비트 15로 게이트 | [S: `src/matched/func_020b9280.c`] |
| `func_ov001_0222d9b0` | ov001 | DWC 자체의 "readTouch": 링을 역방향으로 순회, 무효 건너뜀, 에지 도출 | [S: `src/matched/func_ov001_0222d9b0.c`] |
| `func_ov126_022a04e8` | ov126 | 키보드 히트 테스트; 맨 `sub_229c54c` / `sub_229c448`을 호출하며 그 상주 본체는 `func_ov095_0229c54c` / `0229c448` | [S: `src/matched/func_ov126_022a04e8.c`; `docs/kb/port/input-save-audio.md`, KBD39] |

## 읽고 쓰는 데이터

| 주소 또는 필드 | 의미 | 쓰는 쪽 | 읽는 쪽 |
|---|---|---|---|
| `0x04000130` | `REG_KEYINPUT`, 비트 0..9, 액티브 로우 | 하드웨어 (포트: `acww_input_publish`) | `func_020e9548`, `func_02001324`, `func_ov001_0222db68` [S: `src/matched/func_020e9548.c`] |
| `0x027fffa8` | ARM7 공유 하프워드: X 비트 10, Y 비트 11, 디버그 비트 13, 액티브 로우; 비트 15 = 아무것도 보고하지 않음 | ARM7 (포트는 `0x2c00`을 고정) | 같은 셋, 그리고 main/ov001/ov055의 여섯 게이트 [S: `src/matched/func_ov001_0222db68.c`] |
| `0x021fbde8` | `TP_POINT`: `{u16 x, u16 y, u16 touch, u16 validity}` | `func_020e9314` | `func_020b9280` [S: `src/matched/func_020b9280.c`] [O: probe mode, `port/tools/oracle/README.md`] |
| `0x021fbdd8` | 이전 프레임의 터치 플래그, 1바이트 | `func_020e9314` | 자기 자신, 다음 프레임 [S: `config/adm-kr/arm9/autoload_2/symbols.txt`, `func_020e9314` at `0x020e9314`; historical account: transcribed in `port/shim/input/touch.c`] |
| `0x021fbddc` | 트리거 바이트: 이번 프레임 플래그 XOR 이전 플래그 | `func_020e9314` | UI [S: `config/adm-kr/arm9/autoload_2/symbols.txt`, `func_020e9314` at `0x020e9314`; historical account: `port/shim/input/touch.c`] |
| `0x021fbde0` / `0x021fbde4` | 다시 게시된 x와 y | `func_020e9314` | `func_020b9280` [S: `config/adm-kr/arm9/autoload_2/symbols.txt`, `func_020e9314` at `0x020e9314`; historical account: `port/shim/input/touch.c`] |
| `0x021fbdf0` | 아홉 항목의 자동 샘플링 링 `gAutoData` | `TPi_TpCallback`을 통한 ARM7 (포트에서는 아무것도 없음) | `func_020e9314` [S: `src/matched/func_020e948c.c`] |
| `0x021f6c54` | 키보드의 `< 0x48` 비교가 검사하는 터치 Y -- 카운터가 아니라 좌표 | 키보드 | `func_ov126_022a1228` [H: source account: `docs/kb/port/input-save-audio.md`, KBD39; direct ROM-source provenance unresolved] |
| `0x04000280` | 보정 역수를 미리 계산하는 데 쓰이는 하드웨어 나눗셈기 | `TP_SetCalibrateParam` | 자기 자신 [S: `src/matched/TP_SetCalibrateParam.c`] |

## 확인 방법

`../experiments/touch-latency.md`는 타이밍 측정이다 -- 샘플링 링, 세 샘플 규칙, 1프레임의
지연, VBlank 핸들러에 대한 순서 -- 세 가지 조건과 각각의 레시피를 포함한다.
`../experiments/touch-calibration.md`는 위의 좌표 측정이며, 그 레시피와 음성 대조군을
포함한다. `../experiments/two-tap-town-recipe.md`는 모든 하류 터치 관측이 이루어지는
실행이다. `../experiments/off-recipe.md`는 둘 모두가 비교 대상으로 삼는 대조 실행이다.

## 확정됨 (기록용으로 보존)

이것들은 TOUCH41과 TOUCH42가 닫기 전까지 이 페이지의 가설 섹션이었다. 부정 결과도 긍정
결과만큼 비용이 들었기에 보존한다.

- **확정된 부정.** 1픽셀 오프셋은 원본이 두 번째 키보드의 확인 버튼을 거부하게 만들지
  않는다. 접촉을 222,182 -- 원본의 게임이 실제로 보는 좌표 -- 로 옮겨 포트를 다시
  실행했더니 탭은 여전히 `acww touch: DOWN x=222 y=182`로 도착했고, 접촉 네 번,
  27,000프레임에서 exit 100이었다
  [E: `scratchpad/cycle40/runs/tap-D61`, `ACWW_TOUCH_X=222 ACWW_TOUCH_Y=182`];
  `scratchpad/oracle/tap-220`에 대해 양쪽은 여전히 갈라진다
  [H: source account: `docs/log/cycle40-keyboard-gate-probe.md` ORACLE42; direct ROM-source provenance unresolved].
- **확정된 긍정.** 프레임이 원인이며, 지연이 프레임이 중요한 이유다. 탭을 KEYS3 A 누름
  프레임에서 24,700으로 옮기면 양쪽 모두 확정하고 일치한다
  [H: source account: `docs/log/cycle40-keyboard-gate-probe.md` ORACLE42; E: `tap-D62`;
  O: `scratchpad/oracle/tap-24700`; direct ROM-source provenance unresolved].
- **확정된 긍정 (TOUCH41/TOUCH42).** 레시피가 지연을 피하게 하기보다 포트가 지연을
  모델링해야 하며, 실제로 그렇게 한다. ROM 자신의 `func_020e9314`가 이제 인터프리터 경로에서
  실행되고 포트는 ARM7의 링을 ROM의 VBlank 핸들러 *뒤에* 채운다 -- 그리고 24,600 레시피는
  원본과 같이 동작한다 [E: `scratchpad/cycle40/runs/tap-T42b`]
  [O: `scratchpad/oracle/tap-window`]. `../experiments/touch-latency.md`와 아래 결과 섹션을
  보라.
- **확정됨.** 첫 번째 탭이 결코 확정하지 않는 이유는 히트 테스트가 아니라 모드 전환이다:
  키보드는 첫 번째 접촉을 PAD에서 스타일러스로의 모드 변경으로 소비하고, 스타일러스 모드 창
  안의 두 번째 접촉만이 확인 버튼에 도달한다
  [E: `docs/log/cycle40-keyboard-gate-probe.md` H4 RESULT and TAP40;
  `scratchpad/cycle40/runs/tap-native`, `tap-interp`].
- 키보드를 가진 사람은 스크립트 레시피가 할 수 없는 곳에서 마을 회관을 걸어 나갈 수 있다
  [E: `scratchpad/cycle40/runs/tap-D59`, 90,000 frames of talking to Pelly again].

## 가설

- **인터프리트된 콜백 이상 현상.** [H] ARM7의 프레임당 네 샘플을 인터프리트된 PXI 호출로
  ROM 자신의 `TPi_TpCallback`에 전달하는 것은 호스트 채움과 데이터가 동일한데도 게임을
  바꾼다: 택시 대화가 스크립트 입력 없이 진행되고 두 이름 키보드 모두 왼쪽 위 키를 여덟 번
  입력하고 확정한다
  [E: `scratchpad/cycle40/runs/tap-T41j`, `tap-T41q8705` against `tap-T41pd`;
  S: `docs/log/cycle40-keyboard-gate-probe.md` TOUCH41; `docs/kb/hybrid/stall-playbook.md`
  case 42]. 호스트 채움이 출하되고 `ACWW_TP_PXI=1`은 추적을 위해 인터프리트 경로를 남겨 둔다.
  접촉을 DISABLED로 두고 `ACWW_TP_PXI=1`로 실행하여 확정한다. 그러면 프레임당 네 번의
  인터프리트된 콜백은 펜 업 샘플만 나르므로, 게임이 여전히 앞서 달린다면 부작용은 터치
  데이터가 아니라 `acww_interp_irq_run`에 있다 --
  `../experiments/touch-latency.md`, 미결 항목.
- **인터프리터 경로에서의 유지 시간.** [H] 같은 프레임과 좌표에서 `FOR=10`과 `FOR=90`은
  *네이티브* 경로에서 샘플링된 아홉 프레임 모두에서 바이트 단위로 동일한 이미지를 만들었다
  [H: log/source account: `docs/kb/port/input-save-audio.md`, TOUCH39; receipt provenance unresolved]. ROM 자신의 게시가 넘겨받은 이후로는 다시
  측정되지 않았다. 그 쌍을 `ACWW_INTERP=1`로 반복하여 확정한다.
- **오라클 프로브의 `memory.readword`는 16비트 폭인가?** [H] 의심할 이유는 사라졌다 --
  터치 없음 행에서 반환한 255는 ROM 자신의 0x00ff이지 0xffff의 절단이 아니다
  [H: source account: `docs/log/cycle40-keyboard-gate-probe.md` TOUCH41; direct ROM-source provenance unresolved] -- 하지만 이 접근자가 255를 넘는
  값을 반환하는 것을 긍정적으로 보여 준 것은 아직 없다. 모든 필드가 256 미만인 이 페이지에서는
  어느 것에도 영향이 없다. ROM이 16비트 폭으로 쓰는 주소를 프로브하여 확정한다.


## 결과 (ORACLE42, 이 페이지의 초안 작성 이후)

1픽셀 테스트는 부정이다: 접촉을 222,182에 둔 포트는 여전히 마을 이름을 확정하고(`tap-D61`,
25,200부터 위 화면이 검음 = 탑승), 접촉을 220,180에 둔 원본은 여전히 확정하지 않는다
(`scratchpad/oracle/tap-220`, 27,000까지 키보드) [E: `tap-D61`; `scratchpad/cycle40/runs/tap-D61`]
[O: `scratchpad/oracle/tap-220`]. 프레임이 원인이다: 24,600은 KEYS3 A 누름 프레임(2400 + 37 x 600)
이지만 8,700은 아니며, 원본의 스타일러스 샘플은 포트보다 1-2프레임 늦게 게임에 도달하므로,
누름과 탭의 순서가 양쪽에서 다르게 정해진다
[H: source account: docs/log/cycle40-keyboard-gate-probe.md ORACLE42; direct ROM-source provenance unresolved]. `ACWW_TOUCH2_AT=24700`으로 하면 양쪽
모두 확정하고 일치한다: 24000..27000의 11프레임에서 평균 ncc 0.9955, 위 화면 1.0000
[E: `tap-D62`; `scratchpad/cycle40/runs/tap-D62`] [O: `scratchpad/oracle/tap-24700`]. 기록용 레시피는 24,700을 사용한다.
지연은 이제 모델링되었다(TOUCH41): ROM의 `func_020e9314`가 인터프리터 경로에서 실행되고
포트는 ARM7의 링을 채운다 [H: source account: `docs/log/cycle40-keyboard-gate-probe.md` TOUCH41; direct ROM-source provenance unresolved].
이 모델 아래에서 24,600에 예약된 접촉은 24,601에 TP_POINT에 도달하며, 포트는 원본이
확정하지 않는 곳에서 여전히 마을 이름을 확정한다 [E: `scratchpad/cycle40/runs/tap-T41h`]
[O: `scratchpad/oracle/tap-window`]; 24,700 레시피는 24,000..27,000에서 0.9986을 기록한다
[E: `tap-T41i`; `scratchpad/cycle40/runs/tap-T41i`] [O: `scratchpad/oracle/tap-24700`]. **확정됨 (TOUCH42)**: ROM의 VBlank 핸들러에
대한 샘플의 위치가 같은 프레임의 누름과 탭의 순서를 정한다. 네 샘플을 핸들러 뒤에
전달하면(하드웨어의 순서: 핸들러는 VBlank에서 패드를 읽고, ARM7은 그 다음 프레임 동안
패널을 샘플링한다) 포트는 원본처럼 24,600에서 키보드에 남는다 -- 24,000..27,000의
11프레임에서 ncc 0.9981 [E: `scratchpad/cycle40/runs/tap-T42b`]
[O: `scratchpad/oracle/tap-window`] [H: source account: `docs/log/cycle40-keyboard-gate-probe.md` TOUCH42; direct ROM-source provenance unresolved].

## 결과 (INPUT46): 원본에 대해 측정한 스크립트 패드

패드 경로는 스타일러스처럼 원본에 대해 채점된 적이 없었다. 이제는 그림이 아니라 ROM 자신의
워드로 채점되었다: 포트의 영역 장부(`ACWW_ORACLE_ADDRESS=0x021fbdd0 _LENGTH=120`)와
`oracle.py --peek 0x021fbdd0:1,0x021fbe38:4`가 같은 120바이트 -- ROM의 프레임별 카운터,
`g_021fbe3c`와 `g_021fbe40`의 `{held, trigger, table}` -- 를 하나의 레시피 아래 두 생산자
모두에서 택시 대화 내내 읽었다
[E: `scratchpad/input46/RECEIPTS.md`; `docs/log/cycle40-keyboard-gate-probe.md` INPUT46].

- **누르고 있는 키는 양쪽 모두에서 ONE 트리거다.** `ACWW_KEYS=9 _FOR=10 _EVERY=30`으로,
  `0x021fbe42`의 ROM `changed` 워드는 펄스당 정확히 한 번 올라간다: 매 프레임 샘플링한 포트에서
  35펄스 중 34, 같은 대화를 2프레임마다 샘플링한 원본에서 24 중 24(그리고 패드 페이즈를
  비활성화하여 열차가 멈추지 않게 하면 51 중 51)
  [E: `scratchpad/input46/w-port1.txt`] [O: `scratchpad/input46/w-full.txt`].
- **패드는 메인 루프 반복당 한 번 읽히며, 그것은 두 생산자 모두에서 THREE 프레임당 한
  번이다** -- `0x021fbdd0`은 포트에서 30프레임당 정확히 10, 원본에서 100프레임당 33 증가한다.
  게임의 키 경로는 어느 기계에서도 VBlank당 경로가 아니다
  [S: `func_0206e63c`'s `data_021fbdd0++`, `port/shim/gfx/frameswap.c`].
- **포트의 스크립트 누름은 3프레임 늦게 도착하고 10프레임이 아니라 12프레임 유지된다.**
  `frameswap.c`는 두 패드 레지스터를 `func_0206e63c`의 END에서, 즉 메인 루프 BODY당 한 번
  쓰므로, 마스크는 한 프레임에 계산되어 다음 본문에서 소비된다; 원본의 ROM은 실제 하드웨어를
  읽어 펄스 시작 +2..+4에 누름을 보고 8..10프레임 유지한다. 30프레임 주기에서는 어떤 에지도
  바꾸지 않으며 모델링되지 않았다
  [E: `scratchpad/input46/w-port1.txt` frames 780..795] [O: `scratchpad/input46/w-orig.txt` frames 1,080..1,092].
- **따라서 택시 대화는 ORIGINAL의 속도로 진행된다.** 28번의 메시지 박스 다시 그리기는 같은
  순서의 같은 이벤트이며 일정한 +270프레임 차이이고, 포트는 같은 펄스 열로 택시 시작부터
  키보드 시작까지를 830프레임에 걸치며 원본은 810프레임이다 [E: `scratchpad/input46/table.txt`; `docs/log/cycle40-keyboard-gate-probe.md` INPUT46]. **CARD45의 "포트는 택시 대화를
  1.8배 빠르게 진행한다"는 RETRACTED되었다** (`docs/log/cycle40-keyboard-gate-probe.md`, INPUT46, "The answer in one paragraph"): 포트는 택시에서 약 280프레임 이르므로
  `ACWW_KEYS2`가 프레임 1,800에서 30프레임 열차를 멈추기 전에 끝나는 반면, 원본은 이벤트 넷이
  모자라 `ACWW_KEYS3`의 첫 A를 700프레임 기다린다.

**`ACWW_PAD_SAMPLE`은 이 중 어느 것도 목격할 수 없었고, 삭제되었다.** `port/shim/probe_pad.c`는
`func_020e9548`을 오버라이드하며 링크되어 있지만, 인터프리터는 REGISTERED 함수에 대해서만
네이티브 본체로 들어가고 이 함수는 부팅 라인이 이름 대는 85개에 들지 않으므로, 인터프리터
실행에서는 그 심의 어느 부분도 실행되지 않는다 -- 측정 결과, 목격자를 완전히 설정한 실행은
샘플도 심 자신의 상한 있는 레지스터 로그도 출력하지 않았다. 설정으로 등록할 수도 없다.
대신 영역 장부로 RAM에서 세 워드를 읽어라
[H: source account: `docs/kb/hybrid/stall-playbook.md` case 71; `docs/kb/hybrid/instruments.md` section 3d; direct ROM-source provenance unresolved].

## 관련 문서

- `../experiments/touch-latency.md`, `../experiments/touch-calibration.md`,
  `../experiments/two-tap-town-recipe.md`, `../experiments/off-recipe.md`.
- `../engine/interpreter-path.md` -- ROM 자신의 게시를 핫 패스에 되돌려 놓는 거부 목록.
- `time-and-rtc.md` -- 모든 `_AT`가 표현되는 프레임 카운터.
