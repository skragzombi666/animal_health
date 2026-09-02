# Animal Health 0.9.34

Version 0.9.34 führt die Smartphone-Rückmeldungen aus 0.9.33 über gemeinsame Daten- und UI-Pfade zusammen. Die Fehler werden nicht separat pro Ansicht überdeckt, sondern an den zugrunde liegenden Komponenten behoben.

## Produktdatenbanken

- Home Assistant verwendet weiterhin die serverseitige Produktdatenbank-API aus 0.9.28.
- Das gemeinsam genutzte Frontend besitzt zusätzlich einen vollständigen lokalen `v0928`-Adapter für die eigenständige Android-WebView. Mitgelieferte Medikamente, Impfstoffe, Ergänzungen und Futtermittel werden aus den App-Assets geladen; eigene Datenbanken, Importe, lokale Änderungen, Ausblendungen und Löschungen werden lokal gespeichert.
- Technische Meldungen wie `Unknown command` werden nicht mehr unverändert angezeigt. Bei einem Versionskonflikt erscheint eine verständliche Kompatibilitätsmeldung.

## Smartphone-Zurücknavigation

- Für die interne Navigation besteht nur noch ein maßgeblicher Browser-History-Pfad.
- Jede tatsächliche Änderung von Seite, Detailansicht, Einstellungsbereich oder Dialog erzeugt genau einen History-Eintrag.
- Ein Zurück-Befehl verbraucht genau einen Eintrag und stellt den vorherigen Animal-Health-Zustand wieder her.
- Schnell wiederholte Zurück-Befehle werden gesperrt, bis die aktuelle History-Transition abgeschlossen ist.
- Das direkte Anlegen eines Tiers aus einem Formular kehrt ohne zusätzlichen leeren History-Schritt in das Ursprungsformular zurück.

## Chronik

- Medikamentengaben verwenden in Startseite, Tieransicht, Gesamtchronik und aufgeklappten Behandlungsplänen denselben responsiven Inline-Textfluss.
- Mengenangabe, Produktname, Aufgabenherkunft und Sekundärangaben brechen nur bei tatsächlichem Platzmangel um.
- Die nachträgliche Breitenmessung und der künstliche Blockumbruch nach der Menge entfallen.
- Das Symbol «Aus Aufgabe» belegt regulären Layoutplatz und kann keinen Text mehr überlagern.

## Behandlungspläne aus Aufgaben

- Beim Erledigen einer Behandlungsplan-Aufgabe werden Plan-ID, Planname, Beschreibung und die vollständige Komponenten-Momentaufnahme am übergeordneten Chronikeintrag gespeichert.
- Die untergeordneten Medikamenten-, Ergänzungs-, Futter- und Handlungseinträge werden derselben Ausführung und Aufgabenherkunft zugeordnet.
- Bereits vorhandene unvollständige Einträge werden beim Upgrade repariert, soweit die historischen Aufgaben- oder Plandaten noch vorhanden sind.
- Spätere Änderungen am Stammdaten-Behandlungsplan verändern die gespeicherte historische Momentaufnahme nicht.

## Einheitliche Mehrfachauswahl

- Mehrfachauswahlen verwenden eine gemeinsame Komponente: ausgewählte Werte als entfernbare Chips, darunter ein kompaktes Dropdown und rechts die Plus-Aktion.
- Dies gilt insbesondere für Tierziele und bisherige Checkbox-Mehrfachauswahlen in Aufgaben- und Ausführungsformularen.
- Ein Tier kann direkt aus der Auswahl neu angelegt werden. Danach wird das Ursprungsformular mit seinen Eingaben wiederhergestellt und das neue Tier ausgewählt.

## Abgeschlossene Aufgaben

- Aufgaben werden mit der vollständigen Zahl offener und erledigter Vorkommen sowie dem letzten Erledigungszeitpunkt angereichert.
- Abgeschlossene Einmal-Aufgaben bleiben in einem eigenen Abschnitt der Aufgabenverwaltung sichtbar.
- Sie können dupliziert oder als neue Aufgabe erneut geplant werden. «Fortsetzen / erneut planen» setzt eine abgeschlossene Einmal-Aufgabe standardmäßig als tägliche neue Aufgabe auf.
- Die ursprüngliche Aufgabe und ihre Chronikeinträge bleiben unverändert.

## Versionsstand

- Home-Assistant-/HACS-Version: **0.9.34**
- Android bleibt gemäß bestehender Freigabestrategie bei **0.9.0-alpha.7**; der gemeinsame Frontend-Bundle-Test berücksichtigt den zusätzlichen 0.9.34-Frontendteil.
