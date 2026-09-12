# Threads and interrupts

**Summary.** ACWW uses NitroSDK's cooperative thread model: a handful of `OSThread`s, each
with a 0x64-byte saved ARM register file, switched only where the code calls the scheduler.
The interrupt side is a table of handler slots at the bottom of DTCM, of which the game
depends almost entirely on one — the vertical blank, slot 0. A frame is what a VBlank means:
the game blocks in `VBlankIntrWait`, the handler wakes it, and the idle thread halts in
between. The ARM7 is reached through a FIFO with numbered tags, and its replies arrive as
interrupts too.

## What happens

### The context record

`OSContext` is 0x64 bytes: the CPSR at offset 0, r0 through r12 from 0x04, the stack pointer
at 0x38, the link register at 0x3c, `pc_plus4` at 0x40, the SVC stack pointer at 0x44, and the
coprocessor context from 0x48 to 0x63 [S: `src/matched/OSi_ExitThread_ArgSpecified.c`; source account: `OSContext`, autoload_2,
`port/shim/os/thread.c:80-107`, recovered verbatim from
`src/matched/OSi_ExitThread_ArgSpecified.c`]. The size 0x64 is independently pinned by
`src/matched/OS_InitThread.c`, and the offsets agree with `src/matched/OS_InitContext.c` and
with the two hand-written assembly bodies [H: source account: `port/shim/os/thread.c:84-92`; direct ROM-source provenance unresolved].

The coprocessor context is the ARM9's divider and square-root state: numerator, denominator,
square-root operand, and the two mode words, saved by `CP_SaveContext`
[H: source account: `CPContext`, `port/shim/os/thread.c:93-99`; `port/shim/os/thread.c:57-58`; direct ROM-source provenance unresolved].

`pc_plus4` holds the entry point plus four, deliberately, so that a `ldm ... ^` restore lands
one instruction early [H: source account: `port/shim/os/thread.c:176-179`; direct ROM-source provenance unresolved]. `r[0]` is load-bearing and is
read: it carries the thread procedure's argument, set by `OS_CreateThread` through
`OS_InitContext` and overwritten by `OSi_ExitThread_ArgSpecified`
[H: source account: `port/shim/os/thread.c:59-63`; direct ROM-source provenance unresolved].

### Saving and restoring: setjmp/longjmp over a register file

`OS_SaveContext` stores 1 into the context's own r0 slot and pc+8 into `pc_plus4`, then falls
through returning 0. `OS_LoadContext` restores the file with a user-mode multiple load of r0
through r14 and lands on `subs pc, lr, #4` — the instruction after the store. So the SAVER
sees 0 and the RESUMER sees 1: classic setjmp semantics
[S: `src/matched/OS_SaveContext.c`, `src/matched/OS_LoadContext.c`; source account: `OS_SaveContext` / `OS_LoadContext`, autoload_2, from
`src/matched/OS_SaveContext.c` and `src/matched/OS_LoadContext.c` via
`port/shim/os/thread.c:11-16`]. Both are hand-written ARM assembly bodies
[H: source account: `port/shim/os/thread.c:5-7`; direct ROM-source provenance unresolved].

The scheduler above them is cooperative: `OS_RescheduleThread` runs only where the code calls
it, and a thread runs until it blocks [H: source account: `port/shim/os/thread.c:17-19`; direct ROM-source provenance unresolved]. Its shape is a save,
an early return when the save reports a resume, then the switch callbacks,
`OS_SetCurrentThread`, and `OS_LoadContext` on the next thread
[S: `src/matched/OS_RescheduleThread.c`; source account: `src/matched/OS_RescheduleThread.c` via `port/shim/os/thread.c:31-40`].
`OS_RescheduleThread` and `OSi_ExitThread_ArgSpecified` are the only two functions in
`src/matched/` that name either routine [H: source account: `port/shim/os/thread.c:41-44`; direct ROM-source provenance unresolved].

`OS_CreateThread` writes two stack-overflow checknums into NDS memory, and
`OS_GetCurrentThread()->stackTop` / `stackBottom` address them
[H: source account: `port/shim/os/thread.c:51-55`; direct ROM-source provenance unresolved]. An `OSThread` procedure does not return: the contract is
that it ends in `OS_ExitThread`, which reschedules and never comes back
[H: source account: `port/shim/os/thread.c:222-225`; direct ROM-source provenance unresolved].

### The threads that exist

The launcher thread arrives as an ordinary thread and is never given a context by
`OS_InitThread`, which only fills in its priority and stack bounds; it acquires one at its
first `OS_SaveContext` [H: source account: `port/shim/os/thread.c:231-236`; direct ROM-source provenance unresolved]. The IDLE thread's whole body is
`while (1) OS_Halt();`, and `OS_Halt` is three ARM instructions around the CP15
wait-for-interrupt [S: `src/matched/OSi_IdleThreadProc.c`, `src/matched/OS_Halt.c`, `src/matched/OS_InitThread.c`, `src/matched/OS_SaveContext.c`; source account: `OSi_IdleThreadProc` / `OS_Halt`, itcm,
`port/shim/os/halt.c:6-8`]. Reaching it means the scheduler has correctly concluded that no
thread can run, which on hardware is an entirely normal state
[H: source account: `port/shim/os/halt.c:7-10`; direct ROM-source provenance unresolved]. Its stack is small — 0x80 bytes was measured
[H: log/source account: `docs/log/cycle40-keyboard-gate-probe.md` CARD40..SND40, first fault; receipt provenance unresolved].

`CARD_Init` creates the card task thread, whose procedure `CARDi_TaskThread` sleeps on a
queue waiting for a card interrupt [H: source account: `port/shim/os/halt.c:25-29`; H: historical measurement account: cycle40 log ENTRY40
`off-D16`, where the port created that thread with a host entry; direct ROM-source provenance unresolved]. The sound side creates one
too, at `CARD_GetThreadPriority() - 1` [S: `src/matched/NNS_SndCaptureCreateThread.c`, `src/matched/CARD_Init.c`, `src/matched/CARDi_TaskThread.c`; source account: `NNS_SndCaptureCreateThread`,
`port/shim/os/sndstart.c:145`]. Above them all sits the MAIN thread, the one that blocks in
`VBlankIntrWait` [H: source account: `port/shim/os/vblank.c:58-64`; direct ROM-source provenance unresolved].

### What the four threads actually do, counted on the hardware

The idle thread is not a corner case: **on the DS it owns the CPU for most of an ordinary
frame**, and the one place it stops the ARM9 — `OS_Halt` at `0x01ffa3c0` — is countable from
outside. An execution sampler on the emulator (`port/tools/oracle/README.md`, the `--exec`
arm) counted entries per frame over two scene transitions.

| | ordinary town play | inside the loader's long sub-entry |
|---|---|---|
| `OS_Halt` entries a frame, town-hall exit | **68.9** | **6.0** |
| `OS_Halt` entries a frame, villager-1's door | **106.1** | **0.7** |
| `CARDi_ReadRom` entries a frame | 51.7 / 5.2 | **278.1 / 198.3** |
| `OS_SleepThread` a frame | 52.5 / 6.6 | 279.1 / 199.4 |
| `OS_IrqHandler` a frame | 274.1 | 268.5 — **the same either way** |

So a loading DS is a BUSY DS, not a halted one, and the interrupt rate is flat across both
states [E: `docs/log/cycle41-gameplay.md` ISSUE57 I57-3/I57-4, `--exec` over frames
49,640..49,800 and 57,180..57,320 ; `scratchpad/issue57/spans-exit.txt`,
`scratchpad/issue57/spans-door.txt`].

What the loader issues instead of halting is the **synchronous cartridge round trip**, and the
counts pin its shape: over the town-hall exit's stage 5 there are 30,957 `CARDi_ReadRom`
entries, 31,085 `OS_SleepThread` (**1.004 per read**) and 62,169 `OS_RescheduleThread`
(**2.008 per read**) — one sleep and two switches per read, exactly the path
`CARDi_Request` → post PXI tag 11 → `OS_SleepThread` → card interrupt → `CARDi_OnFifoRecv` →
`OS_WakeupThread` describes. `CARDi_WaitAsync` and `CARDi_Request`'s async entry are **zero on
all 161 frames**: this loader never takes the async path
[E: ISSUE57 I57-3, I57-6 ; `scratchpad/issue57/spans-exit.txt`].

`OSi_ThreadInfo` is at `0x0220426c` and its `current` field at **`0x02204270`**, read out of
`OS_RescheduleThread`'s literal pool at `0x02114b80` (`str r5,[r1,#4]` at `0x02114b6c` is the
write); `OSi_RescheduleCount` is at `0x02204258` and `OSi_pCurrentThread` at `0x02204264`.
Four `OSThread`s are current across the exit window: **`0x0220427c` is the IDLE thread**
(identified by the frame-boundary pc being inside the idle loop on 11 of 11 frames where it is
current, which are exactly the high-`OS_Halt` frames), `0x0220433c` the MAIN thread,
`0x02206284` the card task and `0x02202ee8` a fourth
[E: ISSUE57 I57-2 ; `scratchpad/issue57/exec-exit-full.txt`].

**The PC port never idles inside a loader body either, and for a different reason.** Its
`OS_Halt` reads exactly **1.0 a frame** in all three census windows — the frame boundary, once,
when the main thread blocks and the fiber scheduler finds nothing runnable — and its
`OS_RescheduleThread` 0.7 a frame against the DS's 558. Neither producer is waiting; the
difference between them is entirely what a cartridge read costs
[E: ISSUE57 I57-5, re-reducing CENSUS56's census logs by address ;
`scratchpad/issue57/portcount-exit-sub.txt`].

### The interrupt table

`OS_IRQTable` is at `0x027e0000`, the bottom of DTCM, and slot 0 is the VBlank —
`OS_SetIrqFunction` writes bit 0 straight into that slot
[H: source account: `port/shim/os/vblank.c:65-68, 80`; direct ROM-source provenance unresolved]. On hardware a VBlank vectors through `0x027ffe20`
into the registered handler, which acknowledges the interrupt and calls `OS_WakeupThread` on
the VBlank queue; that is how a thread blocked in `VBlankIntrWait` becomes runnable again
[H: source account: `port/shim/os/halt.c:17-21`; direct ROM-source provenance unresolved]. Acknowledging is `OS_IrqHandler`'s job, not the handler's
[H: source account: `port/shim/os/vblank.c:68-70`; direct ROM-source provenance unresolved]. `REG_IF` is at `0x04000214`
[H: source account: `port/shim/os/vblank.c:81`; direct ROM-source provenance unresolved]. DMA completion is delivered through `OS_IRQTable[8 + ch]`
[H: source account: `docs/kb/hybrid/hardware-services.md` section 2; direct ROM-source provenance unresolved].

Inside the VBlank the ROM also runs a task list at `0x021f6ca0`, walked by `func_020b98ec`
with each task dispatched through vtable slot 0 [H: source account: `port/shim/gfx/vbtask.c` header; direct ROM-source provenance unresolved]. See
`display-objects.md`.

### The ARM7 and the FIFO

The ARM9 talks to the ARM7 through the PXI FIFO, dispatching on a numbered tag
[H: source account: `docs/kb/hybrid/hardware-services.md` section 1; direct ROM-source provenance unresolved]. The receive
callbacks live in a table at `0x027e0394` indexed by tag, filled by
`PXI_SetFifoRecvCallback` [H: source account: `docs/kb/hybrid/hardware-services.md` section 1; direct ROM-source provenance unresolved]. Live tags:
4 is the NVRAM read of the console's user settings, 5 the RTC, 6 the touch panel, 7 sound
commands, 8 power management, 10 wireless, 11 and 14 the card
[H: source account: `docs/kb/hybrid/hardware-services.md` sections 1 and "Other tags"; direct ROM-source provenance unresolved].

Two of them are worth knowing in detail because their TIMING is part of the protocol. On the
touch panel, the SDK's request functions send FIRST and set `command_flg` AFTER the send
returns, so a reply that arrives inside the send clears nothing and `TP_WaitBusy` spins
forever [H: source account: `docs/kb/hybrid/hardware-services.md` section 1; H: historical measurement account: cycle40 log ENTRY40 `off-D8`,
hung at 15 s; direct ROM-source provenance unresolved]. On the card, `CARDi_Request` sets `CARD_STAT_REQ`, sends tag 11 and sleeps; the
poll that follows the post must see BUSY, as it would on hardware, or the lock is released and
the read starts again [S: `src/matched/func_02050974.c`, `src/matched/TP_WaitBusy.c`, `src/matched/CARDi_Request.c`; source account: `docs/kb/hybrid/hardware-services.md` section 1; H: cycle40 log
CARD40, where a synchronous answer produced the Nintendo-logo wait, `func_02050974` once per
loop, BUSY forever]. `CARDi_OnFifoRecv` tests the reply's error word before clearing REQ and
waking the card thread [H: source account: `docs/kb/hybrid/hardware-services.md` section 1; direct ROM-source provenance unresolved].

### Exceptions

`NitroMain` installs the ROM's own user exception handler `func_0206e6c4` with the argument
word `0x0220433c` [H: source account: `port/platform/nitromain.c:36, 46, 66`; direct ROM-source provenance unresolved]. On a fatal fault the ROM
stores the exception's register table at `0x0213fde0` and `func_020012ec` loops
`func_02001324` — the crash screen, both screens black
[H: log/source account: `docs/log/cycle40-keyboard-gate-probe.md` CARD40..SND40; receipt provenance unresolved].

### How the PC port stands in for all of this

Threads become Windows fibers, and the mapping is structural rather than approximate: a fiber
switches only where `SwitchToFiber` is called, which is a cooperative scheduler's contract
exactly [H: source account: `port/shim/os/thread.c:17-21`; direct ROM-source provenance unresolved]. The one non-literal point is that
`OS_SaveContext` cannot return twice, so it always returns 0 and the resume arrives one call
later, when the `SwitchToFiber` inside `OS_LoadContext` returns; that is an equivalence only
because both spellings resume by returning from `OS_RescheduleThread` with nothing run in
between [H: source account: `port/shim/os/thread.c:24-40`; direct ROM-source provenance unresolved]. Because a fiber brings its own stack, the NDS
thread stacks are unused — which is benign, since the overflow checknums are then never
overwritten and every stack check keeps passing [H: source account: `port/shim/os/thread.c:48-55`; direct ROM-source provenance unresolved]. The port
caps live contexts at 64 and stops by name rather than guessing if that is exceeded
[H: source account: `port/shim/os/thread.c:118, 162-164`; direct ROM-source provenance unresolved].

Only IRQ 0 has a source on the host: timers, DMA completion and the card interrupt have none,
so a game that waits on one of those would wait forever
[H: source account: `port/shim/os/vblank.c:76-79`; direct ROM-source provenance unresolved]. The card is answered instead by performing the work a
frame later, at the next VBlank, which reproduces the BUSY-then-DONE sequence
[H: source account: `docs/kb/hybrid/hardware-services.md` section 1; direct ROM-source provenance unresolved]. `acww_vblank` drains the ARM7's queued
PXI replies first, then dispatches `OS_IRQTable[0]`
[H: source account: `port/shim/os/vblank.c:99-103, 172-180`; direct ROM-source provenance unresolved].

On the interpreter path a handler slot may hold a HOST address — the ROM's own game bring-up
installs one — so the port maps it back to its NDS function and runs that interpreted; without
that, the native VBlank step and the ROM's display walk disagreed and nothing joined the
update list [H: source account: `port/shim/os/vblank.c:152-170`; H: historical measurement account: cycle40 log REG40c `off-D4`; direct ROM-source provenance unresolved].

Two stack faults produced the rule that an interrupt handler cannot share a thread's stack.
Placing the VBlank handler just below the MAIN thread's live interpreted frame let the handler
wake the main thread, which ran a whole frame through that memory, and the handler's return
landed in an object [E: cycle40 log REG40c, `off-D5`/`off-D6` ; `scratchpad/cycle40/runs/off-D5`, `scratchpad/cycle40/runs/off-D6`]. And a PXI reply callback that
ran on the IDLE thread's 0x80-byte stack pushed through its bottom into the launcher thread's
own `OSThread` struct during the wakeup's reschedule [E: cycle40 log CARD40..SND40,
`off-D27` ; `scratchpad/cycle40/runs/off-D27`]. Interrupt-context calls now run on a dedicated 16 KB stack
[H: source account: `docs/kb/hybrid/runtime.md` section 4; direct ROM-source provenance unresolved]. The rule as stated: a callback thunk may share the
caller's stack only while the caller stays suspended; an interrupt handler cannot assume that
[H: source account: `port/interp/interp.h:82-90`; direct ROM-source provenance unresolved].

There is a third way a frame ends on the interpreter path, and during the town sequence it is
the one that fires: the ROM's frame sync `func_0200149c` spins reading `VCOUNT`, so the port
advances a synthetic scanline per read — 263 lines a frame, VBlank set on lines 192 to 262 —
and calls the frame boundary when the counter wraps to line 0, exactly as the idle thread's
`OS_Halt` would have [H: source account: `docs/kb/hybrid/hardware-services.md` section 4; H: historical measurement account: cycle40 log
CARD40..SND40 `off-D36`; direct ROM-source provenance unresolved].

## Where it lives

| function or symbol | module | role | grade / citation |
|---|---|---|---|
| `OS_InitThread` | autoload_2 | builds the thread list; pins the context size at 0x64 | [S: `src/matched/OS_InitThread.c`; source account: `port/shim/os/thread.c:88-92, 231-236`] |
| `OS_SaveContext` / `OS_LoadContext` | itcm | setjmp/longjmp over the ARM register file (assembly) | [S: `src/matched/OS_SaveContext.c`, `src/matched/OS_LoadContext.c`; source account: `port/shim/os/thread.c:5-16`] |
| `OS_RescheduleThread` | autoload_2 | the cooperative switch | [S: `src/matched/OS_RescheduleThread.c`; source account: `port/shim/os/thread.c:31-40`] |
| `OSi_ExitThread_ArgSpecified` | autoload_2 | thread exit; overwrites the context's r0 | [S: `src/matched/OSi_ExitThread_ArgSpecified.c`; source account: `port/shim/os/thread.c:41-44, 59-63`] |
| `OS_CreateThread` / `OS_InitContext` | autoload_2 | build a thread; fill its context and checknums | [S: `src/matched/OS_CreateThread.c`, `src/matched/OS_InitContext.c`; source account: `port/shim/os/thread.c:51-63`] |
| `OSi_IdleThreadProc` / `OS_Halt` | itcm | the idle loop and the CP15 wait-for-interrupt | [S: `src/matched/OSi_IdleThreadProc.c`, `src/matched/OS_Halt.c`; source account: `port/shim/os/halt.c:6-8`] |
| `CARDi_TaskThread` | autoload_2 | the card task; sleeps on a queue | [S: `src/matched/CARDi_TaskThread.c`; source account: `port/shim/os/halt.c:25-29`] |
| `NNS_SndCaptureCreateThread` | autoload_2 | the sound thread, at card priority minus one | [S: `src/matched/NNS_SndCaptureCreateThread.c`; source account: `port/shim/os/sndstart.c:145`] |
| `VBlankIntrWait` (`0x020002c7`) | main | BIOS `IntrWait` wrapper; the game's frame block | [S: `src/matched/VBlankIntrWait.c`, `src/matched/IntrWait.c`; source account: `port/shim/os/vblank.c:1-10`] |
| `OS_SetIrqFunction` | itcm | writes slot 0 for the VBlank bit | [S: `src/matched/OS_SetIrqFunction.c`; source account: `port/shim/os/vblank.c:65-68`] |
| `OS_IrqHandler` | itcm | acknowledges the interrupt around the handler | [S: `src/matched/OS_IrqHandler.c`; source account: `port/shim/os/vblank.c:68-70`] |
| `OS_WakeupThread` | autoload_2 | what the game's VBlank handler calls | [S: `src/matched/OS_WakeupThread.c`; source account: `port/shim/os/halt.c:18-20`] |
| `PXI_SetFifoRecvCallback` | autoload_2 | fills the per-tag receive callback table | [S: `src/matched/PXI_SetFifoRecvCallback.c`; source account: `docs/kb/hybrid/hardware-services.md` section 1] |
| `CARDi_Request` / `CARDi_OnFifoRecv` | autoload_2 | posts a card request and receives its reply | [S: `src/matched/CARDi_Request.c`, `src/matched/CARDi_OnFifoRecv.c`; source account: `docs/kb/hybrid/hardware-services.md` section 1] |
| `TP_WaitBusy` | autoload_2 | spins on the touch command flag | [S: `src/matched/TP_WaitBusy.c`; source account: `docs/kb/hybrid/hardware-services.md` section 1] |
| `func_0206e6c4` | main | the user exception handler `NitroMain` installs | [S: `src/matched/func_0206e6c4.c`; source account: `port/platform/nitromain.c:36, 46`] |
| `func_0200149c` | main | frame sync; spins on `VCOUNT` | [E: cycle40 log CARD40..SND40 `off-D36` ; `scratchpad/cycle40/runs/off-D36`] |
| `func_020b98ec` | main | the VBlank task list walk | [S: `config/adm-kr/arm9/symbols.txt` (`func_020b98ec` at 0x020b98ec); source account: `port/shim/gfx/vbtask.c` header] |

## Data it reads and writes

| address or field | meaning | who writes | who reads |
|---|---|---|---|
| `0x027e0000` | `OS_IRQTable[0]`, the VBlank handler slot | `OS_SetIrqFunction` | the vector, and the port's `acww_vblank` [S: `src/matched/OS_SetIrqFunction.c`; source account: `port/shim/os/vblank.c:80, 99-101`] |
| `OS_IRQTable[8 + ch]` | DMA channel completion handler | `OS_SetIrqFunction` | the DMA completion path [S: `src/matched/OS_SetIrqFunction.c`; source account: `docs/kb/hybrid/hardware-services.md` section 2] |
| `0x027ffe20` | the hardware VBlank vector | crt0 | the CPU [H: source account: `port/shim/os/halt.c:17-19`; direct ROM-source provenance unresolved] |
| `0x027e0394 + tag*4` | PXI receive callback per FIFO tag | `PXI_SetFifoRecvCallback` | PXI delivery [S: `src/matched/PXI_SetFifoRecvCallback.c`; source account: `docs/kb/hybrid/hardware-services.md` section 1] |
| `0x04000214` (`REG_IF`) | interrupt request flags | the controller; the port sets the bit around the call | a handler that reads it [H: source account: `port/shim/os/vblank.c:78-81`; direct ROM-source provenance unresolved] |
| `0x04000208` (`REG_IME`) | interrupt master enable | `NitroMain` | the controller [H: source account: `port/platform/nitromain.c:49`; direct ROM-source provenance unresolved] |
| `OSContext +0x00 / +0x04 / +0x38 / +0x3c / +0x40 / +0x44 / +0x48` | cpsr, r0-r12, sp, lr, pc+4, sp_svc, coprocessor state | `OS_SaveContext`, `OS_InitContext` | `OS_LoadContext` [S: `src/matched/OS_SaveContext.c`, `src/matched/OS_InitContext.c`, `src/matched/OS_LoadContext.c`; source account: `port/shim/os/thread.c:100-107`] |
| `OSThread stackTop` / `stackBottom` | the checknum bounds | `OS_CreateThread` | every stack check [S: `src/matched/OS_CreateThread.c`; source account: `port/shim/os/thread.c:51-55`] |
| `0x0213fde0` | the exception register table on a fatal fault | `func_0206e6c4` via `func_0206e3f4` | the crash screen [H: log/source account: cycle40 log CARD40..SND40; receipt provenance unresolved] |
| `0x021f6ca0` | the VBlank task list head | task registration | `func_020b98ec` [S: `config/adm-kr/arm9/symbols.txt` (`func_020b98ec` at 0x020b98ec); source account: `port/shim/gfx/vbtask.c:22-25`] |

## How to check it

Run any recipe from `docs/kb/hybrid/recipes.md` and read the port's own interrupt instruments:
`acww vblank: frame N OS_IRQTable[0] = <word>` prints the slot for the first frames and on
every change, which separates "the handler was never registered" from "the slot was trampled"
[H: host/prose inference from `port/shim/os/vblank.c:104-127, 175-186`; verify against the ROM function or symbol table and this page's recipe]; and
`acww vblank: handler runs interpreted, NDS <addr>` says the slot's host word was mapped back
to a ROM function [H: host/prose inference from `port/shim/os/vblank.c:158-168`; verify against the ROM function or symbol table and this page's recipe]. An unanswered ARM7 tag names itself
once, in the form `acww pxi: tag N word W accepted and dropped (no ARM7)`, so a later wait can
be traced to the tag nobody answered [H: source account: `docs/kb/hybrid/hardware-services.md` section 1; direct ROM-source provenance unresolved].

A frame loop that runs while the game does not advance is a distinct failure and looks
identical from outside until the thread list is read: the diagnostic signature is thread 0
waiting on a queue, the idle thread spinning through `OS_Halt`, and display registers that do
not change from one frame to the next [H: host-source account from `port/shim/os/vblank.c:58-64`; verify with a retained scripted run and frame using this page's recipe].

## Hypotheses

- The game never waits on a timer interrupt, which is why the port's single interrupt source
  is sufficient through the town [H: 90,000 frames without a stall is evidence for
  (`scratchpad/cycle40/runs/tap-D59`, LONG41); settled by an instrument that names any
  `OS_SetIrqFunction` call for a slot other than 0, 8+ch and the card].
- The sound thread created at card priority minus one never blocks the main thread, so a
  silent ARM7 is safe indefinitely [H: the ROM's sound stack runs against a consumer that
  never reports a real player state, so a sequence whose progression the game WAITS on would
  stall; settled by an oracle comparison over a scene with music-driven timing —
  `docs/kb/hybrid/hardware-services.md` section 7].
- The maximum number of live `OSThread` contexts in real play is well under 64
  [H: settled by logging the port's fiber slot high-water mark over the town recipe;
  exceeding it stops by name rather than silently — `port/shim/os/thread.c:162-164`].
- No caller does real work between its `OS_SaveContext` and its `OS_LoadContext`, which is
  what makes the fiber mapping exact [H: true of the two callers in `src/matched/`; settled
  for the rest by disassembling every caller of either routine across all modules —
  `port/shim/os/thread.c:41-44`].

## Related

- `boot-and-entry.md` — `OS_InitThread`, `OS_EnableInterrupts` and what a frame is
- `memory-map.md` — the bottom of DTCM, where the interrupt table lives
- `display-objects.md` — the task list the VBlank walks
- `scenes-and-channels.md` — the game loop the MAIN thread is running
