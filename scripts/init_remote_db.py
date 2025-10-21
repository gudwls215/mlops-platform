#!/usr/bin/env python3
"""
원격 데이터베이스에 mlops 스키마 생성 스크립트
"""
import psycopg2
import sys
import os

def init_database():
    """원격 PostgreSQL 데이터베이스에 mlops 스키마 및 테이블 생성"""
    try:
        # 원격 데이터베이스 연결
        connection = psycopg2.connect(
            host="114.202.2.226",
            port=5433,
            database="mlops",
            user="postgres",
            password="xlxldpa!@#"
        )
        
        cursor = connection.cursor()
        
        print("=== MLOps 데이터베이스 초기화 ===")
        print(f"연결 성공: {connection.get_dsn_parameters()['host']}:{connection.get_dsn_parameters()['port']}")
        
        # SQL 스크립트 파일 읽기
        sql_file_path = "/home/ttm/tensorflow-jupyter/jupyterNotebook/khj/mlops-platform/database/init_schema.sql"
        
        with open(sql_file_path, 'r', encoding='utf-8') as file:
            sql_script = file.read()
        
        print("\n📋 SQL 스크립트 실행 중...")
        
        # SQL 스크립트 실행
        cursor.execute(sql_script)
        connection.commit()
        
        print("✅ 스키마 생성 완료!")
        
        # 생성된 테이블 확인
        query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'mlops'
        ORDER BY table_name;
        """
        cursor.execute(query)
        tables = cursor.fetchall()
        
        print("\n📊 생성된 테이블:")
        if tables:
            for table in tables:
                print(f"  ✅ {table[0]}")
                
                # 각 테이블의 행 수 확인
                try:
                    count_query = f"SELECT COUNT(*) FROM mlops.{table[0]};"
                    cursor.execute(count_query)
                    count = cursor.fetchone()[0]
                    print(f"     → {count}개 레코드")
                except Exception as e:
                    print(f"     → 조회 실패: {e}")
        else:
            print("  ❌ 테이블 생성 실패")
        
        cursor.close()
        connection.close()
        
        print("\n🎉 데이터베이스 초기화 완료!")
        
    except Exception as e:
        print(f"❌ 데이터베이스 초기화 중 오류: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = init_database()
    if success:
        print("\n✅ 이제 사라민 크롤러를 다시 실행할 수 있습니다!")
    else:
        print("\n❌ 초기화 실패. 다시 시도하세요.")
        sys.exit(1)