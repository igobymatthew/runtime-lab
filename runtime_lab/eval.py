from __future__ import annotations

from typing import Any


def evaluate_output(expected: dict[str, Any], output: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    for key, expected_value in expected.items():
        actual_value = output.get(key)
        if actual_value != expected_value:
            failures.append(f"expected {key}={expected_value!r}, got {actual_value!r}")
    return {"passed": not failures, "failures": failures, "expected": expected, "actual": output}
