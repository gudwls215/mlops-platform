// API 기본 설정
// 현재 접속 프로토콜이 HTTPS인 경우 상대 경로 사용, HTTP인 경우 직접 IP 사용
const isHTTPS = typeof window !== 'undefined' && window.location.protocol === 'https:';
export const API_BASE_URL = process.env.REACT_APP_API_URL || (isHTTPS ? '' : 'http://192.168.0.147:9000');

// API 타입 정의
export interface Resume {
  id: number;
  title: string;
  content: string;
  skills?: string;
  experience_years?: number;
  education?: string;
  certifications?: string;
  career_summary?: string;
  generated_by_ai: boolean;
  created_at: string;
  updated_at: string;
}

export interface JobPosting {
  id: number;
  title: string;
  company: string;
  description: string;
  requirements: string;
  salary_min?: number;
  salary_max?: number;
  location?: string;
  employment_type?: string;
  experience_level?: string;
  skills_required?: string;
  deadline?: string;
  source_url?: string;
  created_at: string; 
}

export interface CoverLetter {
  id: number;
  title: string;
  content: string;
  job_posting_id?: number;
  resume_id?: number;
  generated_by_ai: boolean;
  created_at: string;
  updated_at: string;
}

export interface User {
  id: number;
  email: string;
  full_name?: string;
  age?: number;
  phone?: string;
  address?: string;
  created_at: string;
}

export interface CreateResumeRequest {
  title: string;
  content: string;
  skills?: string;
  experience_years?: number;
  education?: string;
  certifications?: string;
  career_summary?: string;
}

export interface CreateCoverLetterRequest {
  title: string;
  content: string;
  job_posting_id?: number;
  resume_id?: number;
}