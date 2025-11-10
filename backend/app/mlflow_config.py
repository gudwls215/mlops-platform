"""
MLflow 설정 및 유틸리티 함수
"""
import os
import mlflow
from mlflow.tracking import MlflowClient
from typing import Optional, Dict, Any

# MLflow 설정
MLFLOW_TRACKING_URI = os.getenv(
    "MLFLOW_TRACKING_URI", 
    "http://192.168.0.147:5001"
)
MLFLOW_EXPERIMENT_NAME = os.getenv(
    "MLFLOW_EXPERIMENT_NAME", 
    "mlops-platform"
)

# MLflow 클라이언트 초기화
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
client = MlflowClient()


def get_or_create_experiment(experiment_name: str = MLFLOW_EXPERIMENT_NAME) -> str:
    """
    실험을 가져오거나 새로 생성합니다.
    
    Args:
        experiment_name: 실험 이름
        
    Returns:
        experiment_id: 실험 ID
    """
    experiment = mlflow.get_experiment_by_name(experiment_name)
    
    if experiment is None:
        experiment_id = mlflow.create_experiment(
            experiment_name,
            tags={"project": "mlops-platform", "version": "1.0"}
        )
        print(f"Created new experiment: {experiment_name} (ID: {experiment_id})")
    else:
        experiment_id = experiment.experiment_id
        print(f"Using existing experiment: {experiment_name} (ID: {experiment_id})")
    
    return experiment_id


def log_model_metrics(
    metrics: Dict[str, float],
    params: Optional[Dict[str, Any]] = None,
    tags: Optional[Dict[str, str]] = None,
    model_name: Optional[str] = None
) -> str:
    """
    모델 메트릭과 파라미터를 MLflow에 로깅합니다.
    
    Args:
        metrics: 로깅할 메트릭 딕셔너리
        params: 로깅할 파라미터 딕셔너리
        tags: 로깅할 태그 딕셔너리
        model_name: 모델 이름
        
    Returns:
        run_id: MLflow run ID
    """
    experiment_id = get_or_create_experiment()
    
    with mlflow.start_run(experiment_id=experiment_id) as run:
        # 메트릭 로깅
        for key, value in metrics.items():
            mlflow.log_metric(key, value)
        
        # 파라미터 로깅
        if params:
            for key, value in params.items():
                mlflow.log_param(key, value)
        
        # 태그 로깅
        if tags:
            for key, value in tags.items():
                mlflow.set_tag(key, value)
        
        # 모델 이름 태그
        if model_name:
            mlflow.set_tag("model_name", model_name)
        
        print(f"✓ Logged to MLflow run: {run.info.run_id}")
        return run.info.run_id


def log_sklearn_model(
    model: Any,
    model_name: str,
    metrics: Dict[str, float],
    params: Optional[Dict[str, Any]] = None,
    tags: Optional[Dict[str, str]] = None,
    artifact_path: str = "model"
) -> str:
    """
    scikit-learn 모델을 MLflow에 로깅합니다.
    
    Args:
        model: 학습된 scikit-learn 모델
        model_name: 모델 이름
        metrics: 로깅할 메트릭 딕셔너리
        params: 로깅할 파라미터 딕셔너리
        tags: 로깅할 태그 딕셔너리
        artifact_path: 모델 저장 경로
        
    Returns:
        run_id: MLflow run ID
    """
    experiment_id = get_or_create_experiment()
    
    with mlflow.start_run(experiment_id=experiment_id) as run:
        # 메트릭 로깅
        for key, value in metrics.items():
            mlflow.log_metric(key, value)
        
        # 파라미터 로깅
        if params:
            mlflow.log_params(params)
        
        # 태그 로깅
        default_tags = {"model_name": model_name, "framework": "scikit-learn"}
        if tags:
            default_tags.update(tags)
        mlflow.set_tags(default_tags)
        
        # 모델 로깅
        mlflow.sklearn.log_model(
            sk_model=model,
            artifact_path=artifact_path,
            registered_model_name=model_name
        )
        
        print(f"✓ Logged sklearn model '{model_name}' to MLflow run: {run.info.run_id}")
        return run.info.run_id


def load_model_from_registry(model_name: str, version: Optional[str] = None) -> Any:
    """
    MLflow Model Registry에서 모델을 로드합니다.
    
    Args:
        model_name: 모델 이름
        version: 모델 버전 (기본값: latest)
        
    Returns:
        model: 로드된 모델
    """
    if version is None:
        model_uri = f"models:/{model_name}/latest"
    else:
        model_uri = f"models:/{model_name}/{version}"
    
    model = mlflow.sklearn.load_model(model_uri)
    print(f"✓ Loaded model from registry: {model_uri}")
    return model


def get_best_run(experiment_name: str = MLFLOW_EXPERIMENT_NAME, metric: str = "f1_score") -> Optional[str]:
    """
    실험에서 최고 성능의 run을 찾습니다.
    
    Args:
        experiment_name: 실험 이름
        metric: 비교할 메트릭 이름
        
    Returns:
        run_id: 최고 성능 run의 ID
    """
    experiment = mlflow.get_experiment_by_name(experiment_name)
    if experiment is None:
        print(f"Experiment '{experiment_name}' not found")
        return None
    
    runs = mlflow.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=[f"metrics.{metric} DESC"],
        max_results=1
    )
    
    if runs.empty:
        print(f"No runs found in experiment '{experiment_name}'")
        return None
    
    best_run_id = runs.iloc[0]["run_id"]
    best_metric_value = runs.iloc[0][f"metrics.{metric}"]
    print(f"✓ Best run: {best_run_id} ({metric}={best_metric_value:.4f})")
    return best_run_id


if __name__ == "__main__":
    # 테스트
    print("=== MLflow Configuration ===")
    print(f"Tracking URI: {MLFLOW_TRACKING_URI}")
    print(f"Experiment Name: {MLFLOW_EXPERIMENT_NAME}")
    print("")
    
    # 실험 생성 테스트
    experiment_id = get_or_create_experiment()
    print(f"✓ Experiment ID: {experiment_id}")
