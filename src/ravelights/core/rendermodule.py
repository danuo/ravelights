import logging
from typing import TYPE_CHECKING, Literal, Optional, Type, cast, overload

from ravelights.core.bpmhandler import BeatStatePattern
from ravelights.core.custom_typing import ArrayFloat, assert_dims
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
        self.generators_dict: dict[str, Pattern | Vfilter | Thinner | Dimmer] = dict()

    def get_selected_trigger(self, gen_type: str | Type[Generator], level: Optional[int] = None) -> BeatStatePattern:
        identifier = gen_type if isinstance(gen_type, str) else gen_type.get_identifier()
        if level is None:
            level = self.device_automatic_timeline_level
        return self.settings.triggers[identifier][level]

    @overload
    def get_selected_generator(self, gen_type: Type[Pattern], timeline_level: Optional[int] = None) -> Pattern:
        ...

    @overload
    def get_selected_generator(self, gen_type: Literal["pattern_sec"], timeline_level: Optional[int] = None) -> Pattern:
        ...

    @overload
    def get_selected_generator(self, gen_type: Type[Vfilter], timeline_level: Optional[int] = None) -> Vfilter:
        ...

    @overload
    def get_selected_generator(self, gen_type: Type[Dimmer], timeline_level: Optional[int] = None) -> Dimmer:
        ...

    @overload
    def get_selected_generator(self, gen_type: Type[Thinner], timeline_level: Optional[int] = None) -> Thinner:
        ...

    @overload
    def get_selected_generator(
        self, gen_type: str, timeline_level: Optional[int] = None
    ) -> Pattern | Vfilter | Dimmer | Thinner:
        ...

    def get_selected_generator(
        self,
        gen_type: str | Type[Pattern] | Type[Vfilter] | Type[Dimmer] | Type[Thinner],
        timeline_level: Optional[int] = None,
    ) -> Pattern | Vfilter | Thinner | Dimmer:
        if timeline_level is None:
            timeline_level = self.get_timeline_level()
        identifier = gen_type if isinstance(gen_type, str) else gen_type.get_identifier()
        gen_name = self.settings.selected[identifier][timeline_level]
        return self.get_generator_by_name(gen_name)

    def get_generator_by_name(self, gen_name: str) -> Pattern | Vfilter | Thinner | Dimmer:
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
        # fmt: off
        pattern: Pattern = self.get_selected_generator(gen_type=Pattern, timeline_level=timeline_level)
        pattern_sec: Pattern = self.get_selected_generator(gen_type="pattern_sec", timeline_level=timeline_level_pattern_sec)
        vfilter: Vfilter = self.get_selected_generator(gen_type=Vfilter, timeline_level=timeline_level_vfilter)
        thinner: Thinner = self.get_selected_generator(gen_type=Thinner, timeline_level=timeline_level_thinner)
        dimmer: Dimmer = self.get_selected_generator(gen_type=Dimmer, timeline_level=timeline_level_dimmer)
        # fmt: on
        # ------------------------ validate thinner and dimmer ----------------------- #
        if pattern.p_add_thinner == 1.0 and thinner.name == "t_none":
            thinner = cast(Thinner, self.get_generator_by_name("t_random"))
            if self.settings.beat_state.is_beat:
                thinner.on_trigger()
        if pattern.p_add_thinner == 0.0:
            thinner = cast(Thinner, self.get_generator_by_name("t_none"))

        if pattern.p_add_dimmer == 1.0 and dimmer.name == "d_none":
            dimmer = cast(Dimmer, self.get_generator_by_name("d_decay_fast"))
            if self.settings.beat_state.is_beat:
                dimmer.on_trigger()
        if pattern.p_add_dimmer == 0.0:
            dimmer = cast(Dimmer, self.get_generator_by_name("d_none"))

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
        # color is a tuple of 2 colors
        # primary color: dominant color in pattern
        # secondary color: optional supplementary color
        colors = self.settings.color_engine.get_colors_rgb(timeline_level=timeline_level)

        # ─── RENDER PATTERN ──────────────────────────────────────────────
        matrix = pattern.render(colors=colors)
        assert_dims(matrix, self.pixelmatrix.n_leds, self.pixelmatrix.n_lights, 3)

        # ─── FRAMESKIP ───────────────────────────────────────────────────
        matrix = self.apply_frameskip(matrix)
        assert_dims(matrix, self.pixelmatrix.n_leds, self.pixelmatrix.n_lights, 3)

        # ─── RENDER SECONDARY PATTERN ────────────────────────────────────
        matrix_sec = pattern_sec.render(colors=colors[::-1])  # todo
        matrix = Generator.merge_matrices(matrix, matrix_sec)

        # ─── RENDER VFILTER ──────────────────────────────────────────────
        matrix = vfilter.render(matrix, colors=colors)
        assert_dims(matrix, self.pixelmatrix.n_leds, self.pixelmatrix.n_lights, 3)

        # ─── RENDER THINNER ──────────────────────────────────────────────
        matrix = thinner.render(matrix, colors=colors)
        assert_dims(matrix, self.pixelmatrix.n_leds, self.pixelmatrix.n_lights, 3)

        # ─── RENDER DIMMER ───────────────────────────────────────────────
        matrix = dimmer.render(matrix, colors=colors)
        assert_dims(matrix, self.pixelmatrix.n_leds, self.pixelmatrix.n_lights, 3)

        # ─── Render Effects ───────────────────────────────────────────────
        in_matrix = matrix.copy()
        for effect_wrapper in self.root.effecthandler.effective_effect_queue:
            out_matrix = effect_wrapper.render(in_matrix=matrix, colors=colors, device_id=self.device.device_id)
            if effect_wrapper.draw_mode == "overlay":
                matrix = Generator.merge_matrices(matrix, out_matrix)
            elif effect_wrapper.draw_mode == "normal":
                matrix = out_matrix
            else:
                assert False

        # global thing
        if self.settings.global_effect_draw_mode == "overlay":
            matrix = Generator.merge_matrices(in_matrix, matrix)
        assert_dims(matrix, self.pixelmatrix.n_leds, self.pixelmatrix.n_lights, 3)

        # ─── Send To Pixelmatrix ──────────────────────────────────────
        self.pixelmatrix.set_matrix_float(matrix)

    def register_generators(self, generators: list[Pattern | Vfilter | Dimmer | Thinner]):
        for g in generators:
            self.generators_dict.update({g.name: g})

    def find_generator(self, name: str) -> Pattern | Vfilter | Dimmer | Thinner:
        return self.generators_dict[name]

    def apply_frameskip(self, in_matrix: ArrayFloat) -> ArrayFloat:
        self.counter_frame += 1
        frameskip = max(self.settings.global_frameskip, self.device.device_frameskip)
        if self.counter_frame % frameskip != 0:
            return self.matrix_memory.copy()
        else:
            self.matrix_memory = in_matrix.copy()
            return in_matrix
