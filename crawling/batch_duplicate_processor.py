"""
배치 중복 제거 처리기
크롤링된 데이터의 중복을 자동으로 감지하고 제거하는 배치 프로세서
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from duplicate_remover import DuplicateRemover
from database import DatabaseManager


class BatchDuplicateProcessor:
    """배치 중복 제거 처리기"""
    
    def __init__(self, similarity_threshold: float = 0.85, 
                 keep_strategy: str = 'most_complete',
                 dry_run: bool = False):
        """
        배치 중복 제거 처리기 초기화
        
        Args:
            similarity_threshold: 유사도 임계값
            keep_strategy: 보존 전략
            dry_run: 실제 삭제 없이 테스트만 수행
        """
        self.similarity_threshold = similarity_threshold
        self.keep_strategy = keep_strategy
        self.dry_run = dry_run
        
        self.remover = DuplicateRemover(similarity_threshold)
        self.db = DatabaseManager()
        
        # 로깅 설정
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # 처리 통계
        self.batch_stats = {
            'start_time': None,
            'end_time': None,
            'total_job_postings': 0,
            'total_cover_letters': 0,
            'job_duplicates_removed': 0,
            'cover_duplicates_removed': 0,
            'processing_time': 0
        }
    
    def process_recent_data(self, hours_back: int = 24) -> Dict:
        """
        최근 N시간 내 데이터의 중복 제거
        
        Args:
            hours_back: 몇 시간 전 데이터까지 처리할지
            
        Returns:
            처리 결과 통계
        """
        self.batch_stats['start_time'] = datetime.now()
        self.logger.info(f"최근 {hours_back}시간 데이터 중복 제거 시작")
        
        if self.dry_run:
            self.logger.info("*** DRY RUN 모드: 실제 삭제는 수행하지 않음 ***")
        
        try:
            # 최근 데이터 조회
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            
            self.db.connect()
            
            # 최근 채용공고 수 확인
            job_count_query = """
            SELECT COUNT(*) as count 
            FROM mlops.job_postings 
            WHERE created_at >= %s
            """
            
            job_count = self.db.execute_query(job_count_query, (cutoff_time,))[0]['count']
            self.batch_stats['total_job_postings'] = job_count
            
            # 최근 자기소개서 수 확인
            cover_count_query = """
            SELECT COUNT(*) as count 
            FROM mlops.cover_letter_samples 
            WHERE created_at >= %s
            """
            
            cover_count = self.db.execute_query(cover_count_query, (cutoff_time,))[0]['count']
            self.batch_stats['total_cover_letters'] = cover_count
            
            self.logger.info(f"대상 데이터: 채용공고 {job_count}건, 자기소개서 {cover_count}건")
            
            # 중복 처리
            if job_count > 0:
                self._process_job_duplicates()
            
            if cover_count > 0:
                self._process_cover_duplicates()
            
            self.batch_stats['end_time'] = datetime.now()
            self.batch_stats['processing_time'] = (
                self.batch_stats['end_time'] - self.batch_stats['start_time']
            ).total_seconds()
            
            self.logger.info("배치 중복 제거 완료")
            return self.batch_stats
            
        except Exception as e:
            self.logger.error(f"배치 중복 제거 중 오류: {e}")
            raise
        finally:
            if self.db.connection:
                self.db.disconnect()
    
    def _process_job_duplicates(self):
        """채용공고 중복 처리"""
        self.logger.info("채용공고 중복 감지 및 제거 시작")
        
        # 중복 감지
        job_duplicates = self.remover.detect_job_posting_duplicates()
        
        if job_duplicates:
            self.logger.info(f"채용공고 중복 그룹 {len(job_duplicates)}개 발견")
            
            if not self.dry_run:
                # 실제 제거
                removed_count = self.remover.remove_job_posting_duplicates(
                    job_duplicates, self.keep_strategy
                )
                self.batch_stats['job_duplicates_removed'] = removed_count
                self.logger.info(f"채용공고 {removed_count}개 제거")
            else:
                # 드라이런: 제거 예상 수만 계산
                expected_removals = sum(
                    len(group['items']) - 1 for group in job_duplicates
                )
                self.logger.info(f"[DRY RUN] 채용공고 {expected_removals}개 제거 예정")
                self.batch_stats['job_duplicates_removed'] = 0
        else:
            self.logger.info("채용공고 중복 없음")
    
    def _process_cover_duplicates(self):
        """자기소개서 중복 처리"""
        self.logger.info("자기소개서 중복 감지 및 제거 시작")
        
        # 중복 감지
        cover_duplicates = self.remover.detect_cover_letter_duplicates()
        
        if cover_duplicates:
            self.logger.info(f"자기소개서 중복 그룹 {len(cover_duplicates)}개 발견")
            
            if not self.dry_run:
                # 실제 제거
                removed_count = self.remover.remove_cover_letter_duplicates(
                    cover_duplicates, self.keep_strategy
                )
                self.batch_stats['cover_duplicates_removed'] = removed_count
                self.logger.info(f"자기소개서 {removed_count}개 제거")
            else:
                # 드라이런: 제거 예상 수만 계산
                expected_removals = sum(
                    len(group['items']) - 1 for group in cover_duplicates
                )
                self.logger.info(f"[DRY RUN] 자기소개서 {expected_removals}개 제거 예정")
                self.batch_stats['cover_duplicates_removed'] = 0
        else:
            self.logger.info("자기소개서 중복 없음")
    
    def process_all_data(self) -> Dict:
        """
        전체 데이터의 중복 제거
        
        Returns:
            처리 결과 통계
        """
        self.batch_stats['start_time'] = datetime.now()
        self.logger.info("전체 데이터 중복 제거 시작")
        
        if self.dry_run:
            self.logger.info("*** DRY RUN 모드: 실제 삭제는 수행하지 않음 ***")
        
        try:
            self.db.connect()
            
            # 전체 데이터 수 확인
            job_count = self.db.execute_query("SELECT COUNT(*) as count FROM mlops.job_postings")[0]['count']
            cover_count = self.db.execute_query("SELECT COUNT(*) as count FROM mlops.cover_letter_samples")[0]['count']
            
            self.batch_stats['total_job_postings'] = job_count
            self.batch_stats['total_cover_letters'] = cover_count
            
            self.logger.info(f"전체 데이터: 채용공고 {job_count}건, 자기소개서 {cover_count}건")
            
            # 중복 처리
            if job_count > 0:
                self._process_job_duplicates()
            
            if cover_count > 0:
                self._process_cover_duplicates()
            
            # 유니크 제약 조건 추가
            if not self.dry_run:
                self.remover.add_unique_constraints()
                self.logger.info("유니크 제약 조건 추가 완료")
            
            self.batch_stats['end_time'] = datetime.now()
            self.batch_stats['processing_time'] = (
                self.batch_stats['end_time'] - self.batch_stats['start_time']
            ).total_seconds()
            
            self.logger.info("전체 데이터 중복 제거 완료")
            return self.batch_stats
            
        except Exception as e:
            self.logger.error(f"전체 데이터 중복 제거 중 오류: {e}")
            raise
        finally:
            if self.db.connection:
                self.db.disconnect()
    
    def cleanup_old_duplicates(self, days_back: int = 30) -> int:
        """
        오래된 중복 데이터 정리
        
        Args:
            days_back: 며칠 전 데이터까지 정리할지
            
        Returns:
            정리된 레코드 수
        """
        self.logger.info(f"{days_back}일 전 데이터 정리 시작")
        
        if self.dry_run:
            self.logger.info("*** DRY RUN 모드: 실제 삭제는 수행하지 않음 ***")
            return 0
        
        cleanup_count = 0
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        try:
            self.db.connect()
            
            # URL 해시가 중복된 오래된 레코드 삭제 (채용공고)
            cleanup_job_query = """
            DELETE FROM mlops.job_postings 
            WHERE id IN (
                SELECT id FROM (
                    SELECT id, ROW_NUMBER() OVER (
                        PARTITION BY url_hash 
                        ORDER BY created_at DESC
                    ) as rn
                    FROM mlops.job_postings 
                    WHERE url_hash IS NOT NULL 
                    AND created_at < %s
                ) t WHERE t.rn > 1
            )
            """
            
            job_cleanup_result = self.db.execute_query(cleanup_job_query, (cutoff_date,), fetch=False)
            
            # URL 해시가 중복된 오래된 레코드 삭제 (자기소개서)
            cleanup_cover_query = """
            DELETE FROM mlops.cover_letter_samples 
            WHERE id IN (
                SELECT id FROM (
                    SELECT id, ROW_NUMBER() OVER (
                        PARTITION BY url_hash 
                        ORDER BY created_at DESC
                    ) as rn
                    FROM mlops.cover_letter_samples 
                    WHERE url_hash IS NOT NULL 
                    AND created_at < %s
                ) t WHERE t.rn > 1
            )
            """
            
            cover_cleanup_result = self.db.execute_query(cleanup_cover_query, (cutoff_date,), fetch=False)
            
            self.db.connection.commit()
            
            self.logger.info(f"오래된 중복 데이터 {cleanup_count}건 정리 완료")
            return cleanup_count
            
        except Exception as e:
            self.db.connection.rollback()
            self.logger.error(f"오래된 데이터 정리 중 오류: {e}")
            raise
        finally:
            if self.db.connection:
                self.db.disconnect()
    
    def get_duplicate_statistics(self) -> Dict:
        """
        현재 데이터베이스의 중복 통계 조회
        
        Returns:
            중복 통계 정보
        """
        stats = {}
        
        try:
            self.db.connect()
            
            # URL 해시 기반 중복 통계
            url_dup_job_query = """
            SELECT COUNT(*) as total_duplicates
            FROM (
                SELECT url_hash, COUNT(*) as dup_count
                FROM mlops.job_postings
                WHERE url_hash IS NOT NULL
                GROUP BY url_hash
                HAVING COUNT(*) > 1
            ) t
            """
            
            url_dup_cover_query = """
            SELECT COUNT(*) as total_duplicates
            FROM (
                SELECT url_hash, COUNT(*) as dup_count
                FROM mlops.cover_letter_samples
                WHERE url_hash IS NOT NULL
                GROUP BY url_hash
                HAVING COUNT(*) > 1
            ) t
            """
            
            job_url_dups = self.db.execute_query(url_dup_job_query)[0]['total_duplicates']
            cover_url_dups = self.db.execute_query(url_dup_cover_query)[0]['total_duplicates']
            
            # 전체 레코드 수
            total_jobs = self.db.execute_query("SELECT COUNT(*) as count FROM mlops.job_postings")[0]['count']
            total_covers = self.db.execute_query("SELECT COUNT(*) as count FROM mlops.cover_letter_samples")[0]['count']
            
            stats = {
                'total_job_postings': total_jobs,
                'total_cover_letters': total_covers,
                'job_url_duplicates': job_url_dups,
                'cover_url_duplicates': cover_url_dups,
                'job_duplicate_rate': (job_url_dups / total_jobs * 100) if total_jobs > 0 else 0,
                'cover_duplicate_rate': (cover_url_dups / total_covers * 100) if total_covers > 0 else 0,
                'scan_time': datetime.now()
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"중복 통계 조회 중 오류: {e}")
            raise
        finally:
            if self.db.connection:
                self.db.disconnect()
    
    def print_batch_statistics(self):
        """배치 처리 통계 출력"""
        if not self.batch_stats['start_time']:
            print("배치 처리가 실행되지 않았습니다.")
            return
        
        print(f"\n{'='*50}")
        print("배치 중복 제거 통계")
        print(f"{'='*50}")
        print(f"처리 시작: {self.batch_stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"처리 완료: {self.batch_stats['end_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"처리 시간: {self.batch_stats['processing_time']:.2f}초")
        print(f"처리 모드: {'DRY RUN' if self.dry_run else 'PRODUCTION'}")
        print(f"-" * 50)
        print(f"총 채용공고: {self.batch_stats['total_job_postings']}건")
        print(f"총 자기소개서: {self.batch_stats['total_cover_letters']}건")
        print(f"제거된 채용공고 중복: {self.batch_stats['job_duplicates_removed']}건")
        print(f"제거된 자기소개서 중복: {self.batch_stats['cover_duplicates_removed']}건")
        print(f"총 제거된 중복: {self.batch_stats['job_duplicates_removed'] + self.batch_stats['cover_duplicates_removed']}건")
        print(f"{'='*50}\n")


def main():
    """배치 중복 제거 실행"""
    
    # 설정
    similarity_threshold = 0.85
    keep_strategy = 'most_complete'  # 'latest', 'oldest', 'most_complete'
    dry_run = False  # True로 설정하면 실제 삭제하지 않고 테스트만
    
    # 배치 처리기 생성
    processor = BatchDuplicateProcessor(
        similarity_threshold=similarity_threshold,
        keep_strategy=keep_strategy,
        dry_run=dry_run
    )
    
    print("배치 중복 제거 프로세스 시작...")
    print(f"유사도 임계값: {similarity_threshold}")
    print(f"보존 전략: {keep_strategy}")
    print(f"드라이런 모드: {dry_run}")
    
    try:
        # 전체 데이터 중복 제거
        stats = processor.process_all_data()
        
        # 통계 출력
        processor.print_batch_statistics()
        
        # 중복 통계 조회
        dup_stats = processor.get_duplicate_statistics()
        print("현재 데이터베이스 중복 현황:")
        print(f"  채용공고 총 {dup_stats['total_job_postings']}건 (URL 중복: {dup_stats['job_url_duplicates']}건, {dup_stats['job_duplicate_rate']:.2f}%)")
        print(f"  자기소개서 총 {dup_stats['total_cover_letters']}건 (URL 중복: {dup_stats['cover_url_duplicates']}건, {dup_stats['cover_duplicate_rate']:.2f}%)")
        
    except Exception as e:
        print(f"배치 중복 제거 중 오류 발생: {e}")
        raise
    
    print("\n배치 중복 제거 완료!")


if __name__ == "__main__":
    main()