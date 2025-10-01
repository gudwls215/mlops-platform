"""
Database management utilities
데이터베이스 관리 및 유틸리티 함수들
"""

import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.core.config import settings
from app.models import Base

logger = logging.getLogger(__name__)

class DatabaseManager:
    """데이터베이스 관리 클래스"""
    
    def __init__(self):
        # 비동기 엔진 생성
        self.async_engine = create_async_engine(
            settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
            echo=settings.debug,
            future=True
        )
        
        # 비동기 세션 팩토리
        self.async_session = sessionmaker(
            self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def create_database_schema(self):
        """데이터베이스 스키마 생성"""
        try:
            async with self.async_engine.begin() as conn:
                # mlops 스키마 생성
                await conn.execute(text("CREATE SCHEMA IF NOT EXISTS mlops"))
                logger.info("✅ mlops 스키마가 생성되었습니다.")
                
                # 모든 테이블 생성
                await conn.run_sync(Base.metadata.create_all)
                logger.info("✅ 모든 테이블이 생성되었습니다.")
                
        except Exception as e:
            logger.error(f"❌ 스키마 생성 실패: {str(e)}")
            raise
    
    async def drop_database_schema(self):
        """데이터베이스 스키마 삭제 (주의!)"""
        try:
            async with self.async_engine.begin() as conn:
                # 모든 테이블 삭제
                await conn.run_sync(Base.metadata.drop_all)
                logger.info("🗑️ 모든 테이블이 삭제되었습니다.")
                
                # 스키마 삭제
                await conn.execute(text("DROP SCHEMA IF EXISTS mlops CASCADE"))
                logger.info("🗑️ mlops 스키마가 삭제되었습니다.")
                
        except Exception as e:
            logger.error(f"❌ 스키마 삭제 실패: {str(e)}")
            raise
    
    async def check_database_connection(self):
        """데이터베이스 연결 확인"""
        try:
            async with self.async_engine.begin() as conn:
                result = await conn.execute(text("SELECT version()"))
                version = result.fetchone()[0]
                logger.info(f"✅ 데이터베이스 연결 성공: {version}")
                return True
        except Exception as e:
            logger.error(f"❌ 데이터베이스 연결 실패: {str(e)}")
            return False
    
    async def get_table_info(self):
        """테이블 정보 조회"""
        try:
            async with self.async_engine.begin() as conn:
                # 스키마 존재 확인
                schema_result = await conn.execute(text("""
                    SELECT schema_name 
                    FROM information_schema.schemata 
                    WHERE schema_name = 'mlops'
                """))
                schema_exists = schema_result.fetchone()
                
                if not schema_exists:
                    logger.warning("⚠️ mlops 스키마가 존재하지 않습니다.")
                    return {"schema_exists": False, "tables": []}
                
                # 테이블 목록 조회
                tables_result = await conn.execute(text("""
                    SELECT table_name, 
                           (SELECT COUNT(*) FROM information_schema.columns 
                            WHERE table_schema = 'mlops' AND table_name = t.table_name) as column_count
                    FROM information_schema.tables t
                    WHERE table_schema = 'mlops'
                    ORDER BY table_name
                """))
                tables = tables_result.fetchall()
                
                table_info = []
                for table_name, column_count in tables:
                    # 각 테이블의 레코드 수 조회
                    try:
                        count_result = await conn.execute(text(f"SELECT COUNT(*) FROM mlops.{table_name}"))
                        record_count = count_result.fetchone()[0]
                    except:
                        record_count = 0
                    
                    table_info.append({
                        "name": table_name,
                        "columns": column_count,
                        "records": record_count
                    })
                
                return {"schema_exists": True, "tables": table_info}
                
        except Exception as e:
            logger.error(f"❌ 테이블 정보 조회 실패: {str(e)}")
            return {"schema_exists": False, "tables": [], "error": str(e)}
    
    async def insert_sample_data(self):
        """샘플 데이터 삽입"""
        try:
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            
            async with self.async_session() as session:
                # 사용자 데이터 확인
                existing_users = await session.execute(text("SELECT COUNT(*) FROM mlops.users"))
                user_count = existing_users.fetchone()[0]
                
                if user_count == 0:
                    # 샘플 사용자 추가
                    sample_users_sql = text("""
                        INSERT INTO mlops.users (email, hashed_password, full_name, age, phone, address) VALUES
                        (:email1, :password1, :name1, :age1, :phone1, :address1),
                        (:email2, :password2, :name2, :age2, :phone2, :address2)
                    """)
                    
                    await session.execute(sample_users_sql, {
                        "email1": "test@example.com",
                        "password1": pwd_context.hash("testpassword"),
                        "name1": "김테스트",
                        "age1": 55,
                        "phone1": "010-1234-5678",
                        "address1": "서울시 강남구",
                        "email2": "senior@example.com",
                        "password2": pwd_context.hash("seniorpassword"),
                        "name2": "박시니어",
                        "age2": 52,
                        "phone2": "010-9876-5432",
                        "address2": "서울시 서초구"
                    })
                    
                    logger.info("✅ 샘플 사용자 데이터가 추가되었습니다.")
                
                # 채용 공고 데이터 확인
                existing_jobs = await session.execute(text("SELECT COUNT(*) FROM mlops.job_postings"))
                job_count = existing_jobs.fetchone()[0]
                
                if job_count == 0:
                    # 샘플 채용 공고 추가
                    sample_jobs_sql = text("""
                        INSERT INTO mlops.job_postings (title, company, description, requirements, salary_min, salary_max, location, employment_type, experience_level, skills_required) VALUES
                        (:title1, :company1, :desc1, :req1, :min1, :max1, :loc1, :type1, :level1, :skills1),
                        (:title2, :company2, :desc2, :req2, :min2, :max2, :loc2, :type2, :level2, :skills2),
                        (:title3, :company3, :desc3, :req3, :min3, :max3, :loc3, :type3, :level3, :skills3)
                    """)
                    
                    await session.execute(sample_jobs_sql, {
                        "title1": "시니어 백엔드 개발자", "company1": "ABC 기술", 
                        "desc1": "경험 많은 백엔드 개발자를 모집합니다", "req1": "Python, Java, 5년 이상 경험",
                        "min1": 4000, "max1": 6000, "loc1": "서울", "type1": "정규직", "level1": "시니어", "skills1": "Python,Java,Spring,Django",
                        
                        "title2": "데이터 분석가", "company2": "XYZ 데이터",
                        "desc2": "데이터 분석 및 인사이트 도출", "req2": "Python, SQL, 통계 지식",
                        "min2": 3500, "max2": 5000, "loc2": "서울", "type2": "정규직", "level2": "중급", "skills2": "Python,SQL,Pandas,NumPy",
                        
                        "title3": "프로젝트 매니저", "company3": "DEF 컨설팅",
                        "desc3": "IT 프로젝트 관리 전문가", "req3": "PMP 자격증, 관리 경험 3년 이상",
                        "min3": 5000, "max3": 7000, "loc3": "서울", "type3": "정규직", "level3": "시니어", "skills3": "Project Management,Agile,Scrum"
                    })
                    
                    logger.info("✅ 샘플 채용 공고 데이터가 추가되었습니다.")
                
                await session.commit()
                logger.info("✅ 모든 샘플 데이터가 성공적으로 추가되었습니다.")
                
        except Exception as e:
            logger.error(f"❌ 샘플 데이터 추가 실패: {str(e)}")
            raise
    
    async def close(self):
        """연결 종료"""
        await self.async_engine.dispose()
        logger.info("✅ 데이터베이스 연결이 종료되었습니다.")


# 전역 데이터베이스 매니저 인스턴스
db_manager = DatabaseManager()


async def init_database():
    """데이터베이스 초기화"""
    logger.info("🔄 데이터베이스 초기화를 시작합니다...")
    
    # 연결 확인
    if not await db_manager.check_database_connection():
        raise Exception("데이터베이스 연결에 실패했습니다.")
    
    # 스키마 생성
    await db_manager.create_database_schema()
    
    # 샘플 데이터 추가
    await db_manager.insert_sample_data()
    
    # 테이블 정보 확인
    table_info = await db_manager.get_table_info()
    logger.info(f"📊 생성된 테이블 정보: {table_info}")
    
    logger.info("✅ 데이터베이스 초기화가 완료되었습니다!")


if __name__ == "__main__":
    # 스크립트로 직접 실행 시
    asyncio.run(init_database())