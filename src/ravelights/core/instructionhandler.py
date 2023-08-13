from typing import cast

from ravelights.core.instruction import InstructionDevice
from ravelights.core.instructionqueue import InstructionQueue
from ravelights.core.pixelmatrix import PixelMatrix
from ravelights.core.rendermodule import RenderModule
from ravelights.core.settings import Settings
from ravelights.core.timehandler import TimeHandler


class InstructionHandler:
    def __init__(
        self,
        pixelmatrix: PixelMatrix,
        settings: Settings,
        timehandler: TimeHandler,
        rendermodule: RenderModule,
    ):
        self.pixelmatrix: PixelMatrix = pixelmatrix
        self.settings: Settings = settings
        self.timehandler: TimeHandler = timehandler
        self.rendermodule: RenderModule = rendermodule
        self.instruction_queue = InstructionQueue(settings=self.settings)

    def apply_instruction(self, instruction: InstructionDevice):
        """Apply_instruction() is called when new instruction is loaded"""

        # ─── APPLY GENERATORS ────────────────────────────────────────────
        self.rendermodule.device_timeline_level = instruction.level

    def load_and_apply_instructions(self):
        instructions_for_frame = cast(list[InstructionDevice], self.instruction_queue.get_instructions())
        for ins in instructions_for_frame:
            self.apply_instruction(ins)
