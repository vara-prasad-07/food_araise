import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.core.vision import analyze_food_image_with_search

@pytest.mark.asyncio
async def test_vision_pipeline_flow():
    # Mock Dependencies
    with patch("app.core.vision.gemini_client") as mock_gemini, \
         patch("app.core.vision.search_client") as mock_search, \
         patch("app.core.vision._resize_image") as mock_resize:
        
        # 1. Setup Mock Outputs
        mock_resize.return_value = b"resized_bytes"
        
        # Step 1: Identify returns a list of items
        mock_gemini.generate_content.side_effect = [
            "Apple (1 medium), Banana (1 small)", # First call (Identify)
            '{"overall_description": "Final Report"}' # Second call (Synthesize)
        ]
        
        # Step 2: Search returns data
        mock_search.search_food_info = AsyncMock(return_value={"calories": 50})
        
        # 2. Run Function
        result = await analyze_food_image_with_search(b"original_bytes")
        
        # 3. Assertions
        
        # Check Verify Resize
        mock_resize.assert_called_once()
        
        # Check Gemini was called twice (Identify + Synthesize)
        assert mock_gemini.generate_content.call_count == 2
        
        # Check Search was called for each item
        assert mock_search.search_food_info.call_count == 2
        
        # Check Final Result
        assert result == {"overall_description": "Final Report"}
