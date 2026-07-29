# Animal Health dashboard

Version 0.7 adds a code-managed Animal Health application to the Home Assistant sidebar.

## Installation and access

After installing or updating the integration and restarting Home Assistant, the sidebar contains **Animal Health**. No Lovelace YAML, custom card installation or external frontend resource is required.

The panel is bundled with the integration and uses Home Assistant's authenticated WebSocket connection. It has no CDN or internet dependency.

## Views

- **Overview**: active animals, overdue and due-today tasks, upcoming tasks and recent records.
- **Animals**: searchable animal cards with current status, weight and next task.
- **Animal detail**: master data, task history, open occurrences and the animal timeline.
- **Tasks**: overdue, due-today, upcoming and resolved occurrences plus task activation controls.
- **Calendar**: task occurrences grouped by local calendar date.
- **Timeline**: recent health, care and status records across all animals.

## Data entry

The dashboard uses the existing validated Animal Health services for all writes. It never writes directly to SQLite.

Available actions include:

- create and edit animals;
- change, archive and restore animal status;
- record weights, symptoms and general events;
- create structured tasks for reminders, weights, medication, vaccination, health checks, care and veterinary visits;
- execute, skip or cancel individual task occurrences;
- activate or deactivate task definitions.

Task forms are dynamic. Only fields that apply to the selected task kind are enabled and submitted. Existing backend validation remains authoritative.

## Language and layout

The panel follows the Home Assistant language setting for German and English text, uses Home Assistant theme variables, and adapts to mobile, tablet and desktop widths.

## Upgrade notes

Version 0.7 does not change the database schema. Existing animals, events, tasks, occurrence IDs and task-linked records remain valid.

A full Home Assistant restart is recommended after updating so the new panel module and versioned URL are loaded cleanly.
