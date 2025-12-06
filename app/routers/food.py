from fastapi import APIRouter, UploadFile, File, HTTPException
from app.core.vision import analyze_food_image_with_search
from app.schemas import FoodAnalysisResponse
from loguru import logger

router = APIRouter()

@router.post("/analyze", response_model=FoodAnalysisResponse)
async def analyze_food(file: UploadFile = File(...)):
    """
    Analyzes a food image using AI and Web Search.
    
    - **Step 1**: Identifies items using a fast AI model.
    - **Step 2**: Verified nutritional info via live web search (SerpAPI).
    - **Step 3**: Synthesizes a comprehensive report using a high-fidelity AI model.
    """
    logger.info(f"Received image analysis request: {file.filename}")
    
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")

    try:
        contents = await file.read()
        result = await analyze_food_image_with_search(contents)
        return result
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))