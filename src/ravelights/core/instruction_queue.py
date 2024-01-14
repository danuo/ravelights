from typing import TYPE_CHECKING

from ravelights.core.instruction import Instruction

if TYPE_CHECKING:
    from ravelights import RaveLightsApp


class InstructionQueue:
    def __init__(self, root: "RaveLightsApp"):
        self.root = root
        self.settings = self.root.settings
        self.timehandler = self.root.timehandler
        self._instruction_queue: list[list[Instruction]]
        self.just_initialized: bool
        self.clear()

    def clear(self):
        self._instruction_queue = [[] for _ in range(self.timehandler.queue_length)]
        self.just_initialized = True

    def add_instruction(self, instruction: Instruction, n_quarter: int):
        """will add the instruction into the instruction queue at position n_quarter"""
        self._instruction_queue[n_quarter].append(instruction)

    def get_instructions(self) -> list[Instruction]:
        """will return all instructions that have not been executed"""
        if self.just_initialized is True:
            self.just_initialized = False
            return self._get_instructions_till(self.timehandler.n_quarters_long)
        elif self.timehandler.beat_state.is_quarter:
            return self._instruction_queue[self.timehandler.n_quarters_long]
        return []

    def _get_instructions_till(self, till_n_quarters: int) -> list[Instruction]:
        """will return all instructions from timerange [0 to till_n_quarters]"""
        out: list[Instruction] = []
        for i in range(till_n_quarters + 1):
            out += self._instruction_queue[i]
        return out
