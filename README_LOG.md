# Project Activity Log

A chronological summary of key changes and fixes applied during this session.

## Recent updates

- Added Gradio UI (`ui_tester.py`) that hits the FastAPI `/api/v1/food/analyze` endpoint with configurable base URL and deep-search toggle.
- Enhanced configuration to accept `LOG_LEVEL` and ignore extra env vars, preventing pydantic validation errors.
- Implemented SerpAPI throttling/backoff with retries, centralized 429 handling, and informative error payloads (status/detail) including JSON decode safeguards.
- Refactored SerpAPI logic to reduce duplication and cognitive complexity.
- Added comprehensive SerpAPI unit tests covering missing API key, 429 retry success, HTTP error exhaustion, JSON decode retry/success, and JSON decode exhaustion scenarios.
- Maintained existing failsafe/local model behavior for vision pipeline.

## Testing

- Full pytest suite now covers API endpoints, vision pipeline flows, failsafe behaviors, and SerpAPI edge cases.
- Latest run: all tests passing (`python -m pytest`).

## Notes

- SerpAPI pacing knobs: `SERPAPI_MIN_INTERVAL`, `SERPAPI_MAX_RETRIES`, `SERPAPI_BACKOFF_FACTOR` in `.env`.
- UI tester can be launched with `python ui_tester.py` while the FastAPI server is running.
