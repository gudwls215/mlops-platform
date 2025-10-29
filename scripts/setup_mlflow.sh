#!/bin/bash

# MLflow 설정 스크립트
# PostgreSQL 백엔드와 로컬 파일 아티팩트 스토어 사용

# 환경 변수
export MLFLOW_BACKEND_STORE_URI="postgresql://postgres:ttm1234@114.202.2.226:5433/postgres"
export MLFLOW_ARTIFACT_ROOT="/home/ttm/tensorflow-jupyter/jupyterNotebook/khj/mlops-platform/mlflow-artifacts"
export MLFLOW_HOST="0.0.0.0"
export MLFLOW_PORT="5000"

echo "=== MLflow Tracking Server 설정 ==="
echo "Backend Store: ${MLFLOW_BACKEND_STORE_URI}"
echo "Artifact Root: ${MLFLOW_ARTIFACT_ROOT}"
echo "Host: ${MLFLOW_HOST}"
echo "Port: ${MLFLOW_PORT}"
echo ""

# 아티팩트 디렉토리 생성
if [ ! -d "${MLFLOW_ARTIFACT_ROOT}" ]; then
    echo "Creating artifact directory..."
    mkdir -p "${MLFLOW_ARTIFACT_ROOT}"
    echo "✓ Artifact directory created: ${MLFLOW_ARTIFACT_ROOT}"
else
    echo "✓ Artifact directory already exists: ${MLFLOW_ARTIFACT_ROOT}"
fi

echo ""
echo "=== MLflow Tracking Server 시작 ==="
echo "다음 명령어로 서버를 시작하세요:"
echo ""
echo "mlflow server \\"
echo "  --backend-store-uri ${MLFLOW_BACKEND_STORE_URI} \\"
echo "  --default-artifact-root ${MLFLOW_ARTIFACT_ROOT} \\"
echo "  --host ${MLFLOW_HOST} \\"
echo "  --port ${MLFLOW_PORT}"
echo ""
echo "또는 백그라운드로 실행:"
echo ""
echo "nohup mlflow server \\"
echo "  --backend-store-uri ${MLFLOW_BACKEND_STORE_URI} \\"
echo "  --default-artifact-root ${MLFLOW_ARTIFACT_ROOT} \\"
echo "  --host ${MLFLOW_HOST} \\"
echo "  --port ${MLFLOW_PORT} > /tmp/mlflow.log 2>&1 &"
echo ""
echo "웹 UI 접근: http://192.168.0.147:5000"
