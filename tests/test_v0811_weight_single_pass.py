from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"
FRONTEND = INTEGRATION / "frontend"


def test_weight_ai_uses_original_v083_single_pass() -> None:
    route = (FRONTEND / "animal-health-panel.part29.js").read_text(encoding="utf-8")
    original = (INTEGRATION / "v083_features.py").read_text(encoding="utf-8")

    assert 'p?.mode==="weight"?`${D}/v083/ai/analyze`:type' in route
    assert 'p?.mode==="weight"?`${D}/v088/ai/analyze`:type' not in route
    assert "A handwritten list with nine animal " in original
    assert "Do not silently discard uncertain " in original
    assert 'task_name=f"animal_health_v083_{mode}_batch_extraction"' in original


def test_new_context_specific_ai_modes_stay_available() -> None:
    route = (FRONTEND / "animal-health-panel.part29.js").read_text(encoding="utf-8")
    frontend = "".join(
        path.read_text(encoding="utf-8")
        for path in sorted(FRONTEND.glob("animal-health-panel.part*.js"))
    )

    assert 'p?.mode==="weight"' in route
    assert 'data-action="ai-product-086"' in frontend
    assert 'data-action="ai-symptom-086"' in frontend
    assert "aiBatchSummary086" in frontend
    assert "aiBatchCommon086" in frontend
