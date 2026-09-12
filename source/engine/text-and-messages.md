# Text and messages

**Summary.** Every line of dialogue in the Korean release is a UTF-16 string in one of 1,791
loose `.bmg` files under `script/KOR/`. The game builds a path from a speaker personality and a
message label, opens that one file, and feeds the text to a typewriter that draws it glyph by
glyph. The glyphs do not come from the Nintendo font library: they come from four private
`font/font{A,B,C,D}` bitmap banks, and the library font stack that also ships in the ROM appears
to serve only the Wi-Fi UI. There is no packed message bank and no compiled string table.

## What happens

The message system is not in an overlay. The dialogue window class, its state tables, the input
handling, the BMG reader and the string object all live in the always-resident ARM9 static
module; overlays only *request* messages [H: source account: `port/TAXI-ROAD.md`, "The message system is not in
an overlay"; direct ROM-source provenance unresolved]. The window occupies two runs in `main`, `0x02066bd0`-`0x02068e00` and
`0x020a8100`-`0x020a9d60` [H: source account: `port/TAXI-ROAD.md`, subsystem table; direct ROM-source provenance unresolved].

A message is addressed by a label plus the speaker's personality. `func_0200366c` builds the key
`<personality>_<label>` from a six-pointer prefix table at `0x020d72a4` holding `bo_`, `ta_`,
`ge_`, `fu_`, `ko_`, `ha_` [S: `src/matched/func_0200366c.c`; source account: `func_0200366c`, `main`, `src/matched/func_0200366c.c`;
`port/TAXI-ROAD.md`, the message path trace]. `func_02067344` turns that key into a path of the
form `/script/KOR/message/<personality>/<group>/<name>_.bmg`
[S: `src/matched/func_02067344.c`; source account: `func_02067344`, `main`, `src/matched/func_02067344.c`]. `func_0206726c` opens it through
the BMG reader held at `self+0xb14` and hands the resulting text to the string object at
`self+0x14ac` [S: `src/matched/func_0206726c.c`; source account: `func_0206726c`, `main`, `src/matched/func_0206726c.c`]. The window is then
driven by a six-state pointer-to-member table; state 2's update is where a button press advances
a line [S: `src/matched/func_02066dc4.c`; source account: `func_02066dc4`, `main`, `src/matched/func_02066dc4.c`].

The path templates are compiled into the ARM9 image, and there are five of them, all built on
the same two or three `%s` components: `%s/%s.bmg`, `%s/%s/%s.bmg`, `%s/%s/%s/%s_.bmg`,
`%s/%s/Other/%s_.bmg` and `%s/Other/%s_.bmg`, plus a separate `/script/%s/select/%s.bmg` for the
choice lists [H: source account: `extract/adm-kr/arm9/arm9.bin`, path-format string literals; direct ROM-source provenance unresolved]. The `%s` that
carries the language is `KOR`, which is the only language directory shipped
[H: source account: `extract/adm-kr/files/script/`, one subdirectory; direct ROM-source provenance unresolved].

### The message tree

`script/KOR/` holds 1,791 `.bmg` files totalling 1,581,466 bytes in seven groups
[H: source account: `extract/adm-kr/files/script/KOR/`, recursive census; direct ROM-source provenance unresolved]. `message/` is 1,526 of them, split
into nine personality directories: `bo`, `ta`, `ge`, `fu`, `ha`, `ko`, plus `sp`, `obj` and
`Other` [H: source account: `extract/adm-kr/files/script/KOR/message/`, subdirectory listing; direct ROM-source provenance unresolved]. `bo` and `ta`
hold 242 files each in eighteen identically-named subdirectories — `3p`, `ai`, `ap`, `etc`,
`ev`, `q`, `q01`..`q07`, `q09`..`q12`, `tsu` — which is the second `%s` in the four-component
template [H: source account: `extract/adm-kr/files/script/KOR/message/bo/`,
`extract/adm-kr/files/script/KOR/message/ta/`, subdirectory listings and counts; direct ROM-source provenance unresolved]. The remaining
groups are `mail/` (168 files in `msg`, `ps`, `super`), `mailz/` (48 in `msga`, `msgb`, `psz`,
`superz`), `string/` (36 loose files), `bbs/` (10), `select/` (2) and `2d/` (1)
[H: source account: `extract/adm-kr/files/script/KOR/`, per-directory census; direct ROM-source provenance unresolved]. `string/` is where the item and
creature name banks live, including `obj_etc_fish.bmg` and `obj_etc_insect.bmg`
[H: source account: `extract/adm-kr/files/script/KOR/string/`, file names; direct ROM-source provenance unresolved].

### The BMG container

1,790 of the 1,791 files are compressed behind the ROM's `LZ77` wrapper; the single uncompressed
one, `script/KOR/message/Other/test_.bmg`, shows the format the rest decompress to
[H: source account: `extract/adm-kr/files/`, first-four-bytes census; direct ROM-source provenance unresolved]. Its header is `MESGbmg1`, a file-size
field that matches exactly, a block count of 2, and an encoding byte of 2 — the BMG code for
UTF-16 [H: source account: `extract/adm-kr/files/script/KOR/message/Other/test_.bmg`, bytes 0..17; direct ROM-source provenance unresolved]. The two
blocks are `INF1` (16 entries of 12 bytes) and `DAT1` (800 bytes), and `DAT1`'s payload is
UTF-16LE text after an initial null entry [H: source account: `extract/adm-kr/files/script/KOR/message/Other/test_.bmg`, bytes 0..17 file, `INF1` +8, `DAT1` payload; direct ROM-source provenance unresolved]. Every
`.bmg` carries compression type `0xf7` rather than the `0x10` used by the other 6,330 compressed
files in the ROM, so the message files are the only asset class with their own compression path
[H: source account: `extract/adm-kr/files/`, byte-4 histogram over all `LZ77`-wrapped files; direct ROM-source provenance unresolved].

The game's own BMG reader is unnamed in the ROM: no symbol anywhere in the tables contains
`bmg`, `msg`, `mes` or any other text-system word, and a content search of `src/matched/` for
`BMG`, `MESG`, `INF1`, `DAT1`, `MID1` or `STR1` returns nothing
[H: source account: `config/adm-kr/arm9/**/symbols.txt`, name sweep; `src/matched/`, content search;
`port/TAXI-ROAD.md`, "This ROM names things by asset path"; direct ROM-source provenance unresolved]. Every game-side text function is a
`func_02xxxxxx`.

### Character codes

Text reaches the glyph layer as 16-bit codes. The string walk reads them **big-endian** —
`(p[1] << 8) | p[0]` over the byte pair — and passes each to a virtual method
[S: `config/adm-kr/arm9/symbols.txt` (`func_020a9368` at 0x020a9368), `config/adm-kr/arm9/symbols.txt` (`main` at 0x02000c38); source account: `func_020a9368`, `main`, transcribed in `port/shim/game/glyphcode.c`, header]. The codes are
Unicode: a live probe of the port recorded `0xC548`, `0xB155` and `0xD558`, which are the Hangul
syllables 안, 녕, 하 [H: host-source account from `port/shim/game/glyphprobe.c`, header, recorded probe output; verify with a retained scripted run and frame using this page's recipe]. When a
code has no glyph the lookup falls back to `0xFF20`, FULLWIDTH COMMERCIAL AT
[S: `src/matched/func_020512d4.c`; source account: `func_020512d4`, `main`, `src/matched/func_020512d4.c`; `port/shim/game/glyphcode.c`,
header]. The SDK's own UTF-16 splitter, `NNSi_G2dSplitCharUTF16`, is present at `0x02104cec` but
belongs to the library stack rather than the game's own path
[S: `src/matched/NNSi_G2dSplitCharUTF16.c`; source account: `config/adm-kr/arm9/autoload_2/symbols.txt`; `src/matched/NNSi_G2dSplitCharUTF16.c`].

The only string primitives with real names are the four NitroSDK leaves in `autoload_2`:
`STD_ConcatenateString` `0x02128d58`, `STD_GetStringLength` `0x02128d88`, `STD_CopyLString`
`0x02128db0` and `STD_CopyString` `0x02128dec`
[S: `src/matched/STD_CopyString.c`; source account: `config/adm-kr/arm9/autoload_2/symbols.txt`; `src/matched/STD_CopyString.c` and siblings].
The game's own 16-bit-aware length routines carry no real name — the tables call them
`func_02051c8c_unk` and `func_020b4950_unk`, zero-sized `unknown` entries each sitting in a small
gap between two named symbols [S: `src/matched/STD_ConcatenateString.c`, `src/matched/STD_GetStringLength.c`, `src/matched/STD_CopyLString.c`, `src/matched/STD_CopyString.c`; source account: `config/adm-kr/arm9/symbols.txt`, both rows
`kind:function(thumb,size=0x0,unknown)`; `port/shim/game/u16len.c`,
`port/shim/game/textlen.c`, headers].

### Fonts

The game's fonts are four faces, each a fixed triple of `head`, `attr` and `img` files under
`font/` [H: source account: `extract/adm-kr/files/font/`, 12 files; direct ROM-source provenance unresolved]. Each `head` is exactly 8 bytes and reads as
a 32-bit glyph count followed by two 16-bit dimensions: fontA is 3,314 glyphs at 9x16, fontB is
3,891 at 7x8, fontC is 19 at 16x16, and fontD is 15 at 8x8
[H: source account: `extract/adm-kr/files/font/font{A,B,C,D}_head.bin`, all 8 bytes; direct ROM-source provenance unresolved]. The `img` sizes confirm a
1-bit-per-pixel bitmap: fontC's 19 glyphs at 16x16 are exactly 608 bytes and fontD's 15 at 8x8
exactly 120, both `count * w * h / 8` with nothing left over
[H: source account: `extract/adm-kr/files/font/fontC_img.bin` 608 bytes, `fontD_img.bin` 120 bytes; direct ROM-source provenance unresolved]. The 3,314
count for fontA is corroborated live: the port's probe printed `font 0x021c8230 glyphs 3314`
[H: host-source account from `port/shim/game/glyphprobe.c`, header, recorded probe output; verify with a retained scripted run and frame using this page's recipe].

`func_02051794` is the loader for those four triples [S: `src/matched/func_02051794.c`; source account: `func_02051794`, `main`,
`src/matched/func_02051794.c`; `port/TAXI-ROAD.md`, ACWW font loader row]. `func_020516b8` is
the code-to-glyph-index lookup over the attribute table and returns -1 on a miss
[S: `src/matched/func_020516b8.c`; source account: `func_020516b8`, `main`, `src/matched/func_020516b8.c`], `func_0205171c` fetches one glyph's
width record [S: `src/matched/func_0205171c.c`; source account: `func_0205171c`, `main`, `src/matched/func_0205171c.c`], and `func_020512d4`
and `func_0205156c` wrap the lookup with the `0xFF20` fallback
[S: `src/matched/func_020512d4.c`, `src/matched/func_0205156c.c`; source account: `src/matched/func_020512d4.c`, `src/matched/func_0205156c.c`]. `func_020a8e8c` dispatches
between the two wrappers on a flag at `self+0x7c` [S: `src/matched/func_020a8e8c.c`; source account: `func_020a8e8c`, `main`,
`src/matched/func_020a8e8c.c`]. fontA's attribute table is LZ77-compressed and holds 3,314
entries of `{u16 code, u8 width, u8}` [H: source account: `port/shim/game/glyphcode.c`, header; direct ROM-source provenance unresolved].

The NitroSystem G2D font stack is also in the ROM — 33 functions from `0x02102f1c` to
`0x02104d00`, all byte-matched, including `NNS_G2dFontFindGlyphIndex` `0x021031b8`,
`NNS_G2dCharCanvasDrawChar` `0x021038d4`, `DrawGlyph1D` `0x02103e2c`, `DrawGlyphLine`
`0x02104050`, `LetterChar` `0x02104208`, the four `NNSi_G2dTextCanvasDraw*` entry points at
`0x02104710`-`0x02104978`, and `NNSi_G2dUnpackNFT` `0x02104a28`
[S: `src/matched/NNS_G2dCharCanvasDrawChar.c`; source account: `config/adm-kr/arm9/autoload_2/symbols.txt`; `src/matched/NNS_G2dCharCanvasDrawChar.c` and
siblings]. It appears to be dead weight for the game proper: `DrawGlyph1D`, the largest renderer
in the cluster at 0x224 bytes, has no call sites anywhere in the ROM, and
`NNS_G2dFontFindGlyphIndex` and `NNS_G2dCharCanvasDrawChar` are called only from `autoload_2`
itself and from `ov001`, the Wi-Fi utility overlay [H: `port/TAXI-ROAD.md`, marked INFERENCE
there; the supporting negative is that `NFTR`, the format `NNSi_G2dUnpackNFT` reads, appears in
exactly one file in the whole ROM — `dwc/utility.bin`]. Settling this needs a call-site trace
under `ACWW_INTERP=1` while a normal dialogue box is on screen.

### The message-box artwork

The window's own graphics are the eighteen loose files in `a_mes/`, named on the
`a_mes[<variant>]_<layer>_<kind>.bin` pattern with `_ncg` tiles, `_ncl` palettes and `_nsc`
screen maps, one set per box skin plus four "ten" pointer-sprite variants and a title plate
[H: source account: `extract/adm-kr/files/a_mes/`, file names and sizes; `extract/adm-kr/arm9/arm9.bin`, the 14
`/a_mes/...` path literals; direct ROM-source provenance unresolved]. The title-plate members are requested by `ov147`
[H: source account: `extract/adm-kr/arm9_overlays/ov147.bin`, four `/a_mes/a_mes_ttl_*` path literals; direct ROM-source provenance unresolved].

### The keyboards

Text *entry* is a separate system in three overlays: `ov095`, `ov124` and `ov126`, 265 functions
between them [H: source account: `port/TAXI-ROAD.md`, keyboard trio row; direct ROM-source provenance unresolved]. The Hangul input method itself is the
game's own code, not a library: `func_020efc74` in `autoload_2` is a 0x7d0-byte on-screen
keyboard state machine for which no library source exists anywhere
[S: `src/matched/func_020efc74.c`; source account: `func_020efc74`, `autoload_2`, `src/matched/func_020efc74.c`, header]. The keyboard artwork
is `menu/han/` (16 Hangul pages) and `menu/chat2/` (11 key pages)
[H: source account: `extract/adm-kr/files/menu/han/` 34 files, `extract/adm-kr/files/menu/chat2/`;
`extract/adm-kr/arm9_overlays/ov124.bin` and `ov095.bin`, path literals; direct ROM-source provenance unresolved]. Like everything else
in the text system, none of it is named: ROM-wide searches for `kbd`, `keyboard`, `namein`,
`hangul`, `ime`, `moji`, `kana` and `yomi` return zero symbols, and the keyboard was found by
its assets [H: source account: `port/TAXI-ROAD.md`, "This ROM names things by asset path"; direct ROM-source provenance unresolved].

The stylus dispatcher for the town-name keyboard is `func_ov126_022a1228`, installed only as a
function pointer through the `ov126` relocation `0x022a1ff0 -> 0x022a1229`
[H: source account: `port/shim/ui/w40_ov126_022a1228_gateprobe.c`, header; direct ROM-source provenance unresolved]. Its gate reads the current touch
coordinates from two words in `autoload_3`, `0x021f6c58` (X) and `0x021f6c54` (Y)
[H: source account: `config/adm-kr/arm9/overlays/ov126/relocs.txt`, resolving the pool words at `0x022a0848` and
`0x022a084c`; `port/shim/ui/w90_ov126_022a07e8_touchwords.c`, header; direct ROM-source provenance unresolved]. The hit test is
`sub_229c54c` and the index-to-key-id lookup `sub_229c448`, both resolved by residency to
`ov095` on the measured path, and key id `0x100` is the confirm key
[S: `src/matched/func_ov126_022a04e8.c`; source account: `src/matched/func_ov126_022a04e8.c`; `port/shim/ui/w90_kbd_hittest_dispatch.c`, header].

## Where it lives

| function or symbol | module | role | grade/citation |
|---|---|---|---|
| `func_0200366c` | `main` | builds `<personality>_<label>` | S: `src/matched/func_0200366c.c` |
| `func_02067344` | `main` | key → `.bmg` path | S: `src/matched/func_02067344.c` |
| `func_0206726c` | `main` | opens the file, feeds the string object | S: `src/matched/func_0206726c.c` |
| `func_02066dc4` | `main` | dialogue state 2: advance on button | S: `src/matched/func_02066dc4.c` |
| `func_02051794` | `main` | loads `font{A..D}_{head,attr,img}` | S: `src/matched/func_02051794.c` |
| `func_020516b8` | `main` | code → glyph index, -1 on miss | S: `src/matched/func_020516b8.c` |
| `func_020512d4` / `func_0205156c` | `main` | lookup with the `0xFF20` fallback | S: `src/matched/func_020512d4.c` |
| `func_020a8e8c` | `main` | picks between the two lookups | S: `src/matched/func_020a8e8c.c` |
| `func_020efc74` | `autoload_2` | the Korean IME state machine | S: `src/matched/func_020efc74.c` |
| `NNSi_G2dSplitCharUTF16` `0x02104cec` | `autoload_2` | SDK UTF-16 cursor step | S: `src/matched/NNSi_G2dSplitCharUTF16.c` |
| `NNS_G2dFontFindGlyphIndex` `0x021031b8`, `GetGlyphIndex` `0x0210325c` | `autoload_2` | SDK code map (DIRECT/TABLE/SCAN) | S: `src/matched/NNS_G2dFontFindGlyphIndex.c`, `GetGlyphIndex.c` |
| `NNSi_G2dUnpackNFT` `0x02104a28` | `autoload_2` | unpacks an `NFTR` font | S: `src/matched/NNSi_G2dUnpackNFT.c` |
| `STD_CopyString` `0x02128dec` and three siblings | `autoload_2` | 8-bit string leaves | S: `src/matched/STD_CopyString.c` |
| `func_ov126_022a1228` | `ov126` | town-name keyboard touch dispatch | S: `port/shim/ui/w40_ov126_022a1228_gateprobe.c` |
| `sub_229c54c` / `sub_229c448` | `ov095` (by residency) | key hit test / key id | S: `src/matched/func_ov126_022a04e8.c` |

## Data it reads and writes

| address or field | meaning | who writes | who reads |
|---|---|---|---|
| `0x020d72a4` | six-pointer table of personality prefixes | ROM data | `func_0200366c` [S: `src/matched/func_0200366c.c`; source account: `port/TAXI-ROAD.md`] |
| `self+0xb14` | the window's BMG reader | window construction | `func_0206726c` [S: `src/matched/func_0206726c.c`; source account: `src/matched/func_0206726c.c`] |
| `self+0x14ac` | the window's string object | `func_0206726c` | the typewriter [S: `src/matched/func_0206726c.c`; source account: `src/matched/func_0206726c.c`] |
| `self+0x7c` | selects which glyph lookup runs | window setup | `func_020a8e8c` [S: `src/matched/func_020a8e8c.c`; source account: `src/matched/func_020a8e8c.c`] |
| `0x021c8230` | the loaded fontA record | `func_02051794` | the glyph lookups [H: host-source account from `port/shim/game/glyphprobe.c`; verify with a retained scripted run and frame using this page's recipe] |
| `0x020d1df4` | three-entry glyph-set table, 8 bytes each | ROM data | `func_020ad4fc` [S: `config/adm-kr/arm9/symbols.txt` (`func_020ad4fc` at 0x020ad4fc); source account: `port/shim/game/fontsetup.c`, header] |
| `0x021f49a0` | three 0x18-byte glyph-surface descriptors | `func_020ad4fc` | the canvas registrations [S: `config/adm-kr/arm9/symbols.txt` (`func_020ad4fc` at 0x020ad4fc); source account: `port/shim/game/fontsetup.c`] |
| `0x021f6c58` / `0x021f6c54` | current stylus X / Y | `port/shim/input/touch.c`; on hardware the touch sampler | the keyboard gates [H: source account: `config/.../ov126/relocs.txt`; direct ROM-source provenance unresolved] |
| BMG `INF1` entry, 12 bytes | one message record | the packer | the BMG reader [H: source account: `.../Other/test_.bmg`; direct ROM-source provenance unresolved] |

## How to check it

There is a known, reproducible defect that exercises the whole chain. Before the fix, a menu box
and a speech bubble rendered with correct position, colour, cursor, line breaks and box sizing
but every glyph identical; the bitmap was matched against all 7,239 glyphs of all four fonts and
hit exactly one — fontA glyph 383, which is `0xFF20`
[H: log/source account: `port/VISIBLE-STATE.md`, the glyph observation; receipt provenance unresolved]. The cause was `func_020a8e8c` dropping the
character code its caller passed in `r1`, so every code missed and every code fell back
[S: `src/matched/func_020a8e8c.c`; source account: `port/shim/game/glyphcode.c`, header; `port/tools/overrides.txt`, the `func_020a8e8c` row].
After the repair the probe printed `0xC548 -> 2313`, `0xB155 -> 1306`, `0xD558 -> 3167`
[H: host-source account from `port/shim/game/glyphprobe.c`, header; verify with a retained scripted run and frame using this page's recipe].

To re-run that check, enable the disarmed probe in `port/shim/game/glyphprobe.c` (it is `#if 0`
and not listed in `port/tools/overrides.txt`), rebuild through `python port/tools/pipeline.py`,
and run any recipe that reaches a dialogue box. Expected: a stream of distinct
`code in -> index out` pairs, not one pair repeated.

To verify the BMG container without running anything, read the first 48 bytes of
`extract/adm-kr/files/script/KOR/message/Other/test_.bmg`: `MESGbmg1`, file size 1,056, block
count 2, encoding 2, then `INF1` (224 bytes, 16 entries of 12) and `DAT1` (800 bytes).

## Hypotheses

- **The NNS G2D font stack is dead in the game proper and serves only the Wi-Fi UI.** The
  evidence is a call-site scan plus `NFTR` appearing in only `dwc/utility.bin`
  [H: `port/TAXI-ROAD.md`, marked INFERENCE]. Settle it by tracing calls to
  `NNS_G2dCharCanvasDrawChar` `0x021038d4` under `ACWW_INTERP=1` on a recipe that opens a
  dialogue box and one that opens the WFC screen (`ov146`), and comparing.
- **The `0xf7` compression type is specific to `.bmg`.** All 1,790 compressed message files carry
  it and no other file does [H: source account: `extract/adm-kr/files/`, byte-4 histogram; direct ROM-source provenance unresolved]. Whether it is a
  different algorithm or an obfuscation is unknown. Settle it by capturing the decompressed
  buffer at the message open and checking whether it begins `MESGbmg1`.
- **The string walk is big-endian while the BMG payload is UTF-16LE.** `func_020a9368` composes
  `(p[1] << 8) | p[0]` [H: source account: `port/shim/game/glyphcode.c`; direct ROM-source provenance unresolved], but the `DAT1` payload of `test_.bmg`
  reads as little-endian [H: source account: `port/shim/game/glyphcode.c` file; direct ROM-source provenance unresolved]. Either the reader byte-swaps on load or one of the two
  readings is of a different buffer. Settle it by dumping the first eight bytes of the string
  object's buffer at `self+0x14ac` immediately after `func_0206726c` returns.
- **`func_02068144`, the per-frame dialogue driver, and `func_020a9368`, the string walk, have no
  matched source.** They are named in prose only [H: `port/TAXI-ROAD.md`]. Settle it by adding
  them to the differential-check queue.
- **The eighteen `q*` subdirectories under each personality are conversation topics, and the
  `3p`/`ai`/`ap`/`etc`/`ev`/`tsu` siblings are categories.** This is inferred from names alone
  [H]. Settle it by logging the composed path at `func_02067344` across a long town run and
  correlating each directory with the on-screen situation.

## Related

- `../data/archives.md` — the `MESGbmg1` and `LZ77` containers in detail.
- `../data/rom-layout.md` — where `script/`, `font/`, `a_mes/` and `menu/han/` sit.
- `graphics-pipeline.md` — how a glyph bitmap becomes pixels.
- `file-system.md` — how `/script/KOR/.../x_.bmg` becomes bytes.

## Settled: who decompresses the chunked (0xf7) message files

The generic loaders (`func_02064b2c`, `func_020649ac`) do not dispatch on the type byte, on
the console or in the port; they never see a `.bmg`. The message window's readers
(`func_020a9540`..`func_020a982c`) go through `func_02064658` (main, Thumb, 0x194 bytes), a
random-access reader that tests `(type & 0xf0) == 0xf0`, takes the chunk size as
`0x20 << (type & 0xf)` (4,096 for 0xf7), reads the u16 cumulative table, and decompresses
only the chunks covering the requested range with a one-chunk cache; a type-0x00 chunk is
copied [S: `src/matched/func_02064b2c.c`, `src/matched/func_020649ac.c`, `src/matched/func_020a982c.c`; source account: `func_02064658` disassembly; port/shim/game/lzread.c]. On the interpreter path
that ROM code runs and calls the registered host `MI_UncompressLZ8` once per chunk, which
is why the town dialogue renders correctly [E: `tap-D63` 37,500 ; `scratchpad/cycle40/runs/tap-D63`]. Fixture:
`port/tools/test_lz77_f7.py` (3 checks, 2 calibrations) decodes a three-chunk file through
lzread.c + lz77.c against an independent Python decoder. The generic loaders now print a
one-shot witness if a 0xf7 container is ever handed to them.
