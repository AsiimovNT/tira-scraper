from tira_scraper.price import parse_price


def test_rupee_with_commas():
    assert parse_price("₹10,560") == ("₹10,560", 10560)


def test_decimal():
    disp, num = parse_price("₹1,299.50")
    assert num == 1299.5


def test_none_when_empty():
    assert parse_price("") == (None, None)
    assert parse_price(None) == (None, None)
    assert parse_price("Price unavailable") == (None, None)
