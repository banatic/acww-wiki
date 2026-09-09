# 감사(audit): 공개 사양 대비 데이터 포맷
<!-- source: wiki/audits/data-formats.md -->

verified-at: 470df4ac 2026-09-09

**목적.** 위키의 여덟 페이지는 닌텐도, NitroSDK, 그리고 거대한 리버스 엔지니어링 커뮤니티가
이미 문서화한 컨테이너 포맷을 설명한다. 이 페이지는 그 페이지들의 구조적 주장 하나하나를
공개된 기록과 대조해 확인하고, 공개 기록이 *추가로* 알려주는 것을 기록하며, 그 차이를 포트와
위키를 위한 작업으로 바꾼다.

**등급 P (public, 공개).** 공개 문서 — GBATEK, 포맷 위키, 도구의 소스 — 는 등급 **P**이며
항상 URL과 절(section)을 함께 표기한다. **P는 결코 S, E, O를 대체하지 않는다.** 공개 사양은
포맷이 *일반적으로* 무엇인지를 말할 뿐이고, 이 ROM이 무엇을 하는지는 오직 `src/matched/`,
실행(run), 또는 오라클만이 말해 준다. P 출처와 S/E 출처가 어긋나는 곳에서는 S/E 출처가 이기며,
그 불일치 자체가 내용이 된다(STYLE 규칙 7). P가 측정과 일치하는 곳에서는 P 출처가 보강 근거가
되고, 위키가 크기만 측정해 두었던 필드에 *이름*을 붙일 수 있게 해 준다.

**방법.** 공개 출처를 먼저 읽은 뒤 `extract/adm-kr/files/` 안의 바이트와 다시 대조했다.
헤더와 구조 필드만 읽었으며, 에셋 내용은 이 페이지나 위키에 전혀 복사하지 않았다. 게임을
실행하지는 않았다. 검사 과정에서 새 측정값이 나온 곳은 `data/rom-layout.md`가 쓰는 것과 같은
의미로 파일과 필드를 적어 **[S: image]**로 표시했다.

## 참조한 출처

| 출처 | URL | 다루는 내용 |
|---|---|---|
| GBATEK, DS Cartridge Header | `https://problemkaputt.de/gbatek-ds-cartridge-header.htm` | 헤더 필드, FNT/FAT/OVT 오프셋, CRC |
| GBATEK, NitroROM and NitroARC File Systems | `https://problemkaputt.de/gbatek-ds-cartridge-nitrorom-and-nitroarc-file-systems.htm` | FNT 서브테이블, FAT 엔트리, 오버레이 테이블 |
| GBATEK, BIOS Decompression Functions | `https://problemkaputt.de/gbatek-bios-decompression-functions.htm` | SWI 0x11/0x12, 4바이트 압축 헤더, LZ77 토큰 인코딩 |
| GBATEK, DS Sound Files — SDAT | `http://problemkaputt.de/gbatek-ds-sound-files-sdat-sound-data-archive.htm` | SDAT 헤더, INFO 테이블, FAT/FILE |
| GBATEK, Nitro Font Resource Format | `https://problemkaputt.de/gbatek-ds-cartridge-nitro-font-resource-format.htm` | NFTR/`RTFN`, FINF/CGLP/CWDH/CMAP |
| Feshrine, Nitro Composer (`*.sdat`) Specification | `https://www.feshrine.net/hacking/doc/nds-sdat.php` | SDAT 레코드 크기, SSEQ/SBNK/SWAR |
| ndspy (`soundArchive.py`, `narc.py`, `_common.py`, `bmg`) | `https://github.com/RoadrunnerWMC/ndspy` | SDAT 레코드 구조체, NARC, 공용 Nitro 헤더, BMG 모델 |
| Pikmin TKB, BMG file | `https://pikmintkb.com/wiki/BMG_file` | BMG 헤더 오프셋, 인코딩 표, INF1/DAT1/MID1, 0x1A 이스케이프 |
| Custom Mario Kart wiki, BMG / 0x1A Escape Sequences | `https://wiki.tockdom.com/wiki/BMG_(File_Format)` (현재 `mkwiiki.org`) | 이스케이프 시퀀스 규칙 |
| scurest, `nsbmd_docs.txt` 및 apicula FILETYPES | `https://github.com/scurest/nsbmd_docs` | BMD0/BTX0/BCA0/BTP0/BTA0 컨테이너와 서브파일 |
| NSMBHD, Particle (`.spa`) documentation | `https://nsmbhd.net/thread/5255-tutorial-particle-spa-editing-tutorial-and-documentation/` | SPA 헤더, 뒤집힌 매직, 버전 스탬프 |
| NintyFont NFTR notes | `https://deepwiki.com/hadashisora/NintyFont/5.2-nftr-format-(nintendo-ds)` | CMAP 타입, CWDH 체이닝, 사설 폰트 변형 |

---

## 핵심 결론: `0xf7` "압축 타입"은 압축 타입이 아니다

`data/archives.md`와 `engine/text-and-messages.md`는 같은 미해결 질문을 안고 있다 — ROM 안의
모든 `.bmg`가 `LZ77` 다음에 SDK의 `0x10` 대신 바이트 `0xf7`로 시작하며, 이것이 "다른 알고리즘인지
난독화인지는 알 수 없다"는 것이다. 둘 다 아니다. **`0xf7`은 청크 단위 컨테이너를 표시하며, 각
청크는 평범한 NitroSDK 타입 `0x10` LZ77 스트림이다.** 압축된 메시지 파일 1,790개 전부가 포트에
이미 있는 압축 해제기로 풀린다.

이미지에서 읽어 내고, 모든 파일을 디코딩해 확인한 레이아웃은 다음과 같다:

```
+0x00  4   'LZ77'
+0x04  1   0xf7                      container tag
+0x05  3   u24 total decompressed size
+0x08  2*N u16 chunk END offsets, cumulative, relative to the end of this table
           N = ceil(total / 4096); the last entry equals filesize - (8 + 2*N)
then, for each chunk:
       4   an ordinary NDS compression header: u8 type + u24 decompressed size
       ..  the chunk payload
```

마지막 청크를 제외한 모든 청크는 정확히 4,096바이트로 풀린다. 1,787개 파일에서는 모든 청크의
타입이 `0x10`(LZ77)이며, 세 파일 — `message/fu/ev/nbirth_.bmg`, `message/ha/tsu/friend_.bmg`,
`message/ko/3p/ge_.bmg` — 은 타입 `0x00`(저장) 청크를 하나씩 가지는데, 이는 표준적인 "압축이 안
되니 그대로 저장" 경우다 [S: image, those three files, chunk headers].

검증은 `.bmg` 파일 1,791개 전부를 대상으로 수행했다: 각 파일에서 테이블의 마지막 엔트리가
`filesize - headersize`와 같고, 모든 청크가 정확히 선언된 크기로 풀리며, 이어 붙인 결과가
컨테이너가 선언한 총 크기와 같고, 결과가 `MESGbmg1`로 시작하며, BMG 자체의 +8 크기 필드가 압축
해제된 길이와 같다. **1,791개 중 1,791개 통과**
[S: image, `extract/adm-kr/files/script/KOR/**/*.bmg`, whole-corpus decode]. 청크 수는 1,659개
파일이 단일 청크, 132개가 둘 이상이며, 최대는 16개다 [S: same decode]. 토큰 인코딩은 GBATEK의
설명과 정확히 같다: 플래그 바이트 하나가 여덟 단위를 다스리고, MSB부터, `len = (b0>>4)+3`,
`disp = ((b0&0xF)<<8|b1)+1`
[P: GBATEK, BIOS Decompression Functions, LZ77 section].

두 가지 결과가 곧바로 따라 나오며, 둘 다 메모가 아니라 작업 항목이다:

- ROM의 범용 파일 로더는 `.bmg`를 읽는 주체일 **수 없다**. `func_020648a0`, `func_020649ac`,
  `func_02064b2c`는 모두 `LZ77` 매직을 검사한 뒤 타입 분기 없이 `header+4`를 곧바로
  `MI_UncompressLZ8`에 넘긴다
  [S: `src/matched/func_020648a0.c`, `src/matched/func_020649ac.c`,
  `port/shim/fs/loadfile.c` (the shadowed `func_02064b2c`)]. `0xf7` 파일에서 이렇게 하면 u16
  청크 테이블을 플래그 바이트와 토큰으로 읽어 쓰레기를 만들어 낸다. `src/matched/`에서
  `MI_UncompressLZ8`을 호출하는 함수는 세 개뿐이고, 그중 어느 것도 청크 테이블을 걷지 않는다
  [S: `src/matched/`, call-site scan]. 따라서 메시지 시스템은 자체 리더를 가지며, 그것은
  `engine/text-and-messages.md`가 이미 나열한 매칭되지 않은 `func_02xxxxxx` 본체 중 하나다.
- 4,096바이트 청크 크기와 누적 끝 오프셋 테이블의 조합은 **임의 접근(random-access)** 설계다:
  `INF1` 오프셋을 4,096으로 나누면 압축 해제해야 할 단 하나의 청크가 정해진다. 이것은 난독화보다
  훨씬 나은 포맷 설명이며, 리더가 파일 전체가 아니라 메시지당 청크 하나를 푼다는 예측을 낳는다
  [H: structure].

---

## 1. `engine/file-system.md`

| 위키 주장 | 공개 출처 | 판정 | 조치 |
|---|---|---|---|
| FNT는 헤더 +0x40, FAT는 +0x48, ARM9 OVT는 +0x50, ARM7 OVT는 +0x58 | P: GBATEK, DS Cartridge Header — 필드 표는 FNT 오프셋 0x40 / 크기 0x44, FAT 오프셋 0x48 / 크기 0x4C, ARM9 오버레이 0x50/0x54, ARM7 오버레이 0x58/0x5C를 제시한다 | **확인됨**, 그리고 +0x44/+0x4C/+0x54/+0x5C의 크기 필드에도 이름이 붙어 있다 | 페이지의 표에 크기 필드를 추가한다; 이것이 `FS_LoadArchive`가 경계 검사를 하는 기준이다 |
| 펌웨어가 `0x027FFE00`에 남겨 두는 헤더 이미지 | P: GBATEK, 같은 페이지 — 카트리지 헤더는 전원 인가 시 `27FFE00h`로 복사된다 | **확인됨** | 없음 |
| 헤더 이미지는 0x160바이트 | P: GBATEK는 ROM Header Size를 *필드*로서 0x4000으로 제시한다; RAM 복사본은 처음 0x160바이트다 | **확인됨, 다만 두 숫자는 서로 다른 것이다** | 0x4000이 무엇인지 명시한다: 복사본이 아니라 헤더 크기 *필드*다 |
| FNT 엔트리: 길이 바이트, 최상위 비트 = 디렉터리, 디렉터리 id는 `0xFFF`로 마스킹 | P: GBATEK, NitroROM File Systems — FNT 서브테이블은 파일과 하위 디렉터리의 ASCII 이름을 정확히 그 타입 비트와 함께 담는다 | **확인됨** | 매칭된 소스 옆에 GBATEK를 인용한다 |
| `FSArchiveFAT {u32 top; u32 bottom;}`, 파일당 8바이트 | P: GBATEK — FAT는 시작/끝 ROM 주소를 파일당 8바이트로 담으며, 최대 61,440개 파일 | **확인됨** | 61,440 상한을 적어 둔다; 이 ROM의 9,508개 파일은 그에 한참 못 미친다 |
| 오버레이 정보 헤더는 32바이트: id, RAM 주소, RAM 크기, BSS 크기, sinit 범위, 파일 id, compressed:24 + flag:8 | P: GBATEK, NitroROM — OVT는 오버레이 ID를 파일 ID에 배정하고 로드 주소를 담는다 | **개요는 확인됨**; GBATEK는 `compressed:24 + flag:8` 패킹을 명명하지 않으며, SDK 헤더가 명명한다 | S 출처를 1차로 유지한다; P는 보강 근거일 뿐이다 |
| NARC 검증은 매직 `NARC`, BOM `0xFFFE`, 버전 `0x0100` | P: ndspy `_common.py`는 BOM 필드를 리틀엔디언 u16으로 읽어 `0xFEFF`를 리틀엔디언, `0xFFFE`를 바이트 스왑 변형으로 취급한다 | **확인됨, 그리고 설명됨**: `str/bsize.arc`는 `FE FF` = 0xFFFE를 저장하므로 ACWW의 NARC는 스왑된 BOM 종류이고, 반면 `BMD0`/`SDAT` 파일은 `FF FE` = 0xFEFF를 저장한다 [S: image, `str/bsize.arc` +4, `anm/0/0.nsbca` (decompressed) +4, `sound_data.sdat` +4] | `archives.md`에 한 문장을 추가한다: 이 ROM의 두 가지 BOM 표기는 불일치가 아니라 문서화된 두 종류이며, 리더는 둘 다 받아들여야 한다 |
| NARC 블록은 `BTAF`, `BTNF`, `GMIF` | P: ndspy `narc.py`, projectpokemon rawdb `nds/narc.py` | **확인됨** | 없음 |

**모순되지 않으며, 추가할 가치가 있는 것:** GBATEK는 +0x15E에 있는 `[0x000..0x15D]` 구간의
헤더 CRC-16과 +0x06C에 있는 secure-area CRC-16을 문서화한다 [P: GBATEK, DS Cartridge Header].
둘 다 위키 어디에도 나오지 않는다. 이들은 세이브 체크섬이 아니며 그것과 혼동해서는 안 되지만,
`extract/adm-kr/header.yaml`을 읽는 포팅 작업자는 그 존재를 알고 싶어할 것이다.

## 2. `engine/text-and-messages.md`

| 위키 주장 | 공개 출처 | 판정 | 조치 |
|---|---|---|---|
| 헤더는 `MESGbmg1`, u32 파일 크기, u32 블록 수, u8 인코딩 | P: Pikmin TKB, BMG file — 0x00 매직(8 B), 0x08 데이터 크기 u32, 0x0C 섹션 수 u32, 0x10 인코딩 u8 | **정확히 확인됨** | 필드 이름만이 아니라 오프셋도 인용한다 |
| 인코딩 바이트 2 = UTF-16 | P: Pikmin TKB — 0 미정의, 1 CP1252, 2 UTF-16, 3 Shift-JIS, 4 UTF-8 | **확인됨** | — |
| "모든 대화 줄은 ... UTF-16 문자열이다" | P: 같은 표 | **90개 파일에서 거짓.** `.bmg` 파일 1,791개 중 1,701개가 인코딩 2를 선언하고, **90개는 인코딩 3, Shift-JIS를 선언**하며, 그 페이로드는 실제로 Shift-JIS 일본어다 — `message/bo/ai/shop1_.bmg`의 첫 메시지는 ウフフ、의 더블바이트 코드로 시작한다 [S: image, whole-corpus decode; `message/bo/ai/shop1_.bmg` DAT1 +1] | 요약 문장을 정정한다; 아래의 발견 사항을 추가한다 |
| 두 블록은 `INF1`과 `DAT1`, 블록 수 2 | P: Pikmin TKB — INF1, DAT1, 선택적 MID1 | **1,791개 파일 전부에서 확인됨**: 모든 파일이 정확히 두 블록을 가지며 `MID1`을 가진 파일은 없다 [S: image, whole-corpus decode] | 부정 사실을 명시한다 — 어디에도 `MID1`이 없다 — 이는 메시지가 id가 아니라 항상 인덱스로 지정된다는 뜻이다 |
| `INF1`은 12바이트 엔트리 16개를 담는다 | P: Pikmin TKB — INF1 +0x08 u16 엔트리 수, +0x0A u16 엔트리 길이; 각 엔트리는 u32 DAT1 오프셋 뒤에 속성 바이트 | **표본 파일에서는 확인됨, 일반화로는 틀림**: 1,528개 파일이 12바이트 엔트리를 쓰고, **263개는 4바이트 엔트리를 쓴다** — 속성 없는 오프셋만 있는 형태. 4바이트 파일들은 `string/` 이름 뱅크다 [S: image, whole-corpus decode] | 엔트리 크기는 파일별이며 `INF1+0x0A`에서 읽어야 한다고 명시한다; 12를 가정하는 리더는 이름 뱅크의 끝을 넘어 걷는다 |
| `DAT1`의 페이로드는 "초기 null 엔트리 다음의 UTF-16LE 텍스트" | P: Pikmin TKB — DAT1은 빈 문자열 하나로 시작한다 | **확인됨** | — |
| 문자열 순회는 코드를 **빅엔디언**으로, `(p[1] << 8) \| p[0]`로 읽는다 | — | **위키가 자기모순이며, 그 식은 리틀엔디언이다.** `(p[1]<<8)\|p[0]`는 *두 번째* 바이트를 상위 절반으로 조합하는데, 이것이 바로 리틀엔디언 u16 로드다. `DAT1` 페이로드는 UTF-16LE다 [S: image, `string/st_npc_name.bmg` decodes to Hangul only under LE]. 해결할 불일치는 없다 | 가설 "페이로드는 UTF-16LE인데 문자열 순회는 빅엔디언이다"를 삭제한다; 잘못 이름 붙인 읽기이며, 그대로 두면 누군가가 텍스트를 망가뜨릴 바이트 스왑을 추가하도록 부추긴다 |
| — (페이지에 없음) | P: Pikmin TKB와 Custom Mario Kart wiki — 이스케이프 시퀀스는 바이트 `0x1A`로 시작하고, 그 뒤에 `0x1A`와 크기 필드를 *포함한* 시퀀스 전체 크기, 그 뒤에 제어 코드 바이트가 온다 | **존재하며 대량으로 쓰인다.** 압축 해제된 `DAT1` 페이로드 전체에서 `0x1A`가 143,657번 나타난다. UTF-16 파일에서는 시퀀스가 16비트 단위다 — `001A 0006 0000`은 6바이트 이스케이프; Shift-JIS 파일에서는 바이트 단위다 — `1A 05 07 14 00`은 5바이트 이스케이프 [S: image, `message/Other/test_.bmg` DAT1 +108, `message/bo/ai/shop1_.bmg` DAT1 +1] | "이스케이프 시퀀스" 하위 절을 추가한다; 타자기(typewriter)는 이것들을 소비해야 하며, 이를 그대로 그리는 렌더러는 페이지가 이미 문서화한 "잘못된 글리프" 부류의 결함을 정확히 만들어 낸다 |
| NNS G2D 폰트 스택은 죽은 짐이다; 뒷받침하는 부정 근거는 `NFTR`이 정확히 한 파일 `dwc/utility.bin`에만 나타난다는 것 | P: GBATEK, Nitro Font Resource Format, 그리고 NintyFont — **DS에서는 매직이 뒤집혀 `RTFN`으로 저장되며**, 블록 매직도 `FNIF`/`PLGC`/`HDWC`/`PAMC`다 | **결론은 살아남지만, 적힌 근거는 부실했다.** ASCII `NFTR`을 검색했다면 실제 DS 폰트를 전부 놓쳤을 것이다. 올바른 매직으로 다시 실행하면: `RTFN`은 정확히 한 파일 `dwc/utility.bin`과 `autoload_2`(라이브러리 자체의 매직 상수)에 나타나고, `NFTR`은 `dwc/utility.bin`과 Wi-Fi 유틸리티 오버레이 `ov001`에 나타난다 [S: image, whole-tree magic scan] | 부정 근거를 `RTFN`을 인용하도록 다시 쓴다; 정정된 스캔은 가설을 *더 강하게* 만들며, 독립적으로 폰트 스택을 `ov001`에 묶어 준다 |
| 네 개의 사설 폰트는 1-bpp 비트맵, `count * w * h / 8` | P: GBATEK CGLP — 글리프 비트맵은 선언된 비트 깊이로 패킹되며, 글리프당 `tileSize` 바이트 | **네 개 모두 확인됨**, 그리고 패킹은 행별 패딩 없이 연속이다: fontA 3,314 × 9 × 16 / 8 = 정확히 59,652바이트, fontB 3,891 × 7 × 8 / 8 = 27,237이 27,240바이트 파일 안에(꼬리 3바이트) [S: image, `font/font{A,B}_img.bin` sizes] | 행 패딩이 없다는 사실을 명시한다; 바이트 경계를 넘는 9픽셀 폭 글리프가 바로 호스트 렌더러가 틀리는 지점이다 |
| fontA의 속성 테이블은 `{u16 code, u8 width, u8}` 엔트리를 담는다 | — | **직접 확인됨**: `font/fontD_attr.bin`은 비압축이고, 글리프 15개에 60바이트이며, `{0x002c, 7, 0}, {0x0030, 7, 0}, ...`로 읽힌다 [S: image, `font/fontD_attr.bin` +0]; fontA/B/C attr은 선언된 크기가 4 × count인 `LZ77` 타입 `0x10` 래퍼다 [S: image, those files +0..8] | 보강 근거가 되는 비압축 사례로 fontD를 인용한다 |

### Shift-JIS 파일 90개

이들은 흩어져 있지 않다. 여섯 성격 디렉터리 모두에서, 성격당 정확히 열다섯 개의 메시지 파일이
인코딩 3을 선언한다: `q09/` 아래 여덟 개, `ai/` 아래 여섯 개, `etc/` 아래 하나
[S: image, whole-corpus decode, grouped by directory]. 이 규칙성은 이것들이 의도된 혼합 인코딩
설계가 아니라, 여섯 목소리 모두에서 번역되지 않은 채 남은 *같은 열다섯 메시지* — 현지화를
살아남은 일본어 원문 — 임을 말해 준다.

포트에게 이것은 잡학이 아니라 실제 위험이다: 요약 문장을 믿고 모든 `DAT1`을 UTF-16으로 다루는
리더는 Shift-JIS 바이트 쌍을 글리프 조회에 넘기게 되고, 모든 코드가 빗나가며, 모든 글리프가
`0xFF20`으로 폴백한다 — `func_020a8e8c`가 다른 이유로 이미 한 번 만들어 냈던 바로 그 실패다.
ROM 자체 리더가 인코딩 바이트를 존중하는지는 알려지지 않았으며, 아래의 실험이 그것이다.

## 3. `data/rom-layout.md`

| 위키 주장 | 공개 출처 | 판정 | 조치 |
|---|---|---|---|
| 추출된 헤더는 식별 정보는 담지만 FNT/FAT/OVT 오프셋은 담지 않는다 | P: GBATEK — 그 필드들은 실제 카트리지 헤더의 +0x40..+0x5C에 존재한다 | **ROM이 아니라 `header.yaml`에 관한 진술로서는 확인됨.** 오프셋은 카트리지에 존재한다; 패커가 다시 계산하므로 추출기가 기록하지 않을 뿐이다 | 독자가 카트리지에 그것이 없다고 결론짓지 않도록 다시 쓴다 |
| 36개 최상위 디렉터리에 9,508개 파일, 더하기 `BUILDTIME`과 `sound_data.sdat` | — | **확인됨**: 트리에는 정확히 36개의 최상위 디렉터리가 있다 [S: image, root listing] | 페이지의 디렉터리 표는 `broadcast/`, `caution/`, `shadow/`, `snowman/`을 빠뜨리고 있다; 추가하거나 표가 부분적이라고 밝힌다 |
| ARM9 오버레이 테이블 엔트리는 base, code size, bss, ctor 범위, 파일 id, compressed, signed를 담는다 | P: GBATEK, NitroROM — OVT는 오버레이 ID를 파일 ID에 대응시키며 로드 주소와 추가 정보를 담는다 | **확인됨** | 없음 |
| 모든 경로는 그것을 필요로 하는 모듈에 컴파일되어 들어간 `printf` 스타일 템플릿이다 | — | 포맷 주장이 아니다; 공개 자료 중 이에 관련된 것이 없다 | 없음 |

## 4. `data/archives.md`

| 위키 주장 | 공개 출처 | 판정 | 조치 |
|---|---|---|---|
| `LZ77` 다음 워드는 "하위 바이트 = 타입, 상위 24비트 = 압축 해제 크기" | P: GBATEK, BIOS Decompression — 비트 0-3 예약, 비트 4-7 타입(1 = LZ77), 비트 8-31 압축 해제 크기 | **타입 `0x10` 파일 6,330개에서 확인됨**, 이들의 LZ77 스트림은 +8에서 곧바로 시작한다 [S: image, `anm/0/0.nsbca` +0..12] | `LZ77` ASCII 매직 자체는 SDK 헤더의 일부가 *아니라* 그 앞에 붙은 이 게임의 4바이트 접두사임을 적어 둔다 |
| 1,790개 파일이 타입 `0xf7`을 가지며, "별개의 압축 변형이거나 난독화" | P: GBATEK의 타입 목록에 `0xf7`은 없다 | **해결됨 — 핵심 결론 절 참조.** `0xf7`은 평범한 타입 `0x10`(그리고 세 번은 타입 `0x00`) 스트림의 청크 컨테이너다 | 두 가설을 디코딩된 레이아웃으로 대체한다; "압축 해제기에 브레이크포인트를 걸어 확정한다"는 실험은 그것이 *무엇인지*에 답하는 데는 더 이상 필요 없고, *누가* 읽는지에만 필요하다 |
| 크기 필드는 "그럴듯하게 읽히지만 ... 실제 압축 해제와 대조되지는 않았다" | — | **대조했다.** 모든 `0xf7` 파일의 선언된 총 크기가 압축 해제 길이와 같고, BMG 자체의 +8 크기 필드도 일치한다 [S: image, whole-corpus decode] | 가설을 닫는다 |
| NARC 헤더: BOM `FFFE`, 버전 `0100`, 헤더 크기 `0x10`, 블록 3개 | P: ndspy `narc.py`, rawdb | **확인됨**, §1의 BOM 종류 메모와 함께 | §1과 같음 |
| `BTAF`의 블록 헤더 뒤 첫 하프워드는 엔트리 수 | P: ndspy는 파일 수를 BTAF+0x08의 u32로 읽고 엔트리를 +0x1C에서 시작한다; 다른 리더들은 u16 count + u16 reserved로 기술한다 | **호환됨** — 이 ROM에서는 상위 하프워드가 0이므로 두 읽기 모두 같은 답을 준다 [S: image, `str/bsize.arc` BTAF +8 = `1e 00 00 00`] | u16 읽기에서는 엔트리가 BTAF+0x0C에서 시작하며, ndspy의 +0x1C 오프셋은 블록 시작이 아니라 파일 시작 기준이므로 두 위치는 같은 곳이라고 밝힌다 |
| `.nsbmd`=`BMD0`, `.nsbtx`=`BTX0`, `.nsbca`=`BCA0`, `.nsbtp`=`BTP0`, `.nsbva`=`BVA0`, `.nsbta`=`BTA0`, `.nsbma`=`BMA0` | P: scurest `nsbmd_docs.txt` §Filetypes, apicula FILETYPES | **BMD0/BTX0/BCA0/BTP0/BTA0는 확인됨**; scurest는 **BVA0와 BMA0를 미문서화로** 명시적으로 표시한다 | 미문서화된 두 개는 이미지 관측으로 유지한다; 존재하지 않는 사양을 인용하지 않는다 |
| G3D 컨테이너는 범용 닌텐도 헤더를 쓴다 | P: scurest §Container Header — 스탬프, BOM 0xFEFF, 버전, 파일 크기, 헤더 크기 16, 서브파일 수, 그 뒤 u32 오프셋 배열 | **확인됨** | `BMD0`가 `TEX0`를 직접 내장할 수 있으므로 모델이 항상 `.nsbtx`와 짝지어지지는 않는다는 점을 추가한다 — 이는 `items.md`의 `ftr/` 짝 주장에 영향을 준다 |
| `spl/spl.spa`, 61,212바이트, "매직 `SPA `가 리틀엔디언으로 저장됨" | P: NSMBHD — 파일은 뒤집힌 바이트 `" APS"`로 시작하고, 그 뒤 버전 스탬프, u16 파티클 수, u16 텍스처 수, 그 뒤 블록 길이들과 텍스처 블록 오프셋 | **확인되고 크게 확장됨.** 첫 여덟 바이트는 `20 41 50 53 30 32 5f 31`, 즉 뒤집힌 두 워드 `SPA `와 `1_20` — **SPA 버전 1.20**이다. 헤더는 이어서 **파티클 이미터 235개와 텍스처 97개**, 파티클 블록 26,788바이트, 오프셋 26,820의 텍스처 블록 34,392바이트를 준다; 26,820 + 34,392 = 61,212 = 정확히 파일 크기 [S: image, `spl/spl.spa` +0..0x1c] | 한 줄짜리 항목을 디코딩된 헤더로 대체한다; 현재 파티클에 관해 아무 말도 없는 페이지에 공짜로 생기는 표다 |
| `.bch`/`.bsc`/`.bpl`은 "자체 매직을 갖지 않는다" | P: 없음 — 사설 관례다 | **공개 출처로는 검증 불가**; `_ncg`/`_ncl`/`_nsc` 유추가 여전히 최선의 읽기다 | NitroSystem 2D 포맷 역시 뒤집힌 매직(`RGCN`, `RLCN`, `RCSN`)을 저장하므로, `NCGR`을 찾는 매직 스캔은 헤더가 있었더라도 아무것도 찾지 못했을 것이라고 적어 둔다 — 헤더가 제거되었다고 결론짓기 전에 뒤집힌 표기로 스캔을 다시 실행한다 |

## 5. `data/music.md`

| 위키 주장 | 공개 출처 | 판정 | 조치 |
|---|---|---|---|
| SDAT 헤더: 매직, BOM, 크기, 헤더 크기 64, 블록 디스크립터 네 개 | P: GBATEK SDAT, Feshrine §Header — 다른 Nitro 파일이 `0x10`을 쓰는 것과 달리 헤더 크기는 특이하게 `0x40`이다; 블록은 SYMB, INFO, FAT, FILE 순서 | **정확히 확인됨**, 블록 수 3까지 포함해서 [S: image, `sound_data.sdat` +8..16] | 0x40 헤더 크기는 게임의 기벽이 아니라 문서화된 SDAT의 특이점임을 적어 둔다 |
| `SYMB` 블록이 없고, 오프셋 0 크기 0이므로 아무것도 이름을 갖지 않는다 | P: GBATEK — "SYMB 블록은 대부분의 SDAT 파일에 존재한다(일부 타이틀 제외 ...)"; 없을 때는 블록 수가 3이고 디스크립터 쌍이 0이다 | **확인됨, 그리고 이는 이상한 경우가 아니라 지원되는 구성이다** | 주장을 유지하고, SYMB 제거가 문서화된 동작임을 추가한다; 가설 "이름 기반 조회는 동작할 수 없다"는 사양으로 확정된다. INFO와 FAT는 설계상 인덱스 기반이기 때문이다 |
| `INFO`는 여덟 개의 레코드 테이블을 담으며, 각각은 count 뒤에 그만큼의 오프셋 | P: GBATEK / Feshrine — INFO의 헤더는 +0x08에 있는 여덟 개의 u32 레코드 테이블 오프셋이고, 각 테이블은 `u32 count` 뒤에 `count × u32` 엔트리 오프셋이며, **0은 부재를 뜻한다** | **확인됨**, 그리고 34개의 0 SEQ 오프셋을 설명해야 할 구멍이 아니라 사양 자체의 "부재 엔트리" 인코딩으로 설명해 준다 | 그렇게 적는다; 가설 "미정의 SEQ 슬롯 34개는 잘려 나간 음악이다"는 이제 0이 무엇을 뜻하는지가 아니라 *왜* 패커가 빈틈을 남겼는지에 관한 질문이다 |
| 여덟 테이블은 SEQ, SEQARC, BANK, WAVEARC, PLAYER, GROUP, PLAYER2, STRM | P: GBATEK, 같은 순서 | **확인됨**; PLAYER2는 **스트림 플레이어** 테이블이다 | 페이지에서 PLAYER2를 STRMPLAYER로 바꾼다 |
| 구간 산술로 유도한 레코드 크기: SEQ 12, SEQARC 4, BANK 12, WAVEARC 4, PLAYER 8, GROUP 가변, PLAYER2 —, STRM — | P: GBATEK + Feshrine + ndspy 일치: SEQ 12(10 사용 + 2 패딩), SEQARC 4, BANK 12, WAVEARC 4, PLAYER 8, GROUP 가변 `4 + n*8`, **STRMPLAYER 24**, **STRM 12**(8 사용 + 4 패딩) | **측정된 모든 크기가 독립적인 경로로 확인됨**, 그리고 위키가 비워 둔 두 개가 채워진다 | 24와 12를 채워 넣는다; 그리고 필드에 이름을 붙인다 — SEQ는 `{u16 fileID, u16, u16 bankID, u8 vol, u8 cpr, u8 ppr, u8 playerID}`, BANK는 `{u16 fileID, u16, u16 swarID[4]}`이며 미사용은 `0xFFFF` |
| "웨이브 아카이브 14개에 악기 뱅크 943개는 비정상적으로 많은 수다" | P: BANK 레코드는 최대 네 개의 SWAR id를 지정하며, `0xFFFF` = 미사용 | **가설은 이제 정적으로 싸게 확정할 수 있다** — 943개 레코드를 전부 디코딩해 네 id 튜플의 히스토그램을 만든다; 실행이 필요 없다 | 실험을 정적인 것으로 다시 쓴다 |
| FAT 엔트리는 16바이트, 오프셋과 크기 | P: Feshrine, GBATEK — `u32 offset`(SDAT 시작부터의 절대값), `u32 size`, 런타임 용도의 예약 8바이트 | **확인됨**, 그리고 예약 8바이트에 이름이 붙는다 | 오프셋이 SDAT 안의 절대값임을 추가한다; 그것이 `NNS_SndArcGetFileAddress`를 단순한 덧셈으로 만드는 이유다 |
| — | P: Feshrine §Sound File Headers — 포함된 파일은 `SSEQ`, `SSAR`, `SBNK`, `SWAR`, `SWAV`, `STRM`이며 각각 표준 16바이트 Nitro 헤더를 가진다 | **여기서는 미검증** | 한 줄짜리 정적 검사: 각 FAT 오프셋의 첫 네 바이트를 히스토그램으로 만든다. 스트림은 `STRM`으로 읽힐 것이므로, "3.2 MB 파일은 두 스트림 중 하나다"라는 가설을 측정으로 바꿔 준다 |

⚠️ 공개 출처들은 두 SDAT 레코드에 관해 서로 다르다: OpenKh는 GROUP을 12바이트, STRM을 8바이트로
적는다. GBATEK, Feshrine, ndspy는 GROUP이 가변이고 STRM의 스트라이드가 12이며 의미 있는 바이트는
8이라는 데 일치한다. 위키 자체의 구간 산술은 GROUP을 가변으로 측정했고, 이는 다수 쪽에 선다 —
위키의 측정이 공개 출처 간의 불일치를 해소했다고 기록한다.

## 6. `data/items.md`

이 페이지에는 컨테이너 포맷 주장이 없다; 센서스와 산술이며, `ftr_info/`나 `item_info/` 레코드
크기에 관련된 공개 사양은 없다. 포맷 수준의 메모 두 가지는 적용된다:

- 이 페이지는 각 가구 id가 `.arc`(지오메트리) 하나와 `.nsbtx`(텍스처) 하나로 짝지어진다고
  가정한다. 공개 G3D 문서는 `BMD0`가 `TEX0` 서브파일을 내장할 **수 있다**고 하므로, 이 짝은
  포맷 요구 사항이 아니라 패킹 선택이다 [P: scurest `nsbmd_docs.txt` §Filetypes]. 싼 검사:
  `ftr/*/*/*.arc` 멤버 몇 개를 풀어 서브파일 스탬프를 센다.
- `NARC`의 `BTNF` 이름 테이블은 아직 읽지 않았다 — 페이지 자체의 가설이다. 공개 리더들은 흔한
  스텁(`08 00 00 00 01 00 00 00`, 암묵적 루트 하나, 이름 없음)을 문서화하므로
  [P: ndspy `narc.py`], 유력한 답은 "이름 없음"이고, 검사는 네 바이트 길이다.

## 7. `data/villagers.md`

컨테이너 포맷 주장이 없다; 페이지는 센서스와, 문자열 리터럴에서 읽어 낸 오버레이-에셋 연결이다.
공개 출처는 더하는 것도 모순되는 것도 없다. 상속된 정정 하나: 이 페이지의 "성격 접두사"와
`.bmg` 경로 설명은 `engine/text-and-messages.md`에 의존하므로, 위의 인코딩 3 발견 사항이 주민
대화 트리에도 적용된다 — 각 성격의 242개 파일 중 열다섯 개가 일본어다.

## 8. `systems/save-data.md`

이 페이지는 공개 기록이 가장 크게 도움이 되는 페이지다. 독립적인 세 세이브 에디터가 **한국판**을
부차적인 것이 아니라 정식 지역으로 다루기 때문이다.

| 위키 주장 | 공개 출처 | 판정 | 조치 |
|---|---|---|---|
| 백업 저장소는 256 KB 플래시 칩이다 | P: WildEdit `core/source/utils/saveUtils.cpp`, `SaveUtils::getSave()`는 정확히 `0x40000`, `0x4007A`(122바이트 DeSmuME `.dsv` 푸터), `0x80000`, `0x8007A`를 받아들인다 | 세 에디터와 ROM 자체의 `0x1202` 식별 워드로 **확인됨** | `.dsv` 덤프는 122바이트 푸터를 달고 있다고 밝힌다 — 그것을 가리키는 `ACWW_SAVE`는 122바이트만큼 길고, 조용히 틀린다 |
| `0x173fc`바이트짜리 뱅크 두 개 | P: WildEdit `saveUtils.cpp` `SavCopyOffsets[4] = { 0x15FE0, 0x15FE0, 0x12224, 0x173FC }`, `WWRegion { EUR, USA, JPN, KOR }`로 인덱싱; 같은 네 숫자가 ACWW-Web-SaveEditor `assets/js/core/sav.js`와 ACWW_Research 위키 `Offset_Sizes`에도 있다 | **정확히 확인됨, 그리고 `func_020b5724`와는 독립적으로.** `0x173FC`는 *한국판* 블록 크기다; `0x15FE0`은 서양판, `0x12224`는 일본판이다 — 같은 필드에 대한 경쟁하는 읽기가 아니다 | 이 페이지에서 가장 강한 보강 근거다: ROM에서 온 S 출처와 네 에디터에서 온 P 출처가 `0x173FC`에서 일치한다. 둘 다 기록한다 |
| 두 뱅크는 "독립적인 두 슬롯이 아니라 주/백업 쌍이다"(가설) | P: WildEdit `core/source/Sav.cpp` `Sav::Finish()`는 체크섬을 고친 뒤 블록 전체를 오프셋 0에서 `SAVCOPY_OFFSET`으로 `memcpy`한다; JS 쌍둥이도 같다 | **에디터들은 복사본 2를 체크섬 필드까지 바이트 단위로 동일한 클론으로 취급한다** — 두 슬롯이 아니라 주/백업 읽기다 | *에디터에 대해서는* 가설이 답해졌다; ROM이 번갈아 쓰는지는 여전히 열려 있다. 실험은 유지하되 에디터들이 무엇을 가정하는지 적어 둔다 |
| "세이브 레코드는 체크섬을 가지지만, 아직 발견되지 않았다" | P: WildEdit `core/source/utils/checksum.cpp` `Checksum::Calculate` — 블록의 모든 리틀엔디언 u16 워드를 합하되 체크섬 인덱스의 워드는 건너뛰고, `(u16)-sum`을 저장한다; ACSE `ACSE.Core/Saves/Checksums/UInt16LEChecksum.cs`는 동일한 루틴을 구현한다; ACWW-Web-SaveEditor `assets/js/utils/checksum.js`는 `0x10000 - sum`을 반환한다 | **발견됨.** 체크섬은 2의 보수로 저장되는 16비트 리틀엔디언 워드 합이므로, 유효한 블록은 합이 0이다. 한국판의 필드는 **`0x173F8`** — 블록의 마지막 u16 정렬 워드 — 에 있으며, `UpdateChecksum`은 워드 수 `0xB9FC`(= `0x173F8 / 2`)를 넘긴다 | 이는 페이지의 첫 가설을 등급 P에서 닫는다. 등급 S에서는 닫지 **않는다**: `func_020b5724`에 있는 ROM 자체의 유효성 검사는 아직 읽지 않았다. 가설을 "`func_020b5724`는 이 합을 계산하는가?"로 다시 서술한다 — 기대하는 답이 알려진, 훨씬 좁은 질문이다 |
| — | P: ACWW_Research 위키 `Offset_Sizes`; WildEdit `core/source/LetterStorage.cpp` | **체크섬이 있는 두 번째 영역이 존재한다.** 편지 보관소는 한국판에서 두 뱅크 바깥인 `0x337FC`에 있으며, 256 KB 이미지의 마지막 u16인 `0x3FFFE`에 `0xC802`바이트에 걸친 자체 체크섬을 가진다 | 추가한다. `2 × 0x173FC = 0x2E7F8`이므로 칩의 약 70 KB는 어느 뱅크에도 속하지 *않는데*, 페이지는 현재 뱅크가 저장소 전체인 것처럼 암시한다 |
| — | P: WildEdit `saveUtils.cpp` — 세이브는 오프셋 0 **그리고** 두 번째 복사본 시작에서 게임코드 바이트가 일치할 때 받아들여진다; `GameCodes[4] = { 0xC5, 0x8A, 0x32, 0x32 }`이므로 한국판은 `0x32`다; `Town.cpp`는 마을 id `0x0000`/`0xFFFF`를 "마을 없음"으로 취급한다; `Player.cpp` `exist()`는 0이 아닌 플레이어 id다 | **게임의 것이 아닌, 에디터 수준의 유효성 검사** | 이것이 바로 페이지의 "0xFF 소거 대 0 채움" 가설을 위한 재료다: 0으로 채워진 블록은 게임코드 0과 마을 id 0을 가지며, 이는 게임코드가 0xFF인 소거된 0xFF 블록과 같지 *않다*. 둘 다 무효이지만, 서로 다른 분기를 탈 수 있다 |
| — | P: ACWW_Research 위키, *Character Encoding*: EUR/USA와 JPN은 사설 256 엔트리 단일 바이트 표를 쓴다; "**한국판은 UTF-16, 더 정확히는 UCS-2를 쓴다**". WildEdit는 한국판 이름을 `ReadUTF16String`으로 읽고 다른 모든 지역은 `wwCharacterDictionary`를 거쳐 읽는다 | **포트와 `engine/text-and-messages.md`에 직접 관련됨**: 한국판 세이브는 이름을 UCS-2로 저장하며, 이는 글리프 조회가 소비하는 것과 같은 16비트 코드다 | 추가한다; 세이브에서 읽어 낸 이름을 변환 없이 글리프 경로에 넘길 수 있다는 뜻이며, 검증 가능한 예측이다 |
| — | P: ACWW_Research 위키 + WildEdit `Sav.cpp`, `Player.cpp` — 한국판: `+0x14`에서 시작하는(다른 모든 지역의 `+0x0C`가 아니라) `0x249C`바이트 플레이어 레코드 4개, 주민 블록은 `0x9284`, 주민 레코드 `0x7EC`; 마을 id는 `+0x02`, 마을 이름은 `+0x04`에 `char16_t` 12바이트 | **구조적이며, 한국판 고유** | 이것으로 `systems/save-data.md`에 등급 P의 "뱅크 안에 무엇이 있는가" 절을 시작하기에 충분하며, S 작업은 각 오프셋을 매칭된 접근자와 대조해 확인하는 것이다 |

⚠️ **ACSE의 상수를 가져오지 말 것.** ACSE의 `WildWorldOffsets` 블록과 `"EMDA" @ 0x1E40` 인식기는
미국판 전용이며, 한국어 문자 표를 싣고 있지 않다. WildEdit와 ACWW_Research 위키가 한국판을
인식하는 출처다. 출처의 결함 하나 더: 리서치 위키의 `Main-Structure` 페이지는 한국판 총 크기를
`0x12224`로 적어 일본판 행을 중복하고 있다; `Offset_Sizes`, `saveUtils.cpp`, `sav.js`는 모두
`0x173FC`라 하고, ROM도 이에 일치한다.

---

## 우선순위별 조치 — 포트

**P1. 포트의 파일 로더에 `0xf7` 청크 컨테이너를 가르치거나, ROM 자체 리더가 이를 처리함을
증명한다.** `port/shim/fs/loadfile.c`의 `func_02064b2c`는 `LZ77` 매직을 인식하고 타입 바이트와
무관하게 `header+4`에 `MI_UncompressLZ8`을 호출한다. 어떤 `.bmg`든 그 로더에 도달하면 텍스트는
쓰레기가 되고 아무것도 오류를 보고하지 않는다. *필요한 근거:* 대화 상자를 여는 레시피에서
`port/shim/gfx/w11_lztrace.c`를 켜고, 각 `MI_UncompressLZ8` 호출마다 `src`의 첫 여덟 바이트를
기록한다. `LZ77 f7`로 시작하는 소스는 잘못된 경로를 증명하고, 0이 아닌 파일 오프셋에서
`10 xx xx xx`로 시작하는 소스는 ROM이 자체 청크 워커를 가짐을 증명하며 호출자로 그것을 식별한다.

**P2. 메시지 시스템의 압축 해제기를 찾아 이름을 붙인다.** 그것은 `func_020648a0`,
`func_020649ac`, `func_02064b2c`, `func_ov001_0222b7c8`이 아니다 — 이 넷이 `src/matched/`에서
`MI_UncompressLZ8`을 호출하는 유일한 호출자이고, 어느 것도 u16 청크 테이블을 읽지 않는다. *필요한
근거:* P1이 식별한 호출자, 그다음 그 함수의 차분 검사; 작고 순수하며 자족적인 본체이므로 싼
네이티브 승격 대상이다.

**P3. 타자기가 BMG 이스케이프 시퀀스와 인코딩 바이트를 존중하게 만든다.** 압축 해제된 메시지
페이로드에 `0x1A`가 143,657번 나타난다. 규칙은 문서화되어 있다: `0x1A`, 그다음 전체 길이, 그다음
제어 코드 — 인코딩 2 파일에서는 16비트 단위, 인코딩 3 파일 90개에서는 바이트 단위. *필요한 근거:*
이스케이프를 담고 있다고 알려진 메시지(임의의 `message/*/q/*` 파일)에서 `func_0206726c`가 반환한
직후 `self+0x14ac`에 있는 문자열 객체의 첫 16바이트를 덤프하고, 버퍼에 `1A`가 여전히 남아 있는지
아니면 리더가 이미 제거했는지 확인한다.

**P4. Shift-JIS 파일에 부딪히기 전에 확정한다.** 성격당 열다섯 개의 메시지 파일이 Shift-JIS
일본어다. *필요한 근거:* 마을 레시피를 `q09/` 대화가 열릴 만큼 충분히 실행하고 상자를 스크린샷한다;
올바른 일본어 글리프, 쓰레기, 또는 `＠`(`0xFF20`)의 벽은 각각 다른 버그를 가리킨다. 이는 싸고,
그렇지 않으면 글리프 조회 탓으로 두 번째로 돌려질 종류의 결함이다.

**P5. 호스트 렌더러에서 사설 폰트 네 개의 패킹을 검증한다.** 비트맵은 1 bpp이며 **행별 패딩이
없다** — fontA의 9픽셀 폭 글리프는 바이트 경계를 넘는다. *필요한 근거:* fontA 글리프 383(`0xFF20`,
알려진 폴백)과 넓은 한글 글리프 하나를 렌더링해 오라클의 프레임과 비교한다; 행을 바이트 단위로
패딩하는 렌더러는 알아볼 수 있는 기울어짐을 만들어 낸다.

**P6. `ACWW_SAVE`에 실제 이미지를 준다.** 체크섬 알고리즘과 한국판 오프셋이 이제 알려졌으므로,
소거된 이미지만이 아니라 *유효한* 256 KB 이미지를 구성할 수 있다 — 오프셋 0과 `0x173FC`에 게임코드
`0x32`, 마을 id, 그리고 블록 합을 0으로 만드는 `0x173F8`의 체크섬. *필요한 근거:* 그런 이미지에
대해 키 입력 START 레시피를 실행하고, 부팅이 `unimplemented: func_02225a90`에서 멈추는 대신
`func_020b5724`에서 기존 마을 분기를 타는지 본다. 이 단일 실험은 포트의 카드 경로, 위키의 뱅크
주장, 공개 체크섬 문서를 한꺼번에 검증한다.

**P7. 낮은 우선순위 — 두 NARC BOM 표기를 모두 받아들인다.** `IsValidArchiveBinary`는 `0xFFFE`를
요구하며, 이 ROM에 대해서는 옳다. 포트가 나중에 갖게 될 호스트 측 NARC 리더는 `0xFEFF`를 기대하는
공개 리더에서 그 요구 사항을 복사해서는 안 된다.

## 우선순위별 조치 — 위키

**W1. `data/archives.md`와 `engine/text-and-messages.md`의 `0xf7` 자료를 다시 쓴다.** "알 수
없는 알고리즘 또는 난독화" 가설 둘을 디코딩된 컨테이너로 대체한다. 이 페이지에서 가장 큰 단일
정정이며, 큐에서 실험 하나를 제거한다. *근거:* 위의 전체 말뭉치 디코드; 파이썬 스무 줄로 재실행
가능하다.

**W2. "모든 대화 줄은 UTF-16이다"를 정정하고 Shift-JIS 파일 90개를 추가한다.** *근거:* 인코딩
바이트 히스토그램, 그리고 디렉터리별 분류(성격당 `q09/` 8개, `ai/` 6개, `etc/` 1개).

**W3. 거짓인 빅엔디언/리틀엔디언 모순을 삭제한다.** `(p[1]<<8)|p[0]`는 리틀엔디언 로드이며
페이로드는 리틀엔디언이다. *근거:* `st_npc_name.bmg`는 LE에서는 한글로, BE에서는 아무것도 아닌
것으로 디코딩된다.

**W4. `NFTR` 부정 근거를 `RTFN`을 검색하도록 고친다.** *근거:* 정정된 전체 트리 스캔 — `RTFN`은
`dwc/utility.bin`과 `autoload_2`에만; `NFTR`은 `dwc/utility.bin`과 `ov001`에. 뒤집힌 2D
매직(`RGCN`/`RLCN`/`RCSN`)에 대한 같은 경고를 `.bch`/`.bsc`/`.bpl` 단락에 추가한다. 그 단락은
현재 잘못된 표기를 찾았을 수 있는 스캔으로부터 "매직 없음"을 결론짓고 있다.

**W5. `INF1` 엔트리 크기가 파일별임을 밝힌다.** 1,528개 파일이 12바이트 엔트리를, 263개가 4바이트
엔트리를 쓴다; 크기는 `INF1+0x0A`에 있다. *근거:* 전체 말뭉치 디코드.

**W6. 위키가 비워 둔 SDAT 레코드를 채우고 그 필드에 이름을 붙인다.** STRMPLAYER는 24바이트, STRM은
12; SEQ와 BANK 필드 목록은 문서화되어 있다. PLAYER2를 STRMPLAYER로 바꾸고, INFO 테이블의 0 오프셋은
포맷 자체의 "부재" 인코딩임을 밝힌다.

**W7. `systems/save-data.md`에서 세이브 뱅크 내부를 시작한다.** 한국판 오프셋 — 헤더 `0x14`,
`0x249C` 플레이어 레코드 4개, `0x9284`의 주민, 마을 id `+0x02`, UCS-2 이름, 체크섬 `0x173F8`,
`0x3FFFE`에 자체 체크섬을 가진 편지 보관소 `0x337FC` — 는 모두 등급 P이고 모두 한국판 고유다. 각각은
그것을 읽는 매칭된 접근자가 발견되는 순간 등급 S가 된다. *행별 필요한 근거:* 그 오프셋을 읽는 함수.

**W8. `data/archives.md`의 한 줄짜리 SPA 항목을 디코딩된 헤더로 대체한다.** 버전 1.20, 이미터
235개, 텍스처 97개, 그리고 합이 파일 크기가 되는 두 블록 길이.

**W9. `data/rom-layout.md`에 헤더 CRC-16 필드를 추가한다.** 아무도 이를 세이브 체크섬으로 오해하지
않도록 하고, 센서스 표에 빠진 최상위 디렉터리 네 개를 추가한다.

**W10. 포맷이 알려졌으므로 세 가설을 정적 검사로 바꾼다:** BANK 레코드 943개의 웨이브 아카이브
튜플, SDAT `FAT` 매직 히스토그램(실행 없이 두 스트림과 3.2 MB 파일을 식별한다), 그리고
`st_music.bmg`의 `INF1` 엔트리 수 — 파일이 이제 풀리므로 읽을 수 있게 되었다.

## 관련 문서

- `../data/archives.md`, `../engine/text-and-messages.md` — 이 감사가 가장 많이 바꾸는 두 페이지.
- `../systems/save-data.md`, `../data/music.md` — 가장 많이 확장하는 두 페이지.
- `../README.md` — 이 페이지의 **P** 등급이 나란히 놓이는 등급 표, 그리고 팬 위키 금지 규칙:
  세이브 에디터의 *소스 코드*는 팬 위키의 주장이 아니라 도구 구현이며, 여기서는 그런 것으로
  인용된다. 그 숫자가 측정된 것과 일치하는 곳에서도 근거는 여전히 측정이다.
