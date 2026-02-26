"""
Saramin 크롤러 단독 테스트 DAG
- 트랜잭션 충돌 없이 Saramin 크롤러만 실행
"""

from datetime import datetime, timedelta
from airflow import DAG
try:
    from airflow.operators.python import PythonOperator
except ImportError:
    from airflow.operators.python_operator import PythonOperator

import sys
import os
import logging

# 프로젝트 경로를 Python path에 추가
project_path = '/home/ttm/tensorflow-jupyter/jupyterNotebook/khj/mlops-platform'
sys.path.append(project_path)

# 기본 DAG 설정
default_args = {
    'owner': 'mlops-platform',
    'depends_on_past': False,
    'start_date': datetime(2025, 10, 17),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

# DAG 정의
dag = DAG(
    'saramin_only_test',
    default_args=default_args,
    description='Saramin 크롤러 단독 테스트',
    schedule=None,  # 수동 실행만
    start_date=datetime(2025, 10, 17),
    catchup=False,
    tags=['test', 'saramin'],
)

def run_saramin_crawler_only():
    """사람인 크롤러 단독 실행"""
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
        
        logging.info("=== Saramin 크롤러 단독 테스트 시작 ===")
        crawler = SaraminCrawler()
        
        # 크롤러 실행 (실시간 DB 저장 방식, 500개 수집)
        result = crawler.crawl_jobs(max_jobs=500, save_to_db=True)
        
        if result and len(result) > 0:
            logging.info(f"✅ Saramin 크롤러 단독 테스트 완료: {len(result)}개 채용공고 수집 및 저장")
            return f"SUCCESS: {len(result)}개 채용공고 수집 및 저장"
        else:
            logging.warning("⚠️ Saramin 크롤러: 수집된 데이터가 없습니다")
            return "WARNING: 수집된 데이터 없음"
            
    except ImportError as e:
        logging.error(f"❌ Saramin 크롤러 모듈 import 실패: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"❌ Saramin 크롤러 실행 오류: {str(e)}")
        raise

# Task 정의
saramin_only_task = PythonOperator(
    task_id='run_saramin_crawler_only',
    python_callable=run_saramin_crawler_only,
    dag=dag,
)