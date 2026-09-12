# 부팅과 진입점
<!-- source: wiki/engine/boot-and-entry.md -->

**요약.** 전원이 켜지면 ARM9는 NitroSDK의 손으로 작성된 스타트업을 실행한 뒤, 세 가지를
고정된 순서로 수행한다: 하드웨어/무선/파일시스템 초기 기동 루틴, C++ 정적
초기화자, 그리고 게임 자체의 `NitroMain`이다. `NitroMain`은 OS 틱, 알람, 스레드를
시작하고, 예외 핸들러를 설치하고, 인터럽트를 활성화한 다음 게임에 제어를 넘기며,
게임은 절대 반환하지 않는다. PC 포트의 인터프리터 경로에서는 이 세 가지 모두가 ROM
자체의 ARM 및 Thumb 바이트로 실행되고, 호스트는 그 아래의 하드웨어만 제공한다. 닌텐도 로고가
영원히 표시되는 부팅을 디버깅하고 있다면, 이 페이지의 시퀀스가 그 증상을 걸어 둘
뼈대가 된다.

## 무슨 일이 일어나는가

### 진입 체인

NDS 헤더의 진입 체인은 `0x02000800`의 `Entry`, 즉 NitroSDK crt0의 손으로 작성된
ARM 스타트업에 도달한다. 이 루틴은 CP15를 설정하고, SVC/IRQ/시스템 스택을 구성하고, OAM과 팔레트 RAM을 지우고
캐시를 플러시한다 [S: `src/matched/Entry.c`; source account: `Entry`, main, `port/platform/nitromain.c` header]. 이 중 어느 것도
디컴파일 가능한 C 본체가 아니다 — 호스트 빌드가 전혀 컴파일할 수 없는 어셈블리 번역 단위 중
하나이다 [H: source account: `port/platform/nitromain.c` header; `port/tools/expected_failed_tus.txt`; direct ROM-source provenance unresolved].

`Entry`는 네 개의 명령어로 끝나며, 이것이 공식적인 부팅 순서이다:
`0x02137124`(`bx lr` no-op) 호출, `func_020b1a74`(하드웨어, 무선, 파일시스템
초기 기동) 호출, `func_02138968`(`__init_cpp`, 정적 초기화자) 호출, 그리고 마지막으로
`0x02000c39`의 리터럴 풀 로드와 그곳으로의 branch-exchange이다
[S: `src/matched/Entry.c`, `src/matched/func_020b1a74.c`, `src/matched/func_02138968.c`; source account: `Entry`, main, quoted in `port/platform/win32.c:2340-2348`].

이 순서는 우연이 아니라 필수적이다: 포트의 첫 번째 구성은 초기 기동 전에
`__init_cpp`를 실행했고, 그러자 생성자들은 힙, VRAM 뱅크, 파일시스템이 아직 존재하지 않는
머신 위에서 첫 오브젝트들을 만들었다 [H: host-source account from `port/platform/win32.c:2346-2349`; verify with a retained scripted run and frame using this page's recipe].

### 진짜 진입점에는 자체 심볼이 없다

`0x02000c38`은 `Entry`가 분기하는 0x60바이트 Thumb 루틴이며, 여기서 시작하는 심볼은 없다
[H: source account: `port/platform/nitromain.c` header; direct ROM-source provenance unresolved]. 심볼 테이블은 0xcc바이트 앞에서 시작하는 0x174바이트 Thumb 심볼
`func_02000b6c`를 잘라 두었으므로, 진입 루틴은 0xcc바이트의
읽기 전용 버전 문자열이 앞에 붙은 채로 도착한다 — 정확히 `0x02000b6c + 0xcc = 0x02000c38`이다
[S: `src/matched/Entry.c`; source account: `func_02000b6c`, main, `port/platform/nitromain.c` header]. 이것은 ROM이 아니라
잘못 잘린 경계가 이상해 보이는 원인이 되는 여러 지점 중 첫 번째이다. 주소 아레나에 미치는 결과는
`memory-map.md`를 참고하라.

### `NitroMain`이 하는 일

ROM의 `0x02000c38`에서 읽어 보면, 이 루틴은 NitroSDK의 `NitroMain` 형태이며 다음을
순서대로 호출한다: `OS_InitTick`, `OS_InitAlarm`, `OS_InitThread`, 그 다음 ROM 자체의 핸들러
`func_0206e6c4`와 인수 워드 `0x0220433c`를 넘기는 `OS_SetUserExceptionHandler`
[H: source account: `port/platform/nitromain.c:33-46, 62-66`; direct ROM-source provenance unresolved]. 그런 다음 `REG_IME`(`0x04000208`)를 읽고
1을 쓰고, `OS_EnableInterrupts`를 호출하고, `func_0206e518`을 호출한다
[H: source account: `port/platform/nitromain.c:68-75`; direct ROM-source provenance unresolved]. `REG_IME` 읽기는 값으로서는 죽어 있지만
하드웨어 접근으로서는 살아 있다 — ROM은 로드된 레지스터를 즉시 덮어쓴다 — 그래서 포트는
이를 volatile 읽기로 유지한다 [H: source account: `port/platform/nitromain.c:67-71`; direct ROM-source provenance unresolved].

`0x027ffc20`의 부팅 플래그 뒤에는 두 번째 경로가 있다: 이 값이 1이면 루틴은
`func_0206e464`도 호출하고, `REG_IME`를 다시 건드리고, `func_02116a1c(2)`를 호출한다
[H: source account: `port/platform/nitromain.c:77-82`; direct ROM-source provenance unresolved]. 두 경로 모두 같은 방식으로, `func_020b1b84`
다음 `func_0206e560`으로 끝나며, 루틴은 절대 반환하지 않는다
[H: source account: `port/platform/nitromain.c:84-85`; direct ROM-source provenance unresolved]. `func_0206e560`이 게임 본체가 시작되는 곳이다;
`scenes-and-channels.md`의 모든 내용은 그 아래에서 일어난다.

여기서 설치되는 예외 핸들러는 장식이 아니다. ROM이 치명적 폴트를 맞으면
`func_0206e3f4 -> func_0206e6c4`를 통해 예외의 레지스터 테이블을 `0x0213fde0`에
저장하고, 이어서 `func_020012ec`가 `func_02001324`를 루프한다 — 양쪽 화면이 모두 검은
ROM 자체의 크래시 화면이다 [H: log/source account: `docs/log/cycle40-keyboard-gate-probe.md`,
CARD40..SND40; observed from frame ~830 of an interpreter run; receipt provenance unresolved].

### 초기 기동 루틴과 그 마지막 호출

`func_020b1a74`는 Thumb이며 하드웨어, 무선, 파일시스템 초기 기동을 수행한다
[S: `src/matched/func_020b1a74.c`; source account: `func_020b1a74`, main, `port/interp/interp_boot.c:29`]. 그 마지막 호출은 게임의
메인 힙 분할인 `func_020ea48c`이므로, 그 힙이 존재하기 전까지는 초기 기동 이후의 어떤 것도 실행될 수 없다
[S: `src/matched/func_020b1a74.c`; source account: `func_020ea48c`, autoload_2, `port/shim/boot/heapinit.c` header]. 이 함수는
`OS_GetArenaLo(0)`과 `OS_GetArenaHi(0)`을 읽고, 빼기 전에 하위 끝을 32바이트로
올림하여 크기가 이미 정렬 패딩을 감당하도록 한 뒤, 나머지를
아레나 0에서 할당한다 [S: `src/matched/func_020b1a74.c`; source account: `func_020ea48c`, autoload_2, `port/shim/boot/heapinit.c` header]. 그 블록 안에
무엇을 구축하는지는 `memory-map.md`를 참고하라.

처음부터 끝까지 인터프리트하면 초기 기동은 3,917스텝, 정적 초기화자는 21,402스텝이다
[E: `docs/log/cycle40-keyboard-gate-probe.md` ENTRY40, runs `off-D17`..`off-D20` ; `scratchpad/cycle40/runs/off-D17`, `scratchpad/cycle40/runs/off-D20`].

### PC 포트 인터프리터 경로의 부팅

`ACWW_INTERP=1`이면 포트는 이 중 어느 것도 자체 전사본을 호출하지 않는다: ROM의
`Entry` 순서 — `0x020b1a75`, `0x02138968`, `0x02000c39` — 를 인터프리터를 통해 실행하며,
인터프리터의 훅이 먼저 설치된다 [H: source account: `port/interp/interp_boot.c:28-30, 404-418`; direct ROM-source provenance unresolved]. 네이티브
초기 기동, 네이티브 `__init_cpp`, 네이티브 사운드 부팅은 모두 건너뛰며, 포트는
stdout에 그렇게 밝힌다 [H: source account: `port/platform/win32.c:2355-2405`; direct ROM-source provenance unresolved].

부팅 줄은 레지스트리 크기, 진입점, 스택을
`acww interp: BOOT via interpreter, registry entries=N entry=0x02000c39 stack=0x027e3e00` 형태로 알린다
[H: source account: `port/interp/interp_boot.c:395-401`; direct ROM-source provenance unresolved]. 인터프리트되는 시스템 스택 상단은 `0x027e3e00`이며,
DTCM 상단에 있는 NitroSDK의 IRQ(0x100) 및 SVC(0x40) 스택 아래에 배치된다
[H: source account: `port/interp/interp_boot.c:11-14, 31`; direct ROM-source provenance unresolved].

두 가지 순서 관련 사실은 폴트를 대가로 얻은 것이다. 네이티브 초기 기동을 먼저 실행하면 네이티브
`CARD_Init`이 HOST 진입점을 가진 카드 태스크 스레드를 만들고, 파이버는 훅이 존재하기도 전에
이를 인터프리트하려 했다 [E: `docs/log/cycle40-keyboard-gate-probe.md` ENTRY40,
`off-D16` ; `scratchpad/cycle40/runs/off-D16`]. 그리고 사운드 커맨드 계층은 인터프리트된 초기 기동 이후로 옮겨야 했는데,
`SND_CommandInit`이 ROM 자체의 `PXI_Init`이 설정하는 PXI 비트를 기다리기 때문이다
[E: `docs/log/cycle40-keyboard-gate-probe.md` ENTRY40, `off-D17`..`off-D20` ; `scratchpad/cycle40/runs/off-D17`, `scratchpad/cycle40/runs/off-D20`].

콘솔 자체 상태 중 하나는 ROM 코드도 PXI도 아니다: 사용자 설정의 NVRAM 읽기
(PXI 태그 4)는 `0x02000c98`의 심볼 없는 영역에서 오며, 등록할 이름이 없기 때문에
포트는 주소로 이를 공급한다 [H: source account: `port/tools/interp_registry.py:77-80`;
H: historical measurement account: `docs/log/cycle40-keyboard-gate-probe.md` ENTRY40, `off-D18`, where the read spun forever; direct ROM-source provenance unresolved].

### 부팅 이후: 프레임이란 무엇인가

NDS에는 프레임 루프가 없다 [H: source account: `port/shim/os/vblank.c:11-14`; direct ROM-source provenance unresolved]. 게임의 루프는 `VBlankIntrWait`
(`0x020002c7`, BIOS `IntrWait`를 둘러싼 세 명령어)에서 블록하며 끝나고, 수직 블랭크
인터럽트가 시간을 흐르게 하는 것이다 [S: `src/matched/VBlankIntrWait.c`, `src/matched/IntrWait.c`; source account: `VBlankIntrWait`, main, `port/shim/os/vblank.c` header].
유휴 스레드의 본체 전체는 `while (1) OS_Halt();`이며, `OS_Halt`는 CP15의
인터럽트 대기(wait-for-interrupt)이다 [S: `src/matched/OSi_IdleThreadProc.c`, `src/matched/OS_Halt.c`, `src/matched/VBlankIntrWait.c`, `src/matched/IntrWait.c`; source account: `OSi_IdleThreadProc` / `OS_Halt`, itcm, `port/shim/os/halt.c` header].

인터프리터 경로에서는 세 번째 것이 프레임을 끝낼 수 있으며, 마을 시퀀스 동안 실제로
그렇게 하는 것이 바로 이것이다: ROM의 프레임 동기화 `func_0200149c`는 `VCOUNT`를 읽으며 스핀하므로,
포트의 I/O 로드 훅은 읽기마다 합성 스캔라인을 하나 진행시키고 카운터가 0번 라인으로
되감길 때 프레임 경계를 호출한다 [H: source account: `port/interp/interp_boot.c:239-254`;
H: historical measurement account: `docs/log/cycle40-keyboard-gate-probe.md` CARD40..SND40, `off-D36`; direct ROM-source provenance unresolved]. 이 규칙이 없으면
상태 머신 경로의 어떤 것도 프레임 경계에 전혀 도달하지 못했다
[H: log/source account: same run; receipt provenance unresolved]. `threads-and-interrupts.md`를 참고하라.

### 부팅이 어디까지 진행되는가

스크립트화된 마을 레시피의 인터프리트 실행은 프레임 4,500까지 이름 키보드가 있는 택시
내부에, 37,500에 마을 회관 앞의 마을에, 40,500까지 마을 회관
내부에 도달하며, 폴트나 인터프리터 정지 없이 48,000프레임을 실행한다
[E: `scratchpad/cycle40/runs/tap-D56`, 31 shots; `docs/log/cycle40-keyboard-gate-probe.md` TOWN40].
같은 레시피를 파이프라인의 영수증(receipt) 경로로 실행하면 801초에 48,000프레임으로 끝났고
자식 종료 코드는 100이었다 [E: `scratchpad/cycle40/runs/town-R1`; RECEIPT41]. 더 긴 실행은
상태 정지 없이 90,000프레임에 도달했다 [E: `scratchpad/cycle40/runs/tap-D59`; LONG41].

프레임 6,000부터 24,000까지 포트와 DeSmuME 레퍼런스는 단계별로 같은 화면에 있으며,
아래 화면 정규화 상호상관은 0.9997에서 1.0000이다
[O: `scratchpad/oracle/tap-fullpad`, compared against `tap-D56`; ORACLE41]. 둘은
25,500에서 갈라지는데, 포트의 예약된 두 번의 탭은 마을 이름을 확정하고 원본의 동일한
탭은 그렇지 않다 [E+O: `scratchpad/cycle40/runs/tap-D59`; LONG41 comparison]. **이 분기는 해결되었다(ORACLE42)**: 24,600의 탭은
KEYS3 A 누름 프레임(2400 + 37 x 600)에 떨어지고, 원본의 스타일러스 샘플은 포트보다
1~2프레임 늦게 게임에 도달하므로, 둘은 누름과 탭의 순서를
다르게 매긴다; 24,700으로 옮기면 양쪽 모두 확정하고 일치하며, 24,000..27,000의 11프레임이 평균 ncc
0.9955이다 [H: source account: `docs/log/cycle40-keyboard-gate-probe.md` ORACLE42; H: historical measurement account: `tap-D62`;
O: `scratchpad/oracle/tap-24700`; direct ROM-source provenance unresolved]. TOUCH42 이후 포트는 그 순서를 피하는 대신 재현하며,
24,600 레시피는 원본과 같이 동작한다
[E: `scratchpad/cycle40/runs/tap-T42b`] [O: `scratchpad/oracle/tap-window`;
`../experiments/touch-latency.md`].

## 어디에 있는가

| 함수 또는 심볼 | 모듈 | 역할 | 등급 / 출처 |
|---|---|---|---|
| `Entry` (`0x02000800`) | main | crt0: CP15, 스택, OAM/팔레트 클리어, 캐시 플러시 | [S: `src/matched/Entry.c`; source account: `port/platform/nitromain.c` header] |
| `func_020b1a74` (Thumb) | main | 하드웨어, 무선, 파일시스템 초기 기동 | [S: `src/matched/func_020b1a74.c`; source account: `port/interp/interp_boot.c:29`] |
| `func_020ea48c` | autoload_2 | 초기 기동의 마지막 호출: 아레나 0에서 게임 힙을 분할 | [S: `config/adm-kr/arm9/autoload_2/symbols.txt` (`func_020ea48c` at 0x020ea48c); source account: `port/shim/boot/heapinit.c` header] |
| `func_02138968` (ARM) | main | `__init_cpp`, C++ 정적 초기화자 | [S: `src/matched/func_02138968.c`; source account: `port/interp/interp_boot.c:30`] |
| `0x02000c38` (Thumb, 0x60 bytes) | main | 진짜 `NitroMain`; 여기서 시작하는 심볼 없음 | [H: source account: `port/platform/nitromain.c` header; direct ROM-source provenance unresolved] |
| `OS_InitTick` / `OS_InitAlarm` / `OS_InitThread` | autoload_2 | OS 서비스, 이 순서대로 | [S: `src/matched/OS_InitTick.c`, `src/matched/OS_InitAlarm.c`, `src/matched/OS_InitThread.c`; source account: `port/platform/nitromain.c:33-35`] |
| `OS_SetUserExceptionHandler` (`0x0211628c`) | autoload_2 | `func_0206e6c4`를 인수 `0x0220433c`와 함께 설치 | [S: `src/matched/OS_SetUserExceptionHandler.c`, `src/matched/func_0206e6c4.c`; source account: `port/platform/nitromain.c:36, 46`] |
| `OS_EnableInterrupts` (`0x01ffa314`) | itcm | 인터럽트 켜기 | [S: `src/matched/OS_EnableInterrupts.c`; source account: `port/platform/nitromain.c:37`] |
| `func_0206e518`, `func_020b1b84`, `func_0206e560` | main | 게임으로의 인계; 절대 반환하지 않음 | [S: `src/matched/func_0206e518.c`, `src/matched/func_020b1b84.c`, `src/matched/func_0206e560.c`; source account: `port/platform/nitromain.c:75, 84-85`] |
| `func_0206e6c4` / `func_0206e3f4` | main | 치명적 경로: 레지스터 테이블 저장 후 크래시 화면 | [H: log/source account: cycle40 log, CARD40..SND40; receipt provenance unresolved] |
| `VBlankIntrWait` (`0x020002c7`) | main | 게임이 블록하는 프레임 경계 | [S: `src/matched/VBlankIntrWait.c`; source account: `port/shim/os/vblank.c` header] |
| `OS_Halt` | itcm | 유휴 스레드의 본체 | [S: `src/matched/OS_Halt.c`; source account: `port/shim/os/halt.c` header] |
| `func_0200149c` | main | 프레임 동기화; `VCOUNT`에서 스핀 | [E: cycle40 log, CARD40..SND40 `off-D36` ; `scratchpad/cycle40/runs/off-D36`] |

## 읽고 쓰는 데이터

| 주소 | 의미 | 쓰는 쪽 | 읽는 쪽 |
|---|---|---|---|
| `0x04000208` (`REG_IME`) | 인터럽트 마스터 활성화; 플래그 경로에서 두 번 1로 설정됨 | `NitroMain` | 인터럽트 컨트롤러 [H: source account: `port/platform/nitromain.c:49, 68-81`; direct ROM-source provenance unresolved] |
| `0x027ffc20` | 부팅 플래그; 1이면 두 번째 부팅 경로 선택 | `NitroMain` 이전에 설정됨 | `NitroMain` [H: source account: `port/platform/nitromain.c:50, 77`; direct ROM-source provenance unresolved] |
| `0x0220433c` | 사용자 예외 핸들러의 인수 워드 | ROM 리터럴 풀 | `OS_SetUserExceptionHandler` [S: `src/matched/OS_SetUserExceptionHandler.c`; source account: `port/platform/nitromain.c:48`] |
| `0x0213fde0` | 치명적 폴트 시의 예외 레지스터 테이블 | `func_0206e6c4` | 크래시 화면, 그리고 `ACWW_INTERP_PEEK` [H: log/source account: cycle40 log, CARD40..SND40; receipt provenance unresolved] |
| `0x027fff9c` | crt0가 쓰는 인터럽트 벡터 슬롯 | `Entry` | 벡터 [S: `src/matched/Entry.c`; source account: `port/platform/win32.c:78-83`] |
| `0x027e3e00` | 인터프리트되는 시스템 스택 상단(포트 전용) | `interp_boot.c` | 인터프리터 [H: source account: `port/interp/interp_boot.c:31`; direct ROM-source provenance unresolved] |

## 확인 방법

대조 레시피는 OFF 조건이다 — 터치를 비활성화한 커스텀 START9000 키 — 다른 어떤 조건보다
먼저 실행하고 보관된 네이티브 실행과 프레임 단위로 비교한다:

    sh scratchpad/cycle40/iterate.sh <name>

이 스크립트는 재링크하고, `ACWW_INTERP=1 ACWW_TOUCH_ENABLE=0 ACWW_STOP_FRAME=9000
ACWW_SHOT_AFTER=4500`으로 실행한 뒤, 31개 BMP 전부를 SHA256으로 비교한다; 31개 중 31개 일치가 통과이다
[H: source account: `docs/kb/hybrid/recipes.md` section 2; direct ROM-source provenance unresolved]. 부팅 자체는 스크린샷 없이도 로그만으로
읽을 수 있다: `interpreter path:` 줄을 찾고, 그 다음
`acww interp: BOOT via interpreter, registry entries=...` 줄을, 그 다음 `STOP` 줄이 없는지를
확인한다 [H: host/prose inference from `port/interp/interp_boot.c:395-401, 419-428`; verify against the ROM function or symbol table and this page's recipe].

타이틀을 지나가려면, `docs/kb/hybrid/recipes.md` 섹션 3의 두 번 탭 마을 레시피가
마을 회관에 도달하는 레시피이다; 이 레시피는 콘솔 시계를 `20050615` / `100000`에 고정하여
오라클이 같은 순간을 고정할 수 있게 한다 [H: source account: `docs/kb/hybrid/recipes.md` sections 3 and 6; direct ROM-source provenance unresolved].

## 가설

- 진입 루틴 앞에 붙은 0xcc바이트의 버전 문자열은 코드가 아니라 `OSi_ReferSymbol`
  데이터이다 [H: settled by resolving every literal-pool reference into
  `0x02000b6c`..`0x02000c37` and showing none is a branch target].
- `0x027ffc20 == 1` 뒤의 두 번째 부팅 경로는 소매 카트리지의 콜드 부팅에서는
  절대 선택되지 않는다 [H: settled by an oracle run reading the flag at the first frame, and by an
  interpreted run reporting whether `func_0206e464` is ever entered].
- 인터프리터의 부팅 속도(마을 레시피에서 페이싱 없이 ~59프레임/초)는 페이싱된
  라이브 플레이에 충분하다 [H: settled by a paced live run with keyboard and mouse; no such run exists
  — `docs/kb/hybrid/open-questions.md`].
- 도달 가능한 부팅 경로의 어떤 것도 `LDM/STM ^` 형태, 게임 코드에서의 `SWI`, 또는
  구조체 값 반환을 사용하지 않는다 [H: 90,000 frames without a status stop is evidence for, not proof;
  settled by an interpreter that names those shapes when it meets them — `docs/HYBRID-PLAN.md`
  phases H1/H2].

## 관련 문서

- `memory-map.md` — 초기 기동의 마지막 호출이 게임 힙을 분할해 내는 아레나
- `threads-and-interrupts.md` — `OS_InitThread`가 구축하는 것, 그리고 VBlank가 하는 일
- `overlays.md` — 초기 기동이 시작하는 파일시스템, 그리고 첫 오버레이 로드
- `scenes-and-channels.md` — `func_0206e560`이 제어를 넘기는 대상
- `interpreter-path.md` — 거부 목록, 그리고 네이티브 본체가 핫 패스를 얻는 방법
- `../experiments/savestate-resume.md` — 이 경로의 실행을 스냅샷하고 정확히 재개하기
