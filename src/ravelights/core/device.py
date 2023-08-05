from typing import TYPE_CHECKING

from ravelights.core.instructionhandler import InstructionHandler
from ravelights.core.pixelmatrix import PixelMatrix
from ravelights.core.rendermodule import RenderModule
from ravelights.core.settings import Settings
from ravelights.core.timehandler import TimeHandler

if TYPE_CHECKING:
    from ravelights.core.ravelights_app import RaveLightsApp


class Device:
    def __init__(self, root: "RaveLightsApp", device_id: int, n_leds: int, n_lights: int, is_prim: bool = False):
        self.root = root
        self.device_id = device_id
        self.settings: "Settings" = self.root.settings
        self.timehandler: "TimeHandler" = self.settings.timehandler
        self.pixelmatrix = PixelMatrix(n_leds=n_leds, n_lights=n_lights, is_prim=is_prim)
        self.rendermodule = RenderModule(root=root, device=self)
        self.instructionhandler = InstructionHandler(
            pixelmatrix=self.pixelmatrix,
            settings=self.settings,
            timehandler=self.timehandler,
            rendermodule=self.rendermodule,
            prim=is_prim,
        )

    def render(self):
        self.rendermodule.render()

    def get_device_objects(self) -> dict[str, Settings | TimeHandler | PixelMatrix]:
        return dict(settings=self.settings, pixelmatrix=self.pixelmatrix)
