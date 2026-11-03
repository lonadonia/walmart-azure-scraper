"""How a product's price is displayed (the record builder's input), independent of the page parser."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class PriceDisplayKind(StrEnum):
    REGULAR = "regular"
    SALE = "sale"
    RELATIVE = "relative"  # "about $X each" (sold by weight)
    RELATIVE_SALE = "relative_sale"
    NOT_DISPLAYED = "not_displayed"  # e.g. "Prices May Vary"
    MISSING = "missing"  # no price block at all and no known placeholder


@dataclass(frozen=True)
class PriceDisplay:
    kind: PriceDisplayKind
    current_text: str  # displayed current price, e.g. "$34.99"
    original_text: str  # struck-through price, e.g. "$39.99"; "" when absent
    sr_text: str  # screen-reader sentence, e.g. "Sale: $34.99 discounted from $39.99"
    placeholder_text: str  # e.g. "Prices May Vary"
    regular_price: str  # normalised two-decimal string or ""
    sale_price: str

    @property
    def is_relative(self) -> bool:
        return self.kind in (PriceDisplayKind.RELATIVE, PriceDisplayKind.RELATIVE_SALE)
