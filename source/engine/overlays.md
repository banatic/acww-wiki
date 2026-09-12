# Overlays

**Summary.** Beyond the resident `main`, `itcm` and `autoload_2` images, ACWW's code lives in
148 overlay slots that are paged into main RAM on demand. Most of them share addresses with
each other, so "what is at `0x02260020`" has no answer without knowing which overlay is
resident. Loading one copies (and optionally decompresses) its image, then runs its C++ static
initialisers; unloading one sweeps its destructors out of the global chain. The town needs
five overlays resident at once, and the taxi that brings you there is a sixth.

## What happens

### How many, and how big

The build configuration declares 148 overlay slots, `ov000` through `ov147`, beside the main
module and four autoloads (`itcm`, `dtcm`, `autoload_2`, `autoload_3`)
[H: source account: `config/adm-kr/arm9/config.yaml`; 148 directories under
`config/adm-kr/arm9/overlays/`; direct ROM-source provenance unresolved]. 138 of those slots carry at least one function symbol; ten
carry none at all — `ov000`, `ov057` through `ov064`, and `ov089`
[H: source account: counted from `config/adm-kr/arm9/overlays/*/symbols.txt`, `kind:function` lines; direct ROM-source provenance unresolved].

Across every module the symbol tables name 25,516 functions and 15,313 data symbols
[H: source account: counted from `config/adm-kr/arm9/**/symbols.txt`; direct ROM-source provenance unresolved]. `main` holds 11,923 of the functions
and `autoload_2` 2,199; `itcm` holds 158; the overlays hold 11,236 between them
[S: `config/adm-kr/arm9/symbols.txt` (`main` at 0x02000c38); source account: counted from `config/adm-kr/arm9/**/symbols.txt` count]. The overlay band's function addresses run `0x02207cc0` to `0x022a31d8`
[S: `config/adm-kr/arm9/symbols.txt` (`main` at 0x02000c38); source account: minimum and maximum `addr:` over `config/adm-kr/arm9/overlays/*/symbols.txt`,
`kind:function` lines].

### Overlays overlap, and that is the central fact about them

129 of 137 adjacent overlay pairs overlap in address
[H: source account: `port/shim/fs/ovlreloc.c` header; direct ROM-source provenance unresolved]. The sharing is not marginal: 35 overlays begin at
`0x02260020`, 19 at `0x02278a00`, 14 at `0x0229c180` and 12 at `0x02260420`
[H: source account: counted from the minimum function address of each `config/adm-kr/arm9/overlays/*/symbols.txt`; direct ROM-source provenance unresolved].

Two consequences follow, and both have cost the port a fault. First, a word at a shared
address belongs to whichever overlay is loaded, so a relocation table cannot be applied to
all candidates up front — the tables are emitted per overlay id and applied at load time
[H: source account: `port/shim/fs/ovlreloc.c` header; direct ROM-source provenance unresolved]. Second, an address alone does not determine the
instruction set: `ov003` and `ov004` share an address, and a table keyed by address alone ran
the Thumb function `func_ov003_02226048` as ARM, executing a push at the host address of the
function being pushed to [H: log/source account: `docs/log/cycle40-keyboard-gate-probe.md` CARD40..SND40, second
fault; receipt provenance unresolved]. The instruction-set table carries an overlay id beside every entry for that reason
[H: source account: `port/interp/interp.h:64-68`; direct ROM-source provenance unresolved].

### Loading one

An overlay's header is a fixed record: id, RAM address, RAM size, BSS size, the bounds of the
static-initialiser array, the file id, a 24-bit compressed size and an 8-bit flag
[H: source account: `FSOverlayInfoHeader`, `port/shim/fs/ovlreloc.c:31-41`; direct ROM-source provenance unresolved]. `FS_LoadOverlayImage` copies the
overlay's bytes into RAM, and `FS_StartOverlay` finishes the job
[S: `src/matched/FS_StartOverlay.c`, `src/matched/FS_LoadOverlayImage.c`; source account: `FS_StartOverlay` / `FS_LoadOverlayImage`, `port/shim/fs/ovlreloc.c` header]. Bit 0 of
the flag means the image is compressed backward and is expanded by `MIi_UncompressBackward`
[H: source account: `FS_OVERLAY_FLAG_COMP`, `port/shim/fs/ovlreloc.c:50, 56`; direct ROM-source provenance unresolved].

The last thing `FS_StartOverlay` does is walk the array from `sinit_init` to `sinit_init_end`
and CALL each word in it — the overlay's C++ static initialisers
[H: source account: `port/shim/fs/ovlreloc.c` header, and the walk at `:243-258`; direct ROM-source provenance unresolved]. Those words are NDS
addresses in a freshly copied image, which is exactly how the first overlay call presented on
the port as a jump into raw ARM code at `0x02266905`
[H: host-source account from `port/shim/fs/ovlreloc.c` header; verify with a retained scripted run and frame using this page's recipe]. An overlay carries at most a couple of hundred of
them; the interpreter path reads up to 256 [H: source account: `port/shim/fs/ovlreloc.c:206-212`; direct ROM-source provenance unresolved].

There is also an authentication block: `FSi_CompareDigest` checks the image against a digest
table and its only failure path is `OS_Terminate()` [H: source account: `port/shim/fs/ovlreloc.c` header; direct ROM-source provenance unresolved].
The PC port drops it deliberately, and says so rather than dropping it silently
[H: source account: `port/shim/fs/ovlreloc.c` header; direct ROM-source provenance unresolved].

### Unloading one, and the destructor chain

`FS_EndOverlay` sweeps the global destructor chain and unlinks every registered destructor
whose address falls inside the range being unloaded — the test is `lo <= dtor < hi` on the
word as stored [S: `src/matched/FS_EndOverlay.c`; source account: `FS_EndOverlay`, `port/shim/fs/ovlreloc.c:213-220`]. That test is the
reason the PC port cannot rewrite overlay pool words on the interpreter path: rewriting a
code address into a host address puts it outside every NDS range, the node stays linked, the
next overlay is loaded over it, and the chain walks into garbage
[E: `docs/log/cycle40-keyboard-gate-probe.md` OVL40, runs `tap-D53` and `tap-D54` ; `scratchpad/cycle40/runs/tap-D53`, `scratchpad/cycle40/runs/tap-D54`].

An earlier variant of the same fault is worth knowing because it is easy to reproduce by
accident: a HOST `FS_EndOverlay` walked the host C++ runtime's `__global_destructor_chain`
instead of the ROM's, which is a different chain entirely
[E: `docs/log/cycle40-keyboard-gate-probe.md` OVL40, `tap-D52` ; `scratchpad/cycle40/runs/tap-D52`].

### Which overlay carries which feature

The identifications below come from resolving literal-pool words that point at printable ROM
text — the overlays name their own subject through their asset paths
[H: source account: `docs/kb/modules/ov003-068.md`, "What these modules are"; direct ROM-source provenance unresolved].

`ov003` is the outdoor town/field 3D scene module: the whole foreground asset tree (trees,
grass, flowers, holes, stones), houses, ground, the snowman NPC, fish, insects, signboards and
the seasonal texture variants [H: source account: `docs/kb/modules/ov003-068.md`; direct ROM-source provenance unresolved]. `ov004` is its indoor
counterpart — room objects, furniture, TV programmes, walls and floors — and shares a source
tree with `ov003`, down to identical insect tables [H: source account: `docs/kb/modules/ov003-068.md`;
`docs/kb/modules/ov004.md`; direct ROM-source provenance unresolved]. `ov068` is the special-NPC and arrival sequence: the special NPC
models, the dog, the taxi and its parts, the rain and splash effects, and the script labels
of the new-game question sequence — Kapp'n's taxi [H: source account: `docs/kb/modules/ov003-068.md`; direct ROM-source provenance unresolved].

`ov001` is NitroDWC's `util` scene/UI library plus the AOSS/Aterm vendor seam
[H: source account: `docs/kb/modules/ov001.md`; direct ROM-source provenance unresolved]. `ov065` is four components under one overlay from three
vendors: NitroWiFi, NitroDWC and GameSpy [H: source account: `docs/kb/modules/ov065.md`; direct ROM-source provenance unresolved]. `ov067` is
NitroSDK's `add-ins/wxc`, the Wireless eXchange library, and it is fully identified at 54 of
54 functions [H: source account: `docs/kb/modules/ov067.md`; direct ROM-source provenance unresolved]. `ov068`'s slot at `0x022667e0` sits beside
`ov065`, `ov066` and `ov067`, but that is reused transient memory and not a Wi-Fi region
[H: source account: `docs/kb/modules/ov003-068.md`; direct ROM-source provenance unresolved].

`ov126` carries the on-screen keyboard's touch dispatcher `func_ov126_022a1228`, which exists
only as a function pointer — the overlay's relocation at `0x022a1ff0` holds `0x022a1229`, the
Thumb entry [H: source account: `docs/log/cycle40-keyboard-gate-probe.md` PROBE40 unit block; direct ROM-source provenance unresolved]. `ov147` holds
a boot-machine state table in BSS at `0x0229ad4c`, filled by its own static initialiser
[H: source account: `port/shim/gfx/pmflist.c:213-222`; direct ROM-source provenance unresolved].

### Residency during the town sequence

At frame 37,500 of the scripted town run — the player standing in front of the town hall —
overlays 5, 36, 54, 120 and 117 are loaded
[E: `scratchpad/cycle40/runs/tap-D56`, frame 37500;
`docs/log/cycle40-keyboard-gate-probe.md` TOWN40]. Overlay 5 is loaded earlier, during town
entry, before the town's scene-6 stages run
[H: log/source account: `docs/log/cycle40-keyboard-gate-probe.md` CALL40; receipt provenance unresolved].

The symbol tables agree that these are small modules: `ov005` names one function, `ov036`
one, `ov054` 88, `ov117` 31 and `ov120` 95
[H: source account: counted from `config/adm-kr/arm9/overlays/*/symbols.txt`; direct ROM-source provenance unresolved]. `ov054` begins at `0x02260420`
and `ov120` at `0x0229a340` [H: source account: counted from `config/adm-kr/arm9/overlays/*/symbols.txt` tables; direct ROM-source provenance unresolved].

### What a scene transition loads, with a frame on it

Loading is not spread over the transition on the PC port: everything a door needs arrives in
the **single frame** its scene loader runs in, and both frames were measured with the ROM-FS
instrument armed [E: `docs/log/cycle41-gameplay.md` LOAD52 L52-3, `ACWW_FSTRACE=1` ; `scratchpad/load52/RECEIPTS.md`].

| door | frame | read requests | bytes | overlays started |
|---|---|---|---|---|
| the town-hall exit | 49,656 | 35,631 | 1,322,272 | four — 2, 3, 5, 9 |
| villager-1's front door | 57,372 | 7,413 | 724,265 | three — 2, 4, 29 |

Most of the requests are tiny: 4,729 of the door's 7,413 read one or two bytes, which is the
FNT name walk, and its three overlay images are 16,896, 306,432 and 544 bytes. **The
`FS_OVERLAY_FLAG_COMP` bit is clear on all seven of these loads**, so `MIi_UncompressBackward`
does not run at either door — which is a different field from the `compressed:` entry in
`arm9_overlays/overlays.yaml` [E: `docs/log/cycle41-gameplay.md` LOAD52 L52-3, `ACWW_FSTRACE=1` ; `scratchpad/load52/RECEIPTS.md`].

**An overlay already loaded earlier is loaded AGAIN at a transition, and the once-per-id
`acww ovl:` line cannot show it**: overlays 2, 3, 5 and 9 are all printed during the boot, so
the town-hall exit looked as though it loaded nothing at all until the frame-stamped
instrument said otherwise [E: LOAD52 L52-3, retracting TRANSITION51 T51-6; playbook case 116 ; `scratchpad/transition51/RECEIPTS.md`, `scratchpad/load52/RECEIPTS.md`].

### Settled: how many functions `ov004` has

The two numbers on record for `ov004` are not a contradiction, they are two tables. The
committed `symbols.txt` lists 121 `kind:function` entries, of which 90 carry a non-zero size and
31 are zero-sized `_unk` placeholders [H: source account: `config/adm-kr/arm9/overlays/ov004/symbols.txt`,
counted over `kind:function` lines; direct ROM-source provenance unresolved]. Beside it sits `recovered.txt`, a SIDECAR of 3,060
boundary-recovered targets, all sized [H: source account: `config/adm-kr/arm9/overlays/ov004/recovered.txt`,
same count; direct ROM-source provenance unresolved]. The sidecar exists because dsd owns `symbols.txt` and rewrites it, so a recovered
guess cannot be mixed in [H: source account: `tools/agent/target.py:183-215`, the "WHY A SIDECAR BESIDE
symbols.txt" note, which records the same 90 sized symbols covering 3.8% of the module; direct ROM-source provenance unresolved].
`T.load_all()` loads both, so a `func_ov004_*` name that appears only in `recovered.txt` is a
legitimate symbol-table name by `../STYLE.md` rule 2 [H: source account: `tools/agent/target.py:50-65, 224`; direct ROM-source provenance unresolved].
The kb page's "90 symbols to 3,075 targets" is the same event counted at a slightly earlier
revision [H: source account: `docs/kb/modules/ov004.md`; direct ROM-source provenance unresolved].

## Where it lives

| function or symbol | module | role | grade / citation |
|---|---|---|---|
| `FS_LoadOverlayImage` | main | copies the overlay's bytes into RAM | [S: `src/matched/FS_LoadOverlayImage.c`; source account: `port/shim/fs/ovlreloc.c` header] |
| `FS_StartOverlay` | main | decompress, authenticate, run static initialisers | [S: `src/matched/FS_StartOverlay.c`; source account: `port/shim/fs/ovlreloc.c` header] |
| `FS_EndOverlay` | main | sweep destructors whose address is in the unloaded range | [S: `src/matched/FS_EndOverlay.c`; source account: `port/shim/fs/ovlreloc.c:213-220`] |
| `FSi_CompareDigest` | main | overlay integrity check; failure is `OS_Terminate()` | [S: `src/matched/FSi_CompareDigest.c`; source account: `port/shim/fs/ovlreloc.c` header] |
| `MIi_UncompressBackward` | autoload_2 | expands a compressed overlay image | [H: source account: `port/shim/fs/ovlreloc.c:56`; direct ROM-source provenance unresolved] |
| `func_ov126_022a1228` | ov126 | the keyboard's touch dispatcher, reached only by pointer | [S: `src/matched/func_ov126_022a1228.c`; source account: cycle40 log, PROBE40] |
| `func_ov003_02226048` | ov003 | Thumb; shares its address with an `ov004` function | [H: log/source account: cycle40 log, CARD40..SND40; receipt provenance unresolved] |
| `__sinit_ov147_0229a700` | ov147 | fills the boot-machine state table at `0x0229ad4c` | [S: `src/matched/__sinit_ov147_0229a700.c`; source account: `port/shim/gfx/pmflist.c:213-217`] |

## Data it reads and writes

| address or field | meaning | who writes | who reads |
|---|---|---|---|
| overlay header `ram_address` / `ram_size` / `bss_size` | where the image lands and how much it occupies | the ROM's overlay table | `FS_StartOverlay` [S: `src/matched/FS_StartOverlay.c`; source account: `port/shim/fs/ovlreloc.c:31-41`] |
| overlay header `sinit_init` .. `sinit_init_end` | the static-initialiser array | the linker | `FS_StartOverlay`'s final walk [S: `src/matched/FS_StartOverlay.c`; source account: `port/shim/fs/ovlreloc.c` header] |
| overlay header `flag` bit 0 | image is backward-compressed | the linker | `FS_StartOverlay` [S: `src/matched/FS_StartOverlay.c`; source account: `port/shim/fs/ovlreloc.c:50`] |
| the ROM's global destructor chain | registered overlay destructors | C++ static initialisers | `FS_EndOverlay`'s `lo <= dtor < hi` sweep [S: `src/matched/FS_EndOverlay.c`; source account: `port/shim/fs/ovlreloc.c:213-220`] |
| `0x0229ad4c` | `ov147`'s boot-machine state table (first 8 words polled) | `__sinit_ov147_0229a700` | `ov147`'s state machine [S: `src/matched/__sinit_ov147_0229a700.c`; source account: `port/shim/gfx/pmflist.c:213-222`] |
| `0x022a1ff0` (`ov126` relocation slot) | holds `0x022a1229`, the keyboard touch dispatcher | `ov126`'s relocations | the keyboard [H: source account: cycle40 log, PROBE40; direct ROM-source provenance unresolved] |

## How to check it

Run the two-tap town recipe from `docs/kb/hybrid/recipes.md` section 3 and read the log for
the port's own overlay lines: `FS_StartOverlay` prints
`acww ovl: overlay N: M static initialisers run as ROM code` for the first eight overlays it
loads on the interpreter path [H: source account: `port/shim/fs/ovlreloc.c:219-231`; direct ROM-source provenance unresolved]. Frame 37,500 of that run
is the town-hall frame whose overlay set is quoted above
[E: `scratchpad/cycle40/runs/tap-D56`].

For **which frame** an overlay loaded in, and for every file read beside it, arm
`ACWW_FSTRACE=1` with a frame window (`docs/kb/hybrid/instruments-runtime.md` section 9e). It prints
one line per `FS_StartOverlay` — every call, not the first per id — and a per-frame summary of
requests, bytes and overlays; a frame with no summary line did no cartridge work at all.

To check which overlay a given address belongs to without a run, count the function symbols
whose module directory contains it: every `config/adm-kr/arm9/overlays/ovNNN/symbols.txt`
line carries `addr:0x...` and the module is the directory
[H: source account: `config/adm-kr/arm9/overlays/*/symbols.txt`; direct ROM-source provenance unresolved].

## Hypotheses

- The ten symbol-less slots (`ov000`, `ov057`-`ov064`, `ov089`) are data-only overlays —
  archives or tables rather than code [H: settled by reading their extracted images' section
  headers, or by showing no branch target in any module resolves into their address range].
- The five overlays resident at the town hall (5, 36, 54, 117, 120) are a stable set for
  outdoor town play, not a transient of that one frame [H: settled by logging every
  `FS_StartOverlay` / `FS_EndOverlay` across the 40,500-48,000 window of the town recipe].
- Overlay identifications made from literal-pool text hold for the small numbered overlays
  too, most of which have no such page [H: settled by re-running the pool-text extraction
  over all 138 symbol-bearing overlays and publishing the subject of each].

## Related

- `memory-map.md` — where the overlay band sits, and what else claims those addresses
- `boot-and-entry.md` — the filesystem bring-up that must run before the first overlay loads
- `scenes-and-channels.md` — the scene machinery that decides which overlays are wanted
- `display-objects.md` — the destructor chain an unload sweeps
