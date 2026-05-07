"""Parser for Azure Pipelines YAML configuration files."""

from __future__ import annotations

from typing import Dict

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise ImportError("PyYAML is required: pip install pyyaml") from exc


class AzurePipelinesParseError(Exception):
    """Raised when an Azure Pipelines YAML file cannot be parsed."""


def _collect_env_blocks(data: dict) -> Dict[str, str]:
    """Walk the pipeline structure and collect env/variables entries.

    Precedence (last write wins, matching envlens convention):
      1. Top-level ``variables`` block
      2. Stage-level ``variables`` blocks
      3. Job-level ``variables`` blocks
      4. Step-level ``env`` blocks
    """
    result: Dict[str, str] = {}

    def _absorb_variables(block) -> None:
        """Merge a ``variables`` block (list or dict) into *result*."""
        if isinstance(block, dict):
            for k, v in block.items():
                result[str(k)] = str(v) if v is not None else ""
        elif isinstance(block, list):
            for item in block:
                if isinstance(item, dict):
                    # Azure list form: [{name: X, value: Y}, ...]
                    if "name" in item and "value" in item:
                        result[str(item["name"])] = str(item["value"]) if item["value"] is not None else ""
                    else:
                        # plain key/value dict inside list
                        for k, v in item.items():
                            result[str(k)] = str(v) if v is not None else ""

    def _walk_steps(steps) -> None:
        if not isinstance(steps, list):
            return
        for step in steps:
            if isinstance(step, dict) and "env" in step:
                _absorb_variables(step["env"])

    def _walk_jobs(jobs) -> None:
        if not isinstance(jobs, list):
            return
        for job in jobs:
            if not isinstance(job, dict):
                continue
            if "variables" in job:
                _absorb_variables(job["variables"])
            for key in ("steps", "deployment"):
                if key in job:
                    _walk_steps(job.get("steps", []))

    def _walk_stages(stages) -> None:
        if not isinstance(stages, list):
            return
        for stage in stages:
            if not isinstance(stage, dict):
                continue
            if "variables" in stage:
                _absorb_variables(stage["variables"])
            _walk_jobs(stage.get("jobs", []))

    # Top-level variables
    if "variables" in data:
        _absorb_variables(data["variables"])

    _walk_stages(data.get("stages", []))
    _walk_jobs(data.get("jobs", []))
    _walk_steps(data.get("steps", []))

    return result


def parse_azure_pipelines(text: str) -> Dict[str, str]:
    """Parse *text* as an Azure Pipelines YAML and return env vars."""
    if not text or not text.strip():
        return {}
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise AzurePipelinesParseError(f"Invalid YAML: {exc}") from exc
    if not isinstance(data, dict):
        return {}
    return _collect_env_blocks(data)


def parse_azure_pipelines_file(path: str) -> Dict[str, str]:
    """Read *path* and delegate to :func:`parse_azure_pipelines`."""
    with open(path, "r", encoding="utf-8") as fh:
        return parse_azure_pipelines(fh.read())
