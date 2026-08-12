# Animal Health 0.8.10

0.8.10 behebt zwei Probleme der KI-Mehrfacherfassung aus dem Praxistest.

- Aufgeklappte Einträge zeigen ihre Detailfelder in der Home-Assistant-App/WebView jetzt mit expliziten Layout-Regeln zuverlässig an. Der sichtbare `up`-Chevron entspricht damit tatsächlich einer geöffneten Detailansicht.
- Die zweite Gewichtserkennung ist keine reine Suche nach vermeintlich fehlenden Zeilen mehr, sondern eine unabhängige vollständige Re-Transkription des gesamten sichtbaren Dokuments. Dadurch kann ein erster Durchlauf mit z. B. 11 erkannten Zeilen durch einen vollständigen zweiten Durchlauf auf 12 ergänzt werden.
- Beim Zusammenführen wird eine bereits bekannte `matched_animal_id` bevorzugt zum Deduplizieren verwendet; leicht unterschiedlich gelesene Schreibweisen desselben Tiernamens erzeugen damit keine Dublette.
- Unsichere oder unbenannte sichtbare Zeilen bleiben als Entwurf erhalten. Es werden weiterhin keine Tiere oder Messungen allein aus dem Tierbestand erfunden.

Behoben: #67.
