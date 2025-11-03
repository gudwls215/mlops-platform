"""
모델 서빙 서비스

scikit-learn 모델을 위한 서빙 인프라
- MLflow Model Registry 통합
- 버전 관리 및 자동 리로드
- 배치 및 실시간 예측
- 모델 캐싱 및 성능 최적화
"""

import os
import json
import joblib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from threading import Lock
import numpy as np
from pydantic import BaseModel, Field

# 성능 최적화 유틸리티
from app.utils.performance import get_optimizer
from app.utils.parallel import get_parallel_predictor
from app.services.prediction_cache import get_prediction_cache

# MLflow 관련
try:
    import mlflow
    from mlflow.tracking import MlflowClient
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False
    logging.warning("MLflow를 사용할 수 없습니다. joblib 모델만 지원됩니다.")


logger = logging.getLogger(__name__)


class PredictionInput(BaseModel):
    """예측 입력 스키마"""
    features: List[float] = Field(..., description="특성 벡터")
    feature_names: Optional[List[str]] = Field(None, description="특성 이름 (선택사항)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "features": [0.1, 0.2, 0.3, 0.4],
                "feature_names": ["feature1", "feature2", "feature3", "feature4"]
            }
        }


class BatchPredictionInput(BaseModel):
    """배치 예측 입력 스키마"""
    batch: List[PredictionInput] = Field(..., description="예측 입력 배치")
    
    class Config:
        json_schema_extra = {
            "example": {
                "batch": [
                    {"features": [0.1, 0.2, 0.3, 0.4]},
                    {"features": [0.5, 0.6, 0.7, 0.8]}
                ]
            }
        }


class PredictionOutput(BaseModel):
    """예측 출력 스키마"""
    prediction: Union[int, float, str] = Field(..., description="예측 결과")
    probability: Optional[float] = Field(None, description="확률 (분류 모델인 경우)")
    probabilities: Optional[List[float]] = Field(None, description="클래스별 확률")
    model_version: str = Field(..., description="모델 버전")
    timestamp: str = Field(..., description="예측 시각")
    inference_time_ms: float = Field(..., description="추론 시간 (밀리초)")


class ModelInfo(BaseModel):
    """모델 정보 스키마"""
    name: str
    version: str
    stage: str
    loaded_at: str
    model_type: str
    metadata: Dict[str, Any]


class ModelLoader:
    """
    모델 로더 클래스
    - MLflow Model Registry 또는 로컬 파일에서 모델 로드
    - 버전 관리 및 캐싱
    - 자동 리로드
    """
    
    def __init__(
        self,
        model_name: str = "job_matching_model",
        model_path: Optional[Path] = None,
        use_mlflow: bool = True,
        cache_ttl_minutes: int = 60
    ):
        """
        Args:
            model_name: MLflow에 등록된 모델 이름
            model_path: 로컬 모델 파일 경로 (MLflow 미사용 시)
            use_mlflow: MLflow Model Registry 사용 여부
            cache_ttl_minutes: 캐시 유효 시간 (분)
        """
        self.model_name = model_name
        self.model_path = model_path
        self.use_mlflow = use_mlflow and MLFLOW_AVAILABLE
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        
        # 캐시
        self._model = None
        self._model_version = None
        self._loaded_at = None
        self._metadata = {}
        self._lock = Lock()
        
        # MLflow 클라이언트
        if self.use_mlflow:
            self.mlflow_client = MlflowClient()
        
        logger.info(f"ModelLoader 초기화: model_name={model_name}, use_mlflow={self.use_mlflow}")
    
    def load_model(self, stage: str = "Production", force_reload: bool = False) -> Any:
        """
        모델 로드 (캐싱 지원)
        
        Args:
            stage: MLflow 모델 스테이지 (Production, Staging, None)
            force_reload: 강제 리로드 여부
            
        Returns:
            로드된 모델 객체
        """
        with self._lock:
            # 캐시 유효성 검사
            if not force_reload and self._is_cache_valid():
                logger.debug(f"캐시된 모델 사용: version={self._model_version}")
                return self._model
            
            # 모델 로드
            if self.use_mlflow:
                model, version, metadata = self._load_from_mlflow(stage)
            else:
                model, version, metadata = self._load_from_file()
            
            # 캐시 업데이트
            self._model = model
            self._model_version = version
            self._loaded_at = datetime.now()
            self._metadata = metadata
            
            logger.info(f"모델 로드 완료: version={version}, loaded_at={self._loaded_at}")
            return model
    
    def _is_cache_valid(self) -> bool:
        """캐시 유효성 검사"""
        if self._model is None or self._loaded_at is None:
            return False
        
        elapsed = datetime.now() - self._loaded_at
        return elapsed < self.cache_ttl
    
    def _load_from_mlflow(self, stage: str) -> tuple:
        """MLflow Model Registry에서 모델 로드"""
        try:
            # 최신 버전 조회
            versions = self.mlflow_client.get_latest_versions(self.model_name, stages=[stage])
            
            if not versions:
                raise ValueError(f"'{self.model_name}' 모델의 '{stage}' 스테이지 버전을 찾을 수 없습니다.")
            
            latest_version = versions[0]
            model_uri = f"models:/{self.model_name}/{stage}"
            
            # 모델 로드
            model = mlflow.sklearn.load_model(model_uri)
            
            # 메타데이터 수집
            run = self.mlflow_client.get_run(latest_version.run_id)
            metadata = {
                "version": latest_version.version,
                "stage": stage,
                "run_id": latest_version.run_id,
                "metrics": run.data.metrics,
                "params": run.data.params,
                "tags": run.data.tags
            }
            
            logger.info(f"MLflow에서 모델 로드: {model_uri}, version={latest_version.version}")
            return model, latest_version.version, metadata
            
        except Exception as e:
            logger.error(f"MLflow에서 모델 로드 실패: {e}")
            # Fallback to local file
            if self.model_path:
                logger.warning("로컬 파일에서 모델을 로드합니다.")
                return self._load_from_file()
            raise
    
    def _load_from_file(self) -> tuple:
        """로컬 파일에서 모델 로드"""
        if not self.model_path:
            # 기본 경로 설정
            base_dir = Path(__file__).parent.parent.parent / "models"
            self.model_path = base_dir / "final_model.joblib"
        
        if not self.model_path.exists():
            raise FileNotFoundError(f"모델 파일을 찾을 수 없습니다: {self.model_path}")
        
        # 모델 로드
        model = joblib.load(self.model_path)
        
        # 메타데이터 로드 (있는 경우)
        metadata_path = self.model_path.with_suffix('.json').name.replace('.joblib', '_metadata.json')
        metadata_file = self.model_path.parent / metadata_path
        
        metadata = {}
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        
        version = metadata.get('version', 'local')
        
        logger.info(f"로컬 파일에서 모델 로드: {self.model_path}")
        return model, version, metadata
    
    def get_model_info(self) -> ModelInfo:
        """현재 로드된 모델 정보 반환"""
        if self._model is None:
            raise ValueError("로드된 모델이 없습니다. load_model()을 먼저 호출하세요.")
        
        return ModelInfo(
            name=self.model_name,
            version=str(self._model_version),
            stage=self._metadata.get('stage', 'local'),
            loaded_at=self._loaded_at.isoformat(),
            model_type=type(self._model).__name__,
            metadata=self._metadata
        )
    
    def reload_model(self, stage: str = "Production"):
        """모델 강제 리로드"""
        logger.info(f"모델 리로드 시작: stage={stage}")
        self.load_model(stage=stage, force_reload=True)


class ModelServingService:
    """
    모델 서빙 서비스
    - 실시간 예측
    - 배치 예측
    - 성능 모니터링
    """
    
    def __init__(
        self,
        model_name: str = "job_matching_model",
        model_path: Optional[Path] = None,
        use_mlflow: bool = True
    ):
        """
        Args:
            model_name: 모델 이름
            model_path: 로컬 모델 경로
            use_mlflow: MLflow 사용 여부
        """
        self.model_loader = ModelLoader(
            model_name=model_name,
            model_path=model_path,
            use_mlflow=use_mlflow
        )
        
        # 캐시 초기화
        self.cache = get_prediction_cache()
        
        # 초기 모델 로드
        try:
            logger.info("모델 로드 시도 중...")
            self.model_loader.load_model(stage="Production")
            logger.info("모델 로드 성공")
        except Exception as e:
            logger.warning(f"Production 모델 로드 실패, 로컬 파일 시도: {e}")
            try:
                # MLflow 실패 시 로컬 파일에서 로드
                self.model_loader.use_mlflow = False
                self.model_loader.load_model()
                logger.info("로컬 파일에서 모델 로드 성공")
            except Exception as e2:
                logger.error(f"모델 로드 완전 실패: {e2}")
                # 서버 시작은 계속하되, 에러 로그만 남김
        
        logger.info("ModelServingService 초기화 완료")
    
    async def predict(
        self,
        features: List[float],
        return_probabilities: bool = True
    ) -> PredictionOutput:
        """
        단일 예측 (실시간)
        
        Args:
            features: 특성 벡터
            return_probabilities: 확률 반환 여부
            
        Returns:
            예측 결과
        """
        # 모델 정보
        model_info = self.model_loader.get_model_info()
        
        # 캐시 조회
        cached_result = self.cache.get(features, model_info.version, return_probabilities)
        if cached_result:
            logger.debug("캐시된 예측 결과 반환")
            return PredictionOutput(**cached_result)
        
        start_time = datetime.now()
        
        try:
            # 모델 로드
            model = self.model_loader.load_model()
            
            # 성능 최적화: float32 사용, C-contiguous 배열
            optimizer = get_optimizer()
            features_array = optimizer.optimize_array([features], dtype=np.float32)
            
            # 예측 (최적화된 배열 사용)
            prediction = model.predict(features_array)[0]
            
            # 확률 계산 (분류 모델인 경우)
            probability = None
            probabilities = None
            
            if return_probabilities and hasattr(model, 'predict_proba'):
                proba = model.predict_proba(features_array)[0]
                probabilities = proba.tolist()
                probability = float(proba[int(prediction)])
            
            # 추론 시간 계산
            inference_time = (datetime.now() - start_time).total_seconds() * 1000
            
            result = PredictionOutput(
                prediction=int(prediction) if isinstance(prediction, (np.integer, int)) else float(prediction),
                probability=probability,
                probabilities=probabilities,
                model_version=model_info.version,
                timestamp=datetime.now().isoformat(),
                inference_time_ms=round(inference_time, 2)
            )
            
            # 캐시에 저장
            self.cache.set(features, model_info.version, return_probabilities, result.dict())
            
            return result
            
        except Exception as e:
            logger.error(f"예측 실패: {e}", exc_info=True)
            raise
    
    async def predict_batch(
        self,
        batch_features: List[List[float]],
        return_probabilities: bool = True,
        use_parallel: bool = False,
        chunk_size: int = 100
    ) -> List[PredictionOutput]:
        """
        배치 예측
        
        Args:
            batch_features: 특성 벡터 배치
            return_probabilities: 확률 반환 여부
            use_parallel: 병렬 처리 사용 여부
            chunk_size: 병렬 처리 시 청크 크기
            
        Returns:
            예측 결과 리스트
        """
        start_time = datetime.now()
        
        try:
            # 모델 로드
            model = self.model_loader.load_model()
            model_info = self.model_loader.get_model_info()
            
            # 병렬 처리 활성화 시
            if use_parallel and len(batch_features) > chunk_size:
                logger.info(f"병렬 배치 예측 시작: {len(batch_features)}개 샘플")
                
                parallel_predictor = get_parallel_predictor()
                predictions_data = parallel_predictor.predict_parallel(
                    model=model,
                    batch_features=batch_features,
                    chunk_size=chunk_size,
                    return_probabilities=return_probabilities
                )
                
                # 결과 변환
                results = []
                for pred_data in predictions_data:
                    results.append(PredictionOutput(
                        prediction=pred_data["prediction"],
                        probability=pred_data.get("probability"),
                        probabilities=pred_data.get("probabilities"),
                        model_version=model_info.version,
                        timestamp=datetime.now().isoformat(),
                        inference_time_ms=0.0
                    ))
            else:
                # 순차 처리
                # 성능 최적화: float32 사용, C-contiguous 배열
                optimizer = get_optimizer()
                features_array = optimizer.optimize_array(batch_features, dtype=np.float32)
                
                # 배치 예측 (최적화된 배열 사용)
                predictions = model.predict(features_array)
                
                # 확률 계산
                probabilities_batch = None
                if return_probabilities and hasattr(model, 'predict_proba'):
                    probabilities_batch = model.predict_proba(features_array)
                
                # 결과 생성 (벡터화)
                results = []
                
                for i, prediction in enumerate(predictions):
                    probability = None
                    probabilities = None
                    
                    if probabilities_batch is not None:
                        proba = probabilities_batch[i]
                        probabilities = proba.tolist()
                        probability = float(proba[int(prediction)])
                    
                    results.append(PredictionOutput(
                        prediction=int(prediction) if isinstance(prediction, (np.integer, int)) else float(prediction),
                        probability=probability,
                        probabilities=probabilities,
                        model_version=model_info.version,
                        timestamp=datetime.now().isoformat(),
                        inference_time_ms=0.0  # 개별 시간은 측정하지 않음
                    ))
            
            # 전체 추론 시간 계산
            total_inference_time = (datetime.now() - start_time).total_seconds() * 1000
            avg_time = total_inference_time / len(batch_features)
            
            # 평균 추론 시간 업데이트
            for result in results:
                result.inference_time_ms = round(avg_time, 2)
            
            logger.info(f"배치 예측 완료: {len(batch_features)}건, 평균 {avg_time:.2f}ms")
            return results
            
        except Exception as e:
            logger.error(f"배치 예측 실패: {e}", exc_info=True)
            raise
    
    def get_model_info(self) -> ModelInfo:
        """모델 정보 조회"""
        return self.model_loader.get_model_info()
    
    def reload_model(self, stage: str = "Production"):
        """모델 리로드"""
        self.model_loader.reload_model(stage=stage)
    
    async def health_check(self) -> Dict[str, Any]:
        """헬스 체크"""
        try:
            model_info = self.get_model_info()
            return {
                "status": "healthy",
                "model_name": model_info.name,
                "model_version": model_info.version,
                "model_type": model_info.model_type,
                "loaded_at": model_info.loaded_at
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# 싱글톤 인스턴스
_model_service_instance: Optional[ModelServingService] = None


def get_model_service() -> ModelServingService:
    """모델 서빙 서비스 싱글톤 인스턴스 반환"""
    global _model_service_instance
    
    if _model_service_instance is None:
        # 환경 변수에서 설정 로드
        model_name = os.getenv("MODEL_NAME", "job_matching_model")
        use_mlflow = os.getenv("USE_MLFLOW", "true").lower() == "true"
        model_path_str = os.getenv("MODEL_PATH")
        
        model_path = Path(model_path_str) if model_path_str else None
        
        _model_service_instance = ModelServingService(
            model_name=model_name,
            model_path=model_path,
            use_mlflow=use_mlflow
        )
    
    return _model_service_instance
