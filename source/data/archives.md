# Archives and container formats

**Summary.** Almost every file in the ROM is wrapped in a four-byte `LZ77` magic followed by a
standard NitroSDK compression header, and inside that wrapper sits one of a small set of
Nintendo container formats: `NARC` archives, the `nsb*` 3D resource family, `MESGbmg1` message
banks, and one `SDAT` sound archive. Knowing the wrapper is what turns the file tree into
readable data: 8,120 of the 9,508 files start with `LZ77` and reveal nothing about their real
type until they are decompressed.

Grade note: **S** on this page covers both symbol tables / matched sources and bytes read
directly out of the extracted ROM image; image citations always name the file and the field.

## What happens

Of the 9,508 files, 8,120 begin with the four ASCII bytes `LZ77` [S: `extract/adm-kr/files/`,
first-four-bytes census across all files]. The word after that magic is the ordinary NitroSDK
compression header, low byte = type and upper 24 bits = decompressed size. 6,330 files carry
type `0x10`, the SDK's LZ77 [S: same census, byte 4 histogram]. The remaining 1,790 carry type
`0xf7`, and every one of them is a `.bmg` message file [S: same census; the 1,790 non-`0x10`
files are exactly the compressed subset of the 1,791 `.bmg` files]. The size field reads
plausibly in both cases — `script/KOR/select/select.bmg` is 2,080 bytes on disk with
`0x001380` = 4,992 in its size field, and `anm/0/0.nsbca` is 2,242 bytes with `0x000a34` =
2,612 [S: `extract/adm-kr/files/`, first 8 bytes of each file].

The port's own decompressor is the SDK routine `MI_UncompressLZ8`, and it is where the port
traced every surviving direct texture byte back to [S: `docs/kb/port/render.md`, VRAM
last-write tracing, host `0x008b932f` / `0x008b939a` in `port/shim/gfx/lz77.c`].

The 1,388 files that are *not* wrapped show their native magic directly, which is how the
format inventory below was taken [S: `extract/adm-kr/files/`, first-four-bytes census].

### NARC archives (`.arc`)

229 `.arc` files are stored uncompressed and start with `NARC` [S: census]. The header is the
NitroSDK generic one: magic, byte-order mark `FFFE`, version `0100`, total file size, header
size `0x0010`, block count 3 [S: `extract/adm-kr/files/str/bsize.arc`, bytes 0..16 read as
`NARC`, `fe ff`, `00 01`, `0x1730`, `0x0010`, `0x0003`]. The three blocks are `BTAF` (the file
allocation table), `BTNF` (the file name table) and `GMIF` (the packed images)
[S: `extract/adm-kr/files/str/bsize.arc`, `bg/grd_anm.arc`, `str/npcHsX.arc`, block magics at
the header-size offset]. `BTAF`'s first halfword is the entry count: `str/bsize.arc` holds 30
sub-files, `str/npcHsX.arc` 7, and `bg/grd_anm.arc` 6 [S: same files, `BTAF` +8].

Sub-files inside `GMIF` are themselves resource files with their own magic — `bg/grd_anm.arc`'s
first sub-file is a `BMA0` material animation and `str/npcHsX.arc`'s is a `BMD0` model
[S: same files, first four bytes of the `GMIF` payload].

The furniture and room-object directories pair an `.arc` with a same-named `.nsbtx`, one holding
geometry and the other the texture set: `ftr/0/0/0000.arc` beside `ftr/0/0/0000.nsbtx`, and
`roomObj/obj_cafe1.arc` beside `roomObj/obj_cafe1.nsbtx` [S: `extract/adm-kr/files/ftr/0/0/`,
`extract/adm-kr/files/roomObj/`, directory listings]. The code opens them as a pair from one
template pair, `/ftr/%d/%d/%04x.arc` and `/ftr/%d/%d/%04x.nsbtx`
[S: `extract/adm-kr/arm9_overlays/ov004.bin`, path-format string literals].

### The `nsb*` 3D resource family

The 3D resources use the NitroSystem G3D block magics: `BMD0` models (243 uncompressed of 767
`.nsbmd`), `BTX0` textures (515 of 3,017 `.nsbtx`), `BCA0` joint animations (80 of 591
`.nsbca`), `BTP0` texture-pattern animations (1 of 391 `.nsbtp`), `BVA0` visibility animations
(1 of 42 `.nsbva`), `BTA0` texture-SRT animations (2 of 6 `.nsbta`), and `BMA0` material
animations (all 4 `.nsbma`) [S: `extract/adm-kr/files/`, census by extension and magic]. These
are the resources the NNS G3D loaders in `autoload_2` consume: `NNS_G3dGetResDataByName`
(`0x021079ac`) walks the block dictionary, `NNS_G3dBindMdlTex` (`0x02104f38`) binds a model's
named textures to an `nsbtx`, and `NNS_G3dGetJntAnmSet` / `GetTexPatAnmSet` / `GetTexSRTAnmSet`
/ `GetVisAnmSet` (`0x02107b28`, `0x02107bdc`, `0x02107ba0`, `0x02107cd4`) fetch one animation
set each [S: `config/adm-kr/arm9/autoload_2/symbols.txt`; `src/matched/NNS_G3dGetResDataByName.c`,
`src/matched/NNS_G3dBindMdlTex.c`].

### `MESGbmg1` message banks (`.bmg`)

Exactly one `.bmg` in the ROM is stored uncompressed, `script/KOR/message/Other/test_.bmg`, and
it shows the format the other 1,790 decompress to [S: `extract/adm-kr/files/`, magic census].
Its header is `MESGbmg1`, a 32-bit file size that matches the file exactly (1,056), a block
count of 2, and an encoding byte of 2 [S: `extract/adm-kr/files/script/KOR/message/Other/test_.bmg`,
bytes 0..17]. The two blocks are `INF1` (224 bytes) and `DAT1` (800 bytes)
[S: same file, block magics at offset 32]. `INF1`'s header gives 16 entries of 12 bytes each,
and `DAT1`'s payload begins with a null entry followed by UTF-16LE text [S: same file, `INF1`
+8 = `0x0010`, `0x000c`; `DAT1` payload bytes]. Encoding 2 and the UTF-16 payload agree with the
SDK helper the ROM ships, `NNSi_G2dSplitCharUTF16` at `0x02104cec`
[S: `config/adm-kr/arm9/autoload_2/symbols.txt`; `src/matched/NNSi_G2dSplitCharUTF16.c`].

There is no packed message bank: all 1,791 `.bmg` files are loose and opened individually by
path [S: `extract/adm-kr/files/script/`, recursive census; `extract/adm-kr/arm9/arm9.bin`,
the five `%s/...bmg` path templates]. See `../engine/text-and-messages.md` for how a message
key becomes one of those paths.

### `SDAT` (`sound_data.sdat`)

The single sound archive is a NitroSDK `SDAT` container, 10,704,768 bytes, header size 64
[S: `extract/adm-kr/files/sound_data.sdat`, bytes 0..16]. Its `SYMB` symbol block is absent
(offset 0, size 0), so the sound entries have no names in the shipped ROM; `INFO` is 24,712
bytes at `0x40`, `FAT ` is 24,188 bytes at `0x60c8`, and `FILE` is 10,655,804 bytes at
`0xbf44` [S: same file, the four block offset/size pairs at offset 16]. See `music.md` for the
record counts inside `INFO`.

### The 2D menu formats (`.bch` / `.bsc` / `.bpl`)

`menu/` uses a private three-extension convention rather than any Nintendo container: `.bch`
character/tile graphics, `.bsc` screen maps and `.bpl` palettes, 385 / 177 / 175 files
[S: `extract/adm-kr/files/menu/`, extension census]. They carry no magic of their own — the
uncompressed ones start straight in data [S: same census, magic column shows raw byte patterns
such as `00000000` and `DDDD`]. The same triple appears with the older `nc*` spelling in the
loose `.bin` directories: `a_mes/` names its files `_ncg` (tiles), `_ncl` (palette) and `_nsc`
(screen) [S: `extract/adm-kr/files/a_mes/`, file names], and `sky/` uses the same suffixes
[S: `extract/adm-kr/files/sky/`, file names].

### `SPA ` particles

One particle archive, `spl/spl.spa`, 61,212 bytes, magic `SPA ` stored little-endian
[S: `extract/adm-kr/files/spl/spl.spa`, bytes 0..4].

## Where it lives

| container | files | magic | who reads it | grade/citation |
|---|---|---|---|---|
| LZ77 wrapper, type `0x10` | 6,330 | `LZ77` + `0x10` | `MI_UncompressLZ8` | S: image census; `docs/kb/port/render.md` |
| LZ77 wrapper, type `0xf7` | 1,790 | `LZ77` + `0xf7` | the message reader (all `.bmg`) | S: image census |
| `NARC` | 229 uncompressed | `NARC`+`BTAF`/`BTNF`/`GMIF` | archive loader | S: `str/bsize.arc` etc. |
| `BMD0`/`BTX0`/`BCA0`/`BTP0`/`BVA0`/`BTA0`/`BMA0` | 846 uncompressed | per format | `NNS_G3d*` in `autoload_2` | S: image census; `config/.../autoload_2/symbols.txt` |
| `MESGbmg1` | 1,791 (1 uncompressed) | `MESG` | the game's own BMG reader | S: `script/KOR/message/Other/test_.bmg` |
| `SDAT` | 1 | `SDAT` | `NNS_SndArcInit` @ `0x0210...` family | S: `sound_data.sdat`; `src/matched/NNS_SndArcInit.c` |
| `.bch`/`.bsc`/`.bpl` | 737 | none | the menu overlays | S: `extract/adm-kr/files/menu/` |
| `SPA ` | 1 | `SPA ` | the particle system | S: `spl/spl.spa` |

## Data it reads and writes

| structure | fields as the image shows them | grade/citation |
|---|---|---|
| LZ77 wrapper | `'LZ77'`, then u8 type + u24 decompressed size | S: image census; `select.bmg`, `anm/0/0.nsbca` |
| NARC header | magic, BOM `FFFE`, version `0100`, u32 size, u16 header size `0x10`, u16 blocks `3` | S: `str/bsize.arc` +0..16 |
| NARC `BTAF` | magic, u32 block size, u16 entry count, then start/end pairs | S: `str/bsize.arc` `BTAF` +8 = 30 |
| BMG header | `MESGbmg1`, u32 file size, u32 block count `2`, u8 encoding `2` | S: `test_.bmg` +0..17 |
| BMG `INF1` | magic, u32 size, u16 entry count, u16 entry size | S: `test_.bmg` `INF1` +8 = 16, 12 |
| SDAT header | `SDAT`, BOM, u32 size, u16 header size `64`, then SYMB/INFO/FAT/FILE offset+size | S: `sound_data.sdat` +0..48 |

## How to check it

Static, no run required:

```bash
python - <<'PY'
import os, collections
B = r"extract/adm-kr/files"
by = collections.defaultdict(collections.Counter)
for dp, dn, fn in os.walk(B):
    for f in fn:
        with open(os.path.join(dp, f), 'rb') as h:
            by[os.path.splitext(f)[1].lower()][h.read(4)] += 1
for e in sorted(by):
    print(e, dict(by[e].most_common(4)))
PY
```

Expected: `.arc` = 1,835 `LZ77` + 229 `NARC`; `.bmg` = 1,790 `LZ77` + 1 `MESG`; `.nsbtx` =
2,502 `LZ77` + 515 `BTX0`; `.sdat` = 1 `SDAT`.

## Hypotheses

- The `0xf7` compression type on every `.bmg` is not the SDK's `0x10`. It may be a distinct
  compression variant or an obfuscation of the text. Settle it by breakpointing the port's
  decompressor on a `.bmg` open (the message path in `../engine/text-and-messages.md`) and
  recording which routine consumes the buffer and what the first output bytes are — they should
  be `MESGbmg1` if the payload is a plain BMG.
- The size field after the type byte reads plausibly on the two files sampled, but has not been
  checked against an actual decompression. Settle it by decompressing one `0x10` file and one
  `0xf7` file and comparing the output length with the header field.
- `.bch`/`.bsc`/`.bpl` are assumed to be the NCGR/NSCR/NCLR payloads with headers stripped,
  by analogy with the `_ncg`/`_nsc`/`_ncl` naming in `a_mes/` and `sky/`. Settle it by tracing
  one `menu/title/bg.bch` load through `ov147` and seeing which VRAM region receives it and at
  what stride.
- The `NARC` `BTNF` name tables have not been read, so it is unknown whether sub-files inside
  the `ftr/` archives carry meaningful names. Settle it by parsing `BTNF` on `ftr/anm/anm.arc`.

## Related

- `rom-layout.md` — where these files sit and how many of each there are.
- `../engine/file-system.md` — the `FS_*` protocol that opens them.
- `../engine/graphics-pipeline.md` — what the `nsb*` resources become on screen.
- `music.md` — the inside of `sound_data.sdat`.
