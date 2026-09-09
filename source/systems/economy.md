# Economy

**Summary.** This is the least-read system on the wiki, and the page says so rather than
inventing mechanics. What is established is the shape of the thing money is spent on: an item
is a 16-bit id whose TOP NIBBLE is its category, `0xfff1` is "no item", and a whole family of
comparison routines shared across the shop and menu overlays exists to test those ids. Bells,
prices, the turnip market and the catalogue have not been read out of the ROM yet. Everything
about them below is a Hypothesis with the function family to read and the experiment to run.

## What happens

An item is a 16-bit id stored in the map's item layer, and the empty slot is `0xfff1`
[S: func_020a13e8, main, port/shim/gfx/pmflist.c] [S: docs/kb/modules/overlays-ov0xx.md].
That value is not a magic number local to the map: it is the ROM's empty item/tile id
generally, and grepping for it selects functions in the item domain rather than functions
using one construct -- a claim this repo made wrongly once and then measured properly
[S: docs/kb/modules/overlays-ov0xx.md, retraction 2026-09-02].

The top four bits of the id are its CATEGORY. The placement gate `func_0204bcf8 ->
func_0204bcdc` accepts a cell only when `(*(u16 *)cell >> 12)` is 3 or 4; `0xfff1`'s nibble is
`0xf`, so an untouched map refuses all 256 cells of a room
[S: func_0204bcdc, main, docs/kb/port/sequencer-and-modes.md]
[E: docs/kb/port/sequencer-and-modes.md, `cells[0..7] = fff1 ...`, 256 refused, channel `0x37`
never opens]. Town fixtures use the `0x5xxx` band: `0x5001`..`0x5008` are the eight villager
houses, `0x500a` a house plot, `0x500d` the shop, and `0x500e`/`0x500f`/`0x5010` are the keys
the flythrough camera cycles through before it hits the shop
[E: port/BOOT-STATE.md, fifth and sixth passes].

Comparing two item ids is a shared routine, `func_0204bcdc` / `func_0204bc64`, which recurs
across `ov049`, `ov050`, `ov052` and `ov079` -- twelve times inside a single function in one
case -- with `src/matched/func_ov052_02261054.c` as the reference implementation
[S: docs/kb/modules/overlays-ov0xx.md]. Those four overlays are the shop and menu band: the
overlay-set table `data_020df5ec` covers overlays 90-146 and is described as shops/menus
[S: data_020df5ec, main, docs/kb/port/sequencer-and-modes.md]. `ov050` is specifically Nook's
side of the arrival sequence -- it is one of only two places in the matched tree that clear the
player's arrival event flag [S: func_ov050_02262628, ov050, port/shim/game/spnpc.c].

There is an eight-way item-category classifier in `ov003` with three known members
(`func_ov003_02220e20`, `func_ov003_022223bc` matched, `func_ov003_0220c57c` unattempted), all
sharing the identical constant set in the same chain order: `0x6-0xb`, `0xc-0x11`,
`0x12-0x19`/`0x1c`, `0x8a-0x8f`/`0x90-0x95`/`0x96-0x9b`/`0x9c-0xa3`/`0xa5`, `0x1a`, `0xa4`,
`0x1d` [S: docs/kb/modules/overlays-ov0xx.md]. Eight flags, eight categories, over ids in the
low byte range -- so the low byte carries a sub-type the nibble does not
[S: docs/kb/modules/overlays-ov0xx.md].

Nothing writes an interior's item grid on any path the port has run. The writer is
`func_02037e44` with map-level front door `func_0204f564`; of its three callers ROM-wide, the
third (`func_ov004_0224522c`) is dark ov004 code with no matched file, no shim and not even a
stub, reachable only through the vtable word at `ov004 0x022567c8` in a class whose channel
band (`0x51`/`0x52`/`0x53`) never opens on the observed boots
[S: func_02037e44 / func_0204f564, main, docs/kb/port/sequencer-and-modes.md]. So the furniture
half of the economy is genuinely unexplored territory rather than merely undocumented
[S: docs/kb/port/sequencer-and-modes.md].

Money appears once in anything observed. In the taxi conversation the driver asks
`가서 어떻게 살려구 그래?` with a two-option answer `돈 있어 / 조금밖에 없어`, and then says
`그럼 적어도 택시비 낼 정도는 있겠네!` -- a taxi-fare line
[E: docs/log/cycle40-keyboard-gate-probe.md LONG40, run `long-a`, frames 16,500 and 18,000].
Whether the answer costs the player anything is not established
[H: instrument the player slot across those frames and diff].

## Where it lives

| function or symbol | module | role | grade/citation |
|---|---|---|---|
| `func_0204bcdc` | main | item-id nibble test; accepts nibble 3 or 4 | S: docs/kb/port/sequencer-and-modes.md |
| `func_0204bcf8` | main | the placement gate that calls it | S: docs/kb/port/sequencer-and-modes.md |
| `func_0204bc64` / `func_0204bc7c` | main | the sibling id comparisons | S: docs/kb/port/sequencer-and-modes.md |
| `func_ov052_02261054` | ov052 | reference implementation of the compare family | S: docs/kb/modules/overlays-ov0xx.md |
| `func_ov003_02220e20`, `func_ov003_022223bc` | ov003 | eight-flag item-category classifier | S: docs/kb/modules/overlays-ov0xx.md |
| `func_02037e44` | main | the interior item-grid writer | S: docs/kb/port/sequencer-and-modes.md |
| `func_0204f564` | main | its map-level front door | S: docs/kb/port/sequencer-and-modes.md |
| `func_0204ef24` / `func_0204ef74` | main | town item writer / multi-tile placer | S: port/shim/game/genfix.c |
| `data_020df5ec` | main | overlay-set table for overlays 90-146 (shops/menus) | S: docs/kb/port/sequencer-and-modes.md |
| `func_ov050_02262628` | ov050 | Nook's side of the arrival sequence | S: port/shim/game/spnpc.c |

## Data it reads and writes

| address or field | meaning | who writes | who reads |
|---|---|---|---|
| item cell (16 bits) | `nibble:category, low 12 bits:id` | `func_0204ef24`, `func_02037e44` | `func_0204bcdc` |
| `0xfff1` | the empty item/tile id | `func_020a13e8` state-1 reset | every placement gate |
| `0x5001`..`0x5008` | villager houses in the town item layer | `func_0207bbb8` | camera waypoints, town scene |
| `0x500a` | a house plot awaiting a house | generation | `func_0207bbb8` |
| `0x500d` | the shop | generation | flythrough camera |
| `data_020df5ec` | overlay set for the shop/menu overlays | static | overlay loader |

Grades: the cell layout and `0xfff1` are S
[docs/kb/port/sequencer-and-modes.md, port/shim/gfx/pmflist.c]; the `0x5xxx` values are E
[port/BOOT-STATE.md].

## How to check it

There is no economy recipe yet. The two cheap starting points are: (1) instrument
`func_0204bcdc`'s argument in the town at frame 37,500 of the town recipe and histogram the
nibbles actually present in a generated town's item layer
[E: docs/log/cycle40-keyboard-gate-probe.md TOWN40, `tap-D56`]; and (2) read
`src/matched/func_ov052_02261054.c` and then grep a partition for `bl 0x204bcdc` to enumerate
every consumer of an item id [S: docs/kb/modules/overlays-ov0xx.md].

Note the standing caution for any economy measurement: the port is an instrument, not the
truth, and a value seen only in the port is grade E until the oracle agrees or the source
explains it [S: wiki/README.md].

## Hypotheses

This section is the page. Each bullet names what to read and what would settle it.

- **H: Bells are a 32-bit field inside the `0x249c` player slot, and the wallet and the bank
  are two such fields.** The player slot is large and its only mapped region so far is the
  event bitfield at `+0x23f8` [S: port/shim/game/newgameprobe.c]. Experiment: on a live run,
  save the player slot, sell one item, save again, and diff -- the field that changes by the
  sale price is the wallet.
- **H: the item id's top nibble is a small enum (furniture, clothing, tool, stationery,
  fixture, house marker, none) and nibble 5 is "town fixture" while 3 and 4 are "placeable
  object".** The gate accepting only 3 and 4 is measured, and every town fixture observed is
  `0x5xxx` [S: docs/kb/port/sequencer-and-modes.md] [E: port/BOOT-STATE.md]. Experiment: dump
  the full item layer of a generated town plus one furnished room and histogram the nibbles.
- **H: prices are a per-item field in the item table rather than a formula, and the sell price
  is a fixed fraction of it.** The eight-flag classifier suggests a per-category rule sitting
  on top of a per-item value [S: docs/kb/modules/overlays-ov0xx.md]. Experiment: locate the
  item table (see `../data/items.md`), read the row stride, and check whether a 16-bit field in the
  row scales with known in-game prices.
- **H: the turnip market is a per-day price recomputed by the day-change routine
  `func_02040c90`, and one of its five `MI_CpuCopy8` blocks shifts yesterday's price into a
  history slot.** Five block copies in the only per-day rewrite found
  [S: port/tools/known_callees.txt]. Experiment: name each copy's source and destination; then
  run several `ACWW_RTC_*` day rollovers and watch for a value that changes once per day and
  has a week-long history.
- **H: `/fg/grass/redTurnip` is the turnip's field model, so turnips are placed as map items
  like flowers rather than held only in the inventory.** ov003's pool names it beside the
  grasses and flowers [S: docs/kb/modules/ov003-068.md]. Experiment: plant a turnip on a live
  run and look for a new non-`0xfff1` cell in the item layer.
- **H: the catalogue is a bitset in the player slot, one bit per catalogued item, written when
  an item is first obtained.** A bitset is what the game already uses for progress
  [S: port/shim/game/spnpc.c]. Experiment: diff the player slot across obtaining one new item
  and look for a single flipped bit at a stable offset.
- **H: the shop is overlay-resident: buying and selling run entirely inside the 90-146 overlay
  band, and `func_0204bcdc`'s twelve call sites in one of those functions are the shop's stock
  filter.** The band is described as shops/menus and the compare family lives there
  [S: docs/kb/port/sequencer-and-modes.md, docs/kb/modules/overlays-ov0xx.md]. Experiment:
  reach the shop on the interpreter path (the town recipe currently stops in the town hall)
  and log which overlays mount.
- **H: the interior item grid stays empty in every run so far only because the class owning
  `func_ov004_0224522c` never opens its channel, not because the writer is broken.** Every
  other link in that chain runs [S: docs/kb/port/sequencer-and-modes.md]
  [E: docs/kb/port/sequencer-and-modes.md, "Every link runs"]. Experiment: force channel
  `0x51`/`0x52`/`0x53` open and re-check `placed=`.
- **H: the taxi-fare line is flavour and the arrival costs nothing, because the player has no
  Bells at that point.** Observed only as dialogue
  [E: docs/log/cycle40-keyboard-gate-probe.md LONG40]. Experiment: instrument the player slot
  across frames 16,000-20,000 of the `long-a` recipe and look for any field decreasing.

## Related

- `town.md` -- the item layer these ids live in
- `player.md` -- the player slot the wallet is presumed to be in
- `events-and-calendar.md` -- the day-change routine a turnip price would ride on
- `../data/items.md` -- the item and furniture tables themselves
