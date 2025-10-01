"""
사람인 크롤러
"""
import re
import urllib.parse
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

from base_crawler import RequestsCrawler, JobCrawlerUtils
from config import TARGET_SITES, SENIOR_KEYWORDS


class SaraminCrawler(RequestsCrawler):
    """사람인 채용공고 크롤러"""
    
    def __init__(self):
        site_config = TARGET_SITES['saramin']
        super().__init__('saramin', site_config['base_url'], site_config['robots_url'])
        self.job_search_url = site_config['job_search_url']
    
    def get_job_urls(self, category: str = None, page_limit: int = 5) -> List[str]:
        """채용공고 URL 목록 가져오기"""
        job_urls = []
        
        # 시니어 관련 키워드로 검색
        for keyword in SENIOR_KEYWORDS[:3]:  # 상위 3개 키워드만 사용
            try:
                for page in range(1, page_limit + 1):
                    search_url = f"{self.base_url}/zf_user/search/recruit?searchType=search&searchword={urllib.parse.quote(keyword)}&recruitPage={page}"
                    
                    self.logger.info(f"검색 페이지 크롤링: {search_url}")
                    html = self.fetch_page(search_url)
                    
                    if not html:
                        continue
                    
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # 채용공고 링크 추출
                    job_links = soup.find_all('a', class_='str_tit')
                    
                    if not job_links:
                        self.logger.warning(f"채용공고 링크를 찾을 수 없음: {search_url}")
                        break
                    
                    for link in job_links:
                        href = link.get('href')
                        if href:
                            if href.startswith('/'):
                                full_url = self.base_url + href
                            else:
                                full_url = href
                            
                            if full_url not in job_urls:
                                job_urls.append(full_url)
                    
                    self.logger.info(f"페이지 {page}에서 {len(job_links)}개 링크 수집")
                    
            except Exception as e:
                self.logger.error(f"키워드 '{keyword}' 검색 중 오류: {e}")
                continue
        
        self.logger.info(f"총 {len(job_urls)}개 채용공고 URL 수집 완료")
        return job_urls
    
    def parse_job_listing(self, html: str) -> Optional[Dict]:
        """개별 채용공고 파싱"""
        if not html:
            return None
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # 기본 정보 추출
            job_data = {
                'site': 'saramin',
                'url': '',
                'title': '',
                'company': '',
                'location': '',
                'salary': '',
                'employment_type': '',
                'experience': '',
                'education': '',
                'category': '',
                'description': '',
                'requirements': '',
                'benefits': '',
                'deadline': '',
                'posted_date': '',
                'tags': []
            }
            
            # 제목
            title_elem = soup.find('h1', class_='tit_job') or soup.find('div', class_='tit_job')
            if title_elem:
                job_data['title'] = JobCrawlerUtils.clean_text(title_elem.get_text())
            
            # 회사명
            company_elem = soup.find('a', class_='link_tit') or soup.find('div', class_='recruit_info_company')
            if company_elem:
                job_data['company'] = JobCrawlerUtils.clean_text(company_elem.get_text())
            
            # 근무지역
            location_elem = soup.find('div', class_='recruit_condition')
            if location_elem:
                location_text = location_elem.get_text()
                # 근무지역 추출
                location_match = re.search(r'근무지역\s*([^·]+)', location_text)
                if location_match:
                    job_data['location'] = JobCrawlerUtils.clean_text(location_match.group(1))
            
            # 급여
            salary_elem = soup.find('div', class_='recruit_condition')
            if salary_elem:
                salary_text = salary_elem.get_text()
                salary = JobCrawlerUtils.extract_salary(salary_text)
                if salary:
                    job_data['salary'] = salary
            
            # 고용형태
            employment_elem = soup.find('div', class_='recruit_condition')
            if employment_elem:
                employment_text = employment_elem.get_text()
                if '정규직' in employment_text:
                    job_data['employment_type'] = '정규직'
                elif '계약직' in employment_text:
                    job_data['employment_type'] = '계약직'
                elif '파트타임' in employment_text or '시간제' in employment_text:
                    job_data['employment_type'] = '파트타임'
            
            # 경력 요구사항
            experience_elem = soup.find('div', class_='recruit_condition')
            if experience_elem:
                exp_text = experience_elem.get_text()
                if '경력무관' in exp_text:
                    job_data['experience'] = '경력무관'
                elif '신입' in exp_text:
                    job_data['experience'] = '신입'
                else:
                    exp_match = re.search(r'(\d+)년\s*이상', exp_text)
                    if exp_match:
                        job_data['experience'] = f"{exp_match.group(1)}년 이상"
            
            # 학력 요구사항
            education_elem = soup.find('div', class_='recruit_condition')
            if education_elem:
                edu_text = education_elem.get_text()
                if '학력무관' in edu_text:
                    job_data['education'] = '학력무관'
                elif '고등학교' in edu_text:
                    job_data['education'] = '고등학교'
                elif '대학교' in edu_text:
                    job_data['education'] = '대학교'
            
            # 직무 카테고리
            category_elem = soup.find('div', class_='recruit_condition')
            if category_elem:
                category_text = category_elem.get_text()
                # 직무 카테고리 추출 로직
                job_data['category'] = JobCrawlerUtils.clean_text(category_text[:50])
            
            # 상세 설명
            desc_elem = soup.find('div', class_='user_content') or soup.find('div', class_='recruit_contents')
            if desc_elem:
                job_data['description'] = JobCrawlerUtils.clean_text(desc_elem.get_text())
            
            # 지원 자격 요건
            req_section = soup.find('div', class_='recruit_condition_list')
            if req_section:
                job_data['requirements'] = JobCrawlerUtils.clean_text(req_section.get_text())
            
            # 복리후생
            benefit_elem = soup.find('div', class_='benefit_list')
            if benefit_elem:
                job_data['benefits'] = JobCrawlerUtils.clean_text(benefit_elem.get_text())
            
            # 마감일
            deadline_elem = soup.find('div', class_='recruit_date')
            if deadline_elem:
                deadline_text = deadline_elem.get_text()
                deadline_match = re.search(r'(\d{4}-\d{2}-\d{2})', deadline_text)
                if deadline_match:
                    job_data['deadline'] = deadline_match.group(1)
            
            # 등록일
            posted_elem = soup.find('div', class_='recruit_date')
            if posted_elem:
                posted_text = posted_elem.get_text()
                posted_match = re.search(r'등록일\s*(\d{4}-\d{2}-\d{2})', posted_text)
                if posted_match:
                    job_data['posted_date'] = posted_match.group(1)
            
            # 태그
            tag_elems = soup.find_all('span', class_='tag')
            job_data['tags'] = [JobCrawlerUtils.clean_text(tag.get_text()) for tag in tag_elems]
            
            # 시니어 친화적인지 확인
            if not JobCrawlerUtils.is_senior_friendly(job_data):
                self.logger.debug(f"시니어 친화적이지 않은 공고: {job_data['title']}")
                return None
            
            self.logger.info(f"채용공고 파싱 완료: {job_data['title']} - {job_data['company']}")
            return job_data
            
        except Exception as e:
            self.logger.error(f"채용공고 파싱 중 오류: {e}")
            return None
    
    def crawl_jobs(self, max_jobs: int = 100) -> List[Dict]:
        """채용공고 크롤링 실행"""
        self.logger.info(f"사람인 채용공고 크롤링 시작 (최대 {max_jobs}개)")
        
        # URL 목록 가져오기
        job_urls = self.get_job_urls()
        
        if not job_urls:
            self.logger.warning("크롤링할 채용공고 URL이 없습니다")
            return []
        
        # 최대 개수 제한
        job_urls = job_urls[:max_jobs]
        
        crawled_jobs = []
        
        for i, url in enumerate(job_urls, 1):
            try:
                self.logger.info(f"채용공고 크롤링 중 ({i}/{len(job_urls)}): {url}")
                
                html = self.fetch_page(url)
                if not html:
                    continue
                
                job_data = self.parse_job_listing(html)
                if job_data:
                    job_data['url'] = url
                    crawled_jobs.append(job_data)
                    self.logger.info(f"채용공고 크롤링 성공: {job_data['title']}")
                
            except Exception as e:
                self.logger.error(f"채용공고 크롤링 실패: {url} - {e}")
                continue
        
        self.logger.info(f"사람인 크롤링 완료: {len(crawled_jobs)}개 채용공고 수집")
        return crawled_jobs


def main():
    """테스트 실행"""
    crawler = SaraminCrawler()
    
    # 테스트 크롤링
    jobs = crawler.crawl_jobs(max_jobs=10)
    
    print(f"\n=== 크롤링 결과 ===")
    print(f"수집된 채용공고 수: {len(jobs)}")
    
    for job in jobs[:3]:  # 상위 3개만 출력
        print(f"\n제목: {job['title']}")
        print(f"회사: {job['company']}")
        print(f"지역: {job['location']}")
        print(f"급여: {job['salary']}")
        print(f"고용형태: {job['employment_type']}")
        print(f"URL: {job['url']}")


if __name__ == "__main__":
    main()