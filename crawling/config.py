"""
크롤링 설정 파일
"""
import os

# 데이터베이스 설정
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:xlxldpa%21%40%23@114.202.2.226:5433/mlops')

# 크롤링 설정
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
]

# 딜레이 설정 (초)
DELAY_MIN = 1
DELAY_MAX = 3

# 동시 요청 제한
CONCURRENT_REQUESTS = 5

# 재시도 설정
RETRY_TIMES = 3

# 시니어 관련 키워드
SENIOR_KEYWORDS = [
    '시니어', '50대', '60대', '경력직', '베테랑', 
    '50+', '60+', '중장년', '경험자', '숙련자',
    '은퇴자', '퇴직자', '재취업', '노인',
    '50세이상', '55세이상', '60세이상'
]

# 크롤링 대상 사이트
TARGET_SITES = {
    'saramin': {
        'base_url': 'https://www.saramin.co.kr',
        'job_search_url': 'https://www.saramin.co.kr/zf_user/jobs/list/job-category',
        'robots_url': 'https://www.saramin.co.kr/robots.txt'
    },
    'jobkorea': {
        'base_url': 'https://www.jobkorea.co.kr',
        'job_search_url': 'https://www.jobkorea.co.kr/recruit/joblist',
        'robots_url': 'https://www.jobkorea.co.kr/robots.txt'
    },
    'worknet': {
        'base_url': 'https://www.work.go.kr',
        'job_search_url': 'https://www.work.go.kr/empInfo/empInfoSrch/list/dtlEmpSrchList.do',
        'robots_url': 'https://www.work.go.kr/robots.txt'
    }
}

# 로깅 설정
LOG_LEVEL = 'INFO'
LOG_FILE = 'crawler.log'

# 출력 파일 설정
OUTPUT_DIR = 'data'
BACKUP_DIR = 'backup'

# 필터링 설정 - 시니어 적합 직무
SENIOR_FRIENDLY_CATEGORIES = [
    '경비보안', '청소', '시설관리', '운전', '배달',
    '상담', '텔레마케팅', '고객서비스', '판매',
    '교육', '강사', '컨설팅', '멘토링',
    '사무', '회계', '총무', '인사', '관리',
    '돌봄', '간병', '육아', '가사도우미'
]

# 제외할 키워드 (체력적으로 힘든 업무)
EXCLUDE_KEYWORDS = [
    '야간', '밤샘', '3교대', '새벽', '심야',
    '장시간', '고강도', '중량물', '위험',
    '신입', '경력무관', '20대', '30대', '청년'
]