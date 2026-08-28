# Animal Health 0.9.24

## Bearbeiten und Audit

- Jeder in der Chronik erfasste Eintrag erhält einen nachvollziehbaren Bearbeitungsweg.
- Allgemeine Einträge und Gewicht werden als Korrekturversion gespeichert; die vorherige Fassung bleibt im Audit Trail erhalten.
- Medikamentenkorrekturen behalten Anhänge und – wenn die Gabe Teil eines Behandlungsplans ist – ihre Gruppenzuordnung.
- Symptom-Episoden und einzelne Verlaufsbeurteilungen können nachträglich korrigiert werden, ohne eine neue Episode zu erzeugen.
- Ausgeführte Behandlungspläne werden als atomare Gruppe bearbeitet: Datum, Uhrzeit/Datum-ohne-Uhrzeit und Notiz werden gemeinsam für Parent und Kinder korrigiert.
- Statusänderungen können ebenfalls als auditierbare Korrektur bearbeitet werden.

## Anhänge und Bilder

- Eine gemeinsame Mehrfachanhang-Logik wird an allen Erfassungsstellen verwendet.
- Mehrere Dateien können gleichzeitig gewählt und weitere Dateien oder Kameraaufnahmen nacheinander ergänzt werden.
- Vor dem Speichern werden alle ausgewählten Anhänge aufgelistet; einzelne Dateien können mit X wieder entfernt werden.
- Bilder erhalten bereits in der Auswahl eine lokale Vorschau.
- Gespeicherte Bildanhänge werden als Thumbnail-Galerie dargestellt, ohne den Dateinamen in den Vordergrund zu stellen.
- Das Thumbnail ist eine echte reduzierte 360-px-Variante; beim Öffnen wird eine bis 1600 px grosse Vorschau geladen. Erst «Originalbild anzeigen» lädt die Originaldatei.
- Nicht-Bild-Dateien bleiben als Dateiname mit passendem Symbol sichtbar.

## Chronik

- Datumgenaue Einträge ohne bekannte Uhrzeit bleiben innerhalb eines Tages zuerst gruppiert.
- Zeitgenaue Einträge werden danach konsequent neu nach alt sortiert.
- Behandlungseinträge zeigen im zugeklappten Zustand die tatsächlich ausgeführten Bestandteile als Liste und zusätzlich die Behandlungsnotiz.
- Separat dokumentierte Medikamentengaben desselben Tiers mit exakt identischem Zeitpunkt werden automatisch als eine «Medikamentengabe» zusammengefasst.
- Datumgenaue Medikamentengaben ohne Uhrzeit werden nicht automatisch zusammengefasst.
- Bestandteile eines Behandlungsplans bleiben ausschliesslich ihrem Behandlungsplan zugeordnet.

## Behandlungspläne

- Jede Ausführung besitzt eine stabile `treatment_execution_id` und eine eindeutige Parent-/Kind-Struktur.
- Doppelte historische Kind-Einträge aus der bisherigen Ausführungslogik werden nur dann automatisch ausgeblendet, wenn sie nachweislich über die Anzahl der im Snapshot erwarteten Bestandteile hinausgehen; die Bereinigung bleibt auditierbar.
- Löschen einer Ausführung entfernt Parent und alle dazugehörigen Kind-/Korrektureinträge gemeinsam aus der normalen Chronik.
- Die Ausführung kann nachträglich um Produkte oder Handlungsschritte ergänzt werden. Solche Elemente werden als «Zusatz» markiert und ändern die Behandlungsplan-Vorlage nicht.
- Bestandteile einer Vorlage können als optional markiert werden. Beim Ausführen werden optionale Bestandteile gezielt ausgewählt; nur ausgewählte Bestandteile werden dokumentiert.
- Wiederholtes Ausführen ist gegen Doppelklicks und wiederholte Requests abgesichert und erzeugt genau eine Ausführung.

## Eintragsarten und Symptome

- «Kontrolle» ist als zusätzliche Eintragsart verfügbar.
- Vordefinierte und eigene Eintragsarten werden gemeinsam in den Einstellungen verwaltet.
- Vordefinierte Einträge können lokal umbenannt oder ausgeblendet werden; die Originaldefinition bleibt erhalten und kann wiederhergestellt werden.
- Eigene Eintragsarten können direkt aus einer unbekannten Freitexteingabe gespeichert werden.
- Dieselbe Stammdatenlogik wird für Symptome verwendet: vordefinierte und eigene Symptome sind gemeinsam sichtbar, anpassbar und ausblendbar.

## Swissmedic und Produktdaten

- Die Schweizer Medikamentenquelle bleibt der offizielle Swissmedic-OGD-Datensatz `ZL172@swissmedic`.
- Der Import arbeitet auf Sequenzebene, damit unterschiedliche Stärken und Varianten derselben Zulassung einzeln auswählbar bleiben.
- Applikationsarten pro Sequenz werden eingelesen. Ist genau ein eindeutiger Applikationsweg vorhanden, wird er bei der Erfassung vorausgewählt.
- Wirkstoffe, Konzentration, Darreichungsform, Ziel-Tierarten und – soweit aus den strukturierten Daten ableitbar – quantitative Wirkstoffangaben werden im Produkt-Snapshot gespeichert.
- Bei maschinenlesbarer Konzentration zeigt die Chronik zusätzlich die berechnete Wirkstoffmenge einer Gabe an.
- Die offizielle Swissmedic-Datenbank kann in den Einstellungen geöffnet und durchsucht werden. Produkte können lokal ausgeblendet oder mit einem rücksetzbaren Override angepasst werden; die offizielle Quelldefinition selbst wird nicht verändert.
- Die Importlogik verwirft Produkte nicht mehr allein anhand des Felds `ABLAUFDATUM`; der explizite Zulassungsstatus ist für die Auswahl aktueller Präparate massgeblich.
- Für Installationen ohne erfolgreichen aktuellen Swissmedic-Abgleich enthält der Fallback zusätzlich Metacam 15 mg/ml für Pferde.

## Android

Die eigenständige Android-Alpha bleibt unverändert bei `0.9.0-alpha.7` (`versionCode=900007`).
