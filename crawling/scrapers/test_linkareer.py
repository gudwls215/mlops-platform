#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Linkareer HTML 구조 테스트
"""

from bs4 import BeautifulSoup
import re

def test_html_parsing():
    """example.html 파일을 파싱해서 구조 확인"""
    
    # example.html 파일 읽기
    with open('/home/ttm/tensorflow-jupyter/jupyterNotebook/khj/mlops-platform/example.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    print("🔍 HTML 구조 분석")
    print("="*50)
    
    # 1. 전체 자기소개서 아이템들 찾기
    print("1. 자기소개서 아이템 찾기")
    
    # 다양한 셀렉터 시도
    selectors = [
        'div.root.flex-wrapper',
        '.CoverLetterListItemDesktop__StyledWrapper-sc-7488c23a-0',
        '[class*="CoverLetterListItemDesktop__StyledWrapper"]',
        'a[href*="/cover-letter/"]'
    ]
    
    for selector in selectors:
        items = soup.select(selector)
        print(f"  {selector}: {len(items)}개")
        
        if items:
            print(f"    첫 번째 아이템 구조:")
            first_item = items[0]
            print(f"    태그: {first_item.name}")
            print(f"    클래스: {first_item.get('class', [])}")
            
            # 링크 찾기
            link = first_item.select_one('a') or first_item
            if link and link.get('href'):
                print(f"    링크: {link.get('href')}")
            
            # 회사명 찾기
            company = first_item.select_one('.organization-name')
            if company:
                print(f"    회사명: {company.get_text().strip()}")
            
            # 직무 찾기  
            role = first_item.select_one('.role')
            if role:
                print(f"    직무: {role.get_text().strip()}")
            
            # 지원시기 찾기
            period = first_item.select_one('.passed-at')
            if period:
                print(f"    지원시기: {period.get_text().strip()}")
            
            print()
    
    # 2. 모든 자기소개서 링크 추출 테스트
    print("\n2. 자기소개서 링크 추출")
    links = soup.select('a[href*="/cover-letter/"]')
    valid_links = []
    
    for link in links:
        href = link.get('href')
        if re.search(r'/cover-letter/\d+', href):  # 숫자 ID가 있는 링크만
            valid_links.append(href)
    
    print(f"  유효한 자기소개서 링크: {len(valid_links)}개")
    
    # 처음 5개 링크 출력
    for i, link in enumerate(valid_links[:5], 1):
        print(f"    {i}. {link}")
    
    # 3. 각 자기소개서 데이터 추출 테스트
    print("\n3. 자기소개서 데이터 추출 테스트")
    
    # 각 링크에 대해 상위 컨테이너 찾고 데이터 추출
    for i, link_href in enumerate(valid_links[:3], 1):  # 처음 3개만 테스트
        link_elem = soup.select_one(f'a[href="{link_href}"]')
        if not link_elem:
            continue
            
        print(f"\n  [{i}] 링크: {link_href}")
        
        # 상위 컨테이너 찾기
        container = link_elem
        for _ in range(5):  # 최대 5단계 상위로 올라가기
            if container and container.parent:
                container = container.parent
                # 자기소개서 관련 클래스가 있는지 확인
                classes = container.get('class', [])
                if any('CoverLetter' in cls for cls in classes):
                    break
            else:
                container = link_elem
                break
        
        print(f"    컨테이너: {container.name} | 클래스: {container.get('class', [])}")
        
        # 데이터 추출
        data = {}
        
        # 회사명
        company_elem = container.select_one('.organization-name')
        if company_elem:
            data['company'] = company_elem.get_text().strip()
        
        # 직무
        role_elem = container.select_one('.role')
        if role_elem:
            data['position'] = role_elem.get_text().strip()
        
        # 지원시기
        period_elem = container.select_one('.passed-at')
        if period_elem:
            data['period'] = period_elem.get_text().strip()
        
        # 타입
        type_elem = container.select_one('.type-text')
        if type_elem:
            data['type'] = type_elem.get_text().strip()
        
        # 스펙
        spec_elem = container.select_one('.spec')
        if spec_elem:
            data['spec'] = spec_elem.get_text().strip()[:100] + "..."
        
        # 미리보기 내용
        content_elem = container.select_one('.content-highlight')
        if content_elem:
            data['preview'] = content_elem.get_text().strip()[:100] + "..."
        
        print(f"    추출된 데이터:")
        for key, value in data.items():
            print(f"      {key}: {value}")

if __name__ == "__main__":
    test_html_parsing()