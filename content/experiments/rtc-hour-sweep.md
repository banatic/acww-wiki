# RTC 시각 스윕
<!-- source: wiki/experiments/rtc-hour-sweep.md -->

**상태: 설계만 됨, 아직 미실행.**

## 목적

이 프로젝트의 지금까지 모든 측정은 시계를 2005-06-15 10:00:00에 고정하므로, 게임의
낮/밤 조명은 한 지점 이상에서 검증된 적이 없다
[E: `port/shim/os/rtcclock.c`; `scratchpad/cycle40/runs/tap-D56`]. 조명이 보간하는 블렌드
가중치는 `0x021dc758`의 분(minute) 바이트를 4096/60으로 스케일링한 값이며, 이를 호스트
스택 쓰레기 값에서 읽었던 적이 있어 이 포트의 모든 스크린샷 비교에 20-26%의 픽셀 노이즈
바닥이 깔린 적이 있다 [H: source/log account from `port/shim/os/rtcclock.c`; verify with a retained run using this page's recipe]. 이 실험은 두 가지를 한꺼번에 묻는다:
시각이 씬을 눈에 띄게 바꾸는가, 그리고 포트와 원본이 같은 방식으로 바뀌는가.

또한 더 작은 질문 하나를 결론짓는다. `ACWW_RTC_TIME=000000`은 예전에는 "기본값을
사용한다"는 뜻이었는데, 포트의 옛 파서가 미설정, 파싱 불가, 0을 하나의 답으로 합쳤기
때문이다 -- 그래서 자정 프로브는 10:00 프로브와 바이트 단위로 동일하게 돌아왔고, 이는
답처럼 보이는 측정이다 [H: host-source account from `port/shim/os/rtcclock.c`; verify with a retained scripted run and frame using this page's recipe]. 현재 파서는 이들을 구별한다; 이
실행은 실제로 그러한지 확인하는 것이다.

## 레시피

네 개의 조건, 시각당 하나씩, 각각 `ACWW_RTC_TIME`만 바꾼 마을 레시피이다. 10:00 조건을
먼저 실행한다: 이는 `scratchpad/cycle40/runs/tap-D56`을 프레임 단위로 재현해야 하며,
그렇지 않으면 스윕은 시각이 아니라 빌드를 측정하는 것이다 (M15).

    for T in 100000 000000 060000 200000; do
      python -B scratchpad/cycle40/run_town.py rtc-$T \
        ACWW_RTC_DATE=20050615 ACWW_RTC_TIME=$T \
        ACWW_INTERP=1 \
        ACWW_TOUCH_AT=6900 ACWW_TOUCH_EVERY=60 ACWW_TOUCH_REPEAT=2 \
        ACWW_TOUCH2_X=221 ACWW_TOUCH2_Y=181 ACWW_TOUCH2_AT=24600 ACWW_TOUCH2_FOR=10 \
        ACWW_TOUCH2_EVERY=60 ACWW_TOUCH2_REPEAT=2 \
        ACWW_STOP_FRAME=39000 ACWW_SHOT_AFTER=36000 ACWW_SHOT_EVERY=750 ACWW_PAD_SAMPLE=0
    done

정지를 48,000이 아닌 39,000으로 두는 이유는 37,500의 마을 외부가 조명을 살펴볼 만한
프레임이기 때문이다; 40,500 이후의 마을 회관 내부는 실내이다
[E: `docs/log/cycle40-keyboard-gate-probe.md` TOWN40].

오라클 조건, 시각당 하나씩 -- RTC는 생성된 무비의 `rtcStart` 줄에 고정되므로, 환경
변수가 아니라 플래그이다 [O: `port/tools/oracle/README.md`, "How the RTC
and the input recipe are enforced"]:

    python port/tools/oracle/oracle.py --frames 36000,36750,37500,38250,39000 \
      --rtc-start 2005-06-15T00:00:00Z \
      --touch-x 221 --touch-y 181 --touch-at 6900 --touch-for 10 \
      --touch-every 60 --touch-repeat 2 \
      --touch2-x 221 --touch2-y 181 --touch2-at 24600 --touch2-for 10 \
      --touch2-every 60 --touch2-repeat 2 \
      --out scratchpad/oracle/rtc-000000

    python port/tools/oracle/compare.py scratchpad/oracle/rtc-000000 \
      scratchpad/cycle40/runs/rtc-000000 --json scratchpad/oracle/rtc-000000.json

실행 전에 `oracle.py --help`에서 정확한 `rtcStart` 플래그 이름을 확인한다; README는
플래그가 아니라 필드를 문서화하고 있다.

**ORACLE42가 제거한 주의 사항.** 24,600 레시피에서 원본은 마을에 전혀 도달하지 못했다 --
25,500부터 48,000까지 마을 이름 키보드에 머물렀으므로, 모든 오라클 조건은 *키보드* 화면을
채점했을 것이다 [O: `docs/log/cycle40-keyboard-gate-probe.md` ORACLE41]. 이는 결론이 났다:
24,600의 탭은 KEYS3 A 누름 프레임에 떨어졌고 원본의 스타일러스 샘플은 1~2 프레임 늦게
도착하므로, `ACWW_TOUCH2_AT=24700`으로 하면 양쪽 모두 확정하고 일치한다
[S: `docs/log/cycle40-keyboard-gate-probe.md` ORACLE42; E: `tap-D62`;
O: `scratchpad/oracle/tap-24700`]. **위의 포트 조건과 오라클 조건 모두에서 24,700을 사용할
것**; 위에 적힌 명령은 여전히 24,600이라고 되어 있어 옛 주의 사항을 재현하게 된다.

## 예상 관측

| 조건 | 예상 |
|---|---|
| `ACWW_RTC_TIME=100000` | 36,000과 37,500에서 `tap-D56`과 바이트 단위로 동일 |
| `000000` | 자정: 부팅 줄이 `hour=0 min=0`으로 읽히고, 37,500의 마을 외부가 눈에 띄게 어둡다 |
| `060000` | 새벽 |
| `200000` | 밤 |

모든 로그에서 확인할 부팅 줄은 `acww rtc: fixed clock year+2000=5 month=6 day=f
week=3 hour=... min=0 sec=0`이다 -- 값은 16진수로 출력된다
[H: host-source account from `port/shim/os/rtcclock.c`; verify with a retained scripted run and frame using this page's recipe]. week 3은 수요일이며, 계산된 값이지 환경에서 가져온
값이 아니다.

반증 가능한 예측: 네 조건 모두 37,500에서 바이트 단위로 동일한 이미지를 만든다면,
오버라이드가 적용되지 않고 있거나(다른 무엇보다 먼저 부팅 줄을 확인할 것) 그 프레임의
씬이 낮/밤 블렌드를 사용하지 않는 것이다.

## 이 실험이 검증하는 가설의 반증 조건

- 네 개의 서로 다른 부팅 줄에 네 시각에 걸쳐 동일한 이미지: 블렌드 가중치는 렌더러에
  도달하지만 마을 외부는 이를 사용하지 않는다.
- 오버라이드 거부 줄 `acww rtc: ACWW_RTC_TIME rejected, keeping the default` -- 값이 범위
  밖이며, 그 조건은 당신이 생각하는 조건이 아니다.
- 10:00 조건이 `tap-D56`과 다른 것: 빌드가 움직였으며, 이것이 설명되기 전까지는 다른
  어떤 조건도 의미가 없다 (M1).

## 관련 문서

- `../systems/time-and-rtc.md`
- `two-tap-town-recipe.md`, `off-recipe.md`
