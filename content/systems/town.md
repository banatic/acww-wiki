# 마을
<!-- source: wiki/systems/town.md -->

**요약.** 마을은 96x96 타일 격자의 에이커들로, 새 세이브를 만들 때 한 번 생성된 뒤 시드에서 다시 유도되는 것이 아니라 세이브 이미지에 저장된다. 격자는 아이템을 담는다: 건물, 집터, 나무, 빈 마커 모두 에이커 바이트 옆의 레이어에 16비트 id로 들어 있다. 플레이어가 걷는 3D 세계는 그 격자를 원기둥에 감은 것으로, 에이커 하나가 32유닛마다 놓이며, 이것이 지평선이 통나무처럼 굴러가는 이유이다. 마을 자체의 이름은 두 번째 키보드 화면에서 플레이어가 입력한다; 생성 시점에 기본 이름이 찍히고 플레이어가 답하면 덮어써진다.

## 무슨 일이 일어나는가

세이브 이미지는 `0x021dc7a8`에 있고 길이는 `0x173fc`바이트이며, `func_020b5724`의 `MI_CpuCopy8`이 그곳으로 복사한다 [S: func_020b5724, main, port/shim/game/newgameprobe.c].
그 안에서 에이커 맵 객체는 `+0xd304`(`0x021e9aac`)에, 주민 집 레코드 여덟 개는 `+0x9284`(`0x021e5a2c`)에 스트라이드 `0x7ec`로 있다
[S: func_02085a30, main, port/shim/game/villspawn.c] [S: port/shim/game/newgameprobe.c].
이미지의 유효성 레코드는 `+0x173f8`(`0x021f3ba0`)에 있다; `func_0209f180`은 그 `+2` 바이트가 2이고 이미지의 바이트 0이 `0x32`일 것을 요구한다
[S: func_0209f180, main, port/shim/game/newgameprobe.c].

쓸 수 있는 세이브가 없는 부팅은 아무 메뉴 없이 마을을 생성한다. `func_020b5898`은 `func_020a1a40`을 통해 플래시 뱅크 둘을 폴링하고, `func_020b5724`는 판정을 자기 객체의 `+0x5e`에 쓰며, `func_020b56a8`이 그것을 읽는다; 판정 1 또는 4는 "쓸 수 있는 세이브 없음"을 뜻한다
[S: func_020b5898/func_020b56a8, main, port/shim/game/newgameprobe.c]. 그 분기는 `func_0209ef7c` -- 이미지 전체의 `MI_CpuFill8`, 플레이어 슬롯 init 넷, 하위 초기화기 28개 -- 를 호출한 뒤 `func_0209e6ec(save, 3)` = `func_0209ebec`를 호출하며, 이것이 지형(TERRAIN)을 만들고 기본 마을 이름을 찍는다
[S: func_0209ef7c/func_0209ebec, main, port/shim/game/newgameprobe.c]. `func_0209ebec`는 아직 플레이어가 존재하지 않으므로 의도적으로 플레이어 상태를 전혀 쓰지 않으며, 유효성 바이트를 다시 0으로 설정하는 것으로 끝난다 [S: func_0209ebec, main, port/shim/game/newgameprobe.c].

생성기 본체는 마을 디스패처 `func_0209e6ec`의 핸들러 2이다: `func_0204e728`을 통한 지형, 기본 마을 이름, 그 다음 주민을 이사시키는 RTC 전진과 `func_020a1038`의 세이브 삭제 경로를 그대로 따르는 생성 후 동기화
[S: func_0209e6ec, main, port/shim/gfx/pmflist.c]. `func_020a1320` / `func_020a13e8` 쌍은 생성기가 아니며(NOT), 이를 확립하는 데 세션 하나가 들었다: `func_020a1320`은 `0x021f3c30`의 새 게임 대기 워드를 1로 설정할 뿐이고, `func_020a13e8`의 상태 1 분기는 맵을 리셋(RESETS)한다 -- 모든 에이커 바이트를 `0x86`으로, 모든 아이템을 `0xfff1`로
[S: func_020a1320/func_020a13e8, main, port/shim/gfx/pmflist.c]. `0xfff1`은 ROM 전반에서 빈 아이템/타일 id이다 [S: docs/kb/modules/overlays-ov0xx.md].

생성 중 셀 쓰기는 네 함수로 된 관용구를 거친다: `func_0209c618`은 중첩된 `setv(cell(self, x, y), k)` 문 스무 개를 수행한 뒤 루프 셋을 돌리는데, 여기서 `cell`은 `func_0209cc30`, `setv`는 `func_0209d01c`, `getv`는 `func_0209d030`, 거부 검사는 `func_02037b14`이다 [S: func_0209c618, main, port/tools/known_callees.txt].

아이템은 맵 레이어의 16비트 id이다. 생성된 마을의 뱅크 0에서 측정: 상점 `0x500d`, 집 자리 `0x500a` 열한 개, 그리고 `0x5014`를 포함한 아이템 열다섯 개
[E: port/BOOT-STATE.md, fifth pass 2026-08-27]. 집 배치기 `func_0207bbb8`은 96x96 스캔을 돌리며 패스마다 `0x500a` 자리 하나를 주민 집 `0x5001`..`0x5008`로 바꾼다
[S: func_0207bbb8, main, port/shim/game/houseplace.c]
[E: port/BOOT-STATE.md, fifth pass 2026-08-27]. 쓰기는 `func_0207bbb8 -> func_0204e404 -> func_0204ef24(grid, item, x, y)`로 진행되며, `func_0204ef74`는 셀 하나 이상을 차지하는 집을 놓는 다중 타일 배치기이다
[S: func_0204e404/func_0204ef24, main, port/shim/game/genfix.c]
[S: func_0204ef74, main, port/BOOT-STATE.md sixth pass].

타일을 다시 읽는 것은 2단계 조회이다. `func_ov003_02227394`는 월드 위치를 받아 타일의 x와 z를 `fx32`(저장된 바이트를 `<< 12 >> 4`한 것)로 종류 바이트와 함께 돌려주며, 레코드가 발견되고 그 종류가 0이 아닐 때만 1을 돌려준다
[S: func_ov003_02227394, ov003, port/shim/game/fieldtile.c]. 레코드 조회 `func_ov003_022273f8`은 타일 워드를 4비트 그룹(비트 12-15)과 12비트 인덱스로 나누고, `0x02236b0c`의 8바이트 디스크립터를 그룹 바이트(`+4`)가 일치하고 개수 하프워드(`+6`)가 인덱스를 초과하는 것이 나올 때까지 순회한 뒤, 그 디스크립터의 기준 포인터에 `3 * index`를 더해 레코드를 계산한다; 첫 바이트가 0인 레코드는 거부된다
[S: func_ov003_022273f8, ov003, src/matched/func_ov003_022273f8.c]. 따라서 레코드는 3바이트 폭이다 [S: func_ov003_022273f8, ov003, src/matched/func_ov003_022273f8.c].

타일 종류는 같은 순서의 같은 상수 집합으로 여러 모듈에 반복되는 9항 술어로 분류된다: `0x26-0x2a`, `0x5d-0x61`, `0x2f-0x56`, `0x57-0x5b`, `0x66-0x68`, `== 0x69`, `0x6a-0x6c`, `== 0x6d`, `0xc8-0xcf`
[S: func_ov003_0220cd84 / func_ov072_022792e4, ov003/ov072, docs/kb/modules/overlays-ov0xx.md].
ROM 전체에서 열네 개 함수가 그 집합을 갖고 있으므로, 이는 한 함수의 사적 테이블이 아니라 마을의 타일 분류 체계이다
[S: docs/kb/modules/overlays-ov0xx.md, membership sweep over every ov003 target >= 0x40].

세계는 원기둥(CYLINDER)으로 그려지며, 이것이 게임의 굴러가는 통나무 지평선의 원천이다: 타일은 2.0유닛, 에이커는 32.0이고, 각 에이커 객체는 `Translate(col * 32, 0, 0)`에 `RotX(row * 0x2999)`를 합성한 위치에 놓이며, 카메라는 모드별 `ov006` 플래그 아래에서 `func_0203f844`에 의해 같은 프레임으로 회전된다
[S: func_0203f844, main, port/BOOT-STATE.md sixth pass] [E: port/BOOT-STATE.md, ~6,269
opaque pixels on the 3D layer]. 에이커별 렌더 객체는 `func_ov003_0221f270`이 만들며, 그 열 이동량은 `a2 * data_020ca0ec`이다
[S: func_ov003_0221f270, ov003, port/shim/game/acresetup.c].

에이커 지면 텍스처는 파일 시스템에서 `/bg/t%d/%04x.nsbtx`로 오며, `func_021077e8`이 이를 텍스처 핸들로 바꾼다 -- `func_02037608`이 `0x020376f4`에서 수행하는 것과 같은 변환이다
[S: func_ov003_0221fe34, ov003, port/shim/game/townsetup.c]. 마을 씬의 등록자는 `func_ov003_0221fe34`(핸들러 196의 init 슬롯인 `func_ov003_022207e0`의 세 번째 호출), `func_ov003_0221ffec`, `func_ov003_0221d76c`이다
[S: ov003, port/shim/game/townsetup.c, townhouses.c, townhouse3.c]. 두 번째 등록자의 `0x022200f0` 리터럴 풀은 건물의 에셋을 직접 명명한다:
`/str/npcHsTex/%c/house_%c%d%c.nsbtx`, `/str/npcHsTex/%c/light_%c%d.nsbtx`,
`/str/obj_house_i.nsbca`, `/str/obj_house_o.nsbca` -- 주민 집 텍스처와 조명 넷에 집 열기/닫기 애니메이션 둘
[S: ov003 image at 0x02239bf8/0x02239c1c/0x02239c40/0x02239c58,
port/shim/game/townhouses.c].

`ov003`은 야외 씬 모듈이며 리터럴 풀을 통해 자기 주제를 스스로 밝힌다: `/fg/` 트리 전체(`/fg/tree/cedar_mdl/`, `/fg/grass/{grassA-D,clover,redTurnip}`, `/fg/flower/{tulip,pansy,cosmos,rose,suzuran,rafflesia}`, `/fg/hole/`, `/fg/stone/`), 플레이어 집(`/str/plHsTex/home%c%c.nsbtx`), 지면(`m_grd_riv`, `m_grd_sea085`), 간판, 물고기와 곤충 [S: ov003 pool words, docs/kb/modules/ov003-068.md].

런타임에 마을은 채널이다. 채널 핸들러 테이블 포인터는 `0x021fd044`이고, 마을의 채널은 `0x22`이며, ROM의 디스패처 `func_020edc58`은 table -> entry -> `[entry]` -> `blx`를 읽는다 [S: func_020edc58, main,
docs/log/cycle40-keyboard-gate-probe.md CHAN40]. 지면은 채널 `0x0d`이고 마을 씬은 `0xc4 -> 0x0f -> 건물당 0xbd 하나`를 연다
[E: port/BOOT-STATE.md, sixth pass]. 채널 189는 마을 렌더러가 아니라 눈사람(SNOWMAN)이며, 오랜 작업이 이 오인 위에 놓여 있었다
[E: port/BOOT-STATE.md, bind log `/snowman/snowball1.nsbmd` id 0x022383ac].

인터프리터 경로에서 스크립트 실행은 프레임 37,500에 마을에 도달한다: 운전사가 마지막 대사를 하는 동안 플레이어는 마을 회관 앞에 서 있고, 오버레이 5, 36, 54, 120, 117이 로드되어 있다 [E: docs/log/cycle40-keyboard-gate-probe.md TOWN40, `tap-D56` frame 37500].
화면에 표시되는 마을 회관의 한국어 이름은 `마을사무소`이다
[E: docs/log/cycle40-keyboard-gate-probe.md LONG40, the five-option destination menu].
마을의 위 화면은 엔진 B 모드 1에 BG3 아핀(`BG3CNT = 0x6f02`) -- 하늘 -- 이며, 아핀 배경이 그려지자 마을 회관 위로 구름이 나타났다
[E: docs/log/cycle40-keyboard-gate-probe.md SKY40, `tap-D57` frame 37800].

## 어디에 있는가

| 함수 또는 심볼 | 모듈 | 역할 | 등급/출처 |
|---|---|---|---|
| `func_0209ebec`(`func_0209e6ec` idx 3) | main | 지형 구축 + 기본 마을 이름 | S: port/shim/game/newgameprobe.c |
| `func_0209ef7c` | main | 이미지 전체 채우기, 플레이어 init 4개, 하위 init 28개 | S: port/shim/game/newgameprobe.c |
| `func_0209c618` | main | `setv(cell(...))` 셀 쓰기 스무 개, 그 다음 루프 셋 | S: port/tools/known_callees.txt |
| `func_0209cc30` / `func_0209d01c` / `func_0209d030` | main | 셀 주소 / 값 설정 / 값 읽기 | S: port/tools/known_callees.txt |
| `func_0207bbb8` | main | 집 배치기, 96x96 스캔, 패스당 자리 하나 | S: port/shim/game/houseplace.c |
| `func_0204ef24` / `func_0204ef74` | main | 아이템 쓰기 함수 / 다중 타일 아이템 배치기 | S: port/shim/game/genfix.c |
| `func_ov003_02227394` | ov003 | 월드 위치 -> 타일 x, z, 종류 | S: port/shim/game/fieldtile.c |
| `func_ov003_022273f8` | ov003 | 타일 워드 -> 3바이트 레코드 | S: src/matched/func_ov003_022273f8.c |
| `func_ov003_0221f270` | ov003 | 에이커별 렌더 객체 설정 | S: port/shim/game/acresetup.c |
| `func_ov003_0221fe34` | ov003 | 마을 씬 등록자 1(`/bg/t%d/%04x.nsbtx`) | S: port/shim/game/townsetup.c |
| `func_ov003_0221ffec` | ov003 | 마을 씬 등록자 2(집 텍스처) | S: port/shim/game/townhouses.c |
| `func_020edc58` | main | 채널 핸들러 디스패처 | S: docs/log/cycle40-keyboard-gate-probe.md |
| `func_0203f844` | main | 카메라를 원기둥 프레임으로 회전 | S: port/BOOT-STATE.md |

## 읽고 쓰는 데이터

| 주소 또는 필드 | 의미 | 쓰는 쪽 | 읽는 쪽 |
|---|---|---|---|
| `0x021dc7a8` | 세이브 이미지 기준, `0x173fc`바이트 | `func_020b5724` | 모든 것 |
| `0x021e9aac`(세이브 `+0xd304`) | 에이커 맵 객체 | `func_0209ebec` | 필드/렌더 |
| `0x021e5a2c`(세이브 `+0x9284`) | 집 레코드 8개, 스트라이드 `0x7ec` | `func_0207bbb8` | `func_02085a30` |
| `0x021f3ba0`(세이브 `+0x173f8`) | 유효성 레코드; `+2`는 2여야 함 | 새 게임 경로 | `func_0209f180` |
| `0x021f3c30` | 새 게임 대기 모드 워드 | `func_020a1320` | `func_ov051_022610d4` |
| `0x02236b0c` | 8바이트 타일 그룹 디스크립터 | 정적 | `func_ov003_022273f8` |
| `0x021c80bc` | 필드 컨텍스트 포인터 | 필드 init | `func_0204f5e0` |
| `0x021c526c` | 필드 데이터 포인터; 구조체는 `+0x2d0` | `func_02034d14` | `func_02035dcc` |
| `0x021fd044` | 채널 핸들러 테이블 포인터 | 씬 설정 | `func_020edc58` |
| `data_020ca0ec` | 에이커 열 스트라이드 승수 | 정적 | `func_ov003_0221f270` |

등급: 세이브 오프셋은 S [port/shim/game/newgameprobe.c]; `0x02236b0c`는 S
[src/matched/func_ov003_022273f8.c]; `0x021c526c`는 S [port/shim/game/fieldptr.c];
`0x021fd044`는 S+E [docs/log/cycle40-keyboard-gate-probe.md CHAN40].

## 확인 방법

영수증이 남은 마을 레시피가 레퍼런스 실행이다. 사용자 정의 START9000 키, `ACWW_INTERP=1`, `ACWW_TOUCH` (221,181) `AT` 6900 `EVERY` 60 `REPEAT` 2, `ACWW_TOUCH2` (221,181) `AT` 24600 `EVERY` 60 `REPEAT` 2, 정지 48,000; 1,500프레임마다 스크린샷. 프레임 37,500은 마을 회관 앞의 플레이어를, 프레임 37,800은 구름 낀 하늘을 보여 준다
[E: docs/log/cycle40-keyboard-gate-probe.md TOWN40/SKY40/RECEIPT41, runs `tap-D56`,
`tap-D57`, `town-R1`].

그림이 아니라 격자를 확인하려면, 생성 후 `0x021e9aac`의 세이브 이미지에서 에이커 바이트를 읽고 아이템 레이어에서 `0x500a`(집 자리), `0x500d`(상점), `0x5001`..`0x5008`(주민 집)을 스캔한다; `0xfff1`은 비어 있음이다
[E: port/BOOT-STATE.md, fifth pass].

## 가설

- **H: 마을 배치는 셀 단위로 생성되는 것이 아니라 소수의 미리 만들어진 에이커 배열 집합에서 선택된다.** `func_0209c618`의 형태 -- 리터럴 `setv(cell(x, y), k)` 문 스무 개 뒤에 루프 셋 -- 는 절차적 생성기가 아니라 루프 기반 변형 패스가 딸린 템플릿 스탬프처럼 읽힌다 [S: port/tools/known_callees.txt]. 실험: `func_0204e728`과 `func_0209c618`을 읽고 스무 개 상수 중 어느 것이 리터럴이고 어느 것이 추첨에서 오는지 기록한다; 그런 다음 서로 다른 RNG 시드로 마을 셋을 생성하고 `0x021e9aac`의 에이커 바이트를 diff한다.
- **H: 리셋이 쓰는 에이커 바이트 `0x86`은 실제 에이커가 아니라 "미설정"이다.** 리셋은 모든 에이커를 `0x86`으로, 모든 아이템을 `0xfff1`로 채우며, `0xfff1`은 빈 id로 알려져 있다 [S: port/shim/gfx/pmflist.c] [S: docs/kb/modules/overlays-ov0xx.md]. 실험: 실제 생성 뒤 여전히 `0x86`인 에이커 바이트 수를 센다; 0이면 `0x86`은 센티널이다.
- **H: 9항 타일 술어는 타일을 물 / 절벽 / 길 / 풀 클래스로 분할한다.** 상수 대역이 연속적이고 서로소인데, 이는 종류 분류기의 모습이다 [S: docs/kb/modules/overlays-ov0xx.md]. 실험: `tap-D56` 마을에서 샘플링한 월드 위치 400곳에 대해 `func_ov003_02227394`의 종류 바이트를 계측하고, 각 대역을 그 위치의 스크린샷이 보여 주는 것과 상관시킨다.
- **H: 마을 이름은 세이브 이미지 안에서 유효성 레코드 근처의 고정 길이 UTF-16 필드로 저장된다.** `func_0209ebec`가 생성 시점에 기본 이름을 찍고 두 번째 키보드가 이를 덮어쓴다 [S: port/shim/game/newgameprobe.c]
  [E: docs/log/cycle40-keyboard-gate-probe.md TOWN40]. 실험: 서로 다른 이름을 입력해 마을 레시피를 두 번 실행하고 두 세이브 이미지를 바이트 단위로 diff하면, 달라진 구간이 그 필드이다.
- **H: `0x500a` 집 자리 열한 개는 마을의 합법적 집터 전체 집합이고 배치기는 그중 여덟을 고른다.** 집 레코드 여덟 개에 대해 자리 열한 개가 측정되었다
  [E: port/BOOT-STATE.md, fifth pass] [S: port/shim/game/villspawn.c]. 실험: 생성 시 모든 `0x500a` 좌표와 배치기가 끝난 뒤 모든 `0x5001`..`0x5008` 좌표를 기록한다; 두 번째 집합은 첫 번째의 부분집합이어야 한다.
- **H: 에이커는 한꺼번에가 아니라 카메라가 구르는 데 따라 행 단위로 파일 시스템에서 스트리밍된다.** kb는 생성 중 "acre archives streaming"을 기록하고 있다
  [E: port/BOOT-STATE.md, fifth pass]. 실험: `tap-D56`의 37,500과 48,000 사이에서 1,000프레임당 `/bg/t%d/%04x.nsbtx` 열기 횟수를 센다.

## 관련 문서

- `villagers.md` -- 집 레코드 여덟 개와 그곳에 누가 사는지
- `weather-and-seasons.md` -- 하늘 행과 계절별 텍스처 변종
- `player.md` -- 같은 세이브 이미지 안의 플레이어 배열
- `dialogue.md` -- 레시피가 도달하는 마을 회관 대화
