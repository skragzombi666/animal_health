# Phase 3 – Application Shell Design

**Status:** Freigegeben durch die Anweisung zur Umsetzung der nächsten Konsolidierungsphase  
**Basis:** `consolidation/phase-2-platform-api`  
**Zielstand:** struktureller App-Kern ohne Aktivierung einer neuen Benutzeroberfläche

## 1. Ziel

Phase 3 baut den hostunabhängigen Anwendungskern des neuen modularen Frontends auf. Sie führt Store, Router, Controller, Panel-Lebenszyklus, kontrolliertes Rendering und die befristete Legacy-Brücke ein. Noch keine fachliche Route wird aus dem eingefrorenen 0.9.41-Frontend übernommen.

Die ausgelieferte Home-Assistant- und Android-Oberfläche bleibt unverändert. Das bestehende Dist-Bundle muss weiterhin bytegenau aus den 99 Legacy-Fragmenten reproduzierbar sein.

## 2. Verbindliche Grenzen

- Keine sichtbare UI-Änderung.
- Keine Änderung bestehender Backend-Commands, Services oder Datenbanken.
- Keine Änderung gespeicherter IDs oder Nutzdaten.
- Keine Änderung der 99 eingefrorenen Legacy-Fragmente oder ihres Manifests.
- Keine neue externe JavaScript-Abhängigkeit.
- Kein Zugriff fachlicher oder App-Module auf `hass`, Android-Bridge, `window.history` oder andere Hostglobals.
- Kein `shadowRoot.innerHTML +=`, keine nachträgliche Markup-Manipulation und keine Prototyp-Patchkette.
- Der Import von `frontend/src/entry.js` bleibt nebenwirkungsfrei.
- Die neue Panelklasse wird in Phase 3 nicht automatisch als Custom Element registriert.

## 3. Struktur

```text
custom_components/animal_health/frontend/src/
├── app/
│   ├── application.js
│   ├── animal-health-panel.js
│   ├── controller.js
│   ├── router.js
│   ├── state.js
│   └── store.js
├── legacy/
│   └── compatibility-bridge.js
└── entry.js
```

Die Phase erweitert die bereits vorhandene Plattform- und API-Grenze aus Phase 2. Der Anwendungskern arbeitet ausschliesslich mit `AnimalHealthClient`, dem Transportvertrag und kanonischen DTOs.

## 4. Kanonischer Zustand

`state.js` erzeugt einen vollständigen Anfangszustand mit folgenden Bereichen:

- `platform`: Hosttyp, Verfügbarkeit und enge Hostmetadaten.
- `language`: aktive Sprache und Locale.
- `navigation`: aktuelle Route, eigener Routenstapel und monotone Revision.
- `dialog`: geschlossener oder geöffneter Dialog mit Typ und Daten.
- `animals`, `timeline`, `tasks`, `products`, `treatments`, `settings`: fachliche Datenbereiche.
- `drafts`: formularbezogene Entwürfe.
- `requests`: laufende und abgeschlossene Requestzustände.
- `notifications`: interne Benachrichtigungen.

Eingangsobjekte werden nicht mutiert. Zustandsteile werden beim Erzeugen kopiert. Die Struktur enthält keine historischen Aliasfelder.

## 5. Store und Schutz vor verspäteten Antworten

`store.js` stellt genau diese öffentliche Grenze bereit:

```javascript
getState()
update(updateOrPatch)
subscribe(listener)
beginRequest(key)
commitRequest(token, updateOrPatch)
failRequest(token, error)
isCurrentRequest(token)
```

Jeder Requesttoken enthält einen monotonen Requestzähler und die Navigationsrevision beim Start. `commitRequest` und `failRequest` verändern den Zustand nur, wenn sowohl Request-ID als auch Navigationsrevision noch aktuell sind. Eine Antwort aus einer verlassenen Ansicht kann dadurch den aktuellen Zustand nicht überschreiben.

Listener werden nur bei einer tatsächlichen Zustandsänderung benachrichtigt. `subscribe` liefert eine idempotente Abmeldefunktion.

## 6. Router und Dialogzustand

`router.js` verwaltet Navigation ohne `window.history`:

```javascript
current()
navigate(route, options)
replace(route)
back()
openDialog(type, data)
closeDialog()
```

Eine Route besteht aus einem stabilen Namen und kanonischen Parametern. `navigate` legt die vorherige Route auf einen internen Stapel. `replace` ersetzt nur die aktuelle Route. `back` verwendet ausschliesslich den internen Stapel; am Wurzelpunkt ist es ein No-op. Jede tatsächliche Routenänderung erhöht `navigation.revision` und schliesst einen offenen Dialog.

## 7. Controller und Aktionsregistry

`controller.js` enthält genau eine Aktionsregistry. Aktionen werden anhand stabiler `data-action`-Namen aufgelöst. Es gibt keine überschreibbaren `handleClick`-, `handleChange`-, `handleSubmit`- oder `render`-Ketten.

Öffentliche Grenze:

```javascript
register(name, handler)
unregister(name)
dispatch(name, context)
handleEvent(event)
runLatest(key, operation, applyResult)
```

Doppelte Registrierung ist ein Fehler. Unbekannte Aktionen werden kontrolliert ignoriert und liefern `false`. Fehler aus Aktionshandlern werden über die Phase-2-Fehlergrenze normalisiert und als Requestfehler gespeichert. `runLatest` verwendet die Requesttokens des Stores und verwirft verspätete Ergebnisse.

Die Registry enthält nur strukturelle Standardaktionen:

- `app.navigate`
- `app.back`
- `dialog.open`
- `dialog.close`

Fachliche Aktionen werden erst mit der jeweiligen vertikalen Migration registriert.

## 8. Panel-Lebenszyklus und Rendering

`animal-health-panel.js` exportiert eine Factory für die neue Panelklasse. Abhängigkeiten werden explizit injiziert, damit das Modul in Node ohne Browser-DOM importierbar und testbar bleibt.

Die erzeugte Panelklasse:

- verwaltet genau einen Shadow Root,
- bindet delegierte Listener für `click`, `change`, `input` und `submit` höchstens einmal,
- abonniert den Store beim Verbinden und meldet sich beim Trennen ab,
- besitzt genau einen kontrollierten Renderpfad,
- ersetzt Markup nur über `shadowRoot.innerHTML = ...`, niemals per Append,
- delegiert Ereignisse ausschliesslich an den Controller.

Der Phase-3-Standardrenderer erzeugt nur eine neutrale, nicht aktivierte Shell-Markierung mit Route, Dialog- und Requeststatus. Er enthält keine neue fachliche Ansicht und kein visuelles Redesign.

## 9. Anwendungskomposition

`application.js` erzeugt aus einem vorhandenen Transport:

- `AnimalHealthClient`,
- Anfangszustand,
- Store,
- Router,
- Controller,
- Legacy-Brücke,
- Panelklasse.

Die Factory registriert nichts global und verändert weder DOM noch Hostzustand. Für spätere Aktivierungsphasen stellt sie eine explizite `define(registry, tagName)`-Funktion bereit. Diese erhält das Custom-Element-Registry-Objekt als Parameter und wird in Phase 3 nicht aufgerufen.

## 10. Befristete Legacy-Brücke

`legacy/compatibility-bridge.js` kennt nur den Migrationsstatus ganzer Routen oder vollständiger Anwendungsfälle.

Öffentliche Grenze:

```javascript
modeFor(routeName)
markMigrated(routeName)
markLegacy(routeName)
delegate(routeName, context)
```

Standard ist `legacy`. Nur explizit migrierte Routen werden an den neuen Delegate gesendet. Die Brücke sammelt keine Daten aus alten Zustandscontainern, synchronisiert keine alten und neuen Zustände und enthält keine Fachlogik.

In Phase 3 ist keine Route migriert. Die Brücke ist vorhanden und getestet, aber nicht mit dem produktiven Legacy-Panel verbunden.

## 11. Einstiegspunkt

`entry.js` exportiert zusätzlich:

- `createAnimalHealthApplication`
- `createInitialState`
- `createStore`
- `createRouter`
- `createController`
- `createAnimalHealthPanelClass`
- `renderApplicationShell`
- `createCompatibilityBridge`

Der Import bleibt vollständig nebenwirkungsfrei.

## 12. Tests und CI

Neue Node-Tests prüfen:

1. Anfangszustand und Nichtmutation der Eingaben.
2. Store-Updates, Subscription und Abmeldung.
3. Verwerfen verspäteter Requestantworten nach neuerem Request oder Navigation.
4. Routerstapel, Replace, Back und Dialogschliessung.
5. Aktionsregistry, unbekannte Aktionen, strukturelle Standardaktionen und Fehlernormalisierung.
6. Einmalige Ereignisbindung und kontrollierten Renderpfad der Panelklasse mit einem Fake-DOM-Host.
7. Routebasierte Legacy-Brücke ohne Zustands-Synchronisation.
8. Nebenwirkungsfreie Anwendungskomposition und explizite, idempotente Registrierung.

Die statischen Phase-2-Grenzen werden erweitert:

- `app/` und `legacy/compatibility-bridge.js` dürfen nicht auf `hass`, Android-Bridge oder `window.history` zugreifen.
- `customElements.define` darf nicht direkt verwendet werden.
- Neue App-Dateien müssen vorhanden sein.
- Das Dist-Bundle bleibt bytegenau die Legacy-Referenz.

Die bestehenden Validate-, Android-Alpha-, HACS- und hassfest-Workflows bleiben verbindlich.

## 13. Abnahmekriterien

Phase 3 ist erfüllt, wenn:

- alle beschriebenen App-Module vorhanden und einzeln testbar sind,
- Store, Router und Controller ausschliesslich über explizite Schnittstellen gekoppelt sind,
- verspätete Antworten nach Navigation oder einem neueren Request verworfen werden,
- die Panelklasse Listener höchstens einmal bindet,
- kein Import globale Seiteneffekte erzeugt,
- keine fachliche Route aktiviert wurde,
- das produktive Bundle und alle 99 Legacy-Fragmente unverändert bleiben,
- sämtliche Node-, Python-, Smoke-, Android-, HACS- und hassfest-Prüfungen erfolgreich sind.
