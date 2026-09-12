# Weather and seasons

**Summary.** The season is a pure function of the calendar date -- a twelve-entry jump table
on the month, with only four of the twelve months testing the day at all, and the boundaries
falling on the 25th of February and the 27th of May, August and November. Season and weather
together select a ROW of a day/night colour table; the hour selects a PAIR of `0x20`-byte
banks inside that row, one for a.m. and one for p.m.; and the game blends the current hour's
bank into the next hour's by two weights, so the sky and the lighting move continuously rather
than in steps. Seasonal appearance also shows up as `w`/`s`/`f` texture variants on the town's
own models, and the snowman is a whole channel of its own.

## What happens

`func_02063bb4(month, day)` returns the season as 0, 1, 2 or 3. It is one `switch` -- `cmp
r0,#0xb` followed by a twelve-entry Thumb jump table at `0x02063bc6`, each entry sign extended
and added to `0x02063bc6`, with `bhi` sending anything above 11 to the first target, which is
why month 0 and the default give the same answer
[S: func_02063bb4, main, port/shim/game/season.c]. The arms are: month 1 -> 3; month 2 ->
3 if `day <= 24` else 0; months 3 and 4 -> 0; month 5 -> 0 if `day <= 26` else 1; months 6 and
7 -> 1; month 8 -> 1 if `day <= 26` else 2; months 9 and 10 -> 2; month 11 -> 2 if
`day <= 26` else 3; month 12 and the default -> 3
[S: func_02063bb4, main, port/shim/game/season.c]. Reading the codes off the calendar, 3 is
winter, 0 spring, 1 summer and 2 autumn, and only every third month tests the day, which is
why arms 3/4, 6/7 and 9/10 share a jump target
[S: func_02063bb4, main, port/shim/game/season.c].

Note the symbol-table hazard on this function: the dsd table calls only its first `0x2a` bytes
`func_02063bb4` and files everything past the jump table as eleven separate two-to-ten-byte
symbols (`func_02063be4` ... `func_02063c20`), each a fragment of one case arm
[S: main symbols.txt, port/shim/game/season.c]. Anyone reading a season fragment in isolation
is reading a piece of a switch, not a function.

A second, finer map exists beside the season. `func_0204fa8c(month)` returns an index in a
larger space: months 1..7 return the month unchanged (the ROM branches straight to the
epilogue with `r0` never rewritten); month 8 returns 8 or 9 depending on
`func_0204fafc` applied to a byte from `func_0209df94`; month 9 returns 10 or 11 on the same
test inverted; months 10..12 return `month + 2`; anything else returns 1
[S: func_0204fa8c, main, src/matched/func_0204fa8c.c and port/shim/game/seasonidx.c]. So
twelve months map onto fourteen indices, with August and September each splitting in two --
a late-summer and a late-September variant that the plain season code does not distinguish
[S: func_0204fa8c, main, port/shim/game/seasonidx.c]. The result indexes `func_0204fb80`'s
table of tables at `0x020dc8b4` [S: func_0204fb80, main, port/shim/game/exprpick.c].

Sky and lighting are one mechanism. `func_020bba14` is the only filler of the day/night colour
table at `0x021f6cf0`, and everything visible in the town's colour comes through it: the
rasteriser modulates each texel by the lit vertex colour, which comes from the NNS glb light
colours, which come from the light manager's elements (channel 7, vtable `0x020de710`,
flushed by `func_02065938`), whose elements sample `func_020bbf00` = that table
[S: func_020bba14, main, port/shim/game/envlight.c]
[H: log/source account: port/BOOT-STATE.md, glb light words all four black before the repair; receipt provenance unresolved].

Decoded instruction by instruction, `func_020bba14` does this
[S: func_020bba14, main, port/shim/game/envlight.c]:

- `func_020bbb6c(0x021f75b0, &w1, &w2)` produces two interpolation weights out of the clock;
- `func_0209def4(clock)` writes the hour into `clock[1]`;
- the hour is split into `(hour % 12, am/pm)` for this hour and for the next hour mod 24;
- `row = table_020d2364[*(u32 *)0x021f8ad4]` -- the current sky row, selected by season and
  weather;
- `pair = (void **)(0x021f8af4 + row * 8)` -- `{am bank, pm bank}`, `0x20` bytes per hour;
- the current hour's entry is blended into the next hour's into buffer 0 of the three
  `0x20`-byte buffers at `0x021f8b14` (allocated by `func_020bbcfc`); when the NEXT ROW
  differs, that row is blended into buffer 1 and the two rows into buffer 2 by `w2`;
- `func_020bb18c(0x021f6f70, 0 or 1, the halfword at `+8` or `+0xa` of the result, 0 or 0xc0)`;
- `func_020bbf0c(w1, w2)` fills the light-colour table at `0x021f6cf0`.

Two weights and two blends is the shape that matters: the game interpolates BOTH across the
hour and across a row change, so a season or weather transition is not a hard cut
[S: func_020bba14, main, port/shim/game/envlight.c].

The environment object's init `func_020baa28` (vtable `0x020e69a4`, slot 0) loads four
`/sky/*_bg_ncl.bin` palettes; when its five globals were mis-bound those loads ran with NULL
names and the whole town composed black
[S: func_020baa28, main, port/BOOT-STATE.md]
[H: log/source account: port/BOOT-STATE.md, 38-42k pixels blended with full alpha and zero colour; receipt provenance unresolved].

The hour drives the sky's appearance directly and visibly: with the clock reading 4 a.m. the
title's sky is a starfield [H: log/source account: port/BOOT-STATE.md, `acww envlight: hour 0x00000004`; receipt provenance unresolved]. In the
town, the sky is a separate affine background: engine B in mode 1 with BG3 affine
(`BG3CNT = 0x6f02`), and once affine layers were rendered the clouds appeared
[E: docs/log/cycle40-keyboard-gate-probe.md SKY40, `tap-D57` frame 37800; `scratchpad/cycle40/runs/tap-D57`].

Weather state itself is reset by `func_02035dcc`, which every ROM caller invokes as
`*(0x021c526c) + 0x2d0` -- so weather is a `0x2d0`-offset substructure of the field object
[S: func_02035dcc, main, port/shim/game/weather.c]. Its callers are `func_02041c88` and
`func_020b90cc -> func_0208a2d8 -> func_020f44f8`
[S: main, port/shim/game/weather.c]. The field object's own init `func_02034d14` (vtable
`0x020da334`, slot 0) stores its `+0x50` into `0x021c526c`
[S: func_02034d14, main, port/shim/game/fieldptr.c].

Snow is a channel, not an effect: channel 189 is the SNOWMAN, binding
`/snowman/snowball1.nsbmd` (model `SNW0`, id `0x022383ac`) and `/snowman/snow_face.nsbmd`
(model `SNW1`, id `0x022383c8`), and ov003 also names `sp_npc_snowman` in its own pool
[H: log/source account: port/BOOT-STATE.md, bind log; receipt provenance unresolved] [H: source account: ov003 pool words, docs/kb/modules/ov003-068.md; direct ROM-source provenance unresolved]. A
53-polygon curved surface that a long line of work treated as terrain turned out to be a
snowball [H: log/source account: port/BOOT-STATE.md, "CHANNEL 189 IS THE SNOWMAN"; receipt provenance unresolved].

Rain is NOT a file. `m_rainA`, `m_rainB` and `m_splash` are model node or animation names
inside the already-loaded `obj_taxi` model, and a filesystem search for `*rain*` returns only
twelve BMG message files -- so there is no missing rain asset and nobody should hunt one
[H: host/prose inference from port/VISIBLE-STATE.md, filesystem search; verify against the ROM function or symbol table and this page's recipe]. ov003's pool names them beside the taxi objects
[H: source account: ov003 pool words, docs/kb/modules/ov003-068.md; direct ROM-source provenance unresolved]. The rain IS visible in the taxi interior
on the interpreter path at frame 4,500
[E: docs/log/cycle40-keyboard-gate-probe.md GX40, off-D51; `scratchpad/cycle40/runs/off-D51`].

Seasonal appearance also lives in the assets: ov003's texture names carry `w`/`s`/`f`
variants [H: source account: ov003 pool words, docs/kb/modules/ov003-068.md; direct ROM-source provenance unresolved].

## Where it lives

| function or symbol | module | role | grade/citation |
|---|---|---|---|
| `func_02063bb4` | main | month + day -> season 0..3 (12-entry jump table) | S: port/shim/game/season.c |
| `func_0204fa8c` | main | month -> 14-value season/event index | S: src/matched/func_0204fa8c.c |
| `func_0204fafc` / `func_0209df94` | main | the August/September split test and its input byte | S: port/shim/game/seasonidx.c |
| `func_020bba14` | main | builds the day/night colour table | S: port/shim/game/envlight.c |
| `func_020bbb6c` | main | two interpolation weights from the clock | S: port/shim/game/envlight.c |
| `func_0209def4` | main | reads the hour into `clock[1]` | S: port/shim/game/envlight.c |
| `func_020bbf0c` | main | fills the light-colour table `0x021f6cf0` | S: port/shim/game/envlight.c |
| `func_020bbf00` | main | the sampler the light elements read | S: port/shim/game/envlight.c |
| `func_020baa28` | main | environment object init; four `/sky/*_bg_ncl.bin` loads | S: port/BOOT-STATE.md |
| `func_02065938` | main | flushes the light manager's elements (channel 7) | S: port/BOOT-STATE.md |
| `func_02035dcc` | main | weather reset over field `+0x2d0` | S: port/shim/game/weather.c |
| `func_02034d14` | main | field object init; publishes `0x021c526c` | S: port/shim/game/fieldptr.c |

## Data it reads and writes

| address or field | meaning | who writes | who reads |
|---|---|---|---|
| `0x02063bc6` | 12-entry Thumb jump table of season arms | static | `func_02063bb4` |
| `0x020dc8b4` | table of tables indexed by the season/event index | static | `func_0204fb80` |
| `0x021f8ad4` | the sky ROW selector (season and weather) | weather/season update | `func_020bba14` |
| `table_020d2364` | row index -> row | static | `func_020bba14` |
| `0x021f8af4 + row*8` | `{am bank, pm bank}`, `0x20` bytes per hour | static | `func_020bba14` |
| `0x021f8b14` | three `0x20`-byte blend buffers | `func_020bbcfc` allocates | `func_020bba14` |
| `0x021f6cf0` | day/night light-colour table | `func_020bbf0c` | `func_020bbf00` -> channel 7 |
| `0x021f6f70` | the two-halfword sky colour target | `func_020bb18c` | render |
| `0x021c526c` | field-data pointer; weather at `+0x2d0` | `func_02034d14` | `func_02035dcc` |
| `0x021f75b0` | the clock/environment object the weights come from | env init | `func_020bbb6c` |

All rows are S, cited from the files in the previous table.

## How to check it

Season is checkable without running anything: read the twelve jump-table entries at
`0x02063bc6` in `arm9.bin` and confirm they resolve to `0x2063c1e, 0x2063bde, 0x2063be2,
0x2063bee, 0x2063bee, 0x2063bf2, 0x2063bfe, 0x2063bfe, 0x2063c02, 0x2063c0e, 0x2063c0e,
0x2063c12` [S: main, port/shim/game/season.c]. One arm compares against `0x18` (February) and three against `0x1a` (May, August,
November), which is the whole day-boundary rule
[S: main, port/shim/game/season.c].

For the sky, run with `ACWW_RTC_*` set to different hours and watch
`acww envlight: hour <h>`; the title's sky is a starfield at hour 4
[H: log/source account: port/BOOT-STATE.md; receipt provenance unresolved]. For the town's sky specifically, the town recipe's frame 37,800
shows clouds over blue [E: docs/log/cycle40-keyboard-gate-probe.md SKY40, `tap-D57`; `scratchpad/cycle40/runs/tap-D57`].

## Hypotheses

- **H: `0x021f8ad4` is a combined `(season, weather)` index rather than a weather-only one,
  and `table_020d2364` is the flattening table.** The double indirection -- a word at
  `0x021f8ad4`, through `table_020d2364`, to a row -- is exactly what a two-dimensional
  lookup collapsed into one dimension looks like
  [H: source account: port/shim/game/envlight.c; direct ROM-source provenance unresolved]. Experiment: force `func_02063bb4`'s result to each of 0..3
  with the same date and record `*(u32 *)0x021f8ad4` and the resulting row.
- **H: weather is chosen once per day from a per-season probability table, not per frame.**
  `func_02035dcc` is a RESET rather than a chooser, and its callers are transition points
  [H: source account: port/shim/game/weather.c; direct ROM-source provenance unresolved]. Experiment: instrument every write to `0x021f8ad4` over a
  three-day `ACWW_RTC_*` run and count them; one write per day rollover supports the
  hypothesis.
- **H: the `w`/`s`/`f` texture suffixes are winter / summer / fall, with spring being the
  unsuffixed default.** Three suffixes for four seasons is the tell
  [H: source account: docs/kb/modules/ov003-068.md; direct ROM-source provenance unresolved]. Experiment: log every `/bg/t%d/%04x.nsbtx` and
  `/fg/**` open with the season forced to each of 0..3 and compare the name sets.
- **H: the August and September splits in `func_0204fa8c` are the two fireworks/festival
  windows, and `func_0204fafc` tests a day-of-month or day-of-week condition on the byte
  `func_0209df94` returns.** Only those two months split
  [S: `src/matched/func_0204fa8c.c`; historical account: port/shim/game/seasonidx.c]. Experiment: decompile `func_0204fafc` and `func_0209df94`
  and evaluate the pair over all 365 dates.
- **H: rain is drawn by the taxi/field model's own `m_rainA`/`m_rainB` nodes being enabled by
  the weather state, not by a particle system.** They are nodes inside a loaded model
  [H: source account: port/VISIBLE-STATE.md; direct ROM-source provenance unresolved]. Experiment: force the weather word to each value in the town and
  count large translucent polygons per frame.
- **H: the snowman channel (189) is opened by the weather/season update when the season is
  winter and snow has accumulated, not by the field scene unconditionally.** The channel
  exists and binds snow models [H: log/source account: port/BOOT-STATE.md; receipt provenance unresolved]. Experiment: run the town recipe with
  the RTC set to January and to July and record whether channel 189 opens.
- **H: the two weights `func_020bbb6c` returns are (minutes-into-the-hour) and
  (progress-through-a-row-transition), and the second is what makes a season change fade over
  more than one day.** The second weight is used only for the two-row blend
  [H: source account: port/shim/game/envlight.c; direct ROM-source provenance unresolved]. Experiment: log `w1` and `w2` across an hour boundary and
  across a season boundary.

## Related

- `town.md` -- the acre textures the season selects between
- `events-and-calendar.md` -- the date that feeds `func_02063bb4`
- `villagers.md` -- the same `0x020dc8b4` table drives villager expressions
