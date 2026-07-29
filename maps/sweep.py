#!/usr/bin/env python3
"""Generate a contact sheet of candidate worlds so one can be chosen by eye."""

import itertools
import numpy as np
from PIL import Image, ImageDraw
import generate_world as G

G.set_resolution(1000)

COMBOS = list(itertools.product(
    [21, 44, 77, 108],          # seeds
    [1.15, 1.45],               # separation
    [0.070, 0.100],             # platform scale
))

COLS, THUMB_W = 4, 700
tiles, labels = [], []

for seed, sep, pscale in COMBOS:
    z, lost = G.build(seed, land_fraction=0.25, warp=0.035, rift=0.5,
                      impact_lat=8.0, impact_lon=-150.0,
                      platform=3800, platform_scale=pscale,
                      separation=sep, lost_continent=True, lost_rank=1)

    land = z >= 0
    lab, n = G.ndimage.label(land, structure=np.ones((3, 3)))
    sizes = np.sort(np.bincount(lab.ravel())[1:])[::-1]
    total = sizes.sum()
    gap = G.ndimage.distance_transform_edt(~land).max() / G.W * 360
    conts = (sizes > total * 0.04).sum()
    top = 100 * sizes[0] / total

    img = G.render_colour(z).resize((THUMB_W, THUMB_W // 2), Image.LANCZOS)
    tiles.append(img)
    labels.append(f"s{seed} sep{sep} pl{pscale}  |  {conts} cont, "
                  f"biggest {top:.0f}%, gap {gap:.0f}deg")
    print(labels[-1], flush=True)

    G.render_heightmap(z).save(f"cand_s{seed}_sep{sep}_pl{pscale}_height.png")
    img.save(f"cand_s{seed}_sep{sep}_pl{pscale}.png")

rows = (len(tiles) + COLS - 1) // COLS
TH = THUMB_W // 2
sheet = Image.new("RGB", (COLS * THUMB_W, rows * (TH + 22)), (18, 18, 22))
d = ImageDraw.Draw(sheet)
for i, (t, cap) in enumerate(zip(tiles, labels)):
    x, y = (i % COLS) * THUMB_W, (i // COLS) * (TH + 22)
    sheet.paste(t, (x, y))
    d.text((x + 6, y + TH + 5), cap, fill=(225, 225, 215))
sheet.save("contact_sheet.png")
print("wrote contact_sheet.png")
