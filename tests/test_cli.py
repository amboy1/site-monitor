import asyncio
import sys
from unittest.mock import patch
import pytest

from app.cli import parse_args, main


class TestCli:

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

    def test_main_check(self, monkeypatch):
        monkeypatch.setattr(sys, 'argv', ['monitor.py', 'check', 'test.com'])
        with patch('app.cli.load_sites', return_value=['https://test.com']), \
             patch('app.cli.one_time_check'):
            asyncio.run(main())

    def test_main_no_sites(self, monkeypatch):
        monkeypatch.setattr(sys, 'argv', ['monitor.py', 'check'])
        with patch('app.cli.load_sites', return_value=[]):
            with pytest.raises(SystemExit):
                asyncio.run(main())
