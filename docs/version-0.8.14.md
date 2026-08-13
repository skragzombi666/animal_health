# Animal Health 0.8.14

0.8.14 vereinheitlicht das Branding, ohne Änderungen an der KI-Erkennung vorzunehmen.

## Logo

- Das gewünschte Animal-Health-Rundlogo mit Huhn, Hund, Schaf und grünem Gesundheitskreuz bleibt als hochauflösende Master-Datei erhalten.
- Für die Home-Assistant-Oberfläche wird eine kleine 128×128-PNG-Ableitung verwendet, damit der Header nicht die grosse Branding-Datei laden muss.
- Das Root-`icon.png` für Repository/HACS verwendet dieselbe kleine Ableitung.
- Die Master-Datei ist die einzige inhaltlich gepflegte Quelle; Ableitungen sollen nicht unabhängig bearbeitet werden.
- Ein Regenerationsskript erstellt die kleinen Dateien aus dem Master neu.
- Der alte, abweichende SVG-Logo-Entwurf wird nicht mehr als eigenständiges Branding verwendet.

Behoben: #69.
