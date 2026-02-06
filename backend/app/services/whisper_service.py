"""
Whisper STT 서비스 모듈
음성 파일을 텍스트로 변환하는 Speech-to-Text 기능 제공
"""
import os
import logging
import tempfile
from typing import Optional, Dict, Any, BinaryIO
from pathlib import Path
import whisper
import torch

logger = logging.getLogger(__name__)


class WhisperService:
    """Whisper STT 서비스 클래스"""
    
    def __init__(
        self,
        model_name: str = "base",
        device: Optional[str] = None,
        language: str = "ko"
    ):
        """
        Whisper 모델 초기화
        
        Args:
            model_name: 모델 크기 (tiny, base, small, medium, large)
            device: 실행 디바이스 ("cuda" 또는 "cpu", None이면 자동 감지)
            language: 인식 언어 코드 (기본값: "ko" 한국어)
        """
        self.model_name = model_name
        self.language = language
        
        # 디바이스 자동 감지
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        logger.info(f"Initializing Whisper model: {model_name} on {self.device}")
        
        # Whisper 모델 로드
        try:
            self.model = whisper.load_model(model_name, device=self.device)
            logger.info(f"Whisper model loaded successfully")
            
            # GPU 정보 출력
            if self.device == "cuda":
                gpu_name = torch.cuda.get_device_name(0)
                logger.info(f"Using GPU: {gpu_name}")
        
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise
        
        # 통계 정보
        self.total_transcriptions = 0
        self.total_duration = 0.0
    
    def transcribe_file(
        self,
        audio_file: BinaryIO,
        filename: str,
        language: Optional[str] = None,
        task: str = "transcribe",
        **kwargs
    ) -> Dict[str, Any]:
        """
        음성 파일을 텍스트로 변환
        
        Args:
            audio_file: 음성 파일 바이너리 객체
            filename: 파일명
            language: 인식 언어 (None이면 self.language 사용)
            task: "transcribe" (음성 인식) 또는 "translate" (영어 번역)
            **kwargs: 추가 Whisper 옵션
        
        Returns:
            변환 결과 딕셔너리
        """
        language = language or self.language
        
        # 임시 파일로 저장 (Whisper는 파일 경로 필요)
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as temp_file:
            temp_path = temp_file.name
            temp_file.write(audio_file.read())
        
        try:
            logger.info(f"Transcribing audio file: {filename} (language: {language})")
            
            # Whisper 실행
            result = self.model.transcribe(
                temp_path,
                language=language,
                task=task,
                **kwargs
            )
            
            # 통계 업데이트
            self.total_transcriptions += 1
            if "segments" in result and result["segments"]:
                # 마지막 세그먼트의 종료 시간을 전체 길이로 사용
                duration = result["segments"][-1]["end"]
                self.total_duration += duration
            
            # 세그먼트 정보 추출
            segments = []
            if "segments" in result:
                for seg in result["segments"]:
                    segments.append({
                        "id": seg["id"],
                        "start": seg["start"],
                        "end": seg["end"],
                        "text": seg["text"].strip()
                    })
            
            logger.info(f"Transcription completed: {len(result['text'])} characters")
            
            return {
                "status": "success",
                "text": result["text"].strip(),
                "language": result.get("language", language),
                "segments": segments,
                "filename": filename,
                "model": self.model_name,
                "device": self.device
            }
        
        except Exception as e:
            logger.error(f"Transcription failed for {filename}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "filename": filename
            }
        
        finally:
            # 임시 파일 삭제
            try:
                os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp file {temp_path}: {e}")
    
    def transcribe_with_timestamps(
        self,
        audio_file: BinaryIO,
        filename: str,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        타임스탬프 포함 음성 인식
        
        Args:
            audio_file: 음성 파일 바이너리 객체
            filename: 파일명
            language: 인식 언어
        
        Returns:
            타임스탬프 포함 변환 결과
        """
        result = self.transcribe_file(
            audio_file,
            filename,
            language=language,
            word_timestamps=True
        )
        
        return result
    
    def detect_language(
        self,
        audio_file: BinaryIO,
        filename: str
    ) -> Dict[str, Any]:
        """
        음성 파일의 언어 감지
        
        Args:
            audio_file: 음성 파일 바이너리 객체
            filename: 파일명
        
        Returns:
            감지된 언어 정보
        """
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as temp_file:
            temp_path = temp_file.name
            temp_file.write(audio_file.read())
        
        try:
            # 오디오 로드
            audio = whisper.load_audio(temp_path)
            audio = whisper.pad_or_trim(audio)
            
            # 멜 스펙트로그램 생성
            mel = whisper.log_mel_spectrogram(audio).to(self.model.device)
            
            # 언어 감지
            _, probs = self.model.detect_language(mel)
            
            # 상위 3개 언어
            top_languages = sorted(probs.items(), key=lambda x: x[1], reverse=True)[:3]
            
            return {
                "status": "success",
                "detected_language": max(probs, key=probs.get),
                "confidence": max(probs.values()),
                "top_languages": [
                    {"language": lang, "probability": prob}
                    for lang, prob in top_languages
                ],
                "filename": filename
            }
        
        except Exception as e:
            logger.error(f"Language detection failed for {filename}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "filename": filename
            }
        
        finally:
            try:
                os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp file {temp_path}: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        서비스 통계 조회
        
        Returns:
            통계 딕셔너리
        """
        return {
            "model": self.model_name,
            "device": self.device,
            "language": self.language,
            "total_transcriptions": self.total_transcriptions,
            "total_duration_seconds": self.total_duration,
            "gpu_available": torch.cuda.is_available(),
            "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
        }


# 싱글톤 인스턴스
_whisper_service_instance = None


def get_whisper_service(
    model_name: Optional[str] = None,
    device: Optional[str] = None,
    language: str = "ko"
) -> WhisperService:
    """
    Whisper 서비스 싱글톤 인스턴스 반환
    
    Args:
        model_name: 모델 크기 (tiny, base, small, medium, large)
                   환경변수 WHISPER_MODEL로도 설정 가능 (기본값: small)
        device: 실행 디바이스
        language: 인식 언어
    
    Returns:
        WhisperService 인스턴스
    """
    global _whisper_service_instance
    
    # 환경변수에서 모델 이름 가져오기 (기본값: small - 더 정확한 인식)
    if model_name is None:
        model_name = os.getenv("WHISPER_MODEL", "small")
    
    if _whisper_service_instance is None:
        _whisper_service_instance = WhisperService(
            model_name=model_name,
            device=device,
            language=language
        )
    
    return _whisper_service_instance
