from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime_lab.local_imports import add_sibling_import_paths

add_sibling_import_paths()

try:
    from ai_runtime_abi.contract import TaskContract
    from ai_runtime_abi.schema_validator import validate_input, validate_output
except ImportError:  # pragma: no cover - only used before sibling repo exists.
    class TaskContract:  # type: ignore[no-redef]
        """TODO(ai-runtime-abi): Remove when the sibling package is importable."""

        def __init__(self, raw: dict[str, Any], path: Path | None = None) -> None:
            self.raw = raw
            self.path = path

        @property
        def task(self) -> str:
            return str(self.raw["task"])

        @property
        def version(self) -> str:
            return str(self.raw["version"])

        @classmethod
        def from_file(cls, path: str | Path) -> "TaskContract":
            import json

            contract_path = Path(path)
            with contract_path.open("r", encoding="utf-8") as handle:
                raw = json.load(handle)
            missing = {"task", "version", "input_schema", "output_schema"} - raw.keys()
            if missing:
                raise ValueError(f"contract missing required fields: {sorted(missing)}")
            return cls(raw=raw, path=contract_path)

    def validate_input(contract: TaskContract, payload: dict[str, Any]) -> None:
        return None

    def validate_output(contract: TaskContract, payload: dict[str, Any]) -> None:
        return None


def load_contract(path: str | Path) -> TaskContract:
    """Load and validate a Runtime ABI contract through the sibling package."""
    return TaskContract.from_file(path)
