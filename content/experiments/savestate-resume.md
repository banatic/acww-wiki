# 세이브스테이트와 재개: 늦은 프레임에 10분 대신 1분 만에 도달하기
<!-- source: wiki/experiments/savestate-resume.md -->

**상태: 실행됨.** 인터프리터 실행을 프레임 N에서 스냅샷하고, 그 파일에서 재개하면, 재개된
실행은 N 이후의 모든 프레임에서 그것을 쓴 실행과 **바이트 단위로 동일**하다. 이것이
마을, 마을 회관, 그 밖에 프레임 24,000을 넘어선 무엇에 관한 실험이든 감당할 수 있게
만드는 계측 장치다.

## 목적

이 위키의 모든 늦은 관측은 전체 재생으로 값을 치러 왔다: 두 번 탭 마을 레시피는 첫
흥미로운 프레임까지 약 750초가 들고, 세 가지 변형이 필요한 질문은 아무것도 배우지 못하는
벽시계 한 시간이 든다. 스냅샷은 그 비용을 한 번으로 옮긴다. 하지만 스냅샷은 그것에서
재개하는 것이 **정확**할 때에만 유용하다 -- 단지 비슷할 뿐인 재개는 이후의 모든 비교를
그 차이가 검사 중인 변경에서 왔는지 스냅샷에서 왔는지에 대한 논쟁으로 바꿔 놓는다.
그래서 여기서의 기준은 `ncc`가 아니라 `exact-rgb`이며, 아래의 영수증이 그것을 얻어 낸다.

## 스냅샷이란 무엇인가

스냅샷 파일은 세 가지를 담는다 [H: source account: `port/platform/state.c`; `docs/kb/hybrid/savestate.md`
sections 1 and 3; direct ROM-source provenance unresolved]:

1. **매핑된 NDS 영역 일곱 개** -- `0x02000000`의 메인 RAM(4 MB, `0x02400000`과
   `0x027f0000` 시스템 RAM 창은 같은 매핑의 뷰이므로 한 번만 나열), `0x027e0000`의
   DTCM(64 KB, 자체 할당), `0x04000000`의 I/O 페이지, `0x05000000`의 팔레트,
   `0x06000000`의 VRAM(8.6 MB), `0x07000000`의 OAM, 그리고 `0x30000000`의 39 MB
   미배치 심볼 아레나. 페이지는 4 KB 단위 제로 비트맵과 함께 저장되므로, 52 MB의 주소
   공간이 약 4.7 MB의 파일이 된다.
2. **18개 등록자의 이름 붙은 블롭 113개**(RTC42 이후 20개 등록자의 118개) -- 프레임을
   넘어 게임 상태를 나르며 NDS 메모리에서 아무것도 다시 만들어 내지 못하는 호스트 쪽
   정적 변수들: 프레임 카운터, 틱 누적기, 인터프리터의 합성 스캔라인 위상과 IRQ 스택,
   지오메트리 엔진의 레지스터 파일 전체(I/O 페이지가 공개하지 않는 30개 선언), GX FIFO
   파서의 위치, 오버레이 상주 테이블, PXI 응답 큐, 사운드 서비스의 소유권 상태 머신,
   스크립트된 키 위상. 서브에이전트의 영수증을 채취할 때는 111개였고, SAVE41의 병합된
   트리에서는 113개였으며 -- RTC42가 시계의 부팅 시각, 동결 플래그, 결정 플래그를 더한
   이후로는 **20개 등록자의 118개**다
   [H: log/source account: `docs/kb/hybrid/savestate.md` section 3; `docs/log/cycle41-gameplay.md` RTC42, item 6,
   whose savestate pair is 21/21 identical with the clock coming from the blob; receipt provenance unresolved]. 아래의
   모든 영수증은 113에서 채취되었고 `.st` 파일은 어차피 다른 빌드에서는 거부되므로, 이
   개수는 포맷이 아니라 빌드에 관한 사실이다(TOUCH41 샘플러의 `tp_auto_on` /
   `tp_frequence`와 `raster3d.c`의 `ever`는 병합 중에 등록되었다)
   [H: source account: `docs/log/cycle40-keyboard-gate-probe.md` SAVE41; direct ROM-source provenance unresolved].
3. **살아 있는 스레드마다 인터프리터 레지스터 파일 하나.** ROM 스레드는 Windows 파이버이며,
   파이버가 멈추는 유일한 곳은 `OS_LoadContext` 안의 `SwitchToFiber`이므로, 일시 중단된
   파이버의 호스트 스택은 항상 정확히 인터프리터 프레임 **하나** 깊이이고 그 아래의 모든
   것은 NDS 메모리에 있다 [H: source account: `port/shim/os/thread.c`; `docs/kb/hybrid/savestate.md` section 5; direct ROM-source provenance unresolved].

헤더는 **링크를 고정한다**: 이미지 베이스, PE TimeDateStamp, `SizeOfImage`,
`AddressOfEntryPoint`, 디스크상의 exe 크기, 그리고 인터프리터 레지스트리의 항목 수.
로드는 여섯 가지 모두를 비교하고 어느 하나라도 다르면 이름을 들어 거부하는데, 이것이
막는 실패는 오래된 파일이 아니라 게임 버그처럼 보일 것이기 때문이다. 다시 링크하면,
이전의 모든 스냅샷은 거부된다 [H: source account: `docs/kb/hybrid/savestate.md` section 5; direct ROM-source provenance unresolved].

## 캡처가 아니라 재구성되는 것

파이버(호스트 스택은 파일에 쓸 수 없다); 모든 Win32 핸들 -- 창, 그 DC와 DIB, 워치독
스레드, 열여섯 핸들짜리 파일 캐시(`romfs.c`는 모든 읽기 전에 절대 위치로 seek하므로
파일 위치를 나를 필요가 없다); 인터프리터의 훅과 호스트 본체 레지스트리, 로드 지점 전에
`acww_interp_boot`가 다시 설치하며, 이것이 로드 지점이 그 자리에 있는 *이유*다; `.fun` /
`.ovl` / `.dark` 사이드 테이블; 트램폴린 풀의 바이트, 해시 테이블에서 다시 방출되어
`call rel32` 변위가 이 이미지의 것이 되도록 함; 그리고 가상 카트리지, 그
`acww_romfs_mount()`는 재개된 실행이 결코 도달하지 않는 호출자(`CARD_Init`) 정확히 하나만
가지므로 로드 경로가 명시적으로 호출한다
[H: source account: `docs/kb/hybrid/savestate.md` section 4; direct ROM-source provenance unresolved].

환경에서 파생된 캐시는 다시 읽히므로, **로드하는 실행은 동작을 바꾸는 모든 것에 대해
저장한 실행과 같은 `ACWW_*` 환경을 써야 한다** -- `ACWW_RTC_DATE`와 `ACWW_RTC_TIME`이
날카로운 사례다. 스크립트된 키 위상은 의도된 예외로서 블롭으로 운반되므로, 재개된 실행은
다르게 설정된 실행이 아니라 저장한 실행을 재현한다 [H: source account: `docs/kb/hybrid/savestate.md` section 4; direct ROM-source provenance unresolved].

## 거부 규칙 -- 계측 장치가 하기를 거절하는 것

이들 각각은 나중에 미묘하게 실패할 스냅샷을 만드는 대신 아무것도 쓰지 않고 이유를
말한다 [H: source account: `docs/kb/hybrid/savestate.md` sections 5, 6, 8; direct ROM-source provenance unresolved]:

| 거부 | 이유 |
|---|---|
| 인터프리터 호출 체인이 정확히 한 프레임 깊이가 아닌 파이버 | 그 레지스터 파일은 재개가 복원할 수 있는 것이 아니다. **모든 프레임이 합법적인 저장 지점은 아니다** -- 6,000과 24,000은 둘 다 한 번에 성공했다; 6,061과 6,150 사이에서 표본한 열 프레임은 모두 거부되었다. 거부는 흔하며 결함이 아니다: 다른 프레임을 고른다 |
| 여섯 헤더 필드 중 어느 하나라도 빌드 정체성 불일치 | exit 9, 두 정체성을 모두 출력. exe의 **크기가 바뀌지 않았고** 타임스탬프와 진입점도 바뀌지 않은 재링크에서 측정됨 -- 크기만 검사했다면 놓쳤을 사례 |
| 다시 쓰인 호스트 워드에서 정규화해 빼내야 할 반환 지점 | 호스트 호출 도중의 프레임을 재개하면 그 호출을 다시 실행하게 된다; `acww_interp_cpu_resume_image`는 프레임이 *가지게 될* 상태를 쓰며, 추측하는 대신 거부한다 |
| `0x20000000`에 자리 잡지 않은 트램폴린 풀 | ROM은 풀 주소를 스냅샷이 캡처하는 RAM에 저장하므로, 풀 베이스는 정체성의 일부다 |

알려진 빈틈 두 가지, 아무도 걸려 넘어지지 않도록 명시한다: `ACWW_SAVE`의 플래시
이미지는 이름 붙은 파일의 `MapViewOfFile`이므로 **복사가 아니라 공유**다 -- 재로드는
파일을 지금 있는 그대로 본다(스크립트된 레시피들은 `ACWW_SAVE`를 해제한다); 그리고
환경 변수로 게이트되는 몇몇 일회성 동작(`ACWW_GENTOWN`, `ACWW_REQ_SCENE`, `ACWW_DEMO_OV4`,
`ACWW_LOAD_OVL`, `ACWW_FORCE_CHAN`, `ACWW_FORCE_FIELD`, 새 게임 프로브)은 운반되지 않으며
같은 변수가 설정된 로드에서 다시 발화할 것이다 [H: source account: `docs/kb/hybrid/savestate.md` sections 5 and 3; direct ROM-source provenance unresolved].

## 레시피

두 변수 모두 **절대** 경로를 받는다: `run_direct.py`는 exe를 cwd `port/build`로 띄우므로,
저장소 상대 경로는 엉뚱한 디렉터리를 기준으로 해석되어 전체 실행이 끝난 뒤 늦게 저장이
실패한다 [H: source account: `docs/kb/hybrid/savestate.md` section 7; direct ROM-source provenance unresolved]. 이들은 DIAGNOSTIC 실행이지 프론티어
주장이 아니다(B38).

OFF 대조, 6,000에서 저장(`off-recipe.md`의 환경):

    python -B scratchpad/cycle40/run_direct.py st-off-save ACWW_INTERP=1 \
      ACWW_TOUCH_ENABLE=0 ACWW_STOP_FRAME=9000 ACWW_SHOT_AFTER=6000 ACWW_SHOT_EVERY=300 \
      ACWW_STATE_SAVE=6000:C:/Users/moomin/Desktop/acww/scratchpad/state/off6000.st

    python -B scratchpad/cycle40/run_direct.py st-off-load ACWW_INTERP=1 \
      ACWW_TOUCH_ENABLE=0 ACWW_STOP_FRAME=9000 ACWW_SHOT_AFTER=6000 ACWW_SHOT_EVERY=300 \
      ACWW_STATE_LOAD=C:/Users/moomin/Desktop/acww/scratchpad/state/off6000.st

마을 레시피, 24,000에서 저장 -- `two-tap-town-recipe.md`와 같은 환경에
`ACWW_TOUCH2_AT=24700`, `ACWW_STOP_FRAME=27000`, `ACWW_SHOT_AFTER=24000`,
`ACWW_SHOT_EVERY=300`, 그리고 `ACWW_STATE_SAVE=24000:.../town24000.st` 다음에
`ACWW_STATE_LOAD=.../town24000.st`.

각 쌍은 다음으로 비교한다

    python port/tools/oracle/compare.py \
      scratchpad/cycle40/runs/st-off-save scratchpad/cycle40/runs/st-off-load

## 예상 관측

저장 다음 프레임부터 끝점까지의 모든 프레임이 `exact-rgb yes`로 읽혀야 한다. 그렇지
않은 프레임은 호스트 상태 한 조각이 블롭 레지스트리에서 빠져 있다는 뜻이며, 고치는
방법은 그것을 찾는 것이다 -- 대신 `ncc` 열을 읽는 것이 **아니다** [H: source account: `docs/kb/hybrid/savestate.md` section 7; direct ROM-source provenance unresolved].

| 쌍 | 프레임 | 결과 | 비용 |
|---|---|---|---|
| `st-off-save` / `st-off-load` | 6,000..9,000, 300마다 | **11/11 exact-rgb** | 309 s -> 110 s [H: log/source account: their `receipt.json`; receipt provenance unresolved] |
| `st-town-save` / `st-town-load` | 24,000..27,000, 300마다 | **11/11 exact-rgb**, 24,700의 접촉과 그것이 시작하는 탑승을 가로질러 | 756 s -> 65 s [H: log/source account: their `receipt.json`; receipt provenance unresolved] |

저장 줄은 실제로 안착한 프레임을 명시한다:
`acww state: saved frame 6000 -- 113 blobs, 5 threads`, 그리고 로드 줄은 어디서 재개했는지
말한다: `resuming pc 0x01ffa4fc` [H: log/source account: the two `*-run.log` files;
`docs/log/cycle40-keyboard-gate-probe.md` SAVE41; receipt provenance unresolved].

이 기능이 만들어진 워크트리에서 나온 이전 영수증들, 그 워크트리가 제거되기 전에 복사해
둔 것: 두 변수 모두 설정하지 않은 상태에서 프론티어는 **31/31 exact**로 온전하고, OFF는
11/11, 그리고 24,000 -> 27,000 마을 저장은 11/11 exact
[E: `scratchpad/state-agent/state/RECEIPTS.md`].

## 반증 조건 -- 그리고 이미 잡아낸 것

정확성 기준은 `ncc`라면 통과시켰을 실제 결함 두 가지를 찾아냈다
[H: source account: `docs/kb/hybrid/savestate.md` section 6; direct ROM-source provenance unresolved]:

- 첫 번째 쌍은 모든 프레임에서 `diff% 49.9`에 `ncc-top 1.0000`으로 `exact-rgb no`였다 --
  엔진 B의 화면 전체가 검은색이었는데, 팔레트 RAM과 OAM이 2 KB, 즉 4 KB 페이지의 절반이라
  페이지 수 `size / PAGE`가 0이 되어 어느 영역도 쓰이지 않았기 때문이다;
- 두 번째는 첫 스크립트된 A 누름부터 이어지는 0.11%의 차이였다: 두 실행에서 같은
  프레임에 채취한 스냅샷이 **52 MB 중 141 바이트**에서 달랐고 모든 영역, 모든 블롭, 모든
  레지스터 파일은 그 외에 동일했다 -- 이는 *호스트* 자원이 빠져 있을 때에만 가능하며,
  그것은 `acww_romfs_mount()`였다.

따라서 반증 요소는 저장 이후의 `exact-rgb`가 아닌 어떤 프레임이며, 그것을 추적하는
방법은 같은 프레임에서 채취한 두 스냅샷을 diff하고 주소를 읽어 내는 것이다.

## 미해결

- [H] **페이스 조절된 라이브** 실행, 즉 사람이 키보드 앞에 있는 실행에서 스냅샷을 채취한
  적은 한 번도 없다. 호스트 입력 상태는 등록되어 있지만, 어떤 라이브 실행도 저장되고
  재로드된 적이 없다. 한 번 해 보면 해결된다 [H: source account: `docs/kb/hybrid/savestate.md` section 8; direct ROM-source provenance unresolved].
- [H] 무엇이 프레임을 거부 대상으로 만드는가. 거부는 슬롯 하나를 지목하는데, 이는
  프레임의 속성이라기보다 생애 대부분을 인터프리터 프레임 두 개 깊이에서 보내는 스레드를
  시사한다; 어느 스레드인지 왜 그런지는 아무것도 측정하지 않았다. 거부된 슬롯의 체인을
  출력하면 해결된다 [H: source account: `docs/kb/hybrid/savestate.md` section 8; direct ROM-source provenance unresolved].
- [H] 오라클 레코더와 결합한 로드. `oracle.c`와 `oracle_events.c` 모두 엄격한 프레임
  단조성을 강제하며 로드를 가로질러서는 트레이스를 중단할 것이다; `run_on2.py`는 이미
  이들을 해제하며, 아무도 시도해 보지 않았다 [H: source account: `docs/kb/hybrid/savestate.md` section 5; direct ROM-source provenance unresolved].

## 위키 독자가 이것을 쓰는 법

프레임 26,000에 관한 질문 -- 씬, 메뉴, 색, 레지스터 -- 을 하려면:

1. 마을 레시피를 `ACWW_STATE_SAVE=24000:<absolute>.st`로 한 번 돌린다. 프레임이 거부되면
   다른 것을 고른다; 근처 프레임은 재생이 아니라 기존 스냅샷에서 시도하면 값싸다
   [H: source account: `scratchpad/state-agent/state/probe_frames.py`; direct ROM-source provenance unresolved].
2. 질문의 모든 변형을 `ACWW_STATE_LOAD=<that file>`과 **같은** `ACWW_*` 환경으로 돌리되,
   추가하는 계측 장치만 바꾼다.
3. 산출물을 보관한다. 재링크는 설계상 스냅샷을 무효화하므로, 포트도 함께 바꾸는 세션은
   매 링크 뒤에 다시 저장해야 한다.

`python port/tools/test_savestate.py`는 게임을 실행하지 않고 1초 이내에 헤더, 두 거부
규칙, 블롭 레지스트리를 검사한다 [H: source account: `docs/kb/hybrid/savestate.md` section 7; direct ROM-source provenance unresolved].

## 관련 문서

- `../engine/interpreter-path.md` -- 스냅샷이 채취되는 런타임
- `two-tap-town-recipe.md`, `off-recipe.md` -- 영수증이 채취된 두 레시피
- `touch-latency.md` -- 이 계측 장치가 겨냥하는 종류의 늦은 프레임 질문
- `../../docs/kb/hybrid/savestate.md` -- 구현 쪽 페이지
