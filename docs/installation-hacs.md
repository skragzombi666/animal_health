# Installation und Updates über HACS

Animal Health kann bereits als **HACS Custom Repository** verwaltet werden. Eine Aufnahme in die HACS-Standardliste ist dafür nicht erforderlich.

## Bestehende manuelle Installation auf HACS umstellen

Die Animal-Health-Nutzdaten liegen ausserhalb des Integrationscodes in der lokalen Datenbank und im Animal-Health-Speicherbereich. Die HACS-Installation ersetzt nur `custom_components/animal_health`.

1. Vor der Umstellung in Animal Health ein vollständiges Backup exportieren und zusätzlich ein Home-Assistant-Backup erstellen.
2. In HACS unter **Custom repositories** das Repository `skragzombi666/animal_health` als Typ **Integration** hinzufügen.
3. Animal Health in HACS herunterladen. Die vorhandenen Dateien unter `custom_components/animal_health` werden durch die HACS-verwaltete Version ersetzt.
4. Home Assistant neu starten.
5. Prüfen, dass der bestehende Animal-Health-Config-Entry geladen wird und Tiere, Aufgaben, Chronik und Anhänge weiterhin vorhanden sind.

Der bestehende Config Entry und die Animal-Health-Daten werden bei diesem Wechsel nicht absichtlich gelöscht oder zurückgesetzt. Der unter Einstellungen vorhandene **Animal Health zurücksetzen**-Button darf für die Umstellung nicht verwendet werden.

## Normale Updates

Sobald das Repository von HACS verwaltet wird, stellt HACS für Animal Health eine normale Home-Assistant-Update-Entität bereit. Verfügbare Versionen können dadurch über **Einstellungen > Updates** installiert werden; ein Terminal-Deploy ist nicht mehr erforderlich.

Für reguläre Versionen werden versionierte GitHub-Releases/Tags verwendet. Dadurch ist eindeutig nachvollziehbar, welche Version installiert wird.

## Entwicklungsstand `main`

HACS kann über die Home-Assistant-Aktion `update.install` auch einen öffentlichen Branch wie `main` als gewünschte Version installieren. Das ist ein Entwicklungsweg und kann Code enthalten, der noch nicht als Release freigegeben wurde.

Für normale Nutzung bleibt der versionierte Release-Kanal der Standard. `main` soll nur bewusst zum Testen des aktuellen Entwicklungsstands verwendet werden.

## Kein eigener Selbst-Updater

Animal Health überschreibt seine eigenen Dateien nicht während des laufenden Betriebs. Download, Austausch der Integrationsdateien und Update-Entität werden HACS/Home Assistant überlassen. Damit bleiben Update-Status, Fehlerbehandlung und der notwendige Home-Assistant-Neustart im dafür vorgesehenen Update-Mechanismus.
