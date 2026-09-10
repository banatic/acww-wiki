# 인터프리터 경로, 그리고 네이티브 본체가 핫 패스를 얻는 방법
<!-- source: wiki/engine/interpreter-path.md -->

**요약.** PC 포트에는 게임을 실행하는 두 가지 방법이 있다. 네이티브 경로는 포트 자체의 C
본체를 실행한다; 인터프리터 경로(`ACWW_INTERP=1`)는 ROM 자체의 ARM 및 Thumb 코드를 프로세스
안에서 실행하고, 호스트 본체가 등록된 곳에서만 그것을 호출한다. 인터프리터 경로가 이
프로젝트의 기본 방향인데, "ROM의 바이트"가 아직 아무도 작성하지 않은 모든 함수의 올바른
구현이기 때문이다. 그래서 흥미로운 질문은 예전 질문의 역이 된다: *이 함수를 우리가 쓸 수
있는가*가 아니라, *이 네이티브 본체가 게임의 동작을 바꾸지 않고 ROM의 바이트를 대체해도
되는가*이다. 그 답은 실제 기록된 호출에 대한 함수별 차분 검사이며, 이 페이지는 그 검사의
통과가 어느 정도의 가치를 갖는지를 말한다.

## 무슨 일이 일어나는가

`ACWW_INTERP=1`은 한 번 읽혀 캐시되고, 두 가지 일을 한다: 포트는 자신의 네이티브 브링업,
네이티브 정적 초기화자, 네이티브 사운드 부팅을 건너뛰고, 대신 인터프리터가 ROM 자체의
`Entry` 순서를 실행한다 [S: `port/interp/interp_boot.c`; `port/platform/win32.c`;
`boot-and-entry.md` 참조]. 나머지 전부 -- 로더, 렌더러, 심(shim), 도구들 -- 는 같은
바이너리다.

어느 함수가 호스트 본체이고 어느 함수가 ROM 바이트인지는 빌드 시점에
`port/tools/interp_registry.py`가 결정하는데, 이 스크립트는 호스트 본체의 레지스트리를
생성하고 자신의 `DENY_FILES` 목록에 있는 베이스네임의 등록을 거부한다 -- TOUCH41 기준 심
파일 50개, 더하기 `DENY_FUNCS = {func_020b1b84}` [S: `port/tools/interp_registry.py`;
`wiki/glossary.md`, "deny list"]. 각 거부 항목은 그것을 강제한 실행(run)을 옆의 주석에
싣고 있으므로, 이 목록은 어느 서브시스템의 절반만 승격했을 때 어느 것이 갈라지는지의
기록이다 [S: `docs/kb/hybrid/stall-playbook.md`, "The deny list is the record of this
table"]. 터치 입력 파일이 가장 분명한 사례다: `port/shim/input/touch.c`를 거부한
것(레지스트리 89 -> 88)이 ROM 자체의 프레임별 스타일러스 게시(publish)를 돌게 만들었고,
그것이 원본의 지연 시간을 재현한 것이다 [S: `docs/log/cycle40-keyboard-gate-probe.md`
TOUCH41; `../experiments/touch-latency.md` 참조].

### 승격 검사 (하이브리드 계획 H5)

네이티브 본체는 지어낸 호출이 아니라 **실제** 호출에 대한 차분 검사로 핫 패스를 얻는다.
실행이 게임이 실제로 하는 호출을 기록하고, 각 호출은 같은 호출 전 메모리에서 두 번
재생된다 -- 한 번은 인터프리터(ROM의 바이트)를 통해, 한 번은 네이티브 본체를 통해 -- 그리고
반환값과 쓰기 집합을 비교한다 [S: `docs/kb/hybrid/promotion.md`]. 세 부분이 이를 수행한다:
`port/interp/interp_record.c`(기록기, `ACWW_INTERP_RECORD`로 활성화되며 그 외에는 비활성 --
전역 로드 한 번과 분기하지 않는 분기 하나), CRT 없는 픽스처를 갖춘 `port/tools/promote.py`,
그리고 기록 실행을 수행하는 추적되는 러너 `port/tools/promote_record.py` [S: same].

각 레코드는 r0-r3와 네 개의 AAPCS 스택 워드, 처음 접근 시 및 모든 스토어 이전에 스냅샷된
**호출 전 페이지 이미지**(이것이 재생을 근사가 아니라 정확하게 만드는 요소다), 유한한 링에
담긴 모든 로드와 스토어, 그리고 반환 시의 r0, r1과 인터프리터 스텝 수를 싣는다. 중첩된
`acww_interp_call` -- 인터럽트 핸들러, 스레드 프로시저 -- 은 더 깊은 깊이에서 실행되고 그
메모리는 제외되는데, 이 호출의 쓰기 집합이 아니기 때문이다 [S: same]. 기록기가 숨기기를
거부하는 세 가지가 각각 플래그로 있다: 등록된 호스트 본체가 호출 안에서 실행됨, I/O 페이지
주소가 접근됨, 한계가 넘침. `promote.py`는 그런 호출을 비교하지 않는다 [S: same].

비교는 **스토어 로그가 아니라 최종 상태 diff**다 -- 올바른 두 본체가 다른 순서로 저장하거나
스크래치 값을 덮어쓸 수 있으며, 호출자가 사후에 관측할 수 있는 것만이 계약이다. 진입 스택
포인터 아래의 죽은 프레임은 의도적으로 제외한다(인터프리터 재생은 기록된 NDS 스택에,
네이티브 본체는 호스트의 스택에 푸시한다); 네 개의 스택 인자 워드는 비교한다. 그리고
네이티브 본체를 판정하기 전에, 인터프리터 재생이 먼저 기록의 반환값을 재현해야 한다 --
그러지 못하면 결과는 `REPLAY-MISMATCH`이며, 이는 하네스의 입력에 대한 진술이지 본체에 대한
진술은 결코 아니다 [S: same]. 종료 코드: 0은 전부 일치, 1은 불일치(발견 사항), 2는 하네스가
판정을 거부함, 3은 일치했으나 일부 호출이 거부됨.

### "AGREE"가 증명하지 않는 것

무엇이든 승격하기 전에 읽어야 할 부분이다 [S: `docs/kb/hybrid/promotion.md` section 3]:

- **커버리지는 기록된 호출뿐, 그 외에는 아무것도 아니다.** 실행이 삼백만 번 호출하는 함수의
  여덟 번의 호출은 여덟 번의 호출이다. 요약이 `calls-that-wrote=`와 `distinct-returns=`를
  출력하는 이유가 그것이다: 모두 같은 값을 반환하고 아무것도 쓰지 않은 호출들에 대한 일치는
  근거가 아니다(M1).
- **콜백은 따라가지 않는다.** ROM 함수가 함수 포인터를 통해 호출하면, 인터프리터 재생은 ROM의
  피호출자를 실행하고 네이티브 본체는 링크가 준 것이 무엇이든 그것을 실행한다. 픽스처는
  정확히 하나의 네이티브 본체만 링크하므로, 네이티브 피호출자를 가진 본체는 링크에 실패한다
  -- 조용히 달라지는 대신 시끄럽게.
- **타이밍, 인터럽트, 순서는 모델링되지 않는다.** 재생은 조용한 프로세스 안의 단일 호출이다.
  고립된 상태에서는 올바르지만 더 오래 걸리거나 재진입되기 때문에 틀린 본체는 여기서 보이지
  않는다. (TOUCH41의 인터프리터 콜백 이상 현상이 정확히 그 부류의 결함이고, 어떤 승격 검사도
  그것을 보지 못했을 것이다 -- `../experiments/touch-latency.md`, Open.)
- **접근된 페이지 밖의 상태는 보이지 않는다.** 기록된 호출이 접근한 페이지만 매핑되고
  diff된다; ROM이 한 번도 접근하지 않은 곳에 쓰는 네이티브 본체는 깔끔한 불일치를 내는 대신
  픽스처를 크래시시킨다.
- **승격은 등록이 아니다.** 일치한다는 것은 그 함수가 호스트 코드여야 *하는지*에 대해 아무
  말도 하지 않는다. 그것이 거부 목록(deny list)의 역할이다.

### 세 가지 결과, 그리고 더 중요한 보정

커스텀 START 레시피, `ACWW_INTERP=1`, `ACWW_STOP_FRAME=3000`, 각각 8회 호출, 런당 약 80초로
기록됨 [S: `docs/kb/hybrid/promotion.md` section 4]:

| 함수 | 위치 | 결과 |
|---|---|---|
| `FX_MulFunc` `0x01ffcb0c` | itcm, ARM, 순수 함수 | **AGREE 8/8**, 호출당 7 스텝, 서로 다른 반환값 6개, 쓰기 0 |
| `func_0204f800` `0x0204f800` | main, Thumb, out 파라미터를 통한 스토어 두 개 | **AGREE 8/8**, 12 스텝, 8회 호출 모두 씀 |
| `MTX_Concat43` `0x01ffb94c` | itcm, ARM, 48바이트 쓰기 | **AGREE 8/8**, 136 스텝, 호출당 기록된 스토어 32개 -- 그러나 관측 가능한 바이트 변화를 낸 것은 **8회 중 2회**뿐; 나머지 여섯은 이미 있던 값을 썼다 |
| `_s32_div_f` `0x021367a8` | autoload_2, 그 실행에서 세 번째로 뜨거운 pc | 기록은 정상, **REFUSED (exit 2): 네이티브 본체 없음.** 손으로 쓴 CodeWarrior 어셈블리; 승격할 것이 없음 |
| `func_02050c58` | main | 레시피 3,000프레임 동안 **한 번도 호출되지 않음** -- 기록할 것이 없음 |

보정이야말로 이 표를 읽는 방식을 바꾸는 결과다. 의도적으로 틀리게 만든 두 본체를
`func_0204f800` 트레이스에 대해 돌렸다 [S: `docs/kb/hybrid/promotion.md` section 5]:

1. 두 out 파라미터를 **맞바꿈** -- **AGREE로 보고됨**, 기록된 여덟 호출 모두가 우연히
   `x == y`이고 `offset_x == offset_y`였기 때문이다. 커버리지 주의사항이 경고가 아니라
   측정으로 도착한 것;
2. 두 번째 스토어의 값을 하위 두 바이트를 맞바꿔 씀 -- **8/8에서 DISAGREE로 보고됨, exit 1**,
   달라진 스토어와 그 주소를 지목.

그러므로 AGREE는 정확히 그 대조(control)의 가치만큼의 가치를 가지며, 대조의 오류는 기록된
인자가 숨길 수 없는 것이어야 한다 -- 어느 포인터로 가는지만이 아니라 저장되는 **값**을
바꿔라.

## 어디에 있는가

| 함수 또는 심볼 | 모듈 | 역할 | 등급/출처 |
|---|---|---|---|
| `acww_interp_boot` | port | 훅을 설치한 뒤 ROM의 `Entry` 순서를 실행한다 | [S: `port/interp/interp_boot.c`; `boot-and-entry.md`] |
| `run_loop` | port | 명령어 루프; 세이브스테이트가 찍히는 곳이기도 하다, 가장 바깥의 인터프리터 프레임에서 | [S: `port/interp/interp_cpu.c`; `docs/kb/hybrid/savestate.md` section 2] |
| `acww_interp_call`, `acww_interp_irq_run` | port | 호출 경계와 IRQ 컨텍스트 진입점 | [S: `port/interp/interp_cpu.c`] |
| `interp_registry.py` `DENY_FILES` | build | ROM 바이트로 남는 심 베이스네임 50개 | [S: `port/tools/interp_registry.py`] |
| `interp_record.c` | port | 호출 기록기; `ACWW_INTERP_RECORD`가 설정되지 않으면 비활성 | [S: `docs/kb/hybrid/promotion.md`] |
| `promote.py`, `promote_main.c` | tools | 재생과 판정; CRT 없음, ROM 이미지는 NDS 주소에 매핑됨 | [S: same] |
| `promote_record.py` | tools | 추적되는 기록 러너, 출력은 `scratchpad/promote/<name>/` 아래 | [S: same] |

## 읽고 쓰는 데이터

| 변수 또는 파일 | 의미 | 쓰는 쪽 | 읽는 쪽 |
|---|---|---|---|
| `ACWW_INTERP` | 1이면 인터프리터 경로 선택; 부팅 시 한 번 읽혀 캐시됨 | 운영자 | `acww_interp_boot` [S: `port/interp/interp_boot.c`] |
| `ACWW_INTERP_RECORD=<hex addr>[,<count>]` | 한 함수에 호출 기록기를 활성화; count 기본값은 8 | 운영자(또는 `promote_record.py`) | `acww_interp_boot` [S: `docs/kb/hybrid/promotion.md` section 1] |
| `ACWW_INTERP_RECORD_OUT=<path>` | 바이너리 트레이스; 기록기가 활성화되면 필수 | 같음 | 기록기 [S: same] |
| `scratchpad/promote/<name>/<name>.rec` | 트레이스 하나: 호출당 경계 워드 여덟 개, 호출 전 4 KB 페이지 이미지, 유한한 로드/스토어 링, 그리고 반환값 | `interp_record.c` | `promote.py` [S: same] |
| `scratchpad/promote/<fn>/receipt.json` | 판정: 트레이스, 소스, 인터프리터, 픽스처 해시, 반환 마스크, 그리고 모든 호출의 인자, 스텝, 반환값 | `promote.py` | 독자 [E: `scratchpad/promote/FX_MulFunc/receipt.json`] |
| `port/tools/interp_registry.py` -> `interp_registry.c` | 생성된 호스트 본체 레지스트리; 그 엔트리 수는 세이브스테이트의 링크 정체성의 일부 | 빌드 | 인터프리터, 그리고 `state.c`의 헤더 검사 [S: `docs/kb/hybrid/savestate.md` section 5] |

## 확인 방법

    python port/tools/promote_record.py fxmul 0x01ffcb0c 8
    python port/tools/promote.py --trace scratchpad/promote/fxmul/fxmul.rec --name FX_MulFunc

러너가 기록 디렉터리의 이름을 정한다(`scratchpad/promote/fxmul/`, 트레이스, 실행 로그, 그리고
exe 해시와 환경 전체를 담은 영수증을 보관); `promote.py`는 판정 영수증을 함수(FUNCTION)의
이름 아래에 쓴다(`scratchpad/promote/FX_MulFunc/receipt.json`, 트레이스, 소스, 인터프리터,
픽스처 해시, 반환 마스크, 그리고 기록된 모든 호출의 인자, 스텝, 반환값을 싣는다).

그런 다음, 매번, 본체를 복사하고, 기록된 인자가 숨길 수 없는 방식으로 망가뜨린 뒤,
`--source <망가뜨린 복사본>`으로 다시 돌린다; DISAGREE를 보고하고 스토어를 지목해야 한다.
판정을 읽기 전에 `calls-that-wrote=`와 `distinct-returns=`를 먼저 읽어라
[S: `docs/kb/hybrid/promotion.md` section 6].

영수증에 관한 주의사항. 원래의 세 검사가 실행된 워크트리는 머지 후 제거되었고, 무시(ignored)
대상이던 `scratchpad/promote/`를 함께 가져갔다 -- 브리프가 지명한 러너와 영수증 둘 다.
`port/tools/promote_record.py`가 추적되는 대체물이며 그것들을 다시 만든다; 머지된 트리에서
`FX_MulFunc`에 대해 다시 돌리면 8회 호출, **AGREE 8/8**, distinct-returns 6을 준다
[E: `scratchpad/promote/FX_MulFunc/receipt.json` -- `"verdict": "AGREE"`, exit 0 -- 그리고
기록 실행 `scratchpad/promote/fxmul/receipt.json`, 76초에 3,000프레임에서 exit 100;
S: `docs/log/cycle40-keyboard-gate-probe.md`, "H5 follow-up"]. `func_0204f800`,
`MTX_Concat43`, `_s32_div_f`의 영수증은 이 트리에 존재하지 **않는다**; 위의 숫자들은
인계 문서의 것이며, 실행 디렉터리에 대한 등급 E가 아니라 `docs/kb/hybrid/promotion.md`
section 4에 대한 등급 S다. 다시 돌리는 것은 각각 명령 하나다.

## 가설

- [H] 일치한 세 본체 중 어느 것이라도 실제로 등록되어야 하는지. AGREE는 동작에 대한 근거이지
  아키텍처에 대한 근거가 아니다; `MTX_Concat43`을 승격하면 전체 실행에 무슨 일이 생기는지는
  아무것도 측정하지 않았다. 하나를 등록하고 마을 실행을 등록하지 않은 같은 실행과
  프레임 단위로 비교하면 확정된다.
- [H] `MTX_Concat43`의 일치가 도대체 무슨 의미가 있는지, 여덟 호출 중 여섯이 이미 있던 값을
  쓴 것을 감안하면. 행렬이 서로 다른 호출 지점에서 기록하면 확정된다 -- 요약 줄의
  `calls-that-wrote=`가 움직여야 할 숫자다.
- [H] `port/interp/interp_cpu.c`와 `interp_bios.c`에 대한, 현재는 검사가 아니라 관례인 규칙:
  **플랫폼 심볼 금지, 훅만 사용.** 첫 번째 읽기 워치포인트 버전은 `acww_frame_count`와
  `acww_out` 참조를 `interp_cpu.c`에 넣었는데, `promote.py`는 이를 플랫폼이 없는 픽스처로
  컴파일하므로 픽스처가 링크에 실패했다(`undefined symbol _acww_frame_count`); 워치는 이제
  `interp_boot.c`가 설치한 훅을 통해 보고한다 [S: `docs/log/cycle40-keyboard-gate-probe.md`,
  "H5 follow-up"]. 기억에 의존하는 대신 게이트 안의 픽스처 링크 검사로 확정된다.

## 관련 문서

- `boot-and-entry.md` -- 인터프리터 경로가 어떻게 부팅하는지, 그리고 그 위에서 프레임이 무엇인지
- `../experiments/savestate-resume.md` -- 이 경로의 실행을 스냅샷하기
- `../experiments/touch-latency.md` -- 도구로 쓰인 거부 목록
- `../../docs/kb/hybrid/promotion.md`, `../../docs/HYBRID-PLAN.md` phase H5
