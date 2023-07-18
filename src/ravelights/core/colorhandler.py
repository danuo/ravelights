import colorsys
import random
from enum import Enum
from typing import TYPE_CHECKING, NamedTuple, Sequence

import numpy as np

from ravelights.core.pid import PIDController, PIDSpeeds

if TYPE_CHECKING:
    from ravelights.core.settings import Settings


COLOR_TRANSITION_SPEEDS = (PIDSpeeds.INSTANT, PIDSpeeds.FAST, PIDSpeeds.MEDIUM, PIDSpeeds.SLOW)


class Color(NamedTuple):
    red: float
    green: float
    blue: float

    def __repr__(self):
        return f"Color(r={round(self[0], 2)}, g={round(self[1], 2)}, b={round(self[2], 2)})"


class DefaultColors(Enum):
    WHITE = Color(1.0, 1.0, 1.0)
    BLACK = Color(0.0, 0.0, 0.0)
    RED = Color(1.0, 0.0, 0.0)
    GREEN = Color(0.0, 1.0, 0.0)
    BLUE = Color(0.0, 0.0, 1.0)
    CYAN = Color(0.0, 1.0, 1.0)
    MAGENTA = Color(1.0, 0.0, 1.0)
    YELLOW = Color(1.0, 1.0, 0.0)


class ColorEngine:
    def __init__(self, settings: "Settings"):
        self.settings = settings
        self._internal_color_transition_speed: str = ""
        default_colors = [DefaultColors.RED.value, DefaultColors.BLUE.value, DefaultColors.GREEN.value]
        self.color_pids: list[ColorPID] = [ColorPID(init_color_rgb=c) for c in default_colors]

    def run_pid_step(self):
        # apply color transition speed to pid controller if it has changed
        if self._internal_color_transition_speed != self.settings.color_transition_speed:
            self._internal_color_transition_speed = self.settings.color_transition_speed
            self.set_color_speed(self.settings.color_transition_speed)

        for color_pid in self.color_pids:
            color_pid.run_pid_step()

    def get_colors_rgb(self, selected_level: int) -> list[Color]:
        if selected_level == 1:
            return [c.get_rgb() for c in self.color_pids]
        else:
            return [self.color_pids[idx].get_rgb() for idx in [1, 0, 2]]

    def get_colors_rgb_target(self) -> list[Color]:
        return [c.get_rgb_target() for c in self.color_pids]

    def set_color_rgb(self, color: Color, level):
        self.color_pids[level].set_rgb_target(color)

    def set_color_speed(self, speed_str: str):
        for color_pid in self.color_pids:
            for pid in color_pid.pids:
                pid.load_parameter_preset(speed_str)


class ColorPID:
    """
    this class handles a group of PIDSystem objects to fully model a dynamic color.
    one pid is used for each channel (r,g,b)
    """

    def __init__(self, init_color_rgb: Color):
        # r, g, b
        self.pids = [PIDController(start_val=val) for val in init_color_rgb]

    def run_pid_step(self):
        for pid in self.pids:
            pid.perform_pid_step()
            # double pid stepping for improved stability. use if stability is a problem
            # pid.perform_pid_step()

    def get_rgb(self) -> Color:
        rgb = np.asarray([pid.value for pid in self.pids])
        rgb = rgb.clip(0, 1)
        return Color(*rgb)

    def set_rgb_target(self, color: Color):
        for val, pid in zip(color, self.pids):
            pid.target = val

    def get_rgb_target(self):
        """get target colors for api"""
        rgb = (pid.target for pid in self.pids)
        return Color(*rgb)


class ColorHandler:
    @classmethod
    def convert_to_color(cls, rgb_values: Sequence[float]) -> Color:
        assert len(rgb_values) == 3
        for val in rgb_values:
            assert 0.0 <= val <= 1.0
        return Color(*rgb_values)

    @classmethod
    def get_random_color(cls) -> Color:
        return cls.get_color_from_hue(random.uniform(0, 1))

    @classmethod
    def get_color_from_hue(cls, hue: float) -> Color:
        """returns a color with the given hue and maximum brightness and saturation.
        hue [0,1]"""
        return cls.convert_to_color(colorsys.hls_to_rgb(hue, 0.5, 1))

    @classmethod
    def get_complementary_color(cls, rgb_values: Sequence[float]) -> Color:
        def hilo(a: float, b: float, c: float) -> float:
            if c < b:
                b, c = c, b
            if b < a:
                a, b = b, a
            if c < b:
                b, c = c, b
            return a + c

        r, g, b = rgb_values
        k = hilo(r, g, b)
        rgb_values = tuple(k - u for u in (r, g, b))
        return cls.convert_to_color(rgb_values)

    @classmethod
    def get_complementary_33(cls, rgb_values: Sequence[float]) -> Color:
        """shift by 0.33"""
        hue = cls.get_hue_from_rgb(rgb_values)
        hue_new = (hue + 0.33) % 1
        return cls.get_color_from_hue(hue_new)

    @classmethod
    def get_complementary_50(cls, rgb_values: Sequence[float]) -> Color:
        """shift by 0.5"""
        hue = cls.get_hue_from_rgb(rgb_values)
        hue_new = (hue + 0.5) % 1
        return cls.get_color_from_hue(hue_new)

    @classmethod
    def get_complementary_66(cls, rgb_values: Sequence[float]) -> Color:
        """shift by 0.66"""
        hue = cls.get_hue_from_rgb(rgb_values)
        hue_new = (hue + 0.66) % 1
        return cls.get_color_from_hue(hue_new)

    @staticmethod
    def get_hue_from_rgb(rgb_values: Sequence[float]):
        """rgb values need to be in the range [0,1]"""
        hue, lightness, saturnation = colorsys.rgb_to_hls(*rgb_values)
        return hue

    @staticmethod
    def rgb_to_brightness(in_matrix: np.ndarray):
        """
        in_matrix: (nx3) with [r,g,b] for each row
        algorithm from colorsys.rgb_to_hsv()
        V: color brightness
        """
        return np.max(in_matrix, axis=1)
