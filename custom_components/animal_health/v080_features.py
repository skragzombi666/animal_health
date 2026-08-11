from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .feature_store import AnimalHealthFeatureStore
from .runtime import AnimalHealthRuntimeData

_STATE_COMMAND = f"{DOMAIN}/v080/state"
_CREATE_TAG_COMMAND = f"{DOMAIN}/tags/create"
_UPDATE_TAG_COMMAND = f"{DOMAIN}/tags/update"
_DELETE_TAG_COMMAND = f"{DOMAIN}/tags/delete"
_SET_TAGS_COMMAND = f"{DOMAIN}/tags/set"
_SET_PHOTO_COMMAND = f"{DOMAIN}/animal_photo/set"
_REMOVE_PHOTO_COMMAND = f"{DOMAIN}/animal_photo/remove"
_DEFAULT_GROUP_NAME = "Unzugeordnet"


def _runtime_data(hass: HomeAssistant) -> AnimalHealthRuntimeData:
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is ConfigEntryState.LOADED:
            return cast(AnimalHealthRuntimeData, entry.runtime_data)
    raise RuntimeError("Animal Health is not loaded")


def _required_text(value: Any) -> str:
    text = str(value).strip()
    if not text:
        raise vol.Invalid("value must not be empty")
    return text


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _text_list(value: Any) -> list[str]:
    if value is None:
        return []
    values = value if isinstance(value, list) else [value]
    result: list[str] = []
    for item in values:
        text = str(item).strip()
        if text and text not in result:
            result.append(text)
    return result


def _initialize_sync(store: AnimalHealthFeatureStore) -> None:
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    with store._connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS animal_tags (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_animal_tags_name
                ON animal_tags(name COLLATE NOCASE);

            CREATE TABLE IF NOT EXISTS animal_tag_memberships (
                animal_id TEXT NOT NULL
                    REFERENCES animals(id) ON DELETE CASCADE,
                tag_id TEXT NOT NULL
                    REFERENCES animal_tags(id) ON DELETE CASCADE,
                created_at TEXT NOT NULL,
                PRIMARY KEY (animal_id, tag_id)
            );
            CREATE INDEX IF NOT EXISTS idx_animal_tag_memberships_tag
                ON animal_tag_memberships(tag_id, animal_id);

            CREATE TABLE IF NOT EXISTS animal_profiles (
                animal_id TEXT PRIMARY KEY
                    REFERENCES animals(id) ON DELETE CASCADE,
                image_attachment_id TEXT
                    REFERENCES attachments(id) ON DELETE SET NULL,
                updated_at TEXT NOT NULL
            );
            """
        )

        ungrouped = [
            str(row[0])
            for row in connection.execute(
                """
                SELECT animal.id
                FROM animals AS animal
                LEFT JOIN animal_group_memberships AS membership
                    ON membership.animal_id = animal.id
                WHERE membership.animal_id IS NULL
                """
            ).fetchall()
        ]
        if not ungrouped:
            return

        group = connection.execute(
            "SELECT id FROM animal_groups WHERE name = ? COLLATE NOCASE LIMIT 1",
            (_DEFAULT_GROUP_NAME,),
        ).fetchone()
        if group is None:
            existing = {
                str(row[0])
                for row in connection.execute("SELECT id FROM animal_groups").fetchall()
            }
            group_id = store._record_id("GR", existing)
            connection.execute(
                """
                INSERT INTO animal_groups (
                    id, name, species, description, created_at, updated_at
                ) VALUES (?, ?, NULL, ?, ?, ?)
                """,
                (
                    group_id,
                    _DEFAULT_GROUP_NAME,
                    "Automatisch für bestehende Tiere ohne primäre Tiergruppe angelegt.",
                    now,
                    now,
                ),
            )
        else:
            group_id = str(group["id"])

        connection.executemany(
            """
            INSERT INTO animal_group_memberships (animal_id, group_id, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(animal_id) DO UPDATE SET
                group_id = excluded.group_id,
                updated_at = excluded.updated_at
            """,
            [(animal_id, group_id, now) for animal_id in ungrouped],
        )


def _state_sync(store: AnimalHealthFeatureStore) -> dict[str, Any]:
    with store._connect() as connection:
        tags = [
            dict(row)
            for row in connection.execute(
                """
                SELECT
                    tag.id,
                    tag.name,
                    tag.description,
                    tag.created_at,
                    tag.updated_at,
                    COUNT(membership.animal_id) AS animal_count
                FROM animal_tags AS tag
                LEFT JOIN animal_tag_memberships AS membership
                    ON membership.tag_id = tag.id
                GROUP BY tag.id
                ORDER BY tag.name COLLATE NOCASE, tag.id
                """
            ).fetchall()
        ]
        memberships: dict[str, list[str]] = {}
        for row in connection.execute(
            """
            SELECT animal_id, tag_id
            FROM animal_tag_memberships
            ORDER BY animal_id, tag_id
            """
        ).fetchall():
            memberships.setdefault(str(row["animal_id"]), []).append(str(row["tag_id"]))
        profiles = {
            str(row["animal_id"]): (
                str(row["image_attachment_id"])
                if row["image_attachment_id"] is not None
                else None
            )
            for row in connection.execute(
                "SELECT animal_id, image_attachment_id FROM animal_profiles"
            ).fetchall()
        }
    return {
        "primary_group_required": True,
        "tags": tags,
        "tag_memberships": memberships,
        "profiles": profiles,
    }


def _create_tag_sync(
    store: AnimalHealthFeatureStore,
    name: str,
    description: str | None,
) -> dict[str, Any]:
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    with store._connect() as connection:
        existing = {
            str(row[0]) for row in connection.execute("SELECT id FROM animal_tags").fetchall()
        }
        tag_id = store._record_id("TG", existing)
        try:
            connection.execute(
                """
                INSERT INTO animal_tags (id, name, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (tag_id, name, description, now, now),
            )
        except Exception as err:
            if "UNIQUE" in str(err).upper():
                raise ValueError("A tag with this name already exists") from err
            raise
    return {
        "id": tag_id,
        "name": name,
        "description": description,
        "created_at": now,
        "updated_at": now,
        "animal_count": 0,
    }


def _update_tag_sync(
    store: AnimalHealthFeatureStore,
    tag_id: str,
    name: str,
    description: str | None,
) -> dict[str, Any]:
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    with store._connect() as connection:
        try:
            cursor = connection.execute(
                """
                UPDATE animal_tags
                SET name = ?, description = ?, updated_at = ?
                WHERE id = ?
                """,
                (name, description, now, tag_id),
            )
        except Exception as err:
            if "UNIQUE" in str(err).upper():
                raise ValueError("A tag with this name already exists") from err
            raise
        if cursor.rowcount == 0:
            raise KeyError(tag_id)
        count = int(
            connection.execute(
                "SELECT COUNT(*) FROM animal_tag_memberships WHERE tag_id = ?",
                (tag_id,),
            ).fetchone()[0]
        )
    return {
        "id": tag_id,
        "name": name,
        "description": description,
        "updated_at": now,
        "animal_count": count,
    }


def _delete_tag_sync(store: AnimalHealthFeatureStore, tag_id: str) -> None:
    with store._connect() as connection:
        cursor = connection.execute("DELETE FROM animal_tags WHERE id = ?", (tag_id,))
        if cursor.rowcount == 0:
            raise KeyError(tag_id)


def _set_tags_sync(
    store: AnimalHealthFeatureStore,
    animal_id: str,
    tag_ids: list[str],
) -> list[str]:
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    with store._connect() as connection:
        if connection.execute(
            "SELECT 1 FROM animals WHERE id = ?", (animal_id,)
        ).fetchone() is None:
            raise KeyError(animal_id)
        if tag_ids:
            known = {
                str(row[0])
                for row in connection.execute(
                    f"SELECT id FROM animal_tags WHERE id IN ({','.join('?' for _ in tag_ids)})",
                    tag_ids,
                ).fetchall()
            }
            missing = [tag_id for tag_id in tag_ids if tag_id not in known]
            if missing:
                raise KeyError(missing[0])
        connection.execute(
            "DELETE FROM animal_tag_memberships WHERE animal_id = ?", (animal_id,)
        )
        connection.executemany(
            """
            INSERT INTO animal_tag_memberships (animal_id, tag_id, created_at)
            VALUES (?, ?, ?)
            """,
            [(animal_id, tag_id, now) for tag_id in tag_ids],
        )
    return tag_ids


def _set_photo_sync(
    store: AnimalHealthFeatureStore,
    animal_id: str,
    attachment_id: str,
) -> str | None:
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    with store._connect() as connection:
        attachment = connection.execute(
            """
            SELECT animal_id, media_type
            FROM attachments
            WHERE id = ?
            """,
            (attachment_id,),
        ).fetchone()
        if attachment is None:
            raise KeyError(attachment_id)
        if str(attachment["animal_id"]) != animal_id:
            raise ValueError("Animal photo belongs to another animal")
        if not str(attachment["media_type"] or "").startswith("image/"):
            raise ValueError("Animal photo must be an image")
        previous = connection.execute(
            "SELECT image_attachment_id FROM animal_profiles WHERE animal_id = ?",
            (animal_id,),
        ).fetchone()
        previous_id = (
            str(previous["image_attachment_id"])
            if previous is not None and previous["image_attachment_id"] is not None
            else None
        )
        connection.execute(
            """
            INSERT INTO animal_profiles (animal_id, image_attachment_id, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(animal_id) DO UPDATE SET
                image_attachment_id = excluded.image_attachment_id,
                updated_at = excluded.updated_at
            """,
            (animal_id, attachment_id, now),
        )
    return previous_id


def _remove_photo_sync(store: AnimalHealthFeatureStore, animal_id: str) -> str | None:
    now = datetime.now(UTC).replace(microsecond=0).isoformat()
    with store._connect() as connection:
        if connection.execute(
            "SELECT 1 FROM animals WHERE id = ?", (animal_id,)
        ).fetchone() is None:
            raise KeyError(animal_id)
        previous = connection.execute(
            "SELECT image_attachment_id FROM animal_profiles WHERE animal_id = ?",
            (animal_id,),
        ).fetchone()
        previous_id = (
            str(previous["image_attachment_id"])
            if previous is not None and previous["image_attachment_id"] is not None
            else None
        )
        connection.execute(
            """
            INSERT INTO animal_profiles (animal_id, image_attachment_id, updated_at)
            VALUES (?, NULL, ?)
            ON CONFLICT(animal_id) DO UPDATE SET
                image_attachment_id = NULL,
                updated_at = excluded.updated_at
            """,
            (animal_id, now),
        )
    return previous_id


async def async_initialize_v080_features(store: AnimalHealthFeatureStore) -> None:
    await store._hass.async_add_executor_job(_initialize_sync, store)


def async_setup_v080_features(hass: HomeAssistant) -> None:
    @websocket_api.websocket_command({vol.Required("type"): _STATE_COMMAND})
    @websocket_api.async_response
    async def websocket_state(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            store = _runtime_data(hass).feature_store
            state = await hass.async_add_executor_job(_state_sync, store)
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "v080_state_failed", str(err))
            return
        connection.send_result(msg["id"], state)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _CREATE_TAG_COMMAND,
            vol.Required("name"): _required_text,
            vol.Optional("description"): _optional_text,
        }
    )
    @websocket_api.async_response
    async def websocket_create_tag(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            store = _runtime_data(hass).feature_store
            tag = await hass.async_add_executor_job(
                _create_tag_sync, store, msg["name"], msg.get("description")
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "create_tag_failed", str(err))
            return
        connection.send_result(msg["id"], tag)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _UPDATE_TAG_COMMAND,
            vol.Required("tag_id"): _required_text,
            vol.Required("name"): _required_text,
            vol.Optional("description"): _optional_text,
        }
    )
    @websocket_api.async_response
    async def websocket_update_tag(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            store = _runtime_data(hass).feature_store
            tag = await hass.async_add_executor_job(
                _update_tag_sync,
                store,
                msg["tag_id"],
                msg["name"],
                msg.get("description"),
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "update_tag_failed", str(err))
            return
        connection.send_result(msg["id"], tag)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _DELETE_TAG_COMMAND,
            vol.Required("tag_id"): _required_text,
        }
    )
    @websocket_api.async_response
    async def websocket_delete_tag(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            store = _runtime_data(hass).feature_store
            await hass.async_add_executor_job(_delete_tag_sync, store, msg["tag_id"])
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "delete_tag_failed", str(err))
            return
        connection.send_result(msg["id"], {"deleted": msg["tag_id"]})

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _SET_TAGS_COMMAND,
            vol.Required("animal_id"): _required_text,
            vol.Optional("tag_ids", default=[]): _text_list,
        }
    )
    @websocket_api.async_response
    async def websocket_set_tags(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            store = _runtime_data(hass).feature_store
            tag_ids = await hass.async_add_executor_job(
                _set_tags_sync, store, msg["animal_id"], msg.get("tag_ids", [])
            )
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "set_tags_failed", str(err))
            return
        connection.send_result(
            msg["id"], {"animal_id": msg["animal_id"], "tag_ids": tag_ids}
        )

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _SET_PHOTO_COMMAND,
            vol.Required("animal_id"): _required_text,
            vol.Required("attachment_id"): _required_text,
        }
    )
    @websocket_api.async_response
    async def websocket_set_photo(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            store = _runtime_data(hass).feature_store
            previous = await hass.async_add_executor_job(
                _set_photo_sync, store, msg["animal_id"], msg["attachment_id"]
            )
            if previous and previous != msg["attachment_id"]:
                await store.delete_attachment(previous)
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "set_photo_failed", str(err))
            return
        connection.send_result(
            msg["id"],
            {
                "animal_id": msg["animal_id"],
                "image_attachment_id": msg["attachment_id"],
            },
        )

    @websocket_api.websocket_command(
        {
            vol.Required("type"): _REMOVE_PHOTO_COMMAND,
            vol.Required("animal_id"): _required_text,
        }
    )
    @websocket_api.async_response
    async def websocket_remove_photo(
        hass: HomeAssistant,
        connection: websocket_api.ActiveConnection,
        msg: dict[str, Any],
    ) -> None:
        try:
            store = _runtime_data(hass).feature_store
            previous = await hass.async_add_executor_job(
                _remove_photo_sync, store, msg["animal_id"]
            )
            if previous:
                await store.delete_attachment(previous)
        except Exception as err:  # noqa: BLE001
            connection.send_error(msg["id"], "remove_photo_failed", str(err))
            return
        connection.send_result(msg["id"], {"animal_id": msg["animal_id"]})

    websocket_api.async_register_command(hass, websocket_state)
    websocket_api.async_register_command(hass, websocket_create_tag)
    websocket_api.async_register_command(hass, websocket_update_tag)
    websocket_api.async_register_command(hass, websocket_delete_tag)
    websocket_api.async_register_command(hass, websocket_set_tags)
    websocket_api.async_register_command(hass, websocket_set_photo)
    websocket_api.async_register_command(hass, websocket_remove_photo)
