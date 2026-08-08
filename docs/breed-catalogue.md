# Breed catalogue

## Principle

Animal Health only offers named breeds or recognized breeding types when a suitable official or recognized breeding source exists. Broad zoological categories are not populated with invented "breeds". Every selectable species nevertheless has explicit fallback choices so that the breed field is never unusable.

The catalogue is split into:

- `catalogs/breeds.json`: original catalogue for dog, cat, chicken and rabbit.
- `catalogs/breeds_supplement.json`: additional Swiss-prioritized breed coverage and generic fallbacks.

Breed resolution is species-aware. Identical generic names in several species therefore resolve to the selected species instead of accidentally matching the first catalogue entry.

## Coverage audit 2026-08

| Species | Catalogue status | Primary source / decision |
| --- | --- | --- |
| Dog | Real breeds | Fédération Cynologique Internationale (FCI) |
| Cat | Real breeds | Fédération Internationale Féline (FIFe) |
| Chicken | Real breeds | Rassegeflügel Schweiz / Swiss breed references |
| Duck | Real breeds | Rassegeflügel Schweiz, Ringgrössenverzeichnis |
| Goose | Real breeds | Rassegeflügel Schweiz, Ringgrössenverzeichnis |
| Turkey | Real breeds | Rassegeflügel Schweiz, Ringgrössenverzeichnis |
| Quail | Recognized breeding type | Rassegeflügel Schweiz; Japanische Legewachtel plus fallbacks |
| Pigeon | Real Swiss breeds | Klub für Schweizertaubenrassen; 26 Swiss breeds |
| Guinea fowl | Generic fallbacks | Swiss poultry standard treats Perlhühner as a group rather than a practical separate breed list for this catalogue |
| Rabbit | Real breeds | Swiss small-animal references; supplemented with Schweizer Fehkaninchen |
| Guinea pig | Real breeds / standard types | Vereinigung der Schweizer Meerschweinchenfreunde, Kleines Rassenlexikon |
| Hamster | Generic fallbacks | No suitable standardized breed list; commonly distinguished by species/varieties instead |
| Rat | Generic fallbacks | No suitable standardized breed list for the app's species abstraction |
| Mouse | Generic fallbacks | No suitable standardized breed list for the app's species abstraction |
| Gerbil | Generic fallbacks | No suitable standardized breed list for the app's species abstraction |
| Chinchilla | Generic fallbacks | No suitable standardized breed list for the app's species abstraction |
| Ferret | Generic fallbacks | Coat colours/varieties are not treated as a breed list here |
| Horse | Real breeds / recognized studbook populations | Swiss Federal Office for Agriculture (BLW), recognized breeding organizations |
| Donkey | Real recognized breeds | Deutscher Zuchtverband für Esel e.V.; state-recognized breeding programs for Deutscher Esel and Thüringer Waldesel |
| Cattle | Real breeds | BLW, recognized Swiss breeding organizations |
| Sheep | Real breeds | BLW, recognized Swiss breeding organizations and Swiss breeds |
| Goat | Real breeds | BLW / Schweizerischer Ziegenzuchtverband and recognized breeding organizations |
| Pig | Real breeds / lines | BLW, recognized Swiss breeding organizations and Swiss breeds |
| Alpaca | Recognized types | BLW-recognized breeding organization: Huacaya and Suri |
| Llama | Recognized types | BLW-recognized breeding organization: Wooly and Classic |
| Bee | Recognized subspecies / breeding populations | BLW-recognized organizations: Apis mellifera mellifera and Apis mellifera carnica |
| Fish | Generic fallbacks | `fish` is an umbrella category; species are not represented as breeds |
| Bird | Generic fallbacks | `bird` is an umbrella category; species are not represented as breeds |
| Reptile | Generic fallbacks | Umbrella category; species are not represented as breeds |
| Tortoise / turtle | Generic fallbacks | Species/varieties rather than a standardized breed list |
| Snake | Generic fallbacks | Species/morphs rather than a standardized breed list |
| Lizard | Generic fallbacks | Species/morphs rather than a standardized breed list |
| Amphibian | Generic fallbacks | Species/morphs rather than a standardized breed list |
| Other species | Generic fallbacks | Deliberately unrestricted category |

## Fallback rule

Every species has at least `Andere / nicht aufgeführt`. Species without a meaningful standardized breed list additionally provide an appropriate `Rasse / Zuchtform / Art unbekannt` option. Free breed entry remains possible in the Animal Health UI.

## Main sources

- Bundesamt für Landwirtschaft BLW: Tierzucht, Schweizer Rassen and list of recognized breeding organizations.
- Rassegeflügel Schweiz: Ringgrössenverzeichnis / recognized poultry breeds.
- Klub für Schweizertaubenrassen: Swiss pigeon breeds and standards.
- Vereinigung der Schweizer Meerschweinchenfreunde: Kleines Rassenlexikon.
- Fédération Cynologique Internationale (FCI): dog breed nomenclature.
- Fédération Internationale Féline (FIFe): recognized cat breeds.
- Deutscher Zuchtverband für Esel e.V.: recognized donkey breeding programs.
