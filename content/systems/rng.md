# 난수
<!-- source: wiki/systems/rng.md -->

**요약.** 이 ROM에는 단일한 난수 생성기가 없다. 매칭된 소스에는 서로 무관한 세 개의 선형
합동 생성기(LCG)가 있다: 네트워킹 코드가 사용하는 NitroSDK의 `MATH_Rand16`과 `MATH_Rand32`;
시각적 흔들림에 사용되는 SPL 파티클 라이브러리 자체의 생성기; 그리고 Wi-Fi 설정 오버레이의
독자적인 생성기. 이들 모두는 하드웨어 틱 카운터, 실시간 시계, 또는 둘 다로부터 시드된다.
**게임 자체가 게임플레이 결과 -- 물고기, 곤충, 주민, 상점 재고 -- 에 사용하는 생성기는 아직
발견되지 않았다.** 그것을 소비할 함수들이 아직 디컴파일되지 않았기 때문이다. 이 페이지는
확립된 것을 기록하며 그 구멍에 대해 명시적으로 밝힌다.

## 무슨 일이 일어나는가

**이 페이지에 필요한 명명 주석.** `MATH_Rand16`, `MATH_Rand32`, `MATH_InitRand16/32`,
`OS_IsTickAvailable`은 NitroSDK 라이브러리 이름이지 이 ROM의 심볼 테이블에 있는 이름이
아니다: 어떤 `config/adm-kr/arm9/**/symbols.txt`에도 그런 심볼은 존재하지 않으며, 이들 모두는
`src/matched/`에서 `func_*` 이름으로 도달된다 [S: `config/adm-kr/arm9/**/symbols.txt`, name sweep].
`../STYLE.md` 규칙 2가 SDK 이름을 허용하기 때문에 여기서는 그 이름을 사용하며, `func_*` 이름이
존재하는 곳에서는 함께 병기한다.

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
`randomSeed`, `worldSeed`, `townSeed` 등을 검색해도 아무것도 나오지 않으며, 관측된 모든 시딩은
세션 한정이거나, 세이브 블록에 기록되거나 거기서 복원되는 모습이 한 번도 보이지 않는 단일
지연 초기화 전역 변수다 [S: absence in `src/matched`]. 이것은 게임이 아니라 코퍼스에 대한
진술이다: 마을별 시드를 소비할 법한 게임플레이 시스템 -- 주민 행동, 물고기와 곤충 스폰, 상점
재고, 마을 자체의 배치 -- 은 `src/matched`에 전혀 디컴파일되어 있지 않으므로, 그 RNG 배관은
단순히 아직 보이지 않는다.

세이브 체크섬의 증거도 없다. 코퍼스의 모든 `crc`/`checksum` 심볼
(`0x02128ac4`의 `MATH_CalcCRC8`, 다항식 `0xA001`의 `0x02128a90` `MATH_CalcCRC16`,
다항식 `0xEDB88320`과 반전 출력의 `0x02128a58` `MATH_CalcCRC32`, 그리고
`MBi_calc_cksum`과 `check_tcpudpsum`)은 무선, 소켓 또는 PPP/TCP 스택에 속하며, 그중 어느
것에서도 세이브 경로로 이어지는 호출 간선이 없다 [S: absence of call edges in
`src/matched`; see `save-data.md`].

### 포트

포트는 이 생성기들 중 어느 것도 건드리지 않는다: 이들은 ROM 코드이며 나머지와 마찬가지로
인터프리트되어 실행된다 [E: `docs/kb/hybrid/runtime.md`'s registry policy; `scratchpad/cycle40/runs/tap-D56`].
포트의 유일한 관련 효과는 두 엔트로피 소스가 *고정*된다는 것이다. 틱은 0부터 프레임당
정확히 8,728 카운트씩 진행하고 [E: `port/platform/tick.c`], RTC는 고정된 순간이다
[E: `port/shim/os/rtcclock.c`]. 따라서 포트 실행은 어느 쪽에서든 시드되는 모든 생성기에서
결정론적이며, 이것이 프레임 단위 오라클 비교를 애초에 의미 있게 만드는 것이다
[O: `scratchpad/oracle/tap-fullpad/compare-vs-tap-D56.txt`, where the two producers agree to
whole-frame ncc 0.9920-0.9959 from 6000 to 24000].

## 어디에 있는가

| 함수 또는 심볼 | 모듈 | 역할 | 등급/출처 |
|---|---|---|---|
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
| `MATH_CalcCRC8` / `CalcCRC16` / `CalcCRC32` | autoload_2 | CRC 헬퍼; 세이브가 아니라 네트워크 스택이 사용 | [S: `src/matched/MATH_CalcCRC32.c`] |

## 읽고 쓰는 데이터

| 주소 또는 필드 | 의미 | 쓰는 쪽 | 읽는 쪽 |
|---|---|---|---|
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

- 게임플레이 RNG는 위 세 개 모두와 구별되는 네 번째 생성기로, 디컴파일되지 않은 `func_020*`
  게임 글루 코드 안에 있다. ov004 또는 main 게임 코드 안에서 정적 워드에 대한 곱셈-덧셈의
  호출자를 찾아 확정하며, `src/matched`의 어떤 검색도 아직 이를 찾아내지 못했다
  [S: absence].
- 마을의 배치는 세이브에 저장된 시드로부터 생성된다. 같은 고정 시계 아래 두 개의 새
  `ACWW_SAVE` 파일로 같은 실행을 두 번 하여 확정한다: 동일한 마을이면 시드는 세이브별이
  아니고, 다른 마을이면 세이브별이다 (`save-data.md`가 먼저 지속되어야 한다).
- `OS_GetLowEntropyData`는 이 ROM에서 죽은 코드다. 전체 마을 실행에 걸쳐 그 진입 주소에
  `ACWW_WATCH`를 걸어 확정한다.
- 포트의 프레임 계수 틱과 에뮬레이터의 사이클 정확 틱은 네트워크 생성기를 다르게 시드하며,
  네트워크 코드가 실행되지 않으므로 상관없다
  [E: no DWC or WM symbol is reached on any recorded run; see `network.md`].

## 관련 문서

- `time-and-rtc.md` -- 두 엔트로피 소스.
- `save-data.md` -- 마을별 시드가 있을 법한 곳, 그리고 체크섬이 발견되지 않은 이유.
- `network.md` -- 모든 SDK 생성기의 유일하게 확립된 소비자.
