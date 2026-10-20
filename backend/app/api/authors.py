from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from app.auth.jwt_handler import get_current_user
from app.core.db import get_db_connection

router = APIRouter(prefix="/authors", tags=["authors"])

class AuthorCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    bio: Optional[str] = None
    era: Optional[str] = None

class AuthorResponse(BaseModel):
    id: str
    name: str
    bio: Optional[str]
    era: Optional[str]

@router.post("", response_model=AuthorResponse)
async def create_author(author: AuthorCreate, current_user: dict = Depends(get_current_user)):
    # Any logged in user can add an author/teacher for study references
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        author_id = str(uuid.uuid4())
        
        with conn:
            conn.execute(
                "INSERT INTO authors (id, name, bio, era) VALUES (?, ?, ?, ?)",
                (author_id, author.name, author.bio, author.era)
            )
            
        return {
            "id": author_id,
            "name": author.name,
            "bio": author.bio,
            "era": author.era
        }
    finally:
        conn.close()

@router.get("", response_model=List[AuthorResponse])
async def list_authors():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM authors ORDER BY name ASC")
        rows = cursor.fetchall()
        authors = []
        for r in rows:
            authors.append({
                "id": r["id"],
                "name": r["name"],
                "bio": r["bio"],
                "era": r["era"]
            })
        return authors
    finally:
        conn.close()
