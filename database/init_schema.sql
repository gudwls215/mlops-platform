-- MLOps Platform Database Schema
-- PostgreSQL 스키마 생성 및 초기 데이터 설정
--
-- 데이터베이스 구조:
--   postgres(DB) → mlops(스키마) → 테이블들
--
-- 접속 정보:
--   Host: 114.202.2.226
--   Port: 5433
--   Database: postgres (mlops DB가 아님!)
--   Schema: mlops
--
-- 사용 방법:
--   psql -h 114.202.2.226 -p 5433 -U postgres -d postgres -f init_schema.sql
--

-- 스키마 생성
CREATE SCHEMA IF NOT EXISTS mlops;

-- 사용자 테이블
CREATE TABLE IF NOT EXISTS mlops.users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    age INTEGER,
    phone VARCHAR(20),
    address TEXT,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- 이력서 테이블
CREATE TABLE IF NOT EXISTS mlops.resumes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES mlops.users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    skills TEXT,
    experience_years INTEGER,
    education TEXT,
    certifications TEXT,
    career_summary TEXT,
    generated_by_ai BOOLEAN DEFAULT FALSE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- 채용 공고 테이블
CREATE TABLE IF NOT EXISTS mlops.job_postings (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    company VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    requirements TEXT NOT NULL,
    salary_min INTEGER,
    salary_max INTEGER,
    location VARCHAR(100),
    employment_type VARCHAR(50),
    experience_level VARCHAR(50),
    skills_required TEXT,
    deadline DATE,
    source_url VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- 자기소개서 테이블 (사용자가 작성한 자소서)
CREATE TABLE IF NOT EXISTS mlops.cover_letters (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES mlops.users(id) ON DELETE CASCADE,
    job_posting_id INTEGER REFERENCES mlops.job_postings(id) ON DELETE SET NULL,
    resume_id INTEGER REFERENCES mlops.resumes(id) ON DELETE SET NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    generated_by_ai BOOLEAN DEFAULT FALSE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- 자기소개서 샘플 테이블 (크롤링한 합격 자소서)
CREATE TABLE IF NOT EXISTS mlops.cover_letter_samples (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    company VARCHAR(200) NOT NULL,
    position VARCHAR(200),
    department VARCHAR(200),
    experience_level VARCHAR(100),
    content TEXT NOT NULL,
    is_passed BOOLEAN DEFAULT TRUE,
    application_year INTEGER,
    keywords TEXT[],
    url VARCHAR(1000) UNIQUE NOT NULL,
    url_hash VARCHAR(64),
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    source VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- 예측 로그 테이블
CREATE TABLE IF NOT EXISTS mlops.prediction_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES mlops.users(id) ON DELETE CASCADE,
    resume_id INTEGER REFERENCES mlops.resumes(id) ON DELETE SET NULL,
    job_posting_id INTEGER REFERENCES mlops.job_postings(id) ON DELETE SET NULL,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50),
    prediction_score REAL NOT NULL,
    prediction_result JSONB,
    input_features JSONB,
    execution_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- 지원 내역 테이블
CREATE TABLE IF NOT EXISTS mlops.job_applications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES mlops.users(id) ON DELETE CASCADE,
    job_posting_id INTEGER NOT NULL REFERENCES mlops.job_postings(id) ON DELETE CASCADE,
    resume_id INTEGER NOT NULL REFERENCES mlops.resumes(id) ON DELETE CASCADE,
    cover_letter_id INTEGER REFERENCES mlops.cover_letters(id) ON DELETE SET NULL,
    status VARCHAR(50) DEFAULT 'applied' NOT NULL,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS ix_mlops_users_email ON mlops.users(email);
CREATE INDEX IF NOT EXISTS ix_mlops_resumes_user_id ON mlops.resumes(user_id);
CREATE INDEX IF NOT EXISTS ix_mlops_resumes_title ON mlops.resumes(title);
CREATE INDEX IF NOT EXISTS ix_mlops_job_postings_title ON mlops.job_postings(title);
CREATE INDEX IF NOT EXISTS ix_mlops_job_postings_company ON mlops.job_postings(company);
CREATE INDEX IF NOT EXISTS ix_mlops_job_postings_location ON mlops.job_postings(location);
CREATE INDEX IF NOT EXISTS ix_mlops_cover_letters_user_id ON mlops.cover_letters(user_id);
CREATE INDEX IF NOT EXISTS ix_mlops_cover_letters_job_posting_id ON mlops.cover_letters(job_posting_id);
CREATE INDEX IF NOT EXISTS idx_cover_letter_samples_company ON mlops.cover_letter_samples(company);
CREATE INDEX IF NOT EXISTS idx_cover_letter_samples_position ON mlops.cover_letter_samples(position);
CREATE INDEX IF NOT EXISTS idx_cover_letter_samples_is_passed ON mlops.cover_letter_samples(is_passed);
CREATE INDEX IF NOT EXISTS idx_cover_letter_samples_year ON mlops.cover_letter_samples(application_year);
CREATE INDEX IF NOT EXISTS idx_cover_letter_samples_created_at ON mlops.cover_letter_samples(created_at);
CREATE UNIQUE INDEX IF NOT EXISTS idx_cover_letters_url_hash_unique ON mlops.cover_letter_samples(url_hash);
CREATE INDEX IF NOT EXISTS ix_mlops_prediction_logs_user_id ON mlops.prediction_logs(user_id);
CREATE INDEX IF NOT EXISTS ix_mlops_prediction_logs_model_name ON mlops.prediction_logs(model_name);
CREATE INDEX IF NOT EXISTS ix_mlops_prediction_logs_created_at ON mlops.prediction_logs(created_at);
CREATE INDEX IF NOT EXISTS ix_mlops_job_applications_user_id ON mlops.job_applications(user_id);
CREATE INDEX IF NOT EXISTS ix_mlops_job_applications_status ON mlops.job_applications(status);
CREATE INDEX IF NOT EXISTS ix_mlops_job_applications_applied_at ON mlops.job_applications(applied_at);

-- 업데이트 트리거 함수 생성
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 각 테이블에 업데이트 트리거 적용
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON mlops.users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_resumes_updated_at BEFORE UPDATE ON mlops.resumes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_job_postings_updated_at BEFORE UPDATE ON mlops.job_postings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_cover_letters_updated_at BEFORE UPDATE ON mlops.cover_letters FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_cover_letter_samples_updated_at BEFORE UPDATE ON mlops.cover_letter_samples FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_job_applications_updated_at BEFORE UPDATE ON mlops.job_applications FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 샘플 데이터 (개발용)
INSERT INTO mlops.users (email, hashed_password, full_name, age, phone, address) VALUES
('test@example.com', '$2b$12$abcdefghijklmnopqrstuvwxyz', '김테스트', 55, '010-1234-5678', '서울시 강남구'),
('senior@example.com', '$2b$12$abcdefghijklmnopqrstuvwxyz', '박시니어', 52, '010-9876-5432', '서울시 서초구')
ON CONFLICT (email) DO NOTHING;

-- 샘플 채용 공고
INSERT INTO mlops.job_postings (title, company, description, requirements, salary_min, salary_max, location, employment_type, experience_level, skills_required) VALUES
('시니어 백엔드 개발자', 'ABC 기술', '경험 많은 백엔드 개발자를 모집합니다', 'Python, Java, 5년 이상 경험', 4000, 6000, '서울', '정규직', '시니어', 'Python,Java,Spring,Django'),
('데이터 분석가', 'XYZ 데이터', '데이터 분석 및 인사이트 도출', 'Python, SQL, 통계 지식', 3500, 5000, '서울', '정규직', '중급', 'Python,SQL,Pandas,NumPy'),
('프로젝트 매니저', 'DEF 컨설팅', 'IT 프로젝트 관리 전문가', 'PMP 자격증, 관리 경험 3년 이상', 5000, 7000, '서울', '정규직', '시니어', 'Project Management,Agile,Scrum')
ON CONFLICT DO NOTHING;

COMMENT ON SCHEMA mlops IS 'MLOps Platform Database Schema for Senior Job Seekers';
COMMENT ON TABLE mlops.users IS '사용자 정보 테이블';
COMMENT ON TABLE mlops.resumes IS '이력서 정보 테이블';
COMMENT ON TABLE mlops.job_postings IS '채용 공고 테이블';
COMMENT ON TABLE mlops.cover_letters IS '사용자가 작성한 자기소개서 테이블';
COMMENT ON TABLE mlops.cover_letter_samples IS '크롤링한 합격 자기소개서 샘플 테이블 (AI 학습용)';
COMMENT ON TABLE mlops.prediction_logs IS 'ML 모델 예측 로그 테이블';
COMMENT ON TABLE mlops.job_applications IS '지원 내역 테이블';