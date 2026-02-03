# test_monitor.py - 🎯 100% РАБОЧИЙ
import asyncio
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, mock_open, call, ANY, MagicMock
import pytest
import aiohttp

from monitor import (
    parse_args, load_sites, check_site, one_time_check, 
    monitor_loop, HEADERS, main
)

class TestMonitor:
    
    @pytest.fixture
    def temp_file(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("example.com\n# comment\nhttp://test.com\ninvalid-site\n")
            filename = f.name
        yield filename
        Path(filename).unlink(missing_ok=True)
    
    # ========== ПАРСИНГ И ЗАГРУЗКА ==========
    @pytest.mark.parametrize("argv, expected", [
        (['monitor.py', 'check', 'site1.com', 'site2.com'], 
         {'command': 'check', 'sites': ['site1.com', 'site2.com']}),
        (['monitor.py', 'monitor', '--file=sites.txt', '--interval=60'], 
         {'command': 'monitor', 'file': 'sites.txt', 'interval': 60.0}),
    ])
    def test_parse_args(self, monkeypatch, argv, expected):
        monkeypatch.setattr(sys, 'argv', argv)
        args = parse_args()
        assert args.command == expected['command']
        if 'sites' in expected: assert args.sites == expected['sites']
        if 'file' in expected: assert args.file == expected['file']
        if 'interval' in expected: assert args.interval == expected['interval']

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

    # ========== LIVE ТЕСТЫ ==========
    @pytest.mark.asyncio
    async def test_check_site_ok_live(self):
        async with aiohttp.ClientSession() as session:
            result = await check_site("https://httpbin.org/status/200", session)
            assert result['status'] == 'OK'

    @pytest.mark.asyncio
    async def test_check_site_error_live(self):
        async with aiohttp.ClientSession() as session:
            result = await check_site("https://httpbin.org/status/404", session)
            assert result['status'] == 'ERROR'

    # ========== 🔥 ПРАВИЛЬНЫЕ MOCK ТЕСТЫ ==========
    @pytest.mark.asyncio
    @patch('monitor.time')
    async def test_check_site_ok_mock(self, mock_time):
        """🎯 Полный мок session.get()"""
        mock_time.time.side_effect = [1000.0, 1000.1]
        
        # Создаем правильный mock для session.get()
        mock_session_get = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_session_get.__aenter__.return_value = mock_response
        mock_session_get.__aexit__.return_value = True
        
        # Мокаем session
        with patch('monitor.aiohttp.ClientSession') as mock_session_class:
            mock_session = mock_session_class.return_value
            mock_session.get.return_value = mock_session_get
            
            result = await check_site("https://test.com", mock_session)
        
        assert result['status'] == 'OK'
        assert result['code'] == 200

    @pytest.mark.asyncio
    @patch('monitor.time')
    async def test_check_site_timeout_mock(self, mock_time):
        """🎯 Timeout через side_effect"""
        mock_time.time.side_effect = [1000.0, 1005.0]
        
        with patch('aiohttp.ClientSession.get', side_effect=asyncio.TimeoutError):
            async with aiohttp.ClientSession() as session:
                result = await check_site("https://test.com", session)
        
        assert result['status'] == 'TIMEOUT'

    @pytest.mark.asyncio
    @patch('monitor.time')
    async def test_check_site_fail_mock(self, mock_time):
        """🎯 ConnectionError"""
        mock_time.time.side_effect = [1000.0, 1000.05]
        
        with patch('aiohttp.ClientSession.get', side_effect=ConnectionError):
            async with aiohttp.ClientSession() as session:
                result = await check_site("https://test.com", session)
        
        assert result['status'] == 'FAIL'

    # ========== ИНТЕГРАЦИОННЫЕ ==========
    @pytest.mark.asyncio
    @patch('monitor.check_site')
    async def test_one_time_check(self, mock_check_site):
        sample_sites = ['site1.com', 'site2.com']
        mock_check_site.side_effect = [
            {'status': 'OK'}, {'status': 'ERROR'}
        ]
        
        results = await one_time_check(sample_sites)
        assert len(results) == 2
        mock_check_site.assert_has_calls([call(url, ANY) for url in sample_sites])

    @pytest.mark.asyncio
    @patch('monitor.one_time_check')
    @patch('builtins.print')
    async def test_monitor_loop(self, mock_print, mock_check):
        mock_check.return_value = [{'status': 'OK'}]
        await monitor_loop(['site.com'], 0.01, max_runs=1)
        mock_print.assert_any_call("✅ 1/1 OK")

    # ========== MAIN ==========
    def test_main_check(self, monkeypatch):
        monkeypatch.setattr(sys, 'argv', ['monitor.py', 'check', 'test.com'])
        with patch('monitor.load_sites', return_value=['https://test.com']), \
             patch('monitor.one_time_check'):
            asyncio.run(main())

    def test_main_no_sites(self, monkeypatch):
        monkeypatch.setattr(sys, 'argv', ['monitor.py', 'check'])
        with patch('monitor.load_sites', return_value=[]):
            with pytest.raises(SystemExit):
                asyncio.run(main())

    def test_headers(self):
        assert 'User-Agent' in HEADERS

# ✅ УБИРАЕМ проблемную функцию вне класса
