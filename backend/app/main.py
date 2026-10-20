from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.db import init_db
from app.api import health, auth, projects, reviews, authors, books, ai

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

# Set up CORS middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include Routers
from fastapi.staticfiles import StaticFiles
import os

app.include_router(health.router, prefix="/api", tags=["system"])
app.include_router(auth.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(reviews.router, prefix="/api")
app.include_router(authors.router, prefix="/api")
app.include_router(books.router, prefix="/api")
app.include_router(ai.router, prefix="/api")

# Mount uploads static folder
uploads_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")





@app.get("/")
def root():
    return {"message": "Welcome to the Arabic Document Intelligence API"}

