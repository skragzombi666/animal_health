# Animal Health brand assets

The canonical full-resolution Animal Health logo is `custom_components/animal_health/brand/icon.png`. It is the single source to replace when the project branding changes and is kept at full quality for documentation, release artwork and other branding cases that need it.

The repository contains only technically necessary delivery copies/derivatives:

- `/icon.png` mirrors the canonical master because repository/HACS branding needs a root-level icon.
- `custom_components/animal_health/frontend/animal-health-brand.svg` is the lightweight runtime derivative used by the Animal Health panel header and loading state. It embeds a small PNG representation so the app does not fetch the roughly 1.3 MB master just to draw a small logo.

Do not edit the runtime derivative independently. After replacing the canonical master, run:

```bash
python scripts/update_brand_assets.py
```

The script regenerates the lightweight runtime asset and synchronizes the root HACS/repository icon. The frontend uses a version/hash-qualified URL, so a changed logo is fetched without requiring users to clear the Home Assistant app cache.
