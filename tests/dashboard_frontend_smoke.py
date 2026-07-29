from __future__ import annotations

import ast
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "animal_health"
FRONTEND = INTEGRATION / "frontend"
PANEL_BACKEND = INTEGRATION / "panel.py"
DASHBOARD_API = INTEGRATION / "dashboard_api.py"
INIT = INTEGRATION / "__init__.py"
MANIFEST = INTEGRATION / "manifest.json"


def _read(path: Path) -> str:
    content = path.read_text(encoding="utf-8")
    assert content.strip(), f"{path} is empty"
    return content


def _panel_source() -> str:
    parts = sorted(FRONTEND.glob("animal-health-panel.part*.js"))
    assert parts, "Animal Health frontend source parts are missing"
    assert [path.name for path in parts] == [
        f"animal-health-panel.part{index:02d}.js"
        for index in range(1, len(parts) + 1)
    ]
    return "".join(_read(path) for path in parts)


def main() -> None:
    panel = _panel_source()
    backend = _read(PANEL_BACKEND)
    api = _read(DASHBOARD_API)
    init = _read(INIT)
    manifest = _read(MANIFEST)

    for source in (backend, api, init):
        ast.parse(source)

    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8") as file:
        file.write(panel)
        file.flush()
        subprocess.run(["node", "--check", file.name], check=True)

    assert 'customElements.define("animal-health-panel"' in panel
    assert 'const V="0.7.0",D="animal_health"' in panel
    assert "mdi:paw-plus" in panel
    for task_kind in (
        "medication",
        "vaccination",
        "health_check",
        "care",
        "veterinary_visit",
    ):
        assert f'data-kind="{task_kind}"' in panel
    assert "syncTask" in panel
    assert "syncExec" in panel
    assert "planned_custom_vaccination_target" in panel

    for command in ("${D}/dashboard", "${D}/animal_detail", "${D}/catalog"):
        assert command in panel

    for service in (
        "create_animal",
        "update_animal",
        "set_animal_status",
        "archive_animal",
        "restore_animal",
        "record_weight",
        "record_symptom",
        "create_event",
        "create_record_task",
        "record_task_reminder",
        "record_task_weight",
        "record_task_medication",
        "record_task_vaccination",
        "record_task_health_check",
        "record_task_care",
        "record_task_veterinary_visit",
        "skip_task_occurrence",
        "cancel_task_occurrence",
        "set_task_active",
    ):
        assert service in panel, f"Missing dashboard service: {service}"

    for external_marker in ("http://", "https://", "unpkg", "jsdelivr", "cdnjs"):
        assert external_marker not in panel.lower(), (
            "The dashboard must not depend on external frontend resources: "
            f"{external_marker}"
        )

    assert 'PANEL_URL_PATH = "animal-health"' in backend
    assert "AnimalHealthPanelView" in backend
    assert "async_register_built_in_panel" in backend
    assert "async_setup_dashboard_api" in init
    assert "async_register_panel" in init
    assert '"frontend"' in manifest and '"http"' in manifest
    assert '"version": "0.7.0"' in manifest

    for command_name in (
        '_DASHBOARD_COMMAND = f"{DOMAIN}/dashboard"',
        '_ANIMAL_DETAIL_COMMAND = f"{DOMAIN}/animal_detail"',
        '_CATALOG_COMMAND = f"{DOMAIN}/catalog"',
    ):
        assert command_name in api

    print("Animal Health dashboard frontend validation passed")


if __name__ == "__main__":
    main()
