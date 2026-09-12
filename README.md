# 놀러오세요 동물의 숲 근거 위키 (한글)

「놀러오세요 동물의 숲」(Animal Crossing: Wild World, 한국판 ADMK)의 게임 메커닉을 디컴파일 근거 기준으로 정리한
영문 위키(`acww-decomp/wiki`)를 한글로 옮긴 정적 팬 위키다. GitHub Pages(`docs/`)로 호스팅한다.

## 구조

| 경로 | 내용 |
|---|---|
| `source/` | 번역 기준 원문 스냅샷. `SNAPSHOT.txt`에 원본 커밋, `SNAPSHOT.json`에 파일별 SHA-256을 기록한다 |
| `content/` | 한글 마크다운. 원문과 같은 상대 경로. `README.md`→`about.md`, `STYLE.md`→`style.md` |
| `templates/`, `assets/` | 페이지 템플릿, CSS, JS, 아이콘 |
| `build.py` | `content/` → `docs/` 정적 빌드 |
| `sync.py` | 원본 레포와 스냅샷을 비교해 다시 번역할 파일을 알려 준다 |
| `validate.py` | 원문과 번역의 제목·표·출처, 스냅샷 해시, 생성된 내부 링크·검색 대상을 검사한다 |
| `docs/` | 빌드 산출물. GitHub Pages가 서빙한다 (직접 수정하지 않는다) |
| `TRANSLATION_GUIDE.md` | 용어 통일표와 번역 규칙 |

## 작업 흐름

```bash
python sync.py            # 원본에서 바뀐 파일 확인 (추가/변경/삭제)
# 바뀐 파일만 content/ 에 다시 번역한다
python sync.py --accept   # 스냅샷 갱신
python build.py           # docs/ 빌드
python validate.py --site # 원문 대조와 내부 링크 검사
python -m unittest discover -s tests -v
python -m http.server 8765 --directory docs   # 로컬 미리보기
```

번역 중 원본이 바뀔 수 있다면 먼저 원문 디렉터리를 별도로 복사하고 해당 커밋 전체 SHA를 기록한다. `python sync.py --source <고정한-wiki-경로>`로 차이를 확인하고 그 복사본을 번역한다. 번역 후 `python validate.py --source <고정한-wiki-경로>`를 통과하면 `python sync.py --source <고정한-wiki-경로> --revision <원본-커밋-SHA> --accept`로 확정한다. 지정 커밋과 파일 목록·내용이 다르면 확정하지 않는다.

기본 `--accept`도 원본 HEAD의 커밋된 내용과 일치해야 한다. Markdown과 TSV를 비교하며, TSV는 번역하지 않고 보조 데이터로 보관한다.

원문이 기록 문서다. 이 위키는 주장을 더하거나 빼지 않고, 출처 태그(`[S: …]` 등)는 원문 그대로 둔다. 구조 검사는 번역 의미의 정확성을 대신하지 않으므로 변경한 문단도 원문과 대조한다.
