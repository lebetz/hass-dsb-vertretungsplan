"""The DSB Vertretungsplan component."""
from __future__ import annotations
from typing import Dict
from datetime import datetime, timedelta, timezone
from babel.dates import format_date, format_datetime
from dataclasses import asdict

from .dsbapi import DSBApi

from .const import *

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data[DOMAIN] = dict()
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setup DSB Vertretungsplan from a config entry."""

    # setup the parser
    session = async_get_clientsession(hass)
    user = entry.data[CONF_USER]
    password = entry.data[CONF_PASS]
    dsb = DSBApi(session, user, password)
    await dsb.fetch_entries()

    # setup a coordinator
    coordinator = DSBDataUpdateCoordinator(hass, _LOGGER, dsb, timedelta(seconds=POLLING_INTERVAL))

    # refresh coordinator for the first time to load initial data
    await coordinator.async_config_entry_first_refresh()
    
    # store coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # setup sensors
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class DSBDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Vertretungsplan data from the DSB."""

    def __init__(self, hass: HomeAssistant, _LOGGER, dsb: DSBApi, update_interval: timedelta) -> None:
        """Initialize."""

        self.dsb = dsb
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=update_interval)


    async def _async_update_data(self) -> Dict:
        """Update data via library."""
        _LOGGER.debug(f"_async_update_data() called")

        """Only update in time window."""
        # todo: allow forced update
        try:
            now = datetime.now().time()
            start = datetime.strptime(POLLING_START, '%H:%M').time()
            end = datetime.strptime(POLLING_END, '%H:%M').time()
            if self.data is not None and (now < start or now > end):
                _LOGGER.debug(f"Time is outside polling window, skipping update")
                return self.data
        except (Exception) as error:
            # in case something goes wrong with date/time parsing, we just update the data and continue
            _LOGGER.error(f"Error occured with time parsing and comparison on update: {error}\n"
                          f"Start and end times should be in format 'HH:MM'.\n"
                          f"Configured are POLLING_START={POLLING_START} and POLLING_END={POLLING_END}\n"
                          f"Please inform the maintainer of the integration.")
            pass

        try:
            """Ask the library to reload fresh data."""
            plaene = await self.dsb.fetch_entries()
            _LOGGER.debug(f"data loaded")
        except (ConnectionError) as error:
            raise UpdateFailed(error) from error

        """Let's return the raw list of all Vertretungen."""
        today = datetime.now().astimezone().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        klassenliste = {}
        for vertretungen in plaene:
            for vertretung in vertretungen:
                stand = vertretung['updated']
                # skip old stuff before today
                if vertretung['date'] < today:
                    continue
                # add to our list
                if vertretung['class'] in klassenliste:
                    klassenliste[vertretung['class']].append(vertretung)
                else:
                    klassenliste[vertretung['class']] = [vertretung]

        """Now put it all together."""
        extra_states = {
            ATTR_VERTRETUNG: klassenliste,
            ATTR_STATUS: stand
        }
        _LOGGER.debug(f"Status as of {stand}")
        return extra_states