# 대기업 최근 3개년 채용공고 분석 리포트 웹

취업컨설턴트가 대기업 채용공고 데이터를 빠르게 분석하고, 상담용 리포트를 즉시 생성할 수 있도록 만든 반응형 웹입니다.

## 주요 기능
- 최근 3개년(기준 연도 포함) 공고 자동 분석
- 기업/직무/지역/키워드 필터
- 핵심 지표 자동 계산
  - 분석 대상 공고 수
  - 최다 직무군
  - 최다 요구 역량
  - 대표 전형 단계
- 3개년 트렌드 표 자동 생성
- 컨설팅용 문장 리포트 + 실행 권고안 자동 생성
- 원클릭 리포트 복사

## 파일 구성
- `index.html`: 반응형 UI 레이아웃
- `styles.css`: 대시보드 스타일 및 브레이크포인트
- `app.js`: 필터링, 지표 계산, 리포트 생성 로직
- `data/sample-data.json`: 샘플 채용공고 데이터

## 실행 방법
1. `report-web/index.html` 파일을 브라우저에서 열기
2. 또는 로컬 서버 실행 후 접속
   - `python -m http.server 5500`
   - `http://127.0.0.1:5500/report-web/`

## PDF 자동 추출 파이프라인
삼성전자 DS PDF 공고를 읽어 `sample-data.json`을 자동 갱신합니다.

1. 의존성 설치
   - `python -m pip install pypdf`
2. 추출 실행
   - `python report-web/scripts/extract_samsung_ds.py --pdf-dir "삼성전자 DS" --target "report-web/data/sample-data.json"`
3. 웹 새로고침
   - 필터/지표/리포트가 갱신된 데이터로 반영됩니다.

## 데이터 확장 가이드
- `sample-data.json`에 동일 스키마로 공고를 추가하면 즉시 분석에 반영됩니다.
- 권장 필드
  - `company`, `year`, `category`, `position`, `region`, `skills[]`, `process[]`, `description`

## 다음 확장 아이디어
- PDF/웹 공고 자동 수집 파이프라인 연동
- 직무별 가중치 기반 맞춤 컨설팅 점수화
- 차트(연도별/직무별/역량별) 시각화 추가
