# 감사(audit): 하드웨어 서비스와 공개 기록의 대조
<!-- source: wiki/audits/hardware-services.md -->

**요약.** 포트가 ROM 아래에 공급하는 모든 하드웨어 서비스 — ARM7 대역, DMA,
나눗셈/제곱근 유닛, 디스플레이 카운터, 2D 효과 유닛, 지오메트리 엔진, 그리고
BIOS — 를 GBATEK, 공개 NitroSDK 소스 미러, 에뮬레이터 소스와 대조하여 점검했다.
서른한 개의 주장을 점검했다. 스물두 개는 공개 기록과 일치하고, 여섯 개는 불일치하며, 세 개는
미규정이다. 여섯 개의 불일치는 작고 국소적이며 각각 이름 붙은 수정안이 있다. 그중 둘
(CpuFastSet의 올림과 262번 라인의 VBlank 플래그)은 인용된 스펙 문장에 비추어 명백히 틀렸고,
하나(스타일러스 지연)는 포트가 원본에서 벗어난 것으로 측정된 가장 큰 차이이며 버그가 아닌
설계상의 선택이다. Animal Crossing의 디컴파일은 공개된 것이 없다. 반면 완전한 NitroSDK와
NitroSystem 소스 트리는 공개되어 있으며, 이 저장소가 아직 `func_XXXXXXXX`라고 부르는 것들의
상당 부분에 이름을 붙여 줄 수 있다.

**방법.** 커밋 `470df4ac`에서 읽었다. 공개 소스는 기억이 아니라 실제로 가져왔으며, 아래 각 행은
URL과 해당 페이지의 제목을 명시한다. 어떤 소스에서도 코드를 복사하지 않았다. 게임은 실행하지
않았다. 한 가지 주장(BIOS CRC16)은 세 후보 알고리즘을 모두 다시 구현하고 수치적으로 비교하여
점검했는데, 이것이 이 감사가 막 발표하려던 발견 사항을 뒤집었다 — B4 행과 M1을 보라.

---

## 1. 주장 표

판정은 **일치** / **불일치** / **미규정**(공개 기록이 결론을 내리지 못함)이다.
"포트"는 주장이 위치한 파일과 함수를 가리킨다.

### A. 스타일러스 샘플링과 TSC 변환

| # | 포트/위키가 서술하는 주장 | 공개 소스 | 판정 | 무엇을 바꿀 것인가 |
|---|---|---|---|---|
| A1 | 터치 패널은 ARM7이 폴링하는 SPI 장치이며, 샘플은 12비트 ADC 카운트로 X는 채널 5, Y는 채널 1이다 [`wiki/systems/input-and-touch.md`, "The stylus"] | GBATEK, [DS Touch Screen Controller (TSC)](https://problemkaputt.de/gbatek-ds-touch-screen-controller-tsc.htm), "Control Byte" 및 "Channels" 절 | 일치 | 없음 |
| A2 | 보정은 ADC 카운트에서 픽셀로 가는 2점 선형 사상이다 | GBATEK, 같은 페이지, "Converting ADC Position to Screen Position": `scr.x = (adc.x-adc.x1) * (scr.x2-scr.x1) / (adc.x2-adc.x1) + (scr.x1-1)` | 일치 | 없음 — 다만 **`-1`** 항에 주목하라. 픽셀→ADC→픽셀 왕복은 항등이 아니며, 이것이 탭이 한 픽셀 어긋나 돌아오는 문서화된 이유이다 |
| A3 | 오라클에서 측정된 1픽셀 오프셋(221,181 입력 → 222,182 출력)은 에뮬레이터가 픽셀을 ADC 카운트로 변환하고 `TP_GetCalibratedPoint`가 다시 되돌리는 과정의 인공물이다 [`input-and-touch.md`, "The port and the original disagree"] | melonDS [`src/SPI.cpp`](https://github.com/melonDS-emu/melonDS/blob/master/src/SPI.cpp), TSC `SetTouchCoords`: 호스트 좌표는 `TouchX <<= 4`, 즉 픽셀×16으로 저장되며 보정 역변환은 전혀 없다 | 일치, 단 정정 있음 | 에뮬레이터는 펌웨어 보정을 역변환하지 **않는다** — 16을 곱할 뿐이다. 따라서 ±1은 기울기가 정확히 16이 아닌 보정값에 대한 `TP_GetCalibratedPoint` 자체의 역수-시프트 연산에서 나온다. 위키 페이지에서 "화면 픽셀을 원시 ADC 카운트로 변환한다" 대신 이렇게 서술하라 |
| A4 | 원본은 포트보다 탭을 1–2프레임 늦게 전달하며, 한 프레임 더 오래 유지한다 [`input-and-touch.md`; ORACLE42] | melonDS `src/SPI.cpp`: "터치 좌표 설정과 ARM7의 읽기 가능 사이에 지연 없음" — 에뮬레이터는 아무 지연도 더하지 않는다 | 일치, 그리고 원인이 이제 명명됨 | 지연은 **전적으로 ROM 자신의 ARM7 + PXI + `func_020e9314` 체인** 때문이지 에뮬레이터 랙이 아니다. 따라서 포트에서 재현 가능하다. 수정안 **P1**을 보라 |
| A5 | ACWW는 "샘플링 주기 4"로 아홉 항목짜리 링을 돌린다 [`input-and-touch.md`, "The stylus"] | NitroSDK, [`include/nitro/spi/ARM9/tp.h`](https://github.com/ntrtwl/NitroSDK/blob/main/include/nitro/spi/ARM9/tp.h): `TP_RequestAutoSamplingStartAsync(u16 vcount, u16 frequence, TPData bufs[], u16 bufSize)` 및 `TP_SAMPLING_FREQUENCY_MAX` | 미규정 (헤더에 주석 없음) | 두 번째 인자는 `frequence`이지 주기가 아니다. 문서화된 최댓값이 16이고 ACWW가 4를 넘기므로, 자연스러운 해석은 **프레임당 네 샘플**이며, 이는 아홉 항목 링을 2.25프레임 깊이로 만들고 `func_020e9314`의 "마지막 네 항목"을 정확히 한 프레임 분량으로 만든다. 페이지를 고쳐 쓰고 ARM7 쪽을 읽을 때까지 H 등급으로 표시하라 |
| A6 | `validity`는 오류 코드이며 0은 샘플이 정상임을 뜻한다 | NitroSDK `tp.h`: `TP_VALIDITY_VALID`, `TP_VALIDITY_INVALID_X`, `_INVALID_Y`, `_INVALID_XY` | 일치 | 없음 |
| A7 | `TPCalibrateParam`은 원점과 축별 도트 크기이다 | NitroSDK `tp.h`: `struct NvTpData { s16 x0, y0, xDotSize, yDotSize; }` | 일치 | 없음 |

### B. BIOS SWI 목록

| # | 주장 | 공개 소스 | 판정 | 무엇을 바꿀 것인가 |
|---|---|---|---|---|
| B1 | 인터프리터의 SWI 번호 체계는 NDS의 것이다: 09h Div, 0Bh CpuSet, 0Ch CpuFastSet, 0Dh Sqrt, 0Eh GetCRC16, 0Fh IsDebugger, 10h BitUnPack, 11h LZ77, 14h RL, 16h/18h Diff 필터 [`port/interp/interp_bios.c` 헤더] | GBATEK, [BIOS Function Summary](https://problemkaputt.de/gbatek-bios-function-summary.htm) | 일치 | 없음. NDS 번호 체계가 GBA와 다르다는 헤더의 경고는 옳으며 유지할 가치가 있다 |
| B2 | 16h와 18h는 Diff 필터이고 17h는 NDS에 존재하지 않는다 | GBATEK, [BIOS Decompression Functions](https://problemkaputt.de/gbatek-bios-decompression-functions.htm): 16h는 `(GBA/NDS9/DSi9)`, 17h는 `(GBA)` 전용, 18h는 `(GBA/NDS9/DSi9)` | 일치 | 없음 — 포트가 17h를 생략한 것은 옳다 |
| B3 | `CpuFastSet`은 워드 수를 8의 배수로 올림한다 [`interp_bios.c` case 0x0c: `n2 = ((ctl & 0x1fffff) + 7) & ~7`] | GBATEK, [BIOS Memory Copy](https://problemkaputt.de/gbatek-bios-memory-copy.htm), "SWI 0Ch — CpuFastSet": *"On the GBA, the length should be a multiple of 8 words (32 bytes) (otherwise the GBA is forcefully rounding-up the length). On NDS/DSi, the length may be any number of words (4 bytes)."* | **불일치** | 수정안 **P4**: 정확히 `ctl & 0x1FFFFF` 워드만 복사하라. 올림은 GBA 동작이며 목적지 너머로 최대 일곱 워드를 쓴다 |
| B4 | `GetCRC16` 테이블은 레지스터 폭 누산기 위에서 `crc ^= tab[j] << (7-j)`로 쓰인다 | GBATEK, [BIOS Misc Functions](https://problemkaputt.de/gbatek-bios-misc-functions.htm), "SWI 0Eh — GetCRC16"; DeSmuME `src/bios.cpp` (`getCRC16`, 니블 테이블 형식) | 일치 | 없음. **이 감사는 하마터면 정반대를 발표할 뻔했다.** 마스킹되지 않은 32비트 누산기는 틀려 보인다. GBATEK의 의사 코드, 고전적인 CRC-16/ARC, 포트의 정확한 식 세 가지를 다시 구현하여 모두 실행해 본 결과, 시도한 모든 입력에서 포트는 CRC-16/ARC와 같았고 오히려 *마스킹된* 해석이 어긋났다. M1 |
| B5 | `GetCRC16`은 바이트 길이를 받는다 | GBATEK, 같은 절: r1은 2바이트 정렬이어야 하고 r2는 *"length in bytes, must be 2-byte aligned"*; DeSmuME는 `size = R[2] >> 1`을 계산하고 하프워드 단위로 반복한다 | **불일치**, 근소하게 | 포트는 `len` 바이트 전부를 순회한다; 하드웨어는 끝의 홀수 바이트를 버린다. 수정안 **P8**(한 줄). DeSmuME는 또한 마지막 하프워드를 R3로 반환하는데, 포트는 이를 모델링하지 않는다 |
| B6 | `CpuSet`의 제어 워드는 21비트 카운트, 비트 24 고정 소스, 비트 26 데이터 크기이다 | GBATEK, [BIOS Memory Copy](https://problemkaputt.de/gbatek-bios-memory-copy.htm), "SWI 0Bh — CpuSet" | 일치 | 없음 |
| B7 | `BitUnPack`의 정보 블록은 `u16 len; u8 srcWidth; u8 dstWidth; u32 offset`이며 비트 31이 제로 데이터 플래그이고, 오프셋은 0이 아닌 단위에는 항상, 0인 단위에는 플래그가 설정된 경우에만 더해진다 | GBATEK, [BIOS Decompression Functions](https://problemkaputt.de/gbatek-bios-decompression-functions.htm), "BitUnPack — SWI 10h" | 일치 | 없음 |
| B8 | `IsDebugger`가 0을 반환하는 것은 옳다 | GBATEK, [BIOS Misc Functions](https://problemkaputt.de/gbatek-bios-misc-functions.htm): 메인 RAM 4 MB(일반) 대 8 MB(디버그)를 보고한다 | 일치 | 없음 |
| B9 | 목록에 없는 SWI는 추측하지 않고 이름을 대며 실행을 멈춘다 | — | 일치 (스펙이 아니라 정책) | 포트가 구현하지 **않은** NDS9 SWI는 00h SoftReset, 12h `LZ77UnCompReadByCallbackWrite16bit`, 13h `HuffUnCompReadByCallback`, 15h `RLUnCompReadByCallbackWrite16bit`, 1Fh `CustomPost`이다. NitroSDK의 `MI_UncompressHuffman`은 SWI 13h이고 VRAM 안전 압축 해제기는 12h/15h이므로, 이들이 다음에 멈출 가능성이 큰 지점이다. 수정안 **P6**이 이를 선제한다 |

### C. DMA

| # | 주장 | 공개 소스 | 판정 | 무엇을 바꿀 것인가 |
|---|---|---|---|---|
| C1 | NDS9 DMA 워드 카운트는 21비트이며 `0 = 0x200000`이다 [`dma.c` `dma_raw`] | GBATEK, [DS DMA Transfers](https://problemkaputt.de/gbatek-ds-dma-transfers.htm): *"Word count of all channels is expanded to 21bits (max 1..1FFFFFh units, or 0=200000h units)"* | 일치 | 없음 |
| C2 | `DMAxCNT` 비트 21–22 목적지 스텝, 23–24 소스 스텝, 25 반복, 26 폭, **27–28 시작 타이밍**, 30 IRQ, 31 활성화 [`dma.c` `dma_raw` 위의 주석] | GBATEK, 같은 페이지: NDS9에서는 *"the gamepak bit (Bit 27) has been removed and is instead used to expand the mode setting to 3bits"* — 타이밍은 NDS9에서 **비트 27–29**이다 (NDS7에서는 비트 28–29) | **불일치** (주석만) | 수정안 **P5**: 주석을 27–29로 고치고 NDS9의 일곱 가지 모드를 나열하라. 코드는 이 필드를 완전히 무시하므로 동작은 바뀌지 않지만, 잘못된 주석은 다음 독자를 오도한다 — 그리고 D12가 바로 이 부류의 결함이다 |
| C3 | 시작 타이밍 7은 Geometry Command FIFO이다 | GBATEK, 같은 페이지: *"0 Start Immediately, 1 Start at V-Blank, 2 Start at H-Blank (paused during V-Blank), 3 Synchronize to start of display, 4 Main memory display, 5 DS Cartridge Slot, 6 GBA Cartridge Slot, 7 Geometry Command FIFO"* | 일치 | 없음 |
| C4 | GX-FIFO를 목적지로 하는 전송은 인식되어 FIFO 파서로 라우팅된다 [`dma.c:409`] | GBATEK, [DS 3D Geometry Commands](https://problemkaputt.de/gbatek-ds-3d-geometry-commands.htm): *"DMA starts when the FIFO becomes less than half full, the DMA does then write 112 words to the GXFIFO register (or less, if the remaining DMA transfer length gets zero)"* | 목적지에 대해서는 일치, 버스트에 대해서는 **미규정** | 포트는 112워드 버스트가 아니라 전송 전체를 한 번에 실행한다. 완료를 기다리는 호출자에게는 보이지 않으며, NitroSDK의 모든 GX 경로가 그렇게 한다. 전송 도중 GXSTAT를 읽는 코드에만 보인다. 언급하지 않은 채 두지 말고 의도된 차이로 기록하라 |
| C5 | FIFO 경로는 타이밍 필드가 아니라 목적지 주소로 감지된다 | GBATEK, 같음 | 일치, 그리고 더 견고함 | 없음 — 다만 그렇게 밝혀 두어라. 타이밍 필드는 스펙 자체의 선택자이므로 누군가 코드를 그것을 쓰도록 "고칠" 것이기 때문이다 |
| C6 | 폭은 하나의 루프로 합쳐지지 않는다; VRAM/OAM에 대한 바이트 쓰기는 불법이다 | GBATEK, [DS Memory Maps](https://problemkaputt.de/gbatek-ds-memory-maps.htm) (VRAM/OAM 16비트 버스) | 일치 | 없음 |
| C7 | 목적지 스텝 모드 3은 "증가 + 리로드"이다 [`dma.c` 주석] | GBATEK, 같은 DMA 페이지 | 이름은 일치; 포트는 3을 단순 증가로 취급하고 리로드하지 않는다 | 실효상 미규정 | 반복(비트 25)과 함께일 때만 의미가 있는데, 포트는 그것도 무시한다. 수정안 **P5**에 언급; 호출자는 발견되지 않음 |
| C8 | `MI_DmaCopy32`/`MI_DmaCopy16`/`MI_DmaFill32`는 DMA 계열의 안전한 대역이다 | — | **불일치** (잠재적) | `dma_raw`만 GX-FIFO 목적지를 검사한다. `0x04000400`으로의 `MI_DmaCopy32`는 목적지 포인터를 FIFO와 45개의 개별 명령 포트에 걸쳐 전진시켜 디스플레이 리스트를 조용히 뒤섞을 것이다. 수정안 **P3** |
| C9 | 작업을 동기적으로 수행하면 `MI_WaitDma`는 no-op이 되며 관측상 동일하다 | — | 일치 | 없음. `dma.c` 헤더의 논증은 타당하다: 모든 ROM 래퍼는 반환 전에 대기한다 |

### D. 나눗셈 및 제곱근 유닛

| # | 주장 | 공개 소스 | 판정 | 무엇을 바꿀 것인가 |
|---|---|---|---|---|
| D1 | `DIVCNT` 비트 0–1은 32/32, 64/32, 64/64를 선택한다 | GBATEK, [DS Maths](https://www.problemkaputt.de/gbatek-ds-maths.htm), "Division": 모드 0 *"32bit / 32bit = 32bit , 32bit ; 18 clks"*, 모드 1 *"64bit / 32bit"*, 모드 2 *"64bit / 64bit"* | 일치 | 없음 |
| D2 | 0으로 나누면 나머지 = 분자, 결과는 분자의 부호에 따라 ±1이다 | GBATEK, 같은 페이지, "Division Overflows": *"REMAIN=NUMER, RESULT=+/-1 (with sign opposite of NUMER)"* | 일치 | 없음 — 포트의 `num < 0 ? 1 : -1`은 뒤집힌 것처럼 보이지만 그렇지 않다: 스펙은 *반대* 부호라고 말한다 |
| D3 | `INT64_MIN / -1`은 `INT64_MIN`, 나머지 0을 준다 | GBATEK, 같음: *"RESULT=-MAX (instead +MAX)"* | 결과는 일치, 나머지는 **미규정** | 그대로 두라; 스펙이 나머지를 명시하지 않음을 기록하라 |
| D4 | `DIVCNT`를 읽으면 저장된 값을 `0x3fff`로 마스킹하여 반환한다 — 절대 busy가 아니다 [`interp_boot.c` `io_load`] | GBATEK, 같음: 비트 14는 **0 나눗셈 플래그**, 비트 15는 busy 플래그 | **불일치** | 마스크가 비트 15뿐 아니라 비트 14도 지우므로, DIV0 플래그를 검사하는 호출자는 항상 "0 나눗셈 없음"을 읽는다. 수정안 **P7**. GBATEK는 이 플래그가 *"only if the full 64bit DIV_DENOM value is zero, even in 32bit mode"* 설정된다고 덧붙이는데, 포트의 모드 0 경로(하위 워드만)도 이를 지켜야 한다 |
| D5 | `SQRTCNT` 비트 0은 64비트 매개변수를 선택한다; `SQRT_PARAM`은 `0x040002B8`에, `SQRT_RESULT`는 `0x040002B4`에 있다 | GBATEK, 같은 페이지, "Square Root" | 일치 | 없음 |
| D6 | 포트가 동기적이므로 busy 비트가 설정되지 않는 것은 안전하다 | GBATEK: 나눗셈은 18/34 클럭, 제곱근은 *"Execution time is 13 clks, in either Mode"* | 일치 | 없음. *"push all DIV/SQRT values … when using DIV/SQRT registers on interrupt level"*이라는 GBATEK의 경고는 이미 구조적으로 지켜진다: `CPContext`는 `OSContext`의 일부이다 [`wiki/engine/threads-and-interrupts.md`] |
| D7 | 결과 레지스터를 읽을 때 계산하는 것은 피연산자를 쓸 때 계산하는 것과 동등하다 | GBATEK: *"Division is started when writing to any of the DIVCNT/NUMER/DENOM registers"* | 실효상 일치 | NUMER를 쓰고 RESULT를 읽은 뒤 DENOM을 쓰는 호출자는 다를 것이다. 그런 호출자는 알려진 바 없다; 수정안이 아니라 가설로 추가하라 |

### E. DISPSTAT와 VCOUNT

| # | 주장 | 공개 소스 | 판정 | 무엇을 바꿀 것인가 |
|---|---|---|---|---|
| E1 | 프레임당 263 스캔라인 | GBATEK, [DS Video Stuff](http://problemkaputt.de/gbatek-ds-video-stuff.htm), "Display Timings": *"V-Timing: 192 lines visible, 71 lines blanking, 263 lines total (59.8261 Hz)"* | 일치 | 없음 |
| E2 | VBlank(DISPSTAT 비트 0)는 **192..262** 라인에서 설정된다 [`interp_boot.c` `dispstat_load`: `v >= 192`; `hardware-services.md` 4절; `threads-and-interrupts.md`] | GBATEK, 같은 절: *"the VBlank flag isn't set in the last line (ie. only in lines 192..261, but not in line 262)"* | **불일치** | 수정안 **P2**. 코드 한 줄, 문서 세 개 |
| E3 | VCOUNT는 9비트, 0..262이며 DISPSTAT의 비교값은 분할되어 있다 | GBATEK, 같음: *"LY = VCOUNT Bit 0..8, and LYC=DISPSTAT Bit8..15,7"* | 일치 | 없음 — 포트의 `0xfff8` 마스크는 비트 3..15를 올바르게 보존하며, 여기에는 DISPSTAT 비트 7에 있는 LYC 비트 8이 포함된다 |
| E4 | V-카운터 일치 플래그는 DISPSTAT 비트 2이다 | GBATEK, [LCD I/O Interrupts and Status](http://problemkaputt.de/gbatek-lcd-i-o-interrupts-and-status.htm): *"Bit 2: V-Counter flag (Read only) (1=Match) (set in selected line)"* | **불일치** | 포트는 비트 2를 절대 설정하지 않는다. V-카운트 일치를 폴링하는 루프는 영원히 돌며, 프레임 경계가 랩에서 발화하므로 *프레임이 진행되는 동안* 돌게 된다 — 이 포트가 가진 최악의 진단 형태이다. 수정안 **P2**가 이를 다룬다 |
| E5 | HBlank(비트 1)는 클리어된 채로 둔다 | GBATEK, 같음: *"Bit 1: H-Blank flag (Read only) (1=HBlank) (toggled in all lines)"* | **불일치**, 의도적 | 같은 수정안; 최소한 DISPSTAT 읽기 뒤에 라인 변화 없이 다시 DISPSTAT 읽기가 이어질 경우, 조용히 멈추지 말고 서비스가 *스스로 이름을 대야* 한다 |
| E6 | VCOUNT 폴링 루프는 하드웨어의 순서대로 한 합성 프레임 안에 풀린다 | — | 일치 | 없음. 읽기당 한 라인 모델은 `func_0200149c`에 대한 타당한 답이다 |
| E7 | 모든 I/O 읽기는 합성 훅을 거친다 | `port/interp/interp_cpu.c:59-82` | **불일치** (잠재적) | `ld8`은 `io_word`를 호출하지 않는다. `0x04000006`(VCOUNT 하위)이나 나눗셈 결과 레지스터의 바이트 읽기는 훅을 우회하여 오래된 페이지 메모리를 반환한다. 수정안 **P9** |

### F. 2D 색상 효과와 아핀 배경

| # | 주장 | 공개 소스 | 판정 | 무엇을 바꿀 것인가 |
|---|---|---|---|---|
| F1 | 알파 블렌드는 `I = min(31, I1*EVA/16 + I2*EVB/16)`이며 16을 넘는 EVA/EVB는 16으로 클램프된다 | GBATEK, [LCD I/O Color Special Effects](https://problemkaputt.de/gbatek-lcd-i-o-color-special-effects.htm): *"I = MIN ( 31, I1st\*EVA + I2nd\*EVB )"*, 계수는 *"0..16 = 0/16..16/16, 17..31=16/16"* | 규칙은 일치, 정의역은 **불일치** | 포트는 8비트로 확장된 채널을 블렌드하고 255에서 클램프한다 [`nds2d.c` `chan_mix`]; 하드웨어는 **5비트** 강도를 블렌드하고 31에서 클램프한다. 수정안 **P10** |
| F2 | 밝기 증가는 `I + (31-I)*EVY/16`, 감소는 `I - I*EVY/16`이다 | GBATEK, 같은 페이지 | 규칙은 일치, 같은 정의역 불일치 | 수정안 **P10** |
| F3 | 반투명 OBJ(attr0 모드 1)는 항상 첫 번째 타깃이며 항상 알파 블렌딩을 사용한다 | GBATEK, 같은 페이지: *"OBJs that are defined as 'Semi-Transparent' in OAM memory are always selected as 1st Target (regardless of BLDCNT Bit 4), and are always using Alpha Blending mode (regardless of BLDCNT Bit 6-7)"* | 전반부는 일치, 후반부는 **불일치** | `apply_color_effects`의 세 번째 분기는 아래 레이어가 두 번째 타깃이 아니고 OBJ가 우연히 BLDCNT 첫 번째 타깃일 때 반투명 OBJ에 *밝기* 효과를 적용할 수 있다. GBATEK의 "regardless of Bit 6-7"은 그래서는 안 된다고 말한다. 에뮬레이터들은 여기서 서로 다르다. 수정안 **P11**, 낮은 우선순위 |
| F4 | 블렌드는 보이는 픽셀과 바로 아래의 픽셀을 소비한다 | GBATEK, 같은 페이지 (첫 번째/두 번째 타깃 쌍) | 일치 | 없음. `nds2d.c`의 2단 깊이 소유자 레코드는 올바른 형태이다 |
| F5 | 백드롭은 알파의 첫 번째 타깃으로서 비활성이다 | — | 구성상 일치 | 없음 |
| F6 | 아핀 BG 행렬 항목 PA..PD는 부호 있는 8.8이다 | GBATEK, [LCD I/O BG Rotation/Scaling](https://problemkaputt.de/gbatek-lcd-i-o-bg-rotation-scaling.htm): *"Bit 0-7 Fractional portion (8 bits); Bit 8-14 Integer portion (7 bits); Bit 15 Sign"* | 일치 | 없음 |
| F7 | 기준점은 20.8이며 부호는 비트 27에 있다 [`nds2d.c:770`; `wiki/engine/graphics-pipeline.md`] | GBATEK, 같은 페이지: *"Bit 0-7 Fractional (8); Bit 8-26 Integer portion (19 bits); Bit 27 Sign; Bit 28-31 Not used"* | 일치, 표현은 제외 | 이 필드는 **19.8 더하기 부호**, 즉 부호 있는 28비트이다 — `sext(v, 28)`이 하는 일이 정확히 그것이다. 그래픽스 페이지의 "20.8" 표현을 "부호 있는 28비트, 소수부 8비트"로 고쳐라 |
| F8 | 스캔라인마다 레이어는 `ref + PB*y`(행)와 `+PA*x`(열)에서 샘플링된다 [`draw_affine_bg`] | GBATEK, 같은 페이지: *"The above reference points are automatically copied to internal registers during each vblank … The internal registers are then incremented by dmx and dmy after each scanline"* | 일치 | 없음. 게임이 프레임 중간에 BGxX를 쓰지 않는 한, `x0 + pb*y`는 대수적으로 그 누적과 정확히 같다 |
| F9 | 프레임 중간의 BGxX 쓰기는 모델링되지 않는다 | GBATEK, 같은 페이지: *"Writing to a reference point register by software outside of the Vblank period does immediately copy the new value to the corresponding internal register … the new value specifies the origin of the &lt;current&gt; scanline"* | 일치 (알려진 한계로 명시됨) | 계측 수단을 명시한 가설로 유지하라: H2 참조 |
| F10 | 아핀 레이어는 항상 8bpp에 바이트 화면 항목, 128..1024 정사각형이며 BGnCNT 비트 13으로 랩한다 | GBATEK, 같은 페이지 및 [LCD I/O BG Control](https://problemkaputt.de/gbatek-lcd-i-o-bg-control.htm) | 일치 | 없음 |
| F11 | BG 모드→레이어 종류 표 (모드 1 → BG3 아핀, 모드 2 → BG2/BG3 아핀, 모드 4 → BG2 아핀 BG3 확장, 모드 6 → BG0 3D + BG2 대형 비트맵) | GBATEK, [DS Video BG Modes](https://problemkaputt.de/gbatek-ds-video-bg-modes.htm) | 일치 | 없음 — `bg_kind`는 행마다 정확하다 |

### G. 지오메트리 엔진

| # | 주장 | 공개 소스 | 판정 | 무엇을 바꿀 것인가 |
|---|---|---|---|---|
| G1 | GXSTAT 비트 8–12는 위치/벡터 행렬 스택 레벨이고 비트 15는 스택 오류이다 | GBATEK, [DS 3D Status](https://problemkaputt.de/gbatek-ds-3d-status.htm): *"8-12 Position & Vector Matrix Stack Level (0..31) (lower 5bit of 6bit value)"*, *"15 Matrix Stack Overflow/Underflow Error"* | 일치 | 없음 |
| G2 | 비트 13은 투영 스택 레벨이다 | 같은 페이지 (가져온 표에는 빠져 있음); ROM 자신의 `G3X_GetMtxStackLevelPJ`가 `0x2000`을 마스킹한다 [`src/matched/G3X_GetMtxStackLevelPJ.c`] | 소스에서는 미규정, ROM으로 확정됨 | 없음 |
| G3 | 비트 25는 "명령 FIFO 비어 있음"이다 [`nds3d.c:217` 주석; `gxstat_update`가 비트 25를 설정] | GBATEK, 같은 페이지: *"25 Command FIFO Less Than Half Full"*, *"26 Command FIFO Empty"* | **불일치** | 수정안 **P12**: 포트는 비트 25를 설정하고 비트 26은 절대 설정하지 않으므로, 비어 있기를 기다리는 루프는 영원히 "비어 있지 않음"을 읽고 반쯤 비기를 기다리는 루프는 통과한다. 둘 다 설정하고 주석을 고쳐라 |
| G4 | 비트 27은 지오메트리 엔진 busy이며 동기 엔진에서 0은 정직한 값이다 | GBATEK, 같은 페이지: *"27 Geometry Engine Busy"* | 일치 | 없음 |
| G5 | `gxstat_update`는 자신이 소유하지 않는 GXSTAT 부분을 보존한다 | GBATEK, 같은 페이지: *"30-31 Command FIFO IRQ (0=Never, 1=Less than half full, 2=Empty, 3=Reserved)"*; `NNS_G3dInit`가 그 필드를 쓴다 [`src/matched/NNS_G3dInit.c`] | **불일치** | `gxstat_update`는 비트 15만 남기고 워드를 다시 조립하므로, 모든 행렬 명령이 ROM이 초기화 시 설치한 FIFO-IRQ 모드와 비트 0을 지운다. 수정안 **P12** |
| G6 | GXSTAT 비트 0은 테스트 busy 플래그이고 비트 1은 박스 테스트 결과이다 | GBATEK, 같은 페이지: *"0 BoxTest,PositionTest,VectorTest Busy"* | 비트 0은 일치; 비트 1은 가져온 표에 없으나 표준적인 박스 테스트 결과이다 | 일치 / 미규정 | 없음; "보임"으로 답하는 것이 안전한 방향이며 파일 안에 이미 논증되어 있다 |
| G7 | POS_TEST와 VEC_TEST는 스텁이다 | GBATEK, [DS 3D Tests](https://problemkaputt.de/gbatek-ds-3d-tests.htm) (`POS_RESULT` 4000620h, `VEC_RESULT` 4000630h) | **불일치**, 알려짐 | 포트는 busy 비트를 지우지만 결과 레지스터를 쓰지 않으므로 호출자는 오래된 워드를 읽는다. 이미 `graphics-pipeline.md`의 가설이다; 그곳에 유지하고, 그 페이지에 명시된 카운팅 계측 수단을 추가하라 |
| G8 | `0x04000400`의 FIFO는 패킹된 명령 리스트를 받고 `0x04000440`+는 개별 포트이다 | GBATEK, [DS 3D Geometry Commands](https://problemkaputt.de/gbatek-ds-3d-geometry-commands.htm): *"command1,2,3,4 packed into one 32bit value"*; 포트에 대해서는 *"For a command with N parameters: issue N writes … For a command without parameters: issue one dummy-write"* | 일치 | 없음 |

### H. PXI FIFO 프로토콜

| # | 주장 | 공개 소스 | 판정 | 무엇을 바꿀 것인가 |
|---|---|---|---|---|
| H1 | IPC FIFO는 각 방향 16워드 깊이이다 | GBATEK, [DS Inter Process Communication (IPC)](https://problemkaputt.de/gbatek-ds-inter-process-communication-ipc.htm): *"max 16 words; 64bytes"* | 일치 | 없음; 포트의 16슬롯 응답 큐는 우연히 일치하는 것이며, 그렇게 밝혀 두어야 한다 |
| H2 | 송신자는 FIFO가 가득 찬 동안 재시도한다 (`RtcSendPxiCommand`, `SND_FlushCommand`) | GBATEK, 같음: IPCFIFOCNT *"Bit 1 (R) Send Fifo Full Status"*, *"Bit 14 (R/W) Error, Read Empty/Send Full"* | 일치 | 포트는 IPCFIFOCNT를 전혀 에뮬레이트하지 않으므로 "가득 참"은 일반 메모리에서 0으로 읽히고 재시도 루프는 항상 첫 번째에 빠져나온다. 절대 차지 않는 큐에 대해서는 이것이 올바른 답이다; 조용히 두지 말고 기록하라 |
| H3 | 터치 응답 워드는 `nitro/spi/common/pm_common.h`에 따라 `START(1<<25) | END(1<<24) | 0x8000 | (command << 8)`이다 [`pxisend.c:8-22`] | NitroSDK, [`include/nitro/spi/common/pm_common.h`](https://github.com/ntrtwl/NitroSDK/tree/main/include/nitro/spi/common)가 공개되어 있어 확정할 수 있다; GBATEK는 SDK의 소프트웨어 프로토콜을 기술하지 않는다 | **미규정** — 검증 필요 | 비트 25와 24는 NitroSDK의 PXI 계층이 `PXI_SendWordByFifo`용 자체 오류 및 태그 필드를 두는 자리이다. 포트는 수신 콜백을 직접 호출하므로 마스킹이 일어나지 않지만, 상수는 바꿔 말하지 말고 공개 헤더에서 읽어 이름으로 인용해야 한다. 수정안 **P13** |
| H4 | 태그 7은 한 워드를 실어 나른다: 사운드 명령 연결 리스트의 주소이며, ARM7이 이를 순회하고 `finishCommandTag`를 증가시킨다 [`pxisend.c` `snd_arm7`; `wiki/systems/audio.md`] | NitroSDK, 같은 미러의 `include/nitro/snd`; 명령 id 29 = `SHARED_WORK` | ROM 자신의 매칭된 소스와 일치; GBATEK에는 없음 | 일치 (S 등급) | 매칭된 소스만이 아니라 명령 id 열거형에 대해 SDK 헤더를 인용하라 |
| H5 | 태그 11은 카드이며, `CARD_REQ_INIT`(0) 뒤에 명령 블록을 가리키는 두 번째 워드가 따른다 | NitroSDK `include/nitro/card` | 매칭된 코드와 일치; GBATEK에는 없음 | 일치 | 같음: SDK 헤더를 명시하라 |
| H6 | 카드는 한 프레임 늦게 응답해야 게시 직후의 폴링이 BUSY를 본다 | — | 일치 (동작적, CARD40으로 확립됨) | 없음. 이는 포트가 가진 가장 강력한 타이밍 규칙이며 어렵게 얻어낸 것이다 |
| H7 | 태그 번호: 4 NVRAM/사용자 설정, 5 RTC, 6 터치, 7 사운드, 8 PM, 10 WM, 11과 14 카드 | NitroSDK `include/nitro/pxi/common/fifo.h` (`PXI_FIFO_TAG_*` 열거형)가 같은 미러에 공개되어 있다 | **미규정** — 검증 가능 | 열거형을 읽고 인용하라; 저장소의 태그 표는 현재 E 등급(관측)이며 S가 될 수 있다 |

---

## 2. 구체적인 포트 수정안, 우선순위 순

각 항목은 파일, 함수, 스펙이 말하는 것, 코드가 하는 것, 검증 방법을 명시한다.

### P1 — 스타일러스의 1–2프레임 지연을 모델링한다 (`port/shim/input/touch.c`, `func_020e9314`)

**스펙.** melonDS는 자체 지연을 더하지 않으므로([`src/SPI.cpp`](https://github.com/melonDS-emu/melonDS/blob/master/src/SPI.cpp), TSC `SetTouchCoords`), 오라클에서 측정된 1–2프레임 랙은 ROM이 만들어 낸다: ARM7이 프레임당 `frequence`개의 샘플로 `gAutoData`를 비동기적으로 채우고([`tp.h`](https://github.com/ntrtwl/NitroSDK/blob/main/include/nitro/spi/ARM9/tp.h)), `TPi_TpCallback`이 PXI 인터럽트에서 인덱스를 전진시키며, `func_020e9314`는 가장 새로운 것 또는 하나 더 오래된 것에서 끝나는 **연속된 세 개의 정상 샘플**을 찾았을 때만 게시한다. 따라서 프레임 N에서 시작된 접촉은 프레임 N 후반이 되기 전에는 세 개의 정상 샘플을 만들 수 없으며, 후행 윈도우 분기는 해제 후 한 프레임 동안 계속 그것을 재게시한다.

**코드.** `touch_scheduled`는 정확히 `[AT, AT+FOR)` 구간의 프레임에 대해 "down"을 반환하고 `func_020e9314`는 그 프레임에 게시한다.

**수정.** `func_020e9314` 안에 최근 세 프레임의 접촉 상태를 담는 작은 시프트 레지스터를 둔다. 셋 모두 down일 때만 `touch = 1`을 게시하고(시작이 두 프레임 지연), 가장 새로운 샘플이 up으로 바뀐 뒤 한 프레임 동안 `touch = 1`을 유지한다(해제가 한 프레임 지연). 기존의 모든 측정이 비교 가능하도록 한 주기 동안은 기본값 **off**인 `ACWW_TOUCH_LATENCY=0|1` 뒤에서 수행한 뒤, 기본값을 뒤집는다.

**검증.** 픽스처는 이미 존재한다. ORACLE42가 24,700으로 옮기기 전에 어긋났던 24,600 레시피를 지연을 모델링한 채 다시 실행하고, 25,500 프레임에서 `scratchpad/oracle/tap-fullpad`와 비교한다. 성공은 포트가 원본과 정확히 같은 방식으로 마을 이름 확정에 실패하는 것이다. 이는 `wiki/systems/input-and-touch.md` 끝의 열린 가설이며 이 수정안이 그 실험이다.

### P2 — DISPSTAT의 VBlank 라인 범위, V-카운트 일치, HBlank (`port/interp/interp_boot.c`, `dispstat_load`)

**스펙.** GBATEK, [DS Video Stuff](http://problemkaputt.de/gbatek-ds-video-stuff.htm): *"the VBlank flag isn't set in the last line (ie. only in lines 192..261, but not in line 262)"*. [LCD I/O Interrupts and Status](http://problemkaputt.de/gbatek-lcd-i-o-interrupts-and-status.htm): 비트 2는 V-카운터 일치 플래그로, VCOUNT가 DISPSTAT 비트 8–15와 7의 비교값과 같을 때 설정된다; 비트 1은 HBlank 플래그이며 *"toggled in all lines"*이다.

**코드.** `return ((v >= 192u ? 1u : 0u) | (page & 0xfff8u)) | (v << 16);` — VBlank는 192..262, 비트 1은 항상 0, 비트 2는 항상 0.

**수정.** 한 식 안에 세 가지 변경: 비트 0에 대해 `v >= 192 && v <= 261`; `v == (((stat >> 8) & 0xFF) | ((stat >> 7) & 1) << 8)`일 때 비트 2 설정; 그리고 HBlank는 의도적으로 결정한다 — 읽기마다 번갈아 비트 1을 설정하고 그렇게 밝히거나, 클리어된 채 두고 진행 없이 263회 넘게 반복된 DISPSTAT 읽기를 이름 대어 알리는 카운터를 추가한다.

**검증.** 실행이 아니라 호스트 측 단위 테스트: 알려진 비교값을 페이지에 써 둔 픽스처에서 `dispstat_load`를 263번 호출하고 정확한 비트 0/비트 2 시퀀스를 단언하며, `acww_frame()` 호출 한 번을 더한다. `port/render/selftest.c`가 이 저장소에서 자기 검사 픽스처의 기존 패턴이다.

### P3 — `MI_DmaCopy32`/`MI_DmaCopy16`/`MI_DmaFill32`는 GX FIFO 목적지를 인식해야 한다 (`port/shim/os/dma.c`)

**스펙.** GBATEK, [DS 3D Geometry Commands](https://problemkaputt.de/gbatek-ds-3d-geometry-commands.htm): `0x04000400`은 하나의 포트이며, 이곳으로의 전송은 목적지를 전진시키지 않는다. `port/shim/os/mi.c`는 이미 FIFO를 목적지로 하는 `MIi_CpuCopy32`를 `acww_gx_fifo_run`으로 라우팅한다([`docs/kb/hybrid/hardware-services.md`](../../docs/kb/hybrid/hardware-services.md) 5절).

**코드.** `dma_raw`만 `dest - 0x04000400u < 0x40u`를 검사한다. 세 래퍼 진입점은 `*d++`로 복사한다.

**수정.** 같은 세 줄짜리 검사를 세 래퍼로 끌어올리고 `acww_gx_fifo_run`으로 라우팅한다. 호출자가 존재하지 *않을* 것으로 기대된다면, 조용히 순회하지 말고 이름을 대는 거부로 만든다 — 그 파일 자신이 밝힌 정책이다.

**검증.** `0x04000400`을 목적지로 하는 두 워드짜리 패킹된 디스플레이 리스트로 `MI_DmaCopy32`를 호출하고 `acww_gx_words()`가 2만큼 전진했으며 `0x04000404`.. 의 명령 포트에는 쓰이지 않았음을 단언하는 픽스처.

### P4 — `CpuFastSet`은 NDS에서 올림하지 않아야 한다 (`port/interp/interp_bios.c`, case `0x0c`)

**스펙.** GBATEK, [BIOS Memory Copy](https://problemkaputt.de/gbatek-bios-memory-copy.htm): *"On the GBA, the length should be a multiple of 8 words … On NDS/DSi, the length may be any number of words (4 bytes). … After processing all 32-byte-blocks, the NDS/DSi additonally processes the remaining words as 4-byte blocks."*

**코드.** `n2 = ((ctl & 0x1fffffu) + 7u) & ~7u;` — 8의 배수가 아닌 모든 호출에서 목적지 너머로 최대 일곱 워드를 덮어쓴다.

**수정.** `n2 = ctl & 0x1fffffu;`. 한 줄.

**검증.** 픽스처: 16워드 버퍼를 센티널로 채우고, 그 안에 9워드를 `CpuFastSet`한 뒤, 워드 9..15가 여전히 센티널을 담고 있음을 단언한다. 목록에서 가장 저렴한 수정이며 이미 무언가를 손상시키고 있을 가능성이 가장 큰 것이다.

### P5 — DMA 제어 워드 주석을 고친다 (`port/shim/os/dma.c`, `dma_raw` 위)

**스펙.** GBATEK, [DS DMA Transfers](https://problemkaputt.de/gbatek-ds-dma-transfers.htm): NDS9에서는 *"the gamepak bit (Bit 27) has been removed and is instead used to expand the mode setting to 3bits"* — 시작 타이밍은 비트 **27–29**이며, 모드 7이 Geometry Command FIFO, 모드 4가 메인 메모리 디스플레이이다.

**코드.** 주석은 "27..28 start timing"이라고 말한다. 코드는 이 필드를 무시한다.

**수정.** 주석을 고치고, 일곱 가지 모드를 나열하며, 포트가 대신 목적지 주소로 FIFO 경로를 선택한다고 명시한다 — 다음 독자가 3비트 필드의 두 비트를 쓰도록 "고치지" 않도록. 또한 반복(비트 25)과 목적지 모드 3의 리로드는 무시되며 아무것도 그것을 필요로 하지 않았다고 밝힌다.

**검증.** 문서만; `tools/check_docs.py`.

### P6 — 빠진 압축 해제 SWI를 선제한다 (`port/interp/interp_bios.c`)

**스펙.** GBATEK, [BIOS Decompression Functions](https://problemkaputt.de/gbatek-bios-decompression-functions.htm): NDS에서 12h는 `LZ77UnCompReadByCallbackWrite16bit`, 13h는 `HuffUnCompReadByCallback`, 15h는 `RLUnCompReadByCallbackWrite16bit`이다.

**코드.** "일반" 형식인 11h와 14h만 존재한다. NitroSDK의 `MI_UncompressHuffman`은 13h이며 VRAM 안전 언패커는 12h/15h이다.

**수정.** 두 가지 선택지가 있으며 선택을 기록해야 한다: 13h(허프만, 4비트 및 8비트)를 구현하고 12h/15h를 16비트 쓰기를 하는 일반 형식의 쌍둥이로 취급하거나, **또는** 구현하지 않은 채 두고 정지 메시지가 SWI 번호를 명시하는지 확인한다. 실제로 하나가 발화하기 전까지는 두 번째를 선호한다 — 현재 동작은 이미 이름을 대며 멈추는데 그것이 포트의 명시된 정책이며, 콜백 ABI를 추측하는 것은 이름 있는 정지보다 나쁘다.

**검증.** `ACWW_INTERP_SWI`는 이미 모델링되지 않은 SWI의 이름을 댄다. 긴 마을 실행의 로그에서 이를 grep한다; 13h가 한 번도 나타나지 않으면 부정적 결과로 닫고 그렇게 밝힌다.

### P7 — DIV0 플래그 (`port/interp/interp_boot.c`, `io_load`)

**스펙.** GBATEK, [DS Maths](https://www.problemkaputt.de/gbatek-ds-maths.htm): DIVCNT 비트 14는 0 나눗셈 플래그이며, *"set only if the full 64bit DIV_DENOM value is zero, even in 32bit mode"*이다.

**코드.** `*w = io_page_word(a) & 0x3fffu;`는 busy 비트와 함께 비트 14를 마스킹해 버린다.

**수정.** 전체 64비트 분모로부터 플래그를 계산하여 반환되는 CNT에 OR한다; 비트 15는 클리어된 채 둔다.

**검증.** 픽스처: DIVCNT 모드 0, NUMER = 5, DENOM = 0을 쓰고 DIVCNT를 읽어 비트 14를 단언한다; 모드 0에서 하위 워드가 0이고 상위 분모 워드가 0이 아닌 값을 쓰고 비트 14가 **클리어**임을 단언한다.

### P8 — `GetCRC16` 길이 (`port/interp/interp_bios.c`, case `0x0e`)

**스펙.** GBATEK, [BIOS Misc Functions](https://problemkaputt.de/gbatek-bios-misc-functions.htm): 주소는 2바이트 정렬이어야 하고 길이는 *"in bytes, must be 2-byte aligned"*이다; DeSmuME의 `getCRC16`은 `size = R[2] >> 1`을 계산하고 하프워드 단위로 반복하므로 끝의 홀수 바이트는 버려진다.

**코드.** 모든 바이트에 대한 `for (i = 0; i < len; i++)`.

**수정.** 루프 전에 `len &= ~1u;`. 선택적으로 `r[3]`을 마지막 하프워드로 설정한다 — DeSmuME는 이를 실제 BIOS 부작용으로 모델링한다.

**검증.** 픽스처: 5바이트 버퍼의 CRC는 그 앞 4바이트의 CRC와 같아야 한다.

### P9 — I/O 페이지의 바이트 읽기가 합성 훅을 우회한다 (`port/interp/interp_cpu.c`, `ld8`)

**스펙.** 스펙 문제가 아니라 내부 일관성 문제이다. `ld32`와 `ld16`은 `io_word`를 호출한다; `ld8`은 그렇지 않다.

**코드.** `static u32_ ld8(u32_ a) { return *(volatile unsigned char *)a; }`.

**수정.** `ld16`이 하프워드를 고르는 것과 똑같이, `ld8`을 `io_word`를 거쳐 바이트를 고르도록 라우팅한다. 저렴하며, 보이지 않았을 "루프가 절대 풀리지 않는다" 부류 전체를 제거한다.

**검증.** 픽스처: 인터프리터를 통해 `0x04000006`에서 `ldrb`를 두 번 수행하고 두 번째 읽기가 1 더 큼을 단언한다.

### P10 — 색상 효과를 5비트 정의역에서 적용한다 (`port/render/nds2d.c`, `chan_mix` 및 `brighten`)

**스펙.** GBATEK, [LCD I/O Color Special Effects](https://problemkaputt.de/gbatek-lcd-i-o-color-special-effects.htm): *"I = MIN ( 31, I1st\*EVA + I2nd\*EVB )"*, *"I = I1st + (31-I1st)\*EVY"*, *"I = I1st - (I1st)\*EVY"*, 계수는 16분의 1 단위.

**코드.** 둘 다 8비트로 확장된 채널에서 동작하며 255에서 클램프한다.

**수정.** BGR555→BGRA 확장 전에 5비트 채널 값으로 산술을 수행하거나, 동등하게 `>>3`, 블렌드, 31에서 클램프, `<<3`. 눈에 보이는 차이는 채널당 기껏해야 몇 레벨이지만 오라클에 대한 체계적 편향이며 제거하는 데 비용이 들지 않는다.

**검증.** `port/render/selftest.c`에는 이미 블렌드 픽스처가 있다(SKY40이 통과를 기록한다). 손으로 계산한 5비트 기댓값을 가진 세 가지 경우를 추가한다: 알려진 두 BGR555 색상에 대한 EVA=9/EVB=7, EVY=5 증가, EVY=5 감소. 그런 다음 `tap-D62`의 샘플링된 아홉 프레임에서 `scratchpad/oracle/tap-24700`에 대한 ncc 비교를 다시 실행하고 평균이 떨어지지 않는지 확인한다.

### P11 — 반투명 OBJ는 절대 밝기 경로를 타지 않아야 한다 (`port/render/nds2d.c`, `apply_color_effects`)

**스펙.** GBATEK, 같은 페이지: 반투명 OBJ는 *"are always using Alpha Blending mode (regardless of BLDCNT Bit 6-7)"*이다.

**코드.** `own_semi[i]`가 설정되었지만 아래 레이어가 두 번째 타깃이 아닐 때, OBJ가 BLDCNT 첫 번째 타깃이면 픽셀이 밝기 분기로 떨어질 수 있다.

**수정.** 밝기 분기를 `!own_semi[i]`로 가드한다. 낮은 우선순위이며 먼저 측정할 가치가 있다: 에뮬레이터들은 여기서 GBATEK의 문자 그대로의 문장과 다르며, 포트의 카운터는 이미 두 모집단을 분리한다(`px_obj_semi` 대 `px_bright`).

**검증.** 먼저 마을 실행에서 `px_obj_semi`와 `px_bright`를 읽는다. 반투명 픽셀에서 `px_bright`가 0이면 이 변경은 무의미하므로 하지 않아야 한다.

### P12 — GXSTAT: empty 비트를 설정하고 FIFO-IRQ 모드를 지우지 않는다 (`port/render/nds3d.c`, `gxstat_update`)

**스펙.** GBATEK, [DS 3D Status](https://problemkaputt.de/gbatek-ds-3d-status.htm): *"25 Command FIFO Less Than Half Full"*, *"26 Command FIFO Empty"*, *"30-31 Command FIFO IRQ"*. `NNS_G3dInit`는 기동 시 비트 30–31을 쓴다 [`src/matched/NNS_G3dInit.c`].

**코드.** `v |= 1u << 25;`뿐이며, `wr32(GX_GXSTAT, v | (old & 0x8000u))`는 스택 오류 비트 외에는 아무것도 유지하지 않는다.

**수정.** 비트 25와 함께 비트 26도 설정하고(동기 엔진은 비어 있으면서 동시에 반보다 덜 찬 상태이다), 비트 16–24는 0으로 두며, 비트 15에 더해 `old & 0xC0000001u` — IRQ 모드와 테스트 명령이 소유하는 테스트 busy 비트 — 를 보존한다. 217번 줄의 주석을 고친다.

**검증.** 픽스처: GXSTAT에 `0x40000000`을 쓰고, `acww_gx_port`를 통해 행렬 명령을 제출한 뒤, GXSTAT를 다시 읽어 비트 30–31이 살아남았고 비트 26이 설정되었음을 단언한다.

### P13 — PXI 프로토콜 상수를 바꿔 말하지 말고 인용한다 (`port/shim/os/pxisend.c`)

**스펙.** NitroSDK 소스는 공개되어 있다: [`include/nitro/pxi/common/fifo.h`](https://github.com/ntrtwl/NitroSDK/tree/main/include/nitro/pxi/common)는 `PXI_FIFO_TAG_*` 열거형과 `PXI_SendWordByFifo`가 사용하는 태그/오류/데이터 필드 배치를 담고 있다; [`include/nitro/spi/common/pm_common.h`](https://github.com/ntrtwl/NitroSDK/tree/main/include/nitro/spi/common)는 터치 응답을 구성하는 START/END 비트를 담고 있다.

**코드.** `pxisend.c:8-22`는 기억에 의존해 `pm_common.h`를 언급하고 `1<<25`, `1<<24`, `0x8000`을 하드코딩한다. `hardware-services.md`의 태그 표는 E 등급 — 읽은 것이 아니라 관측된 것이다.

**수정.** 두 헤더를 읽고, 주석에 상수 이름을 명시하며, 헤더를 출처로 삼아 태그 표를 E에서 S로 승격한다. PXI 데이터 필드가 비트 25보다 좁은 것으로 드러나면, 터치 응답 워드는 포트가 콜백을 직접 호출하기 때문에 현재로서는 문제를 일으키지 못할 뿐인 방식으로 틀린 것이다.

**검증.** 문서와 주석; 그런 다음 한 번 실행하여 `acww pxi:` 줄이 하나도 바뀌지 않았음을 확인한다.

---

## 3. `func_XXXXXXXX`에 이름을 붙여 줄 수 있는 공개 참고 자료

요청대로 URL만 나열한다; 이 중 어느 것도 저장소에 복사되지 않았다.

**Animal Crossing: Wild World의 공개 디컴파일은 존재하지 않는다.** <https://decomp.dev>,
<https://decomp.wiki/platforms/nintendo-ds>, <https://decomp.me>에 없다.
시도에 대한 유일한 공개 논의는
<https://gbatemp.net/threads/need-a-bit-of-guidance-trying-to-decomp-acww.673305/>이다.
ACWW 모딩 프로젝트는 존재하지만 코드 심볼은 담고 있지 않다: <https://github.com/TheGag96/acww-hax>,
<https://github.com/TheGag96/nitromods>, <https://github.com/Universal-Team/WildEdit>,
<https://github.com/MikeFritzDevelops/ACWW-Archipelago>.
다른 플랫폼의 Animal Crossing 디컴파일은 <https://github.com/ACreTeam/ac-decomp>
(GameCube), <https://github.com/zeldaret/af> (N64), <https://github.com/ACreTeam/afe-decomp>이다.

**완전한 NitroSDK 및 NitroSystem 소스 트리가 공개되어 있으며**, 이 저장소가 아직 `func_XXXXXXXX`라고
부르는 SDK 계층 함수에 이름을 붙이는 데 있어 이 감사에서 가장 가치 있는 발견이다:

- <https://github.com/ntrtwl/NitroSDK> — `include/nitro/` (os, fs, card, mi, pxi, spi, gx, fx,
  rtc, snd, std, wm)와 소스. 이 감사 중에 실제로 확인함: `include/nitro/spi/ARM9/tp.h`가
  터치 페이지가 기술하는 TP API 전체를 선언한다.
- <https://github.com/ntrtwl/NitroSystem> — `include/nnsys/` (fnd, g2d, g3d, gfd, snd):
  `NNS_G2d*`, `NNS_G3d*`, `NNS_Snd*` 이름들.
- <https://github.com/ntrtwl/NitroWiFi>, <https://github.com/ntrtwl/NitroDWC> — `ov065`와
  DWC 계층.
- <https://github.com/pret/pokediamond>, <https://github.com/pret/pokeheartgold>,
  <https://github.com/pret/pokeplatinum> — DS 디컴파일 안에 있는 매칭된 NitroSDK/NNS 소스.
- <https://github.com/radicalten/mkdsdecomp> — 생성된 심볼 및 타입 헤더와 함께 SDK 라이브러리의
  재구현인 `libntr`을 제공한다.
- <https://github.com/PikalaxALT/ndsbios> — ARM7 및 ARM9 BIOS의 디스어셈블리; 위에서 인용한
  SWI 벡터 테이블의 기록 출처.
- <https://github.com/AetiasHax/ds-decomp> — `dsd`, 현재의 DS 딜링킹/심볼 툴킷.
- <https://github.com/UsernameFodder/pmdsky-debug> — ACWW는 아니지만, 이 프로젝트에 없는
  산출물의 모범: arm9와 각 오버레이에 대한 지역별 YAML 심볼 테이블.
- <https://www.retroreversing.com/DS-NITRO-SDK> — SDK 트리와 그 `/man` 매뉴얼의 색인.

---

## 4. 이 감사가 제기하는 가설

- **H1.** 1–2프레임의 스타일러스 랙은 "프레임당 네 샘플에서 연속된 세 개의 정상 샘플"로
  완전히 설명된다. P1으로 확정된다: 정확히 그것을 모델링하여 24,600에서의 원본의 거부와
  24,700에서의 수락이 재현되면 메커니즘이 옳은 것이며 `input-and-touch.md`의 미해결 질문이
  닫힌다.
- **H2.** ACWW의 어떤 레이어도 VBlank 밖에서 `BGxX`/`BGxY`를 다시 쓰지 않으며, 이것이
  `draw_affine_bg`의 닫힌 형식을 정확하게 만든다. 마을 레시피에 걸쳐 `0x04000038`과
  `0x0400003C`에 `ACWW_INTERP_WATCH`를 걸어 합성 VCOUNT가 192 미만인 쓰기를 보고하게 하여 확정된다.
- **H3.** 게임의 어떤 것도 DISPSTAT 비트 2나 비트 1을 읽지 않는다. `0x04000004` 읽기에 같은
  계측을 걸어 비트 1 또는 비트 2 검사 후 결과가 버려지는 읽기를 세어 확정된다 — 또는 더 저렴하게,
  P2에 더해 어떤 실행도 바뀌지 않는다는 관측으로 확정된다.
- **H4.** 8의 배수가 아닌 워드 수를 가진 `CpuFastSet`이 실제 플레이에서 도달되므로, P4는 잠재적
  위험이 아니라 실제 손상을 고치는 것이다. 수정 전에 한 마을 실행 동안 SWI 핸들러에서 카운트가
  8의 배수가 아닌 호출을 세어 확정된다.
- **H5.** PXI 터치 응답의 비트 24–25는 NitroSDK 자체의 태그/오류 필드와 충돌하지 않는다.
  `nitro/pxi/common/fifo.h`를 읽어 확정된다(P13).

## 5. 관련 문서

- `../engine/graphics-pipeline.md`, `../engine/threads-and-interrupts.md`
- `../systems/input-and-touch.md`, `../systems/time-and-rtc.md`, `../systems/audio.md`
- `../../docs/kb/hybrid/hardware-services.md` — 이 주장들이 유래한 구현 측 페이지
- `../../docs/rules/D-defects.md` — D12(잘못 입력된 대상을 인코딩한 이름)는 C2가 속하는 부류이다
- `../../docs/rules/M-method.md` — M1(측정을 의심하라)은 B4 행이 그렇게 읽히는 이유이다
