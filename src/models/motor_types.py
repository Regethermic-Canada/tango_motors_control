from dataclasses import dataclass
from enum import Enum


class MotorAction(Enum):
    STARTED = "started"
    STOPPED = "stopped"
    START_FAILED_NO_MOTORS = "start_failed_no_motors"
    START_FAILED = "start_failed"
    STOP_FAILED = "stop_failed"


@dataclass(frozen=True)
class MotorActionResult:
    action: MotorAction
    error: str = ""
