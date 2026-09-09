# 텍스트와 메시지
<!-- source: wiki/engine/text-and-messages.md -->

**요약.** 한국어판의 모든 대화 한 줄 한 줄은 `script/KOR/` 아래 1,791개의 개별 `.bmg` 파일 중 하나에
들어 있는 UTF-16 문자열이다. 게임은 화자의 성격과 메시지 레이블로 경로를 만들고, 그 파일 하나를 열어,
텍스트를 글리프 하나씩 그리는 타자기(typewriter)에 넘긴다. 글리프는 닌텐도 폰트 라이브러리에서
오지 않는다: 네 개의 자체 `font/font{A,B,C,D}` 비트맵 뱅크에서 오며, ROM에 함께 실린 라이브러리
폰트 스택은 Wi-Fi UI에만 쓰이는 것으로 보인다. 패킹된 메시지 뱅크도, 컴파일된 문자열 테이블도 없다.

## 무슨 일이 일어나는가

메시지 시스템은 오버레이에 있지 않다. 대화 창 클래스, 그 상태 테이블, 입력
처리, BMG 리더, 문자열 객체는 모두 항상 상주하는 ARM9 정적
모듈에 있다; 오버레이는 메시지를 *요청*할 뿐이다 [S: `port/TAXI-ROAD.md`, "The message system is not in
an overlay"]. 창은 `main`의 두 구간 `0x02066bd0`-`0x02068e00`과
`0x020a8100`-`0x020a9d60`을 차지한다 [S: `port/TAXI-ROAD.md`, subsystem table].

메시지는 레이블과 화자의 성격으로 지정된다. `func_0200366c`는 `bo_`, `ta_`,
`ge_`, `fu_`, `ko_`, `ha_`를 담은 `0x020d72a4`의 여섯 포인터 접두어 테이블로부터 키
`<personality>_<label>`을 만든다 [S: `func_0200366c`, `main`, `src/matched/func_0200366c.c`;
`port/TAXI-ROAD.md`, the message path trace]. `func_02067344`는 그 키를
`/script/KOR/message/<personality>/<group>/<name>_.bmg` 형식의 경로로 바꾼다
[S: `func_02067344`, `main`, `src/matched/func_02067344.c`]. `func_0206726c`는 `self+0xb14`에 있는
BMG 리더를 통해 그것을 열고 결과 텍스트를 `self+0x14ac`의 문자열 객체에
넘긴다 [S: `func_0206726c`, `main`, `src/matched/func_0206726c.c`]. 그 후 창은
여섯 상태의 멤버 함수 포인터 테이블로 구동된다; 상태 2의 업데이트가 버튼 누름이
한 줄을 넘기는 곳이다 [S: `func_02066dc4`, `main`, `src/matched/func_02066dc4.c`].

경로 템플릿은 ARM9 이미지에 컴파일되어 있으며, 다섯 개가 있고, 모두 같은 두세 개의
`%s` 구성 요소 위에 만들어져 있다: `%s/%s.bmg`, `%s/%s/%s.bmg`, `%s/%s/%s/%s_.bmg`,
`%s/%s/Other/%s_.bmg`, `%s/Other/%s_.bmg`, 그리고 선택 목록용의 별도 `/script/%s/select/%s.bmg`
[S: `extract/adm-kr/arm9/arm9.bin`, path-format string literals]. 언어를 담는 `%s`는
`KOR`이며, 이것이 실린 유일한 언어 디렉터리다
[S: `extract/adm-kr/files/script/`, one subdirectory].

### 메시지 트리

`script/KOR/`는 일곱 그룹에 총 1,581,466바이트의 `.bmg` 파일 1,791개를 담고 있다
[S: `extract/adm-kr/files/script/KOR/`, recursive census]. `message/`가 그중 1,526개이며,
아홉 개의 성격 디렉터리로 나뉜다: `bo`, `ta`, `ge`, `fu`, `ha`, `ko`, 그리고 `sp`, `obj`,
`Other` [S: `extract/adm-kr/files/script/KOR/message/`, subdirectory listing]. `bo`와 `ta`는
같은 이름의 열여덟 개 하위 디렉터리 — `3p`, `ai`, `ap`, `etc`,
`ev`, `q`, `q01`..`q07`, `q09`..`q12`, `tsu` — 에 각각 242개의 파일을 담고 있으며, 이것이 네 구성 요소
템플릿의 두 번째 `%s`다 [S: `extract/adm-kr/files/script/KOR/message/bo/`,
`extract/adm-kr/files/script/KOR/message/ta/`, subdirectory listings and counts]. 나머지
그룹은 `mail/` (`msg`, `ps`, `super`에 168개), `mailz/` (`msga`, `msgb`, `psz`,
`superz`에 48개), `string/` (개별 파일 36개), `bbs/` (10개), `select/` (2개), `2d/` (1개)이다
[S: `extract/adm-kr/files/script/KOR/`, per-directory census]. `string/`은 `obj_etc_fish.bmg`와
`obj_etc_insect.bmg`를 포함한 아이템과 생물 이름 뱅크가 있는 곳이다
[S: `extract/adm-kr/files/script/KOR/string/`, file names].

### BMG 컨테이너

1,791개 중 1,790개의 파일은 ROM의 `LZ77` 래퍼 뒤에 압축되어 있다; 유일하게 압축되지 않은
`script/KOR/message/Other/test_.bmg`가 나머지가 압축 해제되었을 때의 형식을 보여 준다
[S: `extract/adm-kr/files/`, first-four-bytes census]. 그 헤더는 `MESGbmg1`, 정확히 일치하는 파일 크기
필드, 블록 수 2, 그리고 인코딩 바이트 2 — UTF-16의 BMG 코드 — 이다
[S: `extract/adm-kr/files/script/KOR/message/Other/test_.bmg`, bytes 0..17]. 두
블록은 `INF1` (12바이트짜리 항목 16개)과 `DAT1` (800바이트)이며, `DAT1`의 페이로드는
첫 null 항목 뒤에 오는 UTF-16LE 텍스트다 [S: same file, `INF1` +8, `DAT1` payload]. 모든
`.bmg`는 ROM의 다른 6,330개 압축 파일이 쓰는 `0x10` 대신 압축 타입 `0xf7`을 가지므로,
메시지 파일은 자체 압축 경로를 가진 유일한 에셋 부류다
[S: `extract/adm-kr/files/`, byte-4 histogram over all `LZ77`-wrapped files].

게임 자체의 BMG 리더는 ROM에서 이름이 없다: 테이블 어디의 어떤 심볼도
`bmg`, `msg`, `mes` 또는 다른 텍스트 시스템 단어를 포함하지 않으며, `src/matched/`에 대한
`BMG`, `MESG`, `INF1`, `DAT1`, `MID1`, `STR1` 내용 검색은 아무것도 반환하지 않는다
[S: `config/adm-kr/arm9/**/symbols.txt`, name sweep; `src/matched/`, content search;
`port/TAXI-ROAD.md`, "This ROM names things by asset path"]. 게임 쪽 텍스트 함수는 모두
`func_02xxxxxx`다.

### 문자 코드

텍스트는 16비트 코드로 글리프 계층에 도달한다. 문자열 순회는 이를 **빅 엔디언**으로 —
바이트 쌍에 대해 `(p[1] << 8) | p[0]` — 읽고 각각을 가상 메서드에 넘긴다
[S: `func_020a9368`, `main`, transcribed in `port/shim/game/glyphcode.c`, header]. 코드는
유니코드다: 포트의 라이브 프로브가 `0xC548`, `0xB155`, `0xD558`을 기록했는데, 이는 한글
음절 안, 녕, 하이다 [E: `port/shim/game/glyphprobe.c`, header, recorded probe output]. 코드에
글리프가 없으면 조회는 `0xFF20`, FULLWIDTH COMMERCIAL AT으로 폴백한다
[S: `func_020512d4`, `main`, `src/matched/func_020512d4.c`; `port/shim/game/glyphcode.c`,
header]. SDK 자체의 UTF-16 분리기 `NNSi_G2dSplitCharUTF16`은 `0x02104cec`에 존재하지만
게임 자체의 경로가 아니라 라이브러리 스택에 속한다
[S: `config/adm-kr/arm9/autoload_2/symbols.txt`; `src/matched/NNSi_G2dSplitCharUTF16.c`].

실제 이름을 가진 유일한 문자열 프리미티브는 `autoload_2`의 NitroSDK 말단 함수 넷이다:
`STD_ConcatenateString` `0x02128d58`, `STD_GetStringLength` `0x02128d88`, `STD_CopyLString`
`0x02128db0`, `STD_CopyString` `0x02128dec`
[S: `config/adm-kr/arm9/autoload_2/symbols.txt`; `src/matched/STD_CopyString.c` and siblings].
게임 자체의 16비트 인식 길이 루틴은 실제 이름이 없다 — 테이블은 이를
`func_02051c8c_unk`와 `func_020b4950_unk`라 부르며, 각각 이름 있는 두 심볼 사이의 작은
틈에 있는 크기 0의 `unknown` 항목이다 [S: `config/adm-kr/arm9/symbols.txt`, both rows
`kind:function(thumb,size=0x0,unknown)`; `port/shim/game/u16len.c`,
`port/shim/game/textlen.c`, headers].

### 폰트

게임의 폰트는 네 서체로, 각각 `font/` 아래 `head`, `attr`, `img` 파일의 고정된 삼중쌍이다
[S: `extract/adm-kr/files/font/`, 12 files]. 각 `head`는 정확히 8바이트이며
32비트 글리프 수 뒤에 두 개의 16비트 치수가 오는 것으로 읽힌다: fontA는 9x16에 3,314 글리프, fontB는
7x8에 3,891, fontC는 16x16에 19, fontD는 8x8에 15
[S: `extract/adm-kr/files/font/font{A,B,C,D}_head.bin`, all 8 bytes]. `img` 크기는
픽셀당 1비트 비트맵임을 확인해 준다: fontC의 16x16 글리프 19개는 정확히 608바이트이고 fontD의 8x8 15개는
정확히 120바이트로, 둘 다 `count * w * h / 8`에 남는 것이 없다
[S: `extract/adm-kr/files/font/fontC_img.bin` 608 bytes, `fontD_img.bin` 120 bytes]. fontA의 3,314라는
수는 라이브로도 확인된다: 포트의 프로브가 `font 0x021c8230 glyphs 3314`를 출력했다
[E: `port/shim/game/glyphprobe.c`, header, recorded probe output].

`func_02051794`가 그 네 삼중쌍의 로더다 [S: `func_02051794`, `main`,
`src/matched/func_02051794.c`; `port/TAXI-ROAD.md`, ACWW font loader row]. `func_020516b8`은
속성 테이블에 대한 코드-글리프 인덱스 조회로 실패 시 -1을 반환하고
[S: `func_020516b8`, `main`, `src/matched/func_020516b8.c`], `func_0205171c`는 글리프 하나의
너비 레코드를 가져오며 [S: `func_0205171c`, `main`, `src/matched/func_0205171c.c`], `func_020512d4`와
`func_0205156c`는 조회를 `0xFF20` 폴백으로 감싼다
[S: `src/matched/func_020512d4.c`, `src/matched/func_0205156c.c`]. `func_020a8e8c`는
`self+0x7c`의 플래그에 따라 두 래퍼 사이를 디스패치한다 [S: `func_020a8e8c`, `main`,
`src/matched/func_020a8e8c.c`]. fontA의 속성 테이블은 LZ77로 압축되어 있으며
`{u16 code, u8 width, u8}` 항목 3,314개를 담고 있다 [S: `port/shim/game/glyphcode.c`, header].

NitroSystem G2D 폰트 스택도 ROM에 있다 — `0x02102f1c`부터 `0x02104d00`까지 33개의
함수로, 모두 바이트 매칭되었으며, `NNS_G2dFontFindGlyphIndex` `0x021031b8`,
`NNS_G2dCharCanvasDrawChar` `0x021038d4`, `DrawGlyph1D` `0x02103e2c`, `DrawGlyphLine`
`0x02104050`, `LetterChar` `0x02104208`, `0x02104710`-`0x02104978`의 네 `NNSi_G2dTextCanvasDraw*` 진입점,
그리고 `NNSi_G2dUnpackNFT` `0x02104a28`을 포함한다
[S: `config/adm-kr/arm9/autoload_2/symbols.txt`; `src/matched/NNS_G2dCharCanvasDrawChar.c` and
siblings]. 이는 게임 본체에는 죽은 무게로 보인다: 이 무리에서 0x224바이트로 가장 큰 렌더러인
`DrawGlyph1D`는 ROM 어디에도 호출 지점이 없고,
`NNS_G2dFontFindGlyphIndex`와 `NNS_G2dCharCanvasDrawChar`는 `autoload_2`
자체와 Wi-Fi 유틸리티 오버레이인 `ov001`에서만 호출된다 [H: `port/TAXI-ROAD.md`, marked INFERENCE
there; the supporting negative is that `NFTR`, the format `NNSi_G2dUnpackNFT` reads, appears in
exactly one file in the whole ROM — `dwc/utility.bin`]. 이를 확정하려면 일반 대화 상자가 화면에 있는 동안
`ACWW_INTERP=1`로 호출 지점 트레이스를 해야 한다.

### 메시지 박스 아트워크

창 자체의 그래픽은 `a_mes/`의 열여덟 개 개별 파일로,
`a_mes[<variant>]_<layer>_<kind>.bin` 패턴에 `_ncg` 타일, `_ncl` 팔레트, `_nsc`
스크린 맵으로 이름 지어져 있으며, 박스 스킨마다 한 세트에 네 개의 "ten" 포인터 스프라이트 변형과 타이틀 플레이트가 있다
[S: `extract/adm-kr/files/a_mes/`, file names and sizes; `extract/adm-kr/arm9/arm9.bin`, the 14
`/a_mes/...` path literals]. 타이틀 플레이트 멤버는 `ov147`이 요청한다
[S: `extract/adm-kr/arm9_overlays/ov147.bin`, four `/a_mes/a_mes_ttl_*` path literals].

### 키보드

텍스트 *입력*은 세 오버레이 `ov095`, `ov124`, `ov126`에 있는 별개의 시스템으로, 합쳐서 265개의 함수다
[S: `port/TAXI-ROAD.md`, keyboard trio row]. 한글 입력 방식 자체는 라이브러리가 아니라
게임 자체의 코드다: `autoload_2`의 `func_020efc74`는 0x7d0바이트짜리 화면
키보드 상태 머신으로, 이에 해당하는 라이브러리 소스는 어디에도 없다
[S: `func_020efc74`, `autoload_2`, `src/matched/func_020efc74.c`, header]. 키보드 아트워크는
`menu/han/` (한글 페이지 16개)과 `menu/chat2/` (키 페이지 11개)다
[S: `extract/adm-kr/files/menu/han/` 34 files, `extract/adm-kr/files/menu/chat2/`;
`extract/adm-kr/arm9_overlays/ov124.bin` and `ov095.bin`, path literals]. 텍스트 시스템의
다른 모든 것과 마찬가지로, 어느 것도 이름이 없다: ROM 전체에서 `kbd`, `keyboard`, `namein`,
`hangul`, `ime`, `moji`, `kana`, `yomi`를 검색하면 심볼이 0개 반환되며, 키보드는
그 에셋으로 찾아냈다 [S: `port/TAXI-ROAD.md`, "This ROM names things by asset path"].

마을 이름 키보드의 스타일러스 디스패처는 `func_ov126_022a1228`로, `ov126` 재배치
`0x022a1ff0 -> 0x022a1229`를 통해 함수 포인터로만 설치된다
[S: `port/shim/ui/w40_ov126_022a1228_gateprobe.c`, header]. 그 게이트는 현재 터치
좌표를 `autoload_3`의 두 워드 `0x021f6c58` (X)과 `0x021f6c54` (Y)에서 읽는다
[S: `config/adm-kr/arm9/overlays/ov126/relocs.txt`, resolving the pool words at `0x022a0848` and
`0x022a084c`; `port/shim/ui/w90_ov126_022a07e8_touchwords.c`, header]. 히트 테스트는
`sub_229c54c`이고 인덱스-키 id 조회는 `sub_229c448`로, 둘 다 측정된 경로에서 상주 여부로
`ov095`로 해석되며, 키 id `0x100`이 확인 키다
[S: `src/matched/func_ov126_022a04e8.c`; `port/shim/ui/w90_kbd_hittest_dispatch.c`, header].

## 어디에 있는가

| 함수 또는 심볼 | 모듈 | 역할 | 등급/출처 |
|---|---|---|---|
| `func_0200366c` | `main` | `<personality>_<label>`을 만든다 | S: `src/matched/func_0200366c.c` |
| `func_02067344` | `main` | 키 → `.bmg` 경로 | S: `src/matched/func_02067344.c` |
| `func_0206726c` | `main` | 파일을 열고 문자열 객체에 넘긴다 | S: `src/matched/func_0206726c.c` |
| `func_02066dc4` | `main` | 대화 상태 2: 버튼으로 진행 | S: `src/matched/func_02066dc4.c` |
| `func_02051794` | `main` | `font{A..D}_{head,attr,img}`를 로드한다 | S: `src/matched/func_02051794.c` |
| `func_020516b8` | `main` | 코드 → 글리프 인덱스, 실패 시 -1 | S: `src/matched/func_020516b8.c` |
| `func_020512d4` / `func_0205156c` | `main` | `0xFF20` 폴백이 있는 조회 | S: `src/matched/func_020512d4.c` |
| `func_020a8e8c` | `main` | 두 조회 중 하나를 고른다 | S: `src/matched/func_020a8e8c.c` |
| `func_020efc74` | `autoload_2` | 한국어 IME 상태 머신 | S: `src/matched/func_020efc74.c` |
| `NNSi_G2dSplitCharUTF16` `0x02104cec` | `autoload_2` | SDK UTF-16 커서 스텝 | S: `src/matched/NNSi_G2dSplitCharUTF16.c` |
| `NNS_G2dFontFindGlyphIndex` `0x021031b8`, `GetGlyphIndex` `0x0210325c` | `autoload_2` | SDK 코드 맵 (DIRECT/TABLE/SCAN) | S: `src/matched/NNS_G2dFontFindGlyphIndex.c`, `GetGlyphIndex.c` |
| `NNSi_G2dUnpackNFT` `0x02104a28` | `autoload_2` | `NFTR` 폰트를 언팩한다 | S: `src/matched/NNSi_G2dUnpackNFT.c` |
| `STD_CopyString` `0x02128dec`와 형제 셋 | `autoload_2` | 8비트 문자열 말단 함수 | S: `src/matched/STD_CopyString.c` |
| `func_ov126_022a1228` | `ov126` | 마을 이름 키보드 터치 디스패치 | S: `port/shim/ui/w40_ov126_022a1228_gateprobe.c` |
| `sub_229c54c` / `sub_229c448` | `ov095` (상주 여부로) | 키 히트 테스트 / 키 id | S: `src/matched/func_ov126_022a04e8.c` |

## 읽고 쓰는 데이터

| 주소 또는 필드 | 의미 | 쓰는 쪽 | 읽는 쪽 |
|---|---|---|---|
| `0x020d72a4` | 성격 접두어의 여섯 포인터 테이블 | ROM 데이터 | `func_0200366c` [S: `port/TAXI-ROAD.md`] |
| `self+0xb14` | 창의 BMG 리더 | 창 생성 | `func_0206726c` [S: `src/matched/func_0206726c.c`] |
| `self+0x14ac` | 창의 문자열 객체 | `func_0206726c` | 타자기 [S: `src/matched/func_0206726c.c`] |
| `self+0x7c` | 어느 글리프 조회가 실행될지 선택 | 창 설정 | `func_020a8e8c` [S: `src/matched/func_020a8e8c.c`] |
| `0x021c8230` | 로드된 fontA 레코드 | `func_02051794` | 글리프 조회들 [E: `port/shim/game/glyphprobe.c`] |
| `0x020d1df4` | 각 8바이트짜리 세 항목 글리프 집합 테이블 | ROM 데이터 | `func_020ad4fc` [S: `port/shim/game/fontsetup.c`, header] |
| `0x021f49a0` | 0x18바이트짜리 글리프 표면 서술자 셋 | `func_020ad4fc` | 캔버스 등록 [S: `port/shim/game/fontsetup.c`] |
| `0x021f6c58` / `0x021f6c54` | 현재 스타일러스 X / Y | `port/shim/input/touch.c`; 하드웨어에서는 터치 샘플러 | 키보드 게이트 [S: `config/.../ov126/relocs.txt`] |
| BMG `INF1` 항목, 12바이트 | 메시지 레코드 하나 | 패커 | BMG 리더 [S: `.../Other/test_.bmg`] |

## 확인 방법

전체 체인을 실행해 보는 알려진, 재현 가능한 결함이 있다. 수정 전에는 메뉴 박스와
말풍선이 올바른 위치, 색, 커서, 줄바꿈, 박스 크기로 렌더링되었지만
모든 글리프가 동일했다; 그 비트맵을 네 폰트의 전체 7,239개 글리프와 대조했더니
정확히 하나에 맞았다 — fontA 글리프 383, 즉 `0xFF20`
[E: `port/VISIBLE-STATE.md`, the glyph observation]. 원인은 `func_020a8e8c`가 호출자가 `r1`에
넘긴 문자 코드를 떨어뜨려서, 모든 코드가 실패하고 모든 코드가 폴백한 것이었다
[S: `port/shim/game/glyphcode.c`, header; `port/tools/overrides.txt`, the `func_020a8e8c` row].
수리 후 프로브는 `0xC548 -> 2313`, `0xB155 -> 1306`, `0xD558 -> 3167`을 출력했다
[E: `port/shim/game/glyphprobe.c`, header].

그 검사를 다시 실행하려면, `port/shim/game/glyphprobe.c`의 비활성화된 프로브를 활성화하고(`#if 0`이며
`port/tools/overrides.txt`에 없다), `python port/tools/pipeline.py`로 다시 빌드한 다음,
대화 상자에 도달하는 아무 레시피나 실행한다. 예상: 하나의 쌍이 반복되는 것이 아니라 서로 다른
`code in -> index out` 쌍의 흐름.

아무것도 실행하지 않고 BMG 컨테이너를 검증하려면,
`extract/adm-kr/files/script/KOR/message/Other/test_.bmg`의 첫 48바이트를 읽는다: `MESGbmg1`, 파일 크기 1,056, 블록
수 2, 인코딩 2, 그다음 `INF1` (224바이트, 12바이트짜리 항목 16개)과 `DAT1` (800바이트).

## 가설

- **NNS G2D 폰트 스택은 게임 본체에서는 죽어 있고 Wi-Fi UI에만 쓰인다.** 근거는
  호출 지점 스캔과 `NFTR`이 `dwc/utility.bin`에만 등장한다는 것이다
  [H: `port/TAXI-ROAD.md`, marked INFERENCE]. 대화 상자를 여는 레시피와 WFC 화면(`ov146`)을 여는
  레시피에서 `ACWW_INTERP=1`로 `NNS_G2dCharCanvasDrawChar` `0x021038d4`에 대한 호출을
  추적하고 비교하여 확정한다.
- **`0xf7` 압축 타입은 `.bmg`에 특유하다.** 1,790개의 압축된 메시지 파일 모두가 이를
  가지며 다른 파일은 어느 것도 갖지 않는다 [S: `extract/adm-kr/files/`, byte-4 histogram]. 이것이
  다른 알고리즘인지 난독화인지는 알 수 없다. 메시지 열기 시점에 압축 해제된
  버퍼를 캡처해 `MESGbmg1`로 시작하는지 확인하여 확정한다.
- **문자열 순회는 빅 엔디언인데 BMG 페이로드는 UTF-16LE다.** `func_020a9368`은
  `(p[1] << 8) | p[0]`을 조합하지만 [S: `port/shim/game/glyphcode.c`], `test_.bmg`의 `DAT1` 페이로드는
  리틀 엔디언으로 읽힌다 [S: same file]. 리더가 로드 시 바이트를 스왑하거나, 두
  읽기 중 하나가 다른 버퍼에 대한 것이다. `func_0206726c`가 반환한 직후 `self+0x14ac`의 문자열
  객체 버퍼의 첫 여덟 바이트를 덤프하여 확정한다.
- **프레임별 대화 드라이버 `func_02068144`와 문자열 순회 `func_020a9368`은 매칭된 소스가
  없다.** 이들은 산문에서만 이름이 언급된다 [H: `port/TAXI-ROAD.md`]. 차분 검사 큐에
  추가하여 확정한다.
- **각 성격 아래의 열여덟 개 `q*` 하위 디렉터리는 대화 주제이고,
  `3p`/`ai`/`ap`/`etc`/`ev`/`tsu` 형제들은 범주다.** 이는 이름만으로 추론한 것이다
  [H]. 긴 마을 실행에 걸쳐 `func_02067344`에서 조합된 경로를 기록하고
  각 디렉터리를 화면 상황과 연관 지어 확정한다.

## 관련 문서

- `../data/archives.md` — `MESGbmg1`과 `LZ77` 컨테이너의 상세.
- `../data/rom-layout.md` — `script/`, `font/`, `a_mes/`, `menu/han/`이 있는 곳.
- `graphics-pipeline.md` — 글리프 비트맵이 픽셀이 되는 방법.
- `file-system.md` — `/script/KOR/.../x_.bmg`가 바이트가 되는 방법.

## 확정됨: 청크 방식(0xf7) 메시지 파일의 압축을 누가 푸는가

범용 로더(`func_02064b2c`, `func_020649ac`)는 콘솔에서도 포트에서도 타입 바이트로
디스패치하지 않는다; 이들은 `.bmg`를 결코 보지 않는다. 메시지 창의 리더들
(`func_020a9540`..`func_020a982c`)은 `func_02064658` (main, Thumb, 0x194바이트)을 거치는데, 이는
`(type & 0xf0) == 0xf0`을 검사하고, 청크 크기를 `0x20 << (type & 0xf)`로 잡으며(0xf7이면 4,096),
u16 누적 테이블을 읽고, 한 청크 캐시로 요청된 범위를 덮는 청크만
압축 해제하는 임의 접근 리더다; 타입 0x00 청크는 복사된다
[S: `func_02064658` disassembly; port/shim/game/lzread.c]. 인터프리터 경로에서는
그 ROM 코드가 실행되어 등록된 호스트 `MI_UncompressLZ8`을 청크당 한 번 호출하며,
그래서 마을 대화가 올바르게 렌더링된다 [E: `tap-D63` 37,500]. 픽스처:
`port/tools/test_lz77_f7.py` (검사 3개, 보정 2개)는 세 청크짜리 파일을
lzread.c + lz77.c로 독립적인 Python 디코더와 대조하며 디코딩한다. 범용 로더는 이제 0xf7 컨테이너가
넘겨지는 일이 있으면 일회성 증거(witness)를 출력한다.
