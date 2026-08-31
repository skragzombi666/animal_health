# Animal Health 0.9.27

## Schwerpunkt

0.9.27 vereinheitlicht die Dokumentation von verabreichten bzw. angebotenen Produkten unter dem fachlichen Grundmodell **Gabe** und verdichtet gleichzeitig Tieransicht, Chronik und Einstellungen.

## Gabe-Modell

- Gemeinsame semantische Arten: Medikament, Impfung, Entwurmung, Ergänzung und Futter.
- Planung und Durchführung bleiben getrennt: Aufgaben planen eine Gabe; die Chronik dokumentiert das tatsächlich ausgeführte Ereignis.
- Direkt erfasste und aus Aufgaben entstandene Gaben verwenden dieselbe Chronikstruktur. Die Aufgabenherkunft ist nur zusätzliche, nachvollziehbare Metainformation.
- Impfstoffe werden in einer eigenen Produktdatenbank geführt; die vorhandene Schweizer Impfstoffliste wird als vorgegebene Quelle geladen. Lokale Anpassungen und Ausblendungen bleiben vom Quelldatensatz getrennt und können zurückgesetzt werden.
- Ergänzungs- und Futtermittel erhalten dieselbe Verwaltungs- und Auswahltechnik wie andere Produkte.
- Entwurmungen verwenden die Medikamentenbasis, werden aber als eigener semantischer Gabe- und Planungstyp geführt.
- Ergänzungen unterstützen Dosierungsbezüge pro Tier, pro kg Körpergewicht, pro Liter Trinkwasser und pro kg Futter.
- Bei Futter kann zwischen angeboten und tatsächlich aufgenommen unterschieden werden.

## Dosisberechnung

- Verabreichte Wirkstoffmengen werden aus Dosis und strukturierter Konzentration berechnet, sofern die Einheiten sicher zueinander passen.
- Mehrere Wirkstoffe werden getrennt berechnet.
- Die gewichtsbezogene Dosis in mg/kg KG verwendet das letzte dokumentierte Gewicht am oder vor dem Zeitpunkt der Gabe.
- Das verwendete Gewicht wird als Snapshot/Referenz am Ereignis gespeichert, damit spätere Gewichtseinträge historische Berechnungen nicht verändern.
- Unsichere oder nicht konvertierbare Angaben erzeugen keine scheinpräzisen Werte.
- Die Chronik rundet berechnete Werte kompakt auf höchstens drei signifikante Stellen.

## Chronik

- Gabe-Einträge sind responsiv verdichtet: Menge, Produktname, Wirkstoffmenge, mg/kg KG und Applikationsweg nutzen auf breiten Ansichten möglichst eine Zeile.
- Impfung, Entwurmung, Ergänzung und Futter bleiben durch dezente Typkennzeichnung eindeutig erkennbar.
- Aus Aufgaben entstandene Einträge erhalten nur einen kleinen Herkunftshinweis; die medizinische Grunddarstellung bleibt identisch zu direkt erfassten Einträgen.
- In der Detailansicht werden Aufgabenursprung, Aufgabentitel, Planung und Erledigungszeitpunkt nachvollziehbar angezeigt.

## Aufgaben und Behandlungspläne

- Neue Aufgabenarten: Entwurmung, Ergänzung und Futter.
- Impfaufgaben verwenden die Impfstoffdatenbank; die bisherige manuelle Zielkrankheiten-Auswahl bleibt als Fallback verfügbar.
- Optionale Bestandteile eines Behandlungsplans können zusätzlich als standardmässig ausgewählt oder nicht ausgewählt definiert werden.
- Die Datenbankmigration erweitert bestehende Installationen sicher um die neuen Aufgabenarten.

## Benutzeroberfläche

- Das zusätzliche Plus-Badge in der Schnell-Erfassung wird vollständig entfernt.
- In der Tier-Schnellwahl gibt es vor den Tieren einen direkten Einstieg in die Übersicht der aktuell ausgewählten Tiergruppe.
- Die Tierauswahl in der Zielkomponente erhält analog zur Gruppenauswahl eine sichtbare Feldbeschriftung.
- Aktionsmenüs von Behandlungsplänen werden als echte Overlay-Ebene dargestellt und nicht mehr von darunterliegenden Karten überlagert.
- Einstellungen erhalten eine zweistufige Struktur mit den Bereichen Allgemein, Tiere & Stammdaten, Medikamente & Behandlungen, Aufgaben & Planung, KI & Erfassung, Dokumente & Daten, System & Integration sowie Test & Gefahrenbereich.

## Datenquellen

- Swissmedic-Tierarzneimittel verwenden alle zuverlässig verfügbaren strukturierten Metadaten wie Wirkstoffdetails, Konzentration, Darreichungsform, Tierarten, Routen und Zulassungsangaben.
- Fehlende Darstellungen von Konzentration oder Standardroute werden aus vorhandenen strukturierten Metadaten abgeleitet, wenn dies eindeutig möglich ist.
- Amtliche Quelldaten bleiben unverändert; lokale Änderungen werden als rücksetzbare Overrides gespeichert.

## Android

Die Android-App bleibt weiterhin auf `0.9.0-alpha.7` eingefroren. 0.9.27 betrifft die Home-Assistant-Integration und deren Frontend.
