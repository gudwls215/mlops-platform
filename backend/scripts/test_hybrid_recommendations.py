"""
하이브리드 추천 시스템 테스트 및 평가
"""

import requests
import json
import time
import pandas as pd
from typing import Dict, List
import numpy as np

BASE_URL = "http://localhost:9000"


def test_api_availability():
    """API 가용성 테스트"""
    print("=== 1. API 가용성 테스트 ===")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✓ 백엔드 서버 정상 작동")
            return True
        else:
            print(f"✗ 백엔드 서버 오류: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ 백엔드 서버 접근 불가: {e}")
        return False


def test_hybrid_stats():
    """하이브리드 추천 시스템 통계 확인"""
    print("\n=== 2. 하이브리드 추천 시스템 통계 ===")
    
    try:
        response = requests.get(f"{BASE_URL}/api/hybrid-recommendations/stats")
        response.raise_for_status()
        stats = response.json()
        
        print("\n[Content-based]")
        print(f"  임베딩이 있는 이력서: {stats['content_based']['resumes_with_embeddings']}건")
        print(f"  임베딩이 있는 채용공고: {stats['content_based']['jobs_with_embeddings']}건")
        
        print("\n[Collaborative Filtering]")
        print(f"  사용 가능: {stats['collaborative_filtering']['available']}")
        print(f"  총 상호작용: {stats['collaborative_filtering']['total_interactions']}건")
        print(f"  고유 사용자: {stats['collaborative_filtering']['unique_users']}명")
        print(f"  고유 아이템: {stats['collaborative_filtering']['unique_items']}개")
        print(f"  매트릭스 크기: {stats['collaborative_filtering']['matrix_users']} x {stats['collaborative_filtering']['matrix_items']}")
        print(f"  Sparsity: {stats['collaborative_filtering']['sparsity']:.4f}")
        
        print("\n[Hybrid]")
        print(f"  사용 가능한 전략: {', '.join(stats['hybrid']['strategies_available'])}")
        print(f"  기본 전략: {stats['hybrid']['default_strategy']}")
        print(f"  기본 Content 가중치: {stats['hybrid']['default_content_weight']}")
        print(f"  기본 CF 가중치: {stats['hybrid']['default_cf_weight']}")
        
        return stats
    except Exception as e:
        print(f"✗ 통계 조회 실패: {e}")
        return None


def test_recommendation_strategy(resume_id: int, strategy: str, top_n: int = 10):
    """특정 전략의 추천 결과 테스트"""
    print(f"\n=== 3. {strategy.upper()} 전략 테스트 (Resume ID: {resume_id}) ===")
    
    try:
        start_time = time.time()
        
        response = requests.get(
            f"{BASE_URL}/api/hybrid-recommendations/jobs/{resume_id}",
            params={"top_n": top_n, "strategy": strategy}
        )
        response.raise_for_status()
        
        elapsed = time.time() - start_time
        result = response.json()
        
        print(f"\n응답 시간: {elapsed:.3f}초")
        print(f"추천 개수: {result['total_count']}건")
        print(f"전략: {result['strategy']}")
        print(f"Content 가중치: {result['content_weight']}")
        print(f"CF 가중치: {result['cf_weight']}")
        
        print("\n[추천 결과 Top 5]")
        for i, rec in enumerate(result['recommendations'][:5], 1):
            print(f"{i}. [{rec['job_id']}] {rec['company']} - {rec['title']}")
            print(f"   Hybrid Score: {rec['hybrid_score']:.4f}")
            if rec.get('similarity'):
                print(f"   Similarity: {rec['similarity']:.4f}")
            if rec.get('cf_score'):
                print(f"   CF Score: {rec['cf_score']:.4f}")
            print(f"   Strategy: {rec['strategy']}")
        
        return result
    except Exception as e:
        print(f"✗ 추천 생성 실패: {e}")
        return None


def compare_strategies(resume_id: int, top_n: int = 10):
    """여러 전략 비교"""
    print(f"\n=== 4. 전략 비교 (Resume ID: {resume_id}, Top {top_n}) ===")
    
    strategies = ["weighted", "cascade", "mixed"]
    results = {}
    
    for strategy in strategies:
        try:
            response = requests.get(
                f"{BASE_URL}/api/hybrid-recommendations/jobs/{resume_id}",
                params={"top_n": top_n, "strategy": strategy}
            )
            response.raise_for_status()
            results[strategy] = response.json()
        except Exception as e:
            print(f"✗ {strategy} 전략 실패: {e}")
            results[strategy] = None
    
    # 결과 비교
    print("\n[전략별 Top 3 채용공고 비교]")
    print(f"{'Rank':<6}{'Weighted':<15}{'Cascade':<15}{'Mixed':<15}")
    print("-" * 51)
    
    for i in range(min(3, top_n)):
        row = [f"{i+1}"]
        
        for strategy in strategies:
            if results[strategy] and len(results[strategy]['recommendations']) > i:
                job_id = results[strategy]['recommendations'][i]['job_id']
                row.append(f"Job {job_id:<8}")
            else:
                row.append("-" * 13)
        
        print(f"{row[0]:<6}{row[1]:<15}{row[2]:<15}{row[3]:<15}")
    
    # 중복도 분석
    print("\n[전략 간 추천 중복도]")
    
    def get_job_ids(result):
        if result:
            return set(rec['job_id'] for rec in result['recommendations'])
        return set()
    
    weighted_jobs = get_job_ids(results['weighted'])
    cascade_jobs = get_job_ids(results['cascade'])
    mixed_jobs = get_job_ids(results['mixed'])
    
    if weighted_jobs and cascade_jobs:
        overlap_wc = len(weighted_jobs & cascade_jobs)
        print(f"  Weighted ∩ Cascade: {overlap_wc}/{top_n} ({overlap_wc/top_n*100:.1f}%)")
    
    if weighted_jobs and mixed_jobs:
        overlap_wm = len(weighted_jobs & mixed_jobs)
        print(f"  Weighted ∩ Mixed: {overlap_wm}/{top_n} ({overlap_wm/top_n*100:.1f}%)")
    
    if cascade_jobs and mixed_jobs:
        overlap_cm = len(cascade_jobs & mixed_jobs)
        print(f"  Cascade ∩ Mixed: {overlap_cm}/{top_n} ({overlap_cm/top_n*100:.1f}%)")
    
    return results


def test_weight_sensitivity(resume_id: int):
    """가중치 변화에 따른 추천 결과 분석"""
    print(f"\n=== 5. 가중치 민감도 분석 (Resume ID: {resume_id}) ===")
    
    weight_configs = [
        (1.0, 0.0, "Content만"),
        (0.7, 0.3, "Content 우세"),
        (0.5, 0.5, "균등"),
        (0.3, 0.7, "CF 우세"),
        (0.0, 1.0, "CF만")
    ]
    
    results = []
    
    for content_weight, cf_weight, label in weight_configs:
        try:
            response = requests.get(
                f"{BASE_URL}/api/hybrid-recommendations/jobs/{resume_id}",
                params={
                    "top_n": 5,
                    "strategy": "weighted",
                    "content_weight": content_weight,
                    "cf_weight": cf_weight
                }
            )
            response.raise_for_status()
            result = response.json()
            
            top_jobs = [rec['job_id'] for rec in result['recommendations'][:3]]
            results.append({
                "label": label,
                "content_weight": content_weight,
                "cf_weight": cf_weight,
                "top_jobs": top_jobs
            })
        except Exception as e:
            print(f"✗ {label} 테스트 실패: {e}")
    
    # 결과 출력
    print("\n[가중치별 Top 3 채용공고]")
    print(f"{'가중치 설정':<20}{'Content':<10}{'CF':<10}{'Top 3 Job IDs'}")
    print("-" * 60)
    
    for r in results:
        jobs_str = ", ".join(str(jid) for jid in r['top_jobs'])
        print(f"{r['label']:<20}{r['content_weight']:<10.1f}{r['cf_weight']:<10.1f}{jobs_str}")


def performance_test(num_requests: int = 20):
    """성능 테스트"""
    print(f"\n=== 6. 성능 테스트 ({num_requests}회 요청) ===")
    
    resume_ids = [1, 2091, 2092, 2093]  # 테스트할 이력서 ID
    strategies = ["weighted", "cascade", "mixed"]
    
    latencies = []
    
    for i in range(num_requests):
        resume_id = resume_ids[i % len(resume_ids)]
        strategy = strategies[i % len(strategies)]
        
        try:
            start = time.time()
            response = requests.get(
                f"{BASE_URL}/api/hybrid-recommendations/jobs/{resume_id}",
                params={"top_n": 10, "strategy": strategy},
                timeout=10
            )
            elapsed = time.time() - start
            
            if response.status_code == 200:
                latencies.append(elapsed)
        except Exception as e:
            print(f"✗ 요청 {i+1} 실패: {e}")
    
    if latencies:
        print(f"\n총 요청: {num_requests}회")
        print(f"성공: {len(latencies)}회")
        print(f"실패: {num_requests - len(latencies)}회")
        print(f"\n[응답 시간 통계]")
        print(f"  평균: {np.mean(latencies):.3f}초")
        print(f"  중앙값: {np.median(latencies):.3f}초")
        print(f"  최소: {np.min(latencies):.3f}초")
        print(f"  최대: {np.max(latencies):.3f}초")
        print(f"  P95: {np.percentile(latencies, 95):.3f}초")
        print(f"  P99: {np.percentile(latencies, 99):.3f}초")
        
        # 목표 달성 여부
        p95 = np.percentile(latencies, 95)
        if p95 < 2.0:
            print(f"\n✓ 성능 목표 달성 (P95 < 2초): {p95:.3f}초")
        else:
            print(f"\n✗ 성능 목표 미달성 (P95 >= 2초): {p95:.3f}초")


def main():
    """전체 테스트 실행"""
    print("=" * 70)
    print("하이브리드 추천 시스템 종합 테스트")
    print("=" * 70)
    
    # 1. API 가용성 테스트
    if not test_api_availability():
        print("\n✗ 백엔드 서버에 접근할 수 없습니다. 테스트를 중단합니다.")
        return
    
    # 2. 통계 확인
    stats = test_hybrid_stats()
    if not stats:
        print("\n✗ 통계 조회 실패. 테스트를 중단합니다.")
        return
    
    # 3. 전략별 테스트
    test_recommendation_strategy(1, "weighted", top_n=10)
    test_recommendation_strategy(2091, "cascade", top_n=10)
    test_recommendation_strategy(2093, "mixed", top_n=10)
    
    # 4. 전략 비교
    compare_strategies(1, top_n=10)
    
    # 5. 가중치 민감도
    test_weight_sensitivity(2091)
    
    # 6. 성능 테스트
    performance_test(num_requests=20)
    
    print("\n" + "=" * 70)
    print("테스트 완료")
    print("=" * 70)


if __name__ == "__main__":
    main()
