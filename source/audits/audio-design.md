# Audit and design: a host-side ARM7 sound driver

verified-at: 115984f9 2026-09-09

**Purpose.** This page was written when the port was silent and the host "ARM7" completed every
command without producing a sample. **That is no longer true**: ALL EIGHT build-order steps
below are done and `ACWW_SND=1` plays the game's music and effects, through the capture path
the game actually asks for (`docs/kb/hybrid/audio.md`). The page
is kept as the DESIGN and the AUDIT it was, because its command table, its argument
decomposition and its claims table are what the driver was built from and are still correct.
It does three jobs: it names the exact command set that boundary carries, it designs the host
driver that would answer it with sound, and it audits `systems/audio.md` and `data/music.md`
against the public record. No code is copied here; structures are described and cited.

**Grade P (public)** follows `data-formats.md`: a public document — GBATEK, a vendor header, a
decompilation of the same library — carries a URL. **P never replaces S, E or O.** Where P and
S disagree, S wins and the disagreement is content (STYLE rule 7). The unusual thing about this
subject is how much of it is grade **S**: `src/matched/` contains real NitroSDK 2.2a and NNS
library translation units, so the command enum, the argument packing, the shared-work layout,
the driver's own state structures and the SDAT record structs are all readable from this repo.

## Sources consulted

| source | URL | covers |
|---|---|---|
| NitroSDK `nitro/snd/common/command.h` | `https://raw.githubusercontent.com/ntrtwl/NitroSDK/main/include/nitro/snd/common/command.h` | the `SNDCommandID` enum, the node struct, the push flags |
| NitroSDK `nitro/snd/common/mml.h` | `https://raw.githubusercontent.com/ntrtwl/NitroSDK/main/include/nitro/snd/common/mml.h` | the SSEQ opcode names |
| NitroSDK `seq.h`, `bank.h`, `channel.h`, `exchannel.h`, `main.h`, `alarm.h`, `work.h` | same tree, `include/nitro/snd/common/` | player/track/channel limits, instrument types, `SND_PROC_INTERVAL` |
| pret/pokediamond ARM7 SND decomp | `https://raw.githubusercontent.com/pret/pokediamond/master/arm7/lib/src/SND_command.c` (and `SND_main.c`, `SND_seq.c`, `SND_exChannel.c`, `SND_bank.c`) | `SND_CommandProc`, the driver thread loop, the sequencer, the channel allocator |
| GBATEK, DS Sound Channels 0-15 | `https://problemkaputt.de/gbatek-ds-sound-channels-0-15.htm` | `SOUNDxCNT/SAD/TMR/PNT/LEN` bit fields |
| GBATEK, DS Sound Control Registers | `https://problemkaputt.de/gbatek-ds-sound-control-registers.htm` | `SOUNDCNT`, `SOUNDBIAS`, the 32.768 kHz output rate |
| GBATEK, DS Sound Notes | `https://problemkaputt.de/gbatek-ds-sound-notes.htm` | the IMA-ADPCM tables and DS deviations, the ten-step mixing pipeline, PSG duty, the noise LFSR |
| GBATEK, DS Sound Capture | `https://problemkaputt.de/gbatek-ds-sound-capture.htm` | `SNDCAPxCNT/DAD/LEN`, the two capture bugs |
| GBATEK, SDAT / SSEQ / SSAR / SBNK / SWAR / SWAV / STRM | `https://problemkaputt.de/gbatek-ds-files-sound-sdat-etc.htm` and its sub-pages | container and record layouts |
| kiwi.ds, Nitro Composer File Specification | `https://www.feshrine.net/hacking/doc/nds-sdat.html` (the `.php` form returns 406) | the original SDAT spec |
| ndspy | `https://ndspy.readthedocs.io/en/latest/appendices/sdat-structure.html`, `https://github.com/RoadrunnerWMC/ndspy` | field names, a reference SDAT/SSEQ implementation |

---

## 1. The command channel: what the ARM9 actually sends

### The transport

`SND_FlushCommand` moves the reserve list onto the pending list and sends **one word — the
address of the head node — on PXI tag 7**, retrying while the FIFO is full
[S: `src/matched/SND_FlushCommand.c`]. Commands never travel one at a time; they accumulate in
a 256-node pool and travel on a flush. A zero word is `RequestCommandProc`'s wake and carries no
list [H: host-source account from `port/shim/os/pxisend.c`, `snd_arm7`; verify with a retained scripted run and frame using this page's recipe].

The node is 24 bytes: `next` at `+0x00`, the id at `+0x04`, four argument words at `+0x08`,
`+0x0c`, `+0x10`, `+0x14`. `SND_FlushCommand`'s translation unit types the id as `u8` followed
by three pad bytes; `SND_AllocCommand`'s types it as a four-byte enum — the same 24 bytes either
way [S: `src/matched/SND_FlushCommand.c`, `src/matched/SND_AllocCommand.c`]
[P: `command.h`, `struct SNDCommand`]. **The layout is confirmed arithmetically by the port's own
addresses**: the 256-entry command array at `0x022048a0` plus `256 * 24 = 0x1800` lands exactly
on `0x022060a0`, the shared-block pointer [S: `systems/audio.md`'s address table, arithmetic].
The port reads a full word at `+0x04`, which is correct only because the pad bytes are zero on a
little-endian host; the id is a byte [E: `pxisend.c`].

The ARM7 copies each node to a local before dispatching, follows the copied `next`, and
increments `finishCommandTag` **once per flushed list, not per command**
[P: pokediamond `SND_command.c`, `SND_CommandProc`]. The host does the same [E: `pxisend.c`].

`SNDSharedWork` is: `finishCommandTag` u32 at `+0x00`, `playerStatus` u32 at `+0x04`,
`channelStatus` u16 and `captureStatus` u16 at `+0x08`/`+0x0a`, five padding words, then
`player[16]` of `{ s16 variable[16]; u32 tickCounter; }` from `+0x20`, then `s16
globalVariable[16]` — 640 bytes [S: `src/matched/SND_GetPlayerStatus.c`,
`src/matched/AllocFunc_SOCL.c`, the struct verbatim] [P: `work.h`, identical]. **The port's
"increment the first word" is therefore correct**, and the three status words beside it are the
only channel the ARM7 has for reporting state back — see the stall hypothesis in §4.

### The command set

Ids are enumerator positions, 0..33 [S: `src/matched/SND_AllocCommand.c`, the full
`SNDCommandID` enum] [P: `command.h`]. Argument columns are grade S where a matched ARM9 builder
packs them and grade P where only `SND_CommandProc` unpacks them.

| id | name | arguments (arg0..arg3) | what the ARM7 must do |
|---|---|---|---|
| 0 | `START_SEQ` | playerNo, seq base, seq offset, bank | prepare and start in one step [P] |
| 1 | `STOP_SEQ` | playerNo | free the player's tracks and channels [S: `SND_StopSeq.c`] |
| 2 | `PREPARE_SEQ` | playerNo, seq base, seq offset, bank | allocate player + tracks, do not run [S: `SND_PrepareSeq.c`] |
| 3 | `START_PREPARED_SEQ` | playerNo | clear the prepared flag, begin stepping [S: `SND_StartPreparedSeq.c`] |
| 4 | `PAUSE_SEQ` | playerNo, flag | [P] |
| 5 | `SKIP_SEQ` | playerNo, ticks | run the sequencer forward without output [P] |
| 6 | `PLAYER_PARAM` | playerNo, offset, data, size | a raw sized poke into `SNDPlayer` [S: `SNDi_SetPlayerParam.c`] |
| 7 | `TRACK_PARAM` | size<<24 \| playerNo, trackBitMask, offset, data | a raw sized poke into every selected `SNDTrack` [S: `SNDi_SetTrackParam.c`] |
| 8 | `MUTE_TRACK` | playerNo, trackBitMask, mute | [P] |
| 9 | `ALLOCATABLE_CHANNEL` | playerNo, trackBitMask, chBitMask | restrict which of the 16 channels those tracks may take [S: `SND_SetTrackAllocatableChannel.c`] |
| 10 | `PLAYER_LOCAL_VAR` | playerNo, varNo, s16 value | writes `sharedWork.player[n].variable[v]` [P] |
| 11 | `PLAYER_GLOBAL_VAR` | varNo, s16 value | writes `sharedWork.globalVariable[v]` [P] |
| 12 | `START_TIMER` | chBitMask, capBitMask, alarmBitMask, flags | set the start bits on channels, capture units and alarms [S: `SND_StartTimer.c`] |
| 13 | `STOP_TIMER` | chBitMask, capBitMask, alarmBitMask, flags | the inverse; the ARM9 bumps each alarm's id first [S: `SND_StopTimer.c`] |
| 14 | `SETUP_CHANNEL_PCM` | timer<<16\|chNo; dataAddr; volume<<24\|shift<<22\|loopLen; loop<<26\|format<<24\|pan<<16\|loopStart | program one channel from a `SNDWaveData` [S: `SND_SetupChannelPcm.c`] |
| 15 | `SETUP_CHANNEL_PSG` | chNo; volume\|shift<<8; pan\|timer<<8; duty | channels 8-13 only [P] |
| 16 | `SETUP_CHANNEL_NOISE` | chNo; volume\|shift<<8; pan\|timer<<8 | channels 14-15 only [P] |
| 17 | `SETUP_CAPTURE` | buffer; length; capture<<31\|format<<30\|loop<<29\|in<<28\|out<<27; 0 | program a capture unit [S: `SND_SetupCapture.c`] |
| 18 | `SETUP_ALARM` | alarmNo, tick, period, handler id | a periodic ARM7 alarm that raises the ARM9 handler [S: `SND_SetupAlarm.c`] |
| 19 | `CHANNEL_TIMER` | chBitMask, timer | retune running channels [P] |
| 20 | `CHANNEL_VOLUME` | chBitMask, volume, shift | [S: `SND_SetChannelVolume.c`] |
| 21 | `CHANNEL_PAN` | chBitMask, pan | [S: `SND_SetChannelPan.c`] |
| 22 | `SURROUND_DECAY` | decay | the capture-based pseudo-surround depth [S: `SNDi_SetSurroundDecay.c`] |
| 23 | `MASTER_VOLUME` | volume | `SOUNDCNT` bits 0-6 [S: `SND_SetMasterVolume.c`] |
| 24 | `MASTER_PAN` | pan | [P] |
| 25 | `OUTPUT_SELECTOR` | left, right, ch1, ch3 | `SOUNDCNT` bits 8-13 [S: `SND_SetOutputSelector.c`] [P: GBATEK control registers] |
| 26 | `LOCK_CHANNEL` | chBitMask, flags | remove channels from the allocator [S: `SND_LockChannel.c`] |
| 27 | `UNLOCK_CHANNEL` | chBitMask, flags | [S: `SND_UnlockChannel.c`] |
| 28 | `STOP_UNLOCKED_CHANNEL` | chBitMask, flags | [P] |
| 29 | `SHARED_WORK` | address of `SNDSharedWork` | store it; nothing else works until this arrives [S: `SND_CommandInit.c`] [E: `pxisend.c`] |
| 30 | `INVALIDATE_SEQ` | start, end | drop cached pointers into a range being freed [S: `SND_InvalidateSeqData.c`] |
| 31 | `INVALIDATE_BANK` | start, end | [S: `SND_InvalidateBankData.c`] |
| 32 | `INVALIDATE_WAVE` | start, end | [S: `SND_InvalidateWaveData.c`] |
| 33 | `READ_DRIVER_INFO` | address of a `SNDDriverInfo` | copy the whole driver state back to the ARM9 [S: `SND_ReadDriverInfo.c`] |

Two cross-checks are worth recording. The ARM9's packing for id 14 and id 7 matches the ARM7
decomposition field for field, so S and P corroborate [S: `SND_SetupChannelPcm.c`,
`SNDi_SetTrackParam.c`] [P: pokediamond `SND_command.c`]. For id 17 they do **not**: the
pokediamond decomp names bit 31 the capture *format*, where the ARM9 builder puts the capture
*unit number* there and the format at bit 30 [S: `src/matched/SND_SetupCapture.c`]. The ARM9
builder is this ROM's own code and wins; the decomp's argument names for that one command are
unreliable.

### What this ROM has been seen sending

Twelve commands, identical in two runs, all before the end of frame 3, in this order
[E: `scratchpad/cycle40/runs/tap-D59/tap-D59-run.log:161,194-204`;
`scratchpad/cycle40/runs/off-D45/off-D45-run.log:146,163-173`]:

`29 SHARED_WORK` · `22 SURROUND_DECAY` · `26 LOCK_CHANNEL` · `14 SETUP_CHANNEL_PCM` ·
`17 SETUP_CAPTURE` · `14 SETUP_CHANNEL_PCM` · `17 SETUP_CAPTURE` · `18 SETUP_ALARM` ·
`25 OUTPUT_SELECTOR` · `12 START_TIMER` · `23 MASTER_VOLUME` · `13 STOP_TIMER`.

**That list is the whole of the port's evidence, and it is an artefact of the instrument, not of
the game.** `snd_arm7` prints only while a static counter is below twelve, so the twelfth line is
the last one the port will ever emit no matter how long the run goes [E: `pxisend.c`, `said < 12`].
Everything the game sends after frame 3 — every `PREPARE_SEQ`, every `START_PREPARED_SEQ`, every
`PLAYER_PARAM` — is invisible. `systems/audio.md`'s planned `silent-audio-probe` experiment
cannot answer its own question until that cap is raised.

What the twelve *do* show is that the game brings up the **capture-based output effect** before
it plays anything: it locks a channel pair out of the allocator, programs two PCM channels and
two capture units against them, arms an alarm, and then repoints `SOUNDCNT`'s output selector
[H: the identification; settled by raising the cap and printing arg0..arg3 for each node].
`SND_CAPOUT_CHANNEL_MASK` is `0x000A` (channels 1 and 3) and `SND_CAPIN_CHANNEL_MASK` is
`0x0005` (channels 0 and 2) [P: `channel.h`]. `NNS_SndCaptureStartOutputEffect` passes a
32,000-word buffer and a callback into the capture-start path [S:
`src/matched/NNS_SndCaptureStartOutputEffect.c`].

**The design consequence is large.** With the output selector pointed at Ch1/Ch3, GBATEK's
`SOUNDCNT` bits 8-11 mean the speakers no longer hear the mixer at all — they hear those two
channels, which are being fed from the capture buffers
[P: `gbatek-ds-sound-control-registers.htm`]. A host driver that implements sixteen channels and
a mixer but ignores capture and the output selector will render a correct mix into a buffer
nobody listens to.

**SETTLED BY MEASUREMENT (2026-09-09, audio milestone 7).** Every prediction in the two
paragraphs above held, argument for argument, once the port printed all four words of each
node: `LOCK_CHANNEL` mask `0x000A`, `SETUP_CHANNEL_PCM` on channels 1 and 3 with pan 0 and pan
127 over two 512-word buffers at timer 512, `SETUP_CAPTURE` on the SAME two buffers with the
source bit clear (mixer) and the loop bit set, and `OUTPUT_SELECTOR 1 2 1 1`. The capture and
its replay channel share one buffer and one clock, so the speakers hear the mixer delayed by
one buffer -- 1,024 samples at 32,729.5 Hz = 31.3 ms -- re-panned hard left and hard right,
with `SNDi_SetSurroundDecay` pulling down everything except channels 1 and 3. `capture.c`
implements it and the port's own render is the capture-off render at lag 1,025 with
correlation 0.9962 [`docs/kb/hybrid/audio.md` §7].

---

## 2. The design: `port/shim/audio/`

### What the host must model

The ARM7 driver's entire state is one structure, and this repo already holds its declaration:
`SNDWork` is `SNDExChannel channel[16]`, `SNDPlayer player[16]`, `SNDTrack track[32]`,
`SNDAlarm alarm[8]` [S: `src/matched/SND_ReadPlayerInfo.c`, the structs verbatim]. That is not a
convenience — ids 6 and 7 are **raw offset/size writes into `SNDPlayer` and `SNDTrack`**, so a
host driver must reproduce those field offsets exactly or the ARM9's `SND_SetPlayerVolume` will
land on the wrong byte. `SND_SetPlayerVolume` writes offset 6, size 2 — `extFader`
[S: `src/matched/SND_SetPlayerVolume.c`].

- `SNDPlayer`: three flag bits, `myNo`, `prio`, `volume`, `s16 extFader`, `u8 tracks[16]`
  (0xFF = none), `tempo`, `tempo_ratio`, `tempo_counter`, `SNDBankData *bank`.
- `SNDTrack`: eight flag bits (active, note_wait, mute, tie, note_finish_wait, porta, cmp,
  channel_mask), `prgNo`, two volumes, pitch bend and range, pan and ext pan, `extFader`,
  `ext_pitch`, A/D/S/R, `prio`, `transpose`, portamento key and time, `sweep_pitch`, an
  `SNDLfoParam mod`, `channel_mask`, `s32 wait`, `base` and `cur` byte pointers,
  `call_stack[3]`, `loop_count[3]`, `call_stack_depth`, and a channel list head.
- `SNDExChannel`: `env_status`, key, velocity, pans, `env_decay`, sweep counters, A/D/S/R,
  `volume`, `timer`, an `SNDLfo`, `length`, an embedded `SNDWaveParam`, a data pointer or a
  duty value, and a drop/finish callback.

`SND_TRACK_CALL_STACK_DEPTH` is 3 and `SND_TRACK_NUM_PER_PLAYER` is 16 [P: `seq.h`]; the struct
above agrees [S].

### The frame

The real ARM7 driver is a thread woken by an `OS` periodic alarm with `SND_PROC_INTERVAL 0xAA8`
= 2728 OS ticks [P: `main.h`, pokediamond `SND_main.c`]. At `33513982/64 = 523,656` OS ticks per
second that is 191.96 Hz — **the 1/192 s driver frame** [P: arithmetic over those two constants].
Its loop is: update channels, drain the command queue, step sequences, run channel envelopes,
publish `SNDSharedWork`, advance the RNG. A command push wakes the thread with the periodic flag
*false*, so commands are serviced immediately while envelopes and sequences advance only on the
192 Hz frame [P: pokediamond `SND_main.c`]. Sequence timing sits on top: each frame adds
`(tempo * tempoRatio) >> 8` to an accumulator and emits one sequence tick per 240 subtracted
[P: pokediamond `SND_seq.c`; `SND_BASE_TEMPO 240`, `SND_DEFAULT_TEMPO 120` from `seq.h`].

### Data flow, in words

*Request.* Game glue calls `NNS_SndArcPlayerStartSeqArc(handle, seqArcNo, index)`. The NNS layer
reads the SSAR record for `index`, loads the bank and its wave archive through the sound heap,
allocates a player, and calls `SND_PrepareSeq` with the sequence's base pointer and byte offset
and the loaded bank pointer. Those become node id 2 in the pool. `NNS_SndMain`, once per game
frame, flushes the pool: one PXI word, one list.

*Dispatch.* The host receives the head address, walks the list, and for each node runs the driver
mutation the table above names. After the list, `finishCommandTag++`.

*Tick.* Independently of the game's frame, the host advances the driver 192 times a second. Each
driver frame: for each active player, accumulate tempo and, per emitted sequence tick, step every
track whose `wait` has reached zero; each executed note-on resolves the track's `prgNo` through
the bank to an `SNDInstParam`, allocates a channel, and programs it. Then every active channel
advances its envelope and LFO by one frame; a channel in release whose envelope falls below the
floor deactivates and fires its callback with FINISH [P: pokediamond `SND_exChannel.c`].

*Render.* The channel state is not sound; it is a description of sound. A separate mixer renders
N samples at 32.768 kHz from the sixteen channels' current parameters, applies the capture path,
and hands the block to the sink. The mixer must be driven by the sink's clock, not the game's:
this is the one place where the port's variable frame rate cannot be allowed to leak.

### Modules

| module | responsibility |
|---|---|
| `sdat.c` | open `sound_data.sdat` through the host FS; INFO/FAT/FILE accessors by index. Read-only, no allocation. |
| `sseq.c` | the SSEQ/SSAR event decoder: variable-length values, the opcode table, `RANDOM`/`VARIABLE`/`IF` prefixes, the three-deep call and loop stacks. |
| `sbnk.c` | instrument lookup: `instOffset[prgNo]` → type + 24-bit offset; drum-set and key-split descent; `SNDInstParam` out. |
| `swav.c` | PCM8 / PCM16 / IMA-ADPCM decode with the DS's rounding and clipping deviations; loop-point decoder-state snapshot. |
| `driver.c` | `SNDWork`: the 34-command dispatcher, the player/track/channel state machine, the 192 Hz frame, `SNDSharedWork` publication. |
| `chanalloc.c` | `SND_AllocExChannel`: mask, locks, lowest-priority-then-quietest victim, DROP callbacks. |
| `mixer.c` | 32.768 kHz mix: the ten-step volume/pan/master/bias/clip pipeline, PSG duty, the 15-bit noise LFSR. |
| `capture.c` | the two capture units, their loop buffers, the output selector, and the `SOUNDCNT` routing. |
| `sink_win32.c` | WASAPI shared-mode render client (waveOut as the fallback), a ring buffer, and the only thread boundary. |
| `snd_trace.c` | extend the existing `w3_sndtrace` with per-node argument logging and an uncapped id census. |

### Build order

The ordering rule is **silence-preserving**: nothing before step 6 can change what the game
does, so nothing before step 6 can regress the 90,000-frame frontier.

**STATUS (2026-09-09): ALL EIGHT STEPS ARE DONE.** Steps 7 and 8 landed as audio milestones
7 and 8; `docs/kb/hybrid/audio.md` §7-§9; `docs/kb/hybrid/audio-differential.md` §A10 is the page that says what they do today. Step 6 landed with
`port/shim/audio/driver.c` (the 34-command dispatcher), `port/shim/audio/sink_win32.c` (WASAPI
shared mode, waveOut fallback) and the wiring in `port/shim/os/pxisend.c` and
`port/platform/frame.c`. Everything below is kept as written because the ordering argument is
still the reason the work is safe; `docs/kb/hybrid/audio.md` is the page that says what the
port does TODAY, including which commands are dispatched, which are deliberate no-ops and
which are only logged, and it supersedes the per-step wording here.

1. **DONE. Raise the instrument.** Replace `snd_arm7`'s twelve-line cap with an uncapped id histogram
   plus a bounded argument log, both behind an `ACWW_SND_TRACE` variable. This is one edit to
   `pxisend.c` and it is the cheapest thing on this list. Deliverable: the real id census for a
   town run, which decides how much of §2 is actually needed.
2. **DONE. `sdat.c` + `sbnk.c` + `swav.c` offline.** A standalone host tool that walks the archive and
   dumps records. Verification is exact: it must reproduce the counts and the chain in §3 below.
3. **DONE. `sseq.c` offline.** Decode one sequence to an event list. Verify against ndspy's decoder on
   the same file — a disagreement is a bug in one of the two and both are readable.
4. **DONE. `chanalloc.c` + `mixer.c` offline, rendering to a WAV file.** *Milestone 1*:
   `SSAR 0`, entry 121 rendered to disk from `extract/adm-kr/files/sound_data.sdat`, byte-compared
   against a public SDAT player's render of the same entry. It is eight sequence bytes and one
   6,020-byte ADPCM payload (§3), which makes every disagreement diagnosable by hand.
5. **DONE (two sequences, not ten). A larger corpus offline.** Ten sequences chosen to cover PSG, noise, drum-set, key-split and
   a loop. Still no game.
6. **DONE. `sink_win32.c` and the wiring.** Replace `snd_arm7`'s silent walk with the driver's
   dispatcher, drive the 192 Hz frame from `acww_frame` (`port/platform/frame.c`), and open the
   sink. *Milestone 2*: the port makes its first sound. This is the first step that can regress
   the frontier, so it lands alone, with a `ACWW_SND=0` escape that restores the silent walk.
7. **DONE (2026-09-09). `capture.c`.** The two capture units, the output selector, the surround
   decay and the master pan are obeyed, and `SETUP_CHANNEL_PCM/PSG/NOISE` and
   `START_TIMER`/`STOP_TIMER` program and start the hardware channels the capture path replays
   on. The deliberate deviation is gone; `ACWW_SND_CAPTURE=0` restores it, which is what the
   before/after receipt is measured across. **The bring-up hypothesis in §1 and §4 is settled
   by measurement**: a per-id argument log printed all four words of every node, and they are
   exactly what §1 predicted -- `LOCK_CHANNEL` mask 0x000A, two `SETUP_CHANNEL_PCM` on channels
   1 and 3 panned hard left and hard right over two 512-word buffers at timer 512, two
   `SETUP_CAPTURE` on the SAME two buffers from the MIXER with the loop bit set, and
   `OUTPUT_SELECTOR 1 2 1 1` (left from Ch1, right from Ch3, both bypassing the mixer). The
   receipt that the selector is really obeyed is a cross-correlation: the capture-on render is
   the capture-off render delayed by **1,025 samples = 31.28 ms, coefficient 0.9962**, against
   0.2530 at lag zero -- one capture buffer, as the arithmetic predicts
   [`docs/kb/hybrid/audio.md` §7-8; `scratchpad/audio7/`].
8. **DONE, ONE-SIDED (2026-09-09). The differential check.** `READ_DRIVER_INFO` (id 33) is
   implemented -- the port fills the ARM9's `SNDDriverInfo` at this ROM's own struct offsets --
   and **this ROM never sends it**, which closes §4's fourth hypothesis for the OFF recipe: the
   uncapped census over 9,000 frames lists ids 0-32 and no 33. The port's half of the
   differential is `ACWW_SND_DUMP=<frames>:<path>`; the original's half is `--snd-dump` in
   `port/tools/oracle/oracle.py` and a sound block in `observer.lua`; `port/tools/oracle/
   snddiff.py` diffs them. **The emulator would not start in the session this was written in**
   (idle, 1.1 s of CPU in 675 s, no ledger, and the same hang with the pre-milestone-8
   observer), so no agreement table exists yet.

   **What the differential can compare is narrower than this page assumed, and that is
   measured rather than argued.** `SNDi_Work` is an ARM7 static in ARM7 WRAM at 0x037f8000 and
   the sixteen SOUNDxCNT registers are ARM7-only I/O; DeSmuME 0.9.13's Lua reaches neither, and
   nothing can inject an ARM9 `READ_DRIVER_INFO` into a running emulator. What IS comparable is
   `SNDSharedWork` -- in MAIN RAM, because the ARM9 owns it -- which is also the only part of
   the driver any game code can see. `observer.lua` probes the unreachable registers anyway and
   records the raw result rather than comparing zeroes.

   **Step 8 settled the tables without the emulator.** `extract/` holds them:
   `AttackCoeffTable` at `arm7/arm7.bin` +0xf2e0 and `SNDi_DecibelSquareTable` at +0xf1cc,
   `SNDi_DecibelTable` at `arm9/unk_autoload_2.bin` +0x54dcc. Two of the three grade-H
   reconstructions were byte-identical to the ROM; the third table was missing entirely, and it
   is the one the sequencer uses (`SND_CalcDecibelSquare`, not `SND_CalcDecibel`, for velocity,
   both track volumes, the player volume and the sustain level). Entry 0 is -723 in this ROM
   where the public NitroSDK has -32768: S beats P and the disagreement is content.

### Status: ALL EIGHT STEPS DONE, AND THE DIFFERENTIAL HAS NOW RUN (AUDIO8, 2026-09-10)

**AUDIO8 result, in one line: the driver is built and the differential works, and the music is
wrong.** The emulator half ran for the first time (five DeSmuME runs, 9,000 frames in 152 s,
with the DirectSound dialog dismisser beside the first). `SNDSharedWork` is located by
dereferencing the ARM9 global `SNDi_SharedWork` @0x022060a0 -- not by a hard-coded heap address,
which was wrong -- and both machines put the block at **0x02204620**. In the one window where
the two screens are byte-exact (frames 100..300), `captureStatus`, `channelStatus` at the
capture pair, `finishCommandTag` and the sequencer's TICK RATE all agree exactly, while the
first sequence sounds **three channels per track on the port against one on the original** and
ends at **tick 84 against tick 123**. Full table and receipts:
`docs/kb/hybrid/audio-differential.md` §A10, `scratchpad/audio8/`.

### Status: ALL EIGHT STEPS DONE (AUDIO6 `115984f9`, AUDIO7 `36ee5abe`, 2026-09-09)

**Milestone 6 = step 6, milestone 7 = step 7, milestone 8 = step 8, and all three landed the
same night.** `wiki/systems/audio.md` and `docs/kb/hybrid/audio.md` are the pages of record for
what the port does today; the account below is kept as the offline-only state milestone 1 left,
because it is what the fixtures were built against and it is still the argument for why nothing
before step 6 could regress the frontier. Two corrections to it: `port/tools/test_sndrender.py`
is **22 checks** now, not 19, three of them grade S against this ROM's own images; and
"milestone 2 -- the port making a sound -- has not started", below, is retracted -- it landed as
milestone 6.

### The offline state milestone 1 left (TOUCH41 relink, 2026-09-09)

Steps 2-4 above have landed and are **offline only**: `port/shim/audio/{sdat,sbnk,swav,sseq,
chanalloc,mixer}.c` exist, `port/tools/sndrender.py` compiles them unmodified from OUTSIDE the
port's link (its own no-CRT harness, `link.py`'s `GEN_FLAGS`) and renders a sequence out of
this ROM's `sound_data.sdat` to a WAV file. Nothing here is registered, nothing appears in
`link.py` or `overrides.txt`, and no invocation of the tool can change what the game does --
which is what makes the step silence-preserving and unable to regress the frontier
[S: `port/tools/sndrender.py` header; `docs/log/cycle40-keyboard-gate-probe.md` TOUCH41;
`docs/state/port-frontier.md`].

`port/tools/test_sndrender.py` is the fixture, **19 checks**, and every expectation in it comes
from somewhere other than the C under test [H: host/prose inference from `port/tools/test_sndrender.py` header;
`docs/log/cycle40-keyboard-gate-probe.md` TOUCH41, "audio milestone 1, 19 checks"; verify against the ROM function or symbol table and this page's recipe]:

- **the sequencer against ndspy** -- every event the C actually executes must land on an offset
  ndspy also parsed, with the same opcode, the same total length and the same operands. Length
  is the part that matters: the SSEQ opcode set has variable-length integers and three prefix
  opcodes, so a decoder that gets an operand width wrong reads the next event out of the middle
  of this one. If ndspy is not importable the fixture falls back to a local decoder and SAYS SO,
  which is weaker evidence because it shares an author with the C;
- **the waveform sample-exact** against a second IMA-ADPCM decoder written from GBATEK's
  pseudocode, including the DS's two deviations (truncated thirds, and a clamp at -0x7FFF).
  This settles the disagreement §3 records: two offline decoders differed on whether the
  predictor header is an emitted sample, 12,033 samples against 12,032. **12,032 is right**,
  and SWAV 42 -- the 6,020-byte ADPCM payload of the SSAR 0 / entry 121 chain -- is now asserted
  sample for sample;
- **the archive** against §3's claims table: the counts, and every field of the chain SSAR 0
  entry 121 -> bank 154 -> WAVEARC 4 -> SWAR file 1499 -> SWAV 42;
- **`mixer.c`'s `VolumeTable`** re-read out of `src/matched/SND_CalcChannelVolume.c` and
  compared byte for byte, so the one grade-S constant table in the directory cannot drift.

**The calibrations are part of the result (M1).** Two runs feed the driver deliberately wrong
input while asserting the correct answer, and the fixture is sound only if both are caught:
`CALIBRATION-adpcm-nibble` flips one bit of one ADPCM nibble (a differential format, so the
decoded digest must change -- a constant-returning "decoder" or a stale cached file would sail
through), and `CALIBRATION-tempo` renders at half tempo ratio and requires the SAME events in
the same order with the same operands on DIFFERENT driver frames, which is the only way to tell
a sequencer really running the 192 Hz frame and the `(tempo * tempoRatio) >> 8` accumulator from
one that walks the event list straight through [H: host/prose inference from `port/tools/test_sndrender.py` header; verify against the ROM function or symbol table and this page's recipe].

~~Milestone 2 -- the port making a sound -- has **not** started: step 6 is the first step that
can regress the frontier and it lands alone.~~ **Retracted (AUDIO6, `115984f9`): it landed, and
it landed alone as this sentence asked.** With `ACWW_SND=1` the port plays the game's own music
and effects; with the switch absent the frames are byte-identical to the untouched build over
both the 31-frame OFF recipe and the 48,000-frame town recipe
[E: `docs/kb/hybrid/audio.md` sections 8 and 8(b2); `../systems/audio.md`].

---

## 3. Claims table

New measurements below are grade **[S: image]**, read from
`extract/adm-kr/files/sound_data.sdat` in the main checkout (the file is not in a worktree).

| page and claim | public record (P) | verdict |
|---|---|---|
| `music.md`: "376 SEQ slots, 342 defined, 216 SEQARC, 943 BANK, 14 WAVEARC, 21 PLAYER, 30 GROUP, 2 STRM" | P: GBATEK/kiwi.ds INFO is eight count-plus-offset tables | **confirmed**; and the FAT magic histogram is exactly 336 `SSEQ`, 216 `SSAR`, 943 `SBNK`, 14 `SWAR`, 2 `STRM` = 1,511 [S: image] |
| `music.md` hypothesis: "the 3,233,800-byte file is one of the two streams" | — | **settled: yes.** STRM 0 is fileId 1509, volume 112, priority 64, player 0, and its FAT entry is offset 7,136,480 size 3,233,800. STRM 1 is fileId 1510, 334,436 bytes [S: image] |
| `music.md` hypothesis: "943 banks is a lot for 14 wave archives; are they per-song selections?" | P: BANK record names up to four archives, 0xFFFF unused | **settled: yes, and more strongly than asked.** All 943 banks name exactly **one** archive each; there are 14 distinct tuples, all singletons, one per wave archive. No bank in this ROM uses the multi-archive feature [S: image] |
| `music.md`: "SEQ record is 12 bytes: fileID u16, unknown u16, bankNo, volume, channelPriority, playerPriority, playerNo, reserved" | P: kiwi.ds/ndspy read `u16 fileID; u16 unknown; ...` | **the "unknown u16" is not unknown.** The SDK types it as `u32 fileId` followed by `NNSSndSeqParam { u16 bankNo; u8 volume; u8 channelPrio; u8 playerPrio; u8 playerNo; u16 reserved; }` [S: `src/matched/NNS_SndArcGetSeqInfo.c` and siblings]. Same bytes, correct names |
| `music.md`: "BANK record: fileID u16, unknown u16, 4x waveArcNo" | P: same | **same correction**: `u32 fileId; u16 waveArcNo[4]` [S: `src/matched/NNS_SndArcGetBankInfo.c`] |
| `data-formats.md` W6: "fill in the SDAT records and name their fields" | — | **available now, all grade S** from the ROM's own headers: WAVEARC is `u32 fileId:24, flags:8`; PLAYER is `u8 seqMax; u8 pad; u16 allocChBitFlag; u32 heapSize`; GROUP is `u32 count` + items of `u8 type; u8 loadFlag; u16 pad; u32 index`; STRM is `u32 fileId; u8 volume; u8 playerPrio; u8 playerNo; u8 flags`; STRMPLAYER is `u8 numChannels; u8 chNoList[2]`; the FAT entry is `u32 offset; u32 size; void *mem; u32 reserved` — the "8 reserved bytes" are two named runtime fields [S: `src/matched/NNS_SndArcGet*.c`] |
| `audio.md`: "the shared work's first word is `finishCommandTag`" | P: `work.h` | **confirmed exactly** [S: `src/matched/SND_GetPlayerStatus.c`]; the block is 640 bytes and the three status words next to it are the ARM7's only report channel |
| `audio.md`: "a restored request emits id 2 unconditionally; id 9 follows when the mask is non-zero; id 6 when volume differs; id 3 for a prepared player" | P: the ids are right | ~~**unverified in the port**, because the log stops at twelve lines in frame 3.~~ **MEASURED (AUDIO6): the uncapped census sees all four**, from frame 6. With the driver on: 371 each of ids 2 and 3, 741 of id 6, 2,270 of id 7. With it off: 967 each of ids 2 and 3 and 1,933 of id 6, because a silent ARM7 never sets `playerStatus` and the game restarts every sequence it starts [E: `docs/kb/hybrid/audio.md` section 8(c)] |
| `audio.md`: "archive 0 index 121 is eight sequence bytes (rest, program, one note, end), bank 154, wave archive 4, wave 42, one 6,020-byte ADPCM payload" | P: SSAR record layout | **confirmed in every field, and now fully resolved** [S: image]: SSAR 0 is fileId 336, 552 entries, data at +6,656; entry 121 is offset 2,334, bank 154, volume 127, chPrio 96, playerPrio 64, player 13. Its bytes are `80 5a` (rest 90), `81 00` (program 0), `3c 3c 00` (note 60, velocity 60, length 0), `ff` (end). Bank 154 is SBNK file 706, 76 bytes, one instrument of type 1 (PCM), wave archive index 0 → WAVEARC 4 → SWAR file 1499 (81 waves): SWAV 42, format 2 (ADPCM), no loop, 16,000 Hz, timer 1,047, loopstart 1 word, looplen 1,504 words → 6,020 payload bytes in a 6,032-byte block |
| `audio.md`: "216 sequence archives holding 5,550 entries" | — | **confirmed by summing every SSAR's own count field**: 5,550 [S: image] |
| `music.md`: "342 defined SEQ records but 336 distinct physical sequence files" | — | **confirmed and explained**: four fileIds are referenced by more than one SEQ record; the SEQ table aliases. It also references only 262 distinct banks, so 681 of the 943 banks belong to SSAR sequences alone [S: image] |
| `music.md`: "`SYMB` absent, so no name-based lookup can work" | P: GBATEK — absent SYMB is a supported configuration | **confirmed by the library too**: `NNSSndArc` keeps a `symbol` pointer but every accessor in `src/matched/` is index-based [S] |
| `audio.md`: "two offline decoders disagree on whether the ADPCM predictor header is an emitted sample, 12,033 against 12,032" | P: GBATEK — the 4-byte header is the initial predictor and index, and `SOUNDxLEN` counts `8*(N-1)` samples for ADPCM, i.e. the header word yields none | **the spec settles it: 12,032.** 1,505 words × 8 − 8 = 12,032. The decoder that emits 12,033 is emitting the header's initial PCM value as a sample [P: `gbatek-ds-sound-channels-0-15.htm`] |
| `audio.md`: "the port answers the protocol and plays nothing; that is not a step toward audio" | — | ~~**confirmed and worth keeping.**~~ **RETRACTED 2026-09-09**: with `ACWW_SND=1` the port plays. The half that held is the reading of the silent walk -- it provided the shared-work address and the finished tag, which was exactly the bootstrap the real driver started from [E: `docs/kb/hybrid/audio.md` section 1] |
| public: SBNK "single note definition is 16 bytes" (kiwi.ds) | P: kiwi.ds contradicts its own field list; GBATEK and ndspy say 10 | **10 is right** [S: `src/matched/SND_GetNextInstData.c`, `SNDInstParam` = `u16 wave[2]` + six `u8`]; the nested form in drum sets and key splits is 12 (`u8 type; u8 pad;` + those 10) |
| public: SBNK instrument record is "u8 type; u16 offset; u8 reserved" | P: ndspy reads `<BHx` | **the "reserved" byte is the offset's high byte.** The SDK reads the record as one u32 and shifts right by 8, giving a **24-bit** offset [S: `src/matched/SND_GetNextInstData.c`] |
| public: the SWAV field at `+0x08` is "non-loop length" (kiwi.ds) / "total length" (ndspy) / "loop end offset" (NitroStudio2) | three-way conflict | **the SDK calls it `looplen`** and pairs it with `loopstart`, which maps 1:1 onto GBATEK's `SOUNDxPNT`/`SOUNDxLEN` and its "one-shot length = PNT+LEN, looped = 1×PNT then ∞×LEN" rule [S: `src/matched/SND_GetWaveDataAddress.c`, `SNDWaveParam`] |
| public: SSEQ opcode `0xD5` is "expression" | P: `mml.h` names it `SND_MML_VOLUME2` | **use the SDK name.** `SNDTrack` has a `volume2` field beside `volume`, which is what it writes [S: `src/matched/SND_ReadPlayerInfo.c`] [P: `mml.h`]. `0xD7 MUTE` also exists and is missing from most community tables; `0xB7` and `0xE2` are gaps |
| public: "channels 0-7 are PCM-only" | P: `channel.h` — `SND_PCM_CHANNEL_MASK 0xFFFF` | **wrong, and this matters for the allocator.** All 16 channels do PCM; 8-13 *additionally* do PSG, 14-15 *additionally* do noise |
| public: `SNDDriverInfo` layout is undocumented | P: not found in any public header the search reached | **this repo has it**: `SNDWork work; u32 chCtrl[16]; SNDWork *workAddress; u32 lockedChannels; u32 padding[6]` [S: `src/matched/SND_ReadPlayerInfo.c`] |

---

## 4. Hypotheses, each with the experiment that settles it

- ~~**The game never sends a playback command on the measured path.**~~ **SETTLED, and it was a
  measurement artefact exactly as M1 predicted.** The experiment named here was run: the twelve-
  line cap was removed, and the census over the 9,000-frame OFF recipe sees `PREPARE_SEQ` and
  `START_PREPARED_SEQ` from **frame 6**, 371 of each with the driver on
  [E: `docs/kb/hybrid/audio.md` section 8(c)]. The instrument was the whole of the evidence for
  the hypothesis, and it was wrong.
- ~~**The silent ARM7 is adequate for the game's logic indefinitely.**~~ **SETTLED (AUDIO6):
  dead, and by exactly the experiment proposed here.** The port now sets `playerStatus` inside
  `PREPARE_SEQ` and clears it inside `STOP_SEQ`, as the SDK does, and the game's behaviour
  changed measurably: `NNSi_SndPlayerMain` had been tearing every started sequence down, so the
  OFF recipe went from 967 `PREPARE_SEQ` to 371 and from 590 bank invalidations to 6
  [S: `src/matched/NNSi_SndPlayerMain.c`; E: `docs/kb/hybrid/audio.md` section 8(c)]. **Nothing
  STALLED**, so the 90,000-frame evidence for "adequate" was true and the word was still wrong.
  `ACWW_SND_SHARED=0` keeps the old behaviour for a comparison.
- **The bring-up sequence in §1 is `NNS_SndCaptureStartOutputEffect`.** **SETTLED: yes, in
  every predicted field.** The experiment was run -- a per-id argument log in `driver.c` --
  and it produced `LOCK_CHANNEL` mask `0x000A`, the two `SETUP_CHANNEL_PCM` on channels 1 and
  3, `SETUP_CAPTURE` with bit 31 clear then set (unit 0 then unit 1, which is also the
  cross-check that this ROM's builder and not the pokediamond naming is right), and
  `OUTPUT_SELECTOR 1 2 1 1`. Also measured, and not predicted here: `SURROUND_DECAY 0x3000`
  arrives FIRST, and from frame 819 the game programs channels 6 and 7 as hardware PCM too
  (the locked mask grows to `0xCA`) -- NitroSDK's streamed-audio path
  [E: `scratchpad/audio7/args/run-tail.log`].
- **The ROM's `SNDDriverInfo` is never read at runtime.** **SETTLED for the OFF recipe: it is
  never read.** The uncapped census over 9,000 frames lists ids 0-32 and no 33, so no caller
  runs on this path. The command is implemented anyway (audio milestone 8) because it is the
  protocol's own state dump; if a caller ever does run, it now gets the driver's real state at
  this ROM's own struct offsets instead of an uninitialised buffer.
- **Music is selected by an hour-indexed table inside one of the four undecompiled callers of
  the start boundary** — carried over from `systems/audio.md`, unchanged, and now sharper: the
  archive contains 5,550 archived sequences against 342 standalone ones, so whatever selects
  music is choosing an `(archive, index)` pair, and `func_020f1fb4`'s `0x79` argument is an
  index into something. *Experiment:* disassemble `func_020f1fb4` and look for a table indexed by
  an RTC hour.
- **The 34 undefined SEQ slots are cut music.** *Experiment:* list their indices and check
  whether any GROUP item references them; a referenced hole is a packer bug, an unreferenced one
  is a deletion.
- **A host driver can be validated against DeSmuME per command rather than per waveform.**
  **PARTLY SETTLED, and the reach is narrower than this line assumed.** `SNDi_Work` is an ARM7
  static in ARM7 WRAM at 0x037f8000 and the sixteen SOUNDxCNT registers are ARM7-only I/O;
  DeSmuME 0.9.13's Lua reaches neither, and nothing can inject an ARM9 `READ_DRIVER_INFO` into
  a running emulator — so the 32 tracks' `cur` pointers and the 16 channels' `timer`/`volume`
  are not readable on the ORIGINAL's side at all. What IS comparable is `SNDSharedWork`, which
  lives in main RAM because the ARM9 owns it, and which is also the only part of the driver any
  game code can see: two drivers that agree there agree on everything the game can observe. The
  tooling on both sides exists (`ACWW_SND_DUMP`, `oracle.py --snd-dump`,
  `port/tools/oracle/snddiff.py`); the emulator would not start in the session they were
  written in, so no agreement table exists yet [`docs/kb/hybrid/audio-differential.md` §A10].

## Related

- `../audits/night-2026-09-09.md` — AUDIO6 and AUDIO7 in the night's index, with what each left
  open.
- `../systems/audio.md` — the page this design serves; its address table and its account of the
  transport are unchanged by this audit.
- `../data/music.md` — the archive's shape; four of its Hypotheses are settled in §3.
- `data-formats.md` — the **P** grade convention, and W6/W10, which §3 discharges.
- `docs/kb/hybrid/hardware-services.md` §1 tag 7 — the port-side account of the boundary.
