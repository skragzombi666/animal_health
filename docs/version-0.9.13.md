# Animal Health 0.9.13

0.9.13 überarbeitet Chronik, Navigation und Medikamentenverwaltung. Gelöschte Chronikeinträge bleiben auditierbar, Medikamenten-Stammdaten werden historisch stabil behandelt und die Medikamentensuche zeigt Produkt, Wirkstoff und Konzentration gemeinsam an.

## Chronik und Audit Trail

Chronikeinträge können gelöscht werden, ohne den zugrunde liegenden Datensatz physisch zu entfernen. Gelöschte Einträge:

- verschwinden aus der normalen Chronik,
- bleiben mit Löschzeitpunkt im Audit Trail erhalten,
- können über «Gelöschte Einträge anzeigen» wieder eingeblendet werden.

Bei Statusänderungen wird nach dem Löschen der aktuelle Status aus der letzten noch gültigen Statusänderung neu bestimmt. Existiert keine gültige Statusänderung mehr, wird der Status vor der ersten Statusänderung wiederhergestellt.

Beim Gewicht wird der aktuelle Wert aus dem neuesten nicht gelöschten effektiven Gewichtseintrag bestimmt. Gelöschte Korrekturen lassen dadurch den vorherigen gültigen Wert wieder wirksam werden.

## Navigation und Startseite

Die obere Navigation wird reduziert:

- Das Animal-Health-Logo mit dem Schriftzug «Animal Health» führt zur Startseite.
- Die Versionsnummer wird klein und zurückhaltend direkt beim Produktnamen angezeigt.
- Ein separater Startseiten-Link entfällt.
- Die Chronik entfällt als eigener Navigationspunkt.
- Einstellungen bleiben rechts in der Kopfnavigation.

Unter der Tierübersicht zeigt die Startseite die zehn neuesten Chronikeinträge. Über «Alle anzeigen» beziehungsweise «Mehr anzeigen» wird die vollständige Chronik geöffnet.

## Medikamentenauswahl

Medikamente werden in der Auswahl strukturiert dargestellt:

- Produktname als primäre Information,
- Wirkstoff optisch nachgeordnet,
- Wirkstoffkonzentration,
- bei Bedarf Darreichungsform.

Die Suche berücksichtigt Produktname, Alias, Wirkstoff, Konzentration und Darreichungsform.

Für bekannte Präparate werden unter anderem folgende Produktinformationen ergänzt:

- Baytril 10% ad us. vet. – Enrofloxacin – 100 mg/ml
- Flubenol 5% – Flubendazol – 50 mg/g
- Flubenol KH – Flubendazol – 44 mg/ml

Eine pauschale Umrechnung beliebiger Prozentangaben findet nicht statt. Normalisierte Konzentrationen werden nur dort verwendet, wo die Bezugsgröße eindeutig bekannt ist.

## Manuelle Medikamente

Manuell erfasste Medikamente können bearbeitet und archiviert werden. Archivierte Medikamente:

- bleiben als Stammdatensatz erhalten,
- werden standardmäßig nicht mehr in der Medikamentenauswahl vorgeschlagen,
- können über «Archivierte Medikamente anzeigen» sichtbar gemacht und wieder aktiviert werden.

Ein physisches Löschen verwendeter Medikamenten-Stammdaten ist nicht Bestandteil der normalen Oberfläche.

## Historische Produktdaten

Neue Medikamentengaben speichern zusätzlich einen Snapshot der zum Zeitpunkt der Dokumentation verwendeten Produktdaten. Enthalten sind Produktname, Wirkstoff, Konzentration und Darreichungsform. Spätere Änderungen oder Archivierungen des Medikamenten-Stammdatensatzes verändern bereits dokumentierte Gaben dadurch nicht rückwirkend.

## Medikamentensuche

Die Freitextsuche wurde auf eine eigene Vorschlagsliste umgestellt. Treffer werden während der Eingabe im bestehenden DOM aktualisiert, ohne das Eingabefeld neu zu erzeugen. Dadurch bleibt der Fokus beim Tippen erhalten.

## Release

- 0.9.13 ist ein regulärer Home-Assistant/HACS-Release.
- Die Android-App bleibt auf 0.9.0-alpha.7 eingefroren.
