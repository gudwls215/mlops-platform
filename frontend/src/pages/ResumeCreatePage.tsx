import React, { useState, useEffect, useRef } from 'react';
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
  Fab,
  IconButton,
  Chip
} from '@mui/material';
import { Mic, Create, Save, CheckCircle, Feedback, ArrowForward, Edit, Add, Delete } from '@mui/icons-material';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import VoiceRecorder from '../components/VoiceRecorder';
import FeedbackModal from '../components/FeedbackModal';
import FlowStepIndicator from '../components/FlowStepIndicator';
import axios from 'axios';
import { API_BASE_URL } from '../types';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAppContext } from '../contexts/AppContext';

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
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const editResumeId = searchParams.get('edit');
  const { setCurrentResume, setCurrentStep, currentStep } = useAppContext();
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
  const [isSaving, setIsSaving] = useState(false);
  const [generatedResume, setGeneratedResume] = useState<any>(null);
  const [savedResumeId, setSavedResumeId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [feedbackModalOpen, setFeedbackModalOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [newSkill, setNewSkill] = useState('');
  const [isEditMode, setIsEditMode] = useState(false); // 기존 이력서 수정 모드
  const [editingResumeId, setEditingResumeId] = useState<number | null>(null);
  const resumeContentRef = useRef<HTMLDivElement>(null);

  // URL 파라미터로 edit 모드인 경우 이력서 불러오기
  useEffect(() => {
    if (editResumeId) {
      loadResumeForEdit(parseInt(editResumeId));
    }
  }, [editResumeId]);

  const loadResumeForEdit = async (resumeId: number) => {
    setIsGenerating(true);
    setError(null);
    
    try {
      const response = await axios.get(`${API_BASE_URL}/api/v1/resume/${resumeId}`);
      
      if (response.data.status === 'success') {
        const resumeData = response.data.data;
        let content = resumeData.content;
        
        // content가 문자열인 경우 파싱
        if (typeof content === 'string') {
          try {
            content = JSON.parse(content);
          } catch {
            content = { raw: content };
          }
        }
        
        setGeneratedResume(content);
        setIsEditMode(true);
        setEditingResumeId(resumeId);
        setIsEditing(true); // 수정 모드로 시작
        setSuccessMessage('이력서를 불러왔습니다. 수정 후 저장해주세요.');
      } else {
        setError('이력서를 불러오는데 실패했습니다.');
      }
    } catch (err: any) {
      console.error('이력서 불러오기 오류:', err);
      setError(err.response?.data?.error || '이력서를 불러오는데 실패했습니다.');
    } finally {
      setIsGenerating(false);
    }
  };

  // 이력서 필드 수정 핸들러
  const handleResumeFieldChange = (section: string, field: string, value: any) => {
    setGeneratedResume((prev: any) => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value
      }
    }));
  };

  // 경력정보 수정 핸들러
  const handleCareerChange = (index: number, field: string, value: string) => {
    setGeneratedResume((prev: any) => {
      const newCareerInfo = [...(prev.경력정보 || [])];
      newCareerInfo[index] = {
        ...newCareerInfo[index],
        [field]: value
      };
      return {
        ...prev,
        경력정보: newCareerInfo
      };
    });
  };

  // 경력 추가
  const handleAddCareer = () => {
    setGeneratedResume((prev: any) => ({
      ...prev,
      경력정보: [
        ...(prev.경력정보 || []),
        { 회사명: '', 직위: '', 재직기간: '', 담당업무: '', 주요성과: '' }
      ]
    }));
  };

  // 경력 삭제
  const handleDeleteCareer = (index: number) => {
    setGeneratedResume((prev: any) => ({
      ...prev,
      경력정보: prev.경력정보.filter((_: any, i: number) => i !== index)
    }));
  };

  // 기술스택 추가
  const handleAddSkill = () => {
    if (newSkill.trim()) {
      setGeneratedResume((prev: any) => ({
        ...prev,
        '기술스택/자격증': {
          ...prev['기술스택/자격증'],
          기술스택: [...(prev['기술스택/자격증']?.기술스택 || []), newSkill.trim()]
        }
      }));
      setNewSkill('');
    }
  };

  // 기술스택 삭제
  const handleDeleteSkill = (index: number) => {
    setGeneratedResume((prev: any) => ({
      ...prev,
      '기술스택/자격증': {
        ...prev['기술스택/자격증'],
        기술스택: prev['기술스택/자격증']?.기술스택?.filter((_: any, i: number) => i !== index) || []
      }
    }));
  };

  // 자기소개 수정
  const handleIntroductionChange = (value: string) => {
    setGeneratedResume((prev: any) => ({
      ...prev,
      자기소개: value
    }));
  };

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
      // 1. 음성 파일을 텍스트로 변환 (Whisper STT)
      const transcribeFormData = new FormData();
      transcribeFormData.append('file', audioBlob, 'recording.webm');

      const transcribeResponse = await axios.post(
        `${API_BASE_URL}/api/speech/transcribe`,
        transcribeFormData
      );

      const transcript = transcribeResponse.data.text;

      // 2. 음성 텍스트에서 이력서 데이터 추출 (LLM 정제 단계 포함)
      const extractFormData = new FormData();
      extractFormData.append('text', transcript);

      const extractResponse = await axios.post(
        `${API_BASE_URL}/api/v1/resume/extract-from-voice-text`,
        extractFormData
      );

      setGeneratedResume(extractResponse.data.data);
      
      // 정제 정보 표시
      const wasRefined = extractResponse.data.text_was_refined;
      setSuccessMessage(
        wasRefined 
          ? '음성 인식 텍스트를 AI가 교정하여 이력서를 생성했습니다!' 
          : '음성으로부터 이력서가 성공적으로 생성되었습니다!'
      );

    } catch (err: any) {
      console.error('이력서 생성 오류:', err);
      console.error('에러 응답:', err.response);
      console.error('에러 상태:', err.response?.status);
      console.error('에러 데이터:', err.response?.data);
      
      const errorMessage = err.response?.data?.detail || 
                          err.response?.data?.error || 
                          err.response?.data?.message ||
                          err.message ||
                          '이력서 생성 중 오류가 발생했습니다.';
      setError(errorMessage);
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
        `${API_BASE_URL}/api/v1/resume/extract-from-text`,
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

  const handleSaveToDatabase = async () => {
    if (!generatedResume) {
      setError('저장할 이력서가 없습니다.');
      return;
    }

    setIsSaving(true);
    setError(null);

    try {
      // 이력서 제목 생성 (시간 포함)
      const now = new Date();
      const dateStr = `${now.getFullYear()}.${String(now.getMonth() + 1).padStart(2, '0')}.${String(now.getDate()).padStart(2, '0')}`;
      const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
      const resumeTitle = `${generatedResume?.기본정보?.이름 || '이름없음'}의 이력서 - ${dateStr} ${timeStr}`;

      // 기술스택 배열 생성
      const skills = generatedResume?.['기술스택/자격증']?.기술스택 || [];

      let resumeId: number;
      let responseData: any;

      if (isEditMode && editingResumeId) {
        // 기존 이력서 수정 (PUT 요청)
        const updateFormData = new FormData();
        updateFormData.append('title', resumeTitle);
        updateFormData.append('content', JSON.stringify(generatedResume));
        updateFormData.append('skills', JSON.stringify(skills));

        const updateResponse = await axios.put(
          `${API_BASE_URL}/api/v1/resume/${editingResumeId}`,
          updateFormData
        );

        resumeId = editingResumeId;
        responseData = updateResponse.data.data;
        setSuccessMessage('이력서가 성공적으로 수정되었습니다!');
      } else {
        // 새 이력서 생성 (POST 요청)
        const saveFormData = new FormData();
        saveFormData.append('title', resumeTitle);
        saveFormData.append('content', JSON.stringify(generatedResume));
        saveFormData.append('skills', JSON.stringify(skills));

        const saveResponse = await axios.post(
          `${API_BASE_URL}/api/v1/resume/`,
          saveFormData
        );

        resumeId = saveResponse.data.data.id;
        responseData = saveResponse.data.data;
        setSuccessMessage('이력서가 데이터베이스에 저장되었습니다!');
      }

      setSavedResumeId(resumeId);

      // Context에 이력서 정보 저장
      setCurrentResume({
        id: resumeId,
        title: resumeTitle,
        content: JSON.stringify(generatedResume),
        skills: skills,
        created_at: responseData.created_at,
        updated_at: responseData.updated_at || responseData.created_at,
      });
      setCurrentStep(1); // 이력서 생성 완료
      setIsEditMode(false); // 수정 모드 해제

    } catch (err: any) {
      console.error('이력서 저장 오류:', err);
      setError(err.response?.data?.error || '이력서 저장 중 오류가 발생했습니다.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleGoToRecommendations = () => {
    if (savedResumeId) {
      setCurrentStep(2); // 추천 단계로 이동
      navigate(`/recommendations?resumeId=${savedResumeId}`);
    } else {
      setError('먼저 이력서를 저장해주세요.');
    }
  };

  const handleDownloadPDF = async () => {
    if (!resumeContentRef.current || !generatedResume) {
      setError('다운로드할 이력서가 없습니다.');
      return;
    }

    try {
      setSuccessMessage('PDF를 생성 중입니다...');
      
      // 이력서 내용의 복사본 생성 (스타일 조정을 위해)
      const element = resumeContentRef.current;
      
      // html2canvas로 HTML을 캔버스로 변환
      const canvas = await html2canvas(element, {
        scale: 2, // 고해상도
        useCORS: true,
        logging: false,
        backgroundColor: '#ffffff'
      });
      
      // 캔버스를 이미지로 변환
      const imgData = canvas.toDataURL('image/png');
      
      // PDF 생성 (A4 사이즈)
      const pdf = new jsPDF({
        orientation: 'portrait',
        unit: 'mm',
        format: 'a4'
      });
      
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = pdf.internal.pageSize.getHeight();
      const imgWidth = canvas.width;
      const imgHeight = canvas.height;
      const ratio = Math.min(pdfWidth / imgWidth, pdfHeight / imgHeight);
      const imgX = (pdfWidth - imgWidth * ratio) / 2;
      const imgY = 0;
      
      // 이미지가 한 페이지보다 길 경우 여러 페이지로 분할
      const pageHeight = imgHeight * ratio;
      let heightLeft = pageHeight;
      let position = 0;
      
      pdf.addImage(imgData, 'PNG', imgX, imgY, imgWidth * ratio, imgHeight * ratio);
      heightLeft -= pdfHeight;
      
      while (heightLeft >= 0) {
        position = heightLeft - pageHeight;
        pdf.addPage();
        pdf.addImage(imgData, 'PNG', imgX, position, imgWidth * ratio, imgHeight * ratio);
        heightLeft -= pdfHeight;
      }
      
      // PDF 다운로드
      const fileName = `${generatedResume?.기본정보?.이름 || '이력서'}_이력서_${new Date().toISOString().split('T')[0]}.pdf`;
      pdf.save(fileName);
      
      setSuccessMessage('PDF 다운로드가 완료되었습니다!');
    } catch (err: any) {
      console.error('PDF 생성 오류:', err);
      setError('PDF 생성 중 오류가 발생했습니다.');
    }
  };

  return (
    <Container maxWidth="md">
      <FlowStepIndicator currentStep={currentStep} />

      <Typography
        variant="h3"
        component="h1"
        gutterBottom
        sx={{ textAlign: 'center', mb: 4, fontWeight: 600, fontSize: { xs: '2rem', md: '2.5rem' } }}
      >
        {isEditMode ? '이력서 수정하기' : '이력서 작성하기'}
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

      {generatedResume && (
        <Paper elevation={3} sx={{ p: 4, mb: 4, backgroundColor: 'success.lighter' }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h5" sx={{ fontSize: '1.5rem', fontWeight: 600 }}>
              생성된 이력서
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              {!savedResumeId && (
                <Button
                  variant={isEditing ? "contained" : "outlined"}
                  color={isEditing ? "success" : "primary"}
                  size="small"
                  startIcon={<Edit />}
                  onClick={() => setIsEditing(!isEditing)}
                  sx={{ fontSize: '0.9rem' }}
                >
                  {isEditing ? '수정 완료' : '수정하기'}
                </Button>
              )}
              <Button
                variant="outlined"
                size="small"
                onClick={() => {
                  setGeneratedResume(null);
                  setSavedResumeId(null);
                  setSuccessMessage(null);
                  setIsEditing(false);
                }}
                sx={{ fontSize: '0.9rem' }}
              >
                새로 작성하기
              </Button>
            </Box>
          </Box>

          {isEditing && (
            <Alert severity="info" sx={{ mb: 2 }}>
              각 필드를 클릭하여 내용을 수정할 수 있습니다. 수정이 완료되면 "수정 완료" 버튼을 누르세요.
            </Alert>
          )}

          {/* 이력서 내용 */}
          <Box 
            ref={resumeContentRef}
            sx={{
            mt: 3,
            bgcolor: 'white',
            p: 4,
            borderRadius: 2,
            border: isEditing ? '3px solid #4caf50' : '2px solid #1976d2'
          }}>
            {/* 기본정보 */}
            <Box sx={{ mb: 4, pb: 3, borderBottom: '2px solid #e0e0e0' }}>
              <Typography variant="h4" sx={{ mb: 3, fontWeight: 'bold', color: '#1976d2' }}>
                이력서
              </Typography>
              <Box sx={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: 2, alignItems: 'center' }}>
                <Typography sx={{ fontWeight: 'bold', fontSize: '1.1rem' }}>이름</Typography>
                {isEditing ? (
                  <TextField
                    value={generatedResume?.기본정보?.이름 || ''}
                    onChange={(e) => handleResumeFieldChange('기본정보', '이름', e.target.value)}
                    size="small"
                    fullWidth
                  />
                ) : (
                  <Typography sx={{ fontSize: '1.1rem' }}>{generatedResume?.기본정보?.이름 || '-'}</Typography>
                )}

                <Typography sx={{ fontWeight: 'bold', fontSize: '1.1rem' }}>연락처</Typography>
                {isEditing ? (
                  <TextField
                    value={generatedResume?.기본정보?.연락처 || ''}
                    onChange={(e) => handleResumeFieldChange('기본정보', '연락처', e.target.value)}
                    size="small"
                    fullWidth
                  />
                ) : (
                  <Typography sx={{ fontSize: '1.1rem' }}>{generatedResume?.기본정보?.연락처 || '-'}</Typography>
                )}

                <Typography sx={{ fontWeight: 'bold', fontSize: '1.1rem' }}>이메일</Typography>
                {isEditing ? (
                  <TextField
                    value={generatedResume?.기본정보?.이메일 || ''}
                    onChange={(e) => handleResumeFieldChange('기본정보', '이메일', e.target.value)}
                    size="small"
                    fullWidth
                  />
                ) : (
                  <Typography sx={{ fontSize: '1.1rem' }}>{generatedResume?.기본정보?.이메일 || '-'}</Typography>
                )}

                <Typography sx={{ fontWeight: 'bold', fontSize: '1.1rem' }}>주소</Typography>
                {isEditing ? (
                  <TextField
                    value={generatedResume?.기본정보?.주소 || ''}
                    onChange={(e) => handleResumeFieldChange('기본정보', '주소', e.target.value)}
                    size="small"
                    fullWidth
                  />
                ) : (
                  <Typography sx={{ fontSize: '1.1rem' }}>{generatedResume?.기본정보?.주소 || '-'}</Typography>
                )}
              </Box>
            </Box>

            {/* 학력정보 */}
            <Box sx={{ mb: 4, pb: 3, borderBottom: '2px solid #e0e0e0' }}>
              <Typography variant="h5" sx={{ mb: 2, fontWeight: 'bold', color: '#1976d2' }}>
                학력
              </Typography>
              <Box sx={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: 2, alignItems: 'center' }}>
                <Typography sx={{ fontWeight: 'bold', fontSize: '1.1rem' }}>학교명</Typography>
                {isEditing ? (
                  <TextField
                    value={generatedResume?.학력정보?.학교명 || ''}
                    onChange={(e) => handleResumeFieldChange('학력정보', '학교명', e.target.value)}
                    size="small"
                    fullWidth
                  />
                ) : (
                  <Typography sx={{ fontSize: '1.1rem' }}>{generatedResume?.학력정보?.학교명 || '-'}</Typography>
                )}

                <Typography sx={{ fontWeight: 'bold', fontSize: '1.1rem' }}>전공</Typography>
                {isEditing ? (
                  <TextField
                    value={generatedResume?.학력정보?.전공 || ''}
                    onChange={(e) => handleResumeFieldChange('학력정보', '전공', e.target.value)}
                    size="small"
                    fullWidth
                  />
                ) : (
                  <Typography sx={{ fontSize: '1.1rem' }}>{generatedResume?.학력정보?.전공 || '-'}</Typography>
                )}

                <Typography sx={{ fontWeight: 'bold', fontSize: '1.1rem' }}>학위</Typography>
                {isEditing ? (
                  <TextField
                    value={generatedResume?.학력정보?.학위 || ''}
                    onChange={(e) => handleResumeFieldChange('학력정보', '학위', e.target.value)}
                    size="small"
                    fullWidth
                  />
                ) : (
                  <Typography sx={{ fontSize: '1.1rem' }}>{generatedResume?.학력정보?.학위 || '-'}</Typography>
                )}

                <Typography sx={{ fontWeight: 'bold', fontSize: '1.1rem' }}>졸업연도</Typography>
                {isEditing ? (
                  <TextField
                    value={generatedResume?.학력정보?.졸업연도 || ''}
                    onChange={(e) => handleResumeFieldChange('학력정보', '졸업연도', e.target.value)}
                    size="small"
                    fullWidth
                  />
                ) : (
                  <Typography sx={{ fontSize: '1.1rem' }}>{generatedResume?.학력정보?.졸업연도 || '-'}</Typography>
                )}
              </Box>
            </Box>

            {/* 경력정보 */}
            <Box sx={{ mb: 4, pb: 3, borderBottom: '2px solid #e0e0e0' }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h5" sx={{ fontWeight: 'bold', color: '#1976d2' }}>
                  경력
                </Typography>
                {isEditing && (
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<Add />}
                    onClick={handleAddCareer}
                  >
                    경력 추가
                  </Button>
                )}
              </Box>
              {generatedResume?.경력정보 && generatedResume.경력정보.length > 0 ? (
                generatedResume.경력정보.map((career: any, index: number) => (
                  <Box key={index} sx={{ mb: 3, p: 2, bgcolor: '#f8f9fa', borderRadius: 1, position: 'relative' }}>
                    {isEditing && (
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => handleDeleteCareer(index)}
                        sx={{ position: 'absolute', top: 8, right: 8 }}
                      >
                        <Delete />
                      </IconButton>
                    )}
                    {isEditing ? (
                      <TextField
                        value={career.회사명 || ''}
                        onChange={(e) => handleCareerChange(index, '회사명', e.target.value)}
                        size="small"
                        fullWidth
                        placeholder="회사명"
                        sx={{ mb: 2 }}
                      />
                    ) : (
                      <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1, fontSize: '1.2rem' }}>
                        {career.회사명 || '회사명 없음'}
                      </Typography>
                    )}
                    <Box sx={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: 1.5, mt: 1, alignItems: 'center' }}>
                      <Typography sx={{ fontWeight: 'bold' }}>직위</Typography>
                      {isEditing ? (
                        <TextField
                          value={career.직위 || ''}
                          onChange={(e) => handleCareerChange(index, '직위', e.target.value)}
                          size="small"
                          fullWidth
                        />
                      ) : (
                        <Typography>{career.직위 || '-'}</Typography>
                      )}

                      <Typography sx={{ fontWeight: 'bold' }}>재직기간</Typography>
                      {isEditing ? (
                        <TextField
                          value={career.재직기간 || ''}
                          onChange={(e) => handleCareerChange(index, '재직기간', e.target.value)}
                          size="small"
                          fullWidth
                        />
                      ) : (
                        <Typography>{career.재직기간 || '-'}</Typography>
                      )}

                      <Typography sx={{ fontWeight: 'bold' }}>담당업무</Typography>
                      {isEditing ? (
                        <TextField
                          value={career.담당업무 || ''}
                          onChange={(e) => handleCareerChange(index, '담당업무', e.target.value)}
                          size="small"
                          fullWidth
                          multiline
                          rows={2}
                        />
                      ) : (
                        <Typography>{career.담당업무 || '-'}</Typography>
                      )}

                      <Typography sx={{ fontWeight: 'bold' }}>주요성과</Typography>
                      {isEditing ? (
                        <TextField
                          value={career.주요성과 || ''}
                          onChange={(e) => handleCareerChange(index, '주요성과', e.target.value)}
                          size="small"
                          fullWidth
                          multiline
                          rows={2}
                        />
                      ) : (
                        <Typography>{career.주요성과 || '-'}</Typography>
                      )}
                    </Box>
                  </Box>
                ))
              ) : (
                <Box>
                  <Typography color="text.secondary">경력 정보가 없습니다.</Typography>
                  {isEditing && (
                    <Button
                      variant="text"
                      startIcon={<Add />}
                      onClick={handleAddCareer}
                      sx={{ mt: 1 }}
                    >
                      경력 추가하기
                    </Button>
                  )}
                </Box>
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
                      <Chip
                        key={index}
                        label={skill}
                        onDelete={isEditing ? () => handleDeleteSkill(index) : undefined}
                        sx={{
                          bgcolor: '#e3f2fd',
                          fontSize: '1rem'
                        }}
                      />
                    ))}
                  </Box>
                ) : (
                  <Typography color="text.secondary">등록된 기술스택이 없습니다.</Typography>
                )}
                {isEditing && (
                  <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
                    <TextField
                      value={newSkill}
                      onChange={(e) => setNewSkill(e.target.value)}
                      size="small"
                      placeholder="새 기술 추가"
                      onKeyPress={(e) => e.key === 'Enter' && handleAddSkill()}
                    />
                    <Button variant="outlined" onClick={handleAddSkill} startIcon={<Add />}>
                      추가
                    </Button>
                  </Box>
                )}
              </Box>
              <Box>
                <Typography sx={{ fontWeight: 'bold', mb: 1, fontSize: '1.1rem' }}>자격증</Typography>
                {generatedResume?.['기술스택/자격증']?.자격증 && generatedResume['기술스택/자격증'].자격증.length > 0 ? (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {generatedResume['기술스택/자격증'].자격증.map((cert: any, index: number) => (
                      <Box key={index} sx={{
                        px: 2,
                        py: 0.5,
                        bgcolor: '#fff3e0',
                        borderRadius: 2,
                        fontSize: '1rem'
                      }}>
                        {typeof cert === 'string' ? cert : cert.자격증명 || JSON.stringify(cert)}
                        {typeof cert === 'object' && cert.취득일 && (
                          <Typography component="span" sx={{ ml: 1, fontSize: '0.9rem', color: 'text.secondary' }}>
                            ({cert.취득일})
                          </Typography>
                        )}
                      </Box>
                    ))}
                  </Box>
                ) : (
                  <Typography color="text.secondary">등록된 자격증이 없습니다.</Typography>
                )}
              </Box>
            </Box>

            {/* 자기소개 */}
            <Box>
              <Typography variant="h5" sx={{ mb: 2, fontWeight: 'bold', color: '#1976d2' }}>
                자기소개
              </Typography>
              {isEditing ? (
                <TextField
                  value={generatedResume?.자기소개 || ''}
                  onChange={(e) => handleIntroductionChange(e.target.value)}
                  fullWidth
                  multiline
                  rows={4}
                  placeholder="자기소개를 입력하세요"
                  sx={{ bgcolor: '#f8f9fa' }}
                />
              ) : (
                generatedResume?.자기소개 ? (
                  <Typography sx={{
                    fontSize: '1.1rem',
                    lineHeight: 1.8,
                    p: 2,
                    bgcolor: '#f8f9fa',
                    borderRadius: 1
                  }}>
                    {generatedResume.자기소개}
                  </Typography>
                ) : (
                  <Typography color="text.secondary">자기소개가 없습니다.</Typography>
                )
              )}
            </Box>
          </Box>

          <Box sx={{ mt: 3, textAlign: 'center', display: 'flex', gap: 2, justifyContent: 'center' }}>
            {!savedResumeId ? (
              <Button
                variant="contained"
                color="primary"
                size="large"
                startIcon={<Save />}
                onClick={handleSaveToDatabase}
                disabled={isSaving || isEditing}
                sx={{ fontSize: '1.1rem', py: 1.5, px: 4 }}
              >
                {isEditing ? '수정 완료 후 저장 가능' : isSaving ? '저장 중...' : isEditMode ? '이력서 수정 저장' : '이력서 저장'}
              </Button>
            ) : (
              <>
                <Button
                  variant="outlined"
                  color="primary"
                  size="large"
                  onClick={handleDownloadPDF}
                  sx={{ fontSize: '1.1rem', py: 1.5, px: 4 }}
                >
                  이력서 PDF 다운로드
                </Button>
                <Button
                  variant="contained"
                  color="success"
                  size="large"
                  endIcon={<ArrowForward />}
                  onClick={handleGoToRecommendations}
                  sx={{ fontSize: '1.1rem', py: 1.5, px: 4 }}
                >
                  AI 채용공고 추천 받기
                </Button>
              </>
            )}
          </Box>
        </Paper>
      )}

      {!generatedResume && (
        <>
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
              <Box sx={{ textAlign: 'center', mt: 4 }}>
                {isGenerating ? (
                  <Box sx={{ display: 'inline-flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
                    <CircularProgress size={60} />
                    <Typography variant="h6" sx={{ fontSize: '1.2rem', color: 'primary.main' }}>
                      AI가 이력서를 생성하고 있습니다...
                    </Typography>
                  </Box>
                ) : (
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
                )}
              </Box>
            </TabPanel>
          </Paper>


        </>
      )}

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