# 두 번 탭 마을 레시피
<!-- source: wiki/experiments/two-tap-town-recipe.md -->

**상태: 실행됨, 영수증 있음.** 이것은 게임을 타이틀 화면에서 마을 회관 안의 대화까지
진행시키는 레시피이며, 택시, 두 개의 키보드, 마을, 하늘에 관한 모든 관측은 이 레시피
아래에서 얻어진다.

## 목적

스크립트된 패드 펄스와 네 번의 예약된 스타일러스 접촉으로 마을이 보일 만큼 게임을
진행시켜, 포트와 원본을 48,000 프레임에 걸쳐 비교할 수 있게 한다.

**왜 한 번이 아니라 두 번 탭인가.** 한 번 탭 레시피에서는 ROM 자체의 키보드 로직도 이름을
확정하지 않는다 -- 인터프리터 실행과 네이티브 실행이 9 프레임 중 9 프레임 일치했다 -- 즉
그 경로에서 포트는 결코 틀리지 않았고, 틀린 것은 레시피였다
[E: `docs/log/cycle40-keyboard-gate-probe.md` H4 RESULT and TAP40;
`scratchpad/cycle40/runs/tap-native`, `tap-interp`]. 첫 번째 탭은 키보드를 패드 모드에서
스타일러스 모드로 전환하고, 그에 반응할 상태는 눌림 에지가 사라진 다음 프레임부터만
실행된다; 스타일러스 모드 창 안의 두 번째 탭이 확인 버튼이 볼 수 있는 것이다
[E: `port/shim/input/touch.c`].

**왜 탭이 멈춰야 하는가.** 탭을 반복하면 예/아니오 메뉴가 유지되어 대화가 정체되는데,
대화 중의 접촉은 대화를 진행시키지 않기 때문이다. `ACWW_TOUCH_REPEAT=2`가 스크립트된
A 펄스에게 나머지를 맡길 수 있게 하는 설정이다 [E: `docs/log/cycle40-keyboard-gate-probe.md` TAP40, MENU40,
OVL40; `scratchpad/cycle40/runs/tap-D55b`].

## 레시피

    python -B scratchpad/cycle40/run_town.py <name> \
      ACWW_INTERP=1 ACWW_INTERP_STEPS=4000000000 \
      ACWW_TOUCH_AT=6900 ACWW_TOUCH_EVERY=60 ACWW_TOUCH_REPEAT=2 \
      ACWW_TOUCH2_X=221 ACWW_TOUCH2_Y=181 ACWW_TOUCH2_AT=24700 ACWW_TOUCH2_FOR=10 \
      ACWW_TOUCH2_EVERY=60 ACWW_TOUCH2_REPEAT=2 \
      ACWW_STOP_FRAME=48000 ACWW_SHOT_AFTER=6000 ACWW_SHOT_EVERY=1500 ACWW_PAD_SAMPLE=0

[E: `docs/kb/hybrid/recipes.md` section 3; `docs/state/port-frontier.md`, verified-at
`6ca48706`].

나머지는 스크립트 자체의 기본값이 공급한다: 커스텀 START 패드 페이즈 -- 프레임 300에서
1차 마스크 9, `FOR` 10, `EVERY` 30; 1,800에서 페이즈 2 마스크 8, `RELEASE_FOR` 60; 2,400에서
페이즈 3 마스크 1, `EVERY` 600 -- 그리고 `ACWW_RTC_DATE=20050615`, `ACWW_RTC_TIME=100000`,
`ACWW_NOPACE=1`, `ACWW_TRAMP_CONTINUE=1`, `ACWW_ASSERT_CONTINUE=1`, 그리고 첫 접촉
`ACWW_TOUCH_X=221 ACWW_TOUCH_Y=181 ACWW_TOUCH_FOR=10`. 또한 오라클, 세이브, 탐색,
키보드 프로브 변수를 해제하여 오래된 export가 새어 들어오지 못하게 한다
[E: `scratchpad/cycle40/run_town.py`, `BASE`; `docs/kb/hybrid/recipes.md` section 3].

`ACWW_INTERP_STEPS`는 더 이상 필요하지 않다: 기본값은 0으로 무제한을 뜻하며, 게임 실행은
대신 `ACWW_STOP_FRAME`으로 제한된다 [E: `docs/log/cycle40-keyboard-gate-probe.md` LONG41,
`scratchpad/cycle40/runs/tap-D58`, which stopped at ~61,000 frames with `STOP status=STEP
BUDGET`].

오라클 조건은 패드 페이즈 소유권 규칙과 터치 창 규칙을 포함해 이 변수들 하나하나를
그대로 반영하며, `observer.lua`가 두 계약을 매 프레임 강제한다
[O: `port/tools/oracle/README.md`; `docs/log/cycle40-keyboard-gate-probe.md` ORACLE41].

## 예상 관측

| 프레임 | 화면에 보이는 것 |
|---|---|
| 4,500..7,500 | 플레이어 이름 키보드가 있는 택시 내부 |
| ~7,500 | 플레이어 이름 확정 |
| 9,000..13,500 | 주행 구간; **위 화면은 포트와 원본 모두에서 검은색**이므로 이는 게임의 동작이지 포트 결함이 아니다 [O: `scratchpad/oracle/tap-fullpad/compare-vs-tap-D56.txt`, ncc-top 1.0000 at 9000..13500] |
| 15,000..24,000 | 대화, 그 다음 마을 이름 키보드 |
| ~24,700 | 포트와 원본 모두에서 마을 이름 확정 (24,600은 포트에서만 확정된다 -- ORACLE42) |
| 37,500 | 마을 회관 앞의 플레이어; 오버레이 5, 36, 54, 120, 117 로드됨 |
| 37,800 | 어파인 배경이 그려진 뒤 파란 하늘 위의 구름 [E: `scratchpad/cycle40/runs/tap-D57`, SKY40] |
| 39,000 | 전환 장면 |
| 40,500..48,000 | 마을 회관 내부, 펠리와 대화 중, 화면에 선택지 프롬프트 |

[E: `docs/log/cycle40-keyboard-gate-probe.md` TOWN40, SKY40;
`scratchpad/cycle40/runs/tap-D56`].

종료점: 48,000 프레임, 자식 종료 코드 100, 폴트 없음, STOP 없음, HUNG 없음, 페이싱 없이
초당 약 59 프레임, 811초, 스크린샷 31장, 59,808줄의 로그
[E: `scratchpad/cycle40/runs/tap-D56/receipt.json`, `exit 100`, `seconds 811.1`].

## 이 관측을 만들어 낸 실행

- `scratchpad/cycle40/runs/tap-D56` -- TOWN40이 보고하는 진단 실행, 48,000 프레임
  [E: its `receipt.json` carries `diagnostic: true`].
- `scratchpad/cycle40/runs/tap-D57` -- 어파인 배경을 그린 동일 실행 (SKY40).
- `scratchpad/cycle40/runs/town-R1` -- **영수증이 있는 실행**이며, 인터프리터 경로의 첫
  영수증 실행: 런처 종료 코드 0, 48,000에서 자식 종료 코드 100, 801초, 스크린샷 29장, 폴트
  마커 없음 [E: `docs/log/cycle40-keyboard-gate-probe.md` RECEIPT41, commit `6ca48706`].
- `scratchpad/cycle40/runs/tap-D59` -- 90,000 프레임; 펠리가 60,000에서 작별 인사를 하고 A
  펄스가 90,000까지 다시 그녀에게 말을 건다. 이 레시피로는 마을 회관 밖으로 나갈 수 없다
  [E: LONG41].
- `scratchpad/oracle/tap-fullpad` -- 오라클 조건과 그 비교 표.

**영수증과 진단은 같은 주장이 아니다.** 영수증은 READY 파이프라인 아티팩트에 대해
`port/tools/run.py --receipt`를 통해 실행하고 봉인된 로그를 그 옆에 복사·해시한 실행이다;
진단은 직접 `acww.exe`를 띄운 것이다. 어느 쪽인지, 그리고 런처, 아티팩트 출처, 경로,
종료점을 말해야 한다 (B1, B8, B32)
[E: `docs/kb/hybrid/recipes.md` section 5].

## 비교가 말해 주는 것

오프셋 0에서 오라클과 비교한 전체 프레임 정규화 상호상관
[O: `scratchpad/oracle/tap-fullpad/compare-vs-tap-D56.txt`]:

| 프레임 | ncc | ncc-top | 해석 |
|---|---|---|---|
| 6,000..24,000 | 0.9920..0.9959 | 0.9249..1.0000 | 같은 화면, 단계마다 일치 |
| 25,500..36,000 | 0.6957..0.7046 | 0.0000 | 갈라짐 |
| 39,000 | 0.0000 | 0.0000 | 한쪽에서만 전환 장면 |
| 40,500..48,000 | 0.6661..0.6761 | 0.0000 | 여전히 갈라짐 |

29 프레임 비교, RGB 정확 일치 0, 평균 ncc 0.8008 [O: same]. 두 쪽은 `TOUCH2` 창 안인
25,500에서 갈라진다: 포트의 두 탭은 마을 이름을 확정하지만 원본의 동일한 탭은 그러지
않으며, 원본은 48,000까지 마을 이름 키보드에 머문다
[O: `docs/log/cycle40-keyboard-gate-probe.md` ORACLE41]. **결론 (ORACLE42): 키보드에 관해
어느 쪽도 틀리지 않았다; 틀린 것은 레시피였다.** 24,600은 KEYS3 A 누름 프레임(2400 + 37 x 600)이고
원본의 스타일러스 샘플은 포트보다 1~2 프레임 늦게 도착하므로, 누름과 탭의 순서가 두 쪽에서
다르게 잡힌다. `ACWW_TOUCH2_AT=24700`으로 하면 양쪽 모두 확정하고 일치한다 -- 24,000..27,000의
11 프레임에서 평균 ncc 0.9955, 위 화면 1.0000
[S: `docs/log/cycle40-keyboard-gate-probe.md` ORACLE42; E: `tap-D62`;
O: `scratchpad/oracle/tap-24700`]. **따라서 공식 레시피는 24,700을 사용하며**, 위의 표는
기록을 위해 남겨 둔 24,600 실행이다. 오라클은 아직 마을을 보여 주지 못하므로, 하늘과
마을 회관은 아직 점수가 매겨지지 않았다.

## 반증 조건

- 폴트 마커, STOP 줄, 또는 `unimplemented:` 줄을 가진 채 48,000에 도달하는 실행.
- 탭이 도착하지 않는 것: 로그에 `acww touch: DOWN x=221 y=181`이 네 번(6,900과 6,960에서
  두 번의 접촉, 24,700과 24,760에서 두 번) 그리고 짝이 되는 `up` 줄이 있어야 한다. 세어야
  하며, 가정하지 않는다 [E: `scratchpad/cycle40/runs/tap-D60/tap-D60-run.log`, 9 `acww touch:`
  lines].
- 프레임 수나 벽시계 시간을 결과로 읽는 것 (B12). 종료점, 정확한 실패 정체, 그리고
  이미지로 판단한다.
- 트리를 git 기준으로만 동결하는 것: 파이프라인 스냅샷은 추적되지 않는 파일도 포함하며,
  한 빌드는 빌드 도중 운영자의 새 파일이 나타나 게시 시점에 거부되었다 (S10)
  [E: `docs/kb/hybrid/recipes.md` section 8].

## 관련 문서

- `off-recipe.md` -- 대조 실행.
- `touch-calibration.md` -- 이 레시피가 부딪히는 1픽셀, 2프레임 차이와, ORACLE42가 그것을
  어떻게 결론지었는가.
- `../systems/input-and-touch.md`, `../systems/time-and-rtc.md`

## 레퍼런스 대비 결과 (ORACLE43)

`ACWW_TOUCH2_AT=24700`으로 DeSmuME 레퍼런스는 같은 경로를 따른다: 37,500에서 마을,
40,500부터 마을 회관, 27000..48000의 15 프레임에서 평균 ncc 0.8967, 마을 회관 프레임은
0.98-0.998이며 위 화면은 동일하다(마을 회관 안에서는 양쪽 모두 검은색)
[O: `scratchpad/oracle/tap-town`] [E: `tap-D63`]. 두 전환 프레임(39,000과 46,500)은 페이드의
서로 반대편에 떨어진다. 37,500에서 원본의 하늘은 지평선을 향해 원근 스케일링되어 있고
포트의 하늘은 평평하다 [H: the HBlank handler `func_01ffcc30` updates the affine
parameters per scanline; capture BG3 P*/X/Y per line and compare `tap-D63` 37,500 again].

갱신 (SKY41): 스캔라인별 레지스터 캡처(HBlank 콜백이 BG3의 아핀 파라미터와
BLDCNT/BLDALPHA를 줄마다 다시 쓴다)를 적용하면 37,500에서 포트의 하늘은 원본처럼
지평선을 향해 평평해지고 배경(backdrop)으로 페이드된다 [E: `tap-D71`]
[S: docs/log/cycle40-keyboard-gate-probe.md SKY41].
