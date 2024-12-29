class InvalidSnooAuth(Exception):
    """An exception when the user gave the wrong login info."""


class SnooAuthException(Exception):
    """All other authentication exceptions"""


class SnooDeviceError(Exception):
    """Issue getting the device"""
