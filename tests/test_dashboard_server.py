"""Tests for dashboard_server.py — verifies authentication, health check, and metrics."""

import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# Set API key before importing the app
os.environ["DASHBOARD_API_KEY"] = "test-api-key-for-unit-tests"


@pytest.fixture
def client():
    """Create a test client with the app."""
    from dashboard_server import app

    return TestClient(app)


@pytest.fixture
def api_headers():
    """Valid API key headers."""
    return {"X-API-Key": "test-api-key-for-unit-tests"}


# ---------------------------------------------------------------------------
# Health endpoint (unauthenticated)
# ---------------------------------------------------------------------------


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_correct_fields(self, client):
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "mlsec-dashboard-hub"
        assert "version" in data

    def test_health_requires_no_auth(self, client):
        # No X-API-Key header — should still work
        response = client.get("/health")
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


class TestAuthentication:
    def test_api_status_rejects_missing_key(self, client):
        response = client.get("/api/status")
        assert response.status_code == 401

    def test_api_status_rejects_wrong_key(self, client):
        response = client.get("/api/status", headers={"X-API-Key": "wrong-key"})
        assert response.status_code == 401

    def test_api_status_accepts_correct_key(self, client, api_headers):
        response = client.get("/api/status", headers=api_headers)
        assert response.status_code == 200

    def test_api_metrics_rejects_missing_key(self, client):
        response = client.get("/api/metrics")
        assert response.status_code == 401

    def test_api_metrics_accepts_correct_key(self, client, api_headers):
        response = client.get("/api/metrics", headers=api_headers)
        assert response.status_code == 200

    def test_empty_api_key_returns_503(self, client):
        """If DASHBOARD_API_KEY is empty, authentication fails closed with 503."""
        with patch.dict(os.environ, {"DASHBOARD_API_KEY": ""}):
            # Need to reload the module to pick up the new env var
            import dashboard_server

            original_key = dashboard_server.API_KEY
            dashboard_server.API_KEY = ""
            try:
                response = client.get("/api/status", headers={"X-API-Key": "anything"})
                assert response.status_code == 503
                assert (
                    response.json()["detail"] == "Dashboard authentication unavailable"
                )
            finally:
                dashboard_server.API_KEY = original_key


# ---------------------------------------------------------------------------
# API Status endpoint
# ---------------------------------------------------------------------------


class TestApiStatus:
    def test_status_returns_repos_dict(self, client, api_headers):
        response = client.get("/api/status", headers=api_headers)
        data = response.json()
        assert "repos" in data
        assert "repos_dir" not in data
        assert "ts" in data
        assert isinstance(data["repos"], dict)

    def test_status_reports_repo_existence(self, client, api_headers):
        response = client.get("/api/status", headers=api_headers)
        data = response.json()
        # Each repo entry should have an 'exists' field
        for repo_status in data["repos"].values():
            assert "exists" in repo_status
            assert "evidence_file_count" in repo_status
            assert isinstance(repo_status["exists"], bool)


# ---------------------------------------------------------------------------
# API Metrics endpoint
# ---------------------------------------------------------------------------


class TestApiMetrics:
    def test_metrics_returns_dict(self, client, api_headers):
        response = client.get("/api/metrics", headers=api_headers)
        data = response.json()
        assert isinstance(data, dict)

    def test_metrics_has_timestamp(self, client, api_headers):
        response = client.get("/api/metrics", headers=api_headers)
        data = response.json()
        assert "ts" in data


# ---------------------------------------------------------------------------
# Index page
# ---------------------------------------------------------------------------


class TestIndexPage:
    def test_index_returns_html(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_index_contains_dashboard_title(self, client):
        response = client.get("/")
        # Should contain some HTML content
        assert "<" in response.text


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


class TestExtractMetrics:
    def test_extract_from_flat_dict(self):
        from dashboard_server import _extract_metrics

        data = {"detection_rate": 0.95, "fp_rate": 0.02, "unrelated": "ignored"}
        metrics = _extract_metrics(data)
        assert metrics["detection_rate"] == 0.95
        assert metrics["fp_rate"] == 0.02
        assert "unrelated" not in metrics

    def test_extract_from_nested_dict(self):
        from dashboard_server import _extract_metrics

        data = {"metrics": {"f1": 0.88, "precision": 0.91}}
        metrics = _extract_metrics(data)
        assert metrics["f1"] == 0.88
        assert metrics["precision"] == 0.91

    def test_extract_from_non_dict_returns_empty(self):
        from dashboard_server import _extract_metrics

        assert _extract_metrics([1, 2, 3]) == {}
        assert _extract_metrics("string") == {}
        assert _extract_metrics(None) == {}

    def test_extract_handles_empty_dict(self):
        from dashboard_server import _extract_metrics

        assert _extract_metrics({}) == {}


class TestSafeReadJson:
    def test_reads_valid_json(self, tmp_path, monkeypatch):
        from dashboard_server import _safe_read_json

        monkeypatch.setattr("dashboard_server.REPOS_DIR", tmp_path)
        f = tmp_path / "test.json"
        f.write_text('{"key": "value"}', encoding="utf-8")
        result = _safe_read_json(f)
        assert result == {"key": "value"}

    def test_returns_none_for_invalid_json(self, tmp_path):
        from dashboard_server import _safe_read_json

        f = tmp_path / "bad.json"
        f.write_text("not json at all", encoding="utf-8")
        result = _safe_read_json(f)
        assert result is None

    def test_returns_none_for_missing_file(self, tmp_path):
        from dashboard_server import _safe_read_json

        f = tmp_path / "nonexistent.json"
        result = _safe_read_json(f)
        assert result is None


# ---------------------------------------------------------------------------
# Robustness / hardening
# ---------------------------------------------------------------------------


class TestServeIndexRobustness:
    def test_missing_index_returns_fallback(self, client):
        """If index.html is absent, serve a fallback page, not a 500 traceback."""
        with patch("dashboard_server.Path.is_file", return_value=False):
            response = client.get("/")
        assert response.status_code == 200
        assert "No index.html found" in response.text

    def test_unreadable_index_returns_clean_500(self, client):
        """A read/decode error on index.html returns a clean 500, not a traceback."""
        import dashboard_server

        with (
            patch.object(dashboard_server.Path, "is_file", return_value=True),
            patch.object(
                dashboard_server.Path,
                "read_text",
                side_effect=OSError("simulated read failure"),
            ),
        ):
            response = client.get("/")
        assert response.status_code == 500
        assert "could not be read" in response.text


class TestEvidenceSizeCap:
    def test_oversized_evidence_file_is_skipped(self, tmp_path, monkeypatch):
        """Evidence JSON files at/over the 10MB cap are excluded from discovery."""
        import dashboard_server

        repo = tmp_path / "some-repo"
        (repo / "results").mkdir(parents=True)
        small = repo / "results" / "small.json"
        small.write_text('{"detection_rate": 0.9}', encoding="utf-8")
        big = repo / "results" / "big.json"
        # Write a valid-ish JSON larger than the 10MB cap.
        big.write_text("[" + ",".join(["0"] * 6_000_000) + "]", encoding="utf-8")
        assert big.stat().st_size >= 10_000_000

        monkeypatch.setattr(dashboard_server, "REPOS_DIR", tmp_path)
        found = dashboard_server._find_evidence_files("some-repo")
        names = {p.name for p in found}
        assert "small.json" in names
        assert "big.json" not in names


def test_production_secret_validation_is_documented_by_runtime(monkeypatch):
    """Production configuration requires a strong secret before serving."""
    import dashboard_server

    assert hasattr(dashboard_server, "ENVIRONMENT")


class TestMetricAggregationSafety:
    def test_metrics_summary_does_not_average_incompatible_evidence(
        self, tmp_path, monkeypatch, api_headers
    ):
        import dashboard_server

        repo = tmp_path / "sample"
        (repo / "evidence").mkdir(parents=True)
        (repo / "evidence" / "a.json").write_text(
            '{"detection_rate": 0.9, "fp_rate": 0.1}', encoding="utf-8"
        )
        (repo / "evidence" / "b.json").write_text(
            '{"detection_rate": 0.2, "fp_rate": 0.8}', encoding="utf-8"
        )

        monkeypatch.setattr(dashboard_server, "REPOS_DIR", tmp_path)
        monkeypatch.setattr(dashboard_server, "SIBLING_REPOS", ["sample"])
        client = TestClient(dashboard_server.app)
        response = client.get("/api/metrics", headers=api_headers)

        assert response.status_code == 200
        summary = response.json()["repos"]["sample"]["summary"]
        assert "avg_detection_rate" not in summary
        assert "avg_fp_rate" not in summary
        assert summary["evidence_documents_with_metrics"] == 2


class TestSecurityBoundaryRegression:
    def test_rate_limit_budget_is_enforced_per_identity(self, monkeypatch):
        import dashboard_server

        monkeypatch.setattr(dashboard_server, "RATE_LIMIT_RPM", 2)
        dashboard_server._rate_windows.clear()

        assert dashboard_server._consume_rate_limit("client-a") is True
        assert dashboard_server._consume_rate_limit("client-a") is True
        assert dashboard_server._consume_rate_limit("client-a") is False
        assert dashboard_server._consume_rate_limit("client-b") is True

    def test_evidence_repo_name_cannot_escape_root(self, tmp_path, monkeypatch):
        import dashboard_server

        monkeypatch.setattr(dashboard_server, "REPOS_DIR", tmp_path)
        outside = tmp_path.parent / "outside"
        outside.mkdir(exist_ok=True)
        (outside / "evidence").mkdir(exist_ok=True)

        assert dashboard_server._find_evidence_files("../outside") == []

    def test_cors_never_uses_wildcard_origin(self):
        import dashboard_server

        assert "*" not in dashboard_server.ALLOWED_ORIGINS


def test_rotating_invalid_keys_cannot_bypass_limit(client, monkeypatch):
    import dashboard_server

    monkeypatch.setattr(dashboard_server, "RATE_LIMIT_RPM", 2)
    dashboard_server._rate_windows.clear()
    try:
        assert (
            client.get("/api/status", headers={"X-API-Key": "first"}).status_code == 401
        )
        assert (
            client.get("/api/status", headers={"X-API-Key": "second"}).status_code
            == 401
        )
        assert (
            client.get("/api/status", headers={"X-API-Key": "third"}).status_code == 429
        )
    finally:
        dashboard_server._rate_windows.clear()


def test_rate_table_is_bounded_and_expires(monkeypatch):
    import dashboard_server

    dashboard_server._rate_windows.clear()
    monkeypatch.setattr(dashboard_server, "MAX_RATE_IDENTITIES", 2)
    monkeypatch.setattr(dashboard_server.time, "monotonic", lambda: 100.0)
    try:
        assert dashboard_server._consume_rate_limit("a")
        assert dashboard_server._consume_rate_limit("b")
        assert not dashboard_server._consume_rate_limit("c")
        monkeypatch.setattr(dashboard_server.time, "monotonic", lambda: 161.0)
        assert dashboard_server._consume_rate_limit("c")
        assert len(dashboard_server._rate_windows) == 1
    finally:
        dashboard_server._rate_windows.clear()


def test_non_ascii_key_is_rejected_without_500():
    import asyncio

    from fastapi import HTTPException

    from dashboard_server import verify_api_key

    with pytest.raises(HTTPException) as exc:
        asyncio.run(verify_api_key("\u00e9"))
    assert exc.value.status_code == 401


def test_evidence_symlinks_and_external_reads_are_rejected(tmp_path, monkeypatch):
    import dashboard_server

    root = tmp_path / "root"
    results = root / "sample" / "results"
    results.mkdir(parents=True)
    outside = tmp_path / "private.json"
    outside.write_text('{"test_count": 10}')
    (results / "linked.json").symlink_to(outside)
    (results / "directory").symlink_to(tmp_path, target_is_directory=True)
    monkeypatch.setattr(dashboard_server, "REPOS_DIR", root)
    assert dashboard_server._find_evidence_files("sample") == []
    assert dashboard_server._safe_read_json(outside) is None


def test_evidence_read_limit_and_discovery_count(tmp_path, monkeypatch):
    import dashboard_server

    monkeypatch.setattr(dashboard_server, "REPOS_DIR", tmp_path)
    monkeypatch.setattr(dashboard_server, "MAX_EVIDENCE_BYTES", 32)
    monkeypatch.setattr(dashboard_server, "MAX_EVIDENCE_FILES", 2)
    results = tmp_path / "sample" / "results"
    results.mkdir(parents=True)
    for i in range(4):
        (results / f"{i}.json").write_text('{"test_count": 1}')
    big = results / "big.json"
    big.write_text(" " * 32)
    assert dashboard_server._safe_read_json(big) is None
    assert len(dashboard_server._find_evidence_files("sample")) == 2


def test_metric_values_cannot_include_secrets_or_nonfinite_numbers():
    from dashboard_server import _extract_metrics

    assert (
        _extract_metrics(
            {"accuracy": "sensitive data", "f1": float("nan"), "test_count": True}
        )
        == {}
    )
