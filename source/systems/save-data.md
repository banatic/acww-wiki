# Save data

**Summary.** Animal Crossing: Wild World keeps its town in the cartridge's backup store, a
256 KB flash chip that the DS's ARM7 processor owns and the game's ARM9 code can only reach
by asking. The game holds two save banks of 0x173fc bytes each inside that chip and chooses
between them at boot. Everything the player does -- the town, the house, the villagers, the
letters -- lives there; nothing else in the machine survives a power-off. The PC port
supplies the flash itself as a host file, and only when you ask it to. **Since 2026-09-10 the
game writes its own save through that path and a second launch reads it back**: what had
blocked it was never the card protocol but a move-in mode word the game itself clears.

## What happens

The ARM9 never touches the backup chip. It fills a command block, posts a request word into
the inter-processor FIFO on tag 11 (`PXI_FIFO_TAG_FS`), sets the `CARD_STAT_REQ` bit in the
shared card structure and puts the calling thread to sleep; the ARM7 does the transfer and
replies on the same tag, and the reply is what clears the bit and wakes the thread
[S: `CARDi_Request`, card_common, `src/matched/CARDi_Request.c`].
`CARDi_OnFifoRecv` is the ARM9-side callback that the CARD subsystem installs on that tag at
bring-up [S: `CARDi_OnFifoRecv` / `CARDi_InitCommon`, card_common,
`src/matched/CARDi_InitCommon.c`].

The request word is a small enum, and three of its members are the whole save path:
`CARD_REQ_READ_BACKUP` is 6, `CARD_REQ_WRITE_BACKUP` is 7 and `CARD_REQ_VERIFY_BACKUP` is 9
[S: `CARDRequest`, card_backup, `src/matched/CARDi_RequestStreamCommandCore.c`]. The transfer
mode is a second enum -- RECV 0, SEND 1, SEND_VERIFY 2 -- and it decides which of the command
block's `src` and `dst` words is the flash offset and which is the staging buffer
[S: `CARDRequestMode`, card_backup, `src/matched/CARDi_RequestStreamCommandCore.c`].

No transfer is ever larger than one 256-byte page. `CARDi_RequestStreamCommandCore` chops the
caller's whole request into page-sized pieces, moves each through the 256-byte
`backup_cache_page_buf` inside the shared card structure, invalidates or flushes the data
cache around it, and issues one `CARDi_Request` per piece; the flash offset accumulates in the
loop, not in the request [S: `CARDi_RequestStreamCommandCore`, card_backup,
`src/matched/CARDi_RequestStreamCommandCore.c`]. In SEND_VERIFY mode it follows each write
with request 9 on the *unchanged* command block, so the verify compares the same page buffer
against the same flash offset it just wrote [S: `CARDi_RequestStreamCommandCore`, card_backup,
`src/matched/CARDi_RequestStreamCommandCore.c`].

Two details of that loop decide how long a save takes, and both are worth stating because the
port had to reproduce them. First, **the loop does nothing at all between pages** -- no yield,
no poll, no wait on the display: it calls the per-request routine directly and goes straight
round again, so the only thing pacing it is how long a single request takes to be answered
[S: `CARDi_RequestStreamCommandCore`, card_backup,
`src/matched/CARDi_RequestStreamCommandCore.c`]. Second, that answer is awaited by putting the
calling thread to sleep on the request bit, not by spinning, and the FIFO reply is what wakes
it [S: `CARDi_Request`, card_common, `src/matched/CARDi_Request.c`; `CARDi_OnFifoRecv`,
card_common, `src/matched/CARDi_OnFifoRecv.c`]. A whole bank is 744 pages, so on the real
console the read is over in a fraction of a second; a machine that answered one page per
displayed frame would spend more than twelve seconds on it.

The busy flag the *game* watches is a different one and it is held across the whole transfer.
The asynchronous entry point takes it before handing the page loop over, the non-blocking
"is it finished yet" test is a bare read of that one bit, and it is cleared only after the last
page, by the routine that ends the task and wakes anyone waiting
[S: `CARDi_RequestStreamCommand` / `CARDi_TryWaitAsync` / `CARDi_EndTask`, card_common and
card_backup, `src/matched/CARDi_RequestStreamCommand.c`, `src/matched/CARDi_TryWaitAsync.c`,
`src/matched/CARDi_RequestStreamCommandCore.c`]. So "the request has not been answered yet" and
"the transfer is still running" are two independent facts, and only the second one is what the
game's own poll after posting a read is asking about.

The game's two entry points into that machinery are a matched pair. The asynchronous read
calls the stream command with request type 6 and mode 0 (RECV)
[S: `func_020509a8`, main, `src/matched/func_020509a8.c`]; the asynchronous write calls it
with request type 7, retry count 10 and mode 2 (SEND_VERIFY) -- so every save the game writes
is read back and checked before the call returns
[S: `func_02050a84`, main, `src/matched/func_02050a84.c`].

The medium is named in the ROM rather than guessed. `func_02050b78` passes the literal 4610,
which is 0x1202, into the identify-and-size pair, and `CARDi_IdentifyBackupCore` decodes that
packed word as device class 2 (FLASH) with a size shift of 0x12, i.e. 1 << 0x12 = 0x40000
bytes = 256 KB [S: `func_02050b78` / `func_02050b94`, main, `src/matched/func_02050b78.c`;
`CARDi_IdentifyBackupCore`, card_backup, `src/matched/CARDi_IdentifyBackupCore.c`]. The
decode is computed, not looked up: `CARDi_IdentifyBackupCore` switches on the decoded device
class and size and fills a ten-field `spec` structure (total size, sector size, page size,
address width and six timing figures) in eight case branches
[S: `CARDi_IdentifyBackupCore`, card_backup, `src/matched/CARDi_IdentifyBackupCore.c`].

The chip is divided into three slots, and the division is the ROM's own rather than an
editor's: `func_020a1cec` and `func_020a1d94` -- the only two callers of the backup write --
index the flash OFFSET out of `data_020d1c20` and the LENGTH out of `data_020d1bf0` by slot
number, and the boot-time reader `func_020a1a40` reads the same pair. Slot 0 is offset
`0x00000` length `0x173fc`, slot 1 is `0x173fc` length `0x173fc`, slot 2 is `0x337fc` length
`0xc804` -- the two banks and the letter store [S: `func_020a1cec` / `func_020a1d94` literal
pools, main; `func_020a1a40` as `port/shim/game/savepoll.c` carries it].

The two writers are not the same operation, and only one of them is a save.
`func_020a1cec(obj, slot)` fills the working buffer with 0xFF before writing it, so it ERASES a
slot; `func_020a48cc` is its seven-state driver and erases slot 0 then slot 1
[S: `func_020a1cec`, `func_020a48cc`, main]. `func_020a1d94(obj, slot)` is the save proper: it
writes **512 bytes per step**, at flash offset `data_020d1c20[slot] + (chunk << 9)` from the
buffer at the same displacement, with the chunk index a signed halfword in the save manager's
object [S: `func_020a1d94`, main]. `func_020a2120(obj, arg)` is its **seven-state driver**: the
state byte is `obj+0xa0`, the table of pointers-to-member is at `0x021f3c84` (filled once behind
a guard word at `0x021f3c2c`), **state 4 is `func_020a1d94`**, and state 6 resets the machine to
0 [S: `func_020a2120`, main; `docs/log/cycle42-save.md` SAVE42].

### How long one 256-byte page takes on the real machine

This is what fixes the pace of the boot's 744-page read, and until CARD46 it was only an
order-of-magnitude guess in the port.

The backup chip hangs off the cartridge's auxiliary SPI port, whose control register selects
one of four clocks in its low two bits: **0 = 4.19 MHz**, 1 = 2.10 MHz, 2 = 1.05 MHz,
3 = 524 kHz [P: GBATEK, [DS Cartridge Backup](https://problemkaputt.de/gbatek.htm#dscartridgebackup)
and [DS Cartridge I/O Ports](https://problemkaputt.de/gbatek.htm#dscartridgeioports), AUXSPICNT
bits 0-1]. The SDK never selects any other: its `CARDi_EnableSpi` writes the 4 MHz setting
unconditionally on every command [S: NitroSDK `libraries/card/common/src/card_spi.c`, present
locally under `tools/nitrosdk/` and not committed]. At that clock one byte is 8 bits, or
**1.908 us**.

One page on the READ path is more than its 256 data bytes. `CARDi_ReadBackupCore` sends **one**
addressing command -- 1 command byte plus the device's 3 address bytes for a 256 KB part -- and
then streams the whole requested length; the 256-byte chopping happens on the ARM9 side, in
`CARDi_RequestStreamCommandCore`, so each page pays its own command. Before it, the same
function calls `CARDi_WaitPrevCommand`, which issues a **2-byte READ_STATUS** and only sleeps if
the device reports itself busy -- which a read never does. So a page is **262 byte-transfers =
about 500 us**, and a 16.717 ms frame holds **~33 of them** [S: `card_spi.c`
`CARDi_ReadBackupCore`, `CARDi_SendSpiAddressingCommand`, `CARDi_WaitPrevCommand`;
`src/matched/CARDi_RequestStreamCommandCore.c`].

**The ARM7 inserts no wait of its own on this path.** Its task thread runs the request,
acknowledges it and loops [S: NitroSDK `libraries/card/ARM7/src/card_command.c`,
`CARDi_TaskThread`], and the read's own command tail passes a zero force-wait and a zero
timeout -- the `OS_Sleep` branch belongs to the page-program path, not to reads. 33 pages a
frame is therefore a CEILING that the ARM7's per-byte software loop (two busy polls, an
indirect call and an I/O access per byte) can only lower, never raise.

The port models this with a per-frame page budget, `ACWW_CARD_FAST` /
`CARD_FAST_HARDWARE = 32` [S: `port/shim/os/pxisend.c`; `docs/kb/hybrid/instruments.md` 3c].
Pictures cannot confirm the exact figure: measured against the original on a 10-frame grid, the
boot's copyright screen is reproduced exactly at every budget from **8** up and is identical
from 8 to 64, so the differential gives a lower bound and the arithmetic above gives the value
[E: `scratchpad/card46/copyright-table.json`, 10-frame grid; `docs/log/cycle42-save.md` CARD46].

### The save, as the game performs it

**Measured, 2026-09-10 (SAVE43).** Once the arrival is finished the game saves on its own and
the port's store takes it. Both banks are written in ONE session: **744 consecutive 256-byte
card pages from flash offset 0**, each one **verified a frame later**, covering
`0x00000000..0x0002e7f8` -- **bank 1 first, then bank 2** -- 190,456 bytes persisted, 0 verify
mismatches, 745 `FlushViewOfFile` calls [E: `scratchpad/save43/RECEIPTS.md`, run `gp-S3`'s
census; `docs/kb/hybrid/save-flow.md` section 5b]. Two card pages is one of
`func_020a1d94`'s 512-byte steps, and the verify is `func_02050a84`'s own mode-2 SEND_VERIFY
[S: those two functions]. 744 x 256 = 190,464 against `0x2e7f8` = 190,456, the last page being a
252-byte remainder. **A run that stops mid-save leaves bank 2 erased** (134 pages at one
observed stop, 501 at another) [E: same]. The letter store at `0x337fc` (slot 2) stays erased --
there is no mail yet -- so its writer is still unexercised.

The bytes satisfy the ROM's own test. `savetool.py check` on the file afterwards: bank 1
checksum stored `0xa6ad` computed `0xa6ad`, residual `0x0000`, gamecode ok, flag `+0x173fa` ok,
word sum ok -- *the game would LOAD this bank*; bank 2 the same, and a byte-identical mirror of
bank 1 [E: `scratchpad/save43/savecheck-S3.txt`].

**And the second launch takes the continue path.** A fresh launch with the same `ACWW_SAVE` and
no snapshot has the player inside their own house at frames 3,000-4,000 and standing outside
their own front door with the HUD from 5,000 -- no taxi and neither keyboard. The control is the
identical launch on an ERASED store, which gives the taxi in the rain and the player-name
keyboard [E: `boot-A` vs `boot-C`, `scratchpad/save43/png/boot-compare.png`]. The continue path
writes 8 pages of its own (2,040 bytes at `0x2400`, `0x198fc`, `0x2e5fc`, `0x2e6fc`), all
verified [E: `scratchpad/save43/RECEIPTS.md`].

**What GATES the save is not the card path at all**, and it took two cycles to find: the save
prompt refuses while the move-in mode word at `0x021f3c30` is 1 or 2 -- see the Hypotheses
below, and `../experiments/save-and-reload.md` for the chain that lifts it.

Inside those 256 KB the game keeps **two banks of 0x173fc bytes** (95,228 each).
`func_020b5724` picks between them on two flag bytes and copies a bank's worth of data from a
fixed working address, and the same function is the branch that decides whether the boot goes
to the taxi intro or straight into an existing town
[S: `func_020b5724`, main, `src/matched/func_020b5724.c`].

Access is serialised through one lock, and it is one lock for the whole cartridge rather than
one per purpose: `CARDi_LockResource` takes an owner id and a target mode of NONE, ROM or
BACKUP, and a ROM file read and a save write contend for the same `lock_owner` and `lock_ref`
[S: `CARDi_LockResource`, card_common, `src/matched/CARDi_LockResource.c`]. Asynchronous
requests are handed to a dedicated card thread, spawned at bring-up, which waits on the
`CARD_STAT_TASK` bit [S: `CARDi_TaskThread` / `CARDi_SetTask`, card_common,
`src/matched/CARDi_TaskThread.c`].

### What the port does instead

There is no ARM7 in the port, so the card protocol is answered at the request level rather
than at the FIFO level: `acww_card_arm7` performs the operation on the command block and the
reply carries `err = TRUE`, which is what the ROM's own `CARDi_OnFifoRecv` tests before
clearing `CARD_STAT_REQ` [E: `port/shim/fs/cardreq.c`, `port/shim/os/pxisend.c`;
`scratchpad/cycle40/runs/tap-D56`, frames 0..48000]. The work happens **at delivery, a frame
after the request was posted**, so the poll that immediately follows the post still sees BUSY
as it would on hardware; answering synchronously made the boot's card read restart forever at
the Nintendo logo [E: `docs/log/cycle40-keyboard-gate-probe.md` CARD40, `port/shim/os/pxisend.c`].

The backing store is off by default. With `ACWW_SAVE` unset a read leaves the destination
buffer untouched; with `ACWW_SAVE=<path>` set, the port memory-maps that file as a 256 KB
image, extends a short one, and fills the extension with 0xFF because that is what erased
flash reads [E: `port/shim/fs/cardreq.c`; `docs/kb/hybrid/hardware-services.md` section 1].
Writes are copied into the mapping and counted, and a verify compares the page buffer against
the mapping and reports a real mismatch rather than agreeing
[E: `port/shim/fs/cardreq.c`; `scratchpad/cycle40/runs/tap-D56`].

Two constants in that shim were wrong in ways worth recording, because both failures were
silent. The status bit spelled `CARD_STAT_INIT_CMD` had been written as 0x40, which is
`CARD_STAT_CANCEL`, so every answered request also raised the cancel bit and
`CARDi_RequestStreamCommandCore` -- which tests exactly that bit first -- returned
CARD_RESULT_CANCELED; every save read came back as "the read FAILED" rather than "there is no
save" [E: `port/shim/fs/cardreq.c`; the correct values are
`src/matched/CARD_CancelBackupAsync.c`'s INIT 1, INIT_CMD 2, BUSY 4, TASK 8, RECV 16, REQ 32,
CANCEL 64]. And the read request number had been written as 5, while the game issues 6, so the
0xFF-erased fill never executed once [H: host-source account from `port/shim/fs/cardreq.c`, settled against
`src/matched/func_020509a8.c`; verify with a retained scripted run and frame using this page's recipe].

**An erased store is 0xFF, and a zeroed one is a different game.** A block of zeros is not an
absent save; it is a save whose header and checksum are zero, which the game reads as damaged
[H: inferred from `func_020b5724`'s bank validity test; settled by running with `ACWW_SAVE`
pointed at an all-zero file and looking for the damaged-save path]. When the read fill was
corrected to 0xFF the keyed START run stopped at `unimplemented: func_02225a90` around frame
10 — the port's stop line quotes a bare address; the symbol tables name that function
`func_ov003_02225a90` [S: `config/adm-kr/arm9/overlays/ov003/symbols.txt`] — where the same
build with the fill off runs clean -- so the honest answer moves the boot
onto a path the port cannot yet follow [H: host-source account from `port/shim/fs/cardreq.c`, keyed START, frame ~10; verify with a retained scripted run and frame using this page's recipe].

## Where it lives

| function or symbol | module | role | grade/citation |
|---|---|---|---|
| `CARDi_Request` | autoload_2 (card_common) | posts the request word on PXI tag 11, sleeps on `CARD_STAT_REQ`, retries on timeout | [S: `src/matched/CARDi_Request.c`] |
| `CARDi_RequestStreamCommand` | autoload_2 (card_backup) | public entry: stores src/dst/len/callback, sets BUSY, runs the core directly or posts it as a task | [S: `src/matched/CARDi_RequestStreamCommand.c`] |
| `CARDi_RequestStreamCommandCore` | autoload_2 (card_backup) | the 256-byte page loop, the cancel check, the SEND_VERIFY follow-up | [S: `src/matched/CARDi_RequestStreamCommandCore.c`] |
| `CARDi_IdentifyBackupCore` | autoload_2 (card_backup) | decodes a packed `CARDBackupType` into the ten-field device spec | [S: `src/matched/CARDi_IdentifyBackupCore.c`] |
| `CARD_GetBackupTotalSize` | autoload_2 (card_backup) | returns the decoded total size | [S: `src/matched/CARD_GetBackupTotalSize.c`] |
| `CARD_CancelBackupAsync` | autoload_2 (card_backup) | raises `CARD_STAT_CANCEL` under interrupts disabled | [S: `src/matched/CARD_CancelBackupAsync.c`] |
| `CARDi_LockResource` | autoload_2 (card_common) | one lock for ROM and BACKUP alike, by owner id and target mode | [S: `src/matched/CARDi_LockResource.c`] |
| `CARDi_TaskThread` / `CARDi_SetTask` | autoload_2 (card_common) | the dedicated card thread and how work is posted to it | [S: `src/matched/CARDi_TaskThread.c`] |
| `CARDi_OnFifoRecv` | autoload_2 (card_common) | the ARM9's reply callback on `PXI_FIFO_TAG_FS` | [S: `src/matched/CARDi_OnFifoRecv.c`] |
| `CARD_GetResultCode` | autoload_2 (card_common) | returns the command block's `result` word | [S: `src/matched/CARD_GetResultCode.c`] |
| `func_020509a8` | main | the game's asynchronous backup read (type 6, RECV) | [S: `src/matched/func_020509a8.c`] |
| `func_02050a84` | main | the game's asynchronous backup write (type 7, retry 10, SEND_VERIFY) | [S: `src/matched/func_02050a84.c`] |
| `func_02050b78` / `func_02050b94` | main | identify as FLASH 2 Mbit (0x1202) and read back the total size | [S: `src/matched/func_02050b78.c`] |
| `func_020b5724` | main | chooses between the two 0x173fc-byte banks; the fresh-town / existing-town branch | [S: `src/matched/func_020b5724.c`] |
| `func_020a1a40`, `func_020b5898` | main | the boot-time pollers that drive the read state machine (3 = still busy) | [S: `src/matched/func_020a1a40.c`, `src/matched/func_020b5898.c`] |
| `func_020a1d94` / `func_020a2120` | main | the 512-bytes-per-step bank writer, and the seven-state driver whose state 4 runs it | [S: those two functions; `docs/log/cycle42-save.md` SAVE42] |
| `func_0209f6e4` | main | the save prompt's branch: `sp_etc_sequence4` message 4 (refuse) or `sp_etc_sequence2` (the real menu) | [S: `func_0209f6e4`, main] |
| `func_020a128c` / `func_020a12c0` / `func_020a12d4` | main | the move-in mode accessors on `0x021f3c30`: `:= 0`, `== 2`, `== 1` | [S: the ROM; E: `gp-W0`'s store watchpoint, `docs/log/cycle42-save.md` SAVE43] |
| `CARD_GetCurrentBackupType` | -- | **misidentified in the tree**: this address is `DWC_Netcheck_GetReturnCode`, not a CARD function | [S: header comment, `src/matched/CARD_GetCurrentBackupType.c`] |

## Data it reads and writes

| address or field | meaning | who writes | who reads |
|---|---|---|---|
| command block `+0x00` `result` | `CARDResult` for the last request | the ARM7 (the port's `acww_card_arm7`) | `CARD_GetResultCode` [S: `src/matched/CARD_GetResultCode.c`] |
| command block `+0x10` `src` | flash offset on a read; page buffer on a write | `CARDi_RequestStreamCommandCore` | the ARM7 [S: `src/matched/CARDi_RequestStreamCommandCore.c`] |
| command block `+0x14` `dst` | page buffer on a read; flash offset on a write | `CARDi_RequestStreamCommandCore` | the ARM7 [S: same] |
| command block `+0x18` `len` | bytes this request moves, never above 256 | `CARDi_RequestStreamCommandCore` | the ARM7 [S: same] |
| `spec` sub-block | total size, sector size, page size, address width, six timings | `CARDi_IdentifyBackupCore` | `CARD_GetBackupTotalSize`, `CARD_GetBackupPageSize` [S: `src/matched/CARDi_IdentifyBackupCore.c`] |
| `cardi_common.flag` | INIT 1, INIT_CMD 2, BUSY 4, TASK 8, RECV 16, REQ 32, CANCEL 64 | `CARDi_Request`, `CARD_CancelBackupAsync`, the reply path | the core loop and the waiters [S: `src/matched/CARD_CancelBackupAsync.c`] |
| `cardi_common.backup_cache_page_buf` | the 256-byte DMA-safe staging page every transfer passes through | `CARDi_RequestStreamCommandCore` | the ARM7 [S: `src/matched/CARDi_RequestStreamCommandCore.c`] |
| flash `0x00000`..`0x3ffff` | the 256 KB store; two banks of 0x173fc bytes | the ARM7 on request 7 | the ARM7 on request 6 [S: `src/matched/func_020b5724.c`, `src/matched/func_02050b78.c`] |
| `0x021dc7a8` | the working copy `func_020b5724` copies 0x173fc bytes from | the game | `func_020b5724` [S: `src/matched/func_020b5724.c`] |
| player slot `+0x1bf2`, 15x u16 | the pockets; `0xfff1` is an empty slot | `func_02098f0c` (bounds-checked by `func_02098f70`) | `func_02098f48` [S: those three; E: GAMEPLAY47 `g47-SLOTW`, a store watchpoint on `0x021de3ae`] |
| player slot `+0x2408` u16 | **the WORN SHIRT.** A drop from the pockets onto the character swaps them, and the old one returns to the pocket iff it is in the shirt band `0x11a8..0x12a7` | `func_02099704`, called from `func_ov096_0229e3b0` case 2 (ov096's equip dispatcher) | `func_02099710` [S: those three, all matched; E: GAMEPLAY47 `g47-WEARW`, a store watchpoint on `0x021debc4`; `savetool.py check` prints it] |
| `0x021f3c30` | the **move-in mode** word: 1 or 2 refuses the save, 0 allows it | `func_ov147_02299414` / `func_ov147_022997ec` / `func_020a4454` (non-zero), `func_020a128c` (zero) | `func_020a12c0` / `func_020a12d4`, read by `func_0209f6e4` [S: the ROM; E: `gp-W0`] |
| `obj+0xa0`, table `0x021f3c84` | the save driver's state byte and its seven pointers-to-member | `func_020a2120` | `func_020a2120` [S: `func_020a2120`, main] |

## How to check it

That check has now been run, and the shim prints a full census at the stop frame rather than
one line per distinct request type -- **but only since SAVE42**: `acww_card_report()` had no
caller between SAVEFLOW41 and 2026-09-10, so the census printed nothing in between and only
the per-request span lines were evidence [E: `port/platform/frame.c`;
`docs/log/cycle42-save.md`]. The whole 48,000-frame town recipe with a freshly erased
`ACWW_SAVE` issues **746 backup reads (190,456 bytes, both banks, at frame 10), one write and
one verify -- of a single byte at `0x3fffc`** -- and leaves both banks 0xFF
[E: `scratchpad/saveflow/runs/town1`; `port/shim/fs/cardreq.c`'s census;
`../experiments/save-and-reload.md`]. That is the census of a run that never reaches the save.
The census of one that DOES is `744 requests, 190456 bytes` of type 7 and the same of type 9
[E: `scratchpad/save43/RECEIPTS.md`]. Read the two side by side: they are the same instrument on
either side of the move-in gate.

    python -B scratchpad/saveflow/run_sf.py <name> ACWW_INTERP=1 ... "ACWW_SAVE=@SF@\x.sav"
    python port/tools/savetool.py check <the same absolute path>

`run_sf.py` rather than `run_direct.py` because `ACWW_STATE_SAVE`'s `<frame>:<path>` value is
rewritten by MSYS bash, and because another session's `taskkill /F /IM acww.exe` ends any run
launched under that name [E: `../experiments/save-and-reload.md`].

## Hypotheses

- ~~The save record carries a checksum, but none has been found.~~ **Settled 2026-09-09, and
  the search had been looking in the wrong place: the routine is not called `crc` or
  `checksum`.** `func_020a1a40` -- the boot-time poller, carried verbatim in
  `port/shim/game/savepoll.c` -- decides whether a bank is a save with exactly two calls once
  the card read completes. `func_02050920(buffer, data_020d1c08[slot])` is a plain 16-bit
  wrapping sum of little-endian words over the whole slot, no skip and no seed, and the bank is
  accepted only when that sum is **zero**; `func_0209f180(buffer)` is the other half, and it is
  two byte tests, `buffer[0] == 0x32` and (through `func_0209fb3c`) `buffer[0x173fa] == 2`
  [S: `src/matched/func_02050920.c`, `src/matched/func_0209f180.c`,
  `src/matched/func_0209fb3c.c`; `port/shim/game/savepoll.c`]. Summing to zero is precisely
  the property the stored two's-complement word at `+0x173f8` creates, so the algorithm the
  public editors implement is the ROM's [S: as above; `port/tools/savetool.py`'s docstring].
  The three tests are independent -- a perfect checksum with a wrong flag byte is still
  rejected -- which `port/tools/savetool.py`'s `rom_accepts()` reports separately and
  `port/tools/test_savetool.py::test_rom_acceptance_rule_on_a_synthetic_bank` calibrates on a
  synthetic bank.
- ~~The two banks are a primary/backup pair rather than two independent slots.~~ **Half-settled
  (SAVE43): after ONE in-game save bank 2 is a byte-identical mirror of bank 1**, and both are
  written in the same session, in order [E: `scratchpad/save43/savecheck-S3.txt`]. Whether a
  SECOND save alternates them or rewrites both is still open, and the experiment is unchanged:
  save twice and diff the two ranges.
- 0xFF is what an unused ACWW save area reads, and the game distinguishes 0xFF-erased from
  zeroed. Half-settled: an all-0xFF store does NOT derail the interpreter path -- the town
  recipe runs 48,000 frames with no fault and no `unimplemented` line
  [E: `scratchpad/saveflow/runs/town1`]. The all-zero arm has still not been run.
- ~~The `unimplemented: func_02225a90` stop that follows an honest 0xFF read is the
  existing-save load path.~~ That stop is a NATIVE-path observation and does not reproduce on
  the interpreter path with a real store [E: `scratchpad/saveflow/runs/town1`, exit 100 at
  48,000 frames]. Whether it is still reachable natively is now a question about the native
  path only.
- The one byte written at `0x3fffc` at frame 757 is the store's writability probe -- the ROM
  checking that the chip it identified as 256 KB flash accepts a write at its last address.
  Evidence for: one byte, at the very end of the device, once, immediately verified
  [E: `scratchpad/saveflow/runs/town1`'s census]. Settled by reading the caller; the census
  gives the frame to break on. A run that actually saves shows it separately: `gp-S3`'s census
  is 744 type-7 requests over `0x00000000..0x0002e7f8` and no request at `0x3fffc` in that span
  [E: `scratchpad/save43/RECEIPTS.md`].
- ~~A played town survives a relaunch. Completely unmeasured, and blocked: no script reaches a
  point where the game would save.~~ **SETTLED 2026-09-10 (SAVE43): it does.** The game writes
  both banks itself, `savetool.py`'s `rom_accepts()` accepts them, and a fresh launch on the
  same store boots into the saved town -- see "The save, as the game performs it" above and
  `../experiments/save-and-reload.md`. The intermediate SAVE42 reading, kept because the rule it
  found is the content: **a script reaches the save prompt and the GAME refuses.** The prompt's branch is `func_0209f6e4`: it attaches
  the script `sp_etc_sequence4` and asks for message 4 -- `지금은 아직 저장하지 못하나 봐요` --
  iff `func_020a12d4() || func_020a12c0()`, that is iff the play-mode word at `0x021f3c30` is
  1 or 2; otherwise it attaches `sp_etc_sequence2`, the real save menu
  [S: `func_0209f6e4` / `func_020a12c0` / `func_020a12d4`, main; the two archive names are the
  literals at `0x020e37d0` and `0x020e37e4`, immediately before the member table at
  `0x020e3810`]. The word is 1 through the whole move-in session
  [E: `scratchpad/save42/stpeek.py` on `st/town48000.st`]; its writers to non-zero values are
  `func_ov147_02299414` (`:= 1`), `func_ov147_022997ec` (`:= 2`, `:= 3`) and `func_020a4454`
  (`:= 3`, `:= 4`), all in or around the move-in overlay. It is not an opening-DAY rule and the
  RTC cannot lift it: two arms from one snapshot at `20050615` and `20050616` give the identical
  refusal with the HUD showing the two different dates
  [E: `scratchpad/save42/rtc0_a.png`, `rtc1_a.png`; `docs/log/cycle42-save.md` SAVE42].
  ~~**No function writes 0**, so 0 is the BSS default.~~ **RETRACTED 2026-09-10 (SAVE43):**
  the accessor family is TEN functions, not nine. `func_020a128c` is `mode := 0` (pool word
  `0x020a1294`) and it has two callers, `func_0209ec74` (main) and `func_ov068_0226e648`; a
  store watchpoint caught it firing [S: the ROM; E: `gp-W0`, `acww interp: WATCH store to
  0x021f3c30 value 0x00000000 width 4 at pc 0x020a1290`]. **The gate is lifted by the game
  itself** when Nook's speech at the player's own house ends -- between frame 61,000 (still 1)
  and 63,000 (0) on that chain -- and `func_0209f6e4` then routes START to `sp_etc_sequence2`
  message 0, the real save menu. **The attic bed is one save point, not the rule**; what the
  arrival needs is that the player ENTERS THEIR OWN HOUSE
  [E: `docs/log/cycle42-save.md` SAVE43; `../experiments/save-and-reload.md`].
- ~~The save is triggered by putting the manager's object into the state that runs
  `func_020a1d94`, and the driver has to be found through the member table.~~ **Settled
  (SAVE42): the driver is `func_020a2120(obj, arg)`** -- a seven-state machine whose state
  byte is `obj+0xa0`, whose table of pointers-to-member is at `0x021f3c84` (filled once behind
  a guard word at `0x021f3c2c`), and whose **state 4 is `func_020a1d94`**, the 512-bytes-per-
  step bank writer; state 6 resets the machine to 0 [S: `func_020a2120`, main].

## Related

- `../experiments/save-store-probe.md` -- the recipe for the checks above (not yet run).
- `../experiments/two-tap-town-recipe.md` -- the run every save observation is taken under.
- `../experiments/gameplay-walkthrough.md` -- the SAVE43 chain, frame by frame.
- `time-and-rtc.md` -- the other piece of persistent state the game reads at boot; the RTC arm
  that proved the refusal is not a date rule is there and in `save-and-reload.md`.
- `../audits/night-2026-09-09.md` -- SAVEFLOW41, SAVE42 and SAVE43 in the night's index.
