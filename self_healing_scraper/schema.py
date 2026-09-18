"""What a valid scrape result looks like. This is our health detector:
if extracted data fails this schema, a selector has broken."""
from pydantic import BaseModel, ValidationError, field_validator


class Product(BaseModel):
    title: str
    price: float

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("empty title")
        return v.strip()


def validate(raw: dict) -> Product | None:
    """Return a Product if the raw dict is valid, else None (the break signal)."""
    clean = {}
    for key, value in raw.items():
        if value is None:
            return None
        if key == "price":
            value = "".join(c for c in value if c.isdigit() or c == ".")
        clean[key] = value
    try:
        return Product(**clean)
    except ValidationError:
        return None
