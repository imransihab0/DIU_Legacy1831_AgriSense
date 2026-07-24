"""Soil-texture lookup from a farm's coordinates (geospatial grounding).

Samples the SRDI soil-texture map (clay/sand/silt %) at a lat/lon and classifies
it into a USDA texture class + the app's soil_type vocabulary. Lets the agent
AUTO-DETECT the farm's soil from its location instead of asking the farmer.

The heavy GeoTIFF work was done once (data_prep/bake_soil_grid.py using rasterio);
at runtime this is pure Python over a small baked JSON grid — no GDAL/rasterio dep.
"""
import json
from ..config import DATA_DIR

_GRID = json.loads((DATA_DIR / "soil_grid.json").read_text())
_M = _GRID["meta"]

# USDA texture class -> the app's 4-way soil_type vocabulary (matches crops.json)
_APP_SOIL = {
    "sand": "sandy loam", "loamy sand": "sandy loam", "sandy loam": "sandy loam",
    "loam": "loam", "silt loam": "loam", "silt": "loam",
    "clay loam": "clay loam", "silty clay loam": "clay loam", "sandy clay loam": "clay loam",
    "clay": "clay", "silty clay": "clay", "sandy clay": "clay",
}


def _usda_texture(sand: float, silt: float, clay: float) -> str:
    """Standard USDA soil texture triangle classification from sand/silt/clay %."""
    if silt + 1.5 * clay < 15:
        return "sand"
    if silt + 2 * clay < 30:
        return "loamy sand"
    if (7 <= clay < 20 and sand > 52 and silt + 2 * clay >= 30) or (clay < 7 and silt < 50):
        return "sandy loam"
    if 7 <= clay < 27 and 28 <= silt < 50 and sand <= 52:
        return "loam"
    if (silt >= 50 and 12 <= clay < 27) or (50 <= silt < 80 and clay < 12):
        return "silt loam"
    if silt >= 80 and clay < 12:
        return "silt"
    if 20 <= clay < 35 and silt < 28 and sand > 45:
        return "sandy clay loam"
    if 27 <= clay < 40 and 20 < sand <= 45:
        return "clay loam"
    if 27 <= clay < 40 and sand <= 20:
        return "silty clay loam"
    if clay >= 35 and sand > 45:
        return "sandy clay"
    if clay >= 40 and silt >= 40:
        return "silty clay"
    if clay >= 40 and sand <= 45:
        return "clay"
    return "loam"


def _cell(lat: float, lon: float):
    """Nearest grid cell (row, col) for a coordinate, or None if out of bounds."""
    if not (_M["left"] <= lon <= _M["right"] and _M["bottom"] <= lat <= _M["top"]):
        return None
    col = int((lon - _M["left"]) / (_M["right"] - _M["left"]) * _M["width"])
    row = int((_M["top"] - lat) / (_M["top"] - _M["bottom"]) * _M["height"])
    col = min(max(col, 0), _M["width"] - 1)
    row = min(max(row, 0), _M["height"] - 1)
    return row, col


def _nearest_valid(row: int, col: int):
    """Spiral out to the closest cell that has data (some cells are water/nodata)."""
    if _GRID["clay"][row][col] is not None:
        return row, col
    for rad in range(1, 8):
        for dr in range(-rad, rad + 1):
            for dc in range(-rad, rad + 1):
                r, c = row + dr, col + dc
                if 0 <= r < _M["height"] and 0 <= c < _M["width"] and _GRID["clay"][r][c] is not None:
                    return r, c
    return None


def lookup_soil_texture(latitude: float, longitude: float) -> dict:
    """Return the soil texture at a farm's coordinates, from the SRDI soil map."""
    rc = _cell(float(latitude), float(longitude))
    if rc is None:
        return {"error": "Coordinates are outside the Bangladesh soil map. Use the farmer-stated soil type."}
    rc = _nearest_valid(*rc)
    if rc is None:
        return {"error": "No soil data near these coordinates (likely water/coast). Ask the farmer."}
    row, col = rc
    clay, sand, silt = _GRID["clay"][row][col], _GRID["sand"][row][col], _GRID["silt"][row][col]
    total = (clay + sand + silt) or 1
    clay, sand, silt = clay / total * 100, sand / total * 100, silt / total * 100
    usda = _usda_texture(sand, silt, clay)
    return {
        "latitude": latitude, "longitude": longitude,
        "clay_pct": round(clay), "sand_pct": round(sand), "silt_pct": round(silt),
        "usda_texture": usda,
        "soil_type": _APP_SOIL[usda],
        "source": "SRDI soil-texture map (real geospatial data), nearest-cell lookup",
        "note": "Map-derived estimate for the location; if the farmer knows their actual soil, prefer that.",
    }
