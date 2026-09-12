# Random numbers

**Summary.** There is no single random number generator in this ROM. Four are known. Three are
library generators -- NitroSDK's `MATH_Rand16` and `MATH_Rand32`, used by the networking code;
the SPL particle library's own, used for visual jitter; and a bespoke one in the Wi-Fi setup
overlay -- and each is seeded from the hardware tick, the real-time clock, or both. **The
fourth is the GAME's own, and ORACLE46 found it**: one 32-bit state word at `0x021cb5a0`,
stepped by `x = x * 0x19660d + 0x3c6ef35f`, seeded ONCE at boot from four bytes of the
real-time clock, and it is what draws the town's id and its villagers.

## What happens

**A naming note this page needs.** `MATH_Rand16`, `MATH_Rand32`, `MATH_InitRand16/32` and
`OS_IsTickAvailable` are NitroSDK library names, not names in this ROM's symbol tables: no such
symbol exists in any `config/adm-kr/arm9/**/symbols.txt`, and every one of them is reached in
`src/matched/` under a `func_*` name [H: source account: `config/adm-kr/arm9/**/symbols.txt`, name sweep; direct ROM-source provenance unresolved].
They are used here because `../STYLE.md` rule 2 allows SDK names, and the `func_*` name is given
alongside wherever one exists.

### The game's own generator, and its seed

**The state is one word at `0x021cb5a0`** and the step is `func_020e92e8`:
`x = x * 0x19660d + 0x3c6ef35f`, the state written back and returned whole
[S: `src/matched/func_020e92e8.c`]. A bounded draw is `func_020e92d0(state, n)`, which returns
`(n * x) >> 32` -- the high-bit form the SDK generators also use
[S: `src/matched/func_020e92d0.c`]. **`func_020644cc(n)` is the game-wide wrapper that binds
the state**: its three ARM instructions are `ldr r12, [pc,#8]` -> `func_020e92d0`,
`mov r1, r0`, `ldr r0, [pc,#4]` -> `0x021cb5a0`, `bx r12`, so the pool words at `0x020644dc`
and `0x020644e0` are the function and the state and neither is inferred
[S: `extract/adm-kr/arm9/arm9.bin` at `0x020644cc`, read in ORACLE46; the matched file
`src/matched/func_020644cc.c` spells both as placeholder names -- D12].

**It is seeded once, at boot, from the clock, and the seed is four bytes.**
`__sinit_020c5a78` sets the state to 1 and registers a callback
[S: `src/matched/__sinit_020c5a78.c`]; `func_02061530` then calls
`func_020e930c(0x021cb5a0, func_0209dbbc())`, and `func_020e930c` is a two-instruction store --
this is `srand` [S: `src/matched/func_02061530.c`, `src/matched/func_020e930c.c`].
`func_0209dbbc` reads the GAME's clock globals and folds them:

    seed = minute | (day << 8) | (hour << 16) | (second << 24)

from `0x021dc758`, `0x021dc74c`, `0x021dc754` and `0x021dc75c`
[S: `src/matched/func_0209dbbc.c`]. **The year, the month and the weekday are not in it, and
neither is the tick.** On the port, a load watchpoint on that block sees exactly those three
pcs -- `0x0209dbc0`, `0x0209dbc4`, `0x0209dbcc` -- fire at **frame 3**, reading `0`, `0x0f` and
`0x0a`: seed `0x000a0f00` for the default 2005-06-15 10:00:00 instant. The same census windowed
on the two generation frames finds those pcs ABSENT, so nothing re-seeds
[E: `docs/log/cycle41-gameplay.md` ORACLE46, runs `scratchpad/oracle46/runs/o46-A`, `scratchpad/oracle46/runs/o46-D`, `scratchpad/oracle46/runs/o46-E`].

**What it draws.** The town's id is `func_0206426c` = `func_020644cc(0x7fff) | 0x8000`, stored
as the halfword at `0x021dc7aa` by `func_02064244`
[S: `src/matched/func_0206426c.c`, `src/matched/func_02064244.c`]; the villager picker
`func_0207b594` draws from the same wrapper (`villagers.md`). Measured end to end on the port:
at frame 24,789 the state reads `0x010d14fa`, steps to `0x8cdea011`, and
`(0x7fff * 0x8cdea011) >> 32 = 0x466e`, which `| 0x8000` is the `0xc66e` the store watchpoint
sees land [E: ORACLE46 run `scratchpad/oracle46/runs/o46-F`].

**The town's ID and the town's MAP are two DIFFERENT moments on the stream, 11,346 frames
apart.** The id is drawn at the name confirmation (port frame 24,789, draw **#2,667**); the acre
map, the item layer and the villager roster are all drawn in ONE later burst -- port frame
**36,135**, draws **#3,783..#4,014**, all in that single frame; the original spreads the same
burst over ~90 frames. The map is generated a second time, too: once at boot inside the 280-draw
initialiser burst (port frame 758, index 0..280) and then reset to `0x86` / `0xfff1` before the
real one. So a recipe that pins the id draw does NOT pin the map, and a recipe that pins the map
gets the roster for free because it is the same frame
[E: `docs/log/cycle41-gameplay.md` ORACLE49 O49-1/O49-2; current receipt locator: `scratchpad/oracle49/RECEIPTS.md`]. `func_0209ccd4`'s 6x6 loop -- one
bounded draw per acre, 36 of them -- is inside that burst [S: `src/matched/func_0209ccd4.c`].

**The seed is robust; the DRAW COUNT is not.** Because the seed is taken within the first
second of the run, a clock arm that only holds the clock from a later frame cannot change it:
the emulator produces `0x000a0f00` at frame 44 with and without `--rtc-freeze-until`
[E: ORACLE46 `scratchpad/oracle46/runs/o46-seedarm2` / `scratchpad/oracle46/runs/o46-seedoff`]. What separates two towns is how many draws are
consumed between that seed and the moment the id is drawn, which is a property of everything
the run did in between.

### Where the draws go, and how far apart two producers are

**Every draw goes through ONE instruction.** A store watchpoint on `0x021cb5a0` over three
separate windows of a port run -- 131 stores in all -- reports pc `0x020e92f8` and no other:
`func_020e92e8`'s own write-back. There is no second writer and no producer-specific path, so
two runs of this ROM differ only in HOW FAR ALONG the one stream they are
[E: `scratchpad/oracle47/RECEIPTS.md`, O47-2; `docs/log/cycle41-gameplay.md` ORACLE47 O47-2].

**Draws are consumed once per MAIN-LOOP BODY, not once per frame.** On the port, 51 consecutive
stores over frames 852..1,002 are spaced exactly three frames apart, and the main loop runs once
per three frames on both the port and the original [H: log/source account: `docs/log/cycle41-gameplay.md` ORACLE47, and INPUT46 on `0x021fbdd0`,
`docs/kb/hybrid/stall-playbook.md` case 70; receipt provenance unresolved]. The rate is scene-dependent -- one draw per three
frames in the title, one per ~12 on the town-name page -- so **a run that reaches a scene early
arrives with FEWER draws taken**, which is why the port, ~280 frames ahead of the original in
scene time, is ~176 frames BEHIND it in stream position when the town is drawn. Because the LCG
is a bijection, a single peeked word names its own index: `scratchpad/oracle47/lcg.py` steps the
seed forward under a bound and `draws.py` turns either producer's ledger into a draw count.

**Consequence for any differential.** Two producers can be made to draw the same town by moving
the input that triggers the draw, not by changing the clock: `port/tools/oracle/README.md`,
"THE SHARED-TOWN RECIPE".

### The SDK generators

`MATHRandContext32` is a three-field structure -- state, multiplier, addend, all 64-bit -- and
`MATH_Rand32` advances it as `x = mul * x + add`, returning the top 32 bits of the new state, or
`(top32 * max) >> 32` for a bounded draw
[S: `MATH_Rand32`, ov065, `src/matched/func_ov065_0227ef00.c`]. The constants are multiplier
`0x5D588B656C078965` and addend `0x269EC3`; the multiplier is written in the sources as
`(1566083941 << 32) + 1812433253` [S: `src/matched/func_ov065_0227ef00.c`; historical account: `src/matched/func_ov065_0227ef00.c`].

`MATHRandContext16` is the same family truncated: 32-bit state, multiplier `0x5D588B65` --
exactly the high half of the 64-bit multiplier -- addend `0x269EC3`, output the top 16 bits
[S: `MATH_Rand16` / `MATH_InitRand16`, autoload_2, `src/matched/func_02100cbc.c`]. Taking the
high bits rather than the low ones is the point of the design: the low bits of an LCG have
short periods.

The particle generator is unrelated and its constants say so: multiplier `0x5EEDF715`, addend
`0x1B0CB173`, 32-bit state, output the high bits
[S: `SPLRandom_Next` / `gSPLRandomState`, main, `src/matched/func_020fded0.c`]. It drives
particle spawn position, velocity, rotation, lifetime, texture frame and colour
[S: `SPLEmitter_EmitParticles`, main, `src/matched/func_020fded0.c`]. The same generator body
appears against two further, independent state words -- one in ov066 and one named `g_rng_state`
in main -- so at least three particle-class streams run in parallel
[S: `src/matched/func_ov066_022699ec.c`, `src/matched/func_020ff994.c`].

`AOSS_Rand` in ov001 is a fourth implementation reusing the 16-bit constants as its own
independent 32-bit LCG rather than calling the SDK, and returns a 15-bit value as
`(0x7fff * (v >> 16)) >> 16` [S: `AOSS_Rand`, ov001, `src/matched/AOSS_Rand.c`].

### Where the seeds come from

Two sources, and both are clocks.

`OS_GetTick` is the dominant one. It is the direct seed in `func_ov065_0227876c` (a throwaway
context used to fabricate a temporary login id) and in `func_021013d0` (which reads the tick,
runs one LCG step by hand and stores only the high 32 bits of the product as a per-connection
seed) [S: `src/matched/func_ov065_0227876c.c`, `src/matched/func_021013d0.c`]. The shared
network context `DWCi_GetMathRand32` seeds itself once, lazily, from the console's MAC address
combined with the tick [S: `func_ov065_0227ef00`, ov065, `src/matched/func_ov065_0227ef00.c`].

The RTC is the other. `DWCi_AUTH_GetNewWiFiInfo` and `DWCi_AUTH_RemakeWiFiID` seed a 16-bit
context from the RTC date and time converted to seconds, with the tick added when
`OS_IsTickAvailable` says so, and then use `MATH_Rand16` to mint a Wi-Fi id and a non-zero
`randomHistory` value -- the remake path excluding the previous history value
[S: `src/matched/func_02100cbc.c`, `src/matched/func_02100b18.c`]. `AOSS_Rand` folds
`hour << 10 + minute << 3 + second` into its seed on first call, falling back to seed 0 if the
RTC read fails [S: `AOSS_Rand`, ov001, `src/matched/AOSS_Rand.c`].

There is also an entropy pool that none of the town generators above consume.
`OS_GetLowEntropyData` fills eight words from VCOUNT (`0x04000006`) combined with
`OS_GetTickLo`, the 64-bit tick XORed with MAC bytes and the VBlank counter, the geometry
engine's status register at `0x04000600`, the RTC bytes in low WRAM, microphone data, touch
panel state and the Wi-Fi RSSI pool [S: `OS_GetLowEntropyData`, autoload_2,
`src/matched/OS_GetLowEntropyData.c`]. It is not wired into any of the generators above; its matched callers are in the Wi-Fi
overlay, `src/matched/func_ov065_02275b94.c` at three sites [S: `src/matched/func_ov065_02275b94.c`, lines 546, 593, 696
(wiki-provenance-1, HANDOFF16)], so whether it ever runs in an offline session is a
separate question [H: no watch on its entry has been run].

### What has not been found

No save-side or town-side seed field. Searches across `src/matched` for `SaveData`, `TownData`,
`randomSeed`, `worldSeed`, `townSeed` and the like return nothing [H: source account: absence in `src/matched`; direct ROM-source provenance unresolved],
and ORACLE46's measurement is consistent with there being none to find on this path: the state
at `0x021cb5a0` is seeded from the clock at boot and simply runs. What is still open is which
of the game's draws come off THIS stream and which off another -- the villager picker and the
town id are established, fish, bugs and shop stock are not.

The save checksum was missed by the `crc`/`checksum` name search: the bank poller
`func_020a1a40` calls the 16-bit wrapping word sum `func_02050920` and accepts only a zero
sum together with `func_0209f180`'s header checks [S: `port/shim/game/savepoll.c`,
`src/matched/func_02050920.c`, `src/matched/func_0209f180.c`; log:
`docs/log/cycle41-gameplay.md` GP45-5].
GP45-5 recorded a complete save with stored and computed checksum `0xbddf`, residual
`0x0000`, and the ROM acceptance test reporting that the game would LOAD the bank
[E: `scratchpad/gameplay45/RECEIPTS.md`; log: `docs/log/cycle41-gameplay.md` GP45-5].

### The port

The frozen-clock arm does not establish a different boot seed: ORACLE46 measured
`0x000a0f00` on the port at frame 3 and on the original at frame 44 with and without
`--rtc-freeze-until 48000` [E: `scratchpad/oracle46/RECEIPTS.md`; log:
`docs/log/cycle41-gameplay.md` O46-4].
ORACLE47 found the armed and unarmed original at the same stream position from frames
1,000 through 10,000, first differing between 10,000 and 11,000 and ending with 14 extra
armed draws by confirmation [E: `scratchpad/oracle47/RECEIPTS.md`,
`scratchpad/oracle46/ledgers/o-townarm.jsonl`, `scratchpad/oracle46/ledgers/o-townoff.jsonl`;
log: `docs/log/cycle41-gameplay.md` O47-3].
These arms differ in draw consumption on the town-name page, so sharing the boot seed alone
does not establish a shared town [E: `scratchpad/oracle46/RECEIPTS.md`,
`scratchpad/oracle47/RECEIPTS.md`; log: `docs/log/cycle41-gameplay.md` O46-4, O47-3].
The forward recipe aligns the id and the later layout/roster burst on the measured build;
the inverse recipe aligns the id but reaches the layout burst two draws early
[E: `scratchpad/oracle49/RECEIPTS.md`; log: `docs/log/cycle41-gameplay.md` O49-2, O49-4, O49-5].

## Where it lives

| function or symbol | module | role | grade/citation |
|---|---|---|---|
| `func_020e92e8` `0x020e92e8` | main | **the game's LCG**: `x = x * 0x19660d + 0x3c6ef35f` on the caller's state word | [S: `src/matched/func_020e92e8.c`] |
| `func_020e92d0` `0x020e92d0` | main | the bounded draw `(n * next) >> 32` | [S: `src/matched/func_020e92d0.c`] |
| `func_020644cc` `0x020644cc` | main | binds state `0x021cb5a0` to that draw -- the game-wide `rand(n)` | [S: `extract/adm-kr/arm9/arm9.bin` at `0x020644cc`, pool words `0x020644dc`/`0x020644e0`] |
| `func_02061530` `0x02061530` / `func_020e930c` | main | `srand`: the state set to `func_0209dbbc()` | [S: `src/matched/func_02061530.c`] |
| `func_0209dbbc` `0x0209dbbc` | main | the seed: `minute \| day<<8 \| hour<<16 \| second<<24` | [S: `src/matched/func_0209dbbc.c`] |
| `func_0206426c` / `func_02064244` | main | the town id, `rand(0x7fff) \| 0x8000`, into the halfword at `0x021dc7aa` | [S: `src/matched/func_0206426c.c`] |
| `MATH_Rand32` / `MATH_InitRand32` / `MATHRandContext32` | ov065 | 64-bit LCG, mul `0x5D588B656C078965`, add `0x269EC3`, output high 32 | [S: `src/matched/func_ov065_0227ef00.c`] |
| `MATH_Rand16` / `MATH_InitRand16` / `MATHRandContext16` | autoload_2 | 32-bit LCG, mul `0x5D588B65`, add `0x269EC3`, output high 16 | [S: `src/matched/func_02100cbc.c`] |
| `DWCi_GetMathRand32` `0x0227ef00` | ov065 | the shared network context, seeded once from MAC and tick | [S: `src/matched/func_ov065_0227ef00.c`] |
| `func_ov065_02268c78` (`CPS_Resolve`) | ov065 | draws `MATH_Rand32(ctx, 0x10000)` for DNS transaction ids | [S: `src/matched/func_ov065_02268c78.c`] |
| `func_ov065_0227876c` | ov065 | a throwaway context seeded from `OS_GetTick` for a temporary login id | [S: `src/matched/func_ov065_0227876c.c`] |
| `func_021013d0` | autoload_2 | one hand-written LCG step on the tick; keeps only the high 32 bits | [S: `src/matched/func_021013d0.c`] |
| `func_02100cbc` (`DWCi_AUTH_GetNewWiFiInfo`) | autoload_2 | RTC-plus-tick seed, `MATH_Rand16` for the Wi-Fi id and `randomHistory` | [S: `src/matched/func_02100cbc.c`] |
| `func_02100b18` (`DWCi_AUTH_RemakeWiFiID`) | autoload_2 | the same, excluding the previous history value | [S: `src/matched/func_02100b18.c`] |
| `SPLRandom_Next`, `gSPLRandomState` | main | the particle LCG, mul `0x5EEDF715`, add `0x1B0CB173` | [S: `src/matched/func_020fded0.c`] |
| `SPLEmitter_EmitParticles` / `SPLEmitter_EmitChildParticles` | main | its consumers: spawn jitter, rotation, lifetime, frame, colour | [S: `src/matched/func_020fded0.c`, `src/matched/func_020fdc08.c`] |
| `func_020ff994` | main | a third particle-class stream on `g_rng_state` | [S: `src/matched/func_020ff994.c`] |
| `AOSS_Rand` `0x02207cd4` | ov001 | the Wi-Fi setup LCG, seeded from `RTC_GetTime` | [S: `src/matched/AOSS_Rand.c`] |
| `OS_GetLowEntropyData` `0x02116da8` | autoload_2 | an eight-word pool from VCOUNT, tick, MAC, GX status, RTC, mic, touch, RSSI | [S: `src/matched/OS_GetLowEntropyData.c`] |
| `MATH_CalcCRC8` / `CalcCRC16` / `CalcCRC32` | autoload_2 | CRC helpers; the save poller instead calls `func_02050920` | [S: `port/shim/game/savepoll.c`; log: `docs/log/cycle41-gameplay.md` GP45-5; source locator: `src/matched/MATH_CalcCRC8.c`, `src/matched/func_02050920.c`] |

## Data it reads and writes

| address or field | meaning | who writes | who reads |
|---|---|---|---|
| `0x021cb5a0` | **the game's RNG state**, one word | `func_020e930c` (the seed), `func_020e92e8` (every draw) | `func_020e92e8` [E: ORACLE46 `scratchpad/oracle46/runs/o46-F`, `--peek 0x021cb5a0`] |
| `0x021dc7aa` | the town id halfword, `rand(0x7fff) \| 0x8000` | `func_02064244` at pc `0x02064260` | the town record's readers [E: ORACLE46 `scratchpad/oracle46/runs/o46-A`] |
| `MATHRandContext32.x` | 64-bit LCG state | `MATH_Rand32`, `MATH_InitRand32` | `MATH_Rand32` [S: `src/matched/func_ov065_0227ef00.c`] |
| `MATHRandContext16.x` | 32-bit LCG state | `MATH_Rand16`, `MATH_InitRand16` | `MATH_Rand16` [S: `src/matched/func_02100cbc.c`] |
| `gSPLRandomState` | the particle stream's state word | `SPLRandom_Next` | every `SPLRandom_*` accessor [S: `src/matched/func_020fded0.c`] |
| `AOSS_RandState` / `AOSS_RandInited` | `{x, a, c}` plus an init-once flag | `AOSS_Rand` | `AOSS_Rand` [S: `src/matched/AOSS_Rand.c`] |
| `0x04000100` (tick) | the entropy every network seed folds in | timer 0 (the port: `acww_tick_advance`) | `OS_GetTick` [S: `src/matched/OS_GetTick.c`] |
| `0x04000006` (VCOUNT) | one of eight inputs to the entropy pool | the display controller (the port: the DISPSTAT/VCOUNT hook) | `OS_GetLowEntropyData` [S: `src/matched/OS_GetLowEntropyData.c`] |

## How to check it

`../experiments/rng-determinism.md` (designed, not yet run): run the same recipe twice with the
same pinned clock and confirm the screenshots are byte-identical, then move `ACWW_RTC_TIME` by
one second and see whether anything moves. That separates "the port is deterministic" from
"nothing in this scene consumes a clock-seeded draw", which the existing runs cannot.

## Hypotheses

- **SETTLED (ORACLE46).** "The gameplay RNG is a fourth generator, distinct from all three
  above, living in the undecompiled `func_020*` game glue." It is `func_020e92e8` on the state
  word `0x021cb5a0`, and the search missed it because the multiply-add is in a THREE-LINE
  matched file whose state is a caller-supplied pointer, not a static word.
- A town's layout is generated from a seed stored in the save. Settled by the same run twice
  from two fresh `ACWW_SAVE` files under the same pinned clock: identical towns mean the seed
  is not per-save, different towns mean it is (`save-data.md` must persist first). ORACLE46
  leans the first way: the state is seeded from the clock at boot with nothing read from a save.
- **SETTLED for the measured arms: sharing the boot second does not ensure a shared town.**
  ORACLE46's producers share the seed but draw different ids at different stream positions
  [E: `scratchpad/oracle46/RECEIPTS.md`; log: `docs/log/cycle41-gameplay.md` O46-4].
  Matching the id alone also does not pin the later layout/roster burst: the inverse arm
  enters it two draws early, while the forward recipe matches the map and roster
  [E: `scratchpad/oracle49/RECEIPTS.md`; log: `docs/log/cycle41-gameplay.md` O49-2, O49-4, O49-5].
- `OS_GetLowEntropyData` is called only from the Wi-Fi overlay (`func_ov065_02275b94.c`,
  three sites) and by none of the town generators; whether it runs in an offline session
  would be settled by an `ACWW_INTERP_WATCH` on its entry address across a full town run
  (not yet done). The earlier "dead code" wording is retracted (HANDOFF16).
- The port's frame-counted tick and the emulator's cycle-accurate one seed the network
  generators differently, and it does not matter because no network code runs
  [H: log/source account: no DWC or WM symbol is reached on any recorded run; see `network.md`; receipt provenance unresolved].

## Related

- `time-and-rtc.md` -- both entropy sources.
- `save-data.md` -- save checksum and bank acceptance [H: `port/shim/game/savepoll.c`; log: `docs/log/cycle41-gameplay.md` GP45-5 ; provenance unresolved].
- `network.md` -- every SDK generator's only established consumer.

## Who draws (`draw-caller-1`)

The custom START recipe from `promote_record.py`, recorder disabled, frozen RTC, no touch,
stopped at port frame 3000 (exit 100), produces **744 stores: two seed stores and 742 draws**.
The caller watch has 97 distinct keys and no overflow; every return address maps to a
symbol, with overlay residency taken from that run's load log
[E: `scratchpad/handoff/draw-caller-1/census.receipt.json`, `scratchpad/handoff/draw-caller-1/census-summary.json`].

At the bounded RNG's leaf store, LR is `0x020e92dc` in `func_020e92d0`; its validated
saved LR at `sp+4` names the producer. `func_020644cc` tail-calls that bounded draw, so it
does not add a stack frame. A raw leaf call instead identifies its immediate caller in LR;
LR2=0 means unavailable, not a zero-address caller
[H: `port/interp/interp_cpu.c` `watch_lr_parent`; E: `scratchpad/handoff/draw-caller-1/fixture-run.stdout.log` ; provenance unresolved].

**The periodic call is `func_ov068_0226c520`, return address `0x0226c52d`: 118 draws at
828, 831, ..., 1179, exactly one per three frames.** Its first expression unconditionally
draws a bound-5 value once per invocation; subsequent branches do not repeat that site
[S: `src/matched/func_ov068_0226c520.cpp`; E: `scratchpad/handoff/draw-caller-1/caller-events.json`].
The brief's label "title, 759..1600" is not this recipe's scene partition: ORACLE47 calls
759..780 the remaining title (our census also finds zero draws there) and 780..1610 the
taxi conversation. The periodic site covers part of that conversation, alongside other
producers; it does not mean that every frame in the entire requested window has one draw
[E: `docs/log/cycle41-gameplay.md` O47-1; `scratchpad/handoff/draw-caller-1/census-summary.json`].

**The frame-758 burst is 280 draws spread across 61 return sites in 45 functions.** It
includes the town-id draw (`func_0206426c`) and the initial selectors listed below; it is
not 280 calls to one direct producer. The largest direct group is `func_0209ccd4`: 27+9
draws at its two return sites. A separate completed capture measures **36 draws in one
invocation**, matching its 6-by-6 selection loop
[S: `src/matched/func_0209ccd4.c`; E: `scratchpad/handoff/draw-caller-1/probe-summary.json`].
The broad initializer `func_0209ebec` is entered from `func_0209e6ec` at `0x0209e76c`,
but the existing recorder hits its event and 4-million-step caps before observing return;
that probe cannot assign all 280 draws to one enclosing invocation. The exact accounting
below is by direct call site; an enclosing initializer's complete call count remains open
[E: `scratchpad/handoff/draw-caller-1/probe-summary.json`].

All rows watch `0x021cb5a0`, width 4. PC is `0x020e92f8` for draws and `0x020e930c`
for the first two seed rows. "758" counts only that frame; "total" covers 0..3000.
The function column names the LR2 owner when available, otherwise the LR owner; addresses
retain Thumb return bits. Every row is measured in [E: `scratchpad/handoff/draw-caller-1/census-summary.json`, frames 0..3000].

| LR | LR2 | producer function | total | first frame | 758 |
|---|---|---|---:|---:|---:|
| `0x020c5a85` | `0x00000000` | `__sinit_020c5a78` | 1 | 0 | 0 |
| `0x02061541` | `0x00000000` | `func_02061530` | 1 | 3 | 0 |
| `0x020e92dc` | `0x0204126f` | `func_020411fc` | 3 | 758 | 2 |
| `0x020e92dc` | `0x020ae69b` | `func_020ae67c` | 6 | 758 | 4 |
| `0x020e92dc` | `0x020ae05b` | `func_020ae03c` | 6 | 758 | 4 |
| `0x020e92dc` | `0x0206399f` | `func_02063914` | 21 | 758 | 15 |
| `0x020e92dc` | `0x02063a9f` | `func_02063914` | 21 | 758 | 15 |
| `0x020e92dc` | `0x020ae0d9` | `func_020ae03c` | 12 | 758 | 8 |
| `0x020e92dc` | `0x02063fe3` | `func_02063f94` | 8 | 758 | 7 |
| `0x020e92dc` | `0x020ae163` | `func_020ae03c` | 6 | 758 | 4 |
| `0x020e92dc` | `0x0204111b` | `func_02041110` | 12 | 758 | 8 |
| `0x020e92dc` | `0x020410bd` | `func_0204105c` | 6 | 758 | 4 |
| `0x020e92dc` | `0x020ae1c5` | `func_020ae190` | 3 | 758 | 2 |
| `0x020e92dc` | `0x0204e73b` | `func_0204e728` | 1 | 758 | 1 |
| `0x020e92dc` | `0x0209c5c1` | `func_0209c5b0` | 4 | 758 | 4 |
| `0x020e92dc` | `0x0209c7b5` | `func_0209c618` | 4 | 758 | 4 |
| `0x020e92dc` | `0x0209c8a5` | `func_0209c80c` | 4 | 758 | 4 |
| `0x020e92dc` | `0x0209cbbf` | `func_0209cb88` | 12 | 758 | 12 |
| `0x020e92dc` | `0x0209cb13` | `func_0209ca6c` | 1 | 758 | 1 |
| `0x020e92dc` | `0x0209cd37` | `func_0209ccd4` | 27 | 758 | 27 |
| `0x020e92dc` | `0x0209cd99` | `func_0209ccd4` | 9 | 758 | 9 |
| `0x020e92dc` | `0x02064277` | `func_0206426c` | 1 | 758 | 1 |
| `0x020e92dc` | `0x0207cc67` | `func_0207cc54` | 15 | 758 | 15 |
| `0x020e92dc` | `0x0207c97b` | `func_0207c8c8` | 3 | 758 | 3 |
| `0x020e92dc` | `0x0209c4ef` | `func_0209c4a8` | 3 | 758 | 3 |
| `0x020e92dc` | `0x0207f439` | `func_0207f414` | 3 | 758 | 3 |
| `0x020e92dc` | `0x0207d67f` | `func_0207d634` | 3 | 758 | 3 |
| `0x020e92dc` | `0x0207bcab` | `func_0207bbb8` | 3 | 758 | 3 |
| `0x020e92dc` | `0x020b38e9` | `func_020b38dc` | 1 | 758 | 1 |
| `0x020e92dc` | `0x020b38f5` | `func_020b38dc` | 1 | 758 | 1 |
| `0x020e92dc` | `0x020b3935` | `func_020b38dc` | 3 | 758 | 3 |
| `0x020e92dc` | `0x020b398f` | `func_020b38dc` | 1 | 758 | 1 |
| `0x020e92dc` | `0x020b388b` | `func_020b3880` | 1 | 758 | 1 |
| `0x020e92dc` | `0x02064113` | `func_02064108` | 9 | 758 | 9 |
| `0x020e92dc` | `0x0204ce73` | `func_0204ce64` | 1 | 758 | 1 |
| `0x020e92dc` | `0x0204cc57` | `func_0204cc34` | 1 | 758 | 1 |
| `0x020e92dc` | `0x02048433` | `func_02048418` | 1 | 758 | 1 |
| `0x020e92dc` | `0x0204843b` | `func_02048418` | 1 | 758 | 1 |
| `0x020e92dc` | `0x02048445` | `func_02048418` | 3 | 758 | 3 |
| `0x020e92dc` | `0x02048459` | `func_02048418` | 3 | 758 | 3 |
| `0x020e92dc` | `0x02048d43` | `func_02048d2c` | 12 | 758 | 12 |
| `0x020e92dc` | `0x020483e1` | `func_020483c4` | 1 | 758 | 1 |
| `0x020e92dc` | `0x020483e9` | `func_020483c4` | 1 | 758 | 1 |
| `0x020e92dc` | `0x02048b9f` | `func_02048b54` | 4 | 758 | 4 |
| `0x020e92dc` | `0x02048c6f` | `func_02048bc0` | 22 | 758 | 22 |
| `0x020e92dc` | `0x02048b29` | `func_02048b0c` | 2 | 758 | 2 |
| `0x020e92dc` | `0x02048b31` | `func_02048b0c` | 2 | 758 | 2 |
| `0x020e92dc` | `0x020482af` | `func_02048298` | 4 | 758 | 4 |
| `0x020e92dc` | `0x02048325` | `func_0204830c` | 4 | 758 | 4 |
| `0x020e92dc` | `0x020c15dd` | `func_020c15c8` | 2 | 758 | 2 |
| `0x020e92dc` | `0x020875b7` | `func_02087500` | 1 | 758 | 1 |
| `0x020e92dc` | `0x020875cd` | `func_02087500` | 1 | 758 | 1 |
| `0x020e92dc` | `0x020877eb` | `func_020877dc` | 12 | 758 | 12 |
| `0x020e92dc` | `0x0203a615` | `func_0203a5f4` | 3 | 758 | 3 |
| `0x020e92dc` | `0x02086ef5` | `func_02086ee8` | 1 | 758 | 1 |
| `0x020e92dc` | `0x02086f13` | `func_02086ee8` | 1 | 758 | 1 |
| `0x020e92dc` | `0x02086f1b` | `func_02086ee8` | 1 | 758 | 1 |
| `0x020e92dc` | `0x02086f23` | `func_02086ee8` | 1 | 758 | 1 |
| `0x020e92dc` | `0x0207a0a9` | `func_0207a02c` | 2 | 758 | 2 |
| `0x020e92dc` | `0x0204711f` | `func_02047114` | 8 | 758 | 8 |
| `0x020e92dc` | `0x02087fc9` | `func_02087f58` | 1 | 758 | 1 |
| `0x020e92dc` | `0x020878eb` | `func_0208786c` | 1 | 758 | 1 |
| `0x020e92dc` | `0x020879bd` | `func_02087950` | 1 | 758 | 1 |
| `0x020e92dc` | `0x020bb91f` | `func_020bb8e0` | 2 | 822 | 0 |
| `0x020e92dc` | `0x020b1795` | `func_020b177c` | 5 | 822 | 0 |
| `0x020e92dc` | `0x0202e387` | `func_0202e364` | 2 | 822 | 0 |
| `0x020e92dc` | `0x0226d441` | `func_ov068_0226d408` | 2 | 822 | 0 |
| `0x020e92dc` | `0x0226cbd3` | `func_ov068_0226cbc8` | 2 | 822 | 0 |
| `0x020e92dc` | `0x0226ca45` | `func_ov068_0226ca2c` | 2 | 822 | 0 |
| `0x020e92dc` | `0x0201324f` | `func_020131dc` | 2 | 822 | 0 |
| `0x020e92dc` | `0x02082943` | `func_02082904` | 1 | 823 | 0 |
| `0x020e92dc` | `0x0226c52d` | `func_ov068_0226c520` | 118 | 828 | 0 |
| `0x02064627` | `0x00000000` | `func_0206461c` | 22 | 828 | 0 |
| `0x020e92dc` | `0x020645fd` | `func_020645e0` | 22 | 828 | 0 |
| `0x020e92dc` | `0x0204fbb3` | `func_0204fb80` | 7 | 828 | 0 |
| `0x020e92dc` | `0x02227947` | `func_ov003_0222793c` | 13 | 828 | 0 |
| `0x0226bcd9` | `0x00000000` | `func_ov068_0226bc1c` | 8 | 831 | 0 |
| `0x020e92dc` | `0x02012aa9` | `func_02012a98` | 2 | 849 | 0 |
| `0x02012adf` | `0x00000000` | `func_02012a98` | 2 | 849 | 0 |
| `0x020e92dc` | `0x02012af9` | `func_02012a98` | 2 | 849 | 0 |
| `0x020e92dc` | `0x02012b05` | `func_02012a98` | 2 | 849 | 0 |
| `0x020e92dc` | `0x02012b0f` | `func_02012a98` | 2 | 849 | 0 |
| `0x020e92dc` | `0x020b1831` | `func_020b1800` | 9 | 921 | 0 |
| `0x020e92dc` | `0x020b183d` | `func_020b1800` | 9 | 921 | 0 |
| `0x020e92dc` | `0x020b184f` | `func_020b1800` | 8 | 948 | 0 |
| `0x020e92dc` | `0x0222d399` | `func_ov003_0222d388` | 1 | 1005 | 0 |
| `0x020e92dc` | `0x0222d129` | `func_ov003_0222cf60` | 1 | 1005 | 0 |
| `0x020e92dc` | `0x0222c69b` | `func_ov003_0222c68c` | 1 | 1005 | 0 |
| `0x020e92dc` | `0x02230c4f` | `func_ov003_02230c3c` | 1 | 1011 | 0 |
| `0x020e92dc` | `0x02230ccb` | `func_ov003_02230cc0` | 1 | 1011 | 0 |
| `0x020e92dc` | `0x02230c87` | `func_ov003_02230c3c` | 1 | 1011 | 0 |
| `0x020e92dc` | `0x020950df` | `func_020950d4` | 1 | 1182 | 0 |
| `0x020e92dc` | `0x0226dc97` | `func_ov068_0226dc64` | 51 | 1188 | 0 |
| `0x020e92dc` | `0x0226dc3b` | `func_ov068_0226dc08` | 59 | 1188 | 0 |
| `0x020e92dc` | `0x020bb7c5` | `func_020bb7a0` | 1 | 1194 | 0 |
| `0x020e92dc` | `0x0226daf3` | `func_ov068_0226dabc` | 23 | 1230 | 0 |
| `0x020e92dc` | `0x0201a7a3` | `func_0201a798` | 46 | 1392 | 0 |
