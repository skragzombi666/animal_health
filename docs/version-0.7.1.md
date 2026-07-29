# Animal Health 0.7.1

## Navigation and interface

- Restores a Home Assistant menu button in the mobile dashboard header.
- Replaces the unavailable `mdi:paw-plus` icon with `mdi:plus-circle-outline` in the Home Assistant action UI and the Animal Health dashboard.
- Adds direct animal switching in the animal detail view, with pages of up to ten animals and group selection.

## Animal groups

- Adds neutral **animal groups** alongside the full animal population and individual animals.
- Supports multiple groups of the same species and animals without a group.
- Adds group creation, editing, assignment during animal creation or editing, group overview cards and group filters.

The existing `animals` table remains unchanged. Group definitions and assignments are stored in the local `animal_groups` and `animal_group_memberships` tables.

## Fast weight recording

- Prefills the latest recorded weight and unit for the selected animal.
- Adds plus and minus controls for quick adjustments.
- Adds the field hint **“Leave empty for now”** to optional occurrence-time fields.

A prefilled value is only recorded after the form is explicitly saved.

## Local attachments

- Supports document selection and direct camera capture on mobile devices.
- Attachments can be linked to an animal or directly to a health event.
- Files are limited to 15 MB each and are stored locally under:
  `.storage/animal_health/attachments`
- Attachment metadata and relationships are stored in the local SQLite database.
- Downloads use short-lived, single-use tokens instead of exposing a permanent Home Assistant access token.

No cloud storage provider is used in 0.7.1.

## Export and portability

- Portable JSON export containing every Animal Health database table.
- Consistent ZIP backup containing:
  - an SQLite online backup;
  - the portable JSON export;
  - every locally stored original attachment.
- Per-animal PDF health timeline containing master data, group, chronologically ordered health events, medically relevant structured event data and document references. Internal task workflow details are excluded.

## Validation

CI validates Python syntax, frontend JavaScript syntax and event delegation, the 0.7.1 dashboard features, portable JSON export, PDF generation and complete ZIP backup contents.
