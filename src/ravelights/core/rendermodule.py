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
        self.timeline_level = 0  # should be per device. different devices can have different levels
        self.counter_frame = 0  # for frameskip
        self.matrix_memory = self.pixelmatrix.get_matrix_float().copy()

    def assert_dims(self, in_matrix):
        """checks if shape is (n_leds, n_lights, 3). this is a debug function"""
        assert in_matrix.shape == (self.pixelmatrix.n_leds, self.pixelmatrix.n_lights, 3)

    def get_selected_trigger(self, gen_type: str | Type[Generator], level: Optional[int] = None) -> BeatStatePattern:
        identifier = gen_type if isinstance(gen_type, str) else gen_type.get_identifier()
        if level is None:
            level = self.timeline_level
        return self.settings.triggers[identifier][level]

    def get_selected_generator(self, gen_type: str | Type[Generator], timeline_level: Optional[int] = None) -> Generator:
        if timeline_level is None:
            timeline_level = self.get_timeline_level()
        identifier = gen_type if isinstance(gen_type, str) else gen_type.get_identifier()
        gen_name = self.settings.selected[identifier][timeline_level]
        return self.get_generator_by_name(gen_name)

    def get_generator_by_name(self, gen_name: str) -> Generator:
        return self.generators_dict[gen_name]

    def get_timeline_level(self) -> int:
        """
        return manual level or level from timeline, accoridng to setting
        """

        if self.settings.use_manual_timeline:
            return self.settings.manual_timeline_level
        else:
            return self.timeline_level

    def render(self):
        timeline_level = self.get_timeline_level()

        pattern: Pattern = self.get_selected_generator(gen_type=Pattern, timeline_level=timeline_level)
        pattern_sec: Pattern = self.get_selected_generator(gen_type="pattern_sec", timeline_level=timeline_level)
        vfilter: Vfilter = self.get_selected_generator(gen_type=Vfilter, timeline_level=timeline_level)
        thinner: Thinner = self.get_selected_generator(gen_type=Thinner, timeline_level=timeline_level)
        dimmer: Dimmer = self.get_selected_generator(gen_type=Dimmer, timeline_level=timeline_level)

        # ------------------------ validate thinner and dimmer ----------------------- #
        if pattern.p_add_thinner == 1.0 and thinner.name == "t_none":
            thinner = self.get_generator_by_name("t_random")
            if self.settings.beat_state.is_beat:
                thinner.on_trigger()

        if pattern.p_add_dimmer == 1.0 and dimmer.name == "d_none":
            dimmer = self.get_generator_by_name("d_decay_fast")
            if self.settings.beat_state.is_beat:
                dimmer.on_trigger()

        # ------------------------------- check trigger ------------------------------ #
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

        # ---------------------------------- colors ---------------------------------- #
        # color is a tuple of 3 colors
        # primary color: for every Generator, except secondary Pattern
        # secondary color: for secondary Pattern
        # effect color: for every Effect
        #
        color_prim, color_sec, color_effect = self.settings.color_engine.get_colors_rgb(timeline_level=timeline_level)

        # ----------------------- settings overwrite by effect ----------------------- #
        # todo: design choice
        # * settings_overwrite should not return anything
        # * this requires that all arguments are passed into render functions as arguments, instead of being taken from settings
        # * better to overwrite settings and reverse them to original value later on with on_delete()
        # * this mus stay here, must happen before render of patterns
        settings_overwrite = dict()
        for effect_wrapper in self.root.effecthandler.effect_queue:
            settings_overwrite.update(
                effect_wrapper.render_settings_overwrite(device_id=self.device.device_id, timeline_level=timeline_level)
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
