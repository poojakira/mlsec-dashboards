"""
dashboard_server.py — ML Security Dashboard Hub

Safe FastAPI server that serves static dashboards and aggregates metrics
from sibling repository evidence files. No subprocess execution.

Usage:
    export DASHBOARD_API_KEY=your-secret-key
    uvicorn dashboard_server:app --port 8080

Environment Variables:
    DASHBOARD_API_KEY  — Required. API key for token-based authentication.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import math
import os
import re
import time
from collections import deque
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import APIKeyHeader
from fastapi.staticfiles import StaticFiles

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

API_KEY = os.environ.get("DASHBOARD_API_KEY", "")
# SHA-256 fingerprint of a dashboard key value that appeared in public Git history.
# Keep only the fingerprint here so the historical plaintext is not recommitted.
COMPROMISED_API_KEY_SHA256 = "6d51b0ded27991c258a110849c4f6140201ff4af1842853cf80292dda04ece26"


def _is_compromised_api_key(value: str) -> bool:
    if not value:
        return False
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return hmac.compare_digest(digest, COMPROMISED_API_KEY_SHA256)


if _is_compromised_api_key(API_KEY):
    raise RuntimeError(
        "Configured DASHBOARD_API_KEY matches a value exposed in public Git history. "
        "Generate a new key and update the deployment secret store before starting the service."
    )

ENVIRONMENT = os.environ.get("DASHBOARD_ENV", "development").strip().lower()
if ENVIRONMENT == "production" and len(API_KEY) < 32:
    raise RuntimeError("DASHBOARD_API_KEY must be at least 32 characters in production")
RATE_LIMIT_RPM = int(os.environ.get("DASHBOARD_RATE_LIMIT_RPM", "180"))
if RATE_LIMIT_RPM < 1 or RATE_LIMIT_RPM > 10000:
    raise RuntimeError("DASHBOARD_RATE_LIMIT_RPM must be between 1 and 10000")
_rate_windows: dict[str, deque[float]] = {}
MAX_RATE_IDENTITIES = 4096
MAX_EVIDENCE_BYTES = 10_000_000
MAX_EVIDENCE_FILES = 200
BASE_DIR = Path(__file__).resolve().parent
_configured_evidence_root = os.environ.get("DASHBOARD_EVIDENCE_ROOT", "").strip()
REPOS_DIR = (
    Path(_configured_evidence_root).expanduser().resolve()
    if _configured_evidence_root
    else BASE_DIR.parent
)
if ENVIRONMENT == "production" and not _configured_evidence_root:
    raise RuntimeError("DASHBOARD_EVIDENCE_ROOT is required in production")
if ENVIRONMENT == "production" and not REPOS_DIR.is_dir():
    raise RuntimeError(f"DASHBOARD_EVIDENCE_ROOT does not exist: {REPOS_DIR}")

# Known sibling repos to scan for evidence files
_DEFAULT_REPOSITORIES = [
    "aws-agent-identity-guard",
    "hf-model-provenance-scanner",
    "mcp-agent-security-gateway",
    "llm-redteam-framework",
    "model-privacy-attacks",
    "adversarial-ml-lab",
    "attack-v19-core",
    "dataset-poisoning-detector",
]
_configured_repositories = os.environ.get("DASHBOARD_REPOSITORIES", "")
SIBLING_REPOS = (
    [item.strip() for item in _configured_repositories.split(",") if item.strip()]
    if _configured_repositories
    else _DEFAULT_REPOSITORIES
)
_REPO_NAME = re.compile(r"^[A-Za-z0-9_.-]{1,100}$")
if any(name in {".", ".."} or not _REPO_NAME.fullmatch(name) for name in SIBLING_REPOS):
    raise RuntimeError("DASHBOARD_REPOSITORIES contains an invalid repository name")

_configured_origins = [
    item.strip()
    for item in os.environ.get("DASHBOARD_ALLOWED_ORIGINS", "").split(",")
    if item.strip()
]
for origin in _configured_origins:
    if origin == "*" or not re.fullmatch(r"https?://[^/]+(?::\d+)?", origin):
        raise RuntimeError(
            "DASHBOARD_ALLOWED_ORIGINS must contain explicit http(s) origins without paths"
        )

if _configured_origins:
    ALLOWED_ORIGINS = _configured_origins
elif ENVIRONMENT == "production":
    # No CORS headers means browser access remains same-origin only.
    ALLOWED_ORIGINS = []
else:
    ALLOWED_ORIGINS = [
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

# Common evidence file paths to search within each repo
EVIDENCE_PATHS = [
    "evidence",
    "results",
    "metrics",
    "reports",
    "output",
]

app = FastAPI(
    title="ML Security Dashboard Hub",
    version="3.0.0",
    description="Unified dashboard for ML security portfolio tool metrics.",
)


def _consume_rate_limit(identity: str) -> bool:
    now = time.monotonic()
    cutoff = now - 60.0
    # Drop inactive identities and fail closed if the bounded table is full.
    for key in list(_rate_windows):
        if not _rate_windows[key] or _rate_windows[key][-1] <= cutoff:
            del _rate_windows[key]
    if identity not in _rate_windows and len(_rate_windows) >= MAX_RATE_IDENTITIES:
        return False
    bucket = _rate_windows.setdefault(identity, deque())
    while bucket and bucket[0] <= cutoff:
        bucket.popleft()
    if len(bucket) >= RATE_LIMIT_RPM:
        return False
    bucket.append(now)
    return True


@app.middleware("http")
async def _security_boundary(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        peer = request.client.host if request.client else "unknown"
        # Unauthenticated callers must not bypass the budget by rotating keys.
        if not _consume_rate_limit(peer):
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={"Retry-After": "60"},
            )
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    return response


# Same-origin by default in production. Operators may explicitly allow
# owned browser origins with DASHBOARD_ALLOWED_ORIGINS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET"],
    allow_headers=["Authorization", "X-API-Key"],
)

# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str | None = Depends(api_key_header)) -> str:
    """Validate API key from X-API-Key header."""
    if not API_KEY:
        raise HTTPException(
            status_code=503, detail="Dashboard authentication unavailable"
        )
    if not api_key or not hmac.compare_digest(
        api_key.encode("utf-8"), API_KEY.encode("utf-8")
    ):
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")
    return api_key


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _find_evidence_files(repo_name: str) -> list[Path]:
    """Find JSON evidence files in a sibling repo."""
    if repo_name in {".", ".."} or not _REPO_NAME.fullmatch(repo_name):
        return []
    if (REPOS_DIR / repo_name).is_symlink():
        return []
    repo_path = (REPOS_DIR / repo_name).resolve()
    try:
        repo_path.relative_to(REPOS_DIR)
    except ValueError:
        return []
    if not repo_path.is_dir():
        return []

    json_files: list[Path] = []
    for evidence_dir in EVIDENCE_PATHS:
        evidence_path = repo_path / evidence_dir
        if evidence_path.is_symlink() or not evidence_path.is_dir():
            continue
        # os.walk does not follow directory symlinks. Limit files returned.
        for directory, dirs, files in os.walk(evidence_path, followlinks=False):
            dirs[:] = [
                name for name in dirs if not (Path(directory) / name).is_symlink()
            ]
            for name in files:
                f = Path(directory) / name
                if f.suffix == ".json" and _allowed_evidence_file(f):
                    json_files.append(f)
                    if len(json_files) >= MAX_EVIDENCE_FILES:
                        return json_files
    for f in repo_path.glob("*.json"):
        if _allowed_evidence_file(f):
            json_files.append(f)
            if len(json_files) >= MAX_EVIDENCE_FILES:
                break
    return json_files


def _allowed_evidence_file(path: Path) -> bool:
    try:
        path.resolve().relative_to(REPOS_DIR.resolve())
        return (
            not path.is_symlink()
            and path.is_file()
            and path.stat().st_size < MAX_EVIDENCE_BYTES
        )
    except (ValueError, OSError, RuntimeError):
        return False


def _safe_read_json(path: Path) -> dict[str, Any] | list | None:
    """Read only contained evidence, with an enforced read-time byte limit."""
    if not _allowed_evidence_file(path):
        return None
    try:
        with path.open("rb") as stream:
            content = stream.read(MAX_EVIDENCE_BYTES)
        if len(content) >= MAX_EVIDENCE_BYTES:
            return None
        return json.loads(content.decode("utf-8"))
    except (
        json.JSONDecodeError,
        OSError,
        UnicodeDecodeError,
        RecursionError,
        ValueError,
    ):
        return None


def _is_metric(value: Any) -> bool:
    return type(value) is int or (type(value) is float and math.isfinite(value))


def _extract_metrics(data: Any) -> dict[str, Any]:
    """Extract known metric fields from evidence data."""
    metrics: dict[str, Any] = {}

    if not isinstance(data, dict):
        return metrics

    # Common metric keys we look for
    metric_keys = [
        "fp_rate",
        "false_positive_rate",
        "detection_rate",
        "recall",
        "precision",
        "f1",
        "f1_score",
        "auc",
        "auc_roc",
        "accuracy",
        "test_count",
        "tests_passed",
        "tests_failed",
        "total_tests",
        "rules_count",
        "findings_count",
        "model_count",
        "scan_count",
    ]

    for key in metric_keys:
        if key in data and _is_metric(data[key]):
            metrics[key] = data[key]

    # Check nested "metrics" or "results" keys
    for nested_key in ("metrics", "results", "summary", "stats"):
        if nested_key in data and isinstance(data[nested_key], dict):
            for key in metric_keys:
                if key in data[nested_key] and _is_metric(data[nested_key][key]):
                    metrics[key] = data[nested_key][key]

    return metrics


# ---------------------------------------------------------------------------
# GET /health  — unauthenticated health check
# ---------------------------------------------------------------------------


@app.get("/health")
async def health():
    """Basic health check (no auth required)."""
    return {"status": "ok", "service": "mlsec-dashboard-hub", "version": "3.0.0"}


# ---------------------------------------------------------------------------
# GET /  — serve main dashboard
# ---------------------------------------------------------------------------


@app.get("/ready")
async def ready():
    """Readiness requires configured authentication and a readable evidence root."""
    if not API_KEY:
        raise HTTPException(
            status_code=503, detail="DASHBOARD_API_KEY is not configured"
        )
    if not REPOS_DIR.is_dir():
        raise HTTPException(status_code=503, detail="evidence root is unavailable")
    return {"status": "ready", "repositories_configured": len(SIBLING_REPOS)}


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serve the main dashboard index.html.

    Reads are guarded: a missing, unreadable, or non-UTF-8 index.html returns a
    clean fallback page rather than surfacing an unhandled 500 with a traceback.
    """
    index_path = BASE_DIR / "index.html"
    if index_path.is_file():
        try:
            return HTMLResponse(content=index_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            return HTMLResponse(
                content=(
                    "<h1>ML Security Dashboard Hub</h1>"
                    "<p>index.html could not be read.</p>"
                ),
                status_code=500,
            )
    return HTMLResponse(
        content="<h1>ML Security Dashboard Hub</h1><p>No index.html found.</p>"
    )


# ---------------------------------------------------------------------------
# GET /api/status  — repo evidence status (authenticated)
# ---------------------------------------------------------------------------


@app.get("/api/status")
async def api_status(_: str = Depends(verify_api_key)):
    """
    Check which sibling repos exist locally and have evidence files.
    Returns availability status for each known repo.
    """
    status: dict[str, Any] = {}

    for repo_name in SIBLING_REPOS:
        repo_path = REPOS_DIR / repo_name
        repo_exists = repo_path.is_dir()
        evidence_files = _find_evidence_files(repo_name) if repo_exists else []

        status[repo_name] = {
            "exists": repo_exists,
            "evidence_file_count": len(evidence_files),
            "evidence_files": [
                str(f.relative_to(REPOS_DIR)) for f in evidence_files[:20]
            ],
        }

    return {
        "repos": status,
        "ts": time.time(),
    }


# ---------------------------------------------------------------------------
# GET /api/metrics  — aggregated metrics (authenticated)
# ---------------------------------------------------------------------------


@app.get("/api/metrics")
async def api_metrics(_: str = Depends(verify_api_key)):
    """
    Aggregate test counts, FP rates, detection rates from evidence JSON files
    across all sibling repos.
    """
    aggregated: dict[str, Any] = {}

    for repo_name in SIBLING_REPOS:
        evidence_files = _find_evidence_files(repo_name)
        if not evidence_files:
            continue

        repo_metrics: dict[str, Any] = {
            "files_scanned": len(evidence_files),
            "metrics": {},
        }

        for evidence_file in evidence_files:
            data = _safe_read_json(evidence_file)
            if data is None:
                continue

            extracted = _extract_metrics(data)
            if extracted:
                file_key = evidence_file.stem
                repo_metrics["metrics"][file_key] = extracted

        # Evidence files can describe different datasets, attack populations,
        # seeds, and measurement methods. Do not average unrelated precision,
        # recall, false-positive, or detection rates across files. Preserve each
        # artifact's own metrics and summarize only document counts.
        repo_metrics["summary"] = {
            "evidence_documents_with_metrics": len(repo_metrics["metrics"]),
            "aggregation_policy": "no_cross_benchmark_metric_averaging",
        }

        aggregated[repo_name] = repo_metrics

    return {
        "repos": aggregated,
        "total_repos_with_evidence": len(aggregated),
        "ts": time.time(),
    }


# ---------------------------------------------------------------------------
# Static file serving for project dashboards
# ---------------------------------------------------------------------------

# Mount static dashboard subdirectories
_dashboard_dirs = [
    "aws-agent-identity-guard",
    "hf-model-provenance-scanner",
    "mcp-agent-security-gateway",
    "llm-redteam-framework",
    "model-privacy-attacks",
    "adversarial-ml-lab",
    # "PulseNet-RUL-Forecasting",  # ARCHIVED — not an active security product
    "attack-v19-core",
    "dataset-poisoning-detector",
    "ml-security-command-center",
    "mlsec-benchmark-suite",
    "unified-ml-security-platform",
    "shared",
]

for _dir_name in _dashboard_dirs:
    _dir_path = BASE_DIR / _dir_name
    if _dir_path.is_dir():
        app.mount(
            f"/{_dir_name}",
            StaticFiles(directory=str(_dir_path), html=True),
            name=_dir_name,
        )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    if not API_KEY:
        print("\n  WARNING: DASHBOARD_API_KEY not set. API endpoints will return 503.")
        print("  Set it:  export DASHBOARD_API_KEY=your-secret-key\n")

    print("\n  ML Security Dashboard Hub -> http://localhost:8080")
    print("  Serving static dashboards + metrics API\n")
    uvicorn.run(
        "dashboard_server:app",
        host="127.0.0.1",
        port=8080,
        reload=False,
        log_level="info",
    )
