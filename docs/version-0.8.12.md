# Animal Health 0.8.12

0.8.12 behebt zwei Frontend-Probleme der KI-Mehrfacherfassung, ohne die in 0.8.11 wiederhergestellte Single-Pass-Gewichtserkennung zu verändern.

## KI-Mehrfacherfassung

- Aufgeklappte Einträge bleiben jetzt im normalen vertikalen Layoutfluss. Die geöffnete Karte vergrössert ihre Höhe und schiebt nachfolgende Karten nach unten; die Überlagerung in der Android/Home-Assistant-App entfällt.
- Die Kartenliste verwendet dafür einen stabilen vertikalen Flex-Flow; der frühere `overflow:visible`-Workaround wird überschrieben.
- Bei Mehrfach-Gewichtserfassungen übernimmt ein von der KI nicht einem bekannten Tier zugeordneter Eintrag nicht mehr automatisch das Tier, aus dessen Detailansicht die Erfassung gestartet wurde.
- Nur ein echtes `matched_animal_id` wird automatisch übernommen. Unbekannte Tiere bleiben ohne Zuordnung, grau/ungeprüft und müssen manuell einem vorhandenen Tier zugeordnet oder verworfen werden.
- Die Single-Pass-KI-Erkennung aus 0.8.11 bleibt unverändert auf `animal_health/v083/ai/analyze`.

Behoben: #72.
