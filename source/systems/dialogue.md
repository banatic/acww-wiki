# Dialogue

**Summary.** Talking to someone is a small state machine that lives beside the NPC rather than
inside it. A five-entry table of `{enter, update}` member-function pairs is built at static
initialisation time; a talk request writes a state number into a request byte; the machine
notices the request only when it is idle, latches it, and runs that entry's `enter` once and
its `update` every frame. Which lines are spoken is decided further down, by a script bound to
the NPC at the moment the machine starts. Choice prompts and the two name keyboards are
separate screens the same conversation drives.

## What happens

The talk table is `data_021c17c4`: five 16-byte entries of `{enter, update}` POINTERS-TO-
MEMBER, filled at static-init time by `__sinit_020c4270`
[S: data_021c17c4, main, port/shim/game/w1_taxitalk.c]. Entries are member pointers, not plain
function pointers, so they are mwcc `{lo, hi}` pairs and dispatch goes through the port's one
member-pointer resolver [S: port/shim/game/memptr.c, port/shim/game/w1_taxitalk.c].

The machine's state lives in three bytes of a small object (`sm`): `f9` is the REQUEST, `f8`
the CURRENT state and `fa` a sub-state
[S: func_020146cc / func_02014688, main, port/shim/game/w1_taxitalk.c]. Idle is `f9 == 5`
[S: func_02014788, main, port/shim/game/w1_taxitalk.c]. A caller asks for a conversation by
writing a state number into `f9` -- `func_020147e0(obj + 0x618, 1, 0)` reaches
`func_02014788(sm, 1, ...)`, which requires `sm->f9 == 5` and then sets `sm->f9 = 1`
[S: func_020147e0 / func_02014788, main, port/shim/game/w1_taxitalk.c]. The request is picked
up by `func_020146cc`, whose condition is `sm->f9 < 5 && sm->f8 == 5`; it latches
`sm->f8 = sm->f9`, clears `sm->fa = 0`, and runs `gTbl[1].enter = func_02014060`
[S: func_020146cc, main, port/shim/game/w1_taxitalk.c]. Per frame,
`func_02014688` runs `gTbl[1].update = func_02013e68`, which dispatches on `sm->fa` into a
sub-table reaching `func_0201404c`
[S: func_02014688 / func_02013e68, main, port/shim/game/w1_taxitalk.c].

The bind that turns "a conversation is starting" into "this NPC says these lines" is
`func_02014718`. It requires `npc->f634 != 0`, then binds through
`func_0203ee14 -> func_02068340`, attaches the script with `func_020a8164`, takes a key from
`p->f1e`, and arms the conversation by setting `p->f40->f8 = 1`
[S: func_02014718, main, port/shim/game/w1_taxitalk.c]. `npc->f634` is set to `npc + 0x658` by
the scene's own slot 1 (`func_ov051_02261364 -> func_0201c280(self, self + 0x658)`)
[S: func_ov051_02261364, ov051, port/shim/game/w1_taxitalk.c]. So the NPC must have been given
its dialogue substructure before any request can succeed
[S: port/shim/game/w1_taxitalk.c].

There is one more gate on the NPC's side: its per-frame step `func_0201b910` calls
`func_02014688(self + 0x618, self)` only when `self->f561 != 0`, and that byte is set to 1 by
`func_0201bdb4` [S: func_0201b910 / func_0201bdb4, main, port/shim/game/w1_taxitalk.c].

The first conversation in the game -- Kapp'n in the taxi -- shows the whole chain with the
scene-side gates attached. `func_ov051_0226131c` (vtable `0x0226193c` slot 0) sets scene state
0 and writes a 41-frame countdown, `0x29`, into `self + 0x718`
[S: func_ov051_0226131c, ov051, port/shim/game/w1_taxitalk.c]. The per-frame step
`func_ov051_02261270` is `(self->*tbl[self->f654].update)()`
[S: func_ov051_02261270, ov051, port/shim/game/w1_taxitalk.c]. Scene state 0's update
`func_ov051_022611e0` requires the screen fade to have FINISHED -- `*(u8 *)0x021c75b8 == 2`,
where 0 is idle, 1 fading in and 3 fading out -- and the countdown to have expired
(`func_020e8840(self + 0x718) == 0`), and only then advances to scene state 1, whose enter
issues the talk request [S: func_ov051_022611e0, ov051, port/shim/game/w1_taxitalk.c].

Dialogue and menu widgets are built from a shared translation unit whose template is
`func_0202da38`, a nine-argument constructor; the `Self` layout carries `f100`, an array
`f104[0x1e]` and `f122`, and one of its range gates is a volatile double-read
[S: func_0202da38 / func_020224c4, main, src/matched/func_020224c4.c and
src/matched/func_0202b800.c]. `0x1e` array entries is the widget's item capacity
[S: src/matched/func_0202b800.c].

A pair of small `ov002` state functions is called from about twenty small NPC/dialogue
overlays, with 34 call sites in total -- so the per-NPC dialogue code is scattered across many
tiny overlays sharing one state helper
[S: ov002, port/shim/c6d_ov002state.c]. The scripts themselves are named in ov068's own pool:
`q10_call`, `q10_back`, `q10_wait`, `q10_door`, `q10_first`, `q10_furniture`, `q10_layout` --
the arrival sequence's question script, label by label
[S: ov068 pool words, docs/kb/modules/ov003-068.md]. Message text is stored as BMG files in
the ROM filesystem [S: port/VISIBLE-STATE.md, filesystem search returning twelve BMG files].

Kapp'n's own lines are chosen by a flag: `func_ov080_02278c88` reads the player's event flag
1 to pick his intro group `sp_etc_sequence5_2` over his ordinary `sp_npc_turtle` lines
[S: func_ov080_02278c88, ov080, port/shim/game/spnpc.c]. Dialogue selection therefore consults
the player's progress bitfield directly, not only the NPC's state
[S: port/shim/game/spnpc.c].

Observed, on the interpreter path with scripted A pulses driving the conversation
[E: docs/log/cycle40-keyboard-gate-probe.md TAP40/MENU40/LONG40/TOWN40/LONG41, runs
`tap-native`, `menu-a`, `menu-b`, `long-a`, `tap-D56`, `tap-D59`]:

- the first keyboard asks `당신 이름은?`; two taps confirm the name at about frame 7,500;
- the driver (`운전수`) then reacts to the typed name and a two-option confirmation menu
  `그렇대두! / 아니야` is shown;
- the conversation continues only when the taps STOP -- a stylus contact during the
  conversation does not advance it, and repeating taps held the confirmation menu open for
  2,300 frames;
- a five-option destination menu appears at frame 13,500:
  `바다 / 마을사무소 / 가게 / 관문 / 박물관`;
- a two-option money question follows at 16,500 (`돈 있어 / 조금밖에 없어`);
- the second keyboard asks `마을 이름은?` at about frame 24,000 and is confirmed by two taps
  at 24,600;
- in the town hall from frame 40,500, `펠리` (Pelly) talks and a choice prompt is on screen;
  she says goodbye at 60,000 and the scripted A pulses start the conversation again
  (`어머 무슨 일 있으신가요?`) through 90,000.

Two contradictions are on the record and are content rather than noise. First, the DeSmuME
reference and the port agree step for step from frame 6,000 to 24,000 (bottom-screen ncc
0.9997-1.0000) and then PART at 25,500: the port's two taps confirm the town name and the
reference's identical taps do not, leaving it on the town-name keyboard to 48,000
[O: docs/log/cycle40-keyboard-gate-probe.md ORACLE41, `scratchpad/oracle/tap-fullpad`]
[E: `tap-D56`]. Settled (ORACLE42): the tap at 24,600 lands on a KEYS3 A-press frame
(2400 + 37 x 600), and the reference's stylus sample reaches the game 1-2 frames after the
port's does, so the two order the press and the tap differently; with the tap at 24,700
both confirm and agree (11 frames 24000..27000, ncc 0.9955, top screen 1.0000)
[O: `scratchpad/oracle/tap-24700`] [E: `tap-D62`] [S: docs/log/cycle40-keyboard-gate-probe.md ORACLE42].
Whether the port should model that latency is a hypothesis below. Second, a scripted run cannot leave the town
hall -- the A pulses re-open Pelly's conversation forever -- while a person with the keyboard
can [E: docs/log/cycle40-keyboard-gate-probe.md LONG41, `tap-D59`].

The keyboards are `ov126`. Its touch dispatcher `func_ov126_022a1228` is installed only as a
function pointer, through the ov126 relocation at `0x022a1ff0` pointing at `0x022a1229`
(Thumb) [S: ov126, docs/log/cycle40-keyboard-gate-probe.md PROBE40]. Closing the keyboard is
`func_ov126_022a1a54`, which forwards its object to `func_020ee470` at `0x022a1a58` and
returns 1 [S: func_ov126_022a1a54, ov126, port/shim/game/keyboardclose.c]; the readiness test
`func_ov002_022081dc` forwards to `func_020ee550` and normalises the result to 0 or 1
[S: func_ov002_022081dc, ov002, port/shim/game/keyboardready.c].

## Where it lives

| function or symbol | module | role | grade/citation |
|---|---|---|---|
| `data_021c17c4` | main | 5 x `{enter, update}` talk table | S: port/shim/game/w1_taxitalk.c |
| `__sinit_020c4270` | main | fills that table at static-init time | S: port/shim/game/w1_taxitalk.c |
| `func_02014788` | main | accepts a talk request when `sm->f9 == 5` | S: port/shim/game/w1_taxitalk.c |
| `func_020146cc` | main | latches the request: `f8 := f9`, `fa := 0` | S: port/shim/game/w1_taxitalk.c |
| `func_02014060` | main | `gTbl[1].enter` | S: port/shim/game/w1_taxitalk.c |
| `func_02013e68` | main | `gTbl[1].update`, dispatches on `sm->fa` | S: port/shim/game/w1_taxitalk.c |
| `func_02014718` | main | binds script, key and arms the conversation | S: port/shim/game/w1_taxitalk.c |
| `func_020a8164` | main | attaches the dialogue script | S: port/shim/game/w1_taxitalk.c |
| `func_0201b910` | main | NPC per-frame step, gated on `self->f561` | S: port/shim/game/w1_taxitalk.c |
| `func_ov051_022611e0` | ov051 | taxi scene state 0: fade + countdown gates | S: port/shim/game/w1_taxitalk.c |
| `func_0202da38` | main | the nine-argument menu/dialog widget template | S: src/matched/func_0202b800.c |
| `func_ov080_02278c88` | ov080 | picks Kapp'n's intro vs ordinary line group | S: port/shim/game/spnpc.c |
| `func_ov126_022a1228` | ov126 | keyboard touch dispatcher (function pointer only) | S: docs/log/cycle40-keyboard-gate-probe.md |
| `func_ov126_022a1a54` | ov126 | keyboard close | S: port/shim/game/keyboardclose.c |

## Data it reads and writes

| address or field | meaning | who writes | who reads |
|---|---|---|---|
| `0x021c17c4` | the 5-entry talk table | `__sinit_020c4270` | `func_020146cc`, `func_02014688` |
| `sm->f9` | requested talk state; 5 = idle | `func_02014788` | `func_020146cc` |
| `sm->f8` | current talk state | `func_020146cc` | `func_020146cc` |
| `sm->fa` | sub-state index into the update sub-table | `func_020146cc` | `func_02013e68` |
| `npc->f634` | the NPC's dialogue substructure pointer | `func_ov051_02261364` | `func_02014718` |
| `npc + 0x618` | the talk machine object | scene init | `func_020147e0`, `func_02014688` |
| `npc->f561` | "this NPC may run its talk step" | `func_0201bdb4` | `func_0201b910` |
| `p->f1e` | the conversation key | `func_02014718` | script |
| `p->f40->f8` | the "armed" byte | `func_02014718` | script runner |
| `0x021c75b8` | screen fade: 0 idle, 1 in, 2 done, 3 out | fade manager | `func_ov051_022611e0` |
| `ov051 self + 0x718` | 41-frame (`0x29`) scene countdown | `func_ov051_0226131c` | `func_020e8840` |
| `0x022a1ff0` (ov126 reloc) | the keyboard's touch dispatcher pointer | overlay load | keyboard step |

All rows are S, cited from the files in the previous table.

## How to check it

`port/shim/game/w1_taxitalk.c` is a read-only probe over exactly these gates: it prints the
fade state at `0x021c75b8` with its four values named, and all five `{enter, update}` pairs of
`0x021c17c4`, on change plus a power-of-two heartbeat so silence is never ambiguous
[S: port/shim/game/w1_taxitalk.c]. That distinguishes "the table is zero" from "the table is
wrong", which is the distinction any dialogue investigation starts from
[S: port/shim/game/w1_taxitalk.c].

To reproduce the conversations, run the town recipe (see `town.md`) and read the shots at
9,000 / 13,500 / 16,500 / 24,000 / 40,500
[E: docs/log/cycle40-keyboard-gate-probe.md, `tap-D56`, `long-a`].

## Hypotheses

- The port delivers a scheduled stylus sample to `TP_POINT` the same frame; hardware's ARM7 sampling and PXI round trip add 1-2 frames. Modelling that latency in port/shim/input/touch.c would make the 24,600 recipe behave as the reference does [H: re-run `tap-D56`'s recipe after the change and compare with `scratchpad/oracle/tap-fullpad` at 25,500].

- **H: the five talk-table entries are five conversation KINDS (ordinary villager, special
  NPC, sign/board, letter, system prompt), and `sm->f9` names the kind.** The request value
  observed is 1 and idle is 5, so 0..4 are the real entries and 5 is "none"
  [S: port/shim/game/w1_taxitalk.c]. Experiment: log `sm->f9` at every accepted request over a
  town-hall run and a villager conversation and see how many distinct values appear.
- **H: `sm->fa` walks a fixed line-advance sequence (open box -> print -> wait for A ->
  close), which is why one A pulse per 600 frames carries the whole taxi conversation.**
  `func_02013e68` dispatches on `fa` [S: port/shim/game/w1_taxitalk.c]
  [E: docs/log/cycle40-keyboard-gate-probe.md MENU40]. Experiment: log `fa` per frame across
  one line of Pelly's dialogue on `tap-D59`.
- **H: a choice prompt is the same widget as a dialogue box with `f104[0x1e]` populated, and
  the answer is written back into `sm` before the script resumes.** The template is shared
  [S: src/matched/func_0202b800.c]. Experiment: instrument `func_0202da38`'s nine arguments at
  the five-option destination menu and at a plain line.
- **H: a stylus contact during a conversation is consumed as a "cancel/hold" input, which is
  why repeating taps froze the confirmation menu.** Measured behaviour, mechanism unread
  [E: docs/log/cycle40-keyboard-gate-probe.md TAP40/MENU40, `tap-D55b`, `menu-a`]. Experiment:
  instrument `func_020b755c`'s classification and `sm->fa` while a contact is held during a
  line.
- (Settled, kept for the record.) The ADC round trip was NOT the cause: `tap-D61` at 222,182
  still confirms and `scratchpad/oracle/tap-220` at 220,180 still does not. The frame was
  [S: docs/log/cycle40-keyboard-gate-probe.md ORACLE42] [E: `tap-D61`]
  [O: `scratchpad/oracle/tap-220`].
- **H: `func_020a8164` takes a script id derived from the NPC's species and personality plus
  the player's event flags, so dialogue variety is a table lookup rather than a random pick.**
  Kapp'n's group is already known to be chosen by an event flag
  [S: port/shim/game/spnpc.c]. Experiment: log `func_020a8164`'s arguments for three different
  villagers on the same day.
- **H: the `q10_*` labels are the arrival questionnaire's seven steps and map one-to-one onto
  the taxi conversation's observed beats.** Seven labels, and the observed conversation has a
  name prompt, a confirmation, a destination menu, a money question and a town-name prompt
  [S: docs/kb/modules/ov003-068.md] [E: `tap-D56`]. Experiment: instrument `func_020a8164` and
  print the label of each script the taxi conversation loads.

## Related

- `player.md` -- the event bitfield dialogue selection reads
- `villagers.md` -- the expression roll that runs alongside a line
- `town.md` -- the town hall the reference run ends in
