# 주민
<!-- source: wiki/systems/villagers.md -->

**요약.** 마을에는 최대 여덟 명의 주민이 산다. 각 주민은 세이브 이미지 안에서 고정 스트라이드 레코드 하나를 차지하며, 각 레코드는 집 하위 레코드를 품고 있다: 저장소 안에서 주민과 집은 하나의 객체이다. 누가 이사 오는지는 생성 시점에 단 한 번, 여섯 클래스를 순회하며 중복을 거부하는 선택기(picker)가 결정한다; 누가 화면에 있는지는 매 프레임, 현재 있는 주민마다 액터 채널 하나를 여는 스포너(spawner)가 결정한다. 성격은 두 번 나타난다: 선택기가 어느 클래스에서 뽑았는가, 그리고 주민이 반응할 때마다 표정과 애니메이션을 고르는 가중치 테이블에서.

## 무슨 일이 일어나는가

여덟 개의 주민 레코드는 세이브 이미지 안 `0x021dc7a8 + 0x9284` = `0x021e5a2c`에 스트라이드 `0x7ec`로 놓이며, 각 레코드의 `+0x7a0`에 주민 하위 레코드가 있다
[S: func_02085a30, main, port/shim/game/villspawn.c]. 이 단일 스트라이드가 이 게임에서 집과 거주자가 분리 불가능한 이유이다: 집 배치기가 같은 배열을 인덱싱한다
(`for (j = 0; j < 8; self += 0x7ec, j++)`)
[S: func_0207bbb8, main, port/shim/game/houseplace.c].

새 마을에 누가 사는지는 `func_0207b594`가 결정하는데, 이는 매칭된 소스가 없는 `main`의 `0x1d0`바이트짜리 함수이다: 다섯 겹의 중첩 루프가 주민 슬롯 여덟 개와 종(species) 슬롯 열일곱 개를 순회하며, 각각이 허용되는지 `func_0209bcd4`와 `func_0209c380`에 묻고, `func_020644cc`로 뽑고, 결과를 `func_0209bd30`을 통해 쓴다
[S: func_0207b594, main, port/shim/game/villagers.c]. 두 호출자 모두 이를 `void`로 선언하고 어느 쪽도 결과를 읽지 않으므로, 그 유일한 산출물은 주민 테이블이다
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
| `obj + 0x8b0` | 드로우 PMF `{lo, hi}` 쌍 | `func_ov068_0226d850` | `func_ov068_0226d770` |
| `data_ov068_02276eb0` | PMF 원본 쌍 `{0x0226d809, 0}` | 정적 | `func_ov068_0226d850` |
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
- **H: 주민 이동(걷기, 경로 탐색)은 가상 슬롯 25를 통해 `func_0202e0c8`의 프레임별 스텝 안에서 실행된다.** 그 슬롯은 레코드 접근자 `func_0208150c`가 적용되는 객체를 돌려준다 [S: port/shim/game/villhouse.c]. 실험: `tap-D59` 마을 회관 실행에서 슬롯 25의 반환값과 `func_0207945c`의 두 번째 인자를 계측한다.

## 관련 문서

- `town.md` -- 집 레코드는 마을 세이브 이미지의 일부이다
- `dialogue.md` -- 대화 머신이 주민에게 도달했을 때 주민이 하는 말
- `events-and-calendar.md` -- 생일과 날짜 변경 루틴
