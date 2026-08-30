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

    def test_empty_api_key_returns_500(self, client):
        """If DASHBOARD_API_KEY env var is empty, server returns 500."""
        with patch.dict(os.environ, {"DASHBOARD_API_KEY": ""}):
            # Need to reload the module to pick up the new env var
            import dashboard_server
            original_key = dashboard_server.API_KEY
            dashboard_server.API_KEY = ""
            try:
                response = client.get(
                    "/api/status", headers={"X-API-Key": "anything"}
                )
                assert response.status_code == 500
                assert "misconfigured" in response.json()["detail"].lower()
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
        assert "repos_dir" in data
        assert "ts" in data
        assert isinstance(data["repos"], dict)

    def test_status_reports_repo_existence(self, client, api_headers):
        response = client.get("/api/status", headers=api_headers)
        data = response.json()
        # Each repo entry should have an 'exists' field
        for repo_name, repo_status in data["repos"].items():
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
    def test_reads_valid_json(self, tmp_path):
        from dashboard_server import _safe_read_json

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
