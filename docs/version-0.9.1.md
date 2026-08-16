# Animal Health 0.9.1

0.9.1 startet die schnellen Home-Assistant-Iterationen als reguläre HACS-Releases und verbessert die Startseite für den täglichen Zugriff.

## Schnell erfassen

- «Schnell erfassen» kann über das Auf-/Zuklappsymbol rechts oben zwischen der bisherigen Kachelansicht und einer kompakten Symbolleiste umgeschaltet werden.
- Die kompakte Ansicht zeigt Gewicht, Symptom, Medikament/Supplement, weiteren Eintrag, Aufgabe und KI-Erfassung direkt in einer Zeile.
- Die gewählte Ansicht wird lokal im Browser über `localStorage` gespeichert und nach einem Reload oder einer neuen Sitzung wiederhergestellt.
- Die Symbolschaltflächen behalten `title`- und `aria-label`-Beschriftungen.

## Tierübersicht auf der Startseite

- Direkt unter «Schnell erfassen» befindet sich neu eine kompakte Übersicht der Tiere.
- Eine gemeinsame Werkzeugzeile bietet Filter für Tiergruppen und Tags sowie eine kompakte Suchschaltfläche, die das Suchfeld bei Bedarf öffnet.
- Tiere ohne Tiergruppe werden zuerst angezeigt; danach folgen die Tiergruppen nacheinander.
- Innerhalb jeder Gruppe erscheinen die Tiere als kleine Kacheln mit Tierbild und Name. Ohne Tierbild wird das passende Tierart-Symbol verwendet.
- Ein Klick auf ein Tier öffnet direkt dessen Detailansicht.
- Ein Klick auf eine Gruppenüberschrift öffnet die ausführlichere Tieransicht bereits auf diese Gruppe gefiltert.
- Gruppen-, Tag- und Suchfilter lassen sich kombinieren.

## Release-Workflow

- Dieser Stand wird nur für Home Assistant veröffentlicht.
- Die Android-App bleibt vorerst auf `0.9.0-alpha.7` eingefroren und wird durch diesen Release nicht neu gebaut.
- `0.9.1` wird als normaler GitHub-/HACS-Release veröffentlicht und benötigt keinen aktivierten Pre-Release-Schalter.
