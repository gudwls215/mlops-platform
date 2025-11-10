"""
채용공고 추천 API
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
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

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])

# 데이터베이스 연결 설정
DB_HOST = os.getenv('POSTGRES_HOST', '114.202.2.226')
DB_PORT = os.getenv('POSTGRES_PORT', '5433')
DB_NAME = os.getenv('POSTGRES_DB', 'postgres')
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')
DB_SCHEMA = 'mlops'

# 데이터베이스 URL 생성
import urllib.parse
encoded_password = urllib.parse.quote_plus(DB_PASSWORD)
DATABASE_URL = f"postgresql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 모델 경로
MODEL_DIR = project_root / 'models'
FINAL_MODEL_PATH = MODEL_DIR / 'final_model.joblib'

# 추천 시스템 인스턴스 (싱글톤)
_recommender = None
_model = None


def load_model():
    """최종 모델 로드"""
    global _model
    if _model is None and FINAL_MODEL_PATH.exists():
        _model = joblib.load(FINAL_MODEL_PATH)
        print(f"모델 로드 완료: {FINAL_MODEL_PATH}")
    return _model


def parse_embedding(embedding_str: str) -> np.ndarray:
    """임베딩 문자열을 numpy 배열로 변환"""
    if not embedding_str:
        return None
    try:
        embedding = [float(x) for x in embedding_str.split(',')]
        return np.array(embedding)
    except Exception as e:
        print(f"임베딩 파싱 오류: {e}")
        return None


def recommend_jobs(resume_id: int, top_n: int = 10) -> List[dict]:
    """채용공고 추천"""
    engine = create_engine(DATABASE_URL)
    
    # 1. 이력서 임베딩 조회
    resume_query = f"""
    SELECT 
        id,
        embedding_array,
        keywords
    FROM {DB_SCHEMA}.cover_letter_samples
    WHERE id = :resume_id AND embedding_array IS NOT NULL
    """
    
    with engine.connect() as conn:
        resume_result = pd.read_sql(text(resume_query), conn, params={'resume_id': resume_id})
    
    if len(resume_result) == 0:
        return []
    
    resume_row = resume_result.iloc[0]
    resume_embedding = parse_embedding(resume_row['embedding_array'])
    
    if resume_embedding is None:
        return []
    
    # 2. 채용공고 임베딩 조회
    jobs_query = f"""
    SELECT 
        id,
        company,
        title,
        location,
        experience_level,
        employment_type,
        salary_min,
        salary_max,
        embedding_array,
        keywords
    FROM {DB_SCHEMA}.job_postings
    WHERE embedding_array IS NOT NULL
    ORDER BY id
    """
    
    with engine.connect() as conn:
        jobs_df = pd.read_sql(text(jobs_query), conn)
    
    if len(jobs_df) == 0:
        return []
    
    # 3. 임베딩 파싱
    job_embeddings = []
    valid_indices = []
    
    for idx, row in jobs_df.iterrows():
        embedding = parse_embedding(row['embedding_array'])
        if embedding is not None:
            job_embeddings.append(embedding)
            valid_indices.append(idx)
    
    if len(job_embeddings) == 0:
        return []
    
    jobs_df = jobs_df.iloc[valid_indices].reset_index(drop=True)
    job_embeddings = np.array(job_embeddings)
    
    # 4. 유사도 계산
    resume_embedding_2d = resume_embedding.reshape(1, -1)
    similarities = cosine_similarity(resume_embedding_2d, job_embeddings)[0]
    
    # 5. 합격 확률 예측
    model = load_model()
    if model is not None:
        try:
            success_prob = float(model.predict_proba(resume_embedding_2d)[0, 1])
        except:
            success_prob = 0.5
    else:
        success_prob = 0.5
    
    # 6. 상위 N개 선택
    top_indices = np.argsort(similarities)[::-1][:top_n]
    
    # 7. 추천 결과 생성
    recommendations = []
    for rank, idx in enumerate(top_indices, 1):
        job = jobs_df.iloc[idx]
        similarity = similarities[idx]
        
        # 추천 이유 생성
        reason = "매우 높은 적합도" if similarity > 0.8 else "높은 적합도" if similarity > 0.6 else "적합도 양호"
        
        recommendations.append({
            'rank': rank,
            'job_id': int(job['id']),
            'company': job['company'],
            'title': job['title'],
            'location': job['location'],
            'experience_level': job['experience_level'],
            'employment_type': job['employment_type'],
            'salary_min': int(job['salary_min']) if pd.notna(job['salary_min']) else None,
            'salary_max': int(job['salary_max']) if pd.notna(job['salary_max']) else None,
            'similarity_score': float(similarity),
            'success_probability': float(success_prob),
            'recommendation_reason': reason
        })
    
    return recommendations


class RecommendationResponse(BaseModel):
    """추천 결과 응답"""
    rank: int
    job_id: int
    company: str
    title: str
    location: str
    experience_level: Optional[str]
    employment_type: Optional[str]
    salary_min: Optional[int]
    salary_max: Optional[int]
    similarity_score: float
    success_probability: float
    recommendation_reason: str


class RecommendationsListResponse(BaseModel):
    """추천 목록 응답"""
    resume_id: int
    total_count: int
    recommendations: List[RecommendationResponse]
    generated_at: datetime


@router.get("/jobs/{resume_id}", response_model=RecommendationsListResponse)
async def get_job_recommendations(
    resume_id: int,
    top_n: int = Query(10, ge=1, le=50, description="추천 개수 (최소 1, 최대 50)")
):
    """
    특정 이력서에 대한 채용공고 추천
    
    - **resume_id**: 이력서 ID
    - **top_n**: 추천할 채용공고 개수 (기본값: 10)
    """
    try:
        recommendations = recommend_jobs(resume_id, top_n)
        
        if not recommendations:
            raise HTTPException(
                status_code=404, 
                detail=f"이력서 ID {resume_id}에 대한 추천을 생성할 수 없습니다. 이력서가 존재하지 않거나 임베딩이 없습니다."
            )
        
        return RecommendationsListResponse(
            resume_id=resume_id,
            total_count=len(recommendations),
            recommendations=recommendations,
            generated_at=datetime.now()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"추천 생성 중 오류 발생: {str(e)}")


@router.post("/jobs/{resume_id}/save")
async def save_job_recommendations(
    resume_id: int,
    top_n: int = Query(10, ge=1, le=50, description="추천 개수")
):
    """
    채용공고 추천 생성 및 데이터베이스 저장
    
    - **resume_id**: 이력서 ID
    - **top_n**: 추천할 채용공고 개수
    """
    try:
        recommendations = recommend_jobs(resume_id, top_n)
        
        if not recommendations:
            raise HTTPException(
                status_code=404, 
                detail=f"이력서 ID {resume_id}에 대한 추천을 생성할 수 없습니다."
            )
        
        # 데이터베이스에 저장
        engine = create_engine(DATABASE_URL)
        
        # 테이블 생성 (존재하지 않을 경우)
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {DB_SCHEMA}.job_recommendations (
            id SERIAL PRIMARY KEY,
            resume_id INTEGER NOT NULL,
            job_id INTEGER NOT NULL,
            rank INTEGER NOT NULL,
            similarity_score FLOAT NOT NULL,
            success_probability FLOAT NOT NULL,
            recommendation_reason TEXT,
            created_at TIMESTAMP NOT NULL,
            FOREIGN KEY (resume_id) REFERENCES {DB_SCHEMA}.cover_letter_samples(id),
            FOREIGN KEY (job_id) REFERENCES {DB_SCHEMA}.job_postings(id)
        )
        """
        
        insert_query = f"""
        INSERT INTO {DB_SCHEMA}.job_recommendations 
        (resume_id, job_id, rank, similarity_score, success_probability, recommendation_reason, created_at)
        VALUES (:resume_id, :job_id, :rank, :similarity_score, :success_probability, :recommendation_reason, :created_at)
        """
        
        with engine.connect() as conn:
            # 테이블 생성
            conn.execute(text(create_table_query))
            conn.commit()
            
            # 기존 추천 삭제
            delete_query = f"DELETE FROM {DB_SCHEMA}.job_recommendations WHERE resume_id = :resume_id"
            conn.execute(text(delete_query), {'resume_id': resume_id})
            
            # 새 추천 저장
            for rec in recommendations:
                conn.execute(text(insert_query), {
                    'resume_id': resume_id,
                    'job_id': rec['job_id'],
                    'rank': rec['rank'],
                    'similarity_score': rec['similarity_score'],
                    'success_probability': rec['success_probability'],
                    'recommendation_reason': rec['recommendation_reason'],
                    'created_at': datetime.now()
                })
            
            conn.commit()
        
        return {
            "status": "success",
            "message": f"{len(recommendations)}건의 추천이 저장되었습니다.",
            "resume_id": resume_id,
            "total_saved": len(recommendations)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"추천 저장 중 오류 발생: {str(e)}")


@router.get("/stats")
async def get_recommendation_stats():
    """
    추천 시스템 통계
    
    - 전체 추천 건수
    - 평균 유사도
    - 평균 예상 합격률
    """
    try:
        from sqlalchemy import create_engine, text
        import pandas as pd
        from dotenv import load_dotenv
        import urllib.parse
        
        load_dotenv()
        
        DB_HOST = os.getenv('POSTGRES_HOST', '114.202.2.226')
        DB_PORT = os.getenv('POSTGRES_PORT', '5433')
        DB_NAME = os.getenv('POSTGRES_DB', 'postgres')
        DB_USER = os.getenv('POSTGRES_USER', 'postgres')
        DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')
        DB_SCHEMA = 'mlops'
        
        encoded_password = urllib.parse.quote_plus(DB_PASSWORD)
        DATABASE_URL = f"postgresql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        
        engine = create_engine(DATABASE_URL)
        
        query = f"""
        SELECT 
            COUNT(*) as total_recommendations,
            COUNT(DISTINCT resume_id) as total_resumes,
            AVG(similarity_score) as avg_similarity,
            AVG(success_probability) as avg_success_prob,
            MAX(created_at) as last_updated
        FROM {DB_SCHEMA}.job_recommendations
        """
        
        with engine.connect() as conn:
            result = pd.read_sql(text(query), conn)
        
        if len(result) == 0:
            return {
                "total_recommendations": 0,
                "total_resumes": 0,
                "avg_similarity": 0.0,
                "avg_success_probability": 0.0,
                "last_updated": None
            }
        
        row = result.iloc[0]
        return {
            "total_recommendations": int(row['total_recommendations']),
            "total_resumes": int(row['total_resumes']),
            "avg_similarity": float(row['avg_similarity']) if row['avg_similarity'] else 0.0,
            "avg_success_probability": float(row['avg_success_prob']) if row['avg_success_prob'] else 0.0,
            "last_updated": row['last_updated'].isoformat() if row['last_updated'] else None
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 조회 중 오류 발생: {str(e)}")
