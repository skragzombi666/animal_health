# Static catalogues

Animal Health 0.4.2 ships versioned, read-only catalogues for structured data entry.

## Included catalogues

- common animal species
- common dog, cat, chicken and rabbit breeds
- a curated Swiss veterinary medicine starter catalogue
- a curated Swiss veterinary vaccine starter catalogue

The catalogue files are stored under `custom_components/animal_health/catalogs`. Every item has a stable catalogue ID. Species and breed selections are normalised to their canonical display names. A catalogued breed is validated against a catalogued species.

Home Assistant action forms cannot dynamically filter the breed selector based on the species selected earlier in the same form. Breed options therefore contain a species prefix such as `Huhn — Sussex`. The prefix is used only for selection; the stored breed is `Sussex`.

## Custom values

All catalogues retain a custom-value fallback. This is intended for unusual species, unlisted breeds, magistral preparations, imported products or newly authorised products. Medication and vaccine events record whether the selected product came from the catalogue or was entered as a custom value.

## Swiss veterinary products

The Swiss product catalogues are curated starter catalogues based on Swissmedic's authorised veterinary medicinal product lists and official product information. Their catalogue version is tied to the source date. They are not exhaustive and are not updated dynamically.

The catalogues are for documentation only. They do not recommend a diagnosis, medicine, dose, route, vaccine or vaccination schedule. The current authorisation, official product information and veterinary instructions must be checked independently.

## Sources

- Swissmedic lists of authorised veterinary medicinal products
- Swissmedic official veterinary product information
- Fédération Cynologique Internationale breed nomenclature
- Fédération Internationale Féline recognised breeds
- Swiss small-animal and poultry breed references
- Swiss Federal Food Safety and Veterinary Office animal categories

Future releases can add separately versioned country catalogues, including EU/EEA product catalogues, without changing existing event records.
