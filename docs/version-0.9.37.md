# Animal Health 0.9.37

Version 0.9.37 stellt die unmittelbare und zuverlässige Bedienung der Navigation, Schnellaktionen und Dialoge wieder her und verbessert die Bildvorschau bei Dokumenten und Chronikeinträgen.

## Navigation und Dialoge

- Die in 0.9.33 und 0.9.34 eingeführte interne Browser-History für die Smartphone-Zurück-Taste ist vollständig aus dem aktiven Laufweg entfernt.
- Klicks werden nicht mehr durch Zustands-Snapshots, `history.pushState`, `history.replaceState`, `history.back()` oder asynchrone Wiederherstellung verzögert.
- Schliessen- und Zurück-Aktionen werden wieder direkt in der Anwendung ausgeführt.
- Die Schnellaktionen **Aufgabe erfassen**, **Gabe / Medikament** und **Symptom erfassen** öffnen ihren Dialog wieder beim ersten Klick.
- Bestehende 0.9.34- und 0.9.36-Aktionen wie Tierauswahl, Mehrfachauswahl, Duplizieren, erneutes Planen und Wechsel zur Aufgabenübersicht bleiben erhalten.
- Die Unterstützung der Smartphone-Zurück-Taste bleibt bewusst deaktiviert, bis sie ohne Eingriff in den normalen Klick- und Dialogpfad umgesetzt werden kann.

## Vorschaubilder

- Bildanhänge in **Dokumente** und **Chronik** fordern ihre Thumbnail-URLs bereits beim ersten Laden der Tieransicht an.
- Fehlt eine URL nach einem initialen Fehler, erfolgt ein begrenzter automatischer Neuversuch; das Bild muss nicht mehr zuerst geöffnet werden.
- Gleichzeitige URL-Anfragen werden zusammengefasst und auf höchstens 100 Anhänge pro WebSocket-Anfrage begrenzt.
- Vorschaubilder werden mit fester Grösse und asynchroner Dekodierung eingebunden, damit die Darstellung beim Laden stabil bleibt.
- Der Server erzeugt kleine JPEG-Thumbnails mit maximal **96 × 96 Pixeln** und reduzierter Qualität. Das entspricht einer informativen Vorschau für ungefähr 40–50 Pixel grosse Listenelemente.
- Thumbnails werden bereits beim Upload erzeugt. Für bestehende Anhänge werden sie beim ersten Abruf erzeugt und danach dateibasiert wiederverwendet.
- Auch die grössere Bildvorschau wird dateibasiert zwischengespeichert.
- Beim Löschen eines Anhangs werden die zugehörigen Vorschaudateien entfernt.

## Versionsstand

- Home Assistant/HACS: **0.9.37**
- Android bleibt bei **0.9.0-alpha.7** und übernimmt die Korrekturen über das gemeinsame Frontend-Bundle.
