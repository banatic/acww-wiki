# The interpreter path, and how a native body earns the hot path

**Summary.** The PC port has two ways to execute the game. The native path runs the port's own
C bodies; the interpreter path (`ACWW_INTERP=1`) executes the ROM's own ARM and Thumb code in
process, and calls a host body only where one is registered. The interpreter path is the
default direction of the project, because "the ROM's bytes" is a correct implementation of
every function nobody has written yet. That makes the interesting question the reverse of the
old one: not *can we write this function*, but *may this native body replace the ROM's bytes
without changing what the game does*. The answer is a per-function differential check on real
recorded calls, and this page says what a pass from it is worth.

## What happens

`ACWW_INTERP=1` is read once and cached, and does two things: the port skips its native
bring-up, its native static initialisers and its native sound boot, and the interpreter runs
the ROM's own `Entry` order instead [S: `port/interp/interp_boot.c`; `port/platform/win32.c`;
see `boot-and-entry.md`]. Everything else -- the loader, the renderer, the shims, the
instruments -- is the same binary.

Which functions are host bodies and which are ROM bytes is decided at build time by
`port/tools/interp_registry.py`, which generates a registry of host bodies and refuses to
register the basenames in its `DENY_FILES` list -- 50 shim files as of TOUCH41, plus `DENY_FUNCS =
{func_020b1b84}` [S: `port/tools/interp_registry.py`; `wiki/glossary.md`, "deny list"]. Each
deny entry carries the run that forced it in a comment beside it, so the list is the record of
which subsystems diverge when half of one is promoted
[S: `docs/kb/hybrid/stall-playbook.md`, "The deny list is the record of this table"]. The touch
input file is the clearest case: denying `port/shim/input/touch.c` (registry 89 -> 88) is what
made the ROM's own per-frame stylus publish run, which is what reproduced the original's
latency [S: `docs/log/cycle40-keyboard-gate-probe.md` TOUCH41; see
`../experiments/touch-latency.md`].

### The promotion check (hybrid plan H5)

A native body earns the hot path by a differential check on **real** calls, not on invented
ones. The run records the calls the game actually makes, and each is then replayed twice from
the same pre-call memory -- once through the interpreter (the ROM's bytes) and once through
the native body -- and the return value and the write set are compared
[S: `docs/kb/hybrid/promotion.md`]. Three pieces do it: `port/interp/interp_record.c` (the
recorder, armed by `ACWW_INTERP_RECORD`, inert otherwise -- one global load and a not-taken
branch), `port/tools/promote.py` with its no-CRT fixture, and `port/tools/promote_record.py`,
the tracked runner that performs the recording run [S: same].

Each record carries r0-r3 plus the four AAPCS stack words, the **pre-call page images**
snapshotted on first touch and before any store (this is what makes the replay exact rather
than approximate), every load and store in a bounded ring, and on return r0, r1 and the
interpreted step count. A nested `acww_interp_call` -- an interrupt handler, a thread procedure
-- runs at a deeper depth and its memory is excluded, because it is not this call's write set
[S: same]. Three things the recorder refuses to hide, each a flag: a registered host body ran
inside the call, an I/O-page address was touched, a bound overflowed. `promote.py` will not
compare such a call [S: same].

The comparison is a **final-state diff, not a store log** -- two correct bodies may store in a
different order or overwrite a scratch value, and only what the caller can observe afterwards
is the contract. The dead frame below the entry stack pointer is excluded on purpose (the
interpreted replay pushes onto the recorded NDS stack, the native body onto the host's); the
four stack argument words are compared. And before the native body is judged at all, the
interpreted replay must reproduce the recording's own return -- if it does not, the result is
`REPLAY-MISMATCH`, a statement about the harness's inputs and never about the body
[S: same]. Exit codes: 0 all agreed, 1 a disagreement (a finding), 2 the harness declined to
judge, 3 agreed but some calls were refused.

### What "AGREE" does not prove

This is the part to read before promoting anything [S: `docs/kb/hybrid/promotion.md`
section 3]:

- **Coverage is the recorded calls and nothing else.** Eight calls of a function the run makes
  three million times is eight calls. That is why the summary prints `calls-that-wrote=` and
  `distinct-returns=`: an agreement over calls that all returned the same value and wrote
  nothing is not evidence (M1).
- **Callbacks are not followed.** If the ROM function calls through a function pointer, the
  interpreted replay runs the ROM's callee while the native body runs whatever the link gave
  it. The fixture links exactly one native body, so a body with native callees fails to link
  -- loudly, rather than silently differing.
- **Timing, interrupts and ordering are not modelled.** The replay is a single call in a quiet
  process. A body that is correct in isolation and wrong because it takes longer or is
  re-entered is invisible here. (The TOUCH41 interpreted-callback anomaly is exactly that
  class of defect, and no promotion check would have seen it --
  `../experiments/touch-latency.md`, Open.)
- **State outside the touched pages is invisible.** Only pages the recorded call touched are
  mapped and diffed; a native body that writes somewhere the ROM never touched crashes the
  fixture rather than producing a clean disagreement.
- **A promotion is not a registration.** Agreeing says nothing about whether the function
  *should* be host code. That is what the deny list is for.

### The three results, and the calibration that matters more

Recorded on the custom START recipe, `ACWW_INTERP=1`, `ACWW_STOP_FRAME=3000`, 8 calls each,
about 80 seconds a run [S: `docs/kb/hybrid/promotion.md` section 4]:

| function | where | result |
|---|---|---|
| `FX_MulFunc` `0x01ffcb0c` | itcm, ARM, pure | **AGREE 8/8**, 7 steps per call, 6 distinct returns, 0 writes |
| `func_0204f800` `0x0204f800` | main, Thumb, two stores through out-params | **AGREE 8/8**, 12 steps, all 8 calls wrote |
| `MTX_Concat43` `0x01ffb94c` | itcm, ARM, 48-byte write | **AGREE 8/8**, 136 steps, 32 logged stores a call -- but only **2 of 8** produced an observable byte change; the other six wrote values that were already there |
| `_s32_div_f` `0x021367a8` | autoload_2, third hottest pc in the run | recorded fine, **REFUSED (exit 2): no native body.** Hand-written CodeWarrior assembly; nothing to promote |
| `func_02050c58` | main | **never called** in 3,000 frames of the recipe -- nothing to record |

The calibration is the result that changes how the table should be read. Two deliberately
wrong bodies were run against the `func_0204f800` trace [S: `docs/kb/hybrid/promotion.md`
section 5]:

1. the two out-parameters **swapped** -- **REPORTED AGREE**, because every one of the eight
   recorded calls happened to have `x == y` and `offset_x == offset_y`. The coverage caveat
   arriving as a measurement rather than as a warning;
2. the second store's value written with its low two bytes swapped -- **REPORTED DISAGREE on
   8/8, exit 1**, naming the differing store and its address.

So an AGREE is worth exactly what its control is worth, and the control's error must be one the
recorded arguments cannot hide -- change a stored **value**, not just which pointer it goes to.

## Where it lives

| function or symbol | module | role | grade/citation |
|---|---|---|---|
| `acww_interp_boot` | port | installs the hooks, then runs the ROM's `Entry` order | [S: `port/interp/interp_boot.c`; `boot-and-entry.md`] |
| `run_loop` | port | the instruction loop; also where a savestate is taken, at an outermost interpreted frame | [S: `port/interp/interp_cpu.c`; `docs/kb/hybrid/savestate.md` section 2] |
| `acww_interp_call`, `acww_interp_irq_run` | port | the call boundary and the IRQ-context entry | [S: `port/interp/interp_cpu.c`] |
| `interp_registry.py` `DENY_FILES` | build | the 50 shim basenames that stay ROM bytes | [S: `port/tools/interp_registry.py`] |
| `interp_record.c` | port | the call recorder; inert unless `ACWW_INTERP_RECORD` is set | [S: `docs/kb/hybrid/promotion.md`] |
| `promote.py`, `promote_main.c` | tools | the replay and the verdict; no CRT, ROM images mapped at their NDS addresses | [S: same] |
| `promote_record.py` | tools | the tracked recording runner, output under `scratchpad/promote/<name>/` | [S: same] |

## Data it reads and writes

| variable or file | meaning | who writes | who reads |
|---|---|---|---|
| `ACWW_INTERP` | 1 selects the interpreter path; read once and cached at boot | the operator | `acww_interp_boot` [S: `port/interp/interp_boot.c`] |
| `ACWW_INTERP_RECORD=<hex addr>[,<count>]` | arm the call recorder on one function; count defaults to 8 | the operator (or `promote_record.py`) | `acww_interp_boot` [S: `docs/kb/hybrid/promotion.md` section 1] |
| `ACWW_INTERP_RECORD_OUT=<path>` | the binary trace; required when the recorder is armed | the same | the recorder [S: same] |
| `scratchpad/promote/<name>/<name>.rec` | one trace: per call, the eight boundary words, the pre-call 4 KB page images, the bounded load/store ring, and the return | `interp_record.c` | `promote.py` [S: same] |
| `scratchpad/promote/<fn>/receipt.json` | the verdict: trace, source, interpreter and fixture hashes, the return mask, and every call's arguments, steps and returns | `promote.py` | the reader [E: `scratchpad/promote/FX_MulFunc/receipt.json`] |
| `port/tools/interp_registry.py` -> `interp_registry.c` | the generated host-body registry; its entry count is part of a savestate's link identity | the build | the interpreter, and `state.c`'s header check [S: `docs/kb/hybrid/savestate.md` section 5] |

## How to check it

    python port/tools/promote_record.py fxmul 0x01ffcb0c 8
    python port/tools/promote.py --trace scratchpad/promote/fxmul/fxmul.rec --name FX_MulFunc

The runner names the recording directory (`scratchpad/promote/fxmul/`, holding the trace, the
run log and a receipt with the exe hash and the whole environment); `promote.py` writes the
verdict receipt under the FUNCTION's name (`scratchpad/promote/FX_MulFunc/receipt.json`, which
carries the trace, source, interpreter and fixture hashes, the return mask, and every recorded
call's arguments, steps and returns).

Then, every time, copy the body, break it in a way the recorded arguments cannot hide, and
rerun with `--source <the broken copy>`; it must report DISAGREE and name the store. Read
`calls-that-wrote=` and `distinct-returns=` before reading the verdict
[S: `docs/kb/hybrid/promotion.md` section 6].

A caveat on the receipts. The worktree the original three checks ran in was removed after the
merge and took its ignored `scratchpad/promote/` with it -- the runner the brief named and the
receipts both. `port/tools/promote_record.py` is the tracked replacement and re-creates them;
re-run on `FX_MulFunc` on the merged tree it gives 8 calls, **AGREE 8/8**, distinct-returns 6
[E: `scratchpad/promote/FX_MulFunc/receipt.json` -- `"verdict": "AGREE"`, exit 0 -- and the
recording run `scratchpad/promote/fxmul/receipt.json`, exit 100 at 3,000 frames in 76 s;
S: `docs/log/cycle40-keyboard-gate-probe.md`, "H5 follow-up"]. The receipts for
`func_0204f800`, `MTX_Concat43` and `_s32_div_f` do **not** exist on this tree; their numbers
above are the hand-back's and are grade S against `docs/kb/hybrid/promotion.md` section 4
rather than grade E against a run directory. Re-running them is one command each.

## Hypotheses

- [H] Whether any of the three agreeing bodies should actually be registered. An AGREE is
  evidence about behaviour, not about architecture; nothing has measured what promoting
  `MTX_Concat43` does to a full run. Settled by registering one and comparing a town run
  frame-for-frame against the same run without it.
- [H] Whether `MTX_Concat43`'s agreement means anything at all, given that six of its eight
  calls wrote values that were already there. Settled by recording it from a call site where
  the matrices differ -- the summary line's `calls-that-wrote=` is the number to move.
- [H] A rule for `port/interp/interp_cpu.c` and `interp_bios.c` that is currently a convention
  rather than a check: **no platform symbols, hooks only.** The first read-watchpoint version
  put `acww_frame_count` and `acww_out` references into `interp_cpu.c`, which `promote.py`
  compiles into a fixture with no platform, and the fixture failed to link
  (`undefined symbol _acww_frame_count`); the watch now reports through a hook installed by
  `interp_boot.c` [S: `docs/log/cycle40-keyboard-gate-probe.md`, "H5 follow-up"]. Settled by a
  fixture-link check in a gate rather than by remembering.

## Related

- `boot-and-entry.md` -- how the interpreter path boots, and what a frame is on it
- `../experiments/savestate-resume.md` -- snapshotting a run of this path
- `../experiments/touch-latency.md` -- the deny list used as an instrument
- `../../docs/kb/hybrid/promotion.md`, `../../docs/HYBRID-PLAN.md` phase H5
