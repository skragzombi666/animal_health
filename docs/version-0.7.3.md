# Animal Health 0.7.3

## Ziel

0.7.3 ist eine Stabilitäts- und Bedienversion auf Basis der Tests von 0.7.2. Sie behebt vor allem Probleme bei Tiergruppen, Dokumenten, Exporten und der Tierdarstellung.

## Änderungen

### Tierdarstellung und Icons

- Im Panel-Kopf wird ein gebündeltes Animal-Health-Markenzeichen statt der generischen Pfote angezeigt.
- Tierkarten, Tierwechsler und Tierdetail verwenden tierartspezifische Symbole.
- Hühner werden ausdrücklich als Huhn dargestellt und nicht mehr mit dem generischen Vogel-Icon.
- Hunde verwenden weiterhin das spezifische Hundesymbol, soweit verfügbar.

### Tiergruppen

- Die Tierart einer Tiergruppe ist optional. Damit sind gemischte Tiergruppen zulässig.
- Eine festgelegte Tierart kann beim Anlegen eines Tiers weiterhin vorausgefüllt werden.
- Tiergruppen können archiviert, wiederhergestellt und gelöscht werden.
- Sind beim Archivieren oder Löschen noch Tiere zugeordnet, muss zuvor gewählt werden:
  1. Tiere aus der Gruppe entfernen,
  2. Tiere in eine bestehende Gruppe verschieben,
  3. eine neue Gruppe anlegen und die Tiere dorthin verschieben.
- Tier-, Gewichts-, Aufgaben-, Chronik- und Dokumentdaten werden dabei nicht gelöscht.
- Archivierte Tiergruppen werden separat dargestellt und können wiederhergestellt werden.

### Tierformular

- Geschlecht wird als direkte Drei-Fach-Auswahl statt als Dropdown dargestellt.
- Farben werden anhand von Tierart und – soweit vorhanden – Rasse vorgeschlagen.
- Farbvorschläge sind nicht verbindlich; freie Farbangaben bleiben jederzeit möglich.
- Rassenvorschläge werden nach Tierart gefiltert.
- Bei einem Validierungsfehler bleibt das ausgefüllte Tierformular erhalten.
- Die technische Fehlermeldung bei einer unpassenden Rasse-/Tierart-Kombination wird benutzerverständlich lokalisiert.

### Dokumente und Bilder

- Nach Auswahl eines Dokuments wird im Formular unmittelbar angezeigt, welche Datei ausgewählt wurde.
- «Dokument fotografieren» versucht zuerst, die Kamera direkt über den Browser-/WebView-Kamerazugriff zu öffnen und bietet eine integrierte Aufnahmeansicht. Falls der direkte Kamerazugriff nicht verfügbar ist, wird auf die Systemauswahl zurückgefallen.
- Bildanhänge erhalten in der Tieransicht eine direkte Thumbnail-Vorschau.
- Bilder können aus der Tieransicht in einer grösseren Vorschau geöffnet werden.
- Dateidownloads verwenden wieder den vom Backend bereitgestellten Download mit Content-Disposition statt eines vollständig im JavaScript aufgebauten Blob-Downloads.

### Export und Datensicherung

- JSON-, Backup-, PDF- und Anhang-Downloads starten über eine signierte Download-URL direkt im Browser, ohne die Animal-Health-Ansicht zu verlassen.
- Der Benutzer erhält sofort eine Rückmeldung, dass der Download gestartet wird.
- Dadurch wartet das Frontend nicht mehr mehrere Minuten auf die vollständige Datei, bevor überhaupt eine sichtbare Reaktion erfolgt.
- Das vollständige Backup enthält weiterhin SQLite-Datenbank, portablen JSON-Export und lokal gespeicherte Anhänge.

### Chronik

- Der interne Titel `weight_measurement` wird in der Oberfläche als «Gewichtserfassung» lokalisiert.

## Datenbank

Für archivierte Tiergruppen wird die ergänzende Tabelle `animal_group_lifecycle` automatisch angelegt. Bestehende Installationen und Tiergruppen bleiben kompatibel; bestehende Gruppen gelten zunächst als aktiv.

## Update

Nach dem Merge auf `main`:

```sh
cd /config/animal_health
./scripts/update.sh
```

Das Deploy-Skript sichert die bisher installierte Integration, kopiert die neue Version nach `/config/custom_components/animal_health`, führt `ha core check` aus und startet Home Assistant Core neu.
