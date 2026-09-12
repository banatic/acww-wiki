# Run stability: what an exit code means, and what a 48,000-frame run costs

**Status: run, 2026-09-10 (STAB42, `0bc59cc0`).** Two other units had seen the 48,000-frame town
recipe end early with **exit 1**, a log cut mid-line, and no fault marker -- read at the time as
a regression from the sound driver. It was not the port. `acww.exe` **cannot exit 1**: nothing in
its exit-code table produces that value, and every value it does produce prints a report first.
An exit status of 1 means something OUTSIDE the process called `TerminateProcess`. Six
48,000-frame arms on the same build all reached exit 100.

## Purpose

Separate three things a single "the run ended early" observation confuses: a port crash, a port
hang, and an external kill. Until they are separated, every long run's evidence is suspect and
every unit that takes one has to argue about it.

## Recipe

**Step 1, the calibration, and the whole conclusion rests on it (M1).** Measure what each way of
killing a Windows process actually leaves behind, rather than assuming:

    python scratchpad/stab42/killcode.py        # writes killcode.json

| how the process died | exit code |
|---|---|
| `taskkill /F /PID` -- what a session's cleanup does | **1** |
| Python `Popen.kill()` / `terminate()` -- what a runner does on timeout | **1** |
| PowerShell `Stop-Process -Force` | `0xffffffff` |
| a fail-fast / heap corruption | `0xc0000374` / `0xc0000409` |
| a plain `WM_CLOSE` (i.e. `taskkill` WITHOUT `/F`) | **0**, with the save flushed |

[E: `scratchpad/stab42/killcode.json`.] Against that, the port's own table: faults exit 4, the
last-chance filter 8, a stack overflow 4, a normal stop 100 -- and 1 is deliberately not among
them, `acww_exit` being the only wrapper [H: host/prose inference from `port/platform/win32.c`; `port/tools/measure.py`'s
`acww_exit` table; verify against the ROM function or symbol table and this page's recipe]. **The log is truncated rather than short** because `acww_out` is an
unbuffered `WriteFile` per token: the file is complete to the instant of death and no farther.

**Step 2, the arms.** Six 48,000-frame town-recipe runs through `scratchpad/stab42/stabrun.py`,
which puts stdout STRAIGHT to a file (never a pipe), records a deadline far above any plausible
run and whether it fired, samples the child's peak working set and a whole-machine `acww.exe`
census once a second, and keeps the exit code raw AND as hex.

## Expected observations

| arm | audio | exit | seconds | peak working set |
|---|---|---|---|---|
| `A1` | `ACWW_SND` unset | **100** | 1,358 | 24.8 MB |
| `A2` | `ACWW_SND` unset | **100** | 1,285 | 24.8 MB |
| `B_snd1` | `ACWW_SND=1` (driver + sink thread) | **100** | 1,342 | 28.8 MB |
| `C_snd1_nothread` | `ACWW_SND=1 ACWW_SND_NOSINK=1` | **100** | 1,340 | 26.4 MB |
| `D1_pair` | unset, launched together with D2 | **100** | 1,315 | 25.2 MB |
| `D2_pair` | `ACWW_SND=1`, launched with D1 | **100** | 1,003 | 26.9 MB |

Six arms, six exit 100s, 36-49 fps, 600 KB logs, and **15 of 15 shots byte-identical in every
arm** -- with the sound driver off, on, on-without-its-thread, and two copies of the port running
at once, with 3 to 4 other `acww.exe` on the machine throughout. No run printed
`acww: FAULT --`, `ACCESS VIOLATION`, `acww: unimplemented:`, `acww interp: STOP` or `acww: HUNG`
[E: `scratchpad/stab42/INDEX.md`; per-arm receipts `runs/<name>/stab-receipt.json`].

**And the symptom was reproduced first-hand, by accident.** The first attempt at the contention
pair was killed at 00:30:00 by the orchestrator session restarting. What it left is the STAB42
symptom exactly: two logs stopping on an ordinary mid-run line at 34,201 and 33,601 frames, no
stop line, no fault, no receipt because the parent died too, both within one second
[E: `scratchpad/stab42/killed-pair-2026-09-10T0030.txt`].

**The discriminator**, if a session admits to a `taskkill`: without `/F` it posts `WM_CLOSE`,
which a scripted run answers through `acww_window_pump` -- `acww: window closed`, save flushed,
**exit 0**. With `/F` there is no user-mode path at all, so the log stops mid-run and the status
is 1.

**What the recipe actually costs.** On the AUDIO6-era build the town recipe takes **1,000-1,360
seconds**, against `run_town.py`'s 1,500 s timeout -- about 10% headroom uncontended, which is
not much [E: `scratchpad/stab42/INDEX.md`]. On PERF42's build the same chain's town leg cost
**522 s** [H: log/source account: `docs/log/cycle42-save.md` SAVE43; receipt provenance unresolved], so the headroom is now large; the number to
re-measure after any renderer change is this one.

## What would falsify it

- Reading exit 1 as a port failure. It is not one on this image. Re-run, and look for who ran
  `taskkill /IM acww.exe` -- which kills every worktree's exe at once. **Three separate agents
  did that on the night of 2026-09-09**, and each time it ended other sessions' runs; kill by
  PID only, and prefer a uniquely named copy of the exe (`run_sf.py` does this)
  [H: log/source account: `docs/log/cycle40-keyboard-gate-probe.md` AUDIO7, SAVEFLOW41, STAB42; receipt provenance unresolved].
- Judging a run by its frame count or its wall clock under a timeout (B12). Judge the endpoint,
  the exit code and the images.
- Reading a short log as an incomplete one. It is complete to the instant of death, which is what
  makes the last line useful.
- Trusting an arm run through a pipe. `stabrun.py` exists partly because a full pipe can stall
  the child; stdout goes straight to a file.

## Related

- `off-recipe.md`, `two-tap-town-recipe.md` -- the recipes these arms ran
- `live-play.md` -- the pacer, and why a paced window below rate is usually contention
- `../engine/graphics-pipeline.md` -- why the recipe got two and a half times cheaper
- `docs/kb/hybrid/stall-playbook.md` case 47 -- the playbook row this page is the experiment for
- `docs/rules/B-build.md` B12 and B14 -- do not judge on frame counts; record what else was
  running
