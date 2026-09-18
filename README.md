# Self-Healing Scraper

A web scraper that notices when its own CSS selectors break, uses an LLM to find
the data again **and generate a fresh selector**, then saves that selector so the
next run is cheap again.

The LLM is not doing the scraping. It only runs when the normal path breaks — which
is what keeps this practical instead of a way to burn money on every request.

```
request → try SAVED selectors
             │
     ┌───────┴────────┐
   works            fails validation
     │                    │
  return         trim HTML → ask LLM for value + new selector
                            │
                     verify the new selector actually works
                            │
                     save it → return
```

## Install

```bash
pip install -r requirements.txt
```

## Try it (no API key needed)

The demo uses a fake healer so you can see the full lifecycle immediately:

```bash
python example.py
```

```
1. Original site — saved selectors work (no LLM call)
2. Site redesigned — selectors break, scraper heals and saves the fix
3. Same redesigned site — healed selectors reused (no LLM call)
```

## Real usage

```bash
export OPENAI_API_KEY=sk-...
```

```python
import httpx
from self_healing_scraper import scrape

html = httpx.get("https://example.com/product/123").text
product = scrape(html)          # OpenAI healer is the default
print(product)                  # Product(title='...', price=...)
```

Swap the model or provider by passing your own healer — any callable shaped like
`heal_field(field, hint, html) -> {"value": ..., "selector": ...}`:

```python
scrape(html, my_own_healer)
```

## How it works

- **Detect** — a `pydantic` schema (`Product`) is the health check. If extracted
  data fails validation, a selector has broken. This catches wrong-element matches,
  not just empty ones.
- **Heal** — the HTML is trimmed (scripts, styles, SVG stripped) and sent to the
  model, which returns both the value and a CSS selector for it.
- **Verify** — the returned selector is run against the real page to confirm it
  reaches the claimed value. The model can hallucinate; validation and verification
  are what keep a bad answer from being persisted.
- **Remember** — only verified selectors are written to `selectors.json`, so the
  next run skips the LLM entirely.

## Limitations

- **Cost scales with churn.** Healing on failure is cheap on stable sites and
  expensive on sites that reshuffle markup daily. Measure your break rate.
- **Validation is load-bearing.** A loose schema will accept a hallucination and
  persist a broken selector. Keep it strict.
- **It fixes layout, not access.** This repairs selectors after a redesign. It does
  nothing for anti-bot blocking, unrendered JavaScript, or rate limits.
- **Sometimes you shouldn't.** Stable site? Plain selectors are simpler and free.
  Official API available? It's almost always cheaper than healing a scraper.

## Tests

```bash
python -m pytest
```

## License

MIT — see [LICENSE](LICENSE).
