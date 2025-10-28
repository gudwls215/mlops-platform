"""
기존 이력서의 임베딩 생성 스크립트
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import urllib.parse
from app.services.embedding_service import generate_embedding
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

# 데이터베이스 연결
DB_HOST = os.getenv('POSTGRES_HOST', '114.202.2.226')
DB_PORT = os.getenv('POSTGRES_PORT', '5433')
DB_NAME = os.getenv('POSTGRES_DB', 'postgres')
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')
DB_SCHEMA = 'mlops'

encoded_password = urllib.parse.quote_plus(DB_PASSWORD)
DATABASE_URL = f"postgresql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def generate_embeddings_for_existing_resumes():
    """기존 이력서들의 임베딩 생성"""
    engine = create_engine(DATABASE_URL)
    
    # 임베딩이 없는 이력서 조회
    query = f"""
    SELECT id, content
    FROM {DB_SCHEMA}.resumes
    WHERE is_active = true 
      AND content IS NOT NULL 
      AND content != ''
      AND (embedding_array IS NULL OR embedding_array = '')
    ORDER BY id
    """
    
    with engine.connect() as conn:
        result = conn.execute(text(query))
        resumes = result.fetchall()
        
        logger.info(f"임베딩 생성 대상 이력서: {len(resumes)}개")
        
        success_count = 0
        fail_count = 0
        
        for idx, (resume_id, content) in enumerate(resumes, 1):
            try:
                logger.info(f"[{idx}/{len(resumes)}] 이력서 ID {resume_id} 임베딩 생성 중...")
                
                # 임베딩 생성
                embedding_str = generate_embedding(content)
                
                if embedding_str:
                    # 데이터베이스 업데이트
                    update_query = text(f"""
                    UPDATE {DB_SCHEMA}.resumes
                    SET embedding_array = :embedding
                    WHERE id = :resume_id
                    """)
                    
                    conn.execute(update_query, {
                        "embedding": embedding_str,
                        "resume_id": resume_id
                    })
                    conn.commit()
                    
                    success_count += 1
                    logger.info(f"✓ 이력서 ID {resume_id} 임베딩 생성 완료")
                else:
                    fail_count += 1
                    logger.warning(f"✗ 이력서 ID {resume_id} 임베딩 생성 실패")
                    
            except Exception as e:
                fail_count += 1
                logger.error(f"✗ 이력서 ID {resume_id} 처리 오류: {e}")
                conn.rollback()
        
        logger.info(f"\n=== 임베딩 생성 완료 ===")
        logger.info(f"성공: {success_count}개")
        logger.info(f"실패: {fail_count}개")
        logger.info(f"총: {len(resumes)}개")


if __name__ == "__main__":
    try:
        generate_embeddings_for_existing_resumes()
    except Exception as e:
        logger.error(f"스크립트 실행 오류: {e}")
        sys.exit(1)
