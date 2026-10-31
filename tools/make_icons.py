#!/usr/bin/env python3
"""Regenerate every app icon from one letter (macOS only: uses sips and iconutil).

  python3 tools/make_icons.py W

Serves tools/icon.html on http://localhost:8799/icon.html?letter=W. Open that page in a browser;
it draws the icon with the site's fonts and posts it back here. This script then writes
static/favicon.png, static/icon.png, static/apple-touch-icon.png and, if present, the
Wallflower.app icon. It exits when done."""
import http.server
import os
import shutil
import subprocess
import sys
import tempfile

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
STATIC = os.path.join(ROOT, "static")
APP = os.path.join(ROOT, "Wallflower.app")


def sips(*args):
    subprocess.run(["sips", *args], check=True, stdout=subprocess.DEVNULL)


def make_all(png):
    tmp = tempfile.mkdtemp()
    shutil.copy(png, os.path.join(STATIC, "icon.png"))
    sips("-z", "256", "256", png, "--out", os.path.join(STATIC, "favicon.png"))
    # iOS masks its own corners, so the Home Screen icon is a full-bleed crop inside the rounded square
    crop = os.path.join(tmp, "crop.png")
    sips("--cropToHeightWidth", "704", "704", "--cropOffset", "160", "160", png, "--out", crop)
    sips("-z", "180", "180", crop, "--out", os.path.join(STATIC, "apple-touch-icon.png"))
    if os.path.isdir(APP):
        iconset = os.path.join(tmp, "app.iconset")
        os.makedirs(iconset)
        for sz in (16, 32, 128, 256, 512):
            sips("-z", str(sz), str(sz), png, "--out", os.path.join(iconset, "icon_%dx%d.png" % (sz, sz)))
            sips("-z", str(sz * 2), str(sz * 2), png, "--out", os.path.join(iconset, "icon_%dx%d@2x.png" % (sz, sz)))
        icns = os.path.join(APP, "Contents", "Resources", "applet.icns")
        subprocess.run(["iconutil", "-c", "icns", iconset, "-o", icns], check=True)
        subprocess.run(["codesign", "--force", "--deep", "-s", "-", APP], stderr=subprocess.DEVNULL)
        os.utime(APP)
    print("icons written")


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=TOOLS, **kw)

    def log_message(self, *a):
        pass

    def do_POST(self):
        data = self.rfile.read(int(self.headers["Content-Length"]))
        path = os.path.join(tempfile.mkdtemp(), "icon_1024.png")
        with open(path, "wb") as f:
            f.write(data)
        make_all(path)
        self.send_response(200)
        self.end_headers()
        self.server.done = True


if __name__ == "__main__":
    letter = sys.argv[1] if len(sys.argv) > 1 else "W"
    srv = http.server.HTTPServer(("127.0.0.1", 8799), Handler)
    srv.done = False
    print("open http://localhost:8799/icon.html?letter=%s" % letter)
    while not srv.done:
        srv.handle_request()
