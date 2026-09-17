import argparse
import sys
import asyncio

from app.monitoring.checker import load_sites, one_time_check, monitor_loop


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Async Site Checker")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_p = subparsers.add_parser("check")
    check_p.add_argument("sites", nargs="*")
    check_p.add_argument("--file")
    check_p.add_argument("--timeout", type=float, default=5, help="Timeout per request in seconds (default: 5)")

    monitor_p = subparsers.add_parser("monitor")
    monitor_p.add_argument("sites", nargs="*")
    monitor_p.add_argument("--file")
    monitor_p.add_argument("--interval", type=float, default=300, help="Interval between checks in seconds (default: 300)")
    monitor_p.add_argument("--timeout", type=float, default=5, help="Timeout per request in seconds (default: 5)")

    return parser.parse_args()


def print_check_results(results, sites):
    for site, result in zip(sites, results):
        status = result["status"]
        elapsed = result["time"]
        code = result.get("code")
        if status == "OK":
            print(f"[OK {elapsed:.0f}ms] {site}")
        elif status == "ERROR":
            print(f"[ERROR {code} {elapsed:.0f}ms] {site}")
        elif status == "TIMEOUT":
            print(f"[TIMEOUT {elapsed:.0f}ms] {site}")
        elif status == "FAIL":
            error = result.get("error", type(result).__name__)
            print(f"[FAIL {elapsed:.0f}ms] {site}: {error}")


async def main():
    args = parse_args()
    sites = load_sites(args)
    if not sites:
        sys.exit("No sites!")

    if args.command == "check":
        print(f"Checking {len(sites)} sites...")
        print("Starting parallel checks...")
        results = await one_time_check(sites, timeout=args.timeout)
        print_check_results(results, sites)
        ok = sum(r['status'] == 'OK' for r in results)
        print(f"✅ {ok}/{len(sites)} OK")
    elif args.command == "monitor":
        await monitor_loop(sites, args.interval, timeout=args.timeout)


if __name__ == "__main__":
    asyncio.run(main())
