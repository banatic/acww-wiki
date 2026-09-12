# Multiplayer protocol: source map and unresolved boundaries

**Summary.** The game has a common communication layer above local WM and online DWC.
The matched source exposes a control-message envelope, chunked bulk transfers, four
participant slots and several synchronization barriers. It does not yet establish the
complete gate-to-arrival sequence or the meaning of every transferred record. This page
separates verified mechanics from names that still need a two-peer trace.
[S: `src/matched/func_02075050.c:33`, `src/matched/func_02075ff8.c:42`,
`src/matched/func_02074330.c:169`]
[E: `scratchpad/wifi-analysis-1/stage1-evidence.json`]

## What happens

### Evidence and scope

This is a static ADMK audit at `d9e1409d8b2a21ba5ffc56e467e881168b46cabb`;
no multiplayer session was run. The reproducible census covers 29,084 matched C/C++ files;
its lexical references include declarations and address-takes and are **not** a resolved
call graph. The config call-relocation census separately supplies address identities.
[E: `scratchpad/wifi-analysis-1/stage1-evidence.json`]

The source layers are `main`'s `0x020730xx..0x02077bxx`, the communication facade in
`autoload_2`'s `0x020eadxx..0x020edaxx`, local `ov066`, and online `ov065`;
the local SDK `WM_*` functions themselves are in `autoload_2`. Overlay names and call
targets were checked against config metadata, not inferred from address prefixes.
[S: `src/matched/func_02075050.c:26`, `src/matched/func_020ecce4.c:35`,
`src/matched/WM_StartMPEx.c:1`] [E: `scratchpad/wifi-analysis-1/stage1-evidence.json`]

Two lookalikes must remain separate: `ov001`'s settings/UI helper starts data sharing on
port 13 with 68 bytes per station and a three-station bitmap; `ov067`'s WXC driver sends
on port 4. Neither fact establishes the visiting-town protocol's WM port or capacity.
[S: `src/matched/func_ov001_02229e98.c:841`, `src/matched/WXCi_CallSendEvent.c:377`]

### Gate and connection state map

`ov048` has a concrete scan-selection path: `func_ov048_02260d28` obtains the scan list,
requires a 0x1a-byte game-info result, compares six peer identifier bytes, and selects the
matching entry through `func_020eb8d8`; it then requests scene state 5. Assigning an exact
human menu choice to this state is still an inference requiring a gate trace.
[S: `src/matched/func_ov048_02260d28.c:42`, `src/matched/func_ov048_02260d28.c:55`,
`src/matched/func_ov048_02260d28.c:64`, `src/matched/func_ov048_02260d28.c:75`]

| Boundary | Source-backed transition or operation | Unresolved meaning |
|---|---|---|
| `func_02074b44`, main, `0x02074b44` | Config calls the local and online initializers; no matched body in this checkout. [E: `scratchpad/wifi-analysis-1/stage1-evidence.json`] | The user-choice-to-mode selector; do not invent its branches. |
| `func_020ecce4` | Stores the requested mode at `0x021fbef8`; clears 16 bytes; prepares configuration bytes 8, 60 and 2; action 1 requests local state 3, action 2 requests state 4. [S: `src/matched/func_020ecce4.c:39`, `src/matched/func_020ecce4.c:55`] | Source suggests local host/guest modes, but screen mapping is unmeasured. |
| `func_020eb92c` | Clears an eight-entry result list and polls eight entries only in local state 7. [S: `src/matched/func_020eb92c.c:12`] | Eight scan results are not eight simultaneous visitors. |
| `func_020eb8d8` | In local state 7, copies the selected descriptor's 0xe0 bytes and passes it to `ov066:0x022682ec`. [S: `src/matched/func_020eb8d8.c:13`] | Descriptor validation beyond this wrapper. |
| `ov066:0x02268c4c` | Calls WM parent-parameter setup; its matched callee name is a copied, incorrect alias. Config and the owner's shadow agree on `WM_SetParentParameter`. [S: `src/matched/func_ov066_02268c4c.c:13`] [E: `scratchpad/wifi-analysis-1/stage1-evidence.json`] | Exact parent settings need their live initializer traced. |
| `ov066:0x02268a1c` | Connect wrapper passes descriptor, null optional SSID, power-save 1 and auth mode 0 to the address of `WM_StartConnectEx`. [S: `src/matched/func_ov066_02268a1c.c:10`] [E: `scratchpad/wifi-analysis-1/stage1-evidence.json`] | Successful connection callback and discovered beacon values. |
| `ov066:0x022686f0` | MP start passes retry count 4 and fixed-frequency flag 1; buffer sizes and frequency come from configuration fields. [S: `src/matched/func_ov066_022686f0.c:20`] [E: `scratchpad/wifi-analysis-1/stage1-evidence.json`] | Actual frequency and parent/child sizes are not literal constants here. |
| `ov066:0x0226b9b8` | Allocates queue metadata and installs callbacks on ports 12 and 13 plus the indication callback. [S: `src/matched/func_ov066_0226b9b8.c:101`] [E: `scratchpad/wifi-analysis-1/stage1-evidence.json`] | Port-to-game-message classification and callback identity. |
| `func_020ec338` | Modes 1/2 use the local receive-buffer path; modes 3/4 use the online path, narrowing AID to u8. [S: `src/matched/func_020ec338.c:36`] [E: `scratchpad/wifi-analysis-1/stage1-evidence.json`] | This is buffer registration, not a demonstrated send operation. |
| `func_020ec848` | Requests local stop state 0, waits for state 2 with a tick timeout, tears down callbacks/work, then sets mode 6. [S: `src/matched/func_020ec848.c:19`] | Save/rollback consequences are outside this wrapper. |

### WM service contract

The FIFO word on tag 10 is an ARM9-memory request pointer, not a network packet.
`WMi_SendCommand` borrows a 256-byte request slot, tests the accepted bit 0x8000, stores
the API identifier and parameter words, sends the pointer, and returns an asynchronous
status. A host bridge must reproduce request ownership, status and later callbacks.
[S: `src/matched/WMi_SendCommand.c:68`, `src/matched/WMi_SendCommand.c:83`,
`src/matched/WMi_SendCommand.c:106`]

WM parent parameters contain user-game-info pointer/length, GGID, TGID, entry/max-entry,
key-sharing/carrier-sense flags, beacon period, channel and parent/child maximum sizes;
the structure is 64 bytes in this ARM layout. Validation caps each direction at 512 bytes,
including extra key-sharing overhead where enabled.
[S: `src/matched/WM_SetParentParameter.c:127`, `src/matched/WM_SetParentParameter.c:190`,
`src/matched/WM_SetParentParameter.c:202`]

The connect request contains a 24-byte optional SSID field and a BSS descriptor pointer.
This is distinct from the BSS descriptor's 32-byte SSID storage and its WM game-info.
The generic game-info structure reserves 112 bytes of user data; these are SDK capacities,
not a claim that the gate transmits all 112 bytes.
[S: `src/matched/WM_StartConnectEx.c:361`, `src/matched/WM_StartConnectEx.c:382`,
`src/matched/WM_StartConnectEx.c:534`, `src/matched/WM_StartConnectEx.c:589`]

MP startup requires parent/child states 7/8, receive alignment to 64 bytes and send size
alignment to 32 bytes; the request sends half the receive-buffer byte size, accounting
for the receive double buffer. MP send in states 9/10 carries data address, byte size,
destination bitmap, logical port, priority and callback/context; it checks a further
4-byte parent or 2-byte child header allowance.
[S: `src/matched/WM_StartMPEx.c:67`, `src/matched/WM_StartMPEx.c:86`,
`src/matched/WM_StartMPEx.c:104`, `src/matched/WM_SetMPDataToPortEx.c:117`,
`src/matched/WM_SetMPDataToPortEx.c:131`]

Generic data sharing has four dataset buffers, a station bitmap and per-station length,
with aggregate data limited to 508 bytes plus a 4-byte bitmap header. Generic key sharing
is a call to that service with length 2, bitmap 0xffff and double buffering. This audit
does **not** establish that the game's `ov066` visit path uses either convenience API;
port 13 alone cannot establish it.
[S: `src/matched/WM_StartDataSharing.c:42`, `src/matched/WM_StartDataSharing.c:182`,
`src/matched/WM_StartKeySharing.c:80`]

### Online login and transport

The game-level online state machine is `func_020ec980`, keyed by `0x021fbefc`:
0 initializes/connects, 1 waits for Internet status 4, 2 initializes the DWC control
with a 32-entry friend list and begins login, 3 waits on the callback flag, 4 waits
for the next completion and sets the transport split maximum to 0x100, and 5 reports
readiness under mode-specific guards. Those are source states, not observed durations.
[S: `src/matched/func_020ec980.c:41`, `src/matched/func_020ec980.c:59`,
`src/matched/func_020ec980.c:70`]

The Internet pump checks access-connect completion and WCM DCF phase 9. This is
ARM9 connection-manager work. Auth preparation requires successful RTC reads and
access-point metadata; the server's later interpretation of the date is not proved
by a successful RTC read.
[S: `src/matched/func_ov065_0227f32c.c:58`, `src/matched/func_ov065_02274798.c:579`]

Friend-key checking forwards the user-data field at +0x24 and checks a seven-bit CRC8
result over eight bytes using polynomial 7. This establishes a consistency check,
not peer authentication. The facade's friend deletion operates on 12-byte account
records and a second array of 0x23-byte records; login initializes 32 entries.
[S: `src/matched/DWC_CheckFriendKey.c:12`, `src/matched/DWC_Acc_CheckFriendKey.c:36`,
`src/matched/func_020eae80.c:30`, `src/matched/func_020ecba8.c:50`]

Reliable DWC send records the requested size and busy state, emits an eight-byte
transport header, then sends chunks limited by the configured split size and available
GT2 space. It returns accepted before necessarily finishing; the send callback marks
completion. The generic split clamp is 1465, while the game configures 256.
[S: `src/matched/func_ov065_0227eda0.c:100`, `src/matched/func_ov065_0227eda0.c:122`,
`src/matched/func_ov065_0227ee90.c:96`, `src/matched/func_ov065_0227ecd0.c:129`,
`src/matched/func_020ec980.c:75`]

The exact NAS-to-GPCM/GPSP-to-NatNeg-to-GT2 callback chain remains partially unresolved:
the retained graph records direct edges and missing alias resolutions; it does not
turn the presence of GameSpy libraries into a proven sequence for this game.
[E: `scratchpad/wifi-analysis-1/stage1-evidence.json`]

### Game envelope, dispatch and bulk data

The common receive handler `func_02075050` reads one envelope byte. Bits 0..1 are a
two-bit status value; bit 7 selects control dispatch; bits 2..6 contain a five-bit
message ID. IDs below 24 go through `func_02075240` with the envelope removed and
length reduced by one. A separate bulk-data path updates the queue and registers a
0x1000-byte receive buffer. The meaning of the two status bits is not named here.
[S: `src/matched/func_02075050.c:33`, `src/matched/func_02077b14.c:6`,
`src/matched/func_02077b20.c:6`, `src/matched/func_02077b28.c:5`,
`src/matched/func_02075240.c:7`]

The sender `func_02075ff8` chunks bulk data into at most 0xffb data bytes and adds
one envelope byte plus a four-byte offset, producing at most 0x1000 bytes. Its
one-byte chunk counter advances only when the queue accepts the chunk. This is a
game-level chunking rule, separate from WM frames and DWC's 256-byte split setting.
[S: `src/matched/func_02075ff8.c:42`, `src/matched/func_02075ff8.c:55`]

Dispatch IDs below are derived from config pointer-relocation **metadata**, checked
against each matched handler. They describe behavior, not original message names;
the receipt retains source citations and the derivation without source or payload data.
[S: `src/matched/func_02075240.c:5`] [E: `scratchpad/wifi-analysis-1/stage1-evidence.json`]

| ID | Handler | Established operation, not an invented protocol name |
|---|---|---|
| 0 | `0x020756cc` | Mode 12: consumes a participant low-nibble bitmap and two high bits. [S: `src/matched/func_020756cc.c:10`] |
| 1 | `0x02075670` | Mode 12: offset-prefixed copy into a bulk destination; completion threshold defaults to 0x17400 or computed compressed length +4. [S: `src/matched/func_02075670.c:22`] |
| 2 | `0x0207560c` | Offset-prefixed copy into a per-participant record; empty body selects its reset path. [S: `src/matched/func_0207560c.c:12`] |
| 3 | `0x020755b4` | One-byte reset alternative, otherwise a 0x950-byte copy into record index 4. [S: `src/matched/func_020755b4.c:18`] |
| 4 | `0x0207557c` | Offset-prefixed copy through record index `sender + 3`. [S: `src/matched/func_0207557c.c:15`] |
| 5 | `0x0207556c` | Forwards one byte and sender index to `0x020a6f74`. [S: `src/matched/func_0207556c.c:7`] |
| 6 | `0x02075548` | Splits one byte into low-three-bit and high-nibble values. [S: `src/matched/func_02075548.c:8`] |
| 7 | `0x0207553c` | Requests `0x020a6cd4(1)`. [S: `src/matched/func_0207553c.c:7`] |
| 8 | `0x02075514` | Changes communication substate only when its current value is 3. [S: `src/matched/func_02075514.c:9`] |
| 9 | `0x020754e8` | In modes 13/47, sets a transaction flag through `0x020a125c`. [S: `src/matched/func_020754e8.c:9`] |
| 10 | `0x020754b0` | Mode 12: eight-byte transfer and completion flag; copy direction in this reconstruction requires shadow/register-flow audit. [S: `src/matched/func_020754b0.c:24`] |
| 11 | `0x02075484` | Modes 13/47: transaction flag through `0x020a1274`. [S: `src/matched/func_02075484.c:14`] |
| 12 | `0x02075450` | Offset-prefixed copy into the communication object's buffer. [S: `src/matched/func_02075450.c:13`] |
| 13 | `0x02075448` | Tail-call target remains unnamed in the matched file. [S: `src/matched/func_02075448.c:8`] |
| 14 | `0x02075404` | Modes 46/9: sender-specific byte delivery, with host/guest slot remapping. [S: `src/matched/func_02075404.c:10`] |
| 15 | `0x020753a8` | Four two-byte records decoded and applied through `0x020a7394`; actor-field meaning not yet established. [S: `src/matched/func_020753a8.c:18`] |
| 16 | `0x02075380` | Mode 46: sender flag through `0x020a1200`. [S: `src/matched/func_02075380.c:14`] |
| 17 | `0x02075358` | Mode 46: sender flag through `0x020a11f8`. [S: `src/matched/func_02075358.c:14`] |
| 18 | `0x02075334` | Mode 46: flag through `0x020a126c`. [S: `src/matched/func_02075334.c:14`] |
| 19 | `0x0207530c` | Mode 46: sender flag through `0x020a1208`. [S: `src/matched/func_0207530c.c:9`] |
| 20 | `0x02075300` | Forwards sender and length to `0x020a11e0`. [S: `src/matched/func_02075300.c:7`] |
| 21 | `0x020752a8` | Mode 46: offset-prefixed copy through `0x020984e8`; destination binding needs an alias audit. [S: `src/matched/func_020752a8.c:27`] |
| 22 | `0x02075278` | Offset-prefixed copy through `0x020989e0`. [S: `src/matched/func_02075278.c:13`] |
| 23 | `0x02075254` | Mode 46: completion flag through `0x020a11b8`. [S: `src/matched/func_02075254.c:9`] |

### Town state, synchronization and rollback limits

A save/transaction helper copies 0x173fc bytes from `0x021dc7a8` to a temporary buffer
before a multistage operation; a later branch copies them back. This establishes
save-sized staging, **not** that every visitor receives an uncompressed save bank.
The bulk receiver's 0x17400 completion size and its compressed-length alternative
need to be joined to this staging path before naming the complete town-transfer format.
[S: `src/matched/func_020a03e0.c:63`, `src/matched/func_020a03e0.c:113`,
`src/matched/func_02075670.c:31`]

The communication update loops over participant indices 0..3 and builds three remote
send descriptors. It advances queue indices after accepted sends and sets status bits
when the expected participant bitmap or connection check fails. That proves a
four-slot, acknowledged-buffer design; it does not prove deterministic input lockstep,
the actor-coordinate representation, the exact update frequency, or shared gameplay RNG.
[S: `src/matched/func_02074330.c:169`, `src/matched/func_02074330.c:213`,
`src/matched/func_02074330.c:370`]

`func_020a2dec` uses repeated failure guards and explicit barrier flags: states 14/15
wait for outstanding participant work and completion, send IDs 17/19, and progress
to a disconnect-waiting state. Its final/error helper at `0x020a0848` is unmatched;
the exact persistent outcome after a lost peer is therefore still open.
[S: `src/matched/func_020a2dec.c:146`, `src/matched/func_020a2dec.c:168`,
`src/matched/func_02075918.c:24`, `src/matched/func_02075848.c:22`]

## Where it lives

| Layer | Best first source / question |
|---|---|
| Gate scan selection | `func_ov048_02260d28`; bind its state 5 to a captured menu transition. [S: `src/matched/func_ov048_02260d28.c:75`] |
| Mode selector | Unmatched `main:0x02074b44`; entry bridge required before a full gate state graph is claimed. [E: `scratchpad/wifi-analysis-1/stage1-evidence.json`] |
| Shared receive dispatch | `func_02075050` -> `func_02075240`. [S: `src/matched/func_02075050.c:36`] |
| Local transport | `ov066:0x0226ae50` -> WM port send; callback binding at `0x0226b9b8`. [S: `src/matched/func_ov066_0226ae50.c:9`, `src/matched/func_ov066_0226b9b8.c:101`] [E: `scratchpad/wifi-analysis-1/stage1-evidence.json`] |
| Online transport | Reliable sender `ov065:0x0227eda0`; connection readiness/space predicate `0x0227ee90`. [S: `src/matched/func_ov065_0227eda0.c:100`, `src/matched/func_ov065_0227ee90.c:96`] |

## Data it reads and writes

The mode byte is `0x021fbef8`, online state halfword `0x021fbefc`, and common
communication-object pointer slot `0x020ccf94`; the control dispatcher is indexed
at `0x020ccff0`. These are DS addresses, with source alias repairs retained in the receipt.
[S: `src/matched/func_020ecce4.c:39`, `src/matched/func_020ec980.c:41`,
`src/matched/func_02074330.c:110`, `src/matched/func_02075240.c:5`]

## How to check it

Re-run `python -B scratchpad/wifi-analysis-1/source_index.py` and
`python -B scratchpad/wifi-analysis-1/reloc_graph.py`, then the evidence/gate script
in the staged report. The first **runtime** receipt should be a bounded gate-menu
trace with overlay ID, mode/state writes, WM API IDs and callback ordering; no
payload dump is needed. Source review alone cannot produce that receipt.
[E: `scratchpad/wifi-analysis-1/stage1-evidence.json`]

## Hypotheses

- Local modes 1/2 mean host/guest; settle by tracing the choice-to-`0x02074b44` bridge,
  not by translating a numeric mode from an unrelated SDK. [S: `src/matched/func_020ecce4.c:55`]
- Bulk IDs 1/2/4/21/22 cover town and player subrecords; their exact field meanings,
  roster representation, letters, item ownership and chat serialization remain open.
  Settle with producer/consumer field walks and synthetic field mutations before a
  visitor run. [S: `src/matched/func_02075670.c:25`, `src/matched/func_0207557c.c:15`]
- The four-slot and barrier machinery constrains larger-party mods. Raising WM's
  max-entry alone cannot change these explicit loops; the required game changes are
  not yet enumerated exhaustively. [S: `src/matched/func_02074330.c:169`,
  `src/matched/func_020760bc.c:37`]

## Related

- [Network boundaries](network.md).
- [Implementation options and gates](wifi-port-plan.md).
