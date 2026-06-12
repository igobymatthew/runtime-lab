from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

from runtime_lab.local_imports import add_sibling_import_paths

add_sibling_import_paths()

try:
    from afr.recorder import Recorder
except ImportError:  # pragma: no cover - only used before sibling repo exists.
    @dataclass
    class _Run:
        id: str = field(default_factory=lambda: str(uuid4()))

    class Recorder:  # type: ignore[no-redef]
        """TODO(agent-flight-recorder): Remove when the sibling package is importable."""

        def __init__(self, project: str | None = None, db_url: str = "sqlite:///afr.db") -> None:
            self.project = project
            self.db_url = db_url
            self.events: list[dict[str, Any]] = []
            self.artifacts: list[dict[str, Any]] = []

        def start_run(self, name: str | None = None, metadata: dict[str, Any] | None = None):
            run = _Run()
            self.record_event(run.id, "run.started", "run started", metadata=metadata)
            return run

        def complete_run(self, run_id: str, metadata: dict[str, Any] | None = None):
            self.record_event(run_id, "run.completed", "run completed", metadata=metadata)
            return _Run(id=run_id)

        def record_event(self, run_id: str, event_type: str, name: str, **kwargs: Any):
            event = {"id": str(uuid4()), "run_id": run_id, "event_type": event_type, "name": name}
            event.update(kwargs)
            self.events.append(event)
            return type("Event", (), event)

        def add_artifact(self, run_id: str, artifact_type: str, **kwargs: Any):
            artifact = {"run_id": run_id, "artifact_type": artifact_type}
            artifact.update(kwargs)
            self.artifacts.append(artifact)
            return artifact

        def export_run_jsonl(self, run_id: str, path: str | Path) -> Path:
            output = Path(path)
            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open("w", encoding="utf-8") as handle:
                handle.write(json.dumps({"record_type": "run", "data": {"id": run_id}}) + "\n")
                for event in self.events:
                    handle.write(json.dumps({"record_type": "event", "data": event}) + "\n")
                for artifact in self.artifacts:
                    handle.write(json.dumps({"record_type": "artifact", "data": artifact}) + "\n")
            return output

        def replay(self, run_id: str) -> dict[str, Any]:
            return {
                "run": {"id": run_id},
                "events": self.events,
                "failed_steps": [e for e in self.events if e.get("status") == "error"],
                "model_calls": [e for e in self.events if e["event_type"].startswith("model.call.")],
                "tool_calls": [e for e in self.events if e["event_type"].startswith("tool.call.")],
                "artifacts": self.artifacts,
                "eval_results": [
                    a for a in self.artifacts if a.get("artifact_type") == "eval_result"
                ],
            }
