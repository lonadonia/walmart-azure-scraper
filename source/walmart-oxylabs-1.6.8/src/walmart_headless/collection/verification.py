"""The store checks of one page: what Walmart's own data showed against what the store's configuration
expects. A page counts only when every required check passed and none failed."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class StoreCheck:
    name: str
    ok: bool | None  # None: not applicable on this page
    observed: Any
    expected: Any
    required: bool = True
    note: str = ""


@dataclass
class StoreVerification:
    fetch_id: str
    purpose: str
    url: str
    checks: list[StoreCheck]
    context: dict[str, Any]
    attestation: list[dict[str, Any]] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        required_ok = all(c.ok is True for c in self.checks if c.required)
        return required_ok and not any(c.ok is False for c in self.checks)

    def failures(self) -> list[str]:
        return [
            f"{c.name}: observed {c.observed!r}, expected {c.expected!r}"
            for c in self.checks
            if c.ok is False
        ]

    def as_dict(self) -> dict[str, Any]:
        return {
            "fetch_id": self.fetch_id,
            "purpose": self.purpose,
            "url": self.url,
            "passed": self.passed,
            "checks": [asdict(c) for c in self.checks],
            "context": self.context,
            "attestation_A1_A8": self.attestation,
        }
