"""
성능 최적화 유틸리티

모델 추론 및 데이터 처리 최적화
"""

import numpy as np
from typing import List, Tuple, Optional
import hashlib
import json
from functools import lru_cache


class PerformanceOptimizer:
    """
    성능 최적화 유틸리티 클래스
    
    - NumPy 배열 최적화
    - 메모리 효율적인 데이터 처리
    - 입력 해싱 및 캐싱
    """
    
    @staticmethod
    def optimize_array(features: List[List[float]], dtype=np.float32) -> np.ndarray:
        """
        특성 배열 최적화
        
        Args:
            features: 특성 벡터 리스트
            dtype: 데이터 타입 (기본값: float32)
            
        Returns:
            최적화된 NumPy 배열
            
        Note:
            - float64 대신 float32 사용하여 메모리 50% 절약
            - C-contiguous 배열로 변환하여 연산 속도 향상
        """
        # float32로 변환하여 메모리 절약 (float64 대비 50%)
        arr = np.array(features, dtype=dtype)
        
        # C-contiguous 배열로 변환 (캐시 효율성 향상)
        if not arr.flags['C_CONTIGUOUS']:
            arr = np.ascontiguousarray(arr)
        
        return arr
    
    @staticmethod
    def compute_hash(features: List[float]) -> str:
        """
        특성 벡터의 해시 계산 (캐싱용)
        
        Args:
            features: 특성 벡터
            
        Returns:
            SHA256 해시 문자열
        """
        # 특성 벡터를 문자열로 변환하여 해싱
        feature_str = json.dumps(features, sort_keys=True)
        return hashlib.sha256(feature_str.encode()).hexdigest()
    
    @staticmethod
    def batch_split(
        batch: List[List[float]], 
        chunk_size: int = 100
    ) -> List[List[List[float]]]:
        """
        배치를 청크로 분할 (병렬 처리용)
        
        Args:
            batch: 전체 배치
            chunk_size: 청크 크기
            
        Returns:
            분할된 청크 리스트
        """
        chunks = []
        for i in range(0, len(batch), chunk_size):
            chunks.append(batch[i:i + chunk_size])
        return chunks
    
    @staticmethod
    @lru_cache(maxsize=1000)
    def get_feature_stats(feature_dim: int) -> Tuple[float, float]:
        """
        특성 통계 캐싱 (정규화용)
        
        Args:
            feature_dim: 특성 차원
            
        Returns:
            (평균, 표준편차) 튜플
        """
        # 실제로는 학습 데이터 통계를 사용해야 하지만,
        # 여기서는 예시로 고정값 반환
        return (0.5, 0.25)
    
    @staticmethod
    def preprocess_features_vectorized(
        features_array: np.ndarray,
        normalize: bool = False
    ) -> np.ndarray:
        """
        벡터화된 특성 전처리
        
        Args:
            features_array: 특성 배열
            normalize: 정규화 여부
            
        Returns:
            전처리된 배열
        """
        if normalize:
            # 벡터화된 정규화 (루프 없이)
            mean = features_array.mean(axis=1, keepdims=True)
            std = features_array.std(axis=1, keepdims=True)
            std = np.where(std == 0, 1, std)  # 0으로 나누기 방지
            features_array = (features_array - mean) / std
        
        return features_array
    
    @staticmethod
    def optimize_memory_usage():
        """
        메모리 사용량 최적화
        
        - NumPy 메모리 정리
        - 가비지 컬렉션 실행
        """
        import gc
        gc.collect()


# 싱글톤 인스턴스
_optimizer = PerformanceOptimizer()


def get_optimizer() -> PerformanceOptimizer:
    """성능 최적화 유틸리티 반환"""
    return _optimizer
