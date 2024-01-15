from typing import TYPE_CHECKING, Literal, Optional, cast, overload

from loguru import logger
from ravelights.core.custom_typing import ArrayFloat, assert_dims
from ravelights.core.generator_super import Dimmer, Generator, Pattern, Thinner, Vfilter
from ravelights.core.pixel_matrix import PixelMatrix
from ravelights.core.settings import Settings
from ravelights.core.time_handler import BeatStatePattern, TimeHandler

if TYPE_CHECKING:
    from ravelights.core.device import Device
    from ravelights.core.ravelights_app import RaveLightsApp


class RenderModule:
    def __init__(self, root: "RaveLightsApp", device: "Device") -> None:
        self.root = root
        self.settings: Settings = self.root.settings
        self.timehandler: TimeHandler = self.root.timehandler
        self.device: Device = device
        self.pixelmatrix: PixelMatrix = self.device.pixelmatrix
        self.device_automatic_timeline_level = 0
        self.counter_frame = 0  # for frameskip
        self.matrix_memory = self.pixelmatrix.matrix_float.copy()
        self.generators_dict: dict[str, Pattern | Vfilter | Thinner | Dimmer] = dict()

    def get_selected_trigger(
        self,
        gen_type: Literal["pattern", "pattern_sec", "vfilter", "dimmer", "thinner"],
        level: Optional[int] = None,
    ) -> BeatStatePattern:
        if level is None:
            level = self.device_automatic_timeline_level
        return self.settings.triggers[gen_type][level]

    @overload
    def get_selected_generator(self, gen_type: Literal["pattern"], timeline_level: Optional[int] = None) -> Pattern:
        ...

    @overload
    def get_selected_generator(self, gen_type: Literal["pattern_sec"], timeline_level: Optional[int] = None) -> Pattern:
        ...

    @overload
    def get_selected_generator(self, gen_type: Literal["vfilter"], timeline_level: Optional[int] = None) -> Vfilter:
        ...

    @overload
    def get_selected_generator(self, gen_type: Literal["dimmer"], timeline_level: Optional[int] = None) -> Dimmer:
        ...

    @overload
    def get_selected_generator(self, gen_type: Literal["thinner"], timeline_level: Optional[int] = None) -> Thinner:
        ...

    def get_selected_generator(
        self,
        gen_type: Literal["pattern", "pattern_sec", "vfilter", "dimmer", "thinner"],
        timeline_level: Optional[int] = None,
    ) -> Pattern | Vfilter | Thinner | Dimmer:
        if timeline_level is None:
            timeline_level = self.get_timeline_level()
        # identifier = gen_type if isinstance(gen_type, str) else gen_type.get_identifier()
        gen_name = self.settings.selected[gen_type][timeline_level]
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

    def render(self) -> None:
        # ---------------------------- get timeline_level ---------------------------- #
        timeline_level = self.get_timeline_level()
        timeline_level_pattern_sec = 1 if self.settings.global_pattern_sec else timeline_level
        timeline_level_vfilter = 1 if self.settings.global_vfilter else timeline_level
        timeline_level_thinner = 1 if self.settings.global_thinner else timeline_level
        timeline_level_dimmer = 1 if self.settings.global_dimmer else timeline_level

        # ------------------------------ get generators ------------------------------ #
        # fmt: off
        pattern: Pattern = self.get_selected_generator(gen_type="pattern", timeline_level=timeline_level) # type: ignore[type-abstract]
        pattern_sec: Pattern = self.get_selected_generator(gen_type="pattern_sec", timeline_level=timeline_level_pattern_sec)
        vfilter: Vfilter = self.get_selected_generator(gen_type="vfilter", timeline_level=timeline_level_vfilter) # type: ignore[type-abstract]
        thinner: Thinner = self.get_selected_generator(gen_type="thinner", timeline_level=timeline_level_thinner) # type: ignore[type-abstract]
        dimmer: Dimmer = self.get_selected_generator(gen_type="dimmer", timeline_level=timeline_level_dimmer) # type: ignore[type-abstract]
        # fmt: on
        # ------------------------ validate thinner and dimmer ----------------------- #
        if pattern.p_add_thinner == 1.0 and thinner.name == "t_none":
            thinner = cast(Thinner, self.get_generator_by_name("t_random"))
            if self.timehandler.beat_state.is_beat:
                thinner.on_trigger()
        if pattern.p_add_thinner == 0.0:
            thinner = cast(Thinner, self.get_generator_by_name("t_none"))

        if pattern.p_add_dimmer == 1.0 and dimmer.name == "d_none":
            dimmer = cast(Dimmer, self.get_generator_by_name("d_decay_fast"))
            if self.timehandler.beat_state.is_beat:
                dimmer.on_trigger()
        if pattern.p_add_dimmer == 0.0:
            dimmer = cast(Dimmer, self.get_generator_by_name("d_none"))

        # ------------------------------- check trigger ------------------------------ #
        if self.get_selected_trigger(gen_type="pattern").is_match(self.timehandler.beat_state, self.device):
            pattern.on_trigger()
        if self.get_selected_trigger(gen_type="pattern_sec").is_match(self.timehandler.beat_state, self.device):
            pattern_sec.on_trigger()
        if self.get_selected_trigger(gen_type="vfilter").is_match(self.timehandler.beat_state, self.device):
            vfilter.on_trigger()
        if self.get_selected_trigger(gen_type="thinner").is_match(self.timehandler.beat_state, self.device):
            thinner.on_trigger()
        if self.get_selected_trigger(gen_type="dimmer").is_match(self.timehandler.beat_state, self.device):
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
        matrix_sec = pattern_sec.render(colors=colors[::-1])
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
                logger.error("illegal effect_wrapper.draw_mode")

        # global thing
        if self.settings.global_effect_draw_mode == "overlay":
            matrix = Generator.merge_matrices(in_matrix, matrix)
        assert_dims(matrix, self.pixelmatrix.n_leds, self.pixelmatrix.n_lights, 3)

        # ─── Send To Pixelmatrix ──────────────────────────────────────
        self.pixelmatrix.set_matrix_float(matrix)

    def register_generators(self, generators: list[Pattern | Vfilter | Dimmer | Thinner]) -> None:
        for generator in generators:
            self.generators_dict.update({generator.name: generator})

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
