"""
병렬 예측 처리

멀티프로세싱/멀티스레딩을 활용한 배치 예측 병렬화
"""

import logging
from typing import List, Callable, Any
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import multiprocessing as mp
from functools import partial

logger = logging.getLogger(__name__)


class ParallelPredictor:
    """
    병렬 예측 처리 클래스
    
    - 멀티스레딩: I/O 바운드 작업용
    - 멀티프로세싱: CPU 바운드 작업용
    - 작업 분할 및 결과 병합
    """
    
    def __init__(
        self,
        max_workers: int = None,
        use_processes: bool = False
    ):
        """
        Args:
            max_workers: 최대 워커 수 (None이면 CPU 코어 수)
            use_processes: 프로세스 사용 여부 (False면 스레드 사용)
        """
        self.use_processes = use_processes
        
        if max_workers is None:
            self.max_workers = mp.cpu_count()
        else:
            self.max_workers = max_workers
        
        logger.info(
            f"ParallelPredictor 초기화: "
            f"max_workers={self.max_workers}, "
            f"mode={'processes' if use_processes else 'threads'}"
        )
    
    def predict_parallel(
        self,
        model: Any,
        batch_features: List[List[float]],
        chunk_size: int = 100,
        return_probabilities: bool = True
    ) -> List[dict]:
        """
        병렬 배치 예측
        
        Args:
            model: 예측 모델
            batch_features: 특성 벡터 배치
            chunk_size: 청크 크기
            return_probabilities: 확률 반환 여부
            
        Returns:
            예측 결과 리스트
        """
        # 배치를 청크로 분할
        chunks = self._split_into_chunks(batch_features, chunk_size)
        
        logger.info(
            f"병렬 예측 시작: {len(batch_features)}개 샘플, "
            f"{len(chunks)}개 청크, 청크 크기 {chunk_size}"
        )
        
        # 병렬 처리
        if self.use_processes:
            results = self._predict_with_processes(model, chunks, return_probabilities)
        else:
            results = self._predict_with_threads(model, chunks, return_probabilities)
        
        # 결과 병합 (청크 순서대로)
        merged_results = []
        for chunk_results in results:
            merged_results.extend(chunk_results)
        
        logger.info(f"병렬 예측 완료: {len(merged_results)}개 결과")
        return merged_results
    
    def _split_into_chunks(
        self,
        batch: List[List[float]],
        chunk_size: int
    ) -> List[List[List[float]]]:
        """배치를 청크로 분할"""
        chunks = []
        for i in range(0, len(batch), chunk_size):
            chunks.append(batch[i:i + chunk_size])
        return chunks
    
    def _predict_with_threads(
        self,
        model: Any,
        chunks: List[List[List[float]]],
        return_probabilities: bool
    ) -> List[List[dict]]:
        """스레드 기반 병렬 예측"""
        import numpy as np
        
        def predict_chunk(chunk):
            """청크 예측 함수"""
            features_array = np.array(chunk, dtype=np.float32)
            predictions = model.predict(features_array)
            
            results = []
            probabilities_batch = None
            
            if return_probabilities and hasattr(model, 'predict_proba'):
                probabilities_batch = model.predict_proba(features_array)
            
            for i, prediction in enumerate(predictions):
                result = {
                    "prediction": int(prediction) if isinstance(prediction, (np.integer, int)) else float(prediction),
                    "probability": None,
                    "probabilities": None
                }
                
                if probabilities_batch is not None:
                    proba = probabilities_batch[i]
                    result["probabilities"] = proba.tolist()
                    result["probability"] = float(proba[int(prediction)])
                
                results.append(result)
            
            return results
        
        # 스레드풀로 병렬 실행
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(predict_chunk, chunk) for chunk in chunks]
            
            results = []
            for future in as_completed(futures):
                try:
                    chunk_results = future.result()
                    results.append(chunk_results)
                except Exception as e:
                    logger.error(f"청크 예측 실패: {e}", exc_info=True)
                    raise
        
        return results
    
    def _predict_with_processes(
        self,
        model: Any,
        chunks: List[List[List[float]]],
        return_probabilities: bool
    ) -> List[List[dict]]:
        """프로세스 기반 병렬 예측"""
        import numpy as np
        
        def predict_chunk_worker(chunk, model_bytes, return_prob):
            """워커 프로세스 함수"""
            import pickle
            
            # 모델 역직렬화
            model = pickle.loads(model_bytes)
            
            features_array = np.array(chunk, dtype=np.float32)
            predictions = model.predict(features_array)
            
            results = []
            probabilities_batch = None
            
            if return_prob and hasattr(model, 'predict_proba'):
                probabilities_batch = model.predict_proba(features_array)
            
            for i, prediction in enumerate(predictions):
                result = {
                    "prediction": int(prediction) if isinstance(prediction, (np.integer, int)) else float(prediction),
                    "probability": None,
                    "probabilities": None
                }
                
                if probabilities_batch is not None:
                    proba = probabilities_batch[i]
                    result["probabilities"] = proba.tolist()
                    result["probability"] = float(proba[int(prediction)])
                
                results.append(result)
            
            return results
        
        # 모델 직렬화 (프로세스 간 전달용)
        import pickle
        model_bytes = pickle.dumps(model)
        
        # 프로세스풀로 병렬 실행
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            worker_func = partial(
                predict_chunk_worker,
                model_bytes=model_bytes,
                return_prob=return_probabilities
            )
            
            futures = [executor.submit(worker_func, chunk) for chunk in chunks]
            
            results = []
            for future in as_completed(futures):
                try:
                    chunk_results = future.result()
                    results.append(chunk_results)
                except Exception as e:
                    logger.error(f"청크 예측 실패: {e}", exc_info=True)
                    raise
        
        return results


# 싱글톤 인스턴스
_parallel_predictor_instance = None


def get_parallel_predictor() -> ParallelPredictor:
    """병렬 예측 처리기 싱글톤 인스턴스 반환"""
    global _parallel_predictor_instance
    
    if _parallel_predictor_instance is None:
        import os
        
        # 환경 변수에서 설정 로드
        max_workers = int(os.getenv("PARALLEL_MAX_WORKERS", "0")) or None
        use_processes = os.getenv("PARALLEL_USE_PROCESSES", "false").lower() == "true"
        
        _parallel_predictor_instance = ParallelPredictor(
            max_workers=max_workers,
            use_processes=use_processes
        )
    
    return _parallel_predictor_instance
