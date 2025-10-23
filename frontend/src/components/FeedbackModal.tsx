import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Rating,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
  Typography,
  Alert,
  Snackbar
} from '@mui/material';
import axios from 'axios';

interface FeedbackModalProps {
  open: boolean;
  onClose: () => void;
  relatedResumeId?: number;
  relatedJobId?: number;
}

interface FeedbackData {
  feedback_type: string;
  rating: number;
  title: string;
  content: string;
  user_name?: string;
  user_email?: string;
  user_age_group?: string;
  related_resume_id?: number;
  related_job_id?: number;
}

const FeedbackModal: React.FC<FeedbackModalProps> = ({ 
  open, 
  onClose, 
  relatedResumeId, 
  relatedJobId 
}) => {
  const [feedbackType, setFeedbackType] = useState('general');
  const [rating, setRating] = useState<number>(5);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [userName, setUserName] = useState('');
  const [userEmail, setUserEmail] = useState('');
  const [ageGroup, setAgeGroup] = useState('');
  const [loading, setLoading] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async () => {
    if (!title.trim() || !content.trim()) {
      setError('제목과 내용을 입력해주세요.');
      return;
    }

    setLoading(true);
    setError('');

    const feedbackData: FeedbackData = {
      feedback_type: feedbackType,
      rating: rating,
      title: title.trim(),
      content: content.trim(),
    };

    // 선택적 필드 추가
    if (userName.trim()) feedbackData.user_name = userName.trim();
    if (userEmail.trim()) feedbackData.user_email = userEmail.trim();
    if (ageGroup) feedbackData.user_age_group = ageGroup;
    if (relatedResumeId) feedbackData.related_resume_id = relatedResumeId;
    if (relatedJobId) feedbackData.related_job_id = relatedJobId;

    try {
      await axios.post('http://114.202.2.226:9000/api/feedback/', feedbackData);
      setShowSuccess(true);
      
      // 폼 초기화
      setFeedbackType('general');
      setRating(5);
      setTitle('');
      setContent('');
      setUserName('');
      setUserEmail('');
      setAgeGroup('');
      
      // 2초 후 모달 닫기
      setTimeout(() => {
        onClose();
        setShowSuccess(false);
      }, 2000);
    } catch (err: any) {
      setError(err.response?.data?.detail || '피드백 제출 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      onClose();
    }
  };

  return (
    <>
      <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
        <DialogTitle>
          <Typography variant="h5" fontWeight="bold" color="#1976d2">
            피드백 보내기
          </Typography>
        </DialogTitle>
        
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, pt: 1 }}>
            {/* 피드백 유형 */}
            <FormControl fullWidth>
              <InputLabel>피드백 유형</InputLabel>
              <Select
                value={feedbackType}
                label="피드백 유형"
                onChange={(e) => setFeedbackType(e.target.value)}
              >
                <MenuItem value="resume_generation">이력서 생성</MenuItem>
                <MenuItem value="cover_letter">자기소개서</MenuItem>
                <MenuItem value="job_matching">채용공고 매칭</MenuItem>
                <MenuItem value="ui_ux">UI/UX</MenuItem>
                <MenuItem value="general">일반</MenuItem>
              </Select>
            </FormControl>

            {/* 평점 */}
            <Box>
              <Typography component="legend" sx={{ mb: 1 }}>평점</Typography>
              <Rating
                value={rating}
                onChange={(event, newValue) => {
                  setRating(newValue || 1);
                }}
                size="large"
              />
            </Box>

            {/* 제목 */}
            <TextField
              label="제목"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              fullWidth
              placeholder="피드백 제목을 입력해주세요"
            />

            {/* 내용 */}
            <TextField
              label="내용"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              required
              fullWidth
              multiline
              rows={4}
              placeholder="자세한 피드백을 작성해주세요 (최소 10자)"
            />

            {/* 선택 정보 */}
            <Box sx={{ borderTop: '1px solid #e0e0e0', pt: 2 }}>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
                아래 정보는 선택사항입니다
              </Typography>
              
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <TextField
                  label="이름 (선택)"
                  value={userName}
                  onChange={(e) => setUserName(e.target.value)}
                  fullWidth
                  size="small"
                />
                
                <TextField
                  label="이메일 (선택)"
                  value={userEmail}
                  onChange={(e) => setUserEmail(e.target.value)}
                  fullWidth
                  size="small"
                  type="email"
                />
                
                <FormControl fullWidth size="small">
                  <InputLabel>연령대 (선택)</InputLabel>
                  <Select
                    value={ageGroup}
                    label="연령대 (선택)"
                    onChange={(e) => setAgeGroup(e.target.value)}
                  >
                    <MenuItem value="">선택 안 함</MenuItem>
                    <MenuItem value="10대">10대</MenuItem>
                    <MenuItem value="20대">20대</MenuItem>
                    <MenuItem value="30대">30대</MenuItem>
                    <MenuItem value="40대">40대</MenuItem>
                    <MenuItem value="50대 이상">50대 이상</MenuItem>
                  </Select>
                </FormControl>
              </Box>
            </Box>

            {error && (
              <Alert severity="error" onClose={() => setError('')}>
                {error}
              </Alert>
            )}
          </Box>
        </DialogContent>

        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={handleClose} disabled={loading}>
            취소
          </Button>
          <Button 
            onClick={handleSubmit} 
            variant="contained" 
            disabled={loading}
            sx={{ minWidth: 100 }}
          >
            {loading ? '제출 중...' : '제출'}
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={showSuccess}
        autoHideDuration={2000}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert severity="success" sx={{ width: '100%' }}>
          피드백이 성공적으로 제출되었습니다!
        </Alert>
      </Snackbar>
    </>
  );
};

export default FeedbackModal;
