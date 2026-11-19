"""Event platform for the Infrared learning remote integration."""

from datetime import datetime, timedelta
from typing import override

from homeassistant.components.event import EventEntity
from homeassistant.components.infrared import (
    InfraredReceivedSignal,
    InfraredReceiverConsumerEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util
from homeassistant.util import slugify

from .const import CONF_INFRARED_RECEIVER_ENTITY_ID, CONF_TIMINGS, DOMAIN

PARALLEL_UPDATES = 0

# Two captures of the same button press never have identical timings.
TIMING_TOLERANCE = 0.25

# Some protocols send the full frame several times for one press, and the
# receiver reports each frame as its own signal.
REPEAT_WINDOW = timedelta(seconds=0.5)


def _timings_match(received: list[int], learned: list[int]) -> bool:
    """Return True if each received timing is close to the learned timing."""
    return len(received) == len(learned) and all(
        abs(r - l) <= TIMING_TOLERANCE * abs(l)
        for r, l in zip(received, learned, strict=True)
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the event entity from a config entry."""
    async_add_entities([InfraredLearningRemoteEvent(entry)])


class InfraredLearningRemoteEvent(InfraredReceiverConsumerEntity, EventEntity):
    """Event entity that fires when the receiver gets a learned command."""

    _attr_has_entity_name = True
    _attr_translation_key = "received_command"

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the entity."""
        self._attr_unique_id = entry.entry_id
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)})
        self._infrared_receiver_entity_id = entry.data[CONF_INFRARED_RECEIVER_ENTITY_ID]
        self._commands = {
            slugify(subentry.title): subentry.data[CONF_TIMINGS]
            for subentry in entry.subentries.values()
        }
        self._attr_event_types = list(self._commands)
        self._last_event: tuple[str, datetime] | None = None

    @callback
    @override
    def _handle_signal(self, signal: InfraredReceivedSignal) -> None:
        """Fire an event when the signal matches a learned command."""
        for event_type, timings in self._commands.items():
            if _timings_match(signal.timings, timings):
                break
        else:
            return

        now = dt_util.utcnow()
        if self._last_event is not None:
            last_event_type, last_time = self._last_event
            if last_event_type == event_type and now - last_time < REPEAT_WINDOW:
                return
        self._last_event = (event_type, now)

        self._trigger_event(event_type)
        self.async_write_ha_state()
