import asyncio
import pytest
from types import SimpleNamespace

from app.core import search


class FakeResponse:
    def __init__(self, status_code=200, json_data=None, text=""):
        self.status_code = status_code
        self._json_data = json_data
        self.text = text

    def json(self):
        if isinstance(self._json_data, Exception):
            raise self._json_data
        return self._json_data


class FakeClient:
    def __init__(self, responses):
        self._responses = iter(responses)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, *_args, **_kwargs):
        # Async to mirror httpx.AsyncClient interface
        return next(self._responses)


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    original_sleep = asyncio.sleep

    async def _noop(duration):
        # Async no-op to bypass real sleeping in tests while avoiding recursion
        return await original_sleep(0)

    monkeypatch.setattr(asyncio, "sleep", _noop)


def _patch_settings(monkeypatch, **overrides):
    for key, value in overrides.items():
        monkeypatch.setattr(search.settings, key, value)


def _patch_client(monkeypatch, responses):
    # Share a single iterator across retries so subsequent attempts advance
    resp_iter = iter(responses)
    monkeypatch.setattr(search.httpx, "AsyncClient", lambda timeout=10.0: FakeClient(resp_iter))


def _new_client(monkeypatch, **settings_overrides):
    _patch_settings(monkeypatch, **settings_overrides)
    return search.SerpAPIWrapper()


@pytest.mark.asyncio
async def test_missing_api_key_returns_error(monkeypatch):
    client = _new_client(monkeypatch, SERPAPI_API_KEY="")
    result = await client.search_food_info("apple calories")
    assert result == {"error": "API Key missing"}


@pytest.mark.asyncio
async def test_429_then_success(monkeypatch):
    client = _new_client(monkeypatch, SERPAPI_API_KEY="k", SERPAPI_MIN_INTERVAL=0.0, SERPAPI_MAX_RETRIES=2, SERPAPI_BACKOFF_FACTOR=1.0)
    responses = [
        FakeResponse(status_code=429, text="rate limited"),
        FakeResponse(
            status_code=200,
            json_data={
                "knowledge_graph": {"knowledge_data": 1},
                "organic_results": [
                    {"title": "Test Title", "snippet": "Test Snippet", "link": "https://example.com"}
                ],
            },
        ),
    ]
    _patch_client(monkeypatch, responses)

    result = await client.search_food_info("apple calories")
    assert result["knowledge_graph"] == {"knowledge_data": 1}
    assert result["snippets"][0]["title"] == "Test Title"


@pytest.mark.asyncio
async def test_http_error_exhausts_and_returns_status(monkeypatch):
    client = _new_client(monkeypatch, SERPAPI_API_KEY="k", SERPAPI_MIN_INTERVAL=0.0, SERPAPI_MAX_RETRIES=1, SERPAPI_BACKOFF_FACTOR=1.0)
    responses = [
        FakeResponse(status_code=500, text="server error"),
        FakeResponse(status_code=500, text="still bad"),
    ]
    _patch_client(monkeypatch, responses)

    result = await client.search_food_info("apple calories")
    assert result["error"] == "SerpAPI request failed after retries"
    assert result["status"] == 500
    assert (result.get("detail") or "") == "still bad"


@pytest.mark.asyncio
async def test_invalid_json_then_success(monkeypatch):
    client = _new_client(monkeypatch, SERPAPI_API_KEY="k", SERPAPI_MIN_INTERVAL=0.0, SERPAPI_MAX_RETRIES=2, SERPAPI_BACKOFF_FACTOR=1.0)
    responses = [
        FakeResponse(status_code=200, json_data=ValueError("bad json"), text="not json"),
        FakeResponse(status_code=200, json_data={"knowledge_graph": {}, "organic_results": []}),
    ]
    _patch_client(monkeypatch, responses)

    result = await client.search_food_info("apple calories")
    assert result["knowledge_graph"] == {}


@pytest.mark.asyncio
async def test_invalid_json_exhaustion(monkeypatch):
    client = _new_client(monkeypatch, SERPAPI_API_KEY="k", SERPAPI_MIN_INTERVAL=0.0, SERPAPI_MAX_RETRIES=0, SERPAPI_BACKOFF_FACTOR=1.0)
    responses = [
        FakeResponse(status_code=200, json_data=ValueError("bad json"), text="not json"),
    ]
    _patch_client(monkeypatch, responses)

    result = await client.search_food_info("apple calories")
    assert result["error"] == "SerpAPI request failed after retries"
    assert result["detail"] == "invalid json"