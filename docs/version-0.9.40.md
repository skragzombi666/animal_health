# Animal Health 0.9.40

Version 0.9.40 veröffentlicht die nach 0.9.38 gesammelten Korrekturen als konsistent versionierten und vollständig geprüften HACS-Stand. Die nie veröffentlichte Zwischenfassung 0.9.39 wird übersprungen.

## Aufgabenanlage vollständig wiederhergestellt

- Neue Aufgaben, duplizierte Aufgaben und erneut geplante Aufgaben verwenden denselben validierten Speicherpfad.
- Verdeckte Pflichtfelder anderer Aufgabenarten werden deaktiviert und können das Speichern nicht mehr unbemerkt blockieren.
- Ungültige oder unvollständige Eingaben erzeugen eine sichtbare Meldung und fokussieren das betroffene Feld.
- Medikamenten- und Entwurmungsaufgaben zeigen Produktauswahl, Dosis, Einheit und Applikationsweg.
- Impf-, Ergänzungs- und Futteraufgaben zeigen ihre jeweiligen fachlichen Planungsfelder.
- Behandlungsaufgaben besitzen eine direkte Auswahl der vorhandenen Behandlungspläne.
- Gesundheitskontrolle, Pflege und Tierarztbesuch behalten ihre spezifischen Planungsfelder.
- Zielart und Vorauswahl für Gruppe, Tiere oder allgemeine Aufgaben bleiben bei normaler Anlage, Duplizieren und erneutem Planen erhalten.
- Herkunft und Planungskette duplizierter beziehungsweise erneut geplanter Aufgaben bleiben erhalten.

## Einstellungen neu geordnet

Die Einstellungsseite besitzt drei Ebenen: Hauptbereiche, reine Unterpunktübersichten und die jeweils separat geöffnete Detailseite. Formulare und Verwaltungsinhalte werden nicht mehr gleichzeitig in der Übersicht dargestellt.

### Tiere & Stammdaten

- Reihenfolge der Tiergruppen
- Darstellung Wochenanfang
- Eintragsarten
- Symptome verwalten
- Lokale Vorschläge

### Medikamente & Behandlungen

- Produktdatenbanken
- Favoriten
- Off-Label-Anzeige
- Medikamente verwalten
- Behandlungen & Behandlungspläne verwalten

Die Off-Label-Anzeige ist ein eigenständiger Einstellungsbereich und nicht mehr Bestandteil der Medikamentenverwaltung.

### Entwickleroptionen

- KI-Konfiguration
- Verwaltung & Daten
- Test & Gefahrenbereich

Im Test- und Gefahrenbereich werden die beiden Rücksetzungen getrennt und mit ihrer vollständigen Löschwirkung angezeigt:

- **Integration zurücksetzen** löscht Tiere, Tiergruppen, Tags, Aufgaben, Chronikeinträge, Gewichte, Anhänge und Einstellungen. Die Integration bleibt installiert und startet leer.
- **Verlaufs- und Aufgabendaten zurücksetzen** löscht Chronik, Gewichte, Symptome, Medikamentengaben, Aufgaben, Serien und zugehörige Anhänge. Tiere, Tiergruppen, Zuordnungen, Tags, Stammdaten und Tierbilder bleiben erhalten.

## Bestehende Korrekturen beibehalten

- Navigation, Dialoge und Schnellaktionen bleiben auf dem direkten synchronen Pfad ohne interne Browser-History.
- Dokument- und Chronikbilder laden kleine persistente Vorschaubilder bereits beim ersten Anzeigen.

## Release- und Repository-Konsistenz

- Manifest, Frontend und Tests verwenden einheitlich Version 0.9.40.
- Das Android-Bundle erwartet exakt die vorhandenen 99 Frontend-Module.
- Versehentlich eingecheckte temporäre Prüfdateien wurden entfernt.
- Ein Release wird künftig erst nach einem erfolgreichen Validate-Workflow auf `main` erzeugt.
- Der Release-Workflow bricht ab, wenn die zur Manifest-Version gehörenden Release Notes fehlen.

## Versionsstand

- Home Assistant/HACS: **0.9.40**
- Android bleibt bei **0.9.0-alpha.7** und übernimmt die Änderungen über das gemeinsame Frontend-Bundle.
