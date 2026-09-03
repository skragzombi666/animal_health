# Animal Health 0.9.38

Version 0.9.38 stellt die drei zentralen Erfassungsaktionen wieder vollständig her.

## Behobener Fehler

Die gemeinsame Zielauswahl für Aufgaben, Symptome und Medikamentengaben rief seit der Umstellung in 0.9.34 eine nicht vorhandene Zustandsfunktion auf. Beim Klick wurde der Dialog zwar vorbereitet, der anschliessende Aufbau brach jedoch vor der sichtbaren Darstellung ab. Dadurch wirkten die Schaltflächen vollständig funktionslos.

## Korrektur

- **Aufgabe planen** öffnet das Aufgabenformular wieder beim ersten Klick.
- **Symptom erfassen** öffnet die Symptomerfassung wieder beim ersten Klick.
- **Gabe / Medikament** öffnet die Medikamentengabe wieder beim ersten Klick.
- Der gemeinsame Zielzustand für Tier, Tiergruppe und allgemeine Aufgaben wird wieder zuverlässig erzeugt und normalisiert.
- Die ältere Formularschnittstelle mit `initialAnimalId` und `includeGeneral` wird mit der neueren Zielauswahl kompatibel verbunden.
- Beim Start aus einer Tieransicht wird das betreffende Tier wieder vorausgewählt.
- Veraltete Zielzustände aus einem zuvor geöffneten Formular werden vor einer neuen Erfassung entfernt.
- Andere Klickaktionen bleiben auf dem direkten synchronen Navigationspfad aus 0.9.37.

## Regressionstests

Ein Laufzeittest baut alle drei Formulare nach einem simulierten ersten Klick auf. Er prüft neben dem geöffneten Dialog auch die Tier-Vorauswahl, die allgemeine Aufgabenauswahl und die Weiterleitung anderer Aktionen.

## Versionsstand

- Home Assistant/HACS: **0.9.38**
- Android bleibt bei **0.9.0-alpha.7** und übernimmt die Korrektur über das gemeinsame Frontend-Bundle.
