# Modulare Frontend-Quelle

Dieses Verzeichnis enthält den fach- und komponentenbasierten Neuaufbau des Animal-Health-Frontends.

## Status in Phase 3

Phase 3 ergänzt die hostneutrale Anwendungsshell aus Zustand, Store, Router, Controller, kontrolliertem Panel-Lebenszyklus und routebasierter Legacy-Brücke. Keine fachliche Route ist migriert. Die neuen Module sind nicht in das ausgelieferte Panel-Bundle eingebunden und verändern weder die Home-Assistant- noch die Android-Oberfläche.

Die neue Panelklasse wird ausschliesslich über eine injizierte Custom-Element-Registry explizit registriert. Der Import von `entry.js` registriert nichts und erzeugt keine globalen Seiteneffekte.

Das produktive Bundle bleibt bytegenau die Verkettung der 99 eingefrorenen Legacy-Fragmente des Referenzstands 0.9.41.

## Verbindliche Grenzen

- Zugriff auf `hass.callWS` und `hass.callService` nur in `platform/home-assistant-adapter.js`.
- Zugriff auf die Android-JavaScript-Bridge nur in `platform/android-adapter.js`.
- Versionierte WebSocket-Commands nur in `api/commands.js`.
- Historische Feldnamen und Aliasformen nur in `api/normalizers/`.
- App- und Fachmodule verwenden ausschliesslich kanonische camelCase-DTOs.
- Die DTO-Vertragsversion wird in `api/contracts.js` geführt.
- Keine Änderung von `AnimalHealthPanel.prototype`.
- Kein `shadowRoot.innerHTML +=` und keine nachträgliche Markup-Manipulation.
- Keine implizite Registrierung eines Custom Elements.
- Keine Zuweisung an `window` oder `globalThis`.
- Kein Zugriff des Routers auf `window.history`.
- Datumswerte ohne Uhrzeit bleiben `YYYY-MM-DD` und werden nicht über einen JavaScript-Datezeitpunkt umgerechnet.
- Keine Synchronisation zwischen historischem Legacy-Zustand und neuem Store.
- Keine fachliche Logik in der Legacy-Brücke.

## Öffentliche modulare Grenze

`entry.js` exportiert:

- `AnimalHealthClient` und `DTO_SCHEMA_VERSION`,
- die zentrale Command-Registry und stabile Fehlercodes,
- Home-Assistant- und Android-Transportadapter,
- öffentliche Normalisierer für Tiere, Aufgaben, Chronik, Produkte, Behandlungen und Einstellungen,
- `createInitialState` und `createStore`,
- `createRouter` und `createController`,
- `createAnimalHealthPanelClass` und `renderApplicationShell`,
- `createCompatibilityBridge`,
- `createAnimalHealthApplication`.

`createAnimalHealthApplication` komponiert die Module ohne DOM-, Netzwerk- oder Registrierungsnebenwirkungen. Die befristete Legacy-Brücke behandelt in Phase 3 jede Route als `legacy`, bis eine spätere vertikale Migration eine Route ausdrücklich als übernommen markiert.

## Zustands- und Lebenszyklusregeln

- Der Router verwendet einen eigenen Navigationsstapel.
- Jede tatsächliche Routenänderung erhöht die Navigationsrevision und schliesst einen offenen Dialog.
- Requesttokens sind an Request-ID und Navigationsrevision gebunden.
- Verspätete Antworten eines älteren Requests oder einer verlassenen Ansicht werden verworfen.
- Die Panelklasse bindet delegierte Listener für `click`, `change`, `input` und `submit` höchstens einmal.
- Store-Abonnements bestehen nur während der Verbindung des Elements.
- Markup wird über genau einen kontrollierten Renderpfad ersetzt.

## Lokale Prüfung

```bash
npm run check:frontend
npm run test:frontend
python -m pytest -q tests/test_frontend_phase2.py tests/test_frontend_phase3.py
python scripts/architecture_inventory.py --root . --check
node scripts/build_frontend.mjs --check
```
