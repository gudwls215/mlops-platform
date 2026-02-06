import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Paper,
  Divider,
  Tooltip
} from '@mui/material';
import {
  Visibility,
  Delete,
  Edit,
  Add,
  Person,
  Email,
  Phone,
  Work,
  School,
  Code,
  CalendarToday,
  Close,
  Description
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { API_BASE_URL, Resume } from '../types';

interface ResumeDetail {
  id: number;
  user_id: number;
  title: string;
  content: string | object;
  skills: string[];
  created_at: string;
  updated_at: string;
  has_embedding: boolean;
}

interface ResumeListItem {
  id: number;
  user_id: number;
  title: string;
  created_at: string;
  updated_at: string;
}

const ResumeListPage: React.FC = () => {
  const navigate = useNavigate();
  const [resumes, setResumes] = useState<ResumeListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedResume, setSelectedResume] = useState<ResumeDetail | null>(null);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [resumeToDelete, setResumeToDelete] = useState<number | null>(null);

  useEffect(() => {
    fetchResumes();
  }, []);

  const fetchResumes = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.get(`${API_BASE_URL}/api/v1/resume/?user_id=1`);
      
      if (response.data.status === 'success') {
        setResumes(response.data.data.resumes || []);
      } else {
        setError('이력서 목록을 불러오는데 실패했습니다.');
      }
    } catch (err: any) {
      console.error('이력서 목록 조회 오류:', err);
      setError(err.response?.data?.error || '이력서 목록을 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const fetchResumeDetail = async (resumeId: number) => {
    setDetailLoading(true);
    
    try {
      const response = await axios.get(`${API_BASE_URL}/api/v1/resume/${resumeId}`);
      
      if (response.data.status === 'success') {
        setSelectedResume(response.data.data);
        setDetailDialogOpen(true);
      } else {
        setError('이력서 상세 정보를 불러오는데 실패했습니다.');
      }
    } catch (err: any) {
      console.error('이력서 상세 조회 오류:', err);
      setError(err.response?.data?.error || '이력서 상세 정보를 불러오는데 실패했습니다.');
    } finally {
      setDetailLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!resumeToDelete) return;
    
    try {
      await axios.delete(`${API_BASE_URL}/api/v1/resume/${resumeToDelete}`);
      setResumes(prev => prev.filter(r => r.id !== resumeToDelete));
      setDeleteConfirmOpen(false);
      setResumeToDelete(null);
    } catch (err: any) {
      console.error('이력서 삭제 오류:', err);
      setError(err.response?.data?.error || '이력서 삭제에 실패했습니다.');
    }
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const parseResumeContent = (content: string | object): object => {
    if (typeof content === 'object') return content;
    try {
      return JSON.parse(content);
    } catch {
      return { raw: content };
    }
  };

  const renderResumeContent = (resume: ResumeDetail) => {
    const content = parseResumeContent(resume.content);
    
    // 한글 키 지원 (API 응답 구조)
    const 기본정보 = (content as any).기본정보 || (content as any).basicInfo;
    const 경력정보 = (content as any).경력정보 || (content as any).careerInfo || [];
    const 학력정보 = (content as any).학력정보 || (content as any).educationInfo;
    const 기술자격 = (content as any)['기술스택/자격증'] || (content as any).skillsCertifications;
    const 자기소개 = (content as any).자기소개 || (content as any).selfIntroduction;
    
    // 영문 키 호환 (기존 데이터 지원)
    const hasEnglishKeys = (content as any).name || (content as any).career;
    
    return (
      <Box sx={{ mt: 2 }}>
        {/* 기본 정보 - 한글 키 */}
        {기본정보 && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Person color="primary" />
              기본 정보
            </Typography>
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 2 }}>
                {기본정보.이름 && (
                  <Box>
                    <Typography variant="body2" color="text.secondary">이름</Typography>
                    <Typography variant="body1" fontWeight={500}>{기본정보.이름}</Typography>
                  </Box>
                )}
                {기본정보.이메일 && (
                  <Box>
                    <Typography variant="body2" color="text.secondary">이메일</Typography>
                    <Typography variant="body1">{기본정보.이메일}</Typography>
                  </Box>
                )}
                {기본정보.연락처 && (
                  <Box>
                    <Typography variant="body2" color="text.secondary">연락처</Typography>
                    <Typography variant="body1">{기본정보.연락처}</Typography>
                  </Box>
                )}
                {기본정보.주소 && (
                  <Box>
                    <Typography variant="body2" color="text.secondary">주소</Typography>
                    <Typography variant="body1">{기본정보.주소}</Typography>
                  </Box>
                )}
              </Box>
            </Paper>
          </Box>
        )}

        {/* 기본 정보 - 영문 키 (기존 데이터 호환) */}
        {hasEnglishKeys && (content as any).name && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Person color="primary" />
              기본 정보
            </Typography>
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 2 }}>
                {(content as any).name && (
                  <Box>
                    <Typography variant="body2" color="text.secondary">이름</Typography>
                    <Typography variant="body1" fontWeight={500}>{(content as any).name}</Typography>
                  </Box>
                )}
                {(content as any).email && (
                  <Box>
                    <Typography variant="body2" color="text.secondary">이메일</Typography>
                    <Typography variant="body1">{(content as any).email}</Typography>
                  </Box>
                )}
                {(content as any).phone && (
                  <Box>
                    <Typography variant="body2" color="text.secondary">연락처</Typography>
                    <Typography variant="body1">{(content as any).phone}</Typography>
                  </Box>
                )}
                {(content as any).address && (
                  <Box>
                    <Typography variant="body2" color="text.secondary">주소</Typography>
                    <Typography variant="body1">{(content as any).address}</Typography>
                  </Box>
                )}
              </Box>
            </Paper>
          </Box>
        )}

        {/* 경력 정보 - 한글 키 (배열) */}
        {경력정보 && 경력정보.length > 0 && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Work color="primary" />
              경력 사항
            </Typography>
            {경력정보.map((career: any, index: number) => (
              <Paper key={index} variant="outlined" sx={{ p: 2, mb: index < 경력정보.length - 1 ? 2 : 0 }}>
                <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 2, mb: 2 }}>
                  {career.회사명 && (
                    <Box>
                      <Typography variant="body2" color="text.secondary">회사명</Typography>
                      <Typography variant="body1" fontWeight={500}>{career.회사명}</Typography>
                    </Box>
                  )}
                  {career.직위 && (
                    <Box>
                      <Typography variant="body2" color="text.secondary">직위</Typography>
                      <Typography variant="body1">{career.직위}</Typography>
                    </Box>
                  )}
                  {career.재직기간 && (
                    <Box>
                      <Typography variant="body2" color="text.secondary">재직기간</Typography>
                      <Typography variant="body1">{career.재직기간}</Typography>
                    </Box>
                  )}
                </Box>
                {career.담당업무 && (
                  <Box sx={{ mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">담당업무</Typography>
                    <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>{career.담당업무}</Typography>
                  </Box>
                )}
                {career.주요성과 && (
                  <Box>
                    <Typography variant="body2" color="text.secondary">주요성과</Typography>
                    <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', color: 'primary.main' }}>{career.주요성과}</Typography>
                  </Box>
                )}
              </Paper>
            ))}
          </Box>
        )}

        {/* 경력 사항 - 영문 키 (기존 데이터 호환) */}
        {hasEnglishKeys && (content as any).career && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Work color="primary" />
              경력 사항
            </Typography>
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography 
                variant="body1" 
                sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.8 }}
              >
                {(content as any).career}
              </Typography>
            </Paper>
          </Box>
        )}

        {/* 학력 정보 - 한글 키 */}
        {학력정보 && (학력정보.학교명 || 학력정보.전공 || 학력정보.졸업연도 || 학력정보.학위) && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <School color="primary" />
              학력
            </Typography>
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 2 }}>
                {학력정보.학교명 && (
                  <Box>
                    <Typography variant="body2" color="text.secondary">학교명</Typography>
                    <Typography variant="body1" fontWeight={500}>{학력정보.학교명}</Typography>
                  </Box>
                )}
                {학력정보.전공 && (
                  <Box>
                    <Typography variant="body2" color="text.secondary">전공</Typography>
                    <Typography variant="body1">{학력정보.전공}</Typography>
                  </Box>
                )}
                {학력정보.졸업연도 && (
                  <Box>
                    <Typography variant="body2" color="text.secondary">졸업연도</Typography>
                    <Typography variant="body1">{학력정보.졸업연도}</Typography>
                  </Box>
                )}
                {학력정보.학위 && (
                  <Box>
                    <Typography variant="body2" color="text.secondary">학위</Typography>
                    <Typography variant="body1">{학력정보.학위}</Typography>
                  </Box>
                )}
              </Box>
            </Paper>
          </Box>
        )}

        {/* 학력 - 영문 키 (기존 데이터 호환) */}
        {hasEnglishKeys && (content as any).education && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <School color="primary" />
              학력
            </Typography>
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography 
                variant="body1" 
                sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.8 }}
              >
                {(content as any).education}
              </Typography>
            </Paper>
          </Box>
        )}

        {/* 기술 스택 / 자격증 - 한글 키 */}
        {기술자격 && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Code color="primary" />
              기술 스택 / 자격증
            </Typography>
            <Paper variant="outlined" sx={{ p: 2 }}>
              {기술자격.기술스택 && 기술자격.기술스택.length > 0 && (
                <Box sx={{ mb: 기술자격.자격증?.length > 0 ? 2 : 0 }}>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>기술 스택</Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {기술자격.기술스택.map((skill: string, index: number) => (
                      <Chip 
                        key={index} 
                        label={skill} 
                        color="primary" 
                        variant="outlined"
                        size="medium"
                      />
                    ))}
                  </Box>
                </Box>
              )}
              {기술자격.자격증 && 기술자격.자격증.length > 0 && (
                <Box>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>자격증</Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {기술자격.자격증.map((cert: string, index: number) => (
                      <Chip 
                        key={index} 
                        label={cert} 
                        color="secondary" 
                        variant="outlined"
                        size="medium"
                      />
                    ))}
                  </Box>
                </Box>
              )}
            </Paper>
          </Box>
        )}

        {/* 기술 스택 - resume.skills 배열 사용 (fallback) */}
        {!기술자격 && resume.skills?.length > 0 && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Code color="primary" />
              기술 스택
            </Typography>
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {resume.skills.map((skill, index) => (
                  <Chip 
                    key={index} 
                    label={skill} 
                    color="primary" 
                    variant="outlined"
                    size="medium"
                  />
                ))}
              </Box>
            </Paper>
          </Box>
        )}

        {/* 자기소개 - 한글 키 */}
        {자기소개 && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Description color="primary" />
              자기소개
            </Typography>
            <Paper variant="outlined" sx={{ p: 2, backgroundColor: 'primary.50' }}>
              <Typography 
                variant="body1" 
                sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.8 }}
              >
                {자기소개}
              </Typography>
            </Paper>
          </Box>
        )}

        {/* 경험/프로젝트 - 영문 키 (기존 데이터 호환) */}
        {hasEnglishKeys && (content as any).experience && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Description color="primary" />
              경험 / 프로젝트
            </Typography>
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography 
                variant="body1" 
                sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.8 }}
              >
                {(content as any).experience}
              </Typography>
            </Paper>
          </Box>
        )}

        {/* 음성 녹음 원본 (있는 경우) */}
        {(content as any).raw_transcript && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              🎤 음성 녹음 원본
            </Typography>
            <Paper variant="outlined" sx={{ p: 2, backgroundColor: 'grey.50' }}>
              <Typography 
                variant="body1" 
                sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.8 }}
              >
                {(content as any).raw_transcript}
              </Typography>
            </Paper>
          </Box>
        )}

        {/* 기타 원본 내용 (파싱되지 않은 경우) */}
        {(content as any).raw && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              원본 내용
            </Typography>
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography 
                variant="body1" 
                sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.8 }}
              >
                {(content as any).raw}
              </Typography>
            </Paper>
          </Box>
        )}
      </Box>
    );
  };

  if (loading) {
    return (
      <Container maxWidth="lg">
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
          <CircularProgress size={60} />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg">
      <Box sx={{ py: 4 }}>
        {/* 헤더 */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
          <Box>
            <Typography variant="h4" component="h1" gutterBottom fontWeight={600}>
              📄 내 이력서 목록
            </Typography>
            <Typography variant="body1" color="text.secondary">
              작성한 이력서를 확인하고 관리하세요
            </Typography>
          </Box>
          <Button
            variant="contained"
            size="large"
            startIcon={<Add />}
            onClick={() => navigate('/resume/create')}
            sx={{ minHeight: 56 }}
          >
            새 이력서 작성
          </Button>
        </Box>

        {/* 에러 메시지 */}
        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* 이력서 목록 */}
        {resumes.length === 0 ? (
          <Paper sx={{ p: 6, textAlign: 'center' }}>
            <Description sx={{ fontSize: 80, color: 'grey.400', mb: 2 }} />
            <Typography variant="h5" gutterBottom color="text.secondary">
              작성된 이력서가 없습니다
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
              새 이력서를 작성해보세요. 음성으로도 간편하게 작성할 수 있습니다.
            </Typography>
            <Button
              variant="contained"
              size="large"
              startIcon={<Add />}
              onClick={() => navigate('/resume/create')}
            >
              이력서 작성하기
            </Button>
          </Paper>
        ) : (
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: '1fr 1fr 1fr' }, gap: 3 }}>
            {resumes.map((resume) => (
              <Box key={resume.id}>
                <Card 
                  sx={{ 
                    height: '100%', 
                    display: 'flex', 
                    flexDirection: 'column',
                    transition: 'transform 0.2s, box-shadow 0.2s',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: 4
                    }
                  }}
                >
                  <CardContent sx={{ flexGrow: 1 }}>
                    <Typography 
                      variant="h6" 
                      component="h2" 
                      gutterBottom
                      sx={{ 
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap'
                      }}
                    >
                      {resume.title}
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, color: 'text.secondary' }}>
                      <CalendarToday fontSize="small" />
                      <Typography variant="body2">
                        {formatDate(resume.created_at)}
                      </Typography>
                    </Box>
                    {resume.updated_at && resume.updated_at !== resume.created_at && (
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                        수정: {formatDate(resume.updated_at)}
                      </Typography>
                    )}
                  </CardContent>
                  <Divider />
                  <CardActions sx={{ justifyContent: 'space-between', px: 2, py: 1.5 }}>
                    <Button
                      size="medium"
                      startIcon={detailLoading ? <CircularProgress size={16} /> : <Visibility />}
                      onClick={() => fetchResumeDetail(resume.id)}
                      disabled={detailLoading}
                    >
                      상세보기
                    </Button>
                    <Tooltip title="삭제">
                      <IconButton
                        color="error"
                        onClick={() => {
                          setResumeToDelete(resume.id);
                          setDeleteConfirmOpen(true);
                        }}
                      >
                        <Delete />
                      </IconButton>
                    </Tooltip>
                  </CardActions>
                </Card>
              </Box>
            ))}
          </Box>
        )}

        {/* 상세보기 다이얼로그 */}
        <Dialog
          open={detailDialogOpen}
          onClose={() => setDetailDialogOpen(false)}
          maxWidth="md"
          fullWidth
          PaperProps={{
            sx: { minHeight: '60vh' }
          }}
        >
          {selectedResume && (
            <>
              <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                  <Typography variant="h5" component="span" fontWeight={600}>
                    {selectedResume.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                    작성일: {formatDate(selectedResume.created_at)}
                  </Typography>
                </Box>
                <IconButton onClick={() => setDetailDialogOpen(false)}>
                  <Close />
                </IconButton>
              </DialogTitle>
              <DialogContent dividers>
                {renderResumeContent(selectedResume)}
              </DialogContent>
              <DialogActions sx={{ p: 2 }}>
                <Button
                  variant="outlined"
                  onClick={() => setDetailDialogOpen(false)}
                >
                  닫기
                </Button>
                <Button
                  variant="contained"
                  startIcon={<Edit />}
                  onClick={() => {
                    setDetailDialogOpen(false);
                    // TODO: 이력서 수정 페이지로 이동
                    navigate(`/resume/create?edit=${selectedResume.id}`);
                  }}
                >
                  수정하기
                </Button>
              </DialogActions>
            </>
          )}
        </Dialog>

        {/* 삭제 확인 다이얼로그 */}
        <Dialog
          open={deleteConfirmOpen}
          onClose={() => setDeleteConfirmOpen(false)}
        >
          <DialogTitle>이력서 삭제</DialogTitle>
          <DialogContent>
            <Typography>
              정말로 이 이력서를 삭제하시겠습니까?
              <br />
              삭제된 이력서는 복구할 수 없습니다.
            </Typography>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDeleteConfirmOpen(false)}>
              취소
            </Button>
            <Button 
              color="error" 
              variant="contained"
              onClick={handleDelete}
            >
              삭제
            </Button>
          </DialogActions>
        </Dialog>
      </Box>
    </Container>
  );
};

export default ResumeListPage;
