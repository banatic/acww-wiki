# File system

**Summary.** ACWW reads everything it needs by path string through the stock NitroSDK file
system. A path is resolved against the file name table into a file id, the file id is looked up
in the file allocation table to give a byte span on the cartridge, and the span is read by DMA
from the card. All of it is a command queue in front of one archive named `rom`, and every
command can run synchronously or asynchronously against the same code. Overlays go through the
same machinery: an overlay is just a file with a 32-byte header that says where to put it.

## What happens

The whole file system lives in `autoload_2`, in one contiguous run from `0x021195e0` to
`0x0211bcfc` [S: `config/adm-kr/arm9/autoload_2/symbols.txt`, `FSi_TranslateCommand` addr
`0x021195e0` through `FSi_GetOverlayBinarySize` addr `0x0211bce0`]. Sixty-six `FS_*` and `FSi_*`
functions are byte-matched against NitroSDK 2.2a's `fs_file.c`, `fs_archive.c`, `fs_command.c`
and `fs_overlay.c` [S: `src/matched/FS_*.c`, `src/matched/FSi_*.c`, file header comments]. One
member is missing from the ROM's symbol table entirely: `FSi_CloseFileCommand`, eight bytes at
`0x021197c0`, whose body is `mov r0,#0; bx lr` [S: `port/shim/fs/fscmd.c`, header].

Boot calls `FS_Init(dma)` exactly once; it guards on an `is_init` flag and delegates to
`FSi_InitRom` [S: `FS_Init`, `autoload_2`, `src/matched/FS_Init.c`]. `FSi_InitRom` takes a lock
id for the cartridge, zeroes the two overlay-table descriptors, calls `CARD_Init`, initialises
the single ROM archive, registers it under the three-character name `rom`, installs
`FSi_RomArchiveProc` for the `WRITEFILE`, `ACTIVATE` and `IDLE` commands, and loads the archive
with the FAT and FNT regions taken from the ROM header image and a read callback of
`FSi_ReadRomCallback` [S: `FSi_InitRom`, `autoload_2`, `src/matched/FSi_InitRom.c`]. The FAT,
FNT and overlay-table regions come from fixed offsets in the header image the firmware leaves at
`0x027FFE00`: FNT at +0x40, FAT at +0x48, ARM9 overlay table at +0x50, ARM7 overlay table at
+0x58 [S: `src/matched/FSi_InitRom.c`, `src/matched/FS_LoadOverlayInfo.c`, the inline region
accessors].

Opening a file by name is two steps. `FS_OpenFile` calls `FS_ConvertPathToFileID` and then
`FS_OpenFileFast` [S: `FS_OpenFile`, `autoload_2`, `src/matched/FS_OpenFile.c`].
`FS_ConvertPathToFileID` sets up a stack-local `FSFile` and hands the path to `FSi_FindPath`
[S: `FS_ConvertPathToFileID`, `autoload_2`, `src/matched/FS_ConvertPathToFileID.c`], which
parses a leading `/` or a `name:` archive prefix of at most three characters and then issues a
`FINDPATH` command [S: `FSi_FindPath`, `autoload_2`, `src/matched/FSi_FindPath.c`]. The command
handler walks the file name table one component at a time, handling `.` and `..`, rejecting
names longer than 127 characters, and comparing case-insensitively with `FSi_StrNICmp`
[S: `FSi_FindPathCommand`, `autoload_2`, `src/matched/FSi_FindPathCommand.c`;
`src/matched/FSi_StrNICmp.c`]. Directory entries in the FNT are a length byte whose top bit
marks a directory, followed by the name and, for directories, a 16-bit id masked with `0xFFF`;
a file's id is the running index, post-incremented [S: `FSi_ReadDirCommand`, `autoload_2`,
`src/matched/FSi_ReadDirCommand.c`].

`FS_OpenFileFast` then turns the id into a span: it bounds-checks the index against the FAT
size, reads the 8-byte FAT entry, copies its `top` and `bottom` into the direct-open argument
block, and re-enters the command translator as an `OPENFILEDIRECT`
[S: `FSi_OpenFileFastCommand`, `autoload_2`, `src/matched/FSi_OpenFileFastCommand.c`], which
simply stores `top`, `bottom`, the initial position (= `top`) and the file id into the `FSFile`
[S: `FSi_OpenFileDirectCommand`, `autoload_2`, `src/matched/FSi_OpenFileDirectCommand.c`].

Reading clamps the requested length against the remaining span, records the request, marks the
file synchronous when it is not an async read, and issues `READFILE`
[S: `FSi_ReadFileCore`, `autoload_2`, `src/matched/FSi_ReadFileCore.c`]. `FS_ReadFile` is a
one-line tail call into that [S: `FS_ReadFile`, `autoload_2`, `src/matched/FS_ReadFile.c`].
`FS_SeekFile` issues no command at all — it adjusts `pos` inside the `FSFile` and clamps it into
the span [S: `FS_SeekFile`, `autoload_2`, `src/matched/FS_SeekFile.c`].

Every command goes through one queue per archive. `FSi_SendCommand` marks the file busy, appends
it to the archive's list, and — if the archive was idle — raises the running flag and issues
`ACTIVATE` through the archive's proc before executing
[S: `FSi_SendCommand`, `autoload_2`, `src/matched/FSi_SendCommand.c`]. `FSi_TranslateCommand`
offers the command to the archive's own proc first and falls back to the default handler table
[S: `FSi_TranslateCommand`, `autoload_2`, `src/matched/FSi_TranslateCommand.c`].
`FSi_NextCommand` drains cancelled files, wakes synchronous waiters, and when the queue empties
issues `IDLE` through a temporary `FSFile` [S: `FSi_NextCommand`, `autoload_2`,
`src/matched/FSi_NextCommand.c`]. For the ROM archive `ACTIVATE` and `IDLE` are the cartridge
lock and unlock [S: `FSi_RomArchiveProc`, `autoload_2`, `src/matched/FSi_RomArchiveProc.c`], and
the actual transfer is `CARD_ReadRomAsync` with `FSi_OnRomReadDone` as the completion
[S: `FSi_ReadRomCallback`, `autoload_2`, `src/matched/FSi_ReadRomCallback.c`].

Writing to the ROM archive is refused: `FSi_RomArchiveProc` answers `WRITEFILE` with
`FS_RESULT_UNSUPPORTED` [S: `src/matched/FSi_RomArchiveProc.c`]. The game's save data does not
go through the file system at all — it goes to backup flash through the CARD backup requests
(see the Hypotheses).

### Overlays

`FS_LoadOverlay` is three calls: read the overlay's info header, read its image, start it
[S: `FS_LoadOverlay`, `autoload_2`, `src/matched/FS_LoadOverlay.c`]. The info header is 32
bytes: id, RAM address, RAM size, BSS size, static-initialiser start and end, file id, and a
packed 24-bit compressed size plus 8-bit flag [S: `src/matched/FS_LoadOverlayInfo.c`,
`FSOverlayInfoHeader` as the matched sources declare it]. `FS_ClearOverlayImage` invalidates the
instruction and data caches over the whole region and zeroes the BSS tail
[S: `FS_ClearOverlayImage`, `autoload_2`, `src/matched/FS_ClearOverlayImage.c`].
`FS_StartOverlay` optionally authenticates the image with an HMAC-SHA1 digest, decompresses it
backwards when the compressed flag is set, flushes the data cache, and then walks the
`sinit_init`..`sinit_init_end` table calling every non-null constructor
[S: `FS_StartOverlay`, `autoload_2`, `src/matched/FS_StartOverlay.c`; `FSi_CompareDigest`,
`src/matched/FSi_CompareDigest.c`]. Tearing an overlay down is the mirror image: `FS_EndOverlay`
walks `__global_destructor_chain`, unlinks every node whose object or destructor falls inside the
overlay's address range, and runs the collected destructors [S: `FS_EndOverlay`, `autoload_2`,
`src/matched/FS_EndOverlay.c`].

All 148 of this ROM's overlays are stored compressed and none is signed, so the decompress arm
always runs and the digest arm never does [S: `extract/adm-kr/arm9_overlays/overlays.yaml`,
`compressed: true` / `signed: false` on all 148 entries]. The backward decompressor is
`MIi_UncompressBackward`, an assembly body the ROM does not name; it is identified as
`func_02000934` from two independent matched callers [S: `port/shim/fs/arena_uncompback.c`,
header, citing `tools/.../recovered_callees.txt`].

### NARC archives mounted as file systems

The same `FSArchive` object serves in-memory archives. `NNS_FndMountArchive` validates a `NARC`
image, finds its `FATB`, `FNTB` and `FIMG` blocks, and mounts it as an `FSArchive` whose base is
the first byte after the `FIMG` header, with FAT and FNT positions expressed relative to that
base [S: `NNS_FndMountArchive`, `autoload_2` `0x0210288c`, `src/matched/NNS_FndMountArchive.c`].
It passes null read and write callbacks, so `FS_LoadArchive` substitutes the memory callbacks and
the archive is served straight out of RAM [S: `FS_LoadArchive`, `autoload_2`,
`src/matched/FS_LoadArchive.c`; `src/matched/FSi_ReadMemCallback.c`]. Validation is the magic
`NARC`, byte-order mark `0xFFFE` and version `0x0100`
[S: `IsValidArchiveBinary`, `autoload_2` `0x021029e8`, `src/matched/IsValidArchiveBinary.c`].
Once mounted, a member is fetched by `archive:path` through the ordinary `FS_OpenFile`
[S: `NNS_FndGetArchiveFileByName`, `autoload_2` `0x02102808`,
`src/matched/NNS_FndGetArchiveFileByName.c`]. The game does this for town acres: it mounts
`/bg/aN/NNNN.arc` under the archive name `BG` and pulls six members — `BG:a/bmd/bmd0` and its
`bcl0`, `bsd0`, `bca0`, `bma0`, `bta0` companions [S: `port/shim/fs/arcmember.c`, header].

## Where it lives

| function or symbol | module | role | grade/citation |
|---|---|---|---|
| `FS_Init` `0x0211b35c` | `autoload_2` | one-shot init guard | S: `src/matched/FS_Init.c` |
| `FSi_InitRom` `0x0211b398` | `autoload_2` | registers the `rom` archive from the header image | S: `src/matched/FSi_InitRom.c` |
| `FS_OpenFile` `0x0211afdc` | `autoload_2` | path → open file | S: `src/matched/FS_OpenFile.c` |
| `FS_ConvertPathToFileID` `0x0211b100` | `autoload_2` | path → file id | S: `src/matched/FS_ConvertPathToFileID.c` |
| `FSi_FindPath` `0x0211b1cc` | `autoload_2` | parses `/` and `name:` prefixes | S: `src/matched/FSi_FindPath.c` |
| `FSi_FindPathCommand` `0x02119c2c` | `autoload_2` | the FNT walk | S: `src/matched/FSi_FindPathCommand.c` |
| `FSi_ReadDirCommand` `0x02119e48` | `autoload_2` | one FNT entry | S: `src/matched/FSi_ReadDirCommand.c` |
| `FSi_SeekDirCommand` `0x02119f58` | `autoload_2` | positions on a directory | S: `src/matched/FSi_SeekDirCommand.c` |
| `FS_OpenFileFast` `0x0211b02c` | `autoload_2` | file id → open file | S: `src/matched/FS_OpenFileFast.c` |
| `FSi_OpenFileFastCommand` `0x021197f0` | `autoload_2` | the FAT lookup | S: `src/matched/FSi_OpenFileFastCommand.c` |
| `FS_ReadFile` `0x0211ae68` / `FSi_ReadFileCore` `0x0211b144` | `autoload_2` | clamped read | S: `src/matched/FS_ReadFile.c`, `FSi_ReadFileCore.c` |
| `FS_SeekFile` `0x0211adfc` | `autoload_2` | local seek, no command | S: `src/matched/FS_SeekFile.c` |
| `FS_CloseFile` `0x0211af94` | `autoload_2` | closes and clears the file/dir bits | S: `src/matched/FS_CloseFile.c` |
| `FSi_SendCommand` `0x0211a82c` | `autoload_2` | enqueue + activate | S: `src/matched/FSi_SendCommand.c` |
| `FSi_TranslateCommand` `0x021195e0` | `autoload_2` | proc-first dispatch | S: `src/matched/FSi_TranslateCommand.c` |
| `FSi_NextCommand` `0x0211aad4` | `autoload_2` | queue pump, idle | S: `src/matched/FSi_NextCommand.c` |
| `FSi_RomArchiveProc` `0x0211b548` | `autoload_2` | cartridge lock/unlock, refuses writes | S: `src/matched/FSi_RomArchiveProc.c` |
| `FSi_ReadRomCallback` `0x0211b5e0` | `autoload_2` | `CARD_ReadRomAsync` | S: `src/matched/FSi_ReadRomCallback.c` |
| `FS_LoadArchive` `0x0211a5d4` / `FS_LoadArchiveTables` `0x0211a3e0` | `autoload_2` | archive setup, table caching | S: `src/matched/FS_LoadArchive.c`, `FS_LoadArchiveTables.c` |
| `FS_LoadOverlay` `0x0211b690` | `autoload_2` | info → image → start | S: `src/matched/FS_LoadOverlay.c` |
| `FS_StartOverlay` `0x0211b80c` | `autoload_2` | decompress + run constructors | S: `src/matched/FS_StartOverlay.c` |
| `FS_EndOverlay` `0x0211b708` | `autoload_2` | destructor sweep | S: `src/matched/FS_EndOverlay.c` |
| `NNS_FndMountArchive` `0x0210288c` | `autoload_2` | NARC → `FSArchive` | S: `src/matched/NNS_FndMountArchive.c` |
| `FSi_CloseFileCommand` `0x021197c0` | `autoload_2` | unnamed in the ROM; returns success | S: `port/shim/fs/fscmd.c` |

## Data it reads and writes

| address or field | meaning | who writes | who reads |
|---|---|---|---|
| `0x027FFE00` +0x40 / +0x48 | FNT and FAT regions | the firmware's header copy | `FSi_InitRom` [S: `src/matched/FSi_InitRom.c`] |
| `0x027FFE00` +0x50 / +0x58 | ARM9 / ARM7 overlay tables | the firmware's header copy | `FS_LoadOverlayInfo` [S: `src/matched/FS_LoadOverlayInfo.c`] |
| `0x027FFC40` | multiboot boot buffer; non-zero means "child" | firmware | `FSi_InitRom`'s multiboot branch [S: `src/matched/FSi_InitRom.c`] |
| `FSArchiveFAT {u32 top; u32 bottom;}` | 8 bytes per file, a byte span | the packer | `FSi_OpenFileFastCommand` [S: `src/matched/FSi_OpenFileFastCommand.c`] |
| `FSArchiveFNT {u32 start; u16 index; u16 parent;}` | 8 bytes per directory | the packer | `FSi_SeekDirCommand` [S: `src/matched/FSi_SeekDirCommand.c`] |
| `FSFile.stat` bits `0x01/0x02/0x04/0x08/0x10/0x20/0x40` | busy, cancel, sync, async, is-file, is-dir, operating | `FSi_SendCommand`, `FS_OpenFileFast` | `FSi_ExecuteAsyncCommand`, `FS_CloseFile` [S: `src/matched/FSi_SendCommand.c`] |
| `FSArchive.flag` bits `0x01`..`0x200` | registered, loaded, table-loaded, suspend, running, cancelling, suspending, unloading, is-async, is-sync | `FS_RegisterArchiveName`, `FS_LoadArchive`, `FSi_TranslateCommand` | the queue pump [S: `src/matched/FSi_TranslateCommand.c`] |
| `FSOverlayInfoHeader` (32 B) | id, RAM address, RAM size, BSS size, sinit range, file id, compressed:24 + flag:8 | the packer | `FS_LoadOverlayInfo`, `FS_StartOverlay` [S: `src/matched/FS_LoadOverlayInfo.c`] |

A detail that matters to anyone reading these structures: this ROM was built with
`SDK_THREAD_INFINITY`, so `OSThreadQueue` is a real `{head, tail}` pair of 8 bytes rather than a
packed 4-byte field. Every structure embedding an `FSFile` is therefore 4 bytes larger than the
default SDK headers suggest [S: `docs/kb/modules/sdk-nns.md`, the `SDK_THREAD_INFINITY`
section]. The overlay half of the family additionally needs `SDK_TS`, which is what decides
whether `fs_overlay.c` compiles at all [S: `docs/kb/modules/sdk-nns.md`, the `SDK_TS` section].

## How to check it

The port replaces the cartridge, not the API: `port/shim/fs/romfs.c` presents the extracted file
system as a flat virtual ROM address space and `port/shim/fs/card.c` answers `CARDi_ReadRom` out
of it, so every `FS_*` function above is the ROM's own code running unmodified
[S: `port/shim/fs/card.c`, header; `port/shim/fs/romfs.c`, header]. The index blob is written by
`port/tools/fsimage.py` with magic `ACWWFSI1`, and the ROM header, overlay table, FNT and FAT are
stored verbatim at the front of the virtual ROM [S: `port/shim/fs/romfs.c`, `struct Index`].

To watch the file system work, run the interpreter recipe used for the town and watch the
overlay set:

```
ACWW_INTERP=1  ACWW_KEYS_AT/_FOR/_EVERY = the custom START9000 keys
ACWW_TOUCH_ENABLE=1 ACWW_TOUCH_X=221 ACWW_TOUCH_Y=181 ACWW_TOUCH_AT=6900 ACWW_TOUCH_EVERY=60
ACWW_STOP_FRAME=48000
python port/tools/run.py --frontier start
```

Expected: at frame 37,500 the town is on screen with overlays 5, 36, 54, 120 and 117 loaded
[E: `scratchpad/cycle40/runs/tap-D56` frame 37500, per `docs/log/cycle40-keyboard-gate-probe.md`
TOWN40]. That is the file system doing its whole job — a path resolved, an overlay read,
relocated, constructed and drawn.

## Hypotheses

- The port's overlay relocation is a host-side workaround, not ROM behaviour: `relocs.py` cannot
  rewrite overlay pointers statically because the overlays overlap, so per-overlay tables are
  applied inside `FS_StartOverlay`, and the interpreter path deliberately runs no relocation
  pass at all [S: `port/shim/fs/ovlreloc.c`, header]. Whether the interpreter path is now the
  only correct one would be settled by running the same recipe on both paths and diffing the
  loaded-overlay traces.
- `FS_EndOverlay`'s ROM implementation hangs the native port (overlay 65 loads, no frame
  completes) so the port runs a bounded sweep instead [S: `port/shim/fs/endoverlay.c`, header].
  It is not known whether that hang is a defect in the port's destructor chain or in the ROM's
  own teardown under the port's heap. Settle it by running the ROM's `FS_EndOverlay` under
  `ACWW_INTERP=1` and recording where the sweep stops.
- Save data is asserted here to bypass the file system entirely, on the strength of the CARD
  backup request numbers (READ_BACKUP 6, WRITE_BACKUP 7, VERIFY_BACKUP 9) and a 256 KB flash
  device identified from `0x1202` [S: `port/shim/fs/cardreq.c`, header]. That is written up on
  `../systems/save-data.md` and should be confirmed there by watching whether any `FS_*` command
  is ever issued during a save.
- `BUILDTIME` and the `path_order.txt` ordering suggest the tree was packed in a specific order.
  Settle it by comparing FAT spans against `path_order.txt`.

## Related

- `../data/rom-layout.md` — the module and directory layout the file ids index into.
- `../data/archives.md` — the container formats sitting inside each file.
- `overlays.md` — what each of the 148 overlays is for.
- `../data/music.md` — `sound_data.sdat`, the one file read as an archive by the sound library.
