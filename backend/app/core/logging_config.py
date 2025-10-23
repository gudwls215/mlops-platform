"""
Production Logging Configuration
프로덕션 환경용 로깅 설정
"""
import logging
import logging.handlers
import json
import sys
from datetime import datetime
from typing import Any, Dict
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """JSON 형식 로그 포맷터"""
    
    def format(self, record: logging.LogRecord) -> str:
        """로그 레코드를 JSON으로 포맷팅"""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 예외 정보 추가
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # 추가 필드
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        
        if hasattr(record, "duration"):
            log_data["duration_ms"] = record.duration
        
        return json.dumps(log_data, ensure_ascii=False)


def setup_production_logging(
    log_level: str = "INFO",
    log_file: str = "/var/log/mlops/app.log",
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 10
):
    """프로덕션 로깅 설정"""
    
    # 로그 레벨 설정
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # 기존 핸들러 제거
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # JSON 포맷터
    json_formatter = JSONFormatter()
    
    # 파일 핸들러 (로테이션)
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8"
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(json_formatter)
    root_logger.addHandler(file_handler)
    
    # 콘솔 핸들러 (구조화된 로그)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(json_formatter)
    root_logger.addHandler(console_handler)
    
    # 에러 전용 파일 핸들러
    error_log = log_file.replace(".log", "_error.log")
    error_handler = logging.handlers.RotatingFileHandler(
        error_log,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(json_formatter)
    root_logger.addHandler(error_handler)
    
    # 외부 라이브러리 로그 레벨 조정
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    logging.info(f"Production logging configured: level={log_level}, file={log_file}")


class RequestLogger:
    """요청 로깅 헬퍼"""
    
    @staticmethod
    def log_request(
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        request_id: str = None,
        user_id: str = None
    ):
        """API 요청 로깅"""
        logger = logging.getLogger("api.request")
        
        extra = {
            "request_id": request_id,
            "user_id": user_id,
            "duration": duration_ms
        }
        
        level = logging.INFO
        if status_code >= 500:
            level = logging.ERROR
        elif status_code >= 400:
            level = logging.WARNING
        
        logger.log(
            level,
            f"{method} {path} - {status_code} ({duration_ms:.2f}ms)",
            extra=extra
        )
    
    @staticmethod
    def log_error(
        error: Exception,
        context: Dict[str, Any] = None,
        request_id: str = None
    ):
        """에러 로깅"""
        logger = logging.getLogger("api.error")
        
        extra = {
            "request_id": request_id,
            "error_type": type(error).__name__,
            "context": context or {}
        }
        
        logger.error(
            f"Error occurred: {str(error)}",
            exc_info=True,
            extra=extra
        )


def get_logger(name: str) -> logging.Logger:
    """이름으로 로거 가져오기"""
    return logging.getLogger(name)
