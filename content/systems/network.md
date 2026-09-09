# 네트워크
<!-- source: wiki/systems/network.md -->

**요약.** 놀러오세요 동물의 숲(Wild World)에는 완전히 별개인 두 개의 네트워킹 스택이 있다. 로컬
무선(같은 방에 있는 두 대의 DS 본체)은 무선 매니저와 그 연결 매니저에서 멈추며 IP 주소를 전혀
건드리지 않는다. 닌텐도 Wi-Fi 커넥션은 완전한 TCP/IP 스택, TLS, GameSpy의 매치메이킹 서버를
거치며, 이 모든 것이 하나의 오버레이 `ov065`에 담겨 있다. 그 서버가 제공하던 서비스는 2014년에
종료되었으므로, 두 번째 스택의 어떤 것도 출시 당시 그대로는 동작할 수 없다. PC 포트는 이 모든 것을
의도적으로, 완전히 스텁 처리한다. 무선을 끈 DS인 셈이다.

## 무슨 일이 일어나는가

### 두 개의 스택

로컬 무선은 `WCM*` 위의 `WM_*`이다. 무선 매니저는 무선 장치와 MAC 계층을 소유한다. 부모와 자식
역할(`WM_SetParentParameter`, `WM_StartConnectEx`), MP 데이터 포트(`WM_StartMPEx`,
`WM_SetMPDataToPortEx`, `WM_ReadMPData`), DCF 전송, 데이터 공유, 키 공유, 비콘 스캔, WEP를 담당한다
[S: 44 `WM_*` files, NitroWiFi, `src/matched/WM_Init.c` and siblings]. `WCM*`/`Wcm*`은 그 위에
있는 연결 매니저이며, `WCMi_CpsifRecvCallback`을 통해 IP 스택이 있을 때 그리로 연결하는 다리이기도
하다
[S: 21 files, libwcm, `src/matched/WCMi_CpsifRecvCallback.c`]. 순수 로컬 세션은 이 선 위의
어떤 것도 필요로 하지 않는다.

Wi-Fi 커넥션은 그 위에 세 개의 계층을 더 얹는다. `SOC*`/`SOCL*`은 libsoc으로, 자체 ARM7 명령 파이프를
가진 BSD 스타일 소켓 API다. `SOCL_Startup`, `SOCL_CreateSocket`, `SOCL_Bind`, `SOCL_Connect`,
`SOCL_ReadFrom`, `SOCL_WriteTo`에 DHCP 타임아웃 경로가 더해진다
[S: 77 files, libsoc, `src/matched/SOCL_Startup.c` and siblings]. `CPS*`/`CPSi_*`는 Ubiquitous
Corporation의 libcps와 libssl이다. 실제 TCP/IP와 ARP와 DHCP, 그리고 RC4, MD5, SHA-1과 키 교환용
빅넘 라이브러리를 갖춘 TLS다
[S: 42 files, `src/matched/CPS_TcpConnect.c`, `src/matched/CPSi_rc4_crypt.c`,
`src/matched/CPSi_sha1_calc.c`]. `DWC*`/`DWCi_*`는 그 위의 NitroDWC이다. 계정, 친구 코드, 매칭,
전송, 닌텐도 인증 호스트로의 HTTP POST를 담당한다
[S: 119 files, `src/matched/DWC_GetState.c` and siblings].

### ov065의 실체

`ov065`는 하나의 라이브러리가 아니다. 하나의 오버레이로 링크된 네 개의 외부 구성요소다. 닌텐도의
libsoc과 libwcm은 실제 C 소스로 제공되고, Ubiquitous의 libcps와 libssl 그리고 닌텐도의 libdwcac과
libdwcbase는 바이너리 전용 아카이브로 제공된다 [S: `docs/kb/modules/ov065.md`]. 이 오버레이는
약 `0x02269618`부터 약 `0x02292xxx`까지 차지하며, 그 안에서 `0x0227c038`부터 `0x022929f0`까지의
NitroDWC/GameSpy 블록(92,600바이트)은 경계가 없는 rodata와 코드였고, 여기서 706개의 함수 경계를
복구해야 했다 [S: `docs/kb/modules/ov065.md`]. 인증 블록(`dwc_auth.c`, `dwc_netcheck.c`)은
`0x02274798`..`0x02277000`에, 액세스 연결 블록은 `0x02272400`..`0x02273000`에, libdwcbase 본체는
`0x02277000`..`0x0227bxxx`에 있다
[S: `docs/kb/modules/ov065.md`].

GameSpy 리비전은 추측이 아니라 확정되어 있다. NitroDWC 0pr2에 번들된 GameSpy SDK 0.01로, 133개
함수가 바이트 단위로 그대로 일치했으며 DWARF 라인 테이블이 문장 단위로 맞아떨어진다
[S: `docs/kb/modules/ov065-dwc.md`]. 좁은 범위 `0x02269618`..`0x0226e434`(libcps/libssl의 함수
네 개)는 오버레이의 나머지(1.2/base)보다 나중의 CodeWarrior 드롭(1.2/sp2p3)으로 빌드되었는데, 이는
ROM이 어떻게 조립되었는지에 관한 사실이다
[S: `docs/kb/modules/ov065.md`].

바이너리 전용 오버레이가 이만큼이나 이해된 이유는 아카이브에 완전한 DWARF-2 디버그 정보가 함께
실려 있었기 때문이다. 508개 멤버 중 352개가 이를 담고 있어 구조체 레이아웃, 시그니처, 지역 변수별
레지스터 할당, 라인 테이블을 얻을 수 있다
[S: `docs/kb/modules/ov065.md`]. 그렇게 복구된 구체적인 상수로는 `WCM_PHASE_DCF == 9`,
`DWC_ERROR_FATAL == 8`, `DWC_MAX_PLAYER_NAME == 16`이 있고, `DWCMatchControl`의 친구 목록, 친구
인덱스 목록, 평가 콜백의 필드 오프셋도 있다 [S: `docs/kb/modules/ov065-dwc.md`].

### 친구 코드와 로그인 흐름

친구 코드는 `DWC_CheckFriendKey`와 `DWC_Acc_CheckFriendKey`를 통해 검증되고, 그것이 속한 계정
객체는 `DWCi_Acc_*` 접근자(플래그, 친구 키, 사용자 id, 더티 비트, 마스크 설정자)를 통해 도달한다
[S: `src/matched/DWC_CheckFriendKey.c`,
`src/matched/DWCi_Acc_GetFriendKey.c`]. 목록을 변경해도 되는지는 별도의 게이트
`DWC_CanChangeFriendList`가 결정한다 [S: `src/matched/DWC_CanChangeFriendList.c`]. 로그인 자체는
`gsbrcd`와 MAC 주소를 담아 `nas.nintendowifi.net/ac`에 `acctcreate` 또는 `login`을 POST하며, 요청에는
RTC에서 12자리로 포맷한 `devtime` 필드가 실린다
[S: `docs/kb/modules/ov065-dwc.md`; `func_ov065_02274798` (`DWC_Auth_Prepare_FirstPost`),
ov065, `src/matched/func_ov065_02274798.c`]. 그 함수는 시계 읽기가 실패하면 `DWCAUTH_E_RTCERR`를
반환하므로, 실시간 시계는 로그인의 필수 의존성이다
[S: `src/matched/func_ov065_02274798.c`].

`DWCi_*` 목록 중 놀랄 만큼 많은 부분이 프로토콜과 무관하다. `DWCi_KB*`, `DWCi_BTN*`, `DWCi_MOV*`,
`DWCi_FNT*`, `DWCi_IPT*`, `DWCi_OBJ*`, `DWCi_GX*`는 Wi-Fi 설정 및 연결 확인 UI의 화면 키보드, 버튼,
씬 위젯, 폰트, 입력 반복, OAM 연결 코드다 [S: `src/matched/DWCi_KBlGet.c`,
`src/matched/DWCi_BTNlEnable.c`,
`src/matched/DWCi_FNTlRenewBg.c`]. 모듈 노트가 산문으로 이름을 언급하는 핵심 연결 상태 함수들
(`DWC_ProcessInet`, `DWC_GetInetStatus`, `DWCi_TransportProcess`, `DWCi_MatchInit`,
`DWCi_Netcheck_Thread`)은 매칭되었지만 여전히 익명의 `func_ov065_*` 이름으로 정리되어 있다
[S: `docs/kb/modules/ov065-dwc.md`].

### 포트가 하는 일

아무것도 실행되지 않는다. `port/DESIGN.md` 4절이 정책을 밝힌다. 883개 진입점 중 164개(19%)가
무선(`WM`, `MB`, `AOSS`, `CPS`, `WXC`, `DWC`, GameSpy)이고, 닌텐도 WFC는 2014년에 종료되었으므로,
v1은 인터페이스 뒤에서 이들 모두에 "서비스 없음"으로 응답하고, 그 인터페이스를 명시된 모딩 대상으로
남겨둔다 [S: `port/DESIGN.md` section 4].

그럼에도 네 개의 작은 조각은 도달 가능하며, 각각은 스텁이 아니라 실제 응답이다.
`port/shim/net/dwcinit.c`는 설정 저장소 초기화 결과를 2비트 코드로 좁히는 `func_0210172c`를
대체하며, 항상 0(설정 유효, 지워진 것 없음)으로 응답한다
[E: `port/shim/net/dwcinit.c`]. `port/shim/net/dwcbackup.c`는 SSID, WEP 키, DHCP 설정을 담는
저장소인 `DWCi_BACKUPlInit`, `DWCi_BACKUPlRead`, `DWCi_BACKUPlWriteAll`을 구현한다. 읽기는 모두 0인
페이지를 반환하는데, 이는 한 번도 설정된 적 없는 공장 초기 상태의 본체이고, 쓰기는 수락된 뒤
버려진다 [E: `port/shim/net/dwcbackup.c`].
`port/shim/tu_wcm_bits.c`는 어셈블리로만 존재하며 무선을 꺼도 부팅 경로에 있는 두 libwcm 함수
(`WcmCountBits`, 즉 popcount와 `func_ov065_0227029c`, 즉 선행 0 개수 세기)의 C 본체를 공급하는데,
호스트 컴파일러가 mwcc `asm` 본체를 빌드할 수 없기 때문이다 [E: `port/shim/tu_wcm_bits.c`]. 그리고
`port/shim/game/ov065thunks.c`는 *타이틀 메뉴*가 ov065의 로드된 이미지를 가리키는 잔존 vtable 슬롯을
통해 도달하는 세 함수에 응답한다. 셋 모두 포트의 스텁 처리된 무선이 결코 채우지 않는 전역 함수
포인터 슬롯을 검사하고 거절한다 [E: `port/shim/game/ov065thunks.c`].

이와 일관되게, 기록된 어떤 실행 로그에도 `DWC`나 `WM` 심볼은 나타나지 않는다. 유일하게 네트워크에
인접한 PXI 트래픽은 태그 10(WM)이며, 포트는 이를 한 번 이름을 밝히고 버린다
[E: `port/shim/os/pxisend.c`; `docs/kb/hybrid/hardware-services.md` section 1, "Other tags"].

## 어디에 있는가

| 함수 또는 심볼 | 모듈 | 역할 | 등급/출처 |
|---|---|---|---|
| `WM_Init`, `WM_Initialize`, `WM_Enable`, `WM_PowerOn` | NitroWiFi (ov065) | 무선 장치 기동과 전원 상태 | [S: `src/matched/WM_Init.c`] |
| `WM_SetParentParameter`, `WM_StartConnectEx`, `WM_Disconnect` | NitroWiFi | 로컬 무선의 부모 및 자식 역할 | [S: `src/matched/WM_StartConnectEx.c`] |
| `WM_StartMPEx`, `WM_SetMPDataToPortEx`, `WM_ReadMPData` | NitroWiFi | 로컬 플레이에 쓰이는 MP 데이터 포트 세션 | [S: `src/matched/WM_StartMPEx.c`] |
| `WM_StartScan`, `WM_MeasureChannel`, `WM_GetAllowedChannel` | NitroWiFi | 비콘 스캔과 규제상 허용 채널 집합 | [S: `src/matched/WM_StartScan.c`] |
| `WM_StartDataSharing`, `WM_StartKeySharing`, `WM_StartDCF` | NitroWiFi | 세 가지 브로드캐스트 세션 유형 | [S: `src/matched/WM_StartDataSharing.c`] |
| `WM_SetWEPKey`, `WM_SetGameInfo`, `WM_GetLinkLevel` | NitroWiFi | WEP, 비콘 페이로드, 신호 강도 | [S: `src/matched/WM_SetWEPKey.c`] |
| `WCM_BeginSearchAsync`, `WCM_SearchAsync`, `WcmSetPhase` | libwcm | 비동기 AP 검색과 페이즈 상태 머신 | [S: `src/matched/WCM_BeginSearchAsync.c`] |
| `WCMi_CpsifRecvCallback` | libwcm | libwcm에서 libcps로 올라가는 다리 | [S: `src/matched/WCMi_CpsifRecvCallback.c`] |
| `WcmCountBits`, `WcmNotify`, `WcmWmReset` | libwcm | popcount, 이벤트 알림, `WM_*` 리셋 연결 코드 | [S: `src/matched/WcmCountBits.c`] |
| `SOCL_Startup`, `SOCL_CreateSocket`, `SOCL_Bind`, `SOCL_Connect` | libsoc | 소켓 API | [S: `src/matched/SOCL_Startup.c`] |
| `SOCLi_ExecCommandPacket`, `SOCLi_SendCommandPacket`, `SOCLi_DhcpTimeout` | libsoc | ARM7 명령 파이프와 DHCP 타임아웃 | [S: `src/matched/SOCLi_ExecCommandPacket.c`] |
| `CPS_TcpConnect`, `CPS_SocRead`, `CPS_SocWrite`, `CPS_SetUdpCallback` | libcps | 벤더 IP 스택 위의 TCP와 UDP | [S: `src/matched/CPS_TcpConnect.c`] |
| `CPSi_SslConnect`, `CPSi_SslRead`, `CPSi_SslWrite2` | libssl | TLS 세션 | [S: `src/matched/CPSi_SslConnect.c`] |
| `CPSi_rc4_crypt`, `CPSi_md5_calc`, `CPSi_sha1_calc`, `CPSi_big_add_part` | libssl | RC4, MD5, SHA-1과 빅넘 계층 | [S: `src/matched/CPSi_rc4_crypt.c`] |
| `DWC_GetState`, `DWC_GetLastError`, `DWC_GetMyAID`, `DWC_Alloc` | libdwcbase | 연결 상태, 오류, 연관 id, 힙 | [S: `src/matched/DWC_GetState.c`] |
| `DWC_CheckFriendKey`, `DWC_Acc_CheckFriendKey`, `DWC_CanChangeFriendList` | libdwcac | 친구 코드와 목록 변경 가능 게이트 | [S: `src/matched/DWC_CheckFriendKey.c`] |
| `DWCi_Acc_GetFlags`, `_GetFriendKey`, `_GetUserId`, `_IsDirty`, `_SetMaskBits` | libdwcac | 계정 객체의 접근자 | [S: `src/matched/DWCi_Acc_GetFriendKey.c`] |
| `func_ov065_02274798` (`DWC_Auth_Prepare_FirstPost`) | ov065 | RTC에서 얻은 `devtime`을 포함해 WFC 인증 POST를 구성 | [S: `src/matched/func_ov065_02274798.c`] |
| `DWCi_BACKUPlInit` / `_Read` / `_WriteAll` | libdwcac | 무선 설정 백업 저장소 | [S: `src/matched/DWC_BACKUPlCheckSsid.c`] [E: replaced by `port/shim/net/dwcbackup.c`] |
| `DWCi_SNDlPlay`, `_Stop`, `_SetVolume`, `_SetPitch` | libdwcac | 네트워크 UI가 사운드 플레이어로 들어가는 훅 | [S: `src/matched/DWCi_SNDlPlay.c`] |
| `func_0210172c` | autoload_2 | 설정 저장소 초기화 결과를 좁힘; 포트는 0으로 응답 | [E: `port/shim/net/dwcinit.c`] |

## 읽고 쓰는 데이터

| 주소 또는 필드 | 의미 | 쓰는 쪽 | 읽는 쪽 |
|---|---|---|---|
| PXI 태그 10 | ARM7으로 가는 WM 채널 | ARM9 무선 매니저 | ARM7 (포트는 태그 이름을 한 번 밝히고 버린다) [E: `port/shim/os/pxisend.c`] |
| `DWCMatchControl.friendList` / `.friendIdxList` / `.evalCallback` | 세션이 실행되는 근거인 매치메이킹 상태 | `DWCi_MatchInit` | 매칭 계층 [S: `docs/kb/modules/ov065-dwc.md`] |
| `DWCLoginControl` 사용자 id / 비밀번호 / 연결 플래그 / 인증 토큰 | POST가 담는 계정 자격 증명 | 인증 스레드 | `DWC_Auth_Prepare_FirstPost` [S: `docs/kb/modules/ov065-dwc.md`] |
| DWC 백업 페이지 | SSID, WEP 키, DHCP 설정, CRC-16으로 검증됨 | `DWCi_BACKUPlWriteAll` (포트: 버림) | `DWCi_BACKUPlRead` (포트: 모두 0) [E: `port/shim/net/dwcbackup.c`] |
| `DWC_BM` 4페이지 맵 | `DWC_BM_Init`이 `MATH_CalcCRC16`으로 검증하고 복구하는 설정 저장소 | `DWC_BM_Init` | 설정 UI [S: `src/matched/func_02100830.c`] |

## 확인 방법

실행할 것은 없다. 의미 있는 검사는 부정적 검사이며 이미 모든 마을 실행의 일부다. 로그에서
`acww pxi: tag a`(WM)와 `unimplemented:` 줄에 나오는 `DWC`/`WM` 심볼을 grep한다.
`scratchpad/cycle40/runs/tap-D56`의 59,808줄 로그에는 둘 다 나타나지 않는다
[E: `scratchpad/cycle40/runs/tap-D56`, 48,000 frames]. 만약 언젠가 나타난다면, 게임이 네트워크
경로에 도달한 것이며 이 페이지는 더 이상 서술적이지 않게 된다.

## 가설

- 로컬 무선(`WM_*`/`WCM*`만, IP 없음)은 되살릴 수 있는 쪽 절반이다. 더 이상 존재하지 않는 서버가
  필요 없기 때문이다. 게임 자체의 "근처 친구 방문" 경로가 44개 `WM_*` 진입점 중 실제로 어느 것을
  호출하는지 추적하면 해결되는데, 그러려면 그 메뉴에 도달해야 하고, 아직 어떤 레시피도 그러지
  못한다.
- 타이틀 메뉴가 도달하는 `ov065thunks.c`의 세 함수는 부팅 경로에 있는 유일한 네트워크 인접 코드다.
  근거: 48,000프레임 동안 다른 ov065 심볼은 하나도 이름이 나오지 않았다
  [E: `scratchpad/cycle40/runs/tap-D56`]. 전체 실행에 걸쳐 ov065의 주소 범위에 대한 `ACWW_WATCH`
  스윕으로 해결된다.
- `func_0210172c`의 실제 응답이 중요하다. 포트는 항상 "설정 유효, 지워진 것 없음"이라 답한다.
  다른 응답이라면 게임을 설정 삭제 경로로 보낼 것이다. 심(shim)의 반환값을 뒤집고 부팅을 비교하면
  해결된다.
- `devtime` 의존성은, 여전히 로그인할 수 있는 ACWW라 해도 포트의 고정된 2005년 시계 아래에서는
  로그인을 거부할 것임을 뜻한다 [S: `func_ov065_02274798` returns `DWCAUTH_E_RTCERR` on a failed read,
  and the port's read succeeds -- so the failure would be server-side, not clock-side].

## 관련 문서

- `time-and-rtc.md` -- 인증 POST가 담는 시계.
- `rng.md` -- 확립된 소비자가 여기에만 있는 SDK 생성기.
- `../experiments/off-recipe.md` -- 위의 부정적 검사를 읽어내는 실행.
