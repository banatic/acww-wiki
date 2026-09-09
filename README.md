# 놀러오세요 동물의 숲 근거 위키 (한글)

「놀러오세요 동물의 숲」(Animal Crossing: Wild World, 한국판 ADMK)의 게임 메커닉을 디컴파일 근거 기준으로 정리한
영문 위키(`acww-decomp/wiki`)를 한글로 옮긴 정적 팬 위키다. GitHub Pages(`docs/`)로 호스팅한다.

## 구조

| 경로 | 내용 |
|---|---|
| `source/` | 번역의 기준이 된 원문 스냅샷(freeze). `SNAPSHOT.txt`에 원본 커밋이 적혀 있다 |
| `content/` | 한글 마크다운. 원문과 같은 상대 경로. `README.md`→`about.md`, `STYLE.md`→`style.md` |
| `templates/`, `assets/` | 페이지 템플릿, CSS, JS, 아이콘 |
| `build.py` | `content/` → `docs/` 정적 빌드 |
| `sync.py` | 원본 레포와 스냅샷을 비교해 다시 번역할 파일을 알려 준다 |
| `docs/` | 빌드 산출물. GitHub Pages가 서빙한다 (직접 수정하지 않는다) |
| `TRANSLATION_GUIDE.md` | 용어 통일표와 번역 규칙 |

## 작업 흐름

```bash
python sync.py            # 원본에서 바뀐 파일 확인 (추가/변경/삭제)
# 바뀐 파일만 content/ 에 다시 번역한다
python sync.py --accept   # 스냅샷 갱신
python build.py           # docs/ 빌드
python -m http.server 8765 --directory docs   # 로컬 미리보기
```

원문(영문)이 기록 문서다. 이 위키는 주장을 더하거나 빼지 않고, 출처 태그(`[S: …]` 등)는 원문 그대로 둔다.
