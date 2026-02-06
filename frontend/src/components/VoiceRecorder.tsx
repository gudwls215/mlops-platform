import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Button,
  Typography,
  Paper,
  Alert,
  CircularProgress,
  LinearProgress
} from '@mui/material';
import {
  Mic,
  Stop,
  PlayArrow,
  Pause
} from '@mui/icons-material';

interface VoiceRecorderProps {
  onRecordingComplete: (audioBlob: Blob, transcript?: string) => void | Promise<void>;
  maxDuration?: number; // 초 단위
  autoTranscribe?: boolean;
}

const VoiceRecorder: React.FC<VoiceRecorderProps> = ({
  onRecordingComplete,
  maxDuration = 300, // 기본 5분
  autoTranscribe = true
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isTranscribing, setIsTranscribing] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    return () => {
      // 컴포넌트 언마운트 시 정리
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, [audioUrl]);

  const startRecording = async () => {
    try {
      setError(null);
      
      // 브라우저 지원 확인
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        setError('이 브라우저는 음성 녹음을 지원하지 않습니다. Chrome, Firefox, Safari 최신 버전을 사용해 주세요.');
        return;
      }

      // HTTPS 확인 (localhost는 예외)
      const isSecure = window.location.protocol === 'https:' || 
                       window.location.hostname === 'localhost' ||
                       window.location.hostname === '127.0.0.1';
      
      if (!isSecure) {
        setError('보안 연결(HTTPS)이 필요합니다. 마이크 접근은 HTTPS에서만 가능합니다.');
        return;
      }

      console.log('마이크 권한 요청 중...');
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        } 
      });
      
      console.log('마이크 권한 획득 성공');
      
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        setAudioBlob(blob);
        const url = URL.createObjectURL(blob);
        setAudioUrl(url);
        
        // 스트림 정리
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);

      // 타이머 시작
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => {
          const newTime = prev + 1;
          if (newTime >= maxDuration) {
            stopRecording();
            return maxDuration;
          }
          return newTime;
        });
      }, 1000);

    } catch (err: any) {
      console.error('마이크 접근 오류:', err);
      
      let errorMessage = '마이크에 접근할 수 없습니다.';
      
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        errorMessage = '마이크 권한이 거부되었습니다. 브라우저 설정에서 마이크 권한을 허용해 주세요.';
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        errorMessage = '마이크를 찾을 수 없습니다. 마이크가 연결되어 있는지 확인해 주세요.';
      } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
        errorMessage = '마이크를 사용할 수 없습니다. 다른 프로그램에서 마이크를 사용 중일 수 있습니다.';
      } else if (err.name === 'OverconstrainedError') {
        errorMessage = '마이크 설정을 적용할 수 없습니다. 다른 마이크를 시도해 주세요.';
      } else if (err.name === 'SecurityError') {
        errorMessage = '보안 오류: HTTPS 연결이 필요하거나 권한이 차단되었습니다.';
      }
      
      setError(errorMessage);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setIsPaused(false);
      
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
  };

  const pauseRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      if (isPaused) {
        mediaRecorderRef.current.resume();
        setIsPaused(false);
      } else {
        mediaRecorderRef.current.pause();
        setIsPaused(true);
      }
    }
  };

  const playAudio = () => {
    if (audioRef.current && audioUrl) {
      if (isPlaying) {
        audioRef.current.pause();
        setIsPlaying(false);
      } else {
        audioRef.current.play();
        setIsPlaying(true);
      }
    }
  };

  const handleComplete = async () => {
    if (!audioBlob) {
      setError('녹음된 음성이 없습니다. 먼저 녹음을 해주세요.');
      return;
    }

    setIsTranscribing(true);
    setError(null);
    
    try {
      // 부모 컴포넌트(ResumeCreatePage)에서 실제 STT API 호출 및 이력서 생성 처리
      // VoiceRecorder는 audioBlob만 전달하고, STT 처리는 부모에서 수행
      await onRecordingComplete(audioBlob);
    } catch (err: any) {
      console.error('이력서 생성 오류:', err);
      setError(err.message || '이력서 생성 중 오류가 발생했습니다.');
    } finally {
      setIsTranscribing(false);
    }
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const progress = (recordingTime / maxDuration) * 100;

  return (
    <Paper 
      elevation={3} 
      sx={{ 
        p: 4, 
        textAlign: 'center',
        backgroundColor: 'background.paper'
      }}
    >
      <Typography 
        variant="h5" 
        gutterBottom
        sx={{ fontSize: '1.5rem', fontWeight: 600, mb: 3 }}
      >
        음성 녹음
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3, fontSize: '1.1rem' }}>
          {error}
        </Alert>
      )}

      <Box sx={{ mb: 4 }}>
        <Typography 
          variant="h3" 
          sx={{ 
            fontSize: '3rem', 
            fontWeight: 'bold',
            color: isRecording ? 'error.main' : 'text.primary',
            mb: 2
          }}
        >
          {formatTime(recordingTime)}
        </Typography>

        {isRecording && (
          <Box sx={{ mb: 2 }}>
            <LinearProgress 
              variant="determinate" 
              value={progress}
              sx={{ height: 10, borderRadius: 5 }}
            />
            <Typography 
              variant="body2" 
              color="text.secondary"
              sx={{ mt: 1, fontSize: '1rem' }}
            >
              최대 {formatTime(maxDuration)} 까지 녹음 가능
            </Typography>
          </Box>
        )}
      </Box>

      <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', mb: 3 }}>
        {!isRecording && !audioBlob && (
          <Button
            variant="contained"
            color="error"
            size="large"
            startIcon={<Mic />}
            onClick={startRecording}
            sx={{ 
              fontSize: '1.2rem',
              py: 2,
              px: 4,
              minHeight: '60px',
              minWidth: '200px'
            }}
          >
            녹음 시작
          </Button>
        )}

        {isRecording && (
          <>
            <Button
              variant="contained"
              color={isPaused ? 'primary' : 'warning'}
              size="large"
              startIcon={isPaused ? <PlayArrow /> : <Pause />}
              onClick={pauseRecording}
              sx={{ 
                fontSize: '1.2rem',
                py: 2,
                px: 3,
                minHeight: '60px'
              }}
            >
              {isPaused ? '계속' : '일시정지'}
            </Button>
            <Button
              variant="contained"
              color="error"
              size="large"
              startIcon={<Stop />}
              onClick={stopRecording}
              sx={{ 
                fontSize: '1.2rem',
                py: 2,
                px: 3,
                minHeight: '60px'
              }}
            >
              정지
            </Button>
          </>
        )}

        {audioBlob && (
          <>
            <Button
              variant="outlined"
              size="large"
              startIcon={isPlaying ? <Pause /> : <PlayArrow />}
              onClick={playAudio}
              sx={{ 
                fontSize: '1.2rem',
                py: 2,
                px: 3,
                minHeight: '60px'
              }}
            >
              {isPlaying ? '일시정지' : '재생'}
            </Button>
            <Button
              variant="outlined"
              size="large"
              startIcon={<Mic />}
              onClick={() => {
                setAudioBlob(null);
                setAudioUrl(null);
                setRecordingTime(0);
              }}
              sx={{ 
                fontSize: '1.2rem',
                py: 2,
                px: 3,
                minHeight: '60px'
              }}
            >
              다시 녹음
            </Button>
          </>
        )}
      </Box>

      {audioBlob && (
        <Button
          variant="contained"
          color="primary"
          size="large"
          onClick={handleComplete}
          disabled={isTranscribing}
          sx={{ 
            fontSize: '1.3rem',
            py: 2.5,
            px: 5,
            minHeight: '70px',
            minWidth: '250px'
          }}
        >
          {isTranscribing ? (
            <>
              <CircularProgress size={24} sx={{ mr: 2 }} />
              음성 변환 중...
            </>
          ) : (
            '이력서 생성하기'
          )}
        </Button>
      )}

      {audioUrl && (
        <audio
          ref={audioRef}
          src={audioUrl}
          onEnded={() => setIsPlaying(false)}
          style={{ display: 'none' }}
        />
      )}

      <Box sx={{ mt: 4, p: 2, backgroundColor: 'info.lighter', borderRadius: 2 }}>
        <Typography 
          variant="body1" 
          color="info.dark"
          sx={{ fontSize: '1.1rem', lineHeight: 1.6 }}
        >
          💡 <strong>팁:</strong> 조용한 곳에서 마이크에 대고 또박또박 말씀해 주세요.
          <br />
          경력, 학력, 기술 등 이력서에 들어갈 내용을 자유롭게 말씀하시면 됩니다.
        </Typography>
      </Box>
    </Paper>
  );
};

export default VoiceRecorder;
