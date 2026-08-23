# Animal Health 0.9.15

0.9.15 bündelt die im laufenden Test gemeldeten Verbesserungen rund um Tierdetailansicht, Symptome, Medikamentenerfassung und Audit-Trail.

## Home-Assistant-Navigation

Der Home-Assistant-Menüknopf ist wieder ganz links im Kopfbereich verfügbar. Die Kopfzeile folgt damit wieder dem vorgesehenen Aufbau:

**Home-Assistant-Menü → Animal Health + Version → Einstellungen ganz rechts.**

## Medikamentenauswahl und Bearbeitung

- Die Medikamentensuche in der Tieransicht rendert beim Tippen nicht mehr das gesamte Erfassungsformular neu. Dadurch bleibt der Eingabefokus auch bei mehreren aufeinanderfolgenden Buchstaben erhalten.
- Vorschläge in der normalen Medikamentenerfassung und im Behandlungsplan können über die gesamte Trefferzeile ausgewählt werden; der Klick auf Name, Wirkstoff oder Konzentration verhält sich identisch.
- Beim Bearbeiten einer bestehenden Medikamentengabe bleibt der ursprüngliche Ereigniszeitpunkt erhalten. Datum und Uhrzeit ändern sich nur, wenn sie bewusst im Formular angepasst werden.
- Medikamenteneinträge in der Chronik verwenden die beim Speichern hinterlegten Snapshot-Daten und zeigen Präparatname, Wirkstoff, Wirkstoffkonzentration und Darreichungsform analog zur Medikamentenauswahl.

## Symptome

Zusätzliche Symptome können in den Einstellungen als Stammdaten angelegt, bearbeitet, ausgeblendet und wieder eingeblendet werden.

Die Symptomerfassung unterstützt nun mehrere Symptome in einem gemeinsamen Eintrag:

- Such-/Auswahlfeld bleibt verfügbar,
- gewählte Symptome erscheinen als kompakte Chips,
- jedes Symptom kann über × wieder entfernt werden,
- weitere Symptome können unmittelbar ergänzt werden,
- Freitext ist möglich, auch wenn ein Symptom nicht in den Stammdaten vorhanden ist.

Mehrere gleichzeitig erfasste Symptome werden strukturiert in einem gemeinsamen Chronikeintrag gespeichert.

## Tierdetailansicht

Die Detailansicht verwendet für vertiefende Informationen ein einheitliches Overlay-Prinzip mit Schliessen-Kreuz:

- Klick auf den Tiernamen öffnet die Stammdaten,
- «Stammdaten anzeigen» ist zusätzlich im Tieraktionsmenü verfügbar,
- Klick auf das Tierbild öffnet das Bild gross,
- Klick auf das Gewicht öffnet den Gewichtsverlauf mit Grafik und allen Gewichtseinträgen,
- Klick auf eine Aufgabe öffnet die Aufgabendetails inklusive Fälligkeitshistorie.

Die dauerhaft sichtbare Stammdatenbox wurde entfernt. Das Tieraktionsmenü wird beim Verlassen, beim Tierwechsel und nach Auswahl einer Aktion wieder geschlossen.

## Chronik und Audit-Trail

Die Chronikbox eines einzelnen Tiers besitzt rechts oben ein Menü. Darüber können direkt in der Tieransicht:

- gelöschte Einträge eingeblendet werden,
- frühere/geänderte Versionen eingeblendet werden.

Bei Korrekturen werden geänderte Felder soweit möglich als Vorher-/Nachher-Vergleich angezeigt. Standardmässig bleibt die Tierchronik auf den aktuell gültigen Stand reduziert.

## Symbole

Medikamentenaktionen behalten die Pille als fachliches Symbol und erhalten zusätzlich ein Pluszeichen. Damit entspricht die Medikamentenerfassung dem gleichen visuellen Grundsatz wie andere Hinzufügen-/Erfassen-Aktionen.

## Release

- Home-Assistant/HACS-Version: **0.9.15**
- Android bleibt unverändert auf **0.9.0-alpha.7** eingefroren.
