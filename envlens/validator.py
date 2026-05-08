"""Validate environment variable sets against a schema of required/optional keys."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, Iterable, Optional


class ValidationError(Exception):
    """Raised when schema construction receives invalid input."""


@dataclass(frozen=True)
class EnvSchema:
    """Describes required and optional environment variable keys."""

    required: FrozenSet[str] = field(default_factory=frozenset)
    optional: FrozenSet[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        overlap = self.required & self.optional
        if overlap:
            raise ValidationError(
                f"Keys appear in both required and optional: {sorted(overlap)}"
            )

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "EnvSchema":
        """Build an EnvSchema from a plain dict with 'required' / 'optional' lists."""
        required = frozenset(data.get("required", []))
        optional = frozenset(data.get("optional", []))
        return cls(required=required, optional=optional)


@dataclass
class ValidationResult:
    """Outcome of validating an env mapping against a schema."""

    missing_required: FrozenSet[str] = field(default_factory=frozenset)
    unknown_keys: FrozenSet[str] = field(default_factory=frozenset)

    @property
    def is_valid(self) -> bool:
        return not self.missing_required and not self.unknown_keys

    def summary(self) -> str:
        lines = []
        if self.missing_required:
            lines.append("Missing required keys: " + ", ".join(sorted(self.missing_required)))
        if self.unknown_keys:
            lines.append("Unknown keys: " + ", ".join(sorted(self.unknown_keys)))
        return "\n".join(lines) if lines else "OK"


def validate(
    env: Dict[str, str],
    schema: EnvSchema,
    *,
    allow_unknown: bool = True,
) -> ValidationResult:
    """Validate *env* against *schema*.

    Parameters
    ----------
    env:
        The environment mapping to validate.
    schema:
        The schema describing required/optional keys.
    allow_unknown:
        When *False*, keys not listed in required or optional are reported
        as ``unknown_keys``.
    """
    present = frozenset(env.keys())
    missing_required = schema.required - present

    if allow_unknown:
        unknown_keys: FrozenSet[str] = frozenset()
    else:
        known = schema.required | schema.optional
        unknown_keys = present - known

    return ValidationResult(
        missing_required=missing_required,
        unknown_keys=unknown_keys,
    )
