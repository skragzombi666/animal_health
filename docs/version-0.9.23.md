# Animal Health 0.9.23

## Datum ohne Uhrzeit

- Manuelle Gewichtserfassungen, allgemeine Chronikeinträge, Produkt-/Medikamentengaben, Behandlungspläne und Symptome können mit einem Datum ohne bekannte Uhrzeit dokumentiert werden.
- Die zeitliche Präzision wird explizit als `date` oder `datetime` gespeichert.
- Datumgenaue Einträge erhalten intern einen neutralen Speicheranker, dieser wird aber niemals als tatsächliche Uhrzeit dargestellt.
- Damit wird bei Nachdokumentationen keine künstliche oder vermeintlich exakte `00:00` mehr erzeugt.

## Symptom-Episoden

- Neu erfasste Symptome starten eine persistente Symptom-Episode.
- Eine Episode bleibt aktiv, bis sie ausdrücklich beendet wird.
- Eine erneute Erfassung desselben bereits aktiven Symptoms wird als Verlaufsbeurteilung derselben Episode dokumentiert.
- Schweregrad und Notizen können im Verlauf neu beurteilt werden.
- Beim Beenden wird das Ende der Episode dokumentiert; ein späteres erneutes Auftreten startet eine neue Episode.
- Im Tierdetail zeigt `Aktuelle Symptome` alle derzeit aktiven Symptome mit Startdatum, Dauer und aktuellem Schweregrad.
- Aktive Symptome können dort direkt neu beurteilt oder beendet werden.
- Historische Symptomereignisse aus älteren Versionen werden bewusst nicht automatisch zu aktiven Episoden migriert.

## Chronik

- Tagesüberschriften bleiben prominent; für das aktuelle Datum wird `Heute · <Datum>` angezeigt.
- Innerhalb eines Tages stehen zuerst alle Einträge ohne bekannte Uhrzeit.
- Danach folgen Einträge mit Uhrzeit chronologisch von früh nach spät.
- Die Zeilen sind als Zeitachse aufgebaut: `Uhrzeit → Symbol → Inhalt`.
- Bei datumgenauen Einträgen bleibt die Zeitspalte leer.
- Das redundante Präfix `Symptome:` wurde aus Symptomzeilen entfernt.
- Symptom-Episoden werden als zusammenfassender Chronikeintrag dargestellt; aufgeklappt werden Beginn, Verlaufsbeurteilungen und Abschluss gezeigt.
- Die vorhandene Gruppierung von Behandlungsplänen und gemeinsamen Medikamentengaben bleibt erhalten und wird in die neue Zeitachsen-Darstellung eingebettet.

## Android

Die eigenständige Android-Alpha bleibt unverändert bei `0.9.0-alpha.7` (`versionCode=900007`).
