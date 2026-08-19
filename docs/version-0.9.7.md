# Animal Health 0.9.7

0.9.7 trennt die operative Durchführung klarer von der Verwaltung und macht den Zustand wiederkehrender Aufgaben nachvollziehbar.

## Aufgaben & Serien verwalten

- Die bisherige vollständige Aufgabenansicht wird zur kompakten Verwaltung von Aufgabendefinitionen und Serien.
- Die redundanten Listen «Überfällig», «Heute», «Demnächst» und «Erledigt» entfallen dort.
- Aktive Serien, offene Einzelaufgaben und deaktivierte Aufgaben werden getrennt dargestellt.
- Titel, Beschreibung und Zeitplan können bearbeitet werden.
- Aufgaben und Serien können weiterhin aktiviert und deaktiviert werden.
- Fällige Durchführung bleibt in «Anstehend» und im Kalender; erledigte Durchführung in der Chronik.

## Dynamische Ansicht «Anstehend»

- Eine heute fällige, noch nicht bestätigte Serie erscheint im Abschnitt «Heute relevant».
- Überfällige oder vergangene, nicht bestätigte Serien erscheinen gesammelt unter «Überfällig / nicht bestätigt».
- Mehrere verpasste Termine derselben Serie werden zu einer Zeile mit Anzahl und frühestem Datum zusammengefasst.
- Die Ausführung kann bei konkreten fälligen oder überfälligen Vorkommen direkt gestartet werden.
- Zukünftige Serien bleiben jeweils einmalig mit ihrer nächsten Fälligkeit sichtbar.

## Kalenderstatus

- Zukünftig geplante Vorkommen: grau.
- Aktuell fällige Vorkommen: Primärfarbe.
- Vergangene, nicht bestätigte Vorkommen: gelb.
- Bestätigte bzw. ausgeführte Vorkommen: grün.
- Ausgesetzte, übersprungene oder abgebrochene Vorkommen: rot.
- Eine Legende erklärt die Farben.
- Fällige und überfällige Vorkommen können direkt aus dem Kalender ausgeführt werden.

## Tierchronik

- In der Tierdetailansicht erscheint vor der Chronik ein kompakter Abschnitt «Serienstatus».
- Er zeigt pro aktiver Serie offene bzw. nicht bestätigte Termine, heutige Fälligkeit, nächste Fälligkeit sowie zuletzt bestätigte, ausgesetzte oder abgebrochene Vorkommen.
- Dadurch bleibt der Status nachvollziehbar, ohne für tägliche Serien zahlreiche automatische Chronikeinträge zu erzeugen.

## Überfälligkeitsmeldungen

- Home Assistant erzeugt eine zusammengefasste persistente Meldung, sobald wiederkehrende Aufgaben überfällig sind.
- Die Meldung wird bei neuen oder erledigten Fälligkeiten aktualisiert und verschwindet, sobald keine Serie mehr überfällig ist.
- Die Prüfung erfolgt alle 15 Minuten und zusätzlich nach Aktualisierungen der Animal-Health-Daten.
- Neue überfällige Vorkommen lösen das Home-Assistant-Ereignis `animal_health_series_overdue` aus. Dieses kann für eigene Automationen oder mobile Benachrichtigungen verwendet werden.
- Beim Start wird der bestehende Überfälligkeitsstand angezeigt, ohne Automationsereignisse für sämtliche Altbestände erneut auszulösen.

## Release

- 0.9.7 ist ein regulärer Home-Assistant/HACS-Release ohne Android-Build.
- Die Android-App bleibt auf 0.9.0-alpha.7 eingefroren.
