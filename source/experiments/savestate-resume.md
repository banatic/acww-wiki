# Savestate and resume: reaching a late frame in one minute instead of ten

**Status: run.** Snapshot an interpreter run at frame N, resume from the file, and the
resumed run is **byte-identical** to the run that wrote it for every frame after N. This is
the instrument that makes an experiment about the town, the town hall or anything else past
frame 24,000 affordable.

## Purpose

Every late observation in this wiki has been paid for with a full replay: the two-tap town
recipe costs about 750 seconds before its first interesting frame, and a question that needs
three variants costs an hour of wall clock in which nothing is being learned. A snapshot moves
that cost to once. But a snapshot is only useful if resuming from it is **exact** -- a resume
that is merely similar turns every later comparison into an argument about whether the
difference came from the change under test or from the snapshot. So the standard here is
`exact-rgb`, not `ncc`, and the receipts below are what earns it.

## What a snapshot is

A snapshot file holds three things [S: `port/platform/state.c`; `docs/kb/hybrid/savestate.md`
sections 1 and 3]:

1. **The seven mapped NDS regions** -- main RAM at `0x02000000` (4 MB, listed once because
   `0x02400000` and the `0x027f0000` system-RAM window are views of the same mapping), DTCM at
   `0x027e0000` (64 KB, its own allocation), the I/O page at `0x04000000`, palette at
   `0x05000000`, VRAM at `0x06000000` (8.6 MB), OAM at `0x07000000`, and the 39 MB
   unplaced-symbol arena at `0x30000000`. Pages are stored with a per-4 KB zero bitmap, so
   52 MB of address space becomes a file of about 4.7 MB.
2. **113 named blobs from 18 registrars** (118 from 20 since RTC42) -- the host-side statics that carry game state
   across frames and that nothing rebuilds from NDS memory: the frame counter, the tick
   accumulator, the interpreter's synthetic scanline phase and IRQ stack, the geometry
   engine's whole register file (30 declarations that the I/O page does not publish), the
   GX FIFO parser's position, the overlay residency table, the PXI reply queue, the sound
   service's ownership state machine, the scripted key phases. The count was 111 when the
   subagent's receipts were taken, was 113 on the merged tree at SAVE41 -- and is **118 from
   20 registrars** since RTC42 added the clock's boot instant, freeze flag and decided flag
   [E: `docs/kb/hybrid/savestate.md` section 3; `docs/log/cycle41-gameplay.md` RTC42, item 6,
   whose savestate pair is 21/21 identical with the clock coming from the blob]. Every
   receipt below was taken at 113 and a `.st` file is refused on any other build anyway, so
   the count is a fact about a build, not about the format (the TOUCH41 sampler's
   `tp_auto_on` / `tp_frequence` and `raster3d.c`'s `ever` were registered during the merge)
   [S: `docs/log/cycle40-keyboard-gate-probe.md` SAVE41].
3. **One interpreter register file per live thread.** ROM threads are Windows fibers, and the
   only place a fiber ever stops is `SwitchToFiber` inside `OS_LoadContext`, so a suspended
   fiber's host stack is always exactly **one** interpreter frame deep with everything below
   it in NDS memory [S: `port/shim/os/thread.c`; `docs/kb/hybrid/savestate.md` section 5].

The header **pins the link**: image base, PE TimeDateStamp, `SizeOfImage`,
`AddressOfEntryPoint`, the exe's size on disk, and the interpreter registry's entry count. A
load compares all six and refuses by name on any difference, because the failure it prevents
would look like a game bug rather than like a stale file. Relink, and every earlier snapshot is
refused [S: `docs/kb/hybrid/savestate.md` section 5].

## What is rebuilt rather than captured

Fibers (a host stack cannot be written to a file); every Win32 handle -- the window, its DC and
DIB, the watchdog thread, the sixteen-handle file cache (`romfs.c` seeks absolutely before
every read, so no file position needs carrying); the interpreter's hooks and the host-body
registry, re-installed by `acww_interp_boot` before the load point, which is *why* the load
point is where it is; the `.fun` / `.ovl` / `.dark` side tables; the trampoline pool's bytes,
re-emitted from the hash table so the `call rel32` displacement belongs to this image; and the
virtual cartridge, whose `acww_romfs_mount()` has exactly one caller (`CARD_Init`) that a
resumed run never reaches, so the load path calls it explicitly
[S: `docs/kb/hybrid/savestate.md` section 4].

Environment-derived caches are re-read, so **a loading run must use the same `ACWW_*`
environment as the saving run** for anything that changes behaviour -- `ACWW_RTC_DATE` and
`ACWW_RTC_TIME` are the sharp case. The scripted key phases are the deliberate exception and
are carried as blobs, so a resumed run reproduces the saving run rather than a
differently-configured one [S: same].

## The refusal rules -- what the instrument declines to do

Each of these writes nothing and says why, rather than producing a snapshot that would fail
subtly later [S: `docs/kb/hybrid/savestate.md` sections 5, 6, 8]:

| refusal | why |
|---|---|
| a fiber whose interpreter call chain is not exactly one frame deep | its register file is not something a resume could restore. **Not every frame is a legal save point** -- 6,000 and 24,000 both took first time; ten frames sampled between 6,061 and 6,150 were all refused. A refusal is common and is not a defect: pick another frame |
| a build identity mismatch on any of the six header fields | exit 9, both identities printed. Measured on a relink where the exe's **size was unchanged** and the timestamp and entry point were not -- the case a size-only check would have missed |
| a return site that would have to be normalised out of a rewritten host word | resuming a mid-host-call frame would re-execute the call; `acww_interp_cpu_resume_image` writes the state the frame *will* have, and refuses rather than guessing |
| a trampoline pool that did not land at `0x20000000` | the ROM stores pool addresses into RAM the snapshot captures, so the pool base is part of the identity |

Two known gaps, stated so nobody trips over them: `ACWW_SAVE`'s flash image is a
`MapViewOfFile` of the named file, so it is **shared, not copied** -- a reload sees the file as
it is now (the scripted recipes unset `ACWW_SAVE`); and a handful of env-gated one-shots
(`ACWW_GENTOWN`, `ACWW_REQ_SCENE`, `ACWW_DEMO_OV4`, `ACWW_LOAD_OVL`, `ACWW_FORCE_CHAN`,
`ACWW_FORCE_FIELD`, the new-game probe) are not carried and would re-fire on a load with the
same variable set [S: `docs/kb/hybrid/savestate.md` sections 5 and 3].

## Recipe

Both variables take an **absolute** path: `run_direct.py` launches the exe with cwd
`port/build`, so a repo-relative path resolves against the wrong directory and the save fails
late, after the whole run [S: `docs/kb/hybrid/savestate.md` section 7]. These are DIAGNOSTIC
runs, not frontier claims (B38).

OFF control, saved at 6,000 (`off-recipe.md`'s environment):

    python -B scratchpad/cycle40/run_direct.py st-off-save ACWW_INTERP=1 \
      ACWW_TOUCH_ENABLE=0 ACWW_STOP_FRAME=9000 ACWW_SHOT_AFTER=6000 ACWW_SHOT_EVERY=300 \
      ACWW_STATE_SAVE=6000:C:/Users/moomin/Desktop/acww/scratchpad/state/off6000.st

    python -B scratchpad/cycle40/run_direct.py st-off-load ACWW_INTERP=1 \
      ACWW_TOUCH_ENABLE=0 ACWW_STOP_FRAME=9000 ACWW_SHOT_AFTER=6000 ACWW_SHOT_EVERY=300 \
      ACWW_STATE_LOAD=C:/Users/moomin/Desktop/acww/scratchpad/state/off6000.st

Town recipe, saved at 24,000 -- the same environment as `two-tap-town-recipe.md` with
`ACWW_TOUCH2_AT=24700`, `ACWW_STOP_FRAME=27000`, `ACWW_SHOT_AFTER=24000`,
`ACWW_SHOT_EVERY=300`, and `ACWW_STATE_SAVE=24000:.../town24000.st` then
`ACWW_STATE_LOAD=.../town24000.st`.

Compare each pair with

    python port/tools/oracle/compare.py \
      scratchpad/cycle40/runs/st-off-save scratchpad/cycle40/runs/st-off-load

## Expected observations

Every frame from the one after the save to the endpoint must read `exact-rgb yes`. A frame
that does not means a piece of host state is missing from the blob registry, and the fix is to
find it -- **not** to read the `ncc` column instead [S: `docs/kb/hybrid/savestate.md` section 7].

| pair | frames | result | cost |
|---|---|---|---|
| `st-off-save` / `st-off-load` | 6,000..9,000 every 300 | **11/11 exact-rgb** | 309 s -> 110 s [E: their `receipt.json`] |
| `st-town-save` / `st-town-load` | 24,000..27,000 every 300 | **11/11 exact-rgb**, across the 24,700 contact and the ride it starts | 756 s -> 65 s [E: their `receipt.json`] |

The save line names the frame it actually landed on:
`acww state: saved frame 6000 -- 113 blobs, 5 threads`, and the load line says where it
resumed: `resuming pc 0x01ffa4fc` [E: the two `*-run.log` files;
`docs/log/cycle40-keyboard-gate-probe.md` SAVE41].

Earlier receipts from the worktree the feature was built in, copied out before that worktree
was removed: the frontier intact **31/31 exact** with neither variable set, OFF 11/11, and the
town save at 24,000 -> 27,000 11/11 exact
[E: `scratchpad/state-agent/state/RECEIPTS.md`].

## What would falsify it -- and what it already caught

The exactness standard found two real defects that `ncc` would have passed
[S: `docs/kb/hybrid/savestate.md` section 6]:

- the first pair was `exact-rgb no` on every frame at `diff% 49.9` with `ncc-top 1.0000` --
  engine B's whole screen black, because palette RAM and OAM are 2 KB, half of a 4 KB page,
  and the page count `size / PAGE` was 0, so neither region was ever written;
- the second was a 0.11% difference from the first scripted A press onward: snapshots taken at
  the same frame from both runs differed in **141 bytes of 52 MB** with all regions, all blobs
  and all register files otherwise identical -- which is only possible if a *host* resource is
  missing, and it was `acww_romfs_mount()`.

So the falsifier is any non-`exact-rgb` frame after the save, and the method for chasing one is
to diff two snapshots taken at the same frame and read off the addresses.

## Open

- [H] A snapshot has never been taken from a **paced live** run with a person at the keyboard.
  The host input state is registered, but no live run has been saved and reloaded. Settled by
  doing one [S: `docs/kb/hybrid/savestate.md` section 8].
- [H] What makes a frame refusable. The refusals name one slot, which suggests a thread that
  spends most of its life two interpreter frames deep rather than a property of the frame;
  nothing has measured which thread or why. Settled by printing the refused slot's chain
  [S: same].
- [H] A load combined with the oracle recorders. Both `oracle.c` and `oracle_events.c` enforce
  strict frame monotonicity and would abort their traces across a load; `run_on2.py` already
  unsets them, and nothing has tried it [S: `docs/kb/hybrid/savestate.md` section 5].

## How a wiki reader uses this

To ask a question about frame 26,000 -- a scene, a menu, a colour, a register:

1. Run the town recipe once with `ACWW_STATE_SAVE=24000:<absolute>.st`. If the frame is
   refused, pick another; nearby frames are cheap to try from an existing snapshot rather than
   by replaying [S: `scratchpad/state-agent/state/probe_frames.py`].
2. Run every variant of the question with `ACWW_STATE_LOAD=<that file>` and the **same**
   `ACWW_*` environment, changing only the instrument you are adding.
3. Keep the artifact. A relink invalidates the snapshot by design, so a session that is also
   changing the port must re-save after each link.

`python port/tools/test_savestate.py` checks the header, the two refusals and the blob registry
without running the game, in under a second [S: `docs/kb/hybrid/savestate.md` section 7].

## Related

- `../engine/interpreter-path.md` -- the runtime a snapshot is taken of
- `two-tap-town-recipe.md`, `off-recipe.md` -- the two recipes the receipts are taken under
- `touch-latency.md` -- the kind of late-frame question this instrument is for
- `../../docs/kb/hybrid/savestate.md` -- the implementation-side page
