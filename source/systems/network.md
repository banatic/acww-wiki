# Network

**Summary.** Local town visits and online visits share game communication code but use
different transports. Local multiplayer reaches WM through overlay 66; online play
reaches the DWC, socket and TLS code in overlay 65. The interpreter host currently lacks
the tag-10 ARM7 wireless service. This is a hardware-service gap, not evidence that every
network function is replaced by a stub.
[S: `src/matched/func_020ec338.c:36`, `src/matched/CPS_TcpConnect.c:18`]
[E: `scratchpad/wifi-analysis-1/stage1-evidence.json` host source audit]

## What happens

### The boundary that needs implementing

The common receive handler parses a control envelope and dispatches its message
ID; the facade selects different transport implementations for modes 1/2 and 3/4.
The detailed static map, 24 control IDs, bulk-transfer mechanics and remaining unknowns
are in [Multiplayer protocol](multiplayer-protocol.md).
[S: `src/matched/func_02075050.c:33`, `src/matched/func_020ec338.c:36`]

Local `ov066` starts WM parent/child and MP services; the facade registers two
logical port callbacks on 12 and 13. WM lives in `autoload_2`, not inside `ov065`.
The settings UI's `ov001` data-sharing helper and `ov067` WXC driver are separate
consumers and must not supply assumed constants for town visits.
[S: `src/matched/func_020ecce4.c:49`, `src/matched/func_ov066_0226b9b8.c:101`,
`src/matched/WM_StartMPEx.c:1`, `src/matched/func_ov001_02229e98.c:841`,
`src/matched/WXCi_CallSendEvent.c:377`]

WM's FIFO sender writes tag 10 with a pointer to a request buffer. The current host
dispatch explicitly handles tags 7, 6, 11 and 5, while tag 10 reaches the
accepted-and-dropped fallback. This is a source audit, not a gate-menu execution
receipt or a claim that the gate has already reached that branch.
[S: `src/matched/WMi_SendCommand.c:112`]
[E: `scratchpad/wifi-analysis-1/stage1-evidence.json` host `port/shim/os/pxisend.c:661`]

The earlier page's blanket statement that no network code runs reflected the legacy
native design. It cannot describe the interpreter simply from that policy document;
the concrete unsupported service is the missing tag-10 response contract.
[E: `scratchpad/wifi-analysis-1/stage1-evidence.json`]

### WFC and the ARM9/ARM7 split

WCM provides access-point/DCF connection management; the DWC Internet pump checks phase
9 after connection. SOCL command packets travel through an OS message queue in ARM9
software. Calling that queue an ARM7 socket command pipe is incorrect.
[S: `src/matched/func_ov065_0227f32c.c:58`,
`src/matched/SOCLi_SendCommandPacket.c:3102`]

`CPS_TcpConnect` selects `CPSi_SslConnect` or raw TCP using the session SSL flag.
Replacing the ARM7 radio or forwarding IP therefore does not automatically bypass
ARM9 TLS. A socket-level host replacement must choose and test its TLS boundary.
[S: `src/matched/CPS_TcpConnect.c:18`]

The game's online initializer advances through Internet connection, DWC
initialization/login and friend/transport readiness. It supplies 32 friend records
and later chooses a 256-byte transport split size. These facts do not establish
compatibility with a replacement server.
[S: `src/matched/func_020ec980.c:41`, `src/matched/func_020ec980.c:59`,
`src/matched/func_020ec980.c:75`]

The auth builder requires RTC date/time and AP metadata. A successfully read historical
date alone does not prove the server will reject login: that needs server evidence.
The old claim that the fixed clock necessarily prevents login was unsupported.
[S: `src/matched/func_ov065_02274798.c:579`]

### Source names are not enough

`func_ov066_02268c4c` was copied from a scanning wrapper and still names the scan
callee. The config relocation at callsite `0x02268c64` identifies parent-parameter
setup instead; the owner's inspected shadow also names `WM_SetParentParameter`.
That shadow/map observation is retained with hashes and is not a claim about a newly
built helper executable. [S: `src/matched/func_ov066_02268c4c.c:13`]
[E: `scratchpad/wifi-analysis-1/stage1-evidence.json`]

The stage-1 census found 29,084 matched C/C++ files and 79,747 config call-relocation
rows. Lexical references, missing recovered boundaries and indirect callbacks prevent
that census from being a complete runtime call graph.
[E: `scratchpad/wifi-analysis-1/stage1-evidence.json`]

## Where it lives

| Layer | Module | Entry / evidence |
|---|---|---|
| Common game control receive | main | `0x02075050` to `0x02075240`. [S: `src/matched/func_02075050.c:36`] |
| Transport facade | autoload_2 | `0x020ec338`, `0x020ecce4`, `0x020ec980`. [S: `src/matched/func_020ec338.c:36`, `src/matched/func_020ecce4.c:35`, `src/matched/func_020ec980.c:39`] |
| Local town transport | ov066 | MP start, ports 12/13. [S: `src/matched/func_ov066_022686f0.c:20`, `src/matched/func_ov066_0226b9b8.c:101`] |
| Wireless manager | autoload_2 | `WM_StartMPEx`, `WMi_SendCommand`. [S: `src/matched/WM_StartMPEx.c:1`, `src/matched/WMi_SendCommand.c:74`] |
| Online transport | ov065 | Reliable DWC sender `0x0227eda0`. [S: `src/matched/func_ov065_0227eda0.c:100`] |
| TLS versus raw sockets | ov065 | `CPS_TcpConnect`. [S: `src/matched/CPS_TcpConnect.c:18`] |

## Data it reads and writes

| Data | Established role |
|---|---|
| `0x021fbef8` | Common transport mode. [S: `src/matched/func_020ecce4.c:40`] |
| `0x021fbefc` | Online initialization phase. [S: `src/matched/func_020ec980.c:41`] |
| `0x020ccff0` | Indexed control dispatch. [S: `src/matched/func_02075240.c:5`] |
| WM request buffer | 256-byte ARM9 request slot; FIFO pointer and accepted bit. [S: `src/matched/WMi_SendCommand.c:83`] |
| Friend entry | 12-byte account record plus 0x23-byte game record. [S: `src/matched/func_020eae80.c:33`] |

## How to check it

The staged source census and report are under `scratchpad/wifi-analysis-1/`.
For the first runtime test, capture a bounded gate path with overlay residency,
mode/state values and WM API/callback IDs. Require the requested endpoint, no fault,
and unchanged output with the observer disabled. A quiet single-player log proves
neither multiplayer compatibility nor that all networking is unreachable.
[E: `scratchpad/wifi-analysis-1/stage1-evidence.json`]

## Hypotheses

- Implement WM beneath the preserved ARM9 local stack first; prove initialization
  and scan callback ownership before promising two-town visits.
  [S: `src/matched/WMi_SendCommand.c:83`, `src/matched/WM_StartConnectEx.c:585`]
- Validate the control envelope and bulk offsets before existing receive dispatch:
  some receivers copy an external offset without a visible local bounds check.
  An upstream length-validation audit remains necessary.
  [S: `src/matched/func_02075670.c:25`, `src/matched/func_0207557c.c:15`]

## Related

- [Multiplayer protocol](multiplayer-protocol.md).
- [Implementation options and gates](wifi-port-plan.md).
