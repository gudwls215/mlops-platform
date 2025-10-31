"""
경력 분석 알고리즘
이력서에서 경력 정보를 추출하고 분석하여 직무 매칭에 활용
"""
import re
import json
from typing import Dict, List, Tuple, Optional
from collections import Counter
import numpy as np


class CareerAnalyzer:
    """이력서 경력 분석 클래스"""
    
    # 직무 관련 키워드 매핑
    JOB_KEYWORDS = {
        "마케팅": ["마케팅", "광고", "브랜드", "캠페인", "프로모션", "SNS", "디지털마케팅", "콘텐츠", "영업지원"],
        "개발": ["개발", "프로그래밍", "코딩", "소프트웨어", "앱", "웹", "시스템", "백엔드", "프론트엔드", "풀스택"],
        "영업": ["영업", "세일즈", "판매", "고객관리", "B2B", "B2C", "제안", "계약", "매출"],
        "기획": ["기획", "전략", "PM", "PO", "프로젝트", "기획안", "제안서", "분석"],
        "디자인": ["디자인", "UI", "UX", "그래픽", "비주얼", "브랜딩", "편집", "일러스트"],
        "인사": ["인사", "HR", "채용", "교육", "평가", "조직문화", "복리후생", "노무"],
        "재무": ["재무", "회계", "경리", "세무", "결산", "원가", "투자", "예산"],
        "생산": ["생산", "제조", "공정", "품질", "QC", "설비", "안전", "개선"],
        "연구": ["연구", "R&D", "개발", "실험", "분석", "논문", "특허", "기술"],
        "경영지원": ["총무", "구매", "자재", "시설", "법무", "감사", "전산", "비서"],
    }
    
    # 경력 연차 키워드
    EXPERIENCE_KEYWORDS = {
        "신입": 0,
        "1년": 1,
        "2년": 2,
        "3년": 3,
        "4년": 4,
        "5년": 5,
        "10년": 10,
        "15년": 15,
        "20년": 20,
    }
    
    # 기술 스택 키워드
    TECH_KEYWORDS = {
        "프로그래밍": ["Python", "Java", "JavaScript", "C++", "C#", "Go", "Ruby", "PHP"],
        "프레임워크": ["Django", "Flask", "FastAPI", "Spring", "React", "Vue", "Angular", "Node.js"],
        "데이터베이스": ["MySQL", "PostgreSQL", "MongoDB", "Oracle", "Redis", "Elasticsearch"],
        "클라우드": ["AWS", "Azure", "GCP", "Docker", "Kubernetes", "Jenkins"],
        "데이터": ["SQL", "Pandas", "NumPy", "Tableau", "PowerBI", "Excel"],
        "디자인툴": ["Photoshop", "Illustrator", "Figma", "Sketch", "XD"],
    }
    
    def __init__(self):
        """초기화"""
        pass
    
    def analyze_resume(self, resume_content: str, skills: Optional[str] = None) -> Dict:
        """
        이력서 내용을 분석하여 경력 특성 추출
        
        Args:
            resume_content: 이력서 내용
            skills: 기술/스킬 정보 (JSON 문자열)
        
        Returns:
            분석 결과 딕셔너리
        """
        analysis = {
            "job_categories": [],
            "experience_years": 0,
            "key_skills": [],
            "tech_stack": [],
            "career_keywords": [],
            "strengths": [],
        }
        
        # 1. 직무 카테고리 분석
        analysis["job_categories"] = self._extract_job_categories(resume_content)
        
        # 2. 경력 연차 추정
        analysis["experience_years"] = self._estimate_experience_years(resume_content)
        
        # 3. 핵심 키워드 추출
        analysis["career_keywords"] = self._extract_keywords(resume_content)
        
        # 4. 기술 스택 추출
        if skills:
            try:
                skills_data = json.loads(skills) if isinstance(skills, str) else skills
                analysis["key_skills"] = skills_data if isinstance(skills_data, list) else []
            except:
                analysis["key_skills"] = []
        
        analysis["tech_stack"] = self._extract_tech_stack(resume_content + " " + (skills or ""))
        
        # 5. 강점 분석
        analysis["strengths"] = self._analyze_strengths(resume_content, analysis)
        
        return analysis
    
    def _extract_job_categories(self, text: str) -> List[Dict[str, any]]:
        """직무 카테고리 추출"""
        categories = []
        
        for category, keywords in self.JOB_KEYWORDS.items():
            count = sum(1 for keyword in keywords if keyword in text)
            if count > 0:
                # 정규화된 점수 (0~100)
                score = min(100, int((count / len(keywords)) * 100 * 5))
                categories.append({
                    "category": category,
                    "match_count": count,
                    "score": score
                })
        
        # 점수 높은 순으로 정렬
        categories.sort(key=lambda x: x["score"], reverse=True)
        return categories
    
    def _estimate_experience_years(self, text: str) -> int:
        """경력 연차 추정"""
        years = []
        
        # "X년" 패턴 찾기
        year_patterns = re.findall(r'(\d+)년', text)
        for year_str in year_patterns:
            year = int(year_str)
            if 0 <= year <= 40:  # 합리적인 범위
                years.append(year)
        
        # "YYYY.MM - YYYY.MM" 패턴 찾기
        date_patterns = re.findall(r'(\d{4})\.(\d{1,2})\s*[-~]\s*(\d{4})\.(\d{1,2})', text)
        for start_year, start_month, end_year, end_month in date_patterns:
            duration = int(end_year) - int(start_year)
            if 0 <= duration <= 40:
                years.append(duration)
        
        # 최대값 반환 (가장 긴 경력)
        return max(years) if years else 0
    
    def _extract_keywords(self, text: str, top_n: int = 20) -> List[str]:
        """핵심 키워드 추출"""
        # 한글, 영문, 숫자만 추출
        words = re.findall(r'[가-힣A-Za-z0-9]+', text)
        
        # 불용어 제거
        stopwords = {'을', '를', '이', '가', '은', '는', '의', '에', '으로', '로', 
                    '와', '과', '도', '만', '께서', '에게', '한테', '에서', '부터',
                    '하고', '하여', '및', '등', '등등', '년', '월', '일'}
        
        words = [w for w in words if len(w) > 1 and w not in stopwords]
        
        # 빈도수 계산
        word_counts = Counter(words)
        
        # 상위 N개 추출
        top_keywords = [word for word, count in word_counts.most_common(top_n)]
        
        return top_keywords
    
    def _extract_tech_stack(self, text: str) -> List[Dict[str, str]]:
        """기술 스택 추출"""
        tech_stack = []
        
        for category, techs in self.TECH_KEYWORDS.items():
            found_techs = [tech for tech in techs if tech.lower() in text.lower()]
            for tech in found_techs:
                tech_stack.append({
                    "category": category,
                    "tech": tech
                })
        
        return tech_stack
    
    def _analyze_strengths(self, text: str, analysis: Dict) -> List[str]:
        """강점 분석"""
        strengths = []
        
        # 경력 연차 기반 강점
        years = analysis["experience_years"]
        if years >= 15:
            strengths.append("풍부한 실무 경험")
        elif years >= 10:
            strengths.append("충분한 경력")
        elif years >= 5:
            strengths.append("적정 경력 보유")
        
        # 직무 카테고리 기반
        if len(analysis["job_categories"]) >= 3:
            strengths.append("다양한 직무 경험")
        
        # 기술 스택 기반
        if len(analysis["tech_stack"]) >= 5:
            strengths.append("다양한 기술 스택")
        
        # 성과 키워드 감지
        achievement_keywords = ["달성", "개선", "증가", "성장", "수상", "인정"]
        if any(keyword in text for keyword in achievement_keywords):
            strengths.append("성과 중심 경력")
        
        # 리더십 키워드 감지
        leadership_keywords = ["팀장", "리더", "매니저", "관리", "책임", "총괄"]
        if any(keyword in text for keyword in leadership_keywords):
            strengths.append("리더십 경험")
        
        return strengths
    
    def calculate_job_match_score(self, resume_analysis: Dict, job_requirements: str) -> Dict:
        """
        이력서 분석 결과와 채용공고 요구사항을 비교하여 매칭 점수 계산
        
        Args:
            resume_analysis: analyze_resume() 결과
            job_requirements: 채용공고 요구사항 텍스트
        
        Returns:
            매칭 점수 및 상세 정보
        """
        match_result = {
            "total_score": 0,
            "category_match": 0,
            "skill_match": 0,
            "experience_match": 0,
            "matched_skills": [],
            "missing_skills": [],
            "recommendations": []
        }
        
        # 1. 직무 카테고리 매칭 (40점)
        job_cats = resume_analysis["job_categories"]
        if job_cats:
            top_category = job_cats[0]
            if top_category["category"] in job_requirements:
                match_result["category_match"] = min(40, top_category["score"] * 0.4)
        
        # 2. 스킬 매칭 (40점)
        resume_skills = set(resume_analysis["career_keywords"])
        job_keywords = set(re.findall(r'[가-힣A-Za-z0-9]+', job_requirements))
        
        matched = resume_skills & job_keywords
        match_result["matched_skills"] = list(matched)
        
        if job_keywords:
            skill_ratio = len(matched) / len(job_keywords)
            match_result["skill_match"] = int(skill_ratio * 40)
        
        # 3. 경력 연차 매칭 (20점)
        required_years = self._extract_required_years(job_requirements)
        resume_years = resume_analysis["experience_years"]
        
        if required_years:
            if resume_years >= required_years:
                match_result["experience_match"] = 20
            else:
                match_result["experience_match"] = int((resume_years / required_years) * 20)
        else:
            match_result["experience_match"] = 10  # 요구사항 없으면 기본 점수
        
        # 총점 계산
        match_result["total_score"] = (
            match_result["category_match"] +
            match_result["skill_match"] +
            match_result["experience_match"]
        )
        
        # 추천사항 생성
        if match_result["total_score"] < 50:
            match_result["recommendations"].append("이력서에 관련 키워드를 더 추가하세요")
        if resume_years < required_years:
            match_result["recommendations"].append(f"요구 경력 {required_years}년 대비 부족합니다")
        if len(matched) < 3:
            match_result["recommendations"].append("직무 관련 기술/경험을 더 강조하세요")
        
        return match_result
    
    def _extract_required_years(self, job_requirements: str) -> Optional[int]:
        """채용공고에서 요구 경력 연차 추출"""
        patterns = [
            r'경력\s*(\d+)년\s*이상',
            r'(\d+)년\s*이상\s*경력',
            r'경력\s*(\d+)년',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, job_requirements)
            if match:
                return int(match.group(1))
        
        return None
