# The online server: architecture and threat model

**Read this when** you change anything under `server/`, or when you are deciding whether
something belongs on the server at all. The byte-level contract is
`docs/kb/hybrid/online-spec.md`; the endpoint table as implemented, with every open
question this unit had to resolve, is `server/API.md`; the operator's Korean instructions
are `server/README-ko.md`. This page is the shape and the risk.

Built by SERVER79, 2026-09-11, on main at `31f028ee`.

## What it is

One Python process behind the NAS's reverse proxy. FastAPI on uvicorn, one port, one
SQLite file, a directory of 256 KB save images. It does four things and deliberately not a
fifth:

| concern | where it lives | why there |
|---|---|---|
| accounts | `app/security.py`, `users` table | argon2id, HS256 tokens; no session state to lose |
| cloud saves | `app/store.py`, `/data/saves/<user>/<version>.sav` | files, not blobs -- a backup is a file copy and a corrupt row cannot eat a town |
| save validation | `app/savecheck.py` | the ROM's own acceptance test, ported from `port/tools/savetool.py` |
| the lobby | `app/lobby.py`, in memory | a lobby that survived a restart is a list of people who are not there |
| the relay | `app/main.py` `/v1/relay/{room}` | two sockets and a `send_bytes`; the server never parses a frame |

**TLS is not here.** The service speaks plain HTTP on 8080 and the NAS's reverse proxy
terminates HTTPS in front of it. That is one fewer certificate lifecycle in a program that
is otherwise stateless about the network, and Synology already renews the certificate.

**The game is not here either.** The image is `python:3.12-slim`, six pinned wheels and the
`app` package. `.dockerignore` keeps `tests/` -- and therefore the sample save -- out of
the build context. The only game-derived thing on the server is five constants and an
addition in `savecheck.py`.

## The shapes of the two sockets

The lobby socket is a broadcast list plus point-to-point invites. A client says `wait`;
every connected socket is pushed `{"t":"list","users":[...]}` on every change. An `invite`
reaches one person, an `accept` creates a **room** and both sides get
`{"t":"matched","room":id,"peer":{...},"role":"parent"|"child"}`.

The relay socket is the room. Binary frames are forwarded verbatim to exactly one peer;
text is only the `ping`/`pong` keep-alive; when either side goes, the survivor gets
`{"t":"peer_left"}` and the room is freed. The frame layout
`[u8 kind][u8 port][u16 len][payload]` belongs to the WM bridge on both ends
(`wiki/systems/wifi-port-plan.md` section A), and the server's ignorance of it is the
design: a change to the bridge must not be a server deployment. The test suite pins this
by forwarding a frame whose declared `len` disagrees with its payload.

**The role is the WM role.** `parent` beacons and assigns AIDs, so `parent` is the host
("inviting") and `child` the guest ("visiting"). It comes from the declared modes; when
both peers declared the same one -- which the client should prevent and the server must not
trust -- the inviter is the parent, because the invite is the thing that actually happened.

## The save is validated, and that is the interesting part

A cloud save that the server accepted but the game cannot open is the worst failure this
service has, because the owner discovers it at the title screen with the good local copy
already replaced. So `PUT /v1/save` runs the ROM's own acceptance test -- `func_020a1a40`,
transcribed in `port/shim/game/savepoll.c` -- and refuses with 400 and the reason:

* the gamecode byte `+0x0000` must be `0x32` (`func_0209f180`),
* the flag byte `+0x173fa` must be `2` (`func_0209fb3c`),
* the 16-bit wrapping sum of the whole `0x173fc`-byte bank must be `0` (`func_02050920`),

on **both** banks, because the game mirrors bank 1 into bank 2 after every save and one
good bank is an interrupted write. The three are independent and are reported separately:
a bank can carry a perfect checksum and still be rejected for the flag. See
`docs/kb/hybrid/save-flow.md`.

Concurrency is `If-Match` over a per-user version counter, checked again inside the store's
lock: two PCs flushing the same town cannot both believe they won, and the loser is told
to re-read rather than silently overwritten.

## Threat model

The owner's household on the open internet. Not a public service, not a game-preservation
server, not a place anyone else's towns live.

| who | what they can try | what stops them |
|---|---|---|
| a stranger who finds the domain | register an account | `ACWW_ALLOW_REGISTER=0` once the household's accounts exist; this is the main control and the README says so twice |
| a stranger with a password list | guess the owner's password | argon2id (slow by construction) + 10 auth attempts / minute / IP; `ACWW_TRUST_PROXY=1` so the limit is per real client, not per proxy |
| a stranger with a stolen token | read or overwrite that account's town | nothing beyond the token -- this is the accepted risk; the blunt revoke is rotating `ACWW_SERVER_SECRET`, which invalidates every token at once |
| a logged-in user | read another user's save | every save path is keyed by the token's `sub`; there is no endpoint that takes a user id |
| a logged-in user | join a room they were not matched into | membership is the room's two ids, checked before `accept()`; a third party is closed 1008 |
| a logged-in user | store a town that will not load | the ROM's three-part test, both banks, 400 with the reason |
| a logged-in user | spoof their way out of the rate limit | `X-Forwarded-For` is honoured **only** when `ACWW_TRUST_PROXY=1`, so a directly exposed server cannot be talked around with an invented header |
| someone reading the logs | learn a password, a token or a town | one-line JSON with an explicit forbidden-field list; a save appears only as a length and a sha256 |
| someone who gets the image | find a secret or game data | the secret is env or `/data`, never in the image; `tests/` and every `.sav` are excluded from the build context |

**What is deliberately NOT defended.** The client is an unsigned executable, so the server
cannot know that the thing holding a token is really the game -- a user can upload any
262,144 bytes that pass the ROM's test, including a hand-edited town. That is the owner's
own save file on the owner's own server; defending it would mean signing the client, which
buys nothing here. There is also no token revocation list and no refresh: a stolen token is
good until it expires or the secret is rotated.

## Where the state is, and what a restart costs

| state | lives in | survives a restart |
|---|---|---|
| accounts | `/data/acww.sqlite` | yes |
| save versions (last 20) | `/data/saves/...` + a row each | yes |
| the generated signing key | `/data/secret.key` (0600) | yes, if `/data` is in the backup |
| who is waiting in the lobby | memory | no, and should not |
| open rooms and their sockets | memory | no; both peers reconnect and re-invite |

The rate limiter is per process, which is correct for a one-container deployment and would
have to move if this were ever run as more than one replica. It is not.

## Open, ranked

1. The standalone client half of the spec -- `acww-online.ini`, the login dialog, the lobby
   window, and handing the relay socket to the WM bridge -- does not exist yet. The server
   has never talked to the game, only to its own tests and `server/tools/smoke.py`.
2. The relay has never carried a real WM frame, because the WM bridge does not emit one yet
   (`wiki/systems/wifi-g0.md`: the port submits zero WM requests to its stubbed ARM7). The
   frame contract is implemented as a pipe and proven only as a pipe.
3. No restart test with a populated volume: the container was smoked once from an empty
   `/data`. Upgrade-in-place is untested.
4. `GET /v1/save` streams the whole 256 KB into memory. Fine at this size and at this user
   count; it is the first thing to change if either grows.

## The client met it (INTEGRATE83, 2026-09-11)

MEASURED, on main at `1f6a2e36`. `port/tools/test_online_integration.py` builds this image,
runs it on 127.0.0.1:18080 with a FRESH volume and drives `dist/acww.exe` against it: two
accounts registered through the game's own login window, a save round trip, a 412 forced by
writing a version behind the client's back, an offline launch, two standalone processes
meeting in the lobby, and the whole of it again through an nginx TLS reverse proxy. Seven
steps, all passing; receipts in `scratchpad/integrate83/`.

**Six disagreements were found and NOT ONE of them was fixed here.** The list and the
reasoning are in `docs/kb/hybrid/online-spec.md`'s "The two halves met" section; what matters
on this page is that the server's five contested choices all stood:

* `{"t":"list","users":[...]}` -- the client now reads `users` and the spec says `users`.
* An integer `user_id` and a type check on `invite.to` / `accept.from` / `decline.from`. The
  client was quoting ids; refusing them was right, and the error message was the only thing
  that made it findable -- **keep that message specific.**
* `PUT /v1/save` answering 400 for a card image the ROM would refuse. A fresh account's first
  launch used to send one every session; the client now runs the same test before the PUT.
* `{"t":"peer_left"}` and the 1000 close to the survivor. The client had no branch for either.
* The relay forwarding-or-dropping with no buffer. The client's one-shot probe raced the
  peer's connect and lost; the INSTRUMENT was changed, not the relay.

Two things this run says about operating it:

* **The structured events are the integration evidence.** `auth.login`, `save.put` (with
  `if_match`), `save.stale`, `save.rejected`, `lobby.matched` (with `parent` / `child`) and
  `relay.close` (with `frames_forwarded`) are what the fixture asserts on; uvicorn's access
  lines are not enough. Do not make them quieter.
* **`docker logs` returns stdout and stderr as two blocks, not interleaved.** The JSON events
  are on stdout, uvicorn's access log on stderr. Anything reading "the log since a moment ago"
  has to mark the two separately.

### The reverse proxy, measured

The deployment this page assumes -- "TLS is the NAS reverse proxy's job" -- now has a config
that is known to carry the websockets, in `scratchpad/integrate83/tls/acww.conf` and inline in
the fixture. The three lines that decide it are `proxy_http_version 1.1`, the
`Upgrade`/`Connection` pair (with the `map $http_upgrade $connection_upgrade`, because a
constant `Connection: upgrade` breaks every ordinary request) and a `proxy_read_timeout` long
enough for an idle lobby socket. Get them wrong and the cloud save keeps working while the
lobby silently does not, which is the worst shape this service can fail in.

`ACWW_TRUST_PROXY=1` still matters behind a proxy or the rate limiter sees one client.
