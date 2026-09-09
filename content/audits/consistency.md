# 일관성 감사
<!-- source: wiki/audits/consistency.md -->

**요약.** `wiki/` 아래의 36개 콘텐츠 페이지는 네 번의 독립적인 작성 패스와 런타임 kb 패스로
작성되었으며, 이 문서는 그 모든 페이지를 서로 대조하고 리포지토리와 대조하여 읽은 첫 번째
기록이다. 경로 출처는 매우 양호한 상태다: 백틱으로 감싼 384개의 리포지토리 경로 중 정확히
두 개만 해석되지 않으며, 둘 다 플레이스홀더다. 심볼 출처는 한 가지 특정한 방식으로 더 나쁘다 --
"어디에 있는가" 표의 *모듈* 열이 다섯 페이지에 걸쳐 27개 행에서 틀렸고, 거의 항상 심볼
테이블이 `autoload_2`라고 하는 곳에 `main`이라고 적혀 있었다. 열네 페이지에는 작성 하니스가
남긴 불필요한 `</content>` 태그가 있었다. 페이지 간의 실제 모순은 열 건이 발견되었으며, 아홉
건은 리포지토리를 근거로 여기서 수정했고 한 건은 실행이 필요하다. 적용한 모든 사항은 결정 근거가
된 파일과 줄과 함께 아래에 기록되어 있다.

방법: 모든 `wiki/**/*.md`에 대해 리포지토리 경로 존재 여부, 위키 링크 존재 여부, 심볼 테이블
포함 여부, 페이지 길이, 호스트 주소, 펜스 블록, 한국어 문자열 및 등급 태그를 스크립트로
검사하고, 42개 파일 전체를 통독했다. 개수는 이 패스 시점 기준이다; 어떤 편집이든 한 뒤에는
스크립트를 다시 실행하라.

## 1. 페이지 간 모순

### 1.1 수정됨 -- ITCM에는 네 개가 아니라 158개의 함수가 있다

`engine/graphics-pipeline.md`는 "그 네 개를 ITCM에 넣은 것이 ROM이 명령어 TCM을 사용하는 유일한
경우다 [S: `config/adm-kr/arm9/itcm/symbols.txt`, 16 named functions ...]"라고 말했다.
`engine/memory-map.md`와 `engine/display-objects.md`는 둘 다 다르게 말하며, 테이블이 이를
결정한다: `config/adm-kr/arm9/itcm/symbols.txt`에는 158개의 `kind:function` 줄이 있고 그중
114개가 실제 이름이다 -- 네 개의 `NNS_G3dGe*` 제출 루틴, 열세 개의 `NNSi_G3dFuncSbc_*` 씬 그래프
옵코드, `MTX_*`/`VEC_*`/`FX_*` 고정소수점 라이브러리 전체, `OS_IrqHandler`, `OS_Halt`,
`OS_SaveContext`/`OS_LoadContext`, `OS_GetTick`, 그리고 디스플레이 오브젝트 스테퍼들이다.
`graphics-pipeline.md`("Geometry out")와 `data/rom-layout.md`에서 **수정됨**. 후자는 같은 주장을
"예외"로, 그리고 "hot 3D buffer helpers"라고 적힌 ITCM 표 행으로 담고 있었다.

### 1.2 수정됨 -- 채널 189는 필드 렌더러가 아니라 눈사람이다

`systems/town.md`와 `systems/weather-and-seasons.md`는 둘 다 채널 189가 SNOWMAN이라고 말하며
철회 사실을 언급한다. `engine/scenes-and-channels.md`("채널 189는 필드 렌더 오브젝트다")와
`engine/display-objects.md`("FIELD 렌더러의 vtable은 `0x022382ac`이다")는 철회된 해석을 담고
있었는데, 이는 포트 자체의 심(shim) 헤더(`port/shim/game/chanlist.c:6-8`,
`port/shim/gfx/pmflist.c:53`)에서 가져온 것이다 -- 그 헤더들은 오래되어 맞지 않는다.
`port/BOOT-STATE.md:1159-1171`이 철회 기록이다: 채널 189의 바인드 로그는
`/snowman/snowball1.nsbmd`(`SNW0`, id `0x022383ac`)와 `/snowman/snow_face.nsbmd`(`SNW1`, id
`0x022383c8`)를 지목하며, ov003에는 에이커 지면 텍스처가 전혀 없다. 두 엔진 페이지 모두에서
**수정됨**. `display-objects.md`에는 새로운 "어디에 있는가" 행이 추가되었다.

### 1.3 수정됨 -- 디스플레이 노드의 역참조 포인터: `+0x08` 대 `node+0x10`

`engine/display-objects.md`는 이것을 미해결 가설("두 해석이 모순된다")로 담고 있었다.
이는 두 가지 다른 종류의 노드이며, 리포지토리가 이를 직접 말해준다. `func_020ee834`의 네
리스트는 세 워드 노드 `{prev, next, obj}`를 사용하며 오브젝트는 `+0x08`에 있다
[`port/shim/gfx/pmflist.c:106-119`]. `0x021fcff8`에 있는 다섯 번째 리스트 -- 노드는 각
디스플레이 오브젝트의 `+0x14`에 있는 `sub` 블록이고 `func_020ee9a0`가 순회한다 -- 는 `head`가
`+0`에, 멤버 포인터가 `+4`/`+8`에, 오브젝트가 `node+0x10`에 있으며, `next`는
`func_01ffcffc(node)`를 호출하여 얻는다; 주석에는 이것이 가정이 아니라 ROM의 명령어에서 읽어낸
것이라고 기록되어 있다 [`port/shim/gfx/pmflist.c:961-981`].
**수정됨**: 가설은 해결된 것으로 다시 쓰였고, 다섯 번째 리스트는 이제 "순회 자체" 절에
이름이 명시되어 있다.

### 1.4 수정됨 -- `ov004`에는 121개의 심볼 또는 3,075개의 타깃이 있다

`engine/overlays.md`에는 "모순: `ov004`에 함수가 몇 개 있는가"라는 제목의 절이 통째로 있었다.
모순이 아니다: 두 개의 테이블이다. `config/adm-kr/arm9/overlays/ov004/symbols.txt`에는 121개의
`kind:function` 항목이 있고 그중 90개는 크기가 지정되어 있으며 31개는 크기 0인 `_unk`다; 그
옆의 `config/adm-kr/arm9/overlays/ov004/recovered.txt`에는 경계 복구된 타깃 3,060개가 있고
모두 크기가 지정되어 있다. `tools/agent/target.py:183-215`가 이 사이드카를 설명하며(dsd가
`symbols.txt`를 소유하고 다시 쓴다), 독립적으로 같은 "90 sized function symbols covering 3.8%"를
기록한다; `target.py:50-65, 224`는 `T.load_all()`이 둘 다 로드하는 것을 보여준다. **수정됨**:
해당 절의 제목은 이제 "해결됨"이며, 대응하는 가설 항목은 제거되었다. 언급할 가치가 있는 귀결:
`recovered.txt`에만 나타나는 `func_ovNNN_*` 이름도 STYLE 규칙 2에 따르면 심볼 테이블 이름이며,
그렇기 때문에 `func_ov004_0224522c`, `func_ov092_02299324`, `func_ov065_0227ef00`,
`func_ov003_0222f458`은 정당한 출처다.

### 1.5 수정됨 -- 탭 프레임 불일치, ORACLE42로 해결됨

`docs/log/cycle40-keyboard-gate-probe.md:610-624`가 이를 해결한 뒤에도 다섯 페이지가 여전히
미해결이라고 부르고 있었다: 24,600에서의 탭은 KEYS3 A 입력 프레임(2400 + 37 x 600)에 떨어지고,
원본의 스타일러스 샘플은 포트보다 한두 프레임 늦게 게임에 도달하며, `ACWW_TOUCH2_AT=24700`으로
하면 양쪽 모두 확인하고 일치한다(24,000..27,000의 11 프레임, 평균 ncc 0.9955, 위 화면
1.0000). 세 페이지는 이미 이를 담고 있었다(`systems/dialogue.md`, `systems/input-and-touch.md`,
`experiments/touch-calibration.md` -- 뒤의 둘은 덧붙인 "Result (ORACLE42)" 절로).
다섯 페이지 모두에서 **수정됨**:

| 페이지 | 문장 | 수정 |
|---|---|---|
| `engine/boot-and-entry.md` | "둘은 25,500에서 갈라지는데, 포트의 예약된 두 탭은 마을 이름을 확인하고 원본의 동일한 탭은 그러지 않는다" | ORACLE42 해결 내용을 출처와 함께 덧붙임 |
| `experiments/two-tap-town-recipe.md` | "어느 쪽이 맞는지는 미해결이다 -- `touch-calibration.md` 참조" | 해결된 것으로 다시 씀; 레시피, 예상 관측 표, 탭 횟수 검사를 24,700으로 옮김 |
| `experiments/rtc-hour-sweep.md` | "이 실행에서 문제가 될 주의점: 원본은 이 레시피로는 마을에 도달하지 않는다" | ORACLE42가 제거한 주의점으로 다시 쓰고, 양쪽 조건 모두 24,700을 쓰라는 지시를 추가 |
| `systems/input-and-touch.md` | "어느 쪽이 맞는지는 미해결이다." 그리고 여전히 비교를 요구하는 두 가설 | 페이지 자체의 Result 절을 가리키도록 함; 두 가설은 해결(부정) / 해결(긍정)으로 표시 |
| `systems/dialogue.md` | 가설 "포트가 마을 이름을 한 탭 너무 성급하게 확인한다 ... ADC 왕복" | 기록용으로 해결된 것으로 다시 씀; 왕복은 원인이 아니었다 |

### 1.6 수정됨 -- `POWCNT1` 비트 15는 사운드 플래그다

`data/music.md`는 "`POWCNT1` 비트 15는 `func_0205401c`가 사운드 플래그로 쓴다"라고 말했다.
`engine/graphics-pipeline.md`는 `0x04000304`의 비트 15가 어느 2D 엔진이 위 화면을 구동할지를
선택한다고 말하며, `src/matched/func_020540e4.c`가 정확히 그 목적으로 이를 쓴다. "사운드
플래그" 해석은 `src/matched/func_0205401c.cpp`의 `gSoundFlag`라는 변수 이름에서 왔는데, 그
파일의 헤더 자체가 "names are inferred, not original"이라고 말한다. **수정됨**: `music.md`는 이제
두 함수가 같은 비트를 쓴다는 것, 이름은 추론된 것이라는 것, 그 비트가 화면 스왑이라는 것을
서술하고, 그 전역 변수가 실제로 무엇을 담는지는 가설로 기록한다.

### 1.7 수정됨 -- 사운드 라이브러리는 `main`에 있다

`systems/audio.md`의 "어디에 있는가" 표는 열네 행을 `main (NNS)` / `main (SND)`에 두었고;
`data/music.md`는 `autoload_2`라고 말했다. 테이블이 이를 결정한다: 모든 `NNS_Snd*`, `NNSi_Snd*`,
`SND_*`, `SNDi_*` 심볼은 `config/adm-kr/arm9/autoload_2/symbols.txt`에 있으며(각각 105개와
65개), `config/adm-kr/arm9/symbols.txt`에는 하나도 없다. `audio.md`에서 **수정됨**; `music.md`에는
두 개수와 상호 참조가 추가되었다.

### 1.8 수정됨 -- 거부된 사운드 파일이 몇 개인가

`systems/audio.md`는 "열두 개의 사운드 파일이 거부된다"라고 말하면서, 별도로 세 개의 명령
계층 파일을 언급했다. `port/tools/interp_registry.py`의 `DENY_FILES`에는 아카이브/플레이어/힙
파일 열한 개에 `sndcmd.c`, `sndflush.c`, `sndtag.c`를 더한 -- 열네 개가 있다. 열한 개를
열거하여 **수정됨**.

### 1.9 수정됨 -- 거부 목록(deny list)의 크기

`docs/kb/hybrid/runtime.md:158-160`은 "93 host services ... 40 shim files and
`func_020b1b84` denied"라고 말한다. `port/tools/interp_registry.py`의 `DENY_FILES` 집합에는
**49**개의 베이스네임이 있다(여기에 `DENY_FUNCS = {func_020b1b84}`와 `EXTRA_ENTRIES` 추가
항목 하나). `engine/memory-map.md`가 거부 목록을 인용하는 유일한 위키 페이지였다; 측정된 49를
명시하고 runtime.md가 아홉 개만큼 오래되었음을 표시하도록 거기서 **수정됨**.
`engine/threads-and-interrupts.md`는 크기를 서술하지 않으므로, "40 files / 93 services 대 49
basenames" 모순은 두 위키 페이지 사이가 아니라 두 kb 문서 사이의 것이다 -- 6절 참조.

### 1.10 수정됨 -- 계절 날짜 경계 개수

`systems/weather-and-seasons.md`의 "확인 방법"은 "두 분기가 `0x18`과 비교하고 세 분기가
`0x1a`와 비교한다"라고 말했다. `port/shim/game/season.c`의 재조립된 switch에는 `0x18`과
비교하는 분기가 하나(case 2, 2월)이고 `0x1a`와 비교하는 분기가 셋(case 5, 8, 11)이다. 요약의
경계 -- 2월 25일, 5월 27일, 8월 27일, 11월 27일 -- 는 맞으며 변경되지 않았다.
"한 분기 ... 그리고 셋"으로 **수정됨**.

### 1.11 검토됨, 모순 아님

나중에 읽는 사람이 다시 열지 않도록 기록한다:

- **실행 소요 시간.** `engine/graphics-pipeline.md`의 "811초에 48,000 프레임"(`tap-D56`)과
  `engine/boot-and-entry.md`의 "801초에 48,000 프레임"(`town-R1`)은 서로 다른 두 실행이며,
  둘 다 `docs/log/cycle40-keyboard-gate-probe.md:546`과 `:577`에 일치한다. 스크린샷 개수 31과
  29도 마찬가지다.
- **ncc 수치.** `boot-and-entry.md`는 6,000..24,000 구간에 대해 아래 화면 ncc 0.9997-1.0000을
  인용하고; `input-and-touch.md`, `rng.md`, `two-tap-town-recipe.md`는 같은 구간에 대해 전체
  프레임 0.9920-0.9959를 인용한다. 두 가지 지표이며, 각각 표시되어 있고, 둘 다 ORACLE41에 있다.
- **오버레이 구성.** 148개 슬롯, 코드가 있는 138개, 빈 10개(`ov000`, `ov057`-`ov064`, `ov089`),
  오버레이 함수 11,236개, 전체 함수 25,516개, 그리고 `0x02260020`/`0x02278a00`/`0x0229c180`/
  `0x02260420`을 공유하는 35/19/14/12개의 오버레이는 모두 `config/adm-kr/arm9/**/symbols.txt`에서
  정확히 재현된다. `engine/overlays.md`, `engine/memory-map.md`, `data/rom-layout.md`가 일치한다.
- **bmg 엔디언 메모.** `engine/text-and-messages.md`는 문자열 순회가 `(p[1] << 8) | p[0]`으로
  읽는 반면 `test_.bmg`의 `DAT1`은 UTF-16LE라고 서술하고, 이 불일치를 해결할 덤프와 함께 가설로
  기록한다. `data/archives.md`는 컨테이너 사실만 서술한다. 이는 STYLE 규칙 7이 의도대로 작동하는
  것이다 -- 그대로 둔다.
- **`.bmg`의 `0xf7` 압축.** `text-and-messages.md`와 `data/archives.md`는 같은 1,790/6,330
  분할과 같은 미해결 질문을 제시한다.
- **DTCM.** `data/rom-layout.md`의 "0x460 bytes"는 모듈 이미지이고; `engine/memory-map.md`의
  16 KB는 하드웨어 윈도우다. 모순은 아니지만 모순처럼 읽혔으므로, `rom-layout.md`는 이제 어느
  것이 어느 것인지 밝히고 `memory-map.md`를 상호 참조한다.

## 2. 출처 유효성

### 2.1 리포지토리 경로 -- 384개 중 2개 불일치

백틱으로 감싼 모든 `src/matched/`, `port/`, `config/`, `docs/`, `tools/`, `wiki/` 경로를
스크립트로 검사했다. 두 불일치 모두 의도된 플레이스홀더이며 그대로 둔다:

| 경로 | 페이지 | 해석 |
|---|---|---|
| `config/adm-kr/arm9/overlays/ovNNN/symbols.txt` | `engine/overlays.md:175` | `ovNNN`은 메타변수 |
| `port/build/acww.map` | `STYLE.md:54` | 빌드 산출물이며 커밋되지 않음 |

### 2.2 페이지 간 링크 -- 3개 깨짐, 모두 수정됨

페이지 간 마크다운 링크: 깨진 것 없음. 백틱으로 감싼 상대 페이지 참조: 세 개가 어디로도
해석되지 않았다.

| 잘못된 참조 | 페이지 | 수정 |
|---|---|---|
| `systems/save.md` | `data/items.md:167` | `../systems/save-data.md` |
| `systems/save.md` | `engine/file-system.md:209` | `../systems/save-data.md`, 그리고 문장을 "페이지에 속한다"에서 "에 작성되어 있다"로 다시 씀 |
| `systems/villagers.md` | `data/villagers.md:180` | `../systems/villagers.md` |
| `wiki/data/` (두 번) | `systems/economy.md:122, 159` | `../data/items.md` |

### 2.3 심볼 -- 구체적 불일치 8건, 모두 수정 또는 설명됨

백틱으로 감싼 568개의 `func_*`/`data_*`/SDK 이름 중 49개가
`config/adm-kr/arm9/**/symbols.txt`에 없다. 대부분은 SDK API 이름, 구조체 필드 또는 열거형
상수(`CARD_STAT_*`, `PXI_FIFO_TAG_*`, `TP_POINT`, `OS_IRQTable`, `DWC_*`,
`FS_RESULT_UNSUPPORTED`)로 STYLE 규칙 2가 허용하는 것이며, 여기에 `README.md`/`STYLE.md`의
메타변수가 더해진다. 구체적인 것들:

| 심볼 | 페이지 | 발견 사항 | 수정 |
|---|---|---|---|
| `func_02051c8c`, `func_020b4950` | `engine/text-and-messages.md:89` | 테이블은 이들을 `func_02051c8c_unk` / `func_020b4950_unk`, `kind:function(thumb,size=0x0,unknown)`으로 실제로 명시한다 | 이름 수정; 페이지의 "심볼 테이블에 전혀 없다"를 "실제 이름이 없다"로 교체 |
| `func_02225a90` | `systems/save-data.md:103`, `experiments/save-store-probe.md:19` | 그런 심볼은 없다; 해당 주소는 `config/adm-kr/arm9/overlays/ov003/symbols.txt`에서 `func_ov003_02225a90`이다. 포트의 정지 줄은 실제로 짧은 형태를 인용한다 | 두 페이지 모두 이제 정지 줄을 그대로 인용하고 그 옆에 심볼 테이블 해석을 제시한다 |
| `func_0209ded0` | `systems/events-and-calendar.md:22` | 그런 심볼은 없다; `config/adm-kr/arm9/symbols.txt`는 `0x0209ded0`을 `MB_GetBeaconRecvStatus`라고 명명하는데, 이는 날짜 변경 루틴의 피호출자일 수 없는 멀티부트 이름이다. `port/tools/known_callees.txt:253`은 `0x0209ded0`을 `func_02040c90`의 `f2`로 실제로 나열한다 | 주소는 유지(피호출자 목록이 근거)하고, 명명 위험은 이제 두 파일을 모두 인용하여 D12 사례로 서술 |
| `MATH_Rand16/32`, `MATH_InitRand16/32`, `OS_IsTickAvailable` | `systems/rng.md` | 이 ROM에 심볼이 없는 SDK 이름; 모두 `src/matched/`에서 `func_*` 이름으로 도달된다 | "무슨 일이 일어나는가" 맨 위에 명명 메모 추가 |
| `func_ov003_0222f458`, `func_ov004_0224522c`, `func_ov065_0227ef00`, `func_ov092_02299324` | 네 페이지 | 모듈의 `recovered.txt`에 존재하며, `tools/agent/target.py`가 이를 로드한다 | 그대로 유효; 1.4 참조 |
| `0x02239bf8ff` | `systems/villagers.md:108` | 아홉 자리 16진수 주소 -- `systems/town.md:97`이 인용하는 네 주소의 오타 | `0x02239bf8`, `0x02239c1c`, `0x02239c40`, `0x02239c58`로 수정 |
| 오버레이 대역 상단 `0x022a3240` | `engine/overlays.md`, `engine/memory-map.md` | 오버레이 심볼 테이블 전체에서 인용된 최대 함수 주소는 `0x022a31d8`이다 | 둘 다 `0x022a31d8`로 수정; 출처 문구를 "`kind:function` 줄에 대한 `addr:`"로 다듬음 |
| "27 overlays" | `data/villagers.md:122` | 페이지 자체의 표가 32개의 특수 캐릭터 오버레이(`ov004`, `ov045`-`ov055`, `ov068`, `ov070`-`ov088`)를 나열한다 | 32로 수정 |

### 2.4 모듈 레이블 -- 27행 오류, 모두 수정됨

가장 큰 단일 결함 부류다. 인용된 모든 심볼을 `config/adm-kr/arm9/**/symbols.txt`에 대해
해석하고 모듈 열을 다시 썼다:

| 페이지 | 행 수 | 잘못됨 -> 올바름 |
|---|---|---|
| `systems/time-and-rtc.md` | 11 | `RTC_Init`, `RtcCommonCallback`, `RtcBCD2HEX`, `RtcWaitBusy`, `RtcSendPxiCommand`, `RTC_GetTime`, `RTC_GetDateTimeAsync`, `RTC_GetDateAsync`/`GetTimeAsync`, `RTC_SetDateTime`, 세 개의 `Convert*`: `main` -> `autoload_2`. `OS_GetTick`/`OS_GetTickLo`: `main` -> `itcm`; `OS_InitTick`/`OSi_CountUpTick`: `main` -> `autoload_2`. 본문 출처도 일치하도록 수정 |
| `engine/threads-and-interrupts.md` | 9 | `OS_SaveContext`/`OS_LoadContext`, `OSi_IdleThreadProc`/`OS_Halt`, `OS_SetIrqFunction`: `autoload_2` -> `itcm`; `OS_IrqHandler`: `itcm/autoload_2` -> `itcm`; `CARDi_TaskThread`, `CARDi_Request`/`CARDi_OnFifoRecv`, `TP_WaitBusy`, `PXI_SetFifoRecvCallback`, `NNS_SndCaptureCreateThread`: `main` -> `autoload_2` |
| `systems/audio.md` | 14개 셀 | `main (NNS)` / `main (SND)` -> `autoload_2 (NNS)` / `autoload_2 (SND)`; `PXI_SendWordByFifo`: `main` -> `autoload_2` |
| `systems/rng.md` | 2 | `OS_GetLowEntropyData`, `MATH_CalcCRC8/16/32`: `main` -> `autoload_2` |
| `engine/boot-and-entry.md` | 1 | `OS_Halt`: `autoload_2` -> `itcm`, 표와 본문 출처 모두에서 |
| `systems/save-data.md` | 2개 그룹 | `card_common` / `card_backup`은 모듈이 아니라 번역 단위 이름이다; 이제 `autoload_2 (card_common)` / `autoload_2 (card_backup)` |

### 2.5 실행 디렉터리 -- 오케스트레이터를 위한 항목

이 워크트리에서는 `scratchpad/`가 보이지 않으므로, 이들 중 어느 것도 검사할 수 없었다.
위키가 언급하는 모든 서로 다른 `scratchpad/` 경로를 오케스트레이터가 실제 트리와 대조하여
확인할 수 있도록 나열한다(틀렸을 가능성이 가장 높은 것은 표시했다):

`scratchpad/cycle39/execution39-touch39-005/off`; `scratchpad/cycle40/iterate.sh`;
`scratchpad/cycle40/run_direct.py`; `scratchpad/cycle40/run_town.py`;
`scratchpad/cycle40/tap.sh`; `scratchpad/cycle40/runs/off-<name>`;
`scratchpad/cycle40/runs/rtc-000000`; `scratchpad/cycle40/runs/tap-D55b`;
`scratchpad/cycle40/runs/tap-D56` (+ `receipt.json`, `tap-D56-run.log`);
`scratchpad/cycle40/runs/tap-D57`; `scratchpad/cycle40/runs/tap-D58`;
`scratchpad/cycle40/runs/tap-D59`; `scratchpad/cycle40/runs/tap-D60` (+ `tap-D60-run.log`);
`scratchpad/cycle40/runs/tap-D61`; `scratchpad/cycle40/runs/tap-native`;
`scratchpad/cycle40/runs/town-R1`; `scratchpad/oracle/negctl.py`; `scratchpad/oracle/off`;
`scratchpad/oracle/rtc-000000` (+ `.json`); `scratchpad/oracle/tap-220`;
`scratchpad/oracle/tap-24700`; `scratchpad/oracle/tap-fullpad` (+
`compare-vs-tap-D56.txt`); `scratchpad/oracle/tap-window`; `scratchpad/save/fresh.sav`.

`scratchpad/` 접두사 없이 언급되어 페이지에서 철자조차 추측할 수 없는 것들:
`tap-D62` (`systems/dialogue.md`, `systems/input-and-touch.md`,
`experiments/touch-calibration.md`), `tap-interp` (`experiments/two-tap-town-recipe.md`),
`tap-D55` (`systems/player.md` -- `two-tap-town-recipe.md`는 `tap-D55b`를 인용한다는 점에
유의; 둘 중 하나는 아마 틀렸다), `menu-a`, `menu-b`, `long-a` (`systems/dialogue.md`,
`systems/economy.md`), `off-D4`..`off-D51` 및 `tap-D52`..`tap-D54` (여러 엔진 페이지, 항상
cycle40 로그 출처 안에서). **측정 필요: 실제 `scratchpad/cycle40/runs`와 `scratchpad/oracle`을
`ls`로 확인하고 대조하라.**

### 2.6 등급 태그

36개 콘텐츠 페이지에서 요약 절, 표, 펜스 블록을 제외한 모든 본문 문단에 대해 문단 단위 검사를
스크립트로 수행했다. **어떤 콘텐츠 페이지에서도 등급 태그가 없는 본문 문단은 없다.** "수정"하기
보다는 언급해 둘 가치가 있는 세 가지 약한 패턴:

- 여섯 페이지는 행별 등급 없이 "읽고 쓰는 데이터" 표 전체를 두고 그 아래에 한 줄 -- "모든 행은
  S이며, 앞 표의 파일에서 인용했다"(`systems/dialogue.md`, `player.md`, `villagers.md`,
  `events-and-calendar.md`, `weather-and-seasons.md`) -- 또는 짧은 등급 문단(`systems/town.md`,
  `economy.md`)만 두고 있다. STYLE은 행마다 등급을 요구한다. 이는 변호할 수 있는 축약이므로
  그대로 두지만, 검토자가 행을 삭제하더라도 규칙 안에 있다.
- 게임 메커니즘 패스가 작성한 `systems/` 페이지는 백틱 없이 인용하는데
  (`[S: func_02063bb4, main, port/shim/game/season.c]`) 다른 모든 페이지는 백틱을 쓴다. 순전히
  외형상의 문제이며; 스크립트 검사는 둘 다 처리한다.
- `data/` 페이지는 **S**를 `extract/adm-kr/`에서 읽어낸 바이트를 포함하도록 재정의한다. 이는
  `data/README.md`와 각 페이지의 등급 메모에 선언되어 있고 정직하지만, `data/` 페이지의 **S**가
  `engine/` 페이지의 **S**와 같은 주장이 아니라는 뜻이다. `extract/`가 이 워크트리에 없으므로,
  그 이미지 출처는 어느 것도 전혀 검사할 수 없었다.

## 3. 스타일

- **페이지 길이.** STYLE의 80-400 규칙은 스스로를 `engine/`, `systems/`, `data/`로 한정한다.
  해당하는 22개 페이지 모두 범위 안에 있다(가장 짧은 `data/fish-and-bugs.md` 155, 가장 긴
  `engine/display-objects.md` 257). 범위 밖이지만 짧은 것: `experiments/rng-determinism.md` 70과
  `experiments/off-recipe.md` 78, 그리고 모든 README와 용어집.
- **불필요한 하니스 태그 -- 수정됨.** 열네 페이지가 문자 그대로의 `</content>` 줄로 끝났고
  `systems/save-data.md`는 `</content>`에 `</invoke>`까지 있었다: `systems/{audio,
  input-and-touch, network, rng, save-data, time-and-rtc}.md` 전부와, README를 포함한 여덟 개의
  `experiments/` 파일 전부. 제거했다.
- **한국어.** `systems/dialogue.md`, `player.md`, `town.md`에 걸쳐 인용된 구절 열한 개와
  `engine/text-and-messages.md`에 하나. 모두 화면을 식별하는 데 쓰인 짧은 UI 문자열 하나씩이다
  (`당신 이름은?`, `마을사무소`, 다섯 선택지 메뉴). 가장 긴 것은 22자인 다섯 선택지 목적지
  줄이다. STYLE 규칙 5 안에 있다.
- **코드 목록.** 펜스 블록 여섯 개: `engine/file-system.md`와 `engine/graphics-pipeline.md`의
  환경 레시피, 그리고 `data/rom-layout.md`, `archives.md`, `villagers.md`, `items.md`,
  `fish-and-bugs.md`, `music.md`의 재유도 Python. STYLE 규칙 6은 코드 목록을 금지한다; STYLE
  자체 템플릿은 "확인 방법" 아래의 인라인 레시피를 명시적으로 허용하며, `data/README.md`는 Python
  스니펫을 승인한다. 어느 것도 ROM 코드의 전사가 아니므로 모두 그대로 둔다. 규칙과 관행이
  의도적으로 조정될 수 있도록 표시해 둔다.
- **호스트 주소.** 하나: `data/archives.md:27`이 VRAM 쓰기를 추적하며 "host `0x008b932f` /
  `0x008b939a`"를 인용한다. "host"라고 표시되어 있으며, STYLE 규칙 3이 막으려는 것이 바로 이것이다.
  `engine/memory-map.md`도 호스트 범위를 언급하지만, 이를 분리해 두기 위해 존재하는 "PC 포트가
  추가하는 것과 매핑하는 것" 절 안에서다. 둘 다 그대로 둔다.
- **`</content>` 건을 제외하면**, NDS 주소가 있어야 할 자리에 호스트 주소를 담은 페이지는 없다.

## 4. 용어집

이 패스 전에는 서른 행이었고, 하나를 제외하면 모두 올바르다; 열네 행을 추가했다.

**수정됨:** `channel` 행은 채널이 "`func_02003348`을 통해 열린다"고 말했다.
`engine/scenes-and-channels.md`는 `func_0202f134`를 정문으로 명시하고;
`systems/events-and-calendar.md:77`은 `func_02003348`을 명시한다. 둘 다 참이다 -- 두 개의
진입점으로, 하나는 씬의 채널 리스트용이고 하나는 특수 NPC 스케줄러의 준비된 방문객용이며, 둘 다
`func_020edc58`에서 끝난다. 이제 그 행은 그렇게 말하고 두 페이지를 모두 링크한다.

**추가됨**, 두 페이지 이상에서 쓰이지만 행이 없던 용어에 대해, 각각 그것을 정의하는 함수 또는
주소와 함께: `arena`, `BMG`, `deny list`, `display object`, `game heap`, `NARC`,
`OFF recipe`, `PXI tag`, `step gate`, `town recipe`, `TP_POINT`, `VBlank task list`,
`walk mode`. 이로써 용어집은 36줄에서 49줄이 되었다.

의도적으로 행을 주지 않은 용어: `overlay`, `scene`, `save image`, `player slot` (이미 있음);
`frame`, `grade`, `oracle`, `interpreter path` (이미 있거나 `README.md`/`STYLE.md`에 정의됨);
`shadow build`, `receipt`, `differential check` (게임 메커니즘 위키가 아니라 `docs/`에 속하는
포트 프로세스 용어).

## 5. 검사했으나 문제없었던 그 밖의 모든 것

- 이름에 주소가 인코딩된 모든 `func_XXXXXXXX` 이름은 심볼 테이블의 `addr:`와 일치한다 --
  568개 출처에서 불일치 0건. 페이지들이 이미 표시한 두 개(`0x0211e7c0`의 `RTC_SetDateTime`,
  `CARD_GetCurrentBackupType`)를 제외하면 위키에 D12 부류의 이름은 없다.
- `systems/README.md`는 같은 파일의 덧붙인 블록이 작성 완료라고 보고한 여섯 페이지를
  "Planned"로 나열했고, `input-and-touch.md`의 줄 수(231)는 열다섯 줄만큼 어긋나 있었다.
  **수정됨**: Planned 절은 사라졌고, 여섯 페이지는 링크와 함께 작성 완료로 나열되며, 변하기 쉬운
  줄 수 열은 삭제되었고, 실험 집계는 출처와 함께 서술된다.
- `engine/README.md`는 아홉 개의 엔진 페이지를 모두 명시하며 그 외는 없다.
- `data/README.md`는 여섯 개의 데이터 페이지를 모두 명시한다; `experiments/README.md`의
  실행됨 / 미실행 구분은 모든 페이지 자체의 **Status** 줄과 일치한다.

## 6. 오케스트레이터가 필요한 것

1. **2.5절의 실행 디렉터리 철자.** 워크트리에서는 검사할 수 없다. 특히 `tap-D55` 대
   `tap-D55b`, 그리고 `tap-D62`, `tap-interp`, `menu-a`, `menu-b`, `long-a`가
   `scratchpad/cycle40/runs/` 아래에 있는지 여부.
2. **`docs/kb/hybrid/runtime.md:158-160`은 오래되었다.** "40 shim files and `func_020b1b84`
   denied"라고 말하지만; `port/tools/interp_registry.py`의 `DENY_FILES`에는 49개의 베이스네임이
   있다. 그 옆의 "93 host services" 수치는 `verified-at 6ca48706`으로 날짜가 찍혀 있으며 여기서
   다시 유도하지 않았다. 위키는 이제 측정된 49를 인용한다; kb 페이지는 이 감사의 범위 밖이다.
3. **포트의 오래된 심 헤더.** `port/shim/game/chanlist.c:6-8`과
   `port/shim/gfx/pmflist.c:53, 607`은 `port/BOOT-STATE.md:1159-1171`이 철회한 뒤에도 여전히
   채널 189의 오브젝트를 "the FIELD render object"라고 부른다. 위키는 더 이상 이를 반복하지
   않는다; 헤더는 원천에서 수정되어야 하며, 그러지 않으면 다음 패스가 오류를 다시 들여올 것이다.
4. **`data/` 이미지 출처는 여기서 검증할 수 없다.** `extract/`가 이 워크트리에 없으므로, 여섯
   `data/` 페이지의 모든 파일 개수, 크기, 매직, 경로 템플릿 -- 대략 200개의 출처 -- 은 그대로
   믿고 받아들였다. `extract/`가 있는 리포지토리 루트에서 각 페이지 자체의 "확인 방법" 스니펫을
   다시 실행하라.
5. **`func_0205401c`의 `gSoundFlag`.** 측정 필요: 실행 전체에 걸쳐 그 전역 변수와 위/아래 화면
   내용을 함께 관찰하고, 비트 15 쓰기가 실제로 무엇을 하는지 밝혀라. 그때까지 `data/music.md`는
   이를 가설로 기록한다.
6. **`0x0209ded0`의 `func_0209ded0` / `MB_GetBeaconRecvStatus`.** 측정 필요: 해당 영역의
   경계 재절단, 또는 어느 이름이 잘못인지 보여주는 디스어셈블리.

## 관련 문서

- `../STYLE.md` -- 이 감사가 검사 기준으로 삼는 규칙
- `../README.md` -- 등급 정의
- `../glossary.md` -- 이 패스가 확장한 용어 표
