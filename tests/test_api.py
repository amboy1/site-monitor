import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from app.main import app


class TestApiRoot:
    client = TestClient(app)

    def test_root_works(self):
        resp = self.client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "Async Site Monitor"
        assert "stage" in data
        assert "docs" in data


class TestApiCheckSingle:
    @pytest.fixture
    def mock_check_ok(self):
        with patch("app.main.check_site", new_callable=AsyncMock) as m:
            m.return_value = {"status": "OK", "time": 123.4, "code": 200}
            yield m

    @pytest.fixture
    def mock_check_error(self):
        with patch("app.main.check_site", new_callable=AsyncMock) as m:
            m.return_value = {"status": "ERROR", "time": 90.0, "code": 500}
            yield m

    @pytest.mark.asyncio
    async def test_check_accepts_correct_request(self, mock_check_ok):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/v1/check",
                json={"url": "https://example.com", "timeout": 5},
            )
        assert resp.status_code == 200
        mock_check_ok.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_check_returns_expected_structure(self, mock_check_ok):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/v1/check",
                json={"url": "https://example.com"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "OK"
        assert data["code"] == 200
        assert data["time"] == 123.4

    @pytest.mark.asyncio
    async def test_check_passes_timeout(self, mock_check_ok):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/v1/check",
                json={"url": "https://example.com", "timeout": 15.5},
            )
        assert resp.status_code == 200
        args, kwargs = mock_check_ok.call_args
        assert args[2] == 15.5

    @pytest.mark.asyncio
    async def test_check_external_500_not_api_500(self, mock_check_error):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/v1/check",
                json={"url": "https://example.com"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ERROR"
        assert data["code"] == 500

    @pytest.mark.asyncio
    @pytest.mark.parametrize("bad_timeout", [-1, 0, 31, 100])
    async def test_check_timeout_validation_422(self, bad_timeout):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/v1/check",
                json={"url": "https://example.com", "timeout": bad_timeout},
            )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    @pytest.mark.parametrize("good_timeout", [0.1, 5, 10, 30])
    async def test_check_timeout_valid(self, good_timeout, mock_check_ok):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/v1/check",
                json={"url": "https://example.com", "timeout": good_timeout},
            )
        assert resp.status_code == 200


class TestApiCheckBatch:
    @pytest.fixture
    def mock_check_batch(self):
        with patch("app.main.check_site", new_callable=AsyncMock) as m:
            m.side_effect = [
                {"status": "OK", "time": 123.4, "code": 200},
                {"status": "OK", "time": 150.2, "code": 200},
            ]
            yield m

    @pytest.mark.asyncio
    async def test_batch_accepts_multiple_urls(self, mock_check_batch):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/v1/check/batch",
                json={
                    "urls": ["https://example.com", "https://google.com"],
                    "timeout": 5,
                },
            )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_batch_returns_array(self, mock_check_batch):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/v1/check/batch",
                json={"urls": ["https://a.com", "https://b.com"]},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["status"] == "OK"
        assert data[1]["status"] == "OK"

    @pytest.mark.asyncio
    async def test_batch_passes_timeout_each(self, mock_check_batch):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/v1/check/batch",
                json={"urls": ["https://a.com", "https://b.com"], "timeout": 20},
            )
        assert resp.status_code == 200
        assert mock_check_batch.await_count == 2
        for call_args in mock_check_batch.call_args_list:
            args, kwargs = call_args
            assert args[2] == 20

    @pytest.mark.asyncio
    async def test_batch_empty_422(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/v1/check/batch",
                json={"urls": [], "timeout": 5},
            )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_batch_too_many_422(self):
        urls = [f"https://site-{i}.com" for i in range(51)]
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/v1/check/batch",
                json={"urls": urls, "timeout": 5},
            )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_batch_50_urls_ok(self, mock_check_batch):
        mock_check_batch.side_effect = None
        mock_check_batch.return_value = {"status": "OK", "time": 10.0, "code": 200}
        urls = [f"https://site-{i}.com" for i in range(50)]
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/v1/check/batch",
                json={"urls": urls, "timeout": 5},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 50

    @pytest.mark.asyncio
    @pytest.mark.parametrize("bad_timeout", [-1, 0, 31])
    async def test_batch_timeout_validation_422(self, bad_timeout):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/v1/check/batch",
                json={"urls": ["https://a.com"], "timeout": bad_timeout},
            )
        assert resp.status_code == 422
