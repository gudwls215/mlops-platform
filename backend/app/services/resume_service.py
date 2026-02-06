"""
이력서 생성 서비스 모듈
사용자 입력 또는 음성을 기반으로 이력서 생성
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.services.openai_service import get_openai_service

logger = logging.getLogger(__name__)


class ResumeService:
    """이력서 생성 서비스 클래스"""
    
    def __init__(self):
        """이력서 서비스 초기화"""
        self.openai_service = get_openai_service()
        logger.info("ResumeService initialized")
    
    def extract_resume_data_from_text(
        self,
        text: str,
        source: str = "text"
    ) -> Dict[str, Any]:
        """
        텍스트로부터 구조화된 이력서 데이터 추출
        
        Args:
            text: 입력 텍스트 (음성 변환 텍스트 또는 사용자 입력)
            source: 입력 소스 ("text" 또는 "voice")
        
        Returns:
            구조화된 이력서 데이터
        """
        logger.info(f"Extracting resume data from {source}")
        logger.info(f"Input text length: {len(text) if text else 0}, first 500 chars: {text[:500] if text else 'None'}")
        
        # 입력 검증
        if not text or not text.strip():
            logger.warning("Empty or whitespace-only text provided")
            return {
                "status": "error",
                "error": "입력 텍스트가 비어있습니다. 이력서 정보를 입력해주세요.",
                "error_code": "EMPTY_INPUT"
            }
        
        # GPT-4o-mini 프롬프트 작성 (명확한 JSON 출력 요구)
        system_prompt = """당신은 이력서 작성 전문가입니다.
주어진 텍스트에서 이력서에 필요한 정보를 추출하여 JSON 형식으로 구조화하세요.

추출해야 할 정보:
- 기본정보: 이름, 연락처, 이메일, 주소
- 경력정보: 회사명, 직위, 재직기간, 담당업무, 주요성과
- 학력정보: 학교명, 전공, 졸업연도, 학위
- 기술스택/자격증: 기술스택, 자격증명, 취득일
- 자기소개: 간단한 자기소개 또는 경력 요약

중요: 응답은 반드시 순수한 JSON만 출력하세요. 
- 코드 블록(```)을 사용하지 마세요
- 추가 설명을 포함하지 마세요
- 정보가 없는 필드는 null로 설정하세요"""

        user_prompt = f"""다음 텍스트에서 이력서 정보를 추출하여 JSON으로 반환하세요:

텍스트:
{text}

출력 형식:
{{
  "기본정보": {{"이름": "...", "연락처": "...", "이메일": "...", "주소": "..."}},
  "경력정보": [{{"회사명": "...", "직위": "...", "재직기간": "...", "담당업무": "...", "주요성과": "..."}}],
  "학력정보": {{"학교명": "...", "전공": "...", "졸업연도": "...", "학위": "..."}},
  "기술스택/자격증": {{"기술스택": ["..."], "자격증": [{{"자격증명": "...", "취득일": "..."}}]}},
  "자기소개": "..."
}}

위 형식으로 순수 JSON만 응답하세요."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # GPT-4 호출 (빈 응답 시 최대 2회 재시도)
        max_retries = 3
        last_error = None
        
        for attempt in range(max_retries):
            logger.info(f"OpenAI API 호출 시도 {attempt + 1}/{max_retries}")
            
            result = self.openai_service.generate_completion(
                messages=messages,
                temperature=0.3,  # 낮은 temperature로 일관성 향상
                max_tokens=2000
            )
            
            if result["status"] == "success":
                content = result["content"]
                
                # 빈 content 체크 - 재시도
                if not content or not content.strip():
                    logger.warning(f"OpenAI returned empty content (attempt {attempt + 1})")
                    last_error = "AI가 빈 응답을 반환했습니다."
                    continue  # 재시도
                
                # 유효한 응답 받음
                break
            else:
                last_error = result.get("error", "알 수 없는 오류")
                logger.warning(f"OpenAI API error (attempt {attempt + 1}): {last_error}")
                continue  # 재시도
        else:
            # 모든 재시도 실패
            logger.error(f"All {max_retries} attempts failed")
            return {
                "status": "error",
                "error": f"{last_error} ({max_retries}회 시도 실패)",
                "raw_content": ""
            }
        
        if result["status"] == "success":
            try:
                import json
                import re
                
                content = result["content"]
                
                # 빈 content 체크 (이미 위에서 확인했지만 안전을 위해)
                if not content or not content.strip():
                    logger.error("OpenAI returned empty content")
                    return {
                        "status": "error",
                        "error": "AI가 빈 응답을 반환했습니다. 다시 시도해주세요.",
                        "raw_content": content or ""
                    }
                
                # 코드 블록 제거 (```json ... ``` 또는 ``` ... ```)
                if "```" in content:
                    # 코드 블록 내용 추출
                    pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
                    matches = re.findall(pattern, content)
                    if matches:
                        content = matches[0]
                    else:
                        # 시작 ``` 만 있는 경우
                        content = re.sub(r'```(?:json)?', '', content)
                
                # 앞뒤 공백 제거
                content = content.strip()
                
                # JSON 파싱
                resume_data = json.loads(content)
                
                return {
                    "status": "success",
                    "data": resume_data,
                    "source": source,
                    "extracted_at": datetime.now().isoformat(),
                    "tokens_used": result["usage"]["total_tokens"],
                    "cost": result["cost"]
                }
            
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON: {e}")
                logger.error(f"Raw content: {result['content'][:500]}")
                return {
                    "status": "error",
                    "error": "응답을 JSON으로 파싱할 수 없습니다",
                    "raw_content": result["content"]
                }
        
        else:
            return {
                "status": "error",
                "error": result.get("error", "알 수 없는 오류")
            }
    
    def refine_voice_text(
        self,
        raw_text: str
    ) -> Dict[str, Any]:
        """
        Whisper STT로 추출된 텍스트를 LLM으로 정제
        - 음성 인식 오류 수정
        - 의미가 이상한 부분 교정
        - 맥락에 맞게 텍스트 정리
        
        Args:
            raw_text: Whisper로 변환된 원본 텍스트
        
        Returns:
            정제된 텍스트와 상태
        """
        logger.info(f"Refining voice text, length: {len(raw_text)}")
        
        if not raw_text or not raw_text.strip():
            return {
                "status": "error",
                "error": "정제할 텍스트가 비어있습니다.",
                "refined_text": ""
            }
        
        system_prompt = """당신은 음성 인식 결과를 교정하는 전문가입니다.
Whisper STT로 변환된 텍스트를 받아 다음을 수행하세요:

1. 음성 인식 오류 수정: 발음이 비슷해서 잘못 인식된 단어를 맥락에 맞게 수정
2. 띄어쓰기 및 문장 부호 교정
3. 의미가 불분명하거나 어색한 표현을 자연스럽게 수정
4. 이력서 관련 용어(회사명, 직위, 기술 등)가 잘못 인식된 경우 올바르게 수정

중요:
- 원래 화자의 의도를 최대한 유지하세요
- 내용을 추가하거나 삭제하지 마세요
- 교정된 텍스트만 출력하세요 (설명 없이)
- 이력서에 관련된 정보(이름, 연락처, 경력, 학력 등)를 특히 주의해서 교정하세요"""

        user_prompt = f"""다음 음성 인식 텍스트를 교정해주세요:

원본 텍스트:
{raw_text}

교정된 텍스트:"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # LLM 호출
        result = self.openai_service.generate_completion(
            messages=messages,
            temperature=0.3,
            max_tokens=2000
        )
        
        if result["status"] == "success":
            refined_text = result["content"].strip()
            
            if not refined_text:
                logger.warning("LLM returned empty refined text, using original")
                return {
                    "status": "success",
                    "refined_text": raw_text,
                    "original_text": raw_text,
                    "was_refined": False
                }
            
            logger.info(f"Text refined successfully. Original: {len(raw_text)} chars, Refined: {len(refined_text)} chars")
            logger.info(f"Original first 200 chars: {raw_text[:200]}")
            logger.info(f"Refined first 200 chars: {refined_text[:200]}")
            
            return {
                "status": "success",
                "refined_text": refined_text,
                "original_text": raw_text,
                "was_refined": True,
                "tokens_used": result["usage"]["total_tokens"]
            }
        else:
            logger.error(f"Failed to refine text: {result.get('error')}")
            return {
                "status": "error",
                "error": result.get("error", "텍스트 정제 실패"),
                "refined_text": raw_text,  # 실패 시 원본 반환
                "original_text": raw_text,
                "was_refined": False
            }
    
    def extract_from_voice_text(
        self,
        voice_text: str
    ) -> Dict[str, Any]:
        """
        음성 변환 텍스트로부터 이력서 데이터 추출
        1단계: LLM으로 음성 인식 오류 정제
        2단계: 정제된 텍스트로 이력서 데이터 추출
        
        Args:
            voice_text: Whisper로 변환된 음성 텍스트
        
        Returns:
            구조화된 이력서 데이터
        """
        logger.info("Processing voice text with refinement step")
        
        # 1단계: 음성 텍스트 정제
        refine_result = self.refine_voice_text(voice_text)
        
        if refine_result["status"] == "error" and not refine_result.get("refined_text"):
            return {
                "status": "error",
                "error": f"텍스트 정제 실패: {refine_result.get('error')}"
            }
        
        refined_text = refine_result.get("refined_text", voice_text)
        
        logger.info(f"Using {'refined' if refine_result.get('was_refined') else 'original'} text for resume extraction")
        
        # 2단계: 이력서 데이터 추출
        extract_result = self.extract_resume_data_from_text(refined_text, source="voice")
        
        # 원본 및 정제 정보 추가
        if extract_result.get("status") == "success":
            extract_result["original_voice_text"] = voice_text
            extract_result["refined_voice_text"] = refined_text
            extract_result["text_was_refined"] = refine_result.get("was_refined", False)
        
        return extract_result
    
    def extract_from_user_input(
        self,
        user_input: str
    ) -> Dict[str, Any]:
        """
        사용자 직접 입력으로부터 이력서 데이터 추출
        
        Args:
            user_input: 사용자가 입력한 텍스트
        
        Returns:
            구조화된 이력서 데이터
        """
        return self.extract_resume_data_from_text(user_input, source="text")
    
    def generate_formatted_resume(
        self,
        resume_data: Dict[str, Any],
        format_type: str = "markdown"
    ) -> Dict[str, Any]:
        """
        구조화된 데이터로부터 포맷팅된 이력서 생성
        
        Args:
            resume_data: 구조화된 이력서 데이터
            format_type: 출력 형식 ("markdown", "html", "text")
        
        Returns:
            포맷팅된 이력서
        """
        logger.info(f"Generating formatted resume in {format_type} format")
        
        # JSON 데이터를 문자열로 변환
        import json
        resume_json = json.dumps(resume_data, ensure_ascii=False, indent=2)
        
        # 포맷에 따른 프롬프트 작성
        format_instructions = {
            "markdown": "마크다운 형식으로 작성하세요. 제목은 ##를 사용하고, 목록은 - 또는 *를 사용하세요.",
            "html": "HTML 형식으로 작성하세요. 시맨틱 태그를 사용하고, 스타일은 인라인으로 추가하세요.",
            "text": "일반 텍스트 형식으로 작성하세요. 읽기 쉽게 섹션을 구분하세요."
        }
        
        system_prompt = f"""당신은 전문 이력서 작성자입니다.
주어진 구조화된 데이터를 바탕으로 시니어(50대 이상) 구직자를 위한 전문적인 이력서를 작성하세요.

작성 지침:
1. 경력의 깊이와 전문성을 강조
2. 구체적인 성과와 수치 포함
3. 리더십과 멘토링 경험 부각
4. 최신 기술 트렌드 적응력 표현
5. 명확하고 간결한 문장 사용

{format_instructions.get(format_type, format_instructions["markdown"])}"""

        user_prompt = f"""다음 데이터를 바탕으로 전문적인 이력서를 작성하세요:

{resume_json}

{format_type.upper()} 형식으로만 응답하세요."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # GPT-4 호출
        result = self.openai_service.generate_completion(
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        )
        
        if result["status"] == "success":
            return {
                "status": "success",
                "content": result["content"],
                "format": format_type,
                "generated_at": datetime.now().isoformat(),
                "tokens_used": result["usage"]["total_tokens"],
                "cost": result["cost"]
            }
        else:
            return {
                "status": "error",
                "error": result.get("error", "알 수 없는 오류")
            }
    
    def enhance_resume_section(
        self,
        section_name: str,
        section_content: str,
        target_job: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        이력서 특정 섹션 개선
        
        Args:
            section_name: 섹션 이름 (예: "경력", "자기소개", "기술")
            section_content: 개선할 섹션 내용
            target_job: 목표 직무 (선택)
        
        Returns:
            개선된 섹션 내용
        """
        logger.info(f"Enhancing resume section: {section_name}")
        
        system_prompt = f"""당신은 이력서 컨설턴트입니다.
주어진 이력서의 "{section_name}" 섹션을 개선하세요.

개선 방향:
1. 구체적인 성과 지표 추가
2. 액션 동사로 시작하는 문장 사용
3. 불필요한 수식어 제거
4. 전문성과 경험 강조
5. 가독성 향상"""

        user_prompt = f"""다음 "{section_name}" 섹션을 개선하세요:

{section_content}"""

        if target_job:
            user_prompt += f"\n\n목표 직무: {target_job}"
            user_prompt += "\n목표 직무에 맞게 최적화하세요."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        result = self.openai_service.generate_completion(
            messages=messages,
            temperature=0.6,
            max_tokens=1000
        )
        
        if result["status"] == "success":
            return {
                "status": "success",
                "original": section_content,
                "enhanced": result["content"],
                "section": section_name,
                "tokens_used": result["usage"]["total_tokens"],
                "cost": result["cost"]
            }
        else:
            return {
                "status": "error",
                "error": result.get("error", "알 수 없는 오류")
            }
    
    def generate_from_conversation(
        self,
        conversation_history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        대화형 입력으로부터 이력서 생성
        
        Args:
            conversation_history: 대화 기록 리스트
                [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]
        
        Returns:
            구조화된 이력서 데이터
        """
        logger.info("Generating resume from conversation")
        
        # 대화 내용을 하나의 텍스트로 합치기
        conversation_text = "\n\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in conversation_history
        ])
        
        return self.extract_resume_data_from_text(
            conversation_text,
            source="conversation"
        )
    
    def validate_resume_data(
        self,
        resume_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        이력서 데이터 유효성 검증
        
        Args:
            resume_data: 검증할 이력서 데이터
        
        Returns:
            검증 결과
        """
        errors = []
        warnings = []
        
        # 필수 필드 확인
        required_fields = ["이름", "name"]
        has_name = any(field in resume_data for field in required_fields)
        if not has_name:
            errors.append("이름 정보가 없습니다")
        
        # 연락처 확인
        contact_fields = ["연락처", "전화번호", "이메일", "contact", "phone", "email"]
        has_contact = any(field in resume_data for field in contact_fields)
        if not has_contact:
            warnings.append("연락처 정보가 없습니다")
        
        # 경력 정보 확인
        career_fields = ["경력", "career", "experience", "work_experience"]
        has_career = any(field in resume_data for field in career_fields)
        if not has_career:
            warnings.append("경력 정보가 없습니다")
        
        # 학력 정보 확인
        education_fields = ["학력", "education"]
        has_education = any(field in resume_data for field in education_fields)
        if not has_education:
            warnings.append("학력 정보가 없습니다")
        
        is_valid = len(errors) == 0
        
        return {
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "completeness_score": self._calculate_completeness(resume_data)
        }
    
    def _calculate_completeness(self, resume_data: Dict[str, Any]) -> float:
        """
        이력서 완성도 점수 계산
        
        Args:
            resume_data: 이력서 데이터
        
        Returns:
            완성도 점수 (0.0 ~ 1.0)
        """
        total_sections = 7  # 기본정보, 연락처, 경력, 학력, 기술, 자격증, 자기소개
        completed_sections = 0
        
        # 각 섹션 체크
        section_checks = [
            (["이름", "name"], 1),
            (["연락처", "전화번호", "이메일", "contact", "phone", "email"], 1),
            (["경력", "career", "experience", "work_experience"], 1),
            (["학력", "education"], 1),
            (["기술", "skills", "기술스택"], 1),
            (["자격증", "certifications", "certificates"], 1),
            (["자기소개", "summary", "introduction"], 1)
        ]
        
        for fields, weight in section_checks:
            if any(field in resume_data for field in fields):
                completed_sections += weight
        
        return completed_sections / total_sections


# 싱글톤 인스턴스
_resume_service_instance = None


def get_resume_service() -> ResumeService:
    """
    이력서 서비스 싱글톤 인스턴스 반환
    
    Returns:
        ResumeService 인스턴스
    """
    global _resume_service_instance
    
    if _resume_service_instance is None:
        _resume_service_instance = ResumeService()
    
    return _resume_service_instance
