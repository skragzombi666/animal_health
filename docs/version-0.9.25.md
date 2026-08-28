# Animal Health 0.9.25

## Kontinuierliche Symptome

- Symptome, die gemeinsam erfasst wurden, werden über ihre bestehende Capture-Batch-Zuordnung erkannt und in **Aktuelle Symptome** kompakt als gemeinsame Gruppe dargestellt.
- Die Gruppe kann gemeinsam **verlängert**, **neu beurteilt** oder **beendet** werden.
- Ein Aufklappen der Gruppe zeigt weiterhin jedes Symptom einzeln mit den individuellen Aktionen.
- Auch in der Chronik werden gemeinsam erfasste Symptome zunächst als ein kompakter Eintrag dargestellt und können zu den einzelnen Symptomverläufen aufgeklappt werden.
- Die einzelnen Symptom-Episoden bleiben technisch eigenständige Datensätze. Die Gruppierung verändert oder verschmilzt die fachliche Historie nicht.
- Gruppenaktionen werden atomar ausgeführt und nur zugelassen, wenn die betroffenen Symptome tatsächlich aus demselben ursprünglichen Erfassungsvorgang stammen.

## Behandlungspläne und manuelle Medikamente

- Manuell angelegte Behandlungspläne können über das kompakte **⋮-Aktionsmenü** dupliziert werden.
- Manuell angelegte Medikamente können über dasselbe Bedienkonzept dupliziert werden.
- In der Bearbeitungsansicht steht zusätzlich **Als Kopie erstellen** als sekundäre Aktion zur Verfügung.
- Eine Kopie öffnet als vorausgefüllter neuer Entwurf und erhält beim Speichern eine eigene ID.
- Fachliche Stammdaten und Konfiguration werden übernommen; Anwendungen, Chronikeinträge und sonstige Historie werden nicht kopiert.
- Die Listen bleiben kompakt: Bearbeiten, Duplizieren sowie Archivieren/Wiederherstellen sind in einem einheitlichen Objektmenü gebündelt.

## Plattform

- Home-Assistant-Integration und Web-Frontend: **0.9.25**
- Android-App bleibt unverändert auf **0.9.0-alpha.7**.
