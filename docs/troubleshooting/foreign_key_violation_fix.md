# 외래 키 제약 조건 위반 오류 해결

## 문제 상황

```
ForeignKeyViolation: update or delete on table "cover_letter_samples" violates foreign key constraint "job_recommendations_resume_id_fkey" on table "job_recommendations"
DETAIL: Key (id)=(1) is still referenced from table "job_recommendations".
```

### 원인 분석

1. **외래 키 제약 조건**: `job_recommendations` 테이블이 `cover_letter_samples` 테이블을 참조
2. **DELETE 정책**: 기존 설정이 `NO ACTION`이라 참조되는 레코드 삭제 불가
3. **중복 제거 실패**: 중복된 `cover_letter_samples` 레코드를 삭제하려 할 때 오류 발생

## 해결 방법

### 1. duplicate_remover.py 수정

중복 레코드 삭제 전에 참조하는 외래 키를 업데이트하도록 수정:

```python
# 나머지 레코드 삭제
remove_items = [item for item in items if item['id'] != keep_item['id']]

for item in remove_items:
    # 1. 먼저 이 레코드를 참조하는 외래 키 관계들을 업데이트/삭제
    # job_recommendations의 resume_id를 keep_item으로 변경
    update_recommendations_query = """
        UPDATE mlops.job_recommendations 
        SET resume_id = %s 
        WHERE resume_id = %s
    """
    self.db.execute_query(
        update_recommendations_query, 
        (keep_item['id'], item['id']), 
        fetch=False
    )
    
    # 2. 이제 안전하게 cover_letter_samples 레코드 삭제
    delete_query = "DELETE FROM mlops.cover_letter_samples WHERE id = %s"
    self.db.execute_query(delete_query, (item['id'],), fetch=False)
```

**장점**:
- 기존 추천 데이터 유지
- 참조 무결성 보장

### 2. 외래 키 제약 조건을 CASCADE로 변경

향후 문제를 예방하기 위해 외래 키 삭제 정책을 `CASCADE`로 변경:

```sql
-- 1. 기존 외래 키 삭제
ALTER TABLE mlops.job_recommendations 
DROP CONSTRAINT IF EXISTS job_recommendations_resume_id_fkey;

-- 2. CASCADE 옵션으로 재생성
ALTER TABLE mlops.job_recommendations 
ADD CONSTRAINT job_recommendations_resume_id_fkey 
FOREIGN KEY (resume_id) 
REFERENCES mlops.cover_letter_samples(id) 
ON DELETE CASCADE;

-- 3. job_id도 CASCADE로 변경 (일관성)
ALTER TABLE mlops.job_recommendations 
DROP CONSTRAINT IF EXISTS job_recommendations_job_id_fkey;

ALTER TABLE mlops.job_recommendations 
ADD CONSTRAINT job_recommendations_job_id_fkey 
FOREIGN KEY (job_id) 
REFERENCES mlops.job_postings(id) 
ON DELETE CASCADE;
```

**장점**:
- 자동으로 관련 레코드 삭제
- 데이터 정합성 유지
- 향후 유지보수 간편

## 적용 결과

### Before (NO ACTION)
```
⚠️ job_recommendations_resume_id_fkey: resume_id -> cover_letter_samples (DELETE NO ACTION)
⚠️ job_recommendations_job_id_fkey: job_id -> job_postings (DELETE NO ACTION)
```

### After (CASCADE)
```
✅ job_recommendations_resume_id_fkey: resume_id -> cover_letter_samples (DELETE CASCADE)
✅ job_recommendations_job_id_fkey: job_id -> job_postings (DELETE CASCADE)
```

## 동작 방식

### 중복 제거 프로세스
1. **중복 감지**: 동일한 URL, 유사한 내용의 레코드 찾기
2. **보존 레코드 선택**: 최신/가장 완전한 데이터 선택
3. **외래 키 업데이트**: 삭제할 레코드를 참조하는 모든 외래 키를 보존 레코드로 변경
4. **안전한 삭제**: 이제 참조가 없으므로 안전하게 삭제

### CASCADE 동작
- `cover_letter_samples` 삭제 시 → 관련 `job_recommendations` 자동 삭제
- `job_postings` 삭제 시 → 관련 `job_recommendations` 자동 삭제
- `user_interactions`는 이미 CASCADE 설정되어 있음

## 테스트 방법

```bash
# 1. duplicate_remover 테스트
cd /home/ttm/tensorflow-jupyter/jupyterNotebook/khj/mlops-platform/crawling
python -m pytest tests/test_duplicate_remover.py

# 2. 전체 파이프라인 테스트
python -c "
import asyncio
from batch_processor_manager import BatchProcessorManager, JobType

async def test():
    processor = BatchProcessorManager()
    job_id = processor.create_job(JobType.FULL_PIPELINE)
    job = processor.job_queue.pop(0)
    result = await processor.run_job(job)
    print(f'Status: {result.get(\"status\")}')
    print(f'Errors: {result.get(\"errors\", 0)}')

asyncio.run(test())
"
```

## 관련 파일

- `crawling/duplicate_remover.py` - 중복 제거 로직 수정
- `database/migrations/fix_foreign_key_cascade.sql` - CASCADE 마이그레이션
- `crawling/batch_duplicate_processor.py` - 배치 처리
- `airflow/dags/data_collection_dag.py` - DAG 실행

## 주의사항

1. **CASCADE는 신중히 사용**: 자동 삭제가 의도하지 않은 데이터 손실을 야기할 수 있음
2. **백업 필수**: 외래 키 변경 전 데이터베이스 백업
3. **테스트 환경 먼저**: 프로덕션 적용 전 테스트 환경에서 검증

## 추가 개선사항

### 1. 소프트 삭제 (Soft Delete) 도입
```python
# deleted_at 컬럼 추가
ALTER TABLE mlops.cover_letter_samples 
ADD COLUMN deleted_at TIMESTAMP DEFAULT NULL;

# 삭제 대신 마킹
UPDATE mlops.cover_letter_samples 
SET deleted_at = NOW() 
WHERE id = %s;
```

### 2. 중복 제거 전략 개선
- 머신러닝 기반 유사도 계산
- 사용자 피드백 반영
- 중복 후보 리뷰 UI 제공

### 3. 모니터링 강화
- 외래 키 위반 오류 알림
- 중복 제거 통계 대시보드
- 데이터 품질 메트릭 추적
