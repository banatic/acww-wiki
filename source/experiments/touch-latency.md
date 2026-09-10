# Touch latency: how many frames a contact takes to reach the game, and in what order

**Status: run.** This page is the pipeline a stylus contact travels on the interpreter path,
measured end to end, and the ordering rule that decides whether a tap or a button press
scheduled on the same frame reaches the game first. It is the sequel to
`touch-calibration.md`, which measured the *coordinates*; this one measures the *timing*.

## Purpose

`touch-calibration.md` established that the original delivers a tap one to two frames later
than the port did, and left it as the standing explanation for any tap that works on one side
only. Two questions were open. Where does the latency come from -- the emulator, the ARM7, or
the ROM? And is latency alone enough to reproduce the original's behaviour, or does something
else order a same-frame press and tap? The answers are: the latency is entirely the ROM's own
rule, and latency alone is **not** enough -- the position of the ARM7's samples relative to the
ROM's VBlank handler is the second half of the mechanism.

## The pipeline, stage by stage

1. **The ARM7 samples the panel, `frequence` times a frame.** `func_020e948c` asks for
   `TP_RequestAutoSamplingStartAsync(0, 4, &gAutoData, 9)`, so ACWW runs a **nine-entry ring**
   at four samples a frame -- 2.25 frames of history, and exactly one frame's worth in the last
   four entries [S: `func_020e948c`, autoload_2, `src/matched/func_020e948c.c`].
2. **Pen-up has its own encoding.** When the pen is up the ARM7 writes x=0, y=0, touch=0 and
   validity=3 (`TP_VALIDITY_INVALID_XY`); a pen-down sample carries the raw counts with
   validity 0 unless the pressure test rejects it
   [S: NitroSDK `libraries/spi/src/ARM7/tp/tp_sampling.c`, `TP_ExecSampling` -- public source,
   <https://github.com/ntrtwl/NitroSDK>].
3. **Delivery advances the ring.** `TPi_TpCallback` runs on PXI tag 6, increments
   `tpState.index` modulo the buffer size, and unpacks a packed bitfield (x:12, y:12, touch:1,
   validity:2) out of the shared system-work area
   [S: `TPi_TpCallback`, autoload_2, `src/matched/TPi_TpCallback.c`].
4. **The ROM publishes at most one point a frame, under a three-sample rule.**
   `func_020e9314` reads entries latest-4..latest-1 through `TP_GetLatestIndexInAuto` and
   publishes only when **three consecutive entries are touched and valid**, publishing the
   middle one; when nothing is touched it writes x = y = 0xff; anything else leaves `TP_POINT`
   alone [S: `func_020e9314`, autoload_2, disassembly `0x020e9314`..`0x020e9470`; the no-touch
   write is a `mov r1,#0xff` / `strh` pair at `0x020e941c`, i.e. **0x00ff, not 0xffff** --
   the port's earlier transcription had 0xffff and is now pinned by
   `port/tools/test_scheduled_touch.py`]. The consumer `func_020b9280` truncates both
   coordinates to `u8` [S: `src/matched/func_020b9280.c`].

The latency is stage 4 falling out of stage 1: with four samples a frame, a contact that begins
at the frame boundary cannot have three consecutive good samples until the frame after, so the
point appears one frame late.

## What the port does on the interpreter path

`port/shim/input/touch.c` is **denied** on the interpreter path (`DENY_FILES`, registry 89 ->
88), so the ROM's own `func_020e9314` runs and the port plays the ARM7 instead:
`port/shim/os/pxisend.c` notes the AUTO_ON request (tag 6, command 1, low byte = samples a
frame) and from then on writes `frequence` samples a VBlank into the ROM's own `tpState`
(`0x02206134`), then performs `TPi_TpCallback`'s AUTO_SAMPLING step -- index+1 mod bufSize,
copy -- on the host. Raw counts are screen pixel x 16 under an identity calibration that
`port/shim/boot/usersettings.c` publishes (raw1 16/16 -> 1/1, raw2 4080/3056 -> 255/191)
[S: `docs/log/cycle40-keyboard-gate-probe.md` TOUCH41]. The all-zero calibration of the native
days would have made `TP_SetCalibrateParam` install a zero slope and calibrate every tap to
0,0, which is why the identity calibration had to be published before any of this could be
measured [S: same].

## Recipe

All three arms are DIAGNOSTIC runs of `port/build/acww.exe` through
`scratchpad/cycle40/run_direct.py`, never receipted frontier claims (B38). The base is the
two-tap town recipe (`two-tap-town-recipe.md`); only the lines below differ.

**Arm 1 -- measure the latency (a peek at the ring and the point).**

    python -B scratchpad/cycle40/run_direct.py tap-T41pd ACWW_INTERP=1 \
      ACWW_TOUCH_ENABLE=1 ACWW_TOUCH_X=221 ACWW_TOUCH_Y=181 \
      ACWW_TOUCH_AT=8700 ACWW_TOUCH_FOR=10 ACWW_TOUCH_EVERY=60 ACWW_TOUCH_REPEAT=2 \
      ACWW_TP_DIRECT=1 ACWW_INTERP_PEEK=0x021fbde8,0x02206134,0x02206144 \
      ACWW_STOP_FRAME=8705 ACWW_SHOT_AFTER=8400 ACWW_SHOT_EVERY=150

**Arm 2 -- the ordering test at 24,600, samples BEFORE the ROM's VBlank handler.**

    ... ACWW_TOUCH2_X=221 ACWW_TOUCH2_Y=181 ACWW_TOUCH2_AT=24600 ACWW_TOUCH2_FOR=10 \
        ACWW_TOUCH2_EVERY=60 ACWW_TOUCH2_REPEAT=2 \
        ACWW_STOP_FRAME=27000 ACWW_SHOT_AFTER=6000 ACWW_SHOT_EVERY=300      # tap-T41h

**Arm 3 -- the same, samples AFTER the handler (`ACWW_TP_LATE=1`; now the default).**

    ... the same lines plus ACWW_TP_LATE=1                                   # tap-T42b

Compare each 27,000-frame arm against the oracle with

    python port/tools/oracle/compare.py \
      scratchpad/cycle40/runs/<arm> scratchpad/oracle/tap-window

and against `scratchpad/oracle/tap-24700` for the 24,700 variant.

## Expected observations

| what | where | observation |
|---|---|---|
| one frame of latency | contact scheduled at 8,700 | the ring holds nine samples at x 3536, y 2896 (221 x 16, 181 x 16), touch 1, and `TP_POINT` = (221,181) touched, first printed at **frame 8,701** [E: `scratchpad/cycle40/runs/tap-T41pd`] |
| samples before the handler, tap at 24,600 | port vs original | the port **confirms** the town name (top screen black from 24,900 = the ride) where the original stays on the keyboard, ncc 0.70 over 24,900..27,000 [E: `scratchpad/cycle40/runs/tap-T41h`] [O: `scratchpad/oracle/tap-window`] |
| samples after the handler, tap at 24,600 | port vs original | the port **stays on the keyboard** like the original: 11 frames 24,000..27,000 at mean ncc **0.9981**, top screen 0.97-0.99 (the keyboard on both sides) [E: `scratchpad/cycle40/runs/tap-T42b`] [O: `scratchpad/oracle/tap-window`] |
| the 24,700 recipe under the same order | port vs original | still confirms and still agrees: 11 frames at mean ncc **0.9987**, top screen 1.0000 from 24,900 [E: `scratchpad/cycle40/runs/tap-T42c`] [O: `scratchpad/oracle/tap-24700`] |

**The mechanism the third row establishes.** The ROM's VBlank handler samples the pad. A tap
and a scripted A press on the same frame therefore reach the game press-first only if the
tap's samples arrive **after** the handler -- which is the order the hardware produces, because
the ARM7 samples the panel during the frame that follows the VBlank the handler ran in. 24,600
is a KEYS3 A-press frame (2400 + 37 x 600) and 8,700 is not, which is why the disagreement
only ever showed at 24,600 [S: `docs/log/cycle40-keyboard-gate-probe.md` TOUCH42].
`ACWW_TP_EARLY=1` restores the TOUCH41 order for the record [S: same].

## What would falsify it

- Arm 1 printing `TP_POINT` at 8,700 rather than 8,701, or the ring holding fewer than three
  consecutive touched-and-valid entries at the peek: then the three-sample rule is not what
  produces the delay and the whole reading of `func_020e9314` is wrong.
- Arm 3 confirming the town name. That is exactly what arm 2 did, so the two arms are each
  other's control; if the switch stops mattering, the ordering claim is dead.
- A run in which the 24,700 recipe stops agreeing after the order changed. It was re-measured
  for that reason (`tap-T42c`), because a fix that repairs 24,600 by breaking 24,700 is not a
  fix.

## Open

- **The interpreted-callback anomaly (playbook case 42).** [H] The first implementation
  delivered each sample to the ROM's own `TPi_TpCallback` as a PXI word through
  `acww_pxi_deliver_pending` -- four interpreted calls a frame in IRQ context. It was
  **data-identical** to the host fill (`tap-T41q8705` against `tap-T41pd`: same ring, same
  index, same `TP_POINT`) and yet the game changed: the taxi dialogue advanced with no
  scripted input and both name keyboards typed their top-left key eight times and confirmed,
  reaching the town-name keyboard by frame 8,610 instead of about 24,000
  [E: `scratchpad/cycle40/runs/tap-T41j`, and `-T41a`, `-T41d`, `-T41g`, `-T41l`, `-T41v`].
  `TP_POINT` never changed while it happened [E: `tap-T41f`, the on-change instrument in
  `pxisend.c`]. The sampler off (`tap-T41k`) and the host fill (`tap-T41w`) both leave the
  game's pace as the baseline's (`tap-D71`); one interpreted callback a frame (`tap-T41x`)
  advances it a little; four interpreted **no-op** calls a frame
  (`TP_GetLatestIndexInAuto`, `tap-T41n`) do not. A read watchpoint on the ring index
  (`ACWW_INTERP_RWATCH=0x02206140`, `tap-T41y`) names its only two readers,
  `TP_GetLatestIndexInAuto` (`0x0211d010`) and the callback itself. So the game reacts to the
  interpreted *execution* of the callback, not to what it writes: an unknown side effect of
  `acww_interp_irq_run` on the input path [S: `docs/log/cycle40-keyboard-gate-probe.md`
  TOUCH41; `docs/kb/hybrid/stall-playbook.md` case 42]. The host fill ships;
  `ACWW_TP_PXI=1` keeps the interpreted path for whoever hunts this.
  **The experiment that would settle it:** run `ACWW_TP_PXI=1` with the *contact disabled*, so
  the four interpreted callbacks a frame still run but carry only pen-up samples. If the game
  still races ahead, the side effect is in `acww_interp_irq_run` itself (interrupt nesting,
  the IRQ stack, or a CPSR round trip) and has nothing to do with touch data; if it does not,
  the side effect is in what the callback does with a touched sample. Either answer is a
  one-run bisection of a hypothesis that currently has none.
- **Hold duration on the interpreter path.** [H] `FOR=10` and `FOR=90` produced byte-identical
  images at all nine sampled frames on the *native* path
  [E: `docs/kb/port/input-save-audio.md`, TOUCH39]. It has not been re-measured since the ROM's
  own `func_020e9314` took over the publish; settled by repeating that pair on the interpreter
  path.

## The runs

| run | what it is |
|---|---|
| `scratchpad/cycle40/runs/tap-T41pd` | the peek: ring, `tpState`, `TP_POINT` at frame 8,705, exit 100, 277 s |
| `scratchpad/cycle40/runs/tap-T41h` | 24,600, samples before the handler, exit 100 at 27,000, 867 s |
| `scratchpad/cycle40/runs/tap-T41i` | 24,700, samples before the handler: mean ncc 0.9986 against `tap-24700` |
| `scratchpad/cycle40/runs/tap-T42b` | 24,600, `ACWW_TP_LATE=1`, exit 100 at 27,000, 791 s |
| `scratchpad/cycle40/runs/tap-T42c` | 24,700, `ACWW_TP_LATE=1`, exit 100 at 27,000, 763 s |
| `scratchpad/oracle/tap-window`, `scratchpad/oracle/tap-24700` | the two oracle arms both are read against |

## Related

- `../systems/input-and-touch.md` -- the pipeline as a system page
- `touch-calibration.md` -- the coordinates, and the one-pixel round trip
- `two-tap-town-recipe.md` -- the recipe every arm above is a variant of
- `../audits/hardware-services.md` -- fix P1, closed by the arm-3 result
