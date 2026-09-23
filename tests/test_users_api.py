import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch

from app.main import app
from app.db.database import get_db
from app.db.models import User


@pytest.fixture
def mock_db():
    session = AsyncMock()
    return session


@pytest.mark.asyncio
async def test_register_user_success(mock_db):
    app.dependency_overrides[get_db] = lambda: mock_db

    with patch("app.api.users.get_user_by_email", new_callable=AsyncMock) as mock_get, \
         patch("app.api.users.create_user", new_callable=AsyncMock) as mock_create:
        
        mock_get.return_value = None
        mock_create.return_value = User(
            id=1,
            email="test@example.com",
            hashed_password="hashed_secret",
            is_active=True,
        )

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/users/",
                json={"email": "test@example.com", "password": "supersecretpassword"},
            )

        assert resp.status_code == 201
        data = resp.json()
        assert data["id"] == 1
        assert data["email"] == "test@example.com"
        assert data["is_active"] is True
        assert "password" not in data
        assert "hashed_password" not in data

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_register_user_duplicate_email(mock_db):
    app.dependency_overrides[get_db] = lambda: mock_db

    with patch("app.api.users.get_user_by_email", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = User(
            id=1,
            email="existing@example.com",
            hashed_password="somehash",
            is_active=True,
        )

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/users/",
                json={"email": "existing@example.com", "password": "supersecretpassword"},
            )

        assert resp.status_code == 400
        assert resp.json()["detail"] == "Email already registered"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_register_user_invalid_data():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Invalid email
        resp1 = await ac.post(
            "/users/",
            json={"email": "not-an-email", "password": "validpassword"},
        )
        assert resp1.status_code == 422

        # Password too short (< 6)
        resp2 = await ac.post(
            "/users/",
            json={"email": "valid@example.com", "password": "123"},
        )
        assert resp2.status_code == 422
