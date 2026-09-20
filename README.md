# 게시용 Starlight 사이트

이 폴더만 공개 Git 저장소 `banatic/acww-wiki`에 넣을 수 있습니다. `../drafts/`, `../research/`, `../data/`, ROM 및 추출 바이너리는 게시 입력이 아닙니다. 현재 본문은 사이트 준비 상태를 알리는 안내문이며, 게임 설명 글은 없습니다.

## Windows에서 글 편집과 미리보기

PowerShell에서 이 폴더로 이동해 실행합니다.

```powershell
npm ci
npm run dev
```

출력되는 로컬 주소의 `/acww-wiki/` 경로를 엽니다. 사용자가 게시하기로 확정한 글은 `src/content/docs/<slug>.md`로 새 파일을 만듭니다. 맨 위에 `---`, `title: 문서 제목`, `---`를 쓰고 아래에 Markdown 본문을 작성합니다. 기존 게시 글은 해당 Markdown 파일에서 직접 수정합니다. 이미지가 승인되었다면 `public/`에 넣고 사이트의 `/acww-wiki/` 기본 경로를 고려해 참조합니다.

```powershell
npm run build
npm run preview
```

검색은 정적 빌드 결과에서 확인합니다. 연구 중인 초안을 미리 보려면 별도의 작업 복사본에서 시험하고, 이 폴더의 게시용 파일로 자동 복사하지 않습니다.

## 게시

이 폴더를 별도 Git 저장소로 사용합니다. 사용자 검토를 마친 파일만 반영한 뒤 `npm run build`와 산출물 검사를 합니다. GitHub 저장소의 Settings → Pages에서 Source를 **GitHub Actions**로 선택하고, Actions의 **Deploy to GitHub Pages**를 수동 실행합니다. workflow는 `workflow_dispatch`만 사용합니다.
