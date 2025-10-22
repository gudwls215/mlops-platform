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
    
    def __init__(self, database_url: str = None):
        # 올바른 패스워드로 DATABASE_URL 설정
        if database_url is None:
            database_url = 'postgresql://postgres:xlxldpa%21%40%23@114.202.2.226:5433/postgres'
        self.database_url = database_url
        self.connection = None
        
        # 로깅 설정
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def connect(self):
        """데이터베이스 연결"""
        try:
            # 락 타임아웃 설정 (10초)
            self.connection = psycopg2.connect(
                self.database_url,
                options='-c statement_timeout=10000 -c lock_timeout=5000'
            )
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
                    result = cursor.fetchall()
                    # INSERT/UPDATE/DELETE 등의 쿼리도 커밋 필요
                    if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                        self.connection.commit()
                    return result
                else:
                    self.connection.commit()
                    return cursor.rowcount
                    
        except Exception as e:
            self.logger.error(f"쿼리 실행 실패: {e}")
            self.connection.rollback()
            raise
    
    def insert_job_posting(self, job_data: Dict) -> int:
        """채용공고 데이터 삽입 (UPSERT 방식으로 개선)"""
        try:
            # UPSERT로 중복 확인과 삽입을 원자적으로 처리
            upsert_query = """
                INSERT INTO mlops.job_postings (
                    title, company, description, requirements, 
                    salary_min, salary_max, location, employment_type,
                    experience_level, skills_required, deadline, source_url,
                    is_active, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (source_url) 
                DO UPDATE SET
                    title = EXCLUDED.title,
                    company = EXCLUDED.company,
                    description = EXCLUDED.description,
                    requirements = EXCLUDED.requirements,
                    updated_at = EXCLUDED.updated_at
                RETURNING id, (xmax = 0) AS inserted
            """
            
            # 날짜 처리
            deadline = None
            if job_data.get('deadline'):
                try:
                    deadline = datetime.strptime(job_data['deadline'], '%Y-%m-%d')
                except:
                    pass
            
            # description과 requirements 생성
            description = job_data.get('main_duties', '') or job_data.get('description', '') or '상세 내용 없음'
            requirements = job_data.get('qualifications', '') or job_data.get('requirements', '') or '자격 요건 없음'
            
            # salary 처리
            salary_min = None
            salary_max = None
            salary_str = job_data.get('salary', '')
            if salary_str and salary_str != '회사 내규에 따름':
                # 급여 파싱 로직 (간단한 예시)
                try:
                    if '~' in salary_str:
                        parts = salary_str.replace('만원', '').split('~')
                        salary_min = int(parts[0].strip()) * 10000
                        salary_max = int(parts[1].strip()) * 10000
                except:
                    pass
            
            params = (
                job_data.get('title', ''),
                job_data.get('company', ''),
                description,
                requirements,
                salary_min,
                salary_max,
                job_data.get('location', ''),
                job_data.get('employment_type', ''),
                job_data.get('experience', ''),
                job_data.get('skills_required', ''),
                deadline,
                job_data.get('url', ''),
                True,  # is_active
                datetime.now(),
                datetime.now()
            )
            
            result = self.execute_query(upsert_query, params, fetch=True)
            job_id = result[0]['id']
            inserted = result[0]['inserted']
            
            if inserted:
                self.logger.info(f"채용공고 신규 삽입 성공: ID {job_id} - {job_data['title']}")
            else:
                self.logger.info(f"기존 채용공고 업데이트: ID {job_id} - {job_data['title']}")
            
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
    
    def insert_cover_letter_sample(self, data: Dict) -> bool:
        """자기소개서 샘플 데이터 삽입"""
        insert_query = """
        INSERT INTO mlops.cover_letter_samples (
            title, company, position, department, experience_level,
            content, is_passed, application_year, keywords,
            url, views, likes, source
        ) VALUES (
            %(title)s, %(company)s, %(position)s, %(department)s, %(experience_level)s,
            %(content)s, %(is_passed)s, %(application_year)s, %(keywords)s,
            %(url)s, %(views)s, %(likes)s, %(source)s
        )
        ON CONFLICT (url) DO UPDATE SET
            title = EXCLUDED.title,
            content = EXCLUDED.content,
            views = EXCLUDED.views,
            likes = EXCLUDED.likes,
            updated_at = CURRENT_TIMESTAMP
        RETURNING id;
        """
        
        try:
            # 기본값 설정
            insert_data = {
                'title': data.get('title', ''),
                'company': data.get('company', ''),
                'position': data.get('position'),
                'department': data.get('department'),
                'experience_level': data.get('experience_level'),
                'content': data.get('content', ''),
                'is_passed': data.get('is_passed'),
                'application_year': data.get('application_year'),
                'keywords': data.get('keywords', []),
                'url': data.get('url'),
                'views': data.get('views', 0),
                'likes': data.get('likes', 0),
                'source': data.get('source', 'linkareer')
            }
            
            # INSERT 쿼리 실행 및 커밋
            if not self.connection:
                self.connect()
            
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(insert_query, insert_data)
                result = cursor.fetchall()
                self.connection.commit()
            
            if result:
                cover_letter_id = result[0]['id']
                self.logger.info(f"자기소개서 저장 성공 - ID: {cover_letter_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"자기소개서 저장 실패: {e}")
            return False
    
    def bulk_insert_cover_letter_samples(self, cover_letters: List[Dict]) -> int:
        """자기소개서 샘플 벌크 삽입"""
        if not cover_letters:
            return 0
            
        successful_inserts = 0
        
        for cover_letter_data in cover_letters:
            if self.insert_cover_letter_sample(cover_letter_data):
                successful_inserts += 1
        
        self.logger.info(f"자기소개서 벌크 삽입 완료: {successful_inserts}/{len(cover_letters)}")
        return successful_inserts
    
    def get_cover_letter_samples_stats(self) -> Dict:
        """자기소개서 샘플 통계 조회"""
        stats_query = """
        SELECT 
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE created_at >= CURRENT_DATE - INTERVAL '7 days') as recent,
            COUNT(*) FILTER (WHERE is_passed = true) as passed,
            COUNT(*) FILTER (WHERE is_passed = false) as failed,
            COUNT(*) FILTER (WHERE application_year >= EXTRACT(YEAR FROM CURRENT_DATE) - 2) as recent_years
        FROM mlops.cover_letter_samples;
        """
        
        company_stats_query = """
        SELECT company, COUNT(*) as count
        FROM mlops.cover_letter_samples
        WHERE company IS NOT NULL AND company != ''
        GROUP BY company
        ORDER BY count DESC
        LIMIT 10;
        """
        
        position_stats_query = """
        SELECT position, COUNT(*) as count
        FROM mlops.cover_letter_samples
        WHERE position IS NOT NULL AND position != ''
        GROUP BY position
        ORDER BY count DESC
        LIMIT 10;
        """
        
        try:
            # 전체 통계
            stats_result = self.execute_query(stats_query, fetch=True)
            stats = stats_result[0] if stats_result else {}
            
            # 회사별 통계
            company_result = self.execute_query(company_stats_query, fetch=True)
            stats['by_company'] = list(company_result) if company_result else []
            
            # 직무별 통계
            position_result = self.execute_query(position_stats_query, fetch=True)
            stats['by_position'] = list(position_result) if position_result else []
            
            return stats
            
        except Exception as e:
            self.logger.error(f"자기소개서 통계 조회 실패: {e}")
            return {}
    
    def save_cover_letter(self, company: str, position: str, year: str, 
                         content: str, link: str, source: str = 'crawler') -> bool:
        """자기소개서 데이터 저장"""
        try:
            # 제목 생성 (회사명 + 직무명 + 연도)
            title = f"{company} {position} 합격자소서 ({year})"
            
            # 중복 확인
            check_query = """
                SELECT id FROM mlops.cover_letter_samples 
                WHERE company = %s AND position = %s AND content = %s
                LIMIT 1
            """
            existing = self.execute_query(check_query, (company, position, content[:100]))
            
            if existing:
                self.logger.info(f"이미 존재하는 자기소개서: {company} - {position}")
                return False
            
            # 새 데이터 삽입
            insert_query = """
                INSERT INTO mlops.cover_letter_samples (
                    title, company, position, content, application_year, url, source,
                    is_passed, views, likes, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING id
            """
            
            current_time = datetime.now()
            
            result = self.execute_query(
                insert_query,
                (
                    title,
                    company,
                    position,
                    content,
                    int(year) if year.isdigit() else datetime.now().year,
                    link,
                    source,
                    True,  # is_passed - 크롤링된 데이터는 합격 자소서로 가정
                    0,     # views
                    0,     # likes
                    current_time,
                    current_time
                ),
                fetch=True
            )
            
            if result:
                self.logger.info(f"자기소개서 저장 성공: {company} - {position}")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"자기소개서 저장 실패: {e}")
            return False

    def search_cover_letters(self, company: str = None, position: str = None, 
                           passed_only: bool = False, limit: int = 10) -> List[Dict]:
        """자기소개서 검색"""
        conditions = []
        params = {}
        
        if company:
            conditions.append("company ILIKE %(company)s")
            params['company'] = f"%{company}%"
        
        if position:
            conditions.append("position ILIKE %(position)s")
            params['position'] = f"%{position}%"
        
        if passed_only:
            conditions.append("is_passed = true")
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        search_query = f"""
        SELECT 
            id, title, company, position, department, experience_level,
            CASE 
                WHEN LENGTH(content) > 200 
                THEN LEFT(content, 200) || '...'
                ELSE content
            END as content_preview,
            is_passed, application_year, views, likes, url, created_at
        FROM mlops.cover_letter_samples
        {where_clause}
        ORDER BY views DESC, likes DESC, created_at DESC
        LIMIT %(limit)s;
        """
        
        params['limit'] = limit
        
        try:
            result = self.execute_query(search_query, params, fetch=True)
            return list(result) if result else []
        except Exception as e:
            self.logger.error(f"자기소개서 검색 실패: {e}")
            return []


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