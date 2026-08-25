# Animal Health 0.9.21

## Chronik: Behandlungspläne

- Ausgeführte Behandlungspläne verwenden wieder dieselbe Grunddarstellung wie andere Chronikeinträge.
- Datum/Zeit und Tierbezug sind direkt im zusammenfassenden Eintrag sichtbar.
- Die Bestandteile bzw. Behandlungsschritte werden bereits im eingeklappten Zustand als kompakte Zusammenfassung untereinander angezeigt.
- Ein einzelner, vertikal zentrierter Chevron am rechten Rand klappt die Details auf und zu.
- Beim Aufklappen erscheinen die tatsächlich erzeugten Medikament-/Produkteinträge eingerückt unter dem Behandlungsplan.
- Handlungsschritte des Behandlungsplans werden ebenfalls als eingerückte Unterelemente dargestellt.
- Ein kompletter Behandlungsplan kann aus der Chronik erneut ausgeführt oder kopiert werden; einzelne Medikamenteneinträge bleiben separat bedienbar.

## Chronik: gemeinsam erfasste Medikamente

- Mehrere Medikamente, die in einer gemeinsamen Erfassung gespeichert wurden, werden anhand der bereits vorhandenen `batch_id` als eine Gruppe dargestellt.
- Im eingeklappten Zustand zeigt die Gruppe Datum/Zeit, Tier und eine kompakte Zusammenfassung aller Gaben.
- Die Gruppe kann aufgeklappt werden; darunter bleiben die einzelnen Medikamentengaben als echte, separat öffnungs- und wiederholbare Chronikeinträge erhalten.
- Die komplette Medikamentengruppe kann auf einmal kopiert oder nochmals verabreicht werden.
- Die Gruppierung wird auch in der Startseiten-Chronik berücksichtigt, bevor die letzten zehn sichtbaren Einträge ausgewählt werden.

## Kompatibilität

- Es ist keine Datenmigration erforderlich: Mehrfacherfassungen besitzen bereits eine persistente `batch_id`.
- Bestehende Behandlungsplan-Verknüpfungen aus 0.9.20 werden weiterverwendet.
- Die eigenständige Android-Alpha bleibt unverändert auf `0.9.0-alpha.7`.
