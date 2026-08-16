# Animal Health 0.9.0-alpha.7

0.9.0-alpha.7 verdichtet die Erfassungsaktionen in der Tierdetailansicht.

## Kompakte Erfassungsleiste

- Die Erfassungsaktionen werden direkt als sieben Symbole in einer einzigen horizontalen Zeile angezeigt.
- Enthalten sind Gewicht, Symptom, Medikament/Supplement, Aufgabe, KI-Erfassung, weiterer Eintrag und Dokumentanhang.
- Die bisherige Schaltfläche «Mehr» mit horizontalen drei Punkten entfällt vollständig, weil keine Erfassungsaktionen mehr ausgeblendet sind.
- «Gewicht erfassen» bleibt als primäre Aktion farblich hervorgehoben.
- Die Schaltflächen enthalten weiterhin `title`- und `aria-label`-Beschriftungen, obwohl in der kompakten Ansicht kein Text neben den Symbolen angezeigt wird.
- Das vertikale Drei-Punkte-Menü in der Tierkarte bleibt bestehen; es betrifft weiterhin Tierverwaltung und Stammdatenaktionen und ist nicht Teil der Erfassungsleiste.

## Gemeinsame Oberfläche

Die Änderung liegt im gemeinsam verwendeten Frontend und wird damit sowohl in Home Assistant als auch beim nächsten Build der Standalone-Android-App verwendet.
