# Data

Tables and archives: structure, location, counts, and how to read them (no dumps).

| page | what it answers |
|---|---|
| `rom-layout.md` | the cartridge: modules, addresses, the 148 overlays, the 36 resource directories |
| `archives.md` | the container formats — the `LZ77` wrapper, `NARC`, `MESGbmg1`, `SDAT`, `nsb*`, `.bch`/`.bsc`/`.bpl` |
| `items.md` | furniture and item ids, the `ftr_info`/`item_info` tables, clothes, wallpaper, player parts |
| `villagers.md` | 150 villager models, 37 special characters, and the overlay each special character has |
| `fish-and-bugs.md` | 59 fish and 63 bug model slots, the 56-entry encyclopedia sheets, the name banks |
| `music.md` | inside `sound_data.sdat`: the record counts and the 78-function sound library |

## Grade convention on these pages

`STYLE.md`'s grades apply unchanged, with one clarification these pages need. **S** here covers
two kinds of citation:

1. a symbol table (`config/adm-kr/**/symbols.txt`) or a matched source (`src/matched/*.c`), as in
   the rest of the wiki; and
2. **bytes read directly out of the extracted ROM image** under `extract/adm-kr/` — a directory
   census, a file size, a container header field, or a `printf`-style path template read out of a
   module's string data.

Image citations always name the file and say which field or property was read, so any claim can
be re-derived with a few lines of Python. Most pages here carry such a snippet under **How to
check it**, with the expected output; run it from the repository root, where `extract/` lives.

What an image citation does *not* establish is behaviour. That a path template exists in
`ov004.bin` proves `ov004` can build that path, not that it is the only module that opens those
files, and not that the file is ever opened at all. Wherever a page turns file-tree structure
into a claim about what the game does, the claim is a **H** with the experiment that would
settle it.

## Boundaries specific to data pages

- Record *structure* only, never a dump. Entry counts, strides, field meanings and how to index
  are content; the contents are not.
- Item, villager, fish and bug **names** may be listed only as a short illustrative sample (at
  most five) and only where a name is needed to identify a table. None of these pages currently
  needs one: the name banks are cited by file, not quoted.
- Numbers from fan wikis are not evidence. Where a measured count differs from a familiar one,
  the measured count stands and the difference becomes a Hypothesis.
