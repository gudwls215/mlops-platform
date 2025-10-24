"""
텍스트 전처리 파이프라인
자기소개서와 채용공고 텍스트를 정제하고 토큰화합니다.
"""
import re
import sys
import os
from typing import List, Dict, Optional
import logging

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import psycopg2

# KoNLPy 동적 임포트 (없으면 설치 안내)
try:
    from konlpy.tag import Okt
    KONLPY_AVAILABLE = True
except ImportError:
    KONLPY_AVAILABLE = False
    print("Warning: konlpy가 설치되지 않았습니다. 형태소 분석 기능이 제한됩니다.")
    print("설치: pip install konlpy")

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 데이터베이스 연결 설정
from urllib.parse import quote_plus
password = quote_plus("xlxldpa!@#")
DATABASE_URL = f"postgresql://postgres:{password}@114.202.2.226:5433/postgres"


class TextPreprocessor:
    """텍스트 전처리 클래스"""
    
    def __init__(self):
        # 간단한 토큰화 사용 (KoNLPy 없이)
        self.stopwords = self._load_stopwords()
        
    def _load_stopwords(self) -> set:
        """한국어 불용어 목록 로드"""
        # 기본 불용어 리스트
        basic_stopwords = {
            '의', '가', '이', '은', '들', '는', '좀', '잘', '걍', '과', '도', '를',
            '으로', '자', '에', '와', '한', '하다', '을', '를', '에서', '으로', '로',
            '그', '저', '이', '그것', '저것', '것', '수', '등', '및', '또는',
            '때문', '위해', '통해', '대한', '관한', '같은', '각', '매우', '너무',
            '조금', '아주', '정말', '약간', '다소', '좀', '더', '가장', '매우'
        }
        
        # 추가 불용어 (자기소개서/채용공고 특화)
        domain_stopwords = {
            '입니다', '습니다', '합니다', '있습니다', '없습니다', '됩니다',
            '해당', '귀사', '부서', '담당', '업무', '관련', '분야', '가능',
            '우대', '사항', '근무', '조건', '자격', '요건'
        }
        
        return basic_stopwords.union(domain_stopwords)
    
    def clean_text(self, text: str) -> str:
        """텍스트 기본 정제"""
        if not text:
            return ""
        
        # HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', text)
        
        # URL 제거
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # 이메일 제거
        text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '', text)
        
        # 특수문자 정리 (일부 유지)
        text = re.sub(r'[^\w\s가-힣.,!?()~-]', ' ', text)
        
        # 연속된 공백 제거
        text = re.sub(r'\s+', ' ', text)
        
        # 양쪽 공백 제거
        text = text.strip()
        
        return text
    
    def tokenize(self, text: str, remove_stopwords: bool = True) -> List[str]:
        """텍스트 토큰화 (간단한 공백 기반 분리)"""
        if not text:
            return []
        
        # 공백 기반 분리
        tokens = text.split()
        
        # 2글자 이상만 유지
        tokens = [token for token in tokens if len(token) >= 2]
        
        # 불용어 제거
        if remove_stopwords:
            tokens = [token for token in tokens if token not in self.stopwords]
        
        return tokens
    
    def preprocess(self, text: str, remove_stopwords: bool = True) -> Dict[str, any]:
        """전체 전처리 파이프라인"""
        # 1. 텍스트 정제
        cleaned_text = self.clean_text(text)
        
        # 2. 토큰화
        tokens = self.tokenize(cleaned_text, remove_stopwords)
        
        # 3. 통계 정보
        stats = {
            'original_length': len(text),
            'cleaned_length': len(cleaned_text),
            'token_count': len(tokens),
            'unique_token_count': len(set(tokens))
        }
        
        return {
            'original_text': text,
            'cleaned_text': cleaned_text,
            'tokens': tokens,
            'token_text': ' '.join(tokens),
            'stats': stats
        }


def preprocess_cover_letters(batch_size: int = 100) -> None:
    """자기소개서 전처리 및 DB 업데이트"""
    logger.info("자기소개서 전처리 시작...")
    
    # DB 연결
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    preprocessor = TextPreprocessor()
    
    try:
        # 전처리할 자기소개서 조회
        query = text("""
            SELECT id, content
            FROM mlops.cover_letter_samples
            WHERE content IS NOT NULL
            ORDER BY id
        """)
        
        result = session.execute(query)
        cover_letters = result.fetchall()
        
        logger.info(f"전처리할 자기소개서: {len(cover_letters)}건")
        
        processed_count = 0
        
        for idx, (cl_id, content) in enumerate(cover_letters, 1):
            try:
                # 전처리 실행
                processed = preprocessor.preprocess(content)
                
                # DB 업데이트 (cleaned_text, tokens 컬럼 추가 필요)
                update_query = text("""
                    UPDATE mlops.cover_letter_samples
                    SET 
                        cleaned_content = :cleaned_text,
                        tokens = :tokens,
                        token_count = :token_count
                    WHERE id = :id
                """)
                
                session.execute(update_query, {
                    'id': cl_id,
                    'cleaned_text': processed['cleaned_text'],
                    'tokens': processed['token_text'],
                    'token_count': processed['stats']['token_count']
                })
                
                processed_count += 1
                
                if idx % 50 == 0:
                    session.commit()
                    logger.info(f"진행: {idx}/{len(cover_letters)} ({idx/len(cover_letters)*100:.1f}%)")
                    
            except Exception as e:
                logger.error(f"자기소개서 ID {cl_id} 전처리 실패: {e}")
                continue
        
        session.commit()
        logger.info(f"자기소개서 전처리 완료: {processed_count}건")
        
    except Exception as e:
        logger.error(f"전처리 중 오류 발생: {e}")
        session.rollback()
    finally:
        session.close()


def preprocess_job_postings(batch_size: int = 100) -> None:
    """채용공고 전처리 및 DB 업데이트"""
    logger.info("채용공고 전처리 시작...")
    
    # DB 연결
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    preprocessor = TextPreprocessor()
    
    try:
        # 전처리할 채용공고 조회
        query = text("""
            SELECT id, description
            FROM mlops.job_postings
            WHERE description IS NOT NULL
            ORDER BY id
        """)
        
        result = session.execute(query)
        job_postings = result.fetchall()
        
        logger.info(f"전처리할 채용공고: {len(job_postings)}건")
        
        processed_count = 0
        
        for idx, (jp_id, description) in enumerate(job_postings, 1):
            try:
                # 전처리 실행
                processed = preprocessor.preprocess(description)
                
                # DB 업데이트
                update_query = text("""
                    UPDATE mlops.job_postings
                    SET 
                        cleaned_description = :cleaned_text,
                        tokens = :tokens,
                        token_count = :token_count
                    WHERE id = :id
                """)
                
                session.execute(update_query, {
                    'id': jp_id,
                    'cleaned_text': processed['cleaned_text'],
                    'tokens': processed['token_text'],
                    'token_count': processed['stats']['token_count']
                })
                
                processed_count += 1
                
                if idx % 100 == 0:
                    session.commit()
                    logger.info(f"진행: {idx}/{len(job_postings)} ({idx/len(job_postings)*100:.1f}%)")
                    
            except Exception as e:
                logger.error(f"채용공고 ID {jp_id} 전처리 실패: {e}")
                continue
        
        session.commit()
        logger.info(f"채용공고 전처리 완료: {processed_count}건")
        
    except Exception as e:
        logger.error(f"전처리 중 오류 발생: {e}")
        session.rollback()
    finally:
        session.close()


def add_preprocessing_columns():
    """전처리 결과 저장용 컬럼 추가"""
    logger.info("전처리 컬럼 추가 시작...")
    
    conn = psycopg2.connect(
        host="114.202.2.226",
        port=5433,
        database="postgres",
        user="postgres",
        password="xlxldpa!@#"
    )
    
    try:
        with conn.cursor() as cur:
            # cover_letter_samples 테이블에 컬럼 추가
            cur.execute("""
                ALTER TABLE mlops.cover_letter_samples
                ADD COLUMN IF NOT EXISTS cleaned_content TEXT,
                ADD COLUMN IF NOT EXISTS tokens TEXT,
                ADD COLUMN IF NOT EXISTS token_count INTEGER;
            """)
            
            # job_postings 테이블에 컬럼 추가
            cur.execute("""
                ALTER TABLE mlops.job_postings
                ADD COLUMN IF NOT EXISTS cleaned_description TEXT,
                ADD COLUMN IF NOT EXISTS tokens TEXT,
                ADD COLUMN IF NOT EXISTS token_count INTEGER;
            """)
            
            conn.commit()
            logger.info("전처리 컬럼 추가 완료")
            
    except Exception as e:
        logger.error(f"컬럼 추가 실패: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    import time
    
    start_time = time.time()
    
    # 1. 컬럼 추가
    add_preprocessing_columns()
    
    # 2. 자기소개서 전처리
    preprocess_cover_letters()
    
    # 3. 채용공고 전처리
    preprocess_job_postings()
    
    elapsed_time = time.time() - start_time
    logger.info(f"전체 전처리 완료 (소요 시간: {elapsed_time:.2f}초)")
