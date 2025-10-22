"""
MLOps Platform 데이터 수집 DAG
- 사람인 채용공고 크롤링
- Linkareer 자기소개서 크롤링  
- 데이터 전처리 및 저장
- 매일 새벽 2시 실행
"""

from datetime import datetime, timedelta
from airflow import DAG
try:
    # Airflow 2.x
    from airflow.operators.python import PythonOperator
    from airflow.operators.bash import BashOperator
except ImportError:
    # Airflow 1.x
    from airflow.operators.python_operator import PythonOperator
    from airflow.operators.bash_operator import BashOperator

import sys
import os
import random
import logging

# 프로젝트 경로를 Python path에 추가
project_path = '/home/ttm/tensorflow-jupyter/jupyterNotebook/khj/mlops-platform'
sys.path.append(project_path)

# 기본 DAG 설정
default_args = {
    'owner': 'mlops-platform',
    'depends_on_past': False,
    'start_date': datetime(2025, 10, 13),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# DAG 정의
dag = DAG(
    'data_collection_pipeline',
    default_args=default_args,
    description='채용 사이트 데이터 수집 및 처리 파이프라인',
    schedule='@daily',  # 매일 자정에 실행
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['data_collection', 'mlops'],
)

def run_saramin_crawler():
    """사람인 크롤러 실행"""
    import sys
    import os
    import logging
    
    try:
        # 프로젝트 경로를 Python path에 추가
        project_path = '/home/ttm/tensorflow-jupyter/jupyterNotebook/khj/mlops-platform'
        if project_path not in sys.path:
            sys.path.insert(0, project_path)
        
        # scrapers 디렉토리로 이동
        scrapers_path = os.path.join(project_path, 'crawling', 'scrapers')
        os.chdir(scrapers_path)
        
        # 직접 모듈 import 및 실행
        sys.path.insert(0, scrapers_path)
        from saramin_crawler import SaraminCrawler
        
        # 데이터베이스 매니저도 import
        crawling_path = os.path.join(project_path, 'crawling')
        sys.path.insert(0, crawling_path)
        from database import DatabaseManager
        
        logging.info("사람인 크롤러 시작...")
        crawler = SaraminCrawler()
        db_manager = DatabaseManager()
        
        # 크롤러 실행 (최대 100개 채용공고)
        result = crawler.crawl_jobs(max_jobs=100)
        
        if result and len(result) > 0:
            # 데이터베이스에 저장
            inserted_count = db_manager.bulk_insert_job_postings(result)
            logging.info(f"사람인 크롤러 완료: {len(result)}개 채용공고 수집, {inserted_count}개 저장")
            return f"SUCCESS: {len(result)}개 채용공고 수집, {inserted_count}개 저장"
        else:
            logging.warning("사람인 크롤러: 수집된 데이터가 없습니다")
            return "WARNING: 수집된 데이터 없음"
            
    except ImportError as e:
        logging.error(f"사람인 크롤러 모듈 import 실패: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"사람인 크롤러 실행 오류: {str(e)}")
        raise

def run_linkareer_crawler():
    """Linkareer 크롤러 실행"""
    import sys
    import os
    import logging
    
    try:
        # 프로젝트 경로를 Python path에 추가
        project_path = '/home/ttm/tensorflow-jupyter/jupyterNotebook/khj/mlops-platform'
        if project_path not in sys.path:
            sys.path.insert(0, project_path)
        
        # scrapers 디렉토리로 이동
        scrapers_path = os.path.join(project_path, 'crawling', 'scrapers')
        os.chdir(scrapers_path)
        
        # 직접 모듈 import 및 실행
        sys.path.insert(0, scrapers_path)
        

        # 일반 크롤러로 폴백
        from linkareer_crawler import LinkareerCoverLetterCrawler
        
        logging.info("Linkareer 일반 크롤러 시작...")
        crawler = LinkareerCoverLetterCrawler()
        result = crawler.crawl(max_items=50)  # crawl 메서드 파라미터 추가
        
        if result and result.get('status') == 'completed':
            logging.info(f"Linkareer 크롤러 완료: {result.get('message', '데이터 수집')}")
            return f"SUCCESS: Linkareer 크롤링 완료"
        else:
            logging.warning("Linkareer 크롤러: 수집된 데이터가 없습니다")
            return "WARNING: 수집된 데이터 없음"
            
    except ImportError as e:
        logging.error(f"Linkareer 크롤러 모듈 import 실패: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Linkareer 크롤러 실행 오류: {str(e)}")
        raise

def run_data_processing():
    """데이터 전처리 및 검증 실행"""
    import sys
    import os
    import logging
    import asyncio
    
    try:
        # 프로젝트 경로를 Python path에 추가
        project_path = '/home/ttm/tensorflow-jupyter/jupyterNotebook/khj/mlops-platform'
        if project_path not in sys.path:
            sys.path.insert(0, project_path)
        
        # crawling 디렉토리로 이동
        crawling_path = os.path.join(project_path, 'crawling')
        os.chdir(crawling_path)
        sys.path.insert(0, crawling_path)
        
        # BatchProcessorManager import 및 실행
        try:
            from batch_processor_manager import BatchProcessorManager, JobType
            
            async def process_data():
                processor = BatchProcessorManager()
                
                logging.info("데이터 처리 시작...")
                
                # 전체 파이프라인 작업 생성 및 실행
                logging.info("전체 데이터 처리 파이프라인 시작...")
                job_id = processor.create_job(JobType.FULL_PIPELINE)
                
                # 큐에서 작업 가져와서 실행
                if processor.job_queue:
                    job = processor.job_queue.pop(0)
                    result = await processor.run_job(job)
                    
                    # 결과 판단: errors가 0이고 작업이 완료되면 성공으로 판단
                    errors = result.get('errors', 0)
                    processing_time = result.get('total_processing_time', 0)
                    
                    if errors == 0:
                        duplicates_removed = result.get('cover_letters_duplicates_removed', 0)
                        logging.info(f"데이터 처리 파이프라인 완료 (처리시간: {processing_time:.2f}초, 중복제거: {duplicates_removed}개)")
                        return f"SUCCESS: 데이터 처리 완료 (중복제거: {duplicates_removed}개)"
                    else:
                        logging.warning(f"데이터 처리 중 {errors}개 오류 발생")
                        return f"WARNING: 데이터 처리 중 {errors}개 오류"
                else:
                    logging.warning("작업 큐가 비어있습니다")
                    return "WARNING: 처리할 작업이 없습니다"
                
        except ImportError:
            logging.warning("BatchProcessorManager를 찾을 수 없어 기본 처리 모드로 실행")
            
            def process_data():
                # 기본 데이터 처리 (동기 버전)
                from database import DatabaseManager
                
                db = DatabaseManager()
                
                logging.info("기본 데이터 처리 시작...")
                
                # 기본적인 데이터 정리 작업
                connection = db.get_connection()
                cursor = connection.cursor()
                
                # 빈 데이터 정리
                cursor.execute("""
                    DELETE FROM job_postings 
                    WHERE title IS NULL OR title = '' 
                    OR company IS NULL OR company = ''
                """)
                
                cursor.execute("""
                    DELETE FROM cover_letters 
                    WHERE content IS NULL OR content = '' 
                    OR LENGTH(content) < 100
                """)
                
                connection.commit()
                cursor.close()
                connection.close()
                
                logging.info("기본 데이터 처리 완료")
                return "SUCCESS: 기본 데이터 처리 완료"
        
        # 비동기 함수 실행
        try:
            result = asyncio.run(process_data())
            logging.info(f"데이터 처리 결과: {result}")
            return result
        except Exception as e:
            logging.error(f"비동기 처리 중 오류: {e}")
            # 비동기 실행 실패시 동기 모드로 폴백
            raise
            
    except ImportError as e:
        logging.error(f"데이터 처리 모듈 import 실패: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"데이터 처리 실행 오류: {str(e)}")
        raise

def generate_daily_report():
    """일일 수집 결과 리포트 생성"""
    import subprocess
    import logging
    from datetime import datetime
    
    try:
        os.chdir('/home/ttm/tensorflow-jupyter/jupyterNotebook/khj/mlops-platform/crawling')
        
        # 데이터베이스 통계 조회
        result = subprocess.run([
            'python3', '-c', 
            """
from database import DatabaseManager
from datetime import datetime

db = DatabaseManager()
db.connect()

today = datetime.now().strftime('%Y-%m-%d')

# 오늘 수집된 데이터 통계
job_count = db.execute_query("SELECT COUNT(*) as count FROM mlops.job_postings WHERE created_at::date = %s", (today,))
cover_count = db.execute_query("SELECT COUNT(*) as count FROM mlops.cover_letter_samples WHERE created_at::date = %s", (today,))

# 전체 데이터 통계  
total_jobs = db.execute_query("SELECT COUNT(*) as count FROM mlops.job_postings")
total_covers = db.execute_query("SELECT COUNT(*) as count FROM mlops.cover_letter_samples")

print(f"=== 일일 데이터 수집 리포트 ({today}) ===")
print(f"오늘 수집 - 채용공고: {job_count[0]['count'] if job_count else 0}건")
print(f"오늘 수집 - 자기소개서: {cover_count[0]['count'] if cover_count else 0}건")  
print(f"전체 누적 - 채용공고: {total_jobs[0]['count'] if total_jobs else 0}건")
print(f"전체 누적 - 자기소개서: {total_covers[0]['count'] if total_covers else 0}건")

db.disconnect()
            """
        ], capture_output=True, text=True, timeout=300)  # 5분 타임아웃
        
        logging.info(f"일일 리포트:\\n{result.stdout}")
        if result.stderr:
            logging.warning(f"리포트 생성 경고: {result.stderr}")
            
    except Exception as e:
        logging.error(f"리포트 생성 오류: {str(e)}")
        # 리포트 생성 실패는 전체 파이프라인을 중단하지 않음

# Task 정의
# 1. 사람인 크롤러 실행
saramin_task = PythonOperator(
    task_id='run_saramin_crawler',
    python_callable=run_saramin_crawler,
    dag=dag,
)

# 2. Linkareer 크롤러 실행 (사람인과 병렬)
linkareer_task = PythonOperator(
    task_id='run_linkareer_crawler', 
    python_callable=run_linkareer_crawler,
    dag=dag,
)

# 3. 데이터 처리 (크롤러들이 완료된 후)
data_processing_task = PythonOperator(
    task_id='run_data_processing',
    python_callable=run_data_processing,
    dag=dag,
)

# 4. 일일 리포트 생성
report_task = PythonOperator(
    task_id='generate_daily_report',
    python_callable=generate_daily_report,
    dag=dag,
)

# Task 의존성 설정
saramin_task >> linkareer_task >> data_processing_task >> report_task

