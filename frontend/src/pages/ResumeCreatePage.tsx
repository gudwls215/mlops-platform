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
} from '@mui/material';
import { Mic, MicOff, Create, Save } from '@mui/icons-material';

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
  const [isRecording, setIsRecording] = useState(false);
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

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleInputChange = (field: string) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [field]: event.target.value
    }));
  };

  const handleVoiceRecording = () => {
    setIsRecording(!isRecording);
    // TODO: 실제 음성 녹음 로직 구현
    if (!isRecording) {
      console.log('음성 녹음 시작');
    } else {
      console.log('음성 녹음 중지');
    }
  };

  const handleSaveResume = () => {
    // TODO: 백엔드 API 호출하여 이력서 저장
    console.log('이력서 저장:', formData);
  };

  return (
    <Container maxWidth="md">
      <Typography 
        variant="h3" 
        component="h1" 
        gutterBottom 
        sx={{ textAlign: 'center', mb: 4, fontWeight: 600 }}
      >
        이력서 작성하기
      </Typography>

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
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
              음성으로 경력과 경험을 말씀해 주세요
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 4, fontSize: '1.1rem' }}>
              "안녕하세요, 저는 30년간 회계 업무를 해왔습니다..." 처럼 편안하게 말씀해 주세요.
            </Typography>
            
            <Button
              variant={isRecording ? "contained" : "outlined"}
              color={isRecording ? "secondary" : "primary"}
              size="large"
              startIcon={isRecording ? <MicOff /> : <Mic />}
              onClick={handleVoiceRecording}
              sx={{ 
                fontSize: '1.2rem',
                py: 2,
                px: 4,
                minHeight: '64px',
                minWidth: '200px'
              }}
            >
              {isRecording ? '녹음 중지' : '음성 녹음 시작'}
            </Button>

            {isRecording && (
              <Alert severity="info" sx={{ mt: 3, fontSize: '1rem' }}>
                🎤 녹음 중입니다. 편안하게 말씀해 주세요.
              </Alert>
            )}
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
              />
              <TextField
                label="이메일"
                value={formData.email}
                onChange={handleInputChange('email')}
                fullWidth
                required
                type="email"
              />
              <TextField
                label="연락처"
                value={formData.phone}
                onChange={handleInputChange('phone')}
                fullWidth
                required
              />
              <TextField
                label="주소"
                value={formData.address}
                onChange={handleInputChange('address')}
                fullWidth
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
            />

            <TextField
              label="학력"
              value={formData.education}
              onChange={handleInputChange('education')}
              fullWidth
              multiline
              rows={2}
              placeholder="최종 학력을 적어주세요"
            />

            <TextField
              label="보유 기술/스킬"
              value={formData.skills}
              onChange={handleInputChange('skills')}
              fullWidth
              multiline
              rows={2}
              placeholder="컴퓨터, 언어, 자격증 등 보유하신 기술을 적어주세요"
            />

            <TextField
              label="기타 경험"
              value={formData.experience}
              onChange={handleInputChange('experience')}
              fullWidth
              multiline
              rows={3}
              placeholder="자원봉사, 동호회, 특별한 경험 등을 적어주세요"
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