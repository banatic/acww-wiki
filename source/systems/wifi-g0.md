# Wi-Fi G0: gatehouse routes and the first WM request

**Summary.** The gatehouse selects visiting on row 0 and inviting on row 1.
The original wifi-g0-1 traces below submitted no requests. wifi-g0-2 identifies a
zero firmware-prefix predicate before WM_Init and supplies that halfword only under
the default-off diagnostic switch. Two runs per route now submit exactly one
WM_Enable request (API 3). Visiting cleans up after 600 frames; inviting remains
open through frame 18000. No ARM7 request is completed and no scan or peer exists.

## What happens

The owner's answer corrected the brief's location to gatehouse building `0x500b`;
the historical `gate` navigator target was reproduced from the private LIVE46 save.
[H: `docs/log/cycle41-gameplay.md:2922`] [E: `scratchpad/wifi-g0-1/revision2/goto-gate.receipt.json`]

The common snapshot at port frame 7300 has five choice rows; an earlier four-row
reading was corrected after measuring the full local still, and its obsolete
metadata is retained locally but excluded from the final export.
[E: `scratchpad/wifi-g0-1/revision2/safe/menu-common-final.json`]

Row 0 reaches visiting dialogue and row 1 inviting dialogue, followed by three
transport rows and a two-row confirmation; both traces select transport row 0 and
confirmation row 0. These are zero-based visual row ordinals, not message IDs.
Whichline candidates may be stale and are paired with local still hashes.
[E: `scratchpad/wifi-g0-1/revision2/safe/menu-guest-transport.json`, `scratchpad/wifi-g0-1/revision2/safe/menu-host-transport.json`, `scratchpad/wifi-g0-1/revision2/safe/menu-host-confirm.json`]

| Route | Repetitions / stop | Mode first sampled | ov066 load frame | Endpoint observation |
|---|---|---|---|---|
| Row 0, visiting / guest intent | 2 / 18000 | 2 at 12600 | 12581 | Searching dialogue; actual WM scan unproved. |
| Row 1, inviting / host intent | 2 / 18000 | 1 at 13000 | 12953 | Gate visibly open; actual peer-wait unproved. |

Both routes reproduce all 36 sampled screenshots within their respective pair,
mode samples, selected execution totals and overlay events; all exits are 100
with the requested stop record and empty stderr.
[E: `scratchpad/wifi-g0-1/revision2/safe/comparison-residency.json`, `scratchpad/wifi-g0-1/revision2/runs/branch0-repeat1/receipt.json`, `scratchpad/wifi-g0-1/revision2/runs/branch1-repeat2/receipt.json`]

## Where it lives

| Symbol / boundary | Module | Observation and limit |
|---|---|---|
| `func_02074b44`, `0x02074b44` | main | 95 interpreted steps and one call per trace; runtime caller unknown. |
| `CTRDG_WriteAgbFlashSectorAsync`, `0x020ed6c4` | autoload_2 | Zero steps/calls; config names this address, contrary to an established wireless callback bridge. |
| `WM_Init`, `0x02120990` | autoload_2 | One interpreted call per trace; work-buffer pointer nonzero. |
| `WMi_SetCallbackTable`, `0x02120724` | autoload_2 | No interpreted execution in these windows. |
| `WMi_SendCommand`, `0x021205d0` | autoload_2 | No interpreted execution in these windows. |
| `PXI_SendWordByFifo`, tag 10 | host shim | Armed once per process, zero submissions; no print cap. |

Totals come from 2098 guest or 2191 host rows, below the 32768 requested maximum,
with a completed 7301..17900 window; interval counts are not a runtime call graph,
and the frame window is polled every 4096 interpreter steps.
[E: `scratchpad/wifi-g0-1/revision2/safe/branch0-repeat1.json`, `scratchpad/wifi-g0-1/revision2/safe/branch1-repeat1.json`]
[S: `config/adm-kr/arm9/autoload_2/symbols.txt:234`, `port/interp/interp_cpu.c:535`]

Only ov066 loads after the shared snapshot: `0x022667e0..0x0226be20`. The reconstructed
host address resolver also retains ranges for IDs 2, 3, 4, 9, 15, 48, 65, 68 and
147. Some are stale uncovered tails: `FS_EndOverlay` is a no-op, so bookkeeping
does not prove that every listed module remains logically active or executes.
[E: `scratchpad/wifi-g0-1/revision2/safe/comparison-residency.json`]
[S: `port/shim/fs/ovlreloc.c:75`]

## Data it reads and writes

| Field | Meaning / observation | Evidence |
|---|---|---|
| `0x021fbef8`, byte | Mode 0 to 2 for row 0; 0 to 1 for row 1 | Closed 213-sample ledgers, 7350..17950 every 50. |
| `0x021fbefc`, halfword | Online state ID remains 0 | Same ledgers; no online route selected. |
| `0x02206aac`, pointer | WM work-buffer address `0x022d7d20` at endpoint | Allowlisted end peek. |
| WM work buffer +24 | API callback slots 0..13 zero at endpoint | Partial sample, not registration history. |
| Tag-10 request +0, halfword | Request's own state/ownership and API ID | Synthetic bounds fixture; no real request observed. |

Only reduced IDs/counts/addresses are exported; raw ledgers and stills stay local.
The oracle marks coherence unverified and samples after input before VBlank, so
the mode transitions are bounded by the preceding 50-frame sample.
[E: `scratchpad/wifi-g0-1/revision2/safe/branch0-repeat1.json`, `scratchpad/wifi-g0-1/revision2/safe/branch1-repeat1.json`]

`ACWW_WM_REQUEST_TRACE=1` checks an aligned main-RAM pointer with a full 256-byte
slot before reading its first halfword; request length is unavailable because
the FIFO pointer submission carries no independent length. OFF has no formatting,
output, request dereference or counting, but the first environment read and cached
flag checks still cost CPU time; no overhead benchmark was performed.
[S: `port/shim/os/pxisend.c:659`]
[E: `scratchpad/wifi-g0-1/revision2/trace-fixture-sealed/receipt.json`]

## How to check it

Use the exact runner receipts: interpreter, card32, private seed copy per process,
date 20260911/time 113000, `RTC_FREEZE=0` advancing deterministic gameplay clock,
and keyed boot phases 1160/1760. Absolute state/save paths pass through Python env.
Direct executable diagnostics do not assert canonical frontier readiness.
[E: `scratchpad/wifi-g0-1/revision2/boot-observer.json`, `scratchpad/wifi-g0-1/revision2/runs/common-observer/receipt.json`]

Replay `plans/common-menu.pad` from frame 3000, save at 7300, then each of
`plans/branch0-trace.pad` and `plans/branch1-trace.pad` twice to 18000 using
`prepare_trace.py` and `runner.py`. Reduce and compare with `reduce_trace.py` and
`finish_metadata.py`; each native run name must be fresh.
[E: `scratchpad/wifi-g0-1/revision2/prepare_trace.py`, `scratchpad/wifi-g0-1/revision2/finish_metadata.py`]

Final fresh own-worktree link exits 0 with empty stderr and dark194/256; canonical
card32 OFF passes 31/31 EXACT with frozen historical RTC20050615/100000, a distinct
recipe from these advancing gameplay runs.
[E: `scratchpad/wifi-g0-1/revision2/link-observer-final.receipt.json`, `scratchpad/wifi-g0-1/revision2/offgate/offgate-check.json`]

## wifi-g0-2: the pre-submit condition

Pinned base: `27dc0df73a5739d7b1efcee0c31bd711bd752bb8`. The baseline WATCH_LR
at main `0x02074b58` records LR `0x02262651` on both routes: the live caller is
ov048 `func_ov048_02262618`, not the lexical main caller `0x020a2d48`.
The interpreted local initializer `0x0226748c` calls the predicate named
`WM_IsExistAllowedChannel` before WM_Init. Its load at `0x02120d9c` reads the
halfword `0x027ffcf4` as zero (guest 12581, host 12953). This is the first MAC
prefix halfword; `WM_GetAllowedChannel` separately reads `0x027ffcfa`.
[S: `src/matched/func_ov066_0226748c.c`, `src/matched/WM_IsExistAllowedChannel.c`, `src/matched/WM_GetAllowedChannel.c`]
[E: `scratchpad/wifi-g0-2/baseline-analysis.json`, `scratchpad/wifi-g0-2/source-analysis.json`]

The zero branch signals local code `0x41` and calls the registered free callback
through `0x022668c4`. The next device allocation reuses the driver address:
baseline context and device both equal `0x022d7c44`. Consequently those words
are device pointers, not valid driver phase/state. The later WM_Init still runs
and installs 16 port callbacks. PXI readiness at `0x027fff8c` is already all ones;
WmInitCore checks tag 10's bit and returns success without a request handshake.
The once-per-tag tag14 drop is neither a reply nor proof of the blocker.
[S: `src/matched/func_ov066_022668c4.c`, `port/build/shadow/func_02077ae8.c`, `port/shim/os/heapfree.c`, `src/matched/WmInitCore.c`, `port/shim/os/pxi.c`]
[E: `scratchpad/wifi-g0-2/baseline-analysis.json`]

`ACWW_WM_STUB=1` in pxisend.c supplies only synthetic prefix halfword 2 when the
interpreter's field is zero. Native execution, existing nonzero metadata, the
remaining MAC bytes and channel mask stay untouched. It is diagnostic bootstrap
metadata, not a valid radio implementation or real console identity. OFF does
no metadata read/write; cached checks still cost CPU time. The metadata is RAM
snapshot state; the switch remains environment-derived. A four-case native fixture
checks OFF/unmapped, armed-native/unmapped, nonzero preservation and the exact
two-byte zero-field write. No request handler, acceptance bit or callback is added.
[S: `port/shim/os/pxisend.c`]
[E: `scratchpad/wifi-g0-2/stub-fixture/receipt.json`]

## wifi-g0-2: request and bounded outcome

| Route / repetitions | First request | Outcome with no completion |
|---|---|---|
| Visiting / 2 | frame 12581, API 3 | Cleanup/ov068 load at 13181, 600 frames later; error dialogue remains at 18000. |
| Inviting / 2 | frame 12953, API 3 | Gate remains open at 18000, 5047 frames later; no error or timeout demonstrated. |

A supplemental visiting run stops at 13500 and snapshots the error at 13400.
`whichline` reports gatekeeper archive entry 86 in the render region, paired with
the local error-dialogue still; archive 2 entry 21 is also resident there. These
are candidate BMG ordinals, not a proven live message-dispatch ID; render copies
can be stale. No game strings or pictures are exported.
[E: `scratchpad/wifi-g0-2/safe/error-dialogue.json`, `scratchpad/wifi-g0-2/runs/guest-detail/receipt.json`]

All four requests use slot `0x02206b40`, state16 `0x0003` (accepted bit clear),
capacity 256 bytes. WMi_SendCommand writes the API halfword and three argument
words for WM_Enable: WM7, status and ARM7-to-ARM9 FIFO addresses. Their header-plus-
argument footprint is 16 bytes, not a submitted length: PXI carries no length and
the observer correctly retains `request_length=unavailable`. The status halfword
at `0x022d8280` is read as 0 by WMi_CheckStateEx before Enable. These are ARM7
bootstrap pointers, not MP frame bytes or any relay kind 1/2/3 payload.
[S: `src/matched/WM_Enable.c`, `src/matched/WMi_SendCommand.c`, `src/matched/WMi_CheckStateEx.c`, `docs/kb/hybrid/online-spec.md`]

Each completed 7301..17900 census has one WM_Enable, WMi_SetCallbackTable and
WMi_SendCommand call, zero WmReceiveFifo calls, and fewer than 32768 rows. Final
PXI receive census at 18000 reports only tag11 deliveries, no tag10 or tag14.
Each pair has identical request lines, selected census totals and all 36 sampled
BMP hashes. Both routes exit 100 at requested 18000 with empty stderr and no named
runtime fault. Host endpoint driver phase/state is 3/2, with distinct context and
device allocations; callback slot 3 points to `0x02266b94`. Guest cleanup clears
the WM work pointer and replaces ov066, so its old globals must not be decoded.
[E: `scratchpad/wifi-g0-2/safe/comparison.json`, `scratchpad/wifi-g0-2/safe/guest-stub-1.json`, `scratchpad/wifi-g0-2/safe/host-stub-1.json`]

The WCM source-only path is separate: phase 1 calls WM_Init, rejects zero
WM_GetAllowedChannel with WM_Finish/return 5, or registers an indication callback
and calls WM_Enable before phase 2 waiting (phase 3 ready). This helper leaves the
channel mask zero and does not claim WCM/online startup. Request lifetime, completion
and all scan/MP/relay traffic remain G1 or later work.
[S: `src/matched/func_ov065_0227197c.c`]

Fresh own-worktree link: exit 0, empty stderr, dark194/256. With the switch unset,
canonical card32 OFF and explicit card0 reference `2ea19722-dirty` each pass 31/31
EXACT; both baseline gates also pass. Gameplay uses private LIVE46 copies and an
advancing 20260911/113000 clock; OFF uses its frozen historical recipe. Competing
processes are recorded and untouched; elapsed times are not comparative evidence.
Direct diagnostics do not publish a frontier artifact. No pipeline or commit ran.
[E: `scratchpad/wifi-g0-2/link-stub/receipt.json`, `scratchpad/wifi-g0-2/off-stub32-data/offgate-check.json`, `scratchpad/wifi-g0-2/off-stub0-data/offgate-check.json`]

## Related

- [Network boundary](network.md).
- [Protocol map](multiplayer-protocol.md).
- [G0-G5 plan](wifi-port-plan.md).
- [Runtime router](../../docs/kb/hybrid/wifi.md).
