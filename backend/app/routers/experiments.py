"""
실험 관리 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import pandas as pd

from app.services.experiment_tracking import ExperimentTracker

router = APIRouter(prefix="/api/experiments", tags=["experiments"])
tracker = ExperimentTracker()


# Request/Response 스키마
class CreateExperimentRequest(BaseModel):
    name: str
    tags: Optional[Dict[str, str]] = None
    artifact_location: Optional[str] = None


class StartRunRequest(BaseModel):
    experiment_id: str
    run_name: Optional[str] = None
    tags: Optional[Dict[str, str]] = None


class LogParamsRequest(BaseModel):
    run_id: str
    params: Dict[str, Any]


class LogMetricsRequest(BaseModel):
    run_id: str
    metrics: Dict[str, float]
    step: Optional[int] = None


class RegisterModelRequest(BaseModel):
    run_id: str
    model_name: str
    model_path: str = "model"


class TransitionModelStageRequest(BaseModel):
    model_name: str
    version: str
    stage: str
    archive_existing_versions: bool = False


class CompareRunsRequest(BaseModel):
    run_ids: List[str]
    metric_keys: Optional[List[str]] = None


# 실험 관리 엔드포인트
@router.post("/create")
async def create_experiment(request: CreateExperimentRequest):
    """
    새로운 실험 생성
    """
    try:
        experiment_id = tracker.create_experiment(
            name=request.name,
            tags=request.tags,
            artifact_location=request.artifact_location
        )
        return {
            "success": True,
            "data": {
                "experiment_id": experiment_id,
                "message": "Experiment created successfully"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{experiment_id}")
async def get_experiment(experiment_id: str):
    """
    실험 정보 조회
    """
    try:
        experiment = tracker.get_experiment(experiment_id)
        return {
            "success": True,
            "data": experiment
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/")
async def list_experiments(
    view_type: str = Query("ACTIVE_ONLY", description="ACTIVE_ONLY, DELETED_ONLY, ALL")
):
    """
    모든 실험 목록 조회
    """
    try:
        experiments = tracker.list_experiments(view_type=view_type)
        return {
            "success": True,
            "data": experiments,
            "count": len(experiments)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{experiment_id}")
async def delete_experiment(experiment_id: str):
    """
    실험 삭제
    """
    try:
        tracker.delete_experiment(experiment_id)
        return {
            "success": True,
            "message": "Experiment deleted successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Run 관리 엔드포인트
@router.post("/runs/start")
async def start_run(request: StartRunRequest):
    """
    새로운 실험 run 시작
    """
    try:
        run_id = tracker.start_run(
            experiment_id=request.experiment_id,
            run_name=request.run_name,
            tags=request.tags
        )
        return {
            "success": True,
            "data": {
                "run_id": run_id,
                "message": "Run started successfully"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{run_id}")
async def get_run(run_id: str):
    """
    Run 정보 조회
    """
    try:
        run = tracker.get_run(run_id)
        return {
            "success": True,
            "data": run
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/runs/search")
async def search_runs(
    experiment_ids: List[str],
    filter_string: str = "",
    order_by: Optional[List[str]] = None,
    max_results: int = 100
):
    """
    조건에 맞는 runs 검색
    
    예시 filter_string:
    - "metrics.f1_score > 0.8"
    - "params.model_type = 'LogisticRegression'"
    - "tags.mlflow.runName = 'my-run'"
    """
    try:
        runs = tracker.search_runs(
            experiment_ids=experiment_ids,
            filter_string=filter_string,
            order_by=order_by,
            max_results=max_results
        )
        return {
            "success": True,
            "data": runs,
            "count": len(runs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/runs/{run_id}")
async def delete_run(run_id: str):
    """
    Run 삭제
    """
    try:
        tracker.delete_run(run_id)
        return {
            "success": True,
            "message": "Run deleted successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 메트릭/파라미터 로깅 엔드포인트
@router.post("/runs/log-params")
async def log_params(request: LogParamsRequest):
    """
    하이퍼파라미터 로깅
    """
    try:
        tracker.log_params(
            run_id=request.run_id,
            params=request.params
        )
        return {
            "success": True,
            "message": "Parameters logged successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/runs/log-metrics")
async def log_metrics(request: LogMetricsRequest):
    """
    메트릭 로깅
    """
    try:
        tracker.log_metrics(
            run_id=request.run_id,
            metrics=request.metrics,
            step=request.step
        )
        return {
            "success": True,
            "message": "Metrics logged successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 실험 비교 엔드포인트
@router.post("/runs/compare")
async def compare_runs(request: CompareRunsRequest):
    """
    여러 runs 비교
    """
    try:
        comparison_df = tracker.compare_runs(
            run_ids=request.run_ids,
            metric_keys=request.metric_keys
        )
        
        # DataFrame을 JSON으로 변환
        comparison_data = comparison_df.to_dict(orient="records")
        
        return {
            "success": True,
            "data": comparison_data,
            "columns": list(comparison_df.columns)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/best/{experiment_id}")
async def get_best_run(
    experiment_id: str,
    metric_key: str = Query(..., description="메트릭 키 (예: f1_score, accuracy)"),
    ascending: bool = Query(False, description="오름차순 정렬 (True: 낮을수록 좋음)")
):
    """
    최고 성능 run 찾기
    """
    try:
        best_run = tracker.get_best_run(
            experiment_id=experiment_id,
            metric_key=metric_key,
            ascending=ascending
        )
        
        if not best_run:
            raise HTTPException(
                status_code=404, 
                detail=f"No runs found for experiment {experiment_id}"
            )
        
        return {
            "success": True,
            "data": best_run
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 모델 레지스트리 엔드포인트
@router.post("/models/register")
async def register_model(request: RegisterModelRequest):
    """
    모델을 레지스트리에 등록
    """
    try:
        model_version = tracker.register_model(
            run_id=request.run_id,
            model_name=request.model_name,
            model_path=request.model_path
        )
        return {
            "success": True,
            "data": {
                "model_name": request.model_name,
                "version": model_version,
                "message": "Model registered successfully"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/transition-stage")
async def transition_model_stage(request: TransitionModelStageRequest):
    """
    모델 스테이지 변경 (Staging, Production 등)
    """
    try:
        tracker.transition_model_stage(
            model_name=request.model_name,
            version=request.version,
            stage=request.stage,
            archive_existing_versions=request.archive_existing_versions
        )
        return {
            "success": True,
            "message": f"Model {request.model_name} v{request.version} transitioned to {request.stage}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/{model_name}")
async def get_model_version(
    model_name: str,
    version: Optional[str] = Query(None, description="모델 버전"),
    stage: Optional[str] = Query(None, description="모델 스테이지 (Production, Staging)")
):
    """
    모델 버전 정보 조회
    """
    try:
        if not version and not stage:
            raise HTTPException(
                status_code=400, 
                detail="Either version or stage parameter is required"
            )
        
        model_info = tracker.get_model_version(
            model_name=model_name,
            version=version,
            stage=stage
        )
        return {
            "success": True,
            "data": model_info
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 통계 및 대시보드 엔드포인트
@router.get("/stats/{experiment_id}")
async def get_experiment_stats(experiment_id: str):
    """
    실험 통계 조회
    """
    try:
        # 모든 runs 조회
        runs = tracker.search_runs(
            experiment_ids=[experiment_id],
            max_results=1000
        )
        
        if not runs:
            return {
                "success": True,
                "data": {
                    "experiment_id": experiment_id,
                    "total_runs": 0,
                    "completed_runs": 0,
                    "failed_runs": 0,
                    "running_runs": 0
                }
            }
        
        # 상태별 집계
        status_counts = {}
        for run in runs:
            status = run.get("status", "UNKNOWN")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # 메트릭 통계 (가능한 경우)
        all_metrics = {}
        for run in runs:
            for key, value in run.get("metrics", {}).items():
                if key not in all_metrics:
                    all_metrics[key] = []
                all_metrics[key].append(value)
        
        metric_stats = {}
        for key, values in all_metrics.items():
            metric_stats[key] = {
                "min": min(values),
                "max": max(values),
                "mean": sum(values) / len(values),
                "count": len(values)
            }
        
        return {
            "success": True,
            "data": {
                "experiment_id": experiment_id,
                "total_runs": len(runs),
                "status_counts": status_counts,
                "metric_stats": metric_stats
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
