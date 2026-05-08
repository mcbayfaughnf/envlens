"""Normalizer: apply case and whitespace normalization to env variable dicts.

Useful when comparing env sets from sources that may differ in key casing
(e.g. Windows vs Linux) or have stray surrounding whitespace in values.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict


class KeyCase(str, Enum):
    """Strategy for normalizing env variable key casing."""
    PRESERVE = "preserve"
    UPPER = "upper"
    LOWER = "lower"


@dataclass(frozen=True)
class NormalizeOptions:
    """Options controlling normalization behaviour."""
    key_case: KeyCase = KeyCase.PRESERVE
    strip_values: bool = True
    collapse_empty: bool = False  # treat whitespace-only values as empty string


def normalize_keys(env: Dict[str, str], case: KeyCase) -> Dict[str, str]:
    """Return a new dict with keys transformed according to *case*.

    If two keys collide after transformation the *last* one (in iteration
    order) wins — consistent with how duplicate keys are handled elsewhere in
    envlens.
    """
    if case is KeyCase.PRESERVE:
        return dict(env)
    transform = str.upper if case is KeyCase.UPPER else str.lower
    result: Dict[str, str] = {}
    for k, v in env.items():
        result[transform(k)] = v
    return result


def normalize_values(env: Dict[str, str], *, strip: bool, collapse_empty: bool) -> Dict[str, str]:
    """Return a new dict with values optionally stripped / collapsed."""
    result: Dict[str, str] = {}
    for k, v in env.items():
        if strip:
            v = v.strip()
        if collapse_empty and v.strip() == "":
            v = ""
        result[k] = v
    return result


def normalize_env(env: Dict[str, str], options: NormalizeOptions | None = None) -> Dict[str, str]:
    """Apply all normalization steps defined by *options* to *env*.

    Parameters
    ----------
    env:
        Raw mapping of environment variable names to values.
    options:
        :class:`NormalizeOptions` instance; defaults are used when *None*.

    Returns
    -------
    Dict[str, str]
        A new, normalized mapping (the original is never mutated).
    """
    if options is None:
        options = NormalizeOptions()

    result = normalize_keys(env, options.key_case)
    result = normalize_values(
        result,
        strip=options.strip_values,
        collapse_empty=options.collapse_empty,
    )
    return result
