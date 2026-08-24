# Animal Health 0.9.16

0.9.16 behebt die Speicherung von Behandlungsaufgaben und vereinheitlicht die Schnell-Erfassen-Symbolsprache auf Startseite und Tierdetailansicht.

## Behandlungsaufgaben

Behandlungsaufgaben (`task_kind = treatment`) waren in der Oberfläche bereits verfügbar, wurden aber bei bestehenden Installationen noch durch eine ältere SQLite-CHECK-Constraint in `task_record_configs` blockiert. Dadurch konnten insbesondere wiederkehrende beziehungsweise tägliche Behandlungsaufgaben nicht gespeichert werden.

0.9.16:

- ergänzt `treatment` in der aktuellen Task-Record-Schema-Definition,
- migriert bestehende `task_record_configs` verlustfrei auf die erweiterte Constraint,
- erhält bestehende Aufgabenkonfigurationen, Templates und Bestätigungsmodi,
- führt die Migration vor der regulären Task-Record-Schema-Initialisierung aus,
- lässt die bestehenden Trigger und Indizes danach regulär neu anlegen.

Damit können einmalige und wiederkehrende Behandlungsaufgaben, einschliesslich täglicher Behandlungspläne, gespeichert werden.

## Konsistente Schnell-Erfassen-Symbole

Die Erfassungsaktionen verwenden jetzt auf der Startseite und in der Tierdetailansicht dieselbe visuelle Logik:

- ein fachliches Kernsymbol ohne integriertes Plus,
- ein identisches, separat überlagertes Plus-Badge,
- gleiche Badge-Position, Grösse und Linienführung,
- kompakte Beschriftung unter dem Symbol.

Die Kernsymbole sind unter anderem:

- Gewicht: Waage,
- Symptom: Warn-/Symptomkreis,
- Medikation: Pille,
- allgemeiner Eintrag: Dokument ohne Plus,
- Aufgabe: Clipboard ohne Plus,
- KI-Erfassung: Sparkle/Creation-Symbol,
- Anhang in der Tieransicht: Büroklammer.

Damit enthalten insbesondere Dokument- und Clipboard-Symbole kein zweites, redundantes Plus mehr. Das gemeinsame überlagerte Plus ist der einzige visuelle Marker für «neu erfassen / hinzufügen».

## Release

- Home-Assistant/HACS-Version: 0.9.16
- Android bleibt unverändert auf 0.9.0-alpha.7 eingefroren.
