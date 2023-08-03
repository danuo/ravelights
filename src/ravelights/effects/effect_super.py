from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import numpy as np

from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import Array, ArrayNx3
from ravelights.core.pixelmatrix import PixelMatrix

if TYPE_CHECKING:
    from ravelights.app import RaveLightsApp
    from ravelights.core.device import Device
    from ravelights.core.settings import Settings
    from ravelights.core.timehandler import TimeHandler


class EffectWrapper:
    """
    Wrapper class for Effect objects. One EffectWrapper object will be created for each Effect class in Effecthandler object.
    Each EffectWrapper contains one Effect instance per Device
    """

    def __init__(self, root: "RaveLightsApp", effect_objects: list["Effect"], device_ids: list[int]):
        self.root = root
        self.settings: Settings = self.root.settings
        self.effect_dict: dict[int, Effect] = dict()
        for device_id, effect in zip(device_ids, effect_objects):
            self.effect_dict[device_id] = effect
        self.name = effect_objects[0].name

        self.mode = "frames"

        # mode == "frames"
        self.counter_frames: int = 0
        self.limit_frames: int = 0
        self.frames_pattern_binary: list[bool] = [True]

        # mode == "quarters"
        self.counter_quarters: int = 0
        self.limit_quarters: int = 0
        self.limit_quarters_loop: int = 0
        self.counter_quarters_loop: int = 0
        self.loop_length_beats: int = 1

    def render_settings_overwrite(self, device_id: int, selected_level: int) -> dict:
        effect = self.effect_dict[device_id]
        return effect.render_settings_overwrite(selected_level=selected_level)

    def reset(self, mode: str, multi: int, limit_frames: int, limit_quarters: int, loop_length_beats: int, limit_quarters_loop: int):
        """
        reset effects in effectwrapper
        """

        def get_frames_pattern_binary(frames_pattern: list[int], length_target: int, multi: int = 1):
            """
            frames_pattern = ["L10", 0, 2, 6, 8]
            length_target = 6
            multi = 2
            -> [True, True, False, False, True, True]
            """

            frames_pattern = ["L10", 0, 2, 6, 8]
            pattern_length = int(frames_pattern[0][1:])
            pattern = frames_pattern[1:]

            if frames_pattern is None:
                if length_target == "inf":
                    # todo: test this
                    return [True]
                else:
                    return [True] * length_target

            frames_pattern_binary = [y in pattern for x in range(pattern_length) for y in multi * [x]]

            if length_target == "inf":
                return frames_pattern_binary

            n = (length_target // len(frames_pattern_binary)) + 1
            frames_pattern_binary = (n * frames_pattern_binary)[:length_target]
            return frames_pattern_binary

        def get_quarters_pattern_binary(quarters_pattern: list[str], loop_length_beats: int):
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
                if index < loop_length_quarters:
                    quarters_pattern_binary[index] = True
            return quarters_pattern_binary

        """
        mode = "frames"
        limit_frames = 20  # int, match, inf
        """

        """
        mode = "quarters"
        limit_frames = 5
        loop_length_beats = 4
        limit_quarters_loop = 2
        limit_quarters = 2  # do not use this at the beginning
        """
        frames_pattern = None
        quarters_pattern = ["0A", "1A", "2A"]

        print("add effect: ", mode, limit_frames, limit_quarters)

        assert isinstance(multi, int) and multi >= 1
        self.multi = multi
        self.mode = mode

        if self.mode == "frames":
            self.counter_frames = 0
            self.limit_frames = limit_frames
            self.frames_pattern_binary = get_frames_pattern_binary(frames_pattern, length_target=limit_frames, multi=multi)

        if self.mode == "quarters":
            # reset counter erst später
            self.limit_frames = limit_frames
            self.frames_pattern_binary = get_frames_pattern_binary(frames_pattern, length_target=limit_frames, multi=multi)

            self.counter_frames = 0
            self.counter_quarters = 0
            self.counter_quarters_loop = 0
            self.quarters_time = None
            self.quarters_pattern_binary = get_quarters_pattern_binary(
                quarters_pattern=quarters_pattern, loop_length_beats=loop_length_beats
            )
            self.limit_quarters = limit_quarters  # in quarters
            self.loop_length_beats = loop_length_beats  # in beats
            self.limit_quarters_loop = limit_quarters_loop

        for effect in self.effect_dict.values():
            effect.reset()

    def perform_counting_per_frame(self):
        """
        execute this once per frame after rendering
        """

        self.counter_frames += 1
        if self.settings.beat_state.is_quarterbeat:
            self.counter_quarters += 1
            counter_beats = self.counter_quarters // 4
            if counter_beats > 0 and counter_beats // self.loop_length_beats == 0:
                self.counter_quarters_loop += 1
                self.counter_quarters = 0

    def render_matrix(self, in_matrix: ArrayNx3, color: Color, device_id: int) -> ArrayNx3:
        # print("run with device_id ", device_id)
        """Invisible render class with effect logic"""

        out_matrix = in_matrix
        if self.mode == "frames":
            out_matrix = self.render_matrix_frames(in_matrix=in_matrix, color=color, device_id=device_id)
        elif self.mode == "quarters":
            out_matrix = self.render_matrix_quarters(in_matrix=in_matrix, color=color, device_id=device_id)

        return out_matrix

    def render_matrix_frames(self, in_matrix: ArrayNx3, color: Color, device_id: int) -> ArrayNx3:
        effect = self.effect_dict[device_id]
        index = self.counter_frames % len(self.frames_pattern_binary)
        if self.frames_pattern_binary[index]:
            in_matrix = effect.render_matrix(in_matrix=in_matrix, color=color)
        return in_matrix

    def render_matrix_quarters(self, in_matrix: ArrayNx3, color: Color, device_id: int) -> ArrayNx3:
        print("x", self.counter_frames, self.counter_quarters, self.counter_quarters_loop, device_id)

        # * before first quarter, do nothing
        if self.quarters_time is None:
            # first quarter has not been found yet
            # start effect on next full beat:
            if self.settings.beat_state.is_beat:
                self.quarters_time = self.settings.timehandler.time_0  # do i need this?
            else:
                return in_matrix

        # * on quarter beat
        if self.settings.beat_state.is_quarterbeat:
            # * quarter beat is in pattern
            if self.quarters_pattern_binary[self.counter_quarters]:
                self.counter_frames = 0

            # * do counting stuff
            self.counter_quarters += 1
            counter_beats = self.counter_quarters // 4
            if counter_beats > 0 and counter_beats // self.loop_length_beats == 0:
                self.counter_quarters_loop += 1
                self.counter_quarters = 0

        if self.counter_frames < self.limit_frames:
            if self.frames_pattern_binary[self.counter_frames]:
                effect = self.effect_dict[device_id]
                in_matrix = effect.render_matrix(in_matrix=in_matrix, color=color)
        return in_matrix

    def on_delete(self):
        for effect in self.effect_dict.values():
            effect.on_delete()

    def is_finished(self):
        """returns if effect is finished (ready for removal)"""
        if self.mode == "frames":
            if self.limit_frames != "inf" and self.counter_frames >= self.limit_frames:
                return True
        elif self.mode == "quarters":
            if self.counter_quarters_loop >= self.limit_quarters_loop:
                print("quarters_done")
                return True
        return False


class Effect(ABC):
    """
    effects will be present temporarily (for n frames) before delted
    effects can modify settings parameters, for example color attribute
    """

    def __init__(self, root: "RaveLightsApp", device: "Device", name: str, **kwargs: dict[str, str | int | float]):
        self.root = root
        self.settings: Settings = self.root.settings
        self.timehandler: TimeHandler = self.settings.timehandler
        self.device = device
        self.init_pixelmatrix(self.device.pixelmatrix)
        self.name = name

        self.reset()

    @abstractmethod
    def reset(self):
        """Called, when effect is added to the queue"""
        ...

    @abstractmethod
    def render_settings_overwrite(self, selected_level: int) -> dict:
        """Called before each render cycle to overwrite settings for this
        specific frame, for example overwriting the colors"""
        ...

    @abstractmethod
    def render_matrix(self, in_matrix: ArrayNx3, color: Color) -> ArrayNx3:
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

    def colorize_matrix(self, matrix_mono: Array, color: Color) -> ArrayNx3:
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
            if matrix_mono.shape == (self.n,):
                matrix_mono = matrix_mono.reshape((self.n_leds, self.n_lights), order="F")
                matrix_rgb = np.zeros((self.n_leds, self.n_lights, 3))
            else:
                matrix_rgb = np.zeros((matrix_mono.size, 3))
        elif matrix_mono.ndim == 2:
            matrix_rgb = np.zeros((*matrix_mono.shape, 3))

        shape = [1] * matrix_mono.ndim + [3]
        color = np.array(color).reshape(shape)
        matrix_rgb = matrix_mono[..., None] * color
        return matrix_rgb

    def init_pixelmatrix(self, pixelmatrix: "PixelMatrix"):
        self.pixelmatrix = pixelmatrix
        self.n_lights: int = pixelmatrix.n_lights
        self.n_leds: int = pixelmatrix.n_leds
        self.n: int = pixelmatrix.n_leds * pixelmatrix.n_lights

    def __repr__(self):
        return self.name
