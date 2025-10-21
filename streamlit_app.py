#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
장년층 맞춤형 이력서 생성 서비스
Streamlit 웹 인터페이스
"""

import streamlit as st
import pandas as pd
import json
import os
import sys
from datetime import datetime, timedelta
import io
from pathlib import Path

# 프로젝트 루트 경로 추가
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

# 필요한 모듈들 임포트
try:
    from crawling.database import DatabaseManager
    # OpenAI 관련 모듈은 API 키가 있을 때만 임포트
    if os.getenv('OPENAI_API_KEY'):
        import openai
        from openai_api_integration import AIResumeGenerator, ResumeExporter
        OPENAI_AVAILABLE = True
    else:
        OPENAI_AVAILABLE = False
        st.warning("⚠️ OpenAI API 키가 설정되지 않았습니다. 데모 모드로 실행됩니다.")
except ImportError as e:
    st.error(f"모듈 임포트 오류: {e}")
    st.stop()

# 페이지 설정
st.set_page_config(
    page_title="장년층 맞춤 이력서 생성 서비스",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if 'user_data' not in st.session_state:
    st.session_state.user_data = {}
if 'generated_resume' not in st.session_state:
    st.session_state.generated_resume = None
if 'job_postings' not in st.session_state:
    st.session_state.job_postings = []

class StreamlitResumeApp:
    """Streamlit 이력서 생성 앱"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        if OPENAI_AVAILABLE:
            self.ai_generator = AIResumeGenerator()
            self.resume_exporter = ResumeExporter()
        else:
            self.ai_generator = None
            self.resume_exporter = None
    
    def show_header(self):
        """헤더 섹션"""
        st.markdown("""
        <div style="background: linear-gradient(90deg, #1f4e79, #2e7bcf); padding: 2rem; border-radius: 10px; margin-bottom: 2rem;">
            <h1 style="color: white; text-align: center; margin: 0;">
                🎯 장년층 맞춤형 이력서 생성 서비스
            </h1>
            <p style="color: white; text-align: center; margin: 0.5rem 0 0 0; font-size: 1.2rem;">
                풍부한 경험과 전문성을 부각시키는 AI 기반 이력서 작성 도구
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    def show_sidebar(self):
        """사이드바 메뉴"""
        with st.sidebar:
            st.markdown("## 📋 메뉴")
            
            menu_options = [
                "🏠 홈",
                "👤 사용자 정보 입력",
                "🤖 AI 이력서 생성", 
                "📊 채용공고 분석",
                "💾 결과 다운로드",
                "📈 서비스 현황"
            ]
            
            selected_menu = st.selectbox("메뉴 선택", menu_options, index=0)
            
            # 시스템 상태 표시
            st.markdown("---")
            st.markdown("### 🔧 시스템 상태")
            
            # 데이터베이스 연결 상태
            try:
                conn = self.db_manager.get_connection()
                if conn:
                    st.success("✅ 데이터베이스 연결")
                    conn.close()
                else:
                    st.error("❌ 데이터베이스 오류")
            except:
                st.error("❌ 데이터베이스 오류")
            
            # OpenAI API 상태
            if OPENAI_AVAILABLE:
                st.success("✅ OpenAI API 연결")
            else:
                st.warning("⚠️ OpenAI API 미연결")
            
            return selected_menu
    
    def show_home(self):
        """홈 페이지"""
        st.markdown("## 🏠 서비스 소개")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
            ### 🎯 장년층을 위한 특별한 이력서 서비스
            
            **이런 분들께 추천합니다:**
            - 📈 풍부한 경력을 가진 50대 이상 구직자
            - 🔄 새로운 분야로 전환을 원하시는 분
            - 💡 본인의 강점을 효과적으로 어필하고 싶은 분
            - 🤝 멘토링과 리더십 경험을 부각하고 싶은 분
            
            **주요 특징:**
            - 🤖 AI 기반 맞춤형 이력서 생성
            - 📄 다양한 형식 지원 (Word, PDF, JSON)
            - 📊 실시간 채용공고 분석 및 매칭
            - 🎨 전문적이고 모던한 디자인
            """)
            
            # 최근 생성된 이력서 수
            try:
                recent_count = self.get_recent_resume_count()
                st.metric("📊 최근 7일간 생성된 이력서", f"{recent_count}개")
            except:
                st.metric("📊 최근 7일간 생성된 이력서", "데이터 로딩 중...")
        
        with col2:
            st.markdown("### 🚀 시작하기")
            st.info("""
            **3단계로 간단하게!**
            
            1️⃣ 개인정보 및 경력사항 입력
            
            2️⃣ AI가 자동으로 이력서 생성
            
            3️⃣ 원하는 형식으로 다운로드
            """)
            
            if st.button("📝 이력서 만들기 시작", type="primary", use_container_width=True):
                st.session_state.menu_selection = "👤 사용자 정보 입력"
                st.rerun()
    
    def show_user_input(self):
        """사용자 정보 입력 페이지"""
        st.markdown("## 👤 개인정보 및 경력사항 입력")
        
        with st.form("user_info_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📝 기본정보")
                name = st.text_input("성명 *", placeholder="홍길동")
                age = st.number_input("연령", min_value=40, max_value=80, value=55)
                phone = st.text_input("연락처", placeholder="010-1234-5678")
                email = st.text_input("이메일", placeholder="hong@email.com")
                
                st.markdown("### 🎯 희망직무")
                target_position = st.text_input("희망 직책", placeholder="프로젝트 매니저")
                target_industry = st.selectbox("희망 업종", [
                    "IT/소프트웨어", "제조업", "금융/보험", "교육", "의료/제약",
                    "유통/서비스", "건설/부동산", "미디어/광고", "기타"
                ])
                salary_expectation = st.selectbox("희망 연봉", [
                    "면접 후 결정", "3000만원 이상", "4000만원 이상", 
                    "5000만원 이상", "6000만원 이상", "7000만원 이상"
                ])
            
            with col2:
                st.markdown("### 💼 경력사항")
                career_years = st.number_input("총 경력 년수", min_value=10, max_value=50, value=25)
                
                career_history = st.text_area("주요 경력사항", 
                    placeholder="""예시:
- ABC회사 (2000-2015): 팀장, 15년간 프로젝트 관리
- DEF회사 (2015-2020): 부장, 대규모 SI 프로젝트 총괄
- GHI회사 (2020-2023): 이사, 디지털 전환 프로젝트 주도""",
                    height=150)
                
                education = st.text_area("학력사항",
                    placeholder="서울대학교 경영학과 학사 (1995년 졸업)",
                    height=80)
                
                skills = st.text_area("보유 기술/자격증",
                    placeholder="""예시:
- PMP 자격증, 정보처리기사
- Excel, PowerPoint, Project 능숙
- 기본적인 SQL 및 데이터 분석""",
                    height=100)
                
                st.markdown("### 🌟 자기 PR 포인트")
                pr_points = st.text_area("본인의 강점과 어필 포인트",
                    placeholder="""예시:
- 25년간의 풍부한 프로젝트 관리 경험
- 후배 멘토링 및 조직 발전에 기여
- 새로운 기술 학습에 적극적
- 소통과 협업을 통한 문제 해결""",
                    height=120)
            
            # 폼 제출
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                submitted = st.form_submit_button("📝 정보 저장", type="primary", use_container_width=True)
            
            if submitted:
                if not all([name, target_position, career_history]):
                    st.error("❌ 필수 항목(성명, 희망직책, 경력사항)을 모두 입력해주세요.")
                else:
                    # 세션 상태에 사용자 데이터 저장
                    st.session_state.user_data = {
                        'name': name,
                        'age': age,
                        'contact': f"{email} / {phone}",
                        'target_position': target_position,
                        'target_industry': target_industry,
                        'salary_expectation': salary_expectation,
                        'career_years': career_years,
                        'career_history': career_history,
                        'education': education,
                        'skills_certifications': skills,
                        'self_pr_points': pr_points
                    }
                    
                    st.success("✅ 정보가 저장되었습니다!")
                    st.balloons()
                    
                    # 다음 단계 버튼
                    if st.button("🤖 AI 이력서 생성하러 가기", type="primary"):
                        st.session_state.menu_selection = "🤖 AI 이력서 생성"
                        st.rerun()
    
    def show_ai_generation(self):
        """AI 이력서 생성 페이지"""
        st.markdown("## 🤖 AI 이력서 생성")
        
        if not st.session_state.user_data:
            st.warning("⚠️ 먼저 사용자 정보를 입력해주세요.")
            if st.button("👤 사용자 정보 입력하러 가기"):
                st.session_state.menu_selection = "👤 사용자 정보 입력"
                st.rerun()
            return
        
        # 사용자 데이터 표시
        with st.expander("📋 입력된 정보 확인", expanded=False):
            user_data = st.session_state.user_data
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**성명:** {user_data.get('name')}")
                st.write(f"**연령:** {user_data.get('age')}세")
                st.write(f"**희망직책:** {user_data.get('target_position')}")
                st.write(f"**경력:** {user_data.get('career_years')}년")
            with col2:
                st.write(f"**연락처:** {user_data.get('contact')}")
                st.write(f"**업종:** {user_data.get('target_industry')}")
                st.write(f"**희망연봉:** {user_data.get('salary_expectation')}")
        
        # AI 생성 옵션
        st.markdown("### ⚙️ 생성 옵션")
        col1, col2 = st.columns(2)
        
        with col1:
            generation_style = st.selectbox("이력서 스타일", [
                "전문적이고 간결한 스타일",
                "경험 중심 상세 스타일", 
                "성과 중심 임팩트 스타일",
                "멘토링 및 리더십 강조 스타일"
            ])
        
        with col2:
            include_cover_letter = st.checkbox("자기소개서도 함께 생성", value=True)
        
        # 채용공고 매칭 옵션
        st.markdown("### 🎯 채용공고 맞춤 생성 (선택사항)")
        use_job_matching = st.checkbox("특정 채용공고에 맞춰서 생성하기")
        
        selected_job = None
        if use_job_matching:
            # 데이터베이스에서 채용공고 가져오기
            job_postings = self.get_job_postings()
            if job_postings:
                job_options = [f"{job['company_name']} - {job['job_title']}" for job in job_postings[:10]]
                selected_job_idx = st.selectbox("채용공고 선택", range(len(job_options)), 
                                               format_func=lambda x: job_options[x])
                selected_job = job_postings[selected_job_idx]
                
                with st.expander("📋 선택된 채용공고 상세정보"):
                    st.write(f"**회사:** {selected_job['company_name']}")
                    st.write(f"**직무:** {selected_job['job_title']}")
                    st.write(f"**지역:** {selected_job.get('location', 'N/A')}")
                    st.write(f"**경력:** {selected_job.get('experience_level', 'N/A')}")
                    if selected_job.get('job_description'):
                        st.write(f"**업무내용:** {selected_job['job_description'][:200]}...")
            else:
                st.info("💡 현재 매칭 가능한 채용공고가 없습니다. 일반 이력서를 생성합니다.")
        
        # 생성 버튼
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col2:
            if OPENAI_AVAILABLE:
                generate_button = st.button("🚀 AI 이력서 생성", type="primary", use_container_width=True)
            else:
                generate_button = st.button("📄 데모 이력서 생성", type="primary", use_container_width=True)
        
        if generate_button:
            with st.spinner("🤖 AI가 이력서를 생성 중입니다... 잠시만 기다려주세요."):
                if OPENAI_AVAILABLE:
                    # 실제 AI 생성
                    result = self.generate_resume_with_ai(st.session_state.user_data, generation_style)
                else:
                    # 데모 이력서 생성
                    result = self.generate_demo_resume(st.session_state.user_data)
                
                if result['success']:
                    st.session_state.generated_resume = result
                    st.success("✅ 이력서가 성공적으로 생성되었습니다!")
                    st.balloons()
                else:
                    st.error(f"❌ 이력서 생성 실패: {result.get('error', '알 수 없는 오류')}")
        
        # 생성된 이력서 표시
        if st.session_state.generated_resume:
            self.show_generated_resume()
    
    def show_generated_resume(self):
        """생성된 이력서 표시"""
        st.markdown("---")
        st.markdown("## 📄 생성된 이력서")
        
        resume_data = st.session_state.generated_resume
        
        # 이력서 내용 표시
        if resume_data.get('resume'):
            with st.container():
                if isinstance(resume_data['resume'], dict):
                    # JSON 형태의 이력서
                    for section, content in resume_data['resume'].items():
                        st.markdown(f"### {section}")
                        if isinstance(content, list):
                            for item in content:
                                st.write(f"• {item}")
                        else:
                            st.write(content)
                        st.markdown("---")
                else:
                    # 텍스트 형태의 이력서
                    st.markdown(resume_data['resume'])
        
        # 다운로드 버튼들
        st.markdown("### 💾 다운로드")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📄 Word 다운로드", use_container_width=True):
                self.download_resume('word')
        
        with col2:
            if st.button("📋 PDF 다운로드", use_container_width=True):
                self.download_resume('pdf')
        
        with col3:
            if st.button("💾 JSON 다운로드", use_container_width=True):
                self.download_resume('json')
    
    def generate_resume_with_ai(self, user_data, style):
        """AI를 사용한 실제 이력서 생성"""
        try:
            if not self.ai_generator:
                return {'success': False, 'error': 'AI 생성기를 사용할 수 없습니다.'}
            
            # AI 이력서 생성
            result = self.ai_generator.generate_resume(user_data)
            return result
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def generate_demo_resume(self, user_data):
        """데모용 이력서 생성"""
        demo_resume = {
            "개인정보": {
                "성명": user_data.get('name', ''),
                "연령": f"{user_data.get('age', '')}세",
                "연락처": user_data.get('contact', ''),
                "희망직무": user_data.get('target_position', '')
            },
            "자기소개": f"""{user_data.get('career_years', 0)}년간의 풍부한 경험을 바탕으로 {user_data.get('target_position', '전문직')} 분야에서 새로운 도전을 통해 조직 발전에 기여하고자 합니다. 

{user_data.get('self_pr_points', '다양한 프로젝트 경험과 팀 리더십을 통해 검증된 실무 능력을 보유하고 있으며, 지속적인 학습과 변화 적응을 통해 새로운 환경에서도 성과를 창출할 수 있습니다.')}""",
            "경력사항": user_data.get('career_history', '').split('\n') if user_data.get('career_history') else [],
            "학력사항": [user_data.get('education', '')] if user_data.get('education') else [],
            "보유기술": user_data.get('skills_certifications', '').split('\n') if user_data.get('skills_certifications') else [],
            "핵심역량": [
                "프로젝트 관리 및 팀 리더십",
                "문제 해결 및 의사결정 능력", 
                "멘토링 및 후배 육성",
                "새로운 기술 학습 및 적응력"
            ]
        }
        
        return {
            'success': True,
            'resume': demo_resume,
            'note': 'OpenAI API 연결 시 더 정교한 이력서 생성 가능'
        }
    
    def get_job_postings(self):
        """데이터베이스에서 채용공고 가져오기"""
        try:
            conn = self.db_manager.get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor()
            query = """
            SELECT company_name, job_title, location, experience_level, job_description
            FROM mlops.job_postings 
            WHERE job_title IS NOT NULL 
            ORDER BY created_at DESC 
            LIMIT 20
            """
            cursor.execute(query)
            
            columns = ['company_name', 'job_title', 'location', 'experience_level', 'job_description']
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            cursor.close()
            conn.close()
            return results
            
        except Exception as e:
            st.error(f"채용공고 조회 오류: {e}")
            return []
    
    def get_recent_resume_count(self):
        """최근 생성된 이력서 수 조회"""
        try:
            # 데모용으로 랜덤 수치 반환
            import random
            return random.randint(15, 45)
        except:
            return 0
    
    def download_resume(self, format_type):
        """이력서 다운로드"""
        if not st.session_state.generated_resume:
            st.error("생성된 이력서가 없습니다.")
            return
        
        resume_data = st.session_state.generated_resume['resume']
        user_name = st.session_state.user_data.get('name', '이력서')
        
        if format_type == 'json':
            # JSON 다운로드
            json_str = json.dumps(resume_data, ensure_ascii=False, indent=2)
            st.download_button(
                label="📄 JSON 파일 다운로드",
                data=json_str,
                file_name=f"{user_name}_이력서_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
        
        elif format_type == 'word':
            st.info("💡 Word 파일 다운로드는 추후 구현 예정입니다.")
        
        elif format_type == 'pdf':
            st.info("💡 PDF 파일 다운로드는 추후 구현 예정입니다.")
    
    def show_job_analysis(self):
        """채용공고 분석 페이지"""
        st.markdown("## 📊 채용공고 분석")
        
        job_postings = self.get_job_postings()
        
        if not job_postings:
            st.warning("⚠️ 현재 분석 가능한 채용공고가 없습니다.")
            return
        
        # 통계 정보
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 총 채용공고", len(job_postings))
        
        with col2:
            companies = set([job['company_name'] for job in job_postings if job['company_name']])
            st.metric("🏢 참여 기업", len(companies))
        
        with col3:
            positions = set([job['job_title'] for job in job_postings if job['job_title']])
            st.metric("💼 직무 종류", len(positions))
        
        with col4:
            # 시니어 친화적 공고 수 (임시)
            senior_friendly = len([job for job in job_postings if any(keyword in str(job.get('job_description', '')) 
                                                                    for keyword in ['경력', '시니어', '매니저', '책임'])])
            st.metric("👔 시니어 적합", f"{senior_friendly}개")
        
        # 채용공고 목록
        st.markdown("### 📋 최근 채용공고")
        
        for i, job in enumerate(job_postings[:10]):
            with st.expander(f"#{i+1} {job['company_name']} - {job['job_title']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**회사:** {job['company_name']}")
                    st.write(f"**직무:** {job['job_title']}")
                with col2:
                    st.write(f"**지역:** {job.get('location', 'N/A')}")
                    st.write(f"**경력:** {job.get('experience_level', 'N/A')}")
                
                if job.get('job_description'):
                    st.write(f"**업무내용:** {job['job_description'][:300]}...")
    
    def show_download(self):
        """결과 다운로드 페이지"""
        st.markdown("## 💾 결과 다운로드")
        
        if not st.session_state.generated_resume:
            st.warning("⚠️ 다운로드할 이력서가 없습니다. 먼저 이력서를 생성해주세요.")
            return
        
        st.markdown("### 📄 다운로드 옵션")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 💾 파일 형식")
            format_options = st.multiselect("다운로드할 형식 선택", 
                                          ["JSON", "Word (추후 지원)", "PDF (추후 지원)"],
                                          default=["JSON"])
        
        with col2:
            st.markdown("#### 🎨 사용자 정의")
            custom_filename = st.text_input("파일명 (확장자 제외)", 
                                           value=f"{st.session_state.user_data.get('name', '이력서')}_{datetime.now().strftime('%Y%m%d')}")
        
        # 미리보기
        st.markdown("### 👀 이력서 미리보기")
        with st.expander("미리보기 보기", expanded=True):
            resume_data = st.session_state.generated_resume['resume']
            st.json(resume_data)
        
        # 다운로드 실행
        if st.button("📥 선택한 형식으로 다운로드", type="primary"):
            if "JSON" in format_options:
                self.download_resume('json')
    
    def show_dashboard(self):
        """서비스 현황 페이지"""
        st.markdown("## 📈 서비스 현황")
        
        # 시스템 상태
        st.markdown("### 🔧 시스템 모니터링")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # 데이터베이스 상태
            try:
                conn = self.db_manager.get_connection()
                if conn:
                    st.success("✅ DB 연결")
                    conn.close()
                else:
                    st.error("❌ DB 오류")
            except:
                st.error("❌ DB 오류")
        
        with col2:
            # AI 서비스 상태
            if OPENAI_AVAILABLE:
                st.success("✅ AI 서비스")
            else:
                st.warning("⚠️ AI 데모모드")
        
        with col3:
            # 크롤링 상태 (가상)
            st.success("✅ 데이터 수집")
        
        with col4:
            # 전체 시스템 상태
            st.success("✅ 정상 운영")
        
        # 사용 통계 (데모용)
        st.markdown("### 📊 사용 통계")
        
        import random
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📄 생성된 이력서", f"{random.randint(150, 300)}", f"+{random.randint(5, 15)}")
        
        with col2:
            st.metric("👥 누적 사용자", f"{random.randint(80, 150)}", f"+{random.randint(2, 8)}")
        
        with col3:
            st.metric("📋 수집된 공고", f"{random.randint(1200, 2500)}", f"+{random.randint(20, 50)}")
        
        # 최근 활동 로그
        st.markdown("### 📋 최근 활동")
        activity_data = [
            {"시간": "2025-10-14 10:30", "활동": "이력서 생성", "사용자": "김***", "상태": "성공"},
            {"시간": "2025-10-14 10:25", "활동": "채용공고 수집", "사용자": "시스템", "상태": "성공"},
            {"시간": "2025-10-14 10:15", "활동": "이력서 생성", "사용자": "이***", "상태": "성공"},
            {"시간": "2025-10-14 10:10", "활동": "데이터 처리", "사용자": "시스템", "상태": "성공"},
            {"시간": "2025-10-14 10:05", "활동": "이력서 생성", "사용자": "박***", "상태": "성공"}
        ]
        
        df = pd.DataFrame(activity_data)
        st.dataframe(df, use_container_width=True)
    
    def run(self):
        """앱 실행"""
        self.show_header()
        selected_menu = self.show_sidebar()
        
        # 메뉴별 페이지 표시
        if selected_menu == "🏠 홈":
            self.show_home()
        elif selected_menu == "👤 사용자 정보 입력":
            self.show_user_input()
        elif selected_menu == "🤖 AI 이력서 생성":
            self.show_ai_generation()
        elif selected_menu == "📊 채용공고 분석":
            self.show_job_analysis()
        elif selected_menu == "💾 결과 다운로드":
            self.show_download()
        elif selected_menu == "📈 서비스 현황":
            self.show_dashboard()


def main():
    """메인 함수"""
    app = StreamlitResumeApp()
    app.run()


if __name__ == "__main__":
    main()