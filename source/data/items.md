# Items and furniture

**Summary.** ACWW splits "things" into two families with parallel storage. Furniture is a 16-bit
id in `0x0000`-`0x06e8` and has a model and a texture set under `ftr/`, described by three tables
in `ftr_info/`. Everything else — tools, clothes, fruit, fossils, paper — is the *item* family,
described by four tables in `item_info/` and drawn from icon sheets rather than models. Names for
both come out of the message system, not out of the tables.

Grade note: **S** on this page covers symbol tables, matched sources, and bytes read directly out
of the extracted ROM image (path and field always named).

## What happens

### Furniture

Furniture assets are addressed by a 16-bit id split across two directory levels. The template is
`/ftr/%d/%d/%04x.arc` with a matching `.nsbtx`, compiled into `ov004`
[S: `extract/adm-kr/arm9_overlays/ov004.bin`, path-format string literals]. The two `%d` are the
id's high byte and its middle nibble: `ftr/0/0/` holds `0000`..`000f`, `ftr/0/1/` holds
`0010`..`001f`, `ftr/1/0/` holds `0100`..`010f`, and the last populated directory `ftr/6/14/`
holds `06e0`..`06e8` [S: `extract/adm-kr/files/ftr/0/0/`, `ftr/0/1/`, `ftr/1/0/`, `ftr/6/14/`,
directory listings]. That gives **1,769 furniture ids, `0x0000` through `0x06e8`**, each with one
`.arc` and one `.nsbtx` [S: `extract/adm-kr/files/ftr/`, 1,770 `.arc` and 1,792 `.nsbtx`; the
extra `.arc` is `ftr/anm/anm.arc` and the extra 23 `.nsbtx` belong to `ftr/tv/`].

`ftr/anm/anm.arc` is the shared furniture animation archive, and `ftr/tv/` is the television: a
`tv.nsbtx`, a `prog/` directory reached by `/ftr/tv/prog/tv_program%d.nsbtp` and a `weather/`
directory reached by `/ftr/tv/weather/%s.nsbtp`
[S: `extract/adm-kr/files/ftr/`; `extract/adm-kr/arm9_overlays/ov004.bin`, path literals].

The furniture tables are three files under `ftr_info/`: `always.bin` 16,384 bytes, `dma.bin`
65,536 bytes and `indoor.bin` 8,192 bytes, opened from `/ftr_info/always.bin`,
`/ftr_info/dma.bin` and `/ftr_info/indoor.bin`
[S: `extract/adm-kr/files/ftr_info/`, file sizes; `extract/adm-kr/arm9/arm9.bin`, the three path
literals]. All three sizes are powers of two, which is consistent with a fixed slot count of
2,048 at 8, 32 and 4 bytes per entry respectively — enough to cover the 1,769 real ids with room
to spare [H: arithmetic on the sizes above; see Hypotheses]. `dma.bin`'s name and its position in
the same directory suggest it is the block that gets DMA'd to a working buffer rather than read
field by field [H].

### Items

The item tables are four files under `item_info/`: `always.bin` 18,432 bytes, `dma.bin` 36,864,
`indoor.bin` 6,144 and `series.bin` 3,072, all opened by literal path from the ARM9 image
[S: `extract/adm-kr/files/item_info/`, file sizes; `extract/adm-kr/arm9/arm9.bin`, the four path
literals]. The four sizes share the divisor 1,536, giving 12, 24, 4 and 2 bytes per entry —
`series.bin` at 2 bytes per item is exactly the shape of a series id, which is what the furniture
series (matching sets) needs [H: arithmetic; see Hypotheses]. A record-size probe over all four
files at 2, 4, 6, 8, 12 and 16 bytes found no size at which the entries become obviously
structured, so the layout is not settled by the image alone
[S: probe over `extract/adm-kr/files/item_info/*.bin`, distinct-record counts at each stride].

Held and dropped items are 3D: `PItm/` holds 53 models, 43 joint animations and 2 texture-SRT
animations, addressed by `/PItm/Mdl%d/%d.nsbmd`, `/PItm/Anm%d/%d.nsbca`,
`/PItm/ItaAnm%d/%d.nsbta` and `/PItm/Uki0/%d.nsbmd`
[S: `extract/adm-kr/files/PItm/`, per-directory counts; `extract/adm-kr/arm9/arm9.bin`, the four
path literals]. `Mdl0` and `Anm0` hold 32 entries each and `Mdl1`/`Anm1` 18 and 11, so the item
model space is far smaller than the item id space — most items exist only as an inventory icon
[S: `extract/adm-kr/files/PItm/`, per-directory counts].

Those icons live in `menu/icon/` and `menu/inventory/`. `ov094` carries the templates
`menu/icon/icon%02d.bch`, `menu/icon/pre%d.bch`, `menu/inventory/itmp/m%d.bch` and
`menu/inventory/itmp/w%d.bch`, plus the three fixed item sheets `b_itm0.bch`, `b_itm1.bch` and
`b_itm2.bch` at 8,192 bytes each
[S: `extract/adm-kr/arm9_overlays/ov094.bin`, path literals;
`extract/adm-kr/files/menu/inventory/`, file sizes]. `menu/icon/` holds 24 files and
`menu/inventory/` 59 [S: `extract/adm-kr/files/menu/icon/`,
`extract/adm-kr/files/menu/inventory/`, counts].

### Wearables and surfaces

Shirts are texture-only: 256 `.nsbtx` files in sixteen directories of sixteen, addressed by
`/cloth/%d/cloth%03d.nsbtx` [S: `extract/adm-kr/files/cloth/`, 16 subdirectories of 16 files;
`extract/adm-kr/arm9/arm9.bin`, path literal]. Wallpaper and flooring are the same shape but
flat: 68 `wall/wall_%d.nsbtx` and 68 `carpet/floor_%d.nsbtx`
[S: `extract/adm-kr/files/wall/`, `extract/adm-kr/files/carpet/`, counts;
`extract/adm-kr/arm9/arm9.bin`, both path literals]. The player's own body parts follow the same
`%d/%d` scheme: 158 heads under `PHead/` numbered 0..157, 75 eye/face models under `PGls/`, 192
palettes under `PPal/`, 32 face textures under `PFcTx/`, 367 face animations under `FcAnm/`, and
two bodies, `PBody/boy.nsbmd` and `PBody/grl.nsbmd`
[S: `extract/adm-kr/files/`, per-directory counts and listings;
`extract/adm-kr/arm9/arm9.bin`, the seven `/P*` and `/FcAnm/` path literals].

Shop fittings are `roomObj/`: 23 `.arc` + `.nsbtx` pairs opened by `/roomObj/%s.arc` and
`/roomObj/%s.nsbtx` from `ov004`, with twelve of the names also present as literals — the cafés,
the tailor, the tarot booths, the museum exhibits, the telephone and the check-in desk
[S: `extract/adm-kr/files/roomObj/`, 46 files; `extract/adm-kr/arm9_overlays/ov004.bin`, path
literals].

### Names

No table on this page holds a name. Item, fish and bug names come from the message system's
`string/` bank: `script/KOR/string/obj_etc_fish.bmg` (4,239 bytes) and `obj_etc_insect.bmg`
(4,214 bytes) for creatures, and the `st_*.bmg` files for the categories the dialogue needs to
name — `st_object.bmg`, `st_furniture_taste.bmg`, `st_furniture_letter.bmg`, `st_fashion.bmg`,
`st_food.bmg`, `st_fossil.bmg`
[S: `extract/adm-kr/files/script/KOR/string/`, file names and sizes]. The catalogue screen that
displays them is `ov142`, carrying the `menu/catalog/` assets
[S: `extract/adm-kr/arm9_overlays/ov142.bin`, path literals].

## Where it lives

| table or asset | location | entries | grade/citation |
|---|---|---|---|
| furniture models | `ftr/<hi>/<mid>/<id>.arc` + `.nsbtx` | 1,769 ids `0x0000`-`0x06e8` | S: `extract/adm-kr/files/ftr/` |
| furniture animations | `ftr/anm/anm.arc` | 1 archive | S: `extract/adm-kr/files/ftr/anm/` |
| television | `ftr/tv/tv.nsbtx`, `prog/`, `weather/` | 23 files | S: `extract/adm-kr/files/ftr/tv/` |
| furniture table (resident) | `ftr_info/always.bin` | 16,384 B | S: `extract/adm-kr/files/ftr_info/` |
| furniture table (DMA) | `ftr_info/dma.bin` | 65,536 B | S: same |
| furniture table (indoor) | `ftr_info/indoor.bin` | 8,192 B | S: same |
| item table (resident) | `item_info/always.bin` | 18,432 B | S: `extract/adm-kr/files/item_info/` |
| item table (DMA) | `item_info/dma.bin` | 36,864 B | S: same |
| item table (indoor) | `item_info/indoor.bin` | 6,144 B | S: same |
| item series | `item_info/series.bin` | 3,072 B | S: same |
| item models | `PItm/Mdl0`, `Mdl1`, `Uki0` | 53 `.nsbmd` | S: `extract/adm-kr/files/PItm/` |
| item icons | `menu/icon/`, `menu/inventory/` | 24 + 59 files | S: `extract/adm-kr/files/menu/` |
| shirts | `cloth/%d/cloth%03d.nsbtx` | 256 | S: `extract/adm-kr/files/cloth/` |
| wallpaper / flooring | `wall/wall_%d.nsbtx`, `carpet/floor_%d.nsbtx` | 68 each | S: `extract/adm-kr/files/` |
| player parts | `PHead/`, `PGls/`, `PPal/`, `PFcTx/`, `FcAnm/`, `PBody/` | 158/75/192/32/367/2 | S: `extract/adm-kr/files/` |
| names | `script/KOR/string/*.bmg` | 36 banks | S: `extract/adm-kr/files/script/KOR/string/` |

## Data it reads and writes

| field | meaning | who writes | who reads |
|---|---|---|---|
| furniture id (u16) | selects `ftr/<id>>>8>/<(id>>4)&15>/<id>.arc` | the save and the shops | `ov004`'s furniture loader [S: `extract/adm-kr/arm9_overlays/ov004.bin`] |
| `ftr_info/dma.bin` slot | the per-furniture record copied to RAM | the packer | the furniture system [H: name and size] |
| `item_info/series.bin` slot | 2 bytes, probably the matching-set id | the packer | the furniture/interior code [H] |
| `menu/inventory/itmp/m%d.bch`, `w%d.bch` | per-item inventory pictures | the packer | `ov094` [S: `extract/adm-kr/arm9_overlays/ov094.bin`] |

### The id a pocket slot holds, and its three surface bands

Grade **A**. The 16-bit id the save's pockets and a shop's shelf cell carry is **`0x1000` plus an
index into `item_info`'s 1,536 slots**: every id this project has read out of a live game -- twelve
of them, across four cycles -- lies in `0x1000`..`0x15ff`, which is exactly that range
[H: arithmetic over the four `item_info` sizes above; S for the ids themselves,
`docs/log/cycle41-gameplay.md` GP54-8].

Three consecutive bands inside it fall out of the asset counts on this page and are each confirmed
by a name the GAME printed, so the band boundaries are measured rather than assumed:

| band | what, and how many | the witness |
|---|---|---|
| `0x1100`..`0x1143` | the 68 `wall/wall_%d.nsbtx` wallpapers | `0x111f` = `wall_31`, and Nook's shop calls it a `벽지` — a wallpaper |
| `0x1144`..`0x1187` | the 68 `carpet/floor_%d.nsbtx` floorings | `0x114b` = `floor_7`, and the shop calls it a `바닥` — a flooring |
| `0x1188`..`0x1287` | the 256 `cloth/%d/cloth%03d.nsbtx` shirts | `0x11a8` = `cloth032`, which the save reads as the WORN SHIRT [S: `port/tools/savetool.py check`] |

So **`0x117c` is `carpet/floor_56.nsbtx`**, the 57th flooring — which is what the villager who gave
it calls a `바닥`. A fourth witness comes from the save itself: a villager's stored `wallpaper` and
`carpet` bytes are raw indices under 68, so the SAVE keeps the index where a POCKET keeps
`base + index` [S: `savetool.py check` on `scratchpad/gameplay54/town3.sav`].

**Names are not in a KOR message archive.** The largest of the 91 under `script/KOR/` has 256
entries and none is near 1,536, so an item-name table lives in `a_mes/`, `str/arc/` or an overlay
and is still unfound — which is why `0x1547`, `item_info` slot 1351, is identified only by its slot
[S: entry counts over every `script/KOR/**/*.bmg`].

## How to check it

Static checks first. To confirm the furniture id range:

```bash
python - <<'PY'
import os, glob
ids = sorted(int(os.path.basename(p)[:4], 16)
             for p in glob.glob(r"extract/adm-kr/files/ftr/*/*/*.nsbtx"))
print(len(ids), hex(ids[0]), hex(ids[-1]), ids == list(range(ids[0], ids[-1] + 1)))
PY
```

Expected: `1769 0x0 0x6e8 True`.

To settle a table's record size, the useful measurement is a live one: run the interpreter recipe
that reaches the town (see `../engine/file-system.md`), watch the address the loader stores
`ftr_info/dma.bin` at, and record the stride between two consecutive furniture lookups. The port
already reads these files through the ROM's own `FS_*` path, so no shim is needed
[H: host/prose inference from `port/shim/fs/romfs.c`, header; verify against the ROM function or symbol table and this page's recipe].

## Hypotheses

- **`item_info/` has 1,536 slots at 12/24/4/2 bytes and `ftr_info/` has 2,048 slots at 8/32/4
  bytes.** The only evidence is that those are the divisors that make all four (respectively
  three) files come out whole [H: arithmetic on the sizes]. Settle it by tracing the index
  arithmetic in whichever function loads `/item_info/always.bin` — find it by breaking on
  `FS_ConvertPathToFileID` for that path under `ACWW_INTERP=1` and following the caller.
- **`always` / `dma` / `indoor` name a residency policy, not a content split.** Both directories
  use the same three names and `dma` is the largest in both [H: file names and sizes]. Settle it
  the same way, by seeing which one is copied wholesale and which is read in place.
- **The 1,769 furniture ids are not all real furniture.** 1,769 is close to a full `0x06e9` range
  with no gaps, which suggests padding entries [S: the id range is contiguous — see the check
  above]. Settle it by counting how many `ftr_info/always.bin` slots are non-zero.
- **Item ids and furniture ids are different id spaces.** Nothing measured connects them; they
  simply have separate tables and separate assets [H]. Settle it by reading the save's inventory
  encoding against `../systems/save-data.md`.
- **`PItm/Uki0/` (3 models) is the fishing float.** "Uki" is a plausible reading, and the
  directory is tiny and sits beside the item models [H]. Settle it by dumping the model bound
  when a rod is used.

## Related

- `rom-layout.md` — the directory census these counts come from.
- `archives.md` — the `NARC` and `nsb*` containers each asset sits in.
- `fish-and-bugs.md` — the creature families, which use the same icon-sheet pattern.
- `../engine/file-system.md` — how `/ftr/1/0/0100.arc` becomes bytes.

## Item-name lookup (item-names-1)

This measured appendix supersedes the earlier **Names** paragraph's claim that no table
here holds names. Names are UTF-16LE in `item_info/dma.bin` and `ftr_info/dma.bin`;
the offline reader is `port/tools/items.py`. No complete name table is published
[S: `src/matched/func_02062cbc.c`, `func_02053ea4.c`, `func_02062ea4.c`;
E: `scratchpad/handoff/item-names-1/evidence.json`, input hashes and six known-ID checks].

The inventory caller `ov094:0x0229abf8` invokes `main:0x02062ea4`, which first normalizes
the ID with `0x02061e2c`, then selects the item or furniture branch. Item lookup
`0x02062a28` reads the DMA handle at `0x021cb5e0 + 0x38`, indexes by the low 12 bits
(the `0x1000..0x10ff` quantity group ORs in 3), and clamps at index `0x56d`.
Furniture lookup `0x020537e8` uses `0x021c8c48 + 0x38`, index `(id - 0x3000) >> 2`,
and clamps at `0x6e8`. Applying the low-12-bit rule to furniture produces a wrong name
[S: `src/matched/func_ov094_0229abf8.c`, `func_02062ea4.c`, `func_02061e2c.c`,
`func_02062a28.c`, `func_0204bc64.c`, `func_020537e8.c`, `func_0206e6e4.c`;
E: `scratchpad/item-names-1/tests.stderr`, furniture negative control].

The initializer proves 1,536 item slots with 12/4/24-byte always/indoor/DMA strides,
and 2,048 furniture slots with 8/4/32-byte strides. Furniture names occupy the first
22 bytes, before a price halfword at `+0x16`; item names occupy 24 bytes, with their
price halfword at always `+0`. Series initialization is separately **128 records of
24 bytes**, not a proven 1,536-entry array of series halfwords. `--count` returns 3,159
canonical lookup queries (1,390 item + 1,769 furniture, including aliases/empty names),
not the number of distinct names or all physical slots
[S: `src/matched/func_02062cbc.c`, `func_02053ea4.c`, `func_020628ac.c`,
`func_02053e18.c`; E: `scratchpad/handoff/item-names-1/evidence.json`, counts and decoded digest].

| ID band | measured distinction | evidence |
|---|---|---|
| `0x00xx` | includes field-tree IDs; `0x0043/0x0044` have no item-name branch | S: `src/matched/func_02061e2c.c`, `func_02062ea4.c`; E: `scratchpad/item-names-1/tests.stderr` |
| `0x1100..0x1143`, `0x1144..0x1187` | item record categories 1 and 2; the latter contains the measured flooring ID below | S: `src/matched/func_02062870.c`; E: `scratchpad/handoff/item-names-1/evidence.json`, category runs |
| `0x11a8..0x12a7` | wearable range, category 5; thus `0x11xx` is not all clothing | S: `src/matched/func_0204b2c8.c`; E: `scratchpad/handoff/item-names-1/evidence.json`, category runs |
| `0x14fe..0x1517` | flower/seed category 32, including measured `0x150a` | S: `src/matched/func_02062870.c`; E: `scratchpad/handoff/item-names-1/evidence.json`, known-ID and category checks |
| `0x1518..0x151c` | fruit predicate; record category 33 | S: `src/matched/func_0204ca64.c`; E: `scratchpad/handoff/item-names-1/evidence.json`, category runs |
| high nibble `3` or `4` | furniture branch after normalization, not an item-table index | S: `src/matched/func_0204bcdc.c`, `func_0204bc64.c`, `func_02061e2c.c` |

- `0x117c`: **눈속임 바닥**, item index `0x17c`, stored base price 1,600 Bells [E: `scratchpad/handoff/item-names-1/evidence.json`, known IDs].
- `0x3508`: **흰꽃 테이블**, furniture index `0x142`, stored base price 1,900 Bells [E: `scratchpad/handoff/item-names-1/evidence.json`, known IDs].
- `0x1547`: **품절 간판**, item index `0x547`, stored base price zero [E: `scratchpad/handoff/item-names-1/evidence.json`, known IDs].

The base-price label is deliberate: the orange record stores 2,000, but the native-fruit
arm divides by five and shop sale callers can divide by four. The tool does not read town
state or promise an actual buy/sell quote. The brief's seed and rod bases are 80 and 500
[S: `src/matched/func_0204c878.c`, `func_ov049_02260cf8.c`;
E: `scratchpad/handoff/item-names-1/evidence.json`, known-ID prices].

Reproduce with `python port/tools/items.py 117c 3508 1547`, `--grep TEXT`, or `--count`;
`python port/tools/test_items.py` also requires malformed/truncated input refusal. Input
paths are relative to the script's repository root, independent of the caller's cwd
[S: `port/tools/items.py`, `port/tools/test_items.py`].
