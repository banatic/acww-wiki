# 시스템
<!-- source: wiki/systems/README.md -->

게임이 어떻게 동작하는가를 다룬다. 모든 페이지는 `../STYLE.md`를 따른다: 사실을 서술하는 모든
문장에 등급과 출처가 붙고, 가설(Hypotheses) 섹션은 그 페이지가 요구하는 실험의 대기열이다.

## 작성됨

- [`town.md`](town.md) -- 에이커, 96x96 타일 격자, 시드가 아닌 세이브로부터의 생성, 아이템
  레이어, 원통형 세계, 마을 이름
- [`villagers.md`](villagers.md) -- 여덟 개의 집 레코드, 여섯 클래스 선택, 스폰 체인과 액터
  매니저, 얼굴과 표정
- [`player.md`](player.md) -- 네 개의 플레이어 슬롯, 64비트 이벤트 비트필드, 이름 키보드,
  프레임별 이동 의도
- [`economy.md`](economy.md) -- 아이템 id와 그 카테고리 니블; 벨, 가격, 무 시장과 카탈로그는
  미해결 질문이며 페이지의 대부분이 가설이다
- [`weather-and-seasons.md`](weather-and-seasons.md) -- 계절 스위치, 열네 값의 월 인덱스,
  하늘 행과 시간 블렌드, 눈과 비
- [`events-and-calendar.md`](events-and-calendar.md) -- RTC, 날짜 변경 루틴, 열한 개의 스케줄링
  술어와 스물세 개의 방문객 행
- [`dialogue.md`](dialogue.md) -- 다섯 항목의 대화 테이블, 요청/래치 상태 바이트, 스크립트
  바인드, 선택 프롬프트와 두 개의 키보드

---

## 작성됨 (하드웨어 대면 시스템)

아래 여섯 페이지는 첫 번째 패스에서 "계획됨"으로 나열되었고 하드웨어 시스템 패스에서
작성되었다; 이제 `systems/` 아래에 미작성 페이지는 없다.

| 페이지 | 답하는 내용 |
|---|---|
| [`time-and-rtc.md`](time-and-rtc.md) | RTC 요청 프로토콜, BCD 디코드, 날짜 따라잡기 루프, 틱 타이머, 그리고 포트의 시계가 2005-06-15 10:00:00에 고정된 이유 |
| [`save-data.md`](save-data.md) | 256 KB 플래시, 두 개의 `0x173fc`바이트 뱅크, 요청 타입 6/7/9, 256바이트 페이지 루프, 그리고 포트의 옵트인 `ACWW_SAVE` 저장소 |
| [`input-and-touch.md`](input-and-touch.md) | 두 개의 패드 레지스터와 `0x2fff` 마스크, 아홉 항목의 터치 링, 보정, `0x021fbde8`의 `TP_POINT`, 그리고 원본과의 측정된 1픽셀 / 1~2프레임 차이 |
| [`rng.md`](rng.md) | 서로 무관한 세 개의 LCG와 그 상수, 두 엔트로피 소스, 그리고 게임플레이 생성기가 아직 발견되지 않았다는 사실 |
| [`network.md`](network.md) | 로컬 무선과 Wi-Fi 커넥션 스택, `ov065`의 구성, 친구 코드, 그리고 포트가 이 모든 것에 "서비스 없음"으로 답하는 이유 |
| [`audio.md`](audio.md) | 하나의 10.7 MB 아카이브, PXI 태그 7 명령 프로토콜, 공유 작업 영역 레이아웃, 그리고 아무 소리도 나지 않는 이유 |

여기의 모든 페이지는 가설 섹션을 가지며 `../experiments/` 아래의 페이지로 링크한다. 일곱 개의
실험 페이지 중 세 개는 실행되었고(`off-recipe`, `two-tap-town-recipe`,
`touch-calibration`) 네 개는 설계만 되어 "아직 미실행"으로 표시되어 있다(`rtc-hour-sweep`,
`save-store-probe`, `rng-determinism`, `silent-audio-probe`)
[S: `../experiments/README.md`, its two tables].
