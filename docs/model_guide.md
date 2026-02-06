# 🤖 자기소개서 합격 예측 모델 가이드

> **주니어 개발자를 위한 모델 학습 및 서비스 설명서**

---

## 📋 목차

1. [개요](#1-개요)
2. [데이터 파이프라인](#2-데이터-파이프라인)
3. [모델 학습 과정](#3-모델-학습-과정)
4. [서비스에서의 활용](#4-서비스에서의-활용)
5. [MLflow 실험 관리](#5-mlflow-실험-관리)
6. [핵심 코드 설명](#6-핵심-코드-설명)
7. [자주 묻는 질문](#7-자주-묻는-질문)

---

## 1. 개요

### 🎯 목표
자기소개서(이력서)가 **합격할지 불합격할지 예측**하는 머신러닝 모델

### 📦 등록된 모델
| 모델 이름 | 알고리즘 | 용도 |
|---------|---------|------|
| `LogisticRegression_CoverLetter` | 로지스틱 회귀 | 빠른 예측, 해석 가능 |
| `RandomForest_CoverLetter` | 랜덤 포레스트 | 더 높은 정확도 |

### 🔄 전체 흐름 (Big Picture)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           학습 파이프라인                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. 원본 데이터        2. 텍스트 추출        3. 임베딩 생성              │
│  ┌───────────┐      ┌──────────────┐     ┌─────────────────┐           │
│  │ 자기소개서 │  →   │ 회사명, 직무 │  →  │ 768차원 벡터    │           │
│  │ (텍스트)   │      │ 내용 등 추출  │     │ (숫자 배열)     │           │
│  └───────────┘      └──────────────┘     └─────────────────┘           │
│                                                   ↓                     │
│  4. 모델 학습          5. 평가              6. 모델 저장                 │
│  ┌───────────┐      ┌──────────────┐     ┌─────────────────┐           │
│  │ 임베딩 +   │  →   │ F1, Accuracy │  →  │ MLflow Registry │           │
│  │ 합격라벨   │      │ ROC-AUC 측정 │     │ Production 배포 │           │
│  └───────────┘      └──────────────┘     └─────────────────┘           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                           서비스 파이프라인                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  사용자 요청           임베딩 생성            모델 예측                   │
│  ┌───────────┐      ┌──────────────┐     ┌─────────────────┐           │
│  │ 이력서    │  →   │ SBERT 모델로 │  →  │ 합격 확률 계산  │           │
│  │ 업로드    │      │ 768차원 벡터 │     │ (0.0 ~ 1.0)     │           │
│  └───────────┘      └──────────────┘     └─────────────────┘           │
│                                                   ↓                     │
│                                          ┌─────────────────┐           │
│                                          │ 채용공고 추천   │           │
│                                          │ + 합격률 표시   │           │
│                                          └─────────────────┘           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 데이터 파이프라인

### 2.1 데이터 출처

```
PostgreSQL 데이터베이스
├── mlops.cover_letter_samples  ← 자기소개서 (학습 데이터)
└── mlops.job_postings          ← 채용공고 (추천용)
```

### 2.2 학습 데이터 구조

| 컬럼명 | 타입 | 설명 | 예시 |
|-------|------|------|------|
| `id` | INTEGER | 고유 ID | 1, 2, 3... |
| `content` | TEXT | 자기소개서 원문 (JSON) | {"기본정보": {...}, "자기소개서": {...}} |
| `is_passed` | BOOLEAN | **정답 라벨** (합격/불합격) | TRUE / FALSE |
| `embedding_array` | TEXT | **768차원 임베딩 벡터** | "0.123,0.456,..." |
| `split` | VARCHAR | 데이터셋 구분 | 'train', 'validation', 'test' |

### 2.3 현재 데이터 통계

```
Split       Total   Passed  Failed
───────────────────────────────────
train        252      148     104   (58.7% 합격)
validation    86       53      33   (61.6% 합격)
test          85       53      32   (62.4% 합격)
───────────────────────────────────
합계         423      254     169
```

### 2.4 임베딩이란?

> 💡 **임베딩(Embedding)**: 텍스트를 컴퓨터가 이해할 수 있는 숫자 배열(벡터)로 변환한 것

**변환 예시:**
```
"저는 성실하고 책임감 있는 개발자입니다."
    ↓
[0.234, -0.567, 0.891, ..., 0.123]  ← 768개의 숫자
```

**사용 모델:** `snunlp/KR-SBERT-V40K-klueNLI-augSTS`
- 한국어에 특화된 Sentence-BERT 모델
- 768차원 벡터 출력
- 의미적으로 비슷한 문장은 비슷한 벡터를 가짐

---

## 3. 모델 학습 과정

### 3.1 학습 스크립트 위치

```
backend/scripts/train_baseline_models.py
```

### 3.2 학습 단계

```python
# 간략화된 학습 과정

# 1단계: 데이터 로드
X_train, y_train = load_data('train')      # X: 임베딩, y: 합격여부
X_val, y_val = load_data('validation')
X_test, y_test = load_data('test')

# 2단계: 로지스틱 회귀 학습
lr_model = LogisticRegression(
    max_iter=1000,
    class_weight='balanced',  # 클래스 불균형 처리
    solver='lbfgs'
)
lr_model.fit(X_train, y_train)

# 3단계: Random Forest 학습
rf_model = RandomForestClassifier(
    n_estimators=100,      # 트리 100개
    max_depth=10,          # 최대 깊이 10
    class_weight='balanced'
)
rf_model.fit(X_train, y_train)

# 4단계: 평가 및 MLflow에 기록
# → F1 Score가 더 높은 모델을 Production으로 배포
```

### 3.3 모델별 특징

#### 🔵 LogisticRegression_CoverLetter

```python
LogisticRegression(
    max_iter=1000,
    random_state=42,
    class_weight='balanced',
    solver='lbfgs'
)
```

| 장점 | 단점 |
|-----|-----|
| ✅ 빠른 학습/예측 | ❌ 복잡한 패턴 학습 어려움 |
| ✅ 결과 해석 가능 | ❌ 비선형 관계 포착 불가 |
| ✅ 메모리 효율적 | |

#### 🟢 RandomForest_CoverLetter

```python
RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    min_samples_split=10,
    min_samples_leaf=4,
    class_weight='balanced',
    n_jobs=-1
)
```

| 장점 | 단점 |
|-----|-----|
| ✅ 높은 정확도 | ❌ 학습 시간 더 김 |
| ✅ 과적합에 강함 | ❌ 메모리 사용량 높음 |
| ✅ 특성 중요도 제공 | ❌ 해석 어려움 |

### 3.4 평가 지표

| 지표 | 설명 | 현재 성능 (RF) |
|-----|------|--------------|
| **Accuracy** | 전체 정확도 | 0.61 |
| **Precision** | 합격 예측 중 실제 합격 비율 | 0.64 |
| **Recall** | 실제 합격 중 예측 성공 비율 | 0.87 |
| **F1 Score** | Precision과 Recall의 조화평균 | **0.74** |
| **ROC-AUC** | 분류 성능 종합 지표 | 0.53 |

---

## 4. 서비스에서의 활용

### 4.1 사용되는 곳

```
backend/app/routers/
├── recommendations.py         ← 채용공고 추천 API
├── hybrid_recommendations.py  ← 하이브리드 추천 API
└── resume.py                  ← 이력서 분석 API
```

### 4.2 모델 로딩 방식

```python
# hybrid_recommendations.py

def load_model():
    """
    모델 로드 우선순위:
    1. MLflow Model Registry (Production 스테이지)
    2. 로컬 joblib 파일 (fallback)
    """
    global _model
    if _model is None:
        try:
            # 1순위: MLflow Registry
            model_uri = "models:/LogisticRegression_CoverLetter/Production"
            _model = mlflow.sklearn.load_model(model_uri)
        except:
            # 2순위: 로컬 파일
            _model = joblib.load("models/final_model.joblib")
    return _model
```

### 4.3 예측 사용 예시

```python
# 합격 확률 예측
def predict_success_probability(resume_embedding):
    """
    이력서 임베딩으로 합격 확률 예측
    
    Args:
        resume_embedding: 768차원 numpy 배열
        
    Returns:
        float: 합격 확률 (0.0 ~ 1.0)
    """
    model = load_model()
    
    # 2D 배열로 변환 (scikit-learn 요구사항)
    embedding_2d = resume_embedding.reshape(1, -1)
    
    # 예측 확률 (불합격 확률, 합격 확률)
    probabilities = model.predict_proba(embedding_2d)
    
    # 합격 확률 반환 (인덱스 1)
    return float(probabilities[0, 1])
```

### 4.4 추천 시스템에서의 활용

```python
# recommendations.py

def recommend_jobs(resume_id: int, top_n: int = 10):
    """
    이력서 기반 채용공고 추천
    
    1. 이력서 임베딩 조회
    2. 모든 채용공고 임베딩과 유사도 계산 (코사인 유사도)
    3. 합격 예측 모델로 성공 확률 계산
    4. 상위 N개 추천
    """
    # 이력서 임베딩 조회
    resume_embedding = get_embedding_from_db(resume_id)
    
    # 채용공고 임베딩들과 유사도 계산
    job_embeddings = get_all_job_embeddings()
    similarities = cosine_similarity(
        resume_embedding.reshape(1, -1), 
        job_embeddings
    )[0]
    
    # 합격 확률 예측
    model = load_model()
    success_prob = model.predict_proba(resume_embedding.reshape(1, -1))[0, 1]
    
    # 상위 N개 선택 및 결과 생성
    top_indices = np.argsort(similarities)[::-1][:top_n]
    
    return [
        {
            "job_id": job_ids[i],
            "similarity_score": similarities[i],
            "success_probability": success_prob
        }
        for i in top_indices
    ]
```

---

## 5. MLflow 실험 관리

### 5.1 MLflow UI 접속

```
http://192.168.0.147:5001
```

### 5.2 실험 구조

```
MLflow
├── Experiments
│   └── baseline-models-2025 (experiment_id: 1)
│       ├── Logistic_Regression_Baseline (run)
│       └── RandomForest_Baseline (run)
│
└── Model Registry
    ├── LogisticRegression_CoverLetter
    │   ├── Version 1 (Archived)
    │   └── Version 2 (Production) ← 현재 서비스 중
    │
    └── RandomForest_CoverLetter
        ├── Version 1 (Archived)
        └── Version 2 (Production) ← 현재 서비스 중
```

### 5.3 모델 스테이지

| 스테이지 | 설명 |
|---------|------|
| **None** | 초기 상태 |
| **Staging** | 테스트/검증 중 |
| **Production** | 실제 서비스 배포 |
| **Archived** | 이전 버전 보관 |

### 5.4 자동 승격 조건

```python
# model_training_dag.py

F1_THRESHOLD = 0.55  # F1 Score 기준

if best_f1_score >= F1_THRESHOLD:
    # Production으로 자동 승격
    client.transition_model_version_stage(
        name=model_name,
        version=model_version,
        stage="Production"
    )
else:
    # Staging에 유지
    client.transition_model_version_stage(
        name=model_name,
        version=model_version,
        stage="Staging"
    )
```

---

## 6. 핵심 코드 설명

### 6.1 임베딩 생성

```python
# backend/app/services/embedding_service.py

from sentence_transformers import SentenceTransformer

# 한국어 특화 SBERT 모델
model = SentenceTransformer("snunlp/KR-SBERT-V40K-klueNLI-augSTS")

def generate_embedding(text: str) -> str:
    """
    텍스트 → 768차원 임베딩 벡터로 변환
    """
    # numpy 배열로 인코딩
    embedding = model.encode(text, convert_to_numpy=True)
    
    # 문자열로 변환 (DB 저장용)
    embedding_str = ",".join(map(str, embedding.tolist()))
    
    return embedding_str
```

### 6.2 데이터 로드

```python
# backend/scripts/train_baseline_models.py

def load_data(self, split='train'):
    """
    DB에서 학습 데이터 로드
    """
    query = """
    SELECT id, embedding_array, is_passed
    FROM mlops.cover_letter_samples
    WHERE split = :split 
      AND is_passed IS NOT NULL 
      AND embedding_array IS NOT NULL
    """
    
    df = pd.read_sql(query, conn, params={'split': split})
    
    # 임베딩 문자열 → numpy 배열 변환
    X = np.array([
        [float(x) for x in row.split(',')]
        for row in df['embedding_array']
    ])
    
    y = df['is_passed'].values.astype(int)
    
    return X, y
```

### 6.3 모델 저장/로드

```python
# 저장 (학습 후)
import joblib
joblib.dump(model, 'models/logistic_regression_baseline.joblib')

# MLflow에도 저장
mlflow.sklearn.log_model(
    sk_model=model,
    artifact_path="model",
    registered_model_name="LogisticRegression_CoverLetter"
)

# 로드 (서비스에서)
model = joblib.load('models/final_model.joblib')
# 또는
model = mlflow.sklearn.load_model("models:/LogisticRegression_CoverLetter/Production")
```

---

## 7. 자주 묻는 질문

### Q1. 임베딩 차원이 768인 이유는?

> SBERT 모델(`snunlp/KR-SBERT-V40K-klueNLI-augSTS`)의 기본 출력 차원이 768입니다. 
> 이는 BERT 기반 모델의 hidden size와 동일합니다.

### Q2. 왜 두 가지 모델을 학습하나요?

> **Logistic Regression**: 빠르고 해석 가능, 베이스라인 역할
> **Random Forest**: 더 높은 정확도 기대, 앙상블 효과
> 
> 두 모델을 비교하여 F1 Score가 높은 모델을 Production에 배포합니다.

### Q3. class_weight='balanced'는 무엇인가요?

> 합격/불합격 데이터 비율이 다를 때, 소수 클래스에 더 높은 가중치를 부여합니다.
> 예: 합격 60%, 불합격 40%일 때 불합격에 더 큰 가중치

### Q4. 새 데이터로 재학습하려면?

```bash
# 1. Airflow DAG 수동 실행
airflow dags trigger model_training_mlflow_pipeline

# 2. 또는 스크립트 직접 실행
cd backend
python scripts/train_baseline_models.py
```

### Q5. 모델 성능이 낮은 이유는?

> 1. **데이터 부족**: 현재 약 400건으로 딥러닝에는 부족
> 2. **라벨 품질**: 합격/불합격 기준의 일관성 필요
> 3. **특성 부족**: 임베딩만으로는 한계, 추가 특성 필요

### Q6. 서비스에서 예측이 안 되면?

```python
# 체크리스트
1. MLflow 서버 상태: curl http://192.168.0.147:5001/health
2. 모델 파일 존재: ls backend/models/final_model.joblib
3. 임베딩 데이터: SELECT COUNT(*) FROM mlops.cover_letter_samples WHERE embedding_array IS NOT NULL
```

---

## 📚 관련 파일 목록

| 파일 | 설명 |
|-----|------|
| `backend/scripts/train_baseline_models.py` | 모델 학습 메인 스크립트 |
| `backend/scripts/generate_embeddings.py` | 임베딩 생성 스크립트 |
| `backend/app/services/embedding_service.py` | 임베딩 서비스 |
| `backend/app/services/experiment_tracking.py` | MLflow 연동 |
| `backend/app/routers/recommendations.py` | 추천 API |
| `backend/app/routers/hybrid_recommendations.py` | 하이브리드 추천 API |
| `airflow/dags/model_training_dag.py` | Airflow 학습 DAG |

---

> 📅 최종 업데이트: 2025-12-15
> 
> 📧 문의: MLOps Platform Team
 