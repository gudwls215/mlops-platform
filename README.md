# MLOps Platform

50대 이상 시니어를 위한 AI 기반 이력서 생성 및 취업 매칭 플랫폼입니다.

## 📋 프로젝트 개요

### 주요 기능
- 🎤 음성 기반 이력서 입력 (Whisper STT)
- 🤖 AI 기반 이력서 자동 생성 (GPT-4)
- 📊 이력서-채용공고 매칭 및 합격률 예측
- 📈 MLOps 파이프라인을 통한 지속적인 모델 개선

## 프로젝트 구조

```
mlops-platform/
├── backend/                 # FastAPI 백엔드
│   ├── app/
│   │   ├── main.py         # 메인 애플리케이션
│   │   ├── core/           # 핵심 설정
│   │   ├── models/         # 데이터베이스 모델
│   │   ├── schemas/        # API 스키마
│   │   ├── crud/           # CRUD 작업
│   │   ├── api/            # API 라우터
│   │   └── utils/          # 유틸리티
│   ├── requirements.txt    # 의존성
│   └── Dockerfile         # Docker 설정
├── frontend/               # React 프론트엔드
├── ml/                     # ML 모델 및 파이프라인
├── airflow/               # Airflow DAG
├── monitoring/            # 모니터링 설정
├── docker/                # Docker 관련 파일
└── docs/                  # 문서
```

## 시작하기

### 환경 설정

1. 환경 변수 설정:
```bash
cp .env.example .env
# .env 파일을 편집하여 실제 값으로 수정
```

2. Docker 관리 스크립트 실행 권한 부여:
```bash
chmod +x docker-manage.sh
```

### 개발 환경 실행

```bash
# 개발 환경 시작
./docker-manage.sh dev

# 또는 직접 실행
docker-compose -f docker-compose.dev.yml up -d
```

### 프로덕션 환경 실행

```bash
# 프로덕션 환경 시작
./docker-manage.sh prod

# 또는 직접 실행
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 서비스 접근

### 개발 환경
- **API 서버**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **MLflow**: http://localhost:5000

### 프로덕션 환경
- **웹 서비스**: http://localhost
- **Grafana**: http://localhost:3000 (admin/admin123)
- **Prometheus**: http://localhost:9090
- **MLflow**: http://localhost:5000
- **Airflow**: http://localhost:8080

## Docker 명령어

```bash
# 개발 환경 시작
./docker-manage.sh dev

# 프로덕션 환경 시작
./docker-manage.sh prod

# 서비스 중지
./docker-manage.sh stop

# 상태 확인
./docker-manage.sh status

# 로그 확인
./docker-manage.sh logs

# 이미지 다시 빌드
./docker-manage.sh build

# 모든 것 제거 (주의!)
./docker-manage.sh clean
```

## 데이터베이스

- **호스트**: 114.202.2.226:5433
- **데이터베이스**: mlops
- **스키마**: mlops

## API 엔드포인트

### 인증
- `POST /auth/login` - 로그인
- `POST /auth/register` - 회원가입

### 이력서
- `GET /resumes/` - 이력서 목록
- `POST /resumes/` - 이력서 생성
- `GET /resumes/{id}` - 이력서 조회
- `PUT /resumes/{id}` - 이력서 수정
- `DELETE /resumes/{id}` - 이력서 삭제

### 채용 공고
- `GET /jobs/` - 채용 공고 목록
- `POST /jobs/` - 채용 공고 생성
- `GET /jobs/{id}` - 채용 공고 조회

### 자기소개서
- `GET /cover-letters/` - 자기소개서 목록
- `POST /cover-letters/` - 자기소개서 생성
- `GET /cover-letters/{id}` - 자기소개서 조회
- 🔍 실시간 채용공고 크롤링 및 분석

## 🏗️ 아키텍처
```
mlops-platform/
├── backend/          # FastAPI 백엔드
├── frontend/         # React 프론트엔드
├── ml/              # ML 모델 및 파이프라인
├── airflow/         # 데이터 파이프라인
├── monitoring/      # Prometheus & Grafana
└── docker/          # Docker 설정
```

## 🚀 개발 환경
- **Python**: 3.10+
- **Backend**: FastAPI
- **Database**: PostgreSQL (Host: 114.202.2.226:5433)
- **ML**: PyTorch, Transformers, MLflow
- **Monitoring**: Prometheus, Grafana
- **Orchestration**: Apache Airflow

## 📊 데이터베이스 스키마
- `mlops.resumes`: 이력서 정보
- `mlops.job_postings`: 채용공고 정보  
- `mlops.cover_letters`: 자기소개서 정보
- `mlops.prediction_logs`: 예측 결과 로그

## 🔧 설치 및 실행

### 1. 저장소 클론
```bash
git clone https://github.com/gudwls215/mlops-platform.git
cd mlops-platform
```

### 2. 백엔드 실행
```bash
cd backend
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 프론트엔드 실행
```bash
cd frontend
npm install
npm start
```

접속 주소:
로컬: http://localhost:41967
외부: http://192.168.0.211:41967

환경 변수 설정:
API URL: http://114.202.2.226:8000 (백엔드 서버)
외부 접속 허용 설정
접속 가능한 IP 주소들:
192.168.0.211:41967 (메인 네트워크)
192.168.0.147:41967 (보조 네트워크)

## 📈 개발 로드맵
- **Phase 1**: MVP 개발 (2개월)
- **Phase 2**: ML 모델 개발 (2개월)  
- **Phase 3**: MLOps 고도화 (1.5개월)
- **Phase 4**: 고급 기능 및 최적화 (1개월)

## 🤝 기여하기
이 프로젝트는 50대 이상 장년층의 취업을 돕기 위한 사회적 가치를 추구합니다.

## 📄 라이선스
MIT License

## 📞 연락처
- 개발자: gudwls215
- 이메일: [이메일 주소]