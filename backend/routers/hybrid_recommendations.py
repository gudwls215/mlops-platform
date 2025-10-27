"""
하이브리드 추천 API
Content-based + Collaborative Filtering 결합
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime
import sys
import os
from pathlib import Path
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv
import joblib

# 환경 변수 로드
load_dotenv()

# 프로젝트 루트 경로 추가
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'scripts'))

# collaborative_filtering 모듈 임포트
try:
    from collaborative_filtering import CollaborativeFilteringRecommender
except ImportError:
    from scripts.collaborative_filtering import CollaborativeFilteringRecommender

# diversity_novelty 모듈 임포트
try:
    from diversity_novelty import DiversityNoveltyReranker, parse_embedding
except ImportError:
    from scripts.diversity_novelty import DiversityNoveltyReranker, parse_embedding as dn_parse_embedding
    parse_embedding = dn_parse_embedding

router = APIRouter(prefix="/api/hybrid-recommendations", tags=["hybrid-recommendations"])

# 데이터베이스 연결 설정
DB_HOST = os.getenv('POSTGRES_HOST', '114.202.2.226')
DB_PORT = os.getenv('POSTGRES_PORT', '5433')
DB_NAME = os.getenv('POSTGRES_DB', 'postgres')
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')
DB_SCHEMA = 'mlops'

import urllib.parse
encoded_password = urllib.parse.quote_plus(DB_PASSWORD)
DATABASE_URL = f"postgresql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 모델 경로
MODEL_DIR = project_root / 'models'
FINAL_MODEL_PATH = MODEL_DIR / 'final_model.joblib'

# 싱글톤 인스턴스
_model = None
_cf_recommender = None
_diversity_reranker = None


def load_model():
    """최종 모델 로드 (싱글톤)"""
    global _model
    if _model is None:
        if not FINAL_MODEL_PATH.exists():
            raise FileNotFoundError(f"최종 모델 파일이 없습니다: {FINAL_MODEL_PATH}")
        _model = joblib.load(FINAL_MODEL_PATH)
    return _model


def get_cf_recommender():
    """협업 필터링 추천 시스템 로드 (싱글톤)"""
    global _cf_recommender
    if _cf_recommender is None:
        _cf_recommender = CollaborativeFilteringRecommender()
        success = _cf_recommender.build_model()
        if not success:
            _cf_recommender = None
            raise ValueError("협업 필터링 모델 빌드 실패")
    return _cf_recommender


def get_diversity_reranker():
    """다양성/참신성 재정렬 시스템 로드 (싱글톤)"""
    global _diversity_reranker
    if _diversity_reranker is None:
        _diversity_reranker = DiversityNoveltyReranker()
    return _diversity_reranker


def parse_embedding(embedding_str: str) -> np.ndarray:
    """임베딩 문자열 파싱"""
    if embedding_str is None:
        return None
    embedding_str = embedding_str.strip('[]')
    values = [float(x.strip()) for x in embedding_str.split(',')]
    return np.array(values)


def get_content_based_recommendations(resume_id: int, top_n: int = 20) -> List[dict]:
    """
    Content-based 추천 (코사인 유사도 기반)
    
    Returns:
        [{"job_id": int, "similarity": float}, ...]
    """
    engine = create_engine(DATABASE_URL)
    
    # 이력서 임베딩 조회
    resume_query = f"""
    SELECT id, embedding_array
    FROM {DB_SCHEMA}.cover_letter_samples
    WHERE id = :resume_id
    """
    
    with engine.connect() as conn:
        resume_result = conn.execute(text(resume_query), {"resume_id": resume_id}).fetchone()
    
    if not resume_result:
        return []
    
    resume_embedding = parse_embedding(resume_result[1])
    if resume_embedding is None:
        return []
    
    # 채용공고 임베딩 조회
    jobs_query = f"""
    SELECT id, title, company, experience_level, salary_min, salary_max, embedding_array
    FROM {DB_SCHEMA}.job_postings
    WHERE embedding_array IS NOT NULL
    """
    
    with engine.connect() as conn:
        jobs_df = pd.read_sql(text(jobs_query), conn)
    
    if len(jobs_df) == 0:
        return []
    
    # 임베딩 파싱
    job_embeddings = []
    valid_indices = []
    
    for idx, row in jobs_df.iterrows():
        emb = parse_embedding(row['embedding_array'])
        if emb is not None:
            job_embeddings.append(emb)
            valid_indices.append(idx)
    
    if len(job_embeddings) == 0:
        return []
    
    jobs_df = jobs_df.iloc[valid_indices].reset_index(drop=True)
    job_embeddings = np.array(job_embeddings)
    
    # 코사인 유사도 계산
    resume_embedding_2d = resume_embedding.reshape(1, -1)
    similarities = cosine_similarity(resume_embedding_2d, job_embeddings)[0]
    
    # 결과 생성 (success_probability 제거)
    recommendations = []
    for idx, (job_id, similarity) in enumerate(zip(jobs_df['id'], similarities)):
        recommendations.append({
            "job_id": int(job_id),
            "title": jobs_df.iloc[idx]['title'],
            "company": jobs_df.iloc[idx]['company'],
            "similarity": float(similarity),
            "source": "content-based"
        })
    
    # 유사도 기준 정렬 및 Top-N
    recommendations.sort(key=lambda x: x['similarity'], reverse=True)
    return recommendations[:top_n]


def get_collaborative_recommendations(resume_id: int, top_n: int = 20) -> List[dict]:
    """
    Collaborative Filtering 추천
    
    Returns:
        [{"job_id": int, "cf_score": float}, ...]
    """
    try:
        cf_recommender = get_cf_recommender()
        cf_results = cf_recommender.recommend_for_user(resume_id, top_n=top_n)
        
        if not cf_results:
            return []
        
        # 채용공고 상세 정보 조회
        engine = create_engine(DATABASE_URL)
        job_ids = [job_id for job_id, _ in cf_results]
        
        if not job_ids:
            return []
        
        jobs_query = f"""
        SELECT id, title, company
        FROM {DB_SCHEMA}.job_postings
        WHERE id = ANY(:job_ids)
        """
        
        with engine.connect() as conn:
            jobs_df = pd.read_sql(text(jobs_query), conn, params={"job_ids": job_ids})
        
        # 결과 매핑
        cf_scores = {job_id: score for job_id, score in cf_results}
        
        recommendations = []
        for _, row in jobs_df.iterrows():
            job_id = row['id']
            recommendations.append({
                "job_id": int(job_id),
                "title": row['title'],
                "company": row['company'],
                "cf_score": float(cf_scores.get(job_id, 0)),
                "source": "collaborative"
            })
        
        recommendations.sort(key=lambda x: x['cf_score'], reverse=True)
        return recommendations
        
    except Exception as e:
        print(f"협업 필터링 추천 실패: {e}")
        return []


def hybrid_recommend(
    resume_id: int, 
    top_n: int = 10,
    content_weight: float = 0.6,
    cf_weight: float = 0.4,
    strategy: Literal["weighted", "cascade", "mixed"] = "weighted",
    enable_diversity: bool = False,
    diversity_weight: float = 0.3,
    novelty_weight: float = 0.2,
    mmr_lambda: float = 0.7
) -> List[dict]:
    """
    하이브리드 추천
    
    Args:
        resume_id: 이력서 ID
        top_n: 추천 개수
        content_weight: Content-based 가중치 (weighted 전략)
        cf_weight: Collaborative Filtering 가중치 (weighted 전략)
        strategy: 통합 전략
            - weighted: 가중치 합산
            - cascade: Content-based 우선, 부족하면 CF 추가
            - mixed: 번갈아가며 섞기
        enable_diversity: 다양성/참신성 재정렬 활성화
        diversity_weight: 다양성 가중치 (enable_diversity=True일 때)
        novelty_weight: 참신성 가중치 (enable_diversity=True일 때)
        mmr_lambda: MMR 알고리즘 lambda 파라미터 (enable_diversity=True일 때)
    
    Returns:
        [{"job_id", "score", "similarity", "cf_score", ...}, ...]
    """
    # Content-based 추천
    cb_recommendations = get_content_based_recommendations(resume_id, top_n=top_n*2)
    
    # Collaborative Filtering 추천
    cf_recommendations = get_collaborative_recommendations(resume_id, top_n=top_n*2)
    
    if strategy == "weighted":
        # 가중치 합산 전략
        results = _weighted_hybrid(cb_recommendations, cf_recommendations, top_n, content_weight, cf_weight)
    
    elif strategy == "cascade":
        # Cascade 전략: Content-based 우선, 부족하면 CF로 채움
        results = _cascade_hybrid(cb_recommendations, cf_recommendations, top_n)
    
    elif strategy == "mixed":
        # Mixed 전략: 번갈아가며 섞기
        results = _mixed_hybrid(cb_recommendations, cf_recommendations, top_n)
    
    else:
        raise ValueError(f"지원하지 않는 전략: {strategy}")
    
    # 다양성/참신성 재정렬
    if enable_diversity and results:
        try:
            # 이력서 임베딩 조회
            engine = create_engine(DATABASE_URL)
            resume_query = f"""
            SELECT id, embedding_array
            FROM {DB_SCHEMA}.cover_letter_samples
            WHERE id = :resume_id
            """
            
            with engine.connect() as conn:
                resume_result = conn.execute(text(resume_query), {"resume_id": resume_id}).fetchone()
            
            if resume_result:
                resume_embedding = parse_embedding(resume_result[1])
                
                # 채용공고 임베딩 조회
                job_ids = [rec['job_id'] for rec in results]
                jobs_query = f"""
                SELECT id, embedding_array
                FROM {DB_SCHEMA}.job_postings
                WHERE id = ANY(:job_ids) AND embedding_array IS NOT NULL
                """
                
                with engine.connect() as conn:
                    jobs_df = pd.read_sql(text(jobs_query), conn, params={"job_ids": job_ids})
                
                job_embeddings = {}
                for _, row in jobs_df.iterrows():
                    emb = parse_embedding(row['embedding_array'])
                    if emb is not None:
                        job_embeddings[row['id']] = emb
                
                # 다양성/참신성 재정렬
                reranker = get_diversity_reranker()
                
                # 연관성 가중치 조정 (나머지 가중치)
                relevance_weight = 1.0 - diversity_weight - novelty_weight
                
                results = reranker.hybrid_rerank(
                    recommendations=results,
                    resume_embedding=resume_embedding,
                    job_embeddings=job_embeddings,
                    user_id=resume_id,
                    diversity_weight=diversity_weight,
                    novelty_weight=novelty_weight,
                    relevance_weight=relevance_weight,
                    mmr_lambda=mmr_lambda,
                    top_n=top_n
                )
        except Exception as e:
            print(f"다양성/참신성 재정렬 실패 (기본 추천 반환): {e}")
    
    return results


def _weighted_hybrid(
    cb_recs: List[dict], 
    cf_recs: List[dict], 
    top_n: int,
    content_weight: float,
    cf_weight: float
) -> List[dict]:
    """가중치 합산 하이브리드"""
    # 모든 채용공고를 딕셔너리로 통합
    all_jobs = {}
    
    # Content-based 점수 정규화 (0~1)
    if cb_recs:
        max_similarity = max(r['similarity'] for r in cb_recs)
        min_similarity = min(r['similarity'] for r in cb_recs)
        similarity_range = max_similarity - min_similarity if max_similarity != min_similarity else 1
        
        for rec in cb_recs:
            job_id = rec['job_id']
            normalized_similarity = (rec['similarity'] - min_similarity) / similarity_range
            
            all_jobs[job_id] = {
                **rec,
                "normalized_similarity": normalized_similarity,
                "cf_score": 0,
                "normalized_cf_score": 0
            }
    
    # Collaborative Filtering 점수 정규화 (0~1)
    if cf_recs:
        max_cf = max(r['cf_score'] for r in cf_recs)
        min_cf = min(r['cf_score'] for r in cf_recs)
        cf_range = max_cf - min_cf if max_cf != min_cf else 1
        
        for rec in cf_recs:
            job_id = rec['job_id']
            normalized_cf = (rec['cf_score'] - min_cf) / cf_range
            
            if job_id in all_jobs:
                all_jobs[job_id]['cf_score'] = rec['cf_score']
                all_jobs[job_id]['normalized_cf_score'] = normalized_cf
            else:
                all_jobs[job_id] = {
                    **rec,
                    "similarity": 0,
                    "normalized_similarity": 0,
                    "normalized_cf_score": normalized_cf
                }
    
    # 하이브리드 점수 계산
    for job_id, job_data in all_jobs.items():
        hybrid_score = (
            content_weight * job_data['normalized_similarity'] +
            cf_weight * job_data['normalized_cf_score']
        )
        job_data['hybrid_score'] = hybrid_score
        job_data['strategy'] = 'weighted'
    
    # 정렬 및 Top-N
    recommendations = sorted(all_jobs.values(), key=lambda x: x['hybrid_score'], reverse=True)
    return recommendations[:top_n]


def _cascade_hybrid(cb_recs: List[dict], cf_recs: List[dict], top_n: int) -> List[dict]:
    """Cascade 하이브리드: Content-based 우선"""
    results = []
    seen_jobs = set()
    
    # 1. Content-based 추천 먼저 추가
    for rec in cb_recs:
        if len(results) >= top_n:
            break
        if rec['job_id'] not in seen_jobs:
            rec['hybrid_score'] = rec['similarity']
            rec['strategy'] = 'cascade-content'
            results.append(rec)
            seen_jobs.add(rec['job_id'])
    
    # 2. 부족하면 Collaborative Filtering 추천 추가
    for rec in cf_recs:
        if len(results) >= top_n:
            break
        if rec['job_id'] not in seen_jobs:
            rec['hybrid_score'] = rec['cf_score']
            rec['strategy'] = 'cascade-collaborative'
            results.append(rec)
            seen_jobs.add(rec['job_id'])
    
    return results


def _mixed_hybrid(cb_recs: List[dict], cf_recs: List[dict], top_n: int) -> List[dict]:
    """Mixed 하이브리드: 번갈아가며 섞기"""
    results = []
    seen_jobs = set()
    
    cb_idx = 0
    cf_idx = 0
    
    while len(results) < top_n:
        # Content-based에서 하나
        while cb_idx < len(cb_recs):
            rec = cb_recs[cb_idx]
            cb_idx += 1
            if rec['job_id'] not in seen_jobs:
                rec['hybrid_score'] = rec['similarity']
                rec['strategy'] = 'mixed-content'
                results.append(rec)
                seen_jobs.add(rec['job_id'])
                break
        
        if len(results) >= top_n:
            break
        
        # Collaborative Filtering에서 하나
        while cf_idx < len(cf_recs):
            rec = cf_recs[cf_idx]
            cf_idx += 1
            if rec['job_id'] not in seen_jobs:
                rec['hybrid_score'] = rec['cf_score']
                rec['strategy'] = 'mixed-collaborative'
                results.append(rec)
                seen_jobs.add(rec['job_id'])
                break
        
        # 둘 다 소진되면 종료
        if cb_idx >= len(cb_recs) and cf_idx >= len(cf_recs):
            break
    
    return results


# API 응답 모델
class HybridRecommendationResponse(BaseModel):
    """하이브리드 추천 응답"""
    job_id: int
    title: str
    company: str
    hybrid_score: float
    similarity: Optional[float] = None
    cf_score: Optional[float] = None
    strategy: str
    source: Optional[str] = None
    # 다양성/참신성 관련 필드
    final_score: Optional[float] = None
    diversity_score: Optional[float] = None
    novelty_score: Optional[float] = None
    user_novelty: Optional[float] = None
    recency_factor: Optional[float] = None


class HybridRecommendationsListResponse(BaseModel):
    """하이브리드 추천 목록 응답"""
    resume_id: int
    total_count: int
    strategy: str
    content_weight: float
    cf_weight: float
    recommendations: List[HybridRecommendationResponse]
    generated_at: datetime


@router.get("/jobs/{resume_id}", response_model=HybridRecommendationsListResponse)
async def get_hybrid_recommendations(
    resume_id: int,
    top_n: int = Query(10, ge=1, le=50, description="추천 개수"),
    strategy: Literal["weighted", "cascade", "mixed"] = Query("weighted", description="통합 전략"),
    content_weight: float = Query(0.6, ge=0, le=1, description="Content-based 가중치"),
    cf_weight: float = Query(0.4, ge=0, le=1, description="Collaborative Filtering 가중치"),
    enable_diversity: bool = Query(False, description="다양성/참신성 재정렬 활성화"),
    diversity_weight: float = Query(0.3, ge=0, le=1, description="다양성 가중치"),
    novelty_weight: float = Query(0.2, ge=0, le=1, description="참신성 가중치"),
    mmr_lambda: float = Query(0.7, ge=0, le=1, description="MMR lambda (유사도 vs 다양성)")
):
    """
    하이브리드 채용공고 추천 (Content-based + Collaborative Filtering + Diversity/Novelty)
    
    - **resume_id**: 이력서 ID
    - **top_n**: 추천 개수 (기본값: 10)
    - **strategy**: 통합 전략
        - `weighted`: 가중치 합산 (기본값)
        - `cascade`: Content-based 우선, 부족하면 CF 추가
        - `mixed`: 번갈아가며 섞기
    - **content_weight**: Content-based 가중치 (weighted 전략용, 기본값: 0.6)
    - **cf_weight**: Collaborative Filtering 가중치 (weighted 전략용, 기본값: 0.4)
    - **enable_diversity**: 다양성/참신성 재정렬 활성화 (기본값: False)
    - **diversity_weight**: 다양성 가중치 (기본값: 0.3)
    - **novelty_weight**: 참신성 가중치 (기본값: 0.2)
    - **mmr_lambda**: MMR 알고리즘 lambda 파라미터 (기본값: 0.7, 1에 가까울수록 유사도 중시)
    """
    try:
        recommendations = hybrid_recommend(
            resume_id=resume_id,
            top_n=top_n,
            content_weight=content_weight,
            cf_weight=cf_weight,
            strategy=strategy,
            enable_diversity=enable_diversity,
            diversity_weight=diversity_weight,
            novelty_weight=novelty_weight,
            mmr_lambda=mmr_lambda
        )
        
        if not recommendations:
            raise HTTPException(
                status_code=404,
                detail=f"이력서 ID {resume_id}에 대한 추천을 생성할 수 없습니다."
            )
        
        return HybridRecommendationsListResponse(
            resume_id=resume_id,
            total_count=len(recommendations),
            strategy=strategy,
            content_weight=content_weight,
            cf_weight=cf_weight,
            recommendations=[
                HybridRecommendationResponse(**rec) for rec in recommendations
            ],
            generated_at=datetime.now()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"하이브리드 추천 생성 중 오류: {str(e)}")


@router.get("/stats")
async def get_hybrid_stats():
    """하이브리드 추천 시스템 통계"""
    try:
        engine = create_engine(DATABASE_URL)
        
        # Content-based 데이터 통계
        with engine.connect() as conn:
            resumes_count = conn.execute(
                text(f"SELECT COUNT(*) FROM {DB_SCHEMA}.cover_letter_samples WHERE embedding_array IS NOT NULL")
            ).scalar()
            
            jobs_count = conn.execute(
                text(f"SELECT COUNT(*) FROM {DB_SCHEMA}.job_postings WHERE embedding_array IS NOT NULL")
            ).scalar()
            
            interactions_count = conn.execute(
                text(f"SELECT COUNT(*) FROM {DB_SCHEMA}.user_interactions")
            ).scalar()
            
            unique_users = conn.execute(
                text(f"SELECT COUNT(DISTINCT resume_id) FROM {DB_SCHEMA}.user_interactions")
            ).scalar()
            
            unique_items = conn.execute(
                text(f"SELECT COUNT(DISTINCT job_id) FROM {DB_SCHEMA}.user_interactions")
            ).scalar()
        
        # Collaborative Filtering 모델 상태
        cf_available = False
        cf_users = 0
        cf_items = 0
        sparsity = 0.0
        
        try:
            cf_recommender = get_cf_recommender()
            cf_available = True
            cf_users = len(cf_recommender.user_ids) if cf_recommender.user_ids else 0
            cf_items = len(cf_recommender.item_ids) if cf_recommender.item_ids else 0
            
            if cf_recommender.user_item_matrix is not None:
                total_cells = cf_users * cf_items
                filled_cells = cf_recommender.user_item_matrix.nnz
                sparsity = 1 - (filled_cells / total_cells) if total_cells > 0 else 1.0
        except:
            pass
        
        return {
            "content_based": {
                "resumes_with_embeddings": resumes_count,
                "jobs_with_embeddings": jobs_count
            },
            "collaborative_filtering": {
                "available": cf_available,
                "total_interactions": interactions_count,
                "unique_users": unique_users,
                "unique_items": unique_items,
                "matrix_users": cf_users,
                "matrix_items": cf_items,
                "sparsity": round(sparsity, 4)
            },
            "hybrid": {
                "strategies_available": ["weighted", "cascade", "mixed"],
                "default_strategy": "weighted",
                "default_content_weight": 0.6,
                "default_cf_weight": 0.4
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 조회 중 오류: {str(e)}")
