# Experiments

One reproducible recipe per page: purpose, environment (`ACWW_*` variables, the oracle
command), expected observations with frames, the run that produced them, what would falsify it.

A page is either **run** -- it names the run directory its numbers came from -- or **designed,
not yet run**, in which case it carries the exact environment and command a future run would
use, and its predictions are written to be falsifiable rather than to be confirmed.

## Run

| page | what it establishes |
|---|---|
| `off-recipe.md` | the control: 31 screenshots to frame 9,000 with the stylus off, compared by SHA-256 |
| `two-tap-town-recipe.md` | the game from the title screen to the town hall, 48,000 frames, and the oracle comparison over it |
| `touch-calibration.md` | what the ROM's own touch point holds on the original: 221,181 in, 222,182 out, one to two frames late |

## Designed, not yet run

| page | the question |
|---|---|
| `rtc-hour-sweep.md` | does the hour change the scene, and does the original change the same way |
| `save-store-probe.md` | does the game issue backup requests, and does anything reach the file |
| `rng-determinism.md` | is a port run identical to itself, and does one second of clock change anything |
| `silent-audio-probe.md` | which sound command ids does the game actually emit |

## Rules that apply to all of them

- **Run the control first (M15).** An ON arm without its OFF arm measures nothing.
- **`ACWW_KEYS_AT` / `_FOR` / `_EVERY` are the key names (B1).** The short forms are not read and
  silently turn the run into the DEMO cycle.
- **Say which path, which launcher, which artifact, which endpoint (B1, B8, B32, B38).** A
  receipted run and a direct `acww.exe` diagnostic are different claims.
- **Do not judge on a frame count or a wall clock (B12).** Judge the endpoint, the exact failure
  identity and the images.
- **Suspect the measurement first (M1).** Four tools in this project were wrong before they were
  right.
- The port is an instrument, not the truth: a port-only observation is grade E and stays E until
  the oracle agrees or the source explains it.

## Related

- `../systems/README.md`, `../STYLE.md`
- `docs/kb/hybrid/recipes.md` -- the operational version of these recipes, kept beside the code.
- `port/tools/oracle/README.md` -- how the reference is produced and what it is not.
