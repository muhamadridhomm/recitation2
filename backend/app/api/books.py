from fastapi import APIRouter, HTTPException, Depends, status, File, UploadFile, Form
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
import os
import shutil
from datetime import datetime
from app.auth.jwt_handler import get_current_user
from app.core.db import get_db_connection

router = APIRouter(prefix="/books", tags=["books"])

class BookCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    file_path: Optional[str] = None
    author_id: Optional[str] = None

class BookResponse(BaseModel):
    id: str
    title: str
    file_path: Optional[str]
    author_name: Optional[str] = None
    created_at: str

@router.post("", response_model=BookResponse)
async def create_book(book: BookCreate, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        book_id = str(uuid.uuid4())
        
        # Verify author exists if provided
        author_name = None
        if book.author_id:
            cursor.execute("SELECT name FROM authors WHERE id = ?", (book.author_id,))
            author = cursor.fetchone()
            if not author:
                raise HTTPException(status_code=400, detail="Author not found")
            author_name = author["name"]
            
        with conn:
            cursor.execute(
                "INSERT INTO books (id, title, author_id, file_path, uploaded_by) VALUES (?, ?, ?, ?, ?)",
                (book_id, book.title, book.author_id, book.file_path, current_user["id"])
            )
            if book.author_id:
                cursor.execute(
                    "INSERT OR IGNORE INTO book_authors (book_id, author_id) VALUES (?, ?)",
                    (book_id, book.author_id)
                )
                
        return {
            "id": book_id,
            "title": book.title,
            "file_path": book.file_path,
            "author_name": author_name,
            "created_at": ""
        }
    finally:
        conn.close()

@router.get("", response_model=List[BookResponse])
async def list_books():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT b.*, a.name as author_name 
            FROM books b
            LEFT JOIN authors a ON b.author_id = a.id
            ORDER BY b.title ASC
            """
        )
        rows = cursor.fetchall()
        books = []
        for r in rows:
            books.append({
                "id": r["id"],
                "title": r["title"],
                "file_path": r["file_path"],
                "author_name": r["author_name"],
                "created_at": r["created_at"]
            })
        return books
    finally:
        conn.close()

@router.post("/upload", response_model=BookResponse)
async def upload_book(
    title: str = Form(...),
    author_id: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user)
):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        book_id = str(uuid.uuid4())
        
        # Verify author exists if provided
        author_name = None
        if author_id and author_id != "null" and author_id != "undefined":
            cursor.execute("SELECT name FROM authors WHERE id = ?", (author_id,))
            author = cursor.fetchone()
            if not author:
                raise HTTPException(status_code=400, detail="Author not found")
            author_name = author["name"]
        else:
            author_id = None
            
        file_path = None
        if file and file.filename:
            # Save uploaded file
            uploads_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads")
            os.makedirs(uploads_dir, exist_ok=True)
            # Safe filename
            filename = f"{book_id}_{file.filename}"
            target_path = os.path.join(uploads_dir, filename)
            with open(target_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            file_path = f"uploads/{filename}"
            
        created_at = datetime.utcnow().isoformat()
        with conn:
            cursor.execute(
                "INSERT INTO books (id, title, author_id, file_path, uploaded_by, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (book_id, title, author_id, file_path, current_user["id"], created_at)
            )
            if author_id:
                cursor.execute(
                    "INSERT OR IGNORE INTO book_authors (book_id, author_id) VALUES (?, ?)",
                    (book_id, author_id)
                )
                
        return {
            "id": book_id,
            "title": title,
            "file_path": file_path,
            "author_name": author_name,
            "created_at": created_at
        }
    finally:
        conn.close()

@router.get("/stats/tokens")
async def get_token_stats():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Count characters in commits
        cursor.execute("SELECT SUM(length(content)) FROM commits")
        notes_char_sum = cursor.fetchone()[0] or 0
        
        # Count characters in books (titles)
        cursor.execute("SELECT SUM(length(title)) FROM books")
        books_char_sum = cursor.fetchone()[0] or 0
        
        # Estimate tokens (approx 4 chars per token)
        notes_tokens = int(notes_char_sum / 4)
        books_tokens = int(books_char_sum / 4)
        total_tokens = notes_tokens + books_tokens
        
        # Count items
        cursor.execute("SELECT COUNT(*) FROM books")
        total_books = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM authors")
        total_authors = cursor.fetchone()[0] or 0
        
        return {
            "total_books": total_books,
            "total_authors": total_authors,
            "notes_tokens": notes_tokens,
            "books_tokens": books_tokens,
            "total_tokens": total_tokens
        }
    finally:
        conn.close()

@router.get("/{book_id}", response_model=BookResponse)
async def get_book(book_id: str):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT b.*, a.name as author_name 
            FROM books b
            LEFT JOIN authors a ON b.author_id = a.id
            WHERE b.id = ?
            """, (book_id,)
        )
        r = cursor.fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="Book not found")
        
        # Check if created_at is present, fallback if not
        created_at_val = r["created_at"] if "created_at" in r.keys() and r["created_at"] else ""
        
        return {
            "id": r["id"],
            "title": r["title"],
            "file_path": r["file_path"],
            "author_name": r["author_name"],
            "created_at": created_at_val
        }
    finally:
        conn.close()



class PageExtractionRequest(BaseModel):
    start_page: int
    end_page: Optional[int] = None

@router.get("/{book_id}/pages/{page_number}")
async def get_page_text(book_id: str, page_number: int):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT content, extracted_at FROM book_pages WHERE book_id = ? AND page_number = ?", (book_id, page_number))
        row = cursor.fetchone()
        if row:
            return {"page_number": page_number, "content": row["content"], "extracted": True, "extracted_at": row["extracted_at"]}
        return {"page_number": page_number, "content": None, "extracted": False}
    finally:
        conn.close()

import asyncio

@router.post("/{book_id}/extract")
async def extract_pages(book_id: str, req: PageExtractionRequest, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # In a real application, we would call an AI model here.
        # For now, we mock the extraction process with a simulated delay.
        
        start = req.start_page
        end = req.end_page if req.end_page else start
        
        # Simulate processing time for realistic UI testing
        await asyncio.sleep(1.5)
        
        for p in range(start, end + 1):
            mock_text = f"Mock AI Extracted Text for Page {p}.\n\nبِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ\nThis is a placeholder demonstrating that the page was saved to the database."
            
            new_id = str(uuid.uuid4())
            cursor.execute(
                """
                INSERT INTO book_pages (id, book_id, page_number, content) 
                VALUES (?, ?, ?, ?)
                ON CONFLICT(book_id, page_number) DO UPDATE SET content=excluded.content, extracted_at=CURRENT_TIMESTAMP
                """, (new_id, book_id, p, mock_text)
            )
        conn.commit()
        
        return {"status": "success", "extracted_pages": end - start + 1}
    finally:
        conn.close()

from fastapi.responses import FileResponse
import fitz  # PyMuPDF

@router.get("/{book_id}/thumbnail")
async def get_book_thumbnail(book_id: str):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT file_path FROM books WHERE id = ?", (book_id,))
        row = cursor.fetchone()
        if not row or not row["file_path"]:
            raise HTTPException(status_code=404, detail="Book or file not found")
        
        pdf_path = row["file_path"]
        if not os.path.exists(pdf_path):
            # Try appending relative to backend root
            pdf_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), pdf_path)
            if not os.path.exists(pdf_path):
                raise HTTPException(status_code=404, detail="PDF file missing on disk")
        
        thumb_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads", "thumbnails")
        os.makedirs(thumb_dir, exist_ok=True)
        thumb_path = os.path.join(thumb_dir, f"{book_id}.png")
        
        # Generate thumbnail if it doesn't exist
        if not os.path.exists(thumb_path):
            try:
                doc = fitz.open(pdf_path)
                if len(doc) > 0:
                    page = doc[0]
                    # Scale down for a thumbnail
                    matrix = fitz.Matrix(0.3, 0.3)
                    pix = page.get_pixmap(matrix=matrix, alpha=False)
                    pix.save(thumb_path)
                doc.close()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to generate thumbnail: {str(e)}")
                
        if not os.path.exists(thumb_path):
            raise HTTPException(status_code=404, detail="Failed to create thumbnail")
            
        return FileResponse(thumb_path, media_type="image/png")
    finally:
        conn.close()

@router.get("/{book_id}/render/{page_number}")
async def render_book_page(book_id: str, page_number: int):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT file_path FROM books WHERE id = ?", (book_id,))
        row = cursor.fetchone()
        if not row or not row["file_path"]:
            raise HTTPException(status_code=404, detail="Book or file not found")
        
        pdf_path = row["file_path"]
        if not os.path.exists(pdf_path):
            pdf_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), pdf_path)
            if not os.path.exists(pdf_path):
                raise HTTPException(status_code=404, detail="PDF file missing on disk")
                
        page_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads", "pages")
        os.makedirs(page_dir, exist_ok=True)
        # Use a unique name for cache
        page_path = os.path.join(page_dir, f"{book_id}_page_{page_number}.png")
        
        if not os.path.exists(page_path):
            try:
                doc = fitz.open(pdf_path)
                # fitz is 0-indexed, UI is 1-indexed
                zero_index = page_number - 1
                if zero_index < 0 or zero_index >= len(doc):
                    raise HTTPException(status_code=400, detail="Page out of bounds")
                    
                page = doc[zero_index]
                # High resolution render (e.g., zoom 2x)
                matrix = fitz.Matrix(2.0, 2.0)
                pix = page.get_pixmap(matrix=matrix, alpha=False)
                pix.save(page_path)
                doc.close()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to render page: {str(e)}")
                
        if not os.path.exists(page_path):
            raise HTTPException(status_code=404, detail="Failed to render page")
            
        return FileResponse(page_path, media_type="image/png")
    finally:
        conn.close()

