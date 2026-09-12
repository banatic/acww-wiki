# Boot and entry

**Summary.** From power-on the ARM9 runs NitroSDK's hand-written startup, then three things
in a fixed order: a hardware/wireless/filesystem bring-up routine, the C++ static
initialisers, and the game's own `NitroMain`. `NitroMain` starts the OS tick, alarms and
threads, installs an exception handler, enables interrupts and hands control to the game,
which never returns. On the PC port's interpreter path all three of those run as the ROM's
own ARM and Thumb bytes, and the host supplies only the hardware underneath them. If you are
debugging a boot that shows the Nintendo logo forever, the sequence on this page is the frame
to hang the symptom on.

## What happens

### The entry chain

The NDS header's entry chain lands in `Entry` at `0x02000800`, NitroSDK crt0's hand-written
ARM startup: it sets CP15, builds the SVC/IRQ/system stacks, clears OAM and palette RAM and
flushes the cache [S: `src/matched/Entry.c`; source account: `Entry`, main, `port/platform/nitromain.c` header]. None of that is a
decompilable C body — it is one of the assembly translation units the host build cannot
compile at all [H: source account: `port/platform/nitromain.c` header; `port/tools/expected_failed_tus.txt`; direct ROM-source provenance unresolved].

`Entry` ends with four instructions, and they are the boot order of record: a call to
`0x02137124` (a `bx lr` no-op), a call to `func_020b1a74` (hardware, wireless and filesystem
bring-up), a call to `func_02138968` (`__init_cpp`, the static initialisers), and finally a
literal-pool load of `0x02000c39` followed by a branch-exchange into it
[S: `src/matched/Entry.c`, `src/matched/func_020b1a74.c`, `src/matched/func_02138968.c`; source account: `Entry`, main, quoted in `port/platform/win32.c:2340-2348`].

The order is load-bearing rather than incidental: the port's own first arrangement ran
`__init_cpp` before the bring-up, and the constructors then built their first objects against
a machine whose heap, VRAM banks and filesystem did not exist yet [H: host-source account from `port/platform/win32.c:2346-2349`; verify with a retained scripted run and frame using this page's recipe].

### The real entry point has no symbol of its own

`0x02000c38` is the 0x60-byte Thumb routine `Entry` branches to, and no symbol starts there
[H: source account: `port/platform/nitromain.c` header; direct ROM-source provenance unresolved]. The symbol table cuts a 0x174-byte Thumb symbol
`func_02000b6c` that begins 0xcc bytes earlier, so the entry routine arrives with 0xcc bytes
of read-only version strings prepended to it — `0x02000b6c + 0xcc = 0x02000c38` exactly
[S: `src/matched/Entry.c`; source account: `func_02000b6c`, main, `port/platform/nitromain.c` header]. This is the first of several
places where a mis-cut boundary, not the ROM, is the thing that looks wrong; see
`memory-map.md` for the address-arena consequences.

### What `NitroMain` does

Read off the ROM at `0x02000c38`, the routine is NitroSDK's `NitroMain` shape and calls, in
order: `OS_InitTick`, `OS_InitAlarm`, `OS_InitThread`, then `OS_SetUserExceptionHandler` with
the ROM's own handler `func_0206e6c4` and the argument word `0x0220433c`
[H: source account: `port/platform/nitromain.c:33-46, 62-66`; direct ROM-source provenance unresolved]. It then reads `REG_IME` (`0x04000208`) and
writes 1 into it, calls `OS_EnableInterrupts`, and calls `func_0206e518`
[H: source account: `port/platform/nitromain.c:68-75`; direct ROM-source provenance unresolved]. The `REG_IME` read is dead as a value and live as a
hardware access — the ROM overwrites the loaded register immediately — which is why the port
keeps it as a volatile read [H: source account: `port/platform/nitromain.c:67-71`; direct ROM-source provenance unresolved].

A second path exists behind the boot flag at `0x027ffc20`: when it holds 1, the routine also
calls `func_0206e464`, touches `REG_IME` again, and calls `func_02116a1c(2)`
[H: source account: `port/platform/nitromain.c:77-82`; direct ROM-source provenance unresolved]. Both paths end the same way, with `func_020b1b84`
and then `func_0206e560`, and the routine never returns
[H: source account: `port/platform/nitromain.c:84-85`; direct ROM-source provenance unresolved]. `func_0206e560` is where the game proper begins;
everything in `scenes-and-channels.md` happens below it.

The exception handler installed here is not decoration. When the ROM takes a fatal fault it
stores the exception's register table at `0x0213fde0` through
`func_0206e3f4 -> func_0206e6c4`, and `func_020012ec` then loops `func_02001324` — the ROM's
own crash screen, with both screens black [H: log/source account: `docs/log/cycle40-keyboard-gate-probe.md`,
CARD40..SND40; observed from frame ~830 of an interpreter run; receipt provenance unresolved].

### The bring-up routine, and the last call in it

`func_020b1a74` is Thumb and does the hardware, wireless and filesystem bring-up
[S: `src/matched/func_020b1a74.c`; source account: `func_020b1a74`, main, `port/interp/interp_boot.c:29`]. Its LAST call is `func_020ea48c`,
the game's main heap carve-out, so nothing after the bring-up can run until that heap exists
[S: `src/matched/func_020b1a74.c`; source account: `func_020ea48c`, autoload_2, `port/shim/boot/heapinit.c` header]. That function reads
`OS_GetArenaLo(0)` and `OS_GetArenaHi(0)`, rounds the low end up to 32 bytes BEFORE
subtracting so the size already pays for the alignment padding, and allocates the remainder
from arena 0 [S: `src/matched/func_020b1a74.c`; source account: `func_020ea48c`, autoload_2, `port/shim/boot/heapinit.c` header]. See
`memory-map.md` for what it builds in that block.

Interpreted end to end, the bring-up is 3,917 steps and the static initialisers are 21,402
[E: `docs/log/cycle40-keyboard-gate-probe.md` ENTRY40, runs `off-D17`..`off-D20` ; `scratchpad/cycle40/runs/off-D17`, `scratchpad/cycle40/runs/off-D20`].

### Boot on the PC port's interpreter path

With `ACWW_INTERP=1` the port does not call its own transcription of any of this: it runs the
ROM's `Entry` order — `0x020b1a75`, `0x02138968`, `0x02000c39` — through the interpreter, with
the interpreter's hooks installed first [H: source account: `port/interp/interp_boot.c:28-30, 404-418`; direct ROM-source provenance unresolved]. The
native bring-up, the native `__init_cpp` and the native sound boot are all skipped, and the
port says so on stdout [H: source account: `port/platform/win32.c:2355-2405`; direct ROM-source provenance unresolved].

The boot line names the registry size, the entry and the stack, in the form
`acww interp: BOOT via interpreter, registry entries=N entry=0x02000c39 stack=0x027e3e00`
[H: source account: `port/interp/interp_boot.c:395-401`; direct ROM-source provenance unresolved]. The interpreted system stack top is `0x027e3e00`,
placed below NitroSDK's IRQ (0x100) and SVC (0x40) stacks at the top of DTCM
[H: source account: `port/interp/interp_boot.c:11-14, 31`; direct ROM-source provenance unresolved].

Two ordering facts were paid for with faults. Running the native bring-up first made native
`CARD_Init` create the card task thread with a HOST entry, which the fiber then tried to
interpret before any hook existed [E: `docs/log/cycle40-keyboard-gate-probe.md` ENTRY40,
`off-D16` ; `scratchpad/cycle40/runs/off-D16`]. And the sound command layer had to move AFTER the interpreted bring-up, because
`SND_CommandInit` waits for the PXI bit that the ROM's own `PXI_Init` sets
[E: `docs/log/cycle40-keyboard-gate-probe.md` ENTRY40, `off-D17`..`off-D20` ; `scratchpad/cycle40/runs/off-D17`, `scratchpad/cycle40/runs/off-D20`].

One piece of the console's own state is not ROM code and not PXI either: the NVRAM read of
the user settings (PXI tag 4) comes from a symbol-less region at `0x02000c98`, and the port
supplies it by address because there is no name to register [H: source account: `port/tools/interp_registry.py:77-80`;
H: historical measurement account: `docs/log/cycle40-keyboard-gate-probe.md` ENTRY40, `off-D18`, where the read spun forever; direct ROM-source provenance unresolved].

### After boot: what a frame is

The NDS has no frame loop [H: source account: `port/shim/os/vblank.c:11-14`; direct ROM-source provenance unresolved]. The game's loop ends by blocking in `VBlankIntrWait`
(`0x020002c7`, three instructions around the BIOS `IntrWait`), and the vertical-blank
interrupt is what makes time pass [S: `src/matched/VBlankIntrWait.c`, `src/matched/IntrWait.c`; source account: `VBlankIntrWait`, main, `port/shim/os/vblank.c` header].
The idle thread's whole body is `while (1) OS_Halt();`, and `OS_Halt` is the CP15
wait-for-interrupt [S: `src/matched/OSi_IdleThreadProc.c`, `src/matched/OS_Halt.c`, `src/matched/VBlankIntrWait.c`, `src/matched/IntrWait.c`; source account: `OSi_IdleThreadProc` / `OS_Halt`, itcm, `port/shim/os/halt.c` header].

On the interpreter path a third thing can end a frame, and it is the one that actually does
during the town sequence: the ROM's frame sync `func_0200149c` spins reading `VCOUNT`, so the
port's I/O load hook advances a synthetic scanline per read and calls the frame boundary when
the counter wraps to line 0 [H: source account: `port/interp/interp_boot.c:239-254`;
H: historical measurement account: `docs/log/cycle40-keyboard-gate-probe.md` CARD40..SND40, `off-D36`; direct ROM-source provenance unresolved]. Without that rule
nothing on the state-machine path ever reached a frame boundary at all
[H: log/source account: same run; receipt provenance unresolved]. See `threads-and-interrupts.md`.

### How far the boot gets

An interpreted run of the scripted town recipe reaches the taxi interior with the name
keyboard by frame 4,500, the town in front of the town hall at 37,500, and the inside of the
town hall by 40,500, running 48,000 frames with no fault and no interpreter stop
[E: `scratchpad/cycle40/runs/tap-D56`, 31 shots; `docs/log/cycle40-keyboard-gate-probe.md` TOWN40].
The same recipe run through the pipeline's receipt path finished at 48,000 frames in 801 s
with child exit 100 [E: `scratchpad/cycle40/runs/town-R1`; RECEIPT41]. A longer run reached
90,000 frames without a status stop [E: `scratchpad/cycle40/runs/tap-D59`; LONG41].

From frame 6,000 to 24,000 the port and the DeSmuME reference are on the same screen step for
step, bottom-screen normalised cross-correlation 0.9997 to 1.0000
[O: `scratchpad/oracle/tap-fullpad`, compared against `tap-D56`; ORACLE41]. They diverge at
25,500, where the port's two scheduled taps confirm the town name and the original's identical
taps do not [E+O: `scratchpad/cycle40/runs/tap-D59`; LONG41 comparison]. **That divergence is settled (ORACLE42)**: the tap at 24,600
lands on a KEYS3 A-press frame (2400 + 37 x 600) and the original's stylus sample reaches the
game one to two frames later than the port's, so the two order the press and the tap
differently; moved to 24,700 both sides confirm and agree, 11 frames 24,000..27,000 at mean ncc
0.9955 [H: source account: `docs/log/cycle40-keyboard-gate-probe.md` ORACLE42; H: historical measurement account: `tap-D62`;
O: `scratchpad/oracle/tap-24700`; direct ROM-source provenance unresolved]. Since TOUCH42 the port reproduces that ordering rather than
avoiding it, and the 24,600 recipe behaves as the original does
[E: `scratchpad/cycle40/runs/tap-T42b`] [O: `scratchpad/oracle/tap-window`;
`../experiments/touch-latency.md`].

## Where it lives

| function or symbol | module | role | grade / citation |
|---|---|---|---|
| `Entry` (`0x02000800`) | main | crt0: CP15, stacks, OAM/palette clear, cache flush | [S: `src/matched/Entry.c`; source account: `port/platform/nitromain.c` header] |
| `func_020b1a74` (Thumb) | main | hardware, wireless and filesystem bring-up | [S: `src/matched/func_020b1a74.c`; source account: `port/interp/interp_boot.c:29`] |
| `func_020ea48c` | autoload_2 | the bring-up's last call: carve the game heap from arena 0 | [S: `config/adm-kr/arm9/autoload_2/symbols.txt` (`func_020ea48c` at 0x020ea48c); source account: `port/shim/boot/heapinit.c` header] |
| `func_02138968` (ARM) | main | `__init_cpp`, the C++ static initialisers | [S: `src/matched/func_02138968.c`; source account: `port/interp/interp_boot.c:30`] |
| `0x02000c38` (Thumb, 0x60 bytes) | main | the real `NitroMain`; no symbol starts here | [H: source account: `port/platform/nitromain.c` header; direct ROM-source provenance unresolved] |
| `OS_InitTick` / `OS_InitAlarm` / `OS_InitThread` | autoload_2 | OS services, in that order | [S: `src/matched/OS_InitTick.c`, `src/matched/OS_InitAlarm.c`, `src/matched/OS_InitThread.c`; source account: `port/platform/nitromain.c:33-35`] |
| `OS_SetUserExceptionHandler` (`0x0211628c`) | autoload_2 | installs `func_0206e6c4` with arg `0x0220433c` | [S: `src/matched/OS_SetUserExceptionHandler.c`, `src/matched/func_0206e6c4.c`; source account: `port/platform/nitromain.c:36, 46`] |
| `OS_EnableInterrupts` (`0x01ffa314`) | itcm | interrupts on | [S: `src/matched/OS_EnableInterrupts.c`; source account: `port/platform/nitromain.c:37`] |
| `func_0206e518`, `func_020b1b84`, `func_0206e560` | main | the hand-over to the game; never returns | [S: `src/matched/func_0206e518.c`, `src/matched/func_020b1b84.c`, `src/matched/func_0206e560.c`; source account: `port/platform/nitromain.c:75, 84-85`] |
| `func_0206e6c4` / `func_0206e3f4` | main | fatal path: stores the register table, then the crash screen | [H: log/source account: cycle40 log, CARD40..SND40; receipt provenance unresolved] |
| `VBlankIntrWait` (`0x020002c7`) | main | the frame boundary the game blocks on | [S: `src/matched/VBlankIntrWait.c`; source account: `port/shim/os/vblank.c` header] |
| `OS_Halt` | itcm | the idle thread's body | [S: `src/matched/OS_Halt.c`; source account: `port/shim/os/halt.c` header] |
| `func_0200149c` | main | frame sync; spins on `VCOUNT` | [E: cycle40 log, CARD40..SND40 `off-D36` ; `scratchpad/cycle40/runs/off-D36`] |

## Data it reads and writes

| address | meaning | who writes | who reads |
|---|---|---|---|
| `0x04000208` (`REG_IME`) | interrupt master enable; set to 1 twice on the flagged path | `NitroMain` | the interrupt controller [H: source account: `port/platform/nitromain.c:49, 68-81`; direct ROM-source provenance unresolved] |
| `0x027ffc20` | boot flag; 1 selects the second boot path | set before `NitroMain` | `NitroMain` [H: source account: `port/platform/nitromain.c:50, 77`; direct ROM-source provenance unresolved] |
| `0x0220433c` | the user exception handler's argument word | ROM literal pool | `OS_SetUserExceptionHandler` [S: `src/matched/OS_SetUserExceptionHandler.c`; source account: `port/platform/nitromain.c:48`] |
| `0x0213fde0` | the exception register table on a fatal fault | `func_0206e6c4` | the crash screen, and `ACWW_INTERP_PEEK` [H: log/source account: cycle40 log, CARD40..SND40; receipt provenance unresolved] |
| `0x027fff9c` | the interrupt-vector slot crt0 writes | `Entry` | the vector [S: `src/matched/Entry.c`; source account: `port/platform/win32.c:78-83`] |
| `0x027e3e00` | interpreted system stack top (port only) | `interp_boot.c` | the interpreter [H: source account: `port/interp/interp_boot.c:31`; direct ROM-source provenance unresolved] |

## How to check it

The control recipe is the OFF arm — the custom START9000 keys with touch disabled — run
before any other arm and compared frame-for-frame against the retained native run:

    sh scratchpad/cycle40/iterate.sh <name>

which relinks, runs `ACWW_INTERP=1 ACWW_TOUCH_ENABLE=0 ACWW_STOP_FRAME=9000
ACWW_SHOT_AFTER=4500`, and compares all 31 BMPs by SHA256; 31 of 31 equal is the pass
[H: source account: `docs/kb/hybrid/recipes.md` section 2; direct ROM-source provenance unresolved]. The boot itself is legible from the log without
any screenshot: look for the `interpreter path:` line, then the
`acww interp: BOOT via interpreter, registry entries=...` line, then the absence of a `STOP`
line [H: host/prose inference from `port/interp/interp_boot.c:395-401, 419-428`; verify against the ROM function or symbol table and this page's recipe].

To go past the title, the two-tap town recipe in `docs/kb/hybrid/recipes.md` section 3 is the
one that reaches the town hall; it pins the console clock to `20050615` / `100000` so the
oracle can pin the same instant [H: source account: `docs/kb/hybrid/recipes.md` sections 3 and 6; direct ROM-source provenance unresolved].

## Hypotheses

- The 0xcc bytes of version strings prepended to the entry routine are `OSi_ReferSymbol`
  data, not code [H: settled by resolving every literal-pool reference into
  `0x02000b6c`..`0x02000c37` and showing none is a branch target].
- The second boot path behind `0x027ffc20 == 1` is never taken on a cold boot of the retail
  cartridge [H: settled by an oracle run reading the flag at the first frame, and by an
  interpreted run reporting whether `func_0206e464` is ever entered].
- The interpreter's boot speed (~59 frames/s unpaced on the town recipe) is adequate for
  paced live play [H: settled by a paced live run with keyboard and mouse; no such run exists
  — `docs/kb/hybrid/open-questions.md`].
- Nothing on the reachable boot path uses `LDM/STM ^` forms, a `SWI` from game code, or a
  struct-by-value return [H: 90,000 frames without a status stop is evidence for, not proof;
  settled by an interpreter that names those shapes when it meets them — `docs/HYBRID-PLAN.md`
  phases H1/H2].

## Related

- `memory-map.md` — the arena the bring-up's last call carves the game heap from
- `threads-and-interrupts.md` — what `OS_InitThread` builds, and what a VBlank does
- `overlays.md` — the filesystem the bring-up starts, and the first overlay load
- `scenes-and-channels.md` — what `func_0206e560` hands control to
- `interpreter-path.md` — the deny list, and how a native body earns the hot path
- `../experiments/savestate-resume.md` — snapshotting a run of this path and resuming exactly
