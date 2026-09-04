# Gemeinsamer Frontend-Bundle-Vertrag

Die Home-Assistant-Integration und die eigenständige Android-App laden dasselbe eingecheckte Frontend-Artefakt:

```text
custom_components/animal_health/frontend/dist/animal-health-panel.js
```

Die 99 Dateien `animal-health-panel.part01.js` bis `animal-health-panel.part99.js` sind während Phase 0 und Phase 1 nur eingefrorene Legacy-Quellen des Referenzstands 0.9.41. Sie werden nicht mehr von Home Assistant oder Gradle zur Laufzeit gesucht, sortiert oder zusammengesetzt.

Ihre vorübergehend notwendige Reihenfolge ist vollständig und explizit in `custom_components/animal_health/frontend/legacy/manifest.json` festgelegt. `scripts/build_frontend.mjs` erzeugt daraus deterministisch das Dist-Bundle. `node scripts/build_frontend.mjs --check` weist ein fehlendes oder veraltetes Artefakt zurück.

Home Assistant liest nur das Dist-Bundle. Der Android-Build kopiert genau dieselben Bytes als `animal-health-panel.js` in die generierten App-Assets. `android-shared-ui.js` lädt ausschliesslich dieses Bundle.

Dieser Vertrag verhindert eine erneute Abhängigkeit von lexikografischer Fragmentreihenfolge und sichert zugleich den bisherigen Startmechanismus der Android-App. Die Legacy-Fragmente, das Manifest und die Übergangsbrücke werden nach vollständiger fachlicher Ablösung entfernt.
