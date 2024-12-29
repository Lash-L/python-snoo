"""Connect to pubnub."""

# Taken from https://github.com/bdraco/yalexs/blob/main/yalexs/pubnub_async.py
import asyncio
import logging
import secrets
from functools import partial
from typing import Callable

from pubnub.callbacks import SubscribeCallback
from pubnub.enums import PNReconnectionPolicy, PNStatusCategory
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.pubsub import PNMessageResult
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub_asyncio import PubNubAsyncio

from .containers import SnooData

_LOGGER = logging.getLogger(__name__)
logging.basicConfig()

_LOGGER.setLevel(logging.DEBUG)


SHOULD_RECONNECT_CATEGORIES = {
    PNStatusCategory.PNUnknownCategory,
    PNStatusCategory.PNUnexpectedDisconnectCategory,
    PNStatusCategory.PNNetworkIssuesCategory,
    PNStatusCategory.PNTimeoutCategory,
}


class SnooPubNub(SubscribeCallback):
    def __init__(self, pubnub: PubNubAsyncio, device_id: str) -> None:
        """Initialize the SnooPubNub."""
        super().__init__()
        self.pubnub = pubnub
        self.device_id = device_id
        self._subscriptions: set[Callable[[SnooData], None]] = set()  # correct type hint
        self.connected = False
        self.task: asyncio.Task | None = None

    def update_token(self, token: str):
        self.pubnub.config.auth_key = token

    def presence(self, pubnub: PubNubAsyncio, presence):
        _LOGGER.debug("Received new presence: %s", presence)

    def status(self, pubnub: PubNubAsyncio, status: PNStatus) -> None:
        if not pubnub:
            self.connected = False
            return

        _LOGGER.debug(
            "Received new status: category=%s error_data=%s error=%s status_code=%s operation=%s",
            status.category,
            status.error_data,
            status.error,
            status.status_code,
            status.operation,
        )

        if status.category in SHOULD_RECONNECT_CATEGORIES:
            self.connected = False
            if self.task:
                self.task.cancel()  # cancel the task if it exists.
                self.task = None
            asyncio.create_task(self.run())  # restart the task
        elif status.category == PNStatusCategory.PNReconnectedCategory:
            self.connected = True

        elif status.category == PNStatusCategory.PNConnectedCategory:
            self.connected = True

    def message(self, pubnub: PubNubAsyncio, message: PNMessageResult) -> None:
        # Handle new messages
        _LOGGER.debug(
            "Received new messages on channel %s for device_id: %s with timetoken: %s: %s",
            message.channel,
            self.device_id,
            message.timetoken,
            message.message,
        )
        if message.channel.split(".")[0] == "ActivityState":
            if "system_state" in message.message:
                for callback in self._subscriptions:
                    data = SnooData.from_dict(message.message)
                    _LOGGER.debug(data)
                    callback(SnooData.from_dict(message.message))

    def subscribe(self, update_callback: Callable[[SnooData], None]) -> Callable[[], None]:
        """Add an callback subscriber.

        Returns a callable that can be used to unsubscribe.
        """
        self._subscriptions.add(update_callback)
        return partial(self._unsubscribe, update_callback)

    def _unsubscribe(self, update_callback: Callable[[SnooData], None]) -> None:
        self._subscriptions.remove(update_callback)

    async def run(self) -> None:
        """Run the pubnub loop."""
        if self.task:  # prevent multiple tasks from running
            return
        pnconfig = PNConfiguration()
        pnconfig.subscribe_key = "sub-c-97bade2a-483d-11e6-8b3b-02ee2ddab7fe"
        pnconfig.publish_key = "pub-c-699074b0-7664-4be2-abf8-dcbb9b6cd2bf"
        pnconfig.user_id = secrets.token_urlsafe(16)
        pnconfig.auth_key = self.pubnub.config.auth_key
        pnconfig.reconnect_policy = PNReconnectionPolicy.EXPONENTIAL
        self.pubnub.pnconfig = pnconfig
        self.pubnub.add_listener(self)
        self.pubnub.subscribe().channels(
            [f"ActivityState.{self.device_id}", f"ControlCommand.{self.device_id}"]
        ).execute()
