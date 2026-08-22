# Animal Health 0.9.12

0.9.12 erweitert Behandlungspläne zu echten Mehrkomponenten-Abläufen, macht die Off-Label-Logik vollständig konfigurierbar und ergänzt datierte beziehungsweise geplante Tierstatusänderungen.

## Behandlungspläne mit mehreren Bestandteilen

Ein Behandlungsplan kann jetzt beliebig viele feste Bestandteile und Handlungsschritte enthalten. Unterstützt werden:

- Medikament
- Nahrungsergänzung
- Futter
- Handlung / Pflegeschritt

Für Medikament, Nahrungsergänzung und Futter können Produktname, feste Menge beziehungsweise Dosis, Einheit, optionaler Applikationsweg und ein Durchführungshinweis hinterlegt werden. Für Handlungen werden Name und Durchführungshinweis hinterlegt.

Zusätzlich zur Einheit «Teilstrich» steht «Messerspitze» zur Verfügung.

Damit lassen sich beispielsweise abbilden:

- Kaolin + Vitaminpulver + BeneBact Plus, jeweils 1 Messerspitze, anschliessend mit Wasser mischen und verabreichen.
- Füsse reinigen → desinfizieren → mit Gaze und Verbandsmaterial verbinden.
- Futter in einer festgelegten Menge verabreichen → anschliessend Kropf massieren.

## Behandlungsplan ausführen

Behandlungspläne mit Anzeigeziel «Medikament» beziehungsweise «Medikament und Aufgabe» können aus der Medikamentenerfassung direkt als kompletter Plan ausgewählt und mit einer Aktion dokumentiert werden.

Bei der Ausführung:

- entsteht ein zusammenfassender Behandlungseintrag mit dem vollständigen Plan,
- Medikament- und Supplementbestandteile erhalten zusätzlich eigene Medikamenteneinträge mit der hinterlegten Dosis,
- Futterbestandteile werden zusätzlich als Pflege-/Futtereintrag dokumentiert,
- reine Handlungsschritte bleiben nachvollziehbar im zusammenfassenden Behandlungseintrag erhalten.

Behandlungspläne mit Anzeigeziel «Aufgabe / Behandlung» beziehungsweise «beides» können mit einer Behandlungsaufgabe verknüpft werden. Wird diese Aufgabe ausgeführt, werden die im Plan hinterlegten Bestandteile ebenfalls dokumentiert.

## Off-Label-Anzeige

Die bisherige einzelne Off-Label-Einstellung wird durch vier eindeutige Modi ersetzt:

1. **Alle Medikamente immer anzeigen**  
   Tierart-Zuordnungen beeinflussen die Auswahl nicht; es erfolgt keine besondere Off-Label-Markierung.

2. **Alle anzeigen und Off-Label markieren**  
   Alle Medikamente bleiben sichtbar. Präparate, deren Tierart nicht zum ausgewählten Tier passt, werden mit «⚠ Off-Label» gekennzeichnet.

3. **Off-Label grundsätzlich ausblenden**  
   Bei einem Tier werden nur passende oder tierartunabhängige Präparate angeboten.

4. **Off-Label nur auf ausdrücklichen Wunsch anzeigen**  
   Off-Label-Präparate sind standardmässig ausgeblendet. Nur in diesem Modus erscheint in der Medikamentenerfassung beziehungsweise beim Anlegen einer Medikamentenaufgabe die Option «Off-Label anzeigen». Nach Aktivierung werden die zusätzlichen Präparate eingeblendet und gekennzeichnet.

Die freie manuelle Eingabe eines Medikamentennamens bleibt unabhängig davon möglich.

## Tierstatus mit tatsächlichem Zeitpunkt

Bei einer Statusänderung kann jetzt immer angegeben werden, **wann die Änderung tatsächlich erfolgt ist beziehungsweise wirksam werden soll**.

- Zeitpunkt in der Vergangenheit: Der Status wird sofort übernommen, aber mit dem angegebenen historischen Zeitpunkt dokumentiert.
- Aktueller Zeitpunkt: Der Status wird wie bisher sofort übernommen.
- Zeitpunkt in der Zukunft: Der aktuelle Tierstatus bleibt zunächst unverändert; stattdessen wird eine geplante Statusänderung angelegt.

Auch ein bereits gesetzter Status kann mit einem korrigierten historischen Zeitpunkt erneut gespeichert werden. Beispiel: Ein Tier wurde heute als verstorben markiert, ist tatsächlich aber bereits eine Woche zuvor verstorben. Der Statuszeitpunkt wird korrigiert und die Korrektur bleibt nachvollziehbar.

## Geplante Statusänderungen

Eine zukünftige Statusänderung erscheint beim betreffenden Tier als geplante Änderung. Sobald der Zeitpunkt erreicht ist:

- erscheint sie unter «Anstehend» als **Statusänderung fällig**,
- Home Assistant erzeugt eine persistente Erinnerung,
- zusätzlich wird das Ereignis `animal_health_status_change_due` ausgelöst.

Die fällige Änderung kann anschließend:

- **wie geplant bestätigt** werden,
- mit einem **anderen tatsächlichen Zeitpunkt** bestätigt werden,
- auf einen **neuen zukünftigen Zeitpunkt verschoben** werden,
- oder vollständig **abgebrochen** werden.

Der Status des Tiers ändert sich bei einer Zukunftsplanung ausdrücklich erst nach dieser Bestätigung.

## Release

- 0.9.12 ist ein regulärer Home-Assistant/HACS-Release ohne Android-Build.
- Die Android-App bleibt auf 0.9.0-alpha.7 eingefroren.
