# 시간과 실시간 시계
<!-- source: wiki/systems/time-and-rtc.md -->

**요약.** 동물의 숲은 날짜에 관한 게임이고, 그 날짜는 DS의 ARM7 프로세서만 읽을 수 있는
배터리 백업 시계 칩에서 온다. 게임은 비동기 요청을 통해 날짜를 요청하고, 칩의 BCD 자릿수를
숫자로 변환하며, 그 답을 두 개의 전역 변수에 저장하고, 세이브가 기록된 날짜와 비교한다 --
놓친 날을 하루하루 모두 재생하면서. 두 번째 시계인 하드웨어 틱 카운터는 이와 무관하며,
날짜가 아니라 프레임 단위로 짧은 간격을 측정한다. PC 포트는 RTC의 ARM7 쪽을 에뮬레이트한다:
2005-06-15 10:00:00에서 시작해 59.8261프레임마다 1초씩 진행하므로, 플레이하는 동안 게임
시간이 흐르면서도 여전히 프레임 수의 순수 함수로 남는다.

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
[H: source account: read from `extract/adm-kr/arm9/unk_autoload_2.bin` and the autoload_2 symbol table, as
recorded in `port/shim/os/rtcclock.c`; direct ROM-source provenance unresolved]. `0x0211e7c0`은 `RTC_GetDateTime`이다. 하니스가 호출
변위를 마스킹하기 때문에 바이트 매칭으로는 둘을 구별할 수 없다 -- 이것은 결함 클래스 D12,
잘못 타이핑된 대상을 인코딩한 이름이다 [H: source account: `docs/rules/D-defects.md` D12; direct ROM-source provenance unresolved].

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
[S: `func_020bbb6c` / `func_0209def4`, main, quoted in
`port/shim/os/rtcclock.c`].

**시계는 게임플레이 RNG를 한 번 시드하며, 이후 시계 조건은 추출 횟수를 바꾼다.** `func_02061530`은 `func_0209dbbc()`로 `0x021cb5a0`을 설정한다. 이 함수는 `minute | day<<8 | hour<<16 | second<<24`를 접어 넣고 연·월·요일·틱은 제외한다 [S: `src/matched/func_02061530.c`, `src/matched/func_0209dbbc.c`].
ORACLE46은 포트의 프레임 3과 시계 조건을 적용한 원본 및 적용하지 않은 원본의 프레임 44에서 같은 시드 `0x000a0f00`을 측정했다 [E: `scratchpad/oracle46/RECEIPTS.md`;
log: `docs/log/cycle41-gameplay.md` O46-1, O46-4].
ORACLE47에서는 프레임 10,000의 두 원본 모두 추출 인덱스 1,430이었으나 11,000에서는 조건 적용 시 1,532, 미적용 시 1,529였다. 조건 적용으로 늘어난 14개 추출은 모두 10,000 이후 마을 이름 화면에서 확정할 때까지 소비됐다 [E: `scratchpad/oracle46/ledgers/o-townarm.jsonl`,
`scratchpad/oracle46/ledgers/o-townoff.jsonl`; log: `docs/log/cycle41-gameplay.md` O47-3].
마을 id 추출 인덱스는 포트 2,667, 조건 없는 원본 2,684, 조건을 적용한 원본 2,698이므로 시드만 맞춰서는 마을이 같아지지 않았다 [E: `scratchpad/oracle46/RECEIPTS.md`; log: `docs/log/cycle41-gameplay.md` O46-4].
같은 맵에서 게임플레이를 비교하려면 `port/tools/oracle/README.md`의 레시피 선택 표에 있는 정방향 레시피를 쓴다. 포트의 두 번째 탭은 24,908, 오라클 시계 조건 없는 원본은 24,700이며, 마을 `0x8365`에서 새로 만든 체인과 문서에 기록된 HUD 시계 차이 13m22s를 사용한다 [E: `scratchpad/oracle50/RECEIPTS.md`; log: `docs/log/cycle41-gameplay.md` O50-0, O50-3;
recipe: `port/tools/oracle/README.md`].

게임 자체의 시계 밖에서 RTC는 엔트로피 소스다. Wi-Fi 신원 생성기는 초로 변환한 RTC 날짜와
시각으로 16비트 LCG를 시드하며, 틱 카운터가 사용 가능하면 그것으로 솔트한다
[S: `func_02100cbc` (`DWCi_AUTH_GetNewWiFiInfo`), autoload_2,
`src/matched/func_02100cbc.c`], 그리고 AOSS 설정 RNG는 `hour<<10 + minute<<3 + second`를
시드에 접어 넣는다 [S: `AOSS_Rand`, ov001, `src/matched/AOSS_Rand.c`]. **매칭된 `func_ov004_*`
파일 중 RTC를 참조하는 것은 하나도 없다** [H: source account: absence across 2,886 ov004 files in `src/matched`; direct ROM-source provenance unresolved].

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
[H: log/source account: `port/platform/tick.c`; the one-second wait in `func_020b5898` compares against 523,656,
which is 8,728 x 60; receipt provenance unresolved]. 이것은 벽시계 시간이 아니라 프레임을 세는 시계다: 절반 속도로 도는
포트는 시간도 절반 속도로 흐르는 것을 본다 [H: host-source account from `port/platform/tick.c`; verify with a retained scripted run and frame using this page's recipe]. 이것이 존재하기 전에는
두 읽기 모두 0을 답했고, `func_020b5898`의 상태 2는 영원히 `now - saved == 0`을 계산했으며,
프레임 900의 Nintendo 로고 화면은 프레임 120과 동일했다 [H: host-source account from `port/platform/tick.c`; verify with a retained scripted run and frame using this page's recipe].

**RTC에 관해서는 포트가 ARM7이고, 시계는 진행한다 (RTC42).** 인터프리터 경로에서는 세
동기 getter가 호스트 레지스트리에서 거부되므로 ROM 자체의 SDK 코드가 끝까지 실행된다:
`RTC_GetDateTime`은 호출자의 버퍼를 비동기 계층에 넘기고, `RtcSendPxiCommand`는 PXI 태그 5에
`(0x10 << 8)`을 게시하며, 포트의 `PXI_SendWordByFifo`가 답한다 -- 현재 순간을 두 개의
`RTCRawDate`/`RTCRawTime` 워드에 패킹해 `0x027ffde8`의 시스템 작업 영역에 쓰고, ROM이
등록한 수신 콜백에 `command << 8 | RTC_PXI_RESULT_SUCCESS`를 전달하므로, BCD 디코딩은
`RtcCommonCallback`이 수행한다
[E: `port/shim/os/pxisend.c`, `rtc_request`; run `off-rtc42-on` -- its `acww rtc` lines are harvested as `scratchpad/rtc42/rtcline-off-rtc42-on.txt`, and `scratchpad/rtc42/README.md` indexes the arm; the run directory itself stayed in RTC42's worktree -- log line
`acww rtc/arm7: command 0x10 raw date 0x03150605 time 0x00000010 -> callback`]. 응답은 전송
안에서 동기적으로 전달되며, 그 양쪽 절반 모두가 강제된 것이다: `RtcWaitBusy`는 양보(yield)
없이 스핀하므로 큐에 쌓인 응답을 전달하기 위해 진행할 것이 아무것도 없고,
`RTC_GetDateTimeAsync`는 전송하기 전에 락, 시퀀스, 두 버퍼, 콜백을 설정하므로 전송 안에서의
응답이 안전하다 -- SDK가 전송이 반환된 뒤에 `command_flg`를 설정하는 터치 패널의 태그 6과는
정반대다
[S: `src/matched/RtcWaitBusy.c`, `src/matched/RTC_GetDateTimeAsync.c`;
E: `docs/kb/hybrid/hardware-services.md`, "Tag 5"]. 네이티브 경로에서는 실행할 인터프리트된
ROM이 없으므로, 세 getter는 여전히 같은 모델에서 직접 답한다
[H: source/log account from `port/shim/os/rtcclock.c`; verify with a retained run using this page's recipe].

**어떻게 진행하는가.** 한 프레임은 에뮬레이트된 시간으로 1/59.8261초 -- NDS의 33.513982 MHz
클록으로 560190사이클이며, 포트의 프레임 페이서가 쓰는 것과 같은 쌍이다 -- 이고, 순간은
프레임 수의 순수 함수, 즉 `boot + floor(frames * 560190 / 33513982)`초이며, 자정 넘김, 월
길이, 윤일, 요일이 거기서 계산된다
[H: log/source account: `port/shim/os/rtcclock.c`; `port/tools/test_rtc.py` calibrates fourteen cases including a
leap day, three month ends and midnight; receipt provenance unresolved]. 이는 긴장 관계에 있던 두 속성을 모두 지킨다:
플레이하는 동안 게임 시간이 흐르고, 같은 레시피를 두 번 실행해도 여전히 같은 실행인데,
아무것도 벽시계 시간을 읽지 않기 때문이다. 틱이 하는 것과 같은 거래다 -- 절반 속도로 도는
포트는 게임 시간도 절반 속도로 흐르는 것을 본다.

기본 부팅 순간은 2005-06-15 10:00:00, 수요일로, 시대에 맞고, 계절 이벤트가 없으며, 시간이
낮이고, 분이 0이어서 조명 블렌드 가중치가 정확히 테이블 항목 위에서 시작하기 때문에
선택되었다 [H: host-source account from `port/shim/os/rtcclock.c`; verify with a retained scripted run and frame using this page's recipe].
`ACWW_RTC_DATE=YYYYMMDD`와 `ACWW_RTC_TIME=HHMMSS`로 이를 옮길 수 있다; 범위를 벗어난 값은
절반만 적용되는 대신 한 줄의 출력과 함께 통째로 거부되며, 요일은 환경에서 받는 대신 항상
사카모토(Sakamoto) 방법으로 계산된다. `ACWW_RTC_FREEZE=1`은 RTC42 이전의 고정된 시계를
정확히 복원하는데, 길이가 다른 두 실행으로 하나의 순간을 봐야 하는 진단을 위한 것이다
[H: host-source account from `port/shim/os/rtcclock.c`; verify with a retained scripted run and frame using this page's recipe]. 시계는 세이브스테이트에 실린다 --
부팅 순간, 고정 플래그, "순간 결정됨" 플래그 -- 그래서 재개된 실행은 로딩 셸의 환경을 다시
읽는 대신 스냅샷 당시의 시계를 유지한다
[H: log/source account: `port/platform/state.c`; `docs/kb/hybrid/savestate.md`; receipt provenance unresolved].

오라클도 같은 부팅 순간을 고정한다. 생성된 무비의 `rtcStart 2005-06-15T10:00:00Z`이며,
DeSmuME는 거기서부터 에뮬레이트된 시간으로 에뮬레이트된 칩을 진행시키므로, 둘은 부팅
시점에서만이 아니라 특정 프레임에서도 일치한다 [O: `port/tools/oracle/oracle.py`, `RTC_START`;
`port/tools/oracle/README.md`].

**결정지은 숫자.** 워크아웃 조건의 프레임 53,100에서 원본의 HUD 패널은 `6/15 AM10:14`를,
포트의 것은 `6/15 AM10:00`을 읽는다
[O: `scratchpad/oracle/walkout/orig`, `side-by-side-53100.png`;
E: `docs/log/cycle41-gameplay.md` ORACLE44 item 4]. 53,100프레임은 에뮬레이트된 887초 --
14분 47초 -- 이므로 10:14:47이고, 포트는 이제 원본이 읽는 것을 읽는다
[E: `port/tools/test_rtc.py`, case `oracle-53100`; the two zoomed HUD stills are
`scratchpad/rtc42/port-53100-bot.png` and `orig-53100-bot.png`]. 이는 ORACLE44의 마지막 미결
항목을 닫는데, 그 항목은 두 HUD가 정확히 이 프레임에서 갈라지는 것을 포트의 의도적인
비진행으로 기록해 두었다 [O: `scratchpad/oracle/walkout/side-by-side-53100.png`;
`docs/log/cycle41-gameplay.md` ORACLE44 item 4].

**보존된 모든 레퍼런스에 대한 결과이며, 이 페이지 밖의 페이지에도 적용된다.**
분이 `func_020bbb6c`의 낮/밤 블렌드를 구동하므로 이제 프레임은 시계에 의존하며, 따라서
**RTC42 이전에 찍은 실행과 비교하려면 `ACWW_RTC_FREEZE=1`을 설정해야 한다** -- 시계가
진행하면 OFF 레시피의 모든 프레임이 고정 빌드의 것과 달라지는데, 오라클에 대한 평균 ncc는
변함이 없다(둘 다 0.997413, 최악 프레임 -0.000008)
[E: `scratchpad/rtc42/analyse.txt`; `docs/log/cycle41-gameplay.md` RTC42]. 고정 조건은 PXI
재작성 자체가 중립적이라는 영수증이기도 하다: 고정하면 RTC42 이전 빌드와 31/31 동일하다
[E: `scratchpad/rtc42/analyse.txt`].

**왜 호스트의 시계가 아니라 프레임 구동 시계인가.** `rtcclock.c`가 존재하기 전에 포트는 PXI
요청을 버렸으므로 `func_0209e49c`의 지역 변수는 결코 기록되지 않았고, 게임의 시계 전역 변수는
호스트 스택 쓰레기 값을 받았다. `ACWW_WATCH=0x021dc754`로 측정하면 `func_0209e49c`는
`0x001afeb8` -- 스택 주소 -- 을 썼고 그 다음 `0xb8`을 썼다 [H: host-source account from `port/shim/os/rtcclock.c`, `ACWW_WATCH=0x021dc754`; verify with a retained scripted run and frame using this page's recipe].
조명 블렌드 가중치는 그 주소의 하위 바이트를 4096/60으로 스케일한 것이므로, 하나의 실행
파일 안에서는 상수였지만 실행 파일 사이에서는 달랐다: 세 빌드에서 0x00000888, 0x00000955,
0x000008cc가 기록되었다 [H: host-source account from `port/shim/os/rtcclock.c`; verify with a retained scripted run and frame using this page's recipe]. 죽은 코드만 다른
두 실행 파일이 세계를 다르게 비추었고, 이는 모든 고정 프레임 스크린샷 비교 아래에 20-26%의
픽셀 노이즈 바닥을 깔았으며 이미 발표된 발견 사항 하나를 철회하게 만들었다
[H: log/source account: `port/shim/os/rtcclock.c`; M1; receipt provenance unresolved]. 조용히 호스트 시간을 따라가는 포트는 정확히 그 부류의
결함을 한 단계 위에서 다시 불러들일 것이다 -- 하나의 레시피를 두 번 실행해도 하루 중 다른
시각에 시작했다는 이유로 달라질 것이다. 프레임 수로 시계를 구동하면 결정성을 지키면서
게임에 달력을 돌려준다; 그 대가는 길이가 다른 두 실행이 더는 같은 순간에 있지 않다는
것인데, 이는 노이즈 바닥이 아니라 실제 차이다 [H: host-source account from `port/shim/os/rtcclock.c`; verify with a retained scripted run and frame using this page's recipe].

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
| `func_0209e49c` / `func_0209e5b4` | main | 시계를 `0x021dc744` / `0x021dc754`로 읽어 들이고, 기본 날짜에서 요일을 강제 | [S: `src/matched/func_0209e49c.c`, `src/matched/func_0209e5b4.c`; historical account: quoted in `port/shim/os/rtcclock.c`] |
| `func_0207b05c` | main | 날짜 따라잡기: 일 단위 델타, 그 횟수만큼의 하루 단위 스텝; 시계 조작 분기 | [S: `src/matched/func_0207b05c.c`] |
| `func_020bbb6c` | main | 분으로부터의 낮/밤 블렌드 가중치 | [S: `src/matched/func_020bbb6c.c`; historical account: quoted in `port/shim/os/rtcclock.c`] |
| `func_ov092_02299324` | ov092 | 시계 설정 오버레이의 디스패처; 코드 0x43과 0x44가 RTC와 통신 | [S: `src/matched/func_ov092_02299324.c`] |
| `OS_GetTick`, `OS_GetTickLo` (itcm), `OS_InitTick`, `OSi_CountUpTick` (autoload_2) | itcm / autoload_2 | 프리스케일러 64의 타이머 0, 소프트웨어로 64비트 확장 | [S: `src/matched/OS_GetTick.c`, `src/matched/OS_InitTick.c`] |

## 읽고 쓰는 데이터

| 주소 또는 필드 | 의미 | 쓰는 쪽 | 읽는 쪽 |
|---|---|---|---|
| `0x027ffde8` (`OSSystemWork.real_time_clock[8]`) | 칩의 원시 BCD 레지스터 미러 | ARM7 | `RtcCommonCallback` [S: `src/matched/RtcCommonCallback.c`] |
| `rtcWork.lock` | RTC 바쁨 플래그, 콜백이 해제 | `RtcCommonCallback` | `RtcWaitBusy` [S: `src/matched/RtcWaitBusy.c`] |
| `rtcWork.buffer[0..1]` | *호출자의* 날짜 및 시각 구조체를 가리키는 포인터 | 비동기 getter들 | `RtcCommonCallback` [S: `src/matched/RTC_GetDateTimeAsync.c`] |
| `0x021dc744` | 게임의 `RTCDate` (year, month, day, week) | `func_0209e49c` | 달력과 이벤트 코드 [S: `src/matched/func_0209e49c.c`; historical account: quoted in `port/shim/os/rtcclock.c`] |
| `0x021dc754` | 게임의 `RTCTime.hour` | `func_0209e49c` | 시계 경로 [H: log/source account: `ACWW_WATCH=0x021dc754`, `port/shim/os/rtcclock.c`; receipt provenance unresolved] |
| `0x021dc758` | 게임의 `RTCTime.minute` | `func_0209e49c` | `func_0209def4` 다음 `func_020bbb6c` [S: `src/matched/func_0209def4.c`, `src/matched/func_020bbb6c.c`; historical account: quoted in `port/shim/os/rtcclock.c`] |
| 세이브 `+0x4046` | 세이브가 마지막으로 기록된 날짜 | 세이브 경로 | `func_0207b05c` [S: `src/matched/func_0207b05c.c`] |
| `0x04000100` (`REG_TM0CNT_L`) | 하드웨어 타이머 0의 16비트 카운트 | 타이머 (포트: `acww_tick_advance`) | `OS_GetTick`, `OS_GetTickLo` [S: `src/matched/OS_GetTick.c`] |
| `OSi_TickCounter` | 틱의 소프트웨어 확장 상위 절반 | `OSi_CountUpTick` (포트: `acww_tick_advance`) | `OS_GetTick` [S: `src/matched/OSi_CountUpTick.c`] |

## 확인 방법

`python port/tools/test_rtc.py`는 `port/shim/os/rtcclock.c` 자체 -- 복사본이 아니라 실제
출하되는 파일 -- 를 컴파일하고, 열네 개의 보정 사례를 통과시킨다: 부팅 순간, 자정, 30일과
31일짜리 월말, 2004년 윤일로 들어가고 나오는 경우, 2005년의 윤년 아닌 2월, 연말, 만 1년치
프레임, 오라클 자체의 프레임 53,100, 고정 탈출구, 그리고 오후 비트. 패킹된 모든 워드를 SDK의
`RtcBCD2HEX`와 `RTCRawDate`/`RTCRawTime` 비트필드의 독립적인 전사본으로 다시 디코드하고,
페이서와 시계가 여전히 같은 초를 나누는지, `pxisend.c`가 `0x027ffde8`에 원시 블록을 쓰는지,
PXI 태그 5가 디스패치되는지, 시계가 세이브스테이트에 등록되어 있는지를 정적으로 검사한다
[H: source/log account from `port/tools/test_rtc.py`; verify with a retained run using this page's recipe].

실행 중에는 세 가지 계측 수단이 있다: 부팅 라인
`acww rtc: frame-driven clock, 59.8261 frames = 1 s boot 2005-6-15 week=3 10:0:0` (또는 그
`FROZEN` 형태), ARM7의 첫 네 응답
(`acww rtc/arm7: command 0x10 raw date ... -> callback`, ARM9 콜백 슬롯이 있는지 없는지를
알려준다), 그리고 게임 내 1분마다 그 분이 바뀐 프레임과 함께 한 줄을 출력하는
`ACWW_RTC_TRACE=1` [E: `port/shim/os/rtcclock.c`, `port/shim/os/pxisend.c`;
`scratchpad/rtc42/rtcline-off-rtc42-on.txt`, the harvested `acww rtc` lines of run `off-rtc42-on`].

`../experiments/rtc-hour-sweep.md`(설계만 됨, 아직 미실행)도 보라: 같은 레시피를 하루 중 네
시각에서 실행하여, 같은 순간에 대해 포트와 오라클을 비교한다.

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
- **RTC42로 폐기됨.** "시계가 결코 진행하지 않는 것은 90,000프레임 실행 동안 게임에 보이지
  않는다"는 90,000프레임까지 결함도 정지도 없다는 것에 기대고 있었고
  [E: `scratchpad/cycle40/runs/tap-D59`, LONG41], 프레임 53,100에서 HUD가 갈라지는 것으로
  이미 반박되어 있었다. 이제 시계는 진행한다; 미결 질문은 그와 함께 아래로 옮겨졌다.
- 포트의 진행하는 시계와 오라클의 시계는 긴 실행에서도 보조를 맞춘다. 두 속도는 구성상
  동일하지 않다: 포트는 에뮬레이트된 프레임을 33513982/560190으로 나누고, DeSmuME는 무비의
  시작 날짜부터 자신의 에뮬레이트된 시간으로 에뮬레이트된 칩을 진행시킨다. 206,000프레임당
  1초의 드리프트는 53,100에서는 보이지 않지만 하루 단위에서는 보일 것이다. 하나의 조건에서
  멀리 떨어진 두 프레임의 HUD를 비교하여 확정한다.
- 포트의 시계가 자정을 넘을 때 게임 자체의 날짜 넘김이 발동하고 `func_0207b05c`의 따라잡기가
  실행된다. 아직 자정을 넘겨 포트 조건을 실행한 적은 없다 -- 게임 시간 24시간은 517만
  프레임이므로, 긴 조건보다는 `ACWW_RTC_TIME=235900`과 짧은 조건이 필요하다. 그 조건에
  `ACWW_SAVE`를 더하고 `0x021dc744`를 관찰하여 확정한다.

## 관련 문서

- `../experiments/rtc-hour-sweep.md` -- 설계된 스윕.
- `save-data.md` -- 게임이 비교 대상으로 삼는 날짜가 저장되는 곳.
- `rng.md` -- RTC와 틱은 두 개의 엔트로피 소스다.
