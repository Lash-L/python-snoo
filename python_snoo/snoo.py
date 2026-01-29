import asyncio
import json
import logging
import secrets
import ssl
import uuid
from datetime import datetime as dt
from typing import Callable

import aiohttp
import aiomqtt
from pubnub.enums import PNReconnectionPolicy
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub_asyncio import PubNubAsyncio

from .containers import AuthorizationInfo, BabyData, SnooData, SnooDevice, SnooNoiseTimeoutLevels, SnooStates
from .exceptions import InvalidSnooAuth, SnooAuthException, SnooBabyError, SnooCommandException, SnooDeviceError
from .pubnub_async import SnooPubNub

_LOGGER = logging.getLogger(__name__)


class Snoo:
    def __init__(self, email: str, password: str, clientsession: aiohttp.ClientSession):
        self.email = email
        self.password = password
        self.session = clientsession
        self.aws_auth_url = "https://cognito-idp.us-east-1.amazonaws.com/"
        self.snoo_auth_url = "https://api-us-east-1-prod.happiestbaby.com/us/me/v10/pubnub/authorize"
        self.snoo_devices_url = "https://api-us-east-1-prod.happiestbaby.com/hds/me/v11/devices"
        self.snoo_data_url = "https://happiestbaby.pubnubapi.com"
        self.snoo_baby_url = "https://api-us-east-1-prod.happiestbaby.com/us/me/v10/babies"
        self.aws_auth_hdr = {
            "x-amz-target": "AWSCognitoIdentityProviderService.InitiateAuth",
            "accept-language": "US",
            "content-type": "application/x-amz-json-1.1",
            "accept-encoding": "gzip",
            "user-agent": "okhttp/4.12.0",
            "accept": "application/json",
        }
        self.aws_refresh_hdr = {
            "accept": "*/*",
            "content-type": "application/x-amz-json-1.1",
            "x-amz-target": "AWSCognitoIdentityProviderService.InitiateAuth",
            "accept-encoding": "br;q=1.0, gzip;q=0.9, deflate;q=0.8",
            "user-agent": "Happiest Baby/2.1.6 (com.happiestbaby.hbapp; build:88; iOS 18.3.0) Alamofire/5.9.1",
            "accept-language": "en-US;q=1.0",
            "content-length": "1895",
        }
        self.snoo_auth_hdr = {
            "accept-language": "US",
            "content-type": "application/json; charset=UTF-8",
            "accept-encoding": "gzip",
            "user-agent": "okhttp/4.12.0",
            "accept": "application/json",
        }

        self.aws_auth_data = {
            "AuthParameters": {
                "PASSWORD": self.password,
                "USERNAME": self.email,
            },
            "AuthFlow": "USER_PASSWORD_AUTH",
            "ClientId": "6kqofhc8hm394ielqdkvli0oea",
        }
        self.snoo_auth_data = {
            "advertiserId": "",
            "appVersion": "1.8.7",
            "device": "panther",
            "deviceHasGSM": True,
            "locale": "en",
            "os": "Android",
            "osVersion": "14",
            "platform": "Android",
            "timeZone": "America/New_York",
            "userCountry": "US",
            "vendorId": "eyqurgwYQSqmnExnzyiLO5",
        }

        self.aws_auth_data = json.dumps(self.aws_auth_data)
        self.snoo_auth_data = json.dumps(self.snoo_auth_data)
        self.tokens: AuthorizationInfo | None = None
        self.pubnub = None
        self.subscription_functions = {}
        self.data_map = {}
        self.pubnub_instances: dict[str, SnooPubNub] = {}
        self.reauth_task: asyncio.Task | None = None
        self._client_map: dict[str, aiomqtt.Client] = {}
        self._mqtt_tasks: dict[str, asyncio.Task] = {}
        self._mqtt_callbacks: dict[str, tuple[SnooDevice, Callable]] = {}
        self._client_cond = asyncio.Condition()

    async def refresh_tokens(self) -> int:
        """Refreshes AWS Cognito tokens and returns the new expiration time in seconds."""
        _LOGGER.info("AWS Cognito tokens expired, refreshing...")
        if not self.tokens or not self.tokens.aws_refresh:
            _LOGGER.error("No refresh token available. A full re-authentication is required.")
            raise SnooAuthException("Missing refresh token.")

        data = {
            "AuthParameters": {"REFRESH_TOKEN": self.tokens.aws_refresh},
            "AuthFlow": "REFRESH_TOKEN_AUTH",
            "ClientId": "6kqofhc8hm394ielqdkvli0oea",
        }
        r = await self.session.post(self.aws_auth_url, json=data, headers=self.aws_auth_hdr)
        resp = await r.json(content_type=None)

        if r.status >= 400:
            _LOGGER.error(f"Failed to refresh tokens. Status: {r.status}, Response: {resp}")
            raise InvalidSnooAuth(f"Token refresh failed: {resp.get('message', 'Unknown error')}")

        result = resp.get("AuthenticationResult")
        if not result:
            _LOGGER.error(f"Invalid response during token refresh: {resp}")
            raise SnooAuthException("Token refresh response missing 'AuthenticationResult'.")

        # Update tokens with the new ones from the response
        self.tokens = AuthorizationInfo(
            snoo=self.tokens.snoo,
            aws_access=result["AccessToken"],
            aws_id=result["IdToken"],
            aws_refresh=result.get("RefreshToken", self.tokens.aws_refresh),
        )
        _LOGGER.info("✅ Successfully refreshed AWS Cognito tokens.")
        return result.get("ExpiresIn", 3600)

    def check_tokens(self):
        if self.tokens is None:
            raise Exception("You need to authenticate before you continue")

    def generate_snoo_auth_headers(self, amz_token: str) -> dict[str, str]:
        hdrs = self.snoo_auth_hdr.copy()
        hdrs["authorization"] = f"Bearer {amz_token}"
        return hdrs

    def generate_snoo_data_url(self, device_id: str | float, snoo_token: str) -> str:
        if isinstance(device_id, float):
            device_id = str(int(device_id))
        req_uuid = uuid.uuid1()
        dev_uuid = uuid.uuid1()
        app_dev_id_len = 24
        n = app_dev_id_len * 3 // 4
        app_dev_id = secrets.token_urlsafe(n)
        url = f"https://happiestbaby.pubnubapi.com/v2/history/sub-key/sub-c-97bade2a-483d-11e6-8b3b-02ee2ddab7fe/channel/ActivityState.{device_id}?pnsdk=PubNub-Kotlin%2F7.4.0&l_pub=0.064&auth={snoo_token}&requestid={req_uuid}&include_token=true&count=1&include_meta=false&reverse=false&uuid=android_{app_dev_id}_{dev_uuid}"
        return url

    def generate_id(self) -> str:
        app_dev_id_len = 24
        n = app_dev_id_len * 3 // 4
        app_dev_id = secrets.token_urlsafe(n)
        return app_dev_id

    async def subscribe(self, device: SnooDevice, function: Callable):
        pnconfig = PNConfiguration()
        pnconfig.subscribe_key = "sub-c-97bade2a-483d-11e6-8b3b-02ee2ddab7fe"
        pnconfig.publish_key = "pub-c-699074b0-7664-4be2-abf8-dcbb9b6cd2bf"
        pnconfig.user_id = secrets.token_urlsafe(16)
        pnconfig.auth_key = self.tokens.snoo
        pnconfig.reconnect_policy = PNReconnectionPolicy.EXPONENTIAL
        self.pubnub = PubNubAsyncio(pnconfig)
        device_id = device.serialNumber

        if device_id not in self.pubnub_instances:
            self.pubnub_instances[device_id] = SnooPubNub(self.pubnub, device_id)
        pubnub_instance = self.pubnub_instances[device_id]
        unsub = pubnub_instance.subscribe(function)
        asyncio.create_task(pubnub_instance.run())
        return unsub

    async def disconnect(self):
        for pubnub_instance in self.pubnub_instances.values():
            if pubnub_instance.task:
                pubnub_instance.task.cancel()
                try:
                    await pubnub_instance.task
                except asyncio.CancelledError:
                    pass
        self.pubnub_instances = {}

        for task in self._mqtt_tasks.values():
            task.cancel()
        await asyncio.gather(*self._mqtt_tasks.values(), return_exceptions=True)
        self._mqtt_tasks = {}
        self._mqtt_callbacks = {}

        if self.reauth_task:
            self.reauth_task.cancel()
            self.reauth_task = None

    def publish_callback(self, result, status):
        if status.is_error():
            _LOGGER.warning(f"Message failed with {status.status_code}, {status.error_data.__dict__}")

    async def send_command(self, command: str, device: SnooDevice, **kwargs):
        ts = int(dt.now().timestamp() * 10_000_000)
        try:
            # Acquire the condition lock
            async with self._client_cond:
                try:
                    # Wait up to 30 seconds for the client to connect.
                    await asyncio.wait_for(
                        self._client_cond.wait_for(lambda: device.serialNumber in self._client_map), timeout=30.0
                    )
                except asyncio.TimeoutError:
                    _LOGGER.error(f"Timed out waiting for client for device {device.serialNumber} to connect.")
                    raise SnooCommandException(f"Client for device {device.serialNumber} is not connected.") from None

                # Once wait_for returns, we know the client exists and we hold the lock.
                await self._client_map[device.serialNumber].publish(
                    topic=f"{device.awsIoT.thingName}/state_machine/control",
                    payload=json.dumps({"ts": ts, "command": command, **kwargs}),
                )
        except Exception as e:
            raise SnooCommandException from e

    async def start_snoo(self, device: SnooDevice):
        await self.send_command("start_snoo", device)

    async def stop_snoo(self, device: SnooDevice):
        await self.send_command("go_to_state", device, **{"state": "ONLINE", "hold": "off"})

    async def set_level(self, device: SnooDevice, level: SnooStates, hold: bool = False):
        if hold:
            hold = "on"
        else:
            hold = "off"

        await self.send_command("go_to_state", device, **{"state": level.value, "hold": hold})

    async def set_sticky_white_noise(
        self,
        device: SnooDevice,
        on: bool,
        timeout_value: SnooNoiseTimeoutLevels | int = SnooNoiseTimeoutLevels._15_minutes,
    ):
        """Enable or disable sticky white noise for a device.

        Args:
            device: The SnooDevice to control.
            on: True to turn sticky white noise on, False to turn it off.
            timeout_value: How long the white noise should remain on before timing out.
                Must be a member of the SnooNoiseTimeoutLevels enum. The default is
                SnooNoiseTimeoutLevels._15_minutes.
        """
        await self.send_command(
            "set_sticky_white_noise",
            device,
            **{"state": "on" if on else "off", "timeout_min": timeout_value},
        )

    async def get_status(self, device: SnooDevice):
        await self.send_command("send_status", device)

    async def auth_amazon(self) -> dict:
        r = await self.session.post(self.aws_auth_url, data=self.aws_auth_data, headers=self.aws_auth_hdr)
        resp = await r.json(content_type=None)
        if "__type" in resp and resp["__type"] == "NotAuthorizedException":
            raise InvalidSnooAuth()
        result = resp["AuthenticationResult"]
        return result

    async def auth_snoo(self, id_token: str) -> dict:
        hdrs = self.generate_snoo_auth_headers(id_token)
        r = await self.session.post(self.snoo_auth_url, data=self.snoo_auth_data, headers=hdrs)
        return await r.json()

    async def authorize(self) -> AuthorizationInfo:
        try:
            amz = await self.auth_amazon()
            access = amz["AccessToken"]
            _id = amz["IdToken"]
            ref = amz["RefreshToken"]
            expires_in = amz["ExpiresIn"]

            snoo_token_data = await self.auth_snoo(_id)
            snoo_token = snoo_token_data["snoo"]["token"]

            self.tokens = AuthorizationInfo(snoo=snoo_token, aws_access=access, aws_id=_id, aws_refresh=ref)

            if self.reauth_task:
                self.reauth_task.cancel()

            # Schedule reauthorization with a 5-minute buffer before expiry
            reauth_delay = max(expires_in - 300, 0)
            self.reauth_task = asyncio.create_task(self.schedule_reauthorization(reauth_delay))
            _LOGGER.info(f"Authorization successful. Next token refresh scheduled in {reauth_delay} seconds.")

        except InvalidSnooAuth as ex:
            raise ex
        except Exception as ex:
            raise SnooAuthException from ex
        return self.tokens

    async def schedule_reauthorization(self, expiry_seconds: float):
        try:
            await asyncio.sleep(expiry_seconds)
            _LOGGER.info("Executing scheduled token refresh...")

            new_expires_in = await self.refresh_tokens()

            _LOGGER.info("Restarting MQTT subscriptions with new token...")
            # Cancel all existing MQTT tasks
            for task in self._mqtt_tasks.values():
                task.cancel()
            await asyncio.gather(*self._mqtt_tasks.values(), return_exceptions=True)
            self._mqtt_tasks.clear()

            # The `finally` block in `subscribe_mqtt` should clear the `_client_map`
            # as connections close.

            # Re-subscribe for all previously active subscriptions
            for device_sn, (device, function) in self._mqtt_callbacks.items():
                _LOGGER.info(f"Re-establishing MQTT subscription for device {device_sn}")
                self.start_subscribe(device, function)

            _LOGGER.info("✅ MQTT subscriptions restarted successfully.")

            # Schedule the *next* reauthorization
            reauth_delay = max(new_expires_in - 300, 0)
            self.reauth_task = asyncio.create_task(self.schedule_reauthorization(reauth_delay))
            _LOGGER.info(f"Next token refresh scheduled in {reauth_delay} seconds.")

        except asyncio.CancelledError:
            _LOGGER.info("Reauthorization task was cancelled.")
        except Exception:
            _LOGGER.exception("An unexpected error occurred during reauthorization.")

    async def get_devices(self) -> list[SnooDevice]:
        hdrs = self.generate_snoo_auth_headers(self.tokens.aws_id)
        try:
            r = await self.session.get(self.snoo_devices_url, headers=hdrs)
            resp = await r.json()
        except Exception as ex:
            raise SnooDeviceError from ex
        devs = [SnooDevice.from_dict(dev) for dev in resp["snoo"]]
        return devs

    async def get_babies(self) -> list[BabyData]:
        hdrs = self.generate_snoo_auth_headers(self.tokens.aws_id)
        try:
            r = await self.session.get(self.snoo_baby_url, headers=hdrs)
            resp = await r.json()
        except Exception as ex:
            raise SnooBabyError from ex
        babies = [BabyData.from_dict(baby) for baby in resp]
        return babies

    def start_subscribe(self, device: SnooDevice, function: Callable):
        if device.serialNumber in self._mqtt_tasks and not self._mqtt_tasks[device.serialNumber].done():
            _LOGGER.warning(f"Subscription task for device {device.serialNumber} is already running.")
            return

        # Store the device and callback function for re-subscription after re-auth
        self._mqtt_callbacks[device.serialNumber] = (device, function)

        self._mqtt_tasks[device.serialNumber] = asyncio.create_task(self.subscribe_mqtt(device, function))

    async def subscribe_mqtt(self, device: SnooDevice, function: Callable):
        host = device.awsIoT.clientEndpoint
        port = 443
        websocket_path = "/mqtt"
        token = self.tokens.aws_id
        headers = {"token": token}
        password = None
        client_id = f"HA_{uuid.uuid4()}"
        user_name = "?SDK=iOS&Version=2.40.1"

        logging.debug(f"Attempting to connect to wss://{host}:{port}{websocket_path}")

        # The default SSL context creation is a blocking I/O operation.
        # Run it in a separate thread to avoid blocking the Home Assistant event loop.
        ssl_context = await asyncio.to_thread(ssl.create_default_context)

        try:
            async with aiomqtt.Client(
                hostname=host,
                port=port,
                username=user_name,
                password=password,
                identifier=client_id,
                transport="websockets",
                websocket_path=websocket_path,
                websocket_headers=headers,
                tls_context=ssl_context,
                protocol=aiomqtt.ProtocolVersion.V31,
                timeout=10,
            ) as client:
                logging.info(f"✅ Successfully connected to MQTT broker for {device.serialNumber}!")

                # Acquire the lock, add the client to the map, and notify waiting tasks.
                async with self._client_cond:
                    self._client_map[device.serialNumber] = client
                    self._client_cond.notify_all()

                topic = f"{device.awsIoT.thingName}/state_machine/activity_state"
                await client.subscribe(topic)
                logging.info(f"Subscribed to topic: {topic}")

                async for message in client.messages:
                    logging.debug(f"Received message on topic '{message.topic}': {message.payload.decode()}")
                    function(SnooData.from_json(message.payload.decode()))

        except aiomqtt.MqttError as e:
            logging.error(f"MQTT connection for {device.serialNumber} failed: {e}")
        except Exception as e:
            logging.error(f"MQTT connection for {device.serialNumber} failed with an unexpected error: {e}")
        finally:
            # When the connection is lost, remove the client from the map.
            logging.info(f"MQTT connection closed for {device.serialNumber}.")
            async with self._client_cond:
                if device.serialNumber in self._client_map:
                    del self._client_map[device.serialNumber]
