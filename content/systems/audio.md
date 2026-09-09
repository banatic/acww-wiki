# 오디오
<!-- source: wiki/systems/audio.md -->

**요약.** 놀러오세요 동물의 숲(Wild World)의 모든 사운드는 하나의 10.7 MB 아카이브 파일에 들어
있으며, 그중 어떤 것도 게임이 실행되는 프로세서에서 믹싱되지 않는다. ARM9는 명령의 연결 리스트를
만들고, 그 리스트의 주소를 단일 FIFO 워드로 ARM7에 넘긴 뒤, 공유 메모리의 카운터가 전진하기를
기다린다. ARM7이 시퀀서, 채널, 엔벨로프, 사운드 하드웨어를 소유한다. PC 포트는 그 프로토콜에
응답하되 아무것도 재생하지 않는다. 명령 리스트를 순회하며 모든 명령을 조용히 완료 처리하고 카운터를
올린다. 이것만으로 게임을 90,000프레임 동안 계속 실행시키기에 충분하며, 오디오를 향한 한 걸음은
아니다.

## 무슨 일이 일어나는가

### 아카이브

사운드 파일은 정확히 하나다. `sound_data.sdat`, 10,704,768바이트, SHA-256
`d89a5d75307a0c8bbb355b82d5a5189ac0938f348fffafc859fa588127edc1f5`
[S: operator extraction, recorded in `docs/kb/port/input-save-audio.md`]. INFO와 FAT 블록을 직접
파싱하면 SEQ 테이블 슬롯은 376개이지만 정의된 레코드는 342개, 물리적으로 구별되는 시퀀스 파일은
336개다. 5,550개 항목을 담은 216개의 시퀀스 아카이브, 943개의 뱅크, 14개의 웨이브 아카이브, 2개의
스트림이 있다 [S: same]. **이는 세 개의 서로 다른 분모이며 "376개의 SEQ 에셋"이라는 표현은 이를
뭉뚱그린다** [S: same; M1].

`NNS_SndArc*` 계층이 그 구조를 읽는다. `NNS_SndArcInit`은 카드에서 아카이브를 열고 검증하고,
`NNS_SndArcInitOnMemory`는 이미 RAM에 있는 이미지에서 그렇게 하며, `NNS_SndArcSetCurrent`는 이후
호출이 기본으로 사용할 핸들을 기록한다
[S: `NNS_SndArcInit`, `src/matched/NNS_SndArcInit.c`]. 그 다음 유형별 접근자가 INFO 블록을 읽는다.
`NNS_SndArcGetBankInfo`, `GetSeqInfo`, `GetSeqArcInfo`, `GetSeqArcParam`, `GetWaveArcInfo`,
`GetGroupInfo`, `GetPlayerInfo`, `GetStrmInfo`이다
[S: `src/matched/NNS_SndArcGetSeqArcParam.c` and siblings]. 그리고 `NNS_SndArcLoadGroup`은 내부
유형별 로더 `NNSi_SndArcLoadBank`, `LoadSeq`, `LoadSeqArc`, `LoadWaveArc`, `LoadFile`을 통해 이름
붙은 에셋 그룹을 끌어들인다 [S: `src/matched/NNS_SndArcLoadGroup.c`].
라이브러리가 할당하는 모든 것은 저장/복원 워터마크를 가진 자체 확장 힙에서 온다.
`NNS_SndHeapCreate`, `Alloc`, `SaveState`, `LoadState`이다
[S: `src/matched/NNS_SndHeapSaveState.c`].

### 시퀀스 재생

`0x0210e4c4`의 `NNS_SndArcPlayerStartSeqArc`는 세 인수 경계 `(handle, seqArcNo, index)`이다
[S: `src/matched/NNS_SndArcPlayerStartSeqArc.c`;
`docs/kb/port/input-save-audio.md`]. 전수 직접 교차 참조로 다섯 함수에서 여섯 개의 ROM 호출을
찾았다. `func_020eedb8`에서 한 번, `func_020f609c`에서 두 번, `func_020f6350`에서 한 번,
`func_020f7bc4`에서 한 번, `DWCi_SNDlPlay`에서 원시 주소를 통해 한 번이다. `func_020eedb8`은
의도적으로 인수를 그 순서로 재배열하며, 이는 트레이서 결함이 아니다
[S: `docs/kb/port/input-save-audio.md`].

그 아래에서 `NNSi_SndPlayerStartSeq`는 SDK 드라이버의 `SND_PrepareSeq`를 호출하며, 이는
`SND_AllocCommand`로 256항목 풀에서 명령 노드를 할당하고, 채운 뒤, `SND_PushCommand`로 예약
리스트에 덧붙인다. 아직 아무것도 전송되지 않는다
[S: `src/matched/NNSi_SndPlayerStartSeq.c`, `src/matched/SND_PrepareSeq.c`,
`src/matched/SND_PushCommand.c`]. `SND_FlushCommand`는 예약 리스트 전체를 대기 리스트로 옮기고
**연결 리스트의 주소**를 하나의 32비트 워드로 PXI 태그 7에 보내며, FIFO가 가득 차 있는 동안
재시도한다 [S: `src/matched/SND_FlushCommand.c`]. 따라서 명령 일괄 처리가 표준이다. 명령은 쌓이고
플러시 때에만 이동한다.

명령 id 29 `SHARED_WORK`는 두 프로세서가 장부 관리에 쓰는 블록의 주소를 ARM7이 알게 되는 방법이다.
리스트 전체를 처리한 뒤 ARM7은 그 블록의 첫 워드 `finishCommandTag`를 증가시킨다. ARM9 쪽에서는
`SND_RecvCommandReply`가 이를 읽고 완료된 노드를 순회하여 자유 리스트로 재활용하며,
`SND_IsFinishedCommandTag`와 `SND_WaitForCommandProc`는 호출자가 완료를 검사하거나 완료까지
스핀할 수 있게 한다
[S: `src/matched/SND_RecvCommandReply.c`, `src/matched/SND_WaitForCommandProc.c`,
`src/matched/SNDi_InitSharedWork.c`].

실제 재생에 필요한 명령 id는 알려져 있고 순서도 정해져 있다. 복원된 요청은 무조건 id 2
`PREPARE_SEQ`를 내보내고, id 9 `ALLOCATABLE_CHANNEL`은 플레이어의 할당 마스크가 0이 아닐 때에만
뒤따른다. 이후의 플레이어 메인 스텝에서 id 6 `PLAYER_PARAM`은 계산된 페이더나 볼륨이 달라졌을 때에만
내보내지고, 여전히 준비 상태인 플레이어는 id 3 `START_PREPARED_SEQ`를 내보낸다
[S: `docs/kb/port/input-save-audio.md`].

공유 워크 레이아웃은 선언 순서 추론이 필드 여섯 개를 잘못 배정한 뒤, 정확한 PC와 리터럴 교차 검증으로
복구되었다. 자유 리스트 헤드 `0x022045c8`, 회수된 태그 `0x022045cc`, 예약 리스트 헤드와 끝
`0x022045d0` / `0x022045d4`, 자유 리스트 테일 `0x022045d8`, 대기 읽기와 쓰기 `0x022045dc` /
`0x022045e0`, 대기 배치 수 `0x022045e4`, 현재 제출 태그 `0x022045e8`, `0x022045ec`의 아홉 항목
큐, `0x022048a0`의 256항목 명령 배열, 그리고 `0x02204620`과 `0x022060a0`의 공유 블록과 그 포인터다
[S: `docs/kb/port/input-save-audio.md`; retraction in
`docs/log/report-w12.md`].

이 모든 것 위에 플레이어(볼륨, 피치, 트랙별 매개변수, 채널 우선순위, 시퀀스 변수), 볼륨을 램프하는
페이더, 두 STRM 에셋을 위한 스트림 경로, 그리고 최종 믹스에 출력 이펙트를 적용하는 캡처 스레드가
있다
[S: `src/matched/NNS_SndPlayerSetTrackVolume.c`, `src/matched/NNSi_SndFaderUpdate.c`,
`src/matched/NNS_SndStrmStart.c`, `src/matched/NNSi_SndCaptureMain.c`].

### 포트가 하는 일

ARM9 절반은 ROM 코드이며 실행된다. 연속된 SDK 라이브러리 블록은 매칭된 257개 심볼 중 257개를
해석한다(NNS 사운드 187개, Nitro SND 69개, ITCM 알람 핸들러 1개). 다만 그 위의 게임 연결 코드가
그로써 완전해지는 것은 아니다 [S: `docs/kb/port/input-save-audio.md`].
`extract/adm-kr/arm7/arm7.bin`은 166,392바이트로 존재하며, **포트는 이를 패키징하지도, 로드하지도,
실행하지도 않는다**. `fsimage.py`는 ARM7 ROM 오프셋과 크기를 0으로 내보낸다
[S: `docs/kb/port/input-save-audio.md`].

인터프리터 경로에서 ARM7 사운드 프로세서 전체는 함수 하나다. `snd_arm7`은 ARM9가 보낸 워드에서
시작해 명령 리스트를 순회하고, 각 노드의 id를 읽고, id 29를 보면 공유 워크 주소를 기록하고, 처음
열두 개에 대해 `acww snd7: command id N completed silently`를 출력한 뒤, 공유 워크의 첫 워드를 한 번
증가시킨다. 이것이 ARM9가 기다리는 완료 태그다. 워드가 0이면 요청 처리기의 깨우기이며 아무것도
하지 않는다
[E: `port/shim/os/pxisend.c`; `docs/kb/hybrid/hardware-services.md` section 1, tag 7].

ARM9 명령 계층 자체는 의도적으로 대체하지 *않는다*. `sndcmd.c`, `sndflush.c`, `sndtag.c`는 거부
목록(deny list)에 있어 ROM 자체의 `SND_*Command` 함수가 실행되며, id 29만 받아들이던 이전의 가드는
부팅을 중단시켰다 [E: `port/tools/interp_registry.py`;
`docs/log/cycle40-keyboard-gate-probe.md` `off-D44`]. 아카이브는 호스트 파사드가 아니라 파일
시스템에서 오며, 이것 역시 강제된 것이다. 호스트 사운드 파사드가 "아카이브 없음"이라 응답하자 ROM의
`func_020f4b1c`가 `NNS_SndArcGetSeqArcParam`에서 NULL을 돌려받고, ROM 자체의 치명적 오류 경로
`func_0206e3ec`를 호출했으며, ROM의 크래시 화면이 약 830프레임부터 양쪽 화면이 검은 채로 루프했다
[E: `docs/log/cycle40-keyboard-gate-probe.md` CARD40..SND40]. ROM 자체의 본체가 쓰이도록 총 열네 개의
사운드 파일이 거부되어 있다. 아카이브, 플레이어, 힙 파일 열한 개(`sndinit.c`, `sndfacade.c`,
`sndframe.c`, `sndstart.c`, `sndplay.c`, `snd_playeropen.c`, `sequpdate.c`, `arcinfofamily.c`,
`arcbankinfo.c`, `arcseqinfo.c`, `sndheapstate.c`)와 위의 명령 계층 파일 세 개다
[S: `port/tools/interp_registry.py`, `DENY_FILES`, counted].

더 오래된 네이티브 경로에서는 태그 7이 대신 좁은 서비스에 도달하는데, 이 서비스는 SDK의 공유 워크
레이아웃과 일치하는 실제 자유, 예약, 대기 리스트를 유지하지만 id 29만 인식하고 나머지는 모두
거부한다 [E: `port/shim/os/pxisend.c`, `port/shim/audio/w12_sndservice.h`;
`docs/kb/port/input-save-audio.md`].

**아무것도 재생되지 않는다.** 지식 베이스는 경계를 정확히 밝힌다. 전송만으로는 시퀀스를 해석하거나,
뱅크나 웨이브 아카이브를 해석하거나, 채널을 할당하거나, 엔벨로프와 타이머를 전진시키거나, PCM을
생성할 수 없다 [S: `docs/kb/port/input-save-audio.md`].

### 가장 작은 가청 조각, 그리고 아직 시도되지 않은 이유

아카이브 0, 인덱스 121이 식별된 후보다. 시퀀스 아카이브 0의 항목 121은 시퀀스 바이트 여덟 개(쉼,
프로그램, 음표 하나, 끝)이며, 뱅크 154를 선택하고, 이어서 웨이브 아카이브 4와 웨이브 42, 즉
6,020바이트의 DS ADPCM 페이로드 하나를 선택한다 [S: `docs/kb/port/input-save-audio.md`]. 정적
도달 가능성 분석은 `func_020089dc -> func_020f1fb4(..., 0x79) -> func_020eede8 ->
func_020eedb8`을 찾아내며, 이는 핸들 `0x021fd04c`, 아카이브 0, 인덱스 121을 인코딩한다. 하지만
측정된 콜드 START 실행에서 12,000프레임까지 이는 실행되지 않았고, 그 선택자는 0에 머물렀다
[S: `docs/kb/port/input-save-audio.md`]. 두 오프라인 디코더는 ADPCM 예측기 헤더가 출력 샘플인지에
대해 의견이 갈리며(12,033샘플 대 12,032샘플), 따라서 어느 쪽도 충실도 기준(golden)이 아니다
[S: same]. 기록된 계획 추정치는 첫 명령 서비스 가청 조각에 2-4주, 견고한 호스트 에뮬레이션에
7-12주이며, 실제 ARM7을 호스팅하는 것은 1-2주의 타당성 조사와 8-14주 이상의 경로다
[S: same; they are estimates and were not calibrated].

## 어디에 있는가

| 함수 또는 심볼 | 모듈 | 역할 | 등급/출처 |
|---|---|---|---|
| `NNS_SndInit`, `NNS_SndMain` | autoload_2 (NNS) | 라이브러리 기동; 응답을 비우고 페이더를 갱신하는 프레임당 틱 | [S: `src/matched/NNS_SndMain.c`] |
| `NNS_SndArcInit`, `NNS_SndArcInitOnMemory`, `NNS_SndArcSetup` | autoload_2 (NNS) | 아카이브 열기와 검증 | [S: `src/matched/NNS_SndArcInit.c`] |
| `NNS_SndArcGetSeqArcParam` | autoload_2 (NNS) | 포트에서 NULL을 반환해 ROM을 치명적 오류 경로로 보낸 INFO 접근자 | [S: `src/matched/NNS_SndArcGetSeqArcParam.c`] [E: SND40] |
| `NNS_SndArcLoadGroup`, `NNSi_SndArcLoadBank`, `NNSi_SndArcLoadWaveArc` | autoload_2 (NNS) | 일괄 및 유형별 에셋 로딩 | [S: `src/matched/NNS_SndArcLoadGroup.c`] |
| `NNS_SndArcPlayerStartSeqArc` `0x0210e4c4` | autoload_2 (NNS) | `(handle, seqArcNo, index)` 요청 경계; ROM 호출자 여섯 개 | [S: `src/matched/NNS_SndArcPlayerStartSeqArc.c`] |
| `NNSi_SndPlayerStartSeq` `0x0210b148` / `NNSi_SndPlayerStopSeq` | autoload_2 (NNS) | SDK 드라이버를 호출하는 내부 시작과 정지 | [S: `src/matched/NNSi_SndPlayerStartSeq.c`] |
| `NNS_SndHeapCreate`, `Alloc`, `SaveState`, `LoadState` | autoload_2 (NNS) | 워터마크를 가진 라이브러리 자체 확장 힙 | [S: `src/matched/NNS_SndHeapSaveState.c`] |
| `NNSi_SndFaderUpdate`와 네 개의 형제 함수 | autoload_2 (NNS) | 플레이어와 스트림이 공유하는 볼륨 램프 | [S: `src/matched/NNSi_SndFaderUpdate.c`] |
| `NNS_SndStrmStart`, `NNS_SndArcStrmPrepare` | autoload_2 (NNS) | 직접 및 아카이브로부터의 스트림 재생 | [S: `src/matched/NNS_SndStrmStart.c`] |
| `NNSi_SndCaptureMain`, `NNS_SndCaptureStartOutputEffect` | autoload_2 (NNS) | 캡처 스레드와 최종 믹스 출력 이펙트 | [S: `src/matched/NNSi_SndCaptureMain.c`] |
| `SND_Init`, `SNDi_InitSharedWork` | autoload_2 (SND) | 드라이버 초기화와 공유 워크 블록의 필드 레이아웃 | [S: `src/matched/SNDi_InitSharedWork.c`] |
| `SND_AllocCommand`, `SND_PushCommand`, `SND_FlushCommand` | autoload_2 (SND) | 256노드 풀에서 할당, 예약, 그리고 태그 7로 리스트 주소 전송 | [S: `src/matched/SND_FlushCommand.c`] |
| `SND_RecvCommandReply`, `SND_IsFinishedCommandTag`, `SND_WaitForCommandProc` | autoload_2 (SND) | 완료: 완료 태그 읽기, 노드 회수, 또는 스핀 | [S: `src/matched/SND_RecvCommandReply.c`] |
| `SND_PrepareSeq` `0x02118204` / `SND_StartPreparedSeq` / `SND_StopSeq` | autoload_2 (SND) | 명령 id 2, 3과 정지 | [S: `src/matched/SND_PrepareSeq.c`] |
| `SNDi_SetPlayerParam`, `SNDi_SetTrackParam` | autoload_2 (SND) | id 6 `PLAYER_PARAM` 빌더 | [S: `src/matched/SNDi_SetPlayerParam.c`] |
| `SND_SetupChannelPcm`, `SND_CalcChannelVolume`, `SND_SetMasterVolume` | autoload_2 (SND) | 채널 및 믹서 인접 설정 | [S: `src/matched/SND_SetupChannelPcm.c`] |
| `PXI_SendWordByFifo` | autoload_2 | 태그 7이 실려 가는 FIFO 워드 전송 | [S: `src/matched/PXI_SendWordByFifo.c`] [E: replaced by `port/shim/os/pxisend.c`] |
| `DWCi_SNDlPlay`, `_Stop`, `_SetVolume`, `_SetPitch` | libdwcac | 네트워크 UI가 같은 플레이어 경로로 들어가는 훅 | [S: `src/matched/DWCi_SNDlPlay.c`] |
| `func_020eedb8`, `func_020f609c`, `func_020f6350`, `func_020f7bc4` | main | 시작 경계의 게임 연결 코드 호출자 네 개; 디컴파일되지 않음 | [S: `docs/kb/port/input-save-audio.md`] |

## 읽고 쓰는 데이터

| 주소 또는 필드 | 의미 | 쓰는 쪽 | 읽는 쪽 |
|---|---|---|---|
| `0x02204620` | 공유 워크 블록; 첫 워드는 `finishCommandTag` | ARM7 (포트: `snd_arm7`) | `SND_RecvCommandReply`, `SND_IsFinishedCommandTag` [S: `docs/kb/port/input-save-audio.md`] |
| `0x022060a0` | 그 블록을 가리키는 포인터 | `SNDi_InitSharedWork` | 드라이버 [S: same] |
| `0x022048a0` | 256항목 명령 배열 | `SND_AllocCommand` | ARM7 [S: same] |
| `0x022045c8` / `0x022045d8` | 명령 자유 리스트 헤드와 테일 | `SND_AllocCommand`, `SND_RecvCommandReply` | 할당자 [S: same] |
| `0x022045d0` / `0x022045d4` | 예약 리스트 헤드와 끝 | `SND_PushCommand` | `SND_FlushCommand` [S: same] |
| `0x022045dc` / `0x022045e0` / `0x022045e4` | 대기 읽기 인덱스, 쓰기 인덱스, 배치 수 | `SND_FlushCommand` | 응답 경로 [S: same] |
| `0x022045cc` / `0x022045e8` | 회수된 태그와 현재 제출 태그 | 응답 경로 / `SND_FlushCommand` | `SND_WaitForCommandProc` [S: same] |
| 노드 `+0x00` / `+0x04` / `+0x08` | 다음 포인터, 명령 id, 첫 번째 인수 | `SND_AllocCommand`와 빌더들 | ARM7 (포트는 셋 모두 읽는다) [E: `port/shim/os/pxisend.c`] |
| PXI 태그 7 | 명령 리스트의 주소를 실어 나르는 단일 워드 | `SND_FlushCommand` | `snd_arm7` [E: `port/shim/os/pxisend.c`] |
| `sound_data.sdat` | 아카이브 전체: 시퀀스 336개, 시퀀스 아카이브 216개, 뱅크 943개, 웨이브 아카이브 14개, 스트림 2개 | ROM 이미지 | 파일 시스템을 통한 `NNS_SndArc*` [S: `docs/kb/port/input-save-audio.md`] |

## 확인 방법

`../experiments/silent-audio-probe.md`(설계만 됨, 아직 미실행)는 마을 실행에서 `acww snd7:` 줄을
읽어내어 게임이 마을 회관으로 가는 길에 실제로 어떤 명령 id를 내보내는지 묻는다. 이는 2, 9, 6, 3에
도달하기는 하는지, 따라서 첫 가청 조각에 호스트 시퀀서가 얼마나 필요한지를 알아내는 가장 저렴한
방법이다.

## 가설

- 침묵하는 ARM7은 게임의 로직에 무기한 충분하다. 뒷받침하는 근거: 90,000프레임 동안 ROM의 치명적
  오류 경로로 재진입하지 않았다 [E: `scratchpad/cycle40/runs/tap-D59`, LONG41]. 이것이 가설로
  남는 이유는 ROM의 사운드 스택이 실제 플레이어 상태를 결코 보고하지 않는 소비자를 상대로 실행되므로,
  게임이 진행을 기다리는 시퀀스가 있다면 멈출 것이기 때문이다. 음악 주도 타이밍이 있는 씬에 대한
  오라클 비교로 해결된다
  [S: `docs/kb/hybrid/hardware-services.md` section 7].
- ACWW는 시리즈가 그러하듯 시간대별로 배경 음악을 선택한다. **매칭된 사운드 이름 심볼 중에서 그런
  테이블이나 함수는 발견되지 않았고**, RTC 파일은 어떤 사운드 심볼도 참조하지 않는다
  [S: absence in `src/matched`]. 존재한다면 시작 경계의 디컴파일되지 않은 호출자 네 개 중 하나 안에
  있다. `func_020f1fb4`를 디스어셈블하고 그 인덱스 인수에 공급되는 시간 인덱스 테이블을 찾으면
  해결된다.
- 아카이브 0 인덱스 121은 일반 플레이에서 도달 가능하며 첫 소리를 낼 것이다. 측정된 콜드 START
  실행에서 12,000프레임까지 요청되지 않았지만, 그 실행은 최소 128개 요청 중 19개만 샘플링했으므로
  일반 샘플링으로는 그 부재를 확정할 수 없다
  [S: `docs/kb/port/input-save-audio.md`; M11]. 마을 실행에 대한 제한 없는 요청 트레이스로
  해결된다.
- 그 과거 실행에서 처음 샘플링된 요청인 아카이브 19169 / 인덱스 280은 실제 요청이 아니라 상류의
  손상이다. 감사(audit)된 여섯 개의 직접 호출 지점 중 어느 것도 정적으로 그 조합을 공급하지 않으며,
  `DWCi_SNDlPlay`는 아카이브를 0으로 고정한다. 이는 단서이지 진단이 아니다. 간접 디스패치, 오래된
  상태, 손상된 데이터는 아직 분리되지 않았다
  [S: `docs/kb/port/input-save-audio.md`].

## 관련 문서

- `../experiments/silent-audio-probe.md`, `../experiments/two-tap-town-recipe.md`.
- `network.md` -- `DWCi_SNDl*`는 플레이어 경로의 다른 소비자다.
