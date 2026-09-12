# Wi-Fi G0: 문지기 경로와 첫 WM 요청
<!-- source: wiki/systems/wifi-g0.md -->

**요약.** 문지기 메뉴의 행 0은 방문, 행 1은 초대를 선택한다. 아래의 초기 wifi-g0-1 추적은 요청을 제출하지 않았다. wifi-g0-2는 WM_Init 앞에서 펌웨어 접두부가 0인지 검사하는 조건을 찾아, 기본으로 꺼진 진단 스위치 아래에서만 그 하프워드를 제공한다. 이제 경로별 두 실행은 정확히 하나의 WM_Enable 요청(API 3)을 제출한다. 방문은 600프레임 뒤 정리되며 초대는 프레임 18000까지 열린 채 남는다. ARM7 요청은 완료되지 않고 스캔이나 피어도 없다.

## 무슨 일이 일어나는가

소유자의 답변으로 작업 설명의 위치를 문지기 건물 `0x500b`로 정정했다. 기존 내비게이터의 `gate` 목표는 비공개 LIVE46 세이브에서 재현했다.
[H: `docs/log/cycle41-gameplay.md:2922`] [E: `scratchpad/wifi-g0-1/revision2/goto-gate.receipt.json`]

포트 프레임 7300의 공통 스냅샷에는 선택 행 다섯 개가 있다. 이전에 네 행으로 읽었던 것은 로컬 전체 정지 화면을 측정한 뒤 정정했다. 폐기된 메타데이터는 로컬에 보존하되 최종 내보내기에서는 제외했다.
[E: `scratchpad/wifi-g0-1/revision2/safe/menu-common-final.json`]

행 0은 방문 대화, 행 1은 초대 대화로 이어지고, 뒤이어 전송 방식 세 행과 확인 두 행이 나온다. 두 추적 모두 전송 행 0과 확인 행 0을 선택한다. 이는 메시지 ID가 아니라 0부터 센 시각적 행 번호다. Whichline 후보는 오래된 것일 수 있으므로 로컬 정지 화면 해시와 짝지었다.
[E: `scratchpad/wifi-g0-1/revision2/safe/menu-guest-transport.json`, `scratchpad/wifi-g0-1/revision2/safe/menu-host-transport.json`, `scratchpad/wifi-g0-1/revision2/safe/menu-host-confirm.json`]

| 경로 | 반복 / 정지 | 최초 모드 표본 | ov066 로드 프레임 | 끝점 관측 |
|---|---|---|---|---|
| 행 0, 방문 / 게스트 의도 | 2 / 18000 | 12600에서 2 | 12581 | 검색 대화; 실제 WM 스캔은 미입증. |
| 행 1, 초대 / 호스트 의도 | 2 / 18000 | 13000에서 1 | 12953 | 문이 열린 모습; 실제 피어 대기는 미입증. |

두 경로는 각 실행 쌍 안에서 표본 스크린샷 36개, 모드 표본, 선택한 실행 합계, 오버레이 이벤트를 모두 재현한다. 전부 요청한 정지 기록과 빈 stderr를 남기며 종료 100이다.
[E: `scratchpad/wifi-g0-1/revision2/safe/comparison-residency.json`, `scratchpad/wifi-g0-1/revision2/runs/branch0-repeat1/receipt.json`, `scratchpad/wifi-g0-1/revision2/runs/branch1-repeat2/receipt.json`]

## 어디에 있는가

| 심볼 / 경계 | 모듈 | 관측과 한계 |
|---|---|---|
| `func_02074b44`, `0x02074b44` | main | 추적마다 인터프리터 95스텝과 호출 1회; 런타임 호출자 미상. |
| `CTRDG_WriteAgbFlashSectorAsync`, `0x020ed6c4` | autoload_2 | 스텝/호출 0회; 설정은 이 주소를 이렇게 명명하므로 확정된 무선 콜백 브리지라는 해석과 다름. |
| `WM_Init`, `0x02120990` | autoload_2 | 추적마다 인터프리터 호출 1회; 작업 버퍼 포인터는 0이 아님. |
| `WMi_SetCallbackTable`, `0x02120724` | autoload_2 | 이 구간에서 인터프리터 실행 없음. |
| `WMi_SendCommand`, `0x021205d0` | autoload_2 | 이 구간에서 인터프리터 실행 없음. |
| `PXI_SendWordByFifo`, tag 10 | 호스트 심 | 프로세스마다 한 번 켜짐, 제출 0회; 출력 상한 없음. |

합계는 게스트 2098행 또는 호스트 2191행에서 나왔으며 요청한 최대 32768보다 작고 7301..17900 구간이 완료됐다. 구간 개수는 런타임 호출 그래프가 아니며 프레임 구간은 인터프리터 4096스텝마다 확인한다.
[E: `scratchpad/wifi-g0-1/revision2/safe/branch0-repeat1.json`, `scratchpad/wifi-g0-1/revision2/safe/branch1-repeat1.json`]
[S: `config/adm-kr/arm9/autoload_2/symbols.txt:234`, `port/interp/interp_cpu.c:535`]

공통 스냅샷 이후에는 ov066(`0x022667e0..0x0226be20`)만 로드된다. 복원된 호스트 주소 해석기는 ID 2, 3, 4, 9, 15, 48, 65, 68, 147의 범위도 유지한다. 일부는 덮이지 않은 오래된 꼬리 영역이다. `FS_EndOverlay`가 아무것도 하지 않으므로 관리 기록만으로 나열된 모든 모듈이 논리적으로 계속 활성화돼 있거나 실행된다고 입증할 수 없다.
[E: `scratchpad/wifi-g0-1/revision2/safe/comparison-residency.json`]
[S: `port/shim/fs/ovlreloc.c:75`]

## 읽고 쓰는 데이터

| 필드 | 의미 / 관측 | 근거 |
|---|---|---|
| `0x021fbef8`, 바이트 | 행 0은 모드 0에서 2; 행 1은 0에서 1 | 7350..17950을 50마다 기록한 표본 213개의 완결된 장부. |
| `0x021fbefc`, 하프워드 | 온라인 상태 ID는 0 유지 | 같은 장부; 온라인 경로를 선택하지 않음. |
| `0x02206aac`, 포인터 | 끝점의 WM 작업 버퍼 주소 `0x022d7d20` | 허용 목록에 든 끝점 조회. |
| WM 작업 버퍼 +24 | 끝점에서 API 콜백 슬롯 0..13이 0 | 부분 표본이며 등록 이력은 아님. |
| 태그 10 요청 +0, 하프워드 | 요청 자체의 상태/소유권과 API ID | 합성 범위 픽스처; 실제 요청은 관측되지 않음. |

축약한 ID/개수/주소만 내보내며 원시 장부와 정지 화면은 로컬에 둔다. 오라클은 일관성을 미검증으로 표시하고 입력 후 VBlank 전에 표본을 읽으므로, 모드 전환 시점은 직전 50프레임 표본과의 사이로 한정된다.
[E: `scratchpad/wifi-g0-1/revision2/safe/branch0-repeat1.json`, `scratchpad/wifi-g0-1/revision2/safe/branch1-repeat1.json`]

`ACWW_WM_REQUEST_TRACE=1`은 첫 하프워드를 읽기 전에 정렬된 메인 RAM 포인터와 전체 256바이트 슬롯을 검사한다. FIFO 포인터 제출에는 독립적인 길이가 없으므로 요청 길이는 알 수 없다. OFF에는 서식화, 출력, 요청 역참조, 집계가 없지만 최초 환경 읽기와 캐시된 플래그 검사에는 여전히 CPU 시간이 든다. 오버헤드 벤치마크는 하지 않았다.
[S: `port/shim/os/pxisend.c:659`]
[E: `scratchpad/wifi-g0-1/revision2/trace-fixture-sealed/receipt.json`]

## 확인 방법

실행기의 정확한 기록을 사용한다. 인터프리터, card32, 프로세스별 비공개 시드 사본, 날짜 20260911/시간 113000, `RTC_FREEZE=0`으로 진행하는 결정론적 게임플레이 시계, 키 입력 부팅 단계 1160/1760이다. 상태/세이브의 절대 경로는 Python 환경을 통해 전달한다. 실행 파일 직접 진단은 정규 프런티어의 준비 상태를 주장하지 않는다.
[E: `scratchpad/wifi-g0-1/revision2/boot-observer.json`, `scratchpad/wifi-g0-1/revision2/runs/common-observer/receipt.json`]

프레임 3000부터 `plans/common-menu.pad`를 재생하고 7300에서 저장한 다음, `prepare_trace.py`와 `runner.py`로 `plans/branch0-trace.pad`, `plans/branch1-trace.pad`를 각각 두 번씩 18000까지 실행한다. `reduce_trace.py`, `finish_metadata.py`로 축약·비교하며 네이티브 실행 이름은 매번 새것이어야 한다.
[E: `scratchpad/wifi-g0-1/revision2/prepare_trace.py`, `scratchpad/wifi-g0-1/revision2/finish_metadata.py`]

최종 자체 워크트리의 새 링크는 빈 stderr와 dark194/256으로 종료 0이다. 정규 card32 OFF는 과거의 고정 RTC20050615/100000으로 31/31 EXACT를 통과한다. 이는 시계가 진행하는 이번 게임플레이 실행들과 별도 레시피다.
[E: `scratchpad/wifi-g0-1/revision2/link-observer-final.receipt.json`, `scratchpad/wifi-g0-1/revision2/offgate/offgate-check.json`]

## wifi-g0-2: 제출 전 조건

고정한 기준은 `27dc0df73a5739d7b1efcee0c31bd711bd752bb8`이다. main `0x02074b58`의 기준 WATCH_LR은 두 경로 모두 LR `0x02262651`을 기록한다. 실제 호출자는 코드상 main 호출자 `0x020a2d48`이 아니라 ov048 `func_ov048_02262618`이다. 인터프리터로 실행하는 로컬 초기화기 `0x0226748c`은 WM_Init 전에 `WM_IsExistAllowedChannel`이라는 판정을 호출한다. `0x02120d9c`의 로드는 하프워드 `0x027ffcf4`를 0으로 읽는다(게스트 12581, 호스트 12953). 이는 첫 MAC 접두부 하프워드이며 `WM_GetAllowedChannel`은 별도로 `0x027ffcfa`를 읽는다.
[S: `src/matched/func_ov066_0226748c.c`, `src/matched/WM_IsExistAllowedChannel.c`, `src/matched/WM_GetAllowedChannel.c`]
[E: `scratchpad/wifi-g0-2/baseline-analysis.json`, `scratchpad/wifi-g0-2/source-analysis.json`]

0 분기는 로컬 코드 `0x41`을 알리고 `0x022668c4`를 통해 등록된 해제 콜백을 호출한다. 다음 장치 할당이 드라이버 주소를 재사용하여 기준 컨텍스트와 장치가 모두 `0x022d7c44`다. 따라서 그 워드들은 유효한 드라이버 단계/상태가 아니라 장치 포인터다. 이후 WM_Init은 여전히 실행돼 포트 콜백 16개를 설치한다. `0x027fff8c`의 PXI 준비 상태는 이미 모두 1이며, WmInitCore는 태그 10 비트를 검사하고 요청 핸드셰이크 없이 성공을 반환한다. 태그당 한 번인 tag14 드롭은 응답도, 차단 요인의 증거도 아니다.
[S: `src/matched/func_ov066_022668c4.c`, `port/build/shadow/func_02077ae8.c`, `port/shim/os/heapfree.c`, `src/matched/WmInitCore.c`, `port/shim/os/pxi.c`]
[E: `scratchpad/wifi-g0-2/baseline-analysis.json`]

pxisend.c의 `ACWW_WM_STUB=1`은 인터프리터 필드가 0일 때만 합성 접두부 하프워드 2를 제공한다. 네이티브 실행, 기존의 0이 아닌 메타데이터, 나머지 MAC 바이트, 채널 마스크는 건드리지 않는다. 이는 유효한 무선 구현이나 실제 기기 신원이 아니라 진단용 부트스트랩 메타데이터다. OFF에는 메타데이터 읽기/쓰기가 없지만 캐시된 검사에는 여전히 CPU 시간이 든다. 메타데이터는 RAM 스냅샷 상태이고 스위치는 환경에서 유도된다. 네이티브 픽스처 네 조건은 OFF/미매핑, 활성 네이티브/미매핑, 0이 아닌 값 보존, 0 필드에 정확히 두 바이트 쓰기를 검사한다. 요청 핸들러, 수락 비트, 콜백은 추가하지 않는다.
[S: `port/shim/os/pxisend.c`]
[E: `scratchpad/wifi-g0-2/stub-fixture/receipt.json`]

## wifi-g0-2: 요청과 한정된 결과

| 경로 / 반복 | 첫 요청 | 완료가 없는 결과 |
|---|---|---|
| 방문 / 2 | 프레임 12581, API 3 | 600프레임 뒤 13181에서 정리/ov068 로드; 18000에도 오류 대화 유지. |
| 초대 / 2 | 프레임 12953, API 3 | 5047프레임 뒤 18000에도 문 열림 유지; 오류나 타임아웃 미입증. |

보충 방문 실행은 13500에서 정지하고 13400의 오류를 캡처한다. `whichline`은 렌더 영역에 문지기 아카이브 항목 86을 보고하며 로컬 오류 대화 정지 화면과 짝지었다. 아카이브 2의 항목 21도 거기 상주한다. 이는 입증된 활성 메시지 디스패치 ID가 아니라 BMG 순번 후보이며 렌더 사본은 오래된 것일 수 있다. 게임 문자열이나 그림은 내보내지 않는다.
[E: `scratchpad/wifi-g0-2/safe/error-dialogue.json`, `scratchpad/wifi-g0-2/runs/guest-detail/receipt.json`]

네 요청 모두 슬롯 `0x02206b40`, state16 `0x0003`(수락 비트 꺼짐), 용량 256바이트를 사용한다. WMi_SendCommand는 WM_Enable의 API 하프워드와 인자 워드 세 개, 즉 WM7, 상태, ARM7-to-ARM9 FIFO 주소를 쓴다. 헤더와 인자는 16바이트를 차지하지만 제출 길이는 아니다. PXI에는 길이가 없고 관측기는 올바르게 `request_length=unavailable`을 유지한다. `0x022d8280`의 상태 하프워드는 Enable 전에 WMi_CheckStateEx가 0으로 읽는다. 이는 ARM7 부트스트랩 포인터이며 MP 프레임 바이트나 릴레이 kind 1/2/3 페이로드가 아니다.
[S: `src/matched/WM_Enable.c`, `src/matched/WMi_SendCommand.c`, `src/matched/WMi_CheckStateEx.c`, `docs/kb/hybrid/online-spec.md`]

완료된 각 7301..17900 집계에는 WM_Enable, WMi_SetCallbackTable, WMi_SendCommand 호출이 각각 1회, WmReceiveFifo는 0회이며 행 수는 32768 미만이다. 18000의 최종 PXI 수신 집계는 tag11 전달만 보고하고 tag10/tag14는 없다. 각 쌍의 요청 줄, 선택한 집계 합계, 표본 BMP 해시 36개가 모두 같다. 두 경로 모두 빈 stderr, 명명된 런타임 오류 없이 요청한 18000에서 종료 100이다. 호스트 끝점 드라이버 단계/상태는 3/2이며 컨텍스트와 장치는 별도로 할당돼 있다. 콜백 슬롯 3은 `0x02266b94`를 가리킨다. 게스트 정리는 WM 작업 포인터를 지우고 ov066을 교체하므로 이전 전역 변수를 해석해서는 안 된다.
[E: `scratchpad/wifi-g0-2/safe/comparison.json`, `scratchpad/wifi-g0-2/safe/guest-stub-1.json`, `scratchpad/wifi-g0-2/safe/host-stub-1.json`]

소스만 읽은 WCM 경로는 별도다. 단계 1은 WM_Init을 호출하고 WM_GetAllowedChannel이 0이면 WM_Finish/반환 5로 거부한다. 그렇지 않으면 indication 콜백을 등록하고 WM_Enable을 호출한 뒤 단계 2에서 기다린다(단계 3은 준비됨). 이 헬퍼는 채널 마스크를 0으로 남기며 WCM/온라인 시작을 주장하지 않는다. 요청 수명·완료와 모든 스캔/MP/릴레이 통신은 G1 이후의 작업이다.
[S: `src/matched/func_ov065_0227197c.c`]

자체 워크트리의 새 링크는 종료 0, 빈 stderr, dark194/256이다. 스위치 미설정에서 정규 card32 OFF와 명시적 card0 기준 `2ea19722-dirty`는 각각 31/31 EXACT를 통과하고 기준 검사 두 개도 통과한다. 게임플레이는 비공개 LIVE46 사본과 진행하는 20260911/113000 시계를 사용하며 OFF는 과거의 고정 레시피를 쓴다. 경쟁 프로세스는 기록만 하고 건드리지 않으며 경과 시간은 비교 근거가 아니다. 직접 진단은 프런티어 산출물을 게시하지 않는다. 파이프라인이나 커밋은 실행하지 않았다.
[E: `scratchpad/wifi-g0-2/link-stub/receipt.json`, `scratchpad/wifi-g0-2/off-stub32-data/offgate-check.json`, `scratchpad/wifi-g0-2/off-stub0-data/offgate-check.json`]

## 관련 문서

- [네트워크 경계](network.md).
- [프로토콜 지도](multiplayer-protocol.md).
- [G0-G5 계획](wifi-port-plan.md).
- [런타임 안내](../../docs/kb/hybrid/wifi.md).
