"""
자기소개서 생성 서비스 모듈
채용공고와 이력서를 분석하여 맞춤형 자기소개서 생성
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.services.openai_service import get_openai_service

logger = logging.getLogger(__name__)


class CoverLetterService:
    """자기소개서 생성 서비스 클래스"""
    
    def __init__(self):
        """자기소개서 서비스 초기화"""
        self.openai_service = get_openai_service()
        logger.info("CoverLetterService initialized")
    
    def analyze_job_posting(
        self,
        job_posting: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        채용공고 분석 및 핵심 요구사항 추출
        
        Args:
            job_posting: 채용공고 정보
        
        Returns:
            분석 결과 및 핵심 키워드
        """
        logger.info("Analyzing job posting")
        
        # 채용공고 정보 문자열로 변환
        posting_text = f"""
        회사: {job_posting.get('company', 'N/A')}
        직무: {job_posting.get('job_title', 'N/A')}
        직무 내용: {job_posting.get('job_description', 'N/A')}
        자격 요건: {job_posting.get('qualifications', 'N/A')}
        우대사항: {job_posting.get('preferred_qualifications', 'N/A')}
        """
        
        system_prompt = """당신은 채용 전문가입니다.
주어진 채용공고를 분석하여 다음 정보를 추출하세요:

1. 핵심 키워드 (기술, 자격, 경험)
2. 필수 요구사항
3. 우대사항
4. 회사가 원하는 인재상
5. 강조해야 할 포인트

JSON 형식으로 반환하세요."""

        user_prompt = f"다음 채용공고를 분석하세요:\n\n{posting_text}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        result = self.openai_service.generate_completion(
            messages=messages,
            temperature=0.3,
            max_tokens=1000
        )
        
        if result["status"] == "success":
            try:
                import json
                analysis = json.loads(result["content"])
                
                return {
                    "status": "success",
                    "analysis": analysis,
                    "analyzed_at": datetime.now().isoformat(),
                    "tokens_used": result["usage"]["total_tokens"],
                    "cost": result["cost"]
                }
            
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON: {e}")
                return {
                    "status": "error",
                    "error": "분석 결과를 파싱할 수 없습니다",
                    "raw_content": result["content"]
                }
        
        else:
            return {
                "status": "error",
                "error": result.get("error", "알 수 없는 오류")
            }
    
    def generate_cover_letter(
        self,
        job_posting: Dict[str, Any],
        resume_data: Dict[str, Any],
        samples: Optional[List[str]] = None,
        tone: str = "professional"
    ) -> Dict[str, Any]:
        """
        채용공고와 이력서 기반 맞춤형 자기소개서 생성
        
        Args:
            job_posting: 채용공고 정보
            resume_data: 이력서 데이터
            samples: 참고할 자기소개서 샘플 리스트
            tone: 톤 ("professional", "friendly", "passionate")
        
        Returns:
            생성된 자기소개서
        """
        logger.info(f"Generating cover letter with tone: {tone}")
        
        # 톤 설정
        tone_instructions = {
            "professional": "전문적이고 격식있는 어조로 작성하세요.",
            "friendly": "친근하면서도 진지한 어조로 작성하세요.",
            "passionate": "열정적이고 적극적인 어조로 작성하세요."
        }
        
        system_prompt = f"""당신은 50대 이상 시니어 구직자를 위한 자기소개서 작성 전문가입니다.

작성 원칙:
1. 경력의 깊이와 전문성 강조
2. 실무 노하우와 문제해결 능력 부각
3. 멘토링 및 팀 관리 경험 포함
4. 열정과 학습 의지 표현
5. 구체적인 성과와 수치 활용
6. {tone_instructions.get(tone, tone_instructions['professional'])}

구성:
- 인사말 및 지원 동기 (1-2문단)
- 주요 경력 및 성과 (2-3문단)
- 직무 적합성 및 기여 방안 (1-2문단)
- 마무리 및 포부 (1문단)

총 500-800자 분량으로 작성하세요."""

        # 채용공고 정보
        job_info = f"""
# 채용공고 정보
- 회사: {job_posting.get('company', 'N/A')}
- 직무: {job_posting.get('job_title', 'N/A')}
- 직무 내용: {job_posting.get('job_description', 'N/A')}
- 자격 요건: {job_posting.get('qualifications', 'N/A')}
- 우대사항: {job_posting.get('preferred_qualifications', 'N/A')}
"""
        
        # 이력서 정보
        import json
        resume_summary = json.dumps(resume_data, ensure_ascii=False, indent=2)
        resume_info = f"\n# 지원자 정보\n{resume_summary}"
        
        user_prompt = job_info + resume_info
        
        # 샘플 추가
        if samples and len(samples) > 0:
            samples_text = "\n\n# 참고 자기소개서 샘플\n"
            for i, sample in enumerate(samples[:2], 1):  # 최대 2개
                samples_text += f"\n## 샘플 {i}\n{sample}\n"
            user_prompt += samples_text
        
        user_prompt += "\n\n위 정보를 바탕으로 시니어 구직자를 위한 전문적인 자기소개서를 작성하세요."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        result = self.openai_service.generate_completion(
            messages=messages,
            temperature=0.8,
            max_tokens=1500
        )
        
        if result["status"] == "success":
            return {
                "status": "success",
                "content": result["content"],
                "tone": tone,
                "generated_at": datetime.now().isoformat(),
                "tokens_used": result["usage"]["total_tokens"],
                "cost": result["cost"]
            }
        else:
            return {
                "status": "error",
                "error": result.get("error", "알 수 없는 오류")
            }
    
    def extract_key_points(
        self,
        cover_letter: str
    ) -> Dict[str, Any]:
        """
        자기소개서에서 핵심 포인트 추출
        
        Args:
            cover_letter: 자기소개서 내용
        
        Returns:
            추출된 핵심 포인트
        """
        logger.info("Extracting key points from cover letter")
        
        system_prompt = """당신은 자기소개서 분석 전문가입니다.
주어진 자기소개서에서 다음을 추출하세요:

1. 핵심 강점 (3-5개)
2. 주요 경험/성과
3. 지원 동기
4. 차별화 포인트
5. 개선이 필요한 부분

JSON 형식으로 반환하세요."""

        user_prompt = f"다음 자기소개서를 분석하세요:\n\n{cover_letter}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        result = self.openai_service.generate_completion(
            messages=messages,
            temperature=0.3,
            max_tokens=800
        )
        
        if result["status"] == "success":
            try:
                import json
                key_points = json.loads(result["content"])
                
                return {
                    "status": "success",
                    "key_points": key_points,
                    "tokens_used": result["usage"]["total_tokens"],
                    "cost": result["cost"]
                }
            
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON: {e}")
                return {
                    "status": "error",
                    "error": "핵심 포인트를 파싱할 수 없습니다",
                    "raw_content": result["content"]
                }
        
        else:
            return {
                "status": "error",
                "error": result.get("error", "알 수 없는 오류")
            }
    
    def improve_cover_letter(
        self,
        cover_letter: str,
        feedback: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        자기소개서 개선
        
        Args:
            cover_letter: 원본 자기소개서
            feedback: 개선 방향 피드백 (선택)
        
        Returns:
            개선된 자기소개서
        """
        logger.info("Improving cover letter")
        
        system_prompt = """당신은 자기소개서 컨설턴트입니다.
주어진 자기소개서를 다음 관점에서 개선하세요:

1. 문장 구조 및 가독성 향상
2. 구체성 강화 (모호한 표현 제거)
3. 성과 지표 명확화
4. 맞춤법 및 어법 교정
5. 전문성과 열정의 균형

개선된 자기소개서만 반환하세요."""

        user_prompt = f"다음 자기소개서를 개선하세요:\n\n{cover_letter}"
        
        if feedback:
            user_prompt += f"\n\n개선 방향:\n{feedback}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        result = self.openai_service.generate_completion(
            messages=messages,
            temperature=0.6,
            max_tokens=1500
        )
        
        if result["status"] == "success":
            return {
                "status": "success",
                "original": cover_letter,
                "improved": result["content"],
                "tokens_used": result["usage"]["total_tokens"],
                "cost": result["cost"]
            }
        else:
            return {
                "status": "error",
                "error": result.get("error", "알 수 없는 오류")
            }
    
    def validate_cover_letter(
        self,
        cover_letter: str,
        job_posting: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        자기소개서 검증
        
        Args:
            cover_letter: 검증할 자기소개서
            job_posting: 채용공고 정보 (선택)
        
        Returns:
            검증 결과
        """
        issues = []
        suggestions = []
        
        # 기본 검증
        word_count = len(cover_letter)
        
        if word_count < 300:
            issues.append("자기소개서가 너무 짧습니다 (최소 300자 권장)")
        elif word_count > 1000:
            issues.append("자기소개서가 너무 깁니다 (최대 1000자 권장)")
        
        # 구조 검증
        paragraphs = [p.strip() for p in cover_letter.split('\n\n') if p.strip()]
        
        if len(paragraphs) < 3:
            suggestions.append("문단을 더 나누어 가독성을 높이세요")
        
        # 키워드 검증 (채용공고가 있는 경우)
        if job_posting:
            job_title = job_posting.get('job_title', '')
            if job_title and job_title not in cover_letter:
                suggestions.append(f"직무명 '{job_title}'을 명시적으로 언급하세요")
            
            company = job_posting.get('company', '')
            if company and company not in cover_letter:
                suggestions.append(f"회사명 '{company}'을 언급하세요")
        
        # 수치 포함 여부
        import re
        numbers = re.findall(r'\d+', cover_letter)
        if len(numbers) == 0:
            suggestions.append("구체적인 성과 수치를 포함하세요")
        
        # 점수 계산
        score = 100
        score -= len(issues) * 15
        score -= len(suggestions) * 5
        score = max(0, min(100, score))
        
        return {
            "score": score,
            "word_count": word_count,
            "paragraph_count": len(paragraphs),
            "issues": issues,
            "suggestions": suggestions,
            "is_valid": len(issues) == 0
        }
    
    def generate_variations(
        self,
        job_posting: Dict[str, Any],
        resume_data: Dict[str, Any],
        count: int = 3
    ) -> Dict[str, Any]:
        """
        여러 버전의 자기소개서 생성
        
        Args:
            job_posting: 채용공고 정보
            resume_data: 이력서 데이터
            count: 생성할 버전 수 (최대 3개)
        
        Returns:
            여러 버전의 자기소개서
        """
        logger.info(f"Generating {count} cover letter variations")
        
        tones = ["professional", "friendly", "passionate"]
        variations = []
        total_tokens = 0
        total_cost = 0.0
        
        for i in range(min(count, 3)):
            tone = tones[i]
            result = self.generate_cover_letter(
                job_posting,
                resume_data,
                tone=tone
            )
            
            if result["status"] == "success":
                variations.append({
                    "version": i + 1,
                    "tone": tone,
                    "content": result["content"],
                    "tokens_used": result["tokens_used"],
                    "cost": result["cost"]
                })
                total_tokens += result["tokens_used"]
                total_cost += result["cost"]
            else:
                logger.error(f"Failed to generate variation {i+1}: {result.get('error')}")
        
        return {
            "status": "success" if len(variations) > 0 else "error",
            "variations": variations,
            "total_variations": len(variations),
            "total_tokens_used": total_tokens,
            "total_cost": total_cost
        }


# 싱글톤 인스턴스
_cover_letter_service_instance = None


def get_cover_letter_service() -> CoverLetterService:
    """
    자기소개서 서비스 싱글톤 인스턴스 반환
    
    Returns:
        CoverLetterService 인스턴스
    """
    global _cover_letter_service_instance
    
    if _cover_letter_service_instance is None:
        _cover_letter_service_instance = CoverLetterService()
    
    return _cover_letter_service_instance
