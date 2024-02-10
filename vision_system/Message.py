from dataclasses import dataclass

@dataclass(frozen=True)
class TelemetryMessage():
    yaw: float
    pitch: float
    roll: float

@dataclass(frozen=True)
class ParamsMessage():
    area_threshold: int

@dataclass(frozen=True)
class PointMessage():
    colour: str
    x: int
    y: int
    width: int
    height: int
    lat: float
    lon: float
