# 음성 이력서 생성 성능 테스트

이 디렉토리에는 마이크로 입력한 음성을 통한 이력서 생성 기능의 성능을 테스트하는 스크립트가 포함되어 있습니다.

## 테스트 스크립트

### 1. STT API 성능 테스트 (`test_stt_performance.py`)

음성 파일을 텍스트로 변환하는 Speech-to-Text API의 성능을 측정합니다.

```bash
# 기본 사용법 (순차 실행)
python test_stt_performance.py --audio-file /path/to/audio.wav --iterations 10

# 동시 실행 테스트
python test_stt_performance.py --audio-file /path/to/audio.wav --iterations 20 --concurrent 5

# 샘플 오디오 파일 생성
python test_stt_performance.py --create-sample

# 전체 옵션
python test_stt_performance.py \
    --api-url http://localhost:8000 \
    --audio-file /path/to/audio.wav \
    --iterations 10 \
    --concurrent 5 \
    --language ko \
    --output results.json
```

**옵션:**
- `--api-url`: API 서버 URL (기본: http://localhost:8000)
- `--audio-file`: 테스트할 오디오 파일 경로
- `--iterations`: 테스트 반복 횟수 (기본: 10)
- `--concurrent`: 동시 실행 수 (기본: 0, 순차 실행)
- `--language`: 인식 언어 코드 (기본: ko)
- `--output`: 결과 저장 파일 경로

---

### 2. 이력서 생성 API 성능 테스트 (`test_resume_generation_performance.py`)

텍스트 입력으로 이력서를 생성하는 API의 성능을 측정합니다.

```bash
# 이력서 생성 테스트
python test_resume_generation_performance.py --test-type create --iterations 10

# 이력서 조회 테스트
python test_resume_generation_performance.py --test-type fetch --iterations 10

# 생성 + 조회 모두 테스트
python test_resume_generation_performance.py --test-type both --iterations 10

# 동시 실행 테스트
python test_resume_generation_performance.py --iterations 20 --concurrent 5

# 전체 옵션
python test_resume_generation_performance.py \
    --api-url http://localhost:8000 \
    --iterations 10 \
    --concurrent 3 \
    --test-type both \
    --output results.json
```

**옵션:**
- `--api-url`: API 서버 URL (기본: http://localhost:8000)
- `--iterations`: 테스트 반복 횟수 (기본: 10)
- `--concurrent`: 동시 실행 수 (기본: 1)
- `--test-type`: 테스트 유형 - create(생성), fetch(조회), both(모두)
- `--output`: 결과 저장 파일 경로

---

### 3. E2E 성능 테스트 (`test_e2e_voice_resume_performance.py`)

전체 플로우(음성 → STT → 이력서 생성)의 성능을 종합적으로 측정합니다.

```bash
# 기본 사용법
python test_e2e_voice_resume_performance.py --audio-file /path/to/audio.wav --iterations 5

# 워밍업 횟수 조정
python test_e2e_voice_resume_performance.py --audio-file /path/to/audio.wav --warmup 3 --iterations 10

# 전체 옵션
python test_e2e_voice_resume_performance.py \
    --api-url http://localhost:8000 \
    --audio-file /path/to/audio.wav \
    --iterations 10 \
    --language ko \
    --warmup 2 \
    --output e2e_results.json
```

**옵션:**
- `--api-url`: API 서버 URL (기본: http://localhost:8000)
- `--audio-file`: 테스트할 오디오 파일 경로
- `--iterations`: 테스트 반복 횟수 (기본: 5)
- `--language`: 인식 언어 코드 (기본: ko)
- `--warmup`: 워밍업 횟수 (기본: 2)
- `--output`: 결과 저장 파일 경로

---

## 테스트 실행 전 준비사항

### 1. 의존성 설치

```bash
pip install aiohttp
```

샘플 오디오 파일 생성을 위해서는 추가로:
```bash
pip install pydub
```

### 2. 백엔드 서버 실행

```bash
cd /home/ttm/tensorflow-jupyter/jupyterNotebook/khj/mlops-platform/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 테스트용 오디오 파일 준비

실제 음성 녹음 파일을 사용하거나, 샘플 파일을 생성합니다:

```bash
# 샘플 파일 생성 (pydub 필요)
python test_stt_performance.py --create-sample
```

지원되는 오디오 형식: `.mp3`, `.wav`, `.m4a`, `.ogg`, `.flac`, `.webm`

---

## 성능 측정 지표

테스트 결과에는 다음 지표가 포함됩니다:

| 지표 | 설명 |
|------|------|
| 평균 응답 시간 (avg) | 모든 요청의 평균 처리 시간 |
| 최소/최대 응답 시간 | 가장 빠른/느린 요청 시간 |
| P50, P95, P99 | 백분위 응답 시간 |
| 표준편차 (std_dev) | 응답 시간의 일관성 측정 |
| 처리량 (throughput) | 초당 처리 가능한 요청 수 |
| 성공률 | 성공한 요청의 비율 |

---

## 예시 결과 출력

```
============================================================
📊 E2E 음성 이력서 생성 테스트 결과
============================================================

📋 테스트 요약:
  - 총 테스트 수: 10
  - 성공: 10 (100.0%)
  - 실패: 0

⏱️  E2E 전체 응답 시간 (ms):
  - 평균: 2345.67
  - 최소: 1890.45
  - 최대: 3456.78
  - P50: 2234.56
  - P95: 3123.45

📊 단계별 성능 분석:

  🎤 STT 변환:
    - 평균: 2123.45ms
    - P95: 2890.12ms
    - 비중: 90.5%

  📝 이력서 생성:
    - 평균: 222.22ms
    - P95: 456.78ms
    - 비중: 9.5%

🚀 처리량: 0.4265 req/sec
============================================================
```

---

## 권장 테스트 시나리오

### 1. 기본 성능 측정
```bash
# STT 성능만 먼저 확인
python test_stt_performance.py --audio-file sample.wav --iterations 10

# 이력서 생성 성능 확인
python test_resume_generation_performance.py --test-type create --iterations 10
```

### 2. 부하 테스트
```bash
# 동시 5명 사용자 시뮬레이션
python test_stt_performance.py --audio-file sample.wav --iterations 50 --concurrent 5
```

### 3. 전체 시스템 테스트
```bash
# E2E 테스트로 전체 플로우 검증
python test_e2e_voice_resume_performance.py --audio-file sample.wav --iterations 10 --warmup 3
```

---

## 결과 파일

테스트 완료 후 JSON 형식의 상세 결과 파일이 생성됩니다:

- `stt_performance_YYYYMMDD_HHMMSS.json`
- `resume_performance_YYYYMMDD_HHMMSS.json`
- `e2e_voice_resume_YYYYMMDD_HHMMSS.json`

결과 파일을 분석하여 성능 개선 포인트를 파악할 수 있습니다.
