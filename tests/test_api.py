import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.schemas.monitor import CheckResponse


class TestApiRoot:
    @pytest.mark.asyncio
    async def test_root_works(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get("/")
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
    @pytest.mark.parametrize("invalid_url", [
        "not-a-valid-url",
        "ftp://example.com",
        "://missing-scheme.com",
        "just_text",
        "",
    ])
    async def test_check_invalid_url_422(self, invalid_url):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/v1/check",
                json={"url": invalid_url, "timeout": 5},
            )
        assert resp.status_code == 422

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
    async def test_check_without_timeout_uses_default_5(self, mock_check_ok):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/v1/check",
                json={"url": "https://example.com"},
            )
        assert resp.status_code == 200
        mock_check_ok.assert_awaited_once()
        args, kwargs = mock_check_ok.call_args
        assert args[2] == 5.0

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

    @pytest.mark.asyncio
    async def test_check_response_conforms_to_check_response_model(self):
        # Verify response_model excludes unexpected fields and conforms to CheckResponse
        mock_result = {
            "status": "OK",
            "time": 42.5,
            "code": 200,
            "extra_internal_field": "do_not_leak_this",
        }
        with patch("app.main.check_site", new_callable=AsyncMock) as m:
            m.return_value = mock_result
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.post("/api/v1/check", json={"url": "https://example.com"})

        assert resp.status_code == 200
        data = resp.json()
        validated = CheckResponse.model_validate(data)
        assert validated.status == "OK"
        assert validated.code == 200
        assert validated.time == 42.5
        assert "extra_internal_field" not in data
        assert set(data.keys()).issubset({"status", "time", "code", "error"})


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
    async def test_batch_three_urls_success(self):
        mock_results = [
            {"status": "OK", "time": 10.0, "code": 200},
            {"status": "ERROR", "time": 25.0, "code": 404},
            {"status": "TIMEOUT", "time": 5000.0, "code": 0},
        ]
        urls = ["https://site1.com", "https://site2.com", "https://site3.com"]
        with patch("app.main.check_site", new_callable=AsyncMock) as m:
            m.side_effect = mock_results
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.post(
                    "/api/v1/check/batch",
                    json={"urls": urls, "timeout": 10},
                )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 3
        for item, expected in zip(data, mock_results):
            validated = CheckResponse.model_validate(item)
            assert validated.status == expected["status"]
            assert validated.code == expected["code"]
            assert validated.time == expected["time"]

    @pytest.mark.asyncio
    async def test_batch_calls_check_site_for_each_url(self):
        urls = ["https://site1.org", "https://site2.org", "https://site3.org"]
        with patch("app.main.check_site", new_callable=AsyncMock) as m:
            m.return_value = {"status": "OK", "time": 15.0, "code": 200}
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.post(
                    "/api/v1/check/batch",
                    json={"urls": urls, "timeout": 8},
                )
        assert resp.status_code == 200
        assert m.await_count == len(urls)
        called_urls = [call_args[0][0] for call_args in m.call_args_list]
        assert len(called_urls) == 3
        for url in urls:
            assert any(url in called_url for called_url in called_urls)

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
    async def test_batch_without_timeout_uses_default_5(self):
        urls = ["https://a.com", "https://b.com"]
        with patch("app.main.check_site", new_callable=AsyncMock) as m:
            m.return_value = {"status": "OK", "time": 10.0, "code": 200}
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.post(
                    "/api/v1/check/batch",
                    json={"urls": urls},
                )
        assert resp.status_code == 200
        assert m.await_count == 2
        for call_args in m.call_args_list:
            args, kwargs = call_args
            assert args[2] == 5.0

    @pytest.mark.asyncio
    async def test_batch_empty_422(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/v1/check/batch",
                json={"urls": [], "timeout": 5},
            )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_batch_invalid_url_in_list_422(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/v1/check/batch",
                json={"urls": ["https://valid.com", "not-a-valid-url"]},
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

    @pytest.mark.asyncio
    async def test_batch_response_conforms_to_check_response_model(self):
        mock_results = [
            {"status": "OK", "time": 10.0, "code": 200, "extra_secret": "xyz"},
            {"status": "ERROR", "time": 20.0, "code": 500, "leak_data": 123},
        ]
        urls = ["https://a.com", "https://b.com"]
        with patch("app.main.check_site", new_callable=AsyncMock) as m:
            m.side_effect = mock_results
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.post("/api/v1/check/batch", json={"urls": urls})

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        expected_fields = {"status", "time", "code", "error"}
        for item in data:
            validated = CheckResponse.model_validate(item)
            assert validated is not None
            assert "extra_secret" not in item
            assert "leak_data" not in item
            assert set(item.keys()).issubset(expected_fields)
