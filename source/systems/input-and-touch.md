# Input and touch

**Summary.** The DS gives the game two input devices and the ARM9 can read neither of them
completely on its own. Eight of the ten buttons live in a register it can read directly; X, Y
and the debug bit arrive from the ARM7 through a shared halfword; and the stylus arrives as
raw analogue-to-digital counts in a ring buffer that the ARM7 fills and the ARM9 converts to
screen pixels with a calibration the console's owner recorded years earlier. Animal Crossing
reads all of this once per frame and republishes a single touch point at `0x021fbde8` that
everything downstream consumes. The PC port's native path injects a mouse at the *output* of
the calibration, which is why its taps and the original's differed by one pixel and about two
frames -- for a long time the single best-measured disagreement in the project. On the
interpreter path that gap is closed: the ROM's own per-frame publish runs and the port fills
the ARM7's ring instead, one frame of latency and all.

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
[H: log/source account: `port/platform/hostinput.c`; the ARM7 halfword reads `2c00` on every frame of the oracle's
probe run, O: `port/tools/oracle/README.md`, the `TP_POINT` probe table; receipt provenance unresolved].

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

When the pen is up the ARM7 writes x=0, y=0, touch=0 and validity=3 (INVALID_XY); a
pen-down sample carries the raw counts with validity 0 unless the pressure test rejects it
[H: source account: NitroSDK `libraries/spi/src/ARM7/tp/tp_sampling.c` (public source, `TP_ExecSampling`); direct ROM-source provenance unresolved].
The game's per-frame sample `func_020e9314` reads the four entries before the latest and
publishes only when three consecutive entries are touched and valid -- the middle one -- and
writes x=y=0xff when none is touched; otherwise it leaves the previous point in place
[S: `func_020e9314`, autoload_2, disassembly at 0x020e9314..0x020e9470]. That is where the
original's one-to-two-frame stylus latency comes from: with four samples a frame, a contact
that begins mid-frame is published the next frame [E: `scratchpad/cycle40/runs/tap-T41pd`,
contact scheduled at 8,700, TP_POINT set at 8,701]. The port models the ARM7 this way on the
interpreter path (`port/shim/os/pxisend.c`, TOUCH41) [H: source account: `docs/log/cycle40-keyboard-gate-probe.md` TOUCH41; direct ROM-source provenance unresolved].

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
the no-touch state, **x = y = 0x00ff** with both flags zero -- a `mov r1,#0xff` and a `strh`
at `0x020e941c`, not the 0xffff the port's first transcription assumed; the ROM's value is now
transcribed and pinned by `port/tools/test_scheduled_touch.py`
[S: `func_020e9314`, autoload_2, disassembly `0x020e9314`..`0x020e9470`;
`docs/log/cycle40-keyboard-gate-probe.md` TOUCH41]. Whichever branch ran, the
tail is the same: the pressed flag is XORed against the previous frame's to make a trigger
byte at `0x021fbddc`, the previous flag at `0x021fbdd8` is updated, and x and y are republished
to `0x021fbde0` and `0x021fbde4` [S: `config/adm-kr/arm9/autoload_2/symbols.txt`, `func_020e9314` at `0x020e9314`; historical account: transcribed in `port/shim/input/touch.c`].

The consumer is `func_020b9280`, the only caller, and it truncates both coordinates to `u8` --
which is why the published x is 0..255 and y is 0..191. **It calls `func_020e9314` only when bit
15 of `0x027fffa8` is clear** [S: `func_020b9280`, main, `src/matched/func_020b9280.c`, as
recorded in `port/shim/input/touch.c`].

### What the port does instead

**Two paths, and they differ here.** On the interpreter path -- the path of record since
TOUCH41 -- `port/shim/input/touch.c` is DENIED in the host-body registry (89 entries -> 88),
so the ROM's own `func_020e9314` runs and the port plays the ARM7 instead: `pxisend.c` notes
the AUTO_ON request and writes `frequence` samples a VBlank into the ROM's own `tpState` at
`0x02206134`, doing `TPi_TpCallback`'s AUTO_SAMPLING step on the host, under an identity
calibration that `port/shim/boot/usersettings.c` publishes (raw = pixel x 16). The samples land
**after** the ROM's VBlank handler, which is the hardware's order
[H: source account: `docs/log/cycle40-keyboard-gate-probe.md` TOUCH41, TOUCH42;
see `../experiments/touch-latency.md`; direct ROM-source provenance unresolved]. The rest of this section describes the NATIVE path,
which is still what runs without `ACWW_INTERP=1`.

There is no panel and no ARM7, so the port replaces `func_020e9314` with the no-touch branch
plus an injection point, and injects at the **output** of the calibration rather than the
input. Filling the ring with synthetic ADC counts so that an invented calibration could convert
them back into the pixels we started with is a round trip through two SDK functions for no gain
[H: host-source account from `port/shim/input/touch.c`; verify with a retained scripted run and frame using this page's recipe]. A host mouse click on the lower half of the window becomes
`touch = 1, validity = 0` at that pixel; the upper half is not a touch, because the digitiser
sits under the bottom screen only [H: host-source account from `port/shim/input/touch.c`, `port/render/window.c`; verify with a retained scripted run and frame using this page's recipe].

The pad is written every frame rather than on edges, from the frame boundary in
`port/platform/frame.c` rather than from the main-loop body -- the body was measured running
about once every three frames, which would be a 20 Hz keyboard [H: host-source account from `port/platform/hostinput.c`; verify with a retained scripted run and frame using this page's recipe].
The map is arrows for the D-pad, Z=A, X=B, A=Y, S=X, Enter or Space=START, Backspace or
right-Shift=SELECT, Q=L, W=R, left-click the lower screen for the stylus, Escape to quit
[H: host-source account from `port/platform/hostinput.c`; verify with a retained scripted run and frame using this page's recipe]. When `ACWW_KEYS` names a nonzero mask in the `0x2fff` space,
or `ACWW_KEYS3_ENABLE` is set, the scripted path owns the registers and the live keyboard is
ignored entirely; the run says which it is on one announcement line
[H: host-source account from `port/platform/hostinput.c`; verify with a retained scripted run and frame using this page's recipe].

Scheduled contacts are the instrument every touch measurement uses:
`ACWW_TOUCH_ENABLE`, `_X`, `_Y`, `_AT`, `_FOR`, plus `_EVERY` (repeat period, must exceed
`_FOR`) and `_REPEAT` (contact count; absent means unbounded), and an independent second
contact `ACWW_TOUCH2_*` with the same six fields. **The second contact is tested first and wins
its own window** [H: log/source account: `port/shim/input/touch.c`;
`docs/kb/hybrid/hardware-services.md` section 6; receipt provenance unresolved]. The config is parsed once through
`GetEnvironmentVariableA` directly, because the port's own `acww_env_dec` folds unset,
unparsable and zero into one answer; anything short of a fully valid config prints one refusal
line and stays disabled for the run [H: host-source account from `port/shim/input/touch.c`; verify with a retained scripted run and frame using this page's recipe].

`ACWW_PADSCRIPT=<file>` is the fourth scripted input and the only one that is a TIMELINE rather
than a pulse generator: one row per line, `<frame> <mask> <frames>` for the pad and
`<frame> T <x> <y> <frames>` for the stylus, numbers decimal unless prefixed `0x`, overlapping
pad rows OR together and the first matching stylus row wins
[H: source/log account from `port/platform/hostinput.c`; verify with a retained run using this page's recipe]. While a script is live it owns both pad registers from the
frame boundary and `port/shim/gfx/frameswap.c` writes neither, because `frameswap.c`'s phase2
and phase3 come back from a savestate as blobs with their old schedule still armed
[H: log/source account: `port/platform/hostinput.c`; `port/shim/gfx/frameswap.c`;
S: `docs/kb/hybrid/savestate.md` section 4; receipt provenance unresolved]. Its stylus rows are asked for before the
`ACWW_TOUCH*` schedule and before the mouse [H: source/log account from `port/shim/input/touch.c`; verify with a retained run using this page's recipe]. Unset, it changes
nothing: the OFF recipe on the build carrying it is 31/31 byte-identical to a relink of
untouched HEAD [H: `scratchpad/cycle40/runs/off-ps` vs `off-base`;
`docs/log/cycle41-gameplay.md`; receipt lost with its worktree; repeat the named recipe and retain the stated frames]. It is what let a scripted player walk out of the town hall and
around the town [H: log/source account: `wiki/experiments/gameplay-walkthrough.md`; receipt provenance unresolved].

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
[O: `port/tools/oracle/README.md`, "...and the tap reaches the GAME"]. And **the game sees the contact one to two frames late and holds it one frame long**,
because the ring is filled a frame before the ARM9 reads it, where the port publishes on the
exact frame [O: `port/tools/oracle/README.md`, "...and the tap reaches the GAME"]. That two-frame difference is real, measured and unavoidable between the
two producers, and it is the standing candidate explanation for any tap that works on one side
only [O: `port/tools/oracle/README.md`, "...and the tap reaches the GAME"].

One caveat on the instrument itself, since corrected: `memory.readword` in that Lua build
returned 255 in the no-touch rows, which looked like a low-8-bit truncation against a port
transcription that wrote 0xffff. The ROM's own no-touch value is **0x00ff**, so the probe's 255
is right [S: `func_020e9314`, disassembly `0x020e9314`..`0x020e9470`;
`docs/log/cycle40-keyboard-gate-probe.md` TOUCH41]. Whether that Lua build's `readword` is wide
in general is still untested, and every value in the table is below 256 either way
[O: `port/tools/oracle/README.md`, "...and the tap reaches the GAME"; M1].

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
| `func_020e9314` | autoload_2 | the per-frame publish and its three branches | [H: source account: literal pool, transcribed in `port/shim/input/touch.c`; direct ROM-source provenance unresolved] |
| `func_020b9280` | main | the only consumer; truncates to u8; gates on bit 15 of `0x027fffa8` | [S: `src/matched/func_020b9280.c`] |
| `func_ov001_0222d9b0` | ov001 | DWC's own "readTouch": walks the ring backwards, skips invalid, derives edges | [S: `src/matched/func_ov001_0222d9b0.c`] |
| `func_ov126_022a04e8` | ov126 | the keyboard hit-test; calls bare `sub_229c54c` / `sub_229c448` whose resident bodies are `func_ov095_0229c54c` / `0229c448` | [S: `src/matched/func_ov126_022a04e8.c`; `docs/kb/port/input-save-audio.md`, KBD39] |

## Data it reads and writes

| address or field | meaning | who writes | who reads |
|---|---|---|---|
| `0x04000130` | `REG_KEYINPUT`, bits 0..9, active low | the hardware (the port: `acww_input_publish`) | `func_020e9548`, `func_02001324`, `func_ov001_0222db68` [S: `src/matched/func_020e9548.c`] |
| `0x027fffa8` | ARM7 shared halfword: X bit 10, Y bit 11, debug bit 13, active low; bit 15 = report nothing | the ARM7 (the port parks `0x2c00`) | the same three, plus six gates in main/ov001/ov055 [S: `src/matched/func_ov001_0222db68.c`] |
| `0x021fbde8` | `TP_POINT`: `{u16 x, u16 y, u16 touch, u16 validity}` | `func_020e9314` | `func_020b9280` [S: `src/matched/func_020b9280.c`] [O: probe mode, `port/tools/oracle/README.md`] |
| `0x021fbdd8` | the previous frame's touch flag, one byte | `func_020e9314` | itself, next frame [S: `config/adm-kr/arm9/autoload_2/symbols.txt`, `func_020e9314` at `0x020e9314`; historical account: transcribed in `port/shim/input/touch.c`] |
| `0x021fbddc` | the trigger byte: this frame's flag XOR the last | `func_020e9314` | the UI [S: `config/adm-kr/arm9/autoload_2/symbols.txt`, `func_020e9314` at `0x020e9314`; historical account: `port/shim/input/touch.c`] |
| `0x021fbde0` / `0x021fbde4` | the republished x and y | `func_020e9314` | `func_020b9280` [S: `config/adm-kr/arm9/autoload_2/symbols.txt`, `func_020e9314` at `0x020e9314`; historical account: `port/shim/input/touch.c`] |
| `0x021fbdf0` | the nine-entry auto-sampling ring `gAutoData` | the ARM7 through `TPi_TpCallback` (nothing on the port) | `func_020e9314` [S: `src/matched/func_020e948c.c`] |
| `0x021f6c54` | the touch Y the keyboard's `< 0x48` compare tests -- a coordinate, not a counter | the keyboard | `func_ov126_022a1228` [H: source account: `docs/kb/port/input-save-audio.md`, KBD39; direct ROM-source provenance unresolved] |
| `0x04000280` | the hardware divider, used to precompute the calibration reciprocals | `TP_SetCalibrateParam` | itself [S: `src/matched/TP_SetCalibrateParam.c`] |

## How to check it

`../experiments/touch-latency.md` is the timing measurement -- the sampling ring, the
three-sample rule, the one frame of latency and the ordering against the VBlank handler --
with its three arms and their recipes. `../experiments/touch-calibration.md` is the coordinate
measurement above, with its recipe and its negative controls. `../experiments/two-tap-town-recipe.md` is the run every downstream touch
observation is taken under. `../experiments/off-recipe.md` is the control both are read against.

## Settled (kept for the record)

These were the Hypotheses section of this page until TOUCH41 and TOUCH42 closed them. They are
kept because the negatives cost as much as the positive.

- **Settled negative.** The one-pixel offset does not make the original refuse the second
  keyboard's confirm button. The port was re-run with the contact moved to 222,182 -- the
  coordinates the original's game actually sees -- and the taps still arrive as
  `acww touch: DOWN x=222 y=182`, four contacts, exit 100 at 27,000 frames
  [E: `scratchpad/cycle40/runs/tap-D61`, `ACWW_TOUCH_X=222 ACWW_TOUCH_Y=182`]; against
  `scratchpad/oracle/tap-220` the two sides still part
  [H: source account: `docs/log/cycle40-keyboard-gate-probe.md` ORACLE42; direct ROM-source provenance unresolved].
- **Settled positive.** The frame is the cause, and the latency is the reason the frame
  matters. Moving the tap off the KEYS3 A-press frame to 24,700 makes both sides confirm and
  agree [H: source account: `docs/log/cycle40-keyboard-gate-probe.md` ORACLE42; E: `tap-D62`;
  O: `scratchpad/oracle/tap-24700`; direct ROM-source provenance unresolved].
- **Settled positive (TOUCH41/TOUCH42).** The port should model the lag rather than have the
  recipe avoid it, and does. The ROM's own `func_020e9314` now runs on the interpreter path
  and the port fills the ARM7's ring, *after* the ROM's VBlank handler -- and the 24,600 recipe
  behaves as the original does [E: `scratchpad/cycle40/runs/tap-T42b`]
  [O: `scratchpad/oracle/tap-window`]. See `../experiments/touch-latency.md` and the Result
  section below.
- **Settled.** The reason the first tap never confirms is the mode switch, not the hit test:
  the keyboard consumes the first contact as a PAD-to-stylus mode change, and only a second
  contact inside the stylus-mode window reaches the confirm button
  [E: `docs/log/cycle40-keyboard-gate-probe.md` H4 RESULT and TAP40;
  `scratchpad/cycle40/runs/tap-native`, `tap-interp`].
- A person with the keyboard can walk out of the town hall where the scripted recipe cannot
  [E: `scratchpad/cycle40/runs/tap-D59`, 90,000 frames of talking to Pelly again].

## Hypotheses

- **The interpreted-callback anomaly.** [H] Delivering the ARM7's four samples a frame to the
  ROM's own `TPi_TpCallback` as interpreted PXI calls is data-identical to the host fill and
  yet changes the game: the taxi dialogue advances with no scripted input and both name
  keyboards type their top-left key eight times and confirm
  [E: `scratchpad/cycle40/runs/tap-T41j`, `tap-T41q8705` against `tap-T41pd`;
  S: `docs/log/cycle40-keyboard-gate-probe.md` TOUCH41; `docs/kb/hybrid/stall-playbook.md`
  case 42]. The host fill ships and `ACWW_TP_PXI=1` keeps the interpreted path for the hunt.
  Settled by running `ACWW_TP_PXI=1` with the contact DISABLED, so the four interpreted
  callbacks a frame carry only pen-up samples: if the game still races ahead, the side effect
  is in `acww_interp_irq_run` and not in the touch data --
  `../experiments/touch-latency.md`, Open.
- **Hold duration on the interpreter path.** [H] `FOR=10` and `FOR=90` at the same frame and
  coordinate produced byte-identical images at all nine sampled frames on the *native* path
  [H: log/source account: `docs/kb/port/input-save-audio.md`, TOUCH39; receipt provenance unresolved]. It has not been re-measured since the
  ROM's own publish took over. Settled by repeating that pair with `ACWW_INTERP=1`.
- **Is the oracle probe's `memory.readword` wide?** [H] The reason to doubt it is gone -- the
  255 it returned in the no-touch rows is the ROM's own 0x00ff, not a truncation of 0xffff
  [H: source account: `docs/log/cycle40-keyboard-gate-probe.md` TOUCH41; direct ROM-source provenance unresolved] -- but nothing has positively shown
  the accessor returning a value above 255. It does not matter for anything on this page,
  where every field is below 256. Settled by probing an address the ROM writes wide.


## Result (ORACLE42, after this page was drafted)

The one-pixel test is negative: the port with contacts at 222,182 still confirms the town
name (`tap-D61`, top screen black from 25,200 = the ride) and the original with contacts at
220,180 still does not (`scratchpad/oracle/tap-220`, keyboard to 27,000) [E: `tap-D61`; `scratchpad/cycle40/runs/tap-D61`]
[O: `scratchpad/oracle/tap-220`]. The frame is the cause: 24,600 is a KEYS3 A-press frame
(2400 + 37 x 600) while 8,700 is not, and the original's stylus sample reaches the game 1-2
frames after the port's, so the press and the tap are ordered differently on the two sides
[H: source account: docs/log/cycle40-keyboard-gate-probe.md ORACLE42; direct ROM-source provenance unresolved]. With `ACWW_TOUCH2_AT=24700` both
confirm and agree: 11 frames 24000..27000 at mean ncc 0.9955, top screen 1.0000
[E: `tap-D62`; `scratchpad/cycle40/runs/tap-D62`] [O: `scratchpad/oracle/tap-24700`]. The recipe of record uses 24,700.
The latency is now modelled (TOUCH41): the ROM's `func_020e9314` runs on the interpreter
path and the port fills the ARM7's ring [H: source account: `docs/log/cycle40-keyboard-gate-probe.md` TOUCH41; direct ROM-source provenance unresolved].
Under the model the contact scheduled at 24,600 reaches TP_POINT at 24,601 and the port
still confirms the town name where the original does not [E: `scratchpad/cycle40/runs/tap-T41h`]
[O: `scratchpad/oracle/tap-window`]; the 24,700 recipe scores 0.9986 over 24,000..27,000
[E: `tap-T41i`; `scratchpad/cycle40/runs/tap-T41i`] [O: `scratchpad/oracle/tap-24700`]. **Settled (TOUCH42)**: the position of the samples relative to the ROM's VBlank handler
is what orders a same-frame press and tap. With the four samples delivered after the
handler (the hardware's order: the handler reads the pad at VBlank, the ARM7 samples the
panel during the frame that follows) the port stays on the keyboard at 24,600 like the
original -- 11 frames 24,000..27,000 at ncc 0.9981 [E: `scratchpad/cycle40/runs/tap-T42b`]
[O: `scratchpad/oracle/tap-window`] [H: source account: `docs/log/cycle40-keyboard-gate-probe.md` TOUCH42; direct ROM-source provenance unresolved].

## Result (INPUT46): the scripted pad, measured against the original

The pad path had never been scored against the original the way the stylus was. It has now,
on the ROM's own words rather than on pictures: the port's region ledger
(`ACWW_ORACLE_ADDRESS=0x021fbdd0 _LENGTH=120`) and `oracle.py --peek 0x021fbdd0:1,0x021fbe38:4`
read the same 120 bytes -- the ROM's per-frame counter, `g_021fbe3c` and `g_021fbe40`'s
`{held, trigger, table}` -- through the taxi conversation on both producers under one recipe
[E: `scratchpad/input46/RECEIPTS.md`; `docs/log/cycle40-keyboard-gate-probe.md` INPUT46].

- **A held key is ONE trigger on both sides.** With `ACWW_KEYS=9 _FOR=10 _EVERY=30`, the
  ROM's `changed` word at `0x021fbe42` rises exactly once per pulse: 34 of 35 pulses on the
  port sampled EVERY FRAME, 24 of 24 on the original over the same conversation sampled every
  second frame (and 51 of 51 with the pad phases disabled, so the train never stops)
  [E: `scratchpad/input46/w-port1.txt`] [O: `scratchpad/input46/w-full.txt`].
- **The pad is read once per main-loop iteration, and that is once per THREE frames on both
  producers** -- `0x021fbdd0` advances exactly 10 per 30 frames on the port and 33 per 100 on
  the original. The game's key path is not a per-VBlank path on either machine
  [S: `func_0206e63c`'s `data_021fbdd0++`, `port/shim/gfx/frameswap.c`].
- **The port's scripted press arrives 3 frames late and is held 12 frames instead of 10.**
  `frameswap.c` writes both pad registers from the END of `func_0206e63c`, i.e. once per
  main-loop BODY, so the mask is computed on one frame and consumed on the next body; the
  original's ROM reads live hardware and sees the press at pulse start +2..+4, held 8..10
  frames. It changes no edge at a 30-frame period and it is not modelled
  [E: `scratchpad/input46/w-port1.txt` frames 780..795] [O: `scratchpad/input46/w-orig.txt` frames 1,080..1,092].
- **The taxi conversation therefore advances at the ORIGINAL's rate.** The 28 message-box
  repaints are the same events in the same order at a constant +270 frames, and the port
  covers taxi-onset to keyboard-onset in 830 frames against the original's 810 with the same
  pulse train [E: `scratchpad/input46/table.txt`; `docs/log/cycle40-keyboard-gate-probe.md` INPUT46]. **CARD45's "the port advances the taxi dialogue
  1.8x faster" is RETRACTED** (`docs/log/cycle40-keyboard-gate-probe.md`, INPUT46, "The answer in one paragraph"): the port is ~280 frames early at the taxi, so it finishes
  before `ACWW_KEYS2` stops the 30-frame train at frame 1,800, while the original is four
  events short and waits 700 frames for `ACWW_KEYS3`'s first A.

**`ACWW_PAD_SAMPLE` could not witness any of this, and has been deleted.** `port/shim/probe_pad.c`
overrides `func_020e9548` and is linked, but the interpreter enters a native body only for a
REGISTERED function and this one is not among the 85 the boot line names, so NONE of that shim
runs on an interpreter run -- measured, a run with the witness fully configured printed neither
its samples nor the shim's own capped register log. It cannot be registered by configuration
either. Read the three words out of RAM instead, with the region ledger
[H: source account: `docs/kb/hybrid/stall-playbook.md` case 71; `docs/kb/hybrid/instruments.md` section 3d; direct ROM-source provenance unresolved].

## Related

- `../experiments/touch-latency.md`, `../experiments/touch-calibration.md`,
  `../experiments/two-tap-town-recipe.md`, `../experiments/off-recipe.md`.
- `../engine/interpreter-path.md` -- the deny list that puts the ROM's own publish back on
  the hot path.
- `time-and-rtc.md` -- the frame counter every `_AT` is expressed in.
