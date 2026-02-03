import asyncio
import aiohttp
import random
import time 
import argparse
import sys
from typing import List

HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Async Site Checker")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # check
    check_p = subparsers.add_parser("check")
    check_p.add_argument("sites", nargs="*")
    check_p.add_argument("--file")
    
    # monitor  
    monitor_p = subparsers.add_parser("monitor")
    monitor_p.add_argument("sites", nargs="*")
    monitor_p.add_argument("--file")
    monitor_p.add_argument("--interval", type=float, default=300)
    
    return parser.parse_args()


def load_sites(args: argparse.Namespace) -> List[str]:
    sites = []
    if args.file:
        try: 
            with open(args.file) as f:
                for line in f:
                    url = line.strip()
                    if url and not url.startswith('#'):
                        sites.append(f"https://{url}" if not url.startswith(('http')) else url)
        except FileNotFoundError:
            print("File doesn't exist")
            sys.exit()
    elif args.sites:
        sites = [f"https://{url}" if not url.startswith(('http')) else url for url in args.sites]
    return sites


async def check_site(url: str, session: aiohttp.ClientSession):
    start_time = time.time()
    try: 
        async with session.get(
                url, 
                headers=HEADERS,  
                timeout=aiohttp.ClientTimeout(total=5)  
            ) as response:
            elapsed = (time.time() - start_time) * 1000  # в миллисекундах
            if response.status == 200:
                print(f"[OK {elapsed:.0f}ms] {url}")
                return {"status": "OK", "time": elapsed, "code": 200}
            else: 
                print(f"[ERROR {response.status} {elapsed:.0f}ms] {url}")
                return {"status": "ERROR", "time": elapsed, "code": response.status}
    except asyncio.TimeoutError:
        elapsed = (time.time() - start_time) * 1000
        print(f"[TIMEOUT {elapsed:.0f}ms] {url}")
        return {"status": "TIMEOUT", "time": elapsed, "code": 0}
    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        print(f"[FAIL {elapsed:.0f}ms] {url}: {type(e).__name__}")
        return {"status": "FAIL", "time": elapsed, "code": 0, "error": str(e)}
    

async def one_time_check(sites: List[str]):
    print(f"Checking {len(sites)} sites...")
    async with aiohttp.ClientSession() as session:
        tasks = [asyncio.create_task(check_site(url, session)) for url in sites]
        print("Starting parallel checks...")
        results = await asyncio.gather(*tasks) 
        return results
    

async def monitor_loop(sites, interval, max_runs=None):
    run = 0
    while True:
        run += 1
        print(f"[{time.time()}] Run #{run}")
        results = await one_time_check(sites) 
        ok = sum(r['status'] == 'OK' for r in results)
        print(f"✅ {ok}/{len(sites)} OK")
        
        if max_runs and run >= max_runs:
            break
        await asyncio.sleep(interval)


async def main():
    args = parse_args()  # CLI логика
    sites = load_sites(args)  # загрузка
    if not sites:
        sys.exit("No sites!")
    
    if args.command == "check":
        await one_time_check(sites)
    elif args.command == "monitor":
        await monitor_loop(sites, args.interval)


if __name__ == "__main__":
    asyncio.run(main())
