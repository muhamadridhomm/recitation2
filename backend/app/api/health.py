from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def health_check():
    """
    Basic health check endpoint to verify backend connectivity.
    """
    return {"status": "ok", "message": "Arabic Document Intelligence Gateway is running."}
