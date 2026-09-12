# WM request lifetime on the offline ARM7 model

**Summary.** The default-off WM model completes bounded requests on the existing
PXI interrupt path and a WM-only IRQ-enable boundary. It keeps the original ARM9 WM and game code in charge of
callbacks, slot reuse and gate UI. No radio, remote town or multiplayer success
is implied by a successful initialization or MP-start callback.

## What happens

`ACWW_WM_STUB=1` enables the model only on the interpreter path; missing bootstrap
metadata receives a synthetic locally administered MAC and a channel 1..13 mask.
Unset/native paths do not read those metadata words.
[S: `port/shim/os/pxisend.c`, `wm_stub_bootstrap`]

An accepted request receives a monotonically increasing token and a private
256-byte request copy. Its original slot stays unavailable until the existing
PXI queue delivers its response and ARM9 `WmReceiveFifo` sets the reusable bit.
A bounded two-boundary IRQ policy observes the first enable/restore after acceptance
and permits completion only at a later boundary; interrupts-disabled and reentrant
calls do not drain. This preserves the post-send message-queue publication before
Reset callers record their pending flag. It is synthetic latency, not ARM7 timing.
[S: `port/shim/os/pxisend.c`, `acww_wm_irq_poll`; `port/shim/os/interrupts.c`; `src/matched/WMi_SendCommand.c`, `func_ov066_02266a08.c`]

Duplicate submissions, full queues and malformed slot pointers are refused before
acceptance. An already completed token cannot write or deliver a second reply.
[S: `port/shim/os/pxisend.c`, `wm_stub_submit`, `wm_stub_complete`; `src/matched/WmReceiveFifo.c`]

Initialization state is READY 0 -> STOP 1 for Enable, then IDLE 2 for PowerOn;
combined Initialize reaches IDLE. CLASS1 is an internal radio transition, not a
separate ARM9 initialization callback demonstrated by this model.
[S: `src/matched/WM_Enable.c`, `WM_PowerOn.c`, `WM_Initialize.c`]
[P: NitroSDK 2.2a, `man/en_US/wm/wm/WM_Enable.html`]

Scan returns the successful no-parent-found state code 4. StartConnect has no
`WM_ERRCODE_NO_PARENT` enumeration: the SDK callback documents parent-not-found
as timeout, error code 9. This fixture returns that failure while retaining IDLE,
with no connected notification or assigned AID.
[S: `port/shim/os/pxisend.c`, `wm_stub_complete`; `src/matched/WM_StartConnectEx.c`]
[P: NitroSDK 2.2a, `include/nitro/wm/common/wm.h`, WMStartConnectCallback]

StartParent also schedules SDK BEACON_SENT notifications (API 8, state code 2).
They use the shared ARM7 callback buffer, a separate token 0 and the callback-control
handshake; they never reuse a completed request slot or count as terminal replies.
The TU period is rounded upward to frames using 60 Hz, a timing approximation.
[S: `port/shim/os/pxisend.c`, `wm_stub_frame`; `src/matched/WmClearFifoRecvFlag.c`]
[P: NitroSDK 2.2a, WMStartParentCallback]

## Where it lives

| Boundary | Module/file | Role | Evidence |
|---|---|---|---|
| `PXI_SendWordByFifo` | host pxisend.c | Request acceptance and existing delivery queue.  [S: `port/shim/os/pxisend.c`] |
| `WMi_SendCommand` | autoload_2 | ARM9 slot queue, API halfword, argument words.  [S: `src/matched/WMi_SendCommand.c`] |
| `WmReceiveFifo` | autoload_2 | ARM9 callback dispatch and final slot release.  [S: `src/matched/WmReceiveFifo.c`] |
| `func_ov066_0226a074` | ov066 | Channel measurement callback, channel +8 and busy ratio +10.  [S: `port/build/shadow/func_ov066_0226a160.c`] |
| `acww_online_relay_send` | standalone hook / offline adapter | Bounded binary frame boundary.  [S: `port/shim/os/pxisend.c`] |

The old reconstruction comment calling `0226a074` a vote/ack handler is not a
protocol fact: its shadow caller binds WM_MeasureChannel, and its read fields
agree with that SDK callback. No matched source is edited.
[S: `port/build/shadow/func_ov066_0226a160.c`, `src/matched/WM_MeasureChannel.c`]

## Data it reads and writes

| API | Successful model state / result | Reply fields  Evidence |
|---|---|---|---|
| 0 Initialize | 0 -> 2 | API +0, error +2.  [S: `port/shim/os/pxisend.c`, `wm_stub_complete`] |
| 3 Enable; 5 PowerOn | 0 -> 1; 1 -> 2 | API +0, error +2.  [S: `port/shim/os/pxisend.c`, `wm_stub_complete`] |
| 4 Disable; 6 PowerOff | 1 -> 0; 2 -> 1 | API +0, error +2.  [S: `port/shim/os/pxisend.c`, `wm_stub_complete`] |
| 7 Parent parameter | Remain 2 | Copy bounded 64-byte parameter and <=112 opaque user bytes.  [S: `port/shim/os/pxisend.c`, `wm_stub_complete`] |
| 8 StartParent | 2 -> 7 | Start code 0 at +8; no child bitmap.  [S: `port/shim/os/pxisend.c`, `wm_stub_complete`] |
| 10 Scan; 11 EndScan | 2/5 -> 5; 5 -> 2 | Scan code 4 at +8, channel +16.  [S: `port/shim/os/pxisend.c`, `wm_stub_complete`] |
| 12 Connect | Remain 2, error 9 | No AID, no successful connection.  [S: `port/shim/os/pxisend.c`, `wm_stub_complete`] |
| 14 StartMP; 16 EndMP | 7 -> 9; 9 -> 7 | MP-start code 10 at +4; no received data.  [S: `port/shim/os/pxisend.c`, `wm_stub_complete`] |
| 30 MeasureChannel | Remain 2 | Channel +8, synthetic zero busy ratio +10.  [S: `port/shim/os/pxisend.c`, `wm_stub_complete`] |

These are stub transition contracts, not observations of a real ARM7 or peer.
Reset/End, game-info updates, beacon indication and parent-entry enable are also bounded; unsupported
operations terminate with an explicit error rather than claiming success.
[S: `port/shim/os/pxisend.c`, `wm_stub_complete`]

Status fields used by ARM9 include state +0, MP flag +0xc, buffers +0x46..0x54,
MAC +0xdc, parent parameters +0xe4, child bitmap +0x17e, AID +0x184, size limits
+0x18e/+0x190 and channel masks +0x1f0/+0x1f2. Persistent host request copies,
tokens, status pointer and parent data are registered savestate blobs.
[S: `src/matched/WM_StartMPEx.c`, `WM_SetMPDataToPortEx.c`; `port/shim/os/pxisend.c`]

## How to check it

Run `python port/tools/test_wm_stub.py` for synthetic actual-source ownership,
no-parent, duplicate completion and relay-envelope and bounded beacon-service checks, including an intentionally
wrong timeout expectation that the fixture rejects. The OFF and native cases
leave emulated metadata unmapped and must still return safely.
[E: `scratchpad/wifi-g1-1/fixture-native-irq-fields/receipt.json`]

Gameplay uses the predecessor gatehouse plans, private copies of the LIVE46 seed,
`ACWW_CARD_FAST=32`, `ACWW_TICK_MODEL` unset, `ACWW_RTC_DATE=20260911`,
`ACWW_RTC_TIME=113000`, `ACWW_RTC_FREEZE=0`, and same-build snapshots at frames 3000 and
7300. `ACWW_STOP_FRAME=18000`, `ACWW_WM_STUB=1` and `ACWW_WM_REQUEST_TRACE=1`
are explicit in each branch JSON; these are direct diagnostics, not published frontiers.
[S: `scratchpad/wifi-g1-1/prepare.py`, `runner.py`, `guest-irq-1.json`, `host-irq-1.json`]

After preparing the same-build snapshots, replay with `python -B
scratchpad/wifi-g1-1/control.py replay-guest scratchpad/wifi-g1-1/runner.py
--json replay-guest scratchpad/wifi-g1-1/guest-irq-1.json` (one command); use
a fresh run name each time, and the host JSON for the inviting route.
[S: `scratchpad/wifi-g1-1/control.py`, `runner.py`]

Final guest runs each accept and complete 1445 requests: Enable, PowerOn, 1440
empty scans, Reset, PowerOff and Disable; state changes are 0 -> 1 -> 2 -> 5 at
12581 and 5 -> 2 -> 1 -> 0 at 13181, all read from the WM status word.
[E: `scratchpad/wifi-g1-1/safe/guest-irq-1.json`, `guest-irq-2.json`]

Both reach the game's no-open-towns UI at the fixed frame-18000 endpoint, with
identical full event sequences and all 36 still hashes.
[E: `scratchpad/wifi-g1-1/safe/comparison.json`; `scratchpad/wifi-g1-1/runs/guest-irq-1/shot_018000.bmp` inspected privately]

Final host runs each accept and complete 18 requests (Enable, PowerOn, 13 channel
measurements, parent parameters, StartParent, SetGameInfo), with 388 separate
beacon notifications and PARENT state 7 from frame 12956 through endpoint 18000.
[E: `scratchpad/wifi-g1-1/safe/host-irq-1.json`, `host-irq-2.json`]

The host's open-gate UI, full event metadata and all 36 still hashes agree within
the final pair; no StartMP request occurs in either full window.
[E: `scratchpad/wifi-g1-1/safe/comparison.json`; `scratchpad/wifi-g1-1/runs/host-irq-1/shot_018000.bmp` inspected privately]

The observed peer boundary is CHILD_CONNECTED. Its handler sets context bit 0x20;
the SetGameInfo callback invokes the StartMP wrapper only when that bit is set.
Thus the synthetic fixture proves the MP transition, while the no-peer game path
does not demonstrate an actual MP submission.
[S: `port/build/shadow/func_ov066_0226908c.c`, `func_ov066_02268798.c`, `func_ov066_022686f0.c`]

Before the IRQ hook, the default clock guest stopped at frame 13181 with accepted
requests still pending; TICK_MODEL=1 reached 18000 but only after its cleanup deadline
expired, showing the communication-abort UI. These are failed, separate clock arms.
[E: `scratchpad/wifi-g1-1/safe/guest-stub-1.json`, `guest-tick-1.json`]

The final fresh link exits 0 with empty stderr and 194/256 dark slots; switch-unset
canonical card32 and explicit card0/2ea19722 comparisons each pass 31/31 EXACT.
[E: `scratchpad/wifi-g1-1/safe/link-summary.json`; `off-irq32-data/offgate-check.json`, `off-irq0-data/offgate-check.json`]

## Hypotheses

Real peer discovery, parent selection, MAC identity assignment, channel dwell-time
fidelity, link loss, MP delivery and real ARM7 timing remain unverified. A two-peer
transport and original-hardware callback comparison would be separate experiments.
[H: compare a future peer run and original callback trace against these contracts]

## Related

- [G0 bootstrap evidence](wifi-g0.md).
- [Protocol map](multiplayer-protocol.md).
- [WM relay contract](../../docs/kb/hybrid/online-spec.md).
- [Runtime router](../../docs/kb/hybrid/wifi.md).
