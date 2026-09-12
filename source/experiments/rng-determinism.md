# RNG determinism

**Status:** the original A/B/C shot experiment remains a proposal [H: no A/B/C receipt is supplied here].
+The later draw-position arms below were measured in ORACLE47..49 [E: `scratchpad/oracle47/RECEIPTS.md`, `scratchpad/oracle49/RECEIPTS.md`; log: `docs/log/cycle41-gameplay.md` O47-4, O49-1..5].

## Purpose

Separate the boot seed from the stream position at generation: the clock seed folds
`minute | day<<8 | hour<<16 | second<<24`, so changing one second changes a seed byte,
while changing only the year or month does not change this fold
[S: `src/matched/func_0209dbbc.c`; source account: `src/matched/func_0209dbbc.c`; log: `docs/log/cycle41-gameplay.md` O46-1, O46-4].
That source fact alone does not prove whole-frame equality or that every changed seed gives
a different town [H: the A/B/C experiment below is not a retained result].
ORACLE46 measured the same seed `0x000a0f00` with and without the original's freeze arm;
ORACLE47 located the arm's extra draw consumption after frame 10,000, reaching 14 extra draws
by confirmation [E: `scratchpad/oracle46/RECEIPTS.md`, `scratchpad/oracle47/RECEIPTS.md`;
log: `docs/log/cycle41-gameplay.md` O46-4, O47-3].

## Measured arms: id, layout and roster are separate checks

| arm / comparison | measured result | grade and source section |
|---|---|---|
| ORACLE47 port confirmation timing only | `24700` gives `0xc66e`; `24907` and `24908` give `0x8365`; `24909` gives `0xe767` on that build | [E: `scratchpad/oracle47/RECEIPTS.md`; log: `docs/log/cycle41-gameplay.md` O47-4] |
| ORACLE49 boot control, no tap | town `0xd391`; 4,617 compared words, 0 differ | [E: `scratchpad/oracle49/RECEIPTS.md`; log: `docs/log/cycle41-gameplay.md` O49-3] |
| ORACLE49 forward: port `ACWW_TOUCH2_AT=24908`, `ACWW_RTC_FREEZE_UNTIL=48000`; original `--touch2-at 24700`, no arm | town `0x8365`; 36 acre bytes and all seventeen building cells identical; 2,057 map words with 1 loose-item difference at frame 48,000 | [E: `scratchpad/oracle49/RECEIPTS.md`; log: `docs/log/cycle41-gameplay.md` O49-4] |
| ORACLE49 inverse: original `24315` with freeze to 48000; port `24700` | id draw #2,667 on both; original enters layout burst at 3,780, port at 3,782 | [E: `scratchpad/oracle49/RECEIPTS.md`; log: `docs/log/cycle41-gameplay.md` O49-2] |

The new-game path generates twice: the port's boot town is at frame 758, then the map is
reset before the real map, item layer and roster are written together at frame 36,135,
11,346 frames after the id draw at frame 24,789 [E: `scratchpad/oracle49/RECEIPTS.md`;
log: `docs/log/cycle41-gameplay.md` O49-1].
The control port enters the real burst at index 3,782, with first layout draw #3,783 and
232 draws in one frame [E: `scratchpad/oracle49/RECEIPTS.md`; log:
`docs/log/cycle41-gameplay.md` O49-2].
ORACLE49 re-calibrated the forward tap window to 24,907..24,909 on its build, so the older
24,907..24,908 interval is historical rather than a portable constant
[E: `scratchpad/oracle49/RECEIPTS.md`; log: `docs/log/cycle41-gameplay.md` O49-4].

## Recipe

Three arms of the town recipe (`two-tap-town-recipe.md`), differing only as noted, all on one
build.

**Arm A -- the baseline.** `ACWW_RTC_TIME=100000`, shots every 1,500 frames from 6,000.

**Arm B -- the repeat.** Byte-for-byte the same command line, a different output directory.

**Arm C -- one second later.** `ACWW_RTC_TIME=100001`.

    for N in A B; do
      python -B scratchpad/cycle40/run_town.py rngdet-$N \
        ACWW_INTERP=1 ACWW_RTC_DATE=20050615 ACWW_RTC_TIME=100000 \
        ACWW_TOUCH_AT=6900 ACWW_TOUCH_EVERY=60 ACWW_TOUCH_REPEAT=2 \
        ACWW_TOUCH2_X=221 ACWW_TOUCH2_Y=181 ACWW_TOUCH2_AT=24600 ACWW_TOUCH2_FOR=10 \
        ACWW_TOUCH2_EVERY=60 ACWW_TOUCH2_REPEAT=2 \
        ACWW_STOP_FRAME=48000 ACWW_SHOT_AFTER=6000 ACWW_SHOT_EVERY=1500 ACWW_PAD_SAMPLE=0
    done

then arm C with `ACWW_RTC_TIME=100001`, and a SHA-256 comparison of the three shot sets, the
same comparison `iterate.sh` already performs for the OFF recipe
[E: `scratchpad/cycle40/iterate.sh`].

## Original A/B/C predictions, not measured outcomes

| comparison | prediction | what it would mean if wrong |
|---|---|---|
| A vs B | 29 of 29 equal [H: proposed repeat test, not an ORACLE47..49 result] | investigate the differing inputs or nondeterminism before attributing a cause [H] |
| A vs C | frames may differ from the town onward [H: proposed test] | the second changes the seed's top byte, but frame equality alone does not falsify that fold [S: `src/matched/func_0209dbbc.c`; source account: `src/matched/func_0209dbbc.c`; log: `docs/log/cycle41-gameplay.md` O46-1] |
| a fourth arm, `ACWW_RTC_DATE=20060615` (year only) | same boot seed; whole-frame equality is unmeasured [H: proposed test] | the year is absent from this fold; other year-dependent behaviour is not excluded [S: `src/matched/func_0209dbbc.c`; source account: `src/matched/func_0209dbbc.c`; log: `docs/log/cycle41-gameplay.md` O46-1] |

A useful third comparison, cheap because the arms are already there: normalise the two logs from
A and B and diff them. A clean run's only expected differences are the host address-space
layout block and the release line -- that was the observed shape of a matched pair on the native
path [H: log/source account: `docs/kb/port/input-save-audio.md`, TOUCH39, the `FOR=10` versus `FOR=90` diff; receipt provenance unresolved].

## What would falsify it

- Any A-versus-B difference. Before concluding non-determinism, check the two receipts' `exe_sha256`
  are equal -- the arms must be one build [E: receipts record it,
  `scratchpad/cycle40/runs/tap-D56/receipt.json`].
- A difference that appears only after frame 40,500, inside the town hall. The scripted A pulses
  talk to Pelly repeatedly there and the dialogue selection is the likeliest consumer of a
  draw [E: `scratchpad/cycle40/runs/tap-D59`, LONG41]; that would be a positive result, not a
  failure of the experiment.
- Reading equality as proof that the game has no RNG. It proves only that this path, at this
  clock resolution, does not branch on one.

## Related

- `../systems/rng.md`, `../systems/time-and-rtc.md`
- `two-tap-town-recipe.md`
