# ROM layout

**Summary.** The Korean cartridge `ADMK` is an ordinary NitroSDK ROM: a header, an ARM9 and an
ARM7 binary, four ARM9 autoload/TCM regions, an overlay table with 148 ARM9 overlays, and a
file system of 9,508 files in 36 top-level directories. The game addresses everything in that
file system by path string, and almost every path string it uses is a `printf`-style template
compiled into the ARM9 image or into the overlay that needs it. Nothing is packed into one big
archive: the resource tree is loose files, each individually compressed.

**A note on grades.** On this page and the other `data/` pages, **S** covers two kinds of
citation: a symbol table or a matched source under `src/matched/`, and bytes read directly out
of the extracted ROM image under `extract/adm-kr/`. Image citations always name the file and
say which field was read, so a reader can re-run the same read.

## What happens

The cartridge identifies itself as `ANIMAL CROSS`, game code `ADMK`, maker `01`, ROM version 0
[S: `extract/adm-kr/header.yaml` `title`/`gamecode`/`makercode`/`rom_version`]. The ARM9
binary loads at `0x02000000` with its entry point at `0x02000800` and is stored compressed
[S: `extract/adm-kr/arm9/arm9.yaml` `base_address`=33554432, `entry_function`=33556480,
`compressed: true`]. Its autoload callback is at `0x02000A58` and the static module's BSS is
zero-length, because everything after the compressed image is handed to the autoload regions
[S: `extract/adm-kr/arm9/arm9.yaml` `autoload_callback`=33557080, `bss_start`=`bss_end`=34506816
= `0x020E8840`].

Four regions load beside the static ARM9 module. ITCM occupies `0x01FF8000`..`0x01FFDAE0`
[S: `extract/adm-kr/arm9/itcm.yaml` `base_address`=33521664, `code_size`=23264]; the DTCM module
image is 0x460 bytes at `0x027E0000` [S: `extract/adm-kr/arm9/dtcm.yaml` `base_address`=41811968,
`code_size`=1120] — the DTCM *window* the hardware maps there is 16 KB, `0x027e0000`-`0x027e4000`,
and the module image occupies only its bottom [S: `port/interp/interp_boot.c:11-14`;
see `../engine/memory-map.md`]; `autoload_2` occupies `0x020E8840`..`0x0213FDC0` and is where the whole
NitroSDK and NNS library lives [S: `extract/adm-kr/arm9/unk_autoload_2.yaml`
`base_address`=34506816, `code_size`=357760]; `autoload_3` is pure BSS,
`0x0213FDC0`..`0x02207CC0`, and is the game's global data arena
[S: `extract/adm-kr/arm9/unk_autoload_3.yaml` `base_address`=34864576, `code_size`=0,
`bss_size`=818944]. `autoload_3` ends exactly where the first overlay begins, so the overlay
region starts at `0x02207CC0` [S: `extract/adm-kr/arm9_overlays/overlays.yaml`, `id: 0`
`base_address`=35683520].

That layout is what makes the SDK addresses on the other engine pages predictable: every
`FS_*`, `GX_*`, `G3X_*` and `NNS_*` symbol sits in `0x0210xxxx`-`0x0212xxxx`, inside
`autoload_2` [S: `config/adm-kr/arm9/autoload_2/symbols.txt`, e.g. `FS_Init` addr `0x0211b35c`].
ITCM is the exception band, and it is not small: 158 function symbols, 114 of them named,
covering the four geometry-engine buffer helpers at `0x01ff8bd0`-`0x01ff8e18`, the
`NNSi_G3dFuncSbc_*` scene-graph opcodes, the `MTX_*`/`VEC_*`/`FX_*` fixed-point library, the
interrupt entry (`OS_IrqHandler`, `OS_Halt`, `OS_SaveContext`) and `OS_GetTick`
[S: `config/adm-kr/arm9/itcm/symbols.txt`, counted over `kind:function` lines;
`NNS_G3dGeBufferOP_N` addr `0x01ff8bd0`, `NNS_G3dGeWaitSendDL` addr `0x01ff8e18`].

There are 148 ARM9 overlays, `ov000` through `ov147`, and no ARM7 overlays at all
[S: `extract/adm-kr/arm9_overlays/overlays.yaml`, 148 `- id:` entries; `extract/adm-kr/config.yaml`
`arm7_overlays: null`]. Each entry carries `base_address`, `code_size`, `bss_size`,
`ctor_start`, `ctor_end`, `file_id`, `compressed` and `signed`
[S: `extract/adm-kr/arm9_overlays/overlays.yaml`, entry `id: 0`]. Every overlay in this ROM is
compressed and none is signed [S: same file, `compressed: true` / `signed: false` on all 148
entries]. The 148 overlays share only 26 distinct load addresses, so most of them are
alternates that occupy the same memory one at a time: 35 overlays load at `0x02260020`, 19 at
`0x02278a00`, 14 at `0x0229c180` and 12 at `0x02260420` [S: `overlays.yaml`, counted over
`base_address` values]. `ov000`, `ov001` and `ov002` all load at `0x02207CC0`, and `ov003` and
`ov004` both at `0x0220BF00` [S: `overlays.yaml`, entries 0-4]. Their code totals 1,683,328
bytes, more than four times the static ARM9 image's code [S: `overlays.yaml`, sum of
`code_size`]. That overlap is the reason the port cannot statically rewrite overlay pointers:
129 of the 137 adjacent overlay pairs overlap in address, so a word at `0x02262da0` belongs to
whichever overlay is currently loaded [S: `port/shim/fs/ovlreloc.c`, header].

The ROM header stored in the extract carries the cartridge identity but **not** the FNT, FAT or
overlay-table offsets [S: `extract/adm-kr/header.yaml`, 15 fields, none of them a table offset];
those are computed by the packer from the alignment and padding tables
[S: `extract/adm-kr/config.yaml` `alignment`/`padding`]. At runtime the game reads them out of
the 0x160-byte ROM header image the firmware leaves at `0x027FFE00` — FNT at +0x40, FAT at
+0x48, ARM9 overlay table at +0x50, ARM7 overlay table at +0x58
[S: `FSi_InitRom`, `autoload_2`, `src/matched/FSi_InitRom.c`].

The file system holds 9,508 files under 36 top-level directories plus two loose root files,
`BUILDTIME` and `sound_data.sdat` [S: `extract/adm-kr/files/`, recursive file count and
`ls`]. Directory order in the ROM image is recorded separately from the tree
[S: `extract/adm-kr/path_order.txt`, 38 lines]; note that `/dwc` is placed last there rather
than alphabetically [S: `extract/adm-kr/path_order.txt` line 38].

The largest single file in the ROM is `sound_data.sdat` at 10,704,768 bytes, and the largest
directory is `ftr/` (furniture) at 3,585 files and 6,692,184 bytes [S: `extract/adm-kr/files/`,
file sizes]. `script/` is the second largest by file count, 1,791 files, and it is the entire
text of the game [S: `extract/adm-kr/files/script/`, recursive count].

## Where it lives

| region | NDS address | size | role | grade/citation |
|---|---|---|---|---|
| ARM9 static | `0x02000000` | entry `0x02000800` | game code, always resident | S: `arm9/arm9.yaml` |
| ITCM | `0x01FF8000` | 0x5AE0 image (32 KB window) | 158 hot functions: 3D submission, fixed-point maths, the interrupt entry | S: `arm9/itcm.yaml`; `config/.../itcm/symbols.txt` |
| DTCM | `0x027E0000` | 0x460 image (16 KB window) | interrupt-time data; `OS_IRQTable` at the bottom, the stacks at the top | S: `arm9/dtcm.yaml`; `port/interp/interp_boot.c:11-14` |
| `autoload_2` | `0x020E8840` | 0x57580 | NitroSDK + NNS libraries | S: `arm9/unk_autoload_2.yaml` |
| `autoload_3` | `0x0213FDC0` | 0xC7F00 BSS | game globals arena | S: `arm9/unk_autoload_3.yaml` |
| overlays | 26 distinct bases, first `0x02207CC0` | 1,683,328 B total | 148 feature modules | S: `arm9_overlays/overlays.yaml` |
| file system | — | 9,508 files | resources, opened by path | S: `extract/adm-kr/files/` |

## Data it reads and writes

| directory | files | bytes | what it holds | grade/citation |
|---|---|---|---|---|
| `ftr/` | 3,585 | 6,692,184 | furniture models and textures | S: `extract/adm-kr/files/ftr/` |
| `script/` | 1,791 | 1,581,466 | all message text (`.bmg`) | S: `.../script/` |
| `menu/` | 737 | 846,493 | menu screen artwork (`.bch`/`.bsc`/`.bpl`) | S: `.../menu/` |
| `str/` | 338 | 1,371,004 | house and NPC-house *structures*, not strings | S: `.../str/` |
| `anm/`, `npc/`, `npc_sp/` | 324 / 301 / 73 | 2.5 MB | animations, villager and special-character models | S: `.../` |
| `bg/` | 257 | 2,811,379 | town ground and terrain sets | S: `.../bg/` |
| `cloth/` | 256 | 89,878 | shirt textures | S: `.../cloth/` |
| `fish/`, `insect/` | 284 / 129 | 1,348,867 | fish and bug models | S: `.../fish/`, `.../insect/` |
| `fg/` | 213 | 394,984 | trees, flowers, grass, holes, stones | S: `.../fg/` |
| `PHead/ PPal/ PGls/ PItm/ PBody/ PFcTx/ FcAnm/` | 826 | 890,834 | player appearance parts | S: `.../` |
| `carpet/`, `wall/`, `roomObj/` | 68 / 68 / 46 | 593,826 | interior surfaces and shop fittings | S: `.../` |
| `sky/`, `a_mes/`, `ab_all/`, `spl/`, `font/` | 38 / 18 / 2 / 14 / 12 | 0.5 MB | sky layers, message-box art, effects, fonts | S: `.../` |
| `item_info/`, `ftr_info/`, `fg_data/`, `myOrg/` | 4 / 3 / 8 / 1 | 156 KB | the flat data tables (see `items.md`) | S: `.../` |
| `dwc/utility.bin` | 1 | 929,892 | Nintendo WFC utility payload | S: `.../dwc/` |
| `sound_data.sdat` | 1 | 10,704,768 | the whole sound archive (see `music.md`) | S: `extract/adm-kr/files/sound_data.sdat` |

One number in that table is checkable against another file. `bg/a0/`..`bg/a8/` hold 134 acre
archives named `0000.arc` through `0085.arc`, and `bg/bkattr.bin` is exactly 134 bytes — one
attribute byte per acre [S: `extract/adm-kr/files/bg/`, per-directory listings;
`extract/adm-kr/files/bg/bkattr.bin`, size]. The matching texture sets are `bg/t256`, `t257` and
`t258`, 42 files numbered from `1000.nsbtx` [S: `extract/adm-kr/files/bg/t256/`, listing].

`str/` is a name trap: it is house *structures*, 242 `.nsbtx` and 94 `.arc` model files, not
strings [S: `extract/adm-kr/files/str/`, extension census; corroborated in `port/TAXI-ROAD.md`
"the name is a trap"].

The path templates the code uses are compiled into the modules that need them, and reading them
back out of the module images gives the naming grammar for each directory. `arm9.bin` alone
carries 212 distinct resource paths, including the parameterised forms `/PHead/%d/%d.nsbmd`,
`/anm/%d/%d.nsbca`, `/bg/a%d/%04x.arc`, `/cloth/%d/cloth%03d.nsbtx`, `/wall/wall_%d.nsbtx` and
`/script/%s/select/%s.bmg` [S: `extract/adm-kr/arm9/arm9.bin`, path-format string literals].
The overlays carry their own: `ov003` holds 209 tree, flower and house-structure paths, `ov004`
holds the furniture and room-object templates `/ftr/%d/%d/%04x.arc` and `/roomObj/%s.arc`, and
`ov009` holds `/str/arc/%d/str%d%c.arc` [S: `extract/adm-kr/arm9_overlays/ov003.bin`,
`ov004.bin`, `ov009.bin`, path-format string literals].

Every menu overlay from `ov090` upward carries exactly the `menu/<screen>/` paths for the one
screen it draws, which makes the overlay table a readable index of the game's UI: `ov095` and
`ov111`/`ov112`/`ov122`/`ov126` hold `menu/chat2/` keyboard pages, `ov118` and `ov120` the town
map, `ov124` the Hangul keyboard's `menu/han/`, `ov130`/`ov132`/`ov133` the bank, `ov134` the
clock, `ov142` the catalogue, `ov143` the melody screen, `ov144` the music screen, `ov145`
donations, `ov146` the WFC screen and `ov147` the title [S: `extract/adm-kr/arm9_overlays/ov0*.bin`,
path string literals per overlay].

## How to check it

No run is needed for anything on this page; it is all static structure. To re-derive the
directory census:

```bash
python - <<'PY'
import os, collections
B = r"extract/adm-kr/files"
n = b = 0; ext = collections.Counter()
for dp, dn, fn in os.walk(B):
    for f in fn:
        n += 1; b += os.path.getsize(os.path.join(dp, f))
        ext[os.path.splitext(f)[1]] += 1
print(n, b, ext.most_common())
PY
```

Expected: 9,508 files and the extension histogram in `archives.md`. To re-derive the path
templates, scan `extract/adm-kr/arm9/arm9.bin` and `extract/adm-kr/arm9_overlays/*.bin` for
printable runs ending in a known resource extension.

## Hypotheses

- The 26 shared overlay load addresses should partition into a small number of *slots* with a
  known residency discipline. Settle it by logging `FS_LoadOverlay` overlay ids and the
  resulting `FS_StartOverlay` addresses across a `tap-D56`-shaped run and grouping by address.
- `BUILDTIME` (31 bytes at the file-system root) is presumably a build stamp read by nothing at
  runtime. Settle it by watching `FS_ConvertPathToFileID` for the id of `/BUILDTIME` across a
  full run and seeing whether it is ever requested.
- `path_order.txt` places `/dwc` out of alphabetical order, which suggests it was appended after
  the rest of the tree was laid out. Settle it by comparing the FAT offsets of `dwc/utility.bin`
  against the last file of `wall/`.
- The overlay-to-`menu/` mapping above is read from string literals, which proves the path is
  *present* in that overlay, not that the overlay is the only loader of that screen. Settle it
  per screen by logging the loaded overlay set at the frame the screen appears, the way
  `tap-D56` did for the town [E: `docs/log/cycle40-keyboard-gate-probe.md` TOWN40, overlays 5,
  36, 54, 120, 117 at frame 37,500].

## Related

- `archives.md` — the container formats every one of these files is wrapped in.
- `../engine/file-system.md` — how a path becomes bytes in RAM.
- `items.md`, `villagers.md`, `fish-and-bugs.md`, `music.md` — the tables inside the tree.
