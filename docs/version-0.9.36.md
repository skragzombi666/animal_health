# Animal Health 0.9.36

Version 0.9.36 korrigiert die Dokumentübersicht eines Tiers und schliesst die Lücken zwischen tierbezogener Aufgabenansicht, Aufgaben-Gesamtübersicht und erneuter Planung.

## Dokumente in der Tieransicht

- Der Bereich **Dokumente** wird nur noch angezeigt, wenn für das Tier mindestens ein Dokument oder Anhang vorhanden ist.
- Eine leere Karte mit «Keine Einträge vorhanden» entfällt vollständig.
- Die Übersicht enthält nun sämtliche dem Tier zugeordneten Anhänge, auch wenn sie über einen Chronikeintrag, eine Gewichtserfassung, eine Behandlung oder einen anderen fachlichen Eintrag hinzugefügt wurden.
- Die kontextbezogene Darstellung eines Anhangs beim zugehörigen Chronikeintrag bleibt zusätzlich erhalten.

## Aufgaben eines Tiers

- Der Aufgaben-Dialog in der Tieransicht unterscheidet vollständig zwischen **Aktive Aufgaben**, **Abgeschlossen** und **Deaktiviert**.
- Erledigte Einmal-Aufgaben bleiben damit direkt beim Tier nachvollziehbar.
- Abgeschlossene Aufgaben werden nicht mehr irrtümlich als aktiv gezählt.
- Eine neue Aktion **Zur Aufgabenübersicht** wechselt direkt in die zentrale Ansicht «Aufgaben & Serien».
- Duplizieren und erneutes Planen stehen auch in der tierbezogenen Aufgabenansicht zur Verfügung.

## Duplizieren und erneut planen

Die beiden Aktionen besitzen nun getrennte fachliche Bedeutungen:

- **Duplizieren** erstellt eine neue, unabhängige Aufgabe oder Serie auf Basis der bestehenden Definition.
- **Erneut planen** erstellt eine neue Planung derselben fachlichen Aufgabe und speichert die Herkunft zur bisherigen Aufgabe.

Beide Aktionen öffnen das normale Formular für eine neue Aufgabe. Zielbereich, Tiere oder Gruppe, Aufgabenart, Beschreibung, Wiederholung, Uhrzeit und die fachlichen Planungsdaten werden vorausgefüllt. Das Startdatum wird auf heute gesetzt; bei einer vorhandenen Laufzeit bleibt deren Dauer erhalten. Eine abgeschlossene Einmal-Aufgabe wird beim erneuten Planen nicht automatisch in eine tägliche Serie umgewandelt.

Die neue Aufgabe erhält immer eine eigene ID. Bei «Erneut planen» wird zusätzlich die Planungskette mit Ausgangs- und Ursprungsaufgabe im Aufgaben-Snapshot gespeichert. Bei «Duplizieren» wird lediglich die Kopierherkunft dokumentiert; die neue Aufgabe bleibt operativ unabhängig.

## Technische Umsetzung

- Keine Änderung am Datenbankschema erforderlich: Herkunftsmetadaten werden im bestehenden versionierten Aufgaben-Snapshot gespeichert.
- Die Korrekturen gelten für Home Assistant und das gemeinsam verwendete Android-Frontend.
- Regressionstests prüfen Dokumentaggregation, bedingte Sichtbarkeit, Aufgabenstatus, Zielbereichsübernahme, Kopier-/Neuplanungslogik und persistierte Herkunft.

## Versionsstand

- Home Assistant/HACS: **0.9.36**
- Android bleibt bei **0.9.0-alpha.7** und übernimmt die Änderungen über das gemeinsame Frontend-Bundle.
