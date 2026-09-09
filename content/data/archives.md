# 아카이브와 컨테이너 포맷
<!-- source: wiki/data/archives.md -->

**요약.** ROM의 거의 모든 파일은 4바이트 `LZ77` 매직과 그 뒤의 표준 NitroSDK 압축 헤더로 감싸여 있고,
그 래퍼 안에는 소수의 Nintendo 컨테이너 포맷 중 하나가 들어 있다: `NARC` 아카이브, `nsb*` 3D 리소스
계열, `MESGbmg1` 메시지 뱅크, 그리고 하나의 `SDAT` 사운드 아카이브. 래퍼를 아는 것이 파일 트리를 읽을
수 있는 데이터로 바꾸는 열쇠이다: 9,508개 파일 중 8,120개가 `LZ77`로 시작하며 압축을 풀기 전까지는
실제 타입에 대해 아무것도 드러내지 않는다.

등급 주석: 이 페이지의 **S**는 심볼 테이블 / 매칭된 소스와 추출된 ROM 이미지에서 직접 읽어낸 바이트
둘 다를 포함한다; 이미지 출처는 항상 파일과 필드를 명시한다.

## 무슨 일이 일어나는가

9,508개 파일 중 8,120개가 네 개의 ASCII 바이트 `LZ77`로 시작한다 [S: `extract/adm-kr/files/`,
first-four-bytes census across all files]. 그 매직 뒤의 워드는 통상적인 NitroSDK 압축 헤더로, 하위
바이트 = 타입, 상위 24비트 = 압축 해제 크기이다. 6,330개의 파일은 SDK의 LZ77인 타입 `0x10`을 가진다
[S: same census, byte 4 histogram]. 나머지 1,790개는 타입 `0xf7`을 가지며, 그 모두가 `.bmg` 메시지
파일이다 [S: same census; the 1,790 non-`0x10` files are exactly the compressed subset of the 1,791
`.bmg` files]. 크기 필드는 두 경우 모두 그럴듯하게 읽힌다 — `script/KOR/select/select.bmg`는
디스크에서 2,080바이트이고 크기 필드가 `0x001380` = 4,992이며, `anm/0/0.nsbca`는 2,242바이트에
`0x000a34` = 2,612이다 [S: `extract/adm-kr/files/`, first 8 bytes of each file].

포트 자체의 압축 해제기는 SDK 루틴 `MI_UncompressLZ8`이며, 포트가 살아남은 모든 직접 텍스처 바이트를
거슬러 추적해 도달한 곳이 바로 여기이다 [S: `docs/kb/port/render.md`, VRAM
last-write tracing, host `0x008b932f` / `0x008b939a` in `port/shim/gfx/lz77.c`].

감싸이지 *않은* 1,388개의 파일은 자신의 고유 매직을 직접 보여주며, 아래의 포맷 목록은 그렇게 얻은
것이다 [S: `extract/adm-kr/files/`, first-four-bytes census].

### NARC 아카이브 (`.arc`)

229개의 `.arc` 파일은 비압축으로 저장되어 있고 `NARC`로 시작한다 [S: census]. 헤더는 NitroSDK의 일반
헤더이다: 매직, 바이트 순서 표식 `FFFE`, 버전 `0100`, 전체 파일 크기, 헤더 크기 `0x0010`, 블록 수 3
[S: `extract/adm-kr/files/str/bsize.arc`, bytes 0..16 read as
`NARC`, `fe ff`, `00 01`, `0x1730`, `0x0010`, `0x0003`]. 세 블록은 `BTAF`(파일 할당 테이블),
`BTNF`(파일 이름 테이블), `GMIF`(패킹된 이미지)이다
[S: `extract/adm-kr/files/str/bsize.arc`, `bg/grd_anm.arc`, `str/npcHsX.arc`, block magics at
the header-size offset]. `BTAF`의 첫 하프워드는 항목 수이다: `str/bsize.arc`는 30개의 하위 파일을,
`str/npcHsX.arc`는 7개를, `bg/grd_anm.arc`는 6개를 담는다 [S: same files, `BTAF` +8].

`GMIF` 안의 하위 파일들은 그 자체로 고유한 매직을 가진 리소스 파일이다 — `bg/grd_anm.arc`의 첫 하위
파일은 `BMA0` 머티리얼 애니메이션이고 `str/npcHsX.arc`의 것은 `BMD0` 모델이다
[S: same files, first four bytes of the `GMIF` payload].

가구와 방 오브젝트 디렉터리는 `.arc`와 같은 이름의 `.nsbtx`를 짝지으며, 하나는 지오메트리를, 다른
하나는 텍스처 세트를 담는다: `ftr/0/0/0000.arc` 옆에 `ftr/0/0/0000.nsbtx`, `roomObj/obj_cafe1.arc`
옆에 `roomObj/obj_cafe1.nsbtx` [S: `extract/adm-kr/files/ftr/0/0/`,
`extract/adm-kr/files/roomObj/`, directory listings]. 코드는 이들을 하나의 템플릿 쌍
`/ftr/%d/%d/%04x.arc`와 `/ftr/%d/%d/%04x.nsbtx`로부터 쌍으로 연다
[S: `extract/adm-kr/arm9_overlays/ov004.bin`, path-format string literals].

### `nsb*` 3D 리소스 계열

3D 리소스는 NitroSystem G3D 블록 매직을 사용한다: `BMD0` 모델(767개의 `.nsbmd` 중 243개 비압축), `BTX0`
텍스처(3,017개의 `.nsbtx` 중 515개), `BCA0` 조인트 애니메이션(591개의 `.nsbca` 중 80개), `BTP0` 텍스처
패턴 애니메이션(391개의 `.nsbtp` 중 1개), `BVA0` 가시성 애니메이션(42개의 `.nsbva` 중 1개), `BTA0`
텍스처 SRT 애니메이션(6개의 `.nsbta` 중 2개), 그리고 `BMA0` 머티리얼 애니메이션(`.nsbma` 4개 전부)
[S: `extract/adm-kr/files/`, census by extension and magic]. 이들은 `autoload_2`의 NNS G3D 로더가
소비하는 리소스이다: `NNS_G3dGetResDataByName`(`0x021079ac`)은 블록 딕셔너리를 순회하고,
`NNS_G3dBindMdlTex`(`0x02104f38`)는 모델의 이름 붙은 텍스처를 `nsbtx`에 바인딩하며,
`NNS_G3dGetJntAnmSet` / `GetTexPatAnmSet` / `GetTexSRTAnmSet` / `GetVisAnmSet`(`0x02107b28`,
`0x02107bdc`, `0x02107ba0`, `0x02107cd4`)은 각각 애니메이션 세트 하나를 가져온다
[S: `config/adm-kr/arm9/autoload_2/symbols.txt`; `src/matched/NNS_G3dGetResDataByName.c`,
`src/matched/NNS_G3dBindMdlTex.c`].

### `MESGbmg1` 메시지 뱅크 (`.bmg`)

ROM에서 정확히 하나의 `.bmg`만 비압축으로 저장되어 있는데, `script/KOR/message/Other/test_.bmg`이며,
나머지 1,790개가 압축 해제되면 갖게 되는 포맷을 보여준다 [S: `extract/adm-kr/files/`, magic census].
그 헤더는 `MESGbmg1`, 파일과 정확히 일치하는 32비트 파일 크기(1,056), 블록 수 2, 인코딩 바이트 2이다
[S: `extract/adm-kr/files/script/KOR/message/Other/test_.bmg`,
bytes 0..17]. 두 블록은 `INF1`(224바이트)과 `DAT1`(800바이트)이다
[S: same file, block magics at offset 32]. `INF1`의 헤더는 각 12바이트인 16개의 항목을 알려주고,
`DAT1`의 페이로드는 null 항목으로 시작한 뒤 UTF-16LE 텍스트가 이어진다 [S: same file, `INF1`
+8 = `0x0010`, `0x000c`; `DAT1` payload bytes]. 인코딩 2와 UTF-16 페이로드는 ROM이 탑재한 SDK 헬퍼
`0x02104cec`의 `NNSi_G2dSplitCharUTF16`과 일치한다
[S: `config/adm-kr/arm9/autoload_2/symbols.txt`; `src/matched/NNSi_G2dSplitCharUTF16.c`].

패킹된 메시지 뱅크는 없다: 1,791개의 `.bmg` 파일 전부가 낱개이며 경로로 개별적으로 열린다
[S: `extract/adm-kr/files/script/`, recursive census; `extract/adm-kr/arm9/arm9.bin`,
the five `%s/...bmg` path templates]. 메시지 키가 어떻게 그 경로 중 하나가 되는지는
`../engine/text-and-messages.md`를 참조한다.

### `SDAT` (`sound_data.sdat`)

단일 사운드 아카이브는 NitroSDK `SDAT` 컨테이너로, 10,704,768바이트, 헤더 크기 64이다
[S: `extract/adm-kr/files/sound_data.sdat`, bytes 0..16]. `SYMB` 심볼 블록이 없으므로(오프셋 0, 크기 0)
출시된 ROM에서 사운드 항목들은 이름을 갖지 않는다; `INFO`는 `0x40`에 24,712바이트, `FAT `는 `0x60c8`에
24,188바이트, `FILE`은 `0xbf44`에 10,655,804바이트이다 [S: same file, the four block offset/size pairs
at offset 16]. `INFO` 내부의 레코드 개수는 `music.md`를 참조한다.

### 2D 메뉴 포맷 (`.bch` / `.bsc` / `.bpl`)

`menu/`는 어떤 Nintendo 컨테이너도 아닌 자체적인 세 가지 확장자 규약을 사용한다: `.bch`
캐릭터/타일 그래픽, `.bsc` 스크린 맵, `.bpl` 팔레트로, 385 / 177 / 175개의 파일이다
[S: `extract/adm-kr/files/menu/`, extension census]. 이들은 자체 매직을 갖지 않는다 — 비압축된 것들은
곧바로 데이터로 시작한다 [S: same census, magic column shows raw byte patterns
such as `00000000` and `DDDD`]. 같은 삼중 구성이 낱개 `.bin` 디렉터리들에서 더 오래된 `nc*` 표기로
나타난다: `a_mes/`는 파일 이름을 `_ncg`(타일), `_ncl`(팔레트), `_nsc`(스크린)로 붙이며
[S: `extract/adm-kr/files/a_mes/`, file names], `sky/`도 같은 접미사를 사용한다
[S: `extract/adm-kr/files/sky/`, file names].

### `SPA ` 파티클

파티클 아카이브 하나, `spl/spl.spa`, 61,212바이트, 리틀 엔디언으로 저장된 매직 `SPA `
[S: `extract/adm-kr/files/spl/spl.spa`, bytes 0..4].

## 어디에 있는가

| 컨테이너 | 파일 수 | 매직 | 읽는 쪽 | 등급/출처 |
|---|---|---|---|---|
| LZ77 래퍼, 타입 `0x10` | 6,330 | `LZ77` + `0x10` | `MI_UncompressLZ8` | S: image census; `docs/kb/port/render.md` |
| LZ77 래퍼, 타입 `0xf7` | 1,790 | `LZ77` + `0xf7` | 메시지 리더 (모든 `.bmg`) | S: image census |
| `NARC` | 229개 비압축 | `NARC`+`BTAF`/`BTNF`/`GMIF` | 아카이브 로더 | S: `str/bsize.arc` etc. |
| `BMD0`/`BTX0`/`BCA0`/`BTP0`/`BVA0`/`BTA0`/`BMA0` | 846개 비압축 | 포맷별 | `autoload_2`의 `NNS_G3d*` | S: image census; `config/.../autoload_2/symbols.txt` |
| `MESGbmg1` | 1,791 (1개 비압축) | `MESG` | 게임 자체의 BMG 리더 | S: `script/KOR/message/Other/test_.bmg` |
| `SDAT` | 1 | `SDAT` | `NNS_SndArcInit` @ `0x0210...` 계열 | S: `sound_data.sdat`; `src/matched/NNS_SndArcInit.c` |
| `.bch`/`.bsc`/`.bpl` | 737 | 없음 | 메뉴 오버레이들 | S: `extract/adm-kr/files/menu/` |
| `SPA ` | 1 | `SPA ` | 파티클 시스템 | S: `spl/spl.spa` |

## 읽고 쓰는 데이터

| 구조 | 이미지에 나타나는 필드 | 등급/출처 |
|---|---|---|
| LZ77 래퍼 | `'LZ77'`, 그 뒤 u8 타입 + u24 압축 해제 크기 | S: image census; `select.bmg`, `anm/0/0.nsbca` |
| NARC 헤더 | 매직, BOM `FFFE`, 버전 `0100`, u32 크기, u16 헤더 크기 `0x10`, u16 블록 수 `3` | S: `str/bsize.arc` +0..16 |
| NARC `BTAF` | 매직, u32 블록 크기, u16 항목 수, 그 뒤 시작/끝 쌍 | S: `str/bsize.arc` `BTAF` +8 = 30 |
| BMG 헤더 | `MESGbmg1`, u32 파일 크기, u32 블록 수 `2`, u8 인코딩 `2` | S: `test_.bmg` +0..17 |
| BMG `INF1` | 매직, u32 크기, u16 항목 수, u16 항목 크기 | S: `test_.bmg` `INF1` +8 = 16, 12 |
| SDAT 헤더 | `SDAT`, BOM, u32 크기, u16 헤더 크기 `64`, 그 뒤 SYMB/INFO/FAT/FILE 오프셋+크기 | S: `sound_data.sdat` +0..48 |

## 확인 방법

정적이며, 실행이 필요 없다:

```bash
python - <<'PY'
import os, collections
B = r"extract/adm-kr/files"
by = collections.defaultdict(collections.Counter)
for dp, dn, fn in os.walk(B):
    for f in fn:
        with open(os.path.join(dp, f), 'rb') as h:
            by[os.path.splitext(f)[1].lower()][h.read(4)] += 1
for e in sorted(by):
    print(e, dict(by[e].most_common(4)))
PY
```

예상 출력: `.arc` = 1,835 `LZ77` + 229 `NARC`; `.bmg` = 1,790 `LZ77` + 1 `MESG`; `.nsbtx` =
2,502 `LZ77` + 515 `BTX0`; `.sdat` = 1 `SDAT`.

## 가설

- 모든 `.bmg`의 `0xf7` 압축 타입은 SDK의 `0x10`이 아니다. 별개의 압축 변형이거나 텍스트의
  난독화일 수 있다. `.bmg` 열기(`../engine/text-and-messages.md`의 메시지 경로)에서 포트의 압축
  해제기에 브레이크포인트를 걸고 어느 루틴이 버퍼를 소비하는지와 첫 출력 바이트가 무엇인지 기록하여
  결정한다 — 페이로드가 평범한 BMG라면 `MESGbmg1`이어야 한다.
- 타입 바이트 뒤의 크기 필드는 샘플링한 두 파일에서 그럴듯하게 읽히지만, 실제 압축 해제와 대조
  확인되지는 않았다. `0x10` 파일 하나와 `0xf7` 파일 하나를 압축 해제하고 출력 길이를 헤더 필드와
  비교하여 결정한다.
- `.bch`/`.bsc`/`.bpl`은 `a_mes/`와 `sky/`의 `_ncg`/`_nsc`/`_ncl` 명명과의 유추에 의해 헤더가 제거된
  NCGR/NSCR/NCLR 페이로드로 가정된다. `ov147`을 통한 `menu/title/bg.bch` 로드 하나를 추적하여 어느
  VRAM 영역이 어떤 스트라이드로 이를 받는지 보아 결정한다.
- `NARC` `BTNF` 이름 테이블은 읽지 않았으므로, `ftr/` 아카이브 안의 하위 파일들이 의미 있는 이름을
  가지는지는 알려지지 않았다. `ftr/anm/anm.arc`의 `BTNF`를 파싱하여 결정한다.

## 관련 문서

- `rom-layout.md` — 이 파일들이 위치하는 곳과 각각의 개수.
- `../engine/file-system.md` — 이들을 여는 `FS_*` 프로토콜.
- `../engine/graphics-pipeline.md` — `nsb*` 리소스가 화면에서 무엇이 되는가.
- `music.md` — `sound_data.sdat`의 내부.
