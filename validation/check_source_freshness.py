"""Check that dashboard headline metrics still match source-repository evidence."""

from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

USER_AGENT = "mlsec-dashboard-freshness/1.0"
DASHBOARD = Path("index.html")

CHECKS = [
    {
        "name": "attack-v19 tests",
        "url": "https://raw.githubusercontent.com/poojakira/attack-v19-core/main/poster/03_verified_metrics.md",
        "source_regex": r"Tests passed\s*\|\s*\*\*(\d+)\*\*",
        "dashboard_template": "{value} passing tests",
    },
    {
        "name": "HF scanner tests",
        "url": "https://raw.githubusercontent.com/poojakira/hf-model-provenance-scanner/main/poster/03_verified_metrics.md",
        "source_regex": r"Tests passed\s*\|\s*\*\*(\d+)\*\*",
        "dashboard_template": 'data-target="{value}"',
    },
    {
        "name": "HF scanner coverage",
        "url": "https://raw.githubusercontent.com/poojakira/hf-model-provenance-scanner/main/poster/03_verified_metrics.md",
        "source_regex": r"Statement coverage\s*\|\s*\*\*([0-9.]+)%",
        "dashboard_template": 'data-target="{value}" data-suffix="%"',
    },
    {
        "name": "LLM grouped F1",
        "url": "https://raw.githubusercontent.com/poojakira/llm-redteam-framework/main/README.md",
        "source_regex": r"Grouped-split F1 \(in-distribution\)\s*\|\s*([0-9.]+)",
        "dashboard_template": "{value}",
    },
    {
        "name": "LLM OOD F1",
        "url": "https://raw.githubusercontent.com/poojakira/llm-redteam-framework/main/README.md",
        "source_regex": r"Novel-phrasing OOD F1\s*\|\s*([0-9.]+)",
        "dashboard_template": "{value}",
    },
]


def fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:  # nosec B310
        return response.read(2_000_000).decode("utf-8")


def main() -> int:
    dashboard = DASHBOARD.read_text(encoding="utf-8")
    results = []
    failures = []
    cache: dict[str, str] = {}

    for check in CHECKS:
        source = cache.setdefault(check["url"], fetch_text(check["url"]))
        match = re.search(check["source_regex"], source)
        if not match:
            failures.append(f"{check['name']}: source metric not found")
            continue
        value = match.group(1)
        expected = check["dashboard_template"].format(value=value)
        present = expected in dashboard
        results.append(
            {
                "name": check["name"],
                "source": check["url"],
                "source_value": value,
                "dashboard_marker": expected,
                "fresh": present,
            }
        )
        if not present:
            failures.append(f"{check['name']}: dashboard does not contain {expected!r}")

    report = {
        "classification": "source-evidence-freshness-check",
        "results": results,
        "passed": not failures,
        "failures": failures,
        "claim_boundary": "Checks traceability/freshness only; it does not reproduce source benchmarks.",
    }
    Path("validation").mkdir(exist_ok=True)
    Path("validation/source-freshness.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
