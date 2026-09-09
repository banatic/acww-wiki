# Audit: game systems against public knowledge

**Summary.** Thirteen wiki pages were checked against public reverse-engineering and fan
reference. The single most valuable source is the ACWW save-editor corpus (WildEdit-Core and
the `ACWW_Research` wiki), which publishes a **Korean-region** save layout: it independently
reproduces four numbers this repo measured out of the ROM (save copy size `0x173fc`, player
stride `0x249c`, villager stride `0x7ec`, villager array at `+0x9284`) and then supplies a
dozen more the wiki lacks -- the checksum algorithm and its offset, the town-name field, the
wallet and bank fields, the acre and item array bases and their **counts**, and a complete
item-id category map. Fan reference adds a second layer: it agrees exactly with the ROM on the
first day of spring and on three counts the wiki derived from the file tree (150 villagers,
56 fish, 56 bugs), disagrees with the ROM on the other three season boundaries, and supplies the
visitor rota that makes sense of an eleven-entry priority table. Sixteen wiki edits and thirteen
experiments follow; **one open question -- `save-data.md`'s "no checksum has been found" -- is
answered outright**, and two claims are wrong as written.

## Method and the P grade

Every row below cites a **public** source. Public sources are grade **P** and they are NOT
S, E or O: a P citation says "someone outside this project asserts this", nothing more. Two
kinds of P are distinguished in the verdict column:

- **P-code** -- the source is itself code or a datamined table that a reader can run or diff
  (WildEdit-Core, the `ACWW_Research` structure tables). These are strong leads but were
  derived from the retail EUR/USA/JPN/KOR saves, not from this ROM's disassembly.
- **P-fan** -- a fan wiki asserting a game-behaviour number with no visible derivation.

**A P citation never replaces an S/E/O citation on a wiki page.** Where a public number agrees
with a measured one the page keeps the measured citation and may add "(agrees with P)". Where a
public number fills a hole, it becomes an **H with a named experiment**, never a fact.

Verdicts: **AGREES** (public matches a measured claim), **ADDS** (public supplies a number the
page lacks), **DISAGREES** (public contradicts the page), **SILENT** (nothing public found).

### The public sources used

| id | source | what it is |
|---|---|---|
| P1 | <https://github.com/SuperSaiyajinStackZ/ACWW_Research/wiki/Offset_Sizes> "Offsets and Sizes" | per-region save sizes and offsets, incl. KOR |
| P2 | <https://github.com/SuperSaiyajinStackZ/ACWW_Research/wiki/Main-Structure> | save header layout |
| P3 | <https://github.com/SuperSaiyajinStackZ/ACWW_Research/wiki/Player-Structure> | the player record, KOR column |
| P4 | <https://github.com/SuperSaiyajinStackZ/ACWW_Research/wiki/Villager-Structure> | the villager record, KOR column |
| P5 | <https://github.com/Universal-Team/WildEdit/blob/master/core/source/utils/checksum.cpp> | the save checksum, in code |
| P6 | <https://github.com/Universal-Team/WildEdit/blob/master/core/source/Sav.cpp> | player/villager/house/letter bases, the second save copy |
| P7 | <https://github.com/Universal-Team/WildEdit/blob/master/core/source/Town.cpp> | town name, acres, map items, turnip price, buried bits |
| P8 | <https://github.com/Universal-Team/WildEdit/blob/master/core/source/Item.cpp> `Item::itemtype` | the item-id category map |
| P9 | <https://github.com/Universal-Team/WildEdit/blob/master/core/source/Villager.cpp> | villager id and personality bytes |
| P10 | <https://github.com/Universal-Team/WildEdit/blob/master/core/source/Room.cpp> | the interior furniture grid, two layers |
| P11 | <https://github.com/Universal-Team/WildEdit/blob/master/core/source/Player.cpp> | wallet and bank accessors |
| P12 | <https://nookipedia.com/wiki/Villager/Wild_World> | 150 villagers in Wild World |
| P13 | <https://nookipedia.com/wiki/Fish/Wild_World> | 56 fish |
| P14 | <https://nookipedia.com/wiki/Bug/Wild_World> | 56 bugs |
| P15 | <https://animalcrossing.fandom.com/wiki/Acres> / <https://nookipedia.com/wiki/Acre> | town is 16 acres in a 4x4 grid; an acre is 16x16 squares |
| P16 | <https://github.com/Universal-Team/WildEdit> `graphics/acres/` | 131 acre-id images, ids 0..130 |
| P17 | <https://tcrf.net/Animal_Crossing:_Wild_World> | unused `sky/` "weather test" clouds; the TV test-pattern regional change |
| P18 | <https://nookipedia.com/wiki/Species> | 35 villager species across the series |
| P19 | <https://github.com/Universal-Team/ACWW-Web-SaveEditor/blob/main/assets/js/strings/en/items.js> | a named id-to-item database, ~3,260 entries, including every `0x5xxx` building |
| P20 | <https://github.com/Universal-Team/WildEdit/blob/master/arm9/source/screens/acresEditor.cpp> and `townMapEditor.cpp` | the acre grid is 6 wide (cursor steps by 6 over 0..35); the playable acres are indices 7-10, 13-16, 19-22, 25-28; map items are acre-major, 256 per acre |
| P21 | <https://github.com/Universal-Team/ACWW-Web-SaveEditor/blob/main/assets/js/core/player.js> | the editor clamps the wallet at 99,999 and the bank at 999,999,999 |
| P22 | <https://nookipedia.com/wiki/Stalk_Market> and <https://www.thonky.com/acww/stalk-market-guide> | Joan sells Sunday morning ~90-110 Bells; Wild World has two prices a day, Monday to Saturday |
| P23 | <https://nookipedia.com/wiki/Savings> , <https://nookipedia.com/wiki/Bells> | savings interest 0.5% on the 1st, interest capped at 99,999; wallet cap 99,999 |
| P24 | <https://nookipedia.com/wiki/Furniture/Wild_World> | 562 catalogued furniture items plus 14 non-catalogue DLC |
| P25 | <https://nookipedia.com/wiki/Spring> , `/Summer`, `/Autumn`, `/Winter` (intro sections) | season date ranges as fan reference states them |
| P26 | <https://nookipedia.com/wiki/Special_character> "Special visitor schedules -> In Wild World" | the weekly visitor rota and the one-visitor-at-a-time rule |
| P27 | <https://nookipedia.com/wiki/Animal_Crossing:_Wild_World/Characters> "Special characters" / "Villagers" | 32 listed special characters; the 150-villager table with birthdays |
| P28 | <https://nookipedia.com/wiki/Event/Wild_World> and the per-event "Recurrence" tables (`Fireworks_Show`, `Flea_Market`, `Bug-Off`, `Fishing_Tourney`, `Bright_Nights`, `Flower_Fest`, `Acorn_Festival`, `La-Di-Day`, `Yay_Day`, `Countdown`) | the Wild World event calendar as weekday-relative rules |
| P29 | <https://nookipedia.com/wiki/Moving> "In Wild World" | town starts with three villagers, caps at eight, replacement is random |
| P30 | <https://nookipedia.com/wiki/Time_travel> "In Wild World" ; <https://nookipedia.com/wiki/Mr._Resetti> "In Wild World" | dates run to 2099 then wrap to 2000; Resetti reacts to not saving, not to the clock |
| P31 | <https://nookipedia.com/wiki/Nook%27s_Cranny> , `/Nook_'n'_Go`, `/Nookway`, `/Nookington's` ("In Wild World") | the four-stage shop upgrade chain |
| P32 | <https://nookipedia.com/wiki/Weather> "Snow" ; <https://nookipedia.com/wiki/Winter> | snow settles on the ground from about 11 December |

A caution that applies to all of P1-P11: they describe the **retail save image on flash**.
This wiki's addresses are the **working copy in RAM at `0x021dc7a8`**. The two are the same
bytes -- `func_020b5724` copies `0x173fc` bytes between them [S: src/matched/func_020b5724.c]
-- so a save offset `+X` is RAM address `0x021dc7a8 + X`, and that identity is itself worth one
cheap confirmation before anything below is trusted (ACTION A1).

---

## systems/save-data.md

| claim on the page | public source | verdict | action |
|---|---|---|---|
| two save banks of `0x173fc` bytes each in a 256 KB flash | P1 "Save Copy Size / KOR = 0x173FC" | AGREES (P-code) | add "(agrees with P1)"; keep the S citation |
| the second bank is a primary/backup pair -- **open hypothesis** | P6 `Sav::Finish` copies the whole first copy to `savePointer() + 0x173FC` after every write | ADDS | the banks are **adjacent and identical**: bank 1 at `0x00000`, bank 2 at `0x173fc`. Promote the hypothesis to "mirror, written unconditionally"; the experiment is now a diff of two ranges of one file |
| **"The save record carries a checksum, but none has been found"** | P5 `Checksum::Calculate` + `UpdateChecksum` | DISAGREES / ADDS | **settled**. The checksum is a 16-bit sum over the copy read as `u16` words, skipping the checksum word itself, then negated (`-sum`). KOR stores it at byte offset `0x173F8`, word index `0xB9FC`, over `0x173FC/2` words |
| "the validity record sits at `+0x173f8`; `func_0209f180` requires its `+2` byte to be 2" (`town.md`) | P1 "Main Checksumoffset / KOR = 0x173F8" | DISAGREES | `+0x173f8` is the CHECKSUM, not a validity record. The byte `func_0209f180` tests is at `+0x173fa`, the two bytes after it -- a separate flag inside the last four bytes of the copy |
| "byte 0 of the image must be `0x32`" | P2 main structure: `0x0-0x1` is a 16-bit "Gamecode" | ADDS | `0x32` is the low half of the region/game code word, not a magic constant |
| no ACWW-side CRC helper found in `src/matched` | P5 (the algorithm is a plain negated 16-bit sum, not a CRC) | AGREES | the absence was correct: there is no CRC to find. Strike the "no call edge from `MATH_CalcCRC*`" line as evidence of a *missing* finding and record the real algorithm |
| erased flash reads `0xFF`; a zeroed store is a different game | -- | SILENT | unchanged; but note that a zeroed store now has a *predictable* checksum (sum of zeros negated is zero), so an all-zero image is "checksum-valid, gamecode-invalid" |

**Function-level lead.** `func_020b5724` is the bank chooser and `func_0209f180` is the
validity test. If either computes the negated 16-bit sum, that loop is now identifiable on
sight: a word-stride accumulate over `0xb9fe` iterations with one skipped index. Read
`src/matched/func_020b5724.c` and `port/shim/game/newgameprobe.c`'s quotation of
`func_0209f180` and look for it (ACTION A2).

---

## systems/town.md

| claim | public source | verdict | action |
|---|---|---|---|
| save image `0x021dc7a8`, length `0x173fc` | P1 | AGREES | -- |
| acre-map object at save `+0xd304` | P7 `Town::acre`, KOR base `0xD304` | AGREES + ADDS | the object is an array of **36 one-byte acre ids**, index 0..35 -- a 6x6 acre frame |
| "the town is a **96x96 tile grid**" | P7 `Town::item` allows index 0..4095, stride 2, KOR base `0xD328`; P15 an acre is 16x16 squares and the ACWW town is 16 acres in 4x4 | **DISAGREES** | the item layer is **4,096 cells = 64x64 tiles = 4x4 acres**. 96x96 is the extent of the 6x6 acre frame in tiles, not the item grid. Correct the summary |
| item base immediately follows the acres | P7: `0xD304 + 36 = 0xD328` exactly | AGREES | strong internal corroboration that the acre array is exactly 36 bytes |
| -- (the page has no acre geometry) | P20: the acre editor's cursor moves by **6** for up and down over indices 0..35, and the playable acres are indices **7-10, 13-16, 19-22, 25-28** | ADDS | the acre frame is 6x6 and the playable town is the inner 4x4; the outer ring has **no item slots at all**. Map items are stored **acre-major**, 256 tiles per acre |
| -- | P20: buried state is a separate one-bit-per-cell field at save `+0xf328` (KOR) | ADDS | 4,096 bits = 512 bytes immediately after the item layer (`0xd328 + 8192 = 0xf328`, exact). Another arithmetic corroboration of the 4,096 count |
| items are 16-bit ids in a layer beside the acre bytes | P7, P8 | AGREES | -- |
| `0xfff1` is the empty item id | P8 `ID == 0xFFF1 -> ItemType::Empty` | AGREES (P-code) | -- |
| `0x500d` shop, `0x5001..0x5008` villager houses, `0x5014` seen in a generated town | P19 names the whole band: `0x5000` town hall, `0x5001`-`0x5008` **neighbour house 1-8**, `0x500b` gate house, `0x500c` the tailors, `0x500d`-`0x5010` the **four shop tiers**, `0x5011` museum, `0x5012`/`0x5013` the two tents, `0x5014` **the player's house (small)**, `0x5015`-`0x501a` its upgrades, `0x501c` bulletin board, `0x501d` an invisible mailbox, `0x501e` the countdown sign, `0x5020`/`0x5021` two visitor vehicles | **AGREES and names everything** | the eight house ids, the shop and the player's house are all confirmed by name. Adopt the band as an H-graded id table on `town.md` |
| `0x500e`/`0x500f`/`0x5010` are "keys the flythrough camera cycles through before it hits the shop" | P19: they are **Nook 'n' Go, Nookway and Nookington's**; P31: the shop upgrades through exactly those three stages from Nook's Cranny (`0x500d`) | **settled** | the camera was not cycling arbitrary keys -- it was walking the four shop-tier ids in order. Rewrite that sentence on `town.md` and `economy.md` |
| `0x500a` is the house plot the placer converts into a villager house | P19 names `0x500a` "**Sign**" | **DISAGREES -- and this project is probably right** | `port/shim/game/houseplace.c` carries the ROM's own code: it scans for cells equal to `0x500a` and overwrites the chosen ones with `func_0204bbbc(j)`, which yields `0x5001`..`0x5008`. A community name assigned from an item list is weaker than a read of the placer. **Record the disagreement and offer the correction upstream** once the run in A-P1 prints the spot count |
| **H: the town name is a fixed-length UTF-16 field near the validity record** | P7 `Town::name`, KOR: 6 UTF-16 characters at save `+0x0004`; P2 town name follows the gamecode and town id | **DISAGREES on location, settles the shape** | the field is at the **start** of the image, `0x021dc7ac`, 6 UTF-16 units (12 bytes). Promote to a one-run check: read 12 bytes there after the second keyboard |
| **H: `0x86` is an "unset" acre, not a real acre** | P16: the editor ships acre images for ids 0..130 only | ADDS (weak) | `0x86` = 134 is outside every acre id the public corpus knows, which is consistent with a sentinel. Still needs the measured count |
| `func_0207bbb8` runs a "96x96 scan" | P7/P15 imply 64x64 | DISAGREES (probably) | `port/shim/game/houseplace.c` derives the loop bounds from the map object's own `f0c`/`f10` and **already prints them** (`acww houseplace: w .. h ..`). No run has ever recorded that line. Cheapest measurement on this page |
| tiles map to acres as `(x>>4, y>>4)` plus `(x&15, y&15)` | P15 an acre is 16x16 squares | AGREES | `houseplace.c`'s own address arithmetic is the S citation; P15 corroborates |
| the world is drawn as a cylinder, acre stride 32.0 units, tile 2.0 | -- | SILENT | port-only; leave at S+E |
| `0xf030` appears nowhere on the page | P8: `0xF030` is `ItemType::Occupied`, the marker for a cell covered by multi-space furniture | ADDS | this is almost certainly what `func_0204ef74` (the multi-tile placer) writes into the covered cells. Read that function for a `0xf030` literal |

---

## systems/villagers.md

| claim | public source | verdict | action |
|---|---|---|---|
| eight villager records at save `+0x9284`, stride `0x7ec` | P1, P6 (`0x9284 + villager * 0x7EC`, index bounded at 7) | AGREES (P-code, exact) | the strongest single corroboration on the wiki: three independent numbers match |
| the villager and its house are one record | P4: the record holds furniture slots, wallpaper, carpet, shirt, umbrella | AGREES | -- |
| "the villager sub-record is at `+0x7a0`" | P4: personality at `+0x7ae`, id/species at `+0x7af`, ten furniture slots at `+0x78c`, shirt `+0x7d2`, wallpaper `+0x7d4`, carpet `+0x7d5`, umbrella `+0x7da` | ADDS | `+0x7a0` is the start of a small identity block whose contents are now named. Add the six field offsets as H with a save-diff experiment |
| **six personality classes** (`func_0207c818`'s index bounded at 6) | P4: a dedicated one-byte "Personality" field at `+0x7ae`; the six message directories `bo/ta/ge/fu/ko/ha` (`data/villagers.md`) | AGREES | promote **H: the six classes are the six personalities** to near-settled: the record has a personality byte one byte before the id, and the picker bounds its class index at 6. The remaining work is only naming which index is which |
| record `+0x7af` is a "face/table index byte", table `data_020cd884` "bounded at 33 entries" | P9: `+0x7af` is the **villager id** (`0xFF` = slot empty); P12: 150 villagers | **DISAGREES, and the page's own shim proves it** | see below -- this is finding #2 |
| **three** picks observed with values `0x65`, `0x78`, `0x27` in a generated town, out of a loop of eight | P29: "a town starts with **three** villagers" and grows to a maximum of eight; P12: ids run 0..149 | **AGREES, and explains the number** | all three values are legal villager ids, and three is exactly what a new town is supposed to have. The eight-iteration loop filling only three slots is **correct behaviour, not a truncated run** -- promote this from an observation to a claim and stop treating the other five as missing |
| move-in is tied to the calendar; move-out is unread | P29: once eight is reached, a **random** villager packs up; the player may ask them to stay; they leave the next day. A departed villager's plot is refilled **within seven days**. Wild World picks the replacement **at random and does not balance personalities** (later games do) | ADDS | two concrete rules: a seven-day refill timer and *no* personality balancing on replacement. That last point matters -- the six-class picker `func_0207c76c` is the **initial** picker, and a later move-in may not use it. Add as a hypothesis with the day-rollover experiment |
| -- | P29: the selection predicate for who moves out is described publicly only as "a villager who is in-between hobbies", explicitly flagged as needing clarification | ADDS (a gap) | this is a good oracle target: the public corpus does not know the rule, so measuring it here would be a genuinely new result |
| **H: the seventeen species slots are species groups with a per-species cap** | P18: 35 villager species series-wide; the second table in the face chain is bounded at 33 | ADDS | 17 is not a species count for this series. Either the loop is 17 x 2 over 34/35 species, or the second axis is something else. Re-read `func_0207b594`'s loop bounds before decompiling `func_0209bcd4` |
| max eight villagers | P6 (`villager > 7` returns null); P4 | AGREES | -- |

**Finding: the face chain reads the villager id, and the 33-entry bound is on a second table.**
`port/shim/game/villagerface.c` documents the chain exactly: `func_0208150c` returns
`record + 0x7a0`, `func_02003648` reads `[that + 15]` = `record + 0x7af`, and `func_02082500`
indexes `data_020cd884` by that byte times `0x4e`. P9 says `+0x7af` is the villager id, 0..149.
So **`data_020cd884` is a ~150-row villager table with a `0x4e`-byte row**, not a 33-entry
table. The 33-bound belongs to `func_020808d0`'s *second* lookup, `data_020cd4dc[index]`, whose
index is the byte at `row + 0x4c`. Given P18's 35 species, `data_020cd4dc` is plausibly a
per-species byte with ~33 entries. This rewrites two rows of `villagers.md` and one hypothesis
on `data/villagers.md`, and it is checkable **statically**: read `150 * 0x4e = 0x7350` bytes at
`data_020cd884` out of `arm9.bin` and check the row at `+0x4c` never exceeds `0x20` (ACTION A3).

---

## systems/player.md

| claim | public source | verdict | action |
|---|---|---|---|
| four player slots of `0x249c` bytes starting at save `+0x14` | P1, P3, P6 (`0x0014 + player * 0x249C`, bounded at 3) | AGREES (P-code, exact) | -- |
| 64-bit event bitfield at slot `+0x23f8` | P3 lists nothing at `+0x23f8`; nearest named fields are the bank amount at `+0x23e0` and the acorn count at `+0x2421` | ADDS (by exclusion) | the bitfield sits in a 65-byte gap the public corpus has not named. The wiki is **ahead of public knowledge here** -- worth saying so on the page |
| **H: the slot contains pockets, letters and the catalogue as contiguous blocks** | P3, KOR: eight patterns of `0x234` from `+0x0`; ten letters of `0x100` from `+0x11a8`; **fifteen pocket items as `u16` from `+0x1bf2`**; wallet `u32` at `+0x1c10`; bank `u32` at `+0x23e0`; face/hair at `+0x243c`; town id `+0x247e`, town name 6 UTF-16 at `+0x2480`, player id `+0x248c`, player name 6 UTF-16 at `+0x248e`, gender `+0x249a` | **largely settled** | promote to a save-diff experiment with **named** expected offsets. The pockets are 15 slots, not an unknown count. The catalogue is NOT in the public corpus either |
| **H: the player's name is UTF-16 at a fixed offset near the start of the slot** | P3: it is near the **end**, at `+0x248e`, 6 UTF-16 units | DISAGREES on location | correct the hypothesis and keep it as a two-run diff |
| **H: the four slots are the four residents a town may have** | P6 bounds the player index at 3; P3 gives each slot its own player id and a copy of the town name | AGREES | -- |
| the movement intent block at `self+0x134..0x170` | -- | SILENT | port-only, S stands |
| the DS firmware birthday is read | -- | SILENT | -- |

---

## systems/economy.md

This page is the biggest single winner: it says "bells, prices, the turnip market and the
catalogue have not been read out of the ROM yet", and public research supplies addresses for
three of the four.

| claim / hypothesis | public source | verdict | action |
|---|---|---|---|
| **H: Bells are a 32-bit field inside the `0x249c` slot; wallet and bank are two such fields** | P3/P11: wallet `u32` at player `+0x1c10`, bank `u32` at player `+0x23e0` | **settled by P, needs one measurement** | for player 0 those are `0x021de3cc` and `0x021deb9c`. An `ACWW_WATCH` on either during a run that spends money settles it in one run |
| **H: the turnip market is a per-day price recomputed by the day-change routine, with one of the five block copies shifting yesterday's price into history** | P7: the entire publicly-documented turnip state is a **single `u8`** at save `+0x17370`. P22: Wild World has **two prices a day**, morning and afternoon, Monday to Saturday -- twelve slots a week -- and no public source has a Wild World pricing algorithm at all (the pattern models circulated online are from other games in the series) | **ADDS, and refutes half the hypothesis** | one byte cannot be a Bell price and cannot be twelve slots. So the price is **recomputed**, not stored as a table, and the stored byte is at most an index or a seed. **Strike "turnip price" from the five-copy guess.** Watch `0x021f3b18` (= `0x021dc7a8 + 0x17370`) across an `ACWW_RTC_*` rollover and across a midday boundary: two writes a day supports the two-price rule |
| -- | P22: the Sunday seller's price is around 90-110 Bells; P23: savings pay 0.5% on the 1st of the month with the interest capped at 99,999; P21/P23: the wallet caps at 99,999 and the bank at 999,999,999 | ADDS | four numbers `economy.md` currently has none of. All H, all settleable by watching the two 32-bit fields across a month rollover |
| **H: the top nibble of an item id is the category; 3 and 4 are placeable, 5 is town fixture** | P8 `Item::itemtype`, a complete range map | **AGREES in outline, corrects the detail** | see the band summary below |
| the placement gate accepts nibble 3 or 4 | P8: `0x3000`-`0x45d8` and `0x47d8`-`0x4ba0` are furniture, `0x45dc`-`0x47d4` are gyroids | AGREES + names them | nibbles 3 and 4 are **furniture and gyroids** -- exactly the two things a room accepts. Say so on the page |
| an untouched interior refuses all 256 cells | P10 `Room`: furniture is `slot * 2` with a **second layer at `+0x200`**, i.e. two 256-entry `u16` grids, plus carpet at `+0x448`, wallpaper `+0x44a`, song `+0x44c` | AGREES + ADDS | 256 cells is a 16x16 room, and there are **two layers** (floor and on-top). The wiki has only one |
| eight-way `ov003` item classifier over low-byte constants `0x06`-`0xa5` | P8's low band: flowers `<=0x1c`, weeds `0x1d`-`0x24`, trees `0x25`-`0x6d` and `0xc7`-`0xd3`, parched flowers `0x6e`-`0x89`, watered flowers `0x8a`-`0xa5`, patterns `0xa7`-`0xc6`, rocks and money rocks `0xe3`-`0xfb` | **ADDS, and it is the same taxonomy** | the classifier's constant chain and the public low-band boundaries occupy the same numeric space. The `0x8a`-`0xa5` block appears in both. Re-read `func_ov003_02220e20`'s chain against the public bands -- if they line up, the eight flags are named for free |
| bells, catalogue -- unread | P3/P11 give wallet and bank; **no public source documents the catalogue** in any region. The public player layout leaves a `0x481`-byte unnamed block (EUR/USA `+0x1d63`..`+0x21e3`) that is by far the largest gap and the obvious candidate | partly ADDS, partly SILENT | the catalogue is a hole in **both** corpora, so measuring it here would be a new public result. The KOR analogue of that block is roughly player `+0x1f8f`..`+0x23df`, immediately before the bank field -- a bounded region to diff rather than a `0x249c` haystack |
| turnips as a field item | P8: `0x1531`-`0x1541` is `ItemType::Turnip` -- 17 ids | ADDS | a turnip is an inventory id in the `0x1xxx` band, so `/fg/grass/redTurnip` being a field model does not by itself make a turnip a map item |

**The item-id map in one paragraph** (P8, in my own words). The id space is banded, not
nibble-uniform. Band `0x0xxx`-`0x0fff` is ground content the town map places: flowers, weeds,
trees, dried and watered flowers, laid-down patterns, rocks and money rocks. Band `0x1xxx` is
the inventory: paper, wallpaper and carpet, clothes and headwear, **caught creatures, songs,
tools, money bags, turnips, fossils and shells**. Bands `0x3xxx`-`0x4xxx` are furniture and
gyroids, with the low two bits of the id carrying the furniture's **rotation**. Band `0x5xxx`
is buildings. `0xf030`/`0xf031` mark a cell occupied by a multi-space object, and `0xfff1` is
empty. The one arithmetic fact worth carrying to `data/items.md` is in the next section.

---

## systems/rng.md

| claim | public source | verdict | action |
|---|---|---|---|
| three LCGs (SDK `MATH_Rand16/32`, SPL particles, `AOSS_Rand`), constants as listed | NitroSDK is public but the constants are read here from matched sources | SILENT (P adds nothing) | S stands unaided |
| **the gameplay RNG has not been found** | no public source documents an ACWW gameplay RNG, a town seed, or a fish/bug spawn generator | SILENT -- and that is content | say on the page that public reverse-engineering has not found it either, so this is a genuine frontier rather than a gap in this project's reading |
| **H: a town's layout is generated from a seed stored in the save** | P1/P2/P7 name every large block of the KOR save and none is a seed; P7 shows the acre array and the item grid stored **explicitly** | ADDS (against) | the town is stored, not re-derived -- which the page's own summary already says. Downgrade the seed hypothesis: what would be stored is a seed for *future* draws, not for the layout |
| no save checksum in evidence | P5 | DISAGREES | see `save-data.md` above. Remove the checksum paragraph from this page and link `save-data.md` |
| `OS_GetLowEntropyData` may be dead code | -- | SILENT | -- |

---

## systems/time-and-rtc.md

| claim | public source | verdict | action |
|---|---|---|---|
| `RTC_SetDateTime` at `0x0211e7c0` is misnamed and is really `RTC_GetDateTime` | NitroSDK ordering is public; the specific correction is this project's | SILENT | S stands (D12) |
| the day rollover is a catch-up loop replaying every missed day (`func_0207b05c`) | fan sources describe forward time travel as running each missed day (weeds, cockroaches, villagers gone) | AGREES (P-fan) | add "(agrees with P-fan)"; the mechanism citation stays S |
| the save stores the date it was last written at save `+0x4046` | P1/P2/P3 do not name it; `+0x4046` falls inside player 1's slot (`0x14 + 0x249c = 0x24b0` .. `0x494b`), at player-1 offset `+0x1b96` | **flag** | either `func_0207b05c`'s `self` is not the save base, or the offset belongs to a different object. `+0x1b96` sits just before the pocket items at `+0x1bf2`, which is not a plausible place for the save date. **Re-derive what `self` is in `func_0207b05c`** (ACTION A6) |
| **H: `func_0207b05c`'s tampered-clock branch is Resetti or an equivalent scolding** | P30: in Wild World the mole appears when the player **quits without saving**, and says "save the game" rather than "reset"; **no public source describes any reaction to moving the clock**, forward or backward | **DISAGREES -- rename the hypothesis** | the branch is more likely "the delta is not a forward whole-day count, so do not replay days" -- a *skip*, not a scolding. Its destinations `func_0209a654` / `func_0209a77c` remain the thing to read. Note also the public consequences of forward travel that this branch's *normal* arm must produce: weed growth, mail overflow, villagers leaving unannounced, and even a **shop downgrade**, which is Wild World-specific |
| -- | P30: the clock accepts dates to 31 December 2099 then wraps to 1 January 2000 | ADDS | the game's own supported range is exactly the century in which `RTC_ConvertDateToDay`'s `!(year & 3)` leap rule is correct. Add it as a P corroboration of the page's existing parenthesis |
| -- | P22: turnips rot on **any** clock movement, forward or backward | ADDS | a concrete, cheap oracle test for the tampered-clock branch once a save persists: set a turnip id in a pocket slot, move the clock, and watch for the spoiled-turnip band (`0x154a`-`0x1553`) |
| the port pins 2005-06-15 10:00:00 | -- | SILENT | -- |

---

## systems/weather-and-seasons.md

| claim | public source | verdict | action |
|---|---|---|---|
| **spring begins 25 February** (`func_02063bb4`: month 2, `day <= 24` is winter) | P25 Spring: "Spring runs 25 February to 31 May" | **AGREES exactly** | this is the strongest single agreement on the page. 25 February is a distinctive date no one guesses; the S reading and the P-fan reading land on the same day |
| **summer begins 27 May** (month 5, `day <= 26` is spring) | P25: summer begins **1 June** | **DISAGREES by five days** | see the note below |
| **autumn begins 27 August** (month 8, `day <= 26` is summer) | P25: autumn begins **1 September** | **DISAGREES by five days** | same note |
| **winter begins 27 November** (month 11, `day <= 26` is autumn) | P25: winter begins **26 November** | **DISAGREES by one day** | same note |
| four season codes: 3 winter, 0 spring, 1 summer, 2 autumn | P25 orders the four seasons the same way | AGREES on the ordering | -- |
| `func_0204fa8c` maps twelve months onto fourteen indices, splitting **August and September** | P28: **August is the only month with a weekly recurring event** (a fireworks show every Saturday) and the only month excluded from the monthly flea market; September is where the Bug-Off ends and the fishing tourney half of the year resumes; fan reports place Wild World's autumn foliage change in **mid-September** and a mid-August change in weather character | **ADDS a reading** | promote the page's hypothesis with a better story: the split is not "two fireworks windows" but "the month has two behavioural halves". Aug = pre/post the mid-month weather change, Sept = pre/post the mid-month foliage change. The experiment is unchanged: evaluate `func_0204fafc(func_0209df94())` over all 365 dates |
| snow is a whole channel (189) with its own models | P32: snow **settles on the ground from about 11 December** and clears in late February, which is inside a single unbroken winter season code | **ADDS** | the season function has no day test in December, so whatever gates snow accumulation is a **second** date test the wiki has not found. Add it as a hypothesis: look for a `day` comparison against 11 (or a day-of-year threshold) on the winter path |
| the `w`/`s`/`f` texture suffixes are winter/summer/fall with spring unsuffixed | -- | SILENT | the file-tree check on the page is the right one and needs no public help |
| four `/sky/*_bg_ncl.bin` palettes loaded by `func_020baa28` | P17: TCRF records **unused cloud graphics in the `sky/` directory labelled "weather test"** | ADDS | the sky directory holds more than the four the game loads. Worth one line on the page and a census of `/sky/` |
| channel 189 is the snowman | -- | SILENT | -- |
| rain is model nodes inside `obj_taxi`, not a separate asset | -- | SILENT | -- |

**On the four boundary dates.** Three of the four disagree, and they disagree in one direction:
the ROM's boundary is always *earlier* than the fan wiki's, by five, five and one day. The most
economical explanation is that the two are measuring different things -- `func_02063bb4`'s
four-valued code is what the engine branches on, while the fan wiki is describing what a player
*sees* change (grass colour, tree foliage, insect roster), which the game may switch on the 1st
even though the season code flipped on the 27th. That would make `func_0204fa8c`'s fourteen-value
index, not `func_02063bb4`, the map that matches the fan calendar. **The experiment is cheap and
static**: evaluate both functions over all 365 dates from the disassembly and see which one puts
its boundaries on 1 June, 1 September and 26 November (ACTION A-P10). Until then, keep the S
reading and record the fan dates as a disagreement, per STYLE rule 7.

---

## systems/events-and-calendar.md

| claim / hypothesis | public source | verdict | action |
|---|---|---|---|
| **H: the 23 rows at `0x020e1d8c` are the game's full roster of special visitors** | P27 lists **32** special characters for Wild World (33 if the two shop nephews are separate rows, 34 with the acorn-festival persona); this repo's own file census finds **37** `npc_sp` model stems | **DISAGREES** | 23 is neither 32 nor 37. Rewrite the hypothesis: the table is the roster of **stageable scheduled visitors**, not of special characters. Characters who are permanent residents (the shopkeepers, the museum, the town hall pair, the tailors) need no staging row |
| **H: the eleven predicates are eleven scheduling rules in priority order** | P26 states the Wild World rota directly: one scheduled visitor per weekday Monday to Friday; **two** of those weekdays draw a **random** visitor from a pool of seven; **one** weekday is reserved for the tent visitor and that day is settable by talking to the Saturday surveyor; on any day with nothing scheduled a bird flies over at 09:00 or 17:00; plus fixed weekly slots for the Saturday surveyor, the Saturday musician and the Sunday turnip seller | **AGREES and names the rules** | eleven predicates is exactly the right order of magnitude for that rota. Promote the hypothesis and give the instrumentation a target list: expect distinct predicates for "reserved-day visitor", "random-pool visitor", "fixed weekly", "fly-over fallback" and "event lock" |
| **H: `func_02084ad0`, the third gate term, is 'a special NPC is already present'** | P26: "**only one special visitor can appear at a time in Wild World**" | **AGREES -- promote** | the game has an explicit exclusivity rule, and the gate has an explicit no-argument term that must read zero. This is the cheapest promotion on the page |
| the whole schedule is silent while event flag 1 is set | P26 describes a comparable global lock: during the three week-long festivals the town-hall elder stands outside all week and **blocks every other special visitor** | AGREES in kind | the arrival lock is one instance of a general "one blocking presence suppresses the rota" design, which supports reading `func_02084ad0` as the presence test |
| **H: holidays are rows of a date table selected by `func_0204fa8c`'s fourteen-value index** | P28: every Wild World event is a **weekday-relative rule** (nth Saturday, nth Sunday, the Monday of the second week), not a fixed date | **DISAGREES with the shape** | a fourteen-row month table cannot express "third Sunday of January, March, May, November and December; fourth Sunday of February, April and October". Look instead for a routine that computes a weekday-of-month, and expect the event table to be indexed by (month, ordinal, weekday). Drop the `func_0204fa8c` link from this hypothesis |
| the day-change routine `func_02040c90` has five `MI_CpuCopy8` blocks, guessed as weather / shop stock / visitor / turnip price / mail | P7: the turnip price is a **single byte** in the save, so no week of turnip history is stored; P26: the visitor rota forbids repeats **within a week**, which does need a history | ADDS, and redirects one guess | strike "turnip price" from the five-copy guess and add "this week's used-visitor set". A one-byte turnip price cannot be the thing being shifted |
| the 64-bit event bitfield at player `+0x23f8` is the progress record; flag 1 gates every predicate | P3 names no field anywhere near there | ADDS (this project is **ahead** of public knowledge) | say so on the page; also note that under the public layout the same field in the EUR/USA save would fall at player `+0x21fc`, inside a region the public research labels unknown -- a testable cross-region prediction |
| the firmware birthday fields are read | P27 publishes a **birthday for every one of the 150 villagers** | ADDS | that table is a ready-made fixture: set the RTC to a listed villager's birthday, generate a town containing them, and check the day-change path. Do not copy the table -- cite it |
| -- | P30: the in-game clock accepts dates up to 31 December 2099 and then wraps to 1 January 2000 | ADDS | corroborates `time-and-rtc.md`'s note that `RTC_ConvertDateToDay`'s `!(year & 3)` leap test is "adequate inside 2000-2099" -- the game's own range is exactly that century |
| -- | P31: the shop upgrades in four stages | ADDS | matches four consecutive building ids; see the economy section |

---

## systems/dialogue.md

| claim | public source | verdict | action |
|---|---|---|---|
| six personality message directories `bo/ta/ge/fu/ko/ha` selected through the prefix table at `0x020d72a4` | P4: a one-byte personality field in the villager record; P18 | AGREES | the six directories and the six-bounded class index and the personality byte are three independent witnesses to "six personalities" |
| the five-entry talk table, the request/current/sub-state bytes, the fade gate | -- | SILENT | port-and-source only; S stands |
| the port and DeSmuME part at frame 25,500 over one to two frames of stylus latency | -- | SILENT | O stands |
| villager song is chosen per villager | P9: a `song()` accessor exists for KOR at record `+0x7a4` but is **disabled in the editor as unresearched** | ADDS (weak) | a candidate offset for "the villager's K.K. song", inside the same `+0x7a0` identity block. Cheap to include in the save-diff |

---

## data/items.md

| claim | public source | verdict | action |
|---|---|---|---|
| 1,769 furniture assets, file ids `0x0000`-`0x06e8`, one `.arc` + one `.nsbtx` each | P8: furniture ids `0x3000`-`0x45d8` plus `0x47d8`-`0x4ba0` and gyroids `0x45dc`-`0x47d4`, all on a **stride of 4** because the low two bits are rotation | **AGREES, and settles the mapping** | see finding #1 below |
| **H: item ids and furniture ids are different id spaces** | P8 | **DISAGREES / settled** | they are one space: `item_id = 0x3000 + (file_id << 2) + rotation`. Check: `0x3000 + (0x6e8 << 2) = 0x4ba0`, exactly the last furniture id P8 knows |
| `ftr_info/` has 2,048 slots at 8/32/4 bytes; `item_info/` has 1,536 slots at 12/24/4/2 | -- | SILENT | the arithmetic hypothesis stands; but 1,769 real furniture ids fits 2,048 comfortably and P8's `0x1xxx` inventory band is ~1,500 ids wide, which **weakly supports** 1,536 item slots |
| `item_info/series.bin` at 2 bytes per item is a matching-set id | -- | SILENT | -- |
| 68 `wall/wall_%d.nsbtx` files | P19: wallpaper ids `0x1100`-`0x1143` = **68** | **AGREES exactly** | one of the cleanest file-census-to-id-table matches available. Add as a corroboration |
| 68 `carpet/floor_%d.nsbtx` files | P19: carpet ids `0x1144`-`0x11a7` = **100** | **DISAGREES** | 100 carpet ids against 68 carpet textures. Either 32 carpets reuse a texture (patterns? seasonal variants?) or one of the two counts is wrong. Cheap static check: re-count `carpet/` and re-derive the band edge from `Item::itemtype`, whose wallpaper/carpet range stops at `0x1187` where the id database continues to `0x11a7` -- **the two public sources already disagree with each other here** |
| 256 `cloth/%d/cloth%03d.nsbtx` shirt textures | P19: shirt ids `0x11a8`-`0x12af` = **264** | **DISAGREES by 8** | eight shirt ids with no texture file is exactly the shape of the eight player pattern slots being wearable. Static check worth one minute |
| 1,769 furniture assets | P24: **562** catalogued furniture items | not a contradiction | the catalogue counts sellable pieces; the file tree counts every variant, colour and non-catalogue object. Worth one sentence so a reader does not think 1,769 and 562 conflict |
| names come from `script/KOR/string/*.bmg`, not from the tables | -- | SILENT | -- |
| `ftr/tv/prog/tv_program%d.nsbtp` | P17: the TV test pattern differs between NA and PAL builds | ADDS | a named, dated regional difference living in exactly this directory |
| **H: `PItm/Uki0/` is the fishing float** | -- | SILENT | -- |

**Finding #1, in full.** P8's furniture band, read as `(id - 0x3000) >> 2`, is a dense index
`0x000`..`0x6e8` -- the same 1,769 values as the `ftr/` file census on `data/items.md`, and the
same last value. Gyroids are not a separate space: they occupy indices `0x577`..`0x5f5` of the
same run. So an item id in a pocket, a room or a shop converts to a filesystem path by
`(id - 0x3000) >> 2` and then the page's existing `/ftr/<hi>/<mid>/<id>.arc` rule. This is
checkable **without running anything**: the conversion has to land on an existing file for
every id P8 lists (ACTION A4).

---

## data/villagers.md

| claim | public source | verdict | action |
|---|---|---|---|
| **150 villager models, ids 0-149** | P12: "Wild World features 150 villagers in total, the fewest in the series" | **AGREES exactly** | a file-tree census and a fan wiki independently produce 150. Add "(agrees with P12)" |
| 37 special-character model stems under `npc_sp/model/`, one overlay each | -- | SILENT on the count | the overlay-to-stem table is this project's own and has no public counterpart |
| six personality message directories | P4, P18 | AGREES | -- |
| **H: villager id and personality are independent fields in the save record** | P4/P9: personality at `+0x7ae`, id at `+0x7af` -- adjacent, independent bytes | **settled by P** | promote to a one-run check: print both bytes for all eight records |
| **H: the three-letter stems are species or character abbreviations** | P18: 32 species are used only for special characters | ADDS (weak) | the stems are per-character, not per-species -- `rcn/rcc/rcs/rcd` being four raccoons is the reading the count supports |
| `anm/`'s 324 animations are shared across all villagers | -- | SILENT | -- |
| 33-entry table bound (via `systems/villagers.md`) | P12 (150 ids) | DISAGREES | see finding #2 above; `data_020cd884` is the ~150-row villager table |

---

## data/fish-and-bugs.md

| claim | public source | verdict | action |
|---|---|---|---|
| **H: 56 is the real creature count for each family; the extra model slots are variants** | P13 "the total number of fish in Wild World is 56"; P14 "the total number of bugs is 56"; P8: `ItemType::Catchable` spans `0x12b0`-`0x131f` = **112 ids = 56 + 56** | **settled three ways** | 56 encyclopedia pictures per family (S, file census), 56 per family (P-fan), and a 112-id catchable band (P-code). Promote the hypothesis; keep the file census as the S citation |
| 59 fish model slots (0-58), 63 bug model slots (0-62) | P13/P14 | AGREES with the reading that 3 fish and 7 bug models are non-creature | the surplus is 3 and 7; the page's guess that `fish56/57/58` are non-catchable is exactly the size of the fish surplus |
| 56 `m_fish` held models cover ids 0-55 | P13 | AGREES | 56 held models for 56 fish is a one-to-one match -- the strongest evidence yet that `m_fish` is the caught-and-held model |
| bug animation format encodes behaviour class | -- | SILENT | -- |
| `fish_hire` | -- | SILENT | -- |

P19 goes further and splits the catchable band in two: the first 56 ids are the **bugs** and the
second 56 the **fish**, bugs first. That predicts a fixed offset between the item id and this
page's own picture index (0-55) for each family, and between the item id and the model number.
One caught creature, with `ACWW_WATCH` on a pocket slot, settles the entire numbering for both
families at once (ACTION A-P11) -- and would also tell `data/fish-and-bugs.md` which three fish
models and which seven bug models are the non-creature surplus.

---

## Prioritised actions

Ranked by (value to the port or the wiki) / (cost). "Cheap" means no build.

### For the wiki -- corrections that can be made now

1. **A-W1 (strike).** `save-data.md`: the hypothesis "the save record carries a checksum, but
   none has been found" is false. Replace with the algorithm from P5, graded H (public code,
   not yet confirmed against this ROM), and name the experiment: find the negated-16-bit-sum
   loop in `func_020b5724` or `func_0209f180`.
2. **A-W2 (correct).** `town.md` summary: the item grid is 64x64 (4,096 cells), the acre frame
   is 6x6 (36 bytes). Evidence: P7's own bounds and the exact adjacency `0xD304 + 36 = 0xD328`.
   Keep "96x96" only if the measured `w`/`h` from `houseplace.c` say so (A-P1).
3. **A-W3 (correct).** `town.md`: `+0x173f8` is the checksum; the byte `func_0209f180` tests is
   at `+0x173fa`. `+0x0` is a gamecode word, not a magic `0x32`.
4. **A-W4 (correct + promote).** `villagers.md` and `data/villagers.md`: `record + 0x7af` is the
   **villager id**, `+0x7ae` is the **personality**, and `data_020cd884` is a ~150-row table of
   `0x4e`-byte rows; the 33-entry bound belongs to `data_020cd4dc`. Evidence needed: the static
   read in A-P2.
5. **A-W5 (relocate).** `town.md`: the town name is 6 UTF-16 units at save `+0x4`
   (`0x021dc7ac`), not near the validity record. `player.md`: the player name is at slot
   `+0x248e`, not near the slot's start.
6. **A-W6 (promote).** `data/fish-and-bugs.md`: "56 per family" is now supported by three
   independent lines; make it a claim with S (picture census) + P13/P14 + P8 and move the
   surplus-model question into its own hypothesis.
7. **A-W7 (promote).** `data/items.md`: strike "item ids and furniture ids are different id
   spaces"; state the conversion `file_id = (item_id - 0x3000) >> 2` as H pending A-P3.
8. **A-W8 (add).** `economy.md`: wallet at player `+0x1c10`, bank at `+0x23e0`, pockets are 15
   `u16` slots at `+0x1bf2`, the turnip price is a single byte at save `+0x17370`, and a room
   has **two** 256-cell furniture layers. All H, all with a named diff experiment.
9. **A-W9 (add).** `rng.md`: record that public reverse-engineering has not found ACWW's
   gameplay RNG either -- the hole is the field's, not this project's -- and delete the
   checksum paragraph in favour of a link.
10. **A-W10 (flag).** `time-and-rtc.md`: save `+0x4046` lands inside player 1's slot under the
    public layout, which is implausible for "the date the save was written". Re-derive what
    `func_0207b05c`'s `self` points at.
11. **A-W11 (promote).** `villagers.md`: "three picks observed" is not a partial result -- a new
    Wild World town is supposed to start with **three** villagers (P29). Restate it as a claim.
12. **A-W12 (promote).** `events-and-calendar.md`: `func_02084ad0` is the "a special visitor is
    already present" test, because the game has an explicit one-visitor-at-a-time rule (P26).
13. **A-W13 (rewrite).** `events-and-calendar.md`: the 23-row table is the **stageable visitor**
    roster, not the special-character roster (32 public, 37 model stems here). And holidays are
    weekday-relative rules, so `func_0204fa8c`'s month index cannot be the holiday selector --
    drop that link from the hypothesis.
14. **A-W14 (record the disagreement).** `weather-and-seasons.md`: the ROM puts spring at
    25 February, agreeing with public reference **exactly**, and puts the other three boundaries
    one to five days earlier than public reference does. Both go on the page (STYLE rule 7).
15. **A-W15 (rewrite).** `town.md` and `economy.md`: `0x500d`-`0x5010` are the **four shop
    tiers** in upgrade order, not arbitrary camera keys; `0x5014` is the player's own house.
16. **A-W16 (add a disagreement worth exporting).** `town.md`: the public id database calls
    `0x500a` a sign; the ROM's house placer treats it as the plot it converts into a villager
    house. Record ours as the stronger reading.

### For the port -- experiments, cheapest first

- **A-P1 (free, no build).** Re-run nothing: add `ACWW_TRACE_STATE=1` to the next town recipe
  and read the line `acww houseplace: w <w> h <h> spots <n>` that
  `port/shim/game/houseplace.c` already prints. It settles the town grid dimensions, the
  house-plot count (11 observed, 30 slots available), and A-W2 in one line.
- **A-P2 (free, static).** Read `150 * 0x4e = 0x7350` bytes at `data_020cd884` from
  `arm9.bin`, and `0x21` bytes at `data_020cd4dc`. Expected: 150 structured rows, and the byte
  at `row + 0x4c` never above `0x20`. Settles A-W4 and identifies the villager table for
  `data/villagers.md`.
- **A-P3 (free, static).** For every furniture id P8 lists, compute `(id - 0x3000) >> 2` and
  check `extract/adm-kr/files/ftr/<hi>/<mid>/<file_id>.arc` exists. A 100% hit rate settles
  A-W7 and gives the port a real item-id-to-asset path.
- **A-P4 (free, static).** Compute the negated 16-bit sum over the first `0x173fc` bytes of any
  save image the port produces, skipping word `0xb9fc`, and compare against the halfword stored
  there. Also confirm the second copy at `+0x173fc` is byte-identical. Needs `ACWW_SAVE` to
  have persisted once -- which `save-data.md` already lists as its first unrun experiment.
- **A-P5 (one run).** `ACWW_WATCH` on `0x021dc7ac` (town name), `0x021de3cc` (player 0 wallet)
  and `0x021deb9c` (player 0 bank) across the existing town recipe. Three of `economy.md`'s
  and `town.md`'s hypotheses resolve together, and a non-zero wallet before the taxi would also
  settle the taxi-fare question.
- **A-P6 (one run).** Print `record + 0x7ae` and `record + 0x7af` for all eight records after
  generation, beside the values `villpick.c` already logs. Confirms the id/personality split
  and gives the first real villager roster the port has produced.
- **A-P7 (one run, day rollover).** Watch `0x021f3b18` (save `+0x17370`, the turnip byte) and
  the acre array base `0x021e9aac` across an `ACWW_RTC_*` midnight. One write per rollover
  supports `economy.md`'s per-day hypothesis and tells `events-and-calendar.md` whether
  `func_02040c90` touches it.
- **A-P8 (reading, no run).** Read `func_0204ef74` for a `0xf030` literal. If it writes that
  into the cells a multi-tile object covers, the multi-tile placer is fully explained and
  `town.md` gains a second special id.
- **A-P9 (reading, no run).** Compare `func_ov003_02220e20`'s eight-way constant chain against
  P8's low-band boundaries. Any two matching boundaries name the whole classifier.
- **A-P10 (free, static).** Evaluate `func_02063bb4` and `func_0204fa8c` over all 365 dates
  straight from the disassembly and tabulate both. The question is which of the two puts its
  boundaries on 1 June, 1 September and 26 November, because that is the one the fan calendar
  is describing. Settles A-W14 and most of `weather-and-seasons.md`'s open hypotheses at once.
- **A-P11 (one run, needs a caught creature).** `ACWW_WATCH` a pocket slot at player `+0x1bf2`
  while catching one bug and one fish. The catchable band is 112 ids, bugs then fish; a single
  observed id fixes the offset from the model number and the picture index for both families.
- **A-P12 (one run, day rollover).** Instrument the eleven predicates at `0x020e1d08` across
  seven simulated days and match what fires against the public rota: one scheduled visitor per
  weekday, two random-pool days, one reserved day, a fly-over on the remaining days, and fixed
  Saturday and Sunday slots. Any predicate that fires on the same weekday every week is one of
  the fixed slots and is identified immediately.
- **A-P13 (reading, no run).** Read `func_02040c90`'s five block copies and test them against
  the revised guess: weather, shop stock, mail, and **this week's used-visitor set** (the rota
  forbids a repeat within a week, so something must remember it). Not the turnip price.

### Dead ends, so nobody repeats them

- **ACSE (`github.com/Cuyler36/ACSE`) has no Wild World support.** Its resource tables cover the
  GameCube titles and City Folk only. It is the first hit for "Animal Crossing save editor" and
  it is the wrong tree for this game.
- **The `ACWW_Research` wiki has no town or acre page.** Its structure pages stop at the main
  header, the player, the villager, letters and patterns. Everything about acres, map items,
  buried state and the turnip byte lives in WildEdit's `core/` and the web editor's `js/core/`.
- **TCRF, Nookipedia, GameFAQs and Fandom refuse automated fetches** (403 or JavaScript-only).
  Nookipedia answers a browser user agent; the Cloudflare-fronted forums do not.
- **There is no public Wild World turnip algorithm, no public gameplay RNG, and no public
  catalogue offset.** Three of `economy.md`'s and `rng.md`'s holes are the field's holes, and
  measuring any of them here would be a new result rather than a catch-up.

### Deliberately not done

- No fan-wiki number was copied onto a systems or data page. Every P above is proposed as an
  H with an experiment, or as a corroboration beside an existing S/E/O citation.
- No claim here upgrades the port's own observations. Where the wiki is **ahead** of public
  knowledge -- the event bitfield at player `+0x23f8`, the special-NPC table, the talk machine,
  the season jump table, the day/night blend -- that is stated as such rather than hedged.

## Related

- `../systems/save-data.md`, `../systems/town.md`, `../systems/villagers.md`,
  `../systems/economy.md`, `../data/items.md`, `../data/fish-and-bugs.md` -- the pages with
  actions against them.
- `../README.md` -- the evidence-grade rules this page works under.
</content>
</invoke>
