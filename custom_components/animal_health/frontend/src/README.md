# Modulare Frontend-Quelle

Dieses Verzeichnis enthält den fach- und komponentenbasierten Neuaufbau des Animal-Health-Frontends.

## Status in Phase 4

Die ersten drei vollständigen Lesepfade sind im ausgelieferten Bundle aktiv:

- `overview`
- `animals`
- `animal-detail`

Diese Routen verwenden den kanonischen API-Client, Normalisierer, Store, Router, Controller, pure Selektoren und neue Viewmodule. Sie lesen ausschliesslich camelCase-DTOs.

Aufgaben, Kalender, Chronik, Einstellungen und alle übrigen Routen bleiben im Legacy-Frontend. Sämtliche Schreibaktionen bleiben ebenfalls Legacy-Aktionen. Die neuen Views können bestehende Dialoge wie Tier anlegen, Gewicht erfassen, Tier bearbeiten oder Status ändern öffnen; die Datenspeicherung wird aber vollständig vom gespeicherten Legacy-Handler durchgeführt. Es existiert kein zweiter Schreibpfad.

## Bundleaufbau

Das produktive Dist-Bundle besitzt zwei klar getrennte Teile:

1. das bytegenau unveränderte Präfix aus den 99 eingefrorenen Legacy-Fragmenten des Referenzstands 0.9.41;
2. eine mit `esbuild` erzeugte moderne IIFE nach dem Marker `ANIMAL_HEALTH_MODERN_RUNTIME`.

Home Assistant und Android verwenden weiterhin dasselbe eingecheckte Dist-Artefakt. HACS benötigt keine lokale Node- oder Buildumgebung.

## Verbindliche Grenzen

- Zugriff auf `hass.callWS` und `hass.callService` nur in `platform/home-assistant-adapter.js`.
- Zugriff auf die Android-JavaScript-Bridge nur in `platform/android-adapter.js`.
- Versionierte WebSocket-Commands nur in `api/commands.js`.
- Historische Feldnamen und Aliasformen nur in `api/normalizers/`.
- App-, Fach- und Viewmodule verwenden ausschliesslich kanonische camelCase-DTOs.
- Die DTO-Vertragsversion wird in `api/contracts.js` geführt.
- Keine neue nummerierte Frontend-Datei.
- Prototypzugriff für die Übergangsintegration nur in `legacy/compatibility-bridge.js`.
- Kein `shadowRoot.innerHTML +=` und keine nachträgliche Markup-Manipulation.
- Keine implizite Registrierung eines Custom Elements über `entry.js`.
- Keine Zuweisung an `window` oder `globalThis`.
- Kein Zugriff des Routers auf `window.history`.
- Datumswerte ohne Uhrzeit bleiben `YYYY-MM-DD` und werden nicht durch einen JavaScript-Datezeitpunkt verschoben.
- Keine Synchronisation historischer Zustandscontainer mit dem neuen Store.
- Keine Fach- oder Viewlogik in der Legacy-Brücke.
- Keine schreibenden Serviceaufrufe aus `app/read-only-animals.js` oder `ui/views/`.

## Aktiver Datenfluss

```text
Home Assistant oder Android-Hass-Adapter
→ AnimalHealthClient
→ kanonische Normalisierer
→ Phase-3-Store
→ Tierselektoren
→ overview / animals / animal-detail
```

Verzeichnisdaten werden beim ersten Öffnen geladen und bei ausdrücklichem Refresh aktualisiert. Tierdetails werden getrennt geladen. Request-ID und Navigationsrevision verhindern, dass eine ältere Antwort den Zustand einer inzwischen gewechselten Tieransicht überschreibt.

## Übergang zu Legacy

`legacy/compatibility-bridge.js` ist der einzige Installationspunkt am finalen Legacy-Prototyp. Die Brücke entscheidet nach vollständiger Route:

- die drei oben genannten Routen verwenden den neuen Renderer;
- ein offener Legacy-Dialog verwendet immer den vollständigen Legacy-Renderer;
- eine Navigation auf eine nicht migrierte Route verwendet den Legacy-Renderer;
- eine Schreibaktion lädt bei Bedarf den Legacy-Zustand und ruft danach den ursprünglichen Handler auf;
- nach erfolgreichem Legacy-Schreiben wird der neue Verzeichniszustand aktualisiert.

## Öffentliche modulare Grenze

`entry.js` exportiert unter anderem:

- `AnimalHealthClient` und `DTO_SCHEMA_VERSION`,
- Plattformadapter, Fehlercodes und Normalisierer,
- `createInitialState`, `createStore`, `createRouter` und `createController`,
- `createAnimalHealthApplication`,
- `createReadOnlyAnimalsRuntime`,
- `renderReadOnlyAnimalsRoute`,
- `installLegacyReadOnlyAnimalsSlice`,
- Tierselektoren und die drei Routenrenderer.

Der Import von `entry.js` bleibt nebenwirkungsfrei. Nur `runtime-entry.js` aktiviert den produktiven Übergang und wird ausschliesslich vom Bundlebuilder eingebunden.

## Lokale Prüfung

```bash
npm install --no-package-lock
npm run build:frontend
npm run check:frontend
npm run test:frontend
python -m pytest -q tests/test_frontend_phase2.py tests/test_frontend_phase3.py tests/test_frontend_phase4.py
python scripts/architecture_inventory.py --root . --check
node scripts/build_frontend.mjs --check
```
