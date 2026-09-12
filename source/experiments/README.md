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
| `gameplay-walkthrough.md` | past the town hall: out of the building, walking the town, the map, the pockets, night, the save menu -- from a snapshot with a pad script |
| `touch-calibration.md` | what the ROM's own touch point holds on the original: 221,181 in, 222,182 out, one to two frames late |
| `touch-latency.md` | how many frames a contact takes to reach the game, and why the ARM7's samples must land after the ROM's VBlank handler |
| `savestate-resume.md` | snapshot a run at frame N and resume from it exactly, turning ten minutes of replay into one |
| `save-and-reload.md` | does a PLAYED game persist: the card-request census of a whole town run, what the game writes, and the second launch that boots into the saved town |
| `live-play.md` | driving the port from a keyboard: `play.py`, the 59.8261 Hz pacer, the key map, the stylus hold -- and the receipt that no scripted run moved |
| `run-stability.md` | what an exit code means on this image, why an exit 1 is always an external kill, and what a 48,000-frame run costs |

## Designed, not yet run

| page | the question |
|---|---|
| `rtc-hour-sweep.md` | does the hour change the scene, and does the original change the same way |
| `save-store-probe.md` | superseded by `save-and-reload.md`; its arm B is run, arms A and C are not |
| `rng-determinism.md` | is a port run identical to itself, and does one second of clock change anything |
| `silent-audio-probe.md` | which sound command ids does the game actually emit -- **superseded**: the uncapped census answers it, see `../systems/audio.md` |

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
- **Freeze the clock when comparing against a run taken before 2026-09-09.** The port's RTC
  advances now, and the minute drives the day/night blend, so every frame differs; set
  `ACWW_RTC_FREEZE=1` [H: log/source account: `../systems/time-and-rtc.md`; receipt provenance unresolved].
- **An exit code of 1 is somebody else's `taskkill`, not a failure.** Nothing in the image exits
  1 [H: log/source account: `run-stability.md`; receipt provenance unresolved].

## Related

- `../systems/README.md`, `../STYLE.md`
- `docs/kb/hybrid/recipes.md` -- the operational version of these recipes, kept beside the code.
- `port/tools/oracle/README.md` -- how the reference is produced and what it is not.
