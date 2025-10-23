from pydantic_settings import BaseSettings
from typing import Optional
from urllib.parse import quote_plus

class Settings(BaseSettings):
    # 데이터베이스 설정
    DATABASE_HOST: str = "114.202.2.226"
    DATABASE_PORT: int = 5433
    DATABASE_NAME: str = "postgres"
    DATABASE_SCHEMA: str = "mlops"
    DATABASE_USER: str = "postgres"
    DATABASE_PASSWORD: str = "xlxldpa!@#"
    
    # OpenAI API 설정
    OPENAI_API_KEY: Optional[str] = None
    
    # JWT 설정
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 기타 설정
    DEBUG: bool = True
    PROJECT_NAME: str = "MLOps Platform"
    
    @property
    def database_url(self) -> str:
        # 비밀번호를 URL 인코딩하여 특수문자 처리
        encoded_password = quote_plus(self.DATABASE_PASSWORD)
        return f"postgresql://{self.DATABASE_USER}:{encoded_password}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # 추가 필드 무시

settings = Settings()