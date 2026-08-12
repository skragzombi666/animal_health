# Animal Health 0.8.6

0.8.6 behebt die Review-Logik der KI-Mehrfacherfassung.

- Einträge gelten nach der KI-Erkennung nicht mehr automatisch als manuell geprüft.
- Der Button zeigt zunächst **Als geprüft markieren**.
- Nach Bestätigung ist der Zustand visuell hervorgehoben und kann über **Prüfung zurücknehmen** wieder aufgehoben werden.
- Nur explizit geprüfte und vollständige Einträge sind speicherbereit.
- **Alle geprüften Einträge speichern** berücksichtigt damit tatsächlich nur manuell geprüfte Einträge.
- Eine nachträgliche Änderung an Tier, Eintragsart, Wert, Datum/Zeit oder Notiz hebt den Prüfstatus wieder auf und erfordert eine erneute Bestätigung.
