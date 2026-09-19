import asyncio
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, mock_open, call, ANY
import pytest
import aiohttp

from app.monitoring.checker import (
    load_sites, check_site, one_time_check, monitor_loop, HEADERS
)


class TestChecker:

    @pytest.fixture
    def temp_file(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("example.com\n# comment\nhttp://test.com\ninvalid-site\n")
            filename = f.name
        yield filename
        Path(filename).unlink(missing_ok=True)

    def test_load_sites_from_args(self):
        class Args: sites = ['google.com']; file = None
        assert load_sites(Args()) == ['https://google.com']

    def test_load_sites_from_file(self, temp_file):
        class Args: file = temp_file; sites = None
        result = load_sites(Args())
        assert len(result) == 3
        assert result[0] == 'https://example.com'

    @patch('sys.exit')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_sites_file_not_found(self, mock_file, mock_exit):
        mock_file.side_effect = FileNotFoundError()
        class Args: file = 'nope.txt'; sites = None
        load_sites(Args())
        mock_exit.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_site_200_ok(self):
        mock_cm_get = AsyncMock()
        mock_response = Mock()
        mock_response.status = 200
        mock_cm_get.__aenter__.return_value = mock_response
        mock_cm_get.__aexit__.return_value = False

        mock_session = Mock()
        mock_session.get.return_value = mock_cm_get

        result = await check_site("https://test.com", mock_session)

        assert result['status'] == 'OK'
        assert result['code'] == 200
        assert 'time' in result
        mock_session.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_site_404_error(self):
        mock_cm_get = AsyncMock()
        mock_response = Mock()
        mock_response.status = 404
        mock_cm_get.__aenter__.return_value = mock_response
        mock_cm_get.__aexit__.return_value = False

        mock_session = Mock()
        mock_session.get.return_value = mock_cm_get

        result = await check_site("https://test.com/not-found", mock_session)

        assert result['status'] == 'ERROR'
        assert result['code'] == 404
        assert 'time' in result

    @pytest.mark.asyncio
    async def test_check_site_calls_session_get_with_exact_url(self):
        test_url = "https://custom-target.org/path?query=1"
        mock_cm_get = AsyncMock()
        mock_response = Mock()
        mock_response.status = 200
        mock_cm_get.__aenter__.return_value = mock_response
        mock_cm_get.__aexit__.return_value = False

        mock_session = Mock()
        mock_session.get.return_value = mock_cm_get

        await check_site(test_url, mock_session)

        mock_session.get.assert_called_once()
        args, kwargs = mock_session.get.call_args
        assert args[0] == test_url

    @pytest.mark.asyncio
    async def test_check_site_500_error(self):
        mock_cm_get = AsyncMock()
        mock_response = Mock()
        mock_response.status = 500
        mock_cm_get.__aenter__.return_value = mock_response
        mock_cm_get.__aexit__.return_value = False

        mock_session = Mock()
        mock_session.get.return_value = mock_cm_get

        result = await check_site("https://test.com", mock_session)

        assert result['status'] == 'ERROR'
        assert result['code'] == 500

    @pytest.mark.asyncio
    async def test_check_site_timeout(self):
        mock_session = Mock()
        mock_session.get.side_effect = asyncio.TimeoutError()

        result = await check_site("https://test.com", mock_session)

        assert result['status'] == 'TIMEOUT'
        assert result['code'] == 0

    @pytest.mark.asyncio
    async def test_check_site_fail_exception(self):
        mock_session = Mock()
        mock_session.get.side_effect = ConnectionError("boom")

        result = await check_site("https://test.com", mock_session)

        assert result['status'] == 'FAIL'
        assert result['code'] == 0
        assert 'boom' in result['error']

    @pytest.mark.asyncio
    async def test_check_site_timeout_value_is_used(self):
        custom_timeout = 12.5
        mock_cm_get = AsyncMock()
        mock_response = Mock()
        mock_response.status = 200
        mock_cm_get.__aenter__.return_value = mock_response
        mock_cm_get.__aexit__.return_value = False

        mock_session = Mock()
        mock_session.get.return_value = mock_cm_get

        await check_site("https://test.com", mock_session, timeout=custom_timeout)

        call_kwargs = mock_session.get.call_args
        assert call_kwargs is not None
        timeout_arg = call_kwargs.kwargs.get('timeout')
        assert timeout_arg is not None
        assert timeout_arg.total == custom_timeout

    @pytest.mark.asyncio
    @patch('app.monitoring.checker.check_site')
    async def test_one_time_check_passes_timeout(self, mock_check_site):
        sample_sites = ['https://site1.com', 'https://site2.com']
        custom_timeout = 7.5
        mock_check_site.side_effect = [
            {'status': 'OK', 'time': 100.0, 'code': 200},
            {'status': 'ERROR', 'time': 150.0, 'code': 500},
        ]

        results = await one_time_check(sample_sites, timeout=custom_timeout)
        assert len(results) == 2

        assert mock_check_site.call_count == 2
        for call_args in mock_check_site.call_args_list:
            assert call_args[0][1] is not None
            assert call_args[0][2] == custom_timeout

    @pytest.mark.asyncio
    @patch('app.monitoring.checker.one_time_check')
    @patch('builtins.print')
    async def test_monitor_loop(self, mock_print, mock_check):
        mock_check.return_value = [{'status': 'OK'}]
        await monitor_loop(['site.com'], 0.01, timeout=5, max_runs=1)
        mock_print.assert_any_call("✅ 1/1 OK")
        mock_check.assert_called_once_with(['site.com'], 5)

    def test_headers(self):
        assert 'User-Agent' in HEADERS
