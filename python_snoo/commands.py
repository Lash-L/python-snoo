from enum import StrEnum


class SnooCommand(StrEnum):
    START_SNOO = "start_snoo"
    GO_TO_STATE = "go_to_state"
    SET_WEANING = "set_weaning"
    SET_STICKY_WHITE_NOISE = "set_sticky_white_noise"
    SEND_STATUS = "send_status"
    CUSTOM_GET_HISTORY = "custom_get_history"
