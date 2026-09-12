# 시간 예산과 밀리초 시계를 사용하는 다른 곳들
<!-- source: wiki/engine/time-budgets.md -->

**읽을 때:** 프레임보다 세밀한 시계 모델을 평가하거나, 실제로 작업을 나누는 ROM 루프가 무엇인지 궁금할 때 읽는다.

**요약.** 정렬된 시계 변환 리터럴 32개가 작업 예산 32개를 뜻하지는 않는다. 네 지점이 채널 리스트 순회를 포함한 로더의 공통 40 ms 작업 분할 체인을 이룬다. 나머지는 시계 조회, 설정, 알람, 이벤트 조건, 지연, 네트워크 타임아웃을 구현한다. 더 세밀한 시계는 각각에 다르게 영향을 줄 수 있지만, 나열된 모든 함수를 다음 프레임으로 양보하게 하지는 않는다.

## 무슨 일이 일어나는가

독립적인 정렬 워드 스캔은 31개 함수에서 32개 지점을 발견했다. main 6, autoload_2 9, ov001 1, ov065 13, ov066 3으로 LOAD52와 일치한다. 32개 모두 소유 심볼 구간 안에 PC 상대 리터럴 로드가 있다. 목록은 입력/소스 SHA-256 해시, 주소, 로드 주소를 보존하며 추출 바이트나 디스어셈블리는 담지 않는다.
[H: `scratchpad/handoff/budget-family-1/inventory.json`; `scratchpad/handoff/budget-family-1/scan.py` ; provenance unresolved]

이는 리터럴 33514(0x82ea)의 목록이지 모든 가능한 예산이 이 표기를 쓴다는 증거는 아니다. 별도 함수의 변환, 다른 단위, 합성 상수, 정렬되지 않은 데이터는 탐지 범위 밖이다. 리터럴 하나를 여러 비교가 사용할 수 있고 HTTP 본체에는 별도의 리터럴 풀이 두 개 있다. [S: `scratchpad/handoff/budget-family-1/scan.py`;
`src/matched/func_ov065_02275b94.c`]

네 작업 예산은 항목/단계가 끝난 사이에 경과 밀리초가 엄격히 40보다 큰지 비교한다. 비용이 큰 말단 함수를 중간에 끊지는 못한다. 중첩 순회기는 전달받은 시작 타임스탬프를 공유하며, 재개 카운터 포인터가 없으면 예산 검사가 꺼진다. 완료되지 않은 핸들러 역시 디스패처 자체의 경과 시간 검사와 별개로 디스패처를 멈출 수 있다. [S: `src/matched/func_020b0b00.c`; `src/matched/func_020b0bbc.c`;
`src/matched/func_020b0ea8.c`; `src/matched/func_020b6c0c.cpp`]

## 어디에 있는가: 정렬된 모든 지점

각 행의 주소는 함수 진입점이 아니라 리터럴 풀 주소다. 소스 출처는 진입 주소와 의미를 제공하며, `inventory.json`은 모듈·심볼 구간·리터럴 로드 주소를 연결한다. 별도 표시가 없으면 임계값의 단위는 밀리초다. "없음"은 경과 작업 예산이 아니라는 뜻이다. 오프라인 설명은 측정된 로더와 정적으로 가능한 경로, 아직 입증되지 않은 호출자 도달 가능성을 구별한다. Wi-Fi 코드는 인터넷이 연결되지 않아도 실패한 연결 시도 중 진입할 수 있다. "일반 오프라인 플레이"는 그 기능을 시작하는 경우를 제외한다. [H: `scratchpad/handoff/budget-family-1/inventory.json`;
`scratchpad/handoff/budget-family-1/classification.json` ; provenance unresolved]

| 모듈 / 리터럴 지점 | 함수 / 정적 소스 | 분류 | 임계값 (ms) | 반복 또는 호출당 작업 | 다른 종료·완료 조건 | 오프라인 도달 |
|---|---|---|---|---|---|---|
| main `0x200131c` | `func_020012ec` [S: `src/matched/func_020012ec.c`] | 기타: 타임스탬프 | 없음 | 크래시 화면 루프 진입 전에 밀리초 저장 | 로컬 무한 루프에는 종료 없음 | 오프라인 오류 경로; 정상 플레이는 미확정 |
| main `0x208cb20` | `func_0208c978` [S: `src/matched/func_0208c978.c`] | 기타: 이벤트 조건 | <=1100 | 카운트다운을 줄이고 이전 틱 시각으로 이벤트 0x64 허용 판정 | 단일 갱신; 활성화, RTC 플래그, 카운트, 씬 검사가 분기 선택 | 오프라인 주민 갱신; 정적 경로, 새 실행 없음 |
| main `0x20b0bb8` | `func_020b0b00` [S: `src/matched/func_020b0b00.c`] | 로더 | >40 | data_020e41ec을 통해 타입이 있는 항목 하나 디스패치 | 항목 소진 또는 핸들러의 0 반환; 예산은 재개 포인터가 있을 때만 | LOAD52에서 오프라인 측정 |
| main `0x20b0c48` | `func_020b0bbc` [S: `src/matched/func_020b0bbc.c`] | 채널 리스트 / 로더 | >40 | func_0202f134로 하프워드 두 개짜리 채널 항목 하나 열기 | 항목 소진; 예산은 재개 포인터가 있을 때만 | 오프라인 로더 경로; 개별 본체 시간 미측정 |
| main `0x20b0f50` | `func_020b0ea8` [S: `src/matched/func_020b0ea8.c`] | 로더 | >40 | func_02003348로 위치가 있는 항목 하나 구성 | 항목 소진; 예산은 재개 포인터가 있을 때만 | 오프라인 로더 경로; 개별 본체 시간 미측정 |
| main `0x20b6d1c` | `func_020b6c0c` [S: `src/matched/func_020b6c0c.cpp`] | 로더 | >40 | 공통 시작 시각으로 현재 단계 핸들러 호출 | 상태가 1..6 밖, 마지막 단계 완료, 또는 핸들러 미완료 | LOAD52에서 오프라인 측정 |
| autoload_2 `0x20ec140` | `func_020ec040` [S: `src/matched/func_020ec040.c`] | 네트워크: 큐 감시 | > 설정 가능한 gLimit_0213e6b8 | 메시지 큐 확인과 시각 갱신/초기화; 만료 시 func_020ed9f4 호출 | 메시지가 없으면 1 반환; 비활성 매개변수는 시각 삭제 | autoload_2 네트워크 하위 시스템; 일반 오프라인 도달 미입증 |
| autoload_2 `0x20ec824` | `func_020ec5ac` [S: `src/matched/func_020ec5ac.c`] | 네트워크: 핸드셰이크 루프 | > 설정 가능한 g_bootTimeoutMs | 부팅/정리 상태 하나 진행, 네트워크 완료 확인 | 상태 7에서 완료; 훅·모드·상태·완료가 타임아웃 우회 | ov065로 네트워크 호출; 일반 오프라인 도달 미입증 |
| autoload_2 `0x20ec914` | `func_020ec848` [S: `src/matched/func_020ec848.c`] | 네트워크: 바쁜 대기 | > 설정 가능한 g_0213e6b8 | func_0226760c의 상태 2 폴링 | 상태 2에서 대기 종료; 타임아웃은 실패 반환, 후속 상태도 실패 가능 | ov065로 네트워크 호출; 일반 오프라인 도달 미입증 |
| autoload_2 `0x20ecefc` | `func_020ece54` [S: `src/matched/func_020ece54.c`] | 네트워크: 설정 | 없음; 입력 틱을 ms로 변환 | 설정된 타임아웃 저장, 큐/상태 초기화 | 단일 설정 호출; 시간 제한 루프 없음 | 네트워크 하위 시스템; 일반 오프라인 도달 미입증 |
| autoload_2 `0x20ecfe4` | `func_020ecf24` [S: `src/matched/func_020ecf24.c`] | 네트워크: 만료 조건 | >120000 | 네트워크 상태 확인 후 저장 시각 만료 처리 | 단일 갱신; 상태·상태값·시각 없음에 따라 조기 반환 | 네트워크 하위 시스템; 일반 오프라인 도달 미입증 |
| autoload_2 `0x20ed12c` | `func_020ed03c` [S: `src/matched/func_020ed03c.c`] | 네트워크: 주기 | 250 * g_divisor 주기, 예산 아님 | 시간 구간 선택, 피어 탐색, 항목 플래그/값 갱신 | 단일 갱신; threshold<5 또는 구간 불변이면 조기 반환 | ov065로 네트워크 호출; 일반 오프라인 도달 미입증 |
| autoload_2 `0x20ed650` | `func_020ed5f8` [S: `src/matched/func_020ed5f8.c`] | 네트워크: 타임스탬프 | 없음 | 두 인자가 모두 0일 때 현재 밀리초 저장 | 단일 콜백; 0이 아닌 인자는 조기 반환 | 네트워크 하위 시스템; 일반 오프라인 도달 미입증 |
| autoload_2 `0x210030c` | `func_020fff80` [S: `src/matched/func_020fff80.c`] | 기타: NVRAM 타임아웃 | >4000 | SPI NVRAM 명령/상태 진행, 바쁜 쓰기 재시도 | 읽기/쓰기 성공, 콜백 오류, 쓰기 허용 실패, 리셋 완료; 상태 비트 0x20도 리셋 선택 | 하드웨어/설정 경로는 오프라인 실행 가능; 정확한 게임플레이 호출자 미입증 |
| autoload_2 `0x21148c0` | `func_0211482c` [S: `src/matched/func_0211482c.c`] | 기타: 알람 변환 | 입력 msec; 경과 비교 없음 | 수면 알람 설치 후 콜백이 포인터를 지울 때까지 스레드 수면 | 알람 콜백이 로컬 스레드 포인터 삭제 | 범용 OS 수면은 오프라인 사용 가능; 특정 호출 발생 미측정 |
| ov001 `0x220b494` | `GetTickCount` [S: `src/matched/GetTickCount.c`] | 기타: 시계 조회 | 없음 | 틱 카운트를 밀리초로 변환해 반환 | 즉시 반환 | ov001 유틸리티; 호출자/오프라인 도달 미입증 |
| ov065 `0x2273b68` | `func_ov065_02273a8c` [S: `src/matched/func_ov065_02273a8c.c`] | 네트워크: 스캔 주기 | >=150 | 숨김 AP 목록/채널 진행, 스캔 재시작 | 발견 플래그로도 진행; 채널 소진 시 다음 단계 | ov065 Wi-Fi; 일반 오프라인 플레이 아님 |
| ov065 `0x2273c48` | `func_ov065_02273b8c` [S: `src/matched/func_ov065_02273b8c.c`] | 네트워크: 스캔 주기 | >=150 | 다른 채널 AP 목록 진행, 스캔 재시작 | 발견 플래그로도 진행; 목록 소진 시 다음 단계 | ov065 Wi-Fi; 일반 오프라인 플레이 아님 |
| ov065 `0x2273d28` | `func_ov065_02273cb4` [S: `src/matched/func_ov065_02273cb4.c`] | 네트워크: 스캔 주기 | >=300 | 스캔 채널을 2씩 증가 | 채널 >=13이면 다음 단계 | ov065 Wi-Fi; 일반 오프라인 플레이 아님 |
| ov065 `0x2275098` | `func_ov065_02274ea0` [S: `src/matched/func_ov065_02274ea0.c`] | 네트워크: 재시도 지연 | <5000 동안 대기 | 뮤텍스 아래 취소 확인, 인증 재시도 전 5000 수면 | 취소 시 반환; 지연 후 재시도; 외부 루프는 성공/오류/재시도 한도에서 종료 | ov065 Wi-Fi; 일반 오프라인 플레이 아님 |
| ov065 `0x2275f58` | `func_ov065_02275b94` [S: `src/matched/func_ov065_02275b94.c`] | 네트워크: HTTP 송신 타임아웃 | >timeout (기본 60000); >1000 시드 재설정 | 최대 700바이트 전송, 플러시, 요청 커서 진행 | 요청 소진, IP 없음, 쓰기 실패, 타임아웃, 취소 | ov065 Wi-Fi; 일반 오프라인 플레이 아님 |
| ov065 `0x2276078` | `func_ov065_02275b94` [S: `src/matched/func_ov065_02275b94.c`] | 네트워크: HTTP 수신 타임아웃 | >timeout (기본 60000); >1000 시드 재설정 | 수신 바이트 읽기/소비, 완료 경계 파싱 | 버퍼/내용 완료, 읽기 종료/오류, IP 없음, 타임아웃, 취소 | ov065 Wi-Fi; 일반 오프라인 플레이 아님 |
| ov065 `0x2278758` | `func_ov065_02278614` [S: `src/matched/func_ov065_02278614.c`] | 네트워크: 인증 타임아웃 | >10000 | 인증 결과 확인, 대기 요청 재시도 또는 타임아웃 보고 | 성공/상태 0이면 반환; 타임아웃은 로그인 중지 | ov065 Wi-Fi; 일반 오프라인 플레이 아님 |
| ov065 `0x2278b68` | `func_ov065_02278ac8` [S: `src/matched/func_ov065_02278ac8.c`] | 네트워크: 로그인 타임아웃 | >60000 | GP 로그인 진행, 연결 시각 확인 | 비활성/오류/상태 검사; 만료 시 로그인 중지와 플래그 해제 | ov065 Wi-Fi; 일반 오프라인 플레이 아님 |
| ov065 `0x22793d8` | `func_ov065_02279384` [S: `src/matched/func_ov065_02279384.c`] | 네트워크: 주기 | >=300 | 카운트 증가, func_02283cc0 호출, 시각 재기록 | 단일 갱신 후 반환; 임계값 미만은 작업 생략 | ov065 Wi-Fi; 일반 오프라인 플레이 아님 |
| ov065 `0x227e104` | `func_ov065_0227dd8c` [S: `src/matched/func_ov065_0227dd8c.c`] | 네트워크: 매칭 타이머 | >cmdTimeoutTime; >=3000+3000*n; >1000/3000/3000+3000*n | 매칭 진행, 예약 재전송, 서버 브라우저 갱신 | 상태/플래그/오류와 재시도 결과; 시간 제한 작업 리스트 중단이 아님 | ov065 Wi-Fi; 일반 오프라인 플레이 아님 |
| ov065 `0x227ebd4` | `func_ov065_0227eabc` [S: `src/matched/func_ov065_0227eabc.c`] | 네트워크: 피어 감시 | >피어별 recvTimeoutTime | 호스트 목록 순회; 가능한 분할 데이터 전송, 수신 타임아웃 통지와 시각 재기록 | 호스트 수만큼 순회 후 종료; 바쁨/버퍼/유효성 검사는 작업 생략; 타임아웃은 순회를 끊지 않음 | ov065 Wi-Fi; 일반 오프라인 플레이 아님 |
| ov065 `0x227efe4` | `func_ov065_0227efc4` [S: `src/matched/func_ov065_0227efc4.c`] | 네트워크: 시계 조회 | 없음 | 현재 밀리초 반환 | 즉시 반환 | ov065 Wi-Fi 유틸리티; 일반 오프라인 플레이 아님 |
| ov065 `0x22807b4` | `func_ov065_02280794` [S: `src/matched/func_ov065_02280794.c`] | 네트워크: 시계 조회 | 없음 | 현재 밀리초 반환 | 즉시 반환 | ov065 Wi-Fi 유틸리티; 일반 오프라인 플레이 아님 |
| ov066 `0x2267dac` | `func_ov066_02267cb0` [S: `src/matched/func_ov066_02267cb0.c`] | 기타: 알람 변환 | 입력 arg0 ms; 헬퍼는 500 ms 사용 | 슬롯 매니저 설정, 선택적으로 콜백 알람 설치 | 단일 설정; arg0이 0이면 자체 알람 생략 | ov066 통신/슬롯 하위 시스템; 오프라인 도달 미입증 |
| ov066 `0x226a3a8` | `func_ov066_0226a2e8` [S: `src/matched/func_ov066_0226a2e8.c`] | 기타: 알람 변환 | 입력 msec | 각 활성 슬롯의 타임아웃 알람 취소/재설정 | 슬롯 수 소진; 비활성 슬롯 생략 | ov066 통신/슬롯 하위 시스템; 오프라인 도달 미입증 |
| ov066 `0x226a7d0` | `func_ov066_0226a494` [S: `src/matched/func_ov066_0226a494.c`] | 기타: 알람 변환 | 입력 interval ms | 일치 MAC 항목 갱신 또는 빈 항목 할당 후 알람 설정 | 일치/빈 항목이면 성공 반환; 용량 소진 시 실패 | ov066 통신/슬롯 하위 시스템; 오프라인 도달 미입증 |

## 그룹과 예상되는 시계 민감도

| 그룹 | 구성원 | 프레임보다 세밀한 시계가 바꿀 수 있는 것 | 본체당 DS 프레임 |
|---|---|---|---|
| 로더 | main 로더 세 지점과 중첩 채널 리스트 지점 | 항목/단계 사이 시간 검사 만료 가능; 재개 카운터를 통해 여러 메인 루프 본체에 걸친 부분 작업 노출; 말단 중간 선점 없음 | LOAD52 문 단계 5 구간: 6.17; 로더 이전: 3.14. 퇴장 로더 본체: 23.60. 함수별 분리 측정 아님. [E/O: `scratchpad/handoff/budget-family-1/load52-summary.json`] |
| 채널 리스트 | 로더 네 개에 이미 포함된 `func_020b0bbc` | 같은 공통 40 ms 규칙; 호출 반환 시 리스트가 끝났다고 볼 수 없음 | 별도 측정 없음. [S: `src/matched/func_020b0bbc.c`] |
| 네트워크 | ov065 13개와 autoload_2 네트워크 7개 지점 전부 | 만료/재시도/주기 결정이 프레임 내에서 이동 가능; HTTP와 바쁜 대기는 경과 시간을 더 빨리 관측할 수 있음; 로더식 협력적 분할은 아님 | 미측정. [H: sources in table; `scratchpad/handoff/budget-family-1/classification.json` ; provenance unresolved] |
| 기타 | main 크래시/이벤트, ov001 조회, autoload_2 NVRAM/수면, ov066 알람 | 이벤트/기한 해상도 변경 가능; 조회기는 더 세밀한 값 반환; 역변환만으로 새 양보 지점은 생기지 않음. 알람 전달은 스케줄러/인터럽트 구현에도 의존 | 미측정. [H: sources in table; `scratchpad/handoff/budget-family-1/classification.json` ; provenance unresolved] |

이는 TICK53 측정이 아니라 제어 흐름에서 나온 예측이다. LOAD52의 과거 포트 관측은 고정된 산출물을 설명한다. 해당 본체 안에서 틱 시간이 흐르지 않으므로 단계 5는 표본 프레임 하나 안에서 완료된다. 이후 시계 구현의 동작을 입증하지는 않는다. [H: table source control flow; E:
`scratchpad/handoff/budget-family-1/load52-summary.json`]

원본 문의 단계 5는 오라클 프레임 57,268..57,305에 걸치며, 하위 항목 하나가 15프레임을 차지한다. 퇴장에는 33프레임과 62프레임(551, 1,036 ms)이 드는 말단 작업이 있다. 이는 40 ms 경계를 초과함을 보여 주며, 40 ms의 선점 상한을 뜻하지 않는다. LOAD52는 문의 단계 5에서 본체당 6.17프레임(103.1 ms), 그 이전에는 3.14프레임(52.5 ms)을 측정했으며 차이는 50.6 ms다.
[O: `scratchpad/handoff/budget-family-1/load52-summary.json`;
`scratchpad/handoff/budget-family-1/orig-door-walk.txt`; `scratchpad/handoff/budget-family-1/orig-exit-walk.txt`]

## LOAD52 교차 확인과 이전에 읽지 않았던 함수

LOAD52의 네 함수는 정확히 `func_020b6c0c`, `func_020b0b00`, `func_020b0ea8`, `func_020b0bbc`이며 리터럴 지점은 0x020b6d1c, 0x020b0bb8, 0x020b0f50, 0x020b0c48이다. 세 항목짜리 디스패처 표에는 `func_020b0c4c`도 있지만 이는 피호출자이지 다섯 번째 리터럴 적중이 아니다. [H: `scratchpad/handoff/budget-family-1/inventory.json`;
`scratchpad/handoff/budget-family-1/load52-summary.json` ; provenance unresolved]

`func_0208c978`은 로더가 아니라 매칭된 주민 주기 타이머다. 객체 +0xc8의 카운트다운을 줄이고 +0xb4가 활성화된 동안 RTC 시각을 검사하며, 한 카운트 분기에서는 +0xdc의 이전 틱 시각이 최대 0x44c(1100) ms 전일 때만 이벤트 0x64를 허용한다. 이어 시각을 다시 기록한다. 다른 분기에서는 0x258프레임 동안 비활성화하고 이벤트 0x65를 요청하거나 시각만 다시 기록한다. 씬 0x2e는 이벤트 요청을 억제한다. 이는 단일 갱신의 조건이며 경과 시간에 따른 루프 종료가 아니다.
[S: `src/matched/func_0208c978.c`, entry 0x0208c978, literal 0x0208cb20]

ov065 시계 조회기 두 개는 함수 경계가 복원돼 있다. 기존 소스 헤더는 피호출자 이름이 검증되지 않았다고 경고한다. 여기의 독립적인 직접 호출 디코딩은 둘 다 OS_GetTick(0x01ffa6b4)과 나눗셈(0x02136550)으로 해석하며 ov001 조회기와 일치한다. 이는 두 대상을 확정하는 것이지 표의 모든 복원된 포인터를 확정하는 것은 아니다.
[H: `scratchpad/handoff/budget-family-1/inventory.json`, direct_calls for 0x0227efc4 and 0x02280794 ; provenance unresolved]

## 읽고 쓰는 데이터

| 필드 / 주소 | 의미 | 쓰는 쪽 / 읽는 쪽과 근거 |
|---|---|---|
| `0x021f42dc`, `0x021f42e4` | 로더 재개 인덱스 / 하위 항목 카운터 | 단계 5가 항목 순회기에 전달; 작업 후 카운터 증가 [H/E: `scratchpad/handoff/budget-family-1/load52-summary.json` ; provenance unresolved] |
| 객체 `+0xdc` (64비트) | 이전 이벤트 타이머 틱 | `func_0208c978`이 읽고 다시 기록 [S: `src/matched/func_0208c978.c`] |
| `0x0213e6b8` | 설정된 네트워크 타임아웃(ms) | 설정 시 인자 틱을 변환; 감시기와 핸드셰이크가 읽음 [S: `src/matched/func_020ece54.c`; `src/matched/func_020ec040.c`; `src/matched/func_020ec5ac.c`; `src/matched/func_020ec848.c`] |
| 알람 간격 매개변수 | 밀리초를 틱으로 변환 | OS 수면과 ov066 알람 설정; 작업 예산 상태 아님 [S: `src/matched/func_0211482c.c`; `src/matched/func_ov066_0226a2e8.c`] |

## 확인 방법

보존된 유닛 워크트리에서 `python -B scratchpad/budget-family-1/scan.py <checkout-with-extract>`를 실행한다. 레포의 기존 타깃 로더를 사용해 추출된 모듈 파일을 제자리에서 읽으므로 프로비저닝, 컴파일러, 링크, 게임 실행은 필요하지 않다. 예상 결과는 32개 지점, 31개 함수이며 리터럴 로드 참조가 없는 지점은 없어야 한다. 다섯 모듈별 개수를 `scratchpad/budget-family-1/budget-sweep.txt`와 비교하고, 각 출현에 의미를 부여하기 전에 표에 나온 모든 매칭 본체를 검사한다.
[H: `scratchpad/handoff/budget-family-1/scan.py`; `scratchpad/handoff/budget-family-1/inventory.json` ; provenance unresolved]

## 가설과 한계

- 네트워크 래퍼, ov001, ov066 지점의 일반 오프라인 도달 가능성은 미입증이다. 오버레이 상주 여부를 포함해 명명된 오프라인 레시피의 호출자 추적을 얻으면 확정할 수 있다. 항상 로드된 모듈에 속한다는 사실은 실행의 증거가 아니다.
  [H: `scratchpad/handoff/budget-family-1/classification.json`]
- 여기서는 함수별 DS 시간을 측정하지 않았다. 모든 재개 경계를 계측해 LOAD52를 반복하면 채널 순회기의 시간과 다른 로더 말단의 시간을 구별할 수 있다.
  [H: `scratchpad/handoff/budget-family-1/load52-summary.json`]
- 매칭 소스의 이름/타입은 복원된 것일 수 있다. 해시는 검토한 파일을 고정할 뿐 모든 포인터 재배치나 의미상 이름의 증거가 아니다. 그래서 이 문서는 불확실한 작업을 호출/필드 주소로 설명한다. [H: `docs/rules/D-defects.md`, D9/D10/D12 ; provenance unresolved]

## 관련 문서

- [버스 타이밍](bus-timings.md) — 예산 안 작업의 비용: 영역별 버스 표, 카트리지 명령당 비용, 지오메트리 FIFO 깊이
- [씬과 채널](scenes-and-channels.md)
- [스레드와 인터럽트](threads-and-interrupts.md)
- [인터프리터 경로](interpreter-path.md)
