# Memory map

**Summary.** ACWW runs in 4 MB of main RAM at `0x02000000`, with two tightly-coupled memories
either side of it — instruction TCM below at `0x01ff8000` and data TCM at `0x027e0000` — plus
the usual NDS I/O, palette, VRAM and OAM windows. Code occupies the bottom of main RAM
(`main`, then `autoload_2`); overlays page into a band around `0x02207cc0`-`0x022a31d8`; the
game's globals cluster in `0x021cxxxx`-`0x021fdxxx`; and everything above the arena's low
water mark is one expanded heap the game allocates every object from. This page is the address
key the other engine pages cite into.

## What happens

### The regions

| region | address range | size | grade / citation |
|---|---|---|---|
| ITCM | `0x01ff8000`-`0x02000000` | 32 KB | [H: source account: `docs/kb/hybrid/runtime.md` section 2, from `port/interp/interp.h`; direct ROM-source provenance unresolved] |
| main RAM | `0x02000000`-`0x02400000` | 4 MB | [H: source account: `port/platform/win32.c:75-76`; direct ROM-source provenance unresolved] |
| DTCM | `0x027e0000`-`0x027e4000` | 16 KB | [H: source account: `port/interp/interp_boot.c:11-14`; direct ROM-source provenance unresolved] |
| system-RAM mirror window | `0x027f0000`-`0x02800000` | 64 KB | [H: source account: `port/platform/win32.c:108-111`; direct ROM-source provenance unresolved] |
| I/O registers, both 2D engines | `0x04000000`-`0x04002000` | 8 KB | [H: source account: `port/platform/win32.c:99`; direct ROM-source provenance unresolved] |
| palette RAM | `0x05000000`-`0x05000800` | 2 KB | [H: source account: `port/platform/win32.c:100`; direct ROM-source provenance unresolved] |
| VRAM, all windows and LCDC aliases | `0x06000000`-`0x068a4000` | — | [H: source account: `port/platform/win32.c:106`; direct ROM-source provenance unresolved] |
| OAM | `0x07000000`-`0x07000800` | 2 KB | [H: source account: `port/platform/win32.c:107`; direct ROM-source provenance unresolved] |

Main RAM is MIRRORED across `0x02000000`-`0x02ffffff` on hardware, and the game depends on it:
crt0 writes the interrupt-vector slot at `0x027fff9c` and the boot flag lives at `0x027ffc20`,
both inside the `0x027fxxxx` window, which is the same storage as `0x023fxxxx`
[H: host/prose inference from `port/platform/win32.c:78-83`; verify against the ROM function or symbol table and this page's recipe]. Within the VRAM range, engine A's BG window is at
`0x06000000`, engine B's at `0x06200000`, the two OBJ windows at `0x06400000` and `0x06600000`,
and the LCDC bank aliases at `0x06800000`; the ROM's own bring-up clears 128 KB of that last
one [H: host/prose inference from `port/platform/win32.c:101-105`; verify against the ROM function or symbol table and this page's recipe].

### Where the code is

| module | function-address span | function symbols | grade / citation |
|---|---|---|---|
| `itcm` | `0x01ff8000`-`0x01ffda6c` | 158 | [H: source account: `config/adm-kr/arm9/itcm/symbols.txt`; direct ROM-source provenance unresolved] |
| `main` | `0x0200007a`-`0x020c74c4` | 11,923 | [S: `config/adm-kr/arm9/symbols.txt` (`main` at 0x02000c38); source account: `config/adm-kr/arm9/symbols.txt`] |
| `autoload_2` | `0x020e8840`-`0x02138f00` | 2,199 | [H: source account: `config/adm-kr/arm9/autoload_2/symbols.txt`; direct ROM-source provenance unresolved] |
| overlays (138 with code) | `0x02207cc0`-`0x022a31d8` | 11,236 | [H: source account: `config/adm-kr/arm9/overlays/*/symbols.txt`; direct ROM-source provenance unresolved] |
| `dtcm`, `autoload_3` | — | 0 | [H: source account: their `symbols.txt` files contain no `kind:function` lines; direct ROM-source provenance unresolved] |

`itcm` is small and hot: the per-object display step `func_01ffd1b4`, the stepper
`func_01ffd44c`, the step gate `func_01ffd41c` and the list sentinel/successor pair all live
there [H: source account: `port/shim/gfx/dispstep.c` header; `port/shim/gfx/dispsteppers.c:24-28`;
`port/shim/gfx/dispgate.c` header; direct ROM-source provenance unresolved]. `autoload_2` is the library layer — MSL C, the
CodeWarrior float/64-bit runtime, SPL, the Korean IME and the C++ unwinder
[H: source account: `docs/kb/modules/autoload2.md`; direct ROM-source provenance unresolved]. Within it, `0x021341f0`-`0x02137124` is prebuilt
assembly from CodeWarrior's `FP_fastI_v5t_LE.a` and is not compiled C at all
[H: source account: `docs/kb/modules/autoload2.md`; direct ROM-source provenance unresolved].

Overlays overlap heavily — 129 of 137 adjacent pairs share address ranges — so an address in
the overlay band identifies a byte only together with a residency answer
[H: host/prose inference from `port/shim/fs/ovlreloc.c` header; verify against the ROM function or symbol table and this page's recipe]. See `overlays.md`.

### The stacks in DTCM

crt0 puts the SVC and IRQ stacks at the top of DTCM and the system stack below them; the split
is NitroSDK's default, IRQ 0x100 and SVC 0x40 above `0x027e3fc0`
[H: source account: `port/interp/interp_boot.c:11-14`; direct ROM-source provenance unresolved]. Below both, at `0x027e3e00`, the PC port's interpreter
starts its own system stack and grows down [H: source account: `port/interp/interp_boot.c:31`; direct ROM-source provenance unresolved]. The bottom of
DTCM is the OS interrupt table: `OS_IRQTable[0]`, the VBlank slot, is the word at `0x027e0000`
[H: source account: `port/shim/os/vblank.c:80`; direct ROM-source provenance unresolved]. The PXI receive-callback table is at `0x027e0394`, indexed by
FIFO tag [H: source account: `port/shim/os/pxisend.c:99-135` via `docs/kb/hybrid/hardware-services.md` section 1; direct ROM-source provenance unresolved].

### The caches and the TCMs, and which of these regions is cached

The ARM9 is an ARM946E-S with an 8 KB instruction cache, a 4 KB data cache, a 32 KB instruction
TCM and a 16 KB data TCM [P: GBATEK "DS Technical Data", NDS9 line: "60KB TCM/Cache (TCM: 16K
Data, 32K Code) (Cache: 4K Data, 8K Code)"]. Both caches are four-way set associative with
32-byte (eight-word) lines, which makes 64 instruction sets and 32 data sets
[P: ARM946E-S TRM, ARM DDI 0201D section 3.1: "The instruction cache and data cache are
four-way set associative, with a cache line length of 8 words (32 bytes)"]. A hit is one
processor cycle [P: the same section: "Each cache supports single-cycle read access"] and a
miss is a whole-line fetch from main RAM over the 16-bit bus, which GBATEK prices at 23 units
of the 33 MHz bus clock [P: GBATEK "DS Memory Timings", NDS9/DATA row "Cache_Miss (Main RAM)
23 23 23 - 16", with "All timings are counted in 33MHz units" and "NDS9 clock = 66MHz
(internally twice bus clock; for cache/tcm)"] -- 46 ARM9 cycles, against the one a hit costs.

The game configures all of it itself, in one CP15 routine, and that routine is the citation for
every policy question this page could otherwise only guess at. It ends by ORing `0x0005707d`
into the CP15 Control Register, whose bit 2 enables the data cache, bit 12 the instruction
cache, bit 16 the data TCM, bit 18 the instruction TCM and **bit 14 round-robin cache
replacement** [S: `func_02000a5c`, `main`, `src/matched/func_02000a5c.c`]
[P: ARM DDI 0201D Table 2-9, bit 14 "Round-robin replacement"]. It puts DTCM at `0x027e0000`
with size field `0xa`, and the TCM size rule is 512 SHL N over bits 5:1, so N = 5 is 16 KB --
which is the DTCM row in the region table above, from the ROM rather than from the port
[S: `func_02000a5c`, `main`, `src/matched/func_02000a5c.c`].

**Only main RAM is cached.** The same routine writes `0x42` to both CP15 c2,c0,0 (data
cacheable) and c2,c0,1 (instruction cacheable), which selects protection regions 1 and 6 alone
[S: `func_02000a5c`, `main`, `src/matched/func_02000a5c.c`]; region 1 is the main-RAM region the
arena code later rebuilds as a 4 MB region based at `0x02000000`
[S: `OS_InitArenaEx`, `autoload_2`, `src/matched/OS_InitArenaEx.c`], and region 6 is the vector
page at `0xffff0000`. I/O, palette, VRAM, OAM and the `0x027fxxxx` mirror window are therefore
uncached, and the two TCMs are never cached at all because the TCM takes precedence over the
cache for accesses in its range [P: ARM DDI 0201D section 2.9, Control Register bit 16].

The data cache allocates on a read miss only, and a write that misses "is not loaded into the
cache as a result of that miss" [P: ARM DDI 0201D sections 3.3 and 3.3.3]; a dirty victim goes
to the write buffer before the linefill replaces it, not to memory synchronously
[P: ARM DDI 0201D section 3.3]. The port models exactly this geometry when
`ACWW_TICK_MODEL=1` is set, and counts the fills rather than assuming a rate
[H: source account: `port/interp/interp_cpu.c` MEM54 block and `port/platform/tick.c` rule 5;
direct ROM-source provenance unresolved].

**What an access in each of these regions COSTS is `bus-timings.md`**, which carries GBATEK's
whole NDS9/DATA table (an uncached main-RAM word is 20 ARM9 cycles, an I/O or OAM word 8, a
VRAM or palette word 10, a TCM word 1, a line fill 46) together with the cartridge's per-command
price and the geometry FIFO's depth. Read it before pricing anything on this page.

### The arena and the game heap

The bring-up's last call, `func_020ea48c`, carves the game's main heap out of the OS arena
[H: source account: `port/shim/boot/heapinit.c` header; direct ROM-source provenance unresolved]. It reads `OS_GetArenaLo(0)` and `OS_GetArenaHi(0)`, rounds the low end up to 32 bytes BEFORE
subtracting so the size already pays for the alignment padding, and allocates the remainder
with `OS_AllocFromArenaLo` [S: `src/matched/OS_AllocFromArenaLo.c`; source account: `func_020ea48c`, autoload_2,
`port/shim/boot/heapinit.c` header]. Its two literals are its whole state: a configured heap
size at `0x021fbe90`, where zero means "take the rest of the arena", and an arena id at
`0x021fbe98`, which this function always sets to 0, the main arena
[H: source account: `port/shim/boot/heapinit.c` header; direct ROM-source provenance unresolved].

`func_020ea50c` then builds the heap itself [H: source account: `port/shim/boot/gameheap.c` header; direct ROM-source provenance unresolved]. It keeps a 0x30-byte header in front of the
block: the NNS expanded heap is created at block + 0x30 with 0x30 fewer bytes, with the option
flags read from `data_0213e5a4`, and `func_020ea41c` records the arrangement in that header
[S: `src/matched/func_020ea50c.c`, `src/matched/func_020ea298.c`, `src/matched/func_020ea41c.c`; source account: `func_020ea50c` / `func_020ea298`, autoload_2, `port/shim/boot/gameheap.c` header]. The
family's own pool words are `0x021fbe78`, `0x021fbe8c` and `0x021fbe94`
[H: source account: `port/shim/boot/gameheap.c:40-43`; direct ROM-source provenance unresolved].

The arena ceiling on hardware is `0x023e0000` [S: `src/matched/OS_GetInitArenaHi.c`; source account: `OS_GetInitArenaHi`,
`port/shim/os/arenahi.c` header]. The PC port raises it to `0x023f0000` for the MAIN arena
only, a labelled concession that gives the game heap 64 KB the hardware reserves for the OS,
because at the title screen the port holds about 48 KB more live main-heap weight than the
hardware does and a 0x4b000 scene buffer otherwise fails to allocate
[H: source account: `port/shim/os/arenahi.c` header; direct ROM-source provenance unresolved]. That shim is a registered host service on the
interpreter path — it is not in the deny list — so the divergence is live there too
[H: source account: `port/tools/interp_registry.py`, whose `DENY_FILES` set has 49 basenames and does not name
`arenahi.c`; `docs/kb/hybrid/runtime.md` section 4 says "40 shim files" and is stale by nine; direct ROM-source provenance unresolved]. On hardware the
same scene fits in `0x022a3330`-`0x023e0000` [H: source account: `port/shim/os/arenahi.c` header; direct ROM-source provenance unresolved].

Display objects are allocated from that heap, which is why nothing can name one from a
constant: observed town-era objects sit around `0x022b6xxx`-`0x022b7xxx` and move between runs
[H: host-source account from `port/shim/gfx/pmflist.c:52-66, 262-268`, which keeps live pointers precisely because the
allocations move; verify with a retained scripted run and frame using this page's recipe].

### The global bands

Globals cluster in a few narrow bands, and knowing which band an address is in is usually
enough to guess what it is.

`0x020exxxx` is static data at the top of `main`: the channel handler table at `0x020e3134`,
the resource-kind dispatch table `data_020e41ec`, the scene id `data_020e3c80` and the
game-mode byte `data_020e54ac` [H: source account: `port/shim/gfx/gxdirect_a.c:241`;
`port/shim/game/stageloop.c:23`; `port/shim/game/scenestate.c:31-34`;
`docs/kb/port/sequencer-and-modes.md`; direct ROM-source provenance unresolved].

`0x0213xxxx` is `autoload_2`'s data: the heap option flags `data_0213e5a4`, the display walk
mode at `0x0213e7fc`, and the exception register table the fatal path writes at `0x0213fde0`
[H: source account: `port/shim/boot/gameheap.c:40`; `port/shim/gfx/commit.c:21`; H: historical measurement account: cycle40 log, CARD40..SND40; direct ROM-source provenance unresolved].

`0x021cxxxx` is scene-era game state: the field-data pointer at `0x021c526c`, the camera
target defaults at `0x021c67d0`-`0x021c67d8`, and scene 6's two update-gate bytes at
`0x021c75b0` and `0x021c75b8` [H: source account: `port/shim/gfx/pmflist.c:296-300, 173-176, 124-131`; direct ROM-source provenance unresolved].

`0x021fxxxx` is the engine's own control block: scene 6's stage counter at `0x021f42f0`, the
sequencer mailbox at `0x021f69d0`, the VBlank task list at `0x021f6ca0`, the game-heap words
at `0x021fbe78`-`0x021fbe98`, the channel-open state at `0x021fcfd4`/`0x021fcfdc`, the
current-node publication at `0x021fcff4`, the four display-list heads at `0x021fd004`,
`0x021fd014`, `0x021fd024` and `0x021fd034`, and the channel handler table pointer at
`0x021fd044` [H: source account: `port/shim/game/scene6init.c` header; `docs/kb/port/sequencer-and-modes.md`;
`port/shim/gfx/vbtask.c:22-25`; `port/shim/boot/gameheap.c:40-43`;
`port/shim/game/chanstage.c:78-80`; `port/shim/gfx/pmflist.c:104`;
`port/shim/gfx/dispstep.c:55-58`; direct ROM-source provenance unresolved].

### What the PC port adds, and what it maps

Everything above is an NDS address. The port's own additions are host addresses and are named
here only so they are not mistaken for the game's:

- the port's executable image occupies `0x00400000`-`0x00c00000`, and every function in it
  begins with the same three-byte prologue, which is how the port tells a host code entry from
  an NDS word [H: source account: `port/shim/gfx/pmflist.c:76-100`; direct ROM-source provenance unresolved];
- a generated arena at `0x30000000`, 0x02780000 bytes, holds data symbols the ROM tables
  cannot place [H: source account: `port/platform/win32.c:114-117`; direct ROM-source provenance unresolved];
- the interpreter's interrupt stack is a 16 KB host buffer, with nested entries stepping down
  2 KB and a refusal past depth 7 [H: source account: `docs/kb/hybrid/runtime.md` section 4, from
  `port/interp/interp_boot.c:613-641`; direct ROM-source provenance unresolved].

The port maps NDS memory at its real addresses, so an NDS address IS a host pointer and the
interpreter executes ROM bytes in place with no translation and no MMU
[H: source account: `docs/kb/hybrid/runtime.md` section 2; direct ROM-source provenance unresolved]. Main RAM is one 4 MB file mapping viewed twice
rather than two allocations, so the `0x023fxxxx` / `0x027fxxxx` aliasing keeps working
[H: host/prose inference from `port/platform/win32.c:78-86`; verify against the ROM function or symbol table and this page's recipe]. The I/O page is plain host memory except where a hook
intervenes, which is why a register the ROM polls never changes on its own — the root of three
classes of stall [H: source account: `docs/kb/hybrid/runtime.md` section 2; direct ROM-source provenance unresolved].

## Where it lives

| function or symbol | module | role | grade / citation |
|---|---|---|---|
| `OS_GetArenaLo` (`0x02115ef4`) / `OS_GetArenaHi` (`0x02115f08`) | autoload_2 | the arena's current bounds | [S: `src/matched/OS_GetArenaLo.c`, `src/matched/OS_GetArenaHi.c`; source account: `port/shim/boot/heapinit.c` header] |
| `OS_AllocFromArenaLo` (`0x02115c28`) | autoload_2 | takes the block from the low end | [S: `src/matched/OS_AllocFromArenaLo.c`; source account: `port/shim/boot/heapinit.c` header] |
| `OS_GetInitArenaHi` | autoload_2 | the arena ceiling, `0x023e0000` for the main arena | [S: `src/matched/OS_GetInitArenaHi.c`; source account: `port/shim/os/arenahi.c` header] |
| `func_020ea48c` | autoload_2 | carve the game heap; the bring-up's last call | [S: `config/adm-kr/arm9/autoload_2/symbols.txt` (`func_020ea48c` at 0x020ea48c); source account: `port/shim/boot/heapinit.c` header] |
| `func_020ea50c` / `func_020ea298` | autoload_2 | build the expanded heap at block + 0x30 | [S: `src/matched/func_020ea50c.c`, `src/matched/func_020ea298.c`; source account: `port/shim/boot/gameheap.c` header] |
| `func_020ea41c` | autoload_2 | records the block/heap arrangement in the 0x30 header | [S: `src/matched/func_020ea41c.c`; source account: `port/shim/boot/gameheap.c` header] |
| `NNS_FndCreateExpHeapEx` | main | the NNS expanded heap constructor | [S: `src/matched/NNS_FndCreateExpHeapEx.c`; source account: `port/shim/boot/gameheap.c:34`] |
| `MIi_UncompressBackward` | autoload_2 | expands a backward-compressed image in place | [H: source account: `port/shim/fs/ovlreloc.c:56`; direct ROM-source provenance unresolved] |

## Data it reads and writes

| address | meaning | who writes | who reads |
|---|---|---|---|
| `0x021fbe90` | configured game-heap size; 0 = rest of the arena | ROM data | `func_020ea48c` [S: `config/adm-kr/arm9/autoload_2/symbols.txt` (`func_020ea48c` at 0x020ea48c); source account: `port/shim/boot/heapinit.c` header] |
| `0x021fbe98` | arena id to allocate from; always set to 0 | `func_020ea48c` | `func_020ea48c` [S: `config/adm-kr/arm9/autoload_2/symbols.txt` (`func_020ea48c` at 0x020ea48c); source account: `port/shim/boot/heapinit.c` header] |
| `0x021fbe78` / `0x021fbe8c` / `0x021fbe94` | the game-heap family's pool words | `func_020ea50c` / `func_020ea298` | the allocator [S: `src/matched/func_020ea50c.c`, `src/matched/func_020ea298.c`; source account: `port/shim/boot/gameheap.c:40-43`] |
| `data_0213e5a4` | option flags the expanded heap is created with | ROM data | `func_020ea50c` [S: `src/matched/func_020ea50c.c`; source account: `port/shim/boot/gameheap.c:33-34`] |
| `0x027e0000` | `OS_IRQTable[0]`, the VBlank handler slot | `OS_SetIrqFunction` | the interrupt vector [S: `src/matched/OS_SetIrqFunction.c`; source account: `port/shim/os/vblank.c:80`] |
| `0x027e0394 + tag*4` | PXI receive-callback table | `PXI_SetFifoRecvCallback` | PXI delivery [S: `src/matched/PXI_SetFifoRecvCallback.c`; source account: `docs/kb/hybrid/hardware-services.md` section 1] |
| `0x027ffc20` | boot flag; 1 selects the second boot path | pre-`NitroMain` | `NitroMain` [H: source account: `port/platform/nitromain.c:50, 77`; direct ROM-source provenance unresolved] |
| `0x027fff9c` | the interrupt vector slot crt0 writes | `Entry` | the vector [S: `src/matched/Entry.c`; source account: `port/platform/win32.c:79-80`] |
| `0x04000208` (`REG_IME`) | interrupt master enable | `NitroMain` | the interrupt controller [H: source account: `port/platform/nitromain.c:49`; direct ROM-source provenance unresolved] |
| `0x04000004` | `DISPSTAT` low half, `VCOUNT` high half | the display controller | ROM wait loops; synthesised by the port [H: source account: `docs/kb/hybrid/hardware-services.md` section 4; direct ROM-source provenance unresolved] |
| `0x04000280`-`0x040002bf` | divider and square-root unit | `FX_Div` / `FX_Sqrt` | the same, on read [S: `src/matched/FX_Div.c`, `src/matched/FX_Sqrt.c`; source account: `docs/kb/hybrid/hardware-services.md` section 3] |
| `0x04000400`-`0x040005ff` | the GX FIFO and command ports | the geometry submission path | the geometry engine [H: source account: `docs/kb/hybrid/hardware-services.md` section 5; direct ROM-source provenance unresolved] |
| `0x04000640` / `0x04000680` | `CLIPMTX_RESULT` (16 words) / `VECMTX_RESULT` (9 words) | the geometry engine | `G3X_GetClipMtx` / `G3X_GetVectorMtx` [S: `src/matched/G3X_GetClipMtx.c`, `src/matched/G3X_GetVectorMtx.c`; source account: `docs/kb/hybrid/hardware-services.md` section 5] |

## How to check it

Any run prints the port's region report at startup, naming each reservation and its size, and
refuses to continue if a fixed-base reservation fails
[H: host/prose inference from `port/platform/win32.c:1-25, 97-112`; verify against the ROM function or symbol table and this page's recipe]. Because the mapping is at the real addresses, an
address in a fault report is directly comparable to a symbol table row: the module is the one
whose `config/adm-kr/arm9/**/symbols.txt` contains the nearest lower `addr:0x...`
[H: source account: `config/adm-kr/arm9/**/symbols.txt`; direct ROM-source provenance unresolved].

For live memory questions the interpreter carries two instruments: `ACWW_INTERP_WATCH=<hex>`
is a store watchpoint on one address, and `ACWW_INTERP_PEEK=<hex,...>` prints those words at
every dump [H: source account: `docs/log/cycle40-keyboard-gate-probe.md` CARD40..SND40, "Instruments added
this stretch"; direct ROM-source provenance unresolved].

## Hypotheses

- The port's raised arena ceiling (`0x023f0000` instead of `0x023e0000`) has no observable
  effect on game behaviour, only on how much slack a leak can hide in [H: settled by running
  the town recipe with the concession removed and comparing frames and heap-free traces;
  the file itself asks to be deleted the day the leak is found —
  `port/shim/os/arenahi.c` header].
- `autoload_3` and `dtcm` contain data only, which is why their symbol tables name no
  functions [H: settled by checking whether any branch target in another module resolves into
  their address ranges].
- The `0x021cxxxx` band is scene-lifetime state that is torn down and rebuilt per scene, while
  `0x021fxxxx` is boot-lifetime [H: settled by watching one address from each band across a
  scene change and recording whether it is rewritten].
- Nothing in the reachable game reads back a DMA register, which is why the port does not
  emulate DMA register read-back [H: settled by a load watchpoint over `0x040000b0`-`0x040000ef`
  on the town recipe; the port's position is that such a read should hang loudly rather than
  silently work — `docs/kb/hybrid/hardware-services.md` section 7].

## Related

- `boot-and-entry.md` — the bring-up call that carves the heap
- `threads-and-interrupts.md` — what lives at the bottom of DTCM
- `display-objects.md` — the `0x021fdxxx` list heads and what walks them
- `overlays.md` — the overlay band and why an address there is ambiguous
