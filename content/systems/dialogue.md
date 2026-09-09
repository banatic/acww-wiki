# 대화
<!-- source: wiki/systems/dialogue.md -->

**요약.** 누군가와 대화하는 것은 NPC 안이 아니라 NPC 곁에 존재하는 작은 상태 머신이다.
`{enter, update}` 멤버 함수 쌍으로 이루어진 다섯 항목의 테이블이 정적 초기화 시점에 만들어지고,
대화 요청은 요청 바이트에 상태 번호를 쓴다. 머신은 유휴 상태일 때에만 요청을 알아채고, 이를 래치한 뒤
그 항목의 `enter`를 한 번, `update`를 매 프레임 실행한다. 어떤 대사가 나오는지는 더 아래에서, 머신이
시작되는 순간 NPC에 바인딩된 스크립트가 결정한다. 선택지 프롬프트와 두 개의 이름 키보드는 같은
대화가 구동하는 별도의 화면이다.

## 무슨 일이 일어나는가

대화 테이블은 `data_021c17c4`이다. `{enter, update}` 멤버 함수 포인터로 된 16바이트 항목 다섯 개이며,
정적 초기화 시점에 `__sinit_020c4270`이 채운다
[S: data_021c17c4, main, port/shim/game/w1_taxitalk.c]. 항목들은 일반 함수 포인터가 아니라 멤버
포인터이므로 mwcc의 `{lo, hi}` 쌍이며, 디스패치는 포트의 단일 멤버 포인터 해석기를 거친다
[S: port/shim/game/memptr.c, port/shim/game/w1_taxitalk.c].

머신의 상태는 작은 객체(`sm`)의 세 바이트에 있다. `f9`는 요청, `f8`은 현재 상태, `fa`는 하위 상태다
[S: func_020146cc / func_02014688, main, port/shim/game/w1_taxitalk.c]. 유휴는 `f9 == 5`이다
[S: func_02014788, main, port/shim/game/w1_taxitalk.c]. 호출자는 `f9`에 상태 번호를 써서 대화를
요청한다. `func_020147e0(obj + 0x618, 1, 0)`은 `func_02014788(sm, 1, ...)`에 도달하며, 이는
`sm->f9 == 5`를 요구한 뒤 `sm->f9 = 1`을 설정한다
[S: func_020147e0 / func_02014788, main, port/shim/game/w1_taxitalk.c]. 요청은 `func_020146cc`가
받아들이는데, 그 조건은 `sm->f9 < 5 && sm->f8 == 5`이다. 이 함수는 `sm->f8 = sm->f9`로 래치하고,
`sm->fa = 0`으로 지우고, `gTbl[1].enter = func_02014060`을 실행한다
[S: func_020146cc, main, port/shim/game/w1_taxitalk.c]. 매 프레임
`func_02014688`은 `gTbl[1].update = func_02013e68`을 실행하며, 이는 `sm->fa`에 따라 하위 테이블로
디스패치하여 `func_0201404c`에 도달한다
[S: func_02014688 / func_02013e68, main, port/shim/game/w1_taxitalk.c].

"대화가 시작된다"를 "이 NPC가 이 대사를 한다"로 바꾸는 바인딩은 `func_02014718`이다. 이 함수는
`npc->f634 != 0`을 요구한 뒤, `func_0203ee14 -> func_02068340`을 거쳐 바인딩하고, `func_020a8164`로
스크립트를 붙이고, `p->f1e`에서 키를 가져오고, `p->f40->f8 = 1`을 설정하여 대화를 준비(arm)한다
[S: func_02014718, main, port/shim/game/w1_taxitalk.c]. `npc->f634`는 씬 자신의 슬롯 1
(`func_ov051_02261364 -> func_0201c280(self, self + 0x658)`)이 `npc + 0x658`로 설정한다
[S: func_ov051_02261364, ov051, port/shim/game/w1_taxitalk.c]. 즉 어떤 요청이든 성공하려면 그 전에
NPC에 대화 하위 구조가 주어져 있어야 한다
[S: port/shim/game/w1_taxitalk.c].

NPC 쪽에는 게이트가 하나 더 있다. 그 프레임당 스텝 `func_0201b910`은 `self->f561 != 0`일 때에만
`func_02014688(self + 0x618, self)`를 호출하며, 그 바이트는 `func_0201bdb4`가 1로 설정한다
[S: func_0201b910 / func_0201bdb4, main, port/shim/game/w1_taxitalk.c].

게임의 첫 대화인 택시 안의 갑돌이는 씬 쪽 게이트가 붙은 전체 체인을 보여준다.
`func_ov051_0226131c`(vtable `0x0226193c` 슬롯 0)는 씬 상태 0을 설정하고 `self + 0x718`에 41프레임
카운트다운 `0x29`를 쓴다
[S: func_ov051_0226131c, ov051, port/shim/game/w1_taxitalk.c]. 프레임당 스텝
`func_ov051_02261270`은 `(self->*tbl[self->f654].update)()`이다
[S: func_ov051_02261270, ov051, port/shim/game/w1_taxitalk.c]. 씬 상태 0의 update인
`func_ov051_022611e0`은 화면 페이드가 끝났을 것(`*(u8 *)0x021c75b8 == 2`, 여기서 0은 유휴, 1은
페이드 인, 3은 페이드 아웃)과 카운트다운이 만료되었을 것(`func_020e8840(self + 0x718) == 0`)을
요구하며, 그런 뒤에야 씬 상태 1로 진행하고, 그 enter가 대화 요청을 발행한다
[S: func_ov051_022611e0, ov051, port/shim/game/w1_taxitalk.c].

대화 및 메뉴 위젯은 공유 번역 단위에서 만들어지며, 그 템플릿은 아홉 인수 생성자인 `func_0202da38`이다.
`Self` 레이아웃은 `f100`, 배열 `f104[0x1e]`, `f122`를 담고 있으며, 그 범위 게이트 중 하나는
volatile 이중 읽기다
[S: func_0202da38 / func_020224c4, main, src/matched/func_020224c4.c and
src/matched/func_0202b800.c]. 배열 항목 수 `0x1e`는 위젯의 항목 용량이다
[S: src/matched/func_0202b800.c].

작은 `ov002` 상태 함수 한 쌍이 약 스무 개의 작은 NPC/대화 오버레이에서 호출되며, 호출 지점은 총
34곳이다. 즉 NPC별 대화 코드는 하나의 상태 헬퍼를 공유하는 수많은 작은 오버레이에 흩어져 있다
[S: ov002, port/shim/c6d_ov002state.c]. 스크립트 자체는 ov068 자신의 풀에 이름이 있다:
`q10_call`, `q10_back`, `q10_wait`, `q10_door`, `q10_first`, `q10_furniture`, `q10_layout`,
즉 도착 시퀀스의 질문 스크립트가 라벨별로 나열되어 있다
[S: ov068 pool words, docs/kb/modules/ov003-068.md]. 메시지 텍스트는 ROM 파일 시스템에 BMG 파일로
저장된다 [S: port/VISIBLE-STATE.md, filesystem search returning twelve BMG files].

갑돌이 자신의 대사는 플래그로 선택된다. `func_ov080_02278c88`은 플레이어의 이벤트 플래그 1을 읽어
평소의 `sp_npc_turtle` 대사 대신 인트로 그룹 `sp_etc_sequence5_2`를 고른다
[S: func_ov080_02278c88, ov080, port/shim/game/spnpc.c]. 따라서 대화 선택은 NPC의 상태만이 아니라
플레이어의 진행 비트필드를 직접 참조한다
[S: port/shim/game/spnpc.c].

스크립트된 A 펄스로 대화를 구동하는 인터프리터 경로에서 관측된 바는 다음과 같다
[E: docs/log/cycle40-keyboard-gate-probe.md TAP40/MENU40/LONG40/TOWN40/LONG41, runs
`tap-native`, `menu-a`, `menu-b`, `long-a`, `tap-D56`, `tap-D59`]:

- 첫 번째 키보드는 `당신 이름은?`을 묻는다. 두 번의 탭이 약 7,500프레임에서 이름을 확정한다.
- 이어서 운전수(`운전수`)가 입력된 이름에 반응하고, 두 선택지 확인 메뉴 `그렇대두! / 아니야`가
  표시된다.
- 대화는 탭이 멈출 때에만 계속된다. 대화 중의 스타일러스 접촉은 대화를 진행시키지 않으며, 반복되는
  탭은 확인 메뉴를 2,300프레임 동안 열린 채로 유지시켰다.
- 13,500프레임에 다섯 선택지 목적지 메뉴가 나타난다:
  `바다 / 마을사무소 / 가게 / 관문 / 박물관`.
- 16,500에 두 선택지 돈 질문이 이어진다 (`돈 있어 / 조금밖에 없어`).
- 두 번째 키보드는 약 24,000프레임에 `마을 이름은?`을 묻고 24,600에 두 번의 탭으로 확정된다.
- 40,500프레임부터 마을 회관에서 `펠리`(Pelly)가 말하고 선택지 프롬프트가 화면에 있다. 그녀는
  60,000에 작별 인사를 하고, 스크립트된 A 펄스가 90,000까지 대화를 다시 시작시킨다
  (`어머 무슨 일 있으신가요?`).

기록에 남은 두 가지 모순이 있으며, 이는 잡음이 아니라 내용이다. 첫째, DeSmuME 레퍼런스와 포트는
6,000프레임부터 24,000프레임까지 한 단계씩 일치하다가(아래 화면 ncc 0.9997-1.0000) 25,500에서
갈라진다. 포트의 두 탭은 마을 이름을 확정하지만 레퍼런스의 동일한 탭은 그러지 않아, 48,000까지
마을 이름 키보드에 머문다
[O: docs/log/cycle40-keyboard-gate-probe.md ORACLE41, `scratchpad/oracle/tap-fullpad`]
[E: `tap-D56`]. 해결됨(ORACLE42): 24,600의 탭은 KEYS3의 A 누름 프레임(2400 + 37 x 600)에
떨어지고, 레퍼런스의 스타일러스 샘플은 포트보다 1-2프레임 늦게 게임에 도달하므로, 둘은 누름과 탭의
순서를 다르게 매긴다. 탭을 24,700으로 옮기면 둘 다 확정하고 일치한다(24000..27000의 11프레임,
ncc 0.9955, 위 화면 1.0000)
[O: `scratchpad/oracle/tap-24700`] [E: `tap-D62`] [S: docs/log/cycle40-keyboard-gate-probe.md ORACLE42].
포트가 그 지연을 모델링해야 하는지는 아래의 가설이다. 둘째, 스크립트된 실행은 마을 회관을 떠날 수
없지만(A 펄스가 펠리의 대화를 영원히 다시 연다), 키보드를 쥔 사람은 떠날 수 있다
[E: docs/log/cycle40-keyboard-gate-probe.md LONG41, `tap-D59`].

키보드는 `ov126`이다. 그 터치 디스패처 `func_ov126_022a1228`은 `0x022a1229`(Thumb)를 가리키는
`0x022a1ff0`의 ov126 재배치를 통해 함수 포인터로만 설치된다
[S: ov126, docs/log/cycle40-keyboard-gate-probe.md PROBE40]. 키보드를 닫는 것은
`func_ov126_022a1a54`이며, 이는 `0x022a1a58`에서 자신의 객체를 `func_020ee470`에 넘기고 1을 반환한다
[S: func_ov126_022a1a54, ov126, port/shim/game/keyboardclose.c]. 준비 여부 검사
`func_ov002_022081dc`는 `func_020ee550`에 넘기고 결과를 0 또는 1로 정규화한다
[S: func_ov002_022081dc, ov002, port/shim/game/keyboardready.c].

## 어디에 있는가

| 함수 또는 심볼 | 모듈 | 역할 | 등급/출처 |
|---|---|---|---|
| `data_021c17c4` | main | 5 x `{enter, update}` 대화 테이블 | S: port/shim/game/w1_taxitalk.c |
| `__sinit_020c4270` | main | 정적 초기화 시점에 그 테이블을 채움 | S: port/shim/game/w1_taxitalk.c |
| `func_02014788` | main | `sm->f9 == 5`일 때 대화 요청을 수락 | S: port/shim/game/w1_taxitalk.c |
| `func_020146cc` | main | 요청을 래치: `f8 := f9`, `fa := 0` | S: port/shim/game/w1_taxitalk.c |
| `func_02014060` | main | `gTbl[1].enter` | S: port/shim/game/w1_taxitalk.c |
| `func_02013e68` | main | `gTbl[1].update`, `sm->fa`에 따라 디스패치 | S: port/shim/game/w1_taxitalk.c |
| `func_02014718` | main | 스크립트와 키를 바인딩하고 대화를 준비 | S: port/shim/game/w1_taxitalk.c |
| `func_020a8164` | main | 대화 스크립트를 붙임 | S: port/shim/game/w1_taxitalk.c |
| `func_0201b910` | main | NPC 프레임당 스텝, `self->f561`로 게이트됨 | S: port/shim/game/w1_taxitalk.c |
| `func_ov051_022611e0` | ov051 | 택시 씬 상태 0: 페이드 + 카운트다운 게이트 | S: port/shim/game/w1_taxitalk.c |
| `func_0202da38` | main | 아홉 인수 메뉴/대화 위젯 템플릿 | S: src/matched/func_0202b800.c |
| `func_ov080_02278c88` | ov080 | 갑돌이의 인트로 대 평소 대사 그룹 선택 | S: port/shim/game/spnpc.c |
| `func_ov126_022a1228` | ov126 | 키보드 터치 디스패처 (함수 포인터로만) | S: docs/log/cycle40-keyboard-gate-probe.md |
| `func_ov126_022a1a54` | ov126 | 키보드 닫기 | S: port/shim/game/keyboardclose.c |

## 읽고 쓰는 데이터

| 주소 또는 필드 | 의미 | 쓰는 쪽 | 읽는 쪽 |
|---|---|---|---|
| `0x021c17c4` | 5항목 대화 테이블 | `__sinit_020c4270` | `func_020146cc`, `func_02014688` |
| `sm->f9` | 요청된 대화 상태; 5 = 유휴 | `func_02014788` | `func_020146cc` |
| `sm->f8` | 현재 대화 상태 | `func_020146cc` | `func_020146cc` |
| `sm->fa` | update 하위 테이블의 하위 상태 인덱스 | `func_020146cc` | `func_02013e68` |
| `npc->f634` | NPC의 대화 하위 구조 포인터 | `func_ov051_02261364` | `func_02014718` |
| `npc + 0x618` | 대화 머신 객체 | 씬 초기화 | `func_020147e0`, `func_02014688` |
| `npc->f561` | "이 NPC는 대화 스텝을 실행해도 됨" | `func_0201bdb4` | `func_0201b910` |
| `p->f1e` | 대화 키 | `func_02014718` | 스크립트 |
| `p->f40->f8` | "준비됨" 바이트 | `func_02014718` | 스크립트 러너 |
| `0x021c75b8` | 화면 페이드: 0 유휴, 1 인, 2 완료, 3 아웃 | 페이드 매니저 | `func_ov051_022611e0` |
| `ov051 self + 0x718` | 41프레임(`0x29`) 씬 카운트다운 | `func_ov051_0226131c` | `func_020e8840` |
| `0x022a1ff0` (ov126 reloc) | 키보드의 터치 디스패처 포인터 | 오버레이 로드 | 키보드 스텝 |

모든 행은 S 등급이며, 이전 표의 파일에서 인용했다.

## 확인 방법

`port/shim/game/w1_taxitalk.c`는 정확히 이 게이트들에 대한 읽기 전용 프로브다. `0x021c75b8`의
페이드 상태를 네 값의 이름과 함께 출력하고, `0x021c17c4`의 다섯 `{enter, update}` 쌍 모두를 변화
시점과 2의 거듭제곱 하트비트마다 출력하여 침묵이 결코 모호하지 않게 한다
[S: port/shim/game/w1_taxitalk.c]. 이로써 "테이블이 0이다"와 "테이블이 잘못되었다"를 구별할 수
있으며, 이것이 모든 대화 조사가 출발하는 구별점이다
[S: port/shim/game/w1_taxitalk.c].

대화를 재현하려면 마을 레시피(`town.md` 참조)를 실행하고 9,000 / 13,500 / 16,500 / 24,000 / 40,500의
스크린샷을 읽는다
[E: docs/log/cycle40-keyboard-gate-probe.md, `tap-D56`, `long-a`].

## 가설

- 포트는 예약된 스타일러스 샘플을 같은 프레임에 `TP_POINT`로 전달하지만, 하드웨어의 ARM7 샘플링과 PXI 왕복은 1-2프레임을 더한다. port/shim/input/touch.c에서 그 지연을 모델링하면 24,600 레시피가 레퍼런스처럼 동작할 것이다 [H: re-run `tap-D56`'s recipe after the change and compare with `scratchpad/oracle/tap-fullpad` at 25,500].

- **H: 다섯 개의 대화 테이블 항목은 다섯 가지 대화 종류(일반 주민, 특수 NPC, 표지판/게시판, 편지,
  시스템 프롬프트)이며, `sm->f9`는 그 종류를 지정한다.** 관측된 요청 값은 1이고 유휴는 5이므로,
  0..4가 실제 항목이고 5는 "없음"이다
  [S: port/shim/game/w1_taxitalk.c]. 실험: 마을 회관 실행과 주민 대화에 걸쳐 수락된 모든 요청에서
  `sm->f9`를 기록하고 몇 개의 서로 다른 값이 나타나는지 본다.
- **H: `sm->fa`는 고정된 대사 진행 시퀀스(상자 열기 -> 출력 -> A 대기 -> 닫기)를 따라가며, 그래서
  600프레임당 한 번의 A 펄스로 택시 대화 전체가 진행된다.**
  `func_02013e68`은 `fa`에 따라 디스패치한다 [S: port/shim/game/w1_taxitalk.c]
  [E: docs/log/cycle40-keyboard-gate-probe.md MENU40]. 실험: `tap-D59`에서 펠리의 대사 한 줄에 걸쳐
  프레임당 `fa`를 기록한다.
- **H: 선택지 프롬프트는 `f104[0x1e]`가 채워진 대화 상자와 같은 위젯이며, 답은 스크립트가 재개되기
  전에 `sm`에 다시 쓰인다.** 템플릿은 공유된다
  [S: src/matched/func_0202b800.c]. 실험: 다섯 선택지 목적지 메뉴와 일반 대사에서 `func_0202da38`의
  아홉 인수를 계측한다.
- **H: 대화 중의 스타일러스 접촉은 "취소/유지" 입력으로 소비되며, 그래서 반복되는 탭이 확인 메뉴를
  얼렸다.** 측정된 동작이며, 메커니즘은 읽지 않았다
  [E: docs/log/cycle40-keyboard-gate-probe.md TAP40/MENU40, `tap-D55b`, `menu-a`]. 실험: 대사
  도중 접촉을 유지하는 동안 `func_020b755c`의 분류와 `sm->fa`를 계측한다.
- (해결됨, 기록용으로 유지.) ADC 왕복은 원인이 아니었다. 222,182에서 `tap-D61`은 여전히 확정하고
  220,180에서 `scratchpad/oracle/tap-220`은 여전히 확정하지 않는다. 프레임은 (원문 문장이 여기서 끊긴다)
  [S: docs/log/cycle40-keyboard-gate-probe.md ORACLE42] [E: `tap-D61`]
  [O: `scratchpad/oracle/tap-220`].
- **H: `func_020a8164`는 NPC의 종과 성격 및 플레이어의 이벤트 플래그에서 파생된 스크립트 id를 받으며,
  따라서 대화의 다양성은 무작위 선택이 아니라 테이블 조회다.** 갑돌이의 그룹은 이미 이벤트 플래그로
  선택된다고 알려져 있다
  [S: port/shim/game/spnpc.c]. 실험: 같은 날 서로 다른 세 주민에 대해 `func_020a8164`의 인수를
  기록한다.
- **H: `q10_*` 라벨은 도착 설문의 일곱 단계이며, 택시 대화의 관측된 박자에 일대일로 대응된다.**
  라벨은 일곱 개이고, 관측된 대화에는 이름 프롬프트, 확인, 목적지 메뉴, 돈 질문, 마을 이름
  프롬프트가 있다
  [S: docs/kb/modules/ov003-068.md] [E: `tap-D56`]. 실험: `func_020a8164`를 계측하고 택시 대화가
  로드하는 각 스크립트의 라벨을 출력한다.

## 관련 문서

- `player.md` -- 대화 선택이 읽는 이벤트 비트필드
- `villagers.md` -- 대사와 나란히 실행되는 표정 롤
- `town.md` -- 레퍼런스 실행이 끝나는 마을 회관
