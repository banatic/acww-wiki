# 세이브 데이터
<!-- source: wiki/systems/save-data.md -->

**요약.** 놀러오세요 동물의 숲은 마을을 카트리지의 백업 저장소, 즉 DS의 ARM7 프로세서가
소유하고 게임의 ARM9 코드는 요청을 통해서만 접근할 수 있는 256 KB 플래시 칩에 보관한다.
게임은 그 칩 안에 각각 0x173fc바이트인 두 개의 세이브 뱅크를 두고 부팅 시 둘 중 하나를
선택한다. 플레이어가 하는 모든 것 -- 마을, 집, 주민, 편지 -- 이 거기에 있다; 기기 안의 다른
어떤 것도 전원이 꺼지면 살아남지 못한다. PC 포트는 플래시 자체를 호스트 파일로 공급하되,
요청했을 때에만 그렇게 한다.

## 무슨 일이 일어나는가

ARM9는 백업 칩을 결코 직접 건드리지 않는다. 명령 블록을 채우고, 프로세서 간 FIFO의 태그
11(`PXI_FIFO_TAG_FS`)에 요청 워드를 게시하고, 공유 카드 구조체의 `CARD_STAT_REQ` 비트를
설정한 뒤 호출 스레드를 재운다; ARM7이 전송을 수행하고 같은 태그로 응답하며, 그 응답이
비트를 해제하고 스레드를 깨운다
[S: `CARDi_Request`, card_common, `src/matched/CARDi_Request.c`].
`CARDi_OnFifoRecv`는 CARD 서브시스템이 기동 시 그 태그에 설치하는 ARM9 측 콜백이다
[S: `CARDi_OnFifoRecv` / `CARDi_InitCommon`, card_common,
`src/matched/CARDi_InitCommon.c`].

요청 워드는 작은 enum이며 그 멤버 중 셋이 세이브 경로의 전부다: `CARD_REQ_READ_BACKUP`은 6,
`CARD_REQ_WRITE_BACKUP`은 7, `CARD_REQ_VERIFY_BACKUP`은 9다
[S: `CARDRequest`, card_backup, `src/matched/CARDi_RequestStreamCommandCore.c`]. 전송 모드는 두
번째 enum -- RECV 0, SEND 1, SEND_VERIFY 2 -- 이며, 명령 블록의 `src`와 `dst` 워드 중 어느 것이
플래시 오프셋이고 어느 것이 스테이징 버퍼인지를 결정한다
[S: `CARDRequestMode`, card_backup, `src/matched/CARDi_RequestStreamCommandCore.c`].

어떤 전송도 256바이트 페이지 하나보다 크지 않다. `CARDi_RequestStreamCommandCore`는
호출자의 전체 요청을 페이지 크기 조각으로 자르고, 각 조각을 공유 카드 구조체 안의 256바이트
`backup_cache_page_buf`를 통해 옮기며, 그 전후로 데이터 캐시를 무효화하거나 플러시하고,
조각마다 하나의 `CARDi_Request`를 발행한다; 플래시 오프셋은 요청이 아니라 루프 안에서
누적된다 [S: `CARDi_RequestStreamCommandCore`, card_backup,
`src/matched/CARDi_RequestStreamCommandCore.c`]. SEND_VERIFY 모드에서는 각 쓰기 뒤에
*변경되지 않은* 명령 블록으로 요청 9를 이어 보내므로, 검증은 방금 쓴 것과 같은 페이지 버퍼를
같은 플래시 오프셋과 비교한다 [S: `CARDi_RequestStreamCommandCore`, card_backup,
`src/matched/CARDi_RequestStreamCommandCore.c`].

그 기계 장치로 들어가는 게임의 두 진입점은 짝을 이룬다. 비동기 읽기는 요청 타입 6과 모드
0(RECV)으로 스트림 명령을 호출한다
[S: `func_020509a8`, main, `src/matched/func_020509a8.c`]; 비동기 쓰기는 요청 타입 7, 재시도 횟수
10, 모드 2(SEND_VERIFY)로 호출한다 -- 그래서 게임이 쓰는 모든 세이브는 호출이 반환되기 전에
다시 읽혀 검사된다
[S: `func_02050a84`, main, `src/matched/func_02050a84.c`].

매체는 추측이 아니라 ROM에 명시되어 있다. `func_02050b78`은 리터럴 4610, 즉 0x1202를
식별-및-크기 짝에 넘기고, `CARDi_IdentifyBackupCore`는 그 패킹된 워드를 장치 클래스
2(FLASH)와 크기 시프트 0x12로 디코드한다. 즉 1 << 0x12 = 0x40000바이트 = 256 KB다
[S: `func_02050b78` / `func_02050b94`, main, `src/matched/func_02050b78.c`;
`CARDi_IdentifyBackupCore`, card_backup, `src/matched/CARDi_IdentifyBackupCore.c`]. 디코드는
테이블 조회가 아니라 계산이다: `CARDi_IdentifyBackupCore`는 디코드된 장치 클래스와 크기로
switch하여 여덟 개의 case 분기에서 열 필드짜리 `spec` 구조체(전체 크기, 섹터 크기, 페이지
크기, 주소 폭, 여섯 개의 타이밍 값)를 채운다
[S: `CARDi_IdentifyBackupCore`, card_backup, `src/matched/CARDi_IdentifyBackupCore.c`].

그 256 KB 안에 게임은 **0x173fc바이트(각 95,228)짜리 뱅크 두 개**를 둔다.
`func_020b5724`는 두 플래그 바이트를 보고 둘 중 하나를 고르고, 고정된 작업 주소에서 뱅크
하나 분량의 데이터를 복사하며, 같은 함수가 부팅이 택시 인트로로 갈지 기존 마을로 곧장
들어갈지를 결정하는 분기이기도 하다
[S: `func_020b5724`, main, `src/matched/func_020b5724.c`].

접근은 하나의 락으로 직렬화되며, 이는 용도별 락이 아니라 카트리지 전체에 대한 하나의 락이다:
`CARDi_LockResource`는 소유자 id와 NONE, ROM 또는 BACKUP의 대상 모드를 받으며, ROM 파일 읽기와
세이브 쓰기가 같은 `lock_owner`와 `lock_ref`를 놓고 경합한다
[S: `CARDi_LockResource`, card_common, `src/matched/CARDi_LockResource.c`]. 비동기 요청은 기동
시 생성된 전용 카드 스레드에 넘겨지며, 이 스레드는 `CARD_STAT_TASK` 비트를 기다린다
[S: `CARDi_TaskThread` / `CARDi_SetTask`, card_common,
`src/matched/CARDi_TaskThread.c`].

### 포트는 대신 무엇을 하는가

포트에는 ARM7이 없으므로 카드 프로토콜은 FIFO 수준이 아니라 요청 수준에서 응답된다:
`acww_card_arm7`이 명령 블록에 대해 작업을 수행하고, 응답에는 `err = TRUE`가 실리는데, 이는
ROM 자신의 `CARDi_OnFifoRecv`가 `CARD_STAT_REQ`를 해제하기 전에 검사하는 값이다
[E: `port/shim/fs/cardreq.c`, `port/shim/os/pxisend.c`;
`scratchpad/cycle40/runs/tap-D56`, frames 0..48000]. 작업은 **요청이 게시된 한 프레임 뒤, 전달
시점에** 일어나므로, 게시 직후의 폴링은 하드웨어에서처럼 여전히 BUSY를 본다; 동기적으로
응답했더니 부팅의 카드 읽기가 Nintendo 로고에서 영원히 재시작했다
[E: `docs/log/cycle40-keyboard-gate-probe.md` CARD40, `port/shim/os/pxisend.c`].

백업 저장소는 기본적으로 꺼져 있다. `ACWW_SAVE`가 설정되지 않으면 읽기는 대상 버퍼를
건드리지 않은 채로 둔다; `ACWW_SAVE=<path>`가 설정되면 포트는 그 파일을 256 KB 이미지로
메모리 매핑하고, 짧은 파일은 확장하며, 확장된 부분을 0xFF로 채운다. 지워진 플래시를 읽으면
그 값이 나오기 때문이다 [E: `port/shim/fs/cardreq.c`; `docs/kb/hybrid/hardware-services.md` section 1].
쓰기는 매핑에 복사되고 횟수가 세어지며, 검증은 페이지 버퍼를 매핑과 비교해 무조건 동의하는
대신 실제 불일치를 보고한다
[E: `port/shim/fs/cardreq.c`; `scratchpad/cycle40/runs/tap-D56`].

그 심(shim)의 두 상수가 기록할 만한 방식으로 틀려 있었는데, 두 실패 모두 조용했기 때문이다.
`CARD_STAT_INIT_CMD`로 적힌 상태 비트가 0x40, 즉 `CARD_STAT_CANCEL`로 쓰여 있어서 응답된
모든 요청이 취소 비트도 함께 올렸고, 정확히 그 비트를 먼저 검사하는
`CARDi_RequestStreamCommandCore`는 CARD_RESULT_CANCELED를 반환했다; 모든 세이브 읽기가
"세이브가 없다"가 아니라 "읽기가 실패했다"로 돌아왔다 [E: `port/shim/fs/cardreq.c`; the correct values are
`src/matched/CARD_CancelBackupAsync.c`'s INIT 1, INIT_CMD 2, BUSY 4, TASK 8, RECV 16, REQ 32,
CANCEL 64]. 그리고 읽기 요청 번호가 5로 쓰여 있었는데 게임은 6을 발행하므로, 0xFF 소거
채우기는 한 번도 실행되지 않았다 [E: `port/shim/fs/cardreq.c`, settled against
`src/matched/func_020509a8.c`].

**지워진 저장소는 0xFF이고, 0으로 채워진 저장소는 다른 게임이다.** 0 블록은 세이브의 부재가
아니다; 헤더와 체크섬이 0인 세이브이며, 게임은 이를 손상된 것으로 읽는다
[H: inferred from `func_020b5724`'s bank validity test; settled by running with `ACWW_SAVE`
pointed at an all-zero file and looking for the damaged-save path]. 읽기 채우기를 0xFF로
정정하자 키 입력 START 실행은 프레임 10 부근에서 `unimplemented: func_02225a90`에 멈췄다 —
포트의 정지 라인은 맨 주소를 인용하며, 심볼 테이블은 그 함수를
`func_ov003_02225a90`으로 명명한다 [S: `config/adm-kr/arm9/overlays/ov003/symbols.txt`] — 채우기를
끈 같은 빌드는 깨끗하게 실행되므로, 정직한 답은 부팅을 포트가 아직 따라갈 수 없는 경로로
옮긴다 [E: `port/shim/fs/cardreq.c`, keyed START, frame ~10].

## 어디에 있는가

| 함수 또는 심볼 | 모듈 | 역할 | 등급/출처 |
|---|---|---|---|
| `CARDi_Request` | autoload_2 (card_common) | PXI 태그 11에 요청 워드를 게시하고, `CARD_STAT_REQ`를 기다리며 잠들고, 타임아웃 시 재시도 | [S: `src/matched/CARDi_Request.c`] |
| `CARDi_RequestStreamCommand` | autoload_2 (card_backup) | 공개 진입점: src/dst/len/콜백을 저장하고, BUSY를 설정하고, 코어를 직접 실행하거나 태스크로 게시 | [S: `src/matched/CARDi_RequestStreamCommand.c`] |
| `CARDi_RequestStreamCommandCore` | autoload_2 (card_backup) | 256바이트 페이지 루프, 취소 검사, SEND_VERIFY 후속 처리 | [S: `src/matched/CARDi_RequestStreamCommandCore.c`] |
| `CARDi_IdentifyBackupCore` | autoload_2 (card_backup) | 패킹된 `CARDBackupType`을 열 필드 장치 spec으로 디코드 | [S: `src/matched/CARDi_IdentifyBackupCore.c`] |
| `CARD_GetBackupTotalSize` | autoload_2 (card_backup) | 디코드된 전체 크기를 반환 | [S: `src/matched/CARD_GetBackupTotalSize.c`] |
| `CARD_CancelBackupAsync` | autoload_2 (card_backup) | 인터럽트를 비활성화한 채 `CARD_STAT_CANCEL`을 올림 | [S: `src/matched/CARD_CancelBackupAsync.c`] |
| `CARDi_LockResource` | autoload_2 (card_common) | ROM과 BACKUP 모두에 대한 하나의 락, 소유자 id와 대상 모드로 | [S: `src/matched/CARDi_LockResource.c`] |
| `CARDi_TaskThread` / `CARDi_SetTask` | autoload_2 (card_common) | 전용 카드 스레드와 작업이 거기에 게시되는 방식 | [S: `src/matched/CARDi_TaskThread.c`] |
| `CARDi_OnFifoRecv` | autoload_2 (card_common) | `PXI_FIFO_TAG_FS`에 대한 ARM9의 응답 콜백 | [S: `src/matched/CARDi_OnFifoRecv.c`] |
| `CARD_GetResultCode` | autoload_2 (card_common) | 명령 블록의 `result` 워드를 반환 | [S: `src/matched/CARD_GetResultCode.c`] |
| `func_020509a8` | main | 게임의 비동기 백업 읽기 (타입 6, RECV) | [S: `src/matched/func_020509a8.c`] |
| `func_02050a84` | main | 게임의 비동기 백업 쓰기 (타입 7, 재시도 10, SEND_VERIFY) | [S: `src/matched/func_02050a84.c`] |
| `func_02050b78` / `func_02050b94` | main | FLASH 2 Mbit(0x1202)로 식별하고 전체 크기를 읽어 옴 | [S: `src/matched/func_02050b78.c`] |
| `func_020b5724` | main | 두 0x173fc바이트 뱅크 중 선택; 새 마을 / 기존 마을 분기 | [S: `src/matched/func_020b5724.c`] |
| `func_020a1a40`, `func_020b5898` | main | 읽기 상태 머신을 구동하는 부팅 시 폴러들 (3 = 아직 바쁨) | [S: `src/matched/func_020a1a40.c`, `src/matched/func_020b5898.c`] |
| `CARD_GetCurrentBackupType` | -- | **트리에서 잘못 식별됨**: 이 주소는 CARD 함수가 아니라 `DWC_Netcheck_GetReturnCode`다 | [S: header comment, `src/matched/CARD_GetCurrentBackupType.c`] |

## 읽고 쓰는 데이터

| 주소 또는 필드 | 의미 | 쓰는 쪽 | 읽는 쪽 |
|---|---|---|---|
| 명령 블록 `+0x00` `result` | 마지막 요청의 `CARDResult` | ARM7 (포트의 `acww_card_arm7`) | `CARD_GetResultCode` [S: `src/matched/CARD_GetResultCode.c`] |
| 명령 블록 `+0x10` `src` | 읽기에서는 플래시 오프셋; 쓰기에서는 페이지 버퍼 | `CARDi_RequestStreamCommandCore` | ARM7 [S: `src/matched/CARDi_RequestStreamCommandCore.c`] |
| 명령 블록 `+0x14` `dst` | 읽기에서는 페이지 버퍼; 쓰기에서는 플래시 오프셋 | `CARDi_RequestStreamCommandCore` | ARM7 [S: same] |
| 명령 블록 `+0x18` `len` | 이 요청이 옮기는 바이트 수, 256을 넘지 않음 | `CARDi_RequestStreamCommandCore` | ARM7 [S: same] |
| `spec` 하위 블록 | 전체 크기, 섹터 크기, 페이지 크기, 주소 폭, 여섯 개의 타이밍 | `CARDi_IdentifyBackupCore` | `CARD_GetBackupTotalSize`, `CARD_GetBackupPageSize` [S: `src/matched/CARDi_IdentifyBackupCore.c`] |
| `cardi_common.flag` | INIT 1, INIT_CMD 2, BUSY 4, TASK 8, RECV 16, REQ 32, CANCEL 64 | `CARDi_Request`, `CARD_CancelBackupAsync`, 응답 경로 | 코어 루프와 대기자들 [S: `src/matched/CARD_CancelBackupAsync.c`] |
| `cardi_common.backup_cache_page_buf` | 모든 전송이 거치는 256바이트 DMA 안전 스테이징 페이지 | `CARDi_RequestStreamCommandCore` | ARM7 [S: `src/matched/CARDi_RequestStreamCommandCore.c`] |
| 플래시 `0x00000`..`0x3ffff` | 256 KB 저장소; 0x173fc바이트 뱅크 두 개 | 요청 7에서 ARM7 | 요청 6에서 ARM7 [S: `src/matched/func_020b5724.c`, `src/matched/func_02050b78.c`] |
| `0x021dc7a8` | `func_020b5724`가 0x173fc바이트를 복사해 오는 작업 사본 | 게임 | `func_020b5724` [S: `src/matched/func_020b5724.c`] |

## 확인 방법

지금까지 측정된 어떤 레시피에서도 포트는 세이브를 쓰지 않으므로, 첫 번째 검사는 부정적이고
저렴하다: 마을 레시피(`../experiments/two-tap-town-recipe.md` 참고)를 `ACWW_SAVE`를 새 경로로
지정한 채 실행하고, 이후 파일이 여전히 256 KB의 0xFF이며 로그에 `acww card: request type 6`은
있지만 `acww save: persisted N bytes` 줄은 없음을 확인한다
[E: `port/shim/fs/cardreq.c`'s instruments; no such run is recorded yet, so this is the
experiment `../experiments/save-store-probe.md` describes].

## 가설

- 세이브 레코드는 체크섬을 갖지만 아직 발견된 것은 없다. `src/matched`의 모든 `crc`/`checksum`
  심볼은 무선, 소켓 또는 PPP/TCP 스택에 속하며(`MATH_CalcCRC8/16/32`,
  `MBi_calc_cksum`, `check_tcpudpsum`), 그중 어느 것에서도 `func_020509a8` / `func_02050a84`로
  이어지는 호출 간선이 없다 [S: absence in `src/matched`]. `func_020b5724`의 뱅크 유효성 검사를
  디스어셈블하여 그것이 뱅크에 대해 무엇을 계산하는지 명명함으로써 확정한다.
- 두 뱅크는 독립적인 두 슬롯이 아니라 주/백업 쌍이다. 포트가 세이브를 지속하게 만든 뒤(위
  참고), 게임 내 세이브 한 번 후와 두 번 후의 결과 파일에서 두 뱅크 범위를 diff하여 확정한다.
- 0xFF는 사용되지 않은 ACWW 세이브 영역을 읽었을 때의 값이며, 게임은 0xFF 소거 상태와 0
  상태를 구별한다. `ACWW_SAVE`를 모두 0xFF인 파일과 모두 0인 파일로 두고 같은 레시피를 두 번
  실행하여 각각이 타는 부팅 분기를 비교해 확정한다.
- 정직한 0xFF 읽기 뒤에 따라오는 `unimplemented: func_02225a90` 정지는 기존 세이브 로드
  경로이지, 채우기의 결함이 아니다. `ACWW_EXPLORE=1`로 실행하여 어느 호출자가 그 주소에
  도달하는지 읽어 확정한다 [E: `port/shim/fs/cardreq.c`, keyed START].

## 관련 문서

- `../experiments/save-store-probe.md` -- 위 검사들의 레시피 (아직 미실행).
- `../experiments/two-tap-town-recipe.md` -- 모든 세이브 관측이 이루어지는 실행.
- `time-and-rtc.md` -- 게임이 부팅 시 읽는 또 하나의 영속 상태.
