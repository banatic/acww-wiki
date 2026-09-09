# Save data

**Summary.** Animal Crossing: Wild World keeps its town in the cartridge's backup store, a
256 KB flash chip that the DS's ARM7 processor owns and the game's ARM9 code can only reach
by asking. The game holds two save banks of 0x173fc bytes each inside that chip and chooses
between them at boot. Everything the player does -- the town, the house, the villagers, the
letters -- lives there; nothing else in the machine survives a power-off. The PC port
supplies the flash itself as a host file, and only when you ask it to.

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
0xFF-erased fill never executed once [E: `port/shim/fs/cardreq.c`, settled against
`src/matched/func_020509a8.c`].

**An erased store is 0xFF, and a zeroed one is a different game.** A block of zeros is not an
absent save; it is a save whose header and checksum are zero, which the game reads as damaged
[H: inferred from `func_020b5724`'s bank validity test; settled by running with `ACWW_SAVE`
pointed at an all-zero file and looking for the damaged-save path]. When the read fill was
corrected to 0xFF the keyed START run stopped at `unimplemented: func_02225a90` around frame
10 — the port's stop line quotes a bare address; the symbol tables name that function
`func_ov003_02225a90` [S: `config/adm-kr/arm9/overlays/ov003/symbols.txt`] — where the same
build with the fill off runs clean -- so the honest answer moves the boot
onto a path the port cannot yet follow [E: `port/shim/fs/cardreq.c`, keyed START, frame ~10].

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

## How to check it

The port never writes a save on any recipe measured so far, so the first check is negative and
cheap: run the town recipe (see `../experiments/two-tap-town-recipe.md`) with `ACWW_SAVE`
pointed at a fresh path, and confirm afterwards that the file is still 256 KB of 0xFF and that
the log carries `acww card: request type 6` but no `acww save: persisted N bytes` line
[E: `port/shim/fs/cardreq.c`'s instruments; no such run is recorded yet, so this is the
experiment `../experiments/save-store-probe.md` describes].

## Hypotheses

- The save record carries a checksum, but none has been found. Every `crc`/`checksum` symbol
  in `src/matched` belongs to the wireless, socket or PPP/TCP stack (`MATH_CalcCRC8/16/32`,
  `MBi_calc_cksum`, `check_tcpudpsum`), and no call edge runs from any of them into
  `func_020509a8` / `func_02050a84` [S: absence in `src/matched`]. Settled by disassembling
  `func_020b5724`'s bank-validity test and naming what it computes over the bank.
- The two banks are a primary/backup pair rather than two independent slots. Settled by
  making the port persist a save (see above), then diffing the two bank ranges of the
  resulting file after one and after two in-game saves.
- 0xFF is what an unused ACWW save area reads, and the game distinguishes 0xFF-erased from
  zeroed. Settled by running the same recipe twice with `ACWW_SAVE` on an all-0xFF file and on
  an all-zero file and comparing the boot branch each takes.
- The `unimplemented: func_02225a90` stop that follows an honest 0xFF read is the
  existing-save load path, not a defect in the fill. Settled by running with `ACWW_EXPLORE=1`
  and reading which caller reaches that address [E: `port/shim/fs/cardreq.c`, keyed START].

## Related

- `../experiments/save-store-probe.md` -- the recipe for the checks above (not yet run).
- `../experiments/two-tap-town-recipe.md` -- the run every save observation is taken under.
- `time-and-rtc.md` -- the other piece of persistent state the game reads at boot.
