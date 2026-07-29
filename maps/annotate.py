#!/usr/bin/env python3
"""Render a candidate world with the Marreni marked and a latitude grid, so
the impact basin's position can be confirmed at a glance."""

import sys
import numpy as np
from PIL import Image, ImageDraw
import generate_world as G

WIDTH = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
CELLS = int(sys.argv[2]) if len(sys.argv) > 2 else 120
IMPACT_LAT, IMPACT_LON = -48.0, 0.0

G.set_resolution(WIDTH)
z, lost = G.build(44, land_fraction=0.40, warp=0.038, rift=0.4,
                  impact_lat=IMPACT_LAT, impact_lon=IMPACT_LON,
                  platform=3800, platform_scale=0.072, separation=1.0,
                  lost_continent=True, lost_rank=1,
                  rotation=(203.0, 35.0, 55.0), hotspots=5, mountains=1.0,
                  fractures=2, seas=3, sunder=False,
                  crazing=1.0, crazing_scales=3, crazing_cells=CELLS)

img = G.render_colour(z).convert("RGB")
W, H = img.size
d = ImageDraw.Draw(img, "RGBA")

# latitude grid
for lat, style in [(60, 1), (30, 1), (0, 2), (-30, 1), (-60, 1)]:
    y = int((90 - lat) / 180 * H)
    d.line([(0, y), (W, y)], fill=(255, 255, 255, 70), width=style)
    d.text((8, y + 3), f"{lat}°" + (" (equator)" if lat == 0 else ""),
           fill=(255, 255, 255, 180))

# hemisphere labels
d.text((W // 2 - 30, 10), "NORTH", fill=(255, 255, 255, 200))
d.text((W // 2 - 30, H - 22), "SOUTH", fill=(255, 255, 255, 200))
d.text((10, H // 2), "WEST", fill=(255, 255, 255, 200))
d.text((W - 50, H // 2), "EAST", fill=(255, 255, 255, 200))

# the Marreni
cy = int((90 - IMPACT_LAT) / 180 * H)
cx = int((IMPACT_LON + 180) / 360 * W)
r = int(W * 0.055)
d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 90, 90, 255), width=3)
d.line([(cx - r * 1.4, cy), (cx + r * 1.4, cy)], fill=(255, 90, 90, 200), width=2)
d.line([(cx, cy - r * 1.4), (cx, cy + r * 1.4)], fill=(255, 90, 90, 200), width=2)
d.text((cx + r + 8, cy - 8), f"MARRENI SEA  ({abs(IMPACT_LAT):.0f}°S)",
       fill=(255, 120, 120, 255))

img.save("annotated_world.png")

# report
sm = G.ndimage.gaussian_filter(z, 6, mode=("nearest", "wrap"))
patch = sm[max(cy - r, 0):cy + r, max(cx - r, 0):cx + r]
wide = sm[max(cy - 3 * r, 0):cy + 3 * r, max(cx - 3 * r, 0):cx + 3 * r]
print(f"Marreni centre  : {abs(IMPACT_LAT):.0f}S, {abs(IMPACT_LON):.0f}  "
      f"-> {100*cy/H:.0f}% down the map, {100*cx/W:.0f}% across")
print(f"basin depth     : {patch.mean():.0f} m   (surrounding {wide.mean():.0f} m)")
print("wrote annotated_world.png")
