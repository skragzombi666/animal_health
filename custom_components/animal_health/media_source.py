from __future__ import annotations

from homeassistant.components.media_player import BrowseError
from homeassistant.components.media_source import MediaSource, MediaSourceItem, PlayMedia, Unresolvable
from homeassistant.core import HomeAssistant

from .ai_assist import get_ai_upload
from .const import DOMAIN


async def async_get_media_source(hass: HomeAssistant) -> MediaSource:
    return AnimalHealthMediaSource(hass)


class AnimalHealthMediaSource(MediaSource):
    name = "Animal Health AI"

    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__(DOMAIN)
        self.hass = hass

    async def async_resolve_media(self, item: MediaSourceItem) -> PlayMedia:
        record = get_ai_upload(self.hass, item.identifier)
        if record is None:
            raise Unresolvable("Animal Health AI upload expired or missing")
        return PlayMedia(
            url="",
            mime_type=str(record["media_type"]),
            path=__import__("pathlib").Path(record["path"]),
        )

    async def async_browse_media(self, item: MediaSourceItem):
        raise BrowseError("Temporary Animal Health AI uploads are not browsable")
