# 터치 지연: 접촉이 게임에 도달하는 데 몇 프레임이 걸리며, 어떤 순서로 도달하는가
<!-- source: wiki/experiments/touch-latency.md -->

**상태: 실행됨.** 이 페이지는 인터프리터 경로에서 스타일러스 접촉이 지나가는 파이프라인을
끝에서 끝까지 측정한 것이고, 같은 프레임에 예약된 탭과 버튼 입력 중 어느 쪽이 게임에
먼저 도달하는지를 결정하는 순서 규칙이다. *좌표*를 측정한 `touch-calibration.md`의
속편이며, 이 페이지는 *타이밍*을 측정한다.

## 목적

`touch-calibration.md`는 원본이 탭을 포트보다 한두 프레임 늦게 전달한다는 것을 확립했고,
한쪽에서만 동작하는 모든 탭에 대한 상시 설명으로 남겨 두었다. 두 가지 질문이 열려 있었다.
지연은 어디서 오는가 -- 에뮬레이터, ARM7, 아니면 ROM? 그리고 원본의 동작을 재현하는 데
지연만으로 충분한가, 아니면 다른 무언가가 같은 프레임의 입력과 탭의 순서를 정하는가?
답은 이렇다: 지연은 전적으로 ROM 자체의 규칙이고, 지연만으로는 충분하지 **않다** --
ROM의 VBlank 핸들러에 대한 ARM7 샘플의 상대 위치가 메커니즘의 나머지 절반이다.

## 파이프라인, 단계별로

1. **ARM7이 패널을 프레임당 `frequence`번 샘플링한다.** `func_020e948c`가
   `TP_RequestAutoSamplingStartAsync(0, 4, &gAutoData, 9)`를 요청하므로, ACWW는 프레임당
   네 샘플로 **아홉 항목 링**을 돌린다 -- 2.25프레임의 이력이며, 마지막 네 항목이 정확히
   한 프레임분이다 [S: `src/matched/func_020e948c.c`; source account: `func_020e948c`, autoload_2, `src/matched/func_020e948c.c`].
2. **펜업은 자체 인코딩을 가진다.** 펜이 떨어져 있을 때 ARM7은 x=0, y=0, touch=0,
   validity=3(`TP_VALIDITY_INVALID_XY`)을 쓴다; 펜다운 샘플은 압력 검사가 거부하지 않는 한
   validity 0으로 원시 카운트를 담는다
   [H: source account: NitroSDK `libraries/spi/src/ARM7/tp/tp_sampling.c`, `TP_ExecSampling` -- public source,
   <https://github.com/ntrtwl/NitroSDK>; direct ROM-source provenance unresolved].
3. **전달이 링을 전진시킨다.** `TPi_TpCallback`은 PXI 태그 6에서 돌며, `tpState.index`를
   버퍼 크기의 모듈로로 증가시키고, 공유 시스템 작업 영역에서 패킹된 비트필드(x:12, y:12,
   touch:1, validity:2)를 풀어낸다 [S: `src/matched/TPi_TpCallback.c`; source account: `TPi_TpCallback`, autoload_2, `src/matched/TPi_TpCallback.c`].
4. **ROM은 세 샘플 규칙 아래 프레임당 최대 한 점을 공개한다.** `func_020e9314`는
   `TP_GetLatestIndexInAuto`를 통해 latest-4..latest-1 항목을 읽고, **연속 세 항목이 터치
   상태이고 유효할 때만** 공개하며, 가운데 것을 공개한다; 아무것도 터치되지 않았을 때는
   x = y = 0xff를 쓴다; 그 외의 경우는 `TP_POINT`를 그대로 둔다 [S: `src/matched/func_020e948c.c`, `src/matched/TPi_TpCallback.c`, `src/matched/TP_GetLatestIndexInAuto.c`; source account: `func_020e9314`, autoload_2, disassembly `0x020e9314`..`0x020e9470`; the no-touch
   write is a `mov r1,#0xff` / `strh` pair at `0x020e941c`, i.e. **0x00ff, not 0xffff** --
   the port's earlier transcription had 0xffff and is now pinned by
   `port/tools/test_scheduled_touch.py`].
   소비자 `func_020b9280`은 두 좌표를 모두 `u8`로 절단한다 [S: `src/matched/func_020b9280.c`; source account: `src/matched/func_020b9280.c`].

지연은 1단계에서 4단계가 따라 나오는 것이다: 프레임당 네 샘플이면, 프레임 경계에서 시작한
접촉은 다음 프레임이 되어야 연속 세 개의 양호한 샘플을 가질 수 있으므로, 점은 한 프레임
늦게 나타난다.

## 인터프리터 경로에서 포트가 하는 일

`port/shim/input/touch.c`는 인터프리터 경로에서 **거부**되므로(`DENY_FILES`, 레지스트리
89 -> 88), ROM 자체의 `func_020e9314`가 돌고 포트는 대신 ARM7 역할을 한다:
`port/shim/os/pxisend.c`가 AUTO_ON 요청(태그 6, 명령 1, 하위 바이트 = 프레임당 샘플 수)을
기록하고, 그때부터 VBlank마다 `frequence`개의 샘플을 ROM 자체의 `tpState`(`0x02206134`)에
쓴 뒤, `TPi_TpCallback`의 AUTO_SAMPLING 단계 -- index+1 mod bufSize, 복사 -- 를 호스트에서
수행한다. 원시 카운트는 `port/shim/boot/usersettings.c`가 공개하는 항등 보정(raw1 16/16
-> 1/1, raw2 4080/3056 -> 255/191) 아래에서 화면 픽셀 x 16이다
[H: source account: `docs/log/cycle40-keyboard-gate-probe.md` TOUCH41; direct ROM-source provenance unresolved]. 네이티브 시절의 전부 0인 보정은
`TP_SetCalibrateParam`이 기울기 0을 설치하게 하여 모든 탭을 0,0으로 보정했을 것이고,
그것이 이 중 어떤 것도 측정하기 전에 항등 보정이 먼저 공개되어야 했던 이유다 [H: source account: `docs/log/cycle40-keyboard-gate-probe.md` TOUCH41; direct ROM-source provenance unresolved].

## 레시피

세 조건 모두 `scratchpad/cycle40/run_direct.py`를 통한 `port/build/acww.exe`의 진단
실행이며, 영수증이 있는 프론티어 주장이 결코 아니다(B38). 기반은 두 번 탭 마을
레시피(`two-tap-town-recipe.md`)이고, 아래 줄들만 다르다.

**조건 1 -- 지연 측정(링과 점을 들여다보기).**

    python -B scratchpad/cycle40/run_direct.py tap-T41pd ACWW_INTERP=1 \
      ACWW_TOUCH_ENABLE=1 ACWW_TOUCH_X=221 ACWW_TOUCH_Y=181 \
      ACWW_TOUCH_AT=8700 ACWW_TOUCH_FOR=10 ACWW_TOUCH_EVERY=60 ACWW_TOUCH_REPEAT=2 \
      ACWW_TP_DIRECT=1 ACWW_INTERP_PEEK=0x021fbde8,0x02206134,0x02206144 \
      ACWW_STOP_FRAME=8705 ACWW_SHOT_AFTER=8400 ACWW_SHOT_EVERY=150

**조건 2 -- 24,600에서의 순서 검사, ROM의 VBlank 핸들러 전에 샘플.**

    ... ACWW_TOUCH2_X=221 ACWW_TOUCH2_Y=181 ACWW_TOUCH2_AT=24600 ACWW_TOUCH2_FOR=10 \
        ACWW_TOUCH2_EVERY=60 ACWW_TOUCH2_REPEAT=2 \
        ACWW_STOP_FRAME=27000 ACWW_SHOT_AFTER=6000 ACWW_SHOT_EVERY=300      # tap-T41h

**조건 3 -- 같은 것, 핸들러 뒤에 샘플(`ACWW_TP_LATE=1`; 이제 기본값).**

    ... the same lines plus ACWW_TP_LATE=1                                   # tap-T42b

각 27,000프레임 조건을 오라클과 다음으로 비교한다

    python port/tools/oracle/compare.py \
      scratchpad/cycle40/runs/<arm> scratchpad/oracle/tap-window

24,700 변형은 `scratchpad/oracle/tap-24700`과 비교한다.

## 예상 관측

| 무엇 | 어디 | 관측 |
|---|---|---|
| 한 프레임의 지연 | 8,700에 예약된 접촉 | 링은 x 3536, y 2896(221 x 16, 181 x 16), touch 1인 아홉 샘플을 담고, `TP_POINT` = (221,181) 터치됨이 **프레임 8,701**에 처음 출력된다 [E: `scratchpad/cycle40/runs/tap-T41pd`] |
| 핸들러 전의 샘플, 24,600의 탭 | 포트 대 원본 | 원본이 키보드에 머무는 곳에서 포트는 마을 이름을 **확정한다**(24,900부터 위 화면이 검음 = 택시 이동), 24,900..27,000에서 ncc 0.70 [E: `scratchpad/cycle40/runs/tap-T41h`] [O: `scratchpad/oracle/tap-window`] |
| 핸들러 뒤의 샘플, 24,600의 탭 | 포트 대 원본 | 포트가 원본처럼 **키보드에 머문다**: 24,000..27,000의 11프레임이 평균 ncc **0.9981**, 위 화면 0.97-0.99(양쪽 모두 키보드) [E: `scratchpad/cycle40/runs/tap-T42b`] [O: `scratchpad/oracle/tap-window`] |
| 같은 순서 아래의 24,700 레시피 | 포트 대 원본 | 여전히 확정하고 여전히 일치한다: 11프레임이 평균 ncc **0.9987**, 24,900부터 위 화면 1.0000 [E: `scratchpad/cycle40/runs/tap-T42c`] [O: `scratchpad/oracle/tap-24700`] |

**세 번째 행이 확립하는 메커니즘.** ROM의 VBlank 핸들러가 패드를 샘플링한다. 따라서 같은
프레임의 탭과 스크립트된 A 입력은 탭의 샘플이 핸들러 **뒤에** 도착할 때만 입력 우선으로
게임에 도달한다 -- 그리고 이것이 하드웨어가 만드는 순서인데, ARM7은 핸들러가 돌았던
VBlank 다음에 오는 프레임 동안 패널을 샘플링하기 때문이다. 24,600은 KEYS3의 A 입력
프레임(2400 + 37 x 600)이고 8,700은 아니며, 그것이 불일치가 24,600에서만 나타난 이유다
[H: source account: `docs/log/cycle40-keyboard-gate-probe.md` TOUCH42; direct ROM-source provenance unresolved]. `ACWW_TP_EARLY=1`은 기록을 위해
TOUCH41의 순서를 되돌린다 [H: source account: `docs/log/cycle40-keyboard-gate-probe.md` TOUCH42; direct ROM-source provenance unresolved].

## 반증 조건

- 조건 1이 `TP_POINT`를 8,701이 아니라 8,700에 출력하거나, 들여다본 시점에 링이 연속
  세 개 미만의 터치되고 유효한 항목을 담고 있는 것: 그러면 세 샘플 규칙은 지연을 만드는
  것이 아니고 `func_020e9314`에 대한 해석 전체가 틀린 것이다.
- 조건 3이 마을 이름을 확정하는 것. 그것은 정확히 조건 2가 한 일이므로 두 조건은 서로의
  대조군이다; 전환이 더 이상 중요하지 않다면 순서 주장은 죽는다.
- 순서를 바꾼 뒤 24,700 레시피가 일치를 멈추는 실행. 바로 그 이유로 재측정했는데
  (`tap-T42c`), 24,700을 깨서 24,600을 고치는 수정은 수정이 아니기 때문이다.

## 미해결

- **인터프리트된 콜백 이상 현상(플레이북 사례 42).** [H] 첫 구현은 각 샘플을
  `acww_pxi_deliver_pending`을 통해 PXI 워드로 ROM 자체의 `TPi_TpCallback`에 전달했다 --
  IRQ 컨텍스트에서 프레임당 인터프리트된 호출 넷. 호스트 채움과 **데이터가 동일**했는데도
  (`tap-T41q8705` 대 `tap-T41pd`: 같은 링, 같은 인덱스, 같은 `TP_POINT`) 게임이 달라졌다:
  택시 대화가 스크립트된 입력 없이 넘어갔고 두 이름 키보드 모두 왼쪽 위 키를 여덟 번
  입력하고 확정하여, 약 24,000 대신 프레임 8,610에 마을 이름 키보드에 도달했다
  [E: `scratchpad/cycle40/runs/tap-T41j`, and `-T41a`, `-T41d`, `-T41g`, `-T41l`, `-T41v`].
  그 동안 `TP_POINT`는 한 번도 바뀌지 않았다 [H: log/source account: `tap-T41f`, the on-change instrument in
  `pxisend.c`; receipt provenance unresolved]. 샘플러를 끈 것(`tap-T41k`)과 호스트 채움(`tap-T41w`)은 모두 게임의 속도를
  베이스라인(`tap-D71`)의 것으로 남긴다; 프레임당 인터프리트된 콜백 하나(`tap-T41x`)는
  약간 앞당긴다; 프레임당 인터프리트된 **no-op** 호출 넷(`TP_GetLatestIndexInAuto`,
  `tap-T41n`)은 그러지 않는다. 링 인덱스에 대한 읽기 워치포인트
  (`ACWW_INTERP_RWATCH=0x02206140`, `tap-T41y`)는 그 유일한 두 독자,
  `TP_GetLatestIndexInAuto`(`0x0211d010`)와 콜백 자신을 지목한다. 그러므로 게임은 콜백이
  쓰는 것이 아니라 콜백의 인터프리트된 *실행*에 반응한다: 입력 경로에 대한
  `acww_interp_irq_run`의 알려지지 않은 부작용이다 [H: source account: `docs/log/cycle40-keyboard-gate-probe.md`
  TOUCH41; `docs/kb/hybrid/stall-playbook.md` case 42; direct ROM-source provenance unresolved]. 호스트 채움이 출하된다;
  `ACWW_TP_PXI=1`은 이것을 추적할 사람을 위해 인터프리트 경로를 유지한다.
  **이를 결판낼 실험:** `ACWW_TP_PXI=1`을 *접촉을 끈 채로* 돌려서, 프레임당 인터프리트된
  콜백 넷은 여전히 돌되 펜업 샘플만 나르게 한다. 게임이 여전히 앞서 달리면 부작용은
  `acww_interp_irq_run` 자체(인터럽트 중첩, IRQ 스택, 또는 CPSR 왕복)에 있고 터치 데이터와
  무관하다; 그러지 않으면 부작용은 콜백이 터치된 샘플로 하는 일에 있다. 어느 답이든
  현재 가설이 하나도 없는 것에 대한 한 번의 실행짜리 이분 탐색이다.
- **인터프리터 경로에서의 유지 시간.** [H] `FOR=10`과 `FOR=90`은 *네이티브* 경로에서
  샘플링된 아홉 프레임 모두에서 바이트 단위로 동일한 이미지를 냈다
  [H: log/source account: `docs/kb/port/input-save-audio.md`, TOUCH39; receipt provenance unresolved]. ROM 자체의 `func_020e9314`가 공개를
  넘겨받은 뒤로 재측정되지 않았다; 인터프리터 경로에서 그 쌍을 반복하면 결판난다.

## 실행 목록

| 실행 | 무엇인가 |
|---|---|
| `scratchpad/cycle40/runs/tap-T41pd` | 들여다보기: 프레임 8,705에서의 링, `tpState`, `TP_POINT`, exit 100, 277 s |
| `scratchpad/cycle40/runs/tap-T41h` | 24,600, 핸들러 전의 샘플, 27,000에서 exit 100, 867 s |
| `scratchpad/cycle40/runs/tap-T41i` | 24,700, 핸들러 전의 샘플: `tap-24700`에 대해 평균 ncc 0.9986 |
| `scratchpad/cycle40/runs/tap-T42b` | 24,600, `ACWW_TP_LATE=1`, 27,000에서 exit 100, 791 s |
| `scratchpad/cycle40/runs/tap-T42c` | 24,700, `ACWW_TP_LATE=1`, 27,000에서 exit 100, 763 s |
| `scratchpad/oracle/tap-window`, `scratchpad/oracle/tap-24700` | 두 오라클 조건, 둘 다 비교 대상으로 읽힌다 |

## 관련 문서

- `../systems/input-and-touch.md` -- 시스템 페이지로서의 파이프라인
- `touch-calibration.md` -- 좌표, 그리고 1픽셀 왕복
- `two-tap-town-recipe.md` -- 위의 모든 조건이 변형인 레시피
- `../audits/hardware-services.md` -- 수정 P1, 조건 3의 결과로 닫힘
