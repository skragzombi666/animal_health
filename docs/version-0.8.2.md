# Animal Health 0.8.2

0.8.2 bündelt die während der mobilen Testphase gemeldeten Korrekturen und UX-Verbesserungen.

## Tiere und Tiergruppen

- Tiere können wieder ohne Tiergruppe angelegt und gespeichert werden.
- Eine bestehende Gruppenzuordnung kann beim Bearbeiten eines Tiers entfernt werden.
- Die Tierübersicht enthält wieder einen Filter «Ohne Tiergruppe».
- Beim Auswählen eines Tierbilds wird Dateiname und Bildvorschau unmittelbar im Formular angezeigt.

## Bilder und Anhänge

- Tierprofilbilder werden vor dem Upload clientseitig auf eine UI-taugliche Grösse reduziert.
- Für Bildanhänge werden serverseitig gecachte Varianten erzeugt: Thumbnail, Profilbild und Preview.
- Chronik und Dokumentlisten laden zunächst nur kleine Thumbnails.
- Beim Öffnen eines Bilds wird zunächst eine Preview geladen; das unveränderte Original wird erst auf ausdrücklichen Wunsch geladen oder heruntergeladen.
- Originaldateien von Chronik-/Dokumentanhängen bleiben unverändert erhalten.

## Mobile Tieransicht

- Die Suche ist standardmässig auf ein Lupen-Symbol reduziert und wird bei Bedarf aufgeklappt.
- Der Tierwechsel ist horizontal scrollbar und benötigt keine grossen Vor-/Zurück-Schaltflächen mehr.
- Bearbeiten, Status, Archivierung und PDF-Export liegen in einem kompakten Überlaufmenü.
- Häufige Erfassungen bleiben direkt erreichbar; seltenere Aktionen liegen unter «Mehr».
- Stammdaten sind einklappbar und die dauerhaft sichtbaren Kennzahlen wurden reduziert.

## KI-Erfassung

- «KI-Dokumentassistent» wurde zu einer allgemeinen «KI-Erfassung» erweitert.
- Foto/PDF, freie Texteingabe und Diktat können einzeln oder kombiniert verwendet werden.
- Die KI erstellt weiterhin ausschliesslich einen Entwurf; gespeichert wird nur durch den Nutzer.
- «Gewicht erfassen» besitzt eine kontextbezogene KI-Erfassung, z. B. für ein Foto einer Waagenanzeige plus gesprochenen Tiernamen.
- Der Übergang von einem KI-Ergebnis in «Aufgabe anlegen» übernimmt erkannte Angaben tatsächlich in das Formular, einschliesslich Titel, Beschreibung, Tier, Medikament, Dosis, Einheit, Termin und explizit erkannter Wiederholung.
- Anzahl-Dosierungen wie «1 Tablette» bleiben Anzahl-Dosierungen und werden nicht auf `mg` zurückgesetzt.
- Unsichere oder widersprüchliche Tierzuordnungen werden als Hinweis angezeigt und nicht stillschweigend als sichere Zuordnung behandelt.

## Test-Reset

- Unter Einstellungen steht Administratoren während der Testphase ein Gefahrenbereich «Animal Health zurücksetzen» zur Verfügung.
- Der Reset löscht alle Animal-Health-Nutzdaten und lokalen Anhänge, entfernt die zugehörigen Entity-/Device-Registry-Einträge und lädt die Integration anschliessend leer neu.
- Die Home-Assistant-Installation und der Config Entry der Integration bleiben bestehen.
