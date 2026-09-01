# Animal Health 0.9.29

## Aufgaben direkt am Tier bearbeiten

- Der bisherige «Serienstatus» in der Tieransicht wird durch eine tierbezogene **Anstehend**-Ansicht ersetzt.
- Aufgaben lassen sich dort direkt bearbeiten, ohne zuerst auf «Aufgaben & Serien» zu wechseln.
- Medikamenten-, Entwurmungs-, Ergänzungs-, Futter- und Impfaufgaben zeigen ihre fachlichen Planwerte in der Bearbeitung.
- Änderungen an Planwerten werden auf offene, zukünftige Vorkommen übertragen. Bereits erledigte und dokumentierte Vorkommen bleiben unverändert.
- Der Bestätigungsmodus und die bestehende Zeitplanung bleiben in derselben Bearbeitungsmaske verfügbar.

## Präzisere Fälligkeiten

- Anstehende Aufgaben werden getrennt nach **Heute**, **Morgen**, **Übermorgen**, **Diese Woche**, **Nächste Woche** und späteren Zeiträumen gruppiert.
- Eine morgen fällige Aufgabe erscheint damit nicht mehr pauschal unter «Diese Woche».
- Dieselbe Gruppierungslogik wird auf der Startseite und in der jeweiligen Tieransicht verwendet.

## Kompaktere Chronik

- Medikamentengaben verwenden einen responsiven Umbruch: Passt der Produktname in eine Zeile, bleibt die Menge als schnell erfassbare Metazeile darüber. Muss der Name ohnehin umbrechen, wird die Menge in die erste Titelzeile integriert.
- In der tierübergreifenden Chronik steht der Tiername prominent in der oberen Metazeile; in einer einzelnen Tieransicht wird er weiterhin nicht redundant angezeigt.
- Nach dem Symbol «Aus Aufgabe» wird kein zusätzlicher Trennpunkt mehr ausgegeben.
- Chronikeinträge werden relativ in **Heute**, **Gestern**, **Vorgestern**, **Diese Woche**, **Letzte Woche**, **Dieser Monat**, **Letzter Monat** und **Älter** gegliedert. Die Zeiträume überschneiden sich nicht.
- Die Startseite verwendet dieselbe Logik, zeigt aber nur Gruppen, die für die dort sichtbaren letzten Einträge tatsächlich benötigt werden.

## Schnellerfassung

- Das verbliebene blaue Plus am Produkt-/Medikationssymbol der Schnellerfassung auf der Startseite wird entfernt. Die Tieransicht bleibt unverändert kompakt.

## Anhänge

- Bildvorschauen werden beim erneuten Öffnen mit frischen signierten URLs geladen.
- Bei abgelaufenen Vorschau-URLs versucht das Frontend genau einmal, eine neue URL anzufordern, statt dieselbe ungültige URL wiederholt zu verwenden.
- Tokenisierte Bildantworten werden nicht mehr im Browser/WebView zwischengespeichert.
- Abgelaufene interne Vorschau-Tokens werden als abgelaufene Ressourcen und nicht als fehlgeschlagene Home-Assistant-Anmeldung behandelt. Dadurch soll der sporadische `homeassistant.components.http.ban`-Logspam durch Attachment-Previews entfallen.
