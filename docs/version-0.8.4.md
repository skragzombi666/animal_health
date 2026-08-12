# Animal Health 0.8.4

0.8.4 ist eine Konsolidierungs- und Administrationsversion. Sie räumt bereits umgesetzte Issues auf, ergänzt lokale Vorschläge und nicht destruktive Diagnostik und bereitet den normalen Updateweg über HACS/Home Assistant vor.

## Lokale Vorschläge aus der eigenen Historie

Animal Health berücksichtigt zusätzlich zu den statischen Katalogen Werte, die bereits lokal dokumentiert wurden.

- Medikamente und Impfstoffe aus vorhandenen Einzel- und Gruppenereignissen bzw. Aufgaben werden priorisiert vorgeschlagen.
- Behandler/Praxen und geeignete Freitextwerte wie Pflegeaktion, Besuchsgrund oder Kontrollschwerpunkt werden als lokale Vorschläge angeboten.
- Soweit ein Eintrag einer Tierart zugeordnet werden kann, bleibt diese Information erhalten und wird bei der Medikamentenauswahl berücksichtigt.
- Freie Eingaben bleiben möglich.
- Die Vorschlagslogik arbeitet ausschliesslich auf der lokalen Animal-Health-Datenbank und trifft keine medizinische Entscheidung.

## Datenbankdiagnose

Administratoren können unter `Einstellungen` eine nicht destruktive Diagnose ausführen.

Geprüft werden:

- SQLite `integrity_check`,
- `foreign_key_check`,
- Datenbankschema-Version,
- erwartete Tabellen und Indizes,
- in der Datenbank referenzierte, aber lokal fehlende Anhangsdateien,
- lokal vorhandene, aber nicht mehr referenzierte Anhangsdateien.

Die Diagnose verändert oder repariert keine Daten automatisch.

## Updates über HACS und Home Assistant

Animal Health erhält keinen eigenen Selbst-Updater, der seine Integrationsdateien während des Betriebs überschreibt.

Stattdessen wird HACS als Update-Transport verwendet:

- das Repository wird als HACS-Integration und zusätzlich mit `hassfest` validiert,
- eine bestehende Installation kann als HACS Custom Repository verwaltet werden,
- eine Aufnahme in die HACS-Standardliste ist für diesen Weg nicht erforderlich,
- HACS stellt für das Repository eine normale Home-Assistant-Update-Entität bereit,
- in Animal Health `Einstellungen` führt ein Shortcut zur Home-Assistant-Updateansicht,
- reguläre Versionen sollen versioniert veröffentlicht werden; `main` bleibt ein bewusster Entwicklungsweg.

Details: `docs/installation-hacs.md`.

## CI- und Migrationstests

Die bisherige Platzhalterprüfung der Datenbank wurde durch Tests gegen die tatsächliche `AnimalHealthDatabase` und die Task-Record-Schemamigration ersetzt.

Geprüft werden nun unter anderem:

- vollständiger `pytest`-Lauf,
- Neuinitialisierung einer leeren Datenbank,
- repräsentative Upgrades von Schema v1 und v2 auf v3,
- Erhalt bestehender Tier-, Aufgaben-, Vorkommnis- und Ereignisdaten,
- erwartete Tabellen, Spalten, Indizes und Trigger,
- `PRAGMA user_version`, `integrity_check` und `foreign_key_check`,
- Backfill der Task-Record-Konfigurationen und Vorkommnispläne.

Die bestehenden fokussierten Smoke-Tests bleiben zusätzlich aktiv.

## KI-Evaluation

Die bereits vorhandenen Datenschutz-/Provider-Hinweise werden durch reproduzierbare Evaluationsfälle ergänzt. `docs/ai-evaluation-cases.md` definiert unter anderem Medikamentenetikett, Verordnung, Rechnung, Bericht, handschriftliche Gewichtsliste, mehrdeutige Tiernamen, widersprüchliche Quellen und deutschsprachiges STT.

## Issue-Bereinigung

Als bereits in 0.8.1–0.8.3 umgesetzt wurden geschlossen:

- #44 STT-Sprache,
- #45 Gewichtskorrektur,
- #46 Tiergruppen ohne Einzeltiere,
- #47 fokussierte operative Startseite,
- #48 spontane Medikamenten-/Supplementgabe.

Zusätzlich werden mit 0.8.4 abgeschlossen:

- #22 CI-/Migrations-Hardening,
- #35 lokale Vorschläge aus Tier-/Chronikhistorie,
- #38 Datenbankdiagnose,
- #41 README-/Roadmap-Neuordnung,
- #42 Provider-/Datenschutzhinweise und KI-Evaluationsfälle,
- #53 HACS-/Home-Assistant-Updateweg.

## Bewusst offen

Nicht in 0.8.4 vermischt werden grössere oder risikoreichere Themen:

- #36 kontrollierter Import,
- #37 geführter Restore-/Recovery-Workflow,
- #40 optionaler mobiler Gewichtspicker nach echter UX-Evaluation,
- #43 vollständige Restore-/Upgrade-Pfade für 0.9.x.

#23 bleibt als technischer Refactor zur direkten Integration der Stabilisierung in `TaskStore` offen. Praxistest-Issues bleiben offen, bis die jeweiligen Abläufe auf der realen Home-Assistant-Testinstallation tatsächlich geprüft wurden.
