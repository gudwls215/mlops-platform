#!/bin/bash

# MLOps Platform Docker 관리 스크립트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'  
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 함수 정의
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 사용법 출력
usage() {
    echo "사용법: $0 {dev|prod|stop|clean|logs|build}"
    echo ""
    echo "명령어:"
    echo "  dev     - 개발 환경 시작"
    echo "  prod    - 프로덕션 환경 시작"
    echo "  stop    - 모든 서비스 중지"
    echo "  clean   - 모든 컨테이너 및 볼륨 제거"
    echo "  logs    - 로그 확인"
    echo "  build   - 이미지 다시 빌드"
    echo "  status  - 서비스 상태 확인"
    exit 1
}

# 개발 환경 시작
start_dev() {
    print_info "개발 환경을 시작합니다..."
    
    # .env 파일 확인
    if [ ! -f .env ]; then
        print_warning ".env 파일이 없습니다. .env.example을 복사하여 설정하세요."
        cp .env.example .env 2>/dev/null || true
    fi
    
    docker-compose -f docker-compose.dev.yml up -d
    print_success "개발 환경이 시작되었습니다!"
    print_info "백엔드: http://localhost:8000"
    print_info "MLflow: http://localhost:5000"
    print_info "API 문서: http://localhost:8000/docs"
}

# 프로덕션 환경 시작
start_prod() {
    print_info "프로덕션 환경을 시작합니다..."
    
    # .env 파일 확인
    if [ ! -f .env ]; then
        print_error ".env 파일이 필요합니다!"
        exit 1
    fi
    
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
    print_success "프로덕션 환경이 시작되었습니다!"
    print_info "서비스: http://localhost"
    print_info "Grafana: http://localhost:3000"
    print_info "Prometheus: http://localhost:9090"
}

# 서비스 중지
stop_services() {
    print_info "모든 서비스를 중지합니다..."
    docker-compose -f docker-compose.yml down 2>/dev/null || true
    docker-compose -f docker-compose.dev.yml down 2>/dev/null || true
    docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
    print_success "모든 서���스가 중지되었습니다."
}

# 정리 작업
clean_all() {
    print_warning "모든 컨테이너, 이미지, 볼륨을 제거합니다. 계속하시겠습니까? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_info "정리 작업을 시작합니다..."
        docker-compose -f docker-compose.yml down -v --remove-orphans 2>/dev/null || true
        docker-compose -f docker-compose.dev.yml down -v --remove-orphans 2>/dev/null || true
        docker-compose -f docker-compose.prod.yml down -v --remove-orphans 2>/dev/null || true
        
        # MLOps 관련 이미지 제거
        docker images | grep mlops | awk '{print $3}' | xargs docker rmi 2>/dev/null || true
        
        print_success "정리 작업이 완료되었습니다."
    else
        print_info "정리 작업이 취소되었습니다."
    fi
}

# 로그 확인
show_logs() {
    print_info "서비스 로그를 확인합니다..."
    if docker-compose -f docker-compose.dev.yml ps -q > /dev/null 2>&1; then
        docker-compose -f docker-compose.dev.yml logs -f
    elif docker-compose -f docker-compose.yml ps -q > /dev/null 2>&1; then
        docker-compose -f docker-compose.yml logs -f
    else
        print_error "실행 중인 서비스가 없습니다."
    fi
}

# 이미지 빌드
build_images() {
    print_info "Docker 이미지를 다시 빌드합니다..."
    docker-compose -f docker-compose.yml build --no-cache
    docker-compose -f docker-compose.dev.yml build --no-cache
    print_success "이미지 빌드가 완료되었습니다."
}

# 서비스 상태 확인
check_status() {
    print_info "서비스 상태를 확인합니다..."
    echo ""
    echo "=== 개발 환경 ==="
    docker-compose -f docker-compose.dev.yml ps 2>/dev/null || echo "개발 환경이 실행되지 않음"
    echo ""
    echo "=== 프로덕션 환경 ==="
    docker-compose -f docker-compose.yml ps 2>/dev/null || echo "프로덕션 환경이 실행되지 않음"
}

# 메인 로직
case "$1" in
    dev)
        start_dev
        ;;
    prod)
        start_prod
        ;;
    stop)
        stop_services
        ;;
    clean)
        clean_all
        ;;
    logs)
        show_logs
        ;;
    build)
        build_images
        ;;
    status)
        check_status
        ;;
    *)
        usage
        ;;
esac