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

import hmac
import json
import os
import time
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import APIKeyHeader
from fastapi.staticfiles import StaticFiles

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

API_KEY = os.environ.get("DASHBOARD_API_KEY", "")
BASE_DIR = Path(__file__).resolve().parent
REPOS_DIR = BASE_DIR.parent  # sibling repos are in the parent directory

# Known sibling repos to scan for evidence files
SIBLING_REPOS = [
    "aws-agent-identity-guard",
    "hf-model-provenance-scanner",
    "mcp-agent-security-gateway",
    "llm-redteam-framework",
    "model-privacy-attacks",
    "adversarial-ml-lab",
    # "PulseNet-RUL-Forecasting",  # ARCHIVED — not an active security product
    "attack-v19-core",
    "dataset-poisoning-detector",
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

# CORS restricted to localhost only
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
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
            status_code=500,
            detail="Server misconfigured: DASHBOARD_API_KEY environment variable not set.",
        )
    if not api_key or not hmac.compare_digest(api_key, API_KEY):
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")
    return api_key


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _find_evidence_files(repo_name: str) -> list[Path]:
    """Find JSON evidence files in a sibling repo."""
    repo_path = REPOS_DIR / repo_name
    if not repo_path.is_dir():
        return []

    json_files: list[Path] = []

    # Check known evidence directories
    for evidence_dir in EVIDENCE_PATHS:
        evidence_path = repo_path / evidence_dir
        if evidence_path.is_dir():
            for f in evidence_path.rglob("*.json"):
                if f.is_file() and f.stat().st_size < 10_000_000:  # 10MB limit
                    json_files.append(f)

    # Also check root-level evidence/results JSON files
    for f in repo_path.glob("*.json"):
        if f.is_file() and f.stat().st_size < 10_000_000:
            json_files.append(f)

    return json_files


def _safe_read_json(path: Path) -> dict[str, Any] | list | None:
    """Safely read and parse a JSON file. Returns None on failure."""
    try:
        text = path.read_text(encoding="utf-8")
        return json.loads(text)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return None


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
        if key in data:
            metrics[key] = data[key]

    # Check nested "metrics" or "results" keys
    for nested_key in ("metrics", "results", "summary", "stats"):
        if nested_key in data and isinstance(data[nested_key], dict):
            for key in metric_keys:
                if key in data[nested_key]:
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


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serve the main dashboard index.html."""
    index_path = BASE_DIR / "index.html"
    if index_path.is_file():
        return HTMLResponse(content=index_path.read_text(encoding="utf-8"))
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
        "repos_dir": str(REPOS_DIR),
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

        # Compute aggregate stats for this repo
        all_fp_rates = []
        all_detection_rates = []
        total_tests = 0

        for file_metrics in repo_metrics["metrics"].values():
            for key in ("fp_rate", "false_positive_rate"):
                if key in file_metrics and isinstance(file_metrics[key], (int, float)):
                    all_fp_rates.append(file_metrics[key])
            for key in ("detection_rate", "recall"):
                if key in file_metrics and isinstance(file_metrics[key], (int, float)):
                    all_detection_rates.append(file_metrics[key])
            for key in ("test_count", "total_tests"):
                if key in file_metrics and isinstance(file_metrics[key], int):
                    total_tests += file_metrics[key]

        repo_metrics["summary"] = {
            "avg_fp_rate": (
                round(sum(all_fp_rates) / len(all_fp_rates), 4)
                if all_fp_rates
                else None
            ),
            "avg_detection_rate": (
                round(sum(all_detection_rates) / len(all_detection_rates), 4)
                if all_detection_rates
                else None
            ),
            "total_tests": total_tests if total_tests > 0 else None,
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
        print("\n  WARNING: DASHBOARD_API_KEY not set. API endpoints will return 500.")
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
