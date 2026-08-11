# Animal Health 0.8.0

0.8.0 ist die erste Beta-Basis nach Abschluss des 0.7.x-Praxistests. Der Schwerpunkt liegt auf einer belastbaren Tierorganisation, Bildern, einer klareren Aufgaben-/Chroniklogik, mobil schnellerer Bedienung und einem bewusst begrenzten KI-Assistenten zur Dateneingabe.

## Tierorganisation

- Jedes Tier besitzt genau eine primäre Tiergruppe in der Benutzeroberfläche.
- Bestehende Tiere ohne Tiergruppe werden bei der 0.8.0-Initialisierung automatisch der gemischten Gruppe `Unzugeordnet` zugeordnet; bestehende Gruppenzuordnungen bleiben erhalten.
- Beim Archivieren oder Löschen einer Tiergruppe müssen enthaltene Tiere in eine bestehende oder neu anzulegende Tiergruppe verschoben werden.
- Im Tierformular kann direkt `Neue Tiergruppe anlegen …` gewählt werden. Der bisherige Formularstand bleibt erhalten und die neue Gruppe wird danach ausgewählt.
- Zusätzlich stehen frei kombinierbare Tags zur Verfügung. Tags können angelegt, bearbeitet, gelöscht und mehreren Tieren zugeordnet werden; Tiere bleiben trotzdem genau einer primären Tiergruppe zugeordnet.

## Tierbilder

- Pro Tier kann ein Bild hochgeladen, ersetzt oder entfernt werden.
- Das Bild wird lokal im bestehenden Attachment-Speicher von Animal Health abgelegt.
- Tierbilder erscheinen in Tierkarten, Tierdetail, Tierwechsler sowie als kompakte Orientierung in geeigneten Aufgaben-/Chronikzeilen.
- Ohne Tierbild bleibt die tierartspezifische Darstellung der Fallback.

## Dashboard und Filter

- Die vier Kennzahlen auf der Übersicht sind interaktiv.
- `Aktive Tiere` öffnet die Tierliste mit entsprechendem Filter.
- `Überfällig`, `Heute fällig` und `Offene Aufgaben` öffnen die Aufgabenansicht mit passendem Filter.
- Tierliste kann zusätzlich nach Tags gefiltert werden.
- Interaktive Karten und Schaltflächen erhalten sichtbare Hover-, Fokus-, Touch-/Aktiv-Zustände.
- Zentrale Erstellaktionen verwenden konsistent die primäre Aktionsdarstellung.

## Gewicht

- Das zuletzt bekannte Gewicht bleibt beim Erfassen vorausgefüllt.
- Schnelle Korrektur über `−0,10`, `−0,01`, `+0,01` und `+0,10 kg`; direkte Zahleneingabe bleibt möglich.
- Im Detail eines Gewichtseintrags wird analog zur Statusänderung `Letzte Messung → Neue Messung` dargestellt.

## Aufgaben und Chronik

- Wiederkehrende Aufgaben verwenden die Begriffe `Serie pausieren` und `Serie fortsetzen`.
- Pausierte Serien bleiben als Aufgabendefinition sichtbar, erzeugte offene Fälligkeiten bleiben während der Pause aus Fälligkeitsansichten ausgeblendet.
- Gesundheitlich relevante Aufgaben erzeugen beim Ausführen weiterhin zwingend einen verknüpften Chronikeintrag. Dies gilt für Gewicht, Medikament, Impfung, Behandlung, Gesundheitskontrolle, Pflege und Tierarztbesuch.
- `Behandlung` ist als eigene strukturierte Aufgabenart ergänzt.
- Reine tierbezogene Erinnerungen können beim Erledigen optional in den Aktivitätsverlauf übernommen werden. Ohne Auswahl entsteht kein Chronikeintrag.
- Allgemeine Erinnerungen bleiben reine Aufgaben und erzeugen keinen Tierchronikeintrag.
- Die Chronik bietet getrennte Ansichten für `Gesundheitschronik`, `Aktivitätsverlauf` und `Alle Einträge`.

## KI-Dokumentassistent

0.8.0 enthält ein bewusst einfach gehaltenes KI-MVP für die Dateneingabe:

- In der Animal-Health-Oberfläche können bis zu zehn Fotos oder Dateien gemeinsam ausgewählt werden. Unterstützt werden JPEG, PNG, WebP und PDF.
- Mehrere Fotos können nacheinander aufgenommen und gesammelt werden, z. B. Vorderseite, Rückseite und Etikett eines Medikaments oder mehrere Seiten eines Dokuments.
- Die Analyse verwendet Home Assistants `AI Task`-Schnittstelle. Animal Health enthält keinen fest verdrahteten Cloud-Anbieter und keinen eigenen API-Schlüssel.
- Damit kann derselbe Workflow mit einer vom Benutzer gewählten AI-Task-Entität verwendet werden; ob die Verarbeitung lokal oder extern erfolgt, hängt vom in Home Assistant konfigurierten Provider ab.
- Ein zusätzliches Freitextfeld erlaubt Kontext, der auf den Dateien nicht sichtbar ist, z. B. welches Tier gemeint ist oder ergänzende sachliche Angaben.
- Dieses Freitextfeld kann über `Diktieren (KI → Text)` befüllt werden. Dafür verwendet Animal Health eine in Home Assistant konfigurierte Speech-to-Text-Entität; bei Google Gemini erfolgt die Transkription über dessen STT-Entität. Die Aufnahme wird als 16-kHz-Mono-WAV an Home Assistant übergeben und nach der Transkription wieder verworfen.
- Extrahiert werden ausschliesslich Angaben, die in den Dateien sichtbar oder vom Benutzer im Zusatztext ausdrücklich genannt sind, z. B. Dokumentart, Tiername, Medikament/Impfstoff, Dosis und Einheit, Applikationsweg, Praxis/Behandler, Behandlungstext, Terminangaben und Notizen.
- Die KI darf keine Diagnose stellen, keine Dosis berechnen, nichts verschreiben und fehlende medizinische Angaben nicht ergänzen.
- Unsichere, widersprüchliche oder nicht vorhandene Angaben sollen leer bleiben und als Unsicherheit kenntlich gemacht werden.
- Erkannte Angaben werden zunächst nur als Vorschau angezeigt.
- Mit `Aufgabe mit diesen Angaben vorbereiten` werden passende Felder im normalen Aufgabenformular vorausgefüllt. Erst dort kontrolliert der Benutzer alle Angaben und löst den Speichervorgang selbst aus.
- Es gibt keine automatische Speicherung und keine autonome medizinische Entscheidung.
- Temporäre KI-Uploads werden getrennt von der Tierchronik gespeichert und verfallen automatisch; ein Dokument wird nur dann dauerhaft Animal Health zugeordnet, wenn der Benutzer es über die reguläre Dokumentfunktion speichert.

Weitergehende komplexe Dokumentanalyse, robuste Evaluationsfälle und zusätzliche direkte Chronik-Workflows bleiben Folgeausbau.

## Datenmodell und Rückwärtskompatibilität

Zusätzliche 0.8-Tabellen werden idempotent angelegt:

- `animal_tags`
- `animal_tag_memberships`
- `animal_profiles`

Bestehende Tier-, Ereignis-, Aufgaben-, Attachment- und Gruppendaten bleiben unverändert erhalten. Die bisherige Gruppenzuordnung wird als primäre Tiergruppe weiterverwendet. Nur tatsächlich ungruppierte Altdaten werden nach `Unzugeordnet` migriert.

Der KI-Assistent ändert das fachliche Datenmodell nicht. Analyseergebnisse sind temporäre Entwürfe und werden erst über die bestehenden, validierten Animal-Health-Funktionen gespeichert.

## Teststrategie

Die CI prüft zusätzlich zu den bestehenden 0.7.x-Smoke-Tests:

- Migration ungruppierter Bestandsdaten auf eine primäre Tiergruppe,
- Tag-Anlage/-Zuordnung/-Löschung,
- Tierbild-Zuordnung und Entfernung,
- Pflichtauswahl der primären Tiergruppe in der Oberfläche,
- kein `Aus Gruppe entfernen` bei Gruppenarchivierung/-löschung,
- Tierbilder und Tags in Karten/Formularen,
- zweistufigen Gewichts-Stepper,
- `Letzte Messung → Neue Messung`,
- Gesundheitschronik vs. Aktivitätsverlauf,
- klickbare Dashboard-Kennzahlen,
- Serien-Pause/Fortsetzen,
- strukturierte Behandlungsaufgaben,
- KI-Sicherheitsvorgaben, mehrere gemeinsame Dokumente, Zusatzkontext, Speech-to-Text-Diktat, temporären Uploadpfad und Entwurfs-/Bestätigungsworkflow.

## Release-Ablauf

0.8.0 wird vor dem Merge direkt aus dem Release-Branch auf einer realen Home-Assistant-Testinstallation geprüft. Erst nach erfolgreichem Praxistest wird der Branch nach `main` gemergt.
