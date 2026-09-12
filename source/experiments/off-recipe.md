# The OFF recipe

**Status: run, many times.** This is the control every other measurement is read against.

## Purpose

Establish that a change to the port did **not** move anything, by running the game to frame
9,000 with the stylus disabled and comparing all 31 screenshots against a retained reference by
SHA-256. 31 of 31 equal is the pass [H: log/source account: `docs/kb/hybrid/recipes.md` section 2; receipt provenance unresolved].

**The name is a trap and B1 is why.** "OFF" names `ACWW_TOUCH` being off. It is otherwise the
**keyed START** recipe, with `ACWW_KEYS=9` (A and START) pulsing from frame 300
[O: `port/tools/oracle/README.md`, "THE RECIPE NAMED OFF IS NOT AN UNKEYED RUN"]. A genuinely
blank movie was tried once on the oracle side: with no input the original never leaves the
title screen while the port is deep in the taxi intro, every frame scored a normalised
cross-correlation around 0.10, and the resulting table of 31 mismatches said nothing about the
port at all [O: same].

## Recipe

Through the iteration script, which relinks first:

    sh scratchpad/cycle40/iterate.sh <name> [KEY=VAL ...]

which runs, in order, a link through the execution-channel controller (about 3 minutes), then:

    python -B scratchpad/cycle40/run_direct.py off-<name> \
      ACWW_INTERP=1 ACWW_TOUCH_ENABLE=0 \
      ACWW_STOP_FRAME=9000 ACWW_SHOT_AFTER=4500

then a SHA-256 comparison of all 31 BMPs against
`scratchpad/cycle39/execution39-touch39-005/off`, then a grep of the log for the BOOT line, the
stop line, faults, `unimplemented` and the STOP line
[E: `scratchpad/cycle40/iterate.sh`; `docs/kb/hybrid/recipes.md` section 2].

The pad phases come from the script's own base and are the custom START recipe:
`ACWW_KEYS=9 ACWW_KEYS_AT=300 ACWW_KEYS_FOR=10 ACWW_KEYS_EVERY=30`
[O: `port/tools/oracle/README.md`; cycle39 log].

The oracle arm of the same recipe:

    python port/tools/oracle/oracle.py --frames 4500,4650,...,9000 --out scratchpad/oracle/off
    python port/tools/oracle/compare.py scratchpad/oracle/off scratchpad/cycle40/runs/off-<name>

[H: log/source account: `docs/kb/hybrid/recipes.md` section 6; receipt provenance unresolved].

## Expected observations

| what | expected |
|---|---|
| frames | 9,000, child exit 100, launcher 0 |
| screenshots | 31 BMPs from frame 4,500 |
| pass | `equal 31 differ 0` |
| log | one `acww touch: up` line and no more -- the on-change instrument starts at `last = -1`, so every run prints exactly one initial "up"; an ON run has three [H: log/source account: `docs/kb/port/input-save-audio.md`, TOUCH39; receipt provenance unresolved] |
| turnaround | about 90 seconds a turn once the link is warm [H: log/source account: `docs/kb/hybrid/recipes.md` section 2; receipt provenance unresolved] |

## The runs that produced them

The reference is `scratchpad/cycle39/execution39-touch39-005/off`
[H: log/source account: `docs/kb/hybrid/recipes.md` section 2; receipt provenance unresolved]. The whole deny-list bisection of REG40b and REG40c
was built on this loop [H: log/source account: `docs/log/cycle40-keyboard-gate-probe.md` REG40b, REG40c; receipt provenance unresolved]. The oracle
side is `scratchpad/oracle/off`, with `compare-off.json` and `diff-off/` beside it
[O: `scratchpad/oracle/off`].

## What would falsify it

- Any BMP differing without a deliberate change to the port. Read it as a defect in the change,
  not as noise: the reference is a byte comparison, not a similarity score.
- A run that finishes without the `acww touch: up` line, which would mean the instrument itself
  went quiet -- indistinguishable from the thing it measures going quiet
  [H: host-source account from `port/platform/hostinput.c`'s announcement rationale; verify with a retained scripted run and frame using this page's recipe].
- Running an ON arm before this control (M15). The 31-frame comparison is what makes an ON
  difference mean anything.

## Related

- `two-tap-town-recipe.md` -- the ON recipe this controls for.
- `../systems/input-and-touch.md`
