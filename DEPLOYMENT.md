# Production Deployment Guide
# 프로덕션 배포 가이드

## 목차
1. [사전 준비](#사전-준비)
2. [환경 설정](#환경-설정)
3. [배포 실행](#배포-실행)
4. [서비스 관리](#서비스-관리)
5. [백업 및 복구](#백업-및-복구)
6. [모니터링](#모니터링)
7. [트러블슈팅](#트러블슈팅)

---

## 사전 준비

### 시스템 요구사항
- **OS**: Ubuntu 20.04 LTS 이상
- **Python**: 3.11+
- **PostgreSQL**: 13+
- **Redis**: 6+
- **Nginx**: 1.18+
- **메모리**: 최소 4GB (권장 8GB)
- **디스크**: 최소 20GB (데이터/로그 공간 포함)

### 필수 소프트웨어 설치

```bash
# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# Python 3.11 설치
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# PostgreSQL 클라이언트 설치
sudo apt install -y postgresql-client

# Redis 설치
sudo apt install -y redis-server

# Nginx 설치
sudo apt install -y nginx

# 기타 의존성
sudo apt install -y build-essential git curl
```

### 방화벽 설정

```bash
# HTTP/HTTPS 포트 열기
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# SSH 포트 (필요시)
sudo ufw allow 22/tcp

sudo ufw enable
```

---

## 환경 설정

### 1. 환경 변수 파일 생성

`.env.production` 파일을 프로젝트 루트에 생성하고 실제 값으로 채웁니다:

```bash
cd /home/ttm/tensorflow-jupyter/jupyterNotebook/khj/mlops-platform/backend
cp .env.production.example .env.production
nano .env.production
```

**반드시 수정해야 할 필수 설정:**

```ini
# 보안 - 새로운 SECRET_KEY 생성
SECRET_KEY="your-super-secret-key-here-min-32-chars"

# CORS - 프론트엔드 도메인 설정
ALLOWED_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"

# 데이터베이스 - 실제 연결 정보
DATABASE_HOST="114.202.2.226"
DATABASE_PORT="5433"
DATABASE_NAME="mlops_db"
DATABASE_USER="mlops_user"
DATABASE_PASSWORD="your-secure-password"

# OpenAI API
OPENAI_API_KEY="sk-your-actual-openai-api-key"

# SSL 인증서 경로 (Let's Encrypt 사용 시)
SSL_CERT_PATH="/etc/letsencrypt/live/yourdomain.com/fullchain.pem"
SSL_KEY_PATH="/etc/letsencrypt/live/yourdomain.com/privkey.pem"
```

### 2. SECRET_KEY 생성

```bash
# Python으로 안전한 SECRET_KEY 생성
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. SSL 인증서 설정 (Let's Encrypt)

```bash
# Certbot 설치
sudo apt install -y certbot python3-certbot-nginx

# SSL 인증서 발급
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 자동 갱신 테스트
sudo certbot renew --dry-run
```

---

## 배포 실행

### 1. 자동 배포 스크립트 실행

```bash
cd /home/ttm/tensorflow-jupyter/jupyterNotebook/khj/mlops-platform/backend

# 배포 스크립트 실행
./setup_production.sh
```

스크립트는 다음 작업을 자동으로 수행합니다:
1. ✓ 환경 변수 파일 확인
2. ✓ 필요한 디렉토리 생성
3. ✓ Python 가상환경 설정
4. ✓ 의존성 패키지 설치
5. ✓ 데이터베이스 마이그레이션
6. ✓ 프론트엔드 빌드 (있는 경우)
7. ✓ 프로덕션 설정 검증
8. ✓ Systemd 서비스 파일 생성

### 2. Systemd 서비스 등록

```bash
# 생성된 서비스 파일 복사
sudo cp /tmp/mlops-platform.service /etc/systemd/system/

# 서비스 활성화
sudo systemctl daemon-reload
sudo systemctl enable mlops-platform
sudo systemctl start mlops-platform

# 서비스 상태 확인
sudo systemctl status mlops-platform
```

### 3. Nginx 설정

```bash
# Nginx 설정 파일 복사
sudo cp nginx.conf /etc/nginx/sites-available/mlops-platform

# 심볼릭 링크 생성
sudo ln -s /etc/nginx/sites-available/mlops-platform /etc/nginx/sites-enabled/

# 기본 사이트 비활성화 (필요시)
sudo rm /etc/nginx/sites-enabled/default

# Nginx 설정 테스트
sudo nginx -t

# Nginx 재시작
sudo systemctl restart nginx
```

### 4. 배포 검증

```bash
# 애플리케이션 헬스 체크
curl http://localhost:9000/health

# Nginx를 통한 접근 테스트
curl https://yourdomain.com/health

# 로그 확인
sudo tail -f /var/log/mlops/app.log
```

---

## 서비스 관리

### 서비스 제어

```bash
# 서비스 시작
sudo systemctl start mlops-platform

# 서비스 중지
sudo systemctl stop mlops-platform

# 서비스 재시작
sudo systemctl restart mlops-platform

# 설정 리로드 (무중단)
sudo systemctl reload mlops-platform

# 서비스 상태 확인
sudo systemctl status mlops-platform
```

### 로그 확인

```bash
# 애플리케이션 로그
sudo tail -f /var/log/mlops/app.log

# 에러 로그
sudo tail -f /var/log/mlops/app_error.log

# Systemd 서비스 로그
sudo journalctl -u mlops-platform -f

# Nginx 로그
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 코드 업데이트

```bash
# 1. 최신 코드 가져오기
cd /home/ttm/tensorflow-jupyter/jupyterNotebook/khj/mlops-platform/backend
git pull origin main

# 2. 의존성 업데이트
source venv/bin/activate
pip install -r requirements.txt --upgrade

# 3. 데이터베이스 마이그레이션
alembic upgrade head

# 4. 서비스 재시작
sudo systemctl restart mlops-platform
```

---

## 백업 및 복구

### 자동 백업 설정

```bash
# Crontab 편집
crontab -e

# 다음 라인 추가 (매일 새벽 2시 백업)
0 2 * * * cd /home/ttm/tensorflow-jupyter/jupyterNotebook/khj/mlops-platform/backend && ./backup.sh >> /var/log/mlops/backup.log 2>&1
```

### 수동 백업

```bash
cd /home/ttm/tensorflow-jupyter/jupyterNotebook/khj/mlops-platform/backend

# 백업 실행
./backup.sh
```

백업 내용:
- PostgreSQL 데이터베이스 (압축)
- 업로드된 파일 (tar.gz)
- 백업 메타데이터 (JSON)

백업 위치: `/var/mlops/backups/`

### 복구

```bash
cd /home/ttm/tensorflow-jupyter/jupyterNotebook/khj/mlops-platform/backend

# 사용 가능한 백업 목록 확인
./restore.sh

# 특정 백업 복구
./restore.sh 20240115_143022

# 최신 백업 복구
./restore.sh latest
```

---

## 모니터링

### 헬스 체크

```bash
# API 헬스 체크
curl https://yourdomain.com/health

# 응답 예시
{
  "status": "healthy",
  "timestamp": "2024-01-15T14:30:22Z"
}
```

### 리소스 모니터링

```bash
# CPU/메모리 사용량
htop

# 디스크 사용량
df -h

# 프로세스 확인
ps aux | grep gunicorn

# 네트워크 연결
netstat -tulnp | grep :9000
```

### Prometheus 메트릭 (설정된 경우)

메트릭 엔드포인트: `http://localhost:9090/metrics`

주요 메트릭:
- `http_requests_total`: 총 HTTP 요청 수
- `http_request_duration_seconds`: 요청 처리 시간
- `http_requests_in_progress`: 진행 중인 요청
- `database_connections`: 데이터베이스 연결 수

---

## 트러블슈팅

### 일반적인 문제

#### 1. 서비스가 시작되지 않음

```bash
# 로그 확인
sudo journalctl -u mlops-platform -n 50

# 설정 검증
source venv/bin/activate
python -c "from app.core.production_config import validate_production_settings; validate_production_settings()"

# 권한 확인
ls -la /var/log/mlops/
ls -la /var/mlops/uploads/
```

#### 2. 데이터베이스 연결 실패

```bash
# PostgreSQL 연결 테스트
export PGPASSWORD="your-password"
psql -h 114.202.2.226 -p 5433 -U mlops_user -d mlops_db -c "SELECT 1;"

# 연결 풀 확인 (로그에서)
grep "connection pool" /var/log/mlops/app.log
```

#### 3. Nginx 502 Bad Gateway

```bash
# 백엔드 서비스 상태 확인
sudo systemctl status mlops-platform

# 백엔드 포트 리스닝 확인
sudo netstat -tulnp | grep :9000

# Nginx 에러 로그
sudo tail -f /var/log/nginx/error.log

# SELinux 설정 (CentOS/RHEL인 경우)
sudo setsebool -P httpd_can_network_connect 1
```

#### 4. 높은 메모리 사용량

```bash
# Worker 수 조정 (서비스 파일 수정)
sudo nano /etc/systemd/system/mlops-platform.service

# --workers 값을 줄임 (예: 4 → 2)
# 권장: (2 x CPU 코어 수) + 1

sudo systemctl daemon-reload
sudo systemctl restart mlops-platform
```

#### 5. 느린 응답 시간

```bash
# 데이터베이스 쿼리 로그 활성화
# .env.production에 추가
SQLALCHEMY_ECHO=true

# Redis 연결 확인
redis-cli ping

# 캐시 통계 확인
redis-cli info stats
```

### 성능 튜닝

#### 데이터베이스 연결 풀

`.env.production`:
```ini
# 트래픽에 따라 조정
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
```

#### Gunicorn Worker

`/etc/systemd/system/mlops-platform.service`:
```ini
# Worker 수 = (2 x CPU 코어) + 1
ExecStart=/home/ttm/.../venv/bin/gunicorn --workers 4 ...

# 타임아웃 조정 (긴 요청 처리 시)
--timeout 120
```

#### Nginx 버퍼

`/etc/nginx/sites-available/mlops-platform`:
```nginx
# 대용량 요청 처리
client_max_body_size 50M;
client_body_buffer_size 1M;

# 프록시 버퍼
proxy_buffering on;
proxy_buffer_size 4k;
proxy_buffers 8 4k;
```

---

## 보안 체크리스트

- [ ] SECRET_KEY가 강력하고 고유함 (32자 이상)
- [ ] 데이터베이스 비밀번호가 강력함
- [ ] ALLOWED_ORIGINS가 올바르게 설정됨
- [ ] SSL/HTTPS가 활성화됨
- [ ] DEBUG=false로 설정됨
- [ ] 방화벽이 활성화되고 필요한 포트만 열림
- [ ] 파일 업로드 크기 제한이 설정됨
- [ ] Rate limiting이 활성화됨
- [ ] 로그 파일 권한이 적절함 (600 or 644)
- [ ] 백업이 자동으로 실행되고 암호화됨
- [ ] Nginx 보안 헤더가 설정됨
- [ ] 정기적인 보안 업데이트 계획이 있음

---

## 긴급 연락처 및 문서

- **기술 지원**: [이메일/전화]
- **서버 접근**: [SSH 정보]
- **데이터베이스 관리자**: [연락처]
- **API 문서**: https://yourdomain.com/docs
- **상태 페이지**: https://status.yourdomain.com

---

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|-----------|
| 2024-01-15 | 1.0.0 | 초기 프로덕션 배포 가이드 작성 |
