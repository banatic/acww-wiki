# Audit: naming the SDK-layer `func_XXXXXXXX`

**Summary.** The ROM's `autoload_2` band (`0x020e8840`..) and `itcm` are almost entirely
NitroSDK 2.2a / NITRO-System `NNS_Library-20050901` library code, and roughly half of it is
anonymous in `config/adm-kr/arm9/**/symbols.txt`. This audit recovers names for 74 of those
addresses from public library sources alone, without reading or copying any code into the
repo. The lever is a link-order regularity: **within one library translation unit, the ROM's
functions appear in ascending address order that is the exact reverse of the public source
file's order.** Given two named neighbours from the same source file, the anonymous functions
between them are the source functions between them, read backwards. Every row is graded
**P** (public source) with the file URL, plus a confidence.

The method was validated blind: seven of the addresses it names already carry an
independently established identity inside this repo (`src/matched/` headers,
`port/shim/gfx/sbcnames.c`, `port/shim/gfx/g2d_charcanvas_obj1d.c`), and the method
reproduced all seven. Those rows are marked as cross-confirmed rather than treated as new.

Machine-readable rows: `wiki/audits/sdk-names.tsv` (address, proposed name, library,
source URL, confidence).

---

## 1. The ordering rule, and its evidence

`src/matched/<name>.c` headers name the real library file for many already-named functions
(e.g. `Real source: NitroSDK 2.2a (20050826) build/libraries/os/common/src/os_alarm.c`).
Sorting a module's `symbols.txt` by address and annotating each named function with its
source file gives a picture of translation-unit runs. Inside each run the order is reverse
source order. Three independent chains show it:

- **`os/src/os_thread.c`** — ROM ascending: `OS_SetSwitchThreadCallback`,
  `OSi_SleepAlarmCallback`, `func_0211482c`, `OS_GetThreadPriority`, `OS_SetThreadPriority`,
  `OS_GetStackStatus`, `OS_YieldThread`, `OS_RescheduleThread`, `OS_SelectThread`,
  `OS_WakeupThreadDirect`, `OS_WakeupThread`, `OS_SleepThread`. Public source lines:
  1150, 1139, ?, 1109, 1069, 996, 890, 883, 872, 854, 809, 773 — strictly descending
  [P: <https://github.com/ntrtwl/NitroSDK/blob/main/libraries/os/src/os_thread.c>].
- **`snd/src/snd_command.c`** — ROM ascending `InitPXI`, `SND_CountWaitingCommand`,
  `SND_CountReservedCommand`, `SND_CountFreeCommand`, `SND_IsFinishedCommandTag`,
  `SND_GetCurrentCommandTag`, `SND_WaitForCommandProc`, `SND_FlushCommand`,
  `SND_PushCommand`, `SND_AllocCommand`, `SND_RecvCommandReply`, `SND_CommandInit`
  = source lines 605, 397, 381, 365, 342, 327, 281, 212, 191, 156, 112, 61
  [P: <https://github.com/ntrtwl/NitroSDK/blob/main/libraries/snd/src/snd_command.c>].
- **`g3d/src/model.c`** — ROM ascending `NNS_G3dMdlSetMdlAlpha`, `...SetMdlPolygonID`,
  `...SetMdlLightEnableFlag`, `...SetMdlEmi`, `...SetMdlDiff`,
  `NNSi_G3dModifyPolygonAttrMask`, `NNSi_G3dModifyMatFlag` = source lines 167, 152, 107,
  92, 47, 25, 3 [P: <https://github.com/ntrtwl/NitroSystem/blob/main/libraries/g3d/src/model.c>].

Two consequences make the rule usable:

1. **A translation-unit boundary is where the source-line sequence restarts.** The first
   ROM function of a TU is the *last* function of its source file.
2. **Missing functions are dead-stripped, never reordered.** Every observed run is a
   subsequence of the reversed source order, so an anonymous slot's candidate set is exactly
   the source functions strictly between its two named neighbours.

### Two exceptions this audit found

- **ITCM is not in source order — it is alphabetical by symbol.** `CP_RestoreContext`,
  `CP_SaveContext`, `OS_DisableIrqMask`, `OS_EnableIrqMask`, `OS_LoadContext`,
  `OS_ResetRequestIrqMask`, `OS_SaveContext`, `OS_SetIrqMask`, `OSi_IrqCallback`,
  `OSi_IrqDma2`, `OSi_IrqDma3`, `OSi_IrqTimer0..3`; later `MI_SendGXCommandAsync`,
  `MI_WaitDma`, `MIi_CheckDma0SourceAddress`, `MIi_DMACallback`, `MIi_DmaSetParams`,
  `MIi_FIFOCallback`. In ITCM the neighbour constraint is on the *name*, not the source
  line, which is much weaker — but it is exactly what pins `OSi_IrqDma0` / `OSi_IrqDma1`.
- **`asm` functions escape the sequence.** `OSi_AlarmHandler` (`0x02116498`, 0x10) sits at
  the head of the `os_alarm.c` run rather than between `OSi_ArrangeTimer` and
  `OS_CancelAlarm` where the source puts it; `src/matched/OSi_AlarmHandler.c` records it as
  a hand-written `asm void` transcribed from that file. Treat `asm`-declared SDK functions
  as unordered.

### What the rule cannot do

It gives a *set* of candidates, not always a unique name. Where two source functions of
similar size sit between the same two named neighbours and only one survived the link, size
and callees have to break the tie; where they cannot, the row is graded `low` and names the
family rather than the function. Sizes come from `symbols.txt`; a rough rule that held
across the whole band is ~4 bytes per statement at `-O4,p`, and one-line setters/getters are
0x8-0x20.

---

## 2. Coverage by family

| family | anonymous functions found | named here | note |
|---|---|---|---|
| OS thread / alarm / valarm / tick / printf | 9 | 9 | the alarm and thread files are otherwise fully named |
| MI DMA / uncompress | 0 | 0 | **already complete** — see below |
| FS / CARD | 6 | 6 | one is a correction, not a new name |
| SND (SDK `snd_*`) | 0 | 0 | **already complete** — see below |
| TP / PM / RTC | 5 | 5 | TP is fully named; PM and RTC each lose their sync wrappers |
| NNS Fnd (heap / archive) | 4 | 4 | |
| NNS G3D (kernel, glbstate, sbc, model, binres, anm) | 18 | 18 | 4 of them family-level only |
| NNS G2D (font, char canvas) | 3 | 3 | |
| NNS Snd (main, player, sndarc_stream) | 23 | 23 | the stream statics are the largest clean run |
| DGT / math | 1 | 1 | low confidence |

**MI is a non-target.** Every `MI_*` / `MIi_*` function in `autoload_2` between `0x02116e98`
and `0x02117c10` already carries its name: `MI_SetWramBank`, `MIi_CheckAnotherAutoDMA`,
`MI_StopDma`, `MI_DmaCopy32Async`, `MI_DmaFill32Async`, `MI_DmaCopy16`, `MI_DmaCopy32`,
`MI_DmaFill32`, `MIi_DMAFastCallback`, `MI_SendGXCommandAsyncFast`, the `MIi_Cpu*` block,
`MI_Copy32B/36B/48B/64B`, `MI_CpuFill8`, `MI_CpuCopy8`, `MI_Zero36B`, `MI_SwapWord`,
`MI_UncompressLZ8`, `MIi_CardDmaCopy32`, `MI_ReadUncompLZ8`, `MI_InitUncompContextLZ`,
`SearchLZ`, `MI_CompressLZ`, `MI_Init`. The uncompress entry points the game actually uses
are the ARM7 BIOS SWIs named in `config/adm-kr/arm9/symbols.txt`
(`LZ77UnCompReadNormalWrite8bit`, `HuffUnCompReadByCallback`,
`RLUnCompReadByCallbackWrite16bit`, `BitUnPack`). Nothing to propose.

**The SDK SND command family is a non-target too.** `0x02117c10`..`0x02119380` is
`snd_interface.c`, `snd_main.c`, `snd_command.c`, `snd_alarm.c`, `snd_work.c`, `snd_util.c`,
`snd_bank.c` with no anonymous member. The SND work left is all in NITRO-System's
`libraries/snd/`, section 8.

**`main` (arm9 static, `0x02000000`..`0x020e8840`) is a non-target.** It has 16,741 function
symbols and only 139 names, but 97 of those are BIOS/SWI thunks and the rest are game
entry points; there is no SDK band there for a neighbour argument to work on. SDK naming
buys nothing in `main`.

---

## 3. OS: thread, alarm, timer, printf

Neighbours and source order from
<https://github.com/ntrtwl/NitroSDK/blob/main/libraries/os/src/>.

| address | size | proposed | evidence | conf |
|---|---|---|---|---|
| `0x0211482c` | 0x9c | `OS_Sleep` | between `OSi_SleepAlarmCallback` (1139) and `OS_GetThreadPriority` (1109); `OS_Sleep` (1115) is the only source function in the gap, and it is the installer of that very callback [P: `os_thread.c`] | high |
| `0x02114e1c` | 0x74 | `OSi_KillThreadWithPriority` | between `OS_KillThread` (626) and `OSi_ExitThread_Destroy` (498); `OS_KillThread` is 0x30, the thin wrapper shape, so its 0x74 helper is the body [P: `os_thread.c`] | medium |
| `0x021145d4` | 0x30 | `OS_SNPrintf` | between `OS_VSNPrintf` (399) and `OS_VSPrintf` (384); 0x30 is the varargs-forwarding shape shared with `0x0211461c` [P: `os_printf.c`] | high |
| `0x0211461c` | 0x30 | `OS_SPrintf` | between `OS_VSPrintf` (384) and `string_put_string` (358); only `OS_SPrintf` (374) lies in the gap [P: `os_printf.c`] | high |
| `0x02114740` | 0x10 | `OS_PutStringInit` | last function of the `os_printf.c` run, therefore the source file's first; candidate set is `OS_PutStringInit` (54) / `OS_PutStringPrnSrv` (279), and only one slot survives [P: `os_printf.c`] | medium |
| `0x021163ec` | 0x10 | `OS_IsTickAvailable` | between `OSi_CountUpTick` (42) and `OS_InitTick` (16); `OS_IsTickAvailable` (37) is the only candidate and is a one-line flag read [P: `os_tick.c`] | high |
| `0x02116528` | 0x8 | `OS_SetAlarmTag` | between `OS_CancelAlarms` (309) and `OSi_ArrangeTimer` (248); `OS_SetAlarmTag` (300) is a single assignment, and 0x8 is exactly that [P: `os_alarm.c`] | high |
| `0x021166e0` | 0x78 | `OS_SetAlarm` | between `OS_CancelAlarm` (198) and `OSi_InsertAlarm` (94); candidates `OS_SetAlarm` (144) and `OS_SetPeriodicAlarm` (170), one slot. `OS_SetAlarm` preferred as the common caller-facing entry [P: `os_alarm.c`] | medium |
| `0x021168a8` | 0x10 | `OS_IsAlarmAvailable` | between `OS_CreateAlarm` (85) and `OS_InitAlarm` (43); candidates `OS_IsAlarmAvailable` (80, one-line) and `OS_EndAlarm` (60, a loop); 0x10 selects the former [P: `os_alarm.c`] | high |
| `0x02116a1c` | 0x80 | `OSi_VCountArr` | tail of the `os_valarm.c` run, i.e. its source-first function; the only candidate, but 0x80 is large for it and the public file may not be the ROM's revision [P: `os_valarm.c`] | low |

`OSi_IrqDma0` / `OSi_IrqDma1` (`0x01ff82f8`, `0x01ff8308`, 0x10 each) come from the ITCM
alphabetical run: they sit immediately before `OSi_IrqDma2` and `OSi_IrqDma3`, which are
identical 0x10 shims, and `os_irqTable.c` declares exactly `OSi_IrqDma0..3` [P:
<https://github.com/ntrtwl/NitroSDK/blob/main/libraries/os/src/os_irqTable.c>]. Confidence
high for the pair; the 0-then-1 assignment follows the ascending numeric order the other
six shims already show.

---

## 4. FS and CARD

| address | size | proposed | evidence | conf |
|---|---|---|---|---|
| `0x021197c0` | 0x8 | `FSi_CloseFileCommand` | head of the `fs_command_default.c` run, so the file's last function (469); the run then descends 459, 428, 270, 200, 144, 118, 107, 96, 85, 51, 33 without a gap. `src/matched/func_021197c0.c` is `return 0;` = `FS_RESULT_SUCCESS` [P: `fs_command_default.c`] | high |
| `0x0211ed4c` | 0x10 | `CARD_Enable` | between `CARDi_WaitAsync` (136) and `CARD_CheckEnabled` (124); `CARD_Enable` (131) is the only candidate. `src/matched/func_0211ed4c.c` stores its argument into one global [P: `card_common.c`] | high |
| `0x0211ed88` | 0x10 | `CARD_IsEnabled` | between `CARD_CheckEnabled` (124) and `CARDi_InitCommon` (70); `CARD_IsEnabled` (119) is the only candidate [P: `card_common.c`] | high |
| `0x0211ec44` | 0x10 | `CARD_GetRomHeader` | first function of the `card_common.c` run, so the file's last (289); a pointer return is 0x10 [P: `card_common.c`] | medium |
| `0x0211eea0` | 0xa4 | `CARDi_UnlockResource` | **correction, not a new name.** The symbol table calls it `G3C_UpdateGXDLInfo`; it sits between `CARDi_InitCommon` (70) and `CARDi_LockResource` (28), where `CARDi_UnlockResource` (49) belongs. `src/matched/G3C_UpdateGXDLInfo.c` already records the misname [P: `card_common.c`] | high |
| `0x0211f230` | 0xc | `CARD_WaitBackupAsync` | between `CARD_CancelBackupAsync` (274) and `0x0211f23c`; candidates `CARD_TryWaitBackupAsync` (269) and `CARD_WaitBackupAsync` (264), both one-line wrappers [P: `card_backup.c`] | medium |
| `0x0211f23c` | 0x148 | `CARD_IdentifyBackup` | between the wrapper above and `CARD_GetBackupTotalSize` (217); `CARD_IdentifyBackup` (235) is the only large candidate and calls `CARDi_IdentifyBackupCore`, which is named at `0x0211f028` [P: `card_backup.c`] | high |

The three anonymous functions at `0x0211ff5c`, `0x0211ffc0`, `0x02120000` belong to the
`card/src/card_pullOut.c` TU (they precede `CARDi_PulledOutCallback`); they are left
unnamed here because that file was not read.

---

## 5. TP, PM, RTC

TP is fully named in `0x0211cc40`..`0x0211d7d4`; every function in
<https://github.com/ntrtwl/NitroSDK/blob/main/libraries/spi/src/tp.c> that survived the
link has its symbol. PM and RTC lose their *synchronous* wrappers, which is the shape the
rule finds most easily: each is a 0x18-0x50 function sitting immediately before the
`...Async` it wraps.

| address | size | proposed | evidence | conf |
|---|---|---|---|---|
| `0x0211d8dc` | 0x3c | `PM_GetLEDPattern` | between `PMi_PrependList` (825) and `PM_GetLEDPatternAsync` (795); `PM_GetLEDPattern` (812) is the only candidate [P: `spi/src/pm.c`] | high |
| `0x0211d968` | 0x3c | `PMi_SendLEDPatternCommand` | between `PM_GetLEDPatternAsync` (795) and `PMi_SendLEDPatternCommandAsync` (766); `PMi_SendLEDPatternCommand` (782) is the only candidate, same 0x3c wrapper shape [P: `spi/src/pm.c`] | high |
| `0x0211dc78` | 0x3c | `PM_SetBackLight` | between `PM_ForceToPowerOffAsync` (441) and `PM_SetBackLightAsync` (336); five source functions in the gap, one slot, and the surviving one is adjacent to the async it wraps [P: `spi/src/pm.c`] | medium |
| `0x0211e954` | 0x44 | `RTC_GetDate` | between `RTC_GetTimeAsync` (118) and `RTC_GetDateAsync` (79); `RTC_GetDate` (109) is the only candidate, it is the same 0x44 as its twin `RTC_GetTime` at `0x0211e894`, and `src/matched/func_0211e954.c` calls exactly `RTC_GetDateAsync` + `RtcWaitBusy` + `RtcGetResultCallback` [P: `rtc/src/external.c`] | high |
| `0x0211ec34` | 0x10 | `RTCi_IsLeapYear` | last of the `rtc/src/convert.c` run, so its source-first function (6) [P: `rtc/src/convert.c`] | medium |

The `rtc/src/external.c` run is one of the cleanest in the module: ROM ascending
`RtcWaitBusy` (1032), `RtcGetResultCallback` (999), `RtcBCD2HEX` (866),
`RtcCommonCallback` (637), `RTC_SetDateTime` (337), `RTC_GetDateTimeAsync` (159),
`RTC_GetTime` (148), `RTC_GetTimeAsync` (118), the slot, `RTC_GetDateAsync` (79),
`RTC_Init` (58) — strictly descending with a single hole.

`0x0211c9c0` (0x280) trails `DGT_Hash2Reset` and precedes the TP run, so it is the last
function of `math/src/dgt.c`, i.e. its file-scope block transform for the hash-2 (MD5)
path — the counterpart of the named `ProcessBlock` at `0x0211be88` used by the hash-1
family. The public file was not read closely enough to give the exact identifier: `low`.

---

## 6. NNS Fnd

| address | size | proposed | evidence | conf |
|---|---|---|---|---|
| `0x02101c54` | 0x188 | `NNS_FndResizeForMBlockExpHeap` | between `NNS_FndFreeToExpHeap` (729) and `NNS_FndAllocFromExpHeapEx` (632); sole candidate (655). Cross-confirmed by `src/matched/func_02101c54.c` [P: `fnd/src/expheap.c`] | high |
| `0x02101e20` | 0xc | `NNS_FndDestroyExpHeap` | between `NNS_FndAllocFromExpHeapEx` (632) and `NNS_FndCreateExpHeapEx` (604); sole candidate (626), and 0xc is its one-line body [P: `fnd/src/expheap.c`] | high |
| `0x021023c8` | 0xa4 | `NNS_FndResizeForMBlockFrmHeap` | first function of the `frameheap.c` run, so its source-last (339); the run continues `NNS_FndAdjustFrmHeap` (322). Cross-confirmed by `src/matched/func_021023c8.c` [P: `fnd/src/frameheap.c`] | high |
| `0x0210285c` | 0x30 | `NNS_FndUnmountArchive` | between `NNS_FndGetArchiveFileByName` (82) and `NNS_FndMountArchive` (19); sole candidate (71) [P: `fnd/src/archive.c`] | high |

---

## 7. NNS G3D and G2D

| address | size | proposed | evidence | conf |
|---|---|---|---|---|
| `0x02105178` | 0x8 | `NNS_G3dPlttSetPlttKey` | between `NNS_G3dPlttLoad` (407) and `NNS_G3dPlttGetRequiredSize` (384); sole candidate (395), one-line [P: `g3d/src/kernel.c`] | high |
| `0x02105294` | 0x8 | `NNS_G3dRenderObjSetInitFunc` | between `NNS_G3dTexGetRequiredSize` (253) and `NNS_G3dRenderObjSetCallBack` (229); candidates 247 and 238, both one-line, order prefers 247 [P: `g3d/src/kernel.c`] | medium |
| `0x021054e4` | 0x68 | `NNS_G3dRenderObjInit` | between `addLink_` (95) and `NNS_G3dAnmObjInit` (30); candidates 82/73/64, and only 82 is a multi-field initialiser. `src/matched/func_021054e4.c` calls `MIi_CpuClear32` over a struct, which is that function [P: `g3d/src/kernel.c`] | medium |
| `0x021057f4` | 0x28 | `NNS_G3dGlbSetBaseScale` | between `NNS_G3dGlbLightVector` (262) and `NNS_G3dGlbFlushP` (64); the two 0x28 slots take 250 then 238 in order. Cross-confirmed by `src/matched/func_021057f4.c` [P: `g3d/src/glbstate.c`] | high |
| `0x0210581c` | 0x28 | `NNS_G3dGlbSetBaseTrans` | as above, the second slot (238); identical 12-line setter shape [P: `g3d/src/glbstate.c`] | high |
| `0x02107b44` | 0x20 | `NNS_G3dGetJntAnmByIdx` | between `NNS_G3dGetJntAnmSet` (331) and `NNS_G3dGetMatCAnmSet` (291); candidates 315 and 301. `src/matched/func_02107b44.c` reads a `u16` count at +14 and indexes from +8 — the `...ByIdx` accessor shape shared by the three rows below [P: `g3d/src/binres/res_struct_accessor_anm.c`] | medium |
| `0x02107b80` | 0x20 | `NNS_G3dGetMatCAnmByIdx` | between `NNS_G3dGetMatCAnmSet` (291) and `NNS_G3dGetTexSRTAnmSet` (266); sole candidate (276) [P: same] | high |
| `0x02107bbc` | 0x20 | `NNS_G3dGetTexSRTAnmByIdx` | between `...TexSRTAnmSet` (266) and `...TexPatAnmSet` (240); sole candidate (250) [P: same] | high |
| `0x02107bf8` | 0x20 | `NNS_G3dGetTexPatAnmByIdx` | between `...TexPatAnmSet` (240) and `NNSi_G3dGetTexPatAnmDataByIdx` (218); sole candidate (224) [P: same] | high |
| `0x02107cf0` | 0x20 | `NNS_G3dGetVisAnmByIdx` | between `NNS_G3dGetVisAnmSet` (127) and `NNSi_G3dGetBinaryBlockFromFile` (79); candidates 111 and `IsValidAnimHeader` (103); 0x20 matches the accessor family [P: same] | medium |
| `0x02108b80` | 0xbc | `NNSi_G3dAnmObjInitNsBma` | between `NNSi_G3dAnmCalcNsBma` (210) and `GetMatColAnmuAlphaValue_` (94); candidates 183 and `GetMatColAnm_` (153) [P: `g3d/src/anm/nsbma.c`] | medium |
| `0x02108f30` | 0xbc | `NNSi_G3dAnmObjInitNsBta` | between `NNSi_G3dAnmCalcNsBta` (281) and `GetTexSRTAnm_` (182); sole candidate (255), same 0xbc as its Bma twin [P: `g3d/src/anm/nsbta.c`] | high |
| `0x01ff9580` | 0x448 | `NNSi_G3dFuncSbc_NODEDESC` | ITCM alphabetical run, between `NNSi_G3dFuncSbc_NODE` and `..._NOP`; the only names in that interval are `NODEDESC` and `NODEMIX`. Cross-confirmed by `port/shim/gfx/sbcnames.c` from the ROM's own dispatch table at `0x0213cc9c` [P: `g3d/src/sbc.c`] | high |
| `0x021062cc` | 0x674 | `NNSi_G3dFuncSbc_NODEMIX` | between `NNSi_G3dFuncSbc_CALLDL` (1171) and `..._BBY` (814); sole candidate (974). Same cross-confirmation [P: `g3d/src/sbc.c`] | high |
| `0x0210744c`, `0x02107494`, `0x021074dc`, `0x02107524` | 0x48 each | `NNS_G3dMdlSetMdl<field>All` family, in reverse source order | they precede `NNS_G3dMdlGetMdlAlpha` (358) so their source lines exceed 358; the `Get` family is 0x34 and the `Set...All` family is 0x48, which these are. Four of the fourteen `...All` variants (lines 425-529) survived, and nothing in the byte sizes distinguishes them [P: `g3d/src/model.c`] | low |
| `0x02103218` | 0x44 | `NNS_G2dFontInitAuto` | between `NNS_G2dFontFindGlyphIndex` (106) and `GetGlyphIndex` (8); candidates 64 and the 8-line static `GetCharWidthsFromIndex` (56), and 0x44 is too large for the latter [P: `g2d/src/g2d_Font.c`] | medium |
| `0x02103334` | 0x334 | `NNS_G2dArrangeOBJ1D` | first function of the `g2d_CharCanvas.c` run above `NNSi_G2dCalcRequiredOBJ` (1073), so source line > 1073; 0x334 selects the 87-line `NNS_G2dArrangeOBJ1D` (1096) over the 39-line `MakeCell` variants. Cross-confirmed by `port/shim/gfx/g2d_charcanvas_obj1d.c` [P: `g2d/src/g2d_CharCanvas.c`] | high |
| `0x021037f8` | 0x94 | `NNS_G2dCharCanvasInitForOBJ1D` | between `NNS_G2dMapScrToCharText` (963) and `NNS_G2dCharCanvasInitForBG` (904); candidates 943 and 920. Cross-confirmed by the same shim file [P: same] | high |

---

## 8. NNS Snd

The `snd/src/sndarc_stream.c` statics are the largest unbroken run in the module: five
anonymous functions in strictly descending source order between
`NNS_SndArcPlayerSetup` and `FreeCommandBuffer` (991).

| address | size | proposed | evidence | conf |
|---|---|---|---|---|
| `0x0210a9e4` | 0x60 | `NNSi_SndReadDriverPlayerInfo` | follows `NNSi_SndReadDriverTrackInfo` (159); sole 12-line candidate (147) and the same 0x5c-0x60 shape [P: `snd/src/main.c`] | high |
| `0x0210aa44` | 0xf4 | `NNS_SndUpdateDriverInfo` | next slot down; 0xf4 fits the 31-line 104 rather than the 12-line 135 [P: same] | medium |
| `0x0210ab38` | 0xc | `NNS_SndSetMasterVolume` | slot immediately above `NNS_SndMain` (55); 0xc is a one-call forward, and 69 is the nearest such [P: same] | medium |
| `0x0210b498` | 0x34 | `NNS_SndPlayerReadDriverTrackInfo` | follows `NNSi_SndPlayerInit` (614); sole candidate (600) [P: `snd/src/player.c`] | high |
| `0x0210b4cc` | 0x34 | `NNS_SndPlayerReadDriverPlayerInfo` | next slot (586), identical 0x34 [P: same] | high |
| `0x0210b500` | 0x1c | `NNS_SndPlayerWriteGlobalVariable` | slot above `NNS_SndPlayerWriteVariable` (548); candidates 569 (17 lines) and 560 (9 lines), 0x1c selects 560 [P: same] | medium |
| `0x0210b604` | 0x30 | `NNS_SndPlayerSetTempoRatio` | between `NNS_SndPlayerSetSeqNo` (452) and `...SetTrackPitch` (382); six equal-shaped candidates for two slots [P: same] | low |
| `0x0210b634` | 0x30 | `NNS_SndPlayerSetTrackPan` | second slot of the same gap [P: same] | low |
| `0x0210b6d4` | 0x30 | `NNS_SndPlayerSetTrackMute` | between `...SetTrackVolume` (368) and `...SetChannelPriority` (321); candidates 358/345/331 [P: same] | medium |
| `0x0210b734` | 0x2c | `NNS_SndPlayerSetPlayerPriority` | between `...SetChannelPriority` (321) and `...MoveVolume` (299); sole candidate (311) [P: same] | high |
| `0x0210b7e0` | 0xc | `NNS_SndHandleInit` | between `NNS_SndHandleReleaseSeq` (215) and `...StopSeqBySeqArcIdx` (144); candidates 209 (6 lines) and `StopSeqAll` (161, 14 lines); 0xc selects 209 [P: same] | high |
| `0x0210e658` | 0x68 | `SetupStreamFunction` | head of the descending run; 1350 [P: `snd/src/sndarc_stream.c`] | high |
| `0x0210e6c0` | 0x8b4 | `MakeWaveData` | 1137, 213 lines — the only function in the file big enough for 0x8b4. Cross-confirmed by `src/matched/func_0210e6c0.c` [P: same] | high |
| `0x0210ef74` | 0x14c | `OnDataEnd` | 1071 [P: same] | high |
| `0x0210f0c0` | 0x14c | `StrmCallback` | 1026 [P: same] | high |
| `0x0210f20c` | 0xac | `DisposeCallback` | 1002, immediately above the named `FreeCommandBuffer` (991) [P: same] | high |
| `0x0210f404` | 0x74 | `CreateThread` | between `RemoveCommandByPlayer` (934) and `FreeChannel` (902); sole candidate (918) [P: same] | medium |
| `0x0210f500` | 0x70 | `ShutdownPlayer` | between `AllocChannel` (887) and `ForceStopStrm` (850); sole candidate (871) [P: same] | medium |
| `0x0210f988` | 0xa8 | `AllocPlayer` | between `FreePlayer` (711) and `NNSi_SndArcStrmMain` (591); 0xa8 fits the 30-line 681 [P: same] | high |
| `0x0210fbf8` | 0xc | `NNS_SndStrmHandleInit` | between `NNS_SndStrmHandleRelease` (504) and `NNS_SndArcStrmMoveVolume` (468); sole one-line candidate (497) [P: same] | high |
| `0x0210fc50` | 0x2c | `NNS_SndArcStrmSetVolume` | first of two slots below `MoveVolume` (468); 458 [P: same] | medium |
| `0x0210fc7c` | 0x30 | `NNS_SndArcStrmStop` | second slot; candidates 447 and 438 [P: same] | medium |
| `0x0210fd2c` | 0xdc | `NNS_SndArcStrmSetupPlayer` | below `NNS_SndArcStrmPrepare` (299); 255, 35 lines [P: same] | medium |
| `0x0210fe08` | 0x104 | `NNS_SndArcStrmInit` | next slot; 205, 50 lines [P: same] | medium |

---

## 9. Hypotheses

- The four `NNS_G3dMdlSetMdl*All` slots at `0x0210744c`..`0x02107524` can be pinned by
  reading their callers' immediates: each `...All` writer masks one material field, so the
  constant a caller passes identifies the field. Experiment: disassemble the four bodies
  and compare the `NNSi_G3dModifyMatFlag` mask arguments against `g3d/g3d_config.h`.
- `0x02116a1c` may not be `os_valarm.c` at all; the TU boundary there is inferred from a
  single named neighbour on each side. Experiment: check whether it references the
  `OSi_VAlarm` queue globals that `OS_InitVAlarm` at `0x021169ac` touches.
- The two `NNS_SndPlayerSet*` slots at `0x0210b604`/`0x0210b634` are decidable from the
  ROM's callers: each writes one field of the player struct at a fixed offset.
  `port/shim/snd/sequpdate.c` already calls `func_0210b634` — reading which offset it
  expects settles the name.
- `0x0211ff5c`, `0x0211ffc0`, `0x02120000` (`card_pullOut.c`) and the `sndarc_loader.c` /
  `resource_mgr.c` / `capture.c` gaps were left unnamed only because those source files
  were not read; the same method applies unchanged.

## 10. What must be verified before adopting any of this

1. **The SDK revision is not the ROM's.** `ntrtwl/NitroSDK` and `ntrtwl/NitroSystem` are
   whole trees at one revision; `src/matched/` headers show this ROM links a mixture —
   NitroSDK 2.2a (20050826) for most of `os`, but NitroSDK 3.0 (20060125) for
   `OS_KillThreadWithPriority`, `OSi_ExitThread_ArgSpecified`, `OS_ExitThread`, `OS_Init`,
   `OS_GetInitArenaLo`, `CARD_CancelBackupAsync`, and NitroSDK 3.1 for
   `OS_GetLowEntropyData`. A function that exists only in the newer revision, or that moved
   within its file between revisions, breaks the position argument for its whole gap. Check
   the revision recorded in the neighbouring `src/matched/` header before trusting a row.
2. **A name is not a signature.** Every row proposes an identifier, not an argument list or
   a return type. `src/matched/func_02105178.c` says exactly this for its own body: an
   empty body compiles to `bx lr` under any signature. Adopting a name must not be taken as
   adopting a prototype — that is a D2 (dropped argument) and D12 (name encoding a mistyped
   address) invitation.
3. **Confidence `low` rows name a family, not a function.** Do not put a `low` row into
   `port/tools/known_*.txt`, `overrides.txt`, or any registry keyed by name; those are the
   four `model.c` slots, the two `player.c` slots, `0x02116a1c` and `0x0211c9c0`.
4. **Renaming a symbol is a build event, not a documentation event.** `symbols.txt` names
   feed `tools/agent/target.py`, the shadow pass and the link; `port/shim/gfx/sbcnames.c`
   exists precisely because a name-keyed table (`NNS_G3dFuncSbcTable[]`) went wrong when
   two entries were anonymous. Any adoption should go through the normal build/run gate
   (B5, B6) rather than being edited into `config/`.
5. **Re-derive, do not trust this page's line numbers.** They are the public files' line
   numbers as of this audit; the repositories are live. The reproducible artefact is the
   procedure in section 1, not the numbers.
6. **The seven cross-confirmed rows are not evidence for the other 67.** They are evidence
   that the *method* reproduces known answers. Each remaining row still stands on its own
   neighbour argument.

## Related

- `wiki/audits/hardware-services.md` section 3 — the public reference list this audit works
  from.
- `docs/kb/modules/autoload2.md`, `docs/kb/modules/sdk-nns.md` — what the SDK band is and
  how the port treats it.
