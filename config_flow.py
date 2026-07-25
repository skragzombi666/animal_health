from __future__ import annotations

from homeassistant import config_entries

from .const import DOMAIN


class AnimalHealthConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(
                title="Animal Health",
                data={},
            )

        return self.async_show_form(
            step_id="user",
        )