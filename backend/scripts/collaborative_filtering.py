"""
협업 필터링 추천 시스템
Item-based Collaborative Filtering 구현
"""

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix
from typing import List, Dict, Tuple
import os
from dotenv import load_dotenv
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

# 데이터베이스 연결 설정
DB_HOST = os.getenv('DATABASE_HOST', '114.202.2.226')
DB_PORT = os.getenv('DATABASE_PORT', '5433')
DB_NAME = os.getenv('DATABASE_NAME', 'postgres')
DB_USER = os.getenv('DATABASE_USER', 'postgres')
DB_PASSWORD = os.getenv('DATABASE_PASSWORD', '')
DB_SCHEMA = 'mlops'

import urllib.parse
encoded_password = urllib.parse.quote_plus(DB_PASSWORD)
DATABASE_URL = f"postgresql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


class CollaborativeFilteringRecommender:
    """
    Item-based Collaborative Filtering 추천 시스템
    
    사용자-채용공고 상호작용 데이터를 기반으로
    비슷한 패턴을 가진 채용공고를 추천합니다.
    """
    
    def __init__(self):
        self.engine = create_engine(DATABASE_URL)
        self.user_item_matrix = None
        self.item_similarity_matrix = None
        self.item_ids = None
        self.user_ids = None
        
    def create_interaction_table(self):
        """사용자 상호작용 테이블 생성"""
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {DB_SCHEMA}.user_interactions (
            id SERIAL PRIMARY KEY,
            resume_id INTEGER NOT NULL,
            job_id INTEGER NOT NULL,
            interaction_type VARCHAR(50) NOT NULL,  -- 'view', 'apply', 'like', 'save', 'click'
            rating FLOAT DEFAULT 0,  -- 암묵적 평점 (view=1, click=2, save=3, like=4, apply=5)
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (resume_id) REFERENCES {DB_SCHEMA}.cover_letter_samples(id) ON DELETE CASCADE,
            FOREIGN KEY (job_id) REFERENCES {DB_SCHEMA}.job_postings(id) ON DELETE CASCADE,
            UNIQUE(resume_id, job_id, interaction_type)
        );
        
        CREATE INDEX IF NOT EXISTS idx_user_interactions_resume 
        ON {DB_SCHEMA}.user_interactions(resume_id);
        
        CREATE INDEX IF NOT EXISTS idx_user_interactions_job 
        ON {DB_SCHEMA}.user_interactions(job_id);
        
        CREATE INDEX IF NOT EXISTS idx_user_interactions_type 
        ON {DB_SCHEMA}.user_interactions(interaction_type);
        """
        
        with self.engine.connect() as conn:
            conn.execute(text(create_table_sql))
            conn.commit()
            logger.info("user_interactions 테이블 생성 완료")
    
    def generate_sample_interactions(self, num_interactions: int = 500):
        """
        테스트용 샘플 상호작용 데이터 생성
        실제 사용자 행동 패턴을 시뮬레이션
        """
        logger.info(f"샘플 상호작용 데이터 {num_interactions}건 생성 중...")
        
        # 이력서와 채용공고 ID 조회
        with self.engine.connect() as conn:
            resumes = pd.read_sql(
                text(f"SELECT id FROM {DB_SCHEMA}.cover_letter_samples LIMIT 100"),
                conn
            )
            jobs = pd.read_sql(
                text(f"SELECT id FROM {DB_SCHEMA}.job_postings LIMIT 100"),
                conn
            )
        
        if len(resumes) == 0 or len(jobs) == 0:
            logger.error("이력서 또는 채용공고 데이터가 없습니다.")
            return
        
        resume_ids = resumes['id'].tolist()
        job_ids = jobs['id'].tolist()
        
        # 상호작용 타입과 평점 매핑
        interaction_weights = {
            'view': 1.0,
            'click': 2.0,
            'save': 3.0,
            'like': 4.0,
            'apply': 5.0
        }
        
        interactions = []
        np.random.seed(42)
        
        for _ in range(num_interactions):
            resume_id = np.random.choice(resume_ids)
            job_id = np.random.choice(job_ids)
            
            # 상호작용 타입 확률적 선택 (view > click > save > like > apply)
            interaction_type = np.random.choice(
                list(interaction_weights.keys()),
                p=[0.4, 0.25, 0.15, 0.1, 0.1]
            )
            rating = interaction_weights[interaction_type]
            
            interactions.append({
                'resume_id': resume_id,
                'job_id': job_id,
                'interaction_type': interaction_type,
                'rating': rating
            })
        
        # 데이터프레임 생성 및 중복 제거
        df_interactions = pd.DataFrame(interactions)
        df_interactions = df_interactions.drop_duplicates(
            subset=['resume_id', 'job_id', 'interaction_type']
        )
        
        # 데이터베이스에 저장
        insert_sql = f"""
        INSERT INTO {DB_SCHEMA}.user_interactions 
        (resume_id, job_id, interaction_type, rating)
        VALUES (:resume_id, :job_id, :interaction_type, :rating)
        ON CONFLICT (resume_id, job_id, interaction_type) DO NOTHING
        """
        
        with self.engine.connect() as conn:
            for _, row in df_interactions.iterrows():
                conn.execute(text(insert_sql), row.to_dict())
            conn.commit()
        
        logger.info(f"샘플 상호작용 데이터 {len(df_interactions)}건 생성 완료")
    
    def load_interaction_data(self) -> pd.DataFrame:
        """사용자 상호작용 데이터 로드"""
        query = f"""
        SELECT 
            resume_id,
            job_id,
            interaction_type,
            rating
        FROM {DB_SCHEMA}.user_interactions
        ORDER BY created_at DESC
        """
        
        with self.engine.connect() as conn:
            df = pd.read_sql(text(query), conn)
        
        logger.info(f"상호작용 데이터 {len(df)}건 로드 완료")
        return df
    
    def build_user_item_matrix(self, interactions_df: pd.DataFrame) -> csr_matrix:
        """
        사용자-아이템 매트릭스 구축
        
        Args:
            interactions_df: 상호작용 데이터프레임
            
        Returns:
            sparse matrix (users x items)
        """
        # 사용자(resume_id)와 아이템(job_id) 인덱스 매핑
        self.user_ids = sorted(interactions_df['resume_id'].unique())
        self.item_ids = sorted(interactions_df['job_id'].unique())
        
        user_id_map = {uid: idx for idx, uid in enumerate(self.user_ids)}
        item_id_map = {iid: idx for idx, iid in enumerate(self.item_ids)}
        
        # 상호작용별 가중치 합산 (같은 user-item 쌍에 여러 상호작용이 있을 수 있음)
        interactions_grouped = interactions_df.groupby(['resume_id', 'job_id'])['rating'].sum().reset_index()
        
        # 행(user), 열(item), 값(rating) 배열 생성
        rows = [user_id_map[uid] for uid in interactions_grouped['resume_id']]
        cols = [item_id_map[iid] for iid in interactions_grouped['job_id']]
        data = interactions_grouped['rating'].values
        
        # Sparse matrix 생성
        n_users = len(self.user_ids)
        n_items = len(self.item_ids)
        
        self.user_item_matrix = csr_matrix(
            (data, (rows, cols)),
            shape=(n_users, n_items)
        )
        
        logger.info(f"사용자-아이템 매트릭스 구축 완료: {n_users} users x {n_items} items")
        logger.info(f"Sparsity: {1 - (len(data) / (n_users * n_items)):.4f}")
        
        return self.user_item_matrix
    
    def compute_item_similarity(self) -> np.ndarray:
        """
        아이템 간 유사도 계산 (코사인 유사도)
        
        Returns:
            item similarity matrix (items x items)
        """
        if self.user_item_matrix is None:
            raise ValueError("user_item_matrix가 초기화되지 않았습니다.")
        
        # 아이템 벡터 간 코사인 유사도 계산
        # user_item_matrix를 전치하여 (items x users) 형태로 변환
        item_user_matrix = self.user_item_matrix.T.toarray()
        
        self.item_similarity_matrix = cosine_similarity(item_user_matrix)
        
        # 자기 자신과의 유사도는 0으로 설정
        np.fill_diagonal(self.item_similarity_matrix, 0)
        
        logger.info(f"아이템 유사도 매트릭스 계산 완료: {self.item_similarity_matrix.shape}")
        
        return self.item_similarity_matrix
    
    def recommend_for_user(
        self, 
        resume_id: int, 
        top_n: int = 10,
        exclude_interacted: bool = True
    ) -> List[Tuple[int, float]]:
        """
        특정 사용자에게 채용공고 추천
        
        Args:
            resume_id: 이력서 ID (사용자 ID)
            top_n: 추천할 아이템 수
            exclude_interacted: 이미 상호작용한 아이템 제외 여부
            
        Returns:
            [(job_id, predicted_rating), ...]
        """
        if self.user_item_matrix is None or self.item_similarity_matrix is None:
            raise ValueError("모델이 초기화되지 않았습니다. build_model()을 먼저 실행하세요.")
        
        # 사용자 인덱스 찾기
        try:
            user_idx = self.user_ids.index(resume_id)
        except ValueError:
            logger.warning(f"사용자 {resume_id}의 상호작용 데이터가 없습니다.")
            return []
        
        # 사용자의 상호작용 벡터
        user_ratings = self.user_item_matrix[user_idx].toarray().flatten()
        
        # 예측 평점 계산
        # predicted_rating[i] = sum(similarity[i, j] * user_rating[j]) / sum(similarity[i, j])
        predicted_ratings = np.zeros(len(self.item_ids))
        
        for item_idx in range(len(self.item_ids)):
            # 이 아이템과 유사한 아이템들
            similarities = self.item_similarity_matrix[item_idx]
            
            # 사용자가 평가한 아이템들과의 유사도 가중 평균
            numerator = np.sum(similarities * user_ratings)
            denominator = np.sum(np.abs(similarities[user_ratings > 0]))
            
            if denominator > 0:
                predicted_ratings[item_idx] = numerator / denominator
        
        # 이미 상호작용한 아이템 제외
        if exclude_interacted:
            interacted_items = user_ratings > 0
            predicted_ratings[interacted_items] = -np.inf
        
        # Top-N 추천
        top_indices = np.argsort(predicted_ratings)[::-1][:top_n]
        
        recommendations = [
            (self.item_ids[idx], predicted_ratings[idx])
            for idx in top_indices
            if predicted_ratings[idx] > 0
        ]
        
        logger.info(f"사용자 {resume_id}에게 {len(recommendations)}개 추천 생성")
        
        return recommendations
    
    def build_model(self):
        """전체 모델 빌드 프로세스"""
        logger.info("협업 필터링 모델 빌드 시작...")
        
        # 1. 상호작용 데이터 로드
        interactions_df = self.load_interaction_data()
        
        if len(interactions_df) == 0:
            logger.error("상호작용 데이터가 없습니다.")
            return False
        
        # 2. 사용자-아이템 매트릭스 구축
        self.build_user_item_matrix(interactions_df)
        
        # 3. 아이템 유사도 계산
        self.compute_item_similarity()
        
        logger.info("협업 필터링 모델 빌드 완료")
        return True
    
    def get_similar_items(self, job_id: int, top_n: int = 10) -> List[Tuple[int, float]]:
        """
        특정 채용공고와 유사한 채용공고 찾기
        
        Args:
            job_id: 채용공고 ID
            top_n: 반환할 유사 아이템 수
            
        Returns:
            [(similar_job_id, similarity_score), ...]
        """
        if self.item_similarity_matrix is None:
            raise ValueError("모델이 초기화되지 않았습니다.")
        
        try:
            item_idx = self.item_ids.index(job_id)
        except ValueError:
            logger.warning(f"채용공고 {job_id}의 데이터가 없습니다.")
            return []
        
        # 유사도 가져오기
        similarities = self.item_similarity_matrix[item_idx]
        
        # Top-N 유사 아이템
        top_indices = np.argsort(similarities)[::-1][:top_n]
        
        similar_items = [
            (self.item_ids[idx], similarities[idx])
            for idx in top_indices
            if similarities[idx] > 0
        ]
        
        return similar_items


def main():
    """테스트 실행"""
    recommender = CollaborativeFilteringRecommender()
    
    # 1. 테이블 생성
    logger.info("=== 1. 테이블 생성 ===")
    recommender.create_interaction_table()
    
    # 2. 샘플 데이터 생성
    logger.info("\n=== 2. 샘플 데이터 생성 ===")
    recommender.generate_sample_interactions(num_interactions=500)
    
    # 3. 모델 빌드
    logger.info("\n=== 3. 모델 빌드 ===")
    success = recommender.build_model()
    
    if not success:
        logger.error("모델 빌드 실패")
        return
    
    # 4. 추천 테스트
    logger.info("\n=== 4. 추천 테스트 ===")
    if len(recommender.user_ids) > 0:
        test_user = recommender.user_ids[0]
        recommendations = recommender.recommend_for_user(test_user, top_n=10)
        
        logger.info(f"\n사용자 {test_user}에게 추천된 채용공고 (Top 10):")
        for job_id, score in recommendations:
            logger.info(f"  채용공고 ID {job_id}: 예측 평점 {score:.3f}")
    
    # 5. 유사 아이템 테스트
    logger.info("\n=== 5. 유사 아이템 테스트 ===")
    if len(recommender.item_ids) > 0:
        test_item = recommender.item_ids[0]
        similar_items = recommender.get_similar_items(test_item, top_n=5)
        
        logger.info(f"\n채용공고 {test_item}와 유사한 채용공고 (Top 5):")
        for job_id, similarity in similar_items:
            logger.info(f"  채용공고 ID {job_id}: 유사도 {similarity:.3f}")


if __name__ == "__main__":
    main()
