"""
Variable substitution resolver for parsed environment maps.

Supports ${VAR}, $VAR, and ${VAR:-default} syntax.
"""

import re
from typing import Dict, Optional

__all__ = ["SubstitutionError", "resolve_substitutions"]

_BRACED_RE = re.compile(
    r"\$\{(?P<name>[A-Za-z_][A-Za-z0-9_]*)(?::?-(?P<default>[^}]*))?\}"
)
_BARE_RE = re.compile(r"\$(?P<name>[A-Za-z_][A-Za-z0-9_]*)")


class SubstitutionError(ValueError):
    """Raised when a variable reference cannot be resolved."""


def _substitute_value(
    value: str,
    env: Dict[str, str],
    fallback: Optional[Dict[str, str]],
    strict: bool,
) -> str:
    """Expand all variable references in *value*."""

    def _replace_braced(m: re.Match) -> str:
        name = m.group("name")
        default = m.group("default")
        if name in env:
            return env[name]
        if fallback and name in fallback:
            return fallback[name]
        if default is not None:
            return default
        if strict:
            raise SubstitutionError(
                f"Unresolved variable reference: ${{{name}}}"
            )
        return m.group(0)

    def _replace_bare(m: re.Match) -> str:
        name = m.group("name")
        if name in env:
            return env[name]
        if fallback and name in fallback:
            return fallback[name]
        if strict:
            raise SubstitutionError(
                f"Unresolved variable reference: ${name}"
            )
        return m.group(0)

    value = _BRACED_RE.sub(_replace_braced, value)
    value = _BARE_RE.sub(_replace_bare, value)
    return value


def resolve_substitutions(
    env: Dict[str, str],
    fallback: Optional[Dict[str, str]] = None,
    strict: bool = False,
) -> Dict[str, str]:
    """Return a new dict with variable references in values expanded.

    Parameters
    ----------
    env:
        The environment map whose values should be resolved.
    fallback:
        An optional secondary map (e.g. the host environment) consulted
        when a name is not found in *env* itself.
    strict:
        When *True*, raise :class:`SubstitutionError` for any unresolved
        reference instead of leaving the placeholder intact.
    """
    resolved: Dict[str, str] = {}
    for key, value in env.items():
        resolved[key] = _substitute_value(value, env, fallback, strict)
    return resolved
