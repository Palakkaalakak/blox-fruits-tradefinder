#!/usr/bin/env python3
"""Compare densities of the Drowned Fractures at a fixed seed."""

import numpy as np
from PIL import Image, ImageDraw
import generate_world as G

G.set_resolution(1500)

VARIANTS = [
    ("sparse",   0.45, 15.0, 0.32),
    ("moderate", 0.75, 15.0, 0.34),
    ("crazed",   1.05, 15.0, 0.36),
    ("shattered", 1.35, 13.0, 0.38),
]

COLS, TW = 2, 1180
tiles, labels = [], []

for name, craze, sharp, land in VARIANTS:
    z, lost = G.build(44, land_fraction=land, warp=0.038, rift=0.4,
                      impact_lat=-46.0, impact_lon=-150.0,
                      platform=3800, platform_scale=0.072, separation=1.0,
                      lost_continent=True, lost_rank=1,
                      rotation=(203.0, 35.0, 55.0), hotspots=6, mountains=1.0,
                      fractures=3, fracture_width=0.019, seas=3,
                      sunder=False, sunder_width=0.0045,
                      crazing=craze, crazing_scales=5, crazing_sharp=sharp)

    ld = z >= 0
    lab, n = G.ndimage.label(ld, structure=np.ones((3, 3)))
    sizes = np.sort(np.bincount(lab.ravel())[1:])[::-1]
    tot = sizes.sum()

    # how much coastline per unit land — the signature of a crazed continent
    edge = ld ^ G.ndimage.binary_erosion(ld)
    coast_ratio = edge.sum() / max(tot, 1) * 100

    img = G.render_colour(z).resize((TW, TW // 2), Image.LANCZOS)
    tiles.append(img)
    labels.append(f"{name} (crazing {craze}, land {land})  |  biggest {100*sizes[0]/tot:.0f}%, "
                  f"{int((sizes > tot*0.04).sum())} cont, coast/land {coast_ratio:.1f}")
    print(labels[-1], flush=True)
    img.save(f"craze_{name}.png")
    G.render_heightmap(z).save(f"craze_{name}_height.png")

rows = (len(tiles) + COLS - 1) // COLS
TH = TW // 2
sheet = Image.new("RGB", (COLS * TW, rows * (TH + 22)), (18, 18, 22))
d = ImageDraw.Draw(sheet)
for i, (t, cap) in enumerate(zip(tiles, labels)):
    x, y = (i % COLS) * TW, (i // COLS) * (TH + 22)
    sheet.paste(t, (x, y))
    d.text((x + 6, y + TH + 5), cap, fill=(230, 230, 220))
sheet.save("crazing_comparison.png")
print("wrote crazing_comparison.png")
