from typing import TYPE_CHECKING, Any, Optional

import numpy as np
from loguru import logger
from ravelights.core.custom_typing import ArrayFloat, ArrayUInt8
from ravelights.core.instruction_handler import InstructionHandler
from ravelights.core.pixel_matrix import PixelMatrix
from ravelights.core.render_module import RenderModule
from ravelights.core.settings import Settings
from ravelights.core.time_handler import TimeHandler
from ravelights.interface.color_remap import ColorProfiles, ColorProfilesFunctions

if TYPE_CHECKING:
    from ravelights.core.ravelights_app import RaveLightsApp


class Device:
    def __init__(
        self,
        root: "RaveLightsApp",
        device_index: int,
        n_leds: int,
        n_lights: int,
        color_profile: ColorProfiles,
        linked_to: Optional[int] = None,
    ):
        self.root = root
        self.device_index: int = device_index
        self.n_leds: int = n_leds
        self.n_lights: int = n_lights
        self.color_profile: ColorProfiles = color_profile
        self.is_prim: bool = True if device_index == 0 else False

        self.settings: "Settings" = self.root.settings
        self.timehandler: "TimeHandler" = self.root.time_handler
        self.pixelmatrix: PixelMatrix = PixelMatrix(n_leds=n_leds, n_lights=n_lights, is_prim=self.is_prim)
        self.rendermodule: RenderModule = RenderModule(root=root, device=self)
        self.instructionhandler = InstructionHandler(
            root=self.root,
            pixelmatrix=self.pixelmatrix,
            rendermodule=self.rendermodule,
        )

        if isinstance(linked_to, int):
            assert 0 <= linked_to < self.device_index
        self.linked_to: Optional[int] = linked_to

        self.device_triggerskip: int = 0  # Will select max(device_triggerskip, global_triggerskip)
        self.device_frameskip: int = 1  # must be 1 or higher. Will select max(device_frameskip, global_frameskip)
        self.device_brightness: float = 1.0  # will select min(device_brightness, global_brightness)

        self.device_manual_timeline_level: Optional[int] = None  # 0: blackout, 1: level1, ... None: undefined
        self.device_automatic_timeline_level: int = 0
        self.refresh_generators_from_timeline: bool = True

    def render(self):
        self.rendermodule.render()

    def get_matrix_float(self) -> ArrayFloat:
        return self.pixelmatrix.get_matrix_float()

    def get_matrix_processed_int(self) -> ArrayUInt8:
        matrix_float = self.pixelmatrix.get_matrix_float()
        brightness = min(self.settings.global_brightness, self.device_brightness)
        color_map_function = ColorProfilesFunctions[self.color_profile]
        matrix_processed_float = color_map_function(matrix_float * brightness)
        assert np.max(matrix_processed_float <= 255)
        return (matrix_processed_float * 255).astype(np.uint8)

    def get_matrix_int(self) -> ArrayUInt8:
        return self.pixelmatrix.get_matrix_int()

    def update_from_dict(self, update_dict: dict[str, Any]):
        assert isinstance(update_dict, dict)
        for key, value in update_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                logger.warning(f"key {key} does not exist in settings")
        self.root.refresh_ui(sse_event="devices")

    def get_effective_timeline_level(self) -> int:
        """
        return manual level or level from timeline, accoridng to setting
        """
        if isinstance(self.device_manual_timeline_level, int):
            # manual timeline level is defined on device level
            return self.device_manual_timeline_level

        if isinstance(self.settings.global_manual_timeline_level, int):
            # manual timeline level is defined on global level
            return self.settings.global_manual_timeline_level

        # level is chosen by global timeline
        return self.device_automatic_timeline_level
