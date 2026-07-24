"""One-time bake: BRRI/IRRI AWD-suitability GeoTIFFs -> backend/data/awd_grid.json.

Run offline (needs rasterio, dev-only). Source rasters from
pdfs/.tif/BD_AWD_Suitability_Map.rar (BD_{Boro,Aman,Aus}_AWD_Suitability.tif), extracted
with `tar -xf BD_AWD_Suitability_Map.rar`. Rasters are UTM zone 46N (EPSG:32646); this
samples them onto a lat/lon grid (reprojecting each point) so runtime is pure Python.
Classes: 0 = not suitable .. 3 = highly suitable; other/-9999 = no data.

Usage:  python data_prep/bake_awd_grid.py /path/to/extracted/tifs
"""
import json
import sys
from pathlib import Path

import rasterio
from rasterio.warp import transform as warp_transform
from rasterio.crs import CRS

src = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/mapx")
out_path = Path(__file__).resolve().parent.parent / "data" / "awd_grid.json"
UTM = CRS.from_epsg(32646)
LEFT, RIGHT, BOTTOM, TOP, RES = 88.0, 92.72, 20.68, 26.72, 0.05


def _cls(v):
    iv = round(float(v))
    return iv if iv in (0, 1, 2, 3) else None


def main():
    W = int(round((RIGHT - LEFT) / RES))
    H = int(round((TOP - BOTTOM) / RES))
    lons, lats = [], []
    for r in range(H):
        for c in range(W):
            lons.append(LEFT + (c + 0.5) * RES)
            lats.append(TOP - (r + 0.5) * RES)
    xs, ys = warp_transform("EPSG:4326", UTM, lons, lats)
    pts = list(zip(xs, ys))
    out = {"meta": {"left": LEFT, "bottom": BOTTOM, "right": RIGHT, "top": TOP, "width": W, "height": H},
           "note": "AWD rice-irrigation suitability class per lat-lon cell, 0=not suitable..3=highly "
                   "suitable, from BRRI/IRRI BD_*_AWD_Suitability rasters (reprojected from UTM46N)."}
    for s in ["Boro", "Aman", "Aus"]:
        with rasterio.open(src / f"BD_{s}_AWD_Suitability.tif") as ds:
            vals = [_cls(v[0]) for v in ds.sample(pts)]
        out[s.lower()] = [vals[r * W:(r + 1) * W] for r in range(H)]
    json.dump(out, open(out_path, "w"))
    print(f"wrote {out_path} ({out_path.stat().st_size // 1024} KB, {W}x{H} grid)")


if __name__ == "__main__":
    main()
