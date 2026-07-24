"""One-time bake: SRDI soil-texture GeoTIFFs -> compact backend/data/soil_grid.json.

Run offline (needs rasterio, dev-only — NOT a runtime dependency). Source rasters
come from pdfs/.tif/BD_Soiltexture.rar (BD_Clay/BD_Sand/BD_Silt .tif), extracted with
`tar -xf BD_Soiltexture.rar` (macOS bsdtar reads RAR). Values are per-mille -> /10 = %.

Usage:
    uv pip install rasterio
    python data_prep/bake_soil_grid.py /path/to/extracted/tifs
"""
import json
import sys
from pathlib import Path

import rasterio
import numpy as np

src = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/mapx")
out_path = Path(__file__).resolve().parent.parent / "data" / "soil_grid.json"


def _cell(v, nd):
    return None if (not np.isfinite(v) or v == nd or v < 0 or v > 1001) else round(float(v) / 10.0)


def main():
    layers = {}
    meta = None
    for f in ["BD_Clay", "BD_Sand", "BD_Silt"]:
        with rasterio.open(src / f"{f}.tif") as ds:
            b = ds.bounds
            meta = {"left": b.left, "bottom": b.bottom, "right": b.right, "top": b.top,
                    "width": ds.width, "height": ds.height}
            layers[f] = (ds.read(1).astype("float32"), ds.nodata)
    H, W = meta["height"], meta["width"]
    nd = layers["BD_Clay"][1]
    out = {"meta": meta,
           "note": "Soil clay/sand/silt % on a lat-lon grid, baked from SRDI BD_Soiltexture rasters "
                   "(source values per-mille, /10 = %). Nearest-cell lookup at runtime (pure Python).",
           "clay": [], "sand": [], "silt": []}
    for r in range(H):
        out["clay"].append([_cell(layers["BD_Clay"][0][r, c], nd) for c in range(W)])
        out["sand"].append([_cell(layers["BD_Sand"][0][r, c], nd) for c in range(W)])
        out["silt"].append([_cell(layers["BD_Silt"][0][r, c], nd) for c in range(W)])
    json.dump(out, open(out_path, "w"))
    print(f"wrote {out_path} ({out_path.stat().st_size // 1024} KB, {W}x{H} grid)")


if __name__ == "__main__":
    main()
