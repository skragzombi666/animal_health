# Animal Health 0.7.4 – Work in progress

0.7.4 sammelt die Befunde aus dem Praxistest von 0.7.3. Die Version ist noch nicht releasebereit.

## Bereits umgesetzt

### Rassenkatalog

- Alle auswählbaren Tierarten auf vorhandene Rasseneinträge geprüft.
- Für Tierarten mit geeigneten anerkannten Rassen/Zuchttypen zusätzliche Einträge aus möglichst offiziellen bzw. anerkannten Zuchtquellen ergänzt.
- Schafe enthalten nun insbesondere die Schweizer/anerkannten Rassen wie Weisses Alpenschaf, Braunköpfiges Fleischschaf, Schwarzbraunes Bergschaf, Walliser Schwarznasenschaf, Engadinerschaf und weitere.
- Ergänzt wurden außerdem reale Rassen bzw. anerkannte Zuchttypen für Ente, Gans, Truthuhn, Wachtel, Taube, Meerschweinchen, Pferd, Esel, Rind, Schaf, Ziege, Schwein, Alpaka, Lama und Honigbiene.
- Für breite Kategorien ohne sinnvoll standardisierte Rassenliste werden keine künstlichen Rassen erfunden. Stattdessen stehen mindestens `Andere / nicht aufgeführt` sowie je nach Tierart `Rasse / Zuchtform / Art unbekannt` zur Verfügung.
- Die Rassenauflösung ist jetzt tierartspezifisch, damit gleichlautende generische Einträge nicht versehentlich einer anderen Tierart zugeordnet werden.
- Automatisierter Smoke-Test prüft, dass jede auswählbare Tierart Rassen oder explizite Fallbacks besitzt.

Siehe `docs/breed-catalogue.md` für Quellen und Abdeckungsentscheidungen.

## Noch offen

### Deaktivierte Aufgaben weiterhin als fällig sichtbar

Ist:
- Eine deaktivierte Aufgabe kann weiterhin mit bereits erzeugter offener Ausführung unter `Überfällig`, `Heute fällig` oder `Demnächst` erscheinen.

Soll:
- Vorkommnisse deaktivierter Aufgaben werden in den Fälligkeitsbereichen nicht angezeigt.
- Erledigte Historie bleibt erhalten.
- Bei erneuter Aktivierung wird die Serie korrekt fortgeführt, ohne doppelte Vorkommnisse zu erzeugen.
