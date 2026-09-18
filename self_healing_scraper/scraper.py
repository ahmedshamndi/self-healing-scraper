"""The healing mechanics: try saved selectors, and if they fail validation,
ask an LLM to find the data and a fresh selector, verify it, and persist it."""
import json
from pathlib import Path

from bs4 import BeautifulSoup
from parsel import Selector

from .schema import Product, validate

SELECTOR_STORE = Path("selectors.json")

DEFAULT_SELECTORS = {
    "title": "h1.product-title",
    "price": "span.price",
}

FIELD_HINTS = {
    "title": "the product's name or title",
    "price": "the product's price, digits only",
}


def load_selectors() -> dict:
    if SELECTOR_STORE.exists():
        return json.loads(SELECTOR_STORE.read_text())
    return dict(DEFAULT_SELECTORS)


def save_selectors(selectors: dict) -> None:
    SELECTOR_STORE.write_text(json.dumps(selectors, indent=2))


def extract(html: str, selectors: dict) -> dict:
    tree = Selector(html)
    return {f: tree.css(f"{s}::text").get() for f, s in selectors.items()}


def trim_html(html: str) -> str:
    """Drop everything the model doesn't need, to save tokens and money."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "svg", "noscript", "head"]):
        tag.decompose()
    return str(soup)


def verify(html: str, selector: str, expected: str) -> bool:
    """Confirm the LLM's selector actually reaches its claimed value."""
    got = Selector(html).css(f"{selector}::text").get()
    return got is not None and expected.strip() in got.strip()


def scrape(html: str, heal_field=None) -> Product:
    """Scrape one page. Fast path uses saved selectors; on failure it heals.

    heal_field(field, hint, html) -> {"value", "selector"} is injected so you
    can swap providers or mock it. Defaults to the OpenAI healer.
    """
    selectors = load_selectors()

    # Fast path — the selectors we already trust
    product = validate(extract(html, selectors))
    if product is not None:
        return product

    # Slow path — heal
    if heal_field is None:
        from .heal import openai_healer
        heal_field = openai_healer

    trimmed = trim_html(html)
    new_selectors = dict(selectors)
    values = {}
    for field in Product.model_fields:
        result = heal_field(field, FIELD_HINTS[field], trimmed)
        if verify(html, result["selector"], result["value"]):
            new_selectors[field] = result["selector"]  # keep only verified fixes
        values[field] = result["value"]

    product = validate(values)
    if product is None:
        raise ValueError("healing failed: LLM output did not match schema")

    save_selectors(new_selectors)   # next run is back on the fast path
    return product
