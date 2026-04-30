"""Parser for Bitbucket Pipelines bitbucket-pipelines.yml environment variables."""

from __future__ import annotations

from typing import Dict

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise ImportError("PyYAML is required for Bitbucket Pipelines parsing: pip install pyyaml") from exc


class BitbucketParseError(ValueError):
    """Raised when a bitbucket-pipelines.yml file cannot be parsed."""


def _collect_env_blocks(doc: dict) -> Dict[str, str]:
    """Walk the parsed YAML document and collect all 'variables' key-value pairs.

    Bitbucket Pipelines stores environment variables under a top-level
    ``definitions.variables`` block and/or inside individual step
    ``variables`` mappings.  Later definitions overwrite earlier ones,
    mirroring runtime precedence.
    """
    result: Dict[str, str] = {}

    # Top-level definitions.variables
    definitions = doc.get("definitions") or {}
    for key, value in (definitions.get("variables") or {}).items():
        result[str(key)] = str(value) if value is not None else ""

    # Pipeline steps: pipelines -> default / branches / custom -> steps -> variables
    pipelines = doc.get("pipelines") or {}
    for pipeline_group in pipelines.values():
        if not isinstance(pipeline_group, list):
            continue
        for entry in pipeline_group:
            step_wrapper = entry if isinstance(entry, dict) else {}
            step = step_wrapper.get("step") or step_wrapper.get("parallel") or {}
            if isinstance(step, list):
                # parallel block contains a list of {step: ...}
                for parallel_entry in step:
                    inner = (parallel_entry or {}).get("step") or {}
                    for key, value in (inner.get("variables") or {}).items():
                        result[str(key)] = str(value) if value is not None else ""
            else:
                for key, value in (step.get("variables") or {}).items():
                    result[str(key)] = str(value) if value is not None else ""

    return result


def parse_bitbucket_pipelines(text: str) -> Dict[str, str]:
    """Parse *text* as a ``bitbucket-pipelines.yml`` file and return env vars."""
    if not text or not text.strip():
        return {}
    try:
        doc = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise BitbucketParseError(f"Invalid YAML: {exc}") from exc
    if not isinstance(doc, dict):
        return {}
    return _collect_env_blocks(doc)


def parse_bitbucket_pipelines_file(path: str) -> Dict[str, str]:
    """Read *path* from disk and parse it as a ``bitbucket-pipelines.yml`` file."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return parse_bitbucket_pipelines(fh.read())
    except OSError as exc:
        raise BitbucketParseError(f"Cannot read file '{path}': {exc}") from exc
