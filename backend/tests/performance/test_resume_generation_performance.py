"""
이력서 생성 API 성능 테스트 스크립트

텍스트 입력으로 이력서를 생성하는 API의 성능을 측정합니다.

사용법:
    python test_resume_generation_performance.py [--api-url URL] [--iterations N]
"""
import asyncio
import aiohttp
import time
import statistics
import argparse
import os
import sys
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import random
import string


@dataclass
class PerformanceResult:
    """성능 측정 결과"""
    iteration: int
    duration_ms: float
    status_code: int
    success: bool
    resume_id: Optional[int] = None
    error_message: str = ""


@dataclass
class PerformanceReport:
    """성능 테스트 리포트"""
    test_name: str
    total_iterations: int
    successful_iterations: int
    failed_iterations: int
    total_duration_ms: float
    avg_duration_ms: float
    min_duration_ms: float
    max_duration_ms: float
    p50_duration_ms: float
    p95_duration_ms: float
    p99_duration_ms: float
    std_dev_ms: float
    throughput_per_sec: float
    results: List[PerformanceResult] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_name": self.test_name,
            "total_iterations": self.total_iterations,
            "successful_iterations": self.successful_iterations,
            "failed_iterations": self.failed_iterations,
            "total_duration_ms": round(self.total_duration_ms, 2),
            "avg_duration_ms": round(self.avg_duration_ms, 2),
            "min_duration_ms": round(self.min_duration_ms, 2),
            "max_duration_ms": round(self.max_duration_ms, 2),
            "p50_duration_ms": round(self.p50_duration_ms, 2),
            "p95_duration_ms": round(self.p95_duration_ms, 2),
            "p99_duration_ms": round(self.p99_duration_ms, 2),
            "std_dev_ms": round(self.std_dev_ms, 2),
            "throughput_per_sec": round(self.throughput_per_sec, 4),
            "success_rate": round(self.successful_iterations / self.total_iterations * 100, 2)
        }


def calculate_percentile(data: List[float], percentile: float) -> float:
    """퍼센타일 계산"""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    index = (len(sorted_data) - 1) * percentile / 100
    lower = int(index)
    upper = lower + 1
    if upper >= len(sorted_data):
        return sorted_data[-1]
    weight = index - lower
    return sorted_data[lower] * (1 - weight) + sorted_data[upper] * weight


# 샘플 이력서 데이터 템플릿
SAMPLE_RESUME_TEMPLATES = [
    {
        "title": "백엔드 개발자 이력서",
        "content": """안녕하세요. 저는 5년차 백엔드 개발자입니다.

경력사항:
- 2020.03 ~ 현재: ABC 테크 - 시니어 백엔드 개발자
  - Python/FastAPI 기반 마이크로서비스 개발
  - PostgreSQL, Redis 활용한 데이터 처리 시스템 구축
  - 일 100만 트랜잭션 처리 시스템 운영

- 2018.01 ~ 2020.02: XYZ 소프트 - 주니어 개발자
  - Django 웹 애플리케이션 개발
  - RESTful API 설계 및 구현

학력:
- 2018: OO대학교 컴퓨터공학과 졸업

기술 스택:
Python, FastAPI, Django, PostgreSQL, Redis, Docker, Kubernetes, AWS""",
        "skills": ["Python", "FastAPI", "Django", "PostgreSQL", "Redis", "Docker", "Kubernetes", "AWS"]
    },
    {
        "title": "프론트엔드 개발자 이력서",
        "content": """저는 4년차 프론트엔드 개발자입니다.

경력사항:
- 2021.06 ~ 현재: DEF 스타트업 - 프론트엔드 리드
  - React/TypeScript 기반 SPA 개발
  - 디자인 시스템 구축 및 컴포넌트 라이브러리 개발
  - 웹 성능 최적화 (LCP 2초 이하 달성)

- 2019.03 ~ 2021.05: GHI 컴퍼니 - 프론트엔드 개발자
  - Vue.js 기반 관리자 대시보드 개발
  - 반응형 웹 디자인 구현

학력:
- 2019: XX대학교 소프트웨어학과 졸업

기술 스택:
React, TypeScript, Vue.js, Next.js, Tailwind CSS, Webpack, Jest""",
        "skills": ["React", "TypeScript", "Vue.js", "Next.js", "Tailwind CSS", "Webpack", "Jest"]
    },
    {
        "title": "데이터 엔지니어 이력서",
        "content": """데이터 엔지니어링 전문가입니다.

경력사항:
- 2019.09 ~ 현재: JKL 데이터 - 시니어 데이터 엔지니어
  - Apache Spark 기반 대용량 데이터 파이프라인 구축
  - Airflow를 활용한 ETL 워크플로우 자동화
  - 데이터 레이크 아키텍처 설계

- 2017.07 ~ 2019.08: MNO 분석 - 데이터 분석가
  - SQL 기반 비즈니스 데이터 분석
  - Tableau 대시보드 개발

학력:
- 2017: YY대학교 통계학과 졸업
- 2019: ZZ대학원 빅데이터 석사

기술 스택:
Python, Spark, Airflow, Kafka, Hadoop, SQL, Tableau, AWS Glue""",
        "skills": ["Python", "Spark", "Airflow", "Kafka", "Hadoop", "SQL", "Tableau", "AWS"]
    }
]


def generate_random_resume_data(iteration: int) -> Dict[str, Any]:
    """랜덤 이력서 데이터 생성"""
    template = random.choice(SAMPLE_RESUME_TEMPLATES)
    
    # 고유성을 위해 랜덤 문자열 추가
    random_suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    
    return {
        "title": f"{template['title']} - {iteration}_{random_suffix}",
        "content": template["content"],
        "skills": json.dumps(template["skills"])
    }


async def test_resume_creation_api(
    session: aiohttp.ClientSession,
    api_url: str,
    iteration: int,
    user_id: int = 1
) -> PerformanceResult:
    """이력서 생성 API 단일 요청 테스트"""
    
    start_time = time.perf_counter()
    
    try:
        resume_data = generate_random_resume_data(iteration)
        
        # FormData 생성
        data = aiohttp.FormData()
        data.add_field('title', resume_data["title"])
        data.add_field('content', resume_data["content"])
        data.add_field('skills', resume_data["skills"])
        data.add_field('user_id', str(user_id))
        
        async with session.post(f"{api_url}/api/resumes/", data=data) as response:
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000
            
            response_json = await response.json()
            
            if response.status == 200 and response_json.get("status") == "success":
                resume_id = response_json.get("data", {}).get("id")
                return PerformanceResult(
                    iteration=iteration,
                    duration_ms=duration_ms,
                    status_code=response.status,
                    success=True,
                    resume_id=resume_id
                )
            else:
                return PerformanceResult(
                    iteration=iteration,
                    duration_ms=duration_ms,
                    status_code=response.status,
                    success=False,
                    error_message=response_json.get("error", str(response_json))
                )
    
    except Exception as e:
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        return PerformanceResult(
            iteration=iteration,
            duration_ms=duration_ms,
            status_code=0,
            success=False,
            error_message=str(e)
        )


async def test_resume_fetch_api(
    session: aiohttp.ClientSession,
    api_url: str,
    resume_id: int,
    iteration: int
) -> PerformanceResult:
    """이력서 조회 API 테스트"""
    
    start_time = time.perf_counter()
    
    try:
        async with session.get(f"{api_url}/api/resumes/{resume_id}") as response:
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000
            
            response_json = await response.json()
            
            if response.status == 200 and response_json.get("status") == "success":
                return PerformanceResult(
                    iteration=iteration,
                    duration_ms=duration_ms,
                    status_code=response.status,
                    success=True,
                    resume_id=resume_id
                )
            else:
                return PerformanceResult(
                    iteration=iteration,
                    duration_ms=duration_ms,
                    status_code=response.status,
                    success=False,
                    error_message=response_json.get("error", "Unknown error")
                )
    
    except Exception as e:
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        return PerformanceResult(
            iteration=iteration,
            duration_ms=duration_ms,
            status_code=0,
            success=False,
            error_message=str(e)
        )


async def run_resume_creation_test(
    api_url: str,
    iterations: int,
    concurrency: int = 1
) -> PerformanceReport:
    """이력서 생성 테스트 실행"""
    
    test_type = "동시 실행" if concurrency > 1 else "순차 실행"
    
    print(f"\n{'='*60}")
    print(f"이력서 생성 API 성능 테스트 ({test_type})")
    print(f"{'='*60}")
    print(f"API URL: {api_url}")
    print(f"반복 횟수: {iterations}")
    if concurrency > 1:
        print(f"동시 실행 수: {concurrency}")
    print(f"{'='*60}\n")
    
    results: List[PerformanceResult] = []
    
    timeout = aiohttp.ClientTimeout(total=120)
    connector = aiohttp.TCPConnector(limit=concurrency)
    
    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        if concurrency > 1:
            # 동시 실행
            semaphore = asyncio.Semaphore(concurrency)
            
            async def bounded_test(iteration: int):
                async with semaphore:
                    return await test_resume_creation_api(session, api_url, iteration)
            
            tasks = [bounded_test(i) for i in range(1, iterations + 1)]
            
            print(f"총 {len(tasks)}개 요청 시작...")
            results = list(await asyncio.gather(*tasks))
        else:
            # 순차 실행
            for i in range(1, iterations + 1):
                print(f"[{i}/{iterations}] 테스트 실행 중...", end=" ")
                result = await test_resume_creation_api(session, api_url, i)
                results.append(result)
                
                if result.success:
                    print(f"✓ {result.duration_ms:.2f}ms (이력서 ID: {result.resume_id})")
                else:
                    print(f"✗ 실패: {result.error_message}")
    
    return generate_report(f"이력서 생성 API 테스트 ({test_type})", results)


async def run_resume_fetch_test(
    api_url: str,
    iterations: int,
    resume_ids: List[int] = None,
    concurrency: int = 1
) -> PerformanceReport:
    """이력서 조회 테스트 실행"""
    
    test_type = "동시 실행" if concurrency > 1 else "순차 실행"
    
    print(f"\n{'='*60}")
    print(f"이력서 조회 API 성능 테스트 ({test_type})")
    print(f"{'='*60}")
    print(f"API URL: {api_url}")
    print(f"반복 횟수: {iterations}")
    print(f"{'='*60}\n")
    
    # 이력서 목록 조회
    if not resume_ids:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{api_url}/api/resumes/?limit=100") as response:
                data = await response.json()
                if data.get("status") == "success":
                    resume_ids = [r["id"] for r in data.get("data", {}).get("resumes", [])]
                    if not resume_ids:
                        print("❌ 조회할 이력서가 없습니다. 먼저 이력서를 생성해주세요.")
                        return None
    
    print(f"조회할 이력서 수: {len(resume_ids)}")
    
    results: List[PerformanceResult] = []
    
    timeout = aiohttp.ClientTimeout(total=60)
    connector = aiohttp.TCPConnector(limit=concurrency)
    
    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        for i in range(1, iterations + 1):
            resume_id = random.choice(resume_ids)
            print(f"[{i}/{iterations}] 이력서 {resume_id} 조회 중...", end=" ")
            result = await test_resume_fetch_api(session, api_url, resume_id, i)
            results.append(result)
            
            if result.success:
                print(f"✓ {result.duration_ms:.2f}ms")
            else:
                print(f"✗ 실패: {result.error_message}")
    
    return generate_report(f"이력서 조회 API 테스트 ({test_type})", results)


def generate_report(test_name: str, results: List[PerformanceResult]) -> PerformanceReport:
    """성능 리포트 생성"""
    
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]
    
    if not successful:
        return PerformanceReport(
            test_name=test_name,
            total_iterations=len(results),
            successful_iterations=0,
            failed_iterations=len(results),
            total_duration_ms=0,
            avg_duration_ms=0,
            min_duration_ms=0,
            max_duration_ms=0,
            p50_duration_ms=0,
            p95_duration_ms=0,
            p99_duration_ms=0,
            std_dev_ms=0,
            throughput_per_sec=0,
            results=results
        )
    
    durations = [r.duration_ms for r in successful]
    total_duration = sum(durations)
    
    return PerformanceReport(
        test_name=test_name,
        total_iterations=len(results),
        successful_iterations=len(successful),
        failed_iterations=len(failed),
        total_duration_ms=total_duration,
        avg_duration_ms=statistics.mean(durations),
        min_duration_ms=min(durations),
        max_duration_ms=max(durations),
        p50_duration_ms=calculate_percentile(durations, 50),
        p95_duration_ms=calculate_percentile(durations, 95),
        p99_duration_ms=calculate_percentile(durations, 99),
        std_dev_ms=statistics.stdev(durations) if len(durations) > 1 else 0,
        throughput_per_sec=len(successful) / (total_duration / 1000) if total_duration > 0 else 0,
        results=results
    )


def print_report(report: PerformanceReport):
    """리포트 출력"""
    
    if report is None:
        return
    
    print(f"\n{'='*60}")
    print(f"📊 {report.test_name} 결과")
    print(f"{'='*60}")
    print(f"총 요청 수: {report.total_iterations}")
    print(f"성공: {report.successful_iterations} ({report.successful_iterations/report.total_iterations*100:.1f}%)")
    print(f"실패: {report.failed_iterations}")
    print(f"\n⏱️  응답 시간 통계 (ms):")
    print(f"  - 평균: {report.avg_duration_ms:.2f}")
    print(f"  - 최소: {report.min_duration_ms:.2f}")
    print(f"  - 최대: {report.max_duration_ms:.2f}")
    print(f"  - P50: {report.p50_duration_ms:.2f}")
    print(f"  - P95: {report.p95_duration_ms:.2f}")
    print(f"  - P99: {report.p99_duration_ms:.2f}")
    print(f"  - 표준편차: {report.std_dev_ms:.2f}")
    print(f"\n🚀 처리량: {report.throughput_per_sec:.4f} req/sec")
    print(f"{'='*60}")


def save_report(report: PerformanceReport, output_path: str):
    """리포트를 JSON 파일로 저장"""
    if report is None:
        return
    
    report_data = report.to_dict()
    report_data["timestamp"] = datetime.now().isoformat()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n📁 리포트 저장: {output_path}")


async def main():
    parser = argparse.ArgumentParser(description="이력서 생성 API 성능 테스트")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API 서버 URL")
    parser.add_argument("--iterations", type=int, default=10, help="테스트 반복 횟수")
    parser.add_argument("--concurrent", type=int, default=1, help="동시 실행 수")
    parser.add_argument("--test-type", choices=["create", "fetch", "both"], default="both", 
                        help="테스트 유형: create(생성), fetch(조회), both(모두)")
    parser.add_argument("--output", type=str, help="결과 저장 파일 경로 (JSON)")
    
    args = parser.parse_args()
    
    reports = []
    
    if args.test_type in ["create", "both"]:
        report = await run_resume_creation_test(
            args.api_url,
            args.iterations,
            args.concurrent
        )
        print_report(report)
        reports.append(("resume_creation", report))
    
    if args.test_type in ["fetch", "both"]:
        report = await run_resume_fetch_test(
            args.api_url,
            args.iterations,
            concurrency=args.concurrent
        )
        print_report(report)
        if report:
            reports.append(("resume_fetch", report))
    
    # 결과 저장
    output_path = args.output or os.path.join(
        os.path.dirname(__file__),
        f"resume_performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    
    combined_report = {
        "timestamp": datetime.now().isoformat(),
        "config": {
            "api_url": args.api_url,
            "iterations": args.iterations,
            "concurrent": args.concurrent,
            "test_type": args.test_type
        },
        "results": {name: report.to_dict() for name, report in reports if report}
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(combined_report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📁 종합 리포트 저장: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
