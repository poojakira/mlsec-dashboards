"""Check static dashboard headline metrics against immutable source snapshots."""

from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

USER_AGENT = "mlsec-dashboard-source-snapshot/1.0"
DASHBOARD = Path("index.html")
SOURCE_REGISTRY = Path("validation/source_snapshots.json")
_SHA40 = re.compile(r"^[0-9a-f]{40}$")

CHECKS = [
    {
        "name": "attack-v19 tests",
        "source_key": "attack_v19",
        "source_regex": r"Tests passed\s*\|\s*\*\*(\d+)\*\*",
        "dashboard_template": "{value} passing tests",
    },
    {
        "name": "HF scanner tests",
        "source_key": "hf_scanner",
        "source_regex": r"Tests passed\s*\|\s*\*\*(\d+)\*\*",
        "dashboard_template": 'data-target="{value}"',
    },
    {
        "name": "HF scanner coverage",
        "source_key": "hf_scanner",
        "source_regex": r"Statement coverage\s*\|\s*\*\*([0-9.]+)%",
        "dashboard_template": 'data-target="{value}" data-suffix="%"',
    },
    {
        "name": "LLM grouped F1",
        "source_key": "llm_redteam",
        "source_regex": r"Grouped-split F1 \(in-distribution\)\s*\|\s*([0-9.]+)",
        "dashboard_template": "{value}",
    },
    {
        "name": "LLM OOD F1",
        "source_key": "llm_redteam",
        "source_regex": r"Novel-phrasing OOD F1\s*\|\s*([0-9.]+)",
        "dashboard_template": "{value}",
    },
]


def load_sources() -> dict[str, dict[str, str]]:
    payload = json.loads(SOURCE_REGISTRY.read_text(encoding="utf-8"))
    sources = payload.get("sources")
    if not isinstance(sources, dict) or not sources:
        raise ValueError("source snapshot registry must contain a non-empty sources object")
    for key, source in sources.items():
        if not isinstance(source, dict):
            raise ValueError(f"{key}: source entry must be an object")
        repository = source.get("repository", "")
        revision = source.get("revision", "")
        path = source.get("path", "")
        if not repository.startswith("poojakira/"):
            raise ValueError(f"{key}: unsupported source repository")
        if not _SHA40.fullmatch(revision):
            raise ValueError(f"{key}: revision must be an immutable 40-char SHA")
        if not path or path.startswith("/") or ".." in Path(path).parts:
            raise ValueError(f"{key}: unsafe source path")
    return sources


def source_url(source: dict[str, str]) -> str:
    return (
        "https://raw.githubusercontent.com/"
        f"{source['repository']}/{source['revision']}/{source['path']}"
    )


def fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:  # nosec B310
        return response.read(2_000_000).decode("utf-8")


def main() -> int:
    dashboard = DASHBOARD.read_text(encoding="utf-8")
    sources = load_sources()
    results = []
    failures = []
    cache: dict[str, str] = {}

    for check in CHECKS:
        source = sources[check["source_key"]]
        url = source_url(source)
        text = cache.setdefault(url, fetch_text(url))
        match = re.search(check["source_regex"], text)
        if not match:
            failures.append(f"{check['name']}: source metric not found")
            continue
        value = match.group(1)
        expected = check["dashboard_template"].format(value=value)
        present = expected in dashboard
        results.append(
            {
                "name": check["name"],
                "source_repository": source["repository"],
                "source_revision": source["revision"],
                "source_path": source["path"],
                "source_value": value,
                "dashboard_marker": expected,
                "fresh": present,
            }
        )
        if not present:
            failures.append(f"{check['name']}: dashboard does not contain {expected!r}")

    report = {
        "classification": "revision-bound-source-evidence-snapshot-check",
        "results": results,
        "passed": not failures,
        "failures": failures,
        "claim_boundary": (
            "Checks static dashboard values against exact source revisions; "
            "it does not reproduce source benchmarks or prove the pinned revisions are latest."
        ),
    }
    Path("validation").mkdir(exist_ok=True)
    Path("validation/source-freshness.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
