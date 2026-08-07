# Animal Health 0.7.2

## Scope

Version 0.7.2 is a bugfix release based on testing of 0.7.1. New functional concepts remain scheduled for 0.8.0.

## Fixed

- JSON, backup and per-animal PDF exports now download through an explicit browser download instead of navigating away from the Animal Health panel.
- Symptom catalogue values are translated in the German interface.
- Weight stepper values are rounded deterministically; values such as `2.5100000000000002` are no longer shown.
- The mobile header shows only the paw icon while retaining “Animal Health” on wider screens.
- Creating a task from an animal detail view preselects the current animal.
- Creating an animal while a group is selected carries the group and its species into the form.
- Completed one-off tasks no longer retain an irrelevant activate/deactivate control in the task-definition list.
- Animal-group species is a required controlled selection in the graphical interface.
- Group species remains visible, can be edited and controls the group icon.

## Compatibility

- Existing group species values remain readable. Saving an edited group converts recognised legacy names to the canonical species catalogue identifier.
- No database migration is required.

## Validation

CI validates:

- Python and assembled JavaScript syntax;
- German symptom localisation;
- controlled group species selection and species icons;
- group and species preselection during animal creation;
- current-animal preselection during task creation;
- deterministic weight-step rounding;
- removal of the toggle for completed one-off tasks;
- browser-download handling for JSON, ZIP and PDF exports.
