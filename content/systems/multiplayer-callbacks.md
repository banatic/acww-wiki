# 멀티플레이 콜백: 무선 구조체 다섯 개와 그 호출 대상
<!-- source: wiki/systems/multiplayer-callbacks.md -->

**요약.** 게임의 무선 코드는 `0x0226bdec`, `0x0226bdf0`, `0x0226bdf4`, `0x0226bdf8`의 **16바이트에 모인 전역 변수 네 개**에 상태를 유지한다. 세션 구조체, 스캔/비컨 구조체, **통신 컨텍스트**, 난수 시드이며, 바로 아래에는 항목 네 개의 WM 진입점 표도 있다. 통신 컨텍스트 끝에는 `+0x9c`부터 `+0xbc`까지 **연속된 함수 포인터 워드 여덟 개의 콜백 블록**이 있고, **함수 하나가 리터럴 풀 하나에서 여덟 개 모두를 설치한다.** 열두 지점이 그중 하나를 읽고 분기한다. 게임이 직접 할당하는 **비컨/AP 테이블 매니저**와 **요청별 블록**이라는 두 구조체도 콜백을 하나씩 가진다. 이 다섯 구조체를 통해 ov066은 무선 통신을 마을 방문으로 바꾼다. 포팅 작업자가 먼저 만나는 것은 콜백 블록이다. 그 안의 워드는 DS에서만 의미가 있는 ov066 코드 주소이기 때문이다.

## 무슨 일이 일어나는가

`data_ov066_0226bdf4`는 구조체가 아니라 포인터다. `0x0226bdf4`의 워드는 모듈이 할당한 통신 컨텍스트의 주소를 담는다.
[S: `func_ov066_0226b9b8`, ov066, `src/matched/func_ov066_0226b9b8.c` is unwritten; read from
the ROM's own bytes at `0x0226b9e4`-`0x0226ba50`]
[E: `scratchpad/struct100/item2-census.txt`]. 옆의 전역 변수 세 개도 같은 형태다. `0x0226bdec`는 세션 구조체, `0x0226bdf0`는 스캔/비컨 구조체이며, `0x0226bdf8`은 모듈이 프레임을 보낼 때마다 먼저 `seed * 0x5eedf715 + 0x1b0cb173`로 진행시키는 32비트 시드다 [S: `src/matched/func_ov066_0226943c.c:88`, `src/matched/func_ov066_02269528.c:44`].

**함수 하나가 콜백 블록 전체를 설치한다.** `func_ov066_0226b9b8`은 컨텍스트 포인터를 한 번 읽고, 리터럴 두 개씩을 끼워 넣으며 `+0x9c`, `+0xa0`, `+0xa4`, `+0xac`, `+0xb0`, `+0xb4`, `+0xa8`, `+0xbc` 순서로 ov066 코드 주소 여덟 개를 저장한다 [S: ov066 `0x0226b9e4`..`0x0226ba4c`, disassembled with `tools/agent/target.py`]
[E: `scratchpad/struct100/item2-census.txt`]. 마지막에는 게임 자체 핸들러를 SDK에 등록한다. `WM_SetPortCallback(0xc, func_ov066_0226923c, 0)`, `WM_SetPortCallback(0xd, func_ov066_0226aab8, 0)`, `WM_SetIndCallback(func_ov066_0226b818)`이다 [S: ov066 `0x0226bb0c`..`0x0226bb30`; the two SDK
entry points are `src/matched/WM_SetPortCallback.c` at `0x021210c0` and
`src/matched/WM_SetIndCallback.c` at `0x0212111c`]. 따라서 **포트 12와 13은 게임의 것**이며, indication 핸들러는 함수 하나다.

`+0xb8`은 `func_ov066_0226b9b8`이 채우지 않는 유일한 슬롯이다. 공개 설정자의 필드이며 두 함수가 호출자에게 받은 워드를 쓴다. 인터럽트를 끄고 저장한 뒤 복원하는 것만 하는 `func_ov066_02267fe8`과 `func_ov066_02269c28`이다 [S: `src/matched/func_ov066_02267fe8.c:15`; ov066 `0x02269d64`]. 그래서 `+0xb4`와 `+0xb8`은 같은 필드의 두 표기가 아니라, 인자 수가 다른 별개의 함수가 읽는 필드다. `+0xb4`는 설치 시 고정되며 인자가 없고, `+0xb8`은 전송마다 설정되며 인자 세 개를 받는다 [S: `src/matched/func_ov066_02269934.c`; ov066 `0x0226b3a0`-`0x0226b3bc`].

**비컨/AP 테이블**은 별도로 게임이 직접 할당한다. 태그, 활성 개수, 용량, 항목 배열, `OSAlarm` 배열, `+0xc`의 콜백 하나를 가진 매니저 구조체다. 각 항목에는 6바이트 MAC, 채널, 6슬롯 신호 강도 링과 평균, 매니저 역포인터, 비컨 본문인 0xc0바이트 페이로드가 있다. 같은 MAC을 다시 보면 링을 갱신하고 항목의 알람을 다시 설정한다. 새 MAC은 첫 빈 슬롯을 차지하며, 매니저 콜백을 호출하는 유일한 삽입 경로다. 항목 알람이 울리면 피어가 조용해진 것이며 핸들러에서 같은 콜백을 다시 호출한다 [S: `src/matched/func_ov066_0226a494.c:83-160`, `src/matched/func_ov066_0226a43c.c:22-31`]. 알람 간격은 호출자의 밀리초를 `(interval * 33514) / 64`로 틱으로 바꾼 것이며 태그는 `manager tag + 0x80`이다 [S: `src/matched/func_ov066_0226a494.c:104`].

## 어디에 있는가

| 함수 또는 심볼 | 모듈 | 역할 | 등급/출처 |
|---|---|---|---|
| `data_ov066_0226bdec` | ov066 | 세션 구조체 포인터 | [S: `src/matched/func_ov066_02268570.c:33`] |
| `data_ov066_0226bdf0` | ov066 | 스캔/비컨 구조체 포인터 | [S: `src/matched/func_ov066_0226783c.c:41`] |
| `data_ov066_0226bdf4` | ov066 | 통신 컨텍스트 포인터 | [S: `src/matched/func_ov066_02269934.c:14`] |
| `data_ov066_0226bdf8` | ov066 | 송신 헤더용 32비트 LCG 시드 | [S: `src/matched/func_ov066_02269528.c:32`] |
| `data_ov066_0226bdc0` | ov066 | WM 진입점 네 개: `WM_Enable`, `WM_Disable`, `WM_PowerOn`, `WM_PowerOff` | [S: `config/adm-kr/arm9/overlays/ov066/relocs.txt`, four `kind:load module:autoload(2)` rows; `config/adm-kr/arm9/autoload_2/symbols.txt`] |
| `func_ov066_0226b9b8` | ov066 | 콜백 블록 전체 설치 및 포트 12/13 등록 | [S: ov066 `0x0226b9b8`, 0x1c4 bytes] |
| `func_ov066_02267fe8` | ov066 | `+0xb8`의 공개 설정자 | [S: `src/matched/func_ov066_02267fe8.c`] |
| `func_ov066_0226a494` | ov066 | 비컨 테이블 삽입/갱신; 항목마다 알람 하나 설정 | [S: `src/matched/func_ov066_0226a494.c`] |
| `func_ov066_0226a43c` | ov066 | 항목 만료를 처리하는 알람 핸들러 | [S: `src/matched/func_ov066_0226a43c.c`] |
| `WmReceiveFifo` | main | 모든 WM 응답의 ARM9 측; `WMArm9Buf` 콜백 멤버 네 개 모두 디스패치 | [S: `src/matched/WmReceiveFifo.c:161-235`] |

## 읽고 쓰는 데이터

통신 컨텍스트의 콜백 블록이다. "워드"는 `func_ov066_0226b9b8`이 설치하는 값이다. 예외인 `+0xb8`은 대신 설정자를 적는다.

| 주소 또는 필드 | 의미 | 쓰는 쪽 | 읽는 쪽 |
|---|---|---|---|
| ctx `+0x9c` | 상태 변경 통지, `void (*)(void)` — 가장 많이 읽는 슬롯 | `func_ov066_0226b9b8` → `func_ov066_0226a960` | `func_ov066_02268570` (상태 코드 0xa), `func_ov066_02268e14`, `func_ov066_02268f98`, `func_ov066_02269a14` (정리) |
| ctx `+0xa0` | `void (*)(void)`, 상태 코드 0xb에서 호출 | `func_ov066_0226b9b8` → `func_ov066_0226af3c` | `func_ov066_02268570` |
| ctx `+0xa4` | `void (*)(void)`, 상태 코드 0xd에서 호출 | `func_ov066_0226b9b8` → `func_ov066_0226af04` | `func_ov066_02268570` |
| ctx `+0xa8` | 설치되지만 **ov066 어디에서도 읽지 않음** | `func_ov066_0226b9b8` → `func_ov066_0226b90c` | 없음 (ov066 함수 171개 전수 검사) |
| ctx `+0xac` | 송신 훅, `void (*)(void *buf, u32 len, u32 mask, void *done)` | `func_ov066_0226b9b8` → `func_ov066_0226ae1c` | `func_ov066_0226943c` (0x68바이트 상태 방송), `func_ov066_02269528` (8바이트 비컨) |
| ctx `+0xb0` | 포트 송신 큐 삽입, int 네 개 | `func_ov066_0226b9b8` → `func_ov066_0226b81c` | `func_ov066_022698ec` |
| ctx `+0xb4` | `int (*)(void)`, 설치 시 고정 | `func_ov066_0226b9b8` → `func_ov066_0226b8bc` | `func_ov066_02269934` |
| ctx `+0xb8` | 수신 완료, `void (*)(int idx, u32 base, u32 len)` — 전송마다 설정 | `func_ov066_02267fe8` (공개 설정자), `func_ov066_02269c28` | `func_ov066_0226b27c` |
| ctx `+0xbc` | 인자 하나의 핸들러, `void (*)(void *)` | `func_ov066_0226b9b8` → `func_ov066_0226aeb8` | `func_ov066_02269204` |
| ctx `+0x14` | 두 송신 경로가 헤더를 만드는 전송 버퍼 | 여기서 확정하지 않음 | `func_ov066_0226943c`, `func_ov066_02269528` |
| ctx `+0x28`, 0x60바이트 | 0x68바이트 방송으로 보내는 상태 블록 | 여기서 확정하지 않음 | `func_ov066_0226943c` |
| ctx `+0xc0` | 상태 워드; 비트 0 "바쁨", 비트 1 "대기", `lsl #0x1f / asrs #0x1f`로 읽음 | 다수 | 다수 |
| session `+0x30` / `+0x34` | 호출자가 제공하는 완료 콜백과 인자 | `func_ov066_02267530`, `func_ov066_022672b8`, `func_ov066_0226b9b8` | `func_ov066_02266bf4` |
| session `+0x38` | 호출자가 제공하는 `int (*)(void)` | `func_ov066_02267530` | `func_ov066_02266824` |
| scan `+0x6c` | 비컨별 수락 훅, `int (*)(void *)` | `func_ov066_02267e00`, `func_ov066_02267e28` | `func_ov066_0226783c` |
| manager `+0xc` | 비컨 테이블 항목 훅, `void (*)(Entry *)` | 게임 자체 할당 | `func_ov066_0226a494` (삽입), `func_ov066_0226a43c` (만료) |
| request block `+0x20` | 완료 콜백, `void (*)(void *self)`, `+2`가 0일 때 호출 | 게임 자체 할당 | `func_ov066_0226adcc` |
| `WMArm9Buf +0x18`, 42개 항목 | WM 비동기 API 콜백 표 | 각 `WM_*Async` 호출자 | `WmReceiveFifo` |
| `WMArm9Buf +0xc0` | `indCallback` | `WM_SetIndCallback` ← `func_ov066_0226b818` | `WmReceiveFifo` |
| `WMArm9Buf +0xc4`, 16개 항목 | `portCallbackTable`; 12와 13은 게임의 것 | `WM_SetPortCallback` ← `func_ov066_0226923c`, `func_ov066_0226aab8` | `WmReceiveFifo` |

[S: every row's reader and writer resolved by disassembling all 171 ov066 functions for
`ldr`/`str` at `+0x9c`..`+0xbc` and for the literal `0x0226bdf4`; the literal appears in 60
ov066 functions and in NO other module]
[E: `scratchpad/struct100/item2-census.txt`]

## 확인 방법

블록의 읽는 쪽과 설치자는 정적 사실이며, 이를 발견한 전수 검사는 게임 없이 재현할 수 있다. `tools/agent/target.py`로 ov066을 디스어셈블하고 아홉 오프셋 중 하나의 모든 `ldr`/`str`을 나열한 뒤, 여덟 명령어 안에 해당 레지스터로 분기하는 로드를 남긴다. 위 표의 일곱 슬롯에 걸쳐 로드 열두 개가 남고 저장 함수는 세 개다. 런타임 측면, 즉 슬롯 워드가 호스트 주소가 아닌 실제 ov066 주소라는 것은 포트 자체의 검사 `python port/tools/test_callback_struct.py`로 확인한다. 각 필드에 실제 ARM 워드를 놓고 모든 읽는 쪽이 표에 적힌 인자로 인터프리터에 진입해야 한다. 음성 대조 조건은 대신 그 워드를 직접 호출하여 `0xc0000005`로 죽는다 [E: `scratchpad/struct100/fixture/receipt.json`].

## 가설

- **`+0xa8`은 설치되지만 읽지 않는다.** 컨텍스트 포인터가 도달하지 않는 모듈에 읽는 쪽이 있거나(전역 참조는 ov066에만 있으므로 인자로 전달돼야 한다), 흔적만 남은 슬롯이다. 실행 중인 호스트와 게스트의 `+0xa8`에 식별 가능한 워드를 넣고 전체 방문 동안 읽는 곳이 있는지 확인하면 확정할 수 있다. `experiments/`에는 아직 이 문서가 없다.
- **`+0xbc` 핸들러 인자의 정체는 확인되지 않았다.** 유일한 읽는 쪽은 자신의 첫 인자를 그대로 전달한다. 따라서 누가 어떤 값으로 `func_ov066_02269204`를 호출하는지가 문제다. `func_ov066_02268f98`이 피어별 구조체의 16비트 필드로 호출한다.
- **비컨 페이로드는 0xc0바이트이며 여기서는 레이아웃을 읽지 않았다.** 스캔 필터의 수락 훅이 판단하는 비컨 본문이므로 `multiplayer-protocol.md`의 비컨 절과 이 문서의 매니저 항목은 같은 바이트를 양쪽에서 설명한다.

## 관련 문서

- [`multiplayer-protocol.md`](multiplayer-protocol.md) — 이 콜백들이 운반하는 제어 id
- [`multiplayer-visit.md`](multiplayer-visit.md) — 호스트와 게스트가 실행하는 열 단계 도착 절차
- [`network.md`](network.md) — 두 무선 스택과 포트의 응답
- [`wifi-g2.md`](wifi-g2.md) — 이 콜백들이 처음 실제 워드를 갖는 검증 단계
