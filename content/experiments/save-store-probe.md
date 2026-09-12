# 세이브 저장소 프로브
<!-- source: wiki/experiments/save-store-probe.md -->

**상태: 조건 A와 B는 측정됨(SAVEFLOW41); 조건 C는 미실행. 결과와 아래 세 질문에 대한 답은
`save-and-reload.md`에 있다 -- 이 페이지를 다시 실행하기보다 그 페이지를 읽을 것.** 요컨대,
마을 레시피는 746번의 백업 읽기와 정확히 한 번의 쓰기, 즉 `0x3fffc`의 1바이트 쓰기를 발행한다;
파일은 그 외에는 여전히 0xFF이다; 그리고 정직한 0xFF 소거 읽기는 인터프리터 경로에서
`unimplemented: func_02225a90` 정지를 재현하지 않는다(NOT)
[E: `scratchpad/saveflow/runs/town1`; arm A `scratchpad/saveflow/runs/town-nosave`,
6,000..27,000, as recorded in `save-and-reload.md`]. 정지 프레임에서 심이 출력하는 센서스가
이 페이지의 표가 설명하는 요청 타입당 한 줄짜리 도구를 대체했다.

## 원래의 목적 (SAVEFLOW41과 SAVE43 이전)

이 실험이 제안될 당시에는 보관된 게임 실행 중 어느 것도 영속성을 입증하지 못했다.
그 뒤 SAVEFLOW41이 위의 1바이트 쓰기를 측정했고, SAVE43은 저장된 마을이 다시 로드되는
것을 입증했다 [E: `scratchpad/save43/RECEIPTS.md`, `gp-S3`, `boot-A` and `boot-B`;
`docs/log/cycle42-save.md` SAVE43 ; `scratchpad/save43/runs/gp-S3`]. 아래의 원래 질문들은 역사로서 남겨 둔다. 세 가지를 분리할 가치가 있으며,
오직 도구만이 이들을 분리할 수 있다:

1. 게임이 마을 회관으로 가는 길에 백업 요청을 *발행*하는가(요청 타입 6, 그리고 혹시
   7이나 9)?
2. 실제로 무엇인가 파일에 도달하는가?
3. 정직한 0xFF 소거 읽기가 부팅을 바꾸는가?

세 번째는 이미 절반이 측정되어 있다: 읽기 채움(read fill)을 켠 상태에서 키 입력 START
실행은 프레임 10 근처에서 `unimplemented: func_02225a90`에 멈췄고(심볼 테이블은 이를
`func_ov003_02225a90`, `ov003`으로 명명한다 [S: `src/matched/func_ov003_02225a90.c`; source account: `config/adm-kr/arm9/overlays/ov003/symbols.txt`]),
채움을 끈 같은 빌드는 깨끗하게 실행된다 [H: host-source account from `port/shim/fs/cardreq.c`; verify with a retained scripted run and frame using this page's recipe]. 이는 정직한 답이
부팅을 포트가 아직 따라갈 수 없는 경로로 옮긴다는 뜻이다 -- 어느 경로인지는 말해 주지
않는다.

## 레시피

세 개의 조건. 첫 번째는 대조 실행이며 먼저 실행해야 한다 (M15).

**조건 A -- 저장소 없음, 대조.** `two-tap-town-recipe.md`가 제시하는 그대로의 마을
레시피, `ACWW_SAVE` 미설정. `run_town.py`는 이미 기본값에서 세이브 변수를 해제하므로,
이는 기존 실행이다 [E: `scratchpad/cycle40/run_town.py`, `BASE`].

**조건 B -- 새로 소거된 저장소.** `scratchpad/save/fresh.sav`가 있으면 삭제한 뒤:

    python -B scratchpad/cycle40/run_town.py save-fresh \
      ACWW_SAVE=C:/Users/moomin/Desktop/acww/scratchpad/save/fresh.sav \
      ACWW_INTERP=1 \
      ACWW_TOUCH_AT=6900 ACWW_TOUCH_EVERY=60 ACWW_TOUCH_REPEAT=2 \
      ACWW_TOUCH2_X=221 ACWW_TOUCH2_Y=181 ACWW_TOUCH2_AT=24600 ACWW_TOUCH2_FOR=10 \
      ACWW_TOUCH2_EVERY=60 ACWW_TOUCH2_REPEAT=2 \
      ACWW_STOP_FRAME=48000 ACWW_SHOT_AFTER=6000 ACWW_SHOT_EVERY=1500 ACWW_PAD_SAMPLE=0

`run_town.py`는 기본값에서 `ACWW_SAVE`를 해제하므로, 다른 무엇을 읽기 전에 부팅 줄에서
오버라이드가 살아남았는지 확인한다 -- 저장소가 조용히 꺼진 조건은 다른 이름을 쓴 조건 A일
뿐이다.

**조건 C -- 0으로 채운 저장소.** 같은 실행을, 256 KB의 `0x00`으로 만든 파일에 대해
수행한다. 이는 의도적으로 손상된 세이브 분기이다: 0으로 채운 블록은 세이브 부재가
아니라, 헤더와 체크섬이 0인 세이브이다 [H: host-source account from `port/shim/fs/cardreq.c`; verify with a retained scripted run and frame using this page's recipe].

## 예상 관측

도구들, 모두 실행 로그에 있다 [H: host-source account from `port/shim/fs/cardreq.c`; verify with a retained scripted run and frame using this page's recipe]:

| 줄 | 의미 |
|---|---|
| `acww save: backup store LIVE, 256 KB flash, newly erased (0xFF)` | 조건 B의 저장소가 올라왔다 |
| `acww save: backup store LIVE, 256 KB flash, existing file` | 파일이 이미 전체 크기였다 |
| `acww card: request type 6 (with a command block)` | 첫 백업 읽기, 서로 다른 타입마다 한 번 |
| `acww card: request type 7` / `type 9` | 쓰기와 그 검증 -- **게임이 저장을 시도했다고 말하는 줄** |
| `acww save: persisted N bytes` | 첫 쓰기 때, 그 뒤 64 KB마다 -- **바이트가 파일에 도달했다고 말하는 줄** |
| `acww pxi: card request ... queued for the next VBlank` | 요청이 한 프레임 늦는 경로를 탔다 |

예측, 각각 반증 가능:

- 조건 A와 조건 B는 **29 프레임 전부에서 동일한 스크린샷**을 만든다. 새로 소거된 0xFF
  저장소와 저장소 없음은 둘 다 "세이브 없음"을 뜻하기 때문이다 -- 단, 손대지 않은 버퍼
  경로와 0xFF 경로가 다르다면 예외이며, 그것이 바로 위의 `func_02225a90` 정지이다. 다르다면
  그 정지가 인터프리터 경로에서 재현된 것이고 `ACWW_EXPLORE=1`로 진단할 수 있다.
- 조건 B의 파일은 이후에도 여전히 256 KB의 `0xFF`이고, `persisted` 줄이 없다: 마을
  레시피는 게임 내 저장에 결코 도달하지 않는다.
- 조건 C는 조건 A와 일찍 -- 처음 수백 프레임 안에 -- 갈라지며, 손상된 세이브 경로를
  보여 준다.

이후, 로그를 믿지 말고 파일을 확인한다:

    python -c "d=open(r'scratchpad/save/fresh.sav','rb').read(); print(len(d), d.count(255))"

256 KB에 카운트 262,144이면 아무것도 쓰이지 않은 것이다.

## 반증 조건

- `acww card: request type 6` 줄이 전혀 없음: 게임은 이 경로에서 백업을 결코 읽지 않으며,
  세이브 동작에 관한 모든 결론은 레시피가 도달하지 않는 코드 경로에 관한 것이다.
- 조건 A에 `persisted` 줄이 있음. 거기서는 `ACWW_SAVE`가 미설정이다; 쓰기가 있다면 다른
  무엇인가가 저장소를 열었다는 뜻이다.
- 어느 쪽도 쓰기를 발행하지 않은 프레임에서 조건 B가 조건 A와 다름. 이는 읽기 채움이
  부팅을 바꾸는 것이며, 노이즈가 아니라 발견 사항이다.
- `persisted` 줄의 부재를 "포트는 저장할 수 없다"로 읽는 것. 그것은 이 레시피가 저장하지
  않았다는 뜻이다. 발화할 수 없는 도구는 발화하되 아무것도 바꾸지 않는 도구와 구별할 수
  없다 -- 이 심이 이미 가졌던 두 상수 결함이 정확히 그 모양이었다
  [H: host-source account from `port/shim/fs/cardreq.c`; verify with a retained scripted run and frame using this page's recipe].

## 관련 문서

- `../systems/save-data.md`
- `two-tap-town-recipe.md`
