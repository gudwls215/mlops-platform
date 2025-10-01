import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
import hashlib

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/ttm/tensorflow-jupyter/jupyterNotebook/khj/mlops-platform/backend/logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def get_logger(name: str) -> logging.Logger:
    """로거 인스턴스 반환"""
    return logging.getLogger(name)

def safe_json_loads(json_str: Optional[str], default: Any = None) -> Any:
    """안전한 JSON 파싱"""
    if not json_str:
        return default
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        logger.warning(f"Failed to parse JSON: {json_str}")
        return default

def safe_json_dumps(data: Any, default: str = "{}") -> str:
    """안전한 JSON 직렬화"""
    try:
        return json.dumps(data, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        logger.warning(f"Failed to serialize to JSON: {data}")
        return default

def create_hash(text: str) -> str:
    """텍스트의 MD5 해시 생성"""
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def format_datetime(dt: Optional[datetime]) -> Optional[str]:
    """datetime을 문자열로 포맷"""
    if dt:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return None

def clean_text(text: str) -> str:
    """텍스트 정제"""
    if not text:
        return ""
    # 기본적인 텍스트 정제
    text = text.strip()
    text = ' '.join(text.split())  # 연속된 공백 제거
    return text

def validate_resume_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """이력서 데이터 검증 및 정제"""
    validated_data = {}
    
    # 필수 필드
    if 'title' in data and data['title']:
        validated_data['title'] = clean_text(data['title'])
    
    # 선택 필드들
    optional_fields = ['content', 'skills', 'experience', 'education']
    for field in optional_fields:
        if field in data and data[field]:
            if isinstance(data[field], str):
                validated_data[field] = clean_text(data[field])
            else:
                validated_data[field] = safe_json_dumps(data[field])
    
    return validated_data

def validate_job_posting_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """채용공고 데이터 검증 및 정제"""
    validated_data = {}
    
    # 필수 필드
    required_fields = ['title', 'company']
    for field in required_fields:
        if field in data and data[field]:
            validated_data[field] = clean_text(data[field])
    
    # 선택 필드들
    optional_fields = ['description', 'requirements', 'location', 'employment_type', 'experience_level']
    for field in optional_fields:
        if field in data and data[field]:
            validated_data[field] = clean_text(data[field])
    
    # 숫자 필드들
    numeric_fields = ['salary_min', 'salary_max']
    for field in numeric_fields:
        if field in data and data[field] is not None:
            try:
                validated_data[field] = int(data[field])
            except (ValueError, TypeError):
                logger.warning(f"Invalid numeric value for {field}: {data[field]}")
    
    return validated_data