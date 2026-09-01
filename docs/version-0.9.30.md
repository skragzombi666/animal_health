# Animal Health 0.9.30

## Produktdatenbanken vollständig sichtbar

- Das Datenbankmanagement stellt die mitgelieferten Datenbanken bei jedem Laden selbstheilend wieder her, falls Metadaten oder Zuordnungen fehlen.
- Ladefehler werden nicht mehr als leere Liste verschluckt, sondern mit verständlicher Fehlermeldung und direkter Wiederholfunktion angezeigt.
- Die Übersicht zeigt die Zahl der registrierten Datenbanken und die insgesamt verwalteten Produkte.
- Alle Produktdatensätze ohne Datenbankzuordnung werden einer sichtbaren Datenbank zugeordnet.

## Vorhandene und vorgeschlagene Produktwerte

- Die bisherige Medikamenten-Grundliste bleibt als eigener offline verfügbarer Schweizer Medikamenten-Starterkatalog erhalten.
- Manuell erfasste Produkte aus älteren Versionen werden fortlaufend in «Meine Produktdatenbank» übernommen, nicht nur einmalig während der ersten Migration.
- Produktnamen aus Chronik, Aufgaben, Gruppenaktionen und Behandlungsdaten werden in der dynamischen Datenbank «Lokale Produktwerte aus Verlauf & Aufgaben» sichtbar.
- Die dynamische Datenbank umfasst Medikamente, Impfstoffe, Entwurmungsmittel, Ergänzungen und Futtermittel. Höher priorisierte offizielle oder kuratierte Einträge bleiben bei Dubletten massgebend.

## Mitgelieferte Grunddaten

- 14 bereits vorhandene Schweizer Impfstoff-Startereinträge sind nun ausdrücklich Bestandteil der Impfstoffdatenbank.
- Der Ergänzungskatalog enthält UFA Gallo-Fit, UFA-Antifex, UFA-Antifex Natur, UFA-Mixgrit, AviPro Avian, Anima-Strath flüssig, Anima-Strath Granulat und Vetark Nutrobal.
- Der UFA-Geflügelfutterkatalog enthält 42 Produkte für Küken, Junghennen, Legehennen, Mastpoulets, Wassergeflügel, Wachteln und Truten.
- UFA 505 und UFA 506 bleiben mit strukturierten Nährwerten und Fütterungshinweisen hinterlegt.

## Datenprinzip

Die Produktdatenbanken dienen der Dokumentation und Auswahl. Produkt-, Zulassungs-, Fütterungs- und Anwendungshinweise sind vor der Verwendung anhand der aktuellen Herstellerdeklaration beziehungsweise Fachinformation zu prüfen.

## Release

- Home-Assistant/HACS-Version: **0.9.30**
- Android bleibt unverändert bei **0.9.0-alpha.7**
