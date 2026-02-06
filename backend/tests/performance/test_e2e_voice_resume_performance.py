"""
E2E (End-to-End) 음성 이력서 생성 성능 테스트 스크립트

전체 플로우 테스트: 음성 파일 → STT 변환 → 이력서 생성

사용법:
    python test_e2e_voice_resume_performance.py [--api-url URL] [--iterations N] [--audio-file PATH]
"""
import asyncio
import aiohttp
import time
import statistics
import argparse
import os
import sys
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
import random
import string


@dataclass
class E2EStepResult:
    """각 단계별 결과"""
    step_name: str
    duration_ms: float
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    error_message: str = ""


@dataclass
class E2EPerformanceResult:
    """E2E 테스트 결과"""
    iteration: int
    total_duration_ms: float
    success: bool
    steps: List[E2EStepResult] = field(default_factory=list)
    error_message: str = ""


@dataclass
class E2EPerformanceReport:
    """E2E 성능 테스트 리포트"""
    test_name: str
    total_iterations: int
    successful_iterations: int
    failed_iterations: int
    # 전체 E2E 통계
    total_avg_duration_ms: float
    total_min_duration_ms: float
    total_max_duration_ms: float
    total_p50_ms: float
    total_p95_ms: float
    # 단계별 통계
    stt_avg_duration_ms: float
    stt_p95_duration_ms: float
    resume_creation_avg_duration_ms: float
    resume_creation_p95_duration_ms: float
    # 처리량
    throughput_per_sec: float
    results: List[E2EPerformanceResult] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_name": self.test_name,
            "total_iterations": self.total_iterations,
            "successful_iterations": self.successful_iterations,
            "failed_iterations": self.failed_iterations,
            "success_rate": round(self.successful_iterations / self.total_iterations * 100, 2),
            "e2e_statistics": {
                "avg_duration_ms": round(self.total_avg_duration_ms, 2),
                "min_duration_ms": round(self.total_min_duration_ms, 2),
                "max_duration_ms": round(self.total_max_duration_ms, 2),
                "p50_ms": round(self.total_p50_ms, 2),
                "p95_ms": round(self.total_p95_ms, 2)
            },
            "step_statistics": {
                "stt": {
                    "avg_duration_ms": round(self.stt_avg_duration_ms, 2),
                    "p95_duration_ms": round(self.stt_p95_duration_ms, 2)
                },
                "resume_creation": {
                    "avg_duration_ms": round(self.resume_creation_avg_duration_ms, 2),
                    "p95_duration_ms": round(self.resume_creation_p95_duration_ms, 2)
                }
            },
            "throughput_per_sec": round(self.throughput_per_sec, 4)
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


async def step_stt_transcribe(
    session: aiohttp.ClientSession,
    api_url: str,
    audio_file_path: str,
    language: str = "ko"
) -> E2EStepResult:
    """STT 변환 단계"""
    
    start_time = time.perf_counter()
    
    try:
        with open(audio_file_path, 'rb') as f:
            audio_data = f.read()
        
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
                return E2EStepResult(
                    step_name="STT 변환",
                    duration_ms=duration_ms,
                    success=True,
                    data={"transcript": transcript, "length": len(transcript)}
                )
            else:
                return E2EStepResult(
                    step_name="STT 변환",
                    duration_ms=duration_ms,
                    success=False,
                    error_message=response_json.get("error", "Unknown error")
                )
    
    except Exception as e:
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        return E2EStepResult(
            step_name="STT 변환",
            duration_ms=duration_ms,
            success=False,
            error_message=str(e)
        )


async def step_create_resume(
    session: aiohttp.ClientSession,
    api_url: str,
    transcript: str,
    iteration: int,
    user_id: int = 1
) -> E2EStepResult:
    """이력서 생성 단계"""
    
    start_time = time.perf_counter()
    
    try:
        # 랜덤 접미사 생성
        random_suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        
        # 이력서 제목 생성
        title = f"음성 녹음 이력서 - {datetime.now().strftime('%Y%m%d_%H%M%S')}_{random_suffix}"
        
        # 이력서 내용 구조화 (실제로는 LLM 등으로 처리할 수 있음)
        content = {
            "raw_transcript": transcript,
            "processed": True,
            "source": "voice_recording",
            "timestamp": datetime.now().isoformat()
        }
        
        # FormData 생성
        data = aiohttp.FormData()
        data.add_field('title', title)
        data.add_field('content', json.dumps(content, ensure_ascii=False))
        data.add_field('skills', json.dumps([]))
        data.add_field('user_id', str(user_id))
        
        async with session.post(f"{api_url}/api/resumes/", data=data) as response:
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000
            
            response_json = await response.json()
            
            if response.status == 200 and response_json.get("status") == "success":
                resume_id = response_json.get("data", {}).get("id")
                return E2EStepResult(
                    step_name="이력서 생성",
                    duration_ms=duration_ms,
                    success=True,
                    data={"resume_id": resume_id, "title": title}
                )
            else:
                return E2EStepResult(
                    step_name="이력서 생성",
                    duration_ms=duration_ms,
                    success=False,
                    error_message=response_json.get("error", str(response_json))
                )
    
    except Exception as e:
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        return E2EStepResult(
            step_name="이력서 생성",
            duration_ms=duration_ms,
            success=False,
            error_message=str(e)
        )


async def run_e2e_test_single(
    session: aiohttp.ClientSession,
    api_url: str,
    audio_file_path: str,
    iteration: int,
    language: str = "ko"
) -> E2EPerformanceResult:
    """단일 E2E 테스트 실행"""
    
    steps: List[E2EStepResult] = []
    total_start = time.perf_counter()
    
    # Step 1: STT 변환
    stt_result = await step_stt_transcribe(session, api_url, audio_file_path, language)
    steps.append(stt_result)
    
    if not stt_result.success:
        total_duration = (time.perf_counter() - total_start) * 1000
        return E2EPerformanceResult(
            iteration=iteration,
            total_duration_ms=total_duration,
            success=False,
            steps=steps,
            error_message=f"STT 변환 실패: {stt_result.error_message}"
        )
    
    # Step 2: 이력서 생성
    transcript = stt_result.data.get("transcript", "")
    
    if not transcript or len(transcript) < 10:
        # 변환된 텍스트가 너무 짧은 경우 샘플 텍스트 사용
        transcript = """
        안녕하세요. 저는 3년차 소프트웨어 개발자입니다.
        주로 Python과 JavaScript를 사용하여 웹 애플리케이션을 개발해왔습니다.
        현재 ABC 회사에서 백엔드 개발을 담당하고 있으며,
        RESTful API 설계와 데이터베이스 최적화 경험이 있습니다.
        """
    
    resume_result = await step_create_resume(session, api_url, transcript, iteration)
    steps.append(resume_result)
    
    total_duration = (time.perf_counter() - total_start) * 1000
    
    if not resume_result.success:
        return E2EPerformanceResult(
            iteration=iteration,
            total_duration_ms=total_duration,
            success=False,
            steps=steps,
            error_message=f"이력서 생성 실패: {resume_result.error_message}"
        )
    
    return E2EPerformanceResult(
        iteration=iteration,
        total_duration_ms=total_duration,
        success=True,
        steps=steps
    )


async def run_e2e_performance_test(
    api_url: str,
    audio_file_path: str,
    iterations: int,
    language: str = "ko",
    warmup_iterations: int = 2
) -> E2EPerformanceReport:
    """E2E 성능 테스트 실행"""
    
    print(f"\n{'='*70}")
    print("🎯 E2E 음성 이력서 생성 성능 테스트")
    print(f"{'='*70}")
    print(f"API URL: {api_url}")
    print(f"오디오 파일: {audio_file_path}")
    print(f"테스트 반복 횟수: {iterations}")
    print(f"워밍업 횟수: {warmup_iterations}")
    print(f"언어: {language}")
    print(f"{'='*70}\n")
    
    results: List[E2EPerformanceResult] = []
    
    timeout = aiohttp.ClientTimeout(total=300)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        
        # 워밍업 실행
        if warmup_iterations > 0:
            print("🔥 워밍업 실행 중...")
            for i in range(warmup_iterations):
                await run_e2e_test_single(session, api_url, audio_file_path, 0, language)
                print(f"  - 워밍업 {i+1}/{warmup_iterations} 완료")
            print()
        
        # 실제 테스트 실행
        print("📊 성능 테스트 시작...")
        for i in range(1, iterations + 1):
            print(f"\n[{i}/{iterations}] 테스트 실행 중...")
            result = await run_e2e_test_single(session, api_url, audio_file_path, i, language)
            results.append(result)
            
            if result.success:
                print(f"  ✓ 전체 소요시간: {result.total_duration_ms:.2f}ms")
                for step in result.steps:
                    status = "✓" if step.success else "✗"
                    print(f"    {status} {step.step_name}: {step.duration_ms:.2f}ms")
                    if step.data:
                        if "transcript" in step.data:
                            print(f"      - 변환된 텍스트 길이: {step.data.get('length', 0)}자")
                        if "resume_id" in step.data:
                            print(f"      - 이력서 ID: {step.data.get('resume_id')}")
            else:
                print(f"  ✗ 실패: {result.error_message}")
    
    return generate_e2e_report("E2E 음성 이력서 생성 테스트", results)


def generate_e2e_report(test_name: str, results: List[E2EPerformanceResult]) -> E2EPerformanceReport:
    """E2E 리포트 생성"""
    
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]
    
    if not successful:
        return E2EPerformanceReport(
            test_name=test_name,
            total_iterations=len(results),
            successful_iterations=0,
            failed_iterations=len(results),
            total_avg_duration_ms=0,
            total_min_duration_ms=0,
            total_max_duration_ms=0,
            total_p50_ms=0,
            total_p95_ms=0,
            stt_avg_duration_ms=0,
            stt_p95_duration_ms=0,
            resume_creation_avg_duration_ms=0,
            resume_creation_p95_duration_ms=0,
            throughput_per_sec=0,
            results=results
        )
    
    # 전체 E2E 통계
    total_durations = [r.total_duration_ms for r in successful]
    
    # 단계별 통계
    stt_durations = []
    resume_durations = []
    
    for r in successful:
        for step in r.steps:
            if step.step_name == "STT 변환" and step.success:
                stt_durations.append(step.duration_ms)
            elif step.step_name == "이력서 생성" and step.success:
                resume_durations.append(step.duration_ms)
    
    total_time_ms = sum(total_durations)
    
    return E2EPerformanceReport(
        test_name=test_name,
        total_iterations=len(results),
        successful_iterations=len(successful),
        failed_iterations=len(failed),
        total_avg_duration_ms=statistics.mean(total_durations) if total_durations else 0,
        total_min_duration_ms=min(total_durations) if total_durations else 0,
        total_max_duration_ms=max(total_durations) if total_durations else 0,
        total_p50_ms=calculate_percentile(total_durations, 50),
        total_p95_ms=calculate_percentile(total_durations, 95),
        stt_avg_duration_ms=statistics.mean(stt_durations) if stt_durations else 0,
        stt_p95_duration_ms=calculate_percentile(stt_durations, 95),
        resume_creation_avg_duration_ms=statistics.mean(resume_durations) if resume_durations else 0,
        resume_creation_p95_duration_ms=calculate_percentile(resume_durations, 95),
        throughput_per_sec=len(successful) / (total_time_ms / 1000) if total_time_ms > 0 else 0,
        results=results
    )


def print_e2e_report(report: E2EPerformanceReport):
    """E2E 리포트 출력"""
    
    print(f"\n{'='*70}")
    print(f"📊 {report.test_name} 결과")
    print(f"{'='*70}")
    
    print(f"\n📋 테스트 요약:")
    print(f"  - 총 테스트 수: {report.total_iterations}")
    print(f"  - 성공: {report.successful_iterations} ({report.successful_iterations/report.total_iterations*100:.1f}%)")
    print(f"  - 실패: {report.failed_iterations}")
    
    print(f"\n⏱️  E2E 전체 응답 시간 (ms):")
    print(f"  - 평균: {report.total_avg_duration_ms:.2f}")
    print(f"  - 최소: {report.total_min_duration_ms:.2f}")
    print(f"  - 최대: {report.total_max_duration_ms:.2f}")
    print(f"  - P50: {report.total_p50_ms:.2f}")
    print(f"  - P95: {report.total_p95_ms:.2f}")
    
    print(f"\n📊 단계별 성능 분석:")
    print(f"\n  🎤 STT 변환:")
    print(f"    - 평균: {report.stt_avg_duration_ms:.2f}ms")
    print(f"    - P95: {report.stt_p95_duration_ms:.2f}ms")
    if report.total_avg_duration_ms > 0:
        stt_ratio = report.stt_avg_duration_ms / report.total_avg_duration_ms * 100
        print(f"    - 비중: {stt_ratio:.1f}%")
    
    print(f"\n  📝 이력서 생성:")
    print(f"    - 평균: {report.resume_creation_avg_duration_ms:.2f}ms")
    print(f"    - P95: {report.resume_creation_p95_duration_ms:.2f}ms")
    if report.total_avg_duration_ms > 0:
        resume_ratio = report.resume_creation_avg_duration_ms / report.total_avg_duration_ms * 100
        print(f"    - 비중: {resume_ratio:.1f}%")
    
    print(f"\n🚀 처리량: {report.throughput_per_sec:.4f} req/sec")
    print(f"{'='*70}")
    
    # 실패 상세 내역
    if report.failed_iterations > 0:
        print("\n❌ 실패 상세:")
        for r in report.results:
            if not r.success:
                print(f"  - [{r.iteration}] {r.error_message}")


def save_e2e_report(report: E2EPerformanceReport, output_path: str):
    """E2E 리포트를 JSON 파일로 저장"""
    
    report_data = report.to_dict()
    report_data["timestamp"] = datetime.now().isoformat()
    report_data["individual_results"] = [
        {
            "iteration": r.iteration,
            "total_duration_ms": round(r.total_duration_ms, 2),
            "success": r.success,
            "steps": [
                {
                    "step_name": s.step_name,
                    "duration_ms": round(s.duration_ms, 2),
                    "success": s.success,
                    "data": s.data,
                    "error_message": s.error_message
                }
                for s in r.steps
            ],
            "error_message": r.error_message
        }
        for r in report.results
    ]
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n📁 리포트 저장: {output_path}")


async def main():
    parser = argparse.ArgumentParser(description="E2E 음성 이력서 생성 성능 테스트")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API 서버 URL")
    parser.add_argument("--audio-file", type=str, help="테스트할 오디오 파일 경로")
    parser.add_argument("--iterations", type=int, default=5, help="테스트 반복 횟수")
    parser.add_argument("--language", default="ko", help="인식 언어 코드")
    parser.add_argument("--warmup", type=int, default=2, help="워밍업 횟수")
    parser.add_argument("--output", type=str, help="결과 저장 파일 경로 (JSON)")
    
    args = parser.parse_args()
    
    # 오디오 파일 확인
    audio_file_path = args.audio_file
    
    if not audio_file_path:
        # 기본 테스트 오디오 파일 경로
        audio_file_path = os.path.join(
            os.path.dirname(__file__), 
            "sample_audio.wav"
        )
    
    if not os.path.exists(audio_file_path):
        print(f"❌ 오디오 파일을 찾을 수 없습니다: {audio_file_path}")
        print("\n💡 테스트 실행 방법:")
        print("  1. 실제 음성 파일로 테스트:")
        print("     python test_e2e_voice_resume_performance.py --audio-file /path/to/audio.wav")
        print("\n  2. 샘플 파일 생성 후 테스트:")
        print("     먼저 test_stt_performance.py --create-sample 실행 후 이 스크립트 실행")
        sys.exit(1)
    
    # 파일 정보 출력
    file_size = os.path.getsize(audio_file_path)
    print(f"📁 오디오 파일: {audio_file_path}")
    print(f"📁 파일 크기: {file_size / 1024:.2f} KB")
    
    # 테스트 실행
    report = await run_e2e_performance_test(
        args.api_url,
        audio_file_path,
        args.iterations,
        args.language,
        args.warmup
    )
    
    # 결과 출력
    print_e2e_report(report)
    
    # 결과 저장
    output_path = args.output or os.path.join(
        os.path.dirname(__file__),
        f"e2e_voice_resume_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    save_e2e_report(report, output_path)


if __name__ == "__main__":
    asyncio.run(main())
