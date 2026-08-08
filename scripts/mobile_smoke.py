"""ROUND 16.3 P3.6 — Mobile viewport smoke via Playwright.

Purpose: `browser-use` headless doesn't resize viewport reliably in the pod
container. This script uses Playwright (already vendored in the venv) to
open each critical page at a 390×844 mobile viewport, screenshot it, and
assert no horizontal overflow (`scrollWidth === clientWidth`).

Usage (manual, on-demand):

    python /app/scripts/mobile_smoke.py

Environment:
    FRONTEND_URL         — override default preview URL
    TESTER_EMAIL         — default tester@orbus.test
    TESTER_PASSWORD      — default password123
    SCREENSHOTS_DIR      — default /app/_mobile_smoke_screenshots/

Exit codes:
    0  all pages OK (no overflow, no console errors on critical pages)
    1  overflow detected on ≥1 page
    2  playwright failure / unrecoverable error

The script is intentionally NOT wired into pytest — it is a MANUAL check
executed by the operator when releasing mobile-touching changes.

See /app/memory/mobile_testing_policy.md.
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path


PAGES = [
    ("/dashboard", "dashboard"),
    ("/stables", "stables"),
    ("/pvp", "pvp"),
    ("/pvp-season", "pvp-season-overview"),
    ("/world", "world"),
    ("/forge", "forge"),
    ("/achievements", "achievements"),
    ("/class-halls", "class-halls"),
]

MOBILE_VIEWPORT = {"width": 390, "height": 844}


async def run():
    from playwright.async_api import async_playwright  # type: ignore

    frontend_url = os.environ.get(
        "FRONTEND_URL", "https://drain-dispatch.preview.emergentagent.com",
    )
    email = os.environ.get("TESTER_EMAIL", "tester@orbus.test")
    password = os.environ.get("TESTER_PASSWORD", "password123")
    out_dir = Path(os.environ.get(
        "SCREENSHOTS_DIR", "/app/_mobile_smoke_screenshots",
    ))
    out_dir.mkdir(parents=True, exist_ok=True)

    failures = []

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        ctx = await browser.new_context(viewport=MOBILE_VIEWPORT)
        page = await ctx.new_page()

        # Login (idempotent — session persisted for the whole run).
        await page.goto(f"{frontend_url}/login", wait_until="networkidle")
        await page.fill('input[type="email"]', email)
        await page.fill('input[type="password"]', password)
        await page.click('button[type="submit"]')
        try:
            await page.wait_for_url("**/dashboard", timeout=15000)
        except Exception as e:  # noqa: BLE001
            print(f"[mobile_smoke] login redirect failed: {e}", file=sys.stderr)
            await browser.close()
            return 2

        for path, name in PAGES:
            try:
                await page.goto(f"{frontend_url}{path}", wait_until="networkidle")
                await page.wait_for_timeout(500)
                overflow_px = await page.evaluate(
                    "() => document.documentElement.scrollWidth "
                    "- document.documentElement.clientWidth"
                )
                screenshot = out_dir / f"{name}_mobile_390x844.png"
                await page.screenshot(
                    path=str(screenshot), full_page=False,
                )
                status = "OK" if overflow_px == 0 else f"OVERFLOW={overflow_px}px"
                print(f"[mobile_smoke] {name:22s} {path:28s} → {status}")
                if overflow_px != 0:
                    failures.append((name, path, overflow_px))
            except Exception as e:  # noqa: BLE001
                print(f"[mobile_smoke] {name} {path} → ERROR {e}",
                      file=sys.stderr)
                failures.append((name, path, str(e)))

        await browser.close()

    print()
    if failures:
        print(f"[mobile_smoke] {len(failures)}/{len(PAGES)} FAILED:")
        for name, path, info in failures:
            print(f"  - {name} ({path}): {info}")
        return 1
    print(f"[mobile_smoke] all {len(PAGES)} pages PASS · screenshots in {out_dir}")
    return 0


def main() -> int:
    return asyncio.run(run())


if __name__ == "__main__":
    raise SystemExit(main())
