# 시간과 실시간 시계
<!-- source: wiki/systems/time-and-rtc.md -->

**요약.** 동물의 숲은 날짜에 관한 게임이고, 그 날짜는 DS의 ARM7 프로세서만 읽을 수 있는
배터리 백업 시계 칩에서 온다. 게임은 비동기 요청을 통해 날짜를 요청하고, 칩의 BCD 자릿수를
숫자로 변환하며, 그 답을 두 개의 전역 변수에 저장하고, 세이브가 기록된 날짜와 비교한다 --
놓친 날을 하루하루 모두 재생하면서. 두 번째 시계인 하드웨어 틱 카운터는 이와 무관하며,
날짜가 아니라 프레임 단위로 짧은 간격을 측정한다. PC 포트는 *고정된* 날짜 2005-06-15
10:00:00을 공급하며 이를 진행시키지 않는다.

## 무슨 일이 일어나는가

시계는 두 개이고 서로 관련이 없다. RTC 칩은 "오늘이 며칠인가"에 답하고, 하드웨어 타이머 0은
"얼마나 지났는가"에 답한다. 이 둘을 혼동한 대가로 이 프로젝트는 이미 한 번의 정지(stall)와
한 건의 철회된 스크린샷 발견 사항을 치렀다.

### RTC 칩

ARM9는 칩을 읽을 수 없다. `RTC_Init`은 RTC 작업 구조체를 0으로 채우고, PXI를 기동하고,
ARM7의 RTC 채널이 준비될 때까지 스핀한 뒤 `RtcCommonCallback`을 `PXI_FIFO_TAG_RTC`의 수신
콜백으로 등록한다 [S: `RTC_Init`, autoload_2, `src/matched/RTC_Init.c`]. 이후의 모든 읽기는
요청이다: `RtcSendPxiCommand`는 명령 바이트를 FIFO 워드의 비트 8..14에 패킹해 보내며, FIFO가
가득 차 있으면 재시도한다 [S: `RtcSendPxiCommand`, autoload_2,
`src/matched/RtcSendPxiCommand__autoload_2_0211ea98.c`]. 세 가지 읽기 명령은 날짜와 시각이
0x10, 날짜가 0x11, 시각이 0x12이다
[S: `RTCi_ReadRawDateTimeAsync` / `RTCi_ReadRawDateAsync` / `RTCi_ReadRawTimeAsync`, main,
`src/matched/RTCi_ReadRawDateTimeAsync.c`].

답은 FIFO를 통해 돌아오지 않는다. ARM7은 칩의 원시 레지스터를 `0x027ffde8`의 공유 시스템
작업 영역에 쓰고 완료를 알리는 워드를 게시한다; `RtcCommonCallback`은 거기서 비트필드를
읽어 연, 월, 일, 시, 분, 초 각각을 `RtcBCD2HEX`에 통과시키고, 디코드된 값을 호출자의
`RTCDate` / `RTCTime` 버퍼에 쓴다 [S: `RtcCommonCallback`, autoload_2, `src/matched/RtcCommonCallback.c`].
`RtcBCD2HEX`는 모든 니블이 0xA 미만인지 검증하고 하나라도 아니면 0을 반환하므로, 깨진 읽기는
엉뚱한 값이 아니라 0으로 디코드된다 [S: `RtcBCD2HEX`, autoload_2, `src/matched/RtcBCD2HEX.c`].

**요일은 계산되는 것이 아니라 읽힌다.** `RtcCommonCallback`은 칩의 원시 3비트 주 필드를
그대로 `RTCDate.week`에 복사한다; 이를 계산된 요일로 대체한 NitroSDK 리비전은 2005-09-30
날짜로, 이 ROM보다 나중이다
[S: `RtcCommonCallback`, autoload_2, `src/matched/RtcCommonCallback.c`]. 게임은 이 값을 완전히
신뢰하지는 않는다: `func_0209e5b4`는 방금 채운 버퍼를 검사해 날짜가 0년 1월 1일이면 요일을
6으로 강제한다 -- 2000-01-01은 토요일이었고 `RTC_WEEK_SATURDAY`는 6이다
[S: `func_0209e5b4`, main, quoted in `port/shim/os/rtcclock.c`].

동기 getter들은 래퍼다: 각각은 `RtcGetResultCallback`을 넘겨 비동기 짝을 호출한 다음, 락
워드가 해제될 때까지 `RtcWaitBusy`에서 바쁜 대기(busy-wait)를 하고, `rtcWork.commonResult`를
반환한다 [S: `RTC_GetTime`, autoload_2, `src/matched/RTC_GetTime.c`;
`RtcWaitBusy`, autoload_2, `src/matched/RtcWaitBusy.c`]. 결정적으로 **getter들은 결코
`rtcWork`에서 결과를 채우지 않는다** -- 호출자 자신의 버퍼를 비동기 계층으로 내려보내 ARM7이
거기에 쓰게 한다 [S: `RTC_GetTimeAsync`, autoload_2, `src/matched/RTC_GetTimeAsync.c`]. 이것이
PXI 요청을 버리는 호스트가 0을 반환하는 대신 버퍼를 건드리지 않은 채로 두게 되는 이유다.

두 개의 변환이 날짜를 숫자로 바꾼다: `RTC_ConvertDateToDay`는 필드를 검증하고, 열두 항목의
누적 연중 일수 테이블에 윤일 보정(윤년 검사는 `!(year & 3)`으로, 2000-2099 안에서는 충분하다)과
`year*365 + (year+3)/4`를 더해 일 번호를 누적한다
[S: `RTC_ConvertDateToDay`, autoload_2, `src/matched/RTC_ConvertDateToDay.c`], 그리고
`RTC_ConvertDateTimeToSecond`는 거기에 86,400을 곱하고 `RTCi_ConvertTimeToSecond`를 더하며,
어느 한쪽이라도 유효하지 않으면 -1을 반환한다
[S: `RTC_ConvertDateTimeToSecond`, autoload_2, `src/matched/RTC_ConvertDateTimeToSecond.c`].

**트리 안의 이름이 틀렸고 정정은 확정되었다.** `src/matched/RTC_SetDateTime.c`는
`0x0211e7c0`의 68바이트 래퍼를 정의하며 `RTC_SetDateTimeAsync`를 호출한다고 선언한다. 그
심볼은 어떤 매칭된 파일에도 정의되어 있지 않고 링크된 이미지 어디에도 나타나지 않는다; ROM
자체의 `0x0211e7d0` 분기 워드는 `bl 0x0211e804`이며 이는 `RTC_GetDateTimeAsync`다; 그리고 세
개의 68바이트 래퍼는 NitroSDK가 내보내는 순서대로 각자의 비동기 짝 바로 앞에 놓여 있다
[S: read from `extract/adm-kr/arm9/unk_autoload_2.bin` and the autoload_2 symbol table, as
recorded in `port/shim/os/rtcclock.c`]. `0x0211e7c0`은 `RTC_GetDateTime`이다. 하니스가 호출
변위를 마스킹하기 때문에 바이트 매칭으로는 둘을 구별할 수 없다 -- 이것은 결함 클래스 D12,
잘못 타이핑된 대상을 인코딩한 이름이다 [S: `docs/rules/D-defects.md` D12].

### 게임의 시계

`func_0209e49c`는 `RTCDate`와 `RTCTime`을 지역 변수로 선언하고, 그것들에 대해 `func_0209e5b4`
(즉 `RTC_GetDateTime`)를 호출한 뒤, 결과를 `0x021dc744`(날짜)와 `0x021dc754`(시각)의 게임
시계 전역 변수에 복사한다
[S: `func_0209e49c`, main, quoted in `port/shim/os/rtcclock.c`].

날짜 넘김은 이벤트가 아니라 따라잡기 루프다. `func_0207b05c`는 현재 날짜를 가져와 세이브의
`self+0x4046`에 저장된 날짜와 비교하고, `func_0209dcdc`를 통해 일 단위 차이를 계산한 다음,
하루 단위 스텝 `func_0207b268`을 그 횟수만큼 호출한다 -- 그래서 게임은 가장 최근 날로 건너뛰는
대신 놓친 모든 날을 재생한다. 유효해 보이지 않는 델타는 별도의 분기, 즉 시계 조작 경로를
탄다 [S: `func_0207b05c`, main, `src/matched/func_0207b05c.c`]. 이 함수가 "N일 앞으로 시간
여행했다"의 배후 메커니즘이다; 되돌려진 분기는 시계를 과거로 돌렸을 때의 게임 반응으로
이어지는 것이다 [H: the branch is identified, its destination
`func_0209a654` / `func_0209a77c` is not decompiled; settled by following that call chain].

분(minute)이 조명을 구동한다. `func_020bbb6c`는 `0x021dc758`에서 분 바이트를 읽어 0x44445 >> 12,
즉 4096/60으로 스케일한다 -- 낮/밤 환경광 보간을 위한 고정소수점 블렌드 가중치다
[S: `func_020bbb6c` / `func_0209def4`, main, quoted in `port/shim/os/rtcclock.c`].

게임 자체의 시계 밖에서 RTC는 엔트로피 소스다. Wi-Fi 신원 생성기는 초로 변환한 RTC 날짜와
시각으로 16비트 LCG를 시드하며, 틱 카운터가 사용 가능하면 그것으로 솔트한다
[S: `func_02100cbc` (`DWCi_AUTH_GetNewWiFiInfo`), autoload_2,
`src/matched/func_02100cbc.c`], 그리고 AOSS 설정 RNG는 `hour<<10 + minute<<3 + second`를
시드에 접어 넣는다 [S: `AOSS_Rand`, ov001, `src/matched/AOSS_Rand.c`]. **매칭된 `func_ov004_*`
파일 중 RTC를 참조하는 것은 하나도 없다** [S: absence across 2,886 ov004 files in `src/matched`].

### 틱

`OS_InitTick`은 하드웨어 타이머 0을 예약하고, `OSi_TickCounter`를 0으로 만들고, 타이머를
프리스케일러 64와 오버플로 인터럽트 활성화로 프로그래밍하며, 타이머 0 IRQ에
`OSi_CountUpTick`을 설치한다 [S: `OS_InitTick`, autoload_2, `src/matched/OS_InitTick.c`].
`OS_GetTick`은 `0x04000100`의 16비트 레지스터와 소프트웨어로 확장된 상위 절반으로 64비트
답을 조합하며, 오버플로 인터럽트가 대기 중이지만 아직 처리되지 않은 구간에 대한 보정을
포함한다 [S: `OS_GetTick`, itcm, `src/matched/OS_GetTick.c`]; `OS_GetTickLo`는 레지스터를 그대로
읽는다 [S: `OS_GetTickLo`, itcm, `src/matched/OS_GetTickLo.c`]. 속도는 ARM9 시스템 클록 약
33.514 MHz를 64로 나눈 것이다; 매칭된 `OS_TicksToSeconds.c`는 없다 -- 모든 호출자가 SDK 매크로
`(tick*64)/OS_SYSTEM_CLOCK`을 각자의 자리에서 전개한다
[S: `src/matched/func_020ec5ac.c` and six `func_ov065_*` siblings].

### 포트는 대신 무엇을 하는가

포트는 `OS_GetTick`을 심(shim)으로 대체하는 대신 *레지스터*를 구동한다. 매 프레임
`TICKS_PER_FRAME` = 8,728을 `0x04000100`과 카운터에 쓰므로, `OS_GetTick`, `OS_GetTickLo`, 알람
경로와 스레드 슬립 경로가 모두 일관된 진실을 읽는다
[E: `port/platform/tick.c`; the one-second wait in `func_020b5898` compares against 523,656,
which is 8,728 x 60]. 이것은 벽시계 시간이 아니라 프레임을 세는 시계다: 절반 속도로 도는
포트는 시간도 절반 속도로 흐르는 것을 본다 [E: `port/platform/tick.c`]. 이것이 존재하기 전에는
두 읽기 모두 0을 답했고, `func_020b5898`의 상태 2는 영원히 `now - saved == 0`을 계산했으며,
프레임 900의 Nintendo 로고 화면은 프레임 120과 동일했다 [E: `port/platform/tick.c`].

RTC는 로컬에서 답하며 진행하지 않는다. `RtcWaitBusy`는 즉시 반환하고, 세 getter는 고정된
날짜에서 복사한다 [E: `port/shim/os/rtc.c`, `port/shim/os/rtcclock.c`]. 기본값은 2005-06-15
10:00:00, 수요일로, 시대에 맞고, 계절 이벤트가 없으며, 시간이 낮이고, 분이 0이어서 조명
블렌드 가중치가 정확히 테이블 항목 위에 놓이기 때문에 선택되었다
[E: `port/shim/os/rtcclock.c`]. `ACWW_RTC_DATE=YYYYMMDD`와 `ACWW_RTC_TIME=HHMMSS`로 이를
옮길 수 있다; 범위를 벗어난 값은 절반만 적용되는 대신 한 줄의 출력과 함께 통째로 거부되며,
요일은 환경에서 받는 대신 항상 사카모토(Sakamoto) 방법으로 계산된다
[E: `port/shim/os/rtcclock.c`]. 오라클도 같은 순간을 고정한다. 생성된 무비의
`rtcStart 2005-06-15T10:00:00Z`이다
[O: `port/tools/oracle/oracle.py`; `port/tools/oracle/README.md`, "How the RTC and the input
recipe are enforced"].

**왜 호스트의 시계가 아니라 고정된 시계인가.** `rtcclock.c`가 존재하기 전에 포트는 PXI 요청을
버렸으므로 `func_0209e49c`의 지역 변수는 결코 기록되지 않았고, 게임의 시계 전역 변수는 호스트
스택 쓰레기 값을 받았다. `ACWW_WATCH=0x021dc754`로 측정하면 `func_0209e49c`는 `0x001afeb8`
-- 스택 주소 -- 을 썼고 그 다음 `0xb8`을 썼다 [E: `port/shim/os/rtcclock.c`, `ACWW_WATCH=0x021dc754`].
조명 블렌드 가중치는 그 주소의 하위 바이트를 4096/60으로 스케일한 것이므로, 하나의 실행
파일 안에서는 상수였지만 실행 파일 사이에서는 달랐다: 세 빌드에서 0x00000888, 0x00000955,
0x000008cc가 기록되었다 [E: `port/shim/os/rtcclock.c`]. 죽은 코드만 다른 두 실행 파일이 세계를
다르게 비추었고, 이는 모든 고정 프레임 스크린샷 비교 아래에 20-26%의 픽셀 노이즈 바닥을
깔았으며 이미 발표된 발견 사항 하나를 철회하게 만들었다
[E: `port/shim/os/rtcclock.c`; M1]. 조용히 실제 시간을 따라가는 포트는 정확히 그 부류의
결함을 한 단계 위에서 다시 불러들일 것이다.

## 어디에 있는가

| 함수 또는 심볼 | 모듈 | 역할 | 등급/출처 |
|---|---|---|---|
| `RTC_Init` | autoload_2 | 작업 블록을 0으로 채우고, RTC PXI 태그에 `RtcCommonCallback`을 등록 | [S: `src/matched/RTC_Init.c`] |
| `RtcCommonCallback` | autoload_2 | 전체 상태 머신: `0x027ffde8`의 BCD를 디코드하고, 알람을 처리하며, 결과를 디스패치 | [S: `src/matched/RtcCommonCallback.c`] |
| `RtcBCD2HEX` | autoload_2 | BCD에서 이진수로; 9를 넘는 니블이 있으면 0 반환 | [S: `src/matched/RtcBCD2HEX.c`] |
| `RtcWaitBusy` | autoload_2 | `rtcWork.lock`을 스핀하는 다섯 개의 어셈블리 명령 | [S: `src/matched/RtcWaitBusy.c`] |
| `RtcSendPxiCommand` | autoload_2 | 명령을 비트 8..14에 패킹해 RTC 태그로 전송 | [S: `src/matched/RtcSendPxiCommand__autoload_2_0211ea98.c`] |
| `RTC_GetTime` `0x0211e894` | autoload_2 | `RTC_GetTimeAsync`의 동기 래퍼 | [S: `src/matched/RTC_GetTime.c`] |
| `RTC_GetDateTimeAsync` `0x0211e804` | autoload_2 | 시퀀스 GET_DATETIME과 두 버퍼를 설정하고 명령 0x10을 전송 | [S: `src/matched/RTC_GetDateTimeAsync.c`] |
| `RTC_GetDateAsync` `0x0211e998`, `RTC_GetTimeAsync` `0x0211e8d8` | autoload_2 | 날짜만 / 시각만 읽는 비동기 읽기 | [S: `src/matched/RTC_GetDateAsync.c`] |
| `RTC_SetDateTime` `0x0211e7c0` | autoload_2 | **이름이 잘못됨**; ROM은 `RTC_GetDateTimeAsync`로 분기하므로 이것은 `RTC_GetDateTime`이다 | [S: `src/matched/RTC_SetDateTime.c` vs the ROM word at `0x0211e7d0`] |
| `RTC_ConvertDateToDay`, `RTCi_ConvertTimeToSecond`, `RTC_ConvertDateTimeToSecond` | autoload_2 | 날짜를 일 번호로, 시각을 초로, 그리고 그 곱 | [S: `src/matched/RTC_ConvertDateToDay.c`] |
| `func_0209e49c` / `func_0209e5b4` | main | 시계를 `0x021dc744` / `0x021dc754`로 읽어 들이고, 기본 날짜에서 요일을 강제 | [S: quoted in `port/shim/os/rtcclock.c`] |
| `func_0207b05c` | main | 날짜 따라잡기: 일 단위 델타, 그 횟수만큼의 하루 단위 스텝; 시계 조작 분기 | [S: `src/matched/func_0207b05c.c`] |
| `func_020bbb6c` | main | 분으로부터의 낮/밤 블렌드 가중치 | [S: quoted in `port/shim/os/rtcclock.c`] |
| `func_ov092_02299324` | ov092 | 시계 설정 오버레이의 디스패처; 코드 0x43과 0x44가 RTC와 통신 | [S: `src/matched/func_ov092_02299324.c`] |
| `OS_GetTick`, `OS_GetTickLo` (itcm), `OS_InitTick`, `OSi_CountUpTick` (autoload_2) | itcm / autoload_2 | 프리스케일러 64의 타이머 0, 소프트웨어로 64비트 확장 | [S: `src/matched/OS_GetTick.c`, `src/matched/OS_InitTick.c`] |

## 읽고 쓰는 데이터

| 주소 또는 필드 | 의미 | 쓰는 쪽 | 읽는 쪽 |
|---|---|---|---|
| `0x027ffde8` (`OSSystemWork.real_time_clock[8]`) | 칩의 원시 BCD 레지스터 미러 | ARM7 | `RtcCommonCallback` [S: `src/matched/RtcCommonCallback.c`] |
| `rtcWork.lock` | RTC 바쁨 플래그, 콜백이 해제 | `RtcCommonCallback` | `RtcWaitBusy` [S: `src/matched/RtcWaitBusy.c`] |
| `rtcWork.buffer[0..1]` | *호출자의* 날짜 및 시각 구조체를 가리키는 포인터 | 비동기 getter들 | `RtcCommonCallback` [S: `src/matched/RTC_GetDateTimeAsync.c`] |
| `0x021dc744` | 게임의 `RTCDate` (year, month, day, week) | `func_0209e49c` | 달력과 이벤트 코드 [S: quoted in `port/shim/os/rtcclock.c`] |
| `0x021dc754` | 게임의 `RTCTime.hour` | `func_0209e49c` | 시계 경로 [E: `ACWW_WATCH=0x021dc754`, `port/shim/os/rtcclock.c`] |
| `0x021dc758` | 게임의 `RTCTime.minute` | `func_0209e49c` | `func_0209def4` 다음 `func_020bbb6c` [S: quoted in `port/shim/os/rtcclock.c`] |
| 세이브 `+0x4046` | 세이브가 마지막으로 기록된 날짜 | 세이브 경로 | `func_0207b05c` [S: `src/matched/func_0207b05c.c`] |
| `0x04000100` (`REG_TM0CNT_L`) | 하드웨어 타이머 0의 16비트 카운트 | 타이머 (포트: `acww_tick_advance`) | `OS_GetTick`, `OS_GetTickLo` [S: `src/matched/OS_GetTick.c`] |
| `OSi_TickCounter` | 틱의 소프트웨어 확장 상위 절반 | `OSi_CountUpTick` (포트: `acww_tick_advance`) | `OS_GetTick` [S: `src/matched/OSi_CountUpTick.c`] |

## 확인 방법

`../experiments/rtc-hour-sweep.md`(설계만 됨, 아직 미실행)를 보라: 같은 레시피를 하루 중 네
시각에서 실행하여, 같은 순간에 대해 포트와 오라클을 비교한다. 이미 존재하는 계측 수단은
포트 자신의 부팅 라인 `acww rtc: fixed clock year+2000=... hour=...`으로, 실행당 한 번
출력된다 [E: `port/shim/os/rtcclock.c`; present in
`scratchpad/cycle40/runs/tap-D56/tap-D56-run.log`].

## 가설

- 조명은 시각에 따른 눈에 보이는 함수이며, 포트와 원본은 이에 대해 일치한다. 측정된 모든
  실행이 10:00을 고정하므로 낮/밤 블렌드는 한 지점 이상에서 검증된 적이 없다.
  `../experiments/rtc-hour-sweep.md`로 확정한다.
- `func_0207b05c`의 시계 조작 분기는 리셋 씨(Mr. Resetti) 또는 그에 상응하는 꾸중이다. 하나의
  `ACWW_SAVE` 파일에 대해 두 번의 연속 포트 세션을 실행하되 두 번째 세션의 `ACWW_RTC_DATE`를
  첫 번째보다 이르게 설정하여 확정한다 -- 이를 위해서는 먼저 세이브 저장소가 지속되어야
  한다(`save-data.md`).
- 포트가 계산한 요일과 칩에 저장된 요일은 범위 내 모든 날짜에 대해 일치한다. ROM은 칩의
  3비트 필드를 신뢰하고 포트는 사카모토 방법으로 계산한다; 포트에서는 둘이 불일치할 수 없지만,
  에뮬레이트된 칩이 자체 값을 공급하는 오라클에서는 불일치할 수 있다. 요일이 알려진 날짜에서
  오라클 프로브 모드로 `0x021dc744+12`를 읽어 확정한다.
- 시계가 결코 진행하지 않는 것은 90,000프레임 실행 동안 게임에 보이지 않는다. 지지 근거:
  90,000프레임까지 결함도 정지도 없음 [E: `scratchpad/cycle40/runs/tap-D59`, LONG41]. 그 실행에서
  분 경계를 기다리는 것이 아무것도 없었기 때문에 이는 가설로 남는다; 상점 폐점처럼 게임이
  분 단위로 시간을 재는 씬에 대한 오라클 비교로 확정한다.

## 관련 문서

- `../experiments/rtc-hour-sweep.md` -- 설계된 스윕.
- `save-data.md` -- 게임이 비교 대상으로 삼는 날짜가 저장되는 곳.
- `rng.md` -- RTC와 틱은 두 개의 엔트로피 소스다.
