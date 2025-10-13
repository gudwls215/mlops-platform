#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
데이터 정제 및 처리 통합 모듈
크롤링된 데이터의 텍스트 정제, 검증, 저장을 담당
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from text_cleaner import TextCleaner
from database import DatabaseManager
import logging
from typing import Dict, List
import json

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataProcessor:
    """데이터 정제 및 처리 클래스"""
    
    def __init__(self):
        self.text_cleaner = TextCleaner()
        self.db_manager = DatabaseManager()
        
        # 정제 통계
        self.processing_stats = {
            "total_processed": 0,
            "successful_cleanings": 0,
            "failed_cleanings": 0,
            "validation_passed": 0,
            "validation_failed": 0
        }
    
    def process_job_posting(self, job_data: Dict) -> Dict:
        """채용공고 데이터 정제 및 처리"""
        logger.info(f"채용공고 정제 시작: {job_data.get('title', 'Unknown')}")
        
        processed_data = job_data.copy()
        self.processing_stats["total_processed"] += 1
        
        try:
            # 텍스트 필드들 정제
            text_fields = [
                'title', 'company', 'location', 'salary', 'employment_type',
                'experience', 'education', 'main_duties', 'qualifications', 'preferences'
            ]
            
            cleaning_results = {}
            
            for field in text_fields:
                if field in processed_data and processed_data[field]:
                    original_text = str(processed_data[field])
                    
                    # 텍스트 정제
                    cleaned_text = self.text_cleaner.clean_job_posting_text(original_text)
                    
                    # 품질 검증 (필드 타입 고려)
                    validation = self.text_cleaner.validate_cleaned_text(original_text, cleaned_text, field)
                    
                    if validation.get('valid', False):
                        processed_data[field] = cleaned_text
                        cleaning_results[field] = {
                            'success': True,
                            'original_length': len(original_text),
                            'cleaned_length': len(cleaned_text),
                            'length_ratio': validation.get('length_ratio', 0)
                        }
                    else:
                        logger.warning(f"필드 {field} 정제 실패: {validation.get('reason', 'Unknown')}")
                        cleaning_results[field] = {
                            'success': False,
                            'reason': validation.get('reason', 'Validation failed')
                        }
            
            # 정제 결과 통계 업데이트
            successful_fields = sum(1 for result in cleaning_results.values() if result.get('success'))
            total_fields = len(cleaning_results)
            
            if successful_fields > 0:
                self.processing_stats["successful_cleanings"] += 1
                
                if successful_fields == total_fields:
                    self.processing_stats["validation_passed"] += 1
                else:
                    self.processing_stats["validation_failed"] += 1
                    
                # 정제 메타데이터 추가
                processed_data['_cleaning_meta'] = {
                    'processed_fields': successful_fields,
                    'total_fields': total_fields,
                    'success_rate': round(successful_fields / total_fields, 2),
                    'cleaning_results': cleaning_results
                }
                
            else:
                self.processing_stats["failed_cleanings"] += 1
                logger.error(f"채용공고 정제 완전 실패: {job_data.get('title', 'Unknown')}")
                
            return processed_data
            
        except Exception as e:
            logger.error(f"채용공고 처리 중 오류: {e}")
            self.processing_stats["failed_cleanings"] += 1
            return job_data
    
    def process_cover_letter(self, cover_letter_data: Dict) -> Dict:
        """자기소개서 데이터 정제 및 처리"""
        logger.info(f"자기소개서 정제 시작: {cover_letter_data.get('title', 'Unknown')}")
        
        processed_data = cover_letter_data.copy()
        self.processing_stats["total_processed"] += 1
        
        try:
            # 텍스트 필드들 정제
            text_fields = [
                'title', 'company', 'position', 'department', 
                'experience_level', 'content'
            ]
            
            cleaning_results = {}
            
            for field in text_fields:
                if field in processed_data and processed_data[field]:
                    original_text = str(processed_data[field])
                    
                    # 자기소개서 전용 정제
                    cleaned_text = self.text_cleaner.clean_cover_letter_text(original_text)
                    
                    # 품질 검증 (필드 타입 고려)
                    validation = self.text_cleaner.validate_cleaned_text(original_text, cleaned_text, field)
                    
                    if validation.get('valid', False):
                        processed_data[field] = cleaned_text
                        cleaning_results[field] = {
                            'success': True,
                            'original_length': len(original_text),
                            'cleaned_length': len(cleaned_text),
                            'length_ratio': validation.get('length_ratio', 0)
                        }
                    else:
                        logger.warning(f"필드 {field} 정제 실패: {validation.get('reason', 'Unknown')}")
                        cleaning_results[field] = {
                            'success': False,
                            'reason': validation.get('reason', 'Validation failed')
                        }
            
            # 키워드 정제 (배열 필드)
            if 'keywords' in processed_data and processed_data['keywords']:
                cleaned_keywords = []
                for keyword in processed_data['keywords']:
                    if keyword:
                        cleaned_keyword = self.text_cleaner.clean_cover_letter_text(str(keyword))
                        if cleaned_keyword and len(cleaned_keyword.strip()) > 1:
                            cleaned_keywords.append(cleaned_keyword.strip())
                
                processed_data['keywords'] = cleaned_keywords
            
            # 정제 결과 통계 업데이트
            successful_fields = sum(1 for result in cleaning_results.values() if result.get('success'))
            total_fields = len(cleaning_results)
            
            if successful_fields > 0:
                self.processing_stats["successful_cleanings"] += 1
                
                if successful_fields == total_fields:
                    self.processing_stats["validation_passed"] += 1
                else:
                    self.processing_stats["validation_failed"] += 1
                    
                # 정제 메타데이터 추가
                processed_data['_cleaning_meta'] = {
                    'processed_fields': successful_fields,
                    'total_fields': total_fields,
                    'success_rate': round(successful_fields / total_fields, 2),
                    'cleaning_results': cleaning_results
                }
                
            else:
                self.processing_stats["failed_cleanings"] += 1
                logger.error(f"자기소개서 정제 완전 실패: {cover_letter_data.get('title', 'Unknown')}")
                
            return processed_data
            
        except Exception as e:
            logger.error(f"자기소개서 처리 중 오류: {e}")
            self.processing_stats["failed_cleanings"] += 1
            return cover_letter_data
    
    def batch_process_job_postings(self, limit: int = 50) -> Dict:
        """데이터베이스의 채용공고 배치 정제"""
        logger.info(f"채용공고 배치 정제 시작 (최대 {limit}개)")
        
        try:
            # 데이터베이스에서 원시 채용공고 데이터 조회
            self.db_manager.connect()
            
            query = """
            SELECT id, title, company, location, salary, employment_type,
                   experience, education, main_duties, qualifications, preferences,
                   url, source, created_at
            FROM mlops.job_postings
            WHERE main_duties IS NOT NULL OR qualifications IS NOT NULL
            ORDER BY created_at DESC
            LIMIT %s;
            """
            
            job_postings = self.db_manager.execute_query(query, (limit,), fetch=True)
            
            if not job_postings:
                logger.info("정제할 채용공고가 없습니다.")
                return {"processed": 0, "success": 0}
            
            logger.info(f"{len(job_postings)}개의 채용공고를 정제합니다.")
            
            processed_count = 0
            success_count = 0
            
            for job in job_postings:
                # 딕셔너리로 변환
                job_data = dict(job)
                
                # 정제 처리
                processed_job = self.process_job_posting(job_data)
                
                # 정제 메타데이터 확인
                if '_cleaning_meta' in processed_job:
                    success_rate = processed_job['_cleaning_meta'].get('success_rate', 0)
                    if success_rate > 0.5:  # 50% 이상 필드가 성공적으로 정제됨
                        success_count += 1
                        
                        # 정제된 데이터로 업데이트 (메타데이터 제외)
                        cleaned_job = {k: v for k, v in processed_job.items() if not k.startswith('_')}
                        self._update_job_posting(cleaned_job)
                
                processed_count += 1
                
                if processed_count % 10 == 0:
                    logger.info(f"진행률: {processed_count}/{len(job_postings)}")
            
            result = {
                "processed": processed_count,
                "success": success_count,
                "success_rate": round(success_count / processed_count, 2) if processed_count > 0 else 0,
                "stats": self.processing_stats.copy()
            }
            
            logger.info(f"배치 정제 완료: {processed_count}개 처리, {success_count}개 성공")
            return result
            
        except Exception as e:
            logger.error(f"배치 정제 중 오류: {e}")
            return {"processed": 0, "success": 0, "error": str(e)}
        finally:
            self.db_manager.disconnect()
    
    def batch_process_cover_letters(self, limit: int = 50) -> Dict:
        """데이터베이스의 자기소개서 배치 정제"""
        logger.info(f"자기소개서 배치 정제 시작 (최대 {limit}개)")
        
        try:
            # 데이터베이스에서 원시 자기소개서 데이터 조회
            self.db_manager.connect()
            
            query = """
            SELECT id, title, company, position, department, experience_level,
                   content, keywords, url, source, created_at
            FROM mlops.cover_letter_samples
            WHERE content IS NOT NULL
            ORDER BY created_at DESC
            LIMIT %s;
            """
            
            cover_letters = self.db_manager.execute_query(query, (limit,), fetch=True)
            
            if not cover_letters:
                logger.info("정제할 자기소개서가 없습니다.")
                return {"processed": 0, "success": 0}
            
            logger.info(f"{len(cover_letters)}개의 자기소개서를 정제합니다.")
            
            processed_count = 0
            success_count = 0
            
            for cover_letter in cover_letters:
                # 딕셔너리로 변환
                cover_letter_data = dict(cover_letter)
                
                # 정제 처리
                processed_letter = self.process_cover_letter(cover_letter_data)
                
                # 정제 메타데이터 확인
                if '_cleaning_meta' in processed_letter:
                    success_rate = processed_letter['_cleaning_meta'].get('success_rate', 0)
                    if success_rate > 0.5:  # 50% 이상 필드가 성공적으로 정제됨
                        success_count += 1
                        
                        # 정제된 데이터로 업데이트 (메타데이터 제외)
                        cleaned_letter = {k: v for k, v in processed_letter.items() if not k.startswith('_')}
                        self._update_cover_letter(cleaned_letter)
                
                processed_count += 1
                
                if processed_count % 5 == 0:
                    logger.info(f"진행률: {processed_count}/{len(cover_letters)}")
            
            result = {
                "processed": processed_count,
                "success": success_count,
                "success_rate": round(success_count / processed_count, 2) if processed_count > 0 else 0,
                "stats": self.processing_stats.copy()
            }
            
            logger.info(f"배치 정제 완료: {processed_count}개 처리, {success_count}개 성공")
            return result
            
        except Exception as e:
            logger.error(f"배치 정제 중 오류: {e}")
            return {"processed": 0, "success": 0, "error": str(e)}
        finally:
            self.db_manager.disconnect()
    
    def _update_job_posting(self, job_data: Dict) -> bool:
        """정제된 채용공고 데이터로 업데이트"""
        try:
            update_query = """
            UPDATE mlops.job_postings SET
                title = %(title)s,
                company = %(company)s,
                location = %(location)s,
                salary = %(salary)s,
                employment_type = %(employment_type)s,
                experience = %(experience)s,
                education = %(education)s,
                main_duties = %(main_duties)s,
                qualifications = %(qualifications)s,
                preferences = %(preferences)s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %(id)s;
            """
            
            self.db_manager.execute_query(update_query, job_data, fetch=False)
            return True
            
        except Exception as e:
            logger.error(f"채용공고 업데이트 실패 (ID: {job_data.get('id')}): {e}")
            return False
    
    def _update_cover_letter(self, cover_letter_data: Dict) -> bool:
        """정제된 자기소개서 데이터로 업데이트"""
        try:
            update_query = """
            UPDATE mlops.cover_letter_samples SET
                title = %(title)s,
                company = %(company)s,
                position = %(position)s,
                department = %(department)s,
                experience_level = %(experience_level)s,
                content = %(content)s,
                keywords = %(keywords)s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %(id)s;
            """
            
            self.db_manager.execute_query(update_query, cover_letter_data, fetch=False)
            return True
            
        except Exception as e:
            logger.error(f"자기소개서 업데이트 실패 (ID: {cover_letter_data.get('id')}): {e}")
            return False
    
    def get_processing_stats(self) -> Dict:
        """정제 처리 통계 조회"""
        return self.processing_stats.copy()

def main():
    """테스트 실행"""
    processor = DataProcessor()
    
    print("🔧 데이터 정제 및 처리 시스템 테스트")
    print("=" * 60)
    
    # 1. 채용공고 배치 정제
    print("\n📋 채용공고 배치 정제 시작...")
    job_result = processor.batch_process_job_postings(limit=5)
    
    print(f"✅ 채용공고 정제 결과:")
    print(f"  - 처리된 개수: {job_result.get('processed', 0)}개")
    print(f"  - 성공한 개수: {job_result.get('success', 0)}개")
    print(f"  - 성공률: {job_result.get('success_rate', 0):.1%}")
    
    # 2. 자기소개서 배치 정제
    print("\n📝 자기소개서 배치 정제 시작...")
    letter_result = processor.batch_process_cover_letters(limit=5)
    
    print(f"✅ 자기소개서 정제 결과:")
    print(f"  - 처리된 개수: {letter_result.get('processed', 0)}개")
    print(f"  - 성공한 개수: {letter_result.get('success', 0)}개")
    print(f"  - 성공률: {letter_result.get('success_rate', 0):.1%}")
    
    # 3. 전체 통계
    stats = processor.get_processing_stats()
    print(f"\n📊 전체 정제 통계:")
    print(f"  - 총 처리: {stats['total_processed']}개")
    print(f"  - 정제 성공: {stats['successful_cleanings']}개")
    print(f"  - 정제 실패: {stats['failed_cleanings']}개")
    print(f"  - 검증 통과: {stats['validation_passed']}개")
    print(f"  - 검증 실패: {stats['validation_failed']}개")

if __name__ == "__main__":
    main()