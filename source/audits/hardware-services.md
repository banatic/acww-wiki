# Audit: hardware services against the public record

**Summary.** Every hardware service the port supplies under the ROM — the ARM7 stand-in, DMA,
the divider/sqrt unit, the display counters, the 2D effects unit, the geometry engine and the
BIOS — was checked against GBATEK, the public NitroSDK source mirror and emulator source.
Thirty-one claims were checked. Twenty-two agree with the public record, six disagree, three
are unspecified. The six disagreements are small, local and each has a named fix; two of them
(CpuFastSet's rounding and the VBlank flag on line 262) are outright wrong against a quoted
spec sentence, and one (the stylus latency) is the port's largest measured divergence from the
original and is a design choice rather than a bug. No decompilation of Animal Crossing exists
publicly; a full NitroSDK and NitroSystem source tree does, and it can name a large fraction of
what this repo still calls `func_XXXXXXXX`.

**Method.** Read at commit `470df4ac`. Public sources were fetched, not remembered; each row
below names the URL and the heading on that page. No code was copied from any source. The game
was not run. One claim (the BIOS CRC16) was checked by re-implementing all three candidate
algorithms and comparing them numerically, which overturned the finding this audit was about to
publish — see row B4 and M1.

---

## 1. Claims table

Verdict is **agrees** / **disagrees** / **unspecified** (the public record does not settle it).
"Port" names the file and function the claim lives in.

### A. Stylus sampling and the TSC conversion

| # | Claim as the port/wiki states it | Public source | Verdict | What to change |
|---|---|---|---|---|
| A1 | The touch panel is an SPI device the ARM7 polls; a sample is a 12-bit ADC count, X on channel 5 and Y on channel 1 [`wiki/systems/input-and-touch.md`, "The stylus"] | GBATEK, [DS Touch Screen Controller (TSC)](https://problemkaputt.de/gbatek-ds-touch-screen-controller-tsc.htm), sections "Control Byte" and "Channels" | agrees | nothing |
| A2 | Calibration is a two-point linear map from ADC counts to pixels | GBATEK, same page, "Converting ADC Position to Screen Position": `scr.x = (adc.x-adc.x1) * (scr.x2-scr.x1) / (adc.x2-adc.x1) + (scr.x1-1)` | agrees | nothing — but note the **`-1`** term; the round trip pixel→ADC→pixel is not the identity, which is the documented reason a tap comes back one pixel off |
| A3 | The one-pixel offset measured on the oracle (221,181 in → 222,182 out) is an artefact of the emulator converting pixels to ADC counts and `TP_GetCalibratedPoint` converting back [`input-and-touch.md`, "The port and the original disagree"] | melonDS [`src/SPI.cpp`](https://github.com/melonDS-emu/melonDS/blob/master/src/SPI.cpp), TSC `SetTouchCoords`: the host coordinates are stored as `TouchX <<= 4`, i.e. pixel×16, with no calibration inverse at all | agrees, with a correction | The emulator does **not** invert the firmware calibration — it multiplies by 16. The ±1 therefore comes from `TP_GetCalibratedPoint`'s own reciprocal-and-shift against a calibration that does not have slope exactly 16. Say so on the wiki page instead of "converts screen pixels to raw ADC counts" |
| A4 | The original delivers a tap 1–2 frames later than the port, and holds it one frame longer [`input-and-touch.md`; ORACLE42] | melonDS `src/SPI.cpp`: "no delay between setting touch coordinates and ARM7 readability" — the emulator adds none | agrees, and the cause is now named | The latency is **entirely the ROM's own ARM7 + PXI + `func_020e9314` chain**, not emulator lag. That makes it reproducible in the port. See fix **P1** |
| A5 | ACWW runs a nine-entry ring at "a sampling period of 4" [`input-and-touch.md`, "The stylus"] | NitroSDK, [`include/nitro/spi/ARM9/tp.h`](https://github.com/ntrtwl/NitroSDK/blob/main/include/nitro/spi/ARM9/tp.h): `TP_RequestAutoSamplingStartAsync(u16 vcount, u16 frequence, TPData bufs[], u16 bufSize)` with `TP_SAMPLING_FREQUENCY_MAX` | unspecified (header carries no comment) | The second argument is `frequence`, not a period. With 16 the documented maximum and ACWW passing 4, the natural reading is **four samples per frame**, which makes the nine-entry ring 2.25 frames deep and makes `func_020e9314`'s "last four entries" exactly one frame's worth. Reword the page and mark it H until the ARM7 side is read |
| A6 | `validity` is an error code and 0 means the sample is good | NitroSDK `tp.h`: `TP_VALIDITY_VALID`, `TP_VALIDITY_INVALID_X`, `_INVALID_Y`, `_INVALID_XY` | agrees | nothing |
| A7 | `TPCalibrateParam` is an origin plus a per-axis dot size | NitroSDK `tp.h`: `struct NvTpData { s16 x0, y0, xDotSize, yDotSize; }` | agrees | nothing |

### B. The BIOS SWI list

| # | Claim | Public source | Verdict | What to change |
|---|---|---|---|---|
| B1 | The interpreter's SWI numbering is the NDS one: 09h Div, 0Bh CpuSet, 0Ch CpuFastSet, 0Dh Sqrt, 0Eh GetCRC16, 0Fh IsDebugger, 10h BitUnPack, 11h LZ77, 14h RL, 16h/18h Diff filters [`port/interp/interp_bios.c` header] | GBATEK, [BIOS Function Summary](https://problemkaputt.de/gbatek-bios-function-summary.htm) | agrees | nothing. The header's warning that NDS numbering differs from GBA's is correct and worth keeping |
| B2 | 16h and 18h are the Diff filters and 17h does not exist on NDS | GBATEK, [BIOS Decompression Functions](https://problemkaputt.de/gbatek-bios-decompression-functions.htm): 16h is `(GBA/NDS9/DSi9)`, 17h is `(GBA)` only, 18h is `(GBA/NDS9/DSi9)` | agrees | nothing — the port is right to omit 17h |
| B3 | `CpuFastSet` rounds the word count up to a multiple of 8 [`interp_bios.c` case 0x0c: `n2 = ((ctl & 0x1fffff) + 7) & ~7`] | GBATEK, [BIOS Memory Copy](https://problemkaputt.de/gbatek-bios-memory-copy.htm), "SWI 0Ch — CpuFastSet": *"On the GBA, the length should be a multiple of 8 words (32 bytes) (otherwise the GBA is forcefully rounding-up the length). On NDS/DSi, the length may be any number of words (4 bytes)."* | **disagrees** | Fix **P4**: copy exactly `ctl & 0x1FFFFF` words. The rounding is GBA behaviour and writes up to seven words past the destination |
| B4 | The `GetCRC16` table is used as `crc ^= tab[j] << (7-j)` on a register-width accumulator | GBATEK, [BIOS Misc Functions](https://problemkaputt.de/gbatek-bios-misc-functions.htm), "SWI 0Eh — GetCRC16"; DeSmuME `src/bios.cpp` (`getCRC16`, nibble-table form) | agrees | nothing. **This audit nearly published the opposite.** The un-masked 32-bit accumulator looks wrong; re-implementing GBATEK's pseudo-code, the classic CRC-16/ARC and the port's exact expression and running all three showed the port equals CRC-16/ARC on every input tried, and it is the *masked* reading that diverges. M1 |
| B5 | `GetCRC16` takes a byte length | GBATEK, same section: r1 must be 2-byte aligned and r2 is *"length in bytes, must be 2-byte aligned"*; DeSmuME computes `size = R[2] >> 1` and iterates halfwords | **disagrees**, narrowly | The port loops over all `len` bytes; hardware drops a trailing odd byte. Fix **P8** (one line). DeSmuME also returns the last halfword in R3, which the port does not model |
| B6 | `CpuSet`'s control word is a 21-bit count, bit 24 fixed-source, bit 26 datasize | GBATEK, [BIOS Memory Copy](https://problemkaputt.de/gbatek-bios-memory-copy.htm), "SWI 0Bh — CpuSet" | agrees | nothing |
| B7 | `BitUnPack`'s info block is `u16 len; u8 srcWidth; u8 dstWidth; u32 offset` with bit 31 the zero-data flag, the offset added to non-zero units always and to zero units only when the flag is set | GBATEK, [BIOS Decompression Functions](https://problemkaputt.de/gbatek-bios-decompression-functions.htm), "BitUnPack — SWI 10h" | agrees | nothing |
| B8 | `IsDebugger` returning 0 is correct | GBATEK, [BIOS Misc Functions](https://problemkaputt.de/gbatek-bios-misc-functions.htm): it reports 4 MB (normal) vs 8 MB (debug) main RAM | agrees | nothing |
| B9 | Any SWI not listed stops the run by name rather than being guessed | — | agrees (policy, not spec) | The NDS9 SWIs the port does **not** implement are 00h SoftReset, 12h `LZ77UnCompReadByCallbackWrite16bit`, 13h `HuffUnCompReadByCallback`, 15h `RLUnCompReadByCallbackWrite16bit` and 1Fh `CustomPost`. NitroSDK's `MI_UncompressHuffman` is SWI 13h and its VRAM-safe decompressors are 12h/15h, so these are the likely next stops. Fix **P6** pre-empts them |

### C. DMA

| # | Claim | Public source | Verdict | What to change |
|---|---|---|---|---|
| C1 | The NDS9 DMA word count is 21 bits, `0 = 0x200000` [`dma.c` `dma_raw`] | GBATEK, [DS DMA Transfers](https://problemkaputt.de/gbatek-ds-dma-transfers.htm): *"Word count of all channels is expanded to 21bits (max 1..1FFFFFh units, or 0=200000h units)"* | agrees | nothing |
| C2 | `DMAxCNT` bits 21–22 destination step, 23–24 source step, 25 repeat, 26 width, **27–28 start timing**, 30 IRQ, 31 enable [`dma.c` comment above `dma_raw`] | GBATEK, same page: on NDS9 *"the gamepak bit (Bit 27) has been removed and is instead used to expand the mode setting to 3bits"* — timing is **bits 27–29** on NDS9 (bits 28–29 on NDS7) | **disagrees** (comment only) | Fix **P5**: correct the comment to 27–29 and list the seven NDS9 modes. The code ignores the field entirely so no behaviour changes, but the wrong comment will mislead the next reader — and D12 is exactly this class of defect |
| C3 | Start timing 7 is the Geometry Command FIFO | GBATEK, same page: *"0 Start Immediately, 1 Start at V-Blank, 2 Start at H-Blank (paused during V-Blank), 3 Synchronize to start of display, 4 Main memory display, 5 DS Cartridge Slot, 6 GBA Cartridge Slot, 7 Geometry Command FIFO"* | agrees | nothing |
| C4 | A GX-FIFO-destined transfer is recognised and routed to the FIFO parser [`dma.c:409`] | GBATEK, [DS 3D Geometry Commands](https://problemkaputt.de/gbatek-ds-3d-geometry-commands.htm): *"DMA starts when the FIFO becomes less than half full, the DMA does then write 112 words to the GXFIFO register (or less, if the remaining DMA transfer length gets zero)"* | agrees on the destination, **unspecified** on the burst | The port runs the whole transfer in one go rather than in 112-word bursts. That is invisible to a caller that waits for completion, which every NitroSDK GX path does. It is only visible to code that reads GXSTAT mid-transfer. Record it as a deliberate difference rather than leaving it unstated |
| C5 | The FIFO route is detected by destination address, not by the timing field | GBATEK, same | agrees, and is more robust | nothing — but say so, because the timing field is the spec's own selector and someone will "fix" the code to use it |
| C6 | Widths are not collapsed into one loop; a byte write to VRAM/OAM is illegal | GBATEK, [DS Memory Maps](https://problemkaputt.de/gbatek-ds-memory-maps.htm) (VRAM/OAM 16-bit bus) | agrees | nothing |
| C7 | Destination step mode 3 is "increment + reload" [`dma.c` comment] | GBATEK, same DMA page | agrees on the name; the port treats 3 as plain increment and never reloads | unspecified in effect | Only matters with repeat (bit 25), which the port also ignores. Fix **P5** notes it; no caller seen |
| C8 | `MI_DmaCopy32`/`MI_DmaCopy16`/`MI_DmaFill32` are safe stand-ins for the DMA family | — | **disagrees** (latent) | Only `dma_raw` checks for a GX-FIFO destination. `MI_DmaCopy32` to `0x04000400` would walk the destination pointer across the FIFO and the 45 individual command ports, silently scrambling a display list. Fix **P3** |
| C9 | Doing the work synchronously makes `MI_WaitDma` a no-op and is observably identical | — | agrees | nothing. The argument in `dma.c`'s header is sound: every ROM wrapper waits before returning |

### D. The divider and square-root unit

| # | Claim | Public source | Verdict | What to change |
|---|---|---|---|---|
| D1 | `DIVCNT` bits 0–1 select 32/32, 64/32, 64/64 | GBATEK, [DS Maths](https://www.problemkaputt.de/gbatek-ds-maths.htm), "Division": mode 0 *"32bit / 32bit = 32bit , 32bit ; 18 clks"*, mode 1 *"64bit / 32bit"*, mode 2 *"64bit / 64bit"* | agrees | nothing |
| D2 | Divide by zero gives remainder = numerator and result ±1 by the numerator's sign | GBATEK, same page, "Division Overflows": *"REMAIN=NUMER, RESULT=+/-1 (with sign opposite of NUMER)"* | agrees | nothing — the port's `num < 0 ? 1 : -1` looks inverted and is not: the spec says *opposite* sign |
| D3 | `INT64_MIN / -1` gives `INT64_MIN`, remainder 0 | GBATEK, same: *"RESULT=-MAX (instead +MAX)"* | agrees on the result, **unspecified** on the remainder | Leave as is; note that the spec does not state the remainder |
| D4 | Reading `DIVCNT` returns the stored value masked to `0x3fff` — never busy [`interp_boot.c` `io_load`] | GBATEK, same: bit 14 is the **divide-by-zero flag**, bit 15 the busy flag | **disagrees** | The mask clears bit 14 as well as bit 15, so a caller that tests the DIV0 flag always reads "no division by zero". Fix **P7**. GBATEK adds that the flag is set *"only if the full 64bit DIV_DENOM value is zero, even in 32bit mode"*, which the port's mode-0 path (low word only) would also have to honour |
| D5 | `SQRTCNT` bit 0 selects a 64-bit parameter; `SQRT_PARAM` is at `0x040002B8` and `SQRT_RESULT` at `0x040002B4` | GBATEK, same page, "Square Root" | agrees | nothing |
| D6 | The busy bit never setting is safe because the port is synchronous | GBATEK: 18/34 clocks for divide, *"Execution time is 13 clks, in either Mode"* for sqrt | agrees | nothing. GBATEK's warning to *"push all DIV/SQRT values … when using DIV/SQRT registers on interrupt level"* is already honoured structurally: `CPContext` is part of `OSContext` [`wiki/engine/threads-and-interrupts.md`] |
| D7 | Computing on the read of a result register is equivalent to computing on the write of an operand | GBATEK: *"Division is started when writing to any of the DIVCNT/NUMER/DENOM registers"* | agrees in effect | A caller that writes NUMER, reads RESULT, then writes DENOM would differ. No such caller is known; add it as a hypothesis rather than a fix |

### E. DISPSTAT and VCOUNT

| # | Claim | Public source | Verdict | What to change |
|---|---|---|---|---|
| E1 | 263 scanlines a frame | GBATEK, [DS Video Stuff](http://problemkaputt.de/gbatek-ds-video-stuff.htm), "Display Timings": *"V-Timing: 192 lines visible, 71 lines blanking, 263 lines total (59.8261 Hz)"* | agrees | nothing |
| E2 | VBlank (DISPSTAT bit 0) is set on lines **192..262** [`interp_boot.c` `dispstat_load`: `v >= 192`; `hardware-services.md` section 4; `threads-and-interrupts.md`] | GBATEK, same section: *"the VBlank flag isn't set in the last line (ie. only in lines 192..261, but not in line 262)"* | **disagrees** | Fix **P2**. One line of code, three documents |
| E3 | VCOUNT is 9 bits, 0..262, and DISPSTAT's compare value is split | GBATEK, same: *"LY = VCOUNT Bit 0..8, and LYC=DISPSTAT Bit8..15,7"* | agrees | nothing — the port's `0xfff8` mask correctly preserves bits 3..15, which includes LYC bit 8 at DISPSTAT bit 7 |
| E4 | The V-counter match flag is DISPSTAT bit 2 | GBATEK, [LCD I/O Interrupts and Status](http://problemkaputt.de/gbatek-lcd-i-o-interrupts-and-status.htm): *"Bit 2: V-Counter flag (Read only) (1=Match) (set in selected line)"* | **disagrees** | The port never sets bit 2. A loop polling for a V-count match spins forever, and because the frame boundary fires on wrap it would spin *while frames advance* — the worst diagnostic shape this port has. Fix **P2** covers it |
| E5 | HBlank (bit 1) is left clear | GBATEK, same: *"Bit 1: H-Blank flag (Read only) (1=HBlank) (toggled in all lines)"* | **disagrees**, deliberately | Same fix; at minimum the service should *name itself* if a read of DISPSTAT is followed by another read of DISPSTAT with no line change, rather than hanging silently |
| E6 | A VCOUNT-polling loop releases within one synthetic frame, in the hardware's order | — | agrees | nothing. The one-line-per-read model is a sound answer to `func_0200149c` |
| E7 | Every I/O read is routed through the synthesis hook | `port/interp/interp_cpu.c:59-82` | **disagrees** (latent) | `ld8` does not call `io_word`. A byte read of `0x04000006` (VCOUNT low) or of a divider result register bypasses the hook and returns stale page memory. Fix **P9** |

### F. 2D colour effects and affine backgrounds

| # | Claim | Public source | Verdict | What to change |
|---|---|---|---|---|
| F1 | Alpha blend is `I = min(31, I1*EVA/16 + I2*EVB/16)` and EVA/EVB above 16 clamp to 16 | GBATEK, [LCD I/O Color Special Effects](https://problemkaputt.de/gbatek-lcd-i-o-color-special-effects.htm): *"I = MIN ( 31, I1st\*EVA + I2nd\*EVB )"*, coefficients *"0..16 = 0/16..16/16, 17..31=16/16"* | agrees on the rule, **disagrees** on the domain | The port blends 8-bit expanded channels and clamps at 255 [`nds2d.c` `chan_mix`]; hardware blends **5-bit** intensities and clamps at 31. Fix **P10** |
| F2 | Brightness increase is `I + (31-I)*EVY/16` and decrease is `I - I*EVY/16` | GBATEK, same page | agrees on the rule, same domain disagreement | Fix **P10** |
| F3 | A semi-transparent OBJ (attr0 mode 1) is always a first target and always uses alpha blending | GBATEK, same page: *"OBJs that are defined as 'Semi-Transparent' in OAM memory are always selected as 1st Target (regardless of BLDCNT Bit 4), and are always using Alpha Blending mode (regardless of BLDCNT Bit 6-7)"* | agrees on the first half, **disagrees** on the second | `apply_color_effects`' third branch can apply *brightness* to a semi-transparent OBJ when the layer below is not a second target and OBJ happens to be a BLDCNT first target. GBATEK's "regardless of Bit 6-7" says it should not. Emulators differ here. Fix **P11**, low priority |
| F4 | The blend consumes the visible pixel and the one directly below it | GBATEK, same page (the first/second target pair) | agrees | nothing. The two-deep owner record in `nds2d.c` is the right shape |
| F5 | The backdrop is inert as a first target for alpha | — | agrees by construction | nothing |
| F6 | Affine BG matrix entries PA..PD are signed 8.8 | GBATEK, [LCD I/O BG Rotation/Scaling](https://problemkaputt.de/gbatek-lcd-i-o-bg-rotation-scaling.htm): *"Bit 0-7 Fractional portion (8 bits); Bit 8-14 Integer portion (7 bits); Bit 15 Sign"* | agrees | nothing |
| F7 | The reference point is 20.8 with the sign in bit 27 [`nds2d.c:770`; `wiki/engine/graphics-pipeline.md`] | GBATEK, same page: *"Bit 0-7 Fractional (8); Bit 8-26 Integer portion (19 bits); Bit 27 Sign; Bit 28-31 Not used"* | agrees, wording aside | The field is **19.8 plus sign**, i.e. 28 bits signed — which is exactly what `sext(v, 28)` does. Correct the "20.8" wording on the graphics page to "28-bit signed, 8 fractional bits" |
| F8 | Per-scanline the layer is sampled at `ref + PB*y` (row) and `+PA*x` (column) [`draw_affine_bg`] | GBATEK, same page: *"The above reference points are automatically copied to internal registers during each vblank … The internal registers are then incremented by dmx and dmy after each scanline"* | agrees | nothing. `x0 + pb*y` is algebraically the accumulation, exactly, as long as the game does not write BGxX mid-frame |
| F9 | A mid-frame write to BGxX is not modelled | GBATEK, same page: *"Writing to a reference point register by software outside of the Vblank period does immediately copy the new value to the corresponding internal register … the new value specifies the origin of the &lt;current&gt; scanline"* | agrees (stated as a known limit) | Keep as a hypothesis with the instrument named: see H2 |
| F10 | Affine layers are always 8bpp with byte screen entries, square 128..1024, wrap on BGnCNT bit 13 | GBATEK, same page and [LCD I/O BG Control](https://problemkaputt.de/gbatek-lcd-i-o-bg-control.htm) | agrees | nothing |
| F11 | The BG-mode-to-layer-kind table (mode 1 → BG3 affine, mode 2 → BG2/BG3 affine, mode 4 → BG2 affine BG3 extended, mode 6 → BG0 3D + BG2 large bitmap) | GBATEK, [DS Video BG Modes](https://problemkaputt.de/gbatek-ds-video-bg-modes.htm) | agrees | nothing — `bg_kind` is correct row for row |

### G. The geometry engine

| # | Claim | Public source | Verdict | What to change |
|---|---|---|---|---|
| G1 | GXSTAT bits 8–12 are the position/vector matrix stack level and bit 15 the stack error | GBATEK, [DS 3D Status](https://problemkaputt.de/gbatek-ds-3d-status.htm): *"8-12 Position & Vector Matrix Stack Level (0..31) (lower 5bit of 6bit value)"*, *"15 Matrix Stack Overflow/Underflow Error"* | agrees | nothing |
| G2 | Bit 13 is the projection stack level | Same page (the fetched table omits it); the ROM's own `G3X_GetMtxStackLevelPJ` masks `0x2000` [`src/matched/G3X_GetMtxStackLevelPJ.c`] | unspecified in the source, settled by the ROM | nothing |
| G3 | Bit 25 is "command FIFO empty" [`nds3d.c:217` comment; `gxstat_update` sets bit 25] | GBATEK, same page: *"25 Command FIFO Less Than Half Full"*, *"26 Command FIFO Empty"* | **disagrees** | Fix **P12**: the port sets bit 25 and never bit 26, so a wait-for-empty loop reads "not empty" forever while a wait-for-half-empty loop passes. Set both, and correct the comment |
| G4 | Bit 27 is geometry-engine busy and 0 is honest for a synchronous engine | GBATEK, same page: *"27 Geometry Engine Busy"* | agrees | nothing |
| G5 | `gxstat_update` preserves the parts of GXSTAT it does not own | GBATEK, same page: *"30-31 Command FIFO IRQ (0=Never, 1=Less than half full, 2=Empty, 3=Reserved)"*; `NNS_G3dInit` writes that field [`src/matched/NNS_G3dInit.c`] | **disagrees** | `gxstat_update` rebuilds the word keeping only bit 15, so every matrix command erases the FIFO-IRQ mode the ROM installed at init, and bit 0. Fix **P12** |
| G6 | GXSTAT bit 0 is the test-busy flag and bit 1 the box-test result | GBATEK, same page: *"0 BoxTest,PositionTest,VectorTest Busy"* | agrees on bit 0; bit 1 is not in the fetched table but is the standard box-test result | agrees / unspecified | nothing; answering "visible" is the safe direction and is already argued in the file |
| G7 | POS_TEST and VEC_TEST are stubbed | GBATEK, [DS 3D Tests](https://problemkaputt.de/gbatek-ds-3d-tests.htm) (`POS_RESULT` 4000620h, `VEC_RESULT` 4000630h) | **disagrees**, known | The port clears the busy bit but writes no result registers, so a caller reads stale words. Already a hypothesis on `graphics-pipeline.md`; keep it there, and add the counting instrument named in that page |
| G8 | The FIFO at `0x04000400` takes packed command lists and `0x04000440`+ the individual ports | GBATEK, [DS 3D Geometry Commands](https://problemkaputt.de/gbatek-ds-3d-geometry-commands.htm): *"command1,2,3,4 packed into one 32bit value"*; for the ports, *"For a command with N parameters: issue N writes … For a command without parameters: issue one dummy-write"* | agrees | nothing |

### H. The PXI FIFO protocol

| # | Claim | Public source | Verdict | What to change |
|---|---|---|---|---|
| H1 | The IPC FIFO is 16 words deep each way | GBATEK, [DS Inter Process Communication (IPC)](https://problemkaputt.de/gbatek-ds-inter-process-communication-ipc.htm): *"max 16 words; 64bytes"* | agrees | nothing; the port's 16-slot reply queue matches by luck, and should say so |
| H2 | A sender retries while the FIFO is full (`RtcSendPxiCommand`, `SND_FlushCommand`) | GBATEK, same: IPCFIFOCNT *"Bit 1 (R) Send Fifo Full Status"*, *"Bit 14 (R/W) Error, Read Empty/Send Full"* | agrees | The port never emulates IPCFIFOCNT, so "full" reads 0 from plain memory and the retry loop always exits first time. That is the right answer for a queue that never fills; note it rather than leave it silent |
| H3 | The touch reply word is `START(1<<25) | END(1<<24) | 0x8000 | (command << 8)` per `nitro/spi/common/pm_common.h` [`pxisend.c:8-22`] | NitroSDK, [`include/nitro/spi/common/pm_common.h`](https://github.com/ntrtwl/NitroSDK/tree/main/include/nitro/spi/common) exists publicly and can settle it; GBATEK does not describe the SDK's software protocol | **unspecified** — verify | Bits 25 and 24 sit where NitroSDK's PXI layer keeps its own error and tag fields for `PXI_SendWordByFifo`. The port calls the receive callback directly so no masking happens, but the constants should be read out of the public header and cited by name rather than paraphrased. Fix **P13** |
| H4 | Tag 7 carries one word: the address of the sound command linked list; the ARM7 walks it and increments `finishCommandTag` [`pxisend.c` `snd_arm7`; `wiki/systems/audio.md`] | NitroSDK, `include/nitro/snd` in the same mirror; command id 29 = `SHARED_WORK` | agrees with the ROM's own matched sources; not in GBATEK | agrees (S-grade) | Cite the SDK header for the command-id enum rather than only the matched sources |
| H5 | Tag 11 is the card, and `CARD_REQ_INIT` (0) is followed by a second word naming the command block | NitroSDK `include/nitro/card` | agrees with matched code; not in GBATEK | agrees | Same: name the SDK header |
| H6 | The card must be answered a frame late so the poll after the post sees BUSY | — | agrees (behavioural, established by CARD40) | nothing. This is the strongest timing rule the port has and it was won the hard way |
| H7 | Tag numbering: 4 NVRAM/user settings, 5 RTC, 6 touch, 7 sound, 8 PM, 10 WM, 11 and 14 card | NitroSDK `include/nitro/pxi/common/fifo.h` (the `PXI_FIFO_TAG_*` enum) is public in the same mirror | **unspecified** — verifiable | Read the enum and cite it; the repo's tag table is currently grade E (observed) and could be S |

---

## 2. Concrete port fixes, in priority order

Each names the file, the function, what the spec says, what the code does, and how to verify.

### P1 — model the stylus's 1–2 frame latency (`port/shim/input/touch.c`, `func_020e9314`)

**Spec.** melonDS adds no latency of its own ([`src/SPI.cpp`](https://github.com/melonDS-emu/melonDS/blob/master/src/SPI.cpp), TSC `SetTouchCoords`), so the measured 1–2 frame lag on the oracle is produced by the ROM: the ARM7 fills `gAutoData` asynchronously at `frequence` samples a frame ([`tp.h`](https://github.com/ntrtwl/NitroSDK/blob/main/include/nitro/spi/ARM9/tp.h)), `TPi_TpCallback` advances the index on a PXI interrupt, and `func_020e9314` publishes only when it finds **three consecutive good samples** ending at the newest or one older. A contact that begins in frame N therefore cannot produce three good samples before late in frame N, and the trailing-window branch keeps republishing it for one frame after release.

**Code.** `touch_scheduled` returns "down" for exactly the frames in `[AT, AT+FOR)` and `func_020e9314` publishes on that frame.

**Fix.** Keep a small shift register of the last three frames' contact state inside `func_020e9314`. Publish `touch = 1` only when all three are down (onset delayed two frames) and hold `touch = 1` for one frame after the newest sample goes up (release delayed one frame). Do it behind `ACWW_TOUCH_LATENCY=0|1` defaulting **off** for one cycle so every existing measurement stays comparable, then flip the default.

**Verify.** The fixture already exists. Re-run the 24,600 recipe — the one that diverged before ORACLE42 moved it to 24,700 — with the latency modelled, and compare against `scratchpad/oracle/tap-fullpad` at frame 25,500. Success is the port failing to confirm the town name exactly as the original does. This is the open hypothesis at the end of `wiki/systems/input-and-touch.md` and this fix is its experiment.

### P2 — DISPSTAT's VBlank line range, V-count match and HBlank (`port/interp/interp_boot.c`, `dispstat_load`)

**Spec.** GBATEK, [DS Video Stuff](http://problemkaputt.de/gbatek-ds-video-stuff.htm): *"the VBlank flag isn't set in the last line (ie. only in lines 192..261, but not in line 262)"*. [LCD I/O Interrupts and Status](http://problemkaputt.de/gbatek-lcd-i-o-interrupts-and-status.htm): bit 2 is the V-counter match flag, set when VCOUNT equals the compare value in DISPSTAT bits 8–15 and 7; bit 1 is the HBlank flag, *"toggled in all lines"*.

**Code.** `return ((v >= 192u ? 1u : 0u) | (page & 0xfff8u)) | (v << 16);` — VBlank on 192..262, bit 1 always 0, bit 2 always 0.

**Fix.** Three changes in one expression: `v >= 192 && v <= 261` for bit 0; set bit 2 when `v == (((stat >> 8) & 0xFF) | ((stat >> 7) & 1) << 8)`; and decide HBlank deliberately — either set bit 1 on alternate reads and say so, or leave it clear and add a counter that names a DISPSTAT read repeated more than 263 times without progress.

**Verify.** A host-side unit test, not a run: call `dispstat_load` 263 times from a fixture with a known compare value written into the page and assert the exact bit-0/bit-2 sequence, plus one `acww_frame()` call. `port/render/selftest.c` is the existing pattern for a self-checking fixture in this repo.

### P3 — `MI_DmaCopy32`/`MI_DmaCopy16`/`MI_DmaFill32` must recognise a GX FIFO destination (`port/shim/os/dma.c`)

**Spec.** GBATEK, [DS 3D Geometry Commands](https://problemkaputt.de/gbatek-ds-3d-geometry-commands.htm): `0x04000400` is one port; a transfer to it does not advance the destination. `port/shim/os/mi.c` already routes a FIFO-destined `MIi_CpuCopy32` to `acww_gx_fifo_run` ([`docs/kb/hybrid/hardware-services.md`](../../docs/kb/hybrid/hardware-services.md) section 5).

**Code.** Only `dma_raw` tests `dest - 0x04000400u < 0x40u`. The three wrapper entry points copy with `*d++`.

**Fix.** Hoist the same three-line test into the three wrappers and route to `acww_gx_fifo_run`. If a caller is *not* expected to exist, make it a named refusal rather than a silent walk — the file's own stated policy.

**Verify.** A fixture that calls `MI_DmaCopy32` with a two-word packed display list destined for `0x04000400` and asserts that `acww_gx_words()` advanced by two and the command ports at `0x04000404`.. were not written.

### P4 — `CpuFastSet` must not round up on NDS (`port/interp/interp_bios.c`, case `0x0c`)

**Spec.** GBATEK, [BIOS Memory Copy](https://problemkaputt.de/gbatek-bios-memory-copy.htm): *"On the GBA, the length should be a multiple of 8 words … On NDS/DSi, the length may be any number of words (4 bytes). … After processing all 32-byte-blocks, the NDS/DSi additonally processes the remaining words as 4-byte blocks."*

**Code.** `n2 = ((ctl & 0x1fffffu) + 7u) & ~7u;` — up to seven words of overwrite past the destination on every non-multiple-of-8 call.

**Fix.** `n2 = ctl & 0x1fffffu;`. One line.

**Verify.** Fixture: fill a 16-word buffer with a sentinel, `CpuFastSet` 9 words into it, assert words 9..15 still hold the sentinel. This is the cheapest fix on the list and the one most likely to be corrupting something already.

### P5 — correct the DMA control-word comment (`port/shim/os/dma.c`, above `dma_raw`)

**Spec.** GBATEK, [DS DMA Transfers](https://problemkaputt.de/gbatek-ds-dma-transfers.htm): on NDS9 *"the gamepak bit (Bit 27) has been removed and is instead used to expand the mode setting to 3bits"* — start timing is bits **27–29**, with mode 7 the Geometry Command FIFO and mode 4 the main-memory display.

**Code.** The comment says "27..28 start timing". The code ignores the field.

**Fix.** Correct the comment, list the seven modes, and state explicitly that the port selects the FIFO path by destination address instead — so the next reader does not "fix" it into using two bits of a three-bit field. Also say that repeat (bit 25) and destination mode 3's reload are ignored, and that nothing has needed them.

**Verify.** Documentation only; `tools/check_docs.py`.

### P6 — pre-empt the missing decompression SWIs (`port/interp/interp_bios.c`)

**Spec.** GBATEK, [BIOS Decompression Functions](https://problemkaputt.de/gbatek-bios-decompression-functions.htm): on NDS, 12h is `LZ77UnCompReadByCallbackWrite16bit`, 13h is `HuffUnCompReadByCallback`, 15h is `RLUnCompReadByCallbackWrite16bit`.

**Code.** Only the "normal" forms 11h and 14h exist. NitroSDK's `MI_UncompressHuffman` is 13h and its VRAM-safe unpackers are 12h/15h.

**Fix.** Two options and the choice should be recorded: implement 13h (Huffman, 4-bit and 8-bit) and treat 12h/15h as their normal-form twins with a 16-bit write, **or** leave them unimplemented and confirm that the stop message names the SWI number. Prefer the second until one actually fires — the current behaviour already stops by name, which is the port's stated policy, and guessing a callback ABI is worse than a named stop.

**Verify.** `ACWW_INTERP_SWI` already names an unmodelled SWI. Grep a long town run's log for it; if 13h never appears, close this as a negative and say so.

### P7 — the DIV0 flag (`port/interp/interp_boot.c`, `io_load`)

**Spec.** GBATEK, [DS Maths](https://www.problemkaputt.de/gbatek-ds-maths.htm): DIVCNT bit 14 is the divide-by-zero flag, *"set only if the full 64bit DIV_DENOM value is zero, even in 32bit mode"*.

**Code.** `*w = io_page_word(a) & 0x3fffu;` masks bit 14 away along with the busy bit.

**Fix.** Compute the flag from the full 64-bit denominator and OR it into the returned CNT; keep bit 15 clear.

**Verify.** Fixture: write DIVCNT mode 0, NUMER = 5, DENOM = 0, read DIVCNT, assert bit 14; write a non-zero high denominator word with a zero low word in mode 0 and assert bit 14 is **clear**.

### P8 — `GetCRC16` length (`port/interp/interp_bios.c`, case `0x0e`)

**Spec.** GBATEK, [BIOS Misc Functions](https://problemkaputt.de/gbatek-bios-misc-functions.htm): the address must be 2-byte aligned and the length is *"in bytes, must be 2-byte aligned"*; DeSmuME's `getCRC16` computes `size = R[2] >> 1` and iterates halfwords, so an odd trailing byte is dropped.

**Code.** `for (i = 0; i < len; i++)` over every byte.

**Fix.** `len &= ~1u;` before the loop. Optionally set `r[3]` to the last halfword, which DeSmuME models as a real BIOS side effect.

**Verify.** Fixture: CRC of a 5-byte buffer must equal the CRC of its first 4 bytes.

### P9 — byte reads of the I/O page bypass the synthesis hook (`port/interp/interp_cpu.c`, `ld8`)

**Spec.** Not a spec matter — an internal consistency one. `ld32` and `ld16` call `io_word`; `ld8` does not.

**Code.** `static u32_ ld8(u32_ a) { return *(volatile unsigned char *)a; }`.

**Fix.** Route `ld8` through `io_word` and select the byte, exactly as `ld16` selects the halfword. Cheap, and removes a whole class of "the loop never released" that would be invisible.

**Verify.** Fixture: `ldrb` from `0x04000006` twice through the interpreter and assert the second read is one greater.

### P10 — apply the colour effects in the 5-bit domain (`port/render/nds2d.c`, `chan_mix` and `brighten`)

**Spec.** GBATEK, [LCD I/O Color Special Effects](https://problemkaputt.de/gbatek-lcd-i-o-color-special-effects.htm): *"I = MIN ( 31, I1st\*EVA + I2nd\*EVB )"*, *"I = I1st + (31-I1st)\*EVY"*, *"I = I1st - (I1st)\*EVY"*, with the coefficients as sixteenths.

**Code.** Both operate on 8-bit expanded channels and clamp at 255.

**Fix.** Do the arithmetic on the 5-bit channel values before the BGR555→BGRA expansion, or equivalently `>>3`, blend, clamp at 31, `<<3`. The visible difference is at most a couple of levels per channel, but it is a systematic bias against the oracle and it costs nothing to remove.

**Verify.** `port/render/selftest.c` already has a blend fixture (SKY40 records it passing). Add three cases with hand-computed 5-bit expected values: EVA=9/EVB=7 over two known BGR555 colours, EVY=5 increase, EVY=5 decrease. Then re-run the ncc comparison at the nine sampled frames of `tap-D62` against `scratchpad/oracle/tap-24700` and check the mean does not fall.

### P11 — a semi-transparent OBJ should never take the brightness path (`port/render/nds2d.c`, `apply_color_effects`)

**Spec.** GBATEK, same page: semi-transparent OBJs *"are always using Alpha Blending mode (regardless of BLDCNT Bit 6-7)"*.

**Code.** When `own_semi[i]` is set but the layer below is not a second target, the pixel can fall through to the brightness branch if OBJ is a BLDCNT first target.

**Fix.** Guard the brightness branch with `!own_semi[i]`. Low priority and worth measuring first: emulators disagree with GBATEK's literal sentence here, and the port's counters already separate the two populations (`px_obj_semi` vs `px_bright`).

**Verify.** Read `px_obj_semi` and `px_bright` from a town run first. If `px_bright` is zero on semi-transparent pixels the change is inert and should not be made.

### P12 — GXSTAT: set the empty bit and stop erasing the FIFO-IRQ mode (`port/render/nds3d.c`, `gxstat_update`)

**Spec.** GBATEK, [DS 3D Status](https://problemkaputt.de/gbatek-ds-3d-status.htm): *"25 Command FIFO Less Than Half Full"*, *"26 Command FIFO Empty"*, *"30-31 Command FIFO IRQ"*. `NNS_G3dInit` writes bits 30–31 at bring-up [`src/matched/NNS_G3dInit.c`].

**Code.** `v |= 1u << 25;` only, and `wr32(GX_GXSTAT, v | (old & 0x8000u))` keeps nothing but the stack-error bit.

**Fix.** Set bit 26 as well as bit 25 (a synchronous engine is both empty and less-than-half-full), leave bits 16–24 zero, and preserve `old & 0xC0000001u` — the IRQ mode and the test-busy bit the test commands own — in addition to bit 15. Correct the comment on line 217.

**Verify.** Fixture: write `0x40000000` to GXSTAT, submit a matrix command through `acww_gx_port`, read GXSTAT back and assert bits 30–31 survived and bit 26 is set.

### P13 — cite the PXI protocol constants instead of paraphrasing them (`port/shim/os/pxisend.c`)

**Spec.** The NitroSDK source is public: [`include/nitro/pxi/common/fifo.h`](https://github.com/ntrtwl/NitroSDK/tree/main/include/nitro/pxi/common) carries the `PXI_FIFO_TAG_*` enum and the tag/error/data field layout `PXI_SendWordByFifo` uses; [`include/nitro/spi/common/pm_common.h`](https://github.com/ntrtwl/NitroSDK/tree/main/include/nitro/spi/common) carries the START/END bits the touch reply is built from.

**Code.** `pxisend.c:8-22` names `pm_common.h` from memory and hard-codes `1<<25`, `1<<24`, `0x8000`. The tag table in `hardware-services.md` is grade E — observed, not read.

**Fix.** Read both headers, name the constants in the comment, and promote the tag table from E to S with the header as the citation. If the PXI data field turns out to be narrower than bit 25, the touch reply word is wrong in a way that currently cannot bite only because the port calls the callback directly.

**Verify.** Documentation and comment; then one run to confirm no `acww pxi:` line changed.

---

## 3. Public references that could name `func_XXXXXXXX`

URLs only, as asked; none of this was copied into the repo.

**No public decompilation of Animal Crossing: Wild World exists.** It is absent from
<https://decomp.dev>, <https://decomp.wiki/platforms/nintendo-ds> and <https://decomp.me>.
The only public discussion of attempting one is
<https://gbatemp.net/threads/need-a-bit-of-guidance-trying-to-decomp-acww.673305/>.
ACWW modding projects exist but carry no code symbols: <https://github.com/TheGag96/acww-hax>,
<https://github.com/TheGag96/nitromods>, <https://github.com/Universal-Team/WildEdit>,
<https://github.com/MikeFritzDevelops/ACWW-Archipelago>.
The other-platform Animal Crossing decomps are <https://github.com/ACreTeam/ac-decomp>
(GameCube), <https://github.com/zeldaret/af> (N64), <https://github.com/ACreTeam/afe-decomp>.

**A full NitroSDK and NitroSystem source tree is public**, and it is the highest-value find in
this audit for naming SDK-layer functions this repo still calls `func_XXXXXXXX`:

- <https://github.com/ntrtwl/NitroSDK> — `include/nitro/` (os, fs, card, mi, pxi, spi, gx, fx,
  rtc, snd, std, wm) plus sources. Verified live during this audit: `include/nitro/spi/ARM9/tp.h`
  declares the whole TP API the touch page describes.
- <https://github.com/ntrtwl/NitroSystem> — `include/nnsys/` (fnd, g2d, g3d, gfd, snd): the
  `NNS_G2d*`, `NNS_G3d*`, `NNS_Snd*` names.
- <https://github.com/ntrtwl/NitroWiFi>, <https://github.com/ntrtwl/NitroDWC> — the `ov065`
  and DWC layer.
- <https://github.com/pret/pokediamond>, <https://github.com/pret/pokeheartgold>,
  <https://github.com/pret/pokeplatinum> — matched NitroSDK/NNS sources inside DS decomps.
- <https://github.com/radicalten/mkdsdecomp> — ships generated symbol and type headers plus
  `libntr`, a reimplementation of the SDK libraries.
- <https://github.com/PikalaxALT/ndsbios> — disassembly of the ARM7 and ARM9 BIOS; the source of
  record for the SWI vector table cited above.
- <https://github.com/AetiasHax/ds-decomp> — `dsd`, the current DS delinking/symbol toolkit.
- <https://github.com/UsernameFodder/pmdsky-debug> — not ACWW, but the model for the artefact
  this project lacks: per-region YAML symbol tables for arm9 and each overlay.
- <https://www.retroreversing.com/DS-NITRO-SDK> — index of the SDK tree and its `/man` manuals.

---

## 4. Hypotheses this audit raises

- **H1.** The 1–2 frame stylus lag is fully explained by "three consecutive good samples at four
  samples a frame". Settled by P1: if modelling exactly that reproduces the original's refusal at
  24,600 and its acceptance at 24,700, the mechanism is right and `input-and-touch.md`'s standing
  open question closes.
- **H2.** No layer in ACWW rewrites `BGxX`/`BGxY` outside VBlank, which is what makes
  `draw_affine_bg`'s closed form exact. Settled by an `ACWW_INTERP_WATCH` on `0x04000038` and
  `0x0400003C` over the town recipe, reporting any write whose synthetic VCOUNT is under 192.
- **H3.** Nothing in the game reads DISPSTAT bit 2 or bit 1. Settled by the same instrument on
  `0x04000004` reads, counting reads whose result is discarded after a bit-1 or bit-2 test — or
  more cheaply, by P2 plus the observation that no run changes.
- **H4.** `CpuFastSet` with a non-multiple-of-8 word count is reached in real play, so P4 is
  fixing live corruption rather than a latent hazard. Settled by counting calls whose count is
  not a multiple of 8 in the SWI handler for one town run, before making the fix.
- **H5.** The PXI touch reply's bits 24–25 do not collide with NitroSDK's own tag/error fields.
  Settled by reading `nitro/pxi/common/fifo.h` (P13).

## 5. Related

- `../engine/graphics-pipeline.md`, `../engine/threads-and-interrupts.md`
- `../systems/input-and-touch.md`, `../systems/time-and-rtc.md`, `../systems/audio.md`
- `../../docs/kb/hybrid/hardware-services.md` — the implementation-side page these claims come from
- `../../docs/rules/D-defects.md` — D12 (a name encoding a mistyped target) is the class C2 belongs to
- `../../docs/rules/M-method.md` — M1 (suspect the measurement) is why row B4 reads as it does
