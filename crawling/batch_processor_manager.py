"""
배치 처리 관리자
크롤링, 텍스트 정제, 중복 제거, 검증의 전체 배치 작업 관리
"""
import logging
import asyncio
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import traceback
import json

from text_cleaner import TextCleaner
from duplicate_remover import DuplicateRemover
from batch_duplicate_processor import BatchDuplicateProcessor
from data_validator import DataValidator, ValidationLevel
from data_processing_pipeline import DataProcessingPipeline
from database import DatabaseManager


class JobStatus(Enum):
    """작업 상태"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(Enum):
    """작업 타입"""
    CRAWLING = "crawling"
    TEXT_CLEANING = "text_cleaning"
    DUPLICATE_REMOVAL = "duplicate_removal"
    DATA_VALIDATION = "data_validation"
    FULL_PIPELINE = "full_pipeline"
    DATA_MAINTENANCE = "data_maintenance"


@dataclass
class BatchJob:
    """배치 작업"""
    job_id: str
    job_type: JobType
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    config: Dict[str, Any] = field(default_factory=dict)
    result: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3


class BatchProcessorManager:
    """배치 처리 관리자"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        배치 처리 관리자 초기화
        
        Args:
            config: 설정 딕셔너리
        """
        self.config = config or {}
        
        # 기본 설정
        self.max_concurrent_jobs = self.config.get('max_concurrent_jobs', 3)
        self.job_timeout = self.config.get('job_timeout', 3600)  # 1시간
        self.cleanup_interval = self.config.get('cleanup_interval', 86400)  # 1일
        self.enable_notifications = self.config.get('enable_notifications', False)
        
        # 모듈 초기화
        self.text_cleaner = TextCleaner()
        self.duplicate_remover = DuplicateRemover()
        self.batch_duplicate_processor = BatchDuplicateProcessor()
        self.data_validator = DataValidator(ValidationLevel.STANDARD)
        self.pipeline = DataProcessingPipeline()
        self.db = DatabaseManager()
        
        # 작업 관리
        self.active_jobs: Dict[str, BatchJob] = {}
        self.job_queue: List[BatchJob] = []
        self.completed_jobs: List[BatchJob] = []
        
        # 로깅 설정
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # 통계
        self.stats = {
            'total_jobs_created': 0,
            'jobs_completed': 0,
            'jobs_failed': 0,
            'jobs_cancelled': 0,
            'total_processing_time': 0,
            'manager_start_time': datetime.now()
        }
    
    def create_job(self, job_type: JobType, config: Dict[str, Any] = None) -> str:
        """
        배치 작업 생성
        
        Args:
            job_type: 작업 타입
            config: 작업 설정
            
        Returns:
            작업 ID
        """
        job_id = f"{job_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.active_jobs)}"
        
        job = BatchJob(
            job_id=job_id,
            job_type=job_type,
            config=config or {}
        )
        
        self.job_queue.append(job)
        self.stats['total_jobs_created'] += 1
        
        self.logger.info(f"배치 작업 생성: {job_id} ({job_type.value})")
        
        return job_id
    
    async def run_job(self, job: BatchJob) -> Dict[str, Any]:
        """
        단일 배치 작업 실행
        
        Args:
            job: 실행할 작업
            
        Returns:
            작업 결과
        """
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now()
        
        self.logger.info(f"배치 작업 시작: {job.job_id}")
        
        try:
            # 작업 타입에 따른 실행
            if job.job_type == JobType.TEXT_CLEANING:
                result = await self._run_text_cleaning_job(job)
            elif job.job_type == JobType.DUPLICATE_REMOVAL:
                result = await self._run_duplicate_removal_job(job)
            elif job.job_type == JobType.DATA_VALIDATION:
                result = await self._run_validation_job(job)
            elif job.job_type == JobType.FULL_PIPELINE:
                result = await self._run_full_pipeline_job(job)
            elif job.job_type == JobType.DATA_MAINTENANCE:
                result = await self._run_maintenance_job(job)
            else:
                raise ValueError(f"지원하지 않는 작업 타입: {job.job_type}")
            
            job.status = JobStatus.COMPLETED
            job.result = result
            job.completed_at = datetime.now()
            
            self.stats['jobs_completed'] += 1
            processing_time = (job.completed_at - job.started_at).total_seconds()
            self.stats['total_processing_time'] += processing_time
            
            self.logger.info(f"배치 작업 완료: {job.job_id} ({processing_time:.2f}초)")
            
            return result
            
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now()
            
            self.stats['jobs_failed'] += 1
            
            self.logger.error(f"배치 작업 실패: {job.job_id} - {str(e)}")
            self.logger.error(f"스택 트레이스: {traceback.format_exc()}")
            
            # 재시도 로직
            if job.retry_count < job.max_retries:
                job.retry_count += 1
                job.status = JobStatus.PENDING
                self.job_queue.append(job)
                self.logger.info(f"작업 재시도 예약: {job.job_id} (시도 {job.retry_count}/{job.max_retries})")
            
            raise
    
    async def _run_text_cleaning_job(self, job: BatchJob) -> Dict[str, Any]:
        """텍스트 정제 작업 실행"""
        target_table = job.config.get('target_table', 'both')  # 'job_postings', 'cover_letters', 'both'
        batch_size = job.config.get('batch_size', 100)
        
        result = {
            'job_postings_processed': 0,
            'cover_letters_processed': 0,
            'job_postings_cleaned': 0,
            'cover_letters_cleaned': 0,
            'processing_time': 0
        }
        
        start_time = datetime.now()
        
        self.db.connect()
        
        try:
            if target_table in ['job_postings', 'both']:
                # 채용공고 텍스트 정제
                jobs_query = "SELECT * FROM mlops.job_postings WHERE created_at >= %s ORDER BY created_at DESC"
                cutoff_time = datetime.now() - timedelta(days=job.config.get('days_back', 7))
                
                jobs = self.db.execute_query(jobs_query, (cutoff_time,))
                result['job_postings_processed'] = len(jobs)
                
                # 배치 처리
                for i in range(0, len(jobs), batch_size):
                    batch = jobs[i:i + batch_size]
                    
                    for job_posting in batch:
                        # 텍스트 정제
                        cleaned_title = self.text_cleaner.clean_job_posting_text(job_posting.get('title', ''))
                        cleaned_duties = self.text_cleaner.clean_job_posting_text(job_posting.get('main_duties', ''))
                        
                        # 데이터베이스 업데이트
                        update_query = """
                        UPDATE mlops.job_postings 
                        SET title = %s, main_duties = %s, updated_at = NOW()
                        WHERE id = %s
                        """
                        
                        self.db.execute_query(update_query, (cleaned_title, cleaned_duties, job_posting['id']), fetch=False)
                        result['job_postings_cleaned'] += 1
            
            if target_table in ['cover_letters', 'both']:
                # 자기소개서 텍스트 정제
                covers_query = "SELECT * FROM mlops.cover_letter_samples WHERE created_at >= %s ORDER BY created_at DESC"
                cutoff_time = datetime.now() - timedelta(days=job.config.get('days_back', 7))
                
                covers = self.db.execute_query(covers_query, (cutoff_time,))
                result['cover_letters_processed'] = len(covers)
                
                # 배치 처리
                for i in range(0, len(covers), batch_size):
                    batch = covers[i:i + batch_size]
                    
                    for cover_letter in batch:
                        # 텍스트 정제
                        cleaned_title = self.text_cleaner.clean_job_posting_text(cover_letter.get('title', ''))
                        cleaned_content = self.text_cleaner.clean_cover_letter_text(cover_letter.get('content', ''))
                        
                        # 데이터베이스 업데이트
                        update_query = """
                        UPDATE mlops.cover_letter_samples 
                        SET title = %s, content = %s, updated_at = NOW()
                        WHERE id = %s
                        """
                        
                        self.db.execute_query(update_query, (cleaned_title, cleaned_content, cover_letter['id']), fetch=False)
                        result['cover_letters_cleaned'] += 1
            
            # 변경사항 커밋
            self.db.connection.commit()
            
            end_time = datetime.now()
            result['processing_time'] = (end_time - start_time).total_seconds()
            
            return result
            
        finally:
            self.db.disconnect()
    
    async def _run_duplicate_removal_job(self, job: BatchJob) -> Dict[str, Any]:
        """중복 제거 작업 실행"""
        similarity_threshold = job.config.get('similarity_threshold', 0.85)
        keep_strategy = job.config.get('keep_strategy', 'most_complete')
        
        # 배치 중복 제거 프로세서 실행
        processor = BatchDuplicateProcessor(
            similarity_threshold=similarity_threshold,
            keep_strategy=keep_strategy,
            dry_run=False
        )
        
        result = processor.process_all_data()
        
        return result
    
    async def _run_validation_job(self, job: BatchJob) -> Dict[str, Any]:
        """데이터 검증 작업 실행"""
        validation_level = ValidationLevel(job.config.get('validation_level', 'standard'))
        target_table = job.config.get('target_table', 'both')
        
        validator = DataValidator(validation_level)
        
        result = {
            'job_postings_validation': None,
            'cover_letters_validation': None
        }
        
        self.db.connect()
        
        try:
            if target_table in ['job_postings', 'both']:
                # 채용공고 검증
                jobs_query = "SELECT * FROM mlops.job_postings ORDER BY created_at DESC LIMIT %s"
                limit = job.config.get('limit', 1000)
                
                jobs = self.db.execute_query(jobs_query, (limit,))
                
                if jobs:
                    job_validation_result = validator.batch_validate(jobs, 'job_posting')
                    result['job_postings_validation'] = job_validation_result
            
            if target_table in ['cover_letters', 'both']:
                # 자기소개서 검증
                covers_query = "SELECT * FROM mlops.cover_letter_samples ORDER BY created_at DESC LIMIT %s"
                limit = job.config.get('limit', 1000)
                
                covers = self.db.execute_query(covers_query, (limit,))
                
                if covers:
                    cover_validation_result = validator.batch_validate(covers, 'cover_letter')
                    result['cover_letters_validation'] = cover_validation_result
            
            return result
            
        finally:
            self.db.disconnect()
    
    async def _run_full_pipeline_job(self, job: BatchJob) -> Dict[str, Any]:
        """전체 파이프라인 작업 실행"""
        
        # 파이프라인 설정
        pipeline_config = {
            'similarity_threshold': job.config.get('similarity_threshold', 0.85),
            'keep_strategy': job.config.get('keep_strategy', 'most_complete'),
            'enable_text_cleaning': job.config.get('enable_text_cleaning', True),
            'enable_duplicate_removal': job.config.get('enable_duplicate_removal', True),
            'batch_size': job.config.get('batch_size', 100)
        }
        
        # 파이프라인 실행
        pipeline = DataProcessingPipeline(pipeline_config)
        
        # 샘플 데이터 (실제로는 크롤링 결과를 사용)
        job_postings = job.config.get('job_postings', [])
        cover_letters = job.config.get('cover_letters', [])
        
        result = pipeline.run_full_pipeline(
            job_postings=job_postings,
            cover_letters=cover_letters
        )
        
        return result
    
    async def _run_maintenance_job(self, job: BatchJob) -> Dict[str, Any]:
        """데이터 유지보수 작업 실행"""
        
        result = {
            'old_duplicates_cleaned': 0,
            'orphaned_records_removed': 0,
            'statistics_updated': False,
            'indexes_optimized': False
        }
        
        self.db.connect()
        
        try:
            # 오래된 중복 데이터 정리
            days_back = job.config.get('cleanup_days_back', 30)
            cleanup_count = self.batch_duplicate_processor.cleanup_old_duplicates(days_back)
            result['old_duplicates_cleaned'] = cleanup_count
            
            # 고아 레코드 정리 (URL이 없거나 빈 제목 등)
            orphan_job_query = """
            DELETE FROM mlops.job_postings 
            WHERE title IS NULL OR title = '' OR url IS NULL OR url = ''
            """
            
            orphan_cover_query = """
            DELETE FROM mlops.cover_letter_samples 
            WHERE title IS NULL OR title = '' OR content IS NULL OR content = '' OR url IS NULL OR url = ''
            """
            
            self.db.execute_query(orphan_job_query, fetch=False)
            self.db.execute_query(orphan_cover_query, fetch=False)
            self.db.connection.commit()
            
            result['orphaned_records_removed'] = True
            
            # 인덱스 최적화 (PostgreSQL VACUUM)
            if job.config.get('optimize_indexes', False):
                self.db.execute_query("VACUUM ANALYZE mlops.job_postings", fetch=False)
                self.db.execute_query("VACUUM ANALYZE mlops.cover_letter_samples", fetch=False)
                result['indexes_optimized'] = True
            
            result['statistics_updated'] = True
            
            return result
            
        finally:
            self.db.disconnect()
    
    async def process_queue(self):
        """작업 큐 처리"""
        while self.job_queue:
            # 동시 실행 작업 수 확인
            if len(self.active_jobs) >= self.max_concurrent_jobs:
                await asyncio.sleep(1)
                continue
            
            # 다음 작업 가져오기
            job = self.job_queue.pop(0)
            self.active_jobs[job.job_id] = job
            
            # 비동기로 작업 실행
            asyncio.create_task(self._execute_job_with_cleanup(job))
            
            await asyncio.sleep(0.1)  # CPU 사용률 조절
    
    async def _execute_job_with_cleanup(self, job: BatchJob):
        """작업 실행 및 정리"""
        try:
            await self.run_job(job)
        except Exception as e:
            self.logger.error(f"작업 실행 중 오류: {job.job_id} - {str(e)}")
        finally:
            # 활성 작업에서 제거
            if job.job_id in self.active_jobs:
                del self.active_jobs[job.job_id]
            
            # 완료된 작업 목록에 추가
            self.completed_jobs.append(job)
            
            # 완료된 작업 목록 크기 관리 (최근 100개만 보관)
            if len(self.completed_jobs) > 100:
                self.completed_jobs = self.completed_jobs[-100:]
    
    def get_job_status(self, job_id: str) -> Optional[BatchJob]:
        """작업 상태 조회"""
        # 활성 작업에서 찾기
        if job_id in self.active_jobs:
            return self.active_jobs[job_id]
        
        # 완료된 작업에서 찾기
        for job in self.completed_jobs:
            if job.job_id == job_id:
                return job
        
        # 대기 중인 작업에서 찾기
        for job in self.job_queue:
            if job.job_id == job_id:
                return job
        
        return None
    
    def cancel_job(self, job_id: str) -> bool:
        """작업 취소"""
        # 대기 중인 작업 취소
        for i, job in enumerate(self.job_queue):
            if job.job_id == job_id:
                job.status = JobStatus.CANCELLED
                self.job_queue.pop(i)
                self.completed_jobs.append(job)
                self.stats['jobs_cancelled'] += 1
                self.logger.info(f"작업 취소됨: {job_id}")
                return True
        
        # 실행 중인 작업은 취소할 수 없음 (향후 개선 가능)
        self.logger.warning(f"실행 중인 작업은 취소할 수 없습니다: {job_id}")
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """배치 처리 통계 반환"""
        uptime = (datetime.now() - self.stats['manager_start_time']).total_seconds()
        
        return {
            **self.stats,
            'active_jobs': len(self.active_jobs),
            'queued_jobs': len(self.job_queue),
            'completed_jobs_count': len(self.completed_jobs),
            'uptime_seconds': uptime,
            'average_processing_time': (
                self.stats['total_processing_time'] / max(self.stats['jobs_completed'], 1)
            )
        }
    
    def print_status_report(self):
        """상태 리포트 출력"""
        stats = self.get_statistics()
        
        print(f"\n{'='*60}")
        print("배치 처리 관리자 상태")
        print(f"{'='*60}")
        print(f"가동 시간: {stats['uptime_seconds']:.0f}초")
        print(f"생성된 총 작업: {stats['total_jobs_created']}")
        print(f"완료된 작업: {stats['jobs_completed']}")
        print(f"실패한 작업: {stats['jobs_failed']}")
        print(f"취소된 작업: {stats['jobs_cancelled']}")
        print(f"현재 실행 중: {stats['active_jobs']}")
        print(f"대기 중: {stats['queued_jobs']}")
        print(f"평균 처리 시간: {stats['average_processing_time']:.2f}초")
        
        if self.active_jobs:
            print(f"\n현재 실행 중인 작업:")
            for job_id, job in self.active_jobs.items():
                runtime = (datetime.now() - job.started_at).total_seconds() if job.started_at else 0
                print(f"  {job_id}: {job.job_type.value} (실행시간: {runtime:.1f}초)")
        
        if self.job_queue:
            print(f"\n대기 중인 작업:")
            for job in self.job_queue[:5]:  # 처음 5개만 표시
                print(f"  {job.job_id}: {job.job_type.value}")
        
        print(f"{'='*60}\n")


async def main():
    """배치 처리 관리자 실행 예제"""
    
    # 배치 관리자 생성
    manager = BatchProcessorManager({
        'max_concurrent_jobs': 2,
        'job_timeout': 300,
        'enable_notifications': False
    })
    
    print("배치 처리 관리자 시작...")
    
    try:
        # 테스트 작업들 생성
        job1_id = manager.create_job(JobType.TEXT_CLEANING, {
            'target_table': 'both',
            'days_back': 7,
            'batch_size': 50
        })
        
        job2_id = manager.create_job(JobType.DUPLICATE_REMOVAL, {
            'similarity_threshold': 0.85,
            'keep_strategy': 'most_complete'
        })
        
        job3_id = manager.create_job(JobType.DATA_VALIDATION, {
            'validation_level': 'standard',
            'target_table': 'both',
            'limit': 100
        })
        
        job4_id = manager.create_job(JobType.DATA_MAINTENANCE, {
            'cleanup_days_back': 30,
            'optimize_indexes': True
        })
        
        print(f"생성된 작업: {job1_id}, {job2_id}, {job3_id}, {job4_id}")
        
        # 작업 큐 처리 시작
        queue_task = asyncio.create_task(manager.process_queue())
        
        # 상태 모니터링
        start_time = datetime.now()
        timeout = 60  # 1분 타임아웃
        
        while (datetime.now() - start_time).total_seconds() < timeout:
            manager.print_status_report()
            
            # 모든 작업이 완료되었는지 확인
            if (len(manager.job_queue) == 0 and 
                len(manager.active_jobs) == 0 and 
                manager.stats['jobs_completed'] + manager.stats['jobs_failed'] >= 4):
                print("모든 작업이 완료되었습니다!")
                break
            
            await asyncio.sleep(5)
        
        # 정리
        queue_task.cancel()
        
        # 최종 통계
        print("\n=== 최종 결과 ===")
        for job in manager.completed_jobs:
            print(f"작업 {job.job_id}: {job.status.value}")
            if job.status == JobStatus.COMPLETED:
                print(f"  결과: {job.result}")
            elif job.status == JobStatus.FAILED:
                print(f"  오류: {job.error_message}")
        
        manager.print_status_report()
        
    except KeyboardInterrupt:
        print("\n배치 처리 관리자 중단됨")
    except Exception as e:
        print(f"배치 처리 관리자 오류: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())