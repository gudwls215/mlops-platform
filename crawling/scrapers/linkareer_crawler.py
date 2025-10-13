#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Linkareer 자기소개서 크롤러
장년층을 위한 자기소개서 샘플 데이터 수집
"""

import requests
from bs4 import BeautifulSoup
import time
import random
from urllib.parse import urljoin, parse_qs, urlparse
import json
import re
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager

class LinkareerCoverLetterCrawler:
    def __init__(self):
        self.base_url = "https://linkareer.com"
        self.cover_letter_url = "https://linkareer.com/cover-letter"
        
        # 세션 설정
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # 시니어 친화적 키워드
        self.senior_keywords = [
            '경력', '시니어', '책임', '매니저', '부장', '과장', '팀장', 
            '리더', '관리', '운영', '기획', '전략', '컨설팅', '멘토링',
            '10년', '15년', '20년', '25년', '30년', '경험', '전문',
            '노하우', '전문성', '숙련', '베테랑', '실무진', '핵심인재'
        ]
        
        # 데이터베이스 매니저
        self.db_manager = DatabaseManager()
        
    def get_cover_letter_list(self, page=1, max_pages=5):
        """자기소개서 목록 페이지 크롤링"""
        cover_letters = []
        
        for current_page in range(1, max_pages + 1):
            print(f"📄 자기소개서 목록 페이지 {current_page} 크롤링 중...")
            
            try:
                # 페이지 요청
                params = {'page': current_page}
                response = self.session.get(self.cover_letter_url, params=params, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # 자기소개서 아이템 찾기
                cover_letter_items = soup.find_all('div', class_='cover-letter-item') or \
                                   soup.find_all('article', class_='cover-letter') or \
                                   soup.find_all('div', class_='item') or \
                                   soup.select('.list-item, .card-item, .cover-letter-card')
                
                if not cover_letter_items:
                    # 다른 셀렉터 시도
                    cover_letter_items = soup.select('a[href*="cover-letter"]')
                
                print(f"  찾은 자기소개서 아이템: {len(cover_letter_items)}개")
                
                if not cover_letter_items:
                    print(f"  페이지 {current_page}에서 자기소개서를 찾을 수 없습니다.")
                    # HTML 구조 분석을 위한 샘플 출력
                    print("  페이지 HTML 샘플:")
                    print(response.text[:1000])
                    break
                
                # 각 아이템 처리
                for item in cover_letter_items:
                    try:
                        cover_letter_data = self.extract_cover_letter_preview(item)
                        if cover_letter_data and self.is_senior_friendly(cover_letter_data):
                            cover_letters.append(cover_letter_data)
                            print(f"  ✅ 시니어 친화적 자기소개서 발견: {cover_letter_data.get('title', 'N/A')[:50]}...")
                        
                        time.sleep(random.uniform(0.5, 1.0))
                        
                    except Exception as e:
                        print(f"  ❌ 아이템 처리 오류: {e}")
                        continue
                
                # 페이지 간 딜레이
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                print(f"❌ 페이지 {current_page} 크롤링 오류: {e}")
                continue
        
        print(f"📊 총 {len(cover_letters)}개의 시니어 친화적 자기소개서 발견")
        return cover_letters
    
    def extract_cover_letter_preview(self, item):
        """자기소개서 미리보기 정보 추출"""
        data = {}
        
        try:
            # URL 추출
            link = item.find('a') or item
            if link and link.get('href'):
                data['url'] = urljoin(self.base_url, link.get('href'))
            else:
                return None
            
            # 제목 추출
            title_selectors = [
                '.title', '.subject', '.cover-letter-title', 'h3', 'h4', 
                '.item-title', '.card-title', '[class*="title"]'
            ]
            
            for selector in title_selectors:
                title_elem = item.select_one(selector)
                if title_elem:
                    data['title'] = title_elem.get_text().strip()
                    break
            
            if not data.get('title'):
                # 링크 텍스트를 제목으로 사용
                if link and link.get_text():
                    data['title'] = link.get_text().strip()
            
            # 회사명 추출
            company_selectors = [
                '.company', '.company-name', '.corp', '[class*="company"]',
                '.info .company', '.meta .company'
            ]
            
            for selector in company_selectors:
                company_elem = item.select_one(selector)
                if company_elem:
                    data['company'] = company_elem.get_text().strip()
                    break
            
            # 직무/부서 추출
            position_selectors = [
                '.position', '.job', '.dept', '.department', '[class*="position"]',
                '.job-title', '.role'
            ]
            
            for selector in position_selectors:
                position_elem = item.select_one(selector)
                if position_elem:
                    data['position'] = position_elem.get_text().strip()
                    break
            
            # 메타 정보 추출
            meta_info = item.select('.meta, .info, .details')
            for meta in meta_info:
                text = meta.get_text()
                
                # 연도 추출
                year_match = re.search(r'20\d{2}', text)
                if year_match:
                    data['application_year'] = int(year_match.group())
                
                # 조회수 추출
                views_match = re.search(r'조회수?\s*(\d+)', text)
                if views_match:
                    data['views'] = int(views_match.group(1))
                
                # 좋아요 추출
                likes_match = re.search(r'좋아요\s*(\d+)', text)
                if likes_match:
                    data['likes'] = int(likes_match.group(1))
            
            # 합격 여부 추출
            pass_indicators = item.select('.pass, .success, [class*="pass"]')
            if pass_indicators:
                pass_text = ' '.join([elem.get_text() for elem in pass_indicators])
                data['is_passed'] = '합격' in pass_text or '최종합격' in pass_text
            
            return data
            
        except Exception as e:
            print(f"  ❌ 미리보기 추출 오류: {e}")
            return None
    
    def get_cover_letter_detail(self, url):
        """자기소개서 상세 내용 크롤링"""
        try:
            print(f"📝 상세 자기소개서 크롤링: {url}")
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 자기소개서 본문 추출
            content_selectors = [
                '.content', '.cover-letter-content', '.letter-content',
                '.main-content', '.body', '.description', '[class*="content"]'
            ]
            
            content = ""
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # 불필요한 요소 제거
                    for unwanted in content_elem.select('script, style, .ad, .advertisement'):
                        unwanted.decompose()
                    
                    content = content_elem.get_text().strip()
                    break
            
            if not content:
                # 전체 페이지에서 자기소개서 내용 추정
                all_text = soup.get_text()
                paragraphs = [p.strip() for p in all_text.split('\n') if len(p.strip()) > 50]
                if len(paragraphs) > 3:
                    content = '\n'.join(paragraphs[1:6])  # 상위 몇 개 단락 사용
            
            # 추가 메타데이터 추출
            meta_data = {}
            
            # 제목 재추출 (더 정확한)
            title_selectors = ['.title', 'h1', 'h2', '.main-title', '.cover-letter-title']
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    meta_data['title'] = title_elem.get_text().strip()
                    break
            
            # 키워드 추출
            keywords = self.extract_keywords(content)
            meta_data['keywords'] = keywords
            
            return content, meta_data
            
        except Exception as e:
            print(f"❌ 상세 크롤링 오류: {e}")
            return None, None
    
    def extract_keywords(self, content):
        """자기소개서 내용에서 키워드 추출"""
        keywords = []
        
        # 기본 키워드 리스트
        keyword_patterns = [
            # 기술 키워드
            r'\b(Python|Java|JavaScript|React|SQL|AWS|Docker|Kubernetes|Git|Linux)\b',
            # 업무 키워드  
            r'\b(기획|운영|관리|개발|설계|분석|마케팅|영업|인사|재무|회계)\b',
            # 경력 키워드
            r'\b(\d+년|경력|경험|전문|숙련|베테랑|시니어)\b',
            # 성과 키워드
            r'\b(성과|달성|개선|효율|절약|증가|향상|최적화)\b'
        ]
        
        for pattern in keyword_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            keywords.extend(matches)
        
        # 중복 제거 및 정리
        keywords = list(set([kw.strip() for kw in keywords if len(kw.strip()) > 1]))
        return keywords[:10]  # 상위 10개만
    
    def is_senior_friendly(self, cover_letter_data):
        """시니어 친화적 자기소개서인지 판단"""
        text_to_check = f"{cover_letter_data.get('title', '')} {cover_letter_data.get('company', '')} {cover_letter_data.get('position', '')}"
        
        # 시니어 키워드 확인
        for keyword in self.senior_keywords:
            if keyword in text_to_check:
                return True
        
        # 연도 기준 (최근 5년 이내)
        current_year = datetime.now().year
        app_year = cover_letter_data.get('application_year')
        if app_year and current_year - app_year <= 5:
            return True
        
        # 조회수 기준 (인기 있는 자기소개서)
        views = cover_letter_data.get('views', 0)
        if views > 100:
            return True
        
        return False
    
    def save_cover_letter(self, cover_letter_data, content):
        """자기소개서를 데이터베이스에 저장"""
        try:
            # 데이터 준비
            data = {
                'title': cover_letter_data.get('title', ''),
                'company': cover_letter_data.get('company', ''),
                'position': cover_letter_data.get('position'),
                'department': cover_letter_data.get('department'),
                'experience_level': cover_letter_data.get('experience_level'),
                'content': content or '',
                'is_passed': cover_letter_data.get('is_passed'),
                'application_year': cover_letter_data.get('application_year'),
                'keywords': cover_letter_data.get('keywords', []),
                'url': cover_letter_data.get('url'),
                'views': cover_letter_data.get('views', 0),
                'likes': cover_letter_data.get('likes', 0)
            }
            
            # 데이터베이스에 저장
            success = self.db_manager.insert_cover_letter_sample(data)
            
            if success:
                print(f"✅ 자기소개서 저장 성공: {data['title'][:50]}...")
                return True
            else:
                print(f"❌ 자기소개서 저장 실패: {data['title'][:50]}...")
                return False
                
        except Exception as e:
            print(f"❌ 저장 오류: {e}")
            return False
    
    def crawl_cover_letters(self, max_pages=3, max_details=20):
        """전체 자기소개서 크롤링 프로세스"""
        print("🚀 Linkareer 자기소개서 크롤링 시작")
        print("="*60)
        
        try:
            # 1. 목록 페이지 크롤링
            cover_letter_list = self.get_cover_letter_list(max_pages=max_pages)
            
            if not cover_letter_list:
                print("❌ 자기소개서 목록을 찾을 수 없습니다.")
                return
            
            # 2. 상세 페이지 크롤링 및 저장
            saved_count = 0
            
            for i, cover_letter_data in enumerate(cover_letter_list[:max_details]):
                print(f"\n📝 [{i+1}/{min(len(cover_letter_list), max_details)}] 상세 크롤링 중...")
                
                if not cover_letter_data.get('url'):
                    print("  URL이 없어 스킵합니다.")
                    continue
                
                # 상세 내용 크롤링
                content, meta_data = self.get_cover_letter_detail(cover_letter_data['url'])
                
                if content:
                    # 메타데이터 병합
                    if meta_data:
                        cover_letter_data.update(meta_data)
                    
                    # 데이터베이스에 저장
                    if self.save_cover_letter(cover_letter_data, content):
                        saved_count += 1
                
                # 딜레이 (서버 부하 방지)
                time.sleep(random.uniform(2, 4))
            
            print(f"\n🎉 크롤링 완료!")
            print(f"📊 총 발견: {len(cover_letter_list)}개")
            print(f"💾 저장 성공: {saved_count}개")
            
        except Exception as e:
            print(f"❌ 크롤링 중 오류 발생: {e}")

def main():
    """메인 실행 함수"""
    crawler = LinkareerCoverLetterCrawler()
    
    # 크롤링 실행 (테스트용으로 소량)
    crawler.crawl_cover_letters(max_pages=2, max_details=5)

if __name__ == "__main__":
    main()