# RNG 결정성
<!-- source: wiki/experiments/rng-determinism.md -->

**상태: 설계만 됨, 아직 미실행.**

## 목적

포트는 ROM의 두 엔트로피 원천을 모두 고정한다: 틱은 0에서 시작해 프레임당 정확히 8,728
카운트씩 전진하고 [E: `port/platform/tick.c`] RTC는 고정된 시각이다
[E: `port/shim/os/rtcclock.c`]. 따라서 포트 실행은 자기 자신과 비트 단위로 동일*해야* 한다.
이것은 독립된 주장으로 확인된 적이 없다 -- 그 위에 세워진 모든 비교가 늘 가정만 해 왔다.

후반부가 흥미로운 쪽이다. 시계를 1초 옮겨도 아무것도 바뀌지 않는다면, 마을 회관으로
가는 경로의 어떤 것도 시계로 시드된 난수를 소비하지 않으며, 결정성은 자명하게 참이다.
무엇인가 바뀐다면 소비자를 찾은 것이다 -- 그리고 `src/matched`에서는 게임플레이 쪽
생성기가 전혀 발견되지 않았다 [S: absence; see `../systems/rng.md`].

## 레시피

마을 레시피(`two-tap-town-recipe.md`)의 세 조건, 명시된 부분만 다르며, 모두 하나의
빌드에서 실행한다.

**조건 A -- 기준선.** `ACWW_RTC_TIME=100000`, 6,000부터 1,500 프레임마다 스크린샷.

**조건 B -- 반복.** 바이트 단위로 같은 명령줄, 다른 출력 디렉터리.

**조건 C -- 1초 뒤.** `ACWW_RTC_TIME=100001`.

    for N in A B; do
      python -B scratchpad/cycle40/run_town.py rngdet-$N \
        ACWW_INTERP=1 ACWW_RTC_DATE=20050615 ACWW_RTC_TIME=100000 \
        ACWW_TOUCH_AT=6900 ACWW_TOUCH_EVERY=60 ACWW_TOUCH_REPEAT=2 \
        ACWW_TOUCH2_X=221 ACWW_TOUCH2_Y=181 ACWW_TOUCH2_AT=24600 ACWW_TOUCH2_FOR=10 \
        ACWW_TOUCH2_EVERY=60 ACWW_TOUCH2_REPEAT=2 \
        ACWW_STOP_FRAME=48000 ACWW_SHOT_AFTER=6000 ACWW_SHOT_EVERY=1500 ACWW_PAD_SAMPLE=0
    done

그 다음 `ACWW_RTC_TIME=100001`로 조건 C를 실행하고, 세 스크린샷 세트를 SHA-256으로
비교한다. 이는 `iterate.sh`가 OFF 레시피에 대해 이미 수행하는 것과 같은 비교이다
[E: `scratchpad/cycle40/iterate.sh`].

## 예상 관측

| 비교 | 예측 | 틀렸을 때의 의미 |
|---|---|---|
| A 대 B | 29 중 29 동일 | 포트가 결정적이지 않다; 무엇인가 호스트를 읽는다 -- 주소 공간 레이아웃, 벽시계, 또는 초기화되지 않은 버퍼로, 정확히 `rtcclock.c`가 제거하려고 쓰인 결함 부류이다 |
| A 대 C | 29 중 29 동일 | 이 경로의 어떤 것도 초 단위 해상도의 시계 난수를 소비하지 않는다; 고정된 시계는 조명 이외에는 아무 일도 하지 않는다 |
| A 대 C | 일부 프레임이 다름 | 소비자가 존재하며, 처음 달라지는 프레임이 대략 어디인지를 알려 준다 |

조건이 이미 있으므로 저렴한, 유용한 세 번째 비교: A와 B의 두 로그를 정규화하여 diff한다.
깨끗한 실행에서 예상되는 유일한 차이는 호스트 주소 공간 레이아웃 블록과 릴리스 줄이다 --
네이티브 경로에서 관측된 매칭 쌍의 모양이 그러했다 [E: `docs/kb/port/input-save-audio.md`, TOUCH39, the `FOR=10` versus `FOR=90` diff].

## 반증 조건

- A 대 B의 어떤 차이든. 비결정성을 결론짓기 전에 두 영수증의 `exe_sha256`이 같은지
  확인한다 -- 조건들은 하나의 빌드여야 한다 [E: receipts record it,
  `scratchpad/cycle40/runs/tap-D56/receipt.json`].
- 프레임 40,500 이후, 마을 회관 안에서만 나타나는 차이. 거기서는 스크립트된 A 펄스가
  펠리에게 반복해서 말을 걸며, 대화 선택이 난수의 가장 유력한 소비자이다
  [E: `scratchpad/cycle40/runs/tap-D59`, LONG41]; 이는 실험의 실패가 아니라 양성 결과이다.
- 동일함을 게임에 RNG가 없다는 증명으로 읽는 것. 그것은 이 경로가, 이 시계 해상도에서,
  난수로 분기하지 않는다는 것만을 증명한다.

## 관련 문서

- `../systems/rng.md`, `../systems/time-and-rtc.md`
- `two-tap-town-recipe.md`
