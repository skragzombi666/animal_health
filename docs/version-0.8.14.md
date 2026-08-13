# Animal Health 0.8.14

0.8.14 vereinheitlicht das Animal-Health-Branding und reduziert die in der Oberfläche geladenen Bildgrössen. Die KI-Erfassungslogik bleibt unverändert.

## Logo und Branding

- Das gewünschte runde Animal-Health-Logo mit Huhn, Hund und Schaf ist die einzige hochauflösende Master-Quelle.
- Die Master-Datei liegt unter `custom_components/animal_health/assets/animal-health-logo-master.png` und bleibt in voller Auflösung für Branding-Sonderfälle erhalten.
- `custom_components/animal_health/brand/icon.png` wird als optimierte 256-px-Variante für Integrations-/Repository-Branding abgeleitet.
- `custom_components/animal_health/brand/icon-ui.png` wird als optimierte 128-px-Variante für Header und Ladezustände der App verwendet.
- Das Root-`icon.png` wird aus derselben 256-px-Variante synchronisiert und ist keine eigenständige Quelle.
- Das alte abweichende `frontend/animal-health-brand.svg` wurde entfernt.
- Der bestehende Brand-Endpoint liefert nur noch die kleine UI-Variante und verwendet einen versions-/hashbasierten URL sowie langfristiges Immutable-Caching.
- `scripts/update_brand_assets.py` erzeugt die abgeleiteten Dateien aus der Master-Datei; CI prüft die Synchronität.

Damit muss bei einem späteren Logowechsel nur die Master-Datei ersetzt und das Asset-Skript ausgeführt werden; die ausgelieferten Varianten werden daraus neu erzeugt.

Behoben: #69.
