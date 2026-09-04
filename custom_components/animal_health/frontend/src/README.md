# Modulare Frontend-Quelle

Dieses Verzeichnis enthält den fach- und komponentenbasierten Neuaufbau des Animal-Health-Frontends.

## Status in Phase 2

Die Module definieren ausschliesslich Plattformadapter, den API-Client, stabile Fehler und kanonische DTO-Normalisierer. Sie sind noch nicht in das ausgelieferte Panel-Bundle eingebunden und verändern keine bestehende Benutzeroberfläche.

Das produktive Bundle bleibt bis Phase 3 die exakte Reproduktion des eingefrorenen Referenzstands 0.9.41.

## Verbindliche Grenzen

- Zugriff auf `hass.callWS` und `hass.callService` nur in `platform/home-assistant-adapter.js`.
- Zugriff auf die Android-JavaScript-Bridge nur in `platform/android-adapter.js`.
- Versionierte WebSocket-Commands nur in `api/commands.js`.
- Historische Feldnamen und Aliasformen nur in `api/normalizers/`.
- Fachmodule und spätere Views verwenden ausschliesslich kanonische camelCase-DTOs.
- Keine Änderung von `AnimalHealthPanel.prototype`.
- Kein `shadowRoot.innerHTML +=`.
- Keine Registrierung eines Custom Elements vor Phase 3.
- Keine Zuweisung an `window` oder `globalThis`.
- Datumswerte ohne Uhrzeit bleiben `YYYY-MM-DD` und werden nicht über einen JavaScript-Datezeitpunkt umgerechnet.
- Keine neue Abhängigkeit vom eingefrorenen Legacy-Zustand.

## Öffentliche Phase-2-Grenze

`entry.js` exportiert:

- `AnimalHealthClient`,
- die zentrale Command-Registry,
- stabile Fehlercodes,
- Home-Assistant- und Android-Transportadapter,
- öffentliche Normalisierer für Tiere, Aufgaben, Chronik, Produkte, Behandlungen und Einstellungen.

Der Import von `entry.js` ist nebenwirkungsfrei.

## Lokale Prüfung

```bash
npm run check:frontend
npm run test:frontend
python -m pytest -q tests/test_frontend_phase2.py
python scripts/architecture_inventory.py --root . --check
node scripts/build_frontend.mjs --check
```
