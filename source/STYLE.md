# Page template and rules

Every page under `engine/`, `systems/` and `data/` has this shape. Keep pages between
80 and 400 lines; split rather than exceed.

```
# <Title>

**Summary.** Two to five sentences a player or a porter can act on. No citations here.

## What happens
Prose. Each sentence that states a fact ends with a grade tag and a citation:
  ... the clock advances once per frame [S: OS_GetTick, autoload_2, src/matched/OS_GetTick.c].
  ... the taxi ride lasts about 6,000 frames [E: scratchpad/cycle40/runs/tap-D56 9000..15000] [O: scratchpad/oracle/tap-fullpad].

## Where it lives
Table: function or symbol | module | role | grade/citation.

## Data it reads and writes
Table: address or field | meaning | who writes | who reads.

## How to check it
Either a link to an `experiments/` page or an inline recipe: the exact environment
(ACWW_* variables), the stop frame, what to look at, what the expected observation is.

## Hypotheses
Bullets, each ending with the experiment that would settle it. Empty section allowed.

## Related
Links to other pages.
```

## Rules

1. **No claim without a grade and a citation.** A reviewer strikes any sentence lacking one.
2. **Names are the symbol table's.** `func_XXXXXXXX`, `func_ovNNN_XXXXXXXX`, SDK names
   (`OS_`, `FS_`, `NNS_`, `TP_`, `CARD_`) as `tools/agent/target.py` loads them. An invented
   name goes in quotes with "(invented)" the first time.
3. **Addresses are NDS addresses** (0x02xxxxxx, 0x01ffxxxx), never host addresses.
4. **Frames are the port's frame counter** (`ACWW_STOP_FRAME`, `ACWW_SHOT_*`); say when a
   frame number comes from the oracle, whose mapping to the port's counter is assumed
   offset 0 (see `port/tools/oracle/README.md`).
5. **Korean UI text**: quote at most one short phrase per screen for identification,
   e.g. `당신 이름은?`; never paragraphs.
6. **No code listings.** A control-flow description in words is fine; a transcription is not.
7. **Contradictions are content.** When the port and the oracle disagree, both observations
   go on the page with their grades and the disagreement is a Hypothesis.
8. **Experiments are pages.** `experiments/<slug>.md` = purpose, recipe (copy-pasteable),
   expected observations with frames, the run that produced them, what would falsify it.
9. English is the language of record; agent-facing.

## Where to look

- Symbols and modules: `tools/agent/target.py` (`T.load_all()`), `port/build/acww.map`,
  `docs/kb/modules/*.md` (native-era notes on what each overlay is).
- Matched sources: `src/matched/<name>.c` (29k files; a header comment states what the
  file is and whether it is byte-identical).
- Runtime behaviour: `docs/log/cycle40-keyboard-gate-probe.md` (the interpreter path's
  journey to the town), `scratchpad/cycle40/runs/*`, `scratchpad/oracle/*`.
- Recipes: `docs/kb/hybrid/recipes.md` (when present), `scratchpad/cycle40/run_direct.py`,
  `scratchpad/cycle40/tap.sh`, `port/tools/oracle/README.md`.
- ROM file system layout: `extract/adm-kr/files/` (directory names only; do not copy
  contents).
