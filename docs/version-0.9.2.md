# Animal Health 0.9.2

0.9.2 verdichtet und vereinheitlicht die Tierübersicht auf der Startseite.

## Tierübersicht

- Tiere ohne Tiergruppe werden weiterhin zuerst angezeigt, jedoch ohne sichtbare Überschrift «Ohne Tiergruppe» oder separate Gruppenzeile.
- Tierkacheln verwenden einen festen Bildbereich. Wenn kein Tierbild vorhanden ist, wird das Tierart-Symbol innerhalb dieses Bereichs zentriert angezeigt.
- Dadurch stehen die Tiernamen bei Kacheln mit und ohne Bild auf derselben Höhe.
- Die Überschrift «Tiere» verwendet dieselbe visuelle Hierarchie wie «Schnell erfassen» und «Heute relevant».
- Gruppen- und Tagfilter sind nur noch als kompakte Symbole dargestellt und befinden sich zusammen mit der Suche rechts neben der Überschrift «Tiere».
- Aktive Filter werden bereits an den Symbolschaltflächen hervorgehoben.
- In der geöffneten Filterauswahl wird der aktuell ausgewählte Eintrag deutlich mit Primärfarbe, stärkerer Kontur und Häkchen markiert.

## Heute relevant

- Die redundante kleine Zeile «Heute» oberhalb von «Heute relevant» entfällt in der Tagesansicht. Der gewählte Zeitraum bleibt rechts im Zeitraumfeld sichtbar.

## Release

- 0.9.2 ist ein regulärer Home-Assistant/HACS-Release ohne Android-Build.
- Die Android-App bleibt vorerst auf 0.9.0-alpha.7 eingefroren.
- Der Release-Workflow markiert neue Home-Assistant-Releases explizit als neuesten GitHub-Release.
