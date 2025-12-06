from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch, AsyncMock
import pytest

client = TestClient(app)

@pytest.fixture
def mock_vision_analysis():
    with patch("app.routers.food.analyze_food_image_with_search", new_callable=AsyncMock) as mock:
        yield mock

def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_analyze_endpoint_no_file():
    response = client.post("/api/v1/food/analyze")
    assert response.status_code == 422 # Validator error for missing file

def test_analyze_endpoint_valid_image(mock_vision_analysis):
    # Setup mock return value
    mock_result = {
        "overall_description": "Test Food",
        "items": [],
        "total_calories_estimate": "100",
        "health_score": 10,
        "dietary_warnings": []
    }
    mock_vision_analysis.return_value = mock_result

    # Fake image bytes
    file_content = b"fake_image_bytes"
    files = {"file": ("test.jpg", file_content, "image/jpeg")}

    response = client.post("/api/v1/food/analyze", files=files)
    
    assert response.status_code == 200
    assert response.json() == mock_result
