from ravelights.core.instruction import Instruction
from ravelights.core.settings import Settings


class InstructionQueue:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.length_quarters = settings.queue_length
        self._instruction_queue: list[list[Instruction]]
        self.just_initialized: bool
        self.clear()

    def clear(self):
        self._instruction_queue = [[] for _ in range(self.length_quarters)]
        self.just_initialized = True

    def add_instruction(self, instruction: Instruction, n_quarter: int):
        """will add the instruction into the instruction queue at position n_quarter"""
        self._instruction_queue[n_quarter].append(instruction)

    def get_instructions(self) -> list[Instruction]:
        """will return all instructions that have not been executed"""
        if self.just_initialized is True:
            self.just_initialized = False
            return self._get_instructions_till(self.settings.n_quarters_long)
        elif self.settings.beat_state.is_quarter:
            return self._instruction_queue[self.settings.n_quarters_long]
        return []

    def _get_instructions_till(self, till_n_quarters: int) -> list[Instruction]:
        """will return all instructions from timerange [0 to till_n_quarters]"""
        out: list[Instruction] = []
        for i in range(till_n_quarters + 1):
            out += self._instruction_queue[i]
        return out
