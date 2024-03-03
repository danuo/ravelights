from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DeviceSettings:
    linked_to: Optional[int]

    device_triggerskip: int = 0  # Will select max(device_triggerskip, global_triggerskip)
    device_frameskip: int = 1  # must be 1 or higher. Will select max(device_frameskip, global_frameskip)
    device_brightness: float = 1.0  # will select min(device_brightness, global_brightness)

    device_manual_timeline_level: Optional[int] = None  # 0: blackout, 1: level1, ... None: undefined

    refresh_from_timeline: bool = True
    use_autopilot: bool = True
    use_effect: dict[str, bool] = field(init=False)

    def __post_init__(self):
        self.use_effect = {"1": True, "2": True, "3": True}
