# Animal Health 0.9.17

## Tiergruppen und Sortierung

- Die Tiergruppenübersicht ist direkt aus dem Tierbereich der Startseite erreichbar.
- Eine geöffnete Tiergruppe zeigt ihre Tiere als kompakte Kachelübersicht.
- Die Reihenfolge der Tiere kann innerhalb der Gruppe angepasst werden.
- Diese Reihenfolge wird auch auf der Startseite, im Tierwechsler und in Tierauswahllisten verwendet.
- Die Reihenfolge der Tiergruppen kann in den Einstellungen angepasst werden und gilt global.

## Aufgaben und Serien

- Aufgaben ohne hinterlegte Uhrzeit zeigen keine künstliche `00:00` mehr.
- Bei Serien mit Pflichtbestätigung bleibt eine vergangene offene Fälligkeit sichtbar, während die aktuelle Fälligkeit zusätzlich angezeigt wird.
- Eine nicht bestätigte Medikamentengabe vom Vortag wird dadurch nicht mehr durch die heutige Serieninstanz verdrängt.

## Einheitliches Produktmodell

- Behandlungspläne unterscheiden nicht mehr künstlich zwischen Medikament und Nahrungsergänzung.
- Komponenten verwenden `Produkt`, `Futter` oder `Handlung / Pflegeschritt`.
- Medikamente, Ergänzungs-/Futtermittel, Pflegeprodukte und sonstige Produkte werden gemeinsam in einer Produktverwaltung geführt.
- Die Produktart ist eine Klassifikation und kein eigener Auswahlpfad.
- Bestehende manuelle Medikamente bleiben erhalten und können bei Bedarf neu klassifiziert werden.
- Historische Produktgaben erhalten die beim Speichern gültige Produktkategorie im Snapshot.

## Schnell erfassen

- Das Schnell-Erfassen-Design wurde für Desktop und schmale/mobile Ansichten nachgeschärft.
- Alle Aktionen verwenden ein Kernsymbol ohne eingebautes Plus sowie dasselbe überlagerte Plus-Badge.
- Position, Grösse und Abstände sind auf Startseite und Tierdetailansicht vereinheitlicht.

## Android

Die eigenständige Android-Alpha bleibt weiterhin auf `0.9.0-alpha.7` eingefroren. Die Home-Assistant-Integration wird mit 0.9.17 aktualisiert.
