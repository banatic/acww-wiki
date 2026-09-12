# 엔진
<!-- source: wiki/engine/README.md -->

프로그램이 어떻게 조립되어 있는지를 다룬다. 각 페이지는 `../STYLE.md`에 맞춰 작성되어 있다.

작성됨:

- [`boot-and-entry.md`](boot-and-entry.md) -- 진입점, 하드웨어 초기 기동, 정적 초기화자,
  NitroMain, 메인 루프, 프레임이란 무엇인가
- [`overlays.md`](overlays.md) -- 148개의 오버레이 슬롯: 어떤 오버레이가 어떤 기능을 담당하는지,
  로드와 언로드, 상주 여부, 주소가 모호한 이유
- [`scenes-and-channels.md`](scenes-and-channels.md) -- 씬 머신, 씬 6의 6단계
  로더, 채널 열기, 이중 간접 핸들러 테이블, 메일박스와 모드 바이트
- [`display-objects.md`](display-objects.md) -- 디스플레이 오브젝트 프레임워크: 네 개의 리스트,
  네 개의 스테퍼와 그 3슬롯 패턴, join/commit/step, VBlank 태스크
- [`display-callbacks.md`](display-callbacks.md) -- 세 순회기가 도는 하나의 리스트: 노드의 활성·대기 핸들러 쌍, 확정 규칙, 그리고 각 핸들러의 어느 대응물을 설치할지 정하는 서브·메인 엔진 분기
- [`memory-map.md`](memory-map.md) -- 메인 RAM, ITCM/DTCM, 모듈 대역, 아레나,
  게임 힙, 전역 주소 대역
- [`threads-and-interrupts.md`](threads-and-interrupts.md) -- OSContext와 협조적
  스케줄러, 존재하는 스레드들, 인터럽트 테이블, PXI 태그

- [`file-system.md`](file-system.md) -- ROM 파일 시스템, 오버레이 테이블, 아카이브,
  파일을 여는 방법
- [`text-and-messages.md`](text-and-messages.md) -- 메시지 시스템(bmg), 폰트,
  키보드 화면
- [`graphics-pipeline.md`](graphics-pipeline.md) -- 2D 엔진, 3D 지오메트리 제출, VRAM
  뱅크, 디스플레이 리스트, 그리고 포트 자체 렌더러가 하는 일과 그 비용 (PERF42, RENDER42)
- [`interpreter-path.md`](interpreter-path.md) -- 하이브리드 런타임(`ACWW_INTERP=1`), 거부
  목록, 그리고 네이티브 본체가 핫 패스를 얻게 되는 차등 검사 (단계 H5)
- [`time-budgets.md`](time-budgets.md) -- 밀리초 리터럴 32개 전체: 로더 예산, 네트워크 타이머, 알람 변환
