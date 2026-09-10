# Events and calendar

**Summary.** The game's calendar is the DS real-time clock read through the NitroSDK, mapped
onto a season by a twelve-arm switch and onto a fourteen-value season/event index by a second
map. What happens on a given day is decided in two places: a day-change routine that runs
once per rollover and rewrites a block of state, and a special-NPC scheduler that runs every
frame -- eleven predicates in priority order over a twenty-three entry table of visitors, each
naming the channel, actor, overlay and flag that would bring that visitor in. The player's own
64-bit event bitfield is the progress record both consult.

## What happens

Date and time come from the SDK: `RTC_GetDateTime`, `RTC_GetTime` and `RTC_GetDate` at
`0x0211e7c0` and its neighbours [S: NitroSDK, port/shim/os/rtcclock.c]. The game also SETS the
clock: `func_0209e5b4` calls `RTC_SetDateTime(date, time)` with `r1` untouched across the call,
so the time pointer is carried in flight
[S: func_0209e5b4, main, port/shim/game/arity_func_0209e5b4.c]. That path contains a date check
that forces weekday 6 for year 0 / month 1 / day 1, which corroborates that `r0` is the date
[S: port/shim/game/arity_func_0209e5b4.c].

The day change itself is `func_02040c90`. Its seventeen calls line up one for one with the
disassembly, in order: `func_0209e474`, `func_0209ded0`, `func_0209e314`, `func_020409c8`
(twice), `func_0204101c`, `func_02041140`, `func_02040e44`, `func_02040f8c`, `func_02040f04`,
`func_02040da8`, `func_02040bcc`, with five interleaved `MI_CpuCopy8` calls anchoring the
middle of the sequence, over one global at `0x021c7584`
[S: func_02040c90, main, port/tools/known_callees.txt:245-264]. One of those callees is a naming
hazard: `0x0209ded0` carries no `func_` symbol — the table names it `MB_GetBeaconRecvStatus`, a
multiboot name that cannot be right for a day-change callee, so the cut or the label is wrong
there (defect class D12) [S: `config/adm-kr/arm9/symbols.txt`, `MB_GetBeaconRecvStatus` addr
`0x0209ded0`; `docs/rules/D-defects.md` D12]. The five block copies are the shape of
a day rollover that shifts yesterday's state into a history slot before writing today's
[H: read `func_02040c90`'s disassembly and name the source and destination of each copy].

Season is a pure function of month and day (`func_02063bb4`), and a second map
`func_0204fa8c` turns the month into a fourteen-value index in which August and September each
split in two -- both are documented on `weather-and-seasons.md`
[S: func_02063bb4 / func_0204fa8c, main, port/shim/game/season.c and seasonidx.c].

New-game generation and the calendar are coupled: the town dispatcher's generation handler is
followed by "the RTC advance that moves villagers in", then a post-generation sync mirroring
`func_020a1038`'s save-erase path
[S: func_0209e6ec, main, port/shim/gfx/pmflist.c]. So a fresh town gets its residents by
running the day-change machinery forward, not by a separate move-in routine
[S: port/shim/gfx/pmflist.c].

The player's 64-bit event bitfield at `player + 0x23f8` is the progress record. `func_02099020`
tests a bit and `func_02098ff8` sets one
[S: main, port/shim/game/spnpc.c]. Flag 1 is the arrival sequence: set by all four new-game
commits, cleared only by `func_ov050_02262628` (Nook's side) and `func_ov068_0226e948`
[S: port/shim/game/spnpc.c, port/shim/game/newgameprobe.c].

The special-NPC scheduler is the game's visitor calendar and it is worth reading as one
mechanism. Channel `0xd0` builds an object whose vtable is `0x020e1cc0`; its per-frame slot 0
is `func_02085558`, which calls `func_02084c60(self)` -- an eleven-entry PMF/priority table at
`0x020e1d08` [S: func_02085558 / func_02084c60, main, port/shim/game/spnpc.c]. Entry 0 is
`func_02084834 -> func_02084840(1)`, whose gate is `func_02084890`
[S: main, port/shim/game/spnpc.c]. `func_02084890` is a conjunction of four sub-results and
returns 1 only when the first, third and fourth are ZERO and the second is non-zero:
`func_02073dd4(data_020ccf94, data_020ccf94->field_64)`,
`func_02086108(func_0208602c(), 8)`, `func_02084ad0()` and `func_02084af0()`
[S: func_02084890, main, port/shim/game/spnpc.c].

`func_02084af0` is `player && func_02099020(player, 1)` -- the arrival flag -- and every one of
the eleven predicates bails while it is set, so the entire visitor schedule is silent BY
DESIGN during the opening [S: func_02084af0, main, port/shim/game/spnpc.c]. That is a real
mechanic and not a port defect [S: port/shim/game/spnpc.c].

Past the gate, `func_02084840` applies two further tests when its parameter is non-zero: it
requires the indoor/outdoor byte `data_020e54a8` to be 0 and the mode from `func_020b65c4` not
to be `0x2c` [S: func_02084840, main, port/shim/game/spnpc.c]. `data_020e54a8` is the same
byte `func_02085558` dispatches on, with non-zero taking the INTERIOR branch, so a scheduled
visitor cannot be staged from inside a building
[S: func_02085558, main, port/shim/game/spnpc.c].

Staging is `func_02084d34(&data_020e1b84, &data_020e1d8c, data_020d0644)`, where
`*(u16 *)0x020e1b84` is the key -- observed as `0x0056` -- and `data_020e1d8c` is a
TWENTY-THREE entry table whose entry 0 reads `{channel 0x0056, actor 0xd012, overlay 0x50,
pmf, flag 1}` [S: func_02084d34, main, port/shim/game/spnpc.c]. Acting on a staged request is
`func_02084b74(self, &data_020e1d8c, 0x17)` -- `0x17` being the table's 23 entries -- which
mounts the overlay with `func_0204f934(0x50)` and opens the channel with
`func_02003348(86, 0xd012, ...)`
[S: func_02084b74, main, port/shim/game/spnpc.c]. So each of the 23 rows is one special
visitor with everything needed to bring them in
[S: port/shim/game/spnpc.c].

The same table is reached from a second entry point: `func_020842b8` ends in
`func_02084d5c(&v, &data_020e1d8c, data_020d0644)` after a three-call chain
(`func_0208602c -> func_020860c4 -> func_02087f30`) that threads one register through all
three and reads `0x021d27c0` [S: func_020842b8, main, port/shim/game/eventgate.c].

The firmware's own birthday fields -- `birthMonth` at `+0x03`, `birthDay` at `+0x04` of the
user-settings record -- are read by the game, which is why the port supplies a valid date
rather than leaving them zero and says so [H: host/prose inference from port/shim/boot/usersettings.c; verify against the ROM function or symbol table and this page's recipe].

## Where it lives

| function or symbol | module | role | grade/citation |
|---|---|---|---|
| `RTC_GetDateTime` (`0x0211e7c0`) | main/SDK | the clock the calendar reads | S: port/shim/os/rtcclock.c |
| `func_0209e5b4` | main | `RTC_SetDateTime(date, time)` wrapper | S: port/shim/game/arity_func_0209e5b4.c |
| `func_02040c90` | main | day-change / calendar update, 17 calls | S: port/tools/known_callees.txt |
| `func_02063bb4` | main | month + day -> season | S: port/shim/game/season.c |
| `func_0204fa8c` | main | month -> 14-value season/event index | S: src/matched/func_0204fa8c.c |
| `func_02084c60` | main | 11-entry special-NPC decider table `0x020e1d08` | S: port/shim/game/spnpc.c |
| `func_02084890` | main | the four-term gate on entry 0 | S: port/shim/game/spnpc.c |
| `func_02084af0` | main | `player && event flag 1` -- the arrival lock | S: port/shim/game/spnpc.c |
| `func_02084840` | main | stages a visitor; interior and mode tests | S: port/shim/game/spnpc.c |
| `func_02084d34` | main | reads the key and picks a table row | S: port/shim/game/spnpc.c |
| `func_02084b74` | main | acts: mounts overlay, opens channel | S: port/shim/game/spnpc.c |
| `func_020842b8` | main | second entry into the same visitor table | S: port/shim/game/eventgate.c |
| `func_02099020` / `func_02098ff8` | main | test / set an event flag | S: port/shim/game/spnpc.c |

## Data it reads and writes

| address or field | meaning | who writes | who reads |
|---|---|---|---|
| `player + 0x23f8` | 64-bit event bitfield | `func_02098ff8`, the four commits | `func_02099020` |
| event flag 1 | the arrival sequence is running | new-game commits | all 11 predicates |
| `0x020e1d08` | 11 PMF/priority deciders | static | `func_02084c60` |
| `0x020e1d8c` | 23 visitor rows `{chan, actor, overlay, pmf, flag}` | static | `func_02084d34`, `func_02084b74` |
| `0x020e1b84` | the staged visitor key (`0x0056` observed) | `func_02084d34` | `func_02084b74` |
| `data_020e54a8` | indoor (non-zero) / outdoor (0) | scene | `func_02084840`, `func_02085558` |
| `data_020e54ac` | the game mode byte | mode machine | `func_020b65c4` callers |
| `0x021c7584` | the day-change routine's only global | `func_02040c90` | day-change consumers |
| `0x021d27c0` | the word `func_020842b8`'s chain reads | `func_0208602c` family | `func_02087f30` |
| firmware `+0x03` / `+0x04` | birth month / day | firmware | greeting paths |

All rows are S, cited from the files in the previous table.

## How to check it

`port/shim/game/spnpc.c` prints the whole gate as one packed word -- why it declined (0 staged,
1 gate said no, 2 interior, 3 mode `0x2c`), the gate bit, the four sub-results, the
indoor/outdoor byte and the mode -- and only on a change, so a run that never moves prints one
line [H: host/prose inference from port/shim/game/spnpc.c; verify against the ROM function or symbol table and this page's recipe]. Beside it, `acww intro:` prints the player pointer, both
bitfield words, flag 1 and the mode
[H: host/prose inference from port/shim/game/spnpc.c; verify against the ROM function or symbol table and this page's recipe]. Both need `ACWW_TRACE_STATE=1`
[H: host/prose inference from port/shim/game/spnpc.c; verify against the ROM function or symbol table and this page's recipe].

To exercise the calendar rather than the schedule, set the clock with the `ACWW_RTC_*`
instruments and step across a midnight; `ACWW_RTC_TIME=000000` is explicitly distinguished
from "no value given" [H: host/prose inference from port/platform/win32.c, port/shim/os/rtcclock.c; verify against the ROM function or symbol table and this page's recipe].

## Hypotheses

- **H: the 23 rows at `0x020e1d8c` are the game's full roster of special visitors (Kapp'n,
  Nook, Redd, Gulliver, Katrina, Wendell, Saharah, Gracie, Joan, Pete, Phyllis, Copper,
  Booker, Blathers, Tortimer and the rest), one row each.** Each row already carries channel,
  actor, overlay and a flag [S: port/shim/game/spnpc.c], and ov068's own pool names twelve
  special-NPC models `rcn, rcc, rcs, rcd, pga, pgb, poo, ott, wip, xct, mof, end`
  [S: docs/kb/modules/ov003-068.md]. Experiment: dump the 23 rows, resolve each overlay id,
  and read each overlay's pool for the model name it loads.
- **H: the eleven predicates at `0x020e1d08` are eleven SCHEDULING RULES in priority order
  (today's date, a weekday rule, a holiday rule, a random visitor rule ...), each of which may
  stage at most one visitor per day.** The table is described as PMF/priority
  [S: port/shim/game/spnpc.c]. Experiment: instrument each of the eleven and log which fires
  across seven simulated days.
- **H: holidays are rows of a date table consulted by one of those eleven predicates, and
  `func_0204fa8c`'s fourteen-value index is that table's row selector.** The index splits
  exactly the two months where a real holiday falls late
  [S: port/shim/game/seasonidx.c]. Experiment: find the consumer of `func_0204fa8c`'s result
  besides `func_0204fb80` and read its table.
- **H: birthdays are read from the villager record and compared against the RTC date once per
  day inside `func_02040c90`.** The routine is the only per-day rewrite found so far
  [S: port/tools/known_callees.txt]. Experiment: set the RTC to a known villager's birthday
  and diff the eight records at `0x021e5a2c` across the rollover.
- **H: the five `MI_CpuCopy8` blocks in `func_02040c90` shift "yesterday" into "the day
  before" for five separate subsystems (weather, shop stock, visitor, turnip price, mail).**
  Five copies, five subsystems that all need a previous value
  [S: port/tools/known_callees.txt]. Experiment: name each copy's source and destination and
  match them against the save layout.
- **H: `func_02084ad0`, the third gate term, is "a special NPC is already present", which is
  why it must be zero.** It is called with no arguments and its result must be 0 for the gate
  to pass [S: port/shim/game/spnpc.c]. Experiment: read `func_02084ad0` and log it while a
  visitor's channel is open.

## Related

- `weather-and-seasons.md` -- the season the same date produces
- `player.md` -- the event bitfield in detail
- `villagers.md` -- move-in is driven by the RTC advance
- `dialogue.md` -- what a scheduled visitor says once staged
