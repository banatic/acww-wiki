# 그래픽스 파이프라인
<!-- source: wiki/engine/graphics-pipeline.md -->

**요약.** ACWW는 DS의 3D 지오메트리 엔진으로 월드를 그리고, 그 주변의 모든 것 —
하늘, 메시지 상자, 메뉴, HUD — 은 두 개의 2D 엔진으로 그린다. 모델은 NitroSystem G3D
리소스로 도착하고, 이름으로 텍스처에 바인딩되며, 미리 패킹된 디스플레이 리스트로
`0x04000400`의 지오메트리 FIFO에 곧바로 제출된다. 2D 쪽은 평범한 NDS이다: 우선순위에 따라
합성되는 텍스트 및 어파인 배경, OAM의 스프라이트, 그 위의 색상 특수 효과. 어느 엔진이
어느 물리 화면을 소유하는지는 `POWCNT1`에 기록되는 런타임 결정이다.

## 무슨 일이 일어나는가

### 리소스 입력

모델은 `nsbmd`(`BMD0`)이고 그 텍스처는 `nsbtx`(`BTX0`)이다; 애니메이션은 `nsbca`,
`nsbtp`, `nsbta`, `nsbva`, `nsbma`이다 [S: `extract/adm-kr/files/`, magic census — see
`../data/archives.md`]. `0x021079ac`의 `NNS_G3dGetResDataByName`은 리소스 안에서 이름 붙은
블록을 찾는 딕셔너리 조회이고 [S: `src/matched/NNS_G3dGetResDataByName.c`],
`0x02104f38`의 `NNS_G3dBindMdlTex`는 모델의 텍스처-머티리얼 딕셔너리를 순회하며 이름 붙은
각 텍스처를 바인딩하고, `nsbtx`에 없는 이름이 하나라도 있으면 FALSE를 반환한다
[S: `src/matched/NNS_G3dBindMdlTex.c`]. 팔레트 쪽 쌍둥이는 `NNS_G3dBindMdlPltt` `0x02104d7c`이다
[S: `config/adm-kr/arm9/autoload_2/symbols.txt`]. 텍스처 바이트는
`NNS_G3dTexLoad` `0x0210518c`를 통해 VRAM으로 가는데, 이 함수는 `GX_BeginLoadTex` / `GX_LoadTex` /
`GX_EndLoadTex`로 감싸고 4x4 압축 쌍을 두 번의 쓰기로 처리한다
[S: `src/matched/NNS_G3dTexLoad.c`]. 그 텍스처들을 위한 공간은 그래픽스
파운데이션 할당자 `NNS_GfdAllocFrmTexVram` `0x02102a54`가 나눠 주며, 패킹된 텍스처 키를 반환한다
[S: `src/matched/NNS_GfdAllocFrmTexVram.c`].

애니메이션 세트는 한 번에 한 종류씩 가져온다: `NNS_G3dGetJntAnmSet` `0x02107b28`,
`NNS_G3dGetMatCAnmSet` `0x02107b64`, `NNS_G3dGetTexSRTAnmSet` `0x02107ba0`,
`NNS_G3dGetTexPatAnmSet` `0x02107bdc`, `NNS_G3dGetVisAnmSet` `0x02107cd4`
[S: `config/adm-kr/arm9/autoload_2/symbols.txt`].

### 지오메트리 출력

셰이프 하나를 그리는 것은 `NNS_G3dDraw1Mat1Shp` `0x02107088`이다: 머티리얼과
텍스처 행렬 애니메이션 결과를 적용하고, 셰이프의 미리 패킹된 디스플레이 리스트를
`NNS_G3dGeSendDL((u8*)shp + shp->ofsDL, shp->sizeDL)`로 제출하고, 역 위치 스케일을 다시 적용한다
[S: `src/matched/NNS_G3dDraw1Mat1Shp.c`]. 제출 경로는 네 개의 ITCM 루틴이다:
`NNS_G3dGeSendDL` `0x01ff8d4c`는 256바이트 미만의 리스트는 버퍼를 통해, 더 큰 것은
DMA로 보낸다; `NNS_G3dGeBufferOP_N` `0x01ff8bd0`은 op 워드와 N개의 인수를
0xc0워드 명령 버퍼에 버퍼링하거나, op를 `0x04000400`의 FIFO에 곧바로 쓰고
인수를 `MI_CpuSend32`로 스트리밍한다; `NNS_G3dGeFlushBuffer` `0x01ff8ccc`는 진행 중인 DMA를 기다린 뒤
버퍼 전체를 보낸다; `NNS_G3dGeWaitSendDL` `0x01ff8e18`은 비동기 DMA가 완료될 때까지 스핀한다
[S: `src/matched/NNS_G3dGeSendDL.c`, `NNS_G3dGeBufferOP_N.c`, `NNS_G3dGeFlushBuffer.c`,
`NNS_G3dGeWaitSendDL.c`; `config/adm-kr/arm9/itcm/symbols.txt`]. 이 넷은 ITCM의 G3D
제출 멤버이지 ITCM 전체가 아니다: `itcm`은 158개의 함수 심볼을 담고 있고 그중 114개가
이름이 있으며, 여기에는 열세 개의 `NNSi_G3dFuncSbc_*` 씬 그래프 opcode, `MTX_*`/`VEC_*`
/`FX_*` 고정소수점 라이브러리 전체, `OS_IrqHandler`, `OS_Halt`, `OS_SaveContext`/`OS_LoadContext`,
`OS_GetTick`, 디스플레이 오브젝트 스테퍼가 포함된다 [S: `config/adm-kr/arm9/itcm/symbols.txt`, counted
over `kind:function` lines; see `memory-map.md` and `display-objects.md`].

전역 3D 상태 — 조명, 머티리얼 기본값, 스케일 계수 — 는 하나의 블록에 있으며,
`NNS_G3dGlbInit` `0x02105884`가 초기값을 채우고 `NNS_G3dGlbFlushP` `0x02105844`가 0x3e워드로
엔진에 보내며 +0xFC의 더티 비트 둘을 클리어한다
[S: `src/matched/NNS_G3dGlbInit.c`, `src/matched/NNS_G3dGlbFlushP.c`]. 조명 방향은
세 개의 10비트 필드와 비트 30-31의 조명 id로 하나의 `LIGHT_VECTOR` 워드에 패킹된다
[S: `src/matched/NNS_G3dGlbLightVector.c`]. `NNS_G3dInit` `0x021072e4`는 `G3X_Init`, 그 다음
`NNS_G3dGlbInit`을 호출하고, 그 다음 `0x04000600`의 GXSTAT FIFO-IRQ 필드를 설정한다
[S: `src/matched/NNS_G3dInit.c`].

NNS 아래에는 SDK 자체의 지오메트리 계층이 있다. `G3X_Init` `0x0211265c`는 파이프라인이 사용하는 레지스터
집합 전체를 명시한다: `DISP3DCNT` `0x04000060`, `EDGE_COLOR` `0x04000330`, `CLEAR_COLOR`
`0x04000350`, `CLEAR_DEPTH` `0x04000354`, `CLRIMAGE_OFFSET` `0x04000356`, `FOG_COLOR`
`0x04000358`, `FOG_OFFSET` `0x0400035c`, `FOG_TABLE` `0x04000360`, `TOON_TABLE` `0x04000380`,
`POLYGON_ATTR` `0x040004a4`, `TEXIMAGE_PARAM` `0x040004a8`, `TEXPLTT_BASE` `0x040004ac`,
`END_VTXS` `0x04000504`, `GXSTAT` `0x04000600` [S: `src/matched/G3X_Init.c`]. 행렬 결과는
GXSTAT busy 비트 `0x08000000`을 기다린 뒤 `CLIPMTX_RESULT` `0x04000640`과 `VECMTX_RESULT` `0x04000680`에서
읽어 낸다 [S: `src/matched/G3X_GetClipMtx.c`,
`src/matched/G3X_GetVectorMtx.c`]. 행렬 스택 레벨은 GXSTAT 비트 `0x1f00`(위치)과
`0x2000`(투영)이고, 오류 비트는 `0x4000`이다
[S: `src/matched/G3X_GetMtxStackLevelPV.c`, `G3X_GetMtxStackLevelPJ.c`].
`NNS_G3dGetCurrentMtx` `0x021073a8`은 그 읽기 경로를 사용한다: 플러시하고, 포트
`0x04000440`/`0x04000444`/`0x04000454`/`0x04000448`을 통해 단위 투영을 밀어 넣고,
결과 레지스터를 폴링한다 [S: `src/matched/NNS_G3dGetCurrentMtx.c`].

### VRAM

아홉 개의 VRAM 뱅크는 `autoload_2`의 `GX_SetBankFor*` 계열이 할당하며, 모두
`0x04000240`-`0x04000249`의 `VRAMCNT` 바이트에 쓴다(인덱스 7은 `WRAMCNT`이며 건너뛴다):
`GX_SetBankForBG` `0x02111740`, `ForOBJ` `0x021115d4`, `ForSubBG` `0x02110e4c`, `ForSubOBJ`
`0x02110dd0`, `ForTex` `0x02111204`, `ForTexPltt` `0x02111110`, `ForBGExtPltt` `0x021114c0`,
`ForOBJExtPltt` `0x02111408`, `ForClearImage` `0x02110fd0`, `ForLCDC` `0x02110ef8`, `ForARM7`
`0x02110f18` [S: `config/adm-kr/arm9/autoload_2/symbols.txt`;
`src/matched/GX_SetBankForBG.c` and siblings]. `GX_VRAMCNT_SetLCDC_` `0x021119f8`은
뱅크를 LCDC 모드에 두는 루틴이며, 그 상수가 각 뱅크의 LCDC 별칭을 알려 준다:
`0x06800000`, `0x06820000`, `0x06840000`, `0x06860000`, `0x06880000`, `0x06890000`, `0x06894000`,
`0x06898000`, `0x068A0000` [S: `src/matched/GX_VRAMCNT_SetLCDC_.c`].

대량 업로드는 고정 목적지로의 DMA 복사이다: OAM은 `0x07000000`(엔진 A)과
`0x07000400`(엔진 B); BG 팔레트는 `0x05000000` / `0x05000400`; OBJ 팔레트는 `0x05000200`
/ `0x05000600`; OBJ 타일은 `0x06400000` / `0x06600000`
[S: `src/matched/GX_LoadOAM.c`, `GXS_LoadOAM.c`, `GX_LoadBGPltt.c`, `GX_LoadOBJPltt.c`,
`GXS_LoadBGPltt.c`, `GXS_LoadOBJPltt.c`, `GX_LoadOBJ.c`, `GXS_LoadOBJ.c`].

### 2D

디스플레이 모드는 `DISPCNT` `0x04000000`에 대한 `GX_SetGraphicsMode` `0x0211062c`와
`DISPCNT_B` `0x04001000`에 대한 `GXS_SetGraphicsMode` `0x02110610`으로 설정된다; 서브 엔진에는
`bg0_2d3d`나 디스플레이 모드 필드가 없으므로 그 마스크는 세 개의 BG 모드 비트뿐이다
[S: `src/matched/GX_SetGraphicsMode.c`, `src/matched/GXS_SetGraphicsMode.c`]. `GX_DispOn`과
`GX_DispOff`는 `DISPCNT` 비트 16-17을 토글한다 [S: `src/matched/GX_DispOn.c`, `GX_DispOff.c`].
각 BG 레이어의 캐릭터 및 스크린 베이스 포인터는 `0x02111b00`-`0x02111f68`의 `G2_GetBGnCharPtr` /
`G2_GetBGnScrPtr` 쌍과 그 `G2S_` 서브 엔진 쌍둥이에서 온다
[S: `config/adm-kr/arm9/autoload_2/symbols.txt`].

어느 엔진이 어느 물리 화면을 구동하는지는 `0x04000304`의 `POWCNT1` 비트 15이다: `POWCNT1 =
0x020f`이면 엔진 A가 **아래** 화면을 구동하고, `0x820f`이면 위 화면을 구동한다
[S: `docs/kb/port/render.md`, screen ownership; the value is logged between PAD samples 6723 and
6726 on the custom START9000 recipe]. `func_020540e4`가 게임 쪽 쓰기자로,
`(POWCNT1 & 0xfffffdf1) | 0x20e`를 계산한다 [S: `src/matched/func_020540e4.c`].

게임이 실제로 사용하는 2D 레이어는 인터프리터 경로에서 측정되었다. 마을의 위
화면은 BG 모드 1의 엔진 B이고 BG3는 어파인 레이어, `BG3CNT = 0x6f02`이다 — 그 레이어가
하늘이다 [E: `docs/log/cycle40-keyboard-gate-probe.md` SKY40, `tap-D57`]. 어파인 배경은
바이트 스크린 엔트리를 가진 8bpp이고, 크기는 128에서 1024 정사각형, 랩 비트는 13, PA..PD는 8.8이며
20.8 기준점은 BG2는 `+0x20`, BG3는 `+0x30`에 있다
[S: `port/render/nds2d.c`, `draw_affine_bg`, written to GBATEK; E: same run].

## 어디에 있는가

| 함수 또는 심볼 | 모듈 | 역할 | 등급/출처 |
|---|---|---|---|
| `NNS_G3dGeBufferOP_N` `0x01ff8bd0` | `itcm` | GX op 하나를 버퍼링하거나 쓰기 | S: `src/matched/NNS_G3dGeBufferOP_N.c` |
| `NNS_G3dGeFlushBuffer` `0x01ff8ccc` | `itcm` | 명령 버퍼 전송 | S: `src/matched/NNS_G3dGeFlushBuffer.c` |
| `NNS_G3dGeSendDL` `0x01ff8d4c` | `itcm` | 패킹된 디스플레이 리스트 제출 | S: `src/matched/NNS_G3dGeSendDL.c` |
| `NNS_G3dGeWaitSendDL` `0x01ff8e18` | `itcm` | 비동기 GX DMA 대기 | S: `src/matched/NNS_G3dGeWaitSendDL.c` |
| `NNS_G3dDraw1Mat1Shp` `0x02107088` | `autoload_2` | 셰이프 하나 그리기 | S: `src/matched/NNS_G3dDraw1Mat1Shp.c` |
| `NNS_G3dInit` `0x021072e4` | `autoload_2` | G3D 기동 | S: `src/matched/NNS_G3dInit.c` |
| `NNS_G3dGlbInit` `0x02105884` / `NNS_G3dGlbFlushP` `0x02105844` | `autoload_2` | 전역 3D 상태 | S: `src/matched/NNS_G3dGlbInit.c`, `NNS_G3dGlbFlushP.c` |
| `NNS_G3dTexLoad` `0x0210518c` | `autoload_2` | `nsbtx` 블록 업로드 | S: `src/matched/NNS_G3dTexLoad.c` |
| `NNS_G3dBindMdlTex` `0x02104f38` / `BindMdlPltt` `0x02104d7c` | `autoload_2` | 이름으로 바인딩 | S: `src/matched/NNS_G3dBindMdlTex.c` |
| `NNS_G3dGetResDataByName` `0x021079ac` | `autoload_2` | 리소스 딕셔너리 조회 | S: `src/matched/NNS_G3dGetResDataByName.c` |
| `NNS_GfdAllocFrmTexVram` `0x02102a54` | `autoload_2` | 텍스처 VRAM 할당 | S: `src/matched/NNS_GfdAllocFrmTexVram.c` |
| `G3X_Init` `0x0211265c` | `autoload_2` | 모든 3D 레지스터를 명시하고 클리어 | S: `src/matched/G3X_Init.c` |
| `G3X_GetClipMtx` `0x021123a8` / `G3X_GetVectorMtx` `0x02112360` | `autoload_2` | 행렬 읽기 | S: `src/matched/G3X_GetClipMtx.c` |
| `G3_LoadMtx43` `0x02112134`, `G3_MultMtx43` `0x02112118`, `G3_MultMtx33` `0x021120fc` | `autoload_2` | FIFO로의 행렬 연산 | S: `src/matched/G3_LoadMtx43.c` and siblings |
| `GX_SetGraphicsMode` `0x0211062c` / `GXS_` `0x02110610` | `autoload_2` | `DISPCNT` / `DISPCNT_B` | S: `src/matched/GX_SetGraphicsMode.c` |
| `GX_SetBankFor*` `0x02110dd0`..`0x02111740` | `autoload_2` | `VRAMCNT` 할당 | S: `src/matched/GX_SetBankForBG.c` etc. |
| `GX_VRAMCNT_SetLCDC_` `0x021119f8` | `autoload_2` | LCDC 별칭 테이블 | S: `src/matched/GX_VRAMCNT_SetLCDC_.c` |
| `GX_LoadOAM` `0x02113280` / `GXS_LoadOAM` `0x02113218` | `autoload_2` | OAM DMA | S: `src/matched/GX_LoadOAM.c` |
| `func_020540e4` | `main` | `POWCNT1` 쓰기 | S: `src/matched/func_020540e4.c` |
| `NNS_G2dMapScrToCharText` `0x02103734` | `autoload_2` | 32타일 블록 접기로 텍스트 BG 스크린 맵을 채움 | S: `src/matched/NNS_G2dMapScrToCharText.c` |

## 읽고 쓰는 데이터

| 주소 | 의미 | 쓰는 쪽 | 읽는 쪽 |
|---|---|---|---|
| `0x04000000` / `0x04001000` | `DISPCNT` A / B | `GX_SetGraphicsMode`, `GX_DispOn/Off` | LCD [S: `src/matched/GX_SetGraphicsMode.c`] |
| `0x04000008`+2n | `BGnCNT` | 게임의 레이어 설정 | 2D 엔진 [S: `port/render/nds2d.c`] |
| `0x04000050` / `0x52` / `0x54` | `BLDCNT` / `BLDALPHA` / `BLDY` | 게임 | 색상 특수 효과 [S: `port/render/nds2d.c`] |
| `0x04000060` | `DISP3DCNT` | `G3X_Init`, `G3X_SetFog` | 3D 엔진 [S: `src/matched/G3X_Init.c`] |
| `0x04000240`-`0x04000249` | `VRAMCNT` (인덱스 7 = `WRAMCNT`) | `GX_SetBankFor*` | 메모리 컨트롤러 [S: `src/matched/GX_VRAMCNT_SetLCDC_.c`] |
| `0x04000280`-`0x040002bf` | 하드웨어 나눗셈 / 제곱근 | `FX_Div`, `FX_Sqrt` | 동일 [E: `docs/log/...` GX40] |
| `0x04000304` | `POWCNT1`; 비트 15가 어느 엔진이 위인지 바꿈 | `func_020540e4` | LCD들 [S: `src/matched/func_020540e4.c`; E: `docs/kb/port/render.md`] |
| `0x04000330`/`0x350`/`0x354`/`0x356`/`0x358`/`0x35c`/`0x360`/`0x380` | 엣지, 클리어 색상, 클리어 깊이, 클리어 이미지 오프셋, 안개 색상, 안개 오프셋, 안개 테이블, 툰 테이블 | `G3X_*` 설정자 | 3D 엔진 [S: `src/matched/G3X_Init.c`] |
| `0x04000400`-`0x0400043f` | 패킹된 지오메트리 FIFO(64바이트 전부가 같은 포트) | `NNS_G3dGeBufferOP_N`, `GX_SendFifo48B` | 지오메트리 엔진 [S: `src/matched/NNS_G3dGeBufferOP_N.c`; `port/render/gxfifo.c`] |
| `0x04000440`-`0x040005c8` | 45개의 개별 명령 포트, `0x04000440 + (op-0x10)*4` | `G3_*`, `G3X_*` | 동일 [S: `src/matched/G3_LoadMtx43.c`; `port/render/gxfifo.c`] |
| `0x04000600` | `GXSTAT`: busy `0x08000000`, 스택 오류 `0x8000`, 스택 레벨 `0x1f00`/`0x2000`, FIFO IRQ `0xc0000000` | `G3X_Init`, `G3X_ResetMtxStack` | `G3X_GetClipMtx`, 대기 루프들 [S: `src/matched/G3X_Init.c`] |
| `0x04000640` / `0x04000680` | `CLIPMTX_RESULT` (16 fx32) / `VECMTX_RESULT` (9 fx32) | 지오메트리 엔진 | `G3X_GetClipMtx` / `GetVectorMtx` [S: `src/matched/G3X_GetClipMtx.c`] |
| `0x05000000`/`0x200`/`0x400`/`0x600` | BG-A, OBJ-A, BG-B, OBJ-B 팔레트 | `GX_LoadBGPltt` 계열 | 2D 엔진 [S: `src/matched/GX_LoadBGPltt.c`] |
| `0x06400000` / `0x06600000` | OBJ 타일 공간 A / B | `GX_LoadOBJ`, `GXS_LoadOBJ` | 2D 엔진 [S: `src/matched/GX_LoadOBJ.c`] |
| `0x06800000`+ | LCDC 뱅크 별칭 | `GX_VRAMCNT_SetLCDC_`, `GX_LoadTex` | 텍스처 유닛 [S: `src/matched/GX_VRAMCNT_SetLCDC_.c`] |
| `0x07000000` / `0x07000400` | OAM A / B, 각 128 엔트리 | `GX_LoadOAM`, `GXS_LoadOAM` | 2D 엔진 [S: `src/matched/GX_LoadOAM.c`] |

## 확인 방법

포트는 이 모든 것의 하드웨어 쪽을 구현하므로, 어떤 주장을 가장 빠르게 확인하는 방법은
ROM 자체의 코드를 그 위에서 실행하는 것이다. 마을과 그 하늘에 도달하는 레시피:

```
ACWW_INTERP=1
ACWW_KEYS_AT / _FOR / _EVERY   # the custom START9000 keys -- the short forms are not read (B1)
ACWW_TOUCH_ENABLE=1 ACWW_TOUCH_X=221 ACWW_TOUCH_Y=181 ACWW_TOUCH_AT=6900 ACWW_TOUCH_EVERY=60
ACWW_STOP_FRAME=48000
python port/tools/run.py --frontier start
```

예상: 프레임 4,500에 이름 키보드 위로 택시 내부 — 카파(Kapp'n), 비, 창문 — 가
프레임당 대략 291 폴리곤과 99,000 합성 픽셀로 나타난다
[E: `docs/log/cycle40-keyboard-gate-probe.md` GX40, run `off-D51`;
O: `scratchpad/oracle/off`, the same scene in DeSmuME]. 프레임 37,800에는 마을 회관 위의 파란
하늘에 구름이 있다 [E: same log, SKY40, run `tap-D57`]. 프레임 37,500에는 오버레이
5, 36, 54, 120, 117이 로드된 마을이 있고, 48,000프레임이 811초에 실행된다
[E: `scratchpad/cycle40/runs/tap-D56`, per the same log, TOWN40].

이 페이지에 특화된 계측이 둘 있다. `ACWW_TEXTRACE_FRAME`을 십진수
`ACWW_TEXTRACE_INDEX`와 함께 쓰면 2,048 폴리곤 리스트 범위 안에서 한 폴리곤의 텍스처 출처를 덤프한다
[S: `docs/kb/port/render.md`, texture provenance]. `ACWW_OAMDUMP=<frame>`은 두 OAM 테이블을 모두
덤프하며 `ACWW_TRACE_STATE`에 게이트되지 않는다 [S: `docs/kb/port/render.md`, OAM cursor table].
`ACWW_NOBLEND=1`은 색상 특수 효과를 비활성화하여 블렌드를 분리할 수 있게 한다
[S: `port/render/nds2d.c`].

## 가설

- **클리어 이미지(후면 평면 비트맵) 경로는 이 게임에서 절대 사용되지 않는다.** `DISP3DCNT` 비트 14는
  포트에서 기록만 되고 구현되지 않았지만, `func_ov001_0222e4dc`는
  `GX_SetBankForClearImage`를 호출한다 [S: `port/render/raster3d.c`; `src/matched/GX_SetBankForClearImage.c`].
  긴 마을 실행과 WFC 화면 실행에 걸쳐 `DISP3DCNT` 비트 14를 로깅하여 해결한다.
- **확장 회전/확대 및 대형 비트맵 배경(BG 모드 3-6)은 사용되지 않는다.** 포트는 이를 건너뛰며
  지금까지 어떤 씬도 필요로 하지 않았다 [S: `port/render/nds2d.c`, K_EXT / K_LARGE notes].
  인터프리터 레시피들에 걸쳐 이를 선택하는 `BGnCNT` 값에 대해 assert하여 해결한다.
- **윈도잉(`WIN0`/`WIN1`/`OBJWIN`), 모자이크, 확장 팔레트는 사용되지 않는다.** 같은 상황이다:
  기록됨, 미구현, 어떤 씬도 필요로 하지 않음 [S: `port/render/nds2d.c`].
  `DISPCNT & 0xE000`과 `DISPCNT & 0xC0000000`에 대해 assert하여 해결한다.
- **`BOX_TEST`, `POS_TEST`, `VEC_TEST`(GX 명령 0x70-0x72)는 게임의 컬링에 중요하다.**
  포트는 셋 모두를 스텁 처리하여 GXSTAT test-busy 비트를 클리어하고 "보임"으로 보고한다
  [S: `port/render/nds3d.c`]. 게임이 `BOX_TEST`로 컬링한다면, 항상 "보임"으로 답하는 것은
  폴리곤을 낭비하지만 보이는 것은 아무것도 바꾸지 않는다; `POS_TEST` 결과로 컬링한다면,
  틀릴 수 있다. 마을 레시피에서 프레임당 0x70/0x71/0x72 제출을 세어 해결한다.
- **포트의 `POWCNT1` 해석은 `0x020f`에서 엔진 A가 아래라는 것이다.** 이는 포트 실행에 대한
  실험적 해석이며 [E: `docs/kb/port/render.md`], 하드웨어 타이밍에서 같은 스왑을
  확인하는 데 오라클이 사용되지 않았다. 같은 프레임에서 `scratchpad/oracle/*`과 포트 실행 사이의
  두 화면 내용을 비교하여 해결한다.
- **`NNS_G3dGeSendDL`의 256바이트 임계값은 대부분의 셰이프가 DMA가 아니라 버퍼를 거친다는 뜻이다.**
  임계값은 소스에 있다 [S: `src/matched/NNS_G3dGeSendDL.c`]; 실제 분포는
  측정되지 않았다. `NNS_G3dDraw1Mat1Shp`에서 `shp->sizeDL`을 히스토그램으로 만들어 해결한다.

## 관련 문서

- `../data/archives.md` — `nsb*` 리소스 컨테이너.
- `../data/rom-layout.md` — 모델, 텍스처, 메뉴 에셋이 있는 곳.
- `text-and-messages.md` — 같은 2D 엔진으로 그려지는 글리프.
- `display-objects.md`, `memory-map.md` — 이 파이프라인을 둘러싼 프레임워크와 아레나.
