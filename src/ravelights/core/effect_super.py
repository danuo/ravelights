from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal, Optional

from loguru import logger
from ravelights.core.color_handler import Color
from ravelights.core.custom_typing import ArrayFloat, FramesPattern, FramesPatternBinary
from ravelights.core.pixel_matrix import PixelMatrix
from ravelights.core.time_handler import BeatState, BeatStatePattern

if TYPE_CHECKING:
    from ravelights.configs.components import Keyword
    from ravelights.core.device import Device
    from ravelights.core.ravelights_app import RaveLightsApp
    from ravelights.core.settings import Settings
    from ravelights.core.time_handler import TimeHandler


def get_frames_pattern_binary(frames_pattern: FramesPattern, multi: int = 1) -> FramesPatternBinary:
    """
    example input:
    frames_pattern = (4, (0,))
    multi = 2
    -> [True, True, False, False, False, False, False, False]
    """
    assert isinstance(multi, int)
    assert multi >= 1

    pattern_length = frames_pattern.length
    assert isinstance(pattern_length, int)
    assert pattern_length > 0

    out: list[bool] = []

    pattern_indices = frames_pattern.pattern_indices

    for index in range(pattern_length):
        if index in pattern_indices:
            out.extend([True] * multi)
        else:
            out.extend([False] * multi)

    return out


def get_quarters_pattern_binary(quarters_pattern: list[str], loop_length_beats: int, limit_loopquarters: int):
    """
    Turns quarters_pattern into a binary array. Each value represents a quarter
    loop_length_beats: loop length in beats
    quarters_pattern = ["0A", "0C", "1A", "2A"]
    loop_length_beats = 2
    -> [True, False, True, False, True, False, False, False]
    """

    loop_length_quarters = loop_length_beats * 4
    quarters_pattern_binary = [False] * loop_length_quarters

    for item in quarters_pattern:
        num = int(item[:-1])
        letter = item[-1]
        assert letter in "ABCD"
        letter_num = ord(letter) - 65  # A->0, B->1 etc.
        index = num * 4 + letter_num
        if index < limit_loopquarters:
            quarters_pattern_binary[index] = True
    return quarters_pattern_binary


@dataclass
class EffectWrapperState(ABC):
    multi: int
    mode: Literal["frames"]

    counter_frames: int

    @abstractmethod
    def is_active(self, beat_state: BeatState) -> bool:
        ...

    @abstractmethod
    def counting_before_check(self, beat_state: BeatState) -> None:
        """execute this once per frame after check_active"""
        ...

    @abstractmethod
    def counting_after_check(self, beat_state: BeatState) -> None:
        """execute this once per frame after check_active"""
        ...

    @abstractmethod
    def is_finished(self) -> bool:
        """execute this once per frame after check_active"""
        ...


@dataclass
class EffectWrapperStateFrames(EffectWrapperState):
    frames_pattern_binary: FramesPatternBinary
    limit_frames: Optional[int] = None

    def is_active(self, beat_state: BeatState) -> bool:
        index = self.counter_frames % len(self.frames_pattern_binary)
        if self.frames_pattern_binary[index]:
            return True
        return False

    def counting_before_check(self, beat_state: BeatState) -> None:
        pass

    def counting_after_check(self, beat_state: BeatState):
        self.counter_frames += 1

    def is_finished(self):
        """returns if effect is finished (ready for removal)"""

        if self.limit_frames is None:
            return False

        assert isinstance(self.limit_frames, int)
        if self.counter_frames >= self.limit_frames:
            return True

        return False


"""
@dataclass
class EffectWrapperStateQuarters(EffectWrapperState):
    timehandler: Any
    has_started: bool
    # wip

    def is_active(self, beat_state: BeatState) -> bool:
        # search first beat before start
        if not self.has_started:
            if self.timehandler.beat_state.is_beat:
                self.has_started = True
            else:
                return False

        # after start, effect is potentially active
        assert isinstance(self.limit_frames, int)
        if self.counter_frames < self.limit_frames:
            index = self.counter_frames % len(self.frames_pattern_binary)
            if self.frames_pattern_binary[index]:
                return True
        return False

    def counting_after_check(self, beat_state: BeatState):
        if self.has_started:
            self.counter_frames += 1
            if self.timehandler.beat_state.is_quarter:
                self.counter_quarters += 1
                counter_beats = self.counter_quarters // 4
                if counter_beats > 0 and counter_beats % self.loop_length_beats == 0:
                    self.counter_quarters_loop += 1
                    self.counter_quarters = 0
                    self.counter_frames = 0

    def is_finished(self):
        if self.limit_frames != "inf":
            assert isinstance(self.limit_frames, int)
            if self.counter_frames >= self.limit_frames:
                return True

        return False


@dataclass
class EffectWrapperStateLoopQuarters(EffectWrapperState):
    # WIP

    def is_active(self, beat_state: BeatState) -> bool:
        if not self.has_started:
            if self.timehandler.beat_state.is_beat:
                self.has_started = True
            else:
                return False

    def is_finished(self):
        if self.limit_loopquarters_loop != "inf":
            assert isinstance(self.limit_loopquarters_loop, int)
            if self.counter_quarters_loop >= self.limit_loopquarters_loop:
                return True

        return False
"""


# todo: move to core
class EffectWrapper:
    """
    Wrapper class for Effect objects. One EffectWrapper object will be created for each Effect class in Effecthandler object.
    Each EffectWrapper contains one Effect instance per Device
    """

    identifier: Literal["effect"] = "effect"

    def __init__(self, root: "RaveLightsApp", effect_objects: list["Effect"]):
        self.root = root
        self.settings: Settings = self.root.settings
        self.timehandler: TimeHandler = self.root.time_handler
        self.effects: list[Effect] = effect_objects
        self.name = effect_objects[0].name
        self.keywords = effect_objects[0].keywords
        self.weight = effect_objects[0].weight

        self.active = False
        self.trigger: Optional[BeatStatePattern] = None
        self.renew_trigger()

        self.state: Optional[EffectWrapperState] = None

        # self.mode = "frames"  # todo: make EnumStr

        #### mode == "frames"
        # self.counter_frames: int = 0
        # self.limit_frames: Optional[int] = None
        # self.frames_pattern_binary: list[bool] = [True]

        # mode == "quarters"
        # -> use frames infrastructure

        # mode == "loopquarters"
        self.counter_quarters: int = 0
        self.limit_loopquarters: int = 0
        self.limit_loopquarters_loop: int | str = 0
        self.counter_quarters_loop: int = 0
        self.loop_length_beats: int = 1

    def run_before(self):
        """Called once before each render cycle"""
        if self.active:
            effect = self.effects[0]
            effect.run_before()

    def run_after(self):
        """Called once after each render cycle"""
        if self.active:
            effect = self.effects[0]
            effect.run_before()

    def reset_frames(
        self,
        limit_frames: Optional[int],  # None == inf
        multi: int = 1,
        frames_pattern: FramesPattern = FramesPattern(1, (0,)),
    ):
        """for mode == 'frames'"""

        assert isinstance(multi, int) and multi >= 1

        self.state = EffectWrapperStateFrames(
            limit_frames=limit_frames,
            mode="frames",
            multi=multi,
            counter_frames=0,
            frames_pattern_binary=get_frames_pattern_binary(frames_pattern, multi=multi),
        )

    def reset(
        self,
        mode: str,
        multi: int,
        limit_frames: int,
        limit_quarters: int,
        limit_loopquarters: int,
        loop_length_beats: int,
        limit_quarters_loop: int,
        frames_pattern: list[str | int],
        quarters_pattern: list[str],
    ):
        """
        reset effects in effectwrapper
        """

        assert False

        # checks
        assert isinstance(multi, int) and multi >= 1

        # assignments
        self.mode = mode
        self.multi = multi
        self.has_started = False

        if self.mode == "frames":
            assert False, "use reset_frames() instead"
            self.has_started = True
            self.counter_frames = 0
            self.limit_frames = limit_frames
            self.frames_pattern_binary = get_frames_pattern_binary(frames_pattern, multi=multi)

        if self.mode == "quarters":
            self.has_started = True
            self.counter_frames = 0
            if isinstance(limit_quarters, str):
                self.limit_frames = limit_quarters
            else:
                self.limit_frames = int(limit_quarters * self.timehandler.quarter_time * self.timehandler.fps)
            self.frames_pattern_binary = get_frames_pattern_binary(frames_pattern, multi=multi)

        if self.mode == "loopquarters":
            # reset counter erst spaeter
            self.has_started = False
            self.counter_frames = 0
            self.limit_frames = limit_frames
            self.frames_pattern_binary = get_frames_pattern_binary(frames_pattern, multi=multi)

            self.counter_quarters = 0
            self.counter_quarters_loop = 0
            self.quarters_pattern_binary = get_quarters_pattern_binary(
                quarters_pattern=quarters_pattern,
                loop_length_beats=loop_length_beats,
                limit_loopquarters=limit_loopquarters,
            )
            self.limit_loopquarters = limit_quarters  # in quarters
            self.loop_length_beats = loop_length_beats  # in beats
            self.limit_loopquarters_loop = limit_quarters_loop

        for effect in self.effects:
            effect.reset()

    def render(self, in_matrix: ArrayFloat, colors: tuple[Color, Color], device_index: int) -> ArrayFloat:
        if self.active:
            effect = self.effects[device_index]
            return effect.render_matrix(in_matrix=in_matrix, colors=colors)
        else:
            return in_matrix

    def counting_before_check(self):
        """execute this once per frame before check_active"""

        if self.state:
            self.state.counting_before_check(beat_state=self.timehandler.beat_state)

    def check_active(self) -> bool:
        """Invisible render class with effect logic"""

        if not self.settings.global_effects_enabled:
            return False
        if self.state:
            return self.state.is_active(beat_state=self.timehandler.beat_state)
        assert False, "this should not happen -> bug"

    def counting_after_check(self):
        """execute this once per frame after check_active"""

        if self.state:
            self.state.counting_after_check(beat_state=self.timehandler.beat_state)

    def renew_trigger(self):
        self.trigger = self.effects[0].get_new_trigger()

    def alternate(self):
        for effect in self.effects:
            effect.alternate()

    def on_trigger(self):
        for effect in self.effects:
            effect.on_trigger()

    def sync_effects(self):
        sync_dict = self.effects[0].sync_send()
        for effect in self.effects[1:]:
            effect.sync_load(in_dict=sync_dict)

    def on_delete(self):
        for effect in self.effects:
            effect.on_delete()

    def is_finished(self):
        """returns if effect is finished (ready for removal)"""

        if self.state:
            return self.state.is_finished()

        return True

    def __repr__(self):
        return f"<EffectWrapper {self.name}>"


class Effect(ABC):
    """
    effects will be present temporarily (for n frames) before delted
    effects can modify settings parameters, for example color attribute
    """

    identifier: Literal["effect"] = "effect"

    def __init__(
        self,
        root: "RaveLightsApp",
        device: "Device",
        name: str,
        keywords: Optional[list["Keyword"]] = None,
        weight: float = 1.0,
        **kwargs: dict[str, str | int | float],
    ) -> None:
        self.root = root
        self.settings: Settings = self.root.settings
        self.timehandler: TimeHandler = self.root.time_handler
        self.device = device
        self.device_index = device.device_index
        self.init_pixelmatrix(self.device.pixelmatrix)
        self.name: str = name
        self.keywords: list[str] = [k.value for k in keywords] if keywords else []
        self.weight: float = float(weight)
        self.reset()

    @abstractmethod
    def reset(self) -> None:
        """Called, when effect is added to the queue"""
        ...

    @abstractmethod
    def run_before(self) -> None:
        """Called once before each render cycle"""
        ...

    @abstractmethod
    def run_after(self) -> None:
        """Called once after each render cycle"""
        ...

    @abstractmethod
    def render_matrix(self, in_matrix: ArrayFloat, colors: tuple[Color, Color]) -> ArrayFloat:
        """Called inside each render cycle, between vfilter and dimmer"""
        ...

    @abstractmethod
    def on_delete(self) -> None:
        """Called upon effect removal"""
        # todo: is this needed anymore?
        ...

    def sync_send(self) -> Optional[dict[str, Any]]:
        ...

    def sync_load(self, in_dict: Optional[dict[str, Any]]):
        if not isinstance(in_dict, dict):
            return None
        for key, value in in_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                logger.warning(f"key {key} does not exist in settings")

    def alternate(self) -> None:
        ...

    def get_new_trigger(self) -> Optional[BeatStatePattern]:
        return None

    def on_trigger(self) -> None:
        ...

    def init_pixelmatrix(self, pixelmatrix: "PixelMatrix") -> None:
        self.pixelmatrix = pixelmatrix
        self.n_lights: int = pixelmatrix.n_lights
        self.n_leds: int = pixelmatrix.n_leds
        self.n: int = pixelmatrix.n_leds * pixelmatrix.n_lights

    def __repr__(self) -> str:
        return f"<Effect {self.name}>"
