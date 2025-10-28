"""
임베딩 생성 서비스
이력서와 채용공고 텍스트를 벡터로 변환합니다.
"""
import logging
from typing import Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import json

logger = logging.getLogger(__name__)

# 싱글톤 모델 인스턴스
_model: Optional[SentenceTransformer] = None


def get_embedding_model() -> SentenceTransformer:
    """임베딩 모델 로드 (싱글톤)"""
    global _model
    if _model is None:
        logger.info("Sentence-BERT 모델 로딩 시작...")
        model_name = "snunlp/KR-SBERT-V40K-klueNLI-augSTS"
        _model = SentenceTransformer(model_name)
        logger.info(f"모델 로딩 완료. 임베딩 차원: {_model.get_sentence_embedding_dimension()}")
    return _model


def generate_embedding(text: str) -> Optional[str]:
    """
    텍스트를 임베딩 벡터로 변환
    
    Args:
        text: 임베딩할 텍스트 (이력서 content JSON 또는 평문)
        
    Returns:
        임베딩 벡터 문자열 ("[0.1, 0.2, 0.3, ...]" 형태) 또는 None
    """
    try:
        if not text or not text.strip():
            logger.warning("빈 텍스트로 임베딩 생성 시도")
            return None
        
        # JSON 문자열인 경우 파싱하여 텍스트 추출
        processed_text = extract_text_from_resume(text)
        
        if not processed_text:
            logger.warning("텍스트 추출 실패")
            return None
        
        # 임베딩 생성
        model = get_embedding_model()
        embedding = model.encode(processed_text, convert_to_numpy=True)
        
        # 문자열로 변환 (comma-separated values)
        embedding_str = "[" + ",".join(map(str, embedding.tolist())) + "]"
        
        logger.info(f"임베딩 생성 완료 (차원: {len(embedding)})")
        return embedding_str
        
    except Exception as e:
        logger.error(f"임베딩 생성 오류: {e}")
        return None


def extract_text_from_resume(content: str) -> str:
    """
    이력서 content에서 텍스트 추출
    
    Args:
        content: 이력서 content (JSON 문자열 또는 평문)
        
    Returns:
        추출된 텍스트
    """
    try:
        # JSON 파싱 시도
        resume_data = json.loads(content)
        
        # 이력서의 주요 필드에서 텍스트 추출
        text_parts = []
        
        # 기본정보
        if "기본정보" in resume_data:
            info = resume_data["기본정보"]
            if isinstance(info, dict):
                text_parts.extend([
                    info.get("이름", ""),
                    info.get("이메일", ""),
                    info.get("연락처", ""),
                    info.get("주소", "")
                ])
        
        # 학력정보
        if "학력정보" in resume_data:
            edu = resume_data["학력정보"]
            if isinstance(edu, dict):
                text_parts.extend([
                    edu.get("학교명", ""),
                    edu.get("전공", ""),
                    edu.get("학위", "")
                ])
        
        # 경력정보
        if "경력정보" in resume_data:
            careers = resume_data["경력정보"]
            if isinstance(careers, list):
                for career in careers:
                    if isinstance(career, dict):
                        text_parts.extend([
                            career.get("회사명", ""),
                            career.get("직위", ""),
                            career.get("담당업무", ""),
                            career.get("주요성과", "")
                        ])
        
        # 기술스택/자격증
        if "기술스택/자격증" in resume_data:
            skills_certs = resume_data["기술스택/자격증"]
            if isinstance(skills_certs, dict):
                # 기술스택
                if "기술스택" in skills_certs:
                    skills = skills_certs["기술스택"]
                    if isinstance(skills, list):
                        text_parts.extend(skills)
                
                # 자격증
                if "자격증" in skills_certs:
                    certs = skills_certs["자격증"]
                    if isinstance(certs, list):
                        for cert in certs:
                            if isinstance(cert, str):
                                text_parts.append(cert)
                            elif isinstance(cert, dict):
                                text_parts.append(cert.get("자격증명", ""))
        
        # 자기소개
        if "자기소개" in resume_data:
            intro = resume_data["자기소개"]
            if intro:
                text_parts.append(str(intro))
        
        # 텍스트 결합 (빈 문자열 제거)
        combined_text = " ".join([str(part) for part in text_parts if part])
        
        return combined_text.strip()
        
    except json.JSONDecodeError:
        # JSON이 아니면 평문으로 처리
        return content.strip()
    except Exception as e:
        logger.error(f"텍스트 추출 오류: {e}")
        return content.strip()


def parse_embedding(embedding_str: str) -> Optional[np.ndarray]:
    """
    임베딩 문자열을 numpy 배열로 변환
    
    Args:
        embedding_str: "[0.1, 0.2, 0.3, ...]" 형태의 문자열
        
    Returns:
        numpy 배열 또는 None
    """
    try:
        if not embedding_str:
            return None
        
        # 대괄호 제거
        embedding_str = embedding_str.strip('[]')
        
        # 콤마로 분리하여 float 배열 생성
        values = [float(x.strip()) for x in embedding_str.split(',')]
        
        return np.array(values)
        
    except Exception as e:
        logger.error(f"임베딩 파싱 오류: {e}")
        return None
