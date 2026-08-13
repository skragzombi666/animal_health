# Animal Health 0.8.13

0.8.13 stabilisiert die Tierzuordnung und den manuellen Prüfstatus der kompakten KI-Mehrfacherfassung, ohne die in 0.8.11 wiederhergestellte ursprüngliche Single-Pass-KI-Erkennung zu verändern.

## KI-Gewichtserfassung

- Der KI-Aufruf bleibt unverändert auf `animal_health/v083/ai/analyze` mit `mode=weight`; Prompt und Extraktionslogik aus 0.8.3 werden nicht verändert.
- Exakt erkannte Tiernamen werden weiterhin direkt zugeordnet.
- Falls der erkannte Name knapp von einem bekannten Tiernamen abweicht, wird zusätzlich lokal und deterministisch ein konservativer Ähnlichkeitsabgleich durchgeführt. Nur ein eindeutig bester, sehr naher Treffer wird vorgeschlagen.
- Eine solche Ähnlichkeitszuordnung bleibt bewusst unsicher/grau und muss manuell geprüft werden. Echte unbekannte Tiere bleiben unzugeordnet.

## Manuelle Korrektur

- Änderungen in den Detailfeldern der Batch-Ansicht werden jetzt sofort in den internen Entwurf übernommen, auch wenn die Felder nicht in einem HTML-Formular liegen.
- Nach manueller Auswahl eines Tiers ist ein ansonsten vollständiger Eintrag unmittelbar prüfbar; das graue Fragezeichen kann auf grün/manuell geprüft gesetzt werden.
- Die ursprünglich von der KI gelesene Tierbezeichnung bleibt von einer manuellen Zuordnung getrennt.

Behoben: #74.
