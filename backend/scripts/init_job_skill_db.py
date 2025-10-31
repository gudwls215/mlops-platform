"""
스킬-직무 매핑 데이터베이스 초기화 스크립트
"""
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import engine, SessionLocal
from app.models.job_skill_models import (
    JobCategory, SkillMaster, JobSkillMapping,
    INITIAL_JOB_CATEGORIES, INITIAL_SKILLS, INITIAL_MAPPINGS,
    Base
)


def init_job_skill_tables():
    """스킬-직무 매핑 테이블 초기화"""
    print("스킬-직무 매핑 테이블 생성 중...")
    
    # 테이블 생성
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # 1. 직무 카테고리 데이터 삽입
        print("\n1. 직무 카테고리 데이터 삽입 중...")
        for job_data in INITIAL_JOB_CATEGORIES:
            existing = db.query(JobCategory).filter(JobCategory.id == job_data["id"]).first()
            if not existing:
                job = JobCategory(**job_data)
                db.add(job)
        db.commit()
        print(f"   ✓ {len(INITIAL_JOB_CATEGORIES)}개 직무 카테고리 추가 완료")
        
        # 2. 스킬 마스터 데이터 삽입
        print("\n2. 스킬 마스터 데이터 삽입 중...")
        for skill_data in INITIAL_SKILLS:
            existing = db.query(SkillMaster).filter(SkillMaster.id == skill_data["id"]).first()
            if not existing:
                skill = SkillMaster(**skill_data)
                db.add(skill)
        db.commit()
        print(f"   ✓ {len(INITIAL_SKILLS)}개 스킬 추가 완료")
        
        # 3. 직무-스킬 매핑 데이터 삽입
        print("\n3. 직무-스킬 매핑 데이터 삽입 중...")
        for mapping_data in INITIAL_MAPPINGS:
            existing = db.query(JobSkillMapping).filter(
                JobSkillMapping.job_category_id == mapping_data["job_category_id"],
                JobSkillMapping.skill_id == mapping_data["skill_id"]
            ).first()
            if not existing:
                mapping = JobSkillMapping(**mapping_data)
                db.add(mapping)
        db.commit()
        print(f"   ✓ {len(INITIAL_MAPPINGS)}개 매핑 관계 추가 완료")
        
        # 4. 통계 출력
        print("\n" + "=" * 60)
        print("데이터베이스 초기화 완료!")
        print("=" * 60)
        
        job_count = db.query(JobCategory).count()
        skill_count = db.query(SkillMaster).count()
        mapping_count = db.query(JobSkillMapping).count()
        
        print(f"\n총 직무 카테고리: {job_count}개")
        print(f"총 스킬: {skill_count}개")
        print(f"총 매핑 관계: {mapping_count}개")
        
        # 직무별 스킬 개수 출력
        print("\n직무별 매핑된 스킬 개수:")
        for job in db.query(JobCategory).all():
            count = db.query(JobSkillMapping).filter(
                JobSkillMapping.job_category_id == job.id
            ).count()
            print(f"  - {job.name}: {count}개 스킬")
        
        print("\n초기화 성공!")
        
    except Exception as e:
        print(f"\n오류 발생: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def show_job_skills(job_name: str = None):
    """직무별 스킬 목록 조회"""
    db = SessionLocal()
    
    try:
        if job_name:
            jobs = db.query(JobCategory).filter(JobCategory.name == job_name).all()
        else:
            jobs = db.query(JobCategory).all()
        
        for job in jobs:
            print(f"\n[{job.name}]")
            print(f"설명: {job.description}")
            print("\n필수 스킬:")
            
            mappings = db.query(JobSkillMapping, SkillMaster).join(
                SkillMaster, JobSkillMapping.skill_id == SkillMaster.id
            ).filter(
                JobSkillMapping.job_category_id == job.id,
                JobSkillMapping.is_required == 1
            ).all()
            
            for mapping, skill in mappings:
                print(f"  ✓ {skill.name} (중요도: {mapping.importance:.1f})")
            
            print("\n선택 스킬:")
            mappings = db.query(JobSkillMapping, SkillMaster).join(
                SkillMaster, JobSkillMapping.skill_id == SkillMaster.id
            ).filter(
                JobSkillMapping.job_category_id == job.id,
                JobSkillMapping.is_required == 0
            ).all()
            
            for mapping, skill in mappings:
                print(f"  - {skill.name} (중요도: {mapping.importance:.1f})")
            
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="스킬-직무 매핑 DB 초기화")
    parser.add_argument("--init", action="store_true", help="데이터베이스 초기화")
    parser.add_argument("--show", type=str, nargs="?", const="", help="직무별 스킬 조회")
    
    args = parser.parse_args()
    
    if args.init:
        init_job_skill_tables()
    elif args.show is not None:
        job_name = args.show if args.show else None
        show_job_skills(job_name)
    else:
        parser.print_help()
