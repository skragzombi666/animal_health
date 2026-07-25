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

## Planned development phases

The roadmap is provisional. Version numbers and scope may change as the integration develops.

### 0.2.x — Project foundation

- Home Assistant and HACS-compatible repository structure
- Versioned SQLite schema and migrations
- Core data models for animals, events, tasks and task occurrences
- Automated validation and initial schema tests

### 0.3.x — Animal management

- Create, edit, archive and restore animals
- Extended animal profile data such as species, breed, sex, birth date and arrival date
- Stable identifiers and Home Assistant device registration for each animal
- Import of existing animal records where practical

### 0.4.x — Health and care logbook

- Immutable event history for observations, treatments, medication, weight and other health-related records
- Structured event categories with optional notes and measurements
- Corrections through new linked events instead of overwriting historical records
- Filtering and retrieval of an animal's history

### 0.5.x — Tasks and recurrences

- One-time, daily, weekly and monthly care tasks
- Optional start and end dates
- Task occurrences separated from the task definition
- Completion, skipping and overdue state handling
- Conversion of completed care actions into immutable logbook events

### 0.6.x — Home Assistant entities and services

- Entities for relevant animal status and upcoming care
- Services or actions for creating records and completing tasks
- Events for automations and notifications
- Consistent device and entity naming

### 0.7.x — User interface

- Home Assistant frontend panels or dashboard cards for animal profiles
- Task overview and completion workflow
- Timeline and health-history views
- Mobile-friendly data entry

### 0.8.x — Data portability and administration

- Backup and restore guidance
- Export of animal, event and task data
- Controlled import and validation
- Database diagnostics and migration safeguards

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
