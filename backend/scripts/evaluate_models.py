"""
모델 평가 및 최종 선택 스크립트
- 베이스라인 vs 최적화 모델 상세 비교
- 혼동 행렬 분석
- 특성 중요도 분석 (Random Forest)
- ROC 곡선 시각화
- 최종 모델 선택 및 평가 리포트 생성
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
from sklearn.metrics import (
    confusion_matrix, classification_report, roc_curve, roc_auc_score
)
import matplotlib
matplotlib.use('Agg')  # GUI 없이 사용
import matplotlib.pyplot as plt
import seaborn as sns
from dotenv import load_dotenv
import joblib
import json
from datetime import datetime

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

# 경로 설정
MODEL_DIR = Path(__file__).parent.parent / 'models'
REPORT_DIR = Path(__file__).parent.parent / 'reports'
REPORT_DIR.mkdir(exist_ok=True)


class ModelEvaluator:
    """모델 평가 클래스"""
    
    def __init__(self):
        self.engine = create_engine(DATABASE_URL)
        self.models = {}
        self.evaluation_results = {}
        
    def load_data(self, split='test'):
        """테스트 데이터 로드"""
        query = f"""
        SELECT 
            id,
            embedding_array,
            is_passed,
            company,
            position
        FROM {DB_SCHEMA}.cover_letter_samples
        WHERE split = :split AND is_passed IS NOT NULL AND embedding_array IS NOT NULL
        ORDER BY id
        """
        
        with self.engine.connect() as conn:
            df = pd.read_sql(text(query), conn, params={'split': split})
        
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
        
        df = df.iloc[valid_indices].reset_index(drop=True)
        X = np.array(embeddings)
        y = df['is_passed'].values.astype(int)
        
        print(f"{split.upper()} 데이터: {len(X)}건 (합격 {y.sum()}건, 불합격 {len(y)-y.sum()}건)")
        
        return X, y, df
    
    def load_models(self):
        """저장된 모델들 로드"""
        print("\n모델 로드:")
        
        # 베이스라인 모델
        lr_baseline_path = MODEL_DIR / 'logistic_regression_baseline.joblib'
        rf_baseline_path = MODEL_DIR / 'random_forest_baseline.joblib'
        
        # 최적화 모델
        lr_optimized_path = MODEL_DIR / 'logistic_regression_optimized.joblib'
        rf_optimized_path = MODEL_DIR / 'random_forest_optimized.joblib'
        
        if lr_baseline_path.exists():
            self.models['lr_baseline'] = joblib.load(lr_baseline_path)
            print(f"  ✓ 로지스틱 회귀 (베이스라인)")
        
        if rf_baseline_path.exists():
            self.models['rf_baseline'] = joblib.load(rf_baseline_path)
            print(f"  ✓ Random Forest (베이스라인)")
        
        if lr_optimized_path.exists():
            self.models['lr_optimized'] = joblib.load(lr_optimized_path)
            print(f"  ✓ 로지스틱 회귀 (최적화)")
        
        if rf_optimized_path.exists():
            self.models['rf_optimized'] = joblib.load(rf_optimized_path)
            print(f"  ✓ Random Forest (최적화)")
        
        if not self.models:
            raise FileNotFoundError("로드할 모델이 없습니다.")
    
    def plot_confusion_matrix(self, y_true, y_pred, model_name):
        """혼동 행렬 시각화"""
        cm = confusion_matrix(y_true, y_pred)
        
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                    xticklabels=['불합격', '합격'], 
                    yticklabels=['불합격', '합격'])
        plt.title(f'Confusion Matrix - {model_name}')
        plt.ylabel('실제')
        plt.xlabel('예측')
        
        # 저장
        filename = f'confusion_matrix_{model_name.lower().replace(" ", "_")}.png'
        filepath = REPORT_DIR / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  혼동 행렬 저장: {filepath}")
        
        return cm
    
    def plot_roc_curve(self, models_data):
        """ROC 곡선 비교"""
        plt.figure(figsize=(10, 8))
        
        for model_name, data in models_data.items():
            y_true = data['y_true']
            y_pred_proba = data['y_pred_proba']
            
            fpr, tpr, _ = roc_curve(y_true, y_pred_proba)
            auc = roc_auc_score(y_true, y_pred_proba)
            
            plt.plot(fpr, tpr, label=f'{model_name} (AUC = {auc:.3f})')
        
        plt.plot([0, 1], [0, 1], 'k--', label='Random Guess')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('ROC Curves Comparison')
        plt.legend(loc="lower right")
        plt.grid(alpha=0.3)
        
        # 저장
        filepath = REPORT_DIR / 'roc_curves_comparison.png'
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  ROC 곡선 저장: {filepath}")
    
    def analyze_feature_importance(self, model, model_name, top_n=20):
        """특성 중요도 분석 (Random Forest)"""
        if not hasattr(model, 'feature_importances_'):
            print(f"  {model_name}: 특성 중요도 분석 불가 (미지원 모델)")
            return None
        
        importances = model.feature_importances_
        indices = np.argsort(importances)[::-1][:top_n]
        
        plt.figure(figsize=(10, 8))
        plt.title(f'Feature Importance - {model_name} (Top {top_n})')
        plt.bar(range(top_n), importances[indices])
        plt.xlabel('Feature Index')
        plt.ylabel('Importance')
        plt.xticks(range(top_n), [f'F{i}' for i in indices], rotation=45)
        
        # 저장
        filename = f'feature_importance_{model_name.lower().replace(" ", "_")}.png'
        filepath = REPORT_DIR / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  특성 중요도 저장: {filepath}")
        
        return {
            'top_indices': indices.tolist(),
            'top_importances': importances[indices].tolist()
        }
    
    def evaluate_model(self, model, model_name, X, y):
        """모델 상세 평가"""
        print(f"\n{'='*60}")
        print(f"{model_name} 평가")
        print(f"{'='*60}")
        
        # 예측
        y_pred = model.predict(X)
        y_pred_proba = model.predict_proba(X)[:, 1]
        
        # 혼동 행렬
        cm = self.plot_confusion_matrix(y, y_pred, model_name)
        
        # 분류 리포트
        print("\n분류 리포트:")
        report = classification_report(y, y_pred, target_names=['불합격', '합격'], output_dict=True)
        print(classification_report(y, y_pred, target_names=['불합격', '합격']))
        
        # ROC-AUC
        roc_auc = roc_auc_score(y, y_pred_proba)
        print(f"\nROC-AUC: {roc_auc:.4f}")
        
        # 특성 중요도 (Random Forest만)
        feature_importance = None
        if 'forest' in model_name.lower():
            feature_importance = self.analyze_feature_importance(model, model_name)
        
        # 결과 저장
        self.evaluation_results[model_name] = {
            'confusion_matrix': cm.tolist(),
            'classification_report': report,
            'roc_auc': float(roc_auc),
            'feature_importance': feature_importance
        }
        
        return {
            'y_true': y,
            'y_pred': y_pred,
            'y_pred_proba': y_pred_proba
        }
    
    def generate_summary_report(self):
        """종합 평가 리포트 생성"""
        print("\n" + "="*60)
        print("종합 평가 리포트")
        print("="*60)
        
        # 성능 비교 표
        print("\n[모델 성능 비교]")
        print(f"{'모델':<30} {'Accuracy':<12} {'F1 Score':<12} {'ROC-AUC':<12}")
        print("-" * 66)
        
        best_model = None
        best_f1 = 0
        
        for model_name, results in self.evaluation_results.items():
            report = results['classification_report']
            accuracy = report['accuracy']
            f1 = report['weighted avg']['f1-score']
            roc_auc = results['roc_auc']
            
            print(f"{model_name:<30} {accuracy:<12.4f} {f1:<12.4f} {roc_auc:<12.4f}")
            
            if f1 > best_f1:
                best_f1 = f1
                best_model = model_name
        
        print(f"\n최고 성능 모델: {best_model} (F1 Score: {best_f1:.4f})")
        
        # 결과 JSON 저장
        report_path = REPORT_DIR / 'evaluation_report.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump({
                'evaluation_date': datetime.now().isoformat(),
                'best_model': best_model,
                'best_f1_score': float(best_f1),
                'models': self.evaluation_results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n평가 리포트 저장: {report_path}")
        
        return best_model
    
    def select_final_model(self, best_model_name):
        """최종 모델 선택 및 복사"""
        print("\n" + "="*60)
        print("최종 모델 선택")
        print("="*60)
        
        # 최적화 모델 우선, 없으면 베이스라인
        if 'optimized' in best_model_name.lower():
            source_suffix = 'optimized'
        else:
            source_suffix = 'baseline'
        
        if 'logistic' in best_model_name.lower():
            source_name = f'logistic_regression_{source_suffix}'
        else:
            source_name = f'random_forest_{source_suffix}'
        
        source_path = MODEL_DIR / f'{source_name}.joblib'
        final_path = MODEL_DIR / 'final_model.joblib'
        
        # 모델 복사
        import shutil
        shutil.copy(source_path, final_path)
        
        print(f"최종 모델: {best_model_name}")
        print(f"원본: {source_path}")
        print(f"최종: {final_path}")
        
        # 메타데이터 저장
        metadata = {
            'model_name': best_model_name,
            'source_file': source_name,
            'selection_date': datetime.now().isoformat(),
            'performance': self.evaluation_results[best_model_name]
        }
        
        metadata_path = MODEL_DIR / 'final_model_metadata.json'
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"메타데이터: {metadata_path}")
    
    def run(self):
        """전체 프로세스 실행"""
        print("="*60)
        print("모델 평가 및 최종 선택")
        print("="*60)
        
        start_time = datetime.now()
        
        try:
            # 1. 데이터 로드
            print("\n[1단계] 테스트 데이터 로드")
            X_test, y_test, df_test = self.load_data('test')
            
            # 2. 모델 로드
            print("\n[2단계] 모델 로드")
            self.load_models()
            
            # 3. 모델별 평가
            print("\n[3단계] 모델 평가")
            models_roc_data = {}
            
            for model_key, model in self.models.items():
                # 모델 이름 매핑
                name_map = {
                    'lr_baseline': 'Logistic Regression (Baseline)',
                    'lr_optimized': 'Logistic Regression (Optimized)',
                    'rf_baseline': 'Random Forest (Baseline)',
                    'rf_optimized': 'Random Forest (Optimized)'
                }
                model_name = name_map.get(model_key, model_key)
                
                eval_data = self.evaluate_model(model, model_name, X_test, y_test)
                models_roc_data[model_name] = eval_data
            
            # 4. ROC 곡선 비교
            print("\n[4단계] ROC 곡선 생성")
            self.plot_roc_curve(models_roc_data)
            
            # 5. 종합 리포트
            print("\n[5단계] 종합 평가 리포트 생성")
            best_model = self.generate_summary_report()
            
            # 6. 최종 모델 선택
            print("\n[6단계] 최종 모델 선택")
            self.select_final_model(best_model)
            
            end_time = datetime.now()
            elapsed = (end_time - start_time).total_seconds()
            
            print("\n" + "="*60)
            print(f"모델 평가 완료 (소요 시간: {elapsed:.2f}초)")
            print(f"리포트 저장 위치: {REPORT_DIR}")
            print("="*60)
            
        except Exception as e:
            print(f"\n오류 발생: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    evaluator = ModelEvaluator()
    evaluator.run()
