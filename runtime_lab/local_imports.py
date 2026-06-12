from __future__ import annotations

import sys
from pathlib import Path


def add_sibling_import_paths() -> None:
    """Prefer editable installs, but allow direct sibling imports in a fresh checkout."""
    root = Path(__file__).resolve().parents[1]
    sibling_paths = [
        root.parent / "AI-Runtime-ABI",
        root.parent / "ai-runtime-abi",
        root.parent / "agent-flight-recorder" / "src",
    ]
    for path in sibling_paths:
        if path.exists():
            path_text = str(path)
            if path_text not in sys.path:
                sys.path.insert(0, path_text)
