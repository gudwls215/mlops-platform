"""
자기소개서 생성 관련 API 라우터
"""
from fastapi import APIRouter, Depends, HTTPException, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.cover_letter_service import get_cover_letter_service
from typing import Optional, List
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cover-letter", tags=["cover-letter"])


@router.post("/analyze-job")
async def analyze_job_posting(
    job_posting_data: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    채용공고 분석
    
    Args:
        job_posting_data: JSON 형식의 채용공고 데이터
    
    Returns:
        분석 결과 및 핵심 키워드
    """
    try:
        try:
            job_posting = json.loads(job_posting_data)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="유효하지 않은 JSON 형식입니다"
            )
        
        service = get_cover_letter_service()
        result = service.analyze_job_posting(job_posting)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["error"])
        
        return JSONResponse(content=result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Job posting analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"채용공고 분석 실패: {str(e)}"
        )


@router.post("/generate")
async def generate_cover_letter(
    job_posting_data: str = Form(...),
    resume_data: str = Form(...),
    samples: Optional[str] = Form(default=None),
    tone: str = Form(default="professional"),
    db: Session = Depends(get_db)
):
    """
    맞춤형 자기소개서 생성
    
    Args:
        job_posting_data: JSON 형식의 채용공고 데이터
        resume_data: JSON 형식의 이력서 데이터
        samples: JSON 배열 형식의 샘플 자기소개서 리스트 (선택)
        tone: 톤 ("professional", "friendly", "passionate")
    
    Returns:
        생성된 자기소개서
    """
    try:
        # JSON 파싱
        try:
            job_posting = json.loads(job_posting_data)
            resume = json.loads(resume_data)
            sample_list = json.loads(samples) if samples else None
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"유효하지 않은 JSON 형식입니다: {str(e)}"
            )
        
        service = get_cover_letter_service()
        result = service.generate_cover_letter(
            job_posting,
            resume,
            samples=sample_list,
            tone=tone
        )
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["error"])
        
        return JSONResponse(content=result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cover letter generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"자기소개서 생성 실패: {str(e)}"
        )


@router.post("/extract-key-points")
async def extract_key_points(
    cover_letter: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    자기소개서 핵심 포인트 추출
    
    Args:
        cover_letter: 자기소개서 내용
    
    Returns:
        추출된 핵심 포인트
    """
    try:
        service = get_cover_letter_service()
        result = service.extract_key_points(cover_letter)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["error"])
        
        return JSONResponse(content=result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Key points extraction failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"핵심 포인트 추출 실패: {str(e)}"
        )


@router.post("/improve")
async def improve_cover_letter(
    cover_letter: str = Form(...),
    feedback: Optional[str] = Form(default=None),
    db: Session = Depends(get_db)
):
    """
    자기소개서 개선
    
    Args:
        cover_letter: 원본 자기소개서
        feedback: 개선 방향 피드백 (선택)
    
    Returns:
        개선된 자기소개서
    """
    try:
        service = get_cover_letter_service()
        result = service.improve_cover_letter(cover_letter, feedback)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["error"])
        
        return JSONResponse(content=result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cover letter improvement failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"자기소개서 개선 실패: {str(e)}"
        )


@router.post("/validate")
async def validate_cover_letter(
    cover_letter: str = Form(...),
    job_posting_data: Optional[str] = Form(default=None),
    db: Session = Depends(get_db)
):
    """
    자기소개서 검증
    
    Args:
        cover_letter: 검증할 자기소개서
        job_posting_data: JSON 형식의 채용공고 데이터 (선택)
    
    Returns:
        검증 결과
    """
    try:
        job_posting = None
        if job_posting_data:
            try:
                job_posting = json.loads(job_posting_data)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail="채용공고 데이터가 유효하지 않은 JSON 형식입니다"
                )
        
        service = get_cover_letter_service()
        result = service.validate_cover_letter(cover_letter, job_posting)
        
        return JSONResponse(content=result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cover letter validation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"자기소개서 검증 실패: {str(e)}"
        )


@router.post("/generate-variations")
async def generate_variations(
    job_posting_data: str = Form(...),
    resume_data: str = Form(...),
    count: int = Form(default=3),
    db: Session = Depends(get_db)
):
    """
    여러 버전의 자기소개서 생성
    
    Args:
        job_posting_data: JSON 형식의 채용공고 데이터
        resume_data: JSON 형식의 이력서 데이터
        count: 생성할 버전 수 (최대 3개)
    
    Returns:
        여러 버전의 자기소개서
    """
    try:
        try:
            job_posting = json.loads(job_posting_data)
            resume = json.loads(resume_data)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="유효하지 않은 JSON 형식입니다"
            )
        
        if count > 3:
            raise HTTPException(
                status_code=400,
                detail="최대 3개까지만 생성 가능합니다"
            )
        
        service = get_cover_letter_service()
        result = service.generate_variations(job_posting, resume, count)
        
        if result["status"] == "error":
            raise HTTPException(
                status_code=500,
                detail="자기소개서 생성 실패"
            )
        
        return JSONResponse(content=result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cover letter variations generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"자기소개서 버전 생성 실패: {str(e)}"
        )
