from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path
from app.routers import (
    resume, job_posting, cover_letter, matching, 
    model_serving, experiments, labeling, recommendations, 
    hybrid_recommendations, speech
)
from app.api import feedback, monitoring
from app.middleware.usage_monitoring import UsageMonitoringMiddleware
from app.core.config import settings

# .env 파일 로드 (프로젝트 루트의 .env 파일)
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

app = FastAPI(
    title="장년층 이력서 생성 도우미 API",
    description="50대 이상 장년층을 위한 AI 기반 이력서 생성 및 채용 매칭 플랫폼",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 단계에서는 모든 오리진 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 사용량 모니터링 미들웨어 추가
app.add_middleware(UsageMonitoringMiddleware)

# 라우터 등록
app.include_router(resume.router, prefix="/api/v1/resume", tags=["resume"])
app.include_router(job_posting.router, prefix="/api/v1/job", tags=["job"])
app.include_router(speech.router, tags=["speech"])
app.include_router(cover_letter.router, tags=["cover-letter"])
app.include_router(matching.router, tags=["matching"])
app.include_router(feedback.router, tags=["feedback"])
app.include_router(monitoring.router, tags=["monitoring"])
app.include_router(labeling.router, tags=["labeling"])
app.include_router(recommendations.router, tags=["recommendations"])
app.include_router(hybrid_recommendations.router, tags=["hybrid-recommendations"])
app.include_router(model_serving.router, tags=["model-serving"])
app.include_router(experiments.router, tags=["experiments"])

@app.get("/")
async def root():
    return {"message": "장년층 이력서 생성 도우미 API가 정상적으로 실행중입니다."}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)