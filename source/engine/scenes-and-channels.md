# Scenes and channels

**Summary.** Above the display-object framework sits a scene machine — a numbered state
machine whose scenes each own a list of "channels". A channel is a numbered feature (the
ground, the field renderer, the particle system, a widget) that is opened through a
three-stage sequence and dispatched through a double-indirect handler table. Scene 6, the
outdoor field scene, loads in six stages spread over as many frames as it needs, and the fifth
stage is the one that walks resource entries. A one-slot mailbox and a game-mode byte gate
every transition between scenes; when the game will not advance, those two are the first
things to read.

## What happens

### The top-level scene machine

`func_020a636c` is the game's top-level scene machine, and its state is one word at offset 24
of its own object [S: `src/matched/func_020a6688.c`; source account: `func_020a6688` / `func_020a636c`, main,
`port/shim/game/scenestate.c` header, body from `src/matched/func_020a6688.c`]. The setter is
`func_020a6688` and the getter `func_020a6684`, which is called on every step and is therefore
the one place that sees the machine tick [H: source account: `port/shim/game/scenestate.c:30-40`; direct ROM-source provenance unresolved]. The
observed order of states is 16, then 0, 1, 2 and upward
[H: host-source account from `port/shim/game/scenestate.c` header, from the port's `acww scenest:` trace; verify with a retained scripted run and frame using this page's recipe].

State 16's whole body is a single guard: it returns unless the scene id `data_020e3c80`
equals 5 [H: source account: `port/shim/game/scenestate.c:31-34`; direct ROM-source provenance unresolved]. A machine that sets one state and stops
therefore has a guard that never opens, and the state trace names which one
[H: log/source account: same instrument; receipt provenance unresolved].

### Scene 6's six-stage loader

Scene 6's init is `func_020b6c0c`, a staged loader that runs one stage per call and reports
"not finished" (-1) until every stage has returned non-zero — or until 40 ms have been spent,
whichever comes first [S: `config/adm-kr/arm9/symbols.txt` (`func_020b6c0c` at 0x020b6c0c); source account: `func_020b6c0c`, main, `port/shim/game/scene6init.c` header]. The
stages are pointers-to-member held in a function-local static, copied into RAM at `0x021f6a3c`
on the first call from six ROM statics based at `0x020e54c4`, and the stage counter is a byte
at `0x021f42f0` which `func_020a5598` clears when the scene is entered
[H: source account: `port/shim/game/scene6init.c` header; the descriptor addresses read from the extracted
ARM9 image, `docs/log/cycle41-gameplay.md` LOAD52 L52-1; direct ROM-source provenance unresolved].

**The 40 ms is the whole timing contract of the loader, and it is measured, not budgeted per
stage.** `func_020b6c0c` calls `OS_GetTick()` ONCE at entry and passes that tick to every
stage handler, which passes it down again; the test at each level is
`((OS_GetTick() - start) * 64 / 33514) > 0x28`, and because `33514` is the NDS system clock in
kHz the quotient is milliseconds and `0x28` is 40. **Nothing in the chain reads a completion
flag, a DMA bit, a VBlank count or any word the ARM7 writes** — the loader is a time-sliced
work loop, not a waiter [S: `src/matched/func_020b0b00.c`; source account: `func_020b6c0c`, `func_020b0b00`, `func_020b0ea8`,
`func_020b0bbc`, main; `src/matched/func_020b0b00.c` is byte-verified and carries the test].

Stage 4 is the substage list that opens channels
[H: host-source account from `port/shim/game/chanvector.c` header, narrowed by elimination on the native path; verify with a retained scripted run and frame using this page's recipe].
Stage 5 is `func_020b6d8c`, which tail-calls `func_020b0abc` -> `func_020b0b00`, a loop over
resource entries that dispatches `data_020e41ec[e->b0]` for each entry; a handler that returns
zero means "not finished, come back next frame" [S: `src/matched/func_020b0b00.c`; source account: `func_020b0b00`, main,
`port/shim/game/stageloop.c` header, body from `src/matched/func_020b0b00.c`]. The dispatch
table has **exactly three** entries -- `func_020b0ea8`, `func_020b0c4c` and `func_020b0bbc`,
for kinds 0, 1 and 2 -- and the fourth word at that address is string data
[H: source account: read from the extracted ARM9 image; `docs/log/cycle41-gameplay.md` LOAD52 L52-1; direct ROM-source provenance unresolved]. The loop
keeps two byte counters, which `func_020b6d8c` supplies from its own literal pool: the
**resume index** at `0x021f42dc`, so a refused call restarts where it stopped, and the word at
`0x021f42e4`, which is both the loop's per-entry flag and the kind-0/kind-2 handlers' own
sub-entry index [H: source account: read from the extracted ARM9 image; `docs/log/cycle41-gameplay.md` LOAD52 L52-1; direct ROM-source provenance unresolved]. Stage 6 is the only thing in the ROM that clears the
sequencer mailbox, through `func_020b5e88`
[H: source account: `docs/kb/port/sequencer-and-modes.md`, LEGACY-NATIVE page describing the ROM's mechanism; direct ROM-source provenance unresolved].

Scene 6's per-frame update slot is `func_020b6a7c`, and it returns immediately — doing
nothing — unless the byte at `0x021c75b8` is 2 or the byte at `0x021c75b0` is non-zero
[S: `src/matched/func_020b6a7c.c`; source account: `func_020b6a7c`, main, `port/shim/gfx/pmflist.c:122-131`]. Everything downstream of the
town waits on those two bytes: the scene never changes, so the record array that walks the
full fourteen-entry town channel list is never installed
[H: source account: `port/shim/gfx/pmflist.c:124-129`; direct ROM-source provenance unresolved].

### The per-scene channel list

`func_020b0bbc` walks a scene's channel list: an array of two-halfword entries, with the count
in the object's second byte and a resume index passed in [S: `src/matched/func_020b0bbc.c`; source account: `func_020b0bbc`, main,
`port/shim/game/chanlist.c`, body from `src/matched/func_020b0bbc.c`]. The walk is
time-bounded — it gives up after 40 ms of the frame and resumes next time — so "the table does
not contain id N" and "the walk never got that far" look identical from outside
[H: source account: `port/shim/game/chanlist.c` header; direct ROM-source provenance unresolved]. Scene 6 opens its channels from that table rather
than from constants: id 189, the field render object, never appears as an immediate anywhere
in the ROM [H: source account: `port/shim/game/chanlist.c` header; direct ROM-source provenance unresolved].

### Opening a channel: three stages

The front door is `func_0202f134`, which every scene's channel list goes through and which
spells the call with four arguments [S: `src/matched/func_0202f134.c`; source account: `func_0202f134`, main,
`port/shim/game/chanopen.c` header]. It forwards to `func_020edbbc`, thirteen ARM
instructions that return 0 if the handler record is null, add 0x14 to it, and tail into
`func_020edc58` — never writing r2 or r3, so both pass straight through
[S: `src/matched/func_020edbbc.c`, `src/matched/func_0202f134.c`, `src/matched/func_020edc58.c`; source account: `func_020edbbc`, autoload_2, `port/shim/game/chanopen.c` header].

`func_020edc58` is 0xd8 bytes of ARM in `autoload_2` and is byte-identical to the ROM under
mwcc 1.2/base at `-O4,p` [S: `src/matched/func_020edc58.c`; source account: `func_020edc58`, autoload_2,
`src/matched/func_020edc58.c` via `port/shim/game/chanstage.c:37-40`]. It records the channel
id in the halfword at `0x021fcfdc` and a state byte at `0x021fcfd4`, then runs three things
[H: source account: `port/shim/game/chanstage.c:78-96`; direct ROM-source provenance unresolved]:

1. state 1 — a pre-open hook, `func_020edc20`;
2. state 2 — `func_020edd30`, which fills a parameter block from the channel's two extra
   arguments;
3. state 3 — the channel's open handler, invoked through the handler table.

On failure it advances the state to 4 and calls the error hook `func_020edec8`; on either
exit it resets the state to 0 and the channel slot to the sentinel `0xffff`
[H: source account: `port/shim/game/chanstage.c:89-98, 143-176`; direct ROM-source provenance unresolved].

The "error" reading is wrong and worth carrying: the ROM does not touch r0 between the
constructor's `blx` and the `bl` to `func_020edec8`, so the value passed there IS the
constructor's return — the object — and a non-zero result means "an object was made", not "an
error" [H: source account: `port/shim/game/chanstage.c:146-152`; direct ROM-source provenance unresolved]. `func_020edec8` reads and writes bytes
`+0x0e` through `+0x11` of that object and queues it
[H: source account: `port/shim/game/chanstage.c:152-156`; direct ROM-source provenance unresolved].

### The double-indirect handler table

The table pointer is the word at `0x021fd044`
[H: source account: `port/shim/game/chanstage.c:80`; direct ROM-source provenance unresolved]. It is an array of handler pointers indexed by channel,
and the ROM dereferences the global's value, indexes it, and dereferences the result
AGAIN before the call — three loads after the address literal
[H: source account: `g_handlerTable` at `0x021fd044`, autoload_2, `port/shim/game/chanstage.c:41-56, 80`; direct ROM-source provenance unresolved].
Getting that wrong by one star reaches the record instead of the handler and calls it
[H: source account: `g_handlerTable` at `0x021fd044`, autoload_2, `port/shim/game/chanstage.c:41-56, 80` header; direct ROM-source provenance unresolved]. `func_020edc58`'s sibling `func_020ee660` walks the same table and
initialises an object against it [S: `src/matched/func_020edc58.c`; source account: `func_020ee660`, autoload_2,
`port/shim/game/drvopen.c` header].

The table pointer is not constant across a boot. During bring-up it holds `0x020e3134`,
`main`'s own table; by the time the town's channel 0x22 opens, the ROM dispatcher
`func_020edc58` needs it to point at the scene's own table instead
[H: log/source account: `docs/log/cycle40-keyboard-gate-probe.md` REG40, where an interpreter run still had
`main`'s; receipt provenance unresolved]. On the PC port the town's channel 0x22 arrived with the table entry pointing INTO a
host function, so a blind double indirection read that function's first four bytes and
executed them [H: log/source account: `docs/log/cycle40-keyboard-gate-probe.md` CHAN40, `EXECUTE at 0x50e58955`; receipt provenance unresolved].

A lesson from fixing that is general enough to record here: an address being in the NDS
address range does not make it code — data lives there too, so a record test must come before
a code test [H: log/source account: `docs/log/cycle40-keyboard-gate-probe.md` CHAN40b, where channel 0's entry
`0x020e35fc` is a record in main RAM; receipt provenance unresolved].

### Channels seen in practice

The set of distinct handler ids passed to `func_020edbbc` IS the set of channels a boot opens,
because the first argument is the id the table is indexed by
[H: source account: `port/shim/game/chanopen.c:40-56`; direct ROM-source provenance unresolved]. Named ids so far: channel 1 is the title scene
[H: host-source account from `port/shim/gfx/dispjoin.c` header; verify with a retained scripted run and frame using this page's recipe]; channel 13 is the town's ground, whose record is at
`0x02239a2c` and whose constructor `func_ov003_0221fe10` has the acre model and texture loader
in vtable slot 0 [H: source account: `port/shim/game/chanopen.c:41-45`; direct ROM-source provenance unresolved]; channel 189's object has its model draw
in vtable slot 9 at `0x022382ac`, and it is the SNOWMAN rather than the field renderer the
port's shim headers still call it — the bind log names `/snowman/snowball1.nsbmd` and
`/snowman/snow_face.nsbmd` [H: source account: `port/shim/game/chanlist.c` header, retracted by
H: historical measurement account: `port/BOOT-STATE.md:1159-1171`; direct ROM-source provenance unresolved]; channel 0x22 is a town channel
[H: log/source account: cycle40 log, CHAN40; receipt provenance unresolved]; channel 0xd2 is the particle system
[H: source account: `port/shim/game/chanstage.c:6-8`; direct ROM-source provenance unresolved]; channel 216's un-hide runs in scene 1 on hardware
[H: source account: `port/shim/gfx/pmflist.c:290-296`; direct ROM-source provenance unresolved].

### The mailbox and the mode byte

`0x021f69d0` is a one-slot request mailbox whose byte 0 reading `0x3f` means idle, and exactly
one function writes `0x3f` back: `func_020b5e88`, called only from scene 6's stage 6
[H: source account: `docs/kb/port/sequencer-and-modes.md`; direct ROM-source provenance unresolved]. Byte 0 of that mailbox is copied into the
game-mode byte `data_020e54ac` every frame by `func_020b6fd0` through `func_020b5e84`
[H: source account: `docs/kb/port/sequencer-and-modes.md`; direct ROM-source provenance unresolved].

The mode byte is the real gate above every scene transition: `func_020418d0` returns 0 exactly
when `func_020412a0()` is non-zero, which is true when the mode byte returned by
`func_020b65c4()` is one of 6, 12, 13, 14, 44, 45, 46, 47, 48 or 50
[H: source account: `docs/kb/port/sequencer-and-modes.md`; direct ROM-source provenance unresolved]. Modes 0x2c through 0x2f are the transition/fade
band — `func_020b6fd0` calls `func_020a6ef0(4)` for modes 0xc, 0xd, 0xe, 0x2e and 0x2f
[H: source account: `docs/kb/port/sequencer-and-modes.md`; direct ROM-source provenance unresolved]. When stage 5 aborts, stage 6 never runs, the
mailbox never clears, every later mode request is refused and the mode byte stays in the fade
band [H: log/source account: `docs/kb/port/sequencer-and-modes.md`, measured on the native path at `c84db69f`; receipt provenance unresolved].

Beside all of this sits a screen manager whose per-frame pump is `func_020a6c08`; whether
anything below it runs is decided by the current screen at `mgr+0x64` and that screen's enable
byte [S: `src/matched/func_020a6c08.c`; source account: `func_020a6c08`, main, `port/shim/game/screenpump.c` header].

### The anatomy of one transition, measured on both producers

A scene transition has two phases, and only one of them is a loader. Between the mailbox being
raised and its being cleared the game first runs a **pre-loader phase**, which is where the
picture fades out, and then the **six-stage loader**, whose progress is visible in the stage
counter `0x021f42f0`. On hardware a door transition spends about half its frames in each; on
the PC port the loader collapses into a single frame
[E: `docs/log/cycle41-gameplay.md` TRANSITION51 T51-2, T51-4, one-frame shots and peeks on both
producers over the same 93-row pad chain ; `scratchpad/transition51/RECEIPTS.md`].

| | original (DS) | PC port |
|---|---|---|
| mailbox `0x021f69d0[0]` `0x3f` -> `0x80000011` | frame 57,187 | frame 57,309 |
| pre-loader phase, fade-out inside it | **59 frames** | **63 frames** |
| the stage counter walks 1..7 | one stage per main-loop body, then stage 5 held; **59 frames** | **all seven stores in ONE frame** |
| mailbox cleared to `0x8000003f` | frame 57,305 | frame 57,372 |
| whole transition | **118 frames / 30 main-loop bodies** | **63 frames / 21 bodies** |

The pre-loader phase costs the same on both, to within four frames, so **the whole of the
difference is the loader** [E: `docs/log/cycle41-gameplay.md` TRANSITION51 T51-2, T51-4, one-frame shots and peeks on both
producers over the same 93-row pad chain ; `scratchpad/transition51/RECEIPTS.md`]. The reason is that every stage returns "finished" on its
first call on the port: the counter reaching 7 inside one frame means the loop was never told
"not finished, come back next frame", which on hardware is what stage 5's resource handlers say
**once 40 ms of the slice have been spent** — not, as TRANSITION51 wrote here, while a read is
outstanding; there is no outstanding read to wait on (LOAD52)
[H: log/source account: `ACWW_INTERP_WATCH=0x021f42f0`, six stores at pc `0x020b6ca6` in frame 57,372; the same
shape at the town-hall exit in frame 49,656; receipt provenance unresolved]. The same measurement at the town-hall exit holds
stage 5 on hardware for at least 150 frames, at **23.6 frames per main-loop body** against the
port's 2.95, and that is where the port's long-standing ~115-frame walk-out lead is made
[E: TRANSITION51 T51-4, retiring TUT45-4's "inherited from before the seam" ; `scratchpad/transition51/RECEIPTS.md`].

It is not a card-transfer wait. With the ROM-FS instrument armed, the door's loader frame
serves 7,413 read requests, 724,265 bytes and three overlay images, and the town-hall exit's
serves 35,631 requests, 1,322,272 bytes and four; at this ROM's cartridge clock those are 6.5
and 11.8 frames of bus time against 59 and 150+ measured
[E: `docs/log/cycle41-gameplay.md` LOAD52 L52-3, `ACWW_FSTRACE=1`; the clock from the header's
`MCCNT1` CT bit ; `scratchpad/load52/RECEIPTS.md`]. **TRANSITION51's "the town-hall exit loads no overlay at all" is retracted**
-- that was read off the once-per-id `acww ovl:` line, which cannot show a re-load; the
refutation survives on the corrected numbers.

**What stage 5 actually waits on is a 40 ms wall-clock BUDGET, and nothing else.** Every
return-0 path in the stage machine and in the resource loop is one test: more than `0x28`
milliseconds of `OS_GetTick` since the tick the stage machine took at entry and threaded
through every handler. There is no completion flag, no DMA-done bit, no VBlank count and no
ARM7-written word anywhere in the chain
[S: `src/matched/func_020b0b00.c`; source account: `func_020b6c0c`, `func_020b0b00`, `func_020b0ea8`, `func_020b0bbc`, main;
`src/matched/func_020b0b00.c` is byte-verified and carries the test verbatim]. The port never
says "not finished" because `port/platform/tick.c` advances the tick **once per frame by a
whole frame's worth**, so inside one call of the loader the elapsed time is exactly zero and a
40 ms budget cannot expire [E: LOAD52 L52-2 ; `scratchpad/load52/RECEIPTS.md`]. The 59 and 150+ frames are ARM9 work, sliced.

The fade itself is **not** part of the difference: it occupies the same interval on both.
~~The port simply does not draw it -- `MASTER_BRIGHT` and `BLDY` read zero on all 384
scanlines at every frame sampled, and `port/render/nds2d.c` reads `MASTER_BRIGHT` only to
print it.~~ **Retracted by FADE52**: there is no brightness ramp -- the "dim" is window 0
closing around x=127.5 in 13 steps of ~10 columns (`WIN0H` from a shadow at 0x0213fe94,
flushed by `func_02001ecc`), `MASTER_BRIGHT` is zero on both producers, and the port now
draws windows and master brightness (`wiki/engine/graphics-pipeline.md`, the window section)
[E: `scratchpad/fade52/RECEIPTS.md`; log: `docs/log/cycle41-gameplay.md` FADE52]. What the
port still lacks is the thirteen intermediate `WIN0H` values (it writes two): WINDOW53.

difference is the loader** [E: `scratchpad/fade52/RECEIPTS.md`; log: `docs/log/cycle41-gameplay.md` FADE52]. Every stage returns "finished" on its first call on the
port: the counter reaching 7 inside one frame means the loop was never told "not finished, come
back next frame"
[H: `ACWW_INTERP_WATCH=0x021f42f0`, six stores at pc `0x020b6ca6` in frame 57,372; the same
shape at the town-hall exit in frame 49,656 ; provenance unresolved]. The same measurement at the town-hall exit holds
stage 5 on hardware for at least 150 frames, at **23.6 frames per main-loop body** against the
port's 2.95, and that is where the port's long-standing ~115-frame walk-out lead is made
[E: TRANSITION51 T51-4, retiring TUT45-4's "inherited from before the seam"; current receipt locator: `scratchpad/transition51/RECEIPTS.md`].

**What makes the loop say "not finished" is a CLOCK, and this page said otherwise until
LOAD52** -- "which on hardware is what stage 5's resource handlers say while their reads are
outstanding" is RETRACTED. There is no polled word anywhere in the chain. The stage machine
takes ONE `OS_GetTick` at entry and threads it through every handler, and every "come back next
frame" return in all seven functions is the same test on it: a delta scaled by the ROM's own
`64 / 33514` -- milliseconds exactly, the NDS system clock in kHz -- compared against `0x28`,
which is **40 ms**. Stage 5 is a time-sliced work loop that gives itself forty milliseconds a
main-loop body, and the budget is tested only BETWEEN sub-entries, so a body comes out at 40 ms
plus the overshoot of whichever sub-entry crossed the line -- measured at 50.6 ms on the DS,
with two of the town-hall exit's individual sub-entries taking 551 ms and 1,036 ms by
themselves [E: LOAD52 L52-0..L52-5; `src/matched/func_020b0b00.c` carries the test verbatim; current receipt locator: `scratchpad/load52/RECEIPTS.md`].

**The port never refused because its clock had no sub-frame resolution**: it advanced once per
presented frame by a whole frame's worth, so the elapsed time inside one call was identically
zero. With `ACWW_TICK_MODEL=1` -- a clock priced from the ROM's own instruction stream -- the
budget expires, the stage counter is caught mid-walk for the first time, and the exit's loader
takes 15 frames over three main-loop bodies against the DS's 150+ and the door 12 against 59
[E: TICK53 T53-4; `docs/kb/hybrid/hardware-services.md` 4b; current receipt locator: `scratchpad/tick53/RECEIPTS.md`].

It is not a card-transfer wait, and the earlier form of that argument was wrong by ABSENCE.
The door loads three overlays and 724,265 bytes and the town-hall exit four and 1,322,272 --
TRANSITION51's "the exit loads no overlay at all" came from a report line that prints once per
overlay id, so a re-load was invisible. At this ROM's cartridge clock those are 108 ms and
197 ms, **11% and 8%** of the 59 and 150+ frames measured, so the conclusion survives on
corrected numbers [E: LOAD52 L52-3, `ACWW_FSTRACE`; the header's `MCCNT1` CT bit; current receipt locator: `scratchpad/load52/RECEIPTS.md`].

**What the town-hall exit's two long sub-entries ARE, named by a per-function step census over
one main-loop body each.** They are different subsystems, and neither is a wait. The first
(`*flag` 3 -> 4) is a **TOWN TILE SCAN**: one call of an ov003 driver walks the acre grid and
tests every tile's kind, `acre_x * acre_y * 16 * 16` iterations, 6 x 6 acres = **9,216**, and
63% of the body's interpreted instructions are that walk and the two ITCM lookups under it.
The second (`*flag` 4 -> 10) is the **ROM-FS NAME WALK**: `FSi_ReadTable`, `FSi_ReadDirCommand`
and `FSi_ReadRomCallback`, 2,556 table reads in one body, which is the same 2,556 the cartridge
census counts. The bound of the first is a pair of STATIC words, not a computed size --
`(*0x021c80bc)[+4]` and `[+8]`, and `--peek` reads that pointer at `0x02395444` with the same
two words, **6 and 6, on the ORIGINAL as well**, in the same town. **Both producers therefore
run all 9,216 iterations**, which retracts three cycles of "the missing time is work the port
does not perform": everything the port skips there prices at 14% of the DS's 551 ms
[E: CENSUS56, `ACWW_INTERP_CENSUS` + `--peek`; `docs/log/cycle41-gameplay.md` CENSUS56 C56-4/5].

**WHICH sub-entry the scan is, and what the long ones are, CORRECTED on the DS side.** An
execution sampler on the emulator (`--exec`, one entry count per frame) puts the leaf
`func_02031478`'s 9,216 entries in frames 49,683..49,686 — the `*flag` **2 -> 3** span, **4
frames = 67 ms** — and finds **zero** of them in the 33-frame `*flag` 3 -> 4 span the census
was matched to. The tile scan is therefore not the expensive sub-entry on the DS at all, and
the port's 1.43 M instructions for it are the right size for a 4-frame job, not 20x too fast.
What the 33 frames hold is 8,898 `CARDi_ReadRom` round trips and 11,740 `FSi_ReadTable` calls
with one `OS_SleepThread` per read — and the ARM9 **never idles**: `OS_Halt` runs 6.0 times a
frame there against 68.9 in the town play immediately before the loader. The whole of stage 5
is 30,957 card reads in 1,905 ms, **4,126 ARM9 cycles a read**, against LOAD52's own
`ACWW_FSTRACE` count of 35,631 requests. The transition is a per-REQUEST cartridge cost, not a
per-byte one; "it is not a card-transfer wait" was right about the bytes and was the wrong
question [E: `docs/log/cycle41-gameplay.md` ISSUE57 I57-0/I57-3/I57-6 ;
`scratchpad/issue57/spans-exit.txt`].

The door's stage 5 is a THIRD shape over the same machinery -- no tile scan at all (the tile
lookup runs 1,332 times, not 9,216) and one 150,240-instruction call of `func_020723a8` at its
head -- which is why a term ranked at one door does not transfer to the other
[E: CENSUS56 C56-3].

(The fade paragraph that stood here is superseded: see the FADE52 retraction above -- the
"dim" is window 0 closing, not a brightness ramp.)

### What the scene machinery looks like when it works

On the interpreter path the town's whole entry sequence — the problem the native port spent
cycles 34 to 40 on — simply did not arise, because the ROM's own code ran it
[E: `docs/log/cycle40-keyboard-gate-probe.md` TOWN40, run `scratchpad/cycle40/runs/tap-D56`].
The town's scene-6 stages 1 through 4 were observed running after overlay 5 loaded
[H: log/source account: `docs/log/cycle40-keyboard-gate-probe.md` CALL40; receipt provenance unresolved].

## Where it lives

| function or symbol | module | role | grade / citation |
|---|---|---|---|
| `func_020a636c` | main | the top-level scene machine | [S: `src/matched/func_020a636c.c`; source account: `port/shim/game/scenestate.c` header] |
| `func_020a6688` / `func_020a6684` | main | its state setter (`self[24]`) and getter | [S: `src/matched/func_020a6688.c`, `src/matched/func_020a6684.c`; source account: `port/shim/game/scenestate.c:19-40`] |
| `func_020b6c0c` | main | scene 6's six-stage loader, one stage per call, 40 ms budget | [S: `config/adm-kr/arm9/symbols.txt` (`func_020b6c0c` at 0x020b6c0c); source account: `port/shim/game/scene6init.c` header] |
| `func_020a5598` | main | clears the stage counter on scene enter | [S: `src/matched/func_020a5598.c`; source account: `port/shim/game/scene6init.c` header] |
| `func_020b0b00` | main | stage 5's resource-entry loop | [S: `src/matched/func_020b0b00.c`; source account: `port/shim/game/stageloop.c` header] |
| `func_020b5e88` | main | stage 6; the only writer of the mailbox's idle value | [S: `src/matched/func_020b5e88.c`; source account: `docs/kb/port/sequencer-and-modes.md`] |
| `func_020b6a7c` | main | scene 6's update slot, behind the two title-gate bytes | [S: `src/matched/func_020b6a7c.c`; source account: `port/shim/gfx/pmflist.c:122-131`] |
| `func_020b0bbc` | main | the per-scene channel list walk, time-bounded | [S: `src/matched/func_020b0bbc.c`; source account: `port/shim/game/chanlist.c` header] |
| `func_0202f134` | main | the channel-open front door, four arguments | [S: `src/matched/func_0202f134.c`; source account: `port/shim/game/chanopen.c` header] |
| `func_020edbbc` | autoload_2 | thirteen instructions; null check, `+0x14`, tail call | [S: `src/matched/func_020edbbc.c`; source account: `port/shim/game/chanopen.c` header] |
| `func_020edc58` | autoload_2 | the three-stage channel open | [S: `src/matched/func_020edc58.c`; source account: `port/shim/game/chanstage.c:37-66`] |
| `func_020edc20` / `func_020edd30` / `func_020edec8` | autoload_2 | stage 1 hook, stage 2 parameter block, the object-queueing hook | [S: `src/matched/func_020edc20.c`, `src/matched/func_020edd30.c`, `src/matched/func_020edec8.c`; source account: `port/shim/game/chanstage.c:82-84, 143-156`] |
| `func_020ee660` | autoload_2 | walks the handler table and builds an object against it | [S: `config/adm-kr/arm9/autoload_2/symbols.txt` (`func_020ee660` at 0x020ee660); source account: `port/shim/game/drvopen.c` header] |
| `func_020a6c08` | main | the screen manager's per-frame pump | [S: `src/matched/func_020a6c08.c`; source account: `port/shim/game/screenpump.c` header] |
| `func_ov003_0221fe10` | ov003 | channel 13's constructor; acre model/texture loader in slot 0 | [S: `src/matched/func_ov003_0221fe10.c`; source account: `port/shim/game/chanopen.c:41-45`] |

## Data it reads and writes

| address or field | meaning | who writes | who reads |
|---|---|---|---|
| `0x021fd044` | pointer to the array of channel handler pointers | bring-up (`0x020e3134`), then the scene | `func_020edc58`, `func_020ee660` [S: `src/matched/func_020edc58.c`; source account: `port/shim/game/chanstage.c:80`] |
| `0x021fcfdc` | the channel being opened; `0xffff` is "none" | `func_020edc58` | the open sequence [S: `src/matched/func_020edc58.c`; source account: `port/shim/game/chanstage.c:78, 89`] |
| `0x021fcfd4` | the open's stage byte, 1/2/3/4, reset to 0 | `func_020edc58` | the open sequence [S: `src/matched/func_020edc58.c`; source account: `port/shim/game/chanstage.c:79-96`] |
| `0x021f42f0` | scene 6's stage counter | `func_020a5598` clears it on enter | `func_020b6c0c` [S: `src/matched/func_020a5598.c`; source account: `port/shim/game/scene6init.c` header] |
| `0x021f69d0` | one-slot request mailbox; byte 0 `0x3f` = idle | `func_020b5e88` (stage 6) | `func_020b6fd0` [S: `src/matched/func_020b5e88.c`, `src/matched/func_020b6fd0.c`; source account: `docs/kb/port/sequencer-and-modes.md`] |
| `data_020e54ac` | the game-mode byte; 0x2c-0x2f is the fade band | `func_020b6fd0` via `func_020b5e84` | `func_020b65c4`, `func_020412a0` [S: `src/matched/func_020b6fd0.c`, `src/matched/func_020b5e84.c`, `src/matched/func_020b65c4.c`, `src/matched/func_020412a0.c`; source account: `docs/kb/port/sequencer-and-modes.md`] |
| `data_020e3c80` | the scene id state 16 waits to see equal 5 | the scene machine | `func_020a6684` [S: `src/matched/func_020a6684.c`; source account: `port/shim/game/scenestate.c:31-34`] |
| `0x021c75b8` / `0x021c75b0` | the two bytes scene 6's update slot is gated on | not established | `func_020b6a7c` [S: `src/matched/func_020b6a7c.c`; source account: `port/shim/gfx/pmflist.c:124-131`] |
| `data_020e41ec` | stage 5's resource-kind dispatch table | static | `func_020b0b00` [S: `src/matched/func_020b0b00.c`; source account: `port/shim/game/stageloop.c:23`] |
| `0x020e3134` | `main`'s channel handler table | static | the bring-up's table pointer write [S: `config/adm-kr/arm9/symbols.txt` (`main` at 0x02000c38); source account: `port/shim/gfx/gxdirect_a.c:241`] |
| `0x02239a2c` | channel 13's handler record | static in `ov003` | `func_020edc58`'s table walk [S: `src/matched/func_020edc58.c`; source account: `port/shim/game/chanopen.c:41-45`] |

## How to check it

Run the two-tap town recipe (`docs/kb/hybrid/recipes.md` section 3) and grep the log for the
port's channel instruments: `acww chanstage: chan <id> table entry=... *entry=...` says which
shape each channel's table entry took and whether it was handled or refused
[H: source account: `port/shim/game/chanstage.c:130-141`; direct ROM-source provenance unresolved]; `acww chanlist: count=... from index ...` prints
the scene's channel list [H: source account: `port/shim/game/chanlist.c:40-48`; direct ROM-source provenance unresolved]; `acww scenest: -> N` prints
the first forty scene-state transitions and `acww scenest: state=` samples the machine every
120 calls [H: source account: `port/shim/game/scenestate.c:19-40`; direct ROM-source provenance unresolved]. Those lines require `ACWW_TRACE_STATE`
where the instrument checks `acww_trace_state()` [H: source account: `port/shim/game/chanopen.c:38`; direct ROM-source provenance unresolved].

To tell "the channel list is short" from "the walk ran out of frame budget", compare the
printed count against the number of `acww chanstage` lines — the walk is bounded at 40 ms and
resumes on the next frame [H: host/prose inference from `port/shim/game/chanlist.c` header; verify against the ROM function or symbol table and this page's recipe].

## Hypotheses

- The two bytes at `0x021c75b8` and `0x021c75b0` are written by the scene-entry path rather
  than by a channel handler [H: settled by a store watchpoint on both
  (`ACWW_INTERP_WATCH=<hex>`) across the title-to-town transition].
- The scene's own handler table — the one `0x021fd044` must point at before channel 0x22 opens
  — is installed by scene 6's stage 4 [H: settled by watching `0x021fd044` and correlating the
  change frame with the `acww chanstage` line for the first town channel].
- Channel ids are stable across scenes (id 13 always means the ground) rather than per-scene
  indices [H: settled by logging every distinct id and its resolved handler record across two
  different scenes and comparing].
- ~~The 40 ms budget in both the channel list and the six-stage loader is the ROM's own frame
  allowance, not a debug value.~~ Settled by LOAD52: the constant is `0x28` milliseconds
  against `OS_GetTick` scaled by 33514 kHz, tested in `func_020b0b00` and `func_020b6c0c`
  (32 word-aligned occurrences of 33514 in the ROM enumerate the budget family)
  [S: `src/matched/func_020b0b00.c`; log: `docs/log/cycle41-gameplay.md` L52-2]. What is
  still open is only WHY 40 (a design allowance below one 16.7 ms frame times two and a
  half; not a debug value, since the family is release code) [H].

## Related

- `display-objects.md` — what a channel's constructor joins, and what steps it every frame
- `overlays.md` — the overlays a scene's channels need resident
- `boot-and-entry.md` — how control reaches the scene machine
- `memory-map.md` — the `0x021fxxxx` band these globals live in

## The post-loader black hold: four updates, then the kind-2 iris

At the shared-town villager-1 door, the port's 57,372..57,432 black interval is
not a measured counter loaded with 60. It consists of a four-update delay and
the kind-2 iris progression/cleanup, all on the main-loop schedule
[E: `scratchpad/handoff/black-hold-1/mechanism.json`, `original-comparison.json`; current receipt locator: `scratchpad/handoff/black-hold-1/original-comparison.json`].

| word or byte | measured role | receipt |
|---|---|---|
| `0x021f42e0` byte | set to 4 at 57,372; decremented to 0 at 57,384 | [E: `scratchpad/handoff/black-hold-1/delay-summary.json`] |
| `0x021c75b8` / `+1` bytes | fade state / kind; 1 / 2 at 57,384, 2 / 2 at 57,432 | [E: `scratchpad/handoff/black-hold-1/fade-summary.json`] |
| `0x021c75bc` word | progress 4096 to 0, in sixteen -273/clamp updates, zero at 57,429 | [E: `scratchpad/handoff/black-hold-1/fade-summary.json`] |
| `0x021c75c0` word | signed step -273, cleared when progress reaches zero | [E: `scratchpad/handoff/black-hold-1/fade-summary.json`] |
| `0x021fbdd0` word | main-loop count 19,059 to 19,079 over 57,372..57,432 | [E: `scratchpad/handoff/black-hold-1/progress-summary.json`] |

The ending writer is `func_02001ba4`, PC `0x02001baa`, LR `0x02041f2b`,
storing byte 0 to window mask `0x0213fe8c` at 57,432. Its caller is cleanup
`func_02041f20`, which also clears the subengine window mask and BG2 plane bits.
The lower screen changes from entirely black at 57,431 to house interior at
57,432 (mean luma 84.02095) [E: `scratchpad/handoff/black-hold-1/door-summary.json`,
`fade-summary.json`, `door-pictures.json`; current receipt locator: `scratchpad/handoff/black-hold-1/fade-summary.json`, `scratchpad/handoff/black-hold-1/door-pictures.json`].

The native registered `func_0206e63c` calls `func_02054070`, then
`func_02041c28` / `func_020e88dc` advance the progress before the loop counter
increments. Consequently, an interpreted store watch observes initialization
and cleanup but cannot observe those native progress stores; its silence is
not a stopped timer [S: main, `port/shim/gfx/frameswap.c`,
`src/matched/func_02054070.c`, `port/build/shadow/func_02041c28.c`]
[E: `scratchpad/handoff/black-hold-1/source-evidence.json`, `progress-values-summary.json`; current receipt locator: `scratchpad/handoff/black-hold-1/progress-values-summary.json`].

The original runs the same kind-2 fade and the same sixteen progress values,
but draws an expanding circular iris from 57,315 while it is still progressing.
Its fade begins at 57,311 and cleans up at 57,359: the same 48-frame phase as
the port. The whole post-clear interval is **54**, not 60, because its delay
byte is already 2 when the mailbox clears at 57,305; the port's is 4. That
six-frame scheduling residual remains separate from the missing visible iris
[O: `scratchpad/handoff/black-hold-1/original-summary.json`, `original-pictures.json`]
[E: `scratchpad/handoff/black-hold-1/original-comparison.json`].

A bounded follow-up is the HBlank guard, not an assumed MASTER_BRIGHT ramp:
the live reader at PC `0x0204216e` belongs to `func_02042154`, whose WIN0H
stores require DISPSTAT bit 1. The port's synthesized `dispstat_load` always
clears that bit; `scanline_hook` sets the line number but supplies no HBlank
phase. (That was the pre-IRIS54 artefact this appendix was measured against: IRIS54 raised
the flag around the scanline hook, and the iris is now drawn per line -- see
`wiki/engine/graphics-pipeline.md`, "The port reproduces this".) At 57,400..57,402, the only observed main WIN0H stores are `0x8080`
from `func_02042120` (PC `0x02042128`). No fix was applied or counterfactual
run made. RWATCH reports the backing word before the I/O hook, so its value
must not be cited as the synthesized return [S: main,
`src/matched/func_02042154.c`, `port/interp/interp_boot.c`,
`port/interp/interp_cpu.c`]
[E: `scratchpad/handoff/black-hold-1/guard-summary.json`].
