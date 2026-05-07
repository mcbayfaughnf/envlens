"""Utilities for masking sensitive environment variable values in output."""

from __future__ import annotations

import re
from typing import Dict, FrozenSet, Optional

# Patterns whose matching key names are considered sensitive by default
_DEFAULT_SENSITIVE_PATTERNS: tuple[str, ...] = (
    r".*SECRET.*",
    r".*PASSWORD.*",
    r".*PASSWD.*",
    r".*TOKEN.*",
    r".*API_KEY.*",
    r".*PRIVATE_KEY.*",
    r".*CREDENTIALS.*",
    r".*AUTH.*",
    r".*ACCESS_KEY.*",
)

MASK_PLACEHOLDER = "***"


def _compile_patterns(patterns: tuple[str, ...]) -> list[re.Pattern[str]]:
    return [re.compile(p, re.IGNORECASE) for p in patterns]


_DEFAULT_COMPILED = _compile_patterns(_DEFAULT_SENSITIVE_PATTERNS)


def is_sensitive(
    key: str,
    extra_patterns: Optional[tuple[str, ...]] = None,
    sensitive_keys: Optional[FrozenSet[str]] = None,
) -> bool:
    """Return True if *key* should be treated as sensitive."""
    if sensitive_keys and key.upper() in {k.upper() for k in sensitive_keys}:
        return True
    compiled = _DEFAULT_COMPILED
    if extra_patterns:
        compiled = compiled + _compile_patterns(extra_patterns)
    return any(pat.fullmatch(key) for pat in compiled)


def mask_env(
    env: Dict[str, str],
    extra_patterns: Optional[tuple[str, ...]] = None,
    sensitive_keys: Optional[FrozenSet[str]] = None,
    placeholder: str = MASK_PLACEHOLDER,
) -> Dict[str, str]:
    """Return a copy of *env* with sensitive values replaced by *placeholder*."""
    return {
        k: (placeholder if is_sensitive(k, extra_patterns, sensitive_keys) else v)
        for k, v in env.items()
    }
