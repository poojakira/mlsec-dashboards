"""
Comprehensive test suite for mlsec-dashboards.
Covers all endpoints, static assets, CORS, authentication, and error handling.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta


@pytest.fixture
def app():
    """Create and configure a test application instance."""
    from app import create_app
    app = create_app(testing=True)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret-key"
    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture
def auth_headers():
    """Return valid authentication headers."""
    return {
        "Authorization": "Bearer test-valid-token-abc123",
        "Content-Type": "application/json",
    }


@pytest.fixture
def mock_dashboard_data():
    """Sample dashboard data for testing."""
    return {
        "metrics": {
            "total_threats": 142,
            "active_incidents": 7,
            "models_monitored": 23,
            "anomalies_detected": 31,
        },
        "timestamp": "2026-08-27T12:00:00Z",
    }


# ---------------------------------------------------------------------------
# Health & Status Endpoints
# ---------------------------------------------------------------------------

class TestHealthEndpoints:
    """Tests for health check and status endpoints."""

    def test_health_check_returns_200(self, client):
        """GET /health should return 200 with status ok."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"

    def test_health_check_includes_version(self, client):
        """Health endpoint should include application version."""
        response = client.get("/health")
        data = response.get_json()
        assert "version" in data

    def test_readiness_check(self, client):
        """GET /ready should confirm service readiness."""
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.get_json()
        assert data["ready"] is True

    def test_readiness_check_when_db_down(self, client):
        """Readiness should return 503 when database is unavailable."""
        with patch("app.db.check_connection", return_value=False):
            response = client.get("/ready")
            assert response.status_code == 503


# ---------------------------------------------------------------------------
# Dashboard API Endpoints
# ---------------------------------------------------------------------------

class TestDashboardEndpoints:
    """Tests for dashboard data endpoints."""

    def test_get_dashboard_summary_authenticated(self, client, auth_headers):
        """GET /api/v1/dashboard/summary requires auth and returns data."""
        with patch("app.services.dashboard.get_summary") as mock_summary:
            mock_summary.return_value = {"total_threats": 142}
            response = client.get("/api/v1/dashboard/summary", headers=auth_headers)
            assert response.status_code == 200
            data = response.get_json()
            assert "total_threats" in data

    def test_get_dashboard_summary_unauthenticated(self, client):
        """GET /api/v1/dashboard/summary without auth returns 401."""
        response = client.get("/api/v1/dashboard/summary")
        assert response.status_code == 401

    def test_get_threat_timeline(self, client, auth_headers):
        """GET /api/v1/dashboard/threats/timeline returns time series data."""
        with patch("app.services.dashboard.get_threat_timeline") as mock_timeline:
            mock_timeline.return_value = [
                {"timestamp": "2026-08-27T00:00:00Z", "count": 5},
                {"timestamp": "2026-08-27T01:00:00Z", "count": 3},
            ]
            response = client.get(
                "/api/v1/dashboard/threats/timeline",
                headers=auth_headers,
            )
            assert response.status_code == 200
            data = response.get_json()
            assert isinstance(data, list)
            assert len(data) >= 1

    def test_get_model_status(self, client, auth_headers):
        """GET /api/v1/dashboard/models returns model monitoring status."""
        with patch("app.services.dashboard.get_model_status") as mock_models:
            mock_models.return_value = [
                {"model_id": "m-001", "status": "healthy", "drift_score": 0.02}
            ]
            response = client.get("/api/v1/dashboard/models", headers=auth_headers)
            assert response.status_code == 200
            data = response.get_json()
            assert isinstance(data, list)

    def test_get_incidents_list(self, client, auth_headers):
        """GET /api/v1/dashboard/incidents returns active incidents."""
        with patch("app.services.dashboard.get_incidents") as mock_incidents:
            mock_incidents.return_value = []
            response = client.get("/api/v1/dashboard/incidents", headers=auth_headers)
            assert response.status_code == 200

    def test_get_anomaly_details(self, client, auth_headers):
        """GET /api/v1/dashboard/anomalies/:id returns anomaly details."""
        with patch("app.services.dashboard.get_anomaly") as mock_anomaly:
            mock_anomaly.return_value = {
                "id": "a-001",
                "severity": "high",
                "model_id": "m-001",
            }
            response = client.get(
                "/api/v1/dashboard/anomalies/a-001", headers=auth_headers
            )
            assert response.status_code == 200
            data = response.get_json()
            assert data["id"] == "a-001"

    def test_get_anomaly_not_found(self, client, auth_headers):
        """GET /api/v1/dashboard/anomalies/:id returns 404 for missing anomaly."""
        with patch("app.services.dashboard.get_anomaly", return_value=None):
            response = client.get(
                "/api/v1/dashboard/anomalies/nonexistent", headers=auth_headers
            )
            assert response.status_code == 404


# ---------------------------------------------------------------------------
# Static Assets
# ---------------------------------------------------------------------------

class TestStaticAssets:
    """Tests for static asset serving."""

    def test_static_css_served(self, client):
        """Static CSS files should be served with correct content type."""
        response = client.get("/static/css/dashboard.css")
        assert response.status_code == 200
        assert "text/css" in response.content_type

    def test_static_js_served(self, client):
        """Static JS files should be served with correct content type."""
        response = client.get("/static/js/app.js")
        assert response.status_code == 200
        assert "javascript" in response.content_type

    def test_static_asset_caching_headers(self, client):
        """Static assets should include cache control headers."""
        response = client.get("/static/css/dashboard.css")
        assert "Cache-Control" in response.headers

    def test_missing_static_asset_returns_404(self, client):
        """Request for nonexistent static asset returns 404."""
        response = client.get("/static/nonexistent/file.xyz")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

class TestCORS:
    """Tests for CORS configuration."""

    def test_cors_preflight_request(self, client):
        """OPTIONS request should return CORS headers."""
        response = client.options(
            "/api/v1/dashboard/summary",
            headers={"Origin": "https://allowed-origin.example.com"},
        )
        assert response.status_code in (200, 204)
        assert "Access-Control-Allow-Origin" in response.headers

    def test_cors_allowed_origin(self, client, auth_headers):
        """Requests from allowed origins should include CORS headers."""
        headers = {**auth_headers, "Origin": "https://allowed-origin.example.com"}
        with patch("app.services.dashboard.get_summary", return_value={}):
            response = client.get("/api/v1/dashboard/summary", headers=headers)
            assert "Access-Control-Allow-Origin" in response.headers

    def test_cors_disallowed_origin(self, client, auth_headers):
        """Requests from disallowed origins should not have permissive CORS."""
        headers = {**auth_headers, "Origin": "https://evil-site.example.com"}
        with patch("app.services.dashboard.get_summary", return_value={}):
            response = client.get("/api/v1/dashboard/summary", headers=headers)
            cors_header = response.headers.get("Access-Control-Allow-Origin", "")
            assert cors_header != "*"
            assert "evil-site" not in cors_header


# ---------------------------------------------------------------------------
# Authentication & Authorization
# ---------------------------------------------------------------------------

class TestAuthentication:
    """Tests for authentication and authorization."""

    def test_expired_token_rejected(self, client):
        """Expired JWT tokens should be rejected with 401."""
        headers = {
            "Authorization": "Bearer expired-token-xyz",
            "Content-Type": "application/json",
        }
        with patch("app.auth.verify_token", side_effect=Exception("Token expired")):
            response = client.get("/api/v1/dashboard/summary", headers=headers)
            assert response.status_code == 401

    def test_malformed_token_rejected(self, client):
        """Malformed tokens should be rejected."""
        headers = {
            "Authorization": "Bearer not.a.valid.jwt.token",
            "Content-Type": "application/json",
        }
        response = client.get("/api/v1/dashboard/summary", headers=headers)
        assert response.status_code == 401

    def test_missing_authorization_header(self, client):
        """Requests without Authorization header should get 401."""
        response = client.get("/api/v1/dashboard/summary")
        assert response.status_code == 401

    def test_role_based_access_admin(self, client):
        """Admin role should access admin-only endpoints."""
        headers = {
            "Authorization": "Bearer admin-token",
            "Content-Type": "application/json",
        }
        with patch("app.auth.verify_token", return_value={"role": "admin"}):
            with patch("app.services.dashboard.get_admin_config", return_value={}):
                response = client.get("/api/v1/dashboard/admin/config", headers=headers)
                assert response.status_code == 200

    def test_role_based_access_viewer_denied(self, client):
        """Viewer role should be denied access to admin endpoints."""
        headers = {
            "Authorization": "Bearer viewer-token",
            "Content-Type": "application/json",
        }
        with patch("app.auth.verify_token", return_value={"role": "viewer"}):
            response = client.get("/api/v1/dashboard/admin/config", headers=headers)
            assert response.status_code == 403


# ---------------------------------------------------------------------------
# Error Handling & Edge Cases
# ---------------------------------------------------------------------------

class TestErrorHandling:
    """Tests for error handling and edge cases."""

    def test_invalid_json_body(self, client, auth_headers):
        """POST with invalid JSON body should return 400."""
        response = client.post(
            "/api/v1/dashboard/filters",
            data="not-valid-json{{{",
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_method_not_allowed(self, client, auth_headers):
        """Using wrong HTTP method should return 405."""
        response = client.delete("/api/v1/dashboard/summary", headers=auth_headers)
        assert response.status_code == 405

    def test_rate_limiting(self, client, auth_headers):
        """Excessive requests should be rate limited."""
        responses = []
        with patch("app.services.dashboard.get_summary", return_value={}):
            for _ in range(150):
                resp = client.get("/api/v1/dashboard/summary", headers=auth_headers)
                responses.append(resp.status_code)
        assert 429 in responses

    def test_large_query_parameter_rejected(self, client, auth_headers):
        """Excessively large query parameters should be rejected."""
        huge_param = "x" * 10000
        response = client.get(
            f"/api/v1/dashboard/summary?filter={huge_param}",
            headers=auth_headers,
        )
        assert response.status_code in (400, 414)


# ---------------------------------------------------------------------------
# WebSocket / Real-time Updates
# ---------------------------------------------------------------------------

class TestWebSocket:
    """Tests for real-time dashboard updates."""

    def test_websocket_connection_requires_auth(self, client):
        """WebSocket connections should require authentication."""
        with patch("app.ws.authenticate", return_value=False):
            response = client.get("/ws/dashboard")
            assert response.status_code in (401, 403, 426)

    def test_websocket_sends_updates(self, client, auth_headers):
        """Authenticated WebSocket should receive dashboard updates."""
        with patch("app.ws.authenticate", return_value=True):
            with patch("app.ws.get_client") as mock_ws:
                mock_ws.return_value.receive.return_value = json.dumps(
                    {"type": "subscribe", "channel": "threats"}
                )
                response = client.get("/ws/dashboard", headers=auth_headers)
                assert response.status_code in (101, 200, 426)
