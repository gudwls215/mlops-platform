"""
Database connection test script
실제 PostgreSQL 데이터베이스 연결을 테스트합니다.
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# 환경 변수에서 데이터베이스 URL 가져오기
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://your_username:your_password@114.202.2.226:5433/mlops")

def test_database_connection():
    """데이터베이스 연결 테스트"""
    print("🔍 데이터베이스 연결 테스트를 시작합니다...")
    print(f"📊 연결 URL: {DATABASE_URL.replace(DATABASE_URL.split('@')[0].split('://')[1], '***:***')}")
    
    try:
        # 데이터베이스 엔진 생성
        engine = create_engine(DATABASE_URL)
        
        # 연결 테스트
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✅ 데이터베이스 연결 성공!")
            print(f"📋 PostgreSQL 버전: {version}")
            
            # 스키마 확인
            result = connection.execute(text("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'mlops';"))
            schema_exists = result.fetchone()
            
            if schema_exists:
                print("✅ 'mlops' 스키마가 존재합니다.")
            else:
                print("⚠️  'mlops' 스키마가 존재하지 않습니다.")
                print("스키마 생성을 위해 다음 SQL을 실행하세요:")
                print("CREATE SCHEMA IF NOT EXISTS mlops;")
            
            # 테이블 목록 확인
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'mlops'
                ORDER BY table_name;
            """))
            tables = result.fetchall()
            
            if tables:
                print(f"📋 'mlops' 스키마의 테이블 목록:")
                for table in tables:
                    print(f"  - {table[0]}")
            else:
                print("📋 'mlops' 스키마에 테이블이 없습니다.")
        
        return True
        
    except SQLAlchemyError as e:
        print(f"❌ 데이터베이스 연결 실패:")
        print(f"   오류: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 예기치 않은 오류:")
        print(f"   오류: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_database_connection()
    sys.exit(0 if success else 1)