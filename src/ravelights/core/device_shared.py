from dataclasses import dataclass

from ravelights.interface.color_remap import ColorProfiles


@dataclass
class DeviceLightConfig:
    n_lights: int
    n_leds: int
    color_profile: ColorProfiles = ColorProfiles.LINEAR
