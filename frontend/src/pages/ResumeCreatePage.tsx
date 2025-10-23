import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Button,
  TextField,
  Tab,
  Tabs,
  Paper,
  Alert,
  CircularProgress,
  Fab
} from '@mui/material';
import { Mic, MicOff, Create, Save, CheckCircle, Feedback } from '@mui/icons-material';
import VoiceRecorder from '../components/VoiceRecorder';
import FeedbackModal from '../components/FeedbackModal';
import axios from 'axios';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`resume-tabpanel-${index}`}
      aria-labelledby={`resume-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const ResumeCreatePage: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    address: '',
    career: '',
    education: '',
    skills: '',
    experience: ''
  });
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedResume, setGeneratedResume] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [feedbackModalOpen, setFeedbackModalOpen] = useState(false);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
    setError(null);
    setSuccessMessage(null);
  };

  const handleInputChange = (field: string) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [field]: event.target.value
    }));
  };

  const handleVoiceRecordingComplete = async (audioBlob: Blob) => {
    setIsGenerating(true);
    setError(null);
    
    try {
      // 1. 음성 파일을 텍스트로 변환
      const transcribeFormData = new FormData();
      transcribeFormData.append('file', audioBlob, 'recording.webm');
      
      const transcribeResponse = await axios.post(
        'http://localhost:9000/api/speech/transcribe',
        transcribeFormData
      );
      
      const transcript = transcribeResponse.data.text;
      
      // 2. 텍스트에서 이력서 데이터 추출
      const extractFormData = new FormData();
      extractFormData.append('text', transcript);
      
      const extractResponse = await axios.post(
        'http://localhost:9000/api/v1/resume/extract-from-text',
        extractFormData
      );
      
      setGeneratedResume(extractResponse.data.data);
      setSuccessMessage('음성으로부터 이력서가 성공적으로 생성되었습니다!');
      
    } catch (err: any) {
      console.error('이력서 생성 오류:', err);
      setError(err.response?.data?.error || '이력서 생성 중 오류가 발생했습니다.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSaveResume = async () => {
    setIsGenerating(true);
    setError(null);
    
    try {
      // 직접 입력한 내용을 텍스트로 변환
      const inputText = `
        이름: ${formData.name}
        이메일: ${formData.email}
        연락처: ${formData.phone}
        주소: ${formData.address}
        
        경력:
        ${formData.career}
        
        학력:
        ${formData.education}
        
        기술/스킬:
        ${formData.skills}
        
        기타 경험:
        ${formData.experience}
      `;
      
      // 텍스트에서 이력서 데이터 추출
      const extractFormData = new FormData();
      extractFormData.append('text', inputText);
      
      const extractResponse = await axios.post(
        'http://localhost:9000/api/v1/resume/extract-from-text',
        extractFormData
      );
      
      setGeneratedResume(extractResponse.data.data);
      setSuccessMessage('이력서가 성공적으로 생성되었습니다!');
      
    } catch (err: any) {
      console.error('이력서 생성 오류:', err);
      setError(err.response?.data?.error || '이력서 생성 중 오류가 발생했습니다.');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <Container maxWidth="md">
      <Typography 
        variant="h3" 
        component="h1" 
        gutterBottom 
        sx={{ textAlign: 'center', mb: 4, fontWeight: 600, fontSize: { xs: '2rem', md: '2.5rem' } }}
      >
        이력서 작성하기
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3, fontSize: '1.1rem' }}>
          {error}
        </Alert>
      )}

      {successMessage && (
        <Alert 
          severity="success" 
          icon={<CheckCircle />}
          sx={{ mb: 3, fontSize: '1.1rem' }}
        >
          {successMessage}
        </Alert>
      )}

      {isGenerating && (
        <Box sx={{ textAlign: 'center', mb: 3, p: 3 }}>
          <CircularProgress size={60} />
          <Typography variant="h6" sx={{ mt: 2, fontSize: '1.2rem' }}>
            AI가 이력서를 생성하고 있습니다...
          </Typography>
        </Box>
      )}

      {generatedResume && (
        <Paper elevation={3} sx={{ p: 4, mb: 4, backgroundColor: 'success.lighter' }}>
          <Typography variant="h5" gutterBottom sx={{ fontSize: '1.5rem', fontWeight: 600 }}>
            생성된 이력서
          </Typography>
          
          {/* 이력서 내용 */}
          <Box sx={{ 
            mt: 3,
            bgcolor: 'white', 
            p: 4, 
            borderRadius: 2,
            border: '2px solid #1976d2'
          }}>
            {/* 기본정보 */}
            <Box sx={{ mb: 4, pb: 3, borderBottom: '2px solid #e0e0e0' }}>
              <Typography variant="h4" sx={{ mb: 3, fontWeight: 'bold', color: '#1976d2' }}>
                이력서
              </Typography>
              <Box sx={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: 2 }}>
                <Typography sx={{ fontWeight: 'bold', fontSize: '1.1rem' }}>이름</Typography>
                <Typography sx={{ fontSize: '1.1rem' }}>{generatedResume?.기본정보?.이름 || '-'}</Typography>
                
                <Typography sx={{ fontWeight: 'bold', fontSize: '1.1rem' }}>연락처</Typography>
                <Typography sx={{ fontSize: '1.1rem' }}>{generatedResume?.기본정보?.연락처 || '-'}</Typography>
                
                <Typography sx={{ fontWeight: 'bold', fontSize: '1.1rem' }}>이메일</Typography>
                <Typography sx={{ fontSize: '1.1rem' }}>{generatedResume?.기본정보?.이메일 || '-'}</Typography>
                
                <Typography sx={{ fontWeight: 'bold', fontSize: '1.1rem' }}>주소</Typography>
                <Typography sx={{ fontSize: '1.1rem' }}>{generatedResume?.기본정보?.주소 || '-'}</Typography>
              </Box>
            </Box>

            {/* 학력정보 */}
            <Box sx={{ mb: 4, pb: 3, borderBottom: '2px solid #e0e0e0' }}>
              <Typography variant="h5" sx={{ mb: 2, fontWeight: 'bold', color: '#1976d2' }}>
                학력
              </Typography>
              <Box sx={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: 2 }}>
                <Typography sx={{ fontWeight: 'bold', fontSize: '1.1rem' }}>학교명</Typography>
                <Typography sx={{ fontSize: '1.1rem' }}>{generatedResume?.학력정보?.학교명 || '-'}</Typography>
                
                <Typography sx={{ fontWeight: 'bold', fontSize: '1.1rem' }}>전공</Typography>
                <Typography sx={{ fontSize: '1.1rem' }}>{generatedResume?.학력정보?.전공 || '-'}</Typography>
                
                <Typography sx={{ fontWeight: 'bold', fontSize: '1.1rem' }}>학위</Typography>
                <Typography sx={{ fontSize: '1.1rem' }}>{generatedResume?.학력정보?.학위 || '-'}</Typography>
                
                <Typography sx={{ fontWeight: 'bold', fontSize: '1.1rem' }}>졸업연도</Typography>
                <Typography sx={{ fontSize: '1.1rem' }}>{generatedResume?.학력정보?.졸업연도 || '-'}</Typography>
              </Box>
            </Box>

            {/* 경력정보 */}
            <Box sx={{ mb: 4, pb: 3, borderBottom: '2px solid #e0e0e0' }}>
              <Typography variant="h5" sx={{ mb: 2, fontWeight: 'bold', color: '#1976d2' }}>
                경력
              </Typography>
              {generatedResume?.경력정보 && generatedResume.경력정보.length > 0 ? (
                generatedResume.경력정보.map((career: any, index: number) => (
                  <Box key={index} sx={{ mb: 3, p: 2, bgcolor: '#f8f9fa', borderRadius: 1 }}>
                    <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1, fontSize: '1.2rem' }}>
                      {career.회사명 || '회사명 없음'}
                    </Typography>
                    <Box sx={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: 1.5, mt: 1 }}>
                      <Typography sx={{ fontWeight: 'bold' }}>직위</Typography>
                      <Typography>{career.직위 || '-'}</Typography>
                      
                      <Typography sx={{ fontWeight: 'bold' }}>재직기간</Typography>
                      <Typography>{career.재직기간 || '-'}</Typography>
                      
                      <Typography sx={{ fontWeight: 'bold' }}>담당업무</Typography>
                      <Typography>{career.담당업무 || '-'}</Typography>
                      
                      <Typography sx={{ fontWeight: 'bold' }}>주요성과</Typography>
                      <Typography>{career.주요성과 || '-'}</Typography>
                    </Box>
                  </Box>
                ))
              ) : (
                <Typography color="text.secondary">경력 정보가 없습니다.</Typography>
              )}
            </Box>

            {/* 기술스택/자격증 */}
            <Box sx={{ mb: 4, pb: 3, borderBottom: '2px solid #e0e0e0' }}>
              <Typography variant="h5" sx={{ mb: 2, fontWeight: 'bold', color: '#1976d2' }}>
                기술 및 자격
              </Typography>
              <Box sx={{ mb: 2 }}>
                <Typography sx={{ fontWeight: 'bold', mb: 1, fontSize: '1.1rem' }}>기술스택</Typography>
                {generatedResume?.['기술스택/자격증']?.기술스택 && generatedResume['기술스택/자격증'].기술스택.length > 0 ? (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {generatedResume['기술스택/자격증'].기술스택.map((skill: string, index: number) => (
                      <Box key={index} sx={{ 
                        px: 2, 
                        py: 0.5, 
                        bgcolor: '#e3f2fd', 
                        borderRadius: 2,
                        fontSize: '1rem'
                      }}>
                        {skill}
                      </Box>
                    ))}
                  </Box>
                ) : (
                  <Typography color="text.secondary">등록된 기술스택이 없습니다.</Typography>
                )}
              </Box>
              <Box>
                <Typography sx={{ fontWeight: 'bold', mb: 1, fontSize: '1.1rem' }}>자격증</Typography>
                {generatedResume?.['기술스택/자격증']?.자격증 && generatedResume['기술스택/자격증'].자격증.length > 0 ? (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {generatedResume['기술스택/자격증'].자격증.map((cert: string, index: number) => (
                      <Box key={index} sx={{ 
                        px: 2, 
                        py: 0.5, 
                        bgcolor: '#fff3e0', 
                        borderRadius: 2,
                        fontSize: '1rem'
                      }}>
                        {cert}
                      </Box>
                    ))}
                  </Box>
                ) : (
                  <Typography color="text.secondary">등록된 자격증이 없습니다.</Typography>
                )}
              </Box>
            </Box>

            {/* 자기소개 */}
            {generatedResume?.자기소개 && (
              <Box>
                <Typography variant="h5" sx={{ mb: 2, fontWeight: 'bold', color: '#1976d2' }}>
                  자기소개
                </Typography>
                <Typography sx={{ 
                  fontSize: '1.1rem', 
                  lineHeight: 1.8,
                  p: 2,
                  bgcolor: '#f8f9fa',
                  borderRadius: 1
                }}>
                  {generatedResume.자기소개}
                </Typography>
              </Box>
            )}
          </Box>

          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Button
              variant="contained"
              color="primary"
              size="large"
              sx={{ fontSize: '1.1rem', py: 1.5, px: 4 }}
            >
              이력서 다운로드
            </Button>
          </Box>
        </Paper>
      )}

      <Paper elevation={1} sx={{ mb: 3 }}>
        <Tabs 
          value={tabValue} 
          onChange={handleTabChange} 
          aria-label="이력서 작성 방법"
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab 
            label="음성으로 입력" 
            icon={<Mic />} 
            sx={{ fontSize: '1rem', minHeight: '64px' }}
          />
          <Tab 
            label="직접 입력" 
            icon={<Create />} 
            sx={{ fontSize: '1rem', minHeight: '64px' }}
          />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          {/* 음성 입력 탭 */}
          <Box sx={{ py: 2 }}>
            <Typography 
              variant="h5" 
              gutterBottom 
              sx={{ mb: 3, textAlign: 'center', fontSize: '1.5rem' }}
            >
              음성으로 경력과 경험을 말씀해 주세요
            </Typography>
            <Typography 
              variant="body1" 
              color="text.secondary" 
              sx={{ mb: 4, textAlign: 'center', fontSize: '1.1rem' }}
            >
              "안녕하세요, 저는 30년간 회계 업무를 해왔습니다..." 처럼 편안하게 말씀해 주세요.
            </Typography>
            
            <VoiceRecorder
              onRecordingComplete={handleVoiceRecordingComplete}
              maxDuration={300}
              autoTranscribe={true}
            />
          </Box>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          {/* 직접 입력 탭 */}
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <Typography variant="h5" gutterBottom>
              기본 정보
            </Typography>
            
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2 }}>
              <TextField
                label="성명"
                value={formData.name}
                onChange={handleInputChange('name')}
                fullWidth
                required
                InputProps={{ style: { fontSize: '1.1rem' } }}
                InputLabelProps={{ style: { fontSize: '1.1rem' } }}
              />
              <TextField
                label="이메일"
                value={formData.email}
                onChange={handleInputChange('email')}
                fullWidth
                required
                type="email"
                InputProps={{ style: { fontSize: '1.1rem' } }}
                InputLabelProps={{ style: { fontSize: '1.1rem' } }}
              />
              <TextField
                label="연락처"
                value={formData.phone}
                onChange={handleInputChange('phone')}
                fullWidth
                required
                InputProps={{ style: { fontSize: '1.1rem' } }}
                InputLabelProps={{ style: { fontSize: '1.1rem' } }}
              />
              <TextField
                label="주소"
                value={formData.address}
                onChange={handleInputChange('address')}
                fullWidth
                InputProps={{ style: { fontSize: '1.1rem' } }}
                InputLabelProps={{ style: { fontSize: '1.1rem' } }}
              />
            </Box>

            <TextField
              label="경력 사항"
              value={formData.career}
              onChange={handleInputChange('career')}
              fullWidth
              multiline
              rows={4}
              placeholder="어떤 회사에서 어떤 일을 하셨는지 자세히 적어주세요"
              InputProps={{ style: { fontSize: '1.1rem', lineHeight: 1.6 } }}
              InputLabelProps={{ style: { fontSize: '1.1rem' } }}
            />

            <TextField
              label="학력"
              value={formData.education}
              onChange={handleInputChange('education')}
              fullWidth
              multiline
              rows={2}
              placeholder="최종 학력을 적어주세요"
              InputProps={{ style: { fontSize: '1.1rem', lineHeight: 1.6 } }}
              InputLabelProps={{ style: { fontSize: '1.1rem' } }}
            />

            <TextField
              label="보유 기술/스킬"
              value={formData.skills}
              onChange={handleInputChange('skills')}
              fullWidth
              multiline
              rows={2}
              placeholder="컴퓨터, 언어, 자격증 등 보유하신 기술을 적어주세요"
              InputProps={{ style: { fontSize: '1.1rem', lineHeight: 1.6 } }}
              InputLabelProps={{ style: { fontSize: '1.1rem' } }}
            />

            <TextField
              label="기타 경험"
              value={formData.experience}
              onChange={handleInputChange('experience')}
              fullWidth
              multiline
              rows={3}
              placeholder="자원봉사, 동호회, 특별한 경험 등을 적어주세요"
              InputProps={{ style: { fontSize: '1.1rem', lineHeight: 1.6 } }}
              InputLabelProps={{ style: { fontSize: '1.1rem' } }}
            />
          </Box>
        </TabPanel>
      </Paper>

      <Box sx={{ textAlign: 'center', mt: 4 }}>
        <Button
          variant="contained"
          size="large"
          startIcon={<Save />}
          onClick={handleSaveResume}
          sx={{ 
            fontSize: '1.2rem',
            py: 2,
            px: 4,
            minHeight: '56px'
          }}
        >
          AI 이력서 생성하기
        </Button>
      </Box>

      {/* 플로팅 피드백 버튼 */}
      <Fab
        color="primary"
        aria-label="feedback"
        onClick={() => setFeedbackModalOpen(true)}
        sx={{
          position: 'fixed',
          bottom: 24,
          right: 24,
          zIndex: 1000
        }}
      >
        <Feedback />
      </Fab>

      {/* 피드백 모달 */}
      <FeedbackModal
        open={feedbackModalOpen}
        onClose={() => setFeedbackModalOpen(false)}
        relatedResumeId={generatedResume?.id}
      />
    </Container>
  );
};

export default ResumeCreatePage;