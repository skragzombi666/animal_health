# Animal Health 0.9.0-alpha.2

0.9.0-alpha.2 korrigiert die Architektur der ersten Android-Alpha: Die Standalone-App verwendet jetzt **dieselbe Animal-Health-Oberfläche wie die Home-Assistant-Integration**. Es gibt keine separat nachgebaute Android-Oberfläche mehr.

## Eine gemeinsame Oberfläche

Die bestehenden Frontend-Dateien von Animal Health werden direkt in die Android-APK eingebunden. Navigation, Startseite, Tieransichten, Chronik, Kalender, Aufgaben, Tiergruppen, Einstellungen, Formulare und die Medikamentenerfassung stammen damit aus demselben Frontend wie in Home Assistant.

Änderungen an der gemeinsamen Oberfläche müssen künftig nicht getrennt für Home Assistant und Android nachgebaut werden.

## Standalone-Datenschicht

Unter Android stellt eine lokale Kompatibilitätsschicht die Schnittstellen bereit, die das gemeinsame Frontend benötigt. Die Daten liegen weiterhin lokal auf dem Gerät in SQLite; Home Assistant ist für den Betrieb der APK nicht erforderlich.

Der Standalone-Adapter umfasst insbesondere:

- Tiere und Stammdaten,
- Tiergruppen inklusive Gruppenzuordnung und Gruppenchronik,
- Tags,
- Tierbilder und Dokumentanhänge,
- Gewicht, Symptome und weitere Gesundheitsereignisse,
- Aufgaben und wiederkehrende Serien,
- Kalenderdaten und Aufgabenstatus,
- Medikamenten- und Impfstoffkataloge aus denselben Projektkatalogen wie die HA-Integration,
- eigene Medikamente und Off-Label-Einstellung,
- Mehrfacherfassung von Medikamenten,
- Bearbeiten, Kopieren und erneutes Verabreichen,
- Tagesgruppierung der Gesundheitschronik,
- Gruppenaufgaben und Gruppeneinträge,
- JSON-Export, vollständiges lokales Backup inklusive Anhängen sowie Tier- und Gruppen-PDF,
- lokale Diagnose- und Reset-Funktionen.

## Plattformfunktionen

Dateiauswahl, Kamera, lokale Anhänge und Exporte werden über eine Android-Bridge an das gemeinsame Frontend angebunden. Profilbilder und Bildanhänge können dadurch auch in der Standalone-App verwendet werden.

## KI

Die gemeinsame KI-Oberfläche ist ebenfalls enthalten. Die eigentliche KI-Auswertung benötigt – wie auch in Home Assistant – einen konfigurierten KI-Dienst. Die Standalone-App trifft keine medizinischen Entscheidungen; KI dient weiterhin nur zum Extrahieren und Vorausfüllen von Angaben vor der Kontrolle durch den Nutzer.

## Migration von alpha.1

Eine bestehende Installation von 0.9.0-alpha.1 wird mit derselben App-ID aktualisiert. Bereits lokal erfasste Tiere, Gewichte, Medikationen, Aufgaben und eigene Medikamente bleiben erhalten; die lokale Datenbank wird beim ersten Start um die zusätzlichen Strukturen erweitert.
