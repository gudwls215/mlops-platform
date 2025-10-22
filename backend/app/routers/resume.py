from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.resume_service import get_resume_service
from app.services.whisper_service import get_whisper_service
from typing import List, Optional
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/")
async def get_resumes(db: Session = Depends(get_db)):
    """이력서 목록 조회"""
    return {"message": "이력서 목록 조회 API"}

@router.post("/")
async def create_resume(db: Session = Depends(get_db)):
    """이력서 생성"""
    return {"message": "이력서 생성 API"}

@router.get("/{resume_id}")
async def get_resume(resume_id: int, db: Session = Depends(get_db)):
    """특정 이력서 조회"""
    return {"message": f"이력서 {resume_id} 조회 API"}

@router.put("/{resume_id}")
async def update_resume(resume_id: int, db: Session = Depends(get_db)):
    """이력서 수정"""
    return {"message": f"이력서 {resume_id} 수정 API"}

@router.delete("/{resume_id}")
async def delete_resume(resume_id: int, db: Session = Depends(get_db)):
    """이력서 삭제"""
    return {"message": f"이력서 {resume_id} 삭제 API"}


@router.post("/extract-from-text")
async def extract_from_text(
    text: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    텍스트로부터 이력서 데이터 추출
    
    Args:
        text: 이력서 내용이 포함된 텍스트
    
    Returns:
        구조화된 이력서 데이터
    """
    try:
        resume_service = get_resume_service()
        result = resume_service.extract_from_user_input(text)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["error"])
        
        return JSONResponse(content=result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text extraction failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"텍스트에서 이력서 데이터 추출 실패: {str(e)}"
        )


@router.post("/extract-from-voice")
async def extract_from_voice(
    audio_file: UploadFile = File(...),
    language: str = Form(default="ko"),
    db: Session = Depends(get_db)
):
    """
    음성 파일로부터 이력서 데이터 추출
    
    Args:
        audio_file: 음성 파일
        language: 인식 언어
    
    Returns:
        구조화된 이력서 데이터
    """
    try:
        # 1. 음성 → 텍스트 변환
        whisper_service = get_whisper_service()
        
        contents = await audio_file.read()
        from io import BytesIO
        audio_bytes = BytesIO(contents)
        
        transcription_result = whisper_service.transcribe_file(
            audio_bytes,
            audio_file.filename,
            language=language
        )
        
        if transcription_result["status"] == "error":
            raise HTTPException(
                status_code=500,
                detail=f"음성 인식 실패: {transcription_result['error']}"
            )
        
        voice_text = transcription_result["text"]
        
        # 2. 텍스트 → 구조화된 데이터
        resume_service = get_resume_service()
        extraction_result = resume_service.extract_from_voice_text(voice_text)
        
        if extraction_result["status"] == "error":
            raise HTTPException(
                status_code=500,
                detail=f"데이터 추출 실패: {extraction_result['error']}"
            )
        
        # 결과 결합
        return JSONResponse(content={
            "status": "success",
            "transcription": {
                "text": voice_text,
                "language": transcription_result["language"]
            },
            "resume_data": extraction_result["data"],
            "metadata": {
                "source": "voice",
                "extracted_at": extraction_result["extracted_at"],
                "total_tokens": extraction_result["tokens_used"],
                "total_cost": extraction_result["cost"]
            }
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice extraction failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"음성에서 이력서 데이터 추출 실패: {str(e)}"
        )


@router.post("/generate-formatted")
async def generate_formatted(
    resume_data: str = Form(...),
    format_type: str = Form(default="markdown"),
    db: Session = Depends(get_db)
):
    """
    구조화된 데이터로부터 포맷팅된 이력서 생성
    
    Args:
        resume_data: JSON 형식의 이력서 데이터
        format_type: 출력 형식 (markdown, html, text)
    
    Returns:
        포맷팅된 이력서
    """
    try:
        # JSON 파싱
        try:
            data = json.loads(resume_data)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="유효하지 않은 JSON 형식입니다"
            )
        
        resume_service = get_resume_service()
        result = resume_service.generate_formatted_resume(data, format_type)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["error"])
        
        return JSONResponse(content=result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resume formatting failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"이력서 포맷팅 실패: {str(e)}"
        )


@router.post("/enhance-section")
async def enhance_section(
    section_name: str = Form(...),
    section_content: str = Form(...),
    target_job: Optional[str] = Form(default=None),
    db: Session = Depends(get_db)
):
    """
    이력서 특정 섹션 개선
    
    Args:
        section_name: 섹션 이름
        section_content: 개선할 섹션 내용
        target_job: 목표 직무 (선택)
    
    Returns:
        개선된 섹션
    """
    try:
        resume_service = get_resume_service()
        result = resume_service.enhance_resume_section(
            section_name,
            section_content,
            target_job
        )
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["error"])
        
        return JSONResponse(content=result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Section enhancement failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"섹션 개선 실패: {str(e)}"
        )


@router.post("/validate")
async def validate_resume(
    resume_data: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    이력서 데이터 유효성 검증
    
    Args:
        resume_data: JSON 형식의 이력서 데이터
    
    Returns:
        검증 결과
    """
    try:
        try:
            data = json.loads(resume_data)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="유효하지 않은 JSON 형식입니다"
            )
        
        resume_service = get_resume_service()
        result = resume_service.validate_resume_data(data)
        
        return JSONResponse(content=result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resume validation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"이력서 검증 실패: {str(e)}"
        )