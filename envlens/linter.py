"""Lint an env mapping against common best-practice rules."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# Keys that should never be committed with non-empty values
_FORBIDDEN_PATTERNS: List[re.Pattern] = [
    re.compile(r"(?i)(password|passwd|secret|private_key|api_key|token|credential)"),
]

_VALID_KEY_RE = re.compile(r"^[A-Z_][A-Z0-9_]*$")
_SUSPICIOUS_VALUE_RE = re.compile(r"(?i)^(todo|fixme|changeme|example|placeholder|xxx)$")


@dataclass
class LintIssue:
    key: str
    code: str
    message: str
    severity: str  # "error" | "warning" | "info"


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(i.severity == "error" for i in self.issues)

    @property
    def has_warnings(self) -> bool:
        return any(i.severity == "warning" for i in self.issues)

    def errors(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "error"]

    def warnings(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "warning"]


def lint_env(
    env: Dict[str, str],
    *,
    allow_lowercase_keys: bool = False,
    max_value_length: Optional[int] = None,
) -> LintResult:
    """Run all lint rules against *env* and return a :class:`LintResult`."""
    result = LintResult()

    for key, value in env.items():
        # Rule L001 – key naming convention
        if not allow_lowercase_keys and not _VALID_KEY_RE.match(key):
            result.issues.append(
                LintIssue(
                    key=key,
                    code="L001",
                    message=f"Key '{key}' does not follow UPPER_SNAKE_CASE convention.",
                    severity="warning",
                )
            )

        # Rule L002 – empty value for sensitive key
        if not value:
            for pat in _FORBIDDEN_PATTERNS:
                if pat.search(key):
                    result.issues.append(
                        LintIssue(
                            key=key,
                            code="L002",
                            message=f"Sensitive key '{key}' has an empty value.",
                            severity="error",
                        )
                    )
                    break

        # Rule L003 – suspicious placeholder value
        if _SUSPICIOUS_VALUE_RE.match(value):
            result.issues.append(
                LintIssue(
                    key=key,
                    code="L003",
                    message=f"Key '{key}' has a suspicious placeholder value '{value}'.",
                    severity="warning",
                )
            )

        # Rule L004 – value exceeds maximum length
        if max_value_length is not None and len(value) > max_value_length:
            result.issues.append(
                LintIssue(
                    key=key,
                    code="L004",
                    message=(
                        f"Key '{key}' value length {len(value)} exceeds "
                        f"maximum {max_value_length}."
                    ),
                    severity="warning",
                )
            )

    return result
