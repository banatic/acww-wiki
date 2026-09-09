# Display objects

**Summary.** Everything the game draws or steps is a "display object": a C++ object that owns
two list nodes and lives on one of four global lists — initialise, update, draw and destroy.
Once per frame a stepper walks each list and calls a pointer-to-member on every object it
finds. Each stepper drives three vtable slots in a fixed pattern: a predicate that decides
whether to act, the work itself, and a handler told what happened. An object is built by a
channel constructor, joins a pending list, is committed onto the real lists, and is refused
every step until a gate opens. When a scene exists but nothing moves, that gate is the thing
to read.

## What happens

### The four lists

Four list heads sit adjacent in main RAM: `0x021fd004`, `0x021fd014`, `0x021fd024` and
`0x021fd034` [S: `port/shim/gfx/dispstep.c:28-30, 55-58`]. They are ADDRESSES, not pointers to
be dereferenced — the ROM loads each with a PC-relative literal load and passes it straight to
the list call [S: `port/shim/gfx/dispstep.c:29-31`]. Their roles are the initialise list
(`0x021fd014`), the update list (`0x021fd004`), the draw list (`0x021fd024`) and the destroy
list (`0x021fd034`) [S: `port/shim/gfx/commit.c:22-24`; `port/shim/gfx/dispsteppers.c:24-28`].

### The four steppers, and the three-slot pattern

Each list has its own stepper, and all four are the same shape: a call to `func_01ffd44c` with
the list object and three member pointers read out of the function's literal pool
[S: `port/shim/gfx/dispsteppers.c:10-18`]. `func_01ffd44c` calls its THIRD parameter first,
its SECOND next, and its FOURTH last, with a marker derived from the second's return
[S: `port/shim/gfx/dispsteppers.c:16-18`].

Read off the pool words rather than off any reconstruction's parameter names
[S: `port/shim/gfx/dispsteppers.c:20-31`, from `extract/adm-kr/arm9/itcm.bin` and
`unk_autoload_2.bin`]:

| stepper | list | second parameter | third parameter | fourth parameter |
|---|---|---|---|---|
| `func_020ede60` | `0x021fd014` (init) | vtable slot 0 | slot 1 | slot 2 |
| `func_01ffd14c` | `0x021fd004` (update) | slot 6 | slot 7 | slot 8 |
| `func_01ffd0e4` | `0x021fd024` (draw) | slot 9 | slot 10 | slot 11 |
| `func_020edddc` | `0x021fd034` (destroy) | slot 3 | slot 4 | slot 5 |

One pattern, four times: the middle slot is a PREDICATE and runs first, the low slot is the
WORK and returns 1 on success, and the high slot is the HANDLER, entered with 2 when the work
returned 1 [S: `port/shim/gfx/dispsteppers.c:32-36`]. The regularity is the argument that this
reading is the right one — the alternative applies the same permutation to all four groups to
no purpose [S: `port/shim/gfx/dispsteppers.c:36-40`]. All twelve of those member pointers
carry a this-adjustment of 0 [S: `port/shim/gfx/dispsteppers.c:41-43`].

A concrete consequence: `func_020a553c` is slot 5, it clears the byte that `func_020a536c`
refuses to load a new scene through, and it acts only when its second argument is 2 — which is
what the fourth parameter receives [S: `port/shim/gfx/dispsteppers.c:32-38`].

Byte matching cannot settle which pool word is which, because the harness masks literal-pool
relocations: a function that loads three data addresses from its pool is byte-identical under
any permutation of the three names [S: `port/shim/gfx/dispsteppers.c:8-14`].

### The walk itself

`func_020ee834` is the list walk
[S: `func_020ee834`, autoload_2, `port/shim/gfx/pmflist.c` header]. Its argument holds a
list head and a two-word
pointer-to-member; it takes each node's object and invokes the member pointer on it
[S: `func_020ee834`, autoload_2, `port/shim/gfx/pmflist.c` header and `:104-118`]. A node on one
of those four lists is three words — previous, next and a back-pointer to the object
[S: `port/shim/gfx/pmflist.c:106-119`]. There is a FIFTH list, at `0x021fcff8`, whose nodes are
the `sub` block at `+0x14` of each display object and whose layout is different; `func_020ee9a0`
runs the four through `func_020ee834` and that one through its own walk
[S: `port/shim/gfx/pmflist.c:961-972`].

Two properties of the walk are the ROM's and are load-bearing: `next` is read BEFORE the call,
because the call may unlink the node it was made for; and the current node is published at
`0x021fcff4` both before the loop and after each step, because something else reads it while
the callback runs [S: `port/shim/gfx/pmflist.c:36-39, 726-729`].

The member pointer is mwcc's two-word layout, and this function's own instructions show it
being decoded with the adjustment applied: word 0 is either the function address or a vtable
BYTE offset, and word 1 is `(delta << 1) | isVirtual` — bit 0 selects virtual, and the
this-pointer is the object plus word 1 arithmetically shifted right by one
[S: `func_020ee834`, autoload_2, `port/shim/gfx/pmflist.c:22-34`]. This is the third
independent confirmation of that layout and the only one that shows the adjustment in use
[S: `port/shim/gfx/pmflist.c:22-24`].

### Per-object step: rebuild or sync

The per-frame state step is `func_01ffd1b4`, 0x230 bytes of ARM in `itcm`, reached once per
object per frame through the object's vtable via
`func_020ee934 -> func_020ee9a0 -> func_020eea4c` [S: `func_01ffd1b4`, itcm,
`port/shim/gfx/dispstep.c` header]. It has two halves
[S: `port/shim/gfx/dispstep.c:19-27`]:

- a REBUILD when the dirty byte at `+0x0f` is set: unlink the object's two nodes (at `+0x28`
  and `+0x38`) from whichever lists hold them, relink the first, and mark every child on the
  `+0x18` list as needing the same treatment;
- otherwise a SYNC: copy two flag bits down from the object `func_020ee45c` returns, and
  re-sort each node whose sort key at `+0x0e` no longer matches the key it was last sorted
  under at `+0x0c`.

The node's state byte at `+0x0e` runs 1 (live, sorted) to 2 (rebuilding) and back
[S: `port/shim/gfx/dispstep.c:32-35`]. Reading those bytes as a single enum is wrong:
`0x01ffd35c` tests for 2 specifically and falls through for anything else, so a fourth value is
possible and is handled by doing nothing [S: `port/shim/gfx/dispstep.c:33-35`].

### Joining and committing

`func_020edec8` is the hook that puts a newly built display object on the pending list, and it
has four distinct ways to decline: two flags that say the object is not ready, one that says
it is already live, and one that says the walk currently running is the wrong one
[S: `func_020edec8`, autoload_2, `port/shim/gfx/dispjoin.c` header]. `func_020ee59c` is the
commit, and it is the only function in the ROM that writes the deferral byte at `+0x10`
[S: `func_020ee59c`, autoload_2, `port/shim/gfx/commit.c` header, body from
`src/matched/func_020ee59c.c`]. The commit's behaviour depends on the global walk mode at
`0x0213e7fc` [S: `port/shim/gfx/commit.c:21, 64`]. Committing while mode 3 is live appends to
`0x021fd004` while that very list is being walked
[S: `port/shim/gfx/commit.c:58-63`].

### The gate every step is behind

`func_01ffd41c` is six instructions and one test: the step happens only when the object's
`+0x0f` is clear AND bit 1 of `+0x13` is clear [S: `func_01ffd41c`, itcm,
`port/shim/gfx/dispgate.c` header]. `+0x0f` is written by the display step and `+0x13` by the
constructor copying its parent's [S: `port/shim/gfx/dispgate.c:10-12`].

Upstream of that gate is one predicate: `func_020edd74` answers "is any of my children not
live yet?" by walking the child list with `func_01ffcfc0` as the end sentinel and
`func_01ffcffc` as the successor [S: `func_020edd74`, autoload_2,
`port/shim/gfx/childlive.c` header, body from `src/matched/func_020edd74.c`]. When it answers
1, `func_020a5430` leaves the scene's `+0x13` bit 0 set; the constructor propagates bit 0 to
every child as bit 1 and bit 2 as bit 3; and the gate then refuses every step for the whole
subtree [S: `port/shim/gfx/childlive.c:7-16`]. A scene object at `+0x13 = 0x05` gives its
children `0x0a`, and `0x0a` is refused [S: `port/shim/gfx/childlive.c:17-19`].

### The VBlank task list

Separate from the four lists is a VBlank task list at `0x021f6ca0`, walked by `func_020b98ec`
[S: `port/shim/gfx/vbtask.c:22-25`]. Each task's node sits four bytes into its object, and each is run through vtable slot 0 inside
the VBlank [S: `func_020b98ec`, main, `port/shim/gfx/vbtask.c` header, body from
`src/matched/func_020b98ec.cpp`]. The ROM has no null-vtable check there because on the NDS a
null read returns ITCM-mirror bytes [S: `port/shim/gfx/vbtask.c:8-11`].

### Drawing

The draw path an object takes is `func_02055e7c`, which sets the object's camera state through
`func_02055e10` and then draws it with `func_02055e04`
[S: `func_02055e7c`, main, `port/shim/gfx/drawobj.c` header]. `func_02055e10` takes a scale as
its second argument (a null scale picks a unit one) and ends in `NNS_G3dGlbFlushP`, which is
what actually uploads the camera and projection state to the geometry engine
[S: `port/shim/gfx/drawobj.c:1-16`].

Two objects are worth naming because nothing can address them from a constant — their
allocations move between runs. The first is channel 189's object, vtable `0x022382ac`; geometry
is drawn relative to its `+0x5c` [S: `port/shim/gfx/pmflist.c:52-56`]. **That object is the
SNOWMAN, not the town's field renderer**, and the "field renderer" label the port's own shim
headers still carry is a retracted misidentification: channel 189's bind log names
`/snowman/snowball1.nsbmd` (`SNW0`, id `0x022383ac`) and `/snowman/snow_face.nsbmd` (`SNW1`,
id `0x022383c8`), both strings resident in `ov003` at those addresses
[E: `port/BOOT-STATE.md:1159-1171`, "CHANNEL 189 IS THE SNOWMAN"; see `../systems/town.md`].
The FIELD CAMERA's vtable is `0x020da87c` and its draw
slot `func_0203c610` sets both the projection and the view matrix, reading `at` from `+0x188`,
`eye` from `+0x194`, `up` from `+0x1a0`, near from `+0x1b0`, far from `+0x1b4` and a field-of-view
angle index from `+0x1c8` [S: `port/shim/gfx/pmflist.c:59-63, 184-190`].

### The framework is one subsystem — a lesson from porting it

On the PC port the display-object framework spans 29 files of hand-written host code, and
denying a SUBSET of them to the ROM stalls the boot: with the ROM's walk interpreted but a
native join and commit still linked and called from a native VBlank handler, join refused what
the walk expected and nothing ever entered the update list — 36,000 identical frames on the
Nintendo logo [E: `docs/log/cycle40-keyboard-gate-probe.md` REG40b and REG40c]. Denying all 29
passes [E: same]. The rule generalises: the framework is one subsystem, and it is either the
ROM's or the port's, never half of each [E: `docs/kb/hybrid/runtime.md` section 5].

The measured symptom of the update list dying is quiet: a run where the update list is walked
once at frame 0 and never again while the town keeps drawing
[E: `port/shim/gfx/pmflist.c:696-700`, the per-list pass counters].

## Where it lives

| function or symbol | module | role | grade / citation |
|---|---|---|---|
| `func_020ee834` | autoload_2 | the display-list walk; decodes a pointer-to-member inline | [S: `port/shim/gfx/pmflist.c` header] |
| `func_01ffd44c` | itcm | runs three slots per object: predicate, work, handler | [S: `port/shim/gfx/dispsteppers.c:16-18`] |
| `func_020ede60` / `func_01ffd14c` / `func_01ffd0e4` / `func_020edddc` | autoload_2, itcm | the init / update / draw / destroy steppers | [S: `port/shim/gfx/dispsteppers.c:24-28`] |
| `func_01ffd1b4` | itcm | per-object rebuild-or-sync state step | [S: `port/shim/gfx/dispstep.c` header] |
| `func_020ee934` / `func_020ee9a0` / `func_020eea4c` | autoload_2 | the chain that reaches the per-object step | [S: `port/shim/gfx/dispstep.c:17-19`] |
| `func_01ffd41c` | itcm | the gate: `+0x0f` clear and `+0x13` bit 1 clear | [S: `port/shim/gfx/dispgate.c` header] |
| `func_020edd74` | autoload_2 | "is any child not live yet?" | [S: `port/shim/gfx/childlive.c` header] |
| `func_01ffcfc0` / `func_01ffcffc` | itcm | list end sentinel and successor | [S: `port/shim/gfx/childlive.c:22-23`] |
| `func_020edec8` | autoload_2 | join the pending list; four ways to decline | [S: `port/shim/gfx/dispjoin.c` header] |
| `func_020ee59c` | autoload_2 | commit; the only writer of the `+0x10` deferral byte | [S: `port/shim/gfx/commit.c` header] |
| `func_020e8ce0` / `func_020e8c70` / `func_020ee8a8` | autoload_2 | unlink, append, insert-in-sort-order | [S: `port/shim/gfx/dispstep.c:44-47`] |
| `func_020ee45c` / `func_020ee470` | autoload_2 | the object the sync copies flag bits from | [S: `port/shim/gfx/dispstep.c:48-49`] |
| `func_020b98ec` | main | the VBlank task list walk | [S: `port/shim/gfx/vbtask.c` header] |
| `func_02055e7c` / `func_02055e10` / `func_02055e04` | main | set camera state, then draw | [S: `port/shim/gfx/drawobj.c` header] |
| `NNS_G3dGlbFlushP` | main | uploads camera and projection to the geometry engine | [S: `port/shim/gfx/drawobj.c:11-13`] |
| `func_0203c610` | main | the field camera's draw slot: projection and view | [S: `port/shim/gfx/pmflist.c:59-61`] |
| vtable `0x022382ac` | ov003 | channel 189's object — the SNOWMAN, not the field renderer | [E: `port/BOOT-STATE.md:1159-1171`] |

## Data it reads and writes

| address or field | meaning | who writes | who reads |
|---|---|---|---|
| `0x021fd014` | the INITIALISE list head | join/commit | `func_020ede60` [S: `port/shim/gfx/commit.c:22`] |
| `0x021fd004` | the UPDATE list head | join/commit | `func_01ffd14c` [S: `port/shim/gfx/commit.c:23`] |
| `0x021fd024` | the DRAW list head | join/commit | `func_01ffd0e4` [S: `port/shim/gfx/commit.c:24`] |
| `0x021fd034` | the DESTROY list head | join/commit | `func_020edddc` [S: `port/shim/gfx/dispsteppers.c:28`] |
| `0x021fcff4` | the node the walk is stepping right now | `func_020ee834` | read by something while the callback runs [S: `port/shim/gfx/pmflist.c:36-39`] |
| `0x0213e7fc` | the global walk mode; 3 defers a commit | the steppers | `func_020ee59c` [S: `port/shim/gfx/commit.c:21, 64`] |
| `0x021f6ca0` | the VBlank task list head | task registration | `func_020b98ec` [S: `port/shim/gfx/vbtask.c:22-25`] |
| object `+0x0f` | dirty byte: rebuild wanted; also gates the step | the display step | `func_01ffd1b4`, `func_01ffd41c` [S: `port/shim/gfx/dispstep.c:21`, `dispgate.c` header] |
| object `+0x10`, `+0x11` | the two request bytes, consumed and cleared | `func_020ee59c` writes `+0x10` | `func_01ffd1b4` [S: `port/shim/gfx/dispstep.c:32-33`] |
| object `+0x13` | flag bits; bit 1 refuses the step, propagated to children | the constructor, `func_020a5430` | `func_01ffd41c` [S: `port/shim/gfx/childlive.c:7-16`] |
| object `+0x18` | the child list | the constructor | `func_020edd74`, the rebuild [S: `port/shim/gfx/dispstep.c:21-23`] |
| object `+0x28`, `+0x38` | the object's two list nodes | join/commit | the rebuild [S: `port/shim/gfx/dispstep.c:21-22`] |
| node `+0x0c`, `+0x0e` | last-sorted key and current sort key | the sync | the re-sort [S: `port/shim/gfx/dispstep.c:25-26`] |
| field camera `+0x188` / `+0x194` / `+0x1a0` / `+0x1b0` / `+0x1b4` / `+0x1c8` | at, eye, up, near, far, fov index | the camera's own logic | `func_0203c610` [S: `port/shim/gfx/pmflist.c:184-190`] |

## How to check it

Run any recipe from `docs/kb/hybrid/recipes.md` with `ACWW_TRACE_STATE` set and read three
instruments the port prints from inside the walk: `acww passes: frame N init=... update=...
draw=... destroy=...` every 600 frames, which makes a pass that has stopped visible as a
counter that has stopped [S: `port/shim/gfx/pmflist.c:696-722`]; `acww listwalk: list ... node
... back-pointer ... is not an object`, which names a node that is linked but whose object word
is not main RAM [S: `port/shim/gfx/pmflist.c:731-757`]; and `acww camnf: obj ... near ... far
...`, printed whenever the field camera's near/far pair changes
[S: `port/shim/gfx/pmflist.c:203-232`].

The falsifying observation for "the framework is running" is the update-list counter: if
`update=` stops advancing while `draw=` continues, objects are being drawn and nothing is
being stepped [E: `port/shim/gfx/pmflist.c:696-700`].

## Hypotheses

- (Settled, kept for the record.) The `+0x08` versus `node+0x10` disagreement over the node's
  object back-pointer was two different node kinds, not one contradiction. `func_020ee834`'s
  four lists use a three-word node `{prev, next, obj}` with the object at `+0x08`
  [S: `port/shim/gfx/pmflist.c:106-119`]. The FIFTH list, at `0x021fcff8` — whose nodes are the
  `sub` block at `+0x14` of each display object, walked by `func_020ee9a0` — has `head` at `+0`,
  the member pointer at `+4`/`+8` and the object at `node+0x10`, and takes `next` by CALLING
  `func_01ffcffc(node)` rather than loading a field, because the callback may unlink the node
  [S: `port/shim/gfx/pmflist.c:961-981`, read off the ROM's instructions].
- The two nodes at `+0x28` and `+0x38` are "this object on list X" and "this object on list Y"
  for a fixed pair of lists, not a free pair [H: settled by logging, per object, which list
  head each of its two nodes is linked into across a scene change].
- A fourth value of the node state byte at `+0x0e` exists in real play, not just in principle
  [H: settled by a watchpoint on that byte over the town recipe, recording every distinct
  value].
- Every one of the twelve stepper slots is populated by at least one live class [H: settled by
  counting dispatches per slot over the town recipe with the per-object trace already in
  `port/shim/gfx/dispsteppers.c`].

## Related

- `scenes-and-channels.md` — what constructs these objects, and the gate above the gate
- `threads-and-interrupts.md` — the VBlank the task list runs inside
- `memory-map.md` — the `0x021fdxxx` list band
- `overlays.md` — the destructor chain an overlay unload sweeps
