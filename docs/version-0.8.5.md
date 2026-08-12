# Animal Health 0.8.5

0.8.5 ist ein Hotfix für die unmittelbar nach 0.8.4 gemeldeten Einstellungs-/Administrationsprobleme.

## Datenbankdiagnose

- Die Admin-Prüfung des WebSocket-Endpunkts verwendet nun den aktuellen Home-Assistant-Mechanismus `@websocket_api.require_admin`.
- Einzelne Diagnoseprüfungen werden robust abgefangen und als verständlicher Diagnosefehler zurückgegeben, statt den gesamten Vorgang mit `Unknown error` abzubrechen.
- `integrity_check`, `foreign_key_check`, Schema-, Index- und Attachment-Prüfung bleiben nicht destruktiv.

## Testdaten zurücksetzen, Stammdaten behalten

Unter Einstellungen steht zusätzlich **Verlaufs- und Aufgabendaten zurücksetzen** zur Verfügung.

Gelöscht werden:

- Chronik-/Gesundheitseinträge inklusive Gewichte und Symptome,
- Medikamenten-/Behandlungs-/Pflegeereignisse,
- Gruppenchronik,
- Aufgaben, Serien und alle erzeugten Vorkommnisse,
- zu diesen Daten gehörende Anhänge.

Erhalten bleiben:

- Tiere und Tierstammdaten,
- Tiergruppen und Gruppenzuordnungen,
- Tags und Tag-Zuordnungen,
- Tier-/Gruppenmetadaten und lokale Stammdaten,
- Tierbilder samt zugehörigem Attachment.

Der Löschvorgang läuft transaktional; nach dem Löschen wird `foreign_key_check` ausgeführt. Nicht mehr benötigte Attachment-Dateien werden anschliessend entfernt.

## Originales Animal-Health-Logo

Die Panel-Kopfzeile verwendet nun direkt `custom_components/animal_health/brand/icon.png`. Das ist dieselbe Bilddatei, die HACS/Home Assistant als lokales Brand-Icon verwendet, und damit identisch mit dem Original-Icon des Repositories.

## Version

Die Manifest-/Frontend-Version wird auf 0.8.5 erhöht, damit die Korrektur bei HACS-Verwaltung eindeutig als neuer Stand erkannt werden kann.
