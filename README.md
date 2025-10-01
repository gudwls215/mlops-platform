# 장년층 이력서 생성 도우미 - MLOps Platform

## 📋 프로젝트 개요
50대 이상 장년층을 위한 AI 기반 이력서 생성 및 채용 매칭 플랫폼입니다.

### 주요 기능
- 🎤 음성 기반 이력서 입력 (Whisper STT)
- 🤖 AI 기반 이력서 자동 생성 (GPT-4)
- 📊 이력서-채용공고 매칭 및 합격률 예측
- 📈 MLOps 파이프라인을 통한 지속적인 모델 개선
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