# 오디오
<!-- source: wiki/systems/audio.md -->

**요약.** 놀러오세요 동물의 숲(Wild World)의 모든 사운드는 하나의 10.7 MB 아카이브 파일에 들어
있으며, 그중 어떤 것도 게임이 실행되는 프로세서에서 믹싱되지 않는다. ARM9는 명령의 연결 리스트를
만들고, 그 리스트의 주소를 단일 FIFO 워드로 ARM7에 넘긴 뒤, 공유 메모리의 카운터가 전진하기를
기다린다. ARM7이 시퀀서, 채널, 엔벨로프, 사운드 하드웨어를 소유한다.
**이제 PC 포트가 그 ARM7이다.** `ACWW_SND=1`이면 포트는 플레이어 열여섯 개, 트랙 서른두 개,
16채널 믹서, 캡처 유닛 두 개와 출력 선택기를 유지하고, 이를 ARM7 고유의 192 Hz로 스텝하며,
32,768 Hz 스테레오를 호스트 싱크에 넘긴다. ROM 자체의 아카이브에서 나온 게임 자체의 음악과
효과음이다. 스위치가 없으면 이전과 정확히 같이 리스트를 순회하며 모든 명령을 조용히 완료 처리한다.
요약 아래에서 "아무것도 재생되지 않는다"고 말하는 부분은 모두 철회되었으며, 철회에는 날짜와
출처가 붙어 있다.

## 무슨 일이 일어나는가

### 아카이브

사운드 파일은 정확히 하나다. `sound_data.sdat`, 10,704,768바이트, SHA-256
`d89a5d75307a0c8bbb355b82d5a5189ac0938f348fffafc859fa588127edc1f5`
[H: host/prose inference from operator extraction, recorded in `docs/kb/port/input-save-audio.md`; verify against the ROM function or symbol table and this page's recipe]. INFO와 FAT
블록을 직접 파싱하면 SEQ 테이블 슬롯은 376개이지만 정의된 레코드는 342개, 물리적으로 구별되는
시퀀스 파일은 336개다. 5,550개 항목을 담은 216개의 시퀀스 아카이브, 943개의 뱅크, 14개의 웨이브
아카이브, 2개의 스트림이 있다 [H: source account: `docs/kb/port/input-save-audio.md` (archive census); direct ROM-source provenance unresolved]. **이는 세 개의 서로 다른 분모이며 "376개의 SEQ
에셋"이라는 표현은 이를 뭉뚱그린다** [H: source account: `docs/kb/port/input-save-audio.md` (archive census); M1; direct ROM-source provenance unresolved].

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
[H: source account: `docs/kb/port/input-save-audio.md`; direct ROM-source provenance unresolved].

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
[H: source account: `docs/kb/port/input-save-audio.md`; direct ROM-source provenance unresolved].

공유 워크 레이아웃은 선언 순서 추론이 필드 여섯 개를 잘못 배정한 뒤, 정확한 PC와 리터럴 교차 검증으로
복구되었다. 자유 리스트 헤드 `0x022045c8`, 회수된 태그 `0x022045cc`, 예약 리스트 헤드와 끝
`0x022045d0` / `0x022045d4`, 자유 리스트 테일 `0x022045d8`, 대기 읽기와 쓰기 `0x022045dc` /
`0x022045e0`, 대기 배치 수 `0x022045e4`, 현재 제출 태그 `0x022045e8`, `0x022045ec`의 아홉 항목
큐, `0x022048a0`의 256항목 명령 배열, 그리고 `0x02204620`과 `0x022060a0`의 공유 블록과 그 포인터다
[H: source account: `docs/kb/port/input-save-audio.md`; retraction in
`docs/log/report-w12.md`; direct ROM-source provenance unresolved].

이 모든 것 위에 플레이어(볼륨, 피치, 트랙별 매개변수, 채널 우선순위, 시퀀스 변수), 볼륨을 램프하는
페이더, 두 STRM 에셋을 위한 스트림 경로, 그리고 최종 믹스에 출력 이펙트를 적용하는 캡처 스레드가
있다
[S: `src/matched/NNS_SndPlayerSetTrackVolume.c`, `src/matched/NNSi_SndFaderUpdate.c`,
`src/matched/NNS_SndStrmStart.c`, `src/matched/NNSi_SndCaptureMain.c`].

### 포트가 하는 일

ARM9 절반은 ROM 코드이며 실행된다. 연속된 SDK 라이브러리 블록은 매칭된 257개 심볼 중 257개를
해석한다(NNS 사운드 187개, Nitro SND 69개, ITCM 알람 핸들러 1개). 다만 그 위의 게임 연결 코드가
그로써 완전해지는 것은 아니다 [H: host/prose inference from `docs/kb/port/input-save-audio.md`; verify against the ROM function or symbol table and this page's recipe].
`extract/adm-kr/arm7/arm7.bin`은 166,392바이트로 존재하며, **포트는 이를 패키징하지도, 로드하지도,
실행하지도 않는다**. `fsimage.py`는 ARM7 ROM 오프셋과 크기를 0으로 내보낸다
[H: host/prose inference from `docs/kb/port/input-save-audio.md`; verify against the ROM function or symbol table and this page's recipe].

인터프리터 경로에서 ARM7의 사운드 프로세서는 호스트 것이다. AUDIO6 이전까지 그것은 함수 하나였다.
`snd_arm7`은 ARM9가 보낸 워드에서 시작해 명령 리스트를 순회하고, 각 노드의 id를 읽고, id 29를 보면
공유 워크 주소를 기록하고, 처음 열두 개에 대해 `acww snd7: command id N completed silently`를
출력한 뒤, 공유 워크의 첫 워드를 한 번 증가시켰다. 이것이 ARM9가 기다리는 완료 태그다. 워드가
0이면 요청 처리기의 깨우기이며 아무것도 하지 않는다
[H: log/source account: `port/shim/os/pxisend.c`; `docs/kb/hybrid/hardware-services.md` section 1, tag 7; receipt provenance unresolved]. 그
조용한 순회는 `ACWW_SND`가 없을 때 여전히 실행되는 것이며, 여전히 네이티브 경로의 전부이기도
하다.

ARM9 명령 계층 자체는 의도적으로 대체하지 *않는다*. `sndcmd.c`, `sndflush.c`, `sndtag.c`는 거부
목록(deny list)에 있어 ROM 자체의 `SND_*Command` 함수가 실행되며, id 29만 받아들이던 이전의 가드는
부팅을 중단시켰다 [E: `port/tools/interp_registry.py`;
`docs/log/cycle40-keyboard-gate-probe.md` `off-D44`; `scratchpad/cycle40/runs/off-D44`]. 아카이브는 호스트 파사드가 아니라 파일
시스템에서 오며, 이것 역시 강제된 것이다. 호스트 사운드 파사드가 "아카이브 없음"이라 응답하자 ROM의
`func_020f4b1c`가 `NNS_SndArcGetSeqArcParam`에서 NULL을 돌려받고, ROM 자체의 치명적 오류 경로
`func_0206e3ec`를 호출했으며, ROM의 크래시 화면이 약 830프레임부터 양쪽 화면이 검은 채로 루프했다
[H: log/source account: `docs/log/cycle40-keyboard-gate-probe.md` CARD40..SND40; receipt provenance unresolved]. ROM 자체의 본체가 쓰이도록 총 열네 개의
사운드 파일이 거부되어 있다. 아카이브, 플레이어, 힙 파일 열한 개(`sndinit.c`, `sndfacade.c`,
`sndframe.c`, `sndstart.c`, `sndplay.c`, `snd_playeropen.c`, `sequpdate.c`, `arcinfofamily.c`,
`arcbankinfo.c`, `arcseqinfo.c`, `sndheapstate.c`)와 위의 명령 계층 파일 세 개다
[H: source account: `port/tools/interp_registry.py`, `DENY_FILES`, counted; direct ROM-source provenance unresolved].

더 오래된 네이티브 경로에서는 태그 7이 대신 좁은 서비스에 도달하는데, 이 서비스는 SDK의 공유 워크
레이아웃과 일치하는 실제 자유, 예약, 대기 리스트를 유지하지만 id 29만 인식하고 나머지는 모두
거부한다 [H: log/source account: `port/shim/os/pxisend.c`, `port/shim/audio/w12_sndservice.h`;
`docs/kb/port/input-save-audio.md`; receipt provenance unresolved].

### 호스트 ARM7 사운드 드라이버 (`ACWW_SND=1`)

~~**아무것도 재생되지 않는다.**~~ **2026-09-09 철회 (AUDIO6, `115984f9`; AUDIO7, `36ee5abe`).**
포트는 게임 자체의 음악과 효과음을 재생한다. `port/shim/audio/driver.c`는 ROM이 태그 7로 보내는
SNDWork 블록 위의 ARM7 명령 처리기이고, `port/shim/audio/capture.c`는 캡처 유닛 두 개, 출력
선택기, 서라운드 감쇠이며, `port/shim/audio/sink_win32.c`는 호스트 스레드가 끌어가는
WASAPI(waveOut 폴백) 싱크다. 믹서는 프레임 경계에서 ARM7 고유의 192 Hz로 프레임마다 렌더링된다
[H: log/source account: `docs/kb/hybrid/audio.md` sections 1, 6 and 7; receipt provenance unresolved]. **호스트 아카이브는 없다**: ROM 자체의
`NNS_SndArcInit`이 포트의 가상 카트리지를 통해 `/sound_data.sdat`를 열고, `PREPARE_SEQ`가 실어
나르는 포인터는 NDS 주소이므로 `sdat.c`는 링크에서 빠진 채로 남는다
[H: log/source account: `docs/kb/hybrid/audio-banks.md`, section 2; receipt provenance unresolved]. 첫 무음 실행은 `swav.c`가 `waveOffset[]`를 파일 오프셋으로 읽은 것이
원인이었는데, 이 ROM의 WAVEARC 플래그 `0x01`은 그것을 NDS 주소로 만든다
[S: `src/matched/SND_GetWaveDataAddress.c`'s branch].

**명령 센서스.** 대체된 계측기는 열두 줄을 출력하고 멈췄으므로, 게임이 보낸 모든 `PREPARE_SEQ`가
보이지 않았고 감사(audit) 자체의 가설은 전혀 검증될 수 없었다. 이는 게임이 아니라 계측기의
인공물이다(M1) [H: log/source account: `docs/kb/hybrid/audio.md` section 3; receipt provenance unresolved]. 센서스는 이제 상한이 없고 드라이버가
켜져 있든 아니든 실행된다. id 0-4, 6-17, 19-33은 디스패치되고, `SKIP_SEQ`(5)와 `SETUP_ALARM`(18)은
로그만 남긴다. `SETUP_ALARM`은 이를 발화시키면 PXI를 통해 게임 코드로 워드를 되돌려보내어 사운드가
아니라 게임을 바꾸기 때문이다 [H: log/source account: `docs/kb/hybrid/audio.md` section 3; receipt provenance unresolved]. **이 ROM은 id 33 `READ_DRIVER_INFO`를 결코 보내지
않는다**: 9,000프레임 OFF 레시피에 대한 상한 없는 센서스는 id 0-32를 나열하며 33은 없다
[E: same, section 10; `scratchpad/audio7/`].

**ROM이 보내는 그대로의 기동 과정**은 예측이 아니라 id별로 상한이 있는 인수 로그에서 출력한 것이다
[E: `docs/kb/hybrid/audio.md` section 7; `scratchpad/audio7/args/run-tail.log`, frame 3]:
`SURROUND_DECAY 0x3000`, 그 다음 `LOCK_CHANNEL 0x000a`(채널 1과 3을 할당자에서 빼냄), 그 다음 그
두 채널을 타이머 512의 PCM으로 완전 왼쪽과 완전 오른쪽에, 512워드 버퍼 두 개 위에 프로그래밍한다.
그 다음 MIXER로부터 **같은 두 버퍼**에 루프 비트를 세운 `SETUP_CAPTURE` 두 번, 그 다음 버퍼
지속 시간의 절반에서 `SETUP_ALARM`, 그 다음 **`OUTPUT_SELECTOR 1 2 1 1`**(왼쪽은 Ch1에서,
오른쪽은 Ch3에서, 둘 다 믹서를 우회함)과 `START_TIMER`다. 재생 채널과 캡처 유닛이 버퍼 하나와
클럭 하나를 공유하므로, 스피커는 정확히 버퍼 하나만큼 지연되고 완전 왼쪽과 완전 오른쪽으로
다시 패닝된 믹서를 듣게 되며, 그동안 서라운드 감쇠는 1과 3을 제외한 모든 채널을 감쇠시킨다.
이것이 DS의 의사 서라운드다
[E: `scratchpad/audio7/args/run-tail.log`, frame 3; P: GBATEK, "the sample frequency of Channel 1/3 is shared for Capture 0/1"].

**선택기가 준수된다는 영수증**은 같은 바이너리를 `ACWW_SND_CAPTURE=0`으로 실행한 것과 기본값으로
실행한 것 사이의 교차 상관이다. 피크는 **지연 1,025샘플 = 31.28 ms, 계수 0.9962**이며, 지연
0에서는 0.2530이다. 산술은 1,024(타이머 512에서 512워드)를 예측하며, 추가된 샘플 하나는 믹서 스텝
하나 안에서 읽기가 쓰기에 앞서기 때문이다. 선택기를 무시하는 드라이버라면 지연 0에서 1.0000으로
상관되고 다른 어디에서도 상관되지 않을 것이다
[E: `scratchpad/audio7/wavcmp-nocap-vs-on.txt`; `docs/kb/hybrid/audio.md` section 8].

**테이블은 재구성한 것이 아니라 이 ROM 자체의 이미지에서 읽는다.** `AttackCoeffTable`은
`arm7.bin+0xf2e0`에, `SNDi_DecibelSquareTable`은 `arm7.bin+0xf1cc`에 있고, `SNDi_DecibelTable`은
`unk_autoload_2.bin+0x54dcc`에 있다 [H: source account: those images; `port/tools/test_sndrender.py` re-reads all three
at pinned offsets on every run; direct ROM-source provenance unresolved]. 등급 H 재구성 셋 중 둘은 바이트 단위로 동일했다. **오류는
테이블이 아니라 어느 테이블이냐였다.** 벨로시티, 두 트랙 볼륨, 플레이어 볼륨, 엔벨로프의 서스테인
레벨은 모두 `SND_CalcDecibel`이 아니라 `SND_CalcDecibelSquare`를 거치며, 두 곡선은 중간 스케일에서
4데시벨 차이가 난다(볼륨 64는 제곱 테이블에서 -239 십분의 일 단위, 일반 테이블에서는 -60)
[H: source account: the ROM images; P: NitroSDK `snd_seq.c`,
`snd_exchannel.c`; direct ROM-source provenance unresolved]. **두 테이블의 항목 0은 이 ROM에서 -723이며, 공개 NitroSDK에서는
-32768이다**. 이는 라이브러리의 다른 리비전이며, 그 불일치는 잡음이 아니라 내용이다. 공개 값으로
만든 드라이버는 0 항을 포함한 체인을 무음으로 클램프하지만 이 ROM은 그러지 않는다(STYLE 규칙 7)
[H: source account: the images vs P: the public source; direct ROM-source provenance unresolved]. 할당자는 라이브러리 고유의 순서
`{4,5,6,7, 2,0, 3,1, 8,9,10,11, 14,12,15,13}`로 채널을 순회하고, 동률은 할당 연령이 아니라 더
조용한 채널의 하드웨어 볼륨 워드로 가른다. 이것이 4..7 중 하나라도 비어 있는 동안 일반 음표를
채널 0..3에서 떨어뜨려 놓는 요인이며, 그 채널들은 정확히 캡처 경로가 쓰는 네 개다
[P: NitroSDK `snd_exchannel.c`, `SND_AllocExChannel` and
`CompareExChannelVolume`; E: `port/shim/audio/driver.c` walks that order, and
`port/tools/test_sndrender.py` holds the 418/418 note count across the change].

**`playerStatus`를 공개하자 게임이 하는 일이 바뀌었고, 그것이 발견 사항이다.**
`NNSi_SndPlayerMain`은 `playerStatus`가 자기 비트를 담고 있지 않는 순간 플레이어를 종료한다
[S: `src/matched/NNSi_SndPlayerMain.c`]. 침묵하는 ARM7을 상대로는 그 비트가 결코 세워지지
않았으므로, **게임이 시작한 모든 음악이 실행 내내 해체되고 다시 시작되었다**. 371개면 충분한
`PREPARE_SEQ`가 967개, 6개면 충분한 뱅크 무효화가 590개였다. 포트는 줄곧 그렇게 해 왔고 아무것도
이를 드러내지 않았다 [H: log/source account: `docs/kb/hybrid/audio.md` section 8(c); receipt provenance unresolved].
`ACWW_SND_SHARED=0`이 탈출구이며, 상태 공개가 게임이 볼 수 있는 것을 바꾸는 변경이기 때문에
존재한다.

**바뀌지 않는 것: 화면.** OFF 레시피, 환경 변수 하나씩만 다른 네 조건(손대지 않은 빌드,
`ACWW_SND=0`, 캡처 경로를 끈 `ACWW_SND=1`, 그리고 켠 것):
**모든 짝에서 31프레임 중 31프레임이 정확히(RGB) 일치**, 평균 ncc 1.0000
[E: `scratchpad/audio7/frame-exactness.txt`]. 48,000프레임 마을 레시피 전체에 걸쳐 `ACWW_SND`
미설정 대 `ACWW_SND=1`은 **15개 스크린샷 중 15개가 바이트 단위로 동일**하며 둘 다 종료 코드 100이다
[E: `scratchpad/stab42/`; STAB42]. `ACWW_SND`가 미설정이면 싱크 스레드는 아예 생성되지 않는다.

**마일스톤과 각각이 닫은 것.** 마일스톤 6은 드라이버와 싱크다(AUDIO6, `115984f9`). 마일스톤 7은
캡처 경로이며, 마일스톤 6의 유일한 의도적 편차(포트가 믹서를 그대로 재생하고 출력 선택기를
무시한 것)를 제거했다. 마일스톤 8은 `READ_DRIVER_INFO`와 차분 비교다(둘 다 AUDIO7, `36ee5abe`).
감사의 빌드 순서 여덟 단계가 모두 완료되었다 [H: source account: `../audits/audio-design.md` section 2, "Build order"; direct ROM-source provenance unresolved].
픽스처: `port/tools/test_sndrender.py` 22/22(그중 셋은 이 ROM의 이미지에 대한 등급 S),
`port/tools/test_snddispatch.py` 31/31과 보정 세 개. 그중 하나는 ROM 자체의 기동 명령 열두 개를
재생하며, 캡처 유닛을 시작하는 `START_TIMER` 비트 하나를 제거했을 때 스피커가 **피크 0**이 될 것을
요구한다. 그때 재생 채널은 아무것도 채우지 않는 버퍼를 읽고 있기 때문이다. 선택기를 무시하는
드라이버는 둘 다에서 똑같이 시끄럽다
[H: log/source account: `docs/kb/hybrid/audio.md` section 8(d); receipt provenance unresolved].

**영수증이 없는 것: 싱크 자체.** 이 기계에서 `waveOutGetNumDevs()`는 0을 반환하고 WASAPI의
`GetDefaultAudioEndpoint`는 `ERROR_NOT_FOUND`를 반환하는데, 기계에는 오디오 장치가 아홉 개 있고
Audiosrv는 실행 중이다. `MMDeviceEnumerator`에 대한 `CoCreateInstance`는 성공하므로 엔드포인트까지의
COM 경로는 실행되고 그 너머는 실행되지 않는다. 실패하는 모든 단계는 자기 HRESULT를 출력하며,
`scratchpad/audio6/sinktest.py`는 싱크 하나만으로 구형파를 밀어 넣는다
[H: log/source account: `docs/kb/hybrid/audio.md` section 8; receipt provenance unresolved].

### 가장 작은 가청 조각 -- 확보되었고, 아카이브 전체도 함께

아카이브 0, 인덱스 121이 식별된 후보였고 여전히 픽스처의 척추다. 시퀀스 아카이브 0의 항목 121은
시퀀스 바이트 여덟 개(쉼, 프로그램, 음표 하나, 끝), 뱅크 154, 웨이브 아카이브 4, 웨이브 42, 즉
6,020바이트의 DS ADPCM 페이로드 하나다 [H: source account: `docs/kb/port/input-save-audio.md`;
confirmed field by field in `../audits/audio-design.md` section 3; direct ROM-source provenance unresolved]. 12,033샘플 대 12,032샘플로
의견이 갈리던 두 오프라인 디코더는 ADPCM 헤더에 대한 GBATEK으로 정리되었다.
**12,032**이며, SWAV 42는 이제 픽스처가 샘플 단위로 단언한다
[P: `gbatek-ds-sound-channels-0-15.htm`; S: `../audits/audio-design.md` section 3].

~~기록된 계획 추정치는 첫 명령 서비스 가청 조각에 2-4주, 견고한 호스트 에뮬레이션에
7-12주다.~~ **사건에 추월됨**: 드라이버, 캡처 경로, 차분 비교 도구는 하룻밤에 만들어졌다
[H: log/source account: `docs/log/cycle40-keyboard-gate-probe.md` AUDIO6 and AUDIO7; receipt provenance unresolved]. OFF 레시피에서 포트는 시퀀스
371개, 동시 16채널, 9,000 게임 프레임에 대한 28,877 드라이버 프레임(192/59.8261 x 9,000 =
28,884)에 걸쳐 **시도한 418음 중 418음을 소리 냈고 하나도 빠뜨리지 않았으며**, 첫 소리는 36-38
프레임에서 났고, 레시피가 요구하는 150.44 s에 대해 150.40 s WAV를 썼다
[E: `scratchpad/audio7/on/capture.wav`; `docs/kb/hybrid/audio.md` section 8(a)].

## 어디에 있는가

| 함수 또는 심볼 | 모듈 | 역할 | 등급/출처 |
|---|---|---|---|
| `NNS_SndInit`, `NNS_SndMain` | autoload_2 (NNS) | 라이브러리 기동; 응답을 비우고 페이더를 갱신하는 프레임당 틱 | [S: `src/matched/NNS_SndMain.c`] |
| `NNS_SndArcInit`, `NNS_SndArcInitOnMemory`, `NNS_SndArcSetup` | autoload_2 (NNS) | 아카이브 열기와 검증 | [S: `src/matched/NNS_SndArcInit.c`] |
| `NNS_SndArcGetSeqArcParam` | autoload_2 (NNS) | 포트에서 NULL을 반환해 ROM을 치명적 오류 경로로 보낸 INFO 접근자 | [S: `src/matched/NNS_SndArcGetSeqArcParam.c`] [H: log/source account: `docs/log/cycle40-keyboard-gate-probe.md` SND40; receipt provenance unresolved] |
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
| `PXI_SendWordByFifo` | autoload_2 | 태그 7이 실려 가는 FIFO 워드 전송 | [S: `src/matched/PXI_SendWordByFifo.c`] [H: log/source account: replaced by `port/shim/os/pxisend.c`; receipt provenance unresolved] |
| `DWCi_SNDlPlay`, `_Stop`, `_SetVolume`, `_SetPitch` | libdwcac | 네트워크 UI가 같은 플레이어 경로로 들어가는 훅 | [S: `src/matched/DWCi_SNDlPlay.c`] |
| `func_020eedb8`, `func_020f609c`, `func_020f6350`, `func_020f7bc4` | main | 시작 경계의 게임 연결 코드 호출자 네 개; 디컴파일되지 않음 | [H: source account: `docs/kb/port/input-save-audio.md`; direct ROM-source provenance unresolved] |
| `acww_snd_command` (`driver.c`) | 포트 | 호스트 ARM7: 플레이어 열여섯 개, 트랙 서른두 개, 16채널 믹서, 센서스 | [H: log/source account: `port/shim/audio/driver.c`; `docs/kb/hybrid/audio.md` section 3; receipt provenance unresolved] |
| `capture.c` | 포트 | 캡처 유닛 두 개, `OUTPUT_SELECTOR`, 서라운드 감쇠, 하드웨어 채널 | [H: log/source account: `port/shim/audio/capture.c`; `docs/kb/hybrid/audio.md` section 7; receipt provenance unresolved] |
| `sink_win32.c` | 포트 | 유일한 스레드 경계: WASAPI로 들어가는 65,536프레임 무잠금 링, waveOut 폴백 | [H: host-source account from `port/shim/audio/sink_win32.c`; verify with a retained scripted run and frame using this page's recipe] |
| `SND_CalcDecibelSquare` `arm7.bin+0xf1cc` (테이블) | ARM7 이미지 | 벨로시티, 두 트랙 볼륨, 플레이어 볼륨, 서스테인 레벨이 거치는 테이블 | [H: source account: `extract/adm-kr/arm7/arm7.bin`, re-read by `port/tools/test_sndrender.py`; direct ROM-source provenance unresolved] |
| `SNDi_DecibelTable` `unk_autoload_2.bin+0x54dcc`, `AttackCoeffTable` `arm7.bin+0xf2e0` | 이미지 | 나머지 상수 테이블 두 개; 두 데시벨 테이블의 항목 0은 이 ROM에서 **-723**이다 | [H: source account: the `extract/adm-kr/arm7/arm7.bin` and `extract/adm-kr/arm9/unk_autoload_2.bin` two images; direct ROM-source provenance unresolved] |

## 읽고 쓰는 데이터

| 주소 또는 필드 | 의미 | 쓰는 쪽 | 읽는 쪽 |
|---|---|---|---|
| `0x02204620` | 공유 워크 블록; 첫 워드는 `finishCommandTag` | ARM7 (포트: `snd_arm7`) | `SND_RecvCommandReply`, `SND_IsFinishedCommandTag` [H: source account: `docs/kb/port/input-save-audio.md`; direct ROM-source provenance unresolved] |
| `0x022060a0` | 그 블록을 가리키는 포인터 | `SNDi_InitSharedWork` | 드라이버 [H: source account: `docs/kb/port/input-save-audio.md`; direct ROM-source provenance unresolved] |
| `0x022048a0` | 256항목 명령 배열 | `SND_AllocCommand` | ARM7 [H: source account: `docs/kb/port/input-save-audio.md`; direct ROM-source provenance unresolved] |
| `0x022045c8` / `0x022045d8` | 명령 자유 리스트 헤드와 테일 | `SND_AllocCommand`, `SND_RecvCommandReply` | 할당자 [H: source account: `docs/kb/port/input-save-audio.md`; direct ROM-source provenance unresolved] |
| `0x022045d0` / `0x022045d4` | 예약 리스트 헤드와 끝 | `SND_PushCommand` | `SND_FlushCommand` [H: source account: `docs/kb/port/input-save-audio.md`; direct ROM-source provenance unresolved] |
| `0x022045dc` / `0x022045e0` / `0x022045e4` | 대기 읽기 인덱스, 쓰기 인덱스, 배치 수 | `SND_FlushCommand` | 응답 경로 [H: source account: `docs/kb/port/input-save-audio.md`; direct ROM-source provenance unresolved] |
| `0x022045cc` / `0x022045e8` | 회수된 태그와 현재 제출 태그 | 응답 경로 / `SND_FlushCommand` | `SND_WaitForCommandProc` [H: source account: `docs/kb/port/input-save-audio.md`; direct ROM-source provenance unresolved] |
| 노드 `+0x00` / `+0x04` / `+0x08` | 다음 포인터, 명령 id, 첫 번째 인수 | `SND_AllocCommand`와 빌더들 | ARM7 (포트는 셋 모두 읽는다) [H: source/log account from `port/shim/os/pxisend.c`; verify with a retained run using this page's recipe] |
| PXI 태그 7 | 명령 리스트의 주소를 실어 나르는 단일 워드 | `SND_FlushCommand` | `snd_arm7` [H: source/log account from `port/shim/os/pxisend.c`; verify with a retained run using this page's recipe] |
| `sound_data.sdat` | 아카이브 전체: 시퀀스 336개, 시퀀스 아카이브 216개, 뱅크 943개, 웨이브 아카이브 14개, 스트림 2개 | ROM 이미지 | 파일 시스템을 통한 `NNS_SndArc*` [H: source account: `docs/kb/port/input-save-audio.md`; direct ROM-source provenance unresolved] |
| 공유 워크 `+0x04` `playerStatus` | 열여섯 플레이어 중 어느 것이 살아 있는가 | ARM7 (포트, `PREPARE_SEQ` / `STOP_SEQ` 안에서) | `NNSi_SndPlayerMain`, 비트가 꺼져 있으면 플레이어를 종료한다 [S: `src/matched/NNSi_SndPlayerMain.c`; E: `docs/kb/hybrid/audio.md` section 5] |
| 공유 워크 `+0x08` / `+0x0a` `channelStatus` / `captureStatus` | 어느 채널과 캡처 유닛이 실행 중인가 | ARM7 (포트) | ARM9 사운드 코드; 기계의 나머지가 볼 수 있는 유일한 ARM7 상태 [S: `src/matched/SND_GetPlayerStatus.c`] |
| `0x02143420` / `0x02143c20`의 512워드 버퍼 두 개 | 캡처 유닛당 하나, 재생 채널 1과 3과 공유 | 캡처 유닛 0/1 (포트의 `capture.c`) | 채널 1과 3, 버퍼 하나 뒤에서 [E: `scratchpad/audio7/args/run-tail.log`] |

## 확인 방법

`../experiments/silent-audio-probe.md`는 게임이 실제로 어떤 명령 id를 내보내는지 물었다. 그것은
답이 나왔다. 드라이버를 켠 채 OFF 레시피(`off-recipe.md`)를 실행하고 실행이 정지할 때 출력하는
센서스를 읽으면 된다.

    # every run prints `acww snd7 census:` whether or not the driver is on
    ACWW_SND=1 ACWW_SND_NOSINK=1 ACWW_SND_WAV=<path>.wav <the OFF recipe>

`ACWW_SND_CAPTURE=0`은 마일스톤 7을 다시 끄는 조건이며, 전/후 영수증은 이를 사이에 두고 측정된다.
`ACWW_SND_SHARED=0`은 포트가 ARM9에 상태를 되돌려 공개하는 것을 멈추고,
`ACWW_SND_DUMP=<frames>:<path>`는 마일스톤 8 차분 비교의 포트 쪽 절반을 쓴다
[H: log/source account: `docs/kb/hybrid/audio.md` section 6; receipt provenance unresolved]. ROM이 전혀 없어도
`python port/tools/test_snddispatch.py`(검사 31개, 보정 세 개)와
`python port/tools/test_sndrender.py`(검사 22개, 그중 셋은 이 ROM의 이미지에 대한 것)가
픽스처다 [H: log/source account: `docs/kb/hybrid/audio.md`, section 8(d); receipt provenance unresolved].

## 가설

- ~~침묵하는 ARM7은 게임의 로직에 무기한 충분하다.~~ **2026-09-09 해결됨(AUDIO6), 그리고
  충분하지 않았다.** 여기서 지목한 메커니즘이 옳았다. `playerStatus`를 결코 세우지 않는 소비자를
  상대로 `NNSi_SndPlayerMain`은 시작된 모든 시퀀스를 해체했고 게임은 이를 다시 시작했다. OFF
  레시피에서 371개면 충분한 `PREPARE_SEQ`가 967개, 6개면 충분한 뱅크 무효화가 590개였다. 아무것도
  멈추지 않았으므로 90,000프레임 근거는 유효하다. 틀린 것은 "충분하다"였다
  [H: log/source account: `docs/kb/hybrid/audio.md` section 8(c);
  S: `src/matched/NNSi_SndPlayerMain.c`; receipt provenance unresolved].
- **H: 믹스는 단지 존재하는 것이 아니라 정확하다.** 아직 아무것도 포트의 드라이버 상태를 원본의
  것과 비교하지 않았다. `SNDSharedWork`가 유일하게 비교 가능한 부분이다. ARM9가 소유하므로 메인
  RAM에 있고, 게임 코드가 볼 수 있는 드라이버의 유일한 부분이기도 하다. `SNDi_Work`와 열여섯 개의
  SOUNDxCNT 레지스터는 ARM7 쪽이며 DeSmuME 0.9.13의 Lua는 어느 쪽에도 닿지 못하고, 실행 중인
  에뮬레이터에 ARM9 `READ_DRIVER_INFO`를 주입할 방법도 없다. 도구의 양쪽 절반은 모두 존재한다
  (`ACWW_SND_DUMP`, `oracle.py --snd-dump/--snd-shared`, `port/tools/oracle/snddiff.py`).
  **마일스톤 8이 작성된 세션에서 에뮬레이터가 시작되지 않았다**. 세 번 시도했고, 매번 프로세스는
  살아 있고 응답하며 675 s 동안 CPU를 1.1 s 사용한 채로 남았고, 마일스톤 8 이전의 관측기로도
  마찬가지였으므로, 이는 Lua의 문제가 아니라 환경의 사실이다. `port/tools/oracle/oracle.py --frames
  100`을 그대로 실행하고 이유를 알아내면 해결된다 [H: log/source account: `docs/kb/hybrid/audio-differential.md` section A10; receipt provenance unresolved].
- **H: 채널 6과 7을 루프시키는 것이 재생하지 않는 것보다 하드웨어에 가깝다.** 819프레임부터 게임은
  그 채널들을 하드웨어 PCM(NitroSDK의 스트림 경로)으로 프로그래밍하며, `SETUP_ALARM`이 발화되지
  않으면 아무것도 스트림의 버퍼를 전진시키지 않으므로, 그 채널들은 ARM9가 마지막으로 쓴 것을
  되풀이해 재생한다. 마일스톤 6은 이를 전혀 재생하지 않았고 마일스톤 7은 루프시켜 재생한다. 어느
  쪽이 옳은지는 확립되지 않았다. 위의 차분 비교를 그 두 채널에 먼저 겨냥하면 해결된다
  [H: log/source account: `docs/kb/hybrid/audio.md` section 7; receipt provenance unresolved].
- **H: 디코딩된 웨이브 아레나 24 MB는 긴 세션에 충분하다.** 아레나는 범프 할당자다. 가득 차면 모든
  채널이 정지되고 캐시가 버려지고 되감긴다. 영구적 침묵이 아니라 클릭 한 번이다. OFF 레시피는 이를
  0번 재활용한다. 긴 라이브 세션 끝에 실행 보고서의 재활용 카운터를 읽으면 해결된다
  [H: log/source account: `docs/kb/hybrid/audio-differential.md` section A11; receipt provenance unresolved].
- ACWW는 시리즈가 그러하듯 시간대별로 배경 음악을 선택한다. **매칭된 사운드 이름 심볼 중에서 그런
  테이블이나 함수는 발견되지 않았고**, RTC 파일은 어떤 사운드 심볼도 참조하지 않는다
  [H: source account: absence in `src/matched`; direct ROM-source provenance unresolved]. 존재한다면 시작 경계의 디컴파일되지 않은 호출자 네 개 중 하나 안에
  있다. `func_020f1fb4`를 디스어셈블하고 그 인덱스 인수에 공급되는 시간 인덱스 테이블을 찾으면
  해결된다.
- ~~아카이브 0 인덱스 121은 일반 플레이에서 도달 가능하며 첫 소리를 낼 것이다.~~ **후반부는
  해결되었고 거짓이다**: OFF 실행의 첫 소리는 36-38프레임에서 나고 9,000프레임 동안 418음이
  소리 나므로, 무엇이 먼저 재생되든 그 체인을 기다리고 있는 것은 아니다
  [H: log/source account: `docs/kb/hybrid/audio.md` section 8(a); receipt provenance unresolved]. 인덱스 121에 도달하기는 하는지는 여전히 열려
  있으며, 상한 없는 센서스가 이제 그것을 위한 계측기다. 원래 문구는 다음과 같다.
- 아카이브 0 인덱스 121은 일반 플레이에서 도달 가능하며 첫 소리를 낼 것이다. 측정된 콜드 START
  실행에서 12,000프레임까지 요청되지 않았지만, 그 실행은 최소 128개 요청 중 19개만 샘플링했으므로
  일반 샘플링으로는 그 부재를 확정할 수 없다
  [H: source account: `docs/kb/port/input-save-audio.md`; M11; direct ROM-source provenance unresolved]. 마을 실행에 대한 상한 없는 요청 트레이스로
  해결된다.
- 그 과거 실행에서 처음 샘플링된 요청인 아카이브 19169 / 인덱스 280은 실제 요청이 아니라 상류의
  손상이다. 감사(audit)된 여섯 개의 직접 호출 지점 중 어느 것도 정적으로 그 조합을 공급하지 않으며,
  `DWCi_SNDlPlay`는 아카이브를 0으로 고정한다. 이는 단서이지 진단이 아니다. 간접 디스패치, 오래된
  상태, 손상된 데이터는 아직 분리되지 않았다
  [H: source account: `docs/kb/port/input-save-audio.md`; direct ROM-source provenance unresolved].

## 관련 문서

- `../experiments/silent-audio-probe.md`, `../experiments/two-tap-town-recipe.md`,
  `../experiments/off-recipe.md` -- 모든 오디오 영수증이 측정되는 대조 실행.
- `../audits/audio-design.md` -- 명령 테이블, 아카이브의 주장 테이블, 여덟 단계 빌드 순서. 여덟
  단계 모두 완료되었다.
- `../audits/night-2026-09-09.md` -- 그날 밤의 색인에 있는 AUDIO6과 AUDIO7.
- `network.md` -- `DWCi_SNDl*`는 플레이어 경로의 다른 소비자다.
- `docs/kb/hybrid/audio.md` -- 구현 페이지: 무엇이 디스패치되고, 무엇이 의도적 no-op이고, 무엇이
  로그만 남기는지, 그리고 이 페이지 뒤의 모든 영수증.
