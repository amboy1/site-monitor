import asyncio
import aiohttp
import random
from typing import List

async def check_site(url: str, session: aiohttp.ClientSession):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    try: 
        async with session.get(url, timeout=5, headers=headers) as response:
            if response.status == 200:
                print(f"[OK] {url}")
                return True
            else: 
                print(f"[ERROR {response.status}] {url}")
                return False
    except asyncio.TimeoutError:
        print(f"[TIMEOUT] {url}")
        return False
    except Exception as e:
        print(f"[FAIL] {url}: {type(e).__name__}")
        return False
        

async def main(sites: List[str]):
    print(f"Checking {len(sites)} sites...")
    async with aiohttp.ClientSession() as session:
        tasks = []
        for url in sites:
            task = asyncio.create_task(check_site(url, session))
            tasks.append(task)
        
        print("🚀 Starting parallel checks...")
        results = await asyncio.gather(*tasks) 
        
        successful = sum(1 for r in results if r) 
        failed = len(results) - successful
        
        print(f"\n📊 RESULTS:")
        print(f"✅ Working: {successful}")
        print(f"❌ Failed: {failed}")

    


if __name__ == "__main__":
    print("Choose the command:")
    print("1. Test your sites.")
    print("2. Test sites.txt")
    
    command = int(input())
    test_sites = []
    
    if command == 1: 
        print("Count of sites:")
        number = int(input())
        for i in range(number):
            print(f"Site {i+1} URL:")
            url = input().strip()
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            test_sites.append(url)
            
    elif command == 2:
        try:
            with open("sites.txt", "r") as f:
                for line in f:
                    url = line.strip()
                    if url and not url.startswith("#"):  # Пропускаем пустые строки и комментарии
                        if not url.startswith(("http://", "https://")):
                            url = "https://" + url
                        test_sites.append(url)
        except FileNotFoundError:
            print("File sites.txt not found! Creating default...")
            with open("sites.txt", "w") as f:
                f.write("# Add your sites here, one per line\n")
                f.write("https://google.com\n")
                f.write("https://github.com\n")
            test_sites = ["https://google.com", "https://github.com"]
    
    if test_sites:
        asyncio.run(main(test_sites))
    else:
        print("No sites to check!")