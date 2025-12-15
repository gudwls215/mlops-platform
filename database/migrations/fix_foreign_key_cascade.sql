-- job_recommendations 외래 키 제약 조건을 CASCADE로 변경
-- 이렇게 하면 cover_letter_samples 삭제 시 자동으로 관련 job_recommendations도 삭제됨

-- 1. 기존 외래 키 제약 조건 삭제
ALTER TABLE mlops.job_recommendations 
DROP CONSTRAINT IF EXISTS job_recommendations_resume_id_fkey;

-- 2. CASCADE 옵션으로 외래 키 재생성
ALTER TABLE mlops.job_recommendations 
ADD CONSTRAINT job_recommendations_resume_id_fkey 
FOREIGN KEY (resume_id) 
REFERENCES mlops.cover_letter_samples(id) 
ON DELETE CASCADE;

-- 3. job_postings 외래 키도 CASCADE로 변경 (일관성 유지)
ALTER TABLE mlops.job_recommendations 
DROP CONSTRAINT IF EXISTS job_recommendations_job_id_fkey;

ALTER TABLE mlops.job_recommendations 
ADD CONSTRAINT job_recommendations_job_id_fkey 
FOREIGN KEY (job_id) 
REFERENCES mlops.job_postings(id) 
ON DELETE CASCADE;

-- 4. 변경사항 확인
SELECT
    tc.constraint_name,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    rc.delete_rule
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
JOIN information_schema.referential_constraints AS rc
    ON tc.constraint_name = rc.constraint_name
    AND tc.table_schema = rc.constraint_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
AND tc.table_schema = 'mlops'
AND tc.table_name = 'job_recommendations';
