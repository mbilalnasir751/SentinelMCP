Here is the complete README in one block — select all and paste into your `README.md`:

```markdown
# SentinelMCP

> Local-first security and budget governance proxy for autonomous AI agents.

SentinelMCP sits between your AI agent and the LLM API. It silently scrubs secrets from outbound requests and kills runaway loops before they burn your token budget — all on localhost, zero cloud dependency.

---

## The problem it solves

AI coding agents like Claude Code and Cursor read your project files. When they hit a bug loop they will:

1. Accidentally send your `.env` secrets, AWS keys, and JWT tokens to external LLM APIs
2. Get stuck in recursive retry loops and burn hundreds of dollars in API credits in minutes

SentinelMCP intercepts both before they happen.

---

## How it works

```
[ Your AI Agent ]
       │
       ▼
[ SentinelMCP Proxy :8000 ]
   ├── Scrubber        → redacts secrets before network egress
   ├── Circuit Breaker → kills loops, returns 429
   └── Audit Log       → SQLite record of every request
       │
       ▼
[ LLM API — clean request only ]
```

---

## Features

- **Secret redaction** — catches AWS keys, JWTs, GitHub tokens, SSH private keys, Stripe keys, and high-entropy strings via Shannon entropy analysis
- **Loop detection** — SHA-256 state hashing with a configurable moving window circuit breaker
- **Audit log** — every request logged to local SQLite with WAL mode for concurrent writes
- **Live dashboard** — Rich terminal UI showing real-time requests, secrets found, and blocked status
- **Zero cloud dependency** — runs entirely on localhost, nothing leaves your machine unfiltered

---

## Quick start

**Requirements:** Python 3.12+, Poetry

```bash
git clone https://github.com/YOUR_USERNAME/sentinelmcp
cd sentinelmcp
poetry install
cp .env.example .env
poetry run uvicorn sentinelmcp.main:app --host 127.0.0.1 --port 8000
```

Point your AI agent at `http://127.0.0.1:8000` instead of the LLM API directly.

---

## Live dashboard

```bash
poetry run python -m sentinelmcp.dashboard
```

---

## Run tests

```bash
poetry run pytest tests/ -v
```

26 tests — all passing.

---

## Configuration

Edit `.env` to configure:

```env
TARGET_LLM_URL=https://api.anthropic.com
LOOP_WINDOW_SIZE=5
LOOP_THRESHOLD=3
LOG_DB_PATH=audit.db
```

| Variable | Default | Description |
|---|---|---|
| `TARGET_LLM_URL` | `https://api.anthropic.com` | Upstream LLM endpoint |
| `LOOP_WINDOW_SIZE` | `5` | Rolling window for loop detection |
| `LOOP_THRESHOLD` | `3` | Identical requests before circuit trips |
| `LOG_DB_PATH` | `audit.db` | Local SQLite audit log path |

---

## API reference

| Endpoint | Method | Description |
|---|---|---|
| `/_sentinel/health` | GET | Health check |
| `/_sentinel/logs` | GET | Last 50 audit log entries |
| `/_sentinel/reset/{session_id}` | DELETE | Reset a tripped circuit breaker |
| `/{path}` | ANY | Proxy to upstream LLM |

---

## Detected secret patterns

| Pattern | Example |
|---|---|
| AWS Access Key | `AKIA...` |
| JWT Token | `eyJ...` |
| GitHub Token | `ghp_...` |
| Stripe Secret Key | `sk_live_...` |
| SSH Private Key Header | `-----BEGIN RSA PRIVATE KEY-----` |
| Generic API Key | `api_key=...` |
| High entropy strings | Shannon entropy > 4.2 bits |

---

## Production roadmap

This is a lite portfolio version. Production hardening would include:

- PostgreSQL with connection pooling replacing SQLite
- JWT authentication and per-user audit trails
- Configurable custom secret patterns via rules engine
- Prometheus metrics endpoint
- Docker image and Kubernetes helm chart
- SOC 2 compliance audit

---

## Tech stack

| Layer | Technology |
|---|---|
| Framework | FastAPI + asyncio |
| HTTP client | httpx (async streaming) |
| Database | SQLite + WAL mode via aiosqlite |
| ORM | SQLAlchemy 2.0 async |
| Dashboard | Rich |
| Package manager | Poetry |
| Tests | pytest — 26 passing |

---

## Author

Built by Bilal Nasir — AI Engineering portfolio project, 2026.
