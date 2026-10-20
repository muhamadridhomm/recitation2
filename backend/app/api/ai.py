from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import uuid
from app.auth.jwt_handler import get_current_user
from app.core.db import get_db_connection

router = APIRouter(prefix="/ai", tags=["ai"])

class AIConfigSet(BaseModel):
    model_type: str
    provider: str
    api_key: str

@router.get("/config")
async def get_ai_config(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ai_configs WHERE user_id = ? AND is_active = 1", (current_user["id"],))
        config = cursor.fetchone()
        if config:
            return {"configured": True, "model_type": config["model_type"], "provider": config["provider"]}
        return {"configured": False}
    finally:
        conn.close()

@router.post("/config")
async def set_ai_config(config: AIConfigSet, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Deactivate old configs
        cursor.execute("UPDATE ai_configs SET is_active = 0 WHERE user_id = ?", (current_user["id"],))
        
        new_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO ai_configs (id, user_id, model_type, provider, api_key, is_active) VALUES (?, ?, ?, ?, ?, 1)",
            (new_id, current_user["id"], config.model_type, config.provider, config.api_key)
        )
        conn.commit()
        return {"status": "success"}
    finally:
        conn.close()
