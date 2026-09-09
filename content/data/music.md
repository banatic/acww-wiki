# 음악과 사운드
<!-- source: wiki/data/music.md -->

**요약.** 게임의 모든 오디오는 파일 시스템 루트에 있는 10.7 MB 크기의 `SDAT` 아카이브 하나,
`sound_data.sdat`이다. 심볼 블록이 출시 전에 제거되었으므로 내부의 어떤 것도 이름이 없다: 게임은
시퀀스, 뱅크, 스트림을 오직 숫자 인덱스로만 지정한다. 아카이브는 376개의 시퀀스 슬롯(342개 정의됨),
216개의 시퀀스 아카이브 항목, 943개의 뱅크, 14개의 웨이브 아카이브, 21개의 플레이어, 30개의 그룹,
2개의 스트림을 1,511개의 패킹된 파일에 걸쳐 선언한다. 이를 읽는 NitroSystem 사운드 라이브러리는
`autoload_2`에 있는 78개의 매칭된 함수이다.

등급 주석: 이 페이지의 **S**는 심볼 테이블, 매칭된 소스, 그리고 추출된 ROM 이미지에서 직접 읽어낸
바이트(경로와 필드를 항상 명시)를 포함한다.

## 무슨 일이 일어나는가

`sound_data.sdat`은 10,704,768바이트이며 `BUILDTIME` 옆의 파일 시스템 루트에 있다; ROM에서 가장 큰
단일 파일이다 [S: `extract/adm-kr/files/sound_data.sdat`, size;
`extract/adm-kr/files/`, root listing]. ARM9 이미지에 컴파일된 리터럴 경로 `/sound_data.sdat`으로
열린다 [S: `extract/adm-kr/arm9/arm9.bin`, path string literal].

컨테이너는 표준 NitroSDK 것이다: 매직 `SDAT`, 바이트 순서 표식 `0xFEFF`, 파일과 정확히 일치하는 파일
크기 필드, 헤더 크기 64, 그리고 네 개의 블록 디스크립터
[S: `extract/adm-kr/files/sound_data.sdat`, bytes 0..48]. **`SYMB` 블록은 없다** — 오프셋과 크기가 모두
0이다 — 따라서 출시된 아카이브는 어떤 항목에 대해서도 이름을 가지지 않는다
[S: same file, the first block descriptor at offset 16]. 나머지 셋은 `0x40`의 `INFO`(24,712바이트),
`0x60c8`의 `FAT `(24,188바이트), `0xbf44`의 `FILE`(10,655,804바이트)이다
[S: same file, block descriptors at offsets 24, 32 and 40].

`FAT `는 총 10,631,196바이트의 1,511개 패킹된 파일을 선언하며, 그중 가장 큰 것은 3,233,800바이트이다
[S: same file, `FAT ` entry count at +8 and the 16-byte entry array]. 다음으로 큰 범주가 시퀀스 데이터인
아카이브에서 3.2 MB의 단일 파일은 거의 확실히 두 스트림 중 하나이다 [H: see Hypotheses].

`INFO`는 여덟 개의 레코드 테이블을 담으며, 각각은 개수 뒤에 그 개수만큼의 오프셋이 오고, 레코드
본체는 오프셋 배열 뒤에 패킹되어 있다 [S: same file, the eight table offsets at `INFO`+8, and the
span arithmetic between consecutive tables]:

| 레코드 테이블 | 슬롯 | 정의됨 (0이 아닌 오프셋) | 스팬이 암시하는 본체 크기 |
|---|---|---|---|
| SEQ (시퀀스) | 376 | 342 | 각 12바이트 |
| SEQARC (시퀀스 아카이브) | 216 | 216 | 각 4바이트 |
| BANK (악기 뱅크) | 943 | 943 | 각 12바이트 |
| WAVEARC (웨이브 아카이브) | 14 | 14 | 각 4바이트 |
| PLAYER | 21 | 21 | 각 8바이트 |
| GROUP | 30 | 30 | 가변 |
| PLAYER2 | 1 | 1 | — |
| STRM (스트림) | 2 | 2 | — |

[S: `extract/adm-kr/files/sound_data.sdat`, counts read from each table's first word; body sizes
from `(span - 4 - 4*count) / defined`.]

정의되지 않은 34개의 시퀀스 슬롯은 id 공간의 구멍이다 — 게임이 이름 붙일 수는 있지만 데이터를 담지
않는 인덱스이다 [S: same file, 34 of the 376 SEQ offsets are zero]. 다른 모든 테이블은 완전히 빽빽하다.

### 이를 읽는 라이브러리

78개의 `NNS_Snd*` 함수가 바이트 단위로 매칭되어 있으며, 모두 `autoload_2`에 있다
[S: `src/matched/NNS_Snd*.c`, 78 files; `config/adm-kr/arm9/autoload_2/symbols.txt`]. 이는 공개된
절반이다: 심볼 테이블은 `autoload_2`에서 105개의 `NNS_Snd*`/`NNSi_Snd*`와 65개의 `SND_*`/`SNDi_*`
함수를 이름 붙이고, `src/matched/`는 각각 78개, 27개, 65개를 매칭한다
[S: `config/adm-kr/arm9/autoload_2/symbols.txt`, prefix counts; `src/matched/`, file-name
counts]. 사운드 스택 전체는 `main`이 아니라 `autoload_2`이다 — `../systems/audio.md` 참조. 이들은 네
그룹으로 나뉜다. 아카이브 접근자는 인덱스를 레코드나 파일로 바꾼다:
`NNS_SndArcGetSeqInfo`, `GetSeqArcInfo`, `GetBankInfo`, `GetWaveArcInfo`, `GetPlayerInfo`,
`GetGroupInfo`, `GetStrmInfo`, `GetStrmPlayerInfo`, 그리고 `NNS_SndArcGetFileID`,
`GetFileAddress`, `GetFileOffset`, `GetFileSize`, `NNS_SndArcReadFile`
[S: `src/matched/NNS_SndArcGetSeqInfo.c` and siblings]. 설정 쌍은 `NNS_SndArcInit`과
`NNS_SndArcInitOnMemory`이며, `NNS_SndArcSetup`과 `NNS_SndArcSetCurrent`/`GetCurrent`가 함께한다
[S: `src/matched/NNS_SndArcInit.c`, `NNS_SndArcSetup.c`, `NNS_SndArcSetCurrent.c`]. 재생은
`NNS_SndArcPlayerStartSeq`, `StartSeqArc`, `StartSeqArcEx`, `NNS_SndPlayerSetSeqNo`,
`SetSeqArcNo`, `StopSeq`, `StopSeqByPlayerNo`, `StopSeqBySeqArcIdx`, 그리고 트랙별 설정자
`SetTrackVolume`과 `SetTrackPitch`이다
[S: `src/matched/NNS_SndArcPlayerStartSeq.c` and siblings]. 스트리밍은 별도의 집합이다:
`NNS_SndStrmInit`, `Setup`, `Start`, `Stop`, `AllocChannel`, `FreeChannel`, `SetVolume`,
`SetChannelPan`, `HandleRelease`와, `NNS_SndArcStrmPrepare`, `StartPrepared`,
`GetTimeLength`, `GetCurrentPlayingPos`, `MoveVolume`
[S: `src/matched/NNS_SndStrmInit.c` and siblings]. 이 모든 것의 메모리는 전용 힙에서 나온다:
`NNS_SndHeapCreate`, `Alloc`, `Clear`, `Destroy`, `SaveState`, `LoadState`,
`GetCurrentLevel`, 그리고 `NNS_SndPlayerCreateHeap`
[S: `src/matched/NNS_SndHeapCreate.c` and siblings]. `NNS_SndArcLoadGroup`은 한 번의 호출로 그룹 전체를
끌어오는 일괄 로더이며 [S: `src/matched/NNS_SndArcLoadGroup.c`], 30개의 GROUP 레코드는 이를 위한
것이다.

캡처/이펙트 집합도 있다 — `NNS_SndCaptureCreateThread`, `StartEffect`,
`StartOutputEffect`, `ChangeOutputEffect`, `StopEffect`, `NNS_SndLockCapture`, `UnlockCapture` —
따라서 하드웨어 사운드 캡처 유닛이 연결되어 있다
[S: `src/matched/NNS_SndCaptureCreateThread.c` and siblings].

### UI에서 음악이 나타나는 곳

두 오버레이가 음악 화면을 소유한다. `ov144`는 `menu/music/`, 일곱 개의 파일을 가진다 — 수집한 곡을
재생하는 스테레오 화면이다 [S: `extract/adm-kr/arm9_overlays/ov144.bin`, seven path literals;
`extract/adm-kr/files/menu/music/`, 7 files]. `ov143`은 `menu/melody/`, 일곱 개의 파일을 가진다 —
마을 멜로디 편집기이다 [S: `extract/adm-kr/arm9_overlays/ov143.bin`, path literals;
`extract/adm-kr/files/menu/melody/`, 7 files]. 곡 이름은 메시지 뱅크 하나,
`script/KOR/string/st_music.bmg`, 386바이트에서 나온다
[S: `extract/adm-kr/files/script/KOR/string/`, file name and size].

### 포트에서의 사운드

포트에는 오디오가 없다. ROM의 사운드 스택은 인터프리터 경로에서 실행되기는 하며, 이를 실행한 것이
GX40에서 수정된 지오메트리 결함을 드러냈다: 사운드 스택이 활성화된 상태에서 지오메트리 엔진이
프레임당 약 1,400개의 버텍스를 받고도 아무것도 그리지 않아 위 화면이 검은 채로 남아 있었다
[E: `docs/log/cycle40-keyboard-gate-probe.md` GX40]. `func_0205401c`는 또한 재구성이 `gSoundFlag`라
부르는 전역 변수로부터 `0x04000304`의 `POWCNT1` 비트 15를 쓴다 [S: `src/matched/func_0205401c.cpp`].
**그 이름은 추론된 것이지 원래 것이 아니며, 그 비트는 사운드 비트가 아니다**: `POWCNT1` 비트 15는
어느 2D 엔진이 위 화면을 구동하는지 선택하며, `func_020540e4`가 이를 그 용도로 사용한다
[S: `src/matched/func_0205401c.cpp` header, "names are inferred, not original";
`src/matched/func_020540e4.c`; `../engine/graphics-pipeline.md`]. 그 전역 변수가 실제로 무엇을 담는지는
미결이다 [H: settled by watching that word and the top/bottom screen contents together across a
run].

## 어디에 있는가

| 항목 | 위치 | 등급/출처 |
|---|---|---|
| 아카이브 | `/sound_data.sdat`, 10,704,768 B | S: `extract/adm-kr/files/sound_data.sdat` |
| `INFO` 블록 | 오프셋 `0x40`, 24,712 B | S: same, block descriptor |
| `FAT ` 블록 | 오프셋 `0x60c8`, 24,188 B, 1,511개 항목 | S: same |
| `FILE` 블록 | 오프셋 `0xbf44`, 10,655,804 B | S: same |
| `SYMB` 블록 | 없음 (오프셋 0, 크기 0) | S: same |
| `NNS_SndArcInit`와 77개의 형제 함수 | `autoload_2` | S: `src/matched/NNS_Snd*.c` |
| 스테레오 화면 | `ov144`, `menu/music/` | S: `extract/adm-kr/arm9_overlays/ov144.bin` |
| 멜로디 편집기 | `ov143`, `menu/melody/` | S: `extract/adm-kr/arm9_overlays/ov143.bin` |
| 곡 이름 | `script/KOR/string/st_music.bmg` | S: `extract/adm-kr/files/script/KOR/string/` |

## 읽고 쓰는 데이터

| 필드 | 의미 | 쓰는 쪽 | 읽는 쪽 |
|---|---|---|---|
| SEQ 인덱스 (0-375) | 시퀀스 레코드를 고른다 | 게임의 음악 상태 | `NNS_SndArcGetSeqInfo` [S: `src/matched/NNS_SndArcGetSeqInfo.c`] |
| SEQARC 인덱스 (0-215) + 하위 인덱스 | 아카이브 안의 시퀀스 하나를 고른다 | 동일 | `NNS_SndArcPlayerStartSeqArc` [S: `src/matched/NNS_SndArcPlayerStartSeqArc.c`] |
| BANK 인덱스 (0-942) | 악기 뱅크를 고른다; 각 레코드는 최대 네 개의 웨이브 아카이브를 이름 붙인다 | 패커 | `NNS_SndArcGetBankInfo` [S: `src/matched/NNS_SndArcGetBankInfo.c`] |
| GROUP 인덱스 (0-29) | 일괄 로드 집합 | 패커 | `NNS_SndArcLoadGroup` [S: `src/matched/NNS_SndArcLoadGroup.c`] |
| STRM 인덱스 (0-1) | 스트리밍 트랙 | 게임 | `NNS_SndArcStrmPrepare` [S: `src/matched/NNS_SndArcStrmPrepare.c`] |
| FAT 항목 (16 B) | `FILE` 안의 파일 오프셋과 크기 | 패커 | `NNS_SndArcGetFileOffset`/`GetFileSize` [S: `src/matched/NNS_SndArcGetFileOffset.c`] |

## 확인 방법

정적이며, 실행이 필요 없다:

```bash
python - <<'PY'
import struct
d = open(r"extract/adm-kr/files/sound_data.sdat", 'rb').read()
print(d[:4], struct.unpack('<IHH', d[8:16]))
for i, nm in enumerate(('SYMB', 'INFO', 'FAT ', 'FILE')):
    o, s = struct.unpack('<II', d[16 + 8 * i:24 + 8 * i])
    print(nm, hex(o), s, d[o:o + 4] if s else b'-')
io = 0x40
offs = struct.unpack('<8I', d[io + 8:io + 40])
for nm, ro in zip(('SEQ SEQARC BANK WAVEARC PLAYER GROUP PLAYER2 STRM').split(), offs):
    c = struct.unpack('<I', d[io + ro:io + ro + 4])[0]
    e = struct.unpack('<%dI' % c, d[io + ro + 4:io + ro + 4 + 4 * c])
    print(nm, c, sum(1 for x in e if x))
PY
```

예상 출력: `b'SDAT' (10704768, 64, 3)`, `SYMB 0x0 0 -`, `INFO 0x40 24712 b'INFO'`,
`FAT  0x60c8 24188 b'FAT '`, `FILE 0xbf44 10655804 b'FILE'`, 그리고 위 표의 여덟 개 개수.

아직 실제 실행 확인은 없다: 포트는 오디오를 출력하지 않는다 [S: `docs/kb/port/input-save-audio.md`,
which the router lists as "why there is no sound yet"].

## 가설

- **943개의 악기 뱅크는 14개의 웨이브 아카이브에 비해 이례적으로 많은 수이다.** 개수와 12바이트
  레코드 크기는 모두 측정된 것이며 [S: the span arithmetic above], 12바이트는 정확히 NitroSDK 뱅크
  레코드(파일 id, 패딩, 네 개의 웨이브 아카이브 id)이다. 943개의 레코드를 모두 디코딩하여 서로 다른
  웨이브 아카이브 튜플이 몇 개 나타나는지 세어 결정한다 — 대부분의 뱅크가 같은 아카이브를 이름
  붙인다면, 이들은 서로 다른 샘플 세트가 아니라 곡별 악기 선택이다.
- **`FAT `의 3,233,800바이트 파일은 두 스트림 중 하나이다.** 아카이브의 30%를 차지하며 어떤
  시퀀스가 될 수 있는 것보다 훨씬 크다 [H: size]. 두 STRM 레코드의 파일 id를 해석하고 둘 중 하나가 그
  항목을 가리키는지 확인하여 결정한다.
- **정의되지 않은 34개의 SEQ 슬롯은 잘려 나갔거나 자리 표시용 음악이다.** 아카이브 전체에서 유일한
  구멍이다 [S: the SEQ offset scan]. 그 인덱스를 나열하고 어떤 GROUP 레코드가 이들을 참조하는지
  확인하여 결정한다.
- **386바이트의 `st_music.bmg`는 시퀀스 수보다 훨씬 적은 이름을 담는다**, 이는 배경 음악 전체가 아닌
  수집 가능한 곡만 이름 붙인다는 것을 시사한다 [H: size against 342 defined
  sequences]. 압축 해제 후 `INF1` 항목 수를 읽어 결정한다.
- **제거된 `SYMB` 블록은 런타임에 이름 기반 조회가 동작할 수 없음을 의미한다**, 따라서 모든 호출
  지점은 숫자 상수를 가져야 한다 [S: `SYMB` size 0]. 심볼 테이블에 `NNS_SndArc*ByName` 스타일의 함수가
  없음을 확인하여 결정한다 — 위에 나열된 78개의 매칭된 함수에는 그런 것이 하나도 없다.

## 관련 문서

- `archives.md` — 다른 포맷들과 나란히 놓인 `SDAT` 컨테이너.
- `rom-layout.md` — 트리에서 `sound_data.sdat`이 위치하는 곳.
- `../engine/file-system.md` — 아카이브가 열리는 방법.
- `docs/kb/port/input-save-audio.md` — 포트의 오디오 상태.
