#!/usr/bin/env python3
"""
자기소개서 자동 라벨링 스크립트
합격/불합격을 50:50 비율로 무작위 배정
"""
import sys
import os
from datetime import datetime
import random

# 프로젝트 경로 추가
project_path = '/home/ttm/tensorflow-jupyter/jupyterNotebook/khj/mlops-platform'
sys.path.insert(0, project_path)
sys.path.insert(0, os.path.join(project_path, 'backend'))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


def auto_label_cover_letters(pass_rate=0.5):
    """
    자기소개서 자동 라벨링
    
    Args:
        pass_rate: 합격 비율 (0.0 ~ 1.0, 기본값 0.5 = 50%)
    """
    engine = create_engine(DATABASE_URL)
    
    print("=" * 80)
    print(f"자기소개서 자동 라벨링 시작: {datetime.now()}")
    print("=" * 80)
    
    with engine.begin() as conn:
        # 미라벨 자기소개서 조회
        result = conn.execute(text("""
            SELECT id
            FROM mlops.cover_letter_samples
            WHERE is_passed IS NULL
            ORDER BY id
        """))
        
        unlabeled_ids = [row.id for row in result.fetchall()]
        total_count = len(unlabeled_ids)
        
        if total_count == 0:
            print("\n미라벨 자기소개서가 없습니다.")
            return
        
        print(f"\n미라벨 자기소개서: {total_count}건")
        print(f"합격 비율: {pass_rate * 100:.1f}%")
        print(f"불합격 비율: {(1 - pass_rate) * 100:.1f}%")
        
        # 무작위로 섞기
        random.shuffle(unlabeled_ids)
        
        # 합격/불합격 개수 계산
        pass_count = int(total_count * pass_rate)
        fail_count = total_count - pass_count
        
        print(f"\n예상 라벨링:")
        print(f"  - 합격: {pass_count}건")
        print(f"  - 불합격: {fail_count}건")
        
        # 합격 라벨링
        passed_ids = unlabeled_ids[:pass_count]
        if passed_ids:
            placeholders = ','.join([f':id{i}' for i in range(len(passed_ids))])
            params = {f'id{i}': id_val for i, id_val in enumerate(passed_ids)}
            
            conn.execute(
                text(f"""
                    UPDATE mlops.cover_letter_samples
                    SET is_passed = true,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id IN ({placeholders})
                """),
                params
            )
            print(f"\n✓ 합격 라벨링 완료: {len(passed_ids)}건")
        
        # 불합격 라벨링
        failed_ids = unlabeled_ids[pass_count:]
        if failed_ids:
            placeholders = ','.join([f':id{i}' for i in range(len(failed_ids))])
            params = {f'id{i}': id_val for i, id_val in enumerate(failed_ids)}
            
            conn.execute(
                text(f"""
                    UPDATE mlops.cover_letter_samples
                    SET is_passed = false,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id IN ({placeholders})
                """),
                params
            )
            print(f"✓ 불합격 라벨링 완료: {len(failed_ids)}건")
        
        # 최종 통계 확인
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN is_passed = true THEN 1 END) as passed,
                COUNT(CASE WHEN is_passed = false THEN 1 END) as failed,
                COUNT(CASE WHEN is_passed IS NULL THEN 1 END) as unlabeled
            FROM mlops.cover_letter_samples
        """))
        
        row = result.fetchone()
        
        print("\n" + "=" * 80)
        print("최종 라벨링 현황")
        print("=" * 80)
        print(f"  총 자기소개서: {row.total}건")
        print(f"  합격: {row.passed}건 ({row.passed/row.total*100:.1f}%)")
        print(f"  불합격: {row.failed}건 ({row.failed/row.total*100:.1f}%)")
        print(f"  미라벨: {row.unlabeled}건 ({row.unlabeled/row.total*100:.1f}%)")
        print("=" * 80)
        
        print(f"\n✅ 자동 라벨링 완료: {datetime.now()}")


if __name__ == "__main__":
    # 합격 비율을 50%로 설정 (데이터 분석에 이상적)
    auto_label_cover_letters(pass_rate=0.5)
