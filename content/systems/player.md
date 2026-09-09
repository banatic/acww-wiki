# 플레이어
<!-- source: wiki/systems/player.md -->

**요약.** 세이브에는 각각 `0x249c`바이트인 플레이어 슬롯 네 개가 세이브 이미지의 앞부분 근처에 끝과 끝을 맞대고 배치되어 있다. 각 슬롯은 게임이 자체 진행 기록으로 쓰는 64비트 이벤트 비트필드를 갖는다 -- 예를 들어 오프닝 시퀀스는 그 안의 비트 하나이다. 플레이어 이름은 첫 번째 키보드 화면에서 입력한다; 게임은 택시를 타기 전에 이름을 묻고, 마을 이름은 나중에 묻는다. 플레이 중에 플레이어 객체는 패드와 스타일러스 입력 한 프레임을 이동 의도(intent) -- 속도, 방향, 달리기 플래그, 목표 위치, 입력 모드 -- 로 바꾸며, 나머지 갱신은 원시 입력이 아니라 그 블록을 소비한다.

## 무슨 일이 일어나는가

플레이어 배열은 세이브 `+0x14` = `0x021dc7bc`에서 시작하며 스트라이드는 `0x249c`이므로, 플레이어 0의 이벤트 워드는 슬롯 `+0x23f8` = `0x021debb4`에 있다
[S: func_02098844, main, port/shim/game/newgameprobe.c]. 새 세이브 경로에서는 `func_0209ef7c`가 플레이어 슬롯 네 개를 초기화한다 [S: func_0209ef7c, main, port/shim/game/newgameprobe.c].
활성 플레이어는 `func_020984e8`이 돌려준다
[S: func_020984e8, main, port/shim/game/spnpc.c].

`player + 0x23f8`의 64비트는 게임의 이벤트 플래그이다. `func_02099020(player, bit)`는 하나를 검사하고 `func_02098ff8(player, bit)`는 하나를 설정한다
[S: func_02099020 / func_02098ff8, main, port/shim/game/spnpc.c]. 플래그 1은 오프닝 자체의 상태 비트이다: 도착 시퀀스 내내 설정되어 있다가 시퀀스가 끝나면 지워지며, 매칭된 트리에서 이를 지우는 단 두 곳은 `func_ov050_02262628`(너굴 쪽)과 `func_ov068_0226e948`이다 [S: ov050/ov068, port/shim/game/spnpc.c]. 이것이 설정되어 있는 동안에는 `0x020e1d08`의 특수 NPC 결정자 테이블에 있는 열한 개 술어 모두가 중단하므로, 오프닝 동안 특수 NPC 스케줄 전체가 설계상(BY DESIGN) 침묵한다
[S: func_02084af0, main, port/shim/game/spnpc.c].

그 비트필드를 쓰는 함수는 단 넷이며, 각각 같은 세 연산 -- `set(1); set(0x23); clear(9)` -- 을 수행한다: `func_0209ee54`(인덱스 0), `func_0209ed90`(1), `func_0209eac8`(5), `func_0209ea24`(6)
[S: main, port/shim/game/newgameprobe.c]. 어느 것이 실행될지는 `func_ov051_022610d4`가 `0x021f3c30`의 부팅 모드 워드로부터 고른다: 1은 인덱스 0을, 2는 인덱스 1을, 3은 인덱스 6을 선택한다 [S: func_ov051_022610d4, ov051, port/shim/game/newgameprobe.c]. `func_020a1320`은 그 워드를 1로 설정하는 유일한 설정자이다 [S: func_020a1320, main, port/shim/game/newgameprobe.c].
이것이 플레이어 비트필드가 여전히 0인 채로 세이브가 -- 지형까지 전부 -- 생성될 수 있는 이유이다: 생성(`func_0209ebec`)은 아직 플레이어가 존재하지 않으므로 의도적으로 플레이어 상태를 전혀 쓰지 않는다 [S: func_0209ebec, main, port/shim/game/newgameprobe.c].

플레이어 이름은 택시를 타기 전에 먼저 묻는다. 화면의 프롬프트는 `당신 이름은?`이며, 레퍼런스 실행에서는 약 프레임 7,500에 이름이 확정되고 그 뒤 게임이 오버레이 하나를 언로드한다
[E: docs/log/cycle40-keyboard-gate-probe.md OVL40/TOUCH40, `tap-D55`]. 키보드는 첫 번째(FIRST) 스타일러스 탭을 패드(PAD)에서 스타일러스로의 모드 전환으로 소비하므로 탭 한 번으로는 절대 확정되지 않는다; 창 안에서의 탭 두 번이면 확정된다 [E: docs/log/cycle40-keyboard-gate-probe.md TAP40, `tap-D55`]
[S: port/shim/input/touch.c]. 같은 동작이 첫 번째 키보드에 대해 DeSmuME 레퍼런스에서도 재현되었고, 이것이 포트가 이 점에서 틀리지 않았음을 확정지었다
[O: docs/log/cycle40-keyboard-gate-probe.md ORACLE41, `scratchpad/oracle/tap-fullpad`
frames 6000-24000, bottom-screen ncc 0.9997-1.0000].

이동은 프레임마다 한 번 `func_0200dc98`(`main`의 `0x794`바이트, Thumb, 미매칭)이 구성하는데, 이 함수는 `0x021fbe40`의 패드 워드와 터치 드래그 헬퍼 `func_020b755c` / `func_020b758c`를 읽고 `self + 0x134`..`0x170`에 의도 블록을 쓴다
[S: func_0200dc98, main, port/shim/c6a_0200dc98_intent.c]. 함수 자체의 풀과 데이터 흐름에서 읽어 낸 필드는 다음과 같다: `+0x134`는 `[0, 0x1000]`으로 클램프된 `fx12` 걷기 속도; `+0x138`은 `func_020e8ed8(dx, dz)` 또는 `0x021fbe44`의 패드 자체 방향 하프워드에서 온 `s16` 각도의 걷기 방향; `+0x13a`는 속도가 `0xc32`를 넘거나 B/X/Y가 눌려 있을 때 설정되는 달리기 플래그; `+0x13c`는 `func_020b7524`에서 온 탭 목표; `+0x144`는 1 또는 2의 탭 클래스; `+0x16d`는 터치 코드; `+0x14c`와 `+0x158`은 세 워드짜리 위치 둘(기억된 목표와 해석된 목표); 그리고 `+0x170`은 입력 모드로, 패드는 1, 터치는 2이며 어느 쪽도 그 프레임을 차지하지 않으면 진입 시 값이 보존된다
[S: func_0200dc98, main, port/shim/c6a_0200dc98_intent.c]. 터치 분류는 `0x0200ddd8`의 하프워드 오프셋 테이블에서 해독되는 18갈래 switch이다
[S: func_0200dc98, main, port/shim/c6a_0200dc98_intent.c].

그 블록은 참고용이 아니라 필수적이다: 함수를 0을 돌려주도록 스텁 처리하면 실행이 곧 `func_0200d900` 안에서 폴트를 일으킨다
[E: port/shim/c6a_0200dc98_intent.c, `ACWW_EXPLORE=1` run].

플레이어 집은 주민 집과 별개의 에셋 계열이다:
`/str/plHsTex/home%c%c.nsbtx`가 ov003 자체의 표기이다
[S: ov003 pool words, docs/kb/modules/ov003-068.md].

DS 펌웨어의 사용자 설정은 게임이 읽는 닉네임과 생일을 제공한다. 펌웨어 레코드의 `birthMonth`는 `+0x03`에, `birthDay`는 `+0x04`에 있다
[S: port/shim/boot/usersettings.c]. 포트는 자체 값 -- 닉네임 `PLAYER`, 생일 1월 1일 -- 을 제공하고 그렇다고 명시하는데, 이는 복원이 아니라 포트의 선택이기 때문이며, 닉네임은 게임 안에 실제로(IS) 표시된다 [S: port/shim/boot/usersettings.c].

## 어디에 있는가

| 함수 또는 심볼 | 모듈 | 역할 | 등급/출처 |
|---|---|---|---|
| `func_020984e8` | main | 활성 플레이어 객체를 돌려줌 | S: port/shim/game/spnpc.c |
| `func_02098844` | main | 플레이어 슬롯 스트라이드 `0x249c` | S: port/shim/game/newgameprobe.c |
| `func_02099020` | main | 플레이어 64비트 필드의 이벤트 플래그 `n` 검사 | S: port/shim/game/spnpc.c |
| `func_02098ff8` | main | 이벤트 플래그 `n` 설정 | S: port/shim/game/spnpc.c |
| `func_0209ee54` / `_ed90` / `_eac8` / `_ea24` | main | 새 게임 플레이어 커밋 넷 | S: port/shim/game/newgameprobe.c |
| `func_ov051_022610d4` | ov051 | `0x021f3c30`으로부터 어느 커밋이 실행될지 선택 | S: port/shim/game/newgameprobe.c |
| `func_0200dc98` | main | 이동 의도 빌더 | S: port/shim/c6a_0200dc98_intent.c |
| `func_020b755c` / `func_020b758c` | main | 의도에 공급되는 터치 드래그 분류 | S: port/shim/c6a_0200dc98_intent.c |
| `func_020e8ed8` | autoload_2 | 사인 테이블 기반 `atan2`, 걷기 각도를 냄 | S: port/shim/c6a_0200dc98_intent.c |
| `0x020e1d08`의 `func_02099020` 호출자들 | main | 플래그 1로 게이트되는 특수 NPC 술어 열한 개 | S: port/shim/game/spnpc.c |

## 읽고 쓰는 데이터

| 주소 또는 필드 | 의미 | 쓰는 쪽 | 읽는 쪽 |
|---|---|---|---|
| `0x021dc7bc` | 플레이어 배열, 슬롯 4개, 스트라이드 `0x249c` | `func_0209ef7c` | `func_020984e8` |
| 슬롯 `+0x23f8`(슬롯 0은 `0x021debb4`) | 64비트 이벤트 비트필드 | 커밋 넷, `func_02098ff8` | `func_02099020` |
| 이벤트 플래그 1 | "오프닝이 진행 중" | `func_0209ee54` 계열 | `0x020e1d08`의 술어 11개 |
| `0x021f3c30` | 커밋을 고르는 부팅 모드 워드 | `func_020a1320` | `func_ov051_022610d4` |
| `0x021fbe40` / `+4` | 이번 프레임의 패드 워드 / 방향 하프워드 | 입력 | `func_0200dc98` |
| `self + 0x134`..`0x170` | 이동 의도 블록 | `func_0200dc98` | 플레이어 갱신의 나머지 |
| `self + 0x170` | 입력 모드: 1 패드, 2 터치 | `func_0200dc98` | 플레이어 갱신 |
| 펌웨어 `+0x03` / `+0x04` | 생일 월 / 생일 일 | 펌웨어(포트: `usersettings.c`) | 게임 인사 경로 |

모든 행은 S 등급이며, 앞 표의 파일들에서 인용했다.

## 확인 방법

`port/shim/game/spnpc.c`는 `ACWW_TRACE_STATE=1` 아래에서 그 튜플이 바뀔 때마다 `acww intro: f<frame> player <ptr> flag1 <v> bits <w0>/<w1> mode <m> 54a8 <b>`를 출력한다; 게임이 아직 오프닝 중이라고 믿는지를 말해 주는 단 하나의 줄이다
[S: port/shim/game/spnpc.c]. `port/shim/game/newgameprobe.c`는 새 게임의 두 절반 -- 부팅 생성과 플레이어 커밋 -- 중 어느 것이 일어났는지를, 한쪽에서 다른 쪽을 추론하지 않고 직접 보고한다 [S: port/shim/game/newgameprobe.c].

이름 프롬프트에 대해서는 마을 레시피를 실행하고 프레임 4,500에서 7,500을 본다: 키보드가 있는 택시 실내, 그 다음 확정
[E: docs/log/cycle40-keyboard-gate-probe.md TOWN40, `tap-D56`].

## 가설

- **H: `0x249c` 플레이어 슬롯은 주머니(인벤토리), 편지, 카탈로그를 담고 있으며, 이들은 슬롯 안에서 연속된 블록이다.** 슬롯은 크고 이벤트 비트필드는 끝 근처 `+0x23f8`에 있다 [S: port/shim/game/newgameprobe.c]. 실험: 라이브 실행에서 아이템 하나를 줍기 전후에 세이브 이미지 둘을 뜬 뒤 diff하고, 슬롯 안에서 어느 오프셋이 바뀌는지 기록한다.
- **H: 커밋 넷 모두가 플래그 1과 함께 설정하는 이벤트 플래그 `0x23`은 "이 플레이어가 생성되었음"이다.** 넷 모두 `set(1); set(0x23); clear(9)`를 수행한다
  [S: port/shim/game/newgameprobe.c]. 실험: 매칭된 트리에서 `func_02099020(..., 0x23)` 호출 지점을 grep하고 각각이 무엇을 게이트하는지 읽는다.
- **H: 커밋 넷 모두가 지우는(CLEAR) 플래그 9는 "돌아온 플레이어" 또는 튜토리얼 완료 비트이다.** 같은 근거이다 [S: port/shim/game/newgameprobe.c]. 실험: 비트 9에 대해 같은 grep을 하고, 택시 전에 `func_02098ff8`로 손수 설정한 뒤 어떤 대화가 바뀌는지 본다.
- **H: 플레이어 자신의 이름은 `0x249c` 슬롯 안의 시작 근처 고정 오프셋에 UTF-16으로 저장된다.** 마을 이름은 다른 루틴이 마을 영역에 찍는다
  [S: port/shim/game/newgameprobe.c] [E: docs/log/cycle40-keyboard-gate-probe.md TOWN40].
  실험: 서로 다른 플레이어 이름을 입력해 레시피를 두 번 실행하고 슬롯을 diff한다.
- **H: 걷기 속도 클램프 `[0, 0x1000]`과 달리기 임계값 `0xc32`는 달리기가 최대 스타일러스 드래그 속도의 약 76%이고 B를 누르고 있어도 도달할 수 있음을 뜻한다.** 두 상수 모두 풀 워드이다 [S: port/shim/c6a_0200dc98_intent.c]. 실험: 라이브 실행에서 마우스를 플레이어로부터 여러 거리에 두고 `+0x134`와 `+0x13a`를 기록한다.
- **H: 도구는 별도의 도구 슬롯이 아니라 의도 블록의 탭 목표 필드에 보관된다 -- 즉 도구는 지속적인 손의 속성이 아니라 행동의 속성이다.** `+0x13c`는 탭 목표이고 `+0x144`는 탭 클래스이다 [S: port/shim/c6a_0200dc98_intent.c]. 실험: 플레이어가 도구를 든 상태에 도달한 뒤 `self + 0x134`..`0x170`을 도구 없는 프레임과 비교해 살펴본다.
- **H: 플레이어 슬롯 넷은 마을이 가질 수 있는 거주자 넷이며, 부팅 모드 워드 1/2/3은 첫 플레이어 / 추가 플레이어 / 가져온 플레이어에 대응한다.**
  `func_ov051_022610d4`는 1, 2, 3을 서로 다른 세 커밋으로 사상한다
  [S: port/shim/game/newgameprobe.c]. 실험: 워드를 차례로 2와 3으로 강제하고 결과 커밋이 어느 슬롯에 쓰는지 기록한다.

## 관련 문서

- `town.md` -- 플레이어 배열이 사는 세이브 이미지
- `dialogue.md` -- 플레이어가 답하는 키보드와 선택 프롬프트
- `events-and-calendar.md` -- 게임의 진행 기록으로서의 이벤트 비트필드
