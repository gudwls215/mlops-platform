# 하이브리드 추천 API 사용 가이드

## 📋 개요
Content-based Filtering과 Collaborative Filtering을 결합한 하이브리드 추천 시스템 API입니다.

---

## 🔗 엔드포인트

### 1. 하이브리드 추천 조회
**GET** `/api/hybrid-recommendations/jobs/{resume_id}`

특정 이력서에 대한 채용공고 추천을 반환합니다.

#### 파라미터
| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `resume_id` | int | O | - | 이력서 ID |
| `top_n` | int | X | 10 | 추천 개수 (1-50) |
| `strategy` | string | X | "weighted" | 통합 전략 |
| `content_weight` | float | X | 0.6 | Content-based 가중치 (0-1) |
| `cf_weight` | float | X | 0.4 | CF 가중치 (0-1) |

#### 통합 전략 (strategy)
- **weighted**: 가중치 합산 (기본값)
  - Content-based와 CF 점수를 가중치로 합산
  - 유연한 조정 가능
  
- **cascade**: 계단식
  - Content-based 추천 우선
  - 부족하면 CF 추천으로 채움
  - Cold-start 문제 해결에 효과적
  
- **mixed**: 혼합
  - Content-based와 CF 추천을 번갈아 선택
  - 다양성 확보

#### 요청 예시
```bash
# 1. Weighted 전략 (기본)
curl "http://localhost:9000/api/hybrid-recommendations/jobs/1?top_n=10&strategy=weighted"

# 2. Content-based 우세 (7:3 비율)
curl "http://localhost:9000/api/hybrid-recommendations/jobs/2091?top_n=5&strategy=weighted&content_weight=0.7&cf_weight=0.3"

# 3. Cascade 전략
curl "http://localhost:9000/api/hybrid-recommendations/jobs/2092?top_n=10&strategy=cascade"

# 4. Mixed 전략
curl "http://localhost:9000/api/hybrid-recommendations/jobs/2093?top_n=10&strategy=mixed"
```

#### 응답 예시
```json
{
  "resume_id": 1,
  "total_count": 5,
  "strategy": "weighted",
  "content_weight": 0.6,
  "cf_weight": 0.4,
  "recommendations": [
    {
      "job_id": 355,
      "title": "품질관리 담당자 (188)",
      "company": "현대자동차",
      "hybrid_score": 0.6,
      "similarity": 0.6158,
      "cf_score": 0.0,
      "strategy": "weighted",
      "source": "content-based"
    },
    {
      "job_id": 189,
      "title": "프로젝트 매니저 (22)",
      "company": "현대자동차",
      "hybrid_score": 0.4071,
      "similarity": 0.5701,
      "cf_score": 0.0,
      "strategy": "weighted",
      "source": "content-based"
    }
  ],
  "generated_at": "2025-10-27T10:56:53.186395"
}
```

#### 응답 필드 설명
| 필드 | 설명 |
|------|------|
| `job_id` | 채용공고 ID |
| `title` | 채용공고 제목 |
| `company` | 회사명 |
| `hybrid_score` | 하이브리드 점수 (0-1) |
| `similarity` | Content-based 유사도 (0-1) |
| `cf_score` | Collaborative Filtering 점수 |
| `strategy` | 사용된 통합 전략 |
| `source` | 추천 출처 (content-based/collaborative) |

---

### 2. 시스템 통계 조회
**GET** `/api/hybrid-recommendations/stats`

하이브리드 추천 시스템의 현재 상태와 통계를 반환합니다.

#### 요청 예시
```bash
curl "http://localhost:9000/api/hybrid-recommendations/stats"
```

#### 응답 예시
```json
{
  "content_based": {
    "resumes_with_embeddings": 486,
    "jobs_with_embeddings": 41
  },
  "collaborative_filtering": {
    "available": true,
    "total_interactions": 491,
    "unique_users": 100,
    "unique_items": 41,
    "matrix_users": 100,
    "matrix_items": 41,
    "sparsity": 0.8832
  },
  "hybrid": {
    "strategies_available": ["weighted", "cascade", "mixed"],
    "default_strategy": "weighted",
    "default_content_weight": 0.6,
    "default_cf_weight": 0.4
  }
}
```

---

## 💡 사용 시나리오

### 시나리오 1: 신규 사용자 추천
**상황**: 상호작용 데이터가 없는 신규 사용자

**추천 전략**: `cascade` 또는 `weighted` (Content 가중치 높게)

```bash
curl "http://localhost:9000/api/hybrid-recommendations/jobs/NEW_USER_ID?strategy=cascade&top_n=10"
```

**이유**: Content-based 추천으로 Cold-start 문제 해결

---

### 시나리오 2: 활성 사용자 추천
**상황**: 충분한 상호작용 데이터가 있는 사용자

**추천 전략**: `weighted` (균등 또는 CF 우세)

```bash
curl "http://localhost:9000/api/hybrid-recommendations/jobs/ACTIVE_USER_ID?strategy=weighted&content_weight=0.4&cf_weight=0.6&top_n=10"
```

**이유**: CF를 통해 협업 필터링의 장점 활용

---

### 시나리오 3: 다양한 추천 필요
**상황**: 사용자가 다양한 채용공고를 탐색하고 싶음

**추천 전략**: `mixed`

```bash
curl "http://localhost:9000/api/hybrid-recommendations/jobs/USER_ID?strategy=mixed&top_n=20"
```

**이유**: Content-based와 CF를 번갈아 선택하여 다양성 확보

---

## 📊 성능 지표

### 응답 시간
- **평균**: 0.284초
- **P95**: 0.361초
- **P99**: 0.439초

### 추천 품질
- Content-based 유사도: 평균 0.54-0.62
- CF 예측 평점: 평균 3.0-4.0

---

## 🔧 Python 클라이언트 예시

```python
import requests

class HybridRecommendationClient:
    def __init__(self, base_url="http://localhost:9000"):
        self.base_url = base_url
    
    def get_recommendations(
        self, 
        resume_id: int, 
        top_n: int = 10,
        strategy: str = "weighted",
        content_weight: float = 0.6,
        cf_weight: float = 0.4
    ):
        """하이브리드 추천 조회"""
        url = f"{self.base_url}/api/hybrid-recommendations/jobs/{resume_id}"
        params = {
            "top_n": top_n,
            "strategy": strategy,
            "content_weight": content_weight,
            "cf_weight": cf_weight
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_stats(self):
        """시스템 통계 조회"""
        url = f"{self.base_url}/api/hybrid-recommendations/stats"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()


# 사용 예시
client = HybridRecommendationClient()

# 1. Weighted 전략으로 추천 받기
result = client.get_recommendations(
    resume_id=1, 
    top_n=10, 
    strategy="weighted",
    content_weight=0.7,
    cf_weight=0.3
)

print(f"추천 개수: {result['total_count']}")
for rec in result['recommendations']:
    print(f"- [{rec['job_id']}] {rec['company']}: {rec['title']}")
    print(f"  Hybrid Score: {rec['hybrid_score']:.4f}")

# 2. 시스템 통계 확인
stats = client.get_stats()
print(f"\nContent-based 이력서: {stats['content_based']['resumes_with_embeddings']}")
print(f"CF 상호작용: {stats['collaborative_filtering']['total_interactions']}")
```

---

## ⚠️ 주의사항

### 1. 가중치 합산
- `content_weight + cf_weight`는 1.0이 아니어도 됨
- 내부적으로 정규화되므로 비율만 중요

### 2. 데이터 부족 시
- CF 데이터가 부족하면 Content-based 우세
- Sparsity가 높으면 CF 효과 제한적

### 3. 응답 시간
- 첫 요청 시 모델 로딩으로 약간 느릴 수 있음
- 이후 요청은 캐싱으로 빠름

### 4. 에러 처리
- 존재하지 않는 resume_id: 404 에러
- 서버 오류: 500 에러 (로그 확인 필요)

---

## 📚 관련 문서
- [협업 필터링 구현 보고서](./COLLABORATIVE_FILTERING_REPORT.md)
- [추천 시스템 아키텍처](./backend/scripts/collaborative_filtering.py)
- [API 전체 문서](http://localhost:9000/docs)

---

**업데이트**: 2025-10-27  
**버전**: 1.0
