# Animal Health 0.9.42

Version 0.9.42 ist ein Konsolidierungs-Checkpoint nach den schnellen Iterationen bis 0.9.41. Sie führt noch keinen neuen fachlichen Schreibpfad ein, sondern schafft eine überprüfbare technische Grundlage für die weitere Entwicklung.

## Konsolidierungs-Checkpoint

- Die bisherige Frontend-Struktur wurde vollständig inventarisiert und als maschinenlesbare Architektur-Baseline abgesichert.
- Die 99 nummerierten JavaScript-Fragmente bleiben als unveränderliche Legacy-Referenz von 0.9.41 erhalten. Neue nummerierte Fragmente sind gesperrt.
- Home Assistant und die eigenständige Android-App verwenden dasselbe reproduzierbar erzeugte Frontend-Bundle.
- Das Bundle beginnt weiterhin bytegenau mit dem eingefrorenen Legacy-Präfix und ergänzt danach genau eine gebündelte modulare Laufzeit.
- Neue Prototyp-Patches, zusätzliche Runtime-Patchregistrierungen und append-basiertes Rendering werden durch CI-Schutzregeln verhindert.

## Neue modulare Grundlage

0.9.42 enthält erstmals die neue fach- und komponentenbasierte Frontend-Struktur:

- Plattformadapter für Home Assistant und Android
- kanonischer API-Client und einheitliche camelCase-DTOs
- zentrale Fehlernormalisierung
- kanonischer Anwendungszustand und Store
- eigener Router mit Navigationsrevision
- explizite Aktionsregistry statt verteilter Ereignis-Patches
- kontrollierter Panel-Lebenszyklus und genau ein modularer Renderpfad
- eine einzige befristete routebasierte Legacy-Brücke

## Bereits modular aktive Routen

Die folgenden drei Lesepfade verwenden die neue Architektur:

- `overview`
- `animals`
- `animal-detail`

Die neue Übersicht und die Tieransichten verwenden ausschließlich normalisierte Daten. Gruppen-, Tag-, Such- und Archivfilter, Tierdetail-Ladevorgänge sowie der Schutz vor verspäteten Antworten sind zentral getestet.

## Weiterhin unverändert über Legacy

Aufgaben, Kalender, Chronik, Einstellungen und alle weiteren noch nicht migrierten Routen bleiben funktional im bisherigen Frontend. Sämtliche schreibenden Aktionen und Dialoge werden weiterhin ausschließlich über die vorhandenen Legacy-Handler ausgeführt. Es existiert kein paralleler Schreibpfad und keine doppelte Persistenz.

Nach einem Legacy-Schreibvorgang wird die aktive modulare Übersicht beziehungsweise Tierdetailansicht vollständig aktualisiert.

## Laufzeit-Härtung

- Rückkehr aus einer Legacy-Route rendert die modulare Route unmittelbar wieder.
- Suchfelder behalten nach vollständigem Neurendern Fokus und Cursorposition.
- DOM-Aktionsfehler werden kontrolliert normalisiert und erzeugen keine unbehandelten Promise-Ablehnungen.
- Ein Refresh der Tierdetailansicht aktualisiert sowohl das Verzeichnis als auch das konkrete Tierdetail.
- Veraltete Ergebnisse und Fehler einer bereits verlassenen Ansicht werden verworfen.

## Daten und Kompatibilität

- Keine Datenbankmigration
- Keine Änderung bestehender Home-Assistant-Services oder WebSocket-Commands
- Keine Änderung gespeicherter IDs oder Nutzdaten
- Keine Änderung der fachlichen Aufgaben- und Serienregeln aus 0.9.41
- Die eigenständige Android-App bleibt auf 0.9.0-alpha.7 und erhält dasselbe gemeinsame Frontend-Artefakt.

## Technische Absicherung

Der Release-Stand wird durch Architektur-Guardrails, reproduzierbare Bundle-Prüfung, modulare JavaScript-Vertragstests, die vollständige Python-Test-Suite, bestehende Smoke- und Regressionstests, Android-APK-Build, HACS Validation und hassfest abgesichert.

Die visuelle und interaktive Abnahme in einer realen Home-Assistant-Instanz und im Android-WebView folgt nach Veröffentlichung dieses Checkpoints.
