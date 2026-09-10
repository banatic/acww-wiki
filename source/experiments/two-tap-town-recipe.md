# The two-tap town recipe

**Status: run and receipted.** This is the recipe that walks the game from the title screen to
a conversation inside the town hall, and every observation about the taxi, the two keyboards,
the town and the sky is taken under it.

## Purpose

Drive the game with scripted pad pulses and four scheduled stylus contacts far enough to see the
town, so that the port and the original can be compared over 48,000 frames.

**Why two taps and not one.** Under a one-tap recipe the ROM's own keyboard logic does not
confirm the name either -- the interpreter run and the native run matched 9 of 9 frames -- so
the port was never wrong on that path; the recipe was
[E: `docs/log/cycle40-keyboard-gate-probe.md` H4 RESULT and TAP40;
`scratchpad/cycle40/runs/tap-native`, `tap-interp`]. The first tap switches the keyboard from
pad mode to stylus mode and the state that would act on it only runs from the next frame, when
the press edge is gone; a second tap inside the stylus-mode window is what the confirm button
can see [E: `port/shim/input/touch.c`].

**Why the taps must stop.** Repeating taps hold the yes/no menu and stall the conversation,
because a contact during a dialogue does not advance it. `ACWW_TOUCH_REPEAT=2` is what lets the
scripted A pulses carry the rest [E: `docs/log/cycle40-keyboard-gate-probe.md` TAP40, MENU40,
OVL40; `scratchpad/cycle40/runs/tap-D55b`].

## Recipe

    python -B scratchpad/cycle40/run_town.py <name> \
      ACWW_INTERP=1 ACWW_INTERP_STEPS=4000000000 \
      ACWW_TOUCH_AT=6900 ACWW_TOUCH_EVERY=60 ACWW_TOUCH_REPEAT=2 \
      ACWW_TOUCH2_X=221 ACWW_TOUCH2_Y=181 ACWW_TOUCH2_AT=24700 ACWW_TOUCH2_FOR=10 \
      ACWW_TOUCH2_EVERY=60 ACWW_TOUCH2_REPEAT=2 \
      ACWW_STOP_FRAME=48000 ACWW_SHOT_AFTER=6000 ACWW_SHOT_EVERY=1500 ACWW_PAD_SAMPLE=0

[E: `docs/kb/hybrid/recipes.md` section 3; `docs/state/port-frontier.md`, verified-at
`6ca48706`].

The script's own base supplies the rest: the custom START pad phases -- primary mask 9 at frame
300, `FOR` 10, `EVERY` 30; phase 2 mask 8 at 1,800 with `RELEASE_FOR` 60; phase 3 mask 1 at
2,400 with `EVERY` 600 -- plus `ACWW_RTC_DATE=20050615`, `ACWW_RTC_TIME=100000`,
`ACWW_NOPACE=1`, `ACWW_TRAMP_CONTINUE=1`, `ACWW_ASSERT_CONTINUE=1`, and the first contact at
`ACWW_TOUCH_X=221 ACWW_TOUCH_Y=181 ACWW_TOUCH_FOR=10`. It also unsets the oracle, save, explore
and keyboard-probe variables so a stale export cannot leak in
[E: `scratchpad/cycle40/run_town.py`, `BASE`; `docs/kb/hybrid/recipes.md` section 3].

`ACWW_INTERP_STEPS` is no longer needed: the default is 0, meaning unbounded, and a game run is
bounded by `ACWW_STOP_FRAME` instead [E: `docs/log/cycle40-keyboard-gate-probe.md` LONG41,
`scratchpad/cycle40/runs/tap-D58`, which stopped at ~61,000 frames with `STOP status=STEP
BUDGET`].

The oracle arm mirrors every one of those variables one for one, including the pad-phase
ownership rule and the touch window rule, and `observer.lua` enforces both contracts every
frame [O: `port/tools/oracle/README.md`; `docs/log/cycle40-keyboard-gate-probe.md` ORACLE41].

## Expected observations

| frames | what is on screen |
|---|---|
| 4,500..7,500 | the taxi interior with the player-name keyboard |
| ~7,500 | the player's name confirmed |
| 9,000..13,500 | the ride; the **top screen is black on both the port and the original**, so that is the game's behaviour, not a port defect [O: `scratchpad/oracle/tap-fullpad/compare-vs-tap-D56.txt`, ncc-top 1.0000 at 9000..13500] |
| 15,000..24,000 | the conversation, then the town-name keyboard |
| ~24,700 | the town name confirmed on both the port and the original (24,600 confirms on the port only -- ORACLE42) |
| 37,500 | the player in front of the town hall; overlays 5, 36, 54, 120 and 117 loaded |
| 37,800 | clouds over the blue sky, once affine backgrounds are drawn [E: `scratchpad/cycle40/runs/tap-D57`, SKY40] |
| 39,000 | a transition |
| 40,500..48,000 | inside the town hall, talking to Pelly, a choice prompt on screen |

[E: `docs/log/cycle40-keyboard-gate-probe.md` TOWN40, SKY40;
`scratchpad/cycle40/runs/tap-D56`].

Endpoint: 48,000 frames, child exit 100, no fault, no STOP, no HUNG, about 59 frames per second
unpaced, 811 seconds, 31 shots, a 59,808-line log
[E: `scratchpad/cycle40/runs/tap-D56/receipt.json`, `exit 100`, `seconds 811.1`].

## The runs that produced them

- `scratchpad/cycle40/runs/tap-D56` -- the diagnostic run TOWN40 reports, 48,000 frames
  [E: its `receipt.json` carries `diagnostic: true`].
- `scratchpad/cycle40/runs/tap-D57` -- the same with affine backgrounds drawn (SKY40).
- `scratchpad/cycle40/runs/town-R1` -- **the receipted run**, and the first receipted run of the
  interpreter path: launcher exit 0, child exit 100 at 48,000, 801 seconds, 29 shots, no fault
  markers [E: `docs/log/cycle40-keyboard-gate-probe.md` RECEIPT41, commit `6ca48706`].
- `scratchpad/cycle40/runs/tap-D59` -- 90,000 frames; Pelly says goodbye at 60,000 and the A
  pulses talk to her again through 90,000. The recipe cannot walk out of the town hall
  [E: LONG41].
- `scratchpad/oracle/tap-fullpad` -- the oracle arm and its comparison table.

**A receipt and a diagnostic are not the same claim.** A receipt is a run through
`port/tools/run.py --receipt` on a READY pipeline artifact with the sealed log copied and hashed
beside it; a diagnostic is a direct `acww.exe` launch. Say which, plus the launcher, the
artifact provenance, the path and the endpoint (B1, B8, B32)
[E: `docs/kb/hybrid/recipes.md` section 5].

## What the comparison says

Against the oracle at offset 0, whole-frame normalised cross-correlation
[O: `scratchpad/oracle/tap-fullpad/compare-vs-tap-D56.txt`]:

| frames | ncc | ncc-top | reading |
|---|---|---|---|
| 6,000..24,000 | 0.9920..0.9959 | 0.9249..1.0000 | the same screen, step for step |
| 25,500..36,000 | 0.6957..0.7046 | 0.0000 | they have parted |
| 39,000 | 0.0000 | 0.0000 | a transition on one side only |
| 40,500..48,000 | 0.6661..0.6761 | 0.0000 | still parted |

29 frames compared, 0 exact in RGB, mean ncc 0.8008 [O: same]. They part at 25,500, inside the
`TOUCH2` window: the port's two taps confirm the town name and the original's identical taps do
not, and the original sits on the town-name keyboard to 48,000
[O: `docs/log/cycle40-keyboard-gate-probe.md` ORACLE41]. **Settled (ORACLE42): neither side was
wrong about the keyboard; the recipe was.** 24,600 is a KEYS3 A-press frame (2400 + 37 x 600)
and the original's stylus sample arrives one to two frames after the port's, so the press and
the tap are ordered differently on the two sides. With `ACWW_TOUCH2_AT=24700` both confirm and
agree -- 11 frames 24,000..27,000 at mean ncc 0.9955, top screen 1.0000
[S: `docs/log/cycle40-keyboard-gate-probe.md` ORACLE42; E: `tap-D62`;
O: `scratchpad/oracle/tap-24700`]. **The recipe of record therefore uses 24,700**, and the table
above is the 24,600 run kept for the record. The oracle cannot yet show the town, so the sky and
the town hall are still unscored.

## What would falsify it

- A run that reaches 48,000 with a fault marker, a STOP line or an `unimplemented:` line.
- The taps not arriving: the log must carry `acww touch: DOWN x=221 y=181` four times (two
  contacts at 6,900 and 6,960, two at 24,700 and 24,760) and the matching `up` lines. Count
  them; do not assume [E: `scratchpad/cycle40/runs/tap-D60/tap-D60-run.log`, 9 `acww touch:`
  lines].
- Reading the frame count or the wall clock as the result (B12). Judge the endpoint, the exact
  failure identity and the images.
- Freezing the tree in git terms only: the pipeline snapshot includes untracked files, and one
  build was refused at publication because an operator's new file appeared mid-build (S10)
  [E: `docs/kb/hybrid/recipes.md` section 8].

## Related

- `off-recipe.md` -- the control.
- `touch-calibration.md` -- the one-pixel, two-frame difference this recipe runs into, and how
  ORACLE42 settled it.
- `../systems/input-and-touch.md`, `../systems/time-and-rtc.md`

## Result against the reference (ORACLE43)

With `ACWW_TOUCH2_AT=24700` the DeSmuME reference follows the same path: town at 37,500,
town hall from 40,500, 15 frames 27000..48000 at mean ncc 0.8967 and the town-hall frames at
0.98-0.998 with identical top screens (black on both sides inside the town hall)
[O: `scratchpad/oracle/tap-town`] [E: `tap-D63`]. Two transition frames (39,000 and 46,500)
fall on opposite sides of a fade. At 37,500 the original's sky is perspective-scaled toward
the horizon and the port's is flat [H: the HBlank handler `func_01ffcc30` updates the affine
parameters per scanline; capture BG3 P*/X/Y per line and compare `tap-D63` 37,500 again].

Update (SKY41): with per-scanline register capture (the HBlank callbacks rewrite BG3's
affine parameters and BLDCNT/BLDALPHA per line) the port's sky at 37,500 flattens toward
the horizon and fades into the backdrop like the original's [E: `tap-D71`]
[S: docs/log/cycle40-keyboard-gate-probe.md SKY41].
