"""
배치 예측 큐 시스템

비동기 배치 처리를 위한 큐 기반 시스템
- 대량 예측 요청을 큐에 저장
- 백그라운드에서 배치 처리
- 결과 조회 및 상태 추적
"""

import asyncio
import uuid
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from collections import deque
from threading import Lock
from pydantic import BaseModel, Field

from app.services.model_serving import ModelServingService, PredictionOutput


logger = logging.getLogger(__name__)


class BatchStatus(str, Enum):
    """배치 작업 상태"""
    PENDING = "pending"      # 대기 중
    PROCESSING = "processing"  # 처리 중
    COMPLETED = "completed"   # 완료
    FAILED = "failed"         # 실패


class BatchJob(BaseModel):
    """배치 작업 정보"""
    job_id: str = Field(..., description="작업 ID")
    status: BatchStatus = Field(..., description="작업 상태")
    total_samples: int = Field(..., description="전체 샘플 수")
    processed_samples: int = Field(0, description="처리된 샘플 수")
    created_at: str = Field(..., description="생성 시각")
    started_at: Optional[str] = Field(None, description="시작 시각")
    completed_at: Optional[str] = Field(None, description="완료 시각")
    error: Optional[str] = Field(None, description="에러 메시지")
    results: Optional[List[PredictionOutput]] = Field(None, description="예측 결과")


class BatchQueue:
    """
    배치 예측 큐
    
    FIFO 큐로 배치 작업을 관리하고 순차적으로 처리
    """
    
    def __init__(self, max_queue_size: int = 100):
        """
        Args:
            max_queue_size: 최대 큐 크기
        """
        self.max_queue_size = max_queue_size
        self.queue = deque(maxlen=max_queue_size)
        self.jobs: Dict[str, BatchJob] = {}
        self.lock = Lock()
        self.processing = False
        
        logger.info(f"BatchQueue 초기화: max_queue_size={max_queue_size}")
    
    def add_job(self, features_batch: List[List[float]]) -> str:
        """
        새 배치 작업 추가
        
        Args:
            features_batch: 특성 벡터 배치
            
        Returns:
            작업 ID
            
        Raises:
            ValueError: 큐가 가득 찬 경우
        """
        with self.lock:
            if len(self.queue) >= self.max_queue_size:
                raise ValueError(f"큐가 가득 찼습니다. 최대 크기: {self.max_queue_size}")
            
            # 작업 생성
            job_id = str(uuid.uuid4())
            job = BatchJob(
                job_id=job_id,
                status=BatchStatus.PENDING,
                total_samples=len(features_batch),
                created_at=datetime.now().isoformat()
            )
            
            # 큐에 추가
            self.queue.append({
                "job_id": job_id,
                "features_batch": features_batch
            })
            self.jobs[job_id] = job
            
            logger.info(f"배치 작업 추가: job_id={job_id}, samples={len(features_batch)}")
            return job_id
    
    def get_job(self, job_id: str) -> Optional[BatchJob]:
        """작업 정보 조회"""
        return self.jobs.get(job_id)
    
    def get_pending_jobs(self) -> List[Dict[str, Any]]:
        """대기 중인 작업 목록 조회"""
        with self.lock:
            return [
                {"job_id": item["job_id"], "samples": len(item["features_batch"])}
                for item in self.queue
            ]
    
    async def process_next_job(self, service: ModelServingService):
        """
        다음 작업 처리
        
        Args:
            service: 모델 서빙 서비스
        """
        with self.lock:
            if not self.queue:
                return
            
            if self.processing:
                logger.debug("이미 처리 중인 작업이 있습니다.")
                return
            
            self.processing = True
            job_data = self.queue.popleft()
        
        job_id = job_data["job_id"]
        features_batch = job_data["features_batch"]
        
        try:
            # 작업 상태 업데이트
            job = self.jobs[job_id]
            job.status = BatchStatus.PROCESSING
            job.started_at = datetime.now().isoformat()
            
            logger.info(f"배치 작업 처리 시작: job_id={job_id}, samples={len(features_batch)}")
            
            # 배치 예측 수행
            results = await service.predict_batch(
                batch_features=features_batch,
                return_probabilities=True
            )
            
            # 작업 완료
            job.status = BatchStatus.COMPLETED
            job.processed_samples = len(results)
            job.completed_at = datetime.now().isoformat()
            job.results = results
            
            logger.info(f"배치 작업 완료: job_id={job_id}, samples={len(results)}")
            
        except Exception as e:
            logger.error(f"배치 작업 실패: job_id={job_id}, error={e}", exc_info=True)
            
            # 작업 실패 처리
            job = self.jobs[job_id]
            job.status = BatchStatus.FAILED
            job.error = str(e)
            job.completed_at = datetime.now().isoformat()
        
        finally:
            self.processing = False
    
    async def process_all_jobs(self, service: ModelServingService):
        """
        모든 대기 중인 작업 처리
        
        Args:
            service: 모델 서빙 서비스
        """
        while True:
            with self.lock:
                if not self.queue:
                    break
            
            await self.process_next_job(service)
            await asyncio.sleep(0.1)  # 짧은 대기
    
    def get_statistics(self) -> Dict[str, Any]:
        """큐 통계 조회"""
        with self.lock:
            pending_count = len([j for j in self.jobs.values() if j.status == BatchStatus.PENDING])
            processing_count = len([j for j in self.jobs.values() if j.status == BatchStatus.PROCESSING])
            completed_count = len([j for j in self.jobs.values() if j.status == BatchStatus.COMPLETED])
            failed_count = len([j for j in self.jobs.values() if j.status == BatchStatus.FAILED])
            
            return {
                "total_jobs": len(self.jobs),
                "pending": pending_count,
                "processing": processing_count,
                "completed": completed_count,
                "failed": failed_count,
                "queue_size": len(self.queue),
                "max_queue_size": self.max_queue_size
            }
    
    def clear_completed_jobs(self, older_than_minutes: int = 60):
        """
        완료된 작업 정리
        
        Args:
            older_than_minutes: 이 시간보다 오래된 작업만 삭제 (분)
        """
        now = datetime.now()
        with self.lock:
            jobs_to_remove = []
            
            for job_id, job in self.jobs.items():
                if job.status in [BatchStatus.COMPLETED, BatchStatus.FAILED]:
                    if job.completed_at:
                        completed_time = datetime.fromisoformat(job.completed_at)
                        elapsed = (now - completed_time).total_seconds() / 60
                        
                        if elapsed > older_than_minutes:
                            jobs_to_remove.append(job_id)
            
            for job_id in jobs_to_remove:
                del self.jobs[job_id]
            
            if jobs_to_remove:
                logger.info(f"완료된 작업 정리: {len(jobs_to_remove)}건 삭제")


# 싱글톤 인스턴스
_batch_queue_instance: Optional[BatchQueue] = None


def get_batch_queue() -> BatchQueue:
    """배치 큐 싱글톤 인스턴스 반환"""
    global _batch_queue_instance
    
    if _batch_queue_instance is None:
        _batch_queue_instance = BatchQueue(max_queue_size=100)
    
    return _batch_queue_instance
