import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  CircularProgress,
  Alert
} from '@mui/material';
import {
  TrendingUp,
  Error as ErrorIcon,
  Speed,
  CheckCircle
} from '@mui/icons-material';
import axios from 'axios';

interface UsageStats {
  total_requests: number;
  total_errors: number;
  error_rate: number;
  avg_response_time: number;
  total_request_size: number;
  total_response_size: number;
  requests_by_method: { [key: string]: number };
  requests_by_status: { [key: string]: number };
  top_endpoints: { endpoint: string; count: number }[];
}

interface EndpointStats {
  endpoint: string;
  method: string;
  total_requests: number;
  error_count: number;
  avg_response_time: number;
  min_response_time: number;
  max_response_time: number;
}

const MonitoringDashboard: React.FC = () => {
  const [stats, setStats] = useState<UsageStats | null>(null);
  const [endpoints, setEndpoints] = useState<EndpointStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
    // 30초마다 자동 새로고침
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, endpointsRes] = await Promise.all([
        axios.get('http://114.202.2.226:9000/api/monitoring/stats?hours=24'),
        axios.get('http://114.202.2.226:9000/api/monitoring/endpoints?hours=24')
      ]);
      setStats(statsRes.data);
      setEndpoints(endpointsRes.data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || '모니터링 데이터를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ py: 4, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  if (error || !stats) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Alert severity="error">{error || '데이터를 불러올 수 없습니다.'}</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Typography variant="h3" component="h1" gutterBottom sx={{ fontWeight: 600, mb: 4 }}>
        시스템 모니터링 대시보드
      </Typography>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        최근 24시간 데이터 • 자동 새로고침: 30초
      </Typography>

      {/* 주요 지표 카드 */}
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 3, mb: 4 }}>
        <Paper sx={{ p: 3, borderLeft: '4px solid #1976d2' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <TrendingUp sx={{ color: '#1976d2', mr: 1 }} />
            <Typography variant="h6" color="text.secondary">
              총 요청 수
            </Typography>
          </Box>
          <Typography variant="h3" sx={{ fontWeight: 'bold' }}>
            {stats.total_requests.toLocaleString()}
          </Typography>
        </Paper>

        <Paper sx={{ p: 3, borderLeft: '4px solid #d32f2f' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <ErrorIcon sx={{ color: '#d32f2f', mr: 1 }} />
            <Typography variant="h6" color="text.secondary">
              에러율
            </Typography>
          </Box>
          <Typography variant="h3" sx={{ fontWeight: 'bold' }}>
            {stats.error_rate.toFixed(2)}%
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {stats.total_errors}개 에러
          </Typography>
        </Paper>

        <Paper sx={{ p: 3, borderLeft: '4px solid #2e7d32' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <Speed sx={{ color: '#2e7d32', mr: 1 }} />
            <Typography variant="h6" color="text.secondary">
              평균 응답 시간
            </Typography>
          </Box>
          <Typography variant="h3" sx={{ fontWeight: 'bold' }}>
            {stats.avg_response_time.toFixed(2)}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            밀리초
          </Typography>
        </Paper>

        <Paper sx={{ p: 3, borderLeft: '4px solid #ed6c02' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <CheckCircle sx={{ color: '#ed6c02', mr: 1 }} />
            <Typography variant="h6" color="text.secondary">
              성공률
            </Typography>
          </Box>
          <Typography variant="h3" sx={{ fontWeight: 'bold' }}>
            {(100 - stats.error_rate).toFixed(2)}%
          </Typography>
        </Paper>
      </Box>

      {/* 상태 코드별 분포 */}
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 2 }}>
          상태 코드별 요청 분포
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          {Object.entries(stats.requests_by_status).map(([status, count]) => (
            <Chip
              key={status}
              label={`${status}: ${count}`}
              color={status.startsWith('2') ? 'success' : status.startsWith('4') ? 'warning' : 'error'}
              sx={{ fontSize: '1rem', py: 2.5, px: 1 }}
            />
          ))}
        </Box>
      </Paper>

      {/* HTTP 메소드별 분포 */}
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 2 }}>
          HTTP 메소드별 요청 분포
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          {Object.entries(stats.requests_by_method).map(([method, count]) => (
            <Chip
              key={method}
              label={`${method}: ${count}`}
              color="primary"
              variant="outlined"
              sx={{ fontSize: '1rem', py: 2.5, px: 1 }}
            />
          ))}
        </Box>
      </Paper>

      {/* 상위 엔드포인트 */}
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 2 }}>
          가장 많이 호출된 엔드포인트 (TOP 10)
        </Typography>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 'bold' }}>순위</TableCell>
                <TableCell sx={{ fontWeight: 'bold' }}>엔드포인트</TableCell>
                <TableCell align="right" sx={{ fontWeight: 'bold' }}>요청 수</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {stats.top_endpoints.map((item, index) => (
                <TableRow key={index}>
                  <TableCell>{index + 1}</TableCell>
                  <TableCell sx={{ fontFamily: 'monospace' }}>{item.endpoint}</TableCell>
                  <TableCell align="right">{item.count}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* 엔드포인트별 상세 통계 */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 2 }}>
          엔드포인트별 상세 통계
        </Typography>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 'bold' }}>메소드</TableCell>
                <TableCell sx={{ fontWeight: 'bold' }}>엔드포인트</TableCell>
                <TableCell align="right" sx={{ fontWeight: 'bold' }}>요청 수</TableCell>
                <TableCell align="right" sx={{ fontWeight: 'bold' }}>에러 수</TableCell>
                <TableCell align="right" sx={{ fontWeight: 'bold' }}>평균 (ms)</TableCell>
                <TableCell align="right" sx={{ fontWeight: 'bold' }}>최소 (ms)</TableCell>
                <TableCell align="right" sx={{ fontWeight: 'bold' }}>최대 (ms)</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {endpoints.map((endpoint, index) => (
                <TableRow key={index}>
                  <TableCell>
                    <Chip label={endpoint.method} size="small" color="primary" />
                  </TableCell>
                  <TableCell sx={{ fontFamily: 'monospace' }}>{endpoint.endpoint}</TableCell>
                  <TableCell align="right">{endpoint.total_requests}</TableCell>
                  <TableCell align="right">
                    {endpoint.error_count > 0 ? (
                      <Chip label={endpoint.error_count} size="small" color="error" />
                    ) : (
                      <Chip label="0" size="small" color="success" />
                    )}
                  </TableCell>
                  <TableCell align="right">{endpoint.avg_response_time.toFixed(2)}</TableCell>
                  <TableCell align="right">{endpoint.min_response_time.toFixed(2)}</TableCell>
                  <TableCell align="right">{endpoint.max_response_time.toFixed(2)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Container>
  );
};

export default MonitoringDashboard;
