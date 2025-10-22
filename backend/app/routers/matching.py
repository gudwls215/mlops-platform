"""
매칭 API 라우터 - 이력서와 채용공고 매칭
"""

from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from typing import Optional
import json

from app.services.matching_service import get_matching_service

router = APIRouter()


@router.post("/api/matching/calculate-probability")
async def calculate_matching_probability(
    resume_data: str = Form(..., description="이력서 데이터 (JSON 문자열)"),
    job_posting: str = Form(..., description="채용공고 데이터 (JSON 문자열)"),
    weights: Optional[str] = Form(None, description="가중치 설정 (JSON 문자열, 선택사항)")
):
    """
    이력서와 채용공고 간의 매칭 확률 계산
    
    - resume_data: 이력서 구조화된 데이터 (JSON)
    - job_posting: 채용공고 데이터 (JSON)
    - weights: 가중치 설정 (선택사항, similarity/skill_match/experience)
    
    Returns:
    - matching_probability: 매칭 확률 (0-100)
    - details: 세부 점수 (TF-IDF, 스킬, 경력)
    - recommendation: 추천 메시지
    """
    
    try:
        matching_service = get_matching_service()
        
        # JSON 문자열을 딕셔너리로 변환
        resume_dict = json.loads(resume_data)
        job_dict = json.loads(job_posting)
        
        weights_dict = None
        if weights:
            weights_dict = json.loads(weights)
        
        # 매칭 점수 계산
        result = matching_service.calculate_matching_score(
            resume_dict,
            job_dict,
            weights_dict
        )
        
        return JSONResponse(content={
            "status": "success",
            "data": result
        })
        
    except json.JSONDecodeError as e:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error": f"JSON 파싱 오류: {str(e)}"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e)
            }
        )


@router.post("/api/matching/batch-calculate")
async def batch_calculate_matching(
    resume_data: str = Form(..., description="이력서 데이터 (JSON 문자열)"),
    job_postings: str = Form(..., description="채용공고 목록 (JSON 배열 문자열)"),
    top_n: int = Form(10, description="반환할 상위 결과 수")
):
    """
    이력서와 여러 채용공고 간의 매칭 확률 일괄 계산
    
    - resume_data: 이력서 구조화된 데이터 (JSON)
    - job_postings: 채용공고 목록 (JSON 배열)
    - top_n: 반환할 상위 결과 수 (기본값: 10)
    
    Returns:
    - results: 매칭 결과 목록 (매칭 확률 기준 내림차순 정렬)
    """
    
    try:
        matching_service = get_matching_service()
        
        # JSON 문자열을 딕셔너리/리스트로 변환
        resume_dict = json.loads(resume_data)
        job_list = json.loads(job_postings)
        
        if not isinstance(job_list, list):
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "error": "job_postings는 배열 형식이어야 합니다."
                }
            )
        
        # 일괄 매칭 계산
        results = matching_service.batch_calculate_matching(
            resume_dict,
            job_list,
            top_n
        )
        
        return JSONResponse(content={
            "status": "success",
            "data": {
                "total_jobs": len(job_list),
                "returned_results": len(results),
                "results": results
            }
        })
        
    except json.JSONDecodeError as e:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error": f"JSON 파싱 오류: {str(e)}"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e)
            }
        )


@router.post("/api/matching/similarity")
async def calculate_similarity(
    resume_data: str = Form(..., description="이력서 데이터 (JSON 문자열)"),
    job_posting: str = Form(..., description="채용공고 데이터 (JSON 문자열)")
):
    """
    TF-IDF 기반 텍스트 유사도만 계산
    
    - resume_data: 이력서 구조화된 데이터 (JSON)
    - job_posting: 채용공고 데이터 (JSON)
    
    Returns:
    - similarity: 유사도 점수 (0-100)
    """
    
    try:
        matching_service = get_matching_service()
        
        # JSON 문자열을 딕셔너리로 변환
        resume_dict = json.loads(resume_data)
        job_dict = json.loads(job_posting)
        
        # 유사도만 계산
        similarity = matching_service.calculate_similarity(resume_dict, job_dict)
        
        return JSONResponse(content={
            "status": "success",
            "data": {
                "similarity": round(similarity * 100, 2),
                "description": "TF-IDF 기반 코사인 유사도"
            }
        })
        
    except json.JSONDecodeError as e:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error": f"JSON 파싱 오류: {str(e)}"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e)
            }
        )


@router.post("/api/matching/skill-match")
async def calculate_skill_match(
    resume_data: str = Form(..., description="이력서 데이터 (JSON 문자열)"),
    job_posting: str = Form(..., description="채용공고 데이터 (JSON 문자열)")
):
    """
    스킬 매칭 점수만 계산
    
    - resume_data: 이력서 구조화된 데이터 (JSON)
    - job_posting: 채용공고 데이터 (JSON)
    
    Returns:
    - skill_match: 스킬 매칭 점수 (0-100)
    - matched_skills: 매칭된 스킬 목록
    """
    
    try:
        matching_service = get_matching_service()
        
        # JSON 문자열을 딕셔너리로 변환
        resume_dict = json.loads(resume_data)
        job_dict = json.loads(job_posting)
        
        # 스킬 매칭 점수 계산
        skill_match = matching_service.calculate_skill_match(resume_dict, job_dict)
        
        # 매칭된 스킬 추출
        resume_skills = set()
        if "기술스택/자격증" in resume_dict and "기술스택" in resume_dict["기술스택/자격증"]:
            resume_skills = set(
                skill.lower() for skill in resume_dict["기술스택/자격증"]["기술스택"]
            )
        
        job_skills = set()
        if "skills" in job_dict:
            if isinstance(job_dict["skills"], list):
                job_skills = set(skill.lower() for skill in job_dict["skills"])
            else:
                job_skills = set(
                    skill.strip().lower() 
                    for skill in str(job_dict["skills"]).split(",")
                )
        
        matched_skills = list(resume_skills.intersection(job_skills))
        
        return JSONResponse(content={
            "status": "success",
            "data": {
                "skill_match": round(skill_match * 100, 2),
                "matched_skills": matched_skills,
                "resume_skills_count": len(resume_skills),
                "required_skills_count": len(job_skills)
            }
        })
        
    except json.JSONDecodeError as e:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error": f"JSON 파싱 오류: {str(e)}"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e)
            }
        )


@router.get("/api/matching/stats")
async def get_matching_stats():
    """
    매칭 서비스 통계 조회
    
    Returns:
    - total_matches: 총 매칭 수
    - avg_similarity: 평균 유사도
    - high_matches: 높은 매칭 수 (70% 이상)
    - high_match_rate: 높은 매칭 비율
    """
    
    try:
        matching_service = get_matching_service()
        stats = matching_service.get_stats()
        
        return JSONResponse(content={
            "status": "success",
            "data": stats
        })
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e)
            }
        )
