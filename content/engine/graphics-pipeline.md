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
`nsbtp`, `nsbta`, `nsbva`, `nsbma`이다 [H: source account: `extract/adm-kr/files/`, magic census — see
`../data/archives.md`; direct ROM-source provenance unresolved]. `0x021079ac`의 `NNS_G3dGetResDataByName`은 리소스 안에서 이름 붙은
블록을 찾는 딕셔너리 조회이고 [S: `src/matched/NNS_G3dGetResDataByName.c`; source account: `src/matched/NNS_G3dGetResDataByName.c`],
`0x02104f38`의 `NNS_G3dBindMdlTex`는 모델의 텍스처-머티리얼 딕셔너리를 순회하며 이름 붙은
각 텍스처를 바인딩하고, `nsbtx`에 없는 이름이 하나라도 있으면 FALSE를 반환한다
[S: `src/matched/NNS_G3dBindMdlTex.c`; source account: `src/matched/NNS_G3dBindMdlTex.c`]. 팔레트 쪽 쌍둥이는 `NNS_G3dBindMdlPltt` `0x02104d7c`이다
[S: `src/matched/NNS_G3dGetResDataByName.c`, `src/matched/NNS_G3dBindMdlTex.c`, `src/matched/NNS_G3dBindMdlPltt.c`; source account: `config/adm-kr/arm9/autoload_2/symbols.txt`]. 텍스처 바이트는
`NNS_G3dTexLoad` `0x0210518c`를 통해 VRAM으로 가는데, 이 함수는 `GX_BeginLoadTex` / `GX_LoadTex` /
`GX_EndLoadTex`로 감싸고 4x4 압축 쌍을 두 번의 쓰기로 처리한다
[S: `src/matched/NNS_G3dTexLoad.c`; source account: `src/matched/NNS_G3dTexLoad.c`]. 그 텍스처들을 위한 공간은 그래픽스
파운데이션 할당자 `NNS_GfdAllocFrmTexVram` `0x02102a54`가 나눠 주며, 패킹된 텍스처 키를 반환한다
[S: `src/matched/NNS_GfdAllocFrmTexVram.c`; source account: `src/matched/NNS_GfdAllocFrmTexVram.c`].

애니메이션 세트는 한 번에 한 종류씩 가져온다: `NNS_G3dGetJntAnmSet` `0x02107b28`,
`NNS_G3dGetMatCAnmSet` `0x02107b64`, `NNS_G3dGetTexSRTAnmSet` `0x02107ba0`,
`NNS_G3dGetTexPatAnmSet` `0x02107bdc`, `NNS_G3dGetVisAnmSet` `0x02107cd4`
[S: `src/matched/NNS_G3dGetJntAnmSet.c`, `src/matched/NNS_G3dGetMatCAnmSet.c`, `src/matched/NNS_G3dGetTexSRTAnmSet.c`, `src/matched/NNS_G3dGetTexPatAnmSet.c`, `src/matched/NNS_G3dGetVisAnmSet.c`; source account: `config/adm-kr/arm9/autoload_2/symbols.txt`].

### 지오메트리 출력

셰이프 하나를 그리는 것은 `NNS_G3dDraw1Mat1Shp` `0x02107088`이다: 머티리얼과
텍스처 행렬 애니메이션 결과를 적용하고, 셰이프의 미리 패킹된 디스플레이 리스트를
`NNS_G3dGeSendDL((u8*)shp + shp->ofsDL, shp->sizeDL)`로 제출하고, 역 위치 스케일을 다시 적용한다
[S: `src/matched/NNS_G3dDraw1Mat1Shp.c`; source account: `src/matched/NNS_G3dDraw1Mat1Shp.c`]. 제출 경로는 네 개의 ITCM 루틴이다:
`NNS_G3dGeSendDL` `0x01ff8d4c`는 256바이트 미만의 리스트는 버퍼를 통해, 더 큰 것은
DMA로 보낸다; `NNS_G3dGeBufferOP_N` `0x01ff8bd0`은 op 워드와 N개의 인수를
0xc0워드 명령 버퍼에 버퍼링하거나, op를 `0x04000400`의 FIFO에 곧바로 쓰고
인수를 `MI_CpuSend32`로 스트리밍한다; `NNS_G3dGeFlushBuffer` `0x01ff8ccc`는 진행 중인 DMA를 기다린 뒤
버퍼 전체를 보낸다; `NNS_G3dGeWaitSendDL` `0x01ff8e18`은 비동기 DMA가 완료될 때까지 스핀한다
[S: `src/matched/NNS_G3dGeSendDL.c`, `src/matched/NNS_G3dGeBufferOP_N.c`, `src/matched/NNS_G3dGeFlushBuffer.c`, `src/matched/NNS_G3dGeWaitSendDL.c`; source account: `src/matched/NNS_G3dGeSendDL.c`, `NNS_G3dGeBufferOP_N.c`, `NNS_G3dGeFlushBuffer.c`,
`NNS_G3dGeWaitSendDL.c`; `config/adm-kr/arm9/itcm/symbols.txt`]. 이 넷은 ITCM의 G3D
제출 멤버이지 ITCM 전체가 아니다: `itcm`은 158개의 함수 심볼을 담고 있고 그중 114개가
이름이 있으며, 여기에는 열세 개의 `NNSi_G3dFuncSbc_*` 씬 그래프 opcode, `MTX_*`/`VEC_*`
/`FX_*` 고정소수점 라이브러리 전체, `OS_IrqHandler`, `OS_Halt`, `OS_SaveContext`/`OS_LoadContext`,
`OS_GetTick`, 디스플레이 오브젝트 스테퍼가 포함된다 [S: `src/matched/NNS_G3dDraw1Mat1Shp.c`, `src/matched/NNS_G3dGeSendDL.c`, `src/matched/NNS_G3dGeBufferOP_N.c`, `src/matched/NNS_G3dGeFlushBuffer.c`, `src/matched/NNS_G3dGeWaitSendDL.c`, `src/matched/OS_IrqHandler.c`, `src/matched/OS_Halt.c`, `src/matched/OS_SaveContext.c`, `src/matched/OS_LoadContext.c`, `src/matched/OS_GetTick.c`; source account: `config/adm-kr/arm9/itcm/symbols.txt`, counted
over `kind:function` lines; see `memory-map.md` and `display-objects.md`].

전역 3D 상태 — 조명, 머티리얼 기본값, 스케일 계수 — 는 하나의 블록에 있으며,
`NNS_G3dGlbInit` `0x02105884`가 초기값을 채우고 `NNS_G3dGlbFlushP` `0x02105844`가 0x3e워드로
엔진에 보내며 +0xFC의 더티 비트 둘을 클리어한다
[S: `src/matched/NNS_G3dGlbInit.c`, `src/matched/NNS_G3dGlbFlushP.c`; source account: `src/matched/NNS_G3dGlbInit.c`, `src/matched/NNS_G3dGlbFlushP.c`]. 조명 방향은
세 개의 10비트 필드와 비트 30-31의 조명 id로 하나의 `LIGHT_VECTOR` 워드에 패킹된다
[S: `src/matched/NNS_G3dGlbLightVector.c`; source account: `src/matched/NNS_G3dGlbLightVector.c`]. `NNS_G3dInit` `0x021072e4`는 `G3X_Init`, 그 다음
`NNS_G3dGlbInit`을 호출하고, 그 다음 `0x04000600`의 GXSTAT FIFO-IRQ 필드를 설정한다
[S: `src/matched/NNS_G3dInit.c`; source account: `src/matched/NNS_G3dInit.c`].

NNS 아래에는 SDK 자체의 지오메트리 계층이 있다. `G3X_Init` `0x0211265c`는 파이프라인이 사용하는 레지스터
집합 전체를 명시한다: `DISP3DCNT` `0x04000060`, `EDGE_COLOR` `0x04000330`, `CLEAR_COLOR`
`0x04000350`, `CLEAR_DEPTH` `0x04000354`, `CLRIMAGE_OFFSET` `0x04000356`, `FOG_COLOR`
`0x04000358`, `FOG_OFFSET` `0x0400035c`, `FOG_TABLE` `0x04000360`, `TOON_TABLE` `0x04000380`,
`POLYGON_ATTR` `0x040004a4`, `TEXIMAGE_PARAM` `0x040004a8`, `TEXPLTT_BASE` `0x040004ac`,
`END_VTXS` `0x04000504`, `GXSTAT` `0x04000600` [S: `src/matched/G3X_Init.c`; source account: `src/matched/G3X_Init.c`]. 행렬 결과는
GXSTAT busy 비트 `0x08000000`을 기다린 뒤 `CLIPMTX_RESULT` `0x04000640`과 `VECMTX_RESULT` `0x04000680`에서
읽어 낸다 [S: `src/matched/G3X_GetClipMtx.c`, `src/matched/G3X_GetVectorMtx.c`; source account: `src/matched/G3X_GetClipMtx.c`,
`src/matched/G3X_GetVectorMtx.c`]. 행렬 스택 레벨은 GXSTAT 비트 `0x1f00`(위치)과
`0x2000`(투영)이고, 오류 비트는 `0x4000`이다
[S: `src/matched/G3X_GetMtxStackLevelPV.c`, `src/matched/G3X_GetMtxStackLevelPJ.c`; source account: `src/matched/G3X_GetMtxStackLevelPV.c`, `G3X_GetMtxStackLevelPJ.c`].
`NNS_G3dGetCurrentMtx` `0x021073a8`은 그 읽기 경로를 사용한다: 플러시하고, 포트
`0x04000440`/`0x04000444`/`0x04000454`/`0x04000448`을 통해 단위 투영을 밀어 넣고,
결과 레지스터를 폴링한다 [S: `src/matched/NNS_G3dGetCurrentMtx.c`; source account: `src/matched/NNS_G3dGetCurrentMtx.c`].

### VRAM

아홉 개의 VRAM 뱅크는 `autoload_2`의 `GX_SetBankFor*` 계열이 할당하며, 모두
`0x04000240`-`0x04000249`의 `VRAMCNT` 바이트에 쓴다(인덱스 7은 `WRAMCNT`이며 건너뛴다):
`GX_SetBankForBG` `0x02111740`, `ForOBJ` `0x021115d4`, `ForSubBG` `0x02110e4c`, `ForSubOBJ`
`0x02110dd0`, `ForTex` `0x02111204`, `ForTexPltt` `0x02111110`, `ForBGExtPltt` `0x021114c0`,
`ForOBJExtPltt` `0x02111408`, `ForClearImage` `0x02110fd0`, `ForLCDC` `0x02110ef8`, `ForARM7`
`0x02110f18` [S: `src/matched/GX_SetBankForBG.c`; source account: `config/adm-kr/arm9/autoload_2/symbols.txt`;
`src/matched/GX_SetBankForBG.c` and siblings]. `GX_VRAMCNT_SetLCDC_` `0x021119f8`은
뱅크를 LCDC 모드에 두는 루틴이며, 그 상수가 각 뱅크의 LCDC 별칭을 알려 준다:
`0x06800000`, `0x06820000`, `0x06840000`, `0x06860000`, `0x06880000`, `0x06890000`, `0x06894000`,
`0x06898000`, `0x068A0000` [S: `src/matched/GX_VRAMCNT_SetLCDC_.c`; source account: `src/matched/GX_VRAMCNT_SetLCDC_.c`].

대량 업로드는 고정 목적지로의 DMA 복사이다: OAM은 `0x07000000`(엔진 A)과
`0x07000400`(엔진 B); BG 팔레트는 `0x05000000` / `0x05000400`; OBJ 팔레트는 `0x05000200`
/ `0x05000600`; OBJ 타일은 `0x06400000` / `0x06600000`
[S: `src/matched/GX_LoadOAM.c`, `src/matched/GXS_LoadOAM.c`, `src/matched/GX_LoadBGPltt.c`, `src/matched/GX_LoadOBJPltt.c`, `src/matched/GXS_LoadBGPltt.c`, `src/matched/GXS_LoadOBJPltt.c`, `src/matched/GX_LoadOBJ.c`, `src/matched/GXS_LoadOBJ.c`; source account: `src/matched/GX_LoadOAM.c`, `GXS_LoadOAM.c`, `GX_LoadBGPltt.c`, `GX_LoadOBJPltt.c`,
`GXS_LoadBGPltt.c`, `GXS_LoadOBJPltt.c`, `GX_LoadOBJ.c`, `GXS_LoadOBJ.c`].

### 2D

디스플레이 모드는 `DISPCNT` `0x04000000`에 대한 `GX_SetGraphicsMode` `0x0211062c`와
`DISPCNT_B` `0x04001000`에 대한 `GXS_SetGraphicsMode` `0x02110610`으로 설정된다; 서브 엔진에는
`bg0_2d3d`나 디스플레이 모드 필드가 없으므로 그 마스크는 세 개의 BG 모드 비트뿐이다
[S: `src/matched/GX_SetGraphicsMode.c`, `src/matched/GXS_SetGraphicsMode.c`; source account: `src/matched/GX_SetGraphicsMode.c`, `src/matched/GXS_SetGraphicsMode.c`]. `GX_DispOn`과
`GX_DispOff`는 `DISPCNT` 비트 16-17을 토글한다 [S: `src/matched/GX_DispOn.c`, `src/matched/GX_DispOff.c`; source account: `src/matched/GX_DispOn.c`, `GX_DispOff.c`].
각 BG 레이어의 캐릭터 및 스크린 베이스 포인터는 `0x02111b00`-`0x02111f68`의 `G2_GetBGnCharPtr` /
`G2_GetBGnScrPtr` 쌍과 그 `G2S_` 서브 엔진 쌍둥이에서 온다
[S: `src/matched/GX_SetGraphicsMode.c`, `src/matched/GXS_SetGraphicsMode.c`, `src/matched/GX_DispOn.c`, `src/matched/GX_DispOff.c`; source account: `config/adm-kr/arm9/autoload_2/symbols.txt`].

어느 엔진이 어느 물리 화면을 구동하는지는 `0x04000304`의 `POWCNT1` 비트 15이다: `POWCNT1 =
0x020f`이면 엔진 A가 **아래** 화면을 구동하고, `0x820f`이면 위 화면을 구동한다
[H: source account: `docs/kb/port/render.md`, screen ownership; the value is logged between PAD samples 6723 and
6726 on the custom START9000 recipe; direct ROM-source provenance unresolved]. `func_020540e4`가 게임 쪽 쓰기자로,
`(POWCNT1 & 0xfffffdf1) | 0x20e`를 계산한다 [S: `src/matched/func_020540e4.c`; source account: `src/matched/func_020540e4.c`].

게임이 실제로 사용하는 2D 레이어는 인터프리터 경로에서 측정되었다. 마을의 위
화면은 BG 모드 1의 엔진 B이고 BG3는 어파인 레이어, `BG3CNT = 0x6f02`이다 — 그 레이어가
하늘이다 [E: `docs/log/cycle40-keyboard-gate-probe.md` SKY40, `tap-D57` ; `scratchpad/cycle40/runs/tap-D57`]. 어파인 배경은
바이트 스크린 엔트리를 가진 8bpp이고, 크기는 128에서 1024 정사각형, 랩 비트는 13, PA..PD는 8.8이며
20.8 기준점은 BG2는 `+0x20`, BG3는 `+0x30`에 있다
[H: source account: `port/render/nds2d.c`, `draw_affine_bg`, written to GBATEK; H: historical measurement account: same run; direct ROM-source provenance unresolved].

### 씬 전환은 페이드가 아니라 WINDOW이다

측정됨(FADE52). 건물을 나가거나 문을 통과할 때 게임은 같은 `DISPCNT` 쓰기에서 BG2와
window 0을 활성화하고, 두 엔진 모두에서 `WININ = 0x3f3b` / `WINOUT = 0x0024`를 설정한다:
**window 0 안에서는 BG2를 제외한 모든 레이어가 그려지고, 바깥에서는 BG2만 그려진다.** BG2는
검은 덮개이고 window 0은 그림이 보이는 구멍이다. 전환은 그 구멍을 닫는다. 그동안 두 엔진의
`BLDY`와 `MASTER_BRIGHT`는 `0000`으로 유지되며, 원본 자체의 열별 휘도는 가운데에서 켜진
값을 유지하고 바깥 열은 정확히 0이 된다 [E: `docs/log/cycle41-gameplay.md` FADE52; `docs/kb/hybrid/render-fixes.md` P15 ; `scratchpad/fade52/RECEIPTS.md`].

**구멍은 IRIS이며, `WIN0H`는 한 개가 아니라 프레임마다 192개 값을 취한다** (WINDOW53;
FADE52의 "약 10개 열씩 열세 단계, 메인 루프 본체마다 한 단계"라는 측정은 아이리스의 가장
넓은 선을 지나는 애니메이션을 측정한 것이므로 여기서 정정한다). `func_02041f6c`가
`func_0205c024(&data_021c75cc, func_02042154, func_02042120, 0)`을 통해 함께 등록한 두
콜백이 전환 전체에서 이 레지스터를 소유한다:

* **`func_02042120`, VBlank 쪽**: 두 엔진의 `WIN0H`는 `*(u16 *)(*(u32 *)
  0x021c75b4)` — 테이블의 **첫 번째** 항목 — 을 취하고, `WIN0V`는 `0x00c0`을 취한다;
* **`func_02042154`, HBlank 쪽**: 두 엔진의 `WIN0H`는 `table[VCOUNT]`를 취하고, 96번
  라인을 기준으로 대칭시킨다(`if (y >= 0x60) y = 0xbf - y`). 그리고 DISPSTAT 비트 1,
  HBlank 플래그가 설정된 경우에만 동작한다.

테이블은 96개 하프워드이며 `0x021c75e8`과 `0x021c76a8`에서 이중 버퍼링된다. 현재 테이블은
`0x021c75b4`의 포인터가 가리키고, 사용할 버퍼는 `0x021c75ac`의 비트 1이 선택한다.
DS에서 현재 테이블은 한 번에 최대 **서로 다른 값 57개**를 담으며, 가장 넓은 라인이 스크린샷의
점등 열 범위를 결정한다. 마을 회관을 나가는 프레임 49,611에서는 `0x0cf4`(X1 = 12,
X2 = 244, 점등 범위 12..243)이고, 49,640에서는 `0x7789`(점등 범위 119..136)이다. 이는
FADE52가 열 단위로 기록한 행을 열에 대응시킨 값이다 [E: `docs/log/cycle41-gameplay.md` WINDOW53 W53-5; current receipt locator: `scratchpad/window53/RECEIPTS.md`].
`func_02041e48`은 `0x021c75bc`의 애니메이션 위치에서 테이블을 다시 만든다: `0`이면
`0x00ff`(완전히 열림)를 채우고, `0x1000`이면 `0x8080`(닫힘)을 채운다. 그 사이에서는
수직 반지름이 `(0x1000 - pos) * 0xa0 >> 12`인 타원이며, 안쪽의 각 선은
`t = 0x80 - (FX_Sqrt(...) >> 12)`를 계산하여 `(t << 8) | (0x100 - t)`로 쓴다 —
구조상 x = 128을 기준으로 대칭이다. `func_02041d14`는 닫기를 시작하고(`pos = 0`,
`step = FX_Div(0x1000, frames << 12)`을 `0x021c75c0`에서), `func_02041c88`은 열기를
시작한다. `0x021c75b8`의 상태 바이트는 0 유휴 / 1 여는 중 / 2 완료 / 3 닫는 중이다.

**포트는 이를 재현한다** (IRIS54). 두 호스트 결함 때문에 재현하지 못했지만 이제 둘 다
수정되었다. `port/interp/interp_boot.c`가 DISPSTAT 비트 1을 올리지 않아 HBlank 쪽이
쓰기 없이 반환했고 하나의 `WIN0H`가 192개 스캔라인 전체를 덮었다. 또한
`port/shim/math/divider.c`의 `FX_SQRT_SHIFT`가 SDK의 10이 아니라 1이어서 모든 `FX_Sqrt`가
512배 너무 크게 돌아왔고, `func_02041e48`은 모든 내부 라인에서 "이 라인은 화면 전체를
가로지른다" 분기로 들어갔다. 수정 후 측정한 결과, 마을 회관을 나가는 일곱 프레임에서
포트의 스캔라인별 `WIN0H`는 192개 라인에 걸쳐 두 엔진 각각 43, 48, 57, 50, 25, 25,
13개의 서로 다른 값을 담았으며, 일곱 프레임 모두 그 실행 목록이 DS의 현재 테이블과
정확히 일치했다. DS의 열별 점등 범위 열네 개도 순서대로 모두 나타났다
[E: `docs/log/cycle41-gameplay.md` IRIS54 I54-5, I54-6; `docs/kb/hybrid/render-fixes.md`
P17, P18; current receipt locator: `scratchpad/iris54/RECEIPTS.md`].

게임의 지연된 디스플레이 레지스터 플러시 `func_02001ecc`(`0x02001ecc`)
(`src/matched/func_02001ecc.c`)는 `0x04000040`..`0x0400004b`와 블렌드 쌍을
`0x0213fe74` / `0x0213fe94`의 RAM 섀도에서 가져오며, 더티 플래그는
`0x0213fe85` / `0x0213fe86`에 있다. `func_02001cc4`는 유일한 WIN0-A 세터로
(`0x0213fe92`의 `X1`, `0x0213fe94`의 `X2`, 더티 비트 `0x0010`), 두 생산자 모두에서
전환마다 시작 시 `0x00ff`를 **정확히 한 번** `WIN0H`에 쓴다. 아이리스가 진행되는 동안
섀도는 다시 움직이지 않는다. 페이드 투 블랙 *도우미* `func_02001aac` — 두 엔진에서
플레인 `0x3f`와 함께 `G2x_SetBlendBrightness_`를 사용하는 것 — 는 전환 끝에 쓰이는
별도 경로(`BLDCNT = 0x00ff`, `BLDY = 0x10`)이며 램프에는 사용되지 않는다.

### 포트의 렌더러는 무엇을 하고, 그 비용은 얼마인가

위의 모든 것은 ROM이 프로그래밍하는 하드웨어이다. `port/render/`는 그에 응답하는
소프트웨어이다: `nds2d.c`는 두 2D 엔진을 합성하고, `nds3d.c`는 지오메트리 FIFO를 디코드하며, `raster3d.c`는
래스터화한다. 2026-09-09에 두 유닛이 그 렌더러를 처음으로 측정했다 -- 하나는 속도,
하나는 충실도 -- 그리고 둘을 판정한 규칙은 서로 다르며, 둘 다 알아 둘 가치가 있다.

**속도(PERF42, `fbfc987d`): 포트는 `-O0`으로 빌드되고 있었다.** `port/tools/link.py`의
`GEN_FLAGS`에는 `-O` 플래그가 전혀 없었으므로, 포트 전체가 clang의 기본값으로 컴파일되고 있었다.
`port/render/`에만 `-O2 -fwrapv -fno-strict-aliasing`을 추가하자 링크 한 번으로 draw 단계가 26.7 ms에서
7.25 ms로 내려갔고, 바이트 단위로 동일했다; 인터프리터와 심(shim)은 자체 정확성 하니스가
생길 때까지 `-O0`에 머문다 [H: log/source account: `docs/kb/hybrid/render-perf.md` section 4a; receipt provenance unresolved]. 나머지
이득은 정확성 논증을 붙여 픽셀별 루프에서 작업을 걷어 내는 데서 왔다: 스팬 속성
델타를 루프 밖으로 끌어올리고, 안전이 증명되는 곳에서는 32비트 곱셈을 쓰고, 속성은 필요한 곳에서만
보간하고, 스팬 파라미터는 이월 장제법으로, 깊이 테스트는 `z >= D*q`로, VRAMCNT
디코드는 검증 뒤에 구성당 한 번만 해석하고, 팔레트는 레이어당 한 번만
변환하고, 텍스트 BG는 타일 단위로, 색상 효과는 라인 단위로 처리하고 효과가 없는 곳에서는 건너뛴다
[H: log/source account: `docs/kb/hybrid/render-perf.md` section 4a, sections 4b-4d; receipt provenance unresolved].

이 유닛을 판정한 규칙은 충실도 쪽보다 엄격하다: **성능 변경은 픽셀을 단 하나도
움직여서는 안 된다** -- 상관이 아니라 SHA-256 동일성이다. OFF 레시피의 31 프레임은
**일곱 번의 중간 링크 하나하나에서** 31/31을 통과했으므로, 거부가 있었다면 여러 변경의 더미가 아니라
그 변경 자체를 지목했을 것이고, 마을 레시피는 비페이싱 11/11, 페이싱 11/11을 통과했다
[H: log/source account: `scratchpad/perf42/exactness-off-*.json`, `exactness-town.json`,
`exactness-town-paced.json`; receipt provenance unresolved].

| 레시피 | draw 이전 | draw 이후 | 비페이싱 fps 이전 -> 이후 |
|---|---|---|---|
| OFF(택시), 프레임 4,200..9,000 | 26.45 ms | **7.29 ms** | 30.0 -> **77.1** |
| 마을, 프레임 27,000..30,000 | 22.57 ms | **6.17 ms** | 34.8 -> **91.7** |

[E: `docs/kb/hybrid/render-perf.md` section 5; `scratchpad/perf42/runs/`.] 페이싱된 라이브 실행은
창을 연 채로 59.82 Hz를 유지하며, `town-paced`의 11 프레임은 비페이싱 실행의 것과 SHA-256이
동일하다 -- 그러므로 페이싱은 프레임이 언제 일어나는지를 바꾸지, 그 내용을 바꾸지는 않는다 [E: `docs/kb/hybrid/render-perf.md` section 5; `scratchpad/perf42/runs/`.].

**계측 도구는 `ACWW_FRAMETIME=1`이며, 이제 단계(PHASE)를 지목한다.** 이미
`draw / blit / game / other`를 출력하고 있었다; 이제는 2D 엔진별, 600 프레임마다 `hblank`, `fill`,
`text`, `affine`, `3d`, `obj`, `fx`, `lit`을 출력하고, 여기에 3D 래스터라이저의 다섯 하위 단계
(`clear`, `opaque`, `trans`, `count`, `merge`)를 폴리곤 수, 방문한 스팬 픽셀 수, 기록한 스팬 픽셀
수와 함께 출력한다 [H: log/source account: `docs/kb/hybrid/render-perf.md` section 2; receipt provenance unresolved]. 그 보고서는 **이미 공개된
해석 하나를 정정했다**: LIVE41의 "2D 렌더러가 다음 성능 목표다"는 어느 렌더러인지를
틀렸다 -- 26.5 ms 중 21.1 ms가 3D 래스터라이저였다 [H: log/source account: `docs/kb/hybrid/render-perf.md` section 2, section 3; the LIVE41 numbers are
in `docs/kb/hybrid/recipes.md` section 7b, kept as that unit's before-column; receipt provenance unresolved]. 작업 이후에도 여전히 draw의
86%이다: 317,427 스팬 픽셀에 6.29 ms이니 스팬 픽셀당 약 20 ns이다
[H: log/source account: `docs/kb/hybrid/render-perf.md` section 2, section 6; receipt provenance unresolved].

**충실도(RENDER42, `b1080164`): 규칙 둘을 정정했고, 하나는 효과 없음으로 측정되었다.** 여기서의 통과 규칙은
**OFF 레시피가 31 프레임 중 어느 하나에서도 ncc를 잃어서는 안 된다**는 것이다 -- 평균을
올리면서 한 프레임을 낮추는 변경은 거부된다 [H: log/source account: `docs/kb/hybrid/render-fidelity.md` section 1; receipt provenance unresolved].

- **P10 -- 색상 특수 효과는 5비트 영역에서 동작한다.** GBATEK의 블렌드 및 밝기
  공식은 31에서 클램프되는 5비트 강도이다; `chan_mix`와 `brighten`은 `bgr555()`가 확장한
  8비트 채널 위에서 동작하며 255에서 클램프하고 있었는데, 이는 블렌드된 픽셀마다 채널당 최대 7/255만큼
  체계적으로 높은 결과이다. 이제는 `>>3`으로 다시 내려가서 연산하고, 31에서 클램프한 뒤
  다시 확장한다 [P: GBATEK, *LCD I/O Color Special Effects*;
  E: `../audits/hardware-services.md` P10]. **이 레시피들이 도달하는 모든 오라클 프레임에서 효과 없음(INERT)으로
  측정됨** -- 이들이 만나는 효과 상태는 두 영역이 일치하는 것들이다 -- 그러므로
  픽스처가 근거의 전부이며, 두 영역을 갈라놓는 사례 셋이 추가되었다
  (파랑 위 빨강에 EVA=9/EVB=7은 8비트 연산으로는 143, 하드웨어 연산으로는 **140**):
  `port/tools/test_nds2d_blend.py`, 27개 검사, 보정 2건 검출
  [H: log/source account: `docs/kb/hybrid/render-fidelity.md` section 3; receipt provenance unresolved].
- **F6 -- 텍스처 좌표 변환 모드 2와 3.** 둘 다 원시 10비트 법선(시프트 21)과
  20.12 위치(시프트 24)에 대한 3항 형식이므로, 텍스처 행렬의 이동
  행은 결코 들어오지 않는다; 포트는 `v[3] = FX_ONE`과 순 시프트 20으로 전체 4x4를,
  NORMAL 명령이 이미 `<< 3`으로 스케일한 법선에 대해 돌리고 있었다 -- 16배 크고, 있어서는 안 될
  이동이 있었다. **OFF 프레임 6,000의 458개 폴리곤 중 정확히 하나가 모드 2를 쓴다**: 택시 벽의
  액자 그림, 화면 x 164..195의 32x32 포맷 5 머티리얼이다. 이것이 색 줄무늬가 있는 검정으로
  그려졌는데, 16배 큰 좌표가 32x32 이미지에서 샘플링해 오는 것이 바로 그것이다; 이제는
  오라클이 그리는 풍경을 그린다 [E: `scratchpad/render42/picture-frame-before-after.png`;
  `../audits/3d-engine.md` F6]. OFF 전체 프레임: 평균 ncc-top **0.9774 -> 0.9807**, mae
  7.43 -> 7.31, **나빠진 프레임 0**; 마을 `tap-24700` 0.9987 -> 0.9991
  [E: `scratchpad/render42/off-final.json`, `tapfinal-24700.json`]. 픽스처:
  `port/tools/test_nds3d_texmtx.py`, 5개 검사, 보정 2건, 그중 하나는 F6 이전의
  답을 assert하므로 반드시 검출되어야 한다.
- **수치로 거부되었고, 구현된 채 꺼져 있음**: `ACWW_SAMPLE_INT=1`, 픽셀 중심이 아니라
  두 에뮬레이터가 하듯 픽셀의 정수 좌표에서 샘플링한다. 평균 mae를
  7.31 -> 6.66으로, ncc-top을 0.9807 -> 0.9833으로 옮기지만, **31 프레임 중 9개에서 전체 프레임
  ncc를 잃는다**. 이는 한 쌍의 절반이다 -- 에뮬레이터들은 VERTEX 위치도 양자화한다 -- 그러므로
  다음 실험은 완화된 임계값이 아니라 나머지 절반이다 [H: log/source account: `off-sampleint` vs `off-final`,
  `docs/kb/hybrid/render-fidelity.md` section 4; receipt provenance unresolved]. P11(밝기 경로 위의 반투명
  OBJ)은 두 레시피 모두에서 모집단 **0**으로 측정되었고 의도적으로 만들지 않았다
  [H: log/source account: `../audits/hardware-services.md` P11; receipt provenance unresolved].
**BACKDROP은 거의 모든 스캔라인(SCANLINE)마다 바뀌며, 그것이 하늘의 그라디언트이다**
[E: RENDER43, `ACWW_REGDUMP=37500` on the two-tap town recipe,
`scratchpad/render43/regdump-town37500.txt`]. 마을 프레임 37,500에서 엔진 B의 BG 팔레트 엔트리 0은
라인 0의 `0x7084`에서 라인 176의 `0x79e4`까지 열두 단계로 변한다 — 5비트 초록 4 → 15, 빨강은 4로
고정, 파랑 28 → 30 — 반면 엔트리 1..31은 결코 바뀌지 않는다. 이는 팔레트 DMA가 아니라 ROM의 HBlank 핸들러에서
라인마다 하프워드 하나를 쓰는 것이다. `BLDCNT = 0x2042`는 BG1을 첫 번째 대상으로,
BACKDROP을 두 번째 대상으로 지정하고, `BLDALPHA`는 라인 150..167에 걸쳐 `0x0010` → `0x1000`으로 램프하므로,
하늘 레이어는 지평선을 향해 그 라인별 백드롭으로 페이드된다. 프레임 끝의 팔레트로 이
화면을 그리는 것은 무엇이든 평평한 하늘을 얻는다
[H: source account: `port/render/nds2d.c`, `capture_line_regs` and `fill_backdrop`;
`docs/kb/hybrid/render-fixes.md` fix P14; direct ROM-source provenance unresolved].

**3D 레이어는 BG0이며 BG0HOFS로 스크롤된다** — 512픽셀 영역으로, 256은 이미지, 그다음 256은
투명이다 [H: host/prose inference from GBATEK, DS 3D Final 2D Output; `port/render/raster3d.c`,
`acww_nds3d_compose_x`; verify against the ROM function or symbol table and this page's recipe]. 측정됨: ACWW는 OFF 프레임 6,000과 마을
37,500에서 `BG0HOFS = 0`을 쓰므로, 두 증명 세트 중 어느 쪽이 도달하는 모든 프레임에서 효과가 없다.

**SWAP_BUFFERS는 VBlank까지 실행되지 않으며 그때까지 지오메트리 엔진을 정지시킨다**
[H: source account: GBATEK, DS 3D Display Control; direct ROM-source provenance unresolved]. 따라서 한 프레임은 최대 한 번의 스왑만 담는다; 포트는 예전에
모든 스왑을 존중했고, 에이커 지면 탈락은 한 프레임 안의 열아홉 번 스왑이 열여덟 개의
디스플레이 리스트를 버리는 것이었다 [H: host/prose inference from `port/render/nds3d.c`, `case 0x50`;
`docs/kb/hybrid/render-fixes.md` fix F15; verify against the ROM function or symbol table and this page's recipe].

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
| `0x04000000` / `0x04001000` | `DISPCNT` A / B | `GX_SetGraphicsMode`, `GX_DispOn/Off` | LCD [S: `src/matched/GX_SetGraphicsMode.c`; source account: `src/matched/GX_SetGraphicsMode.c`] |
| `0x04000008`+2n | `BGnCNT` | 게임의 레이어 설정 | 2D 엔진 [H: source account: `port/render/nds2d.c`; direct ROM-source provenance unresolved] |
| `0x04000050` / `0x52` / `0x54` | `BLDCNT` / `BLDALPHA` / `BLDY` | 게임 | 색상 특수 효과 [H: source account: `port/render/nds2d.c`; direct ROM-source provenance unresolved] |
| `0x04000060` | `DISP3DCNT` | `G3X_Init`, `G3X_SetFog` | 3D 엔진 [S: `src/matched/G3X_Init.c`; source account: `src/matched/G3X_Init.c`] |
| `0x04000240`-`0x04000249` | `VRAMCNT` (인덱스 7 = `WRAMCNT`) | `GX_SetBankFor*` | 메모리 컨트롤러 [S: `src/matched/GX_VRAMCNT_SetLCDC_.c`; source account: `src/matched/GX_VRAMCNT_SetLCDC_.c`] |
| `0x04000280`-`0x040002bf` | 하드웨어 나눗셈 / 제곱근 | `FX_Div`, `FX_Sqrt` | 동일 [H: log/source account: `docs/log/...` GX40; receipt provenance unresolved] |
| `0x04000304` | `POWCNT1`; 비트 15가 어느 엔진이 위인지 바꿈 | `func_020540e4` | LCD들 [S: `src/matched/func_020540e4.c`; source account: `src/matched/func_020540e4.c`; H: `docs/kb/port/render.md`] |
| `0x04000330`/`0x350`/`0x354`/`0x356`/`0x358`/`0x35c`/`0x360`/`0x380` | 엣지, 클리어 색상, 클리어 깊이, 클리어 이미지 오프셋, 안개 색상, 안개 오프셋, 안개 테이블, 툰 테이블 | `G3X_*` 설정자 | 3D 엔진 [S: `src/matched/G3X_Init.c`; source account: `src/matched/G3X_Init.c`] |
| `0x04000400`-`0x0400043f` | 패킹된 지오메트리 FIFO(64바이트 전부가 같은 포트) | `NNS_G3dGeBufferOP_N`, `GX_SendFifo48B` | 지오메트리 엔진 [S: `src/matched/NNS_G3dGeBufferOP_N.c`; source account: `src/matched/NNS_G3dGeBufferOP_N.c`; `port/render/gxfifo.c`] |
| `0x04000440`-`0x040005c8` | 45개의 개별 명령 포트, `0x04000440 + (op-0x10)*4` | `G3_*`, `G3X_*` | 동일 [S: `src/matched/G3_LoadMtx43.c`; source account: `src/matched/G3_LoadMtx43.c`; `port/render/gxfifo.c`] |
| `0x04000600` | `GXSTAT`: busy `0x08000000`, 스택 오류 `0x8000`, 스택 레벨 `0x1f00`/`0x2000`, FIFO IRQ `0xc0000000` | `G3X_Init`, `G3X_ResetMtxStack` | `G3X_GetClipMtx`, 대기 루프들 [S: `src/matched/G3X_Init.c`; source account: `src/matched/G3X_Init.c`] |
| `0x04000640` / `0x04000680` | `CLIPMTX_RESULT` (16 fx32) / `VECMTX_RESULT` (9 fx32) | 지오메트리 엔진 | `G3X_GetClipMtx` / `GetVectorMtx` [S: `src/matched/G3X_GetClipMtx.c`; source account: `src/matched/G3X_GetClipMtx.c`] |
| `0x05000000`/`0x200`/`0x400`/`0x600` | BG-A, OBJ-A, BG-B, OBJ-B 팔레트 | `GX_LoadBGPltt` 계열 | 2D 엔진 [S: `src/matched/GX_LoadBGPltt.c`; source account: `src/matched/GX_LoadBGPltt.c`] |
| `0x06400000` / `0x06600000` | OBJ 타일 공간 A / B | `GX_LoadOBJ`, `GXS_LoadOBJ` | 2D 엔진 [S: `src/matched/GX_LoadOBJ.c`; source account: `src/matched/GX_LoadOBJ.c`] |
| `0x06800000`+ | LCDC 뱅크 별칭 | `GX_VRAMCNT_SetLCDC_`, `GX_LoadTex` | 텍스처 유닛 [S: `src/matched/GX_VRAMCNT_SetLCDC_.c`; source account: `src/matched/GX_VRAMCNT_SetLCDC_.c`] |
| `0x07000000` / `0x07000400` | OAM A / B, 각 128 엔트리 | `GX_LoadOAM`, `GXS_LoadOAM` | 2D 엔진 [S: `src/matched/GX_LoadOAM.c`; source account: `src/matched/GX_LoadOAM.c`] |

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
O: `scratchpad/oracle/off`, the same scene in DeSmuME ; `scratchpad/cycle40/runs/off-D51`]. 프레임 37,800에는 마을 회관 위의 파란
하늘에 구름이 있다 [E: `docs/log/cycle40-keyboard-gate-probe.md` GX40, run `off-D51`;
O: `scratchpad/oracle/off`, the same scene in DeSmuME log, SKY40, run `tap-D57` ; `scratchpad/cycle40/runs/off-D51`, `scratchpad/cycle40/runs/tap-D57`]. 프레임 37,500에는 오버레이
5, 36, 54, 120, 117이 로드된 마을이 있고, 48,000프레임이 811초에 실행된다
[E: `scratchpad/cycle40/runs/tap-D56`, per the same log, TOWN40].

이 페이지에 특화된 계측이 둘 있다. `ACWW_TEXTRACE_FRAME`을 십진수
`ACWW_TEXTRACE_INDEX`와 함께 쓰면 2,048 폴리곤 리스트 범위 안에서 한 폴리곤의 텍스처 출처를 덤프한다
[H: host/prose inference from `docs/kb/port/render.md`, texture provenance; verify against the ROM function or symbol table and this page's recipe]. `ACWW_OAMDUMP=<frame>`은 두 OAM 테이블을 모두
덤프하며 `ACWW_TRACE_STATE`에 게이트되지 않는다 [H: host/prose inference from `docs/kb/port/render.md`, OAM cursor table; verify against the ROM function or symbol table and this page's recipe].
`ACWW_NOBLEND=1`은 색상 특수 효과를 비활성화하여 블렌드를 분리할 수 있게 한다
[H: host/prose inference from `port/render/nds2d.c`; verify against the ROM function or symbol table and this page's recipe].

## 가설

- **3D 레이어는 오라클의 것보다 약 1픽셀 위·왼쪽에 놓이며, 이는 텍스처 대수가 아니라
  채움 규칙(fill rule)이다.** 택시의 위 화면에 대한 사분면별 서브픽셀 피팅은 네 사분면 모두에서
  같은 이동을 준다 -- dx +1.00, dy +1.00..+2.00 -- 이는 스케일이 아니라 이동이며,
  OFF 프레임 6,000에서 mae를 15.08 -> 7.03으로 옮긴다; 2D인 아래 화면은
  (0, 0)에 피팅되므로, 오프셋은 3D 레이어만의 것이다. 차이 이미지는 텍스처가 입혀진 모든 모서리의
  얇은 윤곽선인데, 이는 서브픽셀 변위의 모습이지 틀린
  색상의 모습이 아니다 [E: `scratchpad/render42/shiftfit.py`,
  `scratchpad/render42/off006000-top-A-B-D.png`]. 에뮬레이터 쌍의 나머지 절반 -- 버텍스 위치를
  정수 픽셀로 양자화하기 -- 를 같은 31 프레임 규칙 아래에서 측정하여 해결하며,
  레이어를 이동시켜서는 안 된다(`ACWW_3DBIAS_X/_Y`가 그렇게 하는데 2-3 프레임에서 ncc를 잃는다).
- **마을의 하늘에는 수직 그라디언트가 없으며, 전체 프레임 렌더러는 그 이유를 볼 수
  없을지 모른다.** 프레임 37,500에서 오라클의 하늘은 초록이 화면 위쪽의 5비트 4에서
  지평선 근처의 9까지 램프하며 파랑은 28 -> 29, 빨강은 4로 고정이다; 포트의 하늘은 어디서나 평평한 (4, 4, 28)
  이다 -- 오라클의 맨 위 행이 화면 전체에 유지된 것이다. 빨강이 동일하다는 것은 세 채널을 모두
  움직이는 밝기 효과를 배제한다; 그 모양은 대략 (4, 31, 31)에 대한 알파 블렌드이거나,
  라인별 팔레트이다 [O: `scratchpad/render42/d63-37500.png`]. `capture_line_regs`는
  이미 어파인 및 효과 레지스터를 위해 ROM의 HBlank 핸들러를 라인마다 한 번 실행하지만
  팔레트는 캡처하지 않는다. 코드 변경이 아니라 계측 도구로 먼저 해결한다: 선택한 프레임에서 BG
  팔레트 엔트리 0과 BLDCNT/BLDALPHA를 라인별로 기록한다. (하늘은 픽셀 위치가 아니라 구조로
  비교한다: 포트가 대화 한 단계 앞서 있으므로 구름 위치가 다르다.)
- **에이커 지면이 간헐적으로 탈락하며, 그동안에도 3D 파이프라인은 돌고 있다.**
  여섯 번의 GAMEPLAY42 실행에서 1,160개의 아래 화면 중 17개가 45-99%가 단일 색상 `0x2184FF` --
  3D 레이어의 클리어 파랑 -- 이며, 때로는 건물과 플레이어가 그 틈 위에 여전히 올바르게
  그려져 있고, 하나 더는 99%가 평평한 짙은 초록이다; 문 전환의 검정은 별개이며
  예상된 것이다. 320 프레임 인스턴스 도중의 정지 덤프는
  `G3dDrawInternal_Loop_`, `NNS_G3dGeBufferOP_N`, `NNSi_G3dFuncSbc_MAT`, `NNSi_G3dFuncSbc_SHP`가
  맨 위에 있는 HOLD 프로파일이다 -- **파이프라인은 먹이를 받고 있는데 화면에는 아무것도 도착하지 않는다** -- 그리고
  `unimplemented`도, 폴트도 없고, 이후에는 정상적으로 플레이된다
  [E: `docs/log/cycle41-gameplay.md` GP42-6; `scratchpad/gameplay42/ground-gap.png`]. 에이커 지형(TERRAIN)에서
  먼저 실패하고 때로는 씬 전체를 잃는다. 재현되는 한 프레임 범위에 대한 오라클 대조 조건과,
  틈 전후에 걸친 에이커 자체 폴리곤의 GX 제출 수 세기로 해결한다.
- **클리어 이미지(후면 평면 비트맵) 경로는 이 게임에서 절대 사용되지 않는다.** `DISP3DCNT` 비트 14는
  포트에서 기록만 되고 구현되지 않았지만, `func_ov001_0222e4dc`는
  `GX_SetBankForClearImage`를 호출한다 [S: `src/matched/GX_SetBankForClearImage.c`; source account: `port/render/raster3d.c`; `src/matched/GX_SetBankForClearImage.c`].
  긴 마을 실행과 WFC 화면 실행에 걸쳐 `DISP3DCNT` 비트 14를 로깅하여 해결한다.
- **확장 회전/확대 및 대형 비트맵 배경(BG 모드 3-6)은 사용되지 않는다.** 포트는 이를 건너뛰며
  지금까지 어떤 씬도 필요로 하지 않았다 [H: source account: `port/render/nds2d.c`, K_EXT / K_LARGE notes; direct ROM-source provenance unresolved].
  인터프리터 레시피들에 걸쳐 이를 선택하는 `BGnCNT` 값에 대해 assert하여 해결한다.
- ~~윈도잉(`WIN0`/`WIN1`/`OBJWIN`), 모자이크, 확장 팔레트는 사용되지 않는다.~~ 분리해야 한다:
  window-0 구성 요소는 **폐기됨(RETIRED)** — 모든 씬 전환은 아이리스로서 window 0을 닫고,
  스캔라인별로 그리며, FADE52/IRIS54 이후 포트는 WIN0/WIN1을 그린다(위의 window 섹션)
  [E: `scratchpad/iris54/RECEIPTS.md`; log: `docs/log/cycle41-gameplay.md` FADE52, IRIS54].
  OBJWIN은 여전히 그리지 않는다(FADE52의 미해결 항목). 모자이크와 확장 팔레트는 이전
  상태를 유지한다: 기록됨, 미구현, 어떤 씬도 지금까지 필요로 하지 않았다
  [H: source account:
  `port/render/nds2d.c`]. `DISPCNT & 0x8000`(OBJWIN),
  `DISPCNT & 0xC0000000`, 그리고 모자이크 비트에 대해 assert하여 해결한다.
- **`BOX_TEST`, `POS_TEST`, `VEC_TEST`(GX 명령 0x70-0x72)는 게임의 컬링에 중요하다.**
  포트는 셋 모두를 스텁 처리하여 GXSTAT test-busy 비트를 클리어하고 "보임"으로 보고한다
  [H: source account: `port/render/nds3d.c`; direct ROM-source provenance unresolved]. 게임이 `BOX_TEST`로 컬링한다면, 항상 "보임"으로 답하는 것은
  폴리곤을 낭비하지만 보이는 것은 아무것도 바꾸지 않는다; `POS_TEST` 결과로 컬링한다면,
  틀릴 수 있다. 마을 레시피에서 프레임당 0x70/0x71/0x72 제출을 세어 해결한다.
- **포트의 `POWCNT1` 해석은 `0x020f`에서 엔진 A가 아래라는 것이다.** 이는 포트 실행에 대한
  실험적 해석이며 [H: log/source account: `docs/kb/port/render.md`; receipt provenance unresolved], 하드웨어 타이밍에서 같은 스왑을
  확인하는 데 오라클이 사용되지 않았다. 같은 프레임에서 `scratchpad/oracle/*`과 포트 실행 사이의
  두 화면 내용을 비교하여 해결한다.
- **`NNS_G3dGeSendDL`의 256바이트 임계값은 대부분의 셰이프가 DMA가 아니라 버퍼를 거친다는 뜻이다.**
  임계값은 소스에 있다 [S: `src/matched/NNS_G3dGeSendDL.c`; source account: `src/matched/NNS_G3dGeSendDL.c`]; 실제 분포는
  측정되지 않았다. `NNS_G3dDraw1Mat1Shp`에서 `shp->sizeDL`을 히스토그램으로 만들어 해결한다.

## 관련 문서

- `../data/archives.md` — `nsb*` 리소스 컨테이너.
- `../audits/hardware-services.md` P10-P13 — 2D 주장 표와 수정들의 상태 행.
- `../audits/3d-engine.md` — 3D 주장 표와 F1-F13.
- `../audits/night-2026-09-09.md` — RENDER42와 PERF42가 그날 밤의 색인에서 놓인 자리.
- `docs/kb/hybrid/render-perf.md`, `docs/kb/hybrid/render-fidelity.md` — 구현
  페이지: 위의 모든 수치, 단계 표, 두 통과 규칙 전문.
- `../data/rom-layout.md` — 모델, 텍스처, 메뉴 에셋이 있는 곳.
- `text-and-messages.md` — 같은 2D 엔진으로 그려지는 글리프.
- `display-objects.md`, `memory-map.md` — 이 파이프라인을 둘러싼 프레임워크와 아레나.
