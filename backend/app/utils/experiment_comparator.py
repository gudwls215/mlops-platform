"""
실험 비교 유틸리티 - 여러 실험 결과 비교 및 시각화
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

from app.services.experiment_tracking import ExperimentTracker


class ExperimentComparator:
    """실험 비교 및 분석 도구"""
    
    def __init__(self, tracker: Optional[ExperimentTracker] = None):
        """
        초기화
        
        Args:
            tracker: ExperimentTracker 인스턴스
        """
        self.tracker = tracker or ExperimentTracker()
        
    def compare_experiments(
        self,
        experiment_ids: List[str],
        metric_keys: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        여러 실험 비교
        
        Args:
            experiment_ids: 비교할 실험 ID 리스트
            metric_keys: 비교할 메트릭 키 리스트
            
        Returns:
            comparison_df: 비교 결과 DataFrame
        """
        all_runs = []
        
        for exp_id in experiment_ids:
            runs = self.tracker.search_runs(
                experiment_ids=[exp_id],
                max_results=1000
            )
            all_runs.extend(runs)
        
        if not all_runs:
            return pd.DataFrame()
        
        # DataFrame 생성
        data = []
        for run in all_runs:
            run_dict = {
                "run_id": run["run_id"],
                "experiment_id": run["experiment_id"],
                "status": run["status"],
                "start_time": run["start_time"]
            }
            
            # 파라미터 추가
            for key, value in run.get("params", {}).items():
                run_dict[f"param_{key}"] = value
            
            # 메트릭 추가
            for key, value in run.get("metrics", {}).items():
                if metric_keys is None or key in metric_keys:
                    run_dict[f"metric_{key}"] = value
            
            # 태그 추가
            for key, value in run.get("tags", {}).items():
                run_dict[f"tag_{key}"] = value
            
            data.append(run_dict)
        
        return pd.DataFrame(data)
    
    def get_best_models(
        self,
        experiment_id: str,
        metric_key: str,
        top_k: int = 5,
        ascending: bool = False
    ) -> List[Dict[str, Any]]:
        """
        상위 K개 모델 찾기
        
        Args:
            experiment_id: 실험 ID
            metric_key: 정렬 메트릭
            top_k: 상위 개수
            ascending: 오름차순 정렬 여부
            
        Returns:
            top_models: 상위 모델 리스트
        """
        order = "ASC" if ascending else "DESC"
        runs = self.tracker.search_runs(
            experiment_ids=[experiment_id],
            order_by=[f"metrics.{metric_key} {order}"],
            max_results=top_k
        )
        
        return runs
    
    def analyze_hyperparameters(
        self,
        experiment_id: str,
        metric_key: str,
        param_keys: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        하이퍼파라미터 영향 분석
        
        Args:
            experiment_id: 실험 ID
            metric_key: 분석할 메트릭
            param_keys: 분석할 파라미터 키 리스트
            
        Returns:
            analysis: 분석 결과
        """
        runs = self.tracker.search_runs(
            experiment_ids=[experiment_id],
            max_results=1000
        )
        
        if not runs:
            return {}
        
        # 데이터 수집
        param_metric_data = {}
        
        for run in runs:
            metric_value = run.get("metrics", {}).get(metric_key)
            if metric_value is None:
                continue
            
            params = run.get("params", {})
            
            for param_key, param_value in params.items():
                if param_keys is None or param_key in param_keys:
                    if param_key not in param_metric_data:
                        param_metric_data[param_key] = []
                    
                    param_metric_data[param_key].append({
                        "value": param_value,
                        "metric": metric_value
                    })
        
        # 파라미터별 통계 계산
        analysis = {}
        
        for param_key, data_list in param_metric_data.items():
            # 파라미터 값별 평균 메트릭 계산
            value_metrics = {}
            for item in data_list:
                value = item["value"]
                metric = item["metric"]
                
                if value not in value_metrics:
                    value_metrics[value] = []
                value_metrics[value].append(metric)
            
            # 평균 계산
            value_avg = {
                value: np.mean(metrics)
                for value, metrics in value_metrics.items()
            }
            
            # 최적값 찾기
            best_value = max(value_avg.items(), key=lambda x: x[1])
            
            analysis[param_key] = {
                "value_metrics": value_avg,
                "best_value": best_value[0],
                "best_metric": best_value[1],
                "correlation": self._calculate_correlation(data_list)
            }
        
        return analysis
    
    def _calculate_correlation(self, data_list: List[Dict[str, Any]]) -> Optional[float]:
        """
        파라미터와 메트릭 간 상관관계 계산
        
        Args:
            data_list: 파라미터-메트릭 데이터 리스트
            
        Returns:
            correlation: 상관계수 (숫자형 파라미터만)
        """
        try:
            # 숫자형 파라미터만 처리
            values = [float(item["value"]) for item in data_list]
            metrics = [item["metric"] for item in data_list]
            
            if len(values) < 2:
                return None
            
            correlation = np.corrcoef(values, metrics)[0, 1]
            return correlation
        except (ValueError, TypeError):
            # 숫자로 변환 불가능한 파라미터
            return None
    
    def plot_metric_comparison(
        self,
        experiment_ids: List[str],
        metric_keys: List[str],
        save_path: Optional[Path] = None
    ) -> None:
        """
        메트릭 비교 플롯 생성
        
        Args:
            experiment_ids: 실험 ID 리스트
            metric_keys: 비교할 메트릭 키 리스트
            save_path: 저장 경로
        """
        df = self.compare_experiments(experiment_ids, metric_keys)
        
        if df.empty:
            print("비교할 데이터가 없습니다.")
            return
        
        # 메트릭 컬럼만 선택
        metric_cols = [col for col in df.columns if col.startswith("metric_")]
        
        if not metric_cols:
            print("메트릭 데이터가 없습니다.")
            return
        
        # 플롯 생성
        n_metrics = len(metric_cols)
        fig, axes = plt.subplots(1, n_metrics, figsize=(6 * n_metrics, 5))
        
        if n_metrics == 1:
            axes = [axes]
        
        for idx, metric_col in enumerate(metric_cols):
            metric_name = metric_col.replace("metric_", "")
            ax = axes[idx]
            
            # Box plot
            df.boxplot(column=metric_col, by="experiment_id", ax=ax)
            ax.set_title(f"{metric_name}")
            ax.set_xlabel("Experiment ID")
            ax.set_ylabel(metric_name)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"플롯 저장 완료: {save_path}")
        else:
            plt.show()
    
    def plot_hyperparameter_impact(
        self,
        experiment_id: str,
        metric_key: str,
        param_keys: List[str],
        save_path: Optional[Path] = None
    ) -> None:
        """
        하이퍼파라미터 영향 시각화
        
        Args:
            experiment_id: 실험 ID
            metric_key: 분석할 메트릭
            param_keys: 시각화할 파라미터 키 리스트
            save_path: 저장 경로
        """
        analysis = self.analyze_hyperparameters(
            experiment_id,
            metric_key,
            param_keys
        )
        
        if not analysis:
            print("분석할 데이터가 없습니다.")
            return
        
        # 플롯 생성
        n_params = len(analysis)
        fig, axes = plt.subplots(1, n_params, figsize=(6 * n_params, 5))
        
        if n_params == 1:
            axes = [axes]
        
        for idx, (param_key, data) in enumerate(analysis.items()):
            ax = axes[idx]
            
            value_metrics = data["value_metrics"]
            
            # Bar plot
            values = list(value_metrics.keys())
            metrics = list(value_metrics.values())
            
            ax.bar(range(len(values)), metrics)
            ax.set_xticks(range(len(values)))
            ax.set_xticklabels(values, rotation=45)
            ax.set_title(f"{param_key}")
            ax.set_xlabel("Parameter Value")
            ax.set_ylabel(metric_key)
            
            # 최적값 표시
            best_idx = values.index(data["best_value"])
            ax.bar(best_idx, metrics[best_idx], color='red', alpha=0.7)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"플롯 저장 완료: {save_path}")
        else:
            plt.show()
    
    def generate_report(
        self,
        experiment_id: str,
        output_path: Path
    ) -> None:
        """
        실험 리포트 생성
        
        Args:
            experiment_id: 실험 ID
            output_path: 리포트 저장 경로
        """
        # 실험 정보 조회
        experiment = self.tracker.get_experiment(experiment_id)
        
        # 모든 runs 조회
        runs = self.tracker.search_runs(
            experiment_ids=[experiment_id],
            max_results=1000
        )
        
        # 리포트 생성
        report = []
        report.append("# 실험 리포트\n")
        report.append(f"## 실험 정보\n")
        report.append(f"- **실험 ID**: {experiment['experiment_id']}\n")
        report.append(f"- **실험 이름**: {experiment['name']}\n")
        report.append(f"- **생성 시간**: {experiment['creation_time']}\n")
        report.append(f"- **총 Run 수**: {len(runs)}\n\n")
        
        # Run 통계
        if runs:
            report.append(f"## Run 통계\n")
            
            # 메트릭 통계
            all_metrics = {}
            for run in runs:
                for key, value in run.get("metrics", {}).items():
                    if key not in all_metrics:
                        all_metrics[key] = []
                    all_metrics[key].append(value)
            
            if all_metrics:
                report.append("### 메트릭 통계\n")
                report.append("| 메트릭 | Min | Max | Mean | Std |\n")
                report.append("|--------|-----|-----|------|-----|\n")
                
                for key, values in all_metrics.items():
                    report.append(
                        f"| {key} | {min(values):.4f} | {max(values):.4f} | "
                        f"{np.mean(values):.4f} | {np.std(values):.4f} |\n"
                    )
                
                report.append("\n")
            
            # 최고 성능 모델
            report.append("### 최고 성능 모델 (상위 5개)\n")
            
            # 주요 메트릭별 최고 성능 모델
            for metric_key in ["test_f1_score", "test_accuracy", "test_roc_auc"]:
                if metric_key in all_metrics:
                    top_models = self.get_best_models(
                        experiment_id,
                        metric_key,
                        top_k=5
                    )
                    
                    if top_models:
                        report.append(f"\n#### {metric_key}\n")
                        report.append("| Rank | Run ID | 값 |\n")
                        report.append("|------|--------|----|\n")
                        
                        for rank, run in enumerate(top_models, 1):
                            run_id = run["run_id"][:8]
                            value = run.get("metrics", {}).get(metric_key, 0)
                            report.append(f"| {rank} | {run_id} | {value:.4f} |\n")
                        
                        report.append("\n")
        
        # 파일 저장
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(report)
        
        print(f"리포트 생성 완료: {output_path}")


if __name__ == "__main__":
    # 예제 사용법
    comparator = ExperimentComparator()
    
    # 실험 비교
    df = comparator.compare_experiments(
        experiment_ids=["0", "1"],
        metric_keys=["test_f1_score", "test_accuracy"]
    )
    print(df)
