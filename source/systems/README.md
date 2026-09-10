# Systems

How the game behaves. Every page follows `../STYLE.md`: a grade and a citation on every
factual sentence, a Hypotheses section that is the queue of experiments the page is asking
for.

## Written

- [`town.md`](town.md) -- acres, the 96x96 tile grid, generation from the save rather than a
  seed, the item layer, the cylinder world, the town name
- [`villagers.md`](villagers.md) -- the eight house records, the six-class pick, the spawn
  chain and the actor manager, faces and expressions
- [`player.md`](player.md) -- the four player slots, the 64-bit event bitfield, the name
  keyboard, the per-frame movement intent
- [`economy.md`](economy.md) -- item ids and their category nibble; Bells, prices, the turnip
  market and the catalogue are open questions and the page is mostly Hypotheses
- [`weather-and-seasons.md`](weather-and-seasons.md) -- the season switch, the fourteen-value
  month index, the sky row and the hour blend, snow and rain
- [`events-and-calendar.md`](events-and-calendar.md) -- the RTC, the day-change routine, the
  eleven scheduling predicates and the twenty-three visitor rows
- [`dialogue.md`](dialogue.md) -- the five-entry talk table, the request/latch state bytes,
  the script bind, choice prompts and the two keyboards

---

## Written (hardware-facing systems)

These six were listed as "planned" by the first pass and were written by the hardware-systems
pass; nothing under `systems/` is unwritten now.

| page | what it answers |
|---|---|
| [`time-and-rtc.md`](time-and-rtc.md) | the RTC request protocol, the BCD decode, the day catch-up loop, the tick timer, and the port's frame-driven clock (it ADVANCES since RTC42; 2005-06-15 10:00:00 is the boot instant, not a freeze) |
| [`save-data.md`](save-data.md) | the 256 KB flash, the two `0x173fc`-byte banks, request types 6/7/9, the 256-byte page loop, the port's opt-in `ACWW_SAVE` store, and the save the game writes itself once the move-in mode word clears |
| [`input-and-touch.md`](input-and-touch.md) | the two pad registers and the `0x2fff` mask, the nine-entry touch ring, the calibration, `TP_POINT` at `0x021fbde8`, and the measured one-pixel / one-to-two-frame difference from the original |
| [`rng.md`](rng.md) | three unrelated LCGs with their constants, both entropy sources, and the fact that the gameplay generator has not been found |
| [`network.md`](network.md) | the local-wireless and Wi-Fi Connection stacks, what `ov065` is made of, friend codes, and why the port answers all of it with "no service" |
| [`audio.md`](audio.md) | the one 10.7 MB archive, the PXI tag-7 command protocol, the shared-work layout, and the host ARM7 driver that plays it (`ACWW_SND=1`) |

Every page here has a Hypotheses section and links to a page under `../experiments/`. The
experiment index is `../experiments/README.md`, which splits them into run and designed-not-yet-
run; nine are run as of 2026-09-10 and three are still designed
[S: `../experiments/README.md`, its two tables].
