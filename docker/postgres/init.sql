-- MLOps 스키마 생성
CREATE SCHEMA IF NOT EXISTS mlops;

-- 스키마 권한 설정
GRANT ALL PRIVILEGES ON SCHEMA mlops TO postgres;

-- 확장 프로그램 설치 (필요한 경우)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- MLOps 테이블들이 자동으로 생성될 수 있도록 스키마 준비
COMMENT ON SCHEMA mlops IS '장년층 이력서 생성 도우미 - MLOps 플랫폼 데이터베이스 스키마';