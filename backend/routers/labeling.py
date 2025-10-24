"""
데이터 라벨링 API 엔드포인트
자기소개서 합격/불합격 라벨링을 위한 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db

router = APIRouter(prefix="/api/labeling", tags=["labeling"])


# Pydantic 모델
class LabelRequest(BaseModel):
    """라벨링 요청 모델"""
    cover_letter_id: int
    is_passed: bool
    confidence: Optional[float] = None  # 라벨링 확신도 (0-1)
    notes: Optional[str] = None  # 라벨링 메모


class LabelBatchRequest(BaseModel):
    """일괄 라벨링 요청 모델"""
    labels: List[LabelRequest]


class CoverLetterLabelResponse(BaseModel):
    """자기소개서 라벨 응답 모델"""
    id: int
    title: str
    company: str
    position: str
    content: str
    is_passed: Optional[bool]
    created_at: datetime


class LabelingStatsResponse(BaseModel):
    """라벨링 통계 응답 모델"""
    total: int
    labeled: int
    unlabeled: int
    passed: int
    failed: int
    labeling_rate: float


@router.get("/stats", response_model=LabelingStatsResponse)
def get_labeling_stats(db: Session = Depends(get_db)):
    """라벨링 통계 조회"""
    result = db.execute(text("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN is_passed IS NOT NULL THEN 1 END) as labeled,
            COUNT(CASE WHEN is_passed IS NULL THEN 1 END) as unlabeled,
            COUNT(CASE WHEN is_passed = true THEN 1 END) as passed,
            COUNT(CASE WHEN is_passed = false THEN 1 END) as failed
        FROM mlops.cover_letter_samples
    """)).fetchone()
    
    labeling_rate = (result.labeled / result.total * 100) if result.total > 0 else 0
    
    return {
        "total": result.total,
        "labeled": result.labeled,
        "unlabeled": result.unlabeled,
        "passed": result.passed,
        "failed": result.failed,
        "labeling_rate": round(labeling_rate, 2)
    }


@router.get("/next", response_model=CoverLetterLabelResponse)
def get_next_unlabeled(
    skip_ids: Optional[str] = Query(None, description="건너뛸 ID 목록 (쉼표로 구분)"),
    db: Session = Depends(get_db)
):
    """라벨링할 다음 자기소개서 조회 (무작위)"""
    skip_id_list = []
    if skip_ids:
        skip_id_list = [int(id.strip()) for id in skip_ids.split(",") if id.strip()]
    
    query = """
        SELECT id, title, company, position, content, is_passed, created_at
        FROM mlops.cover_letter_samples
        WHERE is_passed IS NULL
    """
    
    if skip_id_list:
        placeholders = ",".join([f":id{i}" for i in range(len(skip_id_list))])
        query += f" AND id NOT IN ({placeholders})"
    
    query += """
        ORDER BY RANDOM()
        LIMIT 1
    """
    
    params = {f"id{i}": id_val for i, id_val in enumerate(skip_id_list)}
    result = db.execute(text(query), params).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="라벨링할 자기소개서가 없습니다")
    
    return {
        "id": result.id,
        "title": result.title,
        "company": result.company,
        "position": result.position,
        "content": result.content,
        "is_passed": result.is_passed,
        "created_at": result.created_at
    }


@router.get("/item/{cover_letter_id}", response_model=CoverLetterLabelResponse)
def get_cover_letter_for_labeling(cover_letter_id: int, db: Session = Depends(get_db)):
    """특정 자기소개서 조회"""
    result = db.execute(
        text("""
            SELECT id, title, company, position, content, is_passed, created_at
            FROM mlops.cover_letter_samples
            WHERE id = :id
        """),
        {"id": cover_letter_id}
    ).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="자기소개서를 찾을 수 없습니다")
    
    return {
        "id": result.id,
        "title": result.title,
        "company": result.company,
        "position": result.position,
        "content": result.content,
        "is_passed": result.is_passed,
        "created_at": result.created_at
    }


@router.post("/label")
def label_cover_letter(request: LabelRequest, db: Session = Depends(get_db)):
    """자기소개서 라벨링"""
    # 자기소개서 존재 확인
    existing = db.execute(
        text("SELECT id FROM mlops.cover_letter_samples WHERE id = :id"),
        {"id": request.cover_letter_id}
    ).fetchone()
    
    if not existing:
        raise HTTPException(status_code=404, detail="자기소개서를 찾을 수 없습니다")
    
    # 라벨 업데이트
    db.execute(
        text("""
            UPDATE mlops.cover_letter_samples
            SET is_passed = :is_passed,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
        """),
        {
            "id": request.cover_letter_id,
            "is_passed": request.is_passed
        }
    )
    db.commit()
    
    return {
        "success": True,
        "message": f"자기소개서 #{request.cover_letter_id} 라벨링 완료",
        "cover_letter_id": request.cover_letter_id,
        "is_passed": request.is_passed
    }


@router.post("/label/batch")
def label_batch(request: LabelBatchRequest, db: Session = Depends(get_db)):
    """일괄 라벨링"""
    success_count = 0
    failed_count = 0
    errors = []
    
    for label in request.labels:
        try:
            # 자기소개서 존재 확인
            existing = db.execute(
                text("SELECT id FROM mlops.cover_letter_samples WHERE id = :id"),
                {"id": label.cover_letter_id}
            ).fetchone()
            
            if not existing:
                errors.append(f"ID {label.cover_letter_id}: 자기소개서를 찾을 수 없습니다")
                failed_count += 1
                continue
            
            # 라벨 업데이트
            db.execute(
                text("""
                    UPDATE mlops.cover_letter_samples
                    SET is_passed = :is_passed,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = :id
                """),
                {
                    "id": label.cover_letter_id,
                    "is_passed": label.is_passed
                }
            )
            success_count += 1
            
        except Exception as e:
            errors.append(f"ID {label.cover_letter_id}: {str(e)}")
            failed_count += 1
    
    db.commit()
    
    return {
        "success": True,
        "message": f"일괄 라벨링 완료: {success_count}건 성공, {failed_count}건 실패",
        "success_count": success_count,
        "failed_count": failed_count,
        "errors": errors if errors else None
    }


@router.get("/list")
def get_cover_letters_for_labeling(
    labeled: Optional[bool] = Query(None, description="라벨링 여부 (true: 라벨링됨, false: 미라벨, None: 전체)"),
    is_passed: Optional[bool] = Query(None, description="합격 여부 (true: 합격, false: 불합격)"),
    limit: int = Query(20, ge=1, le=100, description="조회 개수"),
    offset: int = Query(0, ge=0, description="오프셋"),
    db: Session = Depends(get_db)
):
    """라벨링용 자기소개서 목록 조회"""
    query = """
        SELECT id, title, company, position, is_passed, 
               LEFT(content, 100) as content_preview,
               created_at
        FROM mlops.cover_letter_samples
        WHERE 1=1
    """
    params = {}
    
    if labeled is not None:
        if labeled:
            query += " AND is_passed IS NOT NULL"
        else:
            query += " AND is_passed IS NULL"
    
    if is_passed is not None:
        query += " AND is_passed = :is_passed"
        params["is_passed"] = is_passed
    
    query += """
        ORDER BY id
        LIMIT :limit OFFSET :offset
    """
    params["limit"] = limit
    params["offset"] = offset
    
    results = db.execute(text(query), params).fetchall()
    
    items = []
    for row in results:
        items.append({
            "id": row.id,
            "title": row.title,
            "company": row.company,
            "position": row.position,
            "is_passed": row.is_passed,
            "content_preview": row.content_preview + "...",
            "created_at": row.created_at
        })
    
    return {
        "items": items,
        "limit": limit,
        "offset": offset,
        "count": len(items)
    }


@router.delete("/label/{cover_letter_id}")
def remove_label(cover_letter_id: int, db: Session = Depends(get_db)):
    """라벨 제거 (미라벨 상태로 되돌리기)"""
    result = db.execute(
        text("""
            UPDATE mlops.cover_letter_samples
            SET is_passed = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
            RETURNING id
        """),
        {"id": cover_letter_id}
    )
    
    if not result.fetchone():
        raise HTTPException(status_code=404, detail="자기소개서를 찾을 수 없습니다")
    
    db.commit()
    
    return {
        "success": True,
        "message": f"자기소개서 #{cover_letter_id} 라벨 제거 완료"
    }
