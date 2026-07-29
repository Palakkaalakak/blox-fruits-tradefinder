#!/usr/bin/env python3
"""Generate a contact sheet of candidate worlds so one can be chosen by eye."""

import sys
import numpy as np
from PIL import Image, ImageDraw
import generate_world as G

G.set_resolution(int(sys.argv[1]) if len(sys.argv) > 1 else 1100)

# Pole-shift rotations. Alpha is the longitudinal spin; beta tilts the axis,
# which is what actually moves land between tropics and poles.
ROTS = {
    "A": (121.0, 47.0, 29.0),
    "B": (121.0, 78.0, 12.0),
    "C": ( 37.0, 62.0, 71.0),
    "D": (203.0, 35.0, 55.0),
}

COMBOS = [(seed, rk, sep)
          for seed in (5, 44, 91)
          for rk in ("A", "B", "C", "D")
          for sep in (1.30,)]

COLS, THUMB_W = 4, 720
tiles, labels, best = [], [], []

for seed, rk, sep in COMBOS:
    z, lost = G.build(seed, land_fraction=0.25, warp=0.038, rift=0.6,
                      impact_lat=8.0, impact_lon=-150.0,
                      platform=3800, platform_scale=0.072,
                      separation=sep, lost_continent=True, lost_rank=1,
                      rotation=ROTS[rk], hotspots=7, mountains=1.0)

    land = z >= 0
    lab, n = G.ndimage.label(land, structure=np.ones((3, 3)))
    sizes = np.sort(np.bincount(lab.ravel())[1:])[::-1]
    total = sizes.sum()
    gap = G.ndimage.distance_transform_edt(~land).max() / G.W * 360
    conts = int((sizes > total * 0.04).sum())
    top = 100 * sizes[0] / total

    tag = f"s{seed}-rot{rk}"
    img = G.render_colour(z).resize((THUMB_W, THUMB_W // 2), Image.LANCZOS)
    tiles.append(img)
    labels.append(f"{tag}  |  {conts} cont, biggest {top:.0f}%, gap {gap:.0f}deg, "
                  f"{int((sizes < total*0.001).sum())} isles")
    best.append((top, tag, conts))
    print(labels[-1], flush=True)

    G.render_heightmap(z).save(f"cand_{tag}_height.png")
    img.save(f"cand_{tag}.png")

rows = (len(tiles) + COLS - 1) // COLS
TH = THUMB_W // 2
sheet = Image.new("RGB", (COLS * THUMB_W, rows * (TH + 22)), (18, 18, 22))
d = ImageDraw.Draw(sheet)
for i, (t, cap) in enumerate(zip(tiles, labels)):
    x, y = (i % COLS) * THUMB_W, (i // COLS) * (TH + 22)
    sheet.paste(t, (x, y))
    d.text((x + 6, y + TH + 5), cap, fill=(225, 225, 215))
sheet.save("contact_sheet.png")

print("\nmost balanced (lowest share held by largest landmass):")
for top, tag, conts in sorted(best)[:5]:
    print(f"  {tag}: biggest {top:.0f}%, {conts} continents")
print("wrote contact_sheet.png")
