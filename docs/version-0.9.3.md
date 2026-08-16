# Animal Health 0.9.3

0.9.3 räumt die Startseite weiter auf und verbessert die kompakte Tierübersicht.

## Startseite

- Die redundante Seitenüberschrift «Übersicht» entfällt.
- Damit entfällt auf der Startseite auch die bisherige allgemeine Suchleiste oben; die Tiersuche bleibt direkt im Bereich «Tiere» verfügbar.
- Die Startseite beginnt dadurch unmittelbar mit «Heute relevant».

## Tierkacheln

- Bild bzw. Tierart-Symbol und Tiername werden innerhalb der Tierkachel konsequent zentriert.
- Die Zentrierung gilt für Tiere mit und ohne hinterlegtes Foto.

## Tierfilter

- Gruppen- und Tagfilter der Tierübersicht werden lokal gespeichert und nach Reload bzw. neuer Sitzung wiederhergestellt.
- Sobald ein Gruppenfilter, Tagfilter oder eine Suchanfrage aktiv ist, erscheint eine zusätzliche rote Reset-Schaltfläche.
- Die Reset-Schaltfläche setzt Gruppenfilter und Tagfilter auf «alle» zurück, leert die Tiersuche und schliesst geöffnete Filter-/Suchfelder.
- Nicht mehr vorhandene gespeicherte Gruppen oder Tags werden beim Laden automatisch auf den Gesamtbestand zurückgesetzt.

## Release

- 0.9.3 ist ein regulärer Home-Assistant/HACS-Release ohne Android-Build.
- Die Android-App bleibt vorerst auf 0.9.0-alpha.7 eingefroren.
