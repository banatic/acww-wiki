# Town

**Summary.** The town is a 96x96 tile grid of acres, generated once when a new save is made
and then stored in the save image rather than re-derived from a seed. The grid holds items:
buildings, house plots, trees and the empty marker, all as 16-bit ids in a layer beside the
acre bytes. The 3D world the player walks is that grid wrapped onto a cylinder, one acre
every 32 units, which is why the horizon rolls away like a log. The town's own name is typed
by the player at the second keyboard screen; a default name is stamped at generation time and
overwritten when the player answers.

## What happens

The save image lives at `0x021dc7a8` and is `0x173fc` bytes long, copied there by
`func_020b5724`'s `MI_CpuCopy8` [S: func_020b5724, main, port/shim/game/newgameprobe.c].
Inside it the acre-map object is at `+0xd304` (`0x021e9aac`) and the eight villager house
records at `+0x9284` (`0x021e5a2c`), stride `0x7ec`
[S: func_02085a30, main, port/shim/game/villspawn.c] [S: port/shim/game/newgameprobe.c].
The image's validity record sits at `+0x173f8` (`0x021f3ba0`); `func_0209f180` requires its
`+2` byte to be 2 while byte 0 of the image must be `0x32`
[S: func_0209f180, main, port/shim/game/newgameprobe.c].

A boot with no usable save generates a town without any menu. `func_020b5898` polls both
flash banks through `func_020a1a40`, `func_020b5724` writes the verdict to its object's
`+0x5e`, and `func_020b56a8` reads it; verdict 1 or 4 means "no usable save"
[S: func_020b5898/func_020b56a8, main, port/shim/game/newgameprobe.c]. That arm calls
`func_0209ef7c` -- an `MI_CpuFill8` of the whole image, four player-slot inits and 28
sub-initialisers -- and then `func_0209e6ec(save, 3)` = `func_0209ebec`, which builds the
TERRAIN and stamps a default town name
[S: func_0209ef7c/func_0209ebec, main, port/shim/game/newgameprobe.c]. `func_0209ebec`
deliberately writes no player state, because no player exists yet, and ends by setting the
validity byte back to 0 [S: func_0209ebec, main, port/shim/game/newgameprobe.c].

**The town is generated TWICE on the new-game path, and the second time is 11,346 frames after
the town id is drawn.** MEASURED on both producers: the boot generation lands at port frame 758 /
emulator frame 175 (inside the 280-draw initialiser burst), the whole map is then RESET to `0x86`
/ `0xfff1`, the town **id** is drawn at the name confirmation (port frame 24,789, draw #2,667),
and the REAL acre map, item layer and villager roster are all written in ONE later frame -- port
**36,135**, draw index 3,782 -> 4,014 in that single frame
[E: docs/log/cycle41-gameplay.md ORACLE49 O49-1/O49-2]. The acre bytes are written at pc
`0x0204ea54` with `lr 0x0204e735` = `func_0204e728` at the real generation and `lr 0x0209efc5` =
`func_0209ef7c` at the boot one [E: ORACLE49 O49-1, `ACWW_INTERP_WATCH` + `WATCH_LR=1`].

**The generator is FAITHFUL in the port**: given the same stream position at the layout draw, the
port writes the original's map. Two independent checks -- the boot town `0xd391`, where both
producers draw from index 0..280 with no recipe at all (**4,617 compared words, 0 differ**), and
the confirmed town `0x8365` under ORACLE47's forward shared recipe (**2,057 map words, 1
differs**, and that one is a loose item `0x1555` twelve thousand frames of live play later)
[E: docs/log/cycle41-gameplay.md ORACLE49 O49-3/O49-4]. **ORACLE50 re-took the forward tap
window on a later build (it lands in the same three frames, `24,907..24,909`) and read the
roster on BOTH producers rather than slot 0 alone: all eight slots agree,
`6b 5e 84 ff ff ff ff ff`, and so do all SEVENTEEN building cells of `0x8365`, tile for tile --
town hall (72,36), villager houses (61,67) (28,35) (68,20), gate (39,16), Able Sisters (26,24),
Nook (21,25), museum (23,58), the player's house (73,53), the sign (67,38) and seven `0x500a`
plots** [E: docs/log/cycle41-gameplay.md ORACLE50 O50-1].

**The generator agrees when the layout draw starts at the same stream position:**
the boot town `0xd391` has 4,617 compared words with 0 differences
[E: `scratchpad/oracle49/RECEIPTS.md`; log: `docs/log/cycle41-gameplay.md` O49-3].
In the confirmed town `0x8365` under the forward recipe, 2,057 map words have 1 difference
at frame 48,000; the 36 acre bytes and all seventeen building cells agree, with the town hall
at (72, 36) on both producers [E: `scratchpad/oracle49/RECEIPTS.md`; log:
`docs/log/cycle41-gameplay.md` O49-4].
The differing word is a loose item `0x1555`, recorded twelve thousand frames of live play
after generation, rather than a generated building or acre difference
[E: `scratchpad/oracle49/RECEIPTS.md`; log: `docs/log/cycle41-gameplay.md` O49-4].

**A shared id under the inverse recipe is not a shared layout:** EXIT48 found the town-hall
doormats at (40,38) on the port and (40,22) on the armed inverse original, with each producer
recording its own entry position at frame 38,838 and replaying it on exit
[E: `scratchpad/exit48/RECEIPTS.md`; log: `docs/log/cycle41-gameplay.md` X48-2, X48-3, X48-4].
The sixteen tiles therefore describe two town layouts, not a misplaced player in one layout;
ORACLE49 located the inverse recipe's discrepancy at the layout burst, entering at index
3,780 on the armed original and 3,782 on the port [E: `scratchpad/exit48/RECEIPTS.md`,
`scratchpad/oracle49/RECEIPTS.md`; log: `docs/log/cycle41-gameplay.md` X48-4, O49-2].

The generator proper is handler 2 of the town dispatcher `func_0209e6ec`: terrain through
`func_0204e728`, the default town name, then an RTC advance that moves villagers in and a
post-generation sync mirroring `func_020a1038`'s save-erase path
[S: func_0209e6ec, main, port/shim/gfx/pmflist.c]. The pair `func_020a1320` /
`func_020a13e8` is NOT the generator, which cost a session to establish: `func_020a1320`
only sets the new-game-pending word at `0x021f3c30` to 1, and `func_020a13e8`'s state-1
branch RESETS the map -- every acre byte to `0x86` and every item to `0xfff1`
[S: func_020a1320/func_020a13e8, main, port/shim/gfx/pmflist.c]. `0xfff1` is the empty
item/tile id throughout the ROM [S: docs/kb/modules/overlays-ov0xx.md].

Cell writing during generation goes through a four-function idiom: `func_0209c618` performs
twenty nested `setv(cell(self, x, y), k)` statements and then three loops, where `cell` is
`func_0209cc30`, `setv` is `func_0209d01c`, `getv` is `func_0209d030` and the rejection test
is `func_02037b14` [S: func_0209c618, main, port/tools/known_callees.txt].

**Where the map is in the save image, and how a tile maps to an address.** The acre map object at
save `+0xd304` (`0x021e9aac`) is **36 raw acre bytes**, 6x6, and the ITEM LAYER follows it at save
`+0xd328` (`0x021e9ad0`). **The item layer covers only the INNER 4x4 acres** -- 4x4 acres of 16x16
halfwords is exactly 4,096 halfwords / 8,192 bytes, so it holds tiles 16..79 on both axes and the
border acres carry no item block at all:

    idx  = (addr - 0x021e9ad0) / 2
    tile = (16 + 16*((idx//256) % 4) + (idx%256) % 16,
            16 + 16*((idx//256) // 4) + (idx%256) // 16)

MEASURED: that arithmetic run over the port's control town `0xc66e` reproduces every one of the
nine building rows in the door table below -- town hall (40, 36), museum (71, 26), Nook (22, 52),
and the rest -- from a snapshot taken INDOORS, with no live field
[E: docs/log/cycle41-gameplay.md ORACLE49 O49-0, `scratchpad/oracle49/savemap.py`]. This is the
reader to use when the question is what the GENERATOR produced: `navigate.py --list` needs the
live field at `0x021c80bc` and answers about the room the player is standing in.

Items are 16-bit ids in the map layer. Measured in a generated town's bank 0: fifteen items,
including the shop `0x500d`, eleven house spots `0x500a`, and `0x5014`
[E: port/BOOT-STATE.md, fifth pass 2026-08-27]. The house placer `func_0207bbb8` runs a
96x96 scan and converts one `0x500a` spot per pass into a villager house `0x5001`..`0x5008`
[S: func_0207bbb8, main, port/shim/game/houseplace.c]
[E: port/BOOT-STATE.md, fifth pass 2026-08-27]. The write goes
`func_0207bbb8 -> func_0204e404 -> func_0204ef24(grid, item, x, y)`, and `func_0204ef74` is
the multi-tile placer that lands a house occupying more than one cell
[S: func_0204e404/func_0204ef24, main, port/shim/game/genfix.c]
[S: func_0204ef74, main, port/BOOT-STATE.md sixth pass].

Reading a tile back is a two-step lookup. `func_ov003_02227394` takes a world position and
returns the tile's x and z as `fx32` (the stored byte, `<< 12 >> 4`) plus its kind byte,
returning 1 only when a record was found and its kind is non-zero
[S: func_ov003_02227394, ov003, port/shim/game/fieldtile.c]. The record lookup
`func_ov003_022273f8` splits the tile word into a 4-bit group (bits 12-15) and a 12-bit
index, walks the 8-byte descriptors at `0x02236b0c` until one whose group byte (`+4`)
matches and whose count halfword (`+6`) exceeds the index, and computes the record as that
descriptor's base pointer plus `3 * index`; a record whose first byte is zero is rejected
[S: func_ov003_022273f8, ov003, src/matched/func_ov003_022273f8.c]. Records are therefore
three bytes wide [S: func_ov003_022273f8, ov003, src/matched/func_ov003_022273f8.c].

Tile kinds are classified by a nine-term predicate that recurs across modules with the same
constant set in the same order: `0x26-0x2a`, `0x5d-0x61`, `0x2f-0x56`, `0x57-0x5b`,
`0x66-0x68`, `== 0x69`, `0x6a-0x6c`, `== 0x6d`, `0xc8-0xcf`
[S: func_ov003_0220cd84 / func_ov072_022792e4, ov003/ov072, docs/kb/modules/overlays-ov0xx.md].
Fourteen functions ROM-wide carry that set, so it is the town's tile taxonomy rather than
one function's private table
[S: docs/kb/modules/overlays-ov0xx.md, membership sweep over every ov003 target >= 0x40].

The world is drawn as a CYLINDER, which is the source of the game's rolling-log horizon: a
tile is 2.0 units, an acre 32.0, and each acre object is placed at
`Translate(col * 32, 0, 0)` composed with `RotX(row * 0x2999)`, with the camera rolled into
the same frame by `func_0203f844` under a per-mode `ov006` flag
[S: func_0203f844, main, port/BOOT-STATE.md sixth pass] [E: port/BOOT-STATE.md, ~6,269
opaque pixels on the 3D layer]. Per-acre render objects are built by
`func_ov003_0221f270`, whose column translate is `a2 * data_020ca0ec`
[S: func_ov003_0221f270, ov003, port/shim/game/acresetup.c].

Acre ground textures come from the file system as `/bg/t%d/%04x.nsbtx`, turned into a texture
handle by `func_021077e8` -- the same conversion `func_02037608` performs at `0x020376f4`
[S: func_ov003_0221fe34, ov003, port/shim/game/townsetup.c]. The town scene's registrars are
`func_ov003_0221fe34` (the third call in `func_ov003_022207e0`, handler 196's init slot),
`func_ov003_0221ffec`, and `func_ov003_0221d76c`
[S: ov003, port/shim/game/townsetup.c, townhouses.c, townhouse3.c]. The second registrar's
literal pool at `0x022200f0` names the buildings' assets directly:
`/str/npcHsTex/%c/house_%c%d%c.nsbtx`, `/str/npcHsTex/%c/light_%c%d.nsbtx`,
`/str/obj_house_i.nsbca` and `/str/obj_house_o.nsbca` -- four villager-house textures and
lighting plus the two house open/close animations
[S: ov003 image at 0x02239bf8/0x02239c1c/0x02239c40/0x02239c58,
port/shim/game/townhouses.c].

`ov003` is the outdoor scene module and names its own subject through its literal pool: the
whole `/fg/` tree (`/fg/tree/cedar_mdl/`, `/fg/grass/{grassA-D,clover,redTurnip}`,
`/fg/flower/{tulip,pansy,cosmos,rose,suzuran,rafflesia}`, `/fg/hole/`, `/fg/stone/`), the
player houses (`/str/plHsTex/home%c%c.nsbtx`), the ground (`m_grd_riv`, `m_grd_sea085`),
signboards, fish and insects [S: ov003 pool words, docs/kb/modules/ov003-068.md].

At runtime the town is a channel. The channel handler table pointer is `0x021fd044`; the
town's channel is `0x22`, and the ROM's dispatcher `func_020edc58` reads
table -> entry -> `[entry]` -> `blx` [S: func_020edc58, main,
docs/log/cycle40-keyboard-gate-probe.md CHAN40]. The ground is channel `0x0d` and the town
scene opens `0xc4 -> 0x0f -> one 0xbd per building`
[E: port/BOOT-STATE.md, sixth pass]. Channel 189 is the SNOWMAN, not the town renderer, and
a long line of work rested on the misidentification
[E: port/BOOT-STATE.md, bind log `/snowman/snowball1.nsbmd` id 0x022383ac].

On the interpreter path a scripted run reaches the town at frame 37,500: the player stands in
front of the town hall while the driver delivers his last line, with overlays 5, 36, 54, 120
and 117 loaded [E: docs/log/cycle40-keyboard-gate-probe.md TOWN40, `tap-D56` frame 37500].
The Korean name of the town hall on screen is `마을사무소`
[E: docs/log/cycle40-keyboard-gate-probe.md LONG40, the five-option destination menu].
The town's top screen is engine B in mode 1 with BG3 affine (`BG3CNT = 0x6f02`) -- the sky --
and once affine backgrounds were drawn the clouds appeared over the town hall
[E: docs/log/cycle40-keyboard-gate-probe.md SKY40, `tap-D57` frame 37800].

## Walkability: the acre template's collision map

Each acre entry's `+0x20` points at the LOADED ACRE TEMPLATE, shared between every acre of the
same id, and the template's `+0x0c` is that acre's `bcl` file: **256 bytes of a 16x16 TILE KIND
map, then 128 bytes of 16x16 nibbles**. The acre's resource is a NARC whose `BTNF` names its
two members `bmd0` and `bcl0` and whose `BTAF` puts the second at `[0x384, 0x504)` -- 384
bytes, i.e. 256 + 128 [S: port/tools/navlib.py] [E: docs/log/cycle41-gameplay.md NAV42]. So
the town's collision is a per-acre 16x16 byte map indexed by the acre id, and the 96x96 grid is
those 36 maps laid side by side. A tile is **2.0 world units**: an acre origin at `acre+0x0c`
is `gx * 0x20000` = 32.0 units, over 16 tiles [S: port/tools/navlib.py].

The kinds, MEASURED by flood fill over the reference town and then checked against the map
screen [E: docs/log/cycle41-gameplay.md NAV42]:

| kind | what it is | walks? |
|---|---|---|
| `0x03` `0x04` `0x09` `0x17` `0x1d` `0x1e` | grass, house plot, the second grass shade, seams | yes |
| `0x1f`..`0x57` | slopes, ramps, bridge decks, the beach | yes |
| `0x08` | the sea | no |
| `0x0a` | a building's footprint | no |
| `0x0b`..`0x14` | the river | no |
| `0x15` | outside the town (the border acres are all `0x15`) | no |

On the reference town that is **3,256 walkable tiles in one component of 3,214**, containing
the player and every door; the other two components are 41 tiles and 1 tile
[E: docs/log/cycle41-gameplay.md NAV42, `scratchpad/nav42/RECEIPTS.md`]. The ITEM layer blocks
on top of the kind: a building id `0x5000..0x5021`, and the tree/rock family the ROM's own
nine-term predicate picks out [S: src/matched/func_ov003_0220cd84.c]. **That predicate tests
the ITEM word, not the kind byte** -- the town's item layer carries `0x002a` 85 times, `0x0053`
32 times, `0x0068` 15 times and `0x0061` 10 times, all inside its bands -- which retires this
page's hypothesis that it partitions water/cliff/path/grass.

**The item layer is also where a shaken tree and its fallen fruit are recorded**, so it is a
live gameplay field and not only terrain. Measured on one town's orange tree across a single
shake, the four words that moved [E: docs/log/cycle42-save.md `## PICKUP43`,
`scratchpad/pickup43/RECEIPTS.md`]:

| id | what it is | grade |
|---|---|---|
| `0x0043` | an orange tree **bearing fruit** (28 of them in that town) | E: the word at the shaken tile before the shake |
| `0x0044` | the same tree **shaken bare** | E: the same word after it |
| `0x1519` | a fallen **orange** (`오렌지`) | E: three appeared on the shake, and the pockets page named slot 0 `오렌지` on the frame the pocket word read `0x1519` |
| `0x002a` | the ordinary, fruitless tree (80 of them) | E: the census above |

**The tile the game acts on when the B button picks an item up is the player's position
ROUNDED to the nearest tile on each axis** -- fx32 `(p + 0x1000) >> 13` -- **stepped one tile
in the facing direction**, which is one tile away from `navlib.Town.player_tile()`'s FLOOR
whenever the player is past a tile's half-way line. Fifteen runs agree and two discriminate
rounding from flooring [E: docs/log/cycle42-save.md `## PICKUP43`, runs `S14` and `S24`].
Whether the ROM rounds elsewhere is not established.

## The doors, and the tile to stand on

A building is a connected component of `0xf030` footprint filler plus its one
`0x5000..0x5021` id cell, and the id says which building it is. There are two shapes
[E: docs/log/cycle41-gameplay.md NAV42]:

- **a NOTCH** -- a walkable tile inside the building's own block of `0x0a`. The doorway is the
  shallowest such tile and the doormat is the tile immediately south of it. The player's house,
  the town hall and the villagers' houses are this shape. The notch is looked for by BOUNDING
  BOX rather than by component, because it does not always carry the footprint item: Nook's
  shop's notch is at the bottom-left corner of its block and carries none.
- **NO notch** -- a solid block entered from the tile below its front wall, where the doormat
  is the component's own southernmost non-`0x0a` cell. The museum and the sign are this shape.

The facing is NORTH either way: every building in the town faces south. The door does not open
by walking into it; it opens on an A press while standing there
[E: docs/log/cycle42-save.md, `gp-D8` vs `gp-D9`], and the last fraction of a tile has to be
hunted for sideways because the doorway is sub-tile
[E: docs/log/cycle41-gameplay.md NAV42, `W1` vs `E1`].

| building | item | anchor tile | stand on | face | citation |
|---|---|---|---|---|---|
| town hall | `0x5000` | (40, 36) | (40, 38) | north | E: map panel (150,172), NAV42 |
| villager house 1-3 | `0x5001`-`0x5003` | (51,60) (61,69) (76,34) | (51,62) (61,71) (76,36) | north | S: this page, `0x5001`..`0x5008`; E: the three blue map icons |
| empty house plot | `0x500a` | 9 of them | -- | -- | one tile, no footprint, no door |
| gate | `0x500b` | (39, 16) | (40, 16) | north | E: the red arch at the top of the map |
| Able Sisters | `0x500c` | (27, 54) | (25, 56) | north | E: the second red building on the west side |
| Nook's | `0x500d` | (22, 52) | (20, 54) | north | S: this page, the shop is `0x500d`; the notch is at the block's bottom-LEFT corner |
| museum | `0x5011` | (71, 26) | (71, 27) | north | E: the white columned icon |
| player's house | `0x5014` | (41, 53) | (41, 55) | north | E: the GREEN legend icon; `gp-D9` entered this building |
| sign | `0x501c` | (35, 38) | (35, 39) | north | E: 2x2, beside the town hall |

The tiles are this town's; the RULE is what transfers, and `port/tools/navigate.py --list`
re-derives the table from any snapshot -- the two towns cycle41's NAV42 generated produced two
different tables. MEASURED, how far that gets a scripted walk: `port/tools/goto.py` reached
five of six targets from one snapshot -- the player's house, the town hall and the museum
entered, and two arbitrary tiles within one tile -- in 46 to 141 seconds each. ~~**Nook's shop
is the standing exception**: the walk arrives at its doormat and the press does not open it.~~
**No longer**: GAMEPLAY43 was inside in five iterations and 90 s, and GAMEPLAY44 in TWO
iterations and 12.4 s from the player's own doorstep, 22 tiles away
[E: docs/log/cycle41-gameplay.md NAV42 arms `U1`..`U6`; GAMEPLAY43 `NK-1`..`NK-5`; GAMEPLAY44
`NOOK-1`, `NOOK-2`].

**THIS TABLE IS COMPLETE, AND THAT ANSWERS THE POST OFFICE (GAMEPLAY44).** `navigate.py --list`
now also prints every building component the door rule produced NO door for, with its item id.
On this town it prints nine, and all nine are `0x500a` -- the empty house plot, which has no
building. So the ten rows above are ALL the `0x50xx` ids the item layer carries: **there is no
eleventh building and none fell through `navlib.BUILDING_NAMES`.** GAMEPLAY43 recorded an
ENVELOPE icon on the map page and inferred a missing post office, posing the choice "either its
item id is missing from the table or its door is not the walkable-notch shape the rule
recognises"; the answer is NEITHER, and a `--list` on any outdoor snapshot re-checks it in a
second [E: docs/log/cycle41-gameplay.md GP44-4, `scratchpad/gameplay44/png/M1-map.png`].

MEASURED (GAMEPLAY44), an eleventh row that is not a building: the villager ACTORS. The manager
at `0x021d1d4c` holds the live NPCs and `--list` prints them with their world positions and the
tile to talk to each from; `goto.py --to actor:<n>` walks to one and presses A. See
`wiki/systems/villagers.md`.

## Where it lives

| function or symbol | module | role | grade/citation |
|---|---|---|---|
| `func_0209ebec` (`func_0209e6ec` idx 3) | main | terrain build + default town name | S: port/shim/game/newgameprobe.c |
| `func_0209ef7c` | main | whole-image fill, 4 player inits, 28 sub-inits | S: port/shim/game/newgameprobe.c |
| `func_0209c618` | main | twenty `setv(cell(...))` cell writes, then three loops | S: port/tools/known_callees.txt |
| `func_0209cc30` / `func_0209d01c` / `func_0209d030` | main | cell address / set value / get value | S: port/tools/known_callees.txt |
| `func_0207bbb8` | main | house placer, 96x96 scan, one spot per pass | S: port/shim/game/houseplace.c |
| `func_0204ef24` / `func_0204ef74` | main | item writer / multi-tile item placer | S: port/shim/game/genfix.c |
| `func_ov003_02227394` | ov003 | world position -> tile x, z, kind | S: port/shim/game/fieldtile.c |
| `func_ov003_022273f8` | ov003 | tile word -> 3-byte record | S: src/matched/func_ov003_022273f8.c |
| `func_ov003_0221f270` | ov003 | per-acre render-object setup | S: port/shim/game/acresetup.c |
| `func_ov003_0221fe34` | ov003 | town scene registrar 1 (`/bg/t%d/%04x.nsbtx`) | S: port/shim/game/townsetup.c |
| `func_ov003_0221ffec` | ov003 | town scene registrar 2 (house textures) | S: port/shim/game/townhouses.c |
| `func_020edc58` | main | channel handler dispatcher | S: docs/log/cycle40-keyboard-gate-probe.md |
| `func_0203f844` | main | rolls the camera into the cylinder frame | S: port/BOOT-STATE.md |

## Data it reads and writes

| address or field | meaning | who writes | who reads |
|---|---|---|---|
| `0x021dc7a8` | save image base, `0x173fc` bytes | `func_020b5724` | everything |
| `0x021e9aac` (save `+0xd304`) | acre map object -- 36 raw acre bytes, 6x6 | `func_0209ebec`; the store is pc `0x0204ea54` under `func_0204e728` | field/render |
| `0x021e9ad0` (save `+0xd328`) | ITEM LAYER, 8,192 bytes = the inner 4x4 acres, tiles 16..79 | the generation burst | field/render, `savemap.py` |
| `0x021e5a2c` (save `+0x9284`) | 8 house records, stride `0x7ec` | `func_0207bbb8` | `func_02085a30` |
| `0x021f3ba0` (save `+0x173f8`) | validity record; `+2` must be 2 | new-game path | `func_0209f180` |
| `0x021f3c30` | new-game-pending mode word | `func_020a1320` | `func_ov051_022610d4` |
| `0x02236b0c` | 8-byte tile-group descriptors | static | `func_ov003_022273f8` |
| `0x021c80bc` | field context pointer | field init | `func_0204f5e0` |
| `0x021c526c` | field-data pointer; structure at `+0x2d0` | `func_02034d14` | `func_02035dcc` |
| `0x021fd044` | channel handler table pointer | scene setup | `func_020edc58` |
| `data_020ca0ec` | acre column stride multiplier | static | `func_ov003_0221f270` |

Grades: the save offsets are S [port/shim/game/newgameprobe.c]; `0x02236b0c` is S
[src/matched/func_ov003_022273f8.c]; `0x021c526c` is S [port/shim/game/fieldptr.c];
`0x021fd044` is S+E [docs/log/cycle40-keyboard-gate-probe.md CHAN40].

## How to check it

The town recipe, receipted, is the reference run. Custom START9000 keys, `ACWW_INTERP=1`,
`ACWW_TOUCH` (221,181) `AT` 6900 `EVERY` 60 `REPEAT` 2, `ACWW_TOUCH2` (221,181) `AT` 24600
`EVERY` 60 `REPEAT` 2, stop 48,000; shots every 1,500 frames. Frame 37,500 shows the player
in front of the town hall and frame 37,800 the sky with clouds
[E: docs/log/cycle40-keyboard-gate-probe.md TOWN40/SKY40/RECEIPT41, runs `tap-D56`,
`tap-D57`, `town-R1`].

To check the grid rather than the picture, read the save image at `0x021e9aac` for the acre
bytes and scan the item layer for `0x500a` (house spot), `0x500d` (shop) and
`0x5001`..`0x5008` (villager houses) after generation; `0xfff1` is empty
[E: port/BOOT-STATE.md, fifth pass].

## Hypotheses

- **H: the town layout is chosen from a small set of canned acre arrangements rather than
  generated cell by cell.** `func_0209c618`'s shape -- twenty literal `setv(cell(x, y), k)`
  statements followed by three loops -- reads like a template stamp with a loop-driven
  variation pass, not a procedural generator [S: port/tools/known_callees.txt]. Experiment:
  read `func_0204e728` and `func_0209c618` and record which of the twenty constants are
  literal and which come from a roll; then generate three towns with different RNG seeds and
  diff the acre bytes at `0x021e9aac`.
- **H: the acre byte `0x86` written by the reset is "unset", not a real acre.** The reset
  fills every acre with `0x86` and every item with `0xfff1`, and `0xfff1` is known to be the
  empty id [S: port/shim/gfx/pmflist.c] [S: docs/kb/modules/overlays-ov0xx.md]. Experiment:
  after a real generation, count how many acre bytes are still `0x86`; if zero, `0x86` is the
  sentinel.
- **RETIRED, NAV42: the nine-term tile predicate does not partition tiles into water / cliff /
  path / grass classes -- it tests the ITEM word and picks out the tree and rock family.**
  `func_ov003_0220cd84` reads its operand through `func_0204f5e0(..., layer 0)`, which is the
  item layer, and the town's item layer carries `0x002a` 85 times, `0x0053` 32, `0x0068` 15 and
  `0x0061` 10 -- all inside its bands, all trees on the map screen
  [S: src/matched/func_ov003_0220cd84.c] [E: docs/log/cycle41-gameplay.md NAV42]. The terrain
  classifier is a different thing entirely and is the acre template's `bcl` map, above.
- **H: the town name is stored in the save image as a fixed-length UTF-16 field near the
  validity record.** `func_0209ebec` stamps a default name at generation time and the second
  keyboard overwrites it [S: port/shim/game/newgameprobe.c]
  [E: docs/log/cycle40-keyboard-gate-probe.md TOWN40]. Experiment: run the town recipe twice
  with different typed names, diff the two save images byte for byte, and the differing span
  is the field.
- **H: the eleven `0x500a` house spots are the town's full set of legal house plots and the
  placer picks eight of them.** Eleven spots were measured against eight house records
  [E: port/BOOT-STATE.md, fifth pass] [S: port/shim/game/villspawn.c]. Experiment: log every
  `0x500a` coordinate at generation and every `0x5001`..`0x5008` coordinate after the placer
  finishes; the second set should be a subset of the first.
- **H: acres stream from the file system per row as the camera rolls, rather than all at
  once.** The kb records "acre archives streaming" during generation
  [E: port/BOOT-STATE.md, fifth pass]. Experiment: count `/bg/t%d/%04x.nsbtx` opens per
  1,000 frames on `tap-D56` between 37,500 and 48,000.

## Related

- `villagers.md` -- the eight house records and who lives in them
- `weather-and-seasons.md` -- the sky row and the seasonal texture variants
- `player.md` -- the player array in the same save image
- `dialogue.md` -- the town hall conversation the recipe reaches
