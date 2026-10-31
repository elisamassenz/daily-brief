"""Clean cutout of an AI flower stem on a flat backdrop, for dark backgrounds.
Background = pixels near the backdrop color; warmth is weighted so neutral white petals
stay solid against the warm cream. Edges get a soft alpha and the backdrop color
is unmixed from them so no cream halo shows on dark cards.
Usage: python3 tools/cutout.py tools/src/stem-b-original.png static/support-bloom.png"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage

src, out = sys.argv[1], sys.argv[2]
im = np.asarray(Image.open(src).convert("RGB")).astype(np.float32)
H, W, _ = im.shape
border = np.concatenate([im[:4].reshape(-1, 3), im[-4:].reshape(-1, 3), im[:, :4].reshape(-1, 3), im[:, -4:].reshape(-1, 3)])
bg = np.median(border, axis=0)
# distance from the backdrop; warmth (R-B) counts triple, since the cream backdrop is warm
# and white petals, even in shadow, are neutral
sm = ndimage.median_filter(im, size=(3, 3, 1))
warm = (sm[..., 0] - sm[..., 2]) - (bg[0] - bg[2])
d = np.sqrt(((sm - bg) ** 2).sum(-1) + (3 * warm) ** 2)

# background = anything close to the backdrop, including the small gaps between buds and leaves
fg = d >= 12
# the AI render has light neutral halos hugging thin edges; they look like white petal.
# Light pixels only count as flower when they form a big patch (the anemone).
lum = sm.mean(-1)
light = fg & (lum > bg.mean() - 14) & (sm[..., 0] - sm[..., 2] < 30)   # neutral, not pale yellow
lab, n = ndimage.label(light)
if n:
    sizes = ndimage.sum(light, lab, range(1, n + 1))
    fg &= ~(light & ~np.isin(lab, 1 + np.flatnonzero(sizes >= 3000)))
fg = ndimage.binary_opening(fg, iterations=1)   # drop specks
lab, n = ndimage.label(fg)
sizes = ndimage.sum(fg, lab, range(1, n + 1))
fg = np.isin(lab, 1 + np.flatnonzero(sizes >= 40))   # drop stray islands

# soft edge (matting): in a thin ring around the shape, alpha is how far each pixel sits
# from the backdrop toward the nearest solid flower color. Light AI halos project
# backwards (away from the flower color) and drop out.
core = ndimage.binary_erosion(fg, iterations=2)
_, (iy, ix) = ndimage.distance_transform_edt(~core, return_indices=True)
feat = lambda x: np.dstack([x, 3 * ((x[..., 0] - x[..., 2]) - (bg[0] - bg[2]))[..., None]])
I, F = feat(im - bg), feat(sm[iy, ix] - bg)
proj = (I * F).sum(-1) / np.maximum((F * F).sum(-1), 1)
ring = ndimage.binary_dilation(fg, iterations=1) & ~core
alpha = core.astype(np.float32)
alpha[ring] = np.clip(proj[ring], 0, 1) ** 1.3
alpha = ndimage.gaussian_filter(alpha, 0.5)

# unmix the backdrop from semi-transparent edge pixels
a = np.clip(alpha, 1e-3, 1)[..., None]
rgb = np.clip((im - (1 - a) * bg) / a, 0, 255)
rgba = np.dstack([rgb, np.clip(alpha, 0, 1) * 255]).astype(np.uint8)
img = Image.fromarray(rgba)
img = img.crop(img.getbbox())
img.save(out, optimize=True)
print(out, img.size)
