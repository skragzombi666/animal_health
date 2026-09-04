from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "custom_components/animal_health/manifest.json"
README = ROOT / "README.md"
ANDROID_WORKFLOW = ROOT / ".github/workflows/android.yml"
RELEASE_NOTES = ROOT / "docs/version-0.9.42.md"
V0941_TEST = ROOT / "tests/test_v0941_release.py"
BRANDING_TEST = ROOT / "tests/test_branding_assets.py"
TEMP_WORKFLOW = ROOT / ".github/workflows/prepare-0942.yml"
THIS_SCRIPT = Path(__file__).resolve()
LEGACY_VERSION = "0.9.41"
RELEASE_VERSION = "0.9.42"

RELEASE_NOTES_TEXT = """# Animal Health 0.9.42

Version 0.9.42 ist ein Konsolidierungs-Checkpoint nach den schnellen Iterationen bis 0.9.41. Sie führt noch keinen neuen fachlichen Schreibpfad ein, sondern schafft eine überprüfbare technische Grundlage für die weitere Entwicklung.

## Konsolidierungs-Checkpoint

- Die bisherige Frontend-Struktur wurde vollständig inventarisiert und als maschinenlesbare Architektur-Baseline abgesichert.
- Die 99 nummerierten JavaScript-Fragmente bleiben als unveränderliche Legacy-Referenz von 0.9.41 erhalten. Neue nummerierte Fragmente sind gesperrt.
- Home Assistant und die eigenständige Android-App verwenden dasselbe reproduzierbar erzeugte Frontend-Bundle.
- Das Bundle beginnt weiterhin bytegenau mit dem eingefrorenen Legacy-Präfix und ergänzt danach genau eine gebündelte modulare Laufzeit.
- Neue Prototyp-Patches, zusätzliche Runtime-Patchregistrierungen und append-basiertes Rendering werden durch CI-Schutzregeln verhindert.

## Neue modulare Grundlage

0.9.42 enthält erstmals die neue fach- und komponentenbasierte Frontend-Struktur:

- Plattformadapter für Home Assistant und Android
- kanonischer API-Client und einheitliche camelCase-DTOs
- zentrale Fehlernormalisierung
- kanonischer Anwendungszustand und Store
- eigener Router mit Navigationsrevision
- explizite Aktionsregistry statt verteilter Ereignis-Patches
- kontrollierter Panel-Lebenszyklus und genau ein modularer Renderpfad
- eine einzige befristete routebasierte Legacy-Brücke

## Bereits modular aktive Routen

Die folgenden drei Lesepfade verwenden die neue Architektur:

- `overview`
- `animals`
- `animal-detail`

Die neue Übersicht und die Tieransichten verwenden ausschließlich normalisierte Daten. Gruppen-, Tag-, Such- und Archivfilter, Tierdetail-Ladevorgänge sowie der Schutz vor verspäteten Antworten sind zentral getestet.

## Weiterhin unverändert über Legacy

Aufgaben, Kalender, Chronik, Einstellungen und alle weiteren noch nicht migrierten Routen bleiben funktional im bisherigen Frontend. Sämtliche schreibenden Aktionen und Dialoge werden weiterhin ausschließlich über die vorhandenen Legacy-Handler ausgeführt. Es existiert kein paralleler Schreibpfad und keine doppelte Persistenz.

Nach einem Legacy-Schreibvorgang wird die aktive modulare Übersicht beziehungsweise Tierdetailansicht vollständig aktualisiert.

## Laufzeit-Härtung

- Rückkehr aus einer Legacy-Route rendert die modulare Route unmittelbar wieder.
- Suchfelder behalten nach vollständigem Neurendern Fokus und Cursorposition.
- DOM-Aktionsfehler werden kontrolliert normalisiert und erzeugen keine unbehandelten Promise-Ablehnungen.
- Ein Refresh der Tierdetailansicht aktualisiert sowohl das Verzeichnis als auch das konkrete Tierdetail.
- Veraltete Ergebnisse und Fehler einer bereits verlassenen Ansicht werden verworfen.

## Daten und Kompatibilität

- Keine Datenbankmigration
- Keine Änderung bestehender Home-Assistant-Services oder WebSocket-Commands
- Keine Änderung gespeicherter IDs oder Nutzdaten
- Keine Änderung der fachlichen Aufgaben- und Serienregeln aus 0.9.41
- Die eigenständige Android-App bleibt auf 0.9.0-alpha.7 und erhält dasselbe gemeinsame Frontend-Artefakt.

## Technische Absicherung

Der Release-Stand wird durch Architektur-Guardrails, reproduzierbare Bundle-Prüfung, modulare JavaScript-Vertragstests, die vollständige Python-Test-Suite, bestehende Smoke- und Regressionstests, Android-APK-Build, HACS Validation und hassfest abgesichert.

Die visuelle und interaktive Abnahme in einer realen Home-Assistant-Instanz und im Android-WebView folgt nach Veröffentlichung dieses Checkpoints.
"""


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(
            f"Expected exactly one occurrence in {path.relative_to(ROOT)}, found {count}: {old!r}"
        )
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def update_manifest() -> None:
    value = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if value.get("version") != LEGACY_VERSION:
        raise RuntimeError(f"Unexpected starting manifest version: {value.get('version')}")
    value["version"] = RELEASE_VERSION
    MANIFEST.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def update_readme() -> None:
    replace_once(
        README,
        "Die aktuelle Entwicklungsreihe 0.8.x umfasst unter anderem:\n",
        "Die aktuelle Version ist **0.9.42**. Sie ist ein Konsolidierungs-Checkpoint: Die Übersicht, die Tierliste und die Tier-Grundansicht verwenden bereits die neue modulare Architektur; alle übrigen Bereiche und sämtliche Schreibvorgänge bleiben während der kontrollierten Migration funktional über den bestehenden Legacy-Pfad erhalten.\n\nDer Funktionsumfang umfasst unter anderem:\n",
    )


def update_android_workflow() -> None:
    text = ANDROID_WORKFLOW.read_text(encoding="utf-8")
    anchor = '      - "custom_components/animal_health/frontend/**"\n'
    insertion = (
        anchor
        + '      - "custom_components/animal_health/manifest.json"\n'
        + '      - "docs/version-*.md"\n'
    )
    count = text.count(anchor)
    if count != 2:
        raise RuntimeError(f"Expected two Android workflow path anchors, found {count}")
    ANDROID_WORKFLOW.write_text(text.replace(anchor, insertion), encoding="utf-8")


def decouple_historical_frontend_marker_tests() -> None:
    changed = []
    for path in sorted((ROOT / "tests").rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        lines = []
        file_changed = False
        for line in text.splitlines(keepends=True):
            stripped = line.lstrip()
            if stripped.startswith("assert f'const V=") and (
                '{manifest["version"]}' in line or "{version}" in line
            ):
                line = line.replace("assert f'const V=", "assert 'const V=", 1)
                line = line.replace('{manifest["version"]}', LEGACY_VERSION)
                line = line.replace("{version}", LEGACY_VERSION)
                file_changed = True
            elif stripped.startswith('assert f"const V=') and (
                '{manifest["version"]}' in line or "{version}" in line
            ):
                line = line.replace('assert f"const V=', 'assert "const V=', 1)
                line = line.replace('{manifest["version"]}', LEGACY_VERSION)
                line = line.replace("{version}", LEGACY_VERSION)
                file_changed = True
            lines.append(line)
        if file_changed:
            path.write_text("".join(lines), encoding="utf-8")
            changed.append(path.relative_to(ROOT).as_posix())

    remaining = []
    for path in sorted((ROOT / "tests").rglob("*.py")):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if "const V=" in line and "assert f" in line:
                remaining.append(f"{path.relative_to(ROOT)}:{number}: {line.strip()}")
    if remaining:
        raise RuntimeError(
            "Unmigrated dynamic frontend version assertions:\n" + "\n".join(remaining)
        )
    print(f"Decoupled {len(changed)} historical frontend marker tests")


def update_historical_release_test() -> None:
    replace_once(
        V0941_TEST,
        '    assert manifest["version"] == "0.9.41"\n',
        '    assert tuple(map(int, manifest["version"].split("."))) >= (0, 9, 41)\n',
    )


def strengthen_branding_test() -> None:
    text = BRANDING_TEST.read_text(encoding="utf-8")
    marker = '    assert \'const V="0.9.41",D="animal_health"\' in frontend\n'
    if marker not in text:
        raise RuntimeError("Branding test did not receive the frozen marker assertion")
    addition = (
        marker
        + '    assert "version = _integration_version()" in panel\n'
        + '    assert "f\'const V=\\\"{version}\\\",D=\\\"animal_health\\\";\'" in panel\n'
    )
    BRANDING_TEST.write_text(text.replace(marker, addition, 1), encoding="utf-8")


def remove_temporary_automation() -> None:
    for path in (TEMP_WORKFLOW, THIS_SCRIPT):
        if path.exists():
            path.unlink()


def main() -> None:
    update_manifest()
    update_readme()
    update_android_workflow()
    RELEASE_NOTES.write_text(RELEASE_NOTES_TEXT, encoding="utf-8")
    decouple_historical_frontend_marker_tests()
    update_historical_release_test()
    strengthen_branding_test()
    remove_temporary_automation()
    print("Prepared Animal Health 0.9.42 release tree")


if __name__ == "__main__":
    main()
