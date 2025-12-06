from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class NutritionalInfo(BaseModel):
    calories: Optional[str] = Field(None, description="Estimated calories")
    protein: Optional[str] = Field(None, description="Protein content")
    carbs: Optional[str] = Field(None, description="Carbohydrate content")
    fats: Optional[str] = Field(None, description="Fat content")
    vitamins: Optional[List[str]] = Field(default_factory=list, description="Key vitamins")

class IdentifiedItem(BaseModel):
    name: str = Field(..., description="Name of the food item")
    confidence: float = Field(..., description="Confidence score 0-1")
    description: Optional[str] = Field(None, description="Brief description")
    nutrition: Optional[NutritionalInfo] = Field(None, description="Nutritional details")
    search_insights: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Data retrieved from web search")

class FoodAnalysisResponse(BaseModel):
    overall_description: str = Field(..., description="Summary of the entire meal")
    items: List[IdentifiedItem] = Field(default_factory=list, description="List of identified food components")
    total_calories_estimate: Optional[str] = Field(None, description="Estimated total calories for the meal")
    health_score: Optional[int] = Field(None, description="Health rating 1-10")
    dietary_warnings: List[str] = Field(default_factory=list, description="e.g. High Sugar, Gluten, etc.")