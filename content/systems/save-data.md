# 세이브 데이터
<!-- source: wiki/systems/save-data.md -->

**요약.** 놀러오세요 동물의 숲은 마을을 카트리지의 백업 저장소, 즉 DS의 ARM7 프로세서가
소유하고 게임의 ARM9 코드는 요청을 통해서만 접근할 수 있는 256 KB 플래시 칩에 보관한다.
게임은 그 칩 안에 각각 0x173fc바이트인 두 개의 세이브 뱅크를 두고 부팅 시 둘 중 하나를
선택한다. 플레이어가 하는 모든 것 -- 마을, 집, 주민, 편지 -- 이 거기에 있다; 기기 안의 다른
어떤 것도 전원이 꺼지면 살아남지 못한다. PC 포트는 플래시 자체를 호스트 파일로 공급하되,
요청했을 때에만 그렇게 한다. **2026-09-10부터 게임은 그 경로를 통해 자신의 세이브를 쓰고,
두 번째 실행이 그것을 다시 읽어 들인다**: 그것을 막고 있던 것은 카드 프로토콜이 아니라
게임 스스로 해제하는 이사 모드 워드였다.

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

그 루프의 두 가지 세부 사항이 세이브에 걸리는 시간을 결정하며, 포트가 둘 다 재현해야 했기
때문에 둘 다 적어 둘 가치가 있다. 첫째, **루프는 페이지 사이에 아무것도 하지 않는다** --
양보도, 폴링도, 디스플레이 대기도 없다: 요청별 루틴을 직접 호출하고 곧바로 다시 돌기
때문에, 속도를 정하는 유일한 요소는 요청 하나가 응답받기까지 걸리는 시간이다
[S: `CARDi_RequestStreamCommandCore`, card_backup,
`src/matched/CARDi_RequestStreamCommandCore.c`]. 둘째, 그 응답은 스핀이 아니라 호출 스레드를
요청 비트에 대해 재우는 방식으로 기다리며, FIFO 응답이 그것을 깨운다
[S: `CARDi_Request`, card_common, `src/matched/CARDi_Request.c`; `CARDi_OnFifoRecv`,
card_common, `src/matched/CARDi_OnFifoRecv.c`]. 뱅크 하나는 744페이지이므로 실제 콘솔에서는
읽기가 1초도 안 되어 끝난다; 표시되는 프레임마다 한 페이지씩 응답하는 기기라면 거기에
12초 넘게 쓰게 된다.

*게임*이 지켜보는 바쁨 플래그는 다른 것이며, 전송 전체에 걸쳐 유지된다. 비동기 진입점이
페이지 루프에 넘기기 전에 그것을 잡고, 논블로킹 "아직 끝났나" 검사는 그 한 비트를 그대로
읽는 것이며, 마지막 페이지 뒤에야 태스크를 끝내고 대기 중인 모두를 깨우는 루틴이 그것을
해제한다
[S: `CARDi_RequestStreamCommand` / `CARDi_TryWaitAsync` / `CARDi_EndTask`, card_common and
card_backup, `src/matched/CARDi_RequestStreamCommand.c`, `src/matched/CARDi_TryWaitAsync.c`,
`src/matched/CARDi_RequestStreamCommandCore.c`]. 그러므로 "요청이 아직 응답받지 않았다"와
"전송이 아직 진행 중이다"는 서로 독립적인 두 사실이며, 게임이 읽기를 게시한 뒤 스스로
폴링하며 묻는 것은 두 번째 것뿐이다.

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

칩은 세 슬롯으로 나뉘며, 그 구분은 에디터의 것이 아니라 ROM 자신의 것이다: 백업 쓰기의
유일한 두 호출자인 `func_020a1cec`과 `func_020a1d94`는 슬롯 번호로 `data_020d1c20`에서
플래시 오프셋(OFFSET)을, `data_020d1bf0`에서 길이(LENGTH)를 인덱싱하고, 부팅 시 읽기 함수
`func_020a1a40`도 같은 짝을 읽는다. 슬롯 0은 오프셋 `0x00000` 길이 `0x173fc`, 슬롯 1은
`0x173fc` 길이 `0x173fc`, 슬롯 2는 `0x337fc` 길이 `0xc804` -- 두 뱅크와 편지 저장소다
[S: `func_020a1cec` / `func_020a1d94` literal pools, main; `func_020a1a40` as
`port/shim/game/savepoll.c` carries it].

두 쓰기 함수는 같은 연산이 아니며, 그중 하나만이 세이브다. `func_020a1cec(obj, slot)`은
작업 버퍼를 0xFF로 채운 뒤 쓰므로 슬롯을 소거(ERASE)한다; `func_020a48cc`는 그 일곱 상태
드라이버이며 슬롯 0 다음 슬롯 1을 소거한다 [S: `func_020a1cec`, `func_020a48cc`, main].
`func_020a1d94(obj, slot)`이 진짜 세이브다: 플래시 오프셋 `data_020d1c20[slot] + (chunk << 9)`에
같은 변위의 버퍼로부터 **한 스텝에 512바이트**를 쓰며, 청크 인덱스는 세이브 매니저 객체 안의
부호 있는 하프워드다 [S: `func_020a1d94`, main]. `func_020a2120(obj, arg)`은 그 **일곱 상태
드라이버**다: 상태 바이트는 `obj+0xa0`, 멤버 함수 포인터 테이블은 `0x021f3c84`(`0x021f3c2c`의
가드 워드 뒤에서 한 번만 채워짐), **상태 4가 `func_020a1d94`**이고, 상태 6이 머신을 0으로
리셋한다 [S: `func_020a2120`, main; `docs/log/cycle42-save.md` SAVE42].

### 실제 기기에서 256바이트 페이지 하나에 걸리는 시간

이것이 부팅의 744페이지 읽기의 속도를 고정하며, CARD46 이전까지 포트에서는 자릿수
수준의 추측일 뿐이었다.

백업 칩은 카트리지의 보조 SPI 포트에 달려 있으며, 그 제어 레지스터는 하위 두 비트로 네 가지
클록 중 하나를 선택한다: **0 = 4.19 MHz**, 1 = 2.10 MHz, 2 = 1.05 MHz,
3 = 524 kHz [P: GBATEK, [DS Cartridge Backup](https://problemkaputt.de/gbatek.htm#dscartridgebackup)
and [DS Cartridge I/O Ports](https://problemkaputt.de/gbatek.htm#dscartridgeioports), AUXSPICNT
bits 0-1]. SDK는 다른 어떤 것도 선택하지 않는다: `CARDi_EnableSpi`는 모든 명령마다 4 MHz
설정을 무조건 쓴다 [S: NitroSDK `libraries/card/common/src/card_spi.c`, present
locally under `tools/nitrosdk/` and not committed]. 그 클록에서 1바이트는 8비트, 즉
**1.908 us**다.

READ 경로의 페이지 하나는 256 데이터 바이트 이상이다. `CARDi_ReadBackupCore`는 주소 지정
명령을 **한 번** 보내고 -- 명령 바이트 1개에 256 KB 부품의 주소 바이트 3개 -- 그다음 요청된
길이 전체를 스트리밍한다; 256바이트 단위 분할은 ARM9 측의 `CARDi_RequestStreamCommandCore`에서
일어나므로 각 페이지는 자기 몫의 명령 비용을 치른다. 그 전에 같은 함수는
`CARDi_WaitPrevCommand`를 호출하는데, 이는 **2바이트 READ_STATUS**를 발행하고 장치가 바쁘다고
보고할 때에만 잠든다 -- 읽기에서는 결코 그런 일이 없다. 따라서 페이지 하나는 **262바이트
전송 = 약 500 us**이고, 16.717 ms 프레임 하나에 **~33개**가 들어간다 [S: `card_spi.c`
`CARDi_ReadBackupCore`, `CARDi_SendSpiAddressingCommand`, `CARDi_WaitPrevCommand`;
`src/matched/CARDi_RequestStreamCommandCore.c`].

**ARM7은 이 경로에서 자체 대기를 전혀 넣지 않는다.** 그 태스크 스레드는 요청을 실행하고,
확인 응답을 보내고, 루프를 돈다 [S: NitroSDK `libraries/card/ARM7/src/card_command.c`,
`CARDi_TaskThread`], 그리고 읽기 자체의 명령 꼬리는 강제 대기 0과 타임아웃 0을 넘긴다 --
`OS_Sleep` 분기는 읽기가 아니라 페이지 프로그램 경로에 속한다. 그러므로 프레임당 33페이지는
상한(CEILING)이며, ARM7의 바이트별 소프트웨어 루프(바이트마다 두 번의 바쁨 폴링, 간접 호출
하나, I/O 접근 하나)는 이를 낮출 수만 있지 결코 높이지 못한다.

포트는 이를 프레임당 페이지 예산 `ACWW_CARD_FAST` /
`CARD_FAST_HARDWARE = 32`로 모델링한다 [S: `port/shim/os/pxisend.c`; `docs/kb/hybrid/instruments.md` 3c].
그림으로는 정확한 수치를 확인할 수 없다: 10프레임 격자로 원본과 대조하면 부팅의 저작권
화면은 **8** 이상의 모든 예산에서 정확히 재현되고 8부터 64까지 동일하므로, 차분은 하한을
주고 위의 산술이 값을 준다
[E: `scratchpad/card46/copyright-table.json`, 10-frame grid; `docs/log/cycle42-save.md` CARD46].

### 게임이 수행하는 세이브

**측정됨, 2026-09-10 (SAVE43).** 이사가 끝나면 게임은 스스로 세이브하고 포트의 저장소가
그것을 받는다. 두 뱅크 모두 한 세션(ONE session)에 쓰인다: **플래시 오프셋 0부터 연속된
744개의 256바이트 카드 페이지**, 각각 **한 프레임 뒤에 검증**되며,
`0x00000000..0x0002e7f8`을 덮는다 -- **뱅크 1 먼저, 그다음 뱅크 2** -- 190,456바이트 영속,
검증 불일치 0, `FlushViewOfFile` 호출 745회 [E: `scratchpad/save43/RECEIPTS.md`, run `gp-S3`'s
census; `docs/kb/hybrid/save-flow.md` section 5b]. 카드 페이지 두 개가
`func_020a1d94`의 512바이트 스텝 하나이고, 검증은 `func_02050a84` 자신의 모드 2 SEND_VERIFY다
[S: those two functions]. 744 x 256 = 190,464 대 `0x2e7f8` = 190,456이며, 마지막 페이지가
252바이트 나머지다. **세이브 도중에 멈춘 실행은 뱅크 2를 소거된 채로 남긴다**(한 번 관측된
정지에서는 134페이지, 다른 정지에서는 501페이지) [E: same]. `0x337fc`의 편지 저장소(슬롯 2)는
소거된 채 남는다 -- 아직 우편이 없다 -- 그래서 그 쓰기 함수는 아직 실행된 적이 없다.

바이트들은 ROM 자신의 검사를 통과한다. 이후 그 파일에 `savetool.py check`를 돌리면: 뱅크 1
체크섬 저장값 `0xa6ad` 계산값 `0xa6ad`, 잔여 `0x0000`, 게임코드 ok, 플래그 `+0x173fa` ok,
워드 합 ok -- *게임은 이 뱅크를 로드(LOAD)할 것이다*; 뱅크 2도 같으며, 뱅크 1의 바이트 단위
동일 미러다 [E: `scratchpad/save43/savecheck-S3.txt`].

**그리고 두 번째 실행은 이어하기 경로를 탄다.** 같은 `ACWW_SAVE`로 스냅샷 없이 새로 실행하면
플레이어는 프레임 3,000-4,000에 자기 집 안에 있고 5,000부터는 HUD와 함께 자기 현관 앞에 서
있다 -- 택시도 없고 어느 키보드도 없다. 대조군은 소거된(ERASED) 저장소에서의 동일한 실행이며,
이는 빗속의 택시와 플레이어 이름 키보드를 준다 [E: `boot-A` vs `boot-C`,
`scratchpad/save43/png/boot-compare.png`]. 이어하기 경로는 자체적으로 8페이지(`0x2400`,
`0x198fc`, `0x2e5fc`, `0x2e6fc`에 2,040바이트)를 쓰며, 모두 검증된다
[E: `scratchpad/save43/RECEIPTS.md`].

**세이브를 막는(GATES) 것은 카드 경로가 전혀 아니며**, 그것을 찾는 데 두 사이클이 걸렸다:
세이브 프롬프트는 `0x021f3c30`의 이사 모드 워드가 1 또는 2인 동안 거부한다 -- 아래 가설과,
그것을 해제하는 체인에 대해서는 `../experiments/save-and-reload.md`를 보라.

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
채우기는 한 번도 실행되지 않았다 [H: host-source account from `port/shim/fs/cardreq.c`, settled against
`src/matched/func_020509a8.c`; verify with a retained scripted run and frame using this page's recipe].

**지워진 저장소는 0xFF이고, 0으로 채워진 저장소는 다른 게임이다.** 0 블록은 세이브의 부재가
아니다; 헤더와 체크섬이 0인 세이브이며, 게임은 이를 손상된 것으로 읽는다
[H: inferred from `func_020b5724`'s bank validity test; settled by running with `ACWW_SAVE`
pointed at an all-zero file and looking for the damaged-save path]. 읽기 채우기를 0xFF로
정정하자 키 입력 START 실행은 프레임 10 부근에서 `unimplemented: func_02225a90`에 멈췄다 —
포트의 정지 라인은 맨 주소를 인용하며, 심볼 테이블은 그 함수를
`func_ov003_02225a90`으로 명명한다 [S: `config/adm-kr/arm9/overlays/ov003/symbols.txt`] — 채우기를
끈 같은 빌드는 깨끗하게 실행되므로, 정직한 답은 부팅을 포트가 아직 따라갈 수 없는 경로로
옮긴다 [H: host-source account from `port/shim/fs/cardreq.c`, keyed START, frame ~10; verify with a retained scripted run and frame using this page's recipe].

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
| `func_020a1d94` / `func_020a2120` | main | 한 스텝에 512바이트를 쓰는 뱅크 쓰기 함수와, 상태 4가 그것을 실행하는 일곱 상태 드라이버 | [S: those two functions; `docs/log/cycle42-save.md` SAVE42] |
| `func_0209f6e4` | main | 세이브 프롬프트의 분기: `sp_etc_sequence4` 메시지 4(거부) 또는 `sp_etc_sequence2`(진짜 메뉴) | [S: `func_0209f6e4`, main] |
| `func_020a128c` / `func_020a12c0` / `func_020a12d4` | main | `0x021f3c30`의 이사 모드 접근자들: `:= 0`, `== 2`, `== 1` | [S: the ROM; E: `gp-W0`'s store watchpoint, `docs/log/cycle42-save.md` SAVE43] |
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
| 플레이어 슬롯 `+0x1bf2`, 15x u16 | 주머니; `0xfff1`은 빈 슬롯 | `func_02098f0c` (`func_02098f70`이 범위 검사) | `func_02098f48` [S: those three; E: GAMEPLAY47 `g47-SLOTW`, a store watchpoint on `0x021de3ae`] |
| 플레이어 슬롯 `+0x2408` u16 | **입고 있는 셔츠(WORN SHIRT).** 주머니에서 캐릭터 위로 드롭하면 둘이 교환되며, 이전 것은 셔츠 대역 `0x11a8..0x12a7`에 속할 때에만 주머니로 돌아온다 | `func_02099704`, `func_ov096_0229e3b0` case 2(ov096의 장착 디스패처)에서 호출 | `func_02099710` [S: those three, all matched; E: GAMEPLAY47 `g47-WEARW`, a store watchpoint on `0x021debc4`; `savetool.py check` prints it] |
| `0x021f3c30` | **이사 모드** 워드: 1 또는 2는 세이브를 거부, 0은 허용 | `func_ov147_02299414` / `func_ov147_022997ec` / `func_020a4454` (0이 아닌 값), `func_020a128c` (0) | `func_020a12c0` / `func_020a12d4`, `func_0209f6e4`가 읽음 [S: the ROM; E: `gp-W0`] |
| `obj+0xa0`, 테이블 `0x021f3c84` | 세이브 드라이버의 상태 바이트와 그 일곱 멤버 함수 포인터 | `func_020a2120` | `func_020a2120` [S: `func_020a2120`, main] |

## 확인 방법

그 검사는 이제 실행되었고, 심은 정지 프레임에서 요청 타입별 한 줄이 아니라 전체 집계를
출력한다 -- **다만 SAVE42 이후부터만 그렇다**: `acww_card_report()`는 SAVEFLOW41과
2026-09-10 사이에 호출자가 없었으므로, 그 사이에는 집계가 아무것도 출력하지 않았고
요청별 구간 줄만이 근거였다 [E: `port/platform/frame.c`;
`docs/log/cycle42-save.md`]. 새로 소거한 `ACWW_SAVE`로 48,000프레임 마을 레시피 전체를 돌리면
**746번의 백업 읽기(190,456바이트, 두 뱅크, 프레임 10에서), 한 번의 쓰기와 한 번의 검증 --
`0x3fffc`의 1바이트에 대해** -- 를 발행하고 두 뱅크를 0xFF로 남긴다
[E: `scratchpad/saveflow/runs/town1`; `port/shim/fs/cardreq.c`'s census;
`../experiments/save-and-reload.md`]. 이것은 세이브에 도달하지 못하는 실행의 집계다.
세이브에 도달하는 실행의 집계는 타입 7의 `744 requests, 190456 bytes`와 타입 9의 같은 값이다
[E: `scratchpad/save43/RECEIPTS.md`]. 둘을 나란히 읽어 보라: 이사 게이트의 양쪽에서 본 같은
계측기다.

    python -B scratchpad/saveflow/run_sf.py <name> ACWW_INTERP=1 ... "ACWW_SAVE=@SF@\x.sav"
    python port/tools/savetool.py check <the same absolute path>

`run_direct.py`가 아니라 `run_sf.py`를 쓰는 이유는 `ACWW_STATE_SAVE`의 `<frame>:<path>` 값이
MSYS bash에 의해 다시 쓰이기 때문이고, 다른 세션의 `taskkill /F /IM acww.exe`가 그 이름으로
실행된 모든 런을 끝내기 때문이다 [E: `../experiments/save-and-reload.md`].

## 가설

- ~~세이브 레코드는 체크섬을 갖지만 아직 발견된 것은 없다.~~ **2026-09-09 확정되었으며,
  검색은 잘못된 곳을 찾고 있었다: 그 루틴은 `crc`나 `checksum`이라 불리지 않는다.**
  `func_020a1a40` -- 부팅 시 폴러이며 `port/shim/game/savepoll.c`에 그대로 실려 있다 -- 는
  카드 읽기가 끝나면 정확히 두 번의 호출로 뱅크가 세이브인지 판정한다.
  `func_02050920(buffer, data_020d1c08[slot])`은 슬롯 전체에 걸친 리틀 엔디언 워드의 단순한
  16비트 래핑 합이며, 건너뜀도 시드도 없고, 그 합이 **0**일 때에만 뱅크가 받아들여진다;
  `func_0209f180(buffer)`이 나머지 절반이며, 이는 두 바이트 검사 `buffer[0] == 0x32`와
  (`func_0209fb3c`를 통한) `buffer[0x173fa] == 2`다
  [S: `src/matched/func_02050920.c`, `src/matched/func_0209f180.c`,
  `src/matched/func_0209fb3c.c`; `port/shim/game/savepoll.c`]. 합이 0이 되는 것은 정확히
  `+0x173f8`에 저장된 2의 보수 워드가 만들어 내는 성질이므로, 공개 에디터들이 구현한
  알고리즘이 곧 ROM의 것이다 [S: as above; `port/tools/savetool.py`'s docstring].
  세 검사는 독립적이다 -- 체크섬이 완벽해도 플래그 바이트가 틀리면 여전히 거부된다 --
  이를 `port/tools/savetool.py`의 `rom_accepts()`가 따로따로 보고하고,
  `port/tools/test_savetool.py::test_rom_acceptance_rule_on_a_synthetic_bank`가 합성 뱅크에서
  보정한다.
- ~~두 뱅크는 독립적인 두 슬롯이 아니라 주/백업 쌍이다.~~ **반쯤 확정(SAVE43): 게임 내
  세이브 한 번 뒤 뱅크 2는 뱅크 1의 바이트 단위 동일 미러이며**, 둘 다 같은 세션에서
  순서대로 쓰인다 [E: `scratchpad/save43/savecheck-S3.txt`]. 두 번째 세이브가 둘을 번갈아
  쓰는지 둘 다 다시 쓰는지는 아직 열려 있으며, 실험은 그대로다: 두 번 세이브하고 두 범위를
  diff한다.
- 0xFF는 사용되지 않은 ACWW 세이브 영역을 읽었을 때의 값이며, 게임은 0xFF 소거 상태와 0
  상태를 구별한다. 반쯤 확정: 모두 0xFF인 저장소는 인터프리터 경로를 탈선시키지 않는다 --
  마을 레시피가 폴트도 `unimplemented` 줄도 없이 48,000프레임을 돈다
  [E: `scratchpad/saveflow/runs/town1`]. 모두 0인 조건은 아직 실행되지 않았다.
- ~~정직한 0xFF 읽기 뒤에 따라오는 `unimplemented: func_02225a90` 정지는 기존 세이브 로드
  경로다.~~ 그 정지는 네이티브 경로의 관측이며, 실제 저장소를 둔 인터프리터 경로에서는
  재현되지 않는다 [E: `scratchpad/saveflow/runs/town1`, exit 100 at
  48,000 frames]. 네이티브에서 여전히 도달 가능한지는 이제 네이티브 경로만의 질문이다.
- 프레임 757에 `0x3fffc`에 쓰이는 1바이트는 저장소의 쓰기 가능 여부 탐침이다 -- ROM이 256 KB
  플래시로 식별한 칩이 마지막 주소에서 쓰기를 받아들이는지 확인하는 것이다.
  찬성 근거: 1바이트, 장치의 맨 끝에, 한 번, 곧바로 검증됨
  [E: `scratchpad/saveflow/runs/town1`'s census]. 호출자를 읽어 확정한다; 집계가 중단할
  프레임을 알려 준다. 실제로 세이브하는 실행은 이를 따로 보여 준다: `gp-S3`의 집계는
  `0x00000000..0x0002e7f8`에 걸친 744번의 타입 7 요청이며 그 구간에 `0x3fffc`에 대한 요청은
  없다 [E: `scratchpad/save43/RECEIPTS.md`].
- ~~플레이한 마을은 재실행 후에도 살아남는다. 전혀 측정되지 않았고 막혀 있다: 어떤 스크립트도
  게임이 세이브할 지점에 도달하지 못한다.~~ **2026-09-10 확정(SAVE43): 살아남는다.** 게임은
  두 뱅크를 스스로 쓰고, `savetool.py`의 `rom_accepts()`가 그것을 받아들이며, 같은 저장소로
  새로 실행하면 저장된 마을로 부팅한다 -- 위의 "게임이 수행하는 세이브"와
  `../experiments/save-and-reload.md`를 보라. 중간 단계인 SAVE42의 판독은 그것이 찾아낸
  규칙이 곧 내용이므로 남겨 둔다: **스크립트는 세이브 프롬프트에 도달하지만 게임이(GAME)
  거부한다.** 프롬프트의 분기는 `func_0209f6e4`다: `func_020a12d4() || func_020a12c0()`일 때,
  즉 `0x021f3c30`의 플레이 모드 워드가 1 또는 2일 때에만 스크립트 `sp_etc_sequence4`를 붙이고
  메시지 4 -- `지금은 아직 저장하지 못하나 봐요` -- 를 요청한다; 그렇지 않으면 진짜 세이브
  메뉴인 `sp_etc_sequence2`를 붙인다
  [S: `func_0209f6e4` / `func_020a12c0` / `func_020a12d4`, main; the two archive names are the
  literals at `0x020e37d0` and `0x020e37e4`, immediately before the member table at
  `0x020e3810`]. 그 워드는 이사 세션 내내 1이다
  [E: `scratchpad/save42/stpeek.py` on `st/town48000.st`]; 0이 아닌 값을 쓰는 함수는
  `func_ov147_02299414`(`:= 1`), `func_ov147_022997ec`(`:= 2`, `:= 3`), `func_020a4454`(`:= 3`,
  `:= 4`)이며, 모두 이사 오버레이 안이나 그 주변에 있다. 이는 첫날(opening-DAY) 규칙이
  아니며 RTC로 해제할 수 없다: 하나의 스냅샷에서 `20050615`와 `20050616`으로 두 조건을 돌리면
  HUD에 두 다른 날짜가 표시된 채 동일한 거부가 나온다
  [E: `scratchpad/save42/rtc0_a.png`, `rtc1_a.png`; `docs/log/cycle42-save.md` SAVE42].
  ~~**어떤 함수도 0을 쓰지 않으므로**, 0은 BSS 기본값이다.~~ **2026-09-10 철회(SAVE43):**
  접근자 계열은 아홉이 아니라 열(TEN) 개의 함수다. `func_020a128c`가 `mode := 0`(풀 워드
  `0x020a1294`)이고 호출자가 둘, `func_0209ec74`(main)와 `func_ov068_0226e648`이다; 저장
  워치포인트가 그것이 발동하는 것을 잡았다 [S: the ROM; E: `gp-W0`, `acww interp: WATCH store to
  0x021f3c30 value 0x00000000 width 4 at pc 0x020a1290`]. **게이트는 게임 스스로 해제한다** --
  플레이어 자신의 집에서 너굴의 대사가 끝날 때, 그 체인에서 프레임 61,000(아직 1)과
  63,000(0) 사이 -- 그리고 그다음 `func_0209f6e4`는 START를 진짜 세이브 메뉴인
  `sp_etc_sequence2` 메시지 0으로 보낸다. **다락방 침대는 세이브 지점 중 하나이지 규칙이
  아니다**; 이사에 필요한 것은 플레이어가 자기 집에 들어가는(ENTERS THEIR OWN HOUSE) 것이다
  [E: `docs/log/cycle42-save.md` SAVE43; `../experiments/save-and-reload.md`].
- ~~세이브는 매니저 객체를 `func_020a1d94`를 실행하는 상태로 만들어 트리거되며, 드라이버는
  멤버 테이블을 통해 찾아야 한다.~~ **확정(SAVE42): 드라이버는 `func_020a2120(obj, arg)`이다**
  -- 상태 바이트가 `obj+0xa0`이고, 멤버 함수 포인터 테이블이 `0x021f3c84`(`0x021f3c2c`의 가드
  워드 뒤에서 한 번만 채워짐)이며, **상태 4가 `func_020a1d94`**, 즉 한 스텝에 512바이트를
  쓰는 뱅크 쓰기 함수인 일곱 상태 머신이다; 상태 6이 머신을 0으로 리셋한다
  [S: `func_020a2120`, main].

## 관련 문서

- `../experiments/save-store-probe.md` -- 위 검사들의 레시피 (아직 미실행).
- `../experiments/two-tap-town-recipe.md` -- 모든 세이브 관측이 이루어지는 실행.
- `../experiments/gameplay-walkthrough.md` -- SAVE43 체인, 프레임 단위로.
- `time-and-rtc.md` -- 게임이 부팅 시 읽는 또 하나의 영속 상태; 거부가 날짜 규칙이 아님을
  증명한 RTC 조건은 거기와 `save-and-reload.md`에 있다.
- `../audits/night-2026-09-09.md` -- 그날 밤의 색인에 있는 SAVEFLOW41, SAVE42, SAVE43.
