# 용어집
<!-- source: wiki/glossary.md -->

위키 전반에서 사용되는 용어로, 각각 그것을 정의하는 함수나 주소를 함께 적는다.

| 용어 | 의미 | defined by |
|---|---|---|
| 에이커 (acre) | 마을 격자의 32.0 단위 셀 하나; 에이커 오브젝트는 `Translate(col*32,0,0)`에 `RotX(row*0x2999)`를 합성한 위치에 놓인다 | `func_ov003_0221f270` (ov003); `data_020ca0ec` |
| 에이커 맵 (acre map) | 세이브 이미지 안의 에이커 바이트 블록 | save `+0xd304` = `0x021e9aac` |
| 액터 매니저 (actor manager) | 현재 화면에 있는 주민 액터를 담는 여덟 개의 `{actor, id}` 슬롯 | `0x021d1d4c`; registered by `func_0202e1fc` |
| 도착 플래그 (arrival flag) | 플레이어 이벤트 플래그 1: 오프닝 시퀀스 전체 동안 세팅되어 있고, 시퀀스가 끝나면 클리어된다 | `func_02084af0`; cleared by `func_ov050_02262628`, `func_ov068_0226e948` |
| 도착 단계 (arrival step) | 플레이어가 이사 시퀀스에서 어느 단계까지 도달했는지. 따로따로 측정된 두 가지를 게이트한다: 패드 입력을 버리는 튜토리얼 일러스트와, 주민이 그려지는지 여부. **이사 모드** 워드는 그중 세이브 프롬프트가 읽는 부분이다 | `0x021f3c30`; `wiki/systems/villagers.md`, `wiki/systems/save-data.md` |
| 카테고리 니블 (category nibble) | 16비트 아이템 id의 상위 4비트; 배치 게이트는 3과 4를 받아들인다 | `func_0204bcdc` (main) |
| 카드 페이지 (card page) | `CARDi_RequestStreamCommandCore`가 모든 백업 전송을 잘라 넣는 256바이트 단위. 세이브 전체는 744페이지이고, `func_020a1d94`의 512바이트 스텝은 두 페이지다 | `src/matched/CARDi_RequestStreamCommandCore.c`; `wiki/systems/save-data.md` |
| 캡처 유닛 (capture unit) | DS의 두 사운드 캡처 유닛 중 하나로, 믹서(또는 한 채널)를 메인 RAM에 되쓴다. ACWW는 둘 다 가동하며, 재생 채널 1과 3이 읽는 것과 같은 두 버퍼를 겨냥한다 -- 이것이 유사 서라운드가 동작하는 방식이다 | `SETUP_CAPTURE` (command id 17); `port/shim/audio/capture.c`; `wiki/systems/audio.md` |
| 채널 (channel) | 게임의 살아 있는 오브젝트 단위: 핸들러 테이블에서 디스패치되는 번호 붙은 핸들러. 두 개의 정문이 여기에 도달한다 -- 씬의 채널 목록을 위한 `func_0202f134`와 특수 NPC 스케줄러의 준비된 방문객을 위한 `func_02003348` -- 둘 다 `func_020edc58`에서 끝난다 | `func_020edc58`; table pointer `0x021fd044`; `wiki/engine/scenes-and-channels.md`, `wiki/systems/events-and-calendar.md` |
| 날짜 변경 루틴 (day-change routine) | 날짜가 넘어갈 때 한 번 실행되는 달력 갱신: 하나의 전역에 대한 열일곱 번의 호출과 다섯 개의 `MI_CpuCopy8` 블록 | `func_02040c90` (main); `0x021c7584` |
| 빈 아이템 id (empty item id) | `0xfff1`, 리셋이 맵 전체에 찍는 "아이템 없음 / 타일 없음" 센티널 | `func_020a13e8` (main) |
| 이벤트 비트필드 (event bitfield) | 플레이어의 64개 진행 비트 | `player + 0x23f8`; `func_02099020` / `func_02098ff8` |
| 페이드 상태 (fade state) | `0` 대기, `1` 페이드 인, `2` 완료, `3` 페이드 아웃 -- 씬 진행의 게이트 | `0x021c75b8`; read by `func_ov051_022611e0` |
| 필드 오브젝트 (field object) | 야외 씬의 루트; 그 `+0x50`이 필드 데이터 포인터로 공개되고, 날씨는 `+0x2d0`에 매달려 있다 | `func_02034d14` (vtable `0x020da334`); `0x021c526c` |
| 집 레코드 (house record) | 주민과 그 집을 담는 `0x7ec` 바이트 세이브 레코드 여덟 개 중 하나; 주민 서브 레코드는 `+0x7a0`에 있다 | save `+0x9284` = `0x021e5a2c` |
| 집터 (house plot) | 아이템 id `0x500a`, 배치기가 `0x5001`..`0x5008`로 변환하는 지점 | `func_0207bbb8` (main) |
| 실내/실외 바이트 (indoor/outdoor byte) | 0이 아니면 실내 분기를 탄다; 특수 NPC 준비를 막는다 | `data_020e54a8`; `func_02085558` |
| 인터프리터 경로 (interpreter path) | ROM 자체의 ARM/Thumb 코드를 프로세스 내에서 실행하는 하이브리드 런타임 (`ACWW_INTERP=1`) | `port/interp/interp_cpu.c`; `docs/HYBRID-PLAN.md` |
| 키보드 (keyboard) | `ov126` 이름 입력 화면; 그 터치 디스패처는 함수 포인터 워드로만 존재한다 | `func_ov126_022a1228` (ov126); reloc `0x022a1ff0` |
| 조명 테이블 (light table) | 조명을 받는 모든 버텍스가 궁극적으로 샘플링하는 낮/밤 색상 테이블 | `0x021f6cf0`; filled by `func_020bbf0c` |
| 이사 모드 (move-in mode) | 세이브 프롬프트가 읽는 워드: 1 또는 2는 거부(`sp_etc_sequence4` 메시지 4), 0은 실제 세이브 메뉴를 허용한다. ov147의 이사 단계들이 0이 아닌 값으로 쓰고, 도착이 끝나면 `func_020a128c`가 다시 0으로 되돌린다 -- 접근자는 모두 열 개 | `0x021f3c30`; `func_0209f6e4`, `func_020a128c`; `wiki/systems/save-data.md` |
| 오라클 (oracle) | 같은 레시피 아래에서 포트와 비교되는 DeSmuME 레퍼런스 | `port/tools/oracle/` |
| 출력 선택자 (output selector) | `SOUNDCNT`의 각 스피커가 무엇을 듣는지에 대한 선택: 믹서, 또는 채널 1/3 직접. ACWW는 `OUTPUT_SELECTOR 1 2 1 1`을 보낸다 -- 왼쪽은 Ch1에서, 오른쪽은 Ch3에서, 둘 다 믹서를 우회 -- 그래서 스피커는 캡처 경로의 복사본을 한 버퍼 늦게 듣는다 | command id 25; `port/shim/audio/capture.c`; `wiki/systems/audio.md` |
| 멤버 함수 포인터 (PMF) | CodeWarrior의 멤버 함수 포인터로, 8바이트 `{lo, hi}` 쌍으로 저장된다 | `port/shim/game/memptr.c`; e.g. villager draw at `obj + 0x8b0` |
| 패드 스크립트 (pad script) | `ACWW_PADSCRIPT`가 읽는 타임라인 파일: 한 줄에 한 행, 패드는 `<frame> <mask> <frames>`, 스타일러스는 `<frame> T <x> <y> <frames>`. 겹치는 패드 행은 OR로 합쳐지고, 스타일러스 행은 처음 일치하는 것이 이긴다. 프레임 0부터 패드를 소유하므로, 부팅 실행은 부팅 키 단계들을 행으로 다시 구성해야 한다 | `port/platform/hostinput.c`; `docs/kb/hybrid/recipes.md` 4b; `wiki/experiments/gameplay-walkthrough.md`. The oracle takes the same file (`--padscript`) |
| 페이서 (pacer) | 포트를 NDS 고유의 59.8261 Hz(33.513982 MHz / 560190 사이클)에 붙들어 두는 프레임 리미터. 스크립트된 것이라면 기본 OFF -- `ACWW_KEYS*`/`ACWW_TOUCH*`/`ACWW_SHOT*` 변수나 `ACWW_STOP_FRAME`이 있는 경우 -- 이고, 두 프레임 넘게 뒤처지면 질주하는 대신 기준을 다시 잡는다 | `port/platform/frame.c`; `ACWW_PACE`/`ACWW_NOPACE`; `wiki/experiments/live-play.md` |
| 플레이어 슬롯 (player slot) | 세이브 이미지 안의 `0x249c` 바이트 플레이어 레코드 네 개 중 하나 | save `+0x14` = `0x021dc7bc`; stride from `func_02098844` |
| 세이브 이미지 (save image) | 세이브의 `0x173fc` 바이트 RAM 내 복사본 | `0x021dc7a8`; written by `func_020b5724` |
| 씬 (scene) | 씬 기구를 통해 요청되는, 부팅/게임 시퀀스의 번호 붙은 단계 | `func_020a53ec`; pending word `0x020e3c80` |
| 계절 (season) | 0 봄, 1 여름, 2 가을, 3 겨울, 월과 일로부터 결정 | `func_02063bb4` (main) |
| 계절/이벤트 인덱스 (season/event index) | 8월과 9월이 각각 둘로 나뉘는 열네 값의 월 맵 | `func_0204fa8c` (main) |
| 하늘 행 (sky row) | 계절과 날씨로 선택되는 낮/밤 테이블의 행 | `0x021f8ad4` -> `table_020d2364`; used by `func_020bba14` |
| 특수 NPC 테이블 (special-NPC table) | 예약된 방문객당 하나씩, `{channel, actor, overlay, pmf, flag}`의 스물세 행 | `data_020e1d8c` (main) |
| 대화 머신 (talk machine) | 대화를 구동하는 다섯 항목의 `{enter, update}` 테이블과 `f8`/`f9`/`fa` 상태 바이트 | `data_021c17c4`; `func_020146cc` |
| 타일 (tile) | 2.0 월드 단위; 타일 워드의 그룹/인덱스 분할을 통해 찾는 3바이트 레코드 | `func_ov003_022273f8` (ov003); descriptors at `0x02236b0c` |
| 마을 디스패처 (town dispatcher) | 마을을 생성하고, 리셋하고, 동기화하는 핸들러 집합 | `func_0209e6ec` (main) |
| 주민 클래스 (villager class) | 초기 선택이 뽑아 오는 여섯 개의 성격 그룹 중 하나 | `func_0207c818` (main); bound at 6 in `func_0207c76c` |
| 아레나 (arena) | OS의 자유 메인 RAM 구간, `OS_GetArenaLo(0)`..`OS_GetArenaHi(0)`; 게임 힙은 그 아래쪽 끝에서 잘라낸다 | `func_020ea48c`; ceiling `0x023e0000`, the port raises it to `0x023f0000` (`port/shim/os/arenahi.c`) |
| BMG | `MESGbmg1`, 메시지 컨테이너: `INF1` 레코드와 `DAT1` UTF-16 페이로드; `script/KOR/` 아래에 1,791개의 낱개 `.bmg` 파일 | `extract/adm-kr/files/script/KOR/message/Other/test_.bmg`; `wiki/data/archives.md` |
| 거부 목록 (deny list) | `interp_registry.py`가 등록을 거부하는 51개의 심 basename으로, 인터프리터 경로에서는 이들에 대해 ROM 자체의 본체가 실행된다 (TOUCH41이 `touch.c`를 추가하기 전까지는 49개; RTC42가 `rtcclock.c`를 추가해 레지스트리를 93 -> 90으로 만든 이후 51개) | `port/tools/interp_registry.py`, `DENY_FILES` (plus `DENY_FUNCS = {func_020b1b84}`), counted at `2e579f09` |
| 차등 검사 (differential check) | 함수별 승격 테스트: 실제 실행이 하는 호출들을 기록하고, 각각을 같은 호출 전 페이지에서 두 번 재생한 뒤 -- 한 번은 인터프리터로, 한 번은 네이티브 본체로 -- 반환값과 최종 상태의 쓰기 집합을 비교한다. 일치는 기록된 호출들에 대해서만 근거가 된다 | `port/tools/promote.py`, `port/interp/interp_record.c`; `wiki/engine/interpreter-path.md`; `docs/kb/hybrid/promotion.md` |
| 디스플레이 오브젝트 (display object) | 두 개의 리스트 노드를 소유하는 C++ 오브젝트로, 네 개의 전역 리스트에 연결되어 vtable 슬롯을 통해 프레임당 한 번 스텝된다 | `func_020ee834`; heads `0x021fd004`/`14`/`24`/`34`; `wiki/engine/display-objects.md` |
| 게임 힙 (game heap) | 아레나 블록 + 0x30에 만들어지는 NNS 확장 힙으로, 모든 게임 오브젝트가 여기서 할당된다 | `func_020ea50c`; pool words `0x021fbe78`/`8c`/`94` |
| NARC | 게임이 `FSArchive`로 마운트하고 `archive:path`로 멤버를 읽는 `BTAF`/`BTNF`/`GMIF` 아카이브 | `NNS_FndMountArchive` (autoload_2 `0x0210288c`); `src/matched/NNS_FndMountArchive.c` |
| OFF 레시피 (OFF recipe) | 대조 실행: 스타일러스를 비활성화한 키 입력 START(프레임 300부터 `ACWW_KEYS=9`), 프레임 9,000까지의 스크린샷 31장을 SHA-256으로 비교 | `wiki/experiments/off-recipe.md`; `docs/kb/hybrid/recipes.md` section 2 |
| 승격 (promotion) | `src/matched/` 본체를 ROM의 바이트 대신 핫 패스에 되돌려 놓는 것(하이브리드 계획 단계 H5). 승격은 등록이 아니다: 일치한다는 것은 그 함수가 호스트 코드여야 하는지에 대해 아무것도 말해 주지 않는다 | `port/tools/promote_record.py`; `docs/kb/hybrid/promotion.md`; `wiki/engine/interpreter-path.md` |
| PXI 태그 (PXI tag) | ARM9-ARM7 FIFO의 번호 붙은 채널: 4 NVRAM, 5 RTC, 6 터치, 7 사운드, 8 전원, 10 무선, 11/14 카드 | callback table `0x027e0394 + tag*4`; `PXI_SetFifoRecvCallback` (autoload_2) |
| 샘플링 링 (sampling ring) | `gAutoData`, ARM7이 프레임당 네 샘플씩 채우는 아홉 항목의 `TPData` 링; 게임의 프레임당 공개는 그 마지막 네 항목을 읽는다 | `0x021fbdf0`; installed by `func_020e948c` via `TP_RequestAutoSamplingStartAsync(0, 4, &gAutoData, 9)`; `wiki/experiments/touch-latency.md` |
| 세이브스테이트 (savestate) | 한 프레임에서의 실행 스냅샷: 매핑된 NDS 영역 일곱 개(4 KB 페이지, 제로 비트맵), 이름 붙은 호스트 블롭(SAVE41에서 113개, RTC42가 시계를 추가한 이후 **20개 등록자에서 118개**), 그리고 살아 있는 스레드당 인터프리터 레지스터 파일 하나로, 헤더가 링크를 고정하고 다른 빌드를 거부한다 | `port/platform/state.c`; `ACWW_STATE_SAVE` / `ACWW_STATE_LOAD`; `wiki/experiments/savestate-resume.md`; `docs/kb/hybrid/savestate.md` |
| 스텝 게이트 (step gate) | 프레임당 모든 디스플레이 오브젝트 스텝이 통과해야 하는 여섯 명령어짜리 테스트: `+0x0f` 클리어 AND `+0x13`의 비트 1 클리어 | `func_01ffd41c` (itcm); `port/shim/gfx/dispgate.c` |
| 마을 레시피 (town recipe) | 타이틀 화면에서 마을 회관까지의 두 번 탭 실행, 48,000 프레임; 모든 마을, 하늘, 키보드 관측이 이 실행 아래에서 얻어진다 | `wiki/experiments/two-tap-town-recipe.md`; `docs/kb/hybrid/recipes.md` section 3 |
| TP_POINT | ROM 자체가 공개하는 터치 포인트, `{x, y, touch, validity}`; 터치된 샘플이 없으면 x=y=`0x00ff`를 공개한다 [S: `func_020e9314`, autoload_2, `config/adm-kr/arm9/autoload_2/symbols.txt`; `docs/log/cycle40-keyboard-gate-probe.md` TOUCH41] | `0x021fbde8`, written by `func_020e9314` (autoload_2), read by `func_020b9280` |
| 유효성 (validity) | `TPData`의 네 번째 하프워드: 오류 코드이므로 **0이 샘플이 정상이라는 뜻**이다. 3은 `TP_VALIDITY_INVALID_XY`로, 펜이 떨어져 있을 때 ARM7이 x=y=0과 함께 쓰는 값이다 | `TP_GetCalibratedPoint`, autoload_2; NitroSDK `include/nitro/spi/ARM9/tp.h`; `wiki/systems/input-and-touch.md` |
| VBlank 태스크 리스트 (VBlank task list) | ROM이 수직 블랭크 안에서 순회하는 두 번째의 별도 리스트로, 각 태스크는 vtable 슬롯 0을 통해 실행된다 | head `0x021f6ca0`; walked by `func_020b98ec` (main) |
| 워크 모드 (walk mode) | 어느 디스플레이 리스트가 순회 중인지 말하는 전역; 모드 3은 커밋을 업데이트 리스트로 미룬다 | `0x0213e7fc`; read by `func_020ee59c` |
