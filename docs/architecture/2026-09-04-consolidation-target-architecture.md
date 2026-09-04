# Animal Health – Zielarchitektur und Migrationsgrenzen

**Status:** Fachlich freigegeben; Umsetzung beginnt mit Phase 0 und Phase 1  
**Referenzstand:** Animal Health 0.9.41  
**Referenz-Commit:** `4df86bc382b99db3a4276cb451edfacc0eaf502d`  
**Geltungsbereich:** Home-Assistant-Integration, gemeinsames Web-Frontend und eigenständige Android-App

## 1. Zweck

Diese Spezifikation legt die verbindliche Zielarchitektur für die Konsolidierung von Animal Health fest. Der Funktionsstand von 0.9.41 wird kontrolliert in eine fach- und komponentenbasierte Architektur überführt, ohne bestehende Nutzdaten, öffentliche Verträge oder fachliche Regeln unnötig zu verändern.

Die Konsolidierung ist kein Fortführen der 99 nummerierten Frontend-Fragmente. Sie ist ein systematischer Neuaufbau der aktuellen Implementierung nach fachlichen Objekten und Anwendungsfällen. Die alten Fragmente bleiben nur vorübergehend als unveränderlicher Referenzstand erhalten, damit bestehendes Verhalten verglichen, getestet und einzeln ersetzt werden kann.

## 2. Ausgangslage

Das aktuelle Frontend wird aus 99 nummerierten JavaScript-Dateien zusammengesetzt. Diese Dateien sind keine 99 Komponenten, sondern eine historische Überschreibungskette derselben globalen Klasse `AnimalHealthPanel`. Das aktive Verhalten ergibt sich aus Dateireihenfolge, Prototypänderungen, nachträglichen HTML-Manipulationen und CSS-Reihenfolge.

Das Backend verwendet parallel zahlreiche versionsgebundene Runtime-Patches. Zentrale Methoden wie `TaskRecordStore.execute` werden nacheinander ersetzt oder erweitert. Echte Datenmigrationen und laufendes Produktverhalten sind dadurch nicht ausreichend getrennt.

Home Assistant und Android verwenden dieselbe zusammengesetzte Oberfläche. Die aktuelle Android-Konfiguration erwartet exakt 99 Fragmente. Eine weitere Datei `part100.js` würde zugleich die Buildprüfung brechen und wegen lexikografischer Sortierung an der falschen Stelle ausgeführt.

## 3. Verbindliche Grundentscheidung

### 3.1 Die 99 Fragmente sind nur ein Legacy-Snapshot

Die 99 vorhandenen Dateien werden:

- einmalig als Referenzstand von 0.9.41 eingefroren,
- während der Übergangsphase reproduzierbar gebündelt,
- nicht konsolidiert oder zu einer neuen Architektur erklärt,
- nicht um neue Funktionen erweitert,
- nicht eins zu eins in neue Modulnamen übertragen,
- nach vollständiger Ablösung restlos entfernt.

Das temporäre Manifest beschreibt ausschliesslich die Reihenfolge des eingefrorenen Referenzstands. Es ist kein dauerhafter Bestandteil der Zielarchitektur.

### 3.2 Die neue Oberfläche entsteht unabhängig davon

Die neue Oberfläche wird unter `custom_components/animal_health/frontend/src/` fach- und komponentenbasiert aufgebaut. Ihre Grenzen orientieren sich an Verantwortlichkeiten wie Tiere, Gruppen, Chronik, Aufgaben, Produkte, Behandlungspläne, Anhänge und Einstellungen.

Neue Module dürfen keine Methoden der alten Panelklasse überschreiben. Sie erhalten explizite Abhängigkeiten, kanonische DTOs und eigene Tests.

### 3.3 Migration erfolgt bereichsweise

Ein Bereich wird vollständig nach folgendem Muster migriert:

```text
bestehendes Verhalten charakterisieren
→ fachlichen Vertrag festlegen
→ neue Implementierung erstellen
→ Alt- und Neuverhalten vergleichen
→ vollständige Route oder vollständigen Anwendungsfall umschalten
→ zugehörige Legacy-Nutzung entfernen
```

Es werden keine einzelnen Methoden quer durch eine Ansicht halb migriert. Bevorzugt werden ganze Routen und vollständige vertikale Anwendungsfälle.

### 3.4 Kein Big-Bang-Rewrite

Der Neuaufbau erfolgt systematisch, aber nicht als einmaliger vollständiger Rewrite. In den alten Dateien steckt implizites Verhalten, das noch nicht vollständig durch Browser- und Vertragstests beschrieben ist. Ein sofortiges Löschen würde Funktionsverluste schwer erkennbar machen.

Der Legacy-Stand dient daher als Vergleichsobjekt und Rückfallpunkt, nicht als Fundament des neuen Codes.

## 4. Ziele

- Pro fachlicher Funktion existiert genau eine aktuelle Implementierung.
- Frontend-Quellcode ist nach fachlichen Verantwortlichkeiten gegliedert.
- Home Assistant und Android verwenden dasselbe selbstenthaltene Bundle.
- Die Bundle-Reihenfolge wird durch einen deterministischen Build bestimmt.
- Die UI verwendet einen kanonischen Zustand und kanonische DTOs.
- Navigation, Rendering, Aktionen, Formulare, Übersetzungen und Styles besitzen eindeutige Zuständigkeiten.
- Backend-APIs rufen kanonische Anwendungsservices auf.
- Runtime-Monkey-Patches werden vollständig entfernt.
- Echte historische Datenmigrationen bleiben erhalten und idempotent.
- Jede Migrationsetappe ist einzeln testbar, auslieferbar und rücksetzbar.
- Die fachlichen Regeln aus 0.9.41 bleiben erhalten.

## 5. Nichtziele

Die Konsolidierung umfasst nicht:

- neue fachliche Funktionen,
- ein visuelles Redesign,
- eine Änderung medizinischer oder dokumentarischer Regeln,
- neue IDs oder eine unnötige Änderung gespeicherter Nutzdaten,
- eine native Neuentwicklung der Android-Oberfläche,
- die gleichzeitige Einführung eines neuen UI-Frameworks,
- die Entfernung echter historischer Datenmigrationen,
- eine Bereinigung aller Bereiche in einem einzigen Pull Request.

## 6. Technische Zielentscheidung

### 6.1 Frontend-Technik

- ES-Module unter `frontend/src/`
- JSDoc-Typen und statische JavaScript-Prüfung
- ein deterministischer Build über `scripts/build_frontend.mjs`
- ein eingechecktes Laufzeitartefakt unter `frontend/dist/animal-health-panel.js`
- vorhandene Web-Component- und Shadow-DOM-Grundlagen
- kein neues UI-Framework während der Konsolidierung
- `esbuild` erst ab dem ersten tatsächlich migrierten ES-Modul als fest gepinnte Entwicklungsabhängigkeit

Die erste Bundle-Etappe benötigt keine neue externe Abhängigkeit. Sie reproduziert zunächst nur den eingefrorenen Legacy-Stand anhand eines expliziten Manifests.

### 6.2 Eine befristete Legacy-Brücke

Während der Übergangsphase darf genau eine Datei auf die alte `AnimalHealthPanel`-Klasse zugreifen:

```text
frontend/src/legacy/compatibility-bridge.js
```

Die Brücke darf nur:

- vollständige migrierte Routen oder Anwendungsfälle an neue Module delegieren,
- nicht migrierte Bereiche an den eingefrorenen Legacy-Stand weiterreichen,
- den Migrationsstatus eines Bereichs abbilden.

Sie darf nicht:

- neue Fachlogik aufnehmen,
- alte und neue Zustände dauerhaft synchronisieren,
- Daten aus mehreren historischen Containern zusammensuchen,
- zu einer neuen Patchdatei werden.

Nach Migration des letzten Bereichs werden Brücke, Manifest und alle 99 Fragmente entfernt.

## 7. Zielstruktur des Frontends

```text
custom_components/animal_health/frontend/
├── dist/
│   └── animal-health-panel.js
├── legacy/
│   ├── manifest.json
│   └── parts/
│       └── animal-health-panel.part01.js … part99.js
└── src/
    ├── entry.js
    ├── app/
    │   ├── animal-health-panel.js
    │   ├── controller.js
    │   ├── router.js
    │   ├── store.js
    │   └── state.js
    ├── platform/
    │   ├── transport.js
    │   ├── home-assistant-adapter.js
    │   └── android-adapter.js
    ├── api/
    │   ├── client.js
    │   ├── contracts.js
    │   ├── errors.js
    │   └── normalizers.js
    ├── domain/
    │   ├── animals/
    │   ├── groups/
    │   ├── timeline/
    │   ├── attachments/
    │   ├── products/
    │   ├── treatments/
    │   ├── tasks/
    │   ├── capture/
    │   ├── settings/
    │   └── ai/
    └── ui/
        ├── components/
        ├── forms/
        ├── dialogs/
        ├── icons/
        ├── i18n/
        └── styles/
```

Die konkrete Zahl der neuen Dateien ist nicht normativ. Entscheidend sind klare Verantwortlichkeiten, explizite Imports und genau eine aktuelle Implementierung pro Anwendungsfall.

## 8. Frontend-Verantwortlichkeiten

### 8.1 Einstiegspunkt

`entry.js` übernimmt nur:

- Ermitteln des Plattformadapters,
- Erzeugen von API-Client, Store und Controller,
- Registrieren des Custom Elements,
- Bereitstellen von Version und Buildinformationen.

### 8.2 Panel und Controller

`animal-health-panel.js` verwaltet den Shadow-DOM-Lebenszyklus und bindet die delegierten Ereignisse genau einmal.

`controller.js` ordnet stabile Aktionsnamen expliziten Handlern zu. Es gibt keine Kette wiederholt überschriebener `handleClick`-, `handleChange`-, `handleSubmit`- oder `render`-Methoden.

### 8.3 Router

Der Router verwaltet interne Routen und Dialogzustand. Während der Konsolidierung verwendet er einen eigenen Navigationsstapel statt verdeckter Abhängigkeiten von `window.history`. Home Assistant und Android rufen denselben `router.back()`-Vertrag auf.

### 8.4 Store

Der projektspezifische Store stellt `getState`, `update` und `subscribe` bereit. Er enthält kanonische Bereiche für Plattform, Sprache, Navigation, Dialog, Tiere, Chronik, Aufgaben, Produkte, Behandlungen, Einstellungen, Entwürfe, Requests und Benachrichtigungen.

Verspätete asynchrone Antworten dürfen den Zustand einer inzwischen gewechselten Ansicht nicht überschreiben.

### 8.5 Rendering

Es gibt genau einen kontrollierten Renderpfad. Verboten sind im neuen Code:

- `shadowRoot.innerHTML +=`,
- reguläre Ausdrücke zum nachträglichen Umbau bereits erzeugten Markups,
- wiederholt angehängte globale Styles,
- fachliche Entscheidungen anhand bereits gerenderten Texts.

### 8.6 Gemeinsame Komponenten

Mindestens folgende Elemente werden gemeinsam umgesetzt:

- Zielbereich `Gruppe | Tiere | Allgemein`,
- Tier-Mehrfachauswahl,
- Dialograhmen,
- Formularfelder und sichtbare Validierung,
- Aufgaben- und Fälligkeitszeile,
- Chronikzeile,
- Produkt- und Behandlungsplanauswahl,
- Attachment-Liste und Vorschau,
- Lade-, Leer- und Fehlerzustände,
- Toolbar und Suche.

## 9. Plattform- und API-Grenze

Das gemeinsame Frontend kennt Home Assistant und Android nur über einen Transportvertrag:

```javascript
class AnimalHealthTransport {
  request(command, payload) {}
  callService(service, payload, options) {}
  download(resource) {}
  notify(message) {}
}
```

Der Home-Assistant-Adapter verwendet die vorhandenen Home-Assistant-Schnittstellen. Der Android-Adapter verwendet die native Bridge. Fachmodule greifen weder direkt auf `hass` noch auf Android-JavaScript-Interfaces zu.

Der API-Client bietet fachliche Methoden wie:

```text
getDashboard()
getAnimalDetail(animalId)
listTasks(filter)
executeOccurrence(occurrenceId, actual)
listProductDatabases()
saveTreatmentPlan(plan)
```

Bestehende Commands und Services bleiben zunächst unverändert. Aliasfelder und historische Antwortformen werden ausschliesslich in `normalizers.js` in kanonische DTOs übersetzt.

## 10. Kanonische Kerndaten

### Zielbezug

```javascript
/**
 * @typedef {Object} TargetDto
 * @property {"animal"|"animals"|"group"|"general"} scope
 * @property {string|null} animalId
 * @property {string[]} animalIds
 * @property {string|null} groupId
 * @property {string[]} memberSnapshot
 */
```

### Aufgabeninstanz

```javascript
/**
 * @typedef {Object} TaskOccurrenceDto
 * @property {string} id
 * @property {string|null} seriesId
 * @property {string} definitionId
 * @property {TargetDto} target
 * @property {string|null} scheduledAt
 * @property {string|null} dueDate
 * @property {"pending"|"completed"|"skipped"|"cancelled"} status
 * @property {"overdue"|"today"|"upcoming"|"closed"} timing
 * @property {Object} planned
 * @property {Object|null} completion
 */
```

### Chronikereignis

```javascript
/**
 * @typedef {Object} HealthEventDto
 * @property {string} id
 * @property {string} animalId
 * @property {string} type
 * @property {string} occurredAt
 * @property {TargetDto|null} target
 * @property {Object|null} source
 * @property {Object} payload
 * @property {Object[]} attachments
 */
```

Datumswerte ohne Uhrzeit bleiben `YYYY-MM-DD` und werden nicht implizit als UTC-Zeitpunkt interpretiert. Zeitpunkte tragen einen eindeutigen Offset oder Host-Zeitzonenbezug. Die Fälligkeitsklassifikation wird im Backend berechnet und nicht als dauerhafte UI-Wahrheit zurückgeschrieben.

## 11. Fachliche Invarianten

### 11.1 Tiere und Gruppen

- Jedes Tier besitzt höchstens eine primäre Tiergruppe.
- Tags bleiben von der primären Tiergruppe getrennt.
- Gruppen sind eigenständige fachliche Ziele.
- Gruppenaktionen speichern Zielart, `group_id` und Mitglieder-Snapshot.
- Einzelne Tierchroniken kennzeichnen gruppenweite Aktionen weiterhin.

### 11.2 Chronik

- Chronikeinträge sind ereigniszentriert.
- Herkunft aus einer Aufgabe ist sekundäre Metainformation.
- Korrekturen überschreiben bestehende Ereignisse nicht.
- Anhänge bleiben mit Tier und gegebenenfalls Ereignis verknüpft.

### 11.3 Aufgaben und Serien

- Serienvorlage und einzelne Fälligkeit sind getrennte Objekte.
- Jede Fälligkeit besitzt eigene ID, `series_id`, geplante Zeit und Status.
- Offene Instanzen bleiben beim Tageswechsel bestehen.
- Neue Instanzen werden zusätzlich erzeugt.
- „Überfällig“ wird aus offenem Status und überschrittener Fälligkeit in der Home-Assistant-Zeitzone abgeleitet.
- Aktionen adressieren konkrete Aufgabeninstanzen.
- Die Bearbeitung einer Instanz verändert keine andere Instanz derselben Serie.
- Offline-Lücken werden ohne Löschen vorhandener Instanzen materialisiert.
- Routinen ohne Dokumentationspflicht erzeugen keinen künstlichen Überfälligkeitsstau.
- Die Bestandskorrektur aus 0.9.41 bleibt idempotent.

### 11.4 Medizinische Erfassung und KI

- KI-Ergebnisse sind nur zu prüfende Vorbefüllungen.
- Die KI stellt keine Diagnose, empfiehlt keine Therapie und berechnet keine Dosis.
- Speicherung erfolgt erst durch ausdrückliche Benutzeraktion.
- Produktquelle, lokaler Override und dokumentierte Durchführung bleiben unterscheidbar.

## 12. Zielstruktur des Backends

```text
custom_components/animal_health/
├── api/
├── application/
│   ├── animal_service.py
│   ├── timeline_service.py
│   ├── attachment_service.py
│   ├── product_service.py
│   ├── treatment_service.py
│   ├── task_definition_service.py
│   ├── task_occurrence_service.py
│   └── task_execution_service.py
├── domain/
├── infrastructure/
│   ├── database.py
│   ├── repositories/
│   ├── exports/
│   └── media/
└── migrations/
```

Home-Assistant-Services, WebSocket-Handler und Android-Endpunkte validieren Eingaben, rufen einen Anwendungsservice auf und serialisieren das Ergebnis. Sie enthalten keine eigene Fachlogik.

`TaskRecordStore.execute` wird im Zielzustand nicht mehr durch mehrere Module ersetzt. Die Ausführung liegt in einem kanonischen `TaskExecutionService`.

Echte Schema- und Datenmigrationen bleiben unter `migrations/` erhalten. Das Ersetzen laufender Klassenmethoden gilt nicht als Migration und wird entfernt.

## 13. Übergangsarchitektur

### 13.1 Legacy-Isolation

Zunächst bleiben die 99 Dateien an ihrem heutigen Ort, werden aber durch Schutztests eingefroren. Ein explizites Manifest listet exakt diese bestehenden Pfade in der aktuellen Reihenfolge auf.

Erst nachdem Home Assistant, Android und alle Tests ausschliesslich das Dist-Bundle verwenden, werden die Fragmente in einem reinen Verschiebe-Commit nach `frontend/legacy/parts/` verlagert.

### 13.2 Deterministisches Bundle

`scripts/build_frontend.mjs` erzeugt `frontend/dist/animal-health-panel.js` aus dem expliziten Manifest. Das Bundle wird eingecheckt, weil HACS keine Node-Buildumgebung voraussetzen darf.

CI baut das Bundle neu und vergleicht es bytegenau mit dem eingecheckten Artefakt.

Home Assistant liefert nur das Dist-Bundle aus. Android übernimmt dasselbe Dist-Bundle. Kein Host sortiert oder verkettet zur Laufzeit Quelldateien.

### 13.3 Keine parallelen Schreibpfade

Während der Migration gibt es keine duale Persistenz und keine parallelen alten und neuen Schreibpfade. Ein vollständiger Anwendungsfall wird erst umgeschaltet, wenn seine Tests bestanden sind. Ein Revert stellt den Legacy-Pfad wieder her, ohne Nutzdaten zurückmigrieren zu müssen.

## 14. Migrationsphasen

### Phase 0 – Referenzstand und Schutzregeln

- Inventar der 99 Fragmente
- Inventar aller Frontend-Prototypüberschreibungen
- Inventar aller Views, Dialoge, Aktionen, Commands, Services, Übersetzungen und CSS-Blöcke
- Inventar aller Backend-Runtime-Patches und ihrer Reihenfolge
- Trennung zwischen echter Migration und Runtime-Patch
- Charakterisierung zentraler Benutzerabläufe
- CI-Schutz gegen neue Fragmente und neue Patchmuster

**Austrittskriterium:** Der Stand 0.9.41 ist reproduzierbar beschrieben; jede Erweiterung der Altarchitektur führt zu einem CI-Fehler.

### Phase 1 – Build- und Auslieferungsgrenze

- explizites Legacy-Manifest
- deterministisches Dist-Bundle
- `panel.py` liefert ausschliesslich das Dist-Bundle
- Android übernimmt ausschliesslich dasselbe Dist-Bundle
- Entfernung der hart codierten Android-Prüfung auf 99 Quelldateien
- CI-Prüfung der Bundle-Reproduzierbarkeit
- Beibehaltung des Bundle-Hashes für Cache-Busting

**Austrittskriterium:** Home Assistant und Android verwenden bytegleich dasselbe Artefakt; die 99 Fragmente werden nur noch vom Buildskript gelesen.

### Phase 2 – Plattformadapter und API-Normalisierung

Transportinterface, Plattformadapter, fachlicher API-Client, kanonische Fehler und Normalisierer.

### Phase 3 – Anwendungsshell

Store, Router, Dialogzustand, Benachrichtigungen, Styles, Übersetzungen, Aktionsregistry und gemeinsame Zielauswahl.

### Phase 4 – Lesende Tier- und Chronikansichten

Übersicht, Tierliste, Tierdetail-Grunddaten, Chronikliste, Chronikdetails und Kalender.

### Phase 5 – Formulare, Erfassungen und Anhänge

Tierformular, Status, Gewicht, Symptome, allgemeine Chronikeinträge, Zielbereich, Upload, Vorschau und Download.

### Phase 6 – Produkte, Gaben und Behandlungspläne

Produktdatenbanken, lokale Overrides, Medikamente, Impfstoffe, Entwurmungen, Ergänzungen, Futtermittel, Gaben und Behandlungspläne.

### Phase 7 – Aufgaben und Serien

Aufgabendefinition, Serienvorlage, Instanzmaterialisierung, Gruppierung, Übersichten, Duplizieren, Ausführung, Chronikerzeugung, Offline-Lücken und 0.9.41-Bestandskorrektur.

### Phase 8 – Einstellungen, Administration und KI

Einstellungsnavigation, Stammdaten, Export, Diagnose, Rücksetzungen und KI-Erfassung.

### Phase 9 – Entfernung der Legacy-Laufzeit

- direkte Registrierung kanonischer APIs und Services
- Entfernen von `_apply_all_patches`
- Entfernen überführter Runtime-Module
- Erhalt echter Migrationen
- Entfernen der Legacy-Brücke
- Entfernen aller 99 Fragmente und des Manifests
- Entfernen rein strukturgebundener Tests
- Aktualisieren der Gesamtdokumentation

## 15. Pull-Request-Grenzen

Jeder Migrations-PR enthält:

- einen klar abgegrenzten Anwendungsfall oder eine Infrastrukturgrenze,
- keine neue Fachfunktion,
- keine gleichzeitige visuelle Neugestaltung,
- vollständige Tests des migrierten Verhaltens,
- unveränderte öffentliche Verträge, sofern kein eigener Kompatibilitätsplan vorliegt,
- kein neues nummeriertes Frontend-Fragment,
- keinen neuen Backend-Runtime-Patch,
- ein reproduzierbares Dist-Bundle,
- erfolgreiche Home-Assistant- und Android-Prüfungen,
- einen klaren Revert-Punkt.

Alte Dateien werden erst gelöscht, wenn alle darin enthaltenen Anwendungsfälle nachweislich überführt sind.

## 16. Teststrategie

### 16.1 Charakterisierung

Vor jeder Extraktion werden beobachtbare Ergebnisse des bestehenden 0.9.41-Pfads festgehalten. Tests sichern Verhalten und Verträge, nicht historische Methodennamen.

### 16.2 JavaScript-Unit-Tests

Pure Normalisierer, Selektoren, Fälligkeitsgruppierung, Zielbereichslogik, Formularvalidierung und Formatierung werden mit dem eingebauten Node-Testläufer geprüft.

### 16.3 API-Verträge

Repräsentative Home-Assistant- und Android-Antworten müssen in dieselben kanonischen DTOs überführt werden.

### 16.4 Browsertests

Ein kleiner Browser-Smoke-Test prüft mindestens Start, Navigation, Dialoge, Tierdetail, konkrete Aufgabeninstanz, Attachment-Vorschau, Deutsch und Englisch sowie schmale und breite Darstellung.

### 16.5 Backend

Anwendungsservices werden mit temporärer SQLite-Datenbank getestet. Aufgaben- und Chronikschreibvorgänge prüfen Transaktionsatomarität. Migrationstests prüfen repräsentative Altstände und wiederholte Ausführung.

## 17. Architektur-Schutzregeln

Während der Migration schlägt CI bei neuen Verstössen fehl:

```text
neue animal-health-panel.part*.js
neue Prototype-Patches ausserhalb der Legacy-Brücke
neues shadowRoot.innerHTML +=
neue Zuweisung TaskRecordStore.<methode> = ...
neue apply_vXXXX_patches-Registrierung
neue versionsbezogene Zustandscontainer unter frontend/src
abweichendes Dist-Bundle
unterschiedliche Übersetzungsschlüssel
unterschiedliche Frontend-Artefakte für Home Assistant und Android
```

Bestehende Verstösse werden über eine explizite Baseline toleriert. Diese Baseline darf nur kleiner werden.

## 18. Definition of Done

Die Konsolidierung ist abgeschlossen, wenn:

- das Frontend aus fachlichen ES-Modulen gebaut wird,
- Home Assistant und Android dasselbe Bundle verwenden,
- keine nummerierten Fragmente mehr aktiv sind,
- keine Prototyp-Patchkette mehr existiert,
- Rendering, Aktionen und Formulare je einen kontrollierten Pfad besitzen,
- Fachmodule ausschliesslich kanonische DTOs verwenden,
- keine versionsbezogenen Frontend-Zustände mehr existieren,
- Backend-APIs kanonische Anwendungsservices aufrufen,
- `_apply_all_patches` und Runtime-Methodenersetzungen entfernt sind,
- echte historische Migrationen erhalten und getestet sind,
- alle fachlichen Invarianten aus 0.9.41 regressionsgetestet sind,
- README und technische Dokumentation dem tatsächlichen Stand entsprechen.

## 19. Erste Implementierungsetappe

Die erste Etappe umfasst ausschliesslich Phase 0 und Phase 1:

1. maschinenlesbares Architektur-Inventar,
2. Schutztests gegen weiteres Legacy-Wachstum,
3. explizites Manifest des unveränderten Referenzstands,
4. deterministisches Buildskript,
5. eingechecktes Dist-Bundle,
6. Umstellung von `panel.py`,
7. Umstellung des Android-Builds,
8. CI-Prüfung der Reproduzierbarkeit und Artefaktgleichheit.

Diese Etappe ändert keine Ansicht, keine API, keine Datenbank und keinen Benutzerablauf. Sie schafft lediglich eine sichere Auslieferungsgrenze, auf der der objekt- und fachbasierte Neuaufbau beginnen kann.
