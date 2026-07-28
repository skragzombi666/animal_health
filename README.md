# Animal Health

Animal Health is a custom Home Assistant integration for local animal health records, recurring care tasks and immutable event history.

## Repository structure

The integration lives in `custom_components/animal_health` and is prepared for later installation through HACS.

## Current foundation

- Single-instance config flow
- Local SQLite database
- Versioned schema migrations
- Animals, events, tasks and task occurrences
- Foreign-key enforcement and indexes
- Create, update, archive and restore actions for animal profiles
- Separate factual animal status and administrative archival
- One Home Assistant device for each animal
- Separate profile sensors for status, animal ID, species, breed, color/markings, sex, birth date and arrival date
- Immutable health and care logbook with linked correction entries
- Category-specific forms for weight, symptoms, medication and vaccination
- Automatic logbook entries for factual status changes

## Development deployment on Home Assistant OS

For development, clone this repository to `/config/animal_health`. The scripts in `scripts/` deploy only the integration directory to `/config/custom_components/animal_health`.

First-time setup:

```bash
cd /config/animal_health
chmod +x scripts/*.sh
./scripts/deploy.sh
```

Update to the newest commit on the current branch and deploy:

```bash
cd /config/animal_health
./scripts/update.sh
```

Rollback to the commit recorded before the last update:

```bash
cd /config/animal_health
./scripts/rollback.sh
```

The deployment script creates a backup of an existing installation under `/config/animal_health_backups`, runs `ha core check`, and restarts Home Assistant only after a successful configuration check.

## Animal management

Animal profiles are currently managed through Home Assistant actions. A dedicated user interface is planned for a later development phase.

Create an animal:

```yaml
action: animal_health.create_animal
data:
  name: Ada
  species: Chicken
  breed: Sussex
  color: Brown and white
  sex: female
  arrival_date: "2026-07-01"
```

The action returns the animal's single canonical ID, for example `AH-7K3M9QX`. This same ID is the database primary key, the stable Animal Health device identifier and the reference used by events and tasks. Home Assistant additionally maintains its own registry IDs internally, but those are not Animal Health identifiers and are not exposed to the user.

Each animal is registered as a Home Assistant device with separate sensors for:

- status
- animal ID
- species
- breed
- color or markings
- sex
- birth date
- arrival date

The update, status, archive and restore actions use a filtered Home Assistant device selector. In the user interface, the animal is selected by its device name instead of entering an ID manually.

Example YAML for updating an animal:

```yaml
action: animal_health.update_animal
data:
  device_id: REPLACE_WITH_HOME_ASSISTANT_DEVICE_ID
  color: Black with white markings
```

Factual status and administrative archival are separate. A sold, missing or deceased animal can remain visible until the user decides to archive it. Archiving never changes the factual status or event history.

## Health and care logbook

### General events

The general action is intended for entries where free text is appropriate:

- observation
- diagnosis
- treatment
- veterinary visit
- care
- other

```yaml
action: animal_health.create_event
data:
  device_id: REPLACE_WITH_HOME_ASSISTANT_DEVICE_ID
  event_type: observation
  title: General condition normal
  notes: Eating and behaving normally
```

### Structured weight entry

Weight requires a value greater than zero. The unit is selected from milligram, gram or kilogram and defaults to kilogram.

```yaml
action: animal_health.record_weight
data:
  device_id: REPLACE_WITH_HOME_ASSISTANT_DEVICE_ID
  weight: 2.15
  weight_unit: kg
  notes: Before morning feeding
```

### Structured symptom entry

Symptoms use a typeable suggestion list and a required severity level. A custom symptom can be entered when it is not in the suggestion list.

```yaml
action: animal_health.record_symptom
data:
  device_id: REPLACE_WITH_HOME_ASSISTANT_DEVICE_ID
  symptom: reduced_appetite
  severity: moderate
  notes: Eating less since this morning
```

### Structured medication entry

Medication name, dose and dose unit are required. The medication field is a typeable dropdown with starter suggestions and also accepts a custom product name.

```yaml
action: animal_health.record_medication
data:
  device_id: REPLACE_WITH_HOME_ASSISTANT_DEVICE_ID
  medication_name: Flubenol
  dose: 20
  dose_unit: mg
  route: oral
  notes: Administered with feed
```

### Structured vaccination entry

Vaccinations record the product, dose, unit and optional route and batch number.

```yaml
action: animal_health.record_vaccination
data:
  device_id: REPLACE_WITH_HOME_ASSISTANT_DEVICE_ID
  vaccine_name: Newcastle disease
  dose: 0.5
  dose_unit: ml
  route: subcutaneous
  batch_number: LOT-1234
```

### Corrections and retrieval

Events are append-only. Existing entries are not edited or deleted. Every event action accepts an optional `correction_of_event_id` referencing the entry corrected by the new event.

Retrieve the newest events for an animal:

```yaml
action: animal_health.list_events
data:
  device_id: REPLACE_WITH_HOME_ASSISTANT_DEVICE_ID
  limit: 50
response_variable: animal_events
```

Changing an animal's factual status automatically creates a `status_change` event. Administrative archive and restore actions do not create health-history events.

The current Home Assistant action description is static. Typeable selectors can offer fixed suggestions and accept custom values, but they cannot yet learn medication names from the local event history or dynamically change breed suggestions based on the selected species. These features are planned for the dedicated Animal Health user interface.

## Planned development phases

The roadmap is provisional. Version numbers and scope may change as the integration develops.

### ✅ 0.2.x — Project foundation

- Home Assistant and HACS-compatible repository structure
- Versioned SQLite schema and migrations
- Core data models for animals, events, tasks and task occurrences
- Automated validation and initial schema tests

### ✅ 0.3.x — Animal management

- Create, edit, archive and restore animals
- Extended animal profile data such as species, breed, color/markings, sex, birth date and arrival date
- Stable identifiers and Home Assistant device registration for each animal
- Separate factual status and administrative archival

### ✅ 0.4.x — Health and care logbook

- Immutable event history for observations, treatments, medication, weight and other health-related records
- Category-specific forms with validated values, units and option lists
- Corrections through new linked events instead of overwriting historical records
- Filtering and retrieval of an animal's history
- Automatic status-change events

### ✅ 0.5.x — Tasks and recurrences

- One-time, daily, weekly and monthly care tasks
- Optional start and end dates
- Task occurrences separated from the task definition
- Completion, skipping and overdue state handling
- Conversion of completed care actions into immutable logbook events

### ✅ 0.6.x — Home Assistant entities and services

- Entities for relevant animal status and upcoming care
- Services or actions for creating records and completing tasks
- Events for automations and notifications
- Consistent device and entity naming

### 0.7.x — User interface

- Home Assistant frontend panels or dashboard cards for animal profiles
- Dynamic data-entry forms and known-value suggestions from local history
- Species and breed catalogues with dependent breed suggestions
- Task overview and completion workflow
- Timeline and health-history views
- Mobile-friendly data entry

### 0.8.x — Data portability and administration

- Backup and restore guidance
- Export of animal, event and task data
- Controlled import and validation
- Database diagnostics and migration safeguards
- ? care logbook pdf export
- ? AI assistance to fill logbook by scanning medicine and vet bills / reports

### 0.9.x — Beta and hardening

- Broader automated test coverage
- Performance and long-term database testing
- Translation and accessibility review
- Upgrade testing and migration verification
- Documentation for beta installations

### 1.0.0 — Stable release

- Stable database and service interfaces
- Supported installation and upgrade path
- Documented backup, restore and recovery procedures
- Production-ready release for regular personal and noncommercial organizational use

## Contributing

Noncommercial use, modification and collaboration are welcome. Contributions should be submitted through issues or pull requests and must remain distributable under the project's license.

## License

Animal Health is licensed under the **PolyForm Noncommercial License 1.0.0**. The software may be used, studied, modified and redistributed for permitted noncommercial purposes. Selling the software, incorporating it into a commercial product or service, or otherwise using it for commercial gain is not permitted without a separate written commercial license from the copyright holder.

This is a source-available noncommercial license, not an OSI-approved open-source license. See [LICENSE](LICENSE) for the complete terms.

## Development status

This project is under active development and is not yet ready for production use.
