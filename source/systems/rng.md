# Random numbers

**Summary.** There is no single random number generator in this ROM. Three unrelated linear
congruential generators are present in the matched sources: NitroSDK's `MATH_Rand16` and
`MATH_Rand32`, used by the networking code; the SPL particle library's own generator, used for
visual jitter; and a bespoke one in the Wi-Fi setup overlay. Every one of them is seeded from
the hardware tick counter, the real-time clock, or both. **The generator the game itself uses
for gameplay outcomes -- fish, bugs, villagers, shop stock -- has not been found**, because the
functions that would consume it are not decompiled yet. This page records what is established
and is explicit about the hole.

## What happens

**A naming note this page needs.** `MATH_Rand16`, `MATH_Rand32`, `MATH_InitRand16/32` and
`OS_IsTickAvailable` are NitroSDK library names, not names in this ROM's symbol tables: no such
symbol exists in any `config/adm-kr/arm9/**/symbols.txt`, and every one of them is reached in
`src/matched/` under a `func_*` name [S: `config/adm-kr/arm9/**/symbols.txt`, name sweep].
They are used here because `../STYLE.md` rule 2 allows SDK names, and the `func_*` name is given
alongside wherever one exists.

### The SDK generators

`MATHRandContext32` is a three-field structure -- state, multiplier, addend, all 64-bit -- and
`MATH_Rand32` advances it as `x = mul * x + add`, returning the top 32 bits of the new state, or
`(top32 * max) >> 32` for a bounded draw
[S: `MATH_Rand32`, ov065, `src/matched/func_ov065_0227ef00.c`]. The constants are multiplier
`0x5D588B656C078965` and addend `0x269EC3`; the multiplier is written in the sources as
`(1566083941 << 32) + 1812433253` [S: same].

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

There is also an entropy pool nobody in the matched corpus is shown consuming.
`OS_GetLowEntropyData` fills eight words from VCOUNT (`0x04000006`) combined with
`OS_GetTickLo`, the 64-bit tick XORed with MAC bytes and the VBlank counter, the geometry
engine's status register at `0x04000600`, the RTC bytes in low WRAM, microphone data, touch
panel state and the Wi-Fi RSSI pool [S: `OS_GetLowEntropyData`, autoload_2,
`src/matched/OS_GetLowEntropyData.c`]. It reads as available infrastructure rather than as
something wired into any of the generators above [S: absence of callers in `src/matched`].

### What has not been found

No save-side or town-side seed field. Searches across `src/matched` for `SaveData`, `TownData`,
`randomSeed`, `worldSeed`, `townSeed` and the like return nothing, and every seeding observed
is either session-transient or a single lazily-initialised global that is never shown being
written to or restored from a save block [S: absence in `src/matched`]. That is a statement
about the corpus, not about the game: the gameplay systems that would plausibly consume a
per-town seed -- villager behaviour, fish and bug spawns, shop stock, the town's own layout --
are not decompiled into `src/matched` at all, so their RNG plumbing is simply not visible yet.

Nor is there a save checksum in evidence. Every `crc`/`checksum` symbol in the corpus
(`MATH_CalcCRC8` at `0x02128ac4`, `MATH_CalcCRC16` at `0x02128a90` with poly `0xA001`,
`MATH_CalcCRC32` at `0x02128a58` with poly `0xEDB88320` and inverted output, plus
`MBi_calc_cksum` and `check_tcpudpsum`) belongs to the wireless, socket or PPP/TCP stack, and
no call edge runs from any of them into the save path [S: absence of call edges in
`src/matched`; see `save-data.md`].

### The port

The port does not touch any of these generators: they are ROM code and run interpreted like the
rest [E: `docs/kb/hybrid/runtime.md`'s registry policy; `scratchpad/cycle40/runs/tap-D56`]. Its
one relevant effect is that the two entropy sources are *pinned*. The tick advances exactly
8,728 counts per frame from zero [E: `port/platform/tick.c`], and the RTC is a fixed instant
[E: `port/shim/os/rtcclock.c`]. A port run is therefore deterministic in every generator seeded
from either, which is what makes the frame-by-frame oracle comparison meaningful at all
[O: `scratchpad/oracle/tap-fullpad/compare-vs-tap-D56.txt`, where the two producers agree to
whole-frame ncc 0.9920-0.9959 from 6000 to 24000].

## Where it lives

| function or symbol | module | role | grade/citation |
|---|---|---|---|
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
| `MATH_CalcCRC8` / `CalcCRC16` / `CalcCRC32` | autoload_2 | CRC helpers; used by the network stack, not by the save | [S: `src/matched/MATH_CalcCRC32.c`] |

## Data it reads and writes

| address or field | meaning | who writes | who reads |
|---|---|---|---|
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

- The gameplay RNG is a fourth generator, distinct from all three above, living in the
  undecompiled `func_020*` game glue. Settled by finding a caller of a multiply-add on a static
  word inside the ov004 or main game code, which no search in `src/matched` has yet produced
  [S: absence].
- A town's layout is generated from a seed stored in the save. Settled by the same run twice
  from two fresh `ACWW_SAVE` files under the same pinned clock: identical towns mean the seed
  is not per-save, different towns mean it is (`save-data.md` must persist first).
- `OS_GetLowEntropyData` is dead code in this ROM. Settled by an `ACWW_WATCH` on its entry
  address across a full town run.
- The port's frame-counted tick and the emulator's cycle-accurate one seed the network
  generators differently, and it does not matter because no network code runs
  [E: no DWC or WM symbol is reached on any recorded run; see `network.md`].

## Related

- `time-and-rtc.md` -- both entropy sources.
- `save-data.md` -- where a per-town seed would live, and why no checksum has been found.
- `network.md` -- every SDK generator's only established consumer.
