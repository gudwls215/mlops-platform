"""
Redis 기반 예측 결과 캐싱 시스템

- 입력 해싱 기반 캐시 키 생성
- TTL 관리
- 캐시 무효화 전략
"""

import json
import logging
from typing import Optional, Dict, Any
from datetime import timedelta

try:
    import redis
    from redis import Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis를 사용할 수 없습니다. pip install redis 로 설치하세요.")

from app.utils.performance import get_optimizer


logger = logging.getLogger(__name__)


class PredictionCache:
    """
    예측 결과 캐싱 시스템
    
    - Redis 기반 분산 캐싱
    - 입력 해싱으로 캐시 키 생성
    - TTL 자동 관리
    - 캐시 무효화 전략
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        ttl_seconds: int = 3600,
        enabled: bool = True
    ):
        """
        Args:
            host: Redis 호스트
            port: Redis 포트
            db: Redis 데이터베이스 번호
            ttl_seconds: 캐시 TTL (초)
            enabled: 캐싱 활성화 여부
        """
        self.enabled = enabled and REDIS_AVAILABLE
        self.ttl_seconds = ttl_seconds
        self.optimizer = get_optimizer()
        
        if self.enabled:
            try:
                self.redis_client = Redis(
                    host=host,
                    port=port,
                    db=db,
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_timeout=2
                )
                # 연결 테스트
                self.redis_client.ping()
                logger.info(f"Redis 캐시 초기화 완료: {host}:{port}/{db}, TTL={ttl_seconds}s")
            except Exception as e:
                logger.warning(f"Redis 연결 실패, 캐싱 비활성화: {e}")
                self.enabled = False
        else:
            self.redis_client = None
            logger.info("캐싱이 비활성화되었습니다.")
    
    def _generate_cache_key(self, features: list, model_version: str, return_probabilities: bool) -> str:
        """
        캐시 키 생성
        
        Args:
            features: 특성 벡터
            model_version: 모델 버전
            return_probabilities: 확률 반환 여부
            
        Returns:
            캐시 키
        """
        # 입력 해시 계산
        features_hash = self.optimizer.compute_hash(features)
        
        # 캐시 키 생성
        prob_suffix = "_prob" if return_probabilities else ""
        cache_key = f"pred:{model_version}:{features_hash}{prob_suffix}"
        
        return cache_key
    
    def get(
        self,
        features: list,
        model_version: str,
        return_probabilities: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        캐시에서 예측 결과 조회
        
        Args:
            features: 특성 벡터
            model_version: 모델 버전
            return_probabilities: 확률 반환 여부
            
        Returns:
            캐시된 예측 결과 (없으면 None)
        """
        if not self.enabled:
            return None
        
        try:
            cache_key = self._generate_cache_key(features, model_version, return_probabilities)
            cached_value = self.redis_client.get(cache_key)
            
            if cached_value:
                logger.debug(f"캐시 히트: {cache_key[:50]}...")
                return json.loads(cached_value)
            else:
                logger.debug(f"캐시 미스: {cache_key[:50]}...")
                return None
                
        except Exception as e:
            logger.error(f"캐시 조회 실패: {e}")
            return None
    
    def set(
        self,
        features: list,
        model_version: str,
        return_probabilities: bool,
        result: Dict[str, Any]
    ):
        """
        예측 결과를 캐시에 저장
        
        Args:
            features: 특성 벡터
            model_version: 모델 버전
            return_probabilities: 확률 반환 여부
            result: 예측 결과
        """
        if not self.enabled:
            return
        
        try:
            cache_key = self._generate_cache_key(features, model_version, return_probabilities)
            result_json = json.dumps(result)
            
            # TTL과 함께 저장
            self.redis_client.setex(
                name=cache_key,
                time=timedelta(seconds=self.ttl_seconds),
                value=result_json
            )
            
            logger.debug(f"캐시 저장: {cache_key[:50]}... (TTL={self.ttl_seconds}s)")
            
        except Exception as e:
            logger.error(f"캐시 저장 실패: {e}")
    
    def invalidate(self, pattern: str = "pred:*"):
        """
        캐시 무효화
        
        Args:
            pattern: 삭제할 키 패턴 (예: "pred:v1:*")
        """
        if not self.enabled:
            return
        
        try:
            # 패턴에 매칭되는 모든 키 조회
            keys = self.redis_client.keys(pattern)
            
            if keys:
                # 키 삭제
                deleted_count = self.redis_client.delete(*keys)
                logger.info(f"캐시 무효화 완료: {deleted_count}개 키 삭제 (pattern={pattern})")
            else:
                logger.info(f"무효화할 캐시 없음 (pattern={pattern})")
                
        except Exception as e:
            logger.error(f"캐시 무효화 실패: {e}")
    
    def invalidate_by_model_version(self, model_version: str):
        """
        특정 모델 버전의 캐시 무효화
        
        Args:
            model_version: 모델 버전
        """
        pattern = f"pred:{model_version}:*"
        self.invalidate(pattern)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        캐시 통계 조회
        
        Returns:
            캐시 통계 정보
        """
        if not self.enabled:
            return {
                "enabled": False,
                "message": "캐싱이 비활성화되었습니다."
            }
        
        try:
            info = self.redis_client.info("stats")
            
            # 예측 캐시 키 개수 조회
            pred_keys_count = len(self.redis_client.keys("pred:*"))
            
            return {
                "enabled": True,
                "host": self.redis_client.connection_pool.connection_kwargs.get("host"),
                "port": self.redis_client.connection_pool.connection_kwargs.get("port"),
                "db": self.redis_client.connection_pool.connection_kwargs.get("db"),
                "ttl_seconds": self.ttl_seconds,
                "prediction_cache_keys": pred_keys_count,
                "total_keys": self.redis_client.dbsize(),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(info)
            }
            
        except Exception as e:
            logger.error(f"캐시 통계 조회 실패: {e}")
            return {
                "enabled": True,
                "error": str(e)
            }
    
    def _calculate_hit_rate(self, info: Dict[str, Any]) -> float:
        """
        캐시 히트율 계산
        
        Args:
            info: Redis INFO 응답
            
        Returns:
            히트율 (0.0 ~ 1.0)
        """
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        
        if total == 0:
            return 0.0
        
        return hits / total
    
    def clear_all(self):
        """
        모든 캐시 삭제 (주의: 전체 DB 삭제)
        """
        if not self.enabled:
            return
        
        try:
            self.redis_client.flushdb()
            logger.warning("모든 캐시가 삭제되었습니다.")
        except Exception as e:
            logger.error(f"캐시 전체 삭제 실패: {e}")


# 싱글톤 인스턴스
_cache_instance: Optional[PredictionCache] = None


def get_prediction_cache() -> PredictionCache:
    """예측 캐시 싱글톤 인스턴스 반환"""
    global _cache_instance
    
    if _cache_instance is None:
        import os
        
        # 환경 변수에서 설정 로드
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_db = int(os.getenv("REDIS_DB", "0"))
        cache_ttl = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
        cache_enabled = os.getenv("CACHE_ENABLED", "false").lower() == "true"
        
        _cache_instance = PredictionCache(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            ttl_seconds=cache_ttl,
            enabled=cache_enabled
        )
    
    return _cache_instance
