# Multiplayer callbacks: the five wireless structures and who they call

**Summary.** The game's wireless code keeps its state in **four globals packed into sixteen
bytes** at `0x0226bdec`, `0x0226bdf0`, `0x0226bdf4` and `0x0226bdf8` — a session struct, a
scan/beacon struct, the **communication context**, and a random seed — plus a four-entry table
of WM entry points just below them. The communication context ends in a **callback block of
eight consecutive function-pointer words**, `+0x9c` through `+0xbc`, and **one function installs
all eight from a single literal pool**. Twelve places read one of those eight and branch to it.
Two further structures the game allocates itself, the **beacon/AP table manager** and the
**per-request block**, carry one callback each. Together those five structures are how ov066
turns a radio into a town visit, and the callback block is the part a porter meets first,
because a word in it is an ov066 code address that only makes sense to the DS.

## What happens

`data_ov066_0226bdf4` is a POINTER, not a struct: the word at `0x0226bdf4` holds the address of
the communication context, which the module allocates
[S: `func_ov066_0226b9b8`, ov066, `src/matched/func_ov066_0226b9b8.c` is unwritten; read from
the ROM's own bytes at `0x0226b9e4`-`0x0226ba50`]
[E: `scratchpad/struct100/item2-census.txt`]. The three globals beside it are the same shape:
`0x0226bdec` is the session struct, `0x0226bdf0` the scan/beacon struct, and `0x0226bdf8` a
32-bit seed advanced by `seed * 0x5eedf715 + 0x1b0cb173` before every frame the module sends
[S: `src/matched/func_ov066_0226943c.c:88`, `src/matched/func_ov066_02269528.c:44`].

**One function installs the whole callback block.** `func_ov066_0226b9b8` loads the context
pointer once, then stores eight ov066 code addresses into `+0x9c`, `+0xa0`, `+0xa4`, `+0xac`,
`+0xb0`, `+0xb4`, `+0xa8` and `+0xbc` — in that order, interleaved two literals at a time
[S: ov066 `0x0226b9e4`..`0x0226ba4c`, disassembled with `tools/agent/target.py`]
[E: `scratchpad/struct100/item2-census.txt`]. It finishes by registering the game's own
handlers with the SDK: `WM_SetPortCallback(0xc, func_ov066_0226923c, 0)`,
`WM_SetPortCallback(0xd, func_ov066_0226aab8, 0)` and
`WM_SetIndCallback(func_ov066_0226b818)` [S: ov066 `0x0226bb0c`..`0x0226bb30`; the two SDK
entry points are `src/matched/WM_SetPortCallback.c` at `0x021210c0` and
`src/matched/WM_SetIndCallback.c` at `0x0212111c`]. So **ports 12 and 13 are the game's**, and
the indication handler is a single function.

`+0xb8` is the one slot `func_ov066_0226b9b8` does NOT fill: it is a public setter's field, and
two functions write a caller-supplied word into it — `func_ov066_02267fe8`, which does nothing
else but disable interrupts, store, and restore, and `func_ov066_02269c28`
[S: `src/matched/func_ov066_02267fe8.c:15`; ov066 `0x02269d64`]. That is why `+0xb4` and `+0xb8`
are read by different functions with different arities and are not two spellings of one field:
`+0xb4` is fixed at install time and takes no arguments, `+0xb8` is set per transfer and takes
three [S: `src/matched/func_ov066_02269934.c`; ov066 `0x0226b3a0`-`0x0226b3bc`].

The **beacon/AP table** is separate and is the game's own allocation: a manager struct with a
tag, a live count, a capacity, an entry array, an `OSAlarm` array and one callback at `+0xc`.
Each entry holds a 6-byte MAC, a channel, a 6-slot signal-strength ring with its average, a
back pointer to the manager and a 0xc0-byte payload — the beacon body. Seeing a MAC again
refreshes the ring and re-arms the entry's alarm; a MAC that is new takes the first free slot
and is the ONLY path that calls the manager's callback. When an entry's alarm fires the peer has
gone quiet, and the same callback is called again from the handler
[S: `src/matched/func_ov066_0226a494.c:83-160`, `src/matched/func_ov066_0226a43c.c:22-31`].
The alarm's interval is the caller's milliseconds turned into ticks as `(interval * 33514) / 64`
and its tag is `manager tag + 0x80` [S: `src/matched/func_ov066_0226a494.c:104`].

## Where it lives

| function or symbol | module | role | grade/citation |
|---|---|---|---|
| `data_ov066_0226bdec` | ov066 | pointer to the session struct | [S: `src/matched/func_ov066_02268570.c:33`] |
| `data_ov066_0226bdf0` | ov066 | pointer to the scan/beacon struct | [S: `src/matched/func_ov066_0226783c.c:41`] |
| `data_ov066_0226bdf4` | ov066 | pointer to the communication context | [S: `src/matched/func_ov066_02269934.c:14`] |
| `data_ov066_0226bdf8` | ov066 | 32-bit LCG seed for the send header | [S: `src/matched/func_ov066_02269528.c:32`] |
| `data_ov066_0226bdc0` | ov066 | four WM entry points: `WM_Enable`, `WM_Disable`, `WM_PowerOn`, `WM_PowerOff` | [S: `config/adm-kr/arm9/overlays/ov066/relocs.txt`, four `kind:load module:autoload(2)` rows; `config/adm-kr/arm9/autoload_2/symbols.txt`] |
| `func_ov066_0226b9b8` | ov066 | installs the whole callback block and registers ports 12/13 | [S: ov066 `0x0226b9b8`, 0x1c4 bytes] |
| `func_ov066_02267fe8` | ov066 | the public setter for `+0xb8` | [S: `src/matched/func_ov066_02267fe8.c`] |
| `func_ov066_0226a494` | ov066 | beacon-table insert/refresh; arms one alarm per entry | [S: `src/matched/func_ov066_0226a494.c`] |
| `func_ov066_0226a43c` | ov066 | that alarm's handler: an entry timed out | [S: `src/matched/func_ov066_0226a43c.c`] |
| `WmReceiveFifo` | main | the ARM9 side of every WM reply; dispatches all four `WMArm9Buf` callback members | [S: `src/matched/WmReceiveFifo.c:161-235`] |

## Data it reads and writes

The communication context's callback block. "Word" is what `func_ov066_0226b9b8` installs;
`+0xb8` is the exception and is named by its setter instead.

| address or field | meaning | who writes | who reads |
|---|---|---|---|
| ctx `+0x9c` | state-change notification, `void (*)(void)` — the most-read slot | `func_ov066_0226b9b8` → `func_ov066_0226a960` | `func_ov066_02268570` (state code 0xa), `func_ov066_02268e14`, `func_ov066_02268f98`, `func_ov066_02269a14` (teardown) |
| ctx `+0xa0` | `void (*)(void)`, called on state code 0xb | `func_ov066_0226b9b8` → `func_ov066_0226af3c` | `func_ov066_02268570` |
| ctx `+0xa4` | `void (*)(void)`, called on state code 0xd | `func_ov066_0226b9b8` → `func_ov066_0226af04` | `func_ov066_02268570` |
| ctx `+0xa8` | installed and **never read anywhere in ov066** | `func_ov066_0226b9b8` → `func_ov066_0226b90c` | nothing (exhaustive sweep of all 171 ov066 functions) |
| ctx `+0xac` | the SEND hook, `void (*)(void *buf, u32 len, u32 mask, void *done)` | `func_ov066_0226b9b8` → `func_ov066_0226ae1c` | `func_ov066_0226943c` (the 0x68-byte state broadcast), `func_ov066_02269528` (the 8-byte beacon) |
| ctx `+0xb0` | port-send enqueue, four ints | `func_ov066_0226b9b8` → `func_ov066_0226b81c` | `func_ov066_022698ec` |
| ctx `+0xb4` | `int (*)(void)`, fixed at install time | `func_ov066_0226b9b8` → `func_ov066_0226b8bc` | `func_ov066_02269934` |
| ctx `+0xb8` | receive-complete, `void (*)(int idx, u32 base, u32 len)` — set per transfer | `func_ov066_02267fe8` (public setter), `func_ov066_02269c28` | `func_ov066_0226b27c` |
| ctx `+0xbc` | one-argument handler, `void (*)(void *)` | `func_ov066_0226b9b8` → `func_ov066_0226aeb8` | `func_ov066_02269204` |
| ctx `+0x14` | transmit buffer both send paths build their header in | not established here | `func_ov066_0226943c`, `func_ov066_02269528` |
| ctx `+0x28`, 0x60 bytes | the state block the 0x68-byte broadcast ships | not established here | `func_ov066_0226943c` |
| ctx `+0xc0` | the state word; bit 0 "busy", bit 1 "pending", read as `lsl #0x1f / asrs #0x1f` | many | many |
| session `+0x30` / `+0x34` | completion callback and its argument, caller-supplied | `func_ov066_02267530`, `func_ov066_022672b8`, `func_ov066_0226b9b8` | `func_ov066_02266bf4` |
| session `+0x38` | `int (*)(void)`, caller-supplied | `func_ov066_02267530` | `func_ov066_02266824` |
| scan `+0x6c` | the per-beacon ACCEPT hook, `int (*)(void *)` | `func_ov066_02267e00`, `func_ov066_02267e28` | `func_ov066_0226783c` |
| manager `+0xc` | the beacon-table entry hook, `void (*)(Entry *)` | the game's own allocation | `func_ov066_0226a494` (insert), `func_ov066_0226a43c` (expiry) |
| request block `+0x20` | completion callback, `void (*)(void *self)`, called when `+2` is 0 | the game's own allocation | `func_ov066_0226adcc` |
| `WMArm9Buf +0x18`, 42 entries | the WM async API callback table | each `WM_*Async` caller | `WmReceiveFifo` |
| `WMArm9Buf +0xc0` | `indCallback` | `WM_SetIndCallback` ← `func_ov066_0226b818` | `WmReceiveFifo` |
| `WMArm9Buf +0xc4`, 16 entries | `portCallbackTable`; 12 and 13 are the game's | `WM_SetPortCallback` ← `func_ov066_0226923c`, `func_ov066_0226aab8` | `WmReceiveFifo` |

[S: every row's reader and writer resolved by disassembling all 171 ov066 functions for
`ldr`/`str` at `+0x9c`..`+0xbc` and for the literal `0x0226bdf4`; the literal appears in 60
ov066 functions and in NO other module]
[E: `scratchpad/struct100/item2-census.txt`]

## How to check it

The block's readers and installers are a static fact and the sweep that found them is
reproducible without the game: disassemble ov066 with `tools/agent/target.py` and list every
`ldr`/`str` at one of the nine offsets, then keep the loads whose register is branched to within
eight instructions. Twelve loads survive, across the seven slots the table above names, and the
stores are three functions. For the runtime half — that the words in those slots really are ov066
addresses and not host ones — the port's own gate is
`python port/tools/test_callback_struct.py`, which puts a real ARM word in each field and
requires every reader to enter the interpreter with the arguments the table claims; its negative
arm calls the word instead and dies with `0xc0000005`
[E: `scratchpad/struct100/fixture/receipt.json`].

## Hypotheses

- **`+0xa8` is installed and never read.** Either a reader exists in a module the context
  pointer never reaches (the global is referenced only from ov066, so it would have to arrive as
  an argument), or the slot is vestigial. The experiment that settles it: put a distinguishable
  word in `+0xa8` on a live host and a live guest through a full visit and see whether anything
  ever loads it — `experiments/` has no page for this yet.
- **The `+0xbc` handler's argument is not identified.** Its one reader passes its own first
  argument straight through, so the question is who calls `func_ov066_02269204` and with what;
  `func_ov066_02268f98` does, with a 16-bit field of a per-peer struct.
- **The beacon payload is 0xc0 bytes and its layout is not read here.** It is the beacon body
  the scan filter's accept hook judges, so `multiplayer-protocol.md`'s beacon section and this
  page's manager entry describe the same bytes from two ends.

## Related

- [`multiplayer-protocol.md`](multiplayer-protocol.md) — the control ids these callbacks carry
- [`multiplayer-visit.md`](multiplayer-visit.md) — the ten-step arrival the host and guest run
- [`network.md`](network.md) — the two wireless stacks and what the port answers
- [`wifi-g2.md`](wifi-g2.md) — the gate at which these callbacks first hold real words
