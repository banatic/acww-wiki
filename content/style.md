# 문서 템플릿과 규칙
<!-- source: wiki/STYLE.md -->

`engine/`, `systems/`, `data/` 아래의 모든 페이지는 이 형태를 가진다. 페이지는 80줄에서
400줄 사이로 유지한다; 초과하기보다는 분할한다.

```
# <제목>

**요약.** 플레이어나 포팅 담당자가 행동에 옮길 수 있는 두 문장에서 다섯 문장. 여기에는 출처를 달지 않는다.

## 무슨 일이 일어나는가
산문. 사실을 진술하는 각 문장은 등급 태그와 출처로 끝난다:
  ... 시계는 프레임마다 한 번 전진한다 [S: OS_GetTick, autoload_2, src/matched/OS_GetTick.c].
  ... 택시 주행은 약 6,000 프레임 동안 이어진다 [E: scratchpad/cycle40/runs/tap-D56 9000..15000] [O: scratchpad/oracle/tap-fullpad].

## 어디에 있는가
표: 함수 또는 심볼 | 모듈 | 역할 | 등급/출처.

## 읽고 쓰는 데이터
표: 주소 또는 필드 | 의미 | 누가 쓰는가 | 누가 읽는가.

## 확인 방법
`experiments/` 페이지로의 링크 또는 인라인 레시피: 정확한 환경
(ACWW_* 변수), 정지 프레임, 무엇을 볼 것인가, 예상 관측이 무엇인가.

## 가설
글머리 기호 목록, 각각은 이를 결론지을 실험으로 끝난다. 빈 절도 허용된다.

## 관련 문서
다른 페이지로의 링크.
```

## 규칙

1. **등급과 출처 없는 주장은 없다.** 검토자는 이것이 없는 문장을 모두 삭제한다.
2. **이름은 심볼 테이블의 것을 쓴다.** `func_XXXXXXXX`, `func_ovNNN_XXXXXXXX`, SDK 이름
   (`OS_`, `FS_`, `NNS_`, `TP_`, `CARD_`)을 `tools/agent/target.py`가 로드하는 그대로 쓴다.
   지어낸 이름은 처음 등장할 때 따옴표로 감싸고 "(invented)"를 붙인다.
3. **주소는 NDS 주소이다** (0x02xxxxxx, 0x01ffxxxx), 호스트 주소는 절대 쓰지 않는다.
4. **프레임은 포트의 프레임 카운터이다** (`ACWW_STOP_FRAME`, `ACWW_SHOT_*`); 프레임 번호가
   오라클에서 온 것이면 그렇다고 말한다. 오라클의 포트 카운터 대응은 오프셋 0으로 가정한다
   (`port/tools/oracle/README.md` 참조).
5. **한국어 UI 텍스트**: 식별을 위해 화면당 최대 하나의 짧은 문구만 인용한다,
   예: `당신 이름은?`; 문단 단위로는 절대 인용하지 않는다.
6. **코드 목록은 싣지 않는다.** 말로 하는 제어 흐름 설명은 괜찮다; 전사(transcription)는 안 된다.
7. **모순은 콘텐츠다.** 포트와 오라클이 불일치할 때, 두 관측 모두 등급과 함께 페이지에
   싣고 불일치는 가설로 둔다.
8. **실험은 페이지다.** `experiments/<slug>.md` = 목적, 레시피(복사해서 붙여 넣을 수 있는 형태),
   프레임을 명시한 예상 관측, 그 관측을 만들어 낸 실행, 반증 조건.
9. 영어가 공식 기록 언어이다; 에이전트를 향한 것이다.

## 어디를 볼 것인가

- 심볼과 모듈: `tools/agent/target.py` (`T.load_all()`), `port/build/acww.map`,
  `docs/kb/modules/*.md` (각 오버레이가 무엇인지에 관한 네이티브 시절의 노트).
- 매칭된 소스: `src/matched/<name>.c` (29k개 파일; 헤더 주석이 그 파일이 무엇이고
  바이트 단위로 동일한지를 말해 준다).
- 런타임 동작: `docs/log/cycle40-keyboard-gate-probe.md` (인터프리터 경로의 마을까지의
  여정), `scratchpad/cycle40/runs/*`, `scratchpad/oracle/*`.
- 레시피: `docs/kb/hybrid/recipes.md` (있는 경우), `scratchpad/cycle40/run_direct.py`,
  `scratchpad/cycle40/tap.sh`, `port/tools/oracle/README.md`.
- ROM 파일 시스템 레이아웃: `extract/adm-kr/files/` (디렉터리 이름만; 내용은 복사하지
  않는다).
