from typing import TYPE_CHECKING, cast

from ravelights.core.instruction import InstructionDevice
from ravelights.core.instruction_queue import InstructionQueue
from ravelights.core.pixel_matrix import PixelMatrix
from ravelights.core.render_module import RenderModule
from ravelights.core.settings import Settings
from ravelights.core.time_handler import TimeHandler

if TYPE_CHECKING:
    from ravelights import RaveLightsApp
    from ravelights.core.device import Device


class InstructionHandler:
    def __init__(
        self,
        device: "Device",
    ):
        self.device: "Device" = device
        self.pixelmatrix: PixelMatrix = self.device.pixelmatrix
        self.rendermodule: RenderModule = self.device.rendermodule
        self.root: "RaveLightsApp" = self.device.root
        self.settings: Settings = self.root.settings
        self.timehandler: TimeHandler = self.root.time_handler
        self.instruction_queue = InstructionQueue(root=self.root)

    def apply_instruction(self, instruction: InstructionDevice):
        """Apply_instruction() is called when new instruction is loaded"""

        # ─── APPLY GENERATORS ────────────────────────────────────────────
        self.device.device_automatic_timeline_level = instruction.level

    def load_and_apply_instructions(self):
        instructions_for_frame = cast(list[InstructionDevice], self.instruction_queue.get_instructions())
        for ins in instructions_for_frame:
            self.apply_instruction(ins)
