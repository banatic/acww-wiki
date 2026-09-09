# Save store probe

**Status: designed, not yet run.**

## Purpose

The port has a real 256 KB backup store behind `ACWW_SAVE`, and as far as any record goes it has
never persisted a byte on a game run. The shim counts what it writes and prints the total, so
the question is directly answerable [E: `port/shim/fs/cardreq.c`]. Three things are worth
separating, and only instruments can separate them:

1. does the game *issue* backup requests on the way to the town hall (request type 6, and ever
   7 or 9)?
2. does anything actually reach the file?
3. does an honest 0xFF-erased read change the boot?

The third has a measured half already: with the read fill on, the keyed START run stopped at
`unimplemented: func_02225a90` around frame 10 (the symbol tables name it
`func_ov003_02225a90`, `ov003` [S: `config/adm-kr/arm9/overlays/ov003/symbols.txt`]), where the same build with the fill off runs
clean [E: `port/shim/fs/cardreq.c`]. That says the honest answer moves the boot onto a path the
port cannot yet follow -- it does not say which path.

## Recipe

Three arms. The first is the control and must be run first (M15).

**Arm A -- no store, the control.** The town recipe exactly as
`two-tap-town-recipe.md` gives it, with `ACWW_SAVE` unset. `run_town.py` already unsets the save
variable in its base, so this is the existing run [E: `scratchpad/cycle40/run_town.py`, `BASE`].

**Arm B -- a fresh erased store.** Delete `scratchpad/save/fresh.sav` if it exists, then:

    python -B scratchpad/cycle40/run_town.py save-fresh \
      ACWW_SAVE=C:/Users/moomin/Desktop/acww/scratchpad/save/fresh.sav \
      ACWW_INTERP=1 \
      ACWW_TOUCH_AT=6900 ACWW_TOUCH_EVERY=60 ACWW_TOUCH_REPEAT=2 \
      ACWW_TOUCH2_X=221 ACWW_TOUCH2_Y=181 ACWW_TOUCH2_AT=24600 ACWW_TOUCH2_FOR=10 \
      ACWW_TOUCH2_EVERY=60 ACWW_TOUCH2_REPEAT=2 \
      ACWW_STOP_FRAME=48000 ACWW_SHOT_AFTER=6000 ACWW_SHOT_EVERY=1500 ACWW_PAD_SAMPLE=0

`run_town.py` unsets `ACWW_SAVE` in its base, so confirm on the boot line that the override
survived before reading anything else -- an arm whose store is silently off is arm A wearing a
different name.

**Arm C -- a zeroed store.** The same, against a file created as 256 KB of `0x00`. This is the
damaged-save branch on purpose: a block of zeros is not an absent save, it is a save whose
header and checksum are zero [E: `port/shim/fs/cardreq.c`].

## Expected observations

The instruments, all in the run log [E: `port/shim/fs/cardreq.c`]:

| line | meaning |
|---|---|
| `acww save: backup store LIVE, 256 KB flash, newly erased (0xFF)` | arm B's store came up |
| `acww save: backup store LIVE, 256 KB flash, existing file` | the file was already full size |
| `acww card: request type 6 (with a command block)` | the first backup read, once per distinct type |
| `acww card: request type 7` / `type 9` | a write and its verify -- **the line that says the game tried to save** |
| `acww save: persisted N bytes` | first write and then every 64 KB -- **the line that says bytes reached the file** |
| `acww pxi: card request ... queued for the next VBlank` | the request took the frame-late path |

Predictions, each falsifiable:

- Arm A and arm B produce **identical screenshots at all 29 frames**, because a fresh 0xFF store
  and no store both mean "no save present" -- unless the untouched-buffer path and the 0xFF path
  differ, which is exactly the `func_02225a90` stop above. If they differ, that stop is
  reproduced on the interpreter path and can be diagnosed with `ACWW_EXPLORE=1`.
- Arm B's file is still 256 KB of `0xFF` afterwards, and there is no `persisted` line: the town
  recipe never reaches an in-game save.
- Arm C diverges from arm A early -- within the first few hundred frames -- and shows the
  damaged-save path.

Afterwards, check the file rather than trusting the log:

    python -c "d=open(r'scratchpad/save/fresh.sav','rb').read(); print(len(d), d.count(255))"

256 KB with a count of 262,144 means nothing was written.

## What would falsify it

- No `acww card: request type 6` line at all: the game never reads the backup on this path and
  every conclusion about save behaviour is about a code path the recipe does not reach.
- A `persisted` line in arm A. `ACWW_SAVE` is unset there; a write means something else opened a
  store.
- Arm B differing from arm A at a frame where neither has issued a write. That is the read fill
  changing the boot, and it is the finding, not the noise.
- Reading the absence of a `persisted` line as "the port cannot save". It says this recipe did
  not save. An instrument that cannot fire is indistinguishable from one that fires and changes
  nothing -- which is the exact shape of the two constant defects this shim already had
  [E: `port/shim/fs/cardreq.c`].

## Related

- `../systems/save-data.md`
- `two-tap-town-recipe.md`
