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

## Development status

This project is under active development and is not yet ready for production use.
