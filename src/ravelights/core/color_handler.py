import colorsys
import random
from enum import Enum, auto
from typing import TYPE_CHECKING, NamedTuple, Optional, Sequence

import numpy as np
from loguru import logger
from ravelights.core.custom_typing import ArrayFloat
from ravelights.core.pid import PIDController, PIDSpeeds
from ravelights.core.utils import StrEnum

if TYPE_CHECKING:
    from ravelights.core.settings import Settings


COLOR_TRANSITION_SPEEDS = (PIDSpeeds.INSTANT, PIDSpeeds.FAST, PIDSpeeds.MEDIUM, PIDSpeeds.SLOW)


class SecondaryColorModes(StrEnum):
    """available modes to generate secondary color for settings"""

    NONE = auto()
    RANDOM = auto()
    COMPLEMENTARY = auto()
    COMPLEMENTARY33 = auto()
    COMPLEMENTARY50 = auto()
    COMPLEMENTARY66 = auto()


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
        self.color_pids: dict[str, ColorPID] = {
            key: ColorPID(init_color_rgb=color) for key, color in zip("ABC", default_colors)
        }
        # todo: make color_overwrite private
        self.color_overwrite: dict[str, Optional[Color]] = {key: None for key in "ABC"}

    def before(self):
        self._run_pid_step()
        self.reset_color_overwrite()

    def reset_color_overwrite(self):
        self.color_overwrite = {key: None for key in "ABC"}

    def _run_pid_step(self):
        # apply color transition speed to pid controller if it has changed
        if self._internal_color_transition_speed != self.settings.color_transition_speed:
            self._internal_color_transition_speed = self.settings.color_transition_speed
            self.set_color_speed(self.settings.color_transition_speed)

        for color_pid in self.color_pids.values():
            color_pid.run_pid_step()

    def set_color_with_rule(self, color: list[float] | Color, color_key: str):
        assert len(color) == 3
        logger.info(f"set color with rule {self.settings.color_sec_mode} and level {color_key=}")
        color = ColorHandler.convert_to_color(color)
        self.set_single_color_rgb(color, color_key)
        if color_key == "A":
            for key in "BC":
                sec_color = self.get_secondary_color(color, color_key=key)  # todo
                logger.info(f"set sec_color: {key=} {sec_color=}")
                if sec_color is not None:
                    self.set_single_color_rgb(sec_color, key)
        self.settings.root.refresh_ui(sse_event="settings")

    def set_single_color_rgb(self, color: Color, color_key: str):
        """
        color_level_A
        color_level_B
        color_level_C
        """
        self.color_pids[color_key].set_rgb_target(color)
        self.settings.root.refresh_ui(sse_event="test")

    def get_color_keys(self, timeline_level: int) -> tuple[str, str]:
        color_key_prim = self.settings.color_mapping[str(timeline_level)]["prim"]
        color_key_sec = self.settings.color_mapping[str(timeline_level)]["sec"]
        return color_key_prim, color_key_sec

    def get_colors_rgb(self, timeline_level: int) -> tuple[Color, Color]:
        """
        gives the tuple of colors (color_prim, color_sec) in the correct order.
        color_1 and color_2 may be interchanged depending on the level
        """
        if timeline_level == 0:
            return (DefaultColors.BLACK.value, DefaultColors.BLACK.value)
        color_key_prim, color_key_sec = self.get_color_keys(timeline_level=timeline_level)
        color_prim = self.color_overwrite[color_key_prim]
        if color_prim is None:
            color_prim = self.color_pids[color_key_prim].get_rgb()
        color_sec = self.color_overwrite[color_key_sec]
        if color_sec is None:
            color_sec = self.color_pids[color_key_sec].get_rgb()

        return color_prim, color_sec

    def get_colors_rgb_target(self) -> dict[str, Color]:
        return {k: v.get_rgb_target() for k, v in self.color_pids.items()}

    def get_secondary_color(self, in_color: Color, color_key: str) -> Optional[Color]:
        """returns a color that matches in input color, according to the secondary
        color rule currently selected in settings"""

        match SecondaryColorModes(self.settings.color_sec_mode[color_key]):
            case SecondaryColorModes.NONE:
                return None
            case SecondaryColorModes.COMPLEMENTARY:
                return ColorHandler.get_complementary_color(in_color)
            case SecondaryColorModes.COMPLEMENTARY33:
                return ColorHandler.get_complementary_33(in_color)
            case SecondaryColorModes.COMPLEMENTARY50:
                return ColorHandler.get_complementary_50(in_color)
            case SecondaryColorModes.COMPLEMENTARY66:
                return ColorHandler.get_complementary_66(in_color)
            case SecondaryColorModes.RANDOM:
                return ColorHandler.get_random_color()
            case _:
                return None

    def set_color_speed(self, speed_str: str):
        if speed_str in COLOR_TRANSITION_SPEEDS:
            for color_pid in self.color_pids.values():
                for pid in color_pid.pids:
                    pid.load_parameter_preset(speed_str)
        else:
            logger.warning("set_color_speed() called with invalid speed")
        self.settings.root.refresh_ui(sse_event="settings")


class ColorPID:
    """
    this class handles a group of PIDSystem objects to fully model a dynamic color.
    one pid is used for each channel (r,g,b)
    """

    def __init__(self, init_color_rgb: Optional[Color] = None):
        if init_color_rgb is None:
            init_color_rgb = Color(1.0, 0.0, 0.0)
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
    def get_hue_from_rgb(rgb_values: Sequence[float]) -> float:
        """rgb values need to be in the range [0,1]"""
        hue, _, _ = colorsys.rgb_to_hls(*rgb_values)
        return hue

    @staticmethod
    def rgb_to_brightness(in_matrix: ArrayFloat) -> ArrayFloat:
        """
        in_matrix: (nx3) with [r,g,b] for each row
        algorithm from colorsys.rgb_to_hsv()
        V: color brightness
        """
        return np.max(in_matrix, axis=1)
