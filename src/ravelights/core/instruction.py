from typing import Optional


class Instruction:
    ...


class InstructionEffect(Instruction):
    # todo: set color
    # todo: set color_sec
    def __init__(
        self,
        effect_name: Optional[str] = None,
        effect_length_frames: Optional[int] = None,
    ):
        self.effect_name = effect_name
        self.effect_length_frames = effect_length_frames

    def __repr__(self):
        source = vars(self)
        output = {k: v for k, v in source.items() if v is not None}
        return str(output)


# todo: make this dataclass, do not use **parameters but meta instead, see:
# https://stackoverflow.com/a/55101438
class InstructionDevice(Instruction):
    def __init__(
        self,
        level: int,
        **kwargs: dict[str, None],
    ):
        self.level = level
        self.kwargs = kwargs

    def __repr__(self):
        source = vars(self)
        output = {k: v for k, v in source.items() if v is not None}
        return str(output)
