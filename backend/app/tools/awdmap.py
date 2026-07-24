"""AWD (Alternate Wetting & Drying) irrigation-suitability lookup by location.

Tells a rice farmer whether the water-saving AWD method suits their field, from the
BRRI/IRRI AWD suitability maps. AWD lets the paddy dry a few cm below the surface
between irrigations instead of continuous flooding — saving ~25-30% irrigation water
(and cost) with no yield loss, WHERE the soil/water table allow it.

Heavy GeoTIFF + reprojection (UTM46N -> lat/lon) was done once in
data_prep/bake_awd_grid.py; runtime here is pure Python over a small baked JSON.
"""
import json
from ..config import DATA_DIR

_GRID = json.loads((DATA_DIR / "awd_grid.json").read_text())
_M = _GRID["meta"]

_LABELS = {3: "highly suitable", 2: "moderately suitable", 1: "marginally suitable", 0: "not suitable"}
_SEASONS = ("boro", "aman", "aus")


def _season(s: str | None) -> str:
    s = (s or "boro").lower().strip().replace("_rice", "").replace(" ", "")
    for k in _SEASONS:
        if k in s:
            return k
    return "boro"  # most irrigation-intensive rice season -> biggest AWD benefit


def _cell(lat, lon):
    if not (_M["left"] <= lon <= _M["right"] and _M["bottom"] <= lat <= _M["top"]):
        return None
    col = int((lon - _M["left"]) / (_M["right"] - _M["left"]) * _M["width"])
    row = int((_M["top"] - lat) / (_M["top"] - _M["bottom"]) * _M["height"])
    return min(max(row, 0), _M["height"] - 1), min(max(col, 0), _M["width"] - 1)


def _nearest_valid(grid, row, col):
    if grid[row][col] is not None:
        return grid[row][col]
    for rad in range(1, 10):
        for dr in range(-rad, rad + 1):
            for dc in range(-rad, rad + 1):
                r, c = row + dr, col + dc
                if 0 <= r < _M["height"] and 0 <= c < _M["width"] and grid[r][c] is not None:
                    return grid[r][c]
    return None


def lookup_awd_suitability(latitude: float, longitude: float, season: str = "boro") -> dict:
    """AWD irrigation suitability for a farm's coordinates and rice season."""
    rc = _cell(float(latitude), float(longitude))
    if rc is None:
        return {"error": "Coordinates are outside the Bangladesh AWD map."}
    seas = _season(season)
    cls = _nearest_valid(_GRID[seas], *rc)
    if cls is None:
        return {"season": seas, "suitability": "unknown",
                "note": "No AWD rating near these coordinates (not a mapped rice area). Give generic water advice."}
    suitable = cls >= 2
    return {
        "season": seas,
        "suitability_class": cls,
        "suitability": _LABELS[cls],
        "awd_recommended": suitable,
        "est_irrigation_saving": "~25-30% less irrigation water and pumping cost vs continuous flooding" if suitable
        else ("possible with careful monitoring" if cls == 1 else "not advised — keep continuous flooding here"),
        "how": "Let the water drop to ~15 cm below the soil (use a perforated field tube to watch it), then "
        "re-flood to ~5 cm; keep flooded during flowering." if cls >= 1 else None,
        "source": "BRRI/IRRI AWD suitability map (real geospatial data), nearest-cell lookup",
        "note": "Map-based suitability for the location; combine with compute_financials to show the taka saved on this crop's irrigation cost.",
    }
