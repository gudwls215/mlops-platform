"""
Usage Monitoring Middleware
API 사용량을 자동으로 모니터링하는 미들웨어
"""
import time
import sys
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.usage_log import UsageLog


class UsageMonitoringMiddleware(BaseHTTPMiddleware):
    """API 사용량 모니터링 미들웨어"""
    
    async def dispatch(self, request: Request, call_next):
        # 시작 시간 기록
        start_time = time.time()
        
        # 요청 정보 수집
        endpoint = str(request.url.path)
        method = request.method
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")
        
        # 요청 크기 추정
        request_size = int(request.headers.get("content-length", 0))
        
        # 응답 처리
        response = None
        error_message = None
        is_error = False
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            
            # 에러 여부 확인
            if status_code >= 400:
                is_error = True
                
        except Exception as e:
            status_code = 500
            is_error = True
            error_message = str(e)
            # 에러 발생 시 기본 응답 생성
            from fastapi.responses import JSONResponse
            response = JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )
        
        # 응답 시간 계산 (밀리초)
        response_time = (time.time() - start_time) * 1000
        
        # 응답 크기 추정
        response_size = 0
        if response and hasattr(response, 'headers'):
            response_size = int(response.headers.get("content-length", 0))
        
        # 로그 저장 (비동기로 처리하지 않음 - 간단한 구현)
        try:
            db = SessionLocal()
            usage_log = UsageLog(
                endpoint=endpoint,
                method=method,
                client_ip=client_ip,
                user_agent=user_agent,
                status_code=status_code,
                response_time=response_time,
                is_error=is_error,
                error_message=error_message,
                request_size=request_size,
                response_size=response_size
            )
            db.add(usage_log)
            db.commit()
            db.close()
        except Exception as log_error:
            # 로그 저장 실패는 무시 (서비스에 영향 없도록)
            print(f"Failed to save usage log: {log_error}", file=sys.stderr)
        
        return response
