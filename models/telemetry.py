from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class TelemetryData:
    pan_position: Optional[float] = None
    tilt_position: Optional[float] = None
    pan_velocity: Optional[float] = None
    tilt_velocity: Optional[float] = None
    timestamp: datetime = None
    raw_data: bytes = b''

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    @classmethod
    def from_bytes(cls, data: bytes) -> 'TelemetryData':
        return cls(raw_data=data, timestamp=datetime.now())
