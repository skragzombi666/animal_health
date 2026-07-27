# Record-linked tasks

Animal Health 0.6.0 links planned care tasks to the records created when the task is actually performed.

## Task kinds

Every structured task has one stable task kind:

- `reminder`
- `weight`
- `medication`
- `vaccination`
- `health_check`
- `care`
- `veterinary_visit`

Each kind has a matching Home Assistant record action. A record-linked task cannot be completed through the generic completion action; it must be completed through its matching record action so that the task occurrence and logbook stay consistent.

## Reminder tasks

A reminder records completion, processing time, timing deviation and notes in task history. It does not create a medical or care logbook event.

General tasks are supported only for reminders. All other task kinds must belong to an animal because they create an animal logbook record.

## Planned and actual values

The task definition stores planned values. Examples include:

- planned medication, dose, unit and route
- planned vaccination target, product, dose and route
- planned health-check focus
- planned care action
- planned veterinary visit reason and provider

Each occurrence receives a snapshot of the applicable plan. Later changes to a recurring task do not change the plan stored for older occurrences.

When an occurrence is recorded, actual values are stored separately. Planned and actual values therefore remain visible even when the performed treatment differs from the plan.

## Timing

The linked event stores:

- scheduled date and time
- actual performance date and time
- `early`, `on_time` or `late`
- timing deviation in minutes
- optional reason for the deviation

Tasks without a due time apply to the whole scheduled date. They are on time throughout that date and become overdue only after the date has ended.

## Atomic execution

For record-linked task kinds, one record action performs all required changes in one database transaction:

1. validate the open occurrence and task kind
2. preserve the planned occurrence snapshot
3. create the immutable animal logbook event
4. link the event to the task and occurrence
5. mark the occurrence completed

The unique task-occurrence link prevents duplicate logbook events for the same occurrence.

## Skipped and cancelled occurrences

Skipped and cancelled occurrences do not create a fachlicher logbook event. Their status, processing time and optional note remain in task history.

## Compatibility

Existing tasks are migrated as reminder tasks. Existing task and occurrence IDs remain valid. Technical occurrence-ID inputs remain available for automations, while the new record actions can select tasks by their Home Assistant task switch and optionally by scheduled date.
