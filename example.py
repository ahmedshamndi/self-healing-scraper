"""Runnable demo — no API key required.

Shows the full lifecycle with a fake healer so you can run it immediately:
    python example.py

To use a real LLM, see the commented block at the bottom.
"""
from pathlib import Path
from self_healing_scraper import scrape

HTML_ORIGINAL = """
<html><head><style>.x{}</style></head><body>
  <h1 class="product-title">Mechanical Keyboard</h1>
  <span class="price">$129.00</span>
  <script>var a = 1;</script>
</body></html>
"""

# Same product, redesigned markup — the original selectors no longer match.
HTML_REDESIGNED = """
<html><head><style>.x{}</style></head><body>
  <h1 class="pdp__name">Mechanical Keyboard</h1>
  <div class="pdp__pricing"><span data-testid="price">$129.00</span></div>
  <script>var a = 1;</script>
</body></html>
"""


def fake_healer(field, hint, html):
    """Stands in for an LLM call so the demo runs with no API key."""
    return {
        "title": {"value": "Mechanical Keyboard", "selector": "h1.pdp__name"},
        "price": {"value": "$129.00", "selector": "span[data-testid='price']"},
    }[field]


if __name__ == "__main__":
    Path("selectors.json").unlink(missing_ok=True)  # clean slate for a repeatable demo

    print("1. Original site — saved selectors work (no LLM call):")
    print("   ", scrape(HTML_ORIGINAL, fake_healer))

    print("2. Site redesigned — selectors break, scraper heals and saves the fix:")
    print("   ", scrape(HTML_REDESIGNED, fake_healer))

    print("3. Same redesigned site — healed selectors reused (no LLM call):")
    print("   ", scrape(HTML_REDESIGNED, fake_healer))

    # --- Real LLM usage ---
    # export OPENAI_API_KEY=sk-...
    # import httpx
    # from self_healing_scraper.heal import openai_healer
    # html = httpx.get("https://example.com/product/123").text
    # print(scrape(html, openai_healer))   # or just scrape(html) — openai is the default
