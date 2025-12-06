import google.generativeai as genai
from app.config import settings
from loguru import logger
import time

class GeminiClient:
    def __init__(self):
        if not settings.GOOGLE_API_KEY:
            logger.error("GOOGLE_API_KEY is missing!")
            raise ValueError("GOOGLE_API_KEY must be set in .env")
        
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.models = settings.GEMINI_MODELS

    def generate_content(self, prompt: str, image_bytes: bytes = None) -> str:
        """
        Generates content using the first working model from the fallback list.
        """
        inputs = [prompt]
        if image_bytes:
            # Create a dict for the image part as expected by genai
            import PIL.Image
            import io
            try:
                img = PIL.Image.open(io.BytesIO(image_bytes))
                inputs.append(img)
            except Exception as e:
                logger.error(f"Failed to process image bytes: {e}")
                raise

        last_error = None
        
        for model_name in self.models:
            try:
                logger.info(f"Attempting generation with model: {model_name}")
                model = genai.GenerativeModel(model_name)
                
                # Basic generation config
                config = genai.types.GenerationConfig(
                    temperature=0.4,
                    candidate_count=1
                )
                
                response = model.generate_content(
                    inputs,
                    generation_config=config 
                )
                
                if response.text:
                    logger.success(f"Success with model: {model_name}")
                    return response.text
                
            except Exception as e:
                logger.warning(f"Model {model_name} failed: {e}")
                last_error = e
                continue # Try next model
        
        # If we reach here, all models failed
        logger.critical("All Gemini models failed to generate content.")
        raise RuntimeError(f"All models failed. Last error: {last_error}")

gemini_client = GeminiClient()
