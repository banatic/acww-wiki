# Touch calibration: what the game sees when you tap

**Status: run.** The measurement below is the best-characterised difference between the port
and the original in this project.

## Purpose

A scheduled stylus contact is the port's main input instrument, and the oracle mirrors it. But
"the emulator's stylus moved" and "the game saw a touch" are different claims, and a reference
where the panel is emulated but the game never sees a contact would look identical to a good
one. This experiment asks what the *ROM's own published touch point* holds, on the original, on
the exact frames the recipe asked for.

## Recipe

Oracle side, in probe mode:

    python port/tools/oracle/oracle.py --touch-probe 1200 \
      --touch-x 221 --touch-y 181 --touch-at 1000 --touch-for 10 \
      --touch-every 60 --touch-repeat 2

Probe mode stops enforcing the touch contract and instead emits one `{"kind":"stylus"}` ledger
row per frame while the stylus is down and one per state change, and it reads the ROM's own
`TP_POINT` at `0x021fbde8` and the gate word at `0x027fffa8`
[O: `port/tools/oracle/README.md`, "...and the tap reaches the GAME"].

Port side, the same window under the town recipe's environment
(`two-tap-town-recipe.md`), reading the port's `acww touch:` lines, which print on change only
and are therefore uncapped [H: host-source account from `port/shim/input/touch.c`; verify with a retained scripted run and frame using this page's recipe].

## Expected observations

The three-field question the recipe answers, at `AT=1000 FOR=10 EVERY=60 REPEAT=2`,
`X=221 Y=181`:

| movie frame | movie stylus | `0x021fbde8` x, y, touch, validity | `0x027fffa8` |
|---|---|---|---|
| 999 | up | no row (state unchanged) | `2c00` |
| 1000..1009 | down 221,181 | **222, 182, 1, 0** | `2c00` |
| 1010 | up | 222, 182, 1, 0 -- one frame of lag | `2c00` |
| 1060..1061 | down 221,181 | 255, 255, 0, 0 -- not yet sampled | `2c00` |
| 1062.. | down 221,181 | **222, 182, 1, 0** | `2c00` |

[O: `port/tools/oracle/README.md`, 1,200-frame probe run].

Three findings, all of which matter:

1. **The contact reaches the game.** The ROM's own touch words go to `touch = 1` at the
   coordinates the recipe asked for.
2. **The coordinates come back one pixel high**, 221,181 in and 222,182 out. That is the
   digitiser round trip the port deliberately skips: the emulator converts screen pixels to raw
   ADC counts and `TP_GetCalibratedPoint` converts them back, while the port injects at the
   output of that conversion. The two producers therefore differ by up to a pixel on any
   scheduled tap, by construction [O: same; E: `port/shim/input/touch.c`].
3. **The game sees the contact one to two frames late and holds it one frame long**, because
   the ARM7's auto-sampling ring is filled a frame before the ARM9 reads it. A `FOR=10` contact
   is roughly ten frames of `touch = 1` in game RAM, shifted by about two. The port's NATIVE
   path publishes on the exact frame, which was the difference; on the interpreter path the
   port now reproduces the delay and its ordering [E: `scratchpad/cycle40/runs/tap-T41pd`,
   contact 8,700 -> `TP_POINT` 8,701; `touch-latency.md`] [O: same].

The gate word reads `2c00` on every frame -- bit 15 clear -- the same value the port's
`hostinput.c` and `frameswap.c` park it at, so the original agrees with the port that the gate
is open [O: same; E: `port/platform/hostinput.c`].

## The supporting measurements, and their negative controls

The movie format had to be established before any of this meant anything. A `.dsm` frame line
is `|<commands>|<13 pad chars><xxx> <yyy> <t> <mmm>|` with **no pipe of its own before the touch
group**; the four fields are the lower-screen pixel column, the pixel row, the down flag and a
microphone sample [O: `port/tools/oracle/README.md`, "The .dsm touch columns"]. Two controls
were run by rewriting one field of a working movie and replaying it:

- **`t` forced to 0, coordinates left in place**: no contact at all, zero stylus rows. So the
  third field is the flag, and it is not "non-zero coordinates mean touch."
- **an extra `|` inserted before the touch group**: identical result, all 28 rows unchanged. So
  DeSmuME's decimal reader skips non-digit separators; the tool writes the pipe-less form
  anyway, because that is what DeSmuME's own dumper produces.

[O: same; the retained control script is `scratchpad/oracle/tool-updates/negctl.py`, throwaway].

The pad column mapping was measured the same way rather than read: the obvious reading of the
thirteen columns `RLDUTSBAYXWEG` is wrong -- **column `T` is SELECT and column `S` is START** --
caught by the input contract on the first keyed run (expected mask 9 = A|START, observed 5 =
A|SELECT), then all ten KEYINPUT bits were verified in one run with
`--keys 0x3ff --keys-at 1 --keys-for 2 --keys-every 0` [O: same].

The window rule itself was verified against a 300-frame probe with two contacts:
frames 100..109 and 160..169 at 221,181, nothing at 220 because `REPEAT=2` stops after two
contacts, and 250..254 at 40,20 for the second contact -- every observed row equal to its
expected row, edges on the exact frames, and the two contacts told apart by coordinate
[O: same].

## The runs

- The `TP_POINT` probe: `port/tools/oracle/README.md`'s table, 1,200 frames.
- `scratchpad/oracle/tap-220` and `scratchpad/oracle/tap-window` -- two 27,000-frame oracle runs
  under the town recipe's pad phases, both with the stylus held for 40 movie frames, 32 and 51
  shots respectively, both COMPLETE at frame 27,000
  [O: their `manifest.json` and `.out` files]. Neither has been compared against a port arm yet.
- `scratchpad/cycle40/runs/tap-D60` -- the port at 221,181 with shots every 60 frames from
  24,000, exit 100 at 27,000, four contacts logged
  [E: its `receipt.json` and `tap-D60-run.log`].
- `scratchpad/cycle40/runs/tap-D61` -- **the one-pixel test**: the same recipe with the contacts
  moved to `ACWW_TOUCH_X=222 ACWW_TOUCH_Y=182`, the coordinates the original's game actually
  sees. Exit 100 at 27,000, log shows `acww touch: DOWN x=222 y=182` for all four contacts
  [E: its `receipt.json` and `tap-D61-run.log`]. Compared against `tap-220` under ORACLE42 --
  see the Result section below [S: `docs/log/cycle40-keyboard-gate-probe.md` ORACLE42].

## What would falsify it

- A probe run where `0x021fbde8` stays at 255, 255, 0, 0 through the contact window: the tap
  reaches the emulator's input layer but not the game, and every comparison built on it is void.
- The gate word reading anything with bit 15 set. If touch ever goes dead on either side, check
  that bit before anything else [H: host-source account from `port/shim/input/touch.c`; verify with a retained scripted run and frame using this page's recipe].
- (Run, and this is what happened.) The `tap-D61` versus `tap-220` comparison still parted at
  25,500, which ruled the one pixel out and left the one-to-two-frame lag as the explanation --
  confirmed by moving the tap off the A-press frame. See the Result section below.

One caveat on the instrument, recorded as "unexplained" when this page was drafted and now
partly explained: `memory.readword` in that Lua build returned 255 in the no-touch rows, which
was read as "it delivers only the low 8 bits" against a port transcription that wrote 0xffff.
TOUCH41 read the ROM instead -- `mov r1,#0xff` and a `strh` at `0x020e941c` -- so the ROM's own
no-touch value is **0x00ff**, and the probe's 255 is the right answer rather than a truncated
one [S: `func_020e9314`, autoload_2, disassembly `0x020e9314`..`0x020e9470`;
`docs/log/cycle40-keyboard-gate-probe.md` TOUCH41]. That removes the reason to doubt these
rows; whether that Lua build's `readword` is wide in general is untested and is not needed
here, since every value in the table is below 256
[O: `port/tools/oracle/README.md`; M1].

**Frame mapping, stated:** emulator frame N is taken to be port frame N, offset 0. `--offset`
shifts the movie's taps together with its presses and its screenshots, so the assumption is a
single knob, but it is the unproven assumption of the whole tool -- and it matters more for
touch than for keys, because a press that lands early is usually absorbed by a menu still
waiting, while a tap that lands outside a button's hit window simply does not happen
[O: `port/tools/oracle/README.md`, "Frame mapping"; `docs/state/open-questions.md` item (c)].


## Result (ORACLE42, after this page was drafted)

The one-pixel test is negative: the port with contacts at 222,182 still confirms the town
name (`tap-D61`, top screen black from 25,200 = the ride) and the original with contacts at
220,180 still does not (`scratchpad/oracle/tap-220`, keyboard to 27,000) [E: `tap-D61`]
[O: `scratchpad/oracle/tap-220`]. The frame is the cause: 24,600 is a KEYS3 A-press frame
(2400 + 37 x 600) while 8,700 is not, and the original's stylus sample reaches the game 1-2
frames after the port's, so the press and the tap are ordered differently on the two sides
[S: docs/log/cycle40-keyboard-gate-probe.md ORACLE42]. With `ACWW_TOUCH2_AT=24700` both
confirm and agree: 11 frames 24000..27000 at mean ncc 0.9955, top screen 1.0000
[E: `tap-D62`] [O: `scratchpad/oracle/tap-24700`]. The recipe of record uses 24,700.
**Since settled (TOUCH41, TOUCH42):** the latency is modelled rather than avoided. The ROM's
own `func_020e9314` runs on the interpreter path and the port fills the ARM7's ring, after the
ROM's VBlank handler; the 24,600 recipe then stays on the keyboard exactly as the original does
[E: `scratchpad/cycle40/runs/tap-T42b`] [O: `scratchpad/oracle/tap-window`]. The timing
measurement has its own page now: `touch-latency.md`.

## Related

- `../systems/input-and-touch.md`
- `touch-latency.md` -- the timing half of the same pipeline
- `two-tap-town-recipe.md`, `off-recipe.md`
