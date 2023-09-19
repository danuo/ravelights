import logging
from typing import TYPE_CHECKING, Any

from ravelights.core.instructionhandler import InstructionHandler
from ravelights.core.pixelmatrix import PixelMatrix
from ravelights.core.rendermodule import RenderModule
from ravelights.core.settings import Settings
from ravelights.core.timehandler import TimeHandler

if TYPE_CHECKING:
    from ravelights.core.ravelights_app import RaveLightsApp


logger = logging.getLogger(__name__)


class Device:
    def __init__(self, root: "RaveLightsApp", device_id: int, n_leds: int, n_lights: int, is_prim: bool = False):
        self.root = root
        self.device_id: int = device_id
        self.n_leds: int = n_leds
        self.n_lights: int = n_lights
        self.is_prim: bool = is_prim
        self.settings: "Settings" = self.root.settings
        self.timehandler: "TimeHandler" = self.settings.timehandler
        self.pixelmatrix = PixelMatrix(n_leds=n_leds, n_lights=n_lights, is_prim=is_prim)
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

    def get_device_objects(self) -> dict[str, Settings | TimeHandler | PixelMatrix]:
        return dict(settings=self.settings, pixelmatrix=self.pixelmatrix)

    def update_from_dict(self, update_dict: dict[str, Any]):
        assert isinstance(update_dict, dict)
        for key, value in update_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                logger.warning(f"key {key} does not exist in settings")
