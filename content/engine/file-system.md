# 파일 시스템
<!-- source: wiki/engine/file-system.md -->

**요약.** ACWW는 필요한 모든 것을 표준 NitroSDK 파일
시스템을 통해 경로 문자열로 읽는다. 경로는 파일 이름 테이블에 대조되어 파일 id로 해석되고, 파일 id는
파일 할당 테이블에서 조회되어 카트리지 상의 바이트 범위(span)가 되며, 그 범위는 카드에서 DMA로
읽힌다. 이 모든 것은 `rom`이라는 하나의 아카이브 앞에 놓인 명령 큐이며, 모든
명령은 같은 코드에 대해 동기적으로도 비동기적으로도 실행될 수 있다. 오버레이도
같은 장치를 거친다: 오버레이는 어디에 놓을지를 알려 주는 32바이트 헤더가 붙은 파일일 뿐이다.

## 무슨 일이 일어나는가

파일 시스템 전체는 `autoload_2`에, `0x021195e0`부터
`0x0211bcfc`까지 하나의 연속 구간에 있다 [S: `config/adm-kr/arm9/autoload_2/symbols.txt`, `FSi_TranslateCommand` addr
`0x021195e0` through `FSi_GetOverlayBinarySize` addr `0x0211bce0`]. 66개의 `FS_*` 및 `FSi_*`
함수가 NitroSDK 2.2a의 `fs_file.c`, `fs_archive.c`, `fs_command.c`,
`fs_overlay.c`에 대해 바이트 매칭되었다 [S: `src/matched/FS_*.c`, `src/matched/FSi_*.c`, file header comments]. 한
멤버는 ROM의 심볼 테이블에서 완전히 빠져 있다: `FSi_CloseFileCommand`, `0x021197c0`의
8바이트로, 본체는 `mov r0,#0; bx lr`이다 [S: `port/shim/fs/fscmd.c`, header].

부팅은 `FS_Init(dma)`를 정확히 한 번 호출한다; 이 함수는 `is_init` 플래그로 보호하고
`FSi_InitRom`에 위임한다 [S: `FS_Init`, `autoload_2`, `src/matched/FS_Init.c`]. `FSi_InitRom`은 카트리지용 잠금
id를 얻고, 두 오버레이 테이블 디스크립터를 0으로 만들고, `CARD_Init`을 호출하고,
단일 ROM 아카이브를 초기화하고, 세 글자 이름 `rom`으로 등록하고,
`WRITEFILE`, `ACTIVATE`, `IDLE` 명령에 대해 `FSi_RomArchiveProc`을 설치하고, ROM 헤더 이미지에서
가져온 FAT와 FNT 영역과 `FSi_ReadRomCallback` 읽기 콜백으로 아카이브를
로드한다 [S: `FSi_InitRom`, `autoload_2`, `src/matched/FSi_InitRom.c`]. FAT,
FNT, 오버레이 테이블 영역은 펌웨어가 `0x027FFE00`에 남겨 두는 헤더 이미지의
고정 오프셋에서 온다: FNT는 +0x40, FAT는 +0x48, ARM9 오버레이 테이블은 +0x50, ARM7 오버레이 테이블은
+0x58이다 [S: `src/matched/FSi_InitRom.c`, `src/matched/FS_LoadOverlayInfo.c`, the inline region
accessors].

이름으로 파일을 여는 것은 두 단계이다. `FS_OpenFile`은 `FS_ConvertPathToFileID`를 호출한 다음
`FS_OpenFileFast`를 호출한다 [S: `FS_OpenFile`, `autoload_2`, `src/matched/FS_OpenFile.c`].
`FS_ConvertPathToFileID`는 스택 로컬 `FSFile`을 설정하고 경로를 `FSi_FindPath`에 넘기며
[S: `FS_ConvertPathToFileID`, `autoload_2`, `src/matched/FS_ConvertPathToFileID.c`], 이 함수는
선행 `/` 또는 최대 세 글자의 `name:` 아카이브 접두사를 파싱한 다음
`FINDPATH` 명령을 발행한다 [S: `FSi_FindPath`, `autoload_2`, `src/matched/FSi_FindPath.c`]. 명령
핸들러는 파일 이름 테이블을 한 번에 한 구성 요소씩 순회하며, `.`과 `..`을 처리하고,
127자보다 긴 이름을 거부하고, `FSi_StrNICmp`로 대소문자 구분 없이 비교한다
[S: `FSi_FindPathCommand`, `autoload_2`, `src/matched/FSi_FindPathCommand.c`;
`src/matched/FSi_StrNICmp.c`]. FNT의 디렉터리 엔트리는 최상위 비트가 디렉터리를
표시하는 길이 바이트, 그 뒤의 이름, 그리고 디렉터리의 경우 `0xFFF`로 마스킹된 16비트 id로 되어 있다;
파일의 id는 후위 증가되는 누적 인덱스이다 [S: `FSi_ReadDirCommand`, `autoload_2`,
`src/matched/FSi_ReadDirCommand.c`].

`FS_OpenFileFast`는 그 다음 id를 범위로 바꾼다: 인덱스를 FAT
크기에 대해 경계 검사하고, 8바이트 FAT 엔트리를 읽고, 그 `top`과 `bottom`을 직접 열기 인수
블록에 복사한 뒤, `OPENFILEDIRECT`로 명령 번역기에 다시 진입한다
[S: `FSi_OpenFileFastCommand`, `autoload_2`, `src/matched/FSi_OpenFileFastCommand.c`]. 이 명령은
단순히 `top`, `bottom`, 초기 위치(= `top`), 파일 id를 `FSFile`에 저장한다
[S: `FSi_OpenFileDirectCommand`, `autoload_2`, `src/matched/FSi_OpenFileDirectCommand.c`].

읽기는 요청 길이를 남은 범위에 맞춰 클램프하고, 요청을 기록하고, 비동기 읽기가 아니면
파일을 동기로 표시한 뒤 `READFILE`을 발행한다
[S: `FSi_ReadFileCore`, `autoload_2`, `src/matched/FSi_ReadFileCore.c`]. `FS_ReadFile`은
그것으로의 한 줄짜리 꼬리 호출이다 [S: `FS_ReadFile`, `autoload_2`, `src/matched/FS_ReadFile.c`].
`FS_SeekFile`은 명령을 전혀 발행하지 않는다 — `FSFile` 안의 `pos`를 조정하고 범위 안으로
클램프한다 [S: `FS_SeekFile`, `autoload_2`, `src/matched/FS_SeekFile.c`].

모든 명령은 아카이브당 하나의 큐를 거친다. `FSi_SendCommand`는 파일을 사용 중으로 표시하고,
아카이브의 리스트에 추가하고, — 아카이브가 유휴 상태였다면 — 실행 전에 실행 중 플래그를 올리고
아카이브의 proc을 통해 `ACTIVATE`를 발행한다
[S: `FSi_SendCommand`, `autoload_2`, `src/matched/FSi_SendCommand.c`]. `FSi_TranslateCommand`는
명령을 아카이브 자체의 proc에 먼저 제안하고 기본 핸들러 테이블로 폴백한다
[S: `FSi_TranslateCommand`, `autoload_2`, `src/matched/FSi_TranslateCommand.c`].
`FSi_NextCommand`는 취소된 파일을 비우고, 동기 대기자를 깨우고, 큐가 비면
임시 `FSFile`을 통해 `IDLE`을 발행한다 [S: `FSi_NextCommand`, `autoload_2`,
`src/matched/FSi_NextCommand.c`]. ROM 아카이브에서 `ACTIVATE`와 `IDLE`은 카트리지
잠금과 해제이고 [S: `FSi_RomArchiveProc`, `autoload_2`, `src/matched/FSi_RomArchiveProc.c`],
실제 전송은 `FSi_OnRomReadDone`을 완료 콜백으로 하는 `CARD_ReadRomAsync`이다
[S: `FSi_ReadRomCallback`, `autoload_2`, `src/matched/FSi_ReadRomCallback.c`].

ROM 아카이브에 쓰기는 거부된다: `FSi_RomArchiveProc`은 `WRITEFILE`에
`FS_RESULT_UNSUPPORTED`로 응답한다 [S: `src/matched/FSi_RomArchiveProc.c`]. 게임의 세이브 데이터는
파일 시스템을 전혀 거치지 않는다 — CARD 백업 요청을 통해 백업 플래시로 간다
(가설 참고).

### 오버레이

`FS_LoadOverlay`는 세 호출이다: 오버레이의 정보 헤더 읽기, 이미지 읽기, 시작
[S: `FS_LoadOverlay`, `autoload_2`, `src/matched/FS_LoadOverlay.c`]. 정보 헤더는 32
바이트이다: id, RAM 주소, RAM 크기, BSS 크기, 정적 초기화자 시작과 끝, 파일 id, 그리고
패킹된 24비트 압축 크기와 8비트 플래그 [S: `src/matched/FS_LoadOverlayInfo.c`,
`FSOverlayInfoHeader` as the matched sources declare it]. `FS_ClearOverlayImage`는 영역 전체에 걸쳐
명령어 캐시와 데이터 캐시를 무효화하고 BSS 꼬리를 0으로 만든다
[S: `FS_ClearOverlayImage`, `autoload_2`, `src/matched/FS_ClearOverlayImage.c`].
`FS_StartOverlay`는 선택적으로 HMAC-SHA1 다이제스트로 이미지를 인증하고, 압축 플래그가 설정되어 있으면
뒤에서부터 압축을 풀고, 데이터 캐시를 플러시한 다음,
`sinit_init`..`sinit_init_end` 테이블을 순회하며 null이 아닌 모든 생성자를 호출한다
[S: `FS_StartOverlay`, `autoload_2`, `src/matched/FS_StartOverlay.c`; `FSi_CompareDigest`,
`src/matched/FSi_CompareDigest.c`]. 오버레이를 해체하는 것은 그 거울상이다: `FS_EndOverlay`는
`__global_destructor_chain`을 순회하며, 오브젝트나 소멸자가 오버레이의 주소 범위 안에 있는
모든 노드를 언링크하고, 수집된 소멸자들을 실행한다 [S: `FS_EndOverlay`, `autoload_2`,
`src/matched/FS_EndOverlay.c`].

이 ROM의 148개 오버레이 전부가 압축 저장되어 있고 어느 것도 서명되어 있지 않으므로, 압축 해제 분기는
항상 실행되고 다이제스트 분기는 절대 실행되지 않는다 [S: `extract/adm-kr/arm9_overlays/overlays.yaml`,
`compressed: true` / `signed: false` on all 148 entries]. 역방향 압축 해제기는
`MIi_UncompressBackward`로, ROM이 이름 짓지 않은 어셈블리 본체이다; 두 개의 독립적인 매칭된 호출자로부터
`func_02000934`로 식별되었다 [S: `port/shim/fs/arena_uncompback.c`,
header, citing `tools/.../recovered_callees.txt`].

### 파일 시스템으로 마운트되는 NARC 아카이브

같은 `FSArchive` 오브젝트가 메모리 내 아카이브에도 쓰인다. `NNS_FndMountArchive`는 `NARC`
이미지를 검증하고, `FATB`, `FNTB`, `FIMG` 블록을 찾고, `FIMG` 헤더 다음 첫 바이트를 기준(base)으로 하며
FAT와 FNT 위치가 그 기준에 상대적으로 표현되는 `FSArchive`로
마운트한다 [S: `NNS_FndMountArchive`, `autoload_2` `0x0210288c`, `src/matched/NNS_FndMountArchive.c`].
null 읽기 및 쓰기 콜백을 넘기므로, `FS_LoadArchive`가 메모리 콜백으로 대체하고
아카이브는 RAM에서 직접 제공된다 [S: `FS_LoadArchive`, `autoload_2`,
`src/matched/FS_LoadArchive.c`; `src/matched/FSi_ReadMemCallback.c`]. 검증은 매직
`NARC`, 바이트 순서 표식 `0xFFFE`, 버전 `0x0100`이다
[S: `IsValidArchiveBinary`, `autoload_2` `0x021029e8`, `src/matched/IsValidArchiveBinary.c`].
마운트되고 나면 멤버는 일반 `FS_OpenFile`을 통해 `archive:path`로 가져온다
[S: `NNS_FndGetArchiveFileByName`, `autoload_2` `0x02102808`,
`src/matched/NNS_FndGetArchiveFileByName.c`]. 게임은 마을 에이커에 대해 이렇게 한다:
`/bg/aN/NNNN.arc`를 아카이브 이름 `BG`로 마운트하고 여섯 멤버 — `BG:a/bmd/bmd0`과 그
동반자 `bcl0`, `bsd0`, `bca0`, `bma0`, `bta0` — 를 끌어온다 [S: `port/shim/fs/arcmember.c`, header].

## 어디에 있는가

| 함수 또는 심볼 | 모듈 | 역할 | 등급/출처 |
|---|---|---|---|
| `FS_Init` `0x0211b35c` | `autoload_2` | 1회성 초기화 가드 | S: `src/matched/FS_Init.c` |
| `FSi_InitRom` `0x0211b398` | `autoload_2` | 헤더 이미지로부터 `rom` 아카이브 등록 | S: `src/matched/FSi_InitRom.c` |
| `FS_OpenFile` `0x0211afdc` | `autoload_2` | 경로 → 열린 파일 | S: `src/matched/FS_OpenFile.c` |
| `FS_ConvertPathToFileID` `0x0211b100` | `autoload_2` | 경로 → 파일 id | S: `src/matched/FS_ConvertPathToFileID.c` |
| `FSi_FindPath` `0x0211b1cc` | `autoload_2` | `/`와 `name:` 접두사 파싱 | S: `src/matched/FSi_FindPath.c` |
| `FSi_FindPathCommand` `0x02119c2c` | `autoload_2` | FNT 순회 | S: `src/matched/FSi_FindPathCommand.c` |
| `FSi_ReadDirCommand` `0x02119e48` | `autoload_2` | FNT 엔트리 하나 | S: `src/matched/FSi_ReadDirCommand.c` |
| `FSi_SeekDirCommand` `0x02119f58` | `autoload_2` | 디렉터리에 위치시킴 | S: `src/matched/FSi_SeekDirCommand.c` |
| `FS_OpenFileFast` `0x0211b02c` | `autoload_2` | 파일 id → 열린 파일 | S: `src/matched/FS_OpenFileFast.c` |
| `FSi_OpenFileFastCommand` `0x021197f0` | `autoload_2` | FAT 조회 | S: `src/matched/FSi_OpenFileFastCommand.c` |
| `FS_ReadFile` `0x0211ae68` / `FSi_ReadFileCore` `0x0211b144` | `autoload_2` | 클램프된 읽기 | S: `src/matched/FS_ReadFile.c`, `FSi_ReadFileCore.c` |
| `FS_SeekFile` `0x0211adfc` | `autoload_2` | 로컬 탐색, 명령 없음 | S: `src/matched/FS_SeekFile.c` |
| `FS_CloseFile` `0x0211af94` | `autoload_2` | 닫고 file/dir 비트를 클리어 | S: `src/matched/FS_CloseFile.c` |
| `FSi_SendCommand` `0x0211a82c` | `autoload_2` | 큐 삽입 + 활성화 | S: `src/matched/FSi_SendCommand.c` |
| `FSi_TranslateCommand` `0x021195e0` | `autoload_2` | proc 우선 디스패치 | S: `src/matched/FSi_TranslateCommand.c` |
| `FSi_NextCommand` `0x0211aad4` | `autoload_2` | 큐 펌프, 유휴 | S: `src/matched/FSi_NextCommand.c` |
| `FSi_RomArchiveProc` `0x0211b548` | `autoload_2` | 카트리지 잠금/해제, 쓰기 거부 | S: `src/matched/FSi_RomArchiveProc.c` |
| `FSi_ReadRomCallback` `0x0211b5e0` | `autoload_2` | `CARD_ReadRomAsync` | S: `src/matched/FSi_ReadRomCallback.c` |
| `FS_LoadArchive` `0x0211a5d4` / `FS_LoadArchiveTables` `0x0211a3e0` | `autoload_2` | 아카이브 설정, 테이블 캐싱 | S: `src/matched/FS_LoadArchive.c`, `FS_LoadArchiveTables.c` |
| `FS_LoadOverlay` `0x0211b690` | `autoload_2` | 정보 → 이미지 → 시작 | S: `src/matched/FS_LoadOverlay.c` |
| `FS_StartOverlay` `0x0211b80c` | `autoload_2` | 압축 해제 + 생성자 실행 | S: `src/matched/FS_StartOverlay.c` |
| `FS_EndOverlay` `0x0211b708` | `autoload_2` | 소멸자 스윕 | S: `src/matched/FS_EndOverlay.c` |
| `NNS_FndMountArchive` `0x0210288c` | `autoload_2` | NARC → `FSArchive` | S: `src/matched/NNS_FndMountArchive.c` |
| `FSi_CloseFileCommand` `0x021197c0` | `autoload_2` | ROM에 이름 없음; 성공 반환 | S: `port/shim/fs/fscmd.c` |

## 읽고 쓰는 데이터

| 주소 또는 필드 | 의미 | 쓰는 쪽 | 읽는 쪽 |
|---|---|---|---|
| `0x027FFE00` +0x40 / +0x48 | FNT와 FAT 영역 | 펌웨어의 헤더 사본 | `FSi_InitRom` [S: `src/matched/FSi_InitRom.c`] |
| `0x027FFE00` +0x50 / +0x58 | ARM9 / ARM7 오버레이 테이블 | 펌웨어의 헤더 사본 | `FS_LoadOverlayInfo` [S: `src/matched/FS_LoadOverlayInfo.c`] |
| `0x027FFC40` | 멀티부트 부팅 버퍼; 0이 아니면 "자식"을 뜻함 | 펌웨어 | `FSi_InitRom`의 멀티부트 분기 [S: `src/matched/FSi_InitRom.c`] |
| `FSArchiveFAT {u32 top; u32 bottom;}` | 파일당 8바이트, 바이트 범위 | 패커 | `FSi_OpenFileFastCommand` [S: `src/matched/FSi_OpenFileFastCommand.c`] |
| `FSArchiveFNT {u32 start; u16 index; u16 parent;}` | 디렉터리당 8바이트 | 패커 | `FSi_SeekDirCommand` [S: `src/matched/FSi_SeekDirCommand.c`] |
| `FSFile.stat` 비트 `0x01/0x02/0x04/0x08/0x10/0x20/0x40` | busy, cancel, sync, async, is-file, is-dir, operating | `FSi_SendCommand`, `FS_OpenFileFast` | `FSi_ExecuteAsyncCommand`, `FS_CloseFile` [S: `src/matched/FSi_SendCommand.c`] |
| `FSArchive.flag` 비트 `0x01`..`0x200` | registered, loaded, table-loaded, suspend, running, cancelling, suspending, unloading, is-async, is-sync | `FS_RegisterArchiveName`, `FS_LoadArchive`, `FSi_TranslateCommand` | 큐 펌프 [S: `src/matched/FSi_TranslateCommand.c`] |
| `FSOverlayInfoHeader` (32 B) | id, RAM 주소, RAM 크기, BSS 크기, sinit 범위, 파일 id, compressed:24 + flag:8 | 패커 | `FS_LoadOverlayInfo`, `FS_StartOverlay` [S: `src/matched/FS_LoadOverlayInfo.c`] |

이 구조체들을 읽는 사람이라면 누구에게나 중요한 세부 사항: 이 ROM은
`SDK_THREAD_INFINITY`로 빌드되었으므로, `OSThreadQueue`는 패킹된 4바이트 필드가 아니라 실제 8바이트
`{head, tail}` 쌍이다. 따라서 `FSFile`을 내장하는 모든 구조체는 기본 SDK 헤더가
암시하는 것보다 4바이트 더 크다 [S: `docs/kb/modules/sdk-nns.md`, the `SDK_THREAD_INFINITY`
section]. 이 계열의 오버레이 쪽 절반은 추가로 `SDK_TS`가 필요하며, 이것이
`fs_overlay.c`가 컴파일되는지 여부를 결정한다 [S: `docs/kb/modules/sdk-nns.md`, the `SDK_TS` section].

## 확인 방법

포트는 API가 아니라 카트리지를 대체한다: `port/shim/fs/romfs.c`는 추출된 파일
시스템을 평탄한 가상 ROM 주소 공간으로 제시하고 `port/shim/fs/card.c`는 그로부터 `CARDi_ReadRom`에
응답하므로, 위의 모든 `FS_*` 함수는 ROM 자체의 코드가 수정 없이 실행되는 것이다
[S: `port/shim/fs/card.c`, header; `port/shim/fs/romfs.c`, header]. 인덱스 블롭은
`port/tools/fsimage.py`가 매직 `ACWWFSI1`로 작성하며, ROM 헤더, 오버레이 테이블, FNT, FAT는
가상 ROM의 앞부분에 원본 그대로 저장된다 [S: `port/shim/fs/romfs.c`, `struct Index`].

파일 시스템이 동작하는 것을 보려면, 마을에 쓰인 인터프리터 레시피를 실행하고 오버레이
집합을 관찰한다:

```
ACWW_INTERP=1  ACWW_KEYS_AT/_FOR/_EVERY = the custom START9000 keys
ACWW_TOUCH_ENABLE=1 ACWW_TOUCH_X=221 ACWW_TOUCH_Y=181 ACWW_TOUCH_AT=6900 ACWW_TOUCH_EVERY=60
ACWW_STOP_FRAME=48000
python port/tools/run.py --frontier start
```

예상: 프레임 37,500에 오버레이 5, 36, 54, 120, 117이 로드된 채 마을이 화면에 있다
[E: `scratchpad/cycle40/runs/tap-D56` frame 37500, per `docs/log/cycle40-keyboard-gate-probe.md`
TOWN40]. 그것이 파일 시스템이 제 일을 온전히 해내는 모습이다 — 경로가 해석되고, 오버레이가 읽히고,
재배치되고, 생성되고, 그려진다.

## 가설

- 포트의 오버레이 재배치는 ROM 동작이 아니라 호스트 쪽 우회책이다: 오버레이들이 겹치기 때문에
  `relocs.py`는 오버레이 포인터를 정적으로 다시 쓸 수 없으므로, 오버레이별 테이블이
  `FS_StartOverlay` 안에서 적용되며, 인터프리터 경로는 의도적으로 재배치
  패스를 전혀 실행하지 않는다 [S: `port/shim/fs/ovlreloc.c`, header]. 이제 인터프리터 경로가
  유일하게 올바른 경로인지는 같은 레시피를 두 경로에서 실행하고
  로드된 오버레이 추적을 diff하면 해결될 것이다.
- `FS_EndOverlay`의 ROM 구현은 네이티브 포트를 멈추게 하므로(오버레이 65가 로드되고, 어떤 프레임도
  완료되지 않음) 포트는 대신 한정된 스윕을 실행한다 [S: `port/shim/fs/endoverlay.c`, header].
  그 멈춤이 포트의 소멸자 체인의 결함인지 포트의 힙 위에서 실행되는 ROM 자체
  해체의 결함인지는 알려져 있지 않다. `ACWW_INTERP=1`로 ROM의 `FS_EndOverlay`를 실행하고
  스윕이 어디서 멈추는지 기록하여 해결한다.
- 세이브 데이터가 파일 시스템을 완전히 우회한다는 주장은 여기서 CARD
  백업 요청 번호(READ_BACKUP 6, WRITE_BACKUP 7, VERIFY_BACKUP 9)와 `0x1202`에서 식별된 256 KB 플래시
  장치를 근거로 한 것이다 [S: `port/shim/fs/cardreq.c`, header]. 이는
  `../systems/save-data.md`에 정리되어 있으며, 세이브 중에 `FS_*` 명령이 하나라도
  발행되는지 관찰하여 거기서 확인해야 한다.
- `BUILDTIME`과 `path_order.txt`의 순서는 트리가 특정 순서로 패킹되었음을 시사한다.
  FAT 범위를 `path_order.txt`와 비교하여 해결한다.

## 관련 문서

- `../data/rom-layout.md` — 파일 id가 인덱스하는 모듈과 디렉터리 레이아웃.
- `../data/archives.md` — 각 파일 안에 들어 있는 컨테이너 형식.
- `overlays.md` — 148개 오버레이 각각의 용도.
- `../data/music.md` — 사운드 라이브러리가 아카이브로 읽는 유일한 파일 `sound_data.sdat`.
