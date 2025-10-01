from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # 데이터베이스 설정
    DATABASE_HOST: str = "114.202.2.226"
    DATABASE_PORT: int = 5433
    DATABASE_NAME: str = "postgres"
    DATABASE_SCHEMA: str = "mlops"
    DATABASE_USER: str = "postgres"
    DATABASE_PASSWORD: str = ""
    
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
        return f"postgresql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
    
    class Config:
        env_file = ".env"

settings = Settings()