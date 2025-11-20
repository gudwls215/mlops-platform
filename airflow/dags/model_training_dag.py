"""
MLOps Platform 모델 학습 DAG with MLflow
- 신규 데이터 확인
- 모델 학습 실행
- MLflow에 실험 기록
- 모델 평가 및 Registry 등록
- Production 스테이지 자동 승격
"""

from datetime import datetime, timedelta
from airflow import DAG
try:
    from airflow.operators.python import PythonOperator, BranchPythonOperator
    from airflow.operators.bash import BashOperator
except ImportError:
    from airflow.operators.python_operator import PythonOperator, BranchPythonOperator
    from airflow.operators.bash_operator import BashOperator

try:
    from airflow.operators.empty import EmptyOperator as DummyOperator
except ImportError:
    try:
        from airflow.operators.dummy import DummyOperator
    except ImportError:
        from airflow.operators.dummy_operator import DummyOperator

import sys
import os
import logging
from pathlib import Path

# 프로젝트 경로 설정
project_path = '/home/ttm/tensorflow-jupyter/jupyterNotebook/khj/mlops-platform'
sys.path.append(project_path)
sys.path.append(os.path.join(project_path, 'backend'))

# 환경 변수 설정
os.environ['PYTHONPATH'] = f"{project_path}:{os.path.join(project_path, 'backend')}"

logger = logging.getLogger(__name__)

# DAG 기본 설정
default_args = {
    'owner': 'mlops-platform',
    'depends_on_past': False,
    'start_date': datetime(2025, 11, 10),
    'email_on_failure': True,
    'email': ['admin@mlops-platform.com'],
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=10),
}


def check_new_data(**context):
    """
    신규 데이터 확인
    - 전체 학습 가능한 데이터 수 확인
    - 임계값: 최소 100건 이상 (충분한 학습 데이터)
    """
    import psycopg2
    from datetime import datetime, timedelta
    
    logger.info("학습 데이터 확인 시작...")
    
    try:
        # DB 연결
        conn = psycopg2.connect(
            host='114.202.2.226',
            port=5433,
            database='postgres',
            user='postgres',
            password='xlxldpa!@#'
        )
        cursor = conn.cursor()
        
        # 전체 라벨링 데이터 수 확인 (is_passed가 NOT NULL인 데이터)
        cursor.execute("""
            SELECT COUNT(*) 
            FROM mlops.cover_letter_samples 
            WHERE is_passed IS NOT NULL
        """)
        
        total_data_count = cursor.fetchone()[0]
        
        # 최근 7일 내 신규 데이터도 확인
        last_week = datetime.now() - timedelta(days=7)
        cursor.execute("""
            SELECT COUNT(*) 
            FROM mlops.cover_letter_samples 
            WHERE is_passed IS NOT NULL 
            AND created_at > %s
        """, (last_week,))
        
        new_data_count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        logger.info(f"전체 라벨링 데이터: {total_data_count}건")
        logger.info(f"최근 7일 신규 데이터: {new_data_count}건")
        
        # XCom에 데이터 수 저장
        context['task_instance'].xcom_push(key='total_data_count', value=total_data_count)
        context['task_instance'].xcom_push(key='new_data_count', value=new_data_count)
        
        # 임계값: 전체 100건 이상
        THRESHOLD = 100
        
        if total_data_count >= THRESHOLD:
            logger.info(f"학습 데이터 {total_data_count}건 >= 임계값 {THRESHOLD}건: 학습 진행")
            return 'train_model'
        else:
            logger.info(f"학습 데이터 {total_data_count}건 < 임계값 {THRESHOLD}건: 학습 스킵")
            return 'skip_training'
            
    except Exception as e:
        logger.error(f"학습 데이터 확인 실패: {e}")
        raise


def train_model(**context):
    """
    모델 학습 실행 with MLflow
    """
    import subprocess
    
    logger.info("모델 학습 시작...")
    
    # 학습 스크립트 경로
    script_path = os.path.join(project_path, 'backend', 'scripts', 'train_baseline_models.py')
    
    try:
        # 학습 스크립트 실행
        result = subprocess.run(
            ['python3', script_path],
            cwd=os.path.join(project_path, 'backend'),
            capture_output=True,
            text=True,
            timeout=3600  # 1시간 타임아웃
        )
        
        if result.returncode == 0:
            logger.info("모델 학습 완료")
            logger.info(f"출력: {result.stdout}")
            
            # XCom에 성공 상태 저장
            context['task_instance'].xcom_push(key='training_status', value='success')
            return True
        else:
            logger.error(f"모델 학습 실패: {result.stderr}")
            context['task_instance'].xcom_push(key='training_status', value='failed')
            raise Exception(f"학습 스크립트 실행 실패: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        logger.error("모델 학습 타임아웃")
        raise
    except Exception as e:
        logger.error(f"모델 학습 중 오류: {e}")
        raise


def evaluate_model(**context):
    """
    학습된 모델 평가 및 MLflow에서 최고 성능 모델 찾기
    """
    logger.info("모델 평가 시작...")
    
    try:
        from app.services.experiment_tracking import ExperimentTracker
        
        tracker = ExperimentTracker()
        
        # 실험 이름으로 실험 ID 조회
        experiment_name = "baseline-models-2025"
        experiments = tracker.client.search_experiments(
            filter_string=f"name = '{experiment_name}'"
        )
        
        if not experiments:
            logger.error(f"실험 '{experiment_name}'을 찾을 수 없습니다.")
            return False
        
        experiment_id = experiments[0].experiment_id
        logger.info(f"실험 ID: {experiment_id}")
        
        # 최고 성능 모델 찾기
        best_run = tracker.get_best_run(
            experiment_id=experiment_id,
            metric_key="test_f1_score",
            ascending=False
        )
        
        if best_run:
            logger.info(f"최고 성능 모델 발견:")
            logger.info(f"  - Run ID: {best_run['run_id']}")
            logger.info(f"  - Metrics: {best_run['metrics']}")
            
            # test_f1_score 메트릭 확인
            if 'test_f1_score' not in best_run['metrics']:
                logger.error(f"test_f1_score 메트릭을 찾을 수 없습니다. 사용 가능한 메트릭: {list(best_run['metrics'].keys())}")
                return False
            
            f1_score = best_run['metrics']['test_f1_score']
            accuracy = best_run['metrics'].get('test_accuracy', 'N/A')
            
            logger.info(f"  - F1 Score: {f1_score:.4f}")
            logger.info(f"  - Accuracy: {accuracy if accuracy == 'N/A' else f'{accuracy:.4f}'}")
            
            # XCom에 최고 성능 모델 정보 저장
            context['task_instance'].xcom_push(key='best_run_id', value=best_run['run_id'])
            context['task_instance'].xcom_push(key='best_f1_score', value=f1_score)
            
            logger.info(f"XCom에 저장: best_run_id={best_run['run_id']}, best_f1_score={f1_score}")
            
            return True
        else:
            logger.warning("최고 성능 모델을 찾을 수 없습니다.")
            return False
            
    except Exception as e:
        logger.error(f"모델 평가 실패: {e}")
        raise


def register_model(**context):
    """
    최고 성능 모델을 MLflow Model Registry에 등록
    """
    logger.info("모델 등록 시작...")
    
    try:
        from app.services.experiment_tracking import ExperimentTracker
        import mlflow
        
        tracker = ExperimentTracker()
        
        # 최고 성능 모델 정보 가져오기
        best_run_id = context['task_instance'].xcom_pull(key='best_run_id', task_ids='evaluate_model')
        best_f1_score = context['task_instance'].xcom_pull(key='best_f1_score', task_ids='evaluate_model')
        
        if not best_run_id:
            logger.error("최고 성능 모델 정보가 없습니다.")
            return False
        
        # 모델 이름
        model_name = "LogisticRegression_CoverLetter"
        
        # 모델 등록
        model_uri = f"runs:/{best_run_id}/model"
        
        model_version = mlflow.register_model(
            model_uri=model_uri,
            name=model_name,
            tags={
                "trained_by": "airflow",
                "f1_score": str(best_f1_score),
                "training_date": datetime.now().isoformat()
            }
        )
        
        logger.info(f"모델 등록 완료: {model_name} v{model_version.version}")
        
        # XCom에 모델 버전 정보 저장
        context['task_instance'].xcom_push(key='model_version', value=model_version.version)
        
        return True
        
    except Exception as e:
        logger.error(f"모델 등록 실패: {e}")
        raise


def promote_to_production(**context):
    """
    모델을 Production 스테이지로 승격
    - 기준: F1 Score >= 0.55
    """
    logger.info("모델 승격 검토 시작...")
    
    try:
        from app.services.experiment_tracking import ExperimentTracker
        import mlflow
        from mlflow.tracking import MlflowClient
        
        tracker = ExperimentTracker()
        client = MlflowClient()
        
        # 최고 성능 모델 정보
        best_f1_score = context['task_instance'].xcom_pull(key='best_f1_score', task_ids='evaluate_model')
        model_version = context['task_instance'].xcom_pull(key='model_version', task_ids='register_model')
        
        logger.info(f"XCom에서 가져온 값 - best_f1_score: {best_f1_score}, model_version: {model_version}")
        
        # 값 검증
        if best_f1_score is None:
            logger.error("best_f1_score가 None입니다. evaluate_model 태스크에서 메트릭을 찾지 못했을 수 있습니다.")
            raise ValueError("best_f1_score is None")
        
        if model_version is None:
            logger.error("model_version이 None입니다. register_model 태스크가 실패했을 수 있습니다.")
            raise ValueError("model_version is None")
        
        # 승격 기준
        F1_THRESHOLD = 0.55
        
        model_name = "LogisticRegression_CoverLetter"
        
        if best_f1_score >= F1_THRESHOLD:
            logger.info(f"F1 Score {best_f1_score:.4f} >= 기준 {F1_THRESHOLD}: Production 승격")
            
            # 기존 Production 모델을 Archived로 변경
            try:
                current_prod_versions = client.get_latest_versions(modㅁel_name, stages=["Production"])
                for version in current_prod_versions:
                    client.transition_model_version_stage(
                        name=model_name,
                        version=version.version,
                        stage="Archived"
                    )
                    logger.info(f"기존 Production 모델 v{version.version} -> Archived")
            except Exception as e:
                logger.warning(f"기존 Production 모델 처리 중 오류: {e}")
            
            # 새 모델을 Production으로 승격
            client.transition_model_version_stage(
                name=model_name,
                version=model_version,
                stage="Production",
                archive_existing_versions=True
            )
            
            logger.info(f"모델 v{model_version} -> Production 승격 완료")
            
            # 설명 추가
            client.update_model_version(
                name=model_name,
                version=model_version,
                description=f"Auto-promoted by Airflow on {datetime.now().isoformat()} (F1: {best_f1_score:.4f})"
            )
            
            return 'send_success_notification'
        else:
            logger.info(f"F1 Score {best_f1_score:.4f} < 기준 {F1_THRESHOLD}: Staging 유지")
            
            # Staging 스테이지로 설정
            client.transition_model_version_stage(
                name=model_name,
                version=model_version,
                stage="Staging"
            )
            
            logger.info(f"모델 v{model_version} -> Staging 설정 완료")
            
            return 'send_low_performance_notification'
            
    except Exception as e:
        logger.error(f"모델 승격 실패: {e}")
        raise


def send_success_notification(**context):
    """
    성공 알림 전송 (로그로 대체)
    """
    best_f1_score = context['task_instance'].xcom_pull(key='best_f1_score', task_ids='evaluate_model')
    model_version = context['task_instance'].xcom_pull(key='model_version', task_ids='register_model')
    
    message = f"""
    ✅ 모델 학습 및 배포 성공
    
    - 모델 버전: v{model_version}
    - F1 Score: {best_f1_score:.4f}
    - 스테이지: Production
    - 배포 시간: {datetime.now().isoformat()}
    
    모델이 자동으로 Production에 배포되었습니다.
    """
    
    logger.info(message)
    print(message)


def send_low_performance_notification(**context):
    """
    성능 미달 알림 전송 (로그로 대체)
    """
    best_f1_score = context['task_instance'].xcom_pull(key='best_f1_score', task_ids='evaluate_model')
    model_version = context['task_instance'].xcom_pull(key='model_version', task_ids='register_model')
    
    message = f"""
    ⚠️ 모델 학습 완료 (성능 미달)
    
    - 모델 버전: v{model_version}
    - F1 Score: {best_f1_score:.4f}
    - 스테이지: Staging
    - 배포 시간: {datetime.now().isoformat()}
    
    성능이 기준(F1 >= 0.55)에 미달하여 Staging에 유지됩니다.
    추가 데이터 수집 또는 모델 개선이 필요합니다.
    """
    
    logger.warning(message)
    print(message)


# DAG 정의
dag = DAG(
    'model_training_mlflow_pipeline',
    default_args=default_args,
    description='MLflow 연동 모델 학습 및 배포 자동화',
    schedule='0 3 * * *',  # 매일 새벽 3시 실행
    start_date=datetime(2025, 11, 10),
    catchup=False,
    tags=['ml', 'mlflow', 'training', 'automation'],
)

# Task 정의
start = DummyOperator(
    task_id='start',
    dag=dag
)

check_data = BranchPythonOperator(
    task_id='check_new_data',
    python_callable=check_new_data,
    dag=dag
)

skip = DummyOperator(
    task_id='skip_training',
    dag=dag
)

train = PythonOperator(
    task_id='train_model',
    python_callable=train_model,
    dag=dag
)

evaluate = PythonOperator(
    task_id='evaluate_model',
    python_callable=evaluate_model,
    dag=dag
)

register = PythonOperator(
    task_id='register_model',
    python_callable=register_model,
    dag=dag
)

promote = BranchPythonOperator(
    task_id='promote_to_production',
    python_callable=promote_to_production,
    dag=dag
)

notify_success = PythonOperator(
    task_id='send_success_notification',
    python_callable=send_success_notification,
    dag=dag
)

notify_low_perf = PythonOperator(
    task_id='send_low_performance_notification',
    python_callable=send_low_performance_notification,
    dag=dag
)

end = DummyOperator(
    task_id='end',
    dag=dag,
    trigger_rule='none_failed_min_one_success'
)

# Task 의존성 설정
start >> check_data
check_data >> [skip, train]
train >> evaluate >> register >> promote
promote >> [notify_success, notify_low_perf]
[skip, notify_success, notify_low_perf] >> end
