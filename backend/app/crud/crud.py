from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models import Resume, JobPosting, CoverLetter, PredictionLog
from app.schemas.schemas import ResumeCreate, ResumeUpdate, CoverLetterCreate
from typing import List, Optional

class CRUDResume:
    def get_resume(self, db: Session, resume_id: int) -> Optional[Resume]:
        return db.query(Resume).filter(Resume.id == resume_id).first()
    
    def get_resumes_by_user(self, db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Resume]:
        return db.query(Resume).filter(Resume.user_id == user_id).offset(skip).limit(limit).all()
    
    def create_resume(self, db: Session, resume: ResumeCreate) -> Resume:
        db_resume = Resume(**resume.dict())
        db.add(db_resume)
        db.commit()
        db.refresh(db_resume)
        return db_resume
    
    def update_resume(self, db: Session, resume_id: int, resume_update: ResumeUpdate) -> Optional[Resume]:
        db_resume = self.get_resume(db, resume_id)
        if db_resume:
            update_data = resume_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_resume, field, value)
            db.commit()
            db.refresh(db_resume)
        return db_resume
    
    def delete_resume(self, db: Session, resume_id: int) -> bool:
        db_resume = self.get_resume(db, resume_id)
        if db_resume:
            db_resume.is_active = False
            db.commit()
            return True
        return False

class CRUDJobPosting:
    def get_job_posting(self, db: Session, job_id: int) -> Optional[JobPosting]:
        return db.query(JobPosting).filter(JobPosting.id == job_id).first()
    
    def get_job_postings(self, db: Session, skip: int = 0, limit: int = 100) -> List[JobPosting]:
        return db.query(JobPosting).filter(JobPosting.is_active == True).offset(skip).limit(limit).all()
    
    def search_job_postings(self, db: Session, keyword: str, skip: int = 0, limit: int = 100) -> List[JobPosting]:
        return db.query(JobPosting).filter(
            and_(
                JobPosting.is_active == True,
                JobPosting.title.contains(keyword)
            )
        ).offset(skip).limit(limit).all()

class CRUDCoverLetter:
    def get_cover_letter(self, db: Session, cover_letter_id: int) -> Optional[CoverLetter]:
        return db.query(CoverLetter).filter(CoverLetter.id == cover_letter_id).first()
    
    def create_cover_letter(self, db: Session, cover_letter: CoverLetterCreate) -> CoverLetter:
        db_cover_letter = CoverLetter(**cover_letter.dict())
        db.add(db_cover_letter)
        db.commit()
        db.refresh(db_cover_letter)
        return db_cover_letter

class CRUDPrediction:
    def create_prediction_log(self, db: Session, resume_id: int, job_posting_id: int, 
                            prediction_score: float, model_version: str) -> PredictionLog:
        db_prediction = PredictionLog(
            resume_id=resume_id,
            job_posting_id=job_posting_id,
            prediction_score=prediction_score,
            model_version=model_version
        )
        db.add(db_prediction)
        db.commit()
        db.refresh(db_prediction)
        return db_prediction

# CRUD 인스턴스 생성
resume_crud = CRUDResume()
job_posting_crud = CRUDJobPosting()
cover_letter_crud = CRUDCoverLetter()
prediction_crud = CRUDPrediction()