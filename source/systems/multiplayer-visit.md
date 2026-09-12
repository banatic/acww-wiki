# Multiplayer visit: the town-arrival sequence, per-frame play and departure

**Summary.** After MP starts, a visit is driven by a **ten-step control exchange** between the
host (parent) and the arriving guest (child), built out of the 24 control ids the
[protocol map](multiplayer-protocol.md) enumerates. The host ships the participant bitmap, a
two-section record, a 1,696-byte shared-field block, the four-participant status table, the
compressed town and finally its own calendar clock; the guest answers at three fixed points
and then installs the town over its own live save bank. Play afterwards is not lockstep: each
participant sends **one aggregated frame per comms update**, carrying a tagged change stream
over a 0x46-entry field table plus a routed message queue. Departure is two four-participant
barriers and a commit. **No RNG state is sent at any point in the exchange.**
[S: `src/matched/func_020a3bc0.c:94`, `src/matched/func_020a3ea4.c:227`,
`src/matched/func_02074f28.c:14`]
[E: `scratchpad/g3prep89/citation-index.md`]

## Evidence and scope

This is static analysis of `src/matched/` at `a01361ab`; **no multiplayer session was run**,
on hardware, an emulator or the port -- until G3ARRIVAL104 (2026-09-12), whose bridged rig run
reached all twelve arrival steps on the port and is written up under "The origin, MEASURED"
below; the frames there are the port's, not hardware's. Every line number was resolved by
`scratchpad/g3prep89/cite.py` (166 queries, 0 unresolved), not typed by hand. Matched bodies
are byte-verified reconstructions whose NAMES are inferred, so each statement below is a
claim about behaviour, never about an original identifier. Sizes, offsets, ids and message
numbers only: no ROM code, strings, tables or payload bytes.

Two things this page does NOT establish and must not be read as establishing: the meaning of
the individual fields inside any transferred record, and that the port can execute any of it.
The bridge that would carry these messages does not exist yet -- see
[G2's rig](../../docs/kb/hybrid/wifi.md) and the gap section below.

## What happens

### The envelope, and the two channels above it

One byte precedes everything. Bits 0..1 are a status/acknowledgement value, bit 7 selects the
control channel, bits 2..6 are a 5-bit id.
[S: `src/matched/func_02077b3c.c:6`, `func_02077b14.c:6`, `func_02077b20.c:8`,
`func_02077b28.c:6`]

That gives **two channels on one transport**:

* **bit 7 set** -- a control message. Ids below 0x18 index a 24-entry dispatch table with the
  envelope stripped and the length reduced by one. [S: `src/matched/func_02075050.c:38`,
  `func_02075240.c:8`]
* **bit 7 clear** -- a per-frame data frame. It carries only the 2 status bits, runs the
  queue bookkeeping and re-registers a 0x1000-byte receive buffer; there is no handler.
  [S: `src/matched/func_02077b50.c:8`, `func_02075050.c:47`]

Id **24** exists as a sender but has no handler, because 24 is not less than 0x18: the
transport-state-1 arm emits a 1-byte id-24 frame purely to carry its status bits.
[S: `src/matched/func_02074330.c:325`]

Each participant owns a 0x1000-byte transmit slot; index 4 is a common slot. Four participant
indices are remapped onto three remote descriptor slots by deleting the sender's own index.
[S: `src/matched/func_02073d28.c:22`, `func_02077b58.c:11`, `func_020ec260.c:15`]

Anything larger than a slot is chunked by one rule: **ceil(len / 0xffb) chunks, each
`[envelope][u32 absolute offset][<= 0xffb data]` = at most 0x1000 bytes**, with a one-byte
counter that advances only when the queue accepted the chunk.
[S: `src/matched/func_02075ff8.c:38`, `:49`, `:45`, `:52`, `:54`]

### The arrival sequence, step by step

The host runs one instance of its arrival machine **per arriving participant**; the guest runs
its own. Every step's precondition is a specific session-object field that a specific handler
writes, so the sequence is a chain of one-way messages with explicit rendezvous, not a
request/response protocol.

| # | Sender | id | Payload and size | Written into / gate that opens next |
|---|---|---|---|---|
| 1 | guest | **7** | 1 byte | raises the host's join request; the host machine leaves state 0. [S: `src/matched/func_020a3ea4.c:125`, `func_0207553c.c:8`] |
| 2 | both | **5 / 6** | 2 bytes: the sender's visit-phase id | the phase barrier, below. Both sides must show the same phase id before the host leaves state 2. [S: `src/matched/func_0207417c.c:42`, `func_02074dfc.c:20`, `func_020a0340.c:23`] |
| 3 | host | **0** | 2 bytes: low nibble = the present-participant bitmap, bits 6..7 = two more | guest SESS+0xd4 (u16) and +0xd7; the guest leaves state 1. Destination is `1 << arriving`, i.e. the newcomer alone. [S: `src/matched/func_020a3bc0.c:94`, `func_020756cc.c:17`, `func_020a1284.c:9`] |
| 4 | host | **13** | variable; two sections, each `[u16 length][u8 section index]` followed by that section's bytes, built into the common slot by a pair of producer callbacks | handler 13 is a tail call whose callee is unnamed in the matched file. [S: `src/matched/func_02077690.c:32`, `:45`, `func_020a3bc0.c:104`, `:114`, `func_02075448.c:10`] |
| 5 | host | **12** | bulk **0x6a0** (1,696) -- the shared-field block the per-frame stream later sends deltas of | guest's copy of the same block. Chunk counter at host SESS+0xd8. [S: `src/matched/func_020a3bc0.c:125`, `func_02075450.c:14`] |
| 6 | host | **15** | 9 bytes: four 2-byte packed records, one per participant slot | the guest applies all four with mask 7 into the 3-byte-per-participant status table. This is the **participant-count agreement point**: the table has exactly four slots. [S: `src/matched/func_020a3bc0.c:135`, `func_020753a8.c:22`, `func_020a7394.c:18`] |
| 7 | host | **1** | bulk: the **compressed town**, total = its own compressed length + 4, defaulting to **0x17400** when that word is zero | guest's town staging buffer. Reaching the total starts the decompressor with a 0x1000 window. The host starts its compressor at step 6 and waits for it before step 7. [S: `src/matched/func_020a3bc0.c:137`, `:150`, `func_02075fc4.c:17`, `func_02075670.c:34`, `:41`, `func_020a003c.c:9`] |
| 8 | guest | **2** | bulk **0x950** (2,384) -- the guest's own participant record; a one-byte body is the reset form instead | host's per-participant record. Sent at guest state 2, i.e. in parallel with steps 4..7. [S: `src/matched/func_020a3ea4.c:146`, `func_0207560c.c:20`] |
| 8b | each resident visitor | **4** | bulk **0x249c** (9,372) -- that visitor's player slot | newcomer's player handle `sender+3`. A visitor already in the town runs a short machine that sends only this. [S: `src/matched/func_020a3abc.c:62`, `func_0207557c.c:16`] |
| 9 | guest | **9** | 1 byte | host SESS+0xd9; the host leaves state 9. Sent only after the guest's decompressor has finished AND every present peer's 0x249c slot has arrived. [S: `src/matched/func_020a3ea4.c:163`, `:193`, `func_020754e8.c:12`] |
| 10 | host | **10** | 9 bytes: envelope + **8 bytes of calendar/clock** | guest SESS+0xdc, completion flag SESS+0xda. This is what unblocks the guest's install. [S: `src/matched/func_020a3bc0.c:162`, `func_020754b0.c:24`, `func_0209e474.c:12`] |
| 11 | guest | **11** | 1 byte | host SESS+0xe4; the host enters transport state 2 -- MP play. [S: `src/matched/func_020a3ea4.c:255`, `func_02075484.c:21`, `func_020a3bc0.c:174`] |

**The install** is the single most consequential step and it is entirely local. On receiving
id 10 the guest moves its own 0x249c player record into handle `own index + 3`, rewrites the
per-participant presence table from the id-0 bitmap, **copies the received 0x173fc bank over
the live save bank**, adopts the 8 clock bytes id 10 delivered as the session's date and time,
re-initialises the town objects and only then reports ready.
[S: `src/matched/func_020a3ea4.c:209`, `:227`, `:230`]

So: the visitor plays inside the HOST's save image, in the HOST's calendar, with its own
player slot relocated into one of the three visitor handles. That is the fact the port's G3
gate has to see on both sides.

### The layer UNDER step 1: ov066's own session layer, and where the envelope sits

**Everything above rides on a transport ov066 owns, and it has a message table of its own.**
MP99 measured four WM port messages a side and could not find the visit envelope in them; the
reason is that the game's buffer does not begin at offset 0 of a WM port payload. ov066 puts
its own framing in front, and the offset is computable rather than searchable. This section is
the transport's own table, read out of `src/matched/`; it says nothing about the ten steps
except where to look for them.

**The registrar.** `func_ov066_0226b9b8` installs two WM port callbacks and an indication
callback, and fills an op table inside the WM communication context (`data_ov066_0226bdf4`,
the object CALLBACK91 and CALLBACK98 repaired call sites in):

| slot | function | role |
|---|---|---|
| +0x9c | (unnamed in the matched file) | the MP-start hook, run from statecode 10 |
| +0xa0 | `func_ov066_0226af3c` | the PARENT's port-13 pump, run from statecode 11 |
| +0xa4 | `func_ov066_0226af04` -> `func_ov066_0226b3d0` | the CHILD's pump, run from statecode 13 |
| +0xb0 | `func_ov066_0226b81c` | the game's port-send enqueue (4 arguments) |
| +0xb4 | `func_ov066_0226b8bc` | the send-ready predicate |
| +0xb8 | **the GAME's receive callback** | installed separately, see below |
| port 12 | `func_ov066_0226923c` | the session port |
| port 13 | `func_ov066_0226aab8` | the data port |

[S: `port/build/shadow/func_ov066_0226b9b8.c:78`-`:102`, `src/matched/func_ov066_022698ec.c:14`,
`func_ov066_02269934.c:18`]

**+0xb8 is the seam between ov066 and the game**, and it is installed from the other side:
`func_ov066_02267fe8` stores it under an interrupt-disable pair, its only caller is
autoload_2 `func_020ecce4`, and that one's only caller is main `func_02074b44` -- the
unmatched bridge wifi-analysis named. Its three arguments are (sender index, buffer, length),
which is `func_02075050`'s signature: **one control or data message per call**.
[S: `src/matched/func_ov066_02267fe8.c:13`, `func_02075050.c:27`]
[E: `tools/cgquery.py --callers 0x02267fe8`]

**Port 12 -- the session port.** Its callback branches on the reader's own participant index
(context +0x1e), so the two directions have different handlers:

| direction | frame | consumer | what it does |
|---|---|---|---|
| parent -> child | `[u16 kind][u16]` + body | `func_ov066_02268da4` | kind 0 -> `func_ov066_02268d44`; kinds 1 and 2 are accepted and ignored (an empty switch arm the ROM's bytes require) |
| child -> parent | `[u16 kind]` + body, kind must be **2** | `func_ov066_02268f1c` | hands (sender aid, buffer) to `func_ov066_02268ed4`; any other kind is dropped |

[S: `src/matched/func_ov066_0226923c.c:18`, `func_ov066_02268da4.c:29`, `func_ov066_02268f1c.c:19`,
`func_ov066_022699cc.c:10`]

**Port 13 -- the reliable data port.** Its callback takes only statecode 0x15 (PORT_RECV) and
splits on the sender's AID, which is `WMPortRecvCallback+0x12`:

| sender | consumer | what it does |
|---|---|---|
| aid != 0 (a child) | `func_ov066_0226ac68` | decode the 2-byte fragment header, apply the ack bit to the entry it names, store kind 0/1 bytes into that child's slot of a free-list node |
| aid == 0 (the parent) | `func_ov066_0226ab28` | a **4-bit sequence window** on the frame's first byte: accept when it is `(last + 1) & 0xf` (or the first-frame flag is set), request a retransmission when it is `(last + 2) & 0xf`, otherwise raise the resend flag; an accepted frame goes to `func_ov066_0226b1d0` |

[S: `src/matched/func_ov066_0226aab8.c:26`, `func_ov066_0226ab28.c:70`, `func_ov066_0226ac68.c:60`,
`src/matched/WmReceiveFifo.c:84`-`:100`]

**The two frame shapes, and the one offset that matters.**

```
parent -> children   [u8 seq][u8][u16 slot bitmap][slot 0][slot 1]...   each slot ctl->f0 bytes
child  -> parent     [slot]                                            no prefix
slot, kind 0         [b0][u8][u16 destination mask][u32 total] then the game's bytes
slot, kind 1         [b0][u8 length]                          then the game's bytes
slot, kind 2/3       an acknowledgement / a retransmission request -- no game bytes
b0                   kind:2 | done:1 | ack:1 | index:4
```

So the game's buffer -- and therefore the visit envelope -- begins at **prefix + 8** for a
first fragment and **prefix + 2** for a continuation, with the prefix 4 on a frame the parent
built and 0 on one a child built. [S: `src/matched/func_ov066_0226b088.c:66`,
`func_ov066_0226b1d0.c:24`, `func_ov066_0226b5c4.c:61`, `func_ov066_0226b3d0.c:104`,
`func_ov066_0226af3c.c:76`]

**THE PARENT RELAYS, which is a trap for any observer.** A child's frame is stored into that
child's slot of a free-list node (`func_ov066_0226ac68`) and the parent's next pumped frame
packs EVERY set slot and broadcasts it, delivering it to the parent's own game at the same
time (`func_ov066_0226b088` ends by calling `func_ov066_0226b1d0` on what it just built). So a
child sees its own message come back, in a frame the PARENT built, and an observer that only
matches on the message id will count one message as two. The slot bitmap is the discriminator:
a block whose slot index is the reader's own AID is an echo.
[S: `src/matched/func_ov066_0226ac68.c:72`, `func_ov066_0226b088.c:99`, `:107`]

**Reassembly and delivery.** `func_ov066_0226b1d0` walks the slot bitmap and calls
`func_ov066_0226b27c(i, slot)` per set slot; that one accumulates fragments against the
declared total and, only when the total is reached, calls the game's +0xb8 callback with
(index, buffer, total). A transfer that never completes therefore delivers nothing at all,
silently. [S: `src/matched/func_ov066_0226b1d0.c:24`; the reassembler itself has no matched
file -- `port/shim/gen/func_ov066_0226b27c.c` is the port's near-miss reconstruction]

**The visit phase is a table index, not an opaque id.** `func_020a6f74(i, phase)` writes
participant `i`'s phase to session `+0x84 + 4*i`, control id 5's handler `func_0207556c` is
exactly that write for the sender, and the phase numbers index an 8-byte-stride table of visit
sub-machines: **13 is the host arrival machine `func_020a3bc0`, 30 the guest's
`func_020a3ea4`**, 10 the resident-visitor machine and 20 the departure machine. That is why
the phase barrier's arrival pair is (0xd, 0x2f): it is naming machines.
[S: `src/matched/func_020a6f74.c:6`, `func_020a617c.c:5`, `func_0207556c.c:7`]
[E: the table at main `0x020e3810`, indices 10/13/20/30 resolving to `0x020a3abc`,
`0x020a3bc0`, `0x020a3084`, `0x020a3ea4`]

**The one lower-layer answer the whole layer above depends on.** Every arrival state and the
per-frame comms update call the loss predicate `func_02073fdc` FIRST, and in local mode its
entire answer is whether the destination mask is contained in `func_020ec1f8()`. That is
`func_ov066_0226997c`, and it **returns 0 unless ov066's communication state is exactly 10**,
otherwise returning `WMStatus + 0x17e` (the connected-child bitmap). The state becomes 10 on
the parent only inside statecode 10's arm of `func_ov066_02268570`, i.e. on the WM_StartMP
callback that reports MP started. So a transport that never reports statecode 10, or reports
it with the child bitmap still zero, makes every state of every visit machine take its
link-lost branch -- and the symptom is a gate that waits rather than an error.
[S: `src/matched/func_02073fdc.c:19`, `func_020ec1f8.c:9`, `func_ov066_0226997c.c:29`,
`func_ov066_02268570.c:53`-`:69`, `func_ov066_0226760c.c:17`]

### What has to happen BEFORE step 1: the gatehouse's own two-value handshake

The ten steps begin when the guest sends id 7, and the guest sends id 7 from state 0 of its
arrival machine -- so the real first question is what starts that machine. It is not a step in
this table at all; it is the gatehouse overlay's own step machine, and it waits on ONE number.

**The gatehouse's step** is an `int` at its object +0xb4, set by `func_ov048_022616b8` and
dispatched through two vtable slots that pick a `{PMF, PMF, flag}` entry out of a 23-entry
table. Two of those steps are where a visit parks: step 7 (`func_ov048_02260b64`, reached
after `func_0207417c(0)`) and step 9 (`func_ov048_02260ae8`, reached after
`func_0207417c(1)`). [S: `src/matched/func_ov048_022616b8.c:12`, `func_ov048_02261704.cpp:27`,
`func_ov048_022616c0.cpp:22`, `func_ov048_02260c88.c:32`, `func_ov048_02260b4c.c:10`]

**Both wait on the same predicate and nothing else: `func_02074150()` must return 5 or 6.**
Step 9 is literally `if ((unsigned)(ret - 5) > 1) return;`, and step 7 treats 5 as accepted, 6
as refused, and anything else as "come back next frame" unless the link layer is reporting one
specific error code. There is no timer and no local fallback.
[S: `src/matched/func_ov048_02260ae8.c:22`, `func_ov048_02260b64.c:61`, `:90`]

**`func_02074150()` is a getter, and WHICH slot it reads is the whole subtlety.** It is
`phase[own]` when the caller's own presence byte is set and **`phase[3]`** when it is not --
where `phase` is the session object's `+0x84 + 4*i` array, not the 3-byte barrier table.
[S: `src/matched/func_02074150.c:17`, `func_020a6f64.c:8`, `func_020a6170.c:5`,
`func_02073dd4.c:6`]

**Only a peer can put 5 or 6 there.** Every writer of that array is local and small except
three, and all three carry a byte that came off the wire:

| writer | slot | value |
|---|---|---|
| `func_0207417c` (the publisher itself) | `phase[3]`, or `phase[own]` when own index is 0 | 4, or its own argument (0, 1, 3 at the call sites) |
| `func_02075548` -- **control id 6's handler** | `phase[3]` | the sender's low 3 bits |
| `func_0207556c` -- **control id 5's handler** | `phase[sender]` | the message's body byte |
| `func_02076518` / `func_02076540` -- **routed-queue kinds** | `phase[own]` / `phase[i]` | one received byte |

[S: `src/matched/func_0207417c.c:39`, `:48`, `:50`, `func_02075548.c:11`, `func_0207556c.c:8`,
`func_02076518.c:11`, `func_02076540.c:17`]

And control id 6 is only ever BUILT when the sender's own recorded phase for that destination
is already 5 or 6: `func_02074dfc` is guarded by `func_02074e48`, which is exactly
`(phase[dest] - 5) <= 1`, and the body it sends is that phase in its low 3 bits plus the
present-participant mask in its high nibble. So id 6 PROPAGATES an acceptance; it cannot
originate one. [S: `src/matched/func_02074dfc.c:11`, `func_02074e48.c:8`, `func_020740b4.c:15`]

**Which makes the presence byte load-bearing.** `func_020742b4` is the one function that makes
a side a participant of its own session -- transport state 2, own index 0, `presence[0] = 1`,
and the barrier table's slot 0 seeded from the current scene byte -- and its only caller is the
gatehouse, `func_ov048_02263300`. With that byte clear, `func_0207417c` takes its
"I am not in a session" arm, which publishes an id 5 whose body is **0** and sets `phase[3] = 4`
locally, and the gate then waits on `phase[3]` for a 5 that only id 6 could deliver and that
id 6 will not build. [S: `src/matched/func_020742b4.c:24`-`:31`, `func_0207417c.c:36`-`:45`]

**And even after the gate passes, the arrival machine is one more hop away.** Steps 7 and 9 do
not call it: they write the "kind" word at session +0xa4 (0 on step 7's accepted arm, 1 on step
9's) and hand off. `func_020a5750` starts the machine when the per-participant connection-state
entry at session `+0xa8 + 4*i` reaches **5**, choosing by own index and that kind word; the
mode it requests is committed by an arbiter that admits mode 0x14 (the guest machine
`func_020a3ea4`) only while the scene byte is 12 and mode 0x15 (the host machine
`func_020a3bc0`) only while it is 13 or 47.
[S: `src/matched/func_ov048_02260b64.c:77`, `func_ov048_02260ae8.c:31`, `func_020a5750.c:196`,
`func_020a5bb8.c:5`, `func_020a4dc4.c:39`, `func_020a18e8`/`func_020a18f4` at their call sites]

### The gate-handshake state table, and the origin of the acceptance value (G3ARRIVAL103)

The `+0x84 + 4*i` array (base `0x021f4320`) is a SMALL-valued gate-handshake state, distinct
from the 3-byte-per-participant phase barrier: its writer `func_020a6f74` and its reader
`func_020a6170` only ever move values in `{0, 1, 3, 4, 5, 6, 7}`. **4** = published/waiting,
**5** = accepted, **6** = refused, **7** = done, **0/1/3** = the host's published intent.
`func_02074150` reads this array, at `[own]` when the reader's presence byte is set and `[3]`
otherwise; the gatehouse parks until it reads a 5 or a 6.
[S: `src/matched/func_020a6f74.c`, `func_020a6170.c`, `func_02074150.c`]

**Who satisfies the gate, per side and per step** (measured from `src/matched/`):

| side | gate step | predicate | reads | who can satisfy it |
|---|---|---|---|---|
| host | 7 (`func_ov048_02260b64`) | `func_02074150() == 5` | `phase[0]` (own index 0, present) | a wire byte lands 5 in `phase[0]` |
| host | 9 (`func_ov048_02260ae8`) | `(func_02074150()-5) <= 1` | `phase[0]` | id-5/id-6/routed byte = 5 or 6 |
| guest | 7 / 9 | same | **`phase[3]`** (own index = sentinel 4, presence never set) | ONLY id-6's handler `func_02075548` writes `phase[3]`, from a wire byte |

**No local write of the array is ever a literal 5 or 6.** Every caller of `func_020a6f74`
writes a constant or a wire byte: `func_02074120` writes 7; `func_0207417c` writes 4 or its
argument (0/1/3 at the call sites); `func_0207556c` (id 5) writes the received body byte;
`func_02075548` (id 6) writes `body & 7`; `func_02076518`/`func_02076540` (routed-queue kinds)
write a received byte. **So the 5 must arrive over the wire, and the message that carries it
cannot originate it** (`func_02074dfc` builds id 6 only when the sender's own `phase[dest]` is
already 5/6 -- `func_02074e48` -- so it propagates an acceptance).
[S: `src/matched/func_02074120.c`, `func_0207417c.c:39`, `func_0207556c.c`, `func_02075548.c`,
`func_02076518.c`, `func_02076540.c`, `func_02074dfc.c`, `func_02074e48.c`]

**The guest's own message cannot be the 5, because it is a body-0 id 5.** As a non-participant
(own index 4, so `func_02073dd4(self, 4) == 0`), `func_0207417c` takes its first arm: it writes
`phase[3] = 4` locally and sends an id 5 whose body byte is **0** (`func_02077b3c(p, 0, 5)`, then
`p[1] = 0`). The host's id-5 handler therefore writes `phase[guest] = 0`, never reaches 5, and
never builds the id 6 that would set the guest's `phase[3] = 5`. **A participant guest (index
!= 0) would instead send `body = param`** (its `func_0207417c` participant arm), so promotion is
the hinge. [S: `src/matched/func_0207417c.c:23`-`:34`, `func_02073dd4.c`, `func_0207556c.c`]

**So the acceptance value has exactly two possible origins, and both are on the HOST:**
1. **The routed-queue handlers** `func_02076518`/`func_02076540`, which write `phase[own]` /
   `phase[i]` from a byte carried in the per-frame stream's routing kinds (kinds 4-7). This is
   the only path that can put a 5 into the array without an already-5 phase to propagate.
2. **Participant promotion of the guest**, after which its own `func_0207417c` publishes a
   non-zero body. The guest becomes a participant only through `func_020742b4` (the sole writer
   of its presence byte and own index), whose one caller is the HOST gate path
   `func_ov048_02263300` -- invoked under comms **mode 4** (its case 1) or **mode != 3** (case
   2). The measured local-wireless run is mode 1 (host) / 2 (guest), and the guest's own index
   stays 4 for all 24,000 frames.
[S: `src/matched/func_02076518.c`, `func_02076540.c`, `func_020742b4.c:24`,
`func_ov048_02263300.c` cases 1-2; measured `docs/log/cycle42-save.md` G3HANDSHAKE102]

The experiment that settles it: instrument `phase[]` writes on the host with the writer id, and
`func_020742b4`'s presence byte on the guest, over one bridged visit -- the first non-4 write to
the guest's own index, or the first host `phase[guest]` = 5 and its writer, is the answer.

### The origin, MEASURED, and three corrections to the table above (G3ARRIVAL104)

That experiment was run (`docs/log/cycle42-save.md` G3ARRIVAL104: the interpreter's store
watchpoint over `0x021f4320 + 0x84..0xc7`, every hit printed with the leaf's return address).
**The 5 is written LOCALLY on the host, by the connection arbiter `func_020a5c38`**, and the
section above was wrong in three places:

1. **`func_020a6f74` is not the array's only writer.** `func_020a617c` (the raw store) has
   three direct callers besides it -- `func_020a5c38`, `func_020a6104` and the reset
   `func_020a6a74` -- and the first two write **5, 6 and 7 as literals**. The "exhaustive" sweep
   stopped one level short. [S: `src/matched/func_020a5c38.c` (`func_020a617c(self, me, 5)`
   in its state-1 arm, `... 6` in state 3), `func_020a6104.c`]
2. **`func_020742b4` is the HOST's self-registration, not guest promotion.** It sets own index
   0 and `presence[0]`; it is what the host's gate-open path runs. The guest's own index is
   written exactly once, at the INSTALL (`func_020a3ea4` case 6, `g->field_64 = func_020ec260()`,
   its WM AID), so the guest is a non-participant through the whole gate BY DESIGN, and reads
   `phase[3]` -- which is what control id 6 writes. [S: `src/matched/func_020742b4.c:24`,
   `func_020a3ea4.c` case 6, `func_02075548.c`]
3. **Comms mode 1/2 IS the DS local-wireless visit** (`func_02074b44` under mode 1 or 2 installs
   the receive callback through `func_020ecce4`; 3/4 take the DWC roster path with the 32 x 12
   friend table). There is no per-visitor host prompt: opening the gate is the consent, and the
   only host-side check is `func_020a5750`'s state-1 predicate (scene byte not in
   {0xc, 0xd, 0xe, 0x2e, 0x2f}, the player's visit phase 0x3f, `data_021f42f0 == 0`,
   `func_0203df10()`), which answers yes at once in the gatehouse.
   [S: `port/shim/gen/func_02074b44.c`, `src/matched/func_020a5750.c`]
   The mode byte's only writer, `func_020ecce4`, is reached from `func_02074b44`, whose callers
   are `func_ov048_02262618` (the gate's own menu row, `p2` = the mode, from `func_ov048_02263300`
   case 2) and `func_020a2d48` (mode 1): the row the rig's pad script picks IS the DS-to-DS row.
   [E: `tools/cgquery.py --callers 0x02074b44`]

And a naming note for the table above: the `+0x84 + 4*i` words are the GATE-HANDSHAKE state
(`func_020a617c`/`func_020a6170`); the per-player CONNECTION state that `func_020a5750` drives is
the separate `+0xa8 + 4*i` array (`func_020a5bb8`/`func_020a5bc4`), and the visit-phase barrier is
the 3-byte-per-index table at the session base (`func_020a7330`). Three arrays, three readers.

**The chain, with the measured frames** (host time / guest time; the guest launches 600 frames
after the host):

| frame | side | what | writer (lr) |
|---|---|---|---|
| 14,615 g | guest | `phase[3] = 4` and the body-0 id 5 goes out (non-participant arm) | `func_0207417c` (0x0207419d) |
| 15,246 h | host | id 5 lands: `phase[1] = 0` -- a published intent of kind 0 | control dispatch (0x0207524b) |
| 15,248 h | host | arbiter arms: state 0, subject 1, kind 0, `phase[1] = 4`, `conn[0] = 0`; `func_020a5750` answers 0 -> 1 -> 2 the same frame, countdown 0x28 | `func_020a5c38`, `func_020a5750` |
| 15,251 h | host | arbiter state 1: `conn[0] = 5`, **`phase[1] = 5`**, last = 1, state 2 | `func_020a5c38` (**0x020a5f0f**) |
| 15,252 h | host | the per-frame update builds id 6 for the NON-PRESENT index 1 (`func_02074330`'s non-present arm, own == 0) and writes `phase[1] = 7` after the send -- natively, so no STORE line | `func_02074dfc` / `func_02074330` |
| 14,627 g | guest | id 6 lands: **`phase[3] = 5`**, then `+0x98 = 1` | `func_02075548` (0x02075559) |
| 14,630 g | guest | the guest's step-7 accepted arm ships its own 0x249c record as **id 4** (4096 + 4096 + 1195) to the host | `func_ov048_02260b64` -> `func_02075dcc` |
| 15,023 g | guest | kind = 0, `phase[3] = 7` | `func_ov048_02260b64` (0x02260c0d), `func_02074120` |
| 15,306 g | guest | scene byte 12 (the guest arrival machine admitted) | -- |
| 15,710 h | host | handle 4 valid, countdown expired: `kindcopy = 0`, `conn[0] = 6`; arbiter idle (4) at 15,713 | `func_020a5750` |
| 15,936 h | host | id 7 lands (`join = 1`); scene byte 13 at 15,937 (the host arrival machine) | control dispatch |
| 15,942 h | host | transport state 1; `presence` = 3 at 15,945 (the guest is now a participant on the host) | `func_020a3bc0` states 1-2 |
| 16,167 g | guest | **own index 4 -> 1** (the install), transport state 2 at 16,173, scene 0 at 16,206 | `func_020a3ea4` case 6 |
| 16,653 h | host | transport state 2 -- MP play; scene back to 11 at 16,725 | `func_020a3bc0` |

So the acceptance's origin is (a) of the two candidates above -- the routed/arbiter path -- but
not through the routed-queue kinds: for a kind-0 subject the arbiter writes `phase[subject]`
itself and the per-frame update's non-present arm is the propagation. Candidate (b) never
existed. **What kept the port at 1 of 12 was not the game:** the host's id 6 went out as a
zero-length fragment to mask 0 (G3HANDSHAKE102's frame 15,259, `fdest=0 ftotal=0`), because the
per-frame update runs on the NATIVE chain under the registered `func_0206e63c` and the native
`func_020ed874` wrote the send queue into an invented absolute while `func_020ed9f4` drained the
real array -- `port/shim/game/g3cb_func_020ed874.c`. With that one body repaired the rig reads
**12 of 12** on its first run.

### What the other two slots carry with only two players

Nothing. Every loop that walks participants is `for (i = 3; i >= 0; i--)` with two guards --
"does participant i exist" and "is participant i me" -- and a slot that fails the first guard
is skipped entirely: no descriptor is built, no barrier vote is awaited, no phase is read.
The four-participant shape is in the ARRAYS, not in the traffic.
[S: `src/matched/func_02074330.c:187`, `func_020a05e8.c:118`, `func_02077a8c.c:18`]

Two places make that visible as a size rather than a loop. Id 15 always carries **four**
2-byte records regardless of how many players are present -- absent slots simply hold whatever
the table holds, and the receiver applies all four. And the phase accessor returns the
sentinel **0x3f** for any index >= 4. [S: `src/matched/func_020759e0.c:44`,
`func_020753a8.c:22`, `func_020a7330.c:13`]

### The two barrier kinds

**The phase barrier.** Every participant publishes a small visit-phase id (ids 5 and 6), and
peers read it out of a 3-byte-per-participant table together with a busy byte. A machine
passes the barrier when EVERY present, non-self participant's phase equals one of two
permitted ids and its busy byte is zero. The arrival machines use the pair (0xd, 0x2f); the
departure machines use (0x2e, 0x2e). **This is exactly the G3 criterion "both endpoints reach
the same identified visit phase", and it is a readable u8 per participant.**
[S: `src/matched/func_020a0340.c:23`, `func_020a7330.c:13`, `func_020a72d0.c:13`]

**The vote barrier.** Id 14 carries a 2-byte vote. Its handler writes the byte into
SESS+0xef+slot -- indexed by the SENDER on the participant whose own index is 0, and always
into slot 0 on everyone else, which is the host/guest slot remapping. A waiter walks 3..0 over
present non-self participants: **0 = has not voted, 1 = agrees, 2 = abort**; the array is
cleared between barriers. An abort jumps the state machine six states forward, into the
teardown range. [S: `src/matched/func_02075404.c:15`, `func_020a05e8.c:118`, `:145`,
`func_020a1224.c:8`, `func_020a03e0.c:92`]

The vote barrier is what brackets the **save staging**: the 8-state helper copies 0x173fc out
of the live bank into a session-owned buffer, loads the other town, barriers, and on the way
back copies those 0x173fc bytes in again when its caller's restore flag is set. That restore,
not anything in the unmatched teardown helper, is the rollback.
[S: `src/matched/func_020a03e0.c:63`, `:113`]

### Per-frame play

There is **no input lockstep and no shared RNG**. Each participant, once in transport state 2,
builds ONE aggregated frame per comms update and sends it to up to three destinations in a
single send:

```
[u8 status]                                   bits 0..1 only, bit 7 clear
[u8 tag][len(tag) bytes] ... [0x46]           the common block: a change stream
[5-byte header][payload] ...                  the routed queue
```

The common block walks tags 0x45 down to 0, emits a tag only when its dirty flag (at
block + tag + 124) is set, takes each tag's fixed length from a 0x46-entry table, and
terminates with the byte 0x46. It is computed ONCE, for the first destination, and memcpy'd
to the other two -- so the same change set reaches every peer in the same update.
[S: `src/matched/func_02074f28.c:14`, `:32`, `func_020738b4.c:8`, `func_0207762c.c:9`,
`src/matched/func_02074330.c:177`, `:181`, `:213`]

The routed queue appends variable-length records with a 5-byte header (a u16 length, a
selector byte, a kind byte and a packed byte). Eight routing kinds decide, per destination,
whether the record is copied into that destination's frame, re-queued locally, or dropped --
kind 4 is "not the local limit index", kind 5 is "not index 0", kinds 6 and 7 route against
the participant status table. [S: `src/matched/func_02074e64.c:37`, `func_020a70ec.c:50`]

**Authority.** Every participant is the author of its own tagged change stream, so the model
is per-owner state replication, not host authority. The host is authoritative only over
*admission*: the town image, the calendar, the participant bitmap and the arrival ordering all
come from it. The participant status table (three bytes each: phase, a middle field, a busy
byte) is broadcast by id 15 and written per-field with a mask, so an owner can update one
field without clobbering a peer's.
[S: `src/matched/func_020a7394.c:18`, `func_020a3bc0.c:94`, `:162`]

**Rate.** The senders do not pace themselves; the comms update does, and this analysis has NOT
bound that update to a frame. What it can say is that the same update also writes each slot's
status byte before filling it, and that with the send pump closed the identical loop degrades
to ack-only 1-byte frames rather than skipping the tick. [S: `src/matched/func_02074fa0.c:18`,
`func_02074330.c:265`]

**Divergence.** There is no resync message. What exists is a retry deadline and a connectivity
test, described under interruption below; a failure is a session abort, not a state repair.
The status bits are the only feedback channel: they accumulate per remapped sender slot on
receipt. [S: `src/matched/func_02073cf0.c:16`]

### Items, letters, chat

Four record sizes move through the control channel, and this unit proves **sizes, strides and
handles -- not contents**:

| Size | ids | Handle space |
|---|---|---|
| 0x950 (2,384) | 2, 3 | four per-participant records; handle 4 is a distinct slot |
| 0x249c (9,372) | 4, 21 | seven player handles: 0..3 are the save's own player slots, 4..6 the three visitor slots |
| 0x3200 (12,800) | 22 | a four-slot array |
| 0x6a0 (1,696) | 12 | the shared-field block the per-frame stream sends deltas of |
| compressed town | 1 | staged against the 0x173fc save bank |

Ids 16..20 and 23 are single-byte notifications gated on visit phase 46, each setting one
session byte (SESS+0xf8+sender, +0xfc+sender, +0xe5, +0xf4+sender, +0x100, +0x101). Naming any
of them "chat" or "item" would be an invention; the phase gate and the field each writes are
what is established. [S: `src/matched/func_02075380.c:17`, `func_02075358.c:19`,
`func_02075334.c:20`, `func_0207530c.c:11`, `func_02075300.c:8`, `func_02075254.c:12`]

### Departure

The departure machine barriers on visit phase 0x2e, then runs two one-byte rendezvous:

1. wait until **every** present peer has set SESS+0xfc (their id 17), then send **id 18** to
   the whole connected mask; [S: `src/matched/func_020a3084.c:171`, `:187`]
2. wait until every present peer has set SESS+0xf4 (their id 19), then **commit**.
   [S: `src/matched/func_020a3084.c:202`, `:210`]

The commit rebinds the three visitor player handles, reloads the town objects from the live
bank and writes a packed calendar word back into the local player record -- the departing
guest's own record, carrying the date the visit ended. The exit posts a scene message (10 on
one path, 0x0b on another) and the machine's own default arm posts a further one.
[S: `src/matched/func_020a1038.c:91`, `:99`, `:121`, `func_020a261c.c:17`,
`func_020a25e8.c:18`]

On the returning guest, the write that matters is the one already described in reverse: the
staging helper copies the guest's own 0x173fc bank back over the live bank **only when its
caller passes the restore flag**. Different callers pass different flags, so "does the visitor
keep what it did in the other town" is decided by the CALLER, not by the transfer.
[S: `src/matched/func_020a03e0.c:113`]

### Interruption

One predicate decides it, and every arm of every state machine calls it first:

1. if a retry deadline is armed and its counter has reached the limit -> **timed out**;
2. otherwise, if the required destination mask is not contained in the connected mask ->
   **link lost**.

[S: `src/matched/func_02073fdc.c:32`, `:45`]

The deadline is armed by the sender itself: a send that carried data on any of its three
triples sets it to **0x258 ticks**, and an empty send clears it. (0x258 = 600, and 600 frames
is exactly the interval G0 measured between the visiting route's first WM request and its
cleanup -- consistent, though G0's run never reached this layer.)
[S: `src/matched/func_02073e30.c:58`, `:63`] [E: `wiki/systems/wifi-g0.md`]

A failure raises **status bit 0x40** on the comms object and returns; the comms update
separately raises bit 4 when the expected participant bitmap is not inside the connected
bitmap in local mode, and bit 8 for the online equivalent.
[S: `src/matched/func_02074078.c:20`, `func_02074330.c:377`, `:384`]

### The rollback helper, and what it is not

`main:0x020a0848` is **unmatched** -- `size=0x2b0`, no body in this checkout. Seven callers
give it an 11-state span each, always `(base, base + 6)`: the state machines hand it
0xb..0x15, 0xe..0x18, 0xf..0x19, 0x10..0x1a and 0x11..0x1b, and the staging helpers jump into
it at `base` on a normal end and at `base + 6` on an abort vote.
[S: `config/adm-kr/arm9/symbols.txt:9665`, `src/matched/func_020a2dec.c:201`,
`func_020a3084.c:226`, `func_020a33e0.c:129`, `func_020a03e0.c:92`]

Its callee set is readable from relocation METADATA without reading any ROM code, and it is
worth stating because it **refutes the obvious guess**. It calls: the loss predicate and its
flag-raiser at every arm; the own-index query; the transport-ready pair; **id 14 at three
sites and id 19 at two**; the critical-section enter/leave pair twice; a teardown pair four
times; the two scene-message posters; the scene-object accessor; and one autoload_2 SDK call.
[E: `config/adm-kr/arm9/relocs.txt:32971`-`:33018`]

**It never loads the save-staging address and never calls the bank copy.** So it is a
barrier-and-teardown sequence -- vote, announce, tear down, post a scene message -- and NOT
the thing that restores a town. The restore is the `MI_CpuCopy8` in the matched staging
helper. wifi-analysis's "the exact persistent outcome after a lost peer is therefore still
open" is narrowed by this: the outcome is decided by the restore flag the caller passed into
the staging helper, and the unmatched helper's job is to get every peer to agree that the
session is over before that flag is acted on.

## Where it lives

| Layer | First source |
|---|---|
| Envelope encode/decode | `src/matched/func_02077b3c.c:6`, `func_02077b14.c:6` |
| Control dispatch | `src/matched/func_02075050.c:38` -> `func_02075240.c:8` |
| Bulk chunker | `src/matched/func_02075ff8.c:38` |
| Host arrival machine | `src/matched/func_020a3bc0.c:94` |
| Guest arrival machine | `src/matched/func_020a3ea4.c:125` |
| Resident-visitor machine | `src/matched/func_020a3abc.c:62` |
| Vote barrier (8-state / 7-state) | `src/matched/func_020a03e0.c:63`, `func_020a05e8.c:118` |
| Phase barrier | `src/matched/func_020a0340.c:23` |
| Per-frame aggregation | `src/matched/func_02074330.c:177`, `func_02074f28.c:14`, `func_02074e64.c:37` |
| Departure machine | `src/matched/func_020a3084.c:171` |
| Commit | `src/matched/func_020a1038.c:91` |
| Loss predicate | `src/matched/func_02073fdc.c:32` |
| Teardown (UNMATCHED) | `config/adm-kr/arm9/symbols.txt:9665` |

## Data it reads and writes

The session object's fields, each written by exactly one handler, are the state variables a
G3 observer should read. Offsets are from the session pointer; every setter is a one-line leaf
in `src/matched/`.

| Offset | Width | Written by | Read by |
|---|---|---|---|
| +0xc8 | ptr | -- | the town bulk buffer base |
| +0xcc | ptr | -- | the compressor/decompressor object |
| +0xd4 | u16 | id 0 | guest arrival state 1, departure presence loop |
| +0xd7 | u8 | id 0 | the guest's install |
| +0xd8 | u8 | local | bulk chunk counter, reused per transfer |
| +0xd9 | u8 | id 9 | host arrival state 9 |
| +0xda | u8 | id 10 | guest arrival state 6 |
| +0xdc | 8 | id 10 | the guest's clock adoption |
| +0xe4 | u8 | id 11 | host arrival state 10 |
| +0xe5 | u8 | id 18 | a departure arm |
| +0xe6 | u8 | (a sibling setter) | a departure arm |
| +0xef..+0xf2 | u8[4] | id 14 | the vote barrier; cleared between barriers |
| +0xf4..+0xf7 | u8[4] | id 19 | departure state 15 |
| +0xf8..+0xfb | u8[4] | id 16 | an arrival precondition |
| +0xfc..+0xff | u8[4] | id 17 | departure state 13 |
| +0x100 | u8 | id 20 | -- |
| +0x101 | u8 | id 23 | -- |

[S: `src/matched/func_020a132c.c:8`, `func_020a1284.c:9`, `func_020a127c.c:9`,
`func_020a125c.c:9`, `func_020a1254.c:9`, `func_020a1250.c:8`, `func_020a1274.c:9`,
`func_020a126c.c:9`, `func_020a1264.c:9`, `func_020a1238.c:8`, `func_020a1208.c:8`,
`func_020a1200.c:8`, `func_020a11f8.c:8`, `func_020a11e0.c:14`, `func_020a11b8.c:6`,
`func_020a1224.c:8`]

Outside the session object: the participant status table is 3 bytes per participant, the live
save bank is 0x173fc bytes, and the visit-phase id space is shared with the game's own scene
byte -- the handlers gate on phases 9, 12, 13, 46 and 47 using the same numbers the phase
barrier compares. [S: `src/matched/func_020a7330.c:13`, `func_020a03e0.c:63`,
`func_02075404.c:15`, `func_020752a8.c:31`]

## For the port

**Runs on the ARM9 unchanged, if the bridge delivers MP frames faithfully.** Everything on
this page. The control envelope, the 24 handlers, the bulk chunker, both arrival machines,
both barrier kinds, the per-frame aggregation, the departure commit and the loss predicate are
all ARM9 game code above the transport; none of them names a WM API. They need the transport
to deliver *a byte buffer of length N from participant i*, in order, with the sender's index
correct and the destination bitmap honoured -- and nothing else.

**Touches the ARM7/WM in ways the stub does not yet model.** Four things, in the order they
would bite:

1. **MP frame delivery itself.** The stub's StartMP terminates with code 10 and delivers no
   received data; there is no `WM_SetMPDataToPortEx` path and no receive callback carrying a
   payload. Every step on this page needs one. [E: `wiki/systems/wifi-g1.md`]
2. **MP frame timing.** The comms update assumes a send completes or fails within a bounded
   number of ticks, because the 0x258-tick deadline is what turns a stalled peer into a
   session abort. A bridge whose completion latency is unbounded converts a slow network into
   a link-loss UI. [S: `src/matched/func_02073e30.c:58`, `func_02073fdc.c:32`]
3. **Beacon user-info updates during play.** The host re-advertises while the gate is open;
   the stub bounds SetGameInfo but does not re-emit an advertisement carrying changed
   user-info, so a second guest arriving mid-visit has nothing current to select.
4. **Data sharing / key sharing.** Neither service is in the stub's table. This page does NOT
   show the visit path using them -- the town traffic is ordinary port sends -- but the two
   WM services are the remaining unmapped lower-layer surface, and the protocol map's warning
   stands: port 13 alone does not establish it.

**What the relay frame contract must add for G3.** Kind 1 (MP data) has never carried a byte.
For these messages it needs, per frame: the sender's AID, the destination bitmap, the logical
port, the length, and a sequence or epoch number so a duplicate cannot be applied twice --
because the bulk receivers are **absolute-offset writes** and a replayed chunk is silently
idempotent while a reordered one is not detectable at all. Kind 3 (control) needs connect,
AID assignment, disconnect and parent-state transitions so that CHILD_CONNECTED can be
synthesised at all. Kind 2 needs a scan REPLY shape, not only the advertisement. The dated
note in [the relay section](../../docs/kb/hybrid/online-spec.md) spells this out.

## How to check it

Re-derive every citation: `python -B scratchpad/g3prep89/cite.py` -- 166 queries, 0
unresolved, one `file:line` per claim.

The runtime check is G3, and its shape follows from the barriers rather than from a
screenshot. **Per side, at the stop frame, assert:** (a) the visit-phase byte for EVERY
present participant is the same permitted id and its busy byte is 0 -- this is the game's own
barrier, read rather than inferred; (b) the id-0 participant bitmap agrees on both sides and
its population equals the number of live relay peers; (c) the guest's decompressor reported
complete and the guest's copy of the live save bank matches the host's by length and hash
(0x173fc bytes, hash only -- never the bytes); (d) both sides observed the same scripted
movement, as a change in the same tag of the 0x46-tag common stream on the host and the same
tag applied on the guest; (e) departure: the host saw its peer's id 17 then id 19, the guest
committed, and both sides' status byte has bit 0x40 CLEAR at the stop -- a visit that ended
through the loss predicate is not a passed G3.

Details of how to wire that into `port/tools/g2rig.py` are in the g3prep89 section of
[the runtime router](../../docs/kb/hybrid/wifi.md).

## Hypotheses

* The 0x46-tag common block is where actor position, facing, animation and held item live,
  because it is the only per-frame per-owner channel and because the arrival sequence ships a
  full 0x6a0 snapshot of it (id 12) before play starts. **Unproved**: the tag -> field map
  needs one scripted movement on each side and a tag census, which is a G3 receipt, not a
  source reading. [S: `src/matched/func_02074f28.c:14`, `func_020a3bc0.c:125`]
* Id 13's two sections are the player-facing records the visit needs immediately (the section
  index is the only discriminator). Settle by naming the two producer callbacks.
  [S: `src/matched/func_02077690.c:45`]
* Because no RNG state crosses the wire and the calendar DOES (id 10, once), any per-frame
  divergence between the two towns is a delivered-message difference, not a seed difference.
  That makes the common stream's tag counts a sufficient divergence detector.
  [S: `src/matched/func_02075b14.c:28`, `func_0209e474.c:12`]

## Related

- [Protocol map](multiplayer-protocol.md) -- the 24 ids, the WM contracts, the unmatched bridges.
- [G0 gatehouse evidence](wifi-g0.md), [G1 WM request lifetime](wifi-g1.md).
- [G0-G5 plan](wifi-port-plan.md).
- [Relay contract](../../docs/kb/hybrid/online-spec.md), [runtime router](../../docs/kb/hybrid/wifi.md).
- [Save layout](save-data.md), [player slots](player.md), [town](town.md), [villagers](villagers.md).

### Gatekeeper dialogue seam (gatetext-1, 2026-09-12)

The gatehouse overlay does not draw its own words. Its top-menu request chooses message id
`0x0f`, or `0x10` when the gate is already open, then posts that byte with the key referenced
by `data_ov048_02263d20`; the relocation resolves the key storage to `0x02264148`. The resolved
key is `sp_npc_gatekeeper`, which selects the gatekeeper BMG archive. No dialogue text from
that archive is reproduced here. [S: `src/matched/func_ov048_022623f0.c:15-19`;
`config/adm-kr/arm9/overlays/ov048/relocs.txt:1016`]

The request boundary is `func_0206844c`: it stores the message id at window `+0x1e77` and the
key beside it. `func_02067218` copies the id into the request object at `+0x1e`, then
`func_0206726c` opens the archive, selects that record and copies its 12-byte `INF1` metadata.
Changing the id or archive here is possible, but it would require a replacement record whose
metadata and controls agree. [S: `src/matched/func_0206844c.c:8-14`;
`src/matched/func_02067218.c:26-35`; `src/matched/func_0206726c.c:13-24`]

The narrower seam is the decoded pointer. `func_0206741c` obtains it from BMG-reader virtual
slot 2 and immediately installs it in the existing typewriter through `func_020a94c8`.
`ACWW_GATETEXT=1` replaces only that pointer for the exact key/id pair, so the window, `INF1`
attributes, input handling and action callbacks remain game code. [S:
`src/matched/func_0206741c.cpp:71-74`; `src/matched/func_020a94c8.c:13-17`; H:
`port/shim/game/gatetext.c`, gated implementation]

The string format is UTF-16LE: the walker forms each unit from `p[0]` as the low byte and
`p[1]` as the high byte. Unit `0x001a` enters the escape walker, which advances by the chunk's
byte length. Glyph lookup remains the game's code-to-index scan. [S:
`src/matched/func_020a9368.cpp:20-39`; `src/matched/func_020a93f4.cpp:21-27`;
`src/matched/func_020516b8.c:25-56`]

**Corrected 2026-09-12 (GATESTILL105).** This paragraph used to say that the hook's chunk
reaches the choice-position builder at command `0xff`, value 2. It does not, and the numbers
are readable: the escape dispatcher takes the COMMAND from `chunk[3]` and the VALUE from the
little-endian halfword at `chunk+4`, with the payload at `chunk+6` and length `chunk[2]-6`.
The record's choice chunk for this key carries command **2** with value **7**, which is the
arm that hands the value to the group counter as a MODE -- whose table turns 7 into five
following strings and 6 into four. Command `0xff` value 2 is a separate control and this
record does not contain it. Id `0x10`'s own chunk is ten bytes with value 6, i.e. four rows,
because its gate is already open. [S: `src/matched/func_020a8764.c:9-20`;
`src/matched/func_020a87a8.c:3-8`; `src/matched/func_020a9ae0.c`;
`src/matched/func_020a9080.c:43-56`; `src/matched/func_020a83ec.c:20-25`;
`src/matched/func_020a8328.c:7-18`]

**And the group is preceded by one `0x000a`.** The record's own order for id `0x0f` is the
chunk, an empty run, one `0x000a`, then five `0x000a`-separated rows. That unit is not
cosmetic: the group counter measures from `payload + (length-6) + 2`, i.e. two bytes past the
chunk, while the escape walker has already left the cursor AT the chunk's end, and the
`0x000a` is the unit those two readings differ by. The measurement is
`scratchpad/gatestill105/escape105.py` over `script/KOR/message/sp/npc/gatekeeper_.bmg`; no
record text is reproduced. [S: `src/matched/func_020a83ec.c:37-47`;
`src/matched/func_020a93e8.c`; H: `port/shim/game/gatetext.c`, the array's comment]

**The five rows' actions, measured (GATESTILL105).** Driving the gatekeeper's own menu offline
and pressing Down N times then A, the five rows produce five DISTINCT screens at every sampled
frame: row 0 the wireless VISIT path, row 1 the wireless INVITE path, row 2 the friend-code
answer, row 3 the gate explanation, row 4 the dismissal. Row 4 is also the only row with a
large private `ov048` footprint (29 addresses no other row reaches -- the window teardown).
So the action belongs to the row INDEX and not to the row's text, which is what lets a
replacement that keeps the chunk byte-identical keep the callback map. [S: measurement,
`docs/kb/hybrid/wifi.md` `### gatestill105`]
