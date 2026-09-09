# 스레드와 인터럽트
<!-- source: wiki/engine/threads-and-interrupts.md -->

**요약.** ACWW는 NitroSDK의 협력적(cooperative) 스레드 모델을 사용한다: 소수의 `OSThread`가
각각 0x64바이트짜리 저장된 ARM 레지스터 파일을 가지며, 코드가 스케줄러를 호출하는 곳에서만 전환된다.
인터럽트(interrupt) 쪽은 DTCM 맨 아래에 있는 핸들러 슬롯 테이블이며, 게임은
그중 거의 전적으로 하나 — 수직 블랭크, 슬롯 0 — 에 의존한다. 프레임이란 VBlank가 뜻하는 것이다:
게임은 `VBlankIntrWait`에서 블록하고, 핸들러가 깨우며, 그 사이에 유휴 스레드는
정지(halt)한다. ARM7은 번호가 매겨진 태그를 가진 FIFO를 통해 도달하며, 그 응답도
인터럽트로 도착한다.

## 무슨 일이 일어나는가

### 컨텍스트 레코드

`OSContext`는 0x64바이트다: 오프셋 0에 CPSR, 0x04부터 r0에서 r12까지, 0x38에 스택 포인터,
0x3c에 링크 레지스터, 0x40에 `pc_plus4`, 0x44에 SVC 스택 포인터, 그리고 0x48부터 0x63까지
코프로세서 컨텍스트 [S: `OSContext`, autoload_2,
`port/shim/os/thread.c:80-107`, recovered verbatim from
`src/matched/OSi_ExitThread_ArgSpecified.c`]. 크기 0x64는
`src/matched/OS_InitThread.c`로 독립적으로 확정되며, 오프셋은 `src/matched/OS_InitContext.c`와
두 손으로 작성된 어셈블리 본체와 일치한다 [S: `port/shim/os/thread.c:84-92`].

코프로세서 컨텍스트는 ARM9의 나눗셈기와 제곱근기 상태다: 분자, 분모,
제곱근 피연산자, 그리고 두 모드 워드로, `CP_SaveContext`가 저장한다
[S: `CPContext`, `port/shim/os/thread.c:93-99`; `port/shim/os/thread.c:57-58`].

`pc_plus4`는 의도적으로 진입점 더하기 4를 담고 있어서, `ldm ... ^` 복원이
한 명령어 앞에 착지하도록 한다 [S: `port/shim/os/thread.c:176-179`]. `r[0]`은 실제로 의미를 지니며
읽힌다: 스레드 프로시저의 인자를 담고 있으며, `OS_CreateThread`가 `OS_InitContext`를 통해
설정하고 `OSi_ExitThread_ArgSpecified`가 덮어쓴다
[S: `port/shim/os/thread.c:59-63`].

### 저장과 복원: 레지스터 파일 위의 setjmp/longjmp

`OS_SaveContext`는 컨텍스트 자신의 r0 슬롯에 1을, `pc_plus4`에 pc+8을 저장한 다음,
0을 반환하며 빠져나간다. `OS_LoadContext`는 r0부터 r14까지의 사용자 모드 다중 로드로 파일을
복원하고 `subs pc, lr, #4` — 저장 다음 명령어 — 에 착지한다. 따라서 저장하는 쪽은
0을 보고 재개하는 쪽은 1을 본다: 고전적인 setjmp 의미론이다
[S: `OS_SaveContext` / `OS_LoadContext`, autoload_2, from
`src/matched/OS_SaveContext.c` and `src/matched/OS_LoadContext.c` via
`port/shim/os/thread.c:11-16`]. 둘 다 손으로 작성된 ARM 어셈블리 본체다
[S: `port/shim/os/thread.c:5-7`].

그 위의 스케줄러는 협력적이다: `OS_RescheduleThread`는 코드가 호출하는 곳에서만
실행되며, 스레드는 블록할 때까지 실행된다 [S: `port/shim/os/thread.c:17-19`]. 그 형태는 저장,
저장이 재개를 보고하면 조기 반환, 그다음 전환 콜백,
`OS_SetCurrentThread`, 그리고 다음 스레드에 대한 `OS_LoadContext`이다
[S: `src/matched/OS_RescheduleThread.c` via `port/shim/os/thread.c:31-40`].
`OS_RescheduleThread`와 `OSi_ExitThread_ArgSpecified`는 `src/matched/`에서
두 루틴 중 어느 하나라도 이름을 언급하는 유일한 두 함수다 [S: `port/shim/os/thread.c:41-44`].

`OS_CreateThread`는 NDS 메모리에 두 개의 스택 오버플로 체크넘(checknum)을 쓰며,
`OS_GetCurrentThread()->stackTop` / `stackBottom`이 이를 가리킨다
[S: `port/shim/os/thread.c:51-55`]. `OSThread` 프로시저는 반환하지 않는다: 계약은
`OS_ExitThread`로 끝나며, 이것이 재스케줄하고 결코 돌아오지 않는다는 것이다
[S: `port/shim/os/thread.c:222-225`].

### 존재하는 스레드들

런처 스레드는 평범한 스레드로 도착하며 `OS_InitThread`로부터 컨텍스트를 받지 않는데,
이 함수는 우선순위와 스택 경계만 채운다; 컨텍스트는 첫
`OS_SaveContext`에서 얻는다 [S: `port/shim/os/thread.c:231-236`]. 유휴(IDLE) 스레드의 본체 전체는
`while (1) OS_Halt();`이고, `OS_Halt`는 CP15 인터럽트 대기(wait-for-interrupt)를 둘러싼
ARM 명령어 세 개다 [S: `OSi_IdleThreadProc` / `OS_Halt`, itcm,
`port/shim/os/halt.c:6-8`]. 거기에 도달한다는 것은 스케줄러가 실행할 수 있는 스레드가 없다고
올바르게 결론지었다는 뜻이며, 하드웨어에서는 완전히 정상적인 상태다
[S: `port/shim/os/halt.c:7-10`]. 그 스택은 작다 — 0x80바이트로 측정되었다
[E: `docs/log/cycle40-keyboard-gate-probe.md` CARD40..SND40, first fault].

`CARD_Init`은 카드 태스크 스레드를 만드는데, 그 프로시저 `CARDi_TaskThread`는 카드 인터럽트를
기다리며 큐에서 잠든다 [S: `port/shim/os/halt.c:25-29`; E: cycle40 log ENTRY40
`off-D16`, where the port created that thread with a host entry]. 사운드 쪽도 하나를
만드는데, `CARD_GetThreadPriority() - 1`에서다 [S: `NNS_SndCaptureCreateThread`,
`port/shim/os/sndstart.c:145`]. 이들 모두 위에 메인(MAIN) 스레드, 즉
`VBlankIntrWait`에서 블록하는 스레드가 있다 [S: `port/shim/os/vblank.c:58-64`].

### 인터럽트 테이블

`OS_IRQTable`은 DTCM의 맨 아래인 `0x027e0000`에 있고, 슬롯 0이 VBlank다 —
`OS_SetIrqFunction`은 비트 0을 곧바로 그 슬롯에 쓴다
[S: `port/shim/os/vblank.c:65-68, 80`]. 하드웨어에서 VBlank는 `0x027ffe20`을 거쳐
등록된 핸들러로 벡터링되며, 핸들러는 인터럽트를 확인(acknowledge)하고 VBlank 큐에 대해
`OS_WakeupThread`를 호출한다; 이것이 `VBlankIntrWait`에서 블록된 스레드가 다시 실행 가능해지는 방법이다
[S: `port/shim/os/halt.c:17-21`]. 확인은 핸들러가 아니라 `OS_IrqHandler`의 일이다
[S: `port/shim/os/vblank.c:68-70`]. `REG_IF`는 `0x04000214`에 있다
[S: `port/shim/os/vblank.c:81`]. DMA 완료는 `OS_IRQTable[8 + ch]`를 통해 전달된다
[S: `docs/kb/hybrid/hardware-services.md` section 2].

VBlank 안에서 ROM은 `0x021f6ca0`의 태스크 리스트도 실행하는데, `func_020b98ec`가 순회하며
각 태스크를 vtable 슬롯 0을 통해 디스패치한다 [S: `port/shim/gfx/vbtask.c` header].
`display-objects.md`를 참고하라.

### ARM7과 FIFO

ARM9는 PXI FIFO를 통해 ARM7과 대화하며, 번호가 매겨진 태그로 디스패치한다
[S: `docs/kb/hybrid/hardware-services.md` section 1]. 수신
콜백은 태그로 인덱싱되는 `0x027e0394`의 테이블에 있으며,
`PXI_SetFifoRecvCallback`이 채운다 [S: `docs/kb/hybrid/hardware-services.md` section 1]. 살아 있는 태그:
4는 본체 사용자 설정의 NVRAM 읽기, 5는 RTC, 6은 터치 패널, 7은 사운드
명령, 8은 전원 관리, 10은 무선, 11과 14는 카드
[S: `docs/kb/hybrid/hardware-services.md` sections 1 and "Other tags"].

그중 둘은 타이밍이 프로토콜의 일부이기 때문에 자세히 알아 둘 가치가 있다. 터치
패널에서 SDK의 요청 함수들은 먼저 보내고 보내기가 반환된 후에 `command_flg`를 설정하므로,
보내는 도중에 도착한 응답은 아무것도 지우지 못하고 `TP_WaitBusy`는
영원히 스핀한다 [S: `docs/kb/hybrid/hardware-services.md` section 1; E: cycle40 log ENTRY40 `off-D8`,
hung at 15 s]. 카드에서 `CARDi_Request`는 `CARD_STAT_REQ`를 설정하고, 태그 11을 보내고 잠든다;
게시(post) 뒤에 오는 폴링은 하드웨어에서 그러하듯 BUSY를 보아야 하며, 그렇지 않으면 락이 해제되고
읽기가 다시 시작된다 [S: `docs/kb/hybrid/hardware-services.md` section 1; E: cycle40 log
CARD40, where a synchronous answer produced the Nintendo-logo wait, `func_02050974` once per
loop, BUSY forever]. `CARDi_OnFifoRecv`는 REQ를 지우고 카드 스레드를 깨우기 전에 응답의 오류
워드를 검사한다 [S: `docs/kb/hybrid/hardware-services.md` section 1].

### 예외

`NitroMain`은 ROM 자체의 사용자 예외 핸들러 `func_0206e6c4`를 인자
워드 `0x0220433c`와 함께 설치한다 [S: `port/platform/nitromain.c:36, 46, 66`]. 치명적 오류 시 ROM은
예외의 레지스터 테이블을 `0x0213fde0`에 저장하고 `func_020012ec`가
`func_02001324`를 반복한다 — 크래시 화면, 두 화면 모두 검정
[E: `docs/log/cycle40-keyboard-gate-probe.md` CARD40..SND40].

### PC 포트가 이 모든 것을 대신하는 방법

스레드는 Windows 파이버(fiber)가 되며, 이 대응은 근사가 아니라 구조적이다: 파이버는
`SwitchToFiber`가 호출되는 곳에서만 전환되는데, 이는 정확히 협력적 스케줄러의
계약이다 [S: `port/shim/os/thread.c:17-21`]. 유일하게 문자 그대로가 아닌 지점은
`OS_SaveContext`가 두 번 반환할 수 없다는 것이어서, 항상 0을 반환하고 재개는 한 호출
뒤에, `OS_LoadContext` 안의 `SwitchToFiber`가 반환할 때 도착한다; 이것이 동치인 이유는 오직
두 표현 모두 그 사이에 아무것도 실행하지 않은 채 `OS_RescheduleThread`에서 반환함으로써
재개하기 때문이다 [S: `port/shim/os/thread.c:24-40`]. 파이버는 자체 스택을 가져오므로, NDS
스레드 스택은 사용되지 않는다 — 이는 무해한데, 오버플로 체크넘이 그러면 결코
덮어써지지 않아 모든 스택 검사가 계속 통과하기 때문이다 [S: `port/shim/os/thread.c:48-55`]. 포트는
살아 있는 컨텍스트를 64개로 제한하며, 초과하면 추측하는 대신 이름을 대고 멈춘다
[S: `port/shim/os/thread.c:118, 162-164`].

호스트에서는 IRQ 0만이 소스를 가진다: 타이머, DMA 완료, 카드 인터럽트는 소스가 없으므로,
그중 하나를 기다리는 게임은 영원히 기다리게 된다
[S: `port/shim/os/vblank.c:76-79`]. 카드는 대신 작업을 한 프레임 뒤, 다음 VBlank에서
수행함으로써 응답되며, 이것이 BUSY 다음 DONE 시퀀스를 재현한다
[S: `docs/kb/hybrid/hardware-services.md` section 1]. `acww_vblank`는 먼저 ARM7의 큐에 쌓인
PXI 응답을 비운 다음 `OS_IRQTable[0]`을 디스패치한다
[S: `port/shim/os/vblank.c:99-103, 172-180`].

인터프리터 경로에서는 핸들러 슬롯이 호스트 주소를 담고 있을 수 있다 — ROM 자체의 게임 초기화가
하나를 설치한다 — 그래서 포트는 이를 NDS 함수로 되돌려 매핑하고 그것을 인터프리터로 실행한다; 그것이
없으면 네이티브 VBlank 스텝과 ROM의 디스플레이 순회가 서로 어긋나 아무것도
업데이트 리스트에 합류하지 않았다 [S: `port/shim/os/vblank.c:152-170`; E: cycle40 log REG40c `off-D4`].

두 번의 스택 오류가 인터럽트 핸들러는 스레드의 스택을 공유할 수 없다는 규칙을 낳았다.
VBlank 핸들러를 메인 스레드의 살아 있는 인터프리터 프레임 바로 아래에 두자 핸들러가
메인 스레드를 깨웠고, 메인 스레드가 그 메모리를 통해 프레임 하나를 통째로 실행했으며, 핸들러의 반환은
객체 안에 착지했다 [E: cycle40 log REG40c, `off-D5`/`off-D6`]. 그리고 유휴 스레드의
0x80바이트 스택에서 실행된 PXI 응답 콜백은 깨우기의 재스케줄 중에 그 바닥을 뚫고 런처 스레드
자체의 `OSThread` 구조체 안으로 푸시했다 [E: cycle40 log CARD40..SND40,
`off-D27`]. 인터럽트 컨텍스트 호출은 이제 전용 16 KB 스택에서 실행된다
[S: `docs/kb/hybrid/runtime.md` section 4]. 규칙을 그대로 옮기면: 콜백 썽크(thunk)는 호출자가
정지된 채로 있는 동안에만 호출자의 스택을 공유할 수 있다; 인터럽트 핸들러는 그것을 가정할 수 없다
[S: `port/interp/interp.h:82-90`].

인터프리터 경로에서 프레임이 끝나는 세 번째 방법이 있으며, 마을 시퀀스 동안에는 이것이
발동하는 쪽이다: ROM의 프레임 동기화 `func_0200149c`가 `VCOUNT`를 읽으며 스핀하므로, 포트는
읽기마다 합성 스캔라인을 하나씩 진행시키고 — 프레임당 263줄, 192줄부터 262줄까지 VBlank 설정 —
카운터가 0줄로 되감길 때 프레임 경계를 호출하는데, 이는 유휴 스레드의
`OS_Halt`가 했을 것과 정확히 같다 [S: `docs/kb/hybrid/hardware-services.md` section 4; E: cycle40 log
CARD40..SND40 `off-D36`].

## 어디에 있는가

| 함수 또는 심볼 | 모듈 | 역할 | 등급 / 출처 |
|---|---|---|---|
| `OS_InitThread` | autoload_2 | 스레드 리스트를 만든다; 컨텍스트 크기를 0x64로 확정 | [S: `port/shim/os/thread.c:88-92, 231-236`] |
| `OS_SaveContext` / `OS_LoadContext` | itcm | ARM 레지스터 파일 위의 setjmp/longjmp (어셈블리) | [S: `port/shim/os/thread.c:5-16`] |
| `OS_RescheduleThread` | autoload_2 | 협력적 전환 | [S: `port/shim/os/thread.c:31-40`] |
| `OSi_ExitThread_ArgSpecified` | autoload_2 | 스레드 종료; 컨텍스트의 r0을 덮어쓴다 | [S: `port/shim/os/thread.c:41-44, 59-63`] |
| `OS_CreateThread` / `OS_InitContext` | autoload_2 | 스레드를 만든다; 컨텍스트와 체크넘을 채운다 | [S: `port/shim/os/thread.c:51-63`] |
| `OSi_IdleThreadProc` / `OS_Halt` | itcm | 유휴 루프와 CP15 인터럽트 대기 | [S: `port/shim/os/halt.c:6-8`] |
| `CARDi_TaskThread` | autoload_2 | 카드 태스크; 큐에서 잠든다 | [S: `port/shim/os/halt.c:25-29`] |
| `NNS_SndCaptureCreateThread` | autoload_2 | 사운드 스레드, 카드 우선순위 빼기 1 | [S: `port/shim/os/sndstart.c:145`] |
| `VBlankIntrWait` (`0x020002c7`) | main | BIOS `IntrWait` 래퍼; 게임의 프레임 블록 | [S: `port/shim/os/vblank.c:1-10`] |
| `OS_SetIrqFunction` | itcm | VBlank 비트에 대해 슬롯 0을 쓴다 | [S: `port/shim/os/vblank.c:65-68`] |
| `OS_IrqHandler` | itcm | 핸들러 전후로 인터럽트를 확인한다 | [S: `port/shim/os/vblank.c:68-70`] |
| `OS_WakeupThread` | autoload_2 | 게임의 VBlank 핸들러가 호출하는 것 | [S: `port/shim/os/halt.c:18-20`] |
| `PXI_SetFifoRecvCallback` | autoload_2 | 태그별 수신 콜백 테이블을 채운다 | [S: `docs/kb/hybrid/hardware-services.md` section 1] |
| `CARDi_Request` / `CARDi_OnFifoRecv` | autoload_2 | 카드 요청을 게시하고 그 응답을 받는다 | [S: `docs/kb/hybrid/hardware-services.md` section 1] |
| `TP_WaitBusy` | autoload_2 | 터치 명령 플래그에서 스핀한다 | [S: `docs/kb/hybrid/hardware-services.md` section 1] |
| `func_0206e6c4` | main | `NitroMain`이 설치하는 사용자 예외 핸들러 | [S: `port/platform/nitromain.c:36, 46`] |
| `func_0200149c` | main | 프레임 동기화; `VCOUNT`에서 스핀한다 | [E: cycle40 log CARD40..SND40 `off-D36`] |
| `func_020b98ec` | main | VBlank 태스크 리스트 순회 | [S: `port/shim/gfx/vbtask.c` header] |

## 읽고 쓰는 데이터

| 주소 또는 필드 | 의미 | 쓰는 쪽 | 읽는 쪽 |
|---|---|---|---|
| `0x027e0000` | `OS_IRQTable[0]`, VBlank 핸들러 슬롯 | `OS_SetIrqFunction` | 벡터, 그리고 포트의 `acww_vblank` [S: `port/shim/os/vblank.c:80, 99-101`] |
| `OS_IRQTable[8 + ch]` | DMA 채널 완료 핸들러 | `OS_SetIrqFunction` | DMA 완료 경로 [S: `docs/kb/hybrid/hardware-services.md` section 2] |
| `0x027ffe20` | 하드웨어 VBlank 벡터 | crt0 | CPU [S: `port/shim/os/halt.c:17-19`] |
| `0x027e0394 + tag*4` | FIFO 태그별 PXI 수신 콜백 | `PXI_SetFifoRecvCallback` | PXI 전달 [S: `docs/kb/hybrid/hardware-services.md` section 1] |
| `0x04000214` (`REG_IF`) | 인터럽트 요청 플래그 | 컨트롤러; 포트는 호출 전후로 비트를 설정한다 | 이를 읽는 핸들러 [S: `port/shim/os/vblank.c:78-81`] |
| `0x04000208` (`REG_IME`) | 인터럽트 마스터 활성화 | `NitroMain` | 컨트롤러 [S: `port/platform/nitromain.c:49`] |
| `OSContext +0x00 / +0x04 / +0x38 / +0x3c / +0x40 / +0x44 / +0x48` | cpsr, r0-r12, sp, lr, pc+4, sp_svc, 코프로세서 상태 | `OS_SaveContext`, `OS_InitContext` | `OS_LoadContext` [S: `port/shim/os/thread.c:100-107`] |
| `OSThread stackTop` / `stackBottom` | 체크넘 경계 | `OS_CreateThread` | 모든 스택 검사 [S: `port/shim/os/thread.c:51-55`] |
| `0x0213fde0` | 치명적 오류 시의 예외 레지스터 테이블 | `func_0206e6c4`가 `func_0206e3f4`를 통해 | 크래시 화면 [E: cycle40 log CARD40..SND40] |
| `0x021f6ca0` | VBlank 태스크 리스트 헤드 | 태스크 등록 | `func_020b98ec` [S: `port/shim/gfx/vbtask.c:22-25`] |

## 확인 방법

`docs/kb/hybrid/recipes.md`의 아무 레시피나 실행하고 포트 자체의 인터럽트 계측 줄을 읽는다:
`acww vblank: frame N OS_IRQTable[0] = <word>`는 첫 프레임들과 변경이 있을 때마다 슬롯을
출력하며, 이는 "핸들러가 등록되지 않았다"와 "슬롯이 짓밟혔다"를 구분해 준다
[S: `port/shim/os/vblank.c:104-127, 175-186`]; 그리고
`acww vblank: handler runs interpreted, NDS <addr>`는 슬롯의 호스트 워드가 ROM 함수로
되돌려 매핑되었음을 말해 준다 [S: `port/shim/os/vblank.c:158-168`]. 응답되지 않은 ARM7 태그는
`acww pxi: tag N word W accepted and dropped (no ARM7)` 형식으로 한 번 스스로 이름을 대므로, 이후의 대기를
아무도 응답하지 않은 태그로 추적할 수 있다 [S: `docs/kb/hybrid/hardware-services.md` section 1].

게임이 진행되지 않는 동안 돌아가는 프레임 루프는 별개의 실패이며, 스레드 리스트를 읽기 전까지는
밖에서 보면 똑같아 보인다: 진단 서명은 스레드 0이
큐에서 대기하고, 유휴 스레드가 `OS_Halt`를 통해 스핀하며, 디스플레이 레지스터가
한 프레임에서 다음 프레임으로 바뀌지 않는 것이다 [E: `port/shim/os/vblank.c:58-64`].

## 가설

- 게임은 타이머 인터럽트를 결코 기다리지 않으며, 그래서 포트의 단일 인터럽트 소스가
  마을까지 충분하다 [H: 90,000 frames without a stall is evidence for
  (`scratchpad/cycle40/runs/tap-D59`, LONG41); settled by an instrument that names any
  `OS_SetIrqFunction` call for a slot other than 0, 8+ch and the card].
- 카드 우선순위 빼기 1로 만들어진 사운드 스레드는 결코 메인 스레드를 블록하지 않으므로,
  침묵하는 ARM7은 무기한 안전하다 [H: the ROM's sound stack runs against a consumer that
  never reports a real player state, so a sequence whose progression the game WAITS on would
  stall; settled by an oracle comparison over a scene with music-driven timing —
  `docs/kb/hybrid/hardware-services.md` section 7].
- 실제 플레이에서 살아 있는 `OSThread` 컨텍스트의 최대 수는 64보다 훨씬 적다
  [H: settled by logging the port's fiber slot high-water mark over the town recipe;
  exceeding it stops by name rather than silently — `port/shim/os/thread.c:162-164`].
- 어떤 호출자도 `OS_SaveContext`와 `OS_LoadContext` 사이에서 실제 작업을 하지 않으며,
  이것이 파이버 대응을 정확하게 만드는 것이다 [H: true of the two callers in `src/matched/`; settled
  for the rest by disassembling every caller of either routine across all modules —
  `port/shim/os/thread.c:41-44`].

## 관련 문서

- `boot-and-entry.md` — `OS_InitThread`, `OS_EnableInterrupts`, 그리고 프레임이란 무엇인가
- `memory-map.md` — 인터럽트 테이블이 있는 DTCM의 맨 아래
- `display-objects.md` — VBlank가 순회하는 태스크 리스트
- `scenes-and-channels.md` — 메인 스레드가 실행 중인 게임 루프
