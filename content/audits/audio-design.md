# 감사와 설계: 호스트 측 ARM7 사운드 드라이버
<!-- source: wiki/audits/audio-design.md -->

verified-at: 115984f9 2026-09-09

**목적.** 이 페이지는 포트가 무음이었고 호스트 "ARM7"이 샘플 하나 내지 않은 채 모든 명령을
완료하던 시점에 작성되었다. **그것은 더 이상 사실이 아니다**: 아래의 여덟 빌드 순서 단계가
모두 완료되었고, `ACWW_SND=1`은 게임이 실제로 요구하는 캡처 경로를 통해 게임의 음악과 효과음을
재생한다(`docs/kb/hybrid/audio.md`). 이 페이지는 당시의 설계(DESIGN)와 감사(AUDIT) 그대로
보존된다. 이 페이지의 명령 표, 인자 분해, 주장 표가 드라이버를 만드는 바탕이었고 지금도 여전히
옳기 때문이다. 이 페이지는 세 가지 일을 한다: 그 경계가 실어 나르는 정확한 명령 집합을 명명하고,
소리로 응답할 호스트 드라이버를 설계하며, `systems/audio.md`와 `data/music.md`를 공개 기록에
비추어 감사한다. 코드는 여기 복사하지 않으며, 구조는 서술하고 출처를 단다.

**P 등급(공개)** 은 `data-formats.md`를 따른다: 공개 문서 — GBATEK, 벤더 헤더, 같은 라이브러리의
디컴파일 — 는 URL을 갖는다. **P는 결코 S, E, O를 대체하지 않는다.** P와 S가 어긋나는 곳에서는
S가 이기며, 그 불일치 자체가 내용이 된다(STYLE 규칙 7). 이 주제의 특이한 점은 그 상당 부분이
**S** 등급이라는 것이다: `src/matched/`에는 실제 NitroSDK 2.2a와 NNS 라이브러리 번역 단위가
들어 있으므로, 명령 enum, 인자 패킹, 공유 워크 레이아웃, 드라이버 자체의 상태 구조체, SDAT
레코드 구조체를 모두 이 저장소에서 읽을 수 있다.

## 참고한 출처

| 출처 | URL | 다루는 내용 |
|---|---|---|
| NitroSDK `nitro/snd/common/command.h` | `https://raw.githubusercontent.com/ntrtwl/NitroSDK/main/include/nitro/snd/common/command.h` | `SNDCommandID` enum, 노드 구조체, 푸시 플래그 |
| NitroSDK `nitro/snd/common/mml.h` | `https://raw.githubusercontent.com/ntrtwl/NitroSDK/main/include/nitro/snd/common/mml.h` | SSEQ 옵코드 이름 |
| NitroSDK `seq.h`, `bank.h`, `channel.h`, `exchannel.h`, `main.h`, `alarm.h`, `work.h` | 같은 트리, `include/nitro/snd/common/` | 플레이어/트랙/채널 한계, 악기 타입, `SND_PROC_INTERVAL` |
| pret/pokediamond ARM7 SND 디컴파일 | `https://raw.githubusercontent.com/pret/pokediamond/master/arm7/lib/src/SND_command.c` (그리고 `SND_main.c`, `SND_seq.c`, `SND_exChannel.c`, `SND_bank.c`) | `SND_CommandProc`, 드라이버 스레드 루프, 시퀀서, 채널 할당기 |
| GBATEK, DS Sound Channels 0-15 | `https://problemkaputt.de/gbatek-ds-sound-channels-0-15.htm` | `SOUNDxCNT/SAD/TMR/PNT/LEN` 비트 필드 |
| GBATEK, DS Sound Control Registers | `https://problemkaputt.de/gbatek-ds-sound-control-registers.htm` | `SOUNDCNT`, `SOUNDBIAS`, 32.768 kHz 출력 레이트 |
| GBATEK, DS Sound Notes | `https://problemkaputt.de/gbatek-ds-sound-notes.htm` | IMA-ADPCM 테이블과 DS의 편차, 10단계 믹싱 파이프라인, PSG 듀티, 노이즈 LFSR |
| GBATEK, DS Sound Capture | `https://problemkaputt.de/gbatek-ds-sound-capture.htm` | `SNDCAPxCNT/DAD/LEN`, 두 가지 캡처 버그 |
| GBATEK, SDAT / SSEQ / SSAR / SBNK / SWAR / SWAV / STRM | `https://problemkaputt.de/gbatek-ds-files-sound-sdat-etc.htm` 및 그 하위 페이지 | 컨테이너와 레코드 레이아웃 |
| kiwi.ds, Nitro Composer File Specification | `https://www.feshrine.net/hacking/doc/nds-sdat.html` (`.php` 형식은 406을 반환한다) | 원래의 SDAT 스펙 |
| ndspy | `https://ndspy.readthedocs.io/en/latest/appendices/sdat-structure.html`, `https://github.com/RoadrunnerWMC/ndspy` | 필드 이름, 참조용 SDAT/SSEQ 구현 |

---

## 1. 명령 채널: ARM9가 실제로 보내는 것

### 전송

`SND_FlushCommand`는 예약(reserve) 리스트를 대기(pending) 리스트로 옮기고 **한 워드 — 머리
노드의 주소 — 를 PXI 태그 7로** 보내며, FIFO가 가득 차 있는 동안 재시도한다
[S: `src/matched/SND_FlushCommand.c`]. 명령은 결코 하나씩 이동하지 않는다; 256노드 풀에
쌓였다가 플러시 한 번에 이동한다. 0 워드는 `RequestCommandProc`의 깨우기(wake)이며 리스트를
싣지 않는다 [H: host-source account from `port/shim/os/pxisend.c`, `snd_arm7`; verify with a retained scripted run and frame using this page's recipe].

노드는 24바이트다: `next`가 `+0x00`, id가 `+0x04`, 네 개의 인자 워드가 `+0x08`,
`+0x0c`, `+0x10`, `+0x14`. `SND_FlushCommand`의 번역 단위는 id를 `u8`과 그 뒤 3바이트 패딩으로
타입 지정하고, `SND_AllocCommand`의 번역 단위는 4바이트 enum으로 타입 지정한다 — 어느 쪽이든
같은 24바이트다 [S: `src/matched/SND_FlushCommand.c`, `src/matched/SND_AllocCommand.c`]
[P: `command.h`, `struct SNDCommand`]. **이 레이아웃은 포트 자체의 주소로 산술적으로
확인된다**: `0x022048a0`의 256엔트리 명령 배열에 `256 * 24 = 0x1800`을 더하면 정확히
공유 블록 포인터인 `0x022060a0`에 도달한다 [S: `systems/audio.md`'s address table, arithmetic].
포트는 `+0x04`에서 워드 전체를 읽는데, 이것이 맞는 이유는 오직 리틀 엔디언 호스트에서 패딩
바이트가 0이기 때문이다; id는 1바이트다 [E: `pxisend.c`].

ARM7은 디스패치 전에 각 노드를 로컬로 복사하고, 복사된 `next`를 따라가며,
`finishCommandTag`를 **명령마다가 아니라 플러시된 리스트마다 한 번** 증가시킨다
[P: pokediamond `SND_command.c`, `SND_CommandProc`]. 호스트도 같게 한다 [E: `pxisend.c`].

`SNDSharedWork`는 다음과 같다: `+0x00`에 u32 `finishCommandTag`, `+0x04`에 u32 `playerStatus`,
`+0x08`/`+0x0a`에 u16 `channelStatus`와 u16 `captureStatus`, 패딩 워드 다섯 개, 그 다음
`+0x20`부터 `{ s16 variable[16]; u32 tickCounter; }`의 `player[16]`, 그 다음 `s16
globalVariable[16]` — 640바이트 [S: `src/matched/SND_GetPlayerStatus.c`,
`src/matched/AllocFunc_SOCL.c`, the struct verbatim] [P: `work.h`, identical]. **따라서 포트의
"첫 워드를 증가시킨다"는 옳으며**, 그 옆의 세 상태 워드가 ARM7이 상태를 되돌려 보고할 유일한
채널이다 — §4의 정지(stall) 가설을 보라.

### 명령 집합

id는 열거자 위치 0..33이다 [S: `src/matched/SND_AllocCommand.c`, the full
`SNDCommandID` enum] [P: `command.h`]. 인자 열은 매칭된 ARM9 빌더가 패킹하는 곳에서는 S 등급,
`SND_CommandProc`만이 언패킹하는 곳에서는 P 등급이다.

| id | 이름 | 인자 (arg0..arg3) | ARM7이 해야 하는 일 |
|---|---|---|---|
| 0 | `START_SEQ` | playerNo, seq base, seq offset, bank | 준비와 시작을 한 단계로 [P] |
| 1 | `STOP_SEQ` | playerNo | 플레이어의 트랙과 채널을 해제 [S: `SND_StopSeq.c`] |
| 2 | `PREPARE_SEQ` | playerNo, seq base, seq offset, bank | 플레이어 + 트랙을 할당하되 실행하지 않음 [S: `SND_PrepareSeq.c`] |
| 3 | `START_PREPARED_SEQ` | playerNo | 준비됨 플래그를 지우고 스텝 시작 [S: `SND_StartPreparedSeq.c`] |
| 4 | `PAUSE_SEQ` | playerNo, flag | [P] |
| 5 | `SKIP_SEQ` | playerNo, ticks | 출력 없이 시퀀서를 앞으로 진행 [P] |
| 6 | `PLAYER_PARAM` | playerNo, offset, data, size | `SNDPlayer`에 대한 크기 지정 원시 쓰기 [S: `SNDi_SetPlayerParam.c`] |
| 7 | `TRACK_PARAM` | size<<24 \| playerNo, trackBitMask, offset, data | 선택된 모든 `SNDTrack`에 대한 크기 지정 원시 쓰기 [S: `SNDi_SetTrackParam.c`] |
| 8 | `MUTE_TRACK` | playerNo, trackBitMask, mute | [P] |
| 9 | `ALLOCATABLE_CHANNEL` | playerNo, trackBitMask, chBitMask | 그 트랙들이 16채널 중 어느 것을 가져갈 수 있는지 제한 [S: `SND_SetTrackAllocatableChannel.c`] |
| 10 | `PLAYER_LOCAL_VAR` | playerNo, varNo, s16 value | `sharedWork.player[n].variable[v]`에 쓴다 [P] |
| 11 | `PLAYER_GLOBAL_VAR` | varNo, s16 value | `sharedWork.globalVariable[v]`에 쓴다 [P] |
| 12 | `START_TIMER` | chBitMask, capBitMask, alarmBitMask, flags | 채널, 캡처 유닛, 알람의 시작 비트를 세팅 [S: `SND_StartTimer.c`] |
| 13 | `STOP_TIMER` | chBitMask, capBitMask, alarmBitMask, flags | 그 역; ARM9가 먼저 각 알람의 id를 올린다 [S: `SND_StopTimer.c`] |
| 14 | `SETUP_CHANNEL_PCM` | timer<<16\|chNo; dataAddr; volume<<24\|shift<<22\|loopLen; loop<<26\|format<<24\|pan<<16\|loopStart | `SNDWaveData`로부터 채널 하나를 프로그래밍 [S: `SND_SetupChannelPcm.c`] |
| 15 | `SETUP_CHANNEL_PSG` | chNo; volume\|shift<<8; pan\|timer<<8; duty | 채널 8-13만 [P] |
| 16 | `SETUP_CHANNEL_NOISE` | chNo; volume\|shift<<8; pan\|timer<<8 | 채널 14-15만 [P] |
| 17 | `SETUP_CAPTURE` | buffer; length; capture<<31\|format<<30\|loop<<29\|in<<28\|out<<27; 0 | 캡처 유닛 하나를 프로그래밍 [S: `SND_SetupCapture.c`] |
| 18 | `SETUP_ALARM` | alarmNo, tick, period, handler id | ARM9 핸들러를 일으키는 주기적 ARM7 알람 [S: `SND_SetupAlarm.c`] |
| 19 | `CHANNEL_TIMER` | chBitMask, timer | 실행 중인 채널을 재조율 [P] |
| 20 | `CHANNEL_VOLUME` | chBitMask, volume, shift | [S: `SND_SetChannelVolume.c`] |
| 21 | `CHANNEL_PAN` | chBitMask, pan | [S: `SND_SetChannelPan.c`] |
| 22 | `SURROUND_DECAY` | decay | 캡처 기반 의사 서라운드의 깊이 [S: `SNDi_SetSurroundDecay.c`] |
| 23 | `MASTER_VOLUME` | volume | `SOUNDCNT` 비트 0-6 [S: `SND_SetMasterVolume.c`] |
| 24 | `MASTER_PAN` | pan | [P] |
| 25 | `OUTPUT_SELECTOR` | left, right, ch1, ch3 | `SOUNDCNT` 비트 8-13 [S: `SND_SetOutputSelector.c`] [P: GBATEK control registers] |
| 26 | `LOCK_CHANNEL` | chBitMask, flags | 채널을 할당기에서 제거 [S: `SND_LockChannel.c`] |
| 27 | `UNLOCK_CHANNEL` | chBitMask, flags | [S: `SND_UnlockChannel.c`] |
| 28 | `STOP_UNLOCKED_CHANNEL` | chBitMask, flags | [P] |
| 29 | `SHARED_WORK` | `SNDSharedWork`의 주소 | 저장한다; 이것이 도착하기 전에는 아무것도 동작하지 않는다 [S: `SND_CommandInit.c`] [E: `pxisend.c`] |
| 30 | `INVALIDATE_SEQ` | start, end | 해제되는 범위를 가리키는 캐시된 포인터를 버린다 [S: `SND_InvalidateSeqData.c`] |
| 31 | `INVALIDATE_BANK` | start, end | [S: `SND_InvalidateBankData.c`] |
| 32 | `INVALIDATE_WAVE` | start, end | [S: `SND_InvalidateWaveData.c`] |
| 33 | `READ_DRIVER_INFO` | `SNDDriverInfo`의 주소 | 드라이버 상태 전체를 ARM9로 복사해 되돌린다 [S: `SND_ReadDriverInfo.c`] |

기록해 둘 만한 교차 검증이 두 가지 있다. id 14와 id 7에 대한 ARM9의 패킹은 ARM7의 분해와
필드 하나하나까지 일치하므로 S와 P가 서로를 뒷받침한다 [S: `SND_SetupChannelPcm.c`,
`SNDi_SetTrackParam.c`] [P: pokediamond `SND_command.c`]. id 17은 일치하지 **않는다**:
pokediamond 디컴파일은 비트 31을 캡처 *포맷*이라 부르지만, ARM9 빌더는 그 자리에 캡처
*유닛 번호*를 넣고 포맷은 비트 30에 넣는다 [S: `src/matched/SND_SetupCapture.c`]. ARM9
빌더는 이 ROM 자신의 코드이므로 이긴다; 그 한 명령에 대한 디컴파일의 인자 이름은 신뢰할 수
없다.

### 이 ROM이 보내는 것이 관측된 것

두 실행에서 동일한 열두 개의 명령이, 모두 프레임 3이 끝나기 전에, 다음 순서로 관측되었다
[E: `scratchpad/cycle40/runs/tap-D59/tap-D59-run.log:161,194-204`;
`scratchpad/cycle40/runs/off-D45/off-D45-run.log:146,163-173`]:

`29 SHARED_WORK` · `22 SURROUND_DECAY` · `26 LOCK_CHANNEL` · `14 SETUP_CHANNEL_PCM` ·
`17 SETUP_CAPTURE` · `14 SETUP_CHANNEL_PCM` · `17 SETUP_CAPTURE` · `18 SETUP_ALARM` ·
`25 OUTPUT_SELECTOR` · `12 START_TIMER` · `23 MASTER_VOLUME` · `13 STOP_TIMER`.

**그 목록이 포트가 가진 근거의 전부이며, 그것은 게임이 아니라 계측기의 산물이다.**
`snd_arm7`은 정적 카운터가 12 미만인 동안만 출력하므로, 실행이 아무리 길어져도 열두 번째 줄이
포트가 내보내는 마지막 줄이다 [E: `pxisend.c`, `said < 12`].
프레임 3 이후 게임이 보내는 모든 것 — 모든 `PREPARE_SEQ`, 모든 `START_PREPARED_SEQ`, 모든
`PLAYER_PARAM` — 은 보이지 않는다. `systems/audio.md`에 계획된 `silent-audio-probe` 실험은
그 상한을 올리기 전까지 자신의 질문에 답할 수 없다.

열두 명령이 *실제로* 보여주는 것은, 게임이 무엇이든 재생하기 전에 **캡처 기반 출력 이펙트**를
띄운다는 것이다: 채널 쌍 하나를 할당기에서 잠그고, PCM 채널 둘과 그에 대응하는 캡처 유닛 둘을
프로그래밍하고, 알람을 무장시킨 뒤, `SOUNDCNT`의 출력 셀렉터를 다시 가리킨다
[H: the identification; settled by raising the cap and printing arg0..arg3 for each node].
`SND_CAPOUT_CHANNEL_MASK`는 `0x000A`(채널 1과 3)이고 `SND_CAPIN_CHANNEL_MASK`는
`0x0005`(채널 0과 2)이다 [P: `channel.h`]. `NNS_SndCaptureStartOutputEffect`는 32,000워드
버퍼와 콜백을 캡처 시작 경로에 넘긴다 [S:
`src/matched/NNS_SndCaptureStartOutputEffect.c`].

**설계상의 귀결은 크다.** 출력 셀렉터가 Ch1/Ch3를 가리키면, GBATEK의 `SOUNDCNT` 비트 8-11에
따라 스피커는 더 이상 믹서를 전혀 듣지 않는다 — 스피커는 캡처 버퍼로부터 공급되는 그 두
채널을 듣는다
[P: `gbatek-ds-sound-control-registers.htm`]. 열여섯 채널과 믹서를 구현하되 캡처와 출력
셀렉터를 무시하는 호스트 드라이버는 아무도 듣지 않는 버퍼에 올바른 믹스를 렌더링하게 된다.

**측정으로 확정됨 (2026-09-09, 오디오 마일스톤 7).** 포트가 각 노드의 네 워드를 모두 출력하자
위 두 문단의 모든 예측이 인자 하나하나까지 들어맞았다: `LOCK_CHANNEL` 마스크 `0x000A`,
채널 1과 3에 팬 0과 팬 127로 타이머 512의 512워드 버퍼 두 개에 대한 `SETUP_CHANNEL_PCM`,
같은(SAME) 두 버퍼에 소스 비트를 지운 채(믹서) 루프 비트를 세팅한 `SETUP_CAPTURE`, 그리고
`OUTPUT_SELECTOR 1 2 1 1`. 캡처와 그 재생 채널이 버퍼 하나와 클럭 하나를 공유하므로,
스피커는 버퍼 하나만큼 지연된 믹서를 듣는다 -- 32,729.5 Hz에서 1,024 샘플 = 31.3 ms --
왼쪽 끝과 오른쪽 끝으로 다시 팬되고, `SNDi_SetSurroundDecay`가 채널 1과 3을 제외한 모든
것을 끌어내린다. `capture.c`가 이를 구현하며, 포트 자신의 렌더는 지연 1,025에서 상관계수
0.9962로 캡처 끔 렌더와 같다 [`docs/kb/hybrid/audio.md` §7].

---

## 2. 설계: `port/shim/audio/`

### 호스트가 모델링해야 하는 것

ARM7 드라이버의 전체 상태는 구조체 하나이며, 이 저장소는 이미 그 선언을 갖고 있다:
`SNDWork`는 `SNDExChannel channel[16]`, `SNDPlayer player[16]`, `SNDTrack track[32]`,
`SNDAlarm alarm[8]`이다 [S: `src/matched/SND_ReadPlayerInfo.c`, the structs verbatim]. 이것은
편의가 아니다 — id 6과 7은 **`SNDPlayer`와 `SNDTrack`에 대한 원시 오프셋/크기 쓰기**이므로,
호스트 드라이버는 그 필드 오프셋을 정확히 재현해야 하며 그렇지 않으면 ARM9의
`SND_SetPlayerVolume`이 엉뚱한 바이트에 떨어진다. `SND_SetPlayerVolume`은 오프셋 6, 크기 2 —
`extFader` — 에 쓴다 [S: `src/matched/SND_SetPlayerVolume.c`].

- `SNDPlayer`: 플래그 비트 셋, `myNo`, `prio`, `volume`, `s16 extFader`, `u8 tracks[16]`
  (0xFF = 없음), `tempo`, `tempo_ratio`, `tempo_counter`, `SNDBankData *bank`.
- `SNDTrack`: 플래그 비트 여덟 개(active, note_wait, mute, tie, note_finish_wait, porta, cmp,
  channel_mask), `prgNo`, 볼륨 둘, 피치 벤드와 범위, 팬과 ext 팬, `extFader`,
  `ext_pitch`, A/D/S/R, `prio`, `transpose`, 포르타멘토 키와 시간, `sweep_pitch`,
  `SNDLfoParam mod` 하나, `channel_mask`, `s32 wait`, `base`와 `cur` 바이트 포인터,
  `call_stack[3]`, `loop_count[3]`, `call_stack_depth`, 그리고 채널 리스트 머리.
- `SNDExChannel`: `env_status`, 키, 벨로시티, 팬들, `env_decay`, 스윕 카운터, A/D/S/R,
  `volume`, `timer`, `SNDLfo` 하나, `length`, 내장된 `SNDWaveParam`, 데이터 포인터 또는
  듀티 값, 그리고 drop/finish 콜백.

`SND_TRACK_CALL_STACK_DEPTH`는 3이고 `SND_TRACK_NUM_PER_PLAYER`는 16이다 [P: `seq.h`]; 위의
구조체가 이에 동의한다 [S].

### 프레임

실제 ARM7 드라이버는 `SND_PROC_INTERVAL 0xAA8` = 2728 OS 틱의 `OS` 주기 알람으로 깨어나는
스레드다 [P: `main.h`, pokediamond `SND_main.c`]. 초당 `33513982/64 = 523,656` OS 틱이므로
이는 191.96 Hz — **1/192초 드라이버 프레임** — 이다 [P: arithmetic over those two constants].
그 루프는: 채널 갱신, 명령 큐 비우기, 시퀀스 스텝, 채널 엔벨로프 실행, `SNDSharedWork` 게시,
RNG 진행이다. 명령 푸시는 주기 플래그를 *false*로 하여 스레드를 깨우므로, 명령은 즉시
처리되고 엔벨로프와 시퀀스는 192 Hz 프레임에서만 진행한다 [P: pokediamond `SND_main.c`].
시퀀스 타이밍은 그 위에 얹힌다: 프레임마다 누산기에 `(tempo * tempoRatio) >> 8`을 더하고,
240을 뺄 때마다 시퀀스 틱 하나를 낸다
[P: pokediamond `SND_seq.c`; `SND_BASE_TEMPO 240`, `SND_DEFAULT_TEMPO 120` from `seq.h`].

### 데이터 흐름, 말로 풀면

*요청.* 게임 글루가 `NNS_SndArcPlayerStartSeqArc(handle, seqArcNo, index)`를 호출한다. NNS
계층은 `index`의 SSAR 레코드를 읽고, 사운드 힙을 통해 뱅크와 그 웨이브 아카이브를 로드하고,
플레이어를 할당한 뒤, 시퀀스의 베이스 포인터와 바이트 오프셋과 로드된 뱅크 포인터로
`SND_PrepareSeq`를 호출한다. 이것이 풀의 노드 id 2가 된다. `NNS_SndMain`이 게임 프레임마다
한 번 풀을 플러시한다: PXI 워드 하나, 리스트 하나.

*디스패치.* 호스트는 머리 주소를 받아 리스트를 순회하고, 각 노드에 대해 위 표가 명명한
드라이버 변경을 실행한다. 리스트가 끝나면 `finishCommandTag++`.

*틱.* 게임의 프레임과 독립적으로, 호스트는 드라이버를 초당 192번 진행시킨다. 각 드라이버
프레임에서: 활성 플레이어마다 템포를 누산하고, 방출된 시퀀스 틱마다 `wait`가 0에 도달한
모든 트랙을 스텝한다; 실행된 각 노트온은 트랙의 `prgNo`를 뱅크를 통해 `SNDInstParam`으로
해석하고, 채널을 할당하고, 그것을 프로그래밍한다. 그 다음 모든 활성 채널이 엔벨로프와 LFO를
한 프레임 진행시킨다; 릴리스 상태에서 엔벨로프가 바닥 아래로 떨어진 채널은 비활성화되고
FINISH로 콜백을 발화한다 [P: pokediamond `SND_exChannel.c`].

*렌더.* 채널 상태는 소리가 아니다; 소리에 대한 서술이다. 별도의 믹서가 열여섯 채널의 현재
파라미터로부터 32.768 kHz로 N 샘플을 렌더링하고, 캡처 경로를 적용하고, 그 블록을 싱크에
넘긴다. 믹서는 게임의 클럭이 아니라 싱크의 클럭으로 구동되어야 한다: 이곳이 포트의 가변
프레임 레이트가 새어 들어와서는 안 되는 유일한 지점이다.

### 모듈

| 모듈 | 책임 |
|---|---|
| `sdat.c` | 호스트 FS를 통해 `sound_data.sdat`를 연다; 인덱스 기반 INFO/FAT/FILE 접근자. 읽기 전용, 할당 없음. |
| `sseq.c` | SSEQ/SSAR 이벤트 디코더: 가변 길이 값, 옵코드 테이블, `RANDOM`/`VARIABLE`/`IF` 접두어, 깊이 3의 호출 및 루프 스택. |
| `sbnk.c` | 악기 조회: `instOffset[prgNo]` → 타입 + 24비트 오프셋; 드럼 세트와 키 스플릿 하강; `SNDInstParam` 출력. |
| `swav.c` | DS의 반올림과 클리핑 편차를 포함한 PCM8 / PCM16 / IMA-ADPCM 디코드; 루프 지점의 디코더 상태 스냅샷. |
| `driver.c` | `SNDWork`: 34개 명령 디스패처, 플레이어/트랙/채널 상태 머신, 192 Hz 프레임, `SNDSharedWork` 게시. |
| `chanalloc.c` | `SND_AllocExChannel`: 마스크, 잠금, 최저 우선순위 후 최소 음량 희생자 선정, DROP 콜백. |
| `mixer.c` | 32.768 kHz 믹스: 10단계 볼륨/팬/마스터/바이어스/클립 파이프라인, PSG 듀티, 15비트 노이즈 LFSR. |
| `capture.c` | 두 캡처 유닛, 그 루프 버퍼, 출력 셀렉터, 그리고 `SOUNDCNT` 라우팅. |
| `sink_win32.c` | WASAPI 공유 모드 렌더 클라이언트(waveOut을 폴백으로), 링 버퍼, 그리고 유일한 스레드 경계. |
| `snd_trace.c` | 기존 `w3_sndtrace`를 노드별 인자 로깅과 상한 없는 id 집계로 확장. |

### 빌드 순서

순서 규칙은 **무음 보존**이다: 6단계 이전의 어떤 것도 게임이 하는 일을 바꿀 수 없으므로,
6단계 이전의 어떤 것도 90,000프레임 프런티어를 퇴행시킬 수 없다.

**상태 (2026-09-09): 여덟 단계 모두 완료.** 7단계와 8단계는 오디오 마일스톤 7과 8로 착지했다;
`docs/kb/hybrid/audio.md` §7-§9; `docs/kb/hybrid/audio-differential.md` §A10이 그것들이 오늘 무엇을 하는지 말하는 페이지다. 6단계는
`port/shim/audio/driver.c`(34개 명령 디스패처), `port/shim/audio/sink_win32.c`(WASAPI 공유
모드, waveOut 폴백), 그리고 `port/shim/os/pxisend.c`와 `port/platform/frame.c`의 배선으로
착지했다. 아래의 모든 내용은 쓰인 그대로 보존되는데, 순서 논증이 여전히 이 작업이 안전한
이유이기 때문이다; `docs/kb/hybrid/audio.md`는 포트가 오늘(TODAY) 무엇을 하는지 — 어떤
명령이 디스패치되고, 어떤 것이 의도적인 no-op이고, 어떤 것이 로깅만 되는지를 포함해 —
말하는 페이지이며, 여기의 단계별 문구를 대체한다.

1. **완료. 계측기를 올린다.** `snd_arm7`의 열두 줄 상한을 상한 없는 id 히스토그램과 유계
   인자 로그로 교체하고, 둘 다 `ACWW_SND_TRACE` 변수 뒤에 둔다. 이것은 `pxisend.c`의 편집
   하나이며 이 목록에서 가장 값싼 것이다. 산출물: 마을 실행에 대한 실제 id 집계로, §2의
   얼마만큼이 실제로 필요한지를 결정한다.
2. **완료. `sdat.c` + `sbnk.c` + `swav.c` 오프라인.** 아카이브를 순회하고 레코드를 덤프하는
   독립 실행 호스트 도구. 검증은 정확하다: 아래 §3의 개수와 체인을 재현해야 한다.
3. **완료. `sseq.c` 오프라인.** 시퀀스 하나를 이벤트 리스트로 디코드한다. 같은 파일에 대해
   ndspy의 디코더와 대조 검증한다 — 불일치는 둘 중 하나의 버그이며 둘 다 읽을 수 있다.
4. **완료. `chanalloc.c` + `mixer.c` 오프라인, WAV 파일로 렌더링.** *마일스톤 1*:
   `extract/adm-kr/files/sound_data.sdat`에서 `SSAR 0`, 엔트리 121을 디스크로 렌더링하고,
   공개 SDAT 플레이어가 같은 엔트리를 렌더링한 것과 바이트 비교한다. 그것은 시퀀스 바이트
   여덟 개와 6,020바이트 ADPCM 페이로드 하나(§3)이므로, 모든 불일치를 손으로 진단할 수 있다.
5. **완료 (열 개가 아니라 두 시퀀스). 더 큰 오프라인 코퍼스.** PSG, 노이즈, 드럼 세트, 키
   스플릿, 루프를 포괄하도록 고른 열 개의 시퀀스. 여전히 게임은 없다.
6. **완료. `sink_win32.c`와 배선.** `snd_arm7`의 무음 순회를 드라이버의 디스패처로 교체하고,
   `acww_frame`(`port/platform/frame.c`)에서 192 Hz 프레임을 구동하고, 싱크를 연다.
   *마일스톤 2*: 포트가 첫 소리를 낸다. 이것은 프런티어를 퇴행시킬 수 있는 첫 단계이므로,
   무음 순회를 복원하는 `ACWW_SND=0` 탈출구와 함께 단독으로 착지한다.
7. **완료 (2026-09-09). `capture.c`.** 두 캡처 유닛, 출력 셀렉터, 서라운드 감쇠, 마스터 팬이
   준수되고, `SETUP_CHANNEL_PCM/PSG/NOISE`와 `START_TIMER`/`STOP_TIMER`가 캡처 경로가 재생하는
   하드웨어 채널을 프로그래밍하고 시작한다. 의도적 편차는 사라졌다; `ACWW_SND_CAPTURE=0`이
   그것을 복원하며, 전후 영수증은 그 사이에서 측정된다. **§1과 §4의 부팅 가설은 측정으로
   확정되었다**: id별 인자 로그가 모든 노드의 네 워드를 모두 출력했고, 그것들은 §1이 예측한
   그대로였다 -- `LOCK_CHANNEL` 마스크 0x000A, 채널 1과 3에 왼쪽 끝과 오른쪽 끝으로 팬된
   타이머 512의 512워드 버퍼 두 개에 대한 `SETUP_CHANNEL_PCM` 둘, 같은(SAME) 두 버퍼에
   믹서(MIXER)로부터 루프 비트를 세팅한 `SETUP_CAPTURE` 둘, 그리고
   `OUTPUT_SELECTOR 1 2 1 1`(왼쪽은 Ch1에서, 오른쪽은 Ch3에서, 둘 다 믹서 우회). 셀렉터가
   정말로 준수된다는 영수증은 교차 상관이다: 캡처 켬 렌더는 캡처 끔 렌더를
   **1,025 샘플 = 31.28 ms 지연시킨 것, 계수 0.9962**이며, 지연 0에서는 0.2530이다 --
   산술이 예측한 대로 캡처 버퍼 하나 분량
   [`docs/kb/hybrid/audio.md` §7-8; `scratchpad/audio7/`].
8. **완료, 한쪽만 (2026-09-09). 차분 검사.** `READ_DRIVER_INFO`(id 33)가 구현되었다 -- 포트는
   이 ROM 자신의 구조체 오프셋으로 ARM9의 `SNDDriverInfo`를 채운다 -- 그리고 **이 ROM은 그것을
   결코 보내지 않는데**, 이는 OFF 레시피에 대해 §4의 네 번째 가설을 닫는다: 9,000프레임에
   걸친 상한 없는 집계는 id 0-32를 나열하고 33은 없다. 차분의 포트 쪽 절반은
   `ACWW_SND_DUMP=<frames>:<path>`이고; 원본 쪽 절반은 `port/tools/oracle/oracle.py`의
   `--snd-dump`와 `observer.lua`의 사운드 블록이며; `port/tools/oracle/
   snddiff.py`가 둘을 diff한다. **이 글이 쓰인 세션에서 에뮬레이터가 시작되지 않았으므로**
   (유휴, 675초 중 CPU 1.1초, 원장 없음, 마일스톤 8 이전 옵저버로도 같은 행), 아직 일치
   표는 존재하지 않는다.

   **차분이 비교할 수 있는 것은 이 페이지가 가정한 것보다 좁으며, 그것은 논증이 아니라
   측정된 것이다.** `SNDi_Work`는 0x037f8000의 ARM7 WRAM에 있는 ARM7 정적 변수이고 열여섯
   개의 SOUNDxCNT 레지스터는 ARM7 전용 I/O다; DeSmuME 0.9.13의 Lua는 어느 쪽에도 닿지 않고,
   실행 중인 에뮬레이터에 ARM9 `READ_DRIVER_INFO`를 주입할 방법도 없다. 비교 가능한(IS) 것은
   `SNDSharedWork` -- ARM9가 소유하므로 메인 RAM에 있다 -- 이며, 이것은 또한 게임 코드가 볼
   수 있는 드라이버의 유일한 부분이다. `observer.lua`는 어차피 닿지 않는 레지스터를 프로브하되
   0끼리 비교하는 대신 원시 결과를 기록한다.

   **8단계는 에뮬레이터 없이 테이블들을 확정했다.** `extract/`가 그것들을 갖고 있다:
   `AttackCoeffTable`은 `arm7/arm7.bin` +0xf2e0, `SNDi_DecibelSquareTable`은 +0xf1cc,
   `SNDi_DecibelTable`은 `arm9/unk_autoload_2.bin` +0x54dcc. 세 H 등급 재구성 중 둘은 ROM과
   바이트 단위로 동일했다; 세 번째 테이블은 통째로 빠져 있었는데, 그것이 시퀀서가 사용하는
   것이다(벨로시티, 두 트랙 볼륨, 플레이어 볼륨, 서스테인 레벨에 `SND_CalcDecibel`이 아니라
   `SND_CalcDecibelSquare`). 이 ROM에서 엔트리 0은 -723이고 공개 NitroSDK에서는 -32768이다:
   S가 P를 이기며 그 불일치가 내용이다.

### 상태: 여덟 단계 모두 완료, 그리고 차분이 이제 실행됨 (AUDIO8, 2026-09-10)

**AUDIO8 결과, 한 줄로: 드라이버는 만들어졌고 차분은 동작하며, 음악은 틀렸다.** 에뮬레이터
쪽 절반이 처음으로 실행되었다(DeSmuME 다섯 번 실행, 152초에 9,000프레임, 첫 실행 옆에
DirectSound 대화상자 해제기를 둠). `SNDSharedWork`는 ARM9 전역 `SNDi_SharedWork`
@0x022060a0를 역참조하여 찾는다 -- 틀렸던 하드코딩된 힙 주소가 아니라 -- 그리고 두 머신
모두 블록을 **0x02204620**에 둔다. 두 화면이 바이트 단위로 정확히 일치하는 유일한
창(프레임 100..300)에서, `captureStatus`, 캡처 쌍에서의 `channelStatus`, `finishCommandTag`,
그리고 시퀀서의 틱 레이트(TICK RATE)가 모두 정확히 일치하는 반면, 첫 시퀀스는 원본에서
트랙당 하나인 데 반해 **포트에서는 트랙당 세 채널**을 울리고, **원본의 틱 123에 대해 틱
84**에서 끝난다. 전체 표와 영수증:
`docs/kb/hybrid/audio-differential.md` §A10, `scratchpad/audio8/`.

### 상태: 여덟 단계 모두 완료 (AUDIO6 `115984f9`, AUDIO7 `36ee5abe`, 2026-09-09)

**마일스톤 6 = 6단계, 마일스톤 7 = 7단계, 마일스톤 8 = 8단계이며, 셋 모두 같은 밤에
착지했다.** `wiki/systems/audio.md`와 `docs/kb/hybrid/audio.md`가 포트가 오늘 무엇을 하는지에
대한 기록 페이지다; 아래의 서술은 마일스톤 1이 남긴 오프라인 전용 상태 그대로 보존되는데,
픽스처가 그것에 맞춰 만들어졌고 그것이 여전히 6단계 이전의 어떤 것도 프런티어를 퇴행시킬 수
없는 이유에 대한 논증이기 때문이다. 이에 대한 정정 두 가지: `port/tools/test_sndrender.py`는
이제 19개가 아니라 **22개 검사**이며, 그중 셋은 이 ROM 자신의 이미지에 대한 S 등급이다;
그리고 아래의 "마일스톤 2 -- 포트가 소리를 내는 것 -- 는 시작되지 않았다"는 철회된다 --
마일스톤 6으로 착지했다.

### 마일스톤 1이 남긴 오프라인 상태 (TOUCH41 재링크, 2026-09-09)

위의 2-4단계는 착지했으며 **오프라인 전용**이다: `port/shim/audio/{sdat,sbnk,swav,sseq,
chanalloc,mixer}.c`가 존재하고, `port/tools/sndrender.py`가 포트의 링크 바깥(OUTSIDE)에서
그것들을 수정 없이 컴파일하여(자체 no-CRT 하네스, `link.py`의 `GEN_FLAGS`) 이 ROM의
`sound_data.sdat`에서 시퀀스 하나를 WAV 파일로 렌더링한다. 여기의 어떤 것도 등록되지
않았고, `link.py`나 `overrides.txt`에 아무것도 나타나지 않으며, 이 도구의 어떤 호출도 게임이
하는 일을 바꿀 수 없다 -- 이것이 이 단계를 무음 보존이며 프런티어를 퇴행시킬 수 없게 만드는
것이다
[S: `port/tools/sndrender.py` header; `docs/log/cycle40-keyboard-gate-probe.md` TOUCH41;
`docs/state/port-frontier.md`].

`port/tools/test_sndrender.py`가 픽스처이며, **19개 검사**이고, 그 안의 모든 기대값은 시험
대상 C가 아닌 다른 곳에서 온다 [H: host/prose inference from `port/tools/test_sndrender.py` header;
`docs/log/cycle40-keyboard-gate-probe.md` TOUCH41, "audio milestone 1, 19 checks"; verify against the ROM function or symbol table and this page's recipe]:

- **시퀀서를 ndspy와 대조** -- C가 실제로 실행하는 모든 이벤트는 ndspy도 파싱한 오프셋에,
  같은 옵코드, 같은 총 길이, 같은 피연산자로 떨어져야 한다. 중요한 것은 길이다: SSEQ 옵코드
  집합에는 가변 길이 정수와 접두 옵코드 셋이 있으므로, 피연산자 폭을 잘못 잡은 디코더는 다음
  이벤트를 이 이벤트의 한가운데에서 읽게 된다. ndspy를 임포트할 수 없으면 픽스처는 로컬
  디코더로 폴백하고 그렇게 말한다(SAYS SO); 이는 C와 저자를 공유하므로 더 약한 근거다;
- **파형을 샘플 단위로** GBATEK의 의사코드로 작성한 두 번째 IMA-ADPCM 디코더와 대조하며,
  DS의 두 가지 편차(3분의 1 절삭, -0x7FFF 클램프)를 포함한다. 이것은 §3이 기록하는 불일치를
  결론짓는다: 두 오프라인 디코더가 예측기 헤더가 방출되는 샘플인지에 대해 12,033 샘플 대
  12,032로 갈렸다. **12,032가 옳으며**, SWAV 42 -- SSAR 0 / 엔트리 121 체인의 6,020바이트
  ADPCM 페이로드 -- 는 이제 샘플 하나하나까지 단언된다;
- **아카이브**를 §3의 주장 표와 대조: 개수들, 그리고 체인 SSAR 0 엔트리 121 -> 뱅크 154 ->
  WAVEARC 4 -> SWAR 파일 1499 -> SWAV 42의 모든 필드;
- **`mixer.c`의 `VolumeTable`**을 `src/matched/SND_CalcChannelVolume.c`에서 다시 읽어 바이트
  단위로 비교하므로, 디렉터리 안의 유일한 S 등급 상수 테이블이 표류할 수 없다.

**보정은 결과의 일부다 (M1).** 두 실행이 정답을 단언하면서 드라이버에 의도적으로 틀린 입력을
먹이며, 픽스처는 둘 다 잡힐 때에만 건전하다: `CALIBRATION-adpcm-nibble`은 ADPCM 니블 하나의
비트 하나를 뒤집고(차분 포맷이므로 디코드된 다이제스트가 바뀌어야 한다 -- 상수를 반환하는
"디코더"나 오래된 캐시 파일은 그냥 통과할 것이다), `CALIBRATION-tempo`는 템포 비율 절반으로
렌더링하며 같은(SAME) 이벤트가 같은 순서로 같은 피연산자로 다른(DIFFERENT) 드라이버
프레임에서 나오기를 요구하는데, 이것이 정말로 192 Hz 프레임과 `(tempo * tempoRatio) >> 8`
누산기를 돌리는 시퀀서를 이벤트 리스트를 곧장 훑는 것과 구별하는 유일한 방법이다 [H: host/prose inference from `port/tools/test_sndrender.py` header; verify against the ROM function or symbol table and this page's recipe].

~~마일스톤 2 -- 포트가 소리를 내는 것 -- 는 시작되지 **않았다**: 6단계는 프런티어를 퇴행시킬
수 있는 첫 단계이며 단독으로 착지한다.~~ **철회됨 (AUDIO6, `115984f9`): 착지했고, 이 문장이
요구한 대로 단독으로 착지했다.** `ACWW_SND=1`이면 포트는 게임 자신의 음악과 효과음을
재생한다; 스위치가 없으면 31프레임 OFF 레시피와 48,000프레임 마을 레시피 모두에서 프레임이
손대지 않은 빌드와 바이트 단위로 동일하다
[E: `docs/kb/hybrid/audio.md` sections 8 and 8(b2); `../systems/audio.md`].

---

## 3. 주장 표

아래의 새 측정은 **[S: image]** 등급이며, 메인 체크아웃의
`extract/adm-kr/files/sound_data.sdat`에서 읽었다(이 파일은 워크트리에 없다).

| 페이지와 주장 | 공개 기록 (P) | 판정 |
|---|---|---|
| `music.md`: "SEQ 슬롯 376, 정의된 것 342, SEQARC 216, BANK 943, WAVEARC 14, PLAYER 21, GROUP 30, STRM 2" | P: GBATEK/kiwi.ds INFO는 개수+오프셋 테이블 여덟 개 | **확인됨**; 그리고 FAT 매직 히스토그램은 정확히 `SSEQ` 336, `SSAR` 216, `SBNK` 943, `SWAR` 14, `STRM` 2 = 1,511 [S: image] |
| `music.md` 가설: "3,233,800바이트 파일은 두 스트림 중 하나다" | — | **확정: 그렇다.** STRM 0은 fileId 1509, 볼륨 112, 우선순위 64, 플레이어 0이며, 그 FAT 엔트리는 오프셋 7,136,480 크기 3,233,800이다. STRM 1은 fileId 1510, 334,436바이트 [S: image] |
| `music.md` 가설: "웨이브 아카이브 14개에 뱅크 943개는 많다; 곡별 선택인가?" | P: BANK 레코드는 최대 네 아카이브를 명명하며 0xFFFF는 미사용 | **확정: 그렇다, 그리고 질문보다 더 강하게.** 943개 뱅크 모두 정확히 **하나**의 아카이브만 명명한다; 서로 다른 튜플이 14개이고, 모두 싱글턴이며, 웨이브 아카이브당 하나다. 이 ROM의 어떤 뱅크도 다중 아카이브 기능을 쓰지 않는다 [S: image] |
| `music.md`: "SEQ 레코드는 12바이트: fileID u16, unknown u16, bankNo, volume, channelPriority, playerPriority, playerNo, reserved" | P: kiwi.ds/ndspy는 `u16 fileID; u16 unknown; ...`으로 읽는다 | **"unknown u16"은 unknown이 아니다.** SDK는 이를 `u32 fileId` 다음에 `NNSSndSeqParam { u16 bankNo; u8 volume; u8 channelPrio; u8 playerPrio; u8 playerNo; u16 reserved; }`로 타입 지정한다 [S: `src/matched/NNS_SndArcGetSeqInfo.c` and siblings]. 같은 바이트, 올바른 이름 |
| `music.md`: "BANK 레코드: fileID u16, unknown u16, waveArcNo 4개" | P: 같음 | **같은 정정**: `u32 fileId; u16 waveArcNo[4]` [S: `src/matched/NNS_SndArcGetBankInfo.c`] |
| `data-formats.md` W6: "SDAT 레코드를 채우고 필드 이름을 붙일 것" | — | **지금 가능, 모두 S 등급**, ROM 자신의 헤더로부터: WAVEARC는 `u32 fileId:24, flags:8`; PLAYER는 `u8 seqMax; u8 pad; u16 allocChBitFlag; u32 heapSize`; GROUP은 `u32 count` + `u8 type; u8 loadFlag; u16 pad; u32 index` 항목들; STRM은 `u32 fileId; u8 volume; u8 playerPrio; u8 playerNo; u8 flags`; STRMPLAYER는 `u8 numChannels; u8 chNoList[2]`; FAT 엔트리는 `u32 offset; u32 size; void *mem; u32 reserved` — "예약된 8바이트"는 이름 붙은 런타임 필드 둘이다 [S: `src/matched/NNS_SndArcGet*.c`] |
| `audio.md`: "공유 워크의 첫 워드는 `finishCommandTag`다" | P: `work.h` | **정확히 확인됨** [S: `src/matched/SND_GetPlayerStatus.c`]; 블록은 640바이트이고 그 옆의 세 상태 워드가 ARM7의 유일한 보고 채널이다 |
| `audio.md`: "복원된 요청은 id 2를 무조건 내보낸다; 마스크가 0이 아니면 id 9가 뒤따른다; 볼륨이 다르면 id 6; 준비된 플레이어에는 id 3" | P: id들은 맞다 | ~~**포트에서 미검증**, 로그가 프레임 3의 열두 줄에서 멈추기 때문.~~ **측정됨 (AUDIO6): 상한 없는 집계가 넷 모두를 본다**, 프레임 6부터. 드라이버 켬: id 2와 3이 각 371, id 6이 741, id 7이 2,270. 끔: id 2와 3이 각 967, id 6이 1,933인데, 무음 ARM7은 `playerStatus`를 결코 세팅하지 않아 게임이 시작하는 모든 시퀀스를 다시 시작하기 때문이다 [E: `docs/kb/hybrid/audio.md` section 8(c)] |
| `audio.md`: "아카이브 0 인덱스 121은 시퀀스 바이트 여덟 개(쉼표, 프로그램, 노트 하나, 끝), 뱅크 154, 웨이브 아카이브 4, 웨이브 42, 6,020바이트 ADPCM 페이로드 하나" | P: SSAR 레코드 레이아웃 | **모든 필드에서 확인됨, 그리고 이제 완전히 해석됨** [S: image]: SSAR 0은 fileId 336, 엔트리 552개, 데이터는 +6,656; 엔트리 121은 오프셋 2,334, 뱅크 154, 볼륨 127, chPrio 96, playerPrio 64, 플레이어 13. 그 바이트는 `80 5a`(쉼표 90), `81 00`(프로그램 0), `3c 3c 00`(노트 60, 벨로시티 60, 길이 0), `ff`(끝). 뱅크 154는 SBNK 파일 706, 76바이트, 타입 1(PCM) 악기 하나, 웨이브 아카이브 인덱스 0 → WAVEARC 4 → SWAR 파일 1499(웨이브 81개): SWAV 42, 포맷 2(ADPCM), 루프 없음, 16,000 Hz, 타이머 1,047, loopstart 1워드, looplen 1,504워드 → 6,032바이트 블록 안의 페이로드 6,020바이트 |
| `audio.md`: "5,550개 엔트리를 담은 시퀀스 아카이브 216개" | — | **모든 SSAR 자신의 count 필드를 합산하여 확인됨**: 5,550 [S: image] |
| `music.md`: "정의된 SEQ 레코드 342개이지만 서로 다른 물리적 시퀀스 파일은 336개" | — | **확인되고 설명됨**: fileId 넷이 둘 이상의 SEQ 레코드에서 참조된다; SEQ 테이블이 별칭을 갖는다. 또한 서로 다른 뱅크는 262개만 참조하므로, 943개 뱅크 중 681개는 SSAR 시퀀스에만 속한다 [S: image] |
| `music.md`: "`SYMB`가 없으므로 이름 기반 조회는 동작할 수 없다" | P: GBATEK — SYMB 부재는 지원되는 구성 | **라이브러리로도 확인됨**: `NNSSndArc`는 `symbol` 포인터를 갖지만 `src/matched/`의 모든 접근자는 인덱스 기반이다 [S] |
| `audio.md`: "두 오프라인 디코더가 ADPCM 예측기 헤더가 방출되는 샘플인지에 대해 12,033 대 12,032로 갈린다" | P: GBATEK — 4바이트 헤더는 초기 예측기와 인덱스이며, `SOUNDxLEN`은 ADPCM에 대해 `8*(N-1)` 샘플을 센다, 즉 헤더 워드는 샘플을 내지 않는다 | **스펙이 결론짓는다: 12,032.** 1,505워드 × 8 − 8 = 12,032. 12,033을 내는 디코더는 헤더의 초기 PCM 값을 샘플로 방출하고 있다 [P: `gbatek-ds-sound-channels-0-15.htm`] |
| `audio.md`: "포트는 프로토콜에 응답하고 아무것도 재생하지 않는다; 그것은 오디오를 향한 한 걸음이 아니다" | — | ~~**확인됨, 그리고 보존할 가치가 있다.**~~ **철회됨 2026-09-09**: `ACWW_SND=1`이면 포트가 재생한다. 유지된 절반은 무음 순회에 대한 해석이다 -- 그것이 공유 워크 주소와 완료 태그를 제공했고, 그것이 정확히 실제 드라이버가 출발한 부트스트랩이었다 [E: `docs/kb/hybrid/audio.md` section 1] |
| 공개: SBNK "단일 노트 정의는 16바이트" (kiwi.ds) | P: kiwi.ds는 자신의 필드 목록과 모순된다; GBATEK과 ndspy는 10이라 한다 | **10이 옳다** [S: `src/matched/SND_GetNextInstData.c`, `SNDInstParam` = `u16 wave[2]` + six `u8`]; 드럼 세트와 키 스플릿 안의 중첩 형태는 12(`u8 type; u8 pad;` + 그 10) |
| 공개: SBNK 악기 레코드는 "u8 type; u16 offset; u8 reserved" | P: ndspy는 `<BHx`로 읽는다 | **"reserved" 바이트는 오프셋의 상위 바이트다.** SDK는 레코드를 u32 하나로 읽어 8만큼 오른쪽 시프트하여 **24비트** 오프셋을 얻는다 [S: `src/matched/SND_GetNextInstData.c`] |
| 공개: `+0x08`의 SWAV 필드는 "non-loop length"(kiwi.ds) / "total length"(ndspy) / "loop end offset"(NitroStudio2) | 3자 충돌 | **SDK는 이를 `looplen`이라 부르며** `loopstart`와 짝짓는데, 이는 GBATEK의 `SOUNDxPNT`/`SOUNDxLEN`과 그 "원샷 길이 = PNT+LEN, 루프 = 1×PNT 후 ∞×LEN" 규칙에 1:1로 대응한다 [S: `src/matched/SND_GetWaveDataAddress.c`, `SNDWaveParam`] |
| 공개: SSEQ 옵코드 `0xD5`는 "expression" | P: `mml.h`는 이를 `SND_MML_VOLUME2`라 부른다 | **SDK 이름을 쓴다.** `SNDTrack`은 `volume` 옆에 `volume2` 필드를 가지며 그것이 쓰는 곳이다 [S: `src/matched/SND_ReadPlayerInfo.c`] [P: `mml.h`]. `0xD7 MUTE`도 존재하며 대부분의 커뮤니티 표에서 빠져 있다; `0xB7`과 `0xE2`는 빈칸이다 |
| 공개: "채널 0-7은 PCM 전용" | P: `channel.h` — `SND_PCM_CHANNEL_MASK 0xFFFF` | **틀렸으며, 이는 할당기에 중요하다.** 16채널 모두 PCM을 한다; 8-13은 *추가로* PSG를, 14-15는 *추가로* 노이즈를 한다 |
| 공개: `SNDDriverInfo` 레이아웃은 문서화되지 않음 | P: 검색이 닿은 어떤 공개 헤더에서도 찾지 못함 | **이 저장소가 갖고 있다**: `SNDWork work; u32 chCtrl[16]; SNDWork *workAddress; u32 lockedChannels; u32 padding[6]` [S: `src/matched/SND_ReadPlayerInfo.c`] |

---

## 4. 가설, 각각 그것을 결론짓는 실험과 함께

- ~~**게임은 측정된 경로에서 재생 명령을 결코 보내지 않는다.**~~ **확정, 그리고 M1이 예측한
  그대로 측정 산물이었다.** 여기 명명된 실험이 실행되었다: 열두 줄 상한이 제거되었고,
  9,000프레임 OFF 레시피에 걸친 집계는 **프레임 6**부터 `PREPARE_SEQ`와 `START_PREPARED_SEQ`를
  보며, 드라이버를 켠 상태에서 각 371개다
  [E: `docs/kb/hybrid/audio.md` section 8(c)]. 계측기가 이 가설의 근거의 전부였고, 그것은
  틀렸다.
- ~~**무음 ARM7은 게임 로직에 무기한 충분하다.**~~ **확정 (AUDIO6): 죽었으며, 정확히 여기
  제안된 실험에 의해서다.** 포트는 이제 SDK가 하듯 `PREPARE_SEQ` 안에서 `playerStatus`를
  세팅하고 `STOP_SEQ` 안에서 지우며, 게임의 동작이 측정 가능하게 바뀌었다:
  `NNSi_SndPlayerMain`이 시작된 모든 시퀀스를 해체해 오고 있었으므로, OFF 레시피는
  `PREPARE_SEQ` 967에서 371로, 뱅크 무효화 590에서 6으로 갔다
  [S: `src/matched/NNSi_SndPlayerMain.c`; E: `docs/kb/hybrid/audio.md` section 8(c)]. **아무것도
  정지하지(STALLED) 않았으므로**, "충분하다"에 대한 90,000프레임 근거는 참이었고 그 단어는
  여전히 틀렸다. `ACWW_SND_SHARED=0`이 비교를 위해 옛 동작을 유지한다.
- **§1의 부팅 시퀀스는 `NNS_SndCaptureStartOutputEffect`다.** **확정: 그렇다, 예측된 모든
  필드에서.** 실험이 실행되었다 -- `driver.c`의 id별 인자 로그 -- 그리고 그것은
  `LOCK_CHANNEL` 마스크 `0x000A`, 채널 1과 3에 대한 두 `SETUP_CHANNEL_PCM`, 비트 31이
  지워진 뒤 세팅된 `SETUP_CAPTURE`(유닛 0 다음 유닛 1, 이는 또한 pokediamond 명명이 아니라
  이 ROM의 빌더가 옳다는 교차 검증이다), 그리고 `OUTPUT_SELECTOR 1 2 1 1`을 냈다. 또한
  측정되었으나 여기서 예측되지 않은 것: `SURROUND_DECAY 0x3000`이 맨 먼저(FIRST) 도착하고,
  프레임 819부터 게임은 채널 6과 7도 하드웨어 PCM으로 프로그래밍한다(잠긴 마스크가 `0xCA`로
  커진다) -- NitroSDK의 스트리밍 오디오 경로
  [E: `scratchpad/audio7/args/run-tail.log`].
- **ROM의 `SNDDriverInfo`는 런타임에 결코 읽히지 않는다.** **OFF 레시피에 대해 확정: 결코
  읽히지 않는다.** 9,000프레임에 걸친 상한 없는 집계는 id 0-32를 나열하고 33은 없으므로, 이
  경로에서는 어떤 호출자도 실행되지 않는다. 그 명령은 프로토콜 자신의 상태 덤프이므로 어쨌든
  구현되었다(오디오 마일스톤 8); 호출자가 언젠가 실행된다면, 이제 초기화되지 않은 버퍼 대신
  이 ROM 자신의 구조체 오프셋으로 드라이버의 실제 상태를 얻는다.
- **음악은 시작 경계의 디컴파일되지 않은 네 호출자 중 하나 안의 시간 인덱스 테이블로
  선택된다** — `systems/audio.md`에서 그대로 이어받았으며, 이제 더 날카롭다: 아카이브에는
  독립 시퀀스 342개에 대해 아카이브된 시퀀스 5,550개가 있으므로, 음악을 선택하는 것이 무엇이든
  `(archive, index)` 쌍을 고르고 있으며, `func_020f1fb4`의 `0x79` 인자는 무언가에 대한
  인덱스다. *실험:* `func_020f1fb4`를 디스어셈블하여 RTC 시간으로 인덱싱되는 테이블을 찾는다.
- **정의되지 않은 SEQ 슬롯 34개는 잘린 음악이다.** *실험:* 그 인덱스를 나열하고 어떤 GROUP
  항목이든 그것을 참조하는지 확인한다; 참조되는 구멍은 패커 버그이고, 참조되지 않는 구멍은
  삭제다.
- **호스트 드라이버는 파형 단위가 아니라 명령 단위로 DeSmuME와 대조 검증할 수 있다.**
  **부분 확정, 그리고 도달 범위는 이 줄이 가정한 것보다 좁다.** `SNDi_Work`는 0x037f8000의
  ARM7 WRAM에 있는 ARM7 정적 변수이고 열여섯 개의 SOUNDxCNT 레지스터는 ARM7 전용 I/O다;
  DeSmuME 0.9.13의 Lua는 어느 쪽에도 닿지 않고, 실행 중인 에뮬레이터에 ARM9
  `READ_DRIVER_INFO`를 주입할 방법도 없다 — 따라서 32개 트랙의 `cur` 포인터와 16개 채널의
  `timer`/`volume`은 원본(ORIGINAL) 쪽에서는 전혀 읽을 수 없다. 비교 가능한(IS) 것은
  `SNDSharedWork`이며, ARM9가 소유하므로 메인 RAM에 있고, 또한 게임 코드가 볼 수 있는
  드라이버의 유일한 부분이다: 거기서 일치하는 두 드라이버는 게임이 관측할 수 있는 모든 것에서
  일치한다. 양쪽의 도구는 존재한다(`ACWW_SND_DUMP`, `oracle.py --snd-dump`,
  `port/tools/oracle/snddiff.py`); 그것들이 쓰인 세션에서 에뮬레이터가 시작되지 않았으므로,
  아직 일치 표는 존재하지 않는다 [`docs/kb/hybrid/audio-differential.md` §A10].

## 관련 문서

- `../audits/night-2026-09-09.md` — 그 밤의 색인에 있는 AUDIO6와 AUDIO7, 각각이 열어 둔
  것과 함께.
- `../systems/audio.md` — 이 설계가 섬기는 페이지; 그 주소 표와 전송에 대한 서술은 이 감사로
  바뀌지 않는다.
- `../data/music.md` — 아카이브의 형태; 그 가설 넷이 §3에서 확정된다.
- `data-formats.md` — **P** 등급 관례, 그리고 §3이 해소하는 W6/W10.
- `docs/kb/hybrid/hardware-services.md` §1 태그 7 — 경계에 대한 포트 측 서술.
