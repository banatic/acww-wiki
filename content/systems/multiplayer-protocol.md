# 멀티플레이어 프로토콜: 소스 맵과 미해결 경계
<!-- source: wiki/systems/multiplayer-protocol.md -->

**요약.** 게임에는 로컬 WM과 온라인 DWC 위에 공통 통신 계층이 있다. 매칭된 소스는 제어 메시지 엔벨로프, 청크 단위 벌크 전송, 네 개의 참가자 슬롯, 여러 동기화 배리어를 드러낸다. 게이트에서 도착까지의 완전한 순서나 전송되는 모든 레코드의 의미는 아직 확립되지 않았다. 이 페이지는 검증된 메커니즘과 두 플레이어 추적이 필요한 이름을 분리한다.
[S: `src/matched/func_02075050.c:33`, `src/matched/func_02075ff8.c:42`,
`src/matched/func_02074330.c:169`]
[E: `scratchpad/wifi-analysis-1/stage1-evidence.json`]

## 무슨 일이 일어나는가

### 근거와 범위

이는 `d9e1409d8b2a21ba5ffc56e467e881168b46cabb`에서 수행한 정적 ADMK 감사이다. 멀티플레이어 세션은 실행하지 않았다. 재현 가능한 센서스는 매칭된 C/C++ 파일 29,084개를 대상으로 하며, 그 어휘적 참조에는 선언과 주소 취득이 포함되고 **확정된 호출 그래프가 아니다**. 설정 호출 재배치 센서스는 주소 식별자를 별도로 제공한다.
[E: `scratchpad/wifi-analysis-1/stage1-evidence.json`]

소스 계층은 `main`의 `0x020730xx..0x02077bxx`, `autoload_2`의 `0x020eadxx..0x020edaxx`에 있는 통신 퍼사드, 로컬 `ov066`, 온라인 `ov065`이다. 로컬 SDK의 `WM_*` 함수 자체는 `autoload_2`에 있다. 오버레이 이름과 호출 대상은 주소 접두사에서 추론한 것이 아니라 설정 메타데이터와 대조했다.
[S: `src/matched/func_02075050.c:26`, `src/matched/func_020ecce4.c:35`,
`src/matched/WM_StartMPEx.c:1`] [E: `scratchpad/wifi-analysis-1/stage1-evidence.json`]

서로 비슷해 보이는 두 항목은 분리해서 다뤄야 한다. `ov001`의 설정/UI 헬퍼는 스테이션당 68바이트와 3스테이션 비트맵으로 포트 13에서 데이터 공유를 시작하고, `ov067`의 WXC 드라이버는 포트 4에서 전송한다. 어느 사실도 마을 방문 프로토콜의 WM 포트나 용량을 확립하지 않는다.
[S: `src/matched/func_ov001_02229e98.c:841`, `src/matched/WXCi_CallSendEvent.c:377`]

### 게이트 및 연결 상태 맵

`ov048`에는 구체적인 스캔 선택 경로가 있다. `func_ov048_02260d28`은 스캔 목록을 얻고, 0x1a바이트 게임 정보 결과를 요구하며, 피어 식별자 6바이트를 비교하고, `func_020eb8d8`을 통해 일치하는 항목을 선택한 뒤 씬 상태 5를 요청한다. 이 상태를 특정한 사람 메뉴 선택에 대응시키는 것은 게이트 추적이 필요한 추론으로 남아 있다.
[S: `src/matched/func_ov048_02260d28.c:42`, `src/matched/func_ov048_02260d28.c:55`,
`src/matched/func_ov048_02260d28.c:64`, `src/matched/func_ov048_02260d28.c:75`]

| 경계 | 소스로 뒷받침되는 전이 또는 동작 | 미해결 의미 |
|---|---|---|
| `func_02074b44`, main, `0x02074b44` | 설정이 로컬 및 온라인 초기화 함수를 호출한다. 이 체크아웃에는 매칭된 본체가 없다. [E: `scratchpad/wifi-analysis-1/stage1-evidence.json`] | 사용자 선택에서 모드로 가는 선택기이다. 분기를 꾸며내지 않는다. |
| `func_020ecce4` | 요청된 모드를 `0x021fbef8`에 저장하고, 16바이트를 지우며, 설정 바이트 8, 60, 2를 준비한다. 동작 1은 로컬 상태 3을, 동작 2는 상태 4를 요청한다. [S: `src/matched/func_020ecce4.c:39`, `src/matched/func_020ecce4.c:55`] | 소스는 로컬 호스트/게스트 모드를 시사하지만 화면과의 대응은 측정되지 않았다. |
| `func_020eb92c` | 8개 항목 결과 목록을 지우고 로컬 상태 7에서만 8개 항목을 폴링한다. [S: `src/matched/func_020eb92c.c:12`] | 스캔 결과 8개가 동시에 방문하는 플레이어 8명을 뜻하지는 않는다. |
| `func_020eb8d8` | 로컬 상태 7에서 선택한 디스크립터의 0xe0바이트를 복사해 `ov066:0x022682ec`에 전달한다. [S: `src/matched/func_020eb8d8.c:13`] | 이 래퍼 너머의 디스크립터 검증이다. |
| `ov066:0x02268c4c` | WM 부모 파라미터 설정을 호출한다. 매칭된 피호출자 이름은 복사된 잘못된 별칭이다. 설정과 소유자의 shadow는 `WM_SetParentParameter`에 일치한다. [S: `src/matched/func_ov066_02268c4c.c:13`] [E: `scratchpad/wifi-analysis-1/stage1-evidence.json`] | 정확한 부모 설정은 실제 초기화 함수를 추적해야 한다. |
| `ov066:0x02268a1c` | 연결 래퍼는 디스크립터, null 선택적 SSID, 절전 1, 인증 모드 0을 `WM_StartConnectEx`의 주소로 전달한다. [S: `src/matched/func_ov066_02268a1c.c:10`] [E: `scratchpad/wifi-analysis-1/stage1-evidence.json`] | 성공적인 연결 콜백과 발견된 비콘 값이다. |
| `ov066:0x022686f0` | MP 시작은 재시도 횟수 4와 고정 주파수 플래그 1을 전달한다. 버퍼 크기와 주파수는 설정 필드에서 온다. [S: `src/matched/func_ov066_022686f0.c:20`] [E: `scratchpad/wifi-analysis-1/stage1-evidence.json`] | 실제 주파수와 부모/자식 크기는 여기의 리터럴 상수가 아니다. |
| `ov066:0x0226b9b8` | 큐 메타데이터를 할당하고 포트 12와 13 및 인디케이션 콜백에 콜백을 설치한다. [S: `src/matched/func_ov066_0226b9b8.c:101`] [E: `scratchpad/wifi-analysis-1/stage1-evidence.json`] | 포트와 게임 메시지의 분류 및 콜백 식별자이다. |
| `func_020ec338` | 모드 1/2는 로컬 수신 버퍼 경로를 사용하고, 모드 3/4는 온라인 경로를 사용하며 AID를 u8로 좁힌다. [S: `src/matched/func_020ec338.c:36`] [E: `scratchpad/wifi-analysis-1/stage1-evidence.json`] | 이는 버퍼 등록이며, 전송 동작이 입증된 것은 아니다. |
| `func_020ec848` | 로컬 정지 상태 0을 요청하고, 틱 타임아웃으로 상태 2를 기다리며, 콜백/작업을 해제한 뒤 모드를 6으로 설정한다. [S: `src/matched/func_020ec848.c:19`] | 세이브/롤백 결과는 이 래퍼의 범위 밖이다. |

### WM 서비스 계약

태그 10의 FIFO 워드는 네트워크 패킷이 아니라 ARM9 메모리의 요청 포인터이다. `WMi_SendCommand`는 256바이트 요청 슬롯을 빌려 쓰고, 수락 비트 0x8000을 검사하며, API 식별자와 파라미터 워드를 저장하고, 포인터를 전송한 뒤 비동기 상태를 반환한다. 호스트 브리지는 요청 소유권, 상태, 이후 콜백을 재현해야 한다.
[S: `src/matched/WMi_SendCommand.c:68`, `src/matched/WMi_SendCommand.c:83`,
`src/matched/WMi_SendCommand.c:106`]

WM 부모 파라미터에는 사용자 게임 정보 포인터/길이, GGID, TGID, entry/max-entry, 키 공유/반송파 감지 플래그, 비콘 주기, 채널, 부모/자식 최대 크기가 들어간다. 이 ARM 레이아웃에서 구조체 크기는 64바이트이다. 검증은 키 공유가 활성화된 경우의 추가 키 공유 오버헤드를 포함해 각 방향을 512바이트로 제한한다.
[S: `src/matched/WM_SetParentParameter.c:127`, `src/matched/WM_SetParentParameter.c:190`,
`src/matched/WM_SetParentParameter.c:202`]

연결 요청에는 24바이트 선택적 SSID 필드와 BSS 디스크립터 포인터가 들어간다. 이는 BSS 디스크립터의 32바이트 SSID 저장 공간 및 WM 게임 정보와는 별개이다. 일반 게임 정보 구조체는 사용자 데이터 112바이트를 예약한다. 이는 SDK 용량이며 게이트가 112바이트 전부를 전송한다는 주장은 아니다.
[S: `src/matched/WM_StartConnectEx.c:361`, `src/matched/WM_StartConnectEx.c:382`,
`src/matched/WM_StartConnectEx.c:534`, `src/matched/WM_StartConnectEx.c:589`]

MP 시작에는 부모/자식 상태 7/8, 64바이트 단위의 수신 정렬, 32바이트 단위의 전송 크기 정렬이 필요하다. 요청은 수신 이중 버퍼를 고려해 수신 버퍼 바이트 크기의 절반을 전송한다. 상태 9/10에서의 MP 전송은 데이터 주소, 바이트 크기, 대상 비트맵, 논리 포트, 우선순위, 콜백/컨텍스트를 전달하며, 부모 헤더 4바이트 또는 자식 헤더 2바이트의 추가 여유 공간을 검사한다.
[S: `src/matched/WM_StartMPEx.c:67`, `src/matched/WM_StartMPEx.c:86`,
`src/matched/WM_StartMPEx.c:104`, `src/matched/WM_SetMPDataToPortEx.c:117`,
`src/matched/WM_SetMPDataToPortEx.c:131`]

일반 데이터 공유에는 4개의 데이터셋 버퍼, 스테이션 비트맵, 스테이션별 길이가 있으며, 전체 데이터는 4바이트 비트맵 헤더를 더해 508바이트로 제한된다. 일반 키 공유는 길이 2, 비트맵 0xffff, 이중 버퍼를 사용해 해당 서비스를 호출한다. 이 감사로는 게임의 `ov066` 방문 경로가 어느 편의 API를 사용하는지 **확립되지 않는다**. 포트 13만으로는 이를 확립할 수 없다.
[S: `src/matched/WM_StartDataSharing.c:42`, `src/matched/WM_StartDataSharing.c:182`,
`src/matched/WM_StartKeySharing.c:80`]

### 온라인 로그인과 전송

게임 수준의 온라인 상태 머신은 `func_020ec980`이며, `0x021fbefc`를 키로 한다. 0은 초기화/연결하고, 1은 인터넷 상태 4를 기다리며, 2는 32개 항목 친구 목록으로 DWC 제어를 초기화하고 로그인을 시작하며, 3은 콜백 플래그를 기다리고, 4는 다음 완료를 기다린 뒤 전송 분할 최대값을 0x100으로 설정하며, 5는 모드별 가드 아래에서 준비 완료를 보고한다. 이는 관측된 지속 시간이 아니라 소스에 나타난 상태이다.
[S: `src/matched/func_020ec980.c:41`, `src/matched/func_020ec980.c:59`,
`src/matched/func_020ec980.c:70`]

인터넷 펌프는 액세스 연결 완료와 WCM DCF 페이즈 9를 검사한다. 이는 ARM9 연결 매니저의 작업이다. 인증 준비에는 성공적인 RTC 읽기와 액세스 포인트 메타데이터가 필요하며, RTC를 성공적으로 읽었다고 해서 서버가 날짜를 어떻게 해석하는지가 입증되는 것은 아니다.
[S: `src/matched/func_ov065_0227f32c.c:58`, `src/matched/func_ov065_02274798.c:579`]

친구 키 검사는 +0x24의 사용자 데이터 필드를 전달하고, 다항식 7을 사용해 8바이트에 대한 7비트 CRC8 결과를 검사한다. 이는 일관성 검사이며, 피어 인증이 아니다. 퍼사드의 친구 삭제는 12바이트 계정 레코드와 0x23바이트 레코드의 두 번째 배열에 대해 동작하며, 로그인은 32개 항목을 초기화한다.
[S: `src/matched/DWC_CheckFriendKey.c:12`, `src/matched/DWC_Acc_CheckFriendKey.c:36`,
`src/matched/func_020eae80.c:30`, `src/matched/func_020ecba8.c:50`]

신뢰성 있는 DWC 전송은 요청된 크기와 바쁨 상태를 기록하고, 8바이트 전송 헤더를 내보낸 뒤, 설정된 분할 크기와 사용 가능한 GT2 공간으로 제한된 청크를 전송한다. 전송이 반드시 끝나기 전에 수락을 반환할 수 있으며, 전송 콜백이 완료를 표시한다. 일반적인 분할 상한은 1465이고, 게임은 256으로 설정한다.
[S: `src/matched/func_ov065_0227eda0.c:100`, `src/matched/func_ov065_0227eda0.c:122`,
`src/matched/func_ov065_0227ee90.c:96`, `src/matched/func_ov065_0227ecd0.c:129`,
`src/matched/func_020ec980.c:75`]

정확한 NAS-to-GPCM/GPSP-to-NatNeg-to-GT2 콜백 체인은 일부가 여전히 미해결이다. 보존된 그래프는 직접 연결과 해결되지 않은 별칭을 기록하지만, GameSpy 라이브러리가 존재한다는 사실을 이 게임에서 입증된 순서로 바꾸지는 않는다.
[E: `scratchpad/wifi-analysis-1/stage1-evidence.json`]

### 게임 엔벨로프, 디스패치 및 벌크 데이터

공통 수신 핸들러 `func_02075050`은 엔벨로프 바이트 하나를 읽는다. 비트 0..1은 2비트 상태 값이고, 비트 7은 제어 디스패치를 선택하며, 비트 2..6은 5비트 메시지 ID를 담는다. 24 미만의 ID는 엔벨로프를 제거하고 길이를 1 줄인 뒤 `func_02075240`을 거친다. 별도의 벌크 데이터 경로는 큐를 갱신하고 0x1000바이트 수신 버퍼를 등록한다. 두 상태 비트의 의미는 여기서 이름 붙이지 않았다.
[S: `src/matched/func_02075050.c:33`, `src/matched/func_02077b14.c:6`,
`src/matched/func_02077b20.c:6`, `src/matched/func_02077b28.c:5`,
`src/matched/func_02075240.c:7`]

송신자 `func_02075ff8`은 벌크 데이터를 최대 0xffb 데이터 바이트 단위로 나누고, 엔벨로프 바이트 1개와 4바이트 오프셋을 더해 최대 0x1000바이트를 만든다. 1바이트 청크 카운터는 큐가 청크를 수락할 때만 증가한다. 이는 WM 프레임 및 DWC의 256바이트 분할 설정과 별개인 게임 수준의 청크 분할 규칙이다.
[S: `src/matched/func_02075ff8.c:42`, `src/matched/func_02075ff8.c:55`]

아래의 디스패치 ID는 설정 포인터 재배치 **메타데이터**에서 도출하고, 각 매칭된 핸들러와 대조했다. 이는 원래 메시지 이름이 아니라 동작을 설명한다. 근거 기록에는 소스 또는 페이로드 데이터 없이 출처와 도출 과정이 보존되어 있다.
[S: `src/matched/func_02075240.c:5`] [E: `scratchpad/wifi-analysis-1/stage1-evidence.json`]

| ID | 핸들러 | 발명한 프로토콜 이름이 아닌 확립된 동작 |
|---|---|---|
| 0 | `0x020756cc` | 모드 12: 참가자 하위 니블 비트맵과 상위 비트 2개를 소비한다. [S: `src/matched/func_020756cc.c:10`] |
| 1 | `0x02075670` | 모드 12: 오프셋이 앞에 붙은 데이터를 벌크 대상에 복사한다. 완료 임계값은 기본적으로 0x17400이거나 계산된 압축 길이 +4이다. [S: `src/matched/func_02075670.c:22`] |
| 2 | `0x0207560c` | 오프셋이 앞에 붙은 데이터를 참가자별 레코드에 복사한다. 빈 본문은 리셋 경로를 선택한다. [S: `src/matched/func_0207560c.c:12`] |
| 3 | `0x020755b4` | 1바이트 리셋 대안이며, 그렇지 않으면 레코드 인덱스 4에 0x950바이트를 복사한다. [S: `src/matched/func_020755b4.c:18`] |
| 4 | `0x0207557c` | 오프셋이 앞에 붙은 데이터를 레코드 인덱스 `sender + 3`을 거쳐 복사한다. [S: `src/matched/func_0207557c.c:15`] |
| 5 | `0x0207556c` | 1바이트와 송신자 인덱스를 `0x020a6f74`로 전달한다. [S: `src/matched/func_0207556c.c:7`] |
| 6 | `0x02075548` | 1바이트를 하위 3비트 값과 상위 니블 값으로 나눈다. [S: `src/matched/func_02075548.c:8`] |
| 7 | `0x0207553c` | `0x020a6cd4(1)`을 요청한다. [S: `src/matched/func_0207553c.c:7`] |
| 8 | `0x02075514` | 현재 값이 3일 때만 통신 하위 상태를 변경한다. [S: `src/matched/func_02075514.c:9`] |
| 9 | `0x020754e8` | 모드 13/47에서 `0x020a125c`를 통해 트랜잭션 플래그를 설정한다. [S: `src/matched/func_020754e8.c:9`] |
| 10 | `0x020754b0` | 모드 12: 8바이트 전송과 완료 플래그이다. 이 재구성에서 복사 방향은 shadow/레지스터 흐름 감사를 필요로 한다. [S: `src/matched/func_020754b0.c:24`] |
| 11 | `0x02075484` | 모드 13/47: `0x020a1274`를 통한 트랜잭션 플래그이다. [S: `src/matched/func_02075484.c:14`] |
| 12 | `0x02075450` | 오프셋이 앞에 붙은 데이터를 통신 객체의 버퍼에 복사한다. [S: `src/matched/func_02075450.c:13`] |
| 13 | `0x02075448` | 테일 콜 대상은 매칭된 파일에서 여전히 이름이 없다. [S: `src/matched/func_02075448.c:8`] |
| 14 | `0x02075404` | 모드 46/9: 호스트/게스트 슬롯을 재매핑하며 송신자별 바이트를 전달한다. [S: `src/matched/func_02075404.c:10`] |
| 15 | `0x020753a8` | 2바이트 레코드 4개를 디코드하고 `0x020a7394`를 통해 적용한다. 액터 필드의 의미는 아직 확립되지 않았다. [S: `src/matched/func_020753a8.c:18`] |
| 16 | `0x02075380` | 모드 46: `0x020a1200`을 통한 송신자 플래그이다. [S: `src/matched/func_02075380.c:14`] |
| 17 | `0x02075358` | 모드 46: `0x020a11f8`을 통한 송신자 플래그이다. [S: `src/matched/func_02075358.c:14`] |
| 18 | `0x02075334` | 모드 46: `0x020a126c`를 통한 플래그이다. [S: `src/matched/func_02075334.c:14`] |
| 19 | `0x0207530c` | 모드 46: `0x020a1208`을 통한 송신자 플래그이다. [S: `src/matched/func_0207530c.c:9`] |
| 20 | `0x02075300` | 송신자와 길이를 `0x020a11e0`으로 전달한다. [S: `src/matched/func_02075300.c:7`] |
| 21 | `0x020752a8` | 모드 46: `0x020984e8`을 통한 오프셋이 앞에 붙은 복사이다. 대상 바인딩에는 별칭 감사가 필요하다. [S: `src/matched/func_020752a8.c:27`] |
| 22 | `0x02075278` | `0x020989e0`을 통한 오프셋이 앞에 붙은 복사이다. [S: `src/matched/func_02075278.c:13`] |
| 23 | `0x02075254` | 모드 46: `0x020a11b8`을 통한 완료 플래그이다. [S: `src/matched/func_02075254.c:9`] |

### 마을 상태, 동기화 및 롤백 한계

세이브/트랜잭션 헬퍼는 여러 단계의 작업 전에 `0x021dc7a8`에서 임시 버퍼로 0x173fc바이트를 복사하고, 이후 분기에서 이를 되돌려 복사한다. 이는 세이브 크기의 스테이징을 확립하지만, 모든 방문자가 압축되지 않은 세이브 뱅크를 받는다는 뜻은 **아니다**. 완전한 마을 전송 형식이라는 이름을 붙이려면 벌크 수신기의 0x17400 완료 크기와 압축 길이 대안을 이 스테이징 경로와 연결해야 한다.
[S: `src/matched/func_020a03e0.c:63`, `src/matched/func_020a03e0.c:113`,
`src/matched/func_02075670.c:31`]

통신 갱신은 참가자 인덱스 0..3을 순회하며 원격 전송 디스크립터 3개를 만든다. 수락된 전송 뒤에 큐 인덱스를 진행시키고, 예상 참가자 비트맵이나 연결 검사가 실패하면 상태 비트를 설정한다. 이는 4슬롯의 승인된 버퍼 설계를 입증하지만, 결정론적 입력 록스텝, 액터 좌표 표현, 정확한 갱신 빈도, 공유 게임플레이 RNG를 입증하지는 않는다.
[S: `src/matched/func_02074330.c:169`, `src/matched/func_02074330.c:213`,
`src/matched/func_02074330.c:370`]

`func_020a2dec`은 반복되는 실패 가드와 명시적인 배리어 플래그를 사용한다. 상태 14/15는 처리 중인 참가자 작업과 완료를 기다리고, ID 17/19를 전송하며, 연결 해제를 기다리는 상태로 진행한다. `0x020a0848`의 최종/오류 헬퍼는 매칭되지 않았다. 따라서 피어를 잃은 뒤의 정확한 영속 결과는 여전히 열려 있다.
[S: `src/matched/func_020a2dec.c:146`, `src/matched/func_020a2dec.c:168`,
`src/matched/func_02075918.c:24`, `src/matched/func_02075848.c:22`]

## 어디에 있는가

| 계층 | 우선 확인할 소스 / 질문 |
|---|---|
| 게이트 스캔 선택 | `func_ov048_02260d28`; 해당 상태 5를 캡처한 메뉴 전이와 연결한다. [S: `src/matched/func_ov048_02260d28.c:75`] |
| 모드 선택기 | 매칭되지 않은 `main:0x02074b44`; 완전한 게이트 상태 그래프를 주장하기 전에 진입 브리지가 필요하다. [E: `scratchpad/wifi-analysis-1/stage1-evidence.json`] |
| 공통 수신 디스패치 | `func_02075050` -> `func_02075240`. [S: `src/matched/func_02075050.c:36`] |
| 로컬 전송 | `ov066:0x0226ae50` -> WM 포트 전송; `0x0226b9b8`에서 콜백을 연결한다. [S: `src/matched/func_ov066_0226ae50.c:9`, `src/matched/func_ov066_0226b9b8.c:101`] [E: `scratchpad/wifi-analysis-1/stage1-evidence.json`] |
| 온라인 전송 | 신뢰성 있는 송신자 `ov065:0x0227eda0`; 연결 준비/공간 조건자 `0x0227ee90`. [S: `src/matched/func_ov065_0227eda0.c:100`, `src/matched/func_ov065_0227ee90.c:96`] |

## 읽고 쓰는 데이터

모드 바이트는 `0x021fbef8`, 온라인 상태 하프워드는 `0x021fbefc`, 공통 통신 객체 포인터 슬롯은 `0x020ccf94`이며, 제어 디스패처는 `0x020ccff0`에서 인덱싱된다. 이는 DS 주소이며, 소스 별칭 수정은 근거 기록에 보존되어 있다.
[S: `src/matched/func_020ecce4.c:39`, `src/matched/func_020ec980.c:41`,
`src/matched/func_02074330.c:110`, `src/matched/func_02075240.c:5`]

## 확인 방법

`python -B scratchpad/wifi-analysis-1/source_index.py`와
`python -B scratchpad/wifi-analysis-1/reloc_graph.py`를 다시 실행한 다음, 스테이징된 보고서의 근거/게이트 스크립트를 실행한다. 첫 **런타임** 근거 기록은 오버레이 ID, 모드/상태 쓰기, WM API ID, 콜백 순서를 포함한 제한된 게이트 메뉴 추적이어야 하며, 페이로드 덤프는 필요하지 않다. 소스 검토만으로는 그 근거 기록을 만들 수 없다.
[E: `scratchpad/wifi-analysis-1/stage1-evidence.json`]

## 가설

- 로컬 모드 1/2는 호스트/게스트를 뜻한다. 관련 없는 SDK의 숫자 모드를 번역해서 정하지 말고, 선택에서 `0x02074b44`로 이어지는 브리지를 추적해 확정한다. [S: `src/matched/func_020ecce4.c:55`]
- 벌크 ID 1/2/4/21/22는 마을 및 플레이어 하위 레코드를 다룬다. 정확한 필드 의미, 로스터 표현, 편지, 아이템 소유권, 채팅 직렬화는 여전히 미해결이다. 방문자 실행 전에 생산자/소비자 필드 순회와 합성 필드 변경으로 확정한다. [S: `src/matched/func_02075670.c:25`, `src/matched/func_0207557c.c:15`]
- 4슬롯 및 배리어 장치는 더 큰 파티를 지원하는 모드를 제한한다. WM의 max-entry만 높여서는 이 명시적 루프를 바꿀 수 없으며, 필요한 게임 변경 사항은 아직 빠짐없이 열거되지 않았다. [S: `src/matched/func_02074330.c:169`,
`src/matched/func_020760bc.c:37`]

## 관련 문서

- [네트워크 경계](network.md).
- [구현 선택지와 게이트](wifi-port-plan.md).
