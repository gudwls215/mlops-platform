"""
추천 다양성 및 참신성 알고리즘
MMR (Maximal Marginal Relevance) 및 Novelty Score 기반
"""

import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import os
from dotenv import load_dotenv

load_dotenv()

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


class DiversityNoveltyReranker:
    """추천 결과의 다양성과 참신성을 향상시키는 재정렬 시스템"""
    
    def __init__(self):
        self.engine = create_engine(DATABASE_URL)
    
    def mmr_rerank(
        self,
        recommendations: List[Dict],
        resume_embedding: np.ndarray,
        job_embeddings: Dict[int, np.ndarray],
        lambda_param: float = 0.5,
        top_n: int = 10
    ) -> List[Dict]:
        """
        MMR (Maximal Marginal Relevance) 알고리즘으로 재정렬
        
        Args:
            recommendations: 추천 결과 리스트 [{"job_id": int, "similarity": float, ...}, ...]
            resume_embedding: 이력서 임베딩 벡터
            job_embeddings: {job_id: embedding} 딕셔너리
            lambda_param: 유사도와 다양성 간의 균형 파라미터 (0~1)
                         1에 가까울수록 유사도 중시, 0에 가까울수록 다양성 중시
            top_n: 최종 선택할 추천 개수
        
        Returns:
            재정렬된 추천 리스트
        """
        if not recommendations or len(recommendations) == 0:
            return []
        
        # 임베딩이 없는 항목 제거
        valid_recommendations = [
            rec for rec in recommendations
            if rec['job_id'] in job_embeddings
        ]
        
        if not valid_recommendations:
            return recommendations[:top_n]
        
        # 초기 유사도 점수 정규화
        scores = np.array([rec.get('similarity', rec.get('cf_score', 0)) 
                          for rec in valid_recommendations])
        if scores.max() > 0:
            normalized_scores = scores / scores.max()
        else:
            normalized_scores = scores
        
        # 선택된 항목과 후보 항목
        selected = []
        candidates = list(range(len(valid_recommendations)))
        selected_embeddings = []
        
        resume_emb_2d = resume_embedding.reshape(1, -1)
        
        # 첫 번째 항목은 최고 점수로 선택
        first_idx = candidates[np.argmax(normalized_scores)]
        selected.append(first_idx)
        candidates.remove(first_idx)
        selected_embeddings.append(job_embeddings[valid_recommendations[first_idx]['job_id']])
        
        # 나머지 항목 선택 (MMR)
        while len(selected) < top_n and candidates:
            mmr_scores = []
            
            for idx in candidates:
                job_id = valid_recommendations[idx]['job_id']
                job_emb = job_embeddings[job_id].reshape(1, -1)
                
                # 유사도 (이력서와의 유사도)
                relevance = cosine_similarity(resume_emb_2d, job_emb)[0][0]
                
                # 다양성 (이미 선택된 항목들과의 최대 유사도)
                if selected_embeddings:
                    selected_emb_matrix = np.vstack(selected_embeddings)
                    max_similarity = cosine_similarity(job_emb, selected_emb_matrix)[0].max()
                else:
                    max_similarity = 0
                
                # MMR 점수 계산
                mmr = lambda_param * relevance - (1 - lambda_param) * max_similarity
                mmr_scores.append(mmr)
            
            # 최고 MMR 점수 선택
            best_idx = candidates[np.argmax(mmr_scores)]
            selected.append(best_idx)
            candidates.remove(best_idx)
            selected_embeddings.append(job_embeddings[valid_recommendations[best_idx]['job_id']])
        
        # 재정렬된 결과 반환
        reranked = [valid_recommendations[idx] for idx in selected]
        
        # MMR 순위 추가
        for rank, rec in enumerate(reranked, 1):
            rec['mmr_rank'] = rank
        
        return reranked
    
    def calculate_novelty_scores(
        self,
        recommendations: List[Dict],
        user_id: int,
        time_decay_days: int = 30
    ) -> List[Dict]:
        """
        추천 항목의 참신성(Novelty) 점수 계산
        
        Args:
            recommendations: 추천 결과 리스트
            user_id: 사용자 ID
            time_decay_days: 참신성 감쇠 기간 (일)
        
        Returns:
            novelty_score가 추가된 추천 리스트
        """
        if not recommendations:
            return recommendations
        
        job_ids = [rec['job_id'] for rec in recommendations]
        
        # 사용자가 본 채용공고 조회
        viewed_query = f"""
        SELECT job_id, MAX(interaction_time) as last_viewed
        FROM {DB_SCHEMA}.user_interactions
        WHERE user_id = :user_id 
          AND job_id = ANY(:job_ids)
          AND interaction_type IN ('view', 'click')
        GROUP BY job_id
        """
        
        try:
            with self.engine.connect() as conn:
                viewed_df = pd.read_sql(
                    text(viewed_query),
                    conn,
                    params={"user_id": user_id, "job_ids": job_ids}
                )
        except Exception:
            # user_interactions 테이블이 없거나 오류 발생 시
            viewed_df = pd.DataFrame(columns=['job_id', 'last_viewed'])
        
        viewed_dict = dict(zip(viewed_df['job_id'], viewed_df['last_viewed']))
        
        # 채용공고 등록일 조회 (created_at 사용)
        posted_query = f"""
        SELECT id, created_at
        FROM {DB_SCHEMA}.job_postings
        WHERE id = ANY(:job_ids)
        """
        
        with self.engine.connect() as conn:
            posted_df = pd.read_sql(
                text(posted_query),
                conn,
                params={"job_ids": job_ids}
            )
        
        posted_dict = dict(zip(posted_df['id'], posted_df['created_at']))
        
        current_time = datetime.now()
        
        # 각 추천 항목의 참신성 점수 계산
        for rec in recommendations:
            job_id = rec['job_id']
            
            # 1. 사용자가 본 적이 있는지 확인
            if job_id in viewed_dict:
                # 본 적이 있으면 시간 경과에 따라 점수 부여
                last_viewed = viewed_dict[job_id]
                if isinstance(last_viewed, str):
                    last_viewed = datetime.fromisoformat(last_viewed)
                # Timezone aware인 경우 naive로 변환
                if hasattr(last_viewed, 'tzinfo') and last_viewed.tzinfo is not None:
                    last_viewed = last_viewed.replace(tzinfo=None)
                
                days_since_view = (current_time - last_viewed).days
                
                # 시간 경과에 따른 감쇠 (0~1)
                time_factor = min(days_since_view / time_decay_days, 1.0)
                user_novelty = time_factor
            else:
                # 본 적이 없으면 완전히 새로운 항목
                user_novelty = 1.0
            
            # 2. 채용공고의 등록일 확인 (최근 공고일수록 높은 점수)
            if job_id in posted_dict:
                posted_date = posted_dict[job_id]
                if isinstance(posted_date, str):
                    posted_date = datetime.fromisoformat(posted_date)
                # Timezone aware인 경우 naive로 변환
                if hasattr(posted_date, 'tzinfo') and posted_date.tzinfo is not None:
                    posted_date = posted_date.replace(tzinfo=None)
                
                days_since_posted = (current_time - posted_date).days
                
                # 최근 30일 이내는 1.0, 그 이후는 선형 감소 (최소 0.5)
                if days_since_posted <= 30:
                    recency_factor = 1.0
                else:
                    recency_factor = max(0.5, 1.0 - (days_since_posted - 30) / 180)
            else:
                recency_factor = 0.7  # 기본값
            
            # 3. 회사/직무 다양성 (간단한 버전: 추후 확장 가능)
            # 현재는 사용자 novelty와 recency를 결합
            novelty_score = (user_novelty * 0.6 + recency_factor * 0.4)
            
            rec['novelty_score'] = novelty_score
            rec['user_novelty'] = user_novelty
            rec['recency_factor'] = recency_factor
        
        return recommendations
    
    def hybrid_rerank(
        self,
        recommendations: List[Dict],
        resume_embedding: np.ndarray,
        job_embeddings: Dict[int, np.ndarray],
        user_id: int,
        diversity_weight: float = 0.3,
        novelty_weight: float = 0.2,
        relevance_weight: float = 0.5,
        mmr_lambda: float = 0.7,
        top_n: int = 10
    ) -> List[Dict]:
        """
        다양성, 참신성, 연관성을 모두 고려한 하이브리드 재정렬
        
        Args:
            recommendations: 추천 결과 리스트
            resume_embedding: 이력서 임베딩
            job_embeddings: 채용공고 임베딩 딕셔너리
            user_id: 사용자 ID
            diversity_weight: 다양성 가중치
            novelty_weight: 참신성 가중치
            relevance_weight: 연관성 가중치
            mmr_lambda: MMR 알고리즘의 lambda 파라미터
            top_n: 최종 결과 개수
        
        Returns:
            최종 재정렬된 추천 리스트
        """
        if not recommendations:
            return []
        
        # 가중치 정규화
        total_weight = diversity_weight + novelty_weight + relevance_weight
        diversity_weight /= total_weight
        novelty_weight /= total_weight
        relevance_weight /= total_weight
        
        # 1. MMR로 다양성 있는 top 2N 선택
        mmr_candidates = self.mmr_rerank(
            recommendations=recommendations,
            resume_embedding=resume_embedding,
            job_embeddings=job_embeddings,
            lambda_param=mmr_lambda,
            top_n=min(top_n * 2, len(recommendations))
        )
        
        # 2. 참신성 점수 계산
        mmr_candidates = self.calculate_novelty_scores(
            recommendations=mmr_candidates,
            user_id=user_id
        )
        
        # 3. 종합 점수 계산
        for rec in mmr_candidates:
            # 연관성 점수 (원래 점수)
            relevance = rec.get('similarity', rec.get('cf_score', 0))
            
            # 다양성 점수 (MMR 순위 기반: 상위일수록 높은 점수)
            mmr_rank = rec.get('mmr_rank', len(mmr_candidates))
            diversity_score = 1.0 - (mmr_rank - 1) / len(mmr_candidates)
            
            # 참신성 점수
            novelty = rec.get('novelty_score', 0.5)
            
            # 최종 점수
            final_score = (
                relevance_weight * relevance +
                diversity_weight * diversity_score +
                novelty_weight * novelty
            )
            
            rec['final_score'] = final_score
            rec['diversity_score'] = diversity_score
        
        # 최종 점수로 정렬
        mmr_candidates.sort(key=lambda x: x['final_score'], reverse=True)
        
        return mmr_candidates[:top_n]
    
    def analyze_diversity(
        self,
        recommendations: List[Dict],
        job_embeddings: Dict[int, np.ndarray]
    ) -> Dict:
        """
        추천 결과의 다양성 분석
        
        Returns:
            {
                "avg_similarity": float,  # 추천 항목 간 평균 유사도
                "min_similarity": float,  # 최소 유사도
                "max_similarity": float,  # 최대 유사도
                "diversity_score": float  # 다양성 점수 (0~1, 높을수록 다양함)
            }
        """
        if len(recommendations) < 2:
            return {
                "avg_similarity": 0.0,
                "min_similarity": 0.0,
                "max_similarity": 0.0,
                "diversity_score": 1.0
            }
        
        # 임베딩 추출
        embeddings = []
        for rec in recommendations:
            if rec['job_id'] in job_embeddings:
                embeddings.append(job_embeddings[rec['job_id']])
        
        if len(embeddings) < 2:
            return {
                "avg_similarity": 0.0,
                "min_similarity": 0.0,
                "max_similarity": 0.0,
                "diversity_score": 1.0
            }
        
        # 추천 항목 간 유사도 계산
        embeddings_matrix = np.vstack(embeddings)
        similarity_matrix = cosine_similarity(embeddings_matrix)
        
        # 대각선 제외 (자기 자신과의 유사도)
        mask = np.ones(similarity_matrix.shape, dtype=bool)
        np.fill_diagonal(mask, False)
        similarities = similarity_matrix[mask]
        
        avg_sim = similarities.mean()
        min_sim = similarities.min()
        max_sim = similarities.max()
        
        # 다양성 점수 (1 - 평균 유사도)
        diversity_score = 1.0 - avg_sim
        
        return {
            "avg_similarity": float(avg_sim),
            "min_similarity": float(min_sim),
            "max_similarity": float(max_sim),
            "diversity_score": float(diversity_score)
        }


def parse_embedding(embedding_str: str) -> np.ndarray:
    """임베딩 문자열 파싱"""
    if embedding_str is None:
        return None
    embedding_str = embedding_str.strip('[]')
    values = [float(x.strip()) for x in embedding_str.split(',')]
    return np.array(values)


if __name__ == "__main__":
    """테스트 코드"""
    from sqlalchemy import create_engine, text
    
    print("=" * 60)
    print("추천 다양성 및 참신성 시스템 테스트")
    print("=" * 60)
    
    reranker = DiversityNoveltyReranker()
    engine = create_engine(DATABASE_URL)
    
    # 테스트용 이력서 ID
    test_resume_id = 1
    
    # 이력서 임베딩 조회
    resume_query = f"""
    SELECT id, embedding_array
    FROM {DB_SCHEMA}.cover_letter_samples
    WHERE id = :resume_id
    """
    
    with engine.connect() as conn:
        resume_result = conn.execute(text(resume_query), {"resume_id": test_resume_id}).fetchone()
    
    if not resume_result:
        print(f"❌ 이력서 ID {test_resume_id}를 찾을 수 없습니다.")
        exit(1)
    
    resume_embedding = parse_embedding(resume_result[1])
    
    # 상위 50개 채용공고 조회
    jobs_query = f"""
    SELECT id, title, company, embedding_array
    FROM {DB_SCHEMA}.job_postings
    WHERE embedding_array IS NOT NULL
    LIMIT 50
    """
    
    with engine.connect() as conn:
        jobs_df = pd.read_sql(text(jobs_query), conn)
    
    # 임베딩 파싱 및 유사도 계산
    job_embeddings = {}
    recommendations = []
    
    resume_emb_2d = resume_embedding.reshape(1, -1)
    
    for _, row in jobs_df.iterrows():
        emb = parse_embedding(row['embedding_array'])
        if emb is not None:
            job_embeddings[row['id']] = emb
            similarity = cosine_similarity(resume_emb_2d, emb.reshape(1, -1))[0][0]
            recommendations.append({
                "job_id": row['id'],
                "title": row['title'],
                "company": row['company'],
                "similarity": similarity
            })
    
    # 유사도 기준 정렬
    recommendations.sort(key=lambda x: x['similarity'], reverse=True)
    
    print(f"\n✅ 테스트 데이터: 이력서 ID {test_resume_id}, 채용공고 {len(recommendations)}개\n")
    
    # 1. 기본 추천 (Top 10)
    print("=" * 60)
    print("1. 기본 추천 (유사도 기준 Top 10)")
    print("=" * 60)
    baseline = recommendations[:10]
    for i, rec in enumerate(baseline, 1):
        print(f"{i:2d}. [{rec['company']}] {rec['title'][:40]:40s} (유사도: {rec['similarity']:.3f})")
    
    baseline_diversity = reranker.analyze_diversity(baseline, job_embeddings)
    print(f"\n다양성 분석:")
    print(f"  - 평균 유사도: {baseline_diversity['avg_similarity']:.3f}")
    print(f"  - 다양성 점수: {baseline_diversity['diversity_score']:.3f}")
    
    # 2. MMR 재정렬
    print("\n" + "=" * 60)
    print("2. MMR 재정렬 (lambda=0.5, 다양성 중시)")
    print("=" * 60)
    mmr_results = reranker.mmr_rerank(
        recommendations=recommendations[:30],
        resume_embedding=resume_embedding,
        job_embeddings=job_embeddings,
        lambda_param=0.5,
        top_n=10
    )
    
    for i, rec in enumerate(mmr_results, 1):
        print(f"{i:2d}. [{rec['company']}] {rec['title'][:40]:40s} (유사도: {rec['similarity']:.3f})")
    
    mmr_diversity = reranker.analyze_diversity(mmr_results, job_embeddings)
    print(f"\n다양성 분석:")
    print(f"  - 평균 유사도: {mmr_diversity['avg_similarity']:.3f}")
    print(f"  - 다양성 점수: {mmr_diversity['diversity_score']:.3f}")
    print(f"  - 다양성 개선: {(mmr_diversity['diversity_score'] - baseline_diversity['diversity_score']) * 100:.1f}%")
    
    # 3. 참신성 점수 추가
    print("\n" + "=" * 60)
    print("3. 참신성 점수 계산")
    print("=" * 60)
    novelty_results = reranker.calculate_novelty_scores(
        recommendations=recommendations[:10],
        user_id=test_resume_id
    )
    
    for i, rec in enumerate(novelty_results, 1):
        print(f"{i:2d}. [{rec['company']}] {rec['title'][:40]:40s}")
        print(f"     유사도: {rec['similarity']:.3f}, 참신성: {rec['novelty_score']:.3f}")
    
    # 4. 하이브리드 재정렬
    print("\n" + "=" * 60)
    print("4. 하이브리드 재정렬 (다양성 + 참신성 + 연관성)")
    print("=" * 60)
    hybrid_results = reranker.hybrid_rerank(
        recommendations=recommendations[:30],
        resume_embedding=resume_embedding,
        job_embeddings=job_embeddings,
        user_id=test_resume_id,
        diversity_weight=0.3,
        novelty_weight=0.2,
        relevance_weight=0.5,
        top_n=10
    )
    
    for i, rec in enumerate(hybrid_results, 1):
        print(f"{i:2d}. [{rec['company']}] {rec['title'][:40]:40s}")
        print(f"     유사도: {rec['similarity']:.3f}, 참신성: {rec['novelty_score']:.3f}, 최종점수: {rec['final_score']:.3f}")
    
    hybrid_diversity = reranker.analyze_diversity(hybrid_results, job_embeddings)
    print(f"\n다양성 분석:")
    print(f"  - 평균 유사도: {hybrid_diversity['avg_similarity']:.3f}")
    print(f"  - 다양성 점수: {hybrid_diversity['diversity_score']:.3f}")
    print(f"  - 다양성 개선: {(hybrid_diversity['diversity_score'] - baseline_diversity['diversity_score']) * 100:.1f}%")
    
    print("\n" + "=" * 60)
    print("✅ 테스트 완료!")
    print("=" * 60)
