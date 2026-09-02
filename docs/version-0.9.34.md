# Animal Health 0.9.34

Version 0.9.34 consolidates the smartphone feedback from 0.9.33 into shared data and UI paths instead of adding isolated view-specific corrections.

## Product databases

The standalone Android frontend now provides the complete `v0928` product-database command set locally. Bundled medicine, vaccine, supplement and feed catalogues are loaded from verified app assets. Personal databases, imports, edits, local overrides, visibility changes and deletions are persisted locally. Home Assistant continues to use the existing server-side database API. Technical errors such as `Unknown command` are replaced by a clear compatibility message.

## Navigation

Internal navigation now has one authoritative browser-history implementation. Each real Animal Health state change creates one history entry; one back action consumes exactly one entry and restores the preceding page, detail view, settings section or modal. Rapid repeated back requests are locked until the current history transition is complete. Nested animal creation returns to the originating form without leaving a duplicate no-op history entry.

## Chronology

Medication administrations use one responsive inline flow for animal, dose, product name, task origin and secondary metadata. Artificial block breaks and post-render width measurement are removed. The task-origin icon occupies normal layout space and cannot overlap text. The same renderer is used on the home page, animal page, complete chronology and inside expanded treatment plans.

Treatment plans completed from tasks are repaired after execution and during upgrade. The parent event stores the treatment-plan snapshot, task source, occurrence reference and execution identity. Existing component events are linked to the same execution and source. The chronology can render snapshot components even when an older event did not persist its child references.

## Multiple selection

Simple multiple-choice fields use one component: selected values as removable chips, a compact dropdown for additional values, and a plus action for direct creation or a custom value. This covers animal targets and checkbox-based multi-selects, including task creation and task editing. Creating an animal from the selector restores the original form and selects the new animal.

## Completed tasks

Task definitions are enriched with persistent pending/completed counts and the last completion time. Completed one-time tasks remain visible outside the limited occurrence window. They can be duplicated or rescheduled as a new task. The completed historical task and its chronology entries remain immutable.
