"""
베이스라인 모델 학습 스크립트
- 로지스틱 회귀(Logistic Regression) 모델
- Random Forest 모델
- 성능 지표: Accuracy, Precision, Recall, F1 Score, ROC-AUC
- MLflow 연동: 실험 추적 및 모델 레지스트리
"""

import sys
import os
from pathlib import Path

# 환경 변수 로드 (다른 모듈 임포트보다 먼저)
from dotenv import load_dotenv
load_dotenv()

# MLflow URI 환경 변수 설정 (mlflow_config 임포트 전에)
os.environ["MLFLOW_TRACKING_URI"] = "http://192.168.0.147:5001"

# MLFLOW_BACKEND_STORE_URI 제거 (HTTP tracking URI 사용 강제)
if "MLFLOW_BACKEND_STORE_URI" in os.environ:
    del os.environ["MLFLOW_BACKEND_STORE_URI"]

# 프로젝트 루트 경로 추가
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, 
    roc_auc_score, confusion_matrix, classification_report
)
import joblib
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# MLflow import (환경 변수 설정 후)
import mlflow
import mlflow.sklearn
from app.mlflow_config import get_or_create_experiment, MLFLOW_TRACKING_URI
from app.services.experiment_tracking import ExperimentTracker

# MLflow logged-models API 비활성화
os.environ["MLFLOW_ENABLE_LOGGED_MODEL_CREATION"] = "false"

# MLflow 설정
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
print(f"MLflow Tracking URI: {MLFLOW_TRACKING_URI}")
print(f"MLflow actual tracking URI: {mlflow.get_tracking_uri()}")

# ExperimentTracker 초기화
experiment_tracker = ExperimentTracker()

# 데이터베이스 연결 설정
DB_HOST = os.getenv('POSTGRES_HOST', '114.202.2.226')
DB_PORT = os.getenv('POSTGRES_PORT', '5433')
DB_NAME = os.getenv('POSTGRES_DB', 'postgres')
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')
DB_SCHEMA = 'mlops'

# 데이터베이스 URL 생성
import urllib.parse
encoded_password = urllib.parse.quote_plus(DB_PASSWORD)
DATABASE_URL = f"postgresql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 모델 저장 경로
MODEL_DIR = Path(__file__).parent.parent / 'models'
MODEL_DIR.mkdir(exist_ok=True)


class BaselineModelTrainer:
    """베이스라인 모델 학습 클래스"""
    
    def __init__(self):
        self.engine = create_engine(DATABASE_URL)
        self.models = {}
        self.results = {}
        
    def load_data(self, split='train'):
        """
        데이터 로드
        
        Args:
            split: 'train', 'validation', 'test'
        """
        query = f"""
        SELECT 
            id,
            embedding_array,
            is_passed
        FROM {DB_SCHEMA}.cover_letter_samples
        WHERE split = :split AND is_passed IS NOT NULL AND embedding_array IS NOT NULL
        ORDER BY id
        """
        
        with self.engine.connect() as conn:
            df = pd.read_sql(text(query), conn, params={'split': split})
        
        if len(df) == 0:
            print(f"경고: {split} 데이터가 없습니다.")
            return None, None
        
        # 임베딩 파싱 (문자열 -> numpy array)
        embeddings = []
        valid_indices = []
        
        for idx, row in df.iterrows():
            try:
                # CSV 형식의 문자열을 파싱
                embedding_str = row['embedding_array']
                if embedding_str:
                    # 쉼표로 구분된 문자열을 분리하고 float로 변환
                    embedding = [float(x) for x in embedding_str.split(',')]
                    embeddings.append(embedding)
                    valid_indices.append(idx)
            except Exception as e:
                print(f"경고: ID {row['id']} 임베딩 파싱 실패: {e}")
                continue
        
        if len(embeddings) == 0:
            print(f"경고: {split} 데이터의 임베딩을 파싱할 수 없습니다.")
            return None, None
        
        # 유효한 데이터만 선택
        df = df.iloc[valid_indices].reset_index(drop=True)
        X = np.array(embeddings)
        y = df['is_passed'].values.astype(int)
        
        print(f"\n{split.upper()} 데이터 로드 완료:")
        print(f"  샘플 수: {len(X)}건")
        print(f"  임베딩 차원: {X.shape[1]}")
        print(f"  합격: {y.sum()}건 ({y.sum()/len(y)*100:.1f}%)")
        print(f"  불합격: {(~y.astype(bool)).sum()}건 ({(~y.astype(bool)).sum()/len(y)*100:.1f}%)")
        
        return X, y
    
    def train_logistic_regression(self, X_train, y_train, mlflow_run=None):
        """로지스틱 회귀 모델 학습"""
        print("\n" + "="*60)
        print("로지스틱 회귀 모델 학습")
        print("="*60)
        
        # 하이퍼파라미터
        params = {
            'max_iter': 1000,
            'random_state': 42,
            'class_weight': 'balanced',
            'solver': 'lbfgs',
            'model_type': 'logistic_regression'
        }
        
        # MLflow에 파라미터 로깅
        if mlflow_run:
            mlflow.log_params(params)
        
        model = LogisticRegression(
            max_iter=params['max_iter'],
            random_state=params['random_state'],
            class_weight=params['class_weight'],
            solver=params['solver']
        )
        
        start_time = datetime.now()
        model.fit(X_train, y_train)
        elapsed = (datetime.now() - start_time).total_seconds()
        
        # MLflow에 학습 시간 로깅
        if mlflow_run:
            mlflow.log_metric("training_time_seconds", elapsed)
        
        print(f"학습 완료 (소요 시간: {elapsed:.2f}초)")
        
        self.models['logistic_regression'] = model
        return model
    
    def train_random_forest(self, X_train, y_train, mlflow_run=None):
        """Random Forest 모델 학습"""
        print("\n" + "="*60)
        print("Random Forest 모델 학습")
        print("="*60)
        
        # 하이퍼파라미터
        params = {
            'n_estimators': 100,
            'max_depth': 10,
            'min_samples_split': 10,
            'min_samples_leaf': 4,
            'random_state': 42,
            'class_weight': 'balanced',
            'n_jobs': -1,
            'model_type': 'random_forest'
        }
        
        # MLflow에 파라미터 로깅
        if mlflow_run:
            mlflow.log_params(params)
        
        model = RandomForestClassifier(
            n_estimators=params['n_estimators'],
            max_depth=params['max_depth'],
            min_samples_split=params['min_samples_split'],
            min_samples_leaf=params['min_samples_leaf'],
            random_state=params['random_state'],
            class_weight=params['class_weight'],
            n_jobs=params['n_jobs']
        )
        
        start_time = datetime.now()
        model.fit(X_train, y_train)
        elapsed = (datetime.now() - start_time).total_seconds()
        
        # MLflow에 학습 시간 로깅
        if mlflow_run:
            mlflow.log_metric("training_time_seconds", elapsed)
        
        print(f"학습 완료 (소요 시간: {elapsed:.2f}초)")
        
        self.models['random_forest'] = model
        return model
    
    def evaluate_model(self, model, X, y, dataset_name='Test', mlflow_run=None):
        """
        모델 평가
        
        Args:
            model: 학습된 모델
            X: 입력 데이터
            y: 타겟 레이블
            dataset_name: 데이터셋 이름
            mlflow_run: MLflow run 객체
        """
        # 예측
        y_pred = model.predict(X)
        y_pred_proba = model.predict_proba(X)[:, 1]
        
        # 성능 지표 계산
        accuracy = accuracy_score(y, y_pred)
        precision = precision_score(y, y_pred)
        recall = recall_score(y, y_pred)
        f1 = f1_score(y, y_pred)
        roc_auc = roc_auc_score(y, y_pred_proba)
        
        # 혼동 행렬
        cm = confusion_matrix(y, y_pred)
        
        # MLflow에 메트릭 로깅
        if mlflow_run:
            prefix = dataset_name.lower()
            mlflow.log_metric(f"{prefix}_accuracy", accuracy)
            mlflow.log_metric(f"{prefix}_precision", precision)
            mlflow.log_metric(f"{prefix}_recall", recall)
            mlflow.log_metric(f"{prefix}_f1_score", f1)
            mlflow.log_metric(f"{prefix}_roc_auc", roc_auc)
            
            # 혼동 행렬 메트릭
            mlflow.log_metric(f"{prefix}_tn", int(cm[0][0]))
            mlflow.log_metric(f"{prefix}_fp", int(cm[0][1]))
            mlflow.log_metric(f"{prefix}_fn", int(cm[1][0]))
            mlflow.log_metric(f"{prefix}_tp", int(cm[1][1]))
        
        # 결과 출력
        print(f"\n{dataset_name} 성능 평가:")
        print(f"  Accuracy:  {accuracy:.4f}")
        print(f"  Precision: {precision:.4f}")
        print(f"  Recall:    {recall:.4f}")
        print(f"  F1 Score:  {f1:.4f}")
        print(f"  ROC-AUC:   {roc_auc:.4f}")
        print(f"\n혼동 행렬:")
        print(f"  TN: {cm[0][0]:3d}  FP: {cm[0][1]:3d}")
        print(f"  FN: {cm[1][0]:3d}  TP: {cm[1][1]:3d}")
        
        # 상세 리포트
        print(f"\n분류 리포트:")
        print(classification_report(y, y_pred, target_names=['불합격', '합격']))
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'roc_auc': roc_auc,
            'confusion_matrix': cm.tolist(),
            'dataset': dataset_name
        }
    
    def save_model(self, model_name):
        """모델 저장"""
        if model_name not in self.models:
            print(f"경고: {model_name} 모델을 찾을 수 없습니다.")
            return
        
        model = self.models[model_name]
        model_path = MODEL_DIR / f'{model_name}_baseline.joblib'
        
        joblib.dump(model, model_path)
        print(f"\n모델 저장 완료: {model_path}")
    
    def save_results(self):
        """평가 결과 저장"""
        results_path = MODEL_DIR / 'baseline_results.json'
        
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n평가 결과 저장 완료: {results_path}")
    
    def run(self):
        """전체 프로세스 실행 (ExperimentTracker 사용)"""
        print("="*60)
        print("베이스라인 모델 학습 시작 (ExperimentTracker 사용)")
        print("="*60)
        
        start_time = datetime.now()
        
        # MLflow 실험 설정 (ExperimentTracker 사용)
        experiment_name = "baseline-models-2025"
        
        # 디버깅 정보
        print(f"Current directory: {os.getcwd()}")
        print(f"MLflow tracking URI from mlflow: {mlflow.get_tracking_uri()}")
        print(f"MLflow tracking URI from ExperimentTracker: {experiment_tracker.tracking_uri}")
        
        experiment_id = experiment_tracker.create_experiment(
            name=experiment_name,
            tags={
                "project": "mlops-platform",
                "phase": "baseline",
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        )
        print(f"실험 ID: {experiment_id}")
        
        # 실험 확인 (디버깅)
        try:
            exp = mlflow.get_experiment(experiment_id)
            print(f"실험 확인: {exp.name}, artifact_location: {exp.artifact_location}")
        except Exception as e:
            print(f"실험 확인 실패: {e}")
        
        try:
            # 1. 데이터 로드
            print("\n[1단계] 데이터 로드")
            X_train, y_train = self.load_data('train')
            X_val, y_val = self.load_data('validation')
            X_test, y_test = self.load_data('test')
            
            if X_train is None or X_val is None or X_test is None:
                print("\n오류: 데이터 로드 실패")
                return
            
            # 데이터 메타정보
            data_info = {
                'train_samples': len(X_train),
                'val_samples': len(X_val),
                'test_samples': len(X_test),
                'embedding_dim': X_train.shape[1],
                'train_positive_ratio': float(y_train.sum() / len(y_train))
            }
            
            # 2. 로지스틱 회귀 학습 및 평가 (ExperimentTracker)
            print("\n[2단계] 로지스틱 회귀 모델")
            
            # Run 시작
            lr_run_id = experiment_tracker.start_run(
                experiment_id=experiment_id,
                run_name="Logistic_Regression_Baseline",
                tags={
                    "model_type": "logistic_regression",
                    "phase": "baseline",
                    "framework": "scikit-learn"
                }
            )
            
            try:
                # 데이터 정보 로깅
                experiment_tracker.log_params(lr_run_id, data_info)
                
                # 모델 학습
                with mlflow.start_run(run_id=lr_run_id):
                    lr_model = self.train_logistic_regression(X_train, y_train, mlflow_run=True)
                    
                    # 평가
                    lr_train_results = self.evaluate_model(lr_model, X_train, y_train, 'Train', mlflow_run=True)
                    lr_val_results = self.evaluate_model(lr_model, X_val, y_val, 'Validation', mlflow_run=True)
                    lr_test_results = self.evaluate_model(lr_model, X_test, y_test, 'Test', mlflow_run=True)
                    
                    # 모델 저장 (ExperimentTracker)
                    experiment_tracker.log_model(
                        run_id=lr_run_id,
                        model=lr_model,
                        artifact_path="model",
                        registered_model_name="LogisticRegression_CoverLetter"
                    )
                
                self.results['logistic_regression'] = {
                    'train': lr_train_results,
                    'validation': lr_val_results,
                    'test': lr_test_results,
                    'mlflow_run_id': lr_run_id
                }
                
                print(f"\nMLflow Run ID: {lr_run_id}")
                
            except Exception as e:
                print(f"로지스틱 회귀 학습 중 오류: {e}")
                import traceback
                traceback.print_exc()
            
            self.save_model('logistic_regression')
            
            # 3. Random Forest 학습 및 평가 (ExperimentTracker)
            print("\n[3단계] Random Forest 모델")
            
            # Run 시작
            rf_run_id = experiment_tracker.start_run(
                experiment_id=experiment_id,
                run_name="RandomForest_Baseline",
                tags={
                    "model_type": "random_forest",
                    "phase": "baseline",
                    "framework": "scikit-learn"
                }
            )
            
            try:
                # 데이터 정보 로깅
                experiment_tracker.log_params(rf_run_id, data_info)
                
                # 모델 학습
                with mlflow.start_run(run_id=rf_run_id):
                    rf_model = self.train_random_forest(X_train, y_train, mlflow_run=True)
                    
                    # 평가
                    rf_train_results = self.evaluate_model(rf_model, X_train, y_train, 'Train', mlflow_run=True)
                    rf_val_results = self.evaluate_model(rf_model, X_val, y_val, 'Validation', mlflow_run=True)
                    rf_test_results = self.evaluate_model(rf_model, X_test, y_test, 'Test', mlflow_run=True)
                    
                    # 모델 저장 (ExperimentTracker)
                    experiment_tracker.log_model(
                        run_id=rf_run_id,
                        model=rf_model,
                        artifact_path="model",
                        registered_model_name="RandomForest_CoverLetter"
                    )
                
                self.results['random_forest'] = {
                    'train': rf_train_results,
                    'validation': rf_val_results,
                    'test': rf_test_results,
                    'mlflow_run_id': rf_run_id
                }
                
                print(f"\nMLflow Run ID: {rf_run_id}")
                
            except Exception as e:
                print(f"Random Forest 학습 중 오류: {e}")
                import traceback
                traceback.print_exc()
            
            self.save_model('random_forest')
            
            # 4. 결과 저장
            print("\n[4단계] 결과 저장")
            self.save_results()
            
            # 5. 모델 비교
            print("\n" + "="*60)
            print("모델 비교 (Test Set)")
            print("="*60)
            print(f"\n{'모델':<20} {'Accuracy':<10} {'F1 Score':<10} {'ROC-AUC':<10}")
            print("-" * 50)
            print(f"{'Logistic Regression':<20} {lr_test_results['accuracy']:<10.4f} {lr_test_results['f1_score']:<10.4f} {lr_test_results['roc_auc']:<10.4f}")
            print(f"{'Random Forest':<20} {rf_test_results['accuracy']:<10.4f} {rf_test_results['f1_score']:<10.4f} {rf_test_results['roc_auc']:<10.4f}")
            
            # 최고 성능 모델 찾기 (ExperimentTracker 사용)
            print("\n[6단계] 최고 성능 모델 선택")
            best_run = experiment_tracker.get_best_run(
                experiment_id=experiment_id,
                metric_key="test_f1_score",
                ascending=False
            )
            
            if best_run:
                best_model_name = best_run.get('tags', {}).get('model_type', 'Unknown')
                best_f1 = best_run.get('metrics', {}).get('test_f1_score', 0)
                print(f"✓ 최고 성능 모델: {best_model_name} (F1 Score: {best_f1:.4f})")
                print(f"  Run ID: {best_run['run_id']}")
                
                # Production 스테이지로 승격
                try:
                    if best_model_name == 'logistic_regression':
                        model_name = "LogisticRegression_CoverLetter"
                    else:
                        model_name = "RandomForest_CoverLetter"
                    
                    # 모델 레지스트리에서 최신 버전 조회 (max_results 명시)
                    model_versions = mlflow.search_registered_models(
                        filter_string=f"name='{model_name}'",
                        max_results=100
                    )
                    if model_versions and len(model_versions) > 0:
                        latest_versions = model_versions[0].latest_versions
                        if latest_versions and len(latest_versions) > 0:
                            # 버전을 안전하게 정수로 변환
                            version_numbers = []
                            for v in latest_versions:
                                try:
                                    version_numbers.append(int(str(v.version)))
                                except (ValueError, AttributeError):
                                    continue
                            
                            if version_numbers:
                                latest_version = max(version_numbers)
                                
                                # Production으로 승격
                                experiment_tracker.transition_model_stage(
                                    model_name=model_name,
                                    version=str(latest_version),
                                    stage="Production",
                                    archive_existing_versions=True
                                )
                                print(f"✓ 모델 {model_name} v{latest_version}을 Production으로 승격했습니다.")
                            else:
                                print(f"  경고: {model_name} 모델 버전을 찾을 수 없습니다.")
                        else:
                            print(f"  경고: {model_name} 모델이 등록되어 있지만 버전이 없습니다.")
                    else:
                        print(f"  경고: {model_name} 모델이 Model Registry에 등록되지 않았습니다.")
                        print(f"  (권한 문제로 인해 모델이 MLflow에 저장되지 않았을 수 있습니다)")
                except Exception as e:
                    print(f"  모델 승격 중 오류 (무시): {e}")
                    import traceback
                    traceback.print_exc()
            
            end_time = datetime.now()
            elapsed = (end_time - start_time).total_seconds()
            
            print("\n" + "="*60)
            print(f"베이스라인 모델 학습 완료 (소요 시간: {elapsed:.2f}초)")
            print(f"MLflow UI: {MLFLOW_TRACKING_URI}")
            print(f"실험 ID: {experiment_id}")
            print("="*60)
            
        except Exception as e:
            print(f"\n오류 발생: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    trainer = BaselineModelTrainer()
    trainer.run()
 