# Animal Health 0.9.18

## Behandlungspläne

- Neue Behandlungspläne verwenden bei **«Anzeigen bei»** standardmässig **«Medikament und Aufgabe»** (`both`).
- Bestehende Behandlungspläne können direkt bearbeitet werden, inklusive Name, Tierart, Anzeigeziel, Beschreibung und Komponenten.
- Behandlungspläne werden im normalen UI nicht mehr gelöscht, sondern archiviert.
- Archivierte Behandlungspläne werden aus normalen Medikament-/Produkt- und Aufgabenauswahlen ausgeblendet.
- In der Verwaltung können archivierte Pläne optional eingeblendet und wiederhergestellt werden.
- Ein archivierter Plan bleibt vollständig in der Datenbank erhalten; vorhandene historische Dokumentationen und bereits gespeicherte Aufgaben-/Ausführungsdaten werden nicht rückwirkend verändert.

## Migration

Bestehende Installationen erhalten für Behandlungspläne die Felder `is_archived` und `archived_at`. Vorhandene Pläne starten als aktiv und bleiben unverändert nutzbar.

## Android

Die eigenständige Android-Alpha bleibt weiterhin auf `0.9.0-alpha.7` eingefroren. 0.9.18 aktualisiert die Home-Assistant-Integration.
