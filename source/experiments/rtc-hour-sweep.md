# RTC hour sweep

**Status: designed, not yet run.**

## Purpose

Every measurement in this project so far pins the clock to 2005-06-15 10:00:00, so the game's
day/night lighting has never been exercised at more than one point
[E: `port/shim/os/rtcclock.c`; `scratchpad/cycle40/runs/tap-D56`]. The blend weight the
lighting interpolates from is the minute byte at `0x021dc758` scaled by 4096/60, and reading it
off host stack garbage once put a 20-26% pixel noise floor under every screenshot comparison in
this port [H: source/log account from `port/shim/os/rtcclock.c`; verify with a retained run using this page's recipe]. This experiment asks two things at once: does the hour
visibly change the scene, and do the port and the original change the same way.

It also settles a smaller question. `ACWW_RTC_TIME=000000` used to mean "use the default",
because the port's older parser folded unset, unparsable and zero into one answer -- so a
midnight probe came back byte-identical to the 10:00 one, which is a measurement that looks
like an answer [H: host-source account from `port/shim/os/rtcclock.c`; verify with a retained scripted run and frame using this page's recipe]. The current parser distinguishes them; this run
is the check that it does.

## Recipe

Four arms, one per hour, each the town recipe with only `ACWW_RTC_TIME` changed. Run the 10:00
arm first: it must reproduce `scratchpad/cycle40/runs/tap-D56` frame for frame, or the sweep is
measuring the build rather than the hour (M15).

    for T in 100000 000000 060000 200000; do
      python -B scratchpad/cycle40/run_town.py rtc-$T \
        ACWW_RTC_DATE=20050615 ACWW_RTC_TIME=$T \
        ACWW_INTERP=1 \
        ACWW_TOUCH_AT=6900 ACWW_TOUCH_EVERY=60 ACWW_TOUCH_REPEAT=2 \
        ACWW_TOUCH2_X=221 ACWW_TOUCH2_Y=181 ACWW_TOUCH2_AT=24600 ACWW_TOUCH2_FOR=10 \
        ACWW_TOUCH2_EVERY=60 ACWW_TOUCH2_REPEAT=2 \
        ACWW_STOP_FRAME=39000 ACWW_SHOT_AFTER=36000 ACWW_SHOT_EVERY=750 ACWW_PAD_SAMPLE=0
    done

The stop is 39,000 rather than 48,000 because the town exterior at 37,500 is the frame the
lighting is worth looking at; the town hall interior after 40,500 is indoors
[E: `docs/log/cycle40-keyboard-gate-probe.md` TOWN40].

Oracle arms, one per hour -- the RTC is pinned in the generated movie's `rtcStart` line, so it
is a flag rather than an environment variable [O: `port/tools/oracle/README.md`, "How the RTC
and the input recipe are enforced"]:

    python port/tools/oracle/oracle.py --frames 36000,36750,37500,38250,39000 \
      --rtc-start 2005-06-15T00:00:00Z \
      --touch-x 221 --touch-y 181 --touch-at 6900 --touch-for 10 \
      --touch-every 60 --touch-repeat 2 \
      --touch2-x 221 --touch2-y 181 --touch2-at 24600 --touch2-for 10 \
      --touch2-every 60 --touch2-repeat 2 \
      --out scratchpad/oracle/rtc-000000

    python port/tools/oracle/compare.py scratchpad/oracle/rtc-000000 \
      scratchpad/cycle40/runs/rtc-000000 --json scratchpad/oracle/rtc-000000.json

Check `oracle.py --help` for the exact `rtcStart` flag name before running; the README documents
the field, not the flag.

**A caveat that ORACLE42 removed.** Under the 24,600 recipe the original did not reach the town
at all -- it sat on the town-name keyboard from 25,500 to 48,000, so every oracle arm would have
scored the *keyboard* screen [O: `docs/log/cycle40-keyboard-gate-probe.md` ORACLE41]. That is
settled: the tap at 24,600 landed on a KEYS3 A-press frame and the original's stylus sample
arrives one to two frames later, so with `ACWW_TOUCH2_AT=24700` both sides confirm and agree
[S: `docs/log/cycle40-keyboard-gate-probe.md` ORACLE42; E: `tap-D62`;
O: `scratchpad/oracle/tap-24700`]. **Use 24,700 in both the port and the oracle arms above**;
the commands as written still say 24,600 and would reproduce the old caveat.

## Expected observations

| arm | expectation |
|---|---|
| `ACWW_RTC_TIME=100000` | byte-identical to `tap-D56` at 36,000 and 37,500 |
| `000000` | midnight: the boot line reads `hour=0 min=0`, and the town exterior at 37,500 is visibly darker |
| `060000` | dawn |
| `200000` | night |

The boot line to check in every log is `acww rtc: fixed clock year+2000=5 month=6 day=f
week=3 hour=... min=0 sec=0` -- the values are printed in hex
[H: host-source account from `port/shim/os/rtcclock.c`; verify with a retained scripted run and frame using this page's recipe]. Week 3 is Wednesday, computed, never taken from the
environment.

Falsifiable prediction: if all four arms produce byte-identical images at 37,500, either the
override is not being applied (check the boot line before anything else) or the scene at that
frame does not use the day/night blend.

## What would falsify the hypothesis it tests

- Identical images across four hours with four distinct boot lines: the blend weight reaches the
  renderer but the town exterior does not use it.
- A rejected-override line, `acww rtc: ACWW_RTC_TIME rejected, keeping the default` -- the value
  is out of range and the arm is not the arm you think it is.
- The 10:00 arm differing from `tap-D56`: the build moved, and no other arm means anything until
  that is explained (M1).

## Related

- `../systems/time-and-rtc.md`
- `two-tap-town-recipe.md`, `off-recipe.md`
