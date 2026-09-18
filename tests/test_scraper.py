from pathlib import Path
from self_healing_scraper import scrape, Product

HTML_ORIGINAL = """
<h1 class="product-title">Mechanical Keyboard</h1>
<span class="price">$129.00</span>
"""
HTML_REDESIGNED = """
<h1 class="pdp__name">Mechanical Keyboard</h1>
<span data-testid="price">$129.00</span>
"""


def fake_healer(field, hint, html):
    return {
        "title": {"value": "Mechanical Keyboard", "selector": "h1.pdp__name"},
        "price": {"value": "$129.00", "selector": "span[data-testid='price']"},
    }[field]


def setup_function():
    Path("selectors.json").unlink(missing_ok=True)


def test_fast_path_needs_no_healer():
    # Default selectors match, so the healer must never be called.
    def exploding(*_):
        raise AssertionError("healer ran on the fast path")
    assert scrape(HTML_ORIGINAL, exploding) == Product(title="Mechanical Keyboard", price=129.0)


def test_heals_then_reuses_saved_selector():
    healed = scrape(HTML_REDESIGNED, fake_healer)     # breaks -> heals -> saves
    assert healed.price == 129.0

    # Loop is closed only if the second call skips the LLM entirely.
    def exploding(*_):
        raise AssertionError("healer ran, but selectors were already healed")
    reused = scrape(HTML_REDESIGNED, exploding)
    assert reused.price == 129.0
