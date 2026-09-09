# 경제
<!-- source: wiki/systems/economy.md -->

**요약.** 이것은 위키에서 가장 덜 읽힌 시스템이며, 이 문서는 메커니즘을 지어내는 대신 그 사실을 그대로 밝힌다. 확립된 것은 돈이 쓰이는 대상의 형태이다: 아이템은 16비트 id이고 그 최상위 니블(TOP NIBBLE)이 카테고리이며, `0xfff1`은 "아이템 없음"이고, 상점과 메뉴 오버레이 전반에서 공유되는 비교 루틴군이 그 id들을 검사하기 위해 존재한다. 벨, 가격, 무 시장, 카탈로그는 아직 ROM에서 읽어 내지 못했다. 아래에서 이들에 관한 모든 내용은 읽어야 할 함수군과 실행해야 할 실험이 딸린 가설이다.

## 무슨 일이 일어나는가

아이템은 맵의 아이템 레이어에 저장되는 16비트 id이며, 빈 슬롯은 `0xfff1`이다
[S: func_020a13e8, main, port/shim/gfx/pmflist.c] [S: docs/kb/modules/overlays-ov0xx.md].
이 값은 맵에 국한된 매직 넘버가 아니다: ROM 전반의 빈 아이템/타일 id이며, 이 값으로 grep하면 한 가지 구성물을 쓰는 함수가 아니라 아이템 도메인의 함수들이 선택된다 -- 이 저장소가 한 번 잘못 주장했다가 나중에 제대로 측정한 사항이다
[S: docs/kb/modules/overlays-ov0xx.md, retraction 2026-09-02].

id의 상위 4비트는 카테고리(CATEGORY)이다. 배치 게이트 `func_0204bcf8 -> func_0204bcdc`는 `(*(u16 *)cell >> 12)`가 3 또는 4일 때만 셀을 받아들인다; `0xfff1`의 니블은 `0xf`이므로 손대지 않은 맵은 방의 256셀 전부를 거부한다
[S: func_0204bcdc, main, docs/kb/port/sequencer-and-modes.md]
[E: docs/kb/port/sequencer-and-modes.md, `cells[0..7] = fff1 ...`, 256 refused, channel `0x37`
never opens]. 마을의 고정 시설은 `0x5xxx` 대역을 쓴다: `0x5001`..`0x5008`은 여덟 채의 주민 집, `0x500a`는 집터, `0x500d`는 상점, 그리고 `0x500e`/`0x500f`/`0x5010`은 플라이스루 카메라가 상점에 도달하기 전에 순회하는 키들이다
[E: port/BOOT-STATE.md, fifth and sixth passes].

두 아이템 id를 비교하는 것은 공유 루틴 `func_0204bcdc` / `func_0204bc64`이며, `ov049`, `ov050`, `ov052`, `ov079`에 걸쳐 반복해서 나타난다 -- 한 경우에는 단일 함수 안에서 열두 번 -- 그리고 `src/matched/func_ov052_02261054.c`가 참조 구현이다
[S: docs/kb/modules/overlays-ov0xx.md]. 이 네 오버레이는 상점과 메뉴 대역이다: 오버레이 집합 테이블 `data_020df5ec`는 오버레이 90-146을 포괄하며 상점/메뉴로 설명된다
[S: data_020df5ec, main, docs/kb/port/sequencer-and-modes.md]. `ov050`은 특히 도착 시퀀스의 너굴(Nook) 쪽이다 -- 매칭된 트리에서 플레이어의 도착 이벤트 플래그를 지우는 단 두 곳 중 하나이다 [S: func_ov050_02262628, ov050, port/shim/game/spnpc.c].

`ov003`에는 알려진 멤버 세 개(`func_ov003_02220e20`, `func_ov003_022223bc`는 매칭됨, `func_ov003_0220c57c`는 미시도)를 가진 8분류 아이템 카테고리 분류기가 있으며, 모두 같은 체인 순서로 동일한 상수 집합을 공유한다: `0x6-0xb`, `0xc-0x11`, `0x12-0x19`/`0x1c`, `0x8a-0x8f`/`0x90-0x95`/`0x96-0x9b`/`0x9c-0xa3`/`0xa5`, `0x1a`, `0xa4`, `0x1d` [S: docs/kb/modules/overlays-ov0xx.md]. 플래그 여덟 개, 카테고리 여덟 개, 하위 바이트 범위의 id들에 대해 -- 따라서 하위 바이트는 니블이 갖지 않는 하위 타입을 담고 있다
[S: docs/kb/modules/overlays-ov0xx.md].

포트가 실행한 어떤 경로에서도 실내의 아이템 그리드에 쓰는 것은 없다. 쓰는 쪽은 `func_02037e44`이고 맵 수준 정문은 `func_0204f564`이다; ROM 전체에서 그 호출자 셋 중 세 번째(`func_ov004_0224522c`)는 매칭된 파일도, 심도, 심지어 스텁조차 없는 미탐사 ov004 코드이며, 관측된 부팅에서 채널 대역(`0x51`/`0x52`/`0x53`)이 한 번도 열리지 않는 클래스의 `ov004 0x022567c8` vtable 워드를 통해서만 도달 가능하다
[S: func_02037e44 / func_0204f564, main, docs/kb/port/sequencer-and-modes.md]. 따라서 경제의 가구 쪽 절반은 단지 문서화되지 않은 것이 아니라 진정으로 미탐사 영역이다
[S: docs/kb/port/sequencer-and-modes.md].

관측된 것 중 돈은 한 번 등장한다. 택시 대화에서 운전사는 `가서 어떻게 살려구 그래?`라고 묻고 두 선택지 답변 `돈 있어 / 조금밖에 없어`가 나온 뒤 `그럼 적어도 택시비 낼 정도는 있겠네!`라고 말한다 -- 택시 요금 대사이다
[E: docs/log/cycle40-keyboard-gate-probe.md LONG40, run `long-a`, frames 16,500 and 18,000].
그 답변이 플레이어에게 어떤 비용을 물리는지는 확립되지 않았다
[H: instrument the player slot across those frames and diff].

## 어디에 있는가

| 함수 또는 심볼 | 모듈 | 역할 | 등급/출처 |
|---|---|---|---|
| `func_0204bcdc` | main | 아이템 id 니블 검사; 니블 3 또는 4를 허용 | S: docs/kb/port/sequencer-and-modes.md |
| `func_0204bcf8` | main | 이를 호출하는 배치 게이트 | S: docs/kb/port/sequencer-and-modes.md |
| `func_0204bc64` / `func_0204bc7c` | main | 형제 id 비교 루틴 | S: docs/kb/port/sequencer-and-modes.md |
| `func_ov052_02261054` | ov052 | 비교 루틴군의 참조 구현 | S: docs/kb/modules/overlays-ov0xx.md |
| `func_ov003_02220e20`, `func_ov003_022223bc` | ov003 | 8플래그 아이템 카테고리 분류기 | S: docs/kb/modules/overlays-ov0xx.md |
| `func_02037e44` | main | 실내 아이템 그리드 쓰기 함수 | S: docs/kb/port/sequencer-and-modes.md |
| `func_0204f564` | main | 그 맵 수준 정문 | S: docs/kb/port/sequencer-and-modes.md |
| `func_0204ef24` / `func_0204ef74` | main | 마을 아이템 쓰기 함수 / 다중 타일 배치 함수 | S: port/shim/game/genfix.c |
| `data_020df5ec` | main | 오버레이 90-146(상점/메뉴)의 오버레이 집합 테이블 | S: docs/kb/port/sequencer-and-modes.md |
| `func_ov050_02262628` | ov050 | 도착 시퀀스의 너굴 쪽 | S: port/shim/game/spnpc.c |

## 읽고 쓰는 데이터

| 주소 또는 필드 | 의미 | 쓰는 쪽 | 읽는 쪽 |
|---|---|---|---|
| 아이템 셀(16비트) | `nibble:category, low 12 bits:id` | `func_0204ef24`, `func_02037e44` | `func_0204bcdc` |
| `0xfff1` | 빈 아이템/타일 id | `func_020a13e8` 상태 1 리셋 | 모든 배치 게이트 |
| `0x5001`..`0x5008` | 마을 아이템 레이어의 주민 집 | `func_0207bbb8` | 카메라 경유점, 마을 씬 |
| `0x500a` | 집을 기다리는 집터 | 생성 | `func_0207bbb8` |
| `0x500d` | 상점 | 생성 | 플라이스루 카메라 |
| `data_020df5ec` | 상점/메뉴 오버레이의 오버레이 집합 | 정적 | 오버레이 로더 |

등급: 셀 레이아웃과 `0xfff1`은 S
[docs/kb/port/sequencer-and-modes.md, port/shim/gfx/pmflist.c]; `0x5xxx` 값들은 E
[port/BOOT-STATE.md].

## 확인 방법

아직 경제 레시피는 없다. 저렴한 출발점 두 가지는 다음과 같다: (1) 마을 레시피의 프레임 37,500에서 마을 안의 `func_0204bcdc` 인자를 계측하고, 생성된 마을의 아이템 레이어에 실제로 존재하는 니블의 히스토그램을 만든다
[E: docs/log/cycle40-keyboard-gate-probe.md TOWN40, `tap-D56`]; 그리고 (2) `src/matched/func_ov052_02261054.c`를 읽은 뒤 파티션에서 `bl 0x204bcdc`를 grep하여 아이템 id의 모든 소비자를 열거한다 [S: docs/kb/modules/overlays-ov0xx.md].

경제 측정 전반에 적용되는 상시 주의 사항에 유의한다: 포트는 진실이 아니라 계측 도구이며, 포트에서만 관측된 값은 오라클이 동의하거나 소스가 설명하기 전까지 E 등급이다 [S: wiki/README.md].

## 가설

이 절이 이 문서의 본체이다. 각 항목은 무엇을 읽어야 하고 무엇이 결론을 내릴지를 밝힌다.

- **H: 벨은 `0x249c` 플레이어 슬롯 안의 32비트 필드이며, 지갑과 은행은 그런 필드 두 개이다.** 플레이어 슬롯은 크고, 지금까지 매핑된 유일한 영역은 `+0x23f8`의 이벤트 비트필드뿐이다 [S: port/shim/game/newgameprobe.c]. 실험: 라이브 실행에서 플레이어 슬롯을 저장하고, 아이템 하나를 판 뒤, 다시 저장하고 diff한다 -- 판매 가격만큼 변한 필드가 지갑이다.
- **H: 아이템 id의 최상위 니블은 작은 열거형(가구, 의류, 도구, 문구, 고정 시설, 집 마커, 없음)이며, 니블 5는 "마을 고정 시설", 3과 4는 "배치 가능한 오브젝트"이다.** 3과 4만 허용하는 게이트는 측정되었고, 관측된 모든 마을 고정 시설은 `0x5xxx`이다 [S: docs/kb/port/sequencer-and-modes.md] [E: port/BOOT-STATE.md]. 실험: 생성된 마을의 전체 아이템 레이어와 가구가 놓인 방 하나를 덤프하고 니블의 히스토그램을 만든다.
- **H: 가격은 공식이 아니라 아이템 테이블의 아이템별 필드이며, 판매 가격은 그 값의 고정 비율이다.** 8플래그 분류기는 아이템별 값 위에 카테고리별 규칙이 얹혀 있음을 시사한다 [S: docs/kb/modules/overlays-ov0xx.md]. 실험: 아이템 테이블을 찾아(`../data/items.md` 참고) 행 스트라이드를 읽고, 행 안의 16비트 필드가 알려진 게임 내 가격에 비례하는지 확인한다.
- **H: 무 시장은 날짜 변경 루틴 `func_02040c90`가 매일 다시 계산하는 가격이며, 그 안의 다섯 `MI_CpuCopy8` 블록 중 하나가 어제의 가격을 이력 슬롯으로 옮긴다.** 발견된 유일한 일별 재작성 안에 블록 복사 다섯 개가 있다
  [S: port/tools/known_callees.txt]. 실험: 각 복사의 원본과 대상을 명명한다; 그런 다음 `ACWW_RTC_*` 날짜 롤오버를 여러 번 실행하고, 하루에 한 번 바뀌며 일주일 길이의 이력을 갖는 값을 찾는다.
- **H: `/fg/grass/redTurnip`은 무의 필드 모델이며, 따라서 무는 인벤토리에만 보관되는 것이 아니라 꽃처럼 맵 아이템으로 배치된다.** ov003의 풀은 풀과 꽃 옆에 그 이름을 두고 있다 [S: docs/kb/modules/ov003-068.md]. 실험: 라이브 실행에서 무를 심고 아이템 레이어에서 `0xfff1`이 아닌 새 셀을 찾는다.
- **H: 카탈로그는 플레이어 슬롯 안의 비트셋으로, 카탈로그에 등록된 아이템당 1비트이며 아이템을 처음 얻을 때 기록된다.** 비트셋은 게임이 이미 진행도에 쓰는 방식이다
  [S: port/shim/game/spnpc.c]. 실험: 새 아이템 하나를 얻는 전후로 플레이어 슬롯을 diff하고 안정된 오프셋에서 뒤집힌 단일 비트를 찾는다.
- **H: 상점은 오버레이 상주형이다: 구매와 판매는 전적으로 90-146 오버레이 대역 안에서 실행되며, 그 함수들 중 하나에 있는 `func_0204bcdc`의 열두 호출 지점은 상점의 재고 필터이다.** 그 대역은 상점/메뉴로 설명되고 비교 루틴군이 그곳에 있다
  [S: docs/kb/port/sequencer-and-modes.md, docs/kb/modules/overlays-ov0xx.md]. 실험: 인터프리터 경로에서 상점에 도달하고(마을 레시피는 현재 마을 회관에서 멈춘다) 어떤 오버레이가 마운트되는지 기록한다.
- **H: 지금까지의 모든 실행에서 실내 아이템 그리드가 비어 있는 것은 쓰기 함수가 고장 나서가 아니라, `func_ov004_0224522c`를 소유한 클래스가 채널을 한 번도 열지 않기 때문일 뿐이다.** 그 체인의 다른 모든 고리는 실행된다 [S: docs/kb/port/sequencer-and-modes.md]
  [E: docs/kb/port/sequencer-and-modes.md, "Every link runs"]. 실험: 채널 `0x51`/`0x52`/`0x53`을 강제로 열고 `placed=`를 다시 확인한다.
- **H: 택시 요금 대사는 분위기용이며 도착에는 비용이 들지 않는데, 그 시점에 플레이어는 벨이 없기 때문이다.** 대화로만 관측되었다
  [E: docs/log/cycle40-keyboard-gate-probe.md LONG40]. 실험: `long-a` 레시피의 프레임 16,000-20,000에 걸쳐 플레이어 슬롯을 계측하고 감소하는 필드가 있는지 찾는다.

## 관련 문서

- `town.md` -- 이 id들이 사는 아이템 레이어
- `player.md` -- 지갑이 있으리라 추정되는 플레이어 슬롯
- `events-and-calendar.md` -- 무 가격이 올라탈 날짜 변경 루틴
- `../data/items.md` -- 아이템과 가구 테이블 자체
