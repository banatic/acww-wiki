# Input and touch

**Summary.** The DS gives the game two input devices and the ARM9 can read neither of them
completely on its own. Eight of the ten buttons live in a register it can read directly; X, Y
and the debug bit arrive from the ARM7 through a shared halfword; and the stylus arrives as
raw analogue-to-digital counts in a ring buffer that the ARM7 fills and the ARM9 converts to
screen pixels with a calibration the console's owner recorded years earlier. Animal Crossing
reads all of this once per frame and republishes a single touch point at `0x021fbde8` that
everything downstream consumes. The PC port injects a mouse at the *output* of the
calibration, which is why its taps and the original's differ by one pixel and about two
frames -- the single best-measured disagreement in the project.

## What happens

### The pad

`func_020e9548` is the game's whole key path, and it reads two words:

    held = ((*0x04000130 | *0x027fffa8) ^ 0x2fff) & 0x2fff

so both registers are active low and the button space is the mask `0x2fff`
[S: `func_020e9548`, autoload_2, `src/matched/func_020e9548.c`]. `0x04000130` is
`REG_KEYINPUT` and carries bits 0..9 -- A, B, SELECT, START, Right, Left, Up, Down, R, L
[S: `func_ov001_0222db68`, ov001, `src/matched/func_ov001_0222db68.c`]. `0x027fffa8` is the
halfword the ARM7 maintains in shared low WRAM and carries X, Y and the debug bit
[S: `func_ov001_0222db68`, ov001, `src/matched/func_ov001_0222db68.c`]. Released is therefore
`0x03ff` in the register and `0x2c00` in the shared halfword, which OR to exactly `0x2fff`
[E: `port/platform/hostinput.c`; the ARM7 halfword reads `2c00` on every frame of the oracle's
probe run, O: `port/tools/oracle/README.md`, the `TP_POINT` probe table].

**Bit 15 of `0x027fffa8` means "report nothing"**, and it is checked all over the game rather
than only in the input path: `func_0200f748` and `func_020089b0` in main gate state
transitions on it, `func_ov001_0221ff3c` and `func_ov001_02218fa0` return it as a boolean, and
two ov055 functions gate RTC work on it -- so it reads as a general "hardware access blocked"
flag rather than an input flag [S: `src/matched/func_0200f748.c`,
`src/matched/func_020089b0.c`, `src/matched/func_ov055_022607a0.c`].

Key repeat is the game's, not the SDK's. `func_ov001_0222db68` keeps a `PadStatus` with
`cur`, `trg` (newly pressed), `up` (newly released) and `trgRepeat`, and walks a fourteen-entry
timer array: a held button re-triggers once it has been down 40 frames and every 7 frames
after that [S: `func_ov001_0222db68`, ov001, `src/matched/func_ov001_0222db68.c`]. A separate
combo detector in main reads `0x04000130` masked to `0x3ff` and runs a seven-state sequence
machine [S: `func_02001324`, main, `src/matched/func_02001324.c`].

### The stylus

The touch panel is sampled by the ARM7 continuously, not on demand. `func_020e948c` performs
the whole bring-up in order -- `TP_Init`, `TP_GetUserInfo`, `TP_SetCalibrateParam`,
`TP_RequestSetStabilityAsync(3, 30)`, wait, `TP_RequestAutoSamplingStartAsync(0, 4, &gAutoData,
9)`, wait -- so ACWW runs a **nine-entry** ring at a sampling period of 4
[S: `func_020e948c`, autoload_2, `src/matched/func_020e948c.c`]. The ring itself is the
caller's memory; the SDK only stores the pointer and the size
[S: `TP_RequestAutoSamplingStartAsync`, autoload_2,
`src/matched/TP_RequestAutoSamplingStartAsync.c`].

Each entry is a `TPData` of four halfwords: x, y, touch, validity. `touch` is 0 or 1 for
pen-up/pen-down; **`validity` is an error code and 0 means the sample is good**, so a consumer
skips the entries whose validity is non-zero rather than the ones where it is clear
[S: `TP_GetCalibratedPoint`, autoload_2, `src/matched/TP_GetCalibratedPoint.c`;
`func_ov001_0222d9b0`, ov001, `src/matched/func_ov001_0222d9b0.c`]. Delivery is by PXI tag 6:
`TPi_TpCallback` increments `tpState.index` modulo the buffer size and then unpacks a packed
bitfield (x:12, y:12, touch:1, validity:2) from the shared system-work area
[S: `TPi_TpCallback`, autoload_2, `src/matched/TPi_TpCallback.c`].

Calibration turns 12-bit ADC counts into pixels. The console's owner touched two crosses during
firmware setup; `TP_GetUserInfo` reads those two raw/display point pairs out of NVRAM and
`TP_CalcCalibrateParam` derives an origin and a counts-per-pixel slope per axis by linear
interpolation, range-checking each into an `s16`
[S: `TP_GetUserInfo`, autoload_2, `src/matched/TP_GetUserInfo.c`; `TP_CalcCalibrateParam`,
autoload_2, `src/matched/TP_CalcCalibrateParam.c`]. `TP_SetCalibrateParam` then precomputes a
reciprocal `0x10000000 / dotSize` per axis using the hardware divider at `0x04000280`
[S: `TP_SetCalibrateParam`, autoload_2, `src/matched/TP_SetCalibrateParam.c`]. In words, the
conversion shifts the raw count left by 2, subtracts the origin, multiplies by that reciprocal
and shifts right by 22, then clamps x to 0..255 and y to 0..191
[S: `TP_GetCalibratedPoint`, autoload_2, `src/matched/TP_GetCalibratedPoint.c`].

### The per-frame publish

`func_020e9314` is where the two worlds meet. It reads the last four entries of the ring
through `TP_GetLatestIndexInAuto`, copies the ones whose invalid halfword is clear, and then
takes one of three branches: three good samples ending at the newest calibrates the newest into
`0x021fbde8`; three good samples ending one older calibrates that one; nothing valid writes
the no-touch state, x = y = 0xffff with both flags zero [S: `func_020e9314`, autoload_2, read
from its literal pool and transcribed in `port/shim/input/touch.c`]. Whichever branch ran, the
tail is the same: the pressed flag is XORed against the previous frame's to make a trigger
byte at `0x021fbddc`, the previous flag at `0x021fbdd8` is updated, and x and y are republished
to `0x021fbde0` and `0x021fbde4` [S: transcribed in `port/shim/input/touch.c`].

The consumer is `func_020b9280`, the only caller, and it truncates both coordinates to `u8` --
which is why the published x is 0..255 and y is 0..191. **It calls `func_020e9314` only when bit
15 of `0x027fffa8` is clear** [S: `func_020b9280`, main, `src/matched/func_020b9280.c`, as
recorded in `port/shim/input/touch.c`].

### What the port does instead

There is no panel and no ARM7, so the port replaces `func_020e9314` with the no-touch branch
plus an injection point, and injects at the **output** of the calibration rather than the
input. Filling the ring with synthetic ADC counts so that an invented calibration could convert
them back into the pixels we started with is a round trip through two SDK functions for no gain
[E: `port/shim/input/touch.c`]. A host mouse click on the lower half of the window becomes
`touch = 1, validity = 0` at that pixel; the upper half is not a touch, because the digitiser
sits under the bottom screen only [E: `port/shim/input/touch.c`, `port/render/window.c`].

The pad is written every frame rather than on edges, from the frame boundary in
`port/platform/frame.c` rather than from the main-loop body -- the body was measured running
about once every three frames, which would be a 20 Hz keyboard [E: `port/platform/hostinput.c`].
The map is arrows for the D-pad, Z=A, X=B, A=Y, S=X, Enter or Space=START, Backspace or
right-Shift=SELECT, Q=L, W=R, left-click the lower screen for the stylus, Escape to quit
[E: `port/platform/hostinput.c`]. When `ACWW_KEYS` names a nonzero mask in the `0x2fff` space,
or `ACWW_KEYS3_ENABLE` is set, the scripted path owns the registers and the live keyboard is
ignored entirely; the run says which it is on one announcement line
[E: `port/platform/hostinput.c`].

Scheduled contacts are the instrument every touch measurement uses:
`ACWW_TOUCH_ENABLE`, `_X`, `_Y`, `_AT`, `_FOR`, plus `_EVERY` (repeat period, must exceed
`_FOR`) and `_REPEAT` (contact count; absent means unbounded), and an independent second
contact `ACWW_TOUCH2_*` with the same six fields. **The second contact is tested first and wins
its own window** [E: `port/shim/input/touch.c`;
`docs/kb/hybrid/hardware-services.md` section 6]. The config is parsed once through
`GetEnvironmentVariableA` directly, because the port's own `acww_env_dec` folds unset,
unparsable and zero into one answer; anything short of a fully valid config prints one refusal
line and stays disabled for the run [E: `port/shim/input/touch.c`].

## The port and the original disagree, measurably

The oracle's probe mode reads the ROM's own `TP_POINT` at `0x021fbde8` on the original. With
the contact scheduled at 221,181 for 10 frames every 60, twice, from frame 1000:

| movie frame | movie stylus | `0x021fbde8` x, y, touch, validity | `0x027fffa8` |
|---|---|---|---|
| 1000..1009 | down 221,181 | 222, 182, 1, 0 | `2c00` |
| 1010 | up | 222, 182, 1, 0 (one frame of lag) | `2c00` |
| 1060..1061 | down 221,181 | 255, 255, 0, 0 (not yet sampled) | `2c00` |
| 1062.. | down 221,181 | 222, 182, 1, 0 | `2c00` |

[O: `port/tools/oracle/README.md`, "...and the tap reaches the GAME", 1,200-frame probe run].

Three things follow. The contact does reach the game. **The coordinates come back one pixel
high** -- 221,181 in, 222,182 out -- because the emulator converts screen pixels to raw ADC
counts and `TP_GetCalibratedPoint` converts them back, a round trip the port deliberately skips
[O: same]. And **the game sees the contact one to two frames late and holds it one frame long**,
because the ring is filled a frame before the ARM9 reads it, where the port publishes on the
exact frame [O: same]. That two-frame difference is real, measured and unavoidable between the
two producers, and it is the standing candidate explanation for any tap that works on one side
only [O: same].

One caveat on the instrument itself: `memory.readword` in that Lua build returned 255 where the
ROM writes 0xffff, so it appears to deliver only the low 8 bits. The tap/no-tap distinction and
the coordinates are unaffected; the 16-bit values are not verified [O: same; M1].

The disagreement it may explain is the second keyboard. Under the town recipe the port and the
original are on the same screen step for step from frame 6000 to 24000 -- whole-frame ncc
0.9920 to 0.9959 across nine sampled frames -- and then part at 25,500, inside the `TOUCH2`
window: the port's two taps confirm the town name and the original's identical taps do not,
leaving it on the town-name keyboard to 48,000 (ncc falls to about 0.70 and the top-screen ncc
to 0.0000) [O: `scratchpad/oracle/tap-fullpad/compare-vs-tap-D56.txt`, frames 6000..48000]
[E: `scratchpad/cycle40/runs/tap-D56`]. **That is settled (ORACLE42) and the answer is in the
Result section at the end of this page: neither side was wrong, the tap frame was.**

## Where it lives

| function or symbol | module | role | grade/citation |
|---|---|---|---|
| `func_020e9548` | autoload_2 | the game's key read: `((KEYINPUT | ext) ^ 0x2fff) & 0x2fff`, previous, changed | [S: `src/matched/func_020e9548.c`] |
| `func_ov001_0222db68` | ov001 | `PadStatus` with `cur`/`trg`/`up`/`trgRepeat` and the 40-then-7-frame repeat | [S: `src/matched/func_ov001_0222db68.c`] |
| `func_02001324` | main | a seven-state combo detector on `0x04000130` masked to `0x3ff` | [S: `src/matched/func_02001324.c`] |
| `TP_Init` | autoload_2 | PXI bring-up, registers `TPi_TpCallback` on the touch tag | [S: `src/matched/TP_Init.c`] |
| `TP_RequestAutoSamplingStartAsync` | autoload_2 | installs the caller's ring, clears every slot's touch flag, asks the ARM7 to start | [S: `src/matched/TP_RequestAutoSamplingStartAsync.c`] |
| `TP_RequestSetStabilityAsync` | autoload_2 | ADC retry/range noise rejection; ACWW passes (3, 30) | [S: `src/matched/TP_RequestSetStabilityAsync.c`] |
| `TP_GetLatestIndexInAuto` `0x0211d00c` | autoload_2 | returns the newest ring index | [S: `src/matched/TP_GetLatestIndexInAuto.c`] |
| `TP_GetCalibratedPoint` `0x0211cc6c` | autoload_2 | raw ADC to screen pixels, with the 0..255 / 0..191 clamp | [S: `src/matched/TP_GetCalibratedPoint.c`] |
| `TP_SetCalibrateParam`, `TP_CalcCalibrateParam`, `TP_GetUserInfo` | autoload_2 | install, derive and load the calibration from firmware NVRAM | [S: `src/matched/TP_SetCalibrateParam.c`] |
| `TP_CheckError`, `TP_WaitBusy` | autoload_2 | poll `err_flg`, spin on `command_flg` | [S: `src/matched/TP_WaitBusy.c`] |
| `TPi_TpCallback` | autoload_2 | the PXI tag-6 receive handler; unpacks x:12 y:12 touch:1 validity:2 | [S: `src/matched/TPi_TpCallback.c`] |
| `func_020e948c` | autoload_2 | the game's touch bring-up; starts a 9-sample ring at period 4 | [S: `src/matched/func_020e948c.c`] |
| `func_020e9314` | autoload_2 | the per-frame publish and its three branches | [S: literal pool, transcribed in `port/shim/input/touch.c`] |
| `func_020b9280` | main | the only consumer; truncates to u8; gates on bit 15 of `0x027fffa8` | [S: `src/matched/func_020b9280.c`] |
| `func_ov001_0222d9b0` | ov001 | DWC's own "readTouch": walks the ring backwards, skips invalid, derives edges | [S: `src/matched/func_ov001_0222d9b0.c`] |
| `func_ov126_022a04e8` | ov126 | the keyboard hit-test; calls bare `sub_229c54c` / `sub_229c448` whose resident bodies are `func_ov095_0229c54c` / `0229c448` | [S: `src/matched/func_ov126_022a04e8.c`; `docs/kb/port/input-save-audio.md`, KBD39] |

## Data it reads and writes

| address or field | meaning | who writes | who reads |
|---|---|---|---|
| `0x04000130` | `REG_KEYINPUT`, bits 0..9, active low | the hardware (the port: `acww_input_publish`) | `func_020e9548`, `func_02001324`, `func_ov001_0222db68` [S: `src/matched/func_020e9548.c`] |
| `0x027fffa8` | ARM7 shared halfword: X bit 10, Y bit 11, debug bit 13, active low; bit 15 = report nothing | the ARM7 (the port parks `0x2c00`) | the same three, plus six gates in main/ov001/ov055 [S: `src/matched/func_ov001_0222db68.c`] |
| `0x021fbde8` | `TP_POINT`: `{u16 x, u16 y, u16 touch, u16 validity}` | `func_020e9314` | `func_020b9280` [S: `src/matched/func_020b9280.c`] [O: probe mode, `port/tools/oracle/README.md`] |
| `0x021fbdd8` | the previous frame's touch flag, one byte | `func_020e9314` | itself, next frame [S: transcribed in `port/shim/input/touch.c`] |
| `0x021fbddc` | the trigger byte: this frame's flag XOR the last | `func_020e9314` | the UI [S: same] |
| `0x021fbde0` / `0x021fbde4` | the republished x and y | `func_020e9314` | `func_020b9280` [S: same] |
| `0x021fbdf0` | the nine-entry auto-sampling ring `gAutoData` | the ARM7 through `TPi_TpCallback` (nothing on the port) | `func_020e9314` [S: `src/matched/func_020e948c.c`] |
| `0x021f6c54` | the touch Y the keyboard's `< 0x48` compare tests -- a coordinate, not a counter | the keyboard | `func_ov126_022a1228` [S: `docs/kb/port/input-save-audio.md`, KBD39] |
| `0x04000280` | the hardware divider, used to precompute the calibration reciprocals | `TP_SetCalibrateParam` | itself [S: `src/matched/TP_SetCalibrateParam.c`] |

## How to check it

`../experiments/touch-calibration.md` is the measurement above, with its recipe and its
negative controls. `../experiments/two-tap-town-recipe.md` is the run every downstream touch
observation is taken under. `../experiments/off-recipe.md` is the control both are read against.

## Hypotheses

- The one-pixel offset is what makes the original refuse the second keyboard's confirm button.
  Evidence against: the port was re-run with the contact moved to 222,182 -- the coordinates
  the original's game actually sees -- and the taps still arrive as
  `acww touch: DOWN x=222 y=182`, four contacts, exit 100 at 27,000 frames
  [E: `scratchpad/cycle40/runs/tap-D61`, `ACWW_TOUCH_X=222 ACWW_TOUCH_Y=182`]. **Settled
  negative (ORACLE42)**: `tap-D61` against `scratchpad/oracle/tap-220` still parts, so the pixel
  is not the cause [S: `docs/log/cycle40-keyboard-gate-probe.md` ORACLE42].
- The one-to-two-frame stylus lag is the cause instead. **Settled positive (ORACLE42)**: moving
  the tap off the KEYS3 A-press frame to 24,700 makes both sides confirm and agree
  [S: `docs/log/cycle40-keyboard-gate-probe.md` ORACLE42; E: `tap-D62`;
  O: `scratchpad/oracle/tap-24700`]. What remains open is whether the PORT should model the lag
  rather than the recipe avoid it -- see the Result section.
- Hold duration is not a lever. Measured on the native path: `FOR=10` and `FOR=90` at the same
  frame and coordinate produced byte-identical images at all nine sampled frames
  [E: `docs/kb/port/input-save-audio.md`, TOUCH39]. It stays a hypothesis on the interpreter
  path, where the keyboard is driven by ROM code rather than shims.
- The reason the first tap never confirms is the mode switch, not the hit test: the keyboard
  consumes the first contact as a PAD-to-stylus mode change, and only a second contact inside
  the stylus-mode window reaches the confirm button
  [E: `docs/log/cycle40-keyboard-gate-probe.md` H4 RESULT and TAP40;
  `scratchpad/cycle40/runs/tap-native`, `tap-interp`]. Settled further by probing the
  keyboard's own state word rather than the screen.
- A person with the keyboard can walk out of the town hall where the scripted recipe cannot
  [E: `scratchpad/cycle40/runs/tap-D59`, 90,000 frames of talking to Pelly again].


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
Open hypothesis: model the 1-2 frame stylus latency in port/shim/input/touch.c
[H: rerun the 24,600 recipe after the change and compare with `scratchpad/oracle/tap-fullpad` at 25,500].

## Related

- `../experiments/touch-calibration.md`, `../experiments/two-tap-town-recipe.md`,
  `../experiments/off-recipe.md`.
- `time-and-rtc.md` -- the frame counter every `_AT` is expressed in.
