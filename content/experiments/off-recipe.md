# OFF 레시피
<!-- source: wiki/experiments/off-recipe.md -->

**상태: 실행됨, 여러 번.** 이것은 다른 모든 측정을 읽을 때 기준이 되는 대조 실행이다.

## 목적

스타일러스를 비활성화한 채 게임을 프레임 9,000까지 실행하고, 스크린샷 31장 전부를
보관된 레퍼런스와 SHA-256으로 비교하여, 포트에 가한 변경이 아무것도 움직이지 **않았음**을
확립한다. 31장 중 31장이 같으면 통과이다 [E: `docs/kb/hybrid/recipes.md` section 2].

**이름은 함정이며 B1이 그 이유다.** "OFF"는 `ACWW_TOUCH`가 꺼져 있음을 가리킨다. 그 외에는
**키 입력 START** 레시피로, `ACWW_KEYS=9`(A와 START)가 프레임 300부터 펄스를 낸다
[O: `port/tools/oracle/README.md`, "THE RECIPE NAMED OFF IS NOT AN UNKEYED RUN"]. 정말로
입력이 없는 무비를 오라클 쪽에서 한 번 시도한 적이 있다: 입력이 없으면 원본은 타이틀
화면을 영영 벗어나지 않는 반면 포트는 택시 인트로 깊숙이 들어가 있어, 모든 프레임의
정규화 상호상관(normalised cross-correlation)이 0.10 근처로 나왔고, 그 결과로 나온 31개
불일치 표는 포트에 관해 아무것도 말해 주지 않았다 [O: same].

## 레시피

먼저 재링크를 수행하는 반복 스크립트를 통해 실행한다:

    sh scratchpad/cycle40/iterate.sh <name> [KEY=VAL ...]

이 스크립트는 순서대로, 실행 채널 컨트롤러를 통한 링크(약 3분)를 수행한 뒤, 다음을 실행한다:

    python -B scratchpad/cycle40/run_direct.py off-<name> \
      ACWW_INTERP=1 ACWW_TOUCH_ENABLE=0 \
      ACWW_STOP_FRAME=9000 ACWW_SHOT_AFTER=4500

그 다음 31장의 BMP 전부를 `scratchpad/cycle39/execution39-touch39-005/off`와
SHA-256으로 비교하고, 로그에서 BOOT 줄, 정지 줄, 폴트, `unimplemented`, 그리고 STOP 줄을
grep한다
[E: `scratchpad/cycle40/iterate.sh`; `docs/kb/hybrid/recipes.md` section 2].

패드 페이즈는 스크립트 자체의 기본값에서 오며, 커스텀 START 레시피이다:
`ACWW_KEYS=9 ACWW_KEYS_AT=300 ACWW_KEYS_FOR=10 ACWW_KEYS_EVERY=30`
[O: `port/tools/oracle/README.md`; cycle39 log].

같은 레시피의 오라클 조건:

    python port/tools/oracle/oracle.py --frames 4500,4650,...,9000 --out scratchpad/oracle/off
    python port/tools/oracle/compare.py scratchpad/oracle/off scratchpad/cycle40/runs/off-<name>

[E: `docs/kb/hybrid/recipes.md` section 6].

## 예상 관측

| 항목 | 예상 |
|---|---|
| 프레임 | 9,000, 자식 종료 코드 100, 런처 0 |
| 스크린샷 | 프레임 4,500부터 BMP 31장 |
| 통과 | `equal 31 differ 0` |
| 로그 | `acww touch: up` 줄이 하나, 그 이상은 없음 -- 변경 시에만 출력하는 도구가 `last = -1`에서 시작하므로 모든 실행은 정확히 한 번의 초기 "up"을 출력한다; ON 실행은 세 개다 [E: `docs/kb/port/input-save-audio.md`, TOUCH39] |
| 소요 시간 | 링크가 워밍업된 뒤에는 한 턴에 약 90초 [E: `docs/kb/hybrid/recipes.md` section 2] |

## 이 관측을 만들어 낸 실행

레퍼런스는 `scratchpad/cycle39/execution39-touch39-005/off`이다
[E: `docs/kb/hybrid/recipes.md` section 2]. REG40b와 REG40c의 거부 목록(deny list) 이분 탐색
전체가 이 루프 위에서 구축되었다 [E: `docs/log/cycle40-keyboard-gate-probe.md` REG40b, REG40c]. 오라클
쪽은 `scratchpad/oracle/off`이며, 그 옆에 `compare-off.json`과 `diff-off/`가 있다
[O: `scratchpad/oracle/off`].

## 반증 조건

- 포트에 의도적인 변경 없이 BMP가 하나라도 달라지는 것. 이는 노이즈가 아니라 변경의
  결함으로 읽어야 한다: 레퍼런스는 유사도 점수가 아니라 바이트 비교이다.
- `acww touch: up` 줄 없이 끝나는 실행. 이는 도구 자체가 조용해졌다는 뜻이며 -- 측정
  대상이 조용해진 것과 구별할 수 없다
  [E: `port/platform/hostinput.c`'s announcement rationale].
- 이 대조 실행 전에 ON 조건을 실행하는 것 (M15). 31 프레임 비교가 있어야 ON 쪽의
  차이가 의미를 갖는다.

## 관련 문서

- `two-tap-town-recipe.md` -- 이 레시피가 대조하는 ON 레시피.
- `../systems/input-and-touch.md`
