from tira_scraper.quantity import extract_quantities, normalize_primary


def test_basic_ml():
    assert extract_quantities("Azzaro Forever Wanted 100ml") == ["100ml"]


def test_rejects_year_gram_bug():
    # The DDF bug: "2026g" is the year 2026, not a 2026-gram product.
    out = extract_quantities("50ml © 2026 some footer 2026g")
    assert out == ["50ml"]
    assert "2026g" not in out


def test_unit_normalization():
    assert extract_quantities("50 ML") == ["50ml"]
    assert extract_quantities("200 GM compact") == ["200g"]
    assert extract_quantities("1.5 L bottle") == ["1.5l"]


def test_dedup_and_order():
    assert extract_quantities("50ml 50ml 100ml") == ["50ml", "100ml"]


def test_pack_of():
    assert "pack of 2" in extract_quantities("Lipstick set pack of 2")


def test_implausible_rejected():
    assert extract_quantities("99999ml") == []


def test_primary_prefers_selected():
    found = ["50ml", "100ml"]
    assert normalize_primary(found, preferred="100 ml") == "100ml"
    assert normalize_primary(found) == "50ml"
    assert normalize_primary([]) is None
