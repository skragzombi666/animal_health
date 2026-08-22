# Animal Health 0.9.11

0.9.11 erweitert die Medikamentenerfassung und ergänzt einen wiederverwendbaren Katalog für Behandlungen und Behandlungspläne.

## Medikamente und Off-Label

- Medikamente werden in der Erfassung grundsätzlich für jedes Tier angeboten.
- Ist die Off-Label-Kennzeichnung deaktiviert, werden Präparate anderer Tierarten ohne zusätzliche Off-Label-Markierung angezeigt.
- Ist die Off-Label-Kennzeichnung aktiviert, bleiben weiterhin alle Präparate auswählbar; Präparate mit abweichender Tierart werden zusätzlich als Off-Label gekennzeichnet.
- Die Einstellung steuert damit die Kennzeichnung, nicht mehr die grundsätzliche Sichtbarkeit eines Präparats.

## Manuelle Medikamenteneingabe

- In der direkten Medikamentenerfassung ist der Präparatname wieder frei editierbar.
- Die bekannte Medikamentenliste wird als Vorschlagsliste angeboten, ohne die Eingabe auf vorhandene Katalogeinträge zu beschränken.
- Auch beim Anlegen einer Medikamentenaufgabe bleibt eine freie Eingabe möglich.
- Für bekannte eigene Medikamente und Behandlungspläne werden hinterlegte Standard-Einheit und Standard-Applikationsweg weiterhin übernommen.

## Dosiseinheit «Teilstrich»

- «Teilstrich» ist als zusätzliche Dosiseinheit verfügbar.
- Die Einheit steht in der Medikamentenerfassung, bei eigenen Medikamenten, bei Behandlungsplänen und in den Home-Assistant-Dienstselektoren zur Verfügung.
- Exporte verwenden ebenfalls die Bezeichnung «Teilstrich».

## Behandlungen und Behandlungspläne

Unter Einstellungen können wiederverwendbare Behandlungen beziehungsweise Behandlungspläne angelegt werden. Pro Plan können festgelegt werden:

- Name
- optionale Tierart
- Beschreibung beziehungsweise Plan
- wo der Eintrag angeboten wird:
  - Medikament
  - Aufgabe / Behandlung
  - Medikament und Aufgabe
- Standard-Dosiseinheit
- optionaler Standard-Applikationsweg

Ein Plan, der bei «Medikament» angeboten wird, erscheint in der Medikamentenauswahl und kann dort mit Dosis dokumentiert werden. Ein Plan, der bei «Aufgabe / Behandlung» angeboten wird, erscheint beim Anlegen einer Behandlungsaufgabe als Vorschlag und kann Titel sowie Beschreibung vorausfüllen. Die freie Eingabe bleibt in beiden Fällen möglich.

Behandlungspläne können in den Einstellungen wieder gelöscht werden.

## Release

- 0.9.11 ist ein regulärer Home-Assistant/HACS-Release ohne Android-Build.
- Die Android-App bleibt auf 0.9.0-alpha.7 eingefroren.
