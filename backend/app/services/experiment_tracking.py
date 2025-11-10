"""
실험 추적 시스템 - MLflow 기반 실험 관리 서비스
"""
import os
import mlflow
from mlflow.tracking import MlflowClient
from mlflow.entities import ViewType
from typing import Optional, Dict, Any, List
from datetime import datetime
import pandas as pd
import json


class ExperimentTracker:
    """MLflow 실험 추적 서비스"""
    
    def __init__(self, tracking_uri: Optional[str] = None):
        """
        실험 추적 서비스 초기화
        
        Args:
            tracking_uri: MLflow Tracking Server URI
        """
        self.tracking_uri = tracking_uri or os.getenv(
            "MLFLOW_TRACKING_URI", 
            "http://192.168.0.147:5001"
        )
        mlflow.set_tracking_uri(self.tracking_uri)
        self.client = MlflowClient(tracking_uri=self.tracking_uri)
        print(f"[DEBUG] ExperimentTracker initialized with tracking_uri={self.tracking_uri}")
        print(f"[DEBUG] MlflowClient._tracking_client.store: {type(self.client._tracking_client.store)}")
    
    def create_experiment(
        self, 
        name: str, 
        tags: Optional[Dict[str, str]] = None,
        artifact_location: Optional[str] = None
    ) -> str:
        """
        새로운 실험 생성
        
        Args:
            name: 실험 이름
            tags: 실험 태그
            artifact_location: 아티팩트 저장 위치
            
        Returns:
            experiment_id: 생성된 실험 ID
        """
        try:
            # 새 실험 생성 (강제 생성)
            print(f"[DEBUG] Creating experiment '{name}' with tracking_uri={self.tracking_uri}")
            experiment_id = mlflow.create_experiment(
                name=name,
                tags=tags or {},
                artifact_location=artifact_location
            )
            print(f"[DEBUG] Created experiment_id={experiment_id}")
            return experiment_id
        except Exception as e:
            # 이미 존재하는 실험인 경우, client를 통해 검색
            error_msg = str(e).lower()
            print(f"[DEBUG] Exception during create_experiment: {error_msg[:200]}")
            if "already exists" in error_msg or "unique constraint" in error_msg:
                # MlflowClient를 통해 실험 검색 (캐시 우회)
                experiments = self.client.search_experiments(filter_string=f"name   = '{name}'")
                if experiments and len(experiments) > 0:
                    found_id = experiments[0].experiment_id
                    print(f"[DEBUG] Found existing experiment_id={found_id}")
                    return found_id
            raise Exception(f"Failed to create experiment: {str(e)}")
    
    def get_experiment(self, experiment_id: str) -> Dict[str, Any]:
        """
        실험 정보 조회
        
        Args:
            experiment_id: 실험 ID
            
        Returns:
            experiment_info: 실험 정보 딕셔너리
        """
        try:
            experiment = self.client.get_experiment(experiment_id)
            return {
                "experiment_id": experiment.experiment_id,
                "name": experiment.name,
                "artifact_location": experiment.artifact_location,
                "lifecycle_stage": experiment.lifecycle_stage,
                "tags": experiment.tags,
                "creation_time": experiment.creation_time,
                "last_update_time": experiment.last_update_time
            }
        except Exception as e:
            raise Exception(f"Failed to get experiment: {str(e)}")
    
    def list_experiments(self, view_type: str = "ACTIVE_ONLY") -> List[Dict[str, Any]]:
        """
        모든 실험 목록 조회
        
        Args:
            view_type: 뷰 타입 (ACTIVE_ONLY, DELETED_ONLY, ALL)
            
        Returns:
            experiments: 실험 목록
        """
        try:
            view_type_enum = getattr(ViewType, view_type, ViewType.ACTIVE_ONLY)
            experiments = self.client.search_experiments(view_type=view_type_enum)
            
            return [
                {
                    "experiment_id": exp.experiment_id,
                    "name": exp.name,
                    "artifact_location": exp.artifact_location,
                    "lifecycle_stage": exp.lifecycle_stage,
                    "tags": exp.tags
                }
                for exp in experiments
            ]
        except Exception as e:
            raise Exception(f"Failed to list experiments: {str(e)}")
    
    def start_run(
        self, 
        experiment_id: str,
        run_name: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> str:
        """
        새로운 실험 run 시작
        
        Args:
            experiment_id: 실험 ID
            run_name: Run 이름
            tags: Run 태그
            
        Returns:
            run_id: 생성된 run ID
        """
        try:
            with mlflow.start_run(
                experiment_id=experiment_id,
                run_name=run_name,
                tags=tags or {}
            ) as run:
                return run.info.run_id
        except Exception as e:
            raise Exception(f"Failed to start run: {str(e)}")
    
    def log_params(self, run_id: str, params: Dict[str, Any]) -> None:
        """
        하이퍼파라미터 로깅
        
        Args:
            run_id: Run ID
            params: 로깅할 파라미터 딕셔너리
        """
        try:
            with mlflow.start_run(run_id=run_id):
                for key, value in params.items():
                    # MLflow는 스칼라 값만 지원하므로 복잡한 객체는 JSON 문자열로 변환
                    if isinstance(value, (dict, list)):
                        value = json.dumps(value)
                    mlflow.log_param(key, value)
        except Exception as e:
            raise Exception(f"Failed to log params: {str(e)}")
    
    def log_metrics(
        self, 
        run_id: str, 
        metrics: Dict[str, float],
        step: Optional[int] = None
    ) -> None:
        """
        메트릭 로깅
        
        Args:
            run_id: Run ID
            metrics: 로깅할 메트릭 딕셔너리
            step: 스텝 번호 (에포크, 이터레이션 등)
        """
        try:
            with mlflow.start_run(run_id=run_id):
                for key, value in metrics.items():
                    mlflow.log_metric(key, value, step=step)
        except Exception as e:
            raise Exception(f"Failed to log metrics: {str(e)}")
    
    def log_artifact(
        self, 
        run_id: str, 
        local_path: str,
        artifact_path: Optional[str] = None
    ) -> None:
        """
        아티팩트(파일) 로깅
        
        Args:
            run_id: Run ID
            local_path: 로컬 파일 경로
            artifact_path: MLflow 내 저장 경로
        """
        try:
            with mlflow.start_run(run_id=run_id):
                mlflow.log_artifact(local_path, artifact_path)
        except Exception as e:
            raise Exception(f"Failed to log artifact: {str(e)}")
    
    def log_model(
        self,
        run_id: str,
        model: Any,
        artifact_path: str = "model",
        registered_model_name: Optional[str] = None,
        signature: Optional[Any] = None,
        input_example: Optional[Any] = None,
        skip_on_permission_error: bool = True
    ) -> None:
        """
        모델 로깅 및 레지스트리 등록
        
        Args:
            run_id: Run ID
            model: 저장할 모델 객체
            artifact_path: 모델 저장 경로
            registered_model_name: 모델 레지스트리 이름
            signature: 모델 시그니처
            input_example: 입력 예제
            skip_on_permission_error: 권한 오류 시 건너뛰기 (True면 경고만 출력)
        """
        try:
            # 현재 active run 확인
            active_run = mlflow.active_run()
            
            # active run이 있고 run_id와 같으면 그대로 사용
            if active_run and active_run.info.run_id == run_id:
                # scikit-learn 모델 로깅
                mlflow.sklearn.log_model(
                    sk_model=model,
                    artifact_path=artifact_path,
                    registered_model_name=registered_model_name,
                    signature=signature,
                    input_example=input_example
                )
            else:
                # active run이 다르거나 없으면 새로 시작
                with mlflow.start_run(run_id=run_id):
                    # scikit-learn 모델 로깅
                    mlflow.sklearn.log_model(
                        sk_model=model,
                        artifact_path=artifact_path,
                        registered_model_name=registered_model_name,
                        signature=signature,
                        input_example=input_example
                    )
        except PermissionError as e:
            if skip_on_permission_error:
                import warnings
                warnings.warn(f"MLflow 모델 저장 권한 오류 (건너뜀): {str(e)}")
            else:
                raise Exception(f"Failed to log model: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to log model: {str(e)}")
    
    def get_run(self, run_id: str) -> Dict[str, Any]:
        """
        Run 정보 조회
        
        Args:
            run_id: Run ID
            
        Returns:
            run_info: Run 정보 딕셔너리
        """
        try:
            run = self.client.get_run(run_id)
            return {
                "run_id": run.info.run_id,
                "experiment_id": run.info.experiment_id,
                "status": run.info.status,
                "start_time": run.info.start_time,
                "end_time": run.info.end_time,
                "artifact_uri": run.info.artifact_uri,
                "lifecycle_stage": run.info.lifecycle_stage,
                "params": run.data.params,
                "metrics": run.data.metrics,
                "tags": run.data.tags
            }
        except Exception as e:
            raise Exception(f"Failed to get run: {str(e)}")
    
    def search_runs(
        self,
        experiment_ids: List[str],
        filter_string: str = "",
        order_by: List[str] = None,
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """
        조건에 맞는 runs 검색
        
        Args:
            experiment_ids: 실험 ID 리스트
            filter_string: 필터 조건 (예: "metrics.f1_score > 0.8")
            order_by: 정렬 조건 (예: ["metrics.f1_score DESC"])
            max_results: 최대 결과 수
            
        Returns:
            runs: Run 정보 리스트
        """
        try:
            runs = self.client.search_runs(
                experiment_ids=experiment_ids,
                filter_string=filter_string,
                order_by=order_by or ["start_time DESC"],
                max_results=max_results
            )
            
            return [
                {
                    "run_id": run.info.run_id,
                    "experiment_id": run.info.experiment_id,
                    "status": run.info.status,
                    "start_time": run.info.start_time,
                    "end_time": run.info.end_time,
                    "params": run.data.params,
                    "metrics": run.data.metrics,
                    "tags": run.data.tags
                }
                for run in runs
            ]
        except Exception as e:
            raise Exception(f"Failed to search runs: {str(e)}")
    
    def compare_runs(
        self,
        run_ids: List[str],
        metric_keys: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        여러 runs 비교
        
        Args:
            run_ids: 비교할 run ID 리스트
            metric_keys: 비교할 메트릭 키 리스트 (None이면 모든 메트릭)
            
        Returns:
            comparison_df: 비교 결과 DataFrame
        """
        try:
            runs_data = []
            for run_id in run_ids:
                run = self.client.get_run(run_id)
                
                run_dict = {
                    "run_id": run.info.run_id,
                    "run_name": run.data.tags.get("mlflow.runName", ""),
                    "start_time": datetime.fromtimestamp(run.info.start_time / 1000),
                    "status": run.info.status
                }
                
                # 파라미터 추가
                for key, value in run.data.params.items():
                    run_dict[f"param_{key}"] = value
                
                # 메트릭 추가
                for key, value in run.data.metrics.items():
                    if metric_keys is None or key in metric_keys:
                        run_dict[f"metric_{key}"] = value
                
                runs_data.append(run_dict)
            
            return pd.DataFrame(runs_data)
        except Exception as e:
            raise Exception(f"Failed to compare runs: {str(e)}")
    
    def get_best_run(
        self,
        experiment_id: str,
        metric_key: str,
        ascending: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        최고 성능 run 찾기
        
        Args:
            experiment_id: 실험 ID
            metric_key: 비교할 메트릭 키
            ascending: 오름차순 정렬 여부 (True: 낮을수록 좋음)
            
        Returns:
            best_run: 최고 성능 run 정보
        """
        try:
            order = "ASC" if ascending else "DESC"
            runs = self.client.search_runs(
                experiment_ids=[experiment_id],
                order_by=[f"metrics.{metric_key} {order}"],
                max_results=1
            )
            
            if not runs:
                return None
            
            run = runs[0]
            return {
                "run_id": run.info.run_id,
                "experiment_id": run.info.experiment_id,
                "status": run.info.status,
                "start_time": run.info.start_time,
                "end_time": run.info.end_time,
                "params": run.data.params,
                "metrics": run.data.metrics,
                "tags": run.data.tags
            }
        except Exception as e:
            raise Exception(f"Failed to get best run: {str(e)}")
    
    def register_model(
        self,
        run_id: str,
        model_name: str,
        model_path: str = "model"
    ) -> str:
        """
        모델을 레지스트리에 등록
        
        Args:
            run_id: Run ID
            model_name: 모델 레지스트리 이름
            model_path: 모델 아티팩트 경로
            
        Returns:
            model_version: 등록된 모델 버전
        """
        try:
            run = self.client.get_run(run_id)
            model_uri = f"runs:/{run_id}/{model_path}"
            
            model_version = mlflow.register_model(
                model_uri=model_uri,
                name=model_name
            )
            
            return model_version.version
        except Exception as e:
            raise Exception(f"Failed to register model: {str(e)}")
    
    def transition_model_stage(
        self,
        model_name: str,
        version: str,
        stage: str,
        archive_existing_versions: bool = False
    ) -> None:
        """
        모델 스테이지 변경 (Staging, Production 등)
        
        Args:
            model_name: 모델 이름
            version: 모델 버전
            stage: 변경할 스테이지 (Staging, Production, Archived)
            archive_existing_versions: 기존 버전 아카이브 여부
        """
        try:
            self.client.transition_model_version_stage(
                name=model_name,
                version=version,
                stage=stage,
                archive_existing_versions=archive_existing_versions
            )
        except Exception as e:
            raise Exception(f"Failed to transition model stage: {str(e)}")
    
    def get_model_version(
        self,
        model_name: str,
        version: Optional[str] = None,
        stage: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        모델 버전 정보 조회
        
        Args:
            model_name: 모델 이름
            version: 모델 버전 (version 또는 stage 중 하나 필수)
            stage: 모델 스테이지 (Production, Staging 등)
            
        Returns:
            model_info: 모델 버전 정보
        """
        try:
            if version:
                model_version = self.client.get_model_version(
                    name=model_name,
                    version=version
                )
            elif stage:
                model_versions = self.client.get_latest_versions(
                    name=model_name,
                    stages=[stage]
                )
                if not model_versions:
                    raise Exception(f"No model version found for stage: {stage}")
                model_version = model_versions[0]
            else:
                raise ValueError("Either version or stage must be provided")
            
            return {
                "name": model_version.name,
                "version": model_version.version,
                "creation_timestamp": model_version.creation_timestamp,
                "last_updated_timestamp": model_version.last_updated_timestamp,
                "current_stage": model_version.current_stage,
                "description": model_version.description,
                "source": model_version.source,
                "run_id": model_version.run_id,
                "status": model_version.status,
                "tags": model_version.tags
            }
        except Exception as e:
            raise Exception(f"Failed to get model version: {str(e)}")
    
    def delete_experiment(self, experiment_id: str) -> None:
        """
        실험 삭제
        
        Args:
            experiment_id: 실험 ID
        """
        try:
            self.client.delete_experiment(experiment_id)
        except Exception as e:
            raise Exception(f"Failed to delete experiment: {str(e)}")
    
    def delete_run(self, run_id: str) -> None:
        """
        Run 삭제
        
        Args:
            run_id: Run ID
        """
        try:
            self.client.delete_run(run_id)
        except Exception as e:
            raise Exception(f"Failed to delete run: {str(e)}")
