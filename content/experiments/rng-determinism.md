# RNG 결정성
<!-- source: wiki/experiments/rng-determinism.md -->

**상태:** 원래의 A/B/C 스크린샷 실험은 제안으로 남아 있다 [H: no A/B/C receipt is supplied here].
+아래의 후속 드로우 위치(draw-position) 조건들은 ORACLE47..49에서 측정되었다 [E: `scratchpad/oracle47/RECEIPTS.md`, `scratchpad/oracle49/RECEIPTS.md`; log: `docs/log/cycle41-gameplay.md` O47-4, O49-1..5].

## 목적

부팅 시드와 생성 시점의 스트림 위치를 분리한다: 시계 시드는
`minute | day<<8 | hour<<16 | second<<24`를 접으므로(fold), 1초를 바꾸면 시드 바이트 하나가
바뀌지만, 연도나 월만 바꾸면 이 접기는 바뀌지 않는다
[S: `src/matched/func_0209dbbc.c`; log: `docs/log/cycle41-gameplay.md` O46-1, O46-4].
그 소스 사실만으로는 프레임 전체의 동일성이나, 바뀐 모든 시드가 다른 마을을 준다는 것을
증명하지 못한다 [H: the A/B/C experiment below is not a retained result].
ORACLE46은 같은 시드 `0x000a0f00`을 원본의 동결 조건 유무에서 측정했다;
ORACLE47은 그 조건의 추가 드로우 소비가 프레임 10,000 이후에 있음을 찾아냈으며, 확정 시점까지
14개의 추가 드로우에 도달했다 [E: `scratchpad/oracle46/RECEIPTS.md`, `scratchpad/oracle47/RECEIPTS.md`;
log: `docs/log/cycle41-gameplay.md` O46-4, O47-3].

## 측정된 조건들: id, 레이아웃, 명단은 별개의 검사이다

| 조건 / 비교 | 측정 결과 | 등급과 출처 절 |
|---|---|---|
| ORACLE47 포트 확정 타이밍만 | `24700`은 `0xc66e`; `24907`과 `24908`은 `0x8365`; `24909`는 그 빌드에서 `0xe767` | [E: `scratchpad/oracle47/RECEIPTS.md`; log: `docs/log/cycle41-gameplay.md` O47-4] |
| ORACLE49 부팅 대조, 탭 없음 | 마을 `0xd391`; 4,617 워드 비교, 0개 상이 | [E: `scratchpad/oracle49/RECEIPTS.md`; log: `docs/log/cycle41-gameplay.md` O49-3] |
| ORACLE49 정방향: 포트 `ACWW_TOUCH2_AT=24908`, `ACWW_RTC_FREEZE_UNTIL=48000`; 원본 `--touch2-at 24700`, 조건 없음 | 마을 `0x8365`; 36 에이커 바이트와 열일곱 건물 셀 전부 동일; 프레임 48,000에서 2,057 맵 워드 중 떨어진 아이템 1개 상이 | [E: `scratchpad/oracle49/RECEIPTS.md`; log: `docs/log/cycle41-gameplay.md` O49-4] |
| ORACLE49 역방향: 원본 `24315`에 48000까지 동결; 포트 `24700` | 양쪽 모두 id 드로우 #2,667; 원본은 3,780에서, 포트는 3,782에서 레이아웃 버스트에 진입 | [E: `scratchpad/oracle49/RECEIPTS.md`; log: `docs/log/cycle41-gameplay.md` O49-2] |

새 게임 경로는 두 번 생성한다: 포트의 부팅 마을은 프레임 758에 있고, 그 뒤 맵이 리셋된
다음 실제 맵, 아이템 레이어, 명단이 프레임 36,135에 함께 쓰이는데, 이는 프레임 24,789의
id 드로우로부터 11,346 프레임 뒤이다 [E: `scratchpad/oracle49/RECEIPTS.md`;
log: `docs/log/cycle41-gameplay.md` O49-1].
대조 포트는 인덱스 3,782에서 실제 버스트에 진입하며, 첫 레이아웃 드로우는 #3,783이고
한 프레임에 232 드로우이다 [E: `scratchpad/oracle49/RECEIPTS.md`; log:
`docs/log/cycle41-gameplay.md` O49-2].
ORACLE49는 그 빌드에서 정방향 탭 창을 24,907..24,909로 재보정했으므로, 옛
24,907..24,908 구간은 이식 가능한 상수가 아니라 역사적 값이다
[E: `scratchpad/oracle49/RECEIPTS.md`; log: `docs/log/cycle41-gameplay.md` O49-4].

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

## 원래의 A/B/C 예측, 측정된 결과가 아님

| 비교 | 예측 | 틀렸을 때의 의미 |
|---|---|---|
| A 대 B | 29 중 29 동일 [H: proposed repeat test, not an ORACLE47..49 result] | 원인을 귀속하기 전에 달라진 입력이나 비결정성을 조사한다 [H] |
| A 대 C | 마을부터 프레임이 다를 수 있음 [H: proposed test] | 초는 시드의 최상위 바이트를 바꾸지만, 프레임 동일성만으로는 그 접기를 반증하지 못한다 [S: `src/matched/func_0209dbbc.c`; log: `docs/log/cycle41-gameplay.md` O46-1] |
| 네 번째 조건, `ACWW_RTC_DATE=20060615` (연도만) | 같은 부팅 시드; 프레임 전체의 동일성은 미측정 [H: proposed test] | 연도는 이 접기에 없다; 다른 연도 의존 동작은 배제되지 않는다 [S: `src/matched/func_0209dbbc.c`; log: `docs/log/cycle41-gameplay.md` O46-1] |

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
