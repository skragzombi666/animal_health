# Animal Health 0.9.0-alpha.6

0.9.0-alpha.6 korrigiert die noch sichtbaren Darstellungsprobleme der Standalone-Android-App.

## Statusleiste und Display-Cutout

- Die Android-Shell reserviert zusätzlich auf Web-Ebene einen sicheren oberen Bereich für Statusleiste und Display-Cutout.
- `safe-area-inset-*` wird verwendet; zusätzlich besteht ein Mindestabstand von 32 CSS-Pixeln nach oben als Fallback für Android-WebViews, die den Cutout-Inset nicht korrekt an CSS weiterreichen.
- Damit sollen Logo, Navigation und Bedienelemente nicht mehr unter Uhrzeit, Kameraloch oder Notch liegen.

## Mobile Navigation und Icons

- Die Standalone-App erhält Android-spezifische mobile Header-Regeln, ohne die Home-Assistant-Darstellung zu verändern.
- Menü, fünf Hauptnavigationseinträge und Aktualisieren werden auf kleinen Displays explizit sichtbar gehalten und gleichmässig verteilt.
- `ha-icon` und die enthaltenen SVGs erhalten explizite Abmessungen und Sichtbarkeit.
- Das Suchsymbol in kompakten Überschriften wird ebenfalls explizit sichtbar gehalten.
- Die Regeln werden nach jedem Rendern des gemeinsamen Frontends automatisch erneut in dessen Shadow DOM eingesetzt.

## Weiterhin

- gemeinsame Oberfläche für Home Assistant und Android,
- stabiles Alpha-Signing seit alpha.4,
- lokales Standalone-Backend und lokale Datenhaltung.
