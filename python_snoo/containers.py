import dataclasses
from enum import StrEnum

from mashumaro.mixins.json import DataClassJSONMixin


class SnooStates(StrEnum):
    BASELINE = "BASELINE"
    LEVEL_1 = "LEVEL1"
    LEVEL_2 = "LEVEL2"
    LEVEL_3 = "LEVEL3"
    LEVEL_4 = "LEVEL4"
    STOP = "ONLINE"
    PRETIMEOUT = "PRETIMEOUT"
    TIMEOUT = "TIMEOUT"


@dataclasses.dataclass
class AuthorizationInfo:
    snoo: str
    aws_access: str
    aws_id: str
    aws_refresh: str


@dataclasses.dataclass
class SnooDevice(DataClassJSONMixin):
    serialNumber: str
    deviceType: int
    firmwareVersion: str
    babyIds: list[str]
    name: str
    presence: dict
    presenceIoT: dict
    awsIoT: dict
    lastSSID: dict
    provisionedAt: str


@dataclasses.dataclass
class SnooStateMachine(DataClassJSONMixin):
    up_transition: str
    since_session_start_ms: int
    sticky_white_noise: str
    weaning: str
    time_left: int
    session_id: str
    state: SnooStates
    is_active_session: bool
    down_transition: str
    hold: str
    audio: str


@dataclasses.dataclass
class SnooData(DataClassJSONMixin):
    left_safety_clip: int
    rx_signal: dict
    right_safety_clip: int
    sw_version: str
    event_time_ms: int
    state_machine: SnooStateMachine
    system_state: str
    event: str
