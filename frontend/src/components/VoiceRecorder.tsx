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
  onRecordingComplete: (audioBlob: Blob, transcript?: string) => void;
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
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
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

    } catch (err) {
      console.error('마이크 접근 오류:', err);
      setError('마이크에 접근할 수 없습니다. 마이크 권한을 확인해 주세요.');
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
    if (!audioBlob) return;

    if (autoTranscribe) {
      setIsTranscribing(true);
      try {
        // 여기서 실제 STT API 호출
        // const formData = new FormData();
        // formData.append('file', audioBlob);
        // const response = await axios.post('/api/speech/transcribe', formData);
        // onRecordingComplete(audioBlob, response.data.text);
        
        // 임시로 바로 전달
        onRecordingComplete(audioBlob);
      } catch (err) {
        console.error('음성 변환 오류:', err);
        setError('음성을 텍스트로 변환하는 중 오류가 발생했습니다.');
      } finally {
        setIsTranscribing(false);
      }
    } else {
      onRecordingComplete(audioBlob);
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
