# Silent audio probe: which sound commands does the game emit?

**Status: designed, not yet run.**

## Purpose

The port's whole ARM7 sound processor is one function that walks the ARM9's command list,
completes every command silently and bumps the finished tag
[E: `port/shim/os/pxisend.c`]. It prints the id of each command it sees -- but only the first
twelve, because the print is capped at `said < 12` [E: `port/shim/os/pxisend.c`].

That cap makes the most useful question unanswerable as things stand. A first audible slice
would have to support ids 2 (`PREPARE_SEQ`), 9 (`ALLOCATABLE_CHANNEL`), 6 (`PLAYER_PARAM`) and 3
(`START_PREPARED_SEQ`) [S: `docs/kb/port/input-save-audio.md`], and nobody knows which of them
the game actually emits on the way to the town hall. Twelve lines from frame 0 will all be boot
traffic.

This experiment is therefore two parts: raise the cap, then count.

## Recipe

**Step 1, a one-line instrument change.** In `port/shim/os/pxisend.c`'s `snd_arm7`, the print is
gated by a static counter capped at 12. Replace it with a per-id "seen" table, exactly the shape
`acww_card_arm7` already uses for request types -- one line per distinct command id, ungated
[E: `port/shim/fs/cardreq.c`, `static unsigned char seen[16]`]. That answers "which ids occur"
without a print flood; a second counter per id answers "how many", printed once at the dump.

Rationale, and it is this repo's standing warning arriving in a constant: an instrument that
cannot fire is indistinguishable from one that fires and changes nothing. The card shim shipped
two wrong constants for exactly this reason [E: `port/shim/fs/cardreq.c`].

**Step 2, the control.** Run `off-recipe.md` and confirm 31 of 31 equal. A print-only change
must not move a pixel; if it does, the change is not print-only (M15).

**Step 3, the measurement.** The town recipe from `two-tap-town-recipe.md`, unchanged, to
48,000 frames. Then pull the counts out of the log in Python -- **not with a shell `grep`
alternation**: the shell here is ripgrep, whose alternation is `|` and not `\|`, and the old
pattern silently matched nothing twice in one cycle
[E: `docs/kb/hybrid/recipes.md` section 8; `docs/log/cycle40-keyboard-gate-probe.md` ENTRY40].

## Expected observations

| line | meaning |
|---|---|
| `acww snd7: command id 1d completed silently` | id 29, `SHARED_WORK`: the ARM7 learning the block's address. Expected early and at least once |
| `acww snd7: command id 2` | `PREPARE_SEQ` -- a sequence was actually requested |
| `acww snd7: command id 9` | `ALLOCATABLE_CHANNEL`, which follows a prepare only when the player's allocation mask is non-zero |
| `acww snd7: command id 6` | `PLAYER_PARAM`, emitted on the player-main step only when the computed fader or volume differs |
| `acww snd7: command id 3` | `START_PREPARED_SEQ` |

Predictions:

- Id 29 occurs. It is how the protocol starts and the port depends on it to find
  `finishCommandTag`.
- Ids 2 and 3 occur before frame 6,000, because the title and the taxi have music in the
  original.
- Id 6 occurs in bulk, because a fader ramp emits one per differing step.

If ids 2, 3, 6 and 9 are all absent across 48,000 frames, then either the game's own sound path
is not reaching the driver on this build, or the archive load failed silently -- and the second
has a known failure signature: the host sound facade once answered "no archive",
`NNS_SndArcGetSeqArcParam` returned NULL to `func_020f4b1c`, which called the ROM's fatal path
`func_0206e3ec`, and the ROM's crash screen looped from frame ~830 with both screens black
[E: `docs/log/cycle40-keyboard-gate-probe.md` CARD40..SND40]. That run reaches the town, so that
particular failure is excluded -- which makes an all-absent result genuinely surprising and
worth chasing.

A second, free observation from the same log: whether the ARM9 ever *waits*. `SND_WaitForCommandProc`
spins until a tag is finished [S: `src/matched/SND_WaitForCommandProc.c`]. A run that finishes
proves no such wait deadlocked, which is the standing evidence that the silent ARM7 is adequate
-- 90,000 frames without re-entering the ROM's fatal path
[E: `scratchpad/cycle40/runs/tap-D59`, LONG41].

## What would falsify the hypothesis it tests

The hypothesis is that the silent ARM7 is adequate for the game's logic indefinitely
[S: `docs/kb/hybrid/hardware-services.md` section 7]. It is falsified by a stall whose waiting
function is a `SND_*` or `NNS_Snd*` symbol -- the ROM's sound stack runs against a consumer that
never reports a real player state, so a sequence whose progression the game waits on would hang.
This probe cannot produce that; it can only tell you which commands are in play, which is what
an oracle comparison over a scene with music-driven timing would need to be designed against.

**This experiment does not make sound and is not a step toward it.** Transport alone cannot
interpret a sequence, resolve a bank or wave archive, allocate channels, advance envelopes and
timers, or produce PCM [S: `docs/kb/port/input-save-audio.md`].

## Related

- `../systems/audio.md`
- `two-tap-town-recipe.md`, `off-recipe.md`
