# Display callbacks: the list the V-Blank and H-Blank handlers walk

**Summary.** The game keeps ONE singly-linked list of display-callback nodes, and three
different walkers run over it at three different moments: once per frame to commit staged
changes and run the per-frame work, once per frame to run the per-frame handler, and once per
SCANLINE to run the per-line handler. A node carries two PAIRS of handler words -- a live pair
the walkers call and a staged pair a mode change writes -- and a state byte that says whether a
commit is owed. Which pair of handlers a node holds is chosen by which 2D ENGINE the
perspective background is being driven on: the sub engine and the main engine have their own
twin of each handler, writing their own register block.

Every claim here is read off the game's own code and off recorded pre-call memory images; the
two agree. Provenance for each is marked [S: source] or [M: measured].

## The node

The list head is `data_021c9aa8` and the tail pointer is `data_021c9aac` [S]. In a town scene
the list has exactly ONE node, at `0x021f6d2c` [M].

| offset | what it is |
|---|---|
| `+0x00` | the state byte: `0` freshly registered, `1` live, `2` a new handler pair is STAGED |
| `+0x04` | a handler called on EVERY commit pass, whatever the state |
| `+0x08` | the LIVE per-frame handler |
| `+0x0c` | the LIVE per-scanline handler |
| `+0x10` | the STAGED per-scanline handler |
| `+0x14` | the STAGED per-frame handler |
| `+0x18` | the next node |

## The four functions that touch it

- **register** -- takes the node and three handlers, writes `+0x10`, `+0x08`, `+0x04`, zeroes
  `+0x0c` and the state byte, and appends the node to the list [S].
- **stage** -- writes `+0x14` and `+0x10` and sets the state byte to `2` [S]. This is how a mode
  change asks for a different pair without tearing a frame.
- **commit / per-frame pass** -- walks the list; on state `0` or `2` it sets the state to `1` and
  copies `+0x10` into `+0x0c` (and on state `2` also `+0x14` into `+0x08`), then calls the
  per-frame handler; it calls `+0x04` on every node on every pass regardless [S].
- **the per-scanline walk** -- returns immediately if the scanline counter has reached 192, then
  calls `+0x0c` on every node whose word is non-null [S]. This is the H-Blank handler, and it is
  entered once per visible line, 192 times a frame [M].

A consequence worth knowing before trusting any experiment on this list: **`+0x0c` and `+0x10`
hold the SAME word whenever nothing new has been staged since the last commit** [M], so a test
that reads the wrong one of the two cannot tell them apart in a steady scene.

## The two engine arms

One function installs the pair, and it takes a single argument that selects an engine [S]:

| argument | the pair it stages | the register block its handlers write |
|---|---|---|
| `0` | the SUB-engine per-scanline and per-frame handlers | `0x040010xx` (engine B) |
| non-zero | the MAIN-engine twins of both | `0x040000xx` (engine A) |

Both arms are otherwise the same sequence: a mode call, a read of the clock's hour byte, a
day/night branch, four read-modify-writes of that engine's two background control words, and
then the stage call. The day/night branch tests the hour for `6 <= hour < 18` [S] -- the same
test the per-frame handler itself makes to decide whether the first background plane is visible.

**Which arm runs is decided by one flag**, checked at the two call sites that pass a non-zero
argument [S]. In every scripted scene this repo measures with -- boot, title, continue, the town
on foot, a villager conversation, across 9,000 frames -- the installer is called exactly TWICE
and both times with `0` [M], so the main-engine pair is never installed and its two handlers
never run. That is a fact about those scenes, not about the game: the other arm exists, has its
own twin of each handler, and the per-scanline table the handlers index has entries for modes
the sub-engine arm does not select.

## Why the shape is like this

The staged/live split is what lets a mode change be requested at any point in a frame and take
effect only at a frame boundary: the per-scanline handler is called 192 times between commits,
and swapping the word it reads mid-frame would show a seam. The state byte carries the same
information a double-buffer flag would, with the advantage that a node registered but never
staged (`state == 0`) still gets its per-scanline handler published on the first pass.
