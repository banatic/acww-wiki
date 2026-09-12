# 네트워크
<!-- source: wiki/systems/network.md -->

**요약.** 로컬 마을 방문과 온라인 방문은 게임 통신 코드를 공유하지만 서로 다른 전송을 사용한다. 로컬 멀티플레이어는 오버레이 66을 통해 WM에 도달하고, 온라인 플레이는 오버레이 65의 DWC, 소켓, TLS 코드에 도달한다. 현재 인터프리터 호스트에는 태그 10 ARM7 무선 서비스가 없다. 이는 하드웨어 서비스의 공백이며 모든 네트워크 함수가 스텁으로 대체되었다는 근거는 아니다.
[S: `src/matched/func_020ec338.c:36`, `src/matched/CPS_TcpConnect.c:18`]
[E: `scratchpad/wifi-analysis-1/stage1-evidence.json` host source audit]

## 무슨 일이 일어나는가

### 구현이 필요한 경계

공통 수신 핸들러는 제어 엔벨로프를 파싱하고 메시지 ID를 디스패치하며, 퍼사드는 모드 1/2와 3/4에 서로 다른 전송 구현을 선택한다. 상세한 정적 맵, 24개 제어 ID, 벌크 전송 메커니즘 및 남은 미지 사항은 [멀티플레이어 프로토콜](multiplayer-protocol.md)에 있다.
[S: `src/matched/func_02075050.c:33`, `src/matched/func_020ec338.c:36`]

로컬 `ov066`은 WM 부모/자식과 MP 서비스를 시작하며, 퍼사드는 12와 13에 논리 포트 콜백 2개를 등록한다. WM은 `autoload_2`에 있으며 `ov065` 내부에 있지 않다. 설정 UI의 `ov001` 데이터 공유 헬퍼와 `ov067` WXC 드라이버는 별도의 소비자이며, 마을 방문에 사용할 상수를 추정하는 근거로 삼아서는 안 된다.
[S: `src/matched/func_020ecce4.c:49`, `src/matched/func_ov066_0226b9b8.c:101`,
`src/matched/WM_StartMPEx.c:1`, `src/matched/func_ov001_02229e98.c:841`,
`src/matched/WXCi_CallSendEvent.c:377`]

WM의 FIFO 송신자는 요청 버퍼 포인터와 함께 태그 10을 기록한다. 현재 호스트 디스패치는 태그 7, 6, 11, 5를 명시적으로 처리하는 반면 태그 10은 수락 후 버리는 폴백에 도달한다. 이는 소스 감사이며, 게이트 메뉴 실행 근거 기록도 아니고 게이트가 이미 해당 분기에 도달했다는 주장도 아니다.
[S: `src/matched/WMi_SendCommand.c:112`]
[E: `scratchpad/wifi-analysis-1/stage1-evidence.json` host `port/shim/os/pxisend.c:661`]

이전 페이지의 네트워크 코드가 전혀 실행되지 않는다는 포괄적인 서술은 레거시 네이티브 설계를 반영한 것이었다. 정책 문서만으로는 인터프리터를 그렇게 설명할 수 없다. 구체적으로 지원되지 않는 서비스는 태그 10 응답 계약의 부재이다.
[E: `scratchpad/wifi-analysis-1/stage1-evidence.json`]

### WFC와 ARM9/ARM7 분리

WCM은 액세스 포인트/DCF 연결 관리를 제공하며, DWC 인터넷 펌프는 연결 후 페이즈 9를 검사한다. SOCL 명령 패킷은 ARM9 소프트웨어의 OS 메시지 큐를 통해 이동한다. 이 큐를 ARM7 소켓 명령 파이프라고 부르는 것은 잘못이다.
[S: `src/matched/func_ov065_0227f32c.c:58`,
`src/matched/SOCLi_SendCommandPacket.c:3102`]

`CPS_TcpConnect`는 세션 SSL 플래그를 사용해 `CPSi_SslConnect` 또는 raw TCP를 선택한다. 따라서 ARM7 무선을 교체하거나 IP를 전달하는 것만으로는 ARM9 TLS를 자동으로 우회할 수 없다. 소켓 수준의 호스트 교체는 TLS 경계를 선택하고 시험해야 한다.
[S: `src/matched/CPS_TcpConnect.c:18`]

게임의 온라인 초기화 함수는 인터넷 연결, DWC 초기화/로그인, 친구 및 전송 준비 완료를 차례로 진행한다. 친구 레코드 32개를 제공하고, 이후 256바이트 전송 분할 크기를 선택한다. 이 사실만으로는 교체 서버와의 호환성이 확립되지 않는다.
[S: `src/matched/func_020ec980.c:41`, `src/matched/func_020ec980.c:59`,
`src/matched/func_020ec980.c:75`]

인증 빌더에는 RTC 날짜/시간과 액세스 포인트 메타데이터가 필요하다. 과거 날짜를 성공적으로 읽었다고 해서 서버가 로그인을 거부한다는 것이 입증되는 것은 아니다. 이를 입증하려면 서버 근거가 필요하다. 고정된 시계가 반드시 로그인을 막는다는 이전 주장은 근거가 없었다.
[S: `src/matched/func_ov065_02274798.c:579`]

### 소스 이름만으로는 충분하지 않다

`func_ov066_02268c4c`는 스캔 래퍼에서 복사되었으며 여전히 스캔 피호출자의 이름을 갖고 있다. 호출 지점 `0x02268c64`의 설정 재배치는 대신 부모 파라미터 설정을 식별하며, 소유자가 검사한 shadow도 `WM_SetParentParameter`를 이름으로 가리킨다. 해당 shadow/맵 관측은 해시와 함께 보존되어 있으며 새로 빌드한 헬퍼 실행 파일에 대한 주장은 아니다. [S: `src/matched/func_ov066_02268c4c.c:13`]
[E: `scratchpad/wifi-analysis-1/stage1-evidence.json`]

스테이지 1 센서스는 매칭된 C/C++ 파일 29,084개와 설정 호출 재배치 행 79,747개를 찾았다. 어휘적 참조, 복구되지 않은 경계, 간접 콜백 때문에 이 센서스는 완전한 런타임 호출 그래프가 될 수 없다.
[E: `scratchpad/wifi-analysis-1/stage1-evidence.json`]

## 어디에 있는가

| 계층 | 모듈 | 진입점 / 근거 |
|---|---|---|
| 공통 게임 제어 수신 | main | `0x02075050`부터 `0x02075240`까지. [S: `src/matched/func_02075050.c:36`] |
| 전송 퍼사드 | autoload_2 | `0x020ec338`, `0x020ecce4`, `0x020ec980`. [S: `src/matched/func_020ec338.c:36`, `src/matched/func_020ecce4.c:35`, `src/matched/func_020ec980.c:39`] |
| 로컬 마을 전송 | ov066 | MP 시작, 포트 12/13. [S: `src/matched/func_ov066_022686f0.c:20`, `src/matched/func_ov066_0226b9b8.c:101`] |
| 무선 매니저 | autoload_2 | `WM_StartMPEx`, `WMi_SendCommand`. [S: `src/matched/WM_StartMPEx.c:1`, `src/matched/WMi_SendCommand.c:74`] |
| 온라인 전송 | ov065 | 신뢰성 있는 DWC 송신자 `0x0227eda0`. [S: `src/matched/func_ov065_0227eda0.c:100`] |
| TLS와 raw 소켓 | ov065 | `CPS_TcpConnect`. [S: `src/matched/CPS_TcpConnect.c:18`] |

## 읽고 쓰는 데이터

| 데이터 | 확립된 역할 |
|---|---|
| `0x021fbef8` | 공통 전송 모드. [S: `src/matched/func_020ecce4.c:40`] |
| `0x021fbefc` | 온라인 초기화 페이즈. [S: `src/matched/func_020ec980.c:41`] |
| `0x020ccff0` | 인덱스된 제어 디스패치. [S: `src/matched/func_02075240.c:5`] |
| WM 요청 버퍼 | 256바이트 ARM9 요청 슬롯; FIFO 포인터와 수락 비트. [S: `src/matched/WMi_SendCommand.c:83`] |
| 친구 항목 | 12바이트 계정 레코드와 0x23바이트 게임 레코드. [S: `src/matched/func_020eae80.c:33`] |

## 확인 방법

스테이징된 소스 센서스와 보고서는 `scratchpad/wifi-analysis-1/` 아래에 있다. 첫 런타임 테스트에서는 오버레이 상주, 모드/상태 값, WM API/콜백 ID를 포함한 제한된 게이트 경로를 캡처한다. 요청한 엔드포인트와 오류 없음을 확인하고, 관찰기를 비활성화했을 때 출력이 변하지 않는지도 확인한다. 조용한 싱글플레이어 로그는 멀티플레이어 호환성이나 모든 네트워킹에 도달할 수 없다는 사실 어느 쪽도 입증하지 않는다.
[E: `scratchpad/wifi-analysis-1/stage1-evidence.json`]

## 가설

- 보존된 ARM9 로컬 스택 아래에 WM을 먼저 구현한다. 두 마을 방문을 약속하기 전에 초기화와 스캔 콜백 소유권을 입증한다. [S: `src/matched/WMi_SendCommand.c:83`, `src/matched/WM_StartConnectEx.c:585`]
- 기존 수신 디스패치에 앞서 제어 엔벨로프와 벌크 오프셋을 검증한다. 일부 수신기는 눈에 보이는 로컬 범위 검사 없이 외부 오프셋을 복사한다. 상위 단계의 길이 검증 감사가 여전히 필요하다. [S: `src/matched/func_02075670.c:25`, `src/matched/func_0207557c.c:15`]

## 관련 문서

- [멀티플레이어 프로토콜](multiplayer-protocol.md).
- [구현 선택지와 게이트](wifi-port-plan.md).
