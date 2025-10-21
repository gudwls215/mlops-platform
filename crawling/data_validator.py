"""
데이터 검증 모듈
크롤링된 데이터의 품질과 무결성을 검증
"""
import re
import logging
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from database import DatabaseManager


class ValidationLevel(Enum):
    """검증 수준"""
    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"


class ValidationResult(Enum):
    """검증 결과"""
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"


@dataclass
class ValidationIssue:
    """검증 이슈"""
    field: str
    issue_type: str
    severity: ValidationResult
    message: str
    suggested_fix: Optional[str] = None


class DataValidator:
    """데이터 검증기"""
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.STANDARD):
        """
        데이터 검증기 초기화
        
        Args:
            validation_level: 검증 수준
        """
        self.validation_level = validation_level
        self.db = DatabaseManager()
        
        # 로깅 설정
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # 검증 규칙 설정
        self._setup_validation_rules()
        
        # 통계 정보
        self.stats = {
            'total_validated': 0,
            'passed': 0,
            'warnings': 0,
            'failed': 0,
            'validation_time': 0
        }
    
    def _setup_validation_rules(self):
        """검증 규칙 설정"""
        
        # 필수 필드 정의
        self.required_job_fields = ['title', 'company', 'url']
        self.required_cover_fields = ['title', 'company', 'content', 'url']
        
        # 텍스트 길이 제한
        self.text_length_limits = {
            'title': {'min': 5, 'max': 200},
            'company': {'min': 2, 'max': 100},
            'main_duties': {'min': 10, 'max': 5000},
            'qualifications': {'min': 5, 'max': 2000},
            'content': {'min': 20, 'max': 10000},
            'url': {'min': 10, 'max': 500}
        }
        
        # 패턴 검증
        self.validation_patterns = {
            'url': re.compile(r'^https?://[^\s<>"{}|\\^`\[\]]+$'),
            'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
            'phone': re.compile(r'^(\d{2,3}-?\d{3,4}-?\d{4}|\d{10,11})$'),
            'company': re.compile(r'^[가-힣a-zA-Z0-9\s\(\)\.&-]+$'),
            'salary_range': re.compile(r'^\d{1,4}(-\d{1,4})?만원?$')
        }
        
        # 금지 키워드 (스팸, 부적절한 내용)
        self.forbidden_keywords = [
            '대출', '투자', '부업', '재택알바', '다단계', 'MLM',
            '성인', '유흥', '도박', '카지노', '불법'
        ]
        
        # 의심스러운 패턴
        self.suspicious_patterns = [
            re.compile(r'(\d{3}-?\d{4}-?\d{4})'),  # 전화번호
            re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),  # 이메일
            re.compile(r'(http[s]?://[^\s]+)'),  # URL
            re.compile(r'(\d+만원|\d+천만원)'),  # 금액 패턴
        ]
    
    def validate_job_posting(self, job_data: Dict) -> Tuple[ValidationResult, List[ValidationIssue]]:
        """
        채용공고 데이터 검증
        
        Args:
            job_data: 검증할 채용공고 데이터
            
        Returns:
            (전체 검증 결과, 이슈 목록)
        """
        issues = []
        
        # 1. 필수 필드 검증
        for field in self.required_job_fields:
            if not job_data.get(field):
                issues.append(ValidationIssue(
                    field=field,
                    issue_type="required_field_missing",
                    severity=ValidationResult.FAIL,
                    message=f"필수 필드 '{field}'가 누락되었습니다.",
                    suggested_fix=f"{field} 값을 제공해주세요."
                ))
        
        # 2. 텍스트 길이 검증
        text_fields = ['title', 'company', 'main_duties', 'qualifications', 'preferences']
        for field in text_fields:
            if job_data.get(field):
                length_issues = self._validate_text_length(field, job_data[field])
                issues.extend(length_issues)
        
        # 3. URL 형식 검증
        if job_data.get('url'):
            url_issues = self._validate_url(job_data['url'])
            issues.extend(url_issues)
        
        # 4. 회사명 검증
        if job_data.get('company'):
            company_issues = self._validate_company_name(job_data['company'])
            issues.extend(company_issues)
        
        # 5. 금지 키워드 검증
        content_fields = ['title', 'main_duties', 'qualifications', 'preferences']
        for field in content_fields:
            if job_data.get(field):
                keyword_issues = self._validate_forbidden_keywords(field, job_data[field])
                issues.extend(keyword_issues)
        
        # 6. 날짜 검증
        date_issues = self._validate_job_dates(job_data)
        issues.extend(date_issues)
        
        # 7. 중복 검증 (선택적)
        if self.validation_level in [ValidationLevel.STANDARD, ValidationLevel.STRICT]:
            duplicate_issues = self._check_job_duplicates(job_data)
            issues.extend(duplicate_issues)
        
        # 전체 검증 결과 결정
        overall_result = self._determine_overall_result(issues)
        
        return overall_result, issues
    
    def validate_cover_letter(self, cover_data: Dict) -> Tuple[ValidationResult, List[ValidationIssue]]:
        """
        자기소개서 데이터 검증
        
        Args:
            cover_data: 검증할 자기소개서 데이터
            
        Returns:
            (전체 검증 결과, 이슈 목록)
        """
        issues = []
        
        # 1. 필수 필드 검증
        for field in self.required_cover_fields:
            if not cover_data.get(field):
                issues.append(ValidationIssue(
                    field=field,
                    issue_type="required_field_missing",
                    severity=ValidationResult.FAIL,
                    message=f"필수 필드 '{field}'가 누락되었습니다.",
                    suggested_fix=f"{field} 값을 제공해주세요."
                ))
        
        # 2. 텍스트 길이 검증
        text_fields = ['title', 'company', 'content']
        for field in text_fields:
            if cover_data.get(field):
                length_issues = self._validate_text_length(field, cover_data[field])
                issues.extend(length_issues)
        
        # 3. URL 형식 검증
        if cover_data.get('url'):
            url_issues = self._validate_url(cover_data['url'])
            issues.extend(url_issues)
        
        # 4. 내용 품질 검증
        if cover_data.get('content'):
            content_issues = self._validate_cover_content_quality(cover_data['content'])
            issues.extend(content_issues)
        
        # 5. 금지 키워드 검증
        content_fields = ['title', 'content']
        for field in content_fields:
            if cover_data.get(field):
                keyword_issues = self._validate_forbidden_keywords(field, cover_data[field])
                issues.extend(keyword_issues)
        
        # 6. 중복 검증 (선택적)
        if self.validation_level in [ValidationLevel.STANDARD, ValidationLevel.STRICT]:
            duplicate_issues = self._check_cover_duplicates(cover_data)
            issues.extend(duplicate_issues)
        
        # 전체 검증 결과 결정
        overall_result = self._determine_overall_result(issues)
        
        return overall_result, issues
    
    def _validate_text_length(self, field: str, text: str) -> List[ValidationIssue]:
        """텍스트 길이 검증"""
        issues = []
        
        if field not in self.text_length_limits:
            return issues
        
        limits = self.text_length_limits[field]
        text_length = len(text.strip())
        
        if text_length < limits['min']:
            issues.append(ValidationIssue(
                field=field,
                issue_type="text_too_short",
                severity=ValidationResult.WARNING,
                message=f"'{field}' 텍스트가 너무 짧습니다. (현재: {text_length}, 최소: {limits['min']})",
                suggested_fix=f"더 자세한 {field} 정보를 제공해주세요."
            ))
        elif text_length > limits['max']:
            issues.append(ValidationIssue(
                field=field,
                issue_type="text_too_long",
                severity=ValidationResult.WARNING,
                message=f"'{field}' 텍스트가 너무 깁니다. (현재: {text_length}, 최대: {limits['max']})",
                suggested_fix=f"{field} 내용을 요약해주세요."
            ))
        
        return issues
    
    def _validate_url(self, url: str) -> List[ValidationIssue]:
        """URL 형식 검증"""
        issues = []
        
        if not self.validation_patterns['url'].match(url):
            issues.append(ValidationIssue(
                field="url",
                issue_type="invalid_url_format",
                severity=ValidationResult.FAIL,
                message="URL 형식이 올바르지 않습니다.",
                suggested_fix="올바른 URL 형식으로 수정해주세요. (예: https://example.com)"
            ))
        
        # URL 중복 검증
        if self.validation_level == ValidationLevel.STRICT:
            try:
                self.db.connect()
                
                # 채용공고 URL 중복 확인
                job_query = "SELECT COUNT(*) as count FROM mlops.job_postings WHERE url = %s"
                job_count = self.db.execute_query(job_query, (url,))[0]['count']
                
                # 자기소개서 URL 중복 확인  
                cover_query = "SELECT COUNT(*) as count FROM mlops.cover_letter_samples WHERE url = %s"
                cover_count = self.db.execute_query(cover_query, (url,))[0]['count']
                
                if job_count > 0 or cover_count > 0:
                    issues.append(ValidationIssue(
                        field="url",
                        issue_type="duplicate_url",
                        severity=ValidationResult.WARNING,
                        message="동일한 URL이 이미 존재합니다.",
                        suggested_fix="URL 중복을 확인하고 필요시 업데이트하세요."
                    ))
                    
            except Exception as e:
                self.logger.error(f"URL 중복 검증 중 오류: {e}")
            finally:
                if self.db.connection:
                    self.db.disconnect()
        
        return issues
    
    def _validate_company_name(self, company: str) -> List[ValidationIssue]:
        """회사명 검증"""
        issues = []
        
        # 패턴 검증
        if not self.validation_patterns['company'].match(company):
            issues.append(ValidationIssue(
                field="company",
                issue_type="invalid_company_format",
                severity=ValidationResult.WARNING,
                message="회사명에 특수문자나 숫자가 과도하게 포함되어 있습니다.",
                suggested_fix="회사명을 정확히 입력해주세요."
            ))
        
        # 길이 검증 (추가)
        if len(company.strip()) < 2:
            issues.append(ValidationIssue(
                field="company",
                issue_type="company_too_short",
                severity=ValidationResult.FAIL,
                message="회사명이 너무 짧습니다.",
                suggested_fix="정확한 회사명을 입력해주세요."
            ))
        
        return issues
    
    def _validate_forbidden_keywords(self, field: str, text: str) -> List[ValidationIssue]:
        """금지 키워드 검증"""
        issues = []
        
        text_lower = text.lower()
        found_keywords = []
        
        for keyword in self.forbidden_keywords:
            if keyword.lower() in text_lower:
                found_keywords.append(keyword)
        
        if found_keywords:
            issues.append(ValidationIssue(
                field=field,
                issue_type="forbidden_keywords",
                severity=ValidationResult.FAIL,
                message=f"금지된 키워드가 발견되었습니다: {', '.join(found_keywords)}",
                suggested_fix="부적절한 내용을 제거해주세요."
            ))
        
        return issues
    
    def _validate_job_dates(self, job_data: Dict) -> List[ValidationIssue]:
        """채용공고 날짜 검증"""
        issues = []
        
        posted_date = job_data.get('posted_date')
        deadline = job_data.get('deadline')
        
        if posted_date and deadline:
            try:
                if isinstance(posted_date, str):
                    posted_date = datetime.strptime(posted_date, '%Y-%m-%d')
                if isinstance(deadline, str):
                    deadline = datetime.strptime(deadline, '%Y-%m-%d')
                
                # 게시일이 마감일보다 늦은 경우
                if posted_date > deadline:
                    issues.append(ValidationIssue(
                        field="posted_date",
                        issue_type="invalid_date_order",
                        severity=ValidationResult.WARNING,
                        message="게시일이 마감일보다 늦습니다.",
                        suggested_fix="날짜를 확인하고 수정해주세요."
                    ))
                
                # 마감일이 과거인 경우
                if deadline < datetime.now() - timedelta(days=30):
                    issues.append(ValidationIssue(
                        field="deadline",
                        issue_type="expired_deadline", 
                        severity=ValidationResult.WARNING,
                        message="마감일이 30일 이상 지났습니다.",
                        suggested_fix="마감일을 확인해주세요."
                    ))
                    
            except (ValueError, TypeError) as e:
                issues.append(ValidationIssue(
                    field="date",
                    issue_type="invalid_date_format",
                    severity=ValidationResult.WARNING,
                    message=f"날짜 형식이 올바르지 않습니다: {e}",
                    suggested_fix="YYYY-MM-DD 형식으로 입력해주세요."
                ))
        
        return issues
    
    def _validate_cover_content_quality(self, content: str) -> List[ValidationIssue]:
        """자기소개서 내용 품질 검증"""
        issues = []
        
        # 문장 수 검증
        sentences = re.split(r'[.!?]+', content.strip())
        sentence_count = len([s for s in sentences if s.strip()])
        
        if sentence_count < 3:
            issues.append(ValidationIssue(
                field="content",
                issue_type="insufficient_content",
                severity=ValidationResult.WARNING,
                message="자기소개서 내용이 너무 간단합니다.",
                suggested_fix="더 자세한 내용을 추가해주세요."
            ))
        
        # 반복 문구 검증
        words = content.split()
        if len(set(words)) / len(words) < 0.5:  # 고유 단어 비율
            issues.append(ValidationIssue(
                field="content",
                issue_type="repetitive_content",
                severity=ValidationResult.WARNING,
                message="반복적인 내용이 많습니다.",
                suggested_fix="다양한 표현으로 내용을 작성해주세요."
            ))
        
        # 의심스러운 패턴 검증
        suspicious_matches = []
        for pattern in self.suspicious_patterns:
            matches = pattern.findall(content)
            if matches:
                suspicious_matches.extend(matches)
        
        if suspicious_matches:
            issues.append(ValidationIssue(
                field="content",
                issue_type="suspicious_pattern",
                severity=ValidationResult.WARNING,
                message=f"의심스러운 패턴이 발견되었습니다: {', '.join(suspicious_matches[:3])}...",
                suggested_fix="개인정보나 연락처가 포함되지 않았는지 확인해주세요."
            ))
        
        return issues
    
    def _check_job_duplicates(self, job_data: Dict) -> List[ValidationIssue]:
        """채용공고 중복 검증"""
        issues = []
        
        # 간단한 중복 검증 (제목과 회사명 기반)
        title = job_data.get('title', '')
        company = job_data.get('company', '')
        
        if not title or not company:
            return issues
        
        try:
            self.db.connect()
            
            query = """
            SELECT COUNT(*) as count 
            FROM mlops.job_postings 
            WHERE LOWER(title) = LOWER(%s) AND LOWER(company) = LOWER(%s)
            """
            
            count = self.db.execute_query(query, (title, company))[0]['count']
            
            if count > 0:
                issues.append(ValidationIssue(
                    field="title",
                    issue_type="potential_duplicate",
                    severity=ValidationResult.WARNING,
                    message="유사한 채용공고가 이미 존재할 수 있습니다.",
                    suggested_fix="중복 여부를 확인해주세요."
                ))
                
        except Exception as e:
            self.logger.error(f"채용공고 중복 검증 중 오류: {e}")
        finally:
            if self.db.connection:
                self.db.disconnect()
        
        return issues
    
    def _check_cover_duplicates(self, cover_data: Dict) -> List[ValidationIssue]:
        """자기소개서 중복 검증"""
        issues = []
        
        # 간단한 중복 검증 (제목과 회사명 기반)
        title = cover_data.get('title', '')
        company = cover_data.get('company', '')
        
        if not title or not company:
            return issues
        
        try:
            self.db.connect()
            
            query = """
            SELECT COUNT(*) as count 
            FROM mlops.cover_letter_samples 
            WHERE LOWER(title) = LOWER(%s) AND LOWER(company) = LOWER(%s)
            """
            
            count = self.db.execute_query(query, (title, company))[0]['count']
            
            if count > 0:
                issues.append(ValidationIssue(
                    field="title",
                    issue_type="potential_duplicate",
                    severity=ValidationResult.WARNING,
                    message="유사한 자기소개서가 이미 존재할 수 있습니다.",
                    suggested_fix="중복 여부를 확인해주세요."
                ))
                
        except Exception as e:
            self.logger.error(f"자기소개서 중복 검증 중 오류: {e}")
        finally:
            if self.db.connection:
                self.db.disconnect()
        
        return issues
    
    def _determine_overall_result(self, issues: List[ValidationIssue]) -> ValidationResult:
        """전체 검증 결과 결정"""
        if not issues:
            return ValidationResult.PASS
        
        has_fail = any(issue.severity == ValidationResult.FAIL for issue in issues)
        has_warning = any(issue.severity == ValidationResult.WARNING for issue in issues)
        
        if has_fail:
            return ValidationResult.FAIL
        elif has_warning:
            return ValidationResult.WARNING
        else:
            return ValidationResult.PASS
    
    def batch_validate(self, data_list: List[Dict], data_type: str) -> Dict[str, Any]:
        """
        배치 데이터 검증
        
        Args:
            data_list: 검증할 데이터 목록
            data_type: 데이터 타입 ('job_posting' 또는 'cover_letter')
            
        Returns:
            검증 결과 통계
        """
        start_time = datetime.now()
        
        results = {
            'total': len(data_list),
            'passed': 0,
            'warnings': 0,
            'failed': 0,
            'issues': [],
            'validation_time': 0
        }
        
        self.logger.info(f"{data_type} {len(data_list)}건 배치 검증 시작")
        
        for i, data in enumerate(data_list):
            try:
                if data_type == 'job_posting':
                    result, issues = self.validate_job_posting(data)
                elif data_type == 'cover_letter':
                    result, issues = self.validate_cover_letter(data)
                else:
                    raise ValueError(f"지원하지 않는 데이터 타입: {data_type}")
                
                # 결과 집계
                if result == ValidationResult.PASS:
                    results['passed'] += 1
                elif result == ValidationResult.WARNING:
                    results['warnings'] += 1
                else:
                    results['failed'] += 1
                
                # 이슈 저장 (처음 10개만)
                if len(results['issues']) < 10 and issues:
                    results['issues'].append({
                        'index': i,
                        'data_id': data.get('id', f'item_{i}'),
                        'issues': [
                            {
                                'field': issue.field,
                                'type': issue.issue_type,
                                'severity': issue.severity.value,
                                'message': issue.message
                            } for issue in issues
                        ]
                    })
                
                if (i + 1) % 100 == 0:
                    self.logger.info(f"검증 진행중: {i + 1}/{len(data_list)}")
                    
            except Exception as e:
                self.logger.error(f"데이터 검증 중 오류 (인덱스 {i}): {e}")
                results['failed'] += 1
        
        end_time = datetime.now()
        results['validation_time'] = (end_time - start_time).total_seconds()
        
        # 통계 업데이트
        self.stats['total_validated'] += results['total']
        self.stats['passed'] += results['passed']
        self.stats['warnings'] += results['warnings']
        self.stats['failed'] += results['failed']
        self.stats['validation_time'] += results['validation_time']
        
        self.logger.info(f"배치 검증 완료: 통과 {results['passed']}, 경고 {results['warnings']}, 실패 {results['failed']}")
        
        return results
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """검증 통계 반환"""
        return self.stats.copy()
    
    def print_validation_report(self, results: Dict[str, Any]):
        """검증 결과 리포트 출력"""
        print(f"\n{'='*50}")
        print("데이터 검증 리포트")
        print(f"{'='*50}")
        print(f"총 검증 데이터: {results['total']}건")
        print(f"통과: {results['passed']}건 ({results['passed']/results['total']*100:.1f}%)")
        print(f"경고: {results['warnings']}건 ({results['warnings']/results['total']*100:.1f}%)")
        print(f"실패: {results['failed']}건 ({results['failed']/results['total']*100:.1f}%)")
        print(f"검증 시간: {results['validation_time']:.2f}초")
        
        if results['issues']:
            print(f"\n주요 이슈 (상위 {len(results['issues'])}개):")
            for issue_data in results['issues']:
                print(f"  [{issue_data['data_id']}]")
                for issue in issue_data['issues']:
                    print(f"    - {issue['field']}: {issue['message']} ({issue['severity']})")
        
        print(f"{'='*50}\n")


def main():
    """데이터 검증 실행 예제"""
    
    # 검증기 생성
    validator = DataValidator(ValidationLevel.STANDARD)
    
    print("데이터 검증 시스템 테스트...")
    
    # 테스트 채용공고 데이터
    test_job = {
        'title': '시니어 Python 개발자 모집',
        'company': 'ABC 테크놀로지',
        'location': '서울시 강남구',
        'main_duties': 'Python 백엔드 개발 및 시스템 아키텍처 설계',
        'qualifications': 'Python 5년 이상 경험, Django/FastAPI 경험자 우대',
        'url': 'https://saramin.co.kr/test-job-123',
        'posted_date': '2025-10-01',
        'deadline': '2025-11-30'
    }
    
    # 테스트 자기소개서 데이터
    test_cover = {
        'title': 'Python 개발자 지원서',
        'company': 'ABC 테크놀로지',
        'content': '저는 15년간 Python 개발 경험을 가진 시니어 개발자입니다. 웹 애플리케이션 개발부터 시스템 아키텍처 설계까지 다양한 경험을 보유하고 있습니다.',
        'url': 'https://linkareer.com/test-cover-123'
    }
    
    # 개별 검증
    print("\n=== 채용공고 검증 ===")
    job_result, job_issues = validator.validate_job_posting(test_job)
    print(f"검증 결과: {job_result.value}")
    if job_issues:
        for issue in job_issues:
            print(f"  {issue.field}: {issue.message} ({issue.severity.value})")
    else:
        print("  이슈 없음")
    
    print("\n=== 자기소개서 검증 ===")
    cover_result, cover_issues = validator.validate_cover_letter(test_cover)
    print(f"검증 결과: {cover_result.value}")
    if cover_issues:
        for issue in cover_issues:
            print(f"  {issue.field}: {issue.message} ({issue.severity.value})")
    else:
        print("  이슈 없음")
    
    # 배치 검증
    print("\n=== 배치 검증 ===")
    job_batch_result = validator.batch_validate([test_job], 'job_posting')
    validator.print_validation_report(job_batch_result)
    
    cover_batch_result = validator.batch_validate([test_cover], 'cover_letter')
    validator.print_validation_report(cover_batch_result)
    
    # 전체 통계
    stats = validator.get_validation_statistics()
    print("전체 검증 통계:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n데이터 검증 완료!")


if __name__ == "__main__":
    main()