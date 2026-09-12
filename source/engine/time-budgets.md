# Time budgets and other millisecond clock users

**Read this when** judging a sub-frame clock model or asking which ROM loops actually slice work.

**Summary.** Thirty-two aligned clock-conversion literals are not thirty-two work budgets.
Four sites form the loader's shared 40 ms slicing chain, including the channel-list walk.
The other sites implement clock getters, configuration, alarms, event gates, delays and
network timeouts. A finer clock can affect these in different ways; it does not make every
listed function yield into another frame.

## What happens

An independent aligned-word scan found 32 sites in 31 functions: main 6, autoload_2 9,
ov001 1, ov065 13 and ov066 3, agreeing with LOAD52. All 32 have a PC-relative literal
load in their owning symbol interval; the inventory retains input/source SHA-256 hashes,
addresses and load addresses, but no extracted bytes or disassembly.
[H: `scratchpad/handoff/budget-family-1/inventory.json`; `scratchpad/handoff/budget-family-1/scan.py` ; provenance unresolved]

This is an inventory of the literal 33514 (0x82ea), not proof that all possible budgets
use this spelling: out-of-line conversions, other units, synthesized constants and
unaligned data are outside the detector. One literal can serve several comparisons, and
the HTTP body has two separate literal pools. [S: `scratchpad/handoff/budget-family-1/scan.py`;
`src/matched/func_ov065_02275b94.c`]

The four work budgets compare elapsed milliseconds strictly greater than 40 between
completed entries/stages. They cannot interrupt an expensive leaf. The nested walkers
share a supplied start stamp; without a resume-counter pointer their budget checks are
disabled. An incomplete handler can also stop the dispatcher independently of its own
elapsed-time test. [S: `src/matched/func_020b0b00.c`; `src/matched/func_020b0bbc.c`;
`src/matched/func_020b0ea8.c`; `src/matched/func_020b6c0c.cpp`]

## Where it lives: every aligned site

Each row's address is the literal-pool address, not the function entry. Its source citation
supplies the entry address and semantics; `inventory.json` binds module, symbol interval
and literal-load addresses. Thresholds are milliseconds unless stated otherwise. "None"
means this site is not an elapsed-work budget. Offline statements distinguish the measured
loader from static plausibility and unproved caller reachability. Wi-Fi code can of course
be entered during a failed connection attempt without Internet connectivity; "normal
offline play" excludes initiating that feature. [H: `scratchpad/handoff/budget-family-1/inventory.json`;
`scratchpad/handoff/budget-family-1/classification.json` ; provenance unresolved]

| Module / literal site | Function / static source | Class | Threshold (ms) | Work per iteration or call | Other exit or completion | Offline reach |
|---|---|---|---|---|---|---|
| main `0x200131c` | `func_020012ec` [S: `src/matched/func_020012ec.c`] | Other: timestamp | None | Store milliseconds before entering crash-screen pump | No exit in local infinite pump | Offline error path; normal play not established |
| main `0x208cb20` | `func_0208c978` [S: `src/matched/func_0208c978.c`] | Other: event gate | <=1100 | Age countdown and gate event 0x64 using previous tick stamp | Single update; arm, RTC flags, count and scene guard select branches | Offline villager update; static path, no new run |
| main `0x20b0bb8` | `func_020b0b00` [S: `src/matched/func_020b0b00.c`] | Loader | >40 | Dispatch one typed entry through data_020e41ec | Entry count exhausted or handler returns zero; budget only with resume pointer | Offline measured by LOAD52 |
| main `0x20b0c48` | `func_020b0bbc` [S: `src/matched/func_020b0bbc.c`] | Channel-list / loader | >40 | Open one two-halfword channel entry via func_0202f134 | Entry count exhausted; budget only with resume pointer | Offline loader path; individual body timing not measured |
| main `0x20b0f50` | `func_020b0ea8` [S: `src/matched/func_020b0ea8.c`] | Loader | >40 | Construct one positioned entry via func_02003348 | Entry count exhausted; budget only with resume pointer | Offline loader path; individual body timing not measured |
| main `0x20b6d1c` | `func_020b6c0c` [S: `src/matched/func_020b6c0c.cpp`] | Loader | >40 | Invoke current stage handler with shared start stamp | State outside 1..6, last stage complete, or handler incomplete | Offline measured by LOAD52 |
| autoload_2 `0x20ec140` | `func_020ec040` [S: `src/matched/func_020ec040.c`] | Network: queue watchdog | > configurable gLimit_0213e6b8 | Peek message queue and update/reset timestamp; call func_020ed9f4 on expiry | No message returns 1; disabled parameter clears stamp | Network subsystem in autoload_2; normal offline reach unproven |
| autoload_2 `0x20ec824` | `func_020ec5ac` [S: `src/matched/func_020ec5ac.c`] | Network: handshake pump | > configurable g_bootTimeoutMs | Advance one boot/cleanup state and poll network completion | State 7 completes; hooks, mode, status and completion bypass timeout | Network calls into ov065; normal offline reach unproven |
| autoload_2 `0x20ec914` | `func_020ec848` [S: `src/matched/func_020ec848.c`] | Network: busy wait | > configurable g_0213e6b8 | Poll func_0226760c for state 2 | State 2 ends wait; timeout returns failure, later status can fail | Network calls into ov065; normal offline reach unproven |
| autoload_2 `0x20ecefc` | `func_020ece54` [S: `src/matched/func_020ece54.c`] | Network: configuration | None; input ticks converted to ms | Store configured timeout and initialize queues/state | Single setup call; no timed loop | Network subsystem; normal offline reach unproven |
| autoload_2 `0x20ecfe4` | `func_020ecf24` [S: `src/matched/func_020ecf24.c`] | Network: expiry gate | >120000 | Check network state then expire stored timestamp | Single update; state, status or missing timestamp returns early | Network subsystem; normal offline reach unproven |
| autoload_2 `0x20ed12c` | `func_020ed03c` [S: `src/matched/func_020ed03c.c`] | Network: cadence | 250 * g_divisor period, not budget | Select time bucket, probe peer and update entry flags/value | Single update; threshold<5 or unchanged bucket returns early | Network calls into ov065; normal offline reach unproven |
| autoload_2 `0x20ed650` | `func_020ed5f8` [S: `src/matched/func_020ed5f8.c`] | Network: timestamp | None | Store current milliseconds when both arguments are zero | Single callback; nonzero arguments return early | Network subsystem; normal offline reach unproven |
| autoload_2 `0x210030c` | `func_020fff80` [S: `src/matched/func_020fff80.c`] | Other: NVRAM timeout | >4000 | Pump SPI NVRAM command/status state and retry busy write | Successful read/write, callback error, write-enable failure, reset completion; status bit 0x20 also selects reset | Hardware/config path could run offline; exact gameplay caller unproven |
| autoload_2 `0x21148c0` | `func_0211482c` [S: `src/matched/func_0211482c.c`] | Other: alarm conversion | Input msec; no elapsed compare | Install sleep alarm, then sleep thread until callback clears pointer | Alarm callback clears local thread pointer | Generic OS sleep usable offline; specific call occurrence unmeasured |
| ov001 `0x220b494` | `GetTickCount` [S: `src/matched/GetTickCount.c`] | Other: clock getter | None | Return tick count converted to milliseconds | Immediate return | ov001 utility; callers/offline reach unproven |
| ov065 `0x2273b68` | `func_ov065_02273a8c` [S: `src/matched/func_ov065_02273a8c.c`] | Network: scan cadence | >=150 | Advance stealth AP list/channel and restart scan | Found flag also advances; exhausted channels select next phase | ov065 Wi-Fi; not normal offline play |
| ov065 `0x2273c48` | `func_ov065_02273b8c` [S: `src/matched/func_ov065_02273b8c.c`] | Network: scan cadence | >=150 | Advance different-channel AP list and restart scan | Found flag also advances; list exhausted selects next phase | ov065 Wi-Fi; not normal offline play |
| ov065 `0x2273d28` | `func_ov065_02273cb4` [S: `src/matched/func_ov065_02273cb4.c`] | Network: scan cadence | >=300 | Advance scan channel by two | Channel >=13 selects next phase | ov065 Wi-Fi; not normal offline play |
| ov065 `0x2275098` | `func_ov065_02274ea0` [S: `src/matched/func_ov065_02274ea0.c`] | Network: retry delay | <5000 waits | Check abort under mutex and sleep 5000 before retrying auth | Abort returns; after delay retry; outer loop ends on success/error/retry limit | ov065 Wi-Fi; not normal offline play |
| ov065 `0x2275f58` | `func_ov065_02275b94` [S: `src/matched/func_ov065_02275b94.c`] | Network: HTTP send timeout | >timeout (default 60000); >1000 reseed | Send up to 700 bytes, flush and advance request cursor | Request exhausted; no IP, write failure, timeout, or abort | ov065 Wi-Fi; not normal offline play |
| ov065 `0x2276078` | `func_ov065_02275b94` [S: `src/matched/func_ov065_02275b94.c`] | Network: HTTP receive timeout | >timeout (default 60000); >1000 reseed | Read/consume received bytes and parse completion boundaries | Buffer/content complete, read end/error, no IP, timeout, abort | ov065 Wi-Fi; not normal offline play |
| ov065 `0x2278758` | `func_ov065_02278614` [S: `src/matched/func_ov065_02278614.c`] | Network: auth timeout | >10000 | Poll auth result, retry pending request or report timeout | Success/status zero returns; timeout stops login | ov065 Wi-Fi; not normal offline play |
| ov065 `0x2278b68` | `func_ov065_02278ac8` [S: `src/matched/func_ov065_02278ac8.c`] | Network: login timeout | >60000 | Pump GP login and check connect stamp | Inactive/error/state guards; expiry stops login and clears flag | ov065 Wi-Fi; not normal offline play |
| ov065 `0x22793d8` | `func_ov065_02279384` [S: `src/matched/func_ov065_02279384.c`] | Network: cadence | >=300 | Increment count, call func_02283cc0 and restamp | Single update returns; below threshold skips work | ov065 Wi-Fi; not normal offline play |
| ov065 `0x227e104` | `func_ov065_0227dd8c` [S: `src/matched/func_ov065_0227dd8c.c`] | Network: match timers | >cmdTimeoutTime; >=3000+3000*n; >1000/3000/3000+3000*n | Pump matching, resend reservations and update server browser | State/flags/errors and retry outcomes; not a timed work-list break | ov065 Wi-Fi; not normal offline play |
| ov065 `0x227ebd4` | `func_ov065_0227eabc` [S: `src/matched/func_ov065_0227eabc.c`] | Network: peer watchdog | >per-peer recvTimeoutTime | Walk host list; send available split, notify receive timeout and restamp | Host count exhausts walk; busy/buffer/validity guards skip work; timeout does not break walk | ov065 Wi-Fi; not normal offline play |
| ov065 `0x227efe4` | `func_ov065_0227efc4` [S: `src/matched/func_ov065_0227efc4.c`] | Network: clock getter | None | Return current milliseconds | Immediate return | ov065 Wi-Fi utility; not normal offline play |
| ov065 `0x22807b4` | `func_ov065_02280794` [S: `src/matched/func_ov065_02280794.c`] | Network: clock getter | None | Return current milliseconds | Immediate return | ov065 Wi-Fi utility; not normal offline play |
| ov066 `0x2267dac` | `func_ov066_02267cb0` [S: `src/matched/func_ov066_02267cb0.c`] | Other: alarm conversion | Input arg0 ms; helper uses 500 ms | Configure slot manager and optionally install callback alarm | Single setup; arg0 zero skips own alarm | ov066 communication/slot subsystem; offline reach unproven |
| ov066 `0x226a3a8` | `func_ov066_0226a2e8` [S: `src/matched/func_ov066_0226a2e8.c`] | Other: alarm conversion | Input msec | Cancel/rearm timeout alarm for each active slot | Slot count exhausted; inactive slots skipped | ov066 communication/slot subsystem; offline reach unproven |
| ov066 `0x226a7d0` | `func_ov066_0226a494` [S: `src/matched/func_ov066_0226a494.c`] | Other: alarm conversion | Input interval ms | Update matching MAC entry or allocate vacant entry and arm alarm | Matching/free entry returns success; capacity exhausted fails | ov066 communication/slot subsystem; offline reach unproven |

## Groups and expected clock sensitivity

| Group | Members | What a sub-frame clock could change | DS frames per body |
|---|---|---|---|
| Loader | Three main loader sites plus nested channel-list site | Time checks can expire between entries/stages; resume counters then expose partial work across main-loop bodies; no mid-leaf preemption | LOAD52 door stage 5 window: 6.17; before loader: 3.14. Exit loader body: 23.60. Not isolated per function. [E/O: `scratchpad/handoff/budget-family-1/load52-summary.json`] |
| Channel-list | `func_020b0bbc`, already counted in loader four | Same shared 40 ms rule; list is not necessarily finished when call returns | Not measured separately. [S: `src/matched/func_020b0bbc.c`] |
| Network | All 13 ov065 sites and 7 autoload_2 network sites | Expiry/retry/cadence decisions can move within a frame; HTTP and busy waits may observe elapsed time sooner; this is not loader-style cooperative slicing | Not measured. [H: sources in table; `scratchpad/handoff/budget-family-1/classification.json` ; provenance unresolved] |
| Other | main crash/event, ov001 getter, autoload_2 NVRAM/sleep, ov066 alarms | Event/deadline resolution may change; getters return finer values; inverse conversion alone creates no new yield. Alarm delivery also depends on scheduler/interrupt implementation | Not measured. [H: sources in table; `scratchpad/handoff/budget-family-1/classification.json` ; provenance unresolved] |

These are predictions from control flow, not measurements of TICK53. LOAD52's historical
port observations describe its pinned artifact: stage 5 completes within one sampled
frame because tick time does not advance inside that body. They do not establish the
behavior of a later clock implementation. [H: table source control flow; E:
`scratchpad/handoff/budget-family-1/load52-summary.json`]

The original door's stage 5 spans oracle frames 57,268..57,305, with one sub-entry taking
15 frames. The exit has leaves taking 33 and 62 frames (551 and 1,036 ms). These demonstrate
overshoot of a 40 ms boundary, not a 40 ms preemptive cap. LOAD52 measured 6.17 frames/body
(103.1 ms) during door stage 5 versus 3.14 (52.5 ms) before it; the difference is 50.6 ms.
[O: `scratchpad/handoff/budget-family-1/load52-summary.json`;
`scratchpad/handoff/budget-family-1/orig-door-walk.txt`; `scratchpad/handoff/budget-family-1/orig-exit-walk.txt`]

## LOAD52 cross-check and the formerly unread function

LOAD52's four are exactly `func_020b6c0c`, `func_020b0b00`, `func_020b0ea8` and
`func_020b0bbc`, with literal sites 0x020b6d1c, 0x020b0bb8, 0x020b0f50 and 0x020b0c48.
The three-entry dispatcher table also names `func_020b0c4c`; that is a callee, not a
fifth literal hit. [H: `scratchpad/handoff/budget-family-1/inventory.json`;
`scratchpad/handoff/budget-family-1/load52-summary.json` ; provenance unresolved]

`func_0208c978` is the matched villager periodic timer, not a loader. It decrements
the countdown at object +0xc8, examines RTC stamps while +0xb4 is armed, and in one
count branch admits event 0x64 only when the previous tick stamp at +0xdc is at most
0x44c (1100) ms old. It then restamps. Other branches disarm for 0x258 frames and
request event 0x65, or merely restamp; scene 0x2e suppresses event requests. These
are a single update's conditions, not an elapsed-time loop exit.
[S: `src/matched/func_0208c978.c`, entry 0x0208c978, literal 0x0208cb20]

The two ov065 clock getters have recovered function boundaries. Their inherited source
headers warn that callee names are unverified; independent direct-call decoding here
resolves both to OS_GetTick at 0x01ffa6b4 and division at 0x02136550, matching the ov001
getter. This establishes those two targets, not every reconstructed pointer in the table.
[H: `scratchpad/handoff/budget-family-1/inventory.json`, direct_calls for 0x0227efc4 and 0x02280794 ; provenance unresolved]

## Data it reads and writes

| Field / address | Meaning | Writer / reader and evidence |
|---|---|---|
| `0x021f42dc`, `0x021f42e4` | Loader resume index / sub-entry counter | Stage 5 passes these to the entry walker; counters advance after work [H/E: `scratchpad/handoff/budget-family-1/load52-summary.json` ; provenance unresolved] |
| Object `+0xdc` (64 bits) | Previous event timer tick | `func_0208c978` reads and restamps it [S: `src/matched/func_0208c978.c`] |
| `0x0213e6b8` | Configured network timeout in ms | Setup converts argument ticks; watchdog and handshake read it [S: `src/matched/func_020ece54.c`; `src/matched/func_020ec040.c`; `src/matched/func_020ec5ac.c`; `src/matched/func_020ec848.c`] |
| Alarm interval parameters | Milliseconds converted into ticks | OS sleep and ov066 alarm setup; not work-budget state [S: `src/matched/func_0211482c.c`; `src/matched/func_ov066_0226a2e8.c`] |

## How to check it

Run `python -B scratchpad/budget-family-1/scan.py <checkout-with-extract>` from the retained
unit worktree. It uses the repository's existing target loader and reads extracted module
files in place; no provisioning, compiler, link or game run is necessary. The expected
result is 32 sites, 31 functions and no site without a literal-load reference. Compare the
five module counts with `scratchpad/budget-family-1/budget-sweep.txt`; inspect every matched body
named in the table before assigning meaning to an occurrence.
[H: `scratchpad/handoff/budget-family-1/scan.py`; `scratchpad/handoff/budget-family-1/inventory.json` ; provenance unresolved]

## Hypotheses and limits

- Normal offline reachability remains unproven for the network wrapper, ov001 and ov066
  sites. A caller trace from a named offline recipe, including overlay residency, would
  settle it; membership in an always-loaded module does not prove execution.
  [H: `scratchpad/handoff/budget-family-1/classification.json`]
- No per-function DS timing was measured here. Repeating LOAD52 with each resume boundary
  instrumented would distinguish time in the channel walker from other loader leaves.
  [H: `scratchpad/handoff/budget-family-1/load52-summary.json`]
- Matched source names/types may be reconstructed. Hashes bind the reviewed files, not
  proof of all pointer relocations or semantic names; the page deliberately describes
  uncertain work by call/field addresses. [H: `docs/rules/D-defects.md`, D9/D10/D12 ; provenance unresolved]

## Related

- [Bus timings](bus-timings.md) — what the work inside a budget COSTS: the per-region bus
  table, the cartridge's per-command price, the geometry FIFO's depth
- [Scenes and channels](scenes-and-channels.md)
- [Threads and interrupts](threads-and-interrupts.md)
- [Interpreter path](interpreter-path.md)
