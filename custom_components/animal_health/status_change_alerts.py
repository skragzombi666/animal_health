from __future__ import annotations

from datetime import UTC, datetime, timedelta
import logging
from typing import Any, cast

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval

from .const import DOMAIN
from .runtime import AnimalHealthRuntimeData
from .v0912_features import _status_changes_sync

_LOGGER = logging.getLogger(__name__)
CHECK_INTERVAL = timedelta(minutes=15)
NOTIFICATION_ID = f"{DOMAIN}_status_changes_due"
EVENT_STATUS_CHANGE_DUE = f"{DOMAIN}_status_change_due"
_STATE_KEY = f"{DOMAIN}_status_change_alerts"


def _message(items: list[dict[str, Any]], *, german: bool) -> tuple[str, str]:
    if german:
        title = "Animal Health: Statusänderung fällig"
        rows = [
            f"- **{item['animal_name']}** → {item['target_status']} · geplant {item['planned_for']}"
            for item in items
        ]
        return title, "Bitte in Animal Health bestätigen, auf einen anderen Zeitpunkt verschieben oder abbrechen.\n\n" + "\n".join(rows)
    title = "Animal Health: Status change due"
    rows = [
        f"- **{item['animal_name']}** → {item['target_status']} · planned {item['planned_for']}"
        for item in items
    ]
    return title, "Please confirm, reschedule or cancel the change in Animal Health.\n\n" + "\n".join(rows)


async def async_check_status_change_alerts(
    hass: HomeAssistant,
    runtime: AnimalHealthRuntimeData,
    *,
    fire_events: bool,
) -> None:
    state = hass.data.setdefault(_STATE_KEY, {})
    if state.get("running"):
        return
    state["running"] = True
    try:
        items = await hass.async_add_executor_job(
            _status_changes_sync,
            runtime.feature_store.database_path,
        )
        due = [item for item in items if item.get("is_due")]
        ids = {str(item["id"]) for item in due}
        previous = set(state.get("ids", ()))
        german = str(getattr(hass.config, "language", "de") or "de").startswith("de")
        if due:
            signature = tuple(
                (item["id"], item["planned_for"], item["target_status"])
                for item in due
            )
            if signature != state.get("signature"):
                title, message = _message(due, german=german)
                persistent_notification.async_create(
                    hass,
                    message,
                    title,
                    NOTIFICATION_ID,
                )
            if fire_events and state.get("initialized"):
                for item in due:
                    if item["id"] in ids - previous:
                        hass.bus.async_fire(
                            EVENT_STATUS_CHANGE_DUE,
                            {
                                "change_id": item["id"],
                                "animal_id": item["animal_id"],
                                "animal_name": item["animal_name"],
                                "target_status": item["target_status"],
                                "planned_for": item["planned_for"],
                            },
                        )
        else:
            persistent_notification.async_dismiss(hass, NOTIFICATION_ID)
            signature = ()
        state["ids"] = tuple(sorted(ids))
        state["signature"] = signature
        state["initialized"] = True
    except Exception:  # noqa: BLE001
        _LOGGER.exception("Failed to update scheduled status-change reminders")
    finally:
        state["running"] = False


async def async_setup_status_change_alerts(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> None:
    runtime = cast(AnimalHealthRuntimeData, entry.runtime_data)
    await async_check_status_change_alerts(hass, runtime, fire_events=False)

    async def _scheduled(_now: datetime) -> None:
        await async_check_status_change_alerts(hass, runtime, fire_events=True)

    entry.async_on_unload(async_track_time_interval(hass, _scheduled, CHECK_INTERVAL))
