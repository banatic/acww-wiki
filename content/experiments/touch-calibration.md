# 터치 보정: 탭했을 때 게임이 보는 것
<!-- source: wiki/experiments/touch-calibration.md -->

**상태: 실행됨.** 아래의 측정은 이 프로젝트에서 포트와 원본 사이의 차이 중 가장 잘
특성화된 것이다.

## 목적

예약된 스타일러스 접촉은 포트의 주된 입력 도구이며, 오라클도 이를 그대로 반영한다. 그러나
"에뮬레이터의 스타일러스가 움직였다"와 "게임이 터치를 보았다"는 서로 다른 주장이며, 패널은
에뮬레이션되지만 게임은 접촉을 전혀 보지 못하는 레퍼런스는 좋은 레퍼런스와 겉보기에 똑같을
것이다. 이 실험은 레시피가 요청한 정확한 프레임에서, 원본에서, *ROM 자체가 공개하는 터치
포인트*가 무엇을 담고 있는지를 묻는다.

## 레시피

오라클 쪽, 프로브 모드:

    python port/tools/oracle/oracle.py --touch-probe 1200 \
      --touch-x 221 --touch-y 181 --touch-at 1000 --touch-for 10 \
      --touch-every 60 --touch-repeat 2

프로브 모드는 터치 계약의 강제를 멈추고, 대신 스타일러스가 눌려 있는 동안 프레임마다,
그리고 상태 변경마다 `{"kind":"stylus"}` 원장(ledger) 행을 하나씩 내보내며, ROM 자체의
`TP_POINT`를 `0x021fbde8`에서, 게이트 워드를 `0x027fffa8`에서 읽는다
[O: `port/tools/oracle/README.md`, "...and the tap reaches the GAME"].

포트 쪽은 마을 레시피의 환경(`two-tap-town-recipe.md`)에서 같은 창을 관찰하며, 포트의
`acww touch:` 줄을 읽는다. 이 줄은 변경 시에만 출력되므로 개수 제한이 없다
[H: host-source account from `port/shim/input/touch.c`; verify with a retained scripted run and frame using this page's recipe].

## 예상 관측

`AT=1000 FOR=10 EVERY=60 REPEAT=2`, `X=221 Y=181`에서 레시피가 답하는 세 필드 질문:

| 무비 프레임 | 무비 스타일러스 | `0x021fbde8` x, y, touch, validity | `0x027fffa8` |
|---|---|---|---|
| 999 | up | 행 없음 (상태 변경 없음) | `2c00` |
| 1000..1009 | down 221,181 | **222, 182, 1, 0** | `2c00` |
| 1010 | up | 222, 182, 1, 0 -- 1 프레임 지연 | `2c00` |
| 1060..1061 | down 221,181 | 255, 255, 0, 0 -- 아직 샘플링되지 않음 | `2c00` |
| 1062.. | down 221,181 | **222, 182, 1, 0** | `2c00` |

[O: `port/tools/oracle/README.md`, 1,200-frame probe run].

세 가지 발견 사항이며, 모두 중요하다:

1. **접촉이 게임에 도달한다.** ROM 자체의 터치 워드가 레시피가 요청한 좌표에서
   `touch = 1`이 된다.
2. **좌표가 1픽셀 크게 돌아온다**, 221,181 입력에 222,182 출력. 이것은 포트가 의도적으로
   건너뛰는 디지타이저 왕복이다: 에뮬레이터는 화면 픽셀을 원시 ADC 카운트로 변환하고
   `TP_GetCalibratedPoint`가 이를 다시 되돌리는 반면, 포트는 그 변환의 출력 지점에 주입한다.
   따라서 두 생산자는 구조상 어떤 예약된 탭에서든 최대 1픽셀 차이가 난다 [O: same; E: `port/shim/input/touch.c`].
3. **게임은 접촉을 1~2 프레임 늦게 보고 1 프레임 더 길게 유지한다**, ARM7의 자동 샘플링
   링이 ARM9가 읽기 한 프레임 전에 채워지기 때문이다. `FOR=10` 접촉은 게임 RAM에서 약 2
   프레임 밀린 대략 10 프레임의 `touch = 1`이다. 포트의 NATIVE 경로는 정확한 프레임에
   공개하며, 그것이 차이였다; 인터프리터 경로에서는 이제 포트가 그 지연과 순서를
   재현한다 [E: `scratchpad/cycle40/runs/tap-T41pd`,
   contact 8,700 -> `TP_POINT` 8,701; `touch-latency.md`] [O: same].

게이트 워드는 모든 프레임에서 `2c00` -- 비트 15 클리어 -- 로 읽히며, 이는 포트의
`hostinput.c`와 `frameswap.c`가 세워 두는 값과 같으므로, 게이트가 열려 있다는 데 원본은
포트와 동의한다 [O: same; E: `port/platform/hostinput.c`].

## 뒷받침하는 측정들과 그 음성 대조군

이 모든 것이 의미를 갖기 전에 무비 형식을 먼저 확립해야 했다. `.dsm` 프레임 줄은
`|<commands>|<13 pad chars><xxx> <yyy> <t> <mmm>|` 이며 **터치 그룹 앞에 별도의 파이프가
없다**; 네 필드는 아래 화면의 픽셀 열, 픽셀 행, 다운 플래그, 그리고 마이크 샘플이다
[O: `port/tools/oracle/README.md`, "The .dsm touch columns"]. 동작하는 무비의 필드 하나를
고쳐 쓰고 재생하는 방식으로 두 가지 대조를 실행했다:

- **`t`를 0으로 강제하고 좌표는 그대로 둠**: 접촉이 전혀 없고 스타일러스 행이 0개. 따라서
  세 번째 필드가 플래그이며, "0이 아닌 좌표가 터치를 뜻한다"는 것이 아니다.
- **터치 그룹 앞에 `|`를 하나 추가 삽입**: 동일한 결과, 28행 전부 변화 없음. 따라서
  DeSmuME의 십진 리더는 숫자가 아닌 구분자를 건너뛴다; 그래도 도구는 파이프 없는 형태를
  쓰는데, DeSmuME 자체의 덤퍼가 만들어 내는 것이 그 형태이기 때문이다.

[O: same; the retained control script is `scratchpad/oracle/tool-updates/negctl.py`, throwaway].

패드 열 매핑도 읽는 대신 같은 방식으로 측정했다: 13개 열 `RLDUTSBAYXWEG`의 뻔한 해석은
틀렸다 -- **열 `T`가 SELECT이고 열 `S`가 START이다** -- 첫 키 입력 실행에서 입력 계약이
이를 잡아냈고(예상 마스크 9 = A|START, 관측 5 = A|SELECT), 그 뒤 KEYINPUT 비트 10개
전부를 `--keys 0x3ff --keys-at 1 --keys-for 2 --keys-every 0`으로 한 번의 실행에서
검증했다 [O: same].

창 규칙 자체는 두 번의 접촉이 있는 300 프레임 프로브로 검증했다:
프레임 100..109와 160..169에서 221,181, 220에서는 `REPEAT=2`가 두 접촉 후 멈추므로 아무것도
없음, 그리고 두 번째 접촉으로 250..254에서 40,20 -- 관측된 모든 행이 예상 행과 같았고,
에지는 정확한 프레임에 있었으며, 두 접촉은 좌표로 구별되었다
[O: same].

## 실행들

- `TP_POINT` 프로브: `port/tools/oracle/README.md`의 표, 1,200 프레임.
- `scratchpad/oracle/tap-220`과 `scratchpad/oracle/tap-window` -- 마을 레시피의 패드 페이즈
  아래에서 실행한 두 번의 27,000 프레임 오라클 실행으로, 둘 다 스타일러스를 무비 40 프레임
  동안 유지했고, 각각 32장과 51장의 스크린샷, 둘 다 프레임 27,000에서 COMPLETE
  [O: their `manifest.json` and `.out` files]. 둘 다 아직 포트 조건과 비교되지 않았다.
- `scratchpad/cycle40/runs/tap-D60` -- 24,000부터 60 프레임마다 스크린샷을 찍은 221,181의
  포트 실행, 27,000에서 종료 코드 100, 접촉 네 번 기록됨
  [E: its `receipt.json` and `tap-D60-run.log`].
- `scratchpad/cycle40/runs/tap-D61` -- **1픽셀 테스트**: 접촉을 원본의 게임이 실제로 보는
  좌표인 `ACWW_TOUCH_X=222 ACWW_TOUCH_Y=182`로 옮긴 동일 레시피. 27,000에서 종료 코드 100,
  로그에는 네 접촉 모두 `acww touch: DOWN x=222 y=182`가 찍힌다
  [E: its `receipt.json` and `tap-D61-run.log`]. ORACLE42에서 `tap-220`과 비교했다 --
  아래의 결과 절을 볼 것 [S: `docs/log/cycle40-keyboard-gate-probe.md` ORACLE42].

## 반증 조건

- 접촉 창 내내 `0x021fbde8`가 255, 255, 0, 0에 머무는 프로브 실행: 탭이 에뮬레이터의 입력
  계층에는 도달하지만 게임에는 도달하지 않으며, 그 위에 세운 모든 비교는 무효이다.
- 게이트 워드가 비트 15가 세팅된 값으로 읽히는 것. 어느 쪽에서든 터치가 죽는다면, 다른
  무엇보다 먼저 그 비트를 확인한다 [H: host-source account from `port/shim/input/touch.c`; verify with a retained scripted run and frame using this page's recipe].
- (실행됨, 그리고 실제로 이렇게 되었다.) `tap-D61` 대 `tap-220` 비교는 여전히 25,500에서
  갈라졌고, 이는 1픽셀을 배제하고 1~2 프레임 지연을 설명으로 남겼다 -- 탭을 A 누름
  프레임에서 옮겨 확인했다. 아래의 결과 절을 볼 것.

도구에 관한 주의 사항 하나, 이 페이지 초안 당시에는 "설명되지 않음"으로 기록되었고 지금은
부분적으로 설명됨: 그 Lua 빌드의 `memory.readword`는 비터치 행에서 255를 반환했고, 이는
0xffff를 쓰는 포트 쪽 전사(transcription)에 비추어 "하위 8비트만 전달한다"로 읽혔다.
TOUCH41은 대신 ROM을 읽었다 -- `mov r1,#0xff`와 `0x020e941c`의 `strh` -- 따라서 ROM 자체의
비터치 값은 **0x00ff**이며, 프로브의 255는 잘린 값이 아니라 올바른 답이다
[S: `func_020e9314`, autoload_2, disassembly `0x020e9314`..`0x020e9470`;
`docs/log/cycle40-keyboard-gate-probe.md` TOUCH41]. 이로써 그 행들을 의심할 이유는 사라졌다;
그 Lua 빌드의 `readword`가 일반적으로 16비트 폭인지는 시험되지 않았으며 여기서는 필요하지도
않은데, 표의 모든 값이 256 미만이기 때문이다
[O: `port/tools/oracle/README.md`; M1].

**프레임 매핑, 명시:** 에뮬레이터 프레임 N은 포트 프레임 N, 오프셋 0으로 간주한다. `--offset`은
무비의 탭을 누름 및 스크린샷과 함께 이동시키므로 이 가정은 단일 손잡이(knob)이지만, 도구
전체의 증명되지 않은 가정이다 -- 그리고 키보다 터치에서 더 중요한데, 일찍 도착한 누름은
보통 아직 기다리고 있는 메뉴에 흡수되지만 버튼의 히트 창 밖에 떨어진 탭은 그냥 일어나지
않기 때문이다
[O: `port/tools/oracle/README.md`, "Frame mapping"; `docs/state/open-questions.md` item (c)].


## 결과 (ORACLE42, 이 페이지 초안 이후)

1픽셀 테스트는 음성이다: 222,182에서 접촉한 포트는 여전히 마을 이름을 확정하고(`tap-D61`,
25,200부터 위 화면 검정 = 주행 구간), 220,180에서 접촉한 원본은 여전히 확정하지 않는다
(`scratchpad/oracle/tap-220`, 27,000까지 키보드) [E: `tap-D61`]
[O: `scratchpad/oracle/tap-220`]. 원인은 프레임이다: 24,600은 KEYS3 A 누름 프레임(2400 + 37 x 600)인
반면 8,700은 아니며, 원본의 스타일러스 샘플은 포트보다 1-2 프레임 늦게 게임에 도달하므로,
누름과 탭의 순서가 두 쪽에서 다르게 잡힌다
[S: docs/log/cycle40-keyboard-gate-probe.md ORACLE42]. `ACWW_TOUCH2_AT=24700`으로 하면 양쪽
모두 확정하고 일치한다: 24000..27000의 11 프레임에서 평균 ncc 0.9955, 위 화면 1.0000
[E: `tap-D62`] [O: `scratchpad/oracle/tap-24700`]. 공식 레시피는 24,700을 사용한다.
**그 뒤 결론남 (TOUCH41, TOUCH42):** 지연은 회피되지 않고 모델링된다. ROM 자체의
`func_020e9314`가 인터프리터 경로에서 실행되고 포트는 ROM의 VBlank 핸들러 뒤에 ARM7의
링을 채운다; 그러면 24,600 레시피는 원본과 정확히 같이 키보드에 머무른다
[E: `scratchpad/cycle40/runs/tap-T42b`] [O: `scratchpad/oracle/tap-window`]. 타이밍
측정은 이제 자체 페이지를 가진다: `touch-latency.md`.

## 관련 문서

- `../systems/input-and-touch.md`
- `touch-latency.md` -- 같은 파이프라인의 타이밍 절반
- `two-tap-town-recipe.md`, `off-recipe.md`
