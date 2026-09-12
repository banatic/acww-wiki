# Bus timings: what an access costs when it is not a cache hit

**Summary.** `memory-map.md` says which regions exist and which of them are cached; this page
says what each costs in time. Three devices set the price of everything the ARM9 waits for: the
**memory bus**, whose per-region numbers say what an uncached load costs and what a cache line
fill costs; the **cartridge**, which is a page device and not a pipe, so a request costs a
whole 512-byte command or nothing at all; and the **geometry FIFO**, 260 entries deep, which
freezes the storing instruction when a display list overruns it. Every number here is the DS's,
cited; none of it is fitted to anything the port measured.

The clock unit throughout: the bus runs at 33.513982 MHz and the ARM9 at twice that, 67.027964
MHz [P: GBATEK "DS Memory Timings": "Bus clock = 33MHz (33.513982 MHz)", "NDS9 clock = 66MHz
(internally twice bus clock; for cache/tcm)"], so **one bus unit is two ARM9 cycles** and a
"half" unit is one.

## What happens

### The memory bus, per region

GBATEK's NDS9/DATA table, verbatim, in its own 33 MHz units [P: GBATEK "DS Memory Timings",
NDS9/DATA; "All timings are counted in 33MHz units (so "half" cycles can occur on NDS9)"]:

| N32 | S32 | N16 | S16 | Bus | region |
|---|---|---|---|---|---|
| 10 | 2 | 9 | 1 | 16 | Main RAM (read) (cache off) |
| 4 | 1 | 4 | 1 | 32 | WRAM, BIOS, I/O, OAM |
| 5 | 2 | 4 | 1 | 16 | VRAM, Palette RAM |
| 19 | 12 | 13 | 6 | 16 | GBA ROM |
| 13 | 10 | 13 | 10 | 8 | GBA RAM |
| 0.5 | 0.5 | 0.5 | — | 32 | TCM, Cache_Hit |
| 11 | 11 | 11 | — | 32 | Cache_Miss (BIOS) |
| 23 | 23 | 23 | — | 16 | Cache_Miss (Main RAM) |

Read it with `memory-map.md`'s cached-window answer beside it. Main RAM proper is cached, so a
load there is either the 0.5-unit hit or the 23-unit line fill — the fill is where the 46 ARM9
cycles on that page come from. Everything the same routine leaves uncached — I/O, palette,
VRAM, OAM, the `0x027fxxxx` mirror — pays its own row instead, and the two TCMs pay the hit
rate, because a TCM access never reaches the bus.

**A single isolated access is a NON-SEQUENTIAL one**, so N32 applies to a word and N16 to a
halfword or a byte; the S columns are the second and later accesses of a burst. In ARM9 cycles
that makes an uncached main-RAM word **20**, an I/O or OAM word **8**, a VRAM or palette word
**10**, and a TCM word **1**.

**A caution that has already cost one retraction.** GBATEK prints TWO tables, NDS9/CODE and
NDS9/DATA, and their Main-RAM cache-off rows differ: CODE is `9 9 4.5 4.5 16` and DATA is
`10 2 9 1 16`. Quoting 9 as the DATA table's N32 is reading the N16 column
[H: source account: `docs/log/cycle41-gameplay.md` LATENCY55 L55-2, retracting MEM54 finding 7 item
3; direct ROM-source provenance unresolved].

### The cartridge: a command, a gap, a page, a gap

Communication is 8-byte commands [P: GBATEK "DS Cartridge Protocol": "Communication with
Cartridge ROM relies on sending 8 byte commands to the cartridge, after the sending the command,
a data stream can be received from the cartridge"], and ROMCTRL at `0x040001a4` carries the
rest of the shape [P: GBATEK "DS Cartridge I/O Ports", 40001A4h: "0-12 KEY1 gap1 length
(0-1FFFh) ... (leading gap)", "16-21 KEY1 gap2 length (0-3Fh) ... (200h-byte gap)", "24-26 Data
Block size (0=None, 1..6=100h SHL (1..6) bytes, 7=4 bytes)", "27 Transfer CLK rate
(0=6.7MHz=33.51MHz/5, 1=4.2MHz=33.51MHz/8)"].

For this ROM every field is in the header word `normal_cmd_setting = 0x00416017`
[S: `docs/log/cycle41-gameplay.md` LOAD52 L52-3 and LATENCY55 L55-1, from the extracted header]:
gap1 = `0x00416017 & 0x1fff` = **23** clocks, gap2 = `(0x00416017 >> 16) & 0x3f` = **1**, and
bit 27 = 0, the **6.7027964 MHz** clock. The block size is not in the header: the SDK ORs
`CARD_COMMAND_PAGE` = `0x01000000` into the control word, making field 24-26 = 1 = `0x100 SHL 1`
= **512 bytes** [S: `CARDi_TryReadCardDma`, `autoload_2`,
`src/matched/CARDi_TryReadCardDma.c:54,106`], which is `CARD_ROM_PAGE_SIZE`
[S: `CARDi_ReadCard`, `autoload_2`, `src/matched/CARDi_ReadCard.c:19`].

One cartridge clock carries one byte, and 67.027964 / 6.7027964 = **exactly ten ARM9 cycles a
clock**. So one command is

    8 + gap1 23 + 512 + gap2 1 = 544 clocks = 5,440 ARM9 cycles

of which the gaps and the command phase — the LATENCY, as against the 512 clocks of throughput
— are 32 clocks, **6.25%**.

**The page is what matters, not the gaps.** `CARDi_ReadCard` reads a whole page per command and
puts it in the caller's buffer only when the request is page-aligned, word-aligned and at least
a page long; otherwise it lands in `p->cache_buf` and records the page in `p->cache_page`
[S: `CARDi_ReadCard`, `autoload_2`, `src/matched/CARDi_ReadCard.c:75-122`]. That ONE page is
then remembered across requests: `CARDi_ReadFromCache` serves anything inside it with a
`MI_CpuCopy8` and issues no command at all
[S: `CARDi_ReadFromCache`, `autoload_2`, `src/matched/CARDi_ReadFromCache.c:253-269`]. A short
read therefore costs a full 5,440-cycle command or nothing, decided by where the previous read
left the page — and no per-byte rate can express that. Measured on the town-hall exit, 2,956
requests of about eleven bytes were **1,106 commands and 1,850 free hits**
[H: source account: `docs/log/cycle41-gameplay.md` LATENCY55 L55-5; direct ROM-source
provenance unresolved].

**A ROM read never involves the ARM7.** `CARDi_ReadCard` reads `REG_CARD_DATA` at `0x04100010`
on the ARM9 itself and spins on `CARD_DATA_READY` in ROMCTRL
[S: `CARDi_ReadCard`, `autoload_2`, `src/matched/CARDi_ReadCard.c:25,100-109`]. The ARM7 card
driver serves the BACKUP family over PXI — see `systems/save-data.md`.

### The geometry FIFO

The geometry engine is fed through a **256-entry FIFO plus a 4-entry PIPE, 260 in all**, and a
writer that fills it is stopped dead [P: GBATEK "DS 3D Geometry Commands": "The FIFO has 256
entries, additionally, there is a PIPE with four entries"; "If the FIFO is full, then a wait is
generated until data is removed from the FIFO, ie. the STR opcode gets freezed"]. An entry is a
command with one parameter, so a command taking N parameters occupies `max(1, N)` of them.

The drain rate is per command, in the same 33 MHz bus units as the memory table — `MTX_MODE` 1,
`MTX_PUSH` 17, `MTX_POP` 36, `MTX_LOAD_4x4` 34, `MTX_MULT_4x4` 35, `MTX_MULT_4x3` 31,
`MTX_MULT_3x3` 28, `MTX_SCALE`/`MTX_TRANS` 22, `NORMAL` 9, `VTX_16` 9, `VTX_10` and the other
vertex forms 8, `DIF_AMB`/`SPE_EMI` 4, `LIGHT_VECTOR` 6, `SHININESS` 32, `BOX_TEST` 103,
`POS_TEST` 9, `VEC_TEST` 5, `SWAP_BUFFERS` 392, and the state-setting commands 1
[P: GBATEK "DS 3D Geometry Commands", the command list]. The parameter counts of that same list
are independently transcribed in the port's own display-list parser
[H: source account: `port/render/gxfifo.c`'s `param_count[]`; direct ROM-source provenance
unresolved], and the two agree on all 37 entries.

## Grades and gaps

- The per-region bus table, the ROMCTRL field list, the 8-byte command, the FIFO depth and the
  stall sentence are **[P]** — published hardware documentation, quoted.
- The cartridge's gap1, gap2, clock and page size for THIS ROM are **[S]** — the header word
  and the matched SDK sources that consume it.
- What the port does with all of it, and the measured request/command ratio, are **[H]** — the
  port's own model under `ACWW_TICK_MODEL`, recorded in `docs/log/cycle41-gameplay.md`
  TICK53 / MEM54 / LATENCY55 and summarised in `docs/kb/hybrid/hardware-services.md` 4b.
- **Unresolved.** The write buffer's depth and its stall behaviour are not priced anywhere in
  this repo, so a store to an uncached region is treated as free. The cartridge's behaviour when
  a command is issued while the previous one is still streaming is not modelled either. Both
  omissions make any estimate built on this page a LOWER bound on elapsed time.

## Where this is used

`memory-map.md` (the regions and which are cached), `time-budgets.md` (what the game does with
the time), `systems/save-data.md` (the backup device, which is the ARM7's side of the
cartridge), `graphics-pipeline.md` (what goes into the FIFO).
