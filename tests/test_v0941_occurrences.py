from __future__ import annotations

import sqlite3
import sys
from datetime import date
from pathlib import Path

TESTS = Path(__file__).resolve().parent
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))

from v0941_test_db import add_occurrence, add_task, occurrences, schema
from v0941_test_support import ROOT, TIMEZONE, load_feature_module

INIT = ROOT / "custom_components" / "animal_health" / "__init__.py"


def test_041_daily_required_occurrence_remains_overdue_beside_today() -> None:
    module, _v0815, store_class = load_feature_module()
    connection = sqlite3.connect(":memory:")
    schema(connection)
    task = add_task(connection)
    add_occurrence(connection, task, date(2026, 9, 3))

    module.ensure_preserving_occurrences(
        store_class(connection), connection, task, date(2026, 12, 1)
    )
    connection.commit()

    assert occurrences(connection) == [
        (date(2026, 9, 3), "pending"),
        (date(2026, 9, 4), "pending"),
    ]


def test_041_offline_gap_materializes_each_required_due_date() -> None:
    module, _v0815, store_class = load_feature_module()
    connection = sqlite3.connect(":memory:")
    schema(connection)
    task = add_task(connection)
    add_occurrence(connection, task, date(2026, 9, 1), "completed")

    module.ensure_preserving_occurrences(
        store_class(connection), connection, task, date(2026, 12, 1)
    )
    connection.commit()

    assert occurrences(connection) == [
        (date(2026, 9, 1), "completed"),
        (date(2026, 9, 2), "pending"),
        (date(2026, 9, 3), "pending"),
        (date(2026, 9, 4), "pending"),
    ]


def test_041_weekly_occurrence_stays_current_for_configured_period() -> None:
    module, _v0815, store_class = load_feature_module()
    connection = sqlite3.connect(":memory:")
    schema(connection)
    task = add_task(
        connection,
        start=date(2026, 8, 31),
        recurrence_type="weekly",
        created=date(2026, 8, 31),
    )
    store = store_class(connection, today=date(2026, 9, 2))

    module.ensure_preserving_occurrences(
        store, connection, task, date(2026, 12, 1)
    )
    connection.commit()
    assert occurrences(connection) == [(date(2026, 8, 31), "pending")]

    connection.execute("UPDATE task_occurrences SET status='completed'")
    connection.commit()
    module.ensure_preserving_occurrences(
        store, connection, task, date(2026, 12, 1)
    )
    connection.commit()
    assert occurrences(connection) == [
        (date(2026, 8, 31), "completed"),
        (date(2026, 9, 7), "pending"),
    ]


def test_041_closed_routine_periods_are_resolved_not_overdue() -> None:
    module, _v0815, store_class = load_feature_module()
    connection = sqlite3.connect(":memory:")
    schema(connection)
    task = add_task(connection, mode="routine")
    add_occurrence(connection, task, date(2026, 9, 1), "completed")

    module.ensure_preserving_occurrences(
        store_class(connection), connection, task, date(2026, 12, 1)
    )
    connection.commit()

    assert occurrences(connection) == [
        (date(2026, 9, 1), "completed"),
        (date(2026, 9, 2), "not_documented"),
        (date(2026, 9, 3), "not_documented"),
        (date(2026, 9, 4), "pending"),
    ]
    unresolved = connection.execute(
        """
        SELECT COUNT(*)
        FROM task_occurrence_plans AS plan
        JOIN task_occurrences AS occurrence ON occurrence.id=plan.occurrence_id
        WHERE occurrence.status='not_documented' AND plan.resolved_at IS NULL
        """
    ).fetchone()[0]
    assert unresolved == 0


def test_041_migration_recovers_only_latest_evidently_lost_date() -> None:
    module, _v0815, _store_class = load_feature_module()
    connection = sqlite3.connect(":memory:")
    schema(connection)
    task = add_task(
        connection, created=date(2026, 8, 1), updated=date(2026, 8, 1)
    )
    add_occurrence(connection, task, date(2026, 9, 4))

    for _index in range(2):
        module.recover_legacy_required_occurrences_once(
            connection, TIMEZONE, date(2026, 9, 4)
        )
        connection.commit()

    assert occurrences(connection) == [
        (date(2026, 9, 3), "pending"),
        (date(2026, 9, 4), "pending"),
    ]
    assert connection.execute(
        "SELECT COUNT(*) FROM v0941_state "
        "WHERE key='legacy_required_occurrence_recovery'"
    ).fetchone()[0] == 1


def test_041_first_upgrade_after_long_offline_does_not_skip_dates() -> None:
    module, _v0815, store_class = load_feature_module()
    connection = sqlite3.connect(":memory:")
    schema(connection)
    task = add_task(
        connection, created=date(2026, 8, 1), updated=date(2026, 8, 1)
    )
    add_occurrence(connection, task, date(2026, 9, 1))

    module.recover_legacy_required_occurrences_once(
        connection, TIMEZONE, date(2026, 9, 10)
    )
    module.ensure_preserving_occurrences(
        store_class(connection, today=date(2026, 9, 10)),
        connection,
        task,
        date(2026, 12, 1),
    )
    connection.commit()

    assert [item[0] for item in occurrences(connection)] == [
        date(2026, 9, day) for day in range(1, 11)
    ]


def test_041_new_backdated_series_does_not_fabricate_history() -> None:
    module, _v0815, store_class = load_feature_module()
    connection = sqlite3.connect(":memory:")
    schema(connection)
    task = add_task(
        connection,
        start=date(2026, 8, 1),
        created=date(2026, 9, 4),
        updated=date(2026, 9, 4),
    )

    module.ensure_preserving_occurrences(
        store_class(connection), connection, task, date(2026, 12, 1)
    )
    connection.commit()

    assert occurrences(connection) == [(date(2026, 9, 4), "pending")]


def test_041_patch_replaces_destructive_0815_paths_last() -> None:
    module, v0815, store_class = load_feature_module()
    module.apply_v0941_patches()
    assert store_class._ensure_occurrences_for_task is module.ensure_preserving_occurrences
    assert v0815._initialize_v0815_sync is module._initialize_v0941_sync

    source = INIT.read_text(encoding="utf-8")
    assert "from .v0941_features import apply_v0941_patches" in source
    assert source.index("apply_v0936_patches()") < source.index("apply_v0941_patches()")
