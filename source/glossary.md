# Glossary

Terms used across the wiki, each with the function or address that defines it.

| term | meaning | defined by |
|---|---|---|
| acre | one 32.0-unit cell of the town grid; acre objects are placed at `Translate(col*32,0,0)` composed with `RotX(row*0x2999)` | `func_ov003_0221f270` (ov003); `data_020ca0ec` |
| acre map | the block of acre bytes inside the save image | save `+0xd304` = `0x021e9aac` |
| actor manager | the eight `{actor, id}` slots holding the villager actors currently on screen | `0x021d1d4c`; registered by `func_0202e1fc` |
| arrival flag | player event flag 1: set for the whole opening sequence, cleared when it ends | `func_02084af0`; cleared by `func_ov050_02262628`, `func_ov068_0226e948` |
| category nibble | the top four bits of a 16-bit item id; the placement gate accepts 3 and 4 | `func_0204bcdc` (main) |
| channel | the game's unit of live object: a numbered handler dispatched from the handler table. Two front doors reach it -- `func_0202f134` for a scene's channel list and `func_02003348` for the special-NPC scheduler's staged visitor -- both ending in `func_020edc58` | `func_020edc58`; table pointer `0x021fd044`; `wiki/engine/scenes-and-channels.md`, `wiki/systems/events-and-calendar.md` |
| day-change routine | the once-per-rollover calendar update: seventeen calls and five `MI_CpuCopy8` blocks over one global | `func_02040c90` (main); `0x021c7584` |
| empty item id | `0xfff1`, the "no item / no tile" sentinel stamped across the map by the reset | `func_020a13e8` (main) |
| event bitfield | the player's 64 progress bits | `player + 0x23f8`; `func_02099020` / `func_02098ff8` |
| fade state | `0` idle, `1` fading in, `2` finished, `3` fading out -- a gate on scene advance | `0x021c75b8`; read by `func_ov051_022611e0` |
| field object | the outdoor scene's root; its `+0x50` is published as the field-data pointer, and weather hangs at `+0x2d0` | `func_02034d14` (vtable `0x020da334`); `0x021c526c` |
| house record | one of eight `0x7ec`-byte save records holding a villager and their house; villager sub-record at `+0x7a0` | save `+0x9284` = `0x021e5a2c` |
| house plot | item id `0x500a`, a spot the placer converts into `0x5001`..`0x5008` | `func_0207bbb8` (main) |
| indoor/outdoor byte | non-zero takes the interior branch; blocks special-NPC staging | `data_020e54a8`; `func_02085558` |
| interpreter path | the hybrid runtime in which the ROM's own ARM/Thumb code is executed in process (`ACWW_INTERP=1`) | `port/interp/interp_cpu.c`; `docs/HYBRID-PLAN.md` |
| keyboard | the `ov126` name-entry screen; its touch dispatcher exists only as a function-pointer word | `func_ov126_022a1228` (ov126); reloc `0x022a1ff0` |
| light table | the day/night colour table every lit vertex ultimately samples | `0x021f6cf0`; filled by `func_020bbf0c` |
| oracle | the DeSmuME reference the port is compared against under the same recipe | `port/tools/oracle/` |
| PMF | a CodeWarrior pointer-to-member function, stored as an 8-byte `{lo, hi}` pair | `port/shim/game/memptr.c`; e.g. villager draw at `obj + 0x8b0` |
| player slot | one of four `0x249c`-byte player records in the save image | save `+0x14` = `0x021dc7bc`; stride from `func_02098844` |
| save image | the `0x173fc`-byte in-RAM copy of the save | `0x021dc7a8`; written by `func_020b5724` |
| scene | a numbered stage of the boot/game sequence requested through the scene machinery | `func_020a53ec`; pending word `0x020e3c80` |
| season | 0 spring, 1 summer, 2 autumn, 3 winter, from month and day | `func_02063bb4` (main) |
| season/event index | a fourteen-value month map in which August and September each split in two | `func_0204fa8c` (main) |
| sky row | the row of the day/night table selected by season and weather | `0x021f8ad4` -> `table_020d2364`; used by `func_020bba14` |
| special-NPC table | twenty-three rows of `{channel, actor, overlay, pmf, flag}`, one per scheduled visitor | `data_020e1d8c` (main) |
| talk machine | the five-entry `{enter, update}` table and the `f8`/`f9`/`fa` state bytes that drive a conversation | `data_021c17c4`; `func_020146cc` |
| tile | 2.0 world units; a 3-byte record found through a group/index split of the tile word | `func_ov003_022273f8` (ov003); descriptors at `0x02236b0c` |
| town dispatcher | the handler set that generates, resets and syncs the town | `func_0209e6ec` (main) |
| villager class | one of six personality groups the initial pick draws from | `func_0207c818` (main); bound at 6 in `func_0207c76c` |
| arena | the OS's free main-RAM span, `OS_GetArenaLo(0)`..`OS_GetArenaHi(0)`; the game heap is carved from its low end | `func_020ea48c`; ceiling `0x023e0000`, the port raises it to `0x023f0000` (`port/shim/os/arenahi.c`) |
| BMG | `MESGbmg1`, the message container: `INF1` records plus a `DAT1` UTF-16 payload; 1,791 loose `.bmg` files under `script/KOR/` | `extract/adm-kr/files/script/KOR/message/Other/test_.bmg`; `wiki/data/archives.md` |
| deny list | the 49 shim basenames `interp_registry.py` refuses to register, so the ROM's own bodies run for them on the interpreter path | `port/tools/interp_registry.py`, `DENY_FILES` (plus `DENY_FUNCS = {func_020b1b84}`) |
| display object | a C++ object owning two list nodes, joined to the four global lists and stepped once a frame through vtable slots | `func_020ee834`; heads `0x021fd004`/`14`/`24`/`34`; `wiki/engine/display-objects.md` |
| game heap | the NNS expanded heap built at the arena block + 0x30 that every game object is allocated from | `func_020ea50c`; pool words `0x021fbe78`/`8c`/`94` |
| NARC | the `BTAF`/`BTNF`/`GMIF` archive the game mounts as an `FSArchive` and reads members from by `archive:path` | `NNS_FndMountArchive` (autoload_2 `0x0210288c`); `src/matched/NNS_FndMountArchive.c` |
| OFF recipe | the control run: keyed START (`ACWW_KEYS=9` from frame 300) with the stylus disabled, 31 shots to frame 9,000 compared by SHA-256 | `wiki/experiments/off-recipe.md`; `docs/kb/hybrid/recipes.md` section 2 |
| PXI tag | the numbered channel on the ARM9-ARM7 FIFO: 4 NVRAM, 5 RTC, 6 touch, 7 sound, 8 power, 10 wireless, 11/14 card | callback table `0x027e0394 + tag*4`; `PXI_SetFifoRecvCallback` (autoload_2) |
| step gate | the six-instruction test every per-frame display-object step is behind: `+0x0f` clear AND bit 1 of `+0x13` clear | `func_01ffd41c` (itcm); `port/shim/gfx/dispgate.c` |
| town recipe | the two-tap run from the title screen to the town hall, 48,000 frames; the run every town, sky and keyboard observation is taken under | `wiki/experiments/two-tap-town-recipe.md`; `docs/kb/hybrid/recipes.md` section 3 |
| TP_POINT | the ROM's own published touch point, `{x, y, touch, validity}`; `0xffff, 0xffff` is no touch | `0x021fbde8`, written by `func_020e9314` (autoload_2), read by `func_020b9280` |
| VBlank task list | the second, separate list the ROM walks inside the vertical blank, each task run through vtable slot 0 | head `0x021f6ca0`; walked by `func_020b98ec` (main) |
| walk mode | the global that says which display list is being walked; mode 3 defers a commit onto the update list | `0x0213e7fc`; read by `func_020ee59c` |
