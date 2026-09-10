# Music and sound

**Summary.** All of the game's audio is one 10.7 MB `SDAT` archive at the root of the file
system, `sound_data.sdat`. Its symbol block was stripped before shipping, so nothing inside has a
name: the game addresses sequences, banks and streams by numeric index only. The archive declares
376 sequence slots (342 defined), 216 sequence-archive entries, 943 banks, 14 wave archives, 21
players, 30 groups and 2 streams, over 1,511 packed files. The NitroSystem sound library that
reads it is 78 matched functions in `autoload_2`.

Grade note: **S** on this page covers symbol tables, matched sources, and bytes read directly out
of the extracted ROM image (path and field always named).

## What happens

`sound_data.sdat` is 10,704,768 bytes and sits at the file-system root beside `BUILDTIME`; it is
the largest single file in the ROM [S: `extract/adm-kr/files/sound_data.sdat`, size;
`extract/adm-kr/files/`, root listing]. It is opened by the literal path `/sound_data.sdat`
compiled into the ARM9 image [S: `extract/adm-kr/arm9/arm9.bin`, path string literal].

The container is the standard NitroSDK one: magic `SDAT`, byte-order mark `0xFEFF`, a file-size
field that matches the file exactly, header size 64, and four block descriptors
[S: `extract/adm-kr/files/sound_data.sdat`, bytes 0..48]. **The `SYMB` block is absent** — its
offset and size are both zero — so the shipped archive carries no names for any of its entries
[S: same file, the first block descriptor at offset 16]. The other three are `INFO` at `0x40`
(24,712 bytes), `FAT ` at `0x60c8` (24,188 bytes) and `FILE` at `0xbf44` (10,655,804 bytes)
[S: same file, block descriptors at offsets 24, 32 and 40].

`FAT ` declares 1,511 packed files totalling 10,631,196 bytes, the largest of them 3,233,800
bytes [S: same file, `FAT ` entry count at +8 and the 16-byte entry array]. A single file of 3.2
MB in an archive whose next largest category is sequence data is almost certainly one of the two
streams [H: see Hypotheses].

`INFO` holds eight record tables, each a count followed by that many offsets, with the record
bodies packed after the offset array [S: same file, the eight table offsets at `INFO`+8, and the
span arithmetic between consecutive tables]:

| record table | slots | defined (non-zero offset) | body size implied by the span |
|---|---|---|---|
| SEQ (sequences) | 376 | 342 | 12 bytes each |
| SEQARC (sequence archives) | 216 | 216 | 4 bytes each |
| BANK (instrument banks) | 943 | 943 | 12 bytes each |
| WAVEARC (wave archives) | 14 | 14 | 4 bytes each |
| PLAYER | 21 | 21 | 8 bytes each |
| GROUP | 30 | 30 | variable |
| PLAYER2 | 1 | 1 | — |
| STRM (streams) | 2 | 2 | — |

[S: `extract/adm-kr/files/sound_data.sdat`, counts read from each table's first word; body sizes
from `(span - 4 - 4*count) / defined`.]

The 34 undefined sequence slots are holes in the id space — indices the game can name but which
carry no data [S: same file, 34 of the 376 SEQ offsets are zero]. Every other table is fully
dense.

### The library that reads it

Seventy-eight `NNS_Snd*` functions are byte-matched, all in `autoload_2`
[S: `src/matched/NNS_Snd*.c`, 78 files; `config/adm-kr/arm9/autoload_2/symbols.txt`]. That is
the public half: the symbol table names 105 `NNS_Snd*`/`NNSi_Snd*` and 65 `SND_*`/`SNDi_*`
functions in `autoload_2`, and `src/matched/` matches 78, 27 and 65 of them respectively
[S: `config/adm-kr/arm9/autoload_2/symbols.txt`, prefix counts; `src/matched/`, file-name
counts]. The whole sound stack is `autoload_2`, not `main` — see `../systems/audio.md`. They split
into four groups. The archive accessors turn an index into a record or a file:
`NNS_SndArcGetSeqInfo`, `GetSeqArcInfo`, `GetBankInfo`, `GetWaveArcInfo`, `GetPlayerInfo`,
`GetGroupInfo`, `GetStrmInfo`, `GetStrmPlayerInfo`, plus `NNS_SndArcGetFileID`,
`GetFileAddress`, `GetFileOffset`, `GetFileSize` and `NNS_SndArcReadFile`
[S: `src/matched/NNS_SndArcGetSeqInfo.c` and siblings]. The setup pair is `NNS_SndArcInit` and
`NNS_SndArcInitOnMemory`, with `NNS_SndArcSetup` and `NNS_SndArcSetCurrent`/`GetCurrent`
[S: `src/matched/NNS_SndArcInit.c`, `NNS_SndArcSetup.c`, `NNS_SndArcSetCurrent.c`]. Playback is
`NNS_SndArcPlayerStartSeq`, `StartSeqArc`, `StartSeqArcEx`, `NNS_SndPlayerSetSeqNo`,
`SetSeqArcNo`, `StopSeq`, `StopSeqByPlayerNo`, `StopSeqBySeqArcIdx`, and the per-track setters
`SetTrackVolume` and `SetTrackPitch`
[S: `src/matched/NNS_SndArcPlayerStartSeq.c` and siblings]. Streaming is its own set:
`NNS_SndStrmInit`, `Setup`, `Start`, `Stop`, `AllocChannel`, `FreeChannel`, `SetVolume`,
`SetChannelPan`, `HandleRelease`, with `NNS_SndArcStrmPrepare`, `StartPrepared`,
`GetTimeLength`, `GetCurrentPlayingPos` and `MoveVolume`
[S: `src/matched/NNS_SndStrmInit.c` and siblings]. Memory for all of it comes from a dedicated
heap: `NNS_SndHeapCreate`, `Alloc`, `Clear`, `Destroy`, `SaveState`, `LoadState`,
`GetCurrentLevel`, plus `NNS_SndPlayerCreateHeap`
[S: `src/matched/NNS_SndHeapCreate.c` and siblings]. `NNS_SndArcLoadGroup` is the bulk loader
that pulls a whole group in one call [S: `src/matched/NNS_SndArcLoadGroup.c`], which is what the
30 GROUP records are for.

There is also a capture/effect set — `NNS_SndCaptureCreateThread`, `StartEffect`,
`StartOutputEffect`, `ChangeOutputEffect`, `StopEffect`, `NNS_SndLockCapture`, `UnlockCapture` —
so the hardware sound capture unit is wired up
[S: `src/matched/NNS_SndCaptureCreateThread.c` and siblings].

### Where music appears in the UI

Two overlays own music screens. `ov144` carries `menu/music/`, seven files — the stereo screen
that plays a collected song [S: `extract/adm-kr/arm9_overlays/ov144.bin`, seven path literals;
`extract/adm-kr/files/menu/music/`, 7 files]. `ov143` carries `menu/melody/`, seven files — the
town-tune editor [S: `extract/adm-kr/arm9_overlays/ov143.bin`, path literals;
`extract/adm-kr/files/menu/melody/`, 7 files]. Song names come from one message bank,
`script/KOR/string/st_music.bmg`, 386 bytes
[S: `extract/adm-kr/files/script/KOR/string/`, file name and size].

### Sound in the port

With `ACWW_SND=1` the interpreter path produces music and sound effects; the retained PCM
capture is `scratchpad/audio7/on/capture.wav` [E: `scratchpad/audio7/on`, 9,000 frames;
`docs/kb/hybrid/audio.md` sections 1 and 8(a)]. The ROM's sound stack runs on the interpreter path, and running it is
what exposed the geometry defects fixed by GX40: with the sound stack active the top screen
stayed black while the geometry engine received about 1,400 vertices a frame and drew none
[E: `docs/log/cycle40-keyboard-gate-probe.md` GX40]. `func_0205401c` also writes bit 15 of `POWCNT1` at `0x04000304`, from a global the
reconstruction calls `gSoundFlag` [S: `src/matched/func_0205401c.cpp`]. **That name is inferred,
not original, and the bit is not a sound bit**: `POWCNT1` bit 15 selects which 2D engine drives
the top screen, which is what `func_020540e4` uses it for
[S: `src/matched/func_0205401c.cpp` header, "names are inferred, not original";
`src/matched/func_020540e4.c`; `../engine/graphics-pipeline.md`]. What the global actually holds
is open [H: settled by watching that word and the top/bottom screen contents together across a
run].

## Where it lives

| item | location | grade/citation |
|---|---|---|
| the archive | `/sound_data.sdat`, 10,704,768 B | S: `extract/adm-kr/files/sound_data.sdat` |
| `INFO` block | offset `0x40`, 24,712 B | S: same, block descriptor |
| `FAT ` block | offset `0x60c8`, 24,188 B, 1,511 entries | S: same |
| `FILE` block | offset `0xbf44`, 10,655,804 B | S: same |
| `SYMB` block | absent (offset 0, size 0) | S: same |
| `NNS_SndArcInit` and 77 siblings | `autoload_2` | S: `src/matched/NNS_Snd*.c` |
| stereo screen | `ov144`, `menu/music/` | S: `extract/adm-kr/arm9_overlays/ov144.bin` |
| tune editor | `ov143`, `menu/melody/` | S: `extract/adm-kr/arm9_overlays/ov143.bin` |
| song names | `script/KOR/string/st_music.bmg` | S: `extract/adm-kr/files/script/KOR/string/` |

## Data it reads and writes

| field | meaning | who writes | who reads |
|---|---|---|---|
| SEQ index (0-375) | picks a sequence record | the game's music state | `NNS_SndArcGetSeqInfo` [S: `src/matched/NNS_SndArcGetSeqInfo.c`] |
| SEQARC index (0-215) + sub-index | picks one sequence inside an archive | the same | `NNS_SndArcPlayerStartSeqArc` [S: `src/matched/NNS_SndArcPlayerStartSeqArc.c`] |
| BANK index (0-942) | picks an instrument bank; each record names up to four wave archives | the packer | `NNS_SndArcGetBankInfo` [S: `src/matched/NNS_SndArcGetBankInfo.c`] |
| GROUP index (0-29) | a bulk-load set | the packer | `NNS_SndArcLoadGroup` [S: `src/matched/NNS_SndArcLoadGroup.c`] |
| STRM index (0-1) | a streamed track | the game | `NNS_SndArcStrmPrepare` [S: `src/matched/NNS_SndArcStrmPrepare.c`] |
| FAT entry (16 B) | file offset and size inside `FILE` | the packer | `NNS_SndArcGetFileOffset`/`GetFileSize` [S: `src/matched/NNS_SndArcGetFileOffset.c`] |

## How to check it

Static, no run required:

```bash
python - <<'PY'
import struct
d = open(r"extract/adm-kr/files/sound_data.sdat", 'rb').read()
print(d[:4], struct.unpack('<IHH', d[8:16]))
for i, nm in enumerate(('SYMB', 'INFO', 'FAT ', 'FILE')):
    o, s = struct.unpack('<II', d[16 + 8 * i:24 + 8 * i])
    print(nm, hex(o), s, d[o:o + 4] if s else b'-')
io = 0x40
offs = struct.unpack('<8I', d[io + 8:io + 40])
for nm, ro in zip(('SEQ SEQARC BANK WAVEARC PLAYER GROUP PLAYER2 STRM').split(), offs):
    c = struct.unpack('<I', d[io + ro:io + ro + 4])[0]
    e = struct.unpack('<%dI' % c, d[io + ro + 4:io + ro + 4 + 4 * c])
    print(nm, c, sum(1 for x in e if x))
PY
```

Expected: `b'SDAT' (10704768, 64, 3)`, `SYMB 0x0 0 -`, `INFO 0x40 24712 b'INFO'`,
`FAT  0x60c8 24188 b'FAT '`, `FILE 0xbf44 10655804 b'FILE'`, then the eight counts in the table
above.

For the measured audio recipe and its PCM checks, see `../systems/audio.md` and
`docs/kb/hybrid/audio.md` section 8(a) [E: `scratchpad/audio7/on`, 9,000 frames].

## Hypotheses

- **943 instrument banks is an unusually large number for 14 wave archives.** The count and the
  12-byte record size are both measured [S: the span arithmetic above], and 12 bytes is exactly
  a NitroSDK bank record (file id, padding, four wave-archive ids). Settle it by decoding all 943
  records and counting how many distinct wave-archive tuples appear — if most banks name the same
  archives, they are per-song instrument selections rather than distinct sample sets.
- **The 3,233,800-byte file in `FAT ` is one of the two streams.** It is 30% of the archive and
  far larger than any sequence could be [H: size]. Settle it by resolving both STRM records'
  file ids and checking whether either points at that entry.
- **The 34 undefined SEQ slots are cut or placeholder music.** They are the only holes in the
  whole archive [S: the SEQ offset scan]. Settle it by listing their indices and checking whether
  any GROUP record references them.
- **`st_music.bmg` at 386 bytes holds far fewer names than there are sequences**, which suggests
  it names only the collectible songs rather than the score [H: size against 342 defined
  sequences]. Settle it by reading its `INF1` entry count after decompression.
- **The stripped `SYMB` block means no name-based lookup can work at runtime**, so every call
  site must carry a numeric constant [S: `SYMB` size 0]. Settle it by confirming that no
  `NNS_SndArc*ByName`-style function is present in the symbol table — the 78 matched functions
  listed above contain none.

## Related

- `archives.md` — the `SDAT` container beside the other formats.
- `rom-layout.md` — where `sound_data.sdat` sits in the tree.
- `../engine/file-system.md` — how the archive is opened.
- `docs/kb/port/input-save-audio.md` — the port's audio status.
