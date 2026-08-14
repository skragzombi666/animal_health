# Animal Health 0.8.17

0.8.17 optimiert die Medikamentenerfassung und die Gesundheitschronik für wiederkehrende praktische Abläufe.

## Kompakte Mehrfacherfassung von Medikamenten

Bei **Medikament / Supplement** werden Tier, Datum, Uhrzeit und gemeinsame Notiz nur einmal erfasst. Darunter können beliebig mehrere Medikamentengaben ergänzt werden. Jede Gabe bleibt intern ein eigener Gesundheitsdatensatz, wird aber gemeinsam gespeichert.

Die einzelne Medikamentenzeile ist kompakt aufgebaut:

- Medikament,
- Dosis,
- Einheit direkt neben der Dosis,
- optionaler Applikationsweg,
- `Weiteres Medikament` für zusätzliche Gaben.

Bei erkennbaren Tablettenpräparaten wird `Tablette` automatisch als Einheit vorausgewählt; bei Tropfen entsprechend `Tropfen`. Für eigene Medikamente kann die bevorzugte Einheit explizit in den Einstellungen hinterlegt werden.

## Deutsche Dosiseinheiten

Sichtbare Einheiten werden lokalisiert, ohne die stabilen internen Werte zu verändern:

- `tablet` → `Tablette`
- `drop` → `Tropfen`
- `dose` → `Dosis`
- `ul` → `µl`
- `mcg` → `µg`

Die Lokalisierung gilt auch für den Gesundheits-PDF-Export.

## Chronik nach Tagen

Chronikeinträge werden visuell nach Datum gruppiert. Ein Tageskopf zeigt kompakt, welche Arten von Einträgen vorhanden sind. Medikamentengaben erscheinen in der Draufsicht beispielsweise als `1 Tablette Doxycyclin` oder `0,5 ml Metacam`.

Ein Klick auf den Tageskopf öffnet eine Tagesübersicht. Wenn der Tag Medikamentengaben für ein einzelnes Tier enthält, können alle Medikamentengaben dieses Tages gemeinsam erneut vorbereitet werden.

## Medikamentengabe wiederverwenden

Im Detail einer Medikamentengabe stehen jetzt drei direkte Aktionen zur Verfügung:

- **Bearbeiten** – legt fachlich eine Korrektur an; der ursprüngliche Datensatz bleibt intern nachvollziehbar erhalten.
- **Kopieren** – übernimmt Medikament, Dosis, Einheit und Applikationsweg in eine neue Erfassung; das Tier kann gewechselt werden.
- **Nochmals verabreichen** – übernimmt die Gabe für dasselbe Tier mit aktuellem Datum und aktueller Uhrzeit. Vor dem Speichern können Zeitpunkt und Details geändert werden.

Der redundante Knopf `Tier öffnen` wird innerhalb einer bereits geöffneten Tieransicht nicht mehr angezeigt.

## Eigene Medikamente und Off-Label-Einstellung

Unter **Einstellungen → Medikamente verwalten** können fehlende Medikamente selbst ergänzt werden. Dabei können Tierart, Standard-Dosiseinheit und Standard-Applikationsweg hinterlegt werden.

Die bereits vorhandene Off-Label-Auswahl ist nun global konfigurierbar. **Standardmässig ist sie deaktiviert.** Erst nach Aktivierung in den Einstellungen werden Präparate anderer Tierarten in den entsprechenden Auswahllisten angeboten.

## Datenhaltung

Eine gemeinsam erfasste Medikamentenkombination bleibt transaktional und fachlich sauber getrennt: Jede Gabe erhält einen eigenen Gesundheitschronik-Eintrag, während ein interner Batch-Bezug die gemeinsame Erfassung kennzeichnet. Technische Batch-Informationen werden nicht in der kompakten Chronik angezeigt.
