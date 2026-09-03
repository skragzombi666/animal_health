# Animal Health 0.9.39

Version 0.9.39 schliesst die nach den Navigationskorrekturen verbliebenen Funktionslücken bei Aufgaben und ordnet die Einstellungen neu.

## Aufgaben vollständig wiederhergestellt

- Neue Aufgaben, duplizierte Aufgaben und erneut geplante Aufgaben verwenden wieder denselben validierten Speicherpfad.
- Verdeckte Pflichtfelder anderer Aufgabenarten werden konsequent deaktiviert und blockieren das Speichern nicht mehr unbemerkt.
- Bei einer unvollständigen Eingabe wird das betroffene Feld sichtbar markiert und eine konkrete Fehlermeldung angezeigt.
- Medikamenten- und Entwurmungsaufgaben zeigen die Produktauswahl sowie Dosis, Einheit und Applikationsweg.
- Impf-, Ergänzungs- und Futteraufgaben zeigen ihre jeweiligen fachlichen Planungsfelder.
- Behandlungsaufgaben besitzen wieder eine direkte Auswahl der vorhandenen Behandlungspläne.
- Gesundheitskontrolle, Pflege und Tierarztbesuch behalten ihre spezifischen Planungsfelder.
- Zielart und Vorauswahl für Gruppe, Tiere oder allgemeine Aufgaben bleiben bei normaler Anlage, Duplizieren und erneutem Planen erhalten.

## Einstellungen mit drei klaren Ebenen

Die Einstellungsseite zeigt zunächst nur drei Hauptbereiche. Ein Hauptbereich öffnet eine reine Übersicht seiner Unterpunkte; erst ein weiterer Klick zeigt den vollständigen Inhalt.

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

Die Off-Label-Anzeige ist damit ein eigenständiger Einstellungsbereich und nicht mehr in der Medikamentenverwaltung eingebettet.

### Entwickleroptionen

- KI-Konfiguration
- Verwaltung & Daten
- Test & Gefahrenbereich

Im Test- und Gefahrenbereich werden die beiden Rücksetzungen getrennt und mit ihrer vollständigen Löschwirkung dargestellt:

- **Integration zurücksetzen** löscht Tiere, Tiergruppen, Tags, Aufgaben, Chronik, Gewichte, Anhänge und Einstellungen. Die Integration bleibt installiert und startet leer.
- **Verlaufs- und Aufgabendaten zurücksetzen** löscht Chronik, Gewichte, Symptome, Medikamentengaben, Aufgaben, Serien und zugehörige Anhänge. Tiere, Gruppen, Zuordnungen, Tags, Stammdaten und Tierbilder bleiben erhalten.

## Bestehende Korrekturen

- Die schnelle direkte Navigation ohne internen Browser-History-Pfad bleibt bestehen.
- Dokument- und Chronikbilder laden weiterhin kleine persistente Vorschaubilder bereits beim ersten Anzeigen.

## Versionsstand

- Home Assistant/HACS: **0.9.39**
- Android bleibt bei **0.9.0-alpha.7** und übernimmt die Änderungen über das gemeinsame Frontend-Bundle.
