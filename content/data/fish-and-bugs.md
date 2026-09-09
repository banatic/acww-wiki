# 물고기와 곤충
<!-- source: wiki/data/fish-and-bugs.md -->

**요약.** 물고기와 곤충은 작고 병렬적인 두 계열이다. 각각은 자기 디렉터리에 번호가 붙은 3D 모델 세트,
잡은 포즈를 위한 두 번째 "들고 있는" 모델 세트, 박물관과 카탈로그를 위한 56개 항목의 그림 시트, 그리고
이름 메시지 뱅크 하나를 가진다. 번호는 빽빽하고 디렉터리에 매핑되어 있으므로 개수를 파일 트리에서
바로 읽을 수 있다: 59개의 물고기 모델 슬롯, 63개의 곤충 모델 슬롯, 그리고 각 계열에 56개의 도감 그림.

등급 주석: 이 페이지의 **S**는 심볼 테이블, 매칭된 소스, 그리고 추출된 ROM 이미지에서 직접 읽어낸
바이트(경로와 필드를 항상 명시)를 포함한다.

## 무슨 일이 일어나는가

### 물고기

물고기 모델은 `fish/` 아래 두 그룹으로 나뉘는 열 개의 디렉터리에 있다
[S: `extract/adm-kr/files/fish/`, subdirectory listing]. 디렉터리 `00`, `01`, `02`, `03`은 헤엄치는
모델을 담으며, 마지막을 제외하고 각각 열여섯 개의 id를 가진다: `fish/00/`은 `fish00`..`fish15`이고,
`fish/03/`은 `fish58`까지 이어진다 [S: `extract/adm-kr/files/fish/00/`, `/03/`, listings]. 대부분의
id는 `.nsbmd`와 `.nsbca`를 모두 가진다; `fish56`, `fish57`, `fish58`은 모델만 가진다
[S: `extract/adm-kr/files/fish/03/`, listing]. 따라서 **59개의 물고기 모델 슬롯, id 0-58**이 된다
[S: `extract/adm-kr/files/fish/`, counted over the `fish??` stems]. `fish/03/`에 두 개의 추가 항목이
있다: `fish_shadow`(물속에서 움직이는 그림자, 모델 + 애니메이션)와 `fish_hire`(모델, 애니메이션,
그리고 텍스처 SRT 애니메이션) [S: same listing].

경로는 두 곳에 컴파일되어 있다. `arm9.bin`은 `/fish/0%d/fish%d.nsbca`, `/fish/0%d/fish%d.nsbmd`,
0으로 채운 `fish0%d` 변형, 그리고 세 개의 리터럴 `fish/03/fish5N.nsbmd` 이름을 가진다
[S: `extract/adm-kr/arm9/arm9.bin`, path-format string literals];
`ov003`은 그림자와 `fish_hire` 경로를 가진다 [S: `extract/adm-kr/arm9_overlays/ov003.bin`].

디렉터리 `10`부터 `15`까지는 `m_fish` 접두사를 가진 두 번째 별도 모델 세트를 담으며, `ov004`에서
`/fish/%d/m_fish%d.nsbmd`와 `/fish/%d/m_fish%d%d.nsbca`로 지정된다
[S: `extract/adm-kr/arm9_overlays/ov004.bin`, path literals]. 디렉터리는 `10 + id/10`이다:
`fish/15/`는 `m_fish50`..`m_fish55`와 그 애니메이션 `m_fish500`..`m_fish552`를 담으며, 마지막 자릿수는
애니메이션 인덱스이다 [S: `extract/adm-kr/files/fish/15/`, listing]. 따라서 `m_fish` 세트는 id 0-55를
다루며, 헤엄치는 세트보다 셋이 적다
[S: `extract/adm-kr/files/fish/1*/`, counted stems].

### 곤충

곤충은 다른 디렉터리 키로 같은 형태를 따른다. `insect/`에는 일곱 개의 디렉터리 — `01`, `11`, `21`,
`31`, `41`, `51`, `61` — 가 있고, 각각은 열 개의 곤충 id, 스무 개의 파일을 담으며, 예외적으로 `61`은
세 개를 담는다 [S: `extract/adm-kr/files/insect/`, per-directory counts]. `insect/61/`은 `bug60`,
`bug61`, `bug62`를 담으므로, 범위는 **63개의 곤충 모델 슬롯, id 0-62**이다
[S: `extract/adm-kr/files/insect/61/`, listing; `extract/adm-kr/files/insect/`, 129 files].

물고기와 달리 곤충은 곤충별로 선택되는 세 가지 다른 애니메이션 포맷을 사용한다. `insect/51/`은 세
가지를 나란히 보여준다: `bug50`, `bug51`, `bug52`, `bug56`, `bug57`은 `.nsbva`(가시성 애니메이션)를
가진다; `bug53`, `bug54`, `bug55`는 `.nsbca`(조인트 애니메이션)를 가진다; `bug58`과 `bug59`는 `.nsbca`와
`.nsbta`(텍스처 SRT)를 모두 가진다
[S: `extract/adm-kr/files/insect/51/`, listing]. `ov004`는 일곱 디렉터리 전부의 템플릿 —
`/insect/01/bug0%d`, `/insect/11/bug%d` 등에서 `/insect/61/bug%d`까지 — 과, 특정한
`/insect/51/bug52.nsbmd`, `/insect/51/bug52.nsbva`, `/insect/51/bug57`, `/insect/61/bug61`,
`/insect/61/bug62`, `/insect/61/bug%d.nsbta`를 가진다
[S: `extract/adm-kr/arm9_overlays/ov004.bin`, path literals]. `ov003`은
`/insect/51/bug%d.nsbta`를 추가한다 [S: `extract/adm-kr/arm9_overlays/ov003.bin`].

### 도감 그림

두 계열은 하나의 그림 방식을 공유한다. `menu/fish_pic/`과 `menu/bug_pic/`은 각각 `0`..`4`로 번호가
붙은 다섯 개의 디렉터리를 담으며, 각 디렉터리는 `<n>.bpl` 팔레트 하나와 일련의 `<n>_<ii>.bch` 타일
시트를 가진다: `0`은 `0_00`..`0_11`을, `4`는 `4_48`..`4_55`를 담는다
[S: `extract/adm-kr/files/menu/fish_pic/0/`, `/4/`; `extract/adm-kr/files/menu/bug_pic/4/`,
listings]. 두 번째 숫자는 생물 인덱스이고 디렉터리를 가로질러 연속적이므로, 각 계열은 61개 파일에
**56개의 그림, 인덱스 0-55**를 가진다
[S: `extract/adm-kr/files/menu/fish_pic/`, 56 `.bch` + 5 `.bpl`;
`extract/adm-kr/files/menu/bug_pic/`, the same]. 이를 표시하는 화면은 `ov114`이며,
`menu/fish/a_bg.bsc`, `menu/fish/bug_bg.bch`와 그 동반 파일들을 가진다 — 두 계열에 오버레이 하나이다
[S: `extract/adm-kr/arm9_overlays/ov114.bin`, path literals].

### 이름과 텍스트

이름은 두 메시지 뱅크에서 나온다: `script/KOR/string/obj_etc_fish.bmg`(4,239바이트)와
`obj_etc_insect.bmg`(4,214바이트) [S: `extract/adm-kr/files/script/KOR/string/`, file names and
sizes]. 두 개의 뱅크가 더 있어, 생물이 화제에 오를 때 대화가 사용하는 시간대와 계절 표현을 담는다:
`st_fish_time.bmg`(99바이트)와 `st_insect_time.bmg`(116바이트)
[S: same directory]. 잡았을 때의 안내문은 `script/KOR/message/obj/etc/getfish_.bmg`와
`getinsect_.bmg`이며 [S: `extract/adm-kr/files/script/KOR/message/obj/etc/`, listing], 게시판에는
낚시 대회와 곤충 채집 대회 뱅크 `bbs_fishing.bmg`와 `bbs_insect.bmg`가 있다
[S: `extract/adm-kr/files/script/KOR/bbs/`, listing].

## 어디에 있는가

| 에셋 | 위치 | 개수 | 등급/출처 |
|---|---|---|---|
| 헤엄치는 물고기 모델 | `fish/0<0-3>/fish<id>.nsbmd` (+`.nsbca`) | 59개 id, 0-58 | S: `extract/adm-kr/files/fish/00..03/` |
| 물고기 그림자 / hire | `fish/03/fish_shadow.*`, `fish_hire.*` | 2세트 | S: `extract/adm-kr/files/fish/03/` |
| 들고 있는 물고기 모델 | `fish/1<0-5>/m_fish<id>.nsbmd` (+`.nsbca`) | 56개 id, 0-55 | S: `extract/adm-kr/files/fish/10..15/` |
| 곤충 모델 | `insect/<d1>1/bug<id>.nsbmd` | 63개 id, 0-62 | S: `extract/adm-kr/files/insect/` |
| 곤충 애니메이션 | 곤충별로 `.nsbva`, `.nsbca` 또는 `.nsbca`+`.nsbta` | 혼합 | S: `extract/adm-kr/files/insect/51/` |
| 물고기 그림 | `menu/fish_pic/<0-4>/<n>_<ii>.bch` + `<n>.bpl` | 56 + 5 | S: `extract/adm-kr/files/menu/fish_pic/` |
| 곤충 그림 | `menu/bug_pic/<0-4>/<n>_<ii>.bch` + `<n>.bpl` | 56 + 5 | S: `extract/adm-kr/files/menu/bug_pic/` |
| 도감 화면 | `ov114`, `menu/fish/` | 13개 파일 | S: `extract/adm-kr/arm9_overlays/ov114.bin` |
| 이름 | `script/KOR/string/obj_etc_fish.bmg`, `obj_etc_insect.bmg` | 2개 뱅크 | S: `extract/adm-kr/files/script/KOR/string/` |
| 포획 텍스트 | `script/KOR/message/obj/etc/getfish_.bmg`, `getinsect_.bmg` | 2개 뱅크 | S: `.../message/obj/etc/` |
| 로더 | `ov003`, `ov004` | 경로 리터럴 | S: `extract/adm-kr/arm9_overlays/ov003.bin`, `ov004.bin` |

## 읽고 쓰는 데이터

| 필드 | 의미 | 쓰는 쪽 | 읽는 쪽 |
|---|---|---|---|
| 물고기 id | `fish/0<id/16>/fish<id>.nsbmd`와 `fish/1<id/10>/m_fish<id>.nsbmd`를 선택한다 | 낚시 시스템 | `ov003` / `ov004` 로더 [S: `ov003.bin`, `ov004.bin`] |
| 곤충 id | `insect/<(id/10)*10+1>/bug<id>.nsbmd`를 선택한다 | 곤충 시스템 | `ov004` 로더 [S: `ov004.bin`] |
| 그림 인덱스 (0-55) | `menu/<family>_pic/<i/12>/<i/12>_<ii>.bch`를 선택한다 | 도감 | `ov114` [S: `ov114.bin`] |

## 확인 방법

정적 조사:

```bash
python - <<'PY'
import glob, os, re
fish = sorted({int(m.group(1)) for p in glob.glob(r"extract/adm-kr/files/fish/0*/fish*.nsbmd")
               for m in [re.match(r"fish(\d+)\.nsbmd", os.path.basename(p))] if m})
bug  = sorted({int(m.group(1)) for p in glob.glob(r"extract/adm-kr/files/insect/*/bug*.nsbmd")
               for m in [re.match(r"bug(\d+)\.nsbmd", os.path.basename(p))] if m})
pic  = sorted({int(os.path.basename(p).split('_')[1][:2])
               for p in glob.glob(r"extract/adm-kr/files/menu/fish_pic/*/*_*.bch")})
print(len(fish), fish[-1], len(bug), bug[-1], len(pic), pic[-1])
PY
```

예상 출력: `59 58 63 62 56 55`.

실제 확인에는 생물이 있는 씬이 필요한데, 인터프리터 경로는 아직 거기에 도달하지 못했다: 기록된 가장
먼 프레임은 마을 회관이 보이는 37,500의 마을이다
[E: `docs/log/cycle40-keyboard-gate-probe.md` TOWN40, run `tap-D56`]. 실행이 잠자리채나 낚싯대를
손에 들 때까지, 이 페이지의 모든 것은 관측된 동작이 아니라 파일 트리 구조이다.

## 가설

- **56이 각 계열의 실제 생물 수이고 추가 모델 슬롯은 변형이다.** 도감에는 계열당 정확히 56개의 그림이
  있지만, 물고기 모델은 59개, 곤충 모델은 63개이다
  [S: the census above]. 압축 해제 후 `obj_etc_fish.bmg`의 `INF1` 헤더에서 항목 수를 읽어 결정한다 —
  이름 뱅크는 잡을 수 있는 생물마다 하나의 항목을 가져야 한다.
- **`fish56`, `fish57`, `fish58`은 잡을 수 없는 오브젝트이다** — 이들은 `.nsbca`가 없는 유일한
  헤엄치는 모델이며, 템플릿을 통해서가 아니라 리터럴로 이름이 붙어 있다
  [S: `extract/adm-kr/files/fish/03/`; `extract/adm-kr/arm9/arm9.bin`, the three literal paths].
  그 세 리터럴을 로드하는 함수가 무엇인지 찾아 결정한다.
- **`m_fish`는 "잡은 후 들어 올린" 모델이고 `fish_shadow`는 물속에서 움직이는 실루엣이다.** 두 해석
  모두 이름과, `m_fish`가 `ov004`(게임 자체의 모듈)에 의해 로드되는 반면 헤엄치는 모델은 `arm9.bin`에서
  로드된다는 사실에서 나온다 [H].
  스크립트 실행에서 포획 장면을 스크린샷으로 찍어 결정한다.
- **`fish_hire`는 낚시 대회 또는 Chip 관련 모델이다.** 어간은 불투명하고, `.nsbta`를 가진 유일한
  물고기 에셋이다 [H]. 같은 방법으로 결정한다.
- **곤충 애니메이션 포맷은 행동 분류를 인코딩한다** — 깜빡이며 나타났다 사라지기만 하는 곤충에는
  `.nsbva`, 움직이는 부위가 있는 곤충에는 `.nsbca`, 스크롤하는 날개 텍스처에는 `.nsbta` [H: the split in
  `insect/51/`]. 세 종류를 각각 로드하고 움직임을 기술하여 결정한다.

## 관련 문서

- `rom-layout.md` — 디렉터리 조사.
- `archives.md` — `nsbmd`/`nsbca`/`nsbva`/`nsbta`와 `.bch`/`.bpl` 메뉴 포맷.
- `items.md` — 아이템에 대한 같은 아이콘 시트와 메시지 뱅크 패턴.
- `../engine/text-and-messages.md` — 이름이 나오는 `string/` 뱅크.
