# Save and reload

**Status: RUN AND ANSWERED, 2026-09-10 (SAVE43, `2e579f09`). All three claims hold: the game
writes both banks itself, the bytes satisfy the ROM's own validity test, and a second launch
takes the existing-town branch.** Read the **SAVE43** section for the answer. The arms below it
are kept as they were measured and in the order they were measured, because the two intermediate
readings are the content: arm B (SAVEFLOW41) proved the store machinery while the game never
asked it to save, and arm D (SAVE42) reached the prompt and got a REFUSAL that located the rule.
Where an arm says the second launch is blocked, that sentence is superseded by SAVE43 and is
kept only as the record of what was known then.

## Purpose

`save-store-probe.md` asks whether anything reaches the file. This page asks the question after
it: **does a PLAYED game persist** -- does the game write its own record through the card
protocol, does that record satisfy the ROM's own validity test, and does a second launch with
the same `ACWW_SAVE` boot into the saved town instead of the taxi intro?

Three claims have to be separated, and the middle one is where every previous account stopped:

1. the game *issues* a backup write of a bank (request 7 over `0x00000..0x173fc`);
2. the bytes reach the FILE, not only the memory mapping;
3. a second launch reads them back and takes the existing-town branch.

## Recipe

**Arm A -- the control, first (M15).** The two-tap town recipe with no store, to 27,000 frames:

    python -B scratchpad/saveflow/run_sf.py town-nosave \
      ACWW_INTERP=1 \
      ACWW_TOUCH_AT=6900 ACWW_TOUCH_EVERY=60 ACWW_TOUCH_REPEAT=2 \
      ACWW_TOUCH2_X=221 ACWW_TOUCH2_Y=181 ACWW_TOUCH2_AT=24600 ACWW_TOUCH2_FOR=10 \
      ACWW_TOUCH2_EVERY=60 ACWW_TOUCH2_REPEAT=2 \
      ACWW_STOP_FRAME=27000 ACWW_SHOT_AFTER=6000 ACWW_SHOT_EVERY=1500 ACWW_PAD_SAMPLE=0

**Arm B -- a fresh erased store, the whole recipe.** `savetool.py make` an absolute path first,
then the same run to 48,000 with `"ACWW_SAVE=@SF@\town1.sav"` added. `@SF@` expands to
`scratchpad/saveflow` inside `run_sf.py`; do not build the path in the shell (see *What would
falsify it*).

**Arm C -- the second launch.** The same command as arm B, same `ACWW_SAVE`, nothing else
changed, with the file left exactly as arm B ended. The observation is the still at the frame
where arm B showed the taxi.

Read the census the run prints at its stop, and then read the FILE:

    python port/tools/savetool.py check <the same absolute path>

## Expected observations

| where | what says the claim is true |
|---|---|
| the run log | `acww card: req 7 WRITE flash 0x00000000..0x000173fc` -- a whole bank, not a byte |
| the census at the stop | `type 7` with `190456` bytes or more, `verify mismatches 0` |
| `savetool check` | both banks verify AND `the game would LOAD this bank` |
| arm C's stills | the town, not the taxi interior, at the frame arm B showed the taxi |

## What was observed

**Arm B, `scratchpad/saveflow/runs/town1`** (DIAGNOSTIC, B38; exit 100 at 48,000 frames,
1,636 s, 29 stills, no fault, no `unimplemented`), with a freshly `savetool.py make`-erased
256 KB store [E: `scratchpad/saveflow/runs/town1/receipt.json`]:

    acww card census: arm7 requests 748 (native CARDi_Request 0), store LIVE
      type 6: 746 requests, 190461 bytes, flash 0x00000000..0x0002e7f8
      type 7:   1 request,        1 byte,  flash 0x0003fffc..0x0003fffd
      type 9:   1 request,        1 byte,  flash 0x0003fffc..0x0003fffd
      persisted 1 bytes; verify mismatches 0
      FlushViewOfFile calls 2

- The boot reads **both banks back to back** -- 0x2e7f8 bytes from offset 0 at frame 10 --
  which is `func_020a1a40`'s slot 0 and slot 1 [S: `port/shim/game/savepoll.c`,
  `src/matched/func_020a1a40` tables `data_020d1c20` / `data_020d1bf0`].
- It writes **one byte, at `0x3fffc`**, at frame 757, and verifies it at 758. That is outside
  both banks and outside the letter store, at the last word of the chip
  [E: the census above].
- **Nothing else touches the store in 48,000 frames**, and `savetool.py check` afterwards
  reports both banks `ALL 0xFF -- erased flash, no save here` [E: same run].
- An honest 0xFF-erased read does **not** derail this path: no `unimplemented: func_02225a90`,
  no fault, 48,000 frames [E: same run]. That stop is a native-path observation
  [E: `port/shim/fs/cardreq.c`'s comment; `../systems/save-data.md`].

**The blocker.** Arm B's stills show the taxi interior and the town-name keyboard
(`마을 이름은?`) at frames 24,000, 37,500 **and** 48,000 alike -- the second scheduled contact
at 24,600 never confirms the name [E: `scratchpad/saveflow/runs/town1/shot_024000.bmp`,
`shot_037500.bmp`, `shot_048000.bmp`]. The receipted run `town-R1` at commit `6ca48706` had
the player in front of the town hall by 37,500 [E: `docs/state/port-frontier.md`, RECEIPT41].
So at commit `174ae9e3` the recipe does not reach gameplay, and everything downstream of
gameplay -- including the save trigger -- is unreachable by script.

**It is a convergence, not a regression, and the oracle settles it.** The measured divergence
between the port and the DeSmuME original at exactly this window was that the port's two taps
CONFIRM the town name and the original's identical taps do NOT, so the original sits on the
town-name keyboard through 48,000 -- which is where arm B now sits
[O: `docs/kb/hybrid/open-questions.md` question 1, measured at `eb24787a`;
`scratchpad/oracle/tap-fullpad/compare-vs-tap-D56.txt`]. Running the same oracle capture
against arm B:

    python port/tools/oracle/compare.py \
        scratchpad/saveflow/oracle-tap-fullpad scratchpad/saveflow/runs/town1

| frames | `tap-D56` at `6ca48706` | `town1` at `174ae9e3` |
|---|---|---|
| 25,500 .. 48,000, all 17 | ncc 0.70, ncc-top 0.0000 | ncc **0.993-0.999**, ncc-top **0.936-0.990** |

29 frames, mean ncc 0.9762 [O: `scratchpad/saveflow/compare-oracle-vs-town1.txt`]. This run
used `ACWW_TOUCH2_AT=24600`, the stale recipe line, and on a TOUCH42 build the port stays on the
town-name keyboard at 24,600 exactly as the original does [E: `tap-T42b`] [O:
`scratchpad/oracle/tap-window`]; the town frontier stands on the 24,700 recipe of record, where
both sides confirm [E: `tap-T42c`] [O: `scratchpad/oracle/tap-24700`] -- see `touch-latency.md`.
Two frames are the exception, 7,500 and 13,500, which score 0.70 with their mean
luminance swapped while every frame between them agrees: the dark taxi-ride phase begins and
ends about one shot interval early on the port, a phase offset against an uncalibrated oracle
frame counter rather than a different screen [O: same file] [H: settled by `--offset`, or by
stills every 150 across 7,000..14,000 on both sides].

**The OFF recipe moved the same way.** HEAD's own OFF run differs from the retained cycle39
native OFF stills on all 31 frames (277,667 differing bytes of 393,270 at frame 4,500), where
`docs/kb/hybrid/recipes.md` section 2 names 31/31 as the pass [H:
`scratchpad/saveflow/runs/off-control` vs `scratchpad/cycle39/execution39-touch39-005/off`; receipt lost with its worktree; repeat the named recipe and retain the stated frames].
Scored against the oracle's own OFF capture, HEAD gets mean ncc **0.9970** and that reference
gets **0.8401** [O: `scratchpad/saveflow/compare-oracle-vs-off-control.txt`,
`compare-oracle-vs-cycle39ref.txt`] -- so the tree moved towards the original here too, and the
retained reference should be re-taken at HEAD rather than treated as a correctness standard.

**Arm A settles it: the store is not what broke the recipe.** `scratchpad/saveflow/runs/town-nosave`
is the identical recipe with `ACWW_SAVE` unset, to 27,000 frames, and its stills are
**15/15 SHA256-identical** to arm B's over frames 6,000..27,000 -- the taxi, the player-name
keyboard, the ride, the conversation and the town-name keyboard alike
[E: `runs/town-nosave` vs `runs/town1`]. That is the prediction `save-store-probe.md` made for
arms A and B, confirmed.

**The instrument changes are inert when off.** The card census, the `FlushViewOfFile`
write-through and the new `ACWW_PADSCRIPT` timeline all leave the OFF recipe byte-identical:
`runs/off-census` and `runs/off-padscript` are each **31/31 SHA256-identical** to
`runs/off-control`, HEAD's own sources relinked without them [E: those three run directories].

**...and `ACWW_PADSCRIPT` is not inert when on** (B6). Three resumes from the frame-24,000
snapshot, each to 25,500 with stills every 150: `runs/r1` (no script) equals arm B on both
overlapping stills, so the snapshot resumes exactly; `runs/r2a` (`24100:0` -- ownership only)
differs from `r1` from 24,750, which is the script correctly displacing `ACWW_KEYS3`'s A
pulses; and `runs/r2b`, the same script plus two Up presses at 24,200 and 24,400, differs from
`r2a` from **24,300** -- one still after the first press. The two runs differ only in the
presses, and on the picture the difference is the town-name keyboard's tab strip moving its
selection [E: those three run directories; `scratchpad/saveflow/padscript-proof.png`].

**Arm C** had not been run when the above was written: there was nothing in the file for a
second launch to read. It has been now.

## SAVE43 -- all three claims, measured

The chain, all DIAGNOSTIC runs (B38) on a relink in the worktree
`.claude/worktrees/agent-a757560884bf9588e` at `fbfc987d` plus SAVE42's `frame.c` census call
[E: `../../docs/log/cycle42-save.md` SAVE43; `scratchpad/save43/RECEIPTS.md`]:

    town recipe (24,700) with a fresh erased ACWW_SAVE, snapshot at 48,000     522 s
      -> out of the town hall and past the tutorial hold, snapshot at 55,400
      -> the map: the player's own house is the GREEN icon; walk to it
      -> ENTER the house (the slide: push into the wall, pulse sideways, press A)
      -> step back out: Tom Nook is at the door; run his speech out with A
      -> 0x021f3c30 leaves 1 and becomes 0        <- the whole gate
      -> START: the real save menu, then A

**Claim 1, the game issues the write -- and it writes BOTH banks.** The census at the stop:

    type 7: 744 requests, 190456 bytes, flash 0x00000000..0x0002e7f8
    type 9: 744 requests, 190456 bytes, flash 0x00000000..0x0002e7f8
    persisted 190456 bytes; verify mismatches 0
    FlushViewOfFile calls 745

Consecutive 256-byte pages from `0x00000000`, each verified one frame later: `func_020a1d94`'s
512-byte step is two card pages [E: the run's own request spans]. On screen:
`오늘은 여기까지 하시겠습니까?` -> `저장하고 있습니다` -> **`저장했습니다！`** -- `sequence2_`
messages 0, 1 and 2, which is `func_0209f6e4`'s non-refusing branch [S: SAVE42's transcription
of that branch].

**Claim 2, the bytes satisfy the ROM's own test.** `savetool.py check` on the file afterwards:
bank 1 checksum stored `0xa6ad` computed `0xa6ad` residual `0x0000`, gamecode ok, flag
`+0x173fa` ok, word sum ok -> *the game would LOAD this bank*; bank 2 the same and a
byte-identical mirror. Three villagers occupied of eight, player 0 id `0xd185`, and the names
decode to `U+3143` (`ㅃ`) x4 for the player and x6 for the town -- what the scripted keyboard
typed [E: `scratchpad/save43/savecheck-S3.txt`].

**Claim 3, the second launch.** Fresh launch, no snapshot, the same `ACWW_SAVE`: at 3,000-4,000
the player is inside their own house with the bed and the phone under
`시작 준비 중입니다 / 전원을 끄지 말고 그대로 기다려 주십시오`, and from 5,000 outside their own
front door with the HUD -- no taxi, neither keyboard. The control is the identical launch on an
erased store, which is the taxi interior with the name keyboard [E: `boot-A`; SAVE42's
`boot9000.png`]. A second launch driven by a pad timeline walks in the reloaded town and meets
an NPC, so the town is playable and not merely drawable [E: `boot-B`].

**What this changes about the RULE.** The block is the move-in mode word and only that, and it
is cleared by the game's own code: `func_020a128c` is a tenth accessor, `mode := 0`, with
callers `func_0209ec74` and `func_ov068_0226e648`, caught by a store watchpoint
[E: `gp-W0`]. SAVE42's "there is no `mode := 0`" is retracted. Nook's attic bed is one save
point, not the gate.

## Arm D (SAVE42): play on until the game is ASKED to save, and read its answer

**Status: run, 2026-09-10, and it is the answer this page was missing.** Arm B stopped at
"no recipe reaches the save". Arm D reaches it, and the game refuses -- for a reason that is
now located in the ROM rather than guessed at.

The chain, all DIAGNOSTIC (B38) in the worktree `agent-aeac5138b67b1796a` at `61495f07`, run
directories under `scratchpad/save42/runs/`: `town-A` (the 24,700 recipe to 48,600 with a
freshly erased store, snapshot at 48,000) -> `gp-P1` (out of the town hall, through the
tutorial hold, snapshot at 55,400) -> `gp-M1` (the map) -> `gp-W1`..`gp-W7` (six legs steered
by the map marker) -> `gp-D1`..`gp-D9` (inside a house at 58,920) -> `gp-S2` (START).

| where | what was observed |
|---|---|
| `gp-S2` frame 59,700 | the game's own refusal, `어머？ 지금은 아직 / 저장하지 못하나 봐요` [E: `scratchpad/save42/s2_refuse.png`] |
| the message archive | that string is `script/KOR/message/sp/etc/sequence4_.bmg` index **4** [S: `scratchpad/save42/bmg.py find`] |
| the ROM | `func_0209f6e4` attaches `sp_etc_sequence4` and writes 4 into `self+0x72` iff `func_020a12d4() \|\| func_020a12c0()`, i.e. iff the word at `0x021f3c30` is 1 or 2 [S: `func_0209f6e4`, `func_020a12c0`, `func_020a12d4`, main] |
| the snapshot | `0x021f3c30 = 1` at frame 48,000 [E: `scratchpad/save42/stpeek.py st/town48000.st 0x021f3c30`] |
| the store, after ~60,000 frames of play | still one byte differing from erased, `+0x3fffc`; both banks `ALL 0xFF` [E: `savetool.py check`] |
| the census, now that it prints | `arm7 requests 748 ... NO WRITE_BACKUP REACHED THE STORE -- this run never saved` [E: `runs/off-fix`] |

**So the answer arm D gave was: not yet, and not for a port reason.** ~~The mode word's only
writers are `func_ov147_02299414` (`:= 1`) and `func_ov147_022997ec` (`:= 2`, `:= 3`) in the
move-in overlay, plus `func_020a4454` (`:= 3`, `:= 4`); no function in the ROM writes 0, so 0 is
the BSS default.~~ **Retracted by SAVE43 above**: `func_020a128c` is a tenth accessor, `mode :=
0`, and the game calls it when the arrival finishes. The three non-zero writers named here are
correct [S: their pool words]; the "nothing writes 0" half was a search that stopped one
function short.

**The clock is the wrong lever, and it was RUN rather than argued.** Two arms from the same
55,400-frame snapshot, identical except for `ACWW_RTC_DATE`, each pressing START and driving
the prompt with A:

| run | `ACWW_RTC_DATE` | the HUD | what the game said |
|---|---|---|---|
| `runs/gp-RTC0` | `20050615` (control) | `6/15 수` | the refusal |
| `runs/gp-RTC1` | `20050616` | `6/16 목` | **the same refusal, word for word** |

The clock really moved -- the date panel reads the next day and the weekday advanced -- and the
answer did not change [E: `scratchpad/save42/rtc0_a.png`, `rtc1_a.png`]. That is what the ROM
predicts: `ACWW_RTC_DATE` drives `func_0207b05c`'s missed-day catch-up
[S: `../systems/time-and-rtc.md`] and touches nothing the refusal branch reads. What lifts the
block is finishing the arrival, and the ROM says so in the same archive: `sequence4_[12]` is
Nook at the player's house -- lie on the bed in the attic (`옥탑방에 있는 침대`) and the day's
result can be saved.

**One instrument caveat found while doing it.** A resumed run issues no card request at all,
so `flash_store()` -- which is lazy -- never opens the file, and the census reports
`store absent` even with `ACWW_SAVE` set [E: `runs/gp-RTC0`, `gp-RTC1`, `arm7 requests 0`].
That is not a dropped write; it is "nothing asked". Read the line as the census means it.

**One port defect was found on this path and fixed.** `acww_card_report()` -- the census this
page quotes -- had no caller anywhere in the tree, while `docs/kb/hybrid/save-flow.md` said it
printed at the stop frame; the census had been silent since SAVEFLOW41 (B6). It is now called
on both exit paths, and the OFF control says the change is invisible: frames 4,500..9,000
every 150, `runs/off-fix` against `runs/off-control` (the same tree relinked with `frame.c`
reverted), **31/31 exact (RGB), mean ncc 1.0000** [E: those two run directories].

**The second launch's own machinery is proven, which is worth separating from the blocked
claim.** `runs/boot-store` is a fresh launch with the same `ACWW_SAVE` and no snapshot, on the
build with the census wired up: `req 6 READ flash 0x00000000..0x0002e7f8 (190456 bytes) from
frame 10` -- both banks back to back, `func_020a1a40`'s slot 0 and slot 1 -- and a census of
748 requests, 1 byte persisted, 0 verify mismatches [E: `runs/boot-store`]. With the banks
erased the boot takes `func_020b5724`'s new-game branch and the still at 9,000 is the taxi
with the player-name keyboard [E: `scratchpad/save42/boot9000.png`]. **That still is the
control arm C has to differ from**, and the read path it would differ through works today.

**Two navigation facts, so nobody repeats the ten runs.** Steer by the MAP marker, not by the
world: open the map with X, read the pink marker and the target icon in map pixels, and
convert at **0.184 map px per frame east, 0.23 per frame north**. And **walking into a door
does not open it** -- `gp-D8` centred the player in the doorway (Up held 700 frames, Left
pulsed 20 in 100, because pad rows OR together) and nothing happened; `gp-D9` added A pulses
and went inside [E: those two run directories]. Whether the ORIGINAL also needs the A press is
unverified [H: one oracle arm over `st/door57700.st`'s approach settles it].

## What would falsify it

- Reading "persisted 1 bytes" as "the port can save". It says this recipe wrote one byte at
  one address; the write, verify and flush machinery is proven, the game's save is not.
- Concluding from arm B that `ACWW_SAVE` broke the town recipe. The store is touched at frames
  3, 10, 757 and 823 only, all long before the keyboard. Arm A is the control that settles it.
- Building the store path in an MSYS shell. `ACWW_STATE_SAVE=<frame>:<path>`'s colon makes bash
  rewrite the value as a path list, and `24000:C:/...` goes in as `24000:/c/...`; the snapshot
  is then never written and the run says nothing about it until it ends.
- Trusting a run that ended with exit 1. Nothing in the image exits 1
  [S: `port/tools/measure.py`'s `acww_exit` table]; it means another session ran
  `taskkill /F /IM acww.exe`. `run_sf.py` launches a uniquely named copy for that reason.

## Related

- `save-store-probe.md` -- the narrower probe this run also answers (arm B).
- `../systems/save-data.md` -- the ROM-side account.
- `two-tap-town-recipe.md` -- the recipe arms A and B run.
- `savestate-resume.md` -- `scratchpad/saveflow/town24000.st` was taken by arm B.
- `gameplay-walkthrough.md` -- the SAVE43 chain frame by frame, and the three navigation rules
  (the door slide, the blinking map marker, the paving rate) that cost the runs.
- `../audits/night-2026-09-09.md` -- where SAVEFLOW41, SAVE42 and SAVE43 sit in the night.
