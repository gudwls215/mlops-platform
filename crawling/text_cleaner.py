#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
텍스트 전처리 및 정제 모듈
HTML 태그 제거, 특수문자 정리, 텍스트 정규화
"""

import re
import html
import unicodedata
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TextCleaner:
    """텍스트 정제 및 전처리 클래스"""
    
    def __init__(self):
        # HTML 태그 제거용 정규표현식
        self.html_tag_pattern = re.compile(r'<[^>]+>')
        
        # 특수문자 패턴들
        self.special_chars_pattern = re.compile(r'[^\w\s가-힣.,!?()[\]{}":;-]')
        self.multiple_spaces_pattern = re.compile(r'\s+')
        self.multiple_newlines_pattern = re.compile(r'\n{3,}')
        
        # 불필요한 문자열 패턴들
        self.unwanted_patterns = [
            re.compile(r'&[a-zA-Z]+;'),  # HTML 엔티티
            re.compile(r'&#\d+;'),       # 숫자형 HTML 엔티티
            re.compile(r'\[.*?\]'),      # 대괄호 내용
            re.compile(r'<.*?>'),        # HTML 태그
            re.compile(r'javascript:.*?;'), # JavaScript 코드
            re.compile(r'style=".*?"'),     # 인라인 스타일
        ]
        
        # 이메일과 URL 패턴
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        
        # 한국어 문장 구분을 위한 패턴
        self.korean_sentence_pattern = re.compile(r'[.!?]+\s+')
        
    def remove_html_tags(self, text: str) -> str:
        """HTML 태그 제거"""
        if not text:
            return ""
        
        try:
            # BeautifulSoup을 사용한 HTML 태그 제거
            soup = BeautifulSoup(text, 'html.parser')
            
            # 스크립트와 스타일 태그 완전 제거
            for script in soup(["script", "style", "meta", "link", "head"]):
                script.decompose()
            
            # 텍스트만 추출
            clean_text = soup.get_text()
            
            # 정규표현식으로 남은 태그 제거
            clean_text = self.html_tag_pattern.sub('', clean_text)
            
            return clean_text.strip()
            
        except Exception as e:
            logger.warning(f"HTML 태그 제거 중 오류: {e}")
            # BeautifulSoup 실패시 정규표현식 사용
            return self.html_tag_pattern.sub('', text).strip()
    
    def decode_html_entities(self, text: str) -> str:
        """HTML 엔티티 디코딩"""
        if not text:
            return ""
        
        try:
            # HTML 엔티티 디코딩
            decoded_text = html.unescape(text)
            
            # 남은 HTML 엔티티 패턴 제거
            for pattern in self.unwanted_patterns[:2]:  # HTML 엔티티 패턴만
                decoded_text = pattern.sub('', decoded_text)
            
            return decoded_text
            
        except Exception as e:
            logger.warning(f"HTML 엔티티 디코딩 중 오류: {e}")
            return text
    
    def normalize_unicode(self, text: str) -> str:
        """유니코드 정규화"""
        if not text:
            return ""
        
        try:
            # NFKC 정규화 (호환성 문자를 정규형으로 변환)
            normalized_text = unicodedata.normalize('NFKC', text)
            return normalized_text
            
        except Exception as e:
            logger.warning(f"유니코드 정규화 중 오류: {e}")
            return text
    
    def remove_special_characters(self, text: str, preserve_punctuation: bool = True) -> str:
        """특수문자 제거"""
        if not text:
            return ""
        
        try:
            if preserve_punctuation:
                # 기본 문장부호는 보존하고 나머지 특수문자만 제거
                clean_text = self.special_chars_pattern.sub('', text)
            else:
                # 모든 특수문자 제거 (한글, 영문, 숫자, 기본 공백만 유지)
                clean_text = re.sub(r'[^\w\s가-힣]', '', text)
            
            return clean_text
            
        except Exception as e:
            logger.warning(f"특수문자 제거 중 오류: {e}")
            return text
    
    def normalize_whitespace(self, text: str) -> str:
        """공백 정규화"""
        if not text:
            return ""
        
        try:
            # 연속된 공백을 하나로 통합
            clean_text = self.multiple_spaces_pattern.sub(' ', text)
            
            # 연속된 개행문자 정리 (최대 2개까지만 허용)
            clean_text = self.multiple_newlines_pattern.sub('\n\n', clean_text)
            
            # 각 줄의 앞뒤 공백 제거
            lines = clean_text.split('\n')
            clean_lines = [line.strip() for line in lines]
            
            # 빈 줄이 3개 이상 연속되지 않도록 제한
            result_lines = []
            empty_count = 0
            
            for line in clean_lines:
                if line == '':
                    empty_count += 1
                    if empty_count <= 2:  # 최대 2개의 빈 줄만 허용
                        result_lines.append(line)
                else:
                    empty_count = 0
                    result_lines.append(line)
            
            return '\n'.join(result_lines).strip()
            
        except Exception as e:
            logger.warning(f"공백 정규화 중 오류: {e}")
            return text.strip()
    
    def remove_unwanted_patterns(self, text: str) -> str:
        """불필요한 패턴 제거"""
        if not text:
            return ""
        
        try:
            clean_text = text
            
            # URL 제거 (선택적)
            clean_text = self.url_pattern.sub('[URL]', clean_text)
            
            # 이메일 마스킹 (선택적)
            clean_text = self.email_pattern.sub('[EMAIL]', clean_text)
            
            # 기타 불필요한 패턴 제거
            for pattern in self.unwanted_patterns[2:]:  # HTML 엔티티 제외한 나머지
                clean_text = pattern.sub('', clean_text)
            
            return clean_text
            
        except Exception as e:
            logger.warning(f"불필요한 패턴 제거 중 오류: {e}")
            return text
    
    def extract_sentences(self, text: str) -> List[str]:
        """문장 단위로 분리"""
        if not text:
            return []
        
        try:
            # 한국어 문장 구분
            sentences = self.korean_sentence_pattern.split(text)
            
            # 빈 문장 제거 및 정리
            clean_sentences = []
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence and len(sentence) > 5:  # 너무 짧은 문장 제외
                    clean_sentences.append(sentence)
            
            return clean_sentences
            
        except Exception as e:
            logger.warning(f"문장 분리 중 오류: {e}")
            return [text]
    
    def clean_job_posting_text(self, text: str) -> str:
        """채용공고 텍스트 전용 정제"""
        if not text:
            return ""
        
        logger.debug(f"채용공고 텍스트 정제 시작: {len(text)} 문자")
        
        # 1. HTML 태그 제거
        clean_text = self.remove_html_tags(text)
        
        # 2. HTML 엔티티 디코딩
        clean_text = self.decode_html_entities(clean_text)
        
        # 3. 유니코드 정규화
        clean_text = self.normalize_unicode(clean_text)
        
        # 4. 불필요한 패턴 제거
        clean_text = self.remove_unwanted_patterns(clean_text)
        
        # 5. 공백 정규화
        clean_text = self.normalize_whitespace(clean_text)
        
        # 6. 특수문자 정리 (문장부호는 유지)
        clean_text = self.remove_special_characters(clean_text, preserve_punctuation=True)
        
        logger.debug(f"채용공고 텍스트 정제 완료: {len(clean_text)} 문자")
        return clean_text
    
    def clean_cover_letter_text(self, text: str) -> str:
        """자기소개서 텍스트 전용 정제"""
        if not text:
            return ""
        
        logger.debug(f"자기소개서 텍스트 정제 시작: {len(text)} 문자")
        
        # 1. HTML 태그 제거
        clean_text = self.remove_html_tags(text)
        
        # 2. HTML 엔티티 디코딩
        clean_text = self.decode_html_entities(clean_text)
        
        # 3. 유니코드 정규화
        clean_text = self.normalize_unicode(clean_text)
        
        # 4. 공백 정규화
        clean_text = self.normalize_whitespace(clean_text)
        
        # 5. 특수문자 정리 (자기소개서는 문장부호 중요하므로 유지)
        clean_text = self.remove_special_characters(clean_text, preserve_punctuation=True)
        
        # 6. URL과 이메일은 제거하지 않고 유지 (자기소개서에서는 의미가 있을 수 있음)
        
        logger.debug(f"자기소개서 텍스트 정제 완료: {len(clean_text)} 문자")
        return clean_text
    
    def validate_cleaned_text(self, original: str, cleaned: str, field_type: str = "general") -> Dict[str, any]:
        """정제된 텍스트의 품질 검증"""
        if not original:
            return {"valid": False, "reason": "원본 텍스트가 비어있음"}
        
        try:
            original_length = len(original)
            cleaned_length = len(cleaned)
            
            # 길이 변화율 계산
            length_ratio = cleaned_length / original_length if original_length > 0 else 0
            
            # 한글 문자 비율 확인
            korean_chars = len(re.findall(r'[가-힣]', cleaned))
            korean_ratio = korean_chars / cleaned_length if cleaned_length > 0 else 0
            
            # 필드 타입별 검증 기준
            if field_type in ["title", "company", "position", "department"]:
                # 짧은 필드용 완화된 기준
                min_length = 2
                min_korean = 0.0
            elif field_type == "content":
                # 긴 내용용 기준
                min_length = 20
                min_korean = 0.1
            else:
                # 일반 기준
                min_length = 3
                min_korean = 0.05
            
            validations = {
                "length_preserved": length_ratio >= 0.1,  # 원본의 10% 이상 유지
                "has_content": cleaned_length >= min_length,
                "korean_content": korean_ratio >= min_korean,
                "no_html_tags": '<' not in cleaned and '>' not in cleaned,
                "proper_encoding": not any(char in cleaned for char in ['�', '\ufffd'])
            }
            
            is_valid = all(validations.values())
            
            return {
                "valid": is_valid,
                "original_length": original_length,
                "cleaned_length": cleaned_length,
                "length_ratio": round(length_ratio, 3),
                "korean_ratio": round(korean_ratio, 3),
                "validations": validations
            }
            
        except Exception as e:
            logger.warning(f"텍스트 품질 검증 중 오류: {e}")
            return {"valid": False, "reason": f"검증 오류: {e}"}

def main():
    """테스트 실행"""
    cleaner = TextCleaner()
    
    # 테스트 케이스
    test_cases = [
        {
            "name": "HTML 태그가 포함된 채용공고",
            "text": """
            <div class="job-description">
                <h2>주요업무</h2>
                <ul>
                    <li>시스템 &amp; 네트워크 관리</li>
                    <li>데이터베이스 운영&nbsp;&nbsp;관리</li>
                </ul>
                <p>자격요건: <strong>10년 이상</strong> 경력자 우대</p>
            </div>
            """,
            "type": "job_posting"
        },
        {
            "name": "특수문자가 많은 자기소개서",
            "text": """
            안녕하십니까!!! 저는 ***김철수***입니다.
            
            [경력사항]
            - IT분야 15년 경력
            - 프로젝트 매니저 역할 수행
            
            감사합니다. ^^
            """,
            "type": "cover_letter"
        }
    ]
    
    print("🧹 텍스트 정제 모듈 테스트")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 테스트 케이스 {i}: {test_case['name']}")
        print("-" * 50)
        
        original_text = test_case['text']
        print(f"원본 텍스트 (길이: {len(original_text)}):")
        print(repr(original_text[:100]) + "..." if len(original_text) > 100 else repr(original_text))
        
        # 정제 실행
        if test_case['type'] == 'job_posting':
            cleaned_text = cleaner.clean_job_posting_text(original_text)
        else:
            cleaned_text = cleaner.clean_cover_letter_text(original_text)
        
        print(f"\n정제된 텍스트 (길이: {len(cleaned_text)}):")
        print(repr(cleaned_text))
        
        # 품질 검증
        validation = cleaner.validate_cleaned_text(original_text, cleaned_text)
        print(f"\n품질 검증: {'✅ 통과' if validation['valid'] else '❌ 실패'}")
        print(f"  - 길이 보존율: {validation.get('length_ratio', 0):.1%}")
        print(f"  - 한글 비율: {validation.get('korean_ratio', 0):.1%}")

if __name__ == "__main__":
    main()