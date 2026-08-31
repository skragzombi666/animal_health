# Animal Health 0.9.28

## Produktdatenbanken statt fest eingebauter Einzellisten

- Neue zentrale Verwaltung **Produktdatenbanken**.
- Mehrere Datenbanken desselben Produkttyps können gleichzeitig aktiv sein.
- Jede Datenbank zeigt Quelle, Typ, Version beziehungsweise Datenstand, Produktzahl, Aktivstatus, Priorität sowie lokale Anpassungen.
- Mitgelieferte und offizielle Quellen bleiben unverändert; Bearbeiten oder Ausblenden erzeugt einen lokalen, rücksetzbaren Override.
- Eigene kuratierte Datenbanken können angelegt, vollständig bearbeitet, als JSON exportiert und wieder importiert werden.
- Produktvorschläge werden aus allen aktiven Datenbanken zusammengeführt. Herkunft und mehrere Quellen bleiben nachvollziehbar; Dubletten werden über einen kanonischen Produktschlüssel gruppiert.
- Entwurmungsmittel sind eine gefilterte Klassifikation beziehungsweise Ansicht der Arzneimitteldaten und kein inkompatibler separater Produkttyp.

## Mitgelieferte Datenbanken

- **Swissmedic – Tierarzneimittel** als offizielle Arzneimittelquelle.
- **Swissmedic – Entwurmungsmittel** als gefilterte Ansicht.
- **Animal Health – Impfstoffe Schweiz** auf Grundlage des vorhandenen kuratierten Impfstoffkatalogs.
- **Animal Health – Ergänzungspräparate** mit mehrteiligen Wirkstoff- und Komponentenmodellen.
- **Animal Health – Futtermittel Geflügel** mit UFA 505 und UFA 506 einschließlich analytischer Bestandteile und Fütterungshinweisen.
- Ergänzend sind UFA Gallo-Fit und UFA-Antifex als erste Geflügel-Ergänzungspräparate enthalten.

## Produkttypabhängige Fachmodelle

### Medikamente

- Wirkstoffe, Konzentration, Darreichungsform und Applikationsweg.
- Mehrere Wirkstoffe können strukturiert erfasst werden.

### Impfstoffe

- Ziele beziehungsweise Antigene, Produktform, Applikationsweg und Impfschema.

### Ergänzungspräparate

- Kein einzelnes universelles Feld „Wirkstoff“ mehr.
- Beliebig viele aktive und funktionelle Bestandteile mit Kategorie, Menge, Einheit, Bezugsbasis, Form beziehungsweise Stamm und Funktion.
- Separate Zusammensetzung, analytische Bestandteile, Zusatzstoffe und Dosierungsempfehlung.

### Futtermittel

- Keine Medikamentenfelder wie Wirkstoff, Wirkstoffkonzentration oder Antigene.
- Futtermittelart, Futterform, Verwendungszweck, Zusammensetzung, analytische Bestandteile, Zusatzstoffe und Fütterungsempfehlung.
- Strukturierte Richtmengen und Fütterungsart.

## Einstellungen neu geordnet

- **Tiere & Stammdaten**: Tiergruppen und tierbezogene Stammdaten.
- **Medikamente & Behandlungen**: Produktdatenbanken, Off-Label-Verhalten und Behandlungspläne.
- **Erfassung & Vorschläge**: Symptome und lokale Vorschlagslogik.
- **Dokumente & Daten**: Anhänge, Export und Datensicherung.
- **Test & Gefahrenbereich**: Verlaufs-/Aufgaben-Reset und vollständiger Animal-Health-Reset.
- Leere Einstellungsbereiche werden nicht mehr angezeigt.
- Export- und Reset-Funktionen werden nicht mehr unter „Tiere & Stammdaten“ beziehungsweise zwischen Medikamenten dargestellt.

## Erfassung und Chronik

- Das redundante blaue Plus in „Schnell erfassen“ wird entfernt.
- Die tatsächlich verabreichte Menge beziehungsweise Dosis wird in kompakten Chronikeinträgen semibold dargestellt, ohne Badge oder Signalfarbe.
- Direkte Medikamentengaben verwenden ebenfalls den zentralen Produktdatensatz und speichern die Produktquelle im Snapshot.

## Migration und Kompatibilität

- Vorhandene manuell angelegte Medikamente werden einmalig in **Meine Produktdatenbank** übernommen.
- Bestehende Impfstoff-, Ergänzungs- und Futtermittel-Datensätze bleiben erhalten und werden einer passenden Datenbank zugeordnet.
- Vorhandene lokale Swissmedic-Overrides bleiben erhalten.
- Android bleibt unverändert auf `0.9.0-alpha.7`; dieses Release betrifft die Home-Assistant-Integration und ihr Frontend.
