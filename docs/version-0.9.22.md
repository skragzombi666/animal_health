# Animal Health 0.9.22

## Chronikaktionen

- `Kopieren` wurde aus Medikamentengaben, Medikamentengruppen und Behandlungsplan-Ausführungen entfernt, weil es funktional mit `Nochmals verabreichen/ausführen` redundant war.
- Chronikaktionen verwenden einheitliche Symbole:
  - Stift = Bearbeiten
  - Wiederholen = erneut verabreichen/ausführen
  - Papierkorb = Eintrag löschen
- Desktop zeigt Symbol + Text.
- Schmale/mobile Ansichten zeigen nur die Symbole; zugängliche `title`-/`aria-label`-Texte bleiben vorhanden.

## Schnell erfassen

- Alle Plus-Badges wurden vorerst vollständig entfernt.
- Kompakte Schnell-Erfassen-Ansicht: einfache gleichartige Symbolkacheln ohne Zusatzbadge.
- Erweiterte Ansicht: Symbol + Beschriftung, ebenfalls ohne Plus-Badge.
- `Gewicht erfassen` ist nicht mehr blau/primär hervorgehoben, sondern wird wie alle anderen Erfassungsarten dargestellt.
- Dieselbe neutrale Darstellung gilt auch in der Tierdetail-Schnellerfassung.

## Symptome

- Bei einem unbekannten Begriff wird direkt `Als neues eigenes Symptom speichern` angeboten.
- Nach dem Speichern steht das Symptom künftig in der eigenen Symptomenliste und im Dropdown zur Verfügung.
- Das Hinzufügen oder Entfernen weiterer Symptome rendert das komplette Formular nicht mehr neu. Bereits eingegebene Notizen, Schweregrad, Zeitpunkt und Tierauswahl bleiben dadurch erhalten.

## Produkte / Medikamente

- Bei einem unbekannten Produktnamen wird direkt `Als eigenes Produkt speichern` angeboten.
- Offizielle Swissmedic-Produkte und bereits manuell erfasste Produkte werden dabei erkannt und nicht nochmals als neu angeboten.
- Neu gespeicherte eigene Produkte stehen anschließend regulär in der Produktauswahl zur Verfügung.

## Android

Die eigenständige Android-Alpha bleibt unverändert bei `0.9.0-alpha.7` (`versionCode=900007`).
