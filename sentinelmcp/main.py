from fastapi import FastAPI, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from .database import init_db, get_db, AuditLog
from .proxy import handle_proxy
from .scrubber import scrub
import datetime

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title="SentinelMCP",
    description="Local-first security and budget governance proxy for AI agents",
    version="0.1.0",
    lifespan=lifespan,
)

# ── Internal sentinel routes (defined first so they are never caught by the proxy) ──

@app.get("/_sentinel/health")
async def health():
    return {"status": "ok", "service": "SentinelMCP"}

@app.get("/_sentinel/logs")
async def get_logs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(50)
    )
    logs = result.scalars().all()
    return [
        {
            "id":            log.id,
            "timestamp":     str(log.timestamp),
            "endpoint":      log.endpoint,
            "secrets_found": log.secrets_found,
            "blocked":       log.blocked,
        }
        for log in logs
    ]

@app.delete("/_sentinel/reset/{session_id}")
async def reset_session(session_id: str):
    from .circuit_breaker import reset_breaker
    reset_breaker(session_id)
    return {"status": "reset", "session": session_id}

# ── Catch-all proxy route (must be last) ──

@app.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)
async def proxy_all(
    request: Request,
    path:    str,
    db:      AsyncSession = Depends(get_db)
):
    body_bytes   = await request.body()
    body_str     = body_bytes.decode("utf-8", errors="replace")
    scrub_result = scrub(body_str)

    # Log every proxied request to the audit database
    entry = AuditLog(
        timestamp     = datetime.datetime.utcnow(),
        endpoint      = f"/{path}",
        secrets_found = scrub_result.secrets_found,
        blocked       = "false",
        body_preview  = body_str[:200],
    )
    db.add(entry)
    await db.commit()

    return await handle_proxy(request)