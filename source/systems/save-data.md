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

The ARM9 never touches the backup chip. It fills a command block, posts a request word into the inter-processor FIFO on tag 11 (`PXI_FIFO_TAG_FS`), sets the `CARD_STAT_REQ` bit in the shared card structure and puts the calling thread to sleep; the ARM7 does the transfer and
replies on the same tag, and the reply is what clears the bit and wakes the thread [S: `CARDi_Request`, card_common, `src/matched/CARDi_Request.c`]. `CARDi_OnFifoRecv` is the ARM9-side callback that the CARD subsystem installs on that tag at bring-up [S: `CARDi_OnFifoRecv` /
`CARDi_InitCommon`, card_common, `src/matched/CARDi_InitCommon.c`].

The request word is a small enum, and three of its members are the whole save path: `CARD_REQ_READ_BACKUP` is 6, `CARD_REQ_WRITE_BACKUP` is 7 and `CARD_REQ_VERIFY_BACKUP` is 9 [S: `CARDRequest`, card_backup, `src/matched/CARDi_RequestStreamCommandCore.c`]. The transfer mode is a
second enum -- RECV 0, SEND 1, SEND_VERIFY 2 -- and it decides which of the command block's `src` and `dst` words is the flash offset and which is the staging buffer [S: `CARDRequestMode`, card_backup, `src/matched/CARDi_RequestStreamCommandCore.c`].

No transfer is ever larger than one 256-byte page. `CARDi_RequestStreamCommandCore` chops the caller's whole request into page-sized pieces, moves each through the 256-byte `backup_cache_page_buf` inside the shared card structure, invalidates or flushes the data cache around it,
and issues one `CARDi_Request` per piece; the flash offset accumulates in the loop, not in the request [S: `CARDi_RequestStreamCommandCore`, card_backup, `src/matched/CARDi_RequestStreamCommandCore.c`]. In SEND_VERIFY mode it follows each write with request 9 on the *unchanged*
command block, so the verify compares the same page buffer against the same flash offset it just wrote [S: `CARDi_RequestStreamCommandCore`, card_backup, `src/matched/CARDi_RequestStreamCommandCore.c`].

Two details of that loop decide how long a save takes, and both are worth stating because the port had to reproduce them. First, **the loop does nothing at all between pages** -- no yield, no poll, no wait on the display: it calls the per-request routine directly and goes
straight round again, so the only thing pacing it is how long a single request takes to be answered [S: `CARDi_RequestStreamCommandCore`, card_backup, `src/matched/CARDi_RequestStreamCommandCore.c`]. Second, that answer is awaited by putting the calling thread to sleep on the
request bit, not by spinning, and the FIFO reply is what wakes it [S: `CARDi_Request`, card_common, `src/matched/CARDi_Request.c`; `CARDi_OnFifoRecv`, card_common, `src/matched/CARDi_OnFifoRecv.c`]. A whole bank is 744 pages, so on the real console the read is over in a fraction
of a second; a machine that answered one page per displayed frame would spend more than twelve seconds on it.

The busy flag the *game* watches is a different one and it is held across the whole transfer. The asynchronous entry point takes it before handing the page loop over, the non-blocking "is it finished yet" test is a bare read of that one bit, and it is cleared only after the last
page, by the routine that ends the task and wakes anyone waiting [S: `CARDi_RequestStreamCommand` / `CARDi_TryWaitAsync` / `CARDi_EndTask`, card_common and card_backup, `src/matched/CARDi_RequestStreamCommand.c`, `src/matched/CARDi_TryWaitAsync.c`,
`src/matched/CARDi_RequestStreamCommandCore.c`]. So "the request has not been answered yet" and "the transfer is still running" are two independent facts, and only the second one is what the game's own poll after posting a read is asking about.

The game's two entry points into that machinery are a matched pair. The asynchronous read calls the stream command with request type 6 and mode 0 (RECV) [S: `func_020509a8`, main, `src/matched/func_020509a8.c`]; the asynchronous write calls it with request type 7, retry count 10
and mode 2 (SEND_VERIFY) -- so every save the game writes is read back and checked before the call returns [S: `func_02050a84`, main, `src/matched/func_02050a84.c`].

The medium is named in the ROM rather than guessed. `func_02050b78` passes the literal 4610, which is 0x1202, into the identify-and-size pair, and `CARDi_IdentifyBackupCore` decodes that packed word as device class 2 (FLASH) with a size shift of 0x12, i.e. 1 << 0x12 = 0x40000
bytes = 256 KB [S: `func_02050b78` / `func_02050b94`, main, `src/matched/func_02050b78.c`; `CARDi_IdentifyBackupCore`, card_backup, `src/matched/CARDi_IdentifyBackupCore.c`]. The decode is computed, not looked up: `CARDi_IdentifyBackupCore` switches on the decoded device class
and size and fills a ten-field `spec` structure (total size, sector size, page size, address width and six timing figures) in eight case branches [S: `CARDi_IdentifyBackupCore`, card_backup, `src/matched/CARDi_IdentifyBackupCore.c`].

The chip is divided into three slots, and the division is the ROM's own rather than an editor's: `func_020a1cec` and `func_020a1d94` -- the only two callers of the backup write -- index the flash OFFSET out of `data_020d1c20` and the LENGTH out of `data_020d1bf0` by slot number,
and the boot-time reader `func_020a1a40` reads the same pair. Slot 0 is offset `0x00000` length `0x173fc`, slot 1 is `0x173fc` length `0x173fc`, slot 2 is `0x337fc` length `0xc804` -- the two banks and a third region [S: `func_020a1cec` / `func_020a1d94` literal pools, main;
`func_020a1a40` as `port/shim/game/savepoll.c` carries it; source locator: `src/matched/func_020a1cec.c`, `src/matched/func_020a1d94.c`, `config/adm-kr/arm9/symbols.txt (`main` at 0x02000c38)`, `src/matched/func_020a1a40.c`]. **~~Slot 2 is the letter store.~~ RETRACTED by GP58-2**: a letter lives inside bank 1, and the correction is in "A letter is a player field" below.

The two writers are not the same operation, and only one of them is a save. `func_020a1cec(obj, slot)` fills the working buffer with 0xFF before writing it, so it ERASES a slot; `func_020a48cc` is its seven-state driver and erases slot 0 then slot 1 [S: `func_020a1cec`,
`func_020a48cc`, main; source locator: `src/matched/func_020a1cec.c`, `src/matched/func_020a48cc.c`, `config/adm-kr/arm9/symbols.txt (`main` at 0x02000c38)`]. `func_020a1d94(obj, slot)` is the save proper: it writes **512 bytes per step**, at flash offset `data_020d1c20[slot] + (chunk << 9)` from the buffer at the same displacement, with the chunk index a signed halfword in the save manager's object [S: `func_020a1d94`, main; source locator: `src/matched/func_020a1d94.c`, `config/adm-kr/arm9/symbols.txt (`main` at 0x02000c38)`]. `func_020a2120(obj, arg)` is its **seven-state driver**: the state byte is `obj+0xa0`, the table of pointers-to-member is at `0x021f3c84` (filled once behind a guard word at `0x021f3c2c`), **state 4 is `func_020a1d94`**, and state 6 resets the machine to 0
[S: `func_020a2120`, main; `docs/log/cycle42-save.md` SAVE42; source locator: `src/matched/func_020a2120.cpp`, `config/adm-kr/arm9/symbols.txt (`main` at 0x02000c38)`].

### How long one 256-byte page takes on the real machine

This is what fixes the pace of the boot's 744-page read, and until CARD46 it was only an order-of-magnitude guess in the port.

The backup chip hangs off the cartridge's auxiliary SPI port, whose control register selects
one of four clocks in its low two bits: **0 = 4.19 MHz**, 1 = 2.10 MHz, 2 = 1.05 MHz,
3 = 524 kHz [P: GBATEK, [DS Cartridge Backup](https://problemkaputt.de/gbatek.htm#dscartridgebackup)
and [DS Cartridge I/O Ports](https://problemkaputt.de/gbatek.htm#dscartridgeioports), AUXSPICNT
bits 0-1]. The SDK never selects any other: its `CARDi_EnableSpi` writes the 4 MHz setting
unconditionally on every command [H: source account: NitroSDK `libraries/card/common/src/card_spi.c`, present
locally under `tools/nitrosdk/` and not committed; direct ROM-source provenance unresolved]. At that clock one byte is 8 bits, or
**1.908 us**.

One page on the READ path is more than its 256 data bytes. `CARDi_ReadBackupCore` sends **one** addressing command -- 1 command byte plus the device's 3 address bytes for a 256 KB part -- and then streams the whole requested length; the 256-byte chopping happens on the ARM9 side,
in `CARDi_RequestStreamCommandCore`, so each page pays its own command. Before it, the same function calls `CARDi_WaitPrevCommand`, which issues a **2-byte READ_STATUS** and only sleeps if the device reports itself busy -- which a read never does. So a page is **262
byte-transfers = about 500 us**, and a 16.717 ms frame holds **~33 of them** [S: `card_spi.c` `CARDi_ReadBackupCore`, `CARDi_SendSpiAddressingCommand`, `CARDi_WaitPrevCommand`; `src/matched/CARDi_RequestStreamCommandCore.c`].

**The ARM7 inserts no wait of its own on this path.** Its task thread runs the request,
acknowledges it and loops [S: NitroSDK `libraries/card/ARM7/src/card_command.c`,
`CARDi_TaskThread`], and the read's own command tail passes a zero force-wait and a zero
timeout -- the `OS_Sleep` branch belongs to the page-program path, not to reads. 33 pages a
frame is therefore a CEILING that the ARM7's per-byte software loop (two busy polls, an
indirect call and an I/O access per byte) can only lower, never raise.

The port models this with a per-frame page budget, `ACWW_CARD_FAST` / `CARD_FAST_HARDWARE = 32` [H: source account: `port/shim/os/pxisend.c`; `docs/kb/hybrid/instruments-runtime.md` 3c; direct ROM-source provenance unresolved]. Pictures cannot confirm the exact figure: measured against
the original on a 10-frame grid, the boot's copyright screen is reproduced exactly at every budget from **8** up and is identical from 8 to 64, so the differential gives a lower bound and the arithmetic above gives the value [E: `scratchpad/card46/copyright-table.json`, 10-frame
grid; `docs/log/cycle42-save.md` CARD46].

### The save, as the game performs it

**Measured, 2026-09-10 (SAVE43).** Once the arrival is finished the game saves on its own and
the port's store takes it. Both banks are written in ONE session: **744 consecutive 256-byte
card pages from flash offset 0**, each one **verified a frame later**, covering
`0x00000000..0x0002e7f8` -- **bank 1 first, then bank 2** -- 190,456 bytes persisted, 0 verify
mismatches, 745 `FlushViewOfFile` calls [E: `scratchpad/save43/RECEIPTS.md`, run `gp-S3`'s
census; `docs/kb/hybrid/save-flow.md` section 5b]. Two card pages is one of
`func_020a1d94`'s 512-byte steps, and the verify is `func_02050a84`'s own mode-2 SEND_VERIFY
[S: `src/matched/func_020a1d94.c`, `src/matched/func_02050a84.c`; historical account: those two functions]. 744 x 256 = 190,464 against `0x2e7f8` = 190,456, the last page being a
252-byte remainder. **A run that stops mid-save leaves bank 2 erased** (134 pages at one
observed stop, 501 at another) [E: `scratchpad/save43/RECEIPTS.md`]. The slot-2 region at
`0x337fc` stays erased and its writer is still unexercised; SAVE43 read that as "there is no mail
yet", which GAMEPLAY58 refuted (below).

## A letter is a player field, and it is not in slot 2

MEASURED (GAMEPLAY58) [E: `docs/log/cycle41-gameplay.md` GP58-2; saves `scratchpad/gameplay58/town6.sav`, `scratchpad/gameplay57/town5.sav`, `town5-mail.sav`]. A save written on the day a prepaid catalogue order was DELIVERED, with the letter in the mailbox, still prints `beyond
the banks: 0x11808 bytes from 0x2e7f8 -- 0 of them not 0xFF`. The letter is inside bank 1, as a **player** field:

* **Ten records of `0x100` bytes at player offset `0x11AC`.** Player 0's array is
  `0x011c0..0x01bbf`. The same shape sits at `0x14 + p*0x249c + 0x11ac` for p = 0..3, which is
  what makes it a player field rather than a town one.
* **The attached present is a `u16` at record `+0xF8`**, `0xFFF1` when there is none. Taking the
  present in game changed exactly three bytes of the 256: `+0xF8` from the item's id to `0xFFF1`,
  and the low byte of `+0xF6`. Everything from `+0x00` to `+0xF3` was untouched.
* **The record's header is the ADDRESSEE, copied from fields already named here.** `+0x00` (2)
  town id equals the bank's `+0x0002`; `+0x02` (12) town name equals the bank's `+0x0004`;
  `+0x0E` (2) player id equals that player's `+0x248c`; `+0x10` (8) player name equals their
  `+0x248e`. Compared byte for byte.
* **Text ranges, cited and not read:** `+0x40` the salutation, `+0x54` the body (up to 30
  UTF-16LE units, `0x000A` for a line break), `+0xD4` the signature. `+0x1E` is `0x02` on a live
  record and `0x00` on an unused one; `+0x3E` is `0x0004`; `+0xF4` is `0x1804`.
* **A second ten-slot array of the same shape at bank offset `0x15958`**, outside every player
  record, held the identical 256 bytes on the day the order was PLACED and was empty on the day
  it arrived. HYPOTHESIS: the outstanding-delivery queue. Untested.

`port/tools/savetool.py check` prints the census under each player -- slot, offset, addressee ids and the present's id -- and reads no letter text. **An unused slot is zeroed except for `0xFFF1` at `+0xF8`, so the emptiness test is the addressee's town id and not "all zero".**

MEASURED (GAMEPLAY58), **and it is what makes a two-save diff usable: the image is a deterministic function of the recipe.** Two identical boots of one store on one date, each followed by the same START save, gave two files with the same SHA256 (`8164a549...`) and 0 differing
bytes in bank 1.

The bytes satisfy the ROM's own test. `savetool.py check` on the file afterwards: bank 1 checksum stored `0xa6ad` computed `0xa6ad`, residual `0x0000`, gamecode ok, flag `+0x173fa` ok, word sum ok -- *the game would LOAD this bank*; bank 2 the same, and a byte-identical mirror of
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

Inside those 256 KB the game keeps **two banks of 0x173fc bytes** (95,228 each). `func_020b5724` picks between them on two flag bytes and copies a bank's worth of data from a fixed working address, and the same function is the branch that decides whether the boot goes to the taxi
intro or straight into an existing town [S: `func_020b5724`, main, `src/matched/func_020b5724.c`].

Access is serialised through one lock, and it is one lock for the whole cartridge rather than one per purpose: `CARDi_LockResource` takes an owner id and a target mode of NONE, ROM or BACKUP, and a ROM file read and a save write contend for the same `lock_owner` and `lock_ref`
[S: `CARDi_LockResource`, card_common, `src/matched/CARDi_LockResource.c`]. Asynchronous requests are handed to a dedicated card thread, spawned at bring-up, which waits on the `CARD_STAT_TASK` bit [S: `CARDi_TaskThread` / `CARDi_SetTask`, card_common,
`src/matched/CARDi_TaskThread.c`].

### What the port does instead

There is no ARM7 in the port, so the card protocol is answered at the request level rather than at the FIFO level: `acww_card_arm7` performs the operation on the command block and the reply carries `err = TRUE`, which is what the ROM's own `CARDi_OnFifoRecv` tests before clearing
`CARD_STAT_REQ` [E: `port/shim/fs/cardreq.c`, `port/shim/os/pxisend.c`; `scratchpad/cycle40/runs/tap-D56`, frames 0..48000]. The work happens **at delivery, a frame after the request was posted**, so the poll that immediately follows the post still sees BUSY as it would on
hardware; answering synchronously made the boot's card read restart forever at the Nintendo logo [H: log/source account: `docs/log/cycle40-keyboard-gate-probe.md` CARD40, `port/shim/os/pxisend.c`; receipt provenance unresolved].

The backing store is off by default. With `ACWW_SAVE` unset a read leaves the destination buffer untouched; with `ACWW_SAVE=<path>` set, the port memory-maps that file as a 256 KB image, extends a short one, and fills the extension with 0xFF because that is what erased flash
reads [H: log/source account: `port/shim/fs/cardreq.c`; `docs/kb/hybrid/hardware-services.md` section 1; receipt provenance unresolved]. Writes are copied into the mapping and counted, and a verify compares the page buffer against the mapping and reports a real mismatch rather
than agreeing [E: `port/shim/fs/cardreq.c`; `scratchpad/cycle40/runs/tap-D56`].

Two constants in that shim were wrong in ways worth recording, because both failures were silent. The status bit spelled `CARD_STAT_INIT_CMD` had been written as 0x40, which is `CARD_STAT_CANCEL`, so every answered request also raised the cancel bit and
`CARDi_RequestStreamCommandCore` -- which tests exactly that bit first -- returned CARD_RESULT_CANCELED; every save read came back as "the read FAILED" rather than "there is no save" [H: log/source account: `port/shim/fs/cardreq.c`; the correct values are
`src/matched/CARD_CancelBackupAsync.c`'s INIT 1, INIT_CMD 2, BUSY 4, TASK 8, RECV 16, REQ 32, CANCEL 64; receipt provenance unresolved]. And the read request number had been written as 5, while the game issues 6, so the 0xFF-erased fill never executed once [H: host-source account
from `port/shim/fs/cardreq.c`, settled against `src/matched/func_020509a8.c`; verify with a retained scripted run and frame using this page's recipe].

**An erased store is 0xFF, and a zeroed one is a different game.** A block of zeros is not an
absent save; it is a save whose header and checksum are zero, which the game reads as damaged
[H: inferred from `func_020b5724`'s bank validity test; settled by running with `ACWW_SAVE`
pointed at an all-zero file and looking for the damaged-save path]. When the read fill was
corrected to 0xFF the keyed START run stopped at `unimplemented: func_02225a90` around frame
10 — the port's stop line quotes a bare address; the symbol tables name that function
`func_ov003_02225a90` [S: `config/adm-kr/arm9/overlays/ov003/symbols.txt`] — where the same
build with the fill off runs clean -- so the honest answer moves the boot
onto a path the port cannot yet follow [H: host-source account from `port/shim/fs/cardreq.c`, keyed START, frame ~10; verify with a retained scripted run and frame using this page's recipe].

## The save image, by offset

This is a transcription index, not a new save measurement. `--` means that the cited source
does not transcribe that absolute file/RAM/mirror location; no bank-stride arithmetic fills
the gaps. `P+`, `V+`, and `L+` retain the source's player-, villager-, and letter-relative
coordinates rather than claiming an unmeasured absolute file offset. RAM cells name only
the recorded player/slot when stated. All widths are bytes. Source accounts retain H grade:
the scratchpad receipt paths below were checked for existence only, never replayed or opened
as save data. The inventory is `scratchpad/save-layout-1/source-inventory.json`.

| Bank-1 file offset (or explicitly relative coordinate) | Bank-2 file mirror, if transcribed | RAM mirror, if transcribed | Field | Width | Measurement section / retained receipt or source |
|---|---|---|---|---|---|
| 0x00000 | 0x173fc | 0x021dc7a8 | Bank / working town record | 0x173fc | [H: `docs/log/cycle42-save.md` SAVE43; `scratchpad/save43/RECEIPTS.md`]; [H: this page, Data it reads and writes] |
| 0x0000 | -- | -- | Gamecode word (acceptance checks low byte) | 2 | [H: `port/tools/savetool.py`, FIELD OFFSETS/constants; source transcription] |
| 0x0002 | -- | 0x021dc7aa | Town id | 2 | [H: `port/tools/savetool.py`, FIELD OFFSETS/constants; source transcription]; [H: cycle41-gameplay.md O46-1; `scratchpad/oracle46/RECEIPTS.md`] |
| 0x0004 | -- | -- | Town name, 6 UTF-16LE units | 12 | [H: `port/tools/savetool.py`, FIELD OFFSETS/constants; source transcription] |
| 0x0014 | -- | -- | Four player slots; P denotes one slot, stride 0x249c | 4 x 0x249c | [H: `port/tools/savetool.py`, FIELD OFFSETS/constants; source transcription] |
| P+0x0000 | -- | -- | Patterns | 8 x 0x234 | [H: `port/tools/savetool.py`, FIELD OFFSETS/constants; source transcription] |
| P+0x1bf2 | -- | 0x021de3ae (slot 0) | Pocket items | 15 x 2 | [H: `port/tools/savetool.py`, FIELD OFFSETS/constants; source transcription]; [H: this page, Data it reads and writes / GP47] |
| P+0x1c10 | -- | 0x021de3cc (player 0) | Wallet | 4 | [H: `port/tools/savetool.py`, FIELD OFFSETS/constants; source transcription]; [H: cycle41-gameplay.md GP46-5] |
| P+0x23e0 | -- | 0x021deb9c (player 0) | Savings (check labels it bank) | 4 | [H: `port/tools/savetool.py`, FIELD OFFSETS/constants; source transcription]; [H: cycle41-gameplay.md GP56-2; `scratchpad/gameplay56/RECEIPTS.md`] |
| P+0x2408 | -- | 0x021debc4 (player 0) | Worn shirt | 2 | [H: `port/tools/savetool.py`, FIELD OFFSETS/constants; source transcription]; [H: this page, Data it reads and writes / GP47] |
| P+0x240a | -- | -- | Second wearable; not run-confirmed | 2 | [H: `port/tools/savetool.py`, FIELD OFFSETS/constants; source transcription] |
| P+0x243c | -- | -- | Face / hairstyle nibbles | 1 | [H: `port/tools/savetool.py`, FIELD OFFSETS/constants; source transcription] |
| P+0x243d | -- | -- | Tan / hair colour nibbles | 1 | [H: `port/tools/savetool.py`, FIELD OFFSETS/constants; source transcription] |
| P+0x247e | -- | -- | Player town id | 2 | [H: `port/tools/savetool.py`, FIELD OFFSETS/constants; source transcription] |
| P+0x2480 | -- | -- | Player town name | 12 | [H: `port/tools/savetool.py`, FIELD OFFSETS/constants; source transcription] |
| P+0x248c | -- | 0x021dec48 (player 0) | Player id | 2 | [H: `port/tools/savetool.py`, FIELD OFFSETS/constants; source transcription]; [H: cycle41-gameplay.md GP46-5] |
| P+0x248e | -- | -- | Player name (tool decodes 6 units) | 12 | [H: `port/tools/savetool.py`, FIELD OFFSETS/constants; source transcription] |
| P+0x249a | -- | -- | Gender | 1 | [H: `port/tools/savetool.py`, FIELD OFFSETS/constants; source transcription] |
| 0x01c24 (player 0) | -- | 0x021de3cc | Wallet, explicit file offset | 4 | [H: `docs/log/cycle41-gameplay.md` GP46-5; also `port/tools/test_savetool.py`, hand arithmetic] |
| 0x023f4 (player 0) | -- | 0x021deb9c | Savings, explicit fixture file offset | 4 | [H: `port/tools/test_savetool.py`, hand arithmetic; cycle41-gameplay.md GP56-2] |
| 0x024a0 / 0x024a2 (player 0) | -- | 0x021dec48 (id only) | Player id / name, explicit fixture file offsets | 2 / 12 | [H: `port/tools/test_savetool.py`, hand arithmetic; cycle41-gameplay.md GP46-5] |
| P+0x11ac; player 0 0x011c0..0x01bbf | -- | -- | Letters; L denotes one record. the tool said +0x11a8 until HANDOFF22 | 10 x 0x100 | [H: `docs/log/cycle41-gameplay.md` GP58-2; `scratchpad/gameplay58/RECEIPTS.md`]; [H: `port/tools/savetool.py`, FIELD OFFSETS/constants; source transcription] |
| L+0x00 | -- | -- | Addressee town id | 2 | [H: `docs/log/cycle41-gameplay.md` GP58-2; `scratchpad/gameplay58/RECEIPTS.md`] |
| L+0x02 | -- | -- | Addressee town name | 12 | [H: `docs/log/cycle41-gameplay.md` GP58-2; `scratchpad/gameplay58/RECEIPTS.md`] |
| L+0x0e | -- | -- | Addressee player id | 2 | [H: `docs/log/cycle41-gameplay.md` GP58-2; `scratchpad/gameplay58/RECEIPTS.md`] |
| L+0x10 | -- | -- | Addressee player name (4 units, not the tool player-name width) | 8 | [H: `docs/log/cycle41-gameplay.md` GP58-2; `scratchpad/gameplay58/RECEIPTS.md`] |
| L+0x1e | -- | -- | Live/unused marker; meaning otherwise unnamed | 1 | [H: `docs/log/cycle41-gameplay.md` GP58-2; `scratchpad/gameplay58/RECEIPTS.md`] |
| L+0x3e | -- | -- | Unnamed word | 2 | [H: `docs/log/cycle41-gameplay.md` GP58-2; `scratchpad/gameplay58/RECEIPTS.md`] |
| L+0x40 | -- | -- | Salutation range | 12 | [H: `docs/log/cycle41-gameplay.md` GP58-2; `scratchpad/gameplay58/RECEIPTS.md`] |
| L+0x54 | -- | -- | Body range | 60 | [H: `docs/log/cycle41-gameplay.md` GP58-2; `scratchpad/gameplay58/RECEIPTS.md`] |
| L+0xd4 | -- | -- | Signature range | 10 | [H: `docs/log/cycle41-gameplay.md` GP58-2; `scratchpad/gameplay58/RECEIPTS.md`] |
| L+0xf4 | -- | -- | Unnamed word unchanged by present take | 2 | [H: `docs/log/cycle41-gameplay.md` GP58-2; `scratchpad/gameplay58/RECEIPTS.md`] |
| L+0xf6 | -- | -- | Unnamed word whose low byte changed on present take | 2 | [H: `docs/log/cycle41-gameplay.md` GP58-2; `scratchpad/gameplay58/RECEIPTS.md`] |
| L+0xf8 | -- | -- | Attached present; 0xfff1 means none | 2 | [H: `docs/log/cycle41-gameplay.md` GP58-2; `scratchpad/gameplay58/RECEIPTS.md`] |
| 0x12b8, 0x13b8, ... 0x1bb8 | -- | -- | Player-0 letter present positions as logged | 2 each | [H: `docs/log/cycle41-gameplay.md` GP58-2; `scratchpad/gameplay58/RECEIPTS.md`] |
| 0x9284 | -- | -- | Eight villager records; V denotes one record, stride 0x7ec | 8 x 0x7ec | [H: `port/tools/savetool.py`, FIELD OFFSETS/constants; source transcription] |
| V+0x400 | -- | -- | Villager pattern | 0x234 | [H: `port/tools/savetool.py`, FIELD OFFSETS/constants; source transcription] |
| V+0x634 | -- | -- | Villager letter | 0x100 | [H: `port/tools/savetool.py`, FIELD OFFSETS/constants; source transcription] |
| V+0x78c | -- | -- | Furniture ids | 10 x 2 | [H: `port/tools/savetool.py`, FIELD OFFSETS/constants; source transcription] |
| V+0x7a0 | -- | -- | Identity record: id, name, personality, villager id | 16 | [H: `port/tools/savetool.py`, FIELD OFFSETS/constants; source transcription] |
| V+0x7ae | -- | -- | Personality | 1 | [H: `port/tools/savetool.py`, FIELD OFFSETS/constants; source transcription] |
| V+0x7af | -- | 0x021e61db (slot 0) | Villager id; 0xff empty | 1 | [H: `port/tools/savetool.py`, FIELD OFFSETS/constants; source transcription]; [H: cycle41-gameplay.md O46-1; `scratchpad/oracle46/RECEIPTS.md`] |
| V+0x7d2 | -- | -- | Shirt id | 2 | [H: `port/tools/savetool.py`, FIELD OFFSETS/constants; source transcription] |
| V+0x7d4 | -- | -- | Wallpaper | 1 | [H: `port/tools/savetool.py`, FIELD OFFSETS/constants; source transcription] |
| V+0x7d5 | -- | -- | Carpet | 1 | [H: `port/tools/savetool.py`, FIELD OFFSETS/constants; source transcription] |
| V+0x7da | -- | -- | Umbrella | 1 | [H: `port/tools/savetool.py`, FIELD OFFSETS/constants; source transcription] |
| 0x10abc | 0x27eb8 | 0x021ed264 | House loan | 4 | [H: `docs/log/cycle41-gameplay.md` GP49-2; `scratchpad/gameplay49/RECEIPTS.md`]; [H: cycle41-gameplay.md GP52-5 / GP53-6; `scratchpad/gameplay52/RECEIPTS.md`, `scratchpad/gameplay53/RECEIPTS.md`] |
| 0xd304 | -- | 0x021e9aac | 6 x 6 acre map | 36 | [H: `docs/log/cycle41-gameplay.md` O49-0; `scratchpad/oracle49/RECEIPTS.md`] |
| 0xd328 | -- | 0x021e9ad0 | Item layer: inner 4 x 4 acres only | 8192 | [H: `docs/log/cycle41-gameplay.md` O49-0; `scratchpad/oracle49/RECEIPTS.md`] |
| 0x15958 | -- | -- | Second letter-shaped array; delivery-queue interpretation remains a hypothesis | 10 x 0x100 | [H: `docs/log/cycle41-gameplay.md` GP58-2; `scratchpad/gameplay58/RECEIPTS.md`] |
| 0x15a50 .. 0x16350 | -- | -- | Second-array present positions as logged | 2 each | [H: `docs/log/cycle41-gameplay.md` GP58-2; `scratchpad/gameplay58/RECEIPTS.md`] |
| 0x17370 | -- | -- | Turnip field (tool labels turnip price) | 1 | [H: `port/tools/savetool.py`, FIELD OFFSETS/constants; source transcription] |
| 0x173f8 | -- | -- | Checksum; whole-bank wrapping u16 sum is zero | 2 | [H: `port/tools/savetool.py`, FIELD OFFSETS/constants; source transcription]; [H: `docs/log/cycle42-save.md` SAVE43; `scratchpad/save43/RECEIPTS.md`] |
| 0x173fa | -- | -- | Flag word; ROM acceptance checks its low byte | 2 | [H: `port/tools/savetool.py`, FIELD OFFSETS/constants; source transcription] |
| 0x173fb | 0x2e7f7 | -- | High flag byte changed between CARD45 pacing arms | 1 | [H: `docs/kb/hybrid/save-flow.md` section 6, CARD45] |
| 0x2400 | 0x198fc (separate write location, not an asserted mirror) | -- | Continue-path writes: eight pages total across these and next row | 2040 total, not per location | [H: `docs/log/cycle42-save.md` SAVE43; `scratchpad/save43/RECEIPTS.md`]; [H: save-flow.md 5c / GP53-0] |
| -- | 0x2e5fc / 0x2e6fc (bank-2 file locations) | -- | Other continue-path write locations; bank-1 counterpart not transcribed | page-level observation only | [H: `docs/log/cycle42-save.md` SAVE43; `scratchpad/save43/RECEIPTS.md`] |
| outside banks: 0x337fc | not a mirror | -- | Slot 2, retired letter-store label; purpose unestablished | 0x0c804 | [H: `docs/log/cycle41-gameplay.md` GP58-2; `scratchpad/gameplay58/RECEIPTS.md`]; [H: `port/tools/savetool.py`, FIELD OFFSETS/constants; source transcription] |
| outside banks: 0x3fffc | not a mirror | -- | Boot write/verify probe; writability interpretation is a hypothesis | 1 | [H: `docs/log/cycle42-save.md` SAVEFLOW41; `scratchpad/saveflow/RECEIPTS.md`] |
| outside banks: 0x3fffe | not a mirror | -- | Slot-2 checksum claimed by tool prose only; not measured here | not stated | [H: `port/tools/savetool.py`, FIELD OFFSETS/constants; source transcription] |

**Resolved (HANDOFF22).** The tool's FIELD OFFSETS prose used to say the letters start at
`+0x11a8` and its slot table called `0x337fc` the letter store; both were corrected on the
HANDOFF22 fold -- `port/tools/savetool.py` now says `+0x11ac` and labels slot 2 "purpose not
established (GP58-2)". The slot-2 checksum at `0x3fffe` remains a source account, not a
measurement [H: `port/tools/savetool.py`; `docs/log/cycle41-gameplay.md` GP58-2].

**QUESTION (range wording).** `save-flow.md` section 4 calls `0x3fffc` outside
`0x337fc..0x40000`, while the same page's slot table places slot 2 over that interval. Both
claims are retained for correction by the orchestrator [H: `docs/kb/hybrid/save-flow.md` 2 / 4].

`savetool.py check` already prints savings as `bank` and all fifteen pockets. This unit adds
the documented loan word to `describe_bank`, with a synthetic two-bank fixture and a bad
checksum control; it does not repair a save or interpret the unnamed letter words
[H: `port/tools/savetool.py::describe_bank`, `port/tools/test_savetool.py::test_check_reports_each_banks_house_loan`;
E: `scratchpad/handoff/save-layout-1/test-savetool.log`].

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
| `func_020a1d94` / `func_020a2120` | main | the 512-bytes-per-step bank writer, and the seven-state driver whose state 4 runs it | [S: `src/matched/func_020a1d94.c`, `config/adm-kr/arm9/symbols.txt`, `func_020a2120` at `0x020a2120`; historical account: those two functions; `docs/log/cycle42-save.md` SAVE42] |
| `func_0209f6e4` | main | the save prompt's branch: `sp_etc_sequence4` message 4 (refuse) or `sp_etc_sequence2` (the real menu) | [S: `func_0209f6e4`, main] |
| `func_020a128c` / `func_020a12c0` / `func_020a12d4` | main | the move-in mode accessors on `0x021f3c30`: `:= 0`, `== 2`, `== 1` | [S: `src/matched/func_020a128c.c`, `src/matched/func_020a12c0.c`, `src/matched/func_020a12d4.c`; historical account: the ROM; H: `gp-W0`'s store watchpoint, `docs/log/cycle42-save.md` SAVE43] |
| `CARD_GetCurrentBackupType` | -- | **misidentified in the tree**: this address is `DWC_Netcheck_GetReturnCode`, not a CARD function | [S: header comment, `src/matched/CARD_GetCurrentBackupType.c`] |

## Data it reads and writes

| address or field | meaning | who writes | who reads |
|---|---|---|---|
| command block `+0x00` `result` | `CARDResult` for the last request | the ARM7 (the port's `acww_card_arm7`) | `CARD_GetResultCode` [S: `src/matched/CARD_GetResultCode.c`] |
| command block `+0x10` `src` | flash offset on a read; page buffer on a write | `CARDi_RequestStreamCommandCore` | the ARM7 [S: `src/matched/CARDi_RequestStreamCommandCore.c`] |
| command block `+0x14` `dst` | page buffer on a read; flash offset on a write | `CARDi_RequestStreamCommandCore` | the ARM7 [S: `src/matched/CARDi_RequestStreamCommandCore.c`; historical account: `src/matched/CARDi_RequestStreamCommandCore.c`] |
| command block `+0x18` `len` | bytes this request moves, never above 256 | `CARDi_RequestStreamCommandCore` | the ARM7 [S: `src/matched/CARDi_RequestStreamCommandCore.c`; historical account: `src/matched/CARDi_RequestStreamCommandCore.c`] |
| `spec` sub-block | total size, sector size, page size, address width, six timings | `CARDi_IdentifyBackupCore` | `CARD_GetBackupTotalSize`, `CARD_GetBackupPageSize` [S: `src/matched/CARDi_IdentifyBackupCore.c`] |
| `cardi_common.flag` | INIT 1, INIT_CMD 2, BUSY 4, TASK 8, RECV 16, REQ 32, CANCEL 64 | `CARDi_Request`, `CARD_CancelBackupAsync`, the reply path | the core loop and the waiters [S: `src/matched/CARD_CancelBackupAsync.c`] |
| `cardi_common.backup_cache_page_buf` | the 256-byte DMA-safe staging page every transfer passes through | `CARDi_RequestStreamCommandCore` | the ARM7 [S: `src/matched/CARDi_RequestStreamCommandCore.c`] |
| flash `0x00000`..`0x3ffff` | the 256 KB store; two banks of 0x173fc bytes | the ARM7 on request 7 | the ARM7 on request 6 [S: `src/matched/func_020b5724.c`, `src/matched/func_02050b78.c`] |
| `0x021dc7a8` | the working copy `func_020b5724` copies 0x173fc bytes from | the game | `func_020b5724` [S: `src/matched/func_020b5724.c`] |
| player slot `+0x1bf2`, 15x u16 | the pockets; `0xfff1` is an empty slot | `func_02098f0c` (bounds-checked by `func_02098f70`) | `func_02098f48` [S: `src/matched/func_02098f0c.c`, `src/matched/func_02098f70.c`, `src/matched/func_02098f48.c`; historical account: those three; H: GAMEPLAY47 `g47-SLOTW`, a store watchpoint on `0x021de3ae`] |
| player slot `+0x2408` u16 | **the WORN SHIRT.** A drop from the pockets onto the character swaps them, and the old one returns to the pocket iff it is in the shirt band `0x11a8..0x12a7` | `func_02099704`, called from `func_ov096_0229e3b0` case 2 (ov096's equip dispatcher) | `func_02099710` [S: `src/matched/func_02099704.c`, `src/matched/func_ov096_0229e3b0.c`, `src/matched/func_02099710.c`; historical account: those three, all matched; H: GAMEPLAY47 `g47-WEARW`, a store watchpoint on `0x021debc4`; `savetool.py check` prints it] |
| `0x021f3c30` | the **move-in mode** word: 1 or 2 refuses the save, 0 allows it | `func_ov147_02299414` / `func_ov147_022997ec` / `func_020a4454` (non-zero), `func_020a128c` (zero) | `func_020a12c0` / `func_020a12d4`, read by `func_0209f6e4` [S: `src/matched/func_020a128c.c`, `src/matched/func_020a12c0.c`, `src/matched/func_020a12d4.c`; historical account: the ROM; H: `gp-W0`] |
| `obj+0xa0`, table `0x021f3c84` | the save driver's state byte and its seven pointers-to-member | `func_020a2120` | `func_020a2120` [S: `func_020a2120`, main] |

## How to check it

That check has now been run, and the shim prints a full census at the stop frame rather than one line per distinct request type -- **but only since SAVE42**: `acww_card_report()` had no caller between SAVEFLOW41 and 2026-09-10, so the census printed nothing in between and only
the per-request span lines were evidence [H: log/source account: `port/platform/frame.c`; `docs/log/cycle42-save.md`; receipt provenance unresolved]. The whole 48,000-frame town recipe with a freshly erased `ACWW_SAVE` issues **746 backup reads (190,456 bytes, both banks, at
frame 10), one write and one verify -- of a single byte at `0x3fffc`** -- and leaves both banks 0xFF [E: `scratchpad/saveflow/runs/town1`; `port/shim/fs/cardreq.c`'s census; `../experiments/save-and-reload.md`]. That is the census of a run that never reaches the save. The census
of one that DOES is `744 requests, 190456 bytes` of type 7 and the same of type 9 [E: `scratchpad/save43/RECEIPTS.md`]. Read the two side by side: they are the same instrument on either side of the move-in gate.

    python -B scratchpad/saveflow/run_sf.py <name> ACWW_INTERP=1 ... "ACWW_SAVE=@SF@\x.sav"
    python port/tools/savetool.py check <the same absolute path>

`run_sf.py` rather than `run_direct.py` because `ACWW_STATE_SAVE`'s `<frame>:<path>` value is rewritten by MSYS bash, and because another session's `taskkill /F /IM acww.exe` ends any run launched under that name [H: log/source account: `../experiments/save-and-reload.md`;
receipt provenance unresolved].

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
  public editors implement is the ROM's [H: source account: as above; `port/tools/savetool.py`'s docstring; direct ROM-source provenance unresolved].
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
  [H: log/source account: `docs/log/cycle42-save.md` SAVE43; `../experiments/save-and-reload.md`; receipt provenance unresolved].
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
