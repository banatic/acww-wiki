# 무음 오디오 프로브: 게임은 어떤 사운드 명령을 내보내는가?
<!-- source: wiki/experiments/silent-audio-probe.md -->

**상태: 대체됨(SUPERSEDED), 2026-09-09 (AUDIO6, `115984f9`) -- 그리고 아래의 설계는 메커니즘에
관해 옳았다.** 열두 줄 제한이 제거되고 센서스는 제한 없이 만들어졌으며, 이는 정확히 이
페이지가 요구한 것이다. 답: 게임은 **프레임 6부터** id 2, 3, 6, 7, 9를 내보내며, 그 제한이
"게임은 재생 명령을 결코 보내지 않는다"(M1)는 주장의 근거 전부였다. 드라이버를 켜면 OFF
레시피는 `PREPARE_SEQ`와 `START_PREPARED_SEQ`를 각각 371번 본다; 끄면 각각 967번인데,
무음 ARM7은 `playerStatus`를 결코 공개하지 않아 게임이 시작하는 모든 시퀀스를 다시 시작하기
때문이다 [H: log/source account: `docs/kb/hybrid/audio.md` section 8(c); `../systems/audio.md`; receipt provenance unresolved]. 아래 페이지는
그 추론이 거기까지 도달하게 한 추론이므로 남겨 둔다; 포트의 ARM7이 무음이라는 아래의 모든
문장은 `../systems/audio.md`로 대체되었다.

## 목적

포트의 ARM7 사운드 프로세서 전체는 ARM9의 명령 목록을 순회하며 모든 명령을 조용히
완료하고 완료 태그를 올리는 함수 하나이다
[H: host-source account from `port/shim/os/pxisend.c`; verify with a retained scripted run and frame using this page's recipe]. 이 함수는 보는 각 명령의 id를 출력한다 -- 그러나 출력이
`said < 12`로 제한되어 있어 처음 열두 개만 출력한다 [H: host-source account from `port/shim/os/pxisend.c`; verify with a retained scripted run and frame using this page's recipe].

그 제한 때문에 현재 상태로는 가장 유용한 질문에 답할 수 없다. 첫 가청 슬라이스는 id 2
(`PREPARE_SEQ`), 9 (`ALLOCATABLE_CHANNEL`), 6 (`PLAYER_PARAM`), 3 (`START_PREPARED_SEQ`)을
지원해야 할 것이고 [H: host/prose inference from `docs/kb/port/input-save-audio.md`; verify against the ROM function or symbol table and this page's recipe], 게임이 마을 회관으로 가는 길에
그중 어느 것을 실제로 내보내는지는 아무도 모른다. 프레임 0부터의 열두 줄은 모두 부팅
트래픽일 것이다.

따라서 이 실험은 두 부분이다: 제한을 올리고, 그 다음 센다.

## 레시피

**1단계, 한 줄짜리 도구 변경.** `port/shim/os/pxisend.c`의 `snd_arm7`에서 출력은 12로
제한된 정적 카운터로 게이트되어 있다. 이를 id별 "seen" 테이블로 교체한다. `acww_card_arm7`이
요청 타입에 대해 이미 사용하는 것과 정확히 같은 모양이다 -- 서로 다른 명령 id마다 한 줄,
게이트 없음 [H: host-source account from `port/shim/fs/cardreq.c`, `static unsigned char seen[16; verify with a retained scripted run and frame using this page's recipe]`]. 이는 출력 홍수
없이 "어떤 id가 발생하는가"에 답한다; id별 두 번째 카운터가 "몇 번인가"에 답하며, 덤프
시점에 한 번 출력한다.

근거이며, 이 저장소의 상시 경고가 상수 하나의 형태로 도착한 것이다: 발화할 수 없는
도구는 발화하되 아무것도 바꾸지 않는 도구와 구별할 수 없다. 카드 심은 정확히 이
이유로 잘못된 상수 두 개를 내보낸 적이 있다 [H: host-source account from `port/shim/fs/cardreq.c`; verify with a retained scripted run and frame using this page's recipe].

**2단계, 대조.** `off-recipe.md`를 실행하고 31 중 31 동일을 확인한다. 출력만 바꾸는
변경은 픽셀 하나도 움직여서는 안 된다; 움직인다면 그 변경은 출력만 바꾸는 것이 아니다 (M15).

**3단계, 측정.** `two-tap-town-recipe.md`의 마을 레시피를 그대로 48,000 프레임까지.
그 다음 Python으로 로그에서 카운트를 뽑아낸다 -- **셸 `grep` 대안(alternation)으로
하지 말 것**: 여기의 셸은 ripgrep이며 그 대안 기호는 `\|`가 아니라 `|`이고, 옛 패턴은
한 사이클 안에서 두 번이나 조용히 아무것도 매치하지 않았다
[H: log/source account: `docs/kb/hybrid/recipes.md` section 8; `docs/log/cycle40-keyboard-gate-probe.md` ENTRY40; receipt provenance unresolved].

## 예상 관측

| 줄 | 의미 |
|---|---|
| `acww snd7: command id 1d completed silently` | id 29, `SHARED_WORK`: ARM7이 블록의 주소를 알게 되는 것. 초기에, 그리고 최소 한 번은 예상됨 |
| `acww snd7: command id 2` | `PREPARE_SEQ` -- 시퀀스가 실제로 요청되었다 |
| `acww snd7: command id 9` | `ALLOCATABLE_CHANNEL`, 플레이어의 할당 마스크가 0이 아닐 때에만 prepare 뒤에 따라온다 |
| `acww snd7: command id 6` | `PLAYER_PARAM`, 계산된 페이더나 볼륨이 다를 때에만 플레이어 메인 스텝에서 내보내진다 |
| `acww snd7: command id 3` | `START_PREPARED_SEQ` |

예측:

- id 29가 발생한다. 프로토콜은 그렇게 시작하며 포트는 `finishCommandTag`를 찾기 위해
  이에 의존한다.
- id 2와 3이 프레임 6,000 전에 발생한다. 원본에서는 타이틀과 택시에 음악이 있기 때문이다.
- id 6이 대량으로 발생한다. 페이더 램프는 서로 다른 스텝마다 하나씩 내보내기 때문이다.

id 2, 3, 6, 9가 48,000 프레임에 걸쳐 모두 없다면, 이 빌드에서 게임 자체의 사운드 경로가
드라이버에 도달하지 않거나, 아카이브 로드가 조용히 실패한 것이다 -- 그리고 후자는 알려진
실패 시그니처가 있다: 호스트 사운드 파사드가 한 번 "아카이브 없음"이라고 답했고,
`NNS_SndArcGetSeqArcParam`이 `func_020f4b1c`에 NULL을 반환했으며, 이것이 ROM의 치명적
경로 `func_0206e3ec`를 호출했고, ROM의 크래시 화면이 프레임 ~830부터 두 화면 모두 검은
채로 루프했다 [H: log/source account: `docs/log/cycle40-keyboard-gate-probe.md` CARD40..SND40; receipt provenance unresolved]. 그 실행은
마을에 도달하므로 그 특정 실패는 배제된다 -- 따라서 전부 없음이라는 결과는 진정으로
놀라운 것이며 추적할 가치가 있다.

같은 로그에서 공짜로 얻는 두 번째 관측: ARM9가 *기다린* 적이 있는가. `SND_WaitForCommandProc`는
태그가 완료될 때까지 스핀한다 [S: `src/matched/SND_WaitForCommandProc.c`; source account: `src/matched/SND_WaitForCommandProc.c`]. 끝까지 도달한
실행은 그런 대기가 데드락되지 않았음을 증명하며, 이것이 무음 ARM7이 충분하다는 상시
근거이다 -- ROM의 치명적 경로에 다시 들어가지 않은 90,000 프레임
[E: `scratchpad/cycle40/runs/tap-D59`, LONG41].

## 이 실험이 검증하는 가설의 반증 조건

가설은 무음 ARM7이 게임의 로직에 무기한으로 충분하다는 것이다
[H: source account: `docs/kb/hybrid/hardware-services.md` section 7; direct ROM-source provenance unresolved]. 대기 함수가 `SND_*` 또는 `NNS_Snd*`
심볼인 정체(stall)가 있으면 반증된다 -- ROM의 사운드 스택은 실제 플레이어 상태를 결코
보고하지 않는 소비자를 상대로 돌아가므로, 게임이 진행을 기다리는 시퀀스는 멈출 것이다.
이 프로브는 그것을 만들어 낼 수 없다; 어떤 명령이 사용 중인지만 알려 줄 수 있으며, 이는
음악 기반 타이밍이 있는 씬에 대한 오라클 비교를 설계할 때 필요한 정보이다.

**이 실험은 소리를 내지 않으며 그쪽으로 가는 단계도 아니다.** 전송만으로는 시퀀스를
해석하거나, 뱅크나 웨이브 아카이브를 해석하거나, 채널을 할당하거나, 엔벨로프와 타이머를
전진시키거나, PCM을 만들어 낼 수 없다 [H: host/prose inference from `docs/kb/port/input-save-audio.md`; verify against the ROM function or symbol table and this page's recipe].

## 관련 문서

- `../systems/audio.md`
- `two-tap-town-recipe.md`, `off-recipe.md`
