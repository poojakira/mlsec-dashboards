from __future__ import annotations

import json
import re
from pathlib import Path

REGISTRY = Path("validation/source_snapshots.json")
SHA40 = re.compile(r"^[0-9a-f]{40}$")


def test_source_snapshots_are_revision_bound() -> None:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "dashboard-source-snapshots-v1"
    sources = payload["sources"]
    assert sources
    for source in sources.values():
        assert source["repository"].startswith("poojakira/")
        assert SHA40.fullmatch(source["revision"])
        assert source["path"]
        assert "/main/" not in (
            f"https://raw.githubusercontent.com/{source['repository']}/"
            f"{source['revision']}/{source['path']}"
        )


def test_snapshot_registry_states_non_freshness_boundary() -> None:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    boundary = payload["claim_boundary"].lower()
    assert "static dashboard" in boundary
    assert "latest" in boundary
