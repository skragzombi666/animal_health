# Animal Health 0.9.0-alpha.5

0.9.0-alpha.5 behebt drei sichtbare Integrationsfehler der Standalone-Android-App.

## Android-Oberfläche

- Die bisher verwendeten Unicode-/Emoji-Platzhalter für `ha-icon` wurden durch lokal gebündelte SVG-Vektoricons ersetzt.
- Navigation, Schnellaktionen, Gruppen, Einstellungen, Medikamente, Anhänge sowie Tierart-Symbole werden dadurch konsistent und ohne externe Icon-Abhängigkeit dargestellt.
- Unbekannte MDI-Namen werden anhand ihrer Funktion auf ein passendes lokales Symbol abgebildet, statt als Punkt oder falsches Zeichen zu erscheinen.

## Keine Home-Assistant-Warnung in Standalone

- Das Android-Backend verwendet seine Produktversion nun direkt aus `BuildConfig.ANIMAL_HEALTH_VERSION`.
- Der alte fest codierte Backend-Stand `0.9.0-alpha.2` wurde entfernt.
- Die Android-Brücke unterdrückt zusätzlich die Home-Assistant-spezifische Frontend-/Backend-Reload-Warnung und den entsprechenden HA-Reload-Versuch. Diese Logik bleibt in der Home-Assistant-Integration selbst unverändert aktiv.

## Statusleiste, Notch und Navigation

- Der native Android-Container übernimmt die System-Window-Insets für Statusleiste, Display-Cutout/Notch und Navigationsleiste.
- Der WebView erhält entsprechende Innenabstände und liegt damit nicht mehr unter Uhrzeit, Kameraloch/Notch oder Systemnavigation.
- Status- und Navigationsleiste verwenden auf dem hellen App-Hintergrund dunkle System-Symbole.

## Regressionstests

Die Android-Tests prüfen nun ausdrücklich:

- system bar / display cutout insets,
- lokale SVG-Icons ohne Emoji-Platzhalter,
- Unterdrückung HA-spezifischer Warnbanner im Standalone-Modus,
- gemeinsame Versionsquelle zwischen Android-Build und lokalem Backend,
- unveränderte stabile Alpha-Testsignatur für Updates ab alpha.4.
