from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import resume, job_posting
from app.core.config import settings

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

# 라우터 등록
app.include_router(resume.router, prefix="/api/v1/resume", tags=["resume"])
app.include_router(job_posting.router, prefix="/api/v1/job", tags=["job"])

@app.get("/")
async def root():
    return {"message": "장년층 이력서 생성 도우미 API가 정상적으로 실행중입니다."}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)