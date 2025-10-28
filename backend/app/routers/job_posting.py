from fastapi import APIRouter, Depends, HTTPException, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.core.database import get_db
from app.models import JobPosting, Resume
from app.services.matching_service import get_matching_service
from typing import List, Optional
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/")
async def get_job_postings(
    skip: int = 0,
    limit: int = 100,
    company: Optional[str] = None,
    employment_type: Optional[str] = None,
    experience_level: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    채용공고 목록 조회
    
    Args:
        skip: 건너뛸 레코드 수
        limit: 조회할 최대 레코드 수
        company: 회사명 필터
        employment_type: 고용 형태 필터 (정규직, 계약직 등)
        experience_level: 경력 수준 필터 (신입, 경력 등)
    """
    try:
        query = db.query(JobPosting).filter(JobPosting.is_active == True)
        
        if company:
            query = query.filter(JobPosting.company.ilike(f"%{company}%"))
        if employment_type:
            query = query.filter(JobPosting.employment_type == employment_type)
        if experience_level:
            query = query.filter(JobPosting.experience_level == experience_level)
        
        total = query.count()
        job_postings = query.order_by(JobPosting.created_at.desc()).offset(skip).limit(limit).all()
        
        return JSONResponse(content={
            "status": "success",
            "data": {
                "total": total,
                "skip": skip,
                "limit": limit,
                "job_postings": [
                    {
                        "id": jp.id,
                        "title": jp.title,
                        "company": jp.company,
                        "location": jp.location,
                        "employment_type": jp.employment_type,
                        "experience_level": jp.experience_level,
                        "salary_min": jp.salary_min,
                        "salary_max": jp.salary_max,
                        "created_at": jp.created_at.isoformat() if jp.created_at else None
                    }
                    for jp in job_postings
                ]
            }
        })
    except Exception as e:
        logger.error(f"채용공고 목록 조회 오류: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": str(e)}
        )

@router.get("/{job_id}")
async def get_job_posting(job_id: int, db: Session = Depends(get_db)):
    """특정 채용공고 상세 조회"""
    try:
        job_posting = db.query(JobPosting).filter(
            JobPosting.id == job_id,
            JobPosting.is_active == True
        ).first()
        
        if not job_posting:
            return JSONResponse(
                status_code=404,
                content={"status": "error", "error": "채용공고를 찾을 수 없습니다."}
            )
        
        return JSONResponse(content={
            "status": "success",
            "data": {
                "id": job_posting.id,
                "title": job_posting.title,
                "company": job_posting.company,
                "description": job_posting.description,
                "requirements": job_posting.requirements,
                "location": job_posting.location,
                "salary_min": job_posting.salary_min,
                "salary_max": job_posting.salary_max,
                "employment_type": job_posting.employment_type,
                "experience_level": job_posting.experience_level,
                "source_url": job_posting.source_url,
                "created_at": job_posting.created_at.isoformat() if job_posting.created_at else None
            }
        })
    except Exception as e:
        logger.error(f"채용공고 조회 오류: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": str(e)}
        )

@router.post("/search")
async def search_job_postings(
    keyword: str = Form(...),
    skip: int = Form(0),
    limit: int = Form(50),
    db: Session = Depends(get_db)
):
    """
    채용공고 키워드 검색
    
    Args:
        keyword: 검색 키워드
        skip: 건너뛸 레코드 수
        limit: 조회할 최대 레코드 수
    """
    try:
        query = db.query(JobPosting).filter(
            JobPosting.is_active == True,
            or_(
                JobPosting.title.ilike(f"%{keyword}%"),
                JobPosting.company.ilike(f"%{keyword}%"),
                JobPosting.description.ilike(f"%{keyword}%"),
                JobPosting.requirements.ilike(f"%{keyword}%")
            )
        )
        
        total = query.count()
        job_postings = query.order_by(JobPosting.created_at.desc()).offset(skip).limit(limit).all()
        
        return JSONResponse(content={
            "status": "success",
            "data": {
                "keyword": keyword,
                "total": total,
                "skip": skip,
                "limit": limit,
                "job_postings": [
                    {
                        "id": jp.id,
                        "title": jp.title,
                        "company": jp.company,
                        "location": jp.location,
                        "employment_type": jp.employment_type,
                        "experience_level": jp.experience_level,
                        "created_at": jp.created_at.isoformat() if jp.created_at else None
                    }
                    for jp in job_postings
                ]
            }
        })
    except Exception as e:
        logger.error(f"채용공고 검색 오류: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": str(e)}
        )

@router.post("/match")
async def match_job_postings(
    resume_id: int = Form(...),
    top_n: int = Form(10),
    db: Session = Depends(get_db)
):
    """
    이력서-채용공고 매칭
    
    Args:
        resume_id: 이력서 ID
        top_n: 반환할 상위 결과 수
    """
    try:
        # 이력서 조회
        resume = db.query(Resume).filter(
            Resume.id == resume_id,
            Resume.is_active == True
        ).first()
        
        if not resume:
            return JSONResponse(
                status_code=404,
                content={"status": "error", "error": "이력서를 찾을 수 없습니다."}
            )
        
        # 활성 채용공고 조회
        job_postings = db.query(JobPosting).filter(
            JobPosting.is_active == True
        ).all()
        
        if not job_postings:
            return JSONResponse(content={
                "status": "success",
                "data": {
                    "resume_id": resume_id,
                    "total_jobs": 0,
                    "matches": []
                }
            })
        
        # 이력서 데이터 준비
        resume_data = json.loads(resume.content) if resume.content else {}
        
        # 채용공고 데이터 준비
        job_list = [
            {
                "id": jp.id,
                "title": jp.title,
                "company": jp.company,
                "job_description": jp.description,
                "requirements": jp.requirements,
                "location": jp.location,
                "employment_type": jp.employment_type,
                "experience_level": jp.experience_level
            }
            for jp in job_postings
        ]
        
        # 매칭 서비스 호출
        matching_service = get_matching_service()
        matches = matching_service.batch_calculate_matching(resume_data, job_list, top_n)
        
        return JSONResponse(content={
            "status": "success",
            "data": {
                "resume_id": resume_id,
                "total_jobs": len(job_postings),
                "returned_matches": len(matches),
                "matches": [
                    {
                        "job_id": match["job_posting"]["id"],
                        "title": match["job_posting"]["title"],
                        "company": match["job_posting"]["company"],
                        "location": match["job_posting"]["location"],
                        "matching_probability": match["matching_probability"],
                        "details": match["details"],
                        "recommendation": match["recommendation"]
                    }
                    for match in matches
                ]
            }
        })
    except Exception as e:
        logger.error(f"채용공고 매칭 오류: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": str(e)}
        )

@router.get("/recommendations/{user_id}")
async def get_job_recommendations(
    user_id: int,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    사용자 맞춤 채용공고 추천
    
    Args:
        user_id: 사용자 ID
        limit: 반환할 추천 결과 수
    """
    try:
        # 사용자의 최신 이력서 조회
        resume = db.query(Resume).filter(
            Resume.user_id == user_id,
            Resume.is_active == True
        ).order_by(Resume.updated_at.desc()).first()
        
        if not resume:
            return JSONResponse(
                status_code=404,
                content={"status": "error", "error": "사용자의 이력서를 찾을 수 없습니다."}
            )
        
        # 활성 채용공고 조회
        job_postings = db.query(JobPosting).filter(
            JobPosting.is_active == True
        ).limit(500).all()  # 최대 500개까지만 매칭
        
        if not job_postings:
            return JSONResponse(content={
                "status": "success",
                "data": {
                    "user_id": user_id,
                    "resume_id": resume.id,
                    "recommendations": []
                }
            })
        
        # 이력서 데이터 준비
        resume_data = json.loads(resume.content) if resume.content else {}
        
        # 채용공고 데이터 준비
        job_list = [
            {
                "id": jp.id,
                "title": jp.title,
                "company": jp.company,
                "job_description": jp.description,
                "requirements": jp.requirements,
                "location": jp.location,
                "employment_type": jp.employment_type,
                "experience_level": jp.experience_level
            }
            for jp in job_postings
        ]
        
        # 매칭 서비스 호출
        matching_service = get_matching_service()
        recommendations = matching_service.batch_calculate_matching(resume_data, job_list, limit)
        
        return JSONResponse(content={
            "status": "success",
            "data": {
                "user_id": user_id,
                "resume_id": resume.id,
                "total_analyzed": len(job_postings),
                "recommendations": [
                    {
                        "job_id": rec["job_posting"]["id"],
                        "title": rec["job_posting"]["title"],
                        "company": rec["job_posting"]["company"],
                        "location": rec["job_posting"]["location"],
                        "matching_probability": rec["matching_probability"],
                        "recommendation": rec["recommendation"]
                    }
                    for rec in recommendations
                ]
            }
        })
    except Exception as e:
        logger.error(f"채용공고 추천 오류: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": str(e)}
        )