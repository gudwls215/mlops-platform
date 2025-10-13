#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
자기소개서 샘플 데이터 생성기
실제 크롤링 대신 테스트용 샘플 데이터를 생성
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager
from datetime import datetime
import random

class CoverLetterSampleGenerator:
    def __init__(self):
        self.db_manager = DatabaseManager()
        
        # 샘플 회사 목록
        self.companies = [
            'Samsung Electronics', 'LG전자', 'SK하이닉스', 'NAVER', 'Kakao',
            '현대자동차', '기아자동차', '삼성SDI', 'LG화학', '포스코',
            'KB금융그룹', '신한은행', 'NH농협은행', '롯데그룹', 'GS칼텍스',
            '한국전력공사', '한국철도공사', 'KT', 'SKT', 'LG유플러스'
        ]
        
        # 샘플 직무 목록
        self.positions = [
            '시스템 관리자', '프로젝트 매니저', '데이터 분석가', 'IT 컨설턴트', '네트워크 엔지니어',
            '품질 관리 전문가', '영업 관리자', '마케팅 전문가', '인사 담당자', '재무 분석가',
            'R&D 연구원', '생산 관리자', '물류 담당자', '고객 서비스 매니저', '기술 지원 전문가',
            '전략 기획자', '비즈니스 개발자', '운영 매니저', '법무 담당자', '감사 전문가'
        ]
        
        # 샘플 부서 목록
        self.departments = [
            'IT사업부', '기술연구소', '경영지원팀', '마케팅부', '영업부',
            'HR팀', '재무팀', '생산관리부', '품질보증팀', '고객서비스부',
            '전략기획팀', '법무팀', '감사팀', '구매팀', '물류팀'
        ]
        
        # 샘플 자기소개서 내용 템플릿
        self.cover_letter_templates = [
            {
                'title': '{company} {position} 지원',
                'content': """
안녕하십니까. {company} {position} 직무에 지원하게 된 {name}입니다.

저는 지난 {experience_years}년간 {field} 분야에서 다양한 프로젝트를 수행하며 전문성을 쌓아왔습니다. 
특히 {skill_area}에서의 경험을 통해 {achievement}를 달성한 바 있습니다.

{company}의 비전과 가치에 깊이 공감하며, 제가 보유한 {expertise}를 바탕으로 
회사의 성장에 기여하고자 합니다.

주요 경력사항:
- {career_1}
- {career_2} 
- {career_3}

핵심 역량:
- {skill_1}: {skill_1_detail}
- {skill_2}: {skill_2_detail}
- {skill_3}: {skill_3_detail}

향후 계획:
{future_plan}

감사합니다.
                """,
                'keywords': ['경력', '프로젝트', '전문성', '기여', '성장']
            },
            {
                'title': '{position} 경력직 지원서',
                'content': """
{company} 인사담당자님께

{position} 경력직 모집 공고를 보고 지원하게 되었습니다.

저는 {experience_years}년의 실무 경험을 바탕으로 {strength_area}에서 뛰어난 성과를 거두어 왔습니다.
이전 직장에서 {major_project}를 성공적으로 완수하며 {quantified_result}의 성과를 달성했습니다.

제가 {company}에서 기여할 수 있는 부분:
1. {contribution_1}
2. {contribution_2}
3. {contribution_3}

보유 기술 및 경험:
- {tech_1}: {tech_1_years}년 경험
- {tech_2}: {tech_2_years}년 경험  
- {tech_3}: {tech_3_years}년 경험

{company}와 함께 성장하며 더 큰 가치를 창출하고 싶습니다.

지원자 {name} 드림
                """,
                'keywords': ['실무경험', '성과', '기여', '성장', '가치창출']
            }
        ]
        
        # 샘플 개인정보
        self.sample_names = ['김철수', '이영희', '박민수', '정수진', '최동현', '한지원', '오성훈', '임소영']
        
        # 기술 분야
        self.tech_fields = ['IT', '제조업', '금융', '유통', '건설', '화학', '전자', '자동차']
        self.skills = ['프로젝트 관리', '데이터 분석', '시스템 설계', '품질 관리', '고객 관리', '전략 기획']
        
    def generate_sample_cover_letters(self, count=10):
        """샘플 자기소개서 생성"""
        print(f"🎯 {count}개의 샘플 자기소개서 생성 시작...")
        
        generated_letters = []
        
        for i in range(count):
            # 랜덤 데이터 선택
            company = random.choice(self.companies)
            position = random.choice(self.positions)
            department = random.choice(self.departments)
            template = random.choice(self.cover_letter_templates)
            name = random.choice(self.sample_names)
            
            # 경력 연수 (시니어 친화적으로 10-30년)
            experience_years = random.randint(10, 30)
            
            # 템플릿 데이터 채우기
            template_data = {
                'company': company,
                'position': position,
                'name': name,
                'experience_years': experience_years,
                'field': random.choice(self.tech_fields),
                'skill_area': random.choice(self.skills),
                'achievement': f'{random.randint(15, 50)}% 효율성 향상',
                'expertise': random.choice(self.skills),
                'career_1': f'{random.choice(self.tech_fields)} 프로젝트 리드 ({random.randint(5, 10)}년)',
                'career_2': f'팀 관리 및 운영 ({random.randint(3, 8)}년)',
                'career_3': f'신기술 도입 및 적용 ({random.randint(2, 5)}년)',
                'skill_1': '프로젝트 관리',
                'skill_1_detail': f'{random.randint(50, 100)}개 프로젝트 성공적 완수',
                'skill_2': '팀 리더십',
                'skill_2_detail': f'{random.randint(10, 30)}명 팀 관리 경험',
                'skill_3': '기술 전문성',
                'skill_3_detail': f'{random.choice(self.tech_fields)} 분야 {experience_years}년 경험',
                'future_plan': f'{company}의 핵심 인재로서 지속적인 성장과 기여',
                'strength_area': random.choice(self.skills),
                'major_project': f'{random.choice(self.tech_fields)} 시스템 구축',
                'quantified_result': f'{random.randint(20, 60)}% 비용 절감',
                'contribution_1': '기존 업무 프로세스 개선',
                'contribution_2': '신입/주니어 직원 멘토링',
                'contribution_3': '새로운 기술 및 방법론 도입',
                'tech_1': 'Python/SQL',
                'tech_1_years': random.randint(5, 15),
                'tech_2': '프로젝트 관리툴',
                'tech_2_years': random.randint(3, 10),
                'tech_3': '데이터 분석',
                'tech_3_years': random.randint(2, 8)
            }
            
            # 내용 생성
            title = template['title'].format(**template_data)
            content = template['content'].format(**template_data).strip()
            
            # 자기소개서 데이터 구성
            cover_letter_data = {
                'title': title,
                'company': company,
                'position': position,
                'department': department,
                'experience_level': f'{experience_years}년 경력',
                'content': content,
                'is_passed': random.choice([True, False, None]),  # 합격/불합격/미정
                'application_year': random.randint(2020, 2024),
                'keywords': template['keywords'] + [company, position],
                'url': f'https://example.com/cover-letter/{i+1}',
                'views': random.randint(50, 500),
                'likes': random.randint(5, 50),
                'source': 'sample_data'
            }
            
            generated_letters.append(cover_letter_data)
            print(f"  📝 [{i+1}/{count}] {title[:50]}... 생성 완료")
        
        return generated_letters
    
    def save_sample_data(self, count=10):
        """샘플 데이터 생성 및 저장"""
        try:
            # 샘플 자기소개서 생성
            cover_letters = self.generate_sample_cover_letters(count)
            
            # 데이터베이스에 저장
            print("\n💾 데이터베이스 저장 중...")
            saved_count = 0
            
            for cover_letter in cover_letters:
                if self.db_manager.insert_cover_letter_sample(cover_letter):
                    saved_count += 1
            
            print(f"\n🎉 샘플 데이터 생성 완료!")
            print(f"📊 생성된 자기소개서: {len(cover_letters)}개")
            print(f"💾 저장 성공: {saved_count}개")
            
            # 저장 후 통계 확인
            stats = self.db_manager.get_cover_letter_samples_stats()
            print(f"\n📈 전체 자기소개서 통계:")
            print(f"  - 총 개수: {stats.get('total', 0)}개")
            print(f"  - 합격: {stats.get('passed', 0)}개")
            print(f"  - 불합격: {stats.get('failed', 0)}개")
            print(f"  - 최근 2년: {stats.get('recent_years', 0)}개")
            
            return True
            
        except Exception as e:
            print(f"❌ 샘플 데이터 생성 실패: {e}")
            return False

def main():
    """메인 실행 함수"""
    generator = CoverLetterSampleGenerator()
    
    # 샘플 데이터 생성 및 저장
    generator.save_sample_data(count=15)

if __name__ == "__main__":
    main()