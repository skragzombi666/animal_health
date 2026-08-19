# Animal Health 0.9.8

0.9.8 reduziert die obere Navigation auf die dauerhaft notwendigen Hauptbereiche und ersetzt den sichtbaren Aktualisieren-Knopf auf Touch-Geräten durch eine Pull-to-refresh-Geste.

## Obere Navigation

- «Tiergruppen» entfällt aus der oberen Navigationsleiste.
- Die obere Navigation enthält nur noch Übersicht, Chronik und Einstellungen.
- Tiergruppen bleiben über die gruppierte Tierübersicht auf der Startseite erreichbar.
- Ein Klick auf eine Gruppenüberschrift öffnet direkt die Detailansicht dieser Tiergruppe.
- Die vollständige Tiergruppenverwaltung inklusive Anlegen bleibt unter Einstellungen → Verwaltung & Daten → Tiergruppen verfügbar.

## Aktualisieren

- Der dauerhaft sichtbare Aktualisieren-Knopf rechts in der Kopfzeile entfällt.
- Eigene Erfassungen und Änderungen aktualisieren die Oberfläche weiterhin automatisch.
- Änderungen durch externe Home-Assistant-Dienste oder Automationen können auf Touch-Geräten aktualisiert werden, indem die Ansicht am Seitenanfang nach unten gezogen und nach Erreichen der Schwelle losgelassen wird.
- Während der Geste und der Aktualisierung erscheint eine kompakte Statusanzeige.
- Auf Desktop-Systemen bleiben die üblichen Browser- und Home-Assistant-Aktualisierungsmöglichkeiten verfügbar.

## Release

- 0.9.8 ist ein regulärer Home-Assistant/HACS-Release ohne Android-Build.
- Die Android-App bleibt auf 0.9.0-alpha.7 eingefroren.
