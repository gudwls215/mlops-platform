"""
모델 최적화 스크립트 - 하이퍼파라미터 튜닝
- Grid Search를 사용한 최적 파라미터 탐색
- 교차 검증 (Cross Validation)
- 과적합 개선을 위한 정규화 강화
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV, cross_val_score
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, 
    roc_auc_score, make_scorer
)
from dotenv import load_dotenv
import joblib
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 환경 변수 로드
load_dotenv()

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


class ModelOptimizer:
    """모델 최적화 클래스"""
    
    def __init__(self):
        self.engine = create_engine(DATABASE_URL)
        self.best_models = {}
        self.results = {}
        
    def load_data(self, split='train'):
        """데이터 로드"""
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
            return None, None
        
        # 임베딩 파싱
        embeddings = []
        valid_indices = []
        
        for idx, row in df.iterrows():
            try:
                embedding_str = row['embedding_array']
                if embedding_str:
                    embedding = [float(x) for x in embedding_str.split(',')]
                    embeddings.append(embedding)
                    valid_indices.append(idx)
            except Exception:
                continue
        
        if len(embeddings) == 0:
            return None, None
        
        df = df.iloc[valid_indices].reset_index(drop=True)
        X = np.array(embeddings)
        y = df['is_passed'].values.astype(int)
        
        print(f"{split.upper()}: {len(X)}건 (합격 {y.sum()}건, 불합격 {len(y)-y.sum()}건)")
        
        return X, y
    
    def optimize_logistic_regression(self, X_train, y_train, X_val, y_val):
        """로지스틱 회귀 하이퍼파라미터 튜닝"""
        print("\n" + "="*60)
        print("로지스틱 회귀 최적화")
        print("="*60)
        
        # 파라미터 그리드 (과적합 방지를 위한 강한 정규화)
        param_grid = {
            'C': [0.001, 0.01, 0.1, 1.0, 10.0],  # 정규화 강도 (작을수록 강함)
            'penalty': ['l1', 'l2'],
            'solver': ['liblinear', 'saga'],
            'max_iter': [1000],
            'class_weight': ['balanced']
        }
        
        # Grid Search with Cross Validation
        lr = LogisticRegression(random_state=42)
        
        # F1 Score를 최적화 목표로 설정
        f1_scorer = make_scorer(f1_score)
        
        grid_search = GridSearchCV(
            lr, 
            param_grid, 
            cv=5,  # 5-fold Cross Validation
            scoring=f1_scorer,
            n_jobs=-1,
            verbose=1
        )
        
        print("Grid Search 시작...")
        start_time = datetime.now()
        grid_search.fit(X_train, y_train)
        elapsed = (datetime.now() - start_time).total_seconds()
        
        print(f"\nGrid Search 완료 (소요 시간: {elapsed:.2f}초)")
        print(f"최적 파라미터: {grid_search.best_params_}")
        print(f"최적 CV F1 Score: {grid_search.best_score_:.4f}")
        
        # 최적 모델
        best_model = grid_search.best_estimator_
        
        # 교차 검증 점수
        cv_scores = cross_val_score(best_model, X_train, y_train, cv=5, scoring=f1_scorer)
        print(f"CV F1 Scores: {cv_scores}")
        print(f"CV F1 Mean: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
        
        # Validation 성능 평가
        y_val_pred = best_model.predict(X_val)
        val_f1 = f1_score(y_val, y_val_pred)
        val_accuracy = accuracy_score(y_val, y_val_pred)
        
        print(f"\nValidation 성능:")
        print(f"  Accuracy: {val_accuracy:.4f}")
        print(f"  F1 Score: {val_f1:.4f}")
        
        self.best_models['logistic_regression'] = best_model
        self.results['logistic_regression'] = {
            'best_params': grid_search.best_params_,
            'cv_f1_mean': float(cv_scores.mean()),
            'cv_f1_std': float(cv_scores.std()),
            'val_accuracy': float(val_accuracy),
            'val_f1': float(val_f1)
        }
        
        return best_model
    
    def optimize_random_forest(self, X_train, y_train, X_val, y_val):
        """Random Forest 하이퍼파라미터 튜닝"""
        print("\n" + "="*60)
        print("Random Forest 최적화")
        print("="*60)
        
        # 파라미터 그리드 (과적합 방지)
        param_grid = {
            'n_estimators': [50, 100, 200],
            'max_depth': [3, 5, 7, 10],  # 깊이 제한
            'min_samples_split': [10, 20, 30],  # 분할 최소 샘플 수 증가
            'min_samples_leaf': [5, 10, 15],  # 리프 최소 샘플 수 증가
            'max_features': ['sqrt', 'log2'],  # 특성 샘플링
            'class_weight': ['balanced']
        }
        
        # Grid Search with Cross Validation
        rf = RandomForestClassifier(random_state=42, n_jobs=-1)
        
        f1_scorer = make_scorer(f1_score)
        
        grid_search = GridSearchCV(
            rf, 
            param_grid, 
            cv=5,
            scoring=f1_scorer,
            n_jobs=-1,
            verbose=1
        )
        
        print("Grid Search 시작...")
        start_time = datetime.now()
        grid_search.fit(X_train, y_train)
        elapsed = (datetime.now() - start_time).total_seconds()
        
        print(f"\nGrid Search 완료 (소요 시간: {elapsed:.2f}초)")
        print(f"최적 파라미터: {grid_search.best_params_}")
        print(f"최적 CV F1 Score: {grid_search.best_score_:.4f}")
        
        # 최적 모델
        best_model = grid_search.best_estimator_
        
        # 교차 검증 점수
        cv_scores = cross_val_score(best_model, X_train, y_train, cv=5, scoring=f1_scorer)
        print(f"CV F1 Scores: {cv_scores}")
        print(f"CV F1 Mean: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
        
        # Validation 성능 평가
        y_val_pred = best_model.predict(X_val)
        val_f1 = f1_score(y_val, y_val_pred)
        val_accuracy = accuracy_score(y_val, y_val_pred)
        
        print(f"\nValidation 성능:")
        print(f"  Accuracy: {val_accuracy:.4f}")
        print(f"  F1 Score: {val_f1:.4f}")
        
        self.best_models['random_forest'] = best_model
        self.results['random_forest'] = {
            'best_params': grid_search.best_params_,
            'cv_f1_mean': float(cv_scores.mean()),
            'cv_f1_std': float(cv_scores.std()),
            'val_accuracy': float(val_accuracy),
            'val_f1': float(val_f1)
        }
        
        return best_model
    
    def evaluate_final_model(self, model, X_test, y_test, model_name):
        """최종 테스트 평가"""
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        roc_auc = roc_auc_score(y_test, y_pred_proba)
        
        print(f"\n{model_name} Test 성능:")
        print(f"  Accuracy:  {accuracy:.4f}")
        print(f"  Precision: {precision:.4f}")
        print(f"  Recall:    {recall:.4f}")
        print(f"  F1 Score:  {f1:.4f}")
        print(f"  ROC-AUC:   {roc_auc:.4f}")
        
        return {
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1),
            'roc_auc': float(roc_auc)
        }
    
    def save_model(self, model_name):
        """모델 저장"""
        if model_name not in self.best_models:
            return
        
        model = self.best_models[model_name]
        model_path = MODEL_DIR / f'{model_name}_optimized.joblib'
        
        joblib.dump(model, model_path)
        print(f"모델 저장: {model_path}")
    
    def save_results(self):
        """결과 저장"""
        results_path = MODEL_DIR / 'optimized_results.json'
        
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"결과 저장: {results_path}")
    
    def run(self):
        """전체 프로세스 실행"""
        print("="*60)
        print("모델 최적화 시작 - 하이퍼파라미터 튜닝")
        print("="*60)
        
        start_time = datetime.now()
        
        try:
            # 1. 데이터 로드
            print("\n[1단계] 데이터 로드")
            X_train, y_train = self.load_data('train')
            X_val, y_val = self.load_data('validation')
            X_test, y_test = self.load_data('test')
            
            if X_train is None or X_val is None or X_test is None:
                print("오류: 데이터 로드 실패")
                return
            
            # 2. 로지스틱 회귀 최적화
            print("\n[2단계] 로지스틱 회귀 최적화")
            lr_model = self.optimize_logistic_regression(X_train, y_train, X_val, y_val)
            lr_test_results = self.evaluate_final_model(lr_model, X_test, y_test, "Logistic Regression")
            self.results['logistic_regression']['test'] = lr_test_results
            self.save_model('logistic_regression')
            
            # 3. Random Forest 최적화
            print("\n[3단계] Random Forest 최적화")
            rf_model = self.optimize_random_forest(X_train, y_train, X_val, y_val)
            rf_test_results = self.evaluate_final_model(rf_model, X_test, y_test, "Random Forest")
            self.results['random_forest']['test'] = rf_test_results
            self.save_model('random_forest')
            
            # 4. 결과 저장
            print("\n[4단계] 결과 저장")
            self.save_results()
            
            # 5. 모델 비교
            print("\n" + "="*60)
            print("최적화 결과 비교")
            print("="*60)
            
            print("\n[베이스라인 vs 최적화]")
            print(f"\n{'모델':<25} {'베이스라인 F1':<15} {'최적화 F1':<15} {'개선':<10}")
            print("-" * 65)
            
            # 베이스라인 결과 로드
            baseline_path = MODEL_DIR / 'baseline_results.json'
            if baseline_path.exists():
                with open(baseline_path, 'r') as f:
                    baseline_results = json.load(f)
                
                lr_baseline_f1 = baseline_results['logistic_regression']['test']['f1_score']
                lr_optimized_f1 = lr_test_results['f1_score']
                lr_improvement = lr_optimized_f1 - lr_baseline_f1
                
                rf_baseline_f1 = baseline_results['random_forest']['test']['f1_score']
                rf_optimized_f1 = rf_test_results['f1_score']
                rf_improvement = rf_optimized_f1 - rf_baseline_f1
                
                print(f"{'Logistic Regression':<25} {lr_baseline_f1:<15.4f} {lr_optimized_f1:<15.4f} {lr_improvement:+.4f}")
                print(f"{'Random Forest':<25} {rf_baseline_f1:<15.4f} {rf_optimized_f1:<15.4f} {rf_improvement:+.4f}")
            
            # 최고 성능 모델
            if lr_test_results['f1_score'] > rf_test_results['f1_score']:
                best_model = 'Logistic Regression'
                best_f1 = lr_test_results['f1_score']
            else:
                best_model = 'Random Forest'
                best_f1 = rf_test_results['f1_score']
            
            print(f"\n최고 성능 모델: {best_model} (F1 Score: {best_f1:.4f})")
            
            end_time = datetime.now()
            elapsed = (end_time - start_time).total_seconds()
            
            print("\n" + "="*60)
            print(f"모델 최적화 완료 (소요 시간: {elapsed:.2f}초)")
            print("="*60)
            
        except Exception as e:
            print(f"\n오류 발생: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    optimizer = ModelOptimizer()
    optimizer.run()
