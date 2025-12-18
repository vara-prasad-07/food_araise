from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import food
from app.config import settings
from loguru import logger

# Initialize Logging

logger.add("server.log", rotation="500 MB", level="INFO")

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered Food Analysis API with Search and Vision integration.",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(food.router, prefix="/api/v1/food", tags=["Food Analysis"])

@app.get("/")
def health_check():
    return {
        "status": "online",
        "app": settings.APP_NAME,
        "models_configured": settings.GEMINI_MODELS
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)