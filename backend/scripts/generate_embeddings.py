"""
Sentence-BERT 임베딩 생성
자기소개서와 채용공고 텍스트를 벡터로 변환합니다.
"""
import sys
import os
import time
import logging
from typing import List, Optional
from urllib.parse import quote_plus

import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sentence_transformers import SentenceTransformer
import psycopg2

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 데이터베이스 연결 설정
password = quote_plus("xlxldpa!@#")
DATABASE_URL = f"postgresql://postgres:{password}@114.202.2.226:5433/postgres"


class EmbeddingGenerator:
    """임베딩 생성 클래스"""
    
    def __init__(self, model_name: str = "snunlp/KR-SBERT-V40K-klueNLI-augSTS"):
        """
        Args:
            model_name: 사용할 Sentence-BERT 모델명
                - snunlp/KR-SBERT-V40K-klueNLI-augSTS (추천, 한국어 최적화)
                - jhgan/ko-sroberta-multitask (대안)
        """
        logger.info(f"Sentence-BERT 모델 로딩 시작: {model_name}")
        self.model = SentenceTransformer(model_name)
        logger.info(f"모델 로딩 완료. 임베딩 차원: {self.model.get_sentence_embedding_dimension()}")
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
    
    def encode_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        배치 단위로 텍스트를 임베딩으로 변환
        
        Args:
            texts: 임베딩할 텍스트 리스트
            batch_size: 배치 크기
            
        Returns:
            임베딩 배열 (n_samples, embedding_dim)
        """
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        return embeddings


def add_embedding_columns():
    """임베딩 저장용 컬럼 추가"""
    logger.info("임베딩 컬럼 추가 시작...")
    
    conn = psycopg2.connect(
        host="114.202.2.226",
        port=5433,
        database="postgres",
        user="postgres",
        password="xlxldpa!@#"
    )
    
    try:
        with conn.cursor() as cur:
            # TEXT 컬럼으로 추가
            cur.execute("""
                ALTER TABLE mlops.cover_letter_samples
                ADD COLUMN IF NOT EXISTS embedding_array TEXT;
            """)
            
            cur.execute("""
                ALTER TABLE mlops.job_postings
                ADD COLUMN IF NOT EXISTS embedding_array TEXT;
            """)
            
            conn.commit()
            logger.info("임베딩 컬럼 추가 완료 (TEXT 타입)")
            
    except Exception as e:
        logger.error(f"컬럼 추가 실패: {e}")
        conn.rollback()
    finally:
        conn.close()


def generate_cover_letter_embeddings(batch_size: int = 32) -> None:
    """자기소개서 임베딩 생성 및 DB 업데이트"""
    logger.info("자기소개서 임베딩 생성 시작...")
    
    # DB 연결
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # 임베딩 생성기 초기화
    embedding_gen = EmbeddingGenerator()
    
    try:
        # 임베딩 생성할 자기소개서 조회
        query = text("""
            SELECT id, cleaned_content, tokens
            FROM mlops.cover_letter_samples
            WHERE cleaned_content IS NOT NULL
            ORDER BY id
        """)
        
        result = session.execute(query)
        cover_letters = result.fetchall()
        
        logger.info(f"임베딩 생성할 자기소개서: {len(cover_letters)}건")
        
        # 배치 처리
        ids = [cl[0] for cl in cover_letters]
        texts = [cl[1] or cl[2] for cl in cover_letters]  # cleaned_content 우선, 없으면 tokens
        
        # 임베딩 생성
        logger.info("임베딩 생성 중...")
        embeddings = embedding_gen.encode_batch(texts, batch_size=batch_size)
        
        logger.info(f"임베딩 생성 완료. Shape: {embeddings.shape}")
        
        # DB 업데이트
        logger.info("DB 업데이트 중...")
        for idx, (cl_id, embedding) in enumerate(zip(ids, embeddings), 1):
            try:
                # 임베딩을 문자열로 변환 (pgvector가 없으면 TEXT로 저장)
                embedding_str = ','.join(map(str, embedding.tolist()))
                
                update_query = text("""
                    UPDATE mlops.cover_letter_samples
                    SET embedding_array = :embedding
                    WHERE id = :id
                """)
                
                session.execute(update_query, {
                    'id': cl_id,
                    'embedding': embedding_str
                })
                
                if idx % 50 == 0:
                    session.commit()
                    logger.info(f"진행: {idx}/{len(ids)} ({idx/len(ids)*100:.1f}%)")
                    
            except Exception as e:
                logger.error(f"자기소개서 ID {cl_id} 임베딩 저장 실패: {e}")
                continue
        
        session.commit()
        logger.info(f"자기소개서 임베딩 생성 완료: {len(ids)}건")
        
    except Exception as e:
        logger.error(f"임베딩 생성 중 오류 발생: {e}")
        session.rollback()
    finally:
        session.close()


def generate_job_posting_embeddings(batch_size: int = 64) -> None:
    """채용공고 임베딩 생성 및 DB 업데이트"""
    logger.info("채용공고 임베딩 생성 시작...")
    
    # DB 연결
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # 임베딩 생성기 초기화
    embedding_gen = EmbeddingGenerator()
    
    try:
        # 임베딩 생성할 채용공고 조회
        query = text("""
            SELECT id, cleaned_description, tokens
            FROM mlops.job_postings
            WHERE cleaned_description IS NOT NULL
            ORDER BY id
        """)
        
        result = session.execute(query)
        job_postings = result.fetchall()
        
        logger.info(f"임베딩 생성할 채용공고: {len(job_postings)}건")
        
        # 배치 처리
        ids = [jp[0] for jp in job_postings]
        texts = [jp[1] or jp[2] for jp in job_postings]  # cleaned_description 우선, 없으면 tokens
        
        # 임베딩 생성
        logger.info("임베딩 생성 중...")
        embeddings = embedding_gen.encode_batch(texts, batch_size=batch_size)
        
        logger.info(f"임베딩 생성 완료. Shape: {embeddings.shape}")
        
        # DB 업데이트
        logger.info("DB 업데이트 중...")
        for idx, (jp_id, embedding) in enumerate(zip(ids, embeddings), 1):
            try:
                # 임베딩을 문자열로 변환
                embedding_str = ','.join(map(str, embedding.tolist()))
                
                update_query = text("""
                    UPDATE mlops.job_postings
                    SET embedding_array = :embedding
                    WHERE id = :id
                """)
                
                session.execute(update_query, {
                    'id': jp_id,
                    'embedding': embedding_str
                })
                
                if idx % 100 == 0:
                    session.commit()
                    logger.info(f"진행: {idx}/{len(ids)} ({idx/len(ids)*100:.1f}%)")
                    
            except Exception as e:
                logger.error(f"채용공고 ID {jp_id} 임베딩 저장 실패: {e}")
                continue
        
        session.commit()
        logger.info(f"채용공고 임베딩 생성 완료: {len(ids)}건")
        
    except Exception as e:
        logger.error(f"임베딩 생성 중 오류 발생: {e}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    start_time = time.time()
    
    # 1. 컬럼 추가
    add_embedding_columns()
    
    # 2. 자기소개서 임베딩 생성
    generate_cover_letter_embeddings(batch_size=32)
    
    # 3. 채용공고 임베딩 생성
    generate_job_posting_embeddings(batch_size=64)
    
    elapsed_time = time.time() - start_time
    logger.info(f"전체 임베딩 생성 완료 (소요 시간: {elapsed_time:.2f}초)")
