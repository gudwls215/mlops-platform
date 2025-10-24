#!/usr/bin/env python3
"""
Linkareer 자기소개서 크롤러 실행 스크립트
목표: 1,000건의 자기소개서 수집
"""
import sys
import os
from datetime import datetime

# 프로젝트 경로 추가
project_path = '/home/ttm/tensorflow-jupyter/jupyterNotebook/khj/mlops-platform'
sys.path.insert(0, project_path)
sys.path.insert(0, os.path.join(project_path, 'crawling'))
sys.path.insert(0, os.path.join(project_path, 'crawling', 'scrapers'))

from scrapers.linkareer_crawler import LinkareerCoverLetterCrawler
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


def check_current_status():
    """현재 수집 상태 확인"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT COUNT(*) as total,
                   COUNT(DISTINCT company) as companies,
                   COUNT(CASE WHEN is_passed = true THEN 1 END) as passed
            FROM mlops.cover_letter_samples
        """))
        
        row = result.fetchone()
        
        print("\n" + "=" * 80)
        print("📊 자기소개서 현재 수집 현황")
        print("=" * 80)
        print(f"  총 자기소개서: {row.total}건")
        print(f"  고유 회사: {row.companies}개")
        print(f"  합격 자소서: {row.passed}건")
        print(f"  목표 대비: {row.total / 1000 * 100:.1f}% (목표 1,000건)")
        print("=" * 80 + "\n")
        
        return row.total


def main():
    """메인 실행 함수"""
    print("=" * 80)
    print(f"🚀 Linkareer 자기소개서 크롤링 시작: {datetime.now()}")
    print("=" * 80)
    
    # 현재 상태 확인
    current_count = check_current_status()
    
    # 목표 개수 계산
    target = 1000
    needed = max(target - current_count, 0)
    
    if needed == 0:
        print(f"✅ 이미 목표({target}건)를 달성했습니다!")
        return
    
    print(f"📋 추가로 수집할 개수: {needed}건\n")
    
    # 크롤러 실행
    crawler = LinkareerCoverLetterCrawler()
    
    try:
        print(f"⏳ 크롤링 시작... (목표: {needed}건)")
        result = crawler.crawl(max_items=needed)
        
        print("\n" + "=" * 80)
        print(f"✅ 크롤링 완료: {datetime.now()}")
        print("=" * 80)
        print(f"  결과: {result}")
        print("=" * 80)
        
        # 최종 상태 확인
        print("\n최종 수집 현황:")
        check_current_status()
        
    except Exception as e:
        print(f"\n❌ 크롤링 오류: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
