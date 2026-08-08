# Animal Health 0.7.4

0.7.4 sammelt die Befunde aus dem Praxistest von 0.7.3 und behebt insbesondere Aufgaben-, Download-, Chronik- und Katalogprobleme.

## Aufgaben

- Offene Vorkommnisse deaktivierter Aufgaben werden in der Oberfläche nicht mehr unter `Überfällig`, `Heute fällig`, `Demnächst`, Kalender oder Tierdetail als fällig angezeigt.
- Die Kennzahlen für offene, überfällige, heutige und kommende Aufgaben werden nach derselben Logik neu berechnet.
- Erledigte Historie bleibt sichtbar.
- Wird eine Aufgabe wieder aktiviert, werden ihre vorhandenen offenen Vorkommnisse wieder berücksichtigt; es werden durch die Sichtbarkeitslogik keine Duplikate erzeugt.

## Chronik und letzte Einträge

- Chronikeinträge bzw. Einträge unter `Letzte Einträge` sind anklickbar.
- Ein Klick öffnet eine Detailansicht mit Tier, Eintragsart, Zeitpunkt, Wert, Notizen, Aufgaben-/Quellenbezug und vorhandenen Anhängen.
- Von der Detailansicht kann direkt zum zugehörigen Tier gewechselt werden.
- Interne Titel wie `status_change` und bekannte Symptomschlüssel wie `diarrhea` werden lokalisiert angezeigt.

## Downloads und Datensicherung

- Signierte Download-URLs für JSON, vollständiges Backup, Gesundheitschronik-PDF und Anhänge sind für einen kurzen Zeitraum wiederverwendbar statt nach dem ersten HTTP-Zugriff ungültig zu werden.
- Dadurch sind Android-WebView-/Download-Manager-Retries möglich, die zuvor zu sporadischen `Fehler bei Download`-Meldungen bzw. `<Unbenannt>` führen konnten.
- Nach dem ersten gültigen Zugriff bleibt der unguessbare Transfer-Token 15 Minuten gültig; abgelaufene oder falsche Tokens werden weiterhin abgewiesen.
- Die bestehende direkte Downloadlogik und die Dateinamen aus `Content-Disposition` bleiben erhalten.

## Rassenkatalog

- Alle auswählbaren Tierarten wurden auf vorhandene Rasseneinträge geprüft.
- Für Tierarten mit geeigneten anerkannten Rassen/Zuchttypen wurden zusätzliche Einträge aus möglichst offiziellen bzw. anerkannten Zuchtquellen ergänzt.
- Schafe enthalten nun insbesondere Schweizer/anerkannten Rassen wie Weisses Alpenschaf, Braunköpfiges Fleischschaf, Schwarzbraunes Bergschaf, Walliser Schwarznasenschaf, Engadinerschaf und weitere.
- Ergänzt wurden außerdem reale Rassen bzw. anerkannte Zuchttypen für Ente, Gans, Truthuhn, Wachtel, Taube, Meerschweinchen, Pferd, Esel, Rind, Schaf, Ziege, Schwein, Alpaka, Lama und Honigbiene.
- Für breite Kategorien ohne sinnvoll standardisierte Rassenliste werden keine künstlichen Rassen erfunden. Stattdessen stehen mindestens `Andere / nicht aufgeführt` sowie je nach Tierart `Rasse / Zuchtform / Art unbekannt` zur Verfügung.
- Die Rassenauflösung ist tierartspezifisch, damit gleichlautende generische Einträge nicht versehentlich einer anderen Tierart zugeordnet werden.
- Automatisierte Tests prüfen, dass jede auswählbare Tierart reale Rassen oder explizite Fallbacks besitzt.

Siehe `docs/breed-catalogue.md` für Quellen und Abdeckungsentscheidungen.

## Tests

Die CI prüft zusätzlich:

- vollständige Rassenabdeckung bzw. Fallbacks,
- deaktivierte Aufgaben in der Frontend-Sichtbarkeit,
- klickbare und lokalisierte Chronikeinträge,
- retry-sichere Download-Tokens,
- JavaScript-Syntax und Python-Kompilierung neben den bestehenden Smoke-Tests.

## Update

Nach dem Merge auf `main`:

```sh
cd /config/animal_health
git switch main
./scripts/update.sh
```

Das Deploy-Skript sichert die bisher installierte Integration, kopiert die neue Version nach `/config/custom_components/animal_health`, führt `ha core check` aus und startet Home Assistant Core neu.
