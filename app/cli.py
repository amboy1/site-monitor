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

    monitor_p = subparsers.add_parser("monitor")
    monitor_p.add_argument("sites", nargs="*")
    monitor_p.add_argument("--file")
    monitor_p.add_argument("--interval", type=float, default=300)

    return parser.parse_args()


async def main():
    args = parse_args()
    sites = load_sites(args)
    if not sites:
        sys.exit("No sites!")

    if args.command == "check":
        await one_time_check(sites)
    elif args.command == "monitor":
        await monitor_loop(sites, args.interval)


if __name__ == "__main__":
    asyncio.run(main())
