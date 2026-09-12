# 아이템과 가구
<!-- source: wiki/data/items.md -->

**요약.** ACWW는 "물건"을 병렬 저장 구조를 가진 두 계열로 나눈다. 가구는 `0x0000`-`0x06e8` 범위의
16비트 id이며, `ftr/` 아래에 모델과 텍스처 세트를 가지고, `ftr_info/`의 세 테이블로 기술된다. 그 외의
모든 것 — 도구, 옷, 과일, 화석, 편지지 — 은 *아이템* 계열로, `item_info/`의 네 테이블로 기술되며
모델이 아닌 아이콘 시트에서 그려진다. 양쪽의 이름은 테이블이 아니라 메시지 시스템에서 나온다.

등급 주석: 이 페이지의 **S**는 심볼 테이블, 매칭된 소스, 그리고 추출된 ROM 이미지에서 직접 읽어낸
바이트(경로와 필드를 항상 명시)를 포함한다.

## 무슨 일이 일어나는가

### 가구

가구 에셋은 두 디렉터리 레벨로 분할된 16비트 id로 지정된다. 템플릿은 `/ftr/%d/%d/%04x.arc`이고
대응되는 `.nsbtx`가 있으며, `ov004`에 컴파일되어 있다
[S: `extract/adm-kr/arm9_overlays/ov004.bin`, path-format string literals]. 두 `%d`는 id의 상위 바이트와
중간 니블이다: `ftr/0/0/`은 `0000`..`000f`를, `ftr/0/1/`은 `0010`..`001f`를, `ftr/1/0/`은
`0100`..`010f`를, 마지막으로 채워진 디렉터리 `ftr/6/14/`는 `06e0`..`06e8`을 담는다
[S: `extract/adm-kr/files/ftr/0/0/`, `ftr/0/1/`, `ftr/1/0/`, `ftr/6/14/`,
directory listings]. 따라서
**`0x0000`부터 `0x06e8`까지 1,769개의 가구 id**가 있고, 각각 하나의 `.arc`와 하나의 `.nsbtx`를 가진다
[S: `extract/adm-kr/files/ftr/`, 1,770 `.arc` and 1,792 `.nsbtx`; the
extra `.arc` is `ftr/anm/anm.arc` and the extra 23 `.nsbtx` belong to `ftr/tv/`].

`ftr/anm/anm.arc`는 공유 가구 애니메이션 아카이브이고, `ftr/tv/`는 텔레비전이다: `tv.nsbtx` 하나,
`/ftr/tv/prog/tv_program%d.nsbtp`로 접근하는 `prog/` 디렉터리, 그리고 `/ftr/tv/weather/%s.nsbtp`로
접근하는 `weather/` 디렉터리로 이루어진다
[S: `extract/adm-kr/files/ftr/`; `extract/adm-kr/arm9_overlays/ov004.bin`, path literals].

가구 테이블은 `ftr_info/` 아래의 세 파일이다: `always.bin` 16,384바이트, `dma.bin` 65,536바이트,
`indoor.bin` 8,192바이트이며, `/ftr_info/always.bin`, `/ftr_info/dma.bin`, `/ftr_info/indoor.bin`
경로로 열린다
[S: `extract/adm-kr/files/ftr_info/`, file sizes; `extract/adm-kr/arm9/arm9.bin`, the three path
literals]. 세 크기 모두 2의 거듭제곱인데, 이는 항목당 각각 8, 32, 4바이트에 고정 슬롯 수 2,048개라는
가정과 일치한다 — 1,769개의 실제 id를 여유 있게 담을 수 있는 크기다 [H: arithmetic on the sizes above; see Hypotheses]. `dma.bin`이라는 이름과 같은 디렉터리 내 위치는, 이것이 필드 단위로 읽히는 것이 아니라
작업 버퍼로 DMA되는 블록임을 시사한다 [H].

### 아이템

아이템 테이블은 `item_info/` 아래의 네 파일이다: `always.bin` 18,432바이트, `dma.bin` 36,864,
`indoor.bin` 6,144, `series.bin` 3,072이며, 모두 ARM9 이미지의 리터럴 경로로 열린다
[S: `extract/adm-kr/files/item_info/`, file sizes; `extract/adm-kr/arm9/arm9.bin`, the four path
literals]. 네 크기는 공통 약수 1,536을 가지며, 항목당 12, 24, 4, 2바이트가 된다 — 아이템당 2바이트인
`series.bin`은 정확히 시리즈 id의 형태이며, 이는 가구 시리즈(세트 매칭)에 필요한 것이다 [H: arithmetic; see Hypotheses]. 네 파일 전체에 대해 2, 4, 6, 8, 12, 16바이트로 레코드 크기 탐색을 수행했지만 항목이
명백하게 구조화되는 크기는 발견되지 않았으므로, 레이아웃은 이미지만으로는 결정되지 않는다
[S: probe over `extract/adm-kr/files/item_info/*.bin`, distinct-record counts at each stride].

들고 있거나 떨어뜨린 아이템은 3D이다: `PItm/`은 53개의 모델, 43개의 조인트 애니메이션, 2개의 텍스처
SRT 애니메이션을 담으며, `/PItm/Mdl%d/%d.nsbmd`, `/PItm/Anm%d/%d.nsbca`, `/PItm/ItaAnm%d/%d.nsbta`,
`/PItm/Uki0/%d.nsbmd`로 지정된다
[S: `extract/adm-kr/files/PItm/`, per-directory counts; `extract/adm-kr/arm9/arm9.bin`, the four
path literals]. `Mdl0`과 `Anm0`은 각각 32개 항목을, `Mdl1`/`Anm1`은 18개와 11개를 담으므로, 아이템
모델 공간은 아이템 id 공간보다 훨씬 작다 — 대부분의 아이템은 인벤토리 아이콘으로만 존재한다
[S: `extract/adm-kr/files/PItm/`, per-directory counts].

그 아이콘들은 `menu/icon/`과 `menu/inventory/`에 있다. `ov094`는 템플릿 `menu/icon/icon%02d.bch`,
`menu/icon/pre%d.bch`, `menu/inventory/itmp/m%d.bch`, `menu/inventory/itmp/w%d.bch`와, 각각
8,192바이트인 세 개의 고정 아이템 시트 `b_itm0.bch`, `b_itm1.bch`, `b_itm2.bch`를 가진다
[S: `extract/adm-kr/arm9_overlays/ov094.bin`, path literals;
`extract/adm-kr/files/menu/inventory/`, file sizes]. `menu/icon/`은 24개의 파일을, `menu/inventory/`는
59개를 담는다 [S: `extract/adm-kr/files/menu/icon/`,
`extract/adm-kr/files/menu/inventory/`, counts].

### 착용물과 표면

셔츠는 텍스처만으로 이루어진다: 16개씩 16개 디렉터리에 담긴 256개의 `.nsbtx` 파일이며,
`/cloth/%d/cloth%03d.nsbtx`로 지정된다 [S: `extract/adm-kr/files/cloth/`, 16 subdirectories of 16 files;
`extract/adm-kr/arm9/arm9.bin`, path literal]. 벽지와 바닥재는 같은 형태이지만 평면적이다: 68개의
`wall/wall_%d.nsbtx`와 68개의 `carpet/floor_%d.nsbtx`
[S: `extract/adm-kr/files/wall/`, `extract/adm-kr/files/carpet/`, counts;
`extract/adm-kr/arm9/arm9.bin`, both path literals]. 플레이어 자신의 신체 파츠도 같은 `%d/%d` 방식을
따른다: `PHead/` 아래 0..157번의 158개 머리, `PGls/` 아래 75개의 눈/얼굴 모델, `PPal/` 아래 192개의
팔레트, `PFcTx/` 아래 32개의 얼굴 텍스처, `FcAnm/` 아래 367개의 얼굴 애니메이션, 그리고 두 개의 몸체
`PBody/boy.nsbmd`와 `PBody/grl.nsbmd`
[S: `extract/adm-kr/files/`, per-directory counts and listings;
`extract/adm-kr/arm9/arm9.bin`, the seven `/P*` and `/FcAnm/` path literals].

가게 비품은 `roomObj/`이다: `ov004`에서 `/roomObj/%s.arc`와 `/roomObj/%s.nsbtx`로 열리는 23개의
`.arc` + `.nsbtx` 쌍이며, 이름 중 열두 개는 리터럴로도 존재한다 — 카페, 양복점, 타로 부스, 박물관
전시물, 전화기, 체크인 데스크
[S: `extract/adm-kr/files/roomObj/`, 46 files; `extract/adm-kr/arm9_overlays/ov004.bin`, path
literals].

### 이름

이 페이지의 어떤 테이블도 이름을 담지 않는다. 아이템, 물고기, 곤충의 이름은 메시지 시스템의 `string/`
뱅크에서 나온다: 생물은 `script/KOR/string/obj_etc_fish.bmg`(4,239바이트)와
`obj_etc_insect.bmg`(4,214바이트)에서, 대화에서 이름을 불러야 하는 분류들은 `st_*.bmg` 파일들에서 —
`st_object.bmg`, `st_furniture_taste.bmg`, `st_furniture_letter.bmg`, `st_fashion.bmg`, `st_food.bmg`,
`st_fossil.bmg`
[S: `extract/adm-kr/files/script/KOR/string/`, file names and sizes]. 이를 표시하는 카탈로그 화면은
`ov142`이며, `menu/catalog/` 에셋을 가진다
[S: `extract/adm-kr/arm9_overlays/ov142.bin`, path literals].

## 어디에 있는가

| 테이블 또는 에셋 | 위치 | 항목 수 | 등급/출처 |
|---|---|---|---|
| 가구 모델 | `ftr/<hi>/<mid>/<id>.arc` + `.nsbtx` | 1,769개 id `0x0000`-`0x06e8` | S: `extract/adm-kr/files/ftr/` |
| 가구 애니메이션 | `ftr/anm/anm.arc` | 아카이브 1개 | S: `extract/adm-kr/files/ftr/anm/` |
| 텔레비전 | `ftr/tv/tv.nsbtx`, `prog/`, `weather/` | 23개 파일 | S: `extract/adm-kr/files/ftr/tv/` |
| 가구 테이블 (상주) | `ftr_info/always.bin` | 16,384 B | S: `extract/adm-kr/files/ftr_info/` |
| 가구 테이블 (DMA) | `ftr_info/dma.bin` | 65,536 B | S: same |
| 가구 테이블 (실내) | `ftr_info/indoor.bin` | 8,192 B | S: same |
| 아이템 테이블 (상주) | `item_info/always.bin` | 18,432 B | S: `extract/adm-kr/files/item_info/` |
| 아이템 테이블 (DMA) | `item_info/dma.bin` | 36,864 B | S: same |
| 아이템 테이블 (실내) | `item_info/indoor.bin` | 6,144 B | S: same |
| 아이템 시리즈 | `item_info/series.bin` | 3,072 B | S: same |
| 아이템 모델 | `PItm/Mdl0`, `Mdl1`, `Uki0` | 53개 `.nsbmd` | S: `extract/adm-kr/files/PItm/` |
| 아이템 아이콘 | `menu/icon/`, `menu/inventory/` | 24 + 59개 파일 | S: `extract/adm-kr/files/menu/` |
| 셔츠 | `cloth/%d/cloth%03d.nsbtx` | 256 | S: `extract/adm-kr/files/cloth/` |
| 벽지 / 바닥재 | `wall/wall_%d.nsbtx`, `carpet/floor_%d.nsbtx` | 각 68 | S: `extract/adm-kr/files/` |
| 플레이어 파츠 | `PHead/`, `PGls/`, `PPal/`, `PFcTx/`, `FcAnm/`, `PBody/` | 158/75/192/32/367/2 | S: `extract/adm-kr/files/` |
| 이름 | `script/KOR/string/*.bmg` | 36개 뱅크 | S: `extract/adm-kr/files/script/KOR/string/` |

## 읽고 쓰는 데이터

| 필드 | 의미 | 쓰는 쪽 | 읽는 쪽 |
|---|---|---|---|
| 가구 id (u16) | `ftr/<id>>>8>/<(id>>4)&15>/<id>.arc`를 선택한다 | 세이브와 가게 | `ov004`의 가구 로더 [S: `extract/adm-kr/arm9_overlays/ov004.bin`] |
| `ftr_info/dma.bin` 슬롯 | RAM으로 복사되는 가구별 레코드 | 패커 | 가구 시스템 [H: name and size] |
| `item_info/series.bin` 슬롯 | 2바이트, 아마도 세트 매칭 id | 패커 | 가구/인테리어 코드 [H] |
| `menu/inventory/itmp/m%d.bch`, `w%d.bch` | 아이템별 인벤토리 그림 | 패커 | `ov094` [S: `extract/adm-kr/arm9_overlays/ov094.bin`] |

### 주머니 슬롯이 담는 id와 그 세 표면 밴드

등급 **A**. 세이브의 주머니와 가게 진열 칸이 담는 16비트 id는 **`0x1000` 더하기 `item_info`의
1,536개 슬롯에 대한 인덱스**이다: 이 프로젝트가 라이브 게임에서 읽어 낸 모든 id -- 네 사이클에 걸쳐
열두 개 -- 는 `0x1000`..`0x15ff`에 들어 있으며, 이는 정확히 그 범위이다
[H: arithmetic over the four `item_info` sizes above; S for the ids themselves,
`docs/log/cycle41-gameplay.md` GP54-8].

그 안의 연속된 세 밴드는 이 페이지의 에셋 개수에서 저절로 나오며, 각각 게임(GAME)이 출력한 이름으로
확인되므로, 밴드 경계는 가정된 것이 아니라 측정된 것이다:

| 밴드 | 무엇이며 몇 개인가 | 증인 |
|---|---|---|
| `0x1100`..`0x1143` | 68개의 `wall/wall_%d.nsbtx` 벽지 | `0x111f` = `wall_31`이며, 너굴의 가게는 이를 `벽지`라고 부른다 — 벽지 |
| `0x1144`..`0x1187` | 68개의 `carpet/floor_%d.nsbtx` 바닥재 | `0x114b` = `floor_7`이며, 가게는 이를 `바닥`이라고 부른다 — 바닥재 |
| `0x1188`..`0x1287` | 256개의 `cloth/%d/cloth%03d.nsbtx` 셔츠 | `0x11a8` = `cloth032`이며, 세이브는 이를 착용 중인 셔츠(WORN SHIRT)로 읽는다 [H: `port/tools/savetool.py check` ; provenance unresolved] |

따라서 **`0x117c`는 `carpet/floor_56.nsbtx`**, 57번째 바닥재이다 — 이를 준 주민이 `바닥`이라고 부르는
바로 그것이다. 네 번째 증인은 세이브 자체에서 나온다: 주민의 저장된 `wallpaper`와 `carpet` 바이트는
68 미만의 원시 인덱스이므로, 주머니(POCKET)가 `base + index`를 보관하는 곳에서 세이브(SAVE)는
인덱스를 보관한다 [H: `savetool.py check` on `scratchpad/gameplay54/town3.sav` ; provenance unresolved].

**이름은 KOR 메시지 아카이브에 없다.** `script/KOR/` 아래 91개 중 가장 큰 것은 256개 항목을 가지며
1,536에 가까운 것은 하나도 없으므로, 아이템 이름 테이블은 `a_mes/`, `str/arc/` 또는 오버레이에 있고
아직 발견되지 않았다 — `item_info` 슬롯 1351인 `0x1547`이 슬롯으로만 식별되는 이유이다
[H: entry counts over every `script/KOR/**/*.bmg` ; provenance unresolved].

## 확인 방법

정적 확인부터. 가구 id 범위를 확인하려면:

```bash
python - <<'PY'
import os, glob
ids = sorted(int(os.path.basename(p)[:4], 16)
             for p in glob.glob(r"extract/adm-kr/files/ftr/*/*/*.nsbtx"))
print(len(ids), hex(ids[0]), hex(ids[-1]), ids == list(range(ids[0], ids[-1] + 1)))
PY
```

예상 출력: `1769 0x0 0x6e8 True`.

테이블의 레코드 크기를 결정하려면 유용한 측정은 실제 실행이다: 마을에 도달하는 인터프리터 레시피를
실행하고(`../engine/file-system.md` 참조), 로더가 `ftr_info/dma.bin`을 저장하는 주소를 관찰하며, 연속된
두 가구 조회 사이의 스트라이드를 기록한다. 포트는 이미 ROM 자체의 `FS_*` 경로를 통해 이 파일들을
읽으므로 심(shim)은 필요 없다
[H: host/prose inference from `port/shim/fs/romfs.c`, header; verify against the ROM function or symbol table and this page's recipe].

## 가설

- **`item_info/`는 12/24/4/2바이트의 1,536개 슬롯을, `ftr_info/`는 8/32/4바이트의 2,048개 슬롯을
  가진다.** 유일한 근거는 그 약수들이 네 파일(각각 세 파일)을 모두 나누어떨어지게 한다는 것뿐이다
  [H: arithmetic on the sizes]. `/item_info/always.bin`을 로드하는 함수가 무엇이든 그 안의 인덱스 연산을
  추적해서 결정한다 — `ACWW_INTERP=1` 아래에서 해당 경로에 대해 `FS_ConvertPathToFileID`에 브레이크를
  걸고 호출자를 따라가면 찾을 수 있다.
- **`always` / `dma` / `indoor`는 내용 분할이 아니라 상주 정책을 이름 붙인 것이다.** 두 디렉터리 모두
  같은 세 이름을 쓰고, 양쪽에서 `dma`가 가장 크다 [H: file names and sizes]. 같은 방법으로, 어느 것이
  통째로 복사되고 어느 것이 제자리에서 읽히는지 보아 결정한다.
- **1,769개의 가구 id가 모두 실제 가구는 아니다.** 1,769는 빈틈 없는 완전한 `0x06e9` 범위에 가까우며,
  이는 패딩 항목을 시사한다 [S: the id range is contiguous — see the check
  above].
  `ftr_info/always.bin` 슬롯 중 0이 아닌 것이 몇 개인지 세어 결정한다.
- **아이템 id와 가구 id는 서로 다른 id 공간이다.** 측정된 어떤 것도 이 둘을 연결하지 않는다; 단지
  별도의 테이블과 별도의 에셋을 가질 뿐이다 [H]. `../systems/save-data.md`에 대조하여 세이브의 인벤토리
  인코딩을 읽어 결정한다.
- **`PItm/Uki0/`(모델 3개)는 낚시찌이다.** "Uki"는 그럴듯한 해석이고, 이 디렉터리는 작으며 아이템 모델
  옆에 위치한다 [H]. 낚싯대를 사용할 때 바인딩되는 모델을 덤프해서 결정한다.

## 관련 문서

- `rom-layout.md` — 이 개수들의 근거가 되는 디렉터리 조사.
- `archives.md` — 각 에셋이 들어 있는 `NARC`와 `nsb*` 컨테이너.
- `fish-and-bugs.md` — 같은 아이콘 시트 패턴을 쓰는 생물 계열.
- `../engine/file-system.md` — `/ftr/1/0/0100.arc`가 어떻게 바이트가 되는가.

## 아이템 이름 조회 (item-names-1)

이 측정된 부록은 앞의 **이름** 문단에서 이곳의 어떤 테이블도 이름을 담지 않는다고 한 주장을
대체한다. 이름은 `item_info/dma.bin`과 `ftr_info/dma.bin`에 UTF-16LE로 들어 있으며,
오프라인 리더는 `port/tools/items.py`이다. 완전한 이름 테이블은 공개되어 있지 않다
[S: `src/matched/func_02062cbc.c`, `func_02053ea4.c`, `func_02062ea4.c`;
E: `scratchpad/handoff/item-names-1/evidence.json`, input hashes and six known-ID checks].

인벤토리 호출자 `ov094:0x0229abf8`은 `main:0x02062ea4`를 호출하며, 이 함수는 먼저 `0x02061e2c`로
ID를 정규화한 뒤 아이템 분기 또는 가구 분기를 선택한다. 아이템 조회 `0x02062a28`은
`0x021cb5e0 + 0x38`의 DMA 핸들을 읽고, 하위 12비트로 인덱싱하며(`0x1000..0x10ff` 수량 그룹은
3을 OR한다), 인덱스 `0x56d`에서 클램프한다. 가구 조회 `0x020537e8`은 `0x021c8c48 + 0x38`을 쓰고,
인덱스는 `(id - 0x3000) >> 2`이며, `0x6e8`에서 클램프한다. 하위 12비트 규칙을 가구에 적용하면
잘못된 이름이 나온다
[S: `src/matched/func_ov094_0229abf8.c`, `func_02062ea4.c`, `func_02061e2c.c`,
`func_02062a28.c`, `func_0204bc64.c`, `func_020537e8.c`, `func_0206e6e4.c`;
E: `scratchpad/item-names-1/tests.stderr`, furniture negative control].

초기화 함수는 always/indoor/DMA 스트라이드가 12/4/24바이트인 1,536개 아이템 슬롯과,
스트라이드가 8/4/32바이트인 2,048개 가구 슬롯을 증명한다. 가구 이름은 `+0x16`의 가격
하프워드 앞 첫 22바이트를 차지하고, 아이템 이름은 24바이트를 차지하며 가격 하프워드는 always
`+0`에 있다. 시리즈 초기화는 별도로 **24바이트짜리 레코드 128개**이지, 증명된 1,536개 시리즈
하프워드 배열이 아니다. `--count`는 3,159개의 정규 조회 쿼리(아이템 1,390 + 가구 1,769, 별칭/빈
이름 포함)를 돌려주며, 이는 서로 다른 이름의 수나 모든 물리 슬롯의 수가 아니다
[S: `src/matched/func_02062cbc.c`, `func_02053ea4.c`, `func_020628ac.c`,
`func_02053e18.c`; E: `scratchpad/handoff/item-names-1/evidence.json`, counts and decoded digest].

| ID 밴드 | 측정된 구분 | 근거 |
|---|---|---|
| `0x00xx` | 필드 나무 ID를 포함한다; `0x0043/0x0044`는 아이템 이름 분기가 없다 | S: `src/matched/func_02061e2c.c`, `func_02062ea4.c`; E: `scratchpad/item-names-1/tests.stderr` |
| `0x1100..0x1143`, `0x1144..0x1187` | 아이템 레코드 카테고리 1과 2; 후자는 아래의 측정된 바닥재 ID를 담는다 | S: `src/matched/func_02062870.c`; E: `scratchpad/handoff/item-names-1/evidence.json`, category runs |
| `0x11a8..0x12a7` | 착용물 범위, 카테고리 5; 따라서 `0x11xx`가 전부 옷은 아니다 | S: `src/matched/func_0204b2c8.c`; E: `scratchpad/handoff/item-names-1/evidence.json`, category runs |
| `0x14fe..0x1517` | 꽃/씨앗 카테고리 32, 측정된 `0x150a` 포함 | S: `src/matched/func_02062870.c`; E: `scratchpad/handoff/item-names-1/evidence.json`, known-ID and category checks |
| `0x1518..0x151c` | 과일 술어; 레코드 카테고리 33 | S: `src/matched/func_0204ca64.c`; E: `scratchpad/handoff/item-names-1/evidence.json`, category runs |
| 상위 니블 `3` 또는 `4` | 정규화 후 가구 분기이며, 아이템 테이블 인덱스가 아니다 | S: `src/matched/func_0204bcdc.c`, `func_0204bc64.c`, `func_02061e2c.c` |

- `0x117c`: **눈속임 바닥**, 아이템 인덱스 `0x17c`, 저장된 기본 가격 1,600벨 [E: `scratchpad/handoff/item-names-1/evidence.json`, known IDs].
- `0x3508`: **흰꽃 테이블**, 가구 인덱스 `0x142`, 저장된 기본 가격 1,900벨 [E: `scratchpad/handoff/item-names-1/evidence.json`, known IDs].
- `0x1547`: **품절 간판**, 아이템 인덱스 `0x547`, 저장된 기본 가격 0 [E: `scratchpad/handoff/item-names-1/evidence.json`, known IDs].

"기본 가격"이라는 표기는 의도적이다: 오렌지 레코드는 2,000을 저장하지만, 특산 과일 갈래는 5로
나누고 가게 판매 호출자는 4로 나눌 수 있다. 이 도구는 마을 상태를 읽지 않으며 실제 구매/판매
견적을 약속하지 않는다. 브리프의 씨앗과 낚싯대 기본 가격은 80과 500이다
[S: `src/matched/func_0204c878.c`, `func_ov049_02260cf8.c`;
E: `scratchpad/handoff/item-names-1/evidence.json`, known-ID prices].

`python port/tools/items.py 117c 3508 1547`, `--grep TEXT`, 또는 `--count`로 재현한다;
`python port/tools/test_items.py`는 잘못되거나 잘린 입력의 거부도 요구한다. 입력 경로는 호출자의
cwd와 무관하게 스크립트의 리포지토리 루트 기준 상대 경로이다
[S: `port/tools/items.py`, `port/tools/test_items.py`].
