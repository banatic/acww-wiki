# 난수
<!-- source: wiki/systems/rng.md -->

**요약.** 이 ROM에는 단일한 난수 생성기가 없다. 알려진 것은 넷이다. 셋은 라이브러리
생성기다 -- 네트워킹 코드가 사용하는 NitroSDK의 `MATH_Rand16`과 `MATH_Rand32`; 시각적
흔들림에 사용되는 SPL 파티클 라이브러리 자체의 생성기; 그리고 Wi-Fi 설정 오버레이의 독자적인
생성기 -- 이며, 각각은 하드웨어 틱, 실시간 시계, 또는 둘 다로부터 시드된다. **네 번째는
게임 자체의 것이며, ORACLE46이 이를 찾아냈다**: `0x021cb5a0`의 32비트 상태 워드 하나가
`x = x * 0x19660d + 0x3c6ef35f`로 스텝되고, 부팅 시 실시간 시계의 네 바이트로 단 한 번
시드되며, 이것이 마을의 id와 마을의 주민들을 뽑는 것이다.

## 무슨 일이 일어나는가

**이 페이지에 필요한 명명 주석.** `MATH_Rand16`, `MATH_Rand32`, `MATH_InitRand16/32`,
`OS_IsTickAvailable`은 NitroSDK 라이브러리 이름이지 이 ROM의 심볼 테이블에 있는 이름이
아니다: 어떤 `config/adm-kr/arm9/**/symbols.txt`에도 그런 심볼은 존재하지 않으며, 이들 모두는
`src/matched/`에서 `func_*` 이름으로 도달된다 [S: `config/adm-kr/arm9/**/symbols.txt`, name sweep].
`../STYLE.md` 규칙 2가 SDK 이름을 허용하기 때문에 여기서는 그 이름을 사용하며, `func_*` 이름이
존재하는 곳에서는 함께 병기한다.

### 게임 자체의 생성기와 그 시드

**상태는 `0x021cb5a0`의 워드 하나이며** 스텝은 `func_020e92e8`이다:
`x = x * 0x19660d + 0x3c6ef35f`, 상태는 다시 써지고 통째로 반환된다
[S: `src/matched/func_020e92e8.c`]. 범위 제한 추출은 `func_020e92d0(state, n)`이며,
`(n * x) >> 32`를 반환한다 -- SDK 생성기들도 사용하는 상위 비트 형식이다
[S: `src/matched/func_020e92d0.c`]. **`func_020644cc(n)`은 상태를 묶는 게임 전역
래퍼다**: 그 ARM 명령 세 개는 `ldr r12, [pc,#8]` -> `func_020e92d0`,
`mov r1, r0`, `ldr r0, [pc,#4]` -> `0x021cb5a0`, `bx r12`이므로, `0x020644dc`와
`0x020644e0`의 풀 워드는 각각 함수와 상태이며 어느 쪽도 추론이 아니다
[S: `extract/adm-kr/arm9/arm9.bin` at `0x020644cc`, read in ORACLE46; the matched file
`src/matched/func_020644cc.c` spells both as placeholder names -- D12].

**부팅 시 시계로부터 한 번 시드되며, 시드는 네 바이트다.**
`__sinit_020c5a78`은 상태를 1로 설정하고 콜백을 등록한다
[S: `src/matched/__sinit_020c5a78.c`]; 그 다음 `func_02061530`이
`func_020e930c(0x021cb5a0, func_0209dbbc())`를 호출하며, `func_020e930c`는 두 명령짜리 저장이다 --
이것이 `srand`다 [S: `src/matched/func_02061530.c`, `src/matched/func_020e930c.c`].
`func_0209dbbc`는 게임의 시계 전역 변수를 읽어 접어 넣는다:

    seed = minute | (day << 8) | (hour << 16) | (second << 24)

`0x021dc758`, `0x021dc74c`, `0x021dc754`, `0x021dc75c`로부터다
[S: `src/matched/func_0209dbbc.c`]. **연도, 월, 요일은 여기에 들어 있지 않으며, 틱도
들어 있지 않다.** 포트에서 그 블록에 로드 워치포인트를 걸면 정확히 그 세 pc --
`0x0209dbc0`, `0x0209dbc4`, `0x0209dbcc` -- 가 **프레임 3**에서 발화하며 `0`, `0x0f`,
`0x0a`를 읽는 것이 보인다: 기본 2005-06-15 10:00:00 순간에 대한 시드 `0x000a0f00`이다. 같은
센서스를 두 생성 프레임에 창으로 걸면 그 pc들이 부재하므로, 아무것도 다시 시드하지 않는다
[E: `docs/log/cycle41-gameplay.md` ORACLE46, runs `scratchpad/oracle46/runs/o46-A`, `scratchpad/oracle46/runs/o46-D`, `scratchpad/oracle46/runs/o46-E`].

**무엇을 뽑는가.** 마을의 id는 `func_0206426c` = `func_020644cc(0x7fff) | 0x8000`이며,
`func_02064244`에 의해 `0x021dc7aa`의 하프워드로 저장된다
[S: `src/matched/func_0206426c.c`, `src/matched/func_02064244.c`]; 주민 선택기
`func_0207b594`는 같은 래퍼에서 뽑는다(`villagers.md`). 포트에서 끝에서 끝까지 측정한 결과:
프레임 24,789에서 상태는 `0x010d14fa`로 읽히고 `0x8cdea011`로 스텝되며,
`(0x7fff * 0x8cdea011) >> 32 = 0x466e`이고, 이를 `| 0x8000`하면 저장 워치포인트가 안착하는
것을 보는 `0xc66e`다 [E: ORACLE46 run `scratchpad/oracle46/runs/o46-F`].

**마을의 ID와 마을의 지도는 스트림 위의 서로 다른 두 순간이며, 11,346 프레임
떨어져 있다.** id는 이름 확인 시점(포트 프레임 24,789, 추출 **#2,667**)에 뽑히고; 에이커
지도, 아이템 레이어, 주민 명단은 모두 나중의 한 버스트 -- 포트 프레임
**36,135**, 추출 **#3,783..#4,014**, 모두 그 단일 프레임 안 -- 에서 뽑히며; 원본은 같은
버스트를 ~90 프레임에 걸쳐 펼친다. 지도는 두 번째로도 생성된다: 한 번은 부팅 시 280회 추출
초기화 버스트 안에서(포트 프레임 758, 인덱스 0..280), 그 다음 진짜 생성 전에 `0x86` / `0xfff1`로
리셋된다. 따라서 id 추출을 고정하는 레시피는 지도를 고정하지 않으며, 지도를 고정하는 레시피는
같은 프레임이기 때문에 명단을 덤으로 얻는다
[E: `docs/log/cycle41-gameplay.md` ORACLE49 O49-1/O49-2]. `func_0209ccd4`의 6x6 루프 -- 에이커당
범위 제한 추출 하나, 36개 -- 는 그 버스트 안에 있다 [S: `src/matched/func_0209ccd4.c`].

**시드는 견고하지만, 추출 횟수는 그렇지 않다.** 시드는 실행의 첫 1초 안에 취해지기
때문에, 나중 프레임부터만 시계를 붙드는 시계 조건은 이를 바꿀 수 없다:
에뮬레이터는 `--rtc-freeze-until` 유무와 무관하게 프레임 44에서 `0x000a0f00`을 낸다
[E: ORACLE46 `scratchpad/oracle46/runs/o46-seedarm2` / `scratchpad/oracle46/runs/o46-seedoff`]. 두 마을을 가르는 것은
그 시드와 id가 뽑히는 순간 사이에 몇 번의 추출이 소비되는가이며, 이는 그 사이에 실행이
한 모든 일의 속성이다.

### 추출은 어디로 가며, 두 생성자는 얼마나 떨어져 있는가

**모든 추출은 단 하나의 명령을 거친다.** 포트 실행의 세 개 별도 창에 걸쳐 `0x021cb5a0`에
저장 워치포인트를 걸면 -- 총 131회 저장 -- pc `0x020e92f8`만 보고되고 다른 것은 없다:
`func_020e92e8` 자신의 되쓰기다. 두 번째 기록자도 없고 생성자별 경로도 없으므로,
이 ROM의 두 실행은 오직 그 하나의 스트림에서 얼마나 멀리 갔는가만 다르다
[E: `scratchpad/oracle47/RECEIPTS.md`, O47-2; `docs/log/cycle41-gameplay.md` ORACLE47 O47-2].

**추출은 프레임당 한 번이 아니라 메인 루프 본체당 한 번 소비된다.** 포트에서 프레임
852..1,002에 걸친 연속 51회 저장은 정확히 세 프레임 간격이며, 메인 루프는 포트와 원본
양쪽에서 세 프레임에 한 번 돈다 [E: same, and INPUT46 on `0x021fbdd0`,
`docs/kb/hybrid/stall-playbook.md` case 70]. 비율은 씬에 따라 다르다 -- 타이틀에서는 세
프레임에 한 번, 마을 이름 페이지에서는 ~12 프레임에 한 번 -- 이므로 **씬에 일찍 도달하는
실행은 더 적은 추출을 취한 채로 도착하며**, 이것이 씬 시간에서 원본보다 ~280 프레임 앞선
포트가 마을이 뽑힐 때 스트림 위치에서는 ~176 프레임 뒤처지는 이유다. LCG는 전단사이므로
엿본 워드 하나가 자신의 인덱스를 스스로 말해 준다: `scratchpad/oracle47/lcg.py`는 시드를
범위 안에서 앞으로 스텝하고, `draws.py`는 어느 생성자의 장부든 추출 횟수로 바꾼다.

**모든 차분 실험에 대한 귀결.** 두 생성자가 같은 마을을 뽑게 만드는 것은 시계를 바꾸는
것이 아니라 추출을 촉발하는 입력을 옮기는 것이다: `port/tools/oracle/README.md`,
"THE SHARED-TOWN RECIPE".

### SDK 생성기

`MATHRandContext32`는 세 필드 구조체 -- 상태, 승수, 가수, 모두 64비트 -- 이며, `MATH_Rand32`는
이를 `x = mul * x + add`로 진행시키고 새 상태의 상위 32비트를 반환하거나, 범위 제한 추출의
경우 `(top32 * max) >> 32`를 반환한다
[S: `MATH_Rand32`, ov065, `src/matched/func_ov065_0227ef00.c`]. 상수는 승수
`0x5D588B656C078965`와 가수 `0x269EC3`이다; 승수는 소스에
`(1566083941 << 32) + 1812433253`으로 적혀 있다 [S: same].

`MATHRandContext16`은 같은 계열을 절단한 것이다: 32비트 상태, 승수 `0x5D588B65` -- 정확히
64비트 승수의 상위 절반 -- 가수 `0x269EC3`, 출력은 상위 16비트
[S: `MATH_Rand16` / `MATH_InitRand16`, autoload_2, `src/matched/func_02100cbc.c`]. 하위 비트가
아니라 상위 비트를 취하는 것이 설계의 요점이다: LCG의 하위 비트는 주기가 짧다.

파티클 생성기는 무관하며 그 상수가 그렇게 말한다: 승수 `0x5EEDF715`, 가수 `0x1B0CB173`,
32비트 상태, 출력은 상위 비트
[S: `SPLRandom_Next` / `gSPLRandomState`, main, `src/matched/func_020fded0.c`]. 이것은 파티클
스폰 위치, 속도, 회전, 수명, 텍스처 프레임과 색상을 구동한다
[S: `SPLEmitter_EmitParticles`, main, `src/matched/func_020fded0.c`]. 같은 생성기 본체가 두 개의
추가적이고 독립적인 상태 워드 -- 하나는 ov066에, 하나는 main에서 `g_rng_state`라는 이름으로 --
에 대해서도 나타나므로, 최소 세 개의 파티클 류 스트림이 병렬로 돈다
[S: `src/matched/func_ov066_022699ec.c`, `src/matched/func_020ff994.c`].

ov001의 `AOSS_Rand`는 SDK를 호출하는 대신 16비트 상수를 자신만의 독립적인 32비트 LCG로
재사용하는 네 번째 구현이며, `(0x7fff * (v >> 16)) >> 16`으로 15비트 값을 반환한다
[S: `AOSS_Rand`, ov001, `src/matched/AOSS_Rand.c`].

### 시드는 어디에서 오는가

두 소스가 있으며 둘 다 시계다.

`OS_GetTick`이 지배적인 소스다. `func_ov065_0227876c`(임시 로그인 id를 꾸며내는 데 쓰이는
일회용 컨텍스트)와 `func_021013d0`(틱을 읽고, LCG 한 스텝을 손으로 돌리며, 곱의 상위 32비트만
연결별 시드로 저장)에서 직접 시드가 된다 [S: `src/matched/func_ov065_0227876c.c`,
`src/matched/func_021013d0.c`]. 공유 네트워크 컨텍스트 `DWCi_GetMathRand32`는 본체의 MAC
주소와 틱을 결합해 한 번, 지연 방식으로 스스로를 시드한다
[S: `func_ov065_0227ef00`, ov065, `src/matched/func_ov065_0227ef00.c`].

RTC가 다른 하나다. `DWCi_AUTH_GetNewWiFiInfo`와 `DWCi_AUTH_RemakeWiFiID`는 초로 변환한 RTC
날짜와 시각으로 16비트 컨텍스트를 시드하고, `OS_IsTickAvailable`이 그렇다고 하면 틱을 더하며,
그 다음 `MATH_Rand16`을 사용해 Wi-Fi id와 0이 아닌 `randomHistory` 값을 만든다 -- 재생성
경로는 이전 history 값을 제외한다
[S: `src/matched/func_02100cbc.c`, `src/matched/func_02100b18.c`]. `AOSS_Rand`는 첫 호출 시
`hour << 10 + minute << 3 + second`를 시드에 접어 넣으며, RTC 읽기가 실패하면 시드 0으로
대체한다 [S: `AOSS_Rand`, ov001, `src/matched/AOSS_Rand.c`].

매칭된 코퍼스에서 아무도 소비하는 것으로 나타나지 않는 엔트로피 풀도 있다.
`OS_GetLowEntropyData`는 `OS_GetTickLo`와 결합한 VCOUNT(`0x04000006`), MAC 바이트 및 VBlank
카운터와 XOR한 64비트 틱, `0x04000600`의 지오메트리 엔진 상태 레지스터, 하위 WRAM의 RTC
바이트, 마이크 데이터, 터치 패널 상태, Wi-Fi RSSI 풀로부터 여덟 워드를 채운다
[S: `OS_GetLowEntropyData`, autoload_2,
`src/matched/OS_GetLowEntropyData.c`]. 이것은 위의 어느 생성기에도 연결된 것이 아니라 사용
가능한 인프라로 읽힌다 [S: absence of callers in `src/matched`].

### 아직 발견되지 않은 것

세이브 측이나 마을 측의 시드 필드는 없다. `src/matched` 전체에서 `SaveData`, `TownData`,
`randomSeed`, `worldSeed`, `townSeed` 등을 검색해도 아무것도 나오지 않으며 [S: absence in `src/matched`],
ORACLE46의 측정은 이 경로에서 찾을 것이 없다는 것과 일치한다: `0x021cb5a0`의 상태는
부팅 시 시계로부터 시드되고 그저 돈다. 아직 열려 있는 것은 게임의 추출 중 어느 것이
이 스트림에서 나오고 어느 것이 다른 스트림에서 나오는가이다 -- 주민 선택기와
마을 id는 확립되었고, 물고기, 곤충, 상점 재고는 그렇지 않다.

세이브 체크섬은 `crc`/`checksum` 이름 검색에서 놓쳤다: 뱅크 폴러
`func_020a1a40`은 16비트 랩어라운드 워드 합 `func_02050920`을 호출하고, `func_0209f180`의
헤더 검사와 함께 합이 0인 경우만 받아들인다 [S: `port/shim/game/savepoll.c`,
`src/matched/func_02050920.c`, `src/matched/func_0209f180.c`; log:
`docs/log/cycle41-gameplay.md` GP45-5].
GP45-5는 저장된 체크섬과 계산된 체크섬이 `0xbddf`, 잔차 `0x0000`인 완전한 세이브와,
게임이 그 뱅크를 로드할 것이라고 보고하는 ROM 수용 테스트를 기록했다
[E: `scratchpad/gameplay45/RECEIPTS.md`; log: `docs/log/cycle41-gameplay.md` GP45-5].

### 포트

고정 시계 조건은 다른 부팅 시드를 만들어 내지 않는다: ORACLE46은 `--rtc-freeze-until 48000`
유무와 무관하게 포트에서는 프레임 3에, 원본에서는 프레임 44에 `0x000a0f00`을
측정했다 [E: `scratchpad/oracle46/RECEIPTS.md`; log:
`docs/log/cycle41-gameplay.md` O46-4].
ORACLE47은 조건 적용 원본과 미적용 원본이 프레임 1,000부터 10,000까지 같은 스트림
위치에 있고, 10,000과 11,000 사이에서 처음 갈라지며, 확인 시점에는 적용 쪽이 14회 더
추출한 채로 끝나는 것을 발견했다 [E: `scratchpad/oracle47/RECEIPTS.md`,
`scratchpad/oracle46/ledgers/o-townarm.jsonl`, `scratchpad/oracle46/ledgers/o-townoff.jsonl`;
log: `docs/log/cycle41-gameplay.md` O47-3].
이 조건들은 마을 이름 페이지에서의 추출 소비가 다르므로, 부팅 시드를 공유하는 것만으로는
공유 마을이 성립하지 않는다 [E: `scratchpad/oracle46/RECEIPTS.md`,
`scratchpad/oracle47/RECEIPTS.md`; log: `docs/log/cycle41-gameplay.md` O46-4, O47-3].
정방향 레시피는 측정된 빌드에서 id와 나중의 배치/명단 버스트를 정렬하고;
역방향 레시피는 id는 정렬하지만 배치 버스트에 두 추출 일찍 도달한다
[E: `scratchpad/oracle49/RECEIPTS.md`; log: `docs/log/cycle41-gameplay.md` O49-2, O49-4, O49-5].

## 어디에 있는가

| 함수 또는 심볼 | 모듈 | 역할 | 등급/출처 |
|---|---|---|---|
| `func_020e92e8` `0x020e92e8` | main | **게임의 LCG**: 호출자의 상태 워드에 대해 `x = x * 0x19660d + 0x3c6ef35f` | [S: `src/matched/func_020e92e8.c`] |
| `func_020e92d0` `0x020e92d0` | main | 범위 제한 추출 `(n * next) >> 32` | [S: `src/matched/func_020e92d0.c`] |
| `func_020644cc` `0x020644cc` | main | 상태 `0x021cb5a0`을 그 추출에 묶는다 -- 게임 전역 `rand(n)` | [S: `extract/adm-kr/arm9/arm9.bin` at `0x020644cc`, pool words `0x020644dc`/`0x020644e0`] |
| `func_02061530` `0x02061530` / `func_020e930c` | main | `srand`: 상태를 `func_0209dbbc()`로 설정 | [S: `src/matched/func_02061530.c`] |
| `func_0209dbbc` `0x0209dbbc` | main | 시드: `minute \| day<<8 \| hour<<16 \| second<<24` | [S: `src/matched/func_0209dbbc.c`] |
| `func_0206426c` / `func_02064244` | main | 마을 id, `rand(0x7fff) \| 0x8000`, `0x021dc7aa`의 하프워드로 | [S: `src/matched/func_0206426c.c`] |
| `MATH_Rand32` / `MATH_InitRand32` / `MATHRandContext32` | ov065 | 64비트 LCG, 승수 `0x5D588B656C078965`, 가수 `0x269EC3`, 출력 상위 32 | [S: `src/matched/func_ov065_0227ef00.c`] |
| `MATH_Rand16` / `MATH_InitRand16` / `MATHRandContext16` | autoload_2 | 32비트 LCG, 승수 `0x5D588B65`, 가수 `0x269EC3`, 출력 상위 16 | [S: `src/matched/func_02100cbc.c`] |
| `DWCi_GetMathRand32` `0x0227ef00` | ov065 | 공유 네트워크 컨텍스트, MAC과 틱으로 한 번 시드 | [S: `src/matched/func_ov065_0227ef00.c`] |
| `func_ov065_02268c78` (`CPS_Resolve`) | ov065 | DNS 트랜잭션 id를 위해 `MATH_Rand32(ctx, 0x10000)`을 추출 | [S: `src/matched/func_ov065_02268c78.c`] |
| `func_ov065_0227876c` | ov065 | 임시 로그인 id를 위해 `OS_GetTick`으로 시드한 일회용 컨텍스트 | [S: `src/matched/func_ov065_0227876c.c`] |
| `func_021013d0` | autoload_2 | 틱에 대한 손으로 쓴 LCG 한 스텝; 상위 32비트만 유지 | [S: `src/matched/func_021013d0.c`] |
| `func_02100cbc` (`DWCi_AUTH_GetNewWiFiInfo`) | autoload_2 | RTC 더하기 틱 시드, Wi-Fi id와 `randomHistory`를 위한 `MATH_Rand16` | [S: `src/matched/func_02100cbc.c`] |
| `func_02100b18` (`DWCi_AUTH_RemakeWiFiID`) | autoload_2 | 같은 것, 이전 history 값을 제외 | [S: `src/matched/func_02100b18.c`] |
| `SPLRandom_Next`, `gSPLRandomState` | main | 파티클 LCG, 승수 `0x5EEDF715`, 가수 `0x1B0CB173` | [S: `src/matched/func_020fded0.c`] |
| `SPLEmitter_EmitParticles` / `SPLEmitter_EmitChildParticles` | main | 그 소비자들: 스폰 흔들림, 회전, 수명, 프레임, 색상 | [S: `src/matched/func_020fded0.c`, `src/matched/func_020fdc08.c`] |
| `func_020ff994` | main | `g_rng_state`에 대한 세 번째 파티클 류 스트림 | [S: `src/matched/func_020ff994.c`] |
| `AOSS_Rand` `0x02207cd4` | ov001 | Wi-Fi 설정 LCG, `RTC_GetTime`으로 시드 | [S: `src/matched/AOSS_Rand.c`] |
| `OS_GetLowEntropyData` `0x02116da8` | autoload_2 | VCOUNT, 틱, MAC, GX 상태, RTC, 마이크, 터치, RSSI로부터의 여덟 워드 풀 | [S: `src/matched/OS_GetLowEntropyData.c`] |
| `MATH_CalcCRC8` / `CalcCRC16` / `CalcCRC32` | autoload_2 | CRC 헬퍼; 세이브 폴러는 대신 `func_02050920`을 호출한다 | [S: `port/shim/game/savepoll.c`; log: `docs/log/cycle41-gameplay.md` GP45-5] |

## 읽고 쓰는 데이터

| 주소 또는 필드 | 의미 | 쓰는 쪽 | 읽는 쪽 |
|---|---|---|---|
| `0x021cb5a0` | **게임의 RNG 상태**, 워드 하나 | `func_020e930c`(시드), `func_020e92e8`(모든 추출) | `func_020e92e8` [E: ORACLE46 `scratchpad/oracle46/runs/o46-F`, `--peek 0x021cb5a0`] |
| `0x021dc7aa` | 마을 id 하프워드, `rand(0x7fff) \| 0x8000` | `func_02064244`, pc `0x02064260`에서 | 마을 레코드의 읽는 쪽들 [E: ORACLE46 `scratchpad/oracle46/runs/o46-A`] |
| `MATHRandContext32.x` | 64비트 LCG 상태 | `MATH_Rand32`, `MATH_InitRand32` | `MATH_Rand32` [S: `src/matched/func_ov065_0227ef00.c`] |
| `MATHRandContext16.x` | 32비트 LCG 상태 | `MATH_Rand16`, `MATH_InitRand16` | `MATH_Rand16` [S: `src/matched/func_02100cbc.c`] |
| `gSPLRandomState` | 파티클 스트림의 상태 워드 | `SPLRandom_Next` | 모든 `SPLRandom_*` 접근자 [S: `src/matched/func_020fded0.c`] |
| `AOSS_RandState` / `AOSS_RandInited` | `{x, a, c}`와 한 번 초기화 플래그 | `AOSS_Rand` | `AOSS_Rand` [S: `src/matched/AOSS_Rand.c`] |
| `0x04000100` (틱) | 모든 네트워크 시드가 접어 넣는 엔트로피 | 타이머 0 (포트: `acww_tick_advance`) | `OS_GetTick` [S: `src/matched/OS_GetTick.c`] |
| `0x04000006` (VCOUNT) | 엔트로피 풀의 여덟 입력 중 하나 | 디스플레이 컨트롤러 (포트: DISPSTAT/VCOUNT 훅) | `OS_GetLowEntropyData` [S: `src/matched/OS_GetLowEntropyData.c`] |

## 확인 방법

`../experiments/rng-determinism.md`(설계만 됨, 아직 미실행): 같은 고정 시계로 같은 레시피를
두 번 실행해 스크린샷이 바이트 단위로 동일함을 확인한 뒤, `ACWW_RTC_TIME`을 1초 옮겨 무엇이든
움직이는지 본다. 이는 "포트가 결정론적이다"와 "이 씬에서는 시계로 시드된 추출을 소비하는
것이 없다"를 분리하는데, 기존 실행으로는 불가능한 일이다.

## 가설

- **확정됨 (ORACLE46).** "게임플레이 RNG는 위 세 개 모두와 구별되는 네 번째 생성기로,
  디컴파일되지 않은 `func_020*` 게임 글루 코드 안에 있다." 그것은 상태 워드 `0x021cb5a0`에
  대한 `func_020e92e8`이며, 검색이 이를 놓친 이유는 곱셈-덧셈이 상태를 정적 워드가 아니라
  호출자가 넘기는 포인터로 받는 세 줄짜리 매칭 파일 안에 있기 때문이다.
- 마을의 배치는 세이브에 저장된 시드로부터 생성된다. 같은 고정 시계 아래 두 개의 새
  `ACWW_SAVE` 파일로 같은 실행을 두 번 하여 확정한다: 동일한 마을이면 시드는 세이브별이
  아니고, 다른 마을이면 세이브별이다 (`save-data.md`가 먼저 지속되어야 한다). ORACLE46은
  첫 번째 쪽으로 기운다: 상태는 부팅 시 시계로부터 시드되며 세이브에서 읽는 것은 없다.
- **측정된 조건들에 대해 확정됨: 부팅 초를 공유해도 공유 마을이 보장되지 않는다.**
  ORACLE46의 생성자들은 시드를 공유하지만 서로 다른 스트림 위치에서 서로 다른 id를 뽑는다
  [E: `scratchpad/oracle46/RECEIPTS.md`; log: `docs/log/cycle41-gameplay.md` O46-4].
  id만 맞추는 것도 나중의 배치/명단 버스트를 고정하지 않는다: 역방향 조건은
  거기에 두 추출 일찍 진입하는 반면, 정방향 레시피는 지도와 명단을 맞춘다
  [E: `scratchpad/oracle49/RECEIPTS.md`; log: `docs/log/cycle41-gameplay.md` O49-2, O49-4, O49-5].
- `OS_GetLowEntropyData`는 이 ROM에서 죽은 코드다. 전체 마을 실행에 걸쳐 그 진입 주소에
  `ACWW_WATCH`를 걸어 확정한다.
- 포트의 프레임 계수 틱과 에뮬레이터의 사이클 정확 틱은 네트워크 생성기를 다르게 시드하며,
  네트워크 코드가 실행되지 않으므로 상관없다
  [E: no DWC or WM symbol is reached on any recorded run; see `network.md`].

## 관련 문서

- `time-and-rtc.md` -- 두 엔트로피 소스.
- `save-data.md` -- 세이브 체크섬과 뱅크 수용 [S: `port/shim/game/savepoll.c`; log: `docs/log/cycle41-gameplay.md` GP45-5].
- `network.md` -- 모든 SDK 생성기의 유일하게 확립된 소비자.

## 누가 뽑는가 (`draw-caller-1`)

`promote_record.py`의 커스텀 START 레시피는 레코더 비활성, 고정 RTC, 터치 없음,
포트 프레임 3000에서 정지(종료 코드 100)한 상태에서 **744회 저장: 시드 저장 2회와 추출 742회**를
낸다. 호출자 워치는 97개의 서로 다른 키를 가지며 오버플로는 없다; 모든 반환 주소는
심볼에 대응하며, 오버레이 상주 여부는 그 실행의 로드 로그에서 취했다
[E: `scratchpad/handoff/draw-caller-1/census.receipt.json`, `scratchpad/handoff/draw-caller-1/census-summary.json`].

범위 제한 RNG의 리프 저장에서 LR은 `func_020e92d0` 안의 `0x020e92dc`이며; `sp+4`에 검증된
저장 LR이 생성자를 말해 준다. `func_020644cc`는 그 범위 제한 추출을 꼬리 호출하므로
스택 프레임을 더하지 않는다. 반면 원시 리프 호출은 LR에서 직접 호출자를 식별한다;
LR2=0은 사용 불가를 뜻하지 주소 0의 호출자를 뜻하지 않는다
[S: `port/interp/interp_cpu.c` `watch_lr_parent`; E: `scratchpad/handoff/draw-caller-1/fixture-run.stdout.log`].

**주기적 호출은 `func_ov068_0226c520`, 반환 주소 `0x0226c52d`다: 828, 831, ..., 1179에서
118회 추출, 정확히 세 프레임에 한 번.** 그 첫 표현식은 호출마다 무조건 범위 5 값을
한 번 뽑으며; 이후의 분기는 그 지점을 반복하지 않는다
[S: `src/matched/func_ov068_0226c520.cpp`; E: `scratchpad/handoff/draw-caller-1/caller-events.json`].
브리프의 라벨 "title, 759..1600"은 이 레시피의 씬 구획이 아니다: ORACLE47은
759..780을 남은 타이틀(우리 센서스도 거기서 추출 0을 찾는다)로, 780..1610을
택시 대화로 부른다. 주기적 지점은 다른 생성자들과 함께 그 대화의 일부를 덮는다;
요청된 전체 창의 모든 프레임에 추출이 하나씩 있다는 뜻은 아니다
[E: `docs/log/cycle41-gameplay.md` O47-1; `scratchpad/handoff/draw-caller-1/census-summary.json`].

**프레임 758 버스트는 45개 함수의 61개 반환 지점에 퍼진 280회 추출이다.** 여기에는
마을 id 추출(`func_0206426c`)과 아래에 나열된 초기 선택기들이 포함되며; 하나의 직접
생성자에 대한 280회 호출이 아니다. 가장 큰 직접 그룹은 `func_0209ccd4`다: 두 반환 지점에서
27+9회 추출. 별도로 완료된 캡처는 **한 번의 호출에서 36회 추출**을 측정하며,
이는 그 6x6 선택 루프와 일치한다
[S: `src/matched/func_0209ccd4.c`; E: `scratchpad/handoff/draw-caller-1/probe-summary.json`].
광범위한 초기화기 `func_0209ebec`는 `0x0209e76c`에서 `func_0209e6ec`로부터 진입되지만,
기존 레코더는 반환을 관측하기 전에 이벤트 상한과 400만 스텝 상한에 걸린다;
그 프로브는 280회 추출 전부를 하나의 감싸는 호출에 배정할 수 없다. 아래의 정확한 집계는
직접 호출 지점 기준이며; 감싸는 초기화기의 완전한 호출 횟수는 열린 문제로 남는다
[E: `scratchpad/handoff/draw-caller-1/probe-summary.json`].

모든 행은 `0x021cb5a0`을 폭 4로 감시한다. PC는 추출의 경우 `0x020e92f8`, 처음 두 시드 행의
경우 `0x020e930c`다. "758"은 그 프레임만 세고; "합계"는 0..3000을 덮는다.
함수 열은 가능하면 LR2 소유자를, 아니면 LR 소유자를 적는다; 주소는
Thumb 반환 비트를 유지한다. 모든 행은 [E: `scratchpad/handoff/draw-caller-1/census-summary.json`, frames 0..3000]에서 측정되었다.

| LR | LR2 | 생성자 함수 | 합계 | 첫 프레임 | 758 |
|---|---|---|---:|---:|---:|
| `0x020c5a85` | `0x00000000` | `__sinit_020c5a78` | 1 | 0 | 0 |
| `0x02061541` | `0x00000000` | `func_02061530` | 1 | 3 | 0 |
| `0x020e92dc` | `0x0204126f` | `func_020411fc` | 3 | 758 | 2 |
| `0x020e92dc` | `0x020ae69b` | `func_020ae67c` | 6 | 758 | 4 |
| `0x020e92dc` | `0x020ae05b` | `func_020ae03c` | 6 | 758 | 4 |
| `0x020e92dc` | `0x0206399f` | `func_02063914` | 21 | 758 | 15 |
| `0x020e92dc` | `0x02063a9f` | `func_02063914` | 21 | 758 | 15 |
| `0x020e92dc` | `0x020ae0d9` | `func_020ae03c` | 12 | 758 | 8 |
| `0x020e92dc` | `0x02063fe3` | `func_02063f94` | 8 | 758 | 7 |
| `0x020e92dc` | `0x020ae163` | `func_020ae03c` | 6 | 758 | 4 |
| `0x020e92dc` | `0x0204111b` | `func_02041110` | 12 | 758 | 8 |
| `0x020e92dc` | `0x020410bd` | `func_0204105c` | 6 | 758 | 4 |
| `0x020e92dc` | `0x020ae1c5` | `func_020ae190` | 3 | 758 | 2 |
| `0x020e92dc` | `0x0204e73b` | `func_0204e728` | 1 | 758 | 1 |
| `0x020e92dc` | `0x0209c5c1` | `func_0209c5b0` | 4 | 758 | 4 |
| `0x020e92dc` | `0x0209c7b5` | `func_0209c618` | 4 | 758 | 4 |
| `0x020e92dc` | `0x0209c8a5` | `func_0209c80c` | 4 | 758 | 4 |
| `0x020e92dc` | `0x0209cbbf` | `func_0209cb88` | 12 | 758 | 12 |
| `0x020e92dc` | `0x0209cb13` | `func_0209ca6c` | 1 | 758 | 1 |
| `0x020e92dc` | `0x0209cd37` | `func_0209ccd4` | 27 | 758 | 27 |
| `0x020e92dc` | `0x0209cd99` | `func_0209ccd4` | 9 | 758 | 9 |
| `0x020e92dc` | `0x02064277` | `func_0206426c` | 1 | 758 | 1 |
| `0x020e92dc` | `0x0207cc67` | `func_0207cc54` | 15 | 758 | 15 |
| `0x020e92dc` | `0x0207c97b` | `func_0207c8c8` | 3 | 758 | 3 |
| `0x020e92dc` | `0x0209c4ef` | `func_0209c4a8` | 3 | 758 | 3 |
| `0x020e92dc` | `0x0207f439` | `func_0207f414` | 3 | 758 | 3 |
| `0x020e92dc` | `0x0207d67f` | `func_0207d634` | 3 | 758 | 3 |
| `0x020e92dc` | `0x0207bcab` | `func_0207bbb8` | 3 | 758 | 3 |
| `0x020e92dc` | `0x020b38e9` | `func_020b38dc` | 1 | 758 | 1 |
| `0x020e92dc` | `0x020b38f5` | `func_020b38dc` | 1 | 758 | 1 |
| `0x020e92dc` | `0x020b3935` | `func_020b38dc` | 3 | 758 | 3 |
| `0x020e92dc` | `0x020b398f` | `func_020b38dc` | 1 | 758 | 1 |
| `0x020e92dc` | `0x020b388b` | `func_020b3880` | 1 | 758 | 1 |
| `0x020e92dc` | `0x02064113` | `func_02064108` | 9 | 758 | 9 |
| `0x020e92dc` | `0x0204ce73` | `func_0204ce64` | 1 | 758 | 1 |
| `0x020e92dc` | `0x0204cc57` | `func_0204cc34` | 1 | 758 | 1 |
| `0x020e92dc` | `0x02048433` | `func_02048418` | 1 | 758 | 1 |
| `0x020e92dc` | `0x0204843b` | `func_02048418` | 1 | 758 | 1 |
| `0x020e92dc` | `0x02048445` | `func_02048418` | 3 | 758 | 3 |
| `0x020e92dc` | `0x02048459` | `func_02048418` | 3 | 758 | 3 |
| `0x020e92dc` | `0x02048d43` | `func_02048d2c` | 12 | 758 | 12 |
| `0x020e92dc` | `0x020483e1` | `func_020483c4` | 1 | 758 | 1 |
| `0x020e92dc` | `0x020483e9` | `func_020483c4` | 1 | 758 | 1 |
| `0x020e92dc` | `0x02048b9f` | `func_02048b54` | 4 | 758 | 4 |
| `0x020e92dc` | `0x02048c6f` | `func_02048bc0` | 22 | 758 | 22 |
| `0x020e92dc` | `0x02048b29` | `func_02048b0c` | 2 | 758 | 2 |
| `0x020e92dc` | `0x02048b31` | `func_02048b0c` | 2 | 758 | 2 |
| `0x020e92dc` | `0x020482af` | `func_02048298` | 4 | 758 | 4 |
| `0x020e92dc` | `0x02048325` | `func_0204830c` | 4 | 758 | 4 |
| `0x020e92dc` | `0x020c15dd` | `func_020c15c8` | 2 | 758 | 2 |
| `0x020e92dc` | `0x020875b7` | `func_02087500` | 1 | 758 | 1 |
| `0x020e92dc` | `0x020875cd` | `func_02087500` | 1 | 758 | 1 |
| `0x020e92dc` | `0x020877eb` | `func_020877dc` | 12 | 758 | 12 |
| `0x020e92dc` | `0x0203a615` | `func_0203a5f4` | 3 | 758 | 3 |
| `0x020e92dc` | `0x02086ef5` | `func_02086ee8` | 1 | 758 | 1 |
| `0x020e92dc` | `0x02086f13` | `func_02086ee8` | 1 | 758 | 1 |
| `0x020e92dc` | `0x02086f1b` | `func_02086ee8` | 1 | 758 | 1 |
| `0x020e92dc` | `0x02086f23` | `func_02086ee8` | 1 | 758 | 1 |
| `0x020e92dc` | `0x0207a0a9` | `func_0207a02c` | 2 | 758 | 2 |
| `0x020e92dc` | `0x0204711f` | `func_02047114` | 8 | 758 | 8 |
| `0x020e92dc` | `0x02087fc9` | `func_02087f58` | 1 | 758 | 1 |
| `0x020e92dc` | `0x020878eb` | `func_0208786c` | 1 | 758 | 1 |
| `0x020e92dc` | `0x020879bd` | `func_02087950` | 1 | 758 | 1 |
| `0x020e92dc` | `0x020bb91f` | `func_020bb8e0` | 2 | 822 | 0 |
| `0x020e92dc` | `0x020b1795` | `func_020b177c` | 5 | 822 | 0 |
| `0x020e92dc` | `0x0202e387` | `func_0202e364` | 2 | 822 | 0 |
| `0x020e92dc` | `0x0226d441` | `func_ov068_0226d408` | 2 | 822 | 0 |
| `0x020e92dc` | `0x0226cbd3` | `func_ov068_0226cbc8` | 2 | 822 | 0 |
| `0x020e92dc` | `0x0226ca45` | `func_ov068_0226ca2c` | 2 | 822 | 0 |
| `0x020e92dc` | `0x0201324f` | `func_020131dc` | 2 | 822 | 0 |
| `0x020e92dc` | `0x02082943` | `func_02082904` | 1 | 823 | 0 |
| `0x020e92dc` | `0x0226c52d` | `func_ov068_0226c520` | 118 | 828 | 0 |
| `0x02064627` | `0x00000000` | `func_0206461c` | 22 | 828 | 0 |
| `0x020e92dc` | `0x020645fd` | `func_020645e0` | 22 | 828 | 0 |
| `0x020e92dc` | `0x0204fbb3` | `func_0204fb80` | 7 | 828 | 0 |
| `0x020e92dc` | `0x02227947` | `func_ov003_0222793c` | 13 | 828 | 0 |
| `0x0226bcd9` | `0x00000000` | `func_ov068_0226bc1c` | 8 | 831 | 0 |
| `0x020e92dc` | `0x02012aa9` | `func_02012a98` | 2 | 849 | 0 |
| `0x02012adf` | `0x00000000` | `func_02012a98` | 2 | 849 | 0 |
| `0x020e92dc` | `0x02012af9` | `func_02012a98` | 2 | 849 | 0 |
| `0x020e92dc` | `0x02012b05` | `func_02012a98` | 2 | 849 | 0 |
| `0x020e92dc` | `0x02012b0f` | `func_02012a98` | 2 | 849 | 0 |
| `0x020e92dc` | `0x020b1831` | `func_020b1800` | 9 | 921 | 0 |
| `0x020e92dc` | `0x020b183d` | `func_020b1800` | 9 | 921 | 0 |
| `0x020e92dc` | `0x020b184f` | `func_020b1800` | 8 | 948 | 0 |
| `0x020e92dc` | `0x0222d399` | `func_ov003_0222d388` | 1 | 1005 | 0 |
| `0x020e92dc` | `0x0222d129` | `func_ov003_0222cf60` | 1 | 1005 | 0 |
| `0x020e92dc` | `0x0222c69b` | `func_ov003_0222c68c` | 1 | 1005 | 0 |
| `0x020e92dc` | `0x02230c4f` | `func_ov003_02230c3c` | 1 | 1011 | 0 |
| `0x020e92dc` | `0x02230ccb` | `func_ov003_02230cc0` | 1 | 1011 | 0 |
| `0x020e92dc` | `0x02230c87` | `func_ov003_02230c3c` | 1 | 1011 | 0 |
| `0x020e92dc` | `0x020950df` | `func_020950d4` | 1 | 1182 | 0 |
| `0x020e92dc` | `0x0226dc97` | `func_ov068_0226dc64` | 51 | 1188 | 0 |
| `0x020e92dc` | `0x0226dc3b` | `func_ov068_0226dc08` | 59 | 1188 | 0 |
| `0x020e92dc` | `0x020bb7c5` | `func_020bb7a0` | 1 | 1194 | 0 |
| `0x020e92dc` | `0x0226daf3` | `func_ov068_0226dabc` | 23 | 1230 | 0 |
| `0x020e92dc` | `0x0201a7a3` | `func_0201a798` | 46 | 1392 | 0 |
