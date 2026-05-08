"""Redact sensitive values from env dicts before display or export."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, Optional

from envlens.masker import is_sensitive

REDACTED_PLACEHOLDER = "***REDACTED***"


@dataclass(frozen=True)
class RedactOptions:
    """Options controlling redaction behaviour."""

    placeholder: str = REDACTED_PLACEHOLDER
    # Additional keys to always redact, regardless of pattern matching.
    extra_keys: FrozenSet[str] = field(default_factory=frozenset)
    # Keys to never redact even if they match a sensitive pattern.
    allow_keys: FrozenSet[str] = field(default_factory=frozenset)


def redact_env(
    env: Dict[str, str],
    options: Optional[RedactOptions] = None,
) -> Dict[str, str]:
    """Return a copy of *env* with sensitive values replaced by a placeholder.

    Args:
        env: Mapping of environment variable names to values.
        options: Redaction options; defaults are used when *None*.

    Returns:
        A new dict where every sensitive key's value is replaced.
    """
    if options is None:
        options = RedactOptions()

    result: Dict[str, str] = {}
    for key, value in env.items():
        if key in options.allow_keys:
            result[key] = value
        elif key in options.extra_keys or is_sensitive(key):
            result[key] = options.placeholder
        else:
            result[key] = value
    return result


def redact_diff_values(
    only_in_source: Dict[str, str],
    only_in_target: Dict[str, str],
    mismatches: Dict[str, tuple],
    options: Optional[RedactOptions] = None,
) -> tuple:
    """Redact sensitive values inside diff component dicts.

    Returns:
        Tuple of (redacted_only_in_source, redacted_only_in_target,
                  redacted_mismatches) where mismatch values are
                  (src_value, tgt_value) pairs.
    """
    if options is None:
        options = RedactOptions()

    r_src = redact_env(only_in_source, options)
    r_tgt = redact_env(only_in_target, options)

    r_mis: Dict[str, tuple] = {}
    for key, (src_val, tgt_val) in mismatches.items():
        if key in options.allow_keys:
            r_mis[key] = (src_val, tgt_val)
        elif key in options.extra_keys or is_sensitive(key):
            r_mis[key] = (options.placeholder, options.placeholder)
        else:
            r_mis[key] = (src_val, tgt_val)
    return r_src, r_tgt, r_mis
