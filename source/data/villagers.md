# Villagers and special characters

**Summary.** There are 150 ordinary villager models, numbered 0 to 149 and stored eight to a
directory under `npc/model/`, plus 37 special characters stored by a three-letter code under
`npc_sp/model/`. The two families are handled differently in every way that matters: villagers
are a numeric id with shared animations and dialogue chosen by personality, while each special
character has its own overlay that loads its own model. Names live in the message system, not in
any table.

Grade note: **S** on this page covers symbol tables, matched sources, and bytes read directly out
of the extracted ROM image (path and field always named).

## What happens

### Ordinary villagers

The model path is `npc/model/%d/%d.nsbmd` with a matching `npc/model/%d/%d.nsbtx`, compiled into
the ARM9 image [S: `extract/adm-kr/arm9/arm9.bin`, path-format string literals]. The first `%d`
is the directory and the second the villager id, and the directories step by eight:
`npc/model/0/` holds `0`..`7`, `npc/model/8/` holds `8`..`15`, and the last, `npc/model/144/`,
holds `144`..`149` [S: `extract/adm-kr/files/npc/model/0/`, `/8/`, `/144/`, directory listings].
There are 19 directories, 18 of eight models and one of six, for **150 villagers, ids 0-149**
[S: `extract/adm-kr/files/npc/model/`, per-directory counts; 150 `.nsbmd` and 150 `.nsbtx` in the
extension census]. One loose file sits beside them, `npc/ta_test.nsbtp`
[S: `extract/adm-kr/files/npc/`, listing].

Villager animation is shared, not per-villager: `anm/` holds 324 `.nsbca` files numbered 0 to 323
across eleven directories of 32, addressed by `/anm/%d/%d.nsbca` on the same
directory-holds-a-block scheme [S: `extract/adm-kr/files/anm/`, per-directory counts and the
`anm/10/` listing `320`..`323`; `extract/adm-kr/arm9/arm9.bin`, path literal].

Dialogue is chosen by *personality*, not by villager id. The message tree has six personality
directories — `bo`, `ta`, `ge`, `fu`, `ko`, `ha` — and the game composes a path from a
personality prefix table at `0x020d72a4` holding exactly those six strings
[S: `extract/adm-kr/files/script/KOR/message/`, subdirectory listing; `port/TAXI-ROAD.md`, the
prefix table; `src/matched/func_0200366c.c`]. `bo` and `ta` each hold 242 files in eighteen
subdirectories, and the other four personalities have the same shape
[S: `extract/adm-kr/files/script/KOR/message/bo/`, `/ta/`, counts and subdirectory names].
The message tree also has a `3p` directory inside each personality holding one file per *other*
personality — `bo_.bmg`, `fu_.bmg`, `ge_.bmg`, `ha_.bmg`, `ko_.bmg`, `ta_.bmg` — which is a
villager talking about a villager [S: `extract/adm-kr/files/script/KOR/message/bo/3p/`, listing].

Villager names come out of `script/KOR/string/st_npc_name.bmg` (1,466 bytes), their habits out
of `st_npc_habit.bmg` (1,401 bytes), and player-given nicknames out of `st_nickn.bmg` (522 bytes)
[S: `extract/adm-kr/files/script/KOR/string/`, file names and sizes].

### Special characters

`npc_sp/model/` holds 37 distinct three-letter stems, each with an `<stem>.nsbmd` and, for 36 of
them, an `<stem>_tex.nsbtx`: `boa`, `bpt`, `cml`, `dnk`, `end`, `fox`, `grf`, `hgh`, `hgs`,
`los`, `lrc`, `mka`, `mof`, `mol`, `mum`, `ott`, `owl`, `ows`, `pga`, `pgb`, `pge`, `pla`, `plb`,
`plc`, `poo`, `rcc`, `rcd`, `rcn`, `rcs`, `seg`, `seo`, `tti`, `ttl`, `upa`, `wip`, `wrl`, `xct`
[S: `extract/adm-kr/files/npc_sp/model/`, 73 files, stems after stripping `_tex`]. `mka` is the
one without a texture file [S: same listing]. Every path is a literal, not a template — the ARM9
image carries all of them spelled out [S: `extract/adm-kr/arm9/arm9.bin`, the `npc_sp/model/*`
literals].

The strong structural fact is that **each special character has its own overlay**, and the
overlay's image contains only that character's two path strings. Reading them back out gives a
direct overlay-to-character binding
[S: `extract/adm-kr/arm9_overlays/ov0*.bin`, path string literals per overlay]:

| overlay | stems it names | grade/citation |
|---|---|---|
| `ov045` | `bpt` | S: `ov045.bin` |
| `ov046` | `ows` | S: `ov046.bin` |
| `ov047` | `owl` | S: `ov047.bin` |
| `ov048` | `plc` | S: `ov048.bin` |
| `ov049` | `hgh` | S: `ov049.bin` |
| `ov050` | `lrc`, `rcc`, `rcd`, `rcn`, `rcs` | S: `ov050.bin` |
| `ov051` | `wip` | S: `ov051.bin` |
| `ov052` | `fox` | S: `ov052.bin` |
| `ov053` | `poo` | S: `ov053.bin` |
| `ov054` | `pga`, `pgb` | S: `ov054.bin` |
| `ov055` | `xct` | S: `ov055.bin` |
| `ov068` | `end`, `mof`, `ott`, `pga`, `pgb`, `poo`, `rcc`, `rcd`, `rcn`, `rcs`, `wip`, `xct` | S: `ov068.bin` |
| `ov070` | `grf` | S: `ov070.bin` |
| `ov071` | `ott` | S: `ov071.bin` |
| `ov072` | `seg` | S: `ov072.bin` |
| `ov073` | `boa` | S: `ov073.bin` |
| `ov074` | `mka` | S: `ov074.bin` |
| `ov075` | `plb` | S: `ov075.bin` |
| `ov076` | `seo` | S: `ov076.bin` |
| `ov077` | `mol` | S: `ov077.bin` |
| `ov078` | `cml` | S: `ov078.bin` |
| `ov079` | `wrl` | S: `ov079.bin` |
| `ov080`-`ov086` | `ttl` (seven separate overlays, same model) | S: `ov080.bin`..`ov086.bin` |
| `ov087` | `dnk` | S: `ov087.bin` |
| `ov088` | `upa` | S: `ov088.bin` |
| `ov004` | `hgs`, `pge`, `pla`, `tti` | S: `ov004.bin` |

`ov068` is the outlier: it names twelve stems rather than one, and it is the only overlay besides
`ov004` that names more than five [S: `ov068.bin`, path literals]. `ttl` is the other outlier —
seven overlays, `ov080` through `ov086`, each name the same model and nothing else
[S: `ov080.bin`..`ov086.bin`]. The four stems named by `ov004`, the game's own always-loaded C++
module, are the ones needed without an overlay swap [S: `ov004.bin`, path literals;
`docs/kb/modules/ov004.md`].

Special-character names come from `script/KOR/string/st_spnpc_name.bmg` (433 bytes)
[S: `extract/adm-kr/files/script/KOR/string/`, file name and size]. Their dialogue is the `sp`
branch of the message tree, which has two subdirectories, `etc` and `npc`, and 60 files
[S: `extract/adm-kr/files/script/KOR/message/sp/`, listing; `port/TAXI-ROAD.md`, `sp` = 60].

### Houses

Villager houses are `str/npcHs/` and `str/npcHsTex/`, addressed by `/str/npcHs/%d/%s%c.arc`,
`/str/npcHs/%d/%s%c.nsbtx`, `/str/npcHsTex/%c/house_%c%d%c.nsbtx` and
`/str/npcHsTex/%c/light_%c%d.nsbtx`, plus a shared `/str/npcHsX.arc`
[S: `extract/adm-kr/arm9_overlays/ov003.bin`, path-format string literals;
`extract/adm-kr/files/str/`, 80 files under `npcHs/` and 75 under `npcHsTex/`]. The `%c`
parameters are the season and variant letters the same directory uses for player houses
(`/str/plHsTex/home%c%c.nsbtx`, `/str/house_pl/house_pl_%c.nsbtx`) [S: same overlay, path
literals].

## Where it lives

| asset or table | location | count | grade/citation |
|---|---|---|---|
| villager models | `npc/model/<(id/8)*8>/<id>.nsbmd` + `.nsbtx` | 150 ids, 0-149 | S: `extract/adm-kr/files/npc/model/` |
| villager animations | `anm/<blk>/<n>.nsbca` | 324, 0-323 | S: `extract/adm-kr/files/anm/` |
| special-character models | `npc_sp/model/<stem>.nsbmd` + `<stem>_tex.nsbtx` | 37 stems, 73 files | S: `extract/adm-kr/files/npc_sp/model/` |
| special-character overlays | `ov004`, `ov045`-`ov088` | 32 overlays | S: `extract/adm-kr/arm9_overlays/` |
| villager dialogue | `script/KOR/message/{bo,ta,ge,fu,ko,ha}/` | 242 files each | S: `extract/adm-kr/files/script/KOR/message/` |
| special dialogue | `script/KOR/message/sp/{etc,npc}/` | 60 files | S: same |
| villager names / habits | `script/KOR/string/st_npc_name.bmg`, `st_npc_habit.bmg` | 2 banks | S: `extract/adm-kr/files/script/KOR/string/` |
| special names | `script/KOR/string/st_spnpc_name.bmg` | 1 bank | S: same |
| villager houses | `str/npcHs/`, `str/npcHsTex/`, `str/npcHsX.arc` | 156 files | S: `extract/adm-kr/files/str/` |
| personality prefix table | `0x020d72a4` | 6 pointers | S: `port/TAXI-ROAD.md`; `src/matched/func_0200366c.c` |

## Data it reads and writes

| field | meaning | who writes | who reads |
|---|---|---|---|
| villager id (0-149) | selects `npc/model/<(id/8)*8>/<id>.nsbmd` | the save's resident list | the villager loader [S: `extract/adm-kr/arm9/arm9.bin`, path literal] |
| personality (0-5) | indexes `0x020d72a4` to pick `bo_`/`ta_`/`ge_`/`fu_`/`ko_`/`ha_` | the villager record | `func_0200366c` [S: `src/matched/func_0200366c.c`] |
| special-character overlay id | selects which `npc_sp` model is resident | the scene machine | `FS_LoadOverlay` [S: `src/matched/FS_LoadOverlay.c`] |

## How to check it

The overlay-to-stem binding above is read from string literals, which proves the path is
*present* in the overlay, not that the overlay is the only loader. To confirm one binding live,
run to a scene where that character appears and record the loaded overlay set; the town recipe
(`../engine/file-system.md`) already reports overlays 5, 36, 54, 120 and 117 at frame 37,500
[E: `docs/log/cycle40-keyboard-gate-probe.md` TOWN40, run `tap-D56`]. Note that 54 is in that
list and `ov054` names `pga` and `pgb` — a matching prediction to check against the frame's
screenshot.

To re-derive the model census:

```bash
python - <<'PY'
import os, glob
ids = sorted(int(os.path.basename(p)[:-6]) for p in
             glob.glob(r"extract/adm-kr/files/npc/model/*/*.nsbmd"))
print(len(ids), ids[0], ids[-1], ids == list(range(150)))
stems = sorted({os.path.basename(p).split('.')[0].replace('_tex', '')
                for p in glob.glob(r"extract/adm-kr/files/npc_sp/model/*")})
print(len(stems))
PY
```

Expected: `150 0 149 True` and `37`.

## Hypotheses

- **The three-letter stems are species or character abbreviations.** Some readings are tempting
  (`rc*` for a four-member group, `owl`/`ows` for a pair) but nothing here identifies a single
  character by name, and a fan-wiki mapping is not evidence
  [H: `wiki/README.md`, the no-fan-wiki rule]. Settle it per character by loading its overlay in
  a scripted run, screenshotting the model, and pairing that with the name the dialogue box
  shows.
- **`ov068` is a shared "many special characters at once" module — most plausibly the ending or a
  festival scene — rather than one character's overlay.** It names twelve stems where every other
  special overlay names one to five [S: `ov068.bin`]. `docs/kb/modules/ov003-068.md` covers this
  overlay; settle it by reading that page's account against a run that loads it.
- **`ov080`-`ov086` are seven variants of one character (`ttl`) distinguished by behaviour, not
  by model.** All seven name the same two files and nothing else [S: `ov080.bin`..`ov086.bin`].
  Settle it by diffing the seven overlay code images for their entry points.
- **Villager id and personality are independent fields in the save record**, so any villager can
  in principle carry any of the six dialogue sets [H]. Settle it against `../systems/villagers.md`
  by reading the resident record's layout.
- **`anm/`'s 324 animations are shared across all 150 villagers**, since there is one animation
  tree and it is not indexed by villager id [S: `/anm/%d/%d.nsbca` has no villager parameter].
  Settle it by logging which animation index is requested while two different villagers walk.
- **`npc/ta_test.nsbtp` is leftover development data.** It is the only loose file in `npc/` and
  its name contains `test` [H]. Settle it by searching every module image for the string
  `ta_test` — if no module names it, nothing can open it.

## Related

- `rom-layout.md` — the directory census and the overlay table.
- `../engine/text-and-messages.md` — how a personality plus a label becomes a `.bmg` path.
- `../engine/overlays.md` — what the rest of the 148 overlays do.
- `items.md` — the parallel `PHead`/`PGls`/`PPal` scheme for the player's own appearance.
