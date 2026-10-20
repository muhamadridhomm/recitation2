from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid
from app.auth.jwt_handler import get_current_user
from app.core.db import get_db_connection

router = APIRouter(prefix="/projects", tags=["projects"])

# Pydantic Schemas
class ProjectCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    description: Optional[str] = None
    document_id: Optional[str] = None
    teacher_id: Optional[str] = None

class ProjectResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    document_id: Optional[str]
    teacher_id: Optional[str]
    teacher_name: Optional[str] = None
    created_by: str
    is_public: bool
    forked_from_id: Optional[str]
    created_at: str

class CommitCreate(BaseModel):
    commit_message: str = Field(..., min_length=1)
    content: str
    branch_name: str = "main"

class CommitResponse(BaseModel):
    id: str
    project_id: str
    parent_commit_id: Optional[str]
    author_id: str
    commit_message: str
    content: str
    timestamp: str

class BranchResponse(BaseModel):
    id: str
    project_id: str
    name: str
    head_commit_id: str

# Endpoints
@router.post("", response_model=ProjectResponse)
async def create_project(project: ProjectCreate, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Verify book exists if provided
        if project.document_id:
            cursor.execute("SELECT id FROM books WHERE id = ?", (project.document_id,))
            book = cursor.fetchone()
            if not book:
                cursor.execute(
                    "INSERT OR IGNORE INTO books (id, title, file_path) VALUES (?, ?, ?)",
                    (project.document_id, "Sample Book", "uploads/sample.pdf")
                )
        
        # Verify teacher exists if provided
        teacher_name = None
        if project.teacher_id:
            cursor.execute("SELECT name FROM authors WHERE id = ?", (project.teacher_id,))
            teacher = cursor.fetchone()
            if not teacher:
                raise HTTPException(status_code=400, detail="Specified Teacher/Ustadz not found")
            teacher_name = teacher["name"]
        
        project_id = str(uuid.uuid4())
        is_public = 1
        created_at = datetime.utcnow().isoformat()
        
        # 1. Create project row
        cursor.execute(
            """
            INSERT INTO note_projects (id, title, description, document_id, teacher_id, created_by, is_public, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (project_id, project.title, project.description, project.document_id, project.teacher_id, current_user["id"], is_public, created_at)
        )
        
        # 2. Create initial commit
        commit_id = str(uuid.uuid4())
        cursor.execute(
            """
            INSERT INTO commits (id, project_id, parent_commit_id, author_id, commit_message, content, timestamp)
            VALUES (?, ?, NULL, ?, 'Initial commit', '', ?)
            """,
            (commit_id, project_id, current_user["id"], created_at)
        )
        
        # 3. Create main branch pointing to initial commit
        branch_id = str(uuid.uuid4())
        cursor.execute(
            """
            INSERT INTO branches (id, project_id, name, head_commit_id)
            VALUES (?, ?, 'main', ?)
            """,
            (branch_id, project_id, commit_id)
        )
        
        conn.commit()
        return {
            "id": project_id,
            "title": project.title,
            "description": project.description,
            "document_id": project.document_id,
            "teacher_id": project.teacher_id,
            "teacher_name": teacher_name,
            "created_by": current_user["id"],
            "is_public": True,
            "forked_from_id": None,
            "created_at": created_at
        }
    finally:
        conn.close()

@router.get("", response_model=List[ProjectResponse])
async def list_projects(public: bool = True, current_user: Optional[dict] = Depends(get_current_user)):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        query = """
            SELECT np.*, a.name as teacher_name 
            FROM note_projects np
            LEFT JOIN authors a ON np.teacher_id = a.id
        """
        if public:
            cursor.execute(query + " WHERE np.is_public = 1")
        else:
            if not current_user:
                raise HTTPException(status_code=401, detail="Authentication required for private projects")
            cursor.execute(query + " WHERE np.created_by = ?", (current_user["id"],))
        
        rows = cursor.fetchall()
        projects = []
        for r in rows:
            projects.append({
                "id": r["id"],
                "title": r["title"],
                "description": r["description"],
                "document_id": r["document_id"],
                "teacher_id": r["teacher_id"],
                "teacher_name": r["teacher_name"],
                "created_by": r["created_by"],
                "is_public": bool(r["is_public"]),
                "forked_from_id": r["forked_from_id"],
                "created_at": r["created_at"]
            })
        return projects
    finally:
        conn.close()

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT np.*, a.name as teacher_name 
            FROM note_projects np
            LEFT JOIN authors a ON np.teacher_id = a.id
            WHERE np.id = ?
            """, 
            (project_id,)
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Project not found")
        return {
            "id": row["id"],
            "title": row["title"],
            "description": row["description"],
            "document_id": row["document_id"],
            "teacher_id": row["teacher_id"],
            "teacher_name": row["teacher_name"],
            "created_by": row["created_by"],
            "is_public": bool(row["is_public"]),
            "forked_from_id": row["forked_from_id"],
            "created_at": row["created_at"]
        }
    finally:
        conn.close()


@router.post("/{project_id}/commit", response_model=CommitResponse)
async def create_commit(project_id: str, commit_data: CommitCreate, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # 1. Verify project exists
        cursor.execute("SELECT id FROM note_projects WHERE id = ?", (project_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Project not found")
        
        # 2. Get the head commit of the branch
        cursor.execute(
            "SELECT head_commit_id FROM branches WHERE project_id = ? AND name = ?",
            (project_id, commit_data.branch_name)
        )
        branch = cursor.fetchone()
        if not branch:
            raise HTTPException(status_code=400, detail=f"Branch '{commit_data.branch_name}' not found")
        
        parent_commit_id = branch["head_commit_id"]
        commit_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        # 3. Create commit
        cursor.execute(
            """
            INSERT INTO commits (id, project_id, parent_commit_id, author_id, commit_message, content, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (commit_id, project_id, parent_commit_id, current_user["id"], commit_data.commit_message, commit_data.content, timestamp)
        )
        
        # 4. Update head commit of the branch
        cursor.execute(
            "UPDATE branches SET head_commit_id = ? WHERE project_id = ? AND name = ?",
            (commit_id, project_id, commit_data.branch_name)
        )
        
        conn.commit()
        return {
            "id": commit_id,
            "project_id": project_id,
            "parent_commit_id": parent_commit_id,
            "author_id": current_user["id"],
            "commit_message": commit_data.commit_message,
            "content": commit_data.content,
            "timestamp": timestamp
        }
    finally:
        conn.close()

@router.get("/{project_id}/branches/{branch_name}/head", response_model=CommitResponse)
async def get_branch_head(project_id: str, branch_name: str):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT c.* FROM commits c
            JOIN branches b ON b.head_commit_id = c.id
            WHERE b.project_id = ? AND b.name = ?
            """,
            (project_id, branch_name)
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Branch or Commit not found")
        return {
            "id": row["id"],
            "project_id": row["project_id"],
            "parent_commit_id": row["parent_commit_id"],
            "author_id": row["author_id"],
            "commit_message": row["commit_message"],
            "content": row["content"],
            "timestamp": row["timestamp"]
        }
    finally:
        conn.close()

@router.post("/{project_id}/fork", response_model=ProjectResponse)
async def fork_project(project_id: str, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # 1. Fetch original project details
        cursor.execute("SELECT * FROM note_projects WHERE id = ?", (project_id,))
        orig = cursor.fetchone()
        if not orig:
            raise HTTPException(status_code=404, detail="Original project not found")
        
        # 2. Get head commit of main branch on original project
        cursor.execute("SELECT head_commit_id FROM branches WHERE project_id = ? AND name = 'main'", (project_id,))
        branch = cursor.fetchone()
        if not branch:
            raise HTTPException(status_code=400, detail="Cannot fork: original project has no main branch")
        orig_head_commit_id = branch["head_commit_id"]
        
        # Fetch content of original head commit
        cursor.execute("SELECT content FROM commits WHERE id = ?", (orig_head_commit_id,))
        orig_commit = cursor.fetchone()
        orig_content = orig_commit["content"] if orig_commit else ""
        
        new_project_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()
        new_title = f"Fork of {orig['title']}"
        
        # 3. Create forked project row
        cursor.execute(
            """
            INSERT INTO note_projects (id, title, description, document_id, teacher_id, created_by, is_public, forked_from_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
            """,
            (new_project_id, new_title, orig["description"], orig["document_id"], orig["teacher_id"], current_user["id"], project_id, created_at)
        )
        
        # 4. Create new commit carrying over the notes content
        new_commit_id = str(uuid.uuid4())
        cursor.execute(
            """
            INSERT INTO commits (id, project_id, parent_commit_id, author_id, commit_message, content, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (new_commit_id, new_project_id, orig_head_commit_id, current_user["id"], "Initial fork commit", orig_content, created_at)
        )
        
        # 5. Create new main branch pointing to this new commit
        new_branch_id = str(uuid.uuid4())
        cursor.execute(
            """
            INSERT INTO branches (id, project_id, name, head_commit_id)
            VALUES (?, ?, 'main', ?)
            """,
            (new_branch_id, new_project_id, new_commit_id)
        )
        
        # Resolve teacher name if any
        teacher_name = None
        if orig["teacher_id"]:
            cursor.execute("SELECT name FROM authors WHERE id = ?", (orig["teacher_id"],))
            teacher = cursor.fetchone()
            if teacher:
                teacher_name = teacher["name"]

        conn.commit()
        return {
            "id": new_project_id,
            "title": new_title,
            "description": orig["description"],
            "document_id": orig["document_id"],
            "teacher_id": orig["teacher_id"],
            "teacher_name": teacher_name,
            "created_by": current_user["id"],
            "is_public": True,
            "forked_from_id": project_id,
            "created_at": created_at
        }

    finally:
        conn.close()
