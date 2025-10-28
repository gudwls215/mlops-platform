from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.resume_service import get_resume_service
from app.services.whisper_service import get_whisper_service
from app.services.embedding_service import generate_embedding
from app.models import Resume
from typing import List, Optional
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/")
async def get_resumes(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    이력서 목록 조회
    
    Args:
        skip: 건너뛸 레코드 수
        limit: 조회할 최대 레코드 수
        user_id: 특정 사용자의 이력서만 조회 (선택사항)
    """
    try:
        query = db.query(Resume).filter(Resume.is_active == True)
        
        if user_id:
            query = query.filter(Resume.user_id == user_id)
        
        total = query.count()
        resumes = query.offset(skip).limit(limit).all()
        
        return JSONResponse(content={
            "status": "success",
            "data": {
                "total": total,
                "skip": skip,
                "limit": limit,
                "resumes": [
                    {
                        "id": r.id,
                        "user_id": r.user_id,
                        "title": r.title,
                        "skills": json.loads(r.skills) if r.skills else [],
                        "created_at": r.created_at.isoformat() if r.created_at else None,
                        "updated_at": r.updated_at.isoformat() if r.updated_at else None
                    }
                    for r in resumes
                ]
            }
        })
    except Exception as e:
        logger.error(f"이력서 목록 조회 오류: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": str(e)}
        )

@router.post("/")
async def create_resume(
    title: str = Form(...),
    content: str = Form(...),
    skills: Optional[str] = Form(None),
    user_id: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    """
    이력서 생성
    
    Args:
        title: 이력서 제목
        content: 이력서 전체 내용 (JSON 문자열)
        skills: 기술스택 (JSON 배열 문자열)
        user_id: 사용자 ID
    """
    try:
        # user_id가 없으면 기본값 1 사용
        if user_id is None:
            user_id = 1
        
        # 임베딩 생성
        logger.info("이력서 임베딩 생성 시작...")
        embedding_str = generate_embedding(content)
        
        if embedding_str:
            logger.info("임베딩 생성 완료")
        else:
            logger.warning("임베딩 생성 실패 - 이력서는 저장되지만 추천 기능 사용 불가")
        
        new_resume = Resume(
            user_id=user_id,
            title=title,
            content=content,
            skills=skills,
            embedding_array=embedding_str
        )
        
        db.add(new_resume)
        db.commit()
        db.refresh(new_resume)
        
        return JSONResponse(content={
            "status": "success",
            "data": {
                "id": new_resume.id,
                "user_id": new_resume.user_id,
                "title": new_resume.title,
                "created_at": new_resume.created_at.isoformat(),
                "has_embedding": embedding_str is not None
            },
            "message": "이력서가 성공적으로 생성되었습니다." + (
                " (임베딩 생성 완료)" if embedding_str else " (임베딩 생성 실패)"
            )
        })
    except Exception as e:
        db.rollback()
        logger.error(f"이력서 생성 오류: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": str(e)}
        )

@router.get("/{resume_id}")
async def get_resume(resume_id: int, db: Session = Depends(get_db)):
    """특정 이력서 상세 조회"""
    try:
        resume = db.query(Resume).filter(
            Resume.id == resume_id,
            Resume.is_active == True
        ).first()
        
        if not resume:
            return JSONResponse(
                status_code=404,
                content={"status": "error", "error": "이력서를 찾을 수 없습니다."}
            )
        
        return JSONResponse(content={
            "status": "success",
            "data": {
                "id": resume.id,
                "user_id": resume.user_id,
                "title": resume.title,
                "content": json.loads(resume.content) if resume.content else {},
                "skills": json.loads(resume.skills) if resume.skills else [],
                "experience": json.loads(resume.experience) if resume.experience else [],
                "education": json.loads(resume.education) if resume.education else [],
                "created_at": resume.created_at.isoformat() if resume.created_at else None,
                "updated_at": resume.updated_at.isoformat() if resume.updated_at else None
            }
        })
    except Exception as e:
        logger.error(f"이력서 조회 오류: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": str(e)}
        )

@router.put("/{resume_id}")
async def update_resume(
    resume_id: int,
    title: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    skills: Optional[str] = Form(None),
    experience: Optional[str] = Form(None),
    education: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """이력서 수정"""
    try:
        resume = db.query(Resume).filter(
            Resume.id == resume_id,
            Resume.is_active == True
        ).first()
        
        if not resume:
            return JSONResponse(
                status_code=404,
                content={"status": "error", "error": "이력서를 찾을 수 없습니다."}
            )
        
        # 제공된 필드만 업데이트
        if title is not None:
            resume.title = title
        if content is not None:
            resume.content = content
        if skills is not None:
            resume.skills = skills
        if experience is not None:
            resume.experience = experience
        if education is not None:
            resume.education = education
        
        db.commit()
        db.refresh(resume)
        
        return JSONResponse(content={
            "status": "success",
            "data": {
                "id": resume.id,
                "title": resume.title,
                "updated_at": resume.updated_at.isoformat() if resume.updated_at else None
            },
            "message": "이력서가 성공적으로 수정되었습니다."
        })
    except Exception as e:
        db.rollback()
        logger.error(f"이력서 수정 오류: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": str(e)}
        )

@router.delete("/{resume_id}")
async def delete_resume(resume_id: int, db: Session = Depends(get_db)):
    """이력서 삭제 (소프트 삭제)"""
    try:
        resume = db.query(Resume).filter(
            Resume.id == resume_id,
            Resume.is_active == True
        ).first()
        
        if not resume:
            return JSONResponse(
                status_code=404,
                content={"status": "error", "error": "이력서를 찾을 수 없습니다."}
            )
        
        # 소프트 삭제
        resume.is_active = False
        db.commit()
        
        return JSONResponse(content={
            "status": "success",
            "message": "이력서가 성공적으로 삭제되었습니다."
        })
    except Exception as e:
        db.rollback()
        logger.error(f"이력서 삭제 오류: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": str(e)}
        )


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