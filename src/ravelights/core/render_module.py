from typing import TYPE_CHECKING, Literal, Optional, cast, overload

from loguru import logger
from ravelights.core.custom_typing import ArrayFloat
from ravelights.core.generator_super import Dimmer, Generator, Pattern, Thinner, Vfilter
from ravelights.core.pixel_matrix import PixelMatrix
from ravelights.core.settings import AutomateChorus, Settings
from ravelights.core.time_handler import BeatStatePattern, TimeHandler

if TYPE_CHECKING:
    from ravelights.core.device import Device
    from ravelights.core.ravelights_app import RaveLightsApp


class RenderModule:
    def __init__(self, root: "RaveLightsApp", device: "Device") -> None:
        self.root = root
        self.settings: Settings = self.root.settings
        self.timehandler: TimeHandler = self.root.time_handler
        self.device: Device = device
        self.pixelmatrix: PixelMatrix = self.device.pixelmatrix

        self.counter_frame: int = 0  # for frameskip
        self.matrix_memory = self.pixelmatrix.matrix_float.copy()
        self.generators_dict: dict[str, Pattern | Vfilter | Thinner | Dimmer] = dict()

    def get_selected_trigger(
        self,
        device_index: int,
        gen_type: Literal["pattern", "pattern_sec", "pattern_break", "vfilter", "dimmer", "thinner"],
        level: Optional[int] = None,
    ) -> BeatStatePattern:
        if level is None:
            level = self.device.device_automatic_timeline_level
        return self.settings.triggers[device_index][gen_type][level]

    # fmt: off
    @overload
    def get_selected_generator(self, gen_type: Literal["pattern"], device_index: int = -1, timeline_level: int = -1) -> Pattern:
        ...

    @overload
    def get_selected_generator(self, gen_type: Literal["pattern_sec"], device_index: int = -1, timeline_level: int = -1) -> Pattern:
        ...

    @overload
    def get_selected_generator(self, gen_type: Literal["pattern_break"], device_index: int = -1, timeline_level: int = -1) -> Pattern:
        ...

    @overload
    def get_selected_generator(self, gen_type: Literal["vfilter"], device_index: int = -1, timeline_level: int = -1) -> Vfilter:
        ...

    @overload
    def get_selected_generator(self, gen_type: Literal["dimmer"], device_index: int = -1, timeline_level: int = -1) -> Dimmer:
        ...

    @overload
    def get_selected_generator(self, gen_type: Literal["thinner"], device_index: int = -1, timeline_level: int = -1) -> Thinner:
        ...
    # fmt: on

    def get_selected_generator(
        self,
        gen_type: Literal["pattern", "pattern_sec", "pattern_break", "vfilter", "dimmer", "thinner"],
        device_index: Optional[int] = None,
        timeline_level: Optional[int] = None,
    ) -> Pattern | Vfilter | Thinner | Dimmer:
        if device_index is None:
            device_index = self.device.linked_to if isinstance(self.device.linked_to, int) else self.device.device_index
        if timeline_level is None:
            timeline_level = self.root.pattern_scheduler.get_effective_timeline_level(device_index)
        device_selected = self.settings.selected[device_index]
        gen_name = device_selected[gen_type][timeline_level]
        return self.get_generator_by_name(gen_name)

    def get_generator_by_name(self, gen_name: str) -> Pattern | Vfilter | Thinner | Dimmer:
        return self.generators_dict[gen_name]

    def render(self) -> None:
        # ----------------------------- get device index ----------------------------- #
        if isinstance(self.device.linked_to, int):
            device_index = self.device.linked_to
            if isinstance(self.root.devices[device_index].linked_to, int):
                # this device is linked to a device, that is linked itself -> change this link to final target with UI refresh
                self.device.update_from_dict({"linked_to": self.root.devices[device_index].linked_to})

        else:
            device_index = self.device.device_index

        # ---------------------------- get timeline_level ---------------------------- #
        timeline_level = self.root.pattern_scheduler.get_effective_timeline_level(device_index)

        # ---------------------------------- render ---------------------------------- #
        array_chorus = self.render_chorus(device_index=device_index, timeline_level=timeline_level)
        assert array_chorus.shape == (self.pixelmatrix.n_leds, self.pixelmatrix.n_lights, 3), array_chorus.shape
        array_break = self.render_break(device_index=device_index, timeline_level=timeline_level)
        assert array_break.shape == (self.pixelmatrix.n_leds, self.pixelmatrix.n_lights, 3), array_break.shape

        # ---------------------------------- combine --------------------------------- #
        # todo: move this somewhere
        effective_chorus: float = 1.0
        if self.settings.automate_chorus == AutomateChorus.manual:
            effective_chorus = self.settings.global_manual_chorus
        if self.settings.automate_chorus == AutomateChorus.audio:
            effective_chorus = self.root.audio_data.audio_data["level_low"]
        matrix = Generator.merge_matrices_with_weight(
            [array_chorus, array_break],
            [effective_chorus, 1 - effective_chorus],
        )

        # ---------------------------- send to pixelmatrix --------------------------- #
        self.pixelmatrix.set_matrix_float(matrix)

    def render_break(self, device_index: int, timeline_level: int) -> ArrayFloat:
        timeline_level_pattern_break = 1 if self.settings.global_pattern_break else timeline_level

        # fmt: off
        pattern_break: Pattern = self.get_selected_generator(device_index=device_index, gen_type="pattern_break", timeline_level=timeline_level_pattern_break)
        # fmt: on

        # ---------------------------------- colors ---------------------------------- #
        colors = self.settings.color_engine.get_colors_rgb(timeline_level=timeline_level)

        # ─── RENDER PATTERN ──────────────────────────────────────────────
        matrix = pattern_break.render(colors=colors)
        # fmt: off
        assert matrix.shape == (self.pixelmatrix.n_leds, self.pixelmatrix.n_lights, 3), (matrix.shape, pattern_break.name)
        # fmt: on

        return matrix

    def render_chorus(self, device_index: int, timeline_level: int) -> ArrayFloat:
        timeline_level_pattern_sec = 1 if self.settings.global_pattern_sec else timeline_level
        timeline_level_vfilter = 1 if self.settings.global_vfilter else timeline_level
        timeline_level_thinner = 1 if self.settings.global_thinner else timeline_level
        timeline_level_dimmer = 1 if self.settings.global_dimmer else timeline_level

        # ------------------------------ get generators ------------------------------ #
        # fmt: off
        pattern: Pattern = self.get_selected_generator(device_index=device_index, gen_type="pattern", timeline_level=timeline_level)
        pattern_sec: Pattern = self.get_selected_generator(device_index=device_index, gen_type="pattern_sec", timeline_level=timeline_level_pattern_sec)
        vfilter: Vfilter = self.get_selected_generator(device_index=device_index, gen_type="vfilter", timeline_level=timeline_level_vfilter)
        thinner: Thinner = self.get_selected_generator(device_index=device_index, gen_type="thinner", timeline_level=timeline_level_thinner)
        dimmer: Dimmer = self.get_selected_generator(device_index=device_index, gen_type="dimmer", timeline_level=timeline_level_dimmer)
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
        # fmt: off
        if self.get_selected_trigger(device_index=device_index, gen_type="pattern").is_match(self.timehandler.beat_state, self.device):
            pattern.on_trigger()
        if self.get_selected_trigger(device_index=device_index, gen_type="pattern_sec").is_match(self.timehandler.beat_state, self.device):
            pattern_sec.on_trigger()
        if self.get_selected_trigger(device_index=device_index, gen_type="vfilter").is_match(self.timehandler.beat_state, self.device):
            vfilter.on_trigger()
        if self.get_selected_trigger(device_index=device_index, gen_type="thinner").is_match(self.timehandler.beat_state, self.device):
            thinner.on_trigger()
        if self.get_selected_trigger(device_index=device_index, gen_type="dimmer").is_match(self.timehandler.beat_state, self.device):
            dimmer.on_trigger()
        # fmt: on

        # ---------------------------------- colors ---------------------------------- #
        # color is a tuple of 2 colors
        # primary color: dominant color in pattern
        # secondary color: optional supplementary color
        colors = self.settings.color_engine.get_colors_rgb(timeline_level=timeline_level)

        # ─── RENDER PATTERN ──────────────────────────────────────────────
        matrix = pattern.render(colors=colors)
        assert matrix.shape == (self.pixelmatrix.n_leds, self.pixelmatrix.n_lights, 3), (matrix.shape, pattern.name)

        # ─── FRAMESKIP ───────────────────────────────────────────────────
        matrix = self.apply_frameskip(matrix)
        assert matrix.shape == (self.pixelmatrix.n_leds, self.pixelmatrix.n_lights, 3), matrix.shape

        # ─── RENDER SECONDARY PATTERN ────────────────────────────────────
        matrix_sec = pattern_sec.render(colors=colors[::-1])
        # fmt: off
        assert matrix_sec.shape == (self.pixelmatrix.n_leds, self.pixelmatrix.n_lights, 3), (matrix.shape, pattern_sec.name)
        # fmt: on
        matrix = Generator.merge_matrices(matrix, matrix_sec)

        # ─── RENDER VFILTER ──────────────────────────────────────────────
        matrix = vfilter.render(in_matrix=matrix, colors=colors)
        assert matrix.shape == (self.pixelmatrix.n_leds, self.pixelmatrix.n_lights, 3), (matrix.shape, vfilter.name)

        # ─── RENDER THINNER ──────────────────────────────────────────────
        matrix = thinner.render(in_matrix=matrix, colors=colors)
        assert matrix.shape == (self.pixelmatrix.n_leds, self.pixelmatrix.n_lights, 3), (matrix.shape, thinner.name)

        # ─── RENDER DIMMER ───────────────────────────────────────────────
        matrix = dimmer.render(in_matrix=matrix, colors=colors)
        assert matrix.shape == (self.pixelmatrix.n_leds, self.pixelmatrix.n_lights, 3), (matrix.shape, dimmer.name)

        # ─── Render Effects ───────────────────────────────────────────────
        for effect_wrapper in self.root.effect_handler.effect_queue:
            matrix = effect_wrapper.render(in_matrix=matrix, colors=colors, device_index=self.device.device_index)

        assert matrix.shape == (self.pixelmatrix.n_leds, self.pixelmatrix.n_lights, 3)

        return matrix

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
