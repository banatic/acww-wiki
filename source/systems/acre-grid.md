# Acre grid

**Summary.** The town's ground is one two-dimensional array of acres, and each acre holds up to
two independent 16x16 layers of 16-bit tile ids. Nothing in the game indexes a tile directly:
every read and every write goes through a small family of accessors that takes a world position,
splits it into an acre coordinate and a tile-within-acre coordinate, bounds-checks both, and
hands back a pointer to the two bytes -- or a null pointer, which is the game's normal way of
saying "off the map". One world unit of the split is fixed by two shifts: a tile is `1 << 13`
position units and an acre is `1 << 17`, so an acre is exactly 16 tiles on a side. This page is
the data model those accessors reveal; `town.md` is what the town is made of and where the save
keeps it.

## What happens

The whole family reduces to one composed question, `(grid, position, layer) -> u16 *`. The entry
`func_0204f5a8` takes a grid object, a pointer to a position record and a layer number, zeroes a
four-word scratch array, unpacks the position into it and calls the element accessor with the four
unpacked coordinates [S: func_0204f5a8, main, src/matched/func_0204f5a8.c].

The unpack is two functions. `func_0204f828` is a shape adapter: it calls `func_0204f840` with
four destinations derived from two, `(a, a + 4, b, b + 4, source)`
[S: func_0204f828, main, src/matched/func_0204f828.c]. `func_0204f840` then reads exactly two
words of the source record -- the word at `+0` and the word at `+8` -- and writes four values:
`word0 >> 17` and `word8 >> 17` to the first pair, and `(word0 >> 13) & 0xf` and
`(word8 >> 13) & 0xf` to the second [S: func_0204f840, main, src/matched/func_0204f840.c]. Both
shifts are arithmetic, so a negative coordinate yields a negative acre index, which the element
accessor's unsigned bound then rejects [S: func_0204f5e0, main, src/matched/func_0204f5e0.c].

Reading `+0` and `+8` and never `+4` is what identifies the source record: it is an NNS `VecFx32`,
whose members are `x`, `y`, `z` with `y` vertical, so the grid is indexed by `x` and `z` and the
height word is stepped over [S: func_0204f840, main, src/matched/func_0204f840.c]
[H: the VecFx32 reading is inferred from the two offsets and the SDK's vector layout, not from a
named type in the ROM; the experiment that would settle it is in Hypotheses].

`func_0204f5e0` is the element accessor. It rejects the call unless the acre `x` is below the
grid's width, the acre `z` is below its height and the grid's base pointer is non-null; otherwise
it indexes `base + (x + z * width) * 0x28` and passes that element to the tile fetch
[S: func_0204f5e0, main, src/matched/func_0204f5e0.c]. So an acre is a `0x28`-byte record and the
acre array is row-major with the width as the stride.

`func_02037e0c` is the tile fetch, the innermost body and the only ARM one. It rejects the call
unless the layer is below 2 and both tile coordinates are below `0x10`; then it loads the layer's
pointer from the acre element at `+0x18 + layer * 4`, returns 0 if that pointer is null, and
otherwise returns `layer_base + ((tx + (tz << 4)) << 1)`
[S: func_02037e0c, main, src/matched/func_02037e0c.c]. Two layers, 16x16 tiles, two bytes a tile,
`tz` the row: a layer is 512 bytes and an acre element carries two pointers to them rather than
the tiles themselves, which is why an acre can legally have one layer and not the other.

**The null return is a normal outcome, not an error.** Three separate guards can produce it -- the
acre bound, the tile bound and the layer bound -- and every caller tests the pointer before using
it [S: func_02037e44 and func_02037da8, main, src/matched/func_02037e44.c and
src/matched/func_02037da8.c]. PROMOTE77 measured the share: 64 of 512 recorded calls of
`func_02037e0c` and of `func_0204f5e0` failed a guard and returned 0 without computing an index
[E: docs/log/cycle42-save.md `## PROMOTE77` P77-3].

**The write path is the same walk with a store at the end, and it is a separate family.**
`func_0204f538` takes a tile-space `(x, z)` and does the split in the open -- `x >> 4` for the
acre, `x - ((x >> 4) << 4)` for the tile -- then calls `func_0204f564`
[S: func_0204f538, main, src/matched/func_0204f538.c]. `func_0204f564` repeats
`func_0204f5e0`'s three guards and its `* 0x28` indexing verbatim and calls `func_02037e44`,
which calls the tile fetch, stores one 16-bit value through the returned pointer and returns 1,
or returns 0 if the pointer was null
[S: func_0204f564 and func_02037e44, main, src/matched/func_0204f564.c and
src/matched/func_02037e44.c]. The read and write families therefore share the tile fetch and
nothing else, and the bound logic exists twice.

**`func_02037d14` is the inverse map and it fixes the tile index's direction.** It takes an index
and writes `i & 0xf` and `(i >> 4) & 0xf`, which is exactly the inverse of the tile fetch's
`tx + (tz << 4)` [S: func_02037d14, main, src/matched/func_02037d14.c]. `func_02037da8` uses it:
it fetches tile 0 of an acre layer, scans forward through all `0x100` tiles for the first id in a
caller-supplied `[lo, hi]` range, and converts the hit's index back to a coordinate pair
[S: func_02037da8, main, src/matched/func_02037da8.c]. That scan is also the second, independent
statement that one layer is 256 contiguous tiles.

**The grid object carries two sizes, in two different units, and mixing them is a real trap.**
`func_0204f5e0` and `func_0204f564` read the width and height at `+4` and `+8` and compare them
against ACRE coordinates [S: func_0204f5e0, main, src/matched/func_0204f5e0.c]. The map sweep
`func_02046df4` reads a size pair at `+0xc` and `+0x10` and iterates it in TILE coordinates,
deriving the acre coordinate as `x >> 4` and the tile coordinate as `x - ((x >> 4) << 4)` for
each [S: func_02046df4, main, src/matched/func_02046df4.c]. The two pairs are therefore in a 16:1
relation and are not interchangeable.

**This is what the town costs every frame, not what a dialogue costs.** PROMOTE77 measured the
five accessors at 7.22% of the interpreted steps of a 1,200-frame villager-conversation window,
and measured a quiet window with the dialogue box CLOSED dropping MORE (8.15%) than the
conversation window (7.63%) when they were promoted, because the conversation dilutes them with
font work [E: docs/log/cycle42-save.md `## PROMOTE77` P77-6/P77-7]. The boot's frame-58 map sweep
runs `func_0204f5e0` and `func_02037e0c` 43,613 and 43,642 times in that one frame
[E: docs/log/cycle42-save.md `## PERF72` P72-6, re-measured in `## PROMOTE77` P77-2].

## Where it lives

| function or symbol | module | role | grade/citation |
|---|---|---|---|
| `func_0204f5a8` `0x0204f5a8` | main | the ENTRY: zero four words, unpack a position into them, call the element accessor | [S: src/matched/func_0204f5a8.c; the port links `port/build/shadow/func_0204f5a8.c`, which differs -- see Hypotheses] |
| `func_0204f828` `0x0204f828` | main | the two-corner shape adapter: four destinations from two | [S: src/matched/func_0204f828.c] |
| `func_0204f840` `0x0204f840` | main | the UNPACK: two words of the position record into acre x/z and tile x/z | [S: src/matched/func_0204f840.c] |
| `func_0204f5e0` `0x0204f5e0` | main | the ELEMENT accessor: three guards, `(x + z * width) * 0x28` | [S: src/matched/func_0204f5e0.c] |
| `func_02037e0c` `0x02037e0c` | main, ARM | the TILE fetch: three guards, the layer pointer, two bytes per tile | [S: src/matched/func_02037e0c.c] |
| `func_0204f538` `0x0204f538` | main | the write path's split: tile space to acre + tile | [S: src/matched/func_0204f538.c] |
| `func_0204f564` `0x0204f564` | main | the write path's element accessor, `func_0204f5e0`'s guards repeated | [S: src/matched/func_0204f564.c] |
| `func_02037e44` `0x02037e44` | main | the write path's STORE: one `u16` through the fetched pointer, 1 or 0 | [S: src/matched/func_02037e44.c] |
| `func_02037d14` `0x02037d14` | main | the inverse map: tile index to `(x, z)` | [S: src/matched/func_02037d14.c] |
| `func_02037da8` `0x02037da8` | main | scan a whole layer for the first tile id in a range | [S: src/matched/func_02037da8.c] |
| `func_02046df4` `0x02046df4` | main | the MAP SWEEP: both layers, every tile, one id range rewritten | [S: src/matched/func_02046df4.c] |
| `func_0204f260` `0x0204f260` | main | the other user of the unpack: same four words, a different consumer (`func_0204f2b8`) | [S: src/matched/func_0204f260.c] |

**Who calls them, counted rather than sampled.** From the delinker's own reloc table: the element
accessor `func_0204f5e0` has 87 distinct call-site owners, the tile fetch `func_02037e0c` has 14
(one of which is the element accessor), the entry `func_0204f5a8` has 5, the shape adapter has 3
and the unpack has exactly 1 -- its adapter
[E: scratchpad/promote90/callers.txt, produced by scratchpad/promote90/callers90.py over
config/adm-kr/arm9/relocs.txt]. The 87 are concentrated in `0x02042d14`..`0x0204abc8` and
`0x0205a65c`..`0x0205bc60`, two contiguous bands of the `main` module; the entry's five callers
are all in `0x0200ab44`..`0x0200dc98` plus `func_020953e4`, a different band again. So the entry
is the position-driven front door used by a handful of systems, and the element accessor is the
one everything else reaches directly with coordinates it already has.

## Data it reads and writes

| address or field | meaning | who writes | who reads |
|---|---|---|---|
| grid `+0x00` | base pointer of the acre array; null means "no map" | not established here | `func_0204f5e0`, `func_0204f564` [S: src/matched/func_0204f5e0.c] |
| grid `+0x04` | acre-array WIDTH, in acres, and the row stride | not established here | `func_0204f5e0`, `func_0204f564` [S: src/matched/func_0204f5e0.c] |
| grid `+0x08` | acre-array HEIGHT, in acres | not established here | `func_0204f5e0`, `func_0204f564` [S: src/matched/func_0204f5e0.c] |
| grid `+0x0c`, `+0x10` | the same extent in TILES, 16x the acre pair | not established here | `func_02046df4` [S: src/matched/func_02046df4.c] |
| acre element, stride `0x28` | one acre; `+0x00`..`+0x17` is not read by this family | not established here | `func_02037e0c` [S: src/matched/func_02037e0c.c] |
| acre element `+0x18`, `+0x1c` | the two layer pointers, layer 0 and layer 1; either may be null | not established here | `func_02037e0c` [S: src/matched/func_02037e0c.c] |
| layer block, `0x200` bytes | 256 `u16` tile ids, index `tx + tz * 16` | `func_02037e44`, `func_02046df4` | `func_02037e0c`, `func_02037da8` [S: src/matched/func_02037e0c.c, src/matched/func_02037d14.c] |
| position record `+0x00`, `+0x08` | the `x` and `z` of a `VecFx32`; bits 13..16 are the tile, bits 17 and up the acre | not established here | `func_0204f840` [S: src/matched/func_0204f840.c] |
| tile ids `0x1531`..`0x153a` | the ten ids the boot's map sweep rewrites to `0x154a` + the offset | `func_02046df4` | `func_02046df4` [S: src/matched/func_02046df4.c] |

**The `0x28`-byte acre element's first `0x18` bytes are NOT described by this family and this page
does not guess at them.** Nothing in the five accessors, the three write-path bodies or the two
scan bodies touches an offset below `0x18`.

## How to check it

The cheapest live check is the promotion recorder, which logs every load and store of a chosen
function with its address, and therefore prints the strides above directly rather than by
inference. Record the tile fetch from the boot's map sweep, which is where it runs tens of
thousands of times a frame:

    python -B scratchpad/promote90/rec90.py tilefetch 0x02037e0c 256 --scene boot
    python -B scratchpad/promote90/dumprec90.py scratchpad/promote/tilefetch/tilefetch.rec --summary

Expect: every record `hostcalls=0 flags=0x00000000 steps=14`, and the distinct load addresses
falling into `0x18`-and-`0x1c` pairs per acre element with the layer reads `0x200` bytes apart
[E: the same instrument produced scratchpad/promote90/events-summary.txt for a different function
this way]. Read `docs/kb/hybrid/promotion.md` section 1 before arming it; a recorded LOAD carries
its address and width and NOT its value, so a check written against load VALUES will silently read
zero [E: port/interp/interp_cpu.c `REC_LOAD`, measured in docs/log/cycle42-save.md `## PROMOTE90`].

The static check is `scratchpad/promote90/callers90.py`, which resolves every reloc that targets
an address to the symbol that owns the call site; it is the only complete caller list, because a
scan of `src/matched/` sees only the bodies that happen to be matched.

## Hypotheses

- **The position record is a `VecFx32`.** The evidence is two offsets (`+0` and `+8`) and the
  SDK's member order, not a named type. Settle it by recording `func_0204f840` with the promotion
  recorder from the conversation scene and checking that the word at `+4` of the source is never
  loaded, across 512 calls from two scenes.
- **The acre element's first `0x18` bytes.** Unknown. Settle it by recording one of
  `func_0204f5e0`'s 87 callers and listing the offsets it touches on the pointer the accessor
  returned, which is the same element.
- **`src/matched/func_0204f5a8.c` and `port/build/shadow/func_0204f5a8.c` are different
  programs.** The matched body is `void` and drops the element pointer its tail call returns; the
  shadow returns it, and the port links the shadow. Both are byte-exact for the ROM's tail branch,
  so the bytes cannot decide it -- this is **D2**, and PROMOTE77 measured that the differential
  check reports the dropping body as AGREEING on 512 of 512 calls
  [E: docs/log/cycle42-save.md `## PROMOTE77` P77-4]. Settle which one the ROM's callers want by
  reading what the five callers of `func_0204f5a8` do with `r0` on return.
- **Whether the acre width is ever not 6.** `town.md` describes a 96x96 tile grid, which would be
  6x6 acres of 16x16 tiles, but this family reads the width out of the grid object every call and
  never assumes it. Settle it by recording `func_0204f5e0` and reading the `+4` load's value --
  which, per the recorder caveat above, means a store-side or census-side instrument rather than
  the load log.

## Related

- [`town.md`](town.md) -- what the town is made of, where the save keeps it, and the cylinder
  world the grid is drawn as
- [`villagers.md`](villagers.md) -- the actors that move over it
- `docs/kb/hybrid/promotion.md` -- how these five bodies were put on the interpreter's hot path,
  and what the differential check does and does not prove
- `docs/log/cycle42-save.md` `## PROMOTE77` -- the promotion that measured the family's cost, and
  `## PROMOTE90`, which opened this page
