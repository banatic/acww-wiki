# Player

**Summary.** A save holds four player slots of `0x249c` bytes each, laid out end to end near
the top of the save image. Each slot carries a 64-bit event bitfield that the game uses as its
own progress record -- the opening sequence, for instance, is one bit in it. The player's name
is typed at the first keyboard screen; the game asks for it before the taxi ride, and asks for
the town's name later. In play, the player object turns one frame of pad and stylus input into
a movement intent -- speed, direction, running flag, a target position and an input mode -- and
the rest of the update consumes that block rather than the raw input.

## What happens

The player array begins at save `+0x14` = `0x021dc7bc` with stride `0x249c`, so player 0's
event words are at `+0x23f8` of the slot = `0x021debb4`
[S: func_02098844, main, port/shim/game/newgameprobe.c]. Four player slots are initialised by
`func_0209ef7c` on the new-save path [S: func_0209ef7c, main, port/shim/game/newgameprobe.c].
The active player is returned by `func_020984e8`
[S: func_020984e8, main, port/shim/game/spnpc.c].

The 64 bits at `player + 0x23f8` are the game's event flags. `func_02099020(player, bit)`
tests one and `func_02098ff8(player, bit)` sets one
[S: func_02099020 / func_02098ff8, main, port/shim/game/spnpc.c]. Flag 1 is the opening's own
state bit: it is set for the whole arrival sequence and cleared when it ends, and the only two
places in the matched tree that clear it are `func_ov050_02262628` (Nook's side) and
`func_ov068_0226e948` [H: source account: ov050/ov068, port/shim/game/spnpc.c; direct ROM-source provenance unresolved]. While it is set, every one of
the eleven predicates in the special-NPC decider table at `0x020e1d08` bails, so the whole
special-NPC schedule is silent BY DESIGN during the opening
[S: func_02084af0, main, port/shim/game/spnpc.c].

Only four functions write that bitfield, and each does the same three operations --
`set(1); set(0x23); clear(9)`: `func_0209ee54` (index 0), `func_0209ed90` (1),
`func_0209eac8` (5) and `func_0209ea24` (6)
[S: main, port/shim/game/newgameprobe.c]. Which one runs is chosen by `func_ov051_022610d4`
from the boot-mode word at `0x021f3c30`: 1 selects index 0, 2 selects index 1, and 3 selects
index 6 [S: func_ov051_022610d4, ov051, port/shim/game/newgameprobe.c]. `func_020a1320` is
the only setter of that word to 1 [S: func_020a1320, main, port/shim/game/newgameprobe.c].
This is why a save can be generated -- terrain and all -- with a still-zero player bitfield:
generation (`func_0209ebec`) deliberately writes no player state, because no player exists
yet [S: func_0209ebec, main, port/shim/game/newgameprobe.c].

The player's name is asked for first, before the ride. The prompt on screen is
`당신 이름은?`, and on the reference run the name is confirmed at about frame 7,500, after
which the game unloads an overlay
[E: docs/log/cycle40-keyboard-gate-probe.md OVL40/TOUCH40, `tap-D55`; `scratchpad/cycle40/runs/tap-D55`]. The keyboard consumes
the FIRST stylus tap as a PAD-to-stylus mode switch, so a single tap never confirms; two taps
inside the window do [E: docs/log/cycle40-keyboard-gate-probe.md TAP40, `tap-D55`; `scratchpad/cycle40/runs/tap-D55`]
[H: host/prose inference from port/shim/input/touch.c; verify against the ROM function or symbol table and this page's recipe]. The same behaviour was reproduced on the DeSmuME reference for
the first keyboard, which is what settled that the port was not wrong about it
[O: docs/log/cycle40-keyboard-gate-probe.md ORACLE41, `scratchpad/oracle/tap-fullpad`
frames 6000-24000, bottom-screen ncc 0.9997-1.0000].

Movement is built once per frame by `func_0200dc98` (`0x794` bytes in `main`, Thumb,
unmatched), which reads the pad words at `0x021fbe40` and the touch-drag helpers
`func_020b755c` / `func_020b758c` and writes a block of intent at `self + 0x134`..`0x170`
[S: func_0200dc98, main, port/shim/c6a_0200dc98_intent.c]. The fields, read off the
function's own pool and data flow, are: `+0x134` walk speed as `fx12` clamped to
`[0, 0x1000]`; `+0x138` walk direction as an `s16` angle, from `func_020e8ed8(dx, dz)` or the
pad's own direction halfword at `0x021fbe44`; `+0x13a` a running flag, set when speed exceeds
`0xc32` or B/X/Y is held; `+0x13c` a tap target from `func_020b7524`; `+0x144` a one-or-two
tap class; `+0x16d` a touch code; `+0x14c` and `+0x158` two three-word positions (remembered
and resolved target); and `+0x170` the input mode, 1 for pad and 2 for touch, with the entry
value preserved when neither claims the frame
[S: func_0200dc98, main, port/shim/c6a_0200dc98_intent.c]. Touch classification is an 18-way
switch decoded from the halfword offset table at `0x0200ddd8`
[S: func_0200dc98, main, port/shim/c6a_0200dc98_intent.c].

**The stylus walk speed is a curve with a dead zone, and its three constants are in the
function's own pool.** On the touch branch the drag length comes from `func_020ea9c8` (the
horizontal x/z distance helper), is scaled by `FX_MulFunc(d, 0x4f4)` -- `1268/4096`, about
`0.31` -- and then splits three ways: at or above `0x1000` the scaled length IS the speed; at
or below `0x19a` the speed is **zero**, which is the dead zone a small drag falls into; and
between them the speed is `FX_Sqrt((d + 0x39a) * 4096 / 0x139a)` raised to the fourth by three
`FX_MulFunc`s, clamped back into `[0, 0x1000]` and stored at `+0x134`. The `0xc32` running
threshold above is tested on that same result, so a drag can walk without running
[S: func_0200dc98 at `0x0200e1bc`..`0x0200e21a`, main, disassembly with the pool words resolved;
O: docs/log/cycle41-gameplay.md SQRT56 S56-1].

**Leaving a building does not read a door table: it replays the position the player was
standing on when they walked IN.** The outside position is kept in a pending-destination record
at `0x021f69b8` (a `VecFx32` at `+0x00`, then a kind word); `func_020b5ea0` publishes into it
through `func_020b64f0`, and `func_020b6518` installs the default `{0x30000, 0, 0x30000}` before
any door has been used [S: `src/matched/func_020b5ea0.c`, `func_020b64f0.c`, `func_020b6518.c`].
On the exit, `func_020b6098` asks `func_020b6140` for the destination; `func_020b6214` reaches
the same record for an element of kind `0x3c` and hands back its vector, and `func_020b63f4`
copies it into the scene-request record at `0x021f69d4`/`+8`/`+0xc`, refusing unless the
request slot is idle [S: `src/matched/func_020b6098.c`, `func_020b6140.c`, `func_020b6214.c`,
`func_020b63f4.c`]. The live vector at `0x021c749c` only follows: `func_0203c76c` copies it into
the camera target through `func_0203f684` every third frame
[S: `src/matched/func_0203c76c.c`, `func_0203f684.c`]. MEASURED on a scripted arrival: the
record takes the door's value at frame 38,838, eighty-one frames after the player reached the
doormat tile, and the exit at frame 49,593 posts that same word -- 10,755 frames and a savestate
later [E: `docs/log/cycle41-gameplay.md` EXIT48 X48-3, runs `x48-p-originz`, `x48-p-seqwatch`; `scratchpad/exit48/runs/x48-p-originz`, `scratchpad/exit48/runs/x48-p-seqwatch`].
So a building exit is a REPLAY, and the tile it lands on is a property of the town the player
walked through, not of the building.

That block is load-bearing rather than advisory: with the function stubbed to return 0 the run
faults shortly afterwards inside `func_0200d900`
[H: host-source account from port/shim/c6a_0200dc98_intent.c, `ACWW_EXPLORE=1` run; verify with a retained scripted run and frame using this page's recipe].

Player houses are a separate asset family from villager houses:
`/str/plHsTex/home%c%c.nsbtx` is ov003's own spelling
[H: source account: ov003 pool words, docs/kb/modules/ov003-068.md; direct ROM-source provenance unresolved].

The DS firmware's user settings supply a nickname and a birthday that the game reads. The
firmware record's `birthMonth` is at `+0x03` and `birthDay` at `+0x04`
[H: host/prose inference from port/shim/boot/usersettings.c; verify against the ROM function or symbol table and this page's recipe]. The port supplies its own values -- nickname `PLAYER`,
birthday 1 January -- and says so, because those are port choices rather than recoveries, and
the nickname IS shown in game [H: host/prose inference from port/shim/boot/usersettings.c; verify against the ROM function or symbol table and this page's recipe].

## Where it lives

| function or symbol | module | role | grade/citation |
|---|---|---|---|
| `func_020984e8` | main | returns the active player object | S: port/shim/game/spnpc.c |
| `func_02098844` | main | player slot stride `0x249c` | S: port/shim/game/newgameprobe.c |
| `func_02099020` | main | test event flag `n` of the player's 64-bit field | S: port/shim/game/spnpc.c |
| `func_02098ff8` | main | set event flag `n` | S: port/shim/game/spnpc.c |
| `func_0209ee54` / `_ed90` / `_eac8` / `_ea24` | main | the four new-game player commits | S: port/shim/game/newgameprobe.c |
| `func_ov051_022610d4` | ov051 | picks which commit runs, from `0x021f3c30` | S: port/shim/game/newgameprobe.c |
| `func_0200dc98` | main | movement-intent builder | S: port/shim/c6a_0200dc98_intent.c |
| `func_020b755c` / `func_020b758c` | main | touch-drag classification feeding the intent | S: port/shim/c6a_0200dc98_intent.c |
| `func_020e8ed8` | autoload_2 | `atan2` over the sine table, gives the walk angle | S: port/shim/c6a_0200dc98_intent.c |
| `func_02099020` callers in `0x020e1d08` | main | eleven special-NPC predicates gated on flag 1 | S: port/shim/game/spnpc.c |
| `func_ov096_0229e3b0` | ov096 | **the EQUIP dispatcher**: `(page, slot_kind, item_id)`, one case per wearable slot, storing the new id and returning the old one | S: `src/matched/func_ov096_0229e3b0.c`; E: GAMEPLAY47 `g47-WEARW` |
| `func_02099704` / `func_02099710` | main | write / address the worn shirt at slot `+0x2408` | S: those two functions; E: a store watchpoint on `0x021debc4` catching the wear-drop |
| `func_02098f0c` / `func_02098f48` / `func_02098f70` | main | set / address / bounds-check a pocket slot (`base + 0xa4a + 2n`, `0 <= n < 15`), with a 2-bit-per-slot word at `+0xa6c` | S: `src/matched/`; E: GAMEPLAY47 `g47-SLOTW`, `g47-UNIW` |
| `func_020b5ea0` / `func_020b64f0` | main | publish an outside position into the pending-destination record `0x021f69b8` | S: `src/matched/`; E: EXIT48 `x48-p-originz` |
| `func_020b6518` | main | installs that record's default `{0x30000, 0, 0x30000}` before any door is used | S: `src/matched/func_020b6518.c` |
| `func_020b6098` / `func_020b6140` / `func_020b6214` | main | the building EXIT: ask for the destination, forward it, read it back out of `0x021f69b8` for an element of kind `0x3c` | S: `src/matched/`; E: EXIT48 `x48-p-seqwatch` |
| `func_020b63f4` | main | writes the destination into the scene-request record at `0x021f69d4`, only while the request slot reads `0x3f` | S: `src/matched/func_020b63f4.c`; E: EXIT48 store watch, pc `0x020b6400`/`6404`/`6408` |
| `func_0203c76c` / `func_0203f684` | main | copy that position into the camera-tracked vector `0x021c749c` every third frame | S: `src/matched/`; E: EXIT48 store watch, pc `0x0203f68a`/`68e`/`692` |

## Data it reads and writes

| address or field | meaning | who writes | who reads |
|---|---|---|---|
| `0x021dc7bc` | player array, 4 slots, stride `0x249c` | `func_0209ef7c` | `func_020984e8` |
| slot `+0x1bf2`, 15x u16 (`0x021de3ae` for slot 0) | the pockets; `0xfff1` is empty | `func_02098f0c` | `func_02098f48` |
| slot `+0x1c10` u32 (`0x021de3cc`) | the wallet, in Bells | the game | the HUD, the save |
| **slot `+0x2408` u16 (`0x021debc4`)** | **the WORN SHIRT.** A drag from a pocket onto the character SWAPS them: the dropped id lands here and the one that was here goes back into the pocket, iff it is in the shirt band `0x11a8..0x12a7` (otherwise `0xfff1`) | `func_02099704`, from `func_ov096_0229e3b0` case 2 | `func_02099710`, the model loader |
| slot `+0x240a` u16 | the dispatcher's second wearable slot (its cases 3, 4 and 6; bands `0x1429..0x1430` and `0x13a0..0x13a7`). **Not yet exercised by any run** | `func_020996d4` / `func_020996ec` | `func_020996f8` |
| slot `+0x23f8` (`0x021debb4` for slot 0) | 64-bit event bitfield | the four commits, `func_02098ff8` | `func_02099020` |
| event flag 1 | "the opening is running" | `func_0209ee54` family | the 11 predicates at `0x020e1d08` |
| `0x021f3c30` | boot-mode word choosing the commit | `func_020a1320` | `func_ov051_022610d4` |
| `0x021fbe40` / `+4` | this frame's pad words / direction halfword | input | `func_0200dc98` |
| `self + 0x134`..`0x170` | movement intent block | `func_0200dc98` | the rest of the player update |
| `self + 0x170` | input mode: 1 pad, 2 touch | `func_0200dc98` | player update |
| **`0x021f69b8`**, `VecFx32` at `+0x00` | **the pending OUTSIDE position** -- where a building exit will put the player. Written when the player walks IN, defaulted to `{0x30000, 0, 0x30000}` before that | `func_020b64f0`, from `func_020b5ea0` and `func_020b6518` | `func_020b6214` case `0x3c` |
| **`0x021f69d4`/`+8`/`+0xc`** | the scene-request record's destination position | `func_020b63f4` | the scene load |
| `0x021c749c`, 3x `fx32` | the world point the field camera tracks -- the live player position; tile = word / 8192 | `func_0203f684`, from `func_0203c76c` | `ACWW_PLAYER_TRACE`, `port/tools/navlib.py` |
| **`*(u32 *)0x021d5684` + `0x5c`, 3x `fx32`** | **the player ACTOR's own world position** -- the live one, and the one to use indoors, where `0x021c749c` is the camera's clamped target and can be a whole tile out. Tile = word / 8192 | the movement update, at `pc 0x01ffcab8` (lr `0x02003315`), `pc 0x02003326` and `pc 0x02031444` (lr `0x02031427`) | `ACWW_PLAYER_TRACE`, `port/tools/navlib.py` |
| actor `+0x94` u16 | **the heading**, 16-bit turn units: `0` = south (+z), `0x4000` = east, `0x8000` = north (-z), `0xc000` = west. `+0x8c` is the same angle in 16.16 | the movement update | the movement update, the model |
| actor `+0x98` `fx32` | **the commanded walk speed, per LOGIC TICK.** Ramps at `+147` a tick and caps at **`1343`**. It is a command, not a displacement: against a wall or an item it reads `775` while the position does not move | the movement update | the movement update |
| firmware `+0x03` / `+0x04` | birth month / birth day | firmware (port: `usersettings.c`) | game greeting paths |

All rows are S, cited from the files in the previous table; the pockets, wallet and wear rows
are S+E -- the ROM function plus a live store watchpoint that caught it firing
(GAMEPLAY47, `docs/log/cycle41-gameplay.md` GP47-1 and GP47-2). The three actor rows are E:
per-frame region-ledger samples of the actor over held-direction pads, and a store watchpoint
with caller attribution naming the writers (WALK56, `docs/log/cycle41-gameplay.md` WALK56;
receipts `scratchpad/walk56/`).

**HOW FAST THE PLAYER WALKS, and it is one number.** MEASURED (WALK56). The ROM's logic tick is
one per **three** presented frames, so the position only ever changes on every third frame. A
held direction ramps the speed word by `+147` a tick to a cap of **`1343` fx32 a tick**, which is
`447.7` a frame and **18.3 frames a tile** (a tile is `8192` fx32). That cap is the same in all
four directions and the same indoors and out: a clean interior lane holds `1343` straight for
four consecutive tile crossings northbound, southbound, east and west, in **two different rooms**
(Nook's shop, floor kind `0x1e`, and the town hall, `0x06`). **The ORIGINAL agrees term for
term**: an oracle run walking south out of the town hall steps `261, 613, 844, 1017, 1172, 1321,
1343 x8` a tick, which is the port's clean southbound lane exactly. What varies is the
GETTING there -- a held direction that reverses the heading pays a ~30-frame 180-degree turn
first (the heading slews at `6000` units a tick), and a lane that hugs a wall or an item runs at
a reduced step until the player clears it. GAMEPLAY55's "south and west are 84 frames a tile"
was those transients read as a rate, and it is retracted; see `docs/kb/hybrid/scripted-play-2.md`
4n.

## How to check it

`port/shim/game/spnpc.c` prints `acww intro: f<frame> player <ptr> flag1 <v> bits <w0>/<w1>
mode <m> 54a8 <b>` on any change of that tuple, under `ACWW_TRACE_STATE=1`; it is the one
line that says whether the game believes it is still in the opening
[H: host/prose inference from port/shim/game/spnpc.c; verify against the ROM function or symbol table and this page's recipe]. `port/shim/game/newgameprobe.c` reports which of the two
new-game halves -- boot generation or player commit -- has happened, rather than inferring one
from the other [H: host/prose inference from port/shim/game/newgameprobe.c; verify against the ROM function or symbol table and this page's recipe].

For the exit position, arm `ACWW_INTERP_WATCH=0x021f69c0:0x021f69c3` from frame 1 over a run
that walks into a building: there are only three distinct values in a whole arrival, and the
`ACWW_PLAYER_TRACE` line before the second one names the tile it was taken from
[E: `docs/log/cycle41-gameplay.md` EXIT48 X48-3, run `x48-p-originz`; `scratchpad/exit48/runs/x48-p-originz`].

For the name prompt, run the town recipe and look at frames 4,500 to 7,500: the taxi interior
with the keyboard, then the confirmation
[E: docs/log/cycle40-keyboard-gate-probe.md TOWN40, `tap-D56`; `scratchpad/cycle40/runs/tap-D56`].

## Hypotheses

- **H: the `0x249c` player slot contains the pockets (inventory), the letters and the
  catalogue, and they are contiguous blocks inside it.** The slot is large and the event
  bitfield sits near its end at `+0x23f8` [H: source account: port/shim/game/newgameprobe.c; direct ROM-source provenance unresolved]. Experiment:
  diff two save images taken before and after picking up one item on a live run, and record
  which offsets inside the slot change.
- **H: event flag `0x23`, set by all four commits alongside flag 1, is "this player has been
  created".** All four do `set(1); set(0x23); clear(9)`
  [H: source account: port/shim/game/newgameprobe.c; direct ROM-source provenance unresolved]. Experiment: grep the matched tree for
  `func_02099020(..., 0x23)` call sites and read what each gates.
- **H: flag 9, which all four commits CLEAR, is a "returning player" or tutorial-done bit.**
  Same evidence [H: source account: port/shim/game/newgameprobe.c; direct ROM-source provenance unresolved]. Experiment: same grep for bit 9, plus set
  it by hand through `func_02098ff8` before the taxi and see what dialogue changes.
- **H: the player's own name is stored as UTF-16 at a fixed offset inside the `0x249c` slot,
  near its start.** The town name is stamped by a different routine into the town area
  [H: source account: port/shim/game/newgameprobe.c; direct ROM-source provenance unresolved] [H: log/source account: docs/log/cycle40-keyboard-gate-probe.md TOWN40; receipt provenance unresolved].
  Experiment: run the recipe twice with different typed player names and diff the slot.
- **H: the walk-speed clamp `[0, 0x1000]` and the run threshold `0xc32` mean running is
  roughly 76% of maximum stylus-drag speed and is also reachable by holding B.** Both
  constants are pool words [H: source account: port/shim/c6a_0200dc98_intent.c; direct ROM-source provenance unresolved]. Experiment: log `+0x134` and
  `+0x13a` over a live run with the mouse held at different distances from the player.
- **H: tools are held in the intent block's tap-target fields rather than in a separate tool
  slot -- i.e. the tool is a property of the action, not of a persistent hand.** `+0x13c` is a
  tap target and `+0x144` a tap class [H: source account: port/shim/c6a_0200dc98_intent.c; direct ROM-source provenance unresolved]. Experiment: reach
  a state where the player holds a tool and inspect `self + 0x134`..`0x170` against a
  tool-free frame.
- **H: the four player slots are the four residents a town may have, and the boot-mode word
  1/2/3 corresponds to first player / additional player / imported player.**
  `func_ov051_022610d4` maps 1, 2 and 3 to three different commits
  [H: source account: port/shim/game/newgameprobe.c; direct ROM-source provenance unresolved]. Experiment: force the word to 2 and 3 in turn and record
  which slot the resulting commit writes.

## Related

- `town.md` -- the save image the player array lives in
- `dialogue.md` -- the keyboards and the choice prompts the player answers
- `events-and-calendar.md` -- the event bitfield as the game's progress record
