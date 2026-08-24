# Animal Health 0.9.20

## Offizieller Schweizer Tierarzneimittelkatalog

Die bisherige kleine, manuell kuratierte Starterliste ist nicht mehr die primäre Medikamentendatenbank. Animal Health verwendet für die Schweiz neu den offiziellen Swissmedic-OGD-Datensatz `ZL172@swissmedic` («Daten von Human- und Tierarzneimitteln»).

- Aus dem Swissmedic-Datensatz werden ausschliesslich Datensätze mit `VERWENDUNG = TAM` als Tierarzneimittel übernommen.
- Der offizielle Datenbestand wird lokal in der Animal-Health-Datenbank gespiegelt, damit die Auswahl nach erfolgreicher Synchronisation auch ohne permanente Internetverbindung funktioniert.
- Beim Start der Integration und anschliessend regelmässig wird geprüft, ob der lokale Spiegel aktualisiert werden muss. Zusätzlich kann in den Einstellungen eine manuelle Aktualisierung ausgelöst werden.
- In den Einstellungen werden Quelle, Datensatz-ID, Datenstand, Anzahl Produkte sowie der Synchronisationsstatus angezeigt.
- Ein bestehender vollständiger Spiegel bleibt bei einem vorübergehenden Netzwerk-/Swissmedic-Fehler erhalten.
- Auf einer neuen Installation ohne erfolgreichen Erstabgleich bleibt als Notfall-Fallback der bisherige lokale Katalog verfügbar; dieser Zustand wird ausdrücklich als unvollständig angezeigt. Eradia ist zusätzlich im Fallback enthalten.

Swissmedic ist in 0.9.20 die einzige aktivierte offizielle Quelle. Die interne Quellenstruktur ist bereits so aufgebaut, dass später weitere Länder-/Datenquellen oder benutzerdefinierte Kataloge ergänzt werden können, ohne die Produkt- und Favoritenlogik neu zu entwerfen.

Die Katalogdaten dienen ausschliesslich der Produktidentifikation und Dokumentation. Animal Health leitet daraus keine Dosierungs- oder Therapieentscheidung ab.

## Favoriten

Offizielle Swissmedic-Produkte, selbst angelegte Produkte und aktive Behandlungspläne mit Anzeigeziel «Medikament» bzw. «Medikament und Aufgabe» können gemeinsam als Favoriten verwaltet werden.

- Favoriten werden dauerhaft gespeichert.
- Ihre Reihenfolge kann manuell angepasst werden.
- Favorisierte Produkte werden in der Produktauswahl vor allen nicht favorisierten Produkten angezeigt.
- Favorisierte Behandlungspläne werden analog vor den übrigen passenden Behandlungsplänen angezeigt.
- Die Favoritenverwaltung befindet sich in den Einstellungen.

## Behandlungspläne in der Chronik

Die Ausführung eines Behandlungsplans wird nicht mehr als flache Folge aus Behandlungsplan und mehreren scheinbar unabhängigen Medikamenteneinträgen dargestellt.

- Standardmässig ist nur der Behandlungsplan als übergeordneter Chronikeintrag sichtbar.
- Der Eintrag kann auf- und zugeklappt werden.
- Beim Aufklappen werden die bei dieser Ausführung erzeugten Produkt-/Medikamenteneinträge eingerückt unterhalb des Behandlungsplans dargestellt.
- Die Unterelemente bleiben eigenständige strukturierte Chronikdatensätze und können weiterhin einzeln geöffnet werden.

## Historische Produktdaten

Bei neu dokumentierten Gaben aus dem offiziellen Katalog werden Swissmedic-Quelle, Zulassungsnummer und die zum Zeitpunkt der Dokumentation bekannten Produktangaben im historischen Snapshot gespeichert. Spätere Katalogaktualisierungen verändern bereits dokumentierte Einträge nicht rückwirkend.

## Android

Die eigenständige Android-Alpha bleibt weiterhin auf `0.9.0-alpha.7` eingefroren. Version 0.9.20 betrifft die Home-Assistant-Integration.
