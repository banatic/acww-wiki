# RNG determinism

**Status: designed, not yet run.**

## Purpose

The port pins both of the ROM's entropy sources: the tick advances exactly 8,728 counts per
frame from zero [E: `port/platform/tick.c`] and the RTC is a fixed instant
[E: `port/shim/os/rtcclock.c`]. So a port run *should* be bit-identical to itself. That has
never been checked as its own claim -- it has only ever been assumed by every comparison built
on top of it.

The second half is the interesting one. If moving the clock by one second changes nothing, then
nothing on the path to the town hall consumes a clock-seeded draw, and the determinism is
trivially true. If it changes something, we have found a consumer -- and no gameplay-side
generator has been located in `src/matched` at all [S: absence; see `../systems/rng.md`].

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

## Expected observations

| comparison | prediction | what it would mean if wrong |
|---|---|---|
| A vs B | 29 of 29 equal | the port is not deterministic; something reads the host -- the address-space layout, a wall clock, or an uninitialised buffer, which is exactly the class of defect `rtcclock.c` was written to remove |
| A vs C | 29 of 29 equal | nothing on this path consumes a second-resolution clock draw; the pinned clock is doing no work beyond the lighting |
| A vs C | some frames differ | a consumer exists, and the first differing frame names roughly where |

A useful third comparison, cheap because the arms are already there: normalise the two logs from
A and B and diff them. A clean run's only expected differences are the host address-space
layout block and the release line -- that was the observed shape of a matched pair on the native
path [E: `docs/kb/port/input-save-audio.md`, TOUCH39, the `FOR=10` versus `FOR=90` diff].

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
