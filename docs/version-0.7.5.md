# Animal Health 0.7.5

## Ziel

0.7.5 behebt drei im Praxistest von 0.7.4 gefundene Bedienfehler bei Aufgaben und Chronikdetails.

## Änderungen

### Deaktivierte Aufgaben

- Offene Vorkommnisse deaktivierter Aufgaben bleiben weiterhin aus Überfällig, Heute fällig, Demnächst, Kalender und Tierdetail ausgeblendet.
- Die Aufgabendefinition selbst bleibt jedoch im Bereich Aufgaben sichtbar.
- Deaktivierte Aufgaben werden ausdrücklich als `Deaktiviert` gekennzeichnet und können dort wieder über `Aktivieren` reaktiviert werden.
- Dies gilt auch für einmalige Aufgaben, deren offene Ausführung aufgrund der Deaktivierung ausgeblendet ist.

### Chronikdetails bei Statusänderungen

- Statusänderungen zeigen jetzt die tatsächliche Änderung mit vorherigem und neuem Status an.
- Beispiel: `Aktiv → Vermisst`.
- Die vorhandene Detaildarstellung für Messwerte, Notizen, Aufgabenbezug und Anhänge bleibt erhalten.

### «Tier öffnen» aus Chronikdetails

- `Tier öffnen` schliesst das Chronikdetail-Modal vor der Navigation.
- Anschliessend wird die Detailansicht des zugehörigen Tiers geöffnet.
- Ist das Tier bereits im Hintergrund geöffnet, bleibt das Modal nicht mehr über der Tieransicht stehen.

## Tests

Der Dashboard-Smoke-Test deckt zusätzlich ab:

- ausgeblendete offene Vorkommnisse deaktivierter Aufgaben,
- sichtbare und reaktivierbare deaktivierte Einmalaufgaben,
- Statuswechsel `vorher → neu` in Chronikdetails,
- korrektes Schliessen des Chronikdetail-Modals bei `Tier öffnen`.
