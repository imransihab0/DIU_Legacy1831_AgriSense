"""Tests for the AWD irrigation-suitability map lookup (geospatial grounding)."""
from app.tools.awdmap import lookup_awd_suitability as awd, _season, _LABELS


def test_known_districts_return_a_class():
    for lat, lon in [(24.85, 89.37), (25.74, 89.27), (24.90, 91.87)]:
        r = awd(lat, lon, "boro")
        assert "error" not in r
        assert r["suitability"] in _LABELS.values() or r["suitability"] == "unknown"


def test_recommended_only_when_class_2_or_3():
    for lat, lon in [(24.85, 89.37), (23.46, 91.18), (22.70, 90.37), (24.90, 91.87)]:
        r = awd(lat, lon, "boro")
        if "suitability_class" in r:
            assert r["awd_recommended"] == (r["suitability_class"] >= 2)


def test_out_of_bounds_errors():
    assert "error" in awd(10.0, 10.0)


def test_season_normalization():
    assert _season("boro_rice") == "boro"
    assert _season("Aman") == "aman"
    assert _season(None) == "boro"
    assert _season("weird") == "boro"


def test_seasons_can_differ_for_same_point():
    b = awd(24.85, 89.37, "boro")
    a = awd(24.85, 89.37, "aman")
    assert "error" not in b and "error" not in a  # both resolvable
