from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runtime_lab.harness import export_latest_trace


if __name__ == "__main__":
    path = export_latest_trace()
    print(json.dumps({"trace_path": str(path)}, indent=2, sort_keys=True))
