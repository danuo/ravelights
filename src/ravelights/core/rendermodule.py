import logging
from typing import TYPE_CHECKING, Optional, Type

from ravelights.core.bpmhandler import BeatStatePattern
from ravelights.core.custom_typing import ArrayNx1, ArrayNx3
from ravelights.core.generator_super import Dimmer, Generator, Pattern, Thinner, Vfilter
from ravelights.core.pixelmatrix import PixelMatrix
from ravelights.core.settings import Settings

if TYPE_CHECKING:
    from ravelights.app import RaveLightsApp
    from ravelights.core.device import Device

logger = logging.getLogger(__name__)


class RenderModule:
    def __init__(self, root: "RaveLightsApp", device: "Device"):
        self.root = root
        self.settings: Settings = self.root.settings
        self.device: Device = device
        self.pixelmatrix: PixelMatrix = self.device.pixelmatrix
        self.selected_level = 0  # should be per device. different devices can have different levels
        self.counter_frame = 0  # for frameskip
        self.matrix_memory = self.pixelmatrix.get_matrix_float().copy()

    def assert_dims(self, in_matrix):
        """checks if shape is (n_leds, n_lights, 3). this is a debug function"""
        assert in_matrix.shape == (self.pixelmatrix.n_leds, self.pixelmatrix.n_lights, 3)

    def get_selected_trigger(self, gen_type: str | Type[Generator], level: Optional[int] = None) -> BeatStatePattern:
        identifier = gen_type if isinstance(gen_type, str) else gen_type.get_identifier()
        if level is None:
            level = self.selected_level
        return self.settings.triggers[identifier][level]

    def get_selected_generator(self, gen_type: str | Type[Generator], level: Optional[int] = None) -> Generator:
        identifier = gen_type if isinstance(gen_type, str) else gen_type.get_identifier()
        if level is None:
            level = self.selected_level
        gen_name = self.settings.selected[identifier][level]
        return self.get_generator_by_name(gen_name)

    def get_generator_by_name(self, gen_name: str) -> Generator:
        return self.generators_dict[gen_name]

    def render(self):
        pattern: Pattern = self.get_selected_generator(gen_type=Pattern)
        pattern_sec: Pattern = self.get_selected_generator(gen_type="pattern_sec")
        vfilter: Vfilter = self.get_selected_generator(gen_type=Vfilter)
        thinner: Thinner = self.get_selected_generator(gen_type=Thinner)
        dimmer: Dimmer = self.get_selected_generator(gen_type=Dimmer)

        # ─── Check Trigger ────────────────────────────────────────────
        if self.settings.beat_state == self.get_selected_trigger(gen_type=Pattern):
            pattern.on_trigger()
        if self.settings.beat_state == self.get_selected_trigger(gen_type="pattern_sec"):
            pattern_sec.on_trigger()
        if self.settings.beat_state == self.get_selected_trigger(gen_type=Vfilter):
            vfilter.on_trigger()
        if self.settings.beat_state == self.get_selected_trigger(gen_type=Thinner):
            thinner.on_trigger()
        if self.settings.beat_state == self.get_selected_trigger(gen_type=Dimmer):
            dimmer.on_trigger()

        if BeatStatePattern(beats=[0], loop_length=16) == self.settings.beat_state:
            # triggers every 16 beats
            print("BeatStatePattern with loop_length=16 triggered in rendermodule")

        # ---------------------------------- colors ---------------------------------- #
        # color is a tuple of 3 colors
        # primary color: for every Generator, except secondary Pattern
        # secondary color: for secondary Pattern
        # effect color: for every Effect
        #
        color_prim, color_sec, color_effect = self.settings.color_engine.get_colors_rgb(selected_level=self.selected_level)

        # ----------------------- settings overwrite by effect ----------------------- #
        settings_overwrite = dict()
        for effect_wrapper in self.root.effecthandler.effect_queue:
            settings_overwrite.update(
                effect_wrapper.render_settings_overwrite(device_id=self.device.device_id, selected_level=self.selected_level)
            )
        if settings_overwrite:
            if "color_prim" in settings_overwrite:
                color_prim = settings_overwrite["color_prim"]
                print("overwritten color_prim")

        # todo: apply settings overwrite

        # ─── RENDER PATTERN ──────────────────────────────────────────────
        matrix = pattern.render(color=color_prim)
        self.assert_dims(matrix)

        # ─── FRAMESKIP ───────────────────────────────────────────────────
        matrix = self.apply_frame_skip(matrix)
        self.assert_dims(matrix)

        # ─── RENDER SECONDARY PATTERN ────────────────────────────────────
        matrix_sec = pattern_sec.render(color=color_sec)
        matrix = Generator.merge_matrices(matrix, matrix_sec)

        # ─── RENDER VFILTER ──────────────────────────────────────────────
        matrix = vfilter.render(matrix, color=color_prim)
        self.assert_dims(matrix)

        # ─── Render Effects ───────────────────────────────────────────
        for effect_wrapper in self.root.effecthandler.effect_queue:
            # effect = effect_wrapper.effect_dict[self.device.device_id]
            matrix = effect_wrapper.render_matrix(in_matrix=matrix, color=color_effect, device_id=self.device.device_id)
        self.assert_dims(matrix)

        # ─── RENDER THINNER ──────────────────────────────────────────────
        matrix = thinner.render(matrix, color=color_prim)
        self.assert_dims(matrix)

        # ─── RENDER DIMMER ───────────────────────────────────────────────
        matrix = dimmer.render(matrix, color=color_prim)
        self.assert_dims(matrix)

        # ─── Send To Pixelmatrix ──────────────────────────────────────
        self.pixelmatrix.set_matrix_float(matrix)

    def register_generators(self, generators: list[Generator]):
        self.generators_dict: dict[str, Generator] = dict()
        for g in generators:
            self.generators_dict.update({g.name: g})

    def find_generator(self, name: str) -> Generator:
        return self.generators_dict[name]

    def apply_frame_skip(self, in_matrix: ArrayNx3) -> ArrayNx3:
        self.counter_frame += 1
        if self.counter_frame % self.settings.frame_skip != 0:
            return self.matrix_memory.copy()
        else:
            self.matrix_memory = in_matrix.copy()
            return in_matrix
