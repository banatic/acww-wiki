# 오프라인 ARM7 모델의 WM 요청 수명
<!-- source: wiki/systems/wifi-g1.md -->

**요약.** 기본으로 꺼진 WM 모델은 기존 PXI 인터럽트 경로와 WM 전용 IRQ 활성화 경계에서 제한된 요청을 완료한다. 콜백, 슬롯 재사용, 문 UI는 원래 ARM9 WM과 게임 코드가 계속 담당한다. 초기화나 MP 시작 콜백의 성공이 무선 통신, 원격 마을, 멀티플레이 성공을 뜻하지는 않는다.

## 무슨 일이 일어나는가

`ACWW_WM_STUB=1`은 인터프리터 경로에서만 모델을 켠다. 부트스트랩 메타데이터가 없으면 합성된 로컬 관리 MAC과 채널 1..13 마스크를 제공한다. 스위치를 설정하지 않은 경로와 네이티브 경로는 이 메타데이터 워드를 읽지 않는다.
[S: `port/shim/os/pxisend.c`, `wm_stub_bootstrap`]

수락한 요청에는 단조 증가하는 토큰과 비공개 256바이트 요청 사본을 부여한다. 기존 PXI 큐가 응답을 전달하고 ARM9 `WmReceiveFifo`가 재사용 가능 비트를 설정할 때까지 원래 슬롯은 사용할 수 없다. 제한된 두 경계 IRQ 정책은 수락 후 첫 활성화/복원을 관측하고 그 이후 경계에서만 완료를 허용한다. 인터럽트가 꺼졌거나 재진입한 호출에서는 큐를 비우지 않는다. 이로써 Reset 호출자가 대기 플래그를 기록하기 전에 송신 후 메시지 큐 게시가 보존된다. 이는 ARM7 타이밍이 아니라 합성 지연이다.
[S: `port/shim/os/pxisend.c`, `acww_wm_irq_poll`; `port/shim/os/interrupts.c`; `src/matched/WMi_SendCommand.c`, `func_ov066_02266a08.c`]

중복 제출, 가득 찬 큐, 잘못된 슬롯 포인터는 수락 전에 거부한다. 이미 완료된 토큰은 두 번째 응답을 쓰거나 전달할 수 없다.
[S: `port/shim/os/pxisend.c`, `wm_stub_submit`, `wm_stub_complete`; `src/matched/WmReceiveFifo.c`]

초기화 상태는 Enable에서 READY 0 -> STOP 1, PowerOn에서 IDLE 2가 된다. 통합 Initialize는 IDLE에 도달한다. CLASS1은 내부 무선 전이이며 이 모델이 입증한 별도의 ARM9 초기화 콜백이 아니다.
[S: `src/matched/WM_Enable.c`, `WM_PowerOn.c`, `WM_Initialize.c`]
[P: NitroSDK 2.2a, `man/en_US/wm/wm/WM_Enable.html`]

Scan은 부모를 찾지 못한 성공 상태 코드 4를 반환한다. StartConnect에는 `WM_ERRCODE_NO_PARENT` 열거값이 없다. SDK 콜백은 부모를 찾지 못한 경우를 오류 코드 9인 타임아웃으로 문서화한다. 이 픽스처는 IDLE을 유지하면서 그 실패를 반환하며, 연결 통지나 AID 할당은 하지 않는다.
[S: `port/shim/os/pxisend.c`, `wm_stub_complete`; `src/matched/WM_StartConnectEx.c`]
[P: NitroSDK 2.2a, `include/nitro/wm/common/wm.h`, WMStartConnectCallback]

StartParent는 SDK BEACON_SENT 통지(API 8, 상태 코드 2)도 예약한다. 공유 ARM7 콜백 버퍼, 별도 토큰 0, 콜백 제어 핸드셰이크를 사용하며 완료된 요청 슬롯을 재사용하거나 최종 응답으로 집계하지 않는다. TU 주기는 60 Hz를 사용해 프레임으로 올림하므로 타이밍 근사다.
[S: `port/shim/os/pxisend.c`, `wm_stub_frame`; `src/matched/WmClearFifoRecvFlag.c`]
[P: NitroSDK 2.2a, WMStartParentCallback]

## 어디에 있는가

| 경계 | 모듈/파일 | 역할 | 근거 |
|---|---|---|---|
| `PXI_SendWordByFifo` | host pxisend.c | 요청 수락과 기존 전달 큐. [S: `port/shim/os/pxisend.c`] |
| `WMi_SendCommand` | autoload_2 | ARM9 슬롯 큐, API 하프워드, 인자 워드. [S: `src/matched/WMi_SendCommand.c`] |
| `WmReceiveFifo` | autoload_2 | ARM9 콜백 디스패치와 최종 슬롯 해제. [S: `src/matched/WmReceiveFifo.c`] |
| `func_ov066_0226a074` | ov066 | 채널 측정 콜백, 채널 +8과 바쁨 비율 +10. [S: `port/build/shadow/func_ov066_0226a160.c`] |
| `acww_online_relay_send` | 단독 실행 훅 / 오프라인 어댑터 | 제한된 바이너리 프레임 경계. [S: `port/shim/os/pxisend.c`] |

`0226a074`를 투표/확인 핸들러라고 부른 이전 복원 주석은 프로토콜 사실이 아니다. 섀도 호출자는 WM_MeasureChannel을 연결하며 읽는 필드도 해당 SDK 콜백과 일치한다. 매칭 소스는 수정하지 않는다.
[S: `port/build/shadow/func_ov066_0226a160.c`, `src/matched/WM_MeasureChannel.c`]

## 읽고 쓰는 데이터

| API | 성공 시 모델 상태 / 결과 | 응답 필드와 근거 |
|---|---|---|---|
| 0 Initialize | 0 -> 2 | API +0, 오류 +2. [S: `port/shim/os/pxisend.c`, `wm_stub_complete`] |
| 3 Enable; 5 PowerOn | 0 -> 1; 1 -> 2 | API +0, 오류 +2. [S: `port/shim/os/pxisend.c`, `wm_stub_complete`] |
| 4 Disable; 6 PowerOff | 1 -> 0; 2 -> 1 | API +0, 오류 +2. [S: `port/shim/os/pxisend.c`, `wm_stub_complete`] |
| 7 Parent parameter | 2 유지 | 제한된 64바이트 매개변수와 <=112바이트의 불투명 사용자 데이터 복사. [S: `port/shim/os/pxisend.c`, `wm_stub_complete`] |
| 8 StartParent | 2 -> 7 | +8의 시작 코드 0; 자식 비트맵 없음. [S: `port/shim/os/pxisend.c`, `wm_stub_complete`] |
| 10 Scan; 11 EndScan | 2/5 -> 5; 5 -> 2 | +8의 스캔 코드 4, 채널 +16. [S: `port/shim/os/pxisend.c`, `wm_stub_complete`] |
| 12 Connect | 2 유지, 오류 9 | AID 없음, 연결 성공 없음. [S: `port/shim/os/pxisend.c`, `wm_stub_complete`] |
| 14 StartMP; 16 EndMP | 7 -> 9; 9 -> 7 | +4의 MP 시작 코드 10; 수신 데이터 없음. [S: `port/shim/os/pxisend.c`, `wm_stub_complete`] |
| 30 MeasureChannel | 2 유지 | 채널 +8, 합성된 바쁨 비율 0은 +10. [S: `port/shim/os/pxisend.c`, `wm_stub_complete`] |

이는 실제 ARM7이나 피어의 관측이 아니라 스텁 전이 계약이다. Reset/End, 게임 정보 갱신, 비컨 표시, 부모 진입 활성화도 범위가 제한돼 있다. 지원하지 않는 동작은 성공을 주장하지 않고 명시적 오류로 끝난다.
[S: `port/shim/os/pxisend.c`, `wm_stub_complete`]

ARM9이 사용하는 상태 필드는 상태 +0, MP 플래그 +0xc, 버퍼 +0x46..0x54, MAC +0xdc, 부모 매개변수 +0xe4, 자식 비트맵 +0x17e, AID +0x184, 크기 한도 +0x18e/+0x190, 채널 마스크 +0x1f0/+0x1f2다. 지속되는 호스트 요청 사본, 토큰, 상태 포인터, 부모 데이터는 세이브스테이트 블롭으로 등록된다.
[S: `src/matched/WM_StartMPEx.c`, `WM_SetMPDataToPortEx.c`; `port/shim/os/pxisend.c`]

## 확인 방법

`python port/tools/test_wm_stub.py`로 실제 소스의 소유권, 부모 없음, 중복 완료, 릴레이 봉투, 제한된 비컨 서비스를 합성 검사한다. 의도적으로 틀린 타임아웃 기대값을 픽스처가 거부하는 검사도 포함한다. OFF와 네이티브 조건에서는 에뮬레이션 메타데이터를 매핑하지 않고도 안전하게 반환해야 한다.
[E: `scratchpad/wifi-g1-1/fixture-native-irq-fields/receipt.json`]

게임플레이는 이전 문지기 계획, LIVE46 시드의 비공개 사본, `ACWW_CARD_FAST=32`, `ACWW_TICK_MODEL` 미설정, `ACWW_RTC_DATE=20260911`, `ACWW_RTC_TIME=113000`, `ACWW_RTC_FREEZE=0`, 프레임 3000과 7300의 같은 빌드 스냅샷을 사용한다. 각 분기 JSON에는 `ACWW_STOP_FRAME=18000`, `ACWW_WM_STUB=1`, `ACWW_WM_REQUEST_TRACE=1`을 명시한다. 이는 공개된 프런티어가 아니라 직접 진단이다.
[S: `scratchpad/wifi-g1-1/prepare.py`, `runner.py`, `guest-irq-1.json`, `host-irq-1.json`]

같은 빌드의 스냅샷을 준비한 뒤 `python -B scratchpad/wifi-g1-1/control.py replay-guest scratchpad/wifi-g1-1/runner.py --json replay-guest scratchpad/wifi-g1-1/guest-irq-1.json`을 한 명령으로 실행해 재생한다. 매번 새 실행 이름을 쓰며, 초대 경로에는 호스트 JSON을 사용한다.
[S: `scratchpad/wifi-g1-1/control.py`, `runner.py`]

최종 게스트 실행은 각각 요청 1445개를 수락하고 완료한다. Enable, PowerOn, 빈 스캔 1440회, Reset, PowerOff, Disable이다. 상태 변화는 12581에서 0 -> 1 -> 2 -> 5, 13181에서 5 -> 2 -> 1 -> 0이며 모두 WM 상태 워드에서 읽었다.
[E: `scratchpad/wifi-g1-1/safe/guest-irq-1.json`, `guest-irq-2.json`]

둘 다 고정된 프레임 18000 끝점에서 열린 마을이 없다는 게임 UI에 도달하며, 전체 이벤트 순서와 정지 화면 해시 36개가 모두 같다.
[E: `scratchpad/wifi-g1-1/safe/comparison.json`; `scratchpad/wifi-g1-1/runs/guest-irq-1/shot_018000.bmp` inspected privately]

최종 호스트 실행은 각각 요청 18개(Enable, PowerOn, 채널 측정 13회, 부모 매개변수, StartParent, SetGameInfo)를 수락하고 완료한다. 별도 비컨 통지는 388회이며 프레임 12956부터 끝점 18000까지 PARENT 상태 7을 유지한다.
[E: `scratchpad/wifi-g1-1/safe/host-irq-1.json`, `host-irq-2.json`]

최종 두 실행의 호스트 문 열림 UI, 전체 이벤트 메타데이터, 정지 화면 해시 36개가 모두 일치한다. 어느 전체 구간에서도 StartMP 요청은 발생하지 않는다.
[E: `scratchpad/wifi-g1-1/safe/comparison.json`; `scratchpad/wifi-g1-1/runs/host-irq-1/shot_018000.bmp` inspected privately]

관측된 피어 경계는 CHILD_CONNECTED다. 그 핸들러는 컨텍스트 비트 0x20을 설정하며, SetGameInfo 콜백은 그 비트가 설정됐을 때만 StartMP 래퍼를 호출한다. 따라서 합성 픽스처는 MP 전이를 입증하지만 피어 없는 게임 경로는 실제 MP 제출을 입증하지 않는다.
[S: `port/build/shadow/func_ov066_0226908c.c`, `func_ov066_02268798.c`, `func_ov066_022686f0.c`]

IRQ 훅 이전에는 기본 시계 게스트가 수락된 요청을 대기 상태로 남긴 채 프레임 13181에서 멈췄다. TICK_MODEL=1은 18000에 도달했지만 정리 기한이 만료된 뒤였으며 통신 중단 UI를 보였다. 이는 실패한 별개의 시계 조건이다.
[E: `scratchpad/wifi-g1-1/safe/guest-stub-1.json`, `guest-tick-1.json`]

최종 새 링크는 stderr가 비어 있고 dark 슬롯 194/256으로 종료 0이다. 스위치를 설정하지 않은 정규 card32와 명시적 card0/2ea19722 비교는 각각 31/31 EXACT를 통과한다.
[E: `scratchpad/wifi-g1-1/safe/link-summary.json`; `off-irq32-data/offgate-check.json`, `off-irq0-data/offgate-check.json`]

## 가설

실제 피어 발견, 부모 선택, MAC 신원 할당, 채널 체류 시간의 정확성, 연결 손실, MP 전달, 실제 ARM7 타이밍은 아직 검증하지 않았다. 두 피어 전송과 원본 하드웨어 콜백 비교는 별도 실험이 될 것이다.
[H: compare a future peer run and original callback trace against these contracts]

## 관련 문서

- [G0 부트스트랩 근거](wifi-g0.md).
- [프로토콜 지도](multiplayer-protocol.md).
- [WM 릴레이 계약](../../docs/kb/hybrid/online-spec.md).
- [런타임 안내](../../docs/kb/hybrid/wifi.md).
