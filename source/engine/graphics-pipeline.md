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
`nsbtp`, `nsbta`, `nsbva` and `nsbma` [H: source account: `extract/adm-kr/files/`, magic census — see
`../data/archives.md`; direct ROM-source provenance unresolved]. `NNS_G3dGetResDataByName` at `0x021079ac` is the dictionary lookup that
finds a named block inside a resource [S: `src/matched/NNS_G3dGetResDataByName.c`; source account: `src/matched/NNS_G3dGetResDataByName.c`], and
`NNS_G3dBindMdlTex` at `0x02104f38` walks a model's texture-to-material dictionary binding each
named texture, returning FALSE if any name is missing from the `nsbtx`
[S: `src/matched/NNS_G3dBindMdlTex.c`; source account: `src/matched/NNS_G3dBindMdlTex.c`]. The palette twin is `NNS_G3dBindMdlPltt` `0x02104d7c`
[S: `src/matched/NNS_G3dGetResDataByName.c`, `src/matched/NNS_G3dBindMdlTex.c`, `src/matched/NNS_G3dBindMdlPltt.c`; source account: `config/adm-kr/arm9/autoload_2/symbols.txt`]. Texture bytes go to VRAM through
`NNS_G3dTexLoad` `0x0210518c`, which brackets `GX_BeginLoadTex` / `GX_LoadTex` /
`GX_EndLoadTex` and handles the 4x4-compressed pair as two writes
[S: `src/matched/NNS_G3dTexLoad.c`; source account: `src/matched/NNS_G3dTexLoad.c`]. Space for those textures is handed out by the graphics
foundation allocator `NNS_GfdAllocFrmTexVram` `0x02102a54`, which returns a packed texture key
[S: `src/matched/NNS_GfdAllocFrmTexVram.c`; source account: `src/matched/NNS_GfdAllocFrmTexVram.c`].

Animation sets are fetched one kind at a time: `NNS_G3dGetJntAnmSet` `0x02107b28`,
`NNS_G3dGetMatCAnmSet` `0x02107b64`, `NNS_G3dGetTexSRTAnmSet` `0x02107ba0`,
`NNS_G3dGetTexPatAnmSet` `0x02107bdc`, `NNS_G3dGetVisAnmSet` `0x02107cd4`
[S: `src/matched/NNS_G3dGetJntAnmSet.c`, `src/matched/NNS_G3dGetMatCAnmSet.c`, `src/matched/NNS_G3dGetTexSRTAnmSet.c`, `src/matched/NNS_G3dGetTexPatAnmSet.c`, `src/matched/NNS_G3dGetVisAnmSet.c`; source account: `config/adm-kr/arm9/autoload_2/symbols.txt`].

### Geometry out

Drawing one shape is `NNS_G3dDraw1Mat1Shp` `0x02107088`: it applies the material and
texture-matrix animation results, submits the shape's pre-packed display list with
`NNS_G3dGeSendDL((u8*)shp + shp->ofsDL, shp->sizeDL)`, and re-applies the inverse position scale
[S: `src/matched/NNS_G3dDraw1Mat1Shp.c`; source account: `src/matched/NNS_G3dDraw1Mat1Shp.c`]. The submission path is the four ITCM routines:
`NNS_G3dGeSendDL` `0x01ff8d4c` sends lists under 256 bytes through the buffer and larger ones by
DMA; `NNS_G3dGeBufferOP_N` `0x01ff8bd0` either buffers an op word plus N arguments into the
0xc0-word command buffer or writes the op straight to the FIFO at `0x04000400` and streams the
arguments with `MI_CpuSend32`; `NNS_G3dGeFlushBuffer` `0x01ff8ccc` waits on any in-flight DMA and
ships the whole buffer; `NNS_G3dGeWaitSendDL` `0x01ff8e18` spins until the async DMA completes
[S: `src/matched/NNS_G3dGeSendDL.c`, `src/matched/NNS_G3dGeBufferOP_N.c`, `src/matched/NNS_G3dGeFlushBuffer.c`, `src/matched/NNS_G3dGeWaitSendDL.c`; source account: `src/matched/NNS_G3dGeSendDL.c`, `NNS_G3dGeBufferOP_N.c`, `NNS_G3dGeFlushBuffer.c`,
`NNS_G3dGeWaitSendDL.c`; `config/adm-kr/arm9/itcm/symbols.txt`]. Those four are the G3D
submission members of ITCM, not the whole of it: `itcm` holds 158 function symbols, 114 of them
named, including the thirteen `NNSi_G3dFuncSbc_*` scene-graph opcodes, the whole `MTX_*`/`VEC_*`
/`FX_*` fixed-point library, `OS_IrqHandler`, `OS_Halt`, `OS_SaveContext`/`OS_LoadContext`,
`OS_GetTick` and the display-object steppers [S: `src/matched/NNS_G3dDraw1Mat1Shp.c`, `src/matched/NNS_G3dGeSendDL.c`, `src/matched/NNS_G3dGeBufferOP_N.c`, `src/matched/NNS_G3dGeFlushBuffer.c`, `src/matched/NNS_G3dGeWaitSendDL.c`, `src/matched/OS_IrqHandler.c`, `src/matched/OS_Halt.c`, `src/matched/OS_SaveContext.c`, `src/matched/OS_LoadContext.c`, `src/matched/OS_GetTick.c`; source account: `config/adm-kr/arm9/itcm/symbols.txt`, counted
over `kind:function` lines; see `memory-map.md` and `display-objects.md`].

Global 3D state — lights, material defaults, scale factors — lives in one block that
`NNS_G3dGlbInit` `0x02105884` seeds and `NNS_G3dGlbFlushP` `0x02105844` ships to the engine as
0x3e words, clearing two dirty bits at +0xFC
[S: `src/matched/NNS_G3dGlbInit.c`, `src/matched/NNS_G3dGlbFlushP.c`; source account: `src/matched/NNS_G3dGlbInit.c`, `src/matched/NNS_G3dGlbFlushP.c`]. A light direction is
packed into one `LIGHT_VECTOR` word as three 10-bit fields plus the light id in bits 30-31
[S: `src/matched/NNS_G3dGlbLightVector.c`; source account: `src/matched/NNS_G3dGlbLightVector.c`]. `NNS_G3dInit` `0x021072e4` calls `G3X_Init`, then
`NNS_G3dGlbInit`, then sets the GXSTAT FIFO-IRQ field at `0x04000600`
[S: `src/matched/NNS_G3dInit.c`; source account: `src/matched/NNS_G3dInit.c`].

Below NNS sits the SDK's own geometry layer. `G3X_Init` `0x0211265c` names the whole register
set the pipeline uses: `DISP3DCNT` `0x04000060`, `EDGE_COLOR` `0x04000330`, `CLEAR_COLOR`
`0x04000350`, `CLEAR_DEPTH` `0x04000354`, `CLRIMAGE_OFFSET` `0x04000356`, `FOG_COLOR`
`0x04000358`, `FOG_OFFSET` `0x0400035c`, `FOG_TABLE` `0x04000360`, `TOON_TABLE` `0x04000380`,
`POLYGON_ATTR` `0x040004a4`, `TEXIMAGE_PARAM` `0x040004a8`, `TEXPLTT_BASE` `0x040004ac`,
`END_VTXS` `0x04000504` and `GXSTAT` `0x04000600` [S: `src/matched/G3X_Init.c`; source account: `src/matched/G3X_Init.c`]. Matrix results
are read back out of `CLIPMTX_RESULT` `0x04000640` and `VECMTX_RESULT` `0x04000680` after
waiting on the GXSTAT busy bit `0x08000000` [S: `src/matched/G3X_GetClipMtx.c`, `src/matched/G3X_GetVectorMtx.c`; source account: `src/matched/G3X_GetClipMtx.c`,
`src/matched/G3X_GetVectorMtx.c`]. The matrix stack levels are GXSTAT bits `0x1f00` (position)
and `0x2000` (projection), with the error bit at `0x4000`
[S: `src/matched/G3X_GetMtxStackLevelPV.c`, `src/matched/G3X_GetMtxStackLevelPJ.c`; source account: `src/matched/G3X_GetMtxStackLevelPV.c`, `G3X_GetMtxStackLevelPJ.c`].
`NNS_G3dGetCurrentMtx` `0x021073a8` uses that read-back path: it flushes, pushes an identity
projection through ports `0x04000440`/`0x04000444`/`0x04000454`/`0x04000448`, and polls the
result registers [S: `src/matched/NNS_G3dGetCurrentMtx.c`; source account: `src/matched/NNS_G3dGetCurrentMtx.c`].

### VRAM

The nine VRAM banks are assigned by the `GX_SetBankFor*` family in `autoload_2`, all writing the
`VRAMCNT` bytes at `0x04000240`-`0x04000249` (index 7 is `WRAMCNT` and is skipped):
`GX_SetBankForBG` `0x02111740`, `ForOBJ` `0x021115d4`, `ForSubBG` `0x02110e4c`, `ForSubOBJ`
`0x02110dd0`, `ForTex` `0x02111204`, `ForTexPltt` `0x02111110`, `ForBGExtPltt` `0x021114c0`,
`ForOBJExtPltt` `0x02111408`, `ForClearImage` `0x02110fd0`, `ForLCDC` `0x02110ef8`, `ForARM7`
`0x02110f18` [S: `src/matched/GX_SetBankForBG.c`; source account: `config/adm-kr/arm9/autoload_2/symbols.txt`;
`src/matched/GX_SetBankForBG.c` and siblings]. `GX_VRAMCNT_SetLCDC_` `0x021119f8` is the routine
that parks a bank in LCDC mode, and its constants give the LCDC alias for each bank:
`0x06800000`, `0x06820000`, `0x06840000`, `0x06860000`, `0x06880000`, `0x06890000`, `0x06894000`,
`0x06898000`, `0x068A0000` [S: `src/matched/GX_VRAMCNT_SetLCDC_.c`; source account: `src/matched/GX_VRAMCNT_SetLCDC_.c`].

Bulk uploads are DMA copies to fixed destinations: OAM to `0x07000000` (engine A) and
`0x07000400` (engine B); BG palette to `0x05000000` / `0x05000400`; OBJ palette to `0x05000200`
/ `0x05000600`; OBJ tiles to `0x06400000` / `0x06600000`
[S: `src/matched/GX_LoadOAM.c`, `src/matched/GXS_LoadOAM.c`, `src/matched/GX_LoadBGPltt.c`, `src/matched/GX_LoadOBJPltt.c`, `src/matched/GXS_LoadBGPltt.c`, `src/matched/GXS_LoadOBJPltt.c`, `src/matched/GX_LoadOBJ.c`, `src/matched/GXS_LoadOBJ.c`; source account: `src/matched/GX_LoadOAM.c`, `GXS_LoadOAM.c`, `GX_LoadBGPltt.c`, `GX_LoadOBJPltt.c`,
`GXS_LoadBGPltt.c`, `GXS_LoadOBJPltt.c`, `GX_LoadOBJ.c`, `GXS_LoadOBJ.c`].

### 2D

Display modes are set by `GX_SetGraphicsMode` `0x0211062c` on `DISPCNT` `0x04000000` and
`GXS_SetGraphicsMode` `0x02110610` on `DISPCNT_B` `0x04001000`; the sub-engine has no
`bg0_2d3d` or display-mode field, so its mask is just the three BG-mode bits
[S: `src/matched/GX_SetGraphicsMode.c`, `src/matched/GXS_SetGraphicsMode.c`; source account: `src/matched/GX_SetGraphicsMode.c`, `src/matched/GXS_SetGraphicsMode.c`]. `GX_DispOn` and
`GX_DispOff` toggle `DISPCNT` bits 16-17 [S: `src/matched/GX_DispOn.c`, `src/matched/GX_DispOff.c`; source account: `src/matched/GX_DispOn.c`, `GX_DispOff.c`].
Character and screen base pointers for each BG layer come from the `G2_GetBGnCharPtr` /
`G2_GetBGnScrPtr` pairs at `0x02111b00`-`0x02111f68` with their `G2S_` sub-engine twins
[S: `src/matched/GX_SetGraphicsMode.c`, `src/matched/GXS_SetGraphicsMode.c`, `src/matched/GX_DispOn.c`, `src/matched/GX_DispOff.c`; source account: `config/adm-kr/arm9/autoload_2/symbols.txt`].

Which engine drives which physical screen is `POWCNT1` bit 15 at `0x04000304`: with `POWCNT1 =
0x020f` engine A drives the **bottom** screen, and with `0x820f` it drives the top
[H: source account: `docs/kb/port/render.md`, screen ownership; the value is logged between PAD samples 6723 and
6726 on the custom START9000 recipe; direct ROM-source provenance unresolved]. `func_020540e4` is the game's writer, computing
`(POWCNT1 & 0xfffffdf1) | 0x20e` [S: `src/matched/func_020540e4.c`; source account: `src/matched/func_020540e4.c`].

The 2D layers the game actually uses were measured on the interpreter path. The town's top
screen is engine B in BG mode 1 with BG3 an affine layer, `BG3CNT = 0x6f02` — that layer is the
sky [E: `docs/log/cycle40-keyboard-gate-probe.md` SKY40, `tap-D57` ; `scratchpad/cycle40/runs/tap-D57`]. Affine backgrounds are
8bpp with byte screen entries, sizes 128 to 1024 square, a wrap bit at 13, PA..PD in 8.8 and a
20.8 reference point at `+0x20` for BG2 and `+0x30` for BG3
[H: source account: `port/render/nds2d.c`, `draw_affine_bg`, written to GBATEK; H: historical measurement account: same run; direct ROM-source provenance unresolved].

### The scene transition is a WINDOW, not a fade

MEASURED (FADE52). Leaving a building or walking through a door, the game enables BG2 and
window 0 in the same `DISPCNT` write and sets `WININ = 0x3f3b` / `WINOUT = 0x0024` on both
engines: **inside window 0 every layer draws except BG2; outside it, only BG2 draws.** BG2 is a
black cover and window 0 is the hole the picture is seen through. The transition closes the
hole. `BLDY` and `MASTER_BRIGHT` stay at `0000` on both engines throughout, and the original's
own per-column luma keeps its lit values in the middle while the columns outside go to exactly
zero [E: `docs/log/cycle41-gameplay.md` FADE52; `docs/kb/hybrid/render-fixes.md` P15 ; `scratchpad/fade52/RECEIPTS.md`].

**The hole is an IRIS, and `WIN0H` takes 192 values a frame, not one** (WINDOW53; FADE52's
"thirteen steps of about ten columns, one step per main-loop body" measured the animation
through the iris's widest line and is corrected here). Two callbacks registered together by
`func_02041f6c` through `func_0205c024(&data_021c75cc, func_02042154, func_02042120, 0)` own
the register for the whole transition:

* **`func_02042120`, the VBlank half**: `WIN0H` on both engines takes `*(u16 *)(*(u32 *)
  0x021c75b4)` -- the FIRST entry of a table -- and `WIN0V` takes `0x00c0`;
* **`func_02042154`, the HBlank half**: `WIN0H` on both engines takes `table[VCOUNT]`, mirrored
  about line 96 (`if (y >= 0x60) y = 0xbf - y`), and **only when DISPSTAT bit 1, the HBlank
  flag, is set**.

The table is 96 halfwords, double-buffered at `0x021c75e8` and `0x021c76a8` with the live one
named by the pointer at `0x021c75b4` and the buffer chosen by bit 1 of `0x021c75ac`.
On the DS the live table holds up to **57 distinct values at once**, and its widest line is
what a screenshot's lit-column span measures: at frame 49,611 of the town-hall exit it is
`0x0cf4` (X1 = 12, X2 = 244, lit 12..243) and at 49,640 it is `0x7789` (lit 119..136), which are
FADE52's per-column rows to the column [E: `docs/log/cycle41-gameplay.md` WINDOW53 W53-5; current receipt locator: `scratchpad/window53/RECEIPTS.md`].
`func_02041e48` rebuilds it from the animation position at `0x021c75bc`: `0` fills `0x00ff`
(wide open), `0x1000` fills `0x8080` (shut), and in between it is an ellipse of vertical radius
`(0x1000 - pos) * 0xa0 >> 12`, each line inside taking `t = 0x80 - (FX_Sqrt(...) >> 12)` written
as `(t << 8) | (0x100 - t)` -- symmetric about x = 128 by construction. `func_02041d14` starts
a close (`pos = 0`, step `= FX_Div(0x1000, frames << 12)` at `0x021c75c0`) and `func_02041c88`
an open; the state byte at `0x021c75b8` is 0 idle / 1 opening / 2 done / 3 closing.

**The port reproduces this** (IRIS54). Two host defects kept it from doing so and both are
fixed: `port/interp/interp_boot.c` never raised DISPSTAT bit 1, so the HBlank half returned
without writing and one `WIN0H` covered all 192 lines; and `port/shim/math/divider.c`'s
`FX_SQRT_SHIFT` was 1 where the SDK's is 10, so every `FX_Sqrt` came back 512 times too big and
`func_02041e48` took its "this line spans the screen" branch on every interior line. MEASURED
after: at seven frames of the town-hall exit the port's per-scanline `WIN0H` carries 43, 48,
57, 50, 25, 25 and 13 distinct values over 192 lines, both engines, and its run list is exact
against the DS's live table at all seven; the DS's fourteen per-column lit spans all appear, in
order [E: `docs/log/cycle41-gameplay.md` IRIS54 I54-5, I54-6; `docs/kb/hybrid/render-fixes.md`
P17, P18; current receipt locator: `scratchpad/iris54/RECEIPTS.md`].

The game's deferred display-register flush `func_02001ecc` at `0x02001ecc`
(`src/matched/func_02001ecc.c`) takes `0x04000040`..`0x0400004b` and the blend pair from a RAM
shadow at `0x0213fe74` / `0x0213fe94` under the dirty flags at `0x0213fe85` / `0x0213fe86`, and
`func_02001cc4` is its only WIN0-A setter (`X1` at `0x0213fe92`, `X2` at `0x0213fe94`, dirty bit
`0x0010`) -- but it writes `WIN0H` exactly ONCE per transition, `0x00ff` at the start, on both
producers; the shadow does not move again while the iris runs. The fade-to-black *helper*
`func_02001aac` -- `G2x_SetBlendBrightness_` on both engines with plane `0x3f` -- is a separate
path used at the ends of the transition (`BLDCNT = 0x00ff`, `BLDY = 0x10`), not for the ramp.

### What the port's renderer does, and what it costs

Everything above is the hardware the ROM programs. `port/render/` is the software that answers
it: `nds2d.c` composites the two 2D engines, `nds3d.c` decodes the geometry FIFO and `raster3d.c`
rasterises. Two units on 2026-09-09 measured that renderer for the first time -- one for speed
and one for fidelity -- and the rules they were judged by are different and both worth knowing.

**Speed (PERF42, `fbfc987d`): the port had been built at `-O0`.** `port/tools/link.py`'s
`GEN_FLAGS` named no `-O` flag at all, so the whole port was compiled at clang's default. Adding
`-O2 -fwrapv -fno-strict-aliasing` for `port/render/` ALONE took the draw phase from 26.7 ms to
7.25 ms in one link, byte-exact; the interpreter and the shim stay at `-O0` until they have an
exactness harness of their own [H: log/source account: `docs/kb/hybrid/render-perf.md` section 4a; receipt provenance unresolved]. The remaining
gain came from taking work out of per-pixel loops with exactness arguments: span attribute
deltas hoisted, 32-bit multiplies where provably safe, attributes interpolated only where
needed, the span parameter by carried long division, the depth test as `z >= D*q`, the VRAMCNT
decode resolved once per configuration behind a validation, the palette converted once per
layer, text BGs a tile at a time, colour effects per line and skipped where inert
[H: log/source account: `docs/kb/hybrid/render-perf.md` section 4a, sections 4b-4d; receipt provenance unresolved].

The rule this unit was judged by is stricter than the fidelity one: **a performance change may
not move a pixel at all** -- SHA-256 identity, not a correlation. The OFF recipe's 31 frames
cleared 31/31 at **every one of seven intermediate links**, so a rejection would have named its
own change rather than a pile of them, and the town recipe cleared 11/11 unpaced and 11/11 paced
[H: log/source account: `scratchpad/perf42/exactness-off-*.json`, `exactness-town.json`,
`exactness-town-paced.json`; receipt provenance unresolved].

| recipe | draw before | draw after | fps unpaced before -> after |
|---|---|---|---|
| OFF (the taxi), frames 4,200..9,000 | 26.45 ms | **7.29 ms** | 30.0 -> **77.1** |
| town, frames 27,000..30,000 | 22.57 ms | **6.17 ms** | 34.8 -> **91.7** |

[E: `docs/kb/hybrid/render-perf.md` section 5; `scratchpad/perf42/runs/`.] The paced live run
holds 59.82 Hz with the window open, and `town-paced`'s 11 frames are SHA-256 identical to the
unpaced run's -- so pacing changes when frames happen and not what any contains [E: `docs/kb/hybrid/render-perf.md` section 5; `scratchpad/perf42/runs/`.].

**The instrument is `ACWW_FRAMETIME=1`, and it now names a PHASE.** It already printed
`draw / blit / game / other`; it prints, per 2D engine and per 600 frames, `hblank`, `fill`,
`text`, `affine`, `3d`, `obj`, `fx` and `lit`, plus the 3D rasteriser's five sub-phases
(`clear`, `opaque`, `trans`, `count`, `merge`) with polygons, span pixels visited and span pixels
written [H: log/source account: `docs/kb/hybrid/render-perf.md` section 2; receipt provenance unresolved]. That report **corrected a published
reading**: LIVE41's "the 2D renderer is the next performance target" was wrong about which
renderer -- the 3D rasteriser was 21.1 of the 26.5 ms [H: log/source account: `docs/kb/hybrid/render-perf.md` section 2, section 3; the LIVE41 numbers are
in `docs/kb/hybrid/recipes.md` section 7b, kept as that unit's before-column; receipt provenance unresolved]. It is still 86%
of the draw after the work: 6.29 ms for 317,427 span pixels is about 20 ns per span pixel
[H: log/source account: `docs/kb/hybrid/render-perf.md` section 2, section 6; receipt provenance unresolved].

**Fidelity (RENDER42, `b1080164`): two rules corrected, one measured inert.** The pass rule here
is that **the OFF recipe may not lose ncc on ANY of its 31 frames** -- a change that raises the
mean while lowering one frame is rejected [H: log/source account: `docs/kb/hybrid/render-fidelity.md` section 1; receipt provenance unresolved].

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
  [H: log/source account: `docs/kb/hybrid/render-fidelity.md` section 3; receipt provenance unresolved].
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
  next experiment is the other half, not a relaxed threshold [H: log/source account: `off-sampleint` vs `off-final`,
  `docs/kb/hybrid/render-fidelity.md` section 4; receipt provenance unresolved]. P11 (a semi-transparent OBJ on the brightness
  path) was measured with a population of **zero** on both recipes and deliberately NOT made
  [H: log/source account: `../audits/hardware-services.md` P11; receipt provenance unresolved].
**The BACKDROP changes on almost every SCANLINE, and that is the sky's gradient**
[E: RENDER43, `ACWW_REGDUMP=37500` on the two-tap town recipe,
`scratchpad/render43/regdump-town37500.txt`]. At town frame 37,500 engine B's BG palette entry 0
runs `0x7084` at line 0 to `0x79e4` at line 176 in twelve steps — 5-bit green 4 → 15, red fixed
at 4, blue 28 → 30 — while entries 1..31 never change. It is a single halfword written per line
from the ROM's HBlank handler, not a palette DMA. `BLDCNT = 0x2042` names BG1 as the first target
and the BACKDROP as the second, and `BLDALPHA` ramps `0x0010` → `0x1000` over lines 150..167, so
the sky layer is faded into that per-line backdrop toward the horizon. Anything that draws this
screen from an end-of-frame palette gets a flat sky
[H: source account: `port/render/nds2d.c`, `capture_line_regs` and `fill_backdrop`;
`docs/kb/hybrid/render-fixes.md` fix P14; direct ROM-source provenance unresolved].

**The 3D layer is BG0 and is scrolled by BG0HOFS** — a 512-pixel region, 256 of image then 256
transparent [H: host/prose inference from GBATEK, DS 3D Final 2D Output; `port/render/raster3d.c`,
`acww_nds3d_compose_x`; verify against the ROM function or symbol table and this page's recipe]. MEASURED: ACWW writes `BG0HOFS = 0` at OFF frame 6,000 and at town
37,500, so it is inert on every frame either proof set reaches.

**SWAP_BUFFERS is not executed until VBlank and halts the geometry engine until then**
[H: source account: GBATEK, DS 3D Display Control; direct ROM-source provenance unresolved]. A frame therefore carries AT MOST ONE swap; the port used to
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
| `0x04000000` / `0x04001000` | `DISPCNT` A / B | `GX_SetGraphicsMode`, `GX_DispOn/Off` | the LCD [S: `src/matched/GX_SetGraphicsMode.c`; source account: `src/matched/GX_SetGraphicsMode.c`] |
| `0x04000008`+2n | `BGnCNT` | the game's layer setup | the 2D engines [H: source account: `port/render/nds2d.c`; direct ROM-source provenance unresolved] |
| `0x04000050` / `0x52` / `0x54` | `BLDCNT` / `BLDALPHA` / `BLDY` | the game | colour special effects [H: source account: `port/render/nds2d.c`; direct ROM-source provenance unresolved] |
| `0x04000060` | `DISP3DCNT` | `G3X_Init`, `G3X_SetFog` | the 3D engine [S: `src/matched/G3X_Init.c`; source account: `src/matched/G3X_Init.c`] |
| `0x04000240`-`0x04000249` | `VRAMCNT` (index 7 = `WRAMCNT`) | `GX_SetBankFor*` | the memory controller [S: `src/matched/GX_VRAMCNT_SetLCDC_.c`; source account: `src/matched/GX_VRAMCNT_SetLCDC_.c`] |
| `0x04000280`-`0x040002bf` | hardware divide / sqrt | `FX_Div`, `FX_Sqrt` | the same [H: log/source account: `docs/log/...` GX40; receipt provenance unresolved] |
| `0x04000304` | `POWCNT1`; bit 15 swaps which engine is on top | `func_020540e4` | the LCDs [S: `src/matched/func_020540e4.c`; source account: `src/matched/func_020540e4.c`; H: `docs/kb/port/render.md`] |
| `0x04000330`/`0x350`/`0x354`/`0x356`/`0x358`/`0x35c`/`0x360`/`0x380` | edge, clear colour, clear depth, clear-image offset, fog colour, fog offset, fog table, toon table | `G3X_*` setters | the 3D engine [S: `src/matched/G3X_Init.c`; source account: `src/matched/G3X_Init.c`] |
| `0x04000400`-`0x0400043f` | the packed geometry FIFO (all 64 bytes are the same port) | `NNS_G3dGeBufferOP_N`, `GX_SendFifo48B` | the geometry engine [S: `src/matched/NNS_G3dGeBufferOP_N.c`; source account: `src/matched/NNS_G3dGeBufferOP_N.c`; `port/render/gxfifo.c`] |
| `0x04000440`-`0x040005c8` | the 45 individual command ports, `0x04000440 + (op-0x10)*4` | `G3_*`, `G3X_*` | the same [S: `src/matched/G3_LoadMtx43.c`; source account: `src/matched/G3_LoadMtx43.c`; `port/render/gxfifo.c`] |
| `0x04000600` | `GXSTAT`: busy `0x08000000`, stack error `0x8000`, stack levels `0x1f00`/`0x2000`, FIFO IRQ `0xc0000000` | `G3X_Init`, `G3X_ResetMtxStack` | `G3X_GetClipMtx`, the wait loops [S: `src/matched/G3X_Init.c`; source account: `src/matched/G3X_Init.c`] |
| `0x04000640` / `0x04000680` | `CLIPMTX_RESULT` (16 fx32) / `VECMTX_RESULT` (9 fx32) | the geometry engine | `G3X_GetClipMtx` / `GetVectorMtx` [S: `src/matched/G3X_GetClipMtx.c`; source account: `src/matched/G3X_GetClipMtx.c`] |
| `0x05000000`/`0x200`/`0x400`/`0x600` | BG-A, OBJ-A, BG-B, OBJ-B palettes | `GX_LoadBGPltt` family | the 2D engines [S: `src/matched/GX_LoadBGPltt.c`; source account: `src/matched/GX_LoadBGPltt.c`] |
| `0x06400000` / `0x06600000` | OBJ tile space A / B | `GX_LoadOBJ`, `GXS_LoadOBJ` | the 2D engines [S: `src/matched/GX_LoadOBJ.c`; source account: `src/matched/GX_LoadOBJ.c`] |
| `0x06800000`+ | the LCDC bank aliases | `GX_VRAMCNT_SetLCDC_`, `GX_LoadTex` | the texture unit [S: `src/matched/GX_VRAMCNT_SetLCDC_.c`; source account: `src/matched/GX_VRAMCNT_SetLCDC_.c`] |
| `0x07000000` / `0x07000400` | OAM A / B, 128 entries each | `GX_LoadOAM`, `GXS_LoadOAM` | the 2D engines [S: `src/matched/GX_LoadOAM.c`; source account: `src/matched/GX_LoadOAM.c`] |

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
O: `scratchpad/oracle/off`, the same scene in DeSmuME ; `scratchpad/cycle40/runs/off-D51`]. At frame 37,800 clouds over the blue sky
above the town hall [E: `docs/log/cycle40-keyboard-gate-probe.md` GX40, run `off-D51`;
O: `scratchpad/oracle/off`, the same scene in DeSmuME log, SKY40, run `tap-D57` ; `scratchpad/cycle40/runs/off-D51`, `scratchpad/cycle40/runs/tap-D57`]. At frame 37,500 the town with overlays
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
  `GX_SetBankForClearImage` [S: `src/matched/GX_SetBankForClearImage.c`; source account: `port/render/raster3d.c`; `src/matched/GX_SetBankForClearImage.c`].
  Settle it by logging `DISP3DCNT` bit 14 across a long town run and a WFC-screen run.
- **Extended-rotscale and large-bitmap backgrounds (BG modes 3-6) are unused.** The port skips
  them and no scene has needed one so far [H: source account: `port/render/nds2d.c`, K_EXT / K_LARGE notes; direct ROM-source provenance unresolved].
  Settle it by asserting on `BGnCNT` values that select them across the interpreter recipes.
- ~~Windowing (`WIN0`/`WIN1`/`OBJWIN`), mosaic and extended palettes are unused.~~ Split: the
  window-0 component is RETIRED -- every scene transition is window 0 closing as an iris,
  drawn per scanline, and the port draws WIN0/WIN1 since FADE52/IRIS54 (the window section
  above) [E: `scratchpad/iris54/RECEIPTS.md`; log: `docs/log/cycle41-gameplay.md` FADE52, IRIS54].
  OBJWIN is still not drawn (FADE52 open item), and mosaic and extended palettes keep the old
  standing: noted, not implemented, no scene has needed one [H: source account:
  `port/render/nds2d.c`]. Settle those by asserting on `DISPCNT & 0x8000` (OBJWIN),
  `DISPCNT & 0xC0000000`, and the mosaic bits.
- **`BOX_TEST`, `POS_TEST` and `VEC_TEST` (GX commands 0x70-0x72) matter to the game's culling.**
  The port stubs all three, clearing the GXSTAT test-busy bit and reporting "visible"
  [H: source account: `port/render/nds3d.c`; direct ROM-source provenance unresolved]. If the game culls with `BOX_TEST`, always answering "visible"
  costs polygons but changes nothing visible; if it culls with `POS_TEST` results, it could be
  wrong. Settle it by counting 0x70/0x71/0x72 submissions per frame on the town recipe.
- **The port's `POWCNT1` reading is engine-A-on-bottom at `0x020f`.** That is an experimental
  reading of a port run [H: log/source account: `docs/kb/port/render.md`; receipt provenance unresolved], and the oracle has not been used to
  confirm the same swap on hardware timing. Settle it by comparing the two screens' contents
  between `scratchpad/oracle/*` and a port run at the same frame.
- **`NNS_G3dGeSendDL`'s 256-byte threshold means most shapes go through the buffer, not DMA.**
  The threshold is in the source [S: `src/matched/NNS_G3dGeSendDL.c`; source account: `src/matched/NNS_G3dGeSendDL.c`]; the actual distribution is
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
