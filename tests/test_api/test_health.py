"""Tests for health check and system endpoints."""


class TestHealth:
    def test_health_check(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"
        assert data["database"] == "ok"
        assert "timestamp" in data

    def test_scrape_status_empty(self, client):
        response = client.get("/api/v1/scrape/status")
        assert response.status_code == 200
        data = response.get_json()
        assert data["runs"] == []
