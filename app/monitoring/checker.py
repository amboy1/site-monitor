import asyncio
import aiohttp
import time
import sys
import argparse
from typing import List

HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }


def load_sites(args: argparse.Namespace) -> List[str]:
    sites = []
    if args.file:
        try:
            with open(args.file) as f:
                for line in f:
                    url = line.strip()
                    if url and not url.startswith('#'):
                        sites.append(f"https://{url}" if not url.startswith('http') else url)
        except FileNotFoundError:
            print("File doesn't exist")
            sys.exit()
    elif args.sites:
        sites = [f"https://{url}" if not url.startswith('http') else url for url in args.sites]
    return sites


async def check_site(url: str, session: aiohttp.ClientSession, timeout: float = 5):
    start_time = time.time()
    try:
        async with session.get(
                url,
                headers=HEADERS,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
            elapsed = (time.time() - start_time) * 1000
            if response.status == 200:
                return {"status": "OK", "time": elapsed, "code": 200}
            else:
                return {"status": "ERROR", "time": elapsed, "code": response.status}
    except asyncio.TimeoutError:
        elapsed = (time.time() - start_time) * 1000
        return {"status": "TIMEOUT", "time": elapsed, "code": 0}
    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        return {"status": "FAIL", "time": elapsed, "code": 0, "error": str(e)}


async def one_time_check(sites: List[str], timeout: float = 5):
    async with aiohttp.ClientSession() as session:
        tasks = [asyncio.create_task(check_site(url, session, timeout)) for url in sites]
        results = await asyncio.gather(*tasks)
        return results


async def monitor_loop(sites, interval, timeout: float = 5, max_runs=None):
    run = 0
    while True:
        run += 1
        print(f"[{time.time()}] Run #{run}")
        results = await one_time_check(sites, timeout)
        ok = sum(r['status'] == 'OK' for r in results)
        print(f"✅ {ok}/{len(sites)} OK")

        if max_runs and run >= max_runs:
            break
        await asyncio.sleep(interval)
