"""
매칭 서비스 - TF-IDF 기반 이력서-채용공고 유사도 계산
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import Dict, List, Any, Optional
import re


class MatchingService:
    """이력서와 채용공고 간의 매칭 확률을 계산하는 서비스"""
    
    def __init__(self):
        # 한국어 텍스트 처리를 위한 TF-IDF 벡터라이저
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 2),  # 단일 단어와 2-gram
            min_df=1,
            max_df=0.8
        )
        self.stats = {
            "total_matches": 0,
            "avg_similarity": 0.0,
            "high_matches": 0  # 70% 이상
        }
    
    def preprocess_text(self, text: str) -> str:
        """텍스트 전처리"""
        if not text:
            return ""
        
        # 소문자 변환
        text = text.lower()
        
        # 특수문자 제거 (한글, 영문, 숫자, 공백만 유지)
        text = re.sub(r'[^가-힣a-z0-9\s]', ' ', text)
        
        # 여러 공백을 하나로
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def extract_resume_text(self, resume_data: Dict[str, Any]) -> str:
        """이력서 데이터에서 텍스트 추출"""
        parts = []
        
        # 기본 정보
        if "기본정보" in resume_data:
            info = resume_data["기본정보"]
            if "희망직무" in info:
                parts.append(info["희망직무"])
            if "간단소개" in info:
                parts.append(info["간단소개"])
        
        # 경력 정보
        if "경력정보" in resume_data:
            for career in resume_data["경력정보"]:
                if "직무" in career:
                    parts.append(career["직무"])
                if "주요업무" in career:
                    parts.append(career["주요업무"])
                if "성과" in career:
                    parts.append(career["성과"])
        
        # 학력 정보
        if "학력정보" in resume_data:
            edu_data = resume_data["학력정보"]
            # 리스트인 경우
            if isinstance(edu_data, list):
                for edu in edu_data:
                    if "전공" in edu:
                        parts.append(edu["전공"])
            # 딕셔너리인 경우
            elif isinstance(edu_data, dict):
                if "전공" in edu_data:
                    parts.append(edu_data["전공"])
        
        # 기술스택/자격증
        if "기술스택/자격증" in resume_data:
            skills = resume_data["기술스택/자격증"]
            if "기술스택" in skills:
                parts.extend(skills["기술스택"])
            if "자격증" in skills:
                parts.extend(skills["자격증"])
        
        # 자기소개
        if "자기소개" in resume_data:
            parts.append(resume_data["자기소개"])
        
        return " ".join(str(part) for part in parts if part)
    
    def extract_job_posting_text(self, job_posting: Dict[str, Any]) -> str:
        """채용공고 데이터에서 텍스트 추출"""
        parts = []
        
        if "title" in job_posting:
            parts.append(job_posting["title"])
        
        if "company" in job_posting:
            parts.append(job_posting["company"])
        
        if "job_description" in job_posting:
            parts.append(job_posting["job_description"])
        
        if "requirements" in job_posting:
            parts.append(job_posting["requirements"])
        
        if "preferred_qualifications" in job_posting:
            parts.append(job_posting["preferred_qualifications"])
        
        if "skills" in job_posting:
            if isinstance(job_posting["skills"], list):
                parts.extend(job_posting["skills"])
            else:
                parts.append(str(job_posting["skills"]))
        
        return " ".join(str(part) for part in parts if part)
    
    def calculate_similarity(
        self,
        resume_data: Dict[str, Any],
        job_posting: Dict[str, Any]
    ) -> float:
        """TF-IDF 기반 코사인 유사도 계산"""
        
        # 텍스트 추출
        resume_text = self.extract_resume_text(resume_data)
        job_text = self.extract_job_posting_text(job_posting)
        
        if not resume_text or not job_text:
            return 0.0
        
        # 전처리
        resume_text = self.preprocess_text(resume_text)
        job_text = self.preprocess_text(job_text)
        
        if not resume_text or not job_text:
            return 0.0
        
        # TF-IDF 벡터화 (각 계산마다 새로운 vectorizer 사용)
        try:
            vectorizer = TfidfVectorizer(
                max_features=1000,
                ngram_range=(1, 2),
                min_df=1,
                max_df=1.0
            )
            tfidf_matrix = vectorizer.fit_transform([resume_text, job_text])
            
            # 코사인 유사도 계산
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            return float(similarity)
        except Exception as e:
            print(f"유사도 계산 중 오류: {e}")
            return 0.0
    
    def calculate_skill_match(
        self,
        resume_data: Dict[str, Any],
        job_posting: Dict[str, Any]
    ) -> float:
        """스킬 매칭 점수 계산"""
        
        # 이력서의 스킬 추출
        resume_skills = set()
        if "기술스택/자격증" in resume_data and "기술스택" in resume_data["기술스택/자격증"]:
            resume_skills = set(
                skill.lower() for skill in resume_data["기술스택/자격증"]["기술스택"]
            )
        
        # 채용공고의 요구 스킬 추출
        job_skills = set()
        if "skills" in job_posting:
            if isinstance(job_posting["skills"], list):
                job_skills = set(skill.lower() for skill in job_posting["skills"])
            else:
                job_skills = set(
                    skill.strip().lower() 
                    for skill in str(job_posting["skills"]).split(",")
                )
        
        if not job_skills:
            return 0.5  # 스킬 정보 없으면 중립
        
        # 매칭된 스킬 수 계산
        matched_skills = resume_skills.intersection(job_skills)
        
        if not matched_skills:
            return 0.0
        
        # 매칭 비율 계산
        match_ratio = len(matched_skills) / len(job_skills)
        
        return min(match_ratio, 1.0)
    
    def calculate_experience_score(
        self,
        resume_data: Dict[str, Any],
        job_posting: Dict[str, Any]
    ) -> float:
        """경력 점수 계산"""
        
        # 이력서의 총 경력 계산
        total_years = 0
        if "경력정보" in resume_data:
            for career in resume_data["경력정보"]:
                if "재직기간" in career:
                    period = career["재직기간"]
                    # 간단한 년수 추출 (예: "2020.01 ~ 2023.12" -> 3년)
                    years = self._extract_years_from_period(period)
                    total_years += years
        
        # 채용공고의 요구 경력 추출
        required_years = 0
        if "requirements" in job_posting:
            required_years = self._extract_required_years(job_posting["requirements"])
        
        if required_years == 0:
            return 0.8  # 경력 요구사항 없으면 높은 점수
        
        # 경력 매칭 점수 계산
        if total_years >= required_years:
            return 1.0
        elif total_years >= required_years * 0.7:
            return 0.8
        elif total_years >= required_years * 0.5:
            return 0.6
        else:
            return 0.3
    
    def _extract_years_from_period(self, period: str) -> int:
        """재직기간에서 년수 추출"""
        try:
            # "2020.01 ~ 2023.12" 형식
            parts = period.split("~")
            if len(parts) == 2:
                start_year = int(parts[0].strip().split(".")[0])
                end_part = parts[1].strip()
                if "현재" in end_part or "재직중" in end_part:
                    from datetime import datetime
                    end_year = datetime.now().year
                else:
                    end_year = int(end_part.split(".")[0])
                return max(0, end_year - start_year)
        except:
            pass
        return 0
    
    def _extract_required_years(self, requirements: str) -> int:
        """요구사항에서 필요 경력 년수 추출"""
        if not requirements:
            return 0
        
        # "3년 이상", "5년차 이상" 등의 패턴 찾기
        import re
        patterns = [
            r'(\d+)년\s*이상',
            r'(\d+)년차\s*이상',
            r'경력\s*(\d+)년',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, requirements)
            if match:
                return int(match.group(1))
        
        return 0
    
    def calculate_matching_score(
        self,
        resume_data: Dict[str, Any],
        job_posting: Dict[str, Any],
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """종합 매칭 점수 계산"""
        
        # 기본 가중치
        if weights is None:
            weights = {
                "similarity": 0.3,       # TF-IDF 유사도
                "skill_match": 0.45,     # 스킬 매칭
                "experience": 0.25       # 경력 매칭
            }
        
        # 각 점수 계산
        similarity = self.calculate_similarity(resume_data, job_posting)
        skill_match = self.calculate_skill_match(resume_data, job_posting)
        experience_score = self.calculate_experience_score(resume_data, job_posting)
        
        # 가중 평균 계산
        total_score = (
            similarity * weights["similarity"] +
            skill_match * weights["skill_match"] +
            experience_score * weights["experience"]
        )
        
        # 백분율로 변환
        matching_probability = round(total_score * 100, 2)
        
        # 통계 업데이트
        self.stats["total_matches"] += 1
        self.stats["avg_similarity"] = (
            (self.stats["avg_similarity"] * (self.stats["total_matches"] - 1) + matching_probability)
            / self.stats["total_matches"]
        )
        if matching_probability >= 70:
            self.stats["high_matches"] += 1
        
        return {
            "matching_probability": matching_probability,
            "details": {
                "tfidf_similarity": round(similarity * 100, 2),
                "skill_match": round(skill_match * 100, 2),
                "experience_score": round(experience_score * 100, 2)
            },
            "weights": weights,
            "recommendation": self._get_recommendation(matching_probability)
        }
    
    def _get_recommendation(self, score: float) -> str:
        """점수에 따른 추천 메시지"""
        if score >= 80:
            return "매우 적합합니다. 적극 지원을 권장합니다."
        elif score >= 70:
            return "적합합니다. 지원을 권장합니다."
        elif score >= 60:
            return "보통입니다. 관심 있다면 지원을 고려해보세요."
        elif score >= 50:
            return "다소 낮습니다. 부족한 부분을 보완 후 지원하세요."
        else:
            return "적합도가 낮습니다. 다른 공고를 찾아보는 것을 권장합니다."
    
    def batch_calculate_matching(
        self,
        resume_data: Dict[str, Any],
        job_postings: List[Dict[str, Any]],
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """여러 채용공고에 대한 매칭 점수 계산 및 정렬"""
        
        results = []
        
        for job_posting in job_postings:
            try:
                matching_result = self.calculate_matching_score(resume_data, job_posting)
                
                results.append({
                    "job_posting": job_posting,
                    "matching_probability": matching_result["matching_probability"],
                    "details": matching_result["details"],
                    "recommendation": matching_result["recommendation"]
                })
            except Exception as e:
                print(f"매칭 계산 중 오류: {e}")
                continue
        
        # 매칭 확률 기준 내림차순 정렬
        results.sort(key=lambda x: x["matching_probability"], reverse=True)
        
        # 상위 N개 반환
        return results[:top_n]
    
    def get_stats(self) -> Dict[str, Any]:
        """서비스 통계 조회"""
        return {
            "total_matches": self.stats["total_matches"],
            "avg_similarity": round(self.stats["avg_similarity"], 2),
            "high_matches": self.stats["high_matches"],
            "high_match_rate": (
                round(self.stats["high_matches"] / self.stats["total_matches"] * 100, 2)
                if self.stats["total_matches"] > 0 else 0
            )
        }


# 싱글톤 인스턴스
_matching_service = None


def get_matching_service() -> MatchingService:
    """매칭 서비스 인스턴스 반환"""
    global _matching_service
    if _matching_service is None:
        _matching_service = MatchingService()
    return _matching_service
