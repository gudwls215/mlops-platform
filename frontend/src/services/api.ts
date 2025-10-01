import axios from 'axios';
import { 
  API_BASE_URL, 
  Resume, 
  JobPosting, 
  CoverLetter, 
  CreateResumeRequest, 
  CreateCoverLetterRequest 
} from '../types';

// Axios 인스턴스 생성
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 요청 인터셉터
apiClient.interceptors.request.use(
  (config) => {
    // TODO: 필요시 인증 토큰 추가
    // const token = localStorage.getItem('token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 응답 인터셉터
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // 전역 에러 처리
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// 이력서 API
export const resumeApi = {
  // 이력서 목록 조회
  getResumes: async (): Promise<Resume[]> => {
    const response = await apiClient.get('/resumes/');
    return response.data;
  },

  // 이력서 상세 조회
  getResume: async (id: number): Promise<Resume> => {
    const response = await apiClient.get(`/resumes/${id}`);
    return response.data;
  },

  // 이력서 생성
  createResume: async (data: CreateResumeRequest): Promise<Resume> => {
    const response = await apiClient.post('/resumes/', data);
    return response.data;
  },

  // 이력서 수정
  updateResume: async (id: number, data: Partial<CreateResumeRequest>): Promise<Resume> => {
    const response = await apiClient.put(`/resumes/${id}`, data);
    return response.data;
  },

  // 이력서 삭제
  deleteResume: async (id: number): Promise<void> => {
    await apiClient.delete(`/resumes/${id}`);
  },

  // AI 이력서 생성
  generateResume: async (voiceText: string): Promise<Resume> => {
    const response = await apiClient.post('/resumes/generate', { voice_text: voiceText });
    return response.data;
  },
};

// 채용공고 API
export const jobApi = {
  // 채용공고 목록 조회
  getJobs: async (params?: { 
    skip?: number; 
    limit?: number; 
    search?: string;
  }): Promise<JobPosting[]> => {
    const response = await apiClient.get('/jobs/', { params });
    return response.data;
  },

  // 채용공고 상세 조회
  getJob: async (id: number): Promise<JobPosting> => {
    const response = await apiClient.get(`/jobs/${id}`);
    return response.data;
  },

  // 매칭 점수 조회
  getMatchingScore: async (resumeId: number, jobId: number): Promise<{ score: number; details: any }> => {
    const response = await apiClient.get(`/jobs/${jobId}/match/${resumeId}`);
    return response.data;
  },
};

// 자기소개서 API
export const coverLetterApi = {
  // 자기소개서 목록 조회
  getCoverLetters: async (): Promise<CoverLetter[]> => {
    const response = await apiClient.get('/cover-letters/');
    return response.data;
  },

  // 자기소개서 상세 조회
  getCoverLetter: async (id: number): Promise<CoverLetter> => {
    const response = await apiClient.get(`/cover-letters/${id}`);
    return response.data;
  },

  // 자기소개서 생성
  createCoverLetter: async (data: CreateCoverLetterRequest): Promise<CoverLetter> => {
    const response = await apiClient.post('/cover-letters/', data);
    return response.data;
  },

  // AI 자기소개서 생성
  generateCoverLetter: async (resumeId: number, jobId: number): Promise<CoverLetter> => {
    const response = await apiClient.post('/cover-letters/generate', {
      resume_id: resumeId,
      job_posting_id: jobId
    });
    return response.data;
  },
};

// 음성 처리 API
export const voiceApi = {
  // 음성 파일 업로드 및 텍스트 변환
  transcribeAudio: async (audioFile: File): Promise<{ text: string }> => {
    const formData = new FormData();
    formData.append('audio', audioFile);
    
    const response = await apiClient.post('/voice/transcribe', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};

// 헬스체크 API
export const healthApi = {
  checkHealth: async (): Promise<{ status: string; timestamp: string }> => {
    const response = await apiClient.get('/health');
    return response.data;
  },
};

export default apiClient;