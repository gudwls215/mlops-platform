import React from 'react';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  Chip,
  Button,
} from '@mui/material';
import { Work, LocationOn, AttachMoney, Schedule } from '@mui/icons-material';

// 임시 채용공고 데이터
const sampleJobs = [
  {
    id: 1,
    title: '시니어 백엔드 개발자',
    company: 'ABC 기술',
    location: '서울 강남구',
    salary: '4,000만원 ~ 6,000만원',
    type: '정규직',
    tags: ['Python', 'Java', 'Spring', '5년 이상'],
    description: '경험 많은 백엔드 개발자를 모집합니다. 장년층 우대합니다.',
    deadline: '2025-01-15'
  },
  {
    id: 2,
    title: '데이터 분석가',
    company: 'XYZ 데이터',
    location: '서울 서초구',
    salary: '3,500만원 ~ 5,000만원',
    type: '정규직',
    tags: ['Python', 'SQL', 'Pandas', '통계'],
    description: '데이터 분석 및 인사이트 도출 업무를 담당하실 분을 모집합니다.',
    deadline: '2025-01-20'
  },
  {
    id: 3,
    title: '프로젝트 매니저',
    company: 'DEF 컨설팅',
    location: '서울 중구',
    salary: '5,000만원 ~ 7,000만원',
    type: '정규직',
    tags: ['PMP', '프로젝트 관리', '팀 리더십', '시니어'],
    description: 'IT 프로젝트 관리 전문가를 모집합니다. 경력자 우대합니다.',
    deadline: '2025-01-25'
  },
  {
    id: 4,
    title: '회계 담당자',
    company: 'GHI 회계법인',
    location: '서울 영등포구',
    salary: '3,000만원 ~ 4,500만원',
    type: '정규직',
    tags: ['회계', '세무', '전산회계', '경력자'],
    description: '회계 업무 경험이 풍부한 시니어 인재를 모집합니다.',
    deadline: '2025-02-01'
  }
];

const JobListPage: React.FC = () => {
  const handleApply = (jobId: number) => {
    console.log(`채용공고 ${jobId}에 지원`);
    // TODO: 지원 로직 구현
  };

  return (
    <Container maxWidth="lg">
      <Typography 
        variant="h3" 
        component="h1" 
        gutterBottom 
        sx={{ textAlign: 'center', mb: 2, fontWeight: 600 }}
      >
        시니어 친화 채용정보
      </Typography>
      
      <Typography 
        variant="h6" 
        color="text.secondary" 
        sx={{ textAlign: 'center', mb: 6, fontSize: '1.2rem' }}
      >
        50대 이상을 우대하는 채용공고를 모아서 보여드립니다
      </Typography>

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {sampleJobs.map((job) => (
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
                <Chip 
                  label={job.type} 
                  color="primary" 
                  sx={{ fontSize: '0.9rem' }}
                />
              </Box>

              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <LocationOn color="action" fontSize="small" />
                  <Typography variant="body2" sx={{ fontSize: '1rem' }}>
                    {job.location}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <AttachMoney color="action" fontSize="small" />
                  <Typography variant="body2" sx={{ fontSize: '1rem' }}>
                    {job.salary}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Schedule color="action" fontSize="small" />
                  <Typography variant="body2" sx={{ fontSize: '1rem' }}>
                    마감: {job.deadline}
                  </Typography>
                </Box>
              </Box>

              <Typography 
                variant="body1" 
                color="text.secondary" 
                sx={{ mb: 2, fontSize: '1.1rem', lineHeight: 1.6 }}
              >
                {job.description}
              </Typography>

              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 3 }}>
                {job.tags.map((tag, index) => (
                  <Chip 
                    key={index}
                    label={tag} 
                    variant="outlined" 
                    size="small"
                    sx={{ fontSize: '0.85rem' }}
                  />
                ))}
              </Box>

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