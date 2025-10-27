"""
채용공고 추천 시스템
- Content-based 필터링 구현
- 이력서-채용공고 임베딩 유사도 계산 (Cosine Similarity)
- 최종 모델을 사용한 합격 확률 예측
- 추천 결과 랭킹 및 설명 생성
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv
import joblib
from datetime import datetime
from typing import List, Dict, Tuple

# 환경 변수 로드
load_dotenv()

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
MODEL_DIR = Path(__file__).parent.parent / 'models'
FINAL_MODEL_PATH = MODEL_DIR / 'final_model.joblib'


class JobRecommender:
    """채용공고 추천 시스템"""
    
    def __init__(self):
        self.engine = create_engine(DATABASE_URL)
        self.model = None
        self.load_model()
        
    def load_model(self):
        """최종 모델 로드"""
        if FINAL_MODEL_PATH.exists():
            self.model = joblib.load(FINAL_MODEL_PATH)
            print(f"모델 로드 완료: {FINAL_MODEL_PATH}")
        else:
            print(f"경고: 모델 파일이 없습니다 ({FINAL_MODEL_PATH})")
    
    def parse_embedding(self, embedding_str: str) -> np.ndarray:
        """임베딩 문자열을 numpy 배열로 변환"""
        if not embedding_str:
            return None
        try:
            embedding = [float(x) for x in embedding_str.split(',')]
            return np.array(embedding)
        except Exception as e:
            print(f"임베딩 파싱 오류: {e}")
            return None
    
    def get_resume_embedding(self, resume_id: int) -> Tuple[np.ndarray, Dict]:
        """이력서 임베딩 조회"""
        query = f"""
        SELECT 
            id,
            embedding_array,
            cleaned_content,
            keywords
        FROM {DB_SCHEMA}.cover_letter_samples
        WHERE id = :resume_id AND embedding_array IS NOT NULL
        """
        
        with self.engine.connect() as conn:
            result = pd.read_sql(text(query), conn, params={'resume_id': resume_id})
        
        if len(result) == 0:
            return None, None
        
        row = result.iloc[0]
        embedding = self.parse_embedding(row['embedding_array'])
        
        resume_info = {
            'id': int(row['id']),
            'content': row['cleaned_content'],
            'keywords': row['keywords']
        }
        
        return embedding, resume_info
    
    def get_all_job_embeddings(self) -> pd.DataFrame:
        """모든 채용공고 임베딩 조회"""
        query = f"""
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
            cleaned_description,
            keywords
        FROM {DB_SCHEMA}.job_postings
        WHERE embedding_array IS NOT NULL
        ORDER BY id
        """
        
        with self.engine.connect() as conn:
            df = pd.read_sql(text(query), conn)
        
        print(f"채용공고 로드: {len(df)}건")
        return df
    
    def calculate_similarity(self, resume_embedding: np.ndarray, job_embeddings: np.ndarray) -> np.ndarray:
        """코사인 유사도 계산"""
        resume_embedding = resume_embedding.reshape(1, -1)
        similarities = cosine_similarity(resume_embedding, job_embeddings)[0]
        return similarities
    
    def predict_success_probability(self, resume_embedding: np.ndarray) -> float:
        """합격 확률 예측 (최종 모델 사용)"""
        if self.model is None:
            return 0.5  # 모델이 없으면 기본값
        
        try:
            proba = self.model.predict_proba(resume_embedding.reshape(1, -1))[0, 1]
            return float(proba)
        except Exception as e:
            print(f"예측 오류: {e}")
            return 0.5
    
    def generate_recommendation_reason(self, resume_info: Dict, job_info: Dict, similarity: float) -> str:
        """추천 이유 생성"""
        reasons = []
        
        # 유사도 기반
        if similarity > 0.8:
            reasons.append("매우 높은 적합도")
        elif similarity > 0.6:
            reasons.append("높은 적합도")
        else:
            reasons.append("적합도 양호")
        
        # 키워드 매칭
        resume_keywords = set(resume_info.get('keywords', []) or [])
        job_keywords = set(job_info.get('keywords', []) or [])
        
        if resume_keywords and job_keywords:
            common_keywords = resume_keywords & job_keywords
            if len(common_keywords) > 3:
                reasons.append(f"공통 키워드 {len(common_keywords)}개")
        
        return " / ".join(reasons)
    
    def recommend_jobs(self, resume_id: int, top_n: int = 10) -> List[Dict]:
        """채용공고 추천"""
        print(f"\n{'='*60}")
        print(f"채용공고 추천 시작 (이력서 ID: {resume_id})")
        print(f"{'='*60}")
        
        start_time = datetime.now()
        
        # 1. 이력서 임베딩 조회
        resume_embedding, resume_info = self.get_resume_embedding(resume_id)
        if resume_embedding is None:
            print("오류: 이력서를 찾을 수 없거나 임베딩이 없습니다.")
            return []
        
        print(f"이력서 로드 완료 (ID: {resume_id})")
        
        # 2. 채용공고 임베딩 조회
        jobs_df = self.get_all_job_embeddings()
        if len(jobs_df) == 0:
            print("오류: 채용공고가 없습니다.")
            return []
        
        # 3. 임베딩 파싱
        job_embeddings = []
        valid_indices = []
        
        for idx, row in jobs_df.iterrows():
            embedding = self.parse_embedding(row['embedding_array'])
            if embedding is not None:
                job_embeddings.append(embedding)
                valid_indices.append(idx)
        
        if len(job_embeddings) == 0:
            print("오류: 유효한 채용공고 임베딩이 없습니다.")
            return []
        
        jobs_df = jobs_df.iloc[valid_indices].reset_index(drop=True)
        job_embeddings = np.array(job_embeddings)
        
        print(f"유효한 채용공고: {len(job_embeddings)}건")
        
        # 4. 유사도 계산
        similarities = self.calculate_similarity(resume_embedding, job_embeddings)
        
        # 5. 합격 확률 예측
        success_prob = self.predict_success_probability(resume_embedding)
        print(f"예상 합격 확률: {success_prob:.2%}")
        
        # 6. 상위 N개 선택
        top_indices = np.argsort(similarities)[::-1][:top_n]
        
        # 7. 추천 결과 생성
        recommendations = []
        for rank, idx in enumerate(top_indices, 1):
            job = jobs_df.iloc[idx]
            similarity = similarities[idx]
            
            job_info = {
                'id': int(job['id']),
                'company': job['company'],
                'title': job['title'],
                'location': job['location'],
                'experience_level': job['experience_level'],
                'employment_type': job['employment_type'],
                'salary_min': job['salary_min'],
                'salary_max': job['salary_max'],
                'keywords': job['keywords']
            }
            
            reason = self.generate_recommendation_reason(resume_info, job_info, similarity)
            
            recommendations.append({
                'rank': rank,
                'job_id': int(job['id']),
                'company': job['company'],
                'title': job['title'],
                'location': job['location'],
                'experience_level': job['experience_level'],
                'employment_type': job['employment_type'],
                'salary_min': job['salary_min'],
                'salary_max': job['salary_max'],
                'similarity_score': float(similarity),
                'success_probability': float(success_prob),
                'recommendation_reason': reason
            })
        
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\n추천 완료 (소요 시간: {elapsed:.2f}초)")
        print(f"{'='*60}")
        
        return recommendations
    
    def print_recommendations(self, recommendations: List[Dict]):
        """추천 결과 출력"""
        print("\n" + "="*80)
        print("추천 결과")
        print("="*80)
        
        for rec in recommendations:
            print(f"\n[{rec['rank']}위] {rec['company']} - {rec['title']}")
            print(f"  위치: {rec['location']}")
            print(f"  경력: {rec['experience_level']}")
            print(f"  고용형태: {rec['employment_type']}")
            salary_str = f"{rec['salary_min']:,}원" if rec['salary_min'] else "미정"
            if rec['salary_max']:
                salary_str += f" ~ {rec['salary_max']:,}원"
            print(f"  급여: {salary_str}")
            print(f"  적합도: {rec['similarity_score']:.2%}")
            print(f"  예상 합격률: {rec['success_probability']:.2%}")
            print(f"  추천 이유: {rec['recommendation_reason']}")
    
    def save_recommendations(self, resume_id: int, recommendations: List[Dict]):
        """추천 결과 저장"""
        query = f"""
        INSERT INTO {DB_SCHEMA}.job_recommendations 
        (resume_id, job_id, rank, similarity_score, success_probability, recommendation_reason, created_at)
        VALUES (:resume_id, :job_id, :rank, :similarity_score, :success_probability, :recommendation_reason, :created_at)
        """
        
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
        
        with self.engine.connect() as conn:
            # 테이블 생성
            conn.execute(text(create_table_query))
            conn.commit()
            
            # 기존 추천 삭제
            delete_query = f"DELETE FROM {DB_SCHEMA}.job_recommendations WHERE resume_id = :resume_id"
            conn.execute(text(delete_query), {'resume_id': resume_id})
            
            # 새 추천 저장
            for rec in recommendations:
                conn.execute(text(query), {
                    'resume_id': resume_id,
                    'job_id': rec['job_id'],
                    'rank': rec['rank'],
                    'similarity_score': rec['similarity_score'],
                    'success_probability': rec['success_probability'],
                    'recommendation_reason': rec['recommendation_reason'],
                    'created_at': datetime.now()
                })
            
            conn.commit()
        
        print(f"\n추천 결과 저장 완료: {len(recommendations)}건")
    
    def test_recommendation(self, resume_id: int, top_n: int = 10):
        """추천 시스템 테스트"""
        recommendations = self.recommend_jobs(resume_id, top_n)
        
        if recommendations:
            self.print_recommendations(recommendations)
            self.save_recommendations(resume_id, recommendations)
        else:
            print("추천 결과가 없습니다.")


if __name__ == "__main__":
    # 추천 시스템 초기화
    recommender = JobRecommender()
    
    # 테스트: 첫 번째 이력서에 대한 추천
    print("추천 시스템 테스트")
    print("="*60)
    
    # 임의의 이력서 ID로 테스트 (실제로는 사용자 입력 또는 API 파라미터)
    test_resume_id = 1
    
    recommender.test_recommendation(test_resume_id, top_n=10)
    
    print("\n" + "="*60)
    print("추천 시스템 테스트 완료")
    print("="*60)
