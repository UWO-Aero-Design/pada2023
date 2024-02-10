from dataclasses import dataclass, field
from enum import Enum, auto

@dataclass(frozen=True)
class TelemetryMessage():
    yaw: float
    pitch: float
    roll: float

@dataclass(frozen=True)
class ParamsMessage():
    area_threshold: int
