from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = ROOT / "examples"
RUNS_DIR = ROOT / "runtime_lab_runs"
DEFAULT_DB_PATH = RUNS_DIR / "afr.sqlite"
LATEST_RUN_PATH = RUNS_DIR / "latest_run_id.txt"
LATEST_TRACE_PATH = EXAMPLES_DIR / "sample_trace.jsonl"
FAILURE_CASES_PATH = EXAMPLES_DIR / "failure_cases.jsonl"
SAMPLE_CASES_PATH = EXAMPLES_DIR / "sample_case.jsonl"
SAMPLE_CONTRACT_PATH = EXAMPLES_DIR / "sample_contract.json"
