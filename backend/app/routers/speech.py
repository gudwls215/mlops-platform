"""
음성 처리 관련 API 라우터
"""
from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from typing import Optional
import logging

from app.services.whisper_service import get_whisper_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/speech", tags=["speech"])


@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: Optional[str] = Form(default="ko"),
    with_timestamps: bool = Form(default=False)
):
    """
    음성 파일을 텍스트로 변환 (STT)
    
    Args:
        file: 음성 파일 (mp3, wav, m4a, ogg 등)
        language: 인식 언어 코드 (ko, en, ja 등)
        with_timestamps: 타임스탬프 포함 여부
    
    Returns:
        변환된 텍스트 및 세그먼트 정보
    """
    # 파일 검증
    if not file.filename:
        raise HTTPException(status_code=400, detail="파일명이 없습니다")
    
    # 허용된 확장자 검증
    allowed_extensions = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm"}
    file_ext = file.filename[file.filename.rfind("."):].lower() if "." in file.filename else ""
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 파일 형식입니다. 허용된 형식: {', '.join(allowed_extensions)}"
        )
    
    try:
        # Whisper 서비스 가져오기
        whisper_service = get_whisper_service()
        
        # 파일 읽기
        contents = await file.read()
        
        # 바이너리 파일 객체로 변환
        from io import BytesIO
        audio_file = BytesIO(contents)
        
        # 음성 인식
        if with_timestamps:
            result = whisper_service.transcribe_with_timestamps(
                audio_file,
                file.filename,
                language=language
            )
        else:
            result = whisper_service.transcribe_file(
                audio_file,
                file.filename,
                language=language
            )
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["error"])
        
        return JSONResponse(content=result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audio transcription failed: {e}")
        raise HTTPException(status_code=500, detail=f"음성 인식 중 오류가 발생했습니다: {str(e)}")


@router.post("/detect-language")
async def detect_language(file: UploadFile = File(...)):
    """
    음성 파일의 언어 자동 감지
    
    Args:
        file: 음성 파일
    
    Returns:
        감지된 언어 정보
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="파일명이 없습니다")
    
    try:
        whisper_service = get_whisper_service()
        
        contents = await file.read()
        from io import BytesIO
        audio_file = BytesIO(contents)
        
        result = whisper_service.detect_language(audio_file, file.filename)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["error"])
        
        return JSONResponse(content=result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Language detection failed: {e}")
        raise HTTPException(status_code=500, detail=f"언어 감지 중 오류가 발생했습니다: {str(e)}")


@router.get("/stats")
async def get_stats():
    """
    Whisper 서비스 통계 조회
    
    Returns:
        서비스 통계 정보
    """
    try:
        whisper_service = get_whisper_service()
        stats = whisper_service.get_stats()
        return JSONResponse(content=stats)
    
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=f"통계 조회 중 오류가 발생했습니다: {str(e)}")


@router.post("/test")
async def test_whisper():
    """
    Whisper 서비스 연결 테스트
    
    Returns:
        테스트 결과
    """
    try:
        whisper_service = get_whisper_service()
        stats = whisper_service.get_stats()
        
        return JSONResponse(content={
            "status": "success",
            "message": "Whisper service is running",
            "stats": stats
        })
    
    except Exception as e:
        logger.error(f"Whisper test failed: {e}")
        raise HTTPException(status_code=500, detail=f"서비스 테스트 실패: {str(e)}")
