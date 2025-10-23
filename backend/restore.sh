#!/bin/bash
#
# 복구 스크립트 - 백업에서 데이터베이스 및 파일 복구
# Restore Script - Restore database and files from backup
#

set -e

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 백업 설정
BACKUP_DIR="/var/mlops/backups"

# .env.production에서 환경 변수 로드
if [ -f .env.production ]; then
    source .env.production
else
    echo -e "${RED}Error: .env.production file not found${NC}"
    exit 1
fi

echo "========================================="
echo "MLOps Platform Restore Script"
echo "========================================="

# 인자 확인
if [ $# -eq 0 ]; then
    echo -e "\n${YELLOW}Available backups:${NC}"
    echo ""
    
    # 백업 메타데이터 파일 목록
    METADATA_FILES=$(find "${BACKUP_DIR}" -maxdepth 1 -name "backup_*.json" -type f | sort -r)
    
    if [ -z "${METADATA_FILES}" ]; then
        echo -e "${RED}No backups found in ${BACKUP_DIR}${NC}"
        exit 1
    fi
    
    # 백업 목록 출력
    INDEX=1
    declare -A BACKUP_MAP
    
    for metadata in ${METADATA_FILES}; do
        TIMESTAMP=$(jq -r '.timestamp' "${metadata}")
        DATE=$(jq -r '.date' "${metadata}")
        DB_SIZE=$(jq -r '.database.size' "${metadata}")
        
        echo "${INDEX}. Backup from ${DATE} (${TIMESTAMP})"
        echo "   Database size: ${DB_SIZE}"
        
        BACKUP_MAP[$INDEX]="${TIMESTAMP}"
        INDEX=$((INDEX + 1))
    done
    
    echo ""
    echo -e "${YELLOW}Usage:${NC}"
    echo "  $0 <backup_timestamp>         # Restore specific backup"
    echo "  $0 latest                     # Restore latest backup"
    echo ""
    echo -e "${YELLOW}Example:${NC}"
    echo "  $0 20240115_143022"
    echo "  $0 latest"
    exit 0
fi

# 백업 타임스탬프 결정
BACKUP_TIMESTAMP=$1

if [ "${BACKUP_TIMESTAMP}" = "latest" ]; then
    # 최신 백업 찾기
    LATEST_METADATA=$(find "${BACKUP_DIR}" -maxdepth 1 -name "backup_*.json" -type f | sort -r | head -1)
    
    if [ -z "${LATEST_METADATA}" ]; then
        echo -e "${RED}No backups found${NC}"
        exit 1
    fi
    
    BACKUP_TIMESTAMP=$(jq -r '.timestamp' "${LATEST_METADATA}")
    echo -e "${GREEN}Using latest backup: ${BACKUP_TIMESTAMP}${NC}"
fi

# 백업 파일 경로
METADATA_FILE="${BACKUP_DIR}/backup_${BACKUP_TIMESTAMP}.json"
DB_BACKUP_FILE="${BACKUP_DIR}/database/mlops_db_${BACKUP_TIMESTAMP}.sql.gz"
UPLOAD_BACKUP_FILE="${BACKUP_DIR}/uploads/uploads_${BACKUP_TIMESTAMP}.tar.gz"

# 메타데이터 파일 확인
if [ ! -f "${METADATA_FILE}" ]; then
    echo -e "${RED}Error: Backup metadata not found: ${METADATA_FILE}${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Backup Information:${NC}"
jq '.' "${METADATA_FILE}"

# 확인 메시지
echo ""
echo -e "${RED}WARNING: This will overwrite the current database and files!${NC}"
read -p "Are you sure you want to restore this backup? (yes/no): " CONFIRM

if [ "${CONFIRM}" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

# PostgreSQL 연결 정보
DB_HOST=$(echo $DATABASE_HOST)
DB_PORT=$(echo $DATABASE_PORT)
DB_NAME=$(echo $DATABASE_NAME)
DB_USER=$(echo $DATABASE_USER)
DB_PASSWORD=$(echo $DATABASE_PASSWORD)

# Step 1: 데이터베이스 복구
echo -e "\n${YELLOW}[1/2] Restoring database...${NC}"

if [ ! -f "${DB_BACKUP_FILE}" ]; then
    echo -e "${RED}Error: Database backup file not found: ${DB_BACKUP_FILE}${NC}"
    exit 1
fi

export PGPASSWORD="${DB_PASSWORD}"

# 데이터베이스 연결 종료
echo "  Terminating existing connections..."
psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres <<EOF >/dev/null 2>&1 || true
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = '${DB_NAME}'
  AND pid <> pg_backend_pid();
EOF

# 데이터베이스 복구
echo "  Restoring database from backup..."
if gunzip -c "${DB_BACKUP_FILE}" | psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Database restored successfully${NC}"
else
    echo -e "${RED}✗ Database restore failed${NC}"
    unset PGPASSWORD
    exit 1
fi

unset PGPASSWORD

# Step 2: 업로드 파일 복구
echo -e "\n${YELLOW}[2/2] Restoring upload files...${NC}"

UPLOAD_DIR="/var/mlops/uploads"

if [ -f "${UPLOAD_BACKUP_FILE}" ]; then
    # 기존 파일 백업
    if [ -d "${UPLOAD_DIR}" ] && [ "$(ls -A ${UPLOAD_DIR})" ]; then
        TEMP_BACKUP="${UPLOAD_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
        echo "  Backing up existing files to ${TEMP_BACKUP}..."
        mv "${UPLOAD_DIR}" "${TEMP_BACKUP}"
    fi
    
    # 디렉토리 생성
    mkdir -p "${UPLOAD_DIR}"
    
    # 파일 복구
    echo "  Extracting upload files..."
    if tar -xzf "${UPLOAD_BACKUP_FILE}" -C "${UPLOAD_DIR}"; then
        FILE_COUNT=$(find "${UPLOAD_DIR}" -type f | wc -l)
        echo -e "${GREEN}✓ Upload files restored: ${FILE_COUNT} files${NC}"
    else
        echo -e "${RED}✗ Upload file restore failed${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}  No upload backup file found: ${UPLOAD_BACKUP_FILE}${NC}"
fi

# 복구 완료
echo -e "\n========================================="
echo -e "${GREEN}✓ Restore completed successfully!${NC}"
echo "========================================="

echo ""
echo "Restored from backup: ${BACKUP_TIMESTAMP}"
echo "Database: ${DB_BACKUP_FILE}"
echo "Uploads: ${UPLOAD_BACKUP_FILE}"

echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Restart the application"
echo "2. Verify the restored data"
echo "3. Check application logs"
