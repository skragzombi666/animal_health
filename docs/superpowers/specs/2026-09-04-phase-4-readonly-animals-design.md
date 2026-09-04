# Phase 4 – Read-only Animal Slice Design

**Status:** Freigegeben durch die Anweisung zur Umsetzung des nächsten Konsolidierungsschritts  
**Basis:** `consolidation/phase-3-app-shell`  
**Aktivierte Routen:** `overview`, `animals`, `animal-detail`

## 1. Ziel

Phase 4 aktiviert erstmals einen vollständigen vertikalen Ausschnitt der neuen modularen Oberfläche. Die Übersicht, die Tierliste und die Tier-Grundansicht verwenden den Phase-2-API-Client, kanonische DTOs, den Phase-3-Store, den Router und den Controller.

Alle übrigen Routen und sämtliche Schreibvorgänge bleiben im eingefrorenen Legacy-Frontend. Die drei neuen Routen dürfen weder alte Zustandscontainer noch rohe Backend-Aliasfelder lesen.

## 2. Gewählter Migrationsansatz

Gewählt wird eine routebasierte Strangler-Integration in das bestehende Custom Element.

Das ausgelieferte Bundle besteht künftig aus:

```text
unveränderter Legacy-Prelude aus part01.js bis part99.js
+
mit esbuild erzeugte moderne IIFE
+
kleiner Aktivierungsaufruf innerhalb derselben Scriptdatei
```

Die moderne IIFE installiert genau eine befristete Kompatibilitätsbrücke auf der finalen Legacy-Klasse. Diese Brücke ersetzt nicht einzelne Fachmethoden, sondern entscheidet vollständig pro Route:

- `overview`, `animals`, `animal-detail` → neuer modularer Pfad
- alle anderen Routen → unveränderter Legacy-Pfad
- geöffneter Legacy-Dialog → unveränderter Legacy-Renderer

Die 99 Fragmente bleiben unverändert. Die neue Implementierung wird nicht als weiteres Fragment angelegt.

## 3. Verworfene Ansätze

### Vollständiger Wechsel auf die neue Panelklasse

Die Phase-3-Panelklasse könnte das bestehende Custom Element vollständig ersetzen. Dann müssten jedoch gleichzeitig alle nicht migrierten Routen, Dialoge und Schreibvorgänge eingebettet oder neu implementiert werden. Das wäre ein Big-Bang-Wechsel und widerspricht der Strangler-Migration.

### Einzelne Legacy-Methoden fachlich weiterpatchen

Die drei Ansichten könnten durch zusätzliche verstreute Überschreibungen von `overview()`, `animals()` und `animalDetail()` ersetzt werden. Das würde die bestehende Patcharchitektur fortsetzen. Stattdessen existiert genau ein Installationspunkt in `legacy/compatibility-bridge.js`.

### Neue Oberfläche nur vorbereiten, aber nicht aktivieren

Phase 2 und Phase 3 haben bewusst inaktive Grundlagen geschaffen. Der nächste sinnvolle Nachweis ist eine echte vertikale Route. Ein weiterer rein inaktiver Schritt würde das Integrationsrisiko nur verschieben.

## 4. Sichtbarer Umfang

### 4.1 Gemeinsame Shell

Die drei neuen Routen besitzen eine gemeinsame Shell mit:

- Animal-Health-Kopfzeile,
- Navigation zu Übersicht, Tiere, Aufgaben, Kalender und Chronik,
- Aktualisieren-Aktion,
- Lade-, Leer- und Fehlerzustand,
- responsivem Layout über bestehende Home-Assistant-Designvariablen,
- Klassenbezeichnungen, die mit den vorhandenen Android-Anpassungen kompatibel bleiben, soweit fachlich sinnvoll.

Aufgaben, Kalender und Chronik navigieren weiterhin in die Legacy-Oberfläche.

### 4.2 Übersicht

Die neue Übersicht zeigt:

- aktive Tiere,
- überfällige Aufgabeninstanzen,
- heute fällige Aufgabeninstanzen,
- offene Aufgabeninstanzen,
- vorhandene Schnellaktionen,
- Tiere nach primärer Tiergruppe,
- Tiere ohne Gruppe,
- Gruppenfilter,
- Tagfilter,
- Tier-Suche,
- Filter zurücksetzen,
- überfällige und heute fällige Aufgabeninstanzen,
- letzte Chronikereignisse.

Die Tierfilter bleiben für die aktuelle Panel-Laufzeit erhalten. Eine Persistenz in `localStorage` wird nicht in die neue Architektur übernommen. Das ist bewusst, weil Host-Storage ausserhalb der definierten Plattformgrenze liegt. Eine spätere persistente Benutzereinstellung erhält einen eigenen fachlichen Vertrag.

### 4.3 Tierliste

Die Tierliste zeigt:

- Suchfeld,
- aktive und archivierte Tiere,
- Name, Tierart, Rasse und Status,
- primäre Tiergruppe und Tags,
- aktuelles Gewicht,
- nächste offene Aufgabeninstanz,
- Öffnen der Tier-Grundansicht.

Die Sortierung erfolgt stabil nach Archivstatus und Tiername. Die Suche berücksichtigt Name, Tierart, Rasse, Farbe, Status, Gruppenname, Tags und technische ID.

### 4.4 Tier-Grundansicht

Die Tier-Grundansicht zeigt:

- Name, Tierart, Rasse und Status,
- primäre Tiergruppe und Tags,
- aktuelles Gewicht,
- Anzahl offener Aufgabeninstanzen,
- Geburtsdatum und technische ID,
- Stammdaten,
- überfällige, heute fällige und kommende Aufgabeninstanzen,
- letzte Chronikereignisse,
- vorhandene Schnell- und Verwaltungsaktionen.

Chronikereignisse werden in dieser Phase kompakt und ereigniszentriert angezeigt. Herkunft aus einer Aufgabe und Gruppenziel werden als sekundäre Metadaten dargestellt. Attachment-Vorschau und ausführliche Chronikdetails bleiben dem Legacy-Pfad beziehungsweise einer späteren Chronik-/Attachment-Migration vorbehalten.

## 5. Schreibaktionen und Legacy-Fallback

Die neuen Views erzeugen selbst keine schreibenden API-Aufrufe.

Vorhandene Aktionen wie:

- Tier anlegen,
- Aufgabe anlegen,
- Gewicht erfassen,
- Symptom erfassen,
- Tier bearbeiten,
- Status ändern,
- archivieren oder wiederherstellen

werden an die gespeicherten Legacy-Handler delegiert.

Falls der Legacy-Dashboardzustand noch nicht geladen ist, lädt die Brücke ihn einmalig vor der Aktion. Sobald ein Legacy-Dialog geöffnet ist, rendert die Brücke vollständig mit dem gespeicherten Legacy-Renderer. Nach Schliessen des Dialogs erscheint wieder die neue Route.

Es gibt keinen parallelen Schreibpfad und keine Rückübersetzung kanonischer DTOs in Legacy-Payloads.

## 6. Datenfluss

### 6.1 Verzeichnis laden

```text
Legacy-Panel-Hass-Referenz
→ Home-Assistant-Transportadapter
→ AnimalHealthClient.getAnimalDirectory()
→ Normalisierung von Dashboard, Katalog, Gruppen und Tags
→ controller.runLatest("animal-directory")
→ Store-Slices animals, tasks und timeline
→ neuer Renderer
```

Android verwendet weiterhin seinen vorhandenen `hass`-kompatiblen Adapter im WebView. Dadurch kann dieselbe dynamische `getHass`-Grenze für beide Hosts verwendet werden, ohne die native Android-Bridge in dieser Phase umzubauen.

### 6.2 Tierdetail laden

```text
Tier auswählen
→ Router animal-detail/{animalId}
→ AnimalHealthClient.getAnimalDetail(animalId)
→ Zusammenführen mit Gruppen- und Tagmetadaten des Verzeichnisses
→ controller.runLatest("animal-detail")
→ animals.detail
→ Tier-Grundansicht
```

Eine ältere Detailantwort wird durch Request-ID und Navigationsrevision verworfen.

### 6.3 Store-Abbildung

Die bestehenden kanonischen Slices werden erweitert, ohne neue Top-Level-Aliascontainer einzuführen:

```text
animals
├── status
├── items
├── groups
├── tags
├── catalog
├── directoryMeta
├── filters
├── detail
└── error

tasks
├── status
├── definitions
├── occurrences
└── error

timeline
├── status
├── items
└── error
```

`directoryMeta` enthält Version, Zeitzone, lokales Datum, Zusammenfassung und Exportmetadaten. Views lesen ausschliesslich diese kanonischen camelCase-Felder.

## 7. Fachliche Selektoren

Pure Selektoren werden unter `domain/animals/selectors.js` gebündelt:

```javascript
selectAnimalById(state, animalId)
selectGroupById(state, groupId)
selectVisibleAnimals(state)
selectGroupedAnimals(state)
selectNextOccurrenceForAnimal(state, animalId)
selectOpenOccurrencesForAnimal(state, animalId)
selectUrgentOccurrences(state)
selectRecentEvents(state, limit)
```

Filterung, Gruppierung und zeitliche Auswahl stehen nicht in den Viewtemplates. Die Views formatieren nur bereits ausgewählte Daten.

Überfälligkeitslogik wird nicht neu berechnet. Die UI verwendet ausschliesslich das kanonische Feld `timing` aus dem Normalisierer.

## 8. UI-Struktur

```text
frontend/src/
├── app/
│   └── read-only-animals.js
├── domain/
│   └── animals/
│       └── selectors.js
├── ui/
│   ├── read-only/
│   │   ├── components.js
│   │   ├── format.js
│   │   ├── i18n.js
│   │   └── styles.js
│   └── views/
│       ├── overview.js
│       ├── animals.js
│       └── animal-detail.js
├── legacy/
│   └── compatibility-bridge.js
└── runtime-entry.js
```

Die Dateien sind nach Verantwortlichkeiten und nicht nach Releasehistorie getrennt.

## 9. Renderingvertrag

`renderReadOnlyAnimalsRoute(state, context)` rendert genau eine der drei migrierten Routen.

Der Kontext enthält:

```javascript
{
  language,
  narrow,
  integrationVersion
}
```

Alle dynamischen Inhalte werden HTML-escaped. Datumswerte ohne Uhrzeit werden direkt aus `YYYY-MM-DD` formatiert und nicht durch `new Date("YYYY-MM-DD")` in eine Zeitzone verschoben.

Die Shell verwendet weiterhin `ha-icon`, weil Home Assistant und der bestehende Android-WebView-Adapter dieses Element bereitstellen.

## 10. Kompatibilitätsbrücke

`installLegacyReadOnlyAnimalsSlice(LegacyPanelClass)` darf als einzige neue Funktion den Legacy-Prototyp referenzieren.

Sie speichert genau einmal die final aktiven Legacy-Methoden:

```text
render
load
loadDetail
handleClick
handleInput
```

Danach installiert sie je einen dünnen Dispatcher. Der Dispatcher enthält keine Viewlogik. Er ruft entweder den modularen Runtime-Pfad oder die gespeicherte Legacy-Methode auf.

Pro Panelinstanz hält ein `WeakMap` den modularen Runtimezustand. Beim Entfernen des Panels entstehen keine globalen Instanzreferenzen.

## 11. Build und Auslieferung

### 11.1 esbuild

Mit dem ersten aktiven ES-Modul wird `esbuild` als exakt gepinnte Entwicklungsabhängigkeit eingeführt.

`package.json` erhält:

```json
{
  "devDependencies": {
    "esbuild": "0.25.9"
  }
}
```

Die Abhängigkeit wird nur in Entwicklung und CI benötigt. HACS und die Android-App verwenden weiterhin das eingecheckte Dist-Bundle.

### 11.2 Bundleaufbau

`scripts/build_frontend.mjs` erzeugt:

1. den unveränderten Legacy-Prelude anhand von `legacy/manifest.json`,
2. die gebündelte IIFE aus `frontend/src/runtime-entry.js`,
3. einen eindeutigen Trenner mit Buildmarker.

Die Legacy-Prelude-Bytes müssen weiterhin exakt den 99 Eingabedateien entsprechen. Das Gesamtbundle ist ab Phase 4 nicht mehr identisch mit dem Legacy-Prelude, sondern beginnt bytegenau damit.

### 11.3 CI

Validate und Android Alpha installieren die gepinnte Entwicklungsabhängigkeit vor der Bundleprüfung. Beide prüfen:

- reproduzierbares Gesamtbundle,
- syntaktisch gültiges Bundle,
- unveränderte Legacy-Dateien,
- vorhandenen modernen Buildmarker,
- Node-Vertragstests,
- vollständige bestehende Python- und Smoke-Tests,
- erfolgreichen Android-APK-Build.

## 12. Fehler- und Ladeverhalten

- Ein initialer Verzeichnisfehler zeigt eine lokalisierte Fehlermeldung und eine Wiederholen-Aktion.
- Während eines Refreshs bleiben vorhandene Daten sichtbar; die Shell kennzeichnet den laufenden Request.
- Ein Detailfehler zeigt die Tieridentität aus dem Verzeichnis, soweit vorhanden, und eine Wiederholen-Aktion.
- Wechsel auf eine Legacy-Route entfernt keine geladenen kanonischen Daten.
- Rückkehr auf eine neue Route verwendet den vorhandenen Store und lädt nur bei ausdrücklichem Refresh erneut.
- Ein Host- oder API-Fehler wird ausschliesslich über die stabilen Phase-2-Fehlercodes verarbeitet.

## 13. Teststrategie

### 13.1 Selektoren

Node-Tests prüfen:

- Gruppen- und Tagfilter,
- Suche,
- stabile Sortierung,
- Gruppierung einschliesslich Tiere ohne Gruppe,
- nächste und dringliche Aufgabeninstanzen,
- ausschliessliche Verwendung des kanonischen `timing`-Felds.

### 13.2 Views

Node-Tests mit kanonischen Fixtures prüfen:

- Übersicht in Deutsch und Englisch,
- Tierliste mit Filtern und leeren Ergebnissen,
- Tierdetail mit Gruppe, Tags, Gewicht, Aufgaben und Ereignissen,
- korrektes Escaping,
- datumssichere Formatierung,
- ausschliesslich kanonische camelCase-Eingaben.

### 13.3 Runtime

Node-Tests prüfen:

- Verzeichnis- und Detailanforderungen,
- `runLatest`-Verhalten,
- Navigation zwischen den drei neuen Routen,
- Navigation auf Legacy-Routen,
- Filteraktionen,
- Refresh,
- Delegation von Schreibaktionen,
- einmaliges Laden des Legacy-Zustands vor einem Legacy-Dialog,
- vollständigen Legacy-Renderer bei offenem Dialog,
- einmalige Installation der Brücke.

### 13.4 Build

Python- und Node-Tests prüfen:

- Legacy-Prelude ist exakt unverändert,
- Gesamtbundle beginnt mit diesem Prelude,
- IIFE und Aktivierungsmarker sind vorhanden,
- kein `part100.js`,
- das moderne Bundle enthält keine Module-Syntax,
- Home Assistant und Android verwenden weiterhin dasselbe Dist-Artefakt.

## 14. Abnahmekriterien

Phase 4 ist abgeschlossen, wenn:

- Übersicht, Tierliste und Tier-Grundansicht im ausgelieferten Bundle über den neuen modularen Pfad gerendert werden,
- diese Views nur kanonische DTOs lesen,
- Gruppen-, Tag- und Suchfilter funktionieren,
- Navigation innerhalb des neuen Slices den Phase-3-Router verwendet,
- Navigation zu Aufgaben, Kalender und Chronik unverändert auf den Legacy-Pfad führt,
- bestehende Schreibaktionen aus den neuen Views weiterhin über Legacy-Handler erreichbar sind,
- keine doppelte Persistenz und kein neuer Schreibpfad existiert,
- die 99 Legacy-Fragmente bytegenau unverändert sind,
- das Gesamtbundle reproduzierbar ist,
- sämtliche Node-, Python-, Smoke-, Android-, HACS- und hassfest-Prüfungen erfolgreich sind.
