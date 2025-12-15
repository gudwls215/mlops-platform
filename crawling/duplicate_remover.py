"""
중복 데이터 제거 모듈
채용공고와 자기소개서의 중복을 효과적으로 감지하고 제거
"""
import logging
import hashlib
import re
from typing import List, Dict, Set, Tuple, Optional
from datetime import datetime
from difflib import SequenceMatcher
from collections import defaultdict

from database import DatabaseManager


class DuplicateRemover:
    """중복 데이터 제거 및 관리 클래스"""
    
    def __init__(self, similarity_threshold: float = 0.85):
        """
        중복 제거기 초기화
        
        Args:
            similarity_threshold: 유사도 임계값 (0.0-1.0)
        """
        self.similarity_threshold = similarity_threshold
        self.db = DatabaseManager()
        
        # 로깅 설정
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # 통계 정보
        self.stats = {
            'processed': 0,
            'duplicates_found': 0,
            'duplicates_removed': 0,
            'url_duplicates': 0,
            'title_duplicates': 0,
            'content_duplicates': 0,
            'similarity_duplicates': 0
        }
    
    def _normalize_text(self, text: str) -> str:
        """
        텍스트 정규화 (해시 계산용)
        
        Args:
            text: 정규화할 텍스트
            
        Returns:
            정규화된 텍스트
        """
        if not text:
            return ""
        
        # 공백 정규화 및 소문자 변환
        normalized = re.sub(r'\s+', ' ', text.strip().lower())
        
        # 특수문자 제거 (일부 중요한 것은 유지)
        normalized = re.sub(r'[^\w\s\-\.]', '', normalized)
        
        return normalized
    
    def _calculate_hash(self, text: str) -> str:
        """
        텍스트의 MD5 해시 계산
        
        Args:
            text: 해시 계산할 텍스트
            
        Returns:
            MD5 해시값
        """
        if not text:
            return ""
        
        normalized = self._normalize_text(text)
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        두 텍스트 간의 유사도 계산
        
        Args:
            text1: 첫 번째 텍스트
            text2: 두 번째 텍스트
            
        Returns:
            유사도 (0.0-1.0)
        """
        if not text1 or not text2:
            return 0.0
        
        normalized1 = self._normalize_text(text1)
        normalized2 = self._normalize_text(text2)
        
        return SequenceMatcher(None, normalized1, normalized2).ratio()
    
    def _extract_domain(self, url: str) -> str:
        """
        URL에서 도메인 추출
        
        Args:
            url: 전체 URL
            
        Returns:
            도메인명
        """
        if not url:
            return ""
        
        # http:// 또는 https:// 제거
        cleaned = re.sub(r'^https?://', '', url.lower())
        
        # 경로 부분 제거
        domain = cleaned.split('/')[0]
        
        return domain
    
    def _is_url_duplicate(self, url1: str, url2: str) -> bool:
        """
        URL 중복 여부 확인
        
        Args:
            url1: 첫 번째 URL
            url2: 두 번째 URL
            
        Returns:
            중복 여부
        """
        if not url1 or not url2:
            return False
        
        # 완전 일치
        if url1.lower() == url2.lower():
            return True
        
        # 쿼리 파라미터 제거 후 비교
        clean_url1 = url1.lower().split('?')[0].rstrip('/')
        clean_url2 = url2.lower().split('?')[0].rstrip('/')
        
        return clean_url1 == clean_url2
    
    def detect_job_posting_duplicates(self) -> List[Dict]:
        """
        채용공고 중복 감지
        
        Returns:
            중복 그룹 목록
        """
        self.logger.info("채용공고 중복 감지 시작")
        
        self.db.connect()
        
        try:
            # 모든 채용공고 데이터 조회 (source_url 컬럼 사용)
            query = """
            SELECT id, source_url, title, company, description as main_duties, 
                   requirements as qualifications, '' as preferences,
                   created_at, updated_at
            FROM mlops.job_postings
            ORDER BY created_at DESC
            """
            
            job_postings = self.db.execute_query(query)
            self.logger.info(f"총 {len(job_postings)}개 채용공고 분석 중")
            
            if len(job_postings) == 0:
                self.logger.info("분석할 채용공고가 없습니다")
                return []
            
            # 중복 그룹 저장
            duplicate_groups = []
            processed_ids = set()
            
            for i, job1 in enumerate(job_postings):
                if job1['id'] in processed_ids:
                    continue
                
                current_group = [job1]
                processed_ids.add(job1['id'])
                
                for j in range(i + 1, len(job_postings)):
                    job2 = job_postings[j]
                    
                    if job2['id'] in processed_ids:
                        continue
                    
                    is_duplicate = False
                    duplicate_reason = []
                    
                    # URL 중복 체크 (source_url 사용)
                    if self._is_url_duplicate(job1.get('source_url', ''), job2.get('source_url', '')):
                        is_duplicate = True
                        duplicate_reason.append('URL')
                        self.stats['url_duplicates'] += 1
                    
                    # 제목 유사도 체크
                    title_similarity = self._calculate_similarity(
                        job1.get('title', ''), 
                        job2.get('title', '')
                    )
                    
                    if title_similarity >= self.similarity_threshold:
                        # 회사명도 같은 경우에만 제목 중복으로 판단
                        if job1.get('company', '').lower() == job2.get('company', '').lower():
                            is_duplicate = True
                            duplicate_reason.append(f'제목 유사도: {title_similarity:.2f}')
                            self.stats['title_duplicates'] += 1
                    
                    # 상세 내용 유사도 체크 (긴 텍스트인 경우)
                    if (job1.get('main_duties') and job2.get('main_duties') and
                        len(job1['main_duties']) > 100 and len(job2['main_duties']) > 100):
                        
                        content_similarity = self._calculate_similarity(
                            job1.get('main_duties', ''),
                            job2.get('main_duties', '')
                        )
                        
                        if content_similarity >= self.similarity_threshold:
                            is_duplicate = True
                            duplicate_reason.append(f'내용 유사도: {content_similarity:.2f}')
                            self.stats['content_duplicates'] += 1
                    
                    if is_duplicate:
                        current_group.append(job2)
                        processed_ids.add(job2['id'])
                        self.logger.info(f"중복 발견: ID {job1['id']} <-> ID {job2['id']} ({', '.join(duplicate_reason)})")
                
                # 중복이 있는 그룹만 추가
                if len(current_group) > 1:
                    duplicate_groups.append({
                        'group_id': len(duplicate_groups) + 1,
                        'items': current_group,
                        'count': len(current_group)
                    })
                    self.stats['duplicates_found'] += len(current_group) - 1
                
                self.stats['processed'] += 1
            
            self.logger.info(f"채용공고 중복 감지 완료: {len(duplicate_groups)}개 그룹, {self.stats['duplicates_found']}개 중복")
            return duplicate_groups
            
        finally:
            self.db.disconnect()
    
    def detect_cover_letter_duplicates(self) -> List[Dict]:
        """
        자기소개서 중복 감지
        
        Returns:
            중복 그룹 목록
        """
        self.logger.info("자기소개서 중복 감지 시작")
        
        self.db.connect()
        
        try:
            # 모든 자기소개서 데이터 조회
            query = """
            SELECT id, url, title, company, position, content, is_passed,
                   created_at, updated_at
            FROM mlops.cover_letter_samples
            ORDER BY created_at DESC
            """
            
            cover_letters = self.db.execute_query(query)
            self.logger.info(f"총 {len(cover_letters)}개 자기소개서 분석 중")
            
            if len(cover_letters) == 0:
                self.logger.info("분석할 자기소개서가 없습니다")
                return []
            
            # 중복 그룹 저장
            duplicate_groups = []
            processed_ids = set()
            
            for i, letter1 in enumerate(cover_letters):
                if letter1['id'] in processed_ids:
                    continue
                
                current_group = [letter1]
                processed_ids.add(letter1['id'])
                
                for j in range(i + 1, len(cover_letters)):
                    letter2 = cover_letters[j]
                    
                    if letter2['id'] in processed_ids:
                        continue
                    
                    is_duplicate = False
                    duplicate_reason = []
                    
                    # URL 중복 체크
                    if self._is_url_duplicate(letter1.get('url', ''), letter2.get('url', '')):
                        is_duplicate = True
                        duplicate_reason.append('URL')
                        self.stats['url_duplicates'] += 1
                    
                    # 내용 유사도 체크
                    if (letter1.get('content') and letter2.get('content') and
                        len(letter1['content']) > 50 and len(letter2['content']) > 50):
                        
                        content_similarity = self._calculate_similarity(
                            letter1.get('content', ''),
                            letter2.get('content', '')
                        )
                        
                        if content_similarity >= self.similarity_threshold:
                            is_duplicate = True
                            duplicate_reason.append(f'내용 유사도: {content_similarity:.2f}')
                            self.stats['similarity_duplicates'] += 1
                    
                    # 제목과 회사가 같은 경우
                    if (letter1.get('title') and letter2.get('title') and
                        letter1.get('company') and letter2.get('company')):
                        
                        title_similarity = self._calculate_similarity(
                            letter1.get('title', ''),
                            letter2.get('title', '')
                        )
                        
                        if (title_similarity >= 0.9 and 
                            letter1.get('company', '').lower() == letter2.get('company', '').lower()):
                            is_duplicate = True
                            duplicate_reason.append(f'제목+회사 유사: {title_similarity:.2f}')
                    
                    if is_duplicate:
                        current_group.append(letter2)
                        processed_ids.add(letter2['id'])
                        self.logger.info(f"중복 발견: ID {letter1['id']} <-> ID {letter2['id']} ({', '.join(duplicate_reason)})")
                
                # 중복이 있는 그룹만 추가
                if len(current_group) > 1:
                    duplicate_groups.append({
                        'group_id': len(duplicate_groups) + 1,
                        'items': current_group,
                        'count': len(current_group)
                    })
                    self.stats['duplicates_found'] += len(current_group) - 1
                
                self.stats['processed'] += 1
            
            self.logger.info(f"자기소개서 중복 감지 완료: {len(duplicate_groups)}개 그룹, {self.stats['duplicates_found']}개 중복")
            return duplicate_groups
            
        finally:
            self.db.disconnect()
    
    def remove_job_posting_duplicates(self, duplicate_groups: List[Dict], 
                                    keep_strategy: str = 'latest') -> int:
        """
        채용공고 중복 제거
        
        Args:
            duplicate_groups: 중복 그룹 목록
            keep_strategy: 보존 전략 ('latest', 'oldest', 'most_complete')
            
        Returns:
            제거된 레코드 수
        """
        self.logger.info(f"채용공고 중복 제거 시작 (전략: {keep_strategy})")
        
        self.db.connect()
        removed_count = 0
        
        try:
            for group in duplicate_groups:
                items = group['items']
                
                # 보존할 레코드 선택
                if keep_strategy == 'latest':
                    keep_item = max(items, key=lambda x: x['created_at'] or datetime.min)
                elif keep_strategy == 'oldest':
                    keep_item = min(items, key=lambda x: x['created_at'] or datetime.max)
                elif keep_strategy == 'most_complete':
                    # 가장 많은 정보를 가진 레코드 선택
                    keep_item = max(items, key=lambda x: sum([
                        bool(x.get('main_duties')),
                        bool(x.get('qualifications')), 
                        bool(x.get('preferences')),
                        len(x.get('main_duties', '') or '')
                    ]))
                else:
                    keep_item = items[0]  # 기본값
                
                # 나머지 레코드 삭제
                remove_items = [item for item in items if item['id'] != keep_item['id']]
                
                for item in remove_items:
                    delete_query = "DELETE FROM mlops.job_postings WHERE id = %s"
                    self.db.execute_query(delete_query, (item['id'],), fetch=False)
                    removed_count += 1
                    self.logger.info(f"채용공고 ID {item['id']} 삭제 (보존: ID {keep_item['id']})")
            
            # 변경사항 커밋
            self.db.connection.commit()
            self.stats['duplicates_removed'] = removed_count
            
            self.logger.info(f"채용공고 중복 제거 완료: {removed_count}개 레코드 삭제")
            return removed_count
            
        except Exception as e:
            self.db.connection.rollback()
            self.logger.error(f"채용공고 중복 제거 중 오류: {e}")
            raise
        finally:
            self.db.disconnect()
    
    def remove_cover_letter_duplicates(self, duplicate_groups: List[Dict], 
                                     keep_strategy: str = 'latest') -> int:
        """
        자기소개서 중복 제거
        
        Args:
            duplicate_groups: 중복 그룹 목록
            keep_strategy: 보존 전략 ('latest', 'oldest', 'most_complete')
            
        Returns:
            제거된 레코드 수
        """
        self.logger.info(f"자기소개서 중복 제거 시작 (전략: {keep_strategy})")
        
        self.db.connect()
        removed_count = 0
        
        try:
            for group in duplicate_groups:
                items = group['items']
                
                # 보존할 레코드 선택
                if keep_strategy == 'latest':
                    keep_item = max(items, key=lambda x: x['created_at'] or datetime.min)
                elif keep_strategy == 'oldest':
                    keep_item = min(items, key=lambda x: x['created_at'] or datetime.max)
                elif keep_strategy == 'most_complete':
                    # 가장 많은 정보를 가진 레코드 선택
                    keep_item = max(items, key=lambda x: sum([
                        bool(x.get('content')),
                        bool(x.get('is_passed')),
                        len(x.get('content', '') or '')
                    ]))
                else:
                    keep_item = items[0]  # 기본값
                
                # 나머지 레코드 삭제
                remove_items = [item for item in items if item['id'] != keep_item['id']]
                
                for item in remove_items:
                    # 1. 먼저 이 레코드를 참조하는 외래 키 관계들을 업데이트/삭제
                    # job_recommendations의 resume_id를 keep_item으로 변경
                    update_recommendations_query = """
                        UPDATE mlops.job_recommendations 
                        SET resume_id = %s 
                        WHERE resume_id = %s
                    """
                    self.db.execute_query(
                        update_recommendations_query, 
                        (keep_item['id'], item['id']), 
                        fetch=False
                    )
                    
                    # user_interactions는 CASCADE 설정이므로 자동 삭제됨
                    
                    # 2. 이제 안전하게 cover_letter_samples 레코드 삭제
                    delete_query = "DELETE FROM mlops.cover_letter_samples WHERE id = %s"
                    self.db.execute_query(delete_query, (item['id'],), fetch=False)
                    removed_count += 1
                    self.logger.info(f"자기소개서 ID {item['id']} 삭제 (보존: ID {keep_item['id']})")
            
            # 변경사항 커밋
            self.db.connection.commit()
            self.stats['duplicates_removed'] = removed_count
            
            self.logger.info(f"자기소개서 중복 제거 완료: {removed_count}개 레코드 삭제")
            return removed_count
            
        except Exception as e:
            self.db.connection.rollback()
            self.logger.error(f"자기소개서 중복 제거 중 오류: {e}")
            raise
        finally:
            self.db.disconnect()
    
    def add_unique_constraints(self):
        """
        유니크 제약 조건 추가 (중복 방지) - job_postings는 스킵 (source_url에 UNIQUE 제약조건 있음)
        """
        self.logger.info("데이터베이스 유니크 제약 조건 확인")
        
        self.db.connect()
        
        try:
            # job_postings는 source_url에 이미 UNIQUE 제약조건이 있으므로 스킵
            self.logger.info("job_postings: source_url UNIQUE 제약조건 사용 (url_hash 불필요)")
            
            # cover_letter_samples만 처리 (url_hash 컬럼이 이미 있음)
            # 기존 데이터의 해시값 업데이트만 수행
            update_cover_hash = """
            UPDATE mlops.cover_letter_samples 
            SET url_hash = MD5(LOWER(TRIM(url))) 
            WHERE url IS NOT NULL AND (url_hash IS NULL OR url_hash = '')
            """
            
            # cover_letter_samples만 업데이트
            self.db.execute_query(update_cover_hash, fetch=False)
            
            # cover_letter_samples 유니크 인덱스만 생성
            create_cover_index = """
            DO $$ 
            BEGIN 
                IF NOT EXISTS (
                    SELECT 1 FROM pg_indexes 
                    WHERE schemaname = 'mlops' AND tablename = 'cover_letter_samples' 
                    AND indexname = 'idx_cover_letters_url_hash_unique'
                ) THEN
                    CREATE UNIQUE INDEX idx_cover_letters_url_hash_unique 
                    ON mlops.cover_letter_samples(url_hash) 
                    WHERE url_hash IS NOT NULL;
                END IF;
            END $$;
            """
            
            self.db.execute_query(create_cover_index, fetch=False)
            
            self.db.connection.commit()
            self.logger.info("유니크 제약 조건 추가 완료")
            
        except Exception as e:
            self.db.connection.rollback()
            self.logger.error(f"유니크 제약 조건 추가 중 오류: {e}")
            raise
        finally:
            self.db.disconnect()
    
    def get_statistics(self) -> Dict:
        """
        중복 제거 통계 반환
        
        Returns:
            통계 정보 딕셔너리
        """
        return self.stats.copy()
    
    def print_statistics(self):
        """중복 제거 통계 출력"""
        print("\n=== 중복 데이터 제거 통계 ===")
        print(f"처리된 레코드 수: {self.stats['processed']}")
        print(f"발견된 중복 수: {self.stats['duplicates_found']}")
        print(f"제거된 중복 수: {self.stats['duplicates_removed']}")
        print(f"  - URL 중복: {self.stats['url_duplicates']}")
        print(f"  - 제목 중복: {self.stats['title_duplicates']}")
        print(f"  - 내용 중복: {self.stats['content_duplicates']}")
        print(f"  - 유사도 중복: {self.stats['similarity_duplicates']}")
        print("=" * 30)


def main():
    """중복 제거 실행 예제"""
    
    # 중복 제거기 생성
    remover = DuplicateRemover(similarity_threshold=0.85)
    
    print("중복 데이터 제거 시작...")
    
    # 1. 채용공고 중복 감지 및 제거
    job_duplicates = remover.detect_job_posting_duplicates()
    if job_duplicates:
        print(f"\n채용공고 중복 그룹 {len(job_duplicates)}개 발견")
        removed_jobs = remover.remove_job_posting_duplicates(job_duplicates, 'latest')
        print(f"채용공고 {removed_jobs}개 제거 완료")
    else:
        print("채용공고 중복 없음")
    
    # 2. 자기소개서 중복 감지 및 제거  
    cover_duplicates = remover.detect_cover_letter_duplicates()
    if cover_duplicates:
        print(f"\n자기소개서 중복 그룹 {len(cover_duplicates)}개 발견")
        removed_covers = remover.remove_cover_letter_duplicates(cover_duplicates, 'most_complete')
        print(f"자기소개서 {removed_covers}개 제거 완료")
    else:
        print("자기소개서 중복 없음")
    
    # 3. 유니크 제약 조건 추가
    remover.add_unique_constraints()
    
    # 4. 통계 출력
    remover.print_statistics()
    
    print("\n중복 데이터 제거 완료!")


if __name__ == "__main__":
    main()