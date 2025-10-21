#!/usr/bin/env python3
"""
Saramin 크롤러 단독 테스트 스크립트
트랜잭션 충돌 없이 Saramin만 실행
"""

import sys
import os
import logging
from datetime import datetime

# 프로젝트 경로 설정
project_path = '/home/ttm/tensorflow-jupyter/jupyterNotebook/khj/mlops-platform'
sys.path.insert(0, project_path)
sys.path.insert(0, os.path.join(project_path, 'crawling'))
sys.path.insert(0, os.path.join(project_path, 'crawling', 'scrapers'))

def test_saramin_only():
    """Saramin 크롤러 단독 테스트"""
    print("🔧 Saramin 크롤러 단독 테스트 시작")
    print("="*60)
    
    try:
        # 작업 디렉토리 변경
        os.chdir(os.path.join(project_path, 'crawling', 'scrapers'))
        
        # Saramin 크롤러 import
        from saramin_crawler import SaraminCrawler
        
        print("📊 Saramin 크롤러 초기화...")
        crawler = SaraminCrawler()
        
        print("🚀 크롤링 시작 (최대 15개, 실시간 DB 저장)")
        print("-"*40)
        
        # 크롤링 실행
        result = crawler.crawl_jobs(max_jobs=15, save_to_db=True)
        
        print("-"*40)
        print("📋 결과 요약:")
        print(f"   수집된 채용공고: {len(result)}개")
        
        if result:
            print("✅ 크롤링 및 DB 저장 완료!")
            
            # 간단한 결과 미리보기
            print("\n📝 수집된 데이터 미리보기:")
            for i, job in enumerate(result[:3], 1):
                print(f"   {i}. {job['title'][:50]}... - {job['company']}")
        else:
            print("⚠️ 수집된 데이터가 없습니다.")
            
        return len(result)
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 0

def check_db_after_test():
    """테스트 후 DB 확인"""
    print("\n🔍 DB 저장 결과 확인")
    print("-"*30)
    
    try:
        from database import DatabaseManager
        
        db = DatabaseManager()
        db.connect()
        
        # 최근 1시간 데이터 조회
        recent_data = db.execute_query("""
            SELECT id, title, company, source, created_at 
            FROM mlops.job_postings 
            WHERE created_at >= NOW() - INTERVAL '1 hour'
            AND source = 'saramin'
            ORDER BY id DESC
            LIMIT 10
        """)
        
        print(f"📊 최근 1시간간 Saramin 데이터: {len(recent_data)}개")
        
        for job in recent_data[:5]:
            print(f"   ID: {job['id']}, 제목: {job['title'][:40]}..., 회사: {job['company']}")
        
        # 전체 통계
        total_stats = db.execute_query("""
            SELECT source, COUNT(*) as count 
            FROM mlops.job_postings 
            GROUP BY source
        """)
        
        print("\n📈 전체 DB 통계:")
        for stat in total_stats:
            print(f"   {stat['source']}: {stat['count']}개")
            
        return len(recent_data)
        
    except Exception as e:
        print(f"❌ DB 확인 중 오류: {e}")
        return 0

if __name__ == "__main__":
    start_time = datetime.now()
    
    # 1. Saramin 크롤러 테스트
    crawled_count = test_saramin_only()
    
    # 2. DB 확인
    saved_count = check_db_after_test()
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"\n🎯 최종 결과:")
    print(f"   실행 시간: {duration:.1f}초")
    print(f"   크롤링: {crawled_count}개")
    print(f"   DB 저장: {saved_count}개")
    
    if crawled_count > 0 and saved_count > 0:
        print("✅ Saramin 크롤러 단독 실행 성공!")
    else:
        print("❌ 문제가 발생했습니다.")