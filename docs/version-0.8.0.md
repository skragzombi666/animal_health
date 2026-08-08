# Animal Health 0.8.0

0.8.0 ist die erste Beta-Basis nach Abschluss des 0.7.x-Praxistests. Der Schwerpunkt liegt auf einer belastbaren Tierorganisation, Bildern, einer klareren Aufgaben-/Chroniklogik und einer mobil schnelleren Bedienung.

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

## Datenmodell und Rückwärtskompatibilität

Zusätzliche 0.8-Tabellen werden idempotent angelegt:

- `animal_tags`
- `animal_tag_memberships`
- `animal_profiles`

Bestehende Tier-, Ereignis-, Aufgaben-, Attachment- und Gruppendaten bleiben unverändert erhalten. Die bisherige Gruppenzuordnung wird als primäre Tiergruppe weiterverwendet. Nur tatsächlich ungruppierte Altdaten werden nach `Unzugeordnet` migriert.

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
- strukturierte Behandlungsaufgaben.

## Release-Ablauf

0.8.0 wird vor dem Merge direkt aus dem Release-Branch auf einer realen Home-Assistant-Testinstallation geprüft. Erst nach erfolgreichem Praxistest wird der Branch nach `main` gemergt.
