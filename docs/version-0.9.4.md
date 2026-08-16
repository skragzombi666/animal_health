# Animal Health 0.9.4

0.9.4 korrigiert die in 0.9.3 noch sichtbare Seitenüberschrift und globale Suche auf der Startseite.

## Startseite

- Die Überschrift «Übersicht» wird jetzt direkt über die gemeinsame `heading()`-Funktion für die Startseite unterdrückt.
- Damit entfällt auch die daran gekoppelte globale Suchleiste zuverlässig.
- Die Tiersuche im Bereich «Tiere» bleibt unverändert verfügbar.
- Die Änderung ersetzt die in 0.9.3 verwendete nachträgliche HTML-Ersetzung, die nicht alle tatsächlich gerenderten Varianten erfasst hat.

## Release

- 0.9.4 ist ein regulärer Home-Assistant/HACS-Release ohne Android-Build.
- Die Android-App bleibt vorerst auf 0.9.0-alpha.7 eingefroren.
