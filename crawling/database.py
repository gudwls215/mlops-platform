"""
데이터베이스 연동 모듈
"""
import logging
from datetime import datetime
from typing import List, Dict, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd

from config import DATABASE_URL


class DatabaseManager:
    """데이터베이스 관리 클래스"""
    
    def __init__(self, database_url: str = DATABASE_URL):
        self.database_url = database_url
        self.connection = None
        
        # 로깅 설정
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def connect(self):
        """데이터베이스 연결"""
        try:
            self.connection = psycopg2.connect(self.database_url)
            self.logger.info("데이터베이스 연결 성공")
        except Exception as e:
            self.logger.error(f"데이터베이스 연결 실패: {e}")
            raise
    
    def disconnect(self):
        """데이터베이스 연결 해제"""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.logger.info("데이터베이스 연결 해제")
    
    def execute_query(self, query: str, params: tuple = None, fetch: bool = True):
        """쿼리 실행"""
        if not self.connection:
            self.connect()
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                
                if fetch and cursor.description:
                    return cursor.fetchall()
                else:
                    self.connection.commit()
                    return cursor.rowcount
                    
        except Exception as e:
            self.logger.error(f"쿼리 실행 실패: {e}")
            self.connection.rollback()
            raise
    
    def insert_job_posting(self, job_data: Dict) -> int:
        """채용공고 데이터 삽입"""
        try:
            # 중복 확인
            check_query = """
                SELECT id FROM job_postings 
                WHERE url = %s OR (title = %s AND company = %s)
                LIMIT 1
            """
            existing = self.execute_query(
                check_query, 
                (job_data['url'], job_data['title'], job_data['company'])
            )
            
            if existing:
                self.logger.info(f"이미 존재하는 채용공고: {job_data['title']} - {job_data['company']}")
                return existing[0]['id']
            
            # 새 데이터 삽입
            insert_query = """
                INSERT INTO job_postings (
                    title, company, location, salary, employment_type,
                    experience_required, education_required, category,
                    description, requirements, benefits, url, source,
                    deadline, posted_at, tags, is_senior_friendly,
                    created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s
                ) RETURNING id
            """
            
            # 날짜 처리
            posted_at = None
            if job_data.get('posted_date'):
                try:
                    posted_at = datetime.strptime(job_data['posted_date'], '%Y-%m-%d')
                except:
                    pass
            
            deadline = None
            if job_data.get('deadline'):
                try:
                    deadline = datetime.strptime(job_data['deadline'], '%Y-%m-%d')
                except:
                    pass
            
            params = (
                job_data.get('title', ''),
                job_data.get('company', ''),
                job_data.get('location', ''),
                job_data.get('salary', ''),
                job_data.get('employment_type', ''),
                job_data.get('experience', ''),
                job_data.get('education', ''),
                job_data.get('category', ''),
                job_data.get('description', ''),
                job_data.get('requirements', ''),
                job_data.get('benefits', ''),
                job_data.get('url', ''),
                job_data.get('site', ''),
                deadline,
                posted_at,
                job_data.get('tags', []),
                True,  # is_senior_friendly (이미 필터링됨)
                datetime.now(),
                datetime.now()
            )
            
            result = self.execute_query(insert_query, params, fetch=True)
            job_id = result[0]['id']
            
            self.logger.info(f"채용공고 삽입 성공: ID {job_id} - {job_data['title']}")
            return job_id
            
        except Exception as e:
            self.logger.error(f"채용공고 삽입 실패: {e}")
            raise
    
    def bulk_insert_job_postings(self, jobs_data: List[Dict]) -> int:
        """채용공고 데이터 일괄 삽입"""
        if not jobs_data:
            return 0
        
        inserted_count = 0
        
        for job_data in jobs_data:
            try:
                self.insert_job_posting(job_data)
                inserted_count += 1
            except Exception as e:
                self.logger.error(f"개별 삽입 실패: {job_data.get('title', 'Unknown')} - {e}")
                continue
        
        self.logger.info(f"일괄 삽입 완료: {inserted_count}/{len(jobs_data)}개")
        return inserted_count
    
    def get_recent_job_postings(self, limit: int = 100, site: str = None) -> List[Dict]:
        """최근 채용공고 조회"""
        query = """
            SELECT * FROM job_postings
            WHERE is_senior_friendly = true
        """
        params = []
        
        if site:
            query += " AND source = %s"
            params.append(site)
        
        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)
        
        return self.execute_query(query, tuple(params))
    
    def get_job_posting_stats(self) -> Dict:
        """채용공고 통계 조회"""
        queries = {
            'total': "SELECT COUNT(*) as count FROM job_postings WHERE is_senior_friendly = true",
            'by_site': """
                SELECT source, COUNT(*) as count 
                FROM job_postings 
                WHERE is_senior_friendly = true 
                GROUP BY source
            """,
            'by_employment_type': """
                SELECT employment_type, COUNT(*) as count 
                FROM job_postings 
                WHERE is_senior_friendly = true AND employment_type != ''
                GROUP BY employment_type
            """,
            'by_location': """
                SELECT location, COUNT(*) as count 
                FROM job_postings 
                WHERE is_senior_friendly = true AND location != ''
                GROUP BY location 
                ORDER BY count DESC 
                LIMIT 20
            """,
            'recent': """
                SELECT COUNT(*) as count 
                FROM job_postings 
                WHERE is_senior_friendly = true 
                AND created_at >= NOW() - INTERVAL '7 days'
            """
        }
        
        stats = {}
        for key, query in queries.items():
            try:
                result = self.execute_query(query)
                if key == 'total' or key == 'recent':
                    stats[key] = result[0]['count'] if result else 0
                else:
                    stats[key] = result
            except Exception as e:
                self.logger.error(f"통계 조회 실패 ({key}): {e}")
                stats[key] = []
        
        return stats
    
    def cleanup_old_postings(self, days: int = 30) -> int:
        """오래된 채용공고 정리"""
        query = """
            DELETE FROM job_postings 
            WHERE created_at < NOW() - INTERVAL '%s days'
            AND (deadline IS NULL OR deadline < NOW())
        """
        
        try:
            deleted_count = self.execute_query(query % days, fetch=False)
            self.logger.info(f"오래된 채용공고 {deleted_count}개 삭제")
            return deleted_count
        except Exception as e:
            self.logger.error(f"채용공고 정리 실패: {e}")
            return 0
    
    def export_to_csv(self, filename: str, site: str = None) -> bool:
        """CSV 파일로 내보내기"""
        try:
            query = """
                SELECT title, company, location, salary, employment_type,
                       experience_required, education_required, category,
                       url, source, posted_at, deadline, created_at
                FROM job_postings
                WHERE is_senior_friendly = true
            """
            params = []
            
            if site:
                query += " AND source = %s"
                params.append(site)
            
            query += " ORDER BY created_at DESC"
            
            # 데이터 조회
            data = self.execute_query(query, tuple(params) if params else None)
            
            if not data:
                self.logger.warning("내보낼 데이터가 없습니다")
                return False
            
            # DataFrame으로 변환 후 CSV 저장
            df = pd.DataFrame(data)
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            
            self.logger.info(f"CSV 내보내기 완료: {filename} ({len(data)}개 레코드)")
            return True
            
        except Exception as e:
            self.logger.error(f"CSV 내보내기 실패: {e}")
            return False


class CrawlerScheduler:
    """크롤링 스케줄러"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
    
    def schedule_daily_crawling(self):
        """일일 크롤링 스케줄"""
        import schedule
        import time
        
        def run_crawling():
            """크롤링 실행"""
            try:
                from scrapers.saramin_crawler import SaraminCrawler
                
                # 사람인 크롤링
                crawler = SaraminCrawler()
                jobs = crawler.crawl_jobs(max_jobs=50)
                
                if jobs:
                    self.db_manager.bulk_insert_job_postings(jobs)
                    self.logger.info(f"일일 크롤링 완료: {len(jobs)}개 채용공고 수집")
                else:
                    self.logger.warning("크롤링된 채용공고가 없습니다")
                
                # 오래된 데이터 정리
                self.db_manager.cleanup_old_postings(days=30)
                
            except Exception as e:
                self.logger.error(f"일일 크롤링 실패: {e}")
        
        # 매일 오전 9시에 실행
        schedule.every().day.at("09:00").do(run_crawling)
        
        self.logger.info("크롤링 스케줄러 시작 (매일 09:00)")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # 1분마다 체크


def main():
    """테스트 실행"""
    db = DatabaseManager()
    
    try:
        db.connect()
        
        # 통계 조회
        stats = db.get_job_posting_stats()
        print("\n=== 채용공고 통계 ===")
        print(f"총 채용공고 수: {stats['total']}")
        print(f"최근 7일 등록: {stats['recent']}")
        
        print("\n사이트별 분포:")
        for item in stats['by_site']:
            print(f"  {item['source']}: {item['count']}개")
        
        print("\n고용형태별 분포:")
        for item in stats['by_employment_type'][:5]:
            print(f"  {item['employment_type']}: {item['count']}개")
        
        # 최근 채용공고 조회
        recent_jobs = db.get_recent_job_postings(limit=5)
        print(f"\n=== 최근 채용공고 ({len(recent_jobs)}개) ===")
        for job in recent_jobs:
            print(f"- {job['title']} | {job['company']} | {job['location']}")
        
    finally:
        db.disconnect()


if __name__ == "__main__":
    main()