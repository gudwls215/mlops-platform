"""
STT (Speech-to-Text) API 성능 테스트 스크립트

음성 파일을 텍스트로 변환하는 /api/speech/transcribe API의 성능을 측정합니다.

사용법:
    python test_stt_performance.py [--api-url URL] [--iterations N] [--audio-file PATH]
"""
import asyncio
import aiohttp
import time
import statistics
import argparse
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class PerformanceResult:
    """성능 측정 결과"""
    iteration: int
    duration_ms: float
    status_code: int
    success: bool
    transcript_length: int = 0
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


def create_sample_audio_file(output_path: str, duration_seconds: int = 5) -> str:
    """
    테스트용 샘플 오디오 파일 생성 (pydub 필요)
    실제 테스트 시에는 실제 음성 파일 사용 권장
    """
    try:
        from pydub import AudioSegment
        from pydub.generators import Sine
        
        # 간단한 비프음 생성 (테스트용)
        audio = Sine(440).to_audio_segment(duration=duration_seconds * 1000)
        audio = audio.set_channels(1).set_frame_rate(16000)
        audio.export(output_path, format="wav")
        print(f"샘플 오디오 파일 생성: {output_path}")
        return output_path
    except ImportError:
        print("pydub가 설치되지 않았습니다. pip install pydub를 실행하세요.")
        print("또는 --audio-file 옵션으로 실제 오디오 파일을 지정하세요.")
        return None


async def test_stt_api(
    session: aiohttp.ClientSession,
    api_url: str,
    audio_file_path: str,
    iteration: int,
    language: str = "ko"
) -> PerformanceResult:
    """STT API 단일 요청 테스트"""
    
    start_time = time.perf_counter()
    
    try:
        with open(audio_file_path, 'rb') as f:
            audio_data = f.read()
        
        # FormData 생성
        data = aiohttp.FormData()
        data.add_field('file', audio_data, 
                       filename=os.path.basename(audio_file_path),
                       content_type='audio/webm')
        data.add_field('language', language)
        data.add_field('with_timestamps', 'false')
        
        async with session.post(f"{api_url}/api/speech/transcribe", data=data) as response:
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000
            
            response_json = await response.json()
            
            if response.status == 200 and response_json.get("status") == "success":
                transcript = response_json.get("text", "")
                return PerformanceResult(
                    iteration=iteration,
                    duration_ms=duration_ms,
                    status_code=response.status,
                    success=True,
                    transcript_length=len(transcript)
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


async def run_sequential_test(
    api_url: str,
    audio_file_path: str,
    iterations: int,
    language: str = "ko"
) -> PerformanceReport:
    """순차적 STT API 테스트 실행"""
    
    print(f"\n{'='*60}")
    print("STT API 성능 테스트 시작 (순차 실행)")
    print(f"{'='*60}")
    print(f"API URL: {api_url}")
    print(f"오디오 파일: {audio_file_path}")
    print(f"반복 횟수: {iterations}")
    print(f"언어: {language}")
    print(f"{'='*60}\n")
    
    results: List[PerformanceResult] = []
    
    timeout = aiohttp.ClientTimeout(total=300)  # 5분 타임아웃
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for i in range(1, iterations + 1):
            print(f"[{i}/{iterations}] 테스트 실행 중...", end=" ")
            result = await test_stt_api(session, api_url, audio_file_path, i, language)
            results.append(result)
            
            if result.success:
                print(f"✓ {result.duration_ms:.2f}ms (텍스트 길이: {result.transcript_length}자)")
            else:
                print(f"✗ 실패: {result.error_message}")
    
    return generate_report("STT API 순차 테스트", results)


async def run_concurrent_test(
    api_url: str,
    audio_file_path: str,
    iterations: int,
    concurrency: int = 5,
    language: str = "ko"
) -> PerformanceReport:
    """동시성 STT API 테스트 실행"""
    
    print(f"\n{'='*60}")
    print("STT API 성능 테스트 시작 (동시 실행)")
    print(f"{'='*60}")
    print(f"API URL: {api_url}")
    print(f"오디오 파일: {audio_file_path}")
    print(f"총 요청 수: {iterations}")
    print(f"동시 실행 수: {concurrency}")
    print(f"언어: {language}")
    print(f"{'='*60}\n")
    
    results: List[PerformanceResult] = []
    
    timeout = aiohttp.ClientTimeout(total=300)
    connector = aiohttp.TCPConnector(limit=concurrency)
    
    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        # 세마포어로 동시 실행 제어
        semaphore = asyncio.Semaphore(concurrency)
        
        async def bounded_test(iteration: int):
            async with semaphore:
                return await test_stt_api(session, api_url, audio_file_path, iteration, language)
        
        tasks = [bounded_test(i) for i in range(1, iterations + 1)]
        
        print(f"총 {len(tasks)}개 요청 시작...")
        start_time = time.perf_counter()
        results = await asyncio.gather(*tasks)
        end_time = time.perf_counter()
        
        total_time = (end_time - start_time) * 1000
        print(f"\n전체 소요 시간: {total_time:.2f}ms")
    
    return generate_report("STT API 동시성 테스트", list(results))


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
    
    # 실패 상세 내역
    if report.failed_iterations > 0:
        print("\n❌ 실패 상세:")
        for r in report.results:
            if not r.success:
                print(f"  - [{r.iteration}] {r.error_message}")


def save_report(report: PerformanceReport, output_path: str):
    """리포트를 JSON 파일로 저장"""
    report_data = report.to_dict()
    report_data["timestamp"] = datetime.now().isoformat()
    report_data["individual_results"] = [
        {
            "iteration": r.iteration,
            "duration_ms": round(r.duration_ms, 2),
            "success": r.success,
            "transcript_length": r.transcript_length,
            "error_message": r.error_message
        }
        for r in report.results
    ]
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n📁 리포트 저장: {output_path}")


async def main():
    parser = argparse.ArgumentParser(description="STT API 성능 테스트")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API 서버 URL")
    parser.add_argument("--audio-file", type=str, help="테스트할 오디오 파일 경로")
    parser.add_argument("--iterations", type=int, default=10, help="테스트 반복 횟수")
    parser.add_argument("--concurrent", type=int, default=0, help="동시 실행 수 (0이면 순차 실행)")
    parser.add_argument("--language", default="ko", help="인식 언어 코드")
    parser.add_argument("--output", type=str, help="결과 저장 파일 경로 (JSON)")
    parser.add_argument("--create-sample", action="store_true", help="샘플 오디오 파일 생성")
    
    args = parser.parse_args()
    
    # 오디오 파일 확인/생성
    audio_file_path = args.audio_file
    
    if not audio_file_path:
        # 기본 테스트 오디오 파일 경로
        audio_file_path = os.path.join(
            os.path.dirname(__file__), 
            "sample_audio.wav"
        )
        
        if not os.path.exists(audio_file_path) or args.create_sample:
            print("⚠️  테스트용 오디오 파일이 없습니다.")
            print("--audio-file 옵션으로 실제 음성 파일을 지정하거나,")
            print("--create-sample 옵션으로 샘플 파일을 생성하세요.")
            
            if args.create_sample:
                result = create_sample_audio_file(audio_file_path)
                if not result:
                    sys.exit(1)
            else:
                sys.exit(1)
    
    if not os.path.exists(audio_file_path):
        print(f"❌ 오디오 파일을 찾을 수 없습니다: {audio_file_path}")
        sys.exit(1)
    
    # 파일 크기 출력
    file_size = os.path.getsize(audio_file_path)
    print(f"📁 오디오 파일 크기: {file_size / 1024:.2f} KB")
    
    # 테스트 실행
    if args.concurrent > 0:
        report = await run_concurrent_test(
            args.api_url,
            audio_file_path,
            args.iterations,
            args.concurrent,
            args.language
        )
    else:
        report = await run_sequential_test(
            args.api_url,
            audio_file_path,
            args.iterations,
            args.language
        )
    
    # 결과 출력
    print_report(report)
    
    # 결과 저장
    if args.output:
        save_report(report, args.output)
    else:
        # 기본 출력 경로
        default_output = os.path.join(
            os.path.dirname(__file__),
            f"stt_performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        save_report(report, default_output)


if __name__ == "__main__":
    asyncio.run(main())
