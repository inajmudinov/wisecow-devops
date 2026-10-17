#!/usr/bin/env python3
"""Check HTTP status and report availability across sampled requests."""
import argparse
import datetime
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request


def main():
    parser = argparse.ArgumentParser(description="Application health checker")
    parser.add_argument("url")
    parser.add_argument("--checks", type=int, default=1)
    parser.add_argument("--interval", type=float, default=5)
    parser.add_argument("--timeout", type=float, default=10)
    parser.add_argument("--expected-status", type=int, default=200)
    parser.add_argument("--ca-cert")
    args = parser.parse_args()

    url = urllib.parse.urlsplit(args.url)
    if url.scheme not in ("http", "https") or not url.hostname:
        parser.error("Provide a valid HTTP or HTTPS URL")
    if args.checks < 1 or args.interval < 0 or args.timeout <= 0:
        parser.error("checks >= 1, interval >= 0, timeout > 0 required")
    if not 100 <= args.expected_status <= 599:
        parser.error("expected-status must be between 100 and 599")

    try:
        context = ssl.create_default_context(cafile=args.ca_cert)
    except (OSError, ssl.SSLError) as error:
        print(f"Configuration error: {error}")
        return 2

    healthy = 0
    started = time.monotonic()
    for index in range(args.checks):
        timestamp = datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat(timespec="seconds")
        before = time.monotonic()
        code = None
        reason = ""
        try:
            request = urllib.request.Request(
                args.url, headers={"User-Agent": "Wisecow-Health-Checker"}
            )
            with urllib.request.urlopen(
                request, timeout=args.timeout, context=context
            ) as response:
                code = response.status
        except urllib.error.HTTPError as error:
            code = error.code
            error.close()
        except (urllib.error.URLError, OSError, ValueError) as error:
            reason = str(error)

        elapsed = (time.monotonic() - before) * 1000
        up = code == args.expected_status
        healthy += int(up)
        state = "UP" if up else "DOWN"
        detail = f"HTTP {code}" if code is not None else reason
        print(
            f"{timestamp} {state} {detail} response_ms={elapsed:.1f}",
            flush=True
        )
        if index < args.checks - 1:
            time.sleep(args.interval)

    duration = time.monotonic() - started
    print(
        f"Summary: healthy={healthy}/{args.checks}, "
        f"observed_availability={100 * healthy / args.checks:.1f}%, "
        f"observation_seconds={duration:.1f}"
    )
    return 0 if healthy == args.checks else 1


raise SystemExit(main())
