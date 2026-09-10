# Audio

**Summary.** All of Wild World's sound lives in one 10.7 MB archive file, and none of it is
mixed by the processor the game runs on. The ARM9 builds a linked list of commands, hands the
list's address to the ARM7 through a single FIFO word, and waits for a counter in shared memory
to advance; the ARM7 owns the sequencer, the channels, the envelopes and the sound hardware.
**The PC port is now that ARM7.** With `ACWW_SND=1` it keeps sixteen players, thirty-two
tracks, a sixteen-channel mixer, two capture units and the output selector, steps them at the
ARM7's own 192 Hz, and hands 32,768 Hz stereo to a host sink -- the game's own music and
effects, out of the ROM's own archive. With the switch absent it walks the list and completes
every command silently, exactly as before. Everything below the summary that says "nothing
plays" has been retracted; the retraction is dated and cited.

## What happens

### The archive

There is exactly one sound file: `sound_data.sdat`, 10,704,768 bytes, SHA-256
`d89a5d75307a0c8bbb355b82d5a5189ac0938f348fffafc859fa588127edc1f5`
[H: host/prose inference from operator extraction, recorded in `docs/kb/port/input-save-audio.md`; verify against the ROM function or symbol table and this page's recipe]. Parsing its INFO and
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
them is not thereby complete [H: host/prose inference from `docs/kb/port/input-save-audio.md`; verify against the ROM function or symbol table and this page's recipe].
`extract/adm-kr/arm7/arm7.bin` exists, 166,392 bytes, and **the port does not package, load or
execute it**; `fsimage.py` publishes zero ARM7 ROM offset and size
[H: host/prose inference from `docs/kb/port/input-save-audio.md`; verify against the ROM function or symbol table and this page's recipe].

On the interpreter path the ARM7's sound processor is a host one. Until AUDIO6 it was a single
function: `snd_arm7` walked the command list from the word the ARM9 sent, read each node's id,
recorded the shared-work address when it saw id 29, printed
`acww snd7: command id N completed silently` for the first twelve, and incremented the shared
work's first word once -- the finished tag the ARM9 waits on. A zero word is the
request-processor's wake and does nothing
[E: `port/shim/os/pxisend.c`; `docs/kb/hybrid/hardware-services.md` section 1, tag 7]. That
silent walk is still what runs with `ACWW_SND` absent, and it is still the whole of the native
path.

The ARM9 command layer itself is deliberately *not* replaced: `sndcmd.c`, `sndflush.c` and
`sndtag.c` are on the deny list so the ROM's own `SND_*Command` functions run, and an earlier
guard that accepted only id 29 aborted the boot [E: `port/tools/interp_registry.py`;
`docs/log/cycle40-keyboard-gate-probe.md` `off-D44`]. The archive comes from the filesystem
rather than from a host facade, and that too was forced: the host sound facade answered "no
archive", the ROM's `func_020f4b1c` got NULL back from `NNS_SndArcGetSeqArcParam`, called the
ROM's own fatal path `func_0206e3ec`, and the ROM's crash screen looped from frame ~830 with
both screens black [E: `docs/log/cycle40-keyboard-gate-probe.md` CARD40..SND40]. Fourteen sound
files are denied in all so the ROM's own bodies are used: eleven archive, player and heap files
(`sndinit.c`, `sndfacade.c`, `sndframe.c`, `sndstart.c`, `sndplay.c`, `snd_playeropen.c`,
`sequpdate.c`, `arcinfofamily.c`, `arcbankinfo.c`, `arcseqinfo.c`, `sndheapstate.c`) plus the
three command-layer files above
[S: `port/tools/interp_registry.py`, `DENY_FILES`, counted].

On the older native path, tag 7 instead reaches a narrow service that keeps real free, reserve
and pending lists matching the SDK's shared-work layout but recognises only id 29 and rejects
everything else [E: `port/shim/os/pxisend.c`, `port/shim/audio/w12_sndservice.h`;
`docs/kb/port/input-save-audio.md`].

### The host ARM7 sound driver (`ACWW_SND=1`)

~~**Nothing plays.**~~ **Retracted 2026-09-09 (AUDIO6, `115984f9`; AUDIO7, `36ee5abe`).** The
port plays the game's own music and sound effects. `port/shim/audio/driver.c` is the ARM7
command processor over the SNDWork blocks the ROM sends on tag 7; `port/shim/audio/capture.c`
is the two capture units, the output selector and the surround decay;
`port/shim/audio/sink_win32.c` is a WASAPI (waveOut fallback) sink pulled by a host thread; the
mixer is rendered per frame from the frame boundary at the ARM7's own 192 Hz
[E: `docs/kb/hybrid/audio.md` sections 1, 6 and 7]. **There is no host archive**: the ROM's own
`NNS_SndArcInit` opens `/sound_data.sdat` through the port's virtual cartridge, and the pointers
`PREPARE_SEQ` carries are NDS addresses, so `sdat.c` stays out of the link
[E: same, section 2]. The first silent run was `swav.c` reading `waveOffset[]` as file offsets
where this ROM's WAVEARC flag `0x01` makes them NDS addresses
[S: `src/matched/SND_GetWaveDataAddress.c`'s branch].

**The command census.** The instrument it replaced printed twelve lines and stopped, so every
`PREPARE_SEQ` the game ever sent was invisible and the audit's own hypothesis could not be
tested at all -- an artefact of the instrument, not of the game (M1)
[E: `docs/kb/hybrid/audio.md` section 3]. The census is uncapped now and runs whether or not the
driver is on. Ids 0-4, 6-17, 19-33 are dispatched; `SKIP_SEQ` (5) and `SETUP_ALARM` (18) are
logged only, `SETUP_ALARM` because firing it sends a word back into game code over PXI and so
changes the game rather than the sound [E: same]. **This ROM never sends id 33**
`READ_DRIVER_INFO`: the uncapped census over the 9,000-frame OFF recipe lists ids 0-32 and no 33
[E: same, section 10; `scratchpad/audio7/`].

**The bring-up, as the ROM sends it**, printed from a bounded per-id argument log rather than
predicted [E: `docs/kb/hybrid/audio.md` section 7; `scratchpad/audio7/args/run-tail.log`, frame 3]:
`SURROUND_DECAY 0x3000`, then `LOCK_CHANNEL 0x000a` -- channels 1 and 3 out of the allocator --
then those two channels programmed as PCM at timer 512, hard left and hard right, over two
512-word buffers; then two `SETUP_CAPTURE` on **the same two buffers** from the MIXER with the
loop bit set; then `SETUP_ALARM` at half the buffer's duration; then
**`OUTPUT_SELECTOR 1 2 1 1`** -- left from Ch1, right from Ch3, both bypassing the mixer -- and
`START_TIMER`. The replay channels and the capture units share one buffer and one clock, so the
speakers hear the mixer delayed by exactly one buffer, re-panned hard left and hard right, while
the surround decay attenuates every channel EXCEPT 1 and 3. That is the DS's pseudo-surround
[E: same; P: GBATEK, "the sample frequency of Channel 1/3 is shared for Capture 0/1"].

**The receipt that the selector is obeyed** is a cross-correlation between the same binary with
`ACWW_SND_CAPTURE=0` and with it default: the peak is at **lag 1,025 samples = 31.28 ms,
coefficient 0.9962**, against 0.2530 at lag zero. The arithmetic predicts 1,024 (512 words at
timer 512) and the extra sample is the read preceding the write inside one mixer step. A driver
that ignored the selector would correlate 1.0000 at lag 0 and nothing anywhere else
[E: `scratchpad/audio7/wavcmp-nocap-vs-on.txt`; `docs/kb/hybrid/audio.md` section 8].

**The tables are read from this ROM's own images, not reconstructed.** `AttackCoeffTable` is at
`arm7.bin+0xf2e0` and `SNDi_DecibelSquareTable` at `arm7.bin+0xf1cc`; `SNDi_DecibelTable` is at
`unk_autoload_2.bin+0x54dcc` [S: those images; `port/tools/test_sndrender.py` re-reads all three
at pinned offsets on every run]. Two of the three grade-H reconstructions were byte-identical;
**the error was not a table but WHICH table** -- velocity, both track volumes, the player volume
and the envelope's sustain level all go through `SND_CalcDecibelSquare`, not `SND_CalcDecibel`,
and the two curves are four decibels apart mid-scale (volume 64 is -239 tenths in the square
table against -60 in the plain one) [S: the ROM images; P: NitroSDK `snd_seq.c`,
`snd_exchannel.c`]. **Entry 0 of both tables is -723 in this ROM where the public NitroSDK has
-32768**; that is a different revision of the library, and the disagreement is content, not
noise -- a driver built on the public value clamps a chain containing a zero term to silence
where this ROM does not (STYLE rule 7) [S: the images vs P: the public source]. The allocator
walks channels in the library's own order `{4,5,6,7, 2,0, 3,1, 8,9,10,11, 14,12,15,13}` and
breaks ties on the QUIETER channel's hardware volume word, not on allocation age -- which is
what keeps ordinary notes off channels 0..3 while any of 4..7 is free, exactly the quartet the
capture path uses [P: NitroSDK `snd_exchannel.c`, `SND_AllocExChannel` and
`CompareExChannelVolume`; E: `port/shim/audio/driver.c` walks that order, and
`port/tools/test_sndrender.py` holds the 418/418 note count across the change].

**Publishing `playerStatus` changed what the game does, and that is the finding.**
`NNSi_SndPlayerMain` shuts a player down the moment `playerStatus` does not carry its bit
[S: `src/matched/NNSi_SndPlayerMain.c`]. Against the silent ARM7 that bit was never set, so
**every piece of music the game started was torn down and restarted for the whole run** -- 967
`PREPARE_SEQ` where 371 suffice, and 590 bank invalidations where 6 suffice. The port had been
doing that all along and nothing showed it [E: `docs/kb/hybrid/audio.md` section 8(c)].
`ACWW_SND_SHARED=0` is the escape, and it exists because publishing status is a change to what
the game can SEE.

**What it does not change: the picture.** OFF recipe, four arms one environment variable apart
(the untouched build, `ACWW_SND=0`, `ACWW_SND=1` with the capture path off, and with it on):
**31 of 31 frames exact (RGB) in every pairing**, mean ncc 1.0000
[E: `scratchpad/audio7/frame-exactness.txt`]. Over the whole 48,000-frame town recipe,
`ACWW_SND` unset against `ACWW_SND=1` is **15 of 15 shots byte-identical**, both exit 100
[E: `scratchpad/stab42/`; STAB42]. With `ACWW_SND` unset the sink thread is never created at
all.

**The milestones, and what each closed.** Milestone 6 is the driver and the sink (AUDIO6,
`115984f9`); milestone 7 is the capture path, which removed milestone 6's one deliberate
deviation -- the port had played the mixer straight and ignored the output selector; milestone 8
is `READ_DRIVER_INFO` and the differential (both AUDIO7, `36ee5abe`). All eight steps of the
audit's build order are done [S: `../audits/audio-design.md` section 2, "Build order"].
Fixtures: `port/tools/test_sndrender.py` 22/22 (three of them grade S against this ROM's
images), `port/tools/test_snddispatch.py` 31/31 with three calibrations -- one of which replays
the ROM's own twelve bring-up commands and requires the speakers to go to **peak 0** when the
one `START_TIMER` bit that starts the capture units is removed, because the replay channels are
then reading a buffer nothing fills. A driver that ignored the selector is equally loud in both
[E: `docs/kb/hybrid/audio.md` section 8(d)].

**Not receipted: the sink itself.** On this machine `waveOutGetNumDevs()` returns 0 and WASAPI's
`GetDefaultAudioEndpoint` returns `ERROR_NOT_FOUND`, although the machine has nine audio devices
and Audiosrv is running; `CoCreateInstance` on `MMDeviceEnumerator` succeeds, so the COM path up
to the endpoint is exercised and nothing past it is. Every failing step prints its HRESULT, and
`scratchpad/audio6/sinktest.py` pushes a square wave through the sink alone
[E: `docs/kb/hybrid/audio.md` section 8].

### The smallest audible slice -- taken, and the whole archive with it

Archive 0, index 121 was the identified candidate and it is still the fixture's spine: sequence
archive 0 entry 121 is eight sequence bytes (rest, program, one note, end), bank 154, wave
archive 4, wave 42, one 6,020-byte DS ADPCM payload [S: `docs/kb/port/input-save-audio.md`;
confirmed field by field in `../audits/audio-design.md` section 3]. The two offline decoders
that disagreed on 12,033 samples against 12,032 were settled by GBATEK against the ADPCM header:
**12,032**, and SWAV 42 is now asserted sample for sample by the fixture
[P: `gbatek-ds-sound-channels-0-15.htm`; S: `../audits/audio-design.md` section 3].

~~The planning estimates recorded are 2-4 weeks for a first command-service audible slice and
7-12 weeks for a robust host emulation.~~ **Overtaken by events**: the driver, the capture path
and the differential's tooling were built in one night
[E: `docs/log/cycle40-keyboard-gate-probe.md` AUDIO6 and AUDIO7]. On the OFF recipe the port
sounded **418 notes of 418 attempted, none dropped**, across 371 sequences, 16 channels at once,
28,877 driver frames for 9,000 game frames (192/59.8261 x 9,000 = 28,884), first sound at frame
36-38, and wrote a 150.40 s WAV against the 150.44 s the recipe asks for
[E: `scratchpad/audio7/on/capture.wav`; `docs/kb/hybrid/audio.md` section 8(a)].

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
| `acww_snd_command` (`driver.c`) | port | the host ARM7: sixteen players, thirty-two tracks, a sixteen-channel mixer, the census | [E: `port/shim/audio/driver.c`; `docs/kb/hybrid/audio.md` section 3] |
| `capture.c` | port | the two capture units, `OUTPUT_SELECTOR`, the surround decay, the hardware channels | [E: `port/shim/audio/capture.c`; `docs/kb/hybrid/audio.md` section 7] |
| `sink_win32.c` | port | the only thread boundary: a 65,536-frame lock-free ring into WASAPI, waveOut fallback | [H: host-source account from `port/shim/audio/sink_win32.c`; verify with a retained scripted run and frame using this page's recipe] |
| `SND_CalcDecibelSquare` `arm7.bin+0xf1cc` (table) | ARM7 image | the table velocity, both track volumes, the player volume and the sustain level go through | [S: `extract/adm-kr/arm7/arm7.bin`, re-read by `port/tools/test_sndrender.py`] |
| `SNDi_DecibelTable` `unk_autoload_2.bin+0x54dcc`, `AttackCoeffTable` `arm7.bin+0xf2e0` | images | the other two constant tables; entry 0 of both decibel tables is **-723** in this ROM | [S: the same two images] |

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
| node `+0x00` / `+0x04` / `+0x08` | next pointer, command id, first argument | `SND_AllocCommand` and the builders | the ARM7 (the port reads all three) [H: source/log account from `port/shim/os/pxisend.c`; verify with a retained run using this page's recipe] |
| PXI tag 7 | the one word carrying the command list's address | `SND_FlushCommand` | `snd_arm7` [H: source/log account from `port/shim/os/pxisend.c`; verify with a retained run using this page's recipe] |
| `sound_data.sdat` | the whole archive: 336 sequences, 216 sequence archives, 943 banks, 14 wave archives, 2 streams | the ROM image | `NNS_SndArc*` through the filesystem [S: `docs/kb/port/input-save-audio.md`] |
| shared work `+0x04` `playerStatus` | which of the sixteen players is live | the ARM7 (the port, inside `PREPARE_SEQ` / `STOP_SEQ`) | `NNSi_SndPlayerMain`, which SHUTS a player down when its bit is clear [S: `src/matched/NNSi_SndPlayerMain.c`; E: `docs/kb/hybrid/audio.md` section 5] |
| shared work `+0x08` / `+0x0a` `channelStatus` / `captureStatus` | which channels and capture units are running | the ARM7 (the port) | ARM9 sound code; the only ARM7 state the rest of the machine can see [S: `src/matched/SND_GetPlayerStatus.c`] |
| the two 512-word buffers at `0x02143420` / `0x02143c20` | one per capture unit, shared with replay channels 1 and 3 | capture unit 0/1 (the port's `capture.c`) | channels 1 and 3, one buffer behind [E: `scratchpad/audio7/args/run-tail.log`] |

## How to check it

`../experiments/silent-audio-probe.md` asked which command ids the game actually emits. That is
answered: run the OFF recipe (`off-recipe.md`) with the driver on and read the census the run
prints at its stop.

    # every run prints `acww snd7 census:` whether or not the driver is on
    ACWW_SND=1 ACWW_SND_NOSINK=1 ACWW_SND_WAV=<path>.wav <the OFF recipe>

`ACWW_SND_CAPTURE=0` is the arm that turns milestone 7 back off, which is what the before/after
receipt is measured across; `ACWW_SND_SHARED=0` stops the port publishing status back to the
ARM9; `ACWW_SND_DUMP=<frames>:<path>` writes the port's half of the milestone-8 differential
[E: `docs/kb/hybrid/audio.md` section 6]. Without a ROM at all,
`python port/tools/test_snddispatch.py` (31 checks, three calibrations) and
`python port/tools/test_sndrender.py` (22 checks, three of them against this ROM's images) are
the fixtures [E: same, section 8(d)].

## Hypotheses

- ~~The silent ARM7 is adequate for the game's logic indefinitely.~~ **Settled 2026-09-09
  (AUDIO6), and it was not.** The mechanism named here was the right one: against a consumer
  that never set `playerStatus`, `NNSi_SndPlayerMain` tore every started sequence down and the
  game restarted it -- 967 `PREPARE_SEQ` over the OFF recipe where 371 suffice, and 590 bank
  invalidations where 6 suffice. Nothing STALLED, so the 90,000-frame evidence stands; what was
  wrong was "adequate" [E: `docs/kb/hybrid/audio.md` section 8(c);
  S: `src/matched/NNSi_SndPlayerMain.c`].
- **H: the mix is CORRECT, not merely present.** Nothing has yet compared the port's driver
  state against the original's. `SNDSharedWork` is the only comparable part -- it is in main RAM
  because the ARM9 owns it, and it is also the only part of the driver game code can see;
  `SNDi_Work` and the sixteen SOUNDxCNT registers are ARM7-side and DeSmuME 0.9.13's Lua reaches
  neither, and nothing can inject an ARM9 `READ_DRIVER_INFO` into a running emulator. Both
  halves of the tooling exist (`ACWW_SND_DUMP`, `oracle.py --snd-dump/--snd-shared`,
  `port/tools/oracle/snddiff.py`); **the emulator would not start in the session milestone 8 was
  written in** -- three attempts, each leaving the process alive, responding, and having used
  1.1 s of CPU in 675 s, with the pre-milestone-8 observer too, so it is an environment fact and
  not a Lua one. Settled by running `port/tools/oracle/oracle.py --frames 100` unchanged and
  finding out why [E: `docs/kb/hybrid/audio.md` section 10].
- **H: channels 6 and 7 looping is closer to hardware than not playing them.** From frame 819
  the game programs them as hardware PCM -- NitroSDK's streamed path -- and with `SETUP_ALARM`
  not fired nothing advances the stream's buffer, so they replay whatever the ARM9 last wrote.
  Milestone 6 played them not at all, milestone 7 plays them looping; which is right is not
  established. Settled by the differential above, pointed at those two channels first
  [E: `docs/kb/hybrid/audio.md` section 7].
- **H: 24 MB of decoded-wave arena is enough for a long session.** The arena is a bump
  allocator; when it fills, every channel is stopped, the cache is dropped and it is rewound --
  one click rather than permanent silence. The OFF recipe recycles it zero times. Settled by a
  long live session with the run report's recycle counter read at the end
  [E: `docs/kb/hybrid/audio.md` section 11].
- ACWW selects background music by the hour, as the series does. **No such table or function was
  found** among matched, sound-named symbols, and the RTC files reference no sound symbol
  [S: absence in `src/matched`]. If it exists it is inside one of the four undecompiled callers
  of the start boundary. Settled by disassembling `func_020f1fb4` and looking for a hour-indexed
  table feeding its index argument.
- ~~Archive 0 index 121 is reachable in ordinary play and would make the first sound.~~ **The
  second half is settled and false**: the first sound of an OFF run happens at frame 36-38 and
  418 notes sound over 9,000 frames, so whatever plays first, it is not waiting on that chain
  [E: `docs/kb/hybrid/audio.md` section 8(a)]. Whether index 121 is reached at all is still
  open, and the uncapped census is now the instrument for it. The original wording follows.
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

- `../experiments/silent-audio-probe.md`, `../experiments/two-tap-town-recipe.md`,
  `../experiments/off-recipe.md` -- the control every audio receipt is taken on.
- `../audits/audio-design.md` -- the command table, the archive's claims table and the
  eight-step build order, all eight steps of which are done.
- `../audits/night-2026-09-09.md` -- AUDIO6 and AUDIO7 in the night's index.
- `network.md` -- `DWCi_SNDl*` is the other consumer of the player path.
- `docs/kb/hybrid/audio.md` -- the implementation page: what is dispatched, what is a
  deliberate no-op, what is only logged, and every receipt behind this page.
