import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  Chip,
  LinearProgress,
  Alert,
  Stack,
  Divider,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  CheckCircle,
  Cancel,
  Refresh,
  SkipNext
} from '@mui/icons-material';
import axios from 'axios';
import { API_BASE_URL } from '../types';

function LabelingPage() {
  const [currentItem, setCurrentItem] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [skippedIds, setSkippedIds] = useState([]);

  // 통계 로드
  const loadStats = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/labeling/stats`);
      setStats(response.data);
    } catch (err) {
      console.error('통계 로드 실패:', err);
    }
  };

  // 다음 자기소개서 로드
  const loadNextItem = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      const skipIdsParam = skippedIds.length > 0 ? `?skip_ids=${skippedIds.join(',')}` : '';
      const response = await axios.get(`${API_BASE_URL}/api/labeling/next${skipIdsParam}`);
      setCurrentItem(response.data);
    } catch (err) {
      if (err.response?.status === 404) {
        setError('라벨링할 자기소개서가 없습니다.');
      } else {
        setError('자기소개서 로드 실패: ' + (err.response?.data?.detail || err.message));
      }
      setCurrentItem(null);
    } finally {
      setLoading(false);
    }
  };

  // 라벨 저장
  const saveLabel = async (isPassed) => {
    if (!currentItem) return;
    
    setLoading(true);
    setError(null);
    
    try {
      await axios.post(`${API_BASE_URL}/api/labeling/label`, {
        cover_letter_id: currentItem.id,
        is_passed: isPassed
      });
      
      setSuccess(`라벨링 완료: ${isPassed ? '합격' : '불합격'}`);
      
      // 통계 업데이트
      await loadStats();
      
      // 다음 항목 로드
      setTimeout(() => {
        setSkippedIds([]);  // 스킵 목록 초기화
        loadNextItem();
      }, 500);
      
    } catch (err) {
      setError('라벨링 실패: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  // 건너뛰기
  const skipItem = () => {
    if (currentItem) {
      setSkippedIds([...skippedIds, currentItem.id]);
      loadNextItem();
    }
  };

  // 초기 로드
  useEffect(() => {
    loadStats();
    loadNextItem();
  }, []);

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom>
        자기소개서 라벨링
      </Typography>
      
      <Typography variant="body1" color="text.secondary" gutterBottom>
        각 자기소개서를 읽고 합격/불합격 여부를 라벨링해주세요.
      </Typography>

      {/* 통계 */}
      {stats && (
        <Paper sx={{ p: 3, mb: 3, mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            진행 현황
          </Typography>
          
          <Box sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="body2">
                {stats.labeled} / {stats.total} 완료
              </Typography>
              <Typography variant="body2">
                {stats.labeling_rate}%
              </Typography>
            </Box>
            <LinearProgress 
              variant="determinate" 
              value={stats.labeling_rate} 
              sx={{ height: 8, borderRadius: 4 }}
            />
          </Box>

          <Grid container spacing={2}>
            <Grid item xs={4}>
              <Card variant="outlined">
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    합격
                  </Typography>
                  <Typography variant="h4" color="success.main">
                    {stats.passed}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={4}>
              <Card variant="outlined">
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    불합격
                  </Typography>
                  <Typography variant="h4" color="error.main">
                    {stats.failed}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={4}>
              <Card variant="outlined">
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    미라벨
                  </Typography>
                  <Typography variant="h4" color="warning.main">
                    {stats.unlabeled}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* 에러/성공 메시지 */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
      
      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      {/* 자기소개서 내용 */}
      {currentItem && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Box sx={{ mb: 3 }}>
            <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
              <Chip label={`ID: ${currentItem.id}`} size="small" />
              <Chip label={currentItem.company} color="primary" size="small" />
              <Chip label={currentItem.position} color="secondary" size="small" />
            </Stack>
            
            <Typography variant="h5" gutterBottom>
              {currentItem.title}
            </Typography>
            
            <Divider sx={{ my: 2 }} />
            
            <Typography 
              variant="body1" 
              sx={{ 
                whiteSpace: 'pre-wrap',
                lineHeight: 1.8,
                fontSize: '1.1rem'
              }}
            >
              {currentItem.content}
            </Typography>
          </Box>

          {/* 라벨링 버튼 */}
          <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mt: 4 }}>
            <Button
              variant="contained"
              color="error"
              size="large"
              startIcon={<Cancel />}
              onClick={() => saveLabel(false)}
              disabled={loading}
              sx={{ minWidth: 150, py: 1.5 }}
            >
              불합격
            </Button>
            
            <Button
              variant="outlined"
              color="inherit"
              size="large"
              startIcon={<SkipNext />}
              onClick={skipItem}
              disabled={loading}
              sx={{ minWidth: 120, py: 1.5 }}
            >
              건너뛰기
            </Button>
            
            <Button
              variant="contained"
              color="success"
              size="large"
              startIcon={<CheckCircle />}
              onClick={() => saveLabel(true)}
              disabled={loading}
              sx={{ minWidth: 150, py: 1.5 }}
            >
              합격
            </Button>
          </Box>

          {/* 하단 네비게이션 */}
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
            <Tooltip title="새로고침">
              <IconButton onClick={loadNextItem} disabled={loading}>
                <Refresh />
              </IconButton>
            </Tooltip>
          </Box>
        </Paper>
      )}

      {/* 로딩 */}
      {loading && !currentItem && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <Typography>로딩 중...</Typography>
        </Box>
      )}

      {/* 안내 */}
      <Paper sx={{ p: 3, bgcolor: 'info.light' }}>
        <Typography variant="h6" gutterBottom>
          라벨링 가이드
        </Typography>
        <Typography variant="body2" component="div">
          <ul>
            <li><strong>합격</strong>: 실제로 합격한 자기소개서이거나, 내용이 우수하여 합격 가능성이 높은 경우</li>
            <li><strong>불합격</strong>: 실제로 불합격한 자기소개서이거나, 내용이 부족하여 합격 가능성이 낮은 경우</li>
            <li><strong>건너뛰기</strong>: 판단이 어렵거나 나중에 다시 라벨링하고 싶은 경우</li>
          </ul>
          <Typography variant="caption" color="text.secondary">
            목표: 최소 1,000건 라벨링 (합격 500건 + 불합격 500건)
          </Typography>
        </Typography>
      </Paper>
    </Container>
  );
}

export default LabelingPage;
