"""
Production Configuration
프로덕션 환경에 최적화된 설정
"""
import os
from typing import List
from pydantic_settings import BaseSettings
from urllib.parse import quote_plus


class ProductionSettings(BaseSettings):
    """프로덕션 환경 설정"""
    
    # Environment
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    
    # Application
    APP_NAME: str = "MLOps Platform"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    ALLOWED_ORIGINS: str = ""
    ALLOWED_HOSTS: str = ""
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """CORS 허용 오리진 리스트"""
        if not self.ALLOWED_ORIGINS:
            return []
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    @property
    def allowed_hosts_list(self) -> List[str]:
        """허용된 호스트 리스트"""
        if not self.ALLOWED_HOSTS:
            return []
        return [host.strip() for host in self.ALLOWED_HOSTS.split(",")]
    
    # Database
    DATABASE_HOST: str
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str
    DATABASE_USER: str
    DATABASE_PASSWORD: str
    SCHEMA: str = "mlops"
    
    # Database Pool
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    
    @property
    def database_url(self) -> str:
        """데이터베이스 연결 URL (특수문자 인코딩 적용)"""
        encoded_password = quote_plus(self.DATABASE_PASSWORD)
        return (
            f"postgresql://{self.DATABASE_USER}:{encoded_password}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        )
    
    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_MAX_TOKENS: int = 2000
    OPENAI_RATE_LIMIT_REQUESTS: int = 100
    OPENAI_RATE_LIMIT_PERIOD: int = 60
    
    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    
    @property
    def redis_url(self) -> str:
        """Redis 연결 URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # Cache
    CACHE_TTL_SHORT: int = 300
    CACHE_TTL_MEDIUM: int = 1800
    CACHE_TTL_LONG: int = 3600
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: str = "/var/log/mlops/app.log"
    LOG_MAX_BYTES: int = 10485760
    LOG_BACKUP_COUNT: int = 10
    
    # Security
    SECURE_SSL_REDIRECT: bool = True
    SESSION_COOKIE_SECURE: bool = True
    CSRF_COOKIE_SECURE: bool = True
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    
    # Performance
    MAX_REQUEST_SIZE: int = 10485760
    REQUEST_TIMEOUT: int = 30
    WORKER_CONNECTIONS: int = 1000
    
    # File Upload
    UPLOAD_DIR: str = "/var/mlops/uploads"
    MAX_UPLOAD_SIZE: int = 5242880
    ALLOWED_EXTENSIONS: str = "mp3,wav,pdf,doc,docx"
    
    @property
    def allowed_extensions_list(self) -> List[str]:
        """허용된 파일 확장자 리스트"""
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(",")]
    
    # Backup
    BACKUP_ENABLED: bool = True
    BACKUP_DIR: str = "/var/mlops/backups"
    BACKUP_RETENTION_DAYS: int = 30
    
    # Email
    SMTP_ENABLED: bool = False
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    
    # Sentry
    SENTRY_ENABLED: bool = False
    SENTRY_DSN: str = ""
    
    # Feature Flags
    FEATURE_VOICE_INPUT: bool = True
    FEATURE_BATCH_PROCESSING: bool = True
    FEATURE_ADVANCED_MATCHING: bool = True
    FEATURE_ANALYTICS: bool = True
    
    class Config:
        env_file = ".env.production"
        case_sensitive = True


# 싱글톤 인스턴스
_production_settings = None


def get_production_settings() -> ProductionSettings:
    """프로덕션 설정 인스턴스 반환"""
    global _production_settings
    if _production_settings is None:
        _production_settings = ProductionSettings()
    return _production_settings


def validate_production_settings():
    """프로덕션 설정 검증"""
    settings = get_production_settings()
    
    errors = []
    
    # 필수 설정 검증
    if settings.SECRET_KEY == "CHANGE_THIS_TO_RANDOM_STRING_IN_PRODUCTION_MIN_32_CHARS":
        errors.append("SECRET_KEY must be changed from default value")
    
    if len(settings.SECRET_KEY) < 32:
        errors.append("SECRET_KEY must be at least 32 characters long")
    
    if not settings.ALLOWED_ORIGINS:
        errors.append("ALLOWED_ORIGINS must be set in production")
    
    if not settings.DATABASE_HOST:
        errors.append("DATABASE_HOST must be set")
    
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY.startswith("your-"):
        errors.append("Valid OPENAI_API_KEY must be set")
    
    # 보안 설정 검증
    if not settings.SECURE_SSL_REDIRECT:
        errors.append("SECURE_SSL_REDIRECT should be True in production")
    
    if settings.DEBUG:
        errors.append("DEBUG must be False in production")
    
    if errors:
        error_msg = "\n".join([f"  - {error}" for error in errors])
        raise ValueError(f"Production configuration validation failed:\n{error_msg}")
    
    return True
