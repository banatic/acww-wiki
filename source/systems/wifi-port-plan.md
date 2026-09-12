# Wi-Fi port plan

**Summary.** Proposed order: preserve the ARM9 game/WM code, implement a bounded ARM7
WM service for two ports on one host, prove two towns on a LAN, then evaluate WFC and
emulator peers independently. No networking implementation or compatibility run was
performed for this analysis. All costs below are planning estimates.
[E: `scratchpad/wifi-analysis-1/stage1-evidence.json`, `scratchpad/wifi-analysis-1/external-research.json`]

## Evidence and estimate boundaries

The [protocol map](multiplayer-protocol.md) contains source facts and explicit gaps.
`S` means the cited matched source supports the statement; it does not prove host
execution. External references below are primary upstream documents inspected on
2026-09-11, recorded with URLs, retrieval times, hashes or fetch errors in
`scratchpad/wifi-analysis-1/external-research.json` (R1-R19). Their `E` markers refer to
that research receipt, **not** a passed game/server test. Design choices and cycle
ranges are marked **Proposal/Estimate**, never upgraded to observed compatibility.
[E: `scratchpad/wifi-analysis-1/external-research.json`]

An estimated cycle means one bounded implementation, its fixture, the owner's
serialized build/run and review. It is not a fixed number of hours. Ranges exclude
unbounded reverse engineering of unmatched code and server maintenance. A failed
first gate replaces the remaining estimate; elapsed builds are not progress evidence.
[E: `scratchpad/wifi-analysis-1/external-research.json` decisions]

## A. WM service over host transport

### Contract to retain

WM submits tag-10 pointers to 256-byte request slots with ownership state, and returns
asynchronous acceptance. MP send requests contain a DS data pointer, length, destination
bitmap, logical port, priority and callback/argument. These pointers are process-local
emulated addresses, not fields to transmit to another host.
[S: `src/matched/WMi_SendCommand.c:83`, `src/matched/WMi_SendCommand.c:112`,
`src/matched/WM_SetMPDataToPortEx.c:131`]

The local town driver registers ports 12/13, uses MP priority 2 and a retry count of 4.
WM checks parent/child state and buffer capacities before starting MP; the receive
buffer has a double-buffer convention. The game has a separate 4096-byte assembly
buffer and chunks with up to 4091 data bytes plus five framing bytes. That is not a
single legal WM radio payload; the intervening local assembly path still needs audit.
[S: `src/matched/func_ov066_0226b9b8.c:101`, `src/matched/func_ov066_0226ae50.c:9`,
`src/matched/func_ov066_022686f0.c:20`, `src/matched/WM_StartMPEx.c:67`,
`src/matched/WM_StartMPEx.c:104`, `src/matched/func_02075ff8.c:42`]

**Proposal.** Add a narrow tag-10 dispatch in `port/shim/os/pxisend.c`; put request
decoding, state and replies in a new `port/shim/net/wm_service.c`, with host transport
and fixtures in separately named files selected by the owner. Keep WM/game functions
interpreted initially: no bulk promotion or matched-source edits. Queue incoming
host events and execute DS callbacks only on the emulation thread at scheduled ticks.
Copy/validate a request while owned, release it once, and retain callback storage until
the documented completion lifetime ends. Reset/disconnect must cancel stale generations.
[S: `src/matched/WMi_SendCommand.c:83`, `src/matched/WM_SetMPDataToPortEx.c:131`]

**Proposal.** First transport is two processes on loopback, then private LAN UDP with
explicit room/session IDs, protocol version, sender identity, sequence numbers and
bounded lengths. Preserve parent/AID mapping, destination bitmaps, logical ports,
priority, retry and completion distinctions. Define loss, duplicates, stale packets,
queue saturation and cancellation before adding automatic discovery. TCP is possible
for control, but a lost stream segment must not silently change MP completion/timing.
These are new host framing requirements, not a recovered Nintendo wire format.
[S: `src/matched/WM_SetMPDataToPortEx.c:117`, `src/matched/WM_SetMPDataToPortEx.c:131`]

**Timing gap.** The call supplies MP frequency/configuration, but this audit has not
bound the live configuration to gate states or measured an MP epoch duration. Four-way
game barriers do not establish per-frame input lockstep or a fixed 60 Hz network tick.
Measure submit/completion/receive order against emulated time before selecting pacing.
[S: `src/matched/func_ov066_022686f0.c:20`, `src/matched/func_02074330.c:169`,
`src/matched/func_02074330.c:370`]

**Proposal.** An Internet relay would coordinate room membership, parent epochs,
bounded retransmission and delivery acknowledgments without inventing game success.
Separate network arrival time from emulated execution time; stop or disconnect a slow
peer under an explicit policy. Begin with measured delay/loss injection on loopback.
Do not promise arbitrary-latency local-wireless emulation or add a relay before LAN
timing is stable. A relay can forward validated envelopes; it does not understand town
authority or resolve conflicting save changes automatically.
[S: `src/matched/func_02074330.c:213`, `src/matched/func_020a03e0.c:113`]

| Proposed unit | Estimate | First receipt / stop condition |
|---|---:|---|
| A0 observe the gate and WM state/callback contract | 1-2 cycles | Bounded keyed host and guest menu paths reach identified mode/state/API IDs; no fault; observer OFF equivalence. Missing bridge semantics stop an implementation assumption. |
| A1 initialize/reset and one synthetic MP request | 2-4 | Fixture proves request ownership, state errors, one completion, cancellation, and no callback after reset. One real gate initialization reaches its next recorded state. |
| A2 two processes discover/connect/send | 3-6 | Guest lists exactly the intended host using private test identities; AID/bitmap agree; one accepted send reaches exactly one intended receive and completion on ports 12/13. |
| A3 two towns, arrival and clean departure | 4-10+ | Equal permitted region/count summaries across the town transfer, actor movement observed on both sides, departure returns each participant safely; no exported payload. Unknown actor/rollback semantics may dominate. |
| A4 fault handling and Internet relay exploration | 3-8+ | Duplicate/loss/delay/disconnect matrix has bounded outcomes, then one remote pair with pinned delay/loss and room identity. No universal NAT or latency claim. |

All A ranges and receipt definitions are proposals; nothing in this table passed yet.
[E: `scratchpad/wifi-analysis-1/external-research.json` decisions]

### Emulator peers

The retrieved [melonDS releases](https://github.com/melonDS-emu/melonDS/releases)
include LAN support, and pinned upstream
[LAN.cpp](https://github.com/melonDS-emu/melonDS/blob/906e9ebb27da8c6a715cd7abab4abfe8a8d29427/src/net/LAN.cpp)
implements ENet session/control exchange and timestamped MP command/reply/ack traffic.
This is a plausible **later test peer**. An adapter must translate the emulated radio
exchange, identities and timing; sharing UDP or the label NiFi does not make a WM
service datagram compatible. Its internal player limit is not ACWW's visitor limit.
[E: `scratchpad/wifi-analysis-1/external-research.json` R7-R8]

The primary [DeSmuME FAQ](https://wiki.desmume.org/index.php?title=Faq) was visible in
search-index evidence as experimental/unsupported Wi-Fi, but a fresh page fetch failed.
Older official support posts cannot certify a current binary. DeSmuME is an exploratory
peer with **unverified current support**, not an acceptance dependency. Record exact
build, Wi-Fi backend and one beacon/association/MP exchange before claiming compatibility.
[E: `scratchpad/wifi-analysis-1/external-research.json` R9]

**Estimate.** A separate melonDS bridge investigation is 2-4 cycles to one discovery or
association receipt, then 4-10+ to a town visit if the timing/model is compatible.
DeSmuME starts with a 1-cycle feasibility check, not a town-play estimate. Emulator-to-
emulator LAN, port-to-port LAN and port-to-emulator are three independent gates.
[E: `scratchpad/wifi-analysis-1/external-research.json` decisions, R8-R9]

## B. WFC replacement and socket boundary

### What exists, and what is not verified

| Candidate | Documentary evidence | Proposed use / limitation |
|---|---|---|
| [DWC network server emulator / altWFC lineage](https://github.com/barronwaffles/dwc_network_server_emulator) | Public AGPL server code; README still specifies Python 2.7 and legacy dependencies. | Most concrete self-host starting point; pin a revision and modernize/isolate dependencies before testing. No ADMK login or visit receipt. [E: `scratchpad/wifi-analysis-1/external-research.json` R1] |
| Historical CoWFC setup | The upstream setup guide was edited in 2018 and targets old Ubuntu releases. | Evidence of a fork/deployment lineage, not a command to run today or a maintained service claim. [E: `scratchpad/wifi-analysis-1/external-research.json` R2] |
| Wiimmfi service | Kaeru's primary project page identifies Wiimmfi as its auth backend. This audit could not retrieve the Wiimmfi game-status page. | Potential hosted compatibility reference; self-host source availability, current ADMK support and service uptime remain unverified here. [E: `scratchpad/wifi-analysis-1/external-research.json` R4, R10] |
| [Kaeru WFC](https://kaerudev.kaeru.world/projects/wfc) | DNS-configured authentication proxy to Wiimmfi, using ndsconstraint. | Complements a hosted replacement; not evidence of a complete independent open-source private server. [E: `scratchpad/wifi-analysis-1/external-research.json` R4] |
| New minimal private service | Design option only. | Full control, but NAS/profile/friends/matchmaking/NAT/transport compatibility still must be implemented and tested; more uncertainty than adapting a pinned existing server. [E: `scratchpad/wifi-analysis-1/external-research.json` decisions] |

The upstream compatibility wiki's broad 2019 assertion is not an ADMK-specific 2026
test. Public documentation availability is not service liveness. None of these
services was deployed, authenticated against or used for a town visit in this unit.
[E: `scratchpad/wifi-analysis-1/external-research.json` R3-R4, R10]

### Endpoint inventory: external defaults, not captured ADMK destinations

The upstream [configuration](https://github.com/barronwaffles/dwc_network_server_emulator/blob/2c65a9f6afe508e236c222bd1b8f26fd63621a91/altwfc.cfg)
and server listeners supply this initial service inventory. DNS must route the
selected namespace consistently; an auth-only redirect is not the whole connection.
No embedded ROM endpoint strings were exported. Exact ADMK DNS names, selected
regional aliases and successful request order remain a runtime/source-boundary gate.
[E: `scratchpad/wifi-analysis-1/external-research.json` R11-R18]

| Role | Public upstream namespace / default | Boundary to verify |
|---|---|---|
| Connection test and NAS | `conntest` / `nas` under the documented WFC namespace; Apache frontends proxy NAS to internal port 9000 | HTTP/SSL frontend and backend are distinct. Port 9000 is not an inferred DS destination. [E: `scratchpad/wifi-analysis-1/external-research.json` R17-R18] |
| Profile/presence (GPCM) | GameSpy profile service, TCP 29900 | NAS identity must bind to a profile/friend session. Exact ADMK hostname unresolved. [E: `scratchpad/wifi-analysis-1/external-research.json` R11-R12] |
| Player search (GPSP) | `gpsp.gs.nintendowifi.net`, TCP 29901 in public server documentation/source | Friend search is separate from profile presence. [E: `scratchpad/wifi-analysis-1/external-research.json` R11, R13] |
| Query/report | Game-specific `*.master.gs` / `*.available.gs` namespace, default 27900 | Validate heartbeat/report data and advertised peer address; do not export game keys. [E: `scratchpad/wifi-analysis-1/external-research.json` R11, R15] |
| Server browser | Default 28910 | Query service is separate from the selected game peer; exact ADMK domain unresolved. [E: `scratchpad/wifi-analysis-1/external-research.json` R11, R16] |
| NAT negotiation | UDP 27901 | Exchanged addresses and NAT outcomes need a two-peer receipt; it is not a universal game relay. Exact ADMK NAT hostname unresolved. [E: `scratchpad/wifi-analysis-1/external-research.json` R11, R14] |
| Game data | Negotiated peer endpoints, not a universal fixed server port | DWC reliable send chunks to its connection; pin connection/address discovery before describing GT2 traffic as working. [S: `src/matched/func_ov065_0227eda0.c:100`] |

### Shutdown, certificates, and the CPU boundary

[Nintendo's game page](https://www.nintendo.com/de-de/Spiele/Nintendo-DS/Animal-Crossing-Wild-World-270011.html)
records WFC shutdown on 2014-05-20. This is a service-lifecycle fact, not proof that an
expired Nintendo CA causes the port's failure. This audit did not inspect certificates
or establish their expiration/ADMK validity checks. Keep that premise **unverified**.
[E: `scratchpad/wifi-analysis-1/external-research.json` R6]

The primary [ndsconstraint description](https://github.com/KaeruTeam/nds-constraint)
describes a DS certificate-chain validation defect and an SSLv3-compatible server
requirement. The altWFC wiki documents client SSL patching for servers without that
mechanism. These are alternative legacy-client connection techniques, not evidence
that DNS alone repairs every server or that modern TLS can accept the old handshake.
No patch bytes, certificates or keys are included here.
[E: `scratchpad/wifi-analysis-1/external-research.json` R5, R19]

`CPS_TcpConnect` branches to SSL in ARM9 according to session state; SOCL posts OS
messages in ARM9. Therefore an ARM7 radio/IP bridge retains that SSL problem. The
auth builder also requires RTC/AP metadata and the Internet pump observes WCM phase.
Replacing a socket does not satisfy those state contracts automatically.
[S: `src/matched/CPS_TcpConnect.c:18`, `src/matched/SOCLi_SendCommandPacket.c:3102`,
`src/matched/func_ov065_02274798.c:579`, `src/matched/func_ov065_0227f32c.c:58`]

**Proposal.** Compare two explicit boundaries: (B-low) implement WCM/DCF/IP beneath
the existing CPS stack, preserving its SSL and DNS behavior; (B-socket) adapt SOCL/CPS
operations to host sockets and explicitly replace SSL session connect/read/write/close
behavior, plus resolver and AP status. For a private loopback service, application
plaintext can cross that chosen boundary; for a remote service, choose a host TLS
proxy with normal server authentication. Merely changing `CPS_TcpConnect` to raw TCP
leaves other SSL-session behavior unaudited. Keep DWC/NAS/GameSpy logic interpreted
until operation-level fixtures prove a reason to promote a specific function.
[S: `src/matched/CPS_TcpConnect.c:18`, `src/matched/func_020ec980.c:41`]

**Proposal.** New files would be a host socket/session adapter under `port/shim/net/`,
an endpoint-profile/resolver adapter, and fixtures for blocking/nonblocking results,
partial reads/writes, timeouts, DNS failure and close/cancel. Exact symbols requiring
registry overrides are an A0/B0 trace result, not a preapproved list of bulk native
promotions. Each selected SOCL/CPS function must pass the project's per-function
differential gate; SDK names alone do not prove host ABI correctness.
[S: `src/matched/SOCLi_SendCommandPacket.c:3102`, `src/matched/CPS_TcpConnect.c:18`]

| Proposed unit | Estimate | First measurable receipt |
|---|---:|---|
| B0 dependency and socket/TLS boundary probe | 1-3 cycles | One selected DS operation has known caller/SSL state/result/async lifetime; one private synthetic host socket fixture passes, without claiming login. |
| B1 pinned private server bring-up | 2-5 | Local health and synthetic NAS/profile roundtrip in isolated environment; revision/config hash and listener inventory, no credentials/payload in report. |
| B2 port login/friends | 4-8+ | Two private identities reach game's online phase 5, mutual friend/presence result, then clean logout. Failures are tied to the exact DNS/auth/profile boundary. |
| B3 match, peer transport, visit/departure | 5-12+ | Two independent clients negotiate a peer and complete arrival/departure with private save backups and consistency summaries. |
| New server instead of adapting lineage | 12-30+ | First gate remains synthetic NAS/profile roundtrip; estimate does not include all games, moderation or operations. |

All B ranges are estimates. A and B can share game-protocol research but are not one
transport implementation; no server credentials or infrastructure decisions are
needed to finish this documentation stage.
[E: `scratchpad/wifi-analysis-1/external-research.json` decisions]

## C. Modding without inventing protocol semantics

The common control receive entry is `0x02075050`, dispatch is `0x02075240`, and
offset-based bulk handlers include `0x02075670` and `0x0207557c`. The dispatch has 24
established IDs, but many payload meanings are unresolved. Validation needs upstream
length, index, transfer-capacity and state checks before accepting external mutation.
[S: `src/matched/func_02075050.c:33`, `src/matched/func_02075240.c:5`,
`src/matched/func_02075670.c:25`, `src/matched/func_0207557c.c:15`]

**Proposal.** Begin with an observer that records ID/length/sender/state/counts only.
Then add an explicit validation/policy hook before dispatch in a new
`port/shim/net/game_protocol.c` (proposed name), with version negotiation in host room
metadata. Original peers get original messages; custom IDs require all participants
to negotiate the extension. Observe-only mode must not alter event order or saves.
Promoting the receive function is optional and needs its own differential proof.
[S: `src/matched/func_02075050.c:36`, `src/matched/func_02075240.c:5`]

| Desired mod | Actual work and constraint | Estimate / first receipt |
|---|---|---|
| More visitors | Game loops/bitmaps encode four participants and three remote descriptors. WM maximum entry and SDK buffer limits are only lower-layer limits. Audit all actor slots, masks, save records, UI and failure barriers before changing capacity. [S: `src/matched/func_02074330.c:169`, `src/matched/func_02074330.c:213`, `src/matched/func_020760bc.c:37`] | 2-4 cycles for a complete capacity inventory; 12-30+ for a deliberately bounded 5-participant prototype. Unlimited capacity is not a defensible target. First receipt: fifth synthetic participant is rejected safely by unchanged protocol, then every intended expanded structure has a bound. |
| Cross-town item trade | Locate actual item inventory mutators and item message semantics first; ID names in this map do not establish a trade protocol. Proposal: transaction IDs, validation, escrow/commit and crash recovery, with a test save fork. Friend-key CRC is not authorization. [S: `src/matched/DWC_Acc_CheckFriendKey.c:36`, `src/matched/func_020a03e0.c:63`, `src/matched/func_020a03e0.c:113`] | 3-6 cycles semantic inventory; 4-10+ transaction prototype. First receipt: one synthetic item transfer has conserved count under disconnect before/after each commit point. |
| Custom events | Shared dispatch can carry negotiated extension intent, but actor actions, RNG and event progression authority remain unmapped. Proposal: host-authoritative event state with explicit version/participant agreement; no assumed RNG lockstep. [S: `src/matched/func_020753a8.c:10`, `src/matched/func_02074330.c:370`] | 2-4 cycles observer/schema exploration; 3-8+ one event. First receipt: a harmless negotiated event is applied once on both clients; replay and unknown version are rejected. |

All C ranges and new behavior are proposals. Save-sized staging copies 0x173fc bytes
and conditionally restores them, but that is not proof of the persistent save schema,
atomic rollback or a safe cross-town trade. Persistent schema/checksum and save-owner
rules must come from the save-flow analysis before write hooks. No change to saves
was made in this unit.
[S: `src/matched/func_020a03e0.c:63`, `src/matched/func_020a03e0.c:113`]

## Recommended sequence and acceptance ladder

**Recommendation (design judgment).** Choose A0-A2 first, with two isolated private
port identities on one machine and no custom game messages. This tests the concrete
missing tag-10 service while preserving the existing game protocol. Gate A3 before
expanding visitor count, then choose B only if original WFC-style friendship/Internet
interoperability is a product requirement. An emulator bridge has its own experiment;
neither it nor an Internet relay is a prerequisite for the first WM receipt.
[E: `scratchpad/wifi-analysis-1/stage1-evidence.json`, `scratchpad/wifi-analysis-1/external-research.json` decisions]

| Gate | Required artifact | Does not establish |
|---|---|---|
| G0 route and state | Two bounded host/guest menu traces: exact launcher, executable/artifact hash, keyed path, frame endpoint, resident overlays, mode/state IDs and WM submit/callback IDs. Unmatched bridge addresses retained. | That a scan result is a valid peer or callbacks are correct. |
| G1 request ownership | Synthetic invalid state, queue full, duplicate completion and reset/cancel cases; exactly one terminal outcome per accepted request. A real initialization reaches a pinned next state. | A usable MP data channel. |
| G2 one peer and one packet | Two process identities, one intended discovery result, association/AID agreement, exact logical port/length/destination count, one receive and one completion. Negative wrong-room/late-generation cases. | A town transfer, actor sync, original emulator compatibility or Internet play. |
| G3 visit and departure | Both endpoints reach the same identified visit phase, private town/participant data counts agree, both observe a scripted movement, clean departure and return are recorded. | Persistent rollback under interruption or all gameplay features. |
| G4 interrupted session | Kill only the recorded test PID or inject loss at each transfer/commit boundary; reconnect/cancel has bounded result; private save before/after summaries obey the chosen conservation rules. | Unlimited visitors or protection from untrusted mod clients. |
| G5 optional new backend | Repeat G2-G4 for each specific emulator build, relay mode or WFC server revision; add login/friend/match gates for WFC. | Compatibility with other builds/servers/regions or all NAT types. |

These are proposed acceptance criteria, not completed experiments. A receipt exports
IDs, addresses, counts, durations and hashes, never raw town/player/packet data, secrets
or certificates. Each future observer has an OFF-equivalence check and an exact fault
identity; bounded timeout termination is not a passed endpoint.
[E: `scratchpad/wifi-analysis-1/external-research.json` decisions]

### Owner decisions before implementation

| Decision | Recommended first choice | Consequence of choosing more |
|---|---|---|
| First supported pair | Port-to-port, same ADMK revision, loopback then LAN | Emulator/real-DS peers require distinct framing/timing and compatibility evidence. |
| Hosting | No external server for G0-G3 | WFC/relay work needs a hosting/maintenance owner, persistent identity policy and a selected server revision. |
| NAT | Explicit same-LAN pairing first | Direct Internet needs address discovery/forwarding tests; relay needs capacity, lifecycle, slow-peer policy and operating ownership. |
| Trust | Private participants; validate every inbound length/index/state | Public/untrusted peers require authentication, abuse limits, authority policy and a reviewed mutation boundary. CRC friend-key consistency is insufficient. |
| Save changes | Separate private save copies and reversible tests | Cross-town persistent modifications require an agreed commit/rollback policy, conservation rules and recovery tests. |
| Compatibility versus mods | Original four-participant behavior first | New IDs/capacity/events require versioned opt-in and a clear incompatibility boundary. |

These are implementation choices, not blockers for this documentation unit. No
hosting account, credentials or server deployment was requested from the owner.
[E: `scratchpad/wifi-analysis-1/external-research.json` decisions]

### Ranked open questions

| Priority | Unknown | Cheapest next evidence / gate |
|---|---|---|
| P0 | Main `0x02074b44` initialization bridge and autoload_2 `0x020ed6c4` callback lack matched bodies. Host/guest gate choices are not fully bound to facade actions. | G0 bounded callback/state trace or owner-authorized address-level recovery; do not infer full menu semantics from a transport mode. [E: `scratchpad/wifi-analysis-1/stage1-evidence.json` core_coverage] |
| P0 | Exact callback memory lifetime, radio completion status and live MP configuration at town entry. | G0/G1 trace plus request/response structure audit; current request sender proves only one side. [S: `src/matched/WMi_SendCommand.c:83`, `src/matched/func_ov066_022686f0.c:20`] |
| P0 | Shared game bulk buffers versus underlying local fragmentation and acceptance/backpressure. | Follow sends through local driver with lengths/offsets/counts, then G2. No payload dump. [S: `src/matched/func_02075ff8.c:42`, `src/matched/func_020ec338.c:36`] |
| P1 | Town/player/roster mapping of every ID and per-frame position/action/RNG semantics. | Observe one scripted action per endpoint and compare ID/size/caller summaries; recover helper identities. Four-way barriers do not answer state-sync versus input-lockstep. [S: `src/matched/func_020753a8.c:10`, `src/matched/func_02074330.c:370`] |
| P1 | Chat, letters, inventory exchange and persistent disconnect/rollback; main `0x020a0848` is unmatched. | Trace one transaction and each interrupted boundary into save-flow functions, G3/G4. [S: `src/matched/func_020a03e0.c:113`] [E: `scratchpad/wifi-analysis-1/stage1-evidence.json` core_coverage] |
| P1 | Complete NAS/GPCM/GPSP/match/NatNeg/GT2 callback chain and exact ADMK endpoint resolution. | B0 operation trace, then private server synthetic test and B2/B3. No inference from another region's server list. [S: `src/matched/func_020ec980.c:41`, `src/matched/func_ov065_0227eda0.c:100`] |
| P2 | Current hosted ADMK support and DeSmuME backend viability. | Recheck upstream and perform one authorized pinned-build/private-identity experiment if selected; failed document fetches prove neither support nor failure. [E: `scratchpad/wifi-analysis-1/external-research.json` R9-R10] |
| P2 | melonDS bridge, Internet delay tolerance and relay epoch policy. | Pin one upstream protocol revision; translate one MP exchange, then a delay/loss matrix. [E: `scratchpad/wifi-analysis-1/external-research.json` R8] |
| P3 | More than four participants and custom persistent events. | Capacity/authority/save inventory after G4. No realistic unlimited-visitors completion claim. [S: `src/matched/func_020760bc.c:37`, `src/matched/func_020a03e0.c:63`] |

## Related

- [Network boundary](network.md).
- [Game and SDK protocol map](multiplayer-protocol.md).
- [Current runtime router](../../docs/kb/hybrid/wifi.md).
