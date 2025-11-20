import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  Chip,
  Button,
  TextField,
  InputAdornment,
  CircularProgress,
  Alert,
  Pagination
} from '@mui/material';
import { Work, LocationOn, AttachMoney, Schedule, Search, TrendingUp } from '@mui/icons-material';
import axios from 'axios';
import { createApiUrl } from '../utils/api';

interface JobPosting {
  id: number;
  title: string;
  company: string;
  location?: string;
  employment_type?: string;
  experience_level?: string;
  salary_min?: number;
  salary_max?: number;
  description?: string;
  requirements?: string;
  skills_required?: string;
  deadline?: string;
  created_at?: string;
}

const JobListPage: React.FC = () => {
  const [jobs, setJobs] = useState<JobPosting[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const itemsPerPage = 10;

  useEffect(() => {
    // 페이지 로드 시 채용공고 가져오기
    fetchJobs();
  }, [page]);

  const fetchJobs = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const skip = (page - 1) * itemsPerPage;
      const response = await axios.get(
        createApiUrl(`/api/v1/job/?skip=${skip}&limit=${itemsPerPage}`)
      );
      
      if (response.data.status === 'success') {
        setJobs(response.data.data.job_postings);
        setTotal(response.data.data.total);
      } else {
        setError('채용공고를 불러오는데 실패했습니다.');
      }
    } catch (err: any) {
      console.error('채용공고 조회 오류:', err);
      setError('채용공고를 불러오는데 실패했습니다. 잠시 후 다시 시도해주세요.');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchKeyword.trim()) {
      fetchJobs();
      return;
    }

    setLoading(true);
    setError(null);
    
    try {
      const formData = new FormData();
      formData.append('keyword', searchKeyword);
      formData.append('skip', '0');
      formData.append('limit', itemsPerPage.toString());
      
      const response = await axios.post(
        createApiUrl('/api/v1/job/search'),
        formData
      );
      
      if (response.data.status === 'success') {
        setJobs(response.data.data.job_postings);
        setTotal(response.data.data.total);
        setPage(1);
      }
    } catch (err: any) {
      console.error('검색 오류:', err);
      setError('검색 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handlePageChange = (event: React.ChangeEvent<unknown>, value: number) => {
    setPage(value);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleApply = (jobId: number) => {
    console.log(`채용공고 ${jobId}에 지원`);
    // TODO: 자기소개서 생성 페이지로 이동
    window.location.href = `/cover-letter?job_id=${jobId}`;
  };

  const formatSalary = (min?: number, max?: number): string => {
    if (!min && !max) return '협의';
    if (min && max) {
      return `${(min / 10000).toFixed(0)}만원 ~ ${(max / 10000).toFixed(0)}만원`;
    }
    if (min) return `${(min / 10000).toFixed(0)}만원 이상`;
    if (max) return `${(max / 10000).toFixed(0)}만원 이하`;
    return '협의';
  };

  const formatDate = (dateString?: string): string => {
    if (!dateString) return '상시 채용';
    const date = new Date(dateString);
    return date.toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' });
  };

  const parseSkills = (skills?: string): string[] => {
    if (!skills) return [];
    try {
      return JSON.parse(skills);
    } catch {
      return skills.split(',').map(s => s.trim());
    }
  };

  return (
    <Container maxWidth="lg">
      <Typography 
        variant="h3" 
        component="h1" 
        gutterBottom 
        sx={{ textAlign: 'center', mb: 2, fontWeight: 600, fontSize: { xs: '2rem', md: '2.5rem' } }}
      >
        시니어 친화 채용정보
      </Typography>
      
      <Typography 
        variant="h6" 
        color="text.secondary" 
        sx={{ textAlign: 'center', mb: 4, fontSize: '1.2rem' }}
      >
        50대 이상을 우대하는 채용공고를 모아서 보여드립니다
      </Typography>

      {/* 검색 바 */}
      <Box sx={{ mb: 4, display: 'flex', gap: 2 }}>
        <TextField
          fullWidth
          placeholder="회사명, 직무, 키워드로 검색하세요"
          value={searchKeyword}
          onChange={(e) => setSearchKeyword(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Search />
              </InputAdornment>
            ),
            style: { fontSize: '1.1rem' }
          }}
        />
        <Button
          variant="contained"
          onClick={handleSearch}
          disabled={loading}
          sx={{ 
            fontSize: '1.1rem',
            px: 4,
            minWidth: '120px',
            whiteSpace: 'nowrap'
          }}
        >
          검색
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3, fontSize: '1.1rem' }}>
          {error}
        </Alert>
      )}

      {loading ? (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <CircularProgress size={60} />
          <Typography variant="h6" sx={{ mt: 2, fontSize: '1.2rem' }}>
            채용공고를 불러오는 중...
          </Typography>
        </Box>
      ) : (
        <>
          <Typography 
            variant="body1" 
            sx={{ mb: 3, fontSize: '1.1rem', color: 'text.secondary' }}
          >
            총 <strong>{total}</strong>개의 채용공고가 있습니다.
          </Typography>

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            {jobs.map((job) => (
              <Card key={job.id} sx={{ p: 2, '&:hover': { boxShadow: 3 } }}>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Box>
                      <Typography variant="h5" component="h2" gutterBottom sx={{ fontWeight: 600 }}>
                        {job.title}
                      </Typography>
                      <Typography variant="h6" color="primary" gutterBottom>
                        {job.company}
                      </Typography>
                    </Box>
                    {job.employment_type && (
                      <Chip 
                        label={job.employment_type} 
                        color="primary" 
                        sx={{ fontSize: '0.9rem' }}
                      />
                    )}
                  </Box>

                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mb: 2 }}>
                    {job.location && (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <LocationOn color="action" fontSize="small" />
                        <Typography variant="body2" sx={{ fontSize: '1rem' }}>
                          {job.location}
                        </Typography>
                      </Box>
                    )}
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <AttachMoney color="action" fontSize="small" />
                      <Typography variant="body2" sx={{ fontSize: '1rem' }}>
                        {formatSalary(job.salary_min, job.salary_max)}
                      </Typography>
                    </Box>
                    {job.experience_level && (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <TrendingUp color="action" fontSize="small" />
                        <Typography variant="body2" sx={{ fontSize: '1rem' }}>
                          {job.experience_level}
                        </Typography>
                      </Box>
                    )}
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Schedule color="action" fontSize="small" />
                      <Typography variant="body2" sx={{ fontSize: '1rem' }}>
                        마감: {formatDate(job.deadline)}
                      </Typography>
                    </Box>
                  </Box>

                  {job.description && (
                    <Typography 
                      variant="body1" 
                      color="text.secondary" 
                      sx={{ 
                        mb: 2, 
                        fontSize: '1.1rem', 
                        lineHeight: 1.6,
                        display: '-webkit-box',
                        WebkitLineClamp: 3,
                        WebkitBoxOrient: 'vertical',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis'
                      }}
                    >
                      {job.description}
                    </Typography>
                  )}

                  {job.skills_required && parseSkills(job.skills_required).length > 0 && (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 3 }}>
                      {parseSkills(job.skills_required).slice(0, 5).map((skill, index) => (
                        <Chip 
                          key={index}
                          label={skill} 
                          variant="outlined" 
                          size="small"
                          sx={{ fontSize: '0.85rem' }}
                        />
                      ))}
                    </Box>
                  )}

                  <Box sx={{ display: 'flex', gap: 2 }}>
                    <Button
                      variant="contained"
                      startIcon={<Work />}
                      onClick={() => handleApply(job.id)}
                      sx={{ fontSize: '1rem', py: 1.5, px: 3 }}
                    >
                      지원하기
                    </Button>
                    <Button
                      variant="outlined"
                      sx={{ fontSize: '1rem', py: 1.5, px: 3 }}
                    >
                      상세보기
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            ))}
          </Box>

          {/* 페이지네이션 */}
          {total > itemsPerPage && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
              <Pagination
                count={Math.ceil(total / itemsPerPage)}
                page={page}
                onChange={handlePageChange}
                color="primary"
                size="large"
                sx={{ '& .MuiPaginationItem-root': { fontSize: '1.1rem' } }}
              />
            </Box>
          )}
        </>
      )}

      <Box 
        sx={{ 
          textAlign: 'center', 
          mt: 6, 
          py: 4,
          backgroundColor: 'grey.50',
          borderRadius: 2
        }}
      >
        <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
          더 많은 채용정보를 원하시나요?
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3, fontSize: '1.1rem' }}>
          매일 새로운 시니어 친화 채용공고를 업데이트합니다
        </Typography>
        <Button
          variant="outlined"
          size="large"
          sx={{ fontSize: '1.1rem', py: 2, px: 4 }}
        >
          알림 설정하기
        </Button>
      </Box>
    </Container>
  );
};

export default JobListPage;