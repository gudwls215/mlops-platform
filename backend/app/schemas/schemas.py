from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Resume schemas
class ResumeBase(BaseModel):
    title: str = Field(..., description="이력서 제목")
    content: Optional[str] = Field(None, description="이력서 내용")
    skills: Optional[str] = Field(None, description="기술 스택 (JSON)")
    experience: Optional[str] = Field(None, description="경력 사항 (JSON)")
    education: Optional[str] = Field(None, description="학력 사항 (JSON)")

class ResumeCreate(ResumeBase):
    user_id: int = Field(..., description="사용자 ID")

class ResumeUpdate(ResumeBase):
    title: Optional[str] = None

class ResumeResponse(ResumeBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: bool

    class Config:
        from_attributes = True

# Job Posting schemas
class JobPostingBase(BaseModel):
    title: str = Field(..., description="채용공고 제목")
    company: str = Field(..., description="회사명")
    description: Optional[str] = Field(None, description="채용공고 설명")
    requirements: Optional[str] = Field(None, description="지원 요건")
    location: Optional[str] = Field(None, description="근무 지역")
    salary_min: Optional[int] = Field(None, description="최소 연봉")
    salary_max: Optional[int] = Field(None, description="최대 연봉")
    employment_type: Optional[str] = Field(None, description="고용 형태")
    experience_level: Optional[str] = Field(None, description="경력 수준")

class JobPostingResponse(JobPostingBase):
    id: int
    source_url: Optional[str]
    scraped_at: datetime
    is_active: bool

    class Config:
        from_attributes = True

# Cover Letter schemas
class CoverLetterBase(BaseModel):
    content: str = Field(..., description="자기소개서 내용")

class CoverLetterCreate(CoverLetterBase):
    resume_id: int = Field(..., description="이력서 ID")
    job_posting_id: int = Field(..., description="채용공고 ID")

class CoverLetterResponse(CoverLetterBase):
    id: int
    resume_id: int
    job_posting_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# Prediction schemas
class PredictionRequest(BaseModel):
    resume_id: int = Field(..., description="이력서 ID")
    job_posting_id: int = Field(..., description="채용공고 ID")

class PredictionResponse(BaseModel):
    prediction_score: float = Field(..., description="예측 점수")
    model_version: str = Field(..., description="모델 버전")
    created_at: datetime

    class Config:
        from_attributes = True