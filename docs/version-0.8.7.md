# Animal Health 0.8.7

0.8.7 behebt die Vorbelegung von Aufgaben aus der KI-Erkennung.

- Von der KI erkannte Aufgabenwerte werden bereits beim Rendern des Aufgabenformulars deterministisch eingesetzt und hängen nicht mehr nur von einem nachgelagerten DOM-/Timing-Schritt ab.
- Erkannte Aufgabenart, Tier, Titel, Beschreibung/Notiz, Wiederholung, Intervall, Startdatum und Fälligkeit werden übernommen, sofern sie vorhanden sind.
- Bei Medikamenten werden Medikament, Dosis, Einheit und Applikationsweg übernommen.
- Wenn die KI einen bekannten Tiernamen erkannt hat, wird zusätzlich frontendseitig eine exakte Namenszuordnung als Fallback verwendet.
- Ein erkannter Medikamentenname führt auch dann zur Aufgabenart `medication`, wenn die vorgeschlagene Eintragsart unerwartet fehlt.
- Fehlende oder unsichere Angaben werden weiterhin nicht erfunden; gespeichert wird erst durch den Benutzer.

Behoben: #61.
