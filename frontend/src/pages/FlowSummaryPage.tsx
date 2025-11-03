import React from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Button,
  Divider,
  Card,
  CardContent,
  Alert,
  Chip,
  Stack,
} from '@mui/material';
import {
  CheckCircle,
  Download,
  RestartAlt,
  Business,
  Work,
  Article,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAppContext } from '../contexts/AppContext';
import FlowStepIndicator from '../components/FlowStepIndicator';

const FlowSummaryPage: React.FC = () => {
  const navigate = useNavigate();
  const { 
    currentResume, 
    selectedJob, 
    generatedCoverLetter, 
    resetAll,
    currentStep 
  } = useAppContext();

  // 데이터가 없으면 시작 페이지로 리다이렉트
  React.useEffect(() => {
    console.log('=== FlowSummaryPage useEffect ===');
    console.log('currentResume:', currentResume ? '있음' : '없음');
    console.log('selectedJob:', selectedJob ? '있음' : '없음');
    console.log('generatedCoverLetter:', generatedCoverLetter ? '있음' : '없음');
    
    if (!currentResume || !selectedJob || !generatedCoverLetter) {
      console.warn('데이터 누락으로 /resume/create로 리다이렉트합니다.');
      navigate('/resume/create');
    } else {
      console.log('모든 데이터 확인 완료. 페이지를 표시합니다.');
    }
  }, [currentResume, selectedJob, generatedCoverLetter, navigate]);

  const handleDownloadAll = () => {
    if (!generatedCoverLetter || !selectedJob) return;

    // 자기소개서 다운로드
    const blob = new Blob([generatedCoverLetter], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `자기소개서_${selectedJob.company}_${selectedJob.title}_${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleStartNew = () => {
    if (window.confirm('새로운 이력서 작성을 시작하시겠습니까? 현재 데이터는 저장되지 않습니다.')) {
      resetAll();
      navigate('/resume/create');
    }
  };

  if (!currentResume || !selectedJob || !generatedCoverLetter) {
    return null;
  }

  // 이력서 데이터 파싱
  let resumeData: any = {};
  try {
    resumeData = typeof currentResume.content === 'string' 
      ? JSON.parse(currentResume.content) 
      : currentResume.content;
  } catch (e) {
    console.error('이력서 데이터 파싱 오류:', e);
  }

  return (
    <Container maxWidth="lg">
      <FlowStepIndicator currentStep={currentStep} />

      {/* 헤더 */}
      <Box sx={{ textAlign: 'center', mb: 4, mt: 2 }}>
        <CheckCircle sx={{ fontSize: 80, color: 'success.main', mb: 2 }} />
        <Typography 
          variant="h3" 
          component="h1" 
          gutterBottom 
          sx={{ fontWeight: 600, fontSize: { xs: '2rem', md: '2.5rem' } }}
        >
          모든 단계가 완료되었습니다!
        </Typography>
        <Typography variant="h6" color="text.secondary">
          이력서 작성부터 자기소개서 생성까지 성공적으로 완료되었습니다.
        </Typography>
      </Box>

      {/* 완료 상태 안내 */}
      <Alert severity="success" sx={{ mb: 4, fontSize: '1.1rem' }}>
        <Typography variant="body1" sx={{ fontWeight: 'bold', mb: 1 }}>
          🎉 축하합니다! 취업 준비가 한 단계 완료되었습니다.
        </Typography>
        <Typography variant="body2">
          생성된 자기소개서를 다운로드하여 지원서를 제출하세요.
          <br />
          추가로 다른 채용공고에 지원하시려면 이전 페이지로 돌아가 다른 공고를 선택하실 수 있습니다.
        </Typography>
      </Alert>

      {/* 액션 버튼 */}
      <Box sx={{ display: 'flex', gap: 2, mb: 4, justifyContent: 'center', flexWrap: 'wrap' }}>
        <Button
          variant="contained"
          color="primary"
          size="large"
          startIcon={<Download />}
          onClick={handleDownloadAll}
          sx={{ fontSize: '1.1rem', py: 1.5, px: 4 }}
        >
          자기소개서 다운로드
        </Button>
        <Button
          variant="outlined"
          color="primary"
          size="large"
          onClick={() => navigate('/recommendations')}
          sx={{ fontSize: '1.1rem', py: 1.5, px: 4 }}
        >
          다른 공고 보기
        </Button>
        <Button
          variant="outlined"
          color="secondary"
          size="large"
          startIcon={<RestartAlt />}
          onClick={handleStartNew}
          sx={{ fontSize: '1.1rem', py: 1.5, px: 4 }}
        >
          새 이력서 작성
        </Button>
      </Box>

      <Divider sx={{ mb: 4 }} />

      {/* 요약 정보 */}
      <Typography variant="h4" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
        작업 요약
      </Typography>

      <Stack spacing={3}>
        {/* 이력서 정보 */}
        <Card elevation={2}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Article sx={{ fontSize: 32, color: 'primary.main', mr: 2 }} />
              <Typography variant="h5" sx={{ fontWeight: 600 }}>
                1. 이력서 정보
              </Typography>
            </Box>
            <Divider sx={{ mb: 2 }} />
            <Box sx={{ display: 'grid', gridTemplateColumns: '140px 1fr', gap: 2 }}>
              <Typography sx={{ fontWeight: 'bold', fontSize: '1.1rem' }}>이력서 제목</Typography>
              <Typography sx={{ fontSize: '1.1rem' }}>{currentResume.title}</Typography>
              
              <Typography sx={{ fontWeight: 'bold', fontSize: '1.1rem' }}>이름</Typography>
              <Typography sx={{ fontSize: '1.1rem' }}>
                {resumeData?.기본정보?.이름 || '-'}
              </Typography>
              
              <Typography sx={{ fontWeight: 'bold', fontSize: '1.1rem' }}>연락처</Typography>
              <Typography sx={{ fontSize: '1.1rem' }}>
                {resumeData?.기본정보?.연락처 || '-'}
              </Typography>
              
              <Typography sx={{ fontWeight: 'bold', fontSize: '1.1rem' }}>이메일</Typography>
              <Typography sx={{ fontSize: '1.1rem' }}>
                {resumeData?.기본정보?.이메일 || '-'}
              </Typography>
              
              <Typography sx={{ fontWeight: 'bold', fontSize: '1.1rem' }}>기술스택</Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {resumeData?.['기술스택/자격증']?.기술스택?.length > 0 ? (
                  resumeData['기술스택/자격증'].기술스택.map((skill: string, index: number) => (
                    <Chip key={index} label={skill} size="small" color="primary" variant="outlined" />
                  ))
                ) : (
                  <Typography color="text.secondary">-</Typography>
                )}
              </Box>
            </Box>
          </CardContent>
        </Card>

        {/* 선택된 채용공고 */}
        <Card elevation={2}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Business sx={{ fontSize: 32, color: 'secondary.main', mr: 2 }} />
              <Typography variant="h5" sx={{ fontWeight: 600 }}>
                2. 선택된 채용공고
              </Typography>
            </Box>
            <Divider sx={{ mb: 2 }} />
            <Box sx={{ display: 'grid', gridTemplateColumns: '140px 1fr', gap: 2 }}>
              <Typography sx={{ fontWeight: 'bold', fontSize: '1.1rem' }}>회사명</Typography>
              <Typography sx={{ fontSize: '1.1rem' }}>{selectedJob.company}</Typography>
              
              <Typography sx={{ fontWeight: 'bold', fontSize: '1.1rem' }}>직무</Typography>
              <Typography sx={{ fontSize: '1.1rem' }}>{selectedJob.title}</Typography>
              
              {selectedJob.location && (
                <>
                  <Typography sx={{ fontWeight: 'bold', fontSize: '1.1rem' }}>근무지</Typography>
                  <Typography sx={{ fontSize: '1.1rem' }}>{selectedJob.location}</Typography>
                </>
              )}
              
              {selectedJob.employment_type && (
                <>
                  <Typography sx={{ fontWeight: 'bold', fontSize: '1.1rem' }}>고용형태</Typography>
                  <Typography sx={{ fontSize: '1.1rem' }}>{selectedJob.employment_type}</Typography>
                </>
              )}
              
              {selectedJob.experience_level && (
                <>
                  <Typography sx={{ fontWeight: 'bold', fontSize: '1.1rem' }}>경력</Typography>
                  <Typography sx={{ fontSize: '1.1rem' }}>{selectedJob.experience_level}</Typography>
                </>
              )}
            </Box>
          </CardContent>
        </Card>

        {/* 생성된 자기소개서 */}
        <Card elevation={2}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Work sx={{ fontSize: 32, color: 'success.main', mr: 2 }} />
              <Typography variant="h5" sx={{ fontWeight: 600 }}>
                3. 생성된 자기소개서
              </Typography>
            </Box>
            <Divider sx={{ mb: 2 }} />
            <Paper 
              sx={{ 
                p: 3, 
                bgcolor: '#f5f5f5',
                maxHeight: '500px',
                overflow: 'auto'
              }}
            >
              <Typography
                variant="body1"
                sx={{
                  whiteSpace: 'pre-wrap',
                  lineHeight: 1.8,
                  fontSize: '1.1rem',
                }}
              >
                {generatedCoverLetter}
              </Typography>
            </Paper>
            <Box sx={{ mt: 2, textAlign: 'right' }}>
              <Typography variant="caption" color="text.secondary">
                글자 수: {generatedCoverLetter.length}자
              </Typography>
            </Box>
          </CardContent>
        </Card>
      </Stack>

      {/* 하단 액션 버튼 */}
      <Box sx={{ mt: 4, mb: 4, textAlign: 'center' }}>
        <Button
          variant="contained"
          color="success"
          size="large"
          startIcon={<Download />}
          onClick={handleDownloadAll}
          sx={{ fontSize: '1.2rem', py: 2, px: 6 }}
        >
          자기소개서 다운로드
        </Button>
      </Box>

      {/* 추가 안내 */}
      <Alert severity="info" sx={{ mb: 4 }}>
        <Typography variant="body2">
          💡 <strong>팁:</strong> 생성된 자기소개서는 AI가 작성한 초안입니다. 
          실제 지원 시에는 본인의 경험과 생각을 바탕으로 내용을 수정하고 보완하는 것을 권장합니다.
        </Typography>
      </Alert>
    </Container>
  );
};

export default FlowSummaryPage;
