# Animal Health 0.8.14

0.8.14 vereinheitlicht das Animal-Health-Branding und reduziert die in der Oberfläche geladene Bildgrösse. Die KI-Erfassungslogik bleibt unverändert.

## Logo und Branding

- Das gewünschte runde Animal-Health-Logo mit Huhn, Hund und Schaf bleibt unter `custom_components/animal_health/brand/icon.png` als hochauflösende kanonische Quelle erhalten.
- Das Root-`icon.png` bleibt die technisch notwendige Kopie für Repository/HACS-Branding.
- Header und Ladezustand verwenden `custom_components/animal_health/frontend/animal-health-brand.svg`, eine kleine Runtime-Ableitung desselben Logos statt der grossen Master-Datei.
- Beide bisherigen Brand-URLs bleiben kompatibel und liefern die kleine Runtime-Variante.
- Der Brand-Endpoint verwendet eine versions- und hashbasierte URL mit langfristigem Immutable-Caching.
- `scripts/update_brand_assets.py` regeneriert die Runtime-Ableitung aus der Master-Datei und synchronisiert das Root-Icon. Damit muss ein späterer Logowechsel nur an der kanonischen Quelle vorgenommen werden.
- Frontend und Manifest werden auf 0.8.14 angehoben.

Die funktionierende KI-Mehrfacherfassung und insbesondere die ursprüngliche 0.8.3-Single-Pass-Gewichtserkennung wurden nicht verändert.

Behoben: #69.
