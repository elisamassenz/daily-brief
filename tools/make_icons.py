#!/usr/bin/env python3
"""Regenerate every app icon from one letter (macOS only: uses sips and iconutil).

  python3 tools/make_icons.py W           then open http://localhost:8799/tools/icon.html?letter=W
  python3 tools/make_icons.py --texture   then open http://localhost:8799/tools/texture.html
  python3 tools/make_icons.py --figma tools/src/icon-figma.png
                                          uses a full-bleed square exported from Figma for the web icons,
                                          then open http://localhost:8799/tools/mac-icon.html for the Mac app

The page draws the image in a browser (with the site's fonts) and posts it back here. This script then writes
static/favicon.png, static/icon.png, static/apple-touch-icon.png and, if present, the
Wallflower.app icon. It exits when done."""
import http.server
import os
import shutil
import subprocess
import sys
import tempfile
import threading

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
STATIC = os.path.join(ROOT, "static")
APP = os.path.join(ROOT, "Wallflower.app")


def sips(*args):
    subprocess.run(["sips", *args], check=True, stdout=subprocess.DEVNULL)


def make_icns(png):
    """Mac app icon from a 1024px rounded-square PNG."""
    if not os.path.isdir(APP):
        return
    tmp = tempfile.mkdtemp()
    iconset = os.path.join(tmp, "app.iconset")
    os.makedirs(iconset)
    for sz in (16, 32, 128, 256, 512):
        sips("-z", str(sz), str(sz), png, "--out", os.path.join(iconset, "icon_%dx%d.png" % (sz, sz)))
        sips("-z", str(sz * 2), str(sz * 2), png, "--out", os.path.join(iconset, "icon_%dx%d@2x.png" % (sz, sz)))
    icns = os.path.join(APP, "Contents", "Resources", "applet.icns")
    subprocess.run(["iconutil", "-c", "icns", iconset, "-o", icns], check=True)
    subprocess.run(["codesign", "--force", "--deep", "-s", "-", APP], stderr=subprocess.DEVNULL)
    os.utime(APP)


def from_square(png):
    """Web icons from a full-bleed 1024px square (e.g. exported from Figma): no cropping needed."""
    shutil.copy(png, os.path.join(STATIC, "icon.png"))
    sips("-z", "256", "256", png, "--out", os.path.join(STATIC, "favicon.png"))
    sips("-z", "180", "180", png, "--out", os.path.join(STATIC, "apple-touch-icon.png"))
    print("web icons written from", png)


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
        super().__init__(*a, directory=ROOT, **kw)

    def log_message(self, *a):
        pass

    def do_POST(self):
        data = self.rfile.read(int(self.headers["Content-Length"]))
        if "name=mac-icon.png" in self.path:   # rounded Mac icon built by tools/mac-icon.html
            path = os.path.join(tempfile.mkdtemp(), "mac.png")
            with open(path, "wb") as f:
                f.write(data)
            make_icns(path)
            print("mac app icon written")
        elif "name=" in self.path:   # texture.jpg, header-poppy.jpg, ...: saved into static/
            name = os.path.basename(self.path.split("name=", 1)[1].split("&")[0])
            with open(os.path.join(STATIC, name), "wb") as f:
                f.write(data)
            print(name, "written")
        else:
            path = os.path.join(tempfile.mkdtemp(), "icon_1024.png")
            with open(path, "wb") as f:
                f.write(data)
            make_all(path)
        self.send_response(200)
        self.end_headers()
        threading.Thread(target=self.server.shutdown).start()


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "W"
    if arg == "--figma":   # python3 tools/make_icons.py --figma tools/src/icon-figma.png
        from_square(sys.argv[2])
        arg = "--mac"
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 8799), Handler)
    page = {"--texture": "tools/texture.html", "--header": "tools/header.html", "--stem": "tools/stem.html",
            "--mac": "tools/mac-icon.html"}.get(arg, "tools/icon.html?letter=%s" % arg)
    print("open http://localhost:8799/%s" % page)
    srv.serve_forever()
