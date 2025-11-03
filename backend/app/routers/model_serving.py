"""
모델 서빙 API 라우터

실시간 및 배치 예측 엔드포인트 제공
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from app.services.model_serving import (
    ModelServingService,
    get_model_service,
    PredictionInput,
    BatchPredictionInput,
    PredictionOutput,
    ModelInfo
)
from app.services.batch_queue import (
    BatchQueue,
    get_batch_queue,
    BatchJob,
    BatchStatus
)


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/model", tags=["Model Serving"])


@router.get("/health", summary="모델 서빙 헬스 체크")
async def health_check(
    service: ModelServingService = Depends(get_model_service)
) -> Dict[str, Any]:
    """
    모델 서빙 서비스 헬스 체크
    
    Returns:
        헬스 상태 정보
    """
    try:
        health_status = await service.health_check()
        return {
            "success": True,
            "data": health_status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"헬스 체크 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/info", response_model=Dict[str, Any], summary="모델 정보 조회")
async def get_model_info(
    service: ModelServingService = Depends(get_model_service)
) -> Dict[str, Any]:
    """
    현재 로드된 모델 정보 조회
    
    Returns:
        모델 정보 (이름, 버전, 타입, 메타데이터 등)
    """
    try:
        model_info = service.get_model_info()
        return {
            "success": True,
            "data": model_info.dict(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"모델 정보 조회 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict", response_model=Dict[str, Any], summary="실시간 예측")
async def predict(
    input_data: PredictionInput,
    return_probabilities: bool = True,
    service: ModelServingService = Depends(get_model_service)
) -> Dict[str, Any]:
    """
    단일 샘플에 대한 실시간 예측
    
    Args:
        input_data: 예측 입력 데이터
        return_probabilities: 확률 반환 여부
        
    Returns:
        예측 결과 (예측값, 확률, 모델 버전 등)
        
    Example:
        ```json
        {
            "features": [0.54, 0.72, 0.15, 0.88, ...],
            "feature_names": ["similarity", "experience", "education", "skills"]
        }
        ```
    """
    try:
        logger.info(f"예측 요청: features_len={len(input_data.features)}")
        
        # 입력 검증
        if not input_data.features:
            raise HTTPException(status_code=400, detail="features는 비어있을 수 없습니다.")
        
        # 예측 수행
        result = await service.predict(
            features=input_data.features,
            return_probabilities=return_probabilities
        )
        
        return {
            "success": True,
            "data": result.dict(),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"예측 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"예측 중 오류 발생: {str(e)}")


@router.post("/predict/batch", response_model=Dict[str, Any], summary="배치 예측")
async def predict_batch(
    input_data: BatchPredictionInput,
    return_probabilities: bool = True,
    service: ModelServingService = Depends(get_model_service)
) -> Dict[str, Any]:
    """
    여러 샘플에 대한 배치 예측
    
    Args:
        input_data: 예측 입력 배치
        return_probabilities: 확률 반환 여부
        
    Returns:
        예측 결과 리스트
        
    Example:
        ```json
        {
            "batch": [
                {"features": [0.54, 0.72, 0.15, 0.88]},
                {"features": [0.32, 0.45, 0.89, 0.12]},
                {"features": [0.78, 0.91, 0.34, 0.56]}
            ]
        }
        ```
    """
    try:
        logger.info(f"배치 예측 요청: batch_size={len(input_data.batch)}")
        
        # 입력 검증
        if not input_data.batch:
            raise HTTPException(status_code=400, detail="batch는 비어있을 수 없습니다.")
        
        if len(input_data.batch) > 1000:
            raise HTTPException(status_code=400, detail="배치 크기는 1000개를 초과할 수 없습니다.")
        
        # 특성 벡터 추출
        batch_features = [item.features for item in input_data.batch]
        
        # 배치 예측 수행
        results = await service.predict_batch(
            batch_features=batch_features,
            return_probabilities=return_probabilities
        )
        
        return {
            "success": True,
            "data": {
                "predictions": [result.dict() for result in results],
                "count": len(results)
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"배치 예측 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"배치 예측 중 오류 발생: {str(e)}")


@router.post("/reload", summary="모델 리로드")
async def reload_model(
    stage: str = "Production",
    background_tasks: BackgroundTasks = BackgroundTasks(),
    service: ModelServingService = Depends(get_model_service)
) -> Dict[str, Any]:
    """
    모델 리로드 (새 버전 적용)
    
    Args:
        stage: MLflow 모델 스테이지 (Production, Staging, None)
        
    Returns:
        리로드 결과
        
    Note:
        백그라운드에서 실행되며, 즉시 응답을 반환합니다.
    """
    try:
        logger.info(f"모델 리로드 요청: stage={stage}")
        
        # 백그라운드에서 리로드 실행
        def reload_task():
            try:
                service.reload_model(stage=stage)
                logger.info(f"모델 리로드 완료: stage={stage}")
            except Exception as e:
                logger.error(f"모델 리로드 실패: {e}", exc_info=True)
        
        background_tasks.add_task(reload_task)
        
        return {
            "success": True,
            "message": f"모델 리로드 시작: stage={stage}",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"모델 리로드 요청 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", summary="모델 성능 메트릭")
async def get_metrics(
    service: ModelServingService = Depends(get_model_service)
) -> Dict[str, Any]:
    """
    모델 성능 메트릭 조회
    
    Returns:
        모델 메트릭 (정확도, F1 스코어 등)
    """
    try:
        model_info = service.get_model_info()
        
        metrics = model_info.metadata.get('metrics', {})
        
        return {
            "success": True,
            "data": {
                "model_version": model_info.version,
                "metrics": metrics,
                "loaded_at": model_info.loaded_at
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"메트릭 조회 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ===== 배치 큐 관련 엔드포인트 =====

@router.post("/batch/submit", summary="배치 예측 작업 제출")
async def submit_batch_job(
    input_data: BatchPredictionInput,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    queue: BatchQueue = Depends(get_batch_queue),
    service: ModelServingService = Depends(get_model_service)
) -> Dict[str, Any]:
    """
    배치 예측 작업을 큐에 제출
    
    Args:
        input_data: 예측 입력 배치
        
    Returns:
        작업 ID 및 상태
        
    Note:
        - 대량 예측 요청을 비동기로 처리
        - 작업 ID로 결과 조회 가능
        - 큐가 가득 차면 에러 반환
    """
    try:
        logger.info(f"배치 작업 제출: batch_size={len(input_data.batch)}")
        
        # 입력 검증
        if not input_data.batch:
            raise HTTPException(status_code=400, detail="batch는 비어있을 수 없습니다.")
        
        if len(input_data.batch) > 10000:
            raise HTTPException(status_code=400, detail="배치 크기는 10,000개를 초과할 수 없습니다.")
        
        # 특성 벡터 추출
        batch_features = [item.features for item in input_data.batch]
        
        # 큐에 작업 추가
        job_id = queue.add_job(batch_features)
        
        # 백그라운드에서 처리
        background_tasks.add_task(queue.process_next_job, service)
        
        return {
            "success": True,
            "data": {
                "job_id": job_id,
                "status": "pending",
                "total_samples": len(batch_features),
                "message": "배치 작업이 큐에 추가되었습니다."
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        logger.error(f"배치 작업 제출 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/batch/{job_id}", summary="배치 작업 상태 조회")
async def get_batch_job_status(
    job_id: str,
    queue: BatchQueue = Depends(get_batch_queue)
) -> Dict[str, Any]:
    """
    배치 작업 상태 및 결과 조회
    
    Args:
        job_id: 작업 ID
        
    Returns:
        작업 상태 및 결과 (완료된 경우)
    """
    try:
        job = queue.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
        
        return {
            "success": True,
            "data": job.dict(),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"작업 상태 조회 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/batch/queue/stats", summary="배치 큐 통계")
async def get_batch_queue_stats(
    queue: BatchQueue = Depends(get_batch_queue)
) -> Dict[str, Any]:
    """
    배치 큐 통계 조회
    
    Returns:
        큐 상태 및 통계
    """
    try:
        stats = queue.get_statistics()
        
        return {
            "success": True,
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"큐 통계 조회 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch/queue/process", summary="큐의 모든 작업 처리")
async def process_all_batch_jobs(
    background_tasks: BackgroundTasks = BackgroundTasks(),
    queue: BatchQueue = Depends(get_batch_queue),
    service: ModelServingService = Depends(get_model_service)
) -> Dict[str, Any]:
    """
    큐에 대기 중인 모든 작업을 처리
    
    Returns:
        처리 시작 메시지
    """
    try:
        pending_jobs = queue.get_pending_jobs()
        
        if not pending_jobs:
            return {
                "success": True,
                "message": "처리할 작업이 없습니다.",
                "timestamp": datetime.now().isoformat()
            }
        
        # 백그라운드에서 모든 작업 처리
        background_tasks.add_task(queue.process_all_jobs, service)
        
        return {
            "success": True,
            "message": f"{len(pending_jobs)}개 작업 처리를 시작합니다.",
            "pending_jobs": pending_jobs,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"큐 처리 시작 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/batch/queue/clear", summary="완료된 작업 정리")
async def clear_completed_jobs(
    older_than_minutes: int = 60,
    queue: BatchQueue = Depends(get_batch_queue)
) -> Dict[str, Any]:
    """
    완료된 작업 정리
    
    Args:
        older_than_minutes: 이 시간보다 오래된 작업만 삭제 (분, 기본값: 60)
        
    Returns:
        정리 결과
    """
    try:
        queue.clear_completed_jobs(older_than_minutes=older_than_minutes)
        
        return {
            "success": True,
            "message": f"{older_than_minutes}분 이상 된 완료 작업을 정리했습니다.",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"작업 정리 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

