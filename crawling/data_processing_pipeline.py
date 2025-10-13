"""
데이터 처리 통합 모듈
크롤링 -> 텍스트 정제 -> 중복 제거 -> 저장의 전체 파이프라인 관리
"""
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from text_cleaner import TextCleaner
from duplicate_remover import DuplicateRemover
from batch_duplicate_processor import BatchDuplicateProcessor
from database import DatabaseManager


class DataProcessingPipeline:
    """데이터 처리 파이프라인 통합 관리자"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        데이터 처리 파이프라인 초기화
        
        Args:
            config: 설정 딕셔너리
        """
        self.config = config or {}
        
        # 기본 설정
        self.similarity_threshold = self.config.get('similarity_threshold', 0.85)
        self.keep_strategy = self.config.get('keep_strategy', 'most_complete')
        self.enable_text_cleaning = self.config.get('enable_text_cleaning', True)
        self.enable_duplicate_removal = self.config.get('enable_duplicate_removal', True)
        self.batch_size = self.config.get('batch_size', 100)
        
        # 모듈 초기화
        self.text_cleaner = TextCleaner() if self.enable_text_cleaning else None
        self.duplicate_remover = DuplicateRemover(self.similarity_threshold) if self.enable_duplicate_removal else None
        self.batch_processor = BatchDuplicateProcessor(
            similarity_threshold=self.similarity_threshold,
            keep_strategy=self.keep_strategy,
            dry_run=False
        ) if self.enable_duplicate_removal else None
        
        self.db = DatabaseManager()
        
        # 로깅 설정
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # 처리 통계
        self.pipeline_stats = {
            'start_time': None,
            'end_time': None,
            'job_postings_processed': 0,
            'job_postings_cleaned': 0,
            'job_postings_duplicates_removed': 0,
            'cover_letters_processed': 0,
            'cover_letters_cleaned': 0,
            'cover_letters_duplicates_removed': 0,
            'total_processing_time': 0,
            'errors': 0
        }
    
    def process_job_postings(self, job_postings: List[Dict]) -> Tuple[int, int]:
        """
        채용공고 데이터 처리 파이프라인
        
        Args:
            job_postings: 처리할 채용공고 목록
            
        Returns:
            (처리된 수, 성공한 수)
        """
        if not job_postings:
            self.logger.info("처리할 채용공고가 없습니다")
            return 0, 0
        
        self.logger.info(f"채용공고 {len(job_postings)}건 처리 시작")
        
        processed_count = 0
        success_count = 0
        
        try:
            self.db.connect()
            
            for i, job_posting in enumerate(job_postings):
                try:
                    # 1. 텍스트 정제
                    if self.enable_text_cleaning and self.text_cleaner:
                        cleaned_job = self._clean_job_posting(job_posting)
                        self.pipeline_stats['job_postings_cleaned'] += 1
                    else:
                        cleaned_job = job_posting
                    
                    # 2. 데이터베이스 저장
                    self._save_job_posting(cleaned_job)
                    
                    processed_count += 1
                    success_count += 1
                    
                    if (i + 1) % self.batch_size == 0:
                        self.logger.info(f"채용공고 {i + 1}/{len(job_postings)} 처리 완료")
                        
                        # 배치마다 중복 제거 수행
                        if self.enable_duplicate_removal:
                            self._remove_job_posting_duplicates()
                
                except Exception as e:
                    self.logger.error(f"채용공고 처리 중 오류 (인덱스 {i}): {e}")
                    self.pipeline_stats['errors'] += 1
                    processed_count += 1
                    continue
            
            # 최종 중복 제거
            if self.enable_duplicate_removal and success_count > 0:
                removed_count = self._remove_job_posting_duplicates()
                self.pipeline_stats['job_postings_duplicates_removed'] += removed_count
            
            self.pipeline_stats['job_postings_processed'] = processed_count
            self.logger.info(f"채용공고 처리 완료: {success_count}/{processed_count}")
            
            return processed_count, success_count
            
        finally:
            if self.db.connection:
                self.db.disconnect()
    
    def process_cover_letters(self, cover_letters: List[Dict]) -> Tuple[int, int]:
        """
        자기소개서 데이터 처리 파이프라인
        
        Args:
            cover_letters: 처리할 자기소개서 목록
            
        Returns:
            (처리된 수, 성공한 수)
        """
        if not cover_letters:
            self.logger.info("처리할 자기소개서가 없습니다")
            return 0, 0
        
        self.logger.info(f"자기소개서 {len(cover_letters)}건 처리 시작")
        
        processed_count = 0
        success_count = 0
        
        try:
            self.db.connect()
            
            for i, cover_letter in enumerate(cover_letters):
                try:
                    # 1. 텍스트 정제
                    if self.enable_text_cleaning and self.text_cleaner:
                        cleaned_letter = self._clean_cover_letter(cover_letter)
                        self.pipeline_stats['cover_letters_cleaned'] += 1
                    else:
                        cleaned_letter = cover_letter
                    
                    # 2. 데이터베이스 저장
                    self._save_cover_letter(cleaned_letter)
                    
                    processed_count += 1
                    success_count += 1
                    
                    if (i + 1) % self.batch_size == 0:
                        self.logger.info(f"자기소개서 {i + 1}/{len(cover_letters)} 처리 완료")
                        
                        # 배치마다 중복 제거 수행
                        if self.enable_duplicate_removal:
                            self._remove_cover_letter_duplicates()
                
                except Exception as e:
                    self.logger.error(f"자기소개서 처리 중 오류 (인덱스 {i}): {e}")
                    self.pipeline_stats['errors'] += 1
                    processed_count += 1
                    continue
            
            # 최종 중복 제거
            if self.enable_duplicate_removal and success_count > 0:
                removed_count = self._remove_cover_letter_duplicates()
                self.pipeline_stats['cover_letters_duplicates_removed'] += removed_count
            
            self.pipeline_stats['cover_letters_processed'] = processed_count
            self.logger.info(f"자기소개서 처리 완료: {success_count}/{processed_count}")
            
            return processed_count, success_count
            
        finally:
            if self.db.connection:
                self.db.disconnect()
    
    def _clean_job_posting(self, job_posting: Dict) -> Dict:
        """채용공고 텍스트 정제"""
        cleaned = job_posting.copy()
        
        # 정제할 필드들
        text_fields = ['title', 'main_duties', 'qualifications', 'preferences']
        
        for field in text_fields:
            if field in cleaned and cleaned[field]:
                cleaned[field] = self.text_cleaner.clean_job_posting_text(cleaned[field])
        
        return cleaned
    
    def _clean_cover_letter(self, cover_letter: Dict) -> Dict:
        """자기소개서 텍스트 정제"""
        cleaned = cover_letter.copy()
        
        # 정제할 필드들
        text_fields = ['title', 'content']
        
        for field in text_fields:
            if field in cleaned and cleaned[field]:
                if field == 'content':
                    cleaned[field] = self.text_cleaner.clean_cover_letter_text(cleaned[field])
                else:
                    cleaned[field] = self.text_cleaner.clean_job_posting_text(cleaned[field])
        
        return cleaned
    
    def _save_job_posting(self, job_posting: Dict):
        """채용공고 데이터베이스 저장"""
        # URL 해시 계산 (중복 방지용)
        url_hash = None
        if job_posting.get('url'):
            url_hash = self.duplicate_remover._calculate_hash(job_posting['url']) if self.duplicate_remover else None
        
        insert_query = """
        INSERT INTO mlops.job_postings (
            title, company, location, salary, employment_type, 
            experience, education, main_duties, qualifications, preferences,
            deadline, posted_date, url, url_hash, source, is_senior_friendly,
            created_at, updated_at
        ) VALUES (
            %(title)s, %(company)s, %(location)s, %(salary)s, %(employment_type)s,
            %(experience)s, %(education)s, %(main_duties)s, %(qualifications)s, %(preferences)s,
            %(deadline)s, %(posted_date)s, %(url)s, %(url_hash)s, %(source)s, %(is_senior_friendly)s,
            NOW(), NOW()
        )

        """
        
        params = {
            'title': job_posting.get('title'),
            'company': job_posting.get('company'),
            'location': job_posting.get('location'),
            'salary': job_posting.get('salary'),
            'employment_type': job_posting.get('employment_type'),
            'experience': job_posting.get('experience'),
            'education': job_posting.get('education'),
            'main_duties': job_posting.get('main_duties'),
            'qualifications': job_posting.get('qualifications'),
            'preferences': job_posting.get('preferences'),
            'deadline': job_posting.get('deadline'),
            'posted_date': job_posting.get('posted_date'),
            'url': job_posting.get('url'),
            'url_hash': url_hash,
            'source': job_posting.get('source', 'saramin'),
            'is_senior_friendly': job_posting.get('is_senior_friendly', True)
        }
        
        self.db.execute_query(insert_query, params, fetch=False)
    
    def _save_cover_letter(self, cover_letter: Dict):
        """자기소개서 데이터베이스 저장"""
        # URL 해시 계산 (중복 방지용)
        url_hash = None
        if cover_letter.get('url'):
            url_hash = self.duplicate_remover._calculate_hash(cover_letter['url']) if self.duplicate_remover else None
        
        insert_query = """
        INSERT INTO mlops.cover_letter_samples (
            title, company, position, department, experience_level,
            content, is_passed, application_year, keywords, source,
            url, url_hash, views, likes, created_at, updated_at
        ) VALUES (
            %(title)s, %(company)s, %(position)s, %(department)s, %(experience_level)s,
            %(content)s, %(is_passed)s, %(application_year)s, %(keywords)s, %(source)s,
            %(url)s, %(url_hash)s, %(views)s, %(likes)s, NOW(), NOW()
        )

        """
        
        params = {
            'title': cover_letter.get('title'),
            'company': cover_letter.get('company'),
            'position': cover_letter.get('position'),
            'department': cover_letter.get('department'),
            'experience_level': cover_letter.get('experience_level'),
            'content': cover_letter.get('content'),
            'is_passed': cover_letter.get('is_passed'),
            'application_year': cover_letter.get('application_year'),
            'keywords': f"{{{cover_letter.get('keywords', '')}}}" if cover_letter.get('keywords') else None,
            'source': cover_letter.get('source', 'linkareer'),
            'url': cover_letter.get('url'),
            'url_hash': url_hash,
            'views': cover_letter.get('views', 0),
            'likes': cover_letter.get('likes', 0)
        }
        
        self.db.execute_query(insert_query, params, fetch=False)
    
    def _remove_job_posting_duplicates(self) -> int:
        """채용공고 중복 제거"""
        if not self.enable_duplicate_removal or not self.duplicate_remover:
            return 0
        
        job_duplicates = self.duplicate_remover.detect_job_posting_duplicates()
        if job_duplicates:
            return self.duplicate_remover.remove_job_posting_duplicates(
                job_duplicates, self.keep_strategy
            )
        return 0
    
    def _remove_cover_letter_duplicates(self) -> int:
        """자기소개서 중복 제거"""
        if not self.enable_duplicate_removal or not self.duplicate_remover:
            return 0
        
        cover_duplicates = self.duplicate_remover.detect_cover_letter_duplicates()
        if cover_duplicates:
            return self.duplicate_remover.remove_cover_letter_duplicates(
                cover_duplicates, self.keep_strategy
            )
        return 0
    
    def run_full_pipeline(self, job_postings: List[Dict] = None, 
                         cover_letters: List[Dict] = None) -> Dict:
        """
        전체 데이터 처리 파이프라인 실행
        
        Args:
            job_postings: 처리할 채용공고 목록
            cover_letters: 처리할 자기소개서 목록
            
        Returns:
            처리 결과 통계
        """
        self.pipeline_stats['start_time'] = datetime.now()
        self.logger.info("데이터 처리 파이프라인 시작")
        
        try:
            # 채용공고 처리
            if job_postings:
                job_processed, job_success = self.process_job_postings(job_postings)
                self.logger.info(f"채용공고 처리 완료: {job_success}/{job_processed}")
            
            # 자기소개서 처리
            if cover_letters:
                cover_processed, cover_success = self.process_cover_letters(cover_letters)
                self.logger.info(f"자기소개서 처리 완료: {cover_success}/{cover_processed}")
            
            # 최종 중복 제거 (전체 데이터 대상)
            if self.enable_duplicate_removal and self.batch_processor:
                final_stats = self.batch_processor.process_all_data()
                self.pipeline_stats['job_postings_duplicates_removed'] += final_stats.get('job_duplicates_removed', 0)
                self.pipeline_stats['cover_letters_duplicates_removed'] += final_stats.get('cover_duplicates_removed', 0)
            
            self.pipeline_stats['end_time'] = datetime.now()
            self.pipeline_stats['total_processing_time'] = (
                self.pipeline_stats['end_time'] - self.pipeline_stats['start_time']
            ).total_seconds()
            
            self.logger.info("데이터 처리 파이프라인 완료")
            return self.pipeline_stats
            
        except Exception as e:
            self.logger.error(f"데이터 처리 파이프라인 중 오류: {e}")
            raise
    
    def get_pipeline_statistics(self) -> Dict:
        """파이프라인 처리 통계 반환"""
        return self.pipeline_stats.copy()
    
    def print_pipeline_statistics(self):
        """파이프라인 처리 통계 출력"""
        stats = self.pipeline_stats
        
        if not stats['start_time']:
            print("파이프라인이 실행되지 않았습니다.")
            return
        
        print(f"\n{'='*60}")
        print("데이터 처리 파이프라인 통계")
        print(f"{'='*60}")
        print(f"처리 시작: {stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"처리 완료: {stats['end_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"총 처리 시간: {stats['total_processing_time']:.2f}초")
        print(f"-" * 60)
        print("채용공고:")
        print(f"  - 처리된 수: {stats['job_postings_processed']}건")
        print(f"  - 텍스트 정제: {stats['job_postings_cleaned']}건")
        print(f"  - 중복 제거: {stats['job_postings_duplicates_removed']}건")
        print("-" * 60)
        print("자기소개서:")
        print(f"  - 처리된 수: {stats['cover_letters_processed']}건")
        print(f"  - 텍스트 정제: {stats['cover_letters_cleaned']}건")
        print(f"  - 중복 제거: {stats['cover_letters_duplicates_removed']}건")
        print("-" * 60)
        print(f"총 오류: {stats['errors']}건")
        print(f"총 중복 제거: {stats['job_postings_duplicates_removed'] + stats['cover_letters_duplicates_removed']}건")
        print(f"{'='*60}\n")


def create_sample_data():
    """테스트용 샘플 데이터 생성"""
    
    # 샘플 채용공고 (중복 포함)
    sample_job_postings = [
        {
            'title': '<b>시니어 개발자</b> 모집합니다',
            'company': 'ABC 테크놀로지',
            'location': '서울시 강남구',
            'salary': '5000-7000만원',
            'employment_type': '정규직',
            'experience': '5년 이상',
            'education': '학력무관',
            'main_duties': '<p>웹 애플리케이션 개발 및 유지보수</p><br/>시스템 아키텍처 설계',
            'qualifications': 'Python, Django 경험자 우대',
            'preferences': '장년층 환영',
            'deadline': '2025-11-30',
            'posted_date': '2025-10-01',
            'url': 'https://saramin.co.kr/zf_user/jobs/relay/view?isMypage=no&rec_idx=12345',
            'source': 'saramin',
            'is_senior_friendly': True
        },
        {
            'title': '시니어 개발자 모집합니다',  # 중복 (유사한 제목)
            'company': 'ABC 테크놀로지',
            'location': '서울시 강남구',
            'salary': '5000-7000만원',
            'employment_type': '정규직',
            'experience': '5년 이상',
            'education': '학력무관',
            'main_duties': '웹 애플리케이션 개발 및 유지보수\n시스템 아키텍처 설계',  # 중복 (유사한 내용)
            'qualifications': 'Python, Django 경험자 우대',
            'preferences': '장년층 환영',
            'deadline': '2025-11-30',
            'posted_date': '2025-10-02',
            'url': 'https://saramin.co.kr/zf_user/jobs/relay/view?isMypage=no&rec_idx=12346',
            'source': 'saramin',
            'is_senior_friendly': True
        }
    ]
    
    # 샘플 자기소개서 (중복 포함)
    sample_cover_letters = [
        {
            'title': '시니어 개발자 자기소개서',
            'company': 'XYZ 회사',
            'position': '백엔드 개발자',
            'department': 'IT 개발팀',
            'experience_level': '시니어',
            'content': '<div>저는 <strong>15년간</strong> 개발 경험을 가진 시니어 개발자입니다.</div><p>Python과 Django를 활용한 웹 개발에 전문성을 가지고 있습니다.</p>',
            'is_passed': True,
            'application_year': 2025,
            'keywords': 'Python, Django, 시니어, 경력',
            'source': 'linkareer',
            'url': 'https://linkareer.com/cover-letter/12345',
            'views': 100,
            'likes': 15
        },
        {
            'title': '시니어 개발자 지원서',  # 중복 (유사한 제목)
            'company': 'XYZ 회사',
            'position': '백엔드 개발자',
            'department': 'IT 개발팀',
            'experience_level': '시니어',
            'content': '저는 15년간 개발 경험을 가진 시니어 개발자입니다.\nPython과 Django를 활용한 웹 개발에 전문성을 가지고 있습니다.',  # 중복 (유사한 내용)
            'is_passed': True,
            'application_year': 2025,
            'keywords': 'Python, Django, 시니어, 경력',
            'source': 'linkareer',
            'url': 'https://linkareer.com/cover-letter/12346',
            'views': 80,
            'likes': 10
        }
    ]
    
    return sample_job_postings, sample_cover_letters


def main():
    """데이터 처리 파이프라인 실행 예제"""
    
    # 파이프라인 설정
    pipeline_config = {
        'similarity_threshold': 0.85,
        'keep_strategy': 'most_complete',
        'enable_text_cleaning': True,
        'enable_duplicate_removal': True,
        'batch_size': 50
    }
    
    # 파이프라인 생성
    pipeline = DataProcessingPipeline(pipeline_config)
    
    print("데이터 처리 파이프라인 시작...")
    print("설정:")
    for key, value in pipeline_config.items():
        print(f"  {key}: {value}")
    
    try:
        # 샘플 데이터 생성
        job_postings, cover_letters = create_sample_data()
        
        print(f"\n처리 대상 데이터:")
        print(f"  채용공고: {len(job_postings)}건")
        print(f"  자기소개서: {len(cover_letters)}건")
        
        # 전체 파이프라인 실행
        stats = pipeline.run_full_pipeline(
            job_postings=job_postings,
            cover_letters=cover_letters
        )
        
        # 통계 출력
        pipeline.print_pipeline_statistics()
        
    except Exception as e:
        print(f"파이프라인 실행 중 오류: {e}")
        raise
    
    print("데이터 처리 파이프라인 완료!")


if __name__ == "__main__":
    main()