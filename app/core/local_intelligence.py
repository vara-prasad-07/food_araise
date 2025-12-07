import os
from huggingface_hub import hf_hub_download
from loguru import logger
from app.config import settings
import json

class LocalIntelligenceClient:
    def __init__(self):
        self.models_dir = os.path.join(os.getcwd(), settings.LOCAL_MODELS_DIR)
        os.makedirs(self.models_dir, exist_ok=True)
        
        self.light_model = None
        self.heavy_model = None
        
        # We don't load models at init to save RAM until needed

    def ensure_models_available(self, download_missing: bool = False) -> bool:
        """Checks for required local GGUF files. Optionally downloads if missing."""
        required = [
            (settings.LOCAL_MODEL_LIGHT_REPO, settings.LOCAL_MODEL_LIGHT_FILENAME),
            (settings.LOCAL_MODEL_HEAVY_REPO, settings.LOCAL_MODEL_HEAVY_FILENAME),
        ]

        missing = []
        for repo, filename in required:
            path = os.path.join(self.models_dir, filename)
            if not os.path.isfile(path):
                missing.append((repo, filename))

        if not missing:
            return True

        logger.warning(f"Local failsafe models missing: {[f for _, f in missing]}")
        if not download_missing:
            return False

        for repo, filename in missing:
            try:
                self._get_model_path(repo, filename)
            except Exception as e:
                logger.error(f"Auto-download failed for {filename}: {e}")
                return False

        return True

    def _get_model_path(self, repo_id: str, filename: str) -> str:
        """Downloads model if missing and returns path."""
        try:
            logger.info(f"Checking for local model: {filename} in {repo_id}")
            model_path = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                local_dir=self.models_dir,
                local_dir_use_symlinks=False
            )
            return model_path
        except Exception as e:
            logger.error(f"Failed to download model {filename}: {e}")
            raise

    def _load_model(self, model_type: str):
        """Lazy loads the specific model type, unloading others to save RAM."""
        from llama_cpp import Llama
        from llama_cpp.llama_chat_format import MoondreamChatHandler, Llava15ChatHandler

        if model_type == "light":
            if self.light_model: return
            
            # Unload heavy if loaded
            if self.heavy_model:
                logger.info("Unloading Heavy Model to free RAM...")
                del self.heavy_model
                self.heavy_model = None
            
            logger.info("Loading Light Model (Moondream)...")
            path = self._get_model_path(settings.LOCAL_MODEL_LIGHT_REPO, settings.LOCAL_MODEL_LIGHT_FILENAME)
            
            self.light_model = Llama(
                model_path=path,
                n_ctx=2048,
                n_gpu_layers=0,
                verbose=False
            )

        elif model_type == "heavy":
            if self.heavy_model: return
            
            # Unload light if loaded
            if self.light_model:
                logger.info("Unloading Light Model to free RAM...")
                del self.light_model
                self.light_model = None
                
            logger.info("Loading Heavy Model (Phi-3.5/LLaVA)...")
            path = self._get_model_path(settings.LOCAL_MODEL_HEAVY_REPO, settings.LOCAL_MODEL_HEAVY_FILENAME)
            
            self.heavy_model = Llama(
                model_path=path,
                n_ctx=4096,
                n_gpu_layers=0,
                verbose=True
            )

    def analyze_image(self, image_bytes: bytes, deep_search: bool = False) -> dict:
        """
        Analyzes image using local model.
        deep_search=False -> Light Model (<5s)
        deep_search=True -> Heavy Model (>10s)
        """
        import base64
        
        target_model_type = "heavy" if deep_search else "light"
        if not self.ensure_models_available(download_missing=True):
            logger.error("Local failsafe models are not available and could not be downloaded.")
            return {
                "overall_description": "Local failsafe models are missing. Please download them (see README).",
                "total_calories_estimate": "Unknown",
                "items": [],
                "note": "Failsafe unavailable"
            }
        self._load_model(target_model_type)
        model = self.heavy_model if deep_search else self.light_model
        
        # Prepare Image
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        image_url = f"data:image/jpeg;base64,{base64_image}"
        
        system_prompt = (
            "You are a food AI. Identify food items and estimate calories. "
            "Return JSON with keys: 'overall_description', 'items' (list of {name, nutrition}), 'total_calories_estimate'. "
            "Keep description brief."
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": [
                {"type": "text", "text": "Analyze this food."},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]}
        ]

        try:
            response = model.create_chat_completion(
                messages=messages,
                max_tokens=300 if deep_search else 150,
                temperature=0.2
            )
            content = response["choices"][0]["message"]["content"]
            
            # Use basic string parsing if JSON is messy (common in small models)
            # But try to parse JSON first
            return self._parse_local_response(content)
            
        except Exception as e:
            logger.error(f"Local inference failed: {e}")
            # Return emergency fallback
            return {
                "overall_description": "Error in local analysis.",
                "total_calories_estimate": "Unknown",
                "items": [{"name": "Unidentified", "nutrition": {}, "description": "Analysis failed"}]
            }

    def _parse_local_response(self, content: str) -> dict:
        """Attempts to parse JSON from local model output."""
        try:
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = content[start:end]
                return json.loads(json_str)
        except Exception:
            pass
            
        # Fallback if valid JSON not found
        return {
            "overall_description": content[:200] + "...",
            "total_calories_estimate": "Estimated",
            "items": [],
            "note": "Raw output returned due to parsing error."
        }

local_client = LocalIntelligenceClient()
