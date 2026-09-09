# ACWW Wiki (Animal Crossing: Wild World, Korean release "ADMK")

A game-mechanics wiki written to an evidence standard: every claim carries a grade and a
citation that a reader can re-check against the symbol tables, the matched sources, a
scripted run of the PC port, or the emulator oracle. Prose is for readers; the citations
are for anyone who wants to verify or correct. Korean-language pages may be added beside
the English ones later; the English page is the page of record.

## Layers

| directory | scope | what a page answers |
|---|---|---|
| `engine/` | how the program is built | boot, overlays, scenes/channels, display objects, memory, threads, file system, text system |
| `systems/` | how the game behaves | time, save, input, RNG, weather/seasons, economy, villagers, player, town, events, dialogue, network, audio |
| `data/` | what the tables hold | item, villager, fish/bug, music and archive indices: structure, location, counts, how to read them |
| `experiments/` | how a claim is checked | one reproducible recipe per page: environment, expected observations, evidence run |
| `glossary.md` | words | terms used across pages, each with the function or address that defines it |
| `audits/` | the wiki reading itself | one page per audit pass: every finding as page, sentence, problem, and the fix applied or the experiment needed |

## Evidence grades (mandatory on every claim)

| grade | meaning | what the citation must name |
|---|---|---|
| **S** source | read from a matched function or a symbol table | `func_XXXXXXXX` / symbol name, module, and the file under `src/matched/` |
| **E** experiment | observed in a scripted run of the port | the run directory under `scratchpad/` (or the `experiments/` page) and the frame |
| **O** oracle | observed in the DeSmuME reference under the same recipe | the `scratchpad/oracle/<dir>` and the frame |
| **H** hypothesis | inferred, not yet measured | what experiment would settle it |

A claim with two grades (S+O, E+O) is stronger than one; S alone says what the code does,
not that the game was seen doing it. A page section headed **Hypotheses** is the queue of
experiments the wiki is asking for.

## Boundaries

- No decompiled code, ROM strings beyond a short quoted UI phrase needed to identify a
  screen, sound or image assets, or table dumps. Describe structure and behaviour; cite
  addresses and names.
- No claims copied from fan wikis. Where a fan wiki's number agrees with a measured one,
  the measured citation is the evidence; where it disagrees, say so.
- The port is a measuring instrument, not the truth: a port-only observation is grade E
  and stays E until the oracle agrees (O) or the source explains it (S).

See `STYLE.md` for the page template.
