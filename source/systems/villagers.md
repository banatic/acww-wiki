# Villagers

**Summary.** A town holds at most eight villagers. Each one occupies a fixed-stride record in
the save image, and each record carries a house sub-record: the villager and the house are one
object in storage. Who moves in is decided once, at generation time, by a picker that walks
six classes and rejects duplicates; who is on screen is decided every frame by a spawner that
opens one actor channel per present villager. Personality shows up twice: in which class the
picker drew from, and in a weighted table that chooses the villager's expression and animation
each time it reacts. The port draws them: a villager was walked into and talked to on
2026-09-10, after two cycles in which none was ever seen -- the reason for that was the arrival
tutorial's hold, not the draw chain.

## What happens

The eight villager records live in the save image at `0x021dc7a8 + 0x9284` = `0x021e5a2c`,
stride `0x7ec`, with the villager sub-record at `+0x7a0` of each
[S: func_02085a30, main, port/shim/game/villspawn.c]. That single stride is why the house and
the resident are inseparable in this game: the house placer indexes the same array
(`for (j = 0; j < 8; self += 0x7ec, j++)`)
[S: func_0207bbb8, main, port/shim/game/houseplace.c].

Who lives in a new town is decided by `func_0207b594`, `0x1d0` bytes in `main` with no matched
source: five nested loops that walk the eight villager slots and the seventeen species slots,
ask `func_0209bcd4` and `func_0209c380` whether each is allowed, pick with `func_020644cc` and
write the result through `func_0209bd30`
[S: func_0207b594, main, port/shim/game/villagers.c].

**`func_020644cc` is the game's `rand(n)` and its seed is the CLOCK** (`rng.md`): one state
word at `0x021cb5a0`, stepped `x = x * 0x19660d + 0x3c6ef35f`, set once at boot to
`minute | day<<8 | hour<<16 | second<<24` by `func_02061530` through `func_0209dbbc`
[S: `src/matched/func_02061530.c`, `src/matched/func_0209dbbc.c`]. **The roster and the town id
come off ONE stream but at very different moments**: on the two-tap town recipe the id lands at
frame 24,789 and slot 0's villager id byte at `0x021e61db` lands at frame **36,135**, written
by pc `0x020036ec`, 11,346 frames later -- so anything that consumes a draw in between moves
the roster without moving the id
[E: `docs/log/cycle41-gameplay.md` ORACLE46, runs `scratchpad/oracle46/runs/o46-A`, `scratchpad/oracle46/runs/o46-B`, `scratchpad/oracle46/runs/o46-E`].

**A villager id read out of the ORIGINAL is only trustworthy below `0x80`** on any ledger
written before ORACLE46: `observer.lua` printed peeked words with Lua's `%d`, which flattened
every word with bit 31 set -- and the id is byte 3 of that word -- to `-2147483648`, read back
as `128`. TUTORIAL45's emulator rosters `66, 128, 21, 128` and `107, 94, 128, 128` are that
defect, not the game [H: log/source account: `docs/log/cycle41-gameplay.md` ORACLE46 O46-2; receipt provenance unresolved]. **Those emulator rows are RETRACTED:
`docs/log/cycle41-gameplay.md`, O46-2.** Both of its callers declare it `void`
and neither reads a result, so its only product is the villager table
[S: func_0207b57c / func_0209e828, main, port/shim/game/villagers.c].

The initial pick loop is `func_0207c76c`, and its structure is legible. It runs eight
iterations. Each iteration asks `func_0207c818(self, mask)` for a class index; an index of 6
or more is skipped, so there are SIX classes -- the game's personality groups
[S: func_0207c76c, main, src/matched/func_0207c76c.c]. `func_0207c8c8(self, idx, 1)` then
draws a villager from that class, the result is rejected when it equals `~local2` (the
duplicate guard), and on success `func_02081518` writes it into `self + 0x7ec * i` -- the i-th
house record -- while `func_0207ca74` records it at `self + 0x4060`
[S: func_0207c76c, main, src/matched/func_0207c76c.c]. Three picks were observed in a
generated town with values `0x65`, `0x78` and `0x27`
[H: log/source account: port/BOOT-STATE.md, fifth pass 2026-08-27; receipt provenance unresolved].

Move-in is tied to the calendar rather than to generation alone: the town dispatcher's
generation handler is followed by "the RTC advance that moves villagers in", then a post-
generation sync [S: func_0209e6ec, main, port/shim/gfx/pmflist.c].

Putting a villager on screen is a separate chain that runs every session. Mode `0x2c`'s boot
script opens channel `0xd0`; its init `func_02085558` takes the outdoor branch and calls the
spawner `func_02085a30`, which walks the eight house records and, for each present villager,
opens CHANNEL `0x84` with id `(i | 0xe000)`
[S: func_02085558 / func_02085a30, main, port/shim/game/villspawn.c]. Channel `0x84`'s
constructor `func_ov068_0226da64` (record `0x022771a0` in ov068 data) builds the `0xa10`-byte
villager actor, and its init `func_0202e1fc` registers it in the manager at `0x021d1d4c`
[S: func_ov068_0226da64 / func_0202e1fc, ov068/main, port/shim/game/villspawn.c]. The manager
is eight slots of `{actor, id}` pairs, kind `0xe`
[H: source account: port/shim/game/villspawn.c, port/shim/game/campos.c; direct ROM-source provenance unresolved].

The villager's draw entry point is a POINTER-TO-MEMBER held in the object, not in a static
table: `func_ov068_0226d770` reads an 8-byte mwcc `{lo, hi}` pair at `obj + 0x8b0` and calls
through it, falling back to copying the `Vec3` at `+0x5c` into the three slots at `+0x478`,
`+0x484` and `+0x490` when it is null
[S: func_ov068_0226d770, ov068, port/shim/game/villdraw.c]. The pair is bound in the derived
init `func_ov068_0226d850` by an 8-byte copy from `data_ov068_02276eb0`, whose ROM contents
are `{0x0226d809, 0}` -- i.e. `func_ov068_0226d808`, Thumb
[S: func_ov068_0226d850, ov068, port/shim/game/villbind.c]. The bind is state-driven: state
0's enter binds and state 1's enter unbinds
[H: source account: port/shim/game/villdraw.c, observed rebinds; direct ROM-source provenance unresolved].

**The pair is written, and then the ROM clears it on purpose.** A store watchpoint on
`actor + 0x8b0` over the walk out of the town hall produces exactly three stores and no more:
`func_ov068_0226d850` writes `{0x0226d809, 0}` at pc `0x0226d874` (the derived init's own 8-byte
copy from `data_ov068_02276eb0`), a SECOND binder `func_ov068_0226cb00` writes the same pair at
pc `0x0226cb16` from its own source `0x022770a8`, and `func_ov068_0226bb3c` then writes
`{0, 0}` at pc `0x0226bb86` -- from the pool word `0x0213dd98`, which is **autoload_2 `.data`**
(`0x02138f80..0x0213fdc0`) and whose ROM bytes are `00000000 00000000`, mwcc's static NULL member
pointer. So `func_ov068_0226bb3c` is a state enter that UNBINDS the draw member, and the null the
draw slot sees is the ROM's own value, not a lost write
[H: log/source account: docs/log/cycle41-gameplay.md VILLAGER42, `v42-W2`; S: extract/adm-kr/arm9/unk_autoload_2.bin
+0x55558, config/adm-kr/arm9/delinks.txt; receipt provenance unresolved]. A load watchpoint on the vtable's slot 0
(`0x022771c0`) fires at pc `0x01ffd4a0`, so the dispatcher does fetch and run the derived init
[H: log/source account: `v42-W2`; receipt provenance unresolved]. Neither `villdraw.c` nor `villbind.c`/`villspawn.c` is in the interpreter registry
-- `port/shim/game/` is not a `SERVICE_DIRS` entry -- and `FS_StartOverlay` runs no relocation
pass on this path, so every one of those three words is ROM data as shipped
[H: source account: port/tools/interp_registry.py, port/shim/fs/ovlreloc.c; direct ROM-source provenance unresolved].

**This retracts GAMEPLAY42's "the 8-byte copy never reached the object".** That claim came from
two `ACWW_INTERP_PEEK` readings; the watchpoint shows the copy arriving twice
[H: log/source account: docs/log/cycle41-gameplay.md VILLAGER42; receipt provenance unresolved].

The two actors are LIVE, WALKING NPCs. The manager at `0x021d1d4c` holds `{0x022a8f48, 0xe000}`
and `{0x022a8528, 0xe001}`, and `actor + 0x5c` -- the object's own `VecFx32` -- moves between
runs: villager 0 reads `(79.000, 0.125, 95.000)` at frame 55,600, `(83.000, 0.125, 111.00)` at
60,600 and `(87.510, 0.125, 78.130)` at 68,200, with `+0x68` one step behind it; villager 1 walks
the same way near `x = 149..159, z = 83..95`. Both stay at ground level `y = 0.125`
[H: log/source account: docs/log/cycle41-gameplay.md VILLAGER42, `v42-P1`, `v42-V4`, `v42-V5`; receipt provenance unresolved]. The
`+0x478`/`+0x484`/`+0x490` triple GAMEPLAY42 read as "the same Vec3 three times" is only what the
fallback branch had just written there.

**THE HOUSE DOOR OPENS, ON BOTH PRODUCERS, AND THE RESIDENT CAN BE AT HOME (ORACLE50).** The
villager house that three cycles could not enter is a fact about ONE town. On the FORWARD shared
recipe's town `0x8365` -- the one the port and an emulator reference generate identically, down
to all eight roster slots `6b 5e 84 ff ff ff ff ff` and all 17 building cells -- a 93-row chain
walked to villager-1's doormat **(61, 69)** and BOTH producers went inside, five frames apart in
the transition and with the same two words: `0x021f69b8`, the pending outside position, takes
`503808 512 564736` (that doormat) on both, and `0x021f69d0`'s scene request takes the same
destination `65536 512 118784`. Inside, both stills show a villager standing in the room, and
the port's A pulses opened her greeting with `사브리나` in the nameplate. **GAMEPLAY48's
`이 몸은 밖에 계신다` -- the "I am OUT" note at that door -- is the resident of town `0xc66e`
being out on that timeline, not a door the port cannot open** [E: `docs/log/cycle41-gameplay.md`
ORACLE50 O50-3; runs `p50-door`, `e50-door`, `p50-enter`, `e50-enter`; current receipt locator: `scratchpad/oracle50/RECEIPTS.md`]. Only TWO villagers are
ever in the actor manager and the town has three (GP50-1); the third is the one indoors.

**AND THAT IS ENOUGH TO NAVIGATE TO ONE (GAMEPLAY44).** `actor + 0x5c` is in the SAME world
space as the live player position `0x021c749c`, so an actor's tile is `x // 8192` exactly as the
player's is, and `port/tools/navlib.py` now reads the manager's whole layout -- eight
`{actor, id}` slots of kind 0xe from `+0x00` and four of kind 0xd from `+0x40`, which is
`port/shim/game/villspawn.c`'s own `vill_mgr_dump` -- and hands `navigate.py` a talk target:
the walkable neighbour of the actor's tile nearest the player, faced back toward it, with no
doorway sweep. `port/tools/goto.py --to actor:<n>` re-resolves that target from every
iteration's own snapshot, because the villager WALKS -- one moved (76,47) -> (75,47) -> (77,45)
across five iterations -- and presses A once the player is on the tile. 마르 answers on the
first pulse and the A pulses carry the conversation three lines further
[E: `docs/log/cycle41-gameplay.md` GP44-2, `scratchpad/gameplay44/RECEIPTS.md`, runs
`TALK1-1`..`TALK1-5` and `g44-TALK`]. This closes the "reach" candidate of VILL42-4: nothing
was wrong with the spawn, the bind or the draw -- **no walk had ever been aimed at an actor's
own position**, and three cycles of sweeps were aimed at `0x021f69d4`, which is a scene-entry
position and does not move.

**Two retractions, in this order, and this paragraph is what is left of the claim.** This page
used to open here with "No villager has still ever been on screen, and the reason is reach".
**SAVE43 retracted that**: villagers ARE drawn, and one answers a bump plus `A` with a dialogue
box in the acres around the player's house, while Tom Nook is drawn through his whole arrival
speech [H: log/source account: `docs/log/cycle42-save.md` SAVE43, `gp-D2`, `gp-D4`; receipt provenance unresolved]. **GAMEPLAY44 retracted
GAMEPLAY43's clock explanation.** From one frozen-generated town snapshot, the frozen and
advancing clock arms both hold over the same frames; frames 048,000..051,400 are SHA-256
identical. The town-generation difference had confounded GP43's comparison [E:
`docs/log/cycle41-gameplay.md` GAMEPLAY44, GP44-1; `scratchpad/gameplay44/RECEIPTS.md`,
`g44-FRZ` and `g44-ADV`, 048,000..055,000]. The `X` then `B` observation belongs to the
VILLAGER42 arrival chain and is not a general frozen-clock rule.

What still holds is that the two actors are LIVE and WALKING, and that a hunt has to be AIMED at
them. **The player's live position is `0x021c749c`, the vector the field camera tracks -- NOT the
`0x021f69d0` record this page cites below.** That record is a SCENE-ENTRY position: it reads
(145.000, 0.125, 179.875) and the same value again after 1,400 frames of walking, while the
villagers' own `actor + 0x5c` moves between the two reads, and three sweeps aimed off it met
nobody. NAV42 found the right address by diffing two snapshots of one build with the player in two
places, and confirmed it three ways against the field camera's own cylinder transform;
`port/tools/navigate.py` plans a walk over the acre collision grid from it and
`port/tools/goto.py` closes the loop [H: log/source account: `docs/log/cycle41-gameplay.md` NAV42 and GP43-5,
`g43-P2`, `g43-P3`, `g43-T2`, `g43-T3`, `g43-T4`; VILLAGER42 `v42-P4`; receipt provenance unresolved]

The ORIGINAL shows no villager either over the same timeline: an emulator arm with the same pad
script and the same two-tap town recipe, 20 frames at 49,800..55,500, has the original inside the
same arrival tutorial with the same illustration and no villager in any frame
[O: docs/log/cycle41-gameplay.md VILLAGER42, `scratchpad/villager42/oracle-vill/`]. That is
consistent with both readings above: the ORIGINAL is inside the same hold.

**The historical observations differed about the prompt (STYLE rule 7).**
VILLAGER42 measured that with no `X` in the pad script the illustration is still up 11,900
frames later, and that `X` (mask `0x400`) then `B` clears it
[H: log/source account: VILLAGER42, `v42-V1`, `v42-V3`, `v42-V4`; receipt provenance unresolved]. SAVE43's chain had **no `X` row at all** and the
hold released anyway, after which villagers were drawn and could be bumped into
[H: log/source account: SAVE43, `gp-P1`..`gp-D4`; receipt provenance unresolved]. GAMEPLAY44's same-town comparison above resolves the clock
confound; the exact arrival event that opens and clears the prompt remains a separate question.

The villager's own draw slot only pushes its SRT into a per-id slot on a service side
(`func_02012214 -> func_0205e954`); the model geometry is submitted by the NPC model
service's own draw slot `func_020500d8` (vtable `0x020dce48` slot 9, object at
`data_021c8184`), one `func_0205510c` per request slot in state 3
[S: func_020500d8 / func_02012214, main, port/shim/game/villmodel.c]. So a villager emitting
zero GX words in its own slot is normal
[H: source account: port/shim/game/villmodel.c; direct ROM-source provenance unresolved]. Once the light manager was repaired the villager draw was
measured emitting `0x8c8`-`0xa20` words a frame
[H: log/source account: port/BOOT-STATE.md, "Villagers were never missing"; receipt provenance unresolved].

The villager's face is a table index, not a model id. `func_020808ec` reads the byte at
`record + 0x7af` and hands it to `func_02082500`, which indexes `data_020cd884` by
`param * 0x4e`; `func_020808d0`'s fallback for `>= 0x21` being 0 bounds the table at 33
entries [S: func_020808ec / func_02082500, main, port/shim/game/villagerface.c].

Expression and animation are a weighted roll. `func_0204fb80` takes a table of tables at
`0x020dc8b4`, selects `table[a3 - 1][a5]`, adds `a2 * 8` to reach an 8-byte record whose `[0]`
is an entry array and `[4]` a count, and walks 3-byte entries -- `+0` and `+1` the two
outputs, `+2` the weight -- accumulating weights until one exceeds the roll
[S: func_0204fb80, main, port/shim/game/exprpick.c]. The roll comes from
`func_020e92d0(&0x021cb5a0, bound)` with the bound being `0x60` or `0x64` depending on
`func_02073d90(*0x020ccf94)` -- a mode test that also skips the last three entries when it
passes [S: func_0204fb80, main, port/shim/game/exprpick.c]. Nothing is written on a miss and
the function returns 0, so a stub returning 0 leaves every villager using whatever its caller
left in those two words [H: source account: port/shim/game/exprpick.c; direct ROM-source provenance unresolved].

A villager approach scan exists for proximity reactions: `func_ov068_02266bac` calls the
ov003 slot-position getter at `0x0222f458`, which reads
`p = 0x022617bc + (idx & 0xf) * 0x25c`, copies the `Vec3` at `p + 0x204` and returns the
signed byte at `p + 0x24d` -- the slot's occupant id, `-1` for empty -- then rejects the slot
when `func_020ea990(pos, out) >= threshold`
[S: func_ov068_02266bac / func_ov003_0222f458, ov068/ov003, port/shim/game/genfix.c]. There
is a parallel six-slot NPC table at `0x0225f76c`, stride `0x24c`
[H: source account: sub_02227638, ov003, port/shim/game/genfix.c; direct ROM-source provenance unresolved].

The ov003 slot machinery that drives all of this only runs once
`__sinit_ov003_02237af4` has constructed the six `0x24c` slot records at `0x0225f76c`; when
that initialiser was skipped the whole per-frame slot pass was dead
[S: __sinit_ov003_02237af4, ov003, port/shim/game/exprpick.c].

Villager houses use four texture sets and two animations, named in ov003's own pool:
`/str/npcHsTex/%c/house_%c%d%c.nsbtx`, `/str/npcHsTex/%c/light_%c%d.nsbtx`,
`/str/obj_house_i.nsbca` and `/str/obj_house_o.nsbca`
[S: ov003 image at 0x02239bf8, 0x02239c1c, 0x02239c40 and 0x02239c58,
port/shim/game/townhouses.c; the same four addresses `town.md` cites].

**Talking to one has a precondition of its own, and it is the villager's position rather than
the button.** The trigger is the A button's edge: the game publishes the pad into `0x021fbe3c`
(held) and `0x021fbe42` (trigger) once per main-loop iteration, and an iteration is one per
three presented frames, so a press shorter than three frames registers only if it happens to
cover the sampled frame. With that press delivered, an adjacent villager answers on the first
edge if TWO things hold: she is **inside about one tile** of the player -- 1.99 world units
answered, 3.67 did not, and a tile is 2.0 units -- and the player is **facing her**, the facing
they already have rather than one held into them. Facing away or across her from the same tile,
with the same press, opens nothing, and holding a direction into her with no A under it opens
nothing in 740 frames. Every villager measured answering had her own speed word `actor + 0x98`
at 0 (stopped); whether that is required is not separated from the distance here
[E: `docs/log/cycle42-save.md` TALK45, runs `scratchpad/talk45/runs/{B1,B6,B7,B8,C1,C2,C3,L1,L2,L3,L4}`].
A villager's own heading and commanded speed are the same two words the player actor carries,
`actor + 0x94` (16-bit heading, 0 = south, 0x4000 = east, 0x8000 = north, 0xc000 = west) and
`actor + 0x98`, at the same offsets from the actor the manager at `0x021d1d4c` holds
[S: `port/tools/navigate.py` header (WALK56); `port/tools/navlib.py` section 4].

**HOW A WALKING PLAYER GETS INTO THAT TILE: PUSH INTO HER, AND PRESS UNDER THE PUSH
(VILLAGER76).** The paragraph above is a savestate result; this is the on-foot one, and it is
GAMEPLAY73's tree rule on an actor -- the collision does the aiming. A villager BLOCKS the
player and then lets them past: a held direction from the tile beside her takes **116 frames**
to cross into her tile where an open tile costs 18, then pushes the player one tile SIDEWAYS
and walks on freely. So the contact is worth about **96 frames** of standing inside the talk
window, and the stop leaves the player at **0.78 to 0.995 tiles** -- 0.995 tiles is 1.99 units,
the distance TALK45 measured answering. Nine scripted arms that hold the direction for
`25 * tiles + 40` frames with A pulsed underneath are **9 of 9**; seven that hold for 200-240
frames are **0 of 7**, because the player walks through the window and ends four to six tiles
away. Live, through `play.py` and `drive.py` at 59.82 fps, five launches opened five
conversations from five walking encounters, **5 of 5** -- with the `Z` train OVERLAPPING the
held arrow (a `Z` that starts after the release is already spending the 96 frames) and the
closing `X` overlapping a held arrow AWAY from her
[E: `docs/log/cycle41-gameplay.md` VILLAGER76 V76-6, V76-7; runs
`scratchpad/villager76/runs/{H1,W2,W3,T1,T2,BLK,BLK2,W01..W05}*`].

**Who is outdoors depends on the hour.** At 11:30 the manager held three villagers walking the
town at once plus the mayor, on a save whose census is three; at 10:00 the same town's outdoor
snapshots hold two, and after dark none
[E: `docs/log/cycle42-save.md` TALK45; `docs/kb/hybrid/stall-playbook-recent.md` case 91].
**And the manager is CAPPED below the census**: on LIVE47's save, whose census is five, the
outdoor manager held exactly three at 09:00, 11:30, 15:00 and 17:00, the union across those
four hours is four (`0xe000`..`0xe003`), and slot 4 was never outdoors at any of them
[E: `docs/log/cycle41-gameplay.md` VILLAGER76 V76-1].

## The state machine, and the two simulations a villager has (VILLAGER76)

**A villager is not always walking.** The object's state word is `actor + 0x380`, written every
main-loop iteration at pc `0x0201b246` inside `func_0201b1a4`
[S: `src/matched/func_0201b1a4.c`; E: watchpoint `scratchpad/villager76/runs/WATCH-STATE`], and
it selects between two entirely different simulations:

| `+0x380` | what runs | `+0x5c` position | `+0x94` heading | `+0x98` speed | `+0x388` target |
|---|---|---|---|---|---|
| **0** | the TILE LATTICE | always a tile CENTRE | 0 | 0 | (0,0) |
| 1 | walking to the target | free | live | ramps to 256 | a tile centre |
| 2 | a second leg kind, rare | free | live | live | a tile centre |
| 3 | the TURN that starts a leg | held | live | 0 | a tile centre |

**In state 0 a villager advances one whole tile every 120 presented frames and does not walk at
all.** Three villagers over 3,060 frames with the player 15+ tiles away gave 25 steps each and a
gap histogram of `120 x24` -- every gap, every villager. The position is a tile centre by
construction rather than by rounding: `func_0204f794` writes `(tile << 13) + 0x1000` into x and
z and 0 into y, which the ground pass then lifts to `0x200`
[S: `src/matched/func_0204f794.c`; E: watchpoint `runs/WATCH-POS`, pc `0x0204f79a`], and
`func_0204f818` writes the derived tile back into `+0x988`/`+0x98c` on the same frame
[S: `src/matched/func_0204f818.c`; E: `runs/WATCH-TILE`] -- that pair is a CACHE of `pos >> 13`
and never a target.

In states 1/2/3 the same object is integrated every iteration by `func_02031288`, the generic
collision move: a current position, a target position, a `0xc000` clamp, `func_02030ebc`'s
sweep, `func_02034270`'s ground snap to `floor + 0x200`, and the result written back
[S: `src/matched/func_02031288.c`]. A leg is `state 0` (a pause of 12-51 frames with the target
cleared to (0,0)) -> `state 3` (a turn of 27-42 frames, the new target already chosen) ->
`state 1` (48-639 frames of walking). Targets are fresh tile centres one to eight tiles off --
eleven distinct ones per villager in 3,060 frames.

**Which simulation runs is the player's distance, and it is NOT a clean radius.** One variable,
the player standing still, the villager ledgered 255 frames: awake at 2, 4, 6 and 8 tiles south
and 5 and 6 north; on the lattice at 7, 8 and 9 north, 10 and 12 east, 16 west and 20 north. So
the switch is inside 6 tiles in every direction tried and outside 7 in one of them; it is not
the acre (7 north is the same acre as 6 north) [E: VILLAGER76 V76-5, `radius76.py`].

**ORACLE78 SWEPT THAT EDGE IN EIGHTHS OF A TILE: IT IS A FOUR-BOUND AXIS-ALIGNED XZ RECTANGLE
CARRIED BY THE PLAYER -- a PER-AXIS BOX, with the four bounds all different.** Same instrument,
same chain, one variable: the player poked onto a sub-tile position, the villager ledgered
765 frames at one sample a frame. Every edge below is SHARP -- the last awake arm and the first
asleep arm are one eighth of a tile apart -- and stable: `6.875` tiles never wakes in 765
frames, while `6.5` and `6.0` both wake at frame 8,081 [E: `scratchpad/oracle78/BOUND-SWEEP.txt`,
`wake-*.json`, `SHORT-*` arms].

| where the VILLAGER is, relative to the player | awake to | asleep from | arms |
|---|---|---|---|
| SOUTH of the player (the player stands north) | **6.750** | **6.875** | `0x022a7698`, 17 arms |
| SOUTH of the player, a SECOND villager | **6.875** | **7.000** | `0x022a80b8`, 17 arms |
| NORTH of the player (the player stands south) | **12.000** | **12.500** | `0x022a80b8`, 31 arms |
| WEST of the player | **8.375** | **8.500** | `0x022a7698` |
| EAST of the player | **7.750** | **7.875** | `0x022a7698` |

Two different villagers put the same edge one eighth of a tile apart, so the bound is the
player's, not the object's.

**The acre is REFUTED** by the eighth-of-a-tile sharpness of every edge. **A radius about the
villager is REFUTED** by 6.75 against 12.0 along the SAME axis. **A per-axis box SURVIVES, and
one control is what says so**: the x edge is `8.375`/`8.500` measured at the villager's own depth
AND again with the player four tiles away in z -- the x bound does not depend on z
[E: `wake-eperp-4-sweep.json`].

**THE COMPARE IS `func_ov068_0226caac`, AND IT IS LITERALLY A FOUR-BOUND RECTANGLE**
[S: `src/matched/func_ov068_0226caac.c`]: `b->x > a->x - s->halfExtentX && b->x < a->x +
s->halfExtentY`, then `b->y > a->y - s->top`, then `b->y < a->y + s->bottom` -- four independent
bounds in the XZ plane, with `a` and `b` two `VecFx32`-shaped points. It was found by
DIFFERENCING an `ACWW_INTERP_CENSUS` window between one awake arm and one asleep arm from the
same snapshot: the asleep arm's function set is a strict SUBSET of the awake arm's (260 functions
only awake, 0 only asleep), and of the bodies present in both with the SAME call count,
`func_ov068_0226687c` (the per-iteration villager dispatcher, 255 calls, 3,225 steps against
1,785) and `func_ov068_0226caac` (255 calls, 8,773 against 8,653) are the ones whose step counts
separate [E: `scratchpad/oracle78/CENSUS-DIFF.txt`, runs `CEN-awake` / `CEN-asleep`]. The four
bound values have NOT been read out of `s` and are the next thing to take.

**Two instruments were spent first and neither separates the arms, which is the method note:**
`ACWW_INTERP_WATCH_LR` on `actor + 0x380` reports ONE key in both arms
(`pc 0x0201b246 lr 0x020b9fb9` = `func_020b9f80`), and `ACWW_INTERP_RWATCH` over the player
actor's position words reports 47 reader pcs awake against 46 asleep. A watchpoint names the last
writer and the readers of a value; a census names the branch (M1).

**NOT measured: the CORNERS.** At `dz = 6.0`, one eighth inside the z edge, the verdict stops
being monotone in x -- awake at `dx +2`, asleep at `dx +1` and `+3` -- so within about a tile of
an edge a 255-frame window is not a reliable classifier, and the corner arms in
`map-z6.json` are recorded as such rather than read as a shape. Two villagers inside the region
at equal distance are BOTH awake, so there is no one-at-a-time cap [E: arms `CAP-a1`, `CAP-a2`].

**`actor + 0x49c` is NOT an event queue.** VILLAGER76 read its four words as
`{event, code, latched}` for half a cycle -- a 1 and a 9 on the frame a villager stepped, zero
otherwise -- and `src/matched/` corrected it: it is `func_02031288`'s own 0x30-byte `A0 *self`
record, where `f4 |= 1` means the ground pass clamped the position, `f8` is the SURFACE it
landed on and `f24/f28/f2c` is the delta actually moved, and `func_02032c8c` rolls `f4` into
`f0` and clears the rest every iteration [S: `src/matched/func_02031288.c`,
`src/matched/func_02032c8c.c`]. The "event code 9" is a ground-surface id (M1).

**THE LATTICE IS THE ROM'S, NOT THE PORT'S -- the DS was asked and it does the same thing
(ORACLE78).** Two producers in the SHARED town (`port/tools/oracle/README.md`'s forward recipe at
card-32: port `ACWW_TOUCH2_AT=23534`, oracle `--touch2-at 24700`), both standing still outdoors
at tile (72,51) with the two outdoor villagers 28 and 41 tiles away, both read over the SAME 765
frames at the same cadence -- the port through the region ledger, the original through
`--peek` on `+0x5c`, `+0x94`, `+0x98`, `+0x380` and `+0x388`:

| producer | arm | state `+0x380` | on the tile lattice | steps | gaps | heading | speed | target |
|---|---|---|---|---:|---|---|---|---|
| **port** | `0xe001`, `0xe002`, x2 runs each | **0 in 256/256** | 256/256 | 7 | `120 x6` | 0 | 0 | (0,0,0) |
| **ORIGINAL** | `0xe002`, x2 runs | **0 in 256/256** | 256/256 | 6 | `120 x5` | 0 | 0 | (0,0,0) |
| **ORIGINAL** | `0xe001`, x2 runs | **0 in 256/256** | 216/256 | 6 | `120 x5` | 0 | 0 | (0,0,0) |

**The DS does not walk off camera either.** Every gap on both producers is exactly 120 presented
frames, the heading, the speed and the walk target are zero on both, and the state word is 0 on
both. The two producers' villagers are one tile apart at the window's start and take different
paths -- the chains are ~350 frames out of phase and the draw streams differ after the layout
burst -- so this is an agreement about the SHAPE of the simulation, not a frame-for-frame
replay. Each side's two runs are identical to each other [E: `scratchpad/oracle78/SIDE-BY-SIDE.md`,
`tables/`, runs `o78-far-A`/`o78-far-B` (exit 0, 895.0/889.3 s, ledgers complete) and
`P-FAR-*`].

**The one difference, and it is not a port defect: the original's stop is not ALWAYS a tile
centre.** One of `0xe001`'s six stops on the DS is `(35.2128, 41.2128)` -- offset `0x6cf` from the
centre in BOTH axes, held for a whole 120-frame interval, with the stop before and after it back
on centres. The port's own `func_0204f794` is the same matched code and writes
`(tile << 13) + 0x1000`, so an off-centre state-0 position means the ROM called it with something
else (or another writer placed her); the port never reached that cell in ~2,000 samples. **Open,
and ranked below.**

## Where it lives

| function or symbol | module | role | grade/citation |
|---|---|---|---|
| `func_0207b594` | main | decides who lives in a new town (8 slots x 17 species) | S: port/shim/game/villagers.c |
| `func_0207c76c` | main | the initial pick loop, 8 iterations, 6 classes | S: src/matched/func_0207c76c.c |
| `func_0207c818` / `func_0207c8c8` | main | class index / villager draw within a class | S: src/matched/func_0207c76c.c |
| `func_02081518` | main | writes a picked villager into a house record | S: src/matched/func_0207c76c.c |
| `func_02085a30` | main | per-session spawner: opens channel `0x84` per villager | S: port/shim/game/villspawn.c |
| `func_ov068_0226da64` | ov068 | channel `0x84` ctor, `0xa10`-byte villager actor | S: port/shim/game/villspawn.c |
| `func_0202e1fc` | main | registers the actor in the manager | S: port/shim/game/villspawn.c |
| `func_ov068_0226d770` | ov068 | the villager draw slot (PMF at `obj+0x8b0`) | S: port/shim/game/villdraw.c |
| `func_ov068_0226d850` | ov068 | derived init, binds the draw PMF | S: port/shim/game/villbind.c |
| `func_020500d8` | main | NPC model service draw slot: submits geometry | S: port/shim/game/villmodel.c |
| `func_020808ec` / `func_02082500` | main | face byte -> `data_020cd884` index | S: port/shim/game/villagerface.c |
| `func_0204fb80` | main | weighted expression/animation pick | S: port/shim/game/exprpick.c |
| `func_ov068_02266bac` | ov068 | villager-approach slot scan | S: port/shim/game/genfix.c |
| `func_0202e0c8` | main | villager house/record step | S: port/shim/game/villhouse.c |
| `func_0201b1a4` | main | writes the villager STATE word `+0x380` every iteration | S: src/matched/func_0201b1a4.c |
| `func_0204f794` / `func_0204f818` | main | tile -> position `(t<<13)+0x1000`, and its inverse `pos>>13` | S: src/matched/func_0204f794.c, func_0204f818.c |
| `func_02031288` | main | the generic collision MOVE: clamp, sweep, ground snap, write back | S: src/matched/func_02031288.c |
| `func_02032c8c` | main | rolls the `+0x49c` move record forward each iteration | S: src/matched/func_02032c8c.c |

## Data it reads and writes

| address or field | meaning | who writes | who reads |
|---|---|---|---|
| `0x021e5a2c` | 8 house records, stride `0x7ec` | `func_02081518`, `func_0207bbb8` | `func_02085a30` |
| record `+0x7a0` | the villager sub-record | new-game pick | `func_0207c72c`, `func_0208150c` |
| record `+0x7af` | face/table index byte | pick | `func_02003648` -> `func_02082500` |
| `0x021d1d4c` | villager manager, 8 `{actor, id}` slots | `func_02082ab0` | camera pick `func_0203c794` case `0x2c` |
| `obj + 0x8b0` | draw PMF `{lo, hi}` pair | `func_ov068_0226d850`, `func_ov068_0226cb00` (bind); `func_ov068_0226bb3c` (UNbind) | `func_ov068_0226d770` |
| `data_ov068_02276eb0` | the PMF source pair `{0x0226d809, 0}` | static | `func_ov068_0226d850` |
| `0x022770a8` | the same pair, the second binder's source | static | `func_ov068_0226cb00` |
| `0x0213dd98` | autoload_2 `.data`: the static NULL pair `{0, 0}` | static | `func_ov068_0226bb3c` |
| `0x021f69d0` | the local player's record; `+4` is its position `VecFx32` | save load | `func_020b5e10` / `func_020b5e40` |
| `0x020dc8b4` | table of tables of 8-byte expression records | static | `func_0204fb80` |
| `0x021cb5a0` | RNG state used by the expression roll | `func_020e92d0` | `func_0204fb80` |
| `0x0225f76c` | six NPC slots, stride `0x24c` | `__sinit_ov003_02237af4` | `sub_02227638` |
| `0x022617bc` | villager approach slots, stride `0x25c` | ov003 static init | `func_ov003_0222f458` |
| `actor + 0x380` | the villager STATE: 0 lattice, 1 walking, 2 a second leg, 3 the turn | `func_0201b1a4` | the walk step |
| `actor + 0x388` | the WALK TARGET `VecFx32`, always a tile centre; (0,0) in state 0 | the leg chooser | `func_02031288` |
| `actor + 0x49c` | `func_02031288`'s 0x30-byte move record -- NOT an event queue | `func_02031288`, `func_02032c8c` | `func_02031288` |
| `actor + 0x988` | the derived tile, `pos >> 13`, written on the step frame | `func_0204f818` | -- |

All rows above are S, cited from the shim headers named in the previous table.

## How to check it

The manager occupancy probe is the cheapest check: `port/shim/game/villspawn.c` prints the
eight `{actor, id}` slots at `0x021d1d4c` on every mode change and after each spawn pass, and
`port/shim/game/villpick.c` prints one line per pick (slot, class, villager id)
[H: source account: port/shim/game/villspawn.c, villpick.c; direct ROM-source provenance unresolved]. Both are gated on `ACWW_TRACE_STATE=1`
[H: source account: port/shim/game/villspawn.c; direct ROM-source provenance unresolved].

Note the port-only caveat: on the NATIVE path `func_0207b594` is deliberately a no-op and
prints `villager placement SKIPPED`, so a native run's empty villager table is the port's
decision, not the game's [H: source account: port/shim/game/villagers.c; direct ROM-source provenance unresolved]
[H: log/source account: docs/log/cycle40-keyboard-gate-probe.md LONG40, "villager placement SKIPPED" at frame
19335; receipt provenance unresolved]. On the INTERPRETER path the ROM's own `func_0207b594` runs
[H: source account: docs/kb/hybrid/runtime.md via docs/log/cycle40-keyboard-gate-probe.md REG40; direct ROM-source provenance unresolved].

## Hypotheses

- **H (OPEN, ORACLE78's ranked one): `func_ov068_0226caac`'s four bounds ARE the wake rectangle,
  and they have not been read.** The census differential puts that body on the branch and its
  matched source is a four-bound axis-aligned XZ test (see the state-machine section); the
  measured edges are about 8.4 tiles west, 7.8 east, 12.25 north and 6.8 south of the player.
  What is missing is the struct: who `s` is, whether the four words are constants or per-villager,
  and whether `a` is the player or the camera. Experiment: `ACWW_INTERP_RWATCH` on the FOUR words
  `s` points at -- find `s` first with one `ACWW_INTERP_WATCH_LR`-style arm on the call, or read
  `func_ov068_0226d770`'s literal pool, since it is the caller that reads the villager's `+0x5c`
  in the same census.
- **H (ORACLE78, and it is why the awareness path is NOT the gate): `func_ov068_02271cec` is a
  nearest-actor scan, not the switch.** It reads the player's `+0x5c` (pcs `0x02271d18/1c/20`),
  calls `func_020ea990` -- the squared XZ distance, the only body seen reading both the player's
  and the villager's positions -- and hands the result to `func_ov068_02271c58`, which compares it
  with `*(int *)(ctx + 0x224)` and accumulates a byte at `ctx + 0x254` capped at 254. `ctx` is
  `actor - 0x1a8` (its `+0x204` IS the villager's `+0x5c`, byte for byte in three actors) and its
  `+0x224` reads a large NEGATIVE word in every snapshot examined, so `r3 > t` is always true and
  the flag is always 1. Experiment: find what CONSUMES `+0x254` -- an accumulator capped at 254
  with `+1/+3/+5/+8/+15/+25` increments is a friendship or an attention meter, and naming its
  reader would be worth more than another sweep.
- **H (OPEN, ORACLE78): a state-0 villager's position is not always a tile centre on the DS.**
  One of six stops read on the original sits at `0x6cf` from the centre in both axes for a whole
  120-frame interval. `func_0204f794` writes `(tile << 13) + 0x1000` by construction, so either
  its caller passed something else or a second writer placed her. Experiment: put the port's own
  villager on that cell (a snapshot poke, `stand76.py`'s shape applied to the villager) and watch
  `+0x5c` -- if the port reproduces the offset, the two producers agree and the cell is special;
  if it writes a centre, there is a real difference and the caller is the place to look.
- **H: the six classes `func_0207c818` returns are the six personalities (lazy, jock, cranky,
  peppy, normal, snooty).** The index is bounded at 6 and each class has its own draw
  function argument [S: src/matched/func_0207c76c.c]. Experiment: log the class index and the
  drawn villager id for 100 generated towns and check that ids partition into six disjoint
  sets.
- **H: the "seventeen species slots" in `func_0207b594` are species groups (cat, dog, bird
  ...), and `func_0209bcd4` / `func_0209c380` enforce a per-species cap.** The loop nesting
  is 8 x 17 with two permission predicates
  [H: source account: port/shim/game/villagers.c; direct ROM-source provenance unresolved]. Experiment: decompile `func_0209bcd4` and
  `func_0209c380`, then generate 50 towns and count species repeats.
- **H: move-in and move-out are driven by the day-change routine `func_02040c90`, not by the
  villager code.** The generator's own sequence is "generate, then an RTC advance that moves
  villagers in" [H: source account: port/shim/gfx/pmflist.c; direct ROM-source provenance unresolved], and `func_02040c90` is identified as the
  day-change / calendar update [H: source account: port/tools/known_callees.txt; direct ROM-source provenance unresolved]. Experiment: watch the eight
  records at `0x021e5a2c` across an `ACWW_RTC_*` day rollover and see whether any changes.
- **H: friendship is a byte inside the `0x7ec` record, and the expression pick's `a2`
  argument is derived from it.** `func_0204fb80` selects one of several 8-byte records by
  `a2 * 8` inside a per-class table [H: source account: port/shim/game/exprpick.c; direct ROM-source provenance unresolved]. Experiment: instrument
  `func_0204fb80`'s arguments over a long town run and correlate `a2` with any monotonically
  changing byte in the speaking villager's record.
- **H: `data_020cd884`, indexed `param * 0x4e`, is the villager species table with a
  `0x4e`-byte row (name, model, texture, voice).** The stride and the 33-entry bound are
  measured [H: source account: port/shim/game/villagerface.c; direct ROM-source provenance unresolved]. Experiment: dump 33 rows and check for a
  repeating internal structure; cross-check row count against the species count in
  `func_0207b594`'s seventeen slots.
- **H (OPEN, and it is the ranked one): which arrival step gates the villagers, and what
  releases the tutorial hold.** The two chains disagree. VILLAGER42's, driven from
  `st/town48000.st` with a pad script containing no `X`, sat inside the Nintendo-DS illustration
  for at least 11,900 frames with the pad discarded, and pressing `X` then `B` cleared it
  [H: log/source account: `docs/log/cycle41-gameplay.md` VILLAGER42, `v42-V1`/`v42-V3`/`v42-V4`; receipt provenance unresolved]. SAVE43's, driven
  from `st/b55400.st` on a later build with no `X` row, was past the hold and had villagers
  drawn, walkable-into and talkable [H: log/source account: `docs/log/cycle42-save.md` SAVE43, `gp-D2`, `gp-D4`; receipt provenance unresolved].
  GAMEPLAY44 has isolated town generation from the post-snapshot clock arm, as described above.
  The exact arrival step and input that clear the prompt remain to be isolated. **A further experiment is one run each way on ONE
  build**: resume both snapshots, drive each with BOTH pad scripts (the one with an `X` row and
  the one without), take stills every 50 frames across the hold, and record for each arm the
  frame the lower screen releases and the frame a villager first appears -- four arms, ~10
  minutes, and the answer is which of the four combinations reaches the villagers. Peek
  `0x021c749c` (the player's live position, NAV42 above) at each still: a hold that discards the pad shows a
  position that does not move, which separates "the hold is up" from "the script missed".
- **H: villager movement (walking, pathing) runs in `func_0202e0c8`'s per-frame step through
  virtual slot 25.** That slot returns the object the record accessor `func_0208150c` is
  applied to [H: source account: port/shim/game/villhouse.c; direct ROM-source provenance unresolved]. Experiment: instrument slot 25's return and
  `func_0207945c`'s second argument on the `tap-D59` town-hall run.

## Related

- `../experiments/gameplay-walkthrough.md` -- both chains, frame by frame, including the SAVE43
  stills in which a villager is drawn
- `town.md` -- the house records are part of the town's save image
- `dialogue.md` -- what a villager says once the talk machine reaches it
- `events-and-calendar.md` -- birthdays and the day-change routine
