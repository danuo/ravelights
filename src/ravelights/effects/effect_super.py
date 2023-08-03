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

        self.mode = None

        # mode == "frames"
        self.counter_frames = 0
        self.limit_frames = None

        # mode == "quarters"
        self.counter_quarters = 0
        self.limit_quarters = None

    def render_settings_overwrite(self, device_id: int, selected_level: int) -> dict:
        effect = self.effect_dict[device_id]
        return effect.render_settings_overwrite(selected_level=selected_level)

    def render_matrix(self, in_matrix: ArrayNx3, color: Color, device_id: int) -> ArrayNx3:
        """Invisible render class with effect logic"""

        if self.mode == "frames":
            return self.render_matrix_frames(in_matrix=in_matrix, color=color, device_id=device_id)
        elif self.mode == "quarters":
            return self.render_matrix_quarters(in_matrix=in_matrix, color=color, device_id=device_id)
        return in_matrix

    def render_matrix_frames(self, in_matrix: ArrayNx3, color: Color, device_id: int) -> ArrayNx3:
        # todo first
        effect = self.effect_dict[device_id]
        print(self.counter_frames, self.frames_list)
        if self.counter_frames in self.frames_list:
            in_matrix = effect.render_matrix(in_matrix=in_matrix, color=color)
        self.counter_frames += 1
        return in_matrix

    def render_matrix_quarters(self, in_matrix: ArrayNx3, color: Color, device_id: int) -> ArrayNx3:
        # todo second
        effect = self.effect_dict[device_id]
        if self.settings.beat_state.is_quarterbeat:
            self.counter_quarters += 1
        return effect.render_matrix(in_matrix=in_matrix, color=color)

    def on_delete(self):
        for effect in self.effect_dict.values():
            effect.on_delete()

    def reset(self, mode: str = None, limit_frames: int = None, limit_quarters: int = None):
        mode = "frames"
        limit_frames = 12
        print("add effect: ", mode, limit_frames, limit_quarters)
        # assert limit_frames is None or limit_quarters is None

        if mode == "frames":
            assert limit_frames is not None
            self.mode = "frames"
            self.counter_frames = 0
            self.frames_list = [0, 2, 6, 8]
            self.limit_frames = limit_frames
            # todo: match limit_frames with frames_list. shorten or loop?

        if mode == "quarters":
            self.counter_quarters = 0
            self.limit_quarters = limit_quarters

        for effect in self.effect_dict.values():
            effect.reset()

    def is_finished(self):
        """returns if effect is finished (ready for removal)"""
        if self.limit_frames is not None:
            if self.counter_frames >= self.limit_frames:
                return True
        elif self.limit_quarters is not None:
            if self.counter_quarters > self.limit_quarters:
                return True
        return False


class Effect(ABC):
    """
    effects will be present temporarily (for n frames) before delted
    effects can modify settings parameters, for example color attribute
    """

    def __init__(self, root: "RaveLightsApp,", device: "Device", name: str, **kwargs: dict[str, str | int | float]):
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
