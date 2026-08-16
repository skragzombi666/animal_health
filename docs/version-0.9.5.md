# Animal Health 0.9.5

0.9.5 macht «Heute relevant» dynamischer und erweitert die Tierfilter auf Mehrfachauswahl.

## Heute relevant

- Das bisherige Zeitraum-Dropdown entfällt vollständig.
- Wiederkehrende Serien werden zuerst als genau ein Eintrag pro aktiver Serie angezeigt, statt für jeden einzelnen Termin eine eigene Zeile zu erzeugen.
- Danach erscheinen dynamische Zeitabschnitte: «Heute», «Diese Woche», «Nächste Woche», «Diesen Monat» und «Nächsten Monat».
- Ein Zeitabschnitt wird nur angezeigt, wenn darin tatsächlich etwas ansteht.
- Einmalige Aufgaben werden genau einem Abschnitt zugeordnet und dadurch nicht zwischen Woche und Monat doppelt dargestellt.
- Überfällige einmalige Aufgaben bleiben im Abschnitt «Heute» sichtbar.

## Wochenanfang

- Der Wochenanfang ist standardmässig Montag.
- Unter «Einstellungen» → «Darstellung» kann jeder Wochentag als Wochenanfang gewählt werden.
- Die Einstellung wird lokal im Browser gespeichert und gilt sowohl für die dynamischen Wochenabschnitte auf der Startseite als auch für die Kalenderansicht.

## Tierfilter

- Mehrere Tiergruppen können gleichzeitig ausgewählt werden.
- Mehrere Tags können gleichzeitig ausgewählt werden.
- Mehrere Werte innerhalb desselben Filters werden als ODER-Verknüpfung behandelt; Gruppenfilter und Tagfilter werden miteinander kombiniert.
- Die Auswahl bleibt über Sitzungen hinweg gespeichert.
- «Alle Tiere» beziehungsweise «Alle Tags» löscht jeweils die Auswahl dieses Filters.
- Der rote Reset-Button setzt weiterhin alle Tierfilter und die Tiersuche gemeinsam zurück und bleibt links vor den regulären Filtersymbolen.

## Release

- 0.9.5 ist ein regulärer Home-Assistant/HACS-Release ohne Android-Build.
- Die Android-App bleibt auf 0.9.0-alpha.7 eingefroren.
