from __future__ import annotations

from typing import Any


class FakeModelProvider:
    """Deterministic provider; no external APIs or model keys."""

    model_name = "fake-model-provider-v1"

    def complete(self, prompt: str, payload: dict[str, Any], provider_model: str) -> dict[str, Any]:
        question = str(payload.get("question", ""))
        document_text = str(payload.get("document_text", ""))
        lowered = f"{question}\n{document_text}".lower()
        if "alpha" in lowered:
            answer = "alpha"
            confidence = 0.99
        else:
            answer = "unknown"
            confidence = 0.20
        return {
            "answer": answer,
            "confidence": confidence,
            "evidence": [
                {
                    "source_id": str(payload.get("case_id", "case")),
                    "quote": document_text[:120],
                }
            ],
        }
