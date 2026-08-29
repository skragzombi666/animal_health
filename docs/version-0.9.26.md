# Animal Health 0.9.26

## Zielbereiche und Mehrfacherfassung

- Einheitliche Zielauswahl für medizinische Erfassungen: `Gruppe | Tiere`.
- Aufgaben verwenden `Allgemein | Gruppe | Tier`.
- Im Tiermodus können mehrere Tiere über dieselbe wiederverwendbare Multi-Select-Komponente gewählt werden.
- Eine Tiergruppe ist ein eigenständiger fachlicher Scope. Gruppen-ID, Gruppenname und ein Snapshot der zum Erfassungszeitpunkt betroffenen Tiere werden dauerhaft mitgeführt.
- Gruppenweite Einträge werden auch in der Chronik eines einzelnen Tiers als `Gruppenaktion · <Tiergruppe>` gekennzeichnet.
- Symptome, Produkt-/Medikamentengaben und Behandlungspläne unterstützen Gruppen- und Mehrtier-Erfassung.

## Chronik und Anhänge

- Datum-only-Einträge reservieren keine leere Uhrzeitspalte mehr und beginnen links.
- Anhänge an ausgeführten Behandlungsplänen werden direkt in der Chronik als Vorschau angezeigt.
- Eingeklappt werden kleine Thumbnails bzw. Dateikacheln gezeigt; aufgeklappt werden grössere Vorschauen nebeneinander dargestellt.
- Bildvorschauen öffnen die bestehende grosse Bildansicht.
- Behandlungsschritte bleiben in der kompakten Chronik jeweils einzeilig und werden bei Überlänge mit Ellipsis abgeschnitten.

## Datei-Upload

- Der Dateipicker unterstützt die Mehrfachauswahl mehrerer Dateien in einem Auswahlvorgang robust auch über das `input`-Event mobiler Browser.
- Bei Mehrtier-/Gruppenerfassungen werden Anhänge den erzeugten Einträgen der betroffenen Tiere zugeordnet.

## Behandlungspläne

- Behandlungsschritte können beim Erstellen und Bearbeiten nach oben oder unten verschoben werden.
- Die gespeicherte Array-Reihenfolge ist die verbindliche Reihenfolge für Ausführung und Darstellung.

## Android

- Die bestehende Android-Fassung bleibt für 0.9.26 unverändert auf `0.9.0-alpha.7` eingefroren.
