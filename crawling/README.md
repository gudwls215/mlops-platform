# MLOps 플랫폼 크롤링 시스템

## 개요
시니어 구직자(50세 이상)를 위한 채용공고 크롤링 시스템입니다.

## 기능
- 사람인, 잡코리아, 워크넷 등 주요 채용사이트 크롤링  
- 시니어 친화적 채용공고 자동 필터링
- PostgreSQL 데이터베이스 연동
- robots.txt 준수 및 크롤링 예의 (Rate Limiting)
- 스케줄링 및 자동화 지원

## 설치 및 실행

### 1. 가상환경 설정
```bash
cd /home/ttm/tensorflow-jupyter/jupyterNotebook/khj/mlops-platform/crawling
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 환경변수 설정
`.env` 파일 생성:
```
DATABASE_URL=postgresql://postgres:postgres@114.202.2.226:5433/mlops
```

### 3. 크롤링 실행
```bash
# 기본 크롤링 (모든 사이트, 최대 100개)
python main.py

# 사람인만 크롤링 (최대 50개)
python main.py --site saramin --max-jobs 50

# 통계 확인
python main.py --stats

# CSV 내보내기
python main.py --export-csv jobs.csv

# 오래된 데이터 정리
python main.py --cleanup
```

## 프로젝트 구조
```
crawling/
├── venv/                   # 가상환경
├── scrapers/              # 크롤러 구현체
│   └── saramin_crawler.py # 사람인 크롤러
├── base_crawler.py        # 기본 크롤러 클래스
├── config.py             # 설정 파일
├── database.py           # 데이터베이스 연동
├── main.py              # 메인 실행기
├── requirements.txt     # 의존성 목록
└── README.md           # 이 파일
```

## 시니어 친화적 채용공고 필터링 기준

### 포함 키워드
- 시니어, 50대, 60대, 경력직, 베테랑
- 50+, 60+, 중장년, 경험자, 숙련자
- 은퇴자, 퇴직자, 재취업

### 적합 직무 카테고리
- 경비보안, 청소, 시설관리, 운전, 배달
- 상담, 텔레마케팅, 고객서비스, 판매
- 교육, 강사, 컨설팅, 멘토링
- 사무, 회계, 총무, 인사, 관리
- 돌봄, 간병, 육아, 가사도우미

### 제외 키워드
- 야간, 밤샘, 3교대, 새벽, 심야
- 장시간, 고강도, 중량물, 위험
- 신입, 경력무관, 20대, 30대, 청년

## 크롤링 예의 (Crawling Etiquette)
- robots.txt 준수
- 요청 간 1-3초 랜덤 딜레이
- User-Agent 로테이션
- 동시 요청 제한 (최대 5개)
- 재시도 제한 (최대 3회)

## 데이터베이스 스키마
크롤링된 데이터는 `job_postings` 테이블에 저장됩니다:
- 기본정보: 제목, 회사명, 지역, 급여
- 조건: 고용형태, 경력요구, 학력요구
- 상세: 설명, 요구사항, 복리후생
- 메타데이터: URL, 출처, 등록일, 마감일

## 로깅
- 파일 로그: `crawler.log`
- 콘솔 출력: 실시간 진행상황
- 로그 레벨: DEBUG, INFO, WARNING, ERROR

## 스케줄링
매일 오전 9시 자동 크롤링:
```python
from database import CrawlerScheduler, DatabaseManager

db = DatabaseManager()
scheduler = CrawlerScheduler(db)
scheduler.schedule_daily_crawling()  # 무한 루프 실행
```

## 문제 해결

### 일반적인 오류
1. **데이터베이스 연결 실패**: DATABASE_URL 확인
2. **Chrome 드라이버 오류**: webdriver-manager가 자동 설치
3. **robots.txt 차단**: 해당 URL 스킵 처리
4. **네트워크 타임아웃**: 재시도 로직 내장

### 로그 확인
```bash
tail -f crawler.log
```

## 개발자 정보
- MLOps 플랫폼 개발팀
- 버전: 1.0.0
- 업데이트: 2024년 12월