"""
크롤링 메인 실행기
"""
import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

from database import DatabaseManager
from scrapers.saramin_crawler import SaraminCrawler


def setup_logging(log_level: str = 'INFO'):
    """로깅 설정"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('crawler.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description='MLOps 플랫폼 채용공고 크롤러')
    parser.add_argument('--site', choices=['saramin', 'all'], default='all',
                       help='크롤링할 사이트 선택')
    parser.add_argument('--max-jobs', type=int, default=100,
                       help='최대 크롤링할 채용공고 수')
    parser.add_argument('--export-csv', type=str,
                       help='CSV 파일로 내보낼 파일명')
    parser.add_argument('--stats', action='store_true',
                       help='채용공고 통계 출력')
    parser.add_argument('--cleanup', action='store_true',
                       help='오래된 채용공고 정리')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='로그 레벨')
    
    args = parser.parse_args()
    
    # 로깅 설정
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # 데이터베이스 연결
    db_manager = DatabaseManager()
    
    try:
        db_manager.connect()
        logger.info("크롤링 시작")
        
        # 통계 출력
        if args.stats:
            print_statistics(db_manager)
        
        # 크롤링 실행
        if args.site in ['saramin', 'all']:
            crawl_saramin(db_manager, args.max_jobs)
        
        # 정리 작업
        if args.cleanup:
            db_manager.cleanup_old_postings(days=30)
        
        # CSV 내보내기
        if args.export_csv:
            db_manager.export_to_csv(args.export_csv)
        
        logger.info("크롤링 완료")
        
    except Exception as e:
        logger.error(f"크롤링 실행 중 오류: {e}")
        sys.exit(1)
        
    finally:
        db_manager.disconnect()


def crawl_saramin(db_manager: DatabaseManager, max_jobs: int):
    """사람인 크롤링"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"사람인 크롤링 시작 (최대 {max_jobs}개)")
        
        crawler = SaraminCrawler()
        jobs = crawler.crawl_jobs(max_jobs=max_jobs)
        
        if jobs:
            inserted_count = db_manager.bulk_insert_job_postings(jobs)
            logger.info(f"사람인 크롤링 완료: {inserted_count}개 채용공고 저장")
            
            # 크롤링 결과 요약
            print_crawling_summary(jobs)
        else:
            logger.warning("사람인에서 크롤링된 채용공고가 없습니다")
            
    except Exception as e:
        logger.error(f"사람인 크롤링 실패: {e}")


def print_statistics(db_manager: DatabaseManager):
    """통계 출력"""
    stats = db_manager.get_job_posting_stats()
    
    print("\n" + "="*50)
    print("📊 채용공고 통계")
    print("="*50)
    print(f"총 채용공고 수: {stats['total']:,}개")
    print(f"최근 7일 등록: {stats['recent']:,}개")
    
    if stats['by_site']:
        print("\n🌐 사이트별 분포:")
        for item in stats['by_site']:
            print(f"  • {item['source']}: {item['count']:,}개")
    
    if stats['by_employment_type']:
        print("\n💼 고용형태별 분포:")
        for item in stats['by_employment_type'][:5]:
            print(f"  • {item['employment_type']}: {item['count']:,}개")
    
    if stats['by_location']:
        print("\n📍 지역별 분포 (상위 10개):")
        for item in stats['by_location'][:10]:
            location = item['location'] if item['location'] else '미지정'
            print(f"  • {location}: {item['count']:,}개")
    
    print("="*50)


def print_crawling_summary(jobs):
    """크롤링 결과 요약 출력"""
    if not jobs:
        return
    
    print(f"\n📋 크롤링 결과 요약")
    print("-"*30)
    print(f"수집된 채용공고: {len(jobs)}개")
    
    # 회사별 분포
    companies = {}
    for job in jobs:
        company = job.get('company', '미지정')
        companies[company] = companies.get(company, 0) + 1
    
    print(f"\n회사별 분포 (상위 5개):")
    for company, count in sorted(companies.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  • {company}: {count}개")
    
    # 지역별 분포
    locations = {}
    for job in jobs:
        location = job.get('location', '미지정')
        if location:
            locations[location] = locations.get(location, 0) + 1
    
    if locations:
        print(f"\n지역별 분포 (상위 5개):")
        for location, count in sorted(locations.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  • {location}: {count}개")
    
    # 고용형태별 분포
    employment_types = {}
    for job in jobs:
        emp_type = job.get('employment_type', '미지정')
        if emp_type:
            employment_types[emp_type] = employment_types.get(emp_type, 0) + 1
    
    if employment_types:
        print(f"\n고용형태별 분포:")
        for emp_type, count in employment_types.items():
            print(f"  • {emp_type}: {count}개")
    
    print("-"*30)
    
    # 상위 3개 채용공고 미리보기
    print(f"\n🔍 채용공고 미리보기 (상위 3개):")
    for i, job in enumerate(jobs[:3], 1):
        print(f"\n{i}. {job.get('title', 'N/A')}")
        print(f"   회사: {job.get('company', 'N/A')}")
        print(f"   지역: {job.get('location', 'N/A')}")
        print(f"   급여: {job.get('salary', 'N/A')}")
        print(f"   고용형태: {job.get('employment_type', 'N/A')}")


if __name__ == "__main__":
    main()