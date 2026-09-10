# Network

**Summary.** Wild World has two entirely separate networking stacks. Local wireless -- two DS
consoles in the same room -- stops at the wireless manager and its connection manager and never
touches an IP address. Nintendo Wi-Fi Connection goes through a full TCP/IP stack, TLS, and
GameSpy's matchmaking servers, all packed into one overlay, `ov065`. The service those servers
provided was shut down in 2014, so nothing in the second stack can work as shipped. The PC port
stubs all of it, deliberately and completely: the DS with its radio switched off.

## What happens

### The two stacks

Local wireless is `WM_*` over `WCM*`. The wireless manager owns the radio and the MAC layer:
parent and child roles (`WM_SetParentParameter`, `WM_StartConnectEx`), MP data ports
(`WM_StartMPEx`, `WM_SetMPDataToPortEx`, `WM_ReadMPData`), DCF transfers, data sharing, key
sharing, beacon scanning and WEP [S: 44 `WM_*` files, NitroWiFi, `src/matched/WM_Init.c` and
siblings]. `WCM*`/`Wcm*` is the connection manager that sits above it and, through
`WCMi_CpsifRecvCallback`, is also the bridge into the IP stack when there is one
[S: 21 files, libwcm, `src/matched/WCMi_CpsifRecvCallback.c`]. A purely local session never
needs anything above this line.

Wi-Fi Connection adds three more layers on top. `SOC*`/`SOCL*` is libsoc, a BSD-style socket
API with its own ARM7 command pipe -- `SOCL_Startup`, `SOCL_CreateSocket`, `SOCL_Bind`,
`SOCL_Connect`, `SOCL_ReadFrom`, `SOCL_WriteTo`, plus a DHCP timeout path
[S: 77 files, libsoc, `src/matched/SOCL_Startup.c` and siblings]. `CPS*`/`CPSi_*` is libcps and
libssl from Ubiquitous Corporation: the actual TCP/IP and ARP and DHCP, plus TLS with RC4, MD5,
SHA-1 and a bignum library for the key exchange
[S: 42 files, `src/matched/CPS_TcpConnect.c`, `src/matched/CPSi_rc4_crypt.c`,
`src/matched/CPSi_sha1_calc.c`]. `DWC*`/`DWCi_*` is NitroDWC on top of that: accounts, friend
codes, matching, transport and the HTTP posts to Nintendo's authentication host
[S: 119 files, `src/matched/DWC_GetState.c` and siblings].

### What ov065 actually is

`ov065` is not one library. It is four vendored components linked into one overlay: Nintendo's
libsoc and libwcm ship as real C; Ubiquitous's libcps and libssl and Nintendo's libdwcac and
libdwcbase ship as binary-only archives [S: `docs/kb/modules/ov065.md`]. The overlay runs from
about `0x02269618` to about `0x02292xxx`, and inside it the NitroDWC/GameSpy block from
`0x0227c038` to `0x022929f0` -- 92,600 bytes -- was unbounded rodata and code from which 706
function boundaries had to be recovered [S: `docs/kb/modules/ov065.md`]. The auth block
(`dwc_auth.c`, `dwc_netcheck.c`) sits at `0x02274798`..`0x02277000`, the access-connect block at
`0x02272400`..`0x02273000`, and libdwcbase proper at `0x02277000`..`0x0227bxxx`
[S: `docs/kb/modules/ov065.md`].

The GameSpy revision is pinned rather than guessed: GameSpy SDK 0.01, bundled inside NitroDWC
0pr2, matched 133 functions byte-verbatim with the DWARF line tables lining up statement for
statement [S: `docs/kb/modules/ov065-dwc.md`]. A narrow range, `0x02269618`..`0x0226e434` --
four functions of libcps/libssl -- was built with a later CodeWarrior drop (1.2/sp2p3) than the
rest of the overlay (1.2/base), which is a fact about how the ROM was assembled
[S: `docs/kb/modules/ov065.md`].

The reason so much of a binary-only overlay is understood at all is that the archives shipped
with full DWARF-2 debug information: 352 of 508 members carry it, giving struct layouts,
signatures, per-local register attribution and line tables
[S: `docs/kb/modules/ov065.md`]. Concrete constants recovered that way include
`WCM_PHASE_DCF == 9`, `DWC_ERROR_FATAL == 8` and `DWC_MAX_PLAYER_NAME == 16`, and the field
offsets of `DWCMatchControl` for the friend list, the friend index list and the evaluation
callback [S: `docs/kb/modules/ov065-dwc.md`].

### Friend codes and the login flow

A friend code is validated through `DWC_CheckFriendKey` and `DWC_Acc_CheckFriendKey`, and the
account object it belongs to is reached through the `DWCi_Acc_*` accessors -- flags, friend key,
user id, a dirty bit and a mask setter [S: `src/matched/DWC_CheckFriendKey.c`,
`src/matched/DWCi_Acc_GetFriendKey.c`]. Whether the list may be changed at all is a separate
gate, `DWC_CanChangeFriendList` [S: `src/matched/DWC_CanChangeFriendList.c`]. The login itself
posts `acctcreate` or `login` with a `gsbrcd` and a MAC address to `nas.nintendowifi.net/ac`,
and the request carries a `devtime` field formatted from the RTC as twelve digits
[S: `docs/kb/modules/ov065-dwc.md`; `func_ov065_02274798` (`DWC_Auth_Prepare_FirstPost`),
ov065, `src/matched/func_ov065_02274798.c`]. That function returns `DWCAUTH_E_RTCERR` if the
clock read fails, which makes the real-time clock a hard dependency of ever logging in
[S: `src/matched/func_ov065_02274798.c`].

A surprising share of the `DWCi_*` inventory is not protocol at all. `DWCi_KB*`, `DWCi_BTN*`,
`DWCi_MOV*`, `DWCi_FNT*`, `DWCi_IPT*`, `DWCi_OBJ*` and `DWCi_GX*` are the on-screen keyboard,
buttons, scene widgets, fonts, input repeat and OAM glue of the Wi-Fi settings and connection-
check UI [S: `src/matched/DWCi_KBlGet.c`, `src/matched/DWCi_BTNlEnable.c`,
`src/matched/DWCi_FNTlRenewBg.c`]. The core connection-state functions the module notes name
in prose -- `DWC_ProcessInet`, `DWC_GetInetStatus`, `DWCi_TransportProcess`, `DWCi_MatchInit`,
`DWCi_Netcheck_Thread` -- are matched but still filed under anonymous `func_ov065_*` names
[S: `docs/kb/modules/ov065-dwc.md`].

### What the port does

Nothing runs. `port/DESIGN.md` section 4 states the policy: 164 of 883 entry points, 19%, are
wireless (`WM`, `MB`, `AOSS`, `CPS`, `WXC`, `DWC` and GameSpy), Nintendo WFC shut down in 2014,
so v1 answers every one of them with "no service" behind an interface, and leaves that
interface as the stated modding target [S: `port/DESIGN.md` section 4].

Four small pieces are nevertheless reachable, and each is a real answer rather than a stub.
`port/shim/net/dwcinit.c` replaces `func_0210172c`, which narrows the settings-store init result
into a two-bit code, and always answers 0 -- settings valid, nothing erased
[H: host-source account from `port/shim/net/dwcinit.c`; verify with a retained scripted run and frame using this page's recipe]. `port/shim/net/dwcbackup.c` implements `DWCi_BACKUPlInit`,
`DWCi_BACKUPlRead` and `DWCi_BACKUPlWriteAll`, the store that holds SSIDs, WEP keys and DHCP
settings: a read returns an all-zero page, which is a factory-fresh console that has never been
configured, and a write is accepted and dropped [H: host-source account from `port/shim/net/dwcbackup.c`; verify with a retained scripted run and frame using this page's recipe].
`port/shim/tu_wcm_bits.c` supplies C bodies for two libwcm functions that exist only as
assembly and are on the boot path even with wireless off -- `WcmCountBits`, a popcount, and
`func_ov065_0227029c`, a count-leading-zero -- because the host compiler cannot build an mwcc
`asm` body [H: host-source account from `port/shim/tu_wcm_bits.c`; verify with a retained scripted run and frame using this page's recipe]. And `port/shim/game/ov065thunks.c` answers three
functions the *title menu* reaches through leftover vtable slots pointing into ov065's loaded
image; all three test a global function-pointer slot that the port's stubbed wireless never
fills, and decline [H: host-source account from `port/shim/game/ov065thunks.c`; verify with a retained scripted run and frame using this page's recipe].

Consistent with that, no `DWC` or `WM` symbol appears in any recorded run's log: the only
network-adjacent PXI traffic is tag 10 (WM), which the port names once and drops
[E: `port/shim/os/pxisend.c`; `docs/kb/hybrid/hardware-services.md` section 1, "Other tags"].

## Where it lives

| function or symbol | module | role | grade/citation |
|---|---|---|---|
| `WM_Init`, `WM_Initialize`, `WM_Enable`, `WM_PowerOn` | NitroWiFi (ov065) | radio bring-up and power state | [S: `src/matched/WM_Init.c`] |
| `WM_SetParentParameter`, `WM_StartConnectEx`, `WM_Disconnect` | NitroWiFi | local-wireless parent and child roles | [S: `src/matched/WM_StartConnectEx.c`] |
| `WM_StartMPEx`, `WM_SetMPDataToPortEx`, `WM_ReadMPData` | NitroWiFi | the MP data-port session used for local play | [S: `src/matched/WM_StartMPEx.c`] |
| `WM_StartScan`, `WM_MeasureChannel`, `WM_GetAllowedChannel` | NitroWiFi | beacon scan and the regulatory channel set | [S: `src/matched/WM_StartScan.c`] |
| `WM_StartDataSharing`, `WM_StartKeySharing`, `WM_StartDCF` | NitroWiFi | the three broadcast session types | [S: `src/matched/WM_StartDataSharing.c`] |
| `WM_SetWEPKey`, `WM_SetGameInfo`, `WM_GetLinkLevel` | NitroWiFi | WEP, the beacon payload, signal strength | [S: `src/matched/WM_SetWEPKey.c`] |
| `WCM_BeginSearchAsync`, `WCM_SearchAsync`, `WcmSetPhase` | libwcm | asynchronous AP search and the phase state machine | [S: `src/matched/WCM_BeginSearchAsync.c`] |
| `WCMi_CpsifRecvCallback` | libwcm | the bridge from libwcm up into libcps | [S: `src/matched/WCMi_CpsifRecvCallback.c`] |
| `WcmCountBits`, `WcmNotify`, `WcmWmReset` | libwcm | popcount, event notification, `WM_*` reset glue | [S: `src/matched/WcmCountBits.c`] |
| `SOCL_Startup`, `SOCL_CreateSocket`, `SOCL_Bind`, `SOCL_Connect` | libsoc | the socket API | [S: `src/matched/SOCL_Startup.c`] |
| `SOCLi_ExecCommandPacket`, `SOCLi_SendCommandPacket`, `SOCLi_DhcpTimeout` | libsoc | the ARM7 command pipe and DHCP timeout | [S: `src/matched/SOCLi_ExecCommandPacket.c`] |
| `CPS_TcpConnect`, `CPS_SocRead`, `CPS_SocWrite`, `CPS_SetUdpCallback` | libcps | TCP and UDP over the vendor IP stack | [S: `src/matched/CPS_TcpConnect.c`] |
| `CPSi_SslConnect`, `CPSi_SslRead`, `CPSi_SslWrite2` | libssl | the TLS session | [S: `src/matched/CPSi_SslConnect.c`] |
| `CPSi_rc4_crypt`, `CPSi_md5_calc`, `CPSi_sha1_calc`, `CPSi_big_add_part` | libssl | RC4, MD5, SHA-1 and the bignum layer | [S: `src/matched/CPSi_rc4_crypt.c`] |
| `DWC_GetState`, `DWC_GetLastError`, `DWC_GetMyAID`, `DWC_Alloc` | libdwcbase | connection state, error, association id, heap | [S: `src/matched/DWC_GetState.c`] |
| `DWC_CheckFriendKey`, `DWC_Acc_CheckFriendKey`, `DWC_CanChangeFriendList` | libdwcac | friend codes and the list-mutability gate | [S: `src/matched/DWC_CheckFriendKey.c`] |
| `DWCi_Acc_GetFlags`, `_GetFriendKey`, `_GetUserId`, `_IsDirty`, `_SetMaskBits` | libdwcac | the account object's accessors | [S: `src/matched/DWCi_Acc_GetFriendKey.c`] |
| `func_ov065_02274798` (`DWC_Auth_Prepare_FirstPost`) | ov065 | builds the WFC authentication POST, including `devtime` from the RTC | [S: `src/matched/func_ov065_02274798.c`] |
| `DWCi_BACKUPlInit` / `_Read` / `_WriteAll` | libdwcac | the wireless-settings backup store | [S: `src/matched/DWC_BACKUPlCheckSsid.c`] [E: replaced by `port/shim/net/dwcbackup.c`] |
| `DWCi_SNDlPlay`, `_Stop`, `_SetVolume`, `_SetPitch` | libdwcac | the network UI's hooks into the sound player | [S: `src/matched/DWCi_SNDlPlay.c`] |
| `func_0210172c` | autoload_2 | narrows the settings-store init result; the port answers 0 | [H: host-source account from `port/shim/net/dwcinit.c`; verify with a retained scripted run and frame using this page's recipe] |

## Data it reads and writes

| address or field | meaning | who writes | who reads |
|---|---|---|---|
| PXI tag 10 | the WM channel to the ARM7 | the ARM9 wireless manager | the ARM7 (the port drops it, naming the tag once) [H: host-source account from `port/shim/os/pxisend.c`; verify with a retained scripted run and frame using this page's recipe] |
| `DWCMatchControl.friendList` / `.friendIdxList` / `.evalCallback` | the matchmaking state a session runs from | `DWCi_MatchInit` | the matching layer [S: `docs/kb/modules/ov065-dwc.md`] |
| `DWCLoginControl` user id / password / connect flag / auth token | the account credentials the POST carries | the auth thread | `DWC_Auth_Prepare_FirstPost` [S: `docs/kb/modules/ov065-dwc.md`] |
| the DWC backup pages | SSIDs, WEP keys, DHCP settings, validated by CRC-16 | `DWCi_BACKUPlWriteAll` (the port: dropped) | `DWCi_BACKUPlRead` (the port: all zeros) [H: host-source account from `port/shim/net/dwcbackup.c`; verify with a retained scripted run and frame using this page's recipe] |
| `DWC_BM` 4-page map | the settings store `DWC_BM_Init` validates and repairs with `MATH_CalcCRC16` | `DWC_BM_Init` | the settings UI [S: `src/matched/func_02100830.c`] |

## How to check it

There is nothing to run. The check that matters is negative and is already part of every town
run: grep the log for `acww pxi: tag a` (WM) and for any `DWC`/`WM` symbol in an
`unimplemented:` line. Neither appears in `scratchpad/cycle40/runs/tap-D56`'s 59,808-line log
[E: `scratchpad/cycle40/runs/tap-D56`, 48,000 frames]. If one ever does, the game has reached a
network path and this page stops being descriptive.

## Hypotheses

- Local wireless (`WM_*`/`WCM*` alone, no IP) is the tractable half to revive, because it needs
  no server that no longer exists. Settled by tracing which of the 44 `WM_*` entry points the
  game's own "visit a friend nearby" path actually calls -- which requires reaching that menu,
  which no recipe does yet.
- The three `ov065thunks.c` functions the title menu reaches are the only network-adjacent code
  on the boot path. Evidence: 48,000 frames with no other ov065 symbol named
  [E: `scratchpad/cycle40/runs/tap-D56`]. Settled by an `ACWW_WATCH` sweep over ov065's address
  range across a full run.
- `func_0210172c`'s real answer matters. The port always says "settings valid, nothing erased";
  the alternative answer would send the game into the settings-erased path. Settled by flipping
  the shim's return and comparing the boot.
- The `devtime` dependency means an ACWW that could still log in would refuse to do so under the
  port's fixed 2005 clock [S: `func_ov065_02274798` returns `DWCAUTH_E_RTCERR` on a failed read,
  and the port's read succeeds -- so the failure would be server-side, not clock-side].

## Related

- `time-and-rtc.md` -- the clock the authentication POST carries.
- `rng.md` -- the SDK generators whose only established consumers are here.
- `../experiments/off-recipe.md` -- the run the negative check above is read from.
