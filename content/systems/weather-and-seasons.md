# 날씨와 계절
<!-- source: wiki/systems/weather-and-seasons.md -->

**요약.** 계절은 달력 날짜의 순수 함수이다 -- 월(month)에 대한 12항목 점프 테이블이며, 열두 달 중 오직 네 달만 일(day)을 검사하고, 경계는 2월 25일과 5월·8월·11월 27일에 놓인다. 계절과 날씨가 함께 낮/밤 색상 테이블의 한 행(ROW)을 고르고, 시(hour)가 그 행 안에서 `0x20`바이트 뱅크 한 쌍(PAIR)을 -- 하나는 오전용, 하나는 오후용 -- 고르며, 게임은 현재 시의 뱅크를 다음 시의 뱅크로 두 개의 가중치로 블렌딩하므로 하늘과 조명은 계단식이 아니라 연속적으로 움직인다. 계절별 외형은 마을 자체 모델의 `w`/`s`/`f` 텍스처 변종으로도 나타나며, 눈사람은 그 자체로 하나의 채널이다.

## 무슨 일이 일어나는가

`func_02063bb4(month, day)`는 계절을 0, 1, 2, 3 중 하나로 돌려준다. 이것은 단일 `switch`이다 -- `cmp r0,#0xb` 다음에 `0x02063bc6`에 있는 12항목 Thumb 점프 테이블이 오고, 각 항목은 부호 확장되어 `0x02063bc6`에 더해지며, `bhi`가 11을 넘는 값을 모두 첫 번째 대상으로 보내기 때문에 월 0과 기본(default)이 같은 답을 낸다
[S: func_02063bb4, main, port/shim/game/season.c]. 각 분기(arm)는 다음과 같다: 월 1 -> 3; 월 2 -> `day <= 24`이면 3, 아니면 0; 월 3과 4 -> 0; 월 5 -> `day <= 26`이면 0, 아니면 1; 월 6과 7 -> 1; 월 8 -> `day <= 26`이면 1, 아니면 2; 월 9와 10 -> 2; 월 11 -> `day <= 26`이면 2, 아니면 3; 월 12와 기본 -> 3
[S: func_02063bb4, main, port/shim/game/season.c]. 달력에서 코드를 읽어 보면 3은 겨울, 0은 봄, 1은 여름, 2는 가을이며, 세 달마다 한 달만 일을 검사하기 때문에 분기 3/4, 6/7, 9/10이 점프 대상을 공유한다
[S: func_02063bb4, main, port/shim/game/season.c].

이 함수에 걸린 심볼 테이블의 함정에 주의해야 한다: dsd 테이블은 처음 `0x2a`바이트만 `func_02063bb4`라고 부르고, 점프 테이블 이후의 모든 것을 2~10바이트짜리 별개 심볼 열한 개(`func_02063be4` ... `func_02063c20`)로 등록해 두었는데, 각각은 case 분기 하나의 조각이다
[S: main symbols.txt, port/shim/game/season.c]. 계절 조각 하나를 따로 떼어 읽는 사람은 함수가 아니라 switch의 일부를 읽고 있는 것이다.

계절 옆에 더 세밀한 두 번째 맵이 있다. `func_0204fa8c(month)`는 더 큰 공간의 인덱스를 돌려준다: 월 1..7은 월을 그대로 돌려주고(ROM은 `r0`를 한 번도 다시 쓰지 않은 채 곧바로 에필로그로 분기한다); 월 8은 `func_0209df94`에서 얻은 바이트에 `func_0204fafc`를 적용한 결과에 따라 8 또는 9를 돌려주고; 월 9는 같은 검사를 뒤집어 10 또는 11을 돌려주며; 월 10..12는 `month + 2`를 돌려주고; 그 밖의 값은 1을 돌려준다
[S: func_0204fa8c, main, src/matched/func_0204fa8c.c and port/shim/game/seasonidx.c]. 따라서 열두 달이 열네 개 인덱스로 사상되며, 8월과 9월은 각각 둘로 갈라진다 -- 단순 계절 코드로는 구분하지 못하는 늦여름 변종과 늦9월 변종이다
[S: func_0204fa8c, main, port/shim/game/seasonidx.c]. 이 결과는 `0x020dc8b4`에 있는 `func_0204fb80`의 테이블의 테이블을 인덱싱한다 [S: func_0204fb80, main, port/shim/game/exprpick.c].

하늘과 조명은 하나의 메커니즘이다. `func_020bba14`는 `0x021f6cf0`의 낮/밤 색상 테이블을 채우는 유일한 함수이며, 마을 색상에서 눈에 보이는 모든 것이 이를 거친다: 래스터라이저는 각 텍셀을 조명이 적용된 버텍스 색상으로 변조하고, 그 색상은 NNS glb 광원 색상에서 오며, 그것은 광원 매니저의 원소들(채널 7, vtable `0x020de710`, `func_02065938`가 플러시)에서 오고, 그 원소들은 `func_020bbf00` = 바로 그 테이블을 샘플링한다
[S: func_020bba14, main, port/shim/game/envlight.c]
[E: port/BOOT-STATE.md, glb light words all four black before the repair].

명령어 단위로 해독하면 `func_020bba14`는 다음을 수행한다
[S: func_020bba14, main, port/shim/game/envlight.c]:

- `func_020bbb6c(0x021f75b0, &w1, &w2)`가 시계로부터 두 개의 보간 가중치를 만든다;
- `func_0209def4(clock)`가 시(hour)를 `clock[1]`에 쓴다;
- 시는 현재 시와 다음 시(mod 24)에 대해 `(hour % 12, am/pm)`으로 분리된다;
- `row = table_020d2364[*(u32 *)0x021f8ad4]` -- 계절과 날씨로 선택된 현재 하늘 행;
- `pair = (void **)(0x021f8af4 + row * 8)` -- `{am bank, pm bank}`, 시간당 `0x20`바이트;
- 현재 시의 항목이 다음 시의 항목으로 블렌딩되어 `0x021f8b14`의 세 `0x20`바이트 버퍼(`func_020bbcfc`가 할당) 중 버퍼 0에 들어간다; 다음 행(NEXT ROW)이 다를 때는 그 행이 버퍼 1로 블렌딩되고, 두 행이 `w2`로 버퍼 2에 블렌딩된다;
- `func_020bb18c(0x021f6f70, 0 or 1, the halfword at `+8` or `+0xa` of the result, 0 or 0xc0)`;
- `func_020bbf0c(w1, w2)`가 `0x021f6cf0`의 광원 색상 테이블을 채운다.

가중치 둘과 블렌드 둘이라는 형태가 핵심이다: 게임은 시간 경과와 행 변경 양쪽(BOTH)에 걸쳐 보간하므로, 계절이나 날씨 전환은 급격한 컷이 아니다
[S: func_020bba14, main, port/shim/game/envlight.c].

환경 객체의 init `func_020baa28`(vtable `0x020e69a4`, 슬롯 0)는 `/sky/*_bg_ncl.bin` 팔레트 네 개를 로드한다; 그 다섯 전역 변수가 잘못 바인딩되었을 때는 이 로드가 NULL 이름으로 실행되어 마을 전체가 검게 합성되었다
[S: func_020baa28, main, port/BOOT-STATE.md]
[E: port/BOOT-STATE.md, 38-42k pixels blended with full alpha and zero colour].

시(hour)는 하늘의 외형을 직접적이고 눈에 띄게 좌우한다: 시계가 새벽 4시를 가리키면 타이틀의 하늘은 별밭이다 [E: port/BOOT-STATE.md, `acww envlight: hour 0x00000004`]. 마을에서 하늘은 별도의 아핀(affine) 배경이다: 엔진 B 모드 1에 BG3 아핀(`BG3CNT = 0x6f02`)이며, 아핀 레이어가 렌더링되자 구름이 나타났다
[E: docs/log/cycle40-keyboard-gate-probe.md SKY40, `tap-D57` frame 37800].

날씨 상태 자체는 `func_02035dcc`가 리셋하며, ROM의 모든 호출자는 이를 `*(0x021c526c) + 0x2d0`로 호출한다 -- 즉 날씨는 필드 객체의 `0x2d0` 오프셋 하위 구조체이다
[S: func_02035dcc, main, port/shim/game/weather.c]. 그 호출자는 `func_02041c88`과 `func_020b90cc -> func_0208a2d8 -> func_020f44f8`이다
[S: main, port/shim/game/weather.c]. 필드 객체 자체의 init `func_02034d14`(vtable `0x020da334`, 슬롯 0)는 자신의 `+0x50`을 `0x021c526c`에 저장한다
[S: func_02034d14, main, port/shim/game/fieldptr.c].

눈은 이펙트가 아니라 채널이다: 채널 189는 눈사람(SNOWMAN)으로, `/snowman/snowball1.nsbmd`(모델 `SNW0`, id `0x022383ac`)와 `/snowman/snow_face.nsbmd`(모델 `SNW1`, id `0x022383c8`)를 바인딩하며, ov003 역시 자체 풀에 `sp_npc_snowman`이라는 이름을 갖고 있다
[E: port/BOOT-STATE.md, bind log] [S: ov003 pool words, docs/kb/modules/ov003-068.md]. 오랜 작업 동안 지형으로 취급되었던 53폴리곤 곡면은 알고 보니 눈덩이였다 [E: port/BOOT-STATE.md, "CHANNEL 189 IS THE SNOWMAN"].

비는 파일이 아니다(NOT). `m_rainA`, `m_rainB`, `m_splash`는 이미 로드된 `obj_taxi` 모델 안의 모델 노드 또는 애니메이션 이름이며, 파일 시스템에서 `*rain*`을 검색하면 BMG 메시지 파일 열두 개만 나온다 -- 따라서 빠진 비 에셋은 없으며 아무도 그것을 찾아 헤맬 필요가 없다
[S: port/VISIBLE-STATE.md, filesystem search]. ov003의 풀은 택시 객체들 옆에 이들의 이름을 두고 있다
[S: ov003 pool words, docs/kb/modules/ov003-068.md]. 비는 인터프리터 경로에서 프레임 4,500의 택시 실내에서 실제로 보인다(IS)
[E: docs/log/cycle40-keyboard-gate-probe.md GX40, off-D51].

계절별 외형은 에셋에도 들어 있다: ov003의 텍스처 이름은 `w`/`s`/`f` 변종을 갖는다 [S: ov003 pool words, docs/kb/modules/ov003-068.md].

## 어디에 있는가

| 함수 또는 심볼 | 모듈 | 역할 | 등급/출처 |
|---|---|---|---|
| `func_02063bb4` | main | 월 + 일 -> 계절 0..3 (12항목 점프 테이블) | S: port/shim/game/season.c |
| `func_0204fa8c` | main | 월 -> 14값 계절/이벤트 인덱스 | S: src/matched/func_0204fa8c.c |
| `func_0204fafc` / `func_0209df94` | main | 8월/9월 분할 검사와 그 입력 바이트 | S: port/shim/game/seasonidx.c |
| `func_020bba14` | main | 낮/밤 색상 테이블을 구성 | S: port/shim/game/envlight.c |
| `func_020bbb6c` | main | 시계로부터 두 개의 보간 가중치 | S: port/shim/game/envlight.c |
| `func_0209def4` | main | 시(hour)를 `clock[1]`로 읽어 들임 | S: port/shim/game/envlight.c |
| `func_020bbf0c` | main | 광원 색상 테이블 `0x021f6cf0`을 채움 | S: port/shim/game/envlight.c |
| `func_020bbf00` | main | 광원 원소들이 읽는 샘플러 | S: port/shim/game/envlight.c |
| `func_020baa28` | main | 환경 객체 init; `/sky/*_bg_ncl.bin` 로드 네 번 | S: port/BOOT-STATE.md |
| `func_02065938` | main | 광원 매니저의 원소들을 플러시(채널 7) | S: port/BOOT-STATE.md |
| `func_02035dcc` | main | 필드 `+0x2d0`에 대한 날씨 리셋 | S: port/shim/game/weather.c |
| `func_02034d14` | main | 필드 객체 init; `0x021c526c`를 공개 | S: port/shim/game/fieldptr.c |

## 읽고 쓰는 데이터

| 주소 또는 필드 | 의미 | 쓰는 쪽 | 읽는 쪽 |
|---|---|---|---|
| `0x02063bc6` | 계절 분기의 12항목 Thumb 점프 테이블 | 정적 | `func_02063bb4` |
| `0x020dc8b4` | 계절/이벤트 인덱스로 인덱싱되는 테이블의 테이블 | 정적 | `func_0204fb80` |
| `0x021f8ad4` | 하늘 행(ROW) 선택자(계절과 날씨) | 날씨/계절 갱신 | `func_020bba14` |
| `table_020d2364` | 행 인덱스 -> 행 | 정적 | `func_020bba14` |
| `0x021f8af4 + row*8` | `{am bank, pm bank}`, 시간당 `0x20`바이트 | 정적 | `func_020bba14` |
| `0x021f8b14` | `0x20`바이트 블렌드 버퍼 세 개 | `func_020bbcfc`가 할당 | `func_020bba14` |
| `0x021f6cf0` | 낮/밤 광원 색상 테이블 | `func_020bbf0c` | `func_020bbf00` -> 채널 7 |
| `0x021f6f70` | 하프워드 두 개짜리 하늘 색상 대상 | `func_020bb18c` | 렌더 |
| `0x021c526c` | 필드 데이터 포인터; 날씨는 `+0x2d0` | `func_02034d14` | `func_02035dcc` |
| `0x021f75b0` | 가중치의 근원이 되는 시계/환경 객체 | 환경 init | `func_020bbb6c` |

모든 행은 S 등급이며, 앞 표의 파일들에서 인용했다.

## 확인 방법

계절은 아무것도 실행하지 않고 확인할 수 있다: `arm9.bin`에서 `0x02063bc6`의 점프 테이블 항목 열두 개를 읽어 `0x2063c1e, 0x2063bde, 0x2063be2, 0x2063bee, 0x2063bee, 0x2063bf2, 0x2063bfe, 0x2063bfe, 0x2063c02, 0x2063c0e, 0x2063c0e, 0x2063c12`로 해석되는지 확인한다 [S: main, port/shim/game/season.c]. 한 분기는 `0x18`(2월)과 비교하고 세 분기는 `0x1a`(5월, 8월, 11월)와 비교하는데, 이것이 일 경계 규칙의 전부이다
[S: main, port/shim/game/season.c].

하늘에 대해서는 `ACWW_RTC_*`를 서로 다른 시각으로 설정해 실행하고 `acww envlight: hour <h>`를 지켜본다; 타이틀의 하늘은 4시에 별밭이다
[E: port/BOOT-STATE.md]. 마을 하늘에 한정하면, 마을 레시피의 프레임 37,800이 파란 하늘 위의 구름을 보여 준다 [E: docs/log/cycle40-keyboard-gate-probe.md SKY40, `tap-D57`].

## 가설

- **H: `0x021f8ad4`는 날씨만의 인덱스가 아니라 `(season, weather)` 결합 인덱스이며, `table_020d2364`는 이를 평탄화하는 테이블이다.** 이중 간접 참조 -- `0x021f8ad4`의 워드에서 `table_020d2364`를 거쳐 행으로 -- 는 2차원 조회를 1차원으로 접은 모습 그대로이다
  [S: port/shim/game/envlight.c]. 실험: 같은 날짜에서 `func_02063bb4`의 결과를 0..3 각각으로 강제하고 `*(u32 *)0x021f8ad4`와 그 결과 행을 기록한다.
- **H: 날씨는 프레임마다가 아니라 하루에 한 번, 계절별 확률 테이블에서 선택된다.** `func_02035dcc`는 선택자가 아니라 리셋(RESET)이며, 그 호출자들은 전환 지점이다
  [S: port/shim/game/weather.c]. 실험: 사흘짜리 `ACWW_RTC_*` 실행 동안 `0x021f8ad4`에 대한 모든 쓰기를 계측하고 세어 본다; 날짜 롤오버당 한 번의 쓰기라면 가설을 뒷받침한다.
- **H: `w`/`s`/`f` 텍스처 접미사는 winter / summer / fall이며, 봄은 접미사 없는 기본값이다.** 네 계절에 접미사가 셋이라는 점이 단서이다
  [S: docs/kb/modules/ov003-068.md]. 실험: 계절을 0..3 각각으로 강제한 채 `/bg/t%d/%04x.nsbtx`와 `/fg/**`의 모든 열기(open)를 기록하고 이름 집합을 비교한다.
- **H: `func_0204fa8c`의 8월과 9월 분할은 두 개의 불꽃놀이/축제 기간이며, `func_0204fafc`는 `func_0209df94`가 돌려주는 바이트에 대해 일(day-of-month) 또는 요일(day-of-week) 조건을 검사한다.** 오직 그 두 달만 갈라진다
  [S: port/shim/game/seasonidx.c]. 실험: `func_0204fafc`와 `func_0209df94`를 디컴파일하고 365일 전체에 대해 그 쌍을 평가한다.
- **H: 비는 파티클 시스템이 아니라, 택시/필드 모델 자체의 `m_rainA`/`m_rainB` 노드가 날씨 상태에 의해 활성화되어 그려진다.** 이들은 로드된 모델 안의 노드이다
  [S: port/VISIBLE-STATE.md]. 실험: 마을에서 날씨 워드를 각 값으로 강제하고 프레임당 큰 반투명 폴리곤 수를 센다.
- **H: 눈사람 채널(189)은 필드 씬이 무조건 여는 것이 아니라, 계절이 겨울이고 눈이 쌓였을 때 날씨/계절 갱신이 연다.** 채널은 존재하며 눈 모델을 바인딩한다 [E: port/BOOT-STATE.md]. 실험: RTC를 1월과 7월로 설정해 마을 레시피를 실행하고 채널 189가 열리는지 기록한다.
- **H: `func_020bbb6c`가 돌려주는 두 가중치는 (시간 내 경과 분)과 (행 전환 진행도)이며, 후자가 계절 변화를 하루 이상에 걸쳐 서서히 바뀌게 만드는 요인이다.** 두 번째 가중치는 두 행 블렌드에만 사용된다
  [S: port/shim/game/envlight.c]. 실험: 시간 경계와 계절 경계를 가로질러 `w1`과 `w2`를 기록한다.

## 관련 문서

- `town.md` -- 계절이 골라 쓰는 에이커 텍스처
- `events-and-calendar.md` -- `func_02063bb4`에 공급되는 날짜
- `villagers.md` -- 같은 `0x020dc8b4` 테이블이 주민 표정을 구동한다
