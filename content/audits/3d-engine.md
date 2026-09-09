# 감사(audit): 포트의 3D 엔진을 공개 기록과 대조하다
<!-- source: wiki/audits/3d-engine.md -->

**요약.** 포트의 소프트웨어 지오메트리 엔진(`port/render/nds3d.c`)과 래스터라이저
(`port/render/raster3d.c`), 그리고 커맨드 파서(`gxfifo.c`)와 텍스처 유닛(`tex3d.c`)을
GBATEK의 DS 3D 장(章)과 두 개의 정확한 소프트웨어 에뮬레이터, 즉 melonDS의 `GPU3D.cpp` /
`GPU3D_Soft.cpp` 및 DeSmuME의 `gfx3d.cpp` / `rasterize.cpp`에 대해 주장 하나하나 대조하여
검사했다. 61개의 주장을 검사했으며, 38개는 일치, 17개는 불일치, 4개는 공개 기록에 명시되지
않음, 2개는 포트 자체의 측정과 에뮬레이터 사이의 명백한 모순이다. 지오메트리 단계는 양호한
상태다 — 행렬, 행 벡터 규약, 클리핑, 뷰포트, 조명, 텍스처 행렬 모드 1 상수, 그리고 모든
텍스처 형식이 옳으며, 그중 몇 가지는 공개 기록이 틀리기 쉽게 만드는 지점에서도 옳다.
**손상은 세 곳에 집중되어 있다: 반투명 블렌딩(포트는 후면 평면(rear plane) 위에서 폴리곤
알파를 두 번 적용하고, 하드웨어가 최댓값을 취하는 곳에서 알파를 누적한다), W 버퍼 깊이(ACWW는
W 버퍼 게임인데 포트는 W를 선형 보간하고 폴리곤별 W 정규화를 건너뛴다), 그리고 포트가
선언하지만 수행하지 않는 네 가지 효과 — 안개, 엣지 마킹, 툰, 안티에일리어싱.** 열두 개의
진단 노트 중 두 개는 과적재되어 있어 문자 그대로의 의미와 다른 것을 뜻한다.

**방법.** `main`의 워크트리 헤드(`6ca48706`)에서 읽었다. 공개 자료는 기억에 의존하지 않고
가져왔으며, 모든 행은 페이지나 파일을 명시한다. 어떤 소스에서도 코드를 복사하지 않았다. 게임은
실행하지 않았고 이 페이지의 어떤 측정도 새로운 것이 아니다 — 포트 쪽 수치는 `docs/log/`와 이미
디스크에 있는 오라클 비교에서 인용했다.

---

## 1. 게임이 실제로 엔진에 요구하는 것

이것이 어떤 행이 중요한지를 결정한다. `func_02002f68`은 게임의 3D 초기화(bring-up)이고
매칭된 소스이므로, 이는 등급 S다.

| 레지스터 | ROM이 쓰는 값 | 결과 |
|---|---|---|
| `DISP3DCNT` `0x04000060` | 클리어 후 `\|0x10`, 다음 `\|0x08`, 다음 `&0xcfdf` | 알파 블렌딩 **켬**(비트 3), 안티에일리어싱 **켬**(비트 4), 엣지 마킹 **끔**(비트 5), 하이라이트 셰이딩 선택 **끔**(비트 1) [S: `src/matched/func_02002f68.c`] |
| `VIEWPORT` `0x04000580` | `0xbfff0000` | X1=0, Y1=0, X2=255, Y2=191 — 전체 화면이며, 포트가 기본값으로 쓰는 값과 같다 |
| `SWAP_BUFFERS` `0x04000540` | `3` | 비트 0 = **수동** 반투명 Y 정렬, 비트 1 = **W 버퍼** 깊이 |
| `G3X_SetClearColor` `0x02112304` | `(rgb=0, alpha=0, depth=0x7fff, polygonID=0x3f, fog=TRUE)` | 후면 평면 투명(그래서 2D 하늘이 보인다), 클리어 폴리곤 ID `0x3f`, **후면 평면 안개 활성화** |

정리하면: ACWW는 W 버퍼, 알파 블렌딩, 안티에일리어싱, 수동 정렬, 엣지 마킹 끔 게임이며,
후면 평면은 투명하고 안개 플래그가 켜져 있다. 안개 마스터 활성화(`DISP3DCNT` 비트 7)는 이
함수가 설정하지 않는다. 나중에 무언가가 설정하는지는 미해결이다 — H3을 보라.

재질(material) 조사 결과. ROM의 866개 모델에 대한 포트 자체 헤더 주석에서
[S: `port/render/raster3d.c` header]: 2,040개 재질 전부가 `GX_POLYGONMODE_MODULATE`다(데칼
없음, 툰 없음, 섀도우 없음); 18,767개 프리미티브 중 17,173개가 트라이앵글 스트립이다.

---

## 2. 주장 표

판정은 **일치(agrees)** / **불일치(disagrees)** / **미명시(unspecified)** / **모순(contradiction)**
이다. "포트"는 해당 주장이 있는 파일과 함수를 가리킨다.

### A. 커맨드 스트림, 행렬과 스택

| # | 포트가 진술하는 주장 | 공개 자료 | 판정 | 바꿀 것 |
|---|---|---|---|---|
| A1 | 파라미터 개수: `MTX_LOAD_4x4`=16, `4x3`=12, `3x3`=9, `VTX_16`=2, `SHININESS`=32, `BOX_TEST`=3, `POS_TEST`=2, `VEC_TEST`=1 [`gxfifo.c`, `param_count`] | GBATEK, [DS 3D Geometry Commands](https://problemkaputt.de/gbatek-ds-3d-geometry-commands.htm) | 일치 | 없음 |
| A2 | 유효한 커맨드는 0x10–0x1C, 0x20–0x2B, 0x30–0x34, 0x40–0x41, 0x50, 0x60, 0x70–0x72이고, 그 밖의 것은 커맨드가 아니다 [`gxfifo.c`] | GBATEK, [DS 3D Overview](https://problemkaputt.de/gbatek-ds-3d-overview.htm) | 일치 | 없음 |
| A3 | 버텍스는 행 벡터이며 `v' = v × M`, 이동(translation)은 네 번째 **행**에 있다; `MTX_MULT_*`는 `current = param × current`를 계산한다 [`nds3d.c` header, `mat_target_mult`] | GBATEK, [DS 3D Matrix Types](https://problemkaputt.de/gbatek-ds-3d-matrix-types.htm); melonDS `GPU3D.cpp` | 일치 | 없음 — 이 파일에서 거꾸로 하기 가장 쉬운 단 하나의 항목이다 |
| A4 | 위치/벡터 스택은 사용 가능한 레벨이 31개이고, 투영과 텍스처는 1개다 [`nds3d.c`, `POS_STACK_DEPTH`] | GBATEK, [DS 3D Matrix Stack](https://problemkaputt.de/gbatek-ds-3d-matrix-stack.htm) | 일치 | 없음 |
| A5 | `MTX_POP`의 파라미터는 부호 있는 6비트 오프셋이며, 투영 모드에서는 무조건 한 레벨을 팝한다 [`nds3d.c` case 0x12] | GBATEK, 같은 페이지: 오프셋 −30..+31, 투영은 +1로 강제 | 일치 | 없음 |
| A6 | 레벨 31에서 푸시하면 스택 오류를 설정하고 **푸시하지 않는다**; 범위 밖으로 팝하면 오류를 설정하고 클램프한다 [`nds3d.c` case 0x11/0x12] | GBATEK, 같은 페이지: 엔트리 31은 존재하며 읽기/쓰기 접근이 가능하고, 이를 건드리면 **플래그는 설정되지만 연산은 미러링된 엔트리에 대해 그대로 진행된다** | 불일치(경미) | 오류를 올린 뒤 클램프된 슬롯에 대해 푸시가 진행되게 하여, 과도하게 푸시하는 게임도 자기 일관적인 행렬을 돌려받게 한다 |
| A7 | `MTX_STORE`/`MTX_RESTORE`는 5비트 슬롯 인덱스를 받는다 [`nds3d.c` case 0x13/0x14] | GBATEK: 유효한 주소는 0..30이고, 주소 31은 오버플로 플래그를 설정한다 | 불일치(경미) | 인덱스 31에서도 `GX_NOTE_MTXSTACK`을 올린다 |
| A8 | `MTX_SCALE`은 모드 2에서도 위치 행렬에만 적용된다 [`mat_target_mult(..., 1)`] | GBATEK, [DS 3D Matrix Stack](https://problemkaputt.de/gbatek-ds-3d-matrix-stack.htm) | 일치 | 없음 — 그리고 이것이 조명된 지오메트리와, 스케일하면 조명이 바뀌는 지오메트리를 가르는 한 줄이다 |
| A9 | `CLIPMTX_RESULT`는 `position × projection`이며 모든 행렬 커맨드 후에 공개된다 [`mtx_readback`] | GBATEK, [DS 3D Tests](https://problemkaputt.de/gbatek-ds-3d-tests.htm), POS_TEST "clip coordinate matrix" | 일치 | 없음 |
| A10 | `GXSTAT`은 비트 8–12에 스택 레벨, 13에 투영 레벨, 15에 오류를 담으며, 포트는 추가로 "FIFO less than half full"을 비트 25로 보고한다 [`gxstat_update`] | GBATEK, [DS 3D Status](https://problemkaputt.de/gbatek-ds-3d-status.htm): 25 = less-than-half-full, **26 = FIFO empty**, 27 = geometry busy, 30–31 = FIFO IRQ mode(유일하게 쓰기 가능한 필드) | 불일치 | `gxstat_update()`는 매번 새 워드를 쓰며 비트 15만 보존한다. 따라서 (a) **비트 26**을 절대 설정하지 않으므로 "FIFO empty"를 폴링하는 SDK 루프가 끝나지 않는다; (b) `NNS_G3dInit`이 설정하는 **비트 30–31**을 지운다 [S: `src/matched/NNS_G3dInit.c`]; (c) 어떤 행렬 커맨드든 실행되는 순간 비트 1의 박스 테스트 결과를 지운다. 수정 **F7**을 보라 |
| A11 | `BOX_TEST`/`POS_TEST`/`VEC_TEST`는 테스트 없이 "보임(visible)"으로 답하고, busy 비트는 클리어된다 [`nds3d.c` case 0x70–0x72] | GBATEK, [DS 3D Tests](https://problemkaputt.de/gbatek-ds-3d-tests.htm): `POS_RESULT`는 `0x04000620`의 4워드, `VEC_RESULT`는 `0x04000630`의 3하프워드 | 불일치 | `BOX_TEST`가 "보임"으로 답하는 것은 안전한 방향이며 비용은 폴리곤뿐이다. `POS_TEST`와 `VEC_TEST`는 **아무것도** 쓰지 않으므로, 게임은 I/O 페이지에 들어 있던 값을 그대로 읽는다. 둘 다 기존 코드 두 줄이면 된다 — 수정 **F5**를 보라 |
| A12 | `RAM_COUNT`와 `DISP3DCNT` 비트 13 오버플로 플래그는 구현되지 않았다; 오버플로는 노트만 올린다 [`emit_poly`] | GBATEK, [DS 3D Status](https://problemkaputt.de/gbatek-ds-3d-status.htm): `RAM_COUNT` `0x04000604`, 비트 0–11에 폴리곤(최대 2048), 16–28에 버텍스(최대 6144) | 불일치(경미) | 두 카운터를 쓰고 오버플로 시 `DISP3DCNT` 비트 13을 설정한다; 포트는 이미 두 수치를 모두 갖고 있다 |

### B. 버텍스, 프리미티브, 클리핑과 뷰포트

| # | 주장 | 공개 자료 | 판정 | 바꿀 것 |
|---|---|---|---|---|
| B1 | `VTX_16`은 1.3.12 원시값이고, `VTX_10`은 1.3.6이며 왼쪽으로 6 시프트한다 [`nds3d.c` case 0x23/0x24] | GBATEK, [DS 3D Polygon Definitions by Vertices](https://problemkaputt.de/gbatek-ds-3d-polygon-definitions-by-vertices.htm) | 일치 | 없음 |
| B2 | `VTX_DIFF`는 부호 확장된 10비트 필드를 시프트 없이 **원시값 그대로** 더한다 [`nds3d.c` case 0x28] | GBATEK, 같은 페이지: 델타는 "1비트 부호 + 9비트 소수부"이며 `VTX_10` 판독값에 비해 **8로 나눈** 값이다. 즉 1.3.12로는 `<<3`이다. DeSmuME `gfx3d.cpp`는 부호 확장한 뒤 같은 순 3만큼 시프트한다 | **모순** | 포트는 `8a7fdb5f`에서 `<<3`을 제거했다. `npc/model/48/49.nsbmd`의 오프라인 재구성이 시프트 0에서 모델 자체가 선언한 바운딩 박스와 정확히 일치하고 시프트 3에서는 그 밖으로 벗어났기 때문이다 [E: `docs/log/2026-09-02.md`]. 둘 다 옳을 수는 없고, 오라클은 DeSmuME**이다**. H1을 보라 — 이 페이지에서 가장 가치 높은 미해결 질문이다 |
| B3 | `VTX_XY`/`XZ`/`YZ`는 세 번째 성분을 이전 버텍스에서 유지한다 [`nds3d.c` case 0x25–0x27] | GBATEK, 같은 페이지 | 일치 | 없음 |
| B4 | 스트립: 트라이앵글 스트립은 세 개짜리 롤링 윈도우에서 와인딩을 번갈아 바꾸고, 쿼드 스트립은 버텍스를 `v0,v1,v3,v2`로 링 구성한다 [`submit_vertex`] | GBATEK, 같은 페이지, BEGIN_VTXS 0–3 | 일치 | 없음 |
| B5 | `BEGIN_VTXS`/`END_VTXS` 바깥의 버텍스는 무시된다 [`submit_vertex`, `if (!in_prim) return`] | GBATEK: `END_VTXS`는 OpenGL과의 대응을 위한 더미다 | 일치 | 없음 |
| B6 | 클리핑은 여섯 평면 모두에 대한 Sutherland–Hodgman이며, 그 후 폴리곤은 최대 열 개의 버텍스를 가질 수 있다 [`clip_plane`, `ClipPoly`] | GBATEK, 같은 페이지: 여섯 면 모두에 대해 클리핑되며, 클리핑된 버텍스는 새 버텍스 두 개로 대체된다 | 일치 | 없음 |
| B7 | 클리핑된 버텍스 색상은 채널당 8비트로 보간된다 [`lerp_vtx`] | melonDS `GPU3D.cpp`: "vertex colors are kept at 5-bit during clipping. makes for shitty results", 그 후 그리기 전에 `(x<<4)+0xF`로 9비트로 변환되며, "the added bias affects interpolation" | 불일치(외관상) | 포트는 의도적으로 하드웨어보다 부드럽고 그렇게 밝히고 있다; 그대로 두되, 클리핑된 폴리곤을 가로지르는 그라데이션은 오라클과 바이트 단위로 일치하지 않을 것임을 기록한다 |
| B8 | 화면 x는 12.4 형식으로 `x1 + (x + w) · vw / (2w)`이다 [`to_screen`] | GBATEK, 같은 페이지: `screen_x = (xx + ww) × viewport_width / (2 × ww) + viewport_x1` | 일치 | 없음 |
| B9 | 화면 y는 `(191 − y2)·16 + (w − y)·vh·16 / (2w)`이며 `vh = y2 − y1 + 1`이다 [`to_screen`] | GBATEK: 뷰포트 좌표는 **원점이 왼쪽 아래**이므로, 위에서부터의 행은 `191 − [(y+w)·vh/(2w) + y1]`이다 | 불일치(off-by-one 의심) | `y2 = y1 + vh − 1`을 대입하면 포트의 식은 `192 − y1 − t·vh`가 되어 스펙의 `191 − y1 − t·vh`와 어긋난다. **3D 레이어 전체가 한 행 아래에 있다.** 확정하기 쉽다 — 수정 **F8**을 보라 |
| B10 | 앞면은 화면 공간에서 신발끈(shoelace) 값이 음수인 와인딩이다 [`emit_poly`, `GX_FRONT_IS_NEGATIVE_AREA`] | GBATEK: 버텍스는 보통 반시계 방향으로 감긴다; DeSmuME `rasterize.cpp`는 "due to a late change of a y-coord flipping, our winding order is wrong … flip the verts for every front-facing poly"라고 경고한다 | 일치 | 없음 — 부호는 맞으며, 파일은 이미 이것을 공식에서 유도되지 않은 유일한 부호라고 명시한다 |
| B11 | 원근 나눗셈은 랩어라운드 대신 포화(saturate)하는 64비트 시프트-빼기 루프로 수행된다 [`div64`, `sdiv64`] | melonDS `GPU3D.cpp`: "the DS performs these divisions using a 32-bit divider", W가 0xFFFF를 넘으면 아래로 시프트하여 정밀도를 잃는다 | 불일치(포트가 더 정확) | 그대로 둔다; 먼 지오메트리에서 하드웨어의 버텍스 스냅이 **나타나지 않을** 것이며, 이는 오라클에서 차이로 드러날 것임을 기록한다 |
| B12 | 화면 면적이 0인 폴리곤은 버려지고 `degenerate`로 집계된다 [`emit_poly`] | GBATEK, [DS 3D Display Control](https://problemkaputt.de/gbatek-ds-3d-display-control.htm): `DISP_1DOT_DEPTH` `0x04000610`; 1도트 폴리곤은 어느 버텍스의 W가 임계값 이하이고 `POLYGON_ATTR` 비트 13이 설정되어 있으면 **첫 번째 버텍스의** 색상, 깊이, 텍스처로 그려진다. melonDS는 같은 규칙으로 상류에서 거부한다 | 불일치 | 하드웨어가 단일 도트로 렌더링하는 먼 마을의 세부가 조용히 사라진다. 수정 **F9**를 보라 |
| B13 | `POLYGON_ATTR`은 `BEGIN_VTXS`에서 래치되고, `NORMAL`에서의 조명은 래치된 조명 활성화 비트를 사용한다 [`poly_attr_live`, `light_vertex`] | GBATEK, [DS 3D Polygon Attributes](https://problemkaputt.de/gbatek-ds-3d-polygon-attributes.htm): 쓰기는 다음 `BEGIN_VTXS`에서 효력을 가지며, 버텍스 색상은 `NORMAL`이 실행될 때만 다시 계산된다 | 일치 | 없음 |

### C. 조명과 재질

| # | 주장 | 공개 자료 | 판정 | 바꿀 것 |
|---|---|---|---|---|
| C1 | `colour = emission + Σ (specular·shine + diffuse·diff + ambient) · lightcolour`이며, `diff = max(0, −light·normal)`, `shine = max(0, −half·normal)²`이다 [`light_vertex`] | GBATEK, [DS 3D Polygon Light Parameters](https://problemkaputt.de/gbatek-ds-3d-polygon-light-parameters.htm) | 일치 | 없음 |
| C2 | 시선 벡터는 상수 `(0, 0, −1)`이므로 `half = (light + eye)/2`다 [`light_vertex`] | GBATEK, 같은 페이지: DS는 하드웨어에서 정규화할 수 없고, 투영 곱셈을 생략하며 `(0,0,−1.0)`을 하드코딩한다; "specular reflection will not work when the projection matrix is rotated" | 일치 | 없음 — 그리고 포트는 하드웨어의 버그를 물려받는데, 이것이 옳다 |
| C3 | `LIGHT_VECTOR`는 커맨드가 실행되는 순간 벡터 행렬로 변환되어 변환된 채로 저장된다 [`nds3d.c` case 0x32] | GBATEK, 같은 페이지 | 일치 | 없음 |
| C4 | `SHININESS`는 32워드에 128개 엔트리, 워드당 8비트 엔트리 네 개이며, 제곱된 레벨로 인덱싱된다 [`nds3d.c` case 0x34] | GBATEK, 같은 페이지 | 일치 | 없음 |
| C5 | 광택(shininess) 테이블이 비활성화되면 제곱된 레벨이 직접 사용된다 [`spec_table_on`] | GBATEK: 테이블이 비활성화되면 하드웨어는 테이블이 **선형 램프**를 담고 있는 것처럼 동작한다 — 즉 레벨 자체 | 일치 | 없음 |
| C6 | `DIF_AMB` 비트 15는 추가로 버텍스 색상을 설정한다 [`nds3d.c` case 0x30] | GBATEK, 같은 페이지 | 일치 | 없음 |
| C7 | 색상은 전 과정에서 채널당 8비트로 운반된다 [`exp5`, `add_term`] | GBATEK: 내부 파이프라인은 5/6비트다; melonDS는 5비트로 양자화하고 `+0xF` 바이어스로 다시 확장한다 | 불일치(의도적, 외관상) | 그대로 둔다; 파일이 이미 그 논거를 제시한다. 다만 어떤 프레임도 오라클과 바이트 단위로 같아지는 일은 없을 것이라는 뜻이다 |

### D. 텍스처 유닛

| # | 주장 | 공개 자료 | 판정 | 바꿀 것 |
|---|---|---|---|---|
| D1 | 크기 필드는 `8 << n`이므로 log2는 `n + 3`이다; S 크기는 비트 20–22, T 크기는 23–25 [`acww_gx_texel`] | GBATEK, [DS 3D Texture Attributes](https://problemkaputt.de/gbatek-ds-3d-texture-attributes.htm) | 일치 | 없음 |
| D2 | 팔레트 베이스는 형식 2를 **제외한** 모든 형식에서 `PLTT_BASE << 4`이고, 형식 2에서는 `<< 3`이다 [`pbase`] | GBATEK, 같은 페이지: "div8 or div10h"; melonDS와 DeSmuME 모두 2bpp 형식에서 베이스를 절반으로 한다 | 일치 | 없음 — 실패 양상(그럴듯하지만 틀린 색상)에 대한 파일의 주석이 정확히 맞다 |
| D3 | 일곱 형식 모두 디코딩된다: A3I5, 4/16/256색, 4x4 압축, A5I3, 다이렉트 [`acww_gx_texel`] | GBATEK, [DS 3D Texture Formats](https://problemkaputt.de/gbatek-ds-3d-texture-formats.htm) | 일치 | 없음. **이는 "a texture format … is not decoded" 노트가 어떤 형식에 대해서도 절대 발생할 수 없다는 뜻이다** — §3을 보라 |
| D4 | A3I5의 3비트 알파는 `(a<<5)\|(a<<2)\|(a>>1)`, 즉 `a·255/7`로 확장된다 [`case 1`] | GBATEK: 0..31 스케일에서 `Alpha = (Alpha*4) + (Alpha/2)` — 같은 비율 | 일치 | 없음 |
| D5 | 다이렉트 컬러: 비트 15가 설정되면 **불투명**을 뜻한다 [`default` case] | GBATEK, 같은 페이지; melonDS `alpha = (c & 0x8000) ? 31 : 0` | 일치 | 없음 |
| D6 | 4x4 블록의 인덱스 워드는 `0x20000 + (offset & 0x1FFFF)/2 + (offset & 0x40000)/4`에 있다 [`comp4x4_info_offset`] | GBATEK: `slot1 = slot0/2`, 그리고 `slot1 = slot2/2 + 0x10000`. DeSmuME: `indexBase = ((offset & 0xC000) == 0x8000) ? 0x30000 : 0x20000` | 일치 | 없음 |
| D7 | 4x4 셀렉터/모드 표: 모드 0 → {c0,c1,c2,transparent}; 모드 1 → {c0,c1,(c0+c1)/2,transparent}; 모드 2 → {c0..c3}; 모드 3 → {c0,c1,(5c0+3c1)/8,(3c0+5c1)/8} [`case 5`] | GBATEK, 같은 페이지; melonDS와 DeSmuME도 일치 | 일치 | 없음. 포트처럼 확장 전 5비트 채널에서 보간하는 것도 옳다 |
| D8 | 반복/플립: 플립은 반복이 켜져 있을 때만 적용되며, 타일을 번갈아 미러링한다 [`acww_gx_wrap`] | GBATEK; melonDS: `if (s & width) s = (width-1) - (s & (width-1)); else s &= width-1` | 일치 | 없음 |
| D9 | 텍스처 좌표 모드 1은 `(s, t, 1, 1) × M >> 12`이며, 상수항은 `0x100`이 아니라 **1**이다 [`apply_texmtx`] | melonDS `GPU3D.cpp`: `(s*m0 + t*m4 + m8 + m12) >> 12`, "both the third *and* fourth matrix rows are added". GBATEK의 "1/16.0"은 텍셀의 1/16이며, 포트의 1/16 텍셀 단위에서는 곧 **1이다** | 일치 | 없음. 포트의 2026-09-02 수정은 melonDS와 `NNSi_G3dSendTexSRTSi3d`에 의해 각각 독립적으로 확인된다 |
| D10 | 모드 2(법선 소스)는 `raw + (o >> 8)`이며 `o = (n, 1) × M >> 12`다; 모드 3(버텍스 소스)은 위치를 써서 같은 식이다 [`apply_texmtx`] | melonDS: 모드 2는 `raw + (nx·m0 + ny·m4 + nz·m8) >> 21`이고 모드 3은 `raw + (x·m0 + y·m4 + z·m8) >> 24`이며, **네 번째 행 항은 없다**. GBATEK은 TEXCOORD S,T가 행렬의 맨 아래 행에 있다고 말한다 | 불일치 | 포트의 순 시프트는 20인데 이미 `<<3`으로 스케일한 법선에 적용되어, 모드 2가 **16배 너무 크다**; 모드 3도 마찬가지로 16배 너무 크다; 그리고 둘 다 `raw_s` 위에 가짜 `m12/m13` 항을 더한다. 수정 **F6**을 보라 |
| D11 | 매핑되지 않은 VRAM 뱅크나 형식 0 텍스처는 조용히 완전 투명을 반환한다 [`tex_addr`, `pltt_addr` returning 0] | — | 미명시, 그러나 진단상의 구멍 | 뱅크가 매핑되지 않은 텍스처는 **어디에도 노트 없이** 세계에 구멍을 만든다. 수정 **F4**를 보라 |

### E. 깊이, 채우기와 반투명 — 래스터라이저

| # | 주장 | 공개 자료 | 판정 | 바꿀 것 |
|---|---|---|---|---|
| E1 | Z 버퍼 깊이는 `(((z · 0x4000) / w) + 0x3FFF) · 0x200`이며 24비트로 클램프된다 [`to_screen`] | melonDS `GPU3D_Soft.cpp`, 동일한 식 | 일치 | 없음 |
| E2 | W 버퍼 깊이는 클립 `w`이며 24비트로 클램프된다 [`to_screen`] | melonDS `GPU3D.cpp`: "W is normalized, such that all the polygon's W values fit within 16 bits" — 더 적은 비트에 들어가면 위로 확장하고 더 크면 압축한다 — 그리고 W 버퍼링이 사용하는 것은 **정규화된** W다(뷰포트 변환에는 쓰지 않는다) | 불일치 | **ACWW는 W 버퍼 게임이다**(`SWAP_BUFFERS = 3`). 폴리곤별 정규화가 없으면 폴리곤 전체의 깊이 값이 24비트 범위의 잘못된 부분에 놓인다. 수정 **F2**를 보라 |
| E3 | 깊이는 두 모드 모두에서 스팬을 가로질러 선형 보간된다 [`attr_lerp` on `a[0]`] | melonDS `GPU3D_Soft.h`, `InterpolateZ()`: Z 버퍼 깊이는 화면 공간에서 선형이다; **W 버퍼 깊이는 원근 보간기를 거친다** | 불일치 | 역시 ACWW의 모드가 틀린 쪽이다. 얕은 각도의 지면은 모든 폴리곤 한가운데에서 깊이가 틀린다. 수정 **F2**를 보라 |
| E4 | 깊이 동일 허용 오차는 ±0x200이다 [`draw_poly`, `depth_equal`] | GBATEK, [DS 3D Polygon Attributes](https://problemkaputt.de/gbatek-ds-3d-polygon-attributes.htm): "±200h within the 24-bit range". melonDS는 이를 나눈다: **Z 모드에서 ±0x200, W 모드에서 ±0xFF** | 불일치(경미) | `wbuffer_mode`가 설정되면 0xFF를 쓴다 |
| E5 | 깊이 테스트는 엄격한 미만(less-than) 비교다 [`(gu32)a.a[0] >= depth[off]` → reject] | melonDS `GPU3D_Soft.cpp` 및 블로그 "[The DS GPU and its fun quirks](https://melonds.kuribo64.net/comments.php?id=56)": 미만 비교는 "accepts equal depth values when drawing front-facing polygons over opaque **back-facing** pixels"이며, 게임들은 평면 데칼을 위해 이에 의존한다 | 불일치 | 포트는 픽셀별 면(facing) 비트를 저장하지 않으므로 이를 재현할 수 없다. ACWW에는 우선순위가 낮지만(데칼 재질 없음), 동일 평면 스티커가 빠지는 이유가 이것이다 |
| E6 | 반투명 폴리곤은 `POLYGON_ATTR` 비트 11이 설정된 경우에만 깊이를 쓴다 [`write_depth`] | GBATEK와 두 에뮬레이터 모두 | 일치 | 없음 |
| E7 | 이미 있는 픽셀이 **같은** ID의 반투명 폴리곤에 의해 쓰인 것이면 반투명 픽셀은 즉시 거부된다 [`tattr`, `tmark`] | melonDS: `(dstattr & 0x007F0000) == (attr & 0x007F0000)` → 폐기; DeSmuME: "dont overwrite pixels on translucent polys with the same polyids" | 일치 | 없음. 포트 자체 카운터에 따르면 200초 택시 실행에서 이것이 3번 발생하므로, 올바르되 여기서는 사실상 작동하지 않는다 |
| E8 | 알파 블렌딩은 `dst = src·a + dst·(1−a)`이며, 목적지 알파는 `a + da·(1−a)`로 누적된다 [`draw_poly`] | GBATEK, [DS 3D Toon, Edge, Fog, Alpha-Blending, Anti-Aliasing](https://problemkaputt.de/gbatek-ds-3d-toon-edge-fog-alpha-blending-anti-aliasing.htm): `FrameBuf[X] = (Poly[X]·(Poly[A]+1) + FrameBuf[X]·(31−Poly[A]))/32` 그리고 **`FrameBuf[A] = max(Poly[A], FrameBuf[A])`**; melonDS와 DeSmuME도 일치 | 불일치 | 알파는 누적이 아니라 **최댓값**이어야 한다. 알파 16의 반투명 표면 두 개가 겹치면 포트는 88% 불투명, 하드웨어는 52%가 된다. 수정 **F1**을 보라 |
| E9 | 반투명 픽셀은 클리어된 후면 평면을 포함해 색상 버퍼에 있는 무엇이든 그것과 블렌딩된다 [`draw_poly`] | GBATEK, 같은 페이지: (a) 알파 블렌딩이 꺼져 있거나, (b) `Poly[A] = 31`이거나, (c) **`FrameBuf[A] = 0`**이면 블렌딩은 **건너뛰고** 픽셀은 단순히 덮어쓴다; 두 에뮬레이터 모두 일치 | 불일치 | ACWW의 클리어 알파는 0이므로, 빈 후면 평면 위의 모든 반투명 폴리곤은 검은색, 알파 0인 목적지와 블렌딩된다 — RGB에 자신의 알파가 곱해진다 — 그리고 컴포지터가 3D 레이어를 2D 하늘 위에 얹을 때 알파를 **또 한 번** 곱한다. **택시와 마을의 모든 반투명 표면이 두 번 어두워진다.** 수정 **F1**을 보라 |
| E10 | 알파 0은 와이어프레임을 뜻하며, 포트는 그 폴리곤을 건너뛴다 [`draw_poly`, `alpha5 == 0`] | GBATEK: 알파 0은 폴리곤의 **엣지만을 고정 알파 31로** 그린다; melonDS는 정확히 그렇게 구현하고 끝에서 알파를 31로 강제한다. DeSmuME에는 와이어프레임 경로가 아예 없다 | 불일치 | 포트의 조사에 따르면 ACWW에는 와이어프레임 재질이 없으므로 오늘날 비용은 0이다. 그러나 이 건너뛰기는 `GX_NOTE_BADCMD`를 올리며, 이는 "an unknown command id reached the parser"로 보고된다 — §3을 보라 |
| E11 | 알파 테스트는 알파가 0이 아닌 텍셀을 유지한다; `ALPHA_TEST_REF`는 읽지 않는다 [`draw_poly`] | GBATEK, [DS 3D Display Control](https://problemkaputt.de/gbatek-ds-3d-display-control.htm): 픽셀은 알파가 `ALPHA_TEST_REF`**보다 클** 때만 그려지며, 텍스처 블렌딩 후 **최종** 픽셀에 적용된다; ref 0은 테스트가 비활성화된 것과 동일하다 | ACWW에 대해서는 일치(ref 0), 일반적으로는 불일치 | `0x04000340`에서 `ALPHA_TEST_REF`를 읽어 텍셀 알파가 아니라 `fa`와 비교한다. 세 줄이다 |
| E12 | 두 패스, 불투명 다음 반투명, 둘 다 제출 순서로 — `SWAP_BUFFERS` 비트 0이 수동 정렬을 요구하기 때문 [`acww_nds3d_raster`] | melonDS `SortKey`: 불투명 먼저, 다음 반투명; **불투명 폴리곤은 항상 Y 정렬되며**, 비트 0은 반투명 폴리곤이 Y 정렬에 합류할지만 결정한다 | ACWW에 대해서는 일치 | 포트는 비트 0을 전혀 읽지 않는다. 자동 정렬이 요청되면 노트를 추가하여, 나중에 그것을 원하는 씬이 조용히 잘못 정렬되지 않게 한다 |
| E13 | 폴리곤은 `POLYGON_ATTR` 알파가 31이 아닐 때, 그리고 오직 그때만 "반투명"이다 [`trans` in `draw_poly`] | GBATEK, [DS 3D Texture Formats](https://problemkaputt.de/gbatek-ds-3d-texture-formats.htm): A3I5(형식 1)와 A5I3(형식 6)가 "반투명" 형식이다; melonDS는 블렌딩된 알파로 **픽셀별로** 반투명 여부를 결정하며, "translucent polygons can have opaque pixels, and those follow the same rules as opaque polygons"라고 적는다 | 불일치 | A3I5 또는 A5I3 텍스처를 가진 알파 31 폴리곤은 포트에서 **불투명** 패스로 그려지고, 깊이를 쓰며, 동일 ID 규칙에서 면제된다. 하드웨어에서는 그 부분 투명 텍셀들이 반투명 프래그먼트다. 이것이 택시의 비와 창유리다. 수정 **F3**을 보라 |
| E14 | 스팬은 픽셀 중심 `(px·16 + 8)`이 `[xL, xR)`에 있고 샘플 행이 `[ya, yb)`에 있는 곳이 채워진다 [`draw_poly`] | melonDS `GPU3D_Soft.h`/`.cpp`: DS에는 명시적인 기울기 기반 채우기 규칙이 있다 — "right edge is filled if slope > 1; left edge is filled if slope ≤ 1; edges with slope = 0 are always filled"; AA나 엣지 마킹이 켜져 있을 때, 픽셀이 반투명이고 블렌딩이 켜져 있을 때, 또는 폴리곤이 와이어프레임일 때 엣지는 **항상** 채워진다; 그리고 명시된 조건에서 "right vertical edges are pushed 1px to the left" | 불일치 | 샘플 중심 규칙은 중심을 비켜가는, 한 픽셀보다 좁거나 짧은 모든 폴리곤을 버린다; 하드웨어는 최소한 엣지는 채운다. 가는 울타리, 난간, 먼 세부가 사라진다. ACWW는 AA가 켜져 있으므로 그 지오메트리에 대해 하드웨어의 **엣지는 항상 채워지며**, 이 때문에 포트는 체계적으로 더 가늘다. 수정 **F9**를 보라 |
| E15 | 원근 보정은 `q = (wmin << 14)/w`이며, `s·q`, `t·q`, `q`를 선형 보간하고 픽셀마다 나눈다 [`draw_poly`] | melonDS `GPU3D_Soft.h`: DS는 두 W 값에서 **하나의** 원근 계수를 계산하고, 엣지를 따라 9비트, 스팬을 따라 8비트로 양자화한 뒤, 그 단일 계수를 모든 속성에 선형으로 적용한다; 하위 7비트를 마스킹한 후 두 W 값이 같으면 특별한 **선형** 경로가 있다 | 효과상 일치, 정밀도는 불일치 | 포트가 하드웨어보다 더 정확하다. 두 가지 결과: DS의 텍스처 계단 현상이 없고, 3D 엔진으로 그린 2D 쿼드가 하드웨어의 W 동일 지름길이 만드는 방식대로 픽셀 정확하지는 않을 것이다. 기록해 두되, 오라클이 요구하기 전에는 "고치지" 않는다 |
| E16 | 클리어 깊이는 `(cd << 9)`이고, `0x1FF`는 `0x7FFF`에서**만** 더해진다 [`clear_buffers`] | GBATEK, [DS 3D Rear-Plane](https://problemkaputt.de/gbatek-ds-3d-rear-plane.htm): `X = (X·200h) + ((X+1)/8000h)·1FFh` — 포트는 이와 정확히 일치한다. melonDS는 무조건 `(d & 0x7FFF)·0x200 + 0x1FF`를 쓴다 | GBATEK과 일치, melonDS와 불일치 | 변경 없음: ACWW는 `0x7FFF`에서 클리어하며, 거기서는 둘이 동일하다. 포트는 GBATEK을 따랐고 에뮬레이터는 그러지 않았다는 점은 기록할 가치가 있다 |
| E17 | 클리어 폴리곤 ID와 클리어 안개 플래그는 픽셀별로 저장되지 않는다 [`clear_buffers`] | GBATEK: `CLEAR_COLOR` 비트 24–29는 클리어 폴리곤 ID이고 비트 15는 후면 평면 안개 활성화다; melonDS는 둘 다 속성 버퍼에 쓰고, 추가로 가시 영역 **바깥**의 1픽셀 테두리에도 써서 테두리 엣지 마킹이 동작하게 한다 | 불일치 | ACWW는 ID를 `0x3f`로, 안개를 true로 설정한다. 엣지 마킹과 후면 평면 안개를 막는다. **F10**과 **F11**의 선행 조건이다 |
| E18 | 후면 평면 비트맵(`DISP3DCNT` 비트 14)은 구현되지 않았다; 노트가 발생한다 [`clear_buffers`] | GBATEK: 텍스처 슬롯 2와 3에 있는 256×256 16비트 비트맵 두 개, `CLRIMAGE_OFFSET`으로 스크롤된다 | 불일치, 올바르게 노트됨 | `func_ov001_0222e4dc`가 `GX_SetBankForClearImage`를 호출하므로, 이것이 명백히 죽은 코드는 아니다. 비트 14를 로깅하여 확정한다 — `wiki/engine/graphics-pipeline.md`에 이미 미해결 질문으로 있다 |

### F. 포트가 선언하지만 수행하지 않는 효과

| # | 주장 | 공개 자료 | 판정 |
|---|---|---|---|
| F-fog | 안개는 노트되지만 렌더링되지 않는다 [`clear_buffers`, `GX_NOTE_FOG`] | GBATEK은 알고리즘 전체를 제공한다: `FogDepthBoundary[n] = FOG_OFFSET + FOG_STEP·(n+1)`, `FOG_STEP = 0x400 >> FOG_SHIFT`, 경계 사이에서 선형 보간되는 7비트 밀도 엔트리 32개, RGB **와** A에 대한 블렌드 `(FogColor·D + FrameBuf·(128−D))/128`, `D = 127`은 128로 취급, `DISP3DCNT` 비트 6이 설정되면 알파에만 적용, 그리고 후면 평면은 자체 안개 플래그를 가진다. melonDS는 테이블을 17비트 소수부로 보간하며 안개를 **두** 프레임버퍼 레이어 모두에 적용한다 | 불일치 — 완전히 명세되어 있으나 전적으로 부재 |
| F-edge | 엣지 마킹은 노트되지만 렌더링되지 않는다 | GBATEK: `EDGE_COLOR` `0x04000330`, `polygonID >> 3`으로 인덱싱되는 **8**개 엔트리. melonDS: 엣지란 **불투명** 폴리곤 ID가 네 직교 이웃 중 하나와 다르고 **동시에** 깊이가 그 이웃보다 작은 픽셀이다; 화면 테두리는 클리어 폴리곤 ID와 비교한다 | 불일치, 그러나 ACWW는 엣지 마킹을 **끈다** — 비용은 0 |
| F-toon | 폴리곤 모드 2는 모듈레이션으로 그려지고 노트된다 | GBATEK: `TOON_TABLE` `0x04000380`, 32색, **버텍스 색상의 빨간 성분**으로 인덱싱; 툰은 버텍스 색상을 대체한 뒤 모듈레이션하고, 하이라이트는 추가로 툰 색상을 63에서 포화되게 **더하며**, `DISP3DCNT` 비트 1로 전역 선택된다. 두 에뮬레이터 모두 `vertexRed >> 1`로 인덱싱한다 | 불일치; 포트의 조사에 따르면 ACWW에는 툰 재질이 0개지만, `G3X_SetToonTable`이 ROM의 SDK에 존재하며 노트가 유일한 계측 수단이다 |
| F-aa | 안티에일리어싱은 노트되지만 수행되지 않는다 | melonDS "[Antialiasing](https://melonds.kuribo64.net/comments.php?id=32)": 커버리지는 기울기 워커가 엣지 픽셀마다 계산하여 속성 버퍼에 보관하고, **엣지 마킹과 안개 이후의 별도 패스**에서 적용되며, 불투명 쓰기가 아래로 밀어내는 두 번째 레이어와 최상위 프레임버퍼 레이어를 블렌딩한다. 불투명 폴리곤의 실루엣 엣지에만 적용되고, 폴리곤 내부나 교차부에는 절대 적용되지 않는다 | 불일치, 그리고 **ACWW는 AA를 켠다** |
| F-shadow | 폴리곤 모드 3은 버려지고 노트된다 | GBATEK, [DS 3D Shadow Polygons](https://problemkaputt.de/gbatek-ds-3d-shadow-polygons.htm), 그리고 melonDS의 스텐실 비트 두 개 | 불일치; ACWW의 조사에 따르면 섀도우 재질은 0개 |

### G. 2D 엔진과의 합성

| # | 주장 | 공개 자료 | 판정 | 바꿀 것 |
|---|---|---|---|---|
| G1 | 3D 출력은 엔진 A의 BG0이며, BG0 자체의 우선순위로 합성되고, 블렌드 소유자 레코드에 BG0으로 들어간다 [`nds2d.c`, `K_3D` branch] | GBATEK, [DS 3D Final 2D Output](https://problemkaputt.de/gbatek-ds-3d-final-2d-output.htm) | 일치 | 없음 — 그리고 한 프레임에 네 번 합성한다는 주석은 남겨둘 가치가 있다 |
| G2 | 3D 레이어는 0..255 알파로 `dst = c·a + d·(1−a)`를 써서 2D 결과 위에 블렌딩된다 [`acww_nds3d_compose`] | GBATEK, 같은 페이지: 픽셀별 3D 블렌딩은 3D 픽셀 자체의 알파에서 유도한 **`EVA = A/2`, `EVB = 16 − A/2`**를 사용하며 `BLDALPHA`를 우회한다 | 형식은 일치, 양자화는 다름 | 하드웨어에서는 5비트 알파가 4비트 가중치가 된다. 작은 문제다; **E9**의 중첩이 진짜 문제다 |
| G3 | 3D 레이어의 `BG0HOFS` 스크롤, 그리고 모자이크가 이에 적용될 수 없다는 사실 | GBATEK, 같은 페이지: 512픽셀 스팬, 이미지 256 다음 투명 256, 랩어라운드; 수직 스크롤 없음, 회전 없음 | 포트에서 미명시 | 구현되지 않았고 노트도 없다. 우선순위 낮음; 기록해 둔다 |

---

## 3. 열두 개의 노트, 그리고 그중 두 개가 실제로 뜻하는 것

`acww_nds3d_report()`는 열두 개의 노트 문자열을 출력한다. 두 개는 과적재되어 있어, 이를
문자 그대로 받아들이는 독자는 엉뚱한 것을 조사하게 된다(M1).

| 노트 텍스트 | 실제로 올라가는 곳 | 실제 의미 |
|---|---|---|
| "a texture format or blend mode that is not decoded" | `raster3d.c:354`, 그리고 **오직** 거기: `if (mode == 1u)` | **데칼 블렌딩이 요청되었다.** `tex3d.c`는 일곱 형식 모두를 디코딩하며 노트를 전혀 올리지 않으므로, 이 문자열은 절대 텍스처 형식을 뜻할 수 없다 |
| "an unknown command id reached the parser" | `nds3d.c:3111`(default case) **그리고** `raster3d.c:182`, `alpha5 == 0` 분기 | 알 수 없는 커맨드**이거나 와이어프레임 폴리곤이 버려졌다** |
| "fog requested, not rendered" | `clear_buffers`, `DISP3DCNT & 0x0080` | 올바름 — 폴리곤별 비트가 아니라 안개 **마스터 활성화**다 |
| "matrix stack over/underflow" | `mtx_stack_error` | 올바름 |
| "BOX/POS/VEC_TEST answered without testing" | 세 커맨드 모두 공유 | 올바르지만, 무해한 경우(`BOX_TEST`)와 결과를 전혀 쓰지 않는 두 경우를 구분하지 못한다 |

수정: 데칼, 와이어프레임, `POS/VEC_TEST`에 각자의 비트를 준다. 노트 워드에는 빈 비트가 네 개
있고 보고 루프는 리터럴 `12`다.

---

## 4. 수정 목록, 우선순위 순

우선순위는 마을과 택시 씬이 정한다. 각 항목은 파일과 함수, 스펙이 말하는 것, 코드가 하는 것,
그리고 바뀔 프레임과 영역을 명시한다. 오라클 프레임은
`scratchpad/oracle/tap-town/shot_0NNNNN.bmp`(마을, 27,000–48,000, 1,500 간격)와
`scratchpad/oracle/tap-fullpad/shot_0NNNNN.bmp`(택시 6,000–24,000, 마을 25,500 이후)이며;
포트 쪽은 `scratchpad/cycle40/runs/tap-D56`으로, 이미
`scratchpad/oracle/tap-fullpad/compare-vs-tap-D56.txt`에서 비교되었다.

**F1 — 반투명 블렌딩: 알파 0인 목적지에 대한 블렌딩을 건너뛰고, 알파의 최댓값을 취한다.**
`raster3d.c`, `draw_poly`, `if (fa >= 255u)`의 `else` 분기.
*스펙:* `FrameBuf[A] = 0`이면 블렌딩을 건너뛰고 소스가 덮어쓴다; 저장되는 알파는
`max(Poly[A], FrameBuf[A])`다 [GBATEK, Toon/Edge/Fog/Alpha-Blending; melonDS `GPU3D_Soft.cpp`;
DeSmuME `rasterize.cpp`].
*코드:* 클리어된 버퍼(알파 0, RGB 0)에 대해 무조건 블렌딩하므로 색상에 자신의 알파가
곱해지고, 그 다음 `acww_nds3d_compose`가 레이어를 2D 하늘 위에 얹을 때 그 알파를 다시
곱한다. 저장되는 알파는 오버 컴포지트로 누적된다.
*검증:* 택시의 비와 창유리, `tap-fullpad/shot_009000.bmp`를 `tap-D56` 프레임 9,000과
비교, 아래 화면의 위쪽 절반. 그 영역에서 포트의 평균 휘도는 전체 프레임 NCC 0.9958에서
이미 오라클보다 0.7 단위 낮다; 창 영역이 이중 어두워짐이 드러나는 곳이다. 또한
`tap-town/shot_037500.bmp`, 마을의 반투명 표면을 통해 보이는 하늘.

**F2 — W 버퍼 깊이: 폴리곤별로 W를 정규화하고 원근 보정하여 보간한다.**
`nds3d.c`, `to_screen`(`wbuffer_mode` 분기); `raster3d.c`, `draw_poly`(속성 0).
*스펙:* "W is normalized, such that all the polygon's W values fit within 16 bits", 그리고
W 버퍼링이 사용하는 것은 정규화된 W다 — 뷰포트 변환이 아니다; W 버퍼 깊이는 원근 보간기를
거치는 반면 Z 버퍼 깊이는 선형이다 [melonDS `GPU3D.cpp`,
`GPU3D_Soft.h` `InterpolateZ`].
*코드:* `0x00FFFFFF`로 클램프한 원시 클립 `w`를 사용하고, 두 모드 모두에서 스팬을 가로질러
선형 보간한다. ACWW는 `SWAP_BUFFERS = 3`을 쓰므로 이것이 모든 프레임이 사용하는 모드다
[S: `src/matched/func_02002f68.c`].
*검증:* 지면이 건물과 만나는 곳과 택시 대시보드가 창과 만나는 곳의 깊이 순서 —
`tap-town/shot_037500.bmp`의 마을 회관 기초 주변, 그리고 `tap-fullpad`
프레임 9,000–15,000. 포트는 이미 버텍스별로 `q`를 운반하므로 장치는 존재한다.

**F3 — A3I5와 A5I3 폴리곤을 반투명으로 취급한다.** `raster3d.c`, `draw_poly`, `trans`와
`write_depth` 계산, 그리고 `acww_nds3d_raster`의 두 패스.
*스펙:* 형식 1과 6이 반투명 텍스처 형식이다; melonDS는 블렌딩된 알파로 픽셀별로 반투명
여부를 결정하며, 반투명 프래그먼트는 (비트 11 없이는) 깊이를 쓰지 않고 같은 폴리곤 ID에
대해 블렌딩하지도 않는다.
*코드:* `trans = alpha5 != 31u`뿐이다. A5I3 텍스처를 가진 알파 31 폴리곤은 불투명 패스로
그려지고 반투명 텍셀을 통해 깊이를 쓴다.
*검증:* 다시 택시 창과 비 — 포트 자체의 `nds3d tex` 원샷이 그 씬에서 64×64
A5I3 재질을 명시한다 [E: `docs/log/2026-09-02.md`]. `tap-fullpad/shot_012000.bmp`.

**F4 — 텍스처를 샘플링할 수 없을 때 노트를 올린다.** `tex3d.c`, `acww_gx_texel`, null인
`tex_addr` 또는 `pltt_addr` 뒤에 오는 모든 `return 0`.
*스펙:* 해당 없음 — 이것은 동작의 결함이 아니라 진단의 결함이다.
*코드:* 매핑되지 않은 VRAM 뱅크는 완전 투명을 반환하고 아무 말도 하지 않으므로, `VRAMCNT`
오독으로 생긴 세계의 구멍은 모델이 요청한 구멍과 구별할 수 없다.
*검증:* 아무 프레임이나; 마을 레시피에서 노트가 발생하거나 하지 않거나이며, 어느 답이든
`tex_addr`의 뱅크 테이블에 관한 미결 질문을 닫는다.

**F5 — `POS_TEST`와 `VEC_TEST`에 실제로 답한다.** `nds3d.c`, case 0x70–0x72.
*스펙:* `POS_TEST`는 `(x,y,z,1)`에 클립 행렬을 곱해 `POS_RESULT` `0x04000620`에 4워드를
쓴다; `VEC_TEST`는 `(x,y,z,0)`에 방향 행렬을 곱해 `VEC_RESULT` `0x04000630`에 3하프워드를
쓴다; 내부 버텍스 레지스터를 덮어쓴다 [GBATEK, DS 3D Tests].
*코드:* 아무것도 쓰지 않는다; 게임은 I/O 페이지에 들어 있던 값을 그대로 읽는다. 포트에는
이미 `vec_mul`, `dir_mul`, `m_clip`이 있으므로 각각 네 줄이면 된다.
*검증:* 먼저 마을 레시피에서 0x71/0x72 제출을 센다 — 개수가 0이면 이것은 눈에 보이는 변화
없는 공짜 정확성이며,
`wiki/engine/graphics-pipeline.md`의 미결 질문이 닫힌다.

**F6 — 텍스처 좌표 모드 2와 3.** `nds3d.c`, `apply_texmtx`, 모드 2/3 꼬리 부분.
*스펙:* 모드 2는 **원시 10비트** 법선에 대해 `raw + (nx·m0 + ny·m4 + nz·m8) >> 21`이다; 모드 3은
`raw + (x·m0 + y·m4 + z·m8) >> 24`다; 어느 쪽도 행렬의 네 번째 행을 더하지 않는다 [melonDS `GPU3D.cpp`].
*코드:* `v[3] = FX_ONE`인 `vec_mul`은 `m[12]`/`m[13]`을 포함하며, 순 시프트는 포트가 이미
`<<3`으로 스케일한 법선에 대해 20이므로, 두 모드 모두 가짜 이동이 더해진 채 **16배 너무 크게**
나온다.
*검증:* 마을 레시피에서 `(tex_param >> 30) & 3`이 {2,3}인 폴리곤을 센다 — 기존
`nds3d poly-in` 프로브가 이미 `tex`를 출력한다. 개수가 0이 아니면, `tap-town`의 물과 모든
환경 매핑된 표면이 해당 영역이다.

**F7 — `gxstat_update()`가 `GXSTAT`을 덮어쓰는 것을 막는다.** `nds3d.c`, `gxstat_update`.
*스펙:* 비트 30–31이 유일하게 쓰기 가능한 필드다; 26은 FIFO-empty; 1은 박스 테스트 결과다
[GBATEK, DS 3D Status].
*코드:* 비트 15만 보존한 새 워드를 쓰므로, 모든 행렬 커맨드마다 비트 26과 30–31이 클리어되고
테스트와 폴링 사이의 어떤 행렬 커맨드에 의해서도 박스 테스트 답이 파괴된다.
*검증:* 25와 함께 비트 26을 설정하고 비트 0–1과 30–31을 보존한다; 먼저 매칭된 소스에서
`0x04000600`을 읽는 곳을 grep한다. `port/shim/gfx/g3x_fifo.c`는 비트 27이 0인 것이 ROM의
스핀을 끝내는 요인임을 이미 기록하고 있다 — 같은 논리로 비트 26은 **1**이어야 한다.

**F8 — 의심되는 한 행짜리 뷰포트 오프셋.** `nds3d.c`, `to_screen`, `o->y` 식.
*스펙:* 뷰포트 좌표는 **왼쪽 아래**에서 시작하므로, 위에서부터의 행은
`191 − [(y+w)·vh/(2w) + y1]`이다 [GBATEK, DS 3D Display Control, VIEWPORT].
*코드:* `vh = y2 − y1 + 1`인 `(191 − y2)·16 + (w − y)·vh·16/(2w)`이며, 이는
`192 − y1 − t·vh`로 정리된다.
*검증:* `tap-town/shot_037500.bmp`의 지평선 행을 `tap-D56` 프레임 37,500과 비교. 한 행의
이동은 사람 눈에는 보이지 않지만 행 차이 히스토그램에는 명백하다. 대수만으로 바꾸지 말 것 —
오라클이 답하기 전까지 `wiki/STYLE.md` 규칙 7이 적용된다.

**F9 — 엣지를 채우고, 1도트 폴리곤을 렌더링한다.** `raster3d.c`, `draw_poly`; `nds3d.c`,
`emit_poly`(`area == 0` 분기).
*스펙:* DS는 기울기 규칙에 따라 엣지 픽셀을 채우며, "edges are always filled if
antialiasing/edgemarking are enabled, if the pixels are translucent and alpha blending is
enabled, or if the polygon is wireframe" — ACWW는 AA가 켜져 있으므로 그 엣지는 항상 채워진다
[melonDS `GPU3D_Soft.cpp`]. 한 픽셀로 붕괴하는 폴리곤은 `POLYGON_ATTR` 비트 13이 설정되어
있고 어느 W라도 `DISP_1DOT_DEPTH` `0x04000610` 이내이면 첫 번째 버텍스로 그려진다.
*코드:* 픽셀 중심 샘플 규칙이므로, 중심을 비켜가는 모든 폴리곤이 사라진다; 면적 0인
폴리곤은 `degenerate` 카운터로 버려진다.
*검증:* 포트는 이미 `degenerate`를 `culled`와 별도로 세고 있으며, 자체 주석에 버려진
삼각형이 정말로 납작한 것이 아니라 12.4 절삭 이후에만 납작하다고 기록되어 있다. 먼저 마을
레시피에서 `degenerate` 수치를 읽는다; 크다면 `tap-town/shot_027000.bmp`의 먼 마을 세부가
해당 영역이다.

**F10 — 안개.** `raster3d.c`, 합성 전 `colour[]`와 `depth[]`에 대한 후처리 패스.
*스펙:* §2 F-fog에 완전히 문서화되어 있다; 포트는 이미 깊이 버퍼를 갖고 있으며, 픽셀별 안개
플래그 하나가 필요하다. 이는 `CLEAR_COLOR` 비트 15(ACWW가 설정한다)로 초기화되고 불투명
쓰기에서는 `POLYGON_ATTR` 비트 15로 대체되며, 반투명 쓰기에서는 AND된다.
*코드:* 부재; `DISP3DCNT` 비트 7이 설정되면 노트가 발생한다.
*검증:* 먼저 비트 7이 설정되는 일이 있는지를 확정한다 — 보고서는 이미 매 프레임 `DISP3DCNT`를
출력한다. `func_02002f68`은 이를 설정하지 않으며, `G3X_SetFog`의 호출자는
`src/matched/`에 없다. 절대 설정되지 않는다면 이를 닫힌 가설로 강등한다; 설정된다면 택시의
`tap-fullpad/shot_009000.bmp`의 빗속 안개가 해당 영역이다.

**F11 — 클리어 폴리곤 ID와 픽셀별 속성 버퍼.** `raster3d.c`,
`clear_buffers`와 `draw_poly`.
*스펙:* 후면 평면은 색상, 알파, 깊이, 폴리곤 ID, 안개 플래그를 픽셀별로 초기화한다; 반투명
쓰기는 **불투명** 폴리곤 ID를 보존하며, 이 때문에 엣지 마킹이 반투명 오버레이를 거쳐도
살아남는다 [melonDS `GPU3D_Soft.cpp` `ClearBuffers`].
*코드:* `tattr[]`는 반투명 ID만 운반한다. 안개(F10), 엣지 마킹, 안티에일리어싱의 선행
조건이다; 그 자체로는 눈에 보이는 변화가 없다.

**F12 — 과적재된 노트를 분리한다.** `nds3d.h`(`GX_NOTE_*`), `raster3d.c`
(`note_text[12]`와 `for (i = 0; i < 12; i++)` 루프).
*스펙:* 해당 없음. *코드:* §3을 보라. *검증:* 셀프 테스트가 이미 노트를 보이는 상태로 실행된다.

**F13 — 작고, 저렴하며, 눈에 보이는 변화 없음:** `ALPHA_TEST_REF`(E11); W 모드에서의 ±0xFF
깊이 동일 허용 오차(E4); `RAM_COUNT`와 `DISP3DCNT` 비트 13 오버플로 플래그(A12);
`MTX_STORE` 슬롯 31 오류(A7); `SWAP_BUFFERS` 비트 0이 자동 정렬을 요구할 때의 노트(E12).

---

## 5. 가설

- **H1 — `VTX_DIFF`: 포트와 오라클이 둘 다 옳을 수는 없다.** GBATEK과 DeSmuME는
  10비트 델타를 왼쪽으로 3 시프트되어 1.3.12 좌표에 들어가는 1.0.9 소수로 만든다; 포트는
  이를 원시값 그대로 더하는데, `8a7fdb5f`에서 정확히 그 시프트를 제거했기 때문이다. 이는
  `npc/model/48/49.nsbmd`의 오프라인 재구성이 시프트 0에서 모델이 선언한 바운딩 박스와
  일치하고 시프트 3에서는 이를 초과했기 때문이다 [E: `docs/log/2026-09-02.md`]. 오라클은
  DeSmuME**이고**, 그 주민들은 올바르다; 포트의 주민들 역시 올바르다. 두 측정 중 하나가
  틀렸거나, 포트의 다른 무언가가 8배를 흡수하고 있다. *실험:* 같은 프레임에서
  `scratchpad/oracle/tap-town/shot_037500.bmp`와 `tap-D56` 사이의 주민 팔다리 비율을
  비교한 뒤, 시프트를 복원하여 포트를 다시 실행하고 어느 방향이 오라클 쪽으로 움직이는지
  본다. 그때까지는 두 판독값이 모두 페이지에 남는다(`wiki/STYLE.md` 규칙 7).
- **H2 — 포트에서 마을의 위 화면이 프레임 25,500부터 비어 있다.**
  `scratchpad/oracle/tap-fullpad/compare-vs-tap-D56.txt`는 프레임 24,000까지 `ncc-top`이
  0.96–1.00이고 25,500부터 **0.0000**이라고 보고하며, 포트의 전체 프레임 평균 휘도는
  ~130에서 ~66으로 절반이 된다. 정확히 0인 위 화면 NCC는 평탄한 이미지다. 이는 알려진
  검은 상단 LCD [E: `docs/log/2026-09-04.md`]와 부합하며, 3D가 아니라 2D/`POWCNT1` 문제다
  — 위 화면에 내용이 생기기 전까지 **이 페이지의 어떤 수정에도 이를 귀속시키지 말 것**.
- **H3 — ACWW에서 안개는 절대 활성화되지 않는다.** `func_02002f68`은 `DISP3DCNT` 비트 7을
  클리어하고 `G3X_SetFog`의 호출자는 `src/matched/`에 나타나지 않지만, `G3X_SetClearColor`는
  `fog = TRUE`로 호출되며, 이는 마스터 활성화가 켜져 있을 때만 의미가 있다. *실험:* 프레임별
  보고서가 이미 `DISP3DCNT`를 출력한다; 마을과 택시 레시피 전반에서 비트 7을 읽는다.
- **H4 — 텍스처 좌표 변환의 모드 2와 3은 사용되지 않는다.** 포트는 이들이 실행되는 것을 본
  적이 없으며 그렇게 밝히고 있다. *실험:* 마을 레시피에서 `(tex_param >> 30) & 3`의
  히스토그램을 만든다. 0이라면 F6은 수정이 아니라 공짜 정확성이 된다.
- **H5 — 포트의 추가 정확성은 오라클 비교에 부담이다.** 8비트 색상 채널(C7), 완전 정밀도
  원근 보간(E15), 64비트 나눗셈(B11) 모두 포트를 DS보다 *더* 정확하게 만든다. 어떤
  프레임도 오라클과 바이트 단위로 같아지지 않을 것이므로, 감사 방법은 정확 일치가 아니라
  구조적(NCC, 영역 마스크)으로 남아야 한다.

## 6. 관련 문서

- `../engine/graphics-pipeline.md` — 리소스 경로, 레지스터와 VRAM 뱅크.
- `../data/archives.md` — 이 텍스처들이 담겨 오는 `nsbmd`/`nsbtx` 컨테이너.
- `hardware-services.md` — 포트의 나머지 하드웨어에 같은 방법을 적용한 것.
- `port/render/selftest3d.c` — 기존 검사. 파라미터 개수, 패킹된 인코딩, 버텍스 형식, 행렬,
  와인딩, 클리핑, 래핑, I4와 4x4 텍스처 디코드, 깊이 순서, 그리고 합성 사례 하나를 다룬다.
  **다음에 대한 검사는 없다:** 안개, 엣지 마킹, 툰, 반투명 ID 규칙, W 버퍼 깊이, 깊이 동일
  테스트, 와이어프레임, 1도트 폴리곤, `POS_TEST`/`VEC_TEST`, `GXSTAT` 보존, A3I5/A5I3 알파,
  또는 다이렉트 컬러 — §4와 같은 목록이며, 수정의 회귀 테스트가 있어야 할 곳이다.
