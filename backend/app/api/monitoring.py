"""
Usage Monitoring API
사용량 통계 및 모니터링 API
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, Integer
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.core.database import get_db
from app.models.usage_log import UsageLog


router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])


# Pydantic 모델
class UsageStats(BaseModel):
    """사용량 통계"""
    total_requests: int
    total_errors: int
    error_rate: float
    avg_response_time: float
    total_request_size: int
    total_response_size: int
    requests_by_method: dict
    requests_by_status: dict
    top_endpoints: List[dict]


class EndpointStats(BaseModel):
    """엔드포인트별 통계"""
    endpoint: str
    method: str
    total_requests: int
    error_count: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float


class RecentLog(BaseModel):
    """최근 로그"""
    id: int
    endpoint: str
    method: str
    status_code: int
    response_time: float
    is_error: bool
    error_message: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


@router.get("/stats", response_model=UsageStats)
async def get_usage_stats(
    hours: int = Query(24, description="조회할 시간 범위 (시간)"),
    db: Session = Depends(get_db)
):
    """
    사용량 통계 조회
    
    - **hours**: 조회할 시간 범위 (기본 24시간)
    """
    # 시간 범위 계산
    since = datetime.utcnow() - timedelta(hours=hours)
    
    # 전체 통계
    logs = db.query(UsageLog).filter(UsageLog.created_at >= since).all()
    
    if not logs:
        return UsageStats(
            total_requests=0,
            total_errors=0,
            error_rate=0.0,
            avg_response_time=0.0,
            total_request_size=0,
            total_response_size=0,
            requests_by_method={},
            requests_by_status={},
            top_endpoints=[]
        )
    
    total_requests = len(logs)
    total_errors = sum(1 for log in logs if log.is_error)
    error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0.0
    avg_response_time = sum(log.response_time for log in logs) / total_requests
    total_request_size = sum(log.request_size or 0 for log in logs)
    total_response_size = sum(log.response_size or 0 for log in logs)
    
    # 메소드별 통계
    requests_by_method = {}
    for log in logs:
        requests_by_method[log.method] = requests_by_method.get(log.method, 0) + 1
    
    # 상태코드별 통계
    requests_by_status = {}
    for log in logs:
        status_key = f"{log.status_code // 100}xx"
        requests_by_status[status_key] = requests_by_status.get(status_key, 0) + 1
    
    # 상위 엔드포인트
    endpoint_counts = {}
    for log in logs:
        key = f"{log.method} {log.endpoint}"
        endpoint_counts[key] = endpoint_counts.get(key, 0) + 1
    
    top_endpoints = [
        {"endpoint": k, "count": v}
        for k, v in sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    ]
    
    return UsageStats(
        total_requests=total_requests,
        total_errors=total_errors,
        error_rate=round(error_rate, 2),
        avg_response_time=round(avg_response_time, 2),
        total_request_size=total_request_size,
        total_response_size=total_response_size,
        requests_by_method=requests_by_method,
        requests_by_status=requests_by_status,
        top_endpoints=top_endpoints
    )


@router.get("/endpoints", response_model=List[EndpointStats])
async def get_endpoint_stats(
    hours: int = Query(24, description="조회할 시간 범위 (시간)"),
    db: Session = Depends(get_db)
):
    """
    엔드포인트별 통계 조회
    
    - **hours**: 조회할 시간 범위 (기본 24시간)
    """
    since = datetime.utcnow() - timedelta(hours=hours)
    
    # 엔드포인트별 통계 쿼리
    stats = db.query(
        UsageLog.endpoint,
        UsageLog.method,
        func.count(UsageLog.id).label('total_requests'),
        func.sum(func.cast(UsageLog.is_error, Integer)).label('error_count'),
        func.avg(UsageLog.response_time).label('avg_response_time'),
        func.min(UsageLog.response_time).label('min_response_time'),
        func.max(UsageLog.response_time).label('max_response_time')
    ).filter(
        UsageLog.created_at >= since
    ).group_by(
        UsageLog.endpoint, UsageLog.method
    ).order_by(
        func.count(UsageLog.id).desc()
    ).all()
    
    return [
        EndpointStats(
            endpoint=stat.endpoint,
            method=stat.method,
            total_requests=stat.total_requests,
            error_count=stat.error_count or 0,
            avg_response_time=round(stat.avg_response_time, 2),
            min_response_time=round(stat.min_response_time, 2),
            max_response_time=round(stat.max_response_time, 2)
        )
        for stat in stats
    ]


@router.get("/errors", response_model=List[RecentLog])
async def get_recent_errors(
    limit: int = Query(50, description="조회할 에러 수"),
    db: Session = Depends(get_db)
):
    """
    최근 에러 로그 조회
    
    - **limit**: 조회할 에러 수 (기본 50개)
    """
    errors = db.query(UsageLog).filter(
        UsageLog.is_error == True
    ).order_by(
        UsageLog.created_at.desc()
    ).limit(limit).all()
    
    return errors


@router.get("/slow-requests", response_model=List[RecentLog])
async def get_slow_requests(
    threshold: float = Query(1000.0, description="느린 요청 기준 (ms)"),
    limit: int = Query(50, description="조회할 요청 수"),
    db: Session = Depends(get_db)
):
    """
    느린 요청 조회
    
    - **threshold**: 느린 요청으로 판단할 응답 시간 (밀리초, 기본 1000ms)
    - **limit**: 조회할 요청 수 (기본 50개)
    """
    slow_requests = db.query(UsageLog).filter(
        UsageLog.response_time >= threshold
    ).order_by(
        UsageLog.response_time.desc()
    ).limit(limit).all()
    
    return slow_requests


@router.get("/recent", response_model=List[RecentLog])
async def get_recent_logs(
    limit: int = Query(100, description="조회할 로그 수"),
    db: Session = Depends(get_db)
):
    """
    최근 로그 조회
    
    - **limit**: 조회할 로그 수 (기본 100개)
    """
    logs = db.query(UsageLog).order_by(
        UsageLog.created_at.desc()
    ).limit(limit).all()
    
    return logs
