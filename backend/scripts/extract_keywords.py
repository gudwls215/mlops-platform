"""
TF-IDF 키워드 추출
자기소개서와 채용공고에서 중요 키워드를 추출합니다.
"""
import sys
import os
import time
import logging
from typing import List, Dict, Tuple
from urllib.parse import quote_plus
from collections import Counter

import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sklearn.feature_extraction.text import TfidfVectorizer
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


class KeywordExtractor:
    """TF-IDF 기반 키워드 추출 클래스"""
    
    def __init__(self, max_features: int = 100, min_df: int = 2, max_df: float = 0.8):
        """
        Args:
            max_features: 추출할 최대 특성 수
            min_df: 최소 문서 빈도 (이 값 미만이면 제외)
            max_df: 최대 문서 빈도 비율 (이 값 초과면 제외, 너무 흔한 단어)
        """
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            min_df=min_df,
            max_df=max_df,
            lowercase=False,  # 한국어는 대소문자 구분 없음
            token_pattern=r'(?u)\b\w+\b'  # 단어 단위 토큰
        )
        logger.info(f"TF-IDF Vectorizer 초기화: max_features={max_features}, min_df={min_df}, max_df={max_df}")
    
    def fit_transform(self, documents: List[str]) -> Tuple[np.ndarray, List[str]]:
        """
        TF-IDF 행렬 생성
        
        Args:
            documents: 문서 리스트 (토큰화된 텍스트)
            
        Returns:
            tfidf_matrix: TF-IDF 행렬 (n_samples, n_features)
            feature_names: 특성 이름 리스트
        """
        logger.info(f"TF-IDF 행렬 생성 중... (문서 수: {len(documents)})")
        tfidf_matrix = self.vectorizer.fit_transform(documents)
        feature_names = self.vectorizer.get_feature_names_out()
        
        logger.info(f"TF-IDF 행렬 생성 완료. Shape: {tfidf_matrix.shape}")
        logger.info(f"추출된 특성 수: {len(feature_names)}")
        
        return tfidf_matrix, feature_names.tolist()
    
    def get_top_keywords(self, tfidf_matrix: np.ndarray, feature_names: List[str], 
                        top_n: int = 10) -> List[List[Tuple[str, float]]]:
        """
        각 문서의 상위 키워드 추출
        
        Args:
            tfidf_matrix: TF-IDF 행렬
            feature_names: 특성 이름 리스트
            top_n: 문서당 추출할 키워드 수
            
        Returns:
            각 문서의 [(키워드, 점수), ...] 리스트
        """
        keywords_list = []
        
        for i in range(tfidf_matrix.shape[0]):
            # 해당 문서의 TF-IDF 점수
            scores = tfidf_matrix[i].toarray()[0]
            
            # 상위 N개 키워드 추출
            top_indices = scores.argsort()[-top_n:][::-1]
            top_keywords = [(feature_names[idx], scores[idx]) for idx in top_indices if scores[idx] > 0]
            
            keywords_list.append(top_keywords)
        
        return keywords_list


def add_keyword_columns():
    """키워드 저장용 컬럼 추가"""
    logger.info("키워드 컬럼 추가 시작...")
    
    conn = psycopg2.connect(
        host="114.202.2.226",
        port=5433,
        database="postgres",
        user="postgres",
        password="xlxldpa!@#"
    )
    
    try:
        with conn.cursor() as cur:
            # cover_letter_samples 테이블에 키워드 컬럼 추가
            cur.execute("""
                ALTER TABLE mlops.cover_letter_samples
                ADD COLUMN IF NOT EXISTS keywords TEXT,
                ADD COLUMN IF NOT EXISTS keyword_scores TEXT;
            """)
            
            # job_postings 테이블에 키워드 컬럼 추가
            cur.execute("""
                ALTER TABLE mlops.job_postings
                ADD COLUMN IF NOT EXISTS keywords TEXT,
                ADD COLUMN IF NOT EXISTS keyword_scores TEXT;
            """)
            
            conn.commit()
            logger.info("키워드 컬럼 추가 완료")
            
    except Exception as e:
        logger.error(f"컬럼 추가 실패: {e}")
        conn.rollback()
    finally:
        conn.close()


def extract_cover_letter_keywords(top_n: int = 20) -> None:
    """자기소개서 키워드 추출 및 DB 업데이트"""
    logger.info("자기소개서 키워드 추출 시작...")
    
    # DB 연결
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 토큰화된 자기소개서 조회
        query = text("""
            SELECT id, tokens
            FROM mlops.cover_letter_samples
            WHERE tokens IS NOT NULL AND tokens != ''
            ORDER BY id
        """)
        
        result = session.execute(query)
        cover_letters = result.fetchall()
        
        logger.info(f"키워드 추출할 자기소개서: {len(cover_letters)}건")
        
        if len(cover_letters) == 0:
            logger.warning("토큰화된 자기소개서가 없습니다.")
            return
        
        # 문서 리스트 준비
        ids = [cl[0] for cl in cover_letters]
        documents = [cl[1] for cl in cover_letters]
        
        # TF-IDF 키워드 추출
        extractor = KeywordExtractor(max_features=200, min_df=2, max_df=0.5)
        tfidf_matrix, feature_names = extractor.fit_transform(documents)
        keywords_list = extractor.get_top_keywords(tfidf_matrix, feature_names, top_n=top_n)
        
        # 전체 코퍼스에서 가장 중요한 키워드 확인
        logger.info(f"전체 자기소개서 상위 키워드: {feature_names[:20]}")
        
        # DB 업데이트
        logger.info("DB 업데이트 중...")
        for idx, (cl_id, keywords) in enumerate(zip(ids, keywords_list), 1):
            try:
                # 키워드와 점수 분리
                if keywords:
                    keyword_str = ','.join([kw for kw, score in keywords])
                    score_str = ','.join([f"{score:.4f}" for kw, score in keywords])
                else:
                    keyword_str = ''
                    score_str = ''
                
                update_query = text("""
                    UPDATE mlops.cover_letter_samples
                    SET 
                        keywords = :keywords,
                        keyword_scores = :scores
                    WHERE id = :id
                """)
                
                session.execute(update_query, {
                    'id': cl_id,
                    'keywords': keyword_str,
                    'scores': score_str
                })
                
                if idx % 50 == 0:
                    session.commit()
                    logger.info(f"진행: {idx}/{len(ids)} ({idx/len(ids)*100:.1f}%)")
                    
            except Exception as e:
                logger.error(f"자기소개서 ID {cl_id} 키워드 저장 실패: {e}")
                continue
        
        session.commit()
        logger.info(f"자기소개서 키워드 추출 완료: {len(ids)}건")
        
    except Exception as e:
        logger.error(f"키워드 추출 중 오류 발생: {e}")
        session.rollback()
    finally:
        session.close()


def extract_job_posting_keywords(top_n: int = 15) -> None:
    """채용공고 키워드 추출 및 DB 업데이트"""
    logger.info("채용공고 키워드 추출 시작...")
    
    # DB 연결
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 토큰화된 채용공고 조회
        query = text("""
            SELECT id, tokens
            FROM mlops.job_postings
            WHERE tokens IS NOT NULL AND tokens != ''
            ORDER BY id
        """)
        
        result = session.execute(query)
        job_postings = result.fetchall()
        
        logger.info(f"키워드 추출할 채용공고: {len(job_postings)}건")
        
        if len(job_postings) == 0:
            logger.warning("토큰화된 채용공고가 없습니다.")
            return
        
        # 문서 리스트 준비
        ids = [jp[0] for jp in job_postings]
        documents = [jp[1] for jp in job_postings]
        
        # TF-IDF 키워드 추출
        extractor = KeywordExtractor(max_features=150, min_df=5, max_df=0.6)
        tfidf_matrix, feature_names = extractor.fit_transform(documents)
        keywords_list = extractor.get_top_keywords(tfidf_matrix, feature_names, top_n=top_n)
        
        # 전체 코퍼스에서 가장 중요한 키워드 확인
        logger.info(f"전체 채용공고 상위 키워드: {feature_names[:20]}")
        
        # DB 업데이트
        logger.info("DB 업데이트 중...")
        for idx, (jp_id, keywords) in enumerate(zip(ids, keywords_list), 1):
            try:
                # 키워드와 점수 분리
                if keywords:
                    keyword_str = ','.join([kw for kw, score in keywords])
                    score_str = ','.join([f"{score:.4f}" for kw, score in keywords])
                else:
                    keyword_str = ''
                    score_str = ''
                
                update_query = text("""
                    UPDATE mlops.job_postings
                    SET 
                        keywords = :keywords,
                        keyword_scores = :scores
                    WHERE id = :id
                """)
                
                session.execute(update_query, {
                    'id': jp_id,
                    'keywords': keyword_str,
                    'scores': score_str
                })
                
                if idx % 100 == 0:
                    session.commit()
                    logger.info(f"진행: {idx}/{len(ids)} ({idx/len(ids)*100:.1f}%)")
                    
            except Exception as e:
                logger.error(f"채용공고 ID {jp_id} 키워드 저장 실패: {e}")
                continue
        
        session.commit()
        logger.info(f"채용공고 키워드 추출 완료: {len(ids)}건")
        
    except Exception as e:
        logger.error(f"키워드 추출 중 오류 발생: {e}")
        session.rollback()
    finally:
        session.close()


def analyze_keyword_statistics():
    """키워드 통계 분석"""
    logger.info("키워드 통계 분석 시작...")
    
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # 자기소개서 키워드 통계
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(keywords) as with_keywords,
                AVG(array_length(string_to_array(keywords, ','), 1)) as avg_keywords
            FROM mlops.cover_letter_samples
            WHERE keywords IS NOT NULL AND keywords != ''
        """)).fetchone()
        
        if result and result[1] > 0:
            logger.info(f"자기소개서: 총 {result[0]}건, 키워드 추출 {result[1]}건, 평균 키워드 수: {result[2]:.1f}")
        
        # 채용공고 키워드 통계
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(keywords) as with_keywords,
                AVG(array_length(string_to_array(keywords, ','), 1)) as avg_keywords
            FROM mlops.job_postings
            WHERE keywords IS NOT NULL AND keywords != ''
        """)).fetchone()
        
        if result and result[1] > 0:
            logger.info(f"채용공고: 총 {result[0]}건, 키워드 추출 {result[1]}건, 평균 키워드 수: {result[2]:.1f}")
        
        # 자기소개서 샘플 키워드
        result = conn.execute(text("""
            SELECT title, keywords
            FROM mlops.cover_letter_samples
            WHERE keywords IS NOT NULL AND keywords != ''
            LIMIT 1
        """)).fetchone()
        
        if result:
            logger.info(f"\n샘플 자기소개서 키워드:")
            logger.info(f"  제목: {result[0]}")
            logger.info(f"  키워드: {result[1][:200]}...")


if __name__ == "__main__":
    start_time = time.time()
    
    # 1. 컬럼 추가
    add_keyword_columns()
    
    # 2. 자기소개서 키워드 추출
    extract_cover_letter_keywords(top_n=20)
    
    # 3. 채용공고 키워드 추출
    extract_job_posting_keywords(top_n=15)
    
    # 4. 통계 분석
    analyze_keyword_statistics()
    
    elapsed_time = time.time() - start_time
    logger.info(f"전체 키워드 추출 완료 (소요 시간: {elapsed_time:.2f}초)")
