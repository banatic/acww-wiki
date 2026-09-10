# Graphics pipeline

**Summary.** ACWW draws the world with the DS's 3D geometry engine and everything around it —
sky, message boxes, menus, the HUD — with the two 2D engines. Models arrive as NitroSystem G3D
resources, are bound to textures by name, and are submitted as pre-packed display lists straight
into the geometry FIFO at `0x04000400`. The 2D side is ordinary NDS: text and affine backgrounds
composited by priority, sprites from OAM, and colour special effects on top. Which engine owns
which physical screen is a runtime decision written into `POWCNT1`.

## What happens

### Resources in

A model is an `nsbmd` (`BMD0`) and its textures an `nsbtx` (`BTX0`); animations are `nsbca`,
`nsbtp`, `nsbta`, `nsbva` and `nsbma` [S: `extract/adm-kr/files/`, magic census — see
`../data/archives.md`]. `NNS_G3dGetResDataByName` at `0x021079ac` is the dictionary lookup that
finds a named block inside a resource [S: `src/matched/NNS_G3dGetResDataByName.c`], and
`NNS_G3dBindMdlTex` at `0x02104f38` walks a model's texture-to-material dictionary binding each
named texture, returning FALSE if any name is missing from the `nsbtx`
[S: `src/matched/NNS_G3dBindMdlTex.c`]. The palette twin is `NNS_G3dBindMdlPltt` `0x02104d7c`
[S: `config/adm-kr/arm9/autoload_2/symbols.txt`]. Texture bytes go to VRAM through
`NNS_G3dTexLoad` `0x0210518c`, which brackets `GX_BeginLoadTex` / `GX_LoadTex` /
`GX_EndLoadTex` and handles the 4x4-compressed pair as two writes
[S: `src/matched/NNS_G3dTexLoad.c`]. Space for those textures is handed out by the graphics
foundation allocator `NNS_GfdAllocFrmTexVram` `0x02102a54`, which returns a packed texture key
[S: `src/matched/NNS_GfdAllocFrmTexVram.c`].

Animation sets are fetched one kind at a time: `NNS_G3dGetJntAnmSet` `0x02107b28`,
`NNS_G3dGetMatCAnmSet` `0x02107b64`, `NNS_G3dGetTexSRTAnmSet` `0x02107ba0`,
`NNS_G3dGetTexPatAnmSet` `0x02107bdc`, `NNS_G3dGetVisAnmSet` `0x02107cd4`
[S: `config/adm-kr/arm9/autoload_2/symbols.txt`].

### Geometry out

Drawing one shape is `NNS_G3dDraw1Mat1Shp` `0x02107088`: it applies the material and
texture-matrix animation results, submits the shape's pre-packed display list with
`NNS_G3dGeSendDL((u8*)shp + shp->ofsDL, shp->sizeDL)`, and re-applies the inverse position scale
[S: `src/matched/NNS_G3dDraw1Mat1Shp.c`]. The submission path is the four ITCM routines:
`NNS_G3dGeSendDL` `0x01ff8d4c` sends lists under 256 bytes through the buffer and larger ones by
DMA; `NNS_G3dGeBufferOP_N` `0x01ff8bd0` either buffers an op word plus N arguments into the
0xc0-word command buffer or writes the op straight to the FIFO at `0x04000400` and streams the
arguments with `MI_CpuSend32`; `NNS_G3dGeFlushBuffer` `0x01ff8ccc` waits on any in-flight DMA and
ships the whole buffer; `NNS_G3dGeWaitSendDL` `0x01ff8e18` spins until the async DMA completes
[S: `src/matched/NNS_G3dGeSendDL.c`, `NNS_G3dGeBufferOP_N.c`, `NNS_G3dGeFlushBuffer.c`,
`NNS_G3dGeWaitSendDL.c`; `config/adm-kr/arm9/itcm/symbols.txt`]. Those four are the G3D
submission members of ITCM, not the whole of it: `itcm` holds 158 function symbols, 114 of them
named, including the thirteen `NNSi_G3dFuncSbc_*` scene-graph opcodes, the whole `MTX_*`/`VEC_*`
/`FX_*` fixed-point library, `OS_IrqHandler`, `OS_Halt`, `OS_SaveContext`/`OS_LoadContext`,
`OS_GetTick` and the display-object steppers [S: `config/adm-kr/arm9/itcm/symbols.txt`, counted
over `kind:function` lines; see `memory-map.md` and `display-objects.md`].

Global 3D state — lights, material defaults, scale factors — lives in one block that
`NNS_G3dGlbInit` `0x02105884` seeds and `NNS_G3dGlbFlushP` `0x02105844` ships to the engine as
0x3e words, clearing two dirty bits at +0xFC
[S: `src/matched/NNS_G3dGlbInit.c`, `src/matched/NNS_G3dGlbFlushP.c`]. A light direction is
packed into one `LIGHT_VECTOR` word as three 10-bit fields plus the light id in bits 30-31
[S: `src/matched/NNS_G3dGlbLightVector.c`]. `NNS_G3dInit` `0x021072e4` calls `G3X_Init`, then
`NNS_G3dGlbInit`, then sets the GXSTAT FIFO-IRQ field at `0x04000600`
[S: `src/matched/NNS_G3dInit.c`].

Below NNS sits the SDK's own geometry layer. `G3X_Init` `0x0211265c` names the whole register
set the pipeline uses: `DISP3DCNT` `0x04000060`, `EDGE_COLOR` `0x04000330`, `CLEAR_COLOR`
`0x04000350`, `CLEAR_DEPTH` `0x04000354`, `CLRIMAGE_OFFSET` `0x04000356`, `FOG_COLOR`
`0x04000358`, `FOG_OFFSET` `0x0400035c`, `FOG_TABLE` `0x04000360`, `TOON_TABLE` `0x04000380`,
`POLYGON_ATTR` `0x040004a4`, `TEXIMAGE_PARAM` `0x040004a8`, `TEXPLTT_BASE` `0x040004ac`,
`END_VTXS` `0x04000504` and `GXSTAT` `0x04000600` [S: `src/matched/G3X_Init.c`]. Matrix results
are read back out of `CLIPMTX_RESULT` `0x04000640` and `VECMTX_RESULT` `0x04000680` after
waiting on the GXSTAT busy bit `0x08000000` [S: `src/matched/G3X_GetClipMtx.c`,
`src/matched/G3X_GetVectorMtx.c`]. The matrix stack levels are GXSTAT bits `0x1f00` (position)
and `0x2000` (projection), with the error bit at `0x4000`
[S: `src/matched/G3X_GetMtxStackLevelPV.c`, `G3X_GetMtxStackLevelPJ.c`].
`NNS_G3dGetCurrentMtx` `0x021073a8` uses that read-back path: it flushes, pushes an identity
projection through ports `0x04000440`/`0x04000444`/`0x04000454`/`0x04000448`, and polls the
result registers [S: `src/matched/NNS_G3dGetCurrentMtx.c`].

### VRAM

The nine VRAM banks are assigned by the `GX_SetBankFor*` family in `autoload_2`, all writing the
`VRAMCNT` bytes at `0x04000240`-`0x04000249` (index 7 is `WRAMCNT` and is skipped):
`GX_SetBankForBG` `0x02111740`, `ForOBJ` `0x021115d4`, `ForSubBG` `0x02110e4c`, `ForSubOBJ`
`0x02110dd0`, `ForTex` `0x02111204`, `ForTexPltt` `0x02111110`, `ForBGExtPltt` `0x021114c0`,
`ForOBJExtPltt` `0x02111408`, `ForClearImage` `0x02110fd0`, `ForLCDC` `0x02110ef8`, `ForARM7`
`0x02110f18` [S: `config/adm-kr/arm9/autoload_2/symbols.txt`;
`src/matched/GX_SetBankForBG.c` and siblings]. `GX_VRAMCNT_SetLCDC_` `0x021119f8` is the routine
that parks a bank in LCDC mode, and its constants give the LCDC alias for each bank:
`0x06800000`, `0x06820000`, `0x06840000`, `0x06860000`, `0x06880000`, `0x06890000`, `0x06894000`,
`0x06898000`, `0x068A0000` [S: `src/matched/GX_VRAMCNT_SetLCDC_.c`].

Bulk uploads are DMA copies to fixed destinations: OAM to `0x07000000` (engine A) and
`0x07000400` (engine B); BG palette to `0x05000000` / `0x05000400`; OBJ palette to `0x05000200`
/ `0x05000600`; OBJ tiles to `0x06400000` / `0x06600000`
[S: `src/matched/GX_LoadOAM.c`, `GXS_LoadOAM.c`, `GX_LoadBGPltt.c`, `GX_LoadOBJPltt.c`,
`GXS_LoadBGPltt.c`, `GXS_LoadOBJPltt.c`, `GX_LoadOBJ.c`, `GXS_LoadOBJ.c`].

### 2D

Display modes are set by `GX_SetGraphicsMode` `0x0211062c` on `DISPCNT` `0x04000000` and
`GXS_SetGraphicsMode` `0x02110610` on `DISPCNT_B` `0x04001000`; the sub-engine has no
`bg0_2d3d` or display-mode field, so its mask is just the three BG-mode bits
[S: `src/matched/GX_SetGraphicsMode.c`, `src/matched/GXS_SetGraphicsMode.c`]. `GX_DispOn` and
`GX_DispOff` toggle `DISPCNT` bits 16-17 [S: `src/matched/GX_DispOn.c`, `GX_DispOff.c`].
Character and screen base pointers for each BG layer come from the `G2_GetBGnCharPtr` /
`G2_GetBGnScrPtr` pairs at `0x02111b00`-`0x02111f68` with their `G2S_` sub-engine twins
[S: `config/adm-kr/arm9/autoload_2/symbols.txt`].

Which engine drives which physical screen is `POWCNT1` bit 15 at `0x04000304`: with `POWCNT1 =
0x020f` engine A drives the **bottom** screen, and with `0x820f` it drives the top
[S: `docs/kb/port/render.md`, screen ownership; the value is logged between PAD samples 6723 and
6726 on the custom START9000 recipe]. `func_020540e4` is the game's writer, computing
`(POWCNT1 & 0xfffffdf1) | 0x20e` [S: `src/matched/func_020540e4.c`].

The 2D layers the game actually uses were measured on the interpreter path. The town's top
screen is engine B in BG mode 1 with BG3 an affine layer, `BG3CNT = 0x6f02` — that layer is the
sky [E: `docs/log/cycle40-keyboard-gate-probe.md` SKY40, `tap-D57`]. Affine backgrounds are
8bpp with byte screen entries, sizes 128 to 1024 square, a wrap bit at 13, PA..PD in 8.8 and a
20.8 reference point at `+0x20` for BG2 and `+0x30` for BG3
[S: `port/render/nds2d.c`, `draw_affine_bg`, written to GBATEK; E: same run].

### What the port's renderer does, and what it costs

Everything above is the hardware the ROM programs. `port/render/` is the software that answers
it: `nds2d.c` composites the two 2D engines, `nds3d.c` decodes the geometry FIFO and `raster3d.c`
rasterises. Two units on 2026-09-09 measured that renderer for the first time -- one for speed
and one for fidelity -- and the rules they were judged by are different and both worth knowing.

**Speed (PERF42, `fbfc987d`): the port had been built at `-O0`.** `port/tools/link.py`'s
`GEN_FLAGS` named no `-O` flag at all, so the whole port was compiled at clang's default. Adding
`-O2 -fwrapv -fno-strict-aliasing` for `port/render/` ALONE took the draw phase from 26.7 ms to
7.25 ms in one link, byte-exact; the interpreter and the shim stay at `-O0` until they have an
exactness harness of their own [E: `docs/kb/hybrid/render-perf.md` section 4a]. The remaining
gain came from taking work out of per-pixel loops with exactness arguments: span attribute
deltas hoisted, 32-bit multiplies where provably safe, attributes interpolated only where
needed, the span parameter by carried long division, the depth test as `z >= D*q`, the VRAMCNT
decode resolved once per configuration behind a validation, the palette converted once per
layer, text BGs a tile at a time, colour effects per line and skipped where inert
[E: same, sections 4b-4d].

The rule this unit was judged by is stricter than the fidelity one: **a performance change may
not move a pixel at all** -- SHA-256 identity, not a correlation. The OFF recipe's 31 frames
cleared 31/31 at **every one of seven intermediate links**, so a rejection would have named its
own change rather than a pile of them, and the town recipe cleared 11/11 unpaced and 11/11 paced
[E: `scratchpad/perf42/exactness-off-*.json`, `exactness-town.json`,
`exactness-town-paced.json`].

| recipe | draw before | draw after | fps unpaced before -> after |
|---|---|---|---|
| OFF (the taxi), frames 4,200..9,000 | 26.45 ms | **7.29 ms** | 30.0 -> **77.1** |
| town, frames 27,000..30,000 | 22.57 ms | **6.17 ms** | 34.8 -> **91.7** |

[E: `docs/kb/hybrid/render-perf.md` section 5; `scratchpad/perf42/runs/`.] The paced live run
holds 59.82 Hz with the window open, and `town-paced`'s 11 frames are SHA-256 identical to the
unpaced run's -- so pacing changes when frames happen and not what any contains [E: same].

**The instrument is `ACWW_FRAMETIME=1`, and it now names a PHASE.** It already printed
`draw / blit / game / other`; it prints, per 2D engine and per 600 frames, `hblank`, `fill`,
`text`, `affine`, `3d`, `obj`, `fx` and `lit`, plus the 3D rasteriser's five sub-phases
(`clear`, `opaque`, `trans`, `count`, `merge`) with polygons, span pixels visited and span pixels
written [E: `docs/kb/hybrid/render-perf.md` section 2]. That report **corrected a published
reading**: LIVE41's "the 2D renderer is the next performance target" was wrong about which
renderer -- the 3D rasteriser was 21.1 of the 26.5 ms [E: same, section 3; the LIVE41 numbers are
in `docs/kb/hybrid/recipes.md` section 7b, kept as that unit's before-column]. It is still 86%
of the draw after the work: 6.29 ms for 317,427 span pixels is about 20 ns per span pixel
[E: same, section 6].

**Fidelity (RENDER42, `b1080164`): two rules corrected, one measured inert.** The pass rule here
is that **the OFF recipe may not lose ncc on ANY of its 31 frames** -- a change that raises the
mean while lowering one frame is rejected [E: `docs/kb/hybrid/render-fidelity.md` section 1].

- **P10 -- the colour special effects run in the 5-bit domain.** GBATEK's blend and brightness
  formulae are five-bit intensities clamped at 31; `chan_mix` and `brighten` had been operating
  on the 8-bit channels `bgr555()` expands to and clamping at 255, a systematically higher
  result by up to 7/255 per channel per blended pixel. They now go back down with `>>3`, do the
  arithmetic, clamp at 31 and expand again [P: GBATEK, *LCD I/O Color Special Effects*;
  E: `../audits/hardware-services.md` P10]. **Measured INERT on every oracle frame these recipes
  reach** -- the effect states they hit are the ones where the two domains agree -- so the
  fixture is the whole of the evidence, and it grew three cases that SEPARATE the domains
  (EVA=9/EVB=7 over red-on-blue is 143 in 8-bit arithmetic and **140** in hardware's):
  `port/tools/test_nds2d_blend.py`, 27 checks, 2 calibrations caught
  [E: `docs/kb/hybrid/render-fidelity.md` section 3].
- **F6 -- texture-coordinate transform modes 2 and 3.** Both are three-term forms on the raw
  10-bit normal (shift 21) and the 20.12 position (shift 24), so the texture matrix's translation
  row never enters; the port ran the full 4x4 with `v[3] = FX_ONE` and a net shift of 20 against
  a normal the NORMAL command has already scaled `<< 3` -- 16x too large, with a spurious
  translation. **Exactly one polygon of 458 at OFF frame 6,000 uses mode 2**: the framed picture
  on the taxi's wall, a 32x32 format-5 material at screen x 164..195. It drew black with coloured
  stripes, which is what a coordinate 16x too large samples out of a 32x32 image; it now draws
  the landscape the oracle draws [E: `scratchpad/render42/picture-frame-before-after.png`;
  `../audits/3d-engine.md` F6]. Whole-frame OFF: mean ncc-top **0.9774 -> 0.9807**, mae
  7.43 -> 7.31, **0 frames worse**; town `tap-24700` 0.9987 -> 0.9991
  [E: `scratchpad/render42/off-final.json`, `tapfinal-24700.json`]. Fixture:
  `port/tools/test_nds3d_texmtx.py`, 5 checks, 2 calibrations, one of which asserts the pre-F6
  answer and must be caught.
- **Rejected with numbers, and kept implemented and off**: `ACWW_SAMPLE_INT=1`, which samples at
  the pixel's integer coordinate as both emulators do rather than at the pixel centre. It moves
  mean mae 7.31 -> 6.66 and ncc-top 0.9807 -> 0.9833, and **loses whole-frame ncc on 9 of 31
  frames**. It is half of a pair -- the emulators also quantise the VERTEX position -- so the
  next experiment is the other half, not a relaxed threshold [E: `off-sampleint` vs `off-final`,
  `docs/kb/hybrid/render-fidelity.md` section 4]. P11 (a semi-transparent OBJ on the brightness
  path) was measured with a population of **zero** on both recipes and deliberately NOT made
  [E: `../audits/hardware-services.md` P11].
**The BACKDROP changes on almost every SCANLINE, and that is the sky's gradient**
[E: RENDER43, `ACWW_REGDUMP=37500` on the two-tap town recipe,
`scratchpad/render43/regdump-town37500.txt`]. At town frame 37,500 engine B's BG palette entry 0
runs `0x7084` at line 0 to `0x79e4` at line 176 in twelve steps — 5-bit green 4 → 15, red fixed
at 4, blue 28 → 30 — while entries 1..31 never change. It is a single halfword written per line
from the ROM's HBlank handler, not a palette DMA. `BLDCNT = 0x2042` names BG1 as the first target
and the BACKDROP as the second, and `BLDALPHA` ramps `0x0010` → `0x1000` over lines 150..167, so
the sky layer is faded into that per-line backdrop toward the horizon. Anything that draws this
screen from an end-of-frame palette gets a flat sky
[S: `port/render/nds2d.c`, `capture_line_regs` and `fill_backdrop`;
`docs/kb/hybrid/render-fixes.md` fix P14].

**The 3D layer is BG0 and is scrolled by BG0HOFS** — a 512-pixel region, 256 of image then 256
transparent [H: host/prose inference from GBATEK, DS 3D Final 2D Output; `port/render/raster3d.c`,
`acww_nds3d_compose_x`; verify against the ROM function or symbol table and this page's recipe]. MEASURED: ACWW writes `BG0HOFS = 0` at OFF frame 6,000 and at town
37,500, so it is inert on every frame either proof set reaches.

**SWAP_BUFFERS is not executed until VBlank and halts the geometry engine until then**
[S: GBATEK, DS 3D Display Control]. A frame therefore carries AT MOST ONE swap; the port used to
honour every one, and the acre-ground dropout was nineteen swaps in a frame discarding eighteen
display lists [H: host/prose inference from `port/render/nds3d.c`, `case 0x50`;
`docs/kb/hybrid/render-fixes.md` fix F15; verify against the ROM function or symbol table and this page's recipe].

## Where it lives

| function or symbol | module | role | grade/citation |
|---|---|---|---|
| `NNS_G3dGeBufferOP_N` `0x01ff8bd0` | `itcm` | buffer or write one GX op | S: `src/matched/NNS_G3dGeBufferOP_N.c` |
| `NNS_G3dGeFlushBuffer` `0x01ff8ccc` | `itcm` | ship the command buffer | S: `src/matched/NNS_G3dGeFlushBuffer.c` |
| `NNS_G3dGeSendDL` `0x01ff8d4c` | `itcm` | submit a packed display list | S: `src/matched/NNS_G3dGeSendDL.c` |
| `NNS_G3dGeWaitSendDL` `0x01ff8e18` | `itcm` | wait for the async GX DMA | S: `src/matched/NNS_G3dGeWaitSendDL.c` |
| `NNS_G3dDraw1Mat1Shp` `0x02107088` | `autoload_2` | draw one shape | S: `src/matched/NNS_G3dDraw1Mat1Shp.c` |
| `NNS_G3dInit` `0x021072e4` | `autoload_2` | bring up G3D | S: `src/matched/NNS_G3dInit.c` |
| `NNS_G3dGlbInit` `0x02105884` / `NNS_G3dGlbFlushP` `0x02105844` | `autoload_2` | global 3D state | S: `src/matched/NNS_G3dGlbInit.c`, `NNS_G3dGlbFlushP.c` |
| `NNS_G3dTexLoad` `0x0210518c` | `autoload_2` | upload an `nsbtx` block | S: `src/matched/NNS_G3dTexLoad.c` |
| `NNS_G3dBindMdlTex` `0x02104f38` / `BindMdlPltt` `0x02104d7c` | `autoload_2` | bind by name | S: `src/matched/NNS_G3dBindMdlTex.c` |
| `NNS_G3dGetResDataByName` `0x021079ac` | `autoload_2` | resource dictionary lookup | S: `src/matched/NNS_G3dGetResDataByName.c` |
| `NNS_GfdAllocFrmTexVram` `0x02102a54` | `autoload_2` | texture VRAM allocation | S: `src/matched/NNS_GfdAllocFrmTexVram.c` |
| `G3X_Init` `0x0211265c` | `autoload_2` | names and clears every 3D register | S: `src/matched/G3X_Init.c` |
| `G3X_GetClipMtx` `0x021123a8` / `G3X_GetVectorMtx` `0x02112360` | `autoload_2` | matrix read-back | S: `src/matched/G3X_GetClipMtx.c` |
| `G3_LoadMtx43` `0x02112134`, `G3_MultMtx43` `0x02112118`, `G3_MultMtx33` `0x021120fc` | `autoload_2` | matrix ops into the FIFO | S: `src/matched/G3_LoadMtx43.c` and siblings |
| `GX_SetGraphicsMode` `0x0211062c` / `GXS_` `0x02110610` | `autoload_2` | `DISPCNT` / `DISPCNT_B` | S: `src/matched/GX_SetGraphicsMode.c` |
| `GX_SetBankFor*` `0x02110dd0`..`0x02111740` | `autoload_2` | `VRAMCNT` assignment | S: `src/matched/GX_SetBankForBG.c` etc. |
| `GX_VRAMCNT_SetLCDC_` `0x021119f8` | `autoload_2` | the LCDC alias table | S: `src/matched/GX_VRAMCNT_SetLCDC_.c` |
| `GX_LoadOAM` `0x02113280` / `GXS_LoadOAM` `0x02113218` | `autoload_2` | OAM DMA | S: `src/matched/GX_LoadOAM.c` |
| `func_020540e4` | `main` | writes `POWCNT1` | S: `src/matched/func_020540e4.c` |
| `NNS_G2dMapScrToCharText` `0x02103734` | `autoload_2` | fills a text-BG screen map with the 32-tile block fold | S: `src/matched/NNS_G2dMapScrToCharText.c` |

## Data it reads and writes

| address | meaning | who writes | who reads |
|---|---|---|---|
| `0x04000000` / `0x04001000` | `DISPCNT` A / B | `GX_SetGraphicsMode`, `GX_DispOn/Off` | the LCD [S: `src/matched/GX_SetGraphicsMode.c`] |
| `0x04000008`+2n | `BGnCNT` | the game's layer setup | the 2D engines [S: `port/render/nds2d.c`] |
| `0x04000050` / `0x52` / `0x54` | `BLDCNT` / `BLDALPHA` / `BLDY` | the game | colour special effects [S: `port/render/nds2d.c`] |
| `0x04000060` | `DISP3DCNT` | `G3X_Init`, `G3X_SetFog` | the 3D engine [S: `src/matched/G3X_Init.c`] |
| `0x04000240`-`0x04000249` | `VRAMCNT` (index 7 = `WRAMCNT`) | `GX_SetBankFor*` | the memory controller [S: `src/matched/GX_VRAMCNT_SetLCDC_.c`] |
| `0x04000280`-`0x040002bf` | hardware divide / sqrt | `FX_Div`, `FX_Sqrt` | the same [E: `docs/log/...` GX40] |
| `0x04000304` | `POWCNT1`; bit 15 swaps which engine is on top | `func_020540e4` | the LCDs [S: `src/matched/func_020540e4.c`; E: `docs/kb/port/render.md`] |
| `0x04000330`/`0x350`/`0x354`/`0x356`/`0x358`/`0x35c`/`0x360`/`0x380` | edge, clear colour, clear depth, clear-image offset, fog colour, fog offset, fog table, toon table | `G3X_*` setters | the 3D engine [S: `src/matched/G3X_Init.c`] |
| `0x04000400`-`0x0400043f` | the packed geometry FIFO (all 64 bytes are the same port) | `NNS_G3dGeBufferOP_N`, `GX_SendFifo48B` | the geometry engine [S: `src/matched/NNS_G3dGeBufferOP_N.c`; `port/render/gxfifo.c`] |
| `0x04000440`-`0x040005c8` | the 45 individual command ports, `0x04000440 + (op-0x10)*4` | `G3_*`, `G3X_*` | the same [S: `src/matched/G3_LoadMtx43.c`; `port/render/gxfifo.c`] |
| `0x04000600` | `GXSTAT`: busy `0x08000000`, stack error `0x8000`, stack levels `0x1f00`/`0x2000`, FIFO IRQ `0xc0000000` | `G3X_Init`, `G3X_ResetMtxStack` | `G3X_GetClipMtx`, the wait loops [S: `src/matched/G3X_Init.c`] |
| `0x04000640` / `0x04000680` | `CLIPMTX_RESULT` (16 fx32) / `VECMTX_RESULT` (9 fx32) | the geometry engine | `G3X_GetClipMtx` / `GetVectorMtx` [S: `src/matched/G3X_GetClipMtx.c`] |
| `0x05000000`/`0x200`/`0x400`/`0x600` | BG-A, OBJ-A, BG-B, OBJ-B palettes | `GX_LoadBGPltt` family | the 2D engines [S: `src/matched/GX_LoadBGPltt.c`] |
| `0x06400000` / `0x06600000` | OBJ tile space A / B | `GX_LoadOBJ`, `GXS_LoadOBJ` | the 2D engines [S: `src/matched/GX_LoadOBJ.c`] |
| `0x06800000`+ | the LCDC bank aliases | `GX_VRAMCNT_SetLCDC_`, `GX_LoadTex` | the texture unit [S: `src/matched/GX_VRAMCNT_SetLCDC_.c`] |
| `0x07000000` / `0x07000400` | OAM A / B, 128 entries each | `GX_LoadOAM`, `GXS_LoadOAM` | the 2D engines [S: `src/matched/GX_LoadOAM.c`] |

## How to check it

The port implements the hardware side of all of this, so the fastest check of a claim is to run
the ROM's own code against it. The recipe that reaches the town and its sky:

```
ACWW_INTERP=1
ACWW_KEYS_AT / _FOR / _EVERY   # the custom START9000 keys -- the short forms are not read (B1)
ACWW_TOUCH_ENABLE=1 ACWW_TOUCH_X=221 ACWW_TOUCH_Y=181 ACWW_TOUCH_AT=6900 ACWW_TOUCH_EVERY=60
ACWW_STOP_FRAME=48000
python port/tools/run.py --frontier start
```

Expected: at frame 4,500 the taxi interior — Kapp'n, the rain, the window — over the name
keyboard, at roughly 291 polygons and 99,000 composed pixels a frame
[E: `docs/log/cycle40-keyboard-gate-probe.md` GX40, run `off-D51`;
O: `scratchpad/oracle/off`, the same scene in DeSmuME]. At frame 37,800 clouds over the blue sky
above the town hall [E: same log, SKY40, run `tap-D57`]. At frame 37,500 the town with overlays
5, 36, 54, 120 and 117 loaded, 48,000 frames in 811 s
[E: `scratchpad/cycle40/runs/tap-D56`, per the same log, TOWN40].

Two instruments are specific to this page. `ACWW_TEXTRACE_FRAME` with a decimal
`ACWW_TEXTRACE_INDEX` dumps one polygon's texture provenance, bounded by the 2,048-polygon list
[H: host/prose inference from `docs/kb/port/render.md`, texture provenance; verify against the ROM function or symbol table and this page's recipe]. `ACWW_OAMDUMP=<frame>` dumps both OAM tables
and is not gated on `ACWW_TRACE_STATE` [H: host/prose inference from `docs/kb/port/render.md`, OAM cursor table; verify against the ROM function or symbol table and this page's recipe].
`ACWW_NOBLEND=1` disables the colour special effects so a blend can be isolated
[H: host/prose inference from `port/render/nds2d.c`; verify against the ROM function or symbol table and this page's recipe].

## Hypotheses

- **The 3D layer sits about a pixel up and left of the oracle's, and it is a fill rule rather
  than the texture algebra.** A per-quadrant sub-pixel fit on the taxi's top screen gives the
  SAME translation in all four quadrants -- dx +1.00, dy +1.00..+2.00 -- which is a translation,
  not a scale, and it moves mae 15.08 -> 7.03 at OFF frame 6,000; the bottom screen, which is 2D,
  fits at (0, 0), so the offset belongs to the 3D layer alone. The diff image is a thin outline
  on every textured edge, which is what a sub-pixel displacement looks like and not what a wrong
  colour looks like [E: `scratchpad/render42/shiftfit.py`,
  `scratchpad/render42/off006000-top-A-B-D.png`]. Settled by measuring the OTHER half of the
  emulators' pair -- quantising the vertex position to a whole pixel -- under the same 31-frame
  rule, not by translating the layer (`ACWW_3DBIAS_X/_Y` does that and loses ncc on 2-3 frames).
- **The town's sky has no vertical gradient, and the whole-frame renderer may be unable to see
  why.** At frame 37,500 the oracle's sky ramps in GREEN from 5-bit 4 at the top of the screen to
  9 near the horizon with blue 28 -> 29 and red fixed at 4; the port's sky is a flat (4, 4, 28)
  everywhere -- the oracle's TOP row held for the whole screen. Red being identical rules out a
  brightness effect, which moves all three channels; the shape is an alpha blend against roughly
  (4, 31, 31), or a per-line palette [O: `scratchpad/render42/d63-37500.png`]. `capture_line_regs`
  already runs the ROM's HBlank handler once per line for the affine and effect registers and
  does NOT capture the palette. Settled by an INSTRUMENT first, not a code change: record BG
  palette entry 0 and BLDCNT/BLDALPHA per line at a chosen frame. (Compare the sky by structure,
  not by pixel position: the cloud positions differ because the port is one dialogue step ahead.)
- **The acre ground drops out intermittently, and the 3D pipeline is running while it does.**
  17 of 1,160 lower screens over six GAMEPLAY42 runs are 45-99% the single colour `0x2184FF` --
  the 3D layer's clear blue -- sometimes with the buildings and the player still drawn correctly
  over the gap, and one more is 99% flat dark green; the door-transition blacks are separate and
  expected. A stop dump during a 320-frame instance is a HOLD profile with
  `G3dDrawInternal_Loop_`, `NNS_G3dGeBufferOP_N`, `NNSi_G3dFuncSbc_MAT` and `NNSi_G3dFuncSbc_SHP`
  at the top -- **the pipeline is being fed while nothing lands on screen** -- with no
  `unimplemented`, no fault, and normal play afterwards
  [E: `docs/log/cycle41-gameplay.md` GP42-6; `scratchpad/gameplay42/ground-gap.png`]. It fails at
  the acre TERRAIN first and sometimes takes the whole scene. Settled by an oracle arm over one
  reproducing frame range, plus a GX submission count for the acre's own polygons across the gap.
- **The clear-image (rear-plane bitmap) path is never used by this game.** `DISP3DCNT` bit 14 is
  noted but not implemented in the port, yet `func_ov001_0222e4dc` does call
  `GX_SetBankForClearImage` [S: `port/render/raster3d.c`; `src/matched/GX_SetBankForClearImage.c`].
  Settle it by logging `DISP3DCNT` bit 14 across a long town run and a WFC-screen run.
- **Extended-rotscale and large-bitmap backgrounds (BG modes 3-6) are unused.** The port skips
  them and no scene has needed one so far [S: `port/render/nds2d.c`, K_EXT / K_LARGE notes].
  Settle it by asserting on `BGnCNT` values that select them across the interpreter recipes.
- **Windowing (`WIN0`/`WIN1`/`OBJWIN`), mosaic and extended palettes are unused.** Same standing:
  noted, not implemented, no scene has needed one [S: `port/render/nds2d.c`]. Settle it by
  asserting on `DISPCNT & 0xE000` and `DISPCNT & 0xC0000000`.
- **`BOX_TEST`, `POS_TEST` and `VEC_TEST` (GX commands 0x70-0x72) matter to the game's culling.**
  The port stubs all three, clearing the GXSTAT test-busy bit and reporting "visible"
  [S: `port/render/nds3d.c`]. If the game culls with `BOX_TEST`, always answering "visible"
  costs polygons but changes nothing visible; if it culls with `POS_TEST` results, it could be
  wrong. Settle it by counting 0x70/0x71/0x72 submissions per frame on the town recipe.
- **The port's `POWCNT1` reading is engine-A-on-bottom at `0x020f`.** That is an experimental
  reading of a port run [E: `docs/kb/port/render.md`], and the oracle has not been used to
  confirm the same swap on hardware timing. Settle it by comparing the two screens' contents
  between `scratchpad/oracle/*` and a port run at the same frame.
- **`NNS_G3dGeSendDL`'s 256-byte threshold means most shapes go through the buffer, not DMA.**
  The threshold is in the source [S: `src/matched/NNS_G3dGeSendDL.c`]; the actual distribution is
  not measured. Settle it by histogramming `shp->sizeDL` at `NNS_G3dDraw1Mat1Shp`.

## Related

- `../data/archives.md` — the `nsb*` resource containers.
- `../audits/hardware-services.md` P10-P13 — the 2D claims table and the fixes' status rows.
- `../audits/3d-engine.md` — the 3D claims table and F1-F13.
- `../audits/night-2026-09-09.md` — where RENDER42 and PERF42 sit in the night's index.
- `docs/kb/hybrid/render-perf.md`, `docs/kb/hybrid/render-fidelity.md` — the implementation
  pages: every number above, the phase table, and the two pass rules in full.
- `../data/rom-layout.md` — where the model, texture and menu assets live.
- `text-and-messages.md` — glyphs, which are drawn through the same 2D engines.
- `display-objects.md`, `memory-map.md` — the framework and the arenas around this pipeline.
