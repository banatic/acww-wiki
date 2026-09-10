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
defect, not the game [E: same]. **Those emulator rows are RETRACTED:
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
[E: port/BOOT-STATE.md, fifth pass 2026-08-27].

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
[S: port/shim/game/villspawn.c, port/shim/game/campos.c].

The villager's draw entry point is a POINTER-TO-MEMBER held in the object, not in a static
table: `func_ov068_0226d770` reads an 8-byte mwcc `{lo, hi}` pair at `obj + 0x8b0` and calls
through it, falling back to copying the `Vec3` at `+0x5c` into the three slots at `+0x478`,
`+0x484` and `+0x490` when it is null
[S: func_ov068_0226d770, ov068, port/shim/game/villdraw.c]. The pair is bound in the derived
init `func_ov068_0226d850` by an 8-byte copy from `data_ov068_02276eb0`, whose ROM contents
are `{0x0226d809, 0}` -- i.e. `func_ov068_0226d808`, Thumb
[S: func_ov068_0226d850, ov068, port/shim/game/villbind.c]. The bind is state-driven: state
0's enter binds and state 1's enter unbinds
[S: port/shim/game/villdraw.c, observed rebinds].

**The pair is written, and then the ROM clears it on purpose.** A store watchpoint on
`actor + 0x8b0` over the walk out of the town hall produces exactly three stores and no more:
`func_ov068_0226d850` writes `{0x0226d809, 0}` at pc `0x0226d874` (the derived init's own 8-byte
copy from `data_ov068_02276eb0`), a SECOND binder `func_ov068_0226cb00` writes the same pair at
pc `0x0226cb16` from its own source `0x022770a8`, and `func_ov068_0226bb3c` then writes
`{0, 0}` at pc `0x0226bb86` -- from the pool word `0x0213dd98`, which is **autoload_2 `.data`**
(`0x02138f80..0x0213fdc0`) and whose ROM bytes are `00000000 00000000`, mwcc's static NULL member
pointer. So `func_ov068_0226bb3c` is a state enter that UNBINDS the draw member, and the null the
draw slot sees is the ROM's own value, not a lost write
[E: docs/log/cycle41-gameplay.md VILLAGER42, `v42-W2`; S: extract/adm-kr/arm9/unk_autoload_2.bin
+0x55558, config/adm-kr/arm9/delinks.txt]. A load watchpoint on the vtable's slot 0
(`0x022771c0`) fires at pc `0x01ffd4a0`, so the dispatcher does fetch and run the derived init
[E: `v42-W2`]. Neither `villdraw.c` nor `villbind.c`/`villspawn.c` is in the interpreter registry
-- `port/shim/game/` is not a `SERVICE_DIRS` entry -- and `FS_StartOverlay` runs no relocation
pass on this path, so every one of those three words is ROM data as shipped
[S: port/tools/interp_registry.py, port/shim/fs/ovlreloc.c].

**This retracts GAMEPLAY42's "the 8-byte copy never reached the object".** That claim came from
two `ACWW_INTERP_PEEK` readings; the watchpoint shows the copy arriving twice
[E: docs/log/cycle41-gameplay.md VILLAGER42].

The two actors are LIVE, WALKING NPCs. The manager at `0x021d1d4c` holds `{0x022a8f48, 0xe000}`
and `{0x022a8528, 0xe001}`, and `actor + 0x5c` -- the object's own `VecFx32` -- moves between
runs: villager 0 reads `(79.000, 0.125, 95.000)` at frame 55,600, `(83.000, 0.125, 111.00)` at
60,600 and `(87.510, 0.125, 78.130)` at 68,200, with `+0x68` one step behind it; villager 1 walks
the same way near `x = 149..159, z = 83..95`. Both stay at ground level `y = 0.125`
[E: docs/log/cycle41-gameplay.md VILLAGER42, `v42-P1`, `v42-V4`, `v42-V5`]. The
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
ORACLE50 O50-3; runs `p50-door`, `e50-door`, `p50-enter`, `e50-enter`]. Only TWO villagers are
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
speech [E: `docs/log/cycle42-save.md` SAVE43, `gp-D2`, `gp-D4`]. **GAMEPLAY44 retracted
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
`port/tools/goto.py` closes the loop [E: `docs/log/cycle41-gameplay.md` NAV42 and GP43-5,
`g43-P2`, `g43-P3`, `g43-T2`, `g43-T3`, `g43-T4`; VILLAGER42 `v42-P4`]

The ORIGINAL shows no villager either over the same timeline: an emulator arm with the same pad
script and the same two-tap town recipe, 20 frames at 49,800..55,500, has the original inside the
same arrival tutorial with the same illustration and no villager in any frame
[O: docs/log/cycle41-gameplay.md VILLAGER42, `scratchpad/villager42/oracle-vill/`]. That is
consistent with both readings above: the ORIGINAL is inside the same hold.

**The historical observations differed about the prompt (STYLE rule 7).**
VILLAGER42 measured that with no `X` in the pad script the illustration is still up 11,900
frames later, and that `X` (mask `0x400`) then `B` clears it
[E: VILLAGER42, `v42-V1`, `v42-V3`, `v42-V4`]. SAVE43's chain had **no `X` row at all** and the
hold released anyway, after which villagers were drawn and could be bumped into
[E: SAVE43, `gp-P1`..`gp-D4`]. GAMEPLAY44's same-town comparison above resolves the clock
confound; the exact arrival event that opens and clears the prompt remains a separate question.

The villager's own draw slot only pushes its SRT into a per-id slot on a service side
(`func_02012214 -> func_0205e954`); the model geometry is submitted by the NPC model
service's own draw slot `func_020500d8` (vtable `0x020dce48` slot 9, object at
`data_021c8184`), one `func_0205510c` per request slot in state 3
[S: func_020500d8 / func_02012214, main, port/shim/game/villmodel.c]. So a villager emitting
zero GX words in its own slot is normal
[S: port/shim/game/villmodel.c]. Once the light manager was repaired the villager draw was
measured emitting `0x8c8`-`0xa20` words a frame
[E: port/BOOT-STATE.md, "Villagers were never missing"].

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
left in those two words [S: port/shim/game/exprpick.c].

A villager approach scan exists for proximity reactions: `func_ov068_02266bac` calls the
ov003 slot-position getter at `0x0222f458`, which reads
`p = 0x022617bc + (idx & 0xf) * 0x25c`, copies the `Vec3` at `p + 0x204` and returns the
signed byte at `p + 0x24d` -- the slot's occupant id, `-1` for empty -- then rejects the slot
when `func_020ea990(pos, out) >= threshold`
[S: func_ov068_02266bac / func_ov003_0222f458, ov068/ov003, port/shim/game/genfix.c]. There
is a parallel six-slot NPC table at `0x0225f76c`, stride `0x24c`
[S: sub_02227638, ov003, port/shim/game/genfix.c].

The ov003 slot machinery that drives all of this only runs once
`__sinit_ov003_02237af4` has constructed the six `0x24c` slot records at `0x0225f76c`; when
that initialiser was skipped the whole per-frame slot pass was dead
[S: __sinit_ov003_02237af4, ov003, port/shim/game/exprpick.c].

Villager houses use four texture sets and two animations, named in ov003's own pool:
`/str/npcHsTex/%c/house_%c%d%c.nsbtx`, `/str/npcHsTex/%c/light_%c%d.nsbtx`,
`/str/obj_house_i.nsbca` and `/str/obj_house_o.nsbca`
[S: ov003 image at 0x02239bf8, 0x02239c1c, 0x02239c40 and 0x02239c58,
port/shim/game/townhouses.c; the same four addresses `town.md` cites].

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

All rows above are S, cited from the shim headers named in the previous table.

## How to check it

The manager occupancy probe is the cheapest check: `port/shim/game/villspawn.c` prints the
eight `{actor, id}` slots at `0x021d1d4c` on every mode change and after each spawn pass, and
`port/shim/game/villpick.c` prints one line per pick (slot, class, villager id)
[S: port/shim/game/villspawn.c, villpick.c]. Both are gated on `ACWW_TRACE_STATE=1`
[S: port/shim/game/villspawn.c].

Note the port-only caveat: on the NATIVE path `func_0207b594` is deliberately a no-op and
prints `villager placement SKIPPED`, so a native run's empty villager table is the port's
decision, not the game's [S: port/shim/game/villagers.c]
[E: docs/log/cycle40-keyboard-gate-probe.md LONG40, "villager placement SKIPPED" at frame
19335]. On the INTERPRETER path the ROM's own `func_0207b594` runs
[S: docs/kb/hybrid/runtime.md via docs/log/cycle40-keyboard-gate-probe.md REG40].

## Hypotheses

- **H: the six classes `func_0207c818` returns are the six personalities (lazy, jock, cranky,
  peppy, normal, snooty).** The index is bounded at 6 and each class has its own draw
  function argument [S: src/matched/func_0207c76c.c]. Experiment: log the class index and the
  drawn villager id for 100 generated towns and check that ids partition into six disjoint
  sets.
- **H: the "seventeen species slots" in `func_0207b594` are species groups (cat, dog, bird
  ...), and `func_0209bcd4` / `func_0209c380` enforce a per-species cap.** The loop nesting
  is 8 x 17 with two permission predicates
  [S: port/shim/game/villagers.c]. Experiment: decompile `func_0209bcd4` and
  `func_0209c380`, then generate 50 towns and count species repeats.
- **H: move-in and move-out are driven by the day-change routine `func_02040c90`, not by the
  villager code.** The generator's own sequence is "generate, then an RTC advance that moves
  villagers in" [S: port/shim/gfx/pmflist.c], and `func_02040c90` is identified as the
  day-change / calendar update [S: port/tools/known_callees.txt]. Experiment: watch the eight
  records at `0x021e5a2c` across an `ACWW_RTC_*` day rollover and see whether any changes.
- **H: friendship is a byte inside the `0x7ec` record, and the expression pick's `a2`
  argument is derived from it.** `func_0204fb80` selects one of several 8-byte records by
  `a2 * 8` inside a per-class table [S: port/shim/game/exprpick.c]. Experiment: instrument
  `func_0204fb80`'s arguments over a long town run and correlate `a2` with any monotonically
  changing byte in the speaking villager's record.
- **H: `data_020cd884`, indexed `param * 0x4e`, is the villager species table with a
  `0x4e`-byte row (name, model, texture, voice).** The stride and the 33-entry bound are
  measured [S: port/shim/game/villagerface.c]. Experiment: dump 33 rows and check for a
  repeating internal structure; cross-check row count against the species count in
  `func_0207b594`'s seventeen slots.
- **H (OPEN, and it is the ranked one): which arrival step gates the villagers, and what
  releases the tutorial hold.** The two chains disagree. VILLAGER42's, driven from
  `st/town48000.st` with a pad script containing no `X`, sat inside the Nintendo-DS illustration
  for at least 11,900 frames with the pad discarded, and pressing `X` then `B` cleared it
  [E: `docs/log/cycle41-gameplay.md` VILLAGER42, `v42-V1`/`v42-V3`/`v42-V4`]. SAVE43's, driven
  from `st/b55400.st` on a later build with no `X` row, was past the hold and had villagers
  drawn, walkable-into and talkable [E: `docs/log/cycle42-save.md` SAVE43, `gp-D2`, `gp-D4`].
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
  applied to [S: port/shim/game/villhouse.c]. Experiment: instrument slot 25's return and
  `func_0207945c`'s second argument on the `tap-D59` town-hall run.

## Related

- `../experiments/gameplay-walkthrough.md` -- both chains, frame by frame, including the SAVE43
  stills in which a villager is drawn
- `town.md` -- the house records are part of the town's save image
- `dialogue.md` -- what a villager says once the talk machine reaches it
- `events-and-calendar.md` -- birthdays and the day-change routine
