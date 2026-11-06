"""What a product page states about the size of its own pack (release 1.5.0).

A product page carries many numbers that look like sizes. They are read apart, by what each one measures:

* the pack: the selected ``size`` variant, the specifications "Size", "Net content statement" and "Product
  net content parent" (with its unit);
* a count: the selected count variant, "Count per pack", "Total count", "Count", "Number of loads", "Sheets",
  "Piece count", "Pieces";
* a multipack: the selected ``multipack_quantity``, "Multipack quantity", "Pack quantity". It says how many
  packs are sold together and stays beside the size; the two are never multiplied;
* never a pack size: a serving size, the unit-price denominator ("$0.16/oz"), a sibling variant's size, a
  shipping or assembled weight, an average or maximum sold-by-weight value, the weight range of a diaper.

The value is the source's own text. A bare count takes its unit from the specification's own label ("Number
of loads" 88 gives "88 Loads"); nothing is converted, added or multiplied into a value. Units are converted
only to compare two statements ("16 oz" and "1 Pound" agree). Statements that disagree are all kept and the
outcome is ``conflict``: no value is chosen. "Product net content parent" is also checked against the page's
own "Product net content uom": "4 Pound" declared in "Each" (item 162577028, "Fresh Navel Orange, Each": a
bag's weight for one orange) is a page that contradicts itself, so it is a conflict too.

A title that states a size keeps it (the listing displays it). The page is then only compared with it, and a
disagreement is flagged, as for item 49986668, titled "141 oz, 66 Loads" while its page states 88 loads.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from walmart_headless.sites.walmart.page_data import get, text

DATA_PATH = "props.pageProps.initialData.data"
# What an observation measures.
PACK, COUNT, MULTIPACK, NEVER = "pack", "count", "multipack", "never_a_pack_size"

_PACK_SPECS = {
    "size": "spec_size",
    "net content statement": "spec_net_content",
    "product net content parent": "spec_net_content_parent",
}
# label -> (kind, the unit the label gives a bare number)
_COUNT_SPECS = {
    "count per pack": ("spec_count_per_pack", "Count"),
    "total count": ("spec_total_count", "Count"),
    "count": ("spec_count", "Count"),
    "number of loads": ("spec_number_of_loads", "Loads"),
    "sheets": ("spec_sheets", "Sheets"),
    "piece count": ("spec_piece_count", "Pieces"),
    "pieces": ("spec_pieces", "Pieces"),
}
_MULTIPACK_SPECS = {"multipack quantity": "spec_multipack_quantity", "pack quantity": "spec_pack_quantity"}
_NEVER_SPECS = {
    "serving size": "serving",
    "weight": "spec_weight",
    "assembled product weight": "spec_assembled_weight",
    "average sold by weight": "average_sold_by_weight",
    "maximum sold by weight": "maximum_sold_by_weight",
    "minimum weight": "minimum_weight",
    "maximum weight": "maximum_weight",
}
_COUNT_VARIANTS = {
    "count_per_pack": ("selected_variant_count", "Count"),
    "number_of_pieces": ("selected_variant_pieces", "Pieces"),
    "piece_count": ("selected_variant_pieces", "Pieces"),
    "number_of_loads": ("selected_variant_loads", "Loads"),
}

# unit -> (what it measures, its size in that measure's base unit), for comparisons only.
_MASS = {
    "oz": Decimal(1),
    "ounce": Decimal(1),
    "ounces": Decimal(1),
    "lb": Decimal(16),
    "lbs": Decimal(16),
    "pound": Decimal(16),
    "pounds": Decimal(16),
    "g": Decimal("0.035274"),
    "gram": Decimal("0.035274"),
    "grams": Decimal("0.035274"),
    "kg": Decimal("35.274"),
    "mg": Decimal("0.000035274"),
}
_VOLUME = {
    "fl oz": Decimal(1),
    "floz": Decimal(1),
    "fluid ounce": Decimal(1),
    "fluid ounces": Decimal(1),
    "fl ounce": Decimal(1),
    "fl ounces": Decimal(1),
    "gal": Decimal(128),
    "gallon": Decimal(128),
    "gallons": Decimal(128),
    "qt": Decimal(32),
    "quart": Decimal(32),
    "quarts": Decimal(32),
    "pt": Decimal(16),
    "pint": Decimal(16),
    "pints": Decimal(16),
    "ml": Decimal("0.033814"),
    "milliliter": Decimal("0.033814"),
    "milliliters": Decimal("0.033814"),
    "l": Decimal("33.814"),
    "liter": Decimal("33.814"),
    "liters": Decimal("33.814"),
    "litre": Decimal("33.814"),
    "litres": Decimal("33.814"),
}
_COUNT_WORDS = (
    "count|ct|each|ea|pieces?|pcs?|pc|sheets?|rolls?|wipes|diapers|pods?|pacs?|tablets?|tabs?|capsules?|caplets?"
    "|softgels?|gummies|drops?|lozenges?|pouch(?:es)?|packets?|kits?|bags?|cans?|bottles?|bars?|sticks?"
)
_LOADS = "loads?"
_PACK_WORDS = "packs?|pk"
_MEASURE = re.compile(
    r"(?<![\w.])(?P<qty>\d+(?:\.\d+)?)\s*-?\s*"
    r"(?P<unit>fl\.?\s?ounces?|fl\.?\s?oz|fluid\s+ounces?|ounces?|oz|lbs?|pounds?|milliliters?|ml|mg|kg|grams?|g"
    rf"|liters?|litres?|l|gallons?|gal|quarts?|qt|pints?|pt|{_LOADS}|{_PACK_WORDS}|{_COUNT_WORDS})\b\.?",
    re.I,
)
_PACK_OF = re.compile(r"\b(?:pack|case|box|set|bag|bundle) of (?P<qty>\d+)\b", re.I)
_BARE = re.compile(r"^\d+(?:\.\d+)?$")
# The label the source's own net content statement may open with; the value stays as written.
_NET_LABEL = re.compile(r"^(?:net\s*(?:wt|weight|contents?|content)|nt\s*wt)\b\.?:?\s*", re.I)
# Two statements of one measure agree within rounding ("26.46 oz" and "750 g").
_TOLERANCE = Decimal("0.015")
# What a page says when it has nothing more to say: not a size that competes with a real one.
_DEFAULT_COUNT = re.compile(r"^1(?:\.0+)?\s*(?:each|ea|count|ct)\.?$", re.I)


@dataclass(frozen=True)
class SizeObservation:
    """One statement of a page, as written, with where it was read and what it measures."""

    kind: str
    measures: str  # PACK | COUNT | MULTIPACK | NEVER
    value: str
    path: str

    def as_dict(self) -> dict[str, str]:
        return {"kind": self.kind, "measures": self.measures, "value": self.value, "path": self.path}


@dataclass(frozen=True)
class PackSize:
    """The decision about a page's statements (see the module docstring)."""

    value: str  # the size to use when the title states none; "" when none or unresolved
    # title_kept | title_conflict | agreed | single_statement | count_only | conflict | default_only | none
    outcome: str
    rule: str  # the kind of the observation the value came from
    path: str  # where the value came from
    conflicts: tuple[str, ...]
    observations: tuple[SizeObservation, ...]

    @property
    def conflict(self) -> bool:
        return bool(self.conflicts)

    def as_dict(self) -> dict[str, Any]:
        return {
            "value": self.value,
            "outcome": self.outcome,
            "rule": self.rule,
            "path": self.path,
            "conflicts": list(self.conflicts),
            "observations": [o.as_dict() for o in self.observations],
        }


def observations(nd: Mapping[str, Any]) -> tuple[SizeObservation, ...]:
    """Every statement about size on a product page, each under the measure it belongs to."""
    data = get(nd, "props", "pageProps", "initialData", "data")
    if not isinstance(data, Mapping):
        return ()
    found: list[SizeObservation] = []
    product = data.get("product")
    product = product if isinstance(product, Mapping) else {}
    for i, group in enumerate(product.get("variantCriteria") or []):
        if isinstance(group, Mapping):
            found.extend(_variant_group(group, f"{DATA_PATH}.product.variantCriteria[{i}]"))
    idml = data.get("idml")
    idml = idml if isinstance(idml, Mapping) else {}
    found.extend(_specifications(idml))
    serving = get(idml, "nutritionFacts", "servingInfo")
    for path, value in _strings(serving, f"{DATA_PATH}.idml.nutritionFacts.servingInfo"):
        found.append(SizeObservation("serving", NEVER, value, path))
    unit_price = text(get(product, "priceInfo", "unitPrice", "priceString"))
    if unit_price:
        path = f"{DATA_PATH}.product.priceInfo.unitPrice.priceString"
        found.append(SizeObservation("unit_price_denominator", NEVER, unit_price, path))
    return tuple(found)


def _variant_group(group: Mapping[str, Any], path: str) -> list[SizeObservation]:
    cid = text(group.get("id")).casefold()
    if cid != "size" and cid != "multipack_quantity" and cid not in _COUNT_VARIANTS:
        return []
    found = []
    for j, option in enumerate(group.get("variantList") or []):
        if not isinstance(option, Mapping):
            continue
        value, at = text(option.get("name")), f"{path}.variantList[{j}].name"
        if not value:
            continue
        if not option.get("selected"):
            found.append(SizeObservation(f"sibling_variant_{cid}", NEVER, value, at))
        elif cid == "size":
            found.append(SizeObservation("selected_variant_size", PACK, value, at))
        elif cid == "multipack_quantity":
            found.append(SizeObservation("selected_variant_multipack", MULTIPACK, value, at))
        else:
            kind, unit = _COUNT_VARIANTS[cid]
            found.append(SizeObservation(kind, COUNT, _with_unit(value, unit), at))
    return found


def _specifications(idml: Mapping[str, Any]) -> list[SizeObservation]:
    found = []
    specs = idml.get("specifications")
    specs = specs if isinstance(specs, list) else []
    unit = ""
    for spec in specs:
        if isinstance(spec, Mapping) and text(spec.get("name")).casefold() == "product net content uom":
            unit = text(spec.get("value"))
    for i, spec in enumerate(specs):
        if not isinstance(spec, Mapping):
            continue
        label, value = text(spec.get("name")).casefold(), text(spec.get("value"))
        at = f"{DATA_PATH}.idml.specifications[{i}].value"
        if not value:
            continue
        if label == "product net content uom":
            # The unit the parent statement is declared in: kept to check that statement, never a size.
            found.append(SizeObservation("spec_net_content_uom", NEVER, value, at))
        elif label in _PACK_SPECS:
            kind = _PACK_SPECS[label]
            if kind == "spec_net_content_parent" and unit:
                value = _with_unit(value, unit)
            found.append(SizeObservation(kind, PACK, value, at))
        elif label in _COUNT_SPECS:
            kind, word = _COUNT_SPECS[label]
            found.append(SizeObservation(kind, COUNT, _with_unit(value, word), at))
        elif label in _MULTIPACK_SPECS:
            found.append(SizeObservation(_MULTIPACK_SPECS[label], MULTIPACK, value, at))
        elif label in _NEVER_SPECS:
            found.append(SizeObservation(_NEVER_SPECS[label], NEVER, value, at))
    return found


def _with_unit(value: str, unit: str) -> str:
    """A bare number takes the unit its own label states; any other text stays as written."""
    return f"{value} {unit}" if _BARE.match(value) else value


def _strings(obj: Any, path: str) -> list[tuple[str, str]]:
    """The non-empty texts inside a small object (a serving size's labels and values), at most eight."""
    out: list[tuple[str, str]] = []
    if isinstance(obj, Mapping):
        for k, v in obj.items():
            out.extend(_strings(v, f"{path}.{k}"))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.extend(_strings(v, f"{path}[{i}]"))
    elif text(obj):
        out.append((path, text(obj)))
    return out[:8]


def _measure_of(unit: str) -> tuple[str, Decimal]:
    u = " ".join(unit.casefold().replace(".", "").split())
    if u in _MASS:
        return "mass", _MASS[u]
    if u in _VOLUME:
        return "volume", _VOLUME[u]
    if re.fullmatch(_LOADS, u):
        return "loads", Decimal(1)
    if re.fullmatch(_PACK_WORDS, u):
        return "packs", Decimal(1)
    return "count", Decimal(1)


def measures_in(value: str) -> list[tuple[str, Decimal]]:
    """Each amount a size text states, as (what it measures, the amount in that measure's base unit)."""
    out: list[tuple[str, Decimal]] = []
    for m in _MEASURE.finditer(value):
        try:
            qty = Decimal(m.group("qty"))
        except InvalidOperation:
            continue
        measure, factor = _measure_of(m.group("unit"))
        out.append((measure, qty * factor))
    for m in _PACK_OF.finditer(value):
        out.append(("packs", Decimal(m.group("qty"))))
    return out


# A size that names two packages of a set ("12.5 oz shampoo + 10.6 oz conditioner").
_TWO_PACKAGES = re.compile(r"\d[^,]*(?:\+|&|\band\b)[^,]*\d", re.I)


def is_quantity(value: str) -> bool:
    """The text opens with an amount and a unit ("3 lbs", also after a label: "NET WT 7oz (198g)"), unlike
    "Medium Apples", "Blueberries" or a bare "65" that names no unit."""
    return _MEASURE.match(_NET_LABEL.sub("", value, count=1)) is not None


def _close(a: Decimal, b: Decimal) -> bool:
    return abs(a - b) <= _TOLERANCE * max(abs(a), abs(b))


def _agree(a: Decimal, b: Decimal, factors: set[Decimal]) -> bool:
    """Equal within rounding, or one is the other times a pack quantity the page states: a pack and its
    multipack differ by that quantity and that is no conflict. Checked only; nothing is computed for
    export."""
    return _close(a, b) or any(_close(a * f, b) or _close(b * f, a) for f in factors)


def _factors(obs: tuple[SizeObservation, ...]) -> set[Decimal]:
    """Pack quantities and counts the page states (above one), the only amounts two sizes may differ by."""
    out: set[Decimal] = set()
    for o in obs:
        if o.measures == MULTIPACK and _BARE.match(o.value) and Decimal(o.value) > 1:
            out.add(Decimal(o.value))
        elif o.measures == COUNT:
            for measure, amount in measures_in(o.value):
                if measure == "count" and amount > 1:
                    out.add(amount)
    return out


def _disagreements(statements: list[tuple[str, str]], factors: set[Decimal], *, label: str = "") -> list[str]:
    """Pairs of statements of one measure that do not agree, as readable notes."""
    by_measure: dict[str, list[tuple[str, str, Decimal]]] = {}
    for kind, value in statements:
        for measure, amount in measures_in(value):
            by_measure.setdefault(measure, []).append((kind, value, amount))
    notes: list[str] = []
    for measure, group in by_measure.items():
        # A count and a pack of many can differ by design ("Count per pack" 5, "Total count" 25).
        usable = factors if measure in ("mass", "volume") else set()
        for i, (k1, v1, a1) in enumerate(group):
            for k2, v2, a2 in group[i + 1 :]:
                if not _agree(a1, a2, usable):
                    notes.append(f"{label}{k1} {v1!r} and {k2} {v2!r} state different {measure}")
    return list(dict.fromkeys(notes))


def decide(obs: tuple[SizeObservation, ...], title_size: str = "") -> PackSize:
    """The page's statements against each other and against the title's size."""
    factors = _factors(obs)
    pack = [o for o in obs if o.measures == PACK and is_quantity(o.value)]
    real = [o for o in pack if not _DEFAULT_COUNT.match(o.value)]
    counts = [o for o in obs if o.measures == COUNT and is_quantity(o.value)]
    multipack = next(
        (o for o in obs if o.measures == MULTIPACK and _BARE.match(o.value) and Decimal(o.value) > 1), None
    )
    if title_size and _TWO_PACKAGES.search(title_size):
        # The title names a set's two packages (release 1.5.2): a page's one size speaks of one of them or of
        # the whole, so nothing can be compared and nothing is chosen.
        return PackSize("", "title_kept", "", "", (), obs)
    if title_size:
        statements = [("title", title_size), *((o.kind, o.value) for o in real), *_comparable_counts(counts)]
        # "2 pack, 16 lbs" and a page's "32 lb" differ by the pack the title states: no conflict
        # (release 1.5.1).
        title_packs = {a for measure, a in measures_in(title_size) if measure == "packs" and a > 1}
        title_notes = [n for n in _disagreements(statements, factors | title_packs) if "title" in n]
        if multipack is not None:
            title_notes.extend(_title_multipack(title_size, multipack))
        return PackSize(
            "", "title_conflict" if title_notes else "title_kept", "", "", tuple(title_notes), obs
        )
    notes = _declared_unit_notes(real, obs) + _disagreements([(o.kind, o.value) for o in real], factors)
    if notes:
        return PackSize("", "conflict", "", "", tuple(notes), obs)
    if real:
        first = real[0]
        value = first.value
        if multipack is not None and "pack" not in value.casefold():
            value = f"{value}, {multipack.value} Pack"
        return PackSize(
            value, "agreed" if len(real) > 1 else "single_statement", first.kind, first.path, (), obs
        )
    # Counts carry a meaning in their label, so only equal ones of one measure can fill a size.
    if counts:
        loads_and_counts = {(measure, amount) for o in counts for measure, amount in measures_in(o.value)}
        if len(loads_and_counts) > 1:
            shown = "; ".join(f"{o.kind} {o.value!r}" for o in counts)
            return PackSize("", "conflict", "", "", (f"several counts: {shown}",), obs)
        first = counts[0]
        return PackSize(first.value, "count_only", first.kind, first.path, (), obs)
    if pack:
        first = pack[0]
        return PackSize(first.value, "default_only", first.kind, first.path, (), obs)
    if multipack is not None:
        return PackSize(f"{multipack.value} Pack", "count_only", multipack.kind, multipack.path, (), obs)
    return PackSize("", "none", "", "", (), obs)


def _declared_unit_notes(pack: list[SizeObservation], obs: tuple[SizeObservation, ...]) -> list[str]:
    """A "Product net content parent" whose own unit measures something else than the page's declared
    "Product net content uom" ("4 Pound" in "Each"), when no other pack statement of the page stands beside
    it: another statement that agrees corroborates the value (item 19963859025: "Size" 2.6 oz, parent
    "2.6 Ounces" declared in "Count"), and one that disagrees is a conflict anyway. A bare parent value took
    the declared unit and agrees by construction; a declared unit that names no known measure ("Case") is
    not compared."""
    uom = next((o for o in obs if o.kind == "spec_net_content_uom"), None)
    if uom is None or any(o.kind != "spec_net_content_parent" for o in pack):
        return []
    declared = {measure for measure, _ in measures_in(f"1 {uom.value}")}
    if not declared:
        return []
    notes = []
    for o in pack:
        own = {measure for measure, _ in measures_in(o.value)}
        if o.kind == "spec_net_content_parent" and own and not own & declared:
            notes.append(
                f"{o.kind} {o.value!r} and its declared unit spec_net_content_uom {uom.value!r} "
                "state different measures"
            )
    return notes


def _comparable_counts(counts: list[SizeObservation]) -> list[tuple[str, str]]:
    """Counts a title can be checked against: the same unit word means the same thing (loads with loads).
    A title's "24 Count" against a page's total of several packs is not checked here."""
    return [(o.kind, o.value) for o in counts if any(m == "loads" for m, _ in measures_in(o.value))]


def _title_multipack(title_size: str, multipack: SizeObservation) -> list[str]:
    for measure, amount in measures_in(title_size):
        if measure == "packs" and amount > 1 and amount != Decimal(multipack.value):
            return [
                f"title {title_size!r} and {multipack.kind} {multipack.value!r} state different pack "
                "quantities"
            ]
    return []


def pack_size(nd: Mapping[str, Any], title_size: str = "") -> PackSize:
    """What the product page in ``nd`` states about its pack, decided against the title's size."""
    return decide(observations(nd), title_size)
