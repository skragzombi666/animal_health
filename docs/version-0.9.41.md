# Animal Health 0.9.41

Version 0.9.41 korrigiert die Behandlung nicht bestätigter wiederkehrender Aufgaben.

## Ursache

Seit der kompakten Serienlogik aus 0.8.15 wurden beim Tageswechsel und beim Start von Home Assistant alle offenen Instanzen einer Serie bis auf die aktuelle beziehungsweise nächste Fälligkeit gelöscht. Die Oberfläche konnte deshalb eine verpasste Instanz nicht mehr als überfällig anzeigen, obwohl die vorhandene Darstellungslogik dafür bereits ausgelegt war.

## Korrektur

- Offene Serieninstanzen werden beim Tageswechsel und beim Start nicht mehr gelöscht.
- Eine verpasste bestätigungspflichtige Aufgabe bleibt mit ihrer ursprünglichen Fälligkeit als eigene überfällige Instanz erhalten.
- Die überfällige und die aktuelle Instanz derselben Serie können gleichzeitig angezeigt und getrennt bearbeitet werden.
- Nach einer Offline-Phase werden fehlende Fälligkeiten der Serie in korrekter Reihenfolge nachgeführt.
- Abgeschlossene Perioden von Routinen werden weiterhin als «nicht dokumentiert» abgeschlossen und erzeugen keinen künstlichen Überfälligkeitsstau.
- Wochen- und Monatsaufgaben bleiben bis zum Ende ihres konfigurierten Zeitraums aktuell; die nächste Instanz wird erst nach Abschluss oder Ablauf dieses Zeitraums erzeugt.
- Neu rückwirkend angelegte Serien erzeugen keine erfundenen historischen Einzelinstanzen.

## Bestehende Daten

Beim ersten Start von 0.9.41 wird eine konservative, einmalige Wiederherstellung ausgeführt. Sie stellt höchstens die zuletzt durch die alte Kompaktlogik eindeutig verlorene bestätigungspflichtige Instanz innerhalb der letzten 60 Tage wieder her. Eine Instanz wird nur ergänzt, wenn bereits eine neuere Serieninstanz vorhanden ist. Dadurch wird die gemeldete Konstellation repariert, ohne ungesicherte historische Ausführungen zu erfinden.

## Technische Absicherung

- Nicht-destruktive Materialisierung wiederkehrender Aufgaben
- Idempotente Migrationsmarkierung für die einmalige Bestandskorrektur
- Regressionstests für tägliche, wöchentliche und routinemässige Serien
- Tests für Offline-Lücken, rückwirkend angelegte Serien und den Wechsel von 0.9.40 auf 0.9.41

Die Home-Assistant-Integration und das gemeinsame Frontend tragen Version 0.9.41. Die eigenständige Android-App bleibt unverändert auf 0.9.0-alpha.7.
