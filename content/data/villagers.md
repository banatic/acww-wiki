# 주민과 특수 캐릭터
<!-- source: wiki/data/villagers.md -->

**요약.** 일반 주민 모델은 150개로, 0부터 149까지 번호가 붙어 `npc/model/` 아래에 디렉터리당 여덟 개씩
저장되며, 여기에 `npc_sp/model/` 아래에 세 글자 코드로 저장된 37명의 특수 캐릭터가 더해진다. 두
계열은 중요한 모든 면에서 다르게 처리된다: 주민은 공유 애니메이션과 성격에 따라 선택되는 대화를 가진
숫자 id인 반면, 각 특수 캐릭터는 자신의 모델을 로드하는 자신만의 오버레이를 가진다. 이름은 어떤
테이블도 아닌 메시지 시스템에 있다.

등급 주석: 이 페이지의 **S**는 심볼 테이블, 매칭된 소스, 그리고 추출된 ROM 이미지에서 직접 읽어낸
바이트(경로와 필드를 항상 명시)를 포함한다.

## 무슨 일이 일어나는가

### 일반 주민

모델 경로는 `npc/model/%d/%d.nsbmd`이고 대응되는 `npc/model/%d/%d.nsbtx`가 있으며, ARM9 이미지에
컴파일되어 있다 [S: `extract/adm-kr/arm9/arm9.bin`, path-format string literals]. 첫 번째 `%d`는
디렉터리이고 두 번째는 주민 id이며, 디렉터리는 여덟씩 증가한다: `npc/model/0/`은 `0`..`7`을,
`npc/model/8/`은 `8`..`15`를, 마지막인 `npc/model/144/`는 `144`..`149`를 담는다
[S: `extract/adm-kr/files/npc/model/0/`, `/8/`, `/144/`, directory listings].
디렉터리는 19개로, 모델 여덟 개짜리 18개와 여섯 개짜리 하나이며, **150명의 주민, id 0-149**가 된다
[S: `extract/adm-kr/files/npc/model/`, per-directory counts; 150 `.nsbmd` and 150 `.nsbtx` in the
extension census]. 그 옆에 낱개 파일 하나 `npc/ta_test.nsbtp`가 있다
[S: `extract/adm-kr/files/npc/`, listing].

주민 애니메이션은 주민별이 아니라 공유된다: `anm/`은 32개씩 열한 개의 디렉터리에 걸쳐 0부터 323까지
번호가 붙은 324개의 `.nsbca` 파일을 담으며, 같은 디렉터리-블록 방식으로 `/anm/%d/%d.nsbca`로 지정된다
[S: `extract/adm-kr/files/anm/`, per-directory counts and the
`anm/10/` listing `320`..`323`; `extract/adm-kr/arm9/arm9.bin`, path literal].

대화는 주민 id가 아니라 *성격*에 따라 선택된다. 메시지 트리에는 여섯 개의 성격 디렉터리 — `bo`, `ta`,
`ge`, `fu`, `ko`, `ha` — 가 있고, 게임은 정확히 그 여섯 문자열을 담은 `0x020d72a4`의 성격 접두사
테이블로부터 경로를 조합한다
[S: `extract/adm-kr/files/script/KOR/message/`, subdirectory listing; `port/TAXI-ROAD.md`, the
prefix table; `src/matched/func_0200366c.c`]. `bo`와 `ta`는 각각 열여덟 개의 하위 디렉터리에 242개의
파일을 담고 있으며, 나머지 네 성격도 같은 형태이다
[S: `extract/adm-kr/files/script/KOR/message/bo/`, `/ta/`, counts and subdirectory names].
메시지 트리는 또한 각 성격 안에 `3p` 디렉터리를 가지며, 여기에는 *다른* 성격마다 하나씩의 파일 —
`bo_.bmg`, `fu_.bmg`, `ge_.bmg`, `ha_.bmg`, `ko_.bmg`, `ta_.bmg` — 이 들어 있는데, 이는 주민이 주민에
대해 이야기하는 것이다 [S: `extract/adm-kr/files/script/KOR/message/bo/3p/`, listing].

주민 이름은 `script/KOR/string/st_npc_name.bmg`(1,466바이트)에서, 말버릇은
`st_npc_habit.bmg`(1,401바이트)에서, 플레이어가 지어준 별명은 `st_nickn.bmg`(522바이트)에서 나온다
[S: `extract/adm-kr/files/script/KOR/string/`, file names and sizes].

### 특수 캐릭터

`npc_sp/model/`은 37개의 서로 다른 세 글자 어간(stem)을 담으며, 각각 `<stem>.nsbmd`와, 그중 36개에
대해서는 `<stem>_tex.nsbtx`를 가진다: `boa`, `bpt`, `cml`, `dnk`, `end`, `fox`, `grf`, `hgh`, `hgs`,
`los`, `lrc`, `mka`, `mof`, `mol`, `mum`, `ott`, `owl`, `ows`, `pga`, `pgb`, `pge`, `pla`, `plb`,
`plc`, `poo`, `rcc`, `rcd`, `rcn`, `rcs`, `seg`, `seo`, `tti`, `ttl`, `upa`, `wip`, `wrl`, `xct`
[S: `extract/adm-kr/files/npc_sp/model/`, 73 files, stems after stripping `_tex`]. `mka`가 텍스처
파일이 없는 유일한 것이다 [S: same listing]. 모든 경로는 템플릿이 아닌 리터럴이다 — ARM9 이미지가 이들
전부를 그대로 적어 가지고 있다 [S: `extract/adm-kr/arm9/arm9.bin`, the `npc_sp/model/*`
literals].

강력한 구조적 사실은 **각 특수 캐릭터가 자신만의 오버레이를 가진다**는 것이며, 그 오버레이의
이미지에는 해당 캐릭터의 두 경로 문자열만 들어 있다. 이를 읽어내면 오버레이-캐릭터의 직접적인
바인딩을 얻는다
[S: `extract/adm-kr/arm9_overlays/ov0*.bin`, path string literals per overlay]:

| 오버레이 | 이름 붙이는 어간 | 등급/출처 |
|---|---|---|
| `ov045` | `bpt` | S: `ov045.bin` |
| `ov046` | `ows` | S: `ov046.bin` |
| `ov047` | `owl` | S: `ov047.bin` |
| `ov048` | `plc` | S: `ov048.bin` |
| `ov049` | `hgh` | S: `ov049.bin` |
| `ov050` | `lrc`, `rcc`, `rcd`, `rcn`, `rcs` | S: `ov050.bin` |
| `ov051` | `wip` | S: `ov051.bin` |
| `ov052` | `fox` | S: `ov052.bin` |
| `ov053` | `poo` | S: `ov053.bin` |
| `ov054` | `pga`, `pgb` | S: `ov054.bin` |
| `ov055` | `xct` | S: `ov055.bin` |
| `ov068` | `end`, `mof`, `ott`, `pga`, `pgb`, `poo`, `rcc`, `rcd`, `rcn`, `rcs`, `wip`, `xct` | S: `ov068.bin` |
| `ov070` | `grf` | S: `ov070.bin` |
| `ov071` | `ott` | S: `ov071.bin` |
| `ov072` | `seg` | S: `ov072.bin` |
| `ov073` | `boa` | S: `ov073.bin` |
| `ov074` | `mka` | S: `ov074.bin` |
| `ov075` | `plb` | S: `ov075.bin` |
| `ov076` | `seo` | S: `ov076.bin` |
| `ov077` | `mol` | S: `ov077.bin` |
| `ov078` | `cml` | S: `ov078.bin` |
| `ov079` | `wrl` | S: `ov079.bin` |
| `ov080`-`ov086` | `ttl` (일곱 개의 별도 오버레이, 같은 모델) | S: `ov080.bin`..`ov086.bin` |
| `ov087` | `dnk` | S: `ov087.bin` |
| `ov088` | `upa` | S: `ov088.bin` |
| `ov004` | `hgs`, `pge`, `pla`, `tti` | S: `ov004.bin` |

`ov068`은 예외적이다: 하나가 아닌 열두 개의 어간을 이름 붙이며, `ov004`를 제외하고 다섯 개 이상을
이름 붙이는 유일한 오버레이이다 [S: `ov068.bin`, path literals]. `ttl`이 또 하나의 예외이다 —
`ov080`부터 `ov086`까지 일곱 개의 오버레이가 각각 같은 모델만을 이름 붙이고 그 외에는 아무것도 없다
[S: `ov080.bin`..`ov086.bin`]. 게임 자체의 항상 로드되는 C++ 모듈인 `ov004`가 이름 붙이는 네 어간은
오버레이 교체 없이 필요한 것들이다 [S: `ov004.bin`, path literals;
`docs/kb/modules/ov004.md`].

특수 캐릭터 이름은 `script/KOR/string/st_spnpc_name.bmg`(433바이트)에서 나온다
[S: `extract/adm-kr/files/script/KOR/string/`, file name and size]. 이들의 대화는 메시지 트리의 `sp`
가지로, `etc`와 `npc` 두 하위 디렉터리와 60개의 파일을 가진다
[S: `extract/adm-kr/files/script/KOR/message/sp/`, listing; `port/TAXI-ROAD.md`, `sp` = 60].

### 집

주민의 집은 `str/npcHs/`와 `str/npcHsTex/`이며, `/str/npcHs/%d/%s%c.arc`, `/str/npcHs/%d/%s%c.nsbtx`,
`/str/npcHsTex/%c/house_%c%d%c.nsbtx`, `/str/npcHsTex/%c/light_%c%d.nsbtx`로 지정되고, 공유
`/str/npcHsX.arc`가 더해진다
[S: `extract/adm-kr/arm9_overlays/ov003.bin`, path-format string literals;
`extract/adm-kr/files/str/`, 80 files under `npcHs/` and 75 under `npcHsTex/`]. `%c` 매개변수는
같은 디렉터리가 플레이어 집에 사용하는 계절 및 변형 문자이다
(`/str/plHsTex/home%c%c.nsbtx`, `/str/house_pl/house_pl_%c.nsbtx`) [S: same overlay, path
literals].

## 어디에 있는가

| 에셋 또는 테이블 | 위치 | 개수 | 등급/출처 |
|---|---|---|---|
| 주민 모델 | `npc/model/<(id/8)*8>/<id>.nsbmd` + `.nsbtx` | 150개 id, 0-149 | S: `extract/adm-kr/files/npc/model/` |
| 주민 애니메이션 | `anm/<blk>/<n>.nsbca` | 324개, 0-323 | S: `extract/adm-kr/files/anm/` |
| 특수 캐릭터 모델 | `npc_sp/model/<stem>.nsbmd` + `<stem>_tex.nsbtx` | 37개 어간, 73개 파일 | S: `extract/adm-kr/files/npc_sp/model/` |
| 특수 캐릭터 오버레이 | `ov004`, `ov045`-`ov088` | 32개 오버레이 | S: `extract/adm-kr/arm9_overlays/` |
| 주민 대화 | `script/KOR/message/{bo,ta,ge,fu,ko,ha}/` | 각 242개 파일 | S: `extract/adm-kr/files/script/KOR/message/` |
| 특수 대화 | `script/KOR/message/sp/{etc,npc}/` | 60개 파일 | S: same |
| 주민 이름 / 말버릇 | `script/KOR/string/st_npc_name.bmg`, `st_npc_habit.bmg` | 2개 뱅크 | S: `extract/adm-kr/files/script/KOR/string/` |
| 특수 캐릭터 이름 | `script/KOR/string/st_spnpc_name.bmg` | 1개 뱅크 | S: same |
| 주민 집 | `str/npcHs/`, `str/npcHsTex/`, `str/npcHsX.arc` | 156개 파일 | S: `extract/adm-kr/files/str/` |
| 성격 접두사 테이블 | `0x020d72a4` | 6개 포인터 | S: `port/TAXI-ROAD.md`; `src/matched/func_0200366c.c` |

## 읽고 쓰는 데이터

| 필드 | 의미 | 쓰는 쪽 | 읽는 쪽 |
|---|---|---|---|
| 주민 id (0-149) | `npc/model/<(id/8)*8>/<id>.nsbmd`를 선택한다 | 세이브의 거주자 목록 | 주민 로더 [S: `extract/adm-kr/arm9/arm9.bin`, path literal] |
| 성격 (0-5) | `0x020d72a4`를 인덱싱하여 `bo_`/`ta_`/`ge_`/`fu_`/`ko_`/`ha_`를 고른다 | 주민 레코드 | `func_0200366c` [S: `src/matched/func_0200366c.c`] |
| 특수 캐릭터 오버레이 id | 어느 `npc_sp` 모델이 상주할지 선택한다 | 씬 머신 | `FS_LoadOverlay` [S: `src/matched/FS_LoadOverlay.c`] |

## 확인 방법

위의 오버레이-어간 바인딩은 문자열 리터럴에서 읽은 것으로, 경로가 오버레이 안에 *존재한다*는 것을
증명할 뿐 그 오버레이가 유일한 로더라는 것을 증명하지는 않는다. 바인딩 하나를 실제로 확인하려면 해당
캐릭터가 등장하는 씬까지 실행하고 로드된 오버레이 집합을 기록한다; 마을 레시피
(`../engine/file-system.md`)는 이미 프레임 37,500에서 오버레이 5, 36, 54, 120, 117을 보고하고 있다
[E: `docs/log/cycle40-keyboard-gate-probe.md` TOWN40, run `tap-D56`]. 그 목록에 54가 있고 `ov054`가
`pga`와 `pgb`를 이름 붙인다는 점에 주목하라 — 해당 프레임의 스크린샷과 대조해 볼 수 있는 예측이다.

모델 조사를 다시 도출하려면:

```bash
python - <<'PY'
import os, glob
ids = sorted(int(os.path.basename(p)[:-6]) for p in
             glob.glob(r"extract/adm-kr/files/npc/model/*/*.nsbmd"))
print(len(ids), ids[0], ids[-1], ids == list(range(150)))
stems = sorted({os.path.basename(p).split('.')[0].replace('_tex', '')
                for p in glob.glob(r"extract/adm-kr/files/npc_sp/model/*")})
print(len(stems))
PY
```

예상 출력: `150 0 149 True` 및 `37`.

## 가설

- **세 글자 어간은 종(species) 또는 캐릭터의 약어이다.** 몇몇 해석은 유혹적이지만(네 명으로 이루어진
  그룹의 `rc*`, 한 쌍의 `owl`/`ows`) 여기서 어떤 것도 단일 캐릭터를 이름으로 식별하지 않으며, 팬 위키의
  매핑은 근거가 아니다
  [H: `wiki/README.md`, the no-fan-wiki rule]. 캐릭터별로 스크립트 실행에서 그 오버레이를 로드하고,
  모델을 스크린샷으로 찍은 뒤, 대화 상자가 보여주는 이름과 짝지어 결정한다.
- **`ov068`은 한 캐릭터의 오버레이가 아니라 "여러 특수 캐릭터가 한꺼번에" 등장하는 공유 모듈 —
  가장 그럴듯하게는 엔딩 또는 축제 씬 — 이다.** 다른 모든 특수 오버레이가 하나에서 다섯 개의 어간을
  이름 붙이는 데 비해 이것은 열두 개를 이름 붙인다 [S: `ov068.bin`]. `docs/kb/modules/ov003-068.md`가
  이 오버레이를 다룬다; 그 페이지의 설명을 이 오버레이를 로드하는 실행과 대조해 읽어 결정한다.
- **`ov080`-`ov086`은 모델이 아니라 행동으로 구분되는 한 캐릭터(`ttl`)의 일곱 변형이다.** 일곱 개
  모두 같은 두 파일만을 이름 붙이고 그 외에는 아무것도 없다 [S: `ov080.bin`..`ov086.bin`].
  일곱 오버레이의 코드 이미지를 진입점에 대해 diff하여 결정한다.
- **주민 id와 성격은 세이브 레코드에서 독립적인 필드이다**, 따라서 원칙적으로 어떤 주민이든 여섯
  대화 세트 중 어느 것이든 가질 수 있다 [H]. 거주자 레코드의 레이아웃을 읽어
  `../systems/villagers.md`에 대조하여 결정한다.
- **`anm/`의 324개 애니메이션은 150명의 주민 전체에 공유된다**, 애니메이션 트리가 하나뿐이고 주민
  id로 인덱싱되지 않기 때문이다 [S: `/anm/%d/%d.nsbca` has no villager parameter].
  두 명의 서로 다른 주민이 걷는 동안 어떤 애니메이션 인덱스가 요청되는지 로깅하여 결정한다.
- **`npc/ta_test.nsbtp`는 남겨진 개발용 데이터이다.** `npc/`에 있는 유일한 낱개 파일이고 이름에
  `test`가 들어 있다 [H]. 모든 모듈 이미지에서 문자열 `ta_test`를 검색하여 결정한다 — 어떤 모듈도
  이름 붙이지 않는다면, 아무것도 이를 열 수 없다.

## 관련 문서

- `rom-layout.md` — 디렉터리 조사와 오버레이 표.
- `../engine/text-and-messages.md` — 성격과 레이블이 어떻게 `.bmg` 경로가 되는가.
- `../engine/overlays.md` — 148개 오버레이의 나머지가 하는 일.
- `items.md` — 플레이어 자신의 외모를 위한 병렬적인 `PHead`/`PGls`/`PPal` 방식.
