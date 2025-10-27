# 추천 다양성/참신성 기능 사용 가이드

## 🎯 개요

하이브리드 추천 API에 다양성(Diversity)과 참신성(Novelty) 재정렬 기능이 추가되었습니다.  
이 기능을 사용하면 유사한 채용공고가 중복되지 않고, 사용자가 보지 않은 새로운 공고를 우선적으로 추천받을 수 있습니다.

---

## 🚀 빠른 시작

### 기본 추천 (다양성 비활성화)
```bash
curl "http://localhost:8000/api/hybrid-recommendations/jobs/1?top_n=10"
```

### 다양성/참신성 활성화
```bash
curl "http://localhost:8000/api/hybrid-recommendations/jobs/1?\
  top_n=10&\
  enable_diversity=true"
```

---

## 📖 파라미터 설명

### 필수 파라미터
- **resume_id** (경로): 이력서 ID

### 기본 파라미터
- **top_n** (기본값: 10): 추천 개수 (1~50)
- **strategy** (기본값: "weighted"): 통합 전략
  - `weighted`: 가중치 합산
  - `cascade`: Content-based 우선, 부족하면 CF 추가
  - `mixed`: 번갈아가며 섞기

### Content-based / CF 가중치
- **content_weight** (기본값: 0.6): Content-based 가중치 (0~1)
- **cf_weight** (기본값: 0.4): Collaborative Filtering 가중치 (0~1)

### ✨ 다양성/참신성 파라미터 (NEW)

#### enable_diversity (기본값: false)
- 다양성/참신성 재정렬 활성화 여부
- `true`: 다양성/참신성 고려
- `false`: 기본 추천 (유사도만 고려)

#### diversity_weight (기본값: 0.3)
- 다양성 가중치 (0~1)
- 높을수록 다양한 회사/직무 추천
- 낮을수록 유사한 공고 위주 추천

#### novelty_weight (기본값: 0.2)
- 참신성 가중치 (0~1)
- 높을수록 새로운 공고 우선 추천
- 낮을수록 과거에 본 공고도 추천

#### mmr_lambda (기본값: 0.7)
- MMR 알고리즘의 lambda 파라미터 (0~1)
- 1.0: 유사도만 고려 (다양성 무시)
- 0.0: 다양성만 고려 (유사도 무시)
- 0.5~0.7: 균형잡힌 추천

**최종 점수 계산**:
```
relevance_weight = 1.0 - diversity_weight - novelty_weight
final_score = relevance × relevance_weight
            + diversity × diversity_weight
            + novelty × novelty_weight
```

---

## 💡 사용 시나리오

### 1. 유사한 공고 위주 (연관성 중시)
```bash
curl "http://localhost:8000/api/hybrid-recommendations/jobs/1?\
  enable_diversity=true&\
  diversity_weight=0.1&\
  novelty_weight=0.1&\
  mmr_lambda=0.9"
```
- 사용자 이력서와 가장 유사한 공고 위주
- 다양성은 낮지만 정확도 높음

### 2. 다양한 공고 탐색 (다양성 중시)
```bash
curl "http://localhost:8000/api/hybrid-recommendations/jobs/1?\
  enable_diversity=true&\
  diversity_weight=0.4&\
  novelty_weight=0.2&\
  mmr_lambda=0.5"
```
- 여러 산업/직무의 다양한 공고 추천
- 새로운 기회 발견에 유리

### 3. 최신 공고 우선 (참신성 중시)
```bash
curl "http://localhost:8000/api/hybrid-recommendations/jobs/1?\
  enable_diversity=true&\
  diversity_weight=0.2&\
  novelty_weight=0.4&\
  mmr_lambda=0.7"
```
- 사용자가 보지 않은 새로운 공고 우선
- 최근 등록된 공고에 높은 가중치

### 4. 균형잡힌 추천 (권장)
```bash
curl "http://localhost:8000/api/hybrid-recommendations/jobs/1?\
  enable_diversity=true&\
  diversity_weight=0.3&\
  novelty_weight=0.2&\
  mmr_lambda=0.7"
```
- 연관성(50%) + 다양성(30%) + 참신성(20%)
- 대부분의 사용 사례에 적합

---

## 📊 응답 형식

### 다양성 비활성화 시
```json
{
  "resume_id": 1,
  "total_count": 10,
  "strategy": "weighted",
  "content_weight": 0.6,
  "cf_weight": 0.4,
  "recommendations": [
    {
      "job_id": 188,
      "title": "품질관리 담당자",
      "company": "현대자동차",
      "hybrid_score": 0.600,
      "similarity": 0.616,
      "cf_score": 0.0,
      "strategy": "weighted",
      "source": "content-based"
    }
  ]
}
```

### ✨ 다양성 활성화 시 (추가 필드)
```json
{
  "recommendations": [
    {
      "job_id": 188,
      "title": "품질관리 담당자",
      "company": "현대자동차",
      "hybrid_score": 0.600,      // 원래 점수
      "final_score": 0.846,       // ✨ 최종 점수 (diversity+novelty 반영)
      "diversity_score": 1.000,   // ✨ 다양성 점수 (0~1)
      "novelty_score": 1.000,     // ✨ 참신성 점수 (0~1)
      "user_novelty": 1.000,      // ✨ 사용자가 본 적 있는지
      "recency_factor": 1.000,    // ✨ 등록일 기반 최신도
      "similarity": 0.616,
      "cf_score": 0.0,
      "strategy": "weighted"
    }
  ]
}
```

---

## 🔍 점수 해석

### diversity_score (다양성 점수)
- **1.0**: 가장 다양함 (첫 번째 추천)
- **0.5**: 중간 정도 다양함
- **0.0**: 다른 추천과 매우 유사함 (마지막 추천)

**계산 방식**: MMR 순위 기반
- 순위가 높을수록 높은 점수
- `diversity = 1.0 - (rank - 1) / total_count`

### novelty_score (참신성 점수)
- **1.0**: 완전히 새로운 공고
- **0.5**: 보통 수준의 참신성
- **0.0**: 오래되고 이미 본 공고

**계산 방식**:
- `novelty = user_novelty × 0.6 + recency_factor × 0.4`

#### user_novelty (사용자 novelty)
- **1.0**: 사용자가 본 적 없음
- **0.5**: 15일 전에 봄
- **0.0**: 최근에 봄

#### recency_factor (등록일 최신도)
- **1.0**: 30일 이내 등록
- **0.7**: 120일 전 등록
- **0.5**: 210일 이상 경과

### final_score (최종 점수)
```
final_score = (original_score × relevance_weight)
            + (diversity_score × diversity_weight)
            + (novelty_score × novelty_weight)
```

- 높을수록 우선 추천
- 사용자 설정에 따라 가중치 조정

---

## ⚡ 성능 고려사항

### 응답 시간
- **기본 추천**: 평균 0.4초, P95 0.8초
- **다양성 활성화**: 평균 0.6초, P95 1.0초
- **오버헤드**: 약 42%

### 권장 사항
1. **실시간 추천**: `enable_diversity=false` (빠른 응답)
2. **탐색 모드**: `enable_diversity=true` (다양한 결과)
3. **배치 작업**: 다양성 활성화 권장

### 캐싱 전략
- 자주 요청되는 파라미터 조합 캐싱 권장
- Redis 활용 시 응답 시간 50% 단축 가능

---

## 🧪 테스트

### Python 테스트 스크립트
```python
import requests

# 기본 추천
response = requests.get(
    "http://localhost:8000/api/hybrid-recommendations/jobs/1",
    params={"top_n": 10}
)
print(response.json())

# 다양성 활성화
response = requests.get(
    "http://localhost:8000/api/hybrid-recommendations/jobs/1",
    params={
        "top_n": 10,
        "enable_diversity": True,
        "diversity_weight": 0.3,
        "novelty_weight": 0.2,
        "mmr_lambda": 0.7
    }
)
print(response.json())
```

### 종합 테스트
```bash
cd backend
python3 scripts/test_diversity_api.py
```

---

## 📚 추가 자료

- [전체 구현 보고서](DIVERSITY_NOVELTY_REPORT.md)
- [하이브리드 추천 API 가이드](HYBRID_RECOMMENDATION_API_GUIDE.md)
- [협업 필터링 보고서](COLLABORATIVE_FILTERING_REPORT.md)

---

## 🆘 문제 해결

### Q1. novelty_score가 모두 0.0으로 나옵니다
**A**: `enable_diversity=true`를 설정했는지 확인하세요.

### Q2. diversity_score가 모두 같습니다
**A**: 데이터셋이 작거나 모든 공고가 유사한 경우 발생할 수 있습니다. `mmr_lambda`를 낮춰보세요 (예: 0.3).

### Q3. 응답 시간이 느립니다
**A**: `enable_diversity=false`로 설정하거나, Redis 캐싱을 구현하세요.

### Q4. 추천 결과가 너무 다양해서 관련성이 떨어집니다
**A**: `diversity_weight`를 낮추고 `mmr_lambda`를 높이세요 (예: 0.1, 0.9).

---

**마지막 업데이트**: 2025-10-27  
**버전**: 1.0
