# Audit: data formats against public specifications

verified-at: 470df4ac 2026-09-09

**Purpose.** Eight wiki pages describe container formats that Nintendo, the NitroSDK and a
large reverse-engineering community have already documented. This page checks each structural
claim on those pages against the public record, records what the public record *adds*, and
turns the difference into work for the port and for the wiki.

**Grade P (public).** A public document — GBATEK, a format wiki, a tool's source — is grade
**P** and always carries a URL and a section. **P never replaces S, E or O.** A public spec
says what the format is *in general*; only `src/matched/`, a run, or the oracle says what this
ROM does. Where a P source and an S/E citation disagree, the S/E citation wins and the
disagreement is content (STYLE rule 7). Where P agrees with a measurement, the P citation is
corroboration and lets the wiki *name* fields it had only measured sizes for.

**Method.** Public sources were read first, then re-checked against bytes in
`extract/adm-kr/files/`. Only headers and structural fields were read; no asset contents were
copied into this page or the wiki. No run of the game was made. Where a check produced a new
measurement it is marked **[S: image]** with the file and field, in the same sense
`data/rom-layout.md` uses.

## Sources consulted

| source | URL | covers |
|---|---|---|
| GBATEK, DS Cartridge Header | `https://problemkaputt.de/gbatek-ds-cartridge-header.htm` | header fields, FNT/FAT/OVT offsets, CRCs |
| GBATEK, NitroROM and NitroARC File Systems | `https://problemkaputt.de/gbatek-ds-cartridge-nitrorom-and-nitroarc-file-systems.htm` | FNT sub-tables, FAT entries, overlay table |
| GBATEK, BIOS Decompression Functions | `https://problemkaputt.de/gbatek-bios-decompression-functions.htm` | SWI 0x11/0x12, the 4-byte compression header, LZ77 token encoding |
| GBATEK, DS Sound Files — SDAT | `http://problemkaputt.de/gbatek-ds-sound-files-sdat-sound-data-archive.htm` | SDAT header, INFO tables, FAT/FILE |
| GBATEK, Nitro Font Resource Format | `https://problemkaputt.de/gbatek-ds-cartridge-nitro-font-resource-format.htm` | NFTR/`RTFN`, FINF/CGLP/CWDH/CMAP |
| Feshrine, Nitro Composer (`*.sdat`) Specification | `https://www.feshrine.net/hacking/doc/nds-sdat.php` | SDAT record sizes, SSEQ/SBNK/SWAR |
| ndspy (`soundArchive.py`, `narc.py`, `_common.py`, `bmg`) | `https://github.com/RoadrunnerWMC/ndspy` | SDAT record structs, NARC, the shared Nitro header, BMG model |
| Pikmin TKB, BMG file | `https://pikmintkb.com/wiki/BMG_file` | BMG header offsets, encoding table, INF1/DAT1/MID1, 0x1A escapes |
| Custom Mario Kart wiki, BMG / 0x1A Escape Sequences | `https://wiki.tockdom.com/wiki/BMG_(File_Format)` (now `mkwiiki.org`) | escape-sequence rule |
| scurest, `nsbmd_docs.txt` and apicula FILETYPES | `https://github.com/scurest/nsbmd_docs` | BMD0/BTX0/BCA0/BTP0/BTA0 containers and subfiles |
| NSMBHD, Particle (`.spa`) documentation | `https://nsmbhd.net/thread/5255-tutorial-particle-spa-editing-tutorial-and-documentation/` | SPA header, reversed magic, version stamp |
| NintyFont NFTR notes | `https://deepwiki.com/hadashisora/NintyFont/5.2-nftr-format-(nintendo-ds)` | CMAP types, CWDH chaining, private font variants |

---

## The headline: the `0xf7` "compression type" is not a compression type

`data/archives.md` and `engine/text-and-messages.md` both carry the same open question — every
`.bmg` in the ROM begins `LZ77` followed by byte `0xf7` instead of the SDK's `0x10`, and
whether that is "a different algorithm or an obfuscation is unknown". It is neither. **`0xf7`
marks a chunked container whose chunks are ordinary NitroSDK type-`0x10` LZ77 streams**, and
all 1,790 compressed message files decompress with the decompressor the port already has.

The layout, read from the images and confirmed by decoding every file:

```
+0x00  4   'LZ77'
+0x04  1   0xf7                      container tag
+0x05  3   u24 total decompressed size
+0x08  2*N u16 chunk END offsets, cumulative, relative to the end of this table
           N = ceil(total / 4096); the last entry equals filesize - (8 + 2*N)
then, for each chunk:
       4   an ordinary NDS compression header: u8 type + u24 decompressed size
       ..  the chunk payload
```

Every chunk but the last decompresses to exactly 4,096 bytes. Chunk type is `0x10` (LZ77) in
every chunk of 1,787 files; three files carry one type-`0x00` (stored) chunk each —
`message/fu/ev/nbirth_.bmg`, `message/ha/tsu/friend_.bmg`, `message/ko/3p/ge_.bmg` — which is
the standard "incompressible, store it" case [S: image, those three files, chunk headers].

Verification, run over all 1,791 `.bmg` files: for each file the table's last entry equals
`filesize - headersize`; every chunk decompresses to exactly its declared size; the
concatenation equals the container's declared total; the result begins `MESGbmg1`; and the
BMG's own size field at +8 equals the decompressed length. **1,791 of 1,791 pass**
[S: image, `extract/adm-kr/files/script/KOR/**/*.bmg`, whole-corpus decode]. Chunk counts:
1,659 files are a single chunk, 132 are two or more, the largest being 16
[S: same decode]. The token encoding is exactly GBATEK's: a flag byte governing eight units,
MSB first, `len = (b0>>4)+3`, `disp = ((b0&0xF)<<8|b1)+1`
[P: GBATEK, BIOS Decompression Functions, LZ77 section].

Two consequences follow immediately, and both are actions rather than notes:

- The ROM's generic file loaders **cannot** be the ones that read a `.bmg`. `func_020648a0`,
  `func_020649ac` and `func_02064b2c` all test for the `LZ77` magic and then hand
  `header+4` straight to `MI_UncompressLZ8` with no type dispatch at all
  [S: `src/matched/func_020648a0.c`, `src/matched/func_020649ac.c`,
  `port/shim/fs/loadfile.c` (the shadowed `func_02064b2c`)]. On a `0xf7` file that reads the
  u16 chunk table as a flag byte and tokens, and produces garbage. Only three functions in
  `src/matched/` call `MI_UncompressLZ8` at all, and none of them walks a chunk table
  [S: `src/matched/`, call-site scan]. So the message system has its own reader, and it is one
  of the unmatched `func_02xxxxxx` bodies `engine/text-and-messages.md` already lists.
- The 4,096-byte chunk size plus a cumulative end-offset table is a **random-access** design:
  an `INF1` offset divided by 4,096 names the one chunk that has to be decompressed. That is a
  much better explanation of the format than obfuscation, and it predicts that the reader
  decompresses one chunk per message rather than the whole file [H: structure].

---

## 1. `engine/file-system.md`

| wiki claim | public source | verdict | action |
|---|---|---|---|
| FNT at header +0x40, FAT at +0x48, ARM9 OVT at +0x50, ARM7 OVT at +0x58 | P: GBATEK, DS Cartridge Header — the field table gives FNT offset 0x40 / size 0x44, FAT offset 0x48 / size 0x4C, ARM9 overlay 0x50/0x54, ARM7 overlay 0x58/0x5C | **confirmed**, and the sizes at +0x44/+0x4C/+0x54/+0x5C are named too | add the size fields to the page's table; they are what `FS_LoadArchive` bounds-checks against |
| the header image the firmware leaves at `0x027FFE00` | P: GBATEK, same page — the cartridge header is copied to `27FFE00h` at power-up | **confirmed** | none |
| the header image is 0x160 bytes | P: GBATEK gives ROM Header Size as 0x4000 for the *field*; the RAM copy is the first 0x160 bytes | **confirmed, but the two numbers are different things** | say which 0x4000 is: the header-size *field*, not the copy |
| FNT entries: length byte, top bit = directory, directory id masked `0xFFF` | P: GBATEK, NitroROM File Systems — FNT sub-tables hold ASCII names for files and sub-directories with exactly that type bit | **confirmed** | cite GBATEK beside the matched source |
| `FSArchiveFAT {u32 top; u32 bottom;}`, 8 bytes per file | P: GBATEK — FAT holds start/end ROM addresses, 8 bytes per file, up to 61,440 files | **confirmed** | note the 61,440 ceiling; this ROM's 9,508 files are far under it |
| overlay info header is 32 bytes: id, RAM address, RAM size, BSS size, sinit range, file id, compressed:24 + flag:8 | P: GBATEK, NitroROM — the OVT assigns overlay IDs to file IDs and carries load addresses | **confirmed in outline**; GBATEK does not name the `compressed:24 + flag:8` packing, the SDK header does | keep the S citation as primary; P is corroboration only |
| NARC validation is magic `NARC`, BOM `0xFFFE`, version `0x0100` | P: ndspy `_common.py` reads the BOM field as a little-endian u16 and treats `0xFEFF` as little-endian, `0xFFFE` as the byte-swapped variant | **confirmed and explained**: `str/bsize.arc` stores `FE FF` = 0xFFFE, so ACWW's NARCs are the swapped-BOM flavour, while its `BMD0`/`SDAT` files store `FF FE` = 0xFEFF [S: image, `str/bsize.arc` +4, `anm/0/0.nsbca` (decompressed) +4, `sound_data.sdat` +4] | add one sentence to `archives.md`: the two BOM spellings in this ROM are not an inconsistency, they are the two documented flavours, and a reader must accept both |
| NARC blocks are `BTAF`, `BTNF`, `GMIF` | P: ndspy `narc.py`, projectpokemon rawdb `nds/narc.py` | **confirmed** | none |

**Not contradicted, and worth adding:** GBATEK documents a header CRC-16 over `[0x000..0x15D]`
at +0x15E and a secure-area CRC-16 at +0x06C [P: GBATEK, DS Cartridge Header]. Neither appears
anywhere on the wiki. They are not save checksums and should not be confused with one, but a
porter reading `extract/adm-kr/header.yaml` will want to know they exist.

## 2. `engine/text-and-messages.md`

| wiki claim | public source | verdict | action |
|---|---|---|---|
| header is `MESGbmg1`, u32 file size, u32 block count, u8 encoding | P: Pikmin TKB, BMG file — 0x00 magic (8 B), 0x08 data size u32, 0x0C section count u32, 0x10 encoding u8 | **confirmed exactly** | cite the offsets, not just the field names |
| encoding byte 2 = UTF-16 | P: Pikmin TKB — 0 undefined, 1 CP1252, 2 UTF-16, 3 Shift-JIS, 4 UTF-8 | **confirmed** | — |
| "every line of dialogue ... is a UTF-16 string" | P: same table | **FALSE for 90 files.** 1,701 of the 1,791 `.bmg` files declare encoding 2; **90 declare encoding 3, Shift-JIS**, and their payloads really are Shift-JIS Japanese — the first message of `message/bo/ai/shop1_.bmg` begins with the double-byte codes for ウフフ、 [S: image, whole-corpus decode; `message/bo/ai/shop1_.bmg` DAT1 +1] | correct the summary sentence; add the finding below |
| the two blocks are `INF1` and `DAT1`, block count 2 | P: Pikmin TKB — INF1, DAT1, optional MID1 | **confirmed for all 1,791 files**: every file has exactly two blocks and none carries `MID1` [S: image, whole-corpus decode] | state the negative — no `MID1` anywhere — it means messages are addressed by index, never by id |
| `INF1` holds 16 entries of 12 bytes | P: Pikmin TKB — INF1 +0x08 u16 entry count, +0x0A u16 entry length; each entry is a u32 DAT1 offset then attribute bytes | **confirmed for the sampled file, wrong as a generalisation**: 1,528 files use 12-byte entries, **263 use 4-byte entries** — a bare offset with no attributes. The 4-byte files are the `string/` name banks [S: image, whole-corpus decode] | say the entry size is per-file and must be read from `INF1+0x0A`; a reader that assumes 12 walks the name banks off the end |
| `DAT1`'s payload is "UTF-16LE text after an initial null entry" | P: Pikmin TKB — DAT1 begins with a single empty string | **confirmed** | — |
| the string walk reads codes **big-endian**, `(p[1] << 8) \| p[0]` | — | **the wiki contradicts itself, and the expression is little-endian.** `(p[1]<<8)\|p[0]` composes the *second* byte as the high half, which is exactly a little-endian u16 load. The `DAT1` payload is UTF-16LE [S: image, `string/st_npc_name.bmg` decodes to Hangul only under LE]. There is no disagreement to settle | delete the Hypothesis "the string walk is big-endian while the payload is UTF-16LE"; it is a mislabelled reading, and leaving it invites someone to add a byte swap that would break the text |
| — (not on the page) | P: Pikmin TKB and Custom Mario Kart wiki — escape sequences begin with byte `0x1A`, followed by the total size of the sequence *including* the `0x1A` and the size field, then the control-code bytes | **present and heavily used.** `0x1A` occurs 143,657 times across the decompressed `DAT1` payloads. In the UTF-16 files the sequence is in 16-bit units — `001A 0006 0000` is a six-byte escape; in the Shift-JIS files it is byte-oriented — `1A 05 07 14 00` is a five-byte escape [S: image, `message/Other/test_.bmg` DAT1 +108, `message/bo/ai/shop1_.bmg` DAT1 +1] | add an "escape sequences" subsection; the typewriter must consume these, and a renderer that draws them produces exactly the "wrong glyph" class of defect the page already documents |
| the NNS G2D font stack is dead weight; the supporting negative is that `NFTR` appears in exactly one file, `dwc/utility.bin` | P: GBATEK, Nitro Font Resource Format, and NintyFont — **on DS the magic is stored reversed, as `RTFN`**, and the block magics are `FNIF`/`PLGC`/`HDWC`/`PAMC` | **the conclusion survives; the evidence as written was unsound.** A search for the ASCII `NFTR` would have missed every real DS font. Re-run with the correct magic: `RTFN` occurs in exactly one file, `dwc/utility.bin`, and in `autoload_2` (the library's own magic constant); `NFTR` occurs in `dwc/utility.bin` and in `ov001`, the Wi-Fi utility overlay [S: image, whole-tree magic scan] | rewrite the negative to cite `RTFN`; the corrected scan makes the hypothesis *stronger*, and it independently ties the font stack to `ov001` |
| the four private fonts are 1-bpp bitmaps, `count * w * h / 8` | P: GBATEK CGLP — glyph bitmaps are packed at the declared bit depth, `tileSize` bytes per glyph | **confirmed for all four**, and the packing is continuous with no per-row padding: fontA 3,314 × 9 × 16 / 8 = 59,652 bytes exactly, fontB 3,891 × 7 × 8 / 8 = 27,237 in a 27,240-byte file (3 bytes of tail) [S: image, `font/font{A,B}_img.bin` sizes] | state the no-row-padding fact; a 9-pixel-wide glyph crossing byte boundaries is precisely where a host renderer goes wrong |
| fontA's attribute table holds `{u16 code, u8 width, u8}` entries | — | **confirmed directly**: `font/fontD_attr.bin` is uncompressed, 60 bytes for 15 glyphs, and reads as `{0x002c, 7, 0}, {0x0030, 7, 0}, ...` [S: image, `font/fontD_attr.bin` +0]; fontA/B/C attr are `LZ77` type `0x10` wrappers whose declared sizes are 4 × count [S: image, those files +0..8] | cite fontD as the corroborating uncompressed case |

### The 90 Shift-JIS files

They are not scattered. Exactly fifteen message files per personality, in every one of the six
personality directories, declare encoding 3: eight under `q09/`, six under `ai/`, one under
`etc/` [S: image, whole-corpus decode, grouped by directory]. That regularity says these are
the *same fifteen messages* left untranslated in all six voices — Japanese source text that
survived localisation — rather than a deliberate mixed-encoding design.

For the port this is a live hazard, not trivia: a reader that trusts the summary sentence and
treats every `DAT1` as UTF-16 will feed Shift-JIS byte pairs to the glyph lookup, every code
will miss, and every glyph will fall back to `0xFF20` — the exact failure `func_020a8e8c`
already produced once for a different reason. Whether the ROM's own reader honours the encoding
byte is unknown and is the experiment below.

## 3. `data/rom-layout.md`

| wiki claim | public source | verdict | action |
|---|---|---|---|
| the extracted header carries the identity but not the FNT/FAT/OVT offsets | P: GBATEK — those fields exist in the real cartridge header at +0x40..+0x5C | **confirmed as a statement about `header.yaml`, not about the ROM.** The offsets exist on the cartridge; the extractor simply does not record them, because the packer recomputes them | reword so a reader does not conclude the cartridge lacks them |
| 9,508 files in 36 top-level directories plus `BUILDTIME` and `sound_data.sdat` | — | **confirmed**: the tree has exactly 36 top-level directories [S: image, root listing] | the page's directory table omits `broadcast/`, `caution/`, `shadow/` and `snowman/`; add them or say the table is partial |
| ARM9 overlay table entries carry base, code size, bss, ctor range, file id, compressed, signed | P: GBATEK, NitroROM — the OVT maps overlay IDs to file IDs with load addresses and additional information | **confirmed** | none |
| every path is a `printf`-style template compiled into the module that needs it | — | not a format claim; nothing public bears on it | none |

## 4. `data/archives.md`

| wiki claim | public source | verdict | action |
|---|---|---|---|
| the word after `LZ77` is "low byte = type, upper 24 bits = decompressed size" | P: GBATEK, BIOS Decompression — bits 0-3 reserved, bits 4-7 type (1 = LZ77), bits 8-31 decompressed size | **confirmed for the 6,330 type-`0x10` files**, whose LZ77 stream starts immediately at +8 [S: image, `anm/0/0.nsbca` +0..12] | note that the `LZ77` ASCII magic itself is *not* part of the SDK header — it is this game's four-byte prefix in front of it |
| 1,790 files carry type `0xf7`, "a distinct compression variant or an obfuscation" | P: GBATEK's type list has no `0xf7` | **resolved — see the headline section.** `0xf7` is a chunked container of ordinary type-`0x10` (and, three times, type-`0x00`) streams | replace both Hypotheses with the decoded layout; the "settle it by breakpointing the decompressor" experiment is no longer needed to answer *what* it is, only *who* reads it |
| the size field "reads plausibly ... but has not been checked against an actual decompression" | — | **checked.** Every `0xf7` file's declared total equals its decompressed length, and the BMG's own +8 size field agrees [S: image, whole-corpus decode] | close the Hypothesis |
| NARC header: BOM `FFFE`, version `0100`, header size `0x10`, 3 blocks | P: ndspy `narc.py`, rawdb | **confirmed**, with the BOM-flavour note from §1 | as §1 |
| `BTAF`'s first halfword after the block header is the entry count | P: ndspy reads the file count as a u32 at BTAF+0x08 and starts entries at +0x1C; other readers describe u16 count + u16 reserved | **compatible** — the upper halfword is zero in this ROM, so both readings give the same answer [S: image, `str/bsize.arc` BTAF +8 = `1e 00 00 00`] | say entries begin at BTAF+0x0C in the u16 reading and that ndspy's +0x1C offset is measured from file start, not block start, so the two are the same place |
| `.nsbmd`=`BMD0`, `.nsbtx`=`BTX0`, `.nsbca`=`BCA0`, `.nsbtp`=`BTP0`, `.nsbva`=`BVA0`, `.nsbta`=`BTA0`, `.nsbma`=`BMA0` | P: scurest `nsbmd_docs.txt` §Filetypes, apicula FILETYPES | **confirmed for BMD0/BTX0/BCA0/BTP0/BTA0**; scurest explicitly marks **BVA0 and BMA0 as undocumented** | keep the two undocumented ones as image observations; do not cite a spec that does not exist for them |
| G3D containers use the generic Nintendo header | P: scurest §Container Header — stamp, BOM 0xFEFF, version, file size, header size 16, subfile count, then a u32 offset array | **confirmed** | add that a `BMD0` may embed a `TEX0` directly, so a model is not always paired with an `.nsbtx` — which bears on the `ftr/` pairing claim in `items.md` |
| `spl/spl.spa`, 61,212 bytes, "magic `SPA ` stored little-endian" | P: NSMBHD — the file begins with the reversed bytes `" APS"`, then a version stamp, u16 particle count, u16 texture count, then block lengths and the texture block offset | **confirmed and greatly extended.** The first eight bytes are `20 41 50 53 30 32 5f 31`, i.e. the two reversed words `SPA ` and `1_20` — **SPA version 1.20**. The header then gives **235 particle emitters and 97 textures**, particle block 26,788 bytes, texture block 34,392 bytes at offset 26,820; 26,820 + 34,392 = 61,212 = the file size exactly [S: image, `spl/spl.spa` +0..0x1c] | replace the one-line entry with the decoded header; it is a free table for a page that currently says nothing about particles |
| `.bch`/`.bsc`/`.bpl` "carry no magic of their own" | P: none — this is a private convention | **unverifiable from public sources**; the `_ncg`/`_ncl`/`_nsc` analogy remains the best reading | note that the NitroSystem 2D formats also store reversed magics (`RGCN`, `RLCN`, `RCSN`), so a magic scan that looked for `NCGR` would have found nothing even if headers were present — re-run the scan with the reversed spellings before concluding the headers are stripped |

## 5. `data/music.md`

| wiki claim | public source | verdict | action |
|---|---|---|---|
| SDAT header: magic, BOM, size, header size 64, four block descriptors | P: GBATEK SDAT, Feshrine §Header — header size is `0x40`, unusually, where other Nitro files use `0x10`; blocks in the order SYMB, INFO, FAT, FILE | **confirmed exactly**, including block count 3 [S: image, `sound_data.sdat` +8..16] | note the 0x40 header size is a documented SDAT peculiarity, not a game quirk |
| the `SYMB` block is absent, offset 0 size 0, so nothing has a name | P: GBATEK — "the SYMB block exists in most SDAT files (except in some titles ...)"; when it is absent the block count is 3 and the descriptor pair is zero | **confirmed, and it is a supported configuration rather than an oddity** | keep the claim, add that stripping SYMB is documented behaviour; the Hypothesis "no name-based lookup can work" is settled by the spec, since INFO and FAT are index-based by design |
| `INFO` holds eight record tables, each a count followed by that many offsets | P: GBATEK / Feshrine — INFO's header is eight u32 record-table offsets at +0x08, and each table is `u32 count` then `count × u32` entry offsets, **0 meaning absent** | **confirmed**, and it explains the 34 zero SEQ offsets as the spec's own "absent entry" encoding rather than a hole to be explained | say so; the Hypothesis "the 34 undefined SEQ slots are cut music" is now a question about *why* the packer left gaps, not about what a zero means |
| the eight tables are SEQ, SEQARC, BANK, WAVEARC, PLAYER, GROUP, PLAYER2, STRM | P: GBATEK, same order | **confirmed**; PLAYER2 is the **stream player** table | rename PLAYER2 to STRMPLAYER on the page |
| record sizes derived by span arithmetic: SEQ 12, SEQARC 4, BANK 12, WAVEARC 4, PLAYER 8, GROUP variable, PLAYER2 —, STRM — | P: GBATEK + Feshrine + ndspy agree: SEQ 12 (10 used + 2 pad), SEQARC 4, BANK 12, WAVEARC 4, PLAYER 8, GROUP variable `4 + n*8`, **STRMPLAYER 24**, **STRM 12** (8 used + 4 pad) | **every measured size confirmed by an independent route**, and the two the wiki left blank are filled in | fill in 24 and 12; and name the fields — SEQ is `{u16 fileID, u16, u16 bankID, u8 vol, u8 cpr, u8 ppr, u8 playerID}`, BANK is `{u16 fileID, u16, u16 swarID[4]}` with `0xFFFF` for unused |
| "943 instrument banks is an unusually large number for 14 wave archives" | P: BANK records name up to four SWAR ids, `0xFFFF` = unused | **the Hypothesis is now cheap to settle statically** — decode all 943 records and histogram the four-id tuples; no run required | rewrite the experiment as a static one |
| FAT entry is 16 bytes, offset and size | P: Feshrine, GBATEK — `u32 offset` (absolute from the start of the SDAT), `u32 size`, 8 reserved bytes for runtime use | **confirmed**, and the reserved 8 bytes are named | add that the offset is absolute within the SDAT, which is what makes `NNS_SndArcGetFileAddress` a simple add |
| — | P: Feshrine §Sound File Headers — contained files are `SSEQ`, `SSAR`, `SBNK`, `SWAR`, `SWAV`, `STRM`, each with the standard 16-byte Nitro header | **untested here** | a one-line static check: histogram the first four bytes at each FAT offset. It converts the "3.2 MB file is one of the two streams" Hypothesis into a measurement, since a stream will read `STRM` |

⚠️ Public sources disagree on two SDAT records: OpenKh lists GROUP as 12 bytes and STRM as 8.
GBATEK, Feshrine and ndspy agree GROUP is variable and STRM's stride is 12 with 8 meaningful
bytes. The wiki's own span arithmetic measured GROUP as variable, which sides with the
majority — record that the wiki's measurement resolved a public disagreement.

## 6. `data/items.md`

Nothing on this page is a container-format claim; it is a census plus arithmetic, and no public
specification bears on `ftr_info/` or `item_info/` record sizes. Two format-level notes do
apply:

- The page assumes each furniture id pairs one `.arc` (geometry) with one `.nsbtx` (textures).
  Public G3D documentation says a `BMD0` **may** embed a `TEX0` subfile, so the pairing is a
  packing choice, not a format requirement [P: scurest `nsbmd_docs.txt` §Filetypes]. Cheap
  check: decompress a few `ftr/*/*/*.arc` members and count subfile stamps.
- The `NARC` `BTNF` name tables are still unread — the page's own Hypothesis. Public readers
  document the common stub (`08 00 00 00 01 00 00 00`, one implied root, no names)
  [P: ndspy `narc.py`], so the likely answer is "no names", and the check is four bytes long.

## 7. `data/villagers.md`

No container-format claims; the page is a census and an overlay-to-asset binding read from
string literals. Public sources add nothing and contradict nothing. One inherited correction:
its "personality prefix" and `.bmg` path account depends on `engine/text-and-messages.md`, so
the encoding-3 finding above applies to the villager dialogue tree — fifteen of each
personality's 242 files are Japanese.

## 8. `systems/save-data.md`

This is the page the public record helps most, because three independent save editors cover the
**Korean** release as a first-class region rather than as an afterthought.

| wiki claim | public source | verdict | action |
|---|---|---|---|
| the backup store is a 256 KB flash chip | P: WildEdit `core/source/utils/saveUtils.cpp`, `SaveUtils::getSave()` accepts exactly `0x40000`, `0x4007A` (a 122-byte DeSmuME `.dsv` footer), `0x80000`, `0x8007A` | **confirmed** by three editors and by the ROM's own `0x1202` identify word | say that a `.dsv` dump carries a 122-byte footer — `ACWW_SAVE` pointed at one would be 122 bytes long and silently wrong |
| two banks of `0x173fc` bytes | P: WildEdit `saveUtils.cpp` `SavCopyOffsets[4] = { 0x15FE0, 0x15FE0, 0x12224, 0x173FC }` indexed by `WWRegion { EUR, USA, JPN, KOR }`; the same four numbers in ACWW-Web-SaveEditor `assets/js/core/sav.js` and in the ACWW_Research wiki `Offset_Sizes` | **confirmed exactly, and independently of `func_020b5724`.** `0x173FC` is the *Korean* block size; `0x15FE0` is the Western one and `0x12224` the Japanese one — they are not competing readings of the same field | this is the strongest corroboration on the page: an S citation from the ROM and a P citation from four editors agreeing on `0x173FC`. Record both |
| the two banks are "a primary/backup pair rather than two independent slots" (Hypothesis) | P: WildEdit `core/source/Sav.cpp` `Sav::Finish()` fixes the checksum and then `memcpy`s the whole block from offset 0 to `SAVCOPY_OFFSET`; the JS twin does the same | **the editors treat copy 2 as a byte-identical clone, checksum field included** — which is the primary/backup reading, not two slots | the Hypothesis is answered for *editors*; whether the ROM alternates is still open. Keep the experiment but note what the editors assume |
| "the save record carries a checksum, but none has been found" | P: WildEdit `core/source/utils/checksum.cpp` `Checksum::Calculate` — sum every little-endian u16 word of the block, skipping the word at the checksum index, and store `(u16)-sum`; ACSE `ACSE.Core/Saves/Checksums/UInt16LEChecksum.cs` implements the identical routine; ACWW-Web-SaveEditor `assets/js/utils/checksum.js` returns `0x10000 - sum` | **found.** The checksum is a 16-bit little-endian word sum stored as its two's complement, so a valid block sums to zero. For Korea the field is at **`0x173F8`** — the last u16-aligned word of the block — and `UpdateChecksum` passes the word count `0xB9FC` (= `0x173F8 / 2`) | this closes the page's first Hypothesis at grade P. It does **not** close it at grade S: the ROM's own validity test in `func_020b5724` has still not been read. Restate the Hypothesis as "does `func_020b5724` compute this sum?" — a much narrower question with a known expected answer |
| — | P: ACWW_Research wiki `Offset_Sizes`; WildEdit `core/source/LetterStorage.cpp` | **a second checksummed region exists.** Letter storage sits at `0x337FC` for Korea, outside both banks, and has its own checksum at `0x3FFFE`, the last u16 of the 256 KB image, over `0xC802` bytes | add it. `2 × 0x173FC = 0x2E7F8`, so roughly 70 KB of the chip is *not* in either bank, and the page currently implies the banks are the whole store |
| — | P: WildEdit `saveUtils.cpp` — a save is accepted when the gamecode byte matches at offset 0 **and** at the start of the second copy; `GameCodes[4] = { 0xC5, 0x8A, 0x32, 0x32 }`, so Korea is `0x32`; `Town.cpp` treats town id `0x0000`/`0xFFFF` as "no town"; `Player.cpp` `exist()` is a non-zero player id | **an editor-level validity test, not the game's** | this is exactly the material for the page's "0xFF erased vs zeroed" Hypothesis: a zero-filled block has gamecode 0 and town id 0, which is *not* the same as an erased 0xFF block whose gamecode is 0xFF. Both are invalid, and they may take different branches |
| — | P: ACWW_Research wiki, *Character Encoding*: EUR/USA and JPN use a private 256-entry single-byte table; "**Korean uses UTF-16, or better more accurately UCS-2**". WildEdit reads Korean names with `ReadUTF16String` and every other region through `wwCharacterDictionary` | **directly relevant to the port and to `engine/text-and-messages.md`**: the Korean save stores names as UCS-2, the same 16-bit codes the glyph lookup consumes | add it; it means a name read out of the save can be handed to the glyph path with no translation, which is a testable prediction |
| — | P: ACWW_Research wiki + WildEdit `Sav.cpp`, `Player.cpp` — Korea: 4 player records of `0x249C` bytes starting at `+0x14` (not `+0x0C` as in every other region), villager block at `0x9284`, villager record `0x7EC`; town id at `+0x02`, town name at `+0x04` as 12 bytes of `char16_t` | **structural, and Korea-specific** | this is enough to start a `systems/save-data.md` "what is inside a bank" section at grade P, with the S work being to confirm each offset against a matched accessor |

⚠️ **Do not import ACSE's constants.** ACSE's `WildWorldOffsets` block and its `"EMDA" @ 0x1E40`
recognizer are US-only, and it ships no Korean character table. WildEdit and the ACWW_Research
wiki are the Korean-aware sources. One further source glitch: the research wiki's
`Main-Structure` page lists the Korean total as `0x12224`, duplicating the Japanese row;
`Offset_Sizes`, `saveUtils.cpp` and `sav.js` all say `0x173FC`, and the ROM agrees.

---

## Prioritised actions — the port

**P1. Teach the port's file loader the `0xf7` chunked container, or prove the ROM's own reader
handles it.** `func_02064b2c` in `port/shim/fs/loadfile.c` recognises the `LZ77` magic and
calls `MI_UncompressLZ8` on `header+4` regardless of the type byte. If any `.bmg` reaches that
loader, its text is garbage and nothing reports an error. *Evidence needed:* enable
`port/shim/gfx/w11_lztrace.c` on a recipe that opens a dialogue box and record, for each
`MI_UncompressLZ8` call, the first eight bytes at `src`. A source beginning `LZ77 f7` proves
the wrong path; a source beginning `10 xx xx xx` at a non-zero file offset proves the ROM has
its own chunk walker and identifies it by caller.

**P2. Find and name the message system's decompressor.** It is not `func_020648a0`,
`func_020649ac`, `func_02064b2c` or `func_ov001_0222b7c8` — those are the only four callers of
`MI_UncompressLZ8` in `src/matched/` and none reads a u16 chunk table. *Evidence needed:* the
caller identified by P1, then a differential check of that function; it is a small, pure,
self-contained body and therefore a cheap native promotion.

**P3. Make the typewriter honour BMG escape sequences and the encoding byte.** `0x1A` appears
143,657 times in the decompressed message payloads. The rule is documented: `0x1A`, then a
total length, then the control code — in 16-bit units for the encoding-2 files and in bytes for
the 90 encoding-3 files. *Evidence needed:* dump the first 16 bytes of the string object at
`self+0x14ac` immediately after `func_0206726c` returns on a message known to contain an escape
(any `message/*/q/*` file), and check whether the buffer still contains `1A` or whether the
reader already stripped it.

**P4. Settle the Shift-JIS files before they are hit.** Fifteen message files per personality
are Japanese in Shift-JIS. *Evidence needed:* run the town recipe far enough to open a `q09/`
conversation and screenshot the box; correct Japanese glyphs, garbage, or a wall of `＠`
(`0xFF20`) each identify a different bug. This is cheap and it is the kind of defect that would
otherwise be blamed on the glyph lookup for a second time.

**P5. Verify the four private fonts' packing in the host renderer.** The bitmaps are 1 bpp with
**no per-row padding** — fontA's 9-pixel-wide glyphs cross byte boundaries. *Evidence needed:*
render fontA glyph 383 (`0xFF20`, the known fallback) and one wide Hangul glyph and compare
against the oracle's frame; a renderer that pads rows to a byte produces a recognisable shear.

**P6. Give `ACWW_SAVE` a real image.** The checksum algorithm and the Korean offsets are now
known, so a *valid* 256 KB image can be constructed rather than only an erased one — gamecode
`0x32` at offset 0 and at `0x173FC`, a town id, and a checksum at `0x173F8` making the block
sum to zero. *Evidence needed:* run the keyed START recipe against such an image and see
whether the boot takes the existing-town branch at `func_020b5724` instead of stopping at
`unimplemented: func_02225a90`. That single experiment tests the port's card path, the wiki's
bank claim and the public checksum documentation at once.

**P7. Low priority — accept both NARC BOM spellings.** `IsValidArchiveBinary` requires
`0xFFFE`, which is right for this ROM. Any host-side NARC reader the port grows later must not
copy that requirement from a public reader that expects `0xFEFF`.

## Prioritised actions — the wiki

**W1. Rewrite the `0xf7` material on `data/archives.md` and `engine/text-and-messages.md`.**
Replace the two "unknown algorithm or obfuscation" Hypotheses with the decoded container. It is
the single largest correction on this page and it removes an experiment from the queue.
*Evidence:* the whole-corpus decode above; re-runnable in twenty lines of Python.

**W2. Correct "every line of dialogue is UTF-16" and add the 90 Shift-JIS files.**
*Evidence:* the encoding-byte histogram, plus the directory grouping (8 `q09/`, 6 `ai/`, 1
`etc/` per personality).

**W3. Delete the false big-endian/little-endian contradiction.** `(p[1]<<8)|p[0]` is a
little-endian load and the payload is little-endian. *Evidence:* `st_npc_name.bmg` decodes to
Hangul under LE and to nothing under BE.

**W4. Fix the `NFTR` negative to search `RTFN`.** *Evidence:* the corrected whole-tree scan —
`RTFN` in `dwc/utility.bin` and `autoload_2` only; `NFTR` in `dwc/utility.bin` and `ov001`.
Add the same warning for the reversed 2D magics (`RGCN`/`RLCN`/`RCSN`) to the `.bch`/`.bsc`/
`.bpl` paragraph, which currently concludes "no magic" from a scan that may have looked for the
wrong spelling.

**W5. Say that `INF1` entry size is per-file.** 1,528 files use 12-byte entries and 263 use
4-byte entries; the size is at `INF1+0x0A`. *Evidence:* the whole-corpus decode.

**W6. Fill in the SDAT records the wiki left blank and name their fields.** STRMPLAYER is 24
bytes, STRM 12; SEQ and BANK field lists are documented. Rename PLAYER2 to STRMPLAYER, and say
that a zero offset in an INFO table is the format's own "absent" encoding.

**W7. Start the inside of the save bank on `systems/save-data.md`.** The Korean offsets —
header `0x14`, four `0x249C` player records, villagers at `0x9284`, town id `+0x02`, UCS-2
names, checksum `0x173F8`, letter storage `0x337FC` with its own checksum at `0x3FFFE` — are
all grade P and all Korea-specific. Each becomes grade S the moment a matched accessor is found
reading it. *Evidence needed per row:* the function that reads the offset.

**W8. Replace `data/archives.md`'s one-line SPA entry with the decoded header.** Version 1.20,
235 emitters, 97 textures, and the two block lengths that sum to the file size.

**W9. Add the header CRC-16 fields to `data/rom-layout.md`** so nobody mistakes them for a save
checksum, and add the four missing top-level directories to its census table.

**W10. Convert three Hypotheses into static checks** now that the formats are known: the 943
BANK records' wave-archive tuples, the SDAT `FAT` magic histogram (which identifies the two
streams and the 3.2 MB file without a run), and `st_music.bmg`'s `INF1` entry count — which is
now readable, since the file decompresses.

## Related

- `../data/archives.md`, `../engine/text-and-messages.md` — the two pages this audit changes most.
- `../systems/save-data.md`, `../data/music.md` — the two it extends most.
- `../README.md` — the grade table this page's **P** grade sits beside, and the no-fan-wiki rule:
  a save editor's *source code* is a tool implementation, not a fan wiki's assertion, and is
  cited here as such. Where its numbers agree with a measured one, the measurement is still the
  evidence.
</content>
</invoke>
