# Animal Health brand assets

The full-resolution Animal Health logo is the canonical source for all project branding.

- `custom_components/animal_health/brand/animal-health-logo-master.png`: canonical full-resolution source. Keep this file for documentation, release artwork and other branding cases that need full quality.
- `custom_components/animal_health/brand/animal-health-logo-ui.png`: generated lightweight 128×128 UI derivative used inside the Home Assistant panel.
- `/icon.png`: generated 256×256 repository/HACS derivative. This duplicate exists only because repository/HACS branding needs a root-level icon.

Do not edit the derived files independently. When the master logo is replaced, regenerate the derivatives from the master and keep the same paths so the frontend does not need separate branding changes.

The in-app header must use the lightweight UI derivative. The full-resolution master must never be fetched merely to render the small header logo.
