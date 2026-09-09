# 번역 지침 (원문 → 한글 위키 문서)

원문 위키: `C:\Users\moomin\Desktop\acww\wiki\` (영문, 디컴파일 근거 기반)
출력 위치: `C:\Users\moomin\Desktop\acww-wiki\content\` (원문과 같은 상대 경로, 같은 파일명)

## 원칙

1. **내용을 더하거나 빼지 않는다.** 모든 문장, 표의 모든 행, 모든 출처 태그를 그대로 옮긴다. 요약하지 않는다.
2. **출처 태그는 원문 그대로 둔다.** `[S: ...]`, `[E: ...]`, `[O: ...]`, `[H: ...]`, `[S+O: ...]` 등 대괄호 안은 영문/코드 그대로 유지한다. 대괄호 안의 짧은 설명구(예: `its two tables`)도 번역하지 않는다.
3. **코드 식별자, 주소, 숫자, 파일 경로, 심볼 이름은 절대 바꾸지 않는다.** `func_02040c90`, `0x021c7584`, `ov003`, `src/matched/...`, `ACWW_KEYS_AT`, `RTC_Init` 등. 백틱(`` ` ``)도 원문 그대로.
4. **문체는 위키 평서체** ("~이다", "~한다"). 존댓말을 쓰지 않는다. 직역보다 자연스러운 한국어 기술 문서 문장을 우선하되, 의미는 정확히 보존한다.
5. **마크다운 구조 보존.** 제목 레벨, 표, 목록, 굵게, 코드 블록, 구분선을 그대로 유지한다. 표의 열 수를 바꾸지 않는다.
6. **링크는 상대 경로 그대로.** `[`town.md`](town.md)`, `../experiments/off-recipe.md`, `README.md` 등 링크 대상은 절대 바꾸지 않는다. 링크 텍스트는 한글로 옮겨도 된다(파일명만 있는 링크 텍스트는 그대로 두어도 됨).
7. **인용된 한국어 UI 문구**(예: `당신 이름은?`)는 그대로.
8. **영어 원어 병기**: 핵심 용어가 처음 등장할 때 괄호로 원어를 병기해도 좋다. 예: 오버레이(overlay).

## 표준 섹션 제목 (STYLE.md 템플릿)

| 원문 | 번역 |
|---|---|
| `**Summary.**` | `**요약.**` |
| `## What happens` | `## 무슨 일이 일어나는가` |
| `## Where it lives` | `## 어디에 있는가` |
| `## Data it reads and writes` | `## 읽고 쓰는 데이터` |
| `## How to check it` | `## 확인 방법` |
| `## Hypotheses` | `## 가설` |
| `## Related` | `## 관련 문서` |
| `## Purpose` | `## 목적` |
| `## Recipe` | `## 레시피` |
| `## Expected observations` | `## 예상 관측` |
| `## What would falsify it` | `## 반증 조건` |
| `## Run` / `## Designed, not yet run` | `## 실행됨` / `## 설계만 됨 (아직 미실행)` |
| `## Findings` | `## 발견 사항` |

## 용어 통일표

| 영어 | 한글 |
|---|---|
| villager | 주민 |
| player | 플레이어 |
| town | 마을 |
| acre | 에이커 |
| tile | 타일 |
| item | 아이템 |
| Bells | 벨 |
| turnip | 무 |
| catalogue | 카탈로그 |
| house record | 집 레코드 |
| house plot | 집터 |
| save image / save file | 세이브 이미지 / 세이브 파일 |
| save data | 세이브 데이터 |
| overlay | 오버레이 |
| autoload | 오토로드 |
| scene | 씬 |
| channel | 채널 |
| handler | 핸들러 |
| display object | 디스플레이 오브젝트 |
| actor / actor manager | 액터 / 액터 매니저 |
| thread | 스레드 |
| interrupt | 인터럽트 |
| VBlank | VBlank |
| grade (S/E/O/H) | 등급 |
| citation | 출처 |
| evidence | 근거 |
| hypothesis | 가설 |
| experiment | 실험 |
| recipe | 레시피 |
| run (a run of the port) | 실행(run) / 런 |
| the port / PC port | 포트 / PC 포트 |
| the oracle (DeSmuME reference) | 오라클(DeSmuME 레퍼런스) |
| matched source | 매칭된 소스 |
| symbol table | 심볼 테이블 |
| interpreter path | 인터프리터 경로 |
| shim | 심(shim) |
| frame / frame counter | 프레임 / 프레임 카운터 |
| stop frame | 정지 프레임 |
| screenshot / shot | 스크린샷 |
| weather / season | 날씨 / 계절 |
| RTC | RTC(실시간 시계) |
| tick / tick counter | 틱 / 틱 카운터 |
| day-change routine | 날짜 변경 루틴 |
| catch-up loop | 따라잡기 루프 |
| event flag / event bitfield | 이벤트 플래그 / 이벤트 비트필드 |
| special NPC | 특수 NPC |
| visitor | 방문객 |
| talk machine | 대화 머신 |
| dialogue / script | 대화 / 스크립트 |
| message (BMG) | 메시지(BMG) |
| keyboard (name-entry) | 키보드(이름 입력 화면) |
| touch / stylus / touch panel | 터치 / 스타일러스 / 터치 패널 |
| pad / key input | 패드 / 키 입력 |
| calibration | 보정 |
| RNG / LCG / generator | 난수 생성기(RNG) / LCG / 생성기 |
| seed / entropy | 시드 / 엔트로피 |
| arena / game heap / expanded heap | 아레나 / 게임 힙 / 확장 힙 |
| memory map | 메모리 맵 |
| file system / archive (NARC) | 파일 시스템 / 아카이브(NARC) |
| ROM layout | ROM 레이아웃 |
| graphics pipeline | 그래픽스 파이프라인 |
| light table / sky row | 조명 테이블 / 하늘 행 |
| vertex / texture / palette | 버텍스 / 텍스처 / 팔레트 |
| top screen / bottom screen | 위 화면 / 아래 화면 |
| boot / entry | 부팅 / 진입점 |
| title screen | 타이틀 화면 |
| town hall | 마을 회관 |
| local wireless / Wi-Fi Connection | 로컬 무선 / Wi-Fi 커넥션 |
| friend code | 친구 코드 |
| backup / flash / NVRAM | 백업 / 플래시 / NVRAM |
| bank (save bank) | 뱅크 |
| request (PXI/backup request) | 요청 |
| FIFO / PXI tag | FIFO / PXI 태그 |
| audit | 감사(audit) |
| finding | 발견 사항 |
| consistency | 일관성 |
| control run (OFF arm) | 대조 실행(OFF 조건) |
| falsify | 반증하다 |
| deny list | 거부 목록(deny list) |
| step gate | 스텝 게이트 |
| walk mode | 워크 모드 |
| pointer-to-member (PMF) | 멤버 함수 포인터(PMF) |
| vtable | vtable |

## 파일 머리말

각 출력 파일은 원문과 같이 `# 제목` 으로 시작한다. 제목은 한글로 번역한다.
그 다음 줄에 HTML 주석으로 원문 경로를 남긴다:

```
# 시간과 실시간 시계
<!-- source: wiki/systems/time-and-rtc.md -->
```
