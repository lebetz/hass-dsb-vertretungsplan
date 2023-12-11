"""The DSB Vertretungsplan component."""
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .dsbapi import DSBApi

from aiohttp.client_exceptions import ClientConnectorError

from typing import Any

import logging
import voluptuous as vol
import re

from .const import CONF_PASS, CONF_TUTOR_GROUP, CONF_USER, DEFAULT_NAME, DOMAIN, PREFIX

_LOGGER = logging.getLogger(__name__)



class DSBVertretungsplanConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow for DSB Vertretungsplan."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize."""
        self.dsb: DSBApi = None


    def _get_schema(self, user_input):
        """Provide schema for user input."""
        schema = vol.Schema({
            vol.Required(CONF_TUTOR_GROUP, default=user_input.get(CONF_TUTOR_GROUP, '')): cv.string,
            vol.Required(CONF_USER, default=user_input.get(CONF_USER, '')): cv.string,
            vol.Required(CONF_PASS, default=user_input.get(CONF_PASS, '')): cv.string
        })
        return schema


    async def async_step_user(self, user_input: dict[str, Any] = None) -> FlowResult:
        """Handle initial step of user config flow."""

        errors = {}

        # user input was provided, so check and save it
        if user_input is not None:
            try:
                # let's check the tutor group first and normalize
                tutor_group = user_input[CONF_TUTOR_GROUP]
                if tutor_group == None:
                    raise TutorGroupError
                tutor_group = re.sub('\s', '', tutor_group)
                if len(tutor_group) == 0:
                    raise TutorGroupError
                user_input[CONF_TUTOR_GROUP] = tutor_group.lower()

                # let's try and connect to DSB
                session = async_get_clientsession(self.hass)
                user = user_input[CONF_USER]
                password = user_input[CONF_PASS]
                self.dsb = DSBApi(session, user, password)

                # try to load some data
                await self.dsb.fetch_entries()

                # use the tutor_group as unique_id
                unique_id = user_input[CONF_TUTOR_GROUP]
                _LOGGER.debug(f"async_step_user: unique_id={unique_id}")

                # set the unique id for the entry, abort if it already exists
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                # compile a name and return the config entry
                return self.async_create_entry(
                    title=PREFIX + " " + user_input[CONF_TUTOR_GROUP],
                    data=user_input
                )

            except (ConnectionError, ClientConnectorError) as e:
                errors['base'] = "authentication"
            except TutorGroupError:
                errors[CONF_TUTOR_GROUP] = "tutor_group"

        if user_input is None:
            user_input = {}

        # no user_input so far
        # what to ask the user
        schema = self._get_schema(user_input)

        # show the form to the user
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

class TutorGroupError(Exception):
    pass