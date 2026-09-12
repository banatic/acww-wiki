# 버스 타이밍: 캐시 적중이 아닐 때 접근에 드는 비용
<!-- source: wiki/engine/bus-timings.md -->

**요약.** `memory-map.md`는 어떤 영역이 있고 어느 영역이 캐시되는지를 설명한다. 이 문서는 각 영역에 얼마나 시간이 드는지를 설명한다. ARM9이 기다리는 모든 것의 비용은 세 장치가 정한다. **메모리 버스**의 영역별 수치는 캐시되지 않은 로드와 캐시 라인 채우기의 비용을 정한다. **카트리지**는 파이프가 아니라 페이지 장치이므로 요청에는 512바이트 명령 전체의 비용이 들거나 아무 비용도 들지 않는다. **지오메트리 FIFO**는 깊이가 260개 항목이며, 디스플레이 리스트가 이를 넘치게 하면 저장 명령어를 멈춘다. 여기의 모든 수치는 출처가 있는 DS의 수치이며 포트 측정값에 맞춰 보정한 것이 아니다.

이 문서 전체의 클록 단위: 버스는 33.513982 MHz, ARM9은 그 두 배인 67.027964 MHz로 동작한다 [P: GBATEK "DS Memory Timings": "Bus clock = 33MHz (33.513982 MHz)", "NDS9 clock = 66MHz
(internally twice bus clock; for cache/tcm)"]. 따라서 **버스 단위 하나는 ARM9 2사이클**이고 "반" 단위는 1사이클이다.

## 무슨 일이 일어나는가

### 영역별 메모리 버스

GBATEK의 NDS9/DATA 표를 원문의 33 MHz 단위로 그대로 옮겼다 [P: GBATEK "DS Memory Timings",
NDS9/DATA; "All timings are counted in 33MHz units (so "half" cycles can occur on NDS9)"]:

| N32 | S32 | N16 | S16 | Bus | 영역 |
|---|---|---|---|---|---|
| 10 | 2 | 9 | 1 | 16 | 메인 RAM (읽기) (캐시 꺼짐) |
| 4 | 1 | 4 | 1 | 32 | WRAM, BIOS, I/O, OAM |
| 5 | 2 | 4 | 1 | 16 | VRAM, 팔레트 RAM |
| 19 | 12 | 13 | 6 | 16 | GBA ROM |
| 13 | 10 | 13 | 10 | 8 | GBA RAM |
| 0.5 | 0.5 | 0.5 | — | 32 | TCM, Cache_Hit |
| 11 | 11 | 11 | — | 32 | Cache_Miss (BIOS) |
| 23 | 23 | 23 | — | 16 | Cache_Miss (Main RAM) |

`memory-map.md`의 캐시 영역 설명과 함께 읽는다. 메인 RAM 본체는 캐시되므로 로드는 0.5단위의 적중이거나 23단위의 라인 채우기다. 해당 문서의 ARM9 46사이클은 이 채우기에서 나온다. 같은 루틴이 캐시하지 않는 I/O, 팔레트, VRAM, OAM, `0x027fxxxx` 미러에는 각자의 행이 적용된다. 두 TCM에는 적중 비용이 적용되는데 TCM 접근은 버스에 도달하지 않기 때문이다.

**독립된 단일 접근은 비순차 접근이다.** 따라서 워드에는 N32, 하프워드나 바이트에는 N16이 적용된다. S 열은 버스트의 두 번째 이후 접근이다. ARM9 사이클로 환산하면 캐시되지 않은 메인 RAM 워드는 **20**, I/O나 OAM 워드는 **8**, VRAM이나 팔레트 워드는 **10**, TCM 워드는 **1**이다.

**이미 한 번의 철회를 낳은 주의사항.** GBATEK에는 NDS9/CODE와 NDS9/DATA라는 두 표가 있으며 메인 RAM의 캐시 꺼짐 행이 서로 다르다. CODE는 `9 9 4.5 4.5 16`, DATA는 `10 2 9 1 16`이다. DATA 표의 N32가 9라고 인용하는 것은 N16 열을 읽은 것이다 [H: source account: `docs/log/cycle41-gameplay.md` LATENCY55 L55-2, retracting MEM54 finding 7 item
3; direct ROM-source provenance unresolved].

### 카트리지: 명령, 간격, 페이지, 간격

통신은 8바이트 명령으로 이루어진다 [P: GBATEK "DS Cartridge Protocol": "Communication with
Cartridge ROM relies on sending 8 byte commands to the cartridge, after the sending the command,
a data stream can be received from the cartridge"]. 나머지 형식은 `0x040001a4`의 ROMCTRL에 담긴다 [P: GBATEK "DS Cartridge I/O Ports", 40001A4h: "0-12 KEY1 gap1 length
(0-1FFFh) ... (leading gap)", "16-21 KEY1 gap2 length (0-3Fh) ... (200h-byte gap)", "24-26 Data
Block size (0=None, 1..6=100h SHL (1..6) bytes, 7=4 bytes)", "27 Transfer CLK rate
(0=6.7MHz=33.51MHz/5, 1=4.2MHz=33.51MHz/8)"].

이 ROM에서는 각 필드가 헤더 워드 `normal_cmd_setting = 0x00416017`에 들어 있다 [S: `docs/log/cycle41-gameplay.md` LOAD52 L52-3 and LATENCY55 L55-1, from the extracted header]. gap1 = `0x00416017 & 0x1fff` = **23**클록, gap2 = `(0x00416017 >> 16) & 0x3f` = **1**이며 비트 27은 0, 즉 **6.7027964 MHz** 클록이다. 블록 크기는 헤더에 없다. SDK가 `CARD_COMMAND_PAGE` = `0x01000000`을 제어 워드에 OR하므로 필드 24-26 = 1 = `0x100 SHL 1` = **512바이트**가 된다 [S: `CARDi_TryReadCardDma`, `autoload_2`,
`src/matched/CARDi_TryReadCardDma.c:54,106`]. 이것이 `CARD_ROM_PAGE_SIZE`다 [S: `CARDi_ReadCard`, `autoload_2`, `src/matched/CARDi_ReadCard.c:19`].

카트리지 한 클록은 한 바이트를 운반하며, 67.027964 / 6.7027964 = **클록당 정확히 ARM9 10사이클**이다. 따라서 명령 하나의 비용은 다음과 같다.

    8 + gap1 23 + 512 + gap2 1 = 544 clocks = 5,440 ARM9 cycles

이 중 간격과 명령 단계, 즉 512클록의 처리량과 구분되는 지연은 32클록, **6.25%**다.

**중요한 것은 간격이 아니라 페이지다.** `CARDi_ReadCard`는 명령마다 페이지 전체를 읽고, 요청이 페이지 및 워드 경계에 정렬되어 있으며 길이가 한 페이지 이상일 때만 호출자 버퍼에 넣는다. 그렇지 않으면 `p->cache_buf`에 넣고 `p->cache_page`에 페이지를 기록한다 [S: `CARDi_ReadCard`, `autoload_2`, `src/matched/CARDi_ReadCard.c:75-122`]. 이 한 페이지는 요청 사이에도 기억된다. `CARDi_ReadFromCache`는 그 안의 요청을 `MI_CpuCopy8`로 처리하고 명령을 전혀 내보내지 않는다 [S: `CARDi_ReadFromCache`, `autoload_2`, `src/matched/CARDi_ReadFromCache.c:253-269`]. 따라서 짧은 읽기의 비용은 이전 읽기가 남긴 페이지에 따라 5,440사이클짜리 명령 전체이거나 0이다. 바이트당 속도로는 이를 표현할 수 없다. 마을 회관 퇴장 때 측정한 약 열한 바이트짜리 요청 2,956건은 **명령 1,106회와 비용 없는 적중 1,850회**였다 [H: source account: `docs/log/cycle41-gameplay.md` LATENCY55 L55-5; direct ROM-source
provenance unresolved].

**ROM 읽기에는 ARM7이 전혀 관여하지 않는다.** `CARDi_ReadCard`는 ARM9 자체에서 `0x04100010`의 `REG_CARD_DATA`를 읽고 ROMCTRL의 `CARD_DATA_READY`를 기다리며 돈다 [S: `CARDi_ReadCard`, `autoload_2`, `src/matched/CARDi_ReadCard.c:25,100-109`]. ARM7 카드 드라이버는 PXI를 통해 백업 계열을 처리한다. `systems/save-data.md`를 참고한다.

### 지오메트리 FIFO

지오메트리 엔진은 **256개 항목의 FIFO와 4개 항목의 PIPE, 합계 260개**를 통해 입력받으며, 이를 채운 쓰기 명령은 완전히 정지한다 [P: GBATEK "DS 3D Geometry Commands": "The FIFO has 256
entries, additionally, there is a PIPE with four entries"; "If the FIFO is full, then a wait is
generated until data is removed from the FIFO, ie. the STR opcode gets freezed"]. 한 항목은 매개변수 하나를 가진 명령이므로 매개변수 N개를 받는 명령은 `max(1, N)`개 항목을 차지한다.

소비 속도는 명령별이며 메모리 표와 같은 33 MHz 버스 단위다. `MTX_MODE` 1, `MTX_PUSH` 17, `MTX_POP` 36, `MTX_LOAD_4x4` 34, `MTX_MULT_4x4` 35, `MTX_MULT_4x3` 31, `MTX_MULT_3x3` 28, `MTX_SCALE`/`MTX_TRANS` 22, `NORMAL` 9, `VTX_16` 9, `VTX_10`과 다른 버텍스 형식 8, `DIF_AMB`/`SPE_EMI` 4, `LIGHT_VECTOR` 6, `SHININESS` 32, `BOX_TEST` 103, `POS_TEST` 9, `VEC_TEST` 5, `SWAP_BUFFERS` 392, 상태 설정 명령 1이다 [P: GBATEK "DS 3D Geometry Commands", the command list]. 같은 목록의 매개변수 개수는 포트 자체의 디스플레이 리스트 파서에도 독립적으로 옮겨져 있으며 [H: source account: `port/render/gxfifo.c`'s `param_count[]`; direct ROM-source provenance
unresolved], 37개 항목 모두 일치한다.

## 등급과 공백

- 영역별 버스 표, ROMCTRL 필드 목록, 8바이트 명령, FIFO 깊이, 정지에 관한 문장은 **[P]**다. 공개 하드웨어 문서를 인용한 것이다.
- 이 ROM의 카트리지 gap1, gap2, 클록, 페이지 크기는 **[S]**다. 헤더 워드와 이를 사용하는 매칭된 SDK 소스가 근거다.
- 포트가 이를 처리하는 방식과 측정된 요청/명령 비율은 **[H]**다. `ACWW_TICK_MODEL` 아래의 포트 자체 모델이며, `docs/log/cycle41-gameplay.md`의 TICK53 / MEM54 / LATENCY55에 기록되고 `docs/kb/hybrid/hardware-services.md` 4b에 정리돼 있다.
- **미해결.** 이 레포 어디에서도 쓰기 버퍼의 깊이와 정지 동작에 비용을 매기지 않으므로 캐시되지 않은 영역의 저장을 무료로 취급한다. 이전 명령이 아직 스트리밍 중일 때 새 명령을 내보내는 카트리지 동작도 모델링하지 않는다. 두 누락 때문에 이 문서를 바탕으로 한 모든 추정은 경과 시간의 하한이다.

## 사용처

`memory-map.md`(영역과 캐시 여부), `time-budgets.md`(게임이 시간을 사용하는 방식), `systems/save-data.md`(카트리지의 ARM7 측인 백업 장치), `graphics-pipeline.md`(FIFO로 들어가는 것).
