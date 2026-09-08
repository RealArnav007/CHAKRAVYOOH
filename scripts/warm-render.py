#!/usr/bin/env python3
"""
warm-render.py — Render cold-start killer.

Free-tier Render instances sleep after ~15 minutes of inactivity.
Cold-start takes 30–60 seconds, which KILLS a live demo.

Run this script before the demo (or keep it running in the background)
to ping /health every 10 minutes so Render never sleeps.

Usage:
    python scripts/warm-render.py
    python scripts/warm-render.py --url https://your-app.onrender.com --interval 600
"""
import argparse
import time
import urllib.request
import urllib.error
from datetime import datetime


def ping(url: str) -> bool:
    try:
        with urllib.request.urlopen(f"{url.rstrip('/')}/health", timeout=15) as resp:
            body = resp.read().decode()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅  {resp.status} — {body[:80]}")
            return True
    except urllib.error.HTTPError as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  HTTP {e.code}")
        return False
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌  {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Keep Render instance warm before a demo.")
    parser.add_argument(
        "--url",
        default="https://rakshak-backend.vercel.app",
        help="Base URL of the deployed backend (default: Render production URL)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=600,
        help="Ping interval in seconds (default: 600 = 10 minutes)",
    )
    args = parser.parse_args()

    print(f"🔥 Warming {args.url} every {args.interval}s. Press Ctrl+C to stop.")
    print("-" * 60)

    # Immediate first ping to confirm the server is alive
    ping(args.url)

    while True:
        time.sleep(args.interval)
        ping(args.url)


if __name__ == "__main__":
    main()
