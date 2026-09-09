# 감사(audit): SDK 계층의 `func_XXXXXXXX`에 이름 붙이기
<!-- source: wiki/audits/sdk-names.md -->

**요약.** ROM의 `autoload_2` 대역(`0x020e8840`..)과 `itcm`은 거의 전부가
NitroSDK 2.2a / NITRO-System `NNS_Library-20050901` 라이브러리 코드이며, 그 중 대략 절반이
`config/adm-kr/arm9/**/symbols.txt`에서 익명 상태이다. 이 감사는 저장소에 어떤 코드도 읽어 들이거나
복사하지 않고, 공개 라이브러리 소스만으로 그 주소 중 74개의 이름을 복원한다. 지렛대는 링크 순서의
규칙성이다: **하나의 라이브러리 번역 단위(translation unit) 안에서, ROM의 함수들은 공개 소스 파일의
순서를 정확히 뒤집은 오름차순 주소 순서로 나타난다.** 같은 소스 파일에서 온 이름 있는 이웃 둘이
주어지면, 그 사이의 익명 함수들은 그 둘 사이에 있는 소스 함수들을 거꾸로 읽은 것이다. 모든 행은
파일 URL과 함께 **P**(공개 소스) 등급이 매겨지고, 신뢰도가 덧붙는다.

이 방법은 블라인드로 검증되었다: 이 방법이 이름 붙인 주소 중 일곱 개는 이미 이 저장소 안에서
독립적으로 확립된 정체를 갖고 있으며(`src/matched/` 헤더, `port/shim/gfx/sbcnames.c`,
`port/shim/gfx/g2d_charcanvas_obj1d.c`), 방법은 그 일곱 개를 모두 재현했다. 그 행들은 새 이름으로
취급하지 않고 교차 확인됨(cross-confirmed)으로 표시한다.

기계 판독용 행: `wiki/audits/sdk-names.tsv` (주소, 제안 이름, 라이브러리, 소스 URL, 신뢰도).

---

## 1. 순서 규칙과 그 근거

`src/matched/<name>.c` 헤더는 이미 이름이 붙은 많은 함수에 대해 실제 라이브러리 파일을 명시한다
(예: `Real source: NitroSDK 2.2a (20050826) build/libraries/os/common/src/os_alarm.c`).
한 모듈의 `symbols.txt`를 주소순으로 정렬하고 이름 있는 각 함수에 소스 파일을 주석으로 달면
번역 단위 단위의 연속 구간(run)이 그림처럼 드러난다. 각 구간 안에서 순서는 소스 순서의 역순이다.
세 개의 독립적인 사슬이 이를 보여준다:

- **`os/src/os_thread.c`** — ROM 오름차순: `OS_SetSwitchThreadCallback`,
  `OSi_SleepAlarmCallback`, `func_0211482c`, `OS_GetThreadPriority`, `OS_SetThreadPriority`,
  `OS_GetStackStatus`, `OS_YieldThread`, `OS_RescheduleThread`, `OS_SelectThread`,
  `OS_WakeupThreadDirect`, `OS_WakeupThread`, `OS_SleepThread`. 공개 소스 줄 번호:
  1150, 1139, ?, 1109, 1069, 996, 890, 883, 872, 854, 809, 773 — 엄격한 내림차순
  [P: <https://github.com/ntrtwl/NitroSDK/blob/main/libraries/os/src/os_thread.c>].
- **`snd/src/snd_command.c`** — ROM 오름차순 `InitPXI`, `SND_CountWaitingCommand`,
  `SND_CountReservedCommand`, `SND_CountFreeCommand`, `SND_IsFinishedCommandTag`,
  `SND_GetCurrentCommandTag`, `SND_WaitForCommandProc`, `SND_FlushCommand`,
  `SND_PushCommand`, `SND_AllocCommand`, `SND_RecvCommandReply`, `SND_CommandInit`
  = 소스 줄 605, 397, 381, 365, 342, 327, 281, 212, 191, 156, 112, 61
  [P: <https://github.com/ntrtwl/NitroSDK/blob/main/libraries/snd/src/snd_command.c>].
- **`g3d/src/model.c`** — ROM 오름차순 `NNS_G3dMdlSetMdlAlpha`, `...SetMdlPolygonID`,
  `...SetMdlLightEnableFlag`, `...SetMdlEmi`, `...SetMdlDiff`,
  `NNSi_G3dModifyPolygonAttrMask`, `NNSi_G3dModifyMatFlag` = 소스 줄 167, 152, 107,
  92, 47, 25, 3 [P: <https://github.com/ntrtwl/NitroSystem/blob/main/libraries/g3d/src/model.c>].

두 가지 귀결이 이 규칙을 실제로 쓸 수 있게 만든다:

1. **번역 단위의 경계는 소스 줄 번호 수열이 다시 시작하는 지점이다.** 한 TU의 첫 ROM 함수는
   그 소스 파일의 *마지막* 함수이다.
2. **빠진 함수는 데드 스트립(dead-strip)된 것이지, 순서가 바뀐 것이 아니다.** 관측된 모든 구간은
   뒤집힌 소스 순서의 부분 수열이므로, 익명 슬롯의 후보 집합은 정확히 그 두 이름 있는 이웃 사이에
   엄격히 놓이는 소스 함수들이다.

### 이 감사에서 발견한 두 가지 예외

- **ITCM은 소스 순서가 아니다 — 심볼 이름의 알파벳순이다.** `CP_RestoreContext`,
  `CP_SaveContext`, `OS_DisableIrqMask`, `OS_EnableIrqMask`, `OS_LoadContext`,
  `OS_ResetRequestIrqMask`, `OS_SaveContext`, `OS_SetIrqMask`, `OSi_IrqCallback`,
  `OSi_IrqDma2`, `OSi_IrqDma3`, `OSi_IrqTimer0..3`; 뒤이어 `MI_SendGXCommandAsync`,
  `MI_WaitDma`, `MIi_CheckDma0SourceAddress`, `MIi_DMACallback`, `MIi_DmaSetParams`,
  `MIi_FIFOCallback`. ITCM에서 이웃 제약은 소스 줄이 아니라 *이름*에 걸리며, 이는 훨씬 약하다 —
  하지만 바로 그것이 `OSi_IrqDma0` / `OSi_IrqDma1`을 못 박는다.
- **`asm` 함수는 수열에서 벗어난다.** `OSi_AlarmHandler`(`0x02116498`, 0x10)는 소스가 두는 위치인
  `OSi_ArrangeTimer`와 `OS_CancelAlarm` 사이가 아니라 `os_alarm.c` 구간의 머리에 놓인다;
  `src/matched/OSi_AlarmHandler.c`는 이를 그 파일에서 옮겨 적은 손으로 작성한 `asm void`로
  기록한다. `asm`으로 선언된 SDK 함수는 순서가 없는 것으로 취급한다.

### 이 규칙이 할 수 없는 것

이 규칙은 후보의 *집합*을 주며, 항상 유일한 이름을 주지는 않는다. 크기가 비슷한 두 소스 함수가
같은 두 이름 있는 이웃 사이에 놓이고 그 중 하나만 링크에서 살아남은 경우, 크기와 호출 대상(callee)으로
판가름해야 한다; 그것으로도 판가름할 수 없으면 그 행은 `low` 등급을 받고 함수가 아니라 계열(family)의
이름을 적는다. 크기는 `symbols.txt`에서 온다; 대역 전체에 걸쳐 성립한 대략적인 규칙은 `-O4,p`에서
문장당 약 4바이트이며, 한 줄짜리 setter/getter는 0x8-0x20이다.

---

## 2. 계열별 커버리지

| 계열 | 발견된 익명 함수 | 여기서 이름 붙임 | 비고 |
|---|---|---|---|
| OS 스레드 / 알람 / valarm / 틱 / printf | 9 | 9 | 알람과 스레드 파일은 그 외에는 완전히 이름이 붙어 있다 |
| MI DMA / 압축 해제 | 0 | 0 | **이미 완료** — 아래 참조 |
| FS / CARD | 6 | 6 | 하나는 새 이름이 아니라 정정이다 |
| SND (SDK `snd_*`) | 0 | 0 | **이미 완료** — 아래 참조 |
| TP / PM / RTC | 5 | 5 | TP는 완전히 이름이 붙어 있다; PM과 RTC는 각각 동기 래퍼가 빠져 있다 |
| NNS Fnd (힙 / 아카이브) | 4 | 4 | |
| NNS G3D (kernel, glbstate, sbc, model, binres, anm) | 18 | 18 | 그 중 4개는 계열 수준까지만 |
| NNS G2D (font, char canvas) | 3 | 3 | |
| NNS Snd (main, player, sndarc_stream) | 23 | 23 | stream의 static 함수들이 가장 큰 깨끗한 구간이다 |
| DGT / math | 1 | 1 | 낮은 신뢰도 |

**MI는 대상이 아니다.** `autoload_2`의 `0x02116e98`과 `0x02117c10` 사이에 있는 모든 `MI_*` / `MIi_*`
함수는 이미 이름을 갖고 있다: `MI_SetWramBank`, `MIi_CheckAnotherAutoDMA`,
`MI_StopDma`, `MI_DmaCopy32Async`, `MI_DmaFill32Async`, `MI_DmaCopy16`, `MI_DmaCopy32`,
`MI_DmaFill32`, `MIi_DMAFastCallback`, `MI_SendGXCommandAsyncFast`, `MIi_Cpu*` 블록,
`MI_Copy32B/36B/48B/64B`, `MI_CpuFill8`, `MI_CpuCopy8`, `MI_Zero36B`, `MI_SwapWord`,
`MI_UncompressLZ8`, `MIi_CardDmaCopy32`, `MI_ReadUncompLZ8`, `MI_InitUncompContextLZ`,
`SearchLZ`, `MI_CompressLZ`, `MI_Init`. 게임이 실제로 사용하는 압축 해제 진입점은
`config/adm-kr/arm9/symbols.txt`에 이름이 붙어 있는 ARM7 BIOS SWI들이다
(`LZ77UnCompReadNormalWrite8bit`, `HuffUnCompReadByCallback`,
`RLUnCompReadByCallbackWrite16bit`, `BitUnPack`). 제안할 것이 없다.

**SDK SND 명령 계열 역시 대상이 아니다.** `0x02117c10`..`0x02119380`은
`snd_interface.c`, `snd_main.c`, `snd_command.c`, `snd_alarm.c`, `snd_work.c`, `snd_util.c`,
`snd_bank.c`이며 익명 구성원이 없다. 남은 SND 작업은 전부 NITRO-System의
`libraries/snd/`에 있으며, 8절에서 다룬다.

**`main`(arm9 static, `0x02000000`..`0x020e8840`)은 대상이 아니다.** 여기에는 16,741개의 함수
심볼이 있고 이름은 139개뿐이지만, 그 중 97개는 BIOS/SWI 썽크이고 나머지는 게임 진입점이다;
이웃 논증이 작동할 SDK 대역이 거기에는 없다. `main`에서 SDK 이름 붙이기는 아무것도 얻지 못한다.

---

## 3. OS: 스레드, 알람, 타이머, printf

이웃과 소스 순서는
<https://github.com/ntrtwl/NitroSDK/blob/main/libraries/os/src/> 기준이다.

| 주소 | 크기 | 제안 | 근거 | 신뢰도 |
|---|---|---|---|---|
| `0x0211482c` | 0x9c | `OS_Sleep` | `OSi_SleepAlarmCallback`(1139)과 `OS_GetThreadPriority`(1109) 사이; 그 틈에 있는 소스 함수는 `OS_Sleep`(1115)뿐이고, 바로 그 콜백을 설치하는 함수이다 [P: `os_thread.c`] | high |
| `0x02114e1c` | 0x74 | `OSi_KillThreadWithPriority` | `OS_KillThread`(626)와 `OSi_ExitThread_Destroy`(498) 사이; `OS_KillThread`는 0x30으로 얇은 래퍼 형태이므로, 그 0x74 헬퍼가 본체이다 [P: `os_thread.c`] | medium |
| `0x021145d4` | 0x30 | `OS_SNPrintf` | `OS_VSNPrintf`(399)와 `OS_VSPrintf`(384) 사이; 0x30은 `0x0211461c`와 공유하는 가변 인자 전달 형태이다 [P: `os_printf.c`] | high |
| `0x0211461c` | 0x30 | `OS_SPrintf` | `OS_VSPrintf`(384)와 `string_put_string`(358) 사이; 그 틈에는 `OS_SPrintf`(374)만 놓인다 [P: `os_printf.c`] | high |
| `0x02114740` | 0x10 | `OS_PutStringInit` | `os_printf.c` 구간의 마지막 함수이므로 소스 파일의 첫 함수; 후보 집합은 `OS_PutStringInit`(54) / `OS_PutStringPrnSrv`(279)이며 슬롯은 하나만 살아남았다 [P: `os_printf.c`] | medium |
| `0x021163ec` | 0x10 | `OS_IsTickAvailable` | `OSi_CountUpTick`(42)과 `OS_InitTick`(16) 사이; `OS_IsTickAvailable`(37)이 유일한 후보이고 한 줄짜리 플래그 읽기이다 [P: `os_tick.c`] | high |
| `0x02116528` | 0x8 | `OS_SetAlarmTag` | `OS_CancelAlarms`(309)와 `OSi_ArrangeTimer`(248) 사이; `OS_SetAlarmTag`(300)는 단일 대입문이고 0x8은 정확히 그것이다 [P: `os_alarm.c`] | high |
| `0x021166e0` | 0x78 | `OS_SetAlarm` | `OS_CancelAlarm`(198)과 `OSi_InsertAlarm`(94) 사이; 후보는 `OS_SetAlarm`(144)과 `OS_SetPeriodicAlarm`(170), 슬롯은 하나. 호출자 쪽에서 흔히 쓰는 진입점이라 `OS_SetAlarm`을 우선한다 [P: `os_alarm.c`] | medium |
| `0x021168a8` | 0x10 | `OS_IsAlarmAvailable` | `OS_CreateAlarm`(85)과 `OS_InitAlarm`(43) 사이; 후보는 `OS_IsAlarmAvailable`(80, 한 줄)과 `OS_EndAlarm`(60, 루프); 0x10이 전자를 고른다 [P: `os_alarm.c`] | high |
| `0x02116a1c` | 0x80 | `OSi_VCountArr` | `os_valarm.c` 구간의 꼬리, 즉 소스 파일의 첫 함수; 유일한 후보이지만 0x80은 그것치고 크고, 공개 파일이 ROM의 리비전이 아닐 수 있다 [P: `os_valarm.c`] | low |

`OSi_IrqDma0` / `OSi_IrqDma1`(`0x01ff82f8`, `0x01ff8308`, 각 0x10)은 ITCM 알파벳순 구간에서
온다: 이들은 동일한 0x10 심(shim)인 `OSi_IrqDma2`와 `OSi_IrqDma3` 바로 앞에 놓이고,
`os_irqTable.c`는 정확히 `OSi_IrqDma0..3`을 선언한다 [P:
<https://github.com/ntrtwl/NitroSDK/blob/main/libraries/os/src/os_irqTable.c>]. 이 쌍에 대한
신뢰도는 high이다; 0 다음 1의 배정은 다른 여섯 심이 이미 보여주는 오름차순 숫자 순서를 따른다.

---

## 4. FS와 CARD

| 주소 | 크기 | 제안 | 근거 | 신뢰도 |
|---|---|---|---|---|
| `0x021197c0` | 0x8 | `FSi_CloseFileCommand` | `fs_command_default.c` 구간의 머리이므로 파일의 마지막 함수(469); 이후 구간은 틈 없이 459, 428, 270, 200, 144, 118, 107, 96, 85, 51, 33으로 내려간다. `src/matched/func_021197c0.c`는 `return 0;` = `FS_RESULT_SUCCESS`이다 [P: `fs_command_default.c`] | high |
| `0x0211ed4c` | 0x10 | `CARD_Enable` | `CARDi_WaitAsync`(136)와 `CARD_CheckEnabled`(124) 사이; `CARD_Enable`(131)이 유일한 후보. `src/matched/func_0211ed4c.c`는 인자를 전역 하나에 저장한다 [P: `card_common.c`] | high |
| `0x0211ed88` | 0x10 | `CARD_IsEnabled` | `CARD_CheckEnabled`(124)와 `CARDi_InitCommon`(70) 사이; `CARD_IsEnabled`(119)가 유일한 후보 [P: `card_common.c`] | high |
| `0x0211ec44` | 0x10 | `CARD_GetRomHeader` | `card_common.c` 구간의 첫 함수이므로 파일의 마지막 함수(289); 포인터 반환은 0x10이다 [P: `card_common.c`] | medium |
| `0x0211eea0` | 0xa4 | `CARDi_UnlockResource` | **새 이름이 아니라 정정.** 심볼 테이블은 이를 `G3C_UpdateGXDLInfo`라 부른다; 이는 `CARDi_InitCommon`(70)과 `CARDi_LockResource`(28) 사이, 즉 `CARDi_UnlockResource`(49)가 속하는 자리에 놓인다. `src/matched/G3C_UpdateGXDLInfo.c`가 이미 이 잘못된 이름을 기록하고 있다 [P: `card_common.c`] | high |
| `0x0211f230` | 0xc | `CARD_WaitBackupAsync` | `CARD_CancelBackupAsync`(274)와 `0x0211f23c` 사이; 후보는 `CARD_TryWaitBackupAsync`(269)와 `CARD_WaitBackupAsync`(264), 둘 다 한 줄짜리 래퍼 [P: `card_backup.c`] | medium |
| `0x0211f23c` | 0x148 | `CARD_IdentifyBackup` | 위 래퍼와 `CARD_GetBackupTotalSize`(217) 사이; `CARD_IdentifyBackup`(235)이 유일한 큰 후보이며, `0x0211f028`에 이름이 붙어 있는 `CARDi_IdentifyBackupCore`를 호출한다 [P: `card_backup.c`] | high |

`0x0211ff5c`, `0x0211ffc0`, `0x02120000`의 익명 함수 셋은 `card/src/card_pullOut.c` TU에
속한다(`CARDi_PulledOutCallback` 앞에 놓인다); 그 파일을 읽지 않았기 때문에 여기서는 이름 없이
남겨 둔다.

---

## 5. TP, PM, RTC

TP는 `0x0211cc40`..`0x0211d7d4`에서 완전히 이름이 붙어 있다;
<https://github.com/ntrtwl/NitroSDK/blob/main/libraries/spi/src/tp.c>에서 링크에 살아남은 모든
함수가 심볼을 갖고 있다. PM과 RTC는 *동기* 래퍼가 빠져 있는데, 이는 규칙이 가장 쉽게 찾아내는
형태이다: 각각은 자신이 감싸는 `...Async` 바로 앞에 놓인 0x18-0x50 크기의 함수이다.

| 주소 | 크기 | 제안 | 근거 | 신뢰도 |
|---|---|---|---|---|
| `0x0211d8dc` | 0x3c | `PM_GetLEDPattern` | `PMi_PrependList`(825)와 `PM_GetLEDPatternAsync`(795) 사이; `PM_GetLEDPattern`(812)이 유일한 후보 [P: `spi/src/pm.c`] | high |
| `0x0211d968` | 0x3c | `PMi_SendLEDPatternCommand` | `PM_GetLEDPatternAsync`(795)와 `PMi_SendLEDPatternCommandAsync`(766) 사이; `PMi_SendLEDPatternCommand`(782)가 유일한 후보이고 같은 0x3c 래퍼 형태 [P: `spi/src/pm.c`] | high |
| `0x0211dc78` | 0x3c | `PM_SetBackLight` | `PM_ForceToPowerOffAsync`(441)와 `PM_SetBackLightAsync`(336) 사이; 그 틈에 소스 함수 다섯, 슬롯은 하나, 살아남은 것은 자신이 감싸는 async에 인접해 있다 [P: `spi/src/pm.c`] | medium |
| `0x0211e954` | 0x44 | `RTC_GetDate` | `RTC_GetTimeAsync`(118)와 `RTC_GetDateAsync`(79) 사이; `RTC_GetDate`(109)가 유일한 후보이고, `0x0211e894`의 쌍둥이 `RTC_GetTime`과 같은 0x44이며, `src/matched/func_0211e954.c`는 정확히 `RTC_GetDateAsync` + `RtcWaitBusy` + `RtcGetResultCallback`을 호출한다 [P: `rtc/src/external.c`] | high |
| `0x0211ec34` | 0x10 | `RTCi_IsLeapYear` | `rtc/src/convert.c` 구간의 마지막이므로 소스 파일의 첫 함수(6) [P: `rtc/src/convert.c`] | medium |

`rtc/src/external.c` 구간은 이 모듈에서 가장 깨끗한 구간 중 하나이다: ROM 오름차순
`RtcWaitBusy`(1032), `RtcGetResultCallback`(999), `RtcBCD2HEX`(866),
`RtcCommonCallback`(637), `RTC_SetDateTime`(337), `RTC_GetDateTimeAsync`(159),
`RTC_GetTime`(148), `RTC_GetTimeAsync`(118), 슬롯, `RTC_GetDateAsync`(79),
`RTC_Init`(58) — 구멍 하나만 있는 엄격한 내림차순이다.

`0x0211c9c0`(0x280)은 `DGT_Hash2Reset` 뒤에 오고 TP 구간 앞에 놓이므로 `math/src/dgt.c`의
마지막 함수, 즉 hash-2(MD5) 경로용 파일 범위 블록 변환 함수이다 — hash-1 계열이 사용하는
`0x0211be88`의 이름 있는 `ProcessBlock`의 상대편이다. 공개 파일을 정확한 식별자를 줄 만큼
꼼꼼히 읽지 않았다: `low`.

---

## 6. NNS Fnd

| 주소 | 크기 | 제안 | 근거 | 신뢰도 |
|---|---|---|---|---|
| `0x02101c54` | 0x188 | `NNS_FndResizeForMBlockExpHeap` | `NNS_FndFreeToExpHeap`(729)과 `NNS_FndAllocFromExpHeapEx`(632) 사이; 유일한 후보(655). `src/matched/func_02101c54.c`로 교차 확인됨 [P: `fnd/src/expheap.c`] | high |
| `0x02101e20` | 0xc | `NNS_FndDestroyExpHeap` | `NNS_FndAllocFromExpHeapEx`(632)와 `NNS_FndCreateExpHeapEx`(604) 사이; 유일한 후보(626)이고, 0xc는 그 한 줄짜리 본체이다 [P: `fnd/src/expheap.c`] | high |
| `0x021023c8` | 0xa4 | `NNS_FndResizeForMBlockFrmHeap` | `frameheap.c` 구간의 첫 함수이므로 소스의 마지막 함수(339); 구간은 `NNS_FndAdjustFrmHeap`(322)으로 이어진다. `src/matched/func_021023c8.c`로 교차 확인됨 [P: `fnd/src/frameheap.c`] | high |
| `0x0210285c` | 0x30 | `NNS_FndUnmountArchive` | `NNS_FndGetArchiveFileByName`(82)과 `NNS_FndMountArchive`(19) 사이; 유일한 후보(71) [P: `fnd/src/archive.c`] | high |

---

## 7. NNS G3D와 G2D

| 주소 | 크기 | 제안 | 근거 | 신뢰도 |
|---|---|---|---|---|
| `0x02105178` | 0x8 | `NNS_G3dPlttSetPlttKey` | `NNS_G3dPlttLoad`(407)와 `NNS_G3dPlttGetRequiredSize`(384) 사이; 유일한 후보(395), 한 줄짜리 [P: `g3d/src/kernel.c`] | high |
| `0x02105294` | 0x8 | `NNS_G3dRenderObjSetInitFunc` | `NNS_G3dTexGetRequiredSize`(253)와 `NNS_G3dRenderObjSetCallBack`(229) 사이; 후보는 247과 238, 둘 다 한 줄짜리, 순서상 247을 우선한다 [P: `g3d/src/kernel.c`] | medium |
| `0x021054e4` | 0x68 | `NNS_G3dRenderObjInit` | `addLink_`(95)와 `NNS_G3dAnmObjInit`(30) 사이; 후보는 82/73/64이며, 여러 필드를 초기화하는 것은 82뿐이다. `src/matched/func_021054e4.c`는 구조체에 대해 `MIi_CpuClear32`를 호출하는데, 그것이 바로 이 함수이다 [P: `g3d/src/kernel.c`] | medium |
| `0x021057f4` | 0x28 | `NNS_G3dGlbSetBaseScale` | `NNS_G3dGlbLightVector`(262)와 `NNS_G3dGlbFlushP`(64) 사이; 두 0x28 슬롯이 순서대로 250, 238을 차지한다. `src/matched/func_021057f4.c`로 교차 확인됨 [P: `g3d/src/glbstate.c`] | high |
| `0x0210581c` | 0x28 | `NNS_G3dGlbSetBaseTrans` | 위와 같음, 두 번째 슬롯(238); 동일한 12줄짜리 setter 형태 [P: `g3d/src/glbstate.c`] | high |
| `0x02107b44` | 0x20 | `NNS_G3dGetJntAnmByIdx` | `NNS_G3dGetJntAnmSet`(331)과 `NNS_G3dGetMatCAnmSet`(291) 사이; 후보는 315와 301. `src/matched/func_02107b44.c`는 +14에서 `u16` 개수를 읽고 +8부터 인덱싱한다 — 아래 세 행과 공유하는 `...ByIdx` 접근자 형태 [P: `g3d/src/binres/res_struct_accessor_anm.c`] | medium |
| `0x02107b80` | 0x20 | `NNS_G3dGetMatCAnmByIdx` | `NNS_G3dGetMatCAnmSet`(291)과 `NNS_G3dGetTexSRTAnmSet`(266) 사이; 유일한 후보(276) [P: same] | high |
| `0x02107bbc` | 0x20 | `NNS_G3dGetTexSRTAnmByIdx` | `...TexSRTAnmSet`(266)과 `...TexPatAnmSet`(240) 사이; 유일한 후보(250) [P: same] | high |
| `0x02107bf8` | 0x20 | `NNS_G3dGetTexPatAnmByIdx` | `...TexPatAnmSet`(240)과 `NNSi_G3dGetTexPatAnmDataByIdx`(218) 사이; 유일한 후보(224) [P: same] | high |
| `0x02107cf0` | 0x20 | `NNS_G3dGetVisAnmByIdx` | `NNS_G3dGetVisAnmSet`(127)과 `NNSi_G3dGetBinaryBlockFromFile`(79) 사이; 후보는 111과 `IsValidAnimHeader`(103); 0x20은 접근자 계열과 일치한다 [P: same] | medium |
| `0x02108b80` | 0xbc | `NNSi_G3dAnmObjInitNsBma` | `NNSi_G3dAnmCalcNsBma`(210)와 `GetMatColAnmuAlphaValue_`(94) 사이; 후보는 183과 `GetMatColAnm_`(153) [P: `g3d/src/anm/nsbma.c`] | medium |
| `0x02108f30` | 0xbc | `NNSi_G3dAnmObjInitNsBta` | `NNSi_G3dAnmCalcNsBta`(281)와 `GetTexSRTAnm_`(182) 사이; 유일한 후보(255), Bma 쌍둥이와 같은 0xbc [P: `g3d/src/anm/nsbta.c`] | high |
| `0x01ff9580` | 0x448 | `NNSi_G3dFuncSbc_NODEDESC` | ITCM 알파벳순 구간, `NNSi_G3dFuncSbc_NODE`와 `..._NOP` 사이; 그 구간에 있는 이름은 `NODEDESC`와 `NODEMIX`뿐이다. `0x0213cc9c`에 있는 ROM 자체의 디스패치 테이블로부터 `port/shim/gfx/sbcnames.c`로 교차 확인됨 [P: `g3d/src/sbc.c`] | high |
| `0x021062cc` | 0x674 | `NNSi_G3dFuncSbc_NODEMIX` | `NNSi_G3dFuncSbc_CALLDL`(1171)과 `..._BBY`(814) 사이; 유일한 후보(974). 같은 교차 확인 [P: `g3d/src/sbc.c`] | high |
| `0x0210744c`, `0x02107494`, `0x021074dc`, `0x02107524` | 각 0x48 | `NNS_G3dMdlSetMdl<field>All` 계열, 소스 역순 | `NNS_G3dMdlGetMdlAlpha`(358) 앞에 놓이므로 소스 줄은 358을 넘는다; `Get` 계열은 0x34이고 `Set...All` 계열은 0x48인데, 이들이 그렇다. 열네 개의 `...All` 변형(425-529줄) 중 넷이 살아남았으며, 바이트 크기로는 아무것도 구별되지 않는다 [P: `g3d/src/model.c`] | low |
| `0x02103218` | 0x44 | `NNS_G2dFontInitAuto` | `NNS_G2dFontFindGlyphIndex`(106)와 `GetGlyphIndex`(8) 사이; 후보는 64와 8줄짜리 static `GetCharWidthsFromIndex`(56)이며, 0x44는 후자에 비해 너무 크다 [P: `g2d/src/g2d_Font.c`] | medium |
| `0x02103334` | 0x334 | `NNS_G2dArrangeOBJ1D` | `NNSi_G2dCalcRequiredOBJ`(1073) 위쪽 `g2d_CharCanvas.c` 구간의 첫 함수이므로 소스 줄 > 1073; 0x334는 39줄짜리 `MakeCell` 변형들보다 87줄짜리 `NNS_G2dArrangeOBJ1D`(1096)를 고른다. `port/shim/gfx/g2d_charcanvas_obj1d.c`로 교차 확인됨 [P: `g2d/src/g2d_CharCanvas.c`] | high |
| `0x021037f8` | 0x94 | `NNS_G2dCharCanvasInitForOBJ1D` | `NNS_G2dMapScrToCharText`(963)와 `NNS_G2dCharCanvasInitForBG`(904) 사이; 후보는 943과 920. 같은 심 파일로 교차 확인됨 [P: same] | high |

---

## 8. NNS Snd

`snd/src/sndarc_stream.c`의 static 함수들은 이 모듈에서 가장 큰 끊김 없는 구간이다:
`NNS_SndArcPlayerSetup`과 `FreeCommandBuffer`(991) 사이에 다섯 개의 익명 함수가 엄격한
소스 내림차순으로 놓인다.

| 주소 | 크기 | 제안 | 근거 | 신뢰도 |
|---|---|---|---|---|
| `0x0210a9e4` | 0x60 | `NNSi_SndReadDriverPlayerInfo` | `NNSi_SndReadDriverTrackInfo`(159) 뒤에 온다; 유일한 12줄짜리 후보(147)이고 같은 0x5c-0x60 형태 [P: `snd/src/main.c`] | high |
| `0x0210aa44` | 0xf4 | `NNS_SndUpdateDriverInfo` | 그 다음 아래 슬롯; 0xf4는 12줄짜리 135보다 31줄짜리 104에 맞는다 [P: same] | medium |
| `0x0210ab38` | 0xc | `NNS_SndSetMasterVolume` | `NNS_SndMain`(55) 바로 위 슬롯; 0xc는 호출 하나를 전달하는 형태이고, 69가 그에 가장 가깝다 [P: same] | medium |
| `0x0210b498` | 0x34 | `NNS_SndPlayerReadDriverTrackInfo` | `NNSi_SndPlayerInit`(614) 뒤에 온다; 유일한 후보(600) [P: `snd/src/player.c`] | high |
| `0x0210b4cc` | 0x34 | `NNS_SndPlayerReadDriverPlayerInfo` | 다음 슬롯(586), 동일한 0x34 [P: same] | high |
| `0x0210b500` | 0x1c | `NNS_SndPlayerWriteGlobalVariable` | `NNS_SndPlayerWriteVariable`(548) 위 슬롯; 후보는 569(17줄)와 560(9줄), 0x1c가 560을 고른다 [P: same] | medium |
| `0x0210b604` | 0x30 | `NNS_SndPlayerSetTempoRatio` | `NNS_SndPlayerSetSeqNo`(452)와 `...SetTrackPitch`(382) 사이; 두 슬롯에 대해 형태가 같은 후보 여섯 [P: same] | low |
| `0x0210b634` | 0x30 | `NNS_SndPlayerSetTrackPan` | 같은 틈의 두 번째 슬롯 [P: same] | low |
| `0x0210b6d4` | 0x30 | `NNS_SndPlayerSetTrackMute` | `...SetTrackVolume`(368)과 `...SetChannelPriority`(321) 사이; 후보는 358/345/331 [P: same] | medium |
| `0x0210b734` | 0x2c | `NNS_SndPlayerSetPlayerPriority` | `...SetChannelPriority`(321)와 `...MoveVolume`(299) 사이; 유일한 후보(311) [P: same] | high |
| `0x0210b7e0` | 0xc | `NNS_SndHandleInit` | `NNS_SndHandleReleaseSeq`(215)와 `...StopSeqBySeqArcIdx`(144) 사이; 후보는 209(6줄)와 `StopSeqAll`(161, 14줄); 0xc가 209를 고른다 [P: same] | high |
| `0x0210e658` | 0x68 | `SetupStreamFunction` | 내림차순 구간의 머리; 1350 [P: `snd/src/sndarc_stream.c`] | high |
| `0x0210e6c0` | 0x8b4 | `MakeWaveData` | 1137, 213줄 — 파일에서 0x8b4가 될 만큼 큰 유일한 함수. `src/matched/func_0210e6c0.c`로 교차 확인됨 [P: same] | high |
| `0x0210ef74` | 0x14c | `OnDataEnd` | 1071 [P: same] | high |
| `0x0210f0c0` | 0x14c | `StrmCallback` | 1026 [P: same] | high |
| `0x0210f20c` | 0xac | `DisposeCallback` | 1002, 이름 있는 `FreeCommandBuffer`(991) 바로 위 [P: same] | high |
| `0x0210f404` | 0x74 | `CreateThread` | `RemoveCommandByPlayer`(934)와 `FreeChannel`(902) 사이; 유일한 후보(918) [P: same] | medium |
| `0x0210f500` | 0x70 | `ShutdownPlayer` | `AllocChannel`(887)과 `ForceStopStrm`(850) 사이; 유일한 후보(871) [P: same] | medium |
| `0x0210f988` | 0xa8 | `AllocPlayer` | `FreePlayer`(711)와 `NNSi_SndArcStrmMain`(591) 사이; 0xa8은 30줄짜리 681에 맞는다 [P: same] | high |
| `0x0210fbf8` | 0xc | `NNS_SndStrmHandleInit` | `NNS_SndStrmHandleRelease`(504)와 `NNS_SndArcStrmMoveVolume`(468) 사이; 유일한 한 줄짜리 후보(497) [P: same] | high |
| `0x0210fc50` | 0x2c | `NNS_SndArcStrmSetVolume` | `MoveVolume`(468) 아래 두 슬롯 중 첫째; 458 [P: same] | medium |
| `0x0210fc7c` | 0x30 | `NNS_SndArcStrmStop` | 두 번째 슬롯; 후보는 447과 438 [P: same] | medium |
| `0x0210fd2c` | 0xdc | `NNS_SndArcStrmSetupPlayer` | `NNS_SndArcStrmPrepare`(299) 아래; 255, 35줄 [P: same] | medium |
| `0x0210fe08` | 0x104 | `NNS_SndArcStrmInit` | 다음 슬롯; 205, 50줄 [P: same] | medium |

---

## 9. 가설

- `0x0210744c`..`0x02107524`의 네 `NNS_G3dMdlSetMdl*All` 슬롯은 호출자의 즉치값(immediate)을
  읽어 못 박을 수 있다: 각 `...All` 기록 함수는 재질 필드 하나를 마스킹하므로, 호출자가 넘기는
  상수가 그 필드를 식별한다. 실험: 네 본체를 디스어셈블하고 `NNSi_G3dModifyMatFlag` 마스크 인자를
  `g3d/g3d_config.h`와 비교한다.
- `0x02116a1c`는 `os_valarm.c`가 아예 아닐 수도 있다; 그곳의 TU 경계는 양쪽 각각 하나의 이름 있는
  이웃으로부터 추론한 것이다. 실험: `0x021169ac`의 `OS_InitVAlarm`이 건드리는 `OSi_VAlarm` 큐
  전역을 참조하는지 확인한다.
- `0x0210b604`/`0x0210b634`의 두 `NNS_SndPlayerSet*` 슬롯은 ROM의 호출자로부터 판별 가능하다:
  각각은 플레이어 구조체의 고정 오프셋에 있는 필드 하나를 쓴다.
  `port/shim/snd/sequpdate.c`는 이미 `func_0210b634`를 호출한다 — 그것이 기대하는 오프셋을 읽으면
  이름이 정해진다.
- `0x0211ff5c`, `0x0211ffc0`, `0x02120000`(`card_pullOut.c`)과 `sndarc_loader.c` /
  `resource_mgr.c` / `capture.c`의 틈은 오직 그 소스 파일을 읽지 않았기 때문에 이름 없이 남겨졌다;
  같은 방법이 그대로 적용된다.

## 10. 이 중 어느 것이든 채택하기 전에 검증해야 할 것

1. **SDK 리비전은 ROM의 것이 아니다.** `ntrtwl/NitroSDK`와 `ntrtwl/NitroSystem`은 하나의
   리비전에서의 전체 트리이다; `src/matched/` 헤더는 이 ROM이 혼합물을 링크한다는 것을 보여준다 —
   `os`의 대부분은 NitroSDK 2.2a(20050826)이지만,
   `OS_KillThreadWithPriority`, `OSi_ExitThread_ArgSpecified`, `OS_ExitThread`, `OS_Init`,
   `OS_GetInitArenaLo`, `CARD_CancelBackupAsync`는 NitroSDK 3.0(20060125)이고,
   `OS_GetLowEntropyData`는 NitroSDK 3.1이다. 더 새로운 리비전에만 존재하는 함수, 또는 리비전
   사이에 파일 안에서 위치가 옮겨진 함수는 그 틈 전체에 대한 위치 논증을 깨뜨린다. 행을 신뢰하기
   전에 이웃한 `src/matched/` 헤더에 기록된 리비전을 확인한다.
2. **이름은 시그니처가 아니다.** 모든 행은 식별자를 제안하는 것이지, 인자 목록이나 반환 타입을
   제안하는 것이 아니다. `src/matched/func_02105178.c`는 자신의 본체에 대해 정확히 이렇게 말한다:
   빈 본체는 어떤 시그니처로도 `bx lr`로 컴파일된다. 이름을 채택하는 것을 프로토타입을 채택하는
   것으로 받아들여서는 안 된다 — 그것은 D2(누락된 인자)와 D12(잘못 타이핑된 주소를 인코딩한 이름)를
   불러들이는 일이다.
3. **신뢰도 `low` 행은 함수가 아니라 계열의 이름을 적는다.** `low` 행을
   `port/tools/known_*.txt`, `overrides.txt`, 또는 이름을 키로 하는 어떤 레지스트리에도 넣지
   않는다; 그 행들은 `model.c` 슬롯 넷, `player.c` 슬롯 둘, `0x02116a1c`, `0x0211c9c0`이다.
4. **심볼 이름 변경은 문서 이벤트가 아니라 빌드 이벤트이다.** `symbols.txt`의 이름은
   `tools/agent/target.py`, 섀도 패스, 링크에 공급된다; `port/shim/gfx/sbcnames.c`가 존재하는
   이유는 정확히, 이름을 키로 하는 테이블(`NNS_G3dFuncSbcTable[]`)이 두 항목이 익명일 때 잘못
   동작했기 때문이다. 어떤 채택이든 `config/`에 직접 편집해 넣는 대신 통상의 빌드/실행 게이트
   (B5, B6)를 거쳐야 한다.
5. **이 문서의 줄 번호를 신뢰하지 말고 다시 유도한다.** 이 줄 번호들은 이 감사 시점의 공개
   파일의 줄 번호이다; 저장소는 살아 움직인다. 재현 가능한 산출물은 숫자가 아니라 1절의 절차이다.
6. **교차 확인된 일곱 행은 나머지 67행의 근거가 아니다.** 그것들은 *방법*이 알려진 답을 재현한다는
   근거이다. 나머지 각 행은 여전히 자신의 이웃 논증 위에 홀로 서 있다.

## 관련 문서

- `wiki/audits/hardware-services.md` 3절 — 이 감사가 기반으로 삼는 공개 레퍼런스 목록.
- `docs/kb/modules/autoload2.md`, `docs/kb/modules/sdk-nns.md` — SDK 대역이 무엇이며 포트가
  이를 어떻게 다루는지.
