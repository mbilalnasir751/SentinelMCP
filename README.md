# SentinelMCP

> Local-first security and budget governance proxy for autonomous AI agents.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/Tests-26%20passing-brightgreen.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-async-009688.svg)](https://fastapi.tiangolo.com)
[![Poetry](https://img.shields.io/badge/Poetry-package%20manager-60A5FA.svg)](https://python-poetry.org)

![SentinelMCP catching a secret in real time](demo.gif)

SentinelMCP sits between your AI agent and the LLM API. It silently scrubs secrets from outbound requests and kills runaway loops before they burn your token budget — all on localhost, zero cloud dependency.

---

## Table of contents

- [The problem it solves](#the-problem-it-solves)
- [How it works](#how-it-works)
- [Features](#features)
- [Quick start](#quick-start)
- [Live dashboard](#live-dashboard)
- [Run tests](#run-tests)
- [Configuration](#configuration)
- [API reference](#api-reference)
- [Detected secret patterns](#detected-secret-patterns)
- [Troubleshooting](#troubleshooting)
- [Production roadmap](#production-roadmap)
- [Tech stack](#tech-stack)
- [Contributing](#contributing)
- [License](#license)
- [Author](#author)

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

**Requirements:** [Python 3.12+](https://www.python.org/downloads/) and [Poetry](https://python-poetry.org/docs/#installation)

```bash
git clone https://github.com/mbilalnasir751/SentinelMCP
cd SentinelMCP
poetry install
cp .env.example .env
```

> The default values in `.env.example` work out of the box for local testing.
> You do not need to edit anything before running the server.
> Only change `TARGET_LLM_URL` if you want to proxy to a different LLM endpoint.

```bash
poetry run uvicorn sentinelmcp.main:app --host 127.0.0.1 --port 8000
```

Point your AI agent at `http://127.0.0.1:8000` instead of the LLM API directly.

---

## Live dashboard

Open a second terminal and run:

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

## Troubleshooting

**Port 8000 is already in use**

Another service is occupying port 8000. Run the server on a different port:

```bash
poetry run uvicorn sentinelmcp.main:app --host 127.0.0.1 --port 8001
```

Then update your dashboard to point to the new port by editing this line in `sentinelmcp/dashboard.py`:

```python
SENTINEL_URL = "http://127.0.0.1:8001"
```

**ModuleNotFoundError: No module named sentinelmcp**

The package is not installed in your virtual environment. Run:

```bash
poetry install
```

**Dashboard shows "Waiting for SentinelMCP to start"**

The server is not running. Start it first in a separate terminal before launching the dashboard.

**requests blocked with 429 immediately**

Your circuit breaker tripped. Reset it by calling:

```bash
curl -X DELETE http://127.0.0.1:8000/_sentinel/reset/default
```

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

## Contributing

Contributions are welcome. To get started:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes and add tests
4. Ensure all tests pass: `poetry run pytest tests/ -v`
5. Submit a pull request with a clear description of what you changed and why

For bug reports and feature requests please open a GitHub issue.

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines on code style, commit messages, and the pull request process.

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

MIT means you are free to use, modify, and distribute this project for both personal and commercial purposes as long as the original license notice is included.

---

## Author

Built by Muhammad Bilal Nasir.

[![GitHub](https://img.shields.io/badge/GitHub-mbilalnasir751-181717?style=flat&logo=github)](https://github.com/mbilalnasir751)
```
