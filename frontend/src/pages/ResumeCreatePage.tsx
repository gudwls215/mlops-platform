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
  CircularProgress
} from '@mui/material';
import { Mic, MicOff, Create, Save, CheckCircle } from '@mui/icons-material';
import VoiceRecorder from '../components/VoiceRecorder';
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
        'http://localhost:8000/api/speech/transcribe',
        transcribeFormData
      );
      
      const transcript = transcribeResponse.data.text;
      
      // 2. 텍스트에서 이력서 데이터 추출
      const extractFormData = new FormData();
      extractFormData.append('text', transcript);
      
      const extractResponse = await axios.post(
        'http://localhost:8000/api/v1/resume/extract-from-text',
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
        'http://localhost:8000/api/v1/resume/extract-from-text',
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
            ✅ 생성된 이력서
          </Typography>
          <Box sx={{ mt: 2 }}>
            <pre style={{ 
              whiteSpace: 'pre-wrap', 
              fontSize: '1.1rem',
              lineHeight: 1.6,
              fontFamily: 'inherit'
            }}>
              {JSON.stringify(generatedResume, null, 2)}
            </pre>
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
    </Container>
  );
};

export default ResumeCreatePage;