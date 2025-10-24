#!/usr/bin/env python3
"""
데이터 품질 점검 및 정제 스크립트
- 채용공고 및 자기소개서 데이터 품질 점검
- 결측치, 중복, 이상치 탐지
- 데이터 정제 및 정규화
"""
import sys
import os
from datetime import datetime

# 프로젝트 경로 추가
project_path = '/home/ttm/tensorflow-jupyter/jupyterNotebook/khj/mlops-platform'
sys.path.insert(0, project_path)

from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import re

# 환경변수 로드
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


def check_job_postings_quality():
    """채용공고 데이터 품질 점검"""
    engine = create_engine(DATABASE_URL)
    
    print("\n" + "=" * 80)
    print("📊 채용공고 데이터 품질 점검")
    print("=" * 80)
    
    with engine.connect() as conn:
        # 전체 통계
        result = conn.execute(text('''
            SELECT 
                COUNT(*) as total,
                COUNT(DISTINCT company) as unique_companies,
                COUNT(DISTINCT source_url) as unique_urls,
                COUNT(CASE WHEN title IS NULL OR title = '' THEN 1 END) as missing_title,
                COUNT(CASE WHEN company IS NULL OR company = '' THEN 1 END) as missing_company,
                COUNT(CASE WHEN description IS NULL OR description = '' THEN 1 END) as missing_description,
                COUNT(CASE WHEN source_url IS NULL OR source_url = '' THEN 1 END) as missing_url,
                COUNT(CASE WHEN location IS NULL OR location = '' THEN 1 END) as missing_location,
                COUNT(CASE WHEN employment_type IS NULL OR employment_type = '' THEN 1 END) as missing_employment_type,
                AVG(LENGTH(description)) as avg_desc_length,
                MIN(LENGTH(description)) as min_desc_length,
                MAX(LENGTH(description)) as max_desc_length
            FROM mlops.job_postings
        '''))
        
        row = result.fetchone()
        print(f'\n기본 통계:')
        print(f'  전체 데이터: {row.total}건')
        print(f'  고유 회사: {row.unique_companies}개')
        print(f'  고유 URL: {row.unique_urls}개')
        print(f'  중복률: {(row.total - row.unique_urls) / row.total * 100:.1f}%')
        
        print(f'\n결측치:')
        print(f'  - 제목 누락: {row.missing_title}건 ({row.missing_title/row.total*100:.1f}%)')
        print(f'  - 회사명 누락: {row.missing_company}건 ({row.missing_company/row.total*100:.1f}%)')
        print(f'  - 설명 누락: {row.missing_description}건 ({row.missing_description/row.total*100:.1f}%)')
        print(f'  - URL 누락: {row.missing_url}건 ({row.missing_url/row.total*100:.1f}%)')
        print(f'  - 위치 누락: {row.missing_location}건 ({row.missing_location/row.total*100:.1f}%)')
        print(f'  - 고용형태 누락: {row.missing_employment_type}건 ({row.missing_employment_type/row.total*100:.1f}%)')
        
        print(f'\n설명 길이 통계:')
        print(f'  - 평균: {row.avg_desc_length:.0f}자')
        print(f'  - 최소: {row.min_desc_length}자')
        print(f'  - 최대: {row.max_desc_length}자')
        
        # 중복 URL 확인
        result = conn.execute(text('''
            SELECT source_url, COUNT(*) as count, 
                   array_agg(id) as ids,
                   MAX(created_at) as latest_created
            FROM mlops.job_postings
            WHERE source_url IS NOT NULL AND source_url != ''
            GROUP BY source_url
            HAVING COUNT(*) > 1
            ORDER BY count DESC
            LIMIT 10
        '''))
        
        duplicates = result.fetchall()
        print(f'\n중복 URL: {len(duplicates)}개')
        if duplicates:
            print('  상위 10개:')
            for dup in duplicates:
                print(f'    - {dup.source_url[:70]}... ({dup.count}건)')
                print(f'      IDs: {dup.ids}')
        
        # 비정상적으로 짧은 설명
        result = conn.execute(text('''
            SELECT id, title, company, LENGTH(description) as desc_len
            FROM mlops.job_postings
            WHERE LENGTH(description) < 100
            ORDER BY desc_len
            LIMIT 10
        '''))
        
        short_desc = result.fetchall()
        print(f'\n비정상적으로 짧은 설명 (< 100자): {len(short_desc)}건')
        if short_desc:
            for sd in short_desc:
                print(f'    - ID {sd.id}: {sd.company} - {sd.title} ({sd.desc_len}자)')
        
        # 날짜별 데이터 분포
        result = conn.execute(text('''
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM mlops.job_postings
            GROUP BY DATE(created_at)
            ORDER BY date DESC
            LIMIT 10
        '''))
        
        dates = result.fetchall()
        print(f'\n최근 수집 일자 (상위 10일):')
        for d in dates:
            print(f'  - {d.date}: {d.count}건')
        
        # 회사별 공고 수
        result = conn.execute(text('''
            SELECT company, COUNT(*) as count
            FROM mlops.job_postings
            GROUP BY company
            ORDER BY count DESC
            LIMIT 10
        '''))
        
        companies = result.fetchall()
        print(f'\n공고가 많은 회사 (상위 10개):')
        for c in companies:
            print(f'  - {c.company}: {c.count}건')
        
        return row.total


def check_cover_letters_quality():
    """자기소개서 데이터 품질 점검"""
    engine = create_engine(DATABASE_URL)
    
    print("\n" + "=" * 80)
    print("📊 자기소개서 데이터 품질 점검")
    print("=" * 80)
    
    with engine.connect() as conn:
        # 전체 통계
        result = conn.execute(text('''
            SELECT 
                COUNT(*) as total,
                COUNT(DISTINCT company) as unique_companies,
                COUNT(DISTINCT url) as unique_urls,
                COUNT(CASE WHEN title IS NULL OR title = '' THEN 1 END) as missing_title,
                COUNT(CASE WHEN company IS NULL OR company = '' THEN 1 END) as missing_company,
                COUNT(CASE WHEN content IS NULL OR content = '' THEN 1 END) as missing_content,
                COUNT(CASE WHEN position IS NULL OR position = '' THEN 1 END) as missing_position,
                COUNT(CASE WHEN is_passed = true THEN 1 END) as passed_count,
                AVG(LENGTH(content)) as avg_content_length,
                MIN(LENGTH(content)) as min_content_length,
                MAX(LENGTH(content)) as max_content_length
            FROM mlops.cover_letter_samples
        '''))
        
        row = result.fetchone()
        print(f'\n기본 통계:')
        print(f'  전체 데이터: {row.total}건')
        print(f'  고유 회사: {row.unique_companies}개')
        print(f'  고유 URL: {row.unique_urls}개')
        print(f'  중복률: {(row.total - row.unique_urls) / row.total * 100:.1f}%')
        print(f'  합격 자소서: {row.passed_count}건 ({row.passed_count/row.total*100:.1f}%)')
        
        print(f'\n결측치:')
        print(f'  - 제목 누락: {row.missing_title}건 ({row.missing_title/row.total*100:.1f}%)')
        print(f'  - 회사명 누락: {row.missing_company}건 ({row.missing_company/row.total*100:.1f}%)')
        print(f'  - 내용 누락: {row.missing_content}건 ({row.missing_content/row.total*100:.1f}%)')
        print(f'  - 직무 누락: {row.missing_position}건 ({row.missing_position/row.total*100:.1f}%)')
        
        print(f'\n내용 길이 통계:')
        print(f'  - 평균: {row.avg_content_length:.0f}자')
        print(f'  - 최소: {row.min_content_length}자')
        print(f'  - 최대: {row.max_content_length}자')
        
        # 중복 URL 확인
        result = conn.execute(text('''
            SELECT url, COUNT(*) as count, array_agg(id) as ids
            FROM mlops.cover_letter_samples
            WHERE url IS NOT NULL AND url != ''
            GROUP BY url
            HAVING COUNT(*) > 1
            ORDER BY count DESC
            LIMIT 10
        '''))
        
        duplicates = result.fetchall()
        print(f'\n중복 URL: {len(duplicates)}개')
        if duplicates:
            print('  상위 10개:')
            for dup in duplicates:
                print(f'    - {dup.url[:70]}... ({dup.count}건)')
                print(f'      IDs: {dup.ids}')
        
        # 비정상적으로 짧은 내용
        result = conn.execute(text('''
            SELECT id, title, company, position, LENGTH(content) as content_len
            FROM mlops.cover_letter_samples
            WHERE LENGTH(content) < 200
            ORDER BY content_len
            LIMIT 10
        '''))
        
        short_content = result.fetchall()
        print(f'\n비정상적으로 짧은 내용 (< 200자): {len(short_content)}건')
        if short_content:
            for sc in short_content:
                print(f'    - ID {sc.id}: {sc.company} - {sc.position} ({sc.content_len}자)')
        
        # 회사별 자소서 수
        result = conn.execute(text('''
            SELECT company, COUNT(*) as count
            FROM mlops.cover_letter_samples
            GROUP BY company
            ORDER BY count DESC
            LIMIT 10
        '''))
        
        companies = result.fetchall()
        print(f'\n자소서가 많은 회사 (상위 10개):')
        for c in companies:
            print(f'  - {c.company}: {c.count}건')
        
        # 직무별 자소서 수
        result = conn.execute(text('''
            SELECT position, COUNT(*) as count
            FROM mlops.cover_letter_samples
            WHERE position IS NOT NULL AND position != ''
            GROUP BY position
            ORDER BY count DESC
            LIMIT 10
        '''))
        
        positions = result.fetchall()
        print(f'\n자소서가 많은 직무 (상위 10개):')
        for p in positions:
            print(f'  - {p.position}: {p.count}건')
        
        return row.total


def clean_job_postings():
    """채용공고 데이터 정제"""
    engine = create_engine(DATABASE_URL)
    
    print("\n" + "=" * 80)
    print("🧹 채용공고 데이터 정제")
    print("=" * 80)
    
    with engine.begin() as conn:
        # 1. 중복 URL 제거 (최신 데이터만 유지)
        result = conn.execute(text('''
            WITH duplicates AS (
                SELECT id, source_url,
                       ROW_NUMBER() OVER (PARTITION BY source_url ORDER BY created_at DESC, id DESC) as rn
                FROM mlops.job_postings
                WHERE source_url IS NOT NULL AND source_url != ''
            )
            DELETE FROM mlops.job_postings
            WHERE id IN (SELECT id FROM duplicates WHERE rn > 1)
            RETURNING id
        '''))
        
        deleted_count = len(result.fetchall())
        print(f'\n✓ 중복 URL 제거: {deleted_count}건')
        
        # 2. 비정상적으로 짧은 설명 제거 (< 50자)
        result = conn.execute(text('''
            DELETE FROM mlops.job_postings
            WHERE LENGTH(description) < 50
            RETURNING id
        '''))
        
        short_deleted = len(result.fetchall())
        print(f'✓ 비정상적으로 짧은 설명 제거 (< 50자): {short_deleted}건')
        
        # 3. 제목 정규화 (앞뒤 공백 제거)
        result = conn.execute(text('''
            UPDATE mlops.job_postings
            SET title = TRIM(title),
                company = TRIM(company),
                location = TRIM(location)
            WHERE title != TRIM(title) 
               OR company != TRIM(company)
               OR (location IS NOT NULL AND location != TRIM(location))
            RETURNING id
        '''))
        
        trimmed_count = len(result.fetchall())
        print(f'✓ 공백 정규화: {trimmed_count}건')
        
        # 4. NULL 문자열을 실제 NULL로 변환
        result = conn.execute(text('''
            UPDATE mlops.job_postings
            SET location = NULL
            WHERE location = '' OR location = 'null' OR location = 'None'
            RETURNING id
        '''))
        
        null_fixed = len(result.fetchall())
        print(f'✓ NULL 문자열 정규화: {null_fixed}건')
        
        # 최종 통계
        result = conn.execute(text('''
            SELECT COUNT(*) as total,
                   COUNT(DISTINCT company) as companies,
                   COUNT(DISTINCT source_url) as unique_urls
            FROM mlops.job_postings
        '''))
        
        row = result.fetchone()
        print(f'\n정제 후 데이터:')
        print(f'  - 총 {row.total}건')
        print(f'  - {row.companies}개 회사')
        print(f'  - {row.unique_urls}개 고유 URL')


def clean_cover_letters():
    """자기소개서 데이터 정제"""
    engine = create_engine(DATABASE_URL)
    
    print("\n" + "=" * 80)
    print("🧹 자기소개서 데이터 정제")
    print("=" * 80)
    
    with engine.begin() as conn:
        # 1. 중복 URL 제거 (최신 데이터만 유지)
        result = conn.execute(text('''
            WITH duplicates AS (
                SELECT id, url,
                       ROW_NUMBER() OVER (PARTITION BY url ORDER BY created_at DESC, id DESC) as rn
                FROM mlops.cover_letter_samples
                WHERE url IS NOT NULL AND url != ''
            )
            DELETE FROM mlops.cover_letter_samples
            WHERE id IN (SELECT id FROM duplicates WHERE rn > 1)
            RETURNING id
        '''))
        
        deleted_count = len(result.fetchall())
        print(f'\n✓ 중복 URL 제거: {deleted_count}건')
        
        # 2. 비정상적으로 짧은 내용 제거 (< 100자)
        result = conn.execute(text('''
            DELETE FROM mlops.cover_letter_samples
            WHERE LENGTH(content) < 100
            RETURNING id
        '''))
        
        short_deleted = len(result.fetchall())
        print(f'✓ 비정상적으로 짧은 내용 제거 (< 100자): {short_deleted}건')
        
        # 3. 텍스트 정규화 (앞뒤 공백 제거)
        result = conn.execute(text('''
            UPDATE mlops.cover_letter_samples
            SET title = TRIM(title),
                company = TRIM(company),
                position = TRIM(position),
                content = TRIM(content)
            WHERE title != TRIM(title) 
               OR company != TRIM(company)
               OR (position IS NOT NULL AND position != TRIM(position))
               OR content != TRIM(content)
            RETURNING id
        '''))
        
        trimmed_count = len(result.fetchall())
        print(f'✓ 공백 정규화: {trimmed_count}건')
        
        # 4. NULL 문자열을 실제 NULL로 변환
        result = conn.execute(text('''
            UPDATE mlops.cover_letter_samples
            SET position = NULL,
                department = NULL,
                experience_level = NULL
            WHERE (position = '' OR position = 'null' OR position = 'None')
               OR (department = '' OR department = 'null' OR department = 'None')
               OR (experience_level = '' OR experience_level = 'null' OR experience_level = 'None')
            RETURNING id
        '''))
        
        null_fixed = len(result.fetchall())
        print(f'✓ NULL 문자열 정규화: {null_fixed}건')
        
        # 최종 통계
        result = conn.execute(text('''
            SELECT COUNT(*) as total,
                   COUNT(DISTINCT company) as companies,
                   COUNT(DISTINCT url) as unique_urls,
                   COUNT(CASE WHEN is_passed = true THEN 1 END) as passed
            FROM mlops.cover_letter_samples
        '''))
        
        row = result.fetchone()
        print(f'\n정제 후 데이터:')
        print(f'  - 총 {row.total}건')
        print(f'  - {row.companies}개 회사')
        print(f'  - {row.unique_urls}개 고유 URL')
        print(f'  - {row.passed}건 합격 자소서')


def main():
    """메인 실행 함수"""
    print("=" * 80)
    print(f"🔍 데이터 품질 점검 및 정제 시작: {datetime.now()}")
    print("=" * 80)
    
    # 1. 품질 점검
    jp_count = check_job_postings_quality()
    cl_count = check_cover_letters_quality()
    
    # 2. 데이터 정제 확인
    print("\n" + "=" * 80)
    print("데이터 정제를 진행하시겠습니까?")
    print("=" * 80)
    print(f"채용공고: {jp_count}건")
    print(f"자기소개서: {cl_count}건")
    print("\n정제 작업:")
    print("  - 중복 데이터 제거")
    print("  - 비정상적으로 짧은 데이터 제거")
    print("  - 텍스트 정규화 (공백 제거)")
    print("  - NULL 값 정규화")
    
    # 자동 실행 (스크립트 모드)
    response = 'y'
    
    if response.lower() == 'y':
        # 3. 데이터 정제
        clean_job_postings()
        clean_cover_letters()
        
        print("\n" + "=" * 80)
        print(f"✅ 데이터 품질 점검 및 정제 완료: {datetime.now()}")
        print("=" * 80)
    else:
        print("\n정제 작업을 건너뜁니다.")


if __name__ == "__main__":
    main()
