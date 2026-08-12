# Animal Health 0.8.11

0.8.11 setzt die KI-Gewichtserkennung bewusst auf den bewährten ursprünglichen Single-Pass aus 0.8.3 zurück, ohne das aktuelle kompakte Mehrfacherfassungs-UI zurückzubauen.

## KI-Mehrfacherfassung Gewicht

- Das aktuelle scrollbare Übersichtsdesign mit globalen Feldern, Statussymbolen, aufklappbaren Details und Sammelspeicherung bleibt unverändert.
- Gewichtserfassungen verwenden wieder `animal_health/v083/ai/analyze` mit `mode=weight`.
- Der zusätzliche Coverage-/Re-Transkriptionsdurchlauf aus 0.8.8/0.8.10 wird für Gewicht nicht mehr aufgerufen.
- Damit gibt es pro Eingabe wieder genau einen KI-Auswertungsdurchlauf; Ergebnisse zweier unterschiedlich gelesener Transkriptionen können nicht mehr versehentlich als zusätzliche Tiere/Messungen zusammengeführt werden.
- Die neuen kontextbezogenen KI-Einstiege für Medikament/Supplement und Symptom bleiben erhalten.

Behoben: #70.
