# ROM 레이아웃
<!-- source: wiki/data/rom-layout.md -->

**요약.** 한국판 카트리지 `ADMK`는 통상적인 NitroSDK ROM이다: 헤더, ARM9 및 ARM7 바이너리, 네 개의
ARM9 오토로드/TCM 영역, 148개의 ARM9 오버레이가 담긴 오버레이 테이블, 그리고 36개의 최상위 디렉터리에
9,508개의 파일이 있는 파일 시스템. 게임은 그 파일 시스템의 모든 것을 경로 문자열로 지정하며, 사용하는
거의 모든 경로 문자열은 ARM9 이미지나 그것을 필요로 하는 오버레이에 컴파일된 `printf` 스타일의
템플릿이다. 하나의 큰 아카이브로 패킹된 것은 없다: 리소스 트리는 낱개 파일들이며, 각각이 개별적으로
압축되어 있다.

**등급에 대한 주석.** 이 페이지와 다른 `data/` 페이지에서 **S**는 두 종류의 출처를 포함한다:
`src/matched/` 아래의 심볼 테이블 또는 매칭된 소스, 그리고 `extract/adm-kr/` 아래의 추출된 ROM
이미지에서 직접 읽어낸 바이트. 이미지 출처는 항상 파일을 명시하고 어떤 필드를 읽었는지 밝히므로,
독자가 같은 읽기를 다시 수행할 수 있다.

## 무슨 일이 일어나는가

카트리지는 자신을 `ANIMAL CROSS`, 게임 코드 `ADMK`, 메이커 `01`, ROM 버전 0으로 식별한다
[S: `extract/adm-kr/header.yaml` `title`/`gamecode`/`makercode`/`rom_version`]. ARM9 바이너리는
`0x02000000`에 로드되고 진입점은 `0x02000800`이며 압축 저장되어 있다
[S: `extract/adm-kr/arm9/arm9.yaml` `base_address`=33554432, `entry_function`=33556480,
`compressed: true`]. 오토로드 콜백은 `0x02000A58`에 있고 정적 모듈의 BSS는 길이가 0인데, 압축된
이미지 뒤의 모든 것이 오토로드 영역에 넘겨지기 때문이다
[S: `extract/adm-kr/arm9/arm9.yaml` `autoload_callback`=33557080, `bss_start`=`bss_end`=34506816
= `0x020E8840`].

정적 ARM9 모듈 옆에 네 개의 영역이 로드된다. ITCM은 `0x01FF8000`..`0x01FFDAE0`을 차지한다
[S: `extract/adm-kr/arm9/itcm.yaml` `base_address`=33521664, `code_size`=23264]; DTCM 모듈 이미지는
`0x027E0000`에 0x460바이트이다 [S: `extract/adm-kr/arm9/dtcm.yaml` `base_address`=41811968,
`code_size`=1120] — 하드웨어가 그곳에 매핑하는 DTCM *윈도우*는 16 KB, `0x027e0000`-`0x027e4000`이며,
모듈 이미지는 그 하단만을 차지한다 [S: `port/interp/interp_boot.c:11-14`;
see `../engine/memory-map.md`]; `autoload_2`는 `0x020E8840`..`0x0213FDC0`을 차지하며 NitroSDK와 NNS
라이브러리 전체가 있는 곳이다 [S: `extract/adm-kr/arm9/unk_autoload_2.yaml`
`base_address`=34506816, `code_size`=357760]; `autoload_3`은 순수 BSS로,
`0x0213FDC0`..`0x02207CC0`이며 게임의 전역 데이터 아레나이다
[S: `extract/adm-kr/arm9/unk_autoload_3.yaml` `base_address`=34864576, `code_size`=0,
`bss_size`=818944]. `autoload_3`은 정확히 첫 오버레이가 시작하는 곳에서 끝나므로, 오버레이 영역은
`0x02207CC0`에서 시작한다 [S: `extract/adm-kr/arm9_overlays/overlays.yaml`, `id: 0`
`base_address`=35683520].

이 레이아웃이 다른 엔진 페이지의 SDK 주소들을 예측 가능하게 만드는 것이다: 모든 `FS_*`, `GX_*`,
`G3X_*`, `NNS_*` 심볼은 `autoload_2` 안의 `0x0210xxxx`-`0x0212xxxx`에 위치한다
[S: `config/adm-kr/arm9/autoload_2/symbols.txt`, e.g. `FS_Init` addr `0x0211b35c`].
ITCM은 예외 대역이며, 작지 않다: 158개의 함수 심볼, 그중 114개가 이름이 있으며,
`0x01ff8bd0`-`0x01ff8e18`의 네 지오메트리 엔진 버퍼 헬퍼, `NNSi_G3dFuncSbc_*` 씬 그래프 옵코드,
`MTX_*`/`VEC_*`/`FX_*` 고정소수점 라이브러리, 인터럽트 진입(`OS_IrqHandler`, `OS_Halt`,
`OS_SaveContext`), 그리고 `OS_GetTick`을 포괄한다
[S: `config/adm-kr/arm9/itcm/symbols.txt`, counted over `kind:function` lines;
`NNS_G3dGeBufferOP_N` addr `0x01ff8bd0`, `NNS_G3dGeWaitSendDL` addr `0x01ff8e18`].

ARM9 오버레이는 `ov000`부터 `ov147`까지 148개가 있고, ARM7 오버레이는 전혀 없다
[S: `extract/adm-kr/arm9_overlays/overlays.yaml`, 148 `- id:` entries; `extract/adm-kr/config.yaml`
`arm7_overlays: null`]. 각 항목은 `base_address`, `code_size`, `bss_size`, `ctor_start`, `ctor_end`,
`file_id`, `compressed`, `signed`를 가진다
[S: `extract/adm-kr/arm9_overlays/overlays.yaml`, entry `id: 0`]. 이 ROM의 모든 오버레이는 압축되어
있고 어느 것도 서명되어 있지 않다 [S: same file, `compressed: true` / `signed: false` on all 148
entries]. 148개의 오버레이는 단 26개의 서로 다른 로드 주소만을 공유하므로, 대부분은 같은 메모리를 한
번에 하나씩 차지하는 대체물이다: 35개의 오버레이가 `0x02260020`에, 19개가 `0x02278a00`에, 14개가
`0x0229c180`에, 12개가 `0x02260420`에 로드된다 [S: `overlays.yaml`, counted over
`base_address` values]. `ov000`, `ov001`, `ov002`는 모두 `0x02207CC0`에, `ov003`과 `ov004`는 둘 다
`0x0220BF00`에 로드된다 [S: `overlays.yaml`, entries 0-4]. 이들의 코드 합계는 1,683,328바이트로, 정적
ARM9 이미지 코드의 네 배가 넘는다 [S: `overlays.yaml`, sum of
`code_size`]. 이 겹침이 포트가 오버레이 포인터를 정적으로 재작성할 수 없는 이유이다: 인접한 137개의
오버레이 쌍 중 129개가 주소가 겹치므로, `0x02262da0`의 워드는 현재 로드된 오버레이가 무엇이든 그것에
속한다 [S: `port/shim/fs/ovlreloc.c`, header].

추출본에 저장된 ROM 헤더는 카트리지 식별 정보는 담지만 FNT, FAT, 오버레이 테이블 오프셋은 담지
**않는다** [S: `extract/adm-kr/header.yaml`, 15 fields, none of them a table offset];
그것들은 패커가 정렬 및 패딩 테이블로부터 계산한다
[S: `extract/adm-kr/config.yaml` `alignment`/`padding`]. 런타임에 게임은 펌웨어가 `0x027FFE00`에 남겨
두는 0x160바이트 ROM 헤더 이미지에서 이들을 읽는다 — FNT는 +0x40, FAT는 +0x48, ARM9 오버레이
테이블은 +0x50, ARM7 오버레이 테이블은 +0x58
[S: `FSi_InitRom`, `autoload_2`, `src/matched/FSi_InitRom.c`].

파일 시스템은 36개의 최상위 디렉터리 아래 9,508개의 파일과 두 개의 낱개 루트 파일 `BUILDTIME`,
`sound_data.sdat`을 담는다 [S: `extract/adm-kr/files/`, recursive file count and
`ls`]. ROM 이미지에서의 디렉터리 순서는 트리와 별도로 기록되어 있다
[S: `extract/adm-kr/path_order.txt`, 38 lines]; `/dwc`가 알파벳순이 아니라 마지막에 놓여 있음에
주목한다 [S: `extract/adm-kr/path_order.txt` line 38].

ROM에서 가장 큰 단일 파일은 10,704,768바이트의 `sound_data.sdat`이고, 가장 큰 디렉터리는 3,585개 파일
6,692,184바이트의 `ftr/`(가구)이다 [S: `extract/adm-kr/files/`,
file sizes]. `script/`는 파일 수 기준으로 두 번째로 크며, 1,791개의 파일로 게임의 텍스트 전체이다
[S: `extract/adm-kr/files/script/`, recursive count].

## 어디에 있는가

| 영역 | NDS 주소 | 크기 | 역할 | 등급/출처 |
|---|---|---|---|---|
| ARM9 정적 | `0x02000000` | 진입점 `0x02000800` | 게임 코드, 항상 상주 | S: `arm9/arm9.yaml` |
| ITCM | `0x01FF8000` | 0x5AE0 이미지 (32 KB 윈도우) | 158개의 핫 함수: 3D 제출, 고정소수점 연산, 인터럽트 진입 | S: `arm9/itcm.yaml`; `config/.../itcm/symbols.txt` |
| DTCM | `0x027E0000` | 0x460 이미지 (16 KB 윈도우) | 인터럽트 시점 데이터; 하단에 `OS_IRQTable`, 상단에 스택 | S: `arm9/dtcm.yaml`; `port/interp/interp_boot.c:11-14` |
| `autoload_2` | `0x020E8840` | 0x57580 | NitroSDK + NNS 라이브러리 | S: `arm9/unk_autoload_2.yaml` |
| `autoload_3` | `0x0213FDC0` | 0xC7F00 BSS | 게임 전역 변수 아레나 | S: `arm9/unk_autoload_3.yaml` |
| 오버레이 | 26개의 서로 다른 베이스, 첫 번째는 `0x02207CC0` | 총 1,683,328 B | 148개의 기능 모듈 | S: `arm9_overlays/overlays.yaml` |
| 파일 시스템 | — | 9,508개 파일 | 리소스, 경로로 열림 | S: `extract/adm-kr/files/` |

## 읽고 쓰는 데이터

| 디렉터리 | 파일 수 | 바이트 | 담고 있는 것 | 등급/출처 |
|---|---|---|---|---|
| `ftr/` | 3,585 | 6,692,184 | 가구 모델과 텍스처 | S: `extract/adm-kr/files/ftr/` |
| `script/` | 1,791 | 1,581,466 | 모든 메시지 텍스트 (`.bmg`) | S: `.../script/` |
| `menu/` | 737 | 846,493 | 메뉴 화면 아트워크 (`.bch`/`.bsc`/`.bpl`) | S: `.../menu/` |
| `str/` | 338 | 1,371,004 | 집과 NPC 집의 *구조물*(structures), 문자열이 아님 | S: `.../str/` |
| `anm/`, `npc/`, `npc_sp/` | 324 / 301 / 73 | 2.5 MB | 애니메이션, 주민 및 특수 캐릭터 모델 | S: `.../` |
| `bg/` | 257 | 2,811,379 | 마을 지면과 지형 세트 | S: `.../bg/` |
| `cloth/` | 256 | 89,878 | 셔츠 텍스처 | S: `.../cloth/` |
| `fish/`, `insect/` | 284 / 129 | 1,348,867 | 물고기와 곤충 모델 | S: `.../fish/`, `.../insect/` |
| `fg/` | 213 | 394,984 | 나무, 꽃, 풀, 구멍, 돌 | S: `.../fg/` |
| `PHead/ PPal/ PGls/ PItm/ PBody/ PFcTx/ FcAnm/` | 826 | 890,834 | 플레이어 외모 파츠 | S: `.../` |
| `carpet/`, `wall/`, `roomObj/` | 68 / 68 / 46 | 593,826 | 실내 표면과 가게 비품 | S: `.../` |
| `sky/`, `a_mes/`, `ab_all/`, `spl/`, `font/` | 38 / 18 / 2 / 14 / 12 | 0.5 MB | 하늘 레이어, 메시지 상자 아트, 이펙트, 폰트 | S: `.../` |
| `item_info/`, `ftr_info/`, `fg_data/`, `myOrg/` | 4 / 3 / 8 / 1 | 156 KB | 평면 데이터 테이블 (`items.md` 참조) | S: `.../` |
| `dwc/utility.bin` | 1 | 929,892 | Nintendo WFC 유틸리티 페이로드 | S: `.../dwc/` |
| `sound_data.sdat` | 1 | 10,704,768 | 사운드 아카이브 전체 (`music.md` 참조) | S: `extract/adm-kr/files/sound_data.sdat` |

그 표의 숫자 하나는 다른 파일과 대조 확인할 수 있다. `bg/a0/`..`bg/a8/`은 `0000.arc`부터 `0085.arc`까지
이름 붙은 134개의 에이커 아카이브를 담고, `bg/bkattr.bin`은 정확히 134바이트이다 — 에이커당 속성
바이트 하나 [S: `extract/adm-kr/files/bg/`, per-directory listings;
`extract/adm-kr/files/bg/bkattr.bin`, size]. 대응되는 텍스처 세트는 `bg/t256`, `t257`, `t258`이며,
`1000.nsbtx`부터 번호가 붙은 42개의 파일이다 [S: `extract/adm-kr/files/bg/t256/`, listing].

`str/`은 이름의 함정이다: 문자열(strings)이 아니라 집 *구조물*(structures)로, 242개의 `.nsbtx`와 94개의
`.arc` 모델 파일이다 [S: `extract/adm-kr/files/str/`, extension census; corroborated in
`port/TAXI-ROAD.md` "the name is a trap"].

코드가 사용하는 경로 템플릿은 이를 필요로 하는 모듈에 컴파일되어 있으며, 모듈 이미지에서 이를 다시
읽어내면 각 디렉터리의 명명 문법을 얻는다. `arm9.bin` 하나만으로 212개의 서로 다른 리소스 경로를
가지며, 여기에는 매개변수화된 형태 `/PHead/%d/%d.nsbmd`, `/anm/%d/%d.nsbca`, `/bg/a%d/%04x.arc`,
`/cloth/%d/cloth%03d.nsbtx`, `/wall/wall_%d.nsbtx`, `/script/%s/select/%s.bmg`가 포함된다
[S: `extract/adm-kr/arm9/arm9.bin`, path-format string literals].
오버레이는 자기 것을 가진다: `ov003`은 209개의 나무, 꽃, 집 구조물 경로를, `ov004`는 가구와 방
오브젝트 템플릿 `/ftr/%d/%d/%04x.arc`와 `/roomObj/%s.arc`를, `ov009`는 `/str/arc/%d/str%d%c.arc`를
가진다 [S: `extract/adm-kr/arm9_overlays/ov003.bin`,
`ov004.bin`, `ov009.bin`, path-format string literals].

`ov090` 이상의 모든 메뉴 오버레이는 자신이 그리는 화면 하나에 대한 `menu/<screen>/` 경로만을 정확히
가지므로, 오버레이 테이블은 게임 UI의 읽을 수 있는 색인이 된다: `ov095`와
`ov111`/`ov112`/`ov122`/`ov126`은 `menu/chat2/` 키보드 페이지를, `ov118`과 `ov120`은 마을 지도를,
`ov124`는 한글 키보드의 `menu/han/`을, `ov130`/`ov132`/`ov133`은 은행을, `ov134`는 시계를, `ov142`는
카탈로그를, `ov143`은 멜로디 화면을, `ov144`는 음악 화면을, `ov145`는 기부를, `ov146`은 WFC 화면을,
`ov147`은 타이틀을 가진다 [S: `extract/adm-kr/arm9_overlays/ov0*.bin`,
path string literals per overlay].

## 확인 방법

이 페이지의 어떤 것에도 실행이 필요 없다; 모두 정적 구조이다. 디렉터리 조사를 다시 도출하려면:

```bash
python - <<'PY'
import os, collections
B = r"extract/adm-kr/files"
n = b = 0; ext = collections.Counter()
for dp, dn, fn in os.walk(B):
    for f in fn:
        n += 1; b += os.path.getsize(os.path.join(dp, f))
        ext[os.path.splitext(f)[1]] += 1
print(n, b, ext.most_common())
PY
```

예상 출력: 9,508개의 파일과 `archives.md`의 확장자 히스토그램. 경로 템플릿을 다시 도출하려면
`extract/adm-kr/arm9/arm9.bin`과 `extract/adm-kr/arm9_overlays/*.bin`에서 알려진 리소스 확장자로
끝나는 출력 가능 문자열 구간을 스캔한다.

## 가설

- 26개의 공유 오버레이 로드 주소는 알려진 상주 규율을 가진 소수의 *슬롯*으로 분할되어야 한다.
  `tap-D56` 형태의 실행에 걸쳐 `FS_LoadOverlay` 오버레이 id와 그 결과인 `FS_StartOverlay` 주소를
  로깅하고 주소별로 묶어 결정한다.
- `BUILDTIME`(파일 시스템 루트의 31바이트)은 아마도 런타임에 아무것도 읽지 않는 빌드 스탬프이다.
  전체 실행에 걸쳐 `/BUILDTIME`의 id에 대해 `FS_ConvertPathToFileID`를 관찰하고 요청된 적이 있는지
  보아 결정한다.
- `path_order.txt`는 `/dwc`를 알파벳순에서 벗어난 위치에 놓는데, 이는 트리의 나머지가 배치된 후에
  덧붙여졌음을 시사한다. `dwc/utility.bin`의 FAT 오프셋을 `wall/`의 마지막 파일과 비교하여 결정한다.
- 위의 오버레이-`menu/` 매핑은 문자열 리터럴에서 읽은 것으로, 경로가 그 오버레이에 *존재한다*는 것을
  증명할 뿐 그 오버레이가 해당 화면의 유일한 로더라는 것을 증명하지는 않는다. `tap-D56`이 마을에
  대해 했던 방식대로, 화면이 나타나는 프레임에서 로드된 오버레이 집합을 로깅하여 화면별로 결정한다
  [E: `docs/log/cycle40-keyboard-gate-probe.md` TOWN40, overlays 5,
  36, 54, 120, 117 at frame 37,500].

## 관련 문서

- `archives.md` — 이 모든 파일이 감싸여 있는 컨테이너 포맷.
- `../engine/file-system.md` — 경로가 어떻게 RAM의 바이트가 되는가.
- `items.md`, `villagers.md`, `fish-and-bugs.md`, `music.md` — 트리 안의 테이블들.
