"""Tests for the soil-texture map lookup (geospatial grounding)."""
from app.tools.soilmap import lookup_soil_texture as st, _usda_texture, _APP_SOIL


def test_bogura_returns_valid_soil():
    r = st(24.85, 89.37)
    assert "error" not in r
    assert r["soil_type"] in ("clay", "clay loam", "loam", "sandy loam")
    assert 0 <= r["clay_pct"] <= 100 and 0 <= r["sand_pct"] <= 100


def test_percentages_roughly_sum_100():
    r = st(24.85, 89.37)
    assert 95 <= r["clay_pct"] + r["sand_pct"] + r["silt_pct"] <= 105


def test_out_of_bounds_errors():
    assert "error" in st(10.0, 10.0)       # far outside Bangladesh
    assert "error" in st(48.0, 2.0)        # Paris


def test_usda_classification_endpoints():
    assert _usda_texture(90, 5, 5) in ("sand", "loamy sand")   # very sandy
    assert _usda_texture(20, 20, 60) in ("clay", "silty clay") # very clayey
    assert _usda_texture(40, 40, 20) in ("loam", "clay loam")  # balanced-ish


def test_every_usda_class_maps_to_an_app_soil_type():
    for usda, app in _APP_SOIL.items():
        assert app in ("clay", "clay loam", "loam", "sandy loam")


def test_multiple_districts_classify():
    for lat, lon in [(22.70, 90.37), (25.74, 89.27), (23.46, 91.18)]:
        r = st(lat, lon)
        assert "error" not in r and r["soil_type"]
