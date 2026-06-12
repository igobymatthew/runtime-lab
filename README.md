# runtime-lab

Minimal deterministic integration harness for three sibling repos:

- `../bigset-local`
- `../AI-Runtime-ABI`
- `../agent-flight-recorder`

The harness does not copy sibling code. It imports `ai-runtime-abi` and `agent-flight-recorder`
directly when available, and includes a thin BigSet Local JSONL adapter because BigSet Local does
not currently expose a Python package.

## Setup

```powershell
python -m pip install -r requirements-local.txt
```

The scripts also add sibling source paths at runtime, so they can run from a checkout before editable
installs are configured.

## Required commands

```powershell
python scripts/run_local_pdf_demo.py
python scripts/export_trace.py
python scripts/replay_latest_trace.py
pytest
```

`python scripts/run_local_pdf_demo.py` runs the full loop:

1. Load BigSet-style JSONL cases.
2. Load and validate a Runtime ABI contract.
3. Run a deterministic fake agent for each case.
4. Record dataset, retrieval, model, eval, and error events into AFR.
5. Export the latest run to trace JSONL.
6. Replay the trace as a dry-run report.
7. Export failing cases in BigSet-compatible JSONL shape.
