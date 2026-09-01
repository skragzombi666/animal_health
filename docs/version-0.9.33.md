# Animal Health 0.9.33

## Chronik: Dosis nur einmal und ohne unnötigen Umbruch

- Medikamenten- und andere Gabe-Einträge enthalten die Mengenangabe nur noch einmal.
- In der tierübergreifenden Chronik bleibt der Tiername als erste Orientierung sichtbar.
- Passt der Produktname in eine Zeile, steht die Dosis platzsparend in der oberen Metazeile neben dem Tiernamen.
- Muss der Produktname ohnehin umbrechen, wird dieselbe Dosis vor den Produktnamen verschoben. Es wird kein zweites Dosis-Element erzeugt.
- In der Tierchronik gilt dieselbe adaptive Logik ohne redundanten Tiernamen.
- Das Symbol «Aus Aufgabe» und die nachfolgenden Metadaten bleiben kompakt in einer gemeinsamen Zeile.

## Smartphone-Zurücktaste innerhalb von Animal Health

- Interne Ansichten werden nun als eigene Browser-History-Einträge geführt.
- Die Zurücktaste des Smartphones führt aus Unteransichten zur zuletzt geöffneten Animal-Health-Ansicht zurück.
- Dies gilt insbesondere für Tierdetail, Tiergruppenübersicht, Tiergruppendetail, Chronik, Aufgaben, Einstellungen und deren Unterseiten.
- Auch vorwärts gerichtete Browsernavigation kann die gespeicherte interne Ansicht wiederherstellen.
- Geöffnete Pop-ups werden beim Zurücknavigieren zuerst geschlossen, bevor eine übergeordnete Ansicht verlassen wird.
- Erst auf der Animal-Health-Startseite führt die Zurücktaste wieder aus der Integration heraus zum zuvor geöffneten Home-Assistant-Dashboard.
- Der bestehende Home-Assistant-History-State bleibt erhalten und wird nur um den internen Animal-Health-Zustand ergänzt.

## Release

- Home-Assistant/HACS-Version: **0.9.33**
- Android bleibt unverändert bei **0.9.0-alpha.7**
