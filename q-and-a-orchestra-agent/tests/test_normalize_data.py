
import pytest
from scripts.normalize_data import normalize_city

def test_normalize_city_uppercase():
    assert normalize_city("EDMONTON") == "Edmonton"

def test_normalize_city_lowercase():
    assert normalize_city("calgary") == "Calgary"

def test_normalize_city_mixedcase():
    assert normalize_city("Red DEER") == "Red Deer"

def test_normalize_city_whitespace():
    assert normalize_city("  Edmonton  ") == "Edmonton"

def test_normalize_city_empty():
    assert normalize_city("") == ""

def test_normalize_city_none():
    # The function expects string, but in python runtime None might be passed.
    # The implementation `if not city:` handles None safely if typed implicitly,
    # but let's check if it raises or returns empty string.
    # Looking at implementation: `if not city: return ""` handles None.
    assert normalize_city(None) == ""
