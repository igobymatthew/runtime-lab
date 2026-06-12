from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_cases_jsonl(path: str | Path) -> list[dict[str, Any]]:
    """Read BigSet Local-style JSONL cases.

    TODO(bigset-local): Replace this with a real Python import when BigSet Local exposes a stable
    package/API for local dataset case reads. The current sibling repo is a TypeScript app.
    """
    cases: list[dict[str, Any]] = []
    case_path = Path(path)
    with case_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            case = json.loads(line)
            if not isinstance(case, dict):
                raise ValueError(f"{case_path}:{line_number} must contain a JSON object")
            if "id" not in case or "input" not in case or "expected" not in case:
                raise ValueError(
                    f"{case_path}:{line_number} must include id, input, and expected fields"
                )
            cases.append(case)
    return cases


def write_failure_cases_jsonl(cases: list[dict[str, Any]], path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for case in cases:
            handle.write(json.dumps(case, sort_keys=True))
            handle.write("\n")
    return output_path
