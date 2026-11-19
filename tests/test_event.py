"""Test the Infrared learning remote event platform."""

from datetime import timedelta

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.components.event import ATTR_EVENT_TYPE, ATTR_EVENT_TYPES
from homeassistant.components.infrared import InfraredReceivedSignal
from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from pytest_homeassistant.common import MockConfigEntry
from pytest_homeassistant.components.infrared.common import MockInfraredReceiverEntity

from .conftest import TIMINGS

ENTITY_ID = "event.living_room_tv_received_command"

# Each timing is 20% off the learned timing, within the 25% tolerance.
JITTERED_TIMINGS = [round(timing * 1.2) for timing in TIMINGS]


@pytest.fixture(autouse=True)
async def setup_entry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_infrared_receiver_entity: MockInfraredReceiverEntity,
) -> None:
    """Set up the config entry with a receiver."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()


async def test_event_types(hass: HomeAssistant) -> None:
    """Test the event types are the learned commands."""
    state = hass.states.get(ENTITY_ID)
    assert state is not None
    assert state.state == STATE_UNKNOWN
    assert state.attributes[ATTR_EVENT_TYPES] == ["power"]


async def test_matching_signal(
    hass: HomeAssistant,
    mock_infrared_receiver_entity: MockInfraredReceiverEntity,
) -> None:
    """Test a signal close to a learned command fires its event."""
    mock_infrared_receiver_entity._handle_received_signal(
        InfraredReceivedSignal(timings=JITTERED_TIMINGS)
    )
    await hass.async_block_till_done()

    state = hass.states.get(ENTITY_ID)
    assert state is not None
    assert state.state != STATE_UNKNOWN
    assert state.attributes[ATTR_EVENT_TYPE] == "power"


@pytest.mark.parametrize(
    "timings",
    [
        pytest.param(TIMINGS[:-1], id="different_length"),
        pytest.param([round(t * 1.3) for t in TIMINGS], id="outside_tolerance"),
        pytest.param([-t for t in TIMINGS], id="inverted"),
    ],
)
async def test_signal_without_match(
    hass: HomeAssistant,
    mock_infrared_receiver_entity: MockInfraredReceiverEntity,
    timings: list[int],
) -> None:
    """Test a signal that matches no learned command fires no event."""
    mock_infrared_receiver_entity._handle_received_signal(
        InfraredReceivedSignal(timings=timings)
    )
    await hass.async_block_till_done()

    state = hass.states.get(ENTITY_ID)
    assert state is not None
    assert state.state == STATE_UNKNOWN


async def test_repeated_frames(
    hass: HomeAssistant,
    mock_infrared_receiver_entity: MockInfraredReceiverEntity,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test frames repeated within the repeat window fire one event."""
    mock_infrared_receiver_entity._handle_received_signal(
        InfraredReceivedSignal(timings=TIMINGS)
    )
    await hass.async_block_till_done()
    first_state = hass.states.get(ENTITY_ID)
    assert first_state is not None

    freezer.tick(timedelta(milliseconds=100))
    mock_infrared_receiver_entity._handle_received_signal(
        InfraredReceivedSignal(timings=TIMINGS)
    )
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID) == first_state

    # A second press after the repeat window fires again.
    freezer.tick(timedelta(seconds=1))
    mock_infrared_receiver_entity._handle_received_signal(
        InfraredReceivedSignal(timings=TIMINGS)
    )
    await hass.async_block_till_done()
    state = hass.states.get(ENTITY_ID)
    assert state is not None
    assert state.state != first_state.state
