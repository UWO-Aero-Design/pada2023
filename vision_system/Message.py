from dataclasses import dataclass
from numpy import ndarray

# https://mavlink.io/en/messages/common.html#GLOBAL_POSITION_INT
# converted to standard units
@dataclass(frozen=True)
class PositionMessage():
    time_boot_ms: float # seconds
    lat: float          # decimal degrees
    lon: float          # decimal degress
    alt: float          # metres
    relative_alt: float # metres
    vx: float           # m/s
    vy: float           # m/s
    vz: float           # m/s
    hdg: int            # degrees

# https://mavlink.io/en/messages/common.html#ATTITUDE
# converted to standard units
@dataclass(frozen=True)
class AttitudeMessage():
    time_boot_ms: float # seconds
    roll: float         # degrees
    pitch: float        # degress
    yaw: float          # degrees
    rollspeed: float    # degrees/s
    pitchspeed: float   # degrees/s
    yawspeed: float     # degrees/s

@dataclass(frozen=True)
class VideoMessage():
    img: ndarray

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
