import httpx
from loguru import logger
from app.config import settings
from async_lru import alru_cache

class SerpAPIWrapper:
    def __init__(self):
        self.api_key = settings.SERPAPI_API_KEY
        self.base_url = "https://serpapi.com/search"

    @alru_cache(maxsize=128) # lightweight RAM-efficient caching
    async def search_food_info(self, query: str) -> dict:
        """
        Searches for food information using SerpAPI.
        Async + Cached.
        """
        if not self.api_key:
            logger.warning("SerpAPI Key is missing. Skipping web search.")
            return {"error": "API Key missing"}

        logger.info(f"Searching SerpAPI for: {query}")
        
        params = {
            "engine": "google",
            "q": query,
            "api_key": self.api_key,
            "hl": "en",
            "gl": "us"
        }

        try:
            # Threading/Concurrency: await non-blocking IO
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                data = response.json()
            
            # RAM Efficiency: Extract only what's needed, discard the rest
            results = {
                "snippets": [],
                "knowledge_graph": data.get("knowledge_graph", {})
            }

            if "organic_results" in data:
                for res in data["organic_results"][:3]: # Limit to top 3
                    results["snippets"].append({
                        "title": res.get("title"),
                        "snippet": res.get("snippet"),
                        "link": res.get("link")
                    })
            
            return results

        except httpx.HTTPError as e:
            logger.error(f"SerpAPI request failed: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected search error: {e}")
            return {"error": str(e)}

search_client = SerpAPIWrapper()
