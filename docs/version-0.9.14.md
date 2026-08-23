# Animal Health 0.9.14

0.9.14 korrigiert mehrere Bedienungsdetails bei Navigation, Behandlungsplänen und Serienaufgaben und ergänzt eine weitere Dosiseinheit.

## Einstellungen immer rechts

Das Zahnrad für die Einstellungen bleibt als einziger Navigationspunkt im Kopfbereich und wird konsequent an den rechten Rand der Navigationsleiste geschoben. Produktlogo, Name und Versionsnummer beeinflussen seine Position nicht mehr.

## Medikamentenauswahl in Behandlungsplänen

Bei einem Bestandteil vom Typ «Medikament» ist der Produktname nicht mehr nur ein ungestütztes Freitextfeld. Die Auswahl verwendet jetzt dieselbe Medikamentenbasis wie die normale Medikamentenerfassung:

- aktive manuell erfasste Medikamente,
- Katalogmedikamente,
- Suche nach Produktname, Alias, Wirkstoff, Konzentration und Darreichungsform,
- strukturierte Trefferanzeige mit Produktname, Wirkstoff und Konzentration.

Die Tierart des Behandlungsplans wird bei der Auswahl berücksichtigt. Freie Eingabe bleibt weiterhin möglich.

## Lokalisierte Applikationswege

Die technischen Werte der Standard-Applikationswege bleiben unverändert, werden in der Oberfläche aber sprachabhängig dargestellt. In der deutschen Oberfläche erscheinen beispielsweise:

- Topisch
- Subkutan
- Intramuskulär
- Intravenös
- Auge
- Ohr

Die Lokalisierung greift überall, wo die vorhandene gemeinsame Anzeige der Applikationswege verwendet wird, insbesondere bei Medikamenten, Aufgaben und Behandlungsplänen.

## Dosiseinheit Kaffeelöffel

Als zusätzliche Dosiseinheit steht «Kaffeelöffel» zur Verfügung. Der technische Wert lautet `coffee_spoon`. Die Einheit wird nicht automatisch in Milliliter umgerechnet; sie bleibt eine eigenständige dokumentierte Dosiseinheit.

## Tägliche Serien und Überfälligkeit

Die Startseite reduziert eine Serie nicht mehr so, dass eine offene Fälligkeit des Vortags die aktuelle Fälligkeit verdeckt.

Bei einer täglichen Aufgabe kann dadurch gleichzeitig erscheinen:

- die zuletzt offene vergangene Fälligkeit als **überfällig**,
- die aktuelle beziehungsweise nächste Fälligkeit als regulärer Serieneintrag.

Die zugrunde liegenden Occurrences bleiben weiterhin getrennte Datensätze mit eigenem Status. Um die kompakte Startseite nicht mit langen Serienrückständen zu fluten, wird dort die zuletzt überfällige Instanz zusätzlich zur aktuellen/nächsten Instanz gezeigt; in der Aufgabenansicht bleiben sämtliche offenen Occurrences verfügbar.

## Release

- 0.9.14 ist ein regulärer Home-Assistant/HACS-Release.
- Die Android-App bleibt unverändert auf 0.9.0-alpha.7 eingefroren.
