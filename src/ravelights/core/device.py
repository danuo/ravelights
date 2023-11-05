import logging
from typing import TYPE_CHECKING, Any

from ravelights.core.custom_typing import ArrayFloat, ArrayUInt8
from ravelights.core.instructionhandler import InstructionHandler
from ravelights.core.pixelmatrix import PixelMatrix
from ravelights.core.rendermodule import RenderModule
from ravelights.core.settings import Settings
from ravelights.core.timehandler import TimeHandler
from ravelights.interface.color_remap import ColorProfiles, ColorProfilesFunctions

if TYPE_CHECKING:
    from ravelights.core.ravelights_app import RaveLightsApp


logger = logging.getLogger(__name__)


class Device:
    def __init__(
        self,
        root: "RaveLightsApp",
        device_id: int,
        n_leds: int,
        n_lights: int,
        color_profile: ColorProfiles,
    ):
        self.root = root
        self.device_id: int = device_id
        self.n_leds: int = n_leds
        self.n_lights: int = n_lights
        self.color_profile: ColorProfiles = color_profile
        self.is_prim: bool = True if device_id == 0 else False
        self.settings: "Settings" = self.root.settings
        self.timehandler: "TimeHandler" = self.settings.timehandler
        self.pixelmatrix = PixelMatrix(n_leds=n_leds, n_lights=n_lights, is_prim=self.is_prim)
        self.rendermodule = RenderModule(root=root, device=self)
        self.instructionhandler = InstructionHandler(
            pixelmatrix=self.pixelmatrix,
            settings=self.settings,
            timehandler=self.timehandler,
            rendermodule=self.rendermodule,
        )

        self.device_manual_timeline_level: int = 4  # 0: blackout, 1: level1, ... 4: undefined
        self.device_triggerskip: int = 0  # Will select max(device_triggerskip, global_triggerskip)
        self.device_frameskip: int = 1  # must be 1 or higher. Will select max(device_frameskip, global_frameskip)
        self.device_brightness: float = 1.0  # will select min(device_brightness, global_brightness)

    def render(self):
        self.rendermodule.render()

    def get_matrix_processed_float(self) -> ArrayFloat:
        matrix_float = self.pixelmatrix.get_matrix_float()
        brightness = min(self.settings.global_brightness, self.device_brightness)
        color_map_function = ColorProfilesFunctions[self.color_profile]
        return color_map_function(matrix_float * brightness)

    def get_matrix_int(self) -> ArrayUInt8:
        return self.pixelmatrix.get_matrix_int()

    def get_device_objects(self) -> dict[str, Settings | TimeHandler | PixelMatrix]:
        return dict(settings=self.settings, pixelmatrix=self.pixelmatrix)

    def update_from_dict(self, update_dict: dict[str, Any]):
        assert isinstance(update_dict, dict)
        for key, value in update_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                logger.warning(f"key {key} does not exist in settings")
        self.root.refresh_ui(sse_event="devices")
