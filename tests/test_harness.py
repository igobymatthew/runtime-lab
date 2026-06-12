from __future__ import annotations

import json

from runtime_lab.adapters.bigset_local import read_cases_jsonl
from runtime_lab.harness import replay_latest_trace, run_full_loop
from runtime_lab.paths import FAILURE_CASES_PATH, LATEST_TRACE_PATH, SAMPLE_CASES_PATH


def test_bigset_adapter_reads_jsonl_cases() -> None:
    cases = read_cases_jsonl(SAMPLE_CASES_PATH)
    assert [case["id"] for case in cases] == ["case-pass-alpha", "case-fail-beta"]


def test_full_loop_records_trace_and_exports_failures() -> None:
    summary = run_full_loop()
    assert {result["passed"] for result in summary["results"]} == {True, False}
    assert LATEST_TRACE_PATH.exists()
    assert FAILURE_CASES_PATH.exists()

    records = [
        json.loads(line)
        for line in LATEST_TRACE_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    events = [record["data"] for record in records if record["record_type"] == "event"]
    event_types = {event["event_type"] for event in events}
    assert "model.call.started" in event_types
    assert "model.call.completed" in event_types
    assert "retrieval.completed" in event_types
    assert "eval.completed" in event_types
    assert "error" in event_types
    assert "contract.validation.completed" in event_types

    failures = [
        json.loads(line)
        for line in FAILURE_CASES_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(failures) == 1
    assert failures[0]["id"] == "case-fail-beta-failure"
    assert {"id", "task", "input", "expected", "metadata"} <= failures[0].keys()


def test_replay_latest_trace_is_dry_run_report() -> None:
    run_full_loop()
    report = replay_latest_trace()
    assert report["event_count"] >= 8
    assert report["model_calls"]
    assert report["retrieval_events"]
    assert report["eval_events"]
    assert report["error_events"]
