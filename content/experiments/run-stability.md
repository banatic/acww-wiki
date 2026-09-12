# 실행 안정성: 종료 코드가 뜻하는 것, 그리고 48,000프레임 실행의 비용
<!-- source: wiki/experiments/run-stability.md -->

**상태: 실행됨, 2026-09-10 (STAB42, `0bc59cc0`).** 다른 두 유닛이 48,000프레임 마을 레시피가
**exit 1**로 일찍 끝나고, 로그가 줄 중간에서 잘리고, 폴트 마커가 없는 것을 보았다 -- 당시에는
사운드 드라이버로 인한 회귀로 읽혔다. 포트가 아니었다. `acww.exe`는 **exit 1로 끝날 수 없다**:
종료 코드 테이블의 어떤 것도 그 값을 만들지 않으며, 만들어내는 모든 값은 먼저 보고서를
출력한다. 종료 상태 1은 프로세스 바깥(OUTSIDE)의 무언가가 `TerminateProcess`를 호출했다는
뜻이다. 같은 빌드에서 48,000프레임 조건 여섯 개가 모두 exit 100에 도달했다.

## 목적

"실행이 일찍 끝났다"는 하나의 관측이 뒤섞어버리는 세 가지를 분리한다: 포트 크래시, 포트
행(hang), 그리고 외부 킬. 이것들이 분리되기 전까지는 모든 긴 실행의 근거가 의심스럽고, 그런
실행을 하는 모든 유닛이 그것을 두고 논쟁해야 한다.

## 레시피

**1단계, 보정, 그리고 결론 전체가 여기에 달려 있다(M1).** 윈도우 프로세스를 죽이는 각
방법이 실제로 무엇을 남기는지를, 가정하는 대신 측정한다:

    python scratchpad/stab42/killcode.py        # writes killcode.json

| 프로세스가 죽은 방식 | 종료 코드 |
|---|---|
| `taskkill /F /PID` -- 세션의 정리 작업이 하는 것 | **1** |
| Python `Popen.kill()` / `terminate()` -- 러너가 타임아웃 시 하는 것 | **1** |
| PowerShell `Stop-Process -Force` | `0xffffffff` |
| fail-fast / 힙 손상 | `0xc0000374` / `0xc0000409` |
| 평범한 `WM_CLOSE` (즉 `/F` 없는(WITHOUT) `taskkill`) | **0**, 세이브 플러시됨 |

[E: `scratchpad/stab42/killcode.json`.] 이에 대해 포트 자체의 테이블은: 폴트는 exit 4,
최종 예외 필터는 8, 스택 오버플로는 4, 정상 정지는 100 -- 그리고 1은 의도적으로 그 안에 없다,
`acww_exit`가 유일한 래퍼이므로 [H: host/prose inference from `port/platform/win32.c`; `port/tools/measure.py`'s
`acww_exit` table; verify against the ROM function or symbol table and this page's recipe]. **로그는 짧은 것이 아니라 잘린 것이다**, `acww_out`이
토큰마다 버퍼 없는 `WriteFile`이기 때문이다: 파일은 죽는 순간까지 완전하며 그 이상은 없다.

**2단계, 조건들.** `scratchpad/stab42/stabrun.py`를 통한 48,000프레임 마을 레시피 실행 여섯 개.
이 스크립트는 stdout을 곧바로(STRAIGHT) 파일로 보내고(파이프는 절대 아님), 어떤 그럴듯한
실행보다 훨씬 높은 데드라인과 그것이 발동했는지를 기록하고, 자식의 피크 워킹셋과 머신 전체의
`acww.exe` 센서스를 1초에 한 번 샘플링하며, 종료 코드를 원시값과(AND) 16진수 둘 다로 보관한다.

## 예상 관측

| 조건 | 오디오 | 종료 | 초 | 피크 워킹셋 |
|---|---|---|---|---|
| `A1` | `ACWW_SND` 미설정 | **100** | 1,358 | 24.8 MB |
| `A2` | `ACWW_SND` 미설정 | **100** | 1,285 | 24.8 MB |
| `B_snd1` | `ACWW_SND=1` (드라이버 + 싱크 스레드) | **100** | 1,342 | 28.8 MB |
| `C_snd1_nothread` | `ACWW_SND=1 ACWW_SND_NOSINK=1` | **100** | 1,340 | 26.4 MB |
| `D1_pair` | 미설정, D2와 함께 실행 | **100** | 1,315 | 25.2 MB |
| `D2_pair` | `ACWW_SND=1`, D1과 함께 실행 | **100** | 1,003 | 26.9 MB |

조건 여섯 개, exit 100 여섯 개, 36-49 fps, 600 KB 로그, 그리고 **모든 조건에서 15장 중 15장의
스크린샷이 바이트 단위로 동일** -- 사운드 드라이버 꺼짐, 켜짐, 스레드 없이 켜짐, 그리고 포트
두 개를 동시에 실행한 상태로, 그동안 내내 머신에 다른 `acww.exe`가 3-4개 있었다. 어느 실행도
`acww: FAULT --`, `ACCESS VIOLATION`, `acww: unimplemented:`, `acww interp: STOP`, `acww: HUNG`을
출력하지 않았다 [E: `scratchpad/stab42/INDEX.md`; per-arm receipts `runs/<name>/stab-receipt.json`].

**그리고 그 증상은 우연히, 직접 재현되었다.** 경합 쌍의 첫 시도는 00:30:00에 오케스트레이터
세션이 재시작되면서 죽었다. 그것이 남긴 것은 정확히 STAB42의 증상이다: 두 로그가 34,201 및
33,601 프레임의 평범한 실행 중간 줄에서 멈추고, 정지 줄 없음, 폴트 없음, 부모도 죽었으므로
영수증 없음, 둘 다 1초 이내에 [E: `scratchpad/stab42/killed-pair-2026-09-10T0030.txt`].

**판별 기준**, 어느 세션이 `taskkill`을 했다고 인정한다면: `/F` 없이는 `WM_CLOSE`를 게시하고,
스크립트된 실행은 이를 `acww_window_pump`를 통해 응답한다 -- `acww: window closed`, 세이브
플러시됨, **exit 0**. `/F`가 있으면 유저 모드 경로가 전혀 없으므로 로그는 실행 중간에 멈추고
상태는 1이다.

**레시피의 실제 비용.** AUDIO6 시대의 빌드에서 마을 레시피는 `run_town.py`의 1,500초
타임아웃에 대해 **1,000-1,360초**가 든다 -- 경합이 없을 때 약 10%의 여유인데, 많지 않다
[E: `scratchpad/stab42/INDEX.md`]. PERF42의 빌드에서는 같은 체인의 마을 구간이 **522초**
들었으므로 [H: log/source account: `docs/log/cycle42-save.md` SAVE43; receipt provenance unresolved] 여유는 이제 크다; 렌더러를 바꿀 때마다
다시 측정해야 할 숫자가 바로 이것이다.

## 반증 조건

- exit 1을 포트 실패로 읽는 것. 이 이미지에서는 그렇지 않다. 다시 돌리고, 누가
  `taskkill /IM acww.exe`를 실행했는지 찾아라 -- 그것은 모든 워크트리의 exe를 한꺼번에 죽인다.
  **2026-09-09의 밤에 세 개의 별개 에이전트가 그렇게 했고**, 매번 다른 세션의 실행을 끝냈다;
  PID로만 죽이고, 고유한 이름의 exe 복사본을 선호하라(`run_sf.py`가 그렇게 한다)
  [H: log/source account: `docs/log/cycle40-keyboard-gate-probe.md` AUDIO7, SAVEFLOW41, STAB42; receipt provenance unresolved].
- 타임아웃 하에서 실행을 프레임 수나 벽시계 시간으로 판단하는 것(B12). 종점, 종료 코드,
  이미지로 판단하라.
- 짧은 로그를 불완전한 로그로 읽는 것. 로그는 죽는 순간까지 완전하며, 그것이 마지막 줄을
  유용하게 만든다.
- 파이프를 통해 실행된 조건을 신뢰하는 것. `stabrun.py`가 존재하는 이유 중 하나는 가득 찬
  파이프가 자식을 멈출 수 있기 때문이다; stdout은 곧바로 파일로 간다.

## 관련 문서

- `off-recipe.md`, `two-tap-town-recipe.md` -- 이 조건들이 실행한 레시피
- `live-play.md` -- 페이서, 그리고 페이싱된 창이 속도 이하로 떨어지는 것이 대개 경합인 이유
- `../engine/graphics-pipeline.md` -- 레시피가 왜 2.5배 싸졌는가
- `docs/kb/hybrid/stall-playbook.md` case 47 -- 이 페이지가 그 실험인 플레이북 행
- `docs/rules/B-build.md` B12 및 B14 -- 프레임 수로 판단하지 말 것; 무엇이 함께 돌고 있었는지
  기록할 것
