"""Tests for the MQTT subscription reconnect loop in python_snoo.snoo.Snoo."""

import asyncio
import json
from types import SimpleNamespace

import aiomqtt
import pytest

import python_snoo.snoo as snoo_module
from python_snoo.containers import AuthorizationInfo
from python_snoo.snoo import Snoo

PAYLOAD = {
    "system_state": "normal",
    "sw_version": "v1.15.07",
    "state_machine": {
        "session_id": "1",
        "state": "BASELINE",
        "prev_state": "ONLINE",
        "is_active_session": "true",
        "since_session_start_ms": 1000,
        "time_left": -1,
        "hold": "off",
        "weaning": "off",
        "audio": "on",
        "up_transition": "LEVEL1",
        "down_transition": "NONE",
        "sticky_white_noise": "off",
    },
    "left_safety_clip": 1,
    "right_safety_clip": 1,
    "event": "command",
    "event_time_ms": 1793223140196,
    "rx_signal": {"rssi": -56, "strength": 78},
    "iot_capable": True,
}


class FakeClient:
    """Stand-in for aiomqtt.Client driven by a script of connection outcomes.

    Each script entry is either ``"connect_error"`` (connecting raises MqttError) or an
    int ``n`` (connect succeeds, ``n`` messages are delivered, then the connection
    drops with MqttError, mirroring "Disconnected during message iteration").
    """

    script: list = []
    instances: list = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.subscribed: list[str] = []
        self.outcome = FakeClient.script.pop(0) if FakeClient.script else "hang"
        FakeClient.instances.append(self)

    async def __aenter__(self):
        if self.outcome == "connect_error":
            raise aiomqtt.MqttError("Operation timed out")
        return self

    async def __aexit__(self, *exc):
        return False

    async def subscribe(self, topic):
        self.subscribed.append(topic)

    @property
    def messages(self):
        return self._messages()

    async def _messages(self):
        if self.outcome == "hang":
            await asyncio.Event().wait()  # stay connected until cancelled
        for _ in range(int(self.outcome)):
            yield SimpleNamespace(topic="t/state_machine/activity_state", payload=json.dumps(PAYLOAD).encode())
        raise aiomqtt.MqttError("Disconnected during message iteration")


@pytest.fixture
def fast_backoff(monkeypatch):
    monkeypatch.setattr(snoo_module, "MQTT_RECONNECT_MIN_DELAY", 0.01)
    monkeypatch.setattr(snoo_module, "MQTT_RECONNECT_MAX_DELAY", 0.02)
    monkeypatch.setattr(snoo_module, "MQTT_STABLE_CONNECTION_SECONDS", 0.0)


@pytest.fixture
def snoo(monkeypatch, fast_backoff):
    FakeClient.script = []
    FakeClient.instances = []
    monkeypatch.setattr(snoo_module.aiomqtt, "Client", FakeClient)
    s = Snoo("user@example.com", "pw", clientsession=None)
    s.tokens = AuthorizationInfo(snoo="snoo-token", aws_access="a", aws_id="id-token", aws_refresh="r")
    return s


def make_device():
    return SimpleNamespace(
        serialNumber="123",
        awsIoT=SimpleNamespace(clientEndpoint="example.invalid", thingName="thing_123"),
    )


async def wait_for(predicate, timeout=2.0):
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while not predicate():
        if loop.time() > deadline:
            raise AssertionError("condition not met in time")
        await asyncio.sleep(0.005)


@pytest.mark.asyncio
async def test_reconnects_after_connect_failure(snoo):
    """A failed connect is retried instead of killing the subscription."""
    FakeClient.script = ["connect_error", 1, "hang"]
    received = []
    snoo.start_subscribe(make_device(), received.append)

    await wait_for(lambda: len(received) == 1)
    await wait_for(lambda: len(FakeClient.instances) == 3)
    assert received[0].state_machine.state.value == "BASELINE"
    assert FakeClient.instances[2].subscribed == ["thing_123/state_machine/activity_state"]
    await snoo.disconnect()


@pytest.mark.asyncio
async def test_reconnects_after_mid_stream_disconnect(snoo):
    """A connection that drops while iterating messages is re-established."""
    FakeClient.script = [1, 1, "hang"]
    received = []
    snoo.start_subscribe(make_device(), received.append)

    await wait_for(lambda: len(received) == 2)
    assert len(FakeClient.instances) >= 2
    await snoo.disconnect()


@pytest.mark.asyncio
async def test_client_map_reflects_connection_state(snoo):
    """send_command must not see a dead client; the map is cleared on drop and refilled on reconnect."""
    FakeClient.script = [0, "hang"]
    snoo.start_subscribe(make_device(), lambda data: None)

    await wait_for(lambda: len(FakeClient.instances) == 2)
    await wait_for(lambda: snoo._client_map.get("123") is FakeClient.instances[1])
    await snoo.disconnect()
    assert "123" not in snoo._client_map


@pytest.mark.asyncio
async def test_cancel_stops_reconnecting(snoo):
    """Cancelling the task (disconnect / token refresh) ends the loop; no further connects."""
    FakeClient.script = ["connect_error", "connect_error", "connect_error"]
    snoo.start_subscribe(make_device(), lambda data: None)
    await wait_for(lambda: len(FakeClient.instances) >= 1)
    await snoo.disconnect()
    count = len(FakeClient.instances)
    await asyncio.sleep(0.1)
    assert len(FakeClient.instances) == count
    assert snoo._mqtt_tasks == {}


@pytest.mark.asyncio
async def test_each_attempt_uses_current_token(snoo):
    """A token refreshed between attempts is used by the next connection."""
    FakeClient.script = ["connect_error", "hang"]
    snoo.start_subscribe(make_device(), lambda data: None)
    await wait_for(lambda: len(FakeClient.instances) == 1)
    snoo.tokens = AuthorizationInfo(snoo="snoo-token", aws_access="a", aws_id="new-id-token", aws_refresh="r")
    await wait_for(lambda: len(FakeClient.instances) == 2)
    assert FakeClient.instances[1].kwargs["websocket_headers"] == {"token": "new-id-token"}
    await snoo.disconnect()
