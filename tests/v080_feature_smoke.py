from __future__ import annotations

import importlib.util
import sqlite3
import sys
import tempfile
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT_DIR = ROOT / "custom_components" / "animal_health"
PACKAGE = "custom_components.animal_health"


def _stub_modules() -> None:
    custom_components = types.ModuleType("custom_components")
    custom_components.__path__ = [str(ROOT / "custom_components")]
    sys.modules["custom_components"] = custom_components
    package = types.ModuleType(PACKAGE)
    package.__path__ = [str(COMPONENT_DIR)]
    sys.modules[PACKAGE] = package

    vol = types.ModuleType("voluptuous")
    vol.Invalid = ValueError
    vol.Required = lambda key, **_kwargs: key
    vol.Optional = lambda key, **_kwargs: key
    sys.modules["voluptuous"] = vol

    homeassistant = types.ModuleType("homeassistant")
    homeassistant.__path__ = []
    sys.modules["homeassistant"] = homeassistant
    components = types.ModuleType("homeassistant.components")
    components.__path__ = []
    sys.modules["homeassistant.components"] = components
    websocket_api = types.ModuleType("homeassistant.components.websocket_api")
    sys.modules["homeassistant.components.websocket_api"] = websocket_api
    config_entries = types.ModuleType("homeassistant.config_entries")
    config_entries.ConfigEntryState = type("ConfigEntryState", (), {"LOADED": "loaded"})
    sys.modules["homeassistant.config_entries"] = config_entries
    core = types.ModuleType("homeassistant.core")
    core.HomeAssistant = type("HomeAssistant", (), {})
    sys.modules["homeassistant.core"] = core

    const = types.ModuleType(f"{PACKAGE}.const")
    const.DOMAIN = "animal_health"
    sys.modules[f"{PACKAGE}.const"] = const
    feature_store = types.ModuleType(f"{PACKAGE}.feature_store")
    feature_store.AnimalHealthFeatureStore = type("AnimalHealthFeatureStore", (), {})
    sys.modules[f"{PACKAGE}.feature_store"] = feature_store
    runtime = types.ModuleType(f"{PACKAGE}.runtime")
    runtime.AnimalHealthRuntimeData = type("AnimalHealthRuntimeData", (), {})
    sys.modules[f"{PACKAGE}.runtime"] = runtime


def _load_module(name: str):
    spec = importlib.util.spec_from_file_location(f"{PACKAGE}.{name}", COMPONENT_DIR / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeStore:
    def __init__(self, database: Path) -> None:
        self.database = database

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @staticmethod
    def _record_id(prefix: str, existing: set[str]) -> str:
        number = 1
        while f"{prefix}-TEST{number}" in existing:
            number += 1
        return f"{prefix}-TEST{number}"


def main() -> None:
    _stub_modules()
    features = _load_module("v080_features")

    with tempfile.TemporaryDirectory() as temporary_dir:
        database = Path(temporary_dir) / "animal_health.db"
        with sqlite3.connect(database) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.executescript(
                """
                CREATE TABLE animals (id TEXT PRIMARY KEY, name TEXT NOT NULL);
                CREATE TABLE animal_groups (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    species TEXT,
                    description TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE UNIQUE INDEX idx_animal_groups_name ON animal_groups(name COLLATE NOCASE);
                CREATE TABLE animal_group_memberships (
                    animal_id TEXT PRIMARY KEY REFERENCES animals(id) ON DELETE CASCADE,
                    group_id TEXT NOT NULL REFERENCES animal_groups(id) ON DELETE CASCADE,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE attachments (
                    id TEXT PRIMARY KEY,
                    animal_id TEXT NOT NULL REFERENCES animals(id) ON DELETE CASCADE,
                    event_id TEXT,
                    filename TEXT NOT NULL,
                    media_type TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    storage_name TEXT NOT NULL UNIQUE,
                    title TEXT,
                    created_at TEXT NOT NULL
                );
                INSERT INTO animals VALUES ('AH-1', 'Curry');
                INSERT INTO animals VALUES ('AH-2', 'BBQ');
                INSERT INTO animal_groups VALUES ('GR-1','Tschiggis','chicken',NULL,'2026-08-08','2026-08-08');
                INSERT INTO animal_group_memberships VALUES ('AH-1','GR-1','2026-08-08');
                INSERT INTO attachments VALUES ('AT-1','AH-1',NULL,'curry.jpg','image/jpeg',100,'AT-1.jpg','Tierbild','2026-08-08');
                """
            )

        store = FakeStore(database)
        features._initialize_sync(store)
        with store._connect() as connection:
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            assert {"animal_tags", "animal_tag_memberships", "animal_profiles"} <= tables
            membership = connection.execute(
                "SELECT group_id FROM animal_group_memberships WHERE animal_id='AH-2'"
            ).fetchone()
            assert membership is not None, "Existing ungrouped animal was not migrated"
            group = connection.execute(
                "SELECT name FROM animal_groups WHERE id=?", (membership["group_id"],)
            ).fetchone()
            assert group["name"] == "Unzugeordnet"

        tag = features._create_tag_sync(store, "Bumblefoot", "Fussbehandlung")
        features._set_tags_sync(store, "AH-1", [tag["id"]])
        assert features._set_photo_sync(store, "AH-1", "AT-1") is None
        state = features._state_sync(store)
        assert state["primary_group_required"] is True
        assert state["tag_memberships"]["AH-1"] == [tag["id"]]
        assert state["profiles"]["AH-1"] == "AT-1"
        previous = features._remove_photo_sync(store, "AH-1")
        assert previous == "AT-1"
        assert features._state_sync(store)["profiles"]["AH-1"] is None
        features._delete_tag_sync(store, tag["id"])
        assert features._state_sync(store)["tags"] == []

    print("Animal Health 0.8.0 feature migration validation passed")


if __name__ == "__main__":
    main()
