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

**원본(ORIGINAL)에서 읽어 낸 주민 id는 ORACLE46 이전에 작성된 어떤 장부에서도 `0x80` 미만일 때만 신뢰할 수 있다**: `observer.lua`는 엿본(peek) 워드를 Lua의 `%d`로 출력했는데, 이는 비트 31이 켜진 모든 워드 -- id는 그 워드의 바이트 3이다 -- 를 `-2147483648`로 뭉개 버렸고, 이를 다시 읽으면 `128`이 된다. TUTORIAL45의 에뮬레이터 명단 `66, 128, 21, 128`과 `107, 94, 128, 128`은 게임이 아니라 그 결함이다 [E: same]. **그 에뮬레이터 행들은 철회(RETRACTED)되었다:
`docs/log/cycle41-gameplay.md`, O46-2.** 두 호출자 모두 이를 `void`로 선언하고 어느 쪽도 결과를 읽지 않으므로, 그 유일한 산출물은 주민 테이블이다
[S: func_0207b57c / func_0209e828, main, port/shim/game/villagers.c].

초기 선택 루프는 `func_0207c76c`이며 구조가 읽기 쉽다. 여덟 번 반복한다. 각 반복은 `func_0207c818(self, mask)`에 클래스 인덱스를 묻는다; 6 이상인 인덱스는 건너뛰므로 클래스는 여섯(SIX) 개이다 -- 게임의 성격 그룹이다
[S: func_0207c76c, main, src/matched/func_0207c76c.c]. 그 다음 `func_0207c8c8(self, idx, 1)`이 그 클래스에서 주민 하나를 뽑고, 결과가 `~local2`(중복 방지 장치)와 같으면 거부되며, 성공하면 `func_02081518`이 이를 `self + 0x7ec * i` -- i번째 집 레코드 -- 에 쓰고 `func_0207ca74`가 `self + 0x4060`에 기록한다
[S: func_0207c76c, main, src/matched/func_0207c76c.c]. 생성된 마을에서 값 `0x65`, `0x78`, `0x27`의 선택 세 건이 관측되었다
[E: port/BOOT-STATE.md, fifth pass 2026-08-27].

이사 오기는 생성만이 아니라 달력에 묶여 있다: 마을 디스패처의 생성 핸들러 다음에 "주민을 이사시키는 RTC 전진"이 오고, 그 다음 생성 후 동기화가 온다 [S: func_0209e6ec, main, port/shim/gfx/pmflist.c].

주민을 화면에 올리는 것은 매 세션 실행되는 별개의 체인이다. 모드 `0x2c`의 부팅 스크립트가 채널 `0xd0`를 연다; 그 init `func_02085558`은 야외 분기를 타고 스포너 `func_02085a30`을 호출하며, 스포너는 집 레코드 여덟 개를 순회하면서 현재 있는 각 주민마다 id `(i | 0xe000)`으로 채널(CHANNEL) `0x84`를 연다
[S: func_02085558 / func_02085a30, main, port/shim/game/villspawn.c]. 채널 `0x84`의 생성자 `func_ov068_0226da64`(ov068 데이터의 레코드 `0x022771a0`)가 `0xa10`바이트 주민 액터를 만들고, 그 init `func_0202e1fc`가 이를 `0x021d1d4c`의 매니저에 등록한다
[S: func_ov068_0226da64 / func_0202e1fc, ov068/main, port/shim/game/villspawn.c]. 매니저는 `{actor, id}` 쌍 여덟 슬롯이며 종류(kind)는 `0xe`이다
[S: port/shim/game/villspawn.c, port/shim/game/campos.c].

주민의 드로우 진입점은 정적 테이블이 아니라 객체 안에 보관된 멤버 함수 포인터(POINTER-TO-MEMBER)이다: `func_ov068_0226d770`은 `obj + 0x8b0`에서 8바이트 mwcc `{lo, hi}` 쌍을 읽어 이를 통해 호출하며, 그것이 null이면 `+0x5c`의 `Vec3`를 `+0x478`, `+0x484`, `+0x490`의 세 슬롯으로 복사하는 것으로 대체한다
[S: func_ov068_0226d770, ov068, port/shim/game/villdraw.c]. 이 쌍은 파생 init `func_ov068_0226d850`에서 `data_ov068_02276eb0`으로부터의 8바이트 복사로 바인딩되며, 그 ROM 내용은 `{0x0226d809, 0}` -- 즉 `func_ov068_0226d808`, Thumb -- 이다
[S: func_ov068_0226d850, ov068, port/shim/game/villbind.c]. 바인딩은 상태 기반이다: 상태 0의 진입이 바인딩하고 상태 1의 진입이 바인딩을 해제한다
[S: port/shim/game/villdraw.c, observed rebinds].

**이 쌍은 쓰이고, 그 다음 ROM이 의도적으로 지운다.** 마을 회관에서 걸어 나오는 구간에 `actor + 0x8b0`에 스토어 워치포인트를 걸면 정확히 세 번의 스토어가 나오고 그 이상은 없다:
`func_ov068_0226d850`이 pc `0x0226d874`에서 `{0x0226d809, 0}`을 쓰고(파생 init 자신의 `data_ov068_02276eb0`으로부터의 8바이트 복사), 두 번째(SECOND) 바인더 `func_ov068_0226cb00`이 자기 원본 `0x022770a8`에서 같은 쌍을 pc `0x0226cb16`에서 쓰며, 그 다음 `func_ov068_0226bb3c`가 pc `0x0226bb86`에서 `{0, 0}`을 쓴다 -- 풀 워드 `0x0213dd98`로부터인데, 이는 **autoload_2 `.data`**(`0x02138f80..0x0213fdc0`)이고 그 ROM 바이트는 `00000000 00000000`, 즉 mwcc의 정적 NULL 멤버 포인터이다. 따라서 `func_ov068_0226bb3c`는 드로우 멤버의 바인딩을 해제(UNBIND)하는 상태 진입이며, 드로우 슬롯이 보는 null은 잃어버린 쓰기가 아니라 ROM 자체의 값이다
[E: docs/log/cycle41-gameplay.md VILLAGER42, `v42-W2`; S: extract/adm-kr/arm9/unk_autoload_2.bin
+0x55558, config/adm-kr/arm9/delinks.txt]. vtable의 슬롯 0(`0x022771c0`)에 건 로드 워치포인트는 pc `0x01ffd4a0`에서 발화하므로, 디스패처는 파생 init을 실제로 가져와 실행한다
[E: `v42-W2`]. `villdraw.c`도 `villbind.c`/`villspawn.c`도 인터프리터 레지스트리에 없고 -- `port/shim/game/`은 `SERVICE_DIRS` 항목이 아니다 -- `FS_StartOverlay`는 이 경로에서 재배치 패스를 실행하지 않으므로, 그 세 워드 모두 출하된 그대로의 ROM 데이터이다
[S: port/tools/interp_registry.py, port/shim/fs/ovlreloc.c].

**이는 GAMEPLAY42의 "8바이트 복사가 객체에 도달한 적이 없다"를 철회한다.** 그 주장은 `ACWW_INTERP_PEEK` 판독 두 번에서 나왔다; 워치포인트는 복사가 두 번 도착함을 보여 준다
[E: docs/log/cycle41-gameplay.md VILLAGER42].

두 액터는 살아서(LIVE) 걸어 다니는(WALKING) NPC이다. `0x021d1d4c`의 매니저는 `{0x022a8f48, 0xe000}`과 `{0x022a8528, 0xe001}`을 담고 있으며, `actor + 0x5c` -- 객체 자신의 `VecFx32` -- 는 실행 사이에 움직인다: 주민 0은 프레임 55,600에 `(79.000, 0.125, 95.000)`, 60,600에 `(83.000, 0.125, 111.00)`, 68,200에 `(87.510, 0.125, 78.130)`으로 읽히고 `+0x68`은 그보다 한 걸음 뒤에 있다; 주민 1은 `x = 149..159, z = 83..95` 근처에서 같은 식으로 걷는다. 둘 다 지면 높이 `y = 0.125`에 머문다
[E: docs/log/cycle41-gameplay.md VILLAGER42, `v42-P1`, `v42-V4`, `v42-V5`]. GAMEPLAY42가 "같은 Vec3 세 번"으로 읽은 `+0x478`/`+0x484`/`+0x490` 삼중항은 대체 분기가 방금 거기에 써 둔 것일 뿐이다.

**집 문은 두 프로듀서 모두에서 열리며, 거주자는 집에 있을 수 있다 (ORACLE50).** 세 사이클 동안 들어가지 못한 주민 집은 하나(ONE)의 마을에 관한 사실이다. 전진(FORWARD) 공유 레시피의 마을 `0x8365` -- 포트와 에뮬레이터 레퍼런스가 명단 슬롯 여덟 개 `6b 5e 84 ff ff ff ff ff`와 건물 셀 17개까지 모두 동일하게 생성하는 마을 -- 에서 93행짜리 체인이 주민 1의 문 앞 **(61, 69)**까지 걸어갔고, 두(BOTH) 프로듀서 모두 안으로 들어갔다. 전환에서 다섯 프레임 차이가 났으며 같은 두 워드를 보였다: 대기 중인 바깥 위치 `0x021f69b8`은 양쪽 모두 `503808 512 564736`(그 문 앞)이 되고, `0x021f69d0`의 씬 요청은 같은 목적지 `65536 512 118784`가 된다. 안에서는 두 스틸 모두 방 안에 서 있는 주민을 보여 주며, 포트의 A 펄스는 이름표에 `사브리나`가 뜬 그녀의 인사말을 열었다. **GAMEPLAY48의 `이 몸은 밖에 계신다` -- 그 문에서의 "나는 밖(OUT)에 있다" 쪽지 -- 는 포트가 열지 못하는 문이 아니라, 그 타임라인에서 마을 `0xc66e`의 거주자가 외출 중이었던 것이다** [E: `docs/log/cycle41-gameplay.md`
ORACLE50 O50-3; runs `p50-door`, `e50-door`, `p50-enter`, `e50-enter`]. 액터 매니저에는 언제나 두(TWO) 명의 주민만 있고 마을에는 셋이 있다(GP50-1); 세 번째가 실내에 있는 그 주민이다.

**그리고 그것으로 한 명에게 찾아가기에 충분하다 (GAMEPLAY44).** `actor + 0x5c`는 플레이어의 실시간 위치 `0x021c749c`와 같은(SAME) 월드 공간에 있으므로, 액터의 타일은 플레이어와 똑같이 정확히 `x // 8192`이며, `port/tools/navlib.py`는 이제 매니저의 레이아웃 전체 -- `+0x00`부터 종류 0xe의 `{actor, id}` 슬롯 여덟 개와 `+0x40`부터 종류 0xd의 슬롯 네 개, 즉 `port/shim/game/villspawn.c` 자체의 `vill_mgr_dump`와 같다 -- 를 읽어 `navigate.py`에 대화 목표를 건넨다: 액터 타일의 걸을 수 있는 이웃 중 플레이어에게 가장 가까운 것을, 액터 쪽으로 다시 향하게 하며, 출입구 스윕은 없다. `port/tools/goto.py --to actor:<n>`은 매 반복의 자체 스냅샷에서 그 목표를 다시 해석하는데, 주민이 걷기(WALKS) 때문이다 -- 한 명은 다섯 번의 반복에 걸쳐 (76,47) -> (75,47) -> (77,45)로 움직였다 -- 그리고 플레이어가 그 타일에 서면 A를 한 번 누른다. 마르는 첫 펄스에 대답하고 A 펄스들은 대화를 세 줄 더 이어 간다
[E: `docs/log/cycle41-gameplay.md` GP44-2, `scratchpad/gameplay44/RECEIPTS.md`, runs
`TALK1-1`..`TALK1-5` and `g44-TALK`]. 이는 VILL42-4의 "도달(reach)" 후보를 닫는다: 스폰, 바인딩, 드로우에는 아무 문제도 없었다 -- **액터 자신의 위치를 겨냥한 걷기가 한 번도 없었던 것**이며, 세 사이클의 스윕은 씬 진입 위치라서 움직이지 않는 `0x021f69d4`를 겨냥하고 있었다.

**철회 두 건, 이 순서로, 그리고 이 문단이 그 주장에서 남은 것이다.** 이 페이지는 예전에 여기서 "아직 어떤 주민도 화면에 나온 적이 없으며, 그 이유는 도달이다"로 시작했다. **SAVE43이 그것을 철회했다**: 주민은 그려지고(ARE) 있으며, 플레이어 집 주변 에이커에서 한 명이 부딪힘과 `A`에 대화 상자로 응답하고, 너굴은 도착 연설 전체에 걸쳐 그려진다 [E: `docs/log/cycle42-save.md` SAVE43, `gp-D2`, `gp-D4`]. **GAMEPLAY44는 GAMEPLAY43의 시계 설명을 철회했다.** 동결 생성된 마을 스냅샷 하나에서, 동결 시계 조건과 전진 시계 조건이 같은 프레임에 걸쳐 모두 홀드된다; 프레임 048,000..051,400은 SHA-256이 동일하다. 마을 생성 차이가 GP43의 비교를 교란했던 것이다 [E:
`docs/log/cycle41-gameplay.md` GAMEPLAY44, GP44-1; `scratchpad/gameplay44/RECEIPTS.md`,
`g44-FRZ` and `g44-ADV`, 048,000..055,000]. `X` 다음 `B` 관측은 VILLAGER42 도착 체인에 속하는 것이며 동결 시계에 대한 일반 규칙이 아니다.

여전히 유효한 것은 두 액터가 살아서(LIVE) 걸어 다닌다(WALKING)는 점, 그리고 추적은 그들을 겨냥해야(AIMED) 한다는 점이다. **플레이어의 실시간 위치는 `0x021c749c`, 필드 카메라가 추적하는 벡터이다 -- 이 페이지가 아래에서 인용하는 `0x021f69d0` 레코드가 아니다(NOT).** 그 레코드는 씬 진입(SCENE-ENTRY) 위치이다: (145.000, 0.125, 179.875)로 읽히고 1,400 프레임을 걸은 뒤에도 같은 값으로 다시 읽히는 반면, 주민 자신의 `actor + 0x5c`는 두 판독 사이에 움직이며, 그것을 기준으로 겨냥한 세 번의 스윕은 아무도 만나지 못했다. NAV42는 플레이어를 두 곳에 둔 한 빌드의 스냅샷 두 개를 비교(diff)해 올바른 주소를 찾았고, 필드 카메라 자체의 원기둥 변환에 대해 세 가지 방법으로 확인했다;
`port/tools/navigate.py`는 그것으로부터 에이커 충돌 그리드 위의 걷기를 계획하고
`port/tools/goto.py`가 루프를 닫는다 [E: `docs/log/cycle41-gameplay.md` NAV42 and GP43-5,
`g43-P2`, `g43-P3`, `g43-T2`, `g43-T3`, `g43-T4`; VILLAGER42 `v42-P4`]

원본(ORIGINAL)도 같은 타임라인에서 주민을 보여 주지 않는다: 같은 패드 스크립트와 같은 두 번 탭 마을 레시피를 쓴 에뮬레이터 조건에서, 49,800..55,500의 20 프레임 동안 원본은 같은 삽화가 있는 같은 도착 튜토리얼 안에 있고 어느 프레임에도 주민이 없다
[O: docs/log/cycle41-gameplay.md VILLAGER42, `scratchpad/villager42/oracle-vill/`]. 이는 위의 두 해석 모두와 일관된다: 원본도 같은 홀드 안에 있다.

**과거의 관측들은 프롬프트에 관해 서로 달랐다 (STYLE 규칙 7).**
VILLAGER42는 패드 스크립트에 `X`가 없으면 11,900 프레임 뒤에도 삽화가 여전히 떠 있고, `X`(마스크 `0x400`) 다음 `B`가 이를 지운다고 측정했다
[E: VILLAGER42, `v42-V1`, `v42-V3`, `v42-V4`]. SAVE43의 체인에는 **`X` 행이 전혀 없었는데도** 홀드가 풀렸고, 그 뒤 주민이 그려져 부딪힐 수 있었다
[E: SAVE43, `gp-P1`..`gp-D4`]. 위의 GAMEPLAY44 같은 마을 비교는 시계 교란을 해소한다; 프롬프트를 열고 지우는 정확한 도착 이벤트는 별개의 질문으로 남아 있다.

주민 자체의 드로우 슬롯은 서비스 쪽의 id별 슬롯에 SRT를 밀어 넣을 뿐이며(`func_02012214 -> func_0205e954`); 모델 지오메트리는 NPC 모델 서비스 자체의 드로우 슬롯 `func_020500d8`(vtable `0x020dce48` 슬롯 9, `data_021c8184`의 객체)가 상태 3에서 요청 슬롯당 `func_0205510c` 한 번씩 제출한다
[S: func_020500d8 / func_02012214, main, port/shim/game/villmodel.c]. 따라서 주민이 자기 슬롯에서 GX 워드를 0개 내보내는 것은 정상이다
[S: port/shim/game/villmodel.c]. 광원 매니저가 수리된 뒤 주민 드로우는 프레임당 `0x8c8`-`0xa20` 워드를 내보내는 것으로 측정되었다
[E: port/BOOT-STATE.md, "Villagers were never missing"].

주민의 얼굴은 모델 id가 아니라 테이블 인덱스이다. `func_020808ec`는 `record + 0x7af`의 바이트를 읽어 `func_02082500`에 넘기고, 이는 `data_020cd884`를 `param * 0x4e`로 인덱싱한다; `func_020808d0`의 `>= 0x21`에 대한 대체값이 0이므로 테이블은 33항목으로 한정된다 [S: func_020808ec / func_02082500, main, port/shim/game/villagerface.c].

표정과 애니메이션은 가중치 추첨이다. `func_0204fb80`은 `0x020dc8b4`의 테이블의 테이블을 받아 `table[a3 - 1][a5]`를 선택하고, `a2 * 8`을 더해 `[0]`이 항목 배열이고 `[4]`가 개수인 8바이트 레코드에 도달한 뒤, 3바이트 항목들 -- `+0`과 `+1`이 두 출력, `+2`가 가중치 -- 을 순회하며 가중치를 누적해 추첨값을 넘는 항목을 찾는다
[S: func_0204fb80, main, port/shim/game/exprpick.c]. 추첨값은 `func_020e92d0(&0x021cb5a0, bound)`에서 오며, 상한은 `func_02073d90(*0x020ccf94)`에 따라 `0x60` 또는 `0x64`이다 -- 이 모드 검사는 통과할 때 마지막 세 항목도 건너뛴다 [S: func_0204fb80, main, port/shim/game/exprpick.c]. 실패 시에는 아무것도 쓰지 않고 함수가 0을 돌려주므로, 0을 돌려주는 스텁은 모든 주민이 호출자가 그 두 워드에 남겨 둔 값을 그대로 쓰게 만든다 [S: port/shim/game/exprpick.c].

근접 반응을 위한 주민 접근 스캔이 있다: `func_ov068_02266bac`은 `0x0222f458`의 ov003 슬롯 위치 getter를 호출하고, 이는 `p = 0x022617bc + (idx & 0xf) * 0x25c`를 읽어 `p + 0x204`의 `Vec3`를 복사하고 `p + 0x24d`의 부호 있는 바이트 -- 슬롯 점유자 id, 비어 있으면 `-1` -- 를 돌려주며, 그런 다음 `func_020ea990(pos, out) >= threshold`이면 슬롯을 거부한다
[S: func_ov068_02266bac / func_ov003_0222f458, ov068/ov003, port/shim/game/genfix.c]. `0x0225f76c`에 스트라이드 `0x24c`의 병렬 6슬롯 NPC 테이블이 있다
[S: sub_02227638, ov003, port/shim/game/genfix.c].

이 모든 것을 구동하는 ov003 슬롯 기구는 `__sinit_ov003_02237af4`가 `0x0225f76c`에 `0x24c` 슬롯 레코드 여섯 개를 구성한 뒤에야 실행된다; 그 초기화기가 건너뛰어졌을 때는 프레임별 슬롯 패스 전체가 죽어 있었다
[S: __sinit_ov003_02237af4, ov003, port/shim/game/exprpick.c].

주민 집은 텍스처 세트 넷과 애니메이션 둘을 쓰며, ov003 자체 풀에 이름이 있다:
`/str/npcHsTex/%c/house_%c%d%c.nsbtx`, `/str/npcHsTex/%c/light_%c%d.nsbtx`,
`/str/obj_house_i.nsbca`, `/str/obj_house_o.nsbca`
[S: ov003 image at 0x02239bf8, 0x02239c1c, 0x02239c40 and 0x02239c58,
port/shim/game/townhouses.c; the same four addresses `town.md` cites].

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

위 모든 행은 S 등급이며, 앞 표에 명시된 심 헤더에서 인용했다.

## 확인 방법

매니저 점유 프로브가 가장 저렴한 확인 방법이다: `port/shim/game/villspawn.c`는 모드가 바뀔 때마다 그리고 각 스폰 패스 뒤에 `0x021d1d4c`의 `{actor, id}` 슬롯 여덟 개를 출력하고, `port/shim/game/villpick.c`는 선택마다 한 줄(슬롯, 클래스, 주민 id)을 출력한다
[S: port/shim/game/villspawn.c, villpick.c]. 둘 다 `ACWW_TRACE_STATE=1`로 게이트된다
[S: port/shim/game/villspawn.c].

포트 한정 주의 사항에 유의한다: 네이티브(NATIVE) 경로에서 `func_0207b594`는 의도적으로 no-op이며 `villager placement SKIPPED`를 출력하므로, 네이티브 실행의 빈 주민 테이블은 게임이 아니라 포트의 결정이다 [S: port/shim/game/villagers.c]
[E: docs/log/cycle40-keyboard-gate-probe.md LONG40, "villager placement SKIPPED" at frame
19335]. 인터프리터(INTERPRETER) 경로에서는 ROM 자체의 `func_0207b594`가 실행된다
[S: docs/kb/hybrid/runtime.md via docs/log/cycle40-keyboard-gate-probe.md REG40].

## 가설

- **H: `func_0207c818`이 돌려주는 여섯 클래스는 여섯 성격(느긋함, 운동광, 무뚝뚝, 활발함, 보통, 도도함)이다.** 인덱스는 6으로 한정되고 각 클래스에는 고유한 추첨 함수 인자가 있다 [S: src/matched/func_0207c76c.c]. 실험: 생성된 마을 100개에 대해 클래스 인덱스와 뽑힌 주민 id를 기록하고, id가 서로소인 여섯 집합으로 분할되는지 확인한다.
- **H: `func_0207b594`의 "종 슬롯 열일곱 개"는 종 그룹(고양이, 개, 새 ...)이며, `func_0209bcd4` / `func_0209c380`은 종별 상한을 강제한다.** 루프 중첩은 8 x 17이고 허가 술어가 둘이다
  [S: port/shim/game/villagers.c]. 실험: `func_0209bcd4`와 `func_0209c380`을 디컴파일한 뒤 마을 50개를 생성하고 종 반복 횟수를 센다.
- **H: 이사 오기와 이사 가기는 주민 코드가 아니라 날짜 변경 루틴 `func_02040c90`가 구동한다.** 생성기 자체의 순서는 "생성, 그 다음 주민을 이사시키는 RTC 전진"이며 [S: port/shim/gfx/pmflist.c], `func_02040c90`는 날짜 변경 / 달력 갱신으로 식별되어 있다 [S: port/tools/known_callees.txt]. 실험: `ACWW_RTC_*` 날짜 롤오버에 걸쳐 `0x021e5a2c`의 레코드 여덟 개를 지켜보고 무엇이든 바뀌는지 본다.
- **H: 친밀도는 `0x7ec` 레코드 안의 바이트이며, 표정 선택의 `a2` 인자는 그로부터 유도된다.** `func_0204fb80`은 클래스별 테이블 안에서 `a2 * 8`로 여러 8바이트 레코드 중 하나를 선택한다 [S: port/shim/game/exprpick.c]. 실험: 긴 마을 실행 동안 `func_0204fb80`의 인자를 계측하고, `a2`를 말하는 주민 레코드 안에서 단조 변화하는 바이트와 상관시켜 본다.
- **H: `param * 0x4e`로 인덱싱되는 `data_020cd884`는 `0x4e`바이트 행(이름, 모델, 텍스처, 목소리)을 가진 주민 종 테이블이다.** 스트라이드와 33항목 한계는 측정되었다 [S: port/shim/game/villagerface.c]. 실험: 행 33개를 덤프하고 반복되는 내부 구조가 있는지 확인한다; 행 수를 `func_0207b594`의 열일곱 슬롯에 있는 종 수와 교차 확인한다.
- **H (미해결, 그리고 이것이 최우선 순위이다): 어느 도착 단계가 주민을 게이트하며, 무엇이 튜토리얼 홀드를 푸는가.** 두 체인이 서로 다르다. VILLAGER42의 체인은 `st/town48000.st`에서 `X`가 없는 패드 스크립트로 구동되었고, 패드가 버려진 채 최소 11,900 프레임 동안 닌텐도 DS 삽화 안에 머물렀으며, `X` 다음 `B`를 누르자 지워졌다
  [E: `docs/log/cycle41-gameplay.md` VILLAGER42, `v42-V1`/`v42-V3`/`v42-V4`]. SAVE43의 체인은 나중 빌드에서 `st/b55400.st`로부터 `X` 행 없이 구동되었는데, 홀드를 지나 있었고 주민이 그려져 걸어가 부딪히고 말을 걸 수 있었다 [E: `docs/log/cycle42-save.md` SAVE43, `gp-D2`, `gp-D4`].
  GAMEPLAY44는 위에 설명한 대로 마을 생성을 스냅샷 이후의 시계 조건에서 분리해 냈다.
  프롬프트를 지우는 정확한 도착 단계와 입력은 아직 분리해야 할 과제로 남아 있다. **추가 실험은 하나(ONE)의 빌드에서 각 방향으로 한 번씩 실행하는 것이다**: 두 스냅샷을 모두 재개하고, 각각을 두(BOTH) 패드 스크립트(`X` 행이 있는 것과 없는 것)로 구동하며, 홀드에 걸쳐 50 프레임마다 스틸을 찍고, 조건마다 아래 화면이 풀리는 프레임과 주민이 처음 나타나는 프레임을 기록한다 -- 조건 넷, 약 10분이며, 답은 네 조합 중 어느 것이 주민에게 도달하는가이다. 스틸마다 `0x021c749c`(플레이어의 실시간 위치, 위의 NAV42)를 엿본다: 패드를 버리는 홀드는 움직이지 않는 위치를 보이므로, 이것이 "홀드가 떠 있다"와 "스크립트가 놓쳤다"를 구분해 준다.
- **H: 주민 이동(걷기, 경로 탐색)은 가상 슬롯 25를 통해 `func_0202e0c8`의 프레임별 스텝 안에서 실행된다.** 그 슬롯은 레코드 접근자 `func_0208150c`가 적용되는 객체를 돌려준다 [S: port/shim/game/villhouse.c]. 실험: `tap-D59` 마을 회관 실행에서 슬롯 25의 반환값과 `func_0207945c`의 두 번째 인자를 계측한다.

## 관련 문서

- `../experiments/gameplay-walkthrough.md` -- 두 체인을 프레임 단위로, 주민이 그려진 SAVE43 스틸을 포함해 다룬다
- `town.md` -- 집 레코드는 마을 세이브 이미지의 일부이다
- `dialogue.md` -- 대화 머신이 주민에게 도달했을 때 주민이 하는 말
- `events-and-calendar.md` -- 생일과 날짜 변경 루틴
