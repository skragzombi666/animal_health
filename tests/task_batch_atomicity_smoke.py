from __future__ import annotations

import gc
import importlib.util
import sqlite3
import sys
import tempfile
import types
from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).parents[1]
COMPONENT_DIR = ROOT / "custom_components" / "animal_health"
PACKAGE = "custom_components.animal_health"


def _package(name: str, path: Path) -> None:
    module = types.ModuleType(name)
    module.__path__ = [str(path)]
    sys.modules[name] = module


def _load_task_store():
    _package("custom_components", ROOT / "custom_components")
    _package(PACKAGE, COMPONENT_DIR)

    homeassistant = types.ModuleType("homeassistant")
    homeassistant.__path__ = []
    sys.modules["homeassistant"] = homeassistant

    core = types.ModuleType("homeassistant.core")
    core.HomeAssistant = object
    sys.modules["homeassistant.core"] = core

    util = types.ModuleType("homeassistant.util")
    util.__path__ = []
    sys.modules["homeassistant.util"] = util
    dt_util = types.ModuleType("homeassistant.util.dt")
    dt_util.get_time_zone = ZoneInfo
    sys.modules["homeassistant.util.dt"] = dt_util
    util.dt = dt_util

    const = types.ModuleType(f"{PACKAGE}.const")
    const.DATABASE_NAME = "animal_health.db"
    sys.modules[f"{PACKAGE}.const"] = const

    path = COMPONENT_DIR / "task_store.py"
    spec = importlib.util.spec_from_file_location(f"{PACKAGE}.task_store", path)
    if spec is None or spec.loader is None:
        raise AssertionError("Could not load task_store.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class _Config:
    time_zone = "UTC"

    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path

    def path(self, _name: str) -> str:
        return str(self._database_path)


class _Hass:
    def __init__(self, database_path: Path) -> None:
        self.config = _Config(database_path)


def _initialize_database(database_path: Path) -> None:
    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(
            """
            CREATE TABLE animals (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL
            );
            CREATE TABLE tasks (
                id TEXT PRIMARY KEY,
                animal_id TEXT REFERENCES animals(id),
                title TEXT NOT NULL,
                description TEXT,
                recurrence_type TEXT NOT NULL,
                recurrence_interval INTEGER NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT,
                due_time TEXT,
                is_active INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE task_occurrences (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
                scheduled_for TEXT NOT NULL,
                status TEXT NOT NULL,
                completed_at TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE task_record_configs (
                task_id TEXT PRIMARY KEY REFERENCES tasks(id) ON DELETE CASCADE
            );
            INSERT INTO animals VALUES ('AH-FIRST', 'First');
            INSERT INTO animals VALUES ('AH-SECOND', 'Second');
            """
        )


def _counts(database_path: Path) -> tuple[int, int, int]:
    with sqlite3.connect(database_path) as connection:
        return tuple(
            connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("tasks", "task_occurrences", "task_record_configs")
        )


def _create_batch(store, animal_ids, configure_task=None):
    return store._create_tasks_sync(
        animal_ids,
        "Atomic task",
        None,
        "once",
        1,
        date.today(),
        None,
        None,
        configure_task,
    )


def main() -> None:
    task_store_module = _load_task_store()
    with tempfile.TemporaryDirectory() as temporary_directory:
        database_path = Path(temporary_directory) / "animal_health.db"
        _initialize_database(database_path)
        store = task_store_module.TaskStore(_Hass(database_path))

        try:
            _create_batch(store, ["AH-FIRST", "AH-MISSING"])
        except KeyError:
            pass
        else:
            raise AssertionError("A stale later animal did not fail the batch")
        assert _counts(database_path) == (0, 0, 0)

        configured = 0

        def fail_second_configuration(
            connection: sqlite3.Connection,
            task_id: str,
        ) -> None:
            nonlocal configured
            connection.execute(
                "INSERT INTO task_record_configs VALUES (?)",
                (task_id,),
            )
            configured += 1
            if configured == 2:
                raise RuntimeError("simulated configuration failure")

        try:
            _create_batch(
                store,
                ["AH-FIRST", "AH-SECOND"],
                fail_second_configuration,
            )
        except RuntimeError:
            pass
        else:
            raise AssertionError("A later configuration failure did not fail the batch")
        assert _counts(database_path) == (0, 0, 0)

        def configure(
            connection: sqlite3.Connection,
            task_id: str,
        ) -> None:
            connection.execute(
                "INSERT INTO task_record_configs VALUES (?)",
                (task_id,),
            )

        tasks = _create_batch(
            store,
            ["AH-FIRST", "AH-SECOND"],
            configure,
        )
        assert len(tasks) == 2
        assert _counts(database_path) == (2, 2, 2)
        gc.collect()

    print("task batch atomicity smoke test passed")


if __name__ == "__main__":
    main()
