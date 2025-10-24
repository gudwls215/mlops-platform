"""
Linkareer 자기소개서 크롤링 DAG
매일 새벽 3시에 자기소개서를 수집합니다.
"""
from datetime import datetime, timedelta
from airflow import DAG
try:
    from airflow.operators.python import PythonOperator
except ImportError:
    from airflow.operators.python_operator import PythonOperator

import sys
import os

# 프로젝트 경로 추가
project_path = '/home/ttm/tensorflow-jupyter/jupyterNotebook/khj/mlops-platform'
sys.path.append(project_path)
sys.path.append(os.path.join(project_path, 'crawling'))
sys.path.append(os.path.join(project_path, 'crawling', 'scrapers'))

# 기본 DAG 설정
default_args = {
    'owner': 'mlops-platform',
    'depends_on_past': False,
    'start_date': datetime(2025, 10, 24),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# DAG 정의
dag = DAG(
    'linkareer_cover_letter_crawl',
    default_args=default_args,
    description='Linkareer 자기소개서 수집 DAG',
    schedule_interval='0 3 * * *',  # 매일 새벽 3시
    catchup=False,
    tags=['crawling', 'cover-letter', 'linkareer'],
)


def run_linkareer_crawler(**context):
    """Linkareer 크롤러 실행"""
    import sys
    import os
    
    try:
        # 프로젝트 경로 추가
        project_path = '/home/ttm/tensorflow-jupyter/jupyterNotebook/khj/mlops-platform'
        sys.path.insert(0, project_path)
        sys.path.insert(0, os.path.join(project_path, 'crawling'))
        sys.path.insert(0, os.path.join(project_path, 'crawling', 'scrapers'))
        
        from scrapers.linkareer_crawler import LinkareerCoverLetterCrawler
        
        print("=" * 80)
        print(f"Linkareer 크롤링 시작: {datetime.now()}")
        print("=" * 80)
        
        # 크롤러 실행
        crawler = LinkareerCoverLetterCrawler()
        result = crawler.crawl(max_items=100)  # 한 번에 100개씩 수집
        
        print("\n" + "=" * 80)
        print(f"크롤링 완료: {datetime.now()}")
        print(f"결과: {result}")
        print("=" * 80)
        
        # XCom에 결과 저장
        context['ti'].xcom_push(key='crawl_result', value=result)
        context['ti'].xcom_push(key='data_count', value=result.get('data_count', 0))
        
        return result
        
    except Exception as e:
        print(f"❌ 크롤링 오류: {e}")
        import traceback
        traceback.print_exc()
        raise


def check_data_status(**context):
    """자기소개서 데이터 수집 상태 점검"""
    from sqlalchemy import create_engine, text
    from dotenv import load_dotenv
    import os
    
    load_dotenv()
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL이 설정되지 않았습니다.")
        return
    
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT COUNT(*) as total,
                   COUNT(DISTINCT company) as companies,
                   COUNT(CASE WHEN is_passed = true THEN 1 END) as passed
            FROM mlops.cover_letters
        """))
        
        row = result.fetchone()
        
        print("\n" + "=" * 80)
        print("📊 자기소개서 수집 현황")
        print("=" * 80)
        print(f"  총 자기소개서: {row.total}건")
        print(f"  고유 회사: {row.companies}개")
        print(f"  합격 자소서: {row.passed}건")
        print(f"  목표 대비: {row.total / 1000 * 100:.1f}% (목표 1,000건)")
        print("=" * 80)
        
        # XCom에 상태 저장
        ti = context['ti']
        ti.xcom_push(key='total_cover_letters', value=row.total)
        ti.xcom_push(key='total_companies', value=row.companies)
        ti.xcom_push(key='passed_count', value=row.passed)


def send_notification(**context):
    """크롤링 결과 알림"""
    ti = context['ti']
    
    # 이전 태스크의 결과 가져오기
    crawl_result = ti.xcom_pull(key='crawl_result', task_ids='run_linkareer_crawler')
    total_cover_letters = ti.xcom_pull(key='total_cover_letters', task_ids='check_status')
    
    print("\n" + "=" * 80)
    print("📢 Linkareer 크롤링 완료 알림")
    print("=" * 80)
    print(f"  크롤링 결과: {crawl_result}")
    print(f"  누적 데이터: {total_cover_letters}건")
    print(f"  진행률: {total_cover_letters / 1000 * 100:.1f}% (목표 1,000건)")
    print("=" * 80)


# 태스크 정의
task_run_crawler = PythonOperator(
    task_id='run_linkareer_crawler',
    python_callable=run_linkareer_crawler,
    provide_context=True,
    dag=dag,
)

task_check_status = PythonOperator(
    task_id='check_status',
    python_callable=check_data_status,
    provide_context=True,
    dag=dag,
)

task_send_notification = PythonOperator(
    task_id='send_notification',
    python_callable=send_notification,
    provide_context=True,
    dag=dag,
)

# 태스크 의존성 설정
task_run_crawler >> task_check_status >> task_send_notification
