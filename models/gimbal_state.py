from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class GimbalState:
    commanded_pan: float = 0.0
    commanded_tilt: float = 0.0
    actual_pan: Optional[float] = None
    actual_tilt: Optional[float] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def update_commanded(self, pan: float, tilt: float):
        self.commanded_pan = pan
        self.commanded_tilt = tilt
        self.timestamp = datetime.now()

    def update_actual(self, pan: float, tilt: float):
        self.actual_pan = pan
        self.actual_tilt = tilt
        self.timestamp = datetime.now()

    def get_error(self) -> tuple[Optional[float], Optional[float]]:
        if self.actual_pan is None or self.actual_tilt is None:
            return None, None
        return (
            self.commanded_pan - self.actual_pan,
            self.commanded_tilt - self.actual_tilt
        )
