# Animal Health 0.9.0-alpha.1

Die Version 0.9.0-alpha.1 ist der erste Cut von Animal Health als eigenständig testbare Android-App. Die bestehende Home-Assistant-Integration bleibt Teil derselben Versionsfamilie; zusätzlich wird erstmals eine installierbare Android-APK veröffentlicht.

## Standalone Android Alpha

Die Android-App benötigt für den Betrieb **kein Home Assistant**. Die Daten werden lokal auf dem Android-Gerät in einer eigenen SQLite-Datenbank gespeichert.

Der erste Alpha-Build enthält bewusst einen kompakten Kern für frühe Feldtests:

- Tiere lokal anlegen und anzeigen,
- Stammdaten pro Tier,
- Gewicht erfassen,
- mehrere Medikamente in einem gemeinsamen Erfassungsvorgang dokumentieren,
- Medikament, Dosis, Einheit und Applikationsweg kompakt erfassen,
- deutsche sichtbare Dosiseinheiten wie `Tablette`, `Tropfen`, `Dosis`, `µl` und `µg`,
- lokale eigene Medikamentenstammdaten mit bevorzugter Einheit und Applikationsweg,
- Gesundheitschronik neuester Eintrag zuerst und nach Tagen gruppiert,
- einzelne Medikamentengaben kopieren, bearbeiten oder erneut verabreichen,
- die Medikamentengaben eines ganzen Tages gemeinsam erneut vorbereiten,
- einfache lokale Aufgaben/Erinnerungen,
- vollständigen lokalen JSON-Export erzeugen.

## Alpha-Grenzen

Die Android-App ist noch **keine vollständige Portierung** der Home-Assistant-Integration. Insbesondere der kuratierte Medikamentenkatalog mit Zulassungs-/Off-Label-Filterung, KI-Erfassung, Anhänge/Bilder, Gruppenfunktionen, komplexe Serienaufgaben und weitere Verwaltungsfunktionen werden in den nächsten Alpha-Schritten portiert.

Der Off-Label-Schalter ist deshalb in der ersten Standalone-App noch nicht funktional: ohne den zentralen Zulassungskatalog gibt es aktuell nichts sinnvoll zu filtern. Eigene Medikamente können dennoch frei erfasst werden.

## Installation

Der GitHub-Release enthält zusätzlich zur Home-Assistant-Version eine Datei nach dem Muster:

`animal-health-0.9.0-alpha.1-android.apk`

Die APK ist für diese frühe Alpha direkt für Sideload-Tests gebaut und debug-signiert. Android kann beim Installieren aus dem Browser oder Dateimanager einmalig die Erlaubnis **Apps aus dieser Quelle installieren** verlangen.

## Ziel dieser Alpha

Im Vordergrund steht nicht vollständige Feature-Parität, sondern die Frage, ob Animal Health ohne Home Assistant für externe Tester bereits verständlich und praktisch nutzbar ist. Rückmeldungen zu Navigation, Erfassungsaufwand, Verständlichkeit und typischen Arbeitsabläufen sind für die nächsten Alpha-Versionen besonders wichtig.
