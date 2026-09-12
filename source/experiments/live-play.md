# Live play: driving the port from a keyboard

**Status: run, 2026-09-09 (LIVE41, `fd8da4d8`), re-measured after PERF42 (`fbfc987d`), and
CARRIED THROUGH A WHOLE SESSION 2026-09-10 (LIVE42, `0687d989` plus the LIVE42 edits).**
The port is playable at a keyboard: one command launches it paced to the DS's own 59.8261 Hz,
in a 2x window, with sound, a save file that persists and the real date and time.
**LIVE42 retires LIVE41's open item.** A player can now start a new town, type their own name
and the town's at the game's own Korean keyboard, ride out of the taxi, be shown round the town
hall by Pelly, walk the town, open the map and the pockets, find their own house, finish the
arrival with Tom Nook, WRITE A SAVE, quit, and relaunch into the town they saved -- in one
session of 129,001 frames (about 36 minutes) driven entirely by real Windows messages
[E: `scratchpad/live42/RECEIPTS.md`].

**RE-RUN AS A REGRESSION CHECK 2026-09-10 (LIVE43, `4ec6dff0`, no C changed).** The same
session on the build that has the ARM7 audio driver, the fast card read, the bounded env
readers and the thread quotas: **the whole path still works and the boot is 2.3x sooner**. The
744-page flash read now costs **48 frames (0.80 s)** instead of 747 (12.5 s), so the title
screen arrives at **26 s** instead of ~59 and the name keyboard at **104 s** instead of ~160;
the whole new-town session to a written save took **23 min 20 s / 83,430 frames**. Measured
against the host clock over 190 s of town play the frame rate is **59.8254 fps** -- 0.0007 from
the NDS's own 59.8261. Sound came out of a real device in all four launches with **9,186 of
9,186 notes sounded and none dropped**; the save verifies on both banks and the relaunch takes
the continue path. Four launches, 132,000 frames, **zero** faults of any kind
[E: `scratchpad/live43/RECEIPTS.md`, `receipt.json`; `docs/log/cycle42-save.md` LIVE43].
Three live notes from it: the `ㅃ` name field does not appear if you stop pressing `Z` once the
keyboard is up (NAME42's rule, confirmed end to end); your own front door wants the **A
button**, not a held direction; and `play.py`'s real clock means the town is ASLEEP in the
evening -- `--time 113000` on the same save had a villager walk up and talk within 80 s.

**RE-RUN AGAIN AS A REGRESSION CHECK 2026-09-11 (LIVE44, `24b1a636` IRIS54, no C changed).**
The same deliverable on the build that has per-pixel windows and master brightness (FADE52),
the per-scanline iris (IRIS54), the switch-guarded sub-frame clock (TICK53/MEM54, both OFF by
default and both confirmed off here), the loader instrument and the thread quotas: **five
launches, 246,510 frames, every one exit 0, and zero `unimplemented`, `STOP status`, `fault_pc`
or queue-full lines.** The title screen now arrives at **24 s**; a saved town loads on the
continue path; the beach gives up a shell on ONE `X` press and the save file carries it; a
cherry tree shakes bare; **너굴 상점 pays 190 Bells for a 360-Bell shell and a 2,000-Bell
cherry -- 90 = base/4 and a flat 100 for the fruit**, wallet 385 -> 575; and START ->
저장하고 마치기 writes a save that verifies on both banks.

**The headline is the transition.** Walking out of a building now closes a round IRIS, measured
live from the pixels rather than from a frame-pinned capture: the lit column span walks the
DS's own fourteen steps down to `119..136`, the lit rows close with them, and the bottom
screen's mean luma reads `30.51, 24.98, 20.45, 15.73, 10.49, 6.32, 2.84, 0.62` -- IRIS54's
frame-pinned numbers to the hundredth, from an external capture of a person's own keystrokes.
Frame rate: **59.8366 fps** against the host clock over 300 s (a shorter window is quantised by
the caption and reads a tenth high), 198 windows of the port's own counter at mean 59.71 with
every dip at a scene load, and `ACWW_FRAMETIME` says the renderer draws the town in **4.2 ms**
against PERF42's 6.5-7.0 -- so the window mask costs nothing measurable. Sound: `FIRST SOUND at
frame 38`, peak 32,006, sink `dropped 0 frames`, and four of the five launches sounded every
note; the fifth dropped **19 of 22,224 for `no instrument`**, the one number worse than
LIVE43's and still unattributed [E: `scratchpad/live44/RECEIPTS.md`, `runs/*/receipt.json`;
`docs/log/cycle42-save.md` LIVE44]. Three live notes from it: the dark opening under Nook's
sign is a WINDOW and the door is the panel beside it; Redd's password keyboard draws yellow
PLACEHOLDER marks in an empty field and refuses 결정 silently until something is typed; and a
walking villager would not stand still to be talked to in nine attempts, though both
shopkeepers talk on the first `Z`.

## Purpose

Every recipe on the other pages is a SCRIPT: it pins the clock, disables the store, prints a
progress line, and runs as fast as the host manages. A person needs the opposite of all four.
This page is how to give them that without changing what any scripted run measures, and the
receipt that it does not.

## Recipe

    python port/tools/play.py

That is the whole thing [H: log/source account: `port/tools/play.py`; `docs/kb/hybrid/live-play.md`; receipt provenance unresolved]. It
launches `port/build/acww.exe` on the interpreter path with the real clock, a save at
`%LOCALAPPDATA%/acww/town.sav`, the pacer on, the interpreter's progress line off, and no console
window; the log goes beside the save. Options: `--save PATH`, `--log PATH`,
`--date YYYYMMDD --time HHMMSS`, `--state PATH` (resume a savestate -- reaching the town costs
about 80 s that way instead of a full replay), `--console`, `--verbose`, `--wait`, `--env K=V`,
and since LIVE42 `--mute`, `--wav PATH` and `--no-sink` -- **sound is ON by default now**.

**Why a launcher rather than a documented command line**: four of the environment's defaults are
right for a receipt and wrong for a player -- the RTC is pinned in every recipe, `ACWW_SAVE` is
deliberately unset, the interpreter's progress line costs 1,738,500 writes and a 101 MB log on
the 9,000-frame OFF recipe (about 20% of the frame time), and the console-subsystem exe pops a
console window when it is not launched from a terminal [H: log/source account: `docs/kb/hybrid/live-play.md`; receipt provenance unresolved].

### The key map

Printed in full, English and Korean, on the first frame of any run with no scripted keys
[H: host/prose inference from `port/platform/hostinput.c`; verify against the ROM function or symbol table and this page's recipe].

| key | DS | key | DS |
|---|---|---|---|
| arrows | D-pad | `Z` | A |
| `X` | B | `A` | Y |
| `S` | X | `Enter` / `Space` | START |
| `Backspace` / `RShift` | SELECT | `Q` / `W` | L / R |
| left mouse on the LOWER screen | the stylus (drag to stroke) | `Escape` | quit, flushing the save |

### The pacer

The port paces to the NDS's own rate -- 33.513982 MHz / 560190 cycles = **59.8261 Hz** -- with
`timeBeginPeriod(1)`, a sleep of all but the last millisecond and a yield through the remainder.
The deadline advances by exactly one period a frame, so there is no drift, and a host more than
two frames behind **re-bases instead of sprinting**, so a stall cannot become a fast-forward
[H: host-source account from `port/platform/frame.c`; verify with a retained scripted run and frame using this page's recipe].

**It is OFF by default on anything that smells scripted.** Any `ACWW_KEYS*`, `ACWW_TOUCH*` or
`ACWW_SHOT*` variable, or `ACWW_STOP_FRAME`, or `ACWW_NOPACE=1`, turns it off; the environment is
scanned once by PREFIX, so a new `ACWW_KEYS4` is covered without editing anything. `ACWW_PACE=1`
or `ACWW_NOPACE=0` forces it on for a measurement of the pacer itself
[H: log/source account: `docs/kb/hybrid/live-play.md`; receipt provenance unresolved].

## What a player does, step by step

MEASURED (LIVE42). Every input is a `PostMessageA` into the port's OWN window queue --
`WM_KEYDOWN`/`WM_KEYUP` and `WM_LBUTTONDOWN`/`WM_LBUTTONUP` -- so it takes the path a real
keyboard and mouse take: the port's wndproc, `host_vk[]` / the pen edge queue, `hostinput.c`'s
two active-low pad registers, `touch.c`'s minimum contact. **No `ACWW_KEYS*`, `ACWW_TOUCH*`,
`ACWW_SHOT*`, `ACWW_STOP_FRAME` or `ACWW_PADSCRIPT` is set anywhere**, which is what keeps the
pacer ON and the input on the live path. Pictures are `scratchpad/live42/shots/`; the driver is
`scratchpad/live42/drive.py`.

| # | what to do | what appears | frame | E |
|---|---|---|---|---|
| 1 | wait | the title screen, in DAYLIGHT -- the clock is real, where LIVE41's was at night | 3,510 | `01-title.png` |
| 2 | ONE click on the lower screen | Rover: 안녕하세요！놀러 오셨군요 | 4,290 | `02-after-title-tap.png` |
| 3 | `Z` x4 | inside the taxi | 5,100 | `03-menu.png` |
| 4 | `Z` | Rover's questions, some with a two-choice box | 7,050 | `04-taxi.png` |
| 5 | click a choice | it takes it -- the stylus works on dialogue | 8,490 | `05-after-choice-tap.png` |
| 6 | `Z` | **the name keyboard**, 당신 이름은? | 9,601 | `06-taxi2.png`, `06-lower-4x.png` |
| 7 | click ㅁ at DS(33,128), then ㅣ at DS(193,128) | the two taps compose one syllable | 12,630 | `07-typed-mi.png` |
| 8 | click backspace at DS(231,112) | the syllable is removed again | 18,090 | `08-bksp.png` |
| 9 | type the name, click 결정 at DS(220,179) | confirmed on ONE tap; Rover reads it back | 20,190 | `09-typed-mimi.png`, `10-nameline.png` |
| 10 | `Z` | **the town-name keyboard**, 마을 이름은? | 24,390 | `12-townkbd.png` |
| 11 | type it, then 결정 | 헤헷 농담이야, 농담ー！ | 27,390 | `13-townname.png`, `14-townconfirm.png` |
| 12 | `Z` | **out of the taxi**, on the paving at the town hall, sky on the top screen | 31,500 | `16-taxi4.png` |
| 13 | hold Up | inside, with 펠리 (Pelly) | 32,700 | `17-townhall.png` |
| 14 | `Z` | her map page, and the HUD reads **9/10 목 AM11:27** -- the real date and time | 34,770 | `18-pelly.png` |
| 15 | **Down then `Z`** on each question | the tour ends at 그럼 다녀 오세요！ | 50k-56k | `steps.png` |
| 16 | hold Down THROUGH the last box | **out in the town**: sky above, ground below, the map arrow top right | 61,260 | `35-escape.png` |
| 17 | `S` (the X button) | **the map**: the town, its buildings, the villagers 패치 / 핑키 / 탱크 | 62,070 | `36-map.png` |
| 18 | `A` (the Y button) | **the pockets**: portrait, name, `00000` bells, the grid, ten letter slots | 62,910 | `37-pockets.png` |
| 19 | hold an arrow for 600 frames each way | the town walks; the caption advances by exactly 600 | 90,270-91,710 | `walk-montage.png`, `walk.txt` |
| 20 | `Enter` (START) | **어머? 지금은 아직 저장하지 못하나 봐요** -- SAVE42's arrival refusal, live | 94,170 | `41-start.png` |
| 21 | walk to the GREEN house icon on the map | the player's own house, with its red mailbox | 111,210 | `43-mapbox.png`, `45-nearhouse.png` |
| 22 | slide into the front wall with `A` | inside: the 4x4 room, the bench, a figurine, a stereo | 113,910 | `47-enter.png` |
| 23 | hold Down | 너굴 (Tom Nook) at the door | 115,050 | `48-nook.png` |
| 24 | `Z` | Nook DRAWN, gesturing, giving the loan speech | 116,700 | `49-nook2.png` |
| 25 | `Z` | 그럼 나중에 가게로 날 찾아와구리 | 118,620 | `50-nook3.png` |
| 26 | `Enter` (START) | **오늘은 여기까지 하시겠습니까?** -- the refusal is gone | 120,001 | `52-savemenu.png` |
| 27 | click 저장하고 마치기 TWICE | 저장하고 있습니다 전원을 끄지 말고 그대로 기다려 주십시오！ | 123,270 | `53-zoom.png`, `54-saving.png`, `55-saved.png` |
| 28 | `Z` | the title screen again -- **showing the town you just saved**, mailbox and all | 128,401 | `58-postsave.png` |
| 29 | `Escape` | `acww save: flushed the backup store to disk`, exit 0 in 0.11 s | 129,001 | `escape-time.txt` |
| 30 | `play.py` again, same `--save` | the title screen is YOUR town | 3,510 (B) | `60-relaunch-title.png` |
| 31 | click, then `Z` | **you wake in the bed in your attic**: 이 방은 당신의 집에 있는 다락방입니다 | 6,630 (B) | `63-wake.png` |
| 32 | `Z` | outside your own front door, HUD 9/10 목 AM11:59. No taxi, neither keyboard | 11,040 (B) | `66-continued-town.png` |

Every run, paced or not, prints `acww pace: NN.NN fps over 600 frames, frame N (paced|unpaced)`
-- the honest answer to "is it slow or is it stopped" [H: source/log account from `port/platform/frame.c`; verify with a retained run using this page's recipe]. Across all
three LIVE42 sessions that line reads **59.82** on essentially every window; the exceptions are
boot (58.7, 54.6) and the loads either side of a room transition (58.3-58.4). The independent
check is step 19: holding a key for 600 frames of WALL CLOCK advanced the caption by exactly 600
frames, both directions [E: `scratchpad/live42/walk.txt`].

**The save is real.** The game wrote 256-byte pages, each VERIFIED a frame later, over
`0x00000..0x2e7f8` with 0 mismatches, and `savetool.py check` on the image reads
`checksum stored 0xaf74 computed 0xaf74 VERIFIES` and `the game would LOAD this bank`, 3 of 8
villagers occupied -- a new town [E: `scratchpad/live42/sessionA.log`; SAVE43 reached the same
chain under a pad script].

### Three things the walkthrough had to learn

**The arrival conversation restarts on its own** while the player stands at Pelly's counter: the
box closes on `A` and 어머 무슨 일 있으신가요? is back within 2.5 s with nothing pressed
[H: log/source account: `shots/32-free.png`, frame 56,310, 150 frames after the closing press; receipt provenance unresolved]. Hold the direction
you want to leave in BEFORE the last box closes and you walk away the instant control returns.
The tour also LOOPS on 혹시 지도를 어떻게 꺼내는지 잊으셨나요?, because `A` picks the first
option, which is "yes, tell me again" -- press Down first [H: log/source account: `shots/21-pelly4.png` against
`24-declined.png`; receipt provenance unresolved].

**The key grid can be measured off one capture.** Crop the lower screen out of a window capture
(client 512x768, so the lower screen is the bottom half and DS = client/2 at the default 2x),
scale it 2x again, and DS coordinates are that image's pixels over four. The rows are at
DS y = 96, 112, 128, 144, columns 20 DS pixels apart from x = 14; backspace is DS(231,112) and
결정 is DS(220,179) -- which is where `run_town.py`'s long-standing
`ACWW_TOUCH_X=221 ACWW_TOUCH_Y=181` was pointing all along [H: log/source account: `shots/06-lower-4x.png`; receipt provenance unresolved].

**Navigating by the map page works.** `scratchpad/live42/nav.py` walks with the arrows, opens
the map, and finds the player marker (B173 G90 R247) and the player's own house icon
(B0 G165 R0) by colour; 600 frames of diagonal walking moves the marker 82 map pixels, which
closed on the house in three iterations. Two traps it records: **blink detection does not
work** -- the map's river ANIMATES, so the biggest thing changing inside the map frame is water,
not the marker -- and "is the green house icon visible" is not a test for "is the map open",
because tree foliage in the town is the same pure dark green.

## Input latency, as a player feels it

MEASURED (LIVE42; full tables and method in `scratchpad/live42/LATENCY.md`).

| question | answer | E |
|---|---|---|
| until the DS's pad registers hold the key | **0.07-0.98 frames, median 0.69** -- the same frame, every trial | `lat-padpublish.txt` |
| until a PIXEL changes, key | **8.7-12.7 frames** (145-212 ms), n=6 | `lat-keys.txt`, `lat-right.txt` |
| until a PIXEL changes, click | **11.3-13.3 frames** (188-223 ms), n=6 | `lat-taps.txt`, `lat-firsttap.txt` |
| how long a click must be held | **any length**: 24/24 reached the ROM at holds from sub-frame to 400 ms | `lat-touch-sweep.txt` |
| Escape to process exit | **0.11-0.13 s**, three sessions | `escape-time.txt` |

**The port's own input path costs less than a frame** -- `acww_window_pump()` drains the queue
once a frame before the game samples, and that is the whole of it. The 9-13 frames a player
waits for the picture are the ROM's own sampling cadence and its own opening animation.
**Do not quote 12 frames as port overhead**: nothing here separates "the ROM is like this" from
"the port is slow at this", because there is no emulator differential for latency.

A normal mouse click of 50-100 ms registers reliably, and so does one shorter than a frame --
`ACWW_TOUCH_MIN_FRAMES` (4, about 67 ms) earning its keep.

**The instrument, because it will be needed again.** `PrintWindow` costs **37.0 ms** a capture,
more than two frames, and the caption's frame number only updates twice a second, so neither can
time an input. A `BitBlt` from the window's OWN DC (`GetDC(hwnd)`; the class is `CS_OWNDC` and
`acww_present` StretchBlts straight into it) costs **0.21 ms** for a 200x160 patch and returns
real pixels in a session where a BitBlt from the SCREEN DC is black [H: log/source account: `drive.py`, `FastProbe`; receipt provenance unresolved].

## Sound: a player gets it now, and on this machine it reached a device

`play.py` had never set `ACWW_SND`, which is unset in every recipe and therefore OFF, so the
launcher had been shipping a silent game [E: `scratchpad/live42/session1.log`, the abandoned
first launch]. It defaults to on now, with `--mute`, `--wav PATH` and `--no-sink`.

MEASURED: `acww snd: driver ON (ACWW_SND=1)`, `FIRST SOUND at frame 38`, 21 distinct tag-7
command ids in the census (`PREPARE_SEQ` 38, `START_PREPARED_SEQ` 38, `TRACK_PARAM` 111,
`PLAYER_PARAM` 75; only `SETUP_ALARM` is still LOGGED rather than dispatched), 43 notes
attempted and **43 sounded, 0 dropped for any reason**, max 7 simultaneous channels, and a
33.73 s WAV tee at 32,768 Hz stereo, peak 20,357, 57.7% of samples above 64
[H: log/source account: `sessionC.log`, `sessionC.wav`; receipt provenance unresolved].

**And `docs/kb/hybrid/audio.md`'s "this machine's session has no audio endpoint" is not always
true.** Session A got `GetDefaultAudioEndpoint failed, code 0x80070490` and
`waveOutGetNumDevs = 0`; sessions B and C, forty minutes later on the same machine in the same
user session, got `acww snd: sink WASAPI shared mode, 32768 Hz stereo, device buffer 6554
frames` -- the sink opened and the game played out loud [H: log/source account: `sessionA.log` against
`sessionB.log`; receipt provenance unresolved].

**The stylus finding, and it is the one thing that had to CHANGE for live play to work at all.**
The window's edge queue already guaranteed that a click shorter than a frame is not lost. But the
ROM publishes a contact only on **three consecutive good samples** ending at the newest, the ARM7
sampler writes four samples a frame and marks a pen-up sample INVALID, and the ROM's own sampler
runs from the main-loop BODY -- measured at about **once every three frames**. A one-frame contact
is therefore buried under eight to twelve invalid samples before the ROM looks. Measured live on
the title screen: a DOWN+UP inside one message pump gave `acww touch: DOWN x=128 y=96` and NO
`TP_POINT` change at all; the same click held 400 ms gave a `TP_POINT` with `trig 1` and advanced
the screen, with the ROM's publications at frames 7569, 7572, 7581, 7584 -- the three-frame
cadence, visible [H: log/source account: `docs/kb/hybrid/live-play.md`; `../systems/input-and-touch.md`;
`touch-latency.md`; receipt provenance unresolved]. A consumed contact is now held for `ACWW_TOUCH_MIN_FRAMES` frames (4, about
67 ms), far below any human click, and the same sub-frame click then reaches the ROM.

### What it costs, before and after PERF42

LIVE41's own measurement was that the port renders real game content at **30-40 fps on both
paths**, interpreted and native alike, so the interpreter was not the cause: `acww_nds2d_frame`
took 14-22 ms of a 16.71 ms frame and the game's own frame 4-6 ms
[E: `ACWW_FRAMETIME=1`, `scratchpad/liveplay/frametime/`]. **PERF42 closed that gap the same
night**: draw is 7.3 ms on the taxi and 6.2 ms on the town, unpaced 77 and 92 fps, and the paced
live run holds 59.82 Hz with the window open [H: log/source account: `docs/kb/hybrid/render-perf.md` section 5;
`../engine/graphics-pipeline.md`; receipt provenance unresolved]. LIVE41 also named the wrong renderer -- the phase report shows
the 3D rasteriser was 21.1 of the 26.5 ms, not the 2D compositor [H: log/source account: `docs/kb/hybrid/render-perf.md` section 5;
`../engine/graphics-pipeline.md`, section 3; receipt provenance unresolved].

## The receipt that scripted runs are unaffected

This is the whole reason the page can exist beside the recipes.

- The OFF recipe, frames 4,500..9,000 every 150: **31/31 SHA-256 identical** between the
  untouched `174ae9e3` build and the LIVE41 build [E: `scratchpad/liveplay/exactness-off.json`].
- A paced pad-scripted run equals its unpaced twin **31/31**
  [E: `scratchpad/liveplay/exactness-paced.json`].
- The town recipe paced against unpaced, 11 frames: **11/11 exact**, measured a link later
  [E: `scratchpad/perf42/exactness-town-paced.json`].
- Forced on with the renderer out of the way (`ACWW_HEADLESS=1`), the achieved rate is
  **59.82 fps for eight consecutive 600-frame windows**, 4,800 frames inside 0.01 of the target
  [E: `scratchpad/liveplay/paced-hl2/`].

## What would falsify it

- Reading "a human has played it" as "a human sat down and played it". Every input in the
  LIVE42 table was POSTED by a script -- `PostMessageA` into the port's own window queue. That
  is the same path a keyboard and mouse take (wndproc, `host_vk[]`, the pen edge queue, the pad
  registers) and it is why the pacer stayed on and the timings mean anything, but it is not a
  pair of hands. What is now settled is that **the game can be carried through its whole
  opening by that path**; what is still unmeasured is whether it is PLEASANT -- nobody has
  judged the feel, and the 9-13 frame input-to-picture figure is unattributed between the port
  and the ROM.
- Reading the LIVE42 walkthrough as a claim about the ORIGINAL. The `ㅃ` prefill on the name
  fields (below) is the clearest case: it is real, it reaches the save file, and NOTHING here
  says the ROM does not do it too. There is no oracle arm in this session.
- Measuring the pacer with `ACWW_HEADLESS=1` and calling it a frame rate. That arm skips the
  rasteriser altogether, so it can only ever measure the pacer; the window-open arm is the
  number a player gets.
- Reading a paced run's 58.4-59.7 fps windows as a renderer cost. On this machine those windows
  are contention (B14): the headless arm holds 59.82 in every window and the same recipe unpaced
  runs at 91.7 fps -- a frame with 10 ms of headroom does not miss a deadline unless something
  else took the core [H: log/source account: `docs/kb/hybrid/render-perf.md` section 5; receipt provenance unresolved].
- Comparing a live session against a scripted reference. `play.py` uses the REAL clock, and since
  RTC42 the clock moves every frame of the picture through the day/night blend
  [H: log/source account: `../systems/time-and-rtc.md`; receipt provenance unresolved].

## The rough edges, fixed and left

MEASURED (LIVE42). Every fix below was gated: `offgate.py --check --ref
scratchpad/offgate/33376a19/offgate.json` read **31/31 EXACT** on the untouched build, after the
`window.c` + `play.py` edits, and again after the `frame.c` edit.

| edge | what a player got | fix |
|---|---|---|
| no sound | `play.py` never set `ACWW_SND` | it does now; `--mute` restores the old behaviour |
| the window did not take focus | the game is launched from a terminal, and the terminal keeps the foreground -- so the first thing typed at a game asking for a touch went to the shell | `SetForegroundWindow` after `ShowWindow`, an optional import |
| DPI-unaware | on a 150%/200% display Windows renders the 512x768 client small and bitmap-STRETCHES it, defeating the reason `win_scale` is an integer and the blit is `COLORONCOLOR` | `SetProcessDpiAwarenessContext(PER_MONITOR_AWARE_V2)`, falling back to `SetProcessDPIAware`; both optional imports, declared in code because this link has no manifest |
| the title bar dropped the game's name | it opens as "Animal Crossing: Wild World (port)" and the first status update half a second later replaced it with "ACWW (port)" | the status caption carries the full name |
| a live session left no sound receipts | `acww_snd_report()` -- the tag-7 census, the driver counters, and the `ACWW_SND_WAV` flush -- ran only on the `ACWW_STOP_FRAME` path, and a live run by definition ends at Escape, so `ACWW_SND_WAV` wrote no file and said nothing about why | `frame.c` calls it on the window-closed path too; inert on every recipe, they all stop at a frame [H: log/source account: `sessionC.wav`, 4.4 MB, written by an Escape; receipt provenance unresolved] |

Left open:

- **Name fields come up pre-filled with `ㅃ` (U+3143), repeated** -- twelve cells for a player
  name, eight for a town name -- and what you type is appended after them. They are not a
  drawing artefact: the town typed in this session came back out of the save file as raw
  `43 31 43 31 43 31 60 be 34 bb`, that is `ㅃ ㅃ ㅃ 빠 무`, and every dialogue line that prints
  a name prints the ㅃs [H: log/source account: `shots/10-nameline.png`, `shots/17-townhall.png`, `savetool.py check`
  on the played save; receipt provenance unresolved]. The workaround is to press backspace as many times as the field is wide
  before typing. **Whether the ORIGINAL does this is not established** -- there is no oracle arm
  here, so this is an open question and not yet a defect claim. It is the most visible thing a
  new player meets.
  **ANSWERED by NAME42** (`docs/log/cycle40-keyboard-gate-probe.md`, receipts
  `scratchpad/name42/`), and the answer corrects this entry twice. It is not the port's: the
  town keyboard's name row is 0 differing pixels of 1,190 against the tap-for-tap oracle arm
  `scratchpad/oracle/tap-24700`, three frames, and the player keyboard's row differs by 24
  pixels which are all one blinking caret. **And it is not a pre-fill**: the keyboard's cursor
  starts on the top-left key, which IS `ㅃ`, and A means "press the selected key" -- so the `Z`
  presses that were advancing the taxi dialogue typed into the field once the keyboard opened.
  The field grows one `ㅃ` per A press (measured: 8 glyph-ink columns per 600-frame pulse) and
  stops at its capacity, which is **6** characters, not the twelve counted here -- `ㅃ` draws as
  two `ㅂ` boxes. The real workaround is to stop pressing A once the keyboard is up.
- **The first stylus tap after using the keyboard can land without acting.** At the save menu
  the first tap on 저장하고 마치기 only moved the cursor onto it and the second confirmed; the
  first two taps on an open page's tabs did nothing visible and the next four all answered in
  12.2-13.3 frames. It is TOUCH41's stylus-mode switch, seen live. A follow-up trial tapping
  the TOWN did not reproduce it, so it is reported as observed on menu targets, not as a rule
  [H: log/source account: `shots/54-saving.png` against `55-saved.png`; `lat-taps.txt` against `lat-firsttap.txt`; receipt provenance unresolved].
- **No window icon** (`wc.hIcon = 0`): this link has no resources and no SDK to build one with.
- **Escape quits with no confirmation.** It does flush the store, so nothing the GAME wrote is
  lost -- but everything since the last in-game save is. A confirmation needs a dialog in a
  `-nostdlib` link.
- **The window opens at `CW_USEDEFAULT`** and can land partly off-screen on a small display.

## Related

- `../systems/input-and-touch.md` -- the pad registers, the touch ring, and the port's injection
- `touch-latency.md` -- where the three-consecutive-samples rule was measured
- `savestate-resume.md` -- what `--state` resumes, and why a snapshot dies on a relink
- `../engine/graphics-pipeline.md` -- what the renderer costs and what PERF42 did to it
- `run-stability.md` -- how long a session survives, and what an exit code means
- `docs/kb/hybrid/live-play.md` -- the operational version of this page
