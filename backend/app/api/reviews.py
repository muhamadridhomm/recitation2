from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid
from app.auth.jwt_handler import get_current_user
from app.core.db import get_db_connection

router = APIRouter(prefix="/reviews", tags=["reviews"])

# Pydantic Schemas
class ReviewCreate(BaseModel):
    project_id: str
    commit_id: str
    status: str = Field(..., description="approved, needs_work, or pending")
    comments: Optional[str] = None

class ReviewResponse(BaseModel):
    id: str
    project_id: str
    commit_id: str
    scholar_id: str
    scholar_username: str
    status: str
    comments: Optional[str]
    timestamp: str

# Endpoints
@router.post("", response_model=ReviewResponse)
async def create_review(review: ReviewCreate, current_user: dict = Depends(get_current_user)):
    # Check if the user is a scholar/teacher
    if current_user["role"] not in ["scholar", "teacher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only verified scholars or teachers can submit reviews."
        )
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Verify project and commit exist
        cursor.execute("SELECT id FROM note_projects WHERE id = ?", (review.project_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Project not found")
            
        cursor.execute("SELECT id FROM commits WHERE id = ?", (review.commit_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Commit not found")
            
        review_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        with conn:
            conn.execute(
                """
                INSERT INTO scholarly_reviews (id, project_id, commit_id, scholar_id, status, comments, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (review_id, review.project_id, review.commit_id, current_user["id"], review.status, review.comments, timestamp)
            )
            
        return {
            "id": review_id,
            "project_id": review.project_id,
            "commit_id": review.commit_id,
            "scholar_id": current_user["id"],
            "scholar_username": current_user["username"],
            "status": review.status,
            "comments": review.comments,
            "timestamp": timestamp
        }
    finally:
        conn.close()

@router.get("/project/{project_id}", response_model=List[ReviewResponse])
async def list_project_reviews(project_id: str):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT r.*, u.username as scholar_username 
            FROM scholarly_reviews r
            JOIN users u ON r.scholar_id = u.id
            WHERE r.project_id = ?
            ORDER BY r.timestamp DESC
            """,
            (project_id,)
        )
        rows = cursor.fetchall()
        reviews = []
        for r in rows:
            reviews.append({
                "id": r["id"],
                "project_id": r["project_id"],
                "commit_id": r["commit_id"],
                "scholar_id": r["scholar_id"],
                "scholar_username": r["scholar_username"],
                "status": r["status"],
                "comments": r["comments"],
                "timestamp": r["timestamp"]
            })
        return reviews
    finally:
        conn.close()
