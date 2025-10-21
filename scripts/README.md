# Scripts

이 폴더에는 프로젝트 관련 유틸리티 스크립트가 포함되어 있습니다.

## 파일 목록

### test.py
- **용도**: PostgreSQL 데이터베이스 연결 테스트 및 스키마 확인
- **기능**:
  - mlops 스키마 존재 여부 확인
  - mlops 테이블 구조 확인
  - 필요시 스키마 및 테이블 자동 생성
- **실행**:
  ```bash
  python scripts/test.py
  ```

### test_saramin_only.py
- **용도**: Saramin 크롤러 단독 테스트
- **기능**:
  - 트랜잭션 충돌 없이 Saramin 크롤러만 실행
  - DB 저장 결과 자동 확인
  - 크롤링 성능 측정
- **실행**:
  ```bash
  python scripts/test_saramin_only.py
  ```

### init_remote_db.py
- **용도**: 원격 데이터베이스 초기화
- **기능**:
  - mlops 스키마 생성
  - 필요한 테이블 생성
  - 인덱스 및 제약조건 설정
- **실행**:
  ```bash
  python scripts/init_remote_db.py
  ```

## 사용 가이드

### DB 연결 테스트
프로젝트를 처음 설정할 때 데이터베이스 연결을 확인하려면:
```bash
cd /home/ttm/tensorflow-jupyter/jupyterNotebook/khj/mlops-platform
python scripts/test.py
```

### 크롤러 테스트
Saramin 크롤러가 정상 작동하는지 확인하려면:
```bash
python scripts/test_saramin_only.py
```

### DB 초기화
새로운 환경에서 데이터베이스를 초기화하려면:
```bash
python scripts/init_remote_db.py
```
