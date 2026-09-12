# Engine

How the program is put together. Each page is written to `../STYLE.md`.

Written:

- [`boot-and-entry.md`](boot-and-entry.md) -- Entry, hardware bring-up, static initialisers,
  NitroMain, the main loop, what a frame is
- [`overlays.md`](overlays.md) -- the 148 overlay slots: which overlay carries which feature,
  load and unload, residency, why addresses are ambiguous
- [`scenes-and-channels.md`](scenes-and-channels.md) -- the scene machine, scene 6's six-stage
  loader, channel opens, the double-indirect handler table, the mailbox and the mode byte
- [`display-objects.md`](display-objects.md) -- the display-object framework: the four lists,
  the four steppers and their three-slot pattern, join/commit/step, VBlank tasks
- [`display-callbacks.md`](display-callbacks.md) -- the one list three walkers run over: the
  node's live and staged handler pairs, the commit rule, and the two engine arms (sub and main)
  that decide which twin of each handler is installed
- [`memory-map.md`](memory-map.md) -- main RAM, ITCM/DTCM, the module bands, the arena, the
  game heap, the global address bands
- [`threads-and-interrupts.md`](threads-and-interrupts.md) -- OSContext and the cooperative
  scheduler, the threads that exist, the interrupt table, the PXI tags

- [`file-system.md`](file-system.md) -- the ROM file system, overlay table, archives, how
  files are opened
- [`text-and-messages.md`](text-and-messages.md) -- the message system (bmg), fonts, the
  keyboard screens
- [`graphics-pipeline.md`](graphics-pipeline.md) -- 2D engines, 3D geometry submission, VRAM
  banks, the display lists, and what the port's own renderer does and costs (PERF42, RENDER42)
- [`interpreter-path.md`](interpreter-path.md) -- the hybrid runtime (`ACWW_INTERP=1`), the deny
  list, and the differential check by which a native body earns the hot path (phase H5)
- [`time-budgets.md`](time-budgets.md) -- all 32 millisecond literals: loader budgets, network timers and alarm conversions
