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
} from '@mui/material';
import axios from 'axios';

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

const HybridRecommendationPage: React.FC = () => {
  const [resumeId, setResumeId] = useState<number>(1);
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
  const [error, setError] = useState<string>('');
  const [responseInfo, setResponseInfo] = useState<any>(null);

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

  const fetchRecommendations = async () => {
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
        `http://192.168.0.147:9000/api/hybrid-recommendations/jobs/${resumeId}`,
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
      <Typography variant="h4" gutterBottom fontWeight="bold">
        AI 채용공고 추천
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        하이브리드 추천 시스템: Content-based + Collaborative Filtering + 다양성/참신성
      </Typography>

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
                <FormLabel>이력서 ID</FormLabel>
                <Select
                  value={resumeId}
                  onChange={(e) => setResumeId(Number(e.target.value))}
                  size="small"
                >
                  {[1, 2, 3, 4, 5].map((id) => (
                    <MenuItem key={id} value={id}>
                      이력서 {id}
                    </MenuItem>
                  ))}
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
    </Container>
  );
};

export default HybridRecommendationPage;
