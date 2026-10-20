from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.models.user import UserCreate, UserResponse, Token
from app.auth.jwt_handler import get_password_hash, verify_password, create_access_token
from app.core.db import get_db_connection
from datetime import timedelta
import uuid

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Check if email is already registered
        cursor.execute("SELECT id FROM users WHERE email = ?", (user.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Check if username is already registered
        cursor.execute("SELECT id FROM users WHERE username = ?", (user.username,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Username already registered")
        
        user_id = str(uuid.uuid4())
        hashed_password = get_password_hash(user.password)
        role = "student"
        is_active = 1

        with conn:
            conn.execute(
                "INSERT INTO users (id, username, email, hashed_password, role, is_active) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, user.username, user.email, hashed_password, role, is_active)
            )

        return {
            "id": user_id,
            "username": user.username,
            "email": user.email,
            "role": role,
            "is_active": True
        }
    finally:
        conn.close()

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Fetch user by email (form_data.username contains email)
        cursor.execute("SELECT * FROM users WHERE email = ?", (form_data.username,))
        user = cursor.fetchone()
        
        if not user or not verify_password(form_data.password, user["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = create_access_token(
            data={"sub": user["email"], "role": user["role"]},
            expires_delta=timedelta(days=7)
        )
        return {"access_token": access_token, "token_type": "bearer"}
    finally:
        conn.close()

