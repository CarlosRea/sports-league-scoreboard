import os
import httpx
import pytest

DEV_BASE_URL = os.getenv("DEV_BASE_URL", "http://localhost:8009")
PROD_BASE_URL = os.getenv("PROD_BASE_URL", "http://localhost:8010")


def is_service_available(url: str) -> bool:
    try:
        r = httpx.get(f"{url}/health", timeout=1.5)
        return r.status_code == 200
    except Exception:
        return False


@pytest.mark.skipif(
    not (is_service_available(DEV_BASE_URL) and is_service_available(PROD_BASE_URL)),
    reason="Both Dev and Production compose environments must be running for isolation tests",
)
class TestEnvironmentIsolation:
    """Verifies that Development and Production stacks are completely independent."""

    def test_both_environments_healthy(self):
        with httpx.Client(base_url=DEV_BASE_URL, timeout=5.0) as dev_client:
            r_dev = dev_client.get("/health")
            assert r_dev.status_code == 200
            assert r_dev.json()["status"] == "healthy"

        with httpx.Client(base_url=PROD_BASE_URL, timeout=5.0) as prod_client:
            r_prod = prod_client.get("/health")
            assert r_prod.status_code == 200
            assert r_prod.json()["status"] == "healthy"

    def test_jwt_token_signature_isolation(self):
        """Tokens minted by dev should not authenticate against prod due to distinct secrets."""
        with httpx.Client(base_url=DEV_BASE_URL, timeout=5.0) as dev_client:
            res_dev = dev_client.post(
                "/api/auth/login",
                json={"username": "admin", "password": "AdminPassword123!"},
            )
            assert res_dev.status_code == 200
            dev_token = res_dev.json()["access_token"]

        with httpx.Client(base_url=PROD_BASE_URL, timeout=5.0) as prod_client:
            # Use dev token against production endpoint
            res_cross = prod_client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {dev_token}"},
            )
            assert res_cross.status_code == 401

    def test_data_mutation_isolation(self):
        """Mutations in development must not bleed into the production database."""
        with httpx.Client(base_url=DEV_BASE_URL, timeout=5.0) as dev_client:
            login_res = dev_client.post(
                "/api/auth/login",
                json={"username": "admin", "password": "AdminPassword123!"},
            )
            assert login_res.status_code == 200
            dev_token = login_res.json()["access_token"]

            # Create team in dev
            create_res = dev_client.post(
                "/api/leagues/league-metro-2026/teams",
                headers={"Authorization": f"Bearer {dev_token}"},
                json={"name": "Dev Isolated Club", "shortName": "DIC", "color": "#123456"},
            )
            assert create_res.status_code == 201
            created_team = create_res.json()
            dev_team_id = created_team["id"]

        with httpx.Client(base_url=PROD_BASE_URL, timeout=5.0) as prod_client:
            # Verify team is NOT present in production
            prod_teams_res = prod_client.get("/api/leagues/league-metro-2026/teams")
            assert prod_teams_res.status_code == 200
            prod_teams = prod_teams_res.json()
            prod_team_ids = [t["id"] for t in prod_teams]
            assert dev_team_id not in prod_team_ids
            assert not any(t["name"] == "Dev Isolated Club" for t in prod_teams)

        # Cleanup dev by resetting dataset
        with httpx.Client(base_url=DEV_BASE_URL, timeout=5.0) as dev_client:
            reset_res = dev_client.post(
                "/api/dev/reset",
                headers={"Authorization": f"Bearer {dev_token}"},
            )
            assert reset_res.status_code == 200
