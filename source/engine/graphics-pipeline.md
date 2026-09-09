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
[S: `docs/kb/port/render.md`, texture provenance]. `ACWW_OAMDUMP=<frame>` dumps both OAM tables
and is not gated on `ACWW_TRACE_STATE` [S: `docs/kb/port/render.md`, OAM cursor table].
`ACWW_NOBLEND=1` disables the colour special effects so a blend can be isolated
[S: `port/render/nds2d.c`].

## Hypotheses

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
- `../data/rom-layout.md` — where the model, texture and menu assets live.
- `text-and-messages.md` — glyphs, which are drawn through the same 2D engines.
- `display-objects.md`, `memory-map.md` — the framework and the arenas around this pipeline.
