# 주민
<!-- source: wiki/systems/villagers.md -->

**요약.** 마을에는 최대 여덟 명의 주민이 산다. 각 주민은 세이브 이미지 안에서 고정 스트라이드 레코드 하나를 차지하며, 각 레코드는 집 하위 레코드를 품고 있다: 저장소 안에서 주민과 집은 하나의 객체이다. 누가 이사 오는지는 생성 시점에 단 한 번, 여섯 클래스를 순회하며 중복을 거부하는 선택기(picker)가 결정한다; 누가 화면에 있는지는 매 프레임, 현재 있는 주민마다 액터 채널 하나를 여는 스포너(spawner)가 결정한다. 성격은 두 번 나타난다: 선택기가 어느 클래스에서 뽑았는가, 그리고 주민이 반응할 때마다 표정과 애니메이션을 고르는 가중치 테이블에서. 포트는 주민을 그린다: 두 사이클 동안 한 명도 보이지 않은 뒤, 2026-09-10에 주민에게 걸어가 말을 걸었다 -- 그 이유는 드로우 체인이 아니라 도착 튜토리얼의 홀드(hold)였다.

## 무슨 일이 일어나는가

여덟 개의 주민 레코드는 세이브 이미지 안 `0x021dc7a8 + 0x9284` = `0x021e5a2c`에 스트라이드 `0x7ec`로 놓이며, 각 레코드의 `+0x7a0`에 주민 하위 레코드가 있다
[S: func_02085a30, main, port/shim/game/villspawn.c]. 이 단일 스트라이드가 이 게임에서 집과 거주자가 분리 불가능한 이유이다: 집 배치기가 같은 배열을 인덱싱한다
(`for (j = 0; j < 8; self += 0x7ec, j++)`)
[S: func_0207bbb8, main, port/shim/game/houseplace.c].

새 마을에 누가 사는지는 `func_0207b594`가 결정하는데, 이는 매칭된 소스가 없는 `main`의 `0x1d0`바이트짜리 함수이다: 다섯 겹의 중첩 루프가 주민 슬롯 여덟 개와 종(species) 슬롯 열일곱 개를 순회하며, 각각이 허용되는지 `func_0209bcd4`와 `func_0209c380`에 묻고, `func_020644cc`로 뽑고, 결과를 `func_0209bd30`을 통해 쓴다
[S: func_0207b594, main, port/shim/game/villagers.c].

**`func_020644cc`는 이 게임의 `rand(n)`이며 그 시드는 시계(CLOCK)이다** (`rng.md`): `0x021cb5a0`의 상태 워드 하나를 `x = x * 0x19660d + 0x3c6ef35f`로 전진시키며, 부팅 시 `func_02061530`이 `func_0209dbbc`를 통해 `minute | day<<8 | hour<<16 | second<<24`로 단 한 번 설정한다
[S: `src/matched/func_02061530.c`, `src/matched/func_0209dbbc.c`]. **주민 명단(roster)과 마을 id는 하나(ONE)의 스트림에서 나오지만 시점은 크게 다르다**: 두 번 탭하는 마을 레시피에서 id는 프레임 24,789에 확정되고, 슬롯 0의 주민 id 바이트 `0x021e61db`는 pc `0x020036ec`가 쓰는 프레임 **36,135**, 즉 11,346 프레임 뒤에 확정된다 -- 따라서 그 사이에 난수를 하나라도 소비하는 것은 id를 바꾸지 않은 채 명단만 바꾼다
[E: `docs/log/cycle41-gameplay.md` ORACLE46, runs `scratchpad/oracle46/runs/o46-A`, `scratchpad/oracle46/runs/o46-B`, `scratchpad/oracle46/runs/o46-E`].

**원본(ORIGINAL)에서 읽어 낸 주민 id는 ORACLE46 이전에 작성된 어떤 장부에서도 `0x80` 미만일 때만 신뢰할 수 있다**: `observer.lua`는 엿본(peek) 워드를 Lua의 `%d`로 출력했는데, 이는 비트 31이 켜진 모든 워드 -- id는 그 워드의 바이트 3이다 -- 를 `-2147483648`로 뭉개 버렸고, 이를 다시 읽으면 `128`이 된다. TUTORIAL45의 에뮬레이터 명단 `66, 128, 21, 128`과 `107, 94, 128, 128`은 게임이 아니라 그 결함이다 [H: log/source account: `docs/log/cycle41-gameplay.md` ORACLE46 O46-2; receipt provenance unresolved]. **그 에뮬레이터 행들은 철회(RETRACTED)되었다:
`docs/log/cycle41-gameplay.md`, O46-2.** 두 호출자 모두 이를 `void`로 선언하고 어느 쪽도 결과를 읽지 않으므로, 그 유일한 산출물은 주민 테이블이다
[S: func_0207b57c / func_0209e828, main, port/shim/game/villagers.c].

초기 선택 루프는 `func_0207c76c`이며 구조가 읽기 쉽다. 여덟 번 반복한다. 각 반복은 `func_0207c818(self, mask)`에 클래스 인덱스를 묻는다; 6 이상인 인덱스는 건너뛰므로 클래스는 여섯(SIX) 개이다 -- 게임의 성격 그룹이다
[S: func_0207c76c, main, src/matched/func_0207c76c.c]. 그 다음 `func_0207c8c8(self, idx, 1)`이 그 클래스에서 주민 하나를 뽑고, 결과가 `~local2`(중복 방지 장치)와 같으면 거부되며, 성공하면 `func_02081518`이 이를 `self + 0x7ec * i` -- i번째 집 레코드 -- 에 쓰고 `func_0207ca74`가 `self + 0x4060`에 기록한다
[S: func_0207c76c, main, src/matched/func_0207c76c.c]. 생성된 마을에서 값 `0x65`, `0x78`, `0x27`의 선택 세 건이 관측되었다
[H: log/source account: port/BOOT-STATE.md, fifth pass 2026-08-27; receipt provenance unresolved].

이사 오기는 생성만이 아니라 달력에 묶여 있다: 마을 디스패처의 생성 핸들러 다음에 "주민을 이사시키는 RTC 전진"이 오고, 그 다음 생성 후 동기화가 온다 [S: func_0209e6ec, main, port/shim/gfx/pmflist.c].

주민을 화면에 올리는 것은 매 세션 실행되는 별개의 체인이다. 모드 `0x2c`의 부팅 스크립트가 채널 `0xd0`를 연다; 그 init `func_02085558`은 야외 분기를 타고 스포너 `func_02085a30`을 호출하며, 스포너는 집 레코드 여덟 개를 순회하면서 현재 있는 각 주민마다 id `(i | 0xe000)`으로 채널(CHANNEL) `0x84`를 연다
[S: func_02085558 / func_02085a30, main, port/shim/game/villspawn.c]. 채널 `0x84`의 생성자 `func_ov068_0226da64`(ov068 데이터의 레코드 `0x022771a0`)가 `0xa10`바이트 주민 액터를 만들고, 그 init `func_0202e1fc`가 이를 `0x021d1d4c`의 매니저에 등록한다
[S: func_ov068_0226da64 / func_0202e1fc, ov068/main, port/shim/game/villspawn.c]. 매니저는 `{actor, id}` 쌍 여덟 슬롯이며 종류(kind)는 `0xe`이다
[H: source account: port/shim/game/villspawn.c, port/shim/game/campos.c; direct ROM-source provenance unresolved].

주민의 드로우 진입점은 정적 테이블이 아니라 객체 안에 보관된 멤버 함수 포인터(POINTER-TO-MEMBER)이다: `func_ov068_0226d770`은 `obj + 0x8b0`에서 8바이트 mwcc `{lo, hi}` 쌍을 읽어 이를 통해 호출하며, 그것이 null이면 `+0x5c`의 `Vec3`를 `+0x478`, `+0x484`, `+0x490`의 세 슬롯으로 복사하는 것으로 대체한다
[S: func_ov068_0226d770, ov068, port/shim/game/villdraw.c]. 이 쌍은 파생 init `func_ov068_0226d850`에서 `data_ov068_02276eb0`으로부터의 8바이트 복사로 바인딩되며, 그 ROM 내용은 `{0x0226d809, 0}` -- 즉 `func_ov068_0226d808`, Thumb -- 이다
[S: func_ov068_0226d850, ov068, port/shim/game/villbind.c]. 바인딩은 상태 기반이다: 상태 0의 진입이 바인딩하고 상태 1의 진입이 바인딩을 해제한다
[H: source account: port/shim/game/villdraw.c, observed rebinds; direct ROM-source provenance unresolved].

**이 쌍은 쓰이고, 그 다음 ROM이 의도적으로 지운다.** 마을 회관에서 걸어 나오는 구간에 `actor + 0x8b0`에 스토어 워치포인트를 걸면 정확히 세 번의 스토어가 나오고 그 이상은 없다:
`func_ov068_0226d850`이 pc `0x0226d874`에서 `{0x0226d809, 0}`을 쓰고(파생 init 자신의 `data_ov068_02276eb0`으로부터의 8바이트 복사), 두 번째(SECOND) 바인더 `func_ov068_0226cb00`이 자기 원본 `0x022770a8`에서 같은 쌍을 pc `0x0226cb16`에서 쓰며, 그 다음 `func_ov068_0226bb3c`가 pc `0x0226bb86`에서 `{0, 0}`을 쓴다 -- 풀 워드 `0x0213dd98`로부터인데, 이는 **autoload_2 `.data`**(`0x02138f80..0x0213fdc0`)이고 그 ROM 바이트는 `00000000 00000000`, 즉 mwcc의 정적 NULL 멤버 포인터이다. 따라서 `func_ov068_0226bb3c`는 드로우 멤버의 바인딩을 해제(UNBIND)하는 상태 진입이며, 드로우 슬롯이 보는 null은 잃어버린 쓰기가 아니라 ROM 자체의 값이다
[H: log/source account: docs/log/cycle41-gameplay.md VILLAGER42, `v42-W2`; S: extract/adm-kr/arm9/unk_autoload_2.bin +0x55558, config/adm-kr/arm9/delinks.txt; receipt provenance unresolved]. vtable의 슬롯 0(`0x022771c0`)에 건 로드 워치포인트는 pc `0x01ffd4a0`에서 발화하므로, 디스패처는 파생 init을 실제로 가져와 실행한다
[H: log/source account: `v42-W2`; receipt provenance unresolved]. `villdraw.c`도 `villbind.c`/`villspawn.c`도 인터프리터 레지스트리에 없고 -- `port/shim/game/`은 `SERVICE_DIRS` 항목이 아니다 -- `FS_StartOverlay`는 이 경로에서 재배치 패스를 실행하지 않으므로, 그 세 워드 모두 출하된 그대로의 ROM 데이터이다
[H: source account: port/tools/interp_registry.py, port/shim/fs/ovlreloc.c; direct ROM-source provenance unresolved].

**이는 GAMEPLAY42의 "8바이트 복사가 객체에 도달한 적이 없다"를 철회한다.** 그 주장은 `ACWW_INTERP_PEEK` 판독 두 번에서 나왔다; 워치포인트는 복사가 두 번 도착함을 보여 준다
[H: log/source account: docs/log/cycle41-gameplay.md VILLAGER42; receipt provenance unresolved].

두 액터는 살아서(LIVE) 걸어 다니는(WALKING) NPC이다. `0x021d1d4c`의 매니저는 `{0x022a8f48, 0xe000}`과 `{0x022a8528, 0xe001}`을 담고 있으며, `actor + 0x5c` -- 객체 자신의 `VecFx32` -- 는 실행 사이에 움직인다: 주민 0은 프레임 55,600에 `(79.000, 0.125, 95.000)`, 60,600에 `(83.000, 0.125, 111.00)`, 68,200에 `(87.510, 0.125, 78.130)`으로 읽히고 `+0x68`은 그보다 한 걸음 뒤에 있다; 주민 1은 `x = 149..159, z = 83..95` 근처에서 같은 식으로 걷는다. 둘 다 지면 높이 `y = 0.125`에 머문다
[H: log/source account: docs/log/cycle41-gameplay.md VILLAGER42, `v42-P1`, `v42-V4`, `v42-V5`; receipt provenance unresolved]. GAMEPLAY42가 "같은 Vec3 세 번"으로 읽은 `+0x478`/`+0x484`/`+0x490` 삼중항은 대체 분기가 방금 거기에 써 둔 것일 뿐이다.

**집 문은 두 프로듀서 모두에서 열리며, 거주자는 집에 있을 수 있다 (ORACLE50).** 세 사이클 동안 들어가지 못한 주민 집은 하나(ONE)의 마을에 관한 사실이다. 전진(FORWARD) 공유 레시피의 마을 `0x8365` -- 포트와 에뮬레이터 레퍼런스가 명단 슬롯 여덟 개 `6b 5e 84 ff ff ff ff ff`와 건물 셀 17개까지 모두 동일하게 생성하는 마을 -- 에서 93행짜리 체인이 주민 1의 문 앞 **(61, 69)**까지 걸어갔고, 두(BOTH) 프로듀서 모두 안으로 들어갔다. 전환에서 다섯 프레임 차이가 났으며 같은 두 워드를 보였다: 대기 중인 바깥 위치 `0x021f69b8`은 양쪽 모두 `503808 512 564736`(그 문 앞)이 되고, `0x021f69d0`의 씬 요청은 같은 목적지 `65536 512 118784`가 된다. 안에서는 두 스틸 모두 방 안에 서 있는 주민을 보여 주며, 포트의 A 펄스는 이름표에 `사브리나`가 뜬 그녀의 인사말을 열었다. **GAMEPLAY48의 `이 몸은 밖에 계신다` -- 그 문에서의 "나는 밖(OUT)에 있다" 쪽지 -- 는 포트가 열지 못하는 문이 아니라, 그 타임라인에서 마을 `0xc66e`의 거주자가 외출 중이었던 것이다** [E: `docs/log/cycle41-gameplay.md` ORACLE50 O50-3; runs `p50-door`, `e50-door`, `p50-enter`, `e50-enter`; current receipt locator: `scratchpad/oracle50/RECEIPTS.md`]. 액터 매니저에는 언제나 두(TWO) 명의 주민만 있고 마을에는 셋이 있다(GP50-1); 세 번째가 실내에 있는 그 주민이다.

**그리고 그것으로 한 명에게 찾아가기에 충분하다 (GAMEPLAY44).** `actor + 0x5c`는 플레이어의 실시간 위치 `0x021c749c`와 같은(SAME) 월드 공간에 있으므로, 액터의 타일은 플레이어와 똑같이 정확히 `x // 8192`이며, `port/tools/navlib.py`는 이제 매니저의 레이아웃 전체 -- `+0x00`부터 종류 0xe의 `{actor, id}` 슬롯 여덟 개와 `+0x40`부터 종류 0xd의 슬롯 네 개, 즉 `port/shim/game/villspawn.c` 자체의 `vill_mgr_dump`와 같다 -- 를 읽어 `navigate.py`에 대화 목표를 건넨다: 액터 타일의 걸을 수 있는 이웃 중 플레이어에게 가장 가까운 것을, 액터 쪽으로 다시 향하게 하며, 출입구 스윕은 없다. `port/tools/goto.py --to actor:<n>`은 매 반복의 자체 스냅샷에서 그 목표를 다시 해석하는데, 주민이 걷기(WALKS) 때문이다 -- 한 명은 다섯 번의 반복에 걸쳐 (76,47) -> (75,47) -> (77,45)로 움직였다 -- 그리고 플레이어가 그 타일에 서면 A를 한 번 누른다. 마르는 첫 펄스에 대답하고 A 펄스들은 대화를 세 줄 더 이어 간다
[E: `docs/log/cycle41-gameplay.md` GP44-2, `scratchpad/gameplay44/RECEIPTS.md`, runs
`TALK1-1`..`TALK1-5` and `g44-TALK`]. 이는 VILL42-4의 "도달(reach)" 후보를 닫는다: 스폰, 바인딩, 드로우에는 아무 문제도 없었다 -- **액터 자신의 위치를 겨냥한 걷기가 한 번도 없었던 것**이며, 세 사이클의 스윕은 씬 진입 위치라서 움직이지 않는 `0x021f69d4`를 겨냥하고 있었다.

**철회 두 건, 이 순서로, 그리고 이 문단이 그 주장에서 남은 것이다.** 이 페이지는 예전에 여기서 "아직 어떤 주민도 화면에 나온 적이 없으며, 그 이유는 도달이다"로 시작했다. **SAVE43이 그것을 철회했다**: 주민은 그려지고(ARE) 있으며, 플레이어 집 주변 에이커에서 한 명이 부딪힘과 `A`에 대화 상자로 응답하고, 너굴은 도착 연설 전체에 걸쳐 그려진다 [H: log/source account: `docs/log/cycle42-save.md` SAVE43, `gp-D2`, `gp-D4`; receipt provenance unresolved]. **GAMEPLAY44는 GAMEPLAY43의 시계 설명을 철회했다.** 동결 생성된 마을 스냅샷 하나에서, 동결 시계 조건과 전진 시계 조건이 같은 프레임에 걸쳐 모두 홀드된다; 프레임 048,000..051,400은 SHA-256이 동일하다. 마을 생성 차이가 GP43의 비교를 교란했던 것이다 [E:
`docs/log/cycle41-gameplay.md` GAMEPLAY44, GP44-1; `scratchpad/gameplay44/RECEIPTS.md`,
`g44-FRZ` and `g44-ADV`, 048,000..055,000]. `X` 다음 `B` 관측은 VILLAGER42 도착 체인에 속하는 것이며 동결 시계에 대한 일반 규칙이 아니다.

여전히 유효한 것은 두 액터가 살아서(LIVE) 걸어 다닌다(WALKING)는 점, 그리고 추적은 그들을 겨냥해야(AIMED) 한다는 점이다. **플레이어의 실시간 위치는 `0x021c749c`, 필드 카메라가 추적하는 벡터이다 -- 이 페이지가 아래에서 인용하는 `0x021f69d0` 레코드가 아니다(NOT).** 그 레코드는 씬 진입(SCENE-ENTRY) 위치이다: (145.000, 0.125, 179.875)로 읽히고 1,400 프레임을 걸은 뒤에도 같은 값으로 다시 읽히는 반면, 주민 자신의 `actor + 0x5c`는 두 판독 사이에 움직이며, 그것을 기준으로 겨냥한 세 번의 스윕은 아무도 만나지 못했다. NAV42는 플레이어를 두 곳에 둔 한 빌드의 스냅샷 두 개를 비교(diff)해 올바른 주소를 찾았고, 필드 카메라 자체의 원기둥 변환에 대해 세 가지 방법으로 확인했다;
`port/tools/navigate.py`는 그것으로부터 에이커 충돌 그리드 위의 걷기를 계획하고
`port/tools/goto.py`가 루프를 닫는다 [H: log/source account: `docs/log/cycle41-gameplay.md` NAV42 and GP43-5, `g43-P2`, `g43-P3`, `g43-T2`, `g43-T3`, `g43-T4`; VILLAGER42 `v42-P4`; receipt provenance unresolved]

원본(ORIGINAL)도 같은 타임라인에서 주민을 보여 주지 않는다: 같은 패드 스크립트와 같은 두 번 탭 마을 레시피를 쓴 에뮬레이터 조건에서, 49,800..55,500의 20 프레임 동안 원본은 같은 삽화가 있는 같은 도착 튜토리얼 안에 있고 어느 프레임에도 주민이 없다
[O: docs/log/cycle41-gameplay.md VILLAGER42, `scratchpad/villager42/oracle-vill/`]. 이는 위의 두 해석 모두와 일관된다: 원본도 같은 홀드 안에 있다.

**과거의 관측들은 프롬프트에 관해 서로 달랐다 (STYLE 규칙 7).**
VILLAGER42는 패드 스크립트에 `X`가 없으면 11,900 프레임 뒤에도 삽화가 여전히 떠 있고, `X`(마스크 `0x400`) 다음 `B`가 이를 지운다고 측정했다
[H: log/source account: VILLAGER42, `v42-V1`, `v42-V3`, `v42-V4`; receipt provenance unresolved]. SAVE43의 체인에는 **`X` 행이 전혀 없었는데도** 홀드가 풀렸고, 그 뒤 주민이 그려져 부딪힐 수 있었다
[H: log/source account: SAVE43, `gp-P1`..`gp-D4`; receipt provenance unresolved]. 위의 GAMEPLAY44 같은 마을 비교는 시계 교란을 해소한다; 프롬프트를 열고 지우는 정확한 도착 이벤트는 별개의 질문으로 남아 있다.

주민 자체의 드로우 슬롯은 서비스 쪽의 id별 슬롯에 SRT를 밀어 넣을 뿐이며(`func_02012214 -> func_0205e954`); 모델 지오메트리는 NPC 모델 서비스 자체의 드로우 슬롯 `func_020500d8`(vtable `0x020dce48` 슬롯 9, `data_021c8184`의 객체)가 상태 3에서 요청 슬롯당 `func_0205510c` 한 번씩 제출한다
[S: func_020500d8 / func_02012214, main, port/shim/game/villmodel.c]. 따라서 주민이 자기 슬롯에서 GX 워드를 0개 내보내는 것은 정상이다
[H: source account: port/shim/game/villmodel.c; direct ROM-source provenance unresolved]. 광원 매니저가 수리된 뒤 주민 드로우는 프레임당 `0x8c8`-`0xa20` 워드를 내보내는 것으로 측정되었다
[H: log/source account: port/BOOT-STATE.md, "Villagers were never missing"; receipt provenance unresolved].

주민의 얼굴은 모델 id가 아니라 테이블 인덱스이다. `func_020808ec`는 `record + 0x7af`의 바이트를 읽어 `func_02082500`에 넘기고, 이는 `data_020cd884`를 `param * 0x4e`로 인덱싱한다; `func_020808d0`의 `>= 0x21`에 대한 대체값이 0이므로 테이블은 33항목으로 한정된다 [S: func_020808ec / func_02082500, main, port/shim/game/villagerface.c].

표정과 애니메이션은 가중치 추첨이다. `func_0204fb80`은 `0x020dc8b4`의 테이블의 테이블을 받아 `table[a3 - 1][a5]`를 선택하고, `a2 * 8`을 더해 `[0]`이 항목 배열이고 `[4]`가 개수인 8바이트 레코드에 도달한 뒤, 3바이트 항목들 -- `+0`과 `+1`이 두 출력, `+2`가 가중치 -- 을 순회하며 가중치를 누적해 추첨값을 넘는 항목을 찾는다
[S: func_0204fb80, main, port/shim/game/exprpick.c]. 추첨값은 `func_020e92d0(&0x021cb5a0, bound)`에서 오며, 상한은 `func_02073d90(*0x020ccf94)`에 따라 `0x60` 또는 `0x64`이다 -- 이 모드 검사는 통과할 때 마지막 세 항목도 건너뛴다 [S: func_0204fb80, main, port/shim/game/exprpick.c]. 실패 시에는 아무것도 쓰지 않고 함수가 0을 돌려주므로, 0을 돌려주는 스텁은 모든 주민이 호출자가 그 두 워드에 남겨 둔 값을 그대로 쓰게 만든다 [H: source account: port/shim/game/exprpick.c; direct ROM-source provenance unresolved].

근접 반응을 위한 주민 접근 스캔이 있다: `func_ov068_02266bac`은 `0x0222f458`의 ov003 슬롯 위치 getter를 호출하고, 이는 `p = 0x022617bc + (idx & 0xf) * 0x25c`를 읽어 `p + 0x204`의 `Vec3`를 복사하고 `p + 0x24d`의 부호 있는 바이트 -- 슬롯 점유자 id, 비어 있으면 `-1` -- 를 돌려주며, 그런 다음 `func_020ea990(pos, out) >= threshold`이면 슬롯을 거부한다
[S: func_ov068_02266bac / func_ov003_0222f458, ov068/ov003, port/shim/game/genfix.c]. `0x0225f76c`에 스트라이드 `0x24c`의 병렬 6슬롯 NPC 테이블이 있다
[H: source account: sub_02227638, ov003, port/shim/game/genfix.c; direct ROM-source provenance unresolved].

이 모든 것을 구동하는 ov003 슬롯 기구는 `__sinit_ov003_02237af4`가 `0x0225f76c`에 `0x24c` 슬롯 레코드 여섯 개를 구성한 뒤에야 실행된다; 그 초기화기가 건너뛰어졌을 때는 프레임별 슬롯 패스 전체가 죽어 있었다
[S: __sinit_ov003_02237af4, ov003, port/shim/game/exprpick.c].

주민 집은 텍스처 세트 넷과 애니메이션 둘을 쓰며, ov003 자체 풀에 이름이 있다:
`/str/npcHsTex/%c/house_%c%d%c.nsbtx`, `/str/npcHsTex/%c/light_%c%d.nsbtx`,
`/str/obj_house_i.nsbca`, `/str/obj_house_o.nsbca`
[S: ov003 image at 0x02239bf8, 0x02239c1c, 0x02239c40 and 0x02239c58,
port/shim/game/townhouses.c; the same four addresses `town.md` cites].

**주민과 대화하려면 고유한 전제 조건이 있으며, 그것은 버튼이 아니라 주민의 위치에 관한 것이다.** 트리거는 A 버튼의 에지(edge)이다. 게임은 메인 루프가 한 번 돌 때마다 패드를 `0x021fbe3c`(홀드)와 `0x021fbe42`(트리거)에 기록하고, 한 번의 루프는 표시 프레임 세 개마다 한 번이므로 세 프레임보다 짧은 누름은 샘플링 프레임을 우연히 덮을 때만 등록된다. 그 누름을 전달했을 때 인접한 주민은 두 조건이 **모두** 맞으면 첫 에지에 응답한다. 플레이어에서 **약 한 타일 안**이어야 한다 -- 1.99 월드 유닛에서는 응답했고 3.67에서는 응답하지 않았으며 타일은 2.0 유닛이다 -- 그리고 플레이어가 **주민을 향하고** 있어야 한다. 이 방향은 플레이어가 이미 향하고 있던 방향이며 주민 쪽으로 누른 방향이 아니다. 같은 누름으로 반대쪽을 향하거나 같은 타일에서 주민을 가로질러 향하면 아무것도 열리지 않으며, A 없이 주민 쪽으로 방향을 홀드해도 740프레임 동안 아무것도 열리지 않는다. 응답한 주민은 모두 자신의 속도 워드 `actor + 0x98`이 0(정지)이었지만, 그것이 필수 조건인지는 여기서 거리 조건과 분리되지 않는다
[E: `docs/log/cycle42-save.md` TALK45, runs `scratchpad/talk45/runs/{B1,B6,B7,B8,C1,C2,C3,L1,L2,L3,L4}`]. 주민 자신의 방향과 명령 속도는 플레이어 액터가 가진 것과 같은 두 워드이며, 매니저가 `0x021d1d4c`에서 보유하는 액터의 같은 오프셋에 있다: `actor + 0x94`(16비트 방향, 0 = 남쪽, 0x4000 = 동쪽, 0x8000 = 북쪽, 0xc000 = 서쪽)와 `actor + 0x98`
[S: `port/tools/navigate.py` header (WALK56); `port/tools/navlib.py` section 4].

**걷는 플레이어가 그 타일에 들어가는 방법: 주민을 밀어 넣고, 미는 동안 누른다 (VILLAGER76).** 위 문단은 세이브스테이트 결과이고, 이것은 걸어서 접근하는 경우이며, 충돌이 조준을 처리한다. 주민은 플레이어를 **막았다가** 지나가게 한다. 주민 옆 타일에서 방향을 홀드하면 빈 타일에서는 18프레임이면 될 이동이 주민의 타일 안으로 들어가는 데 **116프레임** 걸리고, 그 다음 플레이어를 한 타일 **옆으로** 밀어내며 자유롭게 걷는다. 따라서 접촉은 대화 창 안에 서 있는 약 **96프레임**의 시간이 되며, 멈추면 플레이어는 **0.78~0.995타일**에 남는다 -- 0.995타일은 1.99유닛으로 TALK45가 응답을 측정한 거리이다. 방향을 `25 * tiles + 40`프레임 동안 홀드하고 그 아래에서 A를 펄스하는 스크립트 암(arm) 아홉 개는 **9/9**였고, 200~240프레임 동안 홀드하는 일곱 개는 **0/7**이었다. 후자는 플레이어가 창을 지나 네~여섯 타일 떨어진 곳에서 끝나기 때문이다. 59.82fps의 `play.py`와 `drive.py`를 통한 실시간 실행에서는 걷다가 만난 다섯 번 중 다섯 번 대화가 열려 **5/5**였다 -- 홀드한 방향과 `Z` 열차가 **겹치고**(`Z`를 놓은 뒤 시작하면 이미 96프레임을 소비한다), 닫는 `X`는 주민에게서 **멀어지는** 방향을 홀드한 상태와 겹친다
[E: `docs/log/cycle41-gameplay.md` VILLAGER76 V76-6, V76-7; runs `scratchpad/villager76/runs/{H1,W2,W3,T1,T2,BLK,BLK2,W01..W05}*`].

**누가 밖에 있는지는 시간에 따라 달라진다.** 11:30에는 매니저가 주민 세 명과 시장을 함께 마을 안에서 걷게 했고, 그 세이브의 인구조사는 3명이었다. 10:00에는 같은 마을의 야외 스냅샷에 두 명이 있었고, 어두워진 뒤에는 아무도 없었다
[E: `docs/log/cycle42-save.md` TALK45; `docs/kb/hybrid/stall-playbook-recent.md` case 91]. **그리고 매니저의 상한은 인구조사보다 낮다**: 인구조사가 5명인 LIVE47 세이브에서 09:00, 11:30, 15:00, 17:00에 야외 매니저가 정확히 세 명을 보유했고, 네 시간대의 합집합은 네 명(`0xe000`..`0xe003`)이었으며, 슬롯 4는 어느 시간대에도 야외에 있지 않았다
[E: `docs/log/cycle41-gameplay.md` VILLAGER76 V76-1].

## 상태 머신과 주민이 갖는 두 시뮬레이션 (VILLAGER76)

**주민은 항상 걷는 것이 아니다.** 객체의 상태 워드는 `actor + 0x380`이며, `func_0201b1a4` 안의 pc `0x0201b246`에서 메인 루프가 돌 때마다 기록된다
[S: `src/matched/func_0201b1a4.c`; E: watchpoint `scratchpad/villager76/runs/WATCH-STATE`]. 이 워드는 전혀 다른 두 시뮬레이션 중 하나를 선택한다:

| `+0x380` | 실행되는 것 | `+0x5c` 위치 | `+0x94` 방향 | `+0x98` 속도 | `+0x388` 목표 |
|---|---|---|---|---|---|
| **0** | 타일 격자(TILE LATTICE) | 항상 타일 중심 | 0 | 0 | (0,0) |
| 1 | 목표로 걷기 | 자유 | 실시간 값 | 256까지 상승 | 타일 중심 |
| 2 | 두 번째 다리 종류, 드묾 | 자유 | 실시간 값 | 실시간 값 | 타일 중심 |
| 3 | 다리를 시작하는 회전 | 유지됨 | 실시간 값 | 0 | 타일 중심 |

**상태 0에서 주민은 표시 프레임 120마다 한 타일을 통째로 전진하며 전혀 걷지 않는다.** 플레이어를 15타일 이상 떨어뜨린 채 주민 세 명을 3,060프레임 동안 관찰하자 각각 25걸음을 걸었고, 간격 히스토그램은 `120 x24`였다 -- 모든 주민의 모든 간격이 그랬다. 위치는 반올림으로 얻는 것이 아니라 구성상 타일 중심이다. `func_0204f794`는 x와 z에 `(tile << 13) + 0x1000`을 쓰고 y에는 0을 쓰며, 지면 패스가 이를 `0x200`만큼 올린다
[S: `src/matched/func_0204f794.c`; E: watchpoint `runs/WATCH-POS`, pc `0x0204f79a`], 그리고 `func_0204f818`은 같은 프레임에 계산된 타일을 `+0x988`/`+0x98c`에 다시 쓴다
[S: `src/matched/func_0204f818.c`; E: `runs/WATCH-TILE`] -- 이 쌍은 `pos >> 13`의 **캐시**이며 목표가 아니다.

상태 1/2/3에서는 같은 객체가 매 이터레이션마다 일반 충돌 이동인 `func_02031288`에 의해 통합된다. 현재 위치, 목표 위치, `0xc000` 클램프, `func_02030ebc`의 스윕, `func_02034270`의 `floor + 0x200` 지면 스냅, 그리고 결과의 재기록이 그 과정이다
[S: `src/matched/func_02031288.c`]. 한 다리는 `state 0`(12~51프레임의 정지, 목표는 (0,0)으로 지워짐) -> `state 3`(27~42프레임의 회전, 새 목표는 이미 선택됨) -> `state 1`(48~639프레임의 걷기) 순서다. 목표는 한~여덟 타일 떨어진 새 타일 중심이며, 3,060프레임 동안 주민 하나마다 서로 다른 목표가 11개였다.

**어느 시뮬레이션이 실행되는지를 정하는 것은 플레이어와의 거리이며, 깔끔한 반지름이 아니다.** 플레이어를 세워 두고 주민을 255프레임 기록했을 때, 남쪽 2, 4, 6, 8타일과 북쪽 5, 6타일에서는 깨어 있었고, 북쪽 7, 8, 9타일과 동쪽 10, 12타일, 서쪽 16타일, 북쪽 20타일에서는 격자에 있었다. 따라서 시도한 모든 방향에서 6타일 안쪽이면 전환되고, 한 방향에서는 7타일 바깥에서 전환된다; 에이커 기준은 아니다(북쪽 7타일은 북쪽 6타일과 같은 에이커다)
[E: VILLAGER76 V76-5, `radius76.py`].

**ORACLE78은 그 경계를 타일의 8분의 1 단위로 훑었고, 플레이어가 지닌 네 경계의 축 정렬 XZ 직사각형 -- 축별 상자(PER-AXIS BOX)이며 네 경계가 모두 다르다 -- 임을 확인했다.** 같은 장비와 같은 체인에서 변수 하나만 바꿔 플레이어를 서브타일 위치에 놓고, 주민을 프레임당 한 샘플로 765프레임 기록했다. 아래의 모든 경계는 **날카롭다** -- 마지막 깨어 있음 암과 첫 수면 암은 타일 8분의 1만큼 떨어진다 -- 그리고 안정적이다: `6.875`타일에서는 765프레임 동안 한 번도 깨어나지 않았고, `6.5`와 `6.0`에서는 모두 프레임 8,081에 깨어났다
[E: `scratchpad/oracle78/BOUND-SWEEP.txt`, `wake-*.json`, `SHORT-*` arms].

| 플레이어 기준 주민의 위치 | 깨어남까지 | 그때부터 잠듦 | 암 |
|---|---|---|---|
| 플레이어의 **남쪽**(플레이어는 북쪽에 섬) | **6.750** | **6.875** | `0x022a7698`, 17 arms |
| 플레이어의 남쪽, **두 번째 주민** | **6.875** | **7.000** | `0x022a80b8`, 17 arms |
| 플레이어의 **북쪽**(플레이어는 남쪽에 섬) | **12.000** | **12.500** | `0x022a80b8`, 31 arms |
| 플레이어의 **서쪽** | **8.375** | **8.500** | `0x022a7698` |
| 플레이어의 **동쪽** | **7.750** | **7.875** | `0x022a7698` |

서로 다른 두 주민이 같은 경계를 타일 8분의 1만큼 떨어뜨려 놓았으므로, 그 경계는 객체가 아니라 플레이어의 것이다.

**에이커 가설은** 모든 경계가 타일 8분의 1 단위로 날카롭다는 사실로 **기각된다.** **주민을 중심으로 한 반지름 가설은** 같은 축에서 6.75와 12.0이 나온다는 사실로 **기각된다.** **축별 상자 가설은 남아 있으며, 이를 말해 주는 제어 실험이 하나 있다**: x 경계 `8.375`/`8.500`은 주민의 깊이에서 측정했을 때와 플레이어를 z축으로 네 타일 떨어뜨렸을 때 모두 같았다 -- x 경계는 z에 의존하지 않는다
[E: `wake-eperp-4-sweep.json`].

**비교 함수는 `func_ov068_0226caac`이며, 말 그대로 네 경계 직사각형이다**
[S: `src/matched/func_ov068_0226caac.c`]: `b->x > a->x - s->halfExtentX && b->x < a->x + s->halfExtentY`, 다음으로 `b->y > a->y - s->top`, 그 다음 `b->y < a->y + s->bottom`을 검사한다 -- XZ 평면에서 서로 `VecFx32` 모양인 점 `a`와 `b`에 네 개의 독립된 경계를 적용한다. 이는 같은 스냅샷에서 깨어 있는 암 하나와 잠든 암 하나의 `ACWW_INTERP_CENSUS` 창을 **차분**하여 찾아냈다. 잠든 암의 함수 집합은 깨어 있는 암의 엄격한 부분집합이었다(깨어 있을 때만 260개, 잠들었을 때만 0개). 양쪽에 존재하면서 호출 횟수가 **같은** 본문 중에는 `func_ov068_0226687c`(이터레이션별 주민 디스패처, 255회 호출, 3,225걸음 대 1,785걸음)와 `func_ov068_0226caac`(255회 호출, 8,773 대 8,653)의 스텝 수가 갈렸다
[E: `scratchpad/oracle78/CENSUS-DIFF.txt`, runs `CEN-awake` / `CEN-asleep`]. 네 경계값을 `s`에서 읽어 낸 것은 아직 아니며, 다음에 할 일이다.

**두 장비는 먼저 사용했지만 암을 구분하지 못했으며, 이것이 방법에 대한 기록이다:** `actor + 0x380`에 `ACWW_INTERP_WATCH_LR`을 걸면 두 암 모두에서 키 하나만 보고한다(`pc 0x0201b246 lr 0x020b9fb9` = `func_020b9f80`). 플레이어 액터의 위치 워드에 `ACWW_INTERP_RWATCH`를 걸면 깨어 있을 때 읽는 pc가 47개, 잠들었을 때 46개다. 워치포인트는 값의 마지막 기록자와 리더를 밝히고, 인구조사는 분기(M1)를 밝힌다.

**모퉁이는 측정되지 않았다.** `dz = 6.0`에서 z 경계 안쪽으로 8분의 1타일인 경우 x에 대한 판정이 단조롭지 않다 -- `dx +2`에서는 깨어 있고 `dx +1`과 `+3`에서는 잠든다 -- 따라서 경계에서 약 한 타일 안쪽에서는 255프레임 창이 신뢰할 수 있는 분류기가 아니며, `map-z6.json`의 모퉁이 암도 도형으로 읽지 않고 그렇게 기록했다. 같은 거리로 영역 안에 들어온 두 주민은 **둘 다** 깨어 있었으므로 한 번에 한 명만 깨어 있는 상한은 없다
[E: arms `CAP-a1`, `CAP-a2`].

**`actor + 0x49c`는 이벤트 큐가 아니다.** VILLAGER76은 주민이 한 걸음 움직인 프레임에 1과 9가 나오고 그 외에는 0인 네 워드를 반 사이클 동안 `{event, code, latched}`로 읽었다. 그러나 `src/matched/`가 이를 바로잡았다. 이것은 `func_02031288`이 사용하는 0x30바이트 `A0 *self` 레코드이며, `f4 |= 1`은 지면 패스가 위치를 클램프했다는 뜻이고, `f8`은 착지한 **표면**이며, `f24/f28/f2c`는 실제로 이동한 델타이다. `func_02032c8c`는 매 이터레이션마다 `f4`를 `f0`으로 넘기고 나머지를 지운다
[S: `src/matched/func_02031288.c`, `src/matched/func_02032c8c.c`]. "이벤트 코드 9"는 지면 표면 id이다(M1).

**격자는 포트의 것이 아니라 ROM의 것이다 -- DS에 물어도 같은 결과가 나온다 (ORACLE78).** SHARED 마을에서 두 프로듀서가 모두 정지한 채 타일 (72,51)에 있었고, 야외 주민 둘은 28타일과 41타일 떨어져 있었다. 포트는 `port/tools/oracle/README.md`의 forward recipe card-32에서 `ACWW_TOUCH2_AT=23534`를, 오라클은 `--touch2-at 24700`을 사용했다. 두 프로듀서는 같은 765프레임을 같은 간격으로 기록했다 -- 포트는 영역 장부를 통해, 원본은 `+0x5c`, `+0x94`, `+0x98`, `+0x380`, `+0x388`에 `--peek`를 사용했다:

| 프로듀서 | 암 | 상태 `+0x380` | 타일 격자 위 | 걸음 | 간격 | 방향 | 속도 | 목표 |
|---|---|---|---|---:|---|---|---|---|
| **포트** | `0xe001`, `0xe002`, 각각 x2 실행 | **256/256에서 0** | 256/256 | 7 | `120 x6` | 0 | 0 | (0,0,0) |
| **원본(ORIGINAL)** | `0xe002`, x2 실행 | **256/256에서 0** | 256/256 | 6 | `120 x5` | 0 | 0 | (0,0,0) |
| **원본(ORIGINAL)** | `0xe001`, x2 실행 | **256/256에서 0** | 256/256 중 216 | 6 | `120 x5` | 0 | 0 | (0,0,0) |

**DS도 카메라 밖으로 걷지 않는다.** 두 프로듀서의 모든 간격은 정확히 표시 프레임 120이었고, 양쪽 모두 방향·속도·걷기 목표는 0이며 상태 워드는 0이었다. 두 프로듀서의 주민은 창 시작 시 한 타일 떨어져 있었고 서로 다른 경로를 택했다 -- 체인은 약 350프레임 위상이 어긋났고 레이아웃 버스트 이후 드로우 스트림도 달랐다 -- 따라서 이것은 프레임 단위 재현이 아니라 시뮬레이션 **형태**에 대한 일치다. 각 측의 두 실행은 서로 동일했다
[E: `scratchpad/oracle78/SIDE-BY-SIDE.md`, `tables/`, runs `o78-far-A`/`o78-far-B` (exit 0, 895.0/889.3 s, ledgers complete) and `P-FAR-*`].

**한 가지 차이가 있지만 포트 결함은 아니다: 원본의 정지는 항상 타일 중심이 아니다.** DS에서 `0xe001`의 여섯 정지 중 하나는 `(35.2128, 41.2128)`이며, 두 축 모두 중심에서 `0x6cf`만큼 벗어나고 120프레임 구간 전체에 유지되었다. 그 전후 정지는 다시 중심이었다. 포트의 `func_0204f794`는 매칭된 동일 코드이며 `(tile << 13) + 0x1000`을 쓰므로, 중심에서 벗어난 상태 0 위치는 ROM이 다른 인자로 호출했거나 다른 기록자가 배치했다는 뜻이다. 포트는 약 2,000개 샘플 동안 그 셀에 도달하지 않았다. **미해결이며 아래 가설에서 순위가 낮다.**

## 어디에 있는가

| 함수 또는 심볼 | 모듈 | 역할 | 등급/출처 |
|---|---|---|---|
| `func_0207b594` | main | 새 마을에 누가 사는지 결정(8 슬롯 x 17 종) | S: port/shim/game/villagers.c |
| `func_0207c76c` | main | 초기 선택 루프, 8회 반복, 6 클래스 | S: src/matched/func_0207c76c.c |
| `func_0207c818` / `func_0207c8c8` | main | 클래스 인덱스 / 클래스 안에서의 주민 추첨 | S: src/matched/func_0207c76c.c |
| `func_02081518` | main | 선택된 주민을 집 레코드에 씀 | S: src/matched/func_0207c76c.c |
| `func_02085a30` | main | 세션별 스포너: 주민마다 채널 `0x84`를 엶 | S: port/shim/game/villspawn.c |
| `func_ov068_0226da64` | ov068 | 채널 `0x84` 생성자, `0xa10`바이트 주민 액터 | S: port/shim/game/villspawn.c |
| `func_0202e1fc` | main | 액터를 매니저에 등록 | S: port/shim/game/villspawn.c |
| `func_ov068_0226d770` | ov068 | 주민 드로우 슬롯(`obj+0x8b0`의 PMF) | S: port/shim/game/villdraw.c |
| `func_ov068_0226d850` | ov068 | 파생 init, 드로우 PMF를 바인딩 | S: port/shim/game/villbind.c |
| `func_020500d8` | main | NPC 모델 서비스 드로우 슬롯: 지오메트리 제출 | S: port/shim/game/villmodel.c |
| `func_020808ec` / `func_02082500` | main | 얼굴 바이트 -> `data_020cd884` 인덱스 | S: port/shim/game/villagerface.c |
| `func_0204fb80` | main | 가중치 기반 표정/애니메이션 선택 | S: port/shim/game/exprpick.c |
| `func_ov068_02266bac` | ov068 | 주민 접근 슬롯 스캔 | S: port/shim/game/genfix.c |
| `func_0202e0c8` | main | 주민 집/레코드 스텝 | S: port/shim/game/villhouse.c |
| `func_0201b1a4` | main | 주민 STATE 워드 `+0x380`을 매 이터레이션마다 기록 | S: src/matched/func_0201b1a4.c |
| `func_0204f794` / `func_0204f818` | main | 타일 -> `(t<<13)+0x1000` 위치, 그리고 역변환 `pos>>13` | S: src/matched/func_0204f794.c, func_0204f818.c |
| `func_02031288` | main | 일반 충돌 MOVE: 클램프, 스윕, 지면 스냅, 재기록 | S: src/matched/func_02031288.c |
| `func_02032c8c` | main | 매 이터레이션마다 `+0x49c` 이동 레코드를 앞으로 넘김 | S: src/matched/func_02032c8c.c |

## 읽고 쓰는 데이터

| 주소 또는 필드 | 의미 | 쓰는 쪽 | 읽는 쪽 |
|---|---|---|---|
| `0x021e5a2c` | 집 레코드 8개, 스트라이드 `0x7ec` | `func_02081518`, `func_0207bbb8` | `func_02085a30` |
| 레코드 `+0x7a0` | 주민 하위 레코드 | 새 게임 선택 | `func_0207c72c`, `func_0208150c` |
| 레코드 `+0x7af` | 얼굴/테이블 인덱스 바이트 | 선택 | `func_02003648` -> `func_02082500` |
| `0x021d1d4c` | 주민 매니저, `{actor, id}` 슬롯 8개 | `func_02082ab0` | 카메라 선택 `func_0203c794` case `0x2c` |
| `obj + 0x8b0` | 드로우 PMF `{lo, hi}` 쌍 | `func_ov068_0226d850`, `func_ov068_0226cb00` (바인딩); `func_ov068_0226bb3c` (바인딩 해제) | `func_ov068_0226d770` |
| `data_ov068_02276eb0` | PMF 원본 쌍 `{0x0226d809, 0}` | 정적 | `func_ov068_0226d850` |
| `0x022770a8` | 같은 쌍, 두 번째 바인더의 원본 | 정적 | `func_ov068_0226cb00` |
| `0x0213dd98` | autoload_2 `.data`: 정적 NULL 쌍 `{0, 0}` | 정적 | `func_ov068_0226bb3c` |
| `0x021f69d0` | 로컬 플레이어의 레코드; `+4`가 위치 `VecFx32` | 세이브 로드 | `func_020b5e10` / `func_020b5e40` |
| `0x020dc8b4` | 8바이트 표정 레코드의 테이블의 테이블 | 정적 | `func_0204fb80` |
| `0x021cb5a0` | 표정 추첨에 쓰이는 RNG 상태 | `func_020e92d0` | `func_0204fb80` |
| `0x0225f76c` | NPC 슬롯 6개, 스트라이드 `0x24c` | `__sinit_ov003_02237af4` | `sub_02227638` |
| `0x022617bc` | 주민 접근 슬롯, 스트라이드 `0x25c` | ov003 정적 init | `func_ov003_0222f458` |
| `actor + 0x380` | 주민 STATE: 0 격자, 1 걷기, 2 두 번째 다리, 3 회전 | `func_0201b1a4` | 걷기 스텝 |
| `actor + 0x388` | WALK TARGET `VecFx32`, 항상 타일 중심; 상태 0에서는 (0,0) | 다리 선택기 | `func_02031288` |
| `actor + 0x49c` | `func_02031288`의 0x30바이트 이동 레코드 -- 이벤트 큐가 아님 | `func_02031288`, `func_02032c8c` | `func_02031288` |
| `actor + 0x988` | 도출된 타일 `pos >> 13`, 스텝 프레임에 기록 | `func_0204f818` | -- |

위 모든 행은 S 등급이며, 앞 표에 명시된 심 헤더에서 인용했다.

## 확인 방법

매니저 점유 프로브가 가장 저렴한 확인 방법이다: `port/shim/game/villspawn.c`는 모드가 바뀔 때마다 그리고 각 스폰 패스 뒤에 `0x021d1d4c`의 `{actor, id}` 슬롯 여덟 개를 출력하고, `port/shim/game/villpick.c`는 선택마다 한 줄(슬롯, 클래스, 주민 id)을 출력한다
[H: source account: port/shim/game/villspawn.c, villpick.c; direct ROM-source provenance unresolved]. 둘 다 `ACWW_TRACE_STATE=1`로 게이트된다
[H: source account: port/shim/game/villspawn.c; direct ROM-source provenance unresolved].

포트 한정 주의 사항에 유의한다: 네이티브(NATIVE) 경로에서 `func_0207b594`는 의도적으로 no-op이며 `villager placement SKIPPED`를 출력하므로, 네이티브 실행의 빈 주민 테이블은 게임이 아니라 포트의 결정이다 [H: source account: port/shim/game/villagers.c; direct ROM-source provenance unresolved]
[H: log/source account: docs/log/cycle40-keyboard-gate-probe.md LONG40, "villager placement SKIPPED" at frame 19335; receipt provenance unresolved]. 인터프리터(INTERPRETER) 경로에서는 ROM 자체의 `func_0207b594`가 실행된다
[H: source account: docs/kb/hybrid/runtime.md via docs/log/cycle40-keyboard-gate-probe.md REG40; direct ROM-source provenance unresolved].

## 가설

- **H (미해결, ORACLE78의 현재 1순위): `func_ov068_0226caac`의 네 경계가 깨어남 직사각형이며, 아직 그 값을 읽지 못했다.** 인구조사 차분은 이 본문이 해당 분기에 있음을 보여 주고, 매칭된 소스는 네 경계를 쓰는 축 정렬 XZ 검사이다(상태 머신 절 참조). 측정된 경계는 플레이어에서 서쪽 약 8.4타일, 동쪽 7.8타일, 북쪽 12.25타일, 남쪽 6.8타일이다. 빠진 것은 구조체이다: `s`가 무엇인지, 네 워드가 상수인지 주민별 값인지, `a`가 플레이어인지 카메라인지 모른다. 실험: 호출에 `ACWW_INTERP_WATCH_LR` 방식의 암 하나를 걸어 `s`를 먼저 찾고, 그 `s`가 가리키는 **네 워드**를 `ACWW_INTERP_RWATCH`로 추적하거나, 같은 인구조사에서 호출자가 주민의 `+0x5c`를 읽으므로 `func_ov068_0226d770`의 리터럴 풀을 읽는다.
- **H (ORACLE78, 이것이 인식 경로가 게이트가 아닌 이유): `func_ov068_02271cec`는 전환이 아니라 가장 가까운 액터를 스캔한다.** 이 함수는 플레이어의 `+0x5c`를 읽고(pc `0x02271d18/1c/20`), `func_020ea990` -- 플레이어와 주민 양쪽의 위치를 읽는 것으로 관찰된 유일한 본문인 제곱 XZ 거리 함수 -- 을 호출한 뒤 그 결과를 `func_ov068_02271c58`에 넘긴다. 후자는 `*(int *)(ctx + 0x224)`와 비교하고 `ctx + 0x254`의 바이트를 254에서 상한 처리하며 누적한다. `ctx`는 `actor - 0x1a8`이고(세 액터에서 그 `+0x204`는 주민의 `+0x5c`와 바이트 단위로 같다), 조사한 모든 스냅샷에서 `+0x224`는 큰 **음수** 워드를 읽으므로 `r3 > t`는 항상 참이고 플래그는 항상 1이다. 실험: `+0x254`를 **소비하는** 것이 무엇인지 찾는다 -- `+1/+3/+5/+8/+15/+25`씩 증가하며 254에서 상한 처리되는 누적기는 우정 또는 주의력 미터일 수 있고, 그 리더를 알아내는 것이 또 한 번의 스윕보다 가치 있다.
- **H (미해결, ORACLE78): 상태 0 주민의 위치가 DS에서 항상 타일 중심인 것은 아니다.** 원본에서 읽은 여섯 정지 중 하나는 두 축 모두 중심에서 `0x6cf`만큼 벗어난 위치에 120프레임 동안 머문다. `func_0204f794`는 구조상 `(tile << 13) + 0x1000`을 쓰므로, 호출자가 다른 값을 넘겼거나 두 번째 기록자가 배치했을 가능성이 있다. 실험: 포트의 주민을 그 셀에 놓고(`stand76.py`의 형태로 스냅샷을 찌르는 방식) `+0x5c`를 감시한다 -- 포트가 오프셋을 재현하면 두 프로듀서가 일치하고 그 셀이 특수한 것이며, 중심을 쓰면 실제 차이가 있고 살펴볼 곳은 호출자이다.
- **H: `func_0207c818`이 돌려주는 여섯 클래스는 여섯 성격(느긋함, 운동광, 무뚝뚝, 활발함, 보통, 도도함)이다.** 인덱스는 6으로 한정되고 각 클래스에는 고유한 추첨 함수 인자가 있다 [S: src/matched/func_0207c76c.c]. 실험: 생성된 마을 100개에 대해 클래스 인덱스와 뽑힌 주민 id를 기록하고, id가 서로소인 여섯 집합으로 분할되는지 확인한다.
- **H: `func_0207b594`의 "종 슬롯 열일곱 개"는 종 그룹(고양이, 개, 새 ...)이며, `func_0209bcd4` / `func_0209c380`은 종별 상한을 강제한다.** 루프 중첩은 8 x 17이고 허가 술어가 둘이다
  [H: source account: port/shim/game/villagers.c; direct ROM-source provenance unresolved]. 실험: `func_0209bcd4`와 `func_0209c380`을 디컴파일한 뒤 마을 50개를 생성하고 종 반복 횟수를 센다.
- **H: 이사 오기와 이사 가기는 주민 코드가 아니라 날짜 변경 루틴 `func_02040c90`가 구동한다.** 생성기 자체의 순서는 "생성, 그 다음 주민을 이사시키는 RTC 전진"이며 [H: source account: port/shim/gfx/pmflist.c; direct ROM-source provenance unresolved], `func_02040c90`는 날짜 변경 / 달력 갱신으로 식별되어 있다 [H: source account: port/tools/known_callees.txt; direct ROM-source provenance unresolved]. 실험: `ACWW_RTC_*` 날짜 롤오버에 걸쳐 `0x021e5a2c`의 레코드 여덟 개를 지켜보고 무엇이든 바뀌는지 본다.
- **H: 친밀도는 `0x7ec` 레코드 안의 바이트이며, 표정 선택의 `a2` 인자는 그로부터 유도된다.** `func_0204fb80`은 클래스별 테이블 안에서 `a2 * 8`로 여러 8바이트 레코드 중 하나를 선택한다 [H: source account: port/shim/game/exprpick.c; direct ROM-source provenance unresolved]. 실험: 긴 마을 실행 동안 `func_0204fb80`의 인자를 계측하고, `a2`를 말하는 주민 레코드 안에서 단조 변화하는 바이트와 상관시켜 본다.
- **H: `param * 0x4e`로 인덱싱되는 `data_020cd884`는 `0x4e`바이트 행(이름, 모델, 텍스처, 목소리)을 가진 주민 종 테이블이다.** 스트라이드와 33항목 한계는 측정되었다 [H: source account: port/shim/game/villagerface.c; direct ROM-source provenance unresolved]. 실험: 행 33개를 덤프하고 반복되는 내부 구조가 있는지 확인한다; 행 수를 `func_0207b594`의 열일곱 슬롯에 있는 종 수와 교차 확인한다.
- **H (미해결, 그리고 이것이 최우선 순위이다): 어느 도착 단계가 주민을 게이트하며, 무엇이 튜토리얼 홀드를 푸는가.** 두 체인이 서로 다르다. VILLAGER42의 체인은 `st/town48000.st`에서 `X`가 없는 패드 스크립트로 구동되었고, 패드가 버려진 채 최소 11,900 프레임 동안 닌텐도 DS 삽화 안에 머물렀으며, `X` 다음 `B`를 누르자 지워졌다
  [H: log/source account: `docs/log/cycle41-gameplay.md` VILLAGER42, `v42-V1`/`v42-V3`/`v42-V4`; receipt provenance unresolved]. SAVE43의 체인은 나중 빌드에서 `st/b55400.st`로부터 `X` 행 없이 구동되었는데, 홀드를 지나 있었고 주민이 그려져 걸어가 부딪히고 말을 걸 수 있었다 [H: log/source account: `docs/log/cycle42-save.md` SAVE43, `gp-D2`, `gp-D4`; receipt provenance unresolved].
  GAMEPLAY44는 위에 설명한 대로 마을 생성을 스냅샷 이후의 시계 조건에서 분리해 냈다.
  프롬프트를 지우는 정확한 도착 단계와 입력은 아직 분리해야 할 과제로 남아 있다. **추가 실험은 하나(ONE)의 빌드에서 각 방향으로 한 번씩 실행하는 것이다**: 두 스냅샷을 모두 재개하고, 각각을 두(BOTH) 패드 스크립트(`X` 행이 있는 것과 없는 것)로 구동하며, 홀드에 걸쳐 50 프레임마다 스틸을 찍고, 조건마다 아래 화면이 풀리는 프레임과 주민이 처음 나타나는 프레임을 기록한다 -- 조건 넷, 약 10분이며, 답은 네 조합 중 어느 것이 주민에게 도달하는가이다. 스틸마다 `0x021c749c`(플레이어의 실시간 위치, 위의 NAV42)를 엿본다: 패드를 버리는 홀드는 움직이지 않는 위치를 보이므로, 이것이 "홀드가 떠 있다"와 "스크립트가 놓쳤다"를 구분해 준다.
- **H: 주민 이동(걷기, 경로 탐색)은 가상 슬롯 25를 통해 `func_0202e0c8`의 프레임별 스텝 안에서 실행된다.** 그 슬롯은 레코드 접근자 `func_0208150c`가 적용되는 객체를 돌려준다 [H: source account: port/shim/game/villhouse.c; direct ROM-source provenance unresolved]. 실험: `tap-D59` 마을 회관 실행에서 슬롯 25의 반환값과 `func_0207945c`의 두 번째 인자를 계측한다.

## 관련 문서

- `../experiments/gameplay-walkthrough.md` -- 두 체인을 프레임 단위로, 주민이 그려진 SAVE43 스틸을 포함해 다룬다
- `town.md` -- 집 레코드는 마을 세이브 이미지의 일부이다
- `dialogue.md` -- 대화 머신이 주민에게 도달했을 때 주민이 하는 말
- `events-and-calendar.md` -- 생일과 날짜 변경 루틴
