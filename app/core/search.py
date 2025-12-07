import asyncio
import time
import httpx
from loguru import logger
from app.config import settings
from async_lru import alru_cache

class SerpAPIWrapper:
    def __init__(self):
        self.api_key = settings.SERPAPI_API_KEY
        self.base_url = "https://serpapi.com/search"
        self._lock = asyncio.Lock()
        self._last_request_ts = 0.0
        # Use the configured minimum interval for throttling. If a lower bound is required, enforce it in config.py and document it there.
        self.min_interval = settings.SERPAPI_MIN_INTERVAL
        self.max_retries = max(0, settings.SERPAPI_MAX_RETRIES)
        self.backoff_factor = max(1.0, settings.SERPAPI_BACKOFF_FACTOR)

    async def _throttle(self):
        """Ensure a minimum delay between outbound SerpAPI calls."""
        async with self._lock:
            now = time.monotonic()
            wait = self.min_interval - (now - self._last_request_ts)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_request_ts = time.monotonic()

    def _should_retry(self, attempt: int) -> bool:
        return attempt < self.max_retries

    async def _sleep_with_backoff(self, backoff: float) -> float:
        await asyncio.sleep(backoff)
        return backoff * self.backoff_factor

    async def _request_with_retry(self, params: dict):
        """Throttled SerpAPI call with retry/backoff. Returns (data, status, detail)."""
        backoff = self.min_interval
        last_status = None
        last_detail = None

        for attempt in range(self.max_retries + 1):
            await self._throttle()

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.base_url, params=params)

            last_status = response.status_code
            last_detail = response.text[:300] if response.text else None

            if response.status_code >= 400:
                logger.warning(
                    f"SerpAPI {response.status_code} received; backing off {backoff:.2f}s (attempt {attempt+1}/{self.max_retries})"
                )

                if self._should_retry(attempt):
                    backoff = await self._sleep_with_backoff(backoff)
                    continue

                return None, last_status, last_detail

            try:
                data = response.json()
            except ValueError:
                logger.error("SerpAPI response JSON decode failed")
                if self._should_retry(attempt):
                    backoff = await self._sleep_with_backoff(backoff)
                    continue
                return None, last_status, "invalid json"

            return data, last_status, last_detail

        return None, last_status, last_detail

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
            data, last_status, last_detail = await self._request_with_retry(params)

            if data is None:
                return {
                    "error": "SerpAPI request failed after retries",
                    "status": last_status,
                    "detail": last_detail,
                }
            
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
            status = getattr(getattr(e, "response", None), "status_code", None)
            detail = getattr(getattr(e, "response", None), "text", None)
            logger.error(f"SerpAPI request failed: {e}")
            return {
                "error": str(e),
                "status": status,
                "detail": detail[:300] if detail else None,
            }
        except Exception as e:
            logger.error(f"Unexpected search error: {e}")
            return {"error": str(e)}

search_client = SerpAPIWrapper()
