# Consistency audit

**Summary.** The 36 content pages under `wiki/` were written by four independent passes plus the
runtime kb pass, and this is the first read of all of them against each other and against the
repo. Path citations are in excellent shape: exactly two of 384 backticked repo paths do not
resolve, and both are placeholders. Symbol citations are worse in one specific way -- the
*module* column of the "Where it lives" tables was wrong on 27 rows across five pages, almost
always `main` where the symbol table says `autoload_2`. Fourteen pages carried a stray
`</content>` tag from the writing harness. Ten genuine cross-page contradictions were found; nine
are fixed here from the repo, one needs a run. Everything applied is recorded below with the
deciding file and line.

Method: scripted checks over every `wiki/**/*.md` for repo-path existence, wiki-link existence,
symbol-table membership, page length, host addresses, fenced blocks, Korean runs and grade tags,
plus a full read of all 42 files. Counts as of this pass; re-run the scripts after any edit.

## 1. Contradictions between pages

### 1.1 FIXED -- ITCM holds 158 functions, not four

`engine/graphics-pipeline.md` said "Putting those four in ITCM is the ROM's only use of
instruction TCM [S: `config/adm-kr/arm9/itcm/symbols.txt`, 16 named functions ...]".
`engine/memory-map.md` and `engine/display-objects.md` both say otherwise, and the table decides
it: `config/adm-kr/arm9/itcm/symbols.txt` has 158 `kind:function` lines, 114 of them real names
-- the four `NNS_G3dGe*` submission routines, thirteen `NNSi_G3dFuncSbc_*` scene-graph opcodes,
the whole `MTX_*`/`VEC_*`/`FX_*` fixed-point library, `OS_IrqHandler`, `OS_Halt`,
`OS_SaveContext`/`OS_LoadContext`, `OS_GetTick` and the display-object steppers.
**Fixed** in `graphics-pipeline.md` ("Geometry out") and in `data/rom-layout.md`, which carried
the same claim as "the exception" and as an ITCM table row reading "hot 3D buffer helpers".

### 1.2 FIXED -- channel 189 is the snowman, not the field renderer

`systems/town.md` and `systems/weather-and-seasons.md` both say channel 189 is the SNOWMAN and
name the retraction. `engine/scenes-and-channels.md` ("channel 189 is the field render object")
and `engine/display-objects.md` ("The FIELD renderer's vtable is `0x022382ac`") carried the
retracted reading, which they had taken from the port's own shim headers
(`port/shim/game/chanlist.c:6-8`, `port/shim/gfx/pmflist.c:53`) -- those headers are stale.
`port/BOOT-STATE.md:1159-1171` is the retraction: channel 189's bind log names
`/snowman/snowball1.nsbmd` (`SNW0`, id `0x022383ac`) and `/snowman/snow_face.nsbmd` (`SNW1`, id
`0x022383c8`), and ov003 has no acre ground texture at all. **Fixed** on both engine pages, with
a new "Where it lives" row on `display-objects.md`.

### 1.3 FIXED -- the display node's back-pointer: `+0x08` versus `node+0x10`

`engine/display-objects.md` carried this as an open Hypothesis ("the two readings contradict").
It is two different node kinds, and the repo says so directly. `func_020ee834`'s four lists use
a three-word node `{prev, next, obj}`, object at `+0x08` [`port/shim/gfx/pmflist.c:106-119`].
The FIFTH list, at `0x021fcff8` -- nodes are the `sub` block at `+0x14` of each display object,
walked by `func_020ee9a0` -- has `head` at `+0`, the member pointer at `+4`/`+8` and the object
at `node+0x10`, and takes `next` by CALLING `func_01ffcffc(node)`; the comment records that this
was read off the ROM's instructions, not assumed [`port/shim/gfx/pmflist.c:961-981`].
**Fixed**: the Hypothesis is rewritten as settled and the fifth list is now named in "The walk
itself".

### 1.4 FIXED -- `ov004` has 121 symbols or 3,075 targets

`engine/overlays.md` had a whole section headed "Contradiction: how many functions `ov004` has".
Not a contradiction: two tables. `config/adm-kr/arm9/overlays/ov004/symbols.txt` has 121
`kind:function` entries of which 90 are sized and 31 are zero-sized `_unk`; beside it
`config/adm-kr/arm9/overlays/ov004/recovered.txt` holds 3,060 boundary-recovered targets, all
sized. `tools/agent/target.py:183-215` explains the sidecar (dsd owns `symbols.txt` and rewrites
it) and independently records the same "90 sized function symbols covering 3.8%";
`target.py:50-65, 224` shows `T.load_all()` loading both. **Fixed**: the section is now headed
"Settled", and the matching Hypothesis bullet is removed. Consequence worth stating: a
`func_ovNNN_*` name that appears only in `recovered.txt` IS a symbol-table name under STYLE
rule 2, which is why `func_ov004_0224522c`, `func_ov092_02299324`, `func_ov065_0227ef00` and
`func_ov003_0222f458` are legitimate citations.

### 1.5 FIXED -- the tap-frame disagreement, settled as ORACLE42

Five pages still called this open after `docs/log/cycle40-keyboard-gate-probe.md:610-624` settled
it: the tap at 24,600 lands on a KEYS3 A-press frame (2400 + 37 x 600), the original's stylus
sample reaches the game one to two frames after the port's, and with `ACWW_TOUCH2_AT=24700` both
sides confirm and agree (11 frames 24,000..27,000, mean ncc 0.9955, top screen 1.0000).
Three pages already had it (`systems/dialogue.md`, `systems/input-and-touch.md`,
`experiments/touch-calibration.md` -- the last two as appended "Result (ORACLE42)" sections).
**Fixed** in all five:

| page | sentence | fix |
|---|---|---|
| `engine/boot-and-entry.md` | "They diverge at 25,500, where the port's two scheduled taps confirm the town name and the original's identical taps do not" | ORACLE42 settlement appended with its citations |
| `experiments/two-tap-town-recipe.md` | "Which side is right is open -- see `touch-calibration.md`" | rewritten as settled; recipe, expected-observations table and the tap-count check moved to 24,700 |
| `experiments/rtc-hour-sweep.md` | "Caveat that will bite this run: the original does not reach the town under this recipe" | rewritten as a caveat ORACLE42 removed, with an instruction to use 24,700 in both arms |
| `systems/input-and-touch.md` | "Which side is right is open." and two Hypotheses still asking for the comparison | pointed at the page's own Result section; the two Hypotheses marked settled negative / settled positive |
| `systems/dialogue.md` | Hypothesis "the port confirms the town name one tap too eagerly ... the ADC round trip" | rewritten as settled-for-the-record; the round trip was NOT the cause |

### 1.6 FIXED -- `POWCNT1` bit 15 is a sound flag

`data/music.md` said "`POWCNT1` bit 15 is written as a sound flag by `func_0205401c`".
`engine/graphics-pipeline.md` says bit 15 at `0x04000304` selects which 2D engine drives the top
screen, and `src/matched/func_020540e4.c` writes it for exactly that. The "sound flag" reading
comes from a variable named `gSoundFlag` in `src/matched/func_0205401c.cpp`, whose own header
says "names are inferred, not original". **Fixed**: `music.md` now states that both functions
write the same bit, that the name is inferred, that the bit is the screen swap, and files what
the global actually holds as a Hypothesis.

### 1.7 FIXED -- the sound library lives in `main`

`systems/audio.md`'s "Where it lives" table put fourteen rows in `main (NNS)` / `main (SND)`;
`data/music.md` said `autoload_2`. The tables settle it: every `NNS_Snd*`, `NNSi_Snd*`, `SND_*`
and `SNDi_*` symbol is in `config/adm-kr/arm9/autoload_2/symbols.txt` (105 and 65 respectively),
none in `config/adm-kr/arm9/symbols.txt`. **Fixed** in `audio.md`; `music.md` gained the two
counts and a cross-reference.

### 1.8 FIXED -- how many sound files are denied

`systems/audio.md` said "Twelve sound files are denied", having separately named the three
command-layer files. `port/tools/interp_registry.py`'s `DENY_FILES` has eleven archive/player/
heap files plus `sndcmd.c`, `sndflush.c` and `sndtag.c` -- fourteen. **Fixed**, with the eleven
enumerated.

### 1.9 FIXED -- the deny list's size

`docs/kb/hybrid/runtime.md:158-160` says "93 host services ... 40 shim files and
`func_020b1b84` denied". `port/tools/interp_registry.py`'s `DENY_FILES` set has **49** basenames
(plus `DENY_FUNCS = {func_020b1b84}` and one `EXTRA_ENTRIES` addition). `engine/memory-map.md`
was the only wiki page citing the deny list; **fixed** there to name the measured 49 and to flag
runtime.md as stale by nine. `engine/threads-and-interrupts.md` does not state a size, so the
"40 files / 93 services vs 49 basenames" contradiction is between two kb documents, not between
two wiki pages -- see section 6.

### 1.10 FIXED -- the season day-boundary count

`systems/weather-and-seasons.md`'s "How to check it" said "Two arms compare against `0x18` and
three against `0x1a`". `port/shim/game/season.c`'s reassembled switch has ONE arm comparing
against `0x18` (case 2, February) and three against `0x1a` (cases 5, 8, 11). The Summary's
boundaries -- 25 February, 27 May, 27 August, 27 November -- are right and unchanged.
**Fixed** to "One arm ... and three".

### 1.11 CHECKED, NOT A CONTRADICTION

Recorded so a later reader does not re-open them:

- **Run durations.** `engine/graphics-pipeline.md` "48,000 frames in 811 s" (`tap-D56`) and
  `engine/boot-and-entry.md` "48,000 frames in 801 s" (`town-R1`) are two different runs and
  both match `docs/log/cycle40-keyboard-gate-probe.md:546` and `:577`. Shot counts 31 and 29
  likewise.
- **ncc figures.** `boot-and-entry.md` cites bottom-screen ncc 0.9997-1.0000 for 6,000..24,000;
  `input-and-touch.md`, `rng.md` and `two-tap-town-recipe.md` cite whole-frame 0.9920-0.9959 for
  the same window. Two metrics, each labelled, both in ORACLE41.
- **Overlay geometry.** 148 slots, 138 with code, 10 empty (`ov000`, `ov057`-`ov064`, `ov089`),
  11,236 overlay functions, 25,516 functions in total, and 35/19/14/12 overlays sharing
  `0x02260020`/`0x02278a00`/`0x0229c180`/`0x02260420` all reproduce exactly from
  `config/adm-kr/arm9/**/symbols.txt`. `engine/overlays.md`, `engine/memory-map.md` and
  `data/rom-layout.md` agree.
- **The bmg endianness note.** `engine/text-and-messages.md` states the string walk reads
  `(p[1] << 8) | p[0]` while `test_.bmg`'s `DAT1` is UTF-16LE, and files the disagreement as a
  Hypothesis with the dump that would settle it. `data/archives.md` states only the container
  fact. That is STYLE rule 7 working as intended -- left alone.
- **`0xf7` compression on `.bmg`.** `text-and-messages.md` and `data/archives.md` give the same
  1,790/6,330 split and the same open question.
- **DTCM.** `data/rom-layout.md`'s "0x460 bytes" is the module image; `engine/memory-map.md`'s
  16 KB is the hardware window. Not a contradiction, but it read as one, so `rom-layout.md` now
  says which is which and cross-references `memory-map.md`.

## 2. Citation validity

### 2.1 Repo paths -- 2 misses of 384

Scripted over every backticked `src/matched/`, `port/`, `config/`, `docs/`, `tools/` and `wiki/`
path. Both misses are deliberate placeholders and are left as they are:

| path | page | reading |
|---|---|---|
| `config/adm-kr/arm9/overlays/ovNNN/symbols.txt` | `engine/overlays.md:175` | `ovNNN` is a metavariable |
| `port/build/acww.map` | `STYLE.md:54` | a build artefact, not committed |

### 2.2 Cross-page links -- 3 broken, all FIXED

Markdown links between pages: none broken. Backticked relative page refs: three resolved
nowhere.

| bad ref | page | fix |
|---|---|---|
| `systems/save.md` | `data/items.md:167` | `../systems/save-data.md` |
| `systems/save.md` | `engine/file-system.md:209` | `../systems/save-data.md`, and the sentence rewritten from "belongs on a page" to "is written up on" |
| `systems/villagers.md` | `data/villagers.md:180` | `../systems/villagers.md` |
| `wiki/data/` (twice) | `systems/economy.md:122, 159` | `../data/items.md` |

### 2.3 Symbols -- 8 concrete misses, all FIXED or explained

Of 568 backticked `func_*`/`data_*`/SDK names, 49 are not in
`config/adm-kr/arm9/**/symbols.txt`. Most are SDK API names, struct fields or enum constants
(`CARD_STAT_*`, `PXI_FIFO_TAG_*`, `TP_POINT`, `OS_IRQTable`, `DWC_*`, `FS_RESULT_UNSUPPORTED`),
which STYLE rule 2 permits, plus the metavariables in `README.md`/`STYLE.md`. The concrete ones:

| symbol | page | finding | fix |
|---|---|---|---|
| `func_02051c8c`, `func_020b4950` | `engine/text-and-messages.md:89` | the tables DO name them, as `func_02051c8c_unk` / `func_020b4950_unk`, `kind:function(thumb,size=0x0,unknown)` | names corrected; the page's "not in the symbol table at all" replaced with "carry no real name" |
| `func_02225a90` | `systems/save-data.md:103`, `experiments/save-store-probe.md:19` | no such symbol; the address is `func_ov003_02225a90` in `config/adm-kr/arm9/overlays/ov003/symbols.txt`. The port's stop line does quote the bare form | both pages now quote the stop line verbatim and give the symbol-table resolution beside it |
| `func_0209ded0` | `systems/events-and-calendar.md:22` | no such symbol; `config/adm-kr/arm9/symbols.txt` names `0x0209ded0` `MB_GetBeaconRecvStatus`, a multiboot name that cannot be a day-change callee. `port/tools/known_callees.txt:253` does list `0x0209ded0` as `f2` of `func_02040c90` | the address is kept (the callee list is the evidence) and the naming hazard is now stated as a D12 case, citing both files |
| `MATH_Rand16/32`, `MATH_InitRand16/32`, `OS_IsTickAvailable` | `systems/rng.md` | SDK names with no symbol in this ROM; every one is reached under a `func_*` name in `src/matched/` | a naming note added at the top of "What happens" |
| `func_ov003_0222f458`, `func_ov004_0224522c`, `func_ov065_0227ef00`, `func_ov092_02299324` | four pages | present in the module's `recovered.txt`, which `tools/agent/target.py` loads | valid as written; see 1.4 |
| `0x02239bf8ff` | `systems/villagers.md:108` | a nine-hex-digit address -- a typo for the four addresses `systems/town.md:97` cites | corrected to `0x02239bf8`, `0x02239c1c`, `0x02239c40`, `0x02239c58` |
| overlay band top `0x022a3240` | `engine/overlays.md`, `engine/memory-map.md` | the cited maximum function address over the overlay symbol tables is `0x022a31d8` | both corrected to `0x022a31d8`; the citation wording tightened to "`addr:` over `kind:function` lines" |
| "27 overlays" | `data/villagers.md:122` | the page's own table lists 32 special-character overlays (`ov004`, `ov045`-`ov055`, `ov068`, `ov070`-`ov088`) | corrected to 32 |

### 2.4 Module labels -- 27 rows wrong, all FIXED

The largest single defect class. Resolved every cited symbol against
`config/adm-kr/arm9/**/symbols.txt` and rewrote the module column:

| page | rows | wrong -> right |
|---|---|---|
| `systems/time-and-rtc.md` | 11 | `RTC_Init`, `RtcCommonCallback`, `RtcBCD2HEX`, `RtcWaitBusy`, `RtcSendPxiCommand`, `RTC_GetTime`, `RTC_GetDateTimeAsync`, `RTC_GetDateAsync`/`GetTimeAsync`, `RTC_SetDateTime`, the three `Convert*`: `main` -> `autoload_2`. `OS_GetTick`/`OS_GetTickLo`: `main` -> `itcm`; `OS_InitTick`/`OSi_CountUpTick`: `main` -> `autoload_2`. Prose citations corrected to match |
| `engine/threads-and-interrupts.md` | 9 | `OS_SaveContext`/`OS_LoadContext`, `OSi_IdleThreadProc`/`OS_Halt`, `OS_SetIrqFunction`: `autoload_2` -> `itcm`; `OS_IrqHandler`: `itcm/autoload_2` -> `itcm`; `CARDi_TaskThread`, `CARDi_Request`/`CARDi_OnFifoRecv`, `TP_WaitBusy`, `PXI_SetFifoRecvCallback`, `NNS_SndCaptureCreateThread`: `main` -> `autoload_2` |
| `systems/audio.md` | 14 cells | `main (NNS)` / `main (SND)` -> `autoload_2 (NNS)` / `autoload_2 (SND)`; `PXI_SendWordByFifo`: `main` -> `autoload_2` |
| `systems/rng.md` | 2 | `OS_GetLowEntropyData`, `MATH_CalcCRC8/16/32`: `main` -> `autoload_2` |
| `engine/boot-and-entry.md` | 1 | `OS_Halt`: `autoload_2` -> `itcm`, in the table and in the prose citation |
| `systems/save-data.md` | 2 groups | `card_common` / `card_backup` are translation-unit names, not modules; now `autoload_2 (card_common)` / `autoload_2 (card_backup)` |

### 2.5 Run directories -- FOR THE ORCHESTRATOR

`scratchpad/` is not visible from this worktree, so none of these could be checked. Every
distinct `scratchpad/` path the wiki names, for the orchestrator to verify against the real tree
(the ones most likely to be wrong are marked):

`scratchpad/cycle39/execution39-touch39-005/off`; `scratchpad/cycle40/iterate.sh`;
`scratchpad/cycle40/run_direct.py`; `scratchpad/cycle40/run_town.py`;
`scratchpad/cycle40/tap.sh`; `scratchpad/cycle40/runs/off-<name>`;
`scratchpad/cycle40/runs/rtc-000000`; `scratchpad/cycle40/runs/tap-D55b`;
`scratchpad/cycle40/runs/tap-D56` (+ `receipt.json`, `tap-D56-run.log`);
`scratchpad/cycle40/runs/tap-D57`; `scratchpad/cycle40/runs/tap-D58`;
`scratchpad/cycle40/runs/tap-D59`; `scratchpad/cycle40/runs/tap-D60` (+ `tap-D60-run.log`);
`scratchpad/cycle40/runs/tap-D61`; `scratchpad/cycle40/runs/tap-native`;
`scratchpad/cycle40/runs/town-R1`; `scratchpad/oracle/negctl.py`; `scratchpad/oracle/off`;
`scratchpad/oracle/rtc-000000` (+ `.json`); `scratchpad/oracle/tap-220`;
`scratchpad/oracle/tap-24700`; `scratchpad/oracle/tap-fullpad` (+
`compare-vs-tap-D56.txt`); `scratchpad/oracle/tap-window`; `scratchpad/save/fresh.sav`.

Named without a `scratchpad/` prefix, so the spelling cannot even be guessed from the page:
`tap-D62` (`systems/dialogue.md`, `systems/input-and-touch.md`,
`experiments/touch-calibration.md`), `tap-interp` (`experiments/two-tap-town-recipe.md`),
`tap-D55` (`systems/player.md` -- note `two-tap-town-recipe.md` cites `tap-D55b`; one of the two
is probably wrong), `menu-a`, `menu-b`, `long-a` (`systems/dialogue.md`, `systems/economy.md`),
`off-D4`..`off-D51` and `tap-D52`..`tap-D54` (several engine pages, always inside a cycle40-log
citation). **Needs measurement: `ls` the real `scratchpad/cycle40/runs` and `scratchpad/oracle`
and reconcile.**

### 2.6 Grade tags

Scripted a paragraph-level check over every prose paragraph outside Summary sections, tables and
fenced blocks, on the 36 content pages. **No prose paragraph on any content page lacks a grade
tag.** Three weaker patterns are worth naming rather than "fixing":

- Six pages carry a whole "Data it reads and writes" table with no per-row grade and a single
  line underneath -- "All rows are S, cited from the files in the previous table"
  (`systems/dialogue.md`, `player.md`, `villagers.md`, `events-and-calendar.md`,
  `weather-and-seasons.md`) or a short grade paragraph (`systems/town.md`, `economy.md`). STYLE
  asks for a grade per row. This is a defensible abbreviation and is left, but a reviewer
  striking rows would be within the rules.
- The `systems/` pages written by the game-mechanics pass cite unbackticked
  (`[S: func_02063bb4, main, port/shim/game/season.c]`) where every other page backticks. Purely
  cosmetic; the scripted checks handle both.
- `data/` pages redefine **S** to include bytes read out of `extract/adm-kr/`. That is declared
  in `data/README.md` and in a grade note on each page, and it is honest, but it means an **S**
  on a `data/` page is not the same claim as an **S** on an `engine/` page. Since `extract/` is
  absent from this worktree, none of those image citations could be checked at all.

## 3. Style

- **Page length.** STYLE's 80-400 rule scopes itself to `engine/`, `systems/` and `data/`. All 22
  such pages are inside it (shortest `data/fish-and-bugs.md` 155, longest
  `engine/display-objects.md` 257). Out of scope but short: `experiments/rng-determinism.md` 70
  and `experiments/off-recipe.md` 78, plus every README and the glossary.
- **Stray harness tags -- FIXED.** Fourteen pages ended with a literal `</content>` line and
  `systems/save-data.md` with `</content>` plus `</invoke>`: all of `systems/{audio,
  input-and-touch, network, rng, save-data, time-and-rtc}.md` and all eight `experiments/` files
  including its README. Stripped.
- **Korean.** Eleven quoted phrases across `systems/dialogue.md`, `player.md` and `town.md`, plus
  one in `engine/text-and-messages.md`. Every one is a single short UI string used to identify a
  screen (`당신 이름은?`, `마을사무소`, the five-option menu). Longest is the five-option
  destination line at 22 characters. Within STYLE rule 5.
- **Code listings.** Six fenced blocks: environment recipes in `engine/file-system.md` and
  `engine/graphics-pipeline.md`, and re-derivation Python in `data/rom-layout.md`,
  `archives.md`, `villagers.md`, `items.md`, `fish-and-bugs.md`, `music.md`. STYLE rule 6 bans
  code listings; STYLE's own template explicitly permits an inline recipe under "How to check
  it", and `data/README.md` sanctions the Python snippets. None is a transcription of ROM code,
  so all are left. Flagged so the rule and the practice can be reconciled deliberately.
- **Host addresses.** One: `data/archives.md:27` cites "host `0x008b932f` / `0x008b939a`" while
  tracing VRAM writes. It is labelled "host", which is what STYLE rule 3 is protecting against.
  `engine/memory-map.md` also names host ranges, in a section headed "What the PC port adds, and
  what it maps" that exists to keep them separable. Both left.
- **`</content>` aside**, no page carries a host address where an NDS address belongs.

## 4. The glossary

Thirty rows before this pass, all of them correct except one; fourteen added.

**FIXED:** the `channel` row said channels are "opened through `func_02003348`".
`engine/scenes-and-channels.md` names `func_0202f134` as the front door;
`systems/events-and-calendar.md:77` names `func_02003348`. Both are true -- they are two
entry points, one for a scene's channel list and one for the special-NPC scheduler's staged
visitor, and both end in `func_020edc58`. The row now says so and links both pages.

**Added**, each with the function or address that defines it, for terms used on two or more
pages that had no row: `arena`, `BMG`, `deny list`, `display object`, `game heap`, `NARC`,
`OFF recipe`, `PXI tag`, `step gate`, `town recipe`, `TP_POINT`, `VBlank task list`,
`walk mode`. That takes the glossary from 36 to 49 lines.

Terms deliberately not given a row: `overlay`, `scene`, `save image`, `player slot` (already
present); `frame`, `grade`, `oracle`, `interpreter path` (already present or defined in
`README.md`/`STYLE.md`); `shadow build`, `receipt`, `differential check` (port-process terms
belonging to `docs/`, not to a game-mechanics wiki).

## 5. Everything else that was checked and was fine

- Every `func_XXXXXXXX` name whose address is encoded in the name matches its symbol-table
  `addr:` -- zero mismatches over 568 citations. No D12-class name in the wiki except the two
  the pages already flag (`RTC_SetDateTime` at `0x0211e7c0`, `CARD_GetCurrentBackupType`).
- `systems/README.md` listed six pages as "Planned" that the same file's appended block reported
  as written, and gave a line count for `input-and-touch.md` (231) that had drifted by fifteen.
  **Fixed**: the Planned section is gone, the six are listed as written with links, the volatile
  line-count column is dropped, and the experiment tally is stated with its source.
- `engine/README.md` names all nine engine pages and no others.
- `data/README.md` names all six data pages; `experiments/README.md`'s run / not-yet-run split
  matches every page's own **Status** line.

## 6. What needs the orchestrator

1. **The run-directory spellings in section 2.5.** Cannot be checked from a worktree.
   In particular `tap-D55` versus `tap-D55b`, and whether `tap-D62`, `tap-interp`, `menu-a`,
   `menu-b` and `long-a` live under `scratchpad/cycle40/runs/`.
2. **`docs/kb/hybrid/runtime.md:158-160` is stale.** It says "40 shim files and
   `func_020b1b84` denied"; `port/tools/interp_registry.py`'s `DENY_FILES` has 49 basenames. The
   "93 host services" figure beside it is dated `verified-at 6ca48706` and was not re-derived
   here. The wiki now cites the measured 49; the kb page is outside this audit's remit.
3. **The port's stale shim headers.** `port/shim/game/chanlist.c:6-8` and
   `port/shim/gfx/pmflist.c:53, 607` still call channel 189's object "the FIELD render object"
   after `port/BOOT-STATE.md:1159-1171` retracted it. The wiki no longer repeats them; the
   headers should be corrected at the source or the next pass will re-import the error.
4. **`data/` image citations are unverifiable here.** `extract/` is absent from this worktree, so
   every file count, size, magic and path template on the six `data/` pages -- roughly 200
   citations -- was taken on trust. Re-run each page's own "How to check it" snippet from the
   repo root where `extract/` lives.
5. **`func_0205401c`'s `gSoundFlag`.** Needs measurement: watch that global and the top/bottom
   screen contents together across a run, and say what the bit-15 write is actually doing.
   Until then `data/music.md` files it as a Hypothesis.
6. **`func_0209ded0` / `MB_GetBeaconRecvStatus` at `0x0209ded0`.** Needs measurement: a
   boundary re-cut of that region, or a disassembly showing which name is the mistake.

## Related

- `../STYLE.md` -- the rules this audit checks against
- `../README.md` -- the grade definitions
- `../glossary.md` -- the terms table this pass extended
