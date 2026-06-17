import httpx
import json
import os
from fastapi import Request
from fastapi.responses import StreamingResponse, JSONResponse
from .scrubber import scrub
from .circuit_breaker import get_breaker

TARGET_URL = os.getenv("TARGET_LLM_URL", "https://api.anthropic.com")

async def handle_proxy(request: Request):
    body_bytes = await request.body()

    try:
        payload = json.loads(body_bytes)
    except Exception:
        payload = {}

    session_id   = request.headers.get("x-sentinel-session", "default")
    body_str     = body_bytes.decode("utf-8", errors="replace")
    scrub_result = scrub(body_str)
    clean_body   = scrub_result.cleaned_text.encode("utf-8")

    breaker = get_breaker(session_id)
    if breaker.check(payload):
        return JSONResponse(
            status_code=429,
            content={
                "error": {
                    "type":    "circuit_breaker_tripped",
                    "message": "SentinelMCP: Recursive loop detected. Request blocked.",
                    "session": session_id,
                }
            }
        )

    forward_headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in ("host", "content-length")
    }
    forward_url = TARGET_URL + str(request.url.path)

    async def stream_response():
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                request.method,
                forward_url,
                content=clean_body,
                headers=forward_headers,
                params=dict(request.query_params),
            ) as response:
                async for chunk in response.aiter_bytes():
                    yield chunk

    return StreamingResponse(
        stream_response(),
        media_type="text/event-stream",
    )