#!/usr/bin/env python3
"""
Canvas Component Creation Bug Reproduction Script.

Sends failing canvas component creation requests (e.g. pitch_canvas with 4K resolution
or tactical pitch overlay) to trigger the texture allocation overflow bug.
This increments `canvas_component_creation_failures_total` in OpenTelemetry and
causes the `CanvasComponentCreationFailures` Prometheus / Grafana alert to fire,
which in turn triggers the on-call engineer dispatch loop (`poll_alerts.py`).

Usage:
    python3 on-call-engineer/reproduce_canvas_bug.py [--url http://127.0.0.1:8009] [--count 6] [--test-standard]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any


def send_json_request(url: str, method: str = "GET", payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    """Send HTTP request with JSON payload and return (status_code, response_dict)."""
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "reproduce-canvas-bug/1.0",
    }
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode("utf-8")
            return response.status, json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8")
        try:
            return e.code, json.loads(content) if content else {}
        except json.JSONDecodeError:
            return e.code, {"raw": content}


def run_reproduction(
    base_url: str,
    failure_count: int = 6,
    delay: float = 0.2,
    test_standard: bool = True,
) -> bool:
    """Execute reproduction sequence against the running backend."""
    base_url = base_url.rstrip("/")
    health_url = f"{base_url}/health"
    canvas_url = f"{base_url}/api/canvas/components"
    telemetry_url = f"{base_url}/api/telemetry"

    print("=" * 80)
    print("CANVAS COMPONENT CREATION BUG REPRODUCTION")
    print(f"Target Backend: {base_url}")
    print(f"Failure count target: {failure_count} (alert threshold: >5 in 5m)")
    print("=" * 80)

    # 1. Check backend health
    try:
        status, health_data = send_json_request(health_url)
        if status != 200:
            print(f"[ERROR] Health check failed with HTTP {status}: {health_data}")
            return False
        telemetry = health_data.get("telemetry", {})
        print(f"[OK] Backend healthy: service='{telemetry.get('service_name')}', env='{telemetry.get('environment')}', version='{telemetry.get('deployed_version')}'")
    except urllib.error.URLError as e:
        print(f"\n[ERROR] Unable to connect to backend at {base_url}: {e.reason}")
        print("Please ensure the backend is running:")
        print("    cd backend && uv run uvicorn app.main:app --host 127.0.0.1 --port 8009\n")
        return False

    # 2. Test standard component creation if requested
    if test_standard:
        print("\n--- Step 1: Testing Standard Canvas Component (Expected: 201 Created) ---")
        standard_payload = {
            "component_type": "scoreboard_canvas",
            "name": "Standard Scoreboard Canvas",
            "width": 800,
            "height": 600,
            "config": {
                "theme": "dark",
                "anti_aliasing": True,
            },
        }
        status, resp = send_json_request(canvas_url, method="POST", payload=standard_payload)
        if status == 201:
            print(f"[SUCCESS] Standard canvas component created: id={resp.get('id')}, type={resp.get('component_type')} (HTTP 201)")
        else:
            print(f"[WARN] Standard canvas creation returned unexpected status {status}: {resp}")

    # 3. Send buggy requests to trigger failure and metric emission
    print(f"\n--- Step 2: Triggering {failure_count} Buggy Pitch Canvas Requests (Expected: 500 Texture Overflow) ---")
    buggy_payload = {
        "component_type": "pitch_canvas",
        "name": "4K Ultra-HD Tactical Pitch Canvas",
        "width": 3840,
        "height": 2160,
        "config": {
            "texture_quality": "4k",
            "enable_tactical_overlay": True,
        },
    }

    success_failures = 0
    for i in range(1, failure_count + 1):
        status, resp = send_json_request(canvas_url, method="POST", payload=buggy_payload)
        detail = resp.get("detail", str(resp))
        if status == 500:
            success_failures += 1
            print(f"  [{i}/{failure_count}] HTTP 500 (Expected Bug Triggered): {detail}")
        else:
            print(f"  [{i}/{failure_count}] Unexpected HTTP {status}: {resp}")
        if delay > 0 and i < failure_count:
            time.sleep(delay)

    # 4. Check Telemetry / Metrics endpoint
    print("\n--- Step 3: Checking Telemetry Application Metrics ---")
    status, telem_data = send_json_request(telemetry_url)
    app_metrics = telem_data.get("application_metrics", {})
    canvas_failures = app_metrics.get("canvas_component_failures", 0)
    print(f"Current canvas_component_failures total: {canvas_failures}")

    print("\n" + "=" * 80)
    if success_failures >= 5:
        print("[SUCCESS] Alert Threshold Breached!")
        print(f"Generated {success_failures} failures (>5 in 5m threshold).")
        print("Observability Alert: 'CanvasComponentCreationFailures'")
        print("Metric Counter:      'canvas_component_creation_failures_total'")
        print("On-call Dispatcher:  'on-call-engineer/poll_alerts.py' will detect firing alert and dispatch headless agent.")
        print("=" * 80)
        return True
    else:
        print(f"[PARTIAL] Generated {success_failures} failures. Increase --count to > 5 to breach alert threshold.")
        print("=" * 80)
        return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Trigger reproducible canvas component creation bug to test observability alert and on-call dispatch.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--url",
        default=os.getenv("SCOREBOARD_API_URL", os.getenv("API_URL", "http://127.0.0.1:8009")),
        help="Base URL of the Sports League Scoreboard backend",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=6,
        help="Number of failing requests to trigger (>5 in 5m triggers CanvasComponentCreationFailures alert)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.2,
        help="Delay between requests in seconds",
    )
    parser.add_argument(
        "--no-test-standard",
        action="store_true",
        help="Skip testing the standard canvas creation request first",
    )
    args = parser.parse_args()

    success = run_reproduction(
        base_url=args.url,
        failure_count=args.count,
        delay=args.delay,
        test_standard=not args.no_test_standard,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
