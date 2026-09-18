"""Concrete LLM healer. scrape() only needs a callable shaped like
    heal_field(field, hint, html) -> {"value": ..., "selector": ...}
so you can swap this for Anthropic, a local model, or a mock in tests."""
import json
from functools import lru_cache

HEAL_PROMPT = """You are a web-scraping repair tool.
Find one field in the HTML below and return a CSS selector that reaches it.

Field: {field}
What it is: {hint}

Return ONLY JSON, no prose:
{{"value": "<exact text you found>", "selector": "<CSS selector for the element>"}}

HTML:
{html}
"""


@lru_cache
def _client():
    # imported lazily so the package works with no API key until you actually heal
    from openai import OpenAI
    return OpenAI()  # reads OPENAI_API_KEY


def openai_healer(field: str, hint: str, html: str) -> dict:
    resp = _client().chat.completions.create(
        model="gpt-4o-mini",          # a cheap model is fine — validation catches errors
        temperature=0,
        response_format={"type": "json_object"},
        messages=[{
            "role": "user",
            "content": HEAL_PROMPT.format(field=field, hint=hint, html=html),
        }],
    )
    return json.loads(resp.choices[0].message.content)
