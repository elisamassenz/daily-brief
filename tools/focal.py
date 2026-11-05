"""Find where the people are in each news photo, so the page crops to their faces.

Runs in build.py only (needs `pip install opencv-python-headless`; without it photos just stay center-cropped).
Results live in focal_cache.json as {image url: "x% y%"}, an object-position value; "" means no face found.
"""
import os
import urllib.request
from concurrent.futures import ThreadPoolExecutor

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None

MODEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "face_detection_yunet_2023mar.onnx")
MAX_SIDE = 640          # detection size; plenty for a face that matters in the crop
MIN_SCORE = 0.75
MAX_BYTES = 12 * 1024 * 1024


def download(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.read(MAX_BYTES)
    except Exception:
        return None


def focal_of(raw, detector):
    """object-position for one photo: the eye line of the main faces, or "" when there are none."""
    img = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return ""
    h, w = img.shape[:2]
    scale = min(1, MAX_SIDE / max(h, w))
    if scale < 1:
        img = cv2.resize(img, (round(w * scale), round(h * scale)), interpolation=cv2.INTER_AREA)
        h, w = img.shape[:2]
    detector.setInputSize((w, h))
    _, faces = detector.detect(img)
    if faces is None or not len(faces):
        return ""
    # Background faces shouldn't pull the crop: keep those near the size of the biggest one.
    biggest = max(f[2] * f[3] for f in faces)
    main = [f for f in faces if f[2] * f[3] >= biggest * 0.35]
    weight = sum(f[2] * f[3] for f in main)
    x = sum((f[4] + f[6]) / 2 * f[2] * f[3] for f in main) / weight / w   # f[4:8] = right eye x,y, left eye x,y
    y = sum((f[5] + f[7]) / 2 * f[2] * f[3] for f in main) / weight / h
    return "%d%% %d%%" % (round(min(max(x, 0), 1) * 100), round(min(max(y, 0), 1) * 100))


def update(urls, cache, limit=200):
    """Fill `cache` for any new urls, at most `limit` per run so a build stays quick. Returns how many were added."""
    if cv2 is None:
        return 0
    todo = [u for u in dict.fromkeys(urls) if u and u not in cache][:limit]
    if not todo:
        return 0
    detector = cv2.FaceDetectorYN.create(MODEL, "", (MAX_SIDE, MAX_SIDE), MIN_SCORE)
    added = 0
    with ThreadPoolExecutor(8) as ex:
        for url, raw in zip(todo, ex.map(download, todo)):
            if raw:   # a failed download is retried next run
                cache[url] = focal_of(raw, detector)
                added += 1
    return added
