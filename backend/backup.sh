#!/bin/bash
#
# 백업 스크립트 - 데이터베이스 및 업로드 파일 백업
# Backup Script - PostgreSQL Database and Upload Files
#

set -e

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 백업 설정
BACKUP_DIR="/var/mlops/backups"
RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# .env.production에서 환경 변수 로드
if [ -f .env.production ]; then
    source .env.production
else
    echo -e "${RED}Error: .env.production file not found${NC}"
    exit 1
fi

# 백업 디렉토리 생성
mkdir -p "${BACKUP_DIR}/database"
mkdir -p "${BACKUP_DIR}/uploads"

echo "========================================="
echo "MLOps Platform Backup Script"
echo "========================================="

# Step 1: 데이터베이스 백업
echo -e "\n${YELLOW}[1/4] Backing up database...${NC}"

# PostgreSQL 연결 정보 파싱
DB_HOST=$(echo $DATABASE_HOST)
DB_PORT=$(echo $DATABASE_PORT)
DB_NAME=$(echo $DATABASE_NAME)
DB_USER=$(echo $DATABASE_USER)
DB_PASSWORD=$(echo $DATABASE_PASSWORD)

# 백업 파일명
DB_BACKUP_FILE="${BACKUP_DIR}/database/mlops_db_${TIMESTAMP}.sql"
DB_BACKUP_COMPRESSED="${DB_BACKUP_FILE}.gz"

# PostgreSQL 백업 (pg_dump 사용)
export PGPASSWORD="${DB_PASSWORD}"

if pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
    --no-owner --no-acl --clean --if-exists \
    > "${DB_BACKUP_FILE}"; then
    
    # 압축
    gzip "${DB_BACKUP_FILE}"
    
    # 백업 크기 확인
    BACKUP_SIZE=$(du -h "${DB_BACKUP_COMPRESSED}" | cut -f1)
    echo -e "${GREEN}✓ Database backup completed: ${DB_BACKUP_COMPRESSED} (${BACKUP_SIZE})${NC}"
else
    echo -e "${RED}✗ Database backup failed${NC}"
    exit 1
fi

unset PGPASSWORD

# Step 2: 업로드 파일 백업
echo -e "\n${YELLOW}[2/4] Backing up upload files...${NC}"

UPLOAD_DIR="/var/mlops/uploads"
UPLOAD_BACKUP="${BACKUP_DIR}/uploads/uploads_${TIMESTAMP}.tar.gz"

if [ -d "${UPLOAD_DIR}" ]; then
    # 업로드 디렉토리가 비어있지 않으면 백업
    if [ "$(ls -A ${UPLOAD_DIR})" ]; then
        tar -czf "${UPLOAD_BACKUP}" -C "${UPLOAD_DIR}" .
        
        UPLOAD_SIZE=$(du -h "${UPLOAD_BACKUP}" | cut -f1)
        echo -e "${GREEN}✓ Upload files backup completed: ${UPLOAD_BACKUP} (${UPLOAD_SIZE})${NC}"
    else
        echo -e "${YELLOW}  No files to backup in ${UPLOAD_DIR}${NC}"
    fi
else
    echo -e "${YELLOW}  Upload directory does not exist: ${UPLOAD_DIR}${NC}"
fi

# Step 3: 백업 메타데이터 저장
echo -e "\n${YELLOW}[3/4] Saving backup metadata...${NC}"

METADATA_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.json"

cat > "${METADATA_FILE}" <<EOF
{
    "timestamp": "${TIMESTAMP}",
    "date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "database": {
        "file": "${DB_BACKUP_COMPRESSED}",
        "size": "${BACKUP_SIZE}",
        "host": "${DB_HOST}",
        "name": "${DB_NAME}"
    },
    "uploads": {
        "file": "${UPLOAD_BACKUP}",
        "size": "${UPLOAD_SIZE}"
    },
    "environment": "${ENVIRONMENT}",
    "version": "$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
}
EOF

echo -e "${GREEN}✓ Metadata saved: ${METADATA_FILE}${NC}"

# Step 4: 오래된 백업 정리
echo -e "\n${YELLOW}[4/4] Cleaning up old backups (older than ${RETENTION_DAYS} days)...${NC}"

# 데이터베이스 백업 정리
DELETED_DB=0
if [ -d "${BACKUP_DIR}/database" ]; then
    DELETED_DB=$(find "${BACKUP_DIR}/database" -name "*.sql.gz" -mtime +${RETENTION_DAYS} -delete -print | wc -l)
fi

# 업로드 백업 정리
DELETED_UPLOADS=0
if [ -d "${BACKUP_DIR}/uploads" ]; then
    DELETED_UPLOADS=$(find "${BACKUP_DIR}/uploads" -name "*.tar.gz" -mtime +${RETENTION_DAYS} -delete -print | wc -l)
fi

# 메타데이터 정리
DELETED_METADATA=0
DELETED_METADATA=$(find "${BACKUP_DIR}" -maxdepth 1 -name "backup_*.json" -mtime +${RETENTION_DAYS} -delete -print | wc -l)

echo -e "${GREEN}✓ Cleanup completed:${NC}"
echo "  - Database backups deleted: ${DELETED_DB}"
echo "  - Upload backups deleted: ${DELETED_UPLOADS}"
echo "  - Metadata files deleted: ${DELETED_METADATA}"

# 백업 통계
echo -e "\n========================================="
echo "Backup Statistics"
echo "========================================="

TOTAL_DB_BACKUPS=$(find "${BACKUP_DIR}/database" -name "*.sql.gz" 2>/dev/null | wc -l)
TOTAL_UPLOAD_BACKUPS=$(find "${BACKUP_DIR}/uploads" -name "*.tar.gz" 2>/dev/null | wc -l)
TOTAL_SIZE=$(du -sh "${BACKUP_DIR}" 2>/dev/null | cut -f1)

echo "Total database backups: ${TOTAL_DB_BACKUPS}"
echo "Total upload backups: ${TOTAL_UPLOAD_BACKUPS}"
echo "Total backup size: ${TOTAL_SIZE}"
echo "Backup directory: ${BACKUP_DIR}"

echo -e "\n${GREEN}✓ Backup completed successfully!${NC}"

# 최신 백업 정보 출력
echo -e "\nLatest backup files:"
echo "  Database: ${DB_BACKUP_COMPRESSED}"
echo "  Uploads: ${UPLOAD_BACKUP}"
echo "  Metadata: ${METADATA_FILE}"

# 복구 명령어 힌트
echo -e "\n${YELLOW}To restore this backup:${NC}"
echo "  Database: gunzip -c ${DB_BACKUP_COMPRESSED} | psql -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} -d ${DB_NAME}"
echo "  Uploads: tar -xzf ${UPLOAD_BACKUP} -C ${UPLOAD_DIR}"
