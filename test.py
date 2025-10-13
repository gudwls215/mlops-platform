
import psycopg2

# 연결 정보
host = '114.202.2.226'
port = '5433'
user = 'postgres'
password = 'xlxldpa!@#'
database = 'mlops'

try:
    # mlops DB에 연결
    conn = psycopg2.connect(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password
    )
    
    cur = conn.cursor()
    
    print(f'✅ {database} 데이터베이스 연결 성공')
    
    # 1. 모든 스키마 목록 확인
    cur.execute('''
        SELECT schema_name 
        FROM information_schema.schemata
        ORDER BY schema_name;
    ''')
    
    schemas = cur.fetchall()
    print(f'\\n📋 전체 스키마 목록:')
    for schema in schemas:
        print(f'  - {schema[0]}')
    
    # 2. mlops 스키마 존재 여부 직접 확인
    cur.execute('''
        SELECT COUNT(*) 
        FROM information_schema.schemata 
        WHERE schema_name = 'mlops';
    ''')
    
    mlops_exists = cur.fetchone()[0]
    
    print(f'\\n🎯 mlops 스키마 존재 여부: {"존재" if mlops_exists > 0 else "없음"}')
    
    # 3. mlops 스키마가 없다면 다시 생성
    if mlops_exists == 0:
        print('\\n🔨 mlops 스키마가 없습니다. 다시 생성합니다...')
        cur.execute('CREATE SCHEMA mlops;')
        conn.commit()
        print('✅ mlops 스키마 생성 완료')
    
    # 4. 모든 테이블 목록 확인 (스키마별로)
    cur.execute('''
        SELECT table_schema, table_name
        FROM information_schema.tables 
        WHERE table_type = 'BASE TABLE'
        AND table_schema NOT IN ('information_schema', 'pg_catalog')
        ORDER BY table_schema, table_name;
    ''')
    
    tables = cur.fetchall()
    print(f'\\n📋 전체 테이블 목록:')
    if tables:
        current_schema = None
        for schema_name, table_name in tables:
            if current_schema != schema_name:
                print(f'\\n  [{schema_name} 스키마]')
                current_schema = schema_name
            print(f'    - {table_name}')
    else:
        print('  테이블이 없습니다.')
    
    # 5. mlops 스키마에 테이블이 없다면 생성
    cur.execute('''
        SELECT COUNT(*) 
        FROM information_schema.tables 
        WHERE table_schema = 'mlops';
    ''')
    
    mlops_table_count = cur.fetchone()[0]
    print(f'\\n🎯 mlops 스키마 테이블 개수: {mlops_table_count}개')
    
    if mlops_table_count == 0:
        print('\\n🔨 mlops 스키마에 테이블이 없습니다. 테이블을 생성합니다...')
        
        # mlops.job_postings 테이블 생성
        job_postings_sql = '''
        CREATE TABLE mlops.job_postings (
            id SERIAL PRIMARY KEY,
            title VARCHAR(500) NOT NULL,
            company VARCHAR(200) NOT NULL,
            location VARCHAR(200),
            salary VARCHAR(200),
            employment_type VARCHAR(100),
            experience VARCHAR(200),
            education VARCHAR(200),
            main_duties TEXT,
            qualifications TEXT,
            preferences TEXT,
            deadline DATE,
            posted_date DATE,
            url VARCHAR(1000) UNIQUE,
            source VARCHAR(50) DEFAULT 'saramin',
            is_senior_friendly BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        '''
        
        cur.execute(job_postings_sql)
        print('✅ mlops.job_postings 테이블 생성 완료')
        
        # mlops.users 테이블 생성
        users_sql = '''
        CREATE TABLE mlops.users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(200) UNIQUE,
            phone VARCHAR(50),
            birth_date DATE,
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        '''
        
        cur.execute(users_sql)
        print('✅ mlops.users 테이블 생성 완료')
        
        # mlops.resumes 테이블 생성
        resumes_sql = '''
        CREATE TABLE mlops.resumes (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES mlops.users(id),
            title VARCHAR(200),
            summary TEXT,
            experience_years INTEGER,
            skills TEXT[],
            education TEXT,
            career_history JSONB,
            certifications TEXT[],
            languages TEXT[],
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        '''
        
        cur.execute(resumes_sql)
        print('✅ mlops.resumes 테이블 생성 완료')
        
        # mlops.cover_letters 테이블 생성
        cover_letters_sql = '''
        CREATE TABLE mlops.cover_letters (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES mlops.users(id),
            job_posting_id INTEGER REFERENCES mlops.job_postings(id),
            content TEXT NOT NULL,
            generated_by VARCHAR(50) DEFAULT 'gpt-4',
            match_score FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        '''
        
        cur.execute(cover_letters_sql)
        print('✅ mlops.cover_letters 테이블 생성 완료')
        
        # mlops.prediction_logs 테이블 생성
        prediction_logs_sql = '''
        CREATE TABLE mlops.prediction_logs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES mlops.users(id),
            job_posting_id INTEGER REFERENCES mlops.job_postings(id),
            prediction_type VARCHAR(50),
            input_data JSONB,
            prediction_result JSONB,
            confidence_score FLOAT,
            model_version VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        '''
        
        cur.execute(prediction_logs_sql)
        print('✅ mlops.prediction_logs 테이블 생성 완료')
        
        # 인덱스 생성
        indexes = [
            'CREATE INDEX idx_mlops_job_postings_company ON mlops.job_postings(company);',
            'CREATE INDEX idx_mlops_job_postings_location ON mlops.job_postings(location);',
            'CREATE INDEX idx_mlops_job_postings_posted_date ON mlops.job_postings(posted_date);',
            'CREATE INDEX idx_mlops_job_postings_is_senior_friendly ON mlops.job_postings(is_senior_friendly);'
        ]
        
        for idx_sql in indexes:
            cur.execute(idx_sql)
        
        print('✅ 인덱스 생성 완료')
        
        # 변경사항 커밋
        conn.commit()
    
    # 6. 최종 확인 - mlops 스키마 테이블 목록
    cur.execute('''
        SELECT table_name, 
               (SELECT COUNT(*) FROM information_schema.columns 
                WHERE table_name = t.table_name AND table_schema = 'mlops') as column_count
        FROM information_schema.tables t
        WHERE table_schema = 'mlops'
        ORDER BY table_name;
    ''')
    
    mlops_tables = cur.fetchall()
    print(f'\\n📋 최종 mlops 스키마 테이블 목록:')
    print('-' * 50)
    
    if mlops_tables:
        for table_name, col_count in mlops_tables:
            print(f'  mlops.{table_name} ({col_count}개 컬럼)')
        
        # job_postings 테이블 구조 확인
        cur.execute('''
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'job_postings' 
            AND table_schema = 'mlops'
            ORDER BY ordinal_position;
        ''')
        
        columns = cur.fetchall()
        
        print(f'\\n📋 mlops.job_postings 테이블 구조:')
        print('-' * 50)
        
        for col_name, data_type, nullable in columns:
            null_str = 'NULL' if nullable == 'YES' else 'NOT NULL'
            print(f'  {col_name:<20} | {data_type:<15} | {null_str}')
        
        # 핵심 컬럼 확인
        required_columns = ['main_duties', 'qualifications', 'preferences']
        existing_columns = [col[0] for col in columns]
        
        print(f'\\n🎯 핵심 컬럼 확인:')
        for col in required_columns:
            status = '✅' if col in existing_columns else '❌'
            print(f'  {status} {col}')
            
    else:
        print('  mlops 스키마에 테이블이 없습니다!')
    
    # 7. DB 클라이언트 연결 정보 재안내
    print(f'\\n📋 DB 클라이언트 연결 정보:')
    print('-' * 50)
    print(f'Host: {host}')
    print(f'Port: {port}')
    print(f'Database: {database}')
    print(f'Username: {user}')
    print(f'Password: {password}')
    print(f'Schema: mlops')
    print(f'\\n💡 DB 클라이언트에서 연결 후 \"mlops\" 스키마를 선택하세요!')
    
    cur.close()
    conn.close()
    
    print(f'\\n✅ mlops 스키마 확인 완료!')
    
except Exception as e:
    print(f'❌ 오류 발생: {e}')
    