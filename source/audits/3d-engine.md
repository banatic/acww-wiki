# Audit: the port's 3D engine against the public record

**Summary.** The port's software geometry engine (`port/render/nds3d.c`) and rasteriser
(`port/render/raster3d.c`), with the command parser (`gxfifo.c`) and texture unit (`tex3d.c`),
were checked claim by claim against GBATEK's DS 3D chapter and against the two accurate
software emulators, melonDS's `GPU3D.cpp` / `GPU3D_Soft.cpp` and DeSmuME's `gfx3d.cpp` /
`rasterize.cpp`. Sixty-one claims were checked: thirty-eight agree, seventeen disagree, four
are unspecified by the public record, and two are outright contradictions between the port's
own measurement and the emulators. The geometry stage is in good shape — matrices, the
row-vector convention, clipping, the viewport, lighting, the texture-matrix mode-1 constant and
every texture format are right, several of them right in ways the public record makes easy to
get wrong. **The damage is concentrated in three places: translucent blending (the port applies
the polygon alpha twice over the rear plane and accumulates alpha where hardware takes a
maximum), W-buffered depth (ACWW is a W-buffer game and the port interpolates W linearly and
skips the per-polygon W normalisation), and the four effects the port declares but does not
perform — fog, edge marking, toon and anti-aliasing.** Two of the twelve diagnostic notes are
overloaded and mean something other than what they say.

**Status since that reading (TOUCH41 relink, 2026-09-09).** Two of the three damaged areas have
moved and this page's fix sections carry the numbers. **F3 is ON**: A3I5 and A5I3 polygons are
treated as translucent, worth NCC 0.9958 -> 0.9985 at frame 9,000 and 0.9957 -> 0.9989 at
12,000. **The perspective half of F2 is ON**: W-buffered depth goes through the perspective
interpolator. **The per-polygon W normalisation is REJECTED** and off by default behind
`ACWW_WNORM=1`, because on its own it costs 0.13 NCC — a polygon whose W is constant normalises
to `0x8000` whatever its distance, so a normalised-W depth is ordered within a polygon and
arbitrary between polygons. `port/tools/test_raster3d_depth.py` is the fixture that pins both
answers, **54 checks** [S: `docs/log/cycle40-keyboard-gate-probe.md` TOUCH41;
`docs/state/port-frontier.md`]. Nothing has moved on the translucent-blending group or on the
four declared-but-unperformed effects.

**Status, RENDER43 (2026-09-10, `6081a9a1` + this unit).** Two more rows moved, and one of them
was a whole open break rather than a spec detail. **F15 is ON**: SWAP_BUFFERS is honoured at most
once per frame and the rest are held, which is the `docs/log/cycle41-gameplay.md` GP42-6
acre-ground dropout — nineteen swaps in one frame discarding eighteen display lists (new claim
row **G4**). **F14 is ON**: the 3D layer is scrolled by BG0HOFS (row **G3**, "not implemented,
not noted" since the audit), measured inert because ACWW writes zero. And row **E14b** corrects
this page's own reading of the emulators' sample point: **DeSmuME 0.9.13 does not quantise
vertices to whole pixels — melonDS does** — so `ACWW_SAMPLE_INT` is the whole rule and not half
of a pair, and the reason it is still off is a frame-mapping artefact, not a missing change
[`docs/kb/hybrid/render-fidelity-history.md` sections 2b, 4; `docs/kb/hybrid/render-fixes.md` section 3].

**Method.** Read at the worktree head of `main` (`6ca48706`). Public sources were fetched, not
remembered; every row names the page or file. No code was copied from any source. The game was
not run and no measurement in this page is new — port-side numbers are cited from
`docs/log/` and from the oracle comparison already on disk.

---

## 1. What the game actually asks the engine for

This decides which rows matter. `func_02002f68` is the game's 3D bring-up and it is a matched
source, so this is grade S.

| Register | Value the ROM writes | Consequence |
|---|---|---|
| `DISP3DCNT` `0x04000060` | cleared, then `\|0x10`, then `\|0x08`, then `&0xcfdf` | alpha-blending **on** (bit 3), anti-aliasing **on** (bit 4), edge marking **off** (bit 5), highlight-shading select **off** (bit 1) [S: `src/matched/func_02002f68.c`] |
| `VIEWPORT` `0x04000580` | `0xbfff0000` | X1=0, Y1=0, X2=255, Y2=191 — full screen, and the same value the port defaults to |
| `SWAP_BUFFERS` `0x04000540` | `3` | bit 0 = **manual** translucent Y-sorting, bit 1 = **W-buffer** depth |
| `G3X_SetClearColor` `0x02112304` | `(rgb=0, alpha=0, depth=0x7fff, polygonID=0x3f, fog=TRUE)` | rear plane transparent (so the 2D sky shows), clear polygon ID `0x3f`, **rear-plane fog enabled** |

So: ACWW is a W-buffered, alpha-blended, anti-aliased, manually-sorted, edge-marking-off game
whose rear plane is transparent and fog-flagged. Fog master enable (`DISP3DCNT` bit 7) is not
set by this function; whether anything sets it later is open — see H3.

Material census, from the port's own header comment over the ROM's 866 models
[H: host/prose inference from `port/render/raster3d.c` header; verify against the ROM function or symbol table and this page's recipe]: all 2,040 materials are `GX_POLYGONMODE_MODULATE` (no
decal, no toon, no shadow); 17,173 of 18,767 primitives are triangle strips.

---

## 2. Claims table

Verdict is **agrees** / **disagrees** / **unspecified** / **contradiction**. "Port" names the
file and function the claim lives in.

### A. Command stream, matrices and the stacks

| # | Claim as the port states it | Public source | Verdict | What to change |
|---|---|---|---|---|
| A1 | Parameter counts: `MTX_LOAD_4x4`=16, `4x3`=12, `3x3`=9, `VTX_16`=2, `SHININESS`=32, `BOX_TEST`=3, `POS_TEST`=2, `VEC_TEST`=1 [`gxfifo.c`, `param_count`] | GBATEK, [DS 3D Geometry Commands](https://problemkaputt.de/gbatek-ds-3d-geometry-commands.htm) | agrees | nothing |
| A2 | Valid commands are 0x10–0x1C, 0x20–0x2B, 0x30–0x34, 0x40–0x41, 0x50, 0x60, 0x70–0x72; anything else is not a command [`gxfifo.c`] | GBATEK, [DS 3D Overview](https://problemkaputt.de/gbatek-ds-3d-overview.htm) | agrees | nothing |
| A3 | A vertex is a row vector, `v' = v × M`, translation in the fourth **row**; `MTX_MULT_*` computes `current = param × current` [`nds3d.c` header, `mat_target_mult`] | GBATEK, [DS 3D Matrix Types](https://problemkaputt.de/gbatek-ds-3d-matrix-types.htm); melonDS `GPU3D.cpp` | agrees | nothing — this is the single easiest thing in the file to get backwards |
| A4 | Position/vector stack is 31 usable levels, projection and texture are 1 [`nds3d.c`, `POS_STACK_DEPTH`] | GBATEK, [DS 3D Matrix Stack](https://problemkaputt.de/gbatek-ds-3d-matrix-stack.htm) | agrees | nothing |
| A5 | `MTX_POP`'s parameter is a signed 6-bit offset; projection mode pops one level regardless [`nds3d.c` case 0x12] | GBATEK, same page: offset −30..+31, projection forced to +1 | agrees | nothing |
| A6 | Pushing at level 31 sets the stack error and **does not push**; popping out of range sets the error and clamps [`nds3d.c` case 0x11/0x12] | GBATEK, same page: entry 31 exists and is read/write accessible, touching it **sets the flag but the operation still proceeds** against the mirrored entry | disagrees (minor) | let the push happen against the clamped slot after raising the error, so a game that over-pushes still gets self-consistent matrices back |
| A7 | `MTX_STORE`/`MTX_RESTORE` take a 5-bit slot index [`nds3d.c` case 0x13/0x14] | GBATEK: legal addresses are 0..30; address 31 sets the overflow flag | disagrees (minor) | raise `GX_NOTE_MTXSTACK` on index 31 as well |
| A8 | `MTX_SCALE` applies to the position matrix only, even in mode 2 [`mat_target_mult(..., 1)`] | GBATEK, [DS 3D Matrix Stack](https://problemkaputt.de/gbatek-ds-3d-matrix-stack.htm) | agrees | nothing — and it is the line that separates lit geometry from geometry whose lighting changes when it is scaled |
| A9 | `CLIPMTX_RESULT` is `position × projection`, published after every matrix command [`mtx_readback`] | GBATEK, [DS 3D Tests](https://problemkaputt.de/gbatek-ds-3d-tests.htm), POS_TEST "clip coordinate matrix" | agrees | nothing |
| A10 | `GXSTAT` carries the stack level in bits 8–12, projection level in 13, error in 15, and the port additionally reports "FIFO less than half full" as bit 25 [`gxstat_update`] | GBATEK, [DS 3D Status](https://problemkaputt.de/gbatek-ds-3d-status.htm): 25 = less-than-half-full, **26 = FIFO empty**, 27 = geometry busy, 30–31 = FIFO IRQ mode (the only writable field) | disagrees | `gxstat_update()` writes a fresh word each time and preserves only bit 15. It therefore (a) never sets **bit 26**, so an SDK loop polling "FIFO empty" never terminates; (b) erases **bits 30–31**, which `NNS_G3dInit` sets [S: `src/matched/NNS_G3dInit.c`]; (c) erases the box-test result in bit 1 the moment any matrix command runs. See fix **F7** |
| A11 | `BOX_TEST`/`POS_TEST`/`VEC_TEST` are answered "visible" without testing; the busy bit is cleared [`nds3d.c` case 0x70–0x72] | GBATEK, [DS 3D Tests](https://problemkaputt.de/gbatek-ds-3d-tests.htm): `POS_RESULT` is four words at `0x04000620`, `VEC_RESULT` three halfwords at `0x04000630` | disagrees | `BOX_TEST` answering "visible" is the safe direction and costs only polygons. `POS_TEST` and `VEC_TEST` write **nothing**, so the game reads whatever the I/O page held. Both are two lines of existing code — see fix **F5** |
| A12 | `RAM_COUNT` and the `DISP3DCNT` bit 13 overflow flag are not implemented; overflow raises a note only [`emit_poly`] | GBATEK, [DS 3D Status](https://problemkaputt.de/gbatek-ds-3d-status.htm): `RAM_COUNT` `0x04000604`, polygons in bits 0–11 (max 2048), vertices in 16–28 (max 6144) | disagrees (minor) | write the two counters and set `DISP3DCNT` bit 13 on overflow; the port already has both numbers |

### B. Vertices, primitives, clipping and the viewport

| # | Claim | Public source | Verdict | What to change |
|---|---|---|---|---|
| B1 | `VTX_16` is 1.3.12 raw; `VTX_10` is 1.3.6 and shifts left 6 [`nds3d.c` case 0x23/0x24] | GBATEK, [DS 3D Polygon Definitions by Vertices](https://problemkaputt.de/gbatek-ds-3d-polygon-definitions-by-vertices.htm) | agrees | nothing |
| B2 | `VTX_DIFF` adds the sign-extended 10-bit fields **raw**, with no shift [`nds3d.c` case 0x28] | GBATEK, same page: the deltas are "1-bit sign + 9-bit fractional" and are **divided by 8** relative to the `VTX_10` reading, i.e. `<<3` into 1.3.12. DeSmuME `gfx3d.cpp` sign-extends and shifts by the same net 3 | **contradiction** | The port removed the `<<3` on `8a7fdb5f` after an offline reconstruction of `npc/model/48/49.nsbmd` matched the model's own declared bounding box exactly at shift 0 and fell outside it at shift 3 [E: `docs/log/2026-09-02.md`]. Both cannot be right and the oracle **is** DeSmuME. See H1 — this is the highest-value open question on the page |
| B3 | `VTX_XY`/`XZ`/`YZ` keep the third component from the previous vertex [`nds3d.c` case 0x25–0x27] | GBATEK, same page | agrees | nothing |
| B4 | Strips: triangle strip alternates winding on a rolling window of three; quad strip rings its vertices `v0,v1,v3,v2` [`submit_vertex`] | GBATEK, same page, BEGIN_VTXS 0–3 | agrees | nothing |
| B5 | A vertex outside `BEGIN_VTXS`/`END_VTXS` is ignored [`submit_vertex`, `if (!in_prim) return`] | GBATEK: `END_VTXS` is a dummy for OpenGL parity | agrees | nothing |
| B6 | Clipping is Sutherland–Hodgman against all six planes, after which the polygon may have up to ten vertices [`clip_plane`, `ClipPoly`] | GBATEK, same page: clipped against all six sides, a clipped vertex is replaced by two new ones | agrees | nothing |
| B7 | Clipped vertex colours are interpolated at 8 bits per channel [`lerp_vtx`] | melonDS `GPU3D.cpp`: "vertex colors are kept at 5-bit during clipping. makes for shitty results", then converted to 9-bit as `(x<<4)+0xF` before drawing, "the added bias affects interpolation" | disagrees (cosmetic) | the port is smoother than hardware on purpose and says so; leave it, but record that gradients across a clipped polygon will not match the oracle byte for byte |
| B8 | Screen x is `x1 + (x + w) · vw / (2w)` in 12.4 [`to_screen`] | GBATEK, same page: `screen_x = (xx + ww) × viewport_width / (2 × ww) + viewport_x1` | agrees | nothing |
| B9 | Screen y is `(191 − y2)·16 + (w − y)·vh·16 / (2w)`, with `vh = y2 − y1 + 1` [`to_screen`] | GBATEK: viewport coordinates have their **origin at the lower left**, so the row from the top is `191 − [(y+w)·vh/(2w) + y1]` | disagrees (suspected off-by-one) | Substituting `y2 = y1 + vh − 1` turns the port's expression into `192 − y1 − t·vh` against the spec's `191 − y1 − t·vh`. **The whole 3D layer is one row too low.** Cheap to settle — see fix **F8** |
| B10 | The front face is the negative-shoelace winding in screen space [`emit_poly`, `GX_FRONT_IS_NEGATIVE_AREA`] | GBATEK: vertices are normally wound anti-clockwise; DeSmuME `rasterize.cpp` warns "due to a late change of a y-coord flipping, our winding order is wrong … flip the verts for every front-facing poly" | agrees | nothing — the sign is right and the file already names it as the one sign not derived from a formula |
| B11 | The perspective divide is done with a 64-bit shift-and-subtract loop that saturates rather than wrapping [`div64`, `sdiv64`] | melonDS `GPU3D.cpp`: "the DS performs these divisions using a 32-bit divider", shifting W down when it exceeds 0xFFFF and losing precision | disagrees (the port is more accurate) | leave it; note that distant geometry will **not** show the hardware's vertex snapping, which is a difference the oracle will show |
| B12 | A polygon with zero screen area is dropped and counted as `degenerate` [`emit_poly`] | GBATEK, [DS 3D Display Control](https://problemkaputt.de/gbatek-ds-3d-display-control.htm): `DISP_1DOT_DEPTH` `0x04000610`; a 1-dot polygon is drawn when any vertex's W ≤ the threshold and `POLYGON_ATTR` bit 13 is set, using the **first vertex's** colour, depth and texture. melonDS rejects upstream on the same rule | disagrees | distant town detail that hardware renders as single dots is silently lost. See fix **F9** |
| B13 | `POLYGON_ATTR` is latched at `BEGIN_VTXS`, and lighting at `NORMAL` uses the latched light-enable bits [`poly_attr_live`, `light_vertex`] | GBATEK, [DS 3D Polygon Attributes](https://problemkaputt.de/gbatek-ds-3d-polygon-attributes.htm): writes take effect at the next `BEGIN_VTXS`, and the vertex colour is recomputed only when `NORMAL` executes | agrees | nothing |

### C. Lighting and materials

| # | Claim | Public source | Verdict | What to change |
|---|---|---|---|---|
| C1 | `colour = emission + Σ (specular·shine + diffuse·diff + ambient) · lightcolour`, with `diff = max(0, −light·normal)` and `shine = max(0, −half·normal)²` [`light_vertex`] | GBATEK, [DS 3D Polygon Light Parameters](https://problemkaputt.de/gbatek-ds-3d-polygon-light-parameters.htm) | agrees | nothing |
| C2 | The eye vector is the constant `(0, 0, −1)`, so `half = (light + eye)/2` [`light_vertex`] | GBATEK, same page: the DS cannot normalise in hardware, omits the projection multiply and hardcodes `(0,0,−1.0)`; "specular reflection will not work when the projection matrix is rotated" | agrees | nothing — and the port inherits the hardware bug, which is correct |
| C3 | `LIGHT_VECTOR` is transformed by the vector matrix at the moment the command runs and stored transformed [`nds3d.c` case 0x32] | GBATEK, same page | agrees | nothing |
| C4 | `SHININESS` is 128 entries in 32 words, four 8-bit entries per word, indexed by the squared level [`nds3d.c` case 0x34] | GBATEK, same page | agrees | nothing |
| C5 | With the shininess table disabled, the squared level is used directly [`spec_table_on`] | GBATEK: with the table disabled the hardware behaves as if it held a **linear ramp** — i.e. the level itself | agrees | nothing |
| C6 | `DIF_AMB` bit 15 additionally sets the vertex colour [`nds3d.c` case 0x30] | GBATEK, same page | agrees | nothing |
| C7 | Colours are carried at 8 bits per channel throughout [`exp5`, `add_term`] | GBATEK: the internal pipeline is 5/6-bit; melonDS quantises to 5 bits and re-expands with a `+0xF` bias | disagrees (deliberate, cosmetic) | leave it; the file already argues the case. It does mean no frame will ever be byte-equal to the oracle |

### D. The texture unit

| # | Claim | Public source | Verdict | What to change |
|---|---|---|---|---|
| D1 | Size fields are `8 << n`, so the log2 is `n + 3`; S-size at bits 20–22, T-size at 23–25 [`acww_gx_texel`] | GBATEK, [DS 3D Texture Attributes](https://problemkaputt.de/gbatek-ds-3d-texture-attributes.htm) | agrees | nothing |
| D2 | The palette base is `PLTT_BASE << 4` for every format **except** format 2, where it is `<< 3` [`pbase`] | GBATEK, same page: "div8 or div10h"; melonDS and DeSmuME both halve the base for the 2bpp format | agrees | nothing — the file's comment about the failure mode (plausible but wrong colours) is exactly right |
| D3 | All seven formats decode: A3I5, 4/16/256-colour, 4x4 compressed, A5I3, direct [`acww_gx_texel`] | GBATEK, [DS 3D Texture Formats](https://problemkaputt.de/gbatek-ds-3d-texture-formats.htm) | agrees | nothing. **This means the note "a texture format … is not decoded" can never fire for a format** — see §3 |
| D4 | A3I5's 3-bit alpha expands as `(a<<5)\|(a<<2)\|(a>>1)`, i.e. `a·255/7` [`case 1`] | GBATEK: `Alpha = (Alpha*4) + (Alpha/2)` onto the 0..31 scale — the same ratio | agrees | nothing |
| D5 | Direct colour: bit 15 set means **opaque** [`default` case] | GBATEK, same page; melonDS `alpha = (c & 0x8000) ? 31 : 0` | agrees | nothing |
| D6 | The 4x4 block's index word lives at `0x20000 + (offset & 0x1FFFF)/2 + (offset & 0x40000)/4` [`comp4x4_info_offset`] | GBATEK: `slot1 = slot0/2`, and `slot1 = slot2/2 + 0x10000`. DeSmuME: `indexBase = ((offset & 0xC000) == 0x8000) ? 0x30000 : 0x20000` | agrees | nothing |
| D7 | 4x4 selector/mode table: mode 0 → {c0,c1,c2,transparent}; mode 1 → {c0,c1,(c0+c1)/2,transparent}; mode 2 → {c0..c3}; mode 3 → {c0,c1,(5c0+3c1)/8,(3c0+5c1)/8} [`case 5`] | GBATEK, same page; melonDS and DeSmuME agree | agrees | nothing. Interpolating on the 5-bit channels before expansion, as the port does, is also right |
| D8 | Repeat/flip: flip only applies when repeat is on, and mirrors alternate tiles [`acww_gx_wrap`] | GBATEK; melonDS: `if (s & width) s = (width-1) - (s & (width-1)); else s &= width-1` | agrees | nothing |
| D9 | Texture-coordinate mode 1 is `(s, t, 1, 1) × M >> 12`, the constant terms being **1**, not `0x100` [`apply_texmtx`] | melonDS `GPU3D.cpp`: `(s*m0 + t*m4 + m8 + m12) >> 12`, "both the third *and* fourth matrix rows are added". GBATEK's "1/16.0" is one texel-sixteenth, which in the port's 1/16-texel unit **is** 1 | agrees | nothing. The port's 2026-09-02 correction is confirmed by melonDS and by `NNSi_G3dSendTexSRTSi3d` independently |
| D10 | Mode 2 (normal source) is `raw + (o >> 8)` where `o = (n, 1) × M >> 12`; mode 3 (vertex source) is the same with the position [`apply_texmtx`] | melonDS: mode 2 is `raw + (nx·m0 + ny·m4 + nz·m8) >> 21` and mode 3 is `raw + (x·m0 + y·m4 + z·m8) >> 24`, with **no fourth-row term**. GBATEK says the TEXCOORD S,T sits in the matrix's bottom row | disagrees | The port's net shift is 20 against a normal it has already scaled `<<3`, making mode 2 **16× too large**; mode 3 is likewise 16× too large; and both add a spurious `m12/m13` term on top of `raw_s`. See fix **F6** |
| D11 | An unmapped VRAM bank or a format-0 texture returns fully transparent, silently [`tex_addr`, `pltt_addr` returning 0] | — | unspecified, but a diagnostic hole | a texture whose bank is not mapped produces a hole in the world with **no note anywhere**. See fix **F4** |

### E. Depth, fill and translucency — the rasteriser

| # | Claim | Public source | Verdict | What to change |
|---|---|---|---|---|
| E1 | Z-buffer depth is `(((z · 0x4000) / w) + 0x3FFF) · 0x200`, clamped to 24 bits [`to_screen`] | melonDS `GPU3D_Soft.cpp`, identical expression | agrees | nothing |
| E2 | *(as read at `6ca48706`; F2 has since landed — see the fix)* W-buffer depth is the clip `w`, clamped to 24 bits [`to_screen`] | melonDS `GPU3D.cpp`: "W is normalized, such that all the polygon's W values fit within 16 bits" — expanded upward when they fit in fewer bits, compressed when larger — and the **normalised** W is what W-buffering uses (but not the viewport transform) | disagrees | **ACWW is a W-buffer game** (`SWAP_BUFFERS = 3`). Without the per-polygon normalisation the depth values of a whole polygon land in the wrong part of the 24-bit range. See fix **F2** |
| E3 | *(as read at `6ca48706`; F2 has since landed)* Depth is interpolated linearly across the span in both modes [`attr_lerp` on `a[0]`] | melonDS `GPU3D_Soft.h`, `InterpolateZ()`: Z-buffered depth is linear in screen space; **W-buffered depth goes through the perspective interpolator** | disagrees | again, ACWW's mode is the one that is wrong. A ground plane at a shallow angle has its depth wrong in the middle of every polygon. See fix **F2** |
| E4 | The depth-equal tolerance is ±0x200 [`draw_poly`, `depth_equal`] | GBATEK, [DS 3D Polygon Attributes](https://problemkaputt.de/gbatek-ds-3d-polygon-attributes.htm): "±200h within the 24-bit range". melonDS splits it: **±0x200 in Z mode, ±0xFF in W mode** | disagrees (minor) | use 0xFF when `wbuffer_mode` is set |
| E5 | The depth test is strict less-than [`(gu32)a.a[0] >= depth[off]` → reject] | melonDS `GPU3D_Soft.cpp` and blog "[The DS GPU and its fun quirks](https://melonds.kuribo64.net/comments.php?id=56)": the less-than compare "accepts equal depth values when drawing front-facing polygons over opaque **back-facing** pixels", and games rely on it for flat decals | disagrees | the port stores no facing bit per pixel, so it cannot reproduce this. Low priority for ACWW (no decal materials) but it is why a coplanar sticker can drop out |
| E6 | Translucent polygons write depth only when `POLYGON_ATTR` bit 11 is set [`write_depth`] | GBATEK and both emulators | agrees | nothing |
| E7 | A translucent pixel is rejected outright when the pixel already there was written by a translucent polygon of the **same** ID [`tattr`, `tmark`] | melonDS: `(dstattr & 0x007F0000) == (attr & 0x007F0000)` → discard; DeSmuME: "dont overwrite pixels on translucent polys with the same polyids" | agrees | nothing — but the "3 times in a 200-second taxi run, so it is inert" reading died with F3: once translucency is decided per FRAGMENT, the same recipe to frame 12,000 rejects 4,880,683 fragments, about 400 a frame. The rule is live |
| E8 | Alpha blending is `dst = src·a + dst·(1−a)` with the destination alpha accumulated as `a + da·(1−a)` [`draw_poly`] | GBATEK, [DS 3D Toon, Edge, Fog, Alpha-Blending, Anti-Aliasing](https://problemkaputt.de/gbatek-ds-3d-toon-edge-fog-alpha-blending-anti-aliasing.htm): `FrameBuf[X] = (Poly[X]·(Poly[A]+1) + FrameBuf[X]·(31−Poly[A]))/32` and **`FrameBuf[A] = max(Poly[A], FrameBuf[A])`**; melonDS and DeSmuME agree | disagrees | the alpha must be a **maximum**, not an accumulation. Two overlapping translucent surfaces at alpha 16 leave the port at 88% opaque and hardware at 52%. See fix **F1** |
| E9 | A translucent pixel blends against whatever is in the colour buffer, including the cleared rear plane [`draw_poly`] | GBATEK, same page: blending is **skipped** and the pixel simply overwrites when (a) alpha-blending is off, (b) `Poly[A] = 31`, or (c) **`FrameBuf[A] = 0`**; both emulators agree | disagrees | ACWW's clear alpha is 0, so every translucent polygon over the empty rear plane is blended against a black, zero-alpha destination — its RGB is multiplied by its alpha — and then the compositor multiplies by the alpha **again** when it lays the 3D layer over the 2D sky. **Every translucent surface in the taxi and the town is darkened twice.** See fix **F1** |
| E10 | Alpha 0 means wireframe, and the port skips the polygon [`draw_poly`, `alpha5 == 0`] | GBATEK: alpha 0 draws the polygon's **edges only, at a fixed alpha of 31**; melonDS implements exactly that and forces alpha to 31 at the end. DeSmuME has no wireframe path at all | disagrees | ACWW has no wireframe materials by the port's census, so the cost is zero today. But the skip raises `GX_NOTE_BADCMD`, which reports as "an unknown command id reached the parser" — see §3 |
| E11 | The alpha test keeps a texel whose alpha is non-zero; `ALPHA_TEST_REF` is not read [`draw_poly`] | GBATEK, [DS 3D Display Control](https://problemkaputt.de/gbatek-ds-3d-display-control.htm): a pixel is drawn only if its alpha is **greater than** `ALPHA_TEST_REF`, applied to the **final** pixel after texture blending; ref 0 is identical to the test being disabled | agrees for ACWW (ref 0), disagrees in general | read `ALPHA_TEST_REF` at `0x04000340` and compare against `fa`, not against the texel alpha. Three lines |
| E12 | Two passes, opaque then translucent, both in submission order, because `SWAP_BUFFERS` bit 0 asks for manual sorting [`acww_nds3d_raster`] | melonDS `SortKey`: opaque first, then translucent; **opaque polygons are always Y-sorted**, and bit 0 decides only whether translucent ones join the Y sort | agrees for ACWW | the port never reads bit 0. Add a note when auto-sort is requested, so a later scene that wants it is not silently mis-ordered |
| E13 | *(as read at `6ca48706`; F3 has since landed)* A polygon is "translucent" iff its `POLYGON_ATTR` alpha is not 31 [`trans` in `draw_poly`] | GBATEK, [DS 3D Texture Formats](https://problemkaputt.de/gbatek-ds-3d-texture-formats.htm): A3I5 (format 1) and A5I3 (format 6) are the "translucent" formats; melonDS decides translucency **per pixel** from the blended alpha, and notes "translucent polygons can have opaque pixels, and those follow the same rules as opaque polygons" | disagrees | an alpha-31 polygon carrying an A3I5 or A5I3 texture draws in the **opaque** pass in the port, writes depth, and is exempt from the same-ID rule. On hardware its partially-transparent texels are translucent fragments. This is the taxi's rain and window glass. See fix **F3** |
| E14 | The span is filled where the pixel centre `(px·16 + 8)` lies in `[xL, xR)` and the sample row in `[ya, yb)` [`draw_poly`] | melonDS `GPU3D_Soft.h`/`.cpp`: the DS has explicit slope-based fill rules — "right edge is filled if slope > 1; left edge is filled if slope ≤ 1; edges with slope = 0 are always filled"; edges are **always** filled when AA or edge marking is on, when the pixel is translucent with blending on, or when the polygon is wireframe; and "right vertical edges are pushed 1px to the left" under stated conditions | disagrees | a sample-centre rule drops any polygon narrower or shorter than one pixel that misses the centre; hardware fills at least the edge. Thin fences, railings and distant detail vanish. Because ACWW has AA on, hardware's **edges are always filled** for its geometry, which makes the port systematically thinner. See fix **F9** |
| E14b | *(RENDER43, and it corrects E14's "both emulators sample at the integer coordinate", which was the basis for the RENDER42 experiment)* The ORACLE's fill rule, clause by clause: sub-pixel coordinates are **12.4, rounded to nearest** (`rasterize.cpp` `_TransformVertices`: `vert.coord[0] = (float)iround(16.0f * vert.coord[0])`), the first scanline is `Ceil28_4(y_top)` and `Ceil28_4(v) = (v-1+16)/16 = ceil(v/16)`, the row range is `[ceil(y_top/16), ceil(y_bot/16)-1]`, the span is `[ceil(x_L/16), ceil(x_R/16)-1]` (`edge_fx_fl`, `_drawscanline`'s `width = pRight->X - XStart`), and the sample point is the pixel's INTEGER coordinate | DeSmuME 0.9.13, tag `release_0_9_13`, `desmume/src/rasterize.cpp` | the port's `ACWW_SAMPLE_INT=1` arm **agrees exactly**; the default (`soff = 8`, pixel centres) disagrees by half a pixel | **DeSmuME does NOT quantise vertices to whole pixels — melonDS does** (`GPU3D.cpp` `SubmitPolygon`, `FinalPosition[0] = posX & 0x1FF`). So there is no "pair" and `ACWW_SAMPLE_INT` is the whole rule. Still off by default: it clears the mean and the mae and loses ncc on 9 of 31 OFF frames, and the residual those nine measure is a whole-pixel VERTICAL phase difference (`render-fidelity-history.md` section 4). A CALIBRATED oracle set settles it |
| E15 | Perspective correction is `q = (wmin << 14)/w`, with `s·q`, `t·q` and `q` interpolated linearly and divided per pixel [`draw_poly`] | melonDS `GPU3D_Soft.h`: the DS computes **one** perspective factor from the two W values, quantises it to 9 bits along an edge and 8 bits along a span, then applies that single factor linearly to every attribute; there is a special **linear** path when the two W values are equal after masking the low 7 bits | agrees in effect, disagrees in precision | the port is more accurate than hardware. Two consequences: DS texture stair-stepping is absent, and 2D quads drawn through the 3D engine will not be pixel-exact the way hardware's W-equal shortcut makes them. Record it; do not "fix" it before the oracle asks |
| E16 | The clear depth is `(cd << 9)`, plus `0x1FF` **only** at `0x7FFF` [`clear_buffers`] | GBATEK, [DS 3D Rear-Plane](https://problemkaputt.de/gbatek-ds-3d-rear-plane.htm): `X = (X·200h) + ((X+1)/8000h)·1FFh` — the port matches this exactly. melonDS uses `(d & 0x7FFF)·0x200 + 0x1FF` unconditionally | agrees with GBATEK, disagrees with melonDS | no change: ACWW clears at `0x7FFF`, where the two are identical. Worth recording that the port followed GBATEK and the emulator did not |
| E17 | The clear polygon ID and the clear fog flag are not stored per pixel [`clear_buffers`] | GBATEK: `CLEAR_COLOR` bits 24–29 are the clear polygon ID and bit 15 the rear-plane fog enable; melonDS writes both into the attribute buffer and additionally into a one-pixel border **outside** the visible area so border edge-marking works | disagrees | ACWW sets the ID to `0x3f` and fog to true. Blocks edge marking and rear-plane fog. Prerequisite for **F10** and **F11** |
| E18 | The rear-plane bitmap (`DISP3DCNT` bit 14) is not implemented; a note fires [`clear_buffers`] | GBATEK: two 256×256 16-bit bitmaps in texture slots 2 and 3, scrolled by `CLRIMAGE_OFFSET` | disagrees, correctly noted | `func_ov001_0222e4dc` does call `GX_SetBankForClearImage`, so this is not obviously dead. Settle it by logging bit 14 — already an open question on `wiki/engine/graphics-pipeline.md` |

### F. The effects the port declares and does not perform

| # | Claim | Public source | Verdict |
|---|---|---|---|
| F-fog | Fog is noted, never rendered [`clear_buffers`, `GX_NOTE_FOG`] | GBATEK gives the whole algorithm: `FogDepthBoundary[n] = FOG_OFFSET + FOG_STEP·(n+1)`, `FOG_STEP = 0x400 >> FOG_SHIFT`, 32 density entries of 7 bits linearly interpolated between boundaries, blend `(FogColor·D + FrameBuf·(128−D))/128` on RGB **and** A, with `D = 127` treated as 128, alpha-only when `DISP3DCNT` bit 6 is set, and the rear plane carrying its own fog flag. melonDS interpolates the table with a 17-bit fraction and applies fog to **both** framebuffer layers | disagrees — fully specified, entirely absent |
| F-edge | Edge marking is noted, never rendered | GBATEK: `EDGE_COLOR` `0x04000330`, **8** entries indexed by `polygonID >> 3`. melonDS: an edge is a pixel whose **opaque** polygon ID differs from one of its four orthogonal neighbours **and** whose depth is less than that neighbour's; screen borders compare against the clear polygon ID | disagrees, but ACWW turns edge marking **off** — cost is zero |
| F-toon | Polygon mode 2 is drawn as modulation and noted | GBATEK: `TOON_TABLE` `0x04000380`, 32 colours, indexed by the **red component of the vertex colour**; toon replaces the vertex colour then modulates, highlight additionally **adds** the toon colour with saturation at 63, selected globally by `DISP3DCNT` bit 1. Both emulators index `vertexRed >> 1` | disagrees; the port's census says ACWW has zero toon materials, but `G3X_SetToonTable` exists in the ROM's SDK and the note is the only instrument |
| F-aa | Anti-aliasing is noted, never performed | melonDS "[Antialiasing](https://melonds.kuribo64.net/comments.php?id=32)": coverage is computed per edge pixel by the slope walker, stashed in the attribute buffer, and applied in a **separate pass after edge marking and fog**, blending the top framebuffer layer with a second layer that opaque writes push down. It applies only to silhouette edges of opaque polygons, never inside a polygon or at an intersection | disagrees, and **ACWW turns AA on** |
| F-shadow | Polygon mode 3 is dropped and noted | GBATEK, [DS 3D Shadow Polygons](https://problemkaputt.de/gbatek-ds-3d-shadow-polygons.htm), plus melonDS's two stencil bits | disagrees; ACWW's census says zero shadow materials |

### G. Composition with the 2D engines

| # | Claim | Public source | Verdict | What to change |
|---|---|---|---|---|
| G1 | The 3D output is engine A's BG0, composed at BG0's own priority, and enters the blend owner record as BG0 [`nds2d.c`, `K_3D` branch] | GBATEK, [DS 3D Final 2D Output](https://problemkaputt.de/gbatek-ds-3d-final-2d-output.htm) | agrees | nothing — and the comment about compositing it four times a frame is worth keeping |
| G2 | The 3D layer blends over the 2D result with `dst = c·a + d·(1−a)` on 0..255 alpha [`acww_nds3d_compose`] | GBATEK, same page: per-pixel 3D blending uses **`EVA = A/2`, `EVB = 16 − A/2`** derived from the 3D pixel's own alpha, bypassing `BLDALPHA` | agrees in form, differs in quantisation | the 5-bit alpha becomes a 4-bit weight on hardware. Small; the compounding in **E9** is the real problem |
| G3 | `BG0HOFS` scrolling of the 3D layer, and the fact that mosaic cannot apply to it | GBATEK, same page: 512-pixel span, 256 of image then 256 transparent, wrapping; no vertical scroll, no rotation | **FIXED (F14, RENDER43)** — was "unspecified in the port" | `acww_nds3d_compose_x` reads the 3D buffer through `BG0HOFS & 0x1FF` with the emulator's own wrap (a source column past 256 is DROPPED, not wrapped round), matching DeSmuME 0.9.13 `GPU.cpp` `RenderLine_Layer3D`. **melonDS does NOT do this** (`GPU2D_Soft.cpp` `DrawBG_3D` ignores `BGXPos`) — the two references disagree and the oracle is DeSmuME. MEASURED INERT: ACWW writes `BG0HOFS = 0` on both proof sets (`ACWW_REGDUMP`), 31/31 and 141/141 frames byte-identical. `ACWW_3D_HOFS=0` keeps the old arm |
| G4 | *(RENDER43, new)* `SWAP_BUFFERS` swaps the display list **immediately**, on every command [`nds3d.c` `case 0x50`, as read at `6081a9a1`] | GBATEK, [DS 3D Display Control](https://problemkaputt.de/gbatek-ds-3d-display-control.htm): *"SwapBuffers isn't executed until next VBlank (Scanline 192) (the Geometry Engine is halted for that duration)"*; DeSmuME 0.9.13 `gfx3d.cpp` — `gfx3d_glFlush` only sets `isSwapBuffers`, `gfx3d_execute3D` returns while it is set ("3d engine is locked up"), `gfx3d_VBlankSignal` does the flush | **disagreed — FIXED (F15, RENDER43)** | at most ONE swap per frame; the rest are HELD, and their geometry accumulates into the list the next frame's swap latches. This was the acre-ground dropout: 19 swaps in one frame, 18 lists discarded, the last one empty. `swaps=N held=M` is on the standing report; `ACWW_SWAP_EVERY=1` keeps the old arm |

---

## 3. The twelve notes, and what two of them actually mean

`acww_nds3d_report()` prints twelve note strings. Two are overloaded, and a reader who takes
them at face value will investigate the wrong thing (M1).

| Note text | Where it is actually raised | What it really means |
|---|---|---|
| "a texture format or blend mode that is not decoded" | `raster3d.c:354`, and **only** there: `if (mode == 1u)` | **Decal blending was requested.** `tex3d.c` decodes all seven formats and raises no note at all, so this string can never mean a texture format |
| "an unknown command id reached the parser" | `nds3d.c:3111` (default case) **and** `raster3d.c:182`, the `alpha5 == 0` arm | Either an unknown command **or a wireframe polygon was dropped** |
| "fog requested, not rendered" | `clear_buffers`, `DISP3DCNT & 0x0080` | correct — the fog **master enable**, not the per-polygon bit |
| "matrix stack over/underflow" | `mtx_stack_error` | correct |
| "BOX/POS/VEC_TEST answered without testing" | all three commands share it | correct, but does not distinguish the harmless case (`BOX_TEST`) from the two that write no result at all |

Fix: give decal, wireframe and `POS/VEC_TEST` their own bits. There are four free bits in the
note word and the report loop is a literal `12`.

---

## 4. Fix list, in priority order

Priority is set by the town and taxi scenes. Every entry names the file and function, what the
spec says, what the code does, and the frame and region that would change. The oracle frames
are `scratchpad/oracle/tap-town/shot_0NNNNN.bmp` (town, 27,000–48,000 every 1,500) and
`scratchpad/oracle/tap-fullpad/shot_0NNNNN.bmp` (taxi 6,000–24,000, town 25,500 onward); the
port side is `scratchpad/cycle40/runs/tap-D56`, already compared in
`scratchpad/oracle/tap-fullpad/compare-vs-tap-D56.txt`.

**F1 — translucent blending: skip the blend against a zero-alpha destination, and take the
maximum alpha.** `raster3d.c`, `draw_poly`, the `else` arm of `if (fa >= 255u)`.
*Spec:* blending is skipped and the source overwrites when `FrameBuf[A] = 0`; the stored alpha
is `max(Poly[A], FrameBuf[A])` [GBATEK, Toon/Edge/Fog/Alpha-Blending; melonDS `GPU3D_Soft.cpp`;
DeSmuME `rasterize.cpp`].
*Code:* blends unconditionally against the cleared buffer (alpha 0, RGB 0), so the colour is
multiplied by its own alpha, and then `acww_nds3d_compose` multiplies by that alpha again when
it lays the layer over the 2D sky. The stored alpha accumulates as an over-composite.
*Verify:* the taxi's rain and window panes, `tap-fullpad/shot_009000.bmp` against `tap-D56`
frame 9,000, upper half of the lower screen. The port's mean luminance there is already
0.7 units below the oracle's at a whole-frame NCC of 0.9958; the window region is where a
double-darkening shows. Also `tap-town/shot_037500.bmp`, the sky seen through the town's
translucent surfaces.

**F2 — W-buffered depth: normalise W per polygon and interpolate it perspective-correctly.**
`nds3d.c`, `to_screen` (the `wbuffer_mode` arm); `raster3d.c`, `draw_poly` (attribute 0).
*Spec:* "W is normalized, such that all the polygon's W values fit within 16 bits", and the
normalised W is what W-buffering uses — not the viewport transform; W-buffered depth goes
through the perspective interpolator while Z-buffered depth is linear [melonDS `GPU3D.cpp`,
`GPU3D_Soft.h` `InterpolateZ`].
*Code:* uses the raw clip `w` clamped to `0x00FFFFFF`, and interpolates it linearly across the
span in both modes. ACWW writes `SWAP_BUFFERS = 3`, so this is the mode every frame uses
[S: `src/matched/func_02002f68.c`].
*Verify:* depth ordering where the ground plane meets buildings and the taxi's dashboard meets
its window — `tap-town/shot_037500.bmp` around the town hall's base, and `tap-fullpad`
frames 9,000–15,000. The port already carries `q` per vertex, so the machinery exists.
*LANDED IN HALF, AND THE OTHER HALF IS THE FINDING.* Both changes were implemented and then
measured apart on the tap-fullpad taxi recipe (frames 9,000 / 12,000, whole-frame NCC):

| build | 9,000 | 12,000 |
|---|---|---|
| before F2/F3 | 0.9958 | 0.9957 |
| F3 only | 0.9985 | 0.9989 |
| **F3 + perspective W depth, no normalisation (the default now)** | **0.9986** | **0.9989** |
| F3 + normalisation + perspective | 0.8710 | 0.8684 |
| normalisation + perspective, no F3 | 0.8710 | 0.8685 |
| F3 + normalisation, linear interpolation | 0.8715 | 0.8690 |

E3 (perspective interpolation) is right and is on: `draw_poly` carries the depth as `z*q` and
divides by the interpolated `q`, the same interpolator the texture coordinates use, with a
per-polygon down-shift that keeps `z*q` inside a signed word. E2 (per-polygon normalisation)
is implemented in `emit_poly` and **off by default behind `ACWW_WNORM=1`**, because on its own
it costs 0.13 NCC and turns the taxi's interior 22 luminance units brighter. The mechanism is
structural, not a coding slip, and the fixture shows it: a polygon whose w is constant
normalises to exactly `0x8000` whatever its distance, so a normalised W depth is ordered
*within* a polygon and arbitrary *between* polygons — distant surfaces draw over near ones.
Either the emulator reading in E2 is wrong (the normalised W may be an interpolation-precision
device that is undone before the depth buffer) or something else must change with it. Reopen
by setting the variable; nothing needs reimplementing.

`port/tools/test_raster3d_depth.py` is the fixture, and it pins both answers: two crossing
quads whose crossing is at span `t = 0.6429` under the hardware's rule and `t = 0.5455` under
the old linear-in-w one, probed at `t = 0.6016` where the two disagree, run once per mode.

**F3 — treat A3I5 and A5I3 polygons as translucent.** `raster3d.c`, `draw_poly`, the `trans`
and `write_depth` computation, and the two passes in `acww_nds3d_raster`.
*Spec:* formats 1 and 6 are the translucent texture formats; melonDS decides translucency per
pixel from the blended alpha, and a translucent fragment neither writes depth (without bit 11)
nor blends against the same polygon ID.
*Code:* `trans = alpha5 != 31u` only. An alpha-31 polygon with an A5I3 texture is drawn in the
opaque pass and writes depth through its half-transparent texels.
*Verify:* the taxi window and rain again — the port's own `nds3d tex` one-shot names a 64×64
A5I3 material in that scene [E: `docs/log/2026-09-02.md`]. `tap-fullpad/shot_012000.bmp`.
*LANDED, AND IT IS AN IMPROVEMENT: NCC 0.9958 → 0.9985 at frame 9,000 and 0.9957 → 0.9989 at
12,000, MAE 5.76 → 4.02 and 6.17 → 4.16 (tap-fullpad, oracle `tap-fullpad`).*
`acww_poly_translucent` decides pass membership from the alpha OR the texture format,
and `draw_poly` classifies each FRAGMENT from its final alpha (`ftrans = fa < 255`, 255 being
the only expansion of 5-bit 31): a translucent fragment meets the same-ID rule and writes depth
only under `POLYGON_ATTR` bit 11, an opaque fragment of the same polygon does neither. The
same-ID test moved after texturing because that is the earliest point the class is known; the
only consequence is that `transid_rejects` now counts classified fragments. Two new counters in
`acww_nds3d_report`: `transtex=` polygons this rule moved out of the opaque pass and
`transfrag=` fragments that took the translucent rules, beside a `depth=W|Z` mode read-back.

**F4 — raise a note when a texture cannot be sampled.** `tex3d.c`, `acww_gx_texel`, every
`return 0` that follows a null `tex_addr` or `pltt_addr`.
*Spec:* n/a — this is a diagnostic gap, not a behaviour gap.
*Code:* an unmapped VRAM bank returns fully transparent and says nothing, so a hole in the
world caused by a `VRAMCNT` misread is indistinguishable from a hole the model asked for.
*Verify:* any frame; the note either fires on the town recipe or it does not, and either answer
closes a standing question about `tex_addr`'s bank table.

**F5 — answer `POS_TEST` and `VEC_TEST` for real.** `nds3d.c`, case 0x70–0x72.
*Spec:* `POS_TEST` multiplies `(x,y,z,1)` by the clip matrix and writes four words to
`POS_RESULT` `0x04000620`; `VEC_TEST` multiplies `(x,y,z,0)` by the directional matrix and
writes three halfwords to `VEC_RESULT` `0x04000630`; it overwrites the internal vertex
registers [GBATEK, DS 3D Tests].
*Code:* writes nothing; the game reads whatever the I/O page held. The port already has
`vec_mul`, `dir_mul` and `m_clip`, so this is four lines each.
*Verify:* count 0x71/0x72 submissions on the town recipe first — if the count is zero this is
free correctness with no visible change, and the open question on
`wiki/engine/graphics-pipeline.md` closes.

**F6 — texture-coordinate modes 2 and 3.** `nds3d.c`, `apply_texmtx`, the mode 2/3 tail.
*Spec:* mode 2 is `raw + (nx·m0 + ny·m4 + nz·m8) >> 21` on the **raw 10-bit** normal; mode 3 is
`raw + (x·m0 + y·m4 + z·m8) >> 24`; neither adds the matrix's fourth row [melonDS `GPU3D.cpp`].
*Code:* `vec_mul` with `v[3] = FX_ONE` includes `m[12]`/`m[13]`, and the net shift is 20 against
a normal the port has already scaled `<<3`, so both modes come out **16× too large** with a
spurious translation added.
*Verify:* count polygons with `(tex_param >> 30) & 3` in {2,3} on the town recipe — the
existing `nds3d poly-in` probe already prints `tex`. If the count is nonzero, the water and any
environment-mapped surface in `tap-town` are the region.
*LANDED, AND IT IS THE MOST VISIBLE 3D FIX SO FAR (RENDER42).* The count was taken with
`ACWW_TEXTRACE_FRAME=6000` on the OFF recipe [H: `scratchpad/cycle40/runs/off-textrace42`; receipt lost with its worktree; repeat the named recipe and retain the stated frames]:
**one** polygon of 458 uses mode 2 and none uses mode 3 — the framed picture on the taxi's
wall, texture `0x95230280`, a 32×32 format-5 material at screen x 164..195, y 6..22. The
oracle draws a landscape there and the port drew black with coloured stripes, which is what a
texture coordinate 16× too large samples out of a 32×32 image
[O: `scratchpad/oracle/off/shot_006000.bmp`]
[E: `scratchpad/render42/picture-frame-before-after.png`, oracle | before | after]. Both modes
now take three terms and shift by 24 — the same shift for both only because `cur_normal` is
the raw 10-bit value already `<< 3`, and the comment in `apply_texmtx` says so. Whole-frame on
the OFF recipe's 31 frames: mean ncc 0.9970 → 0.9974, mean ncc-top 0.9774 → 0.9807, mae
7.43 → 7.31, **no frame lost ncc**; in the picture's own box mae 45.8 → 35.9
[H: `scratchpad/cycle40/runs/off-p10` vs `off-f6`; receipt lost with its worktree; repeat the named recipe and retain the stated frames]. `ACWW_TEXMTX23_OLD=1` keeps the old arm.
Fixture: `port/tools/test_nds3d_texmtx.py` (new) — mode 0, mode 2 and mode 3 against
arithmetic written out in Python, with a texture matrix whose fourth row is large on purpose,
and a calibration that asserts the pre-F6 answer and must be caught
[S: `docs/kb/hybrid/render-fixes.md` fix F6].

**F7 — stop `gxstat_update()` clobbering `GXSTAT`.** `nds3d.c`, `gxstat_update`.
*Spec:* bits 30–31 are the only writable field; 26 is FIFO-empty; 1 is the box-test result
[GBATEK, DS 3D Status].
*Code:* writes a fresh word preserving only bit 15, so bits 26 and 30–31 are cleared on every
matrix command and the box-test answer is destroyed by any matrix command between the test and
the poll.
*Verify:* set bit 26 alongside 25 and preserve bits 0–1 and 30–31; grep the matched sources for
`0x04000600` readers first. `port/shim/gfx/g3x_fifo.c` already records that bit 27 being zero is
what makes the ROM's spin terminate — the same argument says bit 26 must be **one**.

**F8 — the suspected one-row viewport offset.** `nds3d.c`, `to_screen`, the `o->y` expression.
*Spec:* viewport coordinates originate at the **lower left**, so the row from the top is
`191 − [(y+w)·vh/(2w) + y1]` [GBATEK, DS 3D Display Control, VIEWPORT].
*Code:* `(191 − y2)·16 + (w − y)·vh·16/(2w)` with `vh = y2 − y1 + 1`, which reduces to
`192 − y1 − t·vh`.
*Verify:* the horizon row in `tap-town/shot_037500.bmp` against `tap-D56` frame 37,500. A
one-row shift is invisible to a human and obvious to a row-difference histogram. Do not change
it on the algebra alone — `wiki/STYLE.md` rule 7 applies until the oracle answers.
*THE ORACLE HAS ANSWERED, AND IT IS BOTH AXES, NOT ONE ROW (RENDER42).*
`scratchpad/render42/shiftfit.py` fits a sub-pixel translation per quadrant. On the taxi's top
screen the best fit is the SAME in all four quadrants — a translation, not a scale — at
dx = **+1.00 px** and dy = +1.00..+2.00, moving mae 15.08 → 7.03 at OFF frame 6,000 and
12.23 → 7.74 at 9,000; the 2D bottom screen fits at (0, 0), so the offset belongs to the 3D
layer alone. The algebra in this row is NOT the cause: with ACWW's full-screen viewport
(y1 = 0, y2 = 191) `(191 − y2)` and `y1` are both 0, so the two expressions agree. The
suspect is the fill rule's sample point instead — see F9 — and the direction matches
(a centre sample puts a feature half a pixel further left and up than an integer sample).
`ACWW_3DBIAS_X`/`_Y` translate the geometry in sixteenths of a pixel FOR MEASUREMENT ONLY:
+0.5 px moves mean mae 7.66 → 6.92 and ncc-top 0.9787 → 0.9824 over OFF frames 4,500..6,000,
but LOSES whole-frame ncc on 2 of 11 frames, so it is rejected as a fix — a translation is
not a rule [H: `scratchpad/cycle40/runs/off-bias4040`, `off-bias4848`;
S: `docs/kb/hybrid/render-fidelity-history.md` section 4; receipt lost with its worktree; repeat the named recipe and retain the stated frames].

**F9 — fill the edges, and render 1-dot polygons.** `raster3d.c`, `draw_poly`; `nds3d.c`,
`emit_poly` (the `area == 0` arm).
*Spec:* the DS fills edge pixels by slope rules, and "edges are always filled if
antialiasing/edgemarking are enabled, if the pixels are translucent and alpha blending is
enabled, or if the polygon is wireframe" — ACWW has AA on, so its edges are always filled
[melonDS `GPU3D_Soft.cpp`]. A polygon that collapses to one pixel is drawn from its first
vertex when `POLYGON_ATTR` bit 13 is set and any W is within `DISP_1DOT_DEPTH` `0x04000610`.
*Code:* a pixel-centre sample rule, so any polygon that misses the centre disappears; zero-area
polygons are dropped into the `degenerate` counter.
*Verify:* the port already counts `degenerate` separately from `culled` and its own comment
records that the dropped triangles are not truly flat, only flat after 12.4 truncation. Read the
`degenerate` figure on the town recipe first; if it is large, distant town detail in
`tap-town/shot_027000.bmp` is the region.
*THE SAMPLE POINT IS NOW A VARIABLE, AND IT IS THE F8 SUSPECT (RENDER42).* `draw_poly` carries
`soff`, the sample point inside a pixel in sixteenths, and every consumer — the scanline's Y,
the row range, the span's first and last column, the span parameter's numerator — is expressed
against it, so the two arms cannot drift apart. `ACWW_SAMPLE_INT=1` selects the integer sample
point both emulators use; the default is unchanged at 8 (the centre). This is the RULE that
F8's measured translation is a proxy for, and it MOVES THE MOST of anything measured in
RENDER42 — over the OFF recipe's 31 frames, mean ncc 0.9974 → 0.9976, mean ncc-top
0.9807 → **0.9833**, mean mae 7.31 → **6.66** — but it LOSES whole-frame ncc on **9 of the 31
frames** (worst −0.0007), so it is REJECTED as a default by the frontier rule and left
implemented and off [H: `scratchpad/cycle40/runs/off-final` vs `off-sampleint`; receipt lost with its worktree; repeat the named recipe and retain the stated frames]. There is a
reading of the loss that says it should be there: the emulators also quantise the VERTEX
position to a whole pixel before rasterising, and this arm changes only the sample point —
half of a pair. The other half, measured the same way, is the next experiment. The edge-fill
and 1-dot halves of F9 are still open.

**F10 — fog.** `raster3d.c`, a post-pass over `colour[]` and `depth[]` before compose.
*Spec:* fully documented in §2 F-fog; the port already holds the depth buffer and would need
one per-pixel fog flag, seeded from `CLEAR_COLOR` bit 15 (which ACWW sets) and replaced by
`POLYGON_ATTR` bit 15 on opaque writes, ANDed on translucent ones.
*Code:* absent; a note fires when `DISP3DCNT` bit 7 is set.
*Verify:* first establish whether bit 7 is ever set — the report already prints `DISP3DCNT`
every frame. `func_02002f68` does not set it, and no caller of `G3X_SetFog` is in
`src/matched/`. If it is never set, downgrade this to a closed hypothesis; if it is, the taxi's
rain haze in `tap-fullpad/shot_009000.bmp` is the region.

**F11 — the clear polygon ID and the per-pixel attribute buffer.** `raster3d.c`,
`clear_buffers` and `draw_poly`.
*Spec:* the rear plane seeds colour, alpha, depth, polygon ID and the fog flag per pixel;
translucent writes preserve the **opaque** polygon ID, which is why edge marking survives a
translucent overlay [melonDS `GPU3D_Soft.cpp` `ClearBuffers`].
*Code:* `tattr[]` carries only the translucent ID. Prerequisite for fog (F10), edge marking and
anti-aliasing; on its own it changes nothing visible.

**F12 — split the overloaded notes.** `nds3d.h` (`GX_NOTE_*`), `raster3d.c`
(`note_text[12]` and the `for (i = 0; i < 12; i++)` loop).
*Spec:* n/a. *Code:* see §3. *Verify:* the self-test already runs with notes visible.

**F13 — small, cheap, no visible change:** `ALPHA_TEST_REF` (E11); the ±0xFF depth-equal
tolerance in W mode (E4); `RAM_COUNT` and the `DISP3DCNT` bit 13 overflow flag (A12); the
`MTX_STORE` slot-31 error (A7); a note when `SWAP_BUFFERS` bit 0 asks for auto-sort (E12).

**F14 — the 3D layer is scrolled by BG0HOFS (G3). LANDED, RENDER43.** `raster3d.c`
(`acww_nds3d_compose_x`), `nds2d.c` (`compose_hofs`). *Spec:* GBATEK,
[DS 3D Final 2D Output](https://problemkaputt.de/gbatek-ds-3d-final-2d-output.htm) — a 512-pixel
scroll region, 256 of image then 256 transparent, wrapping; no vertical scroll, no rotation.
*Code, before:* composed at x = 0 unconditionally. *Now:* reads the 3D buffer through
`BG0HOFS & 0x1FF`, with the emulator's own wrap — a source column past the image is DROPPED, not
wrapped round (DeSmuME 0.9.13 `GPU.cpp`, `RenderLine_Layer3D`). melonDS does not implement this
at all. *Verified:* MEASURED INERT — ACWW writes `BG0HOFS = 0` on both proof sets, so 31/31 and
141/141 frames are byte-identical. A documented gap closed, not a fidelity gain.
`ACWW_3D_HOFS=0` keeps the old arm.

**F15 — one SWAP_BUFFERS per frame; hold the rest (G4). LANDED, RENDER43, and it is the
acre-ground dropout.** `nds3d.c`, `case 0x50`. *Spec:* GBATEK, DS 3D Display Control — *"SwapBuffers
isn't executed until next VBlank (Scanline 192) (the Geometry Engine is halted for that
duration)"*; DeSmuME 0.9.13 `gfx3d.cpp` implements the stall literally. *Code, before:* swapped
on every command, so a host frame carrying several logical frames' GX work latched and discarded
several display lists. *Measured:* at the failure's edge, `swaps` goes 1 → **19** and the list
goes 385 polys → **0**, with VRAMCNT, DISP3DCNT, CLEAR_COLOR, CLEAR_DEPTH and VIEWPORT all
unchanged [E: `scratchpad/render43/gxwatch-58700-58790.txt`]. *Now:* at most one swap per frame;
the geometry after a held swap accumulates into the list the next frame's swap latches.
`swaps=N held=M` is on the standing report; `ACWW_SWAP_EVERY=1` keeps the old arm.

---

## 5. Hypotheses

- **H1 — `VTX_DIFF`: the port and the oracle cannot both be right.** GBATEK and DeSmuME make the
  10-bit delta a 1.0.9 fraction that enters a 1.3.12 coordinate shifted left by three; the port
  adds it raw, after removing exactly that shift on `8a7fdb5f` because an offline reconstruction
  of `npc/model/48/49.nsbmd` matched the model's declared bounding box at shift 0 and exceeded it
  at shift 3 [E: `docs/log/2026-09-02.md`]. The oracle **is** DeSmuME, and its villagers are
  correct; the port's villagers are also correct. One of the two measurements is wrong, or
  something else in the port absorbs a factor of eight. *Experiment:* compare a villager's limb
  proportions between `scratchpad/oracle/tap-town/shot_037500.bmp` and `tap-D56` at the same
  frame, then re-run the port with the shift restored and see which direction moves toward the
  oracle. Until then both readings stand on the page (`wiki/STYLE.md` rule 7).
- **H2 — the town's top screen is blank in the port from frame 25,500 onward.**
  `scratchpad/oracle/tap-fullpad/compare-vs-tap-D56.txt` reports `ncc-top` of 0.96–1.00 through
  frame 24,000 and **0.0000** from 25,500, with the port's whole-frame mean luminance halving
  from ~130 to ~66. A top-screen NCC of exactly zero is a flat image. That is consistent with the
  known black upper LCD [E: `docs/log/2026-09-04.md`] and is a 2D/`POWCNT1` question, not a 3D
  one — **do not attribute it to any fix on this page** until the top screen has content.
- **H3 — fog is never enabled in ACWW.** `func_02002f68` clears `DISP3DCNT` bit 7 and no caller
  of `G3X_SetFog` appears in `src/matched/`, yet `G3X_SetClearColor` is called with `fog = TRUE`,
  which only matters if the master enable is on. *Experiment:* the per-frame report already
  prints `DISP3DCNT`; read bit 7 across the town and taxi recipes.
- **H4 — modes 2 and 3 of the texture-coordinate transform are unused.** ~~The port has never
  seen them exercised and says so.~~ **SETTLED, and FALSE (RENDER42).** The histogram was taken:
  **one** polygon of 458 at OFF frame 6,000 uses mode 2 (none uses mode 3), and it is a visible
  one -- the framed picture on the taxi's wall, which drew stripes and now draws the landscape.
  So F6 was a fix and not free correctness. The town recipe has not been histogrammed
  [E: `off-textrace42`; the F6 row above].
- **H5 — the port's extra accuracy is a liability for the oracle comparison.** 8-bit colour
  channels (C7), full-precision perspective interpolation (E15) and a 64-bit divide (B11) all
  make the port *more* accurate than the DS. No frame will ever be byte-equal to the oracle, so
  the audit method must stay structural (NCC, region masks) rather than exact.

## 6. Related

- `../engine/graphics-pipeline.md` — the resource path, the registers and the VRAM banks.
- `../data/archives.md` — the `nsbmd`/`nsbtx` containers these textures arrive in.
- `hardware-services.md` — the same method applied to the rest of the port's hardware.
- `port/render/selftest3d.c` — the existing checks. It covers parameter counts, the packed
  encoding, vertex formats, matrices, winding, clipping, wrapping, I4 and 4x4 texture decode,
  depth ordering and one composition case. `port/tools/test_raster3d_depth.py` now covers
  W-buffered depth and the normalisation question (54 checks). **Neither has a check for** fog,
  edge marking, toon, the translucent-ID rule, the depth-equal test, wireframe, 1-dot polygons,
  `POS_TEST`/`VEC_TEST`, `GXSTAT` preservation, A3I5/A5I3 alpha, or direct colour — which is the
  same list as §4, and is where a fix's regression test belongs.
