# Gameplay walkthrough: out of the town hall, into the house, and a save that reloads

**Summary.** The two-tap town recipe ends with the player inside the town hall talking to Pelly,
and until cycle41 nobody had played past that. With a snapshot of frame 48,000 and a
pad-and-stylus timeline (`ACWW_PADSCRIPT`), an experiment costs 20 to 160 seconds instead of a
22-minute replay. What a scripted player can do today: answer Pelly, walk out of the town hall,
walk the town in every direction, open the map, open the pockets, drive a UI page with the stylus,
see the town at night, open the save menu, **shake a fruit tree, pick the fruit up and find it in
the pockets, read a field sign, and walk in through the town hall's door and out again**. **SAVE43
adds the rest of the opening**: find the player's own house off the map's GREEN icon, go in, come
out to Tom Nook, run his loan speech out -- and then SAVE, which the game writes itself into both
flash banks, and RELAUNCH into the saved town. Villagers are drawn and talk there too, which
retracts GAMEPLAY42's "no villager is ever drawn". **GAMEPLAY43 then found a condition every
frame number on this page was missing, and GAMEPLAY44 corrected it: the arrival tutorial's
four-thousand-frame hold is a property of the TOWN, not of the clock arm** -- GP43's two arms
differed in both at once, because a frozen clock also generates a different town, and with
`ACWW_RTC_FREEZE_UNTIL` holding the town fixed both clock arms hold identically. **GAMEPLAY44
also talks to a villager on purpose for the first time**, by pointing the navigator at the actor
manager rather than at a door. **GAMEPLAY45 then measured the thing all of that was waiting on**:
the pockets page's fifteen item-slot centres and the player's body, and a scripted stylus stroke
that the port delivers as ONE contact -- a single pen-down edge, fifteen moving publications, a
single pen-up. It also stopped the door arrival walking the player past buildings, by firing it
only on the approach axis and by ordering the doorway sweep from the player's own sub-tile
position. **GAMEPLAY46 then withdrew that cycle's sharpest claim**: those doors were never closed.
Nook's shop opens before the save and after it, and what was in the way was the navigator's
doormat, two tiles off the real doorway on the two buildings whose notch is a corner. With it
corrected the shop is entered closed-loop, the counter dialogue runs, and the scripted stylus
drag is shown ACTING on the game -- it picks the uniform out of the pockets and carries it.
**GAMEPLAY47 then withdrew GAMEPLAY46's remaining claim in turn: that drop was never
refused.** The uniform is worn -- pocket slot 0 and the player's worn-clothing field at
record `+0x2408` SWAP, which is why an item is still in slot 0 afterwards -- and the ROM's
handler is ov096's equip dispatcher, `func_ov096_0229e3b0` case 2. Nook says so in words, sets
the job's first task and hands over seven flowers; the player can plant one; and all four
remaining doors -- Able Sisters, the gate, the museum, the town hall -- are walked into
closed-loop, one `goto.py` each. What the port still cannot do: earn a Bell, use or buy a tool,
write a letter, save from the bed, or enter a villager's house -- and the first three are now
behind a CHORE rather than a defect (Nook pays for seven flowers planted outside his shop, the
shop menu is behind the pay). **GAMEPLAY48 finishes that chore**: all seven flowers are planted,
one per run, each verified in the player record -- what had stopped it was a confirm point read
off a zoom rather than measured (the `땅에 심기` box is drawn BESIDE the tapped slot and moves
with it) and a mode-switch rule that had lost its condition. Nook still does not pay: he goes
for a break near the town hall, where the NPC standing on the plaza turns out to be **고북,
Tortimer, the MAYOR**, met here for the first time. And **the villager's door answers itself** --
the box on the doormat reads `이 몸은 밖에 계신다 / 곤잘레스`, "I am OUT", which is a game rule
and not a defect. Nothing faulted in any of it, across 265 scripted runs in seven
cycles. **The oracle has
since run the same pad timeline on the original** (ORACLE44): the long picture hold after the town
hall and the black top screen in the town hall are both the game's own behaviour, and the port's
only rendering difference over the stretch is its flatter sky.

## Purpose

Find out what a player can actually do on the interpreter path past the frontier of LONG41, and
name and classify every break, so that the next cycle's work is chosen by what blocks play
rather than by what is next in a plan.

## Recipe

Three steps. **Step 1**, once, about 22 minutes -- the town recipe with a snapshot at 48,000
(note `ACWW_TOUCH2_AT=24700`; the older 24,600 never confirms the town name):

    python -B scratchpad/cycle40/run_direct.py town-S2 \
      ACWW_INTERP=1 ACWW_TOUCH_AT=6900 ACWW_TOUCH_EVERY=60 ACWW_TOUCH_REPEAT=2 \
      ACWW_TOUCH2_X=221 ACWW_TOUCH2_Y=181 ACWW_TOUCH2_AT=24700 ACWW_TOUCH2_FOR=10 \
      ACWW_TOUCH2_EVERY=60 ACWW_TOUCH2_REPEAT=2 \
      ACWW_STOP_FRAME=48600 ACWW_SHOT_AFTER=36000 ACWW_SHOT_EVERY=1500 ACWW_PAD_SAMPLE=0 \
      _TIMEOUT=1800 ACWW_STATE_SAVE=48000+400:<abs>/scratchpad/gameplay/st/town48000.st

**Step 2**, a pad script -- one row per line, `#` and blanks ignored, numbers decimal unless
prefixed `0x`:

    <frame> <mask> <frames>          hold `mask` from `frame` for `frames` frames
    <frame> T <x> <y> <frames>       hold a stylus contact at x,y likewise

with `mask` in the game's `0x2fff` space (A=1 B=2 SELECT=4 START=8 Right=16 Left=32 Up=64
Down=128 R=0x100 L=0x200 X=0x400 Y=0x800). Overlapping pad rows OR together; the first matching
stylus row wins [E: `port/platform/hostinput.c`; `docs/kb/hybrid/recipes.md` section 4b].

**Step 3**, the experiment:

    sh scratchpad/gameplay/gp.sh <name> <snapshot.st> <script.pad> <stop frame> <shot every>

`gp.sh` resumes the snapshot, drives the script, takes stills and prints the log's input, touch,
state and fault lines [E: `scratchpad/gameplay/gp.sh`; the GAMEPLAY42 copy with its own worktree
root is `scratchpad/gameplay42/gp42.sh`].

**A snapshot does not survive a relink.** A `.st` file names the link identity and the blob
count that wrote it and is refused by name on any other build, so step 1 is paid once per
worktree, not once per project: cycle41's snapshots are `link 0x6aa14a4d/0x013c0000`, 113 blobs,
and GAMEPLAY42's relink is `0x6aa16242/0x01423000`, 117 blobs [E: `docs/log/cycle41-gameplay.md`
GAMEPLAY42; S: `docs/kb/hybrid/savestate.md` section 5].

**Aim off the map, not off dead reckoning.** One 44-second run holding X shows the whole town --
the gate, the town hall, both shop plazas, four house icons and three villager names -- and four
2,400-frame survey walks then say how many frames of each direction reach each of them. Every
GAMEPLAY42 interaction script was written from that picture [E: `gp42-S1`, `gp42-Wwest`,
`gp42-Wnorth`, `gp42-Wsouth`, `gp42-G1`].

Three pad-script rules the runs paid for:

- **Press A INSIDE a direction hold** when the action needs facing -- shaking a tree, talking.
  Overlapping rows OR together, so `57080 32 300` plus `57120 1 10` is "A while still facing
  west" [E: `gp42-F5`; S: `docs/kb/hybrid/recipes.md` section 4b].
- **Press A STANDING STILL** to pick an item up. A script that walks one square first gets
  nothing [E: `gp42-F3` empty pockets vs `gp42-F4` a cherry in slot 1].
- **B closes a message box but not a two-choice prompt.** They are different boxes
  [E: `gp42-N2` vs `gp-E1b`].

## Expected observations

Frames are the port's counter, continuing from the snapshot.

| frames | script | what is on screen |
|---|---|---|
| 48,000 | -- | inside the town hall, Pelly, a two-choice prompt [H: `scratchpad/cycle40/runs/town-S2`; receipt lost with its worktree; repeat the named recipe and retain the stated frames] |
| 48,000..49,200 | eight B pulses then Down | **nothing changes**: B does not close a choice and an open box locks movement [E: `gp-E1b`] |
| 48,010..48,970 | seventeen A pulses | the tutorial: the map, the lower screen's arrow, and `X 버튼` [E: `gp-E4`] |
| 49,200 | six B pulses | the dialogue closes; the date/time HUD `6/15 AM10:00` appears [E: `gp-E6`] |
| 49,600 | Down | the doorway transition [E: `gp-E6`] |
| **49,800** | Down | **outside, on the town hall plaza, clouds over the sky** [E: `gp-E6`; **O**: the original is still in the doorway transition here, both screens fully black, and is outside at 50,100 -- the port leads the walk by about 300 frames, a scene-progress offset, and this is the first frame the two differ (`ncc` 0.0000): `scratchpad/oracle/walkout/`] |
| 50,300 | X | the lower screen becomes the town map: river, buildings, the player's marker, three villager names [E: `gp-E7`] |
| 50,600..50,830 | three `T 243 10` contacts | the page turns to the POCKETS screen: portrait, name, `00000` bells, the empty item grid [E: `gp-E8`] |
| 50,260 | Y (from `st/out50200.st`) | the pockets open directly; START/SELECT/R/L each move to another page [E: `gp-E10`] |
| 50,700..54,700 | walking south | **a large grey Nintendo-DS-shaped model fills the lower screen and the picture holds** [E: `gp-E13`; **O**: `scratchpad/oracle/walkout/orig`, 50,700..54,600 -- the ORIGINAL freezes its lower screen through the same windows (0 changed pixels per 300-frame window at 51,900..53,700 on both) and shows the same model in the same place, bottom-screen `ncc` 0.967..0.973] |
| 55,000 | still walking | the hold ends by itself; grass, trees, a house, a bug [E: `gp-E14`; **O**: both producers' lower screens come back on the same frame, **54,900**, 46,776 changed pixels on the original against 46,949 on the port] |
| 55,400..57,300 | Down/Left/Up/Right, 400 each | the town: a plank bridge over the river, fruit trees, a house, a rock, and ~~a villager on screen at 56,600~~ -- at x4 on the identical frame that shape is a bed of white-and-purple pansies, so this cell's villager is **retracted** [E: `gp-E15`; retraction `gp42-V1` 056,600] |
| 55,500.. | `ACWW_RTC_TIME=235900` | night: a moon, dark sky, darkened ground and water [E: `gp-E17`] |
| 55,460 | START | the game's own save prompt, refusing: `어라? 지금은 아직 저장하지 못하나 봐요` [E: `gp-E18`] |

Frames below continue from `st/town55400.st` on the GAMEPLAY42 build unless the row says
otherwise; a `gp42-*` receipt is a run directory under `scratchpad/cycle40/runs/`, indexed by
`scratchpad/gameplay42/RECEIPTS.md`.

| frames | script | what is on screen |
|---|---|---|
| 55,560..55,740 | X held | the town map in full: a gate arch top-left, the town hall top-right, two shop plazas, four house icons, two bridges, a pond, and the legend -- the player's house plus three villager names [E: `gp42-S1`] |
| 55,460..57,060 | west 1,600 | the shop plaza: a wooden shop with a brown door under a `너굴 잡화점` sign, and Able Sisters' green-roofed shop beside it [E: `gp42-Wwest`, `gp42-N1`] |
| 55,460..56,660 | north 1,200 | a stone bridge, then the town hall's front: marble, columns, an emblem in the pediment and a black doorway [E: `gp42-Wnorth`] |
| 57,280..57,310 | facing a cherry tree, A at 57,280 | three cherry pairs hanging high in the canopy [E: `gp42-F5`] |
| **57,320..57,350** | the same | **the cherries fall and land on the ground beside the trunk** [E: `gp42-F5`, one still every 10 frames] |
| 57,360 | -- | a green `체리` name balloon over the player: he is standing on the fallen fruit [E: `gp42-F5`, `gp42-V1`] |
| **57,400** | A, standing still | the pick-up. At 57,900 the pockets page shows **a cherry in the first item slot** [E: `gp42-F4`] |
| ~58,000 | A at a roofed tip sign | **the game's own yellow message box**, titled `낚시 지침`, with the blue continue arrow; B closes it [E: `gp42-N2`] |
| 49,720..50,800 | from `st/town48000.st`: A x17, B x6, Down 350, then **Up** | the town hall plaza and the wooden doors, walked into from below [E: `gp42-H6`] |
| **50,880..51,160** | the same | **black -- the doorway transition** [E: `gp42-H6`] |
| **51,200..52,400** | the same | **inside the town hall**: the wooden floor, the counter, the barrel and Pelly at the desk [E: `gp42-H6`, `gp42-H7`] |
| 52,560..52,720 | B, then Down 700 | black again, then **outside on the plaza**: in and out, both directions, by walking [E: `gp42-H7`] |
| 58,640..59,200 | west 1,700 then north 2,000 | the town's northern cliff. The gate is further west and was not reached [E: `gp42-G1`] |
| scattered, 17 of 1,160 stills | any | **the acre ground drops out**: a flat `0x2184FF` lower screen, sometimes with the buildings and the player still drawn over it [E: `gp42-V2` 056,100, `gp42-H2` 058,760..059,080] |

## SAVE43 -- the house, Nook, the save, and the reload

Frames continue from `st/b55400.st` on the SAVE43 build (`fbfc987d` plus SAVE42's `frame.c`
census call); a receipt named here is a run directory under `scratchpad/save43/runs/`, indexed
by `scratchpad/save43/RECEIPTS.md`. The town recipe that starts the chain now costs **522 s**
rather than 1,285-1,360, because PERF42's renderer landed in between.

| frames | script | what is on screen |
|---|---|---|
| 55,600 | X, stills every 10 | the map, with the player's **own house as the GREEN icon** at map (75.2, 122.1) and the three villager houses blue. The player's marker **BLINKS** -- a 50-frame sample can miss it entirely [E: `gp-M1`, `gp-W2`] |
| 55,460..56,360 | west 900 | too far: Nook's shop plaza. Map reading, not dead reckoning, is what corrects it [E: `gp-W1`] |
| 56,400..56,745 | east 270, south 55 | the front paving of a house with a wooden door and a **red mailbox** [E: `gp-W3`, 056,740] |
| 56,900..58,000 | Down+Right, then **Up held 700 with Left pulsed 20-in-100**, then A under a second Up hold | the door opens: **inside the player's house at 058,020**, black at 058,080, the room at 058,140 -- a bench, a figurine, a stereo [E: `gp-D9`; eight other approaches all walked past the door, `gp-D1`..`gp-D8`] |
| 58,420..58,960 | six legs with A pulses | the sweep walks back OUT of the door [E: `gp-I1`] |
| **59,040** | -- | **Tom Nook is at the door, DRAWN, and talking** [E: `gp-I1`, `sequence4_[13]`] |
| 59,120..62,100 | A every 60 frames | his speech: the house, his shop, the **19800 bell** loan, the save instruction, the part-time job -- then he walks away [E: `gp-N1`, `gp-N2`] |
| 62,300 | -- | the player alone with the HUD, and `0x021f3c30` is **0**: the save block is gone [E: `gp-N2`; `gp-W0`'s watchpoint names `func_020a128c` as the writer] |
| **63,200** | START | **the real save menu**: `오늘은 여기까지 하시겠습니까?` with `저장하고 마치기` / `좀 더 놀기` [E: `gp-S1`] |
| 63,600..067,100 | A | `저장하고 있습니다 / 전원을 끄지 말고 그대로 기다려 주십시오！`, while the game writes 744 x 256-byte pages over `0x00000..0x2e7f8` with 744 verifies and 0 mismatches [E: `gp-S3`'s census] |
| **067,200** | -- | **`저장했습니다！`** [E: `gp-S3`] |
| a NEW launch, 3,000..4,000 | the boot key phases, no snapshot, the same `ACWW_SAVE` | **inside the player's own house** -- the bed, the phone -- under `시작 준비 중입니다` [E: `boot-A`] |
| the same, 5,000..12,000 | -- | **the player outside their own front door**, red mailbox, stone paving, HUD `6/15 AM10:00`. No taxi and neither keyboard [E: `boot-A`; the erased-store control is the taxi interior with the name keyboard] |
| the same, +a pad timeline, 6,200..6,900 | four walking legs | the reloaded town is playable: the player walks, and an NPC introduces himself (`도루묵씨`) [E: `boot-B`] |
| 057,360 and 058,380 | a walk that bumps a villager, then A | **곤잘레스 is drawn -- a green rhino with a fishing rod -- with a name balloon and a dialogue box.** RETRACTS GAMEPLAY42's GP42-1 headline; what changed between the two measurements is not established [E: `gp-D2`, `gp-D4`] |

**The three rules this section is worth reading for.** A house door opens on the SLIDE, not on
aim -- hold the direction that pushes into the front wall and pulse the perpendicular direction
20 frames in every 100, then press A under a second push; eight approaches that aimed, including
one aligned to the map pixel, all walked past. The map marker BLINKS, so sample it every 10
frames. And the walking rate on paving is a third of the open-ground rate (3 map px per 60
frames against 0.184 px/frame), which is why every dead-reckoned comb overshot.

## What the port and the game each get right

The pad and the stylus both reach the game. A B press deletes a character on the town-name
keyboard [E: `gp-E1`, 48,000..48,240]; an A press advances a dialogue [E: `gp-E4`]; a scheduled
contact at 243,10 turns a UI page [E: `gp-E8`, three `acww touch: DOWN x=243 y=10` lines]. The
lower screen's page set -- map, pockets, keyboard -- renders in full, the world's 3D renders and
the camera follows the player, the affine sky renders by day and by night, and the HUD carries
the RTC date and time [E: `gp-E7`, `gp-E10`, `gp-E15`, `gp-E17`].

Two refusals in the walkthrough are the GAME's and not the port's: B does not close a choice
prompt [E: `gp-E1b`], and START's save prompt says the player cannot save yet -- which is not a
DAY rule but the move-in mode word `0x021f3c30`, and it lifts the moment the arrival finishes
[E: `gp-E18`, then SAVE43 `gp-S1`; S: `func_0209f6e4`].

GAMEPLAY42 adds three whole interactions to that list. The world responds to A: a fruit tree
shakes and drops its fruit, a dropped item goes into the pockets and shows there, and a field
sign opens the game's own message box [E: `gp42-F5`, `gp42-F4`, `gp42-N2`]. A door works in both
directions: the player walks north into the town hall's doorway, the screen goes black, and he
is inside with Pelly; walking south takes him out again [E: `gp42-H6`, `gp42-H7`]. Across 26
runs and 1,160 stills there was no `unimplemented`, no fault, no STOP status and no dropped PXI
tag [E: `scratchpad/gameplay42/RECEIPTS.md`].

## The villagers, twice retracted

**RETRACTED, and this section is the retraction.** It used to open "No villager has ever been on
screen in this project" and to explain that by a lost bind of the draw pointer-to-member at `actor
+ 0x8b0`. Both halves are gone:

- **The bind is not lost.** A store watchpoint over the walk out of the town hall produces three
  stores and no more: two binders write `{0x0226d809, 0}` and a state enter
  (`func_ov068_0226bb3c`) deliberately writes `{0, 0}` from autoload_2 `.data`, which is mwcc's
  static NULL member pointer. The null the draw slot sees is the ROM's own value [E:
  `docs/log/cycle41-gameplay.md` VILLAGER42, `v42-W2`; S: `wiki/systems/villagers.md`]. -
  **Villagers ARE drawn, and one has been talked to.** In the acres around the player's house a
  villager is on screen with a fishing rod and answers a bump with a dialogue box; Tom Nook is
  drawn through his whole arrival speech; a third NPC introduces himself in the reloaded town [E:
  `docs/log/cycle42-save.md` SAVE43, `gp-D2`, `gp-D4`, `gp-N1`, `boot-B`]. - **Why the hunts
  failed is REACH, not drawing.** GAMEPLAY42's 1,160 stills were taken almost entirely inside the
  arrival tutorial's hold, where the pad is discarded, so the sweeps never covered the ground the
  dead reckoning claimed [E: VILLAGER42 `v42-V1`, `v42-V3`]. And GAMEPLAY43 names the reason an
  AIMED walk fails too: the manager at `0x021d1d4c` holds two live walking actors whose own
  `VecFx32` at `actor + 0x5c` reads world (133, 51) and (105, 97), but `0x021f69d4` -- the only
  published player position -- is a SCENE-ENTRY position, unchanged across 1,400 frames of
  walking, so nothing can be aimed off it. Three aimed sweeps met nobody [E:
  `docs/log/cycle41-gameplay.md` GP43-5, `g43-P2`/`P3`, `g43-T2`/`T3`/`T4`].

So the open question is no longer "are they drawn" but **"where is the player, this frame"**, and
it is one peek-and-diff away.

## GAMEPLAY43 -- the clock decides whether there is a tutorial at all

Frames continue from `st/town48000.st` on the GAMEPLAY43 build (`2e579f09`, unmodified); a
receipt named here is a run directory under `scratchpad/gameplay43/runs/`, indexed by
`scratchpad/gameplay43/RECEIPTS.md`. **Read the clock arm on every row.** The only port code
between SAVE43's `fbfc987d` and this commit is RTC42, and it is enough to change what the game
does.

| frames | clock | script | what is on screen |
|---|---|---|---|
| 049,800 | ADVANCING | A x17, B x6, Down | outside on the plaza, **walking** -- and it keeps walking to 055,500 with no hold anywhere [E: `g43-H0`, `g43-P1`] |
| 050,800..056,600 | ADVANCING | X held 200 then B, every 600 | the map opens on the FIRST press and B closes it, ten times over; the A-pulse arm and the no-input CONTROL are pixel-identical to each other [E: `g43-PRXB` vs `g43-PRA` vs `g43-PRNONE`] |
| **051,200..054,800** | **FROZEN** | the same `P1-out-and-wake.pad` | **the hold is back**: the bottom screen changes 0.3-0.4% per still, twitches at 051,600 and 054,000 -- ORACLE44's own two frames -- and releases at **055,000** [E: `g43-BP1`, `ACWW_RTC_FREEZE=1`] |
| 055,460..059,220 | ADVANCING | seven legs with a map read after each | the marker walks (128.5,165.5) -> (64.5,109.5) -> (76.5,128.5) and the player's house is on screen with its wooden door and RED MAILBOX. **Rates on this ground: 0.073 map px/frame east-west, 0.107 north-south** -- a third value again, so the rate is a property of the acre [E: `g43-M1`, `g43-V1`, `g43-V3`, `g43-V4`] |
| 059,650..060,060 | ADVANCING | **Up held 900, LEFT pulsed 40-in-80, A every 60** | **the door opens first try**: open doorway at 059,900, black 059,940..060,040, the room at 060,060. `gp-D9`'s 20-in-100 pulse, transcribed onto the same frames, walks 700 frames PAST the house [E: `g43-E2`; the miss is `g43-E1`] |
| 062,620 | ADVANCING | Down held 900, RIGHT pulsed 40-in-80, A every 60 | back OUT, the same shape mirrored, also first try [E: `g43-E4`] |
| **063,100** | ADVANCING | -- | **Tom Nook is at the door, drawn and talking** [E: `g43-E4`] |
| 068,100 | ADVANCING | A every 60 for 4,550 frames | the speech ends and `0x021f3c30` is **0** [E: `g43-N3`; before, `g43-P4` reads 1] |
| 068,050..074,200 | ADVANCING | START then A every 100 | **the save**: 744 x 256-byte pages over `0x00000..0x2e7f8`, 744 verifies, 0 mismatches, and `savetool.py check` says *the game would LOAD this bank* for both [E: `g43-S1`, `savecheck-S1.txt`] |
| 069,290 | ADVANCING | west 550 in two legs with map reads | **Able Sisters' shop on screen**; Nook's is 15 map px further west, and its signboard and brown door are on screen one run later [E: `g43-G2`, `g43-G3`] |
| 069,300..072,200 | ADVANCING | four approaches to Nook's door BY MAP PIXEL | **not entered.** A TREE stands on the shop's front paving, and the map cannot resolve which side of it the player is on -- the icon is 9 map px and the marker 3. These four are the last data point of the map-pixel method [E: `g43-G3`..`g43-G6`] |
| 068,000..071,400 | ADVANCING | `port/tools/goto.py --from st/post68000.st --to nook` | **INSIDE NOOK'S SHOP.** A* over the acre collision grid from the LIVE player position at `0x021c749c`, re-planning each iteration: tiles (40,56) -> (19,60) -> (21,59) -> (19,43) -> (20,58), then `the field grid is 1x1 -- the player is INSIDE`. Nook behind his counter, the interior drawn, a dialogue box up. Five iterations, 90 s [E: `NK-1`..`NK-5`; S: NAV42] |
| 071,550..075,100 | ADVANCING | A every 70 at the counter, then `Y` | **Nook's part-time job** -- and this cell is DISPUTED. It read "he offers the uniform, the player CHANGES INTO IT on screen, and the pockets page shows it equipped"; GAMEPLAY44 ran the same counter and got an instruction to DRAG the uniform onto the player's body that neither A nor Y clears, with the wallet `0` and every pocket slot `fff1` in the save. Both cannot be true, GAMEPLAY44's is the later and better-evidenced reading, and GAMEPLAY45 never reached the counter to break the tie. **Treat the uniform as NOT worn until a still shows it** [E: `g43-NK6` against `g44-NK1`/`NK2`/`NK3`, `savecheck-S1.txt`] |

## GAMEPLAY44 -- one town, both clock arms; and a villager talked to on purpose

Receipts are run directories under `scratchpad/gameplay44/runs/`, indexed by
`scratchpad/gameplay44/RECEIPTS.md`; the log section is `docs/log/cycle41-gameplay.md` GP44-1..4.
The TOWN column is the one to read, and it is named by the villager ids in the live record --
77/16/127 for the frozen-generated town, 127/109/67 for the advancing one, both reproduced here
from GAMEPLAY43 and SAVE43 exactly.

| frames | town | clock | what is on screen |
|---|---|---|---|
| 050,400..055,000 | frozen-gen (77/16/127) | FROZEN (`_FREEZE_UNTIL=999000`) | the DS-illustration hold: 0.003-0.004 changed per still, twitch 051,600 and 054,000, released 055,000 [E: `g44-FRZ`] |
| 050,400..055,000 | **the same snapshot** | ADVANCING (`_FREEZE_UNTIL=48000`; the log's clock reads 10:01 at 51,591 and 10:02 at 55,182) | **the same hold, the same frames**, and 048,000..051,400 are SHA-256 IDENTICAL to the frozen arm. The arms first differ at 051,600 -- the frame the minute turned -- by 7.9% of pixels at a mean luma change of -0.005, i.e. the HUD [E: `g44-ADV`, `armcmp.py`] |
| 048,000..055,600 | advancing-gen (127/109/67) | ADVANCING | **no hold**, 0.37-0.43 changed per still throughout: walking, exactly as `g43-P1` [E: `g44-BADV`] |
| **056,580..057,480** | frozen-gen | advancing | **A VILLAGER TALKED TO.** `goto.py --to actor:1` reads the manager at `0x021d1d4c`, takes the actor's own `+0x5c`, walks to the tile beside it and presses A: 마르 drawn with a bucket, the box up on 15 of 18 stills, and the text ADVANCING under the A pulses to `그래서 몇 가지 질문을 / 준비했어요, 아~옹！` [E: `TALK1-1`..`TALK1-5`, `g44-TALK`] |
| 065,683 / 087,726 | frozen-gen | advancing | inside the player's house: a bench with a figurine and a stereo, 4x4 tiles, **no bed** -- before AND after the arrival [E: `g44-BED1`, `g44-BED3`, `roomgrid.py`] |
| 074,900..081,400 | frozen-gen | advancing | the mode word `0x021f3c30` goes 1 -> 0, then **the save**: 744 pages, 0 verify mismatches, both banks `-> the game would LOAD this bank` [E: the Nook-speech run, `g44-S1`, `savecheck-S1.txt`] |
| 081,500..086,800 | frozen-gen | advancing | the game's own continue path -- **the wake-up room with the RED BED and the phone**, then the player outside their own front door, HUD `6/15 AM10:10` [E: `g44-WAKE`; `png/BED2-082500.png`] |
| 088,560..097,700 | frozen-gen | advancing | **inside Nook's shop in TWO iterations, 12.4 s**, from the doorstep 22 tiles away; the counter speech then stops on `작업복을 터치한 상태로 / 자신의 몸으로 / 가져가서 갈아입어구리` and neither A nor Y clears it [E: `NOOK-1`/`NOOK-2`, `g44-NK1`/`NK2`/`NK3`] |

**Two things to carry away.** The first is the correction above: the hold is the town's. The
second is that **the last mile of this walkthrough is a STYLUS DRAG.** Nook's job -- the only
route to a first Bell, and therefore to a purchase, a sale, stationery, a letter and the store
at `0x337fc` -- begins by asking the player to touch the work uniform in their pockets and drag
it onto their own body. `ACWW_PADSCRIPT` has stylus rows and consecutive rows at moving
coordinates are a stroke; what is missing is one measurement, the pockets page's item-slot
centres in bottom-screen pixels. cycle41's `gp-E8` measured the page arrow at (243, 10) and
nothing else.

**And one navigator caveat that is new**: `0x021c749c` is the field camera's target OUTDOORS,
which is what NAV42 verified, but INSIDE A HOUSE it is the interior camera's and its x is
clamped to the room centre. A snapshot read x exactly 16.000 before and after a walk that
visibly crossed the room. Indoors, aim with the half-and-half slide and the stills; read the
grid with `scratchpad/gameplay44/roomgrid.py`, which prints an interior's kinds and item ids and
is how the two player-house interiors were told apart.

**Aim off the GRID, not off the map picture.** Everything above from 055,460 to 072,200 was
steered by reading the pink marker off a map still, and it cost seven legs to cross a town
and four failed approaches to one door. `port/tools/navigate.py` and `port/tools/goto.py`
(NAV42) plan A* over the acre collision grid from the player's LIVE position at `0x021c749c`
and re-plan from where the player actually ended up; the same shop door that beat four
hand-steered runs took five iterations and ninety seconds. Use them. Two seam notes: `--st`
must be an ABSOLUTE path, because the launcher's cwd is `port/build` and a relative one fails
the snapshot with `GetLastError=3` and silently ends the loop after one iteration; and `--runner`
takes any launcher with `gp43g.py`'s argv, so a per-cycle shim is four lines.

**The two rules this section is worth reading for.** First: **say which TOWN a frame number came
from** -- this line said "which clock arm" until GAMEPLAY44, and that was the wrong half of the
pair. A frozen clock generates a DIFFERENT TOWN, because the generator reads the clock, and it
is the town the arrival tutorial follows: see the GAMEPLAY44 section below. Every gameplay frame
in this project before RTC42 is a frozen-clock frame, and therefore a frozen-clock TOWN, whether
it says so or not, and a snapshot is not transferable between arms either. Second: **the door
slide has to be half-and-half.**
`gp-D9`'s 20-frames-in-100 is about nine map pixels of sideways travel over a 700-frame push --
one icon width -- so it tries one tile; 40-in-80 covers thirty-three and tries them all.
`scratchpad/gameplay43/mkpad.py slide` generates it, in either orientation.


## GAMEPLAY45 -- the pockets page calibrated, a real stylus drag, and two doors that will not open

Receipts are run directories under `scratchpad/gameplay45/runs/`, indexed by
`scratchpad/gameplay45/RECEIPTS.md`; the log sections are `docs/log/cycle41-gameplay.md`
GP45-1..7. The town is the frozen-generated one (villager ids **77/16/127**, town id `0xc66e`),
reproduced here from GAMEPLAY43, SAVE43 and GAMEPLAY44 on a fourth build; the clock arm is
`ACWW_RTC_FREEZE_UNTIL=48000` on every gameplay run.

| frames | what was done | what happened |
|---|---|---|
| 055,400..056,400 | `Y` on the walk-out snapshot, stills every 100 | **the pockets page, measured.** `pockets.py` clusters the page's own artwork and finds exactly the 15 item slots `savetool.py`'s `+0x1bf2, 15x u16` predicts, plus 10 letter slots and the portrait. Item slots: y 123 / 147 / 171, x stride 32, **each row staggered +16** -- 19,51,83,115,147 then 35,67,99,131,163 then 51,83,115,147,179. Letters at x 211/235, y 67..163. The player's body at (151, ~60) [E: `PK1`] |
| 003,000..003,110 | a 14-row stylus stroke from slot 6 to the body | **a real DRAG, not fifteen taps.** One `acww touch: DOWN` at (51,147), fifteen `TP_POINT` publications marching along the path, one `acww touch: up` at (151,60), and the ROM's own `trig` byte firing exactly TWICE -- at the two ends [E: `DRAGTEST`; `mkdrag.py`] |
| 060,130..061,060 | the SAME snapshot, twice, with only the arrival sweep's ORDER different | **east-first ends sixteen tiles north of the player's house; west-first is INSIDE in one iteration, 5.6 s.** The doorway is at the doormat tile's centre, and the player stood at fraction 0.86 of it, so the doorway was to their west all along [E: `HOME-6` vs `IN-1`] |
| 057,000..057,600 | the first version of the `at_door` fix -- tile equality for a notch door | **DEADLOCK, and the finding is worth more than the fix**: the player wedged one tile south of the doormat and three iterations each planned the same one-tile leg and moved ZERO units. The last tile of the approach is sub-tile and only the sideways sweep crosses it [E: `HOUSE-1..6`] |
| 063,450..068,700 | A every 60 x85 at the player's own front door | the arrival is FINISHED: `0x021f3c30` goes **1 -> 0** [E: `NK0`, `peek.py`] |
| 072,750..079,000 | START then A every 100, `ACWW_SAVE` live | **the save**: `checksum stored 0xbddf computed 0xbddf residual 0x0000`, and the ROM's own `func_020a1a40` says *the game would LOAD this bank*. Wallet 0, pockets `fff1 x15` [E: `S2`] |
| 072,750..075,200 | the SAME script with a stop frame in the middle of the write | **a save is not atomic.** 1,985 card requests instead of 4,669, `checksum stored 0xffff computed 0x13aa`, *the game would REJECT this bank*. A timeout or a short `ACWW_STOP_FRAME` during a save writes a file that reads as CORRUPT rather than truncated, and `savetool.py check` is the only thing that tells them apart [E: `S1`] |
| 071,600..072,800 | twelve approaches to Nook's shop door | **not entered.** The navigator parks the player on the doormat (20,54) every time; the arrival never crosses z; 1,000 frames of held north with east pulses moved the player *exactly zero units* [E: `NOOK-1..6`, `NK-1..8`, `NKD`] |
| 060,500..066,400 | `goto.py --to villager-1`, then five input shapes at its doormat | **not entered, and the navigation half is DONE**: eight iterations park the player on (51,62) and keep them there. From that tile the full-duty slide, the same with no A, west-alone/north-alone alternating and east-alone/north-alone alternating all move ZERO units -- while a plain "south then east" walks away freely at 18 frames a tile. Not a wall, not a state freeze, no dialogue box [E: `V1-1..V1-8`, `V1D`, `V1N`, `V1A`, `V1E`, `V1S`] |

**What to carry away.** First, **the drag is no longer the unknown** -- the page's coordinates
are measured and the port delivers a stroke as one contact, which is what GAMEPLAY44 said stood
between this port and its first Bell. Second, **the door arrival stopped walking past buildings**,
by two independent fixes: fire it only on the approach axis (never a diagonal), and order the
doorway sweep from the player's own sub-tile position instead of always sweeping east first.
Third, **the blocker moved rather than shrank**: two of the town's doors park the player
perfectly and then admit nothing, and the leading reading -- labelled a HYPOTHESIS -- is that
they are simply CLOSED at this point in the arrival, because a collision pocket cannot block
north, east and west at once and leave south open. Nothing faulted: 44 runs, no
`acww: unimplemented`, no FAULT, no REFUSAL, and the two non-100 exits were the snapshot/link
refusal being provoked on purpose.

## GAMEPLAY46 -- Nook's shop entered, the drag acted on, and a doormat that was two tiles wrong

Receipts are run directories under `scratchpad/gameplay46/runs/`, indexed by
`scratchpad/gameplay46/RECEIPTS.md`; the log sections are `docs/log/cycle41-gameplay.md`
GP46-1..7. The town is the frozen-generated one (villager ids **77/16/127**, town id `0xc66e`),
reproduced here on a fifth build; the clock arm is `ACWW_RTC_FREEZE_UNTIL=48000` on every run.
**63 runs, 839.2 s, every one `exit 100`**; no `acww: unimplemented`, no FAULT, no REFUSAL. No
port source was changed, and `offgate --check` on the tree the runs were made on is 31/31 EXACT.

| frames | what was done | what happened |
|---|---|---|
| 077,750..078,240 | GAMEPLAY44's own Nook plan, replayed from tile (19,53) | **INSIDE the shop** -- and `ACWW_PLAYER_TRACE=1` names the door: the player crosses the model's doormat (20,54), then (21,54), and enters on **(22,54) -> (22,53)**, two tiles east, where `y` leaves 0x2021 for 0x1afc and 0x1259 [E: `g46-NKDIAG`] |
| -- | `doorprobe.py`, no game run | **the doormat was wrong, not the door.** `navlib`'s notch scan wants a WALKABLE cell inside the footprint; Nook's only such cell is the block's open bottom-left corner (20,53). The real doorway (22,53) reads kind `0x0a` -- a solid front wall the collision lets the player through -- and is on the building's own ANCHOR column [E: `doorprobe.py` on `st/wake77000.st`] |
| 064,700..080,300 | `goto.py --to nook` four ways: old doormat / new doormat, before the save / after it | **the retraction.** Old doormat: outside in six iterations both times. New doormat: **inside in four iterations after the save and five before it.** The save, the wake and the in-game hour have nothing to do with it [E: `PRENOOK-1..6`, `NOOK-1..6`, `NKFIX-1..4`, `NKPRE-1..5`] |
| 078,600..081,400 | A pulses at the counter | the job's dialogue, the wallet oval at **0**, and Nook's instruction `작업복을 터치한 상태로 / 자신의 몸으로 / 가져가서 갈아입어구리` [E: `g46-NKDIAG`, `g46-NK1`; `png/NOOK-counter.png`] |
| 081,400..082,900 | five ways to get the pockets page up with his box on screen | **B closes the box, THEN Y opens the page.** Y with the box up does nothing, and neither does a tap on the arrow the line names -- the box eats the stylus too. The nag is three cycling pages, the third of which names the Y button [E: `g46-PK1`, `PK2`, `PK3`, `PK4`, `PK5`; `png/PK5-pockets.png`] |
| 082,060..082,400 | one tap on the uniform, then one on the body | **the first contact is eaten as the pad-to-stylus mode switch** -- the only change is a pen indicator at the top left -- and the second answers `아무 것도 없어`. cycle40's TAP40 finding, on a second page: every drag here must be the SECOND contact [E: `g46-TAP2`] |
| 082,360..082,620 | the drag, as the job asks: slot 0 (19,123) to the body (151,60) | **the game acts on it.** The uniform leaves slot 0, follows the pen with all fifteen rings empty behind it, and the character HIGHLIGHTS GREEN under it -- then the pen lifts and it snaps back [E: `g46-UNI3`; `png/UNI3-082440.png`, `png/DRAG-in-flight.png`] |
| 082,360..082,800 | the same stroke to a POCKET SLOT instead | **the drop STICKS.** So the refusal is the ROM's own "dropped on the character" handler: not delivery, not a lost release position, not the hit test, and not a prompt on the other screen [E: `g46-SLOTMOVE`; `png/SLOTMOVE-stuck.png`] |
| -- | `walletaddr.py`, no game run | **the live wallet is the u32 at `0x021de3cc`**, anchored by 1024 of 1024 bytes of the written save matching RAM at `0x021dc7a8`. It reads 0, and so does the save and the HUD |
| 077,000..078,700 | the player's house after the save and wake, then row 14 | **still the 4x4 room, still no bed**, and rows 14/15 are the DOORWAY APRON -- walking south into them walks the player out of the house [E: `BEDH-1`, `g46-BED1`] |
| 071,500..072,400 | the bed room, from the post-save snapshot | the bed at (6,9) with the player standing at (7,10) -- **and ZERO tile crossings in 900 frames**: the screen is `시작 준비 중입니다 / 전원을 끄지 말고 그대로 기다려 주십시오`, the save-in-progress screen, and the pad is not the player's there [E: `g46-BED2`; `png/BED-the-bedroom.png`] |
| 077,000..078,500 | `goto.py` at villager-1, then one offline check | still not entered, and the obvious cause is **ruled out**: the notch (51,61) and the tile east of the doormat (52,62) are both kind `0x1e`, exactly the two directions GP45 measured as blocked -- but blocking `0x1e` in the model costs 529 of the town's 3,256 walkable tiles and moves no doormat at all, so it is terrain, not a wall. Cause unknown; nobody has yet looked at what is DRAWN on those cells [E: `V1A-1..5`, `doorprobe.py`, `kind1e.py`] |

**What to carry away.** First, **the doors were never closed** -- GAMEPLAY45's sharpest claim is
withdrawn, and the thing that produced it was a doormat two tiles off the door on the two
buildings whose notch is a corner. Its sub-tile sweep-order heuristic is right and was aiming at
the wrong tile; the order of operations is to correct the doormat and only then break ties with
the sub-tile. Second, **the stylus drag is a working instrument on a live page**: the game picks
the item up, carries it and accepts a drop, with two rules that cost this cycle several runs to
find -- a dialogue box eats the stylus, and the first contact after a pad stretch is a mode
switch. Third, **the blocker is now one refused drop**, with a control on either side of it, so
the next move is the ROM's own handler rather than another attempt at the same stroke.

## Hypotheses

- ~~The 4,000-frame picture hold after leaving the town hall is the opening tutorial's own
  Nintendo-DS illustration, not a port defect.~~ **SETTLED, and it was.** The oracle ran the
  same `walkout.pad` timeline the port ran: the original freezes its lower screen through the
  same windows, twitches on the same two frames (51,600 and 54,000), releases on the same
  frame (54,900) and shows the same grey DS model in the same place at the same size
  [E: `gp-E13`, `gp-E14`; **O**: `scratchpad/oracle/walkout/orig`;
  `docs/log/cycle41-gameplay.md` ORACLE44; S: Pelly's line names `니텐도 DS 본체의 X 버튼`].
- ~~The black top screen inside the town hall (40,500..48,000) is the interior's own look.~~
  **SETTLED.** The original's top screen is black on every frame the walk-out passes,
  40,500..49,500, meanY 0.00 on both producers and `ncc-top` exactly 1.0000; and once the
  player is OUTSIDE the original's top screen carries the sky and its clouds, with the town's
  3D world on the lower screen -- the question ORACLE43 could not reach [H:
  `scratchpad/cycle40/runs/town-S2`, `wo-town`; **O**: `scratchpad/oracle/walkout/orig`; receipt lost with its worktree; repeat the named recipe and retain the stated frames].
- The port's sky is flatter than the original's and its whole top screen brighter outdoors
  (mean luma 114..122 against 89..102; the original's blue darkens toward the top of the
  screen and its clouds flatten toward the horizon). FOR: the per-scanline affine parameters
  ORACLE43 named and SKY41 began [**O**: `scratchpad/oracle/walkout/side-by-side-51000.png`,
  `-55500.png`]. Settled by comparing the two skies again after the next SKY change.
- ~~A long comparison drifts on the CLOCK by construction: at 53,100 the original's HUD reads
  `6/15 AM10:14` and the port's `6/15 AM10:00`, because the port's RTC deliberately does not
  advance.~~ **SETTLED and FIXED the same night (RTC42, `ef890990`).** The port is the ARM7 for
  PXI tag 5 now and the clock is a pure function of the frame count; at frame 53,100 both sides
  read `6/15 AM10:14` [**O**: `scratchpad/rtc42/orig-53100-bot.png`;
  E: `scratchpad/rtc42/port-53100-bot.png`; `../systems/time-and-rtc.md`]. **The consequence for
  this page: every frame of an OFF or town comparison now depends on the clock**, because the
  minute drives `func_020bbb6c`'s day/night blend, so a comparison against a pre-RTC42 run must
  set `ACWW_RTC_FREEZE=1` [E: `docs/log/cycle41-gameplay.md` RTC42].
- A villager can be talked to with scripted input alone. Unsettled: `gp-E16` reached a villager
  and pressed A ten times beside it with no dialogue, which a facing requirement would explain
  [E: `gp-E16`]. Settled by a script that circles the villager with a still every 20 frames.
- ~~Three runs of about twenty ended with exit 1 / 0xFFFFFFFF, no fault line and a log cut
  mid-stream, and none reproduced on a re-run.~~ **SETTLED 2026-09-10 (STAB42, `0bc59cc0`):
  they were external kills.** `acww.exe` cannot exit 1 -- its exit-code table excludes it on
  purpose -- and `taskkill /F` and Python's `kill()`/`terminate()` both leave exactly 1, while
  `Stop-Process -Force` leaves `0xffffffff`. Two other agents ran `taskkill /IM acww.exe` that
  night, and the orchestrator's own restart reproduced the symptom on a pair of runs at a
  recorded time. See `run-stability.md` [E: `scratchpad/stab42/killcode.json`,
  `scratchpad/stab42/INDEX.md`].

## The oracle arm (ORACLE44)

The same recipe runs on the original now. `port/tools/oracle/oracle.py` learned `ACWW_PADSCRIPT`
(`--padscript <file> --padscript-at <frame>`), so one 55,864-frame movie carries the town
recipe up to the snapshot frame and the pad timeline after it -- the seam a port run gets for
free by resuming a savestate, which the emulator has to replay:

    python port/tools/oracle/oracle.py --frames 30000,37500,40500,45000,48000:56000:300 \
      --out scratchpad/oracle/walkout/orig \
      --keys 9 --keys-at 300 --keys-for 10 --keys-every 30 \
      --keys2-enable 1 --keys2 8 --keys2-at 1800 --keys2-release-for 60 --keys2-for 10 --keys2-every 0 \
      --keys3-enable 1 --keys3 1 --keys3-at 2400 --keys3-release-for 60 --keys3-for 10 --keys3-every 600 \
      --touch-enable 1 --touch-x 221 --touch-y 181 --touch-at 6900 --touch-for 10 \
      --touch-every 60 --touch-repeat 2 \
      --touch2-x 221 --touch2-y 181 --touch2-at 24700 --touch2-for 10 --touch2-every 60 --touch2-repeat 2 \
      --padscript <abs>/scratchpad/oracle/walkout/walkout.pad --padscript-at 48000

55,800 frames in 940 s, 31/31 shots, and **no input or touch mismatch on any frame**:
`observer.lua` recomputes the timeline's own two lookups and checks them against the emulator's
pad and stylus every frame, so the reference cannot be captured under a different recipe
[**O**: `scratchpad/oracle/walkout/orig/manifest.json`]. If the run writes nothing and sits at
near-zero CPU, it is the invisible DirectSound dialog, not a hang -- see
`port/tools/oracle/README.md`, "When the reference will not start".

## GAMEPLAY47 -- the uniform is worn, every other door opens, and the blocker is a chore

Receipts are run directories under `scratchpad/gameplay47/runs/`, indexed by
`scratchpad/gameplay47/RECEIPTS.md`; the log sections are `docs/log/cycle41-gameplay.md`
GP47-0..6. The town is the frozen-generated one (villager ids **77/16/127**, town id `0xc66e`),
reproduced here on a **sixth** build; the clock arm is `ACWW_RTC_FREEZE_UNTIL=48000` on every
run. **67 runs, 857.2 s, every one `exit 100`**; no `acww: unimplemented`, no FAULT, no REFUSAL.
No port source was changed, and `offgate --check` on the tree the runs were made on is 31/31
EXACT.

| frames | what was done | what happened |
|---|---|---|
| -- | resume any GAMEPLAY46 snapshot | **none of them load, and the READER was broken too.** BUILD44 grew the savestate header from 19 words to 27 (the exe's SHA-256 joined the link identity) and bumped `STATE_VERSION` to 2, but `port/tools/navsnap.py` still assumed 19 -- so `navigate.py`, `goto.py`, `navlib.py`, `doorprobe.py`, `roomgrid.py` and `townid.py` all died with `IndexError: index out of range` on every snapshot the current build writes. Fixed here; the whole chain was then rebuilt and reproduced GAMEPLAY46's frames [E: GP47-0] |
| 082,360..082,680 | GAMEPLAY46's own wear-drop script, unchanged, with `ACWW_INTERP_WATCH` on pocket slot 0 | **TWO stores, so the drop was ACCEPTED**: slot 0 is cleared to `0xfff1` and refilled with `0x11ac`, while the player's `+0x2408` takes `0x11a8`. **It is a SWAP** -- the item that "snapped back" is the shirt the player was already wearing, and one shirt icon looks like another on a still. GAMEPLAY46's refusal is RETRACTED [E: `g47-UNIW`; `png/UNIW-drop.png`] |
| the same | the watch moved to `0x021debc4` (`+0x2408`) | the ROM's handler, named: one store at `pc 0x02099708` with `r14 = 0x0229e3f5` -- `func_02099704` called from **`func_ov096_0229e3b0 + 0x44`**, ov096's equip dispatcher, MATCHED in `src/matched/`. Its `case 2` is the shirt slot; it returns the old garment iff that one is in the band `0x11a8..0x12a7`, which is the same band the eight villagers' `+0x7d2` shirt ids sit in [E: `g47-WEARW`, `dis47.py`] |
| 088,600..089,300 | the page closed with B/Y, then A pulses **with Up HELD under them** | **Nook confirms it in words**: `그래 그래 / 잘 어울려`, then the job's first task -- `가게 주변 분위기가 / 화사해지면 / 손님들도 기뻐하잖아구리 !` and `끝나면 / 다시 와, 구리`. A pulses ALONE opened nothing (the player faces south); A on the page only names the item under the cursor [E: `g47-TALK2` vs `g47-TALK4`; `png/TALK4.png`] |
| 089,400 | -- | **seven flowers in the pockets** where fourteen slots were empty: `11ac 1500 1506 150b 1512 151d 151d 151d` [E: `prec.py` on `st/talk89400.st`] |
| 091,600..092,500 | with the page up, tap a slot TWICE, then tap (58,60) | **an item is placed in the world.** The second tap opens a box offering `땅에 심기` / `그만두기` over the page, naming `노란 튤립`; taking the first line empties the slot and draws the tulip on the grass [E: `g47-PLANT1`, `g47-PLANT2`; `png/PLANTED.png`] |
| 094,900..095,900 | back to the counter with six flowers still in hand | **the wallet is 0 for a GAME reason, in the game's own words**: `앗 ! / 알고 있겠지만 / 밖에 심는 거야구리 !`. The pay is behind seven placements, the shop menu is behind the pay, and a purchase is behind the menu [E: `g47-JOBBACK`; `png/JOBBACK.png`] |
| 077,000..080,400 | one `goto.py --to <name>` at each remaining door | **all four INSIDE, nothing hand-aimed**: able-sisters in 4 iterations (고순이 among the racks), the gate in 4 (a stone room with two lit lamps, and a 165-request CARD READ of the letter store on entry), the museum in 6 (부엉 in the tiled hall), the town hall in 3. `able-sisters` is the second building GAMEPLAY46's anchor rule moved, so this confirms that fix independently [E: `doors47.py`, `D-*`] |
| 081,300..084,500 | villager-1's door, three ways | **the model is RIGHT and the refusal is not aim.** A on the doormat (51,62) opens the house's own NAMEPLATE box, `곤잘레스네 집`, so the ROM agrees that is the door; 750 frames of held Up with A and **1,200 frames with no A at all** both cross zero tiles, with the player resting at world `z = 124.83` hard against the tile-61 boundary; and the same push one column east -- at the kind-`0x0a` cell that was Nook's real doorway -- walks straight through and twelve tiles north. GAMEPLAY46's "cause unknown, `navlib` may be wrong" is answered: not `navlib` [E: `g47-V1DOOR`, `g47-V1NOA`, `g47-V1X52`; `png/V1-acre.png`, `png/V1-door-zoom.png`] |
| -- | a `goto.py` chain from a snapshot taken with the pockets page up | **six iterations, ZERO tiles.** The page eats the pad exactly as a dialogue box does, and it survives the savestate. One `Y` first, and the next chain was inside Nook's shop in four iterations [E: `g47-NK2` vs `g47-CLOSEP`] |

**What to carry away.** First, **there was no defect**: the wear-drop worked from the first
attempt in GAMEPLAY46, and what stood between this project and knowing it was that "refused" and
"accepted" leave the same picture. Five stroke variants and a control on the input could not
separate them; one store watchpoint on the player record did it in a single run. **When two
outcomes look alike, measure the word the action is supposed to move, not the action.** Second,
**every door in the town model is now open** except villager houses, and villager houses are now
an ORACLE question rather than a navigation one. Third, **the port is no longer what blocks the
first Bell** -- a seven-flower errand is, and the placement mechanic that finishes it is proved.

## GAMEPLAY48 -- the seven flowers are planted, the mayor is met, and the villager's door says why

Receipts are run directories under `scratchpad/gameplay48/runs/`, indexed by
`scratchpad/gameplay48/RECEIPTS.md`; the log sections are `docs/log/cycle41-gameplay.md`
GP48-0..10. The town is the frozen-generated one (villager ids **77/16/127**, town id `0xc66e`),
reproduced here on a **seventh** build; the clock arm is `ACWW_RTC_FREEZE_UNTIL=48000` on every
run. No port source was changed, one tool was (`oracle.py`), and `offgate --check` on the tree
the runs were made on is **31/31 EXACT**. Every run is `exit 100` except the one in the last row.

| frames | what was done | what happened |
|---|---|---|
| 048,000..091,400 | GAMEPLAY47's twenty-step chain, replayed **OPEN LOOP** from its own `receipt.json` files | **it reproduces, tile for tile, on a new build**: `HOME-4` at 57,812, the walk-out at (40,56), the save verifying with worn shirt `0x11ac`, the uniform SWAP `0x11a8 -> 0x11ac`, the seven flowers `1500 1506 150b 1512 151d 151d 151d`. Every `goto.py` leg had already written its plan as a `.pad`, so the navigator never ran. **A cycle should hand the next one its PLANS, not its snapshots** -- snapshots are bound to one link and were worthless a build later [E: GP48-0, `chain48.py`] |
| 091,460..097,620 | plant the seven flowers, **one per run**, with the pocket row as the accept test | **seven for seven.** The pockets go `11ac 1500 ...` -> `11ac fff1 x7` and the flowers are drawn in a cluster on the grass. **The player never moved**: the ROM chooses the ground itself [E: `g48-PLANT1..7`; `png/PLANTED-all.png`] |
| the same | why GAMEPLAY47's six-in-one script planted none | **the `땅에 심기` box is drawn BESIDE the tapped slot and moves with it** -- first line at `slot + (10, -62)`, panel width following the item name. GAMEPLAY47's `(58,60)`, read off a 6x zoom of a slot-1 tap, is ten pixels off for slot 1, a whole panel away by slot 3 and a whole ROW away by slot 5. **An eye on a zoom is not a measurement (M1)** [E: GP48-1, `menubox.py`, by colour] |
| the same | and the second half of it | **the pad-to-stylus mode switch is CONDITIONAL.** It is spent only when the previous input was the PAD; on a page already in stylus mode the "switch" tap opens the box and the "real" tap CLOSES it again. Two taps, not three [E: GP48-2, `g48-PLANT3`] |
| 097,800..101,000 | back to Nook with the pockets empty | **he does not pay.** `잠깐 동안 / 휴식 시간을 좀` and `마을사무소 주변에서 / 산책하고 있을 테니 / 찾아봐구리` -- a break, near the town hall. Wallet still 0 [E: `g48-PAY`; `png/PAY.png`] |
| 102,700..104,850 | follow him there | **the NPC standing on the town hall plaza is 고북 -- Tortimer, the MAYOR**, a character this port had never met. The actor manager holds THREE live actors where every previous cycle saw two; `goto.py --to actor:2` is adjacent in three iterations. `내 이름은 고북이라네 !` [E: `NKW-1..3`, `g48-NKTALK`; `png/NKTALK.png`] |
| 077,060..082,300 | villager-1's door, the whole GAMEPLAY47 timeline as ONE 153-row script | **the refusal reproduces exactly** -- onto the doormat at frame **81,344**, the frame GAMEPLAY47 named, and no crossing after it -- **and the box on screen is the answer**: `이 몸은 밖에 계신다 / 곤잘레스`, "I am OUT. -- Gonzalez". It is the note a villager leaves when he is not home, not a nameplate, and two live villager actors are walking the town on that same snapshot. A GAME rule, not a defect [E: GP48-9; `png/V1-plate.png`] |
| 048,000..082,200 | the same timeline on the ORIGINAL, 82,264 emulated frames | **the oracle cannot be asked this.** At the seam (48,000) the two are the same scene on the same line of Pelly's dialogue; after it they are somewhere else entirely, and the HUD does the arithmetic: at 77,000 the port reads AM10:08 and the original AM10:21 -- exactly the 48,000 frozen frames (13m22s) the port did not spend. **The oracle has no counterpart to `ACWW_RTC_FREEZE_UNTIL`**, and GP44 measured two things that follow from a clock difference at generation -- a different town, and no arrival tutorial hold -- which this run does not separate. Either alone breaks the comparison [E: GP48-8; `png/V1-sbs-seam.png`, `png/V1-sbs-door.png`; `compare.py` mean ncc 0.334] |
| -- | give the oracle any `goto.py` plan | **it refused every one of them, and had since ORACLE44.** The port's parser stops a row at a token beginning with `#`; `oracle.py`'s transcription of it split the whole line and refused the trailing comment every plan carries. Fixed here [E: GP48-6] |
| 108,400..139,001 | idle at the town hall for 31,600 frames | **the only non-`exit 100` run in three cycles**: `acww: unimplemented: a savestate-resumed OSThread procedure returned instead of calling OS_ExitThread`. Reached only ~91,000 frames past a resume; not diagnosed [E: GP48-10, `g48-WAIT2`] |

**What to carry away.** First, **Nook's first task is finished** and the port was never what
blocked it -- what blocked it was a confirm point read off a zoom instead of measured, and a
mode-switch rule that had lost its condition. Second, **read the box the game already opened**:
villager houses cost three cycles of navigation work, and the answer was printed on the door the
whole time. Third, **a recipe is not shared until every instrument in it has a counterpart on
both sides**: the pad phases, the two taps and the pad timeline all do; the clock arm, which is
the one that picks the WORLD, does not, and until it does the oracle cannot follow any chain
past frame 48,000.

## ORACLE45 -- the oracle's clock arm, and the seam becomes a match

Receipts: `scratchpad/oracle45/RECEIPTS.md`; the log sections are `docs/log/cycle41-gameplay.md`
ORACLE45-1..5. **No port source was changed**, so no OFF gate is owed; the two tool changes are
`port/tools/oracle/oracle.py` and `observer.lua`, plus a new fixture
`port/tools/test_oracle_rtc.py` (**120 cases**). Both arms run `ACWW_RTC_FREEZE_UNTIL=48000` on
GAMEPLAY48's own 439-row timeline.

| frames | what was done | what happened |
|---|---|---|
| -- | give the oracle the port's clock | **`--rtc-freeze`, `--rtc-freeze-until`, `--rtc-freeze-from`**, each falling back to the `ACWW_RTC_*` variable of the same name. A shifted `rtcStart` cannot express a freeze, and DeSmuME's Lua has no RTC, so the clock is INJECTED at **the same point the port injects at** -- the packed BCD block at `0x027ffde8` that the ROM's own `RtcCommonCallback` unpacks -- from a `memory.registerwrite` hook, because the emulated ARM7 refreshes that block ~1.8 times a frame [E: ORACLE45-1] |
| 000..003,000 | calibrate the arm | with **no** arm the emulated chip and the port's frame-driven clock are the same clock **to within one second**; with `--rtc-freeze-until 1500` the game's own clock words read 10:00:00 through the freeze and the model exactly after it. Costs 52.8 s against 53.6 s [E: `probe-chip`, `probe-until1500`] |
| 048,000..049,600 | the seam, on both arms | **the same PICTURE, not just the same scene**: mean `ncc` **0.9559**, `ncc-top` exactly **1.0000**, and both HUDs read `6/15 AM10:01` at 53,000 where GAMEPLAY48's read `AM10:08` against `AM10:21`. **GP48-8's "every chain this project owns is un-oracleable" is discharged for the clock** [E: ORACLE45-2, `compare-p45.json`] |
| 049,000..055,400 | where they part | first disagreement at **49,000** (the port is further into the town hall's exit fade), agreement again at 49,600, and at **49,800** the port is outside while the original is still in a black doorway -- ORACLE44's ~200-300-frame walk-out lead, with the clock confound removed. Then **the port holds the arrival tutorial's illustration at 51,000 and 53,000 and the ORIGINAL does not**: ~4,400 frames the original spends walking. No frame shift recovers it afterwards [E: ORACLE45-3, `png/seam.png`, `png/hold.png`] -- **RETRACTED by TUTORIAL45 (`docs/log/cycle41-gameplay.md`, TUT45-2) below: the original is frozen on one tile over the same frames, and the reference is in a different town** |
| 081,344 | villager-1's door | **unanswerable on this timeline.** The port is on the doormat with the OUT note; the original is at a cliff face among fruit trees, 31,000 frames of divergence away. The reason is now ordinary rather than "a different town" -- and the way to ask it is a SHORT timeline anchored near 77,000 [E: ORACLE45-4, `png/pinned.png`] |
| -- | replaying a merged chain script on the PORT | **it is an oracle input, not a port input.** GAMEPLAY48's chain crossed these frames in twenty runs joined by savestates, and one leg is the SAVE: replayed continuously the port saves at ~65,400, returns to the title, and the following A pulses start a NEW GAME [E: ORACLE45-5] |

**What to carry away**, as TUTORIAL45 leaves it. The arm exists, its arithmetic is pinned to the
shipped `rtcclock.c` by 120 cases, and the seam scores 0.9559 -- but that seam is INSIDE the town
hall, and a building's interior is the same in every town, so it never saw the world. The two
claims that rested on the pictures alone are both retracted below. The method rule stands and is
sharper: **anchor a comparison near the question**, and score it somewhere the town is visible.

## TUTORIAL45 -- the hold is the ORIGINAL's, and the arm picks the wrong town

**RETRACTION NOTE:** the title's clock-arm inference and TUT45-3's emulator rows are
retracted as stated; see `docs/log/cycle41-gameplay.md`, O46-2 and O46-4. The
observed tile positions remain historical observations.

Receipts: `scratchpad/tutorial45/RECEIPTS.md`; log sections `docs/log/cycle41-gameplay.md`
TUT45-0..4. **No port source was changed and none is owed**: the port already reproduces this
behaviour. The tool change is a memory arm on the oracle -- `oracle.py --peek ADDR[:WORDS]`
with `--peek-at` / `--peek-every`, written to the ledger by `observer.lua` -- which is the first
instrument in this project that can read the ORIGINAL's RAM. Its OFF control: the same recipe
with five peek specs added reproduces `scratchpad/oracle45/v1-frozen` at mean `ncc` **0.9999**,
14 of 30 frames exact-RGB [E: TUT45-0].

| question | what was measured |
|---|---|
| what ends the hold | **a pad press.** With nothing in the script after the walk-out Down the illustration is still up at frame **62,000**; truncate the chain before its `54800 16 600` Right row and it is still up at 57,000; leave the row in and it is gone by 54,900. Not a timer, not the RTC, not a sound event. SAVE42's move-in word `0x021f3c30` is read ONCE in the whole window, at pc `0x020a12ea` frame 48,003, and never stored [E: TUT45-1, `t45-noinput`, `t45-noright`, `t45-w1`] |
| does the ORIGINAL hold | **yes, 4,500 frames.** `--peek 0x021c749c` says the emulator's player is frozen at world `(335176, 8203, 299750)`, tile (40,36), from 50,300 to 54,800 with Down held and A pulsing, and moves on the first shot after that same Right press. ORACLE45 read a still of a standing player as "walking the town" [E: TUT45-1, TUT45-2] |
| does the PORT hold longer | **no.** Against the reference in the port's OWN town -- ORACLE44's unarmed run, whose pad rows over 49,100..54,800 are identical -- the port scores bottom-screen `ncc` **0.9706** over 50,400..54,600 and the two release together at 54,900 with the model half off-screen on both. Against ORACLE45's armed reference the same port arm scores 0.2204. **Only the reference moved** [E: TUT45-2] |
| why the armed reference disagrees | **PARTLY CORRECTED by ORACLE48 below: the sixteen tiles are NOT the town.** As measured: **it is a different town.** Both leave the town hall at world x `0x51000` exactly; the port's first field tile is (40,**38**) and the armed original's is (40,**22**), and each holds after about fourteen tiles. The rule agrees, the world does not -- a stone plaza with hedges against a river with a fence. **ORACLE48 reproduced the same sixteen tiles with the town id EQUAL, so what this row located is a port/original difference at the building's exit, not the world** [E: O48-4]. `--peek` on the live town record `0x021dc7a8` at frame 48,000 gives villager ids **77,16,127** (port), **66,-,21** (armed emulator) and **107,94,-** (unarmed emulator): the two emulator runs differ in ONE flag, so the arm changes the world it was built to hold still [E: TUT45-3] **RETRACTED as stated: the emulator rows and this inference were withdrawn in `docs/log/cycle41-gameplay.md`, O46-2; the corrected measurements are O46-4.** |
| the 200-300 frame walk-out lead | **inherited, not created at the door.** The port's screen is black at 49,620..49,700 and outside at 49,720; both originals are black at 49,800. GP48-8 already had the port one dialogue beat ahead AT the seam frame the snapshot was taken on. It costs nothing: a hold does not care who entered it first [E: TUT45-4] |

## GAMEPLAY49 -- there is no wage to unblock, and the shop says so to the player's face

Receipts are run directories under `scratchpad/gameplay49/runs/`, indexed by
`scratchpad/gameplay49/RECEIPTS.md`; the log sections are `docs/log/cycle41-gameplay.md`
GP49-0..8. **64 runs, 998.7 s**, every one `exit 100` but the first (`exit 9`, the build
refusal in the first row). No port source was changed and no tool under `port/`. The town is the
frozen-generated one again -- villager ids **77/16/127**, town id `0xc66e` -- reproduced here on
an **eighth** build; every run is `ACWW_RTC_FREEZE_UNTIL=48000`.

| frames | what was done | what happened |
|---|---|---|
| -- | load GAMEPLAY48's snapshots | **all twenty refuse.** `acww state: REFUSING a snapshot from a different build` -- a savestate records the image base, the PE stamp, the entry, the file size, the registry count and the exe's SHA-256, and `port/shim/audio/sseq.c` changed since `0824e95b`. **The deliverable a cycle hands on is the PAD TIMELINE, not the snapshot** [E: GP49-0] |
| 000,000..104,850 | rebuild the whole state from GAMEPLAY47's and GAMEPLAY48's own recorded plans (`chain49.py`, `chain49b.py`) | **eight checkpoints identical**, down to `HOME-4` at 57,812, the walk-out at (40,56), the uniform swap, the seven flowers and `outshop` at (27,67) -- and **the same RAM ADDRESSES**: the break message at `0x021cd760` at frame 101,000 in both cycles, the mayor's introduction at `0x02396162` at 104,850 in both [E: GP49-3, `msgaddr.py`] |
| -- | read the ROM's own part-time-job script | **`bmg.py` had been reading at most the first 4,096 bytes of every archive** -- the wrapper is MULTI-CHUNK -- and returning NOTHING at all for one with a long directory. Nook's whole shop dialogue (94 entries) had never been read; the job script's entries [19]..[54] came back blank. **An archive that "has no more messages" and one that was never decompressed look the same from outside (M1)** [E: GP49-1, `bmg49.py`] |
| -- | so what does the break line actually ask for | **greet every resident, and the MAYOR** -- `주민들에게 인사하고 와구리！` -- with a rider to knock before entering a house. GAMEPLAY48 met the mayor by accident and it is a step of the errand [E: GP49-2, `sp/etc/sequence5_1_` entry 18, in RAM at `0x021cd760`] |
| -- | and what does the job PAY | **nothing into the wallet.** The settlement line deducts the `알바비` from the house loan. `0x021de3cc` staying 0 for four cycles is not a defect and not a missing step: the game never credits it. **The loan is `town record + 0x10abc` = `0x021ed264`, 19,800** -- confirmed against BOTH banks of the save the game itself wrote (`0x10abc`, `0x27eb8`, `0x173fc` apart) [E: GP49-2, entry 52; `findword.py`, `savetool check`] |
| 104,850..105,620 | resume the chain and walk | **five `goto.py` iterations move ZERO tiles**: the mayor's box is still up, and a conversation eats the pad exactly as the pockets page does. Eight B pulses close it (`dlg.py` 0.565 -> 0.001) and the next chain walks [E: GP49-5] |
| 105,620..108,900 | greet a villager | **greeted.** A walking villager outruns a three-leg plan -- five iterations closed 8 tiles to 2 -- and two more at `--legs 2` reached ADJACENT, 0 tiles, with the box up at frame 108,000 and the reply in RAM at `0x02396150` [E: GP49-6; `png/GREET1-box.png`] |
| 109,050..118,300 | go to the shop and try to buy something | **the game refuses, in words, three runs and three tiles running**: `알바생한테는 팔지 않는다구리` -- Nook does not sell to his own part-timer. The archive copy is at `0x021cd20a` and the rendered one at `0x0236c0b0`. **The first purchase is behind the END of the whole job**, five errands after the greeting [E: GP49-7; `png/NKREP-box.png`, frame 111,300] |
| the same | where Nook is during his "break" | **behind his own counter, as always.** `npc slot 0 id 0xd019` is in the shop at frame 116,000 and was in the shop at 89,400, 27,000 frames before the break line; the town-hall plaza has three actors and none of them is him. GAMEPLAY48 waited 34,600 frames for someone who never left [E: GP49-4] |

**What to carry away.** First, **the question "what unblocks the pay" had no answer because there
is no payment** -- and the cheapest place to have found that out was the ROM's own script, which
a reader bug had been truncating for two cycles. Second, **a savestate is bound to its exe**, so
plans, not snapshots, are what a cycle inherits. Third, **when a run does nothing, read the box
the game did open**: every A press in the shop produced a sentence, and the sentence was the
answer.

## GAMEPLAY50 -- the greeting gate closes, and two of the six errands are done

**GAMEPLAY50 answers GAMEPLAY49's open question and moves the job on.** The town reproduced on a
NINTH build from the plans alone (46 segments, `chain50.py`; eight checkpoints identical), and
**141 runs in 1,444.8 s were every one `exit 100`**.

| frames | what was done | what happened |
|---|---|---|
| 109,050..123,000 | greet both villagers in the actor manager, having already greeted the mayor | **Nook still shows the gate line.** The manager holds only TWO villagers and the town record says THREE: **it only ever holds who is OUTDOORS**, so a greeting errand cannot be finished from it [E: GP50-1] |
| 123,000..133,531 | go into the third villager's house | **`내 이름은 트로와！`** -- a full introduction with the one id (`0xe002`) that never appears outdoors. The empty third actor slot and the OUT note GAMEPLAY48 read off a door are the same fact from two sides [E: GP50-3] |
| 133,531..140,753 | back to the counter | **the gate is open**: `이제야 겨우 알바생다워졌어구리` -- the FURNITURE errand, entries [24] and [25]. The accept test in memory is the pocket row: the parcel `0x1563` appears in slot 1 [E: GP50-3] |
| 140,753..142,100 | do what the errand says: TOUCH the parcel on the pockets page | **the page names its own recipient, `곤잘레스님`** -- so nobody has to guess who a delivery is for [E: GP50-4] |
| 146,200..156,400 | find 곤잘레스 and talk | **delivered**: slot 1 goes `0x1563` -> `0x3508`, the thank-you. Talking to the WRONG villager is visibly different -- 마르 answers with the two-choice gift prompt and the pocket row does not move [E: GP50-4] |
| 164,200..166,600 | back to the counter | **errand three: the DIRECT MAIL letter** -- write to 마르, post it at the town hall's postal window, and the letter `0x1020` lands in pocket slot 2 [E: GP50-5, entry 31] |

**What to carry away.** First, **an errand's population is not the actor manager's population**:
three cycles chased two walkers because the manager only shows who is outdoors. Second, **the
ROM tells you the answer if you follow its instruction literally** -- the delivery's recipient is
printed on the pockets page because entry [28] says to touch the parcel. Third, **an archive
entry being in RAM is not evidence it is on screen**: the whole decompressed archive is resident,
and only the RENDERED copy above `0x0230....` discriminates. Fourth, two ways for a scripted walk
to move nothing that both read as `exit 100` with a clean log -- a yellow nameplate box the
white-box detector cannot see, and a door approached from the side its building's wall is on
(stall-playbook cases 61 and 62).

## GAMEPLAY51 -- the part-time job is finished, and the loan is a word that moves

**All six errands are done and the game settles the wages against the house loan.** The town
reproduced on a TENTH build from the plans alone; **260 runs in 2,703.7 s were every one
`exit 100`**, and the cycle changed no port source.

| frames | what was done | what happened |
|---|---|---|
| 166,600..170,900 | do what entry [33] says: touch the letter in the pockets and choose `편지 쓰기` | **the addressee is PICKED, not typed** -- a list of three villagers -- and the body may be left EMPTY. The stylus keyboard, which two cycles expected to need, is not on this path [E: GP51-3] |
| 170,900..183,100 | the town hall's postal window | 펠리: `여기는 우편과 창구입니다`. The send page needs the letter **DRAGGED** into it: a TAP raises `읽기 / 버리기 / 그만두기` and that box then eats the confirm, and confirming with nothing staged gets `어머, 편지 안 부치시나요？`. With it staged: **`예, 잘 받았습니다`** [E: GP51-4] |
| 183,100..187,500 | back to Nook | **[40]**, the success line -- not [39], the ROM's own "you posted it to the wrong person". A **blank letter posts** |
| 187,500..211,700 | the carpet, to 트로와 indoors | both middle errands are DELIVERIES, and the ROM names each recipient on the pockets page. Indoors the game opens an ITEM-GIVING page and `건네기` completes it; he hands a floor back [E: GP51-5] |
| 211,700..234,500 | the watering can, to 마르 outdoors | **no page at all** -- an outdoor villager takes the errand item on the TALK itself. The two deliveries differ because the recipients do |
| 234,500..248,100 | the bulletin board by the town hall | it opens to A **only with no direction pressed**; a blank post is accepted |
| **254,100** | back to Nook -- entry **[52]** | **`0x021ed264` goes 19,800 -> 18,400**, and the box reads `남은 대출금은 18400벨이야구리`. The RAM word and the on-screen number agree [E: GP51-8] |

**What to carry away.** First, **the loan word is confirmed**: five cycles watched `0x021ed264`
sit at 19,800 and this one made it move by exactly the 1,400 the ROM's own line names, so
`town record +0x10abc, u32` is the house loan rather than a coincidence of value. Second,
**three targets want three different input shapes** -- a counter NPC wants the direction HELD, a
villager wants it PULSED, a world object wants it not pressed at all -- and picking the wrong one
looks exactly like the game refusing: `exit 100`, a clean log, a delivered pad, nothing on
screen. Third, **a count is not a measurement**: the pockets page's `Y` toggle needed one press,
then two, after a previous cycle had recorded five, so the tool presses one and checks. Fourth,
**a copied `port/build/` is not your build** -- an `acww.exe` bakes absolute paths to its own
checkout's relocation tables, so a worktree that shares one with a session that is rebuilding
dies at 0.1 s naming the other tree's files (stall-playbook cases 63 and 64).

## GAMEPLAY52 -- the first sale, the first purchase, and a save the game itself would load

**Money is earned and money is spent, in one session, and the session ends through the game's
own save-and-quit.** The town reproduced on an ELEVENTH build from the plans alone -- town
`0xc66e`, villagers 77/16/127, every published checkpoint identical to the word -- and **264
runs in 2,953.6 s were every one `exit 100`**. The cycle changed no port source.

| frames | what was done | what happened |
|---|---|---|
| 256,600..257,578 | `goto.py --to nook` from outside the shop | **INSIDE on the first iteration**, and the arrival's own A pulses -- fired at the doorway, aimed at nothing -- opened `raccoon_.bmg` **[30]**, the BUY prompt, and were answered **[33]** `돈이 부족하셔구리`, the refusal for want of money. GP49-7's alba refusal `sequence5_1_` [11] is not in that snapshot at all: **the shop's refusal to serve its own part-timer was a STATE, and finishing the job lifted it** [E: GP52-1] |
| 257,578..258,800 | talk to Nook at the counter | the menu is `팔고 싶어！ / 카탈로그 볼래 / 오늘의 무값은？ / 일 없어` -- **there is no BUY row in it**; the catalogue is a mail order that arrives by post. The counter shape's own A pulses take row one, so the SELL PAGE opens for free |
| 258,800..259,300 | drag 곤잘레스's gift `0x3508` into the sell tray | the page is **the pockets grid with a second copy of itself stacked 94 px above** -- tray rows y 29/53/77, pockets 123/147/171, both on x 19/51/83/115/147 +16 a row. Fifteen `TP_POINT`s and the ROM's `trig` byte firing exactly twice: a drag, not fifteen taps |
| 259,300..261,000 | `결정`, then take `팔게！` | **[14]** `모두 다 해서 ４７５벨 되겠어구리！`, and **`0x021de3cc` goes 0 -> 475** with the pocket row losing the gift. The on-screen price and the RAM word agree [E: GP52-2] |
| 261,000..263,600 | press A at the shelf | the shop has **EIGHT** sellable cells, not the three a previous cycle recorded: the display row y=11 and the west column x=5. `0x1374` is a fishing rod at **500** -- 25 more than the wallet held -- and `0x150a` is white cosmos seeds at **80** |
| 263,600..264,300 | take `살게！` | **`0x021de3cc` 475 -> 395**, exactly the printed price, and **`0x150a` -- the shelf cell's own item id -- is in the pocket row**. A `SOLD OUT` tag appears where the seeds were [E: GP52-3] |
| 264,300..285,300 | close the conversation, walk away, press START | `저장하고 있습니다`, **4,669 card requests, 190,456 bytes, 0 verify mismatches**, and the title screen. `savetool check`: bank 1 VERIFIES under the ROM's own test, bank 2 is a byte-identical mirror, wallet **395**, loan **18,400** in both [E: GP52-5] |

**What to carry away.** First, **a purchase is made at the SHELF and a sale at the COUNTER**, and
the counter menu is not where buying lives -- reading the four rows of `raccoon_.bmg` [12] before
scripting anything saved the cycle a hunt. Second, **a page that looks new is usually the
canonical grid again**: the sell page re-uses the pockets layout exactly, which is the other half
of "every widget's geometry is its own" -- the method is to sample this still, not to expect a
surprise. Third, **a START press inside a conversation is eaten silently**, and the symptom is a
ten-thousand-frame run that reaches `exit 100` with `store absent`; B pulses alone do not fix it,
because standing adjacent and facing is what lets the next A re-open the box -- walk away. Fourth,
**the loan word now has a third independent witness**: RAM, the game's own on-screen number, and
both banks of a save that the ROM's own test would load.

## ORACLE48 -- a shared town id; the one-acre inference retracted by EXIT48

Receipts: `scratchpad/oracle48/RECEIPTS.md`; log sections `docs/log/cycle41-gameplay.md`
O48-0..5. **No port source was changed and none is owed.** ORACLE47 moved the PORT's
confirmation tap so the port drew the ORIGINAL's town; this is the inverse, which is the
direction every chain in this repo actually needs, because they all live in the port's town
`0xc66e`. The knob is the same one -- the second stylus tap's frame -- and the rule is
ORACLE47's, applied the other way: `town draw index = 1 + (UNTAPPED index at frame tap+89)`.

| the recipe | `--touch2-at` | window | town id at 48,000 | clock at 48,000 |
|---|---|---|---|---|
| port, unchanged | `ACWW_TOUCH2_AT=24700` + `ACWW_RTC_FREEZE_UNTIL=48000` | -- | `0xc66e` | 10:00:00 |
| oracle, no arm | **24,513** | 24,503..24,523, **21 frames** | **`0xc66e`** | 10:13:22 |
| oracle, `--rtc-freeze-until 48000` | **24,315** | 24,314..24,316 | **`0xc66e`** | **10:00:00** |

Both edges of the unarmed window are pinned by a run of their own: `24,502 -> 0xed6d`,
`24,503`/`24,513`/`24,523` -> `0xc66e`, `24,524 -> 0xdc95` [E: O48-1]. The window is seven times
wider than ORACLE47's forward one. **The armed form corrects ORACLE47's "the arm would break
it"**: the arm needs its own tap frame, not abolishing, and with it the emulator carries the
port's clock to the second -- 10:01:06 at 52,000, 10:02:13 at 56,000, from the ledger's
`rtc-probe` rows [E: O48-2].

| question | what was measured |
|---|---|
| the seam, on a shared town id | **48,000..49,600 mean `ncc` 0.9504, `ncc-top` 1.0000**, and frame **49,700 is exact-RGB** -- two fully black doorways. First divergence 49,000, the port further into the town hall's exit fade; 49,800 is `ncc` 0.0000, the port outside and the original still in the black [E: O48-3, 84 shared frames of GP48's `V1-oracle.pad`] |
| past the walk-out | **0.30..0.44**, and a swept global frame shift does not recover it (best -500 at 0.4573 against 0.2604 at 0). The whole 48,000..56,300 window is 0.5168 armed, 0.4805 unarmed [E: O48-3] |
| why, if the town id is shared | **one ACRE at the town hall's door.** The port leaves the building at tile (40,**38**) and the armed original at (40,**22**), with world x identical to the unit (`0x51000`); both then walk thirteen tiles south, hold ~4,700 frames and release on the same scripted press [E: `scratchpad/oracle48/RECEIPTS.md`; log: `docs/log/cycle41-gameplay.md` O48-4]. TUT45-3 measured the same sixteen tiles against an original in a DIFFERENT town, so ~~**the sixteen tiles are not the town**~~ [H: historical conclusion retracted by `docs/log/cycle41-gameplay.md` X48-4]. **Retraction:** both producers return to their own town hall's doormat in different layouts [E: `scratchpad/exit48/RECEIPTS.md`; log: `docs/log/cycle41-gameplay.md` X48-3, X48-4] |
| is a shared town id a shared world | **No shared world was established.** One id, three rosters: `4d 10 7f` (port), `09 80 49` (unarmed inverse), `80 89 49` (armed inverse). The draw index at frame 48,000 is 4,667 / 4,727 / 4,721 against 5,095 un-shifted [E: `scratchpad/oracle48/RECEIPTS.md`; log: `docs/log/cycle41-gameplay.md` O48-4]; ~~so the tap closes +428 to about +57 and cannot close it: one knob, two constraints 11,346 frames apart~~ [H: historical inference superseded by `docs/log/cycle41-gameplay.md` O49-2, O49-5]. **Correction:** the inverse recipe enters the layout burst two draws early; the forward recipe aligns id, map and roster [E: `scratchpad/oracle49/RECEIPTS.md`; log: `docs/log/cycle41-gameplay.md` O49-2, O49-4, O49-5] |
| villager-1's door on the original | **still unanswered, and now for a measured reason.** The port arm reaches the doormat at tile (51,62) at frame 81,344 and shows the OUT note at 82,200; the original, on the same town id and the same clock, is at tile (38,16) -- forty-six tiles away, at a fence line. 54 shared frames 77,000..82,300, mean `ncc` 0.2127 [E: O48-5] |

**Historical conclusion, retracted by EXIT48 and ORACLE49:**
~~Score the SEAM, not the walk: on a shared town the interior agrees at
0.95 and the exterior does not, and the reason is a located, ordinary port/original difference
rather than a different world.~~ [H: retracted by `docs/log/cycle41-gameplay.md` X48-4].
~~**And a shared town id is not a shared map** -- ORACLE46's "the
roster's seed IS the layout's" now has a counterexample, and matching a single draw is not
matching a stream.~~ [H: the counterexample inference is superseded by
`docs/log/cycle41-gameplay.md` O49-1, O49-2 and Corrections to the record above].

**EXIT48 correction:** each producer recorded its own town-hall doormat at frame 38,838,
then replayed that position on exit; the one-acre separation is two different layouts under
one id [E: `scratchpad/exit48/RECEIPTS.md`; log: `docs/log/cycle41-gameplay.md` X48-3, X48-4].
**ORACLE49 correction:** the port draws the id at frame 24,789 and the real map and roster
together at frame 36,135, 11,346 frames later [E: `scratchpad/oracle49/RECEIPTS.md`; log:
`docs/log/cycle41-gameplay.md` O49-1].
The inverse recipe enters that burst two draws early, whereas the forward recipe yields the
same id, 36 acre bytes, buildings and roster; the confirmed map comparison has 1 loose-item
difference in 2,057 words at frame 48,000 [E: `scratchpad/oracle49/RECEIPTS.md`; log:
`docs/log/cycle41-gameplay.md` O49-2, O49-4, O49-5].
At boot, the same-stream control has 4,617 compared words and 0 differences, closing EXIT48's
generator question without a tap [E: `scratchpad/oracle49/RECEIPTS.md`; log:
`docs/log/cycle41-gameplay.md` O49-3].

## GAMEPLAY53 -- the save BOOTS, the loan is repaid at the counter, and the loop closes

**Verified on `4bcb4abf` (2026-09-10), sixteen DIAGNOSTIC runs, no source change, OFF gate 31/31
EXACT** [E: `docs/log/cycle41-gameplay.md` GAMEPLAY53; `scratchpad/gameplay53/RECEIPTS.md`].

**The forty-minute chain is retired.** Every cycle since GAMEPLAY47 replayed ~50 minutes of pad
chain to get a played town back. This one BOOTED the store GAMEPLAY52's save-and-quit wrote --
a fresh launch, no snapshot, `ACWW_SAVE` pointed at a copy of it -- and was standing in the town
at **frame 4,250, inside forty seconds of wall clock**, with the wallet, the loan, all fifteen
pocket slots and the three villagers exactly as the file holds them. A savestate is bound to the
link that wrote it; a STORE is a file and is not, so it crosses a relink and a worktree.

| frame | screen |
|---|---|
| 1,000 | the title |
| 3,500 | inside the player's own house, `시작 준비 중입니다` -- no taxi, no rain, no keyboard |
| 4,250 | outside their own front door, the mailbox, the town |
| 4,500 | the HUD, `6/15 AM10:01` |

**Then the town hall, and a menu row nobody had taken.** `goto.py --to town-hall` was inside in
two iterations and 45 s; the counter shape opened Pelly first try. Her menu has **five** rows on a
town with a loan, not the four GP51-4 recorded, and the second is `대출 상환` -- the loan
repayment `sequence5_1_` [53] sends the player there for. Every row this project had taken before
was row one, taken for free by the A pulses that open the box; **this is the first taken with the
stylus**, two contacts on a measured centre (the first is spent on the pad-to-stylus mode switch).

Before it was asked to change anything, the game read the loan word out loud:
`펠리: ・・・남은 금액은 / 현재 １８４００벨 / 입니다！` -- a fourth independent witness for
`0x021ed264`, and the first that owes nothing to the session that wrote the file.

**The amount widget is a stylus KEYPAD**, and it was measured by colour rather than read off a
zoom: `7 8 9 / 4 5 6 / 1 2 3` at y 103 / 119 / 135, a wide `0` at y 151, `C` beside it,
`그만두기` and `결정` underneath. `결정` is drawn disabled while the field is blank and repaints
green once a digit is in -- a free way to check the taps landed before spending the confirm.
Three taps put **100** in `입금할 돈`; one tap on `결정`:

    펠리: 예, 이제 남은 금액은 / １８３００벨입니다 / 그럼， 입금해 드리겠습니다

    wallet 0x021de3cc  395 -> 295        loan 0x021ed264  18,400 -> 18,300

Both words moved by exactly the number the box printed. The whole errand -- walk in, talk, take
row two, carry three boxes, enter an amount, confirm -- is six runs and under forty seconds.

**And the loop closes.** The session then walked away from the counter (`dlg.py` 0.002 against
0.566, playbook case 66's precondition measured rather than assumed), pressed START, and took the
game's own save-and-quit into a fresh erased store: 4,669 card requests, 744 pages per bank,
190,456 bytes, **0 verify mismatches**, both banks VERIFYING under the ROM's own test and
byte-identical, `+0x10abc` = 18,300 in both. A fresh launch on a copy of THAT store put the player
outside their own front door again with wallet 295 and loan 18,300.

**play -> save -> boot -> play, twice round, in under nine minutes of run time.**

**What to carry away.** First, **a store is the handoff and a snapshot is not** -- the one crosses
builds and the other does not, and that difference is worth forty minutes a cycle. Second, **a
menu's rows are STATE**: four rows recorded two cycles ago became five when the town acquired a
loan, so an inherited menu is a hypothesis and the still is the measurement. Third, **a
miscalibrated detector answers instead of failing** -- `rows51.py` reported two rows for a
five-row menu because it was looking for a pale panel and found the dialogue box; the fix was a
detector keyed to the menu's own exact fill. Fourth, **the tool can be the stall**: seven indoor
runs moved nobody because `goto.py` returns at its arrival test before planning, and its own
stdout said so seven times before anything else was suspected.

## GAMEPLAY54 -- the port can walk indoors, and the shop is priced

Grade **S** (fifty-nine diagnostic runs, all `exit 100`, 337 s in total; the OFF gate 31/31 EXACT
on the same build; `docs/log/cycle41-gameplay.md` GAMEPLAY54,
`scratchpad/gameplay54/RECEIPTS.md`).

For five cycles everything inside a building was aimed by hand, because the navigator refused an
indoor tile and a held direction sometimes moved the player nowhere. **Three separate things were
wrong, and each was enough on its own.**

**The position.** `0x021c749c` is the vector the field camera tracks, and indoors it is not the
player: it is the INTERIOR camera's target, and it is clamped to a window. Under a held Left it
ran 16.346 -> 15.000 and then stopped dead while the player carried on to 12.990; under a held
Right it pinned at 17.000. Two units of camera over five tiles of walking, and a whole TILE wrong
on four of seven snapshots. The live position turned out to be the **player's own actor vector**,
at the very offset the tool already used for villagers -- `*(u32 *)0x021d5684 + 0x5c`, with
`y = 0.125` at ground level, found by diffing two indoor snapshots for a vector that moved and
then asking which STATIC word points at it.

**The grid.** The blocked-kind table was measured outdoors -- sea, buildings, river, out-of-town
-- and *none of those occurs in a room*. Nook's shop is floor `0x1e` inside a `0x15` surround with
`0x1b` for the shelves, the counter and the walls, so under the outdoor table the shelves were a
walkable lane and the tool reported **40 walkable tiles for a room with 23**. Indoors the walkable
set is the room's own floor kind, flood-filled from the player, minus every cell the furniture
layer occupies.

**The ramp.** The walk model charges a first leg 30 extra frames, measured on a leg that turns
from a stale heading over open ground. In a room a plan is one or two tiles and that allowance IS
the error: asked for the single tile between two the player kept landing on, the navigator
oscillated for six iterations, each one-tile leg travelling about 2.2. Indoors the first leg costs
the same as any other.

With those three, `goto.py --to <x,z>` reached **all eight of the shop's merchandise approach
tiles on the exact tile, one run each**, and one A press at each read the price off the game's own
box:

| item | the game's name | price |
|---|---|---|
| `0x114b` | luxury flooring | 2,850 |
| `0x111f` | orange wallpaper | 1,120 |
| `0x1374` | a fishing rod | 500 |
| `0x1378` | a watering can (a special offer) | 500 |
| `0x155e` | medicine (a special offer) | 400 |
| `0x151f` | a message in a bottle | 200 |
| `0x10e7` | moon-surface stationery, four sheets a set | **160** |
| `0x1547` | -- the display is drawn SOLD OUT, and an A press opens no box at all | -- |

Then the cheapest was bought and the session saved: wallet **295 -> 135**, the shelf cell's own id
`0x10e7` in a pocket slot, and the game's own save-and-quit -- taken INSIDE the shop, which no
cycle had tried -- writing a store whose both banks verify under the ROM's own test. A fresh
launch on a copy of it is back in the town in 40 seconds with wallet 135 and the item still there.

**What to carry away.** **When a scripted walk "does nothing", the first control belongs on the
two READERS, not on the walk.** A wrong position word and a wrong walkability table each produce
exactly the picture of an input being refused, and here they produced it while disagreeing with
each other -- a tile the player had already reached read as one they had not, so the next
(correct) hold moved them nowhere and looked like a refusal. The whole diagnosis was two prints
on a snapshot that already existed. And: **a constant measured on one scale is a hypothesis on
another** -- the outdoor ramp, charged indoors, was a whole tile of overshoot.

## ORACLE50 -- a chain built in the SHARED town, and the villager's door opens on both producers

Every chain on this page lives in the PORT's town `0xc66e`, and the original cannot be put in
that town without paying two draws at the layout burst -- which move villager-1's house
(`ORACLE48`, `ORACLE49`). So ORACLE50 built the first chain this repo owns in the town BOTH
producers generate, the forward recipe's `0x8365`, and asked it the door question.

**The recipe.** Port `ACWW_TOUCH2_AT=24908` with `ACWW_RTC_FREEZE_UNTIL=48000`; this tool
`--touch2-at 24700` with NO clock arm. The window was re-taken on this build rather than carried
-- `ACWW_TOUCH2_AT = 24,907..24,909`, three frames wide. At frame 48,000 the two agree on the
town id `0x8365`, on all eight roster slots `6b 5e 84 ff ff ff ff ff`, on the 36 acre bytes, on
all 17 building cells tile for tile, and on 2,056 of the 2,057 words that are the map; the one
that differs is a fallen orange twelve thousand frames of play later.

**The chain, 9,762 frames.** SAVE42's own `P1-out-and-wake.pad` from 48,010 leaves the town
hall and rides the arrival-tutorial hold out; four `goto.py --to villager-1` iterations then walk
36 tiles and press. Merged with `catpad.py` into one 93-row timeline, it replays OPEN LOOP on the
port to the frame, and the emulator runs it from power-on with the pad contract clean for all
58,000 frames.

**What happened, and it is the answer GAMEPLAY48 could not get.** The two producers' tiles are
EQUAL on 77 of the 101 shot frames. Both leave the town hall at (72,38), both walk south to
(72,51), both hold there through the tutorial and are released by the same Right press, both
reach the doormat **(61,69)** -- and **both go inside**. The door's own words are identical:
`0x021f69b8`, the pending outside position EXIT48 named, takes `503808 512 564736` (the doormat
tile) on both, and `0x021f69d0` takes the same scene request with the same destination
`65536 512 118784`. The port fires it at frame 57,310, the original at 57,195.

**And the resident is home.** At frame 57,600 both stills show the same room -- the same green
rug, the same bed, the same chairs, black top screen on both -- with a villager standing in it.
By 58,000 the port's A pulses have opened her greeting, with `사브리나` in the nameplate.
**GAMEPLAY48's `이 몸은 밖에 계신다 / 곤잘레스` -- "I am OUT" -- is therefore a fact about town
`0xc66e` on that timeline, not a property of the port's door.**

**What to carry away.** **Score the BOTTOM screen on an outdoor chain.** The top screen outdoors
is the sky, and the port's sky is flatter and brighter than the original's, so `ncc-top` sits
near zero through the whole outdoor half and drags the two-screen `ncc` with it: across the
4,600-frame tutorial hold the bottom screens score **0.9791** while the combined number reads
0.5640. A differential that reports one number for two screens showing two different KINDS of
thing is reporting the louder one. And: **the first divergence on this chain is at 49,000 and it
is Pelly's dialogue box, one beat ahead on the port** -- the two are back to 0.99 by 49,500 and
byte-identical at 49,700.

## GAMEPLAY55 -- the room has a door now, and two of the four directions are 4.6x slower

Grade **S** (`docs/log/cycle41-gameplay.md` GAMEPLAY55, `scratchpad/gameplay55/RECEIPTS.md`; the
OFF gate 31/31 EXACT with the C change in).

GAMEPLAY54 could walk to any shelf in Nook's shop and could not walk out of it. The navigator's
door rule is a rule about the ITEM layer -- a building is a connected block of footprint filler
with one `0x50xx` id on it -- and an interior has no such cell anywhere, so inside a room the
door list was simply EMPTY and leaving was the one step still driven by a hand-written pad.

**The exit was in the other layer all along.** The room's KIND grid ends in two rows that occur
nowhere else in it: `0x05` at z=14 and `0x68` at z=15, in the one column pair the doorway
occupies. So an exit is a connected component of those two kinds; the tile to stand on is the
middle of the row of FLOOR cells beside it, and the facing is computed from that tile into the
apron. In Nook's shop that is one door -- stand (8,13), facing south, apron (7,14) (7,15) (8,14)
(8,15) -- and the apron cells are deliberately kept OUT of the walkable set, so no path can route
through the doorway to somewhere else in the room and leave the building by accident.

**The arrival is a walk and then a conversation, which is the reverse of a front door.** Walking
into a building needs A pulses held under the direction and a sideways hunt for a sub-tile
doorway; walking OUT needs neither -- but the moment the player reaches the second apron row the
shopkeeper says goodbye, and a dialogue box discards movement input. That box is why the first
attempt looked like a broken collision: the player stood in the doorway for three iterations and
760 frames of held direction and moved zero units, with every run `exit 100` and a clean log. One
A press closes it and the transition fires on that same press.

    f10,815   ACWW_PLAYER_TRACE  tile=8,15                the step onto the 0x68 row
    f10,983   0x021f69d0[0] <- 0x00, +0x04..+0x0f <- (45.000, 0.125, 110.0), +0x10 <- 0x0f000000
    f11,046   0x021f69d0[0] <- 0x3f (stage 6), tile=22,54, and the field grid is 6x6 again

The middle line is worth its own sentence: **the scene request carries the destination POSITION**,
which is EXIT48's "the building exit replays the position recorded on the way in" seen from the
writing side. **From all eight of the shop's merchandise stand tiles, one `goto.py --to exit` run
puts the player back on the doormat.**

**And the instrument that had never been moved was moved.** `ACWW_PLAYER_TRACE` still printed the
camera's tracked point, which GAMEPLAY54 had already shown is a tile wrong in a room; it now
prints the player actor's own vector and keeps the camera word as a second column, so every
outdoor receipt written against the old number stays comparable and the disagreement is visible
on one line. In the trace above the player is on the apron at `tile=8,15` while the camera word
is still pinned at `camtile=8,13`.

**The thing nobody expected.** Holding one direction indoors and counting tile crossings: north
and east cross a tile every **18 frames**, the outdoor number -- and south and west every **84**.
Four to five consecutive crossings each way, the same from a player pinned against a wall and
from one at rest mid-room, and the same probe outdoors is 18 frames a tile for eleven tiles in
the very direction that is slow indoors. The planner now charges a leg its own direction's rate;
**why two of the four are 4.6x slower is not established, and it may be a defect in the port's
own movement rather than a rule of the game.**

**And the model generalises, which is the first time that has been checked.** The town hall is a
second interior -- a different floor kind, a different shape, and a door apron ONE row deep
instead of two -- and the exit rule found its door with no change at all, because an apron is a
connected component of two kinds and not a row count. It also produced the first thing the
indoor grid model gets wrong: the hall has **two** counters, the door drops the player at the
Civic Support one, and the other window's service tile is a kind the "walkable = the room's own
floor kind" rule does not include. The savings row is behind that tile and is still unopened.

**What to carry away.** **A model of a place is only as good as the cell the player is actually
standing on.** Every failure this cycle appeared the first time the player stood somewhere the
model had never had to describe -- the threshold. The walkable set collapsed to one tile, the exit
rule then offered the player's own cell as the tile to stand on with a facing that pointed back
into the room, and each of those produced a run indistinguishable from a refused input. The cheap
control is to print the walkable COUNT beside the plan: a room that was 23 tiles a moment ago and
is 1 now has not become smaller, it has become unreadable.

## Related

- `wiki/experiments/two-tap-town-recipe.md` -- how the run reaches frame 48,000
- `wiki/systems/input-and-touch.md` -- the pad registers, the touch ring and the port's injection
- `docs/kb/hybrid/recipes.md` section 4b -- `ACWW_PADSCRIPT` and `ACWW_STATE_SAVE` slack
- `docs/kb/hybrid/savestate.md` -- what a snapshot carries, and what a resumed run re-reads
- `docs/log/cycle41-gameplay.md` -- the raw record this page is distilled from
- `docs/log/cycle41-gameplay.md` ORACLE44 -- the oracle arm that settled the hold and the black
  top screen (it was folded into that file; there is no separate `oracle44.md`)
- `port/tools/oracle/README.md` -- `--padscript`, and calibrations 3 and 5
- `wiki/systems/villagers.md` -- the spawner, the actor manager and the draw member-pointer
- `save-and-reload.md` -- the SAVE43 chain's other half: the save the game writes, and the reload
- `live-play.md` -- the same build driven by a person instead of a pad script
- `run-stability.md` -- why a run of this length ends in exit 1, and what that is worth
- `docs/log/cycle41-gameplay.md` -- the raw record this page is distilled from (cycle41 and the
  GAMEPLAY42 sections at the end)
- `scratchpad/gameplay42/RECEIPTS.md` -- the GAMEPLAY42 run index and its three snapshots
