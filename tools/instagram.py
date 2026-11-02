#!/usr/bin/env python3
"""Render the Instagram carousel (static/ig.html) to JPEGs.

  python3 tools/instagram.py http://localhost:8787 OUT_DIR

Needs Playwright (pip install playwright && playwright install chromium). Writes slide-1.jpg … and caption.txt."""
import os
import sys

from playwright.sync_api import sync_playwright


def render(base, out):
    os.makedirs(out, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=1)
        page.goto(base.rstrip("/") + "/ig.html", wait_until="networkidle")
        page.wait_for_selector("body[data-ready]", timeout=30000)
        files = []
        for i, slide in enumerate(page.query_selector_all(".slide"), 1):
            path = os.path.join(out, "slide-%d.jpg" % i)
            slide.screenshot(path=path, type="jpeg", quality=92)
            files.append(path)
        with open(os.path.join(out, "caption.txt"), "w") as f:
            f.write(page.evaluate("window.CAPTION"))
        browser.close()
    return files


if __name__ == "__main__":
    print("\n".join(render(sys.argv[1], sys.argv[2])))
