from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional

import numpy as np
from loguru import logger  # type:ignore
from ravelights.core.bpmhandler import BeatStatePattern
from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import ArrayFloat
from ravelights.core.pixelmatrix import PixelMatrix

if TYPE_CHECKING:
    from ravelights.configs.components import Keywords
    from ravelights.core.device import Device
    from ravelights.core.ravelights_app import RaveLightsApp
    from ravelights.core.settings import Settings
    from ravelights.core.timehandler import TimeHandler


# todo: move to core
class EffectWrapper:
    """
    Wrapper class for Effect objects. One EffectWrapper object will be created for each Effect class in Effecthandler object.
    Each EffectWrapper contains one Effect instance per Device
    """

    def __init__(self, root: "RaveLightsApp", effect_objects: list["Effect"]):
        self.root = root
        self.settings: Settings = self.root.settings
        self.effects: list[Effect] = effect_objects
        self.name = effect_objects[0].name
        self.keywords = effect_objects[0].keywords
        self.weight = effect_objects[0].weight
        self.mode = "frames"  # todo: make EnumStr
        self.draw_mode = "overlay"  # "overlay", "normal"
        self.active = False
        self.trigger: Optional[BeatStatePattern] = None
        self.renew_trigger()

        # mode == "frames"
        self.counter_frames: int = 0
        self.limit_frames: int | str = 0
        self.frames_pattern_binary: list[bool] = [True]

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

        def get_frames_pattern_binary(frames_pattern: list[str | int], multi: int = 1):
            """
            example input:
            frames_pattern = ["L4", 0]
            multi = 2
            -> [True, True, False, False, False, False, False, False]
            """

            string_part = frames_pattern[0]
            assert isinstance(string_part, str)
            assert string_part[0] == "L"
            pattern_length = int(string_part[1:])

            pattern = frames_pattern[1:]
            frames_pattern_binary = [y in pattern for x in range(pattern_length) for y in multi * [x]]
            return frames_pattern_binary

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

        assert isinstance(multi, int) and multi >= 1
        self.multi = multi
        self.mode = mode
        self.has_started = False

        if self.mode == "frames":
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
                self.limit_frames = int(limit_quarters * self.settings.quarter_time * self.settings.fps)
            self.frames_pattern_binary = get_frames_pattern_binary(frames_pattern, multi=multi)

        if self.mode == "loopquarters":
            # reset counter erst sp�ter
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

    def render(self, in_matrix: ArrayFloat, colors: list[Color], device_id: int) -> ArrayFloat:
        if self.active:
            effect = self.effects[device_id]
            return effect.render_matrix(in_matrix=in_matrix, colors=colors)
        else:
            return in_matrix

    def counting_before_check(self):
        """
        execute this once per frame before check_active
        """

        if self.has_started and self.mode == "loopquarters":
            if self.settings.beat_state.is_quarter:
                if self.quarters_pattern_binary[self.counter_quarters]:
                    self.counter_frames = 0

    def check_active(self) -> bool:
        """Invisible render class with effect logic"""
        if not self.settings.global_effects_enabled:
            return False

        if self.mode == "frames" or self.mode == "quarters":
            return self.check_active_matrix_frames()
        elif self.mode == "loopquarters":
            return self.checkactive_matrix_loopquarters()
        assert False

    def check_active_matrix_frames(self) -> bool:
        index = self.counter_frames % len(self.frames_pattern_binary)
        if self.frames_pattern_binary[index]:
            return True
        return False

    def checkactive_matrix_loopquarters(self) -> bool:
        # search first beat before start
        if not self.has_started:
            if self.settings.beat_state.is_beat:
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

    def counting_after_check(self):
        """
        execute this once per frame after check_active
        """

        if self.has_started:
            self.counter_frames += 1
            if self.settings.beat_state.is_quarter:
                self.counter_quarters += 1
                counter_beats = self.counter_quarters // 4
                if counter_beats > 0 and counter_beats % self.loop_length_beats == 0:
                    self.counter_quarters_loop += 1
                    self.counter_quarters = 0
                    self.counter_frames = 0

    def change_draw(self):
        if self.draw_mode == "overlay":
            self.draw_mode = "normal"
        elif self.draw_mode == "normal":
            self.draw_mode = "overlay"
        else:
            assert False

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
        if self.mode == "frames" or self.mode == "quarters":
            if self.limit_frames != "inf":
                assert isinstance(self.limit_frames, int)
                if self.counter_frames >= self.limit_frames:
                    return True
        elif self.mode == "loopquarters":
            if self.limit_loopquarters_loop != "inf":
                assert isinstance(self.limit_loopquarters_loop, int)
                if self.counter_quarters_loop >= self.limit_loopquarters_loop:
                    return True
        return False

    def get_identifier(self):
        return self.effects[0].get_identifier()

    def __repr__(self):
        return f"<EffectWrapper {self.name}>"


class Effect(ABC):
    """
    effects will be present temporarily (for n frames) before delted
    effects can modify settings parameters, for example color attribute
    """

    def __init__(
        self,
        root: "RaveLightsApp",
        device: "Device",
        name: str,
        keywords: Optional[list["Keywords"]] = None,
        weight: float = 1.0,
        **kwargs: dict[str, str | int | float],
    ):
        self.root = root
        self.settings: Settings = self.root.settings
        self.timehandler: TimeHandler = self.settings.timehandler
        self.device = device
        self.device_id = device.device_id
        self.init_pixelmatrix(self.device.pixelmatrix)
        self.name: str = name
        self.keywords: list[str] = [k.value for k in keywords] if keywords else []
        self.weight: float = float(weight)
        self.reset()

    @abstractmethod
    def reset(self):
        """Called, when effect is added to the queue"""
        ...

    @abstractmethod
    def run_before(self):
        """Called once before each render cycle"""
        ...

    @abstractmethod
    def run_after(self):
        """Called once after each render cycle"""
        ...

    @abstractmethod
    def render_matrix(self, in_matrix: ArrayFloat, colors: list[Color]) -> ArrayFloat:
        """Called inside each render cycle, between vfilter and dimmer"""
        ...

    @abstractmethod
    def on_delete(self):
        """Called upon effect removal"""
        # todo: is this needed anymore?
        ...

    @staticmethod
    def get_identifier():
        return "effect"

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

    def alternate(self):
        ...

    def get_new_trigger(self) -> Optional[BeatStatePattern]:
        return None

    def on_trigger(self):
        ...

    def colorize_matrix(self, matrix_mono: ArrayFloat, color: Color) -> ArrayFloat:
        """
        function to colorize a matrix with a given color
        for colorization, another dimension is added
        special case: input matrix is 1d of size n:
        (n) -> (n_leds, n_lights, 3)  /special case
        (x) -> (x,3)
        (x,y) -> (x,y,3)
        """

        # prepare output matrix of correct size
        if matrix_mono.ndim == 1:
            if matrix_mono.shape == (self.n,) and self.n_lights > 1:
                matrix_mono = matrix_mono.reshape((self.n_leds, self.n_lights), order="F")
                matrix_rgb = np.zeros((self.n_leds, self.n_lights, 3))
            else:
                matrix_rgb = np.zeros((matrix_mono.size, 3))
        elif matrix_mono.ndim == 2:
            matrix_rgb = np.zeros((*matrix_mono.shape, 3))

        shape = [1] * matrix_mono.ndim + [3]
        color_array = np.array(color).reshape(shape)
        matrix_rgb = matrix_mono[..., None] * color_array
        return matrix_rgb

    def init_pixelmatrix(self, pixelmatrix: "PixelMatrix"):
        self.pixelmatrix = pixelmatrix
        self.n_lights: int = pixelmatrix.n_lights
        self.n_leds: int = pixelmatrix.n_leds
        self.n: int = pixelmatrix.n_leds * pixelmatrix.n_lights

    def __repr__(self):
        return f"<Effect {self.name}>"
