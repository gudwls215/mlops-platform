"""
기본 크롤러 클래스
"""
import asyncio
import logging
import random
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from urllib.robotparser import RobotFileParser

import aiohttp
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from config import USER_AGENTS, DELAY_MIN, DELAY_MAX, RETRY_TIMES


class BaseCrawler(ABC):
    """기본 크롤러 추상 클래스"""
    
    def __init__(self, site_name: str, base_url: str, robots_url: str):
        self.site_name = site_name
        self.base_url = base_url
        self.robots_url = robots_url
        self.session = None
        self.robots_parser = None
        
        # 로깅 설정
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('crawler.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(f"{self.__class__.__name__}_{site_name}")
        
    def check_robots_txt(self, url: str) -> bool:
        """robots.txt 준수 확인"""
        try:
            if not self.robots_parser:
                self.robots_parser = RobotFileParser()
                self.robots_parser.set_url(self.robots_url)
                self.robots_parser.read()
            
            user_agent = random.choice(USER_AGENTS)
            can_fetch = self.robots_parser.can_fetch(user_agent, url)
            
            if not can_fetch:
                self.logger.warning(f"robots.txt에 의해 차단된 URL: {url}")
            
            return can_fetch
            
        except Exception as e:
            self.logger.error(f"robots.txt 확인 중 오류: {e}")
            return True  # 오류 시 허용
    
    def get_random_delay(self) -> float:
        """랜덤 딜레이 생성"""
        return random.uniform(DELAY_MIN, DELAY_MAX)
    
    def get_random_user_agent(self) -> str:
        """랜덤 User-Agent 선택"""
        return random.choice(USER_AGENTS)
    
    @abstractmethod
    def parse_job_listing(self, html: str) -> List[Dict]:
        """채용 공고 파싱 (추상 메서드)"""
        pass
    
    @abstractmethod
    def get_job_urls(self, category: str = None) -> List[str]:
        """채용 공고 URL 목록 가져오기 (추상 메서드)"""
        pass


class RequestsCrawler(BaseCrawler):
    """Requests 기반 크롤러"""
    
    def __init__(self, site_name: str, base_url: str, robots_url: str):
        super().__init__(site_name, base_url, robots_url)
        self.session = requests.Session()
    
    def fetch_page(self, url: str, max_retries: int = RETRY_TIMES) -> Optional[str]:
        """페이지 내용 가져오기"""
        if not self.check_robots_txt(url):
            return None
        
        for attempt in range(max_retries):
            try:
                headers = {
                    'User-Agent': self.get_random_user_agent(),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                }
                
                response = self.session.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                
                # 딜레이 적용
                time.sleep(self.get_random_delay())
                
                self.logger.info(f"페이지 가져오기 성공: {url}")
                return response.text
                
            except Exception as e:
                self.logger.warning(f"페이지 가져오기 실패 (시도 {attempt + 1}/{max_retries}): {url} - {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 지수 백오프
        
        self.logger.error(f"모든 재시도 실패: {url}")
        return None


class AsyncCrawler(BaseCrawler):
    """비동기 크롤러"""
    
    def __init__(self, site_name: str, base_url: str, robots_url: str):
        super().__init__(site_name, base_url, robots_url)
        self.session = None
    
    async def create_session(self):
        """비동기 세션 생성"""
        if not self.session:
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            )
    
    async def close_session(self):
        """세션 종료"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def fetch_page_async(self, url: str, max_retries: int = RETRY_TIMES) -> Optional[str]:
        """비동기 페이지 가져오기"""
        if not self.check_robots_txt(url):
            return None
        
        await self.create_session()
        
        for attempt in range(max_retries):
            try:
                headers = {
                    'User-Agent': self.get_random_user_agent(),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
                }
                
                async with self.session.get(url, headers=headers) as response:
                    response.raise_for_status()
                    content = await response.text()
                    
                    # 비동기 딜레이
                    await asyncio.sleep(self.get_random_delay())
                    
                    self.logger.info(f"페이지 가져오기 성공: {url}")
                    return content
                    
            except Exception as e:
                self.logger.warning(f"페이지 가져오기 실패 (시도 {attempt + 1}/{max_retries}): {url} - {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
        
        self.logger.error(f"모든 재시도 실패: {url}")
        return None


class SeleniumCrawler(BaseCrawler):
    """Selenium 기반 크롤러 (동적 페이지용)"""
    
    def __init__(self, site_name: str, base_url: str, robots_url: str):
        super().__init__(site_name, base_url, robots_url)
        self.driver = None
    
    def create_driver(self):
        """Chrome 드라이버 생성"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument(f'--user-agent={self.get_random_user_agent()}')
        
        try:
            from selenium.webdriver.chrome.service import Service
            # Chrome 드라이버 자동 설치
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
        except ImportError:
            # webdriver_manager가 없는 경우 기본 방식
            self.driver = webdriver.Chrome(options=options)
        
        self.driver.implicitly_wait(10)
    
    def fetch_page_selenium(self, url: str, wait_seconds: int = 3) -> Optional[str]:
        """Selenium으로 페이지 가져오기"""
        if not self.check_robots_txt(url):
            return None
        
        try:
            if not self.driver:
                self.create_driver()
            
            self.driver.get(url)
            time.sleep(wait_seconds)  # 페이지 로딩 대기
            
            # 딜레이 적용
            time.sleep(self.get_random_delay())
            
            self.logger.info(f"Selenium 페이지 가져오기 성공: {url}")
            return self.driver.page_source
            
        except Exception as e:
            self.logger.error(f"Selenium 페이지 가져오기 실패: {url} - {e}")
            return None
    
    def close_driver(self):
        """드라이버 종료"""
        if self.driver:
            self.driver.quit()
            self.driver = None


class JobCrawlerUtils:
    """채용 공고 크롤링 유틸리티"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """텍스트 정리"""
        if not text:
            return ""
        
        # 불필요한 공백, 줄바꿈 제거
        text = " ".join(text.split())
        return text.strip()
    
    @staticmethod
    def extract_salary(text: str) -> Optional[str]:
        """급여 정보 추출"""
        import re
        
        # 급여 관련 패턴
        salary_patterns = [
            r'(\d{1,3}(?:,\d{3})*)\s*~\s*(\d{1,3}(?:,\d{3})*)\s*만원',
            r'(\d{1,3}(?:,\d{3})*)\s*만원',
            r'시급\s*(\d{1,3}(?:,\d{3})*)\s*원',
            r'월급\s*(\d{1,3}(?:,\d{3})*)\s*만원',
            r'연봉\s*(\d{1,3}(?:,\d{3})*)\s*만원',
        ]
        
        for pattern in salary_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        
        return None
    
    @staticmethod
    def is_senior_friendly(job_data: Dict) -> bool:
        """시니어 친화적 채용공고인지 판단"""
        from config import SENIOR_KEYWORDS, EXCLUDE_KEYWORDS, SENIOR_FRIENDLY_CATEGORIES
        
        # 텍스트 합치기
        text_content = " ".join([
            job_data.get('title', ''),
            job_data.get('company', ''),
            job_data.get('description', ''),
            job_data.get('requirements', ''),
            job_data.get('qualifications', ''),
            job_data.get('preferences', ''),
            job_data.get('main_duties', ''),
            job_data.get('category', ''),
        ]).lower()
        
        # 시니어 키워드 포함 확인
        senior_score = sum(1 for keyword in SENIOR_KEYWORDS if keyword in text_content)
        
        # 제외 키워드 확인
        exclude_score = sum(1 for keyword in EXCLUDE_KEYWORDS if keyword in text_content)
        
        # 시니어 친화적 카테고리 확인
        category_score = sum(1 for category in SENIOR_FRIENDLY_CATEGORIES 
                           if category in text_content)
        
        # 점수 계산 (시니어 키워드 + 카테고리 점수 - 제외 키워드)
        total_score = senior_score + category_score - (exclude_score * 2)
        
        return total_score > 0