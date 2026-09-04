# Animal Health

Animal Health ist eine benutzerdefinierte Home-Assistant-Integration für lokale Tierstammdaten, Gesundheits-/Pflegechronik, wiederkehrende Aufgaben, Tiergruppen und dokumentationsunterstützende KI-Erfassung.

## Aktueller Stand

Die aktuelle Version ist **0.9.42**. Sie ist ein Konsolidierungs-Checkpoint: Die Übersicht, die Tierliste und die Tier-Grundansicht verwenden bereits die neue modulare Architektur; alle übrigen Bereiche und sämtliche Schreibvorgänge bleiben während der kontrollierten Migration funktional über den bestehenden Legacy-Pfad erhalten.

Der Funktionsumfang umfasst unter anderem:

- Tiere mit Stammdaten, Bild, Tags und optionaler Tiergruppe
- Tiergruppen als eigener fachlicher Bezug, auch ohne erfasste Einzeltiere
- unveränderliche Chronik mit verknüpften Korrektureinträgen
- Gewicht, Symptome, Medikation, Supplemente, Impfungen, Pflege, Kontrollen und Tierarztbesuche
- einmalige und wiederkehrende Aufgaben mit Ausführungsprotokoll
- Gruppenaufgaben und Gruppenchronik
- Bild-/Dokumentanhänge mit komprimierten Vorschauen und unverändertem Original
- JSON-/Backup-Export und PDF-Chroniken
- operative, mobile Startseite mit Schnellaktionen
- KI-Erfassung über Home Assistants `ai_task` und Speech-to-Text; ausschliesslich als zu prüfende Vorbefüllung ohne autonome medizinische Entscheidung

Animal Health befindet sich weiterhin in aktiver Entwicklung und ist noch keine stabile 1.0-Version.

## Installation und Updates

### HACS

Der bevorzugte Installations- und Updateweg ist HACS. Das Repository kann bereits als **HACS Custom Repository** vom Typ **Integration** verwendet werden; eine Aufnahme in die HACS-Standardliste ist dafür nicht erforderlich.

Nach der HACS-Installation stellt HACS für Animal Health eine normale Home-Assistant-Update-Entität bereit. Updates können damit über **Einstellungen > Updates** installiert werden, ohne Terminal-Deploy.

Eine bestehende manuelle Installation kann auf HACS-Verwaltung umgestellt werden. Die detaillierten Schritte und Hinweise zu `main` als Entwicklungsversion stehen in [docs/installation-hacs.md](docs/installation-hacs.md).

### Entwicklung über Terminal

Für Entwicklung kann das Repository weiterhin nach `/config/animal_health` geklont und mit den Skripten unter `scripts/` nach `/config/custom_components/animal_health` ausgerollt werden.

```bash
cd /config/animal_health
chmod +x scripts/*.sh
./scripts/deploy.sh
```

Aktualisieren und ausrollen:

```bash
cd /config/animal_health
./scripts/update.sh
```

Rollback auf den vor dem letzten Update gesicherten Commit:

```bash
cd /config/animal_health
./scripts/rollback.sh
```

Der Entwicklungs-Deploy erstellt vor dem Austausch eine Sicherung, führt `ha core check` aus und startet Home Assistant nur nach erfolgreicher Konfigurationsprüfung neu.

## Datenhaltung und Audit Trail

Animal Health speichert seine Nutzdaten lokal in SQLite. Ereignisse werden nicht nachträglich überschrieben. Korrekturen erzeugen neue verknüpfte Einträge. Tierbilder und Dokumentanhänge werden lokal im Animal-Health-Speicherbereich abgelegt.

Der unter **Einstellungen** vorhandene Test-Reset löscht Animal-Health-Nutzdaten vollständig und ist nicht Teil eines normalen Updates oder einer HACS-Umstellung.

## KI-Erfassung

Animal Health verwendet Home Assistants Provider-Abstraktionen. Je nach konfigurierter `ai_task`- bzw. Speech-to-Text-Entität kann die Verarbeitung lokal oder extern erfolgen.

Die KI darf nur explizit vorhandene Informationen extrahieren und Formulare vorbefüllen. Sie darf keine Diagnose stellen, Therapie empfehlen, Dosis berechnen oder fehlende medizinische Tatsachen ergänzen. Speicherung erfolgt erst nach Prüfung und ausdrücklicher Benutzeraktion.

Reproduzierbare Prüffälle und Provider-/Datenschutzhinweise stehen in [docs/ai-evaluation-cases.md](docs/ai-evaluation-cases.md).

## Entwicklungsplan

Der Plan wird am tatsächlichen Implementierungsstand ausgerichtet; bereits vorgezogene Funktionen bleiben nicht künstlich in alten Phasen stehen.

### Erledigt bis 0.8.3

- Projektgrundlage, SQLite-Schema und Migrationen
- Tierverwaltung und Home-Assistant-Geräte/Entitäten
- unveränderliche Gesundheits-/Pflegechronik
- strukturierte Erfassungen und Korrekturen
- Aufgaben und Wiederholungen
- Tiergruppen, Tags und Gruppenchronik
- mobile operative Oberfläche
- spontane Medikamenten-/Supplementgabe
- Bild-/Dokumentanhänge und Vorschauen
- JSON-/Backup-Export und PDF-Ausgaben
- KI-MVP inklusive Text, Diktat, Foto/PDF und Mehrfacherfassung
- Provider-/STT-Konfiguration ausserhalb des normalen Erfassungsdialogs

### 0.8.4 — Konsolidierung und Distribution

Schwerpunkte:

- offene, bereits implementierte Issues bereinigen und schliessen
- HACS-/Home-Assistant-Updateweg validieren und dokumentieren
- lokale Vorschläge stärker aus vorhandener Tier-/Chronikhistorie ableiten
- nicht destruktive Datenbankdiagnose bereitstellen
- technische Test-/Migrationsabdeckung weiter härten, soweit ohne unnötigen Umbau sinnvoll

### Spätere 0.8.x

- kontrollierter JSON-/Backup-Import mit vollständiger Validierung, Vorschau und atomarem Rollback
- geführter Restore-/Recovery-Workflow mit vorgelagerter Sicherung
- weitere Praxisevaluation der KI mit realen Providern und Dokumenten
- optionaler mobiler Gewichtspicker nur bei nachgewiesenem UX-Vorteil

### 0.9.x — Beta und Hardening

- vollständige Upgrade-/Restore-Tests über repräsentative ältere Datenstände
- Performance- und Langzeittests
- Übersetzungs-, Accessibility- und Mobile-Hardening
- stabiler Installations-, Update- und Recovery-Pfad
- Bereinigung verbleibender technischer Kompatibilitäts-Shims

### 1.0.0 — Stable

- stabile Datenbank- und Service-Schnittstellen
- dokumentierter und getesteter Installations-/Updatepfad
- dokumentierter und getesteter Backup-/Restore-/Recovery-Prozess
- definierte Kompatibilitäts- und Migrationsgarantien
- produktionsreife Dokumentation für den vorgesehenen nichtkommerziellen Einsatz

## Repository-Struktur

Die Integration liegt unter `custom_components/animal_health`. Das Repository enthält zusätzlich Versionsdokumentation, Tests, Entwicklungs-Deploy-Skripte und HACS-Metadaten.

## Lizenz

Animal Health steht unter der **PolyForm Noncommercial License 1.0.0**. Nutzung, Untersuchung, Änderung und Weitergabe sind im Rahmen der nichtkommerziellen Lizenzbedingungen zulässig. Für kommerzielle Nutzung ist eine separate schriftliche Lizenz erforderlich.

Die Lizenz ist source-available und nicht OSI-approved. Massgeblich ist die Datei [LICENSE](LICENSE).
