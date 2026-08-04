"""
dashboard_server.py — Local backend proxy for mlsec-dashboards

Bridges the browser dashboards to the real CLI tools via SSE streams.

Usage:
    pip install fastapi uvicorn httpx
    python dashboard_server.py

Serves on http://localhost:9001
Dashboards connect to this server for live data.
"""

from __future__ import annotations

import asyncio
import json
import re
import shlex
import subprocess
import sys
import time
from typing import AsyncIterator

import httpx
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

MCP_BASE = "http://localhost:8080"   # mcp-gateway server
PROXY_PORT = 9001                    # this server
POLL_INTERVAL = 2.0                  # seconds between MCP metric polls

app = FastAPI(title="mlsec-dashboard-server", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sse(event: str, data: dict | str | list) -> str:
    """Format a Server-Sent Events frame."""
    payload = data if isinstance(data, str) else json.dumps(data)
    return f"event: {event}\ndata: {payload}\n\n"


def sse_error(msg: str) -> str:
    return sse("error", {"error": msg})


def parse_prometheus(text: str) -> dict:
    """Parse Prometheus text exposition into a flat dict."""
    result: dict = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # label-less: metric_name value
        m = re.match(r'^([a-zA-Z_:][a-zA-Z0-9_:]*)\s+([\d.+\-eEinf]+)$', line)
        if m:
            result[m.group(1)] = float(m.group(2)) if "." in m.group(2) else int(float(m.group(2)))
            continue
        # with labels: metric_name{k="v",...} value
        m = re.match(r'^([a-zA-Z_:][a-zA-Z0-9_:]*)\{([^}]+)\}\s+([\d.+\-eEinf]+)$', line)
        if m:
            key = f'{m.group(1)}{{{m.group(2)}}}'
            try:
                result[key] = float(m.group(3)) if "." in m.group(3) else int(float(m.group(3)))
            except ValueError:
                pass
    return result


# ---------------------------------------------------------------------------
# GET /health  — proxy health
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok", "proxy": "dashboard_server", "version": "2.0.0"}


# ---------------------------------------------------------------------------
# SSE /sse/mcp  — live MCP gateway metrics + health
# ---------------------------------------------------------------------------

@app.get("/sse/mcp")
async def sse_mcp():
    """Stream MCP gateway metrics every POLL_INTERVAL seconds."""

    async def generate() -> AsyncIterator[str]:
        yield sse("connected", {"proxy": "dashboard_server", "mcp_base": MCP_BASE})
        async with httpx.AsyncClient(timeout=3.0) as client:
            while True:
                ts = time.time()
                try:
                    h_resp = await client.get(f"{MCP_BASE}/v1/health")
                    m_resp = await client.get(f"{MCP_BASE}/v1/metrics")

                    health_data = h_resp.json() if h_resp.status_code == 200 else {}
                    metrics_raw = m_resp.text if m_resp.status_code == 200 else ""
                    metrics = parse_prometheus(metrics_raw)

                    # extract p99 latency from histogram
                    p99 = _p99_from_prometheus(metrics_raw)

                    payload = {
                        "ts": ts,
                        "connected": True,
                        "health": health_data,
                        "metrics": metrics,
                        "p99_ms": round(p99 * 1000, 2) if p99 is not None else None,
                        "request_total": metrics.get("mcp_request_total", 0),
                        "error_total": metrics.get("mcp_error_total", 0),
                        "active_requests": metrics.get("mcp_active_requests", 0),
                        "circuit_inspect_call": _circuit_label(metrics, "inspect_call"),
                        "circuit_inspect_output": _circuit_label(metrics, "inspect_output"),
                    }
                    yield sse("metrics", payload)

                except httpx.ConnectError:
                    yield sse("disconnected", {
                        "ts": ts,
                        "connected": False,
                        "message": f"MCP gateway not reachable at {MCP_BASE}. "
                                   "Run: pip install -e \".[server]\" && mcp-gateway"
                    })
                except Exception as exc:
                    yield sse("error", {"ts": ts, "error": str(exc)})

                await asyncio.sleep(POLL_INTERVAL)

    return StreamingResponse(generate(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


def _p99_from_prometheus(text: str) -> float | None:
    """Extract approximate p99 from histogram buckets."""
    buckets: list[tuple[float, int]] = []
    total_count = 0
    for line in text.splitlines():
        m = re.match(r'mcp_request_duration_seconds_bucket\{le="([^"]+)"\}\s+(\d+)', line)
        if m:
            le = float("inf") if m.group(1) == "+Inf" else float(m.group(1))
            buckets.append((le, int(m.group(2))))
        m2 = re.match(r'^mcp_request_duration_seconds_count\s+(\d+)$', line)
        if m2:
            total_count = int(m2.group(1))
    if not buckets or total_count == 0:
        return None
    target = total_count * 0.99
    for le, count in buckets:
        if count >= target:
            return le
    return None


def _circuit_label(metrics: dict, name: str) -> str:
    key = f'mcp_circuit_breaker_state{{layer="{name}"}}'
    val = metrics.get(key, 0)
    return {0: "closed", 1: "open", 2: "half_open"}.get(int(val), "unknown")


# ---------------------------------------------------------------------------
# POST /api/mcp/inspect  — forward a tool call to the live MCP gateway
# ---------------------------------------------------------------------------

@app.post("/api/mcp/inspect")
async def mcp_inspect(payload: dict):
    """Forward a tool call to POST /v1/inspect_call on the MCP gateway."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.post(f"{MCP_BASE}/v1/inspect_call", json=payload)
            return resp.json()
        except httpx.ConnectError:
            return {"error": f"MCP gateway not reachable at {MCP_BASE}", "connected": False}


# ---------------------------------------------------------------------------
# SSE /sse/hf-scan  — stream hf-scanner results
# ---------------------------------------------------------------------------

@app.get("/sse/hf-scan")
async def sse_hf_scan(
    model_id: str = Query(..., description="HuggingFace model ID, e.g. bert-base-uncased"),
    token: str = Query("", description="HF API token (optional)"),
):
    """
    Run hf-scanner against a real model ID and stream results as SSE.
    Requires: pip install hf-scanner  (or pip install hf-model-provenance-scanner)
    """

    async def generate() -> AsyncIterator[str]:
        yield sse("started", {"model_id": model_id, "ts": time.time()})

        cmd = ["hf-scanner", model_id, "--format", "json", "--verbose"]
        if token:
            cmd += ["--token", token]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError:
            yield sse_error(
                "hf-scanner not found. Install: pip install hf-model-provenance-scanner"
            )
            return

        # Stream stderr lines as progress events
        assert proc.stderr is not None
        assert proc.stdout is not None

        async def stream_stderr():
            async for line in proc.stderr:
                text = line.decode("utf-8", errors="replace").rstrip()
                if text:
                    yield sse("progress", {"line": text})

        stderr_lines = []
        async for frame in stream_stderr():
            yield frame

        stdout, _ = await proc.communicate()
        rc = proc.returncode

        if rc != 0:
            yield sse_error(f"hf-scanner exited with code {rc}")
            return

        try:
            result = json.loads(stdout.decode("utf-8"))
            yield sse("result", result)
            yield sse("done", {"model_id": model_id, "ts": time.time()})
        except json.JSONDecodeError as exc:
            yield sse_error(f"Could not parse hf-scanner output: {exc}")

    return StreamingResponse(generate(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ---------------------------------------------------------------------------
# SSE /sse/llm-eval  — stream redteam-eval
# ---------------------------------------------------------------------------

@app.get("/sse/llm-eval")
async def sse_llm_eval(
    split_mode: str = Query("grouped", description="grouped or random"),
    seed: int = Query(42),
):
    """
    Run redteam-eval and stream stdout as SSE.
    Requires: pip install llm-redteam-framework
    """

    async def generate() -> AsyncIterator[str]:
        yield sse("started", {"split_mode": split_mode, "seed": seed, "ts": time.time()})

        cmd = [
            sys.executable, "-m", "redteam.eval.harness",
            "--split-mode", split_mode,
            "--seed", str(seed),
            "--output", "-",   # stdout
        ]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError:
            # Try the entry-point script instead
            try:
                proc = await asyncio.create_subprocess_exec(
                    "redteam-eval",
                    "--split-mode", split_mode,
                    "--seed", str(seed),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
            except FileNotFoundError:
                yield sse_error(
                    "redteam-eval not found. Install: pip install llm-redteam-framework"
                )
                return

        assert proc.stderr is not None
        assert proc.stdout is not None

        # Stream stderr progress
        async for line in proc.stderr:
            text = line.decode("utf-8", errors="replace").rstrip()
            if text:
                yield sse("progress", {"line": text})

        stdout, _ = await proc.communicate()
        rc = proc.returncode

        if rc != 0:
            yield sse_error(f"redteam-eval exited with code {rc}")
            return

        raw = stdout.decode("utf-8").strip()
        # Try JSON parse first
        try:
            result = json.loads(raw)
            yield sse("result", result)
        except json.JSONDecodeError:
            # Fall back: emit raw lines
            for line in raw.splitlines():
                yield sse("progress", {"line": line})
            yield sse("result", {"raw": raw})

        yield sse("done", {"ts": time.time()})

    return StreamingResponse(generate(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ---------------------------------------------------------------------------
# SSE /sse/adv-eval  — stream adversarial ML lab eval
# ---------------------------------------------------------------------------

@app.get("/sse/adv-eval")
async def sse_adv_eval(attack: str = Query("pgd", description="fgsm, pgd, or cw")):
    """Run adversarial-ml-lab eval script and stream results."""

    async def generate() -> AsyncIterator[str]:
        yield sse("started", {"attack": attack, "ts": time.time()})
        cmd = [sys.executable, "-m", "adv_lab.eval", "--attack", attack, "--json"]
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError:
            yield sse_error("adversarial-ml-lab not installed. pip install adversarial-ml-lab")
            return

        assert proc.stderr is not None
        assert proc.stdout is not None

        async for line in proc.stderr:
            text = line.decode("utf-8", errors="replace").rstrip()
            if text:
                yield sse("progress", {"line": text})

        stdout, _ = await proc.communicate()
        if proc.returncode != 0:
            yield sse_error(f"adv eval exited {proc.returncode}")
            return
        try:
            yield sse("result", json.loads(stdout))
        except json.JSONDecodeError:
            yield sse("result", {"raw": stdout.decode()})
        yield sse("done", {"ts": time.time()})

    return StreamingResponse(generate(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ---------------------------------------------------------------------------
# SSE /sse/poison-eval  — dataset poisoning detector
# ---------------------------------------------------------------------------

@app.get("/sse/poison-eval")
async def sse_poison_eval(method: str = Query("spectral", description="spectral or influence")):
    """Run dataset-poisoning-detector and stream results."""

    async def generate() -> AsyncIterator[str]:
        yield sse("started", {"method": method, "ts": time.time()})
        cmd = [sys.executable, "-m", "poisoning.eval", "--method", method, "--json"]
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError:
            yield sse_error("dataset-poisoning-detector not installed. pip install dataset-poisoning-detector")
            return

        assert proc.stderr is not None
        assert proc.stdout is not None

        async for line in proc.stderr:
            text = line.decode("utf-8", errors="replace").rstrip()
            if text:
                yield sse("progress", {"line": text})

        stdout, _ = await proc.communicate()
        if proc.returncode != 0:
            yield sse_error(f"poison eval exited {proc.returncode}")
            return
        try:
            yield sse("result", json.loads(stdout))
        except json.JSONDecodeError:
            yield sse("result", {"raw": stdout.decode()})
        yield sse("done", {"ts": time.time()})

    return StreamingResponse(generate(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ---------------------------------------------------------------------------
# GET /api/status  — which tools are installed and reachable
# ---------------------------------------------------------------------------

@app.get("/api/status")
async def api_status():
    """Check which tools are installed and whether MCP is reachable."""
    import shutil

    tools = {
        "hf-scanner":    shutil.which("hf-scanner") is not None,
        "redteam-eval":  shutil.which("redteam-eval") is not None,
        "mcp-gateway":   shutil.which("mcp-gateway") is not None,
    }

    # Check MCP reachability
    mcp_up = False
    try:
        async with httpx.AsyncClient(timeout=1.5) as client:
            r = await client.get(f"{MCP_BASE}/v1/health")
            mcp_up = r.status_code == 200
    except Exception:
        pass

    return {
        "proxy": "ok",
        "tools": tools,
        "mcp_reachable": mcp_up,
        "mcp_base": MCP_BASE,
        "ts": time.time(),
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    print(f"\n  mlsec dashboard server → http://localhost:{PROXY_PORT}")
    print(f"  Polling MCP gateway at  → {MCP_BASE}\n")
    uvicorn.run("dashboard_server:app", host="127.0.0.1", port=PROXY_PORT,
                reload=False, log_level="info")
