# Animal Health 0.9.10

0.9.10 trennt bei Serienaufgaben echte Überfälligkeit von fehlender Einzeldokumentation.

## Bestätigungsmodus pro Serie

Jede wiederkehrende Aufgabe besitzt einen Bestätigungsmodus:

- **Einzelbestätigung erforderlich:** Nach Ablauf des vorgesehenen Zeitraums bleibt die Fälligkeit offen, wird gelb als überfällig markiert und löst die Überfälligkeitsmeldung aus.
- **Routine ohne Einzelbestätigung:** Nach Ablauf des Zeitraums wird die Fälligkeit neutral als «Nicht einzeln dokumentiert» abgeschlossen. Dies behauptet ausdrücklich nicht, dass sie durchgeführt wurde, erzeugt aber keine Warnung.

Bei neuen Serien gelten folgende Voreinstellungen:

- Erinnerung und Pflege: Routine ohne Einzelbestätigung.
- Medikament, Behandlung, Impfung, Gewicht, Gesundheitskontrolle und Tierarzttermin: Einzelbestätigung erforderlich.
- Bestehende Serien bleiben aus Sicherheitsgründen auf «Einzelbestätigung erforderlich», bis sie bewusst umgestellt werden.
- Einmalige Aufgaben verlangen weiterhin immer eine explizite Bestätigung.

Der Modus kann beim Anlegen und unter «Aufgaben & Serien» beim Bearbeiten geändert werden.

## Fälligkeitszeiträume

- Täglich: der jeweilige Kalendertag.
- Wöchentlich: die gesamte konfigurierte Kalenderwoche.
- Monatlich: der gesamte Kalendermonat.
- Einmalig: der angegebene Termin nach der bisherigen Logik.

Damit erscheint eine wöchentliche Serie während der laufenden Woche unter «Diese Woche» und wird erst nach Ende dieser Woche überfällig beziehungsweise nicht einzeln dokumentiert. Der eingestellte Wochenanfang gilt jetzt auch für diese Backend-Logik.

## Kalender

- Grau mit Uhr: zukünftig geplant.
- Primärfarbe: aktuell fällig.
- Neutral mit Fragezeichen: nicht einzeln dokumentiert.
- Gelb mit Warnsymbol: wirklich überfällig und bestätigungspflichtig.
- Grün mit Häkchen: bestätigt beziehungsweise ausgeführt.
- Rot mit Kreuz: ausgesetzt, übersprungen oder abgebrochen.

Nicht einzeln dokumentierte Termine bleiben anklickbar und können nachträglich ausdrücklich dokumentiert werden.

## Startseite und Tieransicht

- Historische Routinevorkommen erscheinen nicht als offene Handlungsaufforderung unter «Anstehend».
- Wirklich überfällige Pflichtbestätigungen bleiben dort aggregiert sichtbar.
- Der Serienstatus eines Tiers weist neutral auf die Anzahl nicht einzeln dokumentierter Vorkommen hin.
- Die Gesundheitschronik wird weiterhin nicht mit automatischen Einträgen für nicht bestätigte Routinetermine geflutet.

## Meldungen

Persistente Home-Assistant-Meldungen und das Ereignis `animal_health_series_overdue` werden nur noch für Serien mit erforderlicher Einzelbestätigung und abgelaufenem Erledigungszeitraum erzeugt. Routinevorkommen lösen keine Warnung aus.

## Release

- 0.9.10 ist ein regulärer Home-Assistant/HACS-Release ohne Android-Build.
- Die Android-App bleibt auf 0.9.0-alpha.7 eingefroren.
