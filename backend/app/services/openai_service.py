"""
OpenAI API 서비스 모듈
GPT-4를 활용한 이력서 생성, 자기소개서 작성 등의 AI 기능 제공
"""
import os
import logging
from typing import Optional, Dict, Any, List
from openai import OpenAI, OpenAIError
import tiktoken

logger = logging.getLogger(__name__)


class OpenAIService:
    """OpenAI API 서비스 클래스"""
    
    def __init__(self):
        """OpenAI 클라이언트 초기화"""
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-5-mini")
        self.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "2000"))
        
        if not self.api_key or self.api_key == "your-openai-api-key-here":
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
        
        self.client = OpenAI(api_key=self.api_key)
        
        # 토큰 사용량 추적을 위한 변수
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_cost = 0.0
        
        # GPT 모델 가격 (2024년 기준, 1000 토큰당)
        self.pricing = {
            "gpt-4": {"prompt": 0.03, "completion": 0.06},
            "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
            "gpt-4o-mini": {"prompt": 0.00015, "completion": 0.0006},
            "gpt-3.5-turbo": {"prompt": 0.0015, "completion": 0.002}
        }
        
        logger.info(f"OpenAI Service initialized with model: {self.model}")
    
    def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        """
        텍스트의 토큰 수를 계산
        
        Args:
            text: 토큰 수를 계산할 텍스트
            model: 사용할 모델 (기본값: self.model)
        
        Returns:
            토큰 수
        """
        model = model or self.model
        try:
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))
        except Exception as e:
            logger.warning(f"Failed to count tokens: {e}, using approximate count")
            # 근사값: 1 토큰 ≈ 4 characters (영문 기준)
            return len(text) // 4
    
    def calculate_cost(self, prompt_tokens: int, completion_tokens: int, model: Optional[str] = None) -> float:
        """
        API 호출 비용 계산
        
        Args:
            prompt_tokens: 프롬프트 토큰 수
            completion_tokens: 완성 토큰 수
            model: 사용할 모델 (기본값: self.model)
        
        Returns:
            예상 비용 (USD)
        """
        model = model or self.model
        pricing = self.pricing.get(model, self.pricing["gpt-5-mini"])
        
        prompt_cost = (prompt_tokens / 1000) * pricing["prompt"]
        completion_cost = (completion_tokens / 1000) * pricing["completion"]
        
        return prompt_cost + completion_cost
    
    def update_usage_stats(self, usage: Dict[str, int]):
        """
        토큰 사용량 통계 업데이트
        
        Args:
            usage: OpenAI API 응답의 usage 객체
        """
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        
        cost = self.calculate_cost(prompt_tokens, completion_tokens)
        self.total_cost += cost
        
        logger.info(f"API Usage - Prompt: {prompt_tokens}, Completion: {completion_tokens}, Cost: ${cost:.4f}")
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        토큰 사용량 통계 조회
        
        Returns:
            사용량 통계 딕셔너리
        """
        return {
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_prompt_tokens + self.total_completion_tokens,
            "total_cost_usd": self.total_cost,
            "model": self.model
        }
    
    def reset_usage_stats(self):
        """토큰 사용량 통계 초기화"""
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_cost = 0.0
        logger.info("Usage statistics reset")
    
    def test_connection(self) -> Dict[str, Any]:
        """
        OpenAI API 연결 테스트
        
        Returns:
            테스트 결과 딕셔너리
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello! This is a connection test."}
                ],
                max_tokens=50,
                temperature=0.7
            )
            
            # 사용량 통계 업데이트
            self.update_usage_stats(response.usage.model_dump())
            
            return {
                "status": "success",
                "model": response.model,
                "response": response.choices[0].message.content,
                "usage": response.usage.model_dump(),
                "cost": self.calculate_cost(
                    response.usage.prompt_tokens,
                    response.usage.completion_tokens
                )
            }
        
        except OpenAIError as e:
            logger.error(f"OpenAI API connection test failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def generate_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        GPT 모델을 사용하여 텍스트 생성
        
        Args:
            messages: 대화 메시지 리스트 [{"role": "user", "content": "..."}]
            temperature: 생성 다양성 (0.0 ~ 2.0)
            max_tokens: 최대 토큰 수
            model: 사용할 모델 (기본값: self.model)
        
        Returns:
            생성 결과 딕셔너리
        """
        model = model or self.model
        max_tokens = max_tokens or self.max_tokens
        
        try:
            # 입력 토큰 수 계산
            prompt_text = " ".join([msg["content"] for msg in messages])
            estimated_prompt_tokens = self.count_tokens(prompt_text, model)
            
            logger.info(f"Generating completion with {estimated_prompt_tokens} estimated prompt tokens")
            
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # 사용량 통계 업데이트
            self.update_usage_stats(response.usage.model_dump())
            
            return {
                "status": "success",
                "content": response.choices[0].message.content,
                "model": response.model,
                "usage": response.usage.model_dump(),
                "cost": self.calculate_cost(
                    response.usage.prompt_tokens,
                    response.usage.completion_tokens,
                    model
                ),
                "finish_reason": response.choices[0].finish_reason
            }
        
        except OpenAIError as e:
            logger.error(f"Failed to generate completion: {e}")
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def generate_cover_letter(
        self,
        job_posting: Dict[str, Any],
        user_resume: Dict[str, Any],
        samples: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        채용 공고와 이력서를 기반으로 자기소개서 생성
        
        Args:
            job_posting: 채용 공고 정보
            user_resume: 사용자 이력서 정보
            samples: 참고할 자기소개서 샘플들
        
        Returns:
            생성된 자기소개서
        """
        # 시스템 프롬프트
        system_prompt = """당신은 50세 이상 시니어 구직자를 위한 자기소개서 작성 전문가입니다.
시니어의 풍부한 경험과 강점을 효과적으로 어필하는 자기소개서를 작성해주세요.
- 경력의 깊이와 전문성 강조
- 실무 노하우와 문제해결 능력 부각
- 멘토링 및 팀 관리 경험 포함
- 열정과 학습 의지 표현
- 3-5개 문단, 500-800자 분량"""
        
        # 사용자 프롬프트 구성
        user_prompt = f"""
# 채용 공고
- 회사: {job_posting.get('company', 'N/A')}
- 직무: {job_posting.get('job_title', 'N/A')}
- 직무 내용: {job_posting.get('job_description', 'N/A')}
- 우대사항: {job_posting.get('preferred_qualifications', 'N/A')}

# 지원자 정보
- 경력: {user_resume.get('total_experience', 'N/A')}
- 주요 기술: {user_resume.get('skills', 'N/A')}
- 주요 경력: {user_resume.get('career_summary', 'N/A')}
"""
        
        if samples:
            user_prompt += f"\n# 참고 자기소개서 샘플\n{' '.join(samples[:2])}"
        
        user_prompt += "\n위 정보를 바탕으로 시니어 구직자를 위한 전문적인 자기소개서를 작성해주세요."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return self.generate_completion(messages, temperature=0.8)
    
    def improve_resume(
        self,
        resume_content: str,
        target_job: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        이력서 내용 개선 및 교정
        
        Args:
            resume_content: 개선할 이력서 내용
            target_job: 목표 직무 (선택)
        
        Returns:
            개선된 이력서 내용
        """
        system_prompt = """당신은 시니어 구직자를 위한 이력서 컨설턴트입니다.
다음 관점에서 이력서를 개선해주세요:
1. 경력 하이라이트 명확화
2. 성과 지표 구체화
3. 전문성 강조
4. 맞춤법 및 문장 교정
5. ATS(지원자 추적 시스템) 최적화"""
        
        user_prompt = f"다음 이력서를 개선해주세요:\n\n{resume_content}"
        
        if target_job:
            user_prompt += f"\n\n목표 직무: {target_job}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return self.generate_completion(messages, temperature=0.5)


# 싱글톤 인스턴스
_openai_service_instance = None


def get_openai_service() -> OpenAIService:
    """
    OpenAI 서비스 싱글톤 인스턴스 반환
    
    Returns:
        OpenAIService 인스턴스
    """
    global _openai_service_instance
    
    if _openai_service_instance is None:
        _openai_service_instance = OpenAIService()
    
    return _openai_service_instance
