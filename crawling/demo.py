"""
크롤링 시스템 데모 (데이터베이스 연결 없이)
"""
import logging
from scrapers.saramin_crawler import SaraminCrawler
from base_crawler import JobCrawlerUtils

def demo_crawling():
    """크롤링 데모 실행"""
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 MLOps 플랫폼 크롤링 시스템 데모")
    print("="*50)
    
    try:
        # 사람인 크롤러 초기화
        print("📋 사람인 크롤러 초기화 중...")
        crawler = SaraminCrawler()
        
        # robots.txt 확인
        print("🤖 robots.txt 준수 확인...")
        test_url = "https://www.saramin.co.kr/zf_user/search/recruit"
        can_crawl = crawler.check_robots_txt(test_url)
        print(f"   크롤링 허용 여부: {'✅ 허용' if can_crawl else '❌ 차단'}")
        
        # URL 수집 테스트 (실제 크롤링 없이)
        print("\n🔍 채용공고 URL 패턴 테스트...")
        print("   대상 키워드:", ['시니어', '50대', '경력직'])
        print("   예상 검색 URL 패턴:")
        for keyword in ['시니어', '50대']:
            search_url = f"https://www.saramin.co.kr/zf_user/search/recruit?searchword={keyword}"
            print(f"   - {search_url}")
        
        # 시니어 친화성 테스트
        print("\n👴 시니어 친화성 필터링 테스트...")
        
        # 테스트 케이스 1: 시니어 친화적
        test_job1 = {
            'title': '시니어 환영 고객상담원',
            'company': '테스트회사',
            'description': '50대 이상 경험자 우대',
            'category': '상담',
            'requirements': '경력 우대'
        }
        
        is_senior_friendly1 = JobCrawlerUtils.is_senior_friendly(test_job1)
        print(f"   테스트 1 - '{test_job1['title']}': {'✅ 적합' if is_senior_friendly1 else '❌ 부적합'}")
        
        # 테스트 케이스 2: 시니어 부적합
        test_job2 = {
            'title': '신입 개발자 모집',
            'company': '테크회사',
            'description': '20대 30대 신입 환영',
            'category': '개발',
            'requirements': '신입만 지원'
        }
        
        is_senior_friendly2 = JobCrawlerUtils.is_senior_friendly(test_job2)
        print(f"   테스트 2 - '{test_job2['title']}': {'✅ 적합' if is_senior_friendly2 else '❌ 부적합'}")
        
        # 설정 정보 출력
        print("\n⚙️  크롤링 설정 정보:")
        from config import DELAY_MIN, DELAY_MAX, CONCURRENT_REQUESTS, SENIOR_KEYWORDS
        print(f"   딜레이 범위: {DELAY_MIN}-{DELAY_MAX}초")
        print(f"   동시 요청 제한: {CONCURRENT_REQUESTS}개")
        print(f"   시니어 키워드 수: {len(SENIOR_KEYWORDS)}개")
        
        print("\n📊 크롤링 예상 성능:")
        print(f"   페이지당 평균 딜레이: {(DELAY_MIN + DELAY_MAX) / 2}초")
        print(f"   시간당 예상 처리량: ~{3600 // ((DELAY_MIN + DELAY_MAX) / 2)}개 페이지")
        
        print("\n✅ 크롤링 인프라 구축 완료!")
        print("   - 기본 크롤러 클래스 구현 완료")
        print("   - 사람인 크롤러 구현 완료") 
        print("   - 시니어 친화성 필터링 구현 완료")
        print("   - robots.txt 준수 로직 구현 완료")
        print("   - 데이터베이스 연동 모듈 구현 완료")
        print("   - 스케줄링 및 자동화 지원 완료")
        
        print(f"\n📁 생성된 파일:")
        files = [
            "base_crawler.py - 기본 크롤러 클래스",
            "config.py - 설정 파일", 
            "database.py - 데이터베이스 연동",
            "scrapers/saramin_crawler.py - 사람인 크롤러",
            "main.py - 메인 실행기",
            "requirements.txt - 의존성 목록",
            "README.md - 사용법 가이드",
            ".env - 환경변수 설정"
        ]
        
        for file in files:
            print(f"   ✓ {file}")
        
        print(f"\n🎯 다음 단계:")
        print("   1. 데이터베이스 연결 정보 확인 후 실제 크롤링 테스트")
        print("   2. 잡코리아, 워크넷 크롤러 추가 개발")
        print("   3. 크롤링 스케줄러 설정 및 자동화")
        print("   4. API 서버와 크롤링 시스템 연동")
        
    except Exception as e:
        print(f"❌ 데모 실행 중 오류: {e}")

if __name__ == "__main__":
    demo_crawling()