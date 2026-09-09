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
coprocessor context from 0x48 to 0x63 [S: `OSContext`, autoload_2,
`port/shim/os/thread.c:80-107`, recovered verbatim from
`src/matched/OSi_ExitThread_ArgSpecified.c`]. The size 0x64 is independently pinned by
`src/matched/OS_InitThread.c`, and the offsets agree with `src/matched/OS_InitContext.c` and
with the two hand-written assembly bodies [S: `port/shim/os/thread.c:84-92`].

The coprocessor context is the ARM9's divider and square-root state: numerator, denominator,
square-root operand, and the two mode words, saved by `CP_SaveContext`
[S: `CPContext`, `port/shim/os/thread.c:93-99`; `port/shim/os/thread.c:57-58`].

`pc_plus4` holds the entry point plus four, deliberately, so that a `ldm ... ^` restore lands
one instruction early [S: `port/shim/os/thread.c:176-179`]. `r[0]` is load-bearing and is
read: it carries the thread procedure's argument, set by `OS_CreateThread` through
`OS_InitContext` and overwritten by `OSi_ExitThread_ArgSpecified`
[S: `port/shim/os/thread.c:59-63`].

### Saving and restoring: setjmp/longjmp over a register file

`OS_SaveContext` stores 1 into the context's own r0 slot and pc+8 into `pc_plus4`, then falls
through returning 0. `OS_LoadContext` restores the file with a user-mode multiple load of r0
through r14 and lands on `subs pc, lr, #4` — the instruction after the store. So the SAVER
sees 0 and the RESUMER sees 1: classic setjmp semantics
[S: `OS_SaveContext` / `OS_LoadContext`, autoload_2, from
`src/matched/OS_SaveContext.c` and `src/matched/OS_LoadContext.c` via
`port/shim/os/thread.c:11-16`]. Both are hand-written ARM assembly bodies
[S: `port/shim/os/thread.c:5-7`].

The scheduler above them is cooperative: `OS_RescheduleThread` runs only where the code calls
it, and a thread runs until it blocks [S: `port/shim/os/thread.c:17-19`]. Its shape is a save,
an early return when the save reports a resume, then the switch callbacks,
`OS_SetCurrentThread`, and `OS_LoadContext` on the next thread
[S: `src/matched/OS_RescheduleThread.c` via `port/shim/os/thread.c:31-40`].
`OS_RescheduleThread` and `OSi_ExitThread_ArgSpecified` are the only two functions in
`src/matched/` that name either routine [S: `port/shim/os/thread.c:41-44`].

`OS_CreateThread` writes two stack-overflow checknums into NDS memory, and
`OS_GetCurrentThread()->stackTop` / `stackBottom` address them
[S: `port/shim/os/thread.c:51-55`]. An `OSThread` procedure does not return: the contract is
that it ends in `OS_ExitThread`, which reschedules and never comes back
[S: `port/shim/os/thread.c:222-225`].

### The threads that exist

The launcher thread arrives as an ordinary thread and is never given a context by
`OS_InitThread`, which only fills in its priority and stack bounds; it acquires one at its
first `OS_SaveContext` [S: `port/shim/os/thread.c:231-236`]. The IDLE thread's whole body is
`while (1) OS_Halt();`, and `OS_Halt` is three ARM instructions around the CP15
wait-for-interrupt [S: `OSi_IdleThreadProc` / `OS_Halt`, itcm,
`port/shim/os/halt.c:6-8`]. Reaching it means the scheduler has correctly concluded that no
thread can run, which on hardware is an entirely normal state
[S: `port/shim/os/halt.c:7-10`]. Its stack is small — 0x80 bytes was measured
[E: `docs/log/cycle40-keyboard-gate-probe.md` CARD40..SND40, first fault].

`CARD_Init` creates the card task thread, whose procedure `CARDi_TaskThread` sleeps on a
queue waiting for a card interrupt [S: `port/shim/os/halt.c:25-29`; E: cycle40 log ENTRY40
`off-D16`, where the port created that thread with a host entry]. The sound side creates one
too, at `CARD_GetThreadPriority() - 1` [S: `NNS_SndCaptureCreateThread`,
`port/shim/os/sndstart.c:145`]. Above them all sits the MAIN thread, the one that blocks in
`VBlankIntrWait` [S: `port/shim/os/vblank.c:58-64`].

### The interrupt table

`OS_IRQTable` is at `0x027e0000`, the bottom of DTCM, and slot 0 is the VBlank —
`OS_SetIrqFunction` writes bit 0 straight into that slot
[S: `port/shim/os/vblank.c:65-68, 80`]. On hardware a VBlank vectors through `0x027ffe20`
into the registered handler, which acknowledges the interrupt and calls `OS_WakeupThread` on
the VBlank queue; that is how a thread blocked in `VBlankIntrWait` becomes runnable again
[S: `port/shim/os/halt.c:17-21`]. Acknowledging is `OS_IrqHandler`'s job, not the handler's
[S: `port/shim/os/vblank.c:68-70`]. `REG_IF` is at `0x04000214`
[S: `port/shim/os/vblank.c:81`]. DMA completion is delivered through `OS_IRQTable[8 + ch]`
[S: `docs/kb/hybrid/hardware-services.md` section 2].

Inside the VBlank the ROM also runs a task list at `0x021f6ca0`, walked by `func_020b98ec`
with each task dispatched through vtable slot 0 [S: `port/shim/gfx/vbtask.c` header]. See
`display-objects.md`.

### The ARM7 and the FIFO

The ARM9 talks to the ARM7 through the PXI FIFO, dispatching on a numbered tag
[S: `docs/kb/hybrid/hardware-services.md` section 1]. The receive
callbacks live in a table at `0x027e0394` indexed by tag, filled by
`PXI_SetFifoRecvCallback` [S: `docs/kb/hybrid/hardware-services.md` section 1]. Live tags:
4 is the NVRAM read of the console's user settings, 5 the RTC, 6 the touch panel, 7 sound
commands, 8 power management, 10 wireless, 11 and 14 the card
[S: `docs/kb/hybrid/hardware-services.md` sections 1 and "Other tags"].

Two of them are worth knowing in detail because their TIMING is part of the protocol. On the
touch panel, the SDK's request functions send FIRST and set `command_flg` AFTER the send
returns, so a reply that arrives inside the send clears nothing and `TP_WaitBusy` spins
forever [S: `docs/kb/hybrid/hardware-services.md` section 1; E: cycle40 log ENTRY40 `off-D8`,
hung at 15 s]. On the card, `CARDi_Request` sets `CARD_STAT_REQ`, sends tag 11 and sleeps; the
poll that follows the post must see BUSY, as it would on hardware, or the lock is released and
the read starts again [S: `docs/kb/hybrid/hardware-services.md` section 1; E: cycle40 log
CARD40, where a synchronous answer produced the Nintendo-logo wait, `func_02050974` once per
loop, BUSY forever]. `CARDi_OnFifoRecv` tests the reply's error word before clearing REQ and
waking the card thread [S: `docs/kb/hybrid/hardware-services.md` section 1].

### Exceptions

`NitroMain` installs the ROM's own user exception handler `func_0206e6c4` with the argument
word `0x0220433c` [S: `port/platform/nitromain.c:36, 46, 66`]. On a fatal fault the ROM
stores the exception's register table at `0x0213fde0` and `func_020012ec` loops
`func_02001324` — the crash screen, both screens black
[E: `docs/log/cycle40-keyboard-gate-probe.md` CARD40..SND40].

### How the PC port stands in for all of this

Threads become Windows fibers, and the mapping is structural rather than approximate: a fiber
switches only where `SwitchToFiber` is called, which is a cooperative scheduler's contract
exactly [S: `port/shim/os/thread.c:17-21`]. The one non-literal point is that
`OS_SaveContext` cannot return twice, so it always returns 0 and the resume arrives one call
later, when the `SwitchToFiber` inside `OS_LoadContext` returns; that is an equivalence only
because both spellings resume by returning from `OS_RescheduleThread` with nothing run in
between [S: `port/shim/os/thread.c:24-40`]. Because a fiber brings its own stack, the NDS
thread stacks are unused — which is benign, since the overflow checknums are then never
overwritten and every stack check keeps passing [S: `port/shim/os/thread.c:48-55`]. The port
caps live contexts at 64 and stops by name rather than guessing if that is exceeded
[S: `port/shim/os/thread.c:118, 162-164`].

Only IRQ 0 has a source on the host: timers, DMA completion and the card interrupt have none,
so a game that waits on one of those would wait forever
[S: `port/shim/os/vblank.c:76-79`]. The card is answered instead by performing the work a
frame later, at the next VBlank, which reproduces the BUSY-then-DONE sequence
[S: `docs/kb/hybrid/hardware-services.md` section 1]. `acww_vblank` drains the ARM7's queued
PXI replies first, then dispatches `OS_IRQTable[0]`
[S: `port/shim/os/vblank.c:99-103, 172-180`].

On the interpreter path a handler slot may hold a HOST address — the ROM's own game bring-up
installs one — so the port maps it back to its NDS function and runs that interpreted; without
that, the native VBlank step and the ROM's display walk disagreed and nothing joined the
update list [S: `port/shim/os/vblank.c:152-170`; E: cycle40 log REG40c `off-D4`].

Two stack faults produced the rule that an interrupt handler cannot share a thread's stack.
Placing the VBlank handler just below the MAIN thread's live interpreted frame let the handler
wake the main thread, which ran a whole frame through that memory, and the handler's return
landed in an object [E: cycle40 log REG40c, `off-D5`/`off-D6`]. And a PXI reply callback that
ran on the IDLE thread's 0x80-byte stack pushed through its bottom into the launcher thread's
own `OSThread` struct during the wakeup's reschedule [E: cycle40 log CARD40..SND40,
`off-D27`]. Interrupt-context calls now run on a dedicated 16 KB stack
[S: `docs/kb/hybrid/runtime.md` section 4]. The rule as stated: a callback thunk may share the
caller's stack only while the caller stays suspended; an interrupt handler cannot assume that
[S: `port/interp/interp.h:82-90`].

There is a third way a frame ends on the interpreter path, and during the town sequence it is
the one that fires: the ROM's frame sync `func_0200149c` spins reading `VCOUNT`, so the port
advances a synthetic scanline per read — 263 lines a frame, VBlank set on lines 192 to 262 —
and calls the frame boundary when the counter wraps to line 0, exactly as the idle thread's
`OS_Halt` would have [S: `docs/kb/hybrid/hardware-services.md` section 4; E: cycle40 log
CARD40..SND40 `off-D36`].

## Where it lives

| function or symbol | module | role | grade / citation |
|---|---|---|---|
| `OS_InitThread` | autoload_2 | builds the thread list; pins the context size at 0x64 | [S: `port/shim/os/thread.c:88-92, 231-236`] |
| `OS_SaveContext` / `OS_LoadContext` | itcm | setjmp/longjmp over the ARM register file (assembly) | [S: `port/shim/os/thread.c:5-16`] |
| `OS_RescheduleThread` | autoload_2 | the cooperative switch | [S: `port/shim/os/thread.c:31-40`] |
| `OSi_ExitThread_ArgSpecified` | autoload_2 | thread exit; overwrites the context's r0 | [S: `port/shim/os/thread.c:41-44, 59-63`] |
| `OS_CreateThread` / `OS_InitContext` | autoload_2 | build a thread; fill its context and checknums | [S: `port/shim/os/thread.c:51-63`] |
| `OSi_IdleThreadProc` / `OS_Halt` | itcm | the idle loop and the CP15 wait-for-interrupt | [S: `port/shim/os/halt.c:6-8`] |
| `CARDi_TaskThread` | autoload_2 | the card task; sleeps on a queue | [S: `port/shim/os/halt.c:25-29`] |
| `NNS_SndCaptureCreateThread` | autoload_2 | the sound thread, at card priority minus one | [S: `port/shim/os/sndstart.c:145`] |
| `VBlankIntrWait` (`0x020002c7`) | main | BIOS `IntrWait` wrapper; the game's frame block | [S: `port/shim/os/vblank.c:1-10`] |
| `OS_SetIrqFunction` | itcm | writes slot 0 for the VBlank bit | [S: `port/shim/os/vblank.c:65-68`] |
| `OS_IrqHandler` | itcm | acknowledges the interrupt around the handler | [S: `port/shim/os/vblank.c:68-70`] |
| `OS_WakeupThread` | autoload_2 | what the game's VBlank handler calls | [S: `port/shim/os/halt.c:18-20`] |
| `PXI_SetFifoRecvCallback` | autoload_2 | fills the per-tag receive callback table | [S: `docs/kb/hybrid/hardware-services.md` section 1] |
| `CARDi_Request` / `CARDi_OnFifoRecv` | autoload_2 | posts a card request and receives its reply | [S: `docs/kb/hybrid/hardware-services.md` section 1] |
| `TP_WaitBusy` | autoload_2 | spins on the touch command flag | [S: `docs/kb/hybrid/hardware-services.md` section 1] |
| `func_0206e6c4` | main | the user exception handler `NitroMain` installs | [S: `port/platform/nitromain.c:36, 46`] |
| `func_0200149c` | main | frame sync; spins on `VCOUNT` | [E: cycle40 log CARD40..SND40 `off-D36`] |
| `func_020b98ec` | main | the VBlank task list walk | [S: `port/shim/gfx/vbtask.c` header] |

## Data it reads and writes

| address or field | meaning | who writes | who reads |
|---|---|---|---|
| `0x027e0000` | `OS_IRQTable[0]`, the VBlank handler slot | `OS_SetIrqFunction` | the vector, and the port's `acww_vblank` [S: `port/shim/os/vblank.c:80, 99-101`] |
| `OS_IRQTable[8 + ch]` | DMA channel completion handler | `OS_SetIrqFunction` | the DMA completion path [S: `docs/kb/hybrid/hardware-services.md` section 2] |
| `0x027ffe20` | the hardware VBlank vector | crt0 | the CPU [S: `port/shim/os/halt.c:17-19`] |
| `0x027e0394 + tag*4` | PXI receive callback per FIFO tag | `PXI_SetFifoRecvCallback` | PXI delivery [S: `docs/kb/hybrid/hardware-services.md` section 1] |
| `0x04000214` (`REG_IF`) | interrupt request flags | the controller; the port sets the bit around the call | a handler that reads it [S: `port/shim/os/vblank.c:78-81`] |
| `0x04000208` (`REG_IME`) | interrupt master enable | `NitroMain` | the controller [S: `port/platform/nitromain.c:49`] |
| `OSContext +0x00 / +0x04 / +0x38 / +0x3c / +0x40 / +0x44 / +0x48` | cpsr, r0-r12, sp, lr, pc+4, sp_svc, coprocessor state | `OS_SaveContext`, `OS_InitContext` | `OS_LoadContext` [S: `port/shim/os/thread.c:100-107`] |
| `OSThread stackTop` / `stackBottom` | the checknum bounds | `OS_CreateThread` | every stack check [S: `port/shim/os/thread.c:51-55`] |
| `0x0213fde0` | the exception register table on a fatal fault | `func_0206e6c4` via `func_0206e3f4` | the crash screen [E: cycle40 log CARD40..SND40] |
| `0x021f6ca0` | the VBlank task list head | task registration | `func_020b98ec` [S: `port/shim/gfx/vbtask.c:22-25`] |

## How to check it

Run any recipe from `docs/kb/hybrid/recipes.md` and read the port's own interrupt instruments:
`acww vblank: frame N OS_IRQTable[0] = <word>` prints the slot for the first frames and on
every change, which separates "the handler was never registered" from "the slot was trampled"
[S: `port/shim/os/vblank.c:104-127, 175-186`]; and
`acww vblank: handler runs interpreted, NDS <addr>` says the slot's host word was mapped back
to a ROM function [S: `port/shim/os/vblank.c:158-168`]. An unanswered ARM7 tag names itself
once, in the form `acww pxi: tag N word W accepted and dropped (no ARM7)`, so a later wait can
be traced to the tag nobody answered [S: `docs/kb/hybrid/hardware-services.md` section 1].

A frame loop that runs while the game does not advance is a distinct failure and looks
identical from outside until the thread list is read: the diagnostic signature is thread 0
waiting on a queue, the idle thread spinning through `OS_Halt`, and display registers that do
not change from one frame to the next [E: `port/shim/os/vblank.c:58-64`].

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
