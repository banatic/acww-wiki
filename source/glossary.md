# Glossary

Terms used across the wiki, each with the function or address that defines it.

| term | meaning | defined by |
|---|---|---|
| acre | one 32.0-unit cell of the town grid; acre objects are placed at `Translate(col*32,0,0)` composed with `RotX(row*0x2999)` | `func_ov003_0221f270` (ov003); `data_020ca0ec` |
| acre map | the block of acre bytes inside the save image | save `+0xd304` = `0x021e9aac` |
| actor manager | the eight `{actor, id}` slots holding the villager actors currently on screen | `0x021d1d4c`; registered by `func_0202e1fc` |
| arrival flag | player event flag 1: set for the whole opening sequence, cleared when it ends | `func_02084af0`; cleared by `func_ov050_02262628`, `func_ov068_0226e948` |
| arrival step | the stage of the move-in sequence the player has reached. It gates two things measured separately: the tutorial illustration that discards the pad, and whether villagers are drawn. The **move-in mode** word is the part of it the save prompt reads | `0x021f3c30`; `wiki/systems/villagers.md`, `wiki/systems/save-data.md` |
| category nibble | the top four bits of a 16-bit item id; the placement gate accepts 3 and 4 | `func_0204bcdc` (main) |
| card page | the 256-byte unit every backup transfer is chopped into by `CARDi_RequestStreamCommandCore`. A whole save is 744 of them; `func_020a1d94`'s 512-byte step is two | `src/matched/CARDi_RequestStreamCommandCore.c`; `wiki/systems/save-data.md` |
| capture unit | one of the DS's two sound capture units, which write the mixer (or a channel) back into main RAM. ACWW arms both, aimed at the same two buffers replay channels 1 and 3 read from, which is how its pseudo-surround works | `SETUP_CAPTURE` (command id 17); `port/shim/audio/capture.c`; `wiki/systems/audio.md` |
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
| move-in mode | the word the save prompt reads: 1 or 2 refuses (`sp_etc_sequence4` message 4), 0 allows the real save menu. Written non-zero by ov147's move-in steps and back to 0 by `func_020a128c` when the arrival finishes -- ten accessors in all | `0x021f3c30`; `func_0209f6e4`, `func_020a128c`; `wiki/systems/save-data.md` |
| oracle | the DeSmuME reference the port is compared against under the same recipe | `port/tools/oracle/` |
| output selector | `SOUNDCNT`'s choice of what each speaker hears: the mixer, or channel 1/3 directly. ACWW sends `OUTPUT_SELECTOR 1 2 1 1` -- left from Ch1, right from Ch3, both bypassing the mixer -- so the speakers hear the capture path's copy one buffer late | command id 25; `port/shim/audio/capture.c`; `wiki/systems/audio.md` |
| PMF | a CodeWarrior pointer-to-member function, stored as an 8-byte `{lo, hi}` pair | `port/shim/game/memptr.c`; e.g. villager draw at `obj + 0x8b0` |
| pad script | a timeline file `ACWW_PADSCRIPT` reads: one row per line, `<frame> <mask> <frames>` for the pad and `<frame> T <x> <y> <frames>` for the stylus. Overlapping pad rows OR together; the first matching stylus row wins. It owns the pad from frame 0, so a boot run must rebuild the boot key phases as rows | `port/platform/hostinput.c`; `docs/kb/hybrid/recipes.md` 4b; `wiki/experiments/gameplay-walkthrough.md`. The oracle takes the same file (`--padscript`) |
| pacer | the frame limiter that holds the port to the NDS's own 59.8261 Hz (33.513982 MHz / 560190 cycles). OFF by default on anything scripted -- any `ACWW_KEYS*`/`ACWW_TOUCH*`/`ACWW_SHOT*` variable or `ACWW_STOP_FRAME` -- and it re-bases rather than sprints when more than two frames behind | `port/platform/frame.c`; `ACWW_PACE`/`ACWW_NOPACE`; `wiki/experiments/live-play.md` |
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
| deny list | the 51 shim basenames `interp_registry.py` refuses to register, so the ROM's own bodies run for them on the interpreter path (49 until TOUCH41 added `touch.c`; 51 since RTC42 added `rtcclock.c`, taking the registry 93 -> 90) | `port/tools/interp_registry.py`, `DENY_FILES` (plus `DENY_FUNCS = {func_020b1b84}`), counted at `2e579f09` |
| differential check | the per-function promotion test: record the calls a real run makes, replay each twice from the SAME pre-call pages -- once through the interpreter, once through the native body -- and compare the return and the final-state write set. Agreement is evidence for the RECORDED calls only | `port/tools/promote.py`, `port/interp/interp_record.c`; `wiki/engine/interpreter-path.md`; `docs/kb/hybrid/promotion.md` |
| display object | a C++ object owning two list nodes, joined to the four global lists and stepped once a frame through vtable slots | `func_020ee834`; heads `0x021fd004`/`14`/`24`/`34`; `wiki/engine/display-objects.md` |
| game heap | the NNS expanded heap built at the arena block + 0x30 that every game object is allocated from | `func_020ea50c`; pool words `0x021fbe78`/`8c`/`94` |
| NARC | the `BTAF`/`BTNF`/`GMIF` archive the game mounts as an `FSArchive` and reads members from by `archive:path` | `NNS_FndMountArchive` (autoload_2 `0x0210288c`); `src/matched/NNS_FndMountArchive.c` |
| OFF recipe | the control run: keyed START (`ACWW_KEYS=9` from frame 300) with the stylus disabled, 31 shots to frame 9,000 compared by SHA-256 | `wiki/experiments/off-recipe.md`; `docs/kb/hybrid/recipes.md` section 2 |
| promotion | putting a `src/matched/` body back on the hot path in place of the ROM's bytes (hybrid plan phase H5). A promotion is not a registration: agreeing says nothing about whether the function should be host code | `port/tools/promote_record.py`; `docs/kb/hybrid/promotion.md`; `wiki/engine/interpreter-path.md` |
| PXI tag | the numbered channel on the ARM9-ARM7 FIFO: 4 NVRAM, 5 RTC, 6 touch, 7 sound, 8 power, 10 wireless, 11/14 card | callback table `0x027e0394 + tag*4`; `PXI_SetFifoRecvCallback` (autoload_2) |
| sampling ring | `gAutoData`, the nine-entry `TPData` ring the ARM7 fills at four samples a frame; the game's per-frame publish reads its last four entries | `0x021fbdf0`; installed by `func_020e948c` via `TP_RequestAutoSamplingStartAsync(0, 4, &gAutoData, 9)`; `wiki/experiments/touch-latency.md` |
| savestate | a snapshot of a run at one frame: the seven mapped NDS regions (4 KB pages, zero bitmap), the named host blobs (113 at SAVE41, **118 from 20 registrars** since RTC42 added the clock), and one interpreter register file per live thread, with a header that pins the link and refuses another build | `port/platform/state.c`; `ACWW_STATE_SAVE` / `ACWW_STATE_LOAD`; `wiki/experiments/savestate-resume.md`; `docs/kb/hybrid/savestate.md` |
| step gate | the six-instruction test every per-frame display-object step is behind: `+0x0f` clear AND bit 1 of `+0x13` clear | `func_01ffd41c` (itcm); `port/shim/gfx/dispgate.c` |
| town recipe | the two-tap run from the title screen to the town hall, 48,000 frames; the run every town, sky and keyboard observation is taken under | `wiki/experiments/two-tap-town-recipe.md`; `docs/kb/hybrid/recipes.md` section 3 |
| TP_POINT | the ROM's own published touch point, `{x, y, touch, validity}`; no touched sample publishes x=y=`0x00ff` [S: `func_020e9314`, autoload_2, `config/adm-kr/arm9/autoload_2/symbols.txt`; `docs/log/cycle40-keyboard-gate-probe.md` TOUCH41] | `0x021fbde8`, written by `func_020e9314` (autoload_2), read by `func_020b9280` |
| validity | the fourth halfword of a `TPData`: an ERROR CODE, so **0 means the sample is good**. 3 is `TP_VALIDITY_INVALID_XY`, which is what the ARM7 writes with x=y=0 when the pen is up | `TP_GetCalibratedPoint`, autoload_2; NitroSDK `include/nitro/spi/ARM9/tp.h`; `wiki/systems/input-and-touch.md` |
| VBlank task list | the second, separate list the ROM walks inside the vertical blank, each task run through vtable slot 0 | head `0x021f6ca0`; walked by `func_020b98ec` (main) |
| walk mode | the global that says which display list is being walked; mode 3 defers a commit onto the update list | `0x0213e7fc`; read by `func_020ee59c` |
