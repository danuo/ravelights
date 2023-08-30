import logging
from typing import TYPE_CHECKING, Optional, Type

from ravelights.core.bpmhandler import BeatStatePattern
from ravelights.core.custom_typing import ArrayNx1, ArrayNx3
from ravelights.core.generator_super import Dimmer, Generator, Pattern, Thinner, Vfilter
from ravelights.core.pixelmatrix import PixelMatrix
from ravelights.core.settings import Settings

if TYPE_CHECKING:
    from ravelights.core.device import Device
    from ravelights.core.ravelights_app import RaveLightsApp

logger = logging.getLogger(__name__)


class RenderModule:
    def __init__(self, root: "RaveLightsApp", device: "Device"):
        self.root = root
        self.settings: Settings = self.root.settings
        self.device: Device = device
        self.pixelmatrix: PixelMatrix = self.device.pixelmatrix
        self.device_automatic_timeline_level = 0
        self.counter_frame = 0  # for frameskip
        self.matrix_memory = self.pixelmatrix.matrix_float.copy()
        self.generators_dict: dict[str, Generator] = dict()

    def assert_dims(self, in_matrix):
        """checks if shape is (n_leds, n_lights, 3). this is a debug function"""
        assert in_matrix.shape == (self.pixelmatrix.n_leds, self.pixelmatrix.n_lights, 3)

    def get_selected_trigger(self, gen_type: str | Type[Generator], level: Optional[int] = None) -> BeatStatePattern:
        identifier = gen_type if isinstance(gen_type, str) else gen_type.get_identifier()
        if level is None:
            level = self.device_automatic_timeline_level
        return self.settings.triggers[identifier][level]

    def get_selected_generator(
        self, gen_type: str | Type[Generator], timeline_level: Optional[int] = None
    ) -> Generator:
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
        # todo: make this pretty
        if self.device.device_manual_timeline_level != 4:
            return self.device.device_manual_timeline_level

        if self.settings.use_manual_timeline:
            if self.device.device_manual_timeline_level != 4:
                return self.device.device_manual_timeline_level
            else:
                return self.settings.global_manual_timeline_level
        else:
            return self.device_automatic_timeline_level

    def render(self):
        # ---------------------------- get timeline_level ---------------------------- #
        timeline_level = self.get_timeline_level()
        timeline_level_pattern_sec = 1 if self.settings.global_pattern_sec else timeline_level
        timeline_level_vfilter = 1 if self.settings.global_vfilter else timeline_level
        timeline_level_thinner = 1 if self.settings.global_thinner else timeline_level
        timeline_level_dimmer = 1 if self.settings.global_dimmer else timeline_level

        # ------------------------------ get generators ------------------------------ #
        pattern: Pattern = self.get_selected_generator(gen_type=Pattern, timeline_level=timeline_level)
        pattern_sec: Pattern = self.get_selected_generator(
            gen_type="pattern_sec", timeline_level=timeline_level_pattern_sec
        )
        vfilter: Vfilter = self.get_selected_generator(gen_type=Vfilter, timeline_level=timeline_level_vfilter)
        thinner: Thinner = self.get_selected_generator(gen_type=Thinner, timeline_level=timeline_level_thinner)
        dimmer: Dimmer = self.get_selected_generator(gen_type=Dimmer, timeline_level=timeline_level_dimmer)

        # ------------------------ validate thinner and dimmer ----------------------- #
        if pattern.p_add_thinner == 1.0 and thinner.name == "t_none":
            thinner = self.get_generator_by_name("t_random")
            if self.settings.beat_state.is_beat:
                thinner.on_trigger()
        if pattern.p_add_thinner == 0.0:
            thinner = self.get_generator_by_name("t_none")

        if pattern.p_add_dimmer == 1.0 and dimmer.name == "d_none":
            dimmer = self.get_generator_by_name("d_decay_fast")
            if self.settings.beat_state.is_beat:
                dimmer.on_trigger()
        if pattern.p_add_dimmer == 0.0:
            dimmer = self.get_generator_by_name("d_none")

        # ------------------------------- check trigger ------------------------------ #
        if self.get_selected_trigger(gen_type=Pattern).is_match(self.settings.beat_state, self.device):
            pattern.on_trigger()
        if self.get_selected_trigger(gen_type="pattern_sec").is_match(self.settings.beat_state, self.device):
            pattern_sec.on_trigger()
        if self.get_selected_trigger(gen_type=Vfilter).is_match(self.settings.beat_state, self.device):
            vfilter.on_trigger()
        if self.get_selected_trigger(gen_type=Thinner).is_match(self.settings.beat_state, self.device):
            thinner.on_trigger()
        if self.get_selected_trigger(gen_type=Dimmer).is_match(self.settings.beat_state, self.device):
            dimmer.on_trigger()

        # ---------------------------------- colors ---------------------------------- #
        # color is a tuple of 3 colors
        # primary color: for every Generator, except secondary Pattern
        # secondary color: for secondary Pattern
        # effect color: for every Effect
        #
        color_prim, color_sec, color_effect = self.settings.color_engine.get_colors_rgb(timeline_level=timeline_level)

        # ─── RENDER PATTERN ──────────────────────────────────────────────
        matrix = pattern.render(color=color_prim)
        self.assert_dims(matrix)

        # ─── FRAMESKIP ───────────────────────────────────────────────────
        matrix = self.apply_frameskip(matrix)
        self.assert_dims(matrix)

        # ─── RENDER SECONDARY PATTERN ────────────────────────────────────
        matrix_sec = pattern_sec.render(color=color_sec)
        matrix = Generator.merge_matrices(matrix, matrix_sec)

        # ─── RENDER VFILTER ──────────────────────────────────────────────
        matrix = vfilter.render(matrix, color=color_prim)
        self.assert_dims(matrix)

        # ─── RENDER THINNER ──────────────────────────────────────────────
        matrix = thinner.render(matrix, color=color_prim)
        self.assert_dims(matrix)

        # ─── RENDER DIMMER ───────────────────────────────────────────────
        matrix = dimmer.render(matrix, color=color_prim)
        self.assert_dims(matrix)

        # ─── Render Effects ───────────────────────────────────────────────
        in_matrix = matrix.copy()
        for effect_wrapper in self.root.effecthandler.effective_effect_queue:
            out_matrix = effect_wrapper.render(in_matrix=matrix, color=color_effect, device_id=self.device.device_id)
            if effect_wrapper.draw_mode == "overlay":
                matrix = Generator.merge_matrices(matrix, out_matrix)
            elif effect_wrapper.draw_mode == "normal":
                matrix = out_matrix
            else:
                assert False

        # global thing
        if self.settings.global_effect_draw_mode == "overlay":
            matrix = Generator.merge_matrices(in_matrix, matrix)
        self.assert_dims(matrix)

        # ─── Send To Pixelmatrix ──────────────────────────────────────
        self.pixelmatrix.set_matrix_float(matrix)

    def register_generators(self, generators: list[Generator]):
        for g in generators:
            self.generators_dict.update({g.name: g})

    def find_generator(self, name: str) -> Generator:
        return self.generators_dict[name]

    def apply_frameskip(self, in_matrix: ArrayNx3) -> ArrayNx3:
        self.counter_frame += 1
        frameskip = max(self.settings.global_frameskip, self.device.device_frameskip)
        if self.counter_frame % frameskip != 0:
            return self.matrix_memory.copy()
        else:
            self.matrix_memory = in_matrix.copy()
            return in_matrix
