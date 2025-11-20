// API 유틸리티 함수들
// HTTPS 환경에서는 상대 경로 사용 (Nginx 프록시), HTTP 환경에서는 직접 IP 연결

/**
 * 현재 환경에 맞는 API Base URL을 반환합니다.
 * HTTPS 환경: '' (상대 경로, Nginx 프록시 사용)
 * HTTP 환경: 'http://192.168.0.147:9000' (직접 연결)
 */
export const getApiBaseUrl = (): string => {
  // 환경변수가 설정된 경우 우선 사용
  if (process.env.REACT_APP_API_URL) {
    console.log('Using environment API URL:', process.env.REACT_APP_API_URL);
    return process.env.REACT_APP_API_URL;
  }
  
  // 브라우저 환경에서 현재 프로토콜 확인
  if (typeof window !== 'undefined') {
    const protocol = window.location.protocol;
    const baseUrl = protocol === 'https:' ? '' : 'http://192.168.0.147:9000';
    console.log('Detected protocol:', protocol, '-> Base URL:', baseUrl || '(empty/relative)');
    return baseUrl;
  }
  
  // 서버사이드 렌더링 환경에서는 기본값
  console.log('Using SSR default URL: http://192.168.0.147:9000');
  return 'http://192.168.0.147:9000';
};

/**
 * API 엔드포인트 URL을 생성합니다.
 * @param endpoint - API 엔드포인트 (예: '/api/v1/job')
 * @returns 완전한 URL
 */
export const createApiUrl = (endpoint: string): string => {
  const baseUrl = getApiBaseUrl();
  const finalUrl = `${baseUrl}${endpoint}`;
  console.log('Creating API URL:', endpoint, '-> Final URL:', finalUrl);
  return finalUrl;
};