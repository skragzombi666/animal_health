# Animal Health 0.8.3

0.8.3 bündelt die während des mobilen Tests gesammelten Verbesserungen für Tierstammdaten, Bildbearbeitung, Auswahlfelder, Medikamente und KI-Erfassung.

## Tiergruppen und Stammdaten

- Tiere dürfen weiterhin ohne primäre Tiergruppe geführt werden.
- Beim Löschen einer Tiergruppe mit Mitgliedern steht explizit **„Tiere keiner Tiergruppe zuordnen“** zur Verfügung. Die Tiere bleiben erhalten und werden nur aus der Gruppe gelöst.
- Tiergruppen können optional eine **Rasse** erhalten. Beim Anlegen eines Tiers innerhalb dieser Gruppe wird die Gruppen-Rasse vorausgefüllt und bleibt am Tier änderbar.
- Tiere erhalten das optionale Freitextfeld **„Besondere Merkmale“** für längerfristige Identifikationsmerkmale wie Fell-/Federzeichnungen, Blesse oder fehlende Zehen.
- Besondere Merkmale werden in der Tiersuche berücksichtigt und nicht automatisch als Gesundheitsereignis protokolliert.

## Rasse, Farbe und benutzerdefinierte Werte

- Die bisherigen Browser-Datalists für Rasse und Farbe werden durch ein eigenes, deckendes Combobox-Menü ersetzt, damit Filtern und Auswählen auf Mobilgeräten stabil bleibt.
- Manuell eingegebene Rassen und Farben werden nach dem Speichern dauerhaft als benutzerdefinierte Vorschläge übernommen.
- Benutzerdefinierte Werte werden im Auswahlmenü mit einem kleinen Bearbeiten-Symbol gekennzeichnet.
- Dubletten werden normalisiert nach Gross-/Kleinschreibung und überflüssigen Leerzeichen vermieden.

## Tierbild und Tierseite

- Nach Auswahl eines Tierbilds steht vor dem Speichern ein Zuschneide-Dialog zur Verfügung.
- Der quadratische Ausschnitt kann gezoomt, horizontal/vertikal verschoben und in 90-Grad-Schritten gedreht werden. Alternativ kann das Original verwendet werden.
- Der Tierkopf wurde kompakter aufgebaut: grösseres Bild, grosser Name, Tierart als Symbol und Geschlecht als Symbol direkt am Namen.
- Darunter folgen kompakt Alter, Rasse und Farbe; besondere Merkmale erscheinen unbeschriftet und kursiv.

## Medikamente und Off-Label-Anzeige

- Die Medikamentenauswahl verwendet ebenfalls die neue stabile Combobox.
- Standardmässig werden Katalogeinträge angezeigt, deren hinterlegte Zieltierart zum ausgewählten Tier passt.
- Mit **„Off-Label / andere Tierarten anzeigen“** werden zusätzlich die übrigen Katalogeinträge eingeblendet; diese werden in der Liste als **Off-Label** markiert.
- Die Kennzeichnung ist reine Katalog-/Dokumentationsinformation und keine Therapie- oder Anwendungsempfehlung.
- Manuell eingetragene Medikamente werden künftig erneut angeboten, mit Benutzerdefiniert-Symbol und dem Status **„Zulassungsstatus nicht hinterlegt“**. Animal Health erfindet für eigene Einträge keinen Zulassungsstatus.
- Präparatstärke und verabreichte Menge bleiben getrennt: Ein Präparat kann z. B. eine Stärke pro Tablette im Namen tragen, während die Aufgabe weiterhin `1 Tablette` als Dosis speichert.
- Für Doxycyclin wurden aktuelle Schweizer Doxycare-Katalogeinträge ergänzt; sie werden nur entsprechend der im Katalog hinterlegten Zieltierarten als reguläre Einträge angezeigt.

## KI-Erfassung

- Der Sicherheits-/Provider-Hinweis steht am unteren Ende des KI-Eingabeformulars statt prominent am Anfang.
- Bei einem einzelnen erkannten Datensatz entfällt der frühere Zwischenschritt „Erkannte Angaben“. Die Erfassung führt direkt in den vorbereiteten Gewichts- bzw. Aufgabenentwurf.
- Die ausführlichen Erkennungsinformationen bleiben aufklappbar unter **„Details zur KI-Erkennung“** verfügbar.
- Foto/PDF, Freitext und Diktat können weiterhin einzeln oder kombiniert verwendet werden.

### KI-Mehrfacherfassung

- Eine Eingabe kann mehrere Entwürfe erzeugen, z. B. eine handschriftliche Gewichtsliste mit mehreren Tieren.
- Eindeutig erkannte Tiernamen werden gegen den vorhandenen Tierbestand abgeglichen.
- Ein gemeinsames, eindeutig erkanntes Datum kann auf die betroffenen Einträge übertragen werden.
- Die Prüfansicht zeigt eine Übersicht sowie **„Eintrag x / n“** mit Navigation zwischen den Einträgen.
- Einträge können korrigiert, als geprüft markiert, verworfen, wieder aufgenommen und einzeln gespeichert werden.
- **„Alle geprüften Einträge speichern“** speichert nur Einträge, die die notwendigen Angaben besitzen und nicht verworfen wurden.
- Die KI speichert niemals unmittelbar nach der Analyse.

## Erneuter Fix: KI → Aufgabenformular

Der in 0.8.2 vorgesehene Fix für die Übernahme eines KI-Ergebnisses in eine Aufgabe hat sich im realen Test als unzureichend erwiesen: Die KI konnte Tier, Medikament, Dosis und Wiederholung korrekt erkennen, das anschliessende Aufgabenformular blieb dennoch weitgehend leer.

0.8.3 behandelt dies ausdrücklich erneut:

- der KI-Entwurf bleibt bestehen, bis das Aufgabenformular tatsächlich gerendert wurde;
- die Übernahme wird bei Bedarf mehrmals nach dem Rendern erneut versucht;
- Aufgabenart, Titel, Beschreibung, Wiederholung, Datum/Zeit und erkannte Tierauswahl werden gesetzt;
- bei Medikamenten werden Name, Dosis, Einheit und Applikationsweg gesetzt;
- `1 Tablette` bleibt `1` + `tablet` und wird nicht aus einer Präparatstärke in `mg` umgedeutet;
- der Entwurf wird erst verworfen, nachdem die zentralen Formularwerte verifiziert wurden;
- ein Runtime-Smoke-Test prüft explizit die Übernahme von Tier, Doxycyclin-Präparat, `1 Tablette` und täglicher Wiederholung.

## Sicherheit

Die KI dient ausschliesslich der Datenerfassung und Vorbefüllung. Sie trifft keine medizinischen Entscheidungen, berechnet keine Dosierungen und speichert erkannte Angaben nicht ohne Nutzeraktion.
