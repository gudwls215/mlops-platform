import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Button,
  Slider,
  FormControl,
  FormLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Chip,
  Paper,
  Divider,
  CircularProgress,
  Alert,
  Stack,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import axios from 'axios';
import { useSearchParams } from 'react-router-dom';
import { useAppContext } from '../contexts/AppContext';
import FlowStepIndicator from '../components/FlowStepIndicator';

interface Recommendation {
  job_id: number;
  title: string;
  company: string;
  hybrid_score: number;
  similarity?: number;
  cf_score?: number;
  strategy: string;
  source?: string;
  final_score?: number;
  diversity_score?: number;
  novelty_score?: number;
  user_novelty?: number;
  recency_factor?: number;
}

interface RecommendationResponse {
  resume_id: number;
  total_count: number;
  strategy: string;
  content_weight: number;
  cf_weight: number;
  recommendations: Recommendation[];
  generated_at: string;
}

interface Resume {
  id: number;
  title: string;
  user_id: number;
  created_at: string;
}

const HybridRecommendationPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const { currentResume, setSelectedJob: setContextSelectedJob, setGeneratedCoverLetter: setContextGeneratedCoverLetter, setCurrentStep, currentStep } = useAppContext();
  const [resumeId, setResumeId] = useState<number | null>(null);
  const [resumeList, setResumeList] = useState<Resume[]>([]);
  const [topN, setTopN] = useState<number>(10);
  const [strategy, setStrategy] = useState<string>('weighted');
  const [contentWeight, setContentWeight] = useState<number>(0.6);
  const [cfWeight, setCfWeight] = useState<number>(0.4);
  
  // 다양성/참신성 파라미터
  const [enableDiversity, setEnableDiversity] = useState<boolean>(false);
  const [diversityWeight, setDiversityWeight] = useState<number>(0.3);
  const [noveltyWeight, setNoveltyWeight] = useState<number>(0.2);
  const [mmrLambda, setMmrLambda] = useState<number>(0.7);
  
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [loadingResumes, setLoadingResumes] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [responseInfo, setResponseInfo] = useState<any>(null);
  
  // 자기소개서 생성 관련 상태
  const [coverLetterModalOpen, setCoverLetterModalOpen] = useState<boolean>(false);
  const [generatingCoverLetter, setGeneratingCoverLetter] = useState<boolean>(false);
  const [selectedJob, setSelectedJob] = useState<Recommendation | null>(null);
  const [generatedCoverLetter, setGeneratedCoverLetter] = useState<string>('');

  // 이력서 리스트 불러오기 (user_id=1)
  useEffect(() => {
    const fetchResumes = async () => {
      setLoadingResumes(true);
      try {
        const response = await axios.get(
          `http://192.168.0.147:9000/api/v1/resume/`,
          { params: { user_id: 1 } }
        );
        const resumes = response.data.data?.resumes || [];
        setResumeList(resumes);
      } catch (err: any) {
        console.error('이력서 리스트 조회 오류:', err);
      } finally {
        setLoadingResumes(false);
      }
    };
    
    fetchResumes();
  }, []);

  // URL 파라미터에서 resumeId 가져오기 및 자동 추천
  useEffect(() => {
    const resumeIdParam = searchParams.get('resumeId');
    if (resumeIdParam) {
      const id = parseInt(resumeIdParam, 10);
      if (!isNaN(id)) {
        setResumeId(id);
        setCurrentStep(2); // 추천 단계
        // resumeId가 설정되면 자동으로 추천 가져오기
        const fetchData = async () => {
          await fetchRecommendationsWithId(id);
        };
        fetchData();
      }
    } else if (currentResume) {
      // Context에서 이력서 정보 가져오기
      setResumeId(currentResume.id);
      const fetchData = async () => {
        await fetchRecommendationsWithId(currentResume.id);
      };
      fetchData();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams, currentResume]);

  // 가중치 자동 조정
  useEffect(() => {
    if (!enableDiversity) {
      setCfWeight(1.0 - contentWeight);
    } else {
      const relevanceWeight = 1.0 - diversityWeight - noveltyWeight;
      if (relevanceWeight < 0) {
        setDiversityWeight(0.5);
        setNoveltyWeight(0.3);
      }
    }
  }, [contentWeight, diversityWeight, noveltyWeight, enableDiversity]);

  const fetchRecommendationsWithId = async (id: number) => {
    setLoading(true);
    setError('');
    
    try {
      const params: any = {
        top_n: topN,
        strategy: strategy,
        content_weight: contentWeight,
        cf_weight: cfWeight,
      };
      
      if (enableDiversity) {
        params.enable_diversity = true;
        params.diversity_weight = diversityWeight;
        params.novelty_weight = noveltyWeight;
        params.mmr_lambda = mmrLambda;
      }
      
      const response = await axios.get<RecommendationResponse>(
        `http://192.168.0.147:9000/api/hybrid-recommendations/jobs/${id}`,
        { params }
      );
      
      setRecommendations(response.data.recommendations);
      setResponseInfo(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || '추천 조회 중 오류가 발생했습니다.');
      console.error('Error fetching recommendations:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchRecommendations = async () => {
    if (resumeId === null) {
      setError('이력서를 선택해주세요.');
      return;
    }
    await fetchRecommendationsWithId(resumeId);
  };

  const handleGenerateCoverLetter = async (job: Recommendation) => {
    if (!resumeId) {
      setError('이력서를 먼저 선택해주세요.');
      return;
    }

    setSelectedJob(job);
    setCoverLetterModalOpen(true);
    setGeneratingCoverLetter(true);
    setGeneratedCoverLetter('');

    try {
      // 1. 이력서 데이터 조회
      const resumeResponse = await axios.get(
        `http://192.168.0.147:9000/api/v1/resume/${resumeId}`
      );
      
      // 2. 채용공고 데이터 조회
      const jobResponse = await axios.get(
        `http://192.168.0.147:9000/api/v1/job/${job.job_id}`
      );

      // 3. 자기소개서 생성 API 호출
      const formData = new FormData();
      formData.append('resume_data', resumeResponse.data.data?.content || '{}');
      formData.append('job_posting_data', JSON.stringify({
        title: jobResponse.data.data?.title || job.title,
        company: jobResponse.data.data?.company || job.company,
        description: jobResponse.data.data?.description || '',
        requirements: jobResponse.data.data?.requirements || '',
      }));
      formData.append('tone', 'professional');

      const coverLetterResponse = await axios.post(
        `http://192.168.0.147:9000/api/cover-letter/generate`,
        formData
      );

      const coverLetterContent = coverLetterResponse.data.content || coverLetterResponse.data.data?.content || '자기소개서 생성 완료';
      setGeneratedCoverLetter(coverLetterContent);
      
      // Context에 자기소개서와 선택된 채용공고 저장
      setContextGeneratedCoverLetter(coverLetterContent);
      setContextSelectedJob({
        id: job.job_id,
        title: job.title,
        company: job.company,
        description: jobResponse.data.data?.description || '',
        requirements: jobResponse.data.data?.requirements || '',
        location: jobResponse.data.data?.location,
        employment_type: jobResponse.data.data?.employment_type,
        experience_level: jobResponse.data.data?.experience_level,
      });
      setCurrentStep(3); // 자기소개서 생성 완료
      
    } catch (err: any) {
      console.error('자기소개서 생성 오류:', err);
      setError(err.response?.data?.error || err.response?.data?.detail || '자기소개서 생성 중 오류가 발생했습니다.');
      setGeneratedCoverLetter('자기소개서 생성에 실패했습니다. 다시 시도해주세요.');
    } finally {
      setGeneratingCoverLetter(false);
    }
  };

  const handleCloseCoverLetterModal = () => {
    setCoverLetterModalOpen(false);
    setSelectedJob(null);
    setGeneratedCoverLetter('');
  };

  const handleDownloadCoverLetter = () => {
    if (!generatedCoverLetter || !selectedJob) return;

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

  const getScoreColor = (score: number): string => {
    if (score >= 0.7) return '#4caf50';
    if (score >= 0.5) return '#ff9800';
    return '#f44336';
  };

  const renderScoreBar = (score: number, label: string) => {
    return (
      <Box sx={{ mb: 1 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
          <Typography variant="caption" color="text.secondary">
            {label}
          </Typography>
          <Typography variant="caption" fontWeight="bold">
            {(score * 100).toFixed(1)}%
          </Typography>
        </Box>
        <Box
          sx={{
            width: '100%',
            height: 8,
            bgcolor: '#e0e0e0',
            borderRadius: 1,
            overflow: 'hidden',
          }}
        >
          <Box
            sx={{
              width: `${score * 100}%`,
              height: '100%',
              bgcolor: getScoreColor(score),
              transition: 'width 0.3s ease',
            }}
          />
        </Box>
      </Box>
    );
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <FlowStepIndicator currentStep={currentStep} />
      
      <Typography variant="h4" gutterBottom fontWeight="bold">
        AI 채용공고 추천
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        하이브리드 추천 시스템: Content-based + Collaborative Filtering + 다양성/참신성
      </Typography>

      {/* 플로우 완료 상태 표시 (자기소개서 생성 완료 시) */}
      {currentStep === 3 && generatedCoverLetter && (
        <Alert severity="success" sx={{ mb: 3 }}>
          <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1 }}>
            ✅ 모든 단계가 완료되었습니다!
          </Typography>
          <Typography variant="body2">
            이력서 작성 → 채용공고 추천 → 자기소개서 생성이 모두 완료되었습니다.
            <br />
            원하시는 경우 다른 채용공고에 대해서도 자기소개서를 생성할 수 있습니다.
          </Typography>
        </Alert>
      )}

      <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 3 }}>
        {/* 왼쪽: 설정 패널 */}
        <Box sx={{ flex: { xs: '1', md: '0 0 33%' } }}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              추천 설정
            </Typography>
            <Divider sx={{ mb: 2 }} />

            <Stack spacing={2}>
              <FormControl fullWidth>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <FormLabel>이력서 선택</FormLabel>
                  {resumeId && (
                    <Chip 
                      label={`선택: #${resumeId}`} 
                      size="small" 
                      color="primary" 
                      variant="outlined"
                    />
                  )}
                </Box>
                <Select
                  value={resumeId || ''}
                  onChange={(e) => setResumeId(Number(e.target.value))}
                  size="small"
                  disabled={loadingResumes}
                  displayEmpty
                >
                  {loadingResumes ? (
                    <MenuItem value="">
                      <em>로딩 중...</em>
                    </MenuItem>
                  ) : resumeList.length === 0 ? (
                    <MenuItem value="">
                      <em>이력서가 없습니다</em>
                    </MenuItem>
                  ) : (
                    [
                      <MenuItem key="placeholder" value="" disabled>
                        <em>이력서를 선택하세요</em>
                      </MenuItem>,
                      ...resumeList.map((resume) => {
                        const date = new Date(resume.created_at);
                        const dateStr = `${date.getMonth() + 1}/${date.getDate()} ${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`;
                        return (
                          <MenuItem key={resume.id} value={resume.id}>
                            #{resume.id} - {resume.title.length > 30 ? resume.title.substring(0, 30) + '...' : resume.title} ({dateStr})
                          </MenuItem>
                        );
                      })
                    ]
                  )}
                </Select>
              </FormControl>

              <FormControl fullWidth>
                <FormLabel>추천 개수: {topN}</FormLabel>
                <Slider
                  value={topN}
                  onChange={(_, value) => setTopN(value as number)}
                  min={5}
                  max={20}
                  step={5}
                  marks
                  valueLabelDisplay="auto"
                />
              </FormControl>

              <FormControl fullWidth>
                <FormLabel>통합 전략</FormLabel>
                <Select
                  value={strategy}
                  onChange={(e) => setStrategy(e.target.value)}
                  size="small"
                >
                  <MenuItem value="weighted">가중치 합산 (Weighted)</MenuItem>
                  <MenuItem value="cascade">캐스케이드 (Cascade)</MenuItem>
                  <MenuItem value="mixed">혼합 (Mixed)</MenuItem>
                </Select>
              </FormControl>

              {!enableDiversity && (
                <>
                  <FormControl fullWidth>
                    <FormLabel>Content-based 가중치: {contentWeight.toFixed(2)}</FormLabel>
                    <Slider
                      value={contentWeight}
                      onChange={(_, value) => setContentWeight(value as number)}
                      min={0}
                      max={1}
                      step={0.1}
                      marks
                      valueLabelDisplay="auto"
                    />
                  </FormControl>

                  <FormControl fullWidth>
                    <FormLabel>CF 가중치: {cfWeight.toFixed(2)}</FormLabel>
                    <Slider
                      value={cfWeight}
                      disabled
                      min={0}
                      max={1}
                      step={0.1}
                      marks
                      valueLabelDisplay="auto"
                    />
                  </FormControl>
                </>
              )}

              <Divider />

              <FormControlLabel
                control={
                  <Switch
                    checked={enableDiversity}
                    onChange={(e) => setEnableDiversity(e.target.checked)}
                    color="primary"
                  />
                }
                label={
                  <Box>
                    <Typography variant="subtitle2">다양성/참신성 활성화</Typography>
                    <Typography variant="caption" color="text.secondary">
                      MMR 알고리즘 적용
                    </Typography>
                  </Box>
                }
              />

              {enableDiversity && (
                <Box sx={{ p: 2, bgcolor: '#f5f5f5', borderRadius: 1 }}>
                  <Stack spacing={2}>
                    <FormControl fullWidth>
                      <FormLabel>다양성 가중치: {diversityWeight.toFixed(2)}</FormLabel>
                      <Slider
                        value={diversityWeight}
                        onChange={(_, value) => setDiversityWeight(value as number)}
                        min={0}
                        max={0.5}
                        step={0.1}
                        marks
                        valueLabelDisplay="auto"
                      />
                      <Typography variant="caption" color="text.secondary">
                        높을수록 다양한 회사/직무 추천
                      </Typography>
                    </FormControl>

                    <FormControl fullWidth>
                      <FormLabel>참신성 가중치: {noveltyWeight.toFixed(2)}</FormLabel>
                      <Slider
                        value={noveltyWeight}
                        onChange={(_, value) => setNoveltyWeight(value as number)}
                        min={0}
                        max={0.5}
                        step={0.1}
                        marks
                        valueLabelDisplay="auto"
                      />
                      <Typography variant="caption" color="text.secondary">
                        높을수록 새로운 공고 우선
                      </Typography>
                    </FormControl>

                    <FormControl fullWidth>
                      <FormLabel>MMR Lambda: {mmrLambda.toFixed(2)}</FormLabel>
                      <Slider
                        value={mmrLambda}
                        onChange={(_, value) => setMmrLambda(value as number)}
                        min={0}
                        max={1}
                        step={0.1}
                        marks
                        valueLabelDisplay="auto"
                      />
                      <Typography variant="caption" color="text.secondary">
                        1.0: 유사도 중시 | 0.0: 다양성 중시
                      </Typography>
                    </FormControl>

                    <Alert severity="info">
                      <Typography variant="caption">
                        연관성 가중치: {(1.0 - diversityWeight - noveltyWeight).toFixed(2)}
                      </Typography>
                    </Alert>
                  </Stack>
                </Box>
              )}

              <Button
                variant="contained"
                fullWidth
                onClick={fetchRecommendations}
                disabled={loading}
                size="large"
              >
                {loading ? <CircularProgress size={24} /> : '추천 받기'}
              </Button>
            </Stack>
          </Paper>
        </Box>

        {/* 오른쪽: 추천 결과 */}
        <Box sx={{ flex: '1' }}>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          {responseInfo && (
            <Paper sx={{ p: 2, mb: 2 }}>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    전략
                  </Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {responseInfo.strategy}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    추천 개수
                  </Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {responseInfo.total_count}개
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Content 가중치
                  </Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {(responseInfo.content_weight * 100).toFixed(0)}%
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    CF 가중치
                  </Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {(responseInfo.cf_weight * 100).toFixed(0)}%
                  </Typography>
                </Box>
              </Box>
            </Paper>
          )}

          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : recommendations.length > 0 ? (
            <Stack spacing={2}>
              {recommendations.map((rec, index) => (
                <Card
                  key={rec.job_id}
                  sx={{
                    border: index < 3 ? '2px solid #1976d2' : '1px solid #e0e0e0',
                    transition: 'transform 0.2s',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: 3,
                    },
                  }}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1, flexWrap: 'wrap', gap: 1 }}>
                      <Chip
                        label={`#${index + 1}`}
                        color={index < 3 ? 'primary' : 'default'}
                        size="small"
                      />
                      <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                        {rec.title}
                      </Typography>
                      <Chip
                        label={rec.company}
                        color="secondary"
                        variant="outlined"
                        size="small"
                      />
                    </Box>

                    <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
                      <Chip label={rec.strategy} size="small" />
                      {rec.source && (
                        <Chip label={rec.source} size="small" variant="outlined" />
                      )}
                    </Box>

                    <Box sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, gap: 2 }}>
                      <Box sx={{ flex: 1 }}>
                        {enableDiversity && rec.final_score !== undefined ? (
                          renderScoreBar(rec.final_score, '최종 점수')
                        ) : (
                          renderScoreBar(rec.hybrid_score, '하이브리드 점수')
                        )}
                        
                        {rec.similarity !== undefined &&
                          renderScoreBar(rec.similarity, 'Content 유사도')}
                        
                        {rec.cf_score !== undefined && rec.cf_score > 0 &&
                          renderScoreBar(rec.cf_score, 'CF 점수')}
                      </Box>

                      {enableDiversity && (
                        <Box sx={{ flex: 1 }}>
                          {rec.diversity_score !== undefined &&
                            renderScoreBar(rec.diversity_score, '다양성')}
                          
                          {rec.novelty_score !== undefined &&
                            renderScoreBar(rec.novelty_score, '참신성')}
                          
                          {rec.user_novelty !== undefined &&
                            renderScoreBar(rec.user_novelty, '사용자 Novelty')}
                          
                          {rec.recency_factor !== undefined &&
                            renderScoreBar(rec.recency_factor, '최신도')}
                        </Box>
                      )}
                    </Box>

                    <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
                      <Button
                        variant="contained"
                        color="primary"
                        onClick={() => handleGenerateCoverLetter(rec)}
                        disabled={!resumeId}
                      >
                        자기소개서 생성
                      </Button>
                    </Box>
                  </CardContent>
                </Card>
              ))}
            </Stack>
          ) : (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <Typography variant="h6" color="text.secondary">
                추천 받기 버튼을 클릭하세요
              </Typography>
            </Paper>
          )}
        </Box>
      </Box>

      {/* 자기소개서 생성 모달 */}
      <Dialog
        open={coverLetterModalOpen}
        onClose={handleCloseCoverLetterModal}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {selectedJob ? `${selectedJob.company} - ${selectedJob.title}` : '자기소개서'}
        </DialogTitle>
        <DialogContent>
          {generatingCoverLetter ? (
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 4 }}>
              <CircularProgress size={60} />
              <Typography variant="h6" sx={{ mt: 2 }}>
                AI가 자기소개서를 생성하고 있습니다...
              </Typography>
            </Box>
          ) : generatedCoverLetter ? (
            <Box sx={{ mt: 2 }}>
              {/* 완료 상태 표시 */}
              <Alert severity="success" sx={{ mb: 3 }}>
                <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1 }}>
                  🎉 모든 단계가 완료되었습니다!
                </Typography>
                <Typography variant="body2">
                  이력서 작성 → 채용공고 추천 → 자기소개서 생성이 모두 완료되었습니다.
                  <br />
                  아래 자기소개서를 확인하고 다운로드하세요.
                </Typography>
              </Alert>

              <Paper sx={{ p: 3, bgcolor: '#f5f5f5' }}>
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
            </Box>
          ) : null}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseCoverLetterModal}>닫기</Button>
          {generatedCoverLetter && !generatingCoverLetter && (
            <>
              <Button
                variant="outlined"
                onClick={handleDownloadCoverLetter}
              >
                다운로드
              </Button>
              <Button
                variant="contained"
                color="success"
                onClick={() => {
                  handleDownloadCoverLetter();
                  handleCloseCoverLetterModal();
                }}
              >
                다운로드 후 완료
              </Button>
            </>
          )}
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default HybridRecommendationPage;
