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
of its own object [S: `func_020a6688` / `func_020a636c`, main,
`port/shim/game/scenestate.c` header, body from `src/matched/func_020a6688.c`]. The setter is
`func_020a6688` and the getter `func_020a6684`, which is called on every step and is therefore
the one place that sees the machine tick [S: `port/shim/game/scenestate.c:30-40`]. The
observed order of states is 16, then 0, 1, 2 and upward
[E: `port/shim/game/scenestate.c` header, from the port's `acww scenest:` trace].

State 16's whole body is a single guard: it returns unless the scene id `data_020e3c80`
equals 5 [S: `port/shim/game/scenestate.c:31-34`]. A machine that sets one state and stops
therefore has a guard that never opens, and the state trace names which one
[E: same instrument].

### Scene 6's six-stage loader

Scene 6's init is `func_020b6c0c`, a staged loader that runs one stage per call and reports
"not finished" (-1) until every stage has returned non-zero — or until 40 ms of the frame have
been spent, whichever comes first [S: `func_020b6c0c`, main,
`port/shim/game/scene6init.c` header]. The stages are pointers-to-member held in a
function-local static, and the stage counter is a byte at `0x021f42f0` which `func_020a5598`
clears when the scene is entered [S: `port/shim/game/scene6init.c` header].

Stage 4 is the substage list that opens channels
[E: `port/shim/game/chanvector.c` header, narrowed by elimination on the native path].
Stage 5 runs `func_020b0b00`, a loop over resource entries that dispatches
`data_020e41ec[e->b0]` for each entry; a handler that returns zero means "not finished, come
back next frame" [S: `func_020b0b00`, main, `port/shim/game/stageloop.c` header, body from
`src/matched/func_020b0b00.c`]. Stage 6 is the only thing in the ROM that clears the
sequencer mailbox, through `func_020b5e88`
[S: `docs/kb/port/sequencer-and-modes.md`, LEGACY-NATIVE page describing the ROM's mechanism].

Scene 6's per-frame update slot is `func_020b6a7c`, and it returns immediately — doing
nothing — unless the byte at `0x021c75b8` is 2 or the byte at `0x021c75b0` is non-zero
[S: `func_020b6a7c`, main, `port/shim/gfx/pmflist.c:122-131`]. Everything downstream of the
town waits on those two bytes: the scene never changes, so the record array that walks the
full fourteen-entry town channel list is never installed
[S: `port/shim/gfx/pmflist.c:124-129`].

### The per-scene channel list

`func_020b0bbc` walks a scene's channel list: an array of two-halfword entries, with the count
in the object's second byte and a resume index passed in [S: `func_020b0bbc`, main,
`port/shim/game/chanlist.c`, body from `src/matched/func_020b0bbc.c`]. The walk is
time-bounded — it gives up after 40 ms of the frame and resumes next time — so "the table does
not contain id N" and "the walk never got that far" look identical from outside
[S: `port/shim/game/chanlist.c` header]. Scene 6 opens its channels from that table rather
than from constants: id 189, the field render object, never appears as an immediate anywhere
in the ROM [S: `port/shim/game/chanlist.c` header].

### Opening a channel: three stages

The front door is `func_0202f134`, which every scene's channel list goes through and which
spells the call with four arguments [S: `func_0202f134`, main,
`port/shim/game/chanopen.c` header]. It forwards to `func_020edbbc`, thirteen ARM
instructions that return 0 if the handler record is null, add 0x14 to it, and tail into
`func_020edc58` — never writing r2 or r3, so both pass straight through
[S: `func_020edbbc`, autoload_2, `port/shim/game/chanopen.c` header].

`func_020edc58` is 0xd8 bytes of ARM in `autoload_2` and is byte-identical to the ROM under
mwcc 1.2/base at `-O4,p` [S: `func_020edc58`, autoload_2,
`src/matched/func_020edc58.c` via `port/shim/game/chanstage.c:37-40`]. It records the channel
id in the halfword at `0x021fcfdc` and a state byte at `0x021fcfd4`, then runs three things
[S: `port/shim/game/chanstage.c:78-96`]:

1. state 1 — a pre-open hook, `func_020edc20`;
2. state 2 — `func_020edd30`, which fills a parameter block from the channel's two extra
   arguments;
3. state 3 — the channel's open handler, invoked through the handler table.

On failure it advances the state to 4 and calls the error hook `func_020edec8`; on either
exit it resets the state to 0 and the channel slot to the sentinel `0xffff`
[S: `port/shim/game/chanstage.c:89-98, 143-176`].

The "error" reading is wrong and worth carrying: the ROM does not touch r0 between the
constructor's `blx` and the `bl` to `func_020edec8`, so the value passed there IS the
constructor's return — the object — and a non-zero result means "an object was made", not "an
error" [S: `port/shim/game/chanstage.c:146-152`]. `func_020edec8` reads and writes bytes
`+0x0e` through `+0x11` of that object and queues it
[S: `port/shim/game/chanstage.c:152-156`].

### The double-indirect handler table

The table pointer is the word at `0x021fd044`
[S: `port/shim/game/chanstage.c:80`]. It is an array of handler pointers indexed by channel,
and the ROM dereferences the global's value, indexes it, and dereferences the result
AGAIN before the call — three loads after the address literal
[S: `g_handlerTable` at `0x021fd044`, autoload_2, `port/shim/game/chanstage.c:41-56, 80`].
Getting that wrong by one star reaches the record instead of the handler and calls it
[S: same header]. `func_020edc58`'s sibling `func_020ee660` walks the same table and
initialises an object against it [S: `func_020ee660`, autoload_2,
`port/shim/game/drvopen.c` header].

The table pointer is not constant across a boot. During bring-up it holds `0x020e3134`,
`main`'s own table; by the time the town's channel 0x22 opens, the ROM dispatcher
`func_020edc58` needs it to point at the scene's own table instead
[E: `docs/log/cycle40-keyboard-gate-probe.md` REG40, where an interpreter run still had
`main`'s]. On the PC port the town's channel 0x22 arrived with the table entry pointing INTO a
host function, so a blind double indirection read that function's first four bytes and
executed them [E: `docs/log/cycle40-keyboard-gate-probe.md` CHAN40, `EXECUTE at 0x50e58955`].

A lesson from fixing that is general enough to record here: an address being in the NDS
address range does not make it code — data lives there too, so a record test must come before
a code test [E: `docs/log/cycle40-keyboard-gate-probe.md` CHAN40b, where channel 0's entry
`0x020e35fc` is a record in main RAM].

### Channels seen in practice

The set of distinct handler ids passed to `func_020edbbc` IS the set of channels a boot opens,
because the first argument is the id the table is indexed by
[S: `port/shim/game/chanopen.c:40-56`]. Named ids so far: channel 1 is the title scene
[E: `port/shim/gfx/dispjoin.c` header]; channel 13 is the town's ground, whose record is at
`0x02239a2c` and whose constructor `func_ov003_0221fe10` has the acre model and texture loader
in vtable slot 0 [S: `port/shim/game/chanopen.c:41-45`]; channel 189's object has its model draw
in vtable slot 9 at `0x022382ac`, and it is the SNOWMAN rather than the field renderer the
port's shim headers still call it — the bind log names `/snowman/snowball1.nsbmd` and
`/snowman/snow_face.nsbmd` [S: `port/shim/game/chanlist.c` header, retracted by
E: `port/BOOT-STATE.md:1159-1171`]; channel 0x22 is a town channel
[E: cycle40 log, CHAN40]; channel 0xd2 is the particle system
[S: `port/shim/game/chanstage.c:6-8`]; channel 216's un-hide runs in scene 1 on hardware
[S: `port/shim/gfx/pmflist.c:290-296`].

### The mailbox and the mode byte

`0x021f69d0` is a one-slot request mailbox whose byte 0 reading `0x3f` means idle, and exactly
one function writes `0x3f` back: `func_020b5e88`, called only from scene 6's stage 6
[S: `docs/kb/port/sequencer-and-modes.md`]. Byte 0 of that mailbox is copied into the
game-mode byte `data_020e54ac` every frame by `func_020b6fd0` through `func_020b5e84`
[S: `docs/kb/port/sequencer-and-modes.md`].

The mode byte is the real gate above every scene transition: `func_020418d0` returns 0 exactly
when `func_020412a0()` is non-zero, which is true when the mode byte returned by
`func_020b65c4()` is one of 6, 12, 13, 14, 44, 45, 46, 47, 48 or 50
[S: `docs/kb/port/sequencer-and-modes.md`]. Modes 0x2c through 0x2f are the transition/fade
band — `func_020b6fd0` calls `func_020a6ef0(4)` for modes 0xc, 0xd, 0xe, 0x2e and 0x2f
[S: `docs/kb/port/sequencer-and-modes.md`]. When stage 5 aborts, stage 6 never runs, the
mailbox never clears, every later mode request is refused and the mode byte stays in the fade
band [E: `docs/kb/port/sequencer-and-modes.md`, measured on the native path at `c84db69f`].

Beside all of this sits a screen manager whose per-frame pump is `func_020a6c08`; whether
anything below it runs is decided by the current screen at `mgr+0x64` and that screen's enable
byte [S: `func_020a6c08`, main, `port/shim/game/screenpump.c` header].

### What the scene machinery looks like when it works

On the interpreter path the town's whole entry sequence — the problem the native port spent
cycles 34 to 40 on — simply did not arise, because the ROM's own code ran it
[E: `docs/log/cycle40-keyboard-gate-probe.md` TOWN40, run `scratchpad/cycle40/runs/tap-D56`].
The town's scene-6 stages 1 through 4 were observed running after overlay 5 loaded
[E: `docs/log/cycle40-keyboard-gate-probe.md` CALL40].

## Where it lives

| function or symbol | module | role | grade / citation |
|---|---|---|---|
| `func_020a636c` | main | the top-level scene machine | [S: `port/shim/game/scenestate.c` header] |
| `func_020a6688` / `func_020a6684` | main | its state setter (`self[24]`) and getter | [S: `port/shim/game/scenestate.c:19-40`] |
| `func_020b6c0c` | main | scene 6's six-stage loader, one stage per call, 40 ms budget | [S: `port/shim/game/scene6init.c` header] |
| `func_020a5598` | main | clears the stage counter on scene enter | [S: `port/shim/game/scene6init.c` header] |
| `func_020b0b00` | main | stage 5's resource-entry loop | [S: `port/shim/game/stageloop.c` header] |
| `func_020b5e88` | main | stage 6; the only writer of the mailbox's idle value | [S: `docs/kb/port/sequencer-and-modes.md`] |
| `func_020b6a7c` | main | scene 6's update slot, behind the two title-gate bytes | [S: `port/shim/gfx/pmflist.c:122-131`] |
| `func_020b0bbc` | main | the per-scene channel list walk, time-bounded | [S: `port/shim/game/chanlist.c` header] |
| `func_0202f134` | main | the channel-open front door, four arguments | [S: `port/shim/game/chanopen.c` header] |
| `func_020edbbc` | autoload_2 | thirteen instructions; null check, `+0x14`, tail call | [S: `port/shim/game/chanopen.c` header] |
| `func_020edc58` | autoload_2 | the three-stage channel open | [S: `port/shim/game/chanstage.c:37-66`] |
| `func_020edc20` / `func_020edd30` / `func_020edec8` | autoload_2 | stage 1 hook, stage 2 parameter block, the object-queueing hook | [S: `port/shim/game/chanstage.c:82-84, 143-156`] |
| `func_020ee660` | autoload_2 | walks the handler table and builds an object against it | [S: `port/shim/game/drvopen.c` header] |
| `func_020a6c08` | main | the screen manager's per-frame pump | [S: `port/shim/game/screenpump.c` header] |
| `func_ov003_0221fe10` | ov003 | channel 13's constructor; acre model/texture loader in slot 0 | [S: `port/shim/game/chanopen.c:41-45`] |

## Data it reads and writes

| address or field | meaning | who writes | who reads |
|---|---|---|---|
| `0x021fd044` | pointer to the array of channel handler pointers | bring-up (`0x020e3134`), then the scene | `func_020edc58`, `func_020ee660` [S: `port/shim/game/chanstage.c:80`] |
| `0x021fcfdc` | the channel being opened; `0xffff` is "none" | `func_020edc58` | the open sequence [S: `port/shim/game/chanstage.c:78, 89`] |
| `0x021fcfd4` | the open's stage byte, 1/2/3/4, reset to 0 | `func_020edc58` | the open sequence [S: `port/shim/game/chanstage.c:79-96`] |
| `0x021f42f0` | scene 6's stage counter | `func_020a5598` clears it on enter | `func_020b6c0c` [S: `port/shim/game/scene6init.c` header] |
| `0x021f69d0` | one-slot request mailbox; byte 0 `0x3f` = idle | `func_020b5e88` (stage 6) | `func_020b6fd0` [S: `docs/kb/port/sequencer-and-modes.md`] |
| `data_020e54ac` | the game-mode byte; 0x2c-0x2f is the fade band | `func_020b6fd0` via `func_020b5e84` | `func_020b65c4`, `func_020412a0` [S: `docs/kb/port/sequencer-and-modes.md`] |
| `data_020e3c80` | the scene id state 16 waits to see equal 5 | the scene machine | `func_020a6684` [S: `port/shim/game/scenestate.c:31-34`] |
| `0x021c75b8` / `0x021c75b0` | the two bytes scene 6's update slot is gated on | not established | `func_020b6a7c` [S: `port/shim/gfx/pmflist.c:124-131`] |
| `data_020e41ec` | stage 5's resource-kind dispatch table | static | `func_020b0b00` [S: `port/shim/game/stageloop.c:23`] |
| `0x020e3134` | `main`'s channel handler table | static | the bring-up's table pointer write [S: `port/shim/gfx/gxdirect_a.c:241`] |
| `0x02239a2c` | channel 13's handler record | static in `ov003` | `func_020edc58`'s table walk [S: `port/shim/game/chanopen.c:41-45`] |

## How to check it

Run the two-tap town recipe (`docs/kb/hybrid/recipes.md` section 3) and grep the log for the
port's channel instruments: `acww chanstage: chan <id> table entry=... *entry=...` says which
shape each channel's table entry took and whether it was handled or refused
[S: `port/shim/game/chanstage.c:130-141`]; `acww chanlist: count=... from index ...` prints
the scene's channel list [S: `port/shim/game/chanlist.c:40-48`]; `acww scenest: -> N` prints
the first forty scene-state transitions and `acww scenest: state=` samples the machine every
120 calls [S: `port/shim/game/scenestate.c:19-40`]. Those lines require `ACWW_TRACE_STATE`
where the instrument checks `acww_trace_state()` [S: `port/shim/game/chanopen.c:38`].

To tell "the channel list is short" from "the walk ran out of frame budget", compare the
printed count against the number of `acww chanstage` lines — the walk is bounded at 40 ms and
resumes on the next frame [S: `port/shim/game/chanlist.c` header].

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
- The 40 ms budget in both the channel list and the six-stage loader is the ROM's own frame
  allowance, not a debug value [H: settled by locating the constant in the ROM's literal pool
  and checking it against the NDS frame period].

## Related

- `display-objects.md` — what a channel's constructor joins, and what steps it every frame
- `overlays.md` — the overlays a scene's channels need resident
- `boot-and-entry.md` — how control reaches the scene machine
- `memory-map.md` — the `0x021fxxxx` band these globals live in
