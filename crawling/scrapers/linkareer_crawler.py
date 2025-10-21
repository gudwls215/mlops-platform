#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Linkareer 자기소개서 크롤러
장년층을 위한 자기소개서 샘플 데이터 수집
"""

import asyncio
import random
import re
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

from database import DatabaseManager

class LinkareerCoverLetterCrawler:
    def __init__(self):
        self.base_url = "https://linkareer.com"
        self.cover_letter_url = "https://linkareer.com/cover-letter/search"
        
        # 데이터베이스 매니저
        self.db_manager = DatabaseManager()
        
        

    # --- 2단계: 상세 페이지에서 정보를 추출하는 함수  ---
    async def scrape_detail_page(self, page, url):
        """
        개별 자소서 URL에 접속하여 상세 정보를 추출하는 함수
        
        이 함수가 하는 일:
        1. 주어진 URL(자소서 페이지)에 접속
        2. HTML에서 회사명, 직무, 합격스펙, 자소서 내용을 찾아서 가져옴
        3. 데이터를 깔끔하게 정리해서 반환
        
        매개변수:
            page: 웹 브라우저 페이지 객체
            url: 방문할 자소서 페이지 주소
        
        반환값:
            딕셔너리 형태의 자소서 정보 (회사, 직무, 스펙, 자소서 내용 등)
        """
        print(f"  > 상세 페이지 분석 중... {url}")
        try:
            # 웹페이지 접속 (최대 20초 대기)
            await page.goto(url, wait_until='domcontentloaded', timeout=20000)
            
            # HTML에서 기본 정보 추출 (회사/직무/시기)
            basic_info_text = await page.locator('h1.basic-info').first.inner_text()
            parts = [p.strip() for p in basic_info_text.split('/')]  # '/'로 나누어서 정리
            company = parts[0] if len(parts) > 0 else ''  # 회사명
            role = parts[1] if len(parts) > 1 else ''     # 직무
            period = parts[2] if len(parts) > 2 else ''   # 시기

            # 합격스펙 정보 가져오기 (학점, 어학점수 등)
            spec_info_text = await page.locator('h3.spec-info').first.inner_text()
            
            # 자기소개서 본문 가져오기
            cover_letter_content = await page.locator('main.dwBPHz').first.inner_text()
            
            # 특수문자 제거 (컴퓨터가 읽기 어려운 문자들)
            clean_cover_letter = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', cover_letter_content)
            
            # 데이터베이스 저장 형식에 맞게 변환
            cover_letter_data = {
                'title': f"{company} {role} ({period})",
                'company': company,
                'position': role,
                'application_period': period,
                'spec': spec_info_text,
                'content': clean_cover_letter,
                'url': url,
                'application_year': self.extract_year_from_period(period)
            }
            
            return cover_letter_data
            
        except Exception as e:
            # 오류가 발생하면 에러 메시지 출력하고 None 반환
            print(f"  [오류] 상세 페이지 처리 실패: {url}, 원인: {e}")
            return None
    
    def extract_year_from_period(self, period):
        """시기 문자열에서 연도 추출"""
        try:
            year_match = re.search(r'20\d{2}', period)
            if year_match:
                return int(year_match.group())
            return datetime.now().year
        except:
            return datetime.now().year

    # --- 1단계: 링크 수집 함수 ---
    async def get_all_data_and_save_to_excel(self, start_page, end_page):
        """
        링커리어에서 자소서 링크들을 수집하고 상세 정보를 가져오는 메인 함수
        
        이 함수가 하는 일:
        1. 지정된 페이지 범위에서 자소서 링크들을 모음
        2. 각 링크에 들어가서 상세 정보를 수집
        3. 모든 데이터를 리스트로 정리해서 반환
        
        매개변수:
            start_page: 시작할 페이지 번호 (예: 1)
            end_page: 끝낼 페이지 번호 (예: 10)
        
        반환값:
            모든 자소서 데이터가 담긴 리스트
        """
        all_links = []        # 수집한 모든 링크를 저장할 리스트
        detailed_data = []    # 상세 정보를 저장할 리스트

        # Playwright로 웹 브라우저 실행
        async with async_playwright() as p:
            # 크롬 브라우저를 headless 모드로 실행 (화면에 안 보이게)
            browser = await p.chromium.launch(headless=True)
            
            # 사용자 에이전트 설정 (봇이 아닌 일반 브라우저처럼 보이게)
            context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            page = await context.new_page()

            # 지정된 페이지 범위만큼 반복
            for i in range(start_page, end_page + 1):
                print(f"\n[INFO] {i}페이지 링크 수집 시작...")
                try: 
                    # 링커리어 자소서 검색 페이지로 이동
                    target_url = f"https://linkareer.com/cover-letter/search?page={i}&tab=all"
                    await page.goto(target_url, wait_until='networkidle', timeout=30000)
                    await page.wait_for_timeout(1000) # 페이지 로드 후 1초 대기 (안정성을 위해)
                    print(f"[SUCCESS] {i}페이지가 완전히 로드되었습니다.")
                    
                    # 페이지에서 모든 자소서 링크를 찾아서 가져옴
                    found_links = await page.eval_on_selector_all(
                        'a.link',  # CSS 선택자: class가 'link'인 모든 <a> 태그
                        'elements => elements.map(el => el.getAttribute("href"))'  # href 속성값 추출
                    )
                    
                    # 각 링크를 확인하고 중복되지 않으면 리스트에 추가
                    for href in found_links:
                        # 상대경로면 절대경로로 변환
                        link = "https://linkareer.com" + href if href.startswith('/') else href
                        # 자소서 링크이고 아직 없는 링크면 추가
                        if '/cover-letter/' in link and link not in all_links:
                            all_links.append(link)
                
                # 페이지 로딩 시간이 너무 오래 걸리면
                except PlaywrightTimeoutError:
                    print(f"[ERROR] {i}페이지 로딩 시간 초과. 다음 페이지로 넘어갑니다.")
                    continue  # 이 페이지는 건너뛰고 다음 페이지로
                
                # 그 외 다른 오류가 발생하면
                except Exception as e:
                    print(f"[ERROR] {i}페이지 처리 중 오류 발생: {e}")
                    print("마지막 페이지에 도달했거나 페이지 이동 중 문제가 발생하여 수집을 중단합니다.")
                    break  # 반복문 종료
            
            print(f"\n--- [1단계 완료] 총 {len(all_links)}개의 고유 링크 수집 완료 ---")
            
            print("\n--- [2단계 시작] 상세 정보 크롤링을 시작합니다. ---")
            # 수집한 모든 링크에 대해 상세 정보 가져오기
            saved_count = 0
            for i, link in enumerate(all_links):
                print(f"[{i+1}/{len(all_links)}] 처리 중: {link}")
                data = await self.scrape_detail_page(page, link)
                if data:  # 정상적으로 데이터를 가져왔으면
                    detailed_data.append(data)
                    # 바로 데이터베이스에 저장
                    if self.save_cover_letter(data, data.get('content', '')):
                        saved_count += 1
                        print(f"    ✅ 저장 성공: {data.get('title', 'Unknown')[:50]}...")
                    else:
                        print(f"    ❌ 저장 실패: {data.get('title', 'Unknown')[:50]}...")
                
                # 딜레이 (서버 부하 방지) 
                await page.wait_for_timeout(random.randint(2000, 4000))
            
            await browser.close()  # 브라우저 종료
            
            print(f"\n🎉 크롤링 완료!")
            print(f"📊 총 발견: {len(all_links)}개")
            print(f"💾 저장 성공: {saved_count}개")
            
        return detailed_data


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
                'content': content or cover_letter_data.get('content', ''),
                'is_passed': cover_letter_data.get('is_passed'),
                'application_year': cover_letter_data.get('application_year'),
                'application_period': cover_letter_data.get('application_period'),
                'company_type': cover_letter_data.get('company_type'),
                'spec': cover_letter_data.get('spec'),
                'keywords': cover_letter_data.get('keywords', []),
                'url': cover_letter_data.get('url'),
                'scrap_count': cover_letter_data.get('scrap_count', 0),
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
    


    async def crawl_cover_letters_playwright(self, max_pages=3):
        """Playwright를 사용한 전체 자기소개서 크롤링 프로세스"""
        print("🚀 Linkareer 자기소개서 크롤링 시작 (Playwright 방식)")
        print("="*60)
        
        try:
            # get_all_data_and_save_to_excel을 사용하여 크롤링
            detailed_data = await self.get_all_data_and_save_to_excel(1, max_pages)
            
            print(f"\n🎉 Playwright 크롤링 완료!")
            print(f"📊 총 수집: {len(detailed_data)}개")
            
            return detailed_data
            
        except Exception as e:
            print(f"❌ Playwright 크롤링 중 오류 발생: {e}")
            print("⚠️ 네트워크 연결을 확인하고 다시 시도해주세요.")
            return []

    def crawl(self, max_items=50):
        """DAG에서 호출하는 인터페이스 메서드"""
        try:
            print(f"🚀 Linkareer 크롤링 시작 (최대 {max_items}개, Playwright 방식)")
            
            # max_items를 기반으로 페이지 수 계산
            max_pages = max(1, max_items // 10)  # 페이지당 약 10개 가정
            
            # asyncio를 사용하여 비동기 크롤링 실행
            detailed_data = asyncio.run(self.crawl_cover_letters_playwright(max_pages=max_pages))
            
            # 결과 반환
            return {
                "status": "completed", 
                "message": f"크롤링 완료 - {len(detailed_data)}개 수집",
                "data_count": len(detailed_data)
            }
            
        except Exception as e:
            print(f"❌ 크롤링 오류: {e}")
            return {"status": "failed", "message": str(e)}

def main():
    """메인 실행 함수"""
    print("🚀 Linkareer 크롤러 시작")
    print("="*50)
    
    try:
        crawler = LinkareerCoverLetterCrawler()
        
        # 크롤링 실행 (Playwright 방식)
        print("\n📋 크롤링 시작...")
        result = crawler.crawl(max_items=20)
        print(f"결과: {result}")
        
    except KeyboardInterrupt:
        print("\n⚠️ 사용자에 의해 중단됨")
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        print("⚠️ 크롤링을 재시도하거나 나중에 다시 시도해주세요.")
    
    print("\n🏁 크롤러 종료")

if __name__ == "__main__":
    main()