# Animal Health 0.8.9

0.8.9 behebt den wiederkehrenden Frontend-/Backend-Versions-Mismatch nach Updates in der Home-Assistant-App.

- Das bereits registrierte Custom Element `animal-health-panel` wird beim Laden einer neuen Frontend-Version nun in-place mit den aktuellen Basismethoden aktualisiert. Dadurch landen auch alle nachfolgenden Frontend-Patches auf der tatsächlich von Home Assistant verwendeten Klasse.
- Der JavaScript-Endpunkt und die gebündelten Brand-Assets werden mit `no-store, no-cache, must-revalidate, max-age=0` ausgeliefert. Die bereits vorhandene versions- und hashbasierte Modul-URL bleibt zusätzlich bestehen.
- Erkennt Animal Health künftig dennoch einen Frontend-/Backend-Versionsunterschied, wird genau einmal automatisch ein cache-bustender Vollreload ausgelöst. Ein Session-Guard verhindert Reload-Schleifen.
- Regressionstests simulieren ausdrücklich ein Update innerhalb derselben bereits laufenden Browser-/WebView-Sitzung.

Nach dem HACS-Update und dem erforderlichen Home-Assistant-Neustart sollte das manuelle Löschen des Android-App-Caches nicht mehr nötig sein.

Behoben: #65.
