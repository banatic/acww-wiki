# Time and the real-time clock

**Summary.** Animal Crossing is a game about the date, and the date comes from a battery-backed
clock chip that only the DS's ARM7 processor can read. The game asks for it through an
asynchronous request, converts the chip's BCD digits to numbers, stores the answer in two
globals, and compares that against the date its save was written on -- replaying every day it
missed. A second, unrelated clock, the hardware tick counter, measures short intervals in
frames rather than dates. The PC port emulates the ARM7's side of the RTC: it starts at
2005-06-15 10:00:00 and advances one second every 59.8261 frames, so game time passes while
playing and is still a pure function of the frame count.

## What happens

There are two clocks and they are not related. The RTC chip answers "what day is it"; hardware
timer 0 answers "how long since". Confusing them has already cost this project a stall and a
retracted screenshot finding.

### The RTC chip

The ARM9 cannot read the chip. `RTC_Init` zeroes the RTC work structure, brings up PXI, spins
until the ARM7's RTC channel is ready and registers `RtcCommonCallback` as the receive callback
for `PXI_FIFO_TAG_RTC` [S: `RTC_Init`, autoload_2, `src/matched/RTC_Init.c`]. Every read is then a
request: `RtcSendPxiCommand` packs a command byte into bits 8..14 of a FIFO word and sends it,
retrying while the FIFO is full [S: `RtcSendPxiCommand`, autoload_2,
`src/matched/RtcSendPxiCommand__autoload_2_0211ea98.c`]. The three read commands are 0x10 for
date-and-time, 0x11 for date and 0x12 for time
[S: `RTCi_ReadRawDateTimeAsync` / `RTCi_ReadRawDateAsync` / `RTCi_ReadRawTimeAsync`, main,
`src/matched/RTCi_ReadRawDateTimeAsync.c`].

The answer does not come back through the FIFO. The ARM7 writes the raw chip registers into
the shared system-work area at `0x027ffde8` and posts a word to say it is done;
`RtcCommonCallback` reads the bitfields from there, runs each of year, month, day, hour,
minute and second through `RtcBCD2HEX`, and writes the decoded values into the caller's
`RTCDate` / `RTCTime` buffers [S: `RtcCommonCallback`, autoload_2, `src/matched/RtcCommonCallback.c`].
`RtcBCD2HEX` validates every nibble is below 0xA and returns 0 if any is not, so a garbled read
decodes to zero rather than to nonsense [S: `RtcBCD2HEX`, autoload_2, `src/matched/RtcBCD2HEX.c`].

**The weekday is read, not computed.** `RtcCommonCallback` copies the chip's raw three-bit week
field straight into `RTCDate.week`; the NitroSDK revision that replaced this with a calculated
day-of-week is dated 2005-09-30 and postdates this ROM
[S: `RtcCommonCallback`, autoload_2, `src/matched/RtcCommonCallback.c`]. The game does not entirely
trust it: `func_0209e5b4` inspects the buffer it just filled and, if the date is year 0, month
1, day 1, forces the weekday to 6 -- 2000-01-01 was a Saturday and `RTC_WEEK_SATURDAY` is 6
[S: `func_0209e5b4`, main, quoted in `port/shim/os/rtcclock.c`].

The synchronous getters are wrappers: each calls its async partner with `RtcGetResultCallback`,
then busy-waits in `RtcWaitBusy` until the lock word clears, then returns
`rtcWork.commonResult` [S: `RTC_GetTime`, autoload_2, `src/matched/RTC_GetTime.c`;
`RtcWaitBusy`, autoload_2, `src/matched/RtcWaitBusy.c`]. Crucially **the getters never fill the
result from `rtcWork`** -- they hand the caller's own buffer down to the async layer for the
ARM7 to write into [S: `RTC_GetTimeAsync`, autoload_2, `src/matched/RTC_GetTimeAsync.c`]. That is
why a host that drops the PXI request leaves the buffer untouched rather than returning zero.

Two conversions turn a date into a number: `RTC_ConvertDateToDay` validates the fields and
accumulates a day number from a twelve-entry cumulative day-of-year table plus a leap-day bump
(the leap test is `!(year & 3)`, adequate inside 2000-2099) plus `year*365 + (year+3)/4`
[S: `RTC_ConvertDateToDay`, autoload_2, `src/matched/RTC_ConvertDateToDay.c`], and
`RTC_ConvertDateTimeToSecond` multiplies that by 86,400 and adds
`RTCi_ConvertTimeToSecond`, returning -1 if either half was invalid
[S: `RTC_ConvertDateTimeToSecond`, autoload_2, `src/matched/RTC_ConvertDateTimeToSecond.c`].

**The name in the tree is wrong and the correction is settled.** `src/matched/RTC_SetDateTime.c`
defines the 68-byte wrapper at `0x0211e7c0` and declares it calling `RTC_SetDateTimeAsync`. That
symbol is defined in no matched file and appears nowhere in the linked image; the ROM's own
branch word at `0x0211e7d0` is `bl 0x0211e804`, which is `RTC_GetDateTimeAsync`; and the three
68-byte wrappers sit immediately before their own async partners in the order NitroSDK emits
them [S: read from `extract/adm-kr/arm9/unk_autoload_2.bin` and the autoload_2 symbol table, as
recorded in `port/shim/os/rtcclock.c`]. `0x0211e7c0` is `RTC_GetDateTime`. Byte matching cannot
tell the two apart, because the harness masks call displacements -- this is defect class D12, a
name encoding a mistyped target [S: `docs/rules/D-defects.md` D12].

### The game's clock

`func_0209e49c` declares an `RTCDate` and an `RTCTime` as locals, calls `func_0209e5b4` on
them (which is `RTC_GetDateTime`), and copies the result into the game's clock globals at
`0x021dc744` (date) and `0x021dc754` (time)
[S: `func_0209e49c`, main, quoted in `port/shim/os/rtcclock.c`].

The day rollover is a catch-up loop, not an event. `func_0207b05c` fetches the current date,
compares it against the date stored in the save at `self+0x4046`, computes the difference in
days through `func_0209dcdc`, and then calls the per-day step `func_0207b268` that many times
-- so the game replays every day it missed rather than skipping to the newest one. A delta that
does not look valid takes a separate branch, the clock-tampered path
[S: `func_0207b05c`, main, `src/matched/func_0207b05c.c`]. That function is the mechanism
behind "you time travelled forward N days"; the rolled-back branch is what leads to the
game's reaction to a clock set backwards [H: the branch is identified, its destination
`func_0209a654` / `func_0209a77c` is not decompiled; settled by following that call chain].

The minute drives the lighting. `func_020bbb6c` reads the minute byte from `0x021dc758` and
scales it by 0x44445 >> 12, which is 4096/60 -- a fixed-point blend weight for the day/night
environment-light interpolation [S: `func_020bbb6c` / `func_0209def4`, main, quoted in
`port/shim/os/rtcclock.c`].

**The clock is what seeds the GAME's own random number generator, and that is what decides the
town** (ORACLE46). `func_02061530` sets the state word at `0x021cb5a0` to `func_0209dbbc()`,
which folds FOUR bytes of the globals above -- `minute | day<<8 | hour<<16 | second<<24`, from
`0x021dc758`, `0x021dc74c`, `0x021dc754` and `0x021dc75c` -- and no year, month, weekday or
tick [S: `src/matched/func_02061530.c`, `src/matched/func_0209dbbc.c`]. On the port a load
watchpoint on that block names the three reading pcs (`0x0209dbc0`, `0x0209dbc4`, `0x0209dbcc`)
at **frame 3**, seeing `0`, `0x0f`, `0x0a` -- seed `0x000a0f00` for the default instant -- and
the same census over the two town-generation windows finds them absent, so the seeding happens
once and never again on this path [E: `scratchpad/oracle46/RECEIPTS.md`, O46-1; `docs/log/cycle41-gameplay.md` ORACLE46]. **The practical
consequence: a clock arm that takes effect after the first second cannot change the seed**, and
one that changes the boot instant's minute, day, hour or second changes the whole town.

Outside the game's own clock, the RTC is an entropy source. The Wi-Fi identity generator seeds
a 16-bit LCG from the RTC date and time converted to seconds, salted with the tick counter if
one is available [S: `func_02100cbc` (`DWCi_AUTH_GetNewWiFiInfo`), autoload_2,
`src/matched/func_02100cbc.c`], and the AOSS setup RNG folds `hour<<10 + minute<<3 + second`
into its seed [S: `AOSS_Rand`, ov001, `src/matched/AOSS_Rand.c`]. **No matched `func_ov004_*`
file references the RTC at all** [S: absence across 2,886 ov004 files in `src/matched`].

### The tick

`OS_InitTick` reserves hardware timer 0, zeroes `OSi_TickCounter`, programs the timer with
prescaler 64 and its overflow interrupt enabled, and installs `OSi_CountUpTick` on the timer-0
IRQ [S: `OS_InitTick`, autoload_2, `src/matched/OS_InitTick.c`]. `OS_GetTick` composes a 64-bit
answer from the 16-bit register at `0x04000100` and the software-extended high half, with a
correction for the window in which the overflow interrupt is pending but not yet taken
[S: `OS_GetTick`, itcm, `src/matched/OS_GetTick.c`]; `OS_GetTickLo` is the bare register read
[S: `OS_GetTickLo`, itcm, `src/matched/OS_GetTickLo.c`]. The rate is the ARM9 system clock,
about 33.514 MHz, divided by 64; there is no matched `OS_TicksToSeconds.c` -- every caller
expands the SDK macro `(tick*64)/OS_SYSTEM_CLOCK` at its own site
[S: `src/matched/func_020ec5ac.c` and six `func_ov065_*` siblings].

### What the port does instead

The port drives the *registers* rather than shimming `OS_GetTick`, writing
`TICKS_PER_FRAME` = 8,728 into `0x04000100` and the counter each frame, so `OS_GetTick`,
`OS_GetTickLo`, the alarm path and the thread-sleep path all read a consistent truth
[E: `port/platform/tick.c`; the one-second wait in `func_020b5898` compares against 523,656,
which is 8,728 x 60]. This is a clock that counts frames, not wall time: a port running at half
speed sees time pass at half speed [H: host-source account from `port/platform/tick.c`; verify with a retained scripted run and frame using this page's recipe]. Before it existed, both reads
answered zero, `func_020b5898`'s state 2 computed `now - saved == 0` forever, and the Nintendo
logo screen at frame 900 was identical to frame 120 [H: host-source account from `port/platform/tick.c`; verify with a retained scripted run and frame using this page's recipe].

**The port is the ARM7 for the RTC, and the clock advances (RTC42).** On the interpreter path
the three synchronous getters are denied from the host registry, so the ROM's own SDK code runs
end to end: `RTC_GetDateTime` hands the caller's buffer to the async layer, `RtcSendPxiCommand`
posts `(0x10 << 8)` on PXI tag 5, and the port's `PXI_SendWordByFifo` answers -- it packs the
current instant into the two `RTCRawDate`/`RTCRawTime` words, writes them into the system work
at `0x027ffde8`, and delivers `command << 8 | RTC_PXI_RESULT_SUCCESS` to the receive callback
the ROM registered, so `RtcCommonCallback` does the BCD decoding
[E: `port/shim/os/pxisend.c`, `rtc_request`; run `off-rtc42-on` -- its `acww rtc` lines are harvested as `scratchpad/rtc42/rtcline-off-rtc42-on.txt`, and `scratchpad/rtc42/README.md` indexes the arm; the run directory itself stayed in RTC42's worktree -- log line
`acww rtc/arm7: command 0x10 raw date 0x03150605 time 0x00000010 -> callback`]. The reply is
delivered synchronously, inside the send, and both halves of that are forced: `RtcWaitBusy`
spins with no yield so nothing would ever advance to deliver a queued reply, and
`RTC_GetDateTimeAsync` sets the lock, the sequence, both buffers and the callback BEFORE it
sends, so an answer inside the send is safe -- the opposite of the touch panel's tag 6, where
the SDK sets `command_flg` after the send returns
[S: `src/matched/RtcWaitBusy.c`, `src/matched/RTC_GetDateTimeAsync.c`;
E: `docs/kb/hybrid/hardware-services.md`, "Tag 5"]. On the NATIVE path there is no interpreted
ROM to run, so the three getters still answer directly from the same model
[H: source/log account from `port/shim/os/rtcclock.c`; verify with a retained run using this page's recipe].

**How it advances.** One frame is 1/59.8261 s of emulated time -- 560190 cycles of the NDS's
33.513982 MHz clock, the same pair the port's frame pacer uses -- and the instant is a PURE
FUNCTION of the frame count, `boot + floor(frames * 560190 / 33513982)` seconds, with the
midnight rollover, the month lengths, the leap day and the weekday computed from there
[E: `port/shim/os/rtcclock.c`; `port/tools/test_rtc.py` calibrates fourteen cases including a
leap day, three month ends and midnight]. That keeps the two properties that were in tension:
game time passes while playing, and the same recipe run twice is still the same run, because
nothing reads wall time. It is the same trade the tick makes -- a port running at half speed
sees game time pass at half speed.

The default boot instant is 2005-06-15 10:00:00, a Wednesday, chosen because it is in-era,
carries no seasonal event, has an hour that is daytime, and has minute 0 so the lighting blend
weight STARTS exactly on a table entry [H: host-source account from `port/shim/os/rtcclock.c`; verify with a retained scripted run and frame using this page's recipe].
`ACWW_RTC_DATE=YYYYMMDD` and `ACWW_RTC_TIME=HHMMSS` move it; an out-of-range value is rejected
as a whole with one printed line rather than half-applied, and the weekday is always computed
by Sakamoto's method rather than taken from the environment. `ACWW_RTC_FREEZE=1` restores the
pre-RTC42 frozen clock exactly, for a diagnostic that needs two runs of different lengths to
see one instant [H: host-source account from `port/shim/os/rtcclock.c`; verify with a retained scripted run and frame using this page's recipe]. The clock is carried in the savestate -- the
boot instant, the freeze flag and the "instant decided" flag -- so a resumed run keeps the
clock it was snapshotted with instead of re-reading the loading shell's environment
[E: `port/platform/state.c`; `docs/kb/hybrid/savestate.md`].

The oracle pins the same boot instant, `rtcStart 2005-06-15T10:00:00Z` in the generated movie,
and DeSmuME advances its emulated chip with emulated time from there, which is why the two
agree at a frame rather than only at boot [O: `port/tools/oracle/oracle.py`, `RTC_START`;
`port/tools/oracle/README.md`].

**The number that settled it.** At frame 53,100 of the walk-out arm the original's HUD panel
reads `6/15 AM10:14` and the port's read `6/15 AM10:00`
[O: `scratchpad/oracle/walkout/orig`, `side-by-side-53100.png`;
E: `docs/log/cycle41-gameplay.md` ORACLE44 item 4]. 53,100 frames is 887 emulated seconds --
14 minutes 47 seconds -- so 10:14:47, and the port now reads what the original reads
[E: `port/tools/test_rtc.py`, case `oracle-53100`; the two zoomed HUD stills are
`scratchpad/rtc42/port-53100-bot.png` and `orig-53100-bot.png`]. That closes ORACLE44's last
open item, which had recorded the two HUDs parting at exactly this frame as the port's
deliberate non-advance [O: `scratchpad/oracle/walkout/side-by-side-53100.png`;
`docs/log/cycle41-gameplay.md` ORACLE44 item 4].

**The consequence for every retained reference, and it applies to pages other than this one.**
Frames now depend on the clock, because the minute drives `func_020bbb6c`'s day/night blend, so
**a comparison against a run taken before RTC42 must set `ACWW_RTC_FREEZE=1`** -- with the clock
running, every frame of the OFF recipe differs from the frozen build's, at unchanged mean ncc
against the oracle (0.997413 both, worst frame -0.000008)
[E: `scratchpad/rtc42/analyse.txt`; `docs/log/cycle41-gameplay.md` RTC42]. The freeze arm is
also the receipt that the PXI rewrite itself is neutral: frozen, it is 31/31 identical to the
pre-RTC42 build [E: same].

**Why a frame-driven clock and not the host's.** Before `rtcclock.c` existed the port dropped the PXI
request, so `func_0209e49c`'s locals were never written and the game's clock globals took host
stack garbage. Measured with `ACWW_WATCH=0x021dc754`, `func_0209e49c` wrote `0x001afeb8` -- a
stack address -- and then `0xb8` [H: host-source account from `port/shim/os/rtcclock.c`, `ACWW_WATCH=0x021dc754`; verify with a retained scripted run and frame using this page's recipe]. The
lighting blend weight is the low byte of that address scaled by 4096/60, so it was constant
within one executable and different between executables: 0x00000888, 0x00000955 and 0x000008cc
were logged from three builds [H: host-source account from `port/shim/os/rtcclock.c`; verify with a retained scripted run and frame using this page's recipe]. Two executables differing only by
dead code lit the world differently, which put a 20-26% pixel noise floor under every
fixed-frame screenshot comparison and forced a published finding to be retracted
[E: `port/shim/os/rtcclock.c`; M1]. A port that quietly tracked HOST time would reintroduce
exactly that class of defect one level up -- two runs of one recipe would differ because they
were started at different times of day. Driving the clock from the FRAME COUNT keeps the
determinism and gives the game its calendar back; the price is that two runs of DIFFERENT
LENGTHS are no longer at the same instant, which is a real difference rather than a noise
floor [H: host-source account from `port/shim/os/rtcclock.c`; verify with a retained scripted run and frame using this page's recipe].

## Where it lives

| function or symbol | module | role | grade/citation |
|---|---|---|---|
| `RTC_Init` | autoload_2 | zeroes the work block, registers `RtcCommonCallback` on the RTC PXI tag | [S: `src/matched/RTC_Init.c`] |
| `RtcCommonCallback` | autoload_2 | the whole state machine: decodes BCD from `0x027ffde8`, handles alarms, dispatches the result | [S: `src/matched/RtcCommonCallback.c`] |
| `RtcBCD2HEX` | autoload_2 | BCD to binary, returning 0 on any nibble above 9 | [S: `src/matched/RtcBCD2HEX.c`] |
| `RtcWaitBusy` | autoload_2 | five instructions of assembly spinning on `rtcWork.lock` | [S: `src/matched/RtcWaitBusy.c`] |
| `RtcSendPxiCommand` | autoload_2 | packs the command into bits 8..14 and sends it on the RTC tag | [S: `src/matched/RtcSendPxiCommand__autoload_2_0211ea98.c`] |
| `RTC_GetTime` `0x0211e894` | autoload_2 | sync wrapper over `RTC_GetTimeAsync` | [S: `src/matched/RTC_GetTime.c`] |
| `RTC_GetDateTimeAsync` `0x0211e804` | autoload_2 | sets sequence GET_DATETIME and both buffers, sends command 0x10 | [S: `src/matched/RTC_GetDateTimeAsync.c`] |
| `RTC_GetDateAsync` `0x0211e998`, `RTC_GetTimeAsync` `0x0211e8d8` | autoload_2 | the date-only and time-only async reads | [S: `src/matched/RTC_GetDateAsync.c`] |
| `RTC_SetDateTime` `0x0211e7c0` | autoload_2 | **misnamed**; the ROM branches to `RTC_GetDateTimeAsync`, so this is `RTC_GetDateTime` | [S: `src/matched/RTC_SetDateTime.c` vs the ROM word at `0x0211e7d0`] |
| `RTC_ConvertDateToDay`, `RTCi_ConvertTimeToSecond`, `RTC_ConvertDateTimeToSecond` | autoload_2 | date to day number, time to seconds, and the product | [S: `src/matched/RTC_ConvertDateToDay.c`] |
| `func_0209e49c` / `func_0209e5b4` | main | reads the clock into `0x021dc744` / `0x021dc754`, and forces the weekday on the default date | [S: quoted in `port/shim/os/rtcclock.c`] |
| `func_0207b05c` | main | the day catch-up: delta in days, then that many per-day steps; the tampered-clock branch | [S: `src/matched/func_0207b05c.c`] |
| `func_020bbb6c` | main | the day/night blend weight from the minute | [S: quoted in `port/shim/os/rtcclock.c`] |
| `func_ov092_02299324` | ov092 | the clock-setting overlay's dispatcher; codes 0x43 and 0x44 talk to the RTC | [S: `src/matched/func_ov092_02299324.c`] |
| `OS_GetTick`, `OS_GetTickLo` (itcm), `OS_InitTick`, `OSi_CountUpTick` (autoload_2) | itcm / autoload_2 | timer 0 at prescaler 64, extended to 64 bits in software | [S: `src/matched/OS_GetTick.c`, `src/matched/OS_InitTick.c`] |

## Data it reads and writes

| address or field | meaning | who writes | who reads |
|---|---|---|---|
| `0x027ffde8` (`OSSystemWork.real_time_clock[8]`) | the chip's raw BCD registers, mirrored | the ARM7 | `RtcCommonCallback` [S: `src/matched/RtcCommonCallback.c`] |
| `rtcWork.lock` | RTC busy flag, cleared by the callback | `RtcCommonCallback` | `RtcWaitBusy` [S: `src/matched/RtcWaitBusy.c`] |
| `rtcWork.buffer[0..1]` | pointers to the *caller's* date and time structs | the async getters | `RtcCommonCallback` [S: `src/matched/RTC_GetDateTimeAsync.c`] |
| `0x021dc744` | the game's `RTCDate` (year, month, day, week) | `func_0209e49c` | the calendar and event code [S: quoted in `port/shim/os/rtcclock.c`] |
| `0x021dc754` | the game's `RTCTime.hour` | `func_0209e49c` | the clock path [E: `ACWW_WATCH=0x021dc754`, `port/shim/os/rtcclock.c`] |
| `0x021dc758` | the game's `RTCTime.minute` | `func_0209e49c` | `func_0209def4` then `func_020bbb6c` [S: quoted in `port/shim/os/rtcclock.c`] |
| save `+0x4046` | the date the save was last written | the save path | `func_0207b05c` [S: `src/matched/func_0207b05c.c`] |
| `0x04000100` (`REG_TM0CNT_L`) | hardware timer 0's 16-bit count | the timer (the port: `acww_tick_advance`) | `OS_GetTick`, `OS_GetTickLo` [S: `src/matched/OS_GetTick.c`] |
| `OSi_TickCounter` | the software-extended high half of the tick | `OSi_CountUpTick` (the port: `acww_tick_advance`) | `OS_GetTick` [S: `src/matched/OSi_CountUpTick.c`] |

## How to check it

`python port/tools/test_rtc.py` compiles `port/shim/os/rtcclock.c` itself -- the shipped file,
not a copy -- and drives fourteen calibration cases through it: the boot instant, midnight, a
30-day and a 31-day month end, into and out of the 2004 leap day, the 2005 non-leap February,
a year end, a full year of frames, the oracle's own frame 53,100, the frozen escape, and the
afternoon bit. It decodes every packed word back with an independent transcription of the SDK's
`RtcBCD2HEX` and the `RTCRawDate`/`RTCRawTime` bitfields, and statically checks that the pacer
and the clock still divide the same second, that `pxisend.c` writes the raw block at
`0x027ffde8`, that PXI tag 5 is dispatched, and that the clock is registered in the savestate
[H: source/log account from `port/tools/test_rtc.py`; verify with a retained run using this page's recipe].

In a run, three instruments: the boot line
`acww rtc: frame-driven clock, 59.8261 frames = 1 s boot 2005-6-15 week=3 10:0:0` (or its
`FROZEN` form), the ARM7's first four answers
(`acww rtc/arm7: command 0x10 raw date ... -> callback`, which names the ARM9 callback slot as
present or absent), and `ACWW_RTC_TRACE=1` for one line per in-game minute with the frame it
turned on [E: `port/shim/os/rtcclock.c`, `port/shim/os/pxisend.c`;
`scratchpad/rtc42/rtcline-off-rtc42-on.txt`, the harvested `acww rtc` lines of run `off-rtc42-on`].

See also `../experiments/rtc-hour-sweep.md` (designed, not yet run): the same recipe at four
hours of the day, comparing the port against the oracle on the same instants.

## Hypotheses

- The lighting is a visible function of the hour, and the port and the original agree on it.
  Every measured run pins 10:00, so the day/night blend has never been exercised at more than
  one point. Settled by `../experiments/rtc-hour-sweep.md`.
- `func_0207b05c`'s tampered-clock branch is Mr. Resetti or the equivalent scolding. Settled by
  running two consecutive port sessions against one `ACWW_SAVE` file with the second session's
  `ACWW_RTC_DATE` earlier than the first's -- which needs the save store to persist first
  (`save-data.md`).
- The port's computed weekday and the chip's stored weekday agree for every date in range. The
  ROM trusts the chip's three-bit field and the port computes Sakamoto's; they cannot disagree
  on the port, but they can on the oracle, whose emulated chip supplies its own. Settled by
  reading `0x021dc744+12` in oracle probe mode on a date whose weekday is known.
- **Retired by RTC42.** "The clock never advancing is invisible to the game over a
  90,000-frame run" stood on no fault and no stall to 90,000 frames
  [E: `scratchpad/cycle40/runs/tap-D59`, LONG41], and was already contradicted by the HUD
  parting at frame 53,100. The clock now advances; the open question moved with it, below.
- The port's advancing clock and the oracle's stay in step over a long run. The two rates are
  not identical by construction: the port divides emulated frames by 33513982/560190, and
  DeSmuME advances its emulated chip with ITS emulated time from the movie's start date. A
  drift of one second per 206,000 frames would be invisible at 53,100 and visible at a day.
  Settled by comparing the HUD at two frames far apart on one arm.
- The game's own day rollover fires, and `func_0207b05c`'s catch-up runs, when the port's
  clock crosses midnight. Nothing has yet run a port arm across a midnight -- 24 hours of game
  time is 5.17 million frames, so it wants `ACWW_RTC_TIME=235900` and a short arm rather than
  a long one. Settled by that arm plus `ACWW_SAVE`, watching `0x021dc744`.

## Related

- `../experiments/rtc-hour-sweep.md` -- the designed sweep.
- `save-data.md` -- where the date the game compares against is stored.
- `rng.md` -- the RTC and the tick are the two entropy sources.
