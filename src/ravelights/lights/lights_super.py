import math
import random
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

import numpy as np

from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import T_ALL, ArrayNx1
from ravelights.core.utils import cos_mapper, p, sign
from ravelights.vfilters.filter_flimmering import VfilterFlimmering
from ravelights.vfilters.vfilter_mirror import VfilterMirrorVer

if TYPE_CHECKING:
    from ravelights.app import RaveLightsApp
    from ravelights.core.device import Device
    from ravelights.core.pixelmatrix import PixelMatrix
    from ravelights.core.settings import Settings


class LightObject(ABC):
    def __init__(self, root: "RaveLightsApp", device: "Device", **kwargs: T_ALL):
        self.root = root
        self.device = device
        self.settings: "Settings" = self.root.settings
        self.pixelmatrix: "PixelMatrix" = self.device.pixelmatrix
        self.n_leds = self.pixelmatrix.n_leds
        self.gen_args = [self.root, self.device]
        self.counter_frame: int = 0
        self.counter_beats: int = -1

        self.lifetime_beats: Optional[int] = kwargs.get("lifetime_beats", None)
        self.lifetime_frames: Optional[int] = kwargs.get("lifetime_frames", None)
        self.init(**kwargs)

    @abstractmethod
    def init(self, **kwargs: T_ALL):
        ...

    @abstractmethod
    def is_done(self) -> bool:
        """Returns True if light object can be deleted"""
        ...

    @abstractmethod
    def render(self, color: Color) -> ArrayNx1:
        ...

    def increase_counters(self):
        self.counter_frame += 1
        if self.settings.beat_state.is_beat:
            self.counter_beats += 1

    def is_done_super(self) -> bool:
        """Default routine of is_done(). Will always be executed, alongside of the child specific
        implementation is_done(), which is overwritten by implementations of LightObjects"""
        if self.counter_frame > 1024:
            return True
        elif self.lifetime_beats is not None:
            if self.lifetime_beats >= self.counter_beats:
                return True
        elif self.lifetime_frames is not None:
            if self.counter_frame > self.lifetime_frames:
                if self.settings.beat_state.is_beat:
                    return True
        else:
            return self.is_done()

    def render_super(self, color: Color) -> tuple[ArrayNx1, bool]:
        self.increase_counters()
        matrix = self.render(color)
        done = self.is_done_super()
        return matrix, done

    def get_float_matrix(self) -> ArrayNx1:
        return np.zeros(shape=(self.n_leds), dtype=float)


class FallingSmallBlock(LightObject):
    # formerly TwoThing
    def init(self, **kwargs: T_ALL):
        if "flip" in kwargs:
            self.flip = kwargs["flip"]
        else:
            self.flip = False
        self.speed = random.uniform(1, 4)
        self.length = random.randint(2, 8) if self.settings.global_energy < 0.8 else random.randint(5, 20)
        self.pos = 1 - self.length  # only one pixel visible at first frame
        self.filter = VfilterFlimmering(*self.gen_args)

    def is_done(self) -> bool:
        return True if self.pos > self.n_leds + 30 else False

    def render(self, color: Color):
        matrix: ArrayNx1 = self.get_float_matrix()
        a = int(max(0, self.pos))
        b = int(self.pos + self.length)
        matrix[a:b] = 1
        speed = self.speed * (0.5 + 15 * self.settings.global_energy**4)
        self.pos += speed
        if self.settings.global_energy < 0.8:
            matrix = self.filter.render(matrix, color)
        if self.flip:
            matrix = np.flip(matrix)
        return matrix


class Slideblock(LightObject):
    # todo: slideblock with only the edges visible
    def init(self, **kwargs: T_ALL):
        self.lifetime_beats: Optional[int] = None
        self.lifetime_frames: int = random.randrange(start=5, stop=40)

        self.speed_a: float = 0.0
        self.speed_b: float = 0.0
        self.pos_a: float = random.random() * self.n_leds
        self.pos_b: float = random.random() * self.n_leds
        while abs(self.speed_a) < 0.1:
            self.speed_a = random.uniform(-1, 1)
        while abs(self.speed_b) < 0.1:
            self.speed_b = random.uniform(-1, 1)

    def render(self, color: Color):
        matrix = self.get_float_matrix()
        a, b = min(self.pos_a, self.pos_b), max(self.pos_a, self.pos_b)
        a, b = max(0, a), min(self.n_leds - 1, b)
        a, b = int(a), int(b)
        self.pos_a += self.speed_a * 4
        self.pos_b += self.speed_b * 4
        matrix[a:b] = 1.0
        return matrix


class SlideStrobe(Slideblock):
    def init(self, **kwargs: str):
        super().init(**kwargs)
        self.done = False
        if "flashes" in kwargs:
            self.flashes = kwargs["flashes"]
        else:
            ran = random.randint(3, 9)
            ran = random.choice([3, 4, 20])
            self.flashes = [x for _ in range(ran) for x in [True, False]]  # produces [True, False, True, False...]
        self.iter = iter(self.flashes)

    def is_done(self):
        return self.done

    def render(self, color: Color):
        matrix = super().render(color=color)
        flash = next(self.iter, None)
        if flash is None:
            self.done = True
        if flash:
            return matrix
        else:
            return self.get_float_matrix()


# class SymmetricalStrobe(SlideStrobe):
class SymmetricalStrobe(Slideblock):
    # todo: do not have this class, have vfilters for pattern sec instead
    def init(self, **kwargs: T_ALL):
        super().init(**kwargs)
        self.mirror = VfilterMirrorVer(**self.gen_args)

    def render(self, color: Color):
        matrix = super().render(color)
        matrix = self.mirror.render(matrix, color)
        return matrix


class Sine(LightObject):
    def init(self, **kwargs: T_ALL):
        matrix = self.get_float_matrix()
        size = 60
        pos_mid = (self.n_leds - size) // 2
        for i in range(size + 1):
            pos = pos_mid + i
            x = (i - size / 2) / size
            y = cos_mapper(x) ** 2
            matrix[pos] = y
        self.mat = matrix

    def is_done(self) -> bool:
        return False

    def render(self, color: Color):
        matrix = self.get_float_matrix()
        matrix[:] = 1
        return self.mat


class Square(LightObject):
    def init(self, **kwargs: T_ALL):
        matrix = self.get_float_matrix()
        size = 60
        pos_mid = (self.n_leds - size) // 2
        for i in range(size + 1):
            pos = pos_mid + i
            x2 = 1 - abs(i - size / 2) * 2 / size
            y = x2**2
            print(x2, y)
            matrix[pos] = y
        self.mat = matrix

    def is_done(self) -> bool:
        return False

    def render(self, color: Color):
        matrix = self.get_float_matrix()
        matrix[:] = 1
        return self.mat


class OneThing(LightObject):
    def init(self, **kwargs: T_ALL):
        if "flip" in kwargs:
            self.flip = kwargs["flip"]
        self.n_leds = self.pixelmatrix.n_leds
        self.lifetime_frames = random.randrange(start=5, stop=40)  # prev: 5, 30
        self.counter_frame = 0
        self.error: int = 0
        self.pos = int(abs(random.gauss(mu=0, sigma=1) * self.n_leds))
        self.pos = max(self.pos, 1)
        self.speed = random.randrange(start=1, stop=5)
        self.length = random.randrange(start=2, stop=7) ** 2  # prev: 2,25
        self.error_speed = max(random.gauss(mu=2, sigma=0.5), 0.5)
        self.sin_factor: float = 2.0

    def is_done(self) -> bool:
        return True if self.counter_frame > self.lifetime_frames else False

    def render(self, color: Color) -> ArrayNx1:
        # lifetime
        self.counter_frame += 1
        matrix: ArrayNx1 = np.zeros(shape=(self.n_leds), dtype=float)
        direction = 1 if p(0.5) else -1

        # update position
        pos = direction * int(self.pos + self.error)
        self.pos += self.speed
        self.pos = self.pos % self.n_leds
        self.error = int(-sign(self.error) * (abs(self.error) + self.error_speed))

        # apply pixel range
        a = min(self.n_leds, pos)
        b = min(self.n_leds, pos + self.length)

        # intensity
        intens = abs(math.sin(self.counter_frame * self.sin_factor)) + 0.1
        intens = min(intens, 1)
        matrix[a:b] = intens

        if self.flip:
            matrix = np.flip(matrix)
        return matrix


class Meteor(LightObject):
    def init(self, **kwargs: T_ALL):
        """speed formular
        speed [px/frame] = 144 px/b * 80 b/min * 1/60 min/s * 1/20 s/f
        """

        self.flip = kwargs.get("flip", False)

        self.travel_time = 1
        self.decay_factor = 0.8
        self.width = 20
        self.speed = self.n_leds * self.settings.bpm / 60 / self.settings.fps / self.travel_time
        # ! this spawns inside the domain, good for swiper, bad for "random meteor"
        self.pos = abs(random.gauss(0.1, 0.2)) * self.n_leds
        self.matrix = self.get_float_matrix()

    def is_done(self) -> bool:
        return self.pos > 2 * self.n_leds

    def render(self, color: Color) -> ArrayNx1:
        decay = np.random.uniform(0.85, 1.0, size=self.n_leds) * self.decay_factor
        decay = np.where(np.random.uniform(0, 1, size=self.n_leds) < 0.05, decay * 0.5, decay)
        self.matrix[:] = np.multiply(self.matrix, decay)
        pos = int(self.pos)
        spawn_chance_np = np.fmax(1.3 - np.abs(pos - np.arange(self.n_leds)) / self.width, 0)
        intensity = np.multiply(np.random.uniform(0, 1, size=self.n_leds), spawn_chance_np)
        intensity = np.clip(intensity, 0, 1)
        self.matrix[:] = np.fmax(self.matrix, intensity)
        self.pos += self.speed

        # apply flip
        out_matrix = np.flip(self.matrix, axis=0) if self.flip else self.matrix
        return out_matrix
