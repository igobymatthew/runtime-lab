from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runtime_lab.harness import replay_latest_trace


if __name__ == "__main__":
    print(json.dumps(replay_latest_trace(), indent=2, sort_keys=True))
