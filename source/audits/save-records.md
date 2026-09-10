# Audit: the save-record interior against the public reversing corpus

**Summary.** `wiki/audits/game-systems.md` established that the public save-editor corpus
publishes a **Korean-region** ACWW save layout and that four of its numbers match this repo's
own readings. This audit goes one level down: every record type inside the 0x173fc-byte bank,
field by field, with the Korean offset, the public source, and -- where the repo can settle it
-- a citation from a matched function. The headline is that **the ROM itself publishes the
bank's top-level map**: `func_0209ef7c` walks the whole image and hands twenty-nine
sub-objects to their own initialisers at literal offsets, so the bank's structure is an
**S**-grade reading, not a P-grade import. Twelve public offsets are confirmed exactly against
matched code, four public numbers are corrected, and five fields nobody has published are
named. `port/tools/savetool.py` grew a villager and player dump, and the fixture that proves
it is a synthetic bank whose expected values are written out by hand.

## Method, and the S+P grade

Grades are `README.md`'s. **P** is a public assertion and never replaces S/E/O. A row graded
**S+P** is one where a public offset and a matched function in `src/matched/` say the same
thing -- the strongest kind of row on this page, because the two derivations are independent:
the editors read retail save images, the matched sources are the ROM's own code.

The bridge between the two is one identity: `func_020b5724` copies **0x173fc** bytes between
the flash bank and the fixed working address **0x021dc7a8** [S: `src/matched/func_020b5724.c`],
so **save offset `+X` is RAM address `0x021dc7a8 + X`** and a matched function that dereferences
a literal `0x021e____` address is naming a save offset. That identity is used on every S row
below and is itself worth one confirming run (see A-S1).

### Public sources

| id | source | what it is |
|---|---|---|
| Q1 | <https://github.com/SuperSaiyajinStackZ/ACWW_Research/wiki/Offset_Sizes> | per-region sizes and base offsets, KOR column |
| Q2 | <https://github.com/SuperSaiyajinStackZ/ACWW_Research/wiki/Main-Structure> | bank header, player and villager arrays |
| Q3 | <https://github.com/SuperSaiyajinStackZ/ACWW_Research/wiki/Player-Structure> | the player record, KOR column |
| Q4 | <https://github.com/SuperSaiyajinStackZ/ACWW_Research/wiki/Villager-Structure> | the villager record, KOR column |
| Q5 | <https://github.com/SuperSaiyajinStackZ/ACWW_Research/wiki/Pattern-Structure> | the pattern record, KOR column |
| Q6 | <https://github.com/SuperSaiyajinStackZ/ACWW_Research/wiki/Letter-Structure> | the letter record, paper-id and flag tables |
| Q7 | <https://github.com/SuperSaiyajinStackZ/ACWW_Research/wiki/Letter-Storage-Structure> | the out-of-bank letter store |
| Q8 | <https://github.com/Universal-Team/WildEdit/blob/master/core/source/Sav.cpp> | `playerPointer`/`villagerPointer`/house/letterstorage bases |
| Q9 | <https://github.com/Universal-Team/WildEdit/blob/master/core/source/Player.cpp> | wallet, bank, names, pockets, patterns, letters, dresser |
| Q10 | <https://github.com/Universal-Team/WildEdit/blob/master/core/source/Villager.cpp> | id, personality, song, furniture, shirt, wallpaper, carpet, umbrella |
| Q11 | <https://github.com/Universal-Team/WildEdit/blob/master/core/source/Town.cpp> | acres, map items, buried bits, turnip, town flag, lost-and-found, recycler |
| Q12 | <https://github.com/Universal-Team/WildEdit/blob/master/core/source/Item.cpp> and `core/include/utils/itemUtils.hpp` | the item-id band map and the `ItemType` enum |
| Q13 | <https://github.com/Universal-Team/WildEdit/blob/master/core/source/utils/checksum.cpp> | the negated 16-bit word sum and the KOR checksum offset |
| Q14 | <https://github.com/Universal-Team/WildEdit/blob/master/core/source/utils/saveUtils.cpp> | accepted image sizes, the gamecode table, `SavCopyOffsets` |
| Q15 | <https://github.com/Universal-Team/ACWW-Web-SaveEditor/blob/main/assets/js/core/sav.js> | the same four regions as a JS table |
| Q16 | <https://github.com/Universal-Team/ACWW-Web-SaveEditor/blob/main/assets/js/core/room.js> | the two-layer 256-cell room grid, carpet/wallpaper/song |
| Q17 | <https://github.com/Universal-Team/ACWW-Web-SaveEditor/blob/main/assets/js/core/house.js> | house debts, song list, house size |
| Q18 | <https://github.com/Universal-Team/ACWW-Web-SaveEditor/blob/main/assets/js/core/shop.js> | the Able Sisters pattern store, KOR `0x10AD0` |
| Q19 | <https://github.com/Universal-Team/ACWW-Web-SaveEditor/blob/main/assets/js/core/pattern.js> | the 4-bit 32x32 image and the palette nibble |
| Q20 | <https://github.com/Universal-Team/ACWW-Web-SaveEditor/blob/main/assets/js/strings/en/items.js> | a named id-to-item database |

**Two dead ends, recorded so nobody re-walks them.** `Cuyler36/ACSE` has no readable Wild World
offset table -- its `SaveType.WildWorld` branches exist but the constants live in a class the
public web fetch cannot reach, and `game-systems.md` already found its resource tables are
GameCube/City Folk only. And a Japanese- and Korean-language search for DS save documentation
(`おいでよ どうぶつの森 セーブデータ 解析 オフセット`, `놀러오세요 동물의 숲 세이브 구조`)
returned no technical page at all: **every Korean-region number in the public corpus traces
back to the one Universal-Team codebase.** Action-Replay code lists exist but publish live RAM
addresses with no published mapping to file offsets. So an S confirmation here is not a
formality -- it is the second independent witness the corpus does not otherwise have.

---

## 1. The bank's top-level map -- the ROM publishes it

`func_0209ef7c(self)` is the bank's member-initialiser chain: it takes the save base and calls
twenty-nine sub-object initialisers at literal offsets, plus a four-iteration loop over
`func_0209ef10(self, i)` [S: `src/matched/func_0209ef7c.c`]. Sorting those offsets gives each
sub-object's **extent by adjacency**, and the extents are then confirmed by what each
initialiser actually writes. This is the single most valuable artefact on the page: the public
corpus has no equivalent, because a save editor sees only the fields it chose to edit.

| offset | initialiser | extent | what the initialiser does | public name |
|---|---|---|---|---|
| `+0x00002` | `func_020642e0` | 0x12 | zeroes a `u16` at +0 and 12 bytes at +2 | town id, town name (Q2, Q11) |
| `+0x00014` | `func_02098788` | 0x9270 | loops `i < 4`, stride `0x249c` | 4 player records (Q1, Q8) |
| `+0x09284` | `func_0207cf80` | 0x4080 | struct is `arr[8]` of `0x7ec` then a 0x11a-byte tail | 8 villager records (Q1, Q8) |
| `+0x0d304` | `func_0204ea40` | 0x2226 | see section 4 | acres, map items, buried bits (Q11) |
| `+0x0f52a` | `func_020871b8` | 0x1 | one byte set to 0 | -- |
| `+0x0f52b` | `func_02087140` | 0x1 | clears four bitfields of one byte (0x01/0x0e/0x70/0x80) | -- |
| `+0x0f52c` | `func_0206108c` | 0x2744 | reads `OS_GetOwnerInfo`; a 9-byte list and a packed flag word | house (Q8) **+ Able Sisters patterns (Q18)** |
| `+0x11c70` | `func_02090174` | 0x950 | memsets exactly `0x950`, then one letter at +0 | -- |
| `+0x125c0` | `func_020781bc` | 0x3394 | zeroes a byte at +0xb7e and a `u16` at +0xb7c | **nothing public** |
| `+0x15954` | `func_02097fa4` | 0xa08 | 10 letters at `i << 8`, then 4 bytes and a `u16` | **nothing public** |
| `+0x1635c` | `func_020b19b4` | 0x774 | -- | its last `0x2d0` is the dresser (Q9) |
| `+0x16ad0` | `func_02088250` | 0x474 | -- | its last `0x234` is the town flag (Q11) |
| `+0x16f44` | `func_02097f00` | 0x108 | -- | -- |
| `+0x1704c` | `func_02090018` | 0x168 | -- | -- |
| `+0x171b4` | `func_020afbcc` | 0x64 | -- | -- |
| `+0x17218` | `func_020411f4` | 0x3c | -- | -- |
| `+0x17254` | `func_0204cdfc` | 0x6c | -- | -- |
| `+0x172c0` | `func_0203a658` | 0x1e | writes `0xfff1` into 15 `u16` slots | lost and found (Q11) |
| `+0x172de` | `func_0203a4ec` | 0x1e | writes `0xfff1` into 15 `u16` slots | recycling bin (Q11) |
| `+0x172fc` | `func_02086874` | 0x48 | two 16-byte character references, `0xfff1` at +0x3e | -- |
| `+0x17344` | `func_02087234` | 0x20 | `0xfff1` into the `u16` at +0x1e | -- |
| `+0x17364` | `func_02087830` | 0x1a | eight bytes as `1,1,0,0,1,1,0,0`, `0xff` at +0x18 | contains the turnip byte (Q11) |
| `+0x1737e` | `func_020c17f0` | 0xa | tail call | -- |
| `+0x17388` | `func_020ae3bc` | 0x14 | tail call | -- |
| `+0x1739c` | `func_020aea20` | 0x12 | -- | -- |
| `+0x173ae` | `func_020b0678` | 0x1a | -- | -- |
| `+0x173c8` | `func_0205bf90` | 0x15 | writes three bytes from a date/clock helper, then 0 | -- |
| `+0x173dd` | `func_0209fad4` | 0x5 | four bytes as `1,1,0,0` | -- |
| `+0x173e2` | `func_020882f0` | 0x12 | -- | -- |
| `+0x173f4` | -- | 0x4 | a 32-bit flag word; see section 2 | **nothing public** |
| `+0x173f8` | -- | 0x4 | checksum `u16`, state byte, pad | checksum (Q1, Q13) |

Three of those extents close exactly, and the arithmetic is the evidence:

- `0x14 + 4 * 0x249c = 0x9284` -- the player array ends precisely where the villager array
  begins [S+P: `src/matched/func_02098788.c` loops `i < 4` at stride `0x249c`; Q1/Q8 give base
  `0x14` and size `0x249C`]. This also settles Korea's odd base: every other region starts its
  player array at `+0xC`, and Korea at `+0x14` (Q1) -- the matched sources spell the Korean
  player-array address as the literal `0x021dc7bc`, which is `0x021dc7a8 + 0x14`
  [S: `src/matched/func_0209847c.c`, `func_02098420.c`, `func_020a13e8.c` and eight others].
- `0xf52c + 0x15a4 + 8 * 0x234 = 0x11c70` -- the house object's extent is exactly the public
  house content (`0x1590` debts, `0x1594` song list, `0x15a0` house size, Q17) **followed by
  the eight Able Sisters pattern slots**, whose public base `0x10ad0` (Q18) is `0xf52c + 0x15a4`
  to the byte. Two public sources that never mention each other are adjacent members of one
  ROM object [S: `src/matched/func_0209ef7c.c`; P: Q17, Q18].
- `0x16800 + 4 * 0xb4 = 0x16ad0` -- the four players' dressers (90 `u16` slots each, Q9) end
  exactly where `func_02088250`'s object begins, so they are the tail of `func_020b19b4`'s
  object [S: `src/matched/func_0209ef7c.c`; P: Q9].

**The biggest hole in the bank is `+0x125c0`, 0x3394 bytes, and no public source names one
byte of it.** It is over three times the size of any other unnamed object and is the obvious
home for the catalogue and the museum donation record -- the two things `economy.md` and the
public corpus both lack [H: settled by watching that range across one museum donation and one
catalogued purchase].

---

## 2. The bank header and trailer

| field | KOR offset | other regions | size/type | public | repo check | grade |
|---|---|---|---|---|---|---|
| gamecode | `+0x0000` | same offset, value differs: EUR `0xC5`, USA `0x8A`, JPN and KOR `0x32` (Q14) | `u16` | Q2, Q14 | `func_0209f180` requires `ptr[0] == 0x32` before it will call the validity test | **S+P** |
| town id | `+0x0002` | same (Q2) | `u16` | Q2, Q11 | `func_020642e0` zeroes the `u16` at +0 of the object `func_0209ef7c` installs at `+0x02` | **S+P** |
| town name | `+0x0004` | EUR/USA 8 `WWChar`, JPN 6 `WWChar`, KOR 6 `char16_t` (Q2) | 12 bytes UCS-2 | Q2, Q11 | the same `func_020642e0` zeroes 12 bytes at +2 of that object | **S+P** |
| unknown | `+0x0010` | KOR only (Q2 calls it "Unknown 1", 4 bytes) | 4 bytes | Q2 | the gap between the header object (ends `+0x14`) and the player array | S (by exclusion) |
| **global flag word** | `+0x173f4` | not published for any region | `u32`, 32 bits | **none** | `func_0209f128(save, bit)` sets and `func_0209f150(save, bit)` tests `((u32*)(save + 0x173f4))[bit >> 5]`, and **both refuse any word index >= 1**, so the field is exactly one word | **S, new** |
| checksum | `+0x173f8` | EUR/USA `0x15FDC`, JPN `0x12220` (Q1) | `u16` | Q1, Q13 | `func_0209f180` passes `ptr + 0x173f8` to the validity test | **S+P** |
| write-state byte | `+0x173fa` | not published | `u8` | **none** | `func_0209fb54` writes 28 and `func_0209fb4c` writes 2 to `[+2]` of the object at `0x021f3ba0` = `0x021dc7a8 + 0x173f8` | **S, new** |

**The 32-bit flag word at `+0x173f4` is a new result.** Six bit numbers appear at call sites in
matched code -- 7, 0xd, 0x11, 0x12, 0x13, 0x14 [S: `src/matched/func_020af648.c`,
`func_020af658.c`, `func_02060cbc.c`, `func_02060f5c.c`, `func_020865d8.c`,
`func_020881c4.c`, `func_0209fe40.c`, `func_0209fea4.c`, `func_020a4454.c`] -- so the game
keeps at least six town-wide progress flags in the last eight bytes of the bank. No public
editor exposes them, and the word sits inside the checksummed range.

**The trailing four bytes are a small structure, not just a checksum.** `func_0209f180` hands
`save + 0x173f8` to `func_0209fb3c`, which reads `[+2]` and demands the value **2**; the same
byte is written to **28** by `func_0209fb54` and back to **2** by `func_0209fb4c`, and the save
state machine calls those two around the copy: 28 is set at the start of the write and 2 at the
end [S: `src/matched/func_020a03e0.c` states `a+1` and `a+4`]. So `+0x173fa` is a
**write-in-progress marker**: an interrupted save leaves 28 and the bank is rejected at boot
[S: `src/matched/func_0209f180.c`, `func_0209fb3c.c`, `func_0209fb28.c`, `func_020a03e0.c`].
This corrects `town.md`'s "the validity record sits at `+0x173f8`" and `game-systems.md`'s
narrower correction alike: `+0x173f8` is the checksum **and** the first member of a four-byte
trailer whose third byte is the marker.

**Note what the ROM does NOT do.** `func_0209f180` tests the gamecode byte and the marker byte
and returns -- there is no sum in it, and the read side has no other validity call. So the
public checksum (Q13) is still **P only**: the game's boot-time acceptance test does not
compute it. Whether the write side does is now a narrow question -- look at
`func_020a1224`, the call `func_020a03e0` makes immediately before it stamps the marker to 2
[H: read `func_020a1224` for a `0xb9fe`-iteration word-stride accumulate].

---

## 3. The player record (KOR `0x249c`, four slots at `+0x14`)

`func_02099ad0(self)` is the player slot's member-initialiser chain and, like `func_0209ef7c`
for the bank, it publishes the slot's map: eighteen calls at literal offsets, in descending
order [S: `src/matched/func_02099ad0.c`]. Its header comment records that the two container
registrations had to carry **different** pool words -- `+0x1bf2` and `+0x11a8` -- because
giving both the same offset collapsed one pool word and cost exactly 4 bytes of size delta.
**The offsets are byte-verified, not inferred.**

| field | KOR offset in slot | other regions | size/type | public | repo check | grade |
|---|---|---|---|---|---|---|
| patterns | `+0x0000` | EUR/USA 8 x `0x228`, JPN 8 x `0x220` (Q1) | 8 x `0x234` | Q3, Q9 | `func_02072ce8` registers a container at slot +0 with **count 8, stride `0x234`** | **S+P** |
| unknown | `+0x11a0` | EUR/USA `+0x1140`, JPN `+0x1100` (Q3) | 8 bytes | Q3 | `func_02072ce8` hands `+0x11a0` to its own initialiser -- it is a real object, not padding | **S+P** |
| pocket letters | `+0x11a8` | EUR/USA `+0x1148` x `0xF4`, JPN `+0x1108` x `0x8C` (Q1, Q3) | 10 x `0x100` | Q3, Q9 | `func_02099ad0` registers a container at `+0x11a8` with **count 10, stride 256** | **S+P** |
| default letter intro | `+0x1ba8` | EUR/USA `+0x1AD0`, JPN `+0x1680` (Q3) | 10 UCS-2 units | Q3 | falls in the gap `0x1ba8..0x1bf1` the chain leaves unregistered | P |
| default letter end | `+0x1bd0` | EUR/USA `+0x1B00`, JPN `+0x1694` (Q3) | 16 UCS-2 units | Q3 | same gap | P |
| pocket items | `+0x1bf2` | EUR/USA `+0x1B22`, JPN `+0x16A6` (Q3) | 15 x `u16` | Q3, Q9 | `func_02099ad0` registers a container at `+0x1bf2` with **count 15, stride 2** | **S+P** |
| wallet | `+0x1c10` | EUR/USA `+0x1B40`, JPN `+0x16C4` (Q3, Q9) | `u32` | Q3, Q9 | the pocket container ends at `0x1bf2 + 30 = 0x1c10` and the next registered object begins at `0x1c18`, so the wallet lies in an 8-byte unregistered gap that starts exactly at the published offset | **S+P** (by adjacency) |
| -- | `+0x1c18` | -- | 0x123 | -- | `func_0203cfa0` | S |
| -- | `+0x1d3b` | -- | 1 byte | -- | `func_0203d388` | S |
| **future letter** | `+0x1d3c` | EUR/USA `+0x1C6C` (Q3) | `0x100`, then 3 date bytes at `+0x1e3c` | Q3 names it for EUR/USA only | `func_02097e18` installs a letter object at `+0x1d3c` and the extent to the next member is `0x104` = one `0x100` letter plus the D/M/Y triple | **S**, KOR offset new |
| -- | `+0x1e40` | -- | 0xcc | -- | `func_0209ade4` | S |
| -- | `+0x1f0c` | -- | 0x50 | -- | `func_02077c0c`, one element of the `+0x1f5c` type at `+0x40` | S |
| **32-element roster** | `+0x1f5c` | EUR/USA the `0x481` "Unknown 5" at `+0x1D63` (Q3) | **32 x `0x24`** | Q3 calls it Unknown | `func_02077d24` registers a container with **count 0x20, stride 0x24**; `0x1f5c + 0x480 + 4 = 0x23e0`, the bank field | **S, new** |
| bank | `+0x23e0` | EUR/USA `+0x21E4`, JPN `+0x1C70` (Q3, Q9) | `u32` | Q3, Q9 | `func_020992fc(p)` is a one-line accessor returning `p + 0x23e0`, and `func_02099ad0` installs an object there | **S+P** |
| -- | `+0x23ec` / `+0x2404` / `+0x2416` / `+0x242c` | -- | 0x18 / 0x12 / 0x11 / 0x12 | -- | `func_02088808`, `func_020adf64`, `func_02088c0c`, `func_02088450` | S |
| acorn count | `+0x2421` | EUR/USA `+0x2225`, JPN `+0x1CB1` (Q3) | `u8` | Q3, Q9 | inside `func_02088c0c`'s object `0x2416..0x2426` | P (bounded by S) |
| face / hairstyle | `+0x243c` | EUR/USA `+0x223C`, JPN `+0x1CC6` (Q3) | `u8`, two nibbles | Q3, Q9 | `func_02099824` returns `((u32)ptr[0x243c] << 24) >> 28` (the high nibble) and `func_02099834` writes the low nibble; `func_02099808` takes its address | **S+P** |
| tan / hair colour | `+0x243d` | EUR/USA `+0x223D`, JPN `+0x1CC7` (Q3) | `u8`, two nibbles | Q3, Q9 | the byte after, inside the same unregistered pair before `func_02097dcc`'s object at `+0x243e` | **S+P** (by adjacency) |
| town id | `+0x247e` | EUR/USA `+0x2276`, JPN `+0x1CFC` (Q3) | `u16` | Q3, Q9 | `func_02099a38` (the per-slot initialiser `func_02098788` calls) hands `p + 0x247e` to `func_02095238`; `func_02099a28` and `func_0209987c` use the same offset | **S+P** |
| town name | `+0x2480` | EUR/USA `+0x2278` 8 chars, JPN `+0x1CFE` 6 chars (Q3) | 6 UCS-2 units | Q3, Q9 | inside the `+0x247e` identity object, which runs to the slot's end (`0x1e` bytes) | **S+P** |
| player id | `+0x248c` | EUR/USA `+0x2280`, JPN `+0x1D04` (Q3) | `u16`, non-zero = slot in use | Q3, Q9 | five `ov105` functions dereference `self + 0x248c` as an object of its own | **S+P** |
| player name | `+0x248e` | EUR/USA `+0x2282`, JPN `+0x1D06` (Q3) | 6 UCS-2 units | Q3, Q9 | same identity object | **S+P** |
| gender | `+0x249a` | EUR/USA `+0x228A`, JPN `+0x1D0C` (Q3) | `u8` | Q3, Q9 | last byte but one of the identity object | **S+P** |

**The 32-element container at `+0x1f5c` is the page's second new result.** It is the Korean
analogue of the `0x481`-byte block the public corpus labels "Unknown 5" for EUR/USA -- the
largest unnamed region in the published player record -- and the ROM says it is **thirty-two
records of thirty-six bytes**, with one further record of the same type embedded at `+0x1f4c`
[S: `src/matched/func_02077d24.c`, `func_02077c0c.c`, both routed to `func_02077ebc`]. Thirty-two
fixed slots per player, each large enough for an id and two short UCS-2 names, is the shape of
a **friend or visitor roster**, which is exactly the record type no public source documents
[H: settled by making the port persist a save after one wireless or gate event and diffing
`0x021de718` (= `0x021dc7a8 + 0x14 + 0x1f5c`) across it].

---

## 4. The town: acres, the item grid, buried items

`func_0204ea40` is the town object's initialiser and it settles four separate wiki questions in
eleven lines [S: `src/matched/func_0204ea40.c`]:

| what the code does | what it settles | grade |
|---|---|---|
| fills **0x24 bytes** at `base + 0` with the byte **0x86** | the acre array is exactly **36 bytes**, one `u8` per acre (Q11 gives base `0xD304`; `0xD304 + 36 = 0xD328`, the published item base) -- and **`0x86` is the unset-acre value**, which `town.md` carried only as a hypothesis and which is outside the 0..130 range the public acre-image set covers | **S+P**, and settles an H |
| loops **16 times** over `base + 0x24`, stepping **0x200** | the map-item layer is **16 blocks of 0x200 bytes = 16 acres x 256 cells x `u16` = 4,096 cells**, stored **acre-major**. `0xD304 + 0x24 = 0xD328` exactly (Q11) | **S+P**; confirms `game-systems.md`'s correction of "96x96" to 4,096 cells and its acre-major reading |
| loops the same 16 times over `base + 0x2024`, stepping **0x20** | the buried-item bitfield is **16 x 32 bytes = 512 bytes = 4,096 bits**, one bit per map cell, at `0xD304 + 0x2024 = 0xF328` -- the published base (Q11) to the byte | **S+P** |
| clears the low two bits of `base + 0x2224` | a two-bit town field at `+0xf528`, in the two bytes between the buried bitfield's end and the next member at `+0xf52a` | **S, new** |

The town object's total extent is `0x2226` (`0xd304` to `0xf52a`), and `0x24 + 0x2000 + 0x200 + 2`
is `0x2226` exactly. **Nothing is left over: the acre array, the item grid, the buried bits and
the two-bit field are the whole object.**

| other town fields | KOR offset | other regions | public | repo check | grade |
|---|---|---|---|---|---|
| town flag pattern | `+0x16d0c` | EUR/USA `0x15930`, JPN `0x11C5C` (Q11) | Q11 | inside `func_02088250`'s object, whose extent ends `0x234` (one pattern) after the published base | **S+P** (by adjacency) |
| lost and found | `+0x172c0` | EUR/USA `0x15EC0`, JPN `0x12114` (Q11) | Q11 | `func_0203a658` writes `0xfff1` into exactly **15** `u16` slots, and `0x172c0 + 0x1e = 0x172de` | **S+P** |
| recycling bin | `+0x172de` | EUR/USA `0x15EDE`, JPN `0x12132` (Q11) | Q11 | `func_0203a4ec`, the same 15-slot fill; `0x172de + 0x1e = 0x172fc` | **S+P** |
| turnip price | `+0x17370` | EUR/USA `0x15F5D`, JPN `0x121A3` (Q11) | Q11 | inside `func_02087830`'s `0x1a`-byte object at `+0x17364`, whose other writes are eight bytes of `1,1,0,0,1,1,0,0` and `0xff` at `+0x18` | P (bounded by S) |

The turnip row is worth one sentence for `economy.md`: the object holding the turnip byte is
**26 bytes with two identical four-byte groups**, which is the shape of a two-slot history, and
the public rule is that Wild World quotes **two prices a day** (`game-systems.md` P22). The
single published `u8` is one member of a small structure, not the whole market state
[H: watch `0x021f3b18`..`0x021f3b1d` across a midday boundary].

---

## 5. The villager record (KOR `0x7ec`, eight records at `+0x9284`)

`func_02081660` memsets `0x7ec` bytes and then initialises the record field by field -- the
whole Korean villager layout in one matched function [S: `src/matched/func_02081660.c`].
`func_0207cec0(base, idx)` is the record accessor: it returns `base + idx * 0x7ec`, gated by
`func_0207cf74(idx)` [S: `src/matched/func_0207cec0.c`], and thirty-odd matched functions call
it with the literal base `0x021e5a2c` = `0x021dc7a8 + 0x9284`.

| field | KOR offset in record | other regions | size/type | public | repo check | grade |
|---|---|---|---|---|---|---|
| eight `0x80`-byte sub-records | `+0x000` | Q4 calls `0x0-0x3FF` "Unknown 1" in every region | 8 x `0x80` | Q4 (unnamed) | `func_02081660` loops `i < 8` over `self + (i << 7)`, ending exactly at `0x400` | **S, new** |
| pattern | `+0x400` | EUR/USA `+0x340`, JPN `+0x280` (Q4) | `0x234` | Q4, Q10 | the 8-record loop ends there and the next initialiser call is `func_02080b50` | **S+P** |
| letter | `+0x634` | EUR/USA `+0x568`, JPN `+0x4A0` (Q4) | `0x100` | Q4, Q10 | `func_02081660` calls **`func_02066650`** at `self + 0x634` -- the same letter initialiser the 10-letter store at `+0x15954` uses | **S+P** |
| -- | `+0x734` | Q4 "Unknown 2", `0x58` | `0x58` | Q4 | `func_0209b604(self + 0x734)` | S |
| furniture | `+0x78c` | EUR/USA `+0x6AC`, JPN `+0x578` (Q4) | 10 x `u16` | Q4, Q10 | `func_02081660` loops `j < 10` writing `0xfff1` into `self + 0x78c + (j << 1)` | **S+P** |
| character reference | `+0x7a0` | Q4 "Unknown 3", `0xE` | 16 bytes | Q4 (unnamed) | `func_02003738(self + 0x7a0)`; see below | **S**, structure new |
| song | `+0x7a4` | EUR/USA `+0x6D0`, JPN `+0x59A` (Q10, disabled as unresearched) | `u8` | Q10 | inside the reference block's name field -- **the public offset is probably wrong**; see the disagreement below | P, contested |
| **personality** | `+0x7ae` | EUR/USA `+0x6CA`, JPN `+0x594` (Q4, Q10) | `u8`, default **6** | Q4, Q10 | `func_02003738` writes `r4[0x0e] = 6` into the block based at `+0x7a0` | **S+P** |
| **villager id** | `+0x7af` | EUR/USA `+0x6CB`, JPN `+0x595` (Q4, Q10) | `u8`, `0xff` = empty | Q4, Q10 | `func_02003738` writes `r4[0x0f] = 0xff`, and `func_02003648(p)` is a leaf returning `p[15]` -- the read path `villagerface.c` documents | **S+P** |
| home town id and name | `+0x7b8` | not published (inside Q4's "Unknown 4") | `u16` + 6 UCS-2 | **none** | `func_02081660` calls `func_020642e0(self + 0x7b8)` -- the identical id-plus-name initialiser the bank header uses at `+0x02` | **S, new** |
| -- | `+0x7ce` | -- | -- | -- | `func_02081f94(self + 0x7ce)` | S |
| shirt | `+0x7d2` | EUR/USA `+0x6EC`, JPN `+0x5AE` (Q4, Q10) | `u16` item id | Q4, Q10 | `func_02081660` writes the literal **`0x11a8`** there -- the first clothes id | **S+P** |
| wallpaper | `+0x7d4` | EUR/USA `+0x6EE`, JPN `+0x5B0` (Q4, Q10) | `u8` | Q4, Q10 | not separately touched | P |
| carpet | `+0x7d5` | EUR/USA `+0x6EF`, JPN `+0x5B1` (Q4, Q10) | `u8` | Q4, Q10 | not separately touched | P |
| -- | `+0x7d6` | Q4 "Unknown 5" | `u8`, default **3** | Q4 (unnamed) | `func_02081660` writes 3 | **S, new** |
| umbrella | `+0x7da` | EUR/USA `+0x6F4`, JPN **`+0x544`** (Q4, Q10) | `u8` | Q4, Q10 | not separately touched | P |
| second town id and name | `+0x7dc` | not published (inside Q4's "Unknown 6") | `u16` + 6 UCS-2 | **none** | a second `func_020642e0(self + 0x7dc)` | **S, new** |

**The 16-byte "character reference" (invented name).** `func_02003738(p)` calls `func_020642e0`
on the same pointer -- which zeroes a `u16` at `+0` and twelve bytes at `+2` -- then writes
`p[0x0e] = 6` and `p[0x0f] = 0xff` [S: `src/matched/func_02003738.c`, `func_020642e0.c`]. So the
block is `{ u16 id; char16_t name[6]; u8 personality; u8 species }`, sixteen bytes, and the
villager record embeds one at `+0x7a0`. The same block appears twice more in the bank, at
`+0x1731a` and `+0x1732a` inside `func_02086874`'s object [S: `src/matched/func_02086874.c`],
so it is a reusable "which character" reference rather than a villager-only field.

**A disagreement worth exporting.** Q10 places the villager's K.K. song at record `+0x7a4` and
disables the accessor as unresearched. `+0x7a4` is the third UCS-2 unit of the reference
block's name field, which `func_020642e0` zeroes as part of a 12-byte string. A `u8` song index
cannot live there. **This project's reading is the stronger one**: `+0x7a4` is name text, and
the song is somewhere else [S: `src/matched/func_020642e0.c`; contradicts Q10].

**Why eight records and three villagers.** The array's own accessor bounds the index at 8
(`func_0207cf80`'s struct is `arr[8]`, and a dozen matched loops run `i < 8` at stride `0x7ec`),
and `func_0207a02c` builds its candidate mask over eight slots but stops at **six** entries
[S: `src/matched/func_0207a02c.c`]. Combined with `game-systems.md`'s finding that a new town
starts with three villagers, the eight-slot loop filling three slots is correct behaviour.

---

## 6. Item ids: the encoding, and two corrections to the public map

The public band map (Q12) is reproduced in `game-systems.md`. Three things the repo can add:

- **`0xfff1` is the empty-item id and the ROM writes it everywhere an item slot is created**:
  villager furniture, the lost-and-found, the recycler, letter attachments, and two more
  stores. It appears 968 times across 612 matched files [S: `src/matched/` census], and
  Q12 agrees (`0xFFF1 -> ItemType::Empty`). **S+P.**
- **Clothes are 256 ids, not 264.** Q12 gives `0x11A8-0x12AF` for Clothes. The ROM's own range
  test, repeated in more than twenty matched functions, is **`0x11a8 <= id <= 0x12a7`**
  [S: `src/matched/func_0207fd1c.c`, `func_02024ab4.c`, `func_020272c0.c`, `func_02029a98.c`
  and ~20 more], and `func_02061e2c` clamps a shirt index at **`0x100`** before adding
  `0x11a8`. `0x12a7 - 0x11a8 + 1 = 256`, which is exactly the 256 `cloth/` textures
  `data/items.md` counted. The eight extra ids `0x12a8..0x12af` are the ROM's **own separate
  class**: `func_020224c4` tests `0x12a8 <= id <= 0x12af` and nothing else does
  [S: `src/matched/func_020224c4.c`]. This settles `data/items.md`'s open "DISAGREES by 8":
  eight ids, no textures, their own predicate -- the eight wearable player patterns.
  **S beats P here.**
- **The catchable band is two bands of 56.** Q12 gives one range `0x12B0-0x131F` (112 ids). The
  ROM never tests that range; it tests **`0x12b0..0x12e7`** and **`0x12e8..0x131f`** as two
  separate predicates, in dozens of paired call sites [S: `src/matched/func_0201f858.c`,
  `func_0201fa58.c`, `func_020255d8.c`, `func_020292b4.c`, `func_0202c704.cpp`,
  `func_0202c5dc.cpp` and ~20 more], and `func_0202c2c4` clamps an index at **0x38 = 56**
  before adding `0x12b0` [S: `src/matched/func_0202c2c4.c`]. Two families of 56 with the first
  based at `0x12b0` -- exactly what `data/fish-and-bugs.md` hypothesised and what P19's
  "bugs first, then fish" asserts. **Promote that page's hypothesis to S+P.**

The furniture encoding is unchanged from `game-systems.md`: base `0x3000`, the low two bits of
the id are the rotation, so `file_id = (id - 0x3000) >> 2` [P: Q12's `0xFFFC` rotation mask and
the `0x3000-0x45D8` / `0x47D8-0x4BA0` bands]. **Note that the JS editor does not implement
rotation at all** (`room.js` treats a cell as a flat `u16`), so the rotation claim rests on
WildEdit's C++ alone and has no S citation yet [H: find a matched function that masks an item
id with `0xfffc` or `& 3` on the placement path].

---

## 7. The pattern record (KOR `0x234`)

| field | KOR | EUR/USA | JPN | size/type | public | grade |
|---|---|---|---|---|---|---|
| image | `+0x000` | same | same | `0x200` bytes, 32x32 at 4 bits, two pixels per byte | Q5, Q19 | P |
| creator town id | `+0x200` | same | same | `u16` | Q5, Q19 | P |
| creator town name | `+0x202` | `+0x202` 8 chars | `+0x202` 6 chars | 6 UCS-2 | Q5, Q19 | P |
| creator player id | `+0x20e` | `+0x20A` | `+0x208` | `u16` | Q5, Q19 | P |
| creator player name | `+0x210` | `+0x20C` | `+0x20A` | 6 UCS-2 | Q5, Q19 | P |
| creator gender | `+0x21c` | `+0x214` | `+0x210` | `u8` | Q5, Q19 | P |
| pattern name | `+0x21e` | `+0x216` 15 chars | `+0x212` 10 chars | 10 UCS-2 | Q5, Q19 | P |
| design type / palette | `+0x232` | `+0x226` | `+0x21C` | `u8`: bits 0-3 palette, 4-7 design type | Q5, Q19 | P |

The record size is the one row the repo confirms: `func_02072ce8` registers the player's
pattern container with **stride `0x234`** and count 8 [S: `src/matched/func_02072ce8.c`;
P: Q1, Q3, Q5]. **S+P for the stride; the interior is P only.** The image is `0x200` bytes for
32 x 32 four-bit pixels (`32 * 32 / 2 = 512`), which is self-consistent, and the palette is one
nibble -- fifteen usable colours plus transparent, as `pattern.js` renders it (Q19).

Patterns appear in five places in the bank: eight per player at slot `+0x0`, one per villager
at record `+0x400`, eight in the Able Sisters store at `+0x10ad0`, and one town flag inside the
object at `+0x16ad0` [S: `src/matched/func_02072ce8.c`, `func_02081660.c`, `func_0209ef7c.c`;
P: Q9, Q10, Q11, Q18].

---

## 8. The letter record (KOR `0x100`) and the letter store

`func_02066650` is the letter initialiser: it zeroes `0x100` bytes and writes `0xfff1` into the
`u16` at `+0xfc` [S: `src/matched/func_02066650.c`]. Q6 says the KOR letter is `0x100` bytes
with its attachment item at `+0xFC`. **Both numbers, S+P, from four lines of code.**

| field | KOR | EUR/USA | JPN | size/type | grade |
|---|---|---|---|---|---|
| padding | `+0x00` | same | same | `u32` | P |
| receiver town id / name | `+0x04` / `+0x06` | `+0x04` / `+0x06` (8 ch) | `+0x04` / `+0x06` (6 ch) | `u16`, 6 UCS-2 | P |
| receiver player id / name | `+0x12` / `+0x14` | `+0x0E` / `+0x10` | `+0x0C` / `+0x0E` | `u16`, 6 UCS-2 | P |
| sender town id / name | `+0x24` / `+0x26` | `+0x1C` / `+0x1E` | `+0x18` / `+0x1A` | `u16`, 6 UCS-2 | P |
| sender player id / name | `+0x32` / `+0x34` | `+0x26` / `+0x28` | `+0x20` / `+0x22` | `u16`, 6 UCS-2 | P |
| intro / body / ending | `+0x44` / `+0x58` / `+0xd8` | `+0x34` / `+0x4C` / `+0xCC` | `+0x2C` / `+0x36` / `+0x76` | 10 / 64 / 16 UCS-2 units | P |
| intro-name index, paper id, flags | `+0xf8` / `+0xf9` / `+0xfa` | `+0xEC` / `+0xED` / `+0xEE` | `+0x86` / `+0x87` / `+0x88` | `u8` each | P |
| **attached item** | `+0xfc` | `+0xF0` | `+0x8A` | `u16`, `0xfff1` = none | **S+P** |

Q6 also publishes a 64-entry paper-id table and a flag enumeration (`0x1` created, `0x2` unread,
`0x3` read, `0x4`/`0x5` bottle letters, `0x40` from Mother), region-invariant. Not copied here;
cite Q6.

Letters live in six places, and the ROM's own initialiser chain finds two the public corpus
does not name: **ten letters at bank `+0x15954`** (`func_02097fa4` calls `func_02066650` ten
times at `i << 8`, then sets four bytes and a `u16` at `+0xa00`..`+0xa04`) and **one letter at
bank `+0x11c70`** (`func_02090174` memsets `0x950` and installs a letter at `+0`)
[S: `src/matched/func_02097fa4.c`, `func_02090174.c`, `func_0209ef7c.c`]. Ten shared letter
slots plus a singleton is the shape of a **post-office hold and a pending mother's letter**
[H: both settled by one save-diff after posting a letter].

Out of the bank, Q7 puts the Korean letter storage at **`0x337fc`**, four players x `0x3200`
holding **50 letters each** (EUR/USA `0x2E20C`, 75 each; JPN `0x35BEC`, 75 each), with its own
`u16` checksum at `0x3fffe`. `2 * 0x173fc = 0x2e7f8`, so it sits in the ~70 KB of the 256 KB
chip that is in neither bank. **Korea holds fewer letters than any other region**, which is a
concrete, cheap prediction to test.

---

## 9. House, rooms, dresser, shops

| field | KOR | EUR/USA | JPN | size/type | public | grade |
|---|---|---|---|---|---|---|
| house object | `+0xf52c` | `0xE558` | `0xC554` | `0x2744` incl. the pattern store | Q8, Q15 | **S+P** (`func_0209ef7c` installs it at exactly the published base) |
| room layer 1 | house `+0x000 + slot*2` | same | same | 256 x `u16` | Q16 | P |
| room layer 2 | house `+0x200 + slot*2` | same | same | 256 x `u16` | Q16 | P |
| carpet / wallpaper / song | house `+0x448` / `+0x44a` / `+0x44c` | same | same | `u16` each | Q16 | P |
| room stride, room count | `0x450`, 4 rooms | same | same | -- | Q17 | P |
| debts / song list / house size | house `+0x1590` / `+0x1594` / `+0x15a0` | -- | -- | `u32`, 9 bytes, `u8 & 7` | Q17 | P |
| Able Sisters patterns | `+0x10ad0` | `0xFAFC` | `0xDAF8` | 8 x `0x234` | Q18 | **S+P** (the house object's extent ends `8 * 0x234` after this base) |
| dresser | `+0x16800`, 90 `u16` per player, stride `0xb4` | `0x15430` | `0x11764` | -- | Q9 | **S+P** (four strides end exactly at the next member) |

**No public source documents Nook's daily stock, the catalogue bit array, the museum donation
record, or a friend list** in any region. Three of those four are the best candidates for the
unnamed `0x3394`-byte object at `+0x125c0` and the 32-slot roster at player `+0x1f5c`.

---

## 10. What the tool now does, and the fixture

`port/tools/savetool.py check` previously dumped the bank header, the checksum verdict and the
four player slots. It now also dumps **the eight villager records** -- slot base, id byte at
`+0x7af` with `0xff` printed as an empty slot, personality byte at `+0x7ae`, shirt id at
`+0x7d2` and the ten furniture ids at `+0x78c` -- and reports how many slots are occupied. The
player dump gained the face/hair nibbles at `+0x243c`/`+0x243d`. Every offset it uses is either
S+P or P from the tables above, and the module docstring says which.

`port/tools/test_savetool.py` gained three tests built on `build_bank_with_villager()`: a
synthetic bank with **one** villager written into slot 3 (id `0x65`, personality 2, shirt
`0x11ab`, two furniture ids and eight `0xfff1` empties), the other seven slots stamped `0xff`.
It keeps the existing fixture's discipline (**M1**): the expected sum `0x99fb` and checksum
`0x6605` are added up by hand in the docstring and asserted as literals, never asked of the
tool. Two traps are made into calibrations rather than comments -- **a zeroed array is eight
copies of villager 0, not eight empty slots**, and **a zeroed furniture slot is item `0x0000`,
not an empty one** -- and the test fails if the dump ever treats zero as absent.

**Fixture result.** `python port/tools/test_savetool.py` -- **9/9 passed** (six pre-existing
tests plus three new ones). `check` on the fixture image reports `villagers occupied: 1 of 8`
in both banks and prints the eight record bases as
`0x09284 0x09a70 0x0a25c 0x0aa48 0x0b234 0x0ba20 0x0c20c 0x0c9f8` -- which is Q2's Korean
villager table, row for row, generated from the repo's own stride rather than copied from it
[S+P: `src/matched/func_0207cec0.c`; Q2].

---

## 11. Prioritised actions

**Corrections to make now (no run).**

1. **A-S1.** `save-data.md`: add the bank's top-level map from `func_0209ef7c` as a "what is
   inside a bank" section at grade S. It is the page's largest missing content and it costs
   nothing -- the function is already matched.
2. **A-S2.** `save-data.md` and `town.md`: `+0x173f8` is the checksum **and** the head of a
   four-byte trailer; `+0x173fa` is a **write-in-progress marker** (28 during a save, 2 when
   complete) that `func_0209f180` demands equal 2. Neither page says this.
3. **A-S3.** `town.md`: strike the "96x96" hypothesis outright. `func_0204ea40` fills 36 acre
   bytes and sixteen 0x200-byte item blocks -- 4,096 cells, acre-major, and `0x86` is the
   unset acre value. Three hypotheses close on one function.
4. **A-S4.** `data/items.md`: clothes are `0x11a8..0x12a7` (256), and `0x12a8..0x12af` is the
   ROM's own separate eight-id class. The catchable band is two bands of 56, not one of 112.
   Both are S readings that beat the public map.
5. **A-S5.** `villagers.md`: the record's `+0x7a0` block is a 16-byte `{id, 6 UCS-2 name,
   personality, species}` reference with defaults 6 and `0xff`; there are two more id-plus-name
   blocks at `+0x7b8` and `+0x7dc`; and the public "song at `+0x7a4`" cannot be right.
6. **A-S6.** `player.md`: add the slot map from `func_02099ad0`, and record that the wallet
   sits in the 8-byte gap the container chain leaves at `+0x1c10`.

**Experiments, cheapest first.**

- **A-E1 (no run).** Read `func_020a1224` -- the call `func_020a03e0` makes immediately before
  stamping the trailer to 2 -- for a `0xb9fe`-iteration word-stride accumulate. That is the one
  place the ROM would compute the public checksum, and finding it moves Q13 from P to S+P.
- **A-E2 (no run).** Read `func_0209ef10`, the four-iteration loop `func_0209ef7c` runs before
  the offsets, for a fifth per-player structure the offset list does not cover.
- **A-E3 (one run).** `ACWW_WATCH` the six flag bits at `0x021f3ba4` (= `+0x173f4`) across the
  town recipe. Six named bit numbers are already known from the call sites; seeing which flip
  at which frame names them.
- **A-E4 (one run + `savetool check`).** Persist a save, then run `check` and confirm the eight
  villager rows against what `port/shim/game/villpick.c` logged during generation. This is the
  first end-to-end test of the whole layout and it needs no new code.
- **A-E5 (one run).** Diff player `+0x1f5c`..`+0x23df` (the 32 x `0x24` roster) before and
  after a gate or wireless event. If it changes, the largest unnamed block in the published
  player record is named, and that is a new public result.
- **A-E6 (static).** Confirm the RAM-to-save identity A-S1 rests on: `ACWW_WATCH 0x021dc7a8`
  and compare against byte 0 of the `ACWW_SAVE` image after a write.

## 12. Related

- `game-systems.md` -- the first pass, whose P1-P32 this page's Q1-Q20 extend downward.
- `data-formats.md` section 8 -- the checksum, the region table and the UCS-2 finding.
- `../systems/save-data.md`, `../systems/player.md`, `../systems/villagers.md`,
  `../systems/town.md`, `../data/items.md` -- the pages A-S1..A-S6 act on.
- `../experiments/save-store-probe.md` -- the recipe every save observation needs.
- `port/tools/savetool.py`, `port/tools/test_savetool.py` -- the tool and its fixture.
