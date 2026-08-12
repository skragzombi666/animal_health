# Animal Health 0.8.8

0.8.8 verbessert die KI-Mehrfacherfassung von Gewichten.

- Der tatsächliche Messzeitpunkt wird in Gewichtserfassungen nicht mehr mit aufgabenbezogenen Begriffen wie Startdatum oder Fälligkeit beschriftet. In reinen Gewichtsbatches heisst das Datumsfeld jetzt **Gewogen am**, die Zeit **Uhrzeit**; bei anderen bzw. gemischten Einträgen bleibt die neutrale Bezeichnung **Durchgeführt am**.
- Die Gewichtserkennung erhält wieder eine explizite Vollständigkeitsregel: Eine handschriftliche Liste wird vollständig von oben nach unten geprüft; unsichere Zeilen dürfen nicht stillschweigend ausgelassen werden.
- Bei erkannten Mehrfach-Gewichtserfassungen aus Bild/PDF wird zusätzlich ein zweiter reiner Vollständigkeitscheck durchgeführt. Er sucht nur nach tatsächlich sichtbaren, im ersten Durchlauf fehlenden Zeilen.
- Ergebnisse aus dem Vollständigkeitscheck werden mit dem ersten Durchlauf zusammengeführt; bereits vorhandene Tiere werden nicht doppelt angelegt und fehlende Felder eines vorhandenen Entwurfs können ergänzt werden.
- Fehlende oder unsichere Werte werden weiterhin nicht erfunden. Jeder Eintrag muss vor dem Speichern durch den Benutzer geprüft werden.

Behoben: #63.
