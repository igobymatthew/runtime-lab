from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from runtime_lab.adapters.bigset_local import read_cases_jsonl, write_failure_cases_jsonl
from runtime_lab.adapters.flight_recorder import Recorder
from runtime_lab.adapters.runtime_abi import load_contract, validate_input, validate_output
from runtime_lab.eval import evaluate_output
from runtime_lab.fake_agent import FakeModelProvider
from runtime_lab.paths import (
    DEFAULT_DB_PATH,
    FAILURE_CASES_PATH,
    LATEST_RUN_PATH,
    LATEST_TRACE_PATH,
    RUNS_DIR,
    SAMPLE_CASES_PATH,
    SAMPLE_CONTRACT_PATH,
)


def db_url() -> str:
    return f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"


def run_full_loop(
    cases_path: Path = SAMPLE_CASES_PATH,
    contract_path: Path = SAMPLE_CONTRACT_PATH,
    trace_path: Path = LATEST_TRACE_PATH,
    failure_cases_path: Path = FAILURE_CASES_PATH,
) -> dict[str, Any]:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)

    recorder = Recorder(project="runtime-lab", db_url=db_url())
    contract = load_contract(contract_path)
    cases = read_cases_jsonl(cases_path)
    provider = FakeModelProvider()
    run = recorder.start_run(
        name="local-pdf-demo",
        metadata={
            "contract": str(contract_path),
            "cases": str(cases_path),
            "fake_provider": provider.model_name,
        },
    )

    failure_cases: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []

    recorder.record_event(
        run.id,
        "contract.validation.completed",
        "runtime abi contract validation completed",
        input_json={"path": str(contract_path)},
        output_json={"task": contract.task, "version": contract.version},
    )

    for case in cases:
        case_id = str(case["id"])
        input_payload = {**case["input"], "case_id": case_id}
        recorder.record_event(
            run.id,
            "dataset.case.loaded",
            "bigset local case loaded",
            output_json={"id": case_id, "task": case.get("task")},
        )
        recorder.add_artifact(
            run.id,
            "dataset_case",
            content_json=case,
            metadata={"source": "bigset-local-jsonl"},
        )

        try:
            validate_input(contract, input_payload)
            retrieval_event = recorder.record_event(
                run.id,
                "retrieval.completed",
                "local document retrieval completed",
                input_json={"case_id": case_id},
                output_json={
                    "documents": [
                        {
                            "source_id": case_id,
                            "text": input_payload.get("document_text", ""),
                        }
                    ]
                },
            )

            prompt = _build_prompt(case["input"])
            model_event = recorder.record_event(
                run.id,
                "model.call.started",
                "fake model call started",
                input_json={"prompt": prompt, "payload": input_payload},
                metadata={"provider": provider.model_name},
            )
            output = provider.complete(prompt, input_payload, provider.model_name)
            validate_output(contract, output)
            recorder.record_event(
                run.id,
                "model.call.completed",
                "fake model call completed",
                output_json=output,
                parent_event_id=model_event.id,
                metadata={"provider": provider.model_name},
            )

            eval_result = evaluate_output(case["expected"], output)
            status = "ok" if eval_result["passed"] else "error"
            eval_event = recorder.record_event(
                run.id,
                "eval.completed",
                "deterministic eval completed",
                input_json={"case_id": case_id, "expected": case["expected"]},
                output_json=eval_result,
                parent_event_id=retrieval_event.id,
                status=status,
            )
            recorder.add_artifact(
                run.id,
                "eval_result",
                event_id=eval_event.id,
                content_json=eval_result,
                metadata={"case_id": case_id},
            )

            result = {"case_id": case_id, "passed": eval_result["passed"], "output": output}
            results.append(result)
            if not eval_result["passed"]:
                recorder.record_event(
                    run.id,
                    "error",
                    "case failed deterministic eval",
                    error_json={"case_id": case_id, "failures": eval_result["failures"]},
                    status="error",
                )
                failure_cases.append(_failure_case(case, output, eval_result))
        except Exception as exc:
            recorder.record_event(
                run.id,
                "error",
                "case raised exception",
                input_json={"case_id": case_id},
                error_json={"type": type(exc).__name__, "message": str(exc)},
                status="error",
            )
            failure_cases.append(
                _failure_case(
                    case,
                    {},
                    {"passed": False, "failures": [f"{type(exc).__name__}: {exc}"]},
                )
            )

    failure_path = write_failure_cases_jsonl(failure_cases, failure_cases_path)
    recorder.add_artifact(
        run.id,
        "file_snapshot",
        uri=str(failure_path),
        metadata={"kind": "bigset-compatible-failure-cases", "count": len(failure_cases)},
    )
    completed = recorder.complete_run(
        run.id,
        metadata={
            "passed": sum(1 for result in results if result["passed"]),
            "failed": len(failure_cases),
        },
    )
    exported_trace = recorder.export_run_jsonl(completed.id, trace_path)
    LATEST_RUN_PATH.write_text(completed.id, encoding="utf-8")
    replay = recorder.replay(completed.id)

    return {
        "run_id": completed.id,
        "trace_path": str(exported_trace),
        "failure_cases_path": str(failure_path),
        "results": results,
        "replay": {
            "event_count": len(replay["events"]),
            "model_call_count": len(replay["model_calls"]),
            "failed_step_count": len(replay["failed_steps"]),
            "eval_result_count": len(replay["eval_results"]),
        },
    }


def export_latest_trace(trace_path: Path = LATEST_TRACE_PATH) -> Path:
    run_id = LATEST_RUN_PATH.read_text(encoding="utf-8").strip()
    recorder = Recorder(project="runtime-lab", db_url=db_url())
    return recorder.export_run_jsonl(run_id, trace_path)


def replay_latest_trace(trace_path: Path = LATEST_TRACE_PATH) -> dict[str, Any]:
    records = []
    with trace_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    events = [record["data"] for record in records if record["record_type"] == "event"]
    artifacts = [record["data"] for record in records if record["record_type"] == "artifact"]
    return {
        "trace_path": str(trace_path),
        "event_count": len(events),
        "model_calls": [event["name"] for event in events if event["event_type"].startswith("model.call.")],
        "retrieval_events": [
            event["name"] for event in events if event["event_type"].startswith("retrieval.")
        ],
        "eval_events": [event["name"] for event in events if event["event_type"].startswith("eval.")],
        "error_events": [event["name"] for event in events if event["event_type"] == "error"],
        "eval_artifact_count": sum(
            1 for artifact in artifacts if artifact["artifact_type"] == "eval_result"
        ),
    }


def _build_prompt(case_input: dict[str, Any]) -> str:
    return (
        "Answer the question from the local document only.\n"
        f"Question: {case_input.get('question', '')}\n"
        f"Document: {case_input.get('document_text', '')}"
    )


def _failure_case(
    case: dict[str, Any], output: dict[str, Any], eval_result: dict[str, Any]
) -> dict[str, Any]:
    return {
        "id": f"{case['id']}-failure",
        "task": case.get("task"),
        "input": case["input"],
        "expected": case["expected"],
        "metadata": {
            **case.get("metadata", {}),
            "source_case_id": case["id"],
            "actual_output": output,
            "eval_failures": eval_result.get("failures", []),
        },
    }
