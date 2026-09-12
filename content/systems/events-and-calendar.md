# 이벤트와 달력
<!-- source: wiki/systems/events-and-calendar.md -->

**요약.** 게임의 달력은 NitroSDK를 통해 읽은 DS의 실시간 시계(RTC)이며, 열두 갈래의 switch 문으로
계절에 대응되고, 두 번째 매핑으로 열네 값의 계절/이벤트 인덱스에 대응된다. 특정 날에 무슨 일이
일어나는지는 두 곳에서 결정된다. 하나는 날짜가 넘어갈 때마다 한 번 실행되어 상태 블록을 다시 쓰는
날짜 변경 루틴이고, 다른 하나는 매 프레임 실행되는 특수 NPC 스케줄러다. 후자는 스물세 개 항목으로
된 방문객 테이블 위에서 우선순위 순으로 열한 개의 술어(predicate)를 평가하며, 각 항목은 그 방문객을
데려오는 데 필요한 채널, 액터, 오버레이, 플래그를 지정한다. 플레이어 자신의 64비트 이벤트 비트필드가
두 쪽 모두가 참조하는 진행 기록이다.

## 무슨 일이 일어나는가

날짜와 시간은 SDK에서 온다. `0x0211e7c0`과 그 이웃에 있는 `RTC_GetDateTime`, `RTC_GetTime`,
`RTC_GetDate`이다 [H: source account: NitroSDK, port/shim/os/rtcclock.c; direct ROM-source provenance unresolved]. 게임은 시계를 설정하기도 한다.
`func_0209e5b4`는 `RTC_SetDateTime(date, time)`을 호출하며, 호출 전후로 `r1`이 건드려지지 않으므로
시간 포인터가 그대로 전달된다
[S: func_0209e5b4, main, port/shim/game/arity_func_0209e5b4.c]. 그 경로에는 연도 0 / 월 1 / 일 1일 때
요일을 6으로 강제하는 날짜 검사가 있어, `r0`이 날짜라는 것을 뒷받침한다
[S: `src/matched/func_0209e5b4.c`; historical account: port/shim/game/arity_func_0209e5b4.c].

날짜 변경 자체는 `func_02040c90`이다. 이 함수의 열일곱 개 호출은 디스어셈블리와 하나하나 순서대로
일치한다: `func_0209e474`, `func_0209ded0`, `func_0209e314`, `func_020409c8`(두 번), `func_0204101c`,
`func_02041140`, `func_02040e44`, `func_02040f8c`, `func_02040f04`, `func_02040da8`, `func_02040bcc`이며,
그 사이에 다섯 개의 `MI_CpuCopy8` 호출이 끼어들어 시퀀스 중간을 고정하고, 전역 변수는 `0x021c7584`
하나만 사용한다
[S: func_02040c90, main, port/tools/known_callees.txt:245-264]. 이 피호출 함수 중 하나에는 이름 붙이기
문제가 있다. `0x0209ded0`에는 `func_` 심볼이 없고, 테이블은 이를 `MB_GetBeaconRecvStatus`라고
부르는데, 이는 멀티부트 이름이라 날짜 변경 루틴의 피호출 함수로는 맞을 수 없으므로, 거기서는 절단
위치나 라벨 중 하나가 잘못되었다 (결함 분류 D12) [S: `config/adm-kr/arm9/symbols.txt`, `MB_GetBeaconRecvStatus` addr
`0x0209ded0`; `docs/rules/D-defects.md` D12]. 다섯 개의 블록 복사는
오늘의 상태를 쓰기 전에 어제의 상태를 이력 슬롯으로 옮기는 날짜 롤오버의 형태다
[H: read `func_02040c90`'s disassembly and name the source and destination of each copy].

계절은 월과 일의 순수 함수(`func_02063bb4`)이며, 두 번째 매핑 `func_0204fa8c`는 월을 열네 값의
인덱스로 바꾸는데, 여기서 8월과 9월은 각각 둘로 나뉜다. 둘 다 `weather-and-seasons.md`에 문서화되어
있다
[S: func_02063bb4 / func_0204fa8c, main, port/shim/game/season.c and seasonidx.c].

새 게임 생성과 달력은 결합되어 있다. 마을 디스패처의 생성 핸들러 뒤에는 "주민을 이사 오게 하는
RTC 전진"이 오고, 그 뒤에 `func_020a1038`의 세이브 삭제 경로를 그대로 따르는 생성 후 동기화가 온다
[S: func_0209e6ec, main, port/shim/gfx/pmflist.c]. 즉 새 마을은 별도의 이사 루틴이 아니라 날짜 변경
기구를 앞으로 돌려서 주민을 얻는다
[H: source account: port/shim/gfx/pmflist.c; direct ROM-source provenance unresolved].

`player + 0x23f8`에 있는 플레이어의 64비트 이벤트 비트필드가 진행 기록이다. `func_02099020`은 비트를
검사하고 `func_02098ff8`은 비트를 설정한다
[S: main, port/shim/game/spnpc.c]. 플래그 1은 도착 시퀀스다. 네 가지 새 게임 커밋 모두가 이를
설정하고, `func_ov050_02262628`(너굴 쪽)과 `func_ov068_0226e948`만이 이를 지운다
[H: source account: port/shim/game/spnpc.c, port/shim/game/newgameprobe.c; direct ROM-source provenance unresolved].

특수 NPC 스케줄러는 게임의 방문객 달력이며, 하나의 기구로서 읽을 가치가 있다. 채널 `0xd0`은 vtable이
`0x020e1cc0`인 객체를 만든다. 그 프레임당 슬롯 0은 `func_02085558`이고, 이는
`func_02084c60(self)`를 호출한다. 이것은 `0x020e1d08`에 있는 열한 항목의 PMF/우선순위 테이블이다
[S: func_02085558 / func_02084c60, main, port/shim/game/spnpc.c]. 항목 0은
`func_02084834 -> func_02084840(1)`이며, 그 게이트는 `func_02084890`이다
[S: main, port/shim/game/spnpc.c]. `func_02084890`은 네 개의 하위 결과의 논리곱으로, 첫째, 셋째,
넷째가 0이고 둘째가 0이 아닐 때에만 1을 반환한다:
`func_02073dd4(data_020ccf94, data_020ccf94->field_64)`,
`func_02086108(func_0208602c(), 8)`, `func_02084ad0()`, `func_02084af0()`
[S: func_02084890, main, port/shim/game/spnpc.c].

`func_02084af0`은 `player && func_02099020(player, 1)`, 즉 도착 플래그이며, 열한 개 술어 모두가 이
플래그가 설정되어 있는 동안 중단하므로, 오프닝 동안 방문객 스케줄 전체가 의도적으로 침묵한다
[S: func_02084af0, main, port/shim/game/spnpc.c]. 이는 실제 게임 메커니즘이지 포트 결함이 아니다
[H: source account: port/shim/game/spnpc.c; direct ROM-source provenance unresolved].

게이트를 지나면, `func_02084840`은 매개변수가 0이 아닐 때 두 가지 검사를 더 적용한다. 실내/실외
바이트 `data_020e54a8`이 0이어야 하고, `func_020b65c4`가 주는 모드가 `0x2c`가 아니어야 한다
[S: func_02084840, main, port/shim/game/spnpc.c]. `data_020e54a8`은 `func_02085558`이 분기에 사용하는
바로 그 바이트로, 0이 아니면 실내 분기를 타므로, 예정된 방문객은 건물 안에서는 준비(staging)될 수
없다
[S: func_02085558, main, port/shim/game/spnpc.c].

준비 단계는 `func_02084d34(&data_020e1b84, &data_020e1d8c, data_020d0644)`이며, 여기서
`*(u16 *)0x020e1b84`이 키이고(관측값 `0x0056`), `data_020e1d8c`는 스물세 항목의 테이블로, 항목 0은
`{channel 0x0056, actor 0xd012, overlay 0x50, pmf, flag 1}`로 읽힌다
[S: func_02084d34, main, port/shim/game/spnpc.c]. 준비된 요청에 따라 행동하는 것은
`func_02084b74(self, &data_020e1d8c, 0x17)`이며(`0x17`은 테이블의 23개 항목 수), 이는
`func_0204f934(0x50)`으로 오버레이를 마운트하고 `func_02003348(86, 0xd012, ...)`로 채널을 연다
[S: func_02084b74, main, port/shim/game/spnpc.c]. 즉 23개의 행 각각은 특수 방문객 한 명이며, 그를
데려오는 데 필요한 모든 것을 담고 있다
[H: source account: port/shim/game/spnpc.c; direct ROM-source provenance unresolved].

같은 테이블에는 두 번째 진입점에서도 도달한다. `func_020842b8`은 세 호출로 이어진 체인
(`func_0208602c -> func_020860c4 -> func_02087f30`) 뒤에
`func_02084d5c(&v, &data_020e1d8c, data_020d0644)`로 끝나는데, 이 체인은 레지스터 하나를 세 함수
모두에 관통시키며 `0x021d27c0`을 읽는다 [S: func_020842b8, main, port/shim/game/eventgate.c].

펌웨어 자체의 생일 필드(사용자 설정 레코드의 `+0x03`에 있는 `birthMonth`, `+0x04`에 있는
`birthDay`)는 게임이 읽으며, 그래서 포트는 이를 0으로 두지 않고 유효한 날짜를 공급하며 그렇게
밝히고 있다 [H: host/prose inference from port/shim/boot/usersettings.c; verify against the ROM function or symbol table and this page's recipe].

## 어디에 있는가

| 함수 또는 심볼 | 모듈 | 역할 | 등급/출처 |
|---|---|---|---|
| `RTC_GetDateTime` (`0x0211e7c0`) | main/SDK | 달력이 읽는 시계 | S: port/shim/os/rtcclock.c |
| `func_0209e5b4` | main | `RTC_SetDateTime(date, time)` 래퍼 | S: port/shim/game/arity_func_0209e5b4.c |
| `func_02040c90` | main | 날짜 변경 / 달력 갱신, 17개 호출 | S: port/tools/known_callees.txt |
| `func_02063bb4` | main | 월 + 일 -> 계절 | S: port/shim/game/season.c |
| `func_0204fa8c` | main | 월 -> 14값 계절/이벤트 인덱스 | S: src/matched/func_0204fa8c.c |
| `func_02084c60` | main | 11항목 특수 NPC 결정 테이블 `0x020e1d08` | S: port/shim/game/spnpc.c |
| `func_02084890` | main | 항목 0의 네 항 게이트 | S: port/shim/game/spnpc.c |
| `func_02084af0` | main | `player && event flag 1` -- 도착 잠금 | S: port/shim/game/spnpc.c |
| `func_02084840` | main | 방문객을 준비시킴; 실내 및 모드 검사 | S: port/shim/game/spnpc.c |
| `func_02084d34` | main | 키를 읽고 테이블 행을 고름 | S: port/shim/game/spnpc.c |
| `func_02084b74` | main | 실행: 오버레이 마운트, 채널 열기 | S: port/shim/game/spnpc.c |
| `func_020842b8` | main | 같은 방문객 테이블로의 두 번째 진입점 | S: port/shim/game/eventgate.c |
| `func_02099020` / `func_02098ff8` | main | 이벤트 플래그 검사 / 설정 | S: port/shim/game/spnpc.c |

## 읽고 쓰는 데이터

| 주소 또는 필드 | 의미 | 쓰는 쪽 | 읽는 쪽 |
|---|---|---|---|
| `player + 0x23f8` | 64비트 이벤트 비트필드 | `func_02098ff8`, 네 가지 커밋 | `func_02099020` |
| 이벤트 플래그 1 | 도착 시퀀스가 진행 중 | 새 게임 커밋 | 11개 술어 전부 |
| `0x020e1d08` | 11개 PMF/우선순위 결정자 | 정적 | `func_02084c60` |
| `0x020e1d8c` | 23개 방문객 행 `{chan, actor, overlay, pmf, flag}` | 정적 | `func_02084d34`, `func_02084b74` |
| `0x020e1b84` | 준비된 방문객 키 (`0x0056` 관측) | `func_02084d34` | `func_02084b74` |
| `data_020e54a8` | 실내 (0이 아님) / 실외 (0) | 씬 | `func_02084840`, `func_02085558` |
| `data_020e54ac` | 게임 모드 바이트 | 모드 머신 | `func_020b65c4` 호출자 |
| `0x021c7584` | 날짜 변경 루틴의 유일한 전역 변수 | `func_02040c90` | 날짜 변경 소비자 |
| `0x021d27c0` | `func_020842b8`의 체인이 읽는 워드 | `func_0208602c` 계열 | `func_02087f30` |
| 펌웨어 `+0x03` / `+0x04` | 생일 월 / 일 | 펌웨어 | 인사 경로 |

모든 행은 S 등급이며, 이전 표의 파일에서 인용했다.

## 확인 방법

`port/shim/game/spnpc.c`는 게이트 전체를 하나의 압축된 워드로 출력한다. 거절한 이유(0 준비됨,
1 게이트가 거부, 2 실내, 3 모드 `0x2c`), 게이트 비트, 네 개의 하위 결과, 실내/실외 바이트, 모드를
포함하며, 변화가 있을 때만 출력하므로 한 번도 움직이지 않는 실행은 한 줄만 출력한다
[H: host/prose inference from port/shim/game/spnpc.c; verify against the ROM function or symbol table and this page's recipe]. 그 옆에서 `acww intro:`는 플레이어 포인터, 비트필드 두 워드, 플래그 1,
모드를 출력한다
[H: host/prose inference from port/shim/game/spnpc.c; verify against the ROM function or symbol table and this page's recipe]. 둘 다 `ACWW_TRACE_STATE=1`이 필요하다
[H: host/prose inference from port/shim/game/spnpc.c; verify against the ROM function or symbol table and this page's recipe].

스케줄이 아니라 달력을 시험하려면, `ACWW_RTC_*` 계측 도구로 시계를 설정하고 자정을 넘겨 스텝하면
된다. `ACWW_RTC_TIME=000000`은 "값이 주어지지 않음"과 명시적으로 구별된다
[H: host/prose inference from port/platform/win32.c, port/shim/os/rtcclock.c; verify against the ROM function or symbol table and this page's recipe].

## 가설

- **H: `0x020e1d8c`의 23개 행은 게임의 특수 방문객 전체 명단(갑돌이, 너굴, 여우, 걸리버, 카트리나,
  웬델, 사하라, 그레이스, 조안, 피트, 필리스, 코퍼, 부커, 부엉, 거북이 촌장 등)이며, 각각 한 행씩이다.**
  각 행은 이미 채널, 액터, 오버레이, 플래그를 담고 있고 [H: source account: port/shim/game/spnpc.c; direct ROM-source provenance unresolved], ov068 자체의
  풀은 열두 개의 특수 NPC 모델 `rcn, rcc, rcs, rcd, pga, pgb, poo, ott, wip, xct, mof, end`를 지정한다
  [H: source account: docs/kb/modules/ov003-068.md; direct ROM-source provenance unresolved]. 실험: 23개 행을 덤프하고, 각 오버레이 id를 해석하고, 각
  오버레이의 풀에서 로드하는 모델 이름을 읽는다.
- **H: `0x020e1d08`의 열한 개 술어는 우선순위 순으로 나열된 열한 개의 스케줄링 규칙(오늘 날짜,
  요일 규칙, 휴일 규칙, 무작위 방문객 규칙 ...)이며, 각각 하루에 최대 한 명의 방문객을 준비시킬 수
  있다.** 테이블은 PMF/우선순위로 설명되어 있다
  [H: source account: port/shim/game/spnpc.c; direct ROM-source provenance unresolved]. 실험: 열한 개 각각을 계측하고 시뮬레이션한 7일에 걸쳐 어느 것이
  발동하는지 기록한다.
- **H: 휴일은 그 열한 개 술어 중 하나가 참조하는 날짜 테이블의 행이며, `func_0204fa8c`의 열네 값
  인덱스가 그 테이블의 행 선택자다.** 인덱스는 실제 휴일이 월말에 오는 정확히 그 두 달을 나눈다
  [S: `src/matched/func_0204fa8c.c`; historical account: port/shim/game/seasonidx.c]. 실험: `func_0204fb80` 외에 `func_0204fa8c`의 결과를 소비하는 곳을
  찾아 그 테이블을 읽는다.
- **H: 생일은 주민 레코드에서 읽어 `func_02040c90` 안에서 하루에 한 번 RTC 날짜와 비교된다.** 이
  루틴은 지금까지 발견된 유일한 하루 단위 재기록이다
  [H: source account: port/tools/known_callees.txt; direct ROM-source provenance unresolved]. 실험: RTC를 알려진 주민의 생일로 설정하고 롤오버 전후로
  `0x021e5a2c`의 여덟 레코드를 비교한다.
- **H: `func_02040c90`의 다섯 `MI_CpuCopy8` 블록은 다섯 개의 별도 하위 시스템(날씨, 상점 재고,
  방문객, 무 가격, 우편)에 대해 "어제"를 "그저께"로 옮긴다.** 다섯 개의 복사, 그리고 이전 값이
  필요한 다섯 개의 하위 시스템이다
  [H: source account: port/tools/known_callees.txt; direct ROM-source provenance unresolved]. 실험: 각 복사의 원본과 대상을 명명하고 세이브 레이아웃과
  대조한다.
- **H: 세 번째 게이트 항인 `func_02084ad0`은 "특수 NPC가 이미 존재한다"이며, 그래서 0이어야 한다.**
  인수 없이 호출되며 게이트가 통과하려면 결과가 0이어야 한다 [S: `src/matched/func_02084ad0.c`; historical account: port/shim/game/spnpc.c]. 실험:
  `func_02084ad0`을 읽고 방문객의 채널이 열려 있는 동안 기록한다.

## 관련 문서

- `weather-and-seasons.md` -- 같은 날짜가 만들어내는 계절
- `player.md` -- 이벤트 비트필드 상세
- `villagers.md` -- 이사는 RTC 전진으로 구동된다
- `dialogue.md` -- 준비된 방문객이 하는 말
