# Airflow 설정 가이드

## 설정 완료 내역

### 1. DAG 파일 위치
- 파일 경로: `/home/ttm/airflow/dags/data_collection_dag.py`
- DAG ID: `data_collection_pipeline`

### 2. 스케줄링 설정
- 실행 시간: 매일 새벽 2시 (0 2 * * *)
- 재시도: 2회 (5분 간격)

### 3. DAG 구조
```
사람인 크롤러 ──┐
                ├──► 데이터 처리 ──► 일일 리포트
Linkareer 크롤러 ──┘
```

### 4. 태스크 목록
1. `run_saramin_crawler`: 사람인 채용공고 크롤링
2. `run_linkareer_crawler`: Linkareer 자기소개서 크롤링  
3. `run_data_processing`: HTML 정제, 중복 제거, 데이터 검증
4. `generate_daily_report`: 일일 수집 현황 리포트 생성

### 5. 웹 UI 접근
- URL: http://localhost:8080
- DAG 이름: data_collection_pipeline

### 6. 수동 실행 방법
```bash
cd /home/ttm/tensorflow-jupyter/jupyterNotebook/khj/movielens-mlops
source movielens_env/bin/activate
airflow dags trigger data_collection_pipeline
```

### 7. 로그 확인
- Airflow 웹 UI > DAGs > data_collection_pipeline > Graph/Tree View
- 각 태스크 클릭하여 실행 로그 확인 가능

### 8. 주의사항
- 크롤러 실행 시간: 최대 30분 (타임아웃)
- 데이터 처리 시간: 최대 1시간 (타임아웃)
- 실패 시 자동 재시도 2회 실행

### 9. 모니터링
- 웹 UI에서 실시간 실행 상태 확인 가능
- 일일 리포트를 통한 데이터 수집 현황 파악
- 실패 태스크 개별 재실행 가능