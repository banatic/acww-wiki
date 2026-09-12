# 저장과 재로드
<!-- source: wiki/experiments/save-and-reload.md -->

**상태: 실행되어 답을 얻음, 2026-09-10 (SAVE43, `2e579f09`). 세 가지 주장 모두 성립한다: 게임이
스스로 두 뱅크를 쓰고, 그 바이트는 ROM 자신의 유효성 검사를 통과하며, 두 번째 실행은
기존 마을 분기를 탄다.** 답은 **SAVE43** 절을 읽으면 된다. 그 아래의 조건들은 측정된 그대로,
측정된 순서대로 남겨 두었다. 두 중간 판독이 곧 내용이기 때문이다: 조건 B(SAVEFLOW41)는
게임이 한 번도 저장을 요청하지 않은 채로 저장소 기계 장치를 증명했고, 조건 D(SAVE42)는
프롬프트에 도달해 규칙의 위치를 짚어 준 거부(REFUSAL)를 받았다.
어떤 조건이 두 번째 실행이 막혀 있다고 말한다면, 그 문장은 SAVE43에 의해 대체되었으며
당시 알려져 있던 것의 기록으로만 남겨 둔 것이다.

## 목적

`save-store-probe.md`는 무엇이든 파일에 도달하는지를 묻는다. 이 페이지는 그 다음 질문을
묻는다: **플레이된 게임이 영속하는가** -- 게임이 카드 프로토콜을 통해 스스로 자기 레코드를
쓰는가, 그 레코드가 ROM 자신의 유효성 검사를 통과하는가, 같은 `ACWW_SAVE`로 두 번째
실행을 하면 택시 인트로 대신 저장된 마을로 부팅되는가?

세 가지 주장을 분리해야 하며, 이전의 모든 설명이 멈춘 곳은 가운데 주장이다:

1. 게임이 한 뱅크의 백업 쓰기를 *발행*한다(`0x00000..0x173fc`에 대한 요청 7);
2. 바이트가 메모리 매핑만이 아니라 파일(FILE)에 도달한다;
3. 두 번째 실행이 그것을 읽어 들여 기존 마을 분기를 탄다.

## 레시피

**조건 A -- 대조, 먼저 (M15).** 저장소 없이 두 번 탭 마을 레시피를 27,000 프레임까지:

    python -B scratchpad/saveflow/run_sf.py town-nosave \
      ACWW_INTERP=1 \
      ACWW_TOUCH_AT=6900 ACWW_TOUCH_EVERY=60 ACWW_TOUCH_REPEAT=2 \
      ACWW_TOUCH2_X=221 ACWW_TOUCH2_Y=181 ACWW_TOUCH2_AT=24600 ACWW_TOUCH2_FOR=10 \
      ACWW_TOUCH2_EVERY=60 ACWW_TOUCH2_REPEAT=2 \
      ACWW_STOP_FRAME=27000 ACWW_SHOT_AFTER=6000 ACWW_SHOT_EVERY=1500 ACWW_PAD_SAMPLE=0

**조건 B -- 새로 소거한 저장소, 레시피 전체.** 먼저 `savetool.py make`로 절대 경로에
만들고, 같은 실행을 `"ACWW_SAVE=@SF@\town1.sav"`를 추가해 48,000까지 돌린다. `@SF@`는
`run_sf.py` 안에서 `scratchpad/saveflow`로 확장된다; 셸에서 경로를 조립하지 않는다(*반증
조건* 참고).

**조건 C -- 두 번째 실행.** 조건 B와 같은 명령, 같은 `ACWW_SAVE`, 그 외에는 아무것도
바꾸지 않고, 파일은 조건 B가 끝난 그대로 둔다. 관측 대상은 조건 B가 택시를 보여 준
프레임의 스틸이다.

실행이 정지 시점에 출력하는 센서스(census)를 읽고, 그 다음 파일(FILE)을 읽는다:

    python port/tools/savetool.py check <the same absolute path>

## 예상 관측

| 어디서 | 무엇이 주장이 참이라고 말하는가 |
|---|---|
| 실행 로그 | `acww card: req 7 WRITE flash 0x00000000..0x000173fc` -- 한 바이트가 아니라 뱅크 전체 |
| 정지 시점의 센서스 | `type 7`이 `190456` 바이트 이상, `verify mismatches 0` |
| `savetool check` | 두 뱅크 모두 검증 통과 그리고 `the game would LOAD this bank` |
| 조건 C의 스틸 | 조건 B가 택시를 보여 준 프레임에서 택시 내부가 아니라 마을 |

## 관측된 것

**조건 B, `scratchpad/saveflow/runs/town1`** (DIAGNOSTIC, B38; 48,000 프레임에서 exit 100,
1,636 s, 스틸 29장, 폴트 없음, `unimplemented` 없음), `savetool.py make`로 새로 소거한
256 KB 저장소 사용 [E: `scratchpad/saveflow/runs/town1/receipt.json`]:

    acww card census: arm7 requests 748 (native CARDi_Request 0), store LIVE
      type 6: 746 requests, 190461 bytes, flash 0x00000000..0x0002e7f8
      type 7:   1 request,        1 byte,  flash 0x0003fffc..0x0003fffd
      type 9:   1 request,        1 byte,  flash 0x0003fffc..0x0003fffd
      persisted 1 bytes; verify mismatches 0
      FlushViewOfFile calls 2

- 부팅은 **두 뱅크를 연달아** 읽는다 -- 프레임 10에 오프셋 0부터 0x2e7f8 바이트 --
  이는 `func_020a1a40`의 슬롯 0과 슬롯 1이다 [S: `src/matched/func_020a1a40.c`; source account: `port/shim/game/savepoll.c`,
  `src/matched/func_020a1a40` tables `data_020d1c20` / `data_020d1bf0`].
- 프레임 757에 **`0x3fffc`에 한 바이트**를 쓰고, 758에 검증한다. 그곳은 두 뱅크 바깥이자
  편지 저장소 바깥, 칩의 마지막 워드다
  [H: log/source account: the census above; receipt provenance unresolved].
- **48,000 프레임 동안 그 외에는 아무것도 저장소를 건드리지 않으며**, 이후 `savetool.py check`는
  두 뱅크 모두 `ALL 0xFF -- erased flash, no save here`라고 보고한다 [H: log/source account: the census above run; receipt provenance unresolved].
- 정직한 0xFF 소거 읽기는 이 경로를 탈선시키지 **않는다**: `unimplemented: func_02225a90`
  없음, 폴트 없음, 48,000 프레임 [H: log/source account: the census above run; receipt provenance unresolved]. 그 정지는 네이티브 경로에서의 관측이다
  [H: log/source account: `port/shim/fs/cardreq.c`'s comment; `../systems/save-data.md`; receipt provenance unresolved].

**차단 요인.** 조건 B의 스틸은 프레임 24,000, 37,500, **그리고** 48,000에서 한결같이 택시
내부와 마을 이름 키보드(`마을 이름은?`)를 보여 준다 -- 24,600에 예정된 두 번째 접촉이
이름을 확정하지 못한다 [E: `scratchpad/saveflow/runs/town1/shot_024000.bmp`,
`shot_037500.bmp`, `shot_048000.bmp`]. 커밋 `6ca48706`의 영수증 있는 실행 `town-R1`은
37,500까지 플레이어를 마을 회관 앞에 세워 두었다 [H: log/source account: `docs/state/port-frontier.md`, RECEIPT41; receipt provenance unresolved].
따라서 커밋 `174ae9e3`에서는 레시피가 게임플레이에 도달하지 못하고, 게임플레이 하류의
모든 것 -- 저장 트리거를 포함해 -- 은 스크립트로 도달할 수 없다.

**이것은 회귀가 아니라 수렴이며, 오라클이 이를 결정한다.** 바로 이 구간에서 측정된 포트와
DeSmuME 원본 사이의 차이는, 포트의 두 탭은 마을 이름을 확정(CONFIRM)하고 원본의 동일한
탭은 확정하지 못해서 원본이 48,000까지 마을 이름 키보드에 머문다는 것이었다 -- 그리고
그곳이 지금 조건 B가 머무는 곳이다
[O: `docs/kb/hybrid/open-questions.md` question 1, measured at `eb24787a`;
`scratchpad/oracle/tap-fullpad/compare-vs-tap-D56.txt`]. 같은 오라클 캡처를 조건 B에 대해
돌리면:

    python port/tools/oracle/compare.py \
        scratchpad/saveflow/oracle-tap-fullpad scratchpad/saveflow/runs/town1

| 프레임 | `6ca48706`의 `tap-D56` | `174ae9e3`의 `town1` |
|---|---|---|
| 25,500 .. 48,000, 17장 전부 | ncc 0.70, ncc-top 0.0000 | ncc **0.993-0.999**, ncc-top **0.936-0.990** |

29 프레임, 평균 ncc 0.9762 [O: `scratchpad/saveflow/compare-oracle-vs-town1.txt`]. 이 실행은
오래된 레시피 줄인 `ACWW_TOUCH2_AT=24600`을 사용했고, TOUCH42 빌드에서 포트는 원본과
정확히 같이 24,600에서 마을 이름 키보드에 머문다 [E: `tap-T42b` ; `scratchpad/cycle40/runs/tap-T42b`] [O:
`scratchpad/oracle/tap-window`]; 마을 프론티어는 기록상의 24,700 레시피 위에 서 있으며,
거기서는 양쪽 모두 확정한다 [E: `tap-T42c` ; `scratchpad/cycle40/runs/tap-T42c`] [O: `scratchpad/oracle/tap-24700`] -- `touch-latency.md`
참고. 예외는 두 프레임, 7,500과 13,500으로, 평균 휘도가 뒤바뀐 채 0.70을 기록하는 한편
그 사이의 모든 프레임은 일치한다: 어두운 택시 탑승 구간이 포트에서 약 한 스크린샷 간격
일찍 시작하고 끝나는 것이며, 다른 화면이 아니라 보정되지 않은 오라클 프레임 카운터에
대한 위상 오프셋이다 [O: same file] [H: settled by `--offset`, or by
stills every 150 across 7,000..14,000 on both sides].

**OFF 레시피도 같은 방향으로 움직였다.** HEAD 자체의 OFF 실행은 보존된 cycle39 네이티브
OFF 스틸과 31 프레임 전부에서 다르고(프레임 4,500에서 393,270 바이트 중 277,667 바이트가
다름), `docs/kb/hybrid/recipes.md` 2절은 31/31을 통과 기준으로 명시한다 [H:
`scratchpad/saveflow/runs/off-control` vs `scratchpad/cycle39/execution39-touch39-005/off`; receipt lost with its worktree; repeat the named recipe and retain the stated frames].
오라클 자체의 OFF 캡처에 대해 채점하면 HEAD는 평균 ncc **0.9970**, 그 레퍼런스는
**0.8401**을 얻는다 [O: `scratchpad/saveflow/compare-oracle-vs-off-control.txt`,
`compare-oracle-vs-cycle39ref.txt`] -- 따라서 여기서도 트리는 원본 쪽으로 움직였고,
보존된 레퍼런스는 정확성 기준으로 취급할 것이 아니라 HEAD에서 다시 채취해야 한다.

**조건 A가 결정한다: 레시피를 망가뜨린 것은 저장소가 아니다.** `scratchpad/saveflow/runs/town-nosave`는
`ACWW_SAVE`를 설정하지 않은 동일한 레시피를 27,000 프레임까지 돌린 것이며, 그 스틸은
프레임 6,000..27,000에 걸쳐 조건 B와 **15/15 SHA256 동일**하다 -- 택시, 플레이어 이름
키보드, 탑승, 대화, 마을 이름 키보드 모두
[H: log/source account: `runs/town-nosave` vs `runs/town1`; receipt provenance unresolved]. 이는 `save-store-probe.md`가 조건 A와 B에 대해
내놓은 예측이며, 확인되었다.

**계측 변경은 꺼져 있을 때 무해하다.** 카드 센서스, `FlushViewOfFile` 라이트스루, 새
`ACWW_PADSCRIPT` 타임라인은 모두 OFF 레시피를 바이트 단위로 동일하게 남긴다:
`runs/off-census`와 `runs/off-padscript`는 각각 이들 없이 HEAD 자체 소스를 다시 링크한
`runs/off-control`과 **31/31 SHA256 동일**하다 [H: log/source account: those three run directories; receipt provenance unresolved].

**...그리고 `ACWW_PADSCRIPT`는 켜져 있을 때 무해하지 않다** (B6). 프레임 24,000 스냅샷에서
세 번 재개하여 각각 25,500까지 150마다 스틸을 찍었다: `runs/r1`(스크립트 없음)은 겹치는
두 스틸 모두에서 조건 B와 같으므로 스냅샷은 정확히 재개된다; `runs/r2a`(`24100:0` --
소유권만)는 24,750부터 `r1`과 달라지는데, 이는 스크립트가 `ACWW_KEYS3`의 A 펄스를 올바르게
밀어낸 것이다; 그리고 `runs/r2b`, 같은 스크립트에 24,200과 24,400의 Up 두 번 누름을 더한
것은 **24,300**부터 `r2a`와 달라진다 -- 첫 누름 뒤 한 스틸 만에. 두 실행은 누름에서만
다르며, 화면에서 그 차이는 마을 이름 키보드의 탭 스트립이 선택을 옮기는 것이다 [E: those three run directories; `scratchpad/saveflow/padscript-proof.png`].

**조건 C**는 위 내용을 쓸 당시 실행되지 않았다: 두 번째 실행이 읽을 것이 파일에 아무것도
없었다. 지금은 실행되었다.

## SAVE43 -- 세 가지 주장 모두 측정됨

체인, 전부 DIAGNOSTIC 실행(B38), 워크트리 `.claude/worktrees/agent-a757560884bf9588e`의
`fbfc987d`에 SAVE42의 `frame.c` 센서스 호출을 더해 다시 링크한 빌드
[E: `../../docs/log/cycle42-save.md` SAVE43; `scratchpad/save43/RECEIPTS.md`]:

    town recipe (24,700) with a fresh erased ACWW_SAVE, snapshot at 48,000     522 s
      -> out of the town hall and past the tutorial hold, snapshot at 55,400
      -> the map: the player's own house is the GREEN icon; walk to it
      -> ENTER the house (the slide: push into the wall, pulse sideways, press A)
      -> step back out: Tom Nook is at the door; run his speech out with A
      -> 0x021f3c30 leaves 1 and becomes 0        <- the whole gate
      -> START: the real save menu, then A

**주장 1, 게임이 쓰기를 발행한다 -- 그리고 두 뱅크(BOTH) 모두 쓴다.** 정지 시점의 센서스:

    type 7: 744 requests, 190456 bytes, flash 0x00000000..0x0002e7f8
    type 9: 744 requests, 190456 bytes, flash 0x00000000..0x0002e7f8
    persisted 190456 bytes; verify mismatches 0
    FlushViewOfFile calls 745

`0x00000000`부터 연속된 256바이트 페이지, 각각 한 프레임 뒤에 검증됨: `func_020a1d94`의
512바이트 스텝은 카드 페이지 두 장이다 [H: log/source account: the run's own request spans; receipt provenance unresolved]. 화면에서는:
`오늘은 여기까지 하시겠습니까?` -> `저장하고 있습니다` -> **`저장했습니다！`** -- `sequence2_`
메시지 0, 1, 2로, 이는 `func_0209f6e4`의 거부하지 않는 분기다 [H: source account: SAVE42's transcription
of that branch; direct ROM-source provenance unresolved].

**주장 2, 바이트가 ROM 자신의 검사를 통과한다.** 이후 파일에 `savetool.py check`:
뱅크 1 체크섬 저장값 `0xa6ad` 계산값 `0xa6ad` 잔차 `0x0000`, 게임코드 ok, 플래그
`+0x173fa` ok, 워드 합 ok -> *the game would LOAD this bank*; 뱅크 2도 같으며
바이트 단위로 동일한 미러다. 여덟 중 세 주민이 입주해 있고, 플레이어 0의 id는 `0xd185`,
이름은 플레이어가 `U+3143`(`ㅃ`) x4, 마을이 x6으로 디코드된다 -- 스크립트된 키보드가
입력한 그대로다 [E: `scratchpad/save43/savecheck-S3.txt`].

**주장 3, 두 번째 실행.** 새 실행, 스냅샷 없음, 같은 `ACWW_SAVE`: 3,000-4,000에서
플레이어는 침대와 전화기가 있는 자기 집 안에 있고, 그 위에
`시작 준비 중입니다 / 전원을 끄지 말고 그대로 기다려 주십시오`가 떠 있으며, 5,000부터는
HUD와 함께 자기 집 현관 밖에 있다 -- 택시도 없고, 어느 키보드도 없다. 대조는 소거된
저장소에서의 동일한 실행으로, 이름 키보드가 뜬 택시 내부다 [H: log/source account: `boot-A`; SAVE42's
`boot9000.png`; receipt provenance unresolved]. 패드 타임라인으로 구동한 두 번째 실행은 재로드된 마을을 걸어 다니며
NPC를 만나므로, 마을은 단지 그려질 뿐 아니라 플레이 가능하다 [H: log/source account: `boot-B`; receipt provenance unresolved].

**이것이 규칙(RULE)에 대해 바꾸는 것.** 차단 요인은 입주 모드 워드 하나뿐이며, 그것은
게임 자신의 코드에 의해 지워진다: `func_020a128c`는 열 번째 접근자, `mode := 0`이고,
호출자는 `func_0209ec74`와 `func_ov068_0226e648`이며, 저장소 워치포인트로 포착되었다
[E: `gp-W0` ; `scratchpad/save43/runs/gp-W0`]. SAVE42의 "`mode := 0`은 없다"는 철회된다. Nook의 다락방 침대는 하나의
저장 지점이지 게이트가 아니다.

## 조건 D (SAVE42): 게임이 저장을 요청받을 때까지 계속 플레이하고, 그 답을 읽는다

**상태: 실행됨, 2026-09-10, 그리고 이것이 이 페이지에 빠져 있던 답이다.** 조건 B는
"어떤 레시피도 저장에 도달하지 못한다"에서 멈췄다. 조건 D는 거기에 도달하고, 게임은
거부한다 -- 추측이 아니라 이제 ROM 안에 위치가 특정된 이유로.

체인, 전부 DIAGNOSTIC(B38), 워크트리 `agent-aeac5138b67b1796a`의 `61495f07`, 실행
디렉터리는 `scratchpad/save42/runs/` 아래: `town-A`(새로 소거한 저장소로 24,700 레시피를
48,600까지, 48,000에서 스냅샷) -> `gp-P1`(마을 회관 밖으로, 튜토리얼 홀드를 지나, 55,400에서
스냅샷) -> `gp-M1`(지도) -> `gp-W1`..`gp-W7`(지도 마커로 조종한 여섯 구간) ->
`gp-D1`..`gp-D9`(58,920에 집 안) -> `gp-S2`(START).

| 어디서 | 무엇이 관측되었는가 |
|---|---|
| `gp-S2` 프레임 59,700 | 게임 자신의 거부, `어머？ 지금은 아직 / 저장하지 못하나 봐요` [E: `scratchpad/save42/s2_refuse.png`] |
| 메시지 아카이브 | 그 문자열은 `script/KOR/message/sp/etc/sequence4_.bmg` 인덱스 **4** [H: source account: `scratchpad/save42/bmg.py find`; direct ROM-source provenance unresolved] |
| ROM | `func_0209f6e4`는 `func_020a12d4() \|\| func_020a12c0()`일 때, 즉 `0x021f3c30`의 워드가 1 또는 2일 때에 한해 `sp_etc_sequence4`를 붙이고 `self+0x72`에 4를 쓴다 [S: `src/matched/func_020a12c0.c`, `src/matched/func_020a12d4.c`; source account: `func_0209f6e4`, `func_020a12c0`, `func_020a12d4`, main] |
| 스냅샷 | 프레임 48,000에서 `0x021f3c30 = 1` [E: `scratchpad/save42/stpeek.py st/town48000.st 0x021f3c30`] |
| ~60,000 프레임 플레이 후의 저장소 | 여전히 소거 상태와 한 바이트만 다름, `+0x3fffc`; 두 뱅크 모두 `ALL 0xFF` [H: log/source account: `savetool.py check`; receipt provenance unresolved] |
| 이제 출력되는 센서스 | `arm7 requests 748 ... NO WRITE_BACKUP REACHED THE STORE -- this run never saved` [H: log/source account: `runs/off-fix`; receipt provenance unresolved] |

**그래서 조건 D가 준 답은: 아직 아니다, 그리고 포트 때문이 아니다.** ~~모드 워드를 쓰는
곳은 입주 오버레이의 `func_ov147_02299414`(`:= 1`)와 `func_ov147_022997ec`(`:= 2`, `:= 3`),
그리고 `func_020a4454`(`:= 3`, `:= 4`)뿐이다; ROM의 어떤 함수도 0을 쓰지 않으므로 0은 BSS
기본값이다.~~ **위 SAVE43에 의해 철회됨**: `func_020a128c`는 열 번째 접근자, `mode :=
0`이며, 게임은 도착이 끝날 때 이를 호출한다. 여기 이름을 든 0이 아닌 값을 쓰는 세 곳은
맞다 [H: source account: their pool words; direct ROM-source provenance unresolved]; "아무것도 0을 쓰지 않는다"는 절반은 함수 하나를 남기고 멈춘
검색이었다.

**시계는 잘못된 지렛대이며, 이는 논증이 아니라 실행(RUN)으로 확인되었다.** 같은
55,400 프레임 스냅샷에서 `ACWW_RTC_DATE`만 다른 두 조건, 각각 START를 누르고 프롬프트를
A로 진행:

| 실행 | `ACWW_RTC_DATE` | HUD | 게임이 말한 것 |
|---|---|---|---|
| `runs/gp-RTC0` | `20050615` (대조) | `6/15 수` | 거부 |
| `runs/gp-RTC1` | `20050616` | `6/16 목` | **같은 거부, 한 글자도 다르지 않음** |

시계는 정말로 움직였고 -- 날짜 패널은 다음 날을 표시하고 요일이 넘어갔다 -- 답은 바뀌지
않았다 [E: `scratchpad/save42/rtc0_a.png`, `rtc1_a.png`]. 그것이 ROM이 예측하는 바다:
`ACWW_RTC_DATE`는 `func_0207b05c`의 놓친 날짜 따라잡기를 구동하고
[H: source account: `../systems/time-and-rtc.md`; direct ROM-source provenance unresolved] 거부 분기가 읽는 어떤 것도 건드리지 않는다. 차단을
푸는 것은 도착을 끝내는 것이며, ROM은 같은 아카이브에서 그렇게 말한다: `sequence4_[12]`는
플레이어의 집에 온 Nook이다 -- 다락방 침대(`옥탑방에 있는 침대`)에 누우면 그날의 결과를
저장할 수 있다.

**작업 중 발견된 계측 주의점 하나.** 재개된 실행은 카드 요청을 전혀 발행하지 않으므로,
지연 초기화되는 `flash_store()`는 파일을 한 번도 열지 않고, 센서스는 `ACWW_SAVE`가
설정되어 있어도 `store absent`라고 보고한다 [E: `runs/gp-RTC0`, `gp-RTC1`, `arm7 requests 0` ; `scratchpad/save42/runs/gp-RTC1`].
그것은 누락된 쓰기가 아니라 "아무것도 요청하지 않음"이다. 그 줄은 센서스가 뜻하는 대로
읽어야 한다.

**이 경로에서 포트 결함 하나가 발견되어 고쳐졌다.** 이 페이지가 인용하는 센서스인
`acww_card_report()`는 트리 어디에도 호출자가 없었던 반면 `docs/kb/hybrid/save-flow.md`는
정지 프레임에서 출력된다고 말했다; 센서스는 SAVEFLOW41(B6) 이래 침묵하고 있었다. 이제
양쪽 종료 경로에서 호출되며, OFF 대조는 이 변경이 보이지 않는다고 말한다: 프레임
4,500..9,000을 150마다, `runs/off-fix` 대 `runs/off-control`(`frame.c`를 되돌려 다시 링크한
같은 트리), **31/31 exact (RGB), 평균 ncc 1.0000** [H: log/source account: those two run directories; receipt provenance unresolved].

**두 번째 실행 자체의 기계 장치는 증명되었으며, 이는 막힌 주장과 분리해 둘 가치가
있다.** `runs/boot-store`는 같은 `ACWW_SAVE`로 스냅샷 없이, 센서스가 연결된 빌드에서의
새 실행이다: `req 6 READ flash 0x00000000..0x0002e7f8 (190456 bytes) from
frame 10` -- 두 뱅크를 연달아, `func_020a1a40`의 슬롯 0과 슬롯 1 -- 그리고 요청 748,
1바이트 영속, 검증 불일치 0의 센서스 [H: log/source account: `runs/boot-store`; receipt provenance unresolved]. 뱅크가 소거되어 있으면
부팅은 `func_020b5724`의 새 게임 분기를 타고 9,000의 스틸은 플레이어 이름 키보드가 뜬
택시다 [E: `scratchpad/save42/boot9000.png`]. **그 스틸이 조건 C가 달라져야 할 대조**이며,
그것이 달라질 통로인 읽기 경로는 오늘 작동한다.

**아무도 열 번의 실행을 반복하지 않도록, 내비게이션 사실 두 가지.** 세계가 아니라
지도(MAP) 마커로 조종한다: X로 지도를 열고, 분홍 마커와 목표 아이콘을 지도 픽셀로 읽고,
**동쪽으로 프레임당 0.184 지도 px, 북쪽으로 프레임당 0.23**으로 환산한다. 그리고 **문으로
걸어 들어가도 문은 열리지 않는다** -- `gp-D8`은 플레이어를 문간 한가운데에 세웠지만(Up을
700 프레임 홀드, Left를 100 중 20 펄스, 패드 행은 OR로 합쳐지므로) 아무 일도 없었다;
`gp-D9`는 A 펄스를 더해 안으로 들어갔다 [H: log/source account: those two run directories; receipt provenance unresolved]. 원본(ORIGINAL)도
A 누름이 필요한지는 미검증이다 [H: one oracle arm over `st/door57700.st`'s approach settles it].

## 반증 조건

- "persisted 1 bytes"를 "포트가 저장할 수 있다"로 읽는 것. 그것은 이 레시피가 한 주소에
  한 바이트를 썼다는 뜻이다; 쓰기, 검증, 플러시 기계 장치는 증명되었지만 게임의 저장은
  아니다.
- 조건 B로부터 `ACWW_SAVE`가 마을 레시피를 망가뜨렸다고 결론짓는 것. 저장소는 프레임
  3, 10, 757, 823에서만 건드려지며, 모두 키보드보다 한참 전이다. 조건 A가 이를 결정하는
  대조다.
- MSYS 셸에서 저장소 경로를 조립하는 것. `ACWW_STATE_SAVE=<frame>:<path>`의 콜론 때문에
  bash가 값을 경로 목록으로 다시 쓰며, `24000:C:/...`는 `24000:/c/...`로 들어간다; 그러면
  스냅샷은 끝내 쓰이지 않고 실행은 끝날 때까지 그에 대해 아무 말도 하지 않는다.
- exit 1로 끝난 실행을 신뢰하는 것. 이미지 안의 어떤 것도 exit 1을 내지 않는다
  [H: source account: `port/tools/measure.py`'s `acww_exit` table; direct ROM-source provenance unresolved]; 이는 다른 세션이
  `taskkill /F /IM acww.exe`를 실행했다는 뜻이다. `run_sf.py`가 고유한 이름의 복사본을
  띄우는 것은 그 때문이다.

## 관련 문서

- `save-store-probe.md` -- 이 실행이 함께 답하는 더 좁은 프로브(조건 B).
- `../systems/save-data.md` -- ROM 쪽 설명.
- `two-tap-town-recipe.md` -- 조건 A와 B가 돌리는 레시피.
- `savestate-resume.md` -- `scratchpad/saveflow/town24000.st`는 조건 B가 채취했다.
- `gameplay-walkthrough.md` -- SAVE43 체인을 프레임 단위로, 그리고 실행들을 잡아먹은 세
  가지 내비게이션 규칙(문 슬라이드, 깜박이는 지도 마커, 이동 속도).
- `../audits/night-2026-09-09.md` -- SAVEFLOW41, SAVE42, SAVE43이 그 밤의 어디에 자리하는지.
