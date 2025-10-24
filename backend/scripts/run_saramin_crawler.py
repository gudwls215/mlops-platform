"""
사람인 크롤러 대량 실행 스크립트
5,000건 이상의 채용공고 수집
"""
import sys
import os
from datetime import datetime

# 프로젝트 루트 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(backend_dir)
crawling_dir = os.path.join(project_root, 'crawling')

sys.path.insert(0, crawling_dir)
sys.path.insert(0, os.path.join(crawling_dir, 'scrapers'))

from scrapers.saramin_crawler import SaraminCrawler


def main():
    """메인 실행 함수"""
    print("=" * 80)
    print("사람인 채용공고 대량 수집")
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    crawler = SaraminCrawler()
    
    # 목표: 5,000건
    target = 5000
    batch_size = 2000  # 한 번에 2000건씩 수집 (필터 제거로 속도 향상)
    total_collected = 0
    
    print(f"\n목표: {target}건")
    print(f"배치 크기: {batch_size}건")
    print("-" * 80)
    
    batch_num = 1
    while total_collected < target:
        print(f"\n[배치 {batch_num}] 수집 시작...")
        
        try:
            # 크롤링 실행 (DB 자동 저장)
            jobs = crawler.crawl_jobs(max_jobs=batch_size, save_to_db=True)
            
            collected = len(jobs)
            total_collected += collected
            
            print(f"[배치 {batch_num}] 완료: {collected}건 수집")
            print(f"누적: {total_collected}/{target}건 ({total_collected/target*100:.1f}%)")
            
            if collected == 0:
                print("\n⚠️  더 이상 수집할 데이터가 없습니다.")
                break
            
            batch_num += 1
            
        except KeyboardInterrupt:
            print("\n\n사용자에 의해 중단되었습니다.")
            break
        except Exception as e:
            print(f"\n❌ 배치 {batch_num} 실행 중 오류: {e}")
            print("다음 배치를 시도합니다...")
            batch_num += 1
            continue
    
    print("\n" + "=" * 80)
    print("수집 완료")
    print(f"종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"총 수집: {total_collected}건")
    print(f"목표 달성률: {total_collected/target*100:.1f}%")
    print("=" * 80)


if __name__ == "__main__":
    main()
