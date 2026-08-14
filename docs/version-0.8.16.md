# Animal Health 0.8.16

0.8.16 erweitert die in 0.8.15 eingeführten kompakten Serien um eine besser navigierbare Kalender- und Startseitenansicht und bereitet den Gesundheitschronik-PDF-Export fachlich neu auf.

## Kalender

- Der Monatskalender kann mit Pfeilen zum vorherigen und nächsten Monat durchgeblättert werden.
- Mit **Heute** wird direkt zum aktuellen Monat zurückgekehrt.
- Ein Filter begrenzt die Ansicht auf eine bestimmte Eintrags-/Aufgabenart.
- Ein zweiter Filter begrenzt die Ansicht auf ein bestimmtes Tier.
- Wiederkehrende Serien werden weiterhin virtuell aus Startdatum, Intervall und Enddatum berechnet. Für die Kalenderdarstellung werden keine zusätzlichen Datenbankeinträge pro Termin erzeugt.

## Startseite – relevant nach Zeitraum

Die bisherige starre Vorschau **innerhalb der nächsten 24 Stunden** wird ersetzt.

- Standard ist **Heute relevant**.
- Rechts oben kann kompakt zwischen **Heute**, **Diese Woche** und **Dieser Monat** gewechselt werden.
- Die Wochenansicht gliedert in **Heute relevant**, **Morgen relevant** und **Rest diese Woche**.
- Die Monatsansicht ergänzt **Nächste Woche** und **Rest diesen Monat**.
- Auch zukünftige Termine wiederkehrender Serien werden virtuell berücksichtigt. Wird z. B. die heutige Medikamentengabe abgeschlossen, bleibt die morgige geplante Gabe in der Wochen-/Monatsansicht sichtbar, obwohl dafür noch kein eigener persistierter Termin notwendig ist.

## Gesundheitschronik als PDF

Der Tier-PDF-Export ist als fachlicher Gesundheitsbericht aufgebaut und nicht mehr als Rohdarstellung der Datenbankdaten.

Reihenfolge:

1. **Tierdaten**
   - Stammdaten mit aktuellem Profilbild
   - Gruppendaten
   - aktuell laufende Therapien / Serien
2. **Gesundheitschronik**
   - neuester Eintrag zuerst

Für die Chronik werden nur gesundheitlich relevante Inhalte ausgegeben. Strukturierte interne Daten werden auf fachliche Felder wie Medikament, Dosis, Applikationsweg, Diagnose, Symptom, Pflege, Tierarzt/Praxis oder Impfstoff reduziert.

Nicht in den PDF-Bericht übernommen werden insbesondere:

- technische Datensatz- oder Attachment-IDs,
- interne Katalog- und Aufgabenmetadaten,
- rohe JSON-Strukturen,
- Timing-/Ausführungsmetadaten,
- der technische Korrektur-/Audit-Trail.

Bei korrigierten Einträgen wird im fachlichen Bericht nur der wirksame aktuelle Eintrag dargestellt. Die zugrunde liegenden unveränderlichen Auditdaten bleiben in Animal Health gespeichert und werden durch diese Darstellungsänderung nicht gelöscht.

Rückwirkend angelegte Medikamentenserien werden im PDF als lesbarer Serienhinweis dargestellt statt als interne `series_medication_started`-Struktur.
