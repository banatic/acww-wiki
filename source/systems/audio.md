# Audio

**Summary.** All of Wild World's sound lives in one 10.7 MB archive file, and none of it is
mixed by the processor the game runs on. The ARM9 builds a linked list of commands, hands the
list's address to the ARM7 through a single FIFO word, and waits for a counter in shared memory
to advance; the ARM7 owns the sequencer, the channels, the envelopes and the sound hardware.
The PC port answers that protocol and plays nothing: it walks the command list, completes every
command silently and bumps the counter. That is enough to keep the game running for 90,000
frames and is not a step toward audio.

## What happens

### The archive

There is exactly one sound file: `sound_data.sdat`, 10,704,768 bytes, SHA-256
`d89a5d75307a0c8bbb355b82d5a5189ac0938f348fffafc859fa588127edc1f5`
[S: operator extraction, recorded in `docs/kb/port/input-save-audio.md`]. Parsing its INFO and
FAT blocks directly gives 376 SEQ table slots but only 342 defined records and 336 distinct
physical sequence files; 216 sequence archives holding 5,550 entries; 943 banks; 14 wave
archives; and 2 streams [S: same]. **Those are three different denominators and "376 SEQ
assets" collapses them** [S: same; M1].

The `NNS_SndArc*` layer is what reads that structure. `NNS_SndArcInit` opens and validates an
archive from the card, `NNS_SndArcInitOnMemory` from an image already in RAM, and
`NNS_SndArcSetCurrent` records which handle later calls default to
[S: `NNS_SndArcInit`, `src/matched/NNS_SndArcInit.c`]. Per-type accessors then read the INFO
block -- `NNS_SndArcGetBankInfo`, `GetSeqInfo`, `GetSeqArcInfo`, `GetSeqArcParam`,
`GetWaveArcInfo`, `GetGroupInfo`, `GetPlayerInfo`, `GetStrmInfo`
[S: `src/matched/NNS_SndArcGetSeqArcParam.c` and siblings] -- and `NNS_SndArcLoadGroup` pulls a
named group of assets in through the internal per-type loaders `NNSi_SndArcLoadBank`,
`LoadSeq`, `LoadSeqArc`, `LoadWaveArc`, `LoadFile` [S: `src/matched/NNS_SndArcLoadGroup.c`].
Everything the library allocates comes from its own expanding heap with save/restore
watermarks: `NNS_SndHeapCreate`, `Alloc`, `SaveState`, `LoadState`
[S: `src/matched/NNS_SndHeapSaveState.c`].

### Playing a sequence

`NNS_SndArcPlayerStartSeqArc` at `0x0210e4c4` is the three-argument boundary
`(handle, seqArcNo, index)` [S: `src/matched/NNS_SndArcPlayerStartSeqArc.c`;
`docs/kb/port/input-save-audio.md`]. Exhaustive direct cross-referencing found six ROM calls in
five functions: `func_020eedb8` once, `func_020f609c` twice, `func_020f6350` once,
`func_020f7bc4` once, and `DWCi_SNDlPlay` once through the raw address. `func_020eedb8`
deliberately permutes its arguments into that order, which is not a tracer defect
[S: `docs/kb/port/input-save-audio.md`].

Below that, `NNSi_SndPlayerStartSeq` calls the SDK driver's `SND_PrepareSeq`, which allocates a
command node with `SND_AllocCommand` from a 256-entry pool, fills it, and appends it to a
reserve list with `SND_PushCommand` -- nothing is sent yet
[S: `src/matched/NNSi_SndPlayerStartSeq.c`, `src/matched/SND_PrepareSeq.c`,
`src/matched/SND_PushCommand.c`]. `SND_FlushCommand` moves the whole reserve list onto the
pending list and sends **the address of the linked list** as one 32-bit word on PXI tag 7,
retrying while the FIFO is full [S: `src/matched/SND_FlushCommand.c`]. Command batching is
therefore the norm: commands accumulate and only travel on a flush.

Command id 29, `SHARED_WORK`, is how the ARM7 learns the address of the block both processors
use for bookkeeping. After processing a whole list the ARM7 increments that block's first word,
`finishCommandTag`; on the ARM9 side `SND_RecvCommandReply` reads it, walks the completed nodes
and recycles them onto the free list, while `SND_IsFinishedCommandTag` and
`SND_WaitForCommandProc` let a caller test or spin on completion
[S: `src/matched/SND_RecvCommandReply.c`, `src/matched/SND_WaitForCommandProc.c`,
`src/matched/SNDi_InitSharedWork.c`].

The command ids that a real playback needs are known and ordered: a restored request emits id 2
`PREPARE_SEQ` unconditionally; id 9 `ALLOCATABLE_CHANNEL` follows only when the player's
allocation mask is non-zero; on the later player-main step id 6 `PLAYER_PARAM` is emitted only
when the computed fader or volume differs, and a still-prepared player emits id 3
`START_PREPARED_SEQ` [S: `docs/kb/port/input-save-audio.md`].

The shared-work layout was recovered by exact PC and literal cross-checks after
declaration-order inference had assigned six of its fields wrongly: free head `0x022045c8`,
reclaimed tag `0x022045cc`, reserve head and end `0x022045d0` / `0x022045d4`, free tail
`0x022045d8`, pending read and write `0x022045dc` / `0x022045e0`, pending batch count
`0x022045e4`, current submission tag `0x022045e8`, a nine-entry queue at `0x022045ec`, the
256-entry command array at `0x022048a0`, and the shared block and its pointer at `0x02204620`
and `0x022060a0` [S: `docs/kb/port/input-save-audio.md`; retraction in
`docs/log/report-w12.md`].

Above all of this sit the players (volume, pitch, per-track parameters, channel priority,
sequence variables), the fader that ramps volumes, the stream path for the two STRM assets, and
a capture thread that applies an output effect to the final mix
[S: `src/matched/NNS_SndPlayerSetTrackVolume.c`, `src/matched/NNSi_SndFaderUpdate.c`,
`src/matched/NNS_SndStrmStart.c`, `src/matched/NNSi_SndCaptureMain.c`].

### What the port does

The ARM9 half is ROM code and runs. The contiguous SDK library blocks resolve 257 of 257 matched
symbols -- 187 NNS sound, 69 Nitro SND and one ITCM alarm handler -- though the game glue above
them is not thereby complete [S: `docs/kb/port/input-save-audio.md`].
`extract/adm-kr/arm7/arm7.bin` exists, 166,392 bytes, and **the port does not package, load or
execute it**; `fsimage.py` publishes zero ARM7 ROM offset and size
[S: `docs/kb/port/input-save-audio.md`].

On the interpreter path the whole ARM7 sound processor is one function. `snd_arm7` walks the
command list from the word the ARM9 sent, reads each node's id, records the shared-work address
when it sees id 29, prints `acww snd7: command id N completed silently` for the first twelve,
and then increments the shared work's first word once -- the finished tag the ARM9 waits on. A
zero word is the request-processor's wake and does nothing
[E: `port/shim/os/pxisend.c`; `docs/kb/hybrid/hardware-services.md` section 1, tag 7].

The ARM9 command layer itself is deliberately *not* replaced: `sndcmd.c`, `sndflush.c` and
`sndtag.c` are on the deny list so the ROM's own `SND_*Command` functions run, and an earlier
guard that accepted only id 29 aborted the boot [E: `port/tools/interp_registry.py`;
`docs/log/cycle40-keyboard-gate-probe.md` `off-D44`]. The archive comes from the filesystem
rather than from a host facade, and that too was forced: the host sound facade answered "no
archive", the ROM's `func_020f4b1c` got NULL back from `NNS_SndArcGetSeqArcParam`, called the
ROM's own fatal path `func_0206e3ec`, and the ROM's crash screen looped from frame ~830 with
both screens black [E: `docs/log/cycle40-keyboard-gate-probe.md` CARD40..SND40]. Fourteen sound files are denied in all so the ROM's own bodies are used: eleven archive,
player and heap files (`sndinit.c`, `sndfacade.c`, `sndframe.c`, `sndstart.c`, `sndplay.c`,
`snd_playeropen.c`, `sequpdate.c`, `arcinfofamily.c`, `arcbankinfo.c`, `arcseqinfo.c`,
`sndheapstate.c`) plus the three command-layer files above
[S: `port/tools/interp_registry.py`, `DENY_FILES`, counted].

On the older native path, tag 7 instead reaches a narrow service that keeps real free, reserve
and pending lists matching the SDK's shared-work layout but recognises only id 29 and rejects
everything else [E: `port/shim/os/pxisend.c`, `port/shim/audio/w12_sndservice.h`;
`docs/kb/port/input-save-audio.md`].

**Nothing plays.** The knowledge base states the boundary precisely: transport alone cannot
interpret a sequence, resolve a bank or wave archive, allocate channels, advance envelopes and
timers, or produce PCM [S: `docs/kb/port/input-save-audio.md`].

### The smallest audible slice, and why it has not been taken

Archive 0, index 121 is the identified candidate: sequence-archive 0 entry 121 is eight
sequence bytes (rest, program, one note, end), selects bank 154, then wave archive 4 and wave
42, one 6,020-byte DS ADPCM payload [S: `docs/kb/port/input-save-audio.md`]. Static
reachability finds `func_020089dc -> func_020f1fb4(..., 0x79) -> func_020eede8 ->
func_020eedb8`, encoding handle `0x021fd04c`, archive 0, index 121 -- but it did not execute in
the measured cold START run through frame 12,000, its selector staying zero
[S: `docs/kb/port/input-save-audio.md`]. Two offline decoders disagree on whether the ADPCM
predictor header is an emitted sample, 12,033 samples against 12,032, so neither is a fidelity
golden [S: same]. The planning estimates recorded are 2-4 weeks for a first command-service
audible slice and 7-12 weeks for a robust host emulation, with hosting the real ARM7 a 1-2 week
feasibility study and an 8-14+ week route [S: same; they are estimates and were not calibrated].

## Where it lives

| function or symbol | module | role | grade/citation |
|---|---|---|---|
| `NNS_SndInit`, `NNS_SndMain` | autoload_2 (NNS) | library bring-up; the per-frame tick that drains replies and updates faders | [S: `src/matched/NNS_SndMain.c`] |
| `NNS_SndArcInit`, `NNS_SndArcInitOnMemory`, `NNS_SndArcSetup` | autoload_2 (NNS) | open and validate the archive | [S: `src/matched/NNS_SndArcInit.c`] |
| `NNS_SndArcGetSeqArcParam` | autoload_2 (NNS) | the INFO accessor whose NULL sent the ROM to its fatal path in the port | [S: `src/matched/NNS_SndArcGetSeqArcParam.c`] [E: SND40] |
| `NNS_SndArcLoadGroup`, `NNSi_SndArcLoadBank`, `NNSi_SndArcLoadWaveArc` | autoload_2 (NNS) | bulk and per-type asset loading | [S: `src/matched/NNS_SndArcLoadGroup.c`] |
| `NNS_SndArcPlayerStartSeqArc` `0x0210e4c4` | autoload_2 (NNS) | the `(handle, seqArcNo, index)` request boundary; six ROM callers | [S: `src/matched/NNS_SndArcPlayerStartSeqArc.c`] |
| `NNSi_SndPlayerStartSeq` `0x0210b148` / `NNSi_SndPlayerStopSeq` | autoload_2 (NNS) | the internal start and stop that call into the SDK driver | [S: `src/matched/NNSi_SndPlayerStartSeq.c`] |
| `NNS_SndHeapCreate`, `Alloc`, `SaveState`, `LoadState` | autoload_2 (NNS) | the library's own expanding heap with watermarks | [S: `src/matched/NNS_SndHeapSaveState.c`] |
| `NNSi_SndFaderUpdate` and four siblings | autoload_2 (NNS) | the volume ramp shared by players and streams | [S: `src/matched/NNSi_SndFaderUpdate.c`] |
| `NNS_SndStrmStart`, `NNS_SndArcStrmPrepare` | autoload_2 (NNS) | streamed playback, direct and from the archive | [S: `src/matched/NNS_SndStrmStart.c`] |
| `NNSi_SndCaptureMain`, `NNS_SndCaptureStartOutputEffect` | autoload_2 (NNS) | the capture thread and the final-mix output effect | [S: `src/matched/NNSi_SndCaptureMain.c`] |
| `SND_Init`, `SNDi_InitSharedWork` | autoload_2 (SND) | driver init and the shared-work block's field layout | [S: `src/matched/SNDi_InitSharedWork.c`] |
| `SND_AllocCommand`, `SND_PushCommand`, `SND_FlushCommand` | autoload_2 (SND) | allocate from the 256-node pool, reserve, then send the list address on tag 7 | [S: `src/matched/SND_FlushCommand.c`] |
| `SND_RecvCommandReply`, `SND_IsFinishedCommandTag`, `SND_WaitForCommandProc` | autoload_2 (SND) | completion: read the finished tag, reclaim nodes, or spin | [S: `src/matched/SND_RecvCommandReply.c`] |
| `SND_PrepareSeq` `0x02118204` / `SND_StartPreparedSeq` / `SND_StopSeq` | autoload_2 (SND) | command ids 2, 3 and the stop | [S: `src/matched/SND_PrepareSeq.c`] |
| `SNDi_SetPlayerParam`, `SNDi_SetTrackParam` | autoload_2 (SND) | the id 6 `PLAYER_PARAM` builders | [S: `src/matched/SNDi_SetPlayerParam.c`] |
| `SND_SetupChannelPcm`, `SND_CalcChannelVolume`, `SND_SetMasterVolume` | autoload_2 (SND) | channel and mixer-adjacent setup | [S: `src/matched/SND_SetupChannelPcm.c`] |
| `PXI_SendWordByFifo` | autoload_2 | the FIFO word send tag 7 rides on | [S: `src/matched/PXI_SendWordByFifo.c`] [E: replaced by `port/shim/os/pxisend.c`] |
| `DWCi_SNDlPlay`, `_Stop`, `_SetVolume`, `_SetPitch` | libdwcac | the network UI's hooks into the same player path | [S: `src/matched/DWCi_SNDlPlay.c`] |
| `func_020eedb8`, `func_020f609c`, `func_020f6350`, `func_020f7bc4` | main | the four game-glue callers of the start boundary; not decompiled | [S: `docs/kb/port/input-save-audio.md`] |

## Data it reads and writes

| address or field | meaning | who writes | who reads |
|---|---|---|---|
| `0x02204620` | the shared work block; its first word is `finishCommandTag` | the ARM7 (the port: `snd_arm7`) | `SND_RecvCommandReply`, `SND_IsFinishedCommandTag` [S: `docs/kb/port/input-save-audio.md`] |
| `0x022060a0` | the pointer to that block | `SNDi_InitSharedWork` | the driver [S: same] |
| `0x022048a0` | the 256-entry command array | `SND_AllocCommand` | the ARM7 [S: same] |
| `0x022045c8` / `0x022045d8` | command free-list head and tail | `SND_AllocCommand`, `SND_RecvCommandReply` | the allocator [S: same] |
| `0x022045d0` / `0x022045d4` | reserve-list head and end | `SND_PushCommand` | `SND_FlushCommand` [S: same] |
| `0x022045dc` / `0x022045e0` / `0x022045e4` | pending read index, write index, batch count | `SND_FlushCommand` | the reply path [S: same] |
| `0x022045cc` / `0x022045e8` | reclaimed tag and current submission tag | the reply path / `SND_FlushCommand` | `SND_WaitForCommandProc` [S: same] |
| node `+0x00` / `+0x04` / `+0x08` | next pointer, command id, first argument | `SND_AllocCommand` and the builders | the ARM7 (the port reads all three) [E: `port/shim/os/pxisend.c`] |
| PXI tag 7 | the one word carrying the command list's address | `SND_FlushCommand` | `snd_arm7` [E: `port/shim/os/pxisend.c`] |
| `sound_data.sdat` | the whole archive: 336 sequences, 216 sequence archives, 943 banks, 14 wave archives, 2 streams | the ROM image | `NNS_SndArc*` through the filesystem [S: `docs/kb/port/input-save-audio.md`] |

## How to check it

`../experiments/silent-audio-probe.md` (designed, not yet run) reads the `acww snd7:` lines out
of a town run and asks which command ids the game actually emits on the way to the town hall --
which is the cheapest way to find out whether 2, 9, 6 and 3 are ever reached, and therefore how
much of a host sequencer a first audible slice would need.

## Hypotheses

- The silent ARM7 is adequate for the game's logic indefinitely. Evidence for: 90,000 frames
  with no re-entry into the ROM's fatal path [E: `scratchpad/cycle40/runs/tap-D59`, LONG41]. It
  remains a hypothesis because the ROM's sound stack runs against a consumer that never reports
  a real player state, so a sequence whose progression the game waits on would stall. Settled by
  an oracle comparison over a scene with music-driven timing
  [S: `docs/kb/hybrid/hardware-services.md` section 7].
- ACWW selects background music by the hour, as the series does. **No such table or function was
  found** among matched, sound-named symbols, and the RTC files reference no sound symbol
  [S: absence in `src/matched`]. If it exists it is inside one of the four undecompiled callers
  of the start boundary. Settled by disassembling `func_020f1fb4` and looking for a hour-indexed
  table feeding its index argument.
- Archive 0 index 121 is reachable in ordinary play and would make the first sound. It was not
  requested in the measured cold START run through frame 12,000 -- but that run sampled only 19
  of at least 128 requests, so general sampling cannot establish its absence
  [S: `docs/kb/port/input-save-audio.md`; M11]. Settled by an uncapped request trace over a town
  run.
- The first sampled request in that historical run, archive 19169 / index 280, is upstream
  corruption rather than a real request: none of the six audited direct call sites statically
  supplies that composite, and `DWCi_SNDlPlay` fixes the archive to zero. It is a lead, not a
  diagnosis; indirect dispatch, stale state and corrupt data are not yet separated
  [S: `docs/kb/port/input-save-audio.md`].

## Related

- `../experiments/silent-audio-probe.md`, `../experiments/two-tap-town-recipe.md`.
- `network.md` -- `DWCi_SNDl*` is the other consumer of the player path.
