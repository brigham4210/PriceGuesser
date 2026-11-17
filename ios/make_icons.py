"""Draw the PriceGuesser icon (from static/favicon.svg) as full-bleed PNGs for iOS.

Usage: python ios/make_icons.py ios/icons   (needs Pillow)
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

out = Path(sys.argv[1])
N = 1024
k = N / 64  # favicon units -> pixels

# Diagonal gradient #0B5FFF -> #00A6FB, full square (iOS rounds the corners itself).
img = Image.new("RGB", (N, N))
a, b = (0x0B, 0x5F, 0xFF), (0x00, 0xA6, 0xFB)
px = img.load()
for y in range(N):
    for x in range(N):
        t = (x + y) / (2 * (N - 1))
        px[x, y] = tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))

d = ImageDraw.Draw(img)
# Scale the art up a little around the centre so it fills the icon.
s, cx = 1.15, 32


def P(x, y):
    return ((cx + (x - cx) * s) * k, (cx + (y - cx) * s) * k)


w = round(5 * s * k)
pts = [P(12, 31), P(32, 14), P(52, 31)]
d.line(pts, fill="white", width=w, joint="curve")
for p in (pts[0], pts[2]):
    d.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2], fill="white")
d.rounded_rectangle([*P(18, 30), *P(46, 50)], radius=3 * s * k, fill="white")
d.rounded_rectangle([*P(29, 37), *P(35, 50)], radius=1.5 * s * k, fill=(0x0B, 0x5F, 0xFF))
(x0, y0), (x1, y1) = P(35, 14), P(51, 30)
d.ellipse([x0, y0, x1, y1], fill=(0xFF, 0xD1, 0x66))
font = ImageFont.load_default(size=round(11 * s * k))
d.text(((x0 + x1) / 2, (y0 + y1) / 2), "$", font=font, fill=(0x1F, 0x29, 0x37), anchor="mm")

for size in (20, 29, 40, 58, 60, 76, 80, 87, 120, 152, 167, 180, 640, 1024, 1280, 1920):
    img.resize((size, size), Image.LANCZOS).save(out / f"priceguesser-{size}.png", optimize=True)
