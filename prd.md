# 제품 요구 사항 명세서 (PRD)
## 장년층 이력서 생성 도우미

---

## 📋 목차
1. [프로젝트 개요](#1-프로젝트-개요)
2. [핵심 기능 명세](#2-핵심-기능-명세)
3. [기술 스택](#3-기술-스택)
4. [시스템 아키텍처](#4-시스템-아키텍처)
5. [MLOps 파이프라인](#5-mlops-파이프라인)
6. [데이터 수집 및 관리](#6-데이터-수집-및-관리)
7. [API 명세](#7-api-명세)
8. [개발 로드맵](#8-개발-로드맵)
9. [용어 설명](#9-용어-설명)

---

## 1. 프로젝트 개요

### 1.1 프로젝트 목적
50대 이상 장년층의 재취업을 돕기 위한 AI 기반 이력서 생성 및 채용 매칭 플랫폼을 개발합니다. 단순히 이력서 도우미에 그치지 않고, 향후 다양한 ML 서비스를 쉽게 추가할 수 있는 **확장 가능한 MLOps 플랫폼**을 구축하는 것이 핵심입니다.

### 1.2 타겟 사용자
- **주 사용자**: 50대 이상 구직자
- **특징**: IT 기술에 익숙하지 않을 수 있으므로 직관적이고 단순한 UI 필요

### 1.3 핵심 가치 제안
- ✅ AI가 자동으로 이력서와 자기소개서 작성
- ✅ 음성으로 편하게 경력 입력 가능
- ✅ 합격 가능성을 숫자로 미리 확인
- ✅ 나에게 맞는 채용공고 자동 추천
- ✅ 합격률 높은 이력서 작성법 제안

### 1.4 개발 환경
- **팀 구성**: 1인 풀스택 개발
- **서버**: 온프레미스 서버 1대 (GPU: 48GB VRAM, CPU: 고성능, RAM: 128GB)
- **데이터베이스**: PostgreSQL (Host: 114.202.2.226:5433, Schema: mlops)
- **개발 기간**: 6개월 (4단계 구성)

---

## 2. 핵심 기능 명세

### 2.1 사용자 기능

#### 2.1.1 이력서 입력
**방법 1: 웹 폼 직접 입력**
- 기본 정보 (이름, 연락처, 학력)
- 경력 사항 (회사명, 직책, 재직기간, 업무내용)
- 자격증 및 스킬
- 희망 직무

**방법 2: 음성 인터뷰**
- 사용자가 음성으로 경력 설명
- Whisper 모델로 음성을 텍스트로 변환 (STT)
- GPT API로 텍스트를 구조화된 이력서 데이터로 변환
- 사용자가 확인 후 수정 가능

#### 2.1.2 자동 이력서 작성
- 입력된 정보를 바탕으로 GPT API가 전문적인 이력서 생성
- 장년층의 경력을 강점으로 표현하는 문구 자동 생성

#### 2.1.3 자기소개서 생성
- 지원하는 채용공고와 사용자 이력서를 분석
- GPT API로 맞춤형 자기소개서 자동 작성

#### 2.1.4 합격률 예측
- 사용자 이력서 + 채용공고 데이터 입력
- ML 모델이 합격 확률을 **퍼센트(%)로 출력**
- 예시: "이 공고에 대한 귀하의 합격 가능성은 **73%**입니다"

#### 2.1.5 채용공고 추천
- 사용자의 경력, 희망 직무, 스킬을 분석
- 가장 적합한 채용공고 상위 N개 추천
- 각 공고별 예상 합격률도 함께 표시

#### 2.1.6 직무 추천
- 사용자의 경력을 분석하여 적합한 직무 카테고리 제안
- 예: "마케팅 경험 → 디지털 마케터, 브랜드 매니저 추천"

#### 2.1.7 이력서 개선 제안
- 현재 이력서를 분석하여 개선점 제안
- "업무 성과를 수치로 표현하세요", "키워드 'OO' 추가 권장" 등

#### 2.1.8 합격률 높은 이력서 추천
- 유사한 경력을 가진 합격 사례 이력서 패턴 분석
- "합격률 높은 이력서들은 이런 키워드를 사용했어요" 형태로 제공

### 2.2 관리자 기능 (개발자용)

#### 2.2.1 데이터 수집 모니터링
- 크롤링 상태 확인 (성공/실패 건수)
- 수집된 데이터 통계 (이력서 수, 채용공고 수)

#### 2.2.2 모델 성능 모니터링
- Grafana 대시보드로 실시간 확인
  - 예측 정확도
  - 응답 시간 (Latency)
  - 데이터 드리프트 지표

#### 2.2.3 MLOps 파이프라인 관리
- Airflow UI에서 데이터 파이프라인 상태 확인
- MLflow에서 모델 버전 관리 및 배포

---

## 3. 기술 스택

### 3.1 백엔드
```
언어: Python 3.10+
프레임워크: FastAPI
데이터베이스: PostgreSQL 14+
ORM: SQLAlchemy
비동기 처리: Celery (선택사항)
```

**선정 이유**:
- FastAPI: 빠른 개발 속도, 자동 API 문서 생성, 비동기 지원
- PostgreSQL: 안정적이고 복잡한 쿼리 처리 가능

### 3.2 프론트엔드
```
기본: HTML5, CSS3, JavaScript
프레임워크: React 18+
상태관리: React Hooks (useState, useContext)
UI 라이브러리: Material-UI or Tailwind CSS
```

**선정 이유**:
- React: 컴포넌트 재사용성, 풍부한 생태계

### 3.3 ML/AI
```
음성 인식: OpenAI Whisper (로컬 호스팅)
텍스트 생성: OpenAI GPT-4 API
ML 프레임워크: PyTorch, scikit-learn
모델 서빙: TorchServe or FastAPI
임베딩: Sentence-Transformers (유사도 계산용)
```

### 3.4 MLOps
```
워크플로우 오케스트레이션: Apache Airflow
실험 추적/모델 관리: MLflow
모니터링: Prometheus + Grafana
컨테이너: Docker, Docker Compose
```

**각 도구의 역할**:
- **Airflow**: 데이터 수집, 전처리, 모델 학습을 자동화
- **MLflow**: 모델 학습 실험 기록, 모델 버전 관리, 모델 배포
- **Prometheus**: 시스템 지표 수집 (CPU, 메모리, API 응답시간 등)
- **Grafana**: Prometheus 데이터를 시각화하여 대시보드 제공

### 3.5 인프라
```
서버: 온프레미스 단일 서버 (기 구축 완료)
OS: Ubuntu 22.04 LTS
리버스 프록시: Nginx (설치 완료)
데이터베이스: PostgreSQL (Host: 114.202.2.226:5433)
- Database: postgres
- Schema: mlops
- 연결 설정 완료
HTTPS: Let's Encrypt (설정 완료)
```

---

## 4. 시스템 아키텍처

### 4.1 전체 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────┐
│                        사용자 (브라우저)                      │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      Nginx (리버스 프록시)                    │
└────────────┬────────────────────────────────┬────────────────┘
             │                                │
             ▼                                ▼
┌──────────────────────┐          ┌─────────────────────────┐
│   React Frontend     │          │   FastAPI Backend       │
│   (Port 3000)        │          │   (Port 8000)           │
└──────────────────────┘          └───────────┬─────────────┘
                                              │
                    ┌─────────────────────────┼─────────────┐
                    │                         │             │
                    ▼                         ▼             ▼
         ┌──────────────────┐     ┌──────────────┐  ┌──────────────┐
         │  PostgreSQL DB   │     │ Whisper STT  │  │  GPT-4 API   │
         │  (Port 5432)     │     │  (로컬)      │  │  (외부)      │
         └──────────────────┘     └──────────────┘  └──────────────┘
                    │
                    │
    ┌───────────────┼───────────────────────────────┐
    │               │                               │
    ▼               ▼                               ▼
┌─────────┐   ┌──────────┐                  ┌──────────────┐
│ Airflow │   │ MLflow   │                  │ ML Model     │
│(Port    │   │(Port     │                  │ Serving      │
│ 8080)   │   │ 5000)    │                  │ (TorchServe) │
└─────────┘   └──────────┘                  └──────────────┘
    │               │                               │
    └───────────────┴───────────────┬───────────────┘
                                    ▼
                          ┌─────────────────────┐
                          │  Prometheus         │
                          │  (Port 9090)        │
                          └──────────┬──────────┘
                                     ▼
                          ┌─────────────────────┐
                          │  Grafana            │
                          │  (Port 3001)        │
                          └─────────────────────┘
```

### 4.2 주요 컴포넌트 설명

#### 4.2.1 Frontend (React)
- 사용자 인터페이스 제공
- 폼 입력, 음성 녹음, 결과 표시

#### 4.2.2 Backend (FastAPI)
- RESTful API 제공
- 비즈니스 로직 처리
- DB CRUD 작업
- ML 모델 호출

#### 4.2.3 Database (PostgreSQL)
**데이터베이스 연결 정보**:
- **Host**: 114.202.2.226:5433
- **Database**: postgres
- **Schema**: mlops
- **Username**: postgres

**테이블 구조** (mlops 스키마):
```sql
-- 사용자 이력서
mlops.resumes (
    id, user_id, name, contact, education, 
    careers (JSONB), skills (JSONB), 
    hope_job, created_at, updated_at
)

-- 자기소개서 (linkareer 크롤링)
mlops.cover_letters (
    id, company, position, content, 
    tags (JSONB), source_url, collected_at
)

-- 채용공고 (사람인, 잡코리아, 워크넷)
mlops.job_postings (
    id, company, title, description, 
    requirements (JSONB), location, salary, 
    source, posted_at, collected_at
)

-- 합격률 예측 로그
mlops.prediction_logs (
    id, resume_id, job_posting_id, 
    predicted_probability, actual_result, 
    created_at
)
```

#### 4.2.4 ML Model Serving
- 합격률 예측 모델 제공 (REST API)
- 이력서-채용공고 매칭 모델
- 직무 추천 모델

---

## 5. MLOps 파이프라인

### 5.1 MLOps 철학
**"확장 가능한 플랫폼"의 의미**:
- 새로운 ML 모델을 추가할 때 **기존 파이프라인을 재사용**
- 모델별로 독립적인 학습/배포 가능
- 표준화된 인터페이스로 일관성 유지

### 5.2 파이프라인 구조

```
┌─────────────────────────────────────────────────────────────┐
│                     1. 데이터 수집 (Airflow DAG)             │
│  - 크롤링 (Scrapy/BeautifulSoup)                            │
│  - 데이터 검증 및 정제                                       │
│  - PostgreSQL 저장                                          │
└────────────────────────┬────────────────────────────────────┘
                         │ 매일 실행 or 수동 트리거
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  2. 데이터 전처리 (Airflow DAG)              │
│  - 텍스트 클리닝 (특수문자 제거, 정규화)                      │
│  - 토큰화 및 임베딩 생성                                     │
│  - Train/Val/Test 분할                                      │
└────────────────────────┬────────────────────────────────────┘
                         │ 조건: 신규 데이터 1000건 이상
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   3. 모델 학습 (Airflow + MLflow)            │
│  - MLflow로 실험 추적 (하이퍼파라미터, 메트릭)               │
│  - 모델 학습 및 검증                                         │
│  - 최고 성능 모델 MLflow Model Registry에 등록               │
└────────────────────────┬────────────────────────────────────┘
                         │ 조건: 신규 모델이 기존보다 5% 이상 우수
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   4. 모델 배포 (MLflow)                      │
│  - Staging 환경에 배포                                       │
│  - A/B 테스트 (선택사항)                                     │
│  - Production 환경에 배포                                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              5. 모니터링 (Prometheus + Grafana)              │
│  - 예측 정확도 추적                                          │
│  - 데이터 드리프트 감지 (입력 분포 변화)                      │
│  - 시스템 리소스 모니터링 (GPU, CPU, RAM)                    │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 Airflow DAG 예시

**DAG 1: 데이터 수집 파이프라인** (`data_collection_dag.py`)
```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'admin',
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'data_collection',
    default_args=default_args,
    description='크롤링 및 데이터 저장',
    schedule_interval='0 2 * * *',  # 매일 새벽 2시
    start_date=datetime(2025, 1, 1),
    catchup=False,
) as dag:
    
    crawl_saramin = PythonOperator(
        task_id='crawl_saramin',
        python_callable=crawl_saramin_jobs,
    )
    
    crawl_jobkorea = PythonOperator(
        task_id='crawl_jobkorea',
        python_callable=crawl_jobkorea_jobs,
    )
    
    crawl_worknet = PythonOperator(
        task_id='crawl_worknet',
        python_callable=crawl_worknet_jobs,
    )
    
    crawl_coverletters = PythonOperator(
        task_id='crawl_coverletters',
        python_callable=crawl_linkareer_coverletters,
    )
    
    validate_data = PythonOperator(
        task_id='validate_data',
        python_callable=validate_collected_data,
    )
    
    # 병렬 실행 후 검증
    [crawl_saramin, crawl_jobkorea, crawl_worknet, crawl_coverletters] >> validate_data
```

**DAG 2: 모델 학습 파이프라인** (`model_training_dag.py`)
```python
# 조건부 실행: 신규 데이터가 1000건 이상일 때만 실행
with DAG(
    'model_training',
    default_args=default_args,
    schedule_interval='@weekly',  # 주 1회 체크
    start_date=datetime(2025, 1, 1),
) as dag:
    
    check_data_volume = BranchPythonOperator(
        task_id='check_data_volume',
        python_callable=check_new_data_count,  # 1000건 이상이면 학습 진행
    )
    
    preprocess_data = PythonOperator(
        task_id='preprocess_data',
        python_callable=preprocess_training_data,
    )
    
    train_model = PythonOperator(
        task_id='train_model',
        python_callable=train_matching_model,
    )
    
    evaluate_model = PythonOperator(
        task_id='evaluate_model',
        python_callable=evaluate_and_register_model,
    )
    
    check_data_volume >> preprocess_data >> train_model >> evaluate_model
```

### 5.4 MLflow 활용

**모델 실험 추적**:
```python
import mlflow
import mlflow.pytorch

# 실험 시작
with mlflow.start_run(run_name="resume_matching_v1"):
    # 하이퍼파라미터 로깅
    mlflow.log_params({
        "learning_rate": 0.001,
        "batch_size": 32,
        "epochs": 50,
        "model_type": "transformer"
    })
    
    # 학습 진행
    for epoch in range(50):
        train_loss = train_one_epoch(model, train_loader)
        val_accuracy = validate(model, val_loader)
        
        # 메트릭 로깅
        mlflow.log_metrics({
            "train_loss": train_loss,
            "val_accuracy": val_accuracy
        }, step=epoch)
    
    # 최종 모델 저장
    mlflow.pytorch.log_model(model, "model")
    
    # 모델 등록 (성능이 우수할 경우)
    if val_accuracy > 0.85:
        mlflow.register_model(
            f"runs:/{mlflow.active_run().info.run_id}/model",
            "ResumeMatchingModel"
        )
```

**모델 배포**:
```python
from mlflow.tracking import MlflowClient

client = MlflowClient()

# Staging으로 승격
client.transition_model_version_stage(
    name="ResumeMatchingModel",
    version=3,
    stage="Staging"
)

# 검증 후 Production으로 승격
client.transition_model_version_stage(
    name="ResumeMatchingModel",
    version=3,
    stage="Production"
)
```

### 5.5 모델 모니터링

**Prometheus 메트릭 수집**:
```python
from prometheus_client import Counter, Histogram, Gauge

# 예측 요청 횟수
prediction_counter = Counter(
    'model_predictions_total', 
    'Total number of predictions',
    ['model_name', 'version']
)

# 예측 응답 시간
prediction_latency = Histogram(
    'model_prediction_latency_seconds',
    'Prediction latency in seconds'
)

# 예측 정확도 (실제 결과 피드백 시)
prediction_accuracy = Gauge(
    'model_accuracy',
    'Model accuracy based on feedback'
)

# 데이터 드리프트 점수
data_drift_score = Gauge(
    'data_drift_score',
    'Data drift detection score'
)
```

**Grafana 대시보드 구성**:
1. **모델 성능 패널**
   - 실시간 예측 정확도 그래프
   - 일별/주별 정확도 추이

2. **시스템 성능 패널**
   - API 응답 시간 (P50, P95, P99)
   - 요청 처리량 (TPS)

3. **데이터 품질 패널**
   - 데이터 드리프트 점수
   - 입력 데이터 분포 변화

4. **인프라 패널**
   - GPU 사용률
   - CPU/메모리 사용률

### 5.6 확장 가능한 설계 원칙

#### 원칙 1: 모델별 독립 파이프라인
```
models/
├── resume_matching/
│   ├── train.py
│   ├── preprocess.py
│   ├── model.py
│   └── config.yaml
├── job_recommendation/
│   ├── train.py
│   ├── preprocess.py
│   └── config.yaml
└── resume_improvement/
    └── ...
```

각 모델은 독립적인 폴더와 설정 파일을 가지며, 공통 유틸리티만 공유.

#### 원칙 2: 표준화된 인터페이스
모든 모델은 동일한 인터페이스를 구현:
```python
class BaseMLModel:
    def preprocess(self, raw_data):
        """데이터 전처리"""
        pass
    
    def train(self, train_data):
        """모델 학습"""
        pass
    
    def predict(self, input_data):
        """예측 수행"""
        pass
    
    def evaluate(self, test_data):
        """모델 평가"""
        pass
```

#### 원칙 3: 설정 기반 파이프라인
```yaml
# config.yaml
model:
  name: "resume_matching"
  version: "1.0"
  
training:
  batch_size: 32
  learning_rate: 0.001
  epochs: 50
  
data:
  source_table: "resumes"
  target_table: "job_postings"
  
deployment:
  staging_threshold: 0.80  # Staging 승격 기준
  production_threshold: 0.85  # Production 승격 기준
```

---

## 6. 데이터 수집 및 관리

### 6.1 데이터 소스

#### 6.1.1 자기소개서 데이터
- **출처**: https://linkareer.com/cover-letter/search
- **수집 정보**:
  - 회사명
  - 직무/포지션
  - 자기소개서 내용
  - 합격/불합격 여부 (있을 경우)
  - 태그 (예: #마케팅, #신입)

#### 6.1.2 채용공고 데이터
- **출처**: 사람인, 잡코리아, 워크넷
- **수집 정보**:
  - 회사명
  - 공고 제목
  - 직무 설명
  - 자격 요건 (학력, 경력, 스킬)
  - 근무 지역
  - 급여 정보
  - 마감일

### 6.2 크롤링 구현

**기술 스택**:
- Scrapy or BeautifulSoup + Selenium (동적 페이지용)
- 로봇 배제 표준 (robots.txt) 준수
- Rate limiting (과도한 요청 방지)

**크롤러 예시** (`crawlers/saramin_crawler.py`):
```python
import scrapy
from datetime import datetime

class SaraminJobSpider(scrapy.Spider):
    name = "saramin_jobs"
    
    def start_requests(self):
        # 50대 이상 채용 공고 검색
        urls = [
            'https://www.saramin.co.kr/zf_user/search/recruit?searchword=50대',
            # ... 추가 URL
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)
    
    def parse(self, response):
        for job in response.css('.item_recruit'):
            yield {
                'company': job.css('.corp_name a::text').get(),
                'title': job.css('.job_tit a::text').get(),
                'description': job.css('.job_condition span::text').getall(),
                'location': job.css('.job_condition span:nth-child(2)::text').get(),
                'source': 'saramin',
                'collected_at': datetime.now()
            }
```

### 6.3 데이터 검증 및 정제

**검증 규칙**:
- 필수 필드 누락 여부 (회사명, 제목, 설명)
- 중복 데이터 제거 (URL 기준)
- 텍스트 길이 제한 (너무 짧거나 긴 데이터 필터링)

**정제 프로세스**:
1. HTML 태그 제거
2. 특수문자 정규화
3. 공백 정리
4. 인코딩 통일 (UTF-8)

### 6.4 데이터 업데이트 전략
- **채용공고**: 매일 새벽 2시 크롤링 (신규 공고 수집)
- **자기소개서**: 주 1회 크롤링 (데이터 변화가 적음)
- **중복 처리**: URL 해시값으로 중복 체크

---

## 7. API 명세

### 7.1 인증
**현재 버전**: 인증 없음 (추후 JWT 도입 가능)

### 7.2 엔드포인트

#### 7.2.1 이력서 관리

**POST /api/v1/resumes**
- 설명: 새 이력서 생성
- 요청 본문:
```json
{
  "name": "홍길동",
  "contact": {
    "email": "hong@example.com",
    "phone": "010-1234-5678"
  },
  "education": [
    {
      "school": "서울대학교",
      "major": "경영학",
      "degree": "학사",
      "graduation_year": 1995
    }
  ],
  "careers": [
    {
      "company": "삼성전자",
      "position": "과장",
      "start_date": "2000-03",
      "end_date": "2020-12",
      "description": "마케팅 전략 수립 및 실행"
    }
  ],
  "skills": ["MS Office", "데이터 분석", "프로젝트 관리"],
  "desired_job": "마케팅 매니저"
}
```
- 응답:
```json
{
  "resume_id": "uuid-1234",
  "message": "이력서가 성공적으로 생성되었습니다"
}
```

**GET /api/v1/resumes/{resume_id}**
- 설명: 이력서 조회
- 응답: 이력서 전체 정보

**POST /api/v1/resumes/voice-input**
- 설명: 음성으로 이력서 입력
- 요청: multipart/form-data (audio file)
- 처리 과정:
  1. Whisper로 음성 → 텍스트 변환
  2. GPT-4로 텍스트 → 구조화된 JSON 변환
- 응답:
```json
{
  "transcript": "저는 20년간 삼성전자에서...",
  "structured_data": {
    "careers": [...],
    "skills": [...]
  },
  "confidence": 0.92
}
```

#### 7.2.2 이력서/자기소개서 생성

**POST /api/v1/generate/resume**
- 설명: AI가 전문적인 이력서 텍스트 생성
- 요청:
```json
{
  "resume_id": "uuid-1234",
  "style": "professional"  // professional, creative, simple
}
```
- 응답:
```json
{
  "generated_resume": "# 홍길동\n\n## 경력 요약\n20년간..."
}
```

**POST /api/v1/generate/cover-letter**
- 설명: 채용공고에 맞춤형 자기소개서 생성
- 요청:
```json
{
  "resume_id": "uuid-1234",
  "job_posting_id": "job-5678"
}
```
- 응답:
```json
{
  "cover_letter": "귀사의 마케팅 매니저 포지션에...",
  "key_points": [
    "20년 경력 강조",
    "데이터 기반 의사결정 경험 부각"
  ]
}
```

#### 7.2.3 합격률 예측

**POST /api/v1/predict/match-probability**
- 설명: 이력서와 채용공고 매칭 확률 계산
- 요청:
```json
{
  "resume_id": "uuid-1234",
  "job_posting_id": "job-5678"
}
```
- 응답:
```json
{
  "probability": 0.73,
  "confidence_interval": [0.68, 0.78],
  "factors": {
    "positive": ["경력 연차 충족", "필수 스킬 보유"],
    "negative": ["학력 요건 미흡"]
  }
}
```

#### 7.2.4 채용공고 추천

**GET /api/v1/recommendations/jobs?resume_id={resume_id}&limit=10**
- 설명: 사용자에게 적합한 채용공고 추천
- 응답:
```json
{
  "recommendations": [
    {
      "job_posting_id": "job-5678",
      "company": "현대자동차",
      "title": "마케팅 매니저",
      "match_probability": 0.85,
      "match_score": 92,
      "reasons": ["경력 연차 일치", "스킬 매칭도 높음"]
    },
    // ... 9개 더
  ]
}
```

#### 7.2.5 직무 추천

**GET /api/v1/recommendations/positions?resume_id={resume_id}**
- 설명: 경력 분석 후 적합한 직무 제안
- 응답:
```json
{
  "recommended_positions": [
    {
      "position": "마케팅 매니저",
      "match_score": 95,
      "reason": "20년 마케팅 경력과 완벽히 일치"
    },
    {
      "position": "브랜드 디렉터",
      "match_score": 88,
      "reason": "브랜드 관리 경험 보유"
    }
  ]
}
```

#### 7.2.6 이력서 개선 제안

**POST /api/v1/improve/resume**
- 설명: 이력서 분석 후 개선 포인트 제공
- 요청:
```json
{
  "resume_id": "uuid-1234"
}
```
- 응답:
```json
{
  "improvement_suggestions": [
    {
      "category": "업무 성과",
      "suggestion": "구체적인 수치로 성과를 표현하세요",
      "example": "매출 20% 증가 달성"
    },
    {
      "category": "키워드",
      "suggestion": "'디지털 마케팅' 키워드 추가 권장",
      "reason": "최근 채용 트렌드 반영"
    }
  ],
  "overall_score": 72
}
```

#### 7.2.7 합격 이력서 패턴 분석

**GET /api/v1/analysis/successful-resumes?position={position}**
- 설명: 특정 직무의 합격 이력서 패턴 분석
- 응답:
```json
{
  "position": "마케팅 매니저",
  "common_keywords": ["데이터 분석", "ROI", "캠페인 기획"],
  "average_career_years": 15,
  "top_skills": ["Google Analytics", "SQL", "A/B Testing"],
  "resume_structure_tips": [
    "성과를 수치로 표현한 이력서가 합격률 30% 높음",
    "프로젝트 사례 3개 이상 포함 권장"
  ]
}
```

#### 7.2.8 채용공고 조회

**GET /api/v1/job-postings?search={keyword}&location={location}&limit=20**
- 설명: 채용공고 검색
- 응답:
```json
{
  "total": 157,
  "results": [
    {
      "id": "job-5678",
      "company": "현대자동차",
      "title": "마케팅 매니저",
      "location": "서울 강남구",
      "salary": "면접 후 결정",
      "posted_at": "2025-09-25",
      "source": "saramin"
    }
  ]
}
```

---

## 8. 개발 로드맵

### 8.1 Phase 1: MVP (최소 기능 제품) - 2개월

**목표**: 핵심 기능만 구현하여 빠르게 검증

#### Week 1-2: 인프라 구축
- [ ] 서버 환경 설정 (Docker, PostgreSQL, Nginx)
- [ ] FastAPI 프로젝트 초기 설정
- [ ] React 프로젝트 초기 설정
- [ ] PostgreSQL 테이블 스키마 설계 및 생성

#### Week 3-4: 데이터 수집
- [ ] 사람인 크롤러 개발 (채용공고)
- [ ] Linkareer 크롤러 개발 (자기소개서)
- [ ] 데이터 검증 및 DB 저장 로직
- [ ] Airflow 설치 및 기본 DAG 구성

#### Week 5-6: 핵심 AI 기능
- [ ] Whisper 모델 로컬 배포 (음성 → 텍스트)
- [ ] GPT-4 API 연동 (이력서/자기소개서 생성)
- [ ] 간단한 매칭 알고리즘 (규칙 기반 또는 TF-IDF)

#### Week 7-8: 웹 인터페이스
- [ ] 이력서 입력 폼 (웹)
- [ ] 음성 녹음 기능
- [ ] 생성된 이력서/자기소개서 표시
- [ ] 간단한 채용공고 목록

**MVP 완성 시 제공 기능**:
✅ 웹/음성으로 이력서 입력
✅ AI 이력서 자동 작성
✅ AI 자기소개서 생성
✅ 기본 채용공고 조회

---

### 8.2 Phase 2: ML 모델 개발 - 2개월

#### Week 9-10: 데이터 준비
- [ ] 충분한 데이터 수집 (최소 5,000건 이상)
- [ ] 데이터 라벨링 (합격/불합격 데이터)
- [ ] 학습/검증/테스트 데이터 분할
- [ ] Feature Engineering (텍스트 임베딩, 키워드 추출)

#### Week 11-12: 합격률 예측 모델
- [ ] Sentence-BERT로 이력서/채용공고 임베딩
- [ ] 유사도 기반 매칭 모델 학습
- [ ] 분류 모델 학습 (Random Forest or XGBoost)
- [ ] 모델 평가 (Accuracy, F1-score, ROC-AUC)

#### Week 13-14: 추천 시스템
- [ ] 채용공고 추천 모델 (협업 필터링 or Content-based)
- [ ] 직무 추천 모델
- [ ] TorchServe로 모델 서빙 API 구축

#### Week 15-16: MLflow 연동
- [ ] MLflow 설치 및 초기 설정
- [ ] 모델 실험 추적 코드 작성
- [ ] Model Registry 구성
- [ ] Airflow에서 모델 학습 DAG 생성

**Phase 2 완성 시 추가 기능**:
✅ 정확한 합격률 예측 (ML 모델)
✅ 개인화된 채용공고 추천
✅ 직무 추천
✅ MLflow로 모델 버전 관리

---

### 8.3 Phase 3: MLOps 고도화 - 1.5개월

#### Week 17-18: 모니터링 구축
- [ ] Prometheus 설치 및 메트릭 수집
- [ ] Grafana 대시보드 구성
  - 모델 성능 패널
  - 시스템 리소스 패널
  - 데이터 품질 패널
- [ ] 알람 설정 (정확도 하락, 시스템 오류)

#### Week 19-20: 자동화 파이프라인
- [ ] 데이터 수집 → 전처리 → 학습 → 배포 전체 자동화
- [ ] 모델 재학습 트리거 (데이터 임계값)
- [ ] A/B 테스트 인프라 (선택사항)
- [ ] 데이터 드리프트 감지 로직

#### Week 21-22: 이력서 개선 기능
- [ ] 이력서 분석 모델 (GPT-4 프롬프트 최적화)
- [ ] 합격 이력서 패턴 분석 알고리즘
- [ ] 키워드 추출 및 트렌드 분석

**Phase 3 완성 시 추가 기능**:
✅ 실시간 모델 모니터링
✅ 자동 모델 재학습/배포
✅ 이력서 개선 제안
✅ 합격 패턴 분석

---

### 8.4 Phase 4: 고급 기능 및 최적화 - 1개월

#### Week 23-24: 성능 최적화
- [ ] API 응답 속도 개선 (캐싱, 쿼리 최적화)
- [ ] 모델 추론 속도 개선 (양자화, TensorRT)
- [ ] 대용량 데이터 처리 최적화

#### Week 25-26: 사용자 경험 개선
- [ ] UI/UX 개선 (장년층 친화적 디자인)
- [ ] 튜토리얼 및 가이드 추가
- [ ] 반응형 디자인 (모바일 지원)
- [ ] 에러 핸들링 및 사용자 피드백

**Phase 4 완성 시**:
✅ 빠른 응답 속도
✅ 직관적인 UI/UX
✅ 안정적인 서비스

---

### 8.5 우선순위 가이드

**반드시 구현 (Must Have)**:
- ✅ 이력서 입력 (웹 폼)
- ✅ AI 이력서 작성
- ✅ AI 자기소개서 생성
- ✅ 채용공고 조회
- ✅ 합격률 예측 (MVP에서는 간단한 알고리즘, Phase 2에서 ML 모델)

**가능하면 구현 (Should Have)**:
- 🔶 음성 입력 (Whisper)
- 🔶 채용공고 추천
- 🔶 직무 추천
- 🔶 MLflow 모델 관리

**여유 있으면 구현 (Nice to Have)**:
- 🟡 이력서 개선 제안
- 🟡 합격 패턴 분석
- 🟡 A/B 테스트
- 🟡 모바일 앱

---

## 9. 용어 설명

### 9.1 AI/ML 용어

**LLM (Large Language Model)**
- 대규모 언어 모델, GPT-4 같은 AI
- 텍스트를 이해하고 생성할 수 있음

**STT (Speech-to-Text)**
- 음성을 텍스트로 변환하는 기술
- Whisper 모델이 대표적

**Embedding (임베딩)**
- 텍스트를 숫자 벡터로 변환
- 유사도 계산에 사용
- 예: "마케팅 경험" → [0.2, 0.8, 0.1, ...]

**Fine-tuning (파인튜닝)**
- 사전 학습된 모델을 특정 작업에 맞게 재학습
- 예: 일반 텍스트 모델 → 이력서 전문 모델로 변환

**Inference (추론)**
- 학습된 모델로 예측하는 과정
- 예: 이력서 입력 → 합격률 73% 출력

**Data Drift (데이터 드리프트)**
- 학습 데이터와 실제 입력 데이터의 분포가 달라지는 현상
- 예: 학습 시에는 40대 데이터가 많았는데, 실제로는 60대 사용자가 많음
- 모델 성능 저하의 주요 원인

### 9.2 MLOps 용어

**MLOps (Machine Learning Operations)**
- ML 모델을 개발, 배포, 운영하는 전체 프로세스
- DevOps의 ML 버전

**Pipeline (파이프라인)**
- 데이터 수집 → 전처리 → 학습 → 배포의 자동화된 흐름
- Airflow DAG로 구현

**Model Registry (모델 레지스트리)**
- 학습된 모델들을 버전별로 저장하고 관리하는 저장소
- MLflow가 제공

**Staging / Production**
- Staging: 테스트 환경 (실제 서비스 전 검증)
- Production: 실제 서비스 환경 (사용자에게 제공)

**Monitoring (모니터링)**
- 모델과 시스템의 상태를 실시간으로 추적
- Prometheus + Grafana로 구현

**A/B Testing**
- 두 가지 버전을 동시에 운영하여 성능 비교
- 예: 모델 v1 vs 모델 v2 중 어느 것이 더 정확한지 테스트

### 9.3 인프라 용어

**Docker**
- 애플리케이션을 컨테이너로 패키징하는 도구
- "내 컴퓨터에서는 잘 되는데"를 방지

**Nginx**
- 웹 서버 겸 리버스 프록시
- 사용자 요청을 백엔드로 전달

**ORM (Object-Relational Mapping)**
- Python 객체로 데이터베이스 조작
- SQL 대신 Python 코드로 DB 작업
- 예: `session.query(Resume).filter_by(id=123).first()`

**REST API**
- 웹 서비스의 표준 통신 방식
- HTTP 메서드 (GET, POST, PUT, DELETE) 사용

**JSONB (PostgreSQL)**
- JSON 형태의 데이터를 효율적으로 저장하는 타입
- 배열이나 중첩된 객체 저장에 유용

### 9.4 데이터 용어

**Crawling (크롤링)**
- 웹사이트에서 자동으로 데이터 수집
- robots.txt 규칙을 준수해야 함

**Feature Engineering**
- 모델 학습에 유용한 특징(변수) 만들기
- 예: "경력 20년" → 숫자 20으로 변환

**Train/Validation/Test Split**
- 학습용 / 검증용 / 테스트용 데이터 분할
- 일반적으로 60% / 20% / 20% 비율

**Labeling (라벨링)**
- 데이터에 정답 표시하기
- 예: 이력서에 "합격" 또는 "불합격" 태그

---

## 10. 리스크 및 대응 방안

### 10.1 기술적 리스크

**리스크 1: 단일 서버 장애**
- **영향**: 전체 서비스 중단
- **대응**:
  - Phase 1에서는 감수 (MVP 단계)
  - Phase 3 이후 백업 서버 또는 클라우드 이전 고려
  - 정기 백업 (DB dump 자동화)

**리스크 2: GPU 메모리 부족**
- **영향**: 모델 학습 실패, 추론 속도 저하
- **대응**:
  - 배치 사이즈 조절
  - 모델 경량화 (Quantization, Distillation)
  - 우선순위 큐 (학습 > 추론)

**리스크 3: 크롤링 차단**
- **영향**: 데이터 수집 불가
- **대응**:
  - Rate limiting (요청 간격 조절)
  - User-Agent 로테이션
  - 프록시 사용 (필요시)
  - 공식 API 사용 검토 (유료)

**리스크 4: GPT-4 API 비용 급증**
- **영향**: 예산 초과
- **대응**:
  - 캐싱 (동일 요청 재사용)
  - 프롬프트 최적화 (토큰 수 감소)
  - 일일 사용량 제한 설정
  - 오픈소스 LLM으로 대체 검토 (SOLAR, LLaMA)

### 10.2 데이터 리스크

**리스크 5: 데이터 품질 저하**
- **영향**: 모델 성능 하락
- **대응**:
  - 자동 검증 규칙 적용
  - 정기적인 데이터 품질 체크
  - 이상치 탐지 및 제거

**리스크 6: 개인정보 유출**
- **영향**: 법적 문제, 신뢰 상실
- **대응**:
  - 민감 정보 암호화 (연락처, 주민번호)
  - 접근 권한 관리
  - 정기 보안 점검
  - HTTPS 적용

**리스크 7: 편향된 데이터**
- **영향**: 특정 연령/성별에 불리한 예측
- **대응**:
  - 데이터 분포 모니터링
  - 공정성 지표 추적 (Fairness Metrics)
  - 정기적인 편향 감사

### 10.3 비즈니스 리스크

**리스크 8: 사용자 확보 실패**
- **영향**: 서비스 지속 불가
- **대응**:
  - 초기에 소규모 타겟 그룹 선정
  - 사용자 피드백 적극 수렴
  - 지속적인 기능 개선

**리스크 9: 모델 정확도 부족**
- **영향**: 사용자 신뢰 하락
- **대응**:
  - 초기에는 참고용으로 안내
  - 지속적인 모델 개선
  - 사용자 피드백으로 재학습

---

## 11. 성공 지표 (KPI)

### 11.1 사용자 지표
- **DAU (일일 활성 사용자)**: 목표 100명 (Phase 2 완료 시)
- **이력서 생성 수**: 월 500건
- **사용자 만족도**: NPS 점수 50 이상

### 11.2 모델 성능 지표
- **합격률 예측 정확도**: 75% 이상
- **추천 채용공고 클릭률**: 30% 이상
- **API 응답 시간**: P95 < 2초

### 11.3 시스템 지표
- **서비스 가동률 (Uptime)**: 99% 이상
- **데이터 수집 성공률**: 95% 이상
- **모델 재학습 주기**: 신규 데이터 1,000건당 1회

---

## 12. 참고 자료

### 12.1 공식 문서
- **FastAPI**: https://fastapi.tiangolo.com/
- **MLflow**: https://mlflow.org/docs/latest/index.html
- **Airflow**: https://airflow.apache.org/docs/
- **Prometheus**: https://prometheus.io/docs/
- **Grafana**: https://grafana.com/docs/

### 12.2 학습 자료
- **MLOps 개념**: "Designing Machine Learning Systems" (Chip Huyen)
- **Whisper 사용법**: OpenAI Whisper GitHub
- **GPT-4 API**: OpenAI Platform Documentation

### 12.3 유사 프로젝트
- Resume.io (이력서 생성 서비스)
- Indeed Resume Builder
- Jobscan (이력서 최적화)

---

## 13. FAQ (자주 묻는 질문)

**Q1: 혼자 개발하는데 6개월이 현실적인가요?**
- A: MVP는 2개월 내 가능합니다. 나머지는 점진적으로 추가하세요. 중요한 건 빠른 출시와 피드백입니다.

**Q2: 서버 1대로 충분한가요?**
- A: 초기 사용자 1,000명까지는 충분합니다. GPU 48GB는 충분한 스펙입니다.

**Q3: 크롤링이 법적으로 괜찮나요?**
- A: robots.txt를 준수하고 과도한 요청을 하지 않으면 일반적으로 문제없습니다. 하지만 각 사이트의 이용약관을 확인하세요.

**Q4: GPT-4 API 비용이 얼마나 나올까요?**
- A: 사용자 100명 기준, 월 $100-300 예상 (이력서 생성 기준). 캐싱으로 비용 절감 가능합니다.

**Q5: 모델 정확도를 어떻게 높일 수 있나요?**
- A: 
  1. 더 많은 학습 데이터 수집
  2. Feature Engineering 개선
  3. 하이퍼파라미터 튜닝
  4. 사용자 피드백 반영 (실제 합격/불합격 결과)

**Q6: MLOps가 정말 필요한가요?**
- A: 모델을 지속적으로 개선하고 자동화하려면 필수입니다. 처음엔 수동으로 시작하고, Phase 3에서 자동화하세요.

**Q7: 다른 서비스로 확장하려면 어떻게 하나요?**
- A: 이 구조는 모듈화되어 있어, 새 모델을 추가하고 Airflow DAG만 작성하면 됩니다. `models/` 폴더에 새 프로젝트 추가하면 됩니다.

---

## 14. 다음 단계

### 14.1 즉시 실행할 작업
1. ✅ GitHub 저장소 생성
2. ✅ 개발 환경 설정 (Docker, PostgreSQL)
3. ✅ Trello/Notion으로 작업 관리 보드 만들기
4. ✅ Week 1-2 작업 시작

### 14.2 첫 주 목표
- 서버에 Ubuntu, Docker, Docker Compose 설치
- PostgreSQL 컨테이너 실행
- FastAPI "Hello World" 실행
- React "Hello World" 실행

### 14.3 문의사항
PRD에 대한 질문이나 추가 설명이 필요하면 언제든 요청하세요!

---

**문서 버전**: 1.0  
**작성일**: 2025-10-01  
**최종 수정일**: 2025-10-01