import dataclasses
import datetime
from enum import IntEnum, StrEnum
from typing import Any, Union

from mashumaro.mixins.json import DataClassJSONMixin


class SnooLevels(StrEnum):
    baseline = "BASELINE"
    weaning_baseline = "WEANING_BASELINE"
    level1 = "LEVEL1"
    level2 = "LEVEL2"
    level3 = "LEVEL3"
    level4 = "LEVEL4"
    stop = "ONLINE"


class SnooNoiseTimeoutLevels(IntEnum):
    _5_minutes = 5
    _10_minutes = 10
    _15_minutes = 15
    _20_minutes = 20
    _25_minutes = 25
    _30_minutes = 30
    _35_minutes = 35
    _40_minutes = 40
    _45_minutes = 45
    _50_minutes = 50
    _55_minutes = 55
    _60_minutes = 60
    _65_minutes = 65
    _70_minutes = 70
    _75_minutes = 75
    _80_minutes = 80
    _85_minutes = 85
    _90_minutes = 90
    _95_minutes = 95
    _100_minutes = 100
    _105_minutes = 105
    _110_minutes = 110
    _115_minutes = 115
    _120_minutes = 120
    _125_minutes = 125
    _130_minutes = 130
    _135_minutes = 135
    _140_minutes = 140
    _145_minutes = 145
    _150_minutes = 150
    _155_minutes = 155
    _160_minutes = 160
    _165_minutes = 165
    _170_minutes = 170
    _175_minutes = 175
    _180_minutes = 180


class SnooStates(StrEnum):
    baseline = "BASELINE"
    level1 = "LEVEL1"
    level2 = "LEVEL2"
    level3 = "LEVEL3"
    level4 = "LEVEL4"
    stop = "ONLINE"
    pretimeout = "PRETIMEOUT"
    timeout = "TIMEOUT"
    suspended = "SUSPENDED"
    weaning_baseline = "WEANING_BASELINE"
    global_settings = "GLOBAL_SETTINGS"
    unrecoverable_suspended = "UNRECOVERABLE_SUSPENDED"
    unrecoverable_error = "UNRECOVERABLE_ERROR"
    none = "NONE"
    manual = "MANUAL"


class SnooEvents(StrEnum):
    TIMER = "timer"
    CRY = "cry"
    COMMAND = "command"
    SAFETY_CLIP = "safety_clip"
    LONG_ACTIVITY_PRESS = "long_activity_press"
    ACTIVITY = "activity"
    POWER = "power"
    STATUS_REQUESTED = "status_requested"
    STICKY_WHITE_NOISE_UPDATED = "sticky_white_noise_updated"
    CONFIG_CHANGE = "config_change"
    RESTART = "restart"


class DiaperTypes(StrEnum):
    """Diaper change types, matching what the Happiest Baby app uses"""

    WET = "pee"
    DIRTY = "poo"


@dataclasses.dataclass
class AuthorizationInfo:
    snoo: str
    aws_access: str
    aws_id: str
    aws_refresh: str


@dataclasses.dataclass
class AwsIOT:
    awsRegion: str
    clientEndpoint: str
    clientReady: bool
    thingName: str


@dataclasses.dataclass
class SnooDevice(DataClassJSONMixin):
    serialNumber: str
    firmwareVersion: str
    babyIds: list[str]
    name: str
    deviceType: int | None = None
    presence: dict | None = None
    presenceIoT: dict | None = None
    awsIoT: AwsIOT | None = None
    lastSSID: dict | None = None
    provisionedAt: str | None = None


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
    time_left_timestamp: datetime.datetime | None = None
    level: SnooLevels | None = None

    def __post_init__(self):
        if self.time_left != -1:
            self.time_left_timestamp = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
                seconds=self.time_left
            )
        else:
            self.time_left_timestamp = None
        if self.up_transition == "NONE" and self.down_transition == "NONE":
            self.level = SnooLevels.stop
        elif self.up_transition == SnooLevels.level1:
            self.level = SnooLevels.baseline
        elif self.up_transition == SnooLevels.level2:
            self.level = SnooLevels.level1
        elif self.up_transition == SnooLevels.level3:
            self.level = SnooLevels.level2
        elif self.up_transition == SnooLevels.level4:
            self.level = SnooLevels.level3
        elif self.down_transition == SnooLevels.level3:
            self.level = SnooLevels.level4


@dataclasses.dataclass
class SnooData(DataClassJSONMixin):
    left_safety_clip: int
    rx_signal: dict
    right_safety_clip: int
    sw_version: str
    event_time_ms: int
    state_machine: SnooStateMachine
    system_state: str
    event: SnooEvents


@dataclasses.dataclass
class BabySettings(DataClassJSONMixin):
    carRideMode: bool
    daytimeStart: int
    minimalLevel: str
    minimalLevelVolume: str
    motionLimiter: bool
    responsivenessLevel: str
    soothingLevelVolume: str
    weaning: bool


@dataclasses.dataclass
class BabyData(DataClassJSONMixin):
    _id: str
    babyName: str
    breathSettingHistory: list
    createdAt: str
    disabledLimiter: bool
    pictures: list
    settings: BabySettings
    sex: str
    preemie: Any | None = None  # Not sure what datatype this is yet & may not be supplied - boolean?
    birthDate: str | None = None
    expectedBirthDate: str | None = None
    startedUsingSnooAt: str | None = None
    updatedAt: str | None = None


@dataclasses.dataclass
class DiaperData(DataClassJSONMixin):
    """Data for diaper change activities"""

    types: list[DiaperTypes]

    def __post_init__(self):
        if not self.types:
            raise ValueError("DiaperData.types cannot be empty or None")

        self.types = [DiaperTypes(dt) for dt in self.types]


@dataclasses.dataclass
class BreastfeedingData(DataClassJSONMixin):
    lastUsedBreast: str
    totalDuration: int
    left: dict | None = None
    right: dict | None = None


@dataclasses.dataclass
class DiaperActivity(DataClassJSONMixin):
    id: str
    type: str
    startTime: str
    babyId: str
    userId: str
    data: DiaperData
    createdAt: str
    updatedAt: str
    note: str | None = None


@dataclasses.dataclass
class BreastfeedingActivity(DataClassJSONMixin):
    id: str
    type: str
    startTime: str
    endTime: str
    babyId: str
    userId: str
    data: BreastfeedingData
    createdAt: str
    updatedAt: str


Activity = Union[DiaperActivity, BreastfeedingActivity]
