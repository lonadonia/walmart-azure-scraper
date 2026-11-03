"""Checked reading of JSON values the database stores (task checkpoints, observation provenance).

A JSONB column comes back as plain Python values whose shape no type checker can know. These readers
check the shape when the value is read: an absent value (``None``) reads as empty, and a value of another
shape raises :class:`CorruptJson` naming where it was found, so a damaged or foreign record stops the
work that reads it instead of being taken for something else."""

from __future__ import annotations

from collections.abc import Mapping


class CorruptJson(ValueError):
    """A stored JSON value does not have the shape its reader expects."""


def obj(value: object, where: str) -> Mapping[str, object]:
    """A JSON object (string keys); ``None`` reads as an empty one."""
    if value is None:
        return {}
    if isinstance(value, Mapping) and all(isinstance(k, str) for k in value):
        return value
    raise CorruptJson(f"{where}: expected a JSON object, found {type(value).__name__}")


def objects(value: object, where: str) -> list[Mapping[str, object]]:
    """A JSON array of objects; ``None`` reads as an empty one."""
    if value is None:
        return []
    if not isinstance(value, list):
        raise CorruptJson(f"{where}: expected a JSON array, found {type(value).__name__}")
    return [obj(v, f"{where}[{i}]") for i, v in enumerate(value)]


def text(value: object, where: str) -> str:
    """A JSON string; ``None`` reads as ``""``, and an integer as its decimal text (an id stored as a
    number). Any other shape is corrupt."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    raise CorruptJson(f"{where}: expected a string, found {type(value).__name__}")


def texts(value: object, where: str) -> list[str]:
    """A JSON array of strings; ``None`` reads as an empty one."""
    if value is None:
        return []
    if not isinstance(value, list):
        raise CorruptJson(f"{where}: expected a JSON array, found {type(value).__name__}")
    return [text(v, f"{where}[{i}]") for i, v in enumerate(value)]


def integer(value: object, where: str) -> int | None:
    """A JSON integer; ``None`` reads as ``None``."""
    if value is None:
        return None
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    raise CorruptJson(f"{where}: expected an integer, found {type(value).__name__}")
