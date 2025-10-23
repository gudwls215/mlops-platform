#!/bin/bash
# Production Setup Script
# 프로덕션 환경 초기 설정 스크립트

set -e

echo "=================================="
echo "MLOps Platform - Production Setup"
echo "=================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. 환경 변수 확인
echo -e "\n${YELLOW}[1/8] Checking environment variables...${NC}"
if [ ! -f .env.production ]; then
    echo -e "${RED}Error: .env.production file not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Environment file found${NC}"

# 2. 필수 디렉토리 생성
echo -e "\n${YELLOW}[2/8] Creating required directories...${NC}"
sudo mkdir -p /var/log/mlops
sudo mkdir -p /var/mlops/uploads
sudo mkdir -p /var/mlops/backups
sudo mkdir -p /var/mlops/mlflow-artifacts

# 권한 설정
sudo chown -R $USER:$USER /var/log/mlops
sudo chown -R $USER:$USER /var/mlops
echo -e "${GREEN}✓ Directories created${NC}"

# 3. Python 가상환경 확인
echo -e "\n${YELLOW}[3/8] Checking Python virtual environment...${NC}"
PYTHON_CMD=""

# Prefer python3.11 if available, otherwise fallback to python3
if command -v python3.11 >/dev/null 2>&1; then
    PYTHON_CMD=python3.11
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD=python3
else
    echo -e "${RED}Error: No suitable Python interpreter found. Please install Python 3.11+ and retry.${NC}"
    exit 1
fi

# Check interpreter version
PY_VERSION=$(${PYTHON_CMD} -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(${PYTHON_CMD} -c "import sys; print(sys.version_info.major)")
PY_MINOR=$(${PYTHON_CMD} -c "import sys; print(sys.version_info.minor)")

if [ "${PY_MAJOR}" -lt 3 ] || { [ "${PY_MAJOR}" -eq 3 ] && [ "${PY_MINOR}" -lt 11 ]; }; then
    echo -e "${RED}Detected Python ${PY_VERSION}. This project requires Python 3.11 or newer to install all dependencies (numpy 2.x, numba, torch, triton, etc.).${NC}"
    echo -e "${YELLOW}Remediation options:${NC}"
    echo "  1) Install Python 3.11 and recreate the virtualenv:" 
    echo "       sudo apt install -y python3.11 python3.11-venv"
    echo "       rm -rf venv"
    echo "       ${PYTHON_CMD}=python3.11 # use python3.11 in the command below"
    echo "       python3.11 -m venv venv"
    echo "       source venv/bin/activate"
    echo "       pip install -r requirements.txt"
    echo "  2) (Advanced) If you cannot upgrade Python, pin or change incompatible packages (not recommended for production). Example: change numpy to 1.26.x in requirements.txt"
    echo -e "\n${RED}Exiting setup. Please install Python 3.11+ and re-run this script.${NC}"
    exit 1
fi

# Create venv using the selected python if not present
if [ ! -d "venv" ]; then
    echo "Creating virtual environment with ${PYTHON_CMD}..."
    ${PYTHON_CMD} -m venv venv
fi
source venv/bin/activate

# Verify venv python version
VENV_PYTHON=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
if [ "$(echo ${VENV_PYTHON} | cut -d. -f1)" -lt 3 ] || [ "$(echo ${VENV_PYTHON} | cut -d. -f2)" -lt 11 ] ; then
    echo -e "${RED}The virtual environment Python is ${VENV_PYTHON}, which is older than 3.11. Remove 'venv' and recreate it using python3.11:${NC}"
    echo "  rm -rf venv && python3.11 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

echo -e "${GREEN}✓ Virtual environment ready (Python ${VENV_PYTHON})${NC}"

# 4. 의존성 설치
echo -e "\n${YELLOW}[4/8] Installing production dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn uvicorn[standard]
echo -e "${GREEN}✓ Dependencies installed${NC}"

# 5. 데이터베이스 마이그레이션
echo -e "\n${YELLOW}[5/8] Running database migrations...${NC}"
# Alembic 마이그레이션 실행
if [ -d "alembic" ]; then
    alembic upgrade head
    echo -e "${GREEN}✓ Database migrations completed${NC}"
else
    echo -e "${YELLOW}⚠ Alembic not configured, skipping migrations${NC}"
fi

# 6. 정적 파일 수집 (프론트엔드가 있는 경우)
echo -e "\n${YELLOW}[6/8] Collecting static files...${NC}"
if [ -d "../frontend" ]; then
    cd ../frontend
    npm install
    npm run build
    cd ../backend
    echo -e "${GREEN}✓ Static files collected${NC}"
else
    echo -e "${YELLOW}⚠ Frontend not found, skipping${NC}"
fi

# 7. 설정 검증
echo -e "\n${YELLOW}[7/8] Validating production configuration...${NC}"
python3 << EOF
import sys
sys.path.insert(0, '.')
from app.core.production_config import validate_production_settings

try:
    validate_production_settings()
    print("✓ Configuration valid")
except ValueError as e:
    print(f"✗ Configuration validation failed:")
    print(str(e))
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Configuration validated${NC}"
else
    echo -e "${RED}✗ Configuration validation failed${NC}"
    echo "Please fix the errors in .env.production and run again"
    exit 1
fi

# 8. Systemd 서비스 파일 생성
echo -e "\n${YELLOW}[8/8] Creating systemd service file...${NC}"
cat > /tmp/mlops-platform.service << 'EOF'
[Unit]
Description=MLOps Platform API Server
After=network.target postgresql.service

[Service]
Type=notify
User=ttm
Group=ttm
WorkingDirectory=/home/ttm/tensorflow-jupyter/jupyterNotebook/khj/mlops-platform/backend
Environment="PATH=/home/ttm/tensorflow-jupyter/jupyterNotebook/khj/mlops-platform/backend/venv/bin"
ExecStart=/home/ttm/tensorflow-jupyter/jupyterNotebook/khj/mlops-platform/backend/venv/bin/gunicorn \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    -b 0.0.0.0:9000 \
    --timeout 30 \
    --access-logfile /var/log/mlops/access.log \
    --error-logfile /var/log/mlops/error.log \
    app.main:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "Systemd service file created at /tmp/mlops-platform.service"
echo "To install, run:"
echo "  sudo mv /tmp/mlops-platform.service /etc/systemd/system/"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl enable mlops-platform"
echo "  sudo systemctl start mlops-platform"

echo -e "\n${GREEN}=================================="
echo "Production setup completed!"
echo "==================================${NC}"
echo ""
echo "Next steps:"
echo "1. Review and update .env.production with your production values"
echo "2. Generate a strong SECRET_KEY (at least 32 characters)"
echo "3. Update ALLOWED_ORIGINS with your domain"
echo "4. Install and start the systemd service"
echo "5. Configure Nginx as a reverse proxy"
echo "6. Set up SSL certificates (Let's Encrypt recommended)"
echo ""
echo "For manual start:"
echo "  source venv/bin/activate"
echo "  gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:9000 app.main:app"
