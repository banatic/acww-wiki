# Fish and bugs

**Summary.** Fish and bugs are two small, parallel families. Each has a numbered set of 3D models
in its own directory, a second "held" model set for the catch pose, a 56-entry picture sheet for
the museum and the catalogue, and one message bank of names. The numbering is dense and
directory-mapped, so the counts can be read straight off the file tree: 59 fish model slots, 63
bug model slots, and 56 encyclopedia pictures for each family.

Grade note: **S** on this page covers symbol tables, matched sources, and bytes read directly out
of the extracted ROM image (path and field always named).

## What happens

### Fish

Fish models live under `fish/` in ten directories that fall into two groups
[S: `extract/adm-kr/files/fish/`, subdirectory listing]. Directories `00`, `01`, `02` and `03`
hold the swimming models, sixteen ids each except the last: `fish/00/` is `fish00`..`fish15`,
`fish/03/` runs to `fish58` [S: `extract/adm-kr/files/fish/00/`, `/03/`, listings]. Most ids have
both an `.nsbmd` and an `.nsbca`; `fish56`, `fish57` and `fish58` have a model only
[S: `extract/adm-kr/files/fish/03/`, listing]. That gives **59 fish model slots, ids 0-58**
[S: `extract/adm-kr/files/fish/`, counted over the `fish??` stems]. Two extras sit in `fish/03/`:
`fish_shadow` (the moving shadow in the water, model + animation) and `fish_hire` (model,
animation and a texture-SRT animation) [S: same listing].

The paths are compiled in two places. `arm9.bin` carries `/fish/0%d/fish%d.nsbca`,
`/fish/0%d/fish%d.nsbmd`, the zero-padded `fish0%d` variants, and the three literal
`fish/03/fish5N.nsbmd` names [S: `extract/adm-kr/arm9/arm9.bin`, path-format string literals];
`ov003` carries the shadow and `fish_hire` paths [S: `extract/adm-kr/arm9_overlays/ov003.bin`].

Directories `10` through `15` hold a second, separate model set with the `m_fish` prefix,
addressed from `ov004` by `/fish/%d/m_fish%d.nsbmd` and `/fish/%d/m_fish%d%d.nsbca`
[S: `extract/adm-kr/arm9_overlays/ov004.bin`, path literals]. The directory is `10 + id/10`:
`fish/15/` holds `m_fish50`..`m_fish55` with their `m_fish500`..`m_fish552` animations, where the
last digit is an animation index [S: `extract/adm-kr/files/fish/15/`, listing]. So the `m_fish`
set covers ids 0-55, three fewer than the swimming set
[S: `extract/adm-kr/files/fish/1*/`, counted stems].

### Bugs

Bugs follow the same shape with a different directory key. `insect/` has seven directories —
`01`, `11`, `21`, `31`, `41`, `51`, `61` — and each holds ten bug ids, twenty files, except `61`
which holds three [S: `extract/adm-kr/files/insect/`, per-directory counts]. `insect/61/` holds
`bug60`, `bug61` and `bug62`, so the range is **63 bug model slots, ids 0-62**
[S: `extract/adm-kr/files/insect/61/`, listing; `extract/adm-kr/files/insect/`, 129 files].

Unlike the fish, bugs use three different animation formats, chosen per bug. `insect/51/` shows
all three side by side: `bug50`, `bug51`, `bug52`, `bug56` and `bug57` carry an `.nsbva`
(visibility animation); `bug53`, `bug54`, `bug55` carry an `.nsbca` (joint animation); `bug58`
and `bug59` carry both `.nsbca` and `.nsbta` (texture SRT)
[S: `extract/adm-kr/files/insect/51/`, listing]. `ov004` carries the templates for all seven
directories — `/insect/01/bug0%d`, `/insect/11/bug%d` and so on up to `/insect/61/bug%d` — plus
the specific `/insect/51/bug52.nsbmd`, `/insect/51/bug52.nsbva`, `/insect/51/bug57`,
`/insect/61/bug61`, `/insect/61/bug62` and `/insect/61/bug%d.nsbta`
[S: `extract/adm-kr/arm9_overlays/ov004.bin`, path literals]. `ov003` adds
`/insect/51/bug%d.nsbta` [S: `extract/adm-kr/arm9_overlays/ov003.bin`].

### Encyclopedia pictures

Both families share one picture scheme. `menu/fish_pic/` and `menu/bug_pic/` each hold five
directories numbered `0`..`4`, each with a `<n>.bpl` palette and a run of `<n>_<ii>.bch` tile
sheets: `0` holds `0_00`..`0_11` and `4` holds `4_48`..`4_55`
[S: `extract/adm-kr/files/menu/fish_pic/0/`, `/4/`; `extract/adm-kr/files/menu/bug_pic/4/`,
listings]. The second number is the creature index and it is continuous across directories, so
each family has **56 pictures, indices 0-55**, in 61 files
[S: `extract/adm-kr/files/menu/fish_pic/`, 56 `.bch` + 5 `.bpl`;
`extract/adm-kr/files/menu/bug_pic/`, the same]. The screen that displays them is `ov114`, which
carries `menu/fish/a_bg.bsc`, `menu/fish/bug_bg.bch` and their companions — one overlay for both
families [S: `extract/adm-kr/arm9_overlays/ov114.bin`, path literals].

### Names and text

Names come from two message banks: `script/KOR/string/obj_etc_fish.bmg` (4,239 bytes) and
`obj_etc_insect.bmg` (4,214 bytes) [S: `extract/adm-kr/files/script/KOR/string/`, file names and
sizes]. Two more banks carry the time-of-day and season phrasing the dialogue uses when a
creature is discussed: `st_fish_time.bmg` (99 bytes) and `st_insect_time.bmg` (116 bytes)
[S: same directory]. The catch announcements are `script/KOR/message/obj/etc/getfish_.bmg` and
`getinsect_.bmg` [S: `extract/adm-kr/files/script/KOR/message/obj/etc/`, listing], and the
bulletin board has fishing and bug-catching tournament banks, `bbs_fishing.bmg` and
`bbs_insect.bmg` [S: `extract/adm-kr/files/script/KOR/bbs/`, listing].

## Where it lives

| asset | location | count | grade/citation |
|---|---|---|---|
| swimming fish models | `fish/0<0-3>/fish<id>.nsbmd` (+`.nsbca`) | 59 ids, 0-58 | S: `extract/adm-kr/files/fish/00..03/` |
| fish shadow / hire | `fish/03/fish_shadow.*`, `fish_hire.*` | 2 sets | S: `extract/adm-kr/files/fish/03/` |
| held fish models | `fish/1<0-5>/m_fish<id>.nsbmd` (+`.nsbca`) | 56 ids, 0-55 | S: `extract/adm-kr/files/fish/10..15/` |
| bug models | `insect/<d1>1/bug<id>.nsbmd` | 63 ids, 0-62 | S: `extract/adm-kr/files/insect/` |
| bug animations | `.nsbva`, `.nsbca` or `.nsbca`+`.nsbta`, per bug | mixed | S: `extract/adm-kr/files/insect/51/` |
| fish pictures | `menu/fish_pic/<0-4>/<n>_<ii>.bch` + `<n>.bpl` | 56 + 5 | S: `extract/adm-kr/files/menu/fish_pic/` |
| bug pictures | `menu/bug_pic/<0-4>/<n>_<ii>.bch` + `<n>.bpl` | 56 + 5 | S: `extract/adm-kr/files/menu/bug_pic/` |
| encyclopedia screen | `ov114`, `menu/fish/` | 13 files | S: `extract/adm-kr/arm9_overlays/ov114.bin` |
| names | `script/KOR/string/obj_etc_fish.bmg`, `obj_etc_insect.bmg` | 2 banks | S: `extract/adm-kr/files/script/KOR/string/` |
| catch text | `script/KOR/message/obj/etc/getfish_.bmg`, `getinsect_.bmg` | 2 banks | S: `.../message/obj/etc/` |
| loaders | `ov003`, `ov004` | path literals | S: `extract/adm-kr/arm9_overlays/ov003.bin`, `ov004.bin` |

## Data it reads and writes

| field | meaning | who writes | who reads |
|---|---|---|---|
| fish id | selects `fish/0<id/16>/fish<id>.nsbmd` and `fish/1<id/10>/m_fish<id>.nsbmd` | the fishing system | `ov003` / `ov004` loaders [S: `ov003.bin`, `ov004.bin`] |
| bug id | selects `insect/<(id/10)*10+1>/bug<id>.nsbmd` | the bug system | `ov004` loader [S: `ov004.bin`] |
| picture index (0-55) | selects `menu/<family>_pic/<i/12>/<i/12>_<ii>.bch` | the encyclopedia | `ov114` [S: `ov114.bin`] |

## How to check it

Static census:

```bash
python - <<'PY'
import glob, os, re
fish = sorted({int(m.group(1)) for p in glob.glob(r"extract/adm-kr/files/fish/0*/fish*.nsbmd")
               for m in [re.match(r"fish(\d+)\.nsbmd", os.path.basename(p))] if m})
bug  = sorted({int(m.group(1)) for p in glob.glob(r"extract/adm-kr/files/insect/*/bug*.nsbmd")
               for m in [re.match(r"bug(\d+)\.nsbmd", os.path.basename(p))] if m})
pic  = sorted({int(os.path.basename(p).split('_')[1][:2])
               for p in glob.glob(r"extract/adm-kr/files/menu/fish_pic/*/*_*.bch")})
print(len(fish), fish[-1], len(bug), bug[-1], len(pic), pic[-1])
PY
```

Expected: `59 58 63 62 56 55`.

A live check needs a scene with a creature in it, which the interpreter path has not yet reached:
the furthest recorded frame is the town at 37,500 with the town hall visible
[E: `docs/log/cycle40-keyboard-gate-probe.md` TOWN40, run `tap-D56`]. Until a run gets a net or
a rod in hand, everything on this page is file-tree structure rather than observed behaviour.

## Hypotheses

- **56 is the real creature count for each family and the extra model slots are variants.** The
  encyclopedia has exactly 56 pictures per family, but there are 59 fish models and 63 bug models
  [S: the census above]. Settle it by reading the entry count out of `obj_etc_fish.bmg`'s `INF1`
  header after decompression — a name bank should have one entry per catchable creature.
- **`fish56`, `fish57` and `fish58` are non-catchable objects** — they are the only swimming
  models with no `.nsbca` and they are named as literals rather than reached through the template
  [S: `extract/adm-kr/files/fish/03/`; `extract/adm-kr/arm9/arm9.bin`, the three literal paths].
  Settle it by finding which function loads those three literals.
- **`m_fish` is the "held up after catching" model and `fish_shadow` is the silhouette that moves
  in the water.** Both readings come from the names and from the fact that `m_fish` is loaded by
  `ov004` (the game's own module) while the swimming models are loaded from `arm9.bin` [H].
  Settle it by screenshotting a catch under a scripted run.
- **`fish_hire` is the fishing-tournament or Chip-related model.** The stem is opaque and it is
  the only fish asset with a `.nsbta` [H]. Settle it the same way.
- **The bug animation format encodes behaviour class** — `.nsbva` for bugs that only blink in and
  out, `.nsbca` for bugs with moving parts, `.nsbta` for scrolling wing texture [H: the split in
  `insect/51/`]. Settle it by loading each of the three kinds and describing the motion.

## Related

- `rom-layout.md` — the directory census.
- `archives.md` — `nsbmd`/`nsbca`/`nsbva`/`nsbta` and the `.bch`/`.bpl` menu formats.
- `items.md` — the same icon-sheet and message-bank pattern for items.
- `../engine/text-and-messages.md` — the `string/` banks the names come from.
