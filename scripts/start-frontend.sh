#!/bin/bash

# React 개발 서버 안정적 실행 스크립트
# 메모리 최적화 및 자동 재시작 기능

FRONTEND_DIR="/home/ttm/tensorflow-jupyter/jupyterNotebook/khj/mlops-platform/frontend"
LOG_FILE="/tmp/frontend.log"
PID_FILE="/tmp/frontend.pid"

# 기존 프로세스 정리
echo "기존 React 프로세스 정리..."
pkill -f "react-scripts start" 2>/dev/null
lsof -ti:9001 | xargs -r kill -9 2>/dev/null
sleep 3

# 환경 변수 설정 (메모리 최적화)
export NODE_OPTIONS="--max-old-space-size=4096"  # 4GB 메모리 제한
export CHOKIDAR_USEPOLLING=false  # 파일 감시 최적화
export FAST_REFRESH=true  # Fast Refresh 활성화
export GENERATE_SOURCEMAP=false  # 소스맵 비활성화로 메모리 절약

cd "$FRONTEND_DIR"

echo "React 서버 시작 중..."
echo "로그 파일: $LOG_FILE"

# nohup으로 백그라운드 실행
nohup npm start > "$LOG_FILE" 2>&1 &
REACT_PID=$!

# PID 저장
echo $REACT_PID > "$PID_FILE"

echo "React 서버 시작됨 (PID: $REACT_PID)"
echo "상태 확인 중..."

# 30초 대기 후 상태 확인
sleep 30

if ps -p $REACT_PID > /dev/null; then
    echo "✅ React 서버 정상 실행 중"
    tail -10 "$LOG_FILE"
else
    echo "❌ React 서버 시작 실패"
    echo "로그 내용:"
    tail -20 "$LOG_FILE"
    exit 1
fi