"""
Feedback API Router
사용자 피드백 수집 API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

from app.core.database import get_db
from app.models.feedback import Feedback, FeedbackType, FeedbackSentiment

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


# Pydantic 모델
class FeedbackCreate(BaseModel):
    """피드백 생성 요청"""
    feedback_type: FeedbackType
    sentiment: Optional[FeedbackSentiment] = None
    rating: Optional[int] = Field(None, ge=1, le=5, description="1-5 별점")
    title: Optional[str] = Field(None, max_length=200)
    content: str = Field(..., min_length=1, max_length=5000)
    user_name: Optional[str] = Field(None, max_length=100)
    user_email: Optional[EmailStr] = None
    user_age_group: Optional[str] = Field(None, max_length=20)
    user_agent: Optional[str] = Field(None, max_length=500)
    page_url: Optional[str] = Field(None, max_length=500)
    related_resume_id: Optional[int] = None
    related_job_id: Optional[int] = None


class FeedbackResponse(BaseModel):
    """피드백 응답"""
    id: int
    feedback_type: FeedbackType
    sentiment: Optional[FeedbackSentiment]
    rating: Optional[int]
    title: Optional[str]
    content: str
    user_name: Optional[str]
    user_age_group: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class FeedbackStats(BaseModel):
    """피드백 통계"""
    total_count: int
    average_rating: Optional[float]
    positive_count: int
    neutral_count: int
    negative_count: int
    by_type: dict


@router.post("/", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_feedback(
    feedback: FeedbackCreate,
    db: Session = Depends(get_db)
):
    """
    피드백 제출
    
    - **feedback_type**: 피드백 유형 (resume_generation, cover_letter, job_matching, ui_ux, general)
    - **sentiment**: 감정 (positive, neutral, negative) - 선택사항
    - **rating**: 별점 1-5 - 선택사항
    - **content**: 피드백 내용 (필수)
    """
    try:
        db_feedback = Feedback(**feedback.model_dump())
        db.add(db_feedback)
        db.commit()
        db.refresh(db_feedback)
        
        return db_feedback
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"피드백 저장 중 오류 발생: {str(e)}"
        )


@router.get("/stats", response_model=FeedbackStats)
async def get_feedback_stats(
    feedback_type: Optional[FeedbackType] = None,
    db: Session = Depends(get_db)
):
    """
    피드백 통계 조회
    
    - **feedback_type**: 특정 유형의 통계만 조회 (선택사항)
    """
    try:
        query = db.query(Feedback)
        
        if feedback_type:
            query = query.filter(Feedback.feedback_type == feedback_type)
        
        feedbacks = query.all()
        
        # 통계 계산
        total_count = len(feedbacks)
        
        # 평균 평점
        ratings = [f.rating for f in feedbacks if f.rating is not None]
        average_rating = sum(ratings) / len(ratings) if ratings else None
        
        # 감정별 카운트
        positive_count = len([f for f in feedbacks if f.sentiment == FeedbackSentiment.POSITIVE])
        neutral_count = len([f for f in feedbacks if f.sentiment == FeedbackSentiment.NEUTRAL])
        negative_count = len([f for f in feedbacks if f.sentiment == FeedbackSentiment.NEGATIVE])
        
        # 유형별 카운트
        by_type = {}
        for fb_type in FeedbackType:
            count = len([f for f in feedbacks if f.feedback_type == fb_type])
            by_type[fb_type.value] = count
        
        return FeedbackStats(
            total_count=total_count,
            average_rating=round(average_rating, 2) if average_rating else None,
            positive_count=positive_count,
            neutral_count=neutral_count,
            negative_count=negative_count,
            by_type=by_type
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"통계 조회 중 오류 발생: {str(e)}"
        )


@router.get("/recent", response_model=List[FeedbackResponse])
async def get_recent_feedbacks(
    limit: int = 10,
    feedback_type: Optional[FeedbackType] = None,
    db: Session = Depends(get_db)
):
    """
    최근 피드백 목록 조회
    
    - **limit**: 조회할 개수 (기본 10개)
    - **feedback_type**: 특정 유형만 조회 (선택사항)
    """
    try:
        query = db.query(Feedback).order_by(Feedback.created_at.desc())
        
        if feedback_type:
            query = query.filter(Feedback.feedback_type == feedback_type)
        
        feedbacks = query.limit(limit).all()
        return feedbacks
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"피드백 조회 중 오류 발생: {str(e)}"
        )


@router.get("/{feedback_id}", response_model=FeedbackResponse)
async def get_feedback(
    feedback_id: int,
    db: Session = Depends(get_db)
):
    """특정 피드백 조회"""
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="피드백을 찾을 수 없습니다"
        )
    
    return feedback
